"""
Unit tests for Wallet Service with Organization Isolation (Simplified).

Tests database-level CRUD operations to verify:
1. Wallets are properly scoped to organizations
2. Organization isolation is enforced at database level
3. All database operations work correctly with organization_id

Uses real MongoDB test database with actual CRUD operations.
Does NOT require payment provider configuration.
"""
import pytest
from datetime import datetime
from decimal import Decimal
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import sys
import uuid

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.services.wallet_service import WalletService
from apps.shared.integration.wallet import Currency

# Test configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/?authSource=admin")
TEST_DATABASE = "kasaai_core_test"

# Test data
TEST_ORG_A = "test_wallet_org_a_" + datetime.now().strftime("%Y%m%d%H%M%S")
TEST_ORG_B = "test_wallet_org_b_" + datetime.now().strftime("%Y%m%d%H%M%S")


@pytest.fixture
async def db_client():
    """Create test database client."""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[TEST_DATABASE]
    yield db
    # Cleanup after all tests
    await db.wallets.delete_many({"tenant_id": {"$in": [TEST_ORG_A, TEST_ORG_B]}})
    await db.transactions.delete_many({"tenant_id": {"$in": [TEST_ORG_A, TEST_ORG_B]}})
    await db.payment_methods.delete_many({"tenant_id": {"$in": [TEST_ORG_A, TEST_ORG_B]}})
    client.close()


@pytest.fixture
async def wallet_service(db_client):
    """Create wallet service instance."""
    service = WalletService(db_client)
    return service


@pytest.mark.asyncio
async def test_wallet_full_crud_lifecycle(wallet_service, db_client):
    """
    Test complete CRUD lifecycle for wallets with organization isolation.
    Flow: CREATE -> READ -> UPDATE -> DELETE with organization checks.
    """
    print("\n" + "="*80)
    print("TEST: Wallet Full CRUD Lifecycle with Organization Isolation")
    print("="*80)

    user_id = "user_wallet_crud_" + str(uuid.uuid4())[:8]

    # CREATE: Create wallet in Org A
    print(f"\n📝 CREATE: Creating wallet for {user_id} in Org A")
    wallet_a = await wallet_service.get_or_create_wallet(
        user_id=user_id,
        currency=Currency.USD,
        organization_id=TEST_ORG_A
    )
    assert wallet_a is not None
    assert wallet_a.user_id == user_id
    assert wallet_a.tenant_id == TEST_ORG_A
    assert wallet_a.balance == Decimal("0.00")
    print(f"✅ VERIFY: Wallet created with ID {wallet_a.id}")

    # READ: Verify wallet exists in database
    print(f"\n📖 READ: Verifying wallet in database")
    wallet_doc = await db_client.wallets.find_one({
        "user_id": user_id,
        "tenant_id": TEST_ORG_A
    })
    assert wallet_doc is not None
    assert wallet_doc["tenant_id"] == TEST_ORG_A
    assert Decimal(str(wallet_doc["balance"])) == Decimal("0.00")
    print(f"✅ VERIFY: Found wallet in database for Org A")

    # UPDATE: Update wallet balance directly in database (simulating a transaction)
    print(f"\n✏️ UPDATE: Updating wallet balance")
    new_balance = Decimal("100.50")
    update_result = await db_client.wallets.update_one(
        {"user_id": user_id, "tenant_id": TEST_ORG_A},
        {"$set": {"balance": str(new_balance), "updated_at": datetime.utcnow()}}
    )
    assert update_result.modified_count == 1
    print(f"✅ VERIFY: Updated wallet balance to {new_balance}")

    # READ: Verify update
    print(f"\n📖 READ: Verifying balance update")
    updated_wallet = await wallet_service.get_or_create_wallet(
        user_id=user_id,
        currency=Currency.USD,
        organization_id=TEST_ORG_A
    )
    assert updated_wallet.balance == new_balance
    print(f"✅ VERIFY: Balance updated successfully")

    # ISOLATION TEST: Create wallet in Org B for same user
    print(f"\n🔒 ISOLATION: Creating wallet in Org B for same user")
    wallet_b = await wallet_service.get_or_create_wallet(
        user_id=user_id,
        currency=Currency.USD,
        organization_id=TEST_ORG_B
    )
    assert wallet_b.id != wallet_a.id
    assert wallet_b.tenant_id == TEST_ORG_B
    assert wallet_b.balance == Decimal("0.00")  # New wallet starts at 0
    print(f"✅ VERIFY: Separate wallet created for Org B")

    # COUNT: Count wallets per organization
    print(f"\n📊 COUNT: Counting wallets by organization")
    count_org_a = await db_client.wallets.count_documents({"tenant_id": TEST_ORG_A})
    count_org_b = await db_client.wallets.count_documents({"tenant_id": TEST_ORG_B})
    assert count_org_a >= 1
    assert count_org_b >= 1
    print(f"✅ VERIFY: Org A has {count_org_a} wallet(s), Org B has {count_org_b} wallet(s)")

    # DELETE: Remove Org A wallet from database
    print(f"\n🗑️ DELETE: Removing Org A wallet")
    delete_result = await db_client.wallets.delete_one({
        "user_id": user_id,
        "tenant_id": TEST_ORG_A
    })
    assert delete_result.deleted_count == 1
    print(f"✅ VERIFY: Deleted Org A wallet")

    # VERIFY: Org A wallet gone, Org B wallet still exists
    print(f"\n📖 VERIFY: Confirming deletion")
    deleted_wallet = await db_client.wallets.find_one({
        "user_id": user_id,
        "tenant_id": TEST_ORG_A
    })
    assert deleted_wallet is None
    print(f"✅ VERIFY: Org A wallet no longer in database")

    existing_wallet = await db_client.wallets.find_one({
        "user_id": user_id,
        "tenant_id": TEST_ORG_B
    })
    assert existing_wallet is not None
    print(f"✅ VERIFY: Org B wallet still exists")

    print(f"\n✅ TEST PASSED: Wallet CRUD with organization isolation")


