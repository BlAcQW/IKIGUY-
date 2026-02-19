"""
Wallet Service for ChurchFlow.

Integrates with shared wallet service to manage credits and billing
for church event features (VAPI kiosk interactions, voice calls, SMS).
"""

import logging
import os
import sys
from decimal import Decimal
from typing import Optional, Dict, Any
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


class ChurchFlowWalletService:
    """
    Wallet service for ChurchFlow.

    Wraps the shared wallet service with ChurchFlow-specific functionality
    for church/conference billing (optional, for organizations wanting
    pay-per-use voice interactions).
    """

    def __init__(self):
        """Initialize ChurchFlow wallet service."""
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

    async def create_organization_wallet(
        self,
        organization_id: str,
        initial_balance: Decimal = Decimal("0.00"),
        currency: Currency = Currency.GHS,
        welcome_bonus: Decimal = Decimal("100.00")
    ) -> Optional[Wallet]:
        """
        Create a wallet for a church organization.

        Args:
            organization_id: Organization/Church ID
            initial_balance: Initial balance (default 0)
            currency: Wallet currency (default GHS for Ghana)
            welcome_bonus: Welcome bonus amount (default 100.00 GHS)

        Returns:
            Created wallet or None if failed
        """
        if not self.initialized:
            self.logger.warning("Wallet service not initialized")
            return None

        try:
            # Create wallet with welcome bonus
            wallet = await self.shared_wallet.create_wallet(
                user_id=organization_id,
                currency=currency,
                initial_balance=initial_balance + welcome_bonus
            )

            self.logger.info(f"Created wallet for organization {organization_id} with {welcome_bonus} welcome bonus")
            return wallet

        except Exception as e:
            self.logger.error(f"Failed to create wallet for organization {organization_id}: {e}")
            return None

    async def charge_kiosk_interaction(
        self,
        organization_id: str,
        conference_id: str,
        duration_seconds: int,
        interaction_type: str = "greeting",  # "greeting", "registration", "query"
        member_name: Optional[str] = None
    ) -> Optional[Transaction]:
        """
        Charge organization for kiosk voice interaction.

        Pricing: $0.05 per interaction (flat rate)

        Args:
            organization_id: Organization ID
            conference_id: Conference ID
            duration_seconds: Interaction duration
            interaction_type: Type of interaction
            member_name: Optional member name

        Returns:
            Transaction record or None if failed
        """
        if not self.initialized:
            self.logger.warning("Wallet service not initialized")
            return None

        try:
            # Get or create organization wallet
            wallet = await self.shared_wallet.get_or_create_wallet(organization_id, Currency.GHS)

            # Flat rate per kiosk interaction
            cost = Decimal("0.05")

            # Create description
            member_info = f" for {member_name}" if member_name else ""
            description = f"Kiosk {interaction_type}{member_info} - {duration_seconds}s"

            # Debit wallet
            transaction = await self.shared_wallet.debit(
                wallet_id=wallet.id,
                amount=cost,
                description=description,
                metadata={
                    "service": "churchflow_kiosk",
                    "conference_id": conference_id,
                    "interaction_type": interaction_type,
                    "duration_seconds": duration_seconds,
                    "member_name": member_name,
                    "rate": 0.05
                },
                allow_negative=False
            )

            self.logger.info(f"Charged organization {organization_id} ${cost} for kiosk interaction")
            return transaction

        except Exception as e:
            self.logger.error(f"Failed to charge kiosk interaction: {e}")
            return None

    async def charge_voice_call(
        self,
        organization_id: str,
        conference_id: str,
        phone_number: str,
        duration_minutes: float,
        purpose: str = "reminder"  # "reminder", "update", "confirmation"
    ) -> Optional[Transaction]:
        """
        Charge organization for automated voice calls.

        Pricing: Passed through from Vonage/Twilio (already tracked in wallet_transactions)

        Args:
            organization_id: Organization ID
            conference_id: Conference ID
            phone_number: Called number
            duration_minutes: Call duration
            purpose: Call purpose

        Returns:
            Transaction record or None if failed
        """
        if not self.initialized:
            self.logger.warning("Wallet service not initialized")
            return None

        try:
            # Get or create organization wallet
            wallet = await self.shared_wallet.get_or_create_wallet(organization_id, Currency.GHS)

            # Estimate cost: ~$0.02 per minute (varies by destination)
            estimated_cost = Decimal(str(duration_minutes)) * Decimal("0.02")

            # Create description
            description = f"Voice call {purpose}: {phone_number} - {duration_minutes:.1f} min"

            # Debit wallet
            transaction = await self.shared_wallet.debit(
                wallet_id=wallet.id,
                amount=estimated_cost,
                description=description,
                metadata={
                    "service": "churchflow_voice",
                    "conference_id": conference_id,
                    "phone_number": phone_number,
                    "duration_minutes": duration_minutes,
                    "purpose": purpose,
                    "estimated": True
                },
                allow_negative=False
            )

            self.logger.info(f"Charged organization {organization_id} ${estimated_cost} for voice call")
            return transaction

        except Exception as e:
            self.logger.error(f"Failed to charge voice call: {e}")
            return None

    async def charge_sms(
        self,
        organization_id: str,
        conference_id: str,
        phone_number: str,
        message_count: int = 1,
        purpose: str = "notification"
    ) -> Optional[Transaction]:
        """
        Charge organization for SMS messages.

        Pricing: $0.01 per SMS segment

        Args:
            organization_id: Organization ID
            conference_id: Conference ID
            phone_number: Recipient number
            message_count: Number of SMS segments
            purpose: Message purpose

        Returns:
            Transaction record or None if failed
        """
        if not self.initialized:
            self.logger.warning("Wallet service not initialized")
            return None

        try:
            # Get or create organization wallet
            wallet = await self.shared_wallet.get_or_create_wallet(organization_id, Currency.GHS)

            # Cost: $0.01 per SMS segment
            cost = Decimal(str(message_count)) * Decimal("0.01")

            # Create description
            description = f"SMS {purpose}: {phone_number} - {message_count} segment(s)"

            # Debit wallet
            transaction = await self.shared_wallet.debit(
                wallet_id=wallet.id,
                amount=cost,
                description=description,
                metadata={
                    "service": "churchflow_sms",
                    "conference_id": conference_id,
                    "phone_number": phone_number,
                    "message_count": message_count,
                    "purpose": purpose,
                    "rate_per_sms": 0.01
                },
                allow_negative=False
            )

            self.logger.info(f"Charged organization {organization_id} ${cost} for SMS")
            return transaction

        except Exception as e:
            self.logger.error(f"Failed to charge SMS: {e}")
            return None

    async def get_balance(self, organization_id: str) -> Optional[Decimal]:
        """
        Get organization's wallet balance.

        Args:
            organization_id: Organization ID

        Returns:
            Balance or None if failed
        """
        if not self.initialized:
            return None

        try:
            wallet = await self.shared_wallet.get_or_create_wallet(organization_id, Currency.GHS)
            return wallet.balance
        except Exception as e:
            self.logger.error(f"Failed to get balance for organization {organization_id}: {e}")
            return None

    async def get_transactions(
        self,
        organization_id: str,
        limit: int = 20,
        skip: int = 0
    ) -> Optional[list]:
        """
        Get organization's transaction history.

        Args:
            organization_id: Organization ID
            limit: Number of transactions to return
            skip: Number of transactions to skip

        Returns:
            List of transactions or None if failed
        """
        if not self.initialized:
            return None

        try:
            wallet = await self.shared_wallet.get_or_create_wallet(organization_id, Currency.GHS)
            transactions = await self.shared_wallet.get_transactions(
                wallet_id=wallet.id,
                limit=limit,
                skip=skip
            )
            return transactions
        except Exception as e:
            self.logger.error(f"Failed to get transactions for organization {organization_id}: {e}")
            return None

    async def top_up_wallet(
        self,
        organization_id: str,
        amount: Decimal,
        payment_gateway: PaymentGateway,
        payment_reference: str
    ) -> Optional[Transaction]:
        """
        Top up organization's wallet.

        Args:
            organization_id: Organization ID
            amount: Amount to add
            payment_gateway: Payment gateway used
            payment_reference: Payment reference/transaction ID

        Returns:
            Transaction record or None if failed
        """
        if not self.initialized:
            return None

        try:
            wallet = await self.shared_wallet.get_or_create_wallet(organization_id, Currency.GHS)

            transaction = await self.shared_wallet.credit(
                wallet_id=wallet.id,
                amount=amount,
                description=f"Top-up via {payment_gateway.value}",
                metadata={
                    "service": "churchflow_topup",
                    "payment_gateway": payment_gateway.value,
                    "payment_reference": payment_reference
                }
            )

            self.logger.info(f"Topped up wallet for organization {organization_id} with ${amount}")
            return transaction

        except Exception as e:
            self.logger.error(f"Failed to top up wallet for organization {organization_id}: {e}")
            return None


# Global service instance
_wallet_service: Optional[ChurchFlowWalletService] = None


async def get_wallet_service() -> ChurchFlowWalletService:
    """
    Get or create the global wallet service instance.

    Returns:
        ChurchFlowWalletService instance
    """
    global _wallet_service

    if _wallet_service is None:
        _wallet_service = ChurchFlowWalletService()

        # Initialize with environment variables
        mongodb_uri = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        await _wallet_service.initialize(mongodb_uri, database_name="kasaai_wallets")

    return _wallet_service
