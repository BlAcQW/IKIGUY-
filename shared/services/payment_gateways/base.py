"""
Base Payment Gateway Interface.

Provides common interface for all payment gateway implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from decimal import Decimal
from enum import Enum


class PaymentStatus(str, Enum):
    """Payment status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentGatewayBase(ABC):
    """
    Abstract base class for payment gateway implementations.

    All payment gateways should inherit from this class and implement
    the required methods.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize payment gateway.

        Args:
            config: Gateway configuration (API keys, environment, etc.)
        """
        self.config = config

    @abstractmethod
    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a payment intent.

        Args:
            amount: Payment amount
            currency: Currency code (e.g., USD, GHS)
            metadata: Additional metadata
            **kwargs: Gateway-specific parameters

        Returns:
            Payment intent data including client_secret
        """
        pass

    @abstractmethod
    async def retrieve_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Retrieve payment status.

        Args:
            payment_id: Payment ID

        Returns:
            Payment data with current status
        """
        pass

    @abstractmethod
    async def refund_payment(
        self,
        payment_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Refund a payment.

        Args:
            payment_id: Payment ID
            amount: Amount to refund (None for full refund)
            reason: Refund reason

        Returns:
            Refund data
        """
        pass

    @abstractmethod
    async def cancel_payment(self, payment_id: str) -> bool:
        """
        Cancel a pending payment.

        Args:
            payment_id: Payment ID

        Returns:
            Success status
        """
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Verify webhook signature and extract event data.

        Args:
            payload: Raw webhook payload
            signature: Signature from headers
            **kwargs: Gateway-specific parameters

        Returns:
            Verified event data

        Raises:
            ValueError: If signature verification fails
        """
        pass

    def normalize_payment_status(self, gateway_status: str) -> PaymentStatus:
        """
        Normalize gateway-specific status to common PaymentStatus.

        Args:
            gateway_status: Gateway's status string

        Returns:
            Normalized PaymentStatus
        """
        # Default implementation - override in subclasses for gateway-specific mapping
        status_map = {
            "succeeded": PaymentStatus.COMPLETED,
            "success": PaymentStatus.COMPLETED,
            "successful": PaymentStatus.COMPLETED,
            "completed": PaymentStatus.COMPLETED,
            "pending": PaymentStatus.PENDING,
            "processing": PaymentStatus.PROCESSING,
            "failed": PaymentStatus.FAILED,
            "canceled": PaymentStatus.CANCELLED,
            "cancelled": PaymentStatus.CANCELLED,
            "refunded": PaymentStatus.REFUNDED,
        }
        return status_map.get(gateway_status.lower(), PaymentStatus.PENDING)