@pytest.mark.asyncio
async def test_wallets_isolated_by_organization(wallet_service, db_client):
    """Test that wallets are completely isolated between organizations."""
    print("\n" + "="*80)
    print("TEST: Wallet Organization Isolation")
    print("="*80)

    user_id = "user_isolation_" + str(uuid.uuid4())[:8]

    # CREATE: Create 3 wallets in Org A
    print(f"\n📝 CREATE: Creating 3 users in Org A")
    for i in range(3):
        await wallet_service.get_or_create_wallet(
            user_id=f"{user_id}_a_{i}",
            currency=Currency.USD,
            organization_id=TEST_ORG_A
        )

    # CREATE: Create 2 wallets in Org B
    print(f"\n📝 CREATE: Creating 2 users in Org B")
    for i in range(2):
        await wallet_service.get_or_create_wallet(
            user_id=f"{user_id}_b_{i}",
            currency=Currency.USD,
            organization_id=TEST_ORG_B
        )

    # READ: Query Org A wallets
    print(f"\n📖 READ: Querying Org A wallets")
    org_a_wallets = await db_client.wallets.find({
        "tenant_id": TEST_ORG_A,
        "user_id": {"$regex": f"^{user_id}_a_"}
    }).to_list(length=100)
    assert len(org_a_wallets) == 3
    print(f"✅ VERIFY: Found {len(org_a_wallets)} wallets in Org A")

    # READ: Query Org B wallets
    print(f"\n📖 READ: Querying Org B wallets")
    org_b_wallets = await db_client.wallets.find({
        "tenant_id": TEST_ORG_B,
        "user_id": {"$regex": f"^{user_id}_b_"}
    }).to_list(length=100)
    assert len(org_b_wallets) == 2
    print(f"✅ VERIFY: Found {len(org_b_wallets)} wallets in Org B")

    # ISOLATION TEST: Verify no cross-organization visibility
    print(f"\n🔒 ISOLATION: Verifying no cross-org visibility")
    org_a_sees_b = await db_client.wallets.find({
        "tenant_id": TEST_ORG_A,
        "user_id": {"$regex": f"^{user_id}_b_"}
    }).to_list(length=100)
    assert len(org_a_sees_b) == 0
    print(f"✅ VERIFY: Org A cannot see Org B wallets")

    org_b_sees_a = await db_client.wallets.find({
        "tenant_id": TEST_ORG_B,
        "user_id": {"$regex": f"^{user_id}_a_"}
    }).to_list(length=100)
    assert len(org_b_sees_a) == 0
    print(f"✅ VERIFY: Org B cannot see Org A wallets")

    print(f"\n✅ TEST PASSED: Wallets are isolated by organization")


@pytest.mark.asyncio
async def test_get_or_create_wallet_idempotency(wallet_service, db_client):
    """Test that get_or_create_wallet is idempotent."""
    print("\n" + "="*80)
    print("TEST: Get or Create Wallet Idempotency")
    print("="*80)

    user_id = "user_idempotent_" + str(uuid.uuid4())[:8]

    # CREATE: First call creates wallet
    print(f"\n📝 CREATE: First call - creating wallet")
    wallet_1 = await wallet_service.get_or_create_wallet(
        user_id=user_id,
        currency=Currency.USD,
        organization_id=TEST_ORG_A
    )
    assert wallet_1 is not None
    wallet_1_id = wallet_1.id
    print(f"✅ VERIFY: Created wallet with ID {wallet_1_id}")

    # READ: Second call returns existing wallet
    print(f"\n📖 READ: Second call - should return existing wallet")
    wallet_2 = await wallet_service.get_or_create_wallet(
        user_id=user_id,
        currency=Currency.USD,
        organization_id=TEST_ORG_A
    )
    assert wallet_2.id == wallet_1_id
    print(f"✅ VERIFY: Returned same wallet ID {wallet_2.id}")

    # READ: Third call still returns same wallet
    print(f"\n📖 READ: Third call - should still return existing wallet")
    wallet_3 = await wallet_service.get_or_create_wallet(
        user_id=user_id,
        currency=Currency.USD,
        organization_id=TEST_ORG_A
    )
    assert wallet_3.id == wallet_1_id
    print(f"✅ VERIFY: Still same wallet ID {wallet_3.id}")

    # VERIFY: Only one wallet exists in database
    print(f"\n📊 VERIFY: Checking database has only one wallet")
    count = await db_client.wallets.count_documents({
        "user_id": user_id,
        "tenant_id": TEST_ORG_A
    })
    assert count == 1
    print(f"✅ VERIFY: Only 1 wallet in database")

    print(f"\n✅ TEST PASSED: get_or_create_wallet is idempotent")


