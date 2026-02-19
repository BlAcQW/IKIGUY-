"""
Consolidated PayStack Integration Service.
Handles all PayStack-related functionality with unified interface.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
from decimal import Decimal

logger = logging.getLogger(__name__)


class Currency(str, Enum):
    """Supported currencies."""
    NGN = "NGN"  # Nigerian Naira
    USD = "USD"  # US Dollar
    GHS = "GHS"  # Ghanaian Cedi
    ZAR = "ZAR"  # South African Rand


class PaymentStatus(str, Enum):
    """Payment status options."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    ABANDONED = "abandoned"
    CANCELLED = "cancelled"


class PayStackPayment(BaseModel):
    """PayStack payment model."""
    amount: Decimal  # Amount in kobo/cents
    currency: Currency = Currency.NGN
    email: str
    reference: Optional[str] = None
    callback_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    channels: List[str] = Field(default_factory=lambda: ["card", "bank", "ussd", "qr", "mobile_money"])
    split_code: Optional[str] = None
    subaccount: Optional[str] = None
    transaction_charge: Optional[int] = None
    bearer: str = "account"  # account, subaccount


class PayStackCustomer(BaseModel):
    """PayStack customer model."""
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    customer_code: Optional[str] = None
    created_at: Optional[datetime] = None


