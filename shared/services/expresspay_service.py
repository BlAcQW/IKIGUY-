"""
ExpressPay Ghana Payment Gateway Service.

Provides integration with ExpressPay for:
- Direct payments (Merchant Direct API)
- Card tokenization (save cards)
- Payment verification
- Webhook handling

Documentation: https://expresspaygh.com/api-documentation
"""

import logging
import hashlib
import hmac
import json
import httpx
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ExpressPayConfig(BaseModel):
    """ExpressPay configuration."""

    merchant_id: str = Field(..., description="ExpressPay Merchant ID")
    api_key: str = Field(..., description="ExpressPay API Key")
    api_secret: str = Field(..., description="ExpressPay API Secret")
    sandbox: bool = Field(default=True, description="Use sandbox environment")

    @property
    def base_url(self) -> str:
        """Get API base URL based on environment."""
        if self.sandbox:
            return "https://sandbox.expresspaygh.com/api"
        return "https://expresspaygh.com/api"


class PaymentRequest(BaseModel):
    """Request model for initiating payment."""

    amount: Decimal = Field(..., gt=0, description="Payment amount")
    currency: str = Field(default="GHS", description="Currency code (GHS, USD)")
    order_id: str = Field(..., description="Unique order/transaction ID")
    order_desc: str = Field(..., description="Order description")
    redirect_url: Optional[str] = Field(None, description="URL to redirect after payment")
    customer_email: Optional[str] = Field(None, description="Customer email")
    customer_name: Optional[str] = Field(None, description="Customer name")
    customer_telephone: Optional[str] = Field(None, description="Customer phone")


class TokenizeCardRequest(BaseModel):
    """Request model for tokenizing a card."""

    card_number: str = Field(..., description="Card number")
    card_expiry_month: str = Field(..., description="Card expiry month (MM)")
    card_expiry_year: str = Field(..., description="Card expiry year (YY)")
    card_cvv: str = Field(..., description="Card CVV")
    customer_email: str = Field(..., description="Customer email")
    customer_name: str = Field(..., description="Customer name")


class ChargeTokenRequest(BaseModel):
    """Request model for charging a tokenized card."""

    token: str = Field(..., description="Card token")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    currency: str = Field(default="GHS", description="Currency code")
    order_id: str = Field(..., description="Unique order ID")
    order_desc: str = Field(..., description="Order description")


