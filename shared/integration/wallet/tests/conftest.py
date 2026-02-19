"""
Test Configuration and Fixtures

This module provides pytest fixtures for wallet system testing:
- MongoDB test database setup/teardown
- Test data fixtures
- Provider mocks
- Cleanup utilities

Author: KasaAI Team
Date: 2025-10-27
"""

import os
import pytest
import asyncio
from decimal import Decimal
from datetime import datetime
from typing import AsyncGenerator, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient

from ..models import (
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
    PaymentInitiationResult,
)
from ..wallet_service import WalletService
from ..webhook_processor import WebhookProcessor
from ..providers.base import BasePaymentProvider


# ============================================================================
# Test Configuration
# ============================================================================

# Get MongoDB test database URL from environment or use default
MONGODB_TEST_URL = os.getenv(
    "MONGODB_TEST_URL",
    "mongodb://admin:aawwER4444%25@127.0.0.1:27017/"
)
TEST_DB_NAME = "kasaai_wallet_test"


# ============================================================================
# Event Loop Configuration
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for the test session.

    This ensures all async tests use the same event loop.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
async def mongodb_client():
    """
    Create MongoDB client for test session.

    Yields:
        AsyncIOMotorClient instance
    """
    client = AsyncIOMotorClient(MONGODB_TEST_URL)
    yield client
    client.close()


@pytest.fixture
async def test_db(mongodb_client):
    """
    Create and clean test database for each test.

    Args:
        mongodb_client: MongoDB client fixture

    Yields:
        MongoDB database instance
    """
    db = mongodb_client[TEST_DB_NAME]

    # Clean up before test
    await db.wallets.delete_many({})
    await db.transactions.delete_many({})
    await db.payment_methods.delete_many({})
    await db.webhook_events.delete_many({})
    await db.reconciliation_reports.delete_many({})
    await db.fraud_alerts.delete_many({})
    await db.auto_reload_logs.delete_many({})

    yield db

    # Clean up after test
    await db.wallets.delete_many({})
    await db.transactions.delete_many({})
    await db.payment_methods.delete_many({})
    await db.webhook_events.delete_many({})
    await db.reconciliation_reports.delete_many({})
    await db.fraud_alerts.delete_many({})
    await db.auto_reload_logs.delete_many({})


@pytest.fixture
async def wallet_service(test_db):
    """
    Create WalletService instance with test database.

    Args:
        test_db: Test database fixture

    Yields:
        WalletService instance
    """
    service = WalletService(database=test_db)
    yield service


@pytest.fixture
async def webhook_processor(wallet_service, test_db):
    """
    Create WebhookProcessor instance with test database.

    Args:
        wallet_service: WalletService fixture
        test_db: Test database fixture

    Yields:
        WebhookProcessor instance
    """
    processor = WebhookProcessor(
        wallet_service=wallet_service,
        database=test_db,
        max_retries=3,
        initial_retry_delay=1,  # 1 second for faster tests
        max_retry_delay=10
    )
    yield processor


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def test_user_id() -> str:
    """Test user ID."""
    return "test_user_123"


@pytest.fixture
def test_tenant_id() -> str:
    """Test tenant ID."""
    return "churchflow"


@pytest.fixture
def test_amount() -> Decimal:
    """Test amount."""
    return Decimal("100.00")


@pytest.fixture
def test_currency() -> Currency:
    """Test currency."""
    return Currency.GHS


@pytest.fixture
async def test_wallet(wallet_service, test_user_id, test_currency, test_tenant_id) -> Wallet:
    """
    Create a test wallet.

    Args:
        wallet_service: WalletService fixture
        test_user_id: Test user ID
        test_currency: Test currency
        test_tenant_id: Test tenant ID

    Returns:
        Created wallet
    """
    wallet = await wallet_service.create_wallet(
        user_id=test_user_id,
        currency=test_currency,
        tenant_id=test_tenant_id,
        low_balance_threshold=Decimal("10.00"),
        low_balance_alert_enabled=True
    )
    return wallet


@pytest.fixture
async def test_wallet_with_balance(
    wallet_service,
    test_wallet,
    test_db
) -> Wallet:
    """
    Create a test wallet with balance.

    Args:
        wallet_service: WalletService fixture
        test_wallet: Test wallet fixture
        test_db: Test database fixture

    Returns:
        Wallet with balance
    """
    # Manually add balance for testing (bypassing payment flow)
    await test_db.wallets.update_one(
        {"id": test_wallet.id},
        {"$set": {"balance": 500.00}}
    )

    return await wallet_service.get_wallet(test_wallet.id)


# ============================================================================
# Provider Config Fixtures
# ============================================================================

@pytest.fixture
def stripe_config() -> ProviderConfig:
    """
    Mock Stripe provider config.

    Returns:
        ProviderConfig for Stripe
    """
    return ProviderConfig(
        provider=PaymentProvider.STRIPE,
        is_active=True,
        is_test_mode=True,
        api_key="test_api_key",
        secret_key="sk_test_123456789",
        webhook_secret="whsec_test_123456789",
        fee_config={
            "percent": 2.9,
            "fixed": 0.30,
            "cap": 10.00
        }
    )


