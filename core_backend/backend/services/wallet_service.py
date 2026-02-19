"""
Wallet Service Adapter for Core Backend.

This adapter wraps the shared wallet library and provides core_backend-specific
features while maintaining API compatibility with the existing wallet service.

Features Added:
- Uses shared WalletService for core operations (with MongoDB atomicity)
- Maintains existing API for routes compatibility
- Adds core_backend-specific features (PDF receipts, notifications)
- Uses shared WebhookProcessor for reliability

Author: KasaAI Team
Date: 2025-10-27
"""

import logging
import os
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import shared wallet library
from apps.shared.integration.wallet import (
    WalletService as SharedWalletService,
    WebhookProcessor,
    Currency,
    TransactionType,
    TransactionStatus,
    PaymentProvider,
    PaymentMethodType,
    Wallet as SharedWallet,
    Transaction as SharedTransaction,
    PaymentMethod as SharedPaymentMethod,
    # Import fraud detection and notifications
    FraudDetectionService,
    NotificationService,
    # Import new exception types for better error handling
    WalletNotFoundError,
    InsufficientBalanceError,
    WalletSuspendedError,
    WalletClosedError,
)

# Import core_backend-specific services
from ..models.wallet import (
    Wallet,
    Transaction,
    PaymentMethod,
    WebhookEvent,
    ProviderConfig,
)

# Import core_backend specific services (will be kept)
try:
    from .wallet_notifications import wallet_notification_service
    HAS_NOTIFICATIONS = True
except ImportError:
    HAS_NOTIFICATIONS = False
    logger = logging.getLogger(__name__)
    logger.warning("Wallet notification service not available")

logger = logging.getLogger(__name__)