@pytest.mark.asyncio
async def test_payment_methods_organization_isolation(wallet_service, db_client):
    """Test that payment methods are properly scoped to organizations."""
    print("\n" + "="*80)
    print("TEST: Payment Methods Organization Isolation")
    print("="*80)

    user_id = "user_pm_" + str(uuid.uuid4())[:8]

    # CREATE: Create wallets in both orgs
    print(f"\n📝 CREATE: Creating wallets in both organizations")
    wallet_a = await wallet_service.get_or_create_wallet(
        user_id=user_id,
        currency=Currency.USD,
        organization_id=TEST_ORG_A
    )
    wallet_b = await wallet_service.get_or_create_wallet(
        user_id=user_id,
        currency=Currency.USD,
        organization_id=TEST_ORG_B
    )

    # CREATE: Add payment methods to Org A
    print(f"\n📝 CREATE: Adding payment methods to Org A")
    pm_a1 = {
        "user_id": user_id,
        "tenant_id": TEST_ORG_A,
        "provider": "stripe",
        "type": "card",
        "is_default": True,
        "is_active": True,
        "details": {"last4": "1111", "brand": "visa"},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    pm_a2 = {
        "user_id": user_id,
        "tenant_id": TEST_ORG_A,
        "provider": "paystack",
        "type": "card",
        "is_default": False,
        "is_active": True,
        "details": {"last4": "2222", "brand": "mastercard"},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    await db_client.payment_methods.insert_many([pm_a1, pm_a2])
    print(f"✅ VERIFY: Added 2 payment methods to Org A")

    # CREATE: Add payment method to Org B
    print(f"\n📝 CREATE: Adding payment method to Org B")
    pm_b1 = {
        "user_id": user_id,
        "tenant_id": TEST_ORG_B,
        "provider": "flutterwave",
        "type": "card",
        "is_default": True,
        "is_active": True,
        "details": {"last4": "3333", "brand": "visa"},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    await db_client.payment_methods.insert_one(pm_b1)
    print(f"✅ VERIFY: Added 1 payment method to Org B")

    # READ: Get payment methods for Org A
    print(f"\n📖 READ: Getting payment methods for Org A")
    org_a_pms = await db_client.payment_methods.find({
        "user_id": user_id,
        "tenant_id": TEST_ORG_A
    }).to_list(length=100)
    assert len(org_a_pms) == 2
    print(f"✅ VERIFY: Org A has 2 payment methods")

    # READ: Get payment methods for Org B
    print(f"\n📖 READ: Getting payment methods for Org B")
    org_b_pms = await db_client.payment_methods.find({
        "user_id": user_id,
        "tenant_id": TEST_ORG_B
    }).to_list(length=100)
    assert len(org_b_pms) == 1
    print(f"✅ VERIFY: Org B has 1 payment method")

    # ISOLATION TEST: Verify no cross-org visibility
    print(f"\n🔒 ISOLATION: Verifying payment method isolation")
    org_a_details = {pm["details"]["last4"] for pm in org_a_pms}
    org_b_details = {pm["details"]["last4"] for pm in org_b_pms}
    assert "1111" in org_a_details
    assert "2222" in org_a_details
    assert "3333" not in org_a_details
    assert "3333" in org_b_details
    assert "1111" not in org_b_details
    print(f"✅ VERIFY: Payment methods properly isolated")

    # DELETE: Remove one payment method from Org A
    print(f"\n🗑️ DELETE: Removing one payment method from Org A")
    delete_result = await db_client.payment_methods.delete_one({
        "user_id": user_id,
        "tenant_id": TEST_ORG_A,
        "details.last4": "1111"
    })
    assert delete_result.deleted_count == 1
    print(f"✅ VERIFY: Deleted 1 payment method from Org A")

    # VERIFY: Org A now has 1, Org B still has 1
    print(f"\n📊 VERIFY: Checking final counts")
    final_org_a_count = await db_client.payment_methods.count_documents({
        "user_id": user_id,
        "tenant_id": TEST_ORG_A
    })
    final_org_b_count = await db_client.payment_methods.count_documents({
        "user_id": user_id,
        "tenant_id": TEST_ORG_B
    })
    assert final_org_a_count == 1
    assert final_org_b_count == 1
    print(f"✅ VERIFY: Org A: 1, Org B: 1")

    print(f"\n✅ TEST PASSED: Payment methods organization isolation")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--no-cov"])
