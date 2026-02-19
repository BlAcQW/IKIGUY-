"""
Wallet Service for InkWave (Interactive Audiobook Platform).

Integrates with shared wallet service to manage credits and billing
for audiobook features (listening time, AI Q&A, TTS generation).
"""

import logging
import os
import sys
import uuid
from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file
# This ensures env vars are available even when uvicorn reloads
from dotenv import load_dotenv
backend_dir = Path(__file__).parent.parent.parent
env_file = backend_dir / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file, override=True)

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from apps.shared.integration.wallet import (
    WalletService as SharedWalletService,
    Transaction,
    Wallet,
    Currency,
    TransactionType,
    PaymentGateway,
    PaymentProvider,
    ProviderConfig,
    FraudDetectionService,
    NotificationService,
    # Import new exception types for better error handling
    WalletNotFoundError,
    InsufficientBalanceError,
    WalletSuspendedError,
    WalletClosedError,
)
from apps.shared.integration.wallet.providers.paystack import PaystackProvider
from apps.shared.integration.wallet.providers.expresspay_provider import ExpressPayProvider
from apps.shared.integration.usage_calculator import (
    UsageCalculator,
    PricingTier,
)

from app.core.config import settings

logger = logging.getLogger(__name__)


class InkWaveWalletService:
    """
    Wallet service for InkWave.

    Wraps the shared wallet service with InkWave-specific functionality
    for pay-per-use audiobook listening and AI interactions.
    """

    def __init__(self):
        """Initialize InkWave wallet service."""
        self.shared_wallet: Optional[SharedWalletService] = None
        self.usage_calculator = UsageCalculator(tier=PricingTier.BASIC)
        self.logger = logging.getLogger(__name__)
        self.initialized = False
        self._paystack_provider: Optional[PaystackProvider] = None
        self._expresspay_provider: Optional[ExpressPayProvider] = None

    def _get_paystack_provider(self) -> Optional[PaystackProvider]:
        """
        Get or create Paystack provider instance.

        Returns:
            PaystackProvider instance or None if not configured
        """
        if self._paystack_provider is not None:
            return self._paystack_provider

        secret_key = os.getenv("PAYSTACK_SECRET_KEY")
        if not secret_key:
            self.logger.warning("PAYSTACK_SECRET_KEY not configured")
            return None

        try:
            config = ProviderConfig(
                provider=PaymentProvider.PAYSTACK,
                secret_key=secret_key,
                webhook_secret=os.getenv("PAYSTACK_WEBHOOK_SECRET"),
                is_active=True,
            )
            self._paystack_provider = PaystackProvider(config)
            self.logger.info("Paystack provider initialized successfully")
            return self._paystack_provider
        except Exception as e:
            self.logger.error(f"Failed to initialize Paystack provider: {e}")
            return None

    def _get_expresspay_provider(self) -> Optional[ExpressPayProvider]:
        """
        Get or create ExpressPay provider instance.

        Returns:
            ExpressPayProvider instance or None if not configured
        """
        if self._expresspay_provider is not None:
            return self._expresspay_provider

        merchant_id = os.getenv("EXPRESSPAY_MERCHANT_ID")
        api_key = os.getenv("EXPRESSPAY_API_KEY")

        if not merchant_id or not api_key:
            self.logger.warning("EXPRESSPAY_MERCHANT_ID or EXPRESSPAY_API_KEY not configured")
            return None

        try:
            config = ProviderConfig(
                provider=PaymentProvider.EXPRESSPAY,
                secret_key=api_key,
                settings={"merchant_id": merchant_id},
                is_test_mode=os.getenv("EXPRESSPAY_TEST_MODE", "false").lower() == "true",
                webhook_url=os.getenv("EXPRESSPAY_WEBHOOK_URL"),
                redirect_url=os.getenv("EXPRESSPAY_REDIRECT_URL"),
                is_active=True,
            )
            self._expresspay_provider = ExpressPayProvider(config)
            self.logger.info("ExpressPay provider initialized successfully")
            return self._expresspay_provider
        except Exception as e:
            self.logger.error(f"Failed to initialize ExpressPay provider: {e}")
            return None

    async def _get_or_create_wallet(
        self,
        user_id: str,
        currency: Currency = Currency.USD
    ) -> Optional[Wallet]:
        """
        Helper method to get existing wallet or create new one with proper exception handling.

        Args:
            user_id: User ID
            currency: Wallet currency (default USD)

        Returns:
            Wallet instance or None if failed
        """
        try:
            return await self.shared_wallet.get_wallet_by_user(user_id, currency=currency)
        except (ValueError, WalletNotFoundError) as e:
            # Wallet not found, create new one
            # Handle both old ValueError and new WalletNotFoundError
            self.logger.info(f"Wallet not found for user {user_id}, creating new wallet")
            return await self.create_user_wallet(user_id, currency=currency)

    async def initialize(self, db=None, mongodb_uri: str = None, database_name: str = "kasaai_wallets") -> bool:
        """
        Initialize wallet service with database connection, fraud detection, and notifications.

        Args:
            db: Existing MongoDB database instance (preferred)
            mongodb_uri: MongoDB connection URI (fallback)
            database_name: Database name for wallets

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if db is not None:
                # Use existing database connection

                # Initialize fraud detection service
                fraud_service = FraudDetectionService(database=db)
                self.logger.info("Fraud detection service enabled")

                # Initialize notification service (with basic SMTP config from env)
                smtp_config = {
                    "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
                    "port": int(os.getenv("SMTP_PORT", "587")),
                    "username": os.getenv("SMTP_USERNAME", ""),
                    "password": os.getenv("SMTP_PASSWORD", ""),
                    "from_address": os.getenv("SMTP_FROM", "noreply@ailabsafrica.com"),
                }

                # Only enable if SMTP is configured
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

            elif mongodb_uri:
                # Create new connection
                from motor.motor_asyncio import AsyncIOMotorClient

                client = AsyncIOMotorClient(mongodb_uri)
                db = client[database_name]

                # Initialize fraud detection service
                fraud_service = FraudDetectionService(database=db)
                self.logger.info("Fraud detection service enabled")

                # Initialize notification service
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

                # Initialize wallet service
                self.shared_wallet = SharedWalletService(
                    database=db,
                    fraud_detection_service=fraud_service,
                    notification_service=notification_service
                )
                self.initialized = True
                self.logger.info("Wallet service initialized with new connection, fraud detection, and notifications")
                return True
            else:
                self.logger.error("No database or URI provided for wallet initialization")
                return False
        except Exception as e:
            self.logger.error(f"Failed to initialize wallet service: {e}")
            return False

    async def create_user_wallet(
        self,
        user_id: str,
        initial_balance: Decimal = Decimal("0.00"),
        currency: Currency = Currency.USD,
        welcome_bonus: Decimal = Decimal("10.00")
    ) -> Optional[Wallet]:
        """
        Create a wallet for a new user.

        Args:
            user_id: User ID
            initial_balance: Initial balance (default 0)
            currency: Wallet currency (default USD)
            welcome_bonus: Welcome bonus amount (default 10.00 USD for 60 mins listening)

        Returns:
            Created wallet or None if failed
        """
        if not self.initialized:
            self.logger.warning("Wallet service not initialized")
            return None

        try:
            # Check if wallet already exists
            try:
                existing_wallet = await self.shared_wallet.get_wallet_by_user(user_id, currency=currency)
                self.logger.info(f"Wallet already exists for user {user_id}")
                return existing_wallet
            except (ValueError, WalletNotFoundError):
                # Wallet doesn't exist, create new one
                # Handle both old ValueError and new WalletNotFoundError
                pass  # Continue to create wallet below

            # Create wallet (starts with 0 balance)
            wallet = await self.shared_wallet.create_wallet(
                user_id=user_id,
                currency=currency
            )

            # TODO: Implement welcome bonus crediting through proper deposit flow
            # For now, wallets start with 0 balance
            self.logger.info(f"Created {currency.value} wallet for user {user_id}")
            return wallet

        except Exception as e:
            self.logger.error(f"Failed to create wallet for user {user_id}: {e}")
            return None

    async def charge_listening_time(
        self,
        user_id: str,
        book_id: str,
        duration_minutes: float,
        book_title: Optional[str] = None
    ) -> Optional[Transaction]:
        """
        Charge user for audiobook listening time.

        Uses config-based pricing (PRICING_NARRATION_PER_MINUTE credits per minute).
        Default: 2 credits/min = $0.02/min when 100 credits = $1

        Args:
            user_id: User ID
            book_id: Book ID
            duration_minutes: Listening duration in minutes
            book_title: Optional book title for description

        Returns:
            Transaction record or None if failed
        """
        if not self.initialized:
            self.logger.warning("Wallet service not initialized")
            return None

        try:
            # Get or create user wallet
            wallet = await self._get_or_create_wallet(user_id)
            if not wallet:
                self.logger.error(f"Failed to get/create wallet for user {user_id}")
                return None

            # Calculate cost from config: PRICING_NARRATION_PER_MINUTE credits per minute
            # 100 credits = $1, so credits / 100 = dollar amount
            credits_per_minute = settings.PRICING_NARRATION_PER_MINUTE
            credits_charged = duration_minutes * credits_per_minute
            cost = Decimal(str(credits_charged)) / Decimal("100")  # Convert credits to dollars

            # Diagnostic: Log wallet state before charge
            self.logger.debug(
                f"[Billing] User {user_id}: attempting charge of ${cost} "
                f"({credits_charged} credits) for {duration_minutes:.2f} min. "
                f"Wallet {wallet.id}: balance=${wallet.balance}, "
                f"available=${wallet.available_balance}, reserved=${wallet.reserved_balance}"
            )

            # Create description
            book_info = book_title or book_id
            description = f"Listening: {book_info} - {duration_minutes:.2f} min ({credits_charged:.2f} credits)"

            # Debit wallet
            transaction = await self.shared_wallet.debit(
                wallet_id=wallet.id,
                amount=cost,
                description=description,
                metadata={
                    "service": "inkwave_listening",
                    "book_id": book_id,
                    "duration_minutes": duration_minutes,
                    "credits_charged": float(credits_charged),
                    "rate_credits_per_minute": credits_per_minute
                },
                allow_negative=False
            )

            self.logger.info(
                f"Charged user {user_id}: {credits_charged:.2f} credits "
                f"(${cost:.4f}) for {duration_minutes:.2f} minutes"
            )
            return transaction

        except InsufficientBalanceError as e:
            self.logger.warning(
                f"[Billing] Insufficient balance for user {user_id}: "
                f"needed=${cost} ({credits_charged} credits), "
                f"available=${e.available}, required=${e.required}"
            )
            return None
        except Exception as e:
            self.logger.error(f"Failed to charge listening time: {e}", exc_info=True)
            return None

    async def charge_ai_interaction(
        self,
        user_id: str,
        book_id: str,
        interaction_type: str,  # "question", "summary", "explanation"
        cost: Decimal,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Transaction]:
        """
        Charge user for AI interactions (Q&A, summaries, explanations).

        Args:
            user_id: User ID
            book_id: Book ID
            interaction_type: Type of interaction
            cost: Cost amount
            metadata: Additional metadata (tokens, model, etc.)

        Returns:
            Transaction record or None if failed
        """
        if not self.initialized:
            self.logger.warning("Wallet service not initialized")
            return None

        try:
            # Get or create user wallet
            wallet = await self._get_or_create_wallet(user_id)
            if not wallet:
                self.logger.error(f"Failed to get/create wallet for user {user_id}")
                return None

            # Create description
            description = f"AI {interaction_type}: {book_id}"

            # Prepare metadata
            tx_metadata = {
                "service": "inkwave_ai",
                "book_id": book_id,
                "interaction_type": interaction_type
            }
            if metadata:
                tx_metadata.update(metadata)

            # Debit wallet
            transaction = await self.shared_wallet.debit(
                wallet_id=wallet.id,
                amount=cost,
                description=description,
                metadata=tx_metadata,
                allow_negative=False
            )

            self.logger.info(f"Charged user {user_id} ${cost} for AI {interaction_type}")
            return transaction

        except Exception as e:
            self.logger.error(f"Failed to charge AI interaction: {e}")
            return None

    async def reserve_credits_atomic(
        self,
        user_id: str,
        credits: int,
        reservation_id: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Transaction]:
        """
        Atomically reserve credits from user wallet BEFORE doing expensive work.

        This prevents race conditions where multiple concurrent requests could
        pass a balance check before any deduction occurs. Uses MongoDB transactions
        to ensure atomicity.

        Args:
            user_id: User ID
            credits: Number of credits to reserve (100 credits = $1)
            reservation_id: Unique ID for this reservation (for idempotency)
            description: Description of what credits are reserved for
            metadata: Additional transaction metadata

        Returns:
            Transaction record if successful, None if failed

        Raises:
            InsufficientBalanceError: If user doesn't have enough credits
            WalletNotFoundError: If wallet doesn't exist
        """
        if not self.initialized:
            self.logger.warning("Wallet service not initialized")
            return None

        try:
            # Get or create user wallet
            wallet = await self._get_or_create_wallet(user_id)
            if not wallet:
                self.logger.error(f"Failed to get/create wallet for user {user_id}")
                return None

            # Convert credits to dollars (100 credits = $1)
            amount = Decimal(credits) / Decimal(100)

            # Prepare metadata with reservation flag
            tx_metadata = {
                "service": "inkwave_reservation",
                "reservation_id": reservation_id,
                "credits_reserved": credits,
                "is_reservation": True
            }
            if metadata:
                tx_metadata.update(metadata)

            # Use shared wallet's atomic debit with idempotency key
            # This will raise InsufficientBalanceError if balance is too low
            transaction = await self.shared_wallet.debit(
                wallet_id=wallet.id,
                amount=amount,
                description=f"[RESERVED] {description}",
                idempotency_key=f"reserve_{reservation_id}",
                metadata=tx_metadata,
                allow_negative=False  # Reject if insufficient balance
            )

            self.logger.info(
                f"Reserved {credits} credits (${amount}) for user {user_id}, "
                f"reservation_id={reservation_id}"
            )
            return transaction

        except InsufficientBalanceError:
            # Re-raise so caller can handle 402 response
            raise
        except Exception as e:
            self.logger.error(f"Failed to reserve credits for user {user_id}: {e}")
            return None

    async def finalize_reservation(
        self,
        user_id: str,
        reservation_id: str,
        actual_credits: int,
        reserved_credits: int,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Transaction]:
        """
        Finalize a credit reservation after work is complete.

        If actual_credits < reserved_credits, refunds the difference.
        If actual_credits > reserved_credits, charges the additional amount.

        Args:
            user_id: User ID
            reservation_id: Original reservation ID
            actual_credits: Actual credits used
            reserved_credits: Credits that were reserved
            description: Description of the finalized charge
            metadata: Additional transaction metadata

        Returns:
            Adjustment transaction if any, None if no adjustment needed
        """
        if not self.initialized:
            self.logger.warning("Wallet service not initialized")
            return None

        difference = reserved_credits - actual_credits

        if difference == 0:
            # No adjustment needed
            self.logger.info(
                f"Reservation {reservation_id} finalized: "
                f"actual={actual_credits} == reserved={reserved_credits}"
            )
            return None

        try:
            wallet = await self._get_or_create_wallet(user_id)
            if not wallet:
                self.logger.error(f"Failed to get wallet for user {user_id}")
                return None

            amount = abs(Decimal(difference)) / Decimal(100)

            tx_metadata = {
                "service": "inkwave_reservation_adjustment",
                "reservation_id": reservation_id,
                "reserved_credits": reserved_credits,
                "actual_credits": actual_credits,
                "adjustment_credits": difference
            }
            if metadata:
                tx_metadata.update(metadata)

            if difference > 0:
                # Refund excess credits
                transaction = await self.shared_wallet.credit(
                    wallet_id=wallet.id,
                    amount=amount,
                    description=f"[REFUND] {description} (overcharged by {difference} credits)",
                    idempotency_key=f"finalize_{reservation_id}",
                    metadata=tx_metadata
                )
                self.logger.info(
                    f"Refunded {difference} credits to user {user_id} "
                    f"for reservation {reservation_id}"
                )
            else:
                # Charge additional credits (rare case)
                transaction = await self.shared_wallet.debit(
                    wallet_id=wallet.id,
                    amount=amount,
                    description=f"[ADDITIONAL] {description} (undercharged by {abs(difference)} credits)",
                    idempotency_key=f"finalize_{reservation_id}",
                    metadata=tx_metadata,
                    allow_negative=False
                )
                self.logger.info(
                    f"Charged additional {abs(difference)} credits to user {user_id} "
                    f"for reservation {reservation_id}"
                )

            return transaction

        except Exception as e:
            self.logger.error(
                f"Failed to finalize reservation {reservation_id} for user {user_id}: {e}"
            )
            return None

    async def refund_reservation(
        self,
        user_id: str,
        reservation_id: str,
        credits: int,
        reason: str
    ) -> Optional[Transaction]:
        """
        Refund a reservation when the operation fails.

        Args:
            user_id: User ID
            reservation_id: Original reservation ID
            credits: Credits to refund
            reason: Reason for refund

        Returns:
            Refund transaction if successful, None if failed
        """
        if not self.initialized:
            self.logger.warning("Wallet service not initialized")
            return None

        try:
            wallet = await self._get_or_create_wallet(user_id)
            if not wallet:
                self.logger.error(f"Failed to get wallet for user {user_id}")
                return None

            amount = Decimal(credits) / Decimal(100)

            transaction = await self.shared_wallet.credit(
                wallet_id=wallet.id,
                amount=amount,
                description=f"[REFUND] Reservation cancelled: {reason}",
                idempotency_key=f"refund_{reservation_id}",
                metadata={
                    "service": "inkwave_refund",
                    "reservation_id": reservation_id,
                    "credits_refunded": credits,
                    "reason": reason
                }
            )

            self.logger.info(
                f"Refunded {credits} credits to user {user_id} "
                f"for cancelled reservation {reservation_id}: {reason}"
            )
            return transaction

        except Exception as e:
            self.logger.error(
                f"Failed to refund reservation {reservation_id} for user {user_id}: {e}"
            )
            return None

    async def get_balance(self, user_id: str) -> Optional[Decimal]:
        """
        Get user's wallet balance.

        Args:
            user_id: User ID

        Returns:
            Balance or None if failed
        """
        if not self.initialized:
            return None

        try:
            wallet = await self._get_or_create_wallet(user_id)
            return wallet.balance if wallet else None
        except Exception as e:
            self.logger.error(f"Failed to get balance for user {user_id}: {e}")
            return None

    async def get_transactions(
        self,
        user_id: str,
        limit: int = 20,
        skip: int = 0
    ) -> Optional[list]:
        """
        Get user's transaction history.

        Args:
            user_id: User ID
            limit: Number of transactions to return
            skip: Number of transactions to skip

        Returns:
            List of transactions or None if failed
        """
        if not self.initialized:
            return None

        try:
            wallet = await self._get_or_create_wallet(user_id)
            if not wallet:
                return None

            transactions = await self.shared_wallet.get_transactions(
                wallet_id=wallet.id,
                limit=limit,
                skip=skip
            )
            return transactions
        except Exception as e:
            self.logger.error(f"Failed to get transactions for user {user_id}: {e}")
            return None

    async def top_up_wallet(
        self,
        user_id: str,
        amount: Decimal,
        payment_gateway: PaymentGateway,
        payment_reference: str
    ) -> Optional[Transaction]:
        """
        Top up user's wallet.

        Args:
            user_id: User ID
            amount: Amount to add
            payment_gateway: Payment gateway used
            payment_reference: Payment reference/transaction ID

        Returns:
            Transaction record or None if failed
        """
        if not self.initialized:
            return None

        try:
            wallet = await self._get_or_create_wallet(user_id)
            if not wallet:
                self.logger.error(f"Failed to get/create wallet for user {user_id}")
                return None

            transaction = await self.shared_wallet.credit(
                wallet_id=wallet.id,
                amount=amount,
                description=f"Top-up via {payment_gateway.value}",
                metadata={
                    "service": "inkwave_topup",
                    "payment_gateway": payment_gateway.value,
                    "payment_reference": payment_reference
                }
            )

            self.logger.info(f"Topped up wallet for user {user_id} with ${amount}")
            return transaction

        except Exception as e:
            self.logger.error(f"Failed to top up wallet for user {user_id}: {e}")
            return None

    async def initiate_paystack_topup(
        self,
        user_id: str,
        amount: Decimal,
        email: str,
        callback_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Initiate Paystack payment for wallet top-up.

        Uses the shared PaystackProvider from apps.shared.integration.wallet.

        Args:
            user_id: User ID
            amount: Amount to top up
            email: User email for Paystack
            callback_url: URL to redirect after payment

        Returns:
            Payment initiation result with checkout URL
        """
        if not self.initialized:
            self.logger.warning("Wallet service not initialized")
            return {"success": False, "error": "Wallet service not initialized"}

        try:
            # Get or create wallet
            wallet = await self._get_or_create_wallet(user_id)
            if not wallet:
                self.logger.error(f"Failed to get/create wallet for user {user_id}")
                return {"success": False, "error": "Failed to get wallet"}

            # Get shared Paystack provider
            paystack = self._get_paystack_provider()
            if not paystack:
                self.logger.error("Paystack not configured")
                return {"success": False, "error": "Paystack not configured"}

            # Generate unique reference
            reference = f"inkwave_topup_{user_id}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"

            # Prepare metadata
            metadata = {
                "user_id": user_id,
                "wallet_id": wallet.id,
                "purpose": "wallet_topup",
                "app": "inkwave",
                "customer_email": email,
            }

            # Initialize transaction with shared Paystack provider
            result = await paystack.initialize_payment(
                amount=amount,
                currency=Currency.GHS,
                customer_id=email,  # Paystack accepts email as customer_id
                metadata=metadata,
            )

            if result.success:
                self.logger.info(
                    f"Paystack payment initiated for user {user_id}: {result.reference}"
                )
                return {
                    "success": True,
                    "payment_url": result.payment_url,
                    "reference": result.reference,
                    "amount": float(amount),
                    "currency": "GHS",
                }
            else:
                error_msg = result.error if result.error else "Payment initialization failed"
                self.logger.error(f"Paystack initialization failed: {error_msg}")
                return {"success": False, "error": error_msg}

        except Exception as e:
            self.logger.error(f"Failed to initiate Paystack payment: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def initiate_stripe_topup(
        self,
        user_id: str,
        amount: Decimal,
        success_url: str,
        cancel_url: str
    ) -> Optional[Dict[str, Any]]:
        """
        Initiate Stripe payment for wallet top-up.

        Args:
            user_id: User ID
            amount: Amount to top up
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancelled payment

        Returns:
            Payment initiation result with checkout URL
        """
        if not self.initialized:
            self.logger.warning("Wallet service not initialized")
            return {"success": False, "error": "Wallet service not initialized"}

        try:
            # Get or create wallet
            wallet = await self._get_or_create_wallet(user_id)
            if not wallet:
                self.logger.error(f"Failed to get/create wallet for user {user_id}")
                return {"success": False, "error": "Failed to get wallet"}

            # Import Stripe
            import stripe
            stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

            if not stripe.api_key or stripe.api_key.startswith("placeholder"):
                self.logger.error("Stripe not configured")
                return {"success": False, "error": "Stripe payment gateway not configured"}

            # Generate unique reference
            import uuid
            reference = f"inkwave_topup_{user_id}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"

            # Convert amount to cents (Stripe uses smallest currency unit)
            amount_in_cents = int(amount * 100)

            # Create Stripe checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'Inkwave Wallet Top-up',
                            'description': f'Add ${amount} to your Inkwave wallet',
                        },
                        'unit_amount': amount_in_cents,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': user_id,
                    'wallet_id': wallet.id,
                    'reference': reference,
                    'purpose': 'wallet_topup',
                    'app': 'inkwave',
                },
            )

            self.logger.info(f"Stripe checkout session created for user {user_id}: {reference}")

            return {
                "success": True,
                "payment_url": session.url,
                "reference": reference,
                "amount": float(amount),
                "currency": "USD",
            }

        except Exception as e:
            self.logger.error(f"Failed to initiate Stripe payment: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def verify_paystack_payment(self, reference: str) -> Optional[Dict[str, Any]]:
        """
        Verify Paystack payment and credit wallet if successful.

        Uses the shared PaystackProvider from apps.shared.integration.wallet.

        Args:
            reference: Payment reference

        Returns:
            Verification result
        """
        if not self.initialized:
            return {"success": False, "error": "Wallet service not initialized"}

        try:
            # Get shared Paystack provider
            paystack = self._get_paystack_provider()
            if not paystack:
                self.logger.error("Paystack not configured")
                return {"success": False, "error": "Paystack not configured"}

            # Verify transaction with shared Paystack provider
            tx_status = await paystack.get_transaction_status(reference)

            # Check if payment was successful
            if tx_status.get("status") != "success":
                status = tx_status.get("status", "unknown")
                self.logger.warning(
                    f"Paystack payment not completed: {reference} - {status}"
                )
                return {
                    "success": False,
                    "error": f"Payment not completed: {status}",
                    "payment_data": {
                        "reference": tx_status.get("reference"),
                        "status": status,
                    },
                }

            # Payment successful - credit wallet
            # Extract user_id from metadata
            metadata = tx_status.get("metadata", {}) or {}
            user_id = metadata.get("user_id")
            wallet_id = metadata.get("wallet_id")

            if not user_id or not wallet_id:
                self.logger.error(
                    f"Missing user_id or wallet_id in Paystack metadata: {reference}"
                )
                return {
                    "success": False,
                    "error": "Invalid transaction metadata",
                }

            # Get amount from transaction status (already converted to GHS by provider)
            amount_ghs = tx_status.get("amount", Decimal("0"))
            currency = tx_status.get("currency", "GHS")
            customer = tx_status.get("customer", {}) or {}
            customer_email = customer.get("email") if isinstance(customer, dict) else None

            # Calculate credits granted and USD equivalent
            # Pricing model: 100 credits = $1 = GH₵1 (simplified)
            # User pays GH₵X → gets X*100 credits → wallet stores $X
            credits_granted = float(amount_ghs) * 100  # For display/logging
            usd_amount = amount_ghs  # Wallet stores USD (GH₵1 ≈ $1 in credits model)

            self.logger.info(
                f"Payment {reference}: amount_GHS={amount_ghs}, "
                f"credits_granted={credits_granted}, usd_to_credit={usd_amount}"
            )

            # Credit the wallet with USD equivalent (wallet stores balance in USD)
            # The billing system charges: cost = credits / 100 (in USD)
            # So wallet balance must be in USD for billing math to work
            transaction = await self.shared_wallet.credit(
                wallet_id=wallet_id,
                amount=usd_amount,
                description=f"Wallet top-up via Paystack ({reference}) - GH₵{amount_ghs}",
                reference=reference,
                idempotency_key=reference,  # Prevent duplicate credits
                metadata={
                    "service": "inkwave_topup",
                    "payment_gateway": "paystack",
                    "payment_reference": reference,
                    "amount_ghs": float(amount_ghs),
                    "usd_credited": float(usd_amount),
                    "credits_granted": credits_granted,
                    "paystack_data": {
                        "customer_email": customer_email,
                        "paid_at": tx_status.get("paid_at"),
                        "channel": tx_status.get("channel"),
                        "currency": currency,
                    },
                },
            )

            # Get balance after credit for logging
            balance_after = await self.get_balance(user_id)
            self.logger.info(
                f"Wallet credited for Paystack payment {reference}: "
                f"${usd_amount} ({credits_granted} credits, GH₵{amount_ghs}) to wallet {wallet_id}, "
                f"balance_after=${balance_after}"
            )

            return {
                "success": True,
                "payment_data": {
                    "reference": tx_status.get("reference"),
                    "amount_ghs": float(amount_ghs) if amount_ghs else 0,
                    "usd_credited": float(usd_amount),
                    "credits_granted": credits_granted,
                    "currency": currency,
                    "status": tx_status.get("status"),
                    "customer_email": customer_email,
                    "paid_at": tx_status.get("paid_at"),
                    "channel": tx_status.get("channel"),
                    "transaction_id": str(transaction.id) if transaction else None,
                    "user_id": user_id,
                },
            }

        except Exception as e:
            self.logger.error(f"Failed to verify Paystack payment: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def initiate_expresspay_topup(
        self,
        user_id: str,
        amount: Decimal,
        email: str,
        firstname: Optional[str] = None,
        lastname: Optional[str] = None,
        phone: Optional[str] = None,
        callback_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Initiate ExpressPay payment for wallet top-up.

        Uses the shared ExpressPayProvider from apps.shared.integration.wallet.

        Args:
            user_id: User ID
            amount: Amount to top up (in GHS)
            email: User email for ExpressPay
            firstname: Customer first name (optional)
            lastname: Customer last name (optional)
            phone: Customer phone number for mobile money (optional)
            callback_url: URL to redirect after payment (optional)

        Returns:
            Payment initiation result with checkout URL
        """
        if not self.initialized:
            self.logger.warning("Wallet service not initialized")
            return {"success": False, "error": "Wallet service not initialized"}

        try:
            # Get or create wallet
            wallet = await self._get_or_create_wallet(user_id)
            if not wallet:
                self.logger.error(f"Failed to get/create wallet for user {user_id}")
                return {"success": False, "error": "Failed to get wallet"}

            # Get shared ExpressPay provider
            expresspay = self._get_expresspay_provider()
            if not expresspay:
                self.logger.error("ExpressPay not configured")
                return {"success": False, "error": "ExpressPay not configured"}

            # Generate unique transaction ID
            transaction_id = f"inkwave_topup_{user_id}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"

            # Prepare metadata
            metadata = {
                "user_id": user_id,
                "wallet_id": wallet.id,
                "purpose": "wallet_topup",
                "app": "inkwave",
                "transaction_id": transaction_id,
                "firstname": firstname or email.split("@")[0],
                "lastname": lastname or "User",
                "phone": phone or "0000000000",
                "description": f"InkWave wallet top-up - {amount} GHS",
            }

            # Initialize transaction with shared ExpressPay provider
            result = await expresspay.initialize_payment(
                amount=amount,
                currency=Currency.GHS,  # ExpressPay only supports GHS
                customer_id=email,  # ExpressPay requires email as customer_id
                metadata=metadata,
            )

            if result.success:
                self.logger.info(
                    f"ExpressPay payment initiated for user {user_id}: "
                    f"token={result.reference[:20] if result.reference else 'N/A'}..."
                )
                return {
                    "success": True,
                    "payment_url": result.payment_url,
                    "token": result.reference,  # ExpressPay uses token as reference
                    "transaction_id": transaction_id,
                    "amount": float(amount),
                    "currency": "GHS",
                }
            else:
                error_msg = result.error if result.error else "Payment initialization failed"
                self.logger.error(f"ExpressPay initialization failed: {error_msg}")
                return {"success": False, "error": error_msg}

        except Exception as e:
            self.logger.error(f"Failed to initiate ExpressPay payment: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def verify_expresspay_payment(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify ExpressPay payment and credit wallet if successful.

        Uses the shared ExpressPayProvider from apps.shared.integration.wallet.

        Args:
            token: Payment token from ExpressPay

        Returns:
            Verification result
        """
        if not self.initialized:
            return {"success": False, "error": "Wallet service not initialized"}

        try:
            # Get shared ExpressPay provider
            expresspay = self._get_expresspay_provider()
            if not expresspay:
                self.logger.error("ExpressPay not configured")
                return {"success": False, "error": "ExpressPay not configured"}

            # Query transaction status from ExpressPay
            tx_status = await expresspay.get_transaction_status(token)

            # ExpressPay status codes: 1=Approved, 2=Declined, 3=Error, 4=Pending
            result_code = tx_status.get("result")
            result_text = tx_status.get("result-text", "Unknown")

            if result_code == 4:  # Pending (mobile money)
                self.logger.info(f"ExpressPay payment pending: token={token[:20]}...")
                return {
                    "success": False,
                    "status": "pending",
                    "error": "Payment is still being processed",
                    "payment_data": {
                        "token": token,
                        "status": "pending",
                        "result_text": result_text,
                    },
                }

            if result_code != 1:  # Not approved
                self.logger.warning(
                    f"ExpressPay payment not completed: token={token[:20]}... - {result_text}"
                )
                return {
                    "success": False,
                    "error": f"Payment not completed: {result_text}",
                    "payment_data": {
                        "token": token,
                        "status": "failed" if result_code in [2, 3] else "unknown",
                        "result_code": result_code,
                        "result_text": result_text,
                    },
                }

            # Payment successful - extract details
            order_id = tx_status.get("order-id")
            amount = Decimal(str(tx_status.get("amount", 0)))
            currency = tx_status.get("currency", "GHS")
            expresspay_txn_id = tx_status.get("transaction-id")

            # We need to extract user_id and wallet_id from our stored metadata
            # The order_id should contain our transaction_id which has user_id
            # For now, we'll need to look up by order_id pattern
            # Pattern: inkwave_topup_{user_id}_{timestamp}_{uuid}
            user_id = None
            wallet_id = None

            if order_id and order_id.startswith("inkwave_topup_"):
                parts = order_id.split("_")
                if len(parts) >= 3:
                    user_id = parts[2]  # Extract user_id from order_id

            if not user_id:
                self.logger.error(
                    f"Could not extract user_id from ExpressPay order_id: {order_id}"
                )
                return {
                    "success": False,
                    "error": "Invalid transaction metadata - could not identify user",
                }

            # Get wallet for this user
            wallet = await self._get_or_create_wallet(user_id)
            if not wallet:
                self.logger.error(f"Could not get wallet for user {user_id}")
                return {
                    "success": False,
                    "error": "Could not find user wallet",
                }

            # Credit the wallet
            transaction = await self.shared_wallet.credit(
                wallet_id=wallet.id,
                amount=amount,
                description=f"Wallet top-up via ExpressPay ({order_id})",
                reference=token,
                idempotency_key=token,  # Prevent duplicate credits
                metadata={
                    "service": "inkwave_topup",
                    "payment_gateway": "expresspay",
                    "payment_token": token,
                    "expresspay_data": {
                        "order_id": order_id,
                        "transaction_id": expresspay_txn_id,
                        "result_text": result_text,
                        "currency": currency,
                        "date_processed": tx_status.get("date-processed"),
                    },
                },
            )

            self.logger.info(
                f"Wallet credited for ExpressPay payment {order_id}: "
                f"{amount} {currency} to wallet {wallet.id}"
            )

            return {
                "success": True,
                "payment_data": {
                    "token": token,
                    "order_id": order_id,
                    "amount": float(amount) if amount else 0,
                    "currency": currency,
                    "status": "approved",
                    "result_text": result_text,
                    "expresspay_transaction_id": expresspay_txn_id,
                    "transaction_id": str(transaction.id) if transaction else None,
                    "user_id": user_id,
                },
            }

        except Exception as e:
            self.logger.error(f"Failed to verify ExpressPay payment: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


# Global service instance
_wallet_service: Optional[InkWaveWalletService] = None


class WalletServiceProxy:
    """
    Proxy class that allows synchronous import but delegates to async wallet service.

    Usage:
        from app.services.wallet_service import wallet_service

        # In async context:
        result = await wallet_service.charge_listening_time(...)
    """
    _instance: Optional[InkWaveWalletService] = None
    _initialized: bool = False

    def __getattr__(self, name):
        """Proxy all attribute access to the underlying wallet service."""
        if self._instance is None:
            self._instance = InkWaveWalletService()
        return getattr(self._instance, name)

    async def ensure_initialized(self):
        """Ensure the wallet service is initialized before first use."""
        if not self._initialized and self._instance is not None:
            mongodb_uri = os.getenv("MONGODB_URI", os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
            await self._instance.initialize(mongodb_uri=mongodb_uri, database_name="kasaai_wallets")
            self._initialized = True


# Singleton proxy for easy import
wallet_service = WalletServiceProxy()


async def get_wallet_service(db=None) -> InkWaveWalletService:
    """
    Get or create the global wallet service instance.

    Args:
        db: Optional existing database connection

    Returns:
        InkWaveWalletService instance
    """
    global _wallet_service

    if _wallet_service is None:
        _wallet_service = InkWaveWalletService()

        # Initialize with existing database or create new connection
        if db is not None:
            await _wallet_service.initialize(db=db)
        else:
            mongodb_uri = os.getenv("MONGODB_URI", os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
            await _wallet_service.initialize(mongodb_uri=mongodb_uri, database_name="kasaai_wallets")

    return _wallet_service