@pytest.fixture
def flutterwave_config() -> ProviderConfig:
    """
    Mock Flutterwave provider config.

    Returns:
        ProviderConfig for Flutterwave
    """
    return ProviderConfig(
        provider=PaymentProvider.FLUTTERWAVE,
        is_active=True,
        is_test_mode=True,
        api_key="test_public_key",
        secret_key="test_secret_key",
        webhook_secret="test_webhook_secret",
        fee_config={
            "percent": 1.4,
            "fixed": 0.00,
            "cap": 5.00
        }
    )


# ============================================================================
# Mock Provider Fixtures
# ============================================================================

class MockPaymentProvider(BasePaymentProvider):
    """
    Mock payment provider for testing.

    This mock provider simulates successful payment processing
    without making actual API calls.
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.payments_initialized = []
        self.webhooks_verified = []
        self.webhooks_processed = []
        self.transactions_checked = []
        self.refunds_processed = []

    async def initialize_payment(
        self,
        amount: Decimal,
        currency: Currency,
        payment_method_id: str = None,
        customer_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> PaymentInitiationResult:
        """Mock payment initialization."""
        self.payments_initialized.append({
            "amount": amount,
            "currency": currency,
            "payment_method_id": payment_method_id,
            "customer_id": customer_id,
            "metadata": metadata
        })

        return PaymentInitiationResult(
            success=True,
            payment_url="https://mock-provider.com/pay/test123",
            reference=f"mock_ref_{len(self.payments_initialized)}",
            amount=amount,
            currency=currency,
            gateway=self.config.provider,
            metadata={
                "status": "pending",
                "mock": True
            }
        )

    async def verify_webhook(
        self,
        payload: Dict[str, Any],
        signature: str = None,
        raw_payload: str = None,
        headers: Dict[str, str] = None
    ) -> bool:
        """Mock webhook verification."""
        self.webhooks_verified.append({
            "payload": payload,
            "signature": signature
        })
        # Accept all webhooks in mock
        return True

    async def process_webhook(
        self,
        payload: Dict[str, Any]
    ) -> tuple[bool, str, Dict[str, Any]]:
        """Mock webhook processing."""
        self.webhooks_processed.append(payload)

        # Extract transaction ID from payload
        transaction_id = payload.get("metadata", {}).get("transaction_id")
        status = payload.get("status", "succeeded")

        return (
            True,
            transaction_id,
            {
                "status": status,
                "provider_transaction_id": payload.get("id", "mock_provider_tx_123"),
                "mock": True
            }
        )

    async def get_transaction_status(
        self,
        transaction_id: str
    ) -> tuple[bool, str, Dict[str, Any]]:
        """Mock transaction status check."""
        self.transactions_checked.append(transaction_id)

        return (
            True,
            "completed",
            {"mock": True, "status": "completed"}
        )

    async def refund_payment(
        self,
        transaction_id: str,
        amount: Decimal = None,
        reason: str = None
    ) -> tuple[bool, str, Dict[str, Any]]:
        """Mock refund processing."""
        self.refunds_processed.append({
            "transaction_id": transaction_id,
            "amount": amount,
            "reason": reason
        })

        return (
            True,
            f"refund_mock_{transaction_id}",
            {"mock": True, "status": "refunded"}
        )


@pytest.fixture
def mock_provider(stripe_config) -> MockPaymentProvider:
    """
    Create mock payment provider.

    Args:
        stripe_config: Provider config fixture

    Returns:
        MockPaymentProvider instance
    """
    return MockPaymentProvider(stripe_config)


@pytest.fixture
async def wallet_service_with_mock_provider(
    wallet_service,
    mock_provider
) -> WalletService:
    """
    Create WalletService with mock provider registered.

    Args:
        wallet_service: WalletService fixture
        mock_provider: Mock provider fixture

    Returns:
        WalletService with mock provider
    """
    wallet_service.register_provider(
        PaymentProvider.STRIPE,
        mock_provider
    )
    return wallet_service


@pytest.fixture
async def webhook_processor_with_mock_provider(
    webhook_processor,
    mock_provider
) -> WebhookProcessor:
    """
    Create WebhookProcessor with mock provider registered.

    Args:
        webhook_processor: WebhookProcessor fixture
        mock_provider: Mock provider fixture

    Returns:
        WebhookProcessor with mock provider
    """
    webhook_processor.register_provider(
        PaymentProvider.STRIPE,
        mock_provider
    )
    return webhook_processor


# ============================================================================
# Helper Fixtures
# ============================================================================

@pytest.fixture
def idempotency_key() -> str:
    """Generate unique idempotency key."""
    import uuid
    return f"test_idem_{uuid.uuid4()}"


@pytest.fixture
def sample_webhook_payload() -> Dict[str, Any]:
    """Sample webhook payload for testing."""
    return {
        "id": "evt_test_123",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test_123",
                "amount": 10000,
                "currency": "ghs",
                "status": "succeeded",
                "metadata": {
                    "transaction_id": "test_tx_123",
                    "wallet_id": "test_wallet_123"
                }
            }
        },
        "metadata": {
            "transaction_id": "test_tx_123"
        },
        "status": "succeeded"
    }