class ExpressPayService:
    """
    ExpressPay payment gateway service.

    Handles payment processing, card tokenization, and verification.
    """

    def __init__(self, config: ExpressPayConfig):
        """
        Initialize ExpressPay service.

        Args:
            config: ExpressPay configuration
        """
        self.config = config
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info(f"ExpressPay service initialized (sandbox={config.sandbox})")

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    def _generate_signature(self, data: Dict[str, Any]) -> str:
        """
        Generate HMAC signature for API request.

        Args:
            data: Request data

        Returns:
            HMAC signature
        """
        # Sort data by keys and concatenate values
        sorted_data = sorted(data.items())
        message = "".join(str(v) for k, v in sorted_data)

        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            self.config.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return signature

    async def initiate_payment(
        self,
        request: PaymentRequest
    ) -> Dict[str, Any]:
        """
        Initiate payment with ExpressPay.

        Uses Merchant Direct API for seamless checkout.

        Args:
            request: Payment request details

        Returns:
            Payment response with payment URL or error
        """
        try:
            # Prepare request data
            data = {
                "merchant-id": self.config.merchant_id,
                "api-key": self.config.api_key,
                "amount": float(request.amount),
                "currency": request.currency,
                "order-id": request.order_id,
                "order-desc": request.order_desc,
            }

            # Add optional fields
            if request.redirect_url:
                data["redirect-url"] = request.redirect_url
            if request.customer_email:
                data["customer-email"] = request.customer_email
            if request.customer_name:
                data["customer-name"] = request.customer_name
            if request.customer_telephone:
                data["customer-telephone"] = request.customer_telephone

            # Generate signature
            data["signature"] = self._generate_signature(data)

            # Make API request
            url = f"{self.config.base_url}/submit"
            response = await self.client.post(url, json=data)
            response.raise_for_status()

            result = response.json()

            if result.get("status") == 1:  # Success
                logger.info(f"Payment initiated: {request.order_id}")
                return {
                    "success": True,
                    "payment_url": result.get("checkout-url"),
                    "order_id": result.get("order-id"),
                    "token": result.get("token"),
                }
            else:
                error = result.get("message", "Payment initiation failed")
                logger.error(f"Payment initiation failed: {error}")
                return {
                    "success": False,
                    "error": error
                }

        except httpx.HTTPError as e:
            logger.error(f"ExpressPay API error: {str(e)}")
            return {
                "success": False,
                "error": f"Payment gateway error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Payment initiation error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Payment failed: {str(e)}"
            }

    async def tokenize_card(
        self,
        request: TokenizeCardRequest
    ) -> Dict[str, Any]:
        """
        Tokenize a card for future payments.

        Uses Tokenization API to securely save card details.

        Args:
            request: Card tokenization request

        Returns:
            Token response or error
        """
        try:
            # Prepare request data
            data = {
                "merchant-id": self.config.merchant_id,
                "api-key": self.config.api_key,
                "card-number": request.card_number,
                "card-expiry-month": request.card_expiry_month,
                "card-expiry-year": request.card_expiry_year,
                "card-cvv": request.card_cvv,
                "customer-email": request.customer_email,
                "customer-name": request.customer_name,
            }

            # Generate signature
            data["signature"] = self._generate_signature(data)

            # Make API request
            url = f"{self.config.base_url}/tokenize"
            response = await self.client.post(url, json=data)
            response.raise_for_status()

            result = response.json()

            if result.get("status") == 1:  # Success
                logger.info(f"Card tokenized for {request.customer_email}")
                return {
                    "success": True,
                    "token": result.get("token"),
                    "card_last4": request.card_number[-4:],
                    "card_type": result.get("card-type"),
                    "expiry_month": request.card_expiry_month,
                    "expiry_year": request.card_expiry_year,
                }
            else:
                error = result.get("message", "Card tokenization failed")
                logger.error(f"Tokenization failed: {error}")
                return {
                    "success": False,
                    "error": error
                }

        except httpx.HTTPError as e:
            logger.error(f"ExpressPay tokenization error: {str(e)}")
            return {
                "success": False,
                "error": f"Tokenization failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Tokenization error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to save card: {str(e)}"
            }

    async def charge_token(
        self,
        request: ChargeTokenRequest
    ) -> Dict[str, Any]:
        """
        Charge a tokenized card.

        Uses saved card token for seamless payment.

        Args:
            request: Charge request with token

        Returns:
            Payment result
        """
        try:
            # Prepare request data
            data = {
                "merchant-id": self.config.merchant_id,
                "api-key": self.config.api_key,
                "token": request.token,
                "amount": float(request.amount),
                "currency": request.currency,
                "order-id": request.order_id,
                "order-desc": request.order_desc,
            }

            # Generate signature
            data["signature"] = self._generate_signature(data)

            # Make API request
            url = f"{self.config.base_url}/charge-token"
            response = await self.client.post(url, json=data)
            response.raise_for_status()

            result = response.json()

            if result.get("status") == 1:  # Success
                logger.info(f"Token charged: {request.order_id}")
                return {
                    "success": True,
                    "transaction_id": result.get("transaction-id"),
                    "order_id": result.get("order-id"),
                    "amount": result.get("amount"),
                    "currency": result.get("currency"),
                }
            else:
                error = result.get("message", "Payment failed")
                logger.error(f"Token charge failed: {error}")
                return {
                    "success": False,
                    "error": error
                }

        except httpx.HTTPError as e:
            logger.error(f"ExpressPay charge error: {str(e)}")
            return {
                "success": False,
                "error": f"Payment failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Charge error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Payment processing failed: {str(e)}"
            }

    async def verify_payment(
        self,
        order_id: str,
        token: str
    ) -> Dict[str, Any]:
        """
        Verify payment status.

        Args:
            order_id: Order ID to verify
            token: Payment token

        Returns:
            Payment verification result with detailed transaction info
        """
        try:
            # Prepare request data
            data = {
                "merchant-id": self.config.merchant_id,
                "api-key": self.config.api_key,
                "order-id": order_id,
                "token": token,
            }

            # Generate signature
            data["signature"] = self._generate_signature(data)

            # Make API request
            url = f"{self.config.base_url}/query"
            response = await self.client.post(url, json=data)
            response.raise_for_status()

            result = response.json()
            logger.info(f"ExpressPay query response for {order_id}: {result}")

            if result.get("status") == 1:  # API call successful
                is_paid = result.get("result") == 1
                result_code = result.get("result-code", result.get("result"))

                # Map result codes to human-readable status
                status_messages = {
                    1: "Payment successful",
                    2: "Payment declined",
                    3: "Payment error",
                    4: "Payment pending",
                }

                logger.info(f"Payment verified: {order_id}, paid={is_paid}")
                return {
                    "success": True,
                    "paid": is_paid,
                    "status_code": result_code,
                    "status_message": status_messages.get(result_code, "Unknown status"),
                    "transaction_id": result.get("transaction-id"),
                    "order_id": result.get("order-id"),
                    "amount": result.get("amount"),
                    "currency": result.get("currency", "GHS"),
                    "payment_method": result.get("payment-method"),
                    "date_processed": result.get("date-processed"),
                    # Additional details from ExpressPay
                    "card_last4": result.get("card-number", "")[-4:] if result.get("card-number") else None,
                    "card_type": result.get("card-type"),
                    "customer_name": result.get("customer-name"),
                    "customer_email": result.get("customer-email"),
                    "raw_response": result,  # Include full response for debugging
                }
            else:
                error = result.get("message", "Verification failed")
                error_code = result.get("status")
                logger.error(f"Verification failed for {order_id}: {error} (code: {error_code})")
                return {
                    "success": False,
                    "error": error,
                    "error_code": error_code,
                    "order_id": order_id,
                }

        except httpx.HTTPError as e:
            logger.error(f"ExpressPay verification error: {str(e)}")
            return {
                "success": False,
                "error": f"Payment gateway connection error: {str(e)}",
                "error_type": "network_error",
                "order_id": order_id,
            }
        except Exception as e:
            logger.error(f"Verification error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Payment verification failed: {str(e)}",
                "error_type": "internal_error",
                "order_id": order_id,
            }

    def verify_webhook(
        self,
        payload: Dict[str, Any],
        signature: str
    ) -> bool:
        """
        Verify webhook signature.

        Args:
            payload: Webhook payload
            signature: Signature from webhook header

        Returns:
            True if signature is valid
        """
        try:
            expected_signature = self._generate_signature(payload)
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Webhook verification error: {str(e)}")
            return False
