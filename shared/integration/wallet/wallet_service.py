"""
Core Wallet Service - Main Orchestrator

This module provides the WalletService class that orchestrates all wallet operations
including wallet management, transaction processing, provider integration, and
balance reconciliation with MongoDB transaction atomicity.

Key Features:
- Wallet CRUD operations
- Transaction atomicity using MongoDB transactions
- Idempotency support to prevent duplicate transactions
- Provider registration and routing
- Balance reconciliation and tracking
- Multi-tenancy support
- Low balance alerts

Author: KasaAI Team
Date: 2025-10-27
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorClientSession
from pymongo.errors import DuplicateKeyError

from .models import (
    Currency,
    TransactionType,
    TransactionStatus,
    PaymentProvider,
    PaymentMethodType,
    WalletStatus,
    Wallet,
    Transaction,
    PaymentMethod,
    ProviderConfig,
    WebhookEvent,
    PaymentInitiationResult,
    DepositRequest,
    WithdrawalRequest,
    RefundRequest,
    WalletBalanceResponse,
    TransactionResponse,
    TransactionListResponse,
)
from .exceptions import (
    WalletError,
    WalletNotFoundError,
    InsufficientBalanceError,
    DuplicateTransactionError,
    TransactionNotFoundError,
    WalletSuspendedError,
    WalletClosedError,
    PaymentMethodNotFoundError,
    ProviderNotConfiguredError,
    ProviderAPIError,
    DatabaseError,
    ValidationError,
)
from .providers.base import BasePaymentProvider


logger = logging.getLogger(__name__)


class WalletService:
    """
    Main wallet service orchestrator.

    This service handles all wallet operations with transaction atomicity,
    idempotency support, and provider integration.

    Example:
        ```python
        # Initialize service
        mongo_client = AsyncIOMotorClient("mongodb://localhost:27017")
        db = mongo_client.kasaai_core
        wallet_service = WalletService(db)

        # Register providers
        stripe_config = await db.provider_configs.find_one({"provider": "stripe"})
        stripe_provider = StripeProvider(ProviderConfig(**stripe_config))
        wallet_service.register_provider(PaymentProvider.STRIPE, stripe_provider)

        # Create wallet
        wallet = await wallet_service.create_wallet(
            user_id="user123",
            currency=Currency.GHS,
            tenant_id="churchflow"
        )

        # Process deposit
        transaction = await wallet_service.deposit(
            wallet_id=wallet.id,
            amount=Decimal("100.00"),
            payment_provider=PaymentProvider.STRIPE,
            payment_method_id="pm_123",
            idempotency_key="unique-key-123"
        )
        ```
    """

    def __init__(self, database, notification_service=None, fraud_detection_service=None):
        """
        Initialize wallet service.

        Args:
            database: MongoDB database instance (motor AsyncIOMotorDatabase)
            notification_service: Optional NotificationService for sending notifications
            fraud_detection_service: Optional FraudDetectionService for fraud prevention
        """
        self.db = database
        self.wallets_collection = database.wallets
        self.transactions_collection = database.transactions
        self.payment_methods_collection = database.payment_methods
        self.webhook_events_collection = database.webhook_events

        # Provider registry
        self.providers: Dict[PaymentProvider, BasePaymentProvider] = {}

        # Notification service (optional)
        self.notification_service = notification_service

        # Fraud detection service (optional)
        self.fraud_detection_service = fraud_detection_service

        logger.info("WalletService initialized")

    @classmethod
    async def create(
        cls,
        mongodb_uri: str,
        database_name: str = "kasaai_wallets",
        notification_service=None,
        fraud_detection_service=None
    ) -> "WalletService":
        """
        Create WalletService instance - backward compatibility classmethod.

        This classmethod provides compatibility with the old wallet.py API.
        For new code, use the regular __init__ constructor with a database instance.

        Args:
            mongodb_uri: MongoDB connection URI
            database_name: Database name for wallet storage
            notification_service: Optional NotificationService instance
            fraud_detection_service: Optional FraudDetectionService instance

        Returns:
            Initialized WalletService instance

        Example:
            ```python
            wallet_service = await WalletService.create(
                mongodb_uri="mongodb://localhost:27017",
                database_name="kasaai_wallets"
            )
            ```
        """
        from motor.motor_asyncio import AsyncIOMotorClient

        # Create MongoDB connection
        client = AsyncIOMotorClient(mongodb_uri)
        database = client[database_name]

        # Create indexes for performance
        await database.wallets.create_index("user_id")
        await database.wallets.create_index([("user_id", 1), ("currency", 1)], unique=True)
        await database.wallets.create_index("status")
        await database.wallets.create_index("tenant_id")
        await database.transactions.create_index("wallet_id")
        await database.transactions.create_index("idempotency_key", unique=True, sparse=True)
        await database.transactions.create_index("reference")
        await database.transactions.create_index("created_at")
        await database.transactions.create_index([("wallet_id", 1), ("created_at", -1)])
        await database.transactions.create_index("user_id")
        await database.transactions.create_index("tenant_id")

        logger.info(f"Database indexes created for wallet service in '{database_name}'")

        return cls(
            database=database,
            notification_service=notification_service,
            fraud_detection_service=fraud_detection_service
        )

    # ============================================================================
    # Provider Management
    # ============================================================================

    def register_provider(
        self,
        provider: PaymentProvider,
        provider_instance: BasePaymentProvider
    ) -> None:
        """
        Register a payment provider.

        Args:
            provider: Payment provider enum
            provider_instance: Initialized provider instance

        Example:
            ```python
            stripe_provider = StripeProvider(stripe_config)
            wallet_service.register_provider(PaymentProvider.STRIPE, stripe_provider)
            ```
        """
        self.providers[provider] = provider_instance
        logger.info(f"Registered payment provider: {provider.value}")

    def get_provider(self, provider: PaymentProvider) -> BasePaymentProvider:
        """
        Get a registered payment provider.

        Args:
            provider: Payment provider enum

        Returns:
            Provider instance

        Raises:
            ProviderNotConfiguredError: If provider not registered
        """
        if provider not in self.providers:
            raise ProviderNotConfiguredError(provider=provider.value)
        return self.providers[provider]

    # ============================================================================
    # Wallet CRUD Operations
    # ============================================================================

    async def create_wallet(
        self,
        user_id: str,
        currency: Currency = Currency.GHS,
        tenant_id: Optional[str] = None,
        low_balance_threshold: Decimal = Decimal("10.00"),
        low_balance_alert_enabled: bool = True,
    ) -> Wallet:
        """
        Create a new wallet for a user.

        Args:
            user_id: User identifier
            currency: Wallet currency (default: GHS)
            tenant_id: Optional tenant/app identifier for multi-tenancy
            low_balance_threshold: Balance threshold for low balance alerts
            low_balance_alert_enabled: Enable low balance alerts

        Returns:
            Created wallet

        Raises:
            DatabaseError: If database operation fails
            ValidationError: If wallet already exists

        Example:
            ```python
            wallet = await wallet_service.create_wallet(
                user_id="user123",
                currency=Currency.GHS,
                tenant_id="churchflow"
            )
            ```
        """
        try:
            # Check if wallet already exists
            existing = await self.wallets_collection.find_one({
                "user_id": user_id,
                "currency": currency.value,
                "tenant_id": tenant_id,
            })

            if existing:
                raise ValidationError(
                    f"Wallet already exists for user {user_id} "
                    f"with currency {currency.value}"
                )

            wallet = Wallet(
                user_id=user_id,
                tenant_id=tenant_id,
                balance=Decimal("0.00"),
                pending_balance=Decimal("0.00"),
                reserved_balance=Decimal("0.00"),
                currency=currency,
                status=WalletStatus.ACTIVE,
                low_balance_threshold=low_balance_threshold,
                low_balance_alert_enabled=low_balance_alert_enabled,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            wallet_dict = wallet.dict()
            # Convert Decimal to float for MongoDB
            for key, value in wallet_dict.items():
                if isinstance(value, Decimal):
                    wallet_dict[key] = float(value)

            await self.wallets_collection.insert_one(wallet_dict)

            logger.info(
                f"Created wallet {wallet.id} for user {user_id} "
                f"with currency {currency.value}"
            )

            return wallet

        except DuplicateKeyError:
            raise ValidationError(
                f"Wallet already exists for user {user_id} "
                f"with currency {currency.value}"
            )
        except Exception as e:
            logger.error(f"Error creating wallet: {e}")
            raise DatabaseError(f"Failed to create wallet: {str(e)}")

    async def get_wallet(
        self,
        wallet_id: str,
        session: Optional[AsyncIOMotorClientSession] = None
    ) -> Wallet:
        """
        Get wallet by ID.

        Args:
            wallet_id: Wallet identifier
            session: Optional MongoDB session for transactions

        Returns:
            Wallet instance

        Raises:
            WalletNotFoundError: If wallet not found
        """
        wallet_dict = await self.wallets_collection.find_one(
            {"id": wallet_id},
            session=session
        )

        if not wallet_dict:
            raise WalletNotFoundError(wallet_id=wallet_id)

        # Convert float to Decimal for financial fields
        for key in ['balance', 'pending_balance', 'reserved_balance', 'low_balance_threshold']:
            if key in wallet_dict and wallet_dict[key] is not None:
                wallet_dict[key] = Decimal(str(wallet_dict[key]))

        return Wallet(**wallet_dict)

    async def get_wallet_by_user(
        self,
        user_id: str,
        currency: Currency = Currency.GHS,
        tenant_id: Optional[str] = None,
        session: Optional[AsyncIOMotorClientSession] = None
    ) -> Wallet:
        """
        Get wallet by user ID, currency, and tenant.

        Args:
            user_id: User identifier
            currency: Wallet currency
            tenant_id: Optional tenant identifier
            session: Optional MongoDB session for transactions

        Returns:
            Wallet instance

        Raises:
            WalletNotFoundError: If wallet not found
        """
        query = {
            "user_id": user_id,
            "currency": currency.value,
        }

        if tenant_id:
            query["tenant_id"] = tenant_id

        wallet_dict = await self.wallets_collection.find_one(query, session=session)

        if not wallet_dict:
            raise WalletNotFoundError(
                wallet_id=f"user:{user_id},currency:{currency.value},tenant:{tenant_id}"
            )

        # Convert float to Decimal
        for key in ['balance', 'pending_balance', 'reserved_balance', 'low_balance_threshold']:
            if key in wallet_dict and wallet_dict[key] is not None:
                wallet_dict[key] = Decimal(str(wallet_dict[key]))

        return Wallet(**wallet_dict)

    async def update_wallet_status(
        self,
        wallet_id: str,
        status: WalletStatus,
        reason: Optional[str] = None
    ) -> Wallet:
        """
        Update wallet status.

        Args:
            wallet_id: Wallet identifier
            status: New wallet status
            reason: Optional reason for status change

        Returns:
            Updated wallet

        Raises:
            WalletNotFoundError: If wallet not found
        """
        wallet = await self.get_wallet(wallet_id)

        update_data = {
            "status": status.value,
            "updated_at": datetime.utcnow(),
        }

        if reason:
            update_data["metadata.status_reason"] = reason

        await self.wallets_collection.update_one(
            {"id": wallet_id},
            {"$set": update_data}
        )

        logger.info(f"Updated wallet {wallet_id} status to {status.value}")

        # Return updated wallet
        return await self.get_wallet(wallet_id)

    async def suspend_wallet(
        self,
        wallet_id: str,
        reason: str
    ) -> Wallet:
        """
        Suspend a wallet.

        Args:
            wallet_id: Wallet identifier
            reason: Reason for suspension

        Returns:
            Updated wallet
        """
        return await self.update_wallet_status(
            wallet_id,
            WalletStatus.SUSPENDED,
            reason
        )

    async def activate_wallet(self, wallet_id: str) -> Wallet:
        """
        Activate a wallet.

        Args:
            wallet_id: Wallet identifier

        Returns:
            Updated wallet
        """
        return await self.update_wallet_status(
            wallet_id,
            WalletStatus.ACTIVE,
            None
        )

    async def close_wallet(
        self,
        wallet_id: str,
        reason: str
    ) -> Wallet:
        """
        Close a wallet (irreversible).

        Args:
            wallet_id: Wallet identifier
            reason: Reason for closing

        Returns:
            Updated wallet

        Raises:
            ValidationError: If wallet has non-zero balance
        """
        wallet = await self.get_wallet(wallet_id)

        if wallet.balance != Decimal("0.00"):
            raise ValidationError(
                "Cannot close wallet with non-zero balance. "
                "Please withdraw all funds first."
            )

        return await self.update_wallet_status(
            wallet_id,
            WalletStatus.CLOSED,
            reason
        )

    # ============================================================================
    # Balance Operations (Internal)
    # ============================================================================

    async def _update_balance_atomic(
        self,
        wallet_id: str,
        amount: Decimal,
        balance_type: str = "balance",
        session: Optional[AsyncIOMotorClientSession] = None
    ) -> Tuple[Decimal, Decimal]:
        """
        Update wallet balance atomically and return before/after balances.

        Args:
            wallet_id: Wallet identifier
            amount: Amount to add (positive) or subtract (negative)
            balance_type: Type of balance to update (balance, pending_balance, reserved_balance)
            session: MongoDB session for transaction atomicity

        Returns:
            Tuple of (balance_before, balance_after)

        Raises:
            InsufficientBalanceError: If balance would go negative
        """
        wallet = await self.get_wallet(wallet_id, session=session)

        balance_before = getattr(wallet, balance_type)
        balance_after = balance_before + amount

        # Check for negative balance
        if balance_after < Decimal("0.00"):
            raise InsufficientBalanceError(
                available=float(balance_before),
                required=float(abs(amount))
            )

        # Update balance
        await self.wallets_collection.update_one(
            {"id": wallet_id},
            {
                "$inc": {balance_type: float(amount)},
                "$set": {"updated_at": datetime.utcnow()}
            },
            session=session
        )

        return balance_before, balance_after

    # ============================================================================
    # Transaction Operations
    # ============================================================================

    async def _check_idempotency(
        self,
        idempotency_key: Optional[str]
    ) -> Optional[Transaction]:
        """
        Check if transaction with idempotency key already exists.

        Args:
            idempotency_key: Idempotency key

        Returns:
            Existing transaction if found, None otherwise
        """
        if not idempotency_key:
            return None

        existing = await self.transactions_collection.find_one({
            "idempotency_key": idempotency_key
        })

        if existing:
            # Convert float to Decimal
            for key in ['amount', 'processing_fee', 'total_amount', 'balance_before', 'balance_after']:
                if key in existing and existing[key] is not None:
                    existing[key] = Decimal(str(existing[key]))

            return Transaction(**existing)

        return None

    async def _create_transaction(
        self,
        wallet_id: str,
        user_id: str,
        transaction_type: TransactionType,
        amount: Decimal,
        currency: Currency,
        processing_fee: Decimal,
        balance_before: Decimal,
        balance_after: Decimal,
        payment_provider: Optional[PaymentProvider] = None,
        payment_method_id: Optional[str] = None,
        provider_transaction_id: Optional[str] = None,
        provider_response: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        reference: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        session: Optional[AsyncIOMotorClientSession] = None
    ) -> Transaction:
        """
        Create a transaction record.

        Args:
            wallet_id: Wallet identifier
            user_id: User identifier
            transaction_type: Type of transaction
            amount: Transaction amount
            currency: Currency
            processing_fee: Provider processing fee
            balance_before: Balance before transaction
            balance_after: Balance after transaction
            payment_provider: Payment provider
            payment_method_id: Payment method identifier
            provider_transaction_id: Provider's transaction ID
            provider_response: Raw provider response
            idempotency_key: Idempotency key
            reference: External reference
            description: Transaction description
            metadata: Additional metadata
            tenant_id: Tenant identifier
            session: MongoDB session for transactions

        Returns:
            Created transaction
        """
        transaction = Transaction(
            wallet_id=wallet_id,
            user_id=user_id,
            tenant_id=tenant_id,
            transaction_type=transaction_type,
            status=TransactionStatus.PENDING,
            amount=amount,
            currency=currency,
            processing_fee=processing_fee,
            total_amount=amount + processing_fee,
            balance_before=balance_before,
            balance_after=balance_after,
            payment_method_id=payment_method_id,
            payment_provider=payment_provider,
            provider_transaction_id=provider_transaction_id,
            provider_response=provider_response or {},
            idempotency_key=idempotency_key,
            reference=reference,
            description=description,
            metadata=metadata or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        transaction_dict = transaction.dict()
        # Convert Decimal to float for MongoDB
        for key, value in transaction_dict.items():
            if isinstance(value, Decimal):
                transaction_dict[key] = float(value)

        await self.transactions_collection.insert_one(transaction_dict, session=session)

        logger.info(
            f"Created transaction {transaction.id} for wallet {wallet_id}: "
            f"{transaction_type.value} {amount} {currency.value}"
        )

        return transaction

    async def get_transaction(
        self,
        transaction_id: str,
        session: Optional[AsyncIOMotorClientSession] = None
    ) -> Transaction:
        """
        Get transaction by ID.

        Args:
            transaction_id: Transaction identifier
            session: Optional MongoDB session for transactions

        Returns:
            Transaction instance

        Raises:
            TransactionNotFoundError: If transaction not found
        """
        transaction_dict = await self.transactions_collection.find_one(
            {"id": transaction_id},
            session=session
        )

        if not transaction_dict:
            raise TransactionNotFoundError(transaction_id=transaction_id)

        # Convert float to Decimal
        for key in ['amount', 'processing_fee', 'total_amount', 'balance_before', 'balance_after']:
            if key in transaction_dict and transaction_dict[key] is not None:
                transaction_dict[key] = Decimal(str(transaction_dict[key]))

        return Transaction(**transaction_dict)

    async def update_transaction_status(
        self,
        transaction_id: str,
        status: TransactionStatus,
        provider_response: Optional[Dict[str, Any]] = None,
        session: Optional[AsyncIOMotorClientSession] = None
    ) -> Transaction:
        """
        Update transaction status.

        Args:
            transaction_id: Transaction identifier
            status: New status
            provider_response: Optional provider response data
            session: MongoDB session for transactions

        Returns:
            Updated transaction
        """
        update_data = {
            "status": status.value,
            "updated_at": datetime.utcnow(),
        }

        if status == TransactionStatus.COMPLETED:
            update_data["completed_at"] = datetime.utcnow()
        elif status == TransactionStatus.FAILED:
            update_data["failed_at"] = datetime.utcnow()

        if provider_response:
            update_data["provider_response"] = provider_response

        await self.transactions_collection.update_one(
            {"id": transaction_id},
            {"$set": update_data},
            session=session
        )

        logger.info(f"Updated transaction {transaction_id} status to {status.value}")

        return await self.get_transaction(transaction_id, session=session)

    async def list_transactions(
        self,
        wallet_id: Optional[str] = None,
        user_id: Optional[str] = None,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> TransactionListResponse:
        """
        List transactions with filters.

        Args:
            wallet_id: Filter by wallet ID
            user_id: Filter by user ID
            transaction_type: Filter by transaction type
            status: Filter by status
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            Transaction list response with pagination
        """
        query = {}

        if wallet_id:
            query["wallet_id"] = wallet_id
        if user_id:
            query["user_id"] = user_id
        if transaction_type:
            query["transaction_type"] = transaction_type.value
        if status:
            query["status"] = status.value

        if start_date or end_date:
            query["created_at"] = {}
            if start_date:
                query["created_at"]["$gte"] = start_date
            if end_date:
                query["created_at"]["$lte"] = end_date

        # Get total count
        total = await self.transactions_collection.count_documents(query)

        # Get transactions
        cursor = self.transactions_collection.find(query).sort(
            "created_at", -1
        ).skip(offset).limit(limit)

        transactions = []
        async for doc in cursor:
            # Convert float to Decimal
            for key in ['amount', 'processing_fee', 'total_amount', 'balance_before', 'balance_after']:
                if key in doc and doc[key] is not None:
                    doc[key] = Decimal(str(doc[key]))
            tx = Transaction(**doc)

            # Convert Transaction to TransactionResponse
            from .models import TransactionResponse
            tx_response = TransactionResponse(
                id=tx.id,
                transaction_type=tx.transaction_type.value,
                status=tx.status.value,
                amount=float(tx.amount),
                currency=tx.currency.value,
                processing_fee=float(tx.processing_fee),
                total_amount=float(tx.total_amount),
                description=tx.description,
                created_at=tx.created_at.isoformat(),
                completed_at=tx.completed_at.isoformat() if tx.completed_at else None,
                failed_at=tx.failed_at.isoformat() if tx.failed_at else None
            )
            transactions.append(tx_response)

        # Calculate if there are more transactions
        has_more = (offset + limit) < total

        return TransactionListResponse(
            transactions=transactions,
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more
        )

    # ============================================================================
    # Deposit Operations
    # ============================================================================

    async def deposit(
        self,
        wallet_id: str,
        amount: Decimal,
        payment_provider: PaymentProvider,
        payment_method_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        reference: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[Transaction, PaymentInitiationResult]:
        """
        Process a deposit to wallet.

        This method:
        1. Checks idempotency
        2. Validates wallet status
        3. Initializes payment with provider
        4. Creates transaction record with pending balance
        5. Returns transaction and payment initiation result

        Args:
            wallet_id: Wallet identifier
            amount: Deposit amount
            payment_provider: Payment provider to use
            payment_method_id: Optional saved payment method ID
            idempotency_key: Optional idempotency key
            reference: Optional external reference
            description: Optional description
            metadata: Optional additional metadata

        Returns:
            Tuple of (Transaction, PaymentInitiationResult)

        Raises:
            DuplicateTransactionError: If idempotency key already exists
            WalletNotFoundError: If wallet not found
            WalletSuspendedError: If wallet is suspended
            WalletClosedError: If wallet is closed
            ProviderNotConfiguredError: If provider not registered
            ProviderAPIError: If provider API fails

        Example:
            ```python
            transaction, payment_result = await wallet_service.deposit(
                wallet_id="wallet123",
                amount=Decimal("100.00"),
                payment_provider=PaymentProvider.STRIPE,
                payment_method_id="pm_123",
                idempotency_key="unique-key-123"
            )

            # Return payment_url to frontend for 3D Secure if needed
            if payment_result.payment_url:
                return {"payment_url": payment_result.payment_url}
            ```
        """
        # Check idempotency
        if idempotency_key:
            existing = await self._check_idempotency(idempotency_key)
            if existing:
                logger.info(f"Duplicate transaction detected: {idempotency_key}")
                raise DuplicateTransactionError(idempotency_key=idempotency_key)

        # Get wallet
        wallet = await self.get_wallet(wallet_id)

        # Check wallet status
        if wallet.status == WalletStatus.SUSPENDED:
            raise WalletSuspendedError(wallet_id=wallet_id)
        if wallet.status == WalletStatus.CLOSED:
            raise WalletClosedError(wallet_id=wallet_id)

        # Get provider
        provider = self.get_provider(payment_provider)

        # Calculate fee
        processing_fee = provider.calculate_fee(amount)

        # Perform fraud detection check if service is configured
        if self.fraud_detection_service:
            # Create a temporary transaction object for fraud checking
            temp_transaction = Transaction(
                id=f"temp_{idempotency_key or 'check'}",
                wallet_id=wallet_id,
                user_id=wallet.user_id,
                transaction_type=TransactionType.DEPOSIT,
                amount=amount,
                currency=wallet.currency,
                status=TransactionStatus.PENDING,
                balance_before=wallet.balance,
                balance_after=wallet.balance,
                tenant_id=wallet.tenant_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            fraud_check = await self.fraud_detection_service.check_transaction(
                temp_transaction, wallet, metadata
            )

            # Handle fraud detection decision
            if fraud_check.decision.value == "blocked":
                logger.warning(
                    f"Transaction blocked by fraud detection: "
                    f"wallet={wallet_id}, risk_score={fraud_check.risk_score}"
                )
                # Send security notification if available
                if self.notification_service:
                    try:
                        await self.notification_service.notify_suspicious_activity(
                            wallet,
                            f"Transaction blocked due to suspicious activity (risk score: {fraud_check.risk_score})"
                        )
                    except Exception as e:
                        logger.error(f"Failed to send fraud alert notification: {e}")

                raise ValidationError(
                    f"Transaction blocked by fraud detection system. "
                    f"Risk score: {fraud_check.risk_score}. "
                    f"Please contact support if you believe this is an error."
                )

            elif fraud_check.requires_review:
                logger.info(
                    f"Transaction flagged for review: "
                    f"wallet={wallet_id}, risk_score={fraud_check.risk_score}"
                )
                # Transaction proceeds but is flagged for review
                # You could add this to metadata for tracking
                if not metadata:
                    metadata = {}
                metadata["fraud_check_id"] = fraud_check.id
                metadata["fraud_risk_score"] = fraud_check.risk_score
                metadata["requires_review"] = True

        # Initialize payment with provider
        payment_metadata = metadata or {}
        payment_metadata["wallet_id"] = wallet_id
        payment_metadata["transaction_type"] = TransactionType.DEPOSIT.value

        try:
            payment_result = await provider.initialize_payment(
                amount=amount,
                currency=wallet.currency,
                payment_method_id=payment_method_id,
                metadata=payment_metadata
            )
        except Exception as e:
            logger.error(f"Provider payment initialization failed: {e}")
            raise ProviderAPIError(
                provider=payment_provider.value,
                message=str(e)
            )

        # Create transaction with pending status
        # Note: Balance is updated to pending_balance, not balance yet
        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                # Add to pending balance
                balance_before, balance_after = await self._update_balance_atomic(
                    wallet_id,
                    Decimal("0.00"),  # Don't update confirmed balance yet
                    balance_type="balance",
                    session=session
                )

                # Add to pending balance
                await self._update_balance_atomic(
                    wallet_id,
                    amount,
                    balance_type="pending_balance",
                    session=session
                )

                transaction = await self._create_transaction(
                    wallet_id=wallet_id,
                    user_id=wallet.user_id,
                    transaction_type=TransactionType.DEPOSIT,
                    amount=amount,
                    currency=wallet.currency,
                    processing_fee=processing_fee,
                    balance_before=balance_before,
                    balance_after=balance_before,  # Not updated yet
                    payment_provider=payment_provider,
                    payment_method_id=payment_method_id,
                    provider_transaction_id=payment_result.reference,
                    provider_response=payment_result.metadata,
                    idempotency_key=idempotency_key,
                    reference=reference,
                    description=description or f"Deposit via {payment_provider.value}",
                    metadata=metadata,
                    tenant_id=wallet.tenant_id,
                    session=session
                )

        logger.info(
            f"Deposit initiated: wallet={wallet_id}, amount={amount}, "
            f"provider={payment_provider.value}, transaction={transaction.id}"
        )

        return transaction, payment_result

    # ============================================================================
    # Withdrawal Operations
    # ============================================================================

    async def withdraw(
        self,
        wallet_id: str,
        amount: Decimal,
        payment_provider: PaymentProvider,
        payment_method_id: str,
        idempotency_key: Optional[str] = None,
        reference: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Transaction:
        """
        Process a withdrawal from wallet.

        This method:
        1. Checks idempotency
        2. Validates wallet status and sufficient balance
        3. Deducts from balance atomically
        4. Creates transaction record
        5. Initiates payout with provider (if applicable)

        Args:
            wallet_id: Wallet identifier
            amount: Withdrawal amount
            payment_provider: Payment provider to use
            payment_method_id: Payment method for withdrawal
            idempotency_key: Optional idempotency key
            reference: Optional external reference
            description: Optional description
            metadata: Optional additional metadata

        Returns:
            Transaction record

        Raises:
            DuplicateTransactionError: If idempotency key already exists
            WalletNotFoundError: If wallet not found
            InsufficientBalanceError: If insufficient balance
            WalletSuspendedError: If wallet is suspended
            WalletClosedError: If wallet is closed
        """
        # Check idempotency
        if idempotency_key:
            existing = await self._check_idempotency(idempotency_key)
            if existing:
                logger.info(f"Duplicate transaction detected: {idempotency_key}")
                raise DuplicateTransactionError(idempotency_key=idempotency_key)

        # Get wallet
        wallet = await self.get_wallet(wallet_id)

        # Check wallet status
        if wallet.status == WalletStatus.SUSPENDED:
            raise WalletSuspendedError(wallet_id=wallet_id)
        if wallet.status == WalletStatus.CLOSED:
            raise WalletClosedError(wallet_id=wallet_id)

        # Check available balance
        if wallet.available_balance < amount:
            raise InsufficientBalanceError(
                available=float(wallet.available_balance),
                required=float(amount)
            )

        # Get provider
        provider = self.get_provider(payment_provider)

        # Calculate fee
        processing_fee = provider.calculate_fee(amount)
        total_amount = amount + processing_fee

        # Check total amount against balance
        if wallet.available_balance < total_amount:
            raise InsufficientBalanceError(
                available=float(wallet.available_balance),
                required=float(total_amount)
            )

        # Perform fraud detection check if service is configured
        if self.fraud_detection_service:
            # Create a temporary transaction object for fraud checking
            temp_transaction = Transaction(
                id=f"temp_{idempotency_key or 'check'}",
                wallet_id=wallet_id,
                user_id=wallet.user_id,
                transaction_type=TransactionType.WITHDRAWAL,
                amount=amount,
                currency=wallet.currency,
                status=TransactionStatus.PENDING,
                balance_before=wallet.balance,
                balance_after=wallet.balance - total_amount,
                tenant_id=wallet.tenant_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            fraud_check = await self.fraud_detection_service.check_transaction(
                temp_transaction, wallet, metadata
            )

            # Handle fraud detection decision
            if fraud_check.decision.value == "blocked":
                logger.warning(
                    f"Withdrawal blocked by fraud detection: "
                    f"wallet={wallet_id}, risk_score={fraud_check.risk_score}"
                )
                # Send security notification
                if self.notification_service:
                    try:
                        await self.notification_service.notify_suspicious_activity(
                            wallet,
                            f"Withdrawal blocked due to suspicious activity (risk score: {fraud_check.risk_score})"
                        )
                    except Exception as e:
                        logger.error(f"Failed to send fraud alert notification: {e}")

                raise ValidationError(
                    f"Withdrawal blocked by fraud detection system. "
                    f"Risk score: {fraud_check.risk_score}. "
                    f"Please contact support if you believe this is an error."
                )

            elif fraud_check.requires_review:
                logger.info(
                    f"Withdrawal flagged for review: "
                    f"wallet={wallet_id}, risk_score={fraud_check.risk_score}"
                )
                # Add to metadata for tracking
                if not metadata:
                    metadata = {}
                metadata["fraud_check_id"] = fraud_check.id
                metadata["fraud_risk_score"] = fraud_check.risk_score
                metadata["requires_review"] = True

        # Process withdrawal atomically
        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                # Deduct from balance
                balance_before, balance_after = await self._update_balance_atomic(
                    wallet_id,
                    -total_amount,  # Negative for withdrawal
                    balance_type="balance",
                    session=session
                )

                transaction = await self._create_transaction(
                    wallet_id=wallet_id,
                    user_id=wallet.user_id,
                    transaction_type=TransactionType.WITHDRAWAL,
                    amount=amount,
                    currency=wallet.currency,
                    processing_fee=processing_fee,
                    balance_before=balance_before,
                    balance_after=balance_after,
                    payment_provider=payment_provider,
                    payment_method_id=payment_method_id,
                    idempotency_key=idempotency_key,
                    reference=reference,
                    description=description or f"Withdrawal via {payment_provider.value}",
                    metadata=metadata,
                    tenant_id=wallet.tenant_id,
                    session=session
                )

                # Mark as completed immediately for withdrawals
                # (In production, this might be pending until payout completes)
                await self.update_transaction_status(
                    transaction.id,
                    TransactionStatus.COMPLETED,
                    session=session
                )

        logger.info(
            f"Withdrawal completed: wallet={wallet_id}, amount={amount}, "
            f"transaction={transaction.id}"
        )

        return await self.get_transaction(transaction.id)

    # ============================================================================
    # Webhook Processing
    # ============================================================================

    async def process_deposit_success(
        self,
        transaction_id: str,
        provider_transaction_id: str,
        provider_response: Optional[Dict[str, Any]] = None
    ) -> Transaction:
        """
        Process successful deposit (called from webhook).

        This method:
        1. Validates transaction exists and is pending
        2. Moves amount from pending_balance to balance atomically
        3. Updates transaction status to completed

        Args:
            transaction_id: Internal transaction ID
            provider_transaction_id: Provider's transaction ID
            provider_response: Optional provider response data

        Returns:
            Updated transaction

        Raises:
            TransactionNotFoundError: If transaction not found
        """
        transaction = await self.get_transaction(transaction_id)

        if transaction.status == TransactionStatus.COMPLETED:
            logger.info(f"Transaction {transaction_id} already completed")
            return transaction

        # Process atomically
        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                # Move from pending to confirmed balance
                await self._update_balance_atomic(
                    transaction.wallet_id,
                    transaction.amount,
                    balance_type="balance",
                    session=session
                )

                await self._update_balance_atomic(
                    transaction.wallet_id,
                    -transaction.amount,
                    balance_type="pending_balance",
                    session=session
                )

                # Update transaction with new balance_after
                wallet = await self.get_wallet(transaction.wallet_id, session=session)

                await self.transactions_collection.update_one(
                    {"id": transaction_id},
                    {
                        "$set": {
                            "balance_after": float(wallet.balance),
                            "provider_transaction_id": provider_transaction_id,
                            "provider_response": provider_response or {},
                            "status": TransactionStatus.COMPLETED.value,
                            "completed_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow(),
                        }
                    },
                    session=session
                )

        logger.info(f"Deposit completed: transaction={transaction_id}")

        # Get updated transaction and wallet for notifications
        updated_transaction = await self.get_transaction(transaction_id)
        updated_wallet = await self.get_wallet(updated_transaction.wallet_id)

        # Send notification if service is configured
        if self.notification_service:
            try:
                await self.notification_service.notify_transaction_completed(
                    updated_transaction, updated_wallet
                )
            except Exception as e:
                logger.error(f"Failed to send deposit success notification: {e}")

        return updated_transaction

    async def process_deposit_failure(
        self,
        transaction_id: str,
        reason: str,
        provider_response: Optional[Dict[str, Any]] = None
    ) -> Transaction:
        """
        Process failed deposit (called from webhook).

        This method:
        1. Validates transaction exists and is pending
        2. Removes amount from pending_balance atomically
        3. Updates transaction status to failed

        Args:
            transaction_id: Internal transaction ID
            reason: Failure reason
            provider_response: Optional provider response data

        Returns:
            Updated transaction
        """
        transaction = await self.get_transaction(transaction_id)

        if transaction.status == TransactionStatus.FAILED:
            logger.info(f"Transaction {transaction_id} already failed")
            return transaction

        # Process atomically
        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                # Remove from pending balance
                await self._update_balance_atomic(
                    transaction.wallet_id,
                    -transaction.amount,
                    balance_type="pending_balance",
                    session=session
                )

                # Update transaction
                await self.transactions_collection.update_one(
                    {"id": transaction_id},
                    {
                        "$set": {
                            "provider_response": provider_response or {},
                            "status": TransactionStatus.FAILED.value,
                            "failed_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow(),
                            "metadata.failure_reason": reason,
                        }
                    },
                    session=session
                )

        logger.info(f"Deposit failed: transaction={transaction_id}, reason={reason}")

        # Get updated transaction and wallet for notifications
        updated_transaction = await self.get_transaction(transaction_id)
        updated_wallet = await self.get_wallet(updated_transaction.wallet_id)

        # Send notification if service is configured
        if self.notification_service:
            try:
                await self.notification_service.notify_transaction_failed(
                    updated_transaction, updated_wallet, reason
                )
            except Exception as e:
                logger.error(f"Failed to send deposit failure notification: {e}")

        return updated_transaction

    # ============================================================================
    # Refund Operations
    # ============================================================================

    async def refund(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None,
        reason: str = "requested_by_customer",
        idempotency_key: Optional[str] = None
    ) -> Transaction:
        """
        Refund a transaction.

        Args:
            transaction_id: Original transaction ID to refund
            amount: Optional partial refund amount (None = full refund)
            reason: Refund reason
            idempotency_key: Optional idempotency key

        Returns:
            Refund transaction

        Raises:
            TransactionNotFoundError: If original transaction not found
            ValidationError: If transaction cannot be refunded
            ProviderAPIError: If provider refund fails
        """
        # Check idempotency
        if idempotency_key:
            existing = await self._check_idempotency(idempotency_key)
            if existing:
                logger.info(f"Duplicate refund detected: {idempotency_key}")
                raise DuplicateTransactionError(idempotency_key=idempotency_key)

        # Get original transaction
        original_tx = await self.get_transaction(transaction_id)

        # Validate transaction can be refunded
        if original_tx.status != TransactionStatus.COMPLETED:
            raise ValidationError("Can only refund completed transactions")

        if original_tx.transaction_type != TransactionType.DEPOSIT:
            raise ValidationError("Can only refund deposit transactions")

        # Determine refund amount
        refund_amount = amount if amount else original_tx.amount

        if refund_amount > original_tx.amount:
            raise ValidationError(
                f"Refund amount ({refund_amount}) cannot exceed "
                f"original amount ({original_tx.amount})"
            )

        # Get wallet
        wallet = await self.get_wallet(original_tx.wallet_id)

        # Check wallet has sufficient balance
        if wallet.available_balance < refund_amount:
            raise InsufficientBalanceError(
                available=float(wallet.available_balance),
                required=float(refund_amount)
            )

        # Get provider and initiate refund
        if original_tx.payment_provider:
            provider = self.get_provider(original_tx.payment_provider)

            try:
                await provider.refund_payment(
                    transaction_id=original_tx.provider_transaction_id,
                    amount=refund_amount,
                    reason=reason
                )
            except Exception as e:
                logger.error(f"Provider refund failed: {e}")
                raise ProviderAPIError(
                    provider=original_tx.payment_provider.value,
                    message=str(e)
                )

        # Process refund atomically
        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                # Deduct from balance
                balance_before, balance_after = await self._update_balance_atomic(
                    original_tx.wallet_id,
                    -refund_amount,
                    balance_type="balance",
                    session=session
                )

                # Create refund transaction
                refund_tx = await self._create_transaction(
                    wallet_id=original_tx.wallet_id,
                    user_id=original_tx.user_id,
                    transaction_type=TransactionType.REFUND,
                    amount=refund_amount,
                    currency=original_tx.currency,
                    processing_fee=Decimal("0.00"),
                    balance_before=balance_before,
                    balance_after=balance_after,
                    payment_provider=original_tx.payment_provider,
                    payment_method_id=original_tx.payment_method_id,
                    provider_transaction_id=original_tx.provider_transaction_id,
                    idempotency_key=idempotency_key,
                    reference=original_tx.id,  # Reference to original transaction
                    description=f"Refund for transaction {original_tx.id}",
                    metadata={"original_transaction_id": original_tx.id, "reason": reason},
                    tenant_id=original_tx.tenant_id,
                    session=session
                )

                # Mark as completed
                await self.update_transaction_status(
                    refund_tx.id,
                    TransactionStatus.COMPLETED,
                    session=session
                )

        logger.info(
            f"Refund completed: original={transaction_id}, "
            f"refund={refund_tx.id}, amount={refund_amount}"
        )

        return await self.get_transaction(refund_tx.id)

    # =========================================================================
    # BACKWARD COMPATIBILITY METHODS (from wallet.py)
    # =========================================================================

    async def credit(
        self,
        wallet_id: str,
        amount: Decimal,
        description: str,
        reference: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Transaction:
        """
        Credit (add money to) a wallet - backward compatibility method.

        This method provides compatibility with the old wallet.py API.
        For new code, use deposit() for external deposits or internal operations.

        Args:
            wallet_id: Wallet ID
            amount: Amount to credit
            description: Transaction description
            reference: External payment reference
            idempotency_key: Idempotency key for duplicate prevention
            metadata: Additional metadata

        Returns:
            Transaction object

        Raises:
            WalletNotFoundError: If wallet not found
            WalletSuspendedError: If wallet is suspended
            WalletClosedError: If wallet is closed
            DuplicateTransactionError: If idempotency key already exists

        Example:
            ```python
            transaction = await wallet_service.credit(
                wallet_id="wallet123",
                amount=Decimal("100.00"),
                description="Manual credit",
                idempotency_key="unique-123"
            )
            ```
        """
        # Check idempotency
        if idempotency_key:
            existing = await self._check_idempotency(idempotency_key)
            if existing:
                logger.info(f"Duplicate credit transaction detected: {idempotency_key}")
                from .exceptions import DuplicateTransactionError
                raise DuplicateTransactionError(
                    f"Transaction with idempotency key '{idempotency_key}' already exists"
                )

        # Get wallet
        wallet = await self.get_wallet(wallet_id)
        if not wallet:
            from .exceptions import WalletNotFoundError
            raise WalletNotFoundError(f"Wallet not found: {wallet_id}")

        if wallet.status == WalletStatus.SUSPENDED:
            from .exceptions import WalletSuspendedError
            raise WalletSuspendedError(f"Wallet is suspended: {wallet_id}")

        if wallet.status == WalletStatus.CLOSED:
            from .exceptions import WalletClosedError
            raise WalletClosedError(f"Wallet is closed: {wallet_id}")

        # Update balance atomically
        balance_before = wallet.balance
        balance_after = balance_before + amount

        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                # Update wallet balance
                await self._update_balance_atomic(
                    wallet_id=wallet_id,
                    amount=amount,
                    session=session
                )

                # Create transaction record
                transaction = await self._create_transaction(
                    wallet_id=wallet_id,
                    user_id=wallet.user_id,
                    transaction_type=TransactionType.CREDIT,
                    amount=amount,
                    currency=wallet.currency,
                    processing_fee=Decimal("0.00"),
                    balance_before=balance_before,
                    balance_after=balance_after,
                    payment_provider=PaymentProvider.MANUAL,
                    payment_method_id=None,
                    provider_transaction_id=None,
                    idempotency_key=idempotency_key,
                    reference=reference,
                    description=description,
                    metadata=metadata or {},
                    tenant_id=wallet.tenant_id,
                    session=session
                )

                # Mark as completed
                await self.update_transaction_status(
                    transaction.id,
                    TransactionStatus.COMPLETED,
                    session=session
                )

        logger.info(f"Wallet credited: {wallet_id}, amount={amount}, new_balance={balance_after}")
        return await self.get_transaction(transaction.id)

    async def debit(
        self,
        wallet_id: str,
        amount: Decimal,
        description: str,
        idempotency_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        allow_negative: bool = False
    ) -> Transaction:
        """
        Debit (deduct money from) a wallet - backward compatibility method.

        This method provides compatibility with the old wallet.py API.
        For new code, use withdraw() for external withdrawals.

        Args:
            wallet_id: Wallet ID
            amount: Amount to debit
            description: Transaction description
            idempotency_key: Idempotency key for duplicate prevention
            metadata: Additional metadata
            allow_negative: Allow negative balance (default False)

        Returns:
            Transaction object

        Raises:
            WalletNotFoundError: If wallet not found
            WalletSuspendedError: If wallet is suspended
            WalletClosedError: If wallet is closed
            InsufficientBalanceError: If insufficient balance and allow_negative=False
            DuplicateTransactionError: If idempotency key already exists

        Example:
            ```python
            transaction = await wallet_service.debit(
                wallet_id="wallet123",
                amount=Decimal("10.00"),
                description="Usage charge",
                allow_negative=False
            )
            ```
        """
        # Check idempotency
        if idempotency_key:
            existing = await self._check_idempotency(idempotency_key)
            if existing:
                logger.info(f"Duplicate debit transaction detected: {idempotency_key}")
                from .exceptions import DuplicateTransactionError
                raise DuplicateTransactionError(
                    f"Transaction with idempotency key '{idempotency_key}' already exists"
                )

        # Get wallet
        wallet = await self.get_wallet(wallet_id)
        if not wallet:
            from .exceptions import WalletNotFoundError
            raise WalletNotFoundError(f"Wallet not found: {wallet_id}")

        if wallet.status == WalletStatus.SUSPENDED:
            from .exceptions import WalletSuspendedError
            raise WalletSuspendedError(f"Wallet is suspended: {wallet_id}")

        if wallet.status == WalletStatus.CLOSED:
            from .exceptions import WalletClosedError
            raise WalletClosedError(f"Wallet is closed: {wallet_id}")

        # Check sufficient balance (unless allow_negative=True)
        if not allow_negative and wallet.available_balance < amount:
            from .exceptions import InsufficientBalanceError
            raise InsufficientBalanceError(
                available=float(wallet.available_balance),
                required=float(amount)
            )

        # Update balance atomically
        balance_before = wallet.balance
        balance_after = balance_before - amount

        # Update balance atomically using MongoDB transactions
        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                # Update wallet balance
                await self._update_balance_atomic(
                    wallet_id=wallet_id,
                    amount=-amount,
                    session=session
                )

                # Create transaction record
                transaction = await self._create_transaction(
                    wallet_id=wallet_id,
                    user_id=wallet.user_id,
                    transaction_type=TransactionType.DEBIT,
                    amount=amount,
                    currency=wallet.currency,
                    processing_fee=Decimal("0.00"),
                    balance_before=balance_before,
                    balance_after=balance_after,
                    payment_provider=PaymentProvider.MANUAL,
                    payment_method_id=None,
                    provider_transaction_id=None,
                    idempotency_key=idempotency_key,
                    reference=None,
                    description=description,
                    metadata=metadata or {},
                    tenant_id=wallet.tenant_id,
                    session=session
                )

                # Mark as completed
                await self.update_transaction_status(
                    transaction.id,
                    TransactionStatus.COMPLETED,
                    session=session
                )

                # Check for low balance alert
                if wallet.low_balance_alert_enabled and balance_after < wallet.low_balance_threshold:
                    logger.warning(
                        f"Low balance alert: wallet={wallet_id}, "
                        f"balance={balance_after}, threshold={wallet.low_balance_threshold}"
                    )
                    # Add flag to metadata for notification service
                    metadata = metadata or {}
                    metadata['low_balance_alert'] = True

        logger.info(f"Wallet debited: {wallet_id}, amount={amount}, new_balance={balance_after}")
        return await self.get_transaction(transaction.id)

    async def get_balance(self, wallet_id: str) -> Decimal:
        """
        Get current wallet balance - backward compatibility method.

        Args:
            wallet_id: Wallet ID

        Returns:
            Current balance

        Raises:
            WalletNotFoundError: If wallet not found

        Example:
            ```python
            balance = await wallet_service.get_balance("wallet123")
            print(f"Balance: {balance}")
            ```
        """
        wallet = await self.get_wallet(wallet_id)
        if not wallet:
            from .exceptions import WalletNotFoundError
            raise WalletNotFoundError(f"Wallet not found: {wallet_id}")
        return wallet.balance

    async def get_transactions(
        self,
        wallet_id: str,
        limit: int = 100,
        skip: int = 0,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Transaction]:
        """
        Get transaction history for a wallet - backward compatibility method.

        This method provides compatibility with the old wallet.py API.
        For new code, use list_transactions() which returns a structured response.

        Args:
            wallet_id: Wallet ID
            limit: Maximum number of transactions to return
            skip: Number of transactions to skip (pagination)
            transaction_type: Filter by transaction type
            status: Filter by transaction status
            start_date: Filter transactions after this date
            end_date: Filter transactions before this date

        Returns:
            List of Transaction objects

        Example:
            ```python
            transactions = await wallet_service.get_transactions(
                wallet_id="wallet123",
                limit=50,
                transaction_type=TransactionType.DEBIT
            )
            ```
        """
        response = await self.list_transactions(
            wallet_id=wallet_id,
            limit=limit,
            offset=skip,
            transaction_type=transaction_type,
            status=status,
            start_date=start_date,
            end_date=end_date
        )
        return response.transactions
