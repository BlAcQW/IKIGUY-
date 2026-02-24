"""
QuickBooks Online sync service.

Handles connecting/disconnecting QBO, syncing invoices, and customer mapping.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.integration.quickbooks_client import (
    QuickBooksClient,
    verify_oauth_state,
    encrypt_token,
    decrypt_token,
)
from app.config import settings
from app.models.quickbooks import QBOConnectionStatus, QBOSyncResult

logger = logging.getLogger(__name__)


class QBOSyncService:
    """Service for QuickBooks Online invoice synchronization."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self.invoices = db.invoices
        self.credentials = db.qbo_credentials
        self.customer_mappings = db.qbo_customer_mappings
        self.contacts = db.contacts
        self.qbo_client = QuickBooksClient()

    def get_auth_url(self, organization_id: str) -> str:
        """Generate QBO OAuth authorization URL for an organization."""
        if not self.qbo_client.is_configured:
            raise ValueError(
                "QuickBooks integration is not configured. "
                "Set QBO_CLIENT_ID and QBO_CLIENT_SECRET."
            )
        return self.qbo_client.get_auth_url(organization_id)

    async def handle_callback(
        self, code: str, state: str, realm_id: str
    ) -> str:
        """
        Handle OAuth callback from Intuit.

        Verifies HMAC state, exchanges code for tokens, stores credentials.

        Returns:
            organization_id on success

        Raises:
            ValueError: If state verification fails
        """
        organization_id = verify_oauth_state(state, settings.SECRET_KEY)
        if not organization_id:
            raise ValueError("Invalid or expired OAuth state")

        # Exchange code for tokens
        token_data = await self.qbo_client.exchange_code(code, realm_id)

        # Try to fetch company name
        access_token = decrypt_token(
            token_data["access_token"], settings.SECRET_KEY
        )
        company_name = await self.qbo_client.get_company_info(
            access_token, realm_id
        )

        now = datetime.utcnow()

        # Upsert credential (one per org)
        await self.credentials.update_one(
            {"organization_id": organization_id},
            {
                "$set": {
                    "realm_id": realm_id,
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data["refresh_token"],
                    "access_token_expires_at": token_data["access_token_expires_at"],
                    "refresh_token_expires_at": token_data["refresh_token_expires_at"],
                    "company_name": company_name,
                    "is_active": True,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "id": str(uuid.uuid4()),
                    "organization_id": organization_id,
                    "created_at": now,
                },
            },
            upsert=True,
        )

        logger.info(
            "QBO connected for org %s (realm %s, company %s)",
            organization_id,
            realm_id,
            company_name,
        )
        return organization_id

    async def disconnect(self, organization_id: str) -> None:
        """Soft-disconnect QBO by deactivating the credential."""
        result = await self.credentials.update_one(
            {"organization_id": organization_id, "is_active": True},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}},
        )
        if result.modified_count == 0:
            raise ValueError("QuickBooks is not connected for this organization")
        logger.info("QBO disconnected for org %s", organization_id)

    async def get_connection_status(
        self, organization_id: str
    ) -> QBOConnectionStatus:
        """Get the QBO connection status for an organization."""
        cred = await self.credentials.find_one({
            "organization_id": organization_id,
            "is_active": True,
        })
        if not cred:
            return QBOConnectionStatus(is_connected=False)

        return QBOConnectionStatus(
            is_connected=True,
            company_name=cred.get("company_name"),
            realm_id=cred.get("realm_id"),
            connected_at=cred.get("created_at"),
        )

    async def _get_or_create_qbo_customer(
        self,
        organization_id: str,
        contact_id: str,
        access_token: str,
        realm_id: str,
    ) -> str:
        """
        Get or create a QBO customer for a DiaServe contact.

        Checks mapping cache first, then searches QBO by email,
        creates if not found. Returns QBO customer ID.
        """
        # Check existing mapping
        mapping = await self.customer_mappings.find_one({
            "organization_id": organization_id,
            "diaserve_contact_id": contact_id,
        })
        if mapping:
            return mapping["qbo_customer_id"]

        # Lookup contact in DiaServe
        contact = await self.contacts.find_one({"id": contact_id})
        if not contact:
            raise ValueError(f"Contact {contact_id} not found")

        contact_email = contact.get("email", "")
        contact_name = contact.get("name", "Unknown")

        # Try to find existing QBO customer by email
        qbo_customer: Optional[Dict[str, str]] = None
        if contact_email:
            qbo_customer = await self.qbo_client.find_customer_by_email(
                access_token, realm_id, contact_email
            )

        # Create QBO customer if not found
        if not qbo_customer:
            qbo_customer = await self.qbo_client.create_customer(
                access_token,
                realm_id,
                {
                    "name": contact_name,
                    "email": contact_email,
                    "phone": contact.get("phone", ""),
                },
            )

        # Store mapping
        await self.customer_mappings.update_one(
            {
                "organization_id": organization_id,
                "diaserve_contact_id": contact_id,
            },
            {
                "$set": {
                    "qbo_customer_id": qbo_customer["Id"],
                    "qbo_customer_name": qbo_customer["DisplayName"],
                },
                "$setOnInsert": {
                    "id": str(uuid.uuid4()),
                    "organization_id": organization_id,
                    "diaserve_contact_id": contact_id,
                    "created_at": datetime.utcnow(),
                },
            },
            upsert=True,
        )

        return qbo_customer["Id"]

    async def sync_invoice(
        self, organization_id: str, invoice_id: str
    ) -> Dict[str, Any]:
        """
        Sync a single invoice to QBO.

        Returns dict with qbo_invoice_id on success.

        Raises:
            ValueError: If invoice not found or QBO not connected
        """
        invoice = await self.invoices.find_one({
            "id": invoice_id,
            "organization_id": organization_id,
            "is_deleted": {"$ne": True},
        })
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        now = datetime.utcnow()

        try:
            # Ensure valid token
            token_info = await self.qbo_client.ensure_valid_token(
                self.db, organization_id
            )
            access_token = token_info["access_token"]
            realm_id = token_info["realm_id"]

            # Get or create QBO customer
            qbo_customer_id = await self._get_or_create_qbo_customer(
                organization_id,
                invoice["contact_id"],
                access_token,
                realm_id,
            )

            # Create invoice in QBO
            qbo_result = await self.qbo_client.create_invoice(
                access_token, realm_id, invoice, qbo_customer_id
            )

            # Update local invoice with sync info
            await self.invoices.update_one(
                {"id": invoice_id},
                {
                    "$set": {
                        "qbo_invoice_id": qbo_result["Id"],
                        "qbo_sync_status": "synced",
                        "qbo_last_synced_at": now,
                        "qbo_sync_error": None,
                        "updated_at": now,
                    }
                },
            )

            logger.info(
                "Synced invoice %s to QBO (QBO ID: %s)",
                invoice_id,
                qbo_result["Id"],
            )
            return {"qbo_invoice_id": qbo_result["Id"]}

        except Exception as e:
            error_msg = str(e)
            logger.error("Failed to sync invoice %s: %s", invoice_id, error_msg)

            # Mark invoice with error status
            await self.invoices.update_one(
                {"id": invoice_id},
                {
                    "$set": {
                        "qbo_sync_status": "error",
                        "qbo_sync_error": error_msg[:500],
                        "updated_at": now,
                    }
                },
            )
            raise

    async def sync_all_unsynced(self, organization_id: str) -> QBOSyncResult:
        """
        Sync all unsynced non-draft invoices to QBO.

        Returns a QBOSyncResult with counts and error messages.
        """
        # Find invoices that need syncing
        cursor = self.invoices.find({
            "organization_id": organization_id,
            "is_deleted": {"$ne": True},
            "status": {"$ne": "draft"},
            "qbo_sync_status": {"$ne": "synced"},
        })
        invoices = await cursor.to_list(length=500)

        total = len(invoices)
        synced = 0
        failed = 0
        errors: list[str] = []

        for inv in invoices:
            try:
                await self.sync_invoice(organization_id, inv["id"])
                synced += 1
            except Exception as e:
                failed += 1
                errors.append(
                    f"{inv.get('invoice_number', inv['id'])}: {str(e)[:200]}"
                )

        logger.info(
            "QBO bulk sync for org %s: %d total, %d synced, %d failed",
            organization_id,
            total,
            synced,
            failed,
        )

        return QBOSyncResult(
            total_invoices=total,
            synced=synced,
            failed=failed,
            errors=errors,
        )
