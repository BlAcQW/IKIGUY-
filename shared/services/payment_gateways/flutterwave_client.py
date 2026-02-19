"""
Flutterwave Payment Gateway Integration.

Handles cards, mobile money, bank transfers for African markets.
Centralized implementation for use across all backend applications.
"""

import logging
import hashlib
import hmac
import httpx
from typing import Dict, Any, Optional, List
from decimal import Decimal
from uuid import uuid4

from .base import PaymentGatewayBase, PaymentStatus

logger = logging.getLogger(__name__)


class FlutterwaveClient(PaymentGatewayBase):
    """
    Flutterwave payment gateway client.

    Supports:
    - Card payments
    - Mobile money (MTN, Vodafone, AirtelTigo)
    - Bank transfers
    - Payment links
    - Webhook verification
    """

    BASE_URL = "https://api.flutterwave.com/v3"

    def __init__(
        self,
        secret_key: str,
        public_key: Optional[str] = None,
        encryption_key: Optional[str] = None,
        webhook_secret: Optional[str] = None
    ):
        """
        Initialize Flutterwave client.

        Args:
            secret_key: Flutterwave secret key
            public_key: Flutterwave public key (for frontend)
            encryption_key: Encryption key for 3DS
            webhook_secret: Webhook verification hash
        """
        super().__init__({
            "secret_key": secret_key,
            "public_key": public_key,
            "encryption_key": encryption_key,
            "webhook_secret": webhook_secret
        })

        self.secret_key = secret_key
        self.public_key = public_key
        self.encryption_key = encryption_key
        self.webhook_secret = webhook_secret

        # HTTP client for API requests
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {secret_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )

        logger.info("Flutterwave client initialized")

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    # ==================== Payment Initialization ====================

    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        customer_email: str,
        customer_name: Optional[str] = None,
        customer_phone: Optional[str] = None,
        payment_method: Optional[str] = None,
        redirect_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create Flutterwave payment.

        Args:
            amount: Payment amount
            currency: Currency code (GHS, NGN, USD, etc.)
            customer_email: Customer email
            customer_name: Customer name
            customer_phone: Customer phone (required for mobile money)
            payment_method: Payment method (card, mobilemoney, banktransfer)
            redirect_url: URL to redirect after payment
            metadata: Additional metadata
            **kwargs: Additional Flutterwave parameters

        Returns:
            Payment data with payment link
        """
        try:
            tx_ref = kwargs.get("tx_ref", f"FLW-{uuid4().hex[:16]}")

            payload = {
                "tx_ref": tx_ref,
                "amount": float(amount),
                "currency": currency.upper(),
                "redirect_url": redirect_url or "https://example.com/callback",
                "payment_options": payment_method or "card,mobilemoney,banktransfer",
                "customer": {
                    "email": customer_email,
                },
                "customizations": {
                    "title": metadata.get("title", "Payment"),
                    "description": metadata.get("description", "Payment for services"),
                },
                "meta": metadata or {}
            }

            if customer_name:
                payload["customer"]["name"] = customer_name

            if customer_phone:
                payload["customer"]["phonenumber"] = customer_phone

            # Add payment-specific data
            if payment_method == "mobilemoney" and customer_phone:
                payload["customer"]["phonenumber"] = customer_phone

            response = await self.client.post("/payments", json=payload)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != "success":
                raise Exception(f"Flutterwave error: {data.get('message')}")

            payment_data = data.get("data", {})

            logger.info(f"Created Flutterwave payment: {tx_ref}")

            return {
                "id": tx_ref,
                "payment_link": payment_data.get("link"),
                "client_secret": payment_data.get("link"),  # Using link as client_secret for consistency
                "status": "pending",
                "amount": amount,
                "currency": currency,
                "metadata": metadata
            }

        except httpx.HTTPError as e:
            logger.error(f"Flutterwave HTTP error: {str(e)}")
            raise Exception(f"Payment initialization failed: {str(e)}")

        except Exception as e:
            logger.error(f"Flutterwave error: {str(e)}")
            raise

    async def initiate_mobile_money(
        self,
        amount: Decimal,
        currency: str,
        phone_number: str,
        network: str,
        customer_email: str,
        customer_name: Optional[str] = None,
        tx_ref: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initiate mobile money payment.

        Args:
            amount: Payment amount
            currency: Currency (GHS for Ghana)
            phone_number: Customer phone number
            network: Mobile network (MTN, VODAFONE, TIGO)
            customer_email: Customer email
            customer_name: Customer name
            tx_ref: Transaction reference
            metadata: Additional metadata

        Returns:
            Mobile money payment data
        """
        try:
            tx_ref = tx_ref or f"FLW-MOMO-{uuid4().hex[:12]}"

            payload = {
                "tx_ref": tx_ref,
                "amount": float(amount),
                "currency": currency.upper(),
                "email": customer_email,
                "phone_number": phone_number,
                "network": network.upper(),
                "meta": metadata or {}
            }

            if customer_name:
                payload["fullname"] = customer_name

            response = await self.client.post("/charges", params={"type": "mobile_money_ghana"}, json=payload)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != "success":
                raise Exception(f"Mobile money error: {data.get('message')}")

            charge_data = data.get("data", {})

            logger.info(f"Initiated mobile money: {tx_ref}")

            return {
                "id": charge_data.get("id"),
                "tx_ref": tx_ref,
                "status": charge_data.get("status"),
                "amount": amount,
                "currency": currency,
                "phone_number": phone_number,
                "network": network,
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"Mobile money initiation failed: {str(e)}")
            raise

    # ==================== Payment Verification ====================

    async def retrieve_payment(self, transaction_id: str) -> Dict[str, Any]:
        """
        Verify transaction status.

        Args:
            transaction_id: Transaction ID or tx_ref

        Returns:
            Transaction data with status
        """
        try:
            response = await self.client.get(f"/transactions/{transaction_id}/verify")
            response.raise_for_status()

            data = response.json()

            if data.get("status") != "success":
                raise Exception(f"Verification failed: {data.get('message')}")

            tx_data = data.get("data", {})

            return {
                "id": tx_data.get("id"),
                "tx_ref": tx_data.get("tx_ref"),
                "flw_ref": tx_data.get("flw_ref"),
                "status": tx_data.get("status"),
                "amount": tx_data.get("amount"),
                "currency": tx_data.get("currency"),
                "charged_amount": tx_data.get("charged_amount"),
                "customer": {
                    "email": tx_data.get("customer", {}).get("email"),
                    "name": tx_data.get("customer", {}).get("name"),
                    "phone": tx_data.get("customer", {}).get("phone_number")
                },
                "payment_type": tx_data.get("payment_type"),
                "created_at": tx_data.get("created_at"),
                "metadata": tx_data.get("meta", {})
            }

        except httpx.HTTPError as e:
            logger.error(f"Verification HTTP error: {str(e)}")
            raise

        except Exception as e:
            logger.error(f"Verification failed: {str(e)}")
            raise

    # ==================== Refunds ====================

    async def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate a refund.

        Args:
            transaction_id: Transaction ID
            amount: Amount to refund (None for full refund)
            reason: Refund reason

        Returns:
            Refund data
        """
        try:
            payload = {"id": transaction_id}

            if amount:
                payload["amount"] = float(amount)

            response = await self.client.post("/transactions/refund", json=payload)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != "success":
                raise Exception(f"Refund failed: {data.get('message')}")

            refund_data = data.get("data", {})

            logger.info(f"Created refund for: {transaction_id}")

            return {
                "id": refund_data.get("id"),
                "tx_ref": refund_data.get("tx_ref"),
                "flw_ref": refund_data.get("flw_ref"),
                "amount_refunded": refund_data.get("amount_refunded"),
                "status": refund_data.get("status"),
                "created_at": refund_data.get("created_at")
            }

        except Exception as e:
            logger.error(f"Refund failed: {str(e)}")
            raise

    # ==================== Payment Cancellation ====================

    async def cancel_payment(self, transaction_id: str) -> bool:
        """
        Cancel a pending payment.

        Note: Flutterwave doesn't have explicit cancel endpoint.
        Payments expire automatically if not completed.

        Args:
            transaction_id: Transaction ID

        Returns:
            Success status
        """
        logger.warning("Flutterwave doesn't support explicit payment cancellation")
        return False

    # ==================== Webhooks ====================

    def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Verify Flutterwave webhook signature.

        Args:
            payload: Raw webhook payload (as string or dict)
            signature: Webhook signature from headers
            **kwargs: Additional parameters

        Returns:
            Verified event data

        Raises:
            ValueError: If signature verification fails
        """
        try:
            if not self.webhook_secret:
                raise ValueError("Webhook secret not configured")

            # Flutterwave uses verif-hash header
            if signature != self.webhook_secret:
                raise ValueError("Invalid webhook signature")

            # Parse payload if string
            if isinstance(payload, str):
                import json
                event_data = json.loads(payload)
            else:
                event_data = payload

            logger.info(f"Verified Flutterwave webhook: {event_data.get('event')}")

            return event_data

        except ValueError as e:
            logger.error(f"Webhook verification failed: {str(e)}")
            raise

    # ==================== Status Normalization ====================

    def normalize_payment_status(self, flutterwave_status: str) -> PaymentStatus:
        """
        Normalize Flutterwave status to common PaymentStatus.

        Args:
            flutterwave_status: Flutterwave transaction status

        Returns:
            Normalized PaymentStatus
        """
        status_map = {
            "pending": PaymentStatus.PENDING,
            "successful": PaymentStatus.COMPLETED,
            "success": PaymentStatus.COMPLETED,
            "failed": PaymentStatus.FAILED,
            "cancelled": PaymentStatus.CANCELLED,
        }
        return status_map.get(flutterwave_status.lower(), PaymentStatus.PENDING)

    # ==================== Additional Features ====================

    async def get_banks(self, country: str = "GH") -> List[Dict[str, Any]]:
        """
        Get list of banks for bank transfers.

        Args:
            country: Country code (GH for Ghana, NG for Nigeria)

        Returns:
            List of banks
        """
        try:
            response = await self.client.get(f"/banks/{country}")
            response.raise_for_status()

            data = response.json()

            if data.get("status") != "success":
                return []

            return data.get("data", [])

        except Exception as e:
            logger.error(f"Failed to get banks: {str(e)}")
            return []

    async def verify_account(
        self,
        account_number: str,
        account_bank: str
    ) -> Dict[str, Any]:
        """
        Verify bank account details.

        Args:
            account_number: Bank account number
            account_bank: Bank code

        Returns:
            Account details
        """
        try:
            payload = {
                "account_number": account_number,
                "account_bank": account_bank
            }

            response = await self.client.post("/accounts/resolve", json=payload)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != "success":
                raise Exception(f"Account verification failed: {data.get('message')}")

            return data.get("data", {})

        except Exception as e:
            logger.error(f"Account verification failed: {str(e)}")
            raise
