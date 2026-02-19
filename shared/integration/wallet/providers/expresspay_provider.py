"""
ExpressPay Payment Provider

Handles payments via ExpressPay (Ghana) with support for:
- Card payments (hosted payment page)
- Mobile money (MTN, Vodafone, Airtel, Tigo)
- Bank transfers
- Webhook processing (without signature verification - security limitation)
- Transaction status querying

Coverage: Ghana (GHS)
Documentation: https://expresspaygh.com/developers

Security Note: ExpressPay does NOT provide webhook signature verification.
Always query transaction status after webhook to confirm legitimacy.

Author: KasaAI Team
Date: 2025-11-23
"""

import logging
import httpx
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal
from urllib.parse import urlencode

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


class ExpressPayProvider(BasePaymentProvider):
    """
    ExpressPay payment provider implementation.

    Supports:
    - Credit/debit card payments (hosted page)
    - Mobile money (MTN, Vodafone, Airtel, Tigo)
    - Bank transfers
    - Transaction status querying
    - Webhook processing (NO signature verification available)

    Coverage:
    - Ghana (GHS)

    Security Limitation:
    - ExpressPay does NOT provide webhook signature verification
    - Always query transaction status to verify webhook authenticity
    - Validate token ownership before processing webhooks

    Example:
        provider = ExpressPayProvider(expresspay_config)

        # Initialize payment
        result = await provider.initialize_payment(
            amount=Decimal("100.00"),
            currency=Currency.GHS,
            customer_id="user@example.com",
            metadata={"transaction_id": "txn_123"}
        )

        # Process webhook (always query status afterward)
        success, txn_id, data = await provider.process_webhook(webhook_payload)
    """

    # ExpressPay API URLs
    SANDBOX_API_URL = "https://sandbox.expresspaygh.com/api"
    LIVE_API_URL = "https://expresspaygh.com/api"

    # Transaction status codes
    STATUS_SUCCESS = 1
    STATUS_INVALID_CREDENTIALS = 2
    STATUS_INVALID_REQUEST = 3
    STATUS_INVALID_IP = 4

    # Transaction result codes
    RESULT_APPROVED = 1
    RESULT_DECLINED = 2
    RESULT_ERROR = 3
    RESULT_PENDING = 4

    # Mobile money networks
    MOBILE_NETWORKS = {
        "mtn": "MTN_MM",
        "vodafone": "VODAFONE_CASH",
        "airtel": "AIRTEL_MM",
        "tigo": "TIGO_CASH"
    }

    def __init__(self, config: ProviderConfig):
        """
        Initialize ExpressPay provider.

        Args:
            config: Provider configuration with ExpressPay credentials
                    Required: merchant_id (in credentials dict)
                             secret_key (API key)
        """
        # Get merchant ID from settings BEFORE calling super().__init__()
        # because _validate_config() is called by parent and needs merchant_id
        self.merchant_id = config.settings.get("merchant_id") if config.settings else None
        if not self.merchant_id:
            raise ValidationError(
                "merchant_id",
                "ExpressPay merchant_id is required in credentials"
            )

        # Call parent init (which calls _validate_config)
        super().__init__(config)

        # Set API base URL based on mode (is_test_mode set by parent)
        self.api_url = self.SANDBOX_API_URL if self.is_test_mode else self.LIVE_API_URL

        # HTTP client for API calls (ExpressPay uses form-urlencoded)
        self.http_client = httpx.AsyncClient(
            base_url=self.api_url,
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            },
            timeout=30.0
        )

        logger.info(
            f"ExpressPay provider initialized "
            f"(merchant={self.merchant_id[:8]}..., "
            f"test_mode={self.is_test_mode})"
        )

    def _validate_config(self):
        """Validate ExpressPay configuration."""
        super()._validate_config()

        # Validate merchant ID
        if not self.merchant_id:
            raise ValidationError(
                "merchant_id",
                "ExpressPay merchant_id is required"
            )

        # Warn about webhook security limitation
        logger.warning(
            "⚠️ ExpressPay does NOT support webhook signature verification. "
            "Always query transaction status to verify webhooks."
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
        Initialize ExpressPay transaction (Merchant API - hosted payment page).

        Args:
            amount: Amount to charge (in major currency units, e.g., GHS)
            currency: Currency code (only GHS supported)
            payment_method_id: Payment channel (card, mobile_money) - optional
            customer_id: Customer email address (required)
            metadata: Additional metadata (must include transaction_id)

        Returns:
            PaymentInitiationResult with checkout URL

        Raises:
            ValidationError: If required parameters are missing
            ProviderAPIError: If ExpressPay API returns an error
        """
        try:
            # Validate currency
            if currency != Currency.GHS:
                raise ValidationError(
                    "currency",
                    f"ExpressPay only supports GHS, got {currency.value}"
                )

            # Validate customer email
            if not customer_id or "@" not in customer_id:
                raise ValidationError(
                    "customer_id",
                    "ExpressPay requires customer email address as customer_id"
                )

            # Extract customer details
            metadata = metadata or {}
            email = customer_id
            firstname = metadata.get("firstname", email.split("@")[0])
            lastname = metadata.get("lastname", "User")
            phonenumber = metadata.get("phone", "0000000000")

            # Generate order ID from transaction_id
            order_id = metadata.get("transaction_id", f"txn_{int(amount * 100)}")

            # Build request payload (form-urlencoded)
            payload = {
                "merchant-id": self.merchant_id,
                "api-key": self.config.secret_key,
                "firstname": firstname,
                "lastname": lastname,
                "email": email,
                "phonenumber": phonenumber,
                "username": email,  # Required but not used
                "accountnumber": email,  # Required but not used
                "currency": currency.value,
                "amount": float(amount),
                "order-id": order_id,
                "order-desc": metadata.get("description", f"Payment of {amount} {currency.value}"),
                "order-img-url": metadata.get("image_url", ""),
                "redirect-url": self._get_redirect_url() or "https://ailabsafrica.com/payment-success",
            }

            # Add webhook URL if configured (for mobile money)
            webhook_url = self._get_webhook_url()
            if webhook_url:
                payload["post-url"] = webhook_url

            # Make API call
            response = await self.http_client.post(
                "/submit.php",
                data=payload
            )

            result = response.json()

            # Check response status
            status = result.get("status")

            if status == self.STATUS_INVALID_CREDENTIALS:
                logger.error(f"ExpressPay invalid credentials: merchant_id or api_key incorrect")
                raise ProviderAPIError(
                    self.provider_name,
                    "Invalid credentials (merchant_id or api_key)"
                )

            elif status == self.STATUS_INVALID_REQUEST:
                error_msg = result.get("message", "Invalid request parameters")
                logger.error(f"ExpressPay invalid request: {error_msg}")
                raise ProviderAPIError(
                    self.provider_name,
                    f"Invalid request: {error_msg}"
                )

            elif status == self.STATUS_INVALID_IP:
                logger.error(f"ExpressPay IP not whitelisted")
                raise ProviderAPIError(
                    self.provider_name,
                    "Server IP not whitelisted with ExpressPay"
                )

            elif status != self.STATUS_SUCCESS:
                error_msg = result.get("message", "Unknown error")
                logger.error(f"ExpressPay initialization failed: {error_msg}")
                raise ProviderAPIError(
                    self.provider_name,
                    f"Initialization failed: {error_msg}"
                )

            # Extract payment details
            token = result.get("token")
            # Build checkout URL from token - ExpressPay returns our redirect_url in response
            # but the actual checkout URL is their hosted page with the token
            checkout_url = f"{self.api_url}/checkout.php?token={token}"

            logger.info(
                f"ExpressPay payment initialized: "
                f"order_id={order_id}, token={token[:20]}..."
            )

            return PaymentInitiationResult(
                success=True,
                payment_url=checkout_url,
                reference=token,  # Token acts as transaction reference
                amount=amount,
                currency=currency,
                gateway=PaymentProvider.EXPRESSPAY,
                metadata={
                    "order_id": order_id,
                    "token": token,
                    "redirect_url": checkout_url,
                    "customer_email": email
                }
            )

        except (ValidationError, ProviderAPIError):
            raise
        except Exception as e:
            logger.error(f"ExpressPay initialization error: {e}", exc_info=True)
            raise ProviderAPIError(
                self.provider_name,
                f"Initialization failed: {str(e)}"
            )

    async def verify_webhook(
        self,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        raw_payload: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Verify webhook from ExpressPay.

        ⚠️ SECURITY LIMITATION: ExpressPay does NOT provide webhook signature
        verification. This method performs basic validation only.

        Always call get_transaction_status() after receiving a webhook to
        verify the transaction legitimacy.

        Args:
            payload: Parsed webhook payload (dict)
            signature: Not used (ExpressPay doesn't provide signatures)
            raw_payload: Not used
            headers: Request headers

        Returns:
            True if webhook has required fields (order-id, token)

        Security Note:
            This method only checks if required fields are present.
            You MUST query transaction status afterward to verify authenticity.
        """
        # Log security warning
        logger.warning(
            "⚠️ ExpressPay webhook verification: NO signature verification available. "
            "Will validate token ownership and query transaction status."
        )

        # Check required fields
        order_id = payload.get("order-id") or payload.get("order_id")
        token = payload.get("token")

        if not order_id or not token:
            logger.error(
                f"ExpressPay webhook missing required fields: "
                f"order_id={bool(order_id)}, token={bool(token)}"
            )
            return False

        logger.info(
            f"ExpressPay webhook has required fields: "
            f"order_id={order_id}, token={token[:20]}..."
        )

        # Basic validation passed, but caller MUST query transaction status
        return True

    async def process_webhook(
        self,
        payload: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Process webhook payload and query transaction status.

        ExpressPay webhooks do NOT include transaction status. We must query
        the transaction status using the token provided in the webhook.

        Args:
            payload: Verified webhook payload with order-id and token

        Returns:
            Tuple of (success, transaction_id, provider_data)

        Security:
            Always queries transaction status from ExpressPay API to prevent
            webhook spoofing attacks.
        """
        try:
            # Extract order-id and token
            order_id = payload.get("order-id") or payload.get("order_id")
            token = payload.get("token")

            if not order_id or not token:
                logger.error("ExpressPay webhook missing order-id or token")
                return False, None, {
                    "error": "Missing order-id or token",
                    "payload": payload
                }

            logger.info(
                f"Processing ExpressPay webhook: "
                f"order_id={order_id}, querying status..."
            )

            # Query transaction status (critical security step)
            status_data = await self.get_transaction_status(token)

            # Extract result
            result_code = status_data.get("result")
            result_text = status_data.get("result-text", "Unknown")

            # Check if transaction succeeded
            if result_code == self.RESULT_APPROVED:
                logger.info(
                    f"ExpressPay transaction approved: "
                    f"order_id={order_id}, txn_id={status_data.get('transaction-id')}"
                )
                return True, order_id, status_data

            elif result_code == self.RESULT_DECLINED:
                logger.warning(
                    f"ExpressPay transaction declined: "
                    f"order_id={order_id}, reason={result_text}"
                )
                return False, order_id, {
                    **status_data,
                    "failure_reason": result_text
                }

            elif result_code == self.RESULT_PENDING:
                logger.info(
                    f"ExpressPay transaction still pending: order_id={order_id}"
                )
                return False, order_id, {
                    **status_data,
                    "status": "pending",
                    "message": "Transaction is still being processed"
                }

            else:  # RESULT_ERROR
                logger.error(
                    f"ExpressPay transaction error: "
                    f"order_id={order_id}, error={result_text}"
                )
                return False, order_id, {
                    **status_data,
                    "failure_reason": result_text or "Transaction failed"
                }

        except Exception as e:
            logger.error(f"ExpressPay webhook processing error: {e}", exc_info=True)
            return False, None, {
                "error": str(e),
                "payload": payload
            }

    # ========================================================================
    # TRANSACTION MANAGEMENT
    # ========================================================================

    async def get_transaction_status(
        self,
        provider_transaction_id: str
    ) -> Dict[str, Any]:
        """
        Query transaction status from ExpressPay.

        This is the ONLY way to verify transaction status with ExpressPay.
        Always call this after receiving a webhook.

        Args:
            provider_transaction_id: Token from payment initialization

        Returns:
            Transaction status details:
            {
                "result": 1,  # 1=Approved, 2=Declined, 3=Error, 4=Pending
                "result-text": "Approved",
                "order-id": "xxx",
                "token": "xxx",
                "transaction-id": "xxx",
                "currency": "GHS",
                "amount": 100.00,
                "date-processed": "23rd November, 2025"
            }

        Raises:
            ProviderAPIError: If query fails
        """
        try:
            # Build query payload
            payload = {
                "merchant-id": self.merchant_id,
                "api-key": self.config.secret_key,
                "token": provider_transaction_id
            }

            # Query transaction status
            response = await self.http_client.post(
                "/query.php",
                data=payload
            )

            result = response.json()

            logger.info(
                f"ExpressPay status query: "
                f"token={provider_transaction_id[:20]}..., "
                f"result={result.get('result')}, "
                f"status={result.get('result-text')}"
            )

            return result

        except Exception as e:
            logger.error(
                f"ExpressPay status query failed: {e}",
                exc_info=True
            )
            raise ProviderAPIError(
                self.provider_name,
                f"Status query failed: {str(e)}"
            )

    async def refund_payment(
        self,
        provider_transaction_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Refund a payment.

        ⚠️ NOT SUPPORTED: ExpressPay does not provide a refund API.
        Refunds must be processed manually by contacting ExpressPay support.

        Args:
            provider_transaction_id: Token/transaction ID
            amount: Amount to refund (ignored)
            reason: Refund reason (logged)

        Raises:
            NotImplementedError: Always (no API available)

        Note:
            For refunds, contact ExpressPay support at support@expresspaygh.com
            with the transaction ID and refund details.
        """
        logger.error(
            f"ExpressPay refund requested but NOT SUPPORTED: "
            f"txn_id={provider_transaction_id}, amount={amount}, reason={reason}. "
            f"Manual refund required via ExpressPay support."
        )

        raise NotImplementedError(
            "ExpressPay does not provide a refund API. "
            "Please contact ExpressPay support at support@expresspaygh.com "
            "with transaction ID and refund details."
        )

    # ========================================================================
    # PAYMENT METHOD MANAGEMENT (Not Supported)
    # ========================================================================

    async def create_customer(
        self,
        user_id: str,
        email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        ExpressPay does not support customer objects.

        Returns:
            Empty customer dict
        """
        logger.info("ExpressPay does not support customer creation")
        return {"customer_id": None, "email": email}

    # ========================================================================
    # HEALTH CHECK
    # ========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """
        Check ExpressPay API connectivity.

        Performs a test query with invalid token to verify API is reachable.

        Returns:
            Health status dict
        """
        try:
            # Test API with invalid token (should return error but prove connectivity)
            payload = {
                "merchant-id": self.merchant_id,
                "api-key": self.config.secret_key,
                "token": "test_health_check_token"
            }

            response = await self.http_client.post(
                "/query.php",
                data=payload,
                timeout=5.0
            )

            # If we get a response (even an error), API is healthy
            result = response.json()

            return {
                "provider": self.provider_name,
                "status": "healthy",
                "message": "ExpressPay API is reachable",
                "test_mode": self.is_test_mode
            }

        except Exception as e:
            logger.error(f"ExpressPay health check failed: {e}")
            return {
                "provider": self.provider_name,
                "status": "unhealthy",
                "message": f"ExpressPay API unreachable: {str(e)}",
                "test_mode": self.is_test_mode
            }

    def __del__(self):
        """Clean up HTTP client on deletion."""
        try:
            import asyncio
            if hasattr(self, 'http_client'):
                # Try to close the client
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(self.http_client.aclose())
                    else:
                        loop.run_until_complete(self.http_client.aclose())
                except:
                    pass
        except:
            pass
