"""
Wallet Service for EventFlow.

Integrates with shared wallet service to manage credits and billing
for event planning features (AI task generation, voice calls, etc.).
"""

import logging
import os
import sys
from decimal import Decimal
from typing import Optional, Dict, Any, List
from datetime import datetime

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from apps.shared.integration.wallet import (
    WalletService as SharedWalletService,
    Transaction,
    Wallet,
    Currency,
    TransactionType,
    PaymentGateway,
    # Import fraud detection and notifications
    FraudDetectionService,
    NotificationService,
    # Import new exception types for better error handling
    WalletNotFoundError,
    InsufficientBalanceError,
    WalletSuspendedError,
    WalletClosedError,
)
from apps.shared.integration.usage_calculator import (
    UsageCalculator,
    PricingTier,
)

logger = logging.getLogger(__name__)


class EventFlowWalletService:
    """
    Wallet service for EventFlow.

    Wraps the shared wallet service with EventFlow-specific functionality.
    """

    def __init__(self):
        """Initialize EventFlow wallet service."""
        self.shared_wallet: Optional[SharedWalletService] = None
        self.usage_calculator = UsageCalculator(tier=PricingTier.BASIC)
        self.logger = logging.getLogger(__name__)
        self.initialized = False

    async def initialize(self, mongodb_uri: str, database_name: str = "kasaai_wallets") -> bool:
        """
        Initialize wallet service with database connection, fraud detection, and notifications.

        Args:
            mongodb_uri: MongoDB connection URI
            database_name: Database name for wallets

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            from motor.motor_asyncio import AsyncIOMotorClient

            # Create database connection
            client = AsyncIOMotorClient(mongodb_uri)
            db = client[database_name]

            # Initialize fraud detection service
            fraud_service = FraudDetectionService(database=db)
            self.logger.info("Fraud detection service enabled")

            # Initialize notification service (with SMTP config from env)
            smtp_config = {
                "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
                "port": int(os.getenv("SMTP_PORT", "587")),
                "username": os.getenv("SMTP_USERNAME", ""),
                "password": os.getenv("SMTP_PASSWORD", ""),
                "from_address": os.getenv("SMTP_FROM", "noreply@ailabsafrica.com"),
            }

            notification_service = None
            if smtp_config.get("username") and smtp_config.get("password"):
                notification_service = NotificationService(
                    database=db,
                    smtp_config=smtp_config
                )
                self.logger.info("Notification service enabled")
            else:
                self.logger.warning("Notification service disabled (SMTP not configured)")

            # Initialize wallet service with fraud detection and notifications
            self.shared_wallet = SharedWalletService(
                database=db,
                fraud_detection_service=fraud_service,
                notification_service=notification_service
            )
            self.initialized = True
            self.logger.info("Wallet service initialized with fraud detection and notifications")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize wallet service: {e}")
            return False

    async def create_user_wallet(
        self,
        user_id: str,
        initial_balance: Decimal = Decimal("0.00"),
        currency: Currency = Currency.GHS,
        welcome_bonus: Decimal = Decimal("50.00")
    ) -> Optional[Wallet]:
        """
        Create a wallet for a new user.

        Args:
            user_id: User ID
            initial_balance: Initial balance (default 0)
            currency: Wallet currency (default GHS)
            welcome_bonus: Welcome bonus amount (default 50.00 GHS)

        Returns:
            Created wallet or None if failed
        """
        if not self.initialized:
            self.logger.warning("Wallet service not initialized")
            return None

        try:
            # Create wallet with welcome bonus
            wallet = await self.shared_wallet.create_wallet(
                user_id=user_id,
                currency=currency,
                initial_balance=initial_balance + welcome_bonus
            )

            self.logger.info(f"Created wallet for user {user_id} with {welcome_bonus} welcome bonus")
            return wallet

        except Exception as e:
            self.logger.error(f"Failed to create wallet: {e}")
            return None

    async def deduct_ai_task_generation_cost(
        self,
        wallet_id: str,
        event_id: str,
        num_tasks: int,
        used_rag: bool = False
    ) -> Optional[Transaction]:
        """
        Deduct cost for AI task generation.

        Args:
            wallet_id: User's wallet ID
            event_id: Event ID for tracking
            num_tasks: Number of tasks generated
            used_rag: Whether RAG AI was used (more expensive)

        Returns:
            Transaction record or None if failed
        """
        if not self.initialized:
            self.logger.warning("Wallet service not initialized")
            return None

        try:
            # Calculate cost based on usage
            cost_per_task = Decimal("0.50") if used_rag else Decimal("0.00")  # RAG costs, templates free
            total_cost = cost_per_task * num_tasks

            if total_cost == 0:
                self.logger.info("Task generation using templates - no cost")
                return None

            # Deduct from wallet
            transaction = await self.shared_wallet.debit(
                wallet_id=wallet_id,
                amount=total_cost,
                description=f"AI task generation - {num_tasks} tasks for event",
                idempotency_key=f"task-gen-{event_id}-{datetime.utcnow().timestamp()}",
                metadata={
                    "event_id": event_id,
                    "num_tasks": num_tasks,
                    "used_rag": used_rag,
                    "service": "ai_task_generation"
                }
            )

            self.logger.info(f"Deducted {total_cost} GHS for task generation (wallet: {wallet_id})")
            return transaction

        except Exception as e:
            self.logger.error(f"Failed to deduct task generation cost: {e}")
            return None

    async def deduct_voice_call_cost(
        self,
        wallet_id: str,
        event_id: str,
        task_id: str,
        duration_minutes: float,
        responsible_person_name: str
    ) -> Optional[Transaction]:
        """
        Deduct cost for a voice call.

        Args:
            wallet_id: User's wallet ID
            event_id: Event ID
            task_id: Task ID
            duration_minutes: Call duration in minutes
            responsible_person_name: Name of person called

        Returns:
            Transaction record or None if failed
        """
        if not self.initialized:
            self.logger.warning("Wallet service not initialized")
            return None

        try:
            # Calculate cost using usage calculator
            cost_result = self.usage_calculator.calculate_voice_call_cost(
                duration_minutes=duration_minutes,
                direction="outbound",
                platform="vapi"
            )

            # Deduct from wallet
            transaction = await self.shared_wallet.debit(
                wallet_id=wallet_id,
                amount=Decimal(str(cost_result.total_cost)),
                description=f"Voice call - {responsible_person_name} ({duration_minutes:.1f} min)",
                idempotency_key=f"call-{task_id}-{datetime.utcnow().timestamp()}",
                metadata={
                    "event_id": event_id,
                    "task_id": task_id,
                    "duration_minutes": duration_minutes,
                    "responsible_person": responsible_person_name,
                    "service": "voice_call"
                }
            )

            self.logger.info(f"Deducted {cost_result.total_cost} GHS for voice call (wallet: {wallet_id})")
            return transaction

        except Exception as e:
            self.logger.error(f"Failed to deduct voice call cost: {e}")
            return None

    async def deduct_sms_cost(
        self,
        wallet_id: str,
        event_id: str,
        task_id: str,
        recipient_phone: str,
        num_messages: int = 1
    ) -> Optional[Transaction]:
        """
        Deduct cost for SMS messages.

        Args:
            wallet_id: User's wallet ID
            event_id: Event ID
            task_id: Task ID
            recipient_phone: Phone number
            num_messages: Number of SMS messages sent

        Returns:
            Transaction record or None if failed
        """
        if not self.initialized:
            self.logger.warning("Wallet service not initialized")
            return None

        try:
            # Calculate SMS cost
            cost_per_sms = Decimal("0.20")  # 0.20 GHS per SMS
            total_cost = cost_per_sms * num_messages

            # Deduct from wallet
            transaction = await self.shared_wallet.debit(
                wallet_id=wallet_id,
                amount=total_cost,
                description=f"SMS reminder - {recipient_phone} ({num_messages} msg)",
                idempotency_key=f"sms-{task_id}-{datetime.utcnow().timestamp()}",
                metadata={
                    "event_id": event_id,
                    "task_id": task_id,
                    "recipient": recipient_phone,
                    "num_messages": num_messages,
                    "service": "sms_notification"
                }
            )

            self.logger.info(f"Deducted {total_cost} GHS for SMS (wallet: {wallet_id})")
            return transaction

        except Exception as e:
            self.logger.error(f"Failed to deduct SMS cost: {e}")
            return None

    async def get_user_balance(self, wallet_id: str) -> Optional[Decimal]:
        """
        Get user's current wallet balance.

        Args:
            wallet_id: User's wallet ID

        Returns:
            Current balance or None if failed
        """
        if not self.initialized:
            self.logger.warning("Wallet service not initialized")
            return None

        try:
            balance = await self.shared_wallet.get_balance(wallet_id)
            return balance
        except Exception as e:
            self.logger.error(f"Failed to get balance: {e}")
            return None

    async def topup_wallet(
        self,
        wallet_id: str,
        amount: Decimal,
        gateway: PaymentGateway = PaymentGateway.PAYSTACK,
        payment_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Initiate wallet top-up via payment gateway.

        Args:
            wallet_id: User's wallet ID
            amount: Amount to top up
            gateway: Payment gateway to use
            payment_metadata: Additional payment metadata (email, etc.)

        Returns:
            Payment initiation result with payment URL
        """
        if not self.initialized:
            self.logger.warning("Wallet service not initialized")
            return None

        try:
            result = await self.shared_wallet.topup_with_gateway(
                wallet_id=wallet_id,
                amount=amount,
                gateway=gateway,
                payment_metadata=payment_metadata or {}
            )

            self.logger.info(f"Initiated {amount} GHS top-up for wallet {wallet_id}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to initiate top-up: {e}")
            return None

    async def get_event_spending(self, wallet_id: str, event_id: str) -> Dict[str, Any]:
        """
        Get total spending for a specific event.

        Args:
            wallet_id: User's wallet ID
            event_id: Event ID

        Returns:
            Dictionary with spending breakdown
        """
        if not self.initialized:
            self.logger.warning("Wallet service not initialized")
            return {"total": 0, "by_service": {}}

        try:
            # Get all transactions for this event
            transactions = await self.shared_wallet.get_transactions(
                wallet_id=wallet_id,
                filters={"metadata.event_id": event_id}
            )

            # Calculate totals
            total_spent = Decimal("0.00")
            by_service = {}

            for txn in transactions:
                if txn["type"] == "debit":
                    amount = Decimal(str(txn["amount"]))
                    total_spent += amount

                    service = txn.get("metadata", {}).get("service", "other")
                    by_service[service] = by_service.get(service, Decimal("0.00")) + amount

            return {
                "total": float(total_spent),
                "by_service": {k: float(v) for k, v in by_service.items()},
                "num_transactions": len(transactions)
            }

        except Exception as e:
            self.logger.error(f"Failed to get event spending: {e}")
            return {"total": 0, "by_service": {}, "error": str(e)}
