"""
QuickBooks Online integration client.

Handles OAuth 2.0 flow, token encryption, and QBO API calls.
All synchronous python-quickbooks calls are wrapped in asyncio.to_thread().
"""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet

from app.config import settings

logger = logging.getLogger(__name__)

# Rate limiter: cap concurrent QBO API calls
_qbo_semaphore = asyncio.Semaphore(10)


def _derive_fernet_key(secret: str) -> bytes:
    """Derive a Fernet-compatible key from the app SECRET_KEY."""
    digest = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_token(token: str, secret: str) -> str:
    """Encrypt a token string using Fernet symmetric encryption."""
    key = _derive_fernet_key(secret)
    f = Fernet(key)
    return f.encrypt(token.encode()).decode()


def decrypt_token(encrypted: str, secret: str) -> str:
    """Decrypt a Fernet-encrypted token string."""
    key = _derive_fernet_key(secret)
    f = Fernet(key)
    return f.decrypt(encrypted.encode()).decode()


def create_oauth_state(organization_id: str, secret: str) -> str:
    """
    Create HMAC-signed OAuth state parameter.

    Encodes organization_id + timestamp, signs with SECRET_KEY.
    """
    payload = json.dumps({
        "org_id": organization_id,
        "ts": int(time.time()),
        "nonce": uuid.uuid4().hex[:8],
    })
    signature = hmac.new(
        secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    encoded = base64.urlsafe_b64encode(payload.encode()).decode()
    return f"{encoded}.{signature}"


def verify_oauth_state(state: str, secret: str, max_age_seconds: int = 600) -> Optional[str]:
    """
    Verify HMAC-signed OAuth state and return organization_id.

    Returns None if signature is invalid or state is expired.
    """
    try:
        encoded, signature = state.rsplit(".", 1)
        payload_bytes = base64.urlsafe_b64decode(encoded)
        expected_sig = hmac.new(
            secret.encode(), payload_bytes, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            logger.warning("OAuth state HMAC mismatch")
            return None
        payload = json.loads(payload_bytes)
        if time.time() - payload["ts"] > max_age_seconds:
            logger.warning("OAuth state expired")
            return None
        return payload["org_id"]
    except Exception:
        logger.exception("Failed to verify OAuth state")
        return None


class QuickBooksClient:
    """
    QuickBooks Online API client.

    Wraps intuit-oauth for OAuth flow and python-quickbooks for API calls.
    """

    def __init__(self) -> None:
        self.client_id = settings.QBO_CLIENT_ID
        self.client_secret = settings.QBO_CLIENT_SECRET
        self.redirect_uri = settings.QBO_REDIRECT_URI
        self.environment = settings.QBO_ENVIRONMENT
        self.secret_key = settings.SECRET_KEY

    @property
    def is_configured(self) -> bool:
        """Check if QBO credentials are configured."""
        return bool(self.client_id and self.client_secret)

    def _get_auth_client(self) -> Any:
        """Create an intuit-oauth AuthClient instance."""
        from intuit_oauth import AuthClient
        return AuthClient(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            environment=self.environment,
        )

    def get_auth_url(self, organization_id: str) -> str:
        """
        Generate QBO OAuth authorization URL.

        Args:
            organization_id: Org ID to encode in state param

        Returns:
            Authorization URL to redirect user to
        """
        auth_client = self._get_auth_client()
        state = create_oauth_state(organization_id, self.secret_key)
        scopes = ["com.intuit.quickbooks.accounting"]
        return auth_client.get_authorization_url(scopes, state_token=state)

    async def exchange_code(
        self, auth_code: str, realm_id: str
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access + refresh tokens.

        Returns dict with access_token, refresh_token, and expiry info.
        """
        auth_client = self._get_auth_client()

        def _exchange() -> Any:
            auth_client.get_bearer_token(auth_code, realm_id=realm_id)
            return auth_client

        result = await asyncio.to_thread(_exchange)
        now = datetime.utcnow()

        return {
            "access_token": encrypt_token(result.access_token, self.secret_key),
            "refresh_token": encrypt_token(result.refresh_token, self.secret_key),
            "realm_id": realm_id,
            "access_token_expires_at": now + timedelta(
                seconds=result.expires_in if hasattr(result, "expires_in") else 3600
            ),
            "refresh_token_expires_at": now + timedelta(days=101),
        }

    async def refresh_tokens(self, encrypted_refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token.

        Args:
            encrypted_refresh_token: Fernet-encrypted refresh token

        Returns:
            Dict with new encrypted tokens and expiry times
        """
        refresh_token = decrypt_token(encrypted_refresh_token, self.secret_key)
        auth_client = self._get_auth_client()

        def _refresh() -> Any:
            auth_client.refresh(refresh_token=refresh_token)
            return auth_client

        result = await asyncio.to_thread(_refresh)
        now = datetime.utcnow()

        return {
            "access_token": encrypt_token(result.access_token, self.secret_key),
            "refresh_token": encrypt_token(result.refresh_token, self.secret_key),
            "access_token_expires_at": now + timedelta(
                seconds=result.expires_in if hasattr(result, "expires_in") else 3600
            ),
            "refresh_token_expires_at": now + timedelta(days=101),
        }

    async def ensure_valid_token(self, db: Any, organization_id: str) -> Dict[str, Any]:
        """
        Load credential from DB, auto-refresh if near expiry.

        Returns dict with decrypted access_token and realm_id.

        Raises:
            ValueError: If no active credential found or refresh token expired
        """
        cred = await db.qbo_credentials.find_one({
            "organization_id": organization_id,
            "is_active": True,
        })
        if not cred:
            raise ValueError("QuickBooks is not connected for this organization")

        now = datetime.utcnow()

        # Check if refresh token is expired
        refresh_expires = cred.get("refresh_token_expires_at")
        if refresh_expires and now > refresh_expires:
            await db.qbo_credentials.update_one(
                {"_id": cred["_id"]},
                {"$set": {"is_active": False, "updated_at": now}},
            )
            raise ValueError(
                "QuickBooks refresh token expired. Please reconnect."
            )

        # Refresh if access token expires within 5 minutes
        access_expires = cred.get("access_token_expires_at")
        if access_expires and now > (access_expires - timedelta(minutes=5)):
            logger.info("Refreshing QBO access token for org %s", organization_id)
            new_tokens = await self.refresh_tokens(cred["refresh_token"])
            await db.qbo_credentials.update_one(
                {"_id": cred["_id"]},
                {"$set": {**new_tokens, "updated_at": now}},
            )
            return {
                "access_token": decrypt_token(new_tokens["access_token"], self.secret_key),
                "realm_id": cred["realm_id"],
            }

        return {
            "access_token": decrypt_token(cred["access_token"], self.secret_key),
            "realm_id": cred["realm_id"],
        }

    async def get_company_info(
        self, access_token: str, realm_id: str
    ) -> Optional[str]:
        """Fetch QBO company name. Returns None on failure."""
        try:
            from quickbooks import QuickBooks
            from quickbooks.objects.company_info import CompanyInfo

            def _fetch() -> str:
                client = QuickBooks(
                    auth_client=None,
                    company_id=realm_id,
                    access_token=access_token,
                )
                info = CompanyInfo.get(1, qb=client)
                return info.CompanyName
            async with _qbo_semaphore:
                return await asyncio.to_thread(_fetch)
        except Exception:
            logger.exception("Failed to fetch QBO company info")
            return None

    async def find_customer_by_email(
        self, access_token: str, realm_id: str, email: str
    ) -> Optional[Dict[str, str]]:
        """
        Search QBO for a customer by email.

        Returns dict with Id and DisplayName, or None.
        """
        from quickbooks import QuickBooks
        from quickbooks.objects.customer import Customer

        def _search() -> Optional[Dict[str, str]]:
            client = QuickBooks(
                auth_client=None,
                company_id=realm_id,
                access_token=access_token,
            )
            customers = Customer.where(
                f"PrimaryEmailAddr = '{email}'", qb=client
            )
            if customers:
                c = customers[0]
                return {"Id": c.Id, "DisplayName": c.DisplayName}
            return None

        async with _qbo_semaphore:
            return await asyncio.to_thread(_search)

    async def create_customer(
        self, access_token: str, realm_id: str, contact_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Create a new Customer in QBO.

        Args:
            contact_data: Dict with name, email, phone fields

        Returns:
            Dict with QBO customer Id and DisplayName
        """
        from quickbooks import QuickBooks
        from quickbooks.objects.customer import Customer

        def _create() -> Dict[str, str]:
            client = QuickBooks(
                auth_client=None,
                company_id=realm_id,
                access_token=access_token,
            )
            customer = Customer()
            customer.DisplayName = contact_data.get("name", "Unknown")

            email = contact_data.get("email")
            if email:
                customer.PrimaryEmailAddr = customer.PrimaryEmailAddr or type(
                    "EmailAddr", (), {}
                )()
                customer.PrimaryEmailAddr.Address = email

            phone = contact_data.get("phone")
            if phone:
                customer.PrimaryPhone = customer.PrimaryPhone or type(
                    "PhoneNumber", (), {}
                )()
                customer.PrimaryPhone.FreeFormNumber = phone

            customer.save(qb=client)
            return {"Id": customer.Id, "DisplayName": customer.DisplayName}

        async with _qbo_semaphore:
            return await asyncio.to_thread(_create)

    async def create_invoice(
        self,
        access_token: str,
        realm_id: str,
        invoice_data: Dict[str, Any],
        customer_id: str,
    ) -> Dict[str, Any]:
        """
        Create an Invoice in QBO.

        Args:
            invoice_data: DiaServe invoice data dict
            customer_id: QBO customer ID

        Returns:
            Dict with QBO invoice Id and DocNumber
        """
        from quickbooks import QuickBooks
        from quickbooks.objects.invoice import Invoice as QBOInvoice

        def _create() -> Dict[str, Any]:
            client = QuickBooks(
                auth_client=None,
                company_id=realm_id,
                access_token=access_token,
            )
            qbo_inv = QBOInvoice()

            # Document number (max 21 chars)
            doc_number = invoice_data.get("invoice_number", "")[:21]
            qbo_inv.DocNumber = doc_number

            # Customer reference
            qbo_inv.CustomerRef = {"value": customer_id}

            # Dates
            due_date = invoice_data.get("due_date")
            if due_date:
                if isinstance(due_date, datetime):
                    qbo_inv.DueDate = due_date.strftime("%Y-%m-%d")
                else:
                    qbo_inv.DueDate = str(due_date)[:10]

            invoice_date = invoice_data.get("invoice_date")
            if invoice_date:
                if isinstance(invoice_date, datetime):
                    qbo_inv.TxnDate = invoice_date.strftime("%Y-%m-%d")
                else:
                    qbo_inv.TxnDate = str(invoice_date)[:10]

            # Email
            email = invoice_data.get("contact_email")
            if email:
                qbo_inv.BillEmail = {"Address": email}

            # Currency
            currency = invoice_data.get("currency")
            if currency:
                qbo_inv.CurrencyRef = {"value": currency}

            # Notes
            notes = invoice_data.get("notes", "")
            if notes:
                qbo_inv.PrivateNote = notes[:4000]

            terms = invoice_data.get("terms", "")
            if terms:
                qbo_inv.CustomerMemo = {"value": terms[:1000]}

            # Line items
            lines = []
            for item in invoice_data.get("line_items", []):
                qty = item.get("quantity", 1)
                unit_price = item.get("unit_price", 0)
                amount = qty * unit_price
                tax_rate = item.get("tax_rate", 0)

                line = {
                    "Amount": amount,
                    "DetailType": "SalesItemLineDetail",
                    "Description": item.get("description", ""),
                    "SalesItemLineDetail": {
                        "Qty": qty,
                        "UnitPrice": unit_price,
                        "TaxCodeRef": {
                            "value": "TAX" if tax_rate > 0 else "NON"
                        },
                    },
                }
                lines.append(line)

            qbo_inv.Line = lines

            qbo_inv.save(qb=client)
            return {
                "Id": qbo_inv.Id,
                "DocNumber": qbo_inv.DocNumber,
            }

        async with _qbo_semaphore:
            return await asyncio.to_thread(_create)
