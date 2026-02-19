"""
M-Pesa Payment Provider (Safaricom - Kenya)

Handles mobile money payments via M-Pesa Daraja API with support for:
- STK Push (Lipa Na M-Pesa Online) - customer-initiated payments
- C2B (Customer to Business) payments
- B2C (Business to Customer) for withdrawals
- Transaction status queries
- Callback/webhook processing
- Balance queries

Coverage: Kenya (KES), Tanzania (TZS), and other M-Pesa markets

Author: KasaAI Team
Date: 2025-10-27
"""

import logging
import httpx
import base64
from datetime import datetime
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


class MPesaProvider(BasePaymentProvider):
    """
    M-Pesa (Safaricom) payment provider implementation.

    Supports:
    - STK Push (Lipa Na M-Pesa Online) for deposits
    - C2B payments (customer-initiated)
    - B2C payments for withdrawals
    - Transaction status queries
    - Callback/webhook processing
    - Balance queries

    Coverage:
    - Kenya (KES) - Primary market
    - Tanzania (TZS)
    - Other M-Pesa markets

    Example:
        provider = MPesaProvider(mpesa_config)

        # Initialize STK Push payment
        result = await provider.initialize_payment(
            amount=Decimal("100.00"),
            currency=Currency.KES,
            metadata={
                "phone_number": "254712345678",
                "account_reference": "Invoice123"
            }
        )

        # Process callback
        success, txn_id, data = await provider.process_webhook(callback_data)
    """

    # M-Pesa API URLs
    SANDBOX_URL = "https://sandbox.safaricom.co.ke"
    PRODUCTION_URL = "https://api.safaricom.co.ke"

    def __init__(self, config: ProviderConfig):
        """
        Initialize M-Pesa provider.

        Args:
            config: Provider configuration with M-Pesa credentials
                - api_key: Consumer Key
                - secret_key: Consumer Secret
                - Additional required in settings:
                    - business_short_code: Till/Paybill number
                    - passkey: Lipa Na M-Pesa passkey
                    - initiator_name: For B2C
                    - security_credential: For B2C
        """
        # Extract M-Pesa specific config BEFORE calling super().__init__()
        # because _validate_config() is called in parent's __init__()
        settings = config.settings or {}
        self.business_short_code = settings.get("business_short_code")
        self.passkey = settings.get("passkey")
        self.initiator_name = settings.get("initiator_name")
        self.security_credential = settings.get("security_credential")

        super().__init__(config)

        # Set API base URL
        self.api_url = self.SANDBOX_URL if self.is_test_mode else self.PRODUCTION_URL

        # HTTP client
        self.http_client = httpx.AsyncClient(
            base_url=self.api_url,
            timeout=30.0
        )

        # Access token (will be fetched on first request)
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

        logger.info(f"M-Pesa provider initialized (test_mode={self.is_test_mode})")

    def _validate_config(self):
        """Validate M-Pesa configuration."""
        super()._validate_config()

        if not self.business_short_code:
            raise ValidationError(
                'business_short_code',
                'M-Pesa business_short_code is required in metadata'
            )

        if not self.passkey:
            logger.warning("M-Pesa passkey not configured. STK Push will fail.")

    # ========================================================================
    # AUTHENTICATION
    # ========================================================================

    async def _get_access_token(self) -> str:
        """
        Get OAuth access token from M-Pesa.

        Returns:
            Access token string

        Raises:
            ProviderAPIError: If authentication fails
        """
        # Check if we have a valid token
        if self._access_token and self._token_expiry:
            if datetime.utcnow() < self._token_expiry:
                return self._access_token

        try:
            # Create Basic Auth credentials
            credentials = f"{self.config.api_key}:{self.config.secret_key}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()

            # Request access token
            response = await self.http_client.get(
                "/oauth/v1/generate?grant_type=client_credentials",
                headers={
                    "Authorization": f"Basic {encoded_credentials}"
                }
            )

            if response.status_code != 200:
                logger.error(f"M-Pesa auth failed: {response.text}")
                raise ProviderAPIError(
                    provider=self.provider_name,
                    error_message="Failed to authenticate with M-Pesa",
                    error_code=str(response.status_code)
                )

            result = response.json()
            self._access_token = result["access_token"]

            # Token expires in 1 hour, we'll refresh 5 minutes early
            from datetime import timedelta
            self._token_expiry = datetime.utcnow() + timedelta(seconds=3300)

            logger.info("M-Pesa access token obtained")
            return self._access_token

        except httpx.HTTPError as e:
            logger.error(f"M-Pesa auth HTTP error: {str(e)}")
            raise ProviderAPIError(
                provider=self.provider_name,
                error_message=f"HTTP error during authentication: {str(e)}",
                error_code="auth_error"
            )

    def _generate_password(self, timestamp: str) -> str:
        """
        Generate M-Pesa password for STK Push.

        Args:
            timestamp: Timestamp in format YYYYMMDDHHmmss

        Returns:
            Base64 encoded password
        """
        password_str = f"{self.business_short_code}{self.passkey}{timestamp}"
        return base64.b64encode(password_str.encode()).decode()

    # ========================================================================
    # PAYMENT PROCESSING - STK PUSH
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
        Initialize M-Pesa STK Push (Lipa Na M-Pesa Online).

        Args:
            amount: Amount to charge
            currency: Currency (should be KES for Kenya)
            payment_method_id: Not used for M-Pesa
            customer_id: Not used for M-Pesa
            metadata: Required fields:
                - phone_number: Customer phone number (254XXXXXXXXX)
                - account_reference: Reference (e.g., account number)
                - transaction_desc: Description (optional)

        Returns:
            PaymentInitiationResult with checkout request ID

        Raises:
            ValidationError: If required fields are missing
            ProviderAPIError: If M-Pesa API returns an error
        """
        if not metadata or "phone_number" not in metadata:
            raise ValidationError(
                "phone_number",
                "Phone number is required for M-Pesa STK Push"
            )

        phone_number = metadata["phone_number"]
        account_reference = metadata.get("account_reference", "Payment")
        transaction_desc = metadata.get("transaction_desc", "Payment")

        # Ensure phone number is in correct format (254XXXXXXXXX)
        if phone_number.startswith("0"):
            phone_number = "254" + phone_number[1:]
        elif phone_number.startswith("+254"):
            phone_number = phone_number[1:]
        elif not phone_number.startswith("254"):
            phone_number = "254" + phone_number

        try:
            # Get access token
            token = await self._get_access_token()

            # Generate timestamp and password
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            password = self._generate_password(timestamp)

            # Convert amount to integer (M-Pesa doesn't use decimals)
            amount_int = int(amount)

            # Build STK Push request
            payload = {
                "BusinessShortCode": self.business_short_code,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": amount_int,
                "PartyA": phone_number,
                "PartyB": self.business_short_code,
                "PhoneNumber": phone_number,
                "CallBackURL": self._get_redirect_url(),  # Callback URL
                "AccountReference": account_reference,
                "TransactionDesc": transaction_desc
            }

            # Send STK Push request
            response = await self.http_client.post(
                "/mpesa/stkpush/v1/processrequest",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )

            result = response.json()

            # Check response code
            if result.get("ResponseCode") != "0":
                error_msg = result.get("ResponseDescription", "STK Push failed")
                logger.error(f"M-Pesa STK Push failed: {error_msg}")
                raise ProviderAPIError(
                    provider=self.provider_name,
                    error_message=error_msg,
                    error_code=result.get("ResponseCode", "unknown")
                )

            checkout_request_id = result["CheckoutRequestID"]
            merchant_request_id = result["MerchantRequestID"]

            logger.info(f"M-Pesa STK Push initiated: {checkout_request_id}")

            return PaymentInitiationResult(
                success=True,
                payment_url=None,  # No URL for STK Push (push to phone)
                reference=checkout_request_id,
                amount=amount,
                currency=currency,
                gateway=PaymentProvider.MPESA,
                metadata={
                    "checkout_request_id": checkout_request_id,
                    "merchant_request_id": merchant_request_id,
                    "phone_number": phone_number,
                    "message": "STK Push sent to customer's phone"
                }
            )

        except httpx.HTTPError as e:
            logger.error(f"M-Pesa HTTP error: {str(e)}")
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
        Verify M-Pesa callback.

        M-Pesa doesn't use signature verification - callbacks are verified
        by ensuring they come from the callback URL you configured.

        Args:
            payload: Callback payload
            signature: Not used for M-Pesa
            raw_payload: Not used for M-Pesa
            headers: Not used for M-Pesa

        Returns:
            True (M-Pesa doesn't use signature verification)
        """
        # M-Pesa callbacks should be verified by:
        # 1. Checking the callback URL matches what you configured
        # 2. Validating the payload structure
        # 3. Optionally checking IP whitelist

        # For now, we'll just validate the payload has required fields
        if "Body" in payload and "stkCallback" in payload["Body"]:
            logger.info("M-Pesa STK callback received")
            return True

        logger.warning("Invalid M-Pesa callback structure")
        return False

    async def process_webhook(
        self,
        payload: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Process M-Pesa STK Push callback.

        Args:
            payload: Callback payload from M-Pesa

        Returns:
            Tuple of (success, transaction_id, provider_data)

        Callback Structure:
        {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "...",
                    "CheckoutRequestID": "...",
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 1},
                            {"Name": "MpesaReceiptNumber", "Value": "LHG31AA5TX"},
                            {"Name": "TransactionDate", "Value": 20191219102115},
                            {"Name": "PhoneNumber", "Value": 254708374149}
                        ]
                    }
                }
            }
        }
        """
        try:
            callback = payload.get("Body", {}).get("stkCallback", {})

            # If callback is empty, it's malformed
            if not callback:
                logger.error("Malformed M-Pesa callback - missing stkCallback")
                return False, None, None

            result_code = callback.get("ResultCode")
            result_desc = callback.get("ResultDesc", "")
            checkout_request_id = callback.get("CheckoutRequestID")

            # Result code 0 means success
            if result_code == 0:
                # Extract callback metadata
                items = callback.get("CallbackMetadata", {}).get("Item", [])
                metadata_dict = {item["Name"]: item.get("Value") for item in items}

                amount = Decimal(str(metadata_dict.get("Amount", 0)))
                mpesa_receipt = metadata_dict.get("MpesaReceiptNumber", "")
                phone_number = str(metadata_dict.get("PhoneNumber", ""))
                transaction_date = str(metadata_dict.get("TransactionDate", ""))

                provider_data = {
                    "provider_id": mpesa_receipt,
                    "checkout_request_id": checkout_request_id,
                    "amount": amount,
                    "currency": "KES",
                    "status": "completed",
                    "mpesa_receipt_number": mpesa_receipt,
                    "phone_number": phone_number,
                    "transaction_date": transaction_date,
                    "result_desc": result_desc
                }

                logger.info(f"M-Pesa payment succeeded: {mpesa_receipt}")

                # Use checkout_request_id as transaction_id lookup
                return True, checkout_request_id, provider_data

            else:
                # Payment failed
                provider_data = {
                    "provider_id": checkout_request_id,
                    "checkout_request_id": checkout_request_id,
                    "failure_reason": result_desc,
                    "status": "failed",
                    "result_code": result_code
                }

                logger.warning(f"M-Pesa payment failed: {checkout_request_id} - {result_desc}")
                return False, checkout_request_id, provider_data

        except Exception as e:
            logger.error(f"Error processing M-Pesa callback: {str(e)}")
            return False, None, None

    # ========================================================================
    # TRANSACTION MANAGEMENT
    # ========================================================================

    async def get_transaction_status(
        self,
        provider_transaction_id: str
    ) -> Dict[str, Any]:
        """
        Query M-Pesa transaction status.

        Args:
            provider_transaction_id: CheckoutRequestID from STK Push

        Returns:
            Transaction status details
        """
        try:
            # Get access token
            token = await self._get_access_token()

            # Generate timestamp and password
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            password = self._generate_password(timestamp)

            # Build query request
            payload = {
                "BusinessShortCode": self.business_short_code,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": provider_transaction_id
            }

            # Query transaction status
            response = await self.http_client.post(
                "/mpesa/stkpushquery/v1/query",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )

            result = response.json()

            return {
                "checkout_request_id": result.get("CheckoutRequestID"),
                "merchant_request_id": result.get("MerchantRequestID"),
                "result_code": result.get("ResultCode"),
                "result_desc": result.get("ResultDesc"),
                "status": "success" if result.get("ResultCode") == "0" else "failed"
            }

        except httpx.HTTPError as e:
            logger.error(f"Failed to query M-Pesa transaction: {str(e)}")
            raise ProviderAPIError(
                provider=self.provider_name,
                error_message=f"Failed to query transaction: {str(e)}",
                error_code="query_error"
            )

    async def refund_payment(
        self,
        provider_transaction_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Refund M-Pesa payment (reversal).

        Note: M-Pesa reversal is complex and requires special permissions.
        This is a placeholder implementation.

        Args:
            provider_transaction_id: M-Pesa receipt number
            amount: Amount to refund
            reason: Refund reason

        Returns:
            Refund result
        """
        # M-Pesa refunds/reversals require:
        # 1. Initiator credentials
        # 2. API user with reversal permissions
        # 3. Certificate for encrypting security credential
        # This is typically done manually through M-Pesa portal

        logger.warning(
            "M-Pesa refunds require manual processing through Safaricom portal. "
            f"Transaction: {provider_transaction_id}"
        )

        return {
            "success": False,
            "error": "M-Pesa refunds must be processed manually through Safaricom portal",
            "transaction_id": provider_transaction_id,
            "contact": "Contact Safaricom support for refund processing"
        }

    # ========================================================================
    # B2C PAYMENTS (WITHDRAWALS)
    # ========================================================================

    async def initiate_b2c_payment(
        self,
        phone_number: str,
        amount: Decimal,
        occasion: str = "Withdrawal",
        remarks: str = "Payment"
    ) -> Dict[str, Any]:
        """
        Initiate B2C (Business to Customer) payment for withdrawals.

        Args:
            phone_number: Customer phone number (254XXXXXXXXX)
            amount: Amount to send
            occasion: Payment occasion
            remarks: Payment remarks

        Returns:
            B2C transaction result
        """
        if not self.initiator_name or not self.security_credential:
            return {
                "success": False,
                "error": "B2C not configured. Need initiator_name and security_credential"
            }

        try:
            # Get access token
            token = await self._get_access_token()

            # Ensure phone number format
            if phone_number.startswith("0"):
                phone_number = "254" + phone_number[1:]
            elif phone_number.startswith("+254"):
                phone_number = phone_number[1:]

            # Build B2C request
            payload = {
                "InitiatorName": self.initiator_name,
                "SecurityCredential": self.security_credential,
                "CommandID": "BusinessPayment",
                "Amount": int(amount),
                "PartyA": self.business_short_code,
                "PartyB": phone_number,
                "Remarks": remarks,
                "QueueTimeOutURL": self._get_redirect_url() + "/timeout",
                "ResultURL": self._get_redirect_url(),
                "Occasion": occasion
            }

            # Send B2C request
            response = await self.http_client.post(
                "/mpesa/b2c/v1/paymentrequest",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )

            result = response.json()

            if result.get("ResponseCode") == "0":
                logger.info(f"M-Pesa B2C initiated: {result.get('ConversationID')}")
                return {
                    "success": True,
                    "conversation_id": result.get("ConversationID"),
                    "originator_conversation_id": result.get("OriginatorConversationID"),
                    "response_description": result.get("ResponseDescription")
                }
            else:
                logger.error(f"M-Pesa B2C failed: {result.get('ResponseDescription')}")
                return {
                    "success": False,
                    "error": result.get("ResponseDescription", "B2C payment failed")
                }

        except httpx.HTTPError as e:
            logger.error(f"M-Pesa B2C HTTP error: {str(e)}")
            return {
                "success": False,
                "error": f"HTTP request failed: {str(e)}"
            }

    # ========================================================================
    # HEALTH CHECK
    # ========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """
        Check M-Pesa API connectivity.

        Returns:
            Health status
        """
        try:
            # Try to get access token
            token = await self._get_access_token()

            if token:
                return {
                    "provider": self.provider_name,
                    "status": "healthy",
                    "message": "Successfully connected to M-Pesa API",
                    "test_mode": self.is_test_mode
                }
            else:
                return {
                    "provider": self.provider_name,
                    "status": "unhealthy",
                    "message": "Failed to obtain M-Pesa access token",
                    "test_mode": self.is_test_mode
                }

        except Exception as e:
            return {
                "provider": self.provider_name,
                "status": "unhealthy",
                "message": f"M-Pesa API error: {str(e)}",
                "test_mode": self.is_test_mode
            }

    # ========================================================================
    # CLEANUP
    # ========================================================================

    async def close(self):
        """Close HTTP client connection."""
        await self.http_client.aclose()
