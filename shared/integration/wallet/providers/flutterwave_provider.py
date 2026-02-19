"""
Flutterwave Payment Provider

Handles payments via Flutterwave with support for:
- Card payments
- Mobile Money (Ghana): MTN, Vodafone, AirtelTigo
- Mobile Money (Other countries)
- Bank transfers
- Webhook verification
- Refunds

Ported from core_backend with enhancements.

Author: KasaAI Team
Date: 2025-10-27
"""

import logging
import hashlib
import httpx
from typing import Dict, Any, Optional, Tuple
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


class FlutterwaveProvider(BasePaymentProvider):
    """
    Flutterwave payment provider implementation.

    Supports:
    - Credit/debit card payments
    - Mobile Money (Ghana): MTN, Vodafone, AirtelTigo
    - Mobile Money (Kenya, Uganda, Rwanda, etc.)
    - Bank transfers
    - USSD payments
    - Webhook verification
    - Refunds (full and partial)

    Example:
        provider = FlutterwaveProvider(flutterwave_config)

        # Initialize card payment
        result = await provider.initialize_payment(
            amount=Decimal("100.00"),
            currency=Currency.GHS,
            metadata={
                "transaction_id": "txn_123",
                "email": "user@example.com",
                "name": "John Doe"
            }
        )

        # Initialize mobile money payment
        result = await provider.initialize_payment(
            amount=Decimal("50.00"),
            currency=Currency.GHS,
            payment_method_id="phone:+233201234567",  # Phone number
            metadata={
                "transaction_id": "txn_456",
                "email": "user@example.com",
                "network": "MTN"  # MTN, VODAFONE, or AIRTELTIGO
            }
        )
    """

    def __init__(self, config: ProviderConfig):
        """
        Initialize Flutterwave provider.

        Args:
            config: Provider configuration with Flutterwave credentials
        """
        super().__init__(config)

        # HTTP client for API requests
        self.http_client = httpx.AsyncClient(timeout=30.0)

        # Flutterwave API base URL
        self.base_url = "https://api.flutterwave.com/v3"

        logger.info(f"Flutterwave provider initialized (test_mode={self.is_test_mode})")

    def _validate_config(self):
        """Validate Flutterwave configuration."""
        super()._validate_config()

        # Warn if no webhook secret (needed for webhook verification)
        if not self.config.webhook_secret:
            logger.warning(
                "Flutterwave webhook_secret not configured. "
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
        Initialize Flutterwave payment.

        Args:
            amount: Amount to charge
            currency: Currency code
            payment_method_id: For mobile money, format: "phone:+233..."
            customer_id: Customer ID (not used by Flutterwave)
            metadata: Required fields:
                - transaction_id: Our transaction ID
                - email: Customer email
                - name: Customer name (optional)
                - network: For mobile money (MTN, VODAFONE, AIRTELTIGO)
                - phone_number: For mobile money (can also use payment_method_id)

        Returns:
            PaymentInitiationResult with payment URL or status

        Raises:
            ProviderAPIError: If Flutterwave API returns an error
        """
        metadata = metadata or {}

        # Extract transaction ID (required)
        tx_ref = metadata.get('transaction_id')
        if not tx_ref:
            raise ValidationError(
                'transaction_id',
                'transaction_id is required in metadata'
            )

        # Determine payment type
        is_mobile_money = (
            payment_method_id and payment_method_id.startswith('phone:')
        ) or metadata.get('network')

        if is_mobile_money:
            # Mobile money payment
            return await self._initialize_mobile_money_payment(
                amount, currency, payment_method_id, metadata
            )
        else:
            # Card payment (default)
            return await self._initialize_card_payment(
                amount, currency, metadata
            )

    async def _initialize_card_payment(
        self,
        amount: Decimal,
        currency: Currency,
        metadata: Dict[str, Any]
    ) -> PaymentInitiationResult:
        """Initialize card payment via Flutterwave."""

        try:
            # Build payment data
            payment_data = {
                "tx_ref": metadata['transaction_id'],
                "amount": str(amount),
                "currency": currency.value,
                "payment_options": "card",  # Only card for this method
                "redirect_url": self._get_redirect_url() or "https://example.com/callback",
                "customer": {
                    "email": metadata.get('email', f"{metadata['transaction_id']}@example.com"),
                    "name": metadata.get('name', 'Customer')
                },
                "customizations": {
                    "title": "Wallet Deposit",
                    "description": metadata.get('description', 'Add funds to wallet')
                },
                "meta": {
                    "transaction_id": metadata['transaction_id'],
                    "user_id": metadata.get('user_id')
                }
            }

            # Make API request
            response = await self.http_client.post(
                f"{self.base_url}/payments",
                headers={
                    "Authorization": f"Bearer {self.config.secret_key}",
                    "Content-Type": "application/json"
                },
                json=payment_data
            )

            response.raise_for_status()
            result = response.json()

            if result.get("status") == "success":
                data = result.get("data", {})

                logger.info(f"Flutterwave payment initiated: {data.get('id')}")

                return PaymentInitiationResult(
                    success=True,
                    payment_url=data.get("link"),  # User redirects here to complete payment
                    reference=data.get("id", metadata['transaction_id']),
                    amount=amount,
                    currency=currency,
                    gateway=PaymentProvider.FLUTTERWAVE,
                    metadata={
                        "tx_ref": metadata['transaction_id'],
                        "flw_ref": data.get("flw_ref"),
                        "payment_link": data.get("link")
                    }
                )
            else:
                error_message = result.get("message", "Payment initialization failed")
                logger.error(f"Flutterwave error: {error_message}")

                return PaymentInitiationResult(
                    success=False,
                    reference=metadata['transaction_id'],
                    amount=amount,
                    currency=currency,
                    gateway=PaymentProvider.FLUTTERWAVE,
                    error=error_message
                )

        except httpx.HTTPStatusError as e:
            error_message = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"Flutterwave HTTP error: {error_message}")

            raise ProviderAPIError(
                provider=self.provider_name,
                error_message=error_message,
                error_code=str(e.response.status_code)
            )

        except Exception as e:
            logger.error(f"Flutterwave payment initialization error: {str(e)}")
            raise ProviderAPIError(
                provider=self.provider_name,
                error_message=str(e),
                error_code="initialization_error"
            )

    async def _initialize_mobile_money_payment(
        self,
        amount: Decimal,
        currency: Currency,
        payment_method_id: Optional[str],
        metadata: Dict[str, Any]
    ) -> PaymentInitiationResult:
        """Initialize mobile money payment via Flutterwave."""

        try:
            # Extract phone number
            if payment_method_id and payment_method_id.startswith('phone:'):
                phone_number = payment_method_id.replace('phone:', '')
            else:
                phone_number = metadata.get('phone_number')

            if not phone_number:
                raise ValidationError(
                    'phone_number',
                    'phone_number is required for mobile money payments'
                )

            # Extract network
            network = metadata.get('network', '').upper()
            if not network:
                raise ValidationError(
                    'network',
                    'network is required for mobile money (MTN, VODAFONE, AIRTELTIGO)'
                )

            # Build mobile money charge data
            charge_data = {
                "tx_ref": metadata['transaction_id'],
                "amount": str(amount),
                "currency": currency.value,
                "network": network,  # MTN, VODAFONE, AIRTELTIGO
                "phone_number": phone_number,
                "email": metadata.get('email', f"{metadata['transaction_id']}@example.com"),
                "fullname": metadata.get('name', 'Customer'),
                "meta": {
                    "transaction_id": metadata['transaction_id'],
                    "user_id": metadata.get('user_id')
                }
            }

            # Make API request
            response = await self.http_client.post(
                f"{self.base_url}/charges?type=mobile_money_ghana",
                headers={
                    "Authorization": f"Bearer {self.config.secret_key}",
                    "Content-Type": "application/json"
                },
                json=charge_data
            )

            response.raise_for_status()
            result = response.json()

            if result.get("status") == "success":
                data = result.get("data", {})

                logger.info(f"Flutterwave mobile money charge initiated: {data.get('id')}")

                return PaymentInitiationResult(
                    success=True,
                    payment_url=None,  # Mobile money doesn't need redirect
                    reference=data.get("id", metadata['transaction_id']),
                    amount=amount,
                    currency=currency,
                    gateway=PaymentProvider.FLUTTERWAVE,
                    metadata={
                        "tx_ref": metadata['transaction_id'],
                        "flw_ref": data.get("flw_ref"),
                        "status": data.get("status"),
                        "network": network,
                        "phone_number": phone_number
                    }
                )
            else:
                error_message = result.get("message", "Mobile money charge failed")
                logger.error(f"Flutterwave mobile money error: {error_message}")

                return PaymentInitiationResult(
                    success=False,
                    reference=metadata['transaction_id'],
                    amount=amount,
                    currency=currency,
                    gateway=PaymentProvider.FLUTTERWAVE,
                    error=error_message
                )

        except httpx.HTTPStatusError as e:
            error_message = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"Flutterwave HTTP error: {error_message}")

            raise ProviderAPIError(
                provider=self.provider_name,
                error_message=error_message,
                error_code=str(e.response.status_code)
            )

        except Exception as e:
            logger.error(f"Flutterwave mobile money error: {str(e)}")
            raise ProviderAPIError(
                provider=self.provider_name,
                error_message=str(e),
                error_code="mobile_money_error"
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
        Verify Flutterwave webhook signature.

        Flutterwave uses SHA256 hash of webhook secret.

        Args:
            payload: Parsed webhook payload
            signature: verif-hash header value
            raw_payload: Not used for Flutterwave
            headers: Request headers

        Returns:
            True if signature is valid
        """
        if not signature:
            logger.error("Flutterwave webhook signature not provided")
            return False

        if not self.config.webhook_secret:
            logger.error("Flutterwave webhook_secret not configured")
            return False

        try:
            # Flutterwave verification: SHA256 hash of webhook secret
            expected_hash = hashlib.sha256(
                self.config.webhook_secret.encode()
            ).hexdigest()

            is_valid = signature == expected_hash

            if is_valid:
                logger.info("Flutterwave webhook signature verified")
            else:
                logger.warning("Invalid Flutterwave webhook signature")

            return is_valid

        except Exception as e:
            logger.error(f"Flutterwave webhook verification error: {str(e)}")
            return False

    async def process_webhook(
        self,
        payload: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Process Flutterwave webhook event.

        Args:
            payload: Verified webhook payload

        Returns:
            Tuple of (success, transaction_id, provider_data)

        Flutterwave Webhook Structure:
        {
            "event": "charge.completed",
            "data": {
                "id": 12345,
                "tx_ref": "our_transaction_id",
                "flw_ref": "FLW_REF",
                "amount": 100,
                "currency": "GHS",
                "status": "successful",
                "payment_type": "mobilemoney" or "card"
            }
        }
        """
        try:
            # Extract event type
            event = payload.get('event', '')

            # Extract data
            data = payload.get('data', {})
            status = data.get('status', '').lower()
            tx_ref = data.get('tx_ref')  # Our transaction ID

            if not tx_ref:
                logger.error("No tx_ref in Flutterwave webhook")
                return True, None, None

            if status == 'successful':
                # Payment succeeded
                provider_data = {
                    'provider_id': str(data.get('id')),
                    'flw_ref': data.get('flw_ref'),
                    'amount': data.get('amount'),
                    'currency': data.get('currency'),
                    'status': 'completed',
                    'payment_type': data.get('payment_type'),
                    'charged_amount': data.get('charged_amount'),
                    'app_fee': data.get('app_fee'),
                    'merchant_fee': data.get('merchant_fee')
                }

                logger.info(f"Flutterwave payment succeeded: {tx_ref}")
                return True, tx_ref, provider_data

            elif status == 'failed':
                # Payment failed
                provider_data = {
                    'provider_id': str(data.get('id')),
                    'flw_ref': data.get('flw_ref'),
                    'status': 'failed',
                    'failure_reason': data.get('narration', 'Payment failed')
                }

                logger.warning(f"Flutterwave payment failed: {tx_ref}")
                return False, tx_ref, provider_data

            else:
                # Other status (pending, etc.)
                logger.info(f"Flutterwave webhook status '{status}' for {tx_ref}")
                return True, None, {'status': status}

        except Exception as e:
            logger.error(f"Flutterwave webhook processing error: {str(e)}")
            return False, None, {'error': str(e)}

    # ========================================================================
    # TRANSACTION MANAGEMENT
    # ========================================================================

    async def get_transaction_status(
        self,
        provider_transaction_id: str
    ) -> Dict[str, Any]:
        """
        Get Flutterwave transaction status.

        Args:
            provider_transaction_id: Flutterwave transaction ID

        Returns:
            Transaction status details
        """
        try:
            response = await self.http_client.get(
                f"{self.base_url}/transactions/{provider_transaction_id}/verify",
                headers={
                    "Authorization": f"Bearer {self.config.secret_key}"
                }
            )

            response.raise_for_status()
            result = response.json()

            if result.get("status") == "success":
                data = result.get("data", {})

                return {
                    'id': str(data.get('id')),
                    'tx_ref': data.get('tx_ref'),
                    'flw_ref': data.get('flw_ref'),
                    'status': data.get('status'),
                    'amount': data.get('amount'),
                    'currency': data.get('currency'),
                    'payment_type': data.get('payment_type'),
                    'charged_amount': data.get('charged_amount'),
                    'created_at': data.get('created_at')
                }
            else:
                raise ProviderAPIError(
                    provider=self.provider_name,
                    error_message=result.get("message", "Failed to verify transaction"),
                    error_code="verification_error"
                )

        except httpx.HTTPStatusError as e:
            logger.error(f"Flutterwave verification error: {e.response.text}")
            raise ProviderAPIError(
                provider=self.provider_name,
                error_message=f"HTTP {e.response.status_code}: {e.response.text}",
                error_code=str(e.response.status_code)
            )

        except Exception as e:
            logger.error(f"Flutterwave status check error: {str(e)}")
            raise ProviderAPIError(
                provider=self.provider_name,
                error_message=str(e),
                error_code="status_check_error"
            )

    async def refund_payment(
        self,
        provider_transaction_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Refund a Flutterwave payment.

        Args:
            provider_transaction_id: Flutterwave transaction ID
            amount: Amount to refund (None = full refund)
            reason: Refund reason

        Returns:
            Refund result with refund_id and status
        """
        try:
            # Build refund data
            refund_data = {
                "id": provider_transaction_id
            }

            if amount:
                refund_data["amount"] = str(amount)

            # Make refund request
            response = await self.http_client.post(
                f"{self.base_url}/transactions/{provider_transaction_id}/refund",
                headers={
                    "Authorization": f"Bearer {self.config.secret_key}",
                    "Content-Type": "application/json"
                },
                json=refund_data
            )

            response.raise_for_status()
            result = response.json()

            if result.get("status") == "success":
                data = result.get("data", {})

                logger.info(f"Flutterwave refund created: {data.get('id')}")

                return {
                    'success': True,
                    'refund_id': str(data.get('id')),
                    'amount': data.get('amount_refunded'),
                    'status': data.get('status'),
                    'created_at': data.get('created_at')
                }
            else:
                error_message = result.get("message", "Refund failed")
                logger.error(f"Flutterwave refund error: {error_message}")

                return {
                    'success': False,
                    'error': error_message
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"Flutterwave refund HTTP error: {e.response.text}")
            return {
                'success': False,
                'error': f"HTTP {e.response.status_code}: {e.response.text}"
            }

        except Exception as e:
            logger.error(f"Flutterwave refund error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    # ========================================================================
    # HEALTH CHECK
    # ========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Flutterwave API connectivity.

        Returns:
            Health status
        """
        try:
            # Try to fetch balance (simple API call)
            response = await self.http_client.get(
                f"{self.base_url}/balances",
                headers={
                    "Authorization": f"Bearer {self.config.secret_key}"
                }
            )

            response.raise_for_status()
            result = response.json()

            if result.get("status") == "success":
                return {
                    "provider": self.provider_name,
                    "status": "healthy",
                    "message": "Successfully connected to Flutterwave API",
                    "test_mode": self.is_test_mode
                }
            else:
                return {
                    "provider": self.provider_name,
                    "status": "unhealthy",
                    "message": result.get("message", "Unknown error"),
                    "test_mode": self.is_test_mode
                }

        except httpx.HTTPStatusError as e:
            return {
                "provider": self.provider_name,
                "status": "unhealthy",
                "message": f"HTTP {e.response.status_code}: {e.response.text}",
                "test_mode": self.is_test_mode
            }

        except Exception as e:
            return {
                "provider": self.provider_name,
                "status": "unhealthy",
                "message": f"Flutterwave API error: {str(e)}",
                "test_mode": self.is_test_mode
            }

    # ========================================================================
    # CLEANUP
    # ========================================================================

    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()
        logger.info("Flutterwave provider HTTP client closed")