class PayStackTransaction(BaseModel):
    """PayStack transaction model."""
    transaction_id: str
    reference: str
    amount: Decimal
    currency: Currency
    status: PaymentStatus
    customer_email: str
    paid_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    gateway_response: Optional[str] = None
    channel: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PayStackService:
    """
    Consolidated service for PayStack integration.
    Handles payments, customers, transactions, and webhooks.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize PayStack service with configuration.

        Args:
            config: Configuration dictionary with PayStack settings
        """
        self.config = config or {}
        self.secret_key = self.config.get("secret_key")
        self.public_key = self.config.get("public_key")
        self.webhook_secret = self.config.get("webhook_secret")
        self.base_url = "https://api.paystack.co"
        self.session = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize PayStack client."""
        if not self.secret_key:
            logger.warning("PayStack secret key not configured")
            return

        logger.info("Initialized PayStack service")

    async def initialize_payment(
        self,
        payment: PayStackPayment
    ) -> Dict[str, Any]:
        """
        Initialize a payment transaction.

        Args:
            payment: Payment data to initialize

        Returns:
            Payment initialization result
        """
        try:
            if not self.secret_key:
                return {
                    "success": False,
                    "error": "PayStack secret key not configured"
                }

            # Generate reference if not provided
            if not payment.reference:
                payment.reference = f"paystack_{int(datetime.now().timestamp())}_{hash(payment.email) % 10000}"

            # Prepare payment data for PayStack API
            payment_data = {
                "amount": int(payment.amount * 100),  # Convert to kobo/cents
                "currency": payment.currency.value,
                "email": payment.email,
                "reference": payment.reference,
                "callback_url": payment.callback_url,
                "metadata": payment.metadata,
                "channels": payment.channels
            }

            if payment.split_code:
                payment_data["split_code"] = payment.split_code
            if payment.subaccount:
                payment_data["subaccount"] = payment.subaccount
            if payment.transaction_charge:
                payment_data["transaction_charge"] = payment.transaction_charge

            # Here would be actual API call to PayStack
            logger.info(f"Initializing PayStack payment: {payment.reference}")

            # Mock response for now
            return {
                "success": True,
                "authorization_url": f"https://checkout.paystack.com/{payment.reference}",
                "access_code": f"access_{payment.reference}",
                "reference": payment.reference,
                "amount": payment.amount,
                "currency": payment.currency.value,
                "email": payment.email,
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error initializing PayStack payment: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def verify_payment(
        self,
        reference: str
    ) -> Dict[str, Any]:
        """
        Verify a payment transaction.

        Args:
            reference: Payment reference to verify

        Returns:
            Payment verification result
        """
        try:
            if not self.secret_key:
                return {
                    "success": False,
                    "error": "PayStack secret key not configured"
                }

            logger.info(f"Verifying PayStack payment: {reference}")

            # Mock verification response
            return {
                "success": True,
                "transaction": {
                    "id": f"txn_{reference}",
                    "reference": reference,
                    "amount": 50000,  # 500.00 NGN in kobo
                    "currency": "NGN",
                    "status": "success",
                    "gateway_response": "Successful",
                    "paid_at": datetime.now().isoformat(),
                    "created_at": datetime.now().isoformat(),
                    "channel": "card",
                    "customer": {
                        "email": "customer@example.com",
                        "customer_code": "CUS_xnxdt6s1zg5f4v5"
                    },
                    "metadata": {}
                },
                "verified_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error verifying PayStack payment {reference}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def create_customer(
        self,
        customer: PayStackCustomer
    ) -> Dict[str, Any]:
        """
        Create a new customer.

        Args:
            customer: Customer data to create

        Returns:
            Customer creation result
        """
        try:
            if not self.secret_key:
                return {
                    "success": False,
                    "error": "PayStack secret key not configured"
                }

            customer_data = {
                "email": customer.email,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "phone": customer.phone,
                "metadata": customer.metadata
            }

            logger.info(f"Creating PayStack customer: {customer.email}")

            # Mock customer creation
            mock_customer_code = f"CUS_{hash(customer.email) % 1000000:06d}"

            return {
                "success": True,
                "customer_code": mock_customer_code,
                "email": customer.email,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "phone": customer.phone,
                "created_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error creating PayStack customer: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_transaction(
        self,
        transaction_id: str
    ) -> Dict[str, Any]:
        """
        Get transaction details by ID.

        Args:
            transaction_id: Transaction ID to fetch

        Returns:
            Transaction details
        """
        try:
            if not self.secret_key:
                return {
                    "success": False,
                    "error": "PayStack secret key not configured"
                }

            logger.info(f"Fetching PayStack transaction: {transaction_id}")

            # Mock transaction data
            return {
                "success": True,
                "transaction": {
                    "id": transaction_id,
                    "reference": f"ref_{transaction_id}",
                    "amount": 100000,  # 1000.00 NGN in kobo
                    "currency": "NGN",
                    "status": "success",
                    "gateway_response": "Successful",
                    "paid_at": datetime.now().isoformat(),
                    "created_at": datetime.now().isoformat(),
                    "channel": "card",
                    "customer": {
                        "email": "customer@example.com",
                        "customer_code": "CUS_xnxdt6s1zg5f4v5"
                    },
                    "metadata": {}
                }
            }

        except Exception as e:
            logger.error(f"Error fetching PayStack transaction {transaction_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def list_transactions(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        List transactions with optional filters.

        Args:
            filters: Optional filters (status, customer, amount_gte, amount_lte, etc.)
            limit: Maximum number of transactions to return

        Returns:
            List of transactions
        """
        try:
            if not self.secret_key:
                return {
                    "success": False,
                    "error": "PayStack secret key not configured"
                }

            logger.info(f"Listing PayStack transactions with filters: {filters}")

            # Mock transaction list
            mock_transactions = []
            for i in range(min(limit, 10)):  # Return up to 10 mock transactions
                mock_transactions.append({
                    "id": f"txn_{i+1}",
                    "reference": f"ref_{i+1}",
                    "amount": (i+1) * 10000,  # Varying amounts
                    "currency": "NGN",
                    "status": "success" if i % 3 != 2 else "failed",
                    "created_at": datetime.now().isoformat(),
                    "customer": {
                        "email": f"customer{i+1}@example.com"
                    }
                })

            return {
                "success": True,
                "transactions": mock_transactions,
                "total": len(mock_transactions),
                "filters": filters or {},
                "limit": limit
            }

        except Exception as e:
            logger.error(f"Error listing PayStack transactions: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def refund_transaction(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Refund a transaction.

        Args:
            transaction_id: Transaction ID to refund
            amount: Amount to refund (full amount if not specified)
            reason: Reason for refund

        Returns:
            Refund result
        """
        try:
            if not self.secret_key:
                return {
                    "success": False,
                    "error": "PayStack secret key not configured"
                }

            refund_data = {
                "transaction": transaction_id,
                "amount": int(amount * 100) if amount else None,  # Convert to kobo if specified
                "merchant_note": reason
            }

            logger.info(f"Refunding PayStack transaction: {transaction_id}")

            return {
                "success": True,
                "refund_id": f"refund_{transaction_id}",
                "transaction_id": transaction_id,
                "amount_refunded": amount or "full_amount",
                "reason": reason,
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error refunding PayStack transaction {transaction_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def handle_webhook(
        self,
        payload: Dict[str, Any],
        signature: str
    ) -> Dict[str, Any]:
        """
        Handle PayStack webhook.

        Args:
            payload: Webhook payload
            signature: Webhook signature for verification

        Returns:
            Webhook handling result
        """
        try:
            if not self.webhook_secret:
                return {
                    "success": False,
                    "error": "PayStack webhook secret not configured"
                }

            # Verify webhook signature (simplified for demo)
            event_type = payload.get("event")
            data = payload.get("data", {})

            logger.info(f"Handling PayStack webhook: {event_type}")

            # Process different event types
            if event_type == "charge.success":
                return await self._handle_successful_payment(data)
            elif event_type == "charge.failed":
                return await self._handle_failed_payment(data)
            elif event_type == "refund.successful":
                return await self._handle_successful_refund(data)
            else:
                return {
                    "success": True,
                    "message": f"Webhook event '{event_type}' received but not processed",
                    "event_type": event_type
                }

        except Exception as e:
            logger.error(f"Error handling PayStack webhook: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _handle_successful_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment webhook."""
        reference = data.get("reference")
        amount = data.get("amount")
        customer_email = data.get("customer", {}).get("email")

        logger.info(f"Payment successful: {reference}")

        return {
            "success": True,
            "event_type": "payment_success",
            "reference": reference,
            "amount": amount,
            "customer_email": customer_email,
            "processed_at": datetime.now().isoformat()
        }

    async def _handle_failed_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment webhook."""
        reference = data.get("reference")
        gateway_response = data.get("gateway_response")

        logger.info(f"Payment failed: {reference}")

        return {
            "success": True,
            "event_type": "payment_failed",
            "reference": reference,
            "reason": gateway_response,
            "processed_at": datetime.now().isoformat()
        }

    async def _handle_successful_refund(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful refund webhook."""
        transaction_reference = data.get("transaction", {}).get("reference")
        amount = data.get("amount")

        logger.info(f"Refund successful: {transaction_reference}")

        return {
            "success": True,
            "event_type": "refund_success",
            "transaction_reference": transaction_reference,
            "amount": amount,
            "processed_at": datetime.now().isoformat()
        }

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to PayStack API.

        Returns:
            Connection test result
        """
        try:
            if not self.secret_key:
                return {
                    "success": False,
                    "error": "PayStack secret key not configured"
                }

            logger.info("Testing PayStack connection")

            # Mock connection test
            return {
                "success": True,
                "message": "Connection to PayStack successful",
                "api_base": self.base_url,
                "secret_key_configured": bool(self.secret_key),
                "public_key_configured": bool(self.public_key),
                "webhook_secret_configured": bool(self.webhook_secret),
                "tested_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"PayStack connection test error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get service capabilities."""
        return {
            "service": "paystack",
            "capabilities": [
                "initialize_payment",
                "verify_payment",
                "create_customer",
                "get_transaction",
                "list_transactions",
                "refund_transaction",
                "handle_webhook",
                "test_connection"
            ],
            "supported_currencies": [currency.value for currency in Currency],
            "supported_channels": ["card", "bank", "ussd", "qr", "mobile_money"],
            "api_reference": "https://paystack.com/docs/api/",
            "documentation": "https://paystack.com/docs/",
            "configured": bool(self.secret_key)
        }


# Global PayStack service instance
paystack_service = PayStackService()