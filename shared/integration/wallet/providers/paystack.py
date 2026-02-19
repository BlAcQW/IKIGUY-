"""
Paystack Payment Provider

Handles payments via Paystack with support for:
- Card payments
- Bank transfers
- Mobile money (MTN, Vodafone, AirtelTigo)
- USSD payments
- Customer management
- Bank account verification
- Webhook verification (HMAC SHA512)
- Refunds

Coverage: Nigeria, Ghana, Kenya, South Africa

Author: KasaAI Team
Date: 2025-10-27
"""

import logging
import httpx
import hmac
import hashlib
from typing import Dict, Any, Optional, Tuple, List
from decimal import Decimal

from .base import BasePaymentProvider
from ..models import (
    PaymentInitiationResult,
    ProviderConfig,
    Currency,
    PaymentProvider
)
from ..exceptions import (
    ProviderAPIError,
    PaymentDeclinedError,
    InvalidWebhookSignatureError,
    ValidationError
)

logger = logging.getLogger(__name__)


class PaystackProvider(BasePaymentProvider):
    """
    Paystack payment provider implementation.

    Supports:
    - Credit/debit card payments
    - Bank transfers
    - Mobile money (Ghana: MTN, Vodafone, AirtelTigo)
    - USSD payments
    - Customer management
    - Bank account resolution
    - Webhook verification (HMAC SHA512)
    - Refunds (full and partial)

    Coverage:
    - Nigeria (NGN)
    - Ghana (GHS)
    - Kenya (KES)
    - South Africa (ZAR)

    Example:
        provider = PaystackProvider(paystack_config)

        # Initialize payment
        result = await provider.initialize_payment(
            amount=Decimal("100.00"),
            currency=Currency.GHS,
            customer_id="CUS_xxx",
            metadata={"transaction_id": "txn_123"}
        )

        # Verify webhook
        is_valid = await provider.verify_webhook(
            payload=webhook_data,
            signature=paystack_signature,
            raw_payload=raw_body
        )
    """

    # Paystack API base URLs
    LIVE_API_URL = "https://api.paystack.co"
    TEST_API_URL = "https://api.paystack.co"  # Paystack uses same URL for test/live

    def __init__(self, config: ProviderConfig):
        """
        Initialize Paystack provider.

        Args:
            config: Provider configuration with Paystack credentials
        """
        super().__init__(config)

        # Set API base URL
        self.api_url = self.LIVE_API_URL  # Paystack uses same URL for both modes

        # HTTP client for API calls
        self.http_client = httpx.AsyncClient(
            base_url=self.api_url,
            headers={
                "Authorization": f"Bearer {config.secret_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )

        logger.info(f"Paystack provider initialized (test_mode={self.is_test_mode})")

    def _validate_config(self):
        """Validate Paystack configuration."""
        super()._validate_config()

        # Validate secret key format
        if not self.config.secret_key.startswith('sk_'):
            raise ValidationError(
                'secret_key',
                'Paystack secret key must start with sk_'
            )

        # Warn if no webhook secret
        if not self.config.webhook_secret:
            logger.warning(
                "Paystack webhook_secret not configured. "
                "Webhook verification will fail."
            )

    # ========================================================================
    # PAYMENT PROCESSING
    # ========================================================================

    async def initialize_payment(
        self,
        amount: Decimal,
        currency: Currency,
        payment_method_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentInitiationResult:
        """
        Initialize Paystack transaction.

        Args:
            amount: Amount to charge (in major currency units)
            currency: Currency code (GHS, NGN, KES, ZAR, USD)
            payment_method_id: Payment channel (card, bank, mobile_money, ussd)
            customer_id: Paystack customer code (CUS_xxx) or email
            metadata: Additional metadata (must include transaction_id)

        Returns:
            PaymentInitiationResult with payment details

        Raises:
            ValidationError: If required parameters are missing
            ProviderAPIError: If Paystack API returns an error
        """
        try:
            # Convert amount to kobo/pesewas (minor units)
            amount_minor = self._convert_to_minor_unit(amount, currency)

            # Build request payload
            payload: Dict[str, Any] = {
                "amount": amount_minor,
                "currency": currency.value,
                "metadata": metadata or {},
            }

            # Add customer email or code
            if customer_id:
                if "@" in customer_id:
                    payload["email"] = customer_id
                else:
                    payload["customer"] = customer_id
            elif metadata and metadata.get("customer_email"):
                payload["email"] = metadata.get("customer_email")
            else:
                raise ValidationError(
                    "customer_id",
                    "Customer ID/email is required for Paystack transactions"
                )

            # Add payment channel if specified
            if payment_method_id:
                payload["channels"] = [payment_method_id]

            # Add callback URL for redirects
            payload["callback_url"] = self._get_redirect_url()

            # Initialize transaction
            response = await self.http_client.post(
                "/transaction/initialize",
                json=payload
            )

            result = response.json()

            if response.status_code != 200 or not result.get("status"):
                error_msg = result.get("message", "Transaction initialization failed")
                logger.error(f"Paystack initialization failed: {error_msg}")
                raise ProviderAPIError(
                    provider=self.provider_name,
                    error_message=error_msg,
                    error_code=str(response.status_code)
                )

            data = result["data"]
            logger.info(f"Initialized Paystack transaction: {data['reference']}")

            return PaymentInitiationResult(
                success=True,
                payment_url=data["authorization_url"],
                reference=data["reference"],
                amount=amount,
                currency=currency,
                gateway=PaymentProvider.PAYSTACK,
                metadata={
                    "access_code": data["access_code"],
                    "reference": data["reference"]
                }
            )

        except httpx.HTTPError as e:
            logger.error(f"Paystack HTTP error: {str(e)}")
            raise ProviderAPIError(
                provider=self.provider_name,
                error_message=f"HTTP request failed: {str(e)}",
                error_code="http_error"
            )

    # ========================================================================
    # WEBHOOK HANDLING
    # ========================================================================

    async def verify_webhook(
        self,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        raw_payload: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Verify Paystack webhook signature using HMAC SHA512.

        Args:
            payload: Parsed webhook payload (not used)
            signature: x-paystack-signature header value
            raw_payload: Raw request body (required)
            headers: Request headers

        Returns:
            True if signature is valid

        Raises:
            InvalidWebhookSignatureError: If signature is invalid
        """
        if not signature or not raw_payload:
            logger.error("Paystack webhook verification requires signature and raw_payload")
            return False

        if not self.config.webhook_secret:
            logger.error("Paystack webhook_secret not configured")
            return False

        try:
            # Compute HMAC SHA512 signature
            computed_signature = hmac.new(
                self.config.webhook_secret.encode('utf-8'),
                raw_payload.encode('utf-8') if isinstance(raw_payload, str) else raw_payload,
                hashlib.sha512
            ).hexdigest()

            # Compare signatures
            if hmac.compare_digest(computed_signature, signature):
                logger.info("Verified Paystack webhook signature")
                return True
            else:
                logger.error("Invalid Paystack webhook signature")
                return False

        except Exception as e:
            logger.error(f"Paystack webhook verification error: {str(e)}")
            return False

    async def process_webhook(
        self,
        payload: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Process Paystack webhook event.

        Args:
            payload: Verified webhook payload

        Returns:
            Tuple of (success, transaction_id, provider_data)

        Supported Events:
        - charge.success: Payment completed successfully
        - charge.failed: Payment failed
        - transfer.success: Transfer completed (for withdrawals)
        - transfer.failed: Transfer failed
        """
        event_type = payload.get('event')

        if event_type == 'charge.success':
            # Payment succeeded
            data = payload.get('data', {})
            transaction_id = data.get('metadata', {}).get('transaction_id')

            # Extract amount (convert from kobo/pesewas)
            amount_minor = data.get('amount', 0)
            currency_str = data.get('currency', 'GHS')
            try:
                currency = Currency(currency_str)
                amount = self._convert_from_minor_unit(amount_minor, currency)
            except ValueError:
                amount = Decimal(str(amount_minor / 100))
                currency = Currency.GHS

            provider_data = {
                'provider_id': data.get('reference'),
                'amount': amount,
                'currency': currency_str,
                'status': 'completed',
                'channel': data.get('channel'),
                'fees': self._convert_from_minor_unit(
                    data.get('fees', 0),
                    currency
                ),
                'authorization': data.get('authorization'),
                'customer': data.get('customer'),
                'paid_at': data.get('paid_at')
            }

            logger.info(f"Paystack payment succeeded: {data.get('reference')}")
            return True, transaction_id, provider_data

        elif event_type == 'charge.failed':
            # Payment failed
            data = payload.get('data', {})
            transaction_id = data.get('metadata', {}).get('transaction_id')

            failure_message = data.get('gateway_response', 'Payment failed')

            provider_data = {
                'provider_id': data.get('reference'),
                'failure_reason': failure_message,
                'status': 'failed',
                'channel': data.get('channel'),
                'gateway_response': data.get('gateway_response')
            }

            logger.warning(f"Paystack payment failed: {data.get('reference')} - {failure_message}")
            return False, transaction_id, provider_data

        elif event_type == 'transfer.success':
            # Transfer succeeded (withdrawal)
            data = payload.get('data', {})
            transaction_id = data.get('reason', '')  # We store transaction_id in reason field

            provider_data = {
                'provider_id': data.get('transfer_code'),
                'amount': self._convert_from_minor_unit(
                    data.get('amount', 0),
                    Currency.GHS
                ),
                'currency': data.get('currency', 'GHS'),
                'status': 'completed',
                'recipient': data.get('recipient'),
                'transferred_at': data.get('transferred_at')
            }

            logger.info(f"Paystack transfer succeeded: {data.get('transfer_code')}")
            return True, transaction_id, provider_data

        elif event_type == 'transfer.failed':
            # Transfer failed (withdrawal)
            data = payload.get('data', {})
            transaction_id = data.get('reason', '')

            failure_message = data.get('status', 'Transfer failed')

            provider_data = {
                'provider_id': data.get('transfer_code'),
                'failure_reason': failure_message,
                'status': 'failed'
            }

            logger.warning(f"Paystack transfer failed: {data.get('transfer_code')}")
            return False, transaction_id, provider_data

        else:
            # Unknown event type
            logger.info(f"Ignoring Paystack webhook event: {event_type}")
            return True, None, None

    # ========================================================================
    # TRANSACTION MANAGEMENT
    # ========================================================================

    async def get_transaction_status(
        self,
        provider_transaction_id: str
    ) -> Dict[str, Any]:
        """
        Get Paystack transaction status.

        Args:
            provider_transaction_id: Paystack reference

        Returns:
            Transaction status details
        """
        try:
            response = await self.http_client.get(
                f"/transaction/verify/{provider_transaction_id}"
            )

            result = response.json()

            if response.status_code != 200 or not result.get("status"):
                error_msg = result.get("message", "Transaction verification failed")
                logger.error(f"Paystack verification failed: {error_msg}")
                raise ProviderAPIError(
                    provider=self.provider_name,
                    error_message=error_msg,
                    error_code=str(response.status_code)
                )

            data = result["data"]

            # Convert amount from kobo/pesewas
            amount_minor = data.get('amount', 0)
            currency_str = data.get('currency', 'GHS')
            try:
                currency = Currency(currency_str)
                amount = self._convert_from_minor_unit(amount_minor, currency)
            except ValueError:
                amount = Decimal(str(amount_minor / 100))

            return {
                'id': data.get('id'),
                'reference': data.get('reference'),
                'status': data.get('status'),
                'amount': amount,
                'currency': currency_str,
                'channel': data.get('channel'),
                'fees': self._convert_from_minor_unit(data.get('fees', 0), currency),
                'authorization': data.get('authorization'),
                'customer': data.get('customer'),
                'metadata': data.get('metadata'),
                'created_at': data.get('created_at'),
                'paid_at': data.get('paid_at')
            }

        except httpx.HTTPError as e:
            logger.error(f"Failed to retrieve Paystack transaction: {str(e)}")
            raise ProviderAPIError(
                provider=self.provider_name,
                error_message=f"Failed to get transaction status: {str(e)}",
                error_code="retrieval_error"
            )

    async def refund_payment(
        self,
        provider_transaction_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Refund a Paystack payment.

        Args:
            provider_transaction_id: Paystack reference
            amount: Amount to refund (None = full refund)
            reason: Refund reason

        Returns:
            Refund result with status
        """
        try:
            # Build refund payload
            payload: Dict[str, Any] = {
                "transaction": provider_transaction_id
            }

            if amount:
                # Convert to kobo/pesewas
                payload["amount"] = int(amount * 100)

            if reason:
                payload["merchant_note"] = reason

            # Create refund
            response = await self.http_client.post(
                "/refund",
                json=payload
            )

            result = response.json()

            if response.status_code != 200 or not result.get("status"):
                error_msg = result.get("message", "Refund failed")
                logger.error(f"Paystack refund failed: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }

            data = result.get("data", {})
            logger.info(f"Created Paystack refund for {provider_transaction_id}")

            return {
                'success': True,
                'refund_id': data.get('id'),
                'amount': self._convert_from_minor_unit(
                    data.get('amount', 0),
                    Currency.GHS
                ),
                'currency': data.get('currency', 'GHS'),
                'status': data.get('status'),
                'refunded_at': data.get('refunded_at')
            }

        except httpx.HTTPError as e:
            logger.error(f"Paystack refund HTTP error: {str(e)}")
            return {
                'success': False,
                'error': f"HTTP request failed: {str(e)}"
            }

    # ========================================================================
    # CUSTOMER MANAGEMENT
    # ========================================================================

    async def create_customer(
        self,
        user_id: str,
        email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create Paystack customer.

        Args:
            user_id: Our user ID
            email: User's email (required)
            metadata: Additional metadata

        Returns:
            Customer details with customer_code
        """
        if not email:
            raise ValidationError("email", "Email is required for Paystack customers")

        try:
            customer_metadata = metadata or {}
            customer_metadata['user_id'] = user_id

            payload = {
                "email": email,
                "metadata": customer_metadata
            }

            response = await self.http_client.post(
                "/customer",
                json=payload
            )

            result = response.json()

            if response.status_code != 200 or not result.get("status"):
                error_msg = result.get("message", "Customer creation failed")
                logger.error(f"Paystack customer creation failed: {error_msg}")
                raise ProviderAPIError(
                    provider=self.provider_name,
                    error_message=error_msg,
                    error_code=str(response.status_code)
                )

            data = result["data"]
            logger.info(f"Created Paystack customer: {data['customer_code']} for user {user_id}")

            return {
                'customer_id': data['customer_code'],
                'customer_code': data['customer_code'],
                'email': data['email'],
                'integration': data.get('integration'),
                'created_at': data.get('createdAt')
            }

        except httpx.HTTPError as e:
            logger.error(f"Failed to create Paystack customer: {str(e)}")
            raise ProviderAPIError(
                provider=self.provider_name,
                error_message=f"Failed to create customer: {str(e)}",
                error_code="customer_creation_error"
            )

    # ========================================================================
    # PAYSTACK-SPECIFIC METHODS
    # ========================================================================

    async def list_banks(self, country: str = "ghana") -> List[Dict[str, Any]]:
        """
        List supported banks for a country.

        Args:
            country: Country name (ghana, nigeria, kenya, south africa)

        Returns:
            List of banks with name, code, and slug
        """
        try:
            response = await self.http_client.get(
                "/bank",
                params={"country": country}
            )

            result = response.json()

            if response.status_code != 200 or not result.get("status"):
                logger.error(f"Failed to list banks: {result.get('message')}")
                return []

            banks = result.get("data", [])
            logger.info(f"Retrieved {len(banks)} banks for {country}")

            return [
                {
                    "id": bank.get("id"),
                    "name": bank.get("name"),
                    "code": bank.get("code"),
                    "slug": bank.get("slug"),
                    "country": bank.get("country"),
                    "currency": bank.get("currency"),
                    "type": bank.get("type"),
                    "active": bank.get("active", True)
                }
                for bank in banks
            ]

        except httpx.HTTPError as e:
            logger.error(f"Failed to list banks: {str(e)}")
            return []

    async def resolve_account_number(
        self,
        account_number: str,
        bank_code: str
    ) -> Dict[str, Any]:
        """
        Resolve and verify bank account details.

        Args:
            account_number: Bank account number
            bank_code: Bank code from list_banks()

        Returns:
            Account details with account_name
        """
        try:
            response = await self.http_client.get(
                "/bank/resolve",
                params={
                    "account_number": account_number,
                    "bank_code": bank_code
                }
            )

            result = response.json()

            if response.status_code != 200 or not result.get("status"):
                error_msg = result.get("message", "Account resolution failed")
                logger.error(f"Paystack account resolution failed: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }

            data = result["data"]
            logger.info(f"Resolved account: {account_number} - {data.get('account_name')}")

            return {
                'success': True,
                'account_number': data.get('account_number'),
                'account_name': data.get('account_name'),
                'bank_id': data.get('bank_id')
            }

        except httpx.HTTPError as e:
            logger.error(f"Failed to resolve account: {str(e)}")
            return {
                'success': False,
                'error': f"HTTP request failed: {str(e)}"
            }

    async def create_transfer_recipient(
        self,
        account_name: str,
        account_number: str,
        bank_code: str,
        currency: Currency = Currency.GHS
    ) -> Dict[str, Any]:
        """
        Create transfer recipient for withdrawals.

        Args:
            account_name: Account holder name
            account_number: Bank account number
            bank_code: Bank code from list_banks()
            currency: Currency (GHS, NGN, etc.)

        Returns:
            Recipient details with recipient_code
        """
        try:
            payload = {
                "type": "nuban",  # Nigerian Uniform Bank Account Number (also used for others)
                "name": account_name,
                "account_number": account_number,
                "bank_code": bank_code,
                "currency": currency.value
            }

            response = await self.http_client.post(
                "/transferrecipient",
                json=payload
            )

            result = response.json()

            if response.status_code != 201 or not result.get("status"):
                error_msg = result.get("message", "Recipient creation failed")
                logger.error(f"Paystack recipient creation failed: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }

            data = result["data"]
            logger.info(f"Created transfer recipient: {data['recipient_code']}")

            return {
                'success': True,
                'recipient_code': data['recipient_code'],
                'type': data.get('type'),
                'name': data.get('name'),
                'details': data.get('details')
            }

        except httpx.HTTPError as e:
            logger.error(f"Failed to create recipient: {str(e)}")
            return {
                'success': False,
                'error': f"HTTP request failed: {str(e)}"
            }

    async def initiate_transfer(
        self,
        recipient_code: str,
        amount: Decimal,
        currency: Currency = Currency.GHS,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate transfer to recipient (withdrawal).

        Args:
            recipient_code: Recipient code from create_transfer_recipient()
            amount: Amount to transfer
            currency: Currency
            reason: Transfer reason/description

        Returns:
            Transfer details with transfer_code
        """
        try:
            # Convert to kobo/pesewas
            amount_minor = self._convert_to_minor_unit(amount, currency)

            payload = {
                "source": "balance",
                "amount": amount_minor,
                "recipient": recipient_code,
                "reason": reason or "Wallet withdrawal"
            }

            response = await self.http_client.post(
                "/transfer",
                json=payload
            )

            result = response.json()

            if response.status_code != 200 or not result.get("status"):
                error_msg = result.get("message", "Transfer initiation failed")
                logger.error(f"Paystack transfer failed: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }

            data = result["data"]
            logger.info(f"Initiated Paystack transfer: {data['transfer_code']}")

            return {
                'success': True,
                'transfer_code': data['transfer_code'],
                'reference': data.get('reference'),
                'amount': self._convert_from_minor_unit(data['amount'], currency),
                'status': data.get('status'),
                'created_at': data.get('createdAt')
            }

        except httpx.HTTPError as e:
            logger.error(f"Failed to initiate transfer: {str(e)}")
            return {
                'success': False,
                'error': f"HTTP request failed: {str(e)}"
            }

    # ========================================================================
    # HEALTH CHECK
    # ========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Paystack API connectivity.

        Returns:
            Health status
        """
        try:
            # Try to list banks (simple API call)
            banks = await self.list_banks("ghana")

            return {
                "provider": self.provider_name,
                "status": "healthy",
                "message": f"Successfully connected to Paystack API ({len(banks)} banks available)",
                "test_mode": self.is_test_mode
            }

        except Exception as e:
            return {
                "provider": self.provider_name,
                "status": "unhealthy",
                "message": f"Paystack API error: {str(e)}",
                "test_mode": self.is_test_mode
            }

    # ========================================================================
    # CLEANUP
    # ========================================================================

    async def close(self):
        """Close HTTP client connection."""
        await self.http_client.aclose()
