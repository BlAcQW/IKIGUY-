"""
Wallet service for StudyFlow.

Handles wallet operations, transactions, and payment processing.
"""

import logging
import os
from typing import Optional, List
from datetime import datetime, timedelta
from bson import ObjectId
import sys

# Add shared services to path
sys.path.insert(0, "/opt/kasaai/apps")

from shared.integration.wallet import (
    WalletService as SharedWalletService,
    FraudDetectionService,
    NotificationService,
)

from app.models.wallet import (
    Wallet,
    WalletCreate,
    Transaction,
    TransactionCreate,
    TransactionType,
    TransactionStatus,
    PaymentMethod,
    WalletSummary
)
from app.core.database import mongodb, COLLECTION_WALLETS, COLLECTION_TRANSACTIONS
from app.config import settings

logger = logging.getLogger(__name__)


class WalletService:
    """
    Service for wallet and transaction management.

    Handles parent wallets, credits, debits, and payment processing.
    """

    _shared_wallet_service: Optional[SharedWalletService] = None

    @classmethod
    def get_shared_wallet_service(cls) -> SharedWalletService:
        """
        Get or create shared wallet service instance with fraud detection and notifications.

        Returns:
            SharedWalletService instance
        """
        if cls._shared_wallet_service is None:
            # Get database
            db = mongodb.db

            # Initialize fraud detection service
            fraud_service = FraudDetectionService(database=db)
            logger.info("✓ Fraud detection service enabled")

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
                logger.info("✓ Notification service enabled")
            else:
                logger.warning("⚠ Notification service disabled (SMTP not configured)")

            # Create shared wallet service with fraud detection and notifications
            cls._shared_wallet_service = SharedWalletService(
                database=db,
                fraud_detection_service=fraud_service,
                notification_service=notification_service
            )
            logger.info("✓ Shared Wallet Service initialized with fraud detection and notifications")

        return cls._shared_wallet_service

    @staticmethod
    async def get_or_create_wallet(
        user_id: str,
        organization_id: Optional[str] = None
    ) -> Wallet:
        """
        Get existing wallet or create new one for user with organization scoping.

        Args:
            user_id: Parent user ID
            organization_id: Organization ID for scoping (required for creation)

        Returns:
            Wallet instance
        """
        collection = mongodb.get_collection(COLLECTION_WALLETS)

        # Build query
        query = {"user_id": user_id}
        if organization_id:
            query["organization_id"] = organization_id

        wallet_doc = await collection.find_one(query)

        if wallet_doc:
            wallet_doc["id"] = str(wallet_doc["_id"])
            return Wallet(**wallet_doc)

        # Create new wallet (requires organization_id)
        if not organization_id:
            logger.warning(f"Cannot create wallet for {user_id} without organization_id")
            # Return wallet with empty organization_id for backward compatibility
            wallet = Wallet(user_id=user_id, organization_id="")
            return wallet

        wallet = Wallet(user_id=user_id, organization_id=organization_id)
        result = await collection.insert_one(wallet.dict(by_alias=True, exclude={"id"}))
        wallet.id = str(result.inserted_id)

        logger.info(f"Wallet created for user: {user_id}")
        return wallet

    @staticmethod
    async def get_wallet_by_id(
        wallet_id: str,
        organization_id: Optional[str] = None
    ) -> Optional[Wallet]:
        """
        Get wallet by ID with optional organization filtering.

        Args:
            wallet_id: Wallet ID
            organization_id: Organization ID for access control (optional)

        Returns:
            Wallet if found and accessible, None otherwise
        """
        collection = mongodb.get_collection(COLLECTION_WALLETS)

        # Build query
        query = {"_id": ObjectId(wallet_id)}
        if organization_id:
            query["organization_id"] = organization_id

        wallet_doc = await collection.find_one(query)

        if wallet_doc:
            wallet_doc["id"] = str(wallet_doc["_id"])
            return Wallet(**wallet_doc)
        return None

    @staticmethod
    async def create_transaction(
        wallet_id: str,
        transaction_type: TransactionType,
        amount: float,
        description: str,
        payment_method: Optional[PaymentMethod] = None,
        reference: Optional[str] = None,
        metadata: dict = None
    ) -> Transaction:
        """
        Create a transaction and update wallet balance.

        Args:
            wallet_id: Wallet ID
            transaction_type: CREDIT, DEBIT, REFUND, or ADJUSTMENT
            amount: Transaction amount (positive)
            description: Transaction description
            payment_method: Payment method used
            reference: External payment reference
            metadata: Additional transaction data

        Returns:
            Created transaction

        Raises:
            ValueError: If insufficient balance for debit
        """
        # Get wallet
        wallet = await WalletService.get_wallet_by_id(wallet_id)
        if not wallet:
            raise ValueError(f"Wallet not found: {wallet_id}")

        if not wallet.is_active:
            raise ValueError("Wallet is not active")

        # Check balance for debits
        if transaction_type == TransactionType.DEBIT and wallet.balance < amount:
            raise ValueError(
                f"Insufficient balance: {wallet.balance} GHS, required: {amount} GHS"
            )

        # Calculate new balance
        balance_before = wallet.balance
        if transaction_type == TransactionType.CREDIT:
            balance_after = balance_before + amount
        elif transaction_type == TransactionType.DEBIT:
            balance_after = balance_before - amount
        elif transaction_type == TransactionType.REFUND:
            balance_after = balance_before + amount
        elif transaction_type == TransactionType.ADJUSTMENT:
            # Adjustment can be positive or negative
            balance_after = balance_before + amount
        else:
            raise ValueError(f"Unknown transaction type: {transaction_type}")

        # Create transaction
        transaction = Transaction(
            wallet_id=wallet_id,
            user_id=wallet.user_id,
            type=transaction_type,
            status=TransactionStatus.COMPLETED,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description=description,
            payment_method=payment_method,
            reference=reference,
            metadata=metadata or {},
            completed_at=datetime.utcnow()
        )

        # Save transaction
        transactions_collection = mongodb.get_collection(COLLECTION_TRANSACTIONS)
        result = await transactions_collection.insert_one(
            transaction.dict(by_alias=True, exclude={"id"})
        )
        transaction.id = str(result.inserted_id)

        # Update wallet
        wallets_collection = mongodb.get_collection(COLLECTION_WALLETS)
        update_data = {
            "balance": balance_after,
            "last_transaction_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        if transaction_type == TransactionType.CREDIT:
            update_data["total_credited"] = wallet.total_credited + amount
        elif transaction_type == TransactionType.DEBIT:
            update_data["total_debited"] = wallet.total_debited + amount

        await wallets_collection.update_one(
            {"_id": ObjectId(wallet_id)},
            {"$set": update_data}
        )

        logger.info(
            f"Transaction created: {transaction.id} "
            f"({transaction_type.value}, {amount} GHS) "
            f"for wallet {wallet_id}"
        )

        return transaction

    @staticmethod
    async def deduct_cost(
        user_id: str,
        amount: float,
        description: str,
        metadata: dict = None
    ) -> Transaction:
        """
        Deduct cost from user's wallet.

        Used for tutoring session costs.

        Args:
            user_id: Parent user ID
            amount: Amount to deduct
            description: Transaction description
            metadata: Additional data (session_id, student_id, etc.)

        Returns:
            Transaction record

        Raises:
            ValueError: If insufficient balance
        """
        # Get or create wallet
        wallet = await WalletService.get_or_create_wallet(user_id)

        # Create debit transaction
        transaction = await WalletService.create_transaction(
            wallet_id=wallet.id,
            transaction_type=TransactionType.DEBIT,
            amount=amount,
            description=description,
            metadata=metadata
        )

        return transaction

    @staticmethod
    async def credit_wallet(
        wallet_id: str,
        amount: float,
        description: str,
        payment_method: PaymentMethod,
        reference: str,
        metadata: dict = None
    ) -> Transaction:
        """
        Credit wallet (top-up).

        Args:
            wallet_id: Wallet ID
            amount: Amount to credit
            description: Transaction description
            payment_method: Payment method used
            reference: Payment reference
            metadata: Additional data

        Returns:
            Transaction record
        """
        transaction = await WalletService.create_transaction(
            wallet_id=wallet_id,
            transaction_type=TransactionType.CREDIT,
            amount=amount,
            description=description,
            payment_method=payment_method,
            reference=reference,
            metadata=metadata
        )

        return transaction

    @staticmethod
    async def get_transaction_history(
        wallet_id: str,
        limit: int = 50,
        skip: int = 0,
        transaction_type: Optional[TransactionType] = None
    ) -> List[Transaction]:
        """
        Get transaction history for wallet.

        Args:
            wallet_id: Wallet ID
            limit: Maximum transactions to return
            skip: Number to skip (pagination)
            transaction_type: Filter by transaction type

        Returns:
            List of transactions
        """
        collection = mongodb.get_collection(COLLECTION_TRANSACTIONS)

        query = {"wallet_id": wallet_id}
        if transaction_type:
            query["type"] = transaction_type.value

        cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)

        transactions = []
        async for txn_doc in cursor:
            txn_doc["id"] = str(txn_doc["_id"])
            transactions.append(Transaction(**txn_doc))

        return transactions

    @staticmethod
    async def get_wallet_summary(
        wallet_id: str,
        period_days: int = 30
    ) -> WalletSummary:
        """
        Get wallet summary for analytics.

        Args:
            wallet_id: Wallet ID
            period_days: Number of days to include in summary

        Returns:
            Wallet summary with stats
        """
        wallet = await WalletService.get_wallet_by_id(wallet_id)
        if not wallet:
            raise ValueError(f"Wallet not found: {wallet_id}")

        # Calculate period
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=period_days)

        # Get transactions in period
        collection = mongodb.get_collection(COLLECTION_TRANSACTIONS)
        cursor = collection.find({
            "wallet_id": wallet_id,
            "created_at": {"$gte": period_start, "$lte": period_end}
        })

        total_spent = 0.0
        transaction_count = 0
        subjects_spending = {}

        async for txn_doc in cursor:
            if txn_doc["type"] == TransactionType.DEBIT.value:
                total_spent += txn_doc["amount"]
                transaction_count += 1

                # Track spending by subject
                subject = txn_doc.get("metadata", {}).get("subject")
                if subject:
                    subjects_spending[subject] = subjects_spending.get(subject, 0) + txn_doc["amount"]

        # Determine top spending subject
        top_subject = None
        if subjects_spending:
            top_subject = max(subjects_spending, key=subjects_spending.get)

        # Calculate average session cost
        avg_cost = total_spent / transaction_count if transaction_count > 0 else 0.0

        # Low balance alert (less than 10 GHS)
        low_balance = wallet.balance < 10.0

        return WalletSummary(
            wallet_id=wallet_id,
            user_id=wallet.user_id,
            current_balance=wallet.balance,
            total_spent_this_month=total_spent,
            total_spent_lifetime=wallet.total_debited,
            transaction_count_this_month=transaction_count,
            top_spending_subject=top_subject,
            average_session_cost=avg_cost,
            low_balance_alert=low_balance,
            period_start=period_start,
            period_end=period_end
        )

    @staticmethod
    async def initiate_payment(
        wallet_id: str,
        amount: float,
        payment_method: PaymentMethod,
        callback_url: Optional[str] = None
    ) -> dict:
        """
        Initiate payment via payment gateway.

        Args:
            wallet_id: Wallet ID
            amount: Amount to pay
            payment_method: Payment method
            callback_url: Callback URL for confirmation

        Returns:
            Payment initialization data (authorization_url, reference, etc.)

        Raises:
            ValueError: If payment initiation fails
        """
        wallet = await WalletService.get_wallet_by_id(wallet_id)
        if not wallet:
            raise ValueError(f"Wallet not found: {wallet_id}")

        # Use shared wallet service for payment gateway integration
        shared_wallet = WalletService.get_shared_wallet_service()

        try:
            # Get user email from wallet metadata
            email = wallet.metadata.get("email", "user@studyflow.com")

            # Initialize payment
            payment_data = await shared_wallet.initialize_payment(
                amount=amount,
                email=email,
                callback_url=callback_url or f"{settings.API_BASE_URL}/api/v1/wallet/payment/callback",
                metadata={
                    "wallet_id": wallet_id,
                    "user_id": wallet.user_id,
                    "service": "StudyFlow"
                }
            )

            # Create pending transaction
            await WalletService.create_transaction(
                wallet_id=wallet_id,
                transaction_type=TransactionType.CREDIT,
                amount=amount,
                description=f"Wallet top-up via {payment_method.value}",
                payment_method=payment_method,
                reference=payment_data.get("reference"),
                metadata={"payment_status": "initiated"}
            )

            logger.info(f"Payment initiated for wallet {wallet_id}: {amount} GHS")
            return payment_data

        except Exception as e:
            logger.error(f"Payment initiation error: {str(e)}")
            raise ValueError(f"Failed to initiate payment: {str(e)}")

    @staticmethod
    async def verify_payment(reference: str) -> bool:
        """
        Verify payment with payment gateway.

        Args:
            reference: Payment reference

        Returns:
            True if payment verified, False otherwise
        """
        shared_wallet = WalletService.get_shared_wallet_service()

        try:
            verification = await shared_wallet.verify_payment(reference)

            if verification.get("status") == "success":
                logger.info(f"Payment verified: {reference}")
                return True
            else:
                logger.warning(f"Payment verification failed: {reference}")
                return False

        except Exception as e:
            logger.error(f"Payment verification error: {str(e)}")
            return False

    @staticmethod
    async def check_sufficient_balance(user_id: str, required_amount: float) -> bool:
        """
        Check if user has sufficient balance.

        Args:
            user_id: User ID
            required_amount: Amount required

        Returns:
            True if sufficient balance, False otherwise
        """
        wallet = await WalletService.get_or_create_wallet(user_id)
        return wallet.balance >= required_amount

    @staticmethod
    async def get_low_balance_users(threshold: float = 10.0) -> List[str]:
        """
        Get users with low wallet balance.

        Used for sending balance alerts.

        Args:
            threshold: Balance threshold in GHS

        Returns:
            List of user IDs with low balance
        """
        collection = mongodb.get_collection(COLLECTION_WALLETS)
        cursor = collection.find({
            "balance": {"$lt": threshold},
            "is_active": True
        })

        user_ids = []
        async for wallet_doc in cursor:
            user_ids.append(wallet_doc["user_id"])

        return user_ids
