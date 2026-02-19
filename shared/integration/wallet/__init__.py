"""
KasaAI Shared Wallet Library

A comprehensive, production-ready wallet system for managing payments,
balances, and transactions across multiple payment providers.

Features:
- Multi-provider support (Stripe, Flutterwave, Paystack, Mobile Money)
- Transaction atomicity and idempotency
- Fraud detection
- Webhook processing with retries
- Email/SMS notifications
- Balance reconciliation
- Multi-currency support
- Multi-tenancy support

Usage:
    ```python
    from apps.shared.integration.wallet import WalletService, Currency
    from apps.shared.integration.wallet.providers import StripeProvider

    # Initialize service
    wallet_service = await WalletService.create(
        mongodb_uri="mongodb://localhost:27017",
        database_name="my_app_wallets"
    )

    # Register providers
    wallet_service.register_provider(StripeProvider(stripe_config))

    # Create or get wallet
    wallet = await wallet_service.get_or_create_wallet(
        user_id="user123",
        currency=Currency.GHS
    )

    # Create deposit
    transaction = await wallet_service.create_deposit(
        user_id="user123",
        amount=Decimal("100.00"),
        currency=Currency.GHS,
        payment_method_id="pm_xxx"
    )
    ```

Author: KasaAI Team
Date: 2025-10-27
Version: 2.0.0 (Consolidated)
"""

# Import core models
from .models import (
    # Enums
    Currency,
    TransactionType,
    TransactionStatus,
    PaymentProvider,
    PaymentGateway,  # Backward compatibility alias
    PaymentMethodType,
    WalletStatus,
    # Core models
    Wallet,
    Transaction,
    PaymentMethod,
    ProviderConfig,
    WebhookEvent,
    PaymentInitiationResult,
    # Request/Response models
    DepositRequest,
    WithdrawalRequest,
    RefundRequest,
    WalletBalanceResponse,
    TransactionResponse,
    TransactionListResponse,
    PaymentMethodResponse,
    PaymentMethodListResponse,
)

# Import exceptions
from .exceptions import (
    WalletError,
    WalletNotFoundError,
    InsufficientBalanceError,
    DuplicateTransactionError,
    TransactionNotFoundError,
    WalletSuspendedError,
    WalletClosedError,
    PaymentMethodNotFoundError,
    PaymentMethodNotVerifiedError,
    ProviderError,
    ProviderNotConfiguredError,
    ProviderAPIError,
    PaymentDeclinedError,
    InvalidWebhookSignatureError,
    RefundError,
    FraudDetectionError,
    ValidationError,
    ConfigurationError,
    DatabaseError,
)

# Import core services
from .wallet_service import WalletService
from .webhook_processor import WebhookProcessor
from .notification_service import NotificationService
from .notification_models import (
    NotificationType,
    NotificationChannel,
    NotificationStatus,
    NotificationPriority,
    NotificationFrequency,
    Notification,
    NotificationPreference,
    NotificationTemplate,
)
from .fraud_detection_service import FraudDetectionService
from .fraud_models import (
    FraudRuleType,
    FraudAction,
    FraudCheckDecision,
    FraudCheckStatus,
    RiskLevel,
    FraudRule,
    FraudCheck,
    UserRiskProfile,
)

# Import analytics and reporting services
from .analytics import (
    WalletAnalyticsService,
    MetricPeriod,
)
from .reports import (
    BalanceReconciliationService,
    ReconciliationReport,
    ReconciliationStatus,
    Discrepancy,
    DiscrepancyType,
)
from .auto_reload_service import AutoReloadService

__version__ = "2.0.0"
__author__ = "KasaAI Team"

