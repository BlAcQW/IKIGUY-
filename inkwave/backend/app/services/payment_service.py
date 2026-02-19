"""
Payment service for InkWave.

Handles book purchases, saved cards, and payment processing.
"""

import logging
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from apps.shared.services.expresspay_service import (
    ExpressPayService,
    ExpressPayConfig,
    PaymentRequest,
    TokenizeCardRequest,
    ChargeTokenRequest,
)
from ..models.payment import (
    PaymentGateway,
    PaymentStatus,
    SavedCard,
    PaymentTransaction,
    SaveCardRequest,
    BookPurchaseRequest,
)

logger = logging.getLogger(__name__)


class InkWavePaymentService:
    """
    Payment service for InkWave.

    Manages book purchases, saved cards, and payment processing
    using ExpressPay Ghana.
    """

    def __init__(self, db_client: AsyncIOMotorClient, database_name: str = "inkwave"):
        """
        Initialize payment service.

        Args:
            db_client: MongoDB client
            database_name: Database name
        """
        self.db = db_client[database_name]
        self.saved_cards = self.db["saved_cards"]
        self.payment_transactions = self.db["payment_transactions"]
        self.books = self.db["books"]

        # Initialize ExpressPay service
        self.expresspay = self._init_expresspay()

        # Initialize indexes
        self._init_indexes()

        logger.info("InkWave Payment Service initialized")

    def _init_expresspay(self) -> Optional[ExpressPayService]:
        """
        Initialize ExpressPay service from environment variables.

        Returns:
            ExpressPay service or None if not configured
        """
        try:
            merchant_id = os.getenv("EXPRESSPAY_MERCHANT_ID")
            api_key = os.getenv("EXPRESSPAY_API_KEY")
            api_secret = os.getenv("EXPRESSPAY_API_SECRET")
            # Support both EXPRESSPAY_SANDBOX and EXPRESSPAY_TEST_MODE
            sandbox_env = os.getenv("EXPRESSPAY_SANDBOX") or os.getenv("EXPRESSPAY_TEST_MODE", "true")
            sandbox = sandbox_env.lower() == "true"

            if not all([merchant_id, api_key, api_secret]):
                logger.warning(f"ExpressPay credentials not configured - merchant_id: {bool(merchant_id)}, api_key: {bool(api_key)}, api_secret: {bool(api_secret)}")
                return None

            config = ExpressPayConfig(
                merchant_id=merchant_id,
                api_key=api_key,
                api_secret=api_secret,
                sandbox=sandbox,
            )

            return ExpressPayService(config)

        except Exception as e:
            logger.error(f"Failed to initialize ExpressPay: {str(e)}")
            return None

    def _init_indexes(self):
        """Initialize database indexes."""
        # Saved cards indexes
        self.saved_cards.create_index("user_id")
        self.saved_cards.create_index([("user_id", 1), ("is_default", -1)])

        # Payment transactions indexes
        self.payment_transactions.create_index("user_id")
        self.payment_transactions.create_index("order_id", unique=True)
        self.payment_transactions.create_index([("user_id", 1), ("status", 1)])

        logger.info("Payment service indexes created")

    async def get_book_price(self, book_id: str) -> Optional[Decimal]:
        """
        Get book price.

        Args:
            book_id: Book ID

        Returns:
            Book price or None
        """
        try:
            book = await self.books.find_one({"book_id": book_id})
            if not book:
                return None

            price = book.get("price", 0.0)
            return Decimal(str(price))

        except Exception as e:
            logger.error(f"Failed to get book price: {str(e)}")
            return None

    async def save_card(
        self,
        user_id: str,
        card_request: SaveCardRequest,
        customer_email: str,
        customer_name: str,
    ) -> Dict[str, Any]:
        """
        Save a card for future payments.

        Args:
            user_id: User ID
            card_request: Card details
            customer_email: Customer email
            customer_name: Customer name

        Returns:
            Saved card info or error
        """
        try:
            if not self.expresspay:
                return {"success": False, "error": "ExpressPay not configured"}

            # Tokenize card with ExpressPay
            tokenize_request = TokenizeCardRequest(
                card_number=card_request.card_number,
                card_expiry_month=card_request.card_expiry_month,
                card_expiry_year=card_request.card_expiry_year,
                card_cvv=card_request.card_cvv,
                customer_email=customer_email,
                customer_name=customer_name,
            )

            result = await self.expresspay.tokenize_card(tokenize_request)

            if not result.get("success"):
                return result

            # If set as default, unset other default cards
            if card_request.set_as_default:
                await self.saved_cards.update_many(
                    {"user_id": user_id, "is_default": True},
                    {"$set": {"is_default": False}}
                )

            # Save card to database
            card = SavedCard(
                user_id=user_id,
                gateway=PaymentGateway.EXPRESSPAY,
                token=result["token"],
                last4=result["card_last4"],
                card_type=result.get("card_type"),
                expiry_month=result["expiry_month"],
                expiry_year=result["expiry_year"],
                is_default=card_request.set_as_default,
            )

            card_dict = card.dict(exclude={"id"})
            insert_result = await self.saved_cards.insert_one(card_dict)

            logger.info(f"Card saved for user {user_id}")

            return {
                "success": True,
                "card_id": str(insert_result.inserted_id),
                "last4": card.last4,
                "card_type": card.card_type,
            }

        except Exception as e:
            logger.error(f"Failed to save card: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Failed to save card: {str(e)}"}

    async def get_saved_cards(self, user_id: str) -> List[SavedCard]:
        """
        Get user's saved cards.

        Args:
            user_id: User ID

        Returns:
            List of saved cards
        """
        try:
            cursor = self.saved_cards.find(
                {"user_id": user_id, "is_active": True}
            ).sort([("is_default", -1), ("created_at", -1)])

            cards = []
            async for card_doc in cursor:
                card_doc["id"] = str(card_doc.pop("_id"))
                cards.append(SavedCard(**card_doc))

            return cards

        except Exception as e:
            logger.error(f"Failed to get saved cards: {str(e)}")
            return []

    async def delete_saved_card(self, user_id: str, card_id: str) -> bool:
        """
        Delete a saved card.

        Args:
            user_id: User ID
            card_id: Card ID

        Returns:
            True if deleted
        """
        try:
            result = await self.saved_cards.update_one(
                {"_id": ObjectId(card_id), "user_id": user_id},
                {"$set": {"is_active": False}}
            )
            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Failed to delete card: {str(e)}")
            return False

    async def purchase_book(
        self,
        user_id: str,
        request: BookPurchaseRequest,
        customer_email: str,
        customer_name: str,
    ) -> Dict[str, Any]:
        """
        Purchase a book.

        Args:
            user_id: User ID
            request: Purchase request
            customer_email: Customer email
            customer_name: Customer name

        Returns:
            Payment response
        """
        try:
            if not self.expresspay:
                return {"success": False, "error": "ExpressPay not configured"}

            # Get book price
            price = await self.get_book_price(request.book_id)
            if price is None:
                return {"success": False, "error": "Book not found"}

            if price == 0:
                return {"success": False, "error": "Book is free"}

            # Generate unique order ID
            order_id = f"BOOK_{request.book_id}_{user_id}_{int(datetime.utcnow().timestamp())}"

            # Create payment transaction record
            transaction = PaymentTransaction(
                user_id=user_id,
                order_id=order_id,
                gateway=PaymentGateway.EXPRESSPAY,
                status=PaymentStatus.PENDING,
                amount=float(price),
                currency="GHS",
                order_type="book_purchase",
                order_desc=f"Purchase of book {request.book_id}",
                order_items=[{"book_id": request.book_id, "price": float(price)}],
                customer_email=customer_email,
                customer_name=customer_name,
                redirect_url=request.redirect_url,
            )

            # Save transaction
            tx_dict = transaction.dict(exclude={"id"})
            await self.payment_transactions.insert_one(tx_dict)

            # If using saved card, charge it
            if request.use_saved_card and request.saved_card_id:
                return await self._charge_saved_card(
                    user_id,
                    request.saved_card_id,
                    order_id,
                    price,
                    f"Purchase of book {request.book_id}"
                )

            # Otherwise, initiate new payment
            payment_request = PaymentRequest(
                amount=price,
                currency="GHS",
                order_id=order_id,
                order_desc=f"Purchase of book {request.book_id}",
                redirect_url=request.redirect_url,
                customer_email=customer_email,
                customer_name=customer_name,
            )

            result = await self.expresspay.initiate_payment(payment_request)

            if result.get("success"):
                # Update transaction with payment URL
                await self.payment_transactions.update_one(
                    {"order_id": order_id},
                    {
                        "$set": {
                            "payment_reference": result.get("token"),
                            "status": PaymentStatus.PROCESSING.value,
                        }
                    }
                )

                return {
                    "success": True,
                    "order_id": order_id,
                    "payment_url": result.get("payment_url"),
                    "requires_redirect": True,
                }

            return result

        except Exception as e:
            logger.error(f"Failed to purchase book: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Purchase failed: {str(e)}"}

    async def _charge_saved_card(
        self,
        user_id: str,
        card_id: str,
        order_id: str,
        amount: Decimal,
        description: str,
    ) -> Dict[str, Any]:
        """
        Charge a saved card.

        Args:
            user_id: User ID
            card_id: Saved card ID
            order_id: Order ID
            amount: Amount to charge
            description: Charge description

        Returns:
            Payment result
        """
        try:
            # Get saved card
            card_doc = await self.saved_cards.find_one(
                {"_id": ObjectId(card_id), "user_id": user_id, "is_active": True}
            )

            if not card_doc:
                return {"success": False, "error": "Card not found"}

            card = SavedCard(**{**card_doc, "id": str(card_doc["_id"])})

            # Charge the card
            charge_request = ChargeTokenRequest(
                token=card.token,
                amount=amount,
                currency="GHS",
                order_id=order_id,
                order_desc=description,
            )

            result = await self.expresspay.charge_token(charge_request)

            if result.get("success"):
                # Update transaction
                await self.payment_transactions.update_one(
                    {"order_id": order_id},
                    {
                        "$set": {
                            "status": PaymentStatus.COMPLETED.value,
                            "transaction_id": result.get("transaction_id"),
                            "saved_card_id": card_id,
                            "card_last4": card.last4,
                            "completed_at": datetime.utcnow(),
                        }
                    }
                )

                return {
                    "success": True,
                    "order_id": order_id,
                    "transaction_id": result.get("transaction_id"),
                    "requires_redirect": False,
                    "message": "Payment successful",
                }

            # Payment failed
            await self.payment_transactions.update_one(
                {"order_id": order_id},
                {
                    "$set": {
                        "status": PaymentStatus.FAILED.value,
                        "error_message": result.get("error"),
                        "failed_at": datetime.utcnow(),
                    }
                }
            )

            return result

        except Exception as e:
            logger.error(f"Failed to charge saved card: {str(e)}")
            return {"success": False, "error": f"Payment failed: {str(e)}"}

    async def verify_payment(
        self,
        order_id: str,
        token: str
    ) -> Dict[str, Any]:
        """
        Verify payment status.

        Args:
            order_id: Order ID
            token: Payment token

        Returns:
            Verification result
        """
        try:
            if not self.expresspay:
                return {"success": False, "error": "ExpressPay not configured"}

            result = await self.expresspay.verify_payment(order_id, token)

            if result.get("success") and result.get("paid"):
                # Update transaction
                await self.payment_transactions.update_one(
                    {"order_id": order_id},
                    {
                        "$set": {
                            "status": PaymentStatus.COMPLETED.value,
                            "transaction_id": result.get("transaction_id"),
                            "payment_method": result.get("payment_method"),
                            "completed_at": datetime.utcnow(),
                        }
                    }
                )

                return {
                    "success": True,
                    "paid": True,
                    "order_id": order_id,
                    "transaction_id": result.get("transaction_id"),
                    "amount": result.get("amount"),
                }

            return result

        except Exception as e:
            logger.error(f"Failed to verify payment: {str(e)}")
            return {"success": False, "error": f"Verification failed: {str(e)}"}

    async def get_transaction(self, order_id: str) -> Optional[PaymentTransaction]:
        """
        Get transaction by order ID.

        Args:
            order_id: Order ID

        Returns:
            Payment transaction or None
        """
        try:
            tx_doc = await self.payment_transactions.find_one({"order_id": order_id})
            if not tx_doc:
                return None

            tx_doc["id"] = str(tx_doc.pop("_id"))
            return PaymentTransaction(**tx_doc)

        except Exception as e:
            logger.error(f"Failed to get transaction: {str(e)}")
            return None

    async def close(self):
        """Close service connections."""
        if self.expresspay:
            await self.expresspay.close()


# Dependency for FastAPI
_payment_service: Optional[InkWavePaymentService] = None


async def get_payment_service() -> InkWavePaymentService:
    """
    Get payment service instance.

    Returns:
        Payment service
    """
    global _payment_service
    if _payment_service is None:
        # Initialize from environment
        from motor.motor_asyncio import AsyncIOMotorClient
        mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        client = AsyncIOMotorClient(mongo_url)
        _payment_service = InkWavePaymentService(client)
    return _payment_service