class WalletService:
    """
    Core Backend Wallet Service Adapter.

    Wraps the shared wallet library and adds core_backend-specific features:
    - PDF receipt generation (delegated to routes)
    - Email/SMS notifications
    - Legacy API compatibility
    - Auto-reload functionality (future enhancement)

    This maintains the exact same API as the old WalletService for
    seamless integration with existing routes.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize wallet service adapter with fraud detection and notifications.

        Args:
            db: MongoDB database connection
        """
        self.db = db

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

        # Initialize shared wallet service with fraud detection and notifications
        self.shared_wallet = SharedWalletService(
            database=db,
            fraud_detection_service=fraud_service,
            notification_service=notification_service
        )

        # Initialize shared webhook processor
        self.webhook_processor = WebhookProcessor(
            wallet_service=self.shared_wallet,
            database=db
        )

        # Keep references to MongoDB collections for legacy compatibility
        self.wallets = db.wallets
        self.transactions = db.transactions
        self.payment_methods = db.payment_methods
        self.webhook_events = db.webhook_events
        self.provider_configs = db.provider_configs

        logger.info("✓ Wallet Service Adapter initialized with shared library")

    # ============================================================================
    # WALLET MANAGEMENT (Delegated to Shared Library)
    # ============================================================================

    async def get_or_create_wallet(
        self,
        user_id: str,
        currency: Currency = Currency.USD,
        tenant_id: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Wallet:
        """
        Get existing wallet or create new one.

        Delegates to shared library for MongoDB atomicity.

        Args:
            user_id: User ID
            currency: Wallet currency
            tenant_id: Optional tenant ID (deprecated, use organization_id)
            organization_id: Optional organization ID for multi-tenant isolation

        Returns:
            Wallet instance
        """
        # Use organization_id if provided, fallback to tenant_id for backward compatibility
        tenant_or_org_id = organization_id or tenant_id or "core_backend"

        try:
            # Try to get existing wallet
            shared_wallet = await self.shared_wallet.get_wallet_by_user(
                user_id=user_id,
                currency=currency,
                tenant_id=tenant_or_org_id
            )
        except Exception:
            # Create new wallet if doesn't exist
            shared_wallet = await self.shared_wallet.create_wallet(
                user_id=user_id,
                currency=currency,
                tenant_id=tenant_or_org_id
            )

        # Convert to core_backend Wallet model for compatibility
        return self._convert_to_core_wallet(shared_wallet)

    async def get_wallet_balance(
        self,
        user_id: str,
        currency: Currency = Currency.USD
    ) -> Dict[str, Any]:
        """
        Get wallet balance information.

        Args:
            user_id: User ID
            currency: Wallet currency

        Returns:
            Balance information dict
        """
        wallet = await self.get_or_create_wallet(user_id, currency)

        return {
            "wallet_id": wallet.id,
            "balance": float(wallet.balance),
            "pending_balance": float(wallet.pending_balance),
            "reserved_balance": float(wallet.reserved_balance),
            "available_balance": float(wallet.available_balance),
            "total_balance": float(wallet.total_balance),
            "currency": wallet.currency.value,
            "last_transaction_at": wallet.last_transaction_at.isoformat() if wallet.last_transaction_at else None
        }

    async def update_wallet_balance(
        self,
        wallet_id: str,
        amount: Decimal,
        transaction_type: str
    ) -> Wallet:
        """
        Update wallet balance after transaction.

        NOTE: This is handled automatically by shared library's atomic transactions.
        Kept for API compatibility but delegates to shared library.

        Args:
            wallet_id: Wallet ID
            amount: Amount to add/subtract
            transaction_type: Type of transaction

        Returns:
            Updated wallet
        """
        # Get wallet using shared library
        shared_wallet = await self.shared_wallet.get_wallet(wallet_id)

        # Convert to core model
        return self._convert_to_core_wallet(shared_wallet)

    # ============================================================================
    # PAYMENT METHODS (Delegated to Shared Library)
    # ============================================================================

    async def add_payment_method(
        self,
        user_id: str,
        provider: PaymentProvider,
        method_type: PaymentMethodType,
        display_name: str,
        provider_payment_method_id: Optional[str] = None,
        **kwargs
    ) -> PaymentMethod:
        """
        Add new payment method for user.

        Stores directly in MongoDB (payment method management not in shared library yet).

        Args:
            user_id: User ID
            provider: Payment provider
            method_type: Payment method type
            display_name: Display name
            provider_payment_method_id: Provider's payment method ID
            **kwargs: Additional method-specific fields

        Returns:
            Created payment method
        """
        # Create shared payment method model
        shared_method = SharedPaymentMethod(
            user_id=user_id,
            provider=provider,
            method_type=method_type,
            display_name=display_name,
            provider_payment_method_id=provider_payment_method_id,
            tenant_id="core_backend",
            **kwargs
        )

        # If this is first payment method, make it default
        existing_methods = await self.payment_methods.count_documents({"user_id": user_id})
        if existing_methods == 0:
            shared_method.is_default = True

        # Store in database
        await self.payment_methods.insert_one(shared_method.dict())
        logger.info(f"Added payment method {shared_method.id} for user {user_id}")

        # Convert to core model
        return self._convert_to_core_payment_method(shared_method)

    async def get_payment_methods(
        self,
        user_id: str,
        organization_id: Optional[str] = None
    ) -> List[PaymentMethod]:
        """
        Get all payment methods for user, optionally filtered by organization.

        Args:
            user_id: User ID
            organization_id: Optional organization ID for filtering

        Returns:
            List of payment methods
        """
        # Build query filter
        query_filter = {"user_id": user_id, "is_active": True}
        if organization_id:
            query_filter["organization_id"] = organization_id

        # Query database directly
        methods = []
        cursor = self.payment_methods.find(query_filter)

        async for method_doc in cursor:
            shared_method = SharedPaymentMethod(**method_doc)
            methods.append(self._convert_to_core_payment_method(shared_method))

        logger.info(f"Retrieved {len(methods)} payment methods for user={user_id}, organization={organization_id}")
        return methods

    async def set_default_payment_method(
        self,
        user_id: str,
        payment_method_id: str,
        organization_id: Optional[str] = None
    ) -> bool:
        """
        Set default payment method.

        Args:
            user_id: User ID
            payment_method_id: Payment method ID
            organization_id: Optional organization ID for validation

        Returns:
            Success status
        """
        # Build query filter
        query_filter = {"user_id": user_id}
        if organization_id:
            query_filter["organization_id"] = organization_id

        # Unset all existing defaults
        await self.payment_methods.update_many(
            query_filter,
            {"$set": {"is_default": False}}
        )

        # Set new default
        result = await self.payment_methods.update_one(
            {"id": payment_method_id, **query_filter},
            {"$set": {"is_default": True, "updated_at": datetime.utcnow()}}
        )

        success = result.modified_count > 0
        logger.info(f"Set default payment method {payment_method_id} for user={user_id}, organization={organization_id}, success={success}")
        return success

    # ============================================================================
    # DEPOSITS (Delegated to Shared Library)
    # ============================================================================

    async def create_deposit(
        self,
        user_id: str,
        amount: Decimal,
        currency: Currency,
        payment_method_id: str,
        description: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Transaction:
        """
        Create deposit transaction.

        Uses shared library for atomic transaction processing.

        Args:
            user_id: User ID
            amount: Deposit amount
            currency: Currency
            payment_method_id: Payment method to use
            description: Optional description
            organization_id: Optional organization ID for multi-tenant isolation

        Returns:
            Created transaction
        """
        # Get wallet with organization context
        wallet = await self.get_or_create_wallet(user_id, currency, organization_id=organization_id)

        # Delegate to shared library (handles atomicity and provider integration)
        # Note: payment_provider is required instead of currency
        # Use MANUAL provider for admin/internal deposits, can be overridden
        shared_transaction, payment_result = await self.shared_wallet.deposit(
            wallet_id=wallet.id,
            amount=amount,
            payment_provider=PaymentProvider.MANUAL,  # Use MANUAL for internal deposits
            payment_method_id=payment_method_id,
            description=description or f"Wallet deposit"
        )

        # Convert to core model
        transaction = self._convert_to_core_transaction(shared_transaction)

        logger.info(f"Created deposit transaction {transaction.id} for ${amount}, organization={organization_id}")

        return transaction

    async def _calculate_processing_fee(
        self,
        amount: Decimal,
        provider: PaymentProvider
    ) -> Decimal:
        """
        Calculate processing fee for payment provider.

        NOTE: This is now handled by shared library's provider configuration.
        Kept for backward compatibility.

        Args:
            amount: Transaction amount
            provider: Payment provider

        Returns:
            Processing fee
        """
        # Fee structures (should be from database via shared library)
        fee_configs = {
            PaymentProvider.STRIPE: {"percent": Decimal("2.9"), "fixed": Decimal("0.30")},
            PaymentProvider.FLUTTERWAVE: {"percent": Decimal("1.4"), "fixed": Decimal("0.00")},
            PaymentProvider.MTN_MOMO: {"percent": Decimal("1.5"), "fixed": Decimal("0.10")},
            PaymentProvider.VODAFONE_CASH: {"percent": Decimal("1.5"), "fixed": Decimal("0.10")},
            PaymentProvider.AIRTELTIGO_MONEY: {"percent": Decimal("1.5"), "fixed": Decimal("0.10")},
            PaymentProvider.MPESA: {"percent": Decimal("1.0"), "fixed": Decimal("0.00")},
        }

        config = fee_configs.get(provider, {"percent": Decimal("0.0"), "fixed": Decimal("0.0")})
        return (amount * config["percent"] / Decimal("100")) + config["fixed"]

    # ============================================================================
    # WEBHOOK HANDLERS (Delegated to Shared WebhookProcessor)
    # ============================================================================

    async def handle_webhook(
        self,
        provider: PaymentProvider,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Handle payment webhook from provider.

        Uses shared WebhookProcessor for reliability and retry logic.

        Args:
            provider: Payment provider
            payload: Webhook payload
            signature: Webhook signature
            headers: Request headers

        Returns:
            Processing result
        """
        # Delegate to shared webhook processor
        # This provides automatic retry, signature verification, and error handling
        result = await self.webhook_processor.process_webhook(
            provider=provider,
            payload=payload,
            signature=signature,
            headers=headers or {}
        )

        # Send notifications if transaction completed successfully
        if result.get("success") and result.get("transaction_id"):
            try:
                await self._send_transaction_notifications(result["transaction_id"])
            except Exception as e:
                # Don't fail webhook if notifications fail
                logger.error(f"Failed to send notifications: {e}")

        return result

    # ============================================================================
    # NOTIFICATIONS (Core Backend Specific)
    # ============================================================================

    async def _send_transaction_notifications(self, transaction_id: str):
        """
        Send email/SMS notifications for transaction.

        This is a core_backend-specific feature that uses the existing
        wallet_notification_service.

        Args:
            transaction_id: Transaction ID
        """
        if not HAS_NOTIFICATIONS:
            logger.warning("Notifications service not available")
            return

        try:
            # Get transaction details
            shared_transaction = await self.shared_wallet.get_transaction(transaction_id)
            if not shared_transaction:
                logger.error(f"Transaction {transaction_id} not found for notifications")
                return

            # Only send for completed deposits
            if (shared_transaction.transaction_type != TransactionType.DEPOSIT or
                shared_transaction.status != TransactionStatus.COMPLETED):
                return

            # Get user email
            user_doc = await self.db.users.find_one({"id": shared_transaction.user_id})
            if not user_doc or not user_doc.get("email"):
                logger.warning(f"No email found for user {shared_transaction.user_id}")
                return

            user_email = user_doc["email"]

            # Get payment method display name
            payment_method_display = "Unknown"
            if shared_transaction.payment_method_id:
                method_doc = await self.payment_methods.find_one(
                    {"id": shared_transaction.payment_method_id}
                )
                if method_doc:
                    payment_method_display = method_doc.get("display_name", "Unknown")

            # Get wallet for balance
            wallet = await self.shared_wallet.get_wallet(shared_transaction.wallet_id)

            # Send email notification
            asyncio.create_task(
                wallet_notification_service.send_deposit_success_email(
                    to_email=user_email,
                    amount=shared_transaction.amount,
                    currency=shared_transaction.currency.value,
                    transaction_id=shared_transaction.id,
                    payment_method=payment_method_display,
                    processing_fee=shared_transaction.processing_fee,
                    new_balance=wallet.balance,
                    transaction_date=shared_transaction.completed_at.strftime(
                        "%B %d, %Y at %I:%M %p UTC"
                    ) if shared_transaction.completed_at else "Unknown"
                )
            )
            logger.info(f"Queued deposit success email for user {shared_transaction.user_id}")

            # Send SMS for mobile money transactions
            if shared_transaction.payment_provider in [
                PaymentProvider.MTN_MOMO,
                PaymentProvider.VODAFONE_CASH,
                PaymentProvider.AIRTELTIGO_MONEY,
                PaymentProvider.MPESA
            ]:
                if shared_transaction.payment_method_id:
                    method_doc = await self.payment_methods.find_one(
                        {"id": shared_transaction.payment_method_id}
                    )
                    if method_doc and method_doc.get("phone_number"):
                        phone_number = method_doc["phone_number"]

                        asyncio.create_task(
                            wallet_notification_service.send_deposit_success_sms(
                                to_number=phone_number,
                                amount=shared_transaction.amount,
                                currency=shared_transaction.currency.value,
                                new_balance=wallet.balance
                            )
                        )
                        logger.info(f"Queued deposit success SMS for {phone_number}")

        except Exception as e:
            # Don't fail transaction if notification fails
            logger.error(f"Failed to send deposit notifications: {e}")

    # ============================================================================
    # TRANSACTION MANAGEMENT (Delegated to Shared Library)
    # ============================================================================

    async def get_transaction(
        self,
        transaction_id: str,
        organization_id: Optional[str] = None
    ) -> Optional[Transaction]:
        """
        Get transaction by ID.

        Args:
            transaction_id: Transaction ID
            organization_id: Optional organization ID for validation

        Returns:
            Transaction or None if not found
        """
        shared_transaction = await self.shared_wallet.get_transaction(transaction_id)
        if shared_transaction:
            # If organization_id is provided, verify the transaction belongs to the organization
            if organization_id and hasattr(shared_transaction, 'metadata'):
                tx_org_id = shared_transaction.metadata.get('organization_id') if shared_transaction.metadata else None
                if tx_org_id and tx_org_id != organization_id:
                    logger.warning(f"Transaction {transaction_id} belongs to different organization")
                    return None

            logger.info(f"Retrieved transaction {transaction_id} for organization={organization_id}")
            return self._convert_to_core_transaction(shared_transaction)
        return None

    async def get_transaction_history(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        organization_id: Optional[str] = None
    ) -> List[Transaction]:
        """
        Get transaction history for user.

        Args:
            user_id: User ID
            limit: Number of transactions
            offset: Offset for pagination
            organization_id: Optional organization ID for filtering

        Returns:
            List of transactions
        """
        transaction_list = await self.shared_wallet.list_transactions(
            user_id=user_id,
            limit=limit,
            offset=offset  # Fixed: use offset instead of skip
        )

        # Extract transactions from response (list_transactions returns TransactionListResponse)
        shared_transactions = transaction_list.transactions

        # Filter by organization if provided
        filtered_transactions = []
        for t in shared_transactions:
            if organization_id:
                # Check if transaction belongs to the organization
                tx_org_id = t.metadata.get('organization_id') if t.metadata else None
                if tx_org_id and tx_org_id != organization_id:
                    continue  # Skip transactions from other organizations
            filtered_transactions.append(self._convert_to_core_transaction(t))

        logger.info(f"Retrieved {len(filtered_transactions)} transactions for user={user_id}, organization={organization_id}")
        return filtered_transactions

    # ============================================================================
    # LEGACY COMPATIBILITY HELPERS
    # ============================================================================

    async def _complete_transaction(
        self,
        transaction_id: str,
        provider_response: Dict[str, Any]
    ):
        """
        Complete a successful transaction.

        NOTE: This is now handled automatically by shared library.
        Kept for backward compatibility.

        Args:
            transaction_id: Transaction ID
            provider_response: Provider response data
        """
        # Shared library handles this automatically via webhook processor
        logger.info(f"Transaction {transaction_id} completion handled by shared library")

    async def _fail_transaction(self, transaction_id: str, failure_reason: str):
        """
        Mark transaction as failed.

        NOTE: This is now handled automatically by shared library.
        Kept for backward compatibility.

        Args:
            transaction_id: Transaction ID
            failure_reason: Reason for failure
        """
        # Shared library handles this automatically via webhook processor
        logger.info(f"Transaction {transaction_id} failure handled by shared library")

    async def _get_provider_config(self, provider: PaymentProvider) -> ProviderConfig:
        """
        Get provider configuration.

        Args:
            provider: Payment provider

        Returns:
            Provider config
        """
        config_doc = await self.provider_configs.find_one({
            "provider": provider.value,
            "is_active": True
        })

        if not config_doc:
            raise ValueError(f"No configuration found for {provider.value}")

        return ProviderConfig(**config_doc)

    # ============================================================================
    # MODEL CONVERSION HELPERS
    # ============================================================================

    def _convert_to_core_wallet(self, shared_wallet: SharedWallet) -> Wallet:
        """
        Convert shared Wallet model to core_backend Wallet model.

        Args:
            shared_wallet: Shared wallet instance

        Returns:
            Core backend wallet instance
        """
        return Wallet(
            id=shared_wallet.id,
            user_id=shared_wallet.user_id,
            tenant_id=shared_wallet.tenant_id,
            balance=shared_wallet.balance,
            pending_balance=shared_wallet.pending_balance,
            reserved_balance=shared_wallet.reserved_balance,
            currency=shared_wallet.currency,
            status=shared_wallet.status,
            low_balance_threshold=shared_wallet.low_balance_threshold,
            low_balance_alert_enabled=shared_wallet.low_balance_alert_enabled,
            last_low_balance_alert_at=shared_wallet.last_low_balance_alert_at,
            auto_reload_enabled=shared_wallet.auto_reload_enabled,
            auto_reload_threshold=shared_wallet.auto_reload_threshold,
            auto_reload_amount=shared_wallet.auto_reload_amount,
            auto_reload_payment_method_id=shared_wallet.auto_reload_payment_method_id,
            metadata=shared_wallet.metadata,
            created_at=shared_wallet.created_at,
            updated_at=shared_wallet.updated_at,
            last_transaction_at=shared_wallet.last_transaction_at
        )

    def _convert_to_core_transaction(
        self,
        shared_transaction: SharedTransaction
    ) -> Transaction:
        """
        Convert shared Transaction model to core_backend Transaction model.

        Args:
            shared_transaction: Shared transaction instance

        Returns:
            Core backend transaction instance
        """
        return Transaction(
            id=shared_transaction.id,
            wallet_id=shared_transaction.wallet_id,
            user_id=shared_transaction.user_id,
            tenant_id=shared_transaction.tenant_id,
            transaction_type=shared_transaction.transaction_type,
            status=shared_transaction.status,
            amount=shared_transaction.amount,
            currency=shared_transaction.currency,
            processing_fee=shared_transaction.processing_fee,
            total_amount=shared_transaction.total_amount,
            balance_before=shared_transaction.balance_before,
            balance_after=shared_transaction.balance_after,
            payment_method_id=shared_transaction.payment_method_id,
            payment_provider=shared_transaction.payment_provider,
            provider_transaction_id=shared_transaction.provider_transaction_id,
            provider_response=shared_transaction.provider_response,
            idempotency_key=shared_transaction.idempotency_key,
            reference=shared_transaction.reference,
            description=shared_transaction.description,
            created_at=shared_transaction.created_at,
            updated_at=shared_transaction.updated_at,
            completed_at=shared_transaction.completed_at,
            failed_at=shared_transaction.failed_at,
            failure_reason=shared_transaction.failure_reason,
            retry_count=shared_transaction.retry_count,
            refunded_from=shared_transaction.refunded_from,
            refund_amount=shared_transaction.refund_amount,
            metadata=shared_transaction.metadata
        )

    def _convert_to_core_payment_method(
        self,
        shared_method: SharedPaymentMethod
    ) -> PaymentMethod:
        """
        Convert shared PaymentMethod model to core_backend PaymentMethod model.

        Args:
            shared_method: Shared payment method instance

        Returns:
            Core backend payment method instance
        """
        return PaymentMethod(
            id=shared_method.id,
            user_id=shared_method.user_id,
            tenant_id=shared_method.tenant_id,
            provider=shared_method.provider,
            method_type=shared_method.method_type,
            display_name=shared_method.display_name,
            nickname=shared_method.nickname,
            provider_payment_method_id=shared_method.provider_payment_method_id,
            provider_customer_id=shared_method.provider_customer_id,
            card_last4=shared_method.card_last4,
            card_brand=shared_method.card_brand,
            card_exp_month=shared_method.card_exp_month,
            card_exp_year=shared_method.card_exp_year,
            card_fingerprint=shared_method.card_fingerprint,
            phone_number=shared_method.phone_number,
            phone_number_masked=shared_method.phone_number_masked,
            network=shared_method.network,
            bank_name=shared_method.bank_name,
            account_last4=shared_method.account_last4,
            account_holder_name=shared_method.account_holder_name,
            is_active=shared_method.is_active,
            is_default=shared_method.is_default,
            is_verified=shared_method.is_verified,
            metadata=shared_method.metadata,
            created_at=shared_method.created_at,
            updated_at=shared_method.updated_at,
            last_used_at=shared_method.last_used_at
        )

    async def close(self):
        """Close HTTP client (if needed)."""
        # Shared library handles cleanup
        pass
