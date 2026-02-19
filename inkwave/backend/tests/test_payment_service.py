"""
Unit tests for ExpressPay payment service.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from app.services.payment_service import InkWavePaymentService
from app.models.payment import (
    PaymentGateway,
    PaymentStatus,
    SaveCardRequest,
    BookPurchaseRequest,
)


@pytest.mark.asyncio
async def test_save_card_validation():
    """Test card save request validation."""
    # Valid card request
    card_request = SaveCardRequest(
        card_number="4111111111111111",
        card_expiry_month="12",
        card_expiry_year="25",
        card_cvv="123",
        set_as_default=True,
    )
    assert card_request.card_number == "4111111111111111"
    assert card_request.card_expiry_month == "12"
    assert card_request.set_as_default is True


@pytest.mark.asyncio
async def test_book_purchase_request_validation():
    """Test book purchase request validation."""
    # Purchase with saved card
    purchase_request = BookPurchaseRequest(
        book_id="test_book_123",
        use_saved_card=True,
        saved_card_id="card_abc123",
        redirect_url="https://inkwave.com/payment/success",
    )
    assert purchase_request.book_id == "test_book_123"
    assert purchase_request.use_saved_card is True
    assert purchase_request.saved_card_id == "card_abc123"

    # Purchase with new card
    new_card_purchase = BookPurchaseRequest(
        book_id="test_book_456",
        use_saved_card=False,
        save_card=True,
    )
    assert new_card_purchase.use_saved_card is False
    assert new_card_purchase.save_card is True


@pytest.mark.asyncio
async def test_payment_status_enum():
    """Test payment status enum values."""
    assert PaymentStatus.PENDING.value == "pending"
    assert PaymentStatus.PROCESSING.value == "processing"
    assert PaymentStatus.COMPLETED.value == "completed"
    assert PaymentStatus.FAILED.value == "failed"


@pytest.mark.asyncio
async def test_payment_gateway_enum():
    """Test payment gateway enum values."""
    assert PaymentGateway.EXPRESSPAY.value == "expresspay"
    assert PaymentGateway.PAYSTACK.value == "paystack"
    assert PaymentGateway.STRIPE.value == "stripe"


# Integration tests (require MongoDB)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_payment_service_initialization(test_db_client):
    """Test payment service initializes correctly."""
    service = InkWavePaymentService(test_db_client, "inkwave_test")
    assert service.db is not None
    assert service.saved_cards is not None
    assert service.payment_transactions is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_book_price(test_db_client):
    """Test getting book price from database."""
    service = InkWavePaymentService(test_db_client, "inkwave_test")

    # Insert test book
    await service.books.insert_one({
        "book_id": "test_book_price",
        "title": "Test Book",
        "price": 29.99,
    })

    # Get price
    price = await service.get_book_price("test_book_price")
    assert price == Decimal("29.99")

    # Cleanup
    await service.books.delete_one({"book_id": "test_book_price"})


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_saved_cards_empty(test_db_client):
    """Test getting saved cards returns empty list for new user."""
    service = InkWavePaymentService(test_db_client, "inkwave_test")

    cards = await service.get_saved_cards("test_user_123")
    assert isinstance(cards, list)
    assert len(cards) == 0