__all__ = [
    # Enums
    "Currency",
    "TransactionType",
    "TransactionStatus",
    "PaymentProvider",
    "PaymentGateway",  # Backward compatibility alias
    "PaymentMethodType",
    "WalletStatus",
    # Core models
    "Wallet",
    "Transaction",
    "PaymentMethod",
    "ProviderConfig",
    "WebhookEvent",
    "PaymentInitiationResult",
    # Request/Response models
    "DepositRequest",
    "WithdrawalRequest",
    "RefundRequest",
    "WalletBalanceResponse",
    "TransactionResponse",
    "TransactionListResponse",
    "PaymentMethodResponse",
    "PaymentMethodListResponse",
    # Exceptions
    "WalletError",
    "WalletNotFoundError",
    "InsufficientBalanceError",
    "DuplicateTransactionError",
    "TransactionNotFoundError",
    "WalletSuspendedError",
    "WalletClosedError",
    "PaymentMethodNotFoundError",
    "PaymentMethodNotVerifiedError",
    "ProviderError",
    "ProviderNotConfiguredError",
    "ProviderAPIError",
    "PaymentDeclinedError",
    "InvalidWebhookSignatureError",
    "RefundError",
    "FraudDetectionError",
    "ValidationError",
    "ConfigurationError",
    "DatabaseError",
    # Core services
    "WalletService",
    "WebhookProcessor",
    "NotificationService",
    "FraudDetectionService",
    # Notification models
    "NotificationType",
    "NotificationChannel",
    "NotificationStatus",
    "NotificationPriority",
    "NotificationFrequency",
    "Notification",
    "NotificationPreference",
    "NotificationTemplate",
    # Fraud detection models
    "FraudRuleType",
    "FraudAction",
    "FraudCheckDecision",
    "FraudCheckStatus",
    "RiskLevel",
    "FraudRule",
    "FraudCheck",
    "UserRiskProfile",
    # Analytics and reporting
    "WalletAnalyticsService",
    "MetricPeriod",
    "BalanceReconciliationService",
    "ReconciliationReport",
    "ReconciliationStatus",
    "Discrepancy",
    "DiscrepancyType",
    "AutoReloadService",
]


# ============================================================================
# BACKWARD COMPATIBILITY HELPERS
# ============================================================================

async def create_wallet_service_from_env(
    database_name: str = "kasaai_wallets"
) -> WalletService:
    """
    Create WalletService using environment variables - backward compatibility helper.

    This function provides compatibility with the old wallet.py API that had
    a WalletService.create() classmethod.

    Environment variables:
        MONGODB_URI: MongoDB connection string
        PAYSTACK_SECRET_KEY: Paystack secret key (optional)
        STRIPE_SECRET_KEY: Stripe secret key (optional)

    Args:
        database_name: MongoDB database name

    Returns:
        Initialized WalletService

    Raises:
        ValueError: If MONGODB_URI not set

    Example:
        ```python
        from apps.shared.integration.wallet import create_wallet_service_from_env

        wallet_service = await create_wallet_service_from_env(
            database_name="inkwave_wallets"
        )
        ```
    """
    import os
    from motor.motor_asyncio import AsyncIOMotorClient

    # Support both MONGODB_URI and MONGODB_URL (different apps use different names)
    mongodb_uri = os.getenv("MONGODB_URI") or os.getenv("MONGODB_URL")
    if not mongodb_uri:
        raise ValueError("MONGODB_URI or MONGODB_URL environment variable not set")

    # Create MongoDB connection
    client = AsyncIOMotorClient(mongodb_uri)
    database = client[database_name]

    # Create indexes
    await database.wallets.create_index("user_id")
    await database.wallets.create_index([("user_id", 1), ("currency", 1)], unique=True)
    await database.wallets.create_index("status")
    await database.transactions.create_index("wallet_id")
    await database.transactions.create_index("idempotency_key", unique=True, sparse=True)
    await database.transactions.create_index("reference")
    await database.transactions.create_index("created_at")
    await database.transactions.create_index([("wallet_id", 1), ("created_at", -1)])

    # Initialize services
    notification_service = None  # Apps can inject this later if needed
    fraud_detection_service = None  # Apps can inject this later if needed

    return WalletService(
        database=database,
        notification_service=notification_service,
        fraud_detection_service=fraud_detection_service
    )


__all__.append("create_wallet_service_from_env")
