"""
Payment Service for EstateFlow.

Handles payment processing with multiple gateways (Stripe, Flutterwave),
mobile money integration, and payment tracking.

Now using centralized payment gateway clients from @shared/.
"""

import logging
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4
from decimal import Decimal
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import shared payment gateway clients
from shared.services.payment_gateways import StripeClient, FlutterwaveClient

from app.models.payment import (
    Payment,
    PaymentCreate,
    PaymentConfirm,
    PaymentRefund,
    PaymentListFilters,
    PaymentListResponse,
    PaymentStats,
    PaymentStatus,
    PaymentGateway,
    PaymentMethod,
    PaymentMetadata,
    PaymentIntent,
    WebhookEvent,
    CardDetails,
    MobileMoneyDetails,
)

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for managing payments across multiple gateways."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize payment service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db.payments
        self.webhooks_collection = db.payment_webhooks

        # Initialize gateway clients using shared implementations
        self._stripe_client = None
        self._flutterwave_client = None

    def _get_stripe_client(self) -> StripeClient:
        """
        Get or create Stripe client (shared implementation).

        Returns:
            StripeClient instance from @shared/
        """
        if self._stripe_client is None:
            self._stripe_client = StripeClient(
                secret_key=os.getenv("STRIPE_SECRET_KEY"),
                publishable_key=os.getenv("STRIPE_PUBLISHABLE_KEY"),
                webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET")
            )
            logger.info("Stripe client initialized (shared implementation)")
        return self._stripe_client

    def _get_flutterwave_client(self) -> FlutterwaveClient:
        """
        Get or create Flutterwave client (shared implementation).

        Returns:
            FlutterwaveClient instance from @shared/
        """
        if self._flutterwave_client is None:
            self._flutterwave_client = FlutterwaveClient(
                secret_key=os.getenv("FLUTTERWAVE_SECRET_KEY"),
                public_key=os.getenv("FLUTTERWAVE_PUBLIC_KEY"),
                encryption_key=os.getenv("FLUTTERWAVE_ENCRYPTION_KEY"),
                webhook_secret=os.getenv("FLUTTERWAVE_WEBHOOK_SECRET")
            )
            logger.info("Flutterwave client initialized (shared implementation)")
        return self._flutterwave_client

    def _calculate_fees(self, amount: float, gateway: PaymentGateway, payment_method: PaymentMethod) -> Dict[str, float]:
        """
        Calculate platform and gateway fees.

        Args:
            amount: Payment amount
            gateway: Payment gateway
            payment_method: Payment method

        Returns:
            Dict with gateway_fee, platform_fee, and net_amount
        """
        # Gateway fees (typical rates - adjust based on actual agreements)
        gateway_fee = 0.0

        if gateway == PaymentGateway.STRIPE:
            # Stripe: 2.9% + $0.30 for cards (typical)
            if payment_method == PaymentMethod.CARD:
                gateway_fee = (amount * 0.029) + 0.30
        elif gateway == PaymentGateway.FLUTTERWAVE:
            # Flutterwave Ghana rates (approximate)
            if payment_method == PaymentMethod.CARD:
                gateway_fee = amount * 0.028  # 2.8%
            elif payment_method == PaymentMethod.MOBILE_MONEY:
                gateway_fee = amount * 0.015  # 1.5%
            elif payment_method == PaymentMethod.BANK_TRANSFER:
                gateway_fee = amount * 0.01  # 1%

        # Platform fee (example: 1% of transaction)
        platform_fee = amount * 0.01

        # Net amount after fees
        net_amount = amount - gateway_fee - platform_fee

        return {
            "gateway_fee": round(gateway_fee, 2),
            "platform_fee": round(platform_fee, 2),
            "net_amount": round(net_amount, 2)
        }

    async def create_payment(
        self,
        organization_id: str,
        payment_data: PaymentCreate,
        user_id: str
    ) -> Payment:
        """
        Create a new payment record.

        Args:
            organization_id: Organization ID
            payment_data: Payment creation data
            user_id: User creating the payment

        Returns:
            Created payment

        Raises:
            ValueError: If customer info missing or gateway not configured
        """
        # Validate customer information
        if not payment_data.customer_id:
            if not all([payment_data.customer_name, payment_data.customer_email]):
                raise ValueError("Customer information required: name and email")

        # Get customer info from database if customer_id provided
        customer_name = payment_data.customer_name
        customer_email = payment_data.customer_email
        customer_phone = payment_data.customer_phone

        if payment_data.customer_id:
            contact = await self.db.contacts.find_one({"id": payment_data.customer_id})
            if contact:
                customer_name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
                customer_email = contact.get('email')
                customer_phone = contact.get('phone')

        # Calculate fees
        fees = self._calculate_fees(
            payment_data.amount,
            payment_data.gateway,
            payment_data.payment_method
        )

        # Build metadata
        metadata = PaymentMetadata(
            invoice_id=payment_data.invoice_id,
            property_id=payment_data.property_id,
            booking_id=payment_data.booking_id,
            custom_fields=payment_data.custom_metadata
        )

        # Create payment record
        payment = Payment(
            id=str(uuid4()),
            organization_id=organization_id,
            amount=payment_data.amount,
            currency=payment_data.currency,
            description=payment_data.description,
            purpose=payment_data.purpose,
            gateway=payment_data.gateway,
            payment_method=payment_data.payment_method,
            status=PaymentStatus.PENDING,
            customer_id=payment_data.customer_id or str(uuid4()),
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            metadata=metadata,
            platform_fee=fees["platform_fee"],
            gateway_fee=fees["gateway_fee"],
            net_amount=fees["net_amount"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Save to database
        await self.collection.insert_one(payment.dict())

        logger.info(f"Created payment {payment.id} for {payment.amount} {payment.currency}")

        return payment

    async def create_payment_intent(
        self,
        payment_id: str,
        organization_id: str
    ) -> PaymentIntent:
        """
        Create a payment intent for client-side payment initialization.

        Args:
            payment_id: Payment ID
            organization_id: Organization ID

        Returns:
            Payment intent with client_secret

        Raises:
            ValueError: If payment not found or invalid gateway
        """
        # Get payment
        payment = await self.get_payment(payment_id, organization_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")

        if payment.gateway == PaymentGateway.STRIPE:
            return await self._create_stripe_intent(payment)
        elif payment.gateway == PaymentGateway.FLUTTERWAVE:
            return await self._create_flutterwave_intent(payment)
        else:
            raise ValueError(f"Payment intents not supported for gateway: {payment.gateway}")

    async def _create_stripe_intent(self, payment: Payment) -> PaymentIntent:
        """
        Create Stripe PaymentIntent using shared client.

        Args:
            payment: Payment record

        Returns:
            Payment intent
        """
        stripe_client = self._get_stripe_client()

        try:
            # Create Stripe PaymentIntent using shared client
            intent = await stripe_client.create_payment_intent(
                amount=Decimal(str(payment.amount)),
                currency=payment.currency,
                metadata={
                    "payment_id": payment.id,
                    "organization_id": payment.organization_id,
                    "customer_id": payment.customer_id,
                    "invoice_id": payment.metadata.invoice_id or "",
                    "property_id": payment.metadata.property_id or "",
                    "description": payment.description
                }
            )

            # Update payment record with gateway ID
            await self.collection.update_one(
                {"id": payment.id},
                {
                    "$set": {
                        "gateway_payment_id": intent["id"],
                        "status": PaymentStatus.PROCESSING.value,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            return PaymentIntent(
                id=intent["id"],
                amount=payment.amount,
                currency=payment.currency,
                client_secret=intent["client_secret"],
                gateway=PaymentGateway.STRIPE,
                status=intent.status
            )

        except Exception as e:
            logger.error(f"Failed to create Stripe intent: {str(e)}")
            await self._mark_payment_failed(payment.id, str(e))
            raise ValueError(f"Failed to initialize Stripe payment: {str(e)}")

    async def _create_flutterwave_intent(self, payment: Payment) -> PaymentIntent:
        """
        Create Flutterwave payment link using shared client.

        Args:
            payment: Payment record

        Returns:
            Payment intent with payment link

        Note:
            Flutterwave uses redirect-based flow, not client-side integration
        """
        flutterwave_client = self._get_flutterwave_client()

        try:
            # Generate transaction reference
            tx_ref = f"EST-{payment.id}"

            # Create payment using shared client
            payment_data = await flutterwave_client.create_payment_intent(
                amount=Decimal(str(payment.amount)),
                currency=payment.currency,
                customer_email=payment.customer_email,
                customer_name=payment.customer_name,
                customer_phone=payment.customer_phone,
                redirect_url=payment.metadata.custom_fields.get("return_url", ""),
                metadata={
                    "payment_id": payment.id,
                    "organization_id": payment.organization_id,
                    "title": "EstateFlow Payment",
                    "description": payment.description
                },
                tx_ref=tx_ref
            )

            payment_link = payment_data["payment_link"]

            # Update payment record
            await self.collection.update_one(
                {"id": payment.id},
                {
                    "$set": {
                        "gateway_payment_id": payment_data["id"],
                        "status": PaymentStatus.PROCESSING.value,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            return PaymentIntent(
                id=payment_data["id"],
                amount=payment.amount,
                currency=payment.currency,
                client_secret=payment_link,  # Using client_secret field for payment link
                gateway=PaymentGateway.FLUTTERWAVE,
                status="requires_action"
            )

        except Exception as e:
            logger.error(f"Failed to create Flutterwave payment: {str(e)}")
            await self._mark_payment_failed(payment.id, str(e))
            raise ValueError(f"Failed to initialize Flutterwave payment: {str(e)}")

    async def confirm_payment(
        self,
        payment_id: str,
        organization_id: str,
        confirm_data: Optional[PaymentConfirm] = None
    ) -> Payment:
        """
        Confirm payment after gateway processing.

        Args:
            payment_id: Payment ID
            organization_id: Organization ID
            confirm_data: Optional confirmation data from gateway

        Returns:
            Updated payment

        Raises:
            ValueError: If payment not found
        """
        payment = await self.get_payment(payment_id, organization_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")

        if payment.gateway == PaymentGateway.STRIPE:
            return await self._confirm_stripe_payment(payment, confirm_data)
        elif payment.gateway == PaymentGateway.FLUTTERWAVE:
            return await self._confirm_flutterwave_payment(payment, confirm_data)
        else:
            # Manual payment - mark as completed
            return await self._mark_payment_completed(payment.id)

    async def _confirm_stripe_payment(
        self,
        payment: Payment,
        confirm_data: Optional[PaymentConfirm]
    ) -> Payment:
        """Confirm Stripe payment using shared client."""
        stripe_client = self._get_stripe_client()

        try:
            # Retrieve PaymentIntent from Stripe using shared client
            intent = await stripe_client.retrieve_payment(payment.gateway_payment_id)

            if intent["status"] == "succeeded":
                # Extract payment method details from charges
                card_details = None
                if intent.get("charges") and len(intent["charges"]) > 0:
                    charge = intent["charges"][0]
                    # Note: Shared client returns simplified charge data
                    # Card details would need to be fetched separately if needed
                    # For now, mark as completed without full card details

                # Update payment
                await self.collection.update_one(
                    {"id": payment.id},
                    {
                        "$set": {
                            "status": PaymentStatus.COMPLETED.value,
                            "card_details": card_details.dict() if card_details else None,
                            "gateway_charge_id": charge.get("id") if intent.get("charges") else None,
                            "processed_at": datetime.utcnow(),
                            "completed_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }
                    }
                )

                # Update related invoice if exists
                if payment.metadata.invoice_id:
                    await self._update_invoice_payment_status(payment.metadata.invoice_id, payment.id)

                logger.info(f"Payment {payment.id} completed successfully via Stripe")

            elif intent.status in ["canceled", "failed"]:
                await self._mark_payment_failed(payment.id, f"Stripe payment {intent.status}")

            return await self.get_payment(payment.id, payment.organization_id)

        except Exception as e:
            logger.error(f"Failed to confirm Stripe payment: {str(e)}")
            raise ValueError(f"Failed to confirm payment: {str(e)}")

    async def _confirm_flutterwave_payment(
        self,
        payment: Payment,
        confirm_data: Optional[PaymentConfirm]
    ) -> Payment:
        """Confirm Flutterwave payment using shared client."""
        flutterwave_client = self._get_flutterwave_client()

        try:
            # Verify transaction with Flutterwave using shared client
            tx_id = confirm_data.gateway_payment_id if confirm_data else payment.gateway_payment_id

            tx_data = await flutterwave_client.retrieve_payment(tx_id)

            if tx_data["status"] == "successful":
                # Extract payment method details
                payment_method_details = {}
                if tx_data.get("payment_type") == "card":
                    payment_method_details["card_details"] = {
                        "last4": tx_data.get("card", {}).get("last_4digits"),
                        "brand": tx_data.get("card", {}).get("type"),
                        "exp_month": tx_data.get("card", {}).get("expiry_month"),
                        "exp_year": tx_data.get("card", {}).get("expiry_year"),
                        "country": tx_data.get("card", {}).get("country")
                    }
                elif tx_data.get("payment_type") == "mobilemoney":
                    payment_method_details["mobile_money_details"] = {
                        "provider": "mtn_momo",  # Determine from tx_data
                        "phone_number": "***" + str(payment.customer_phone)[-3:] if payment.customer_phone else "",
                        "account_name": payment.customer_name
                    }

                # Update payment
                await self.collection.update_one(
                    {"id": payment.id},
                    {
                        "$set": {
                            "status": PaymentStatus.COMPLETED.value,
                            **payment_method_details,
                            "gateway_payment_id": str(tx_data.get("id")),
                            "processed_at": datetime.utcnow(),
                            "completed_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }
                    }
                )

                # Update related invoice if exists
                if payment.metadata.invoice_id:
                    await self._update_invoice_payment_status(payment.metadata.invoice_id, payment.id)

                logger.info(f"Payment {payment.id} completed successfully via Flutterwave")

            else:
                await self._mark_payment_failed(payment.id, "Payment verification failed")

            return await self.get_payment(payment.id, payment.organization_id)

        except Exception as e:
            logger.error(f"Failed to confirm Flutterwave payment: {str(e)}")
            raise ValueError(f"Failed to confirm payment: {str(e)}")

    async def _mark_payment_completed(self, payment_id: str) -> Payment:
        """Mark manual payment as completed."""
        await self.collection.update_one(
            {"id": payment_id},
            {
                "$set": {
                    "status": PaymentStatus.COMPLETED.value,
                    "processed_at": datetime.utcnow(),
                    "completed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        payment = await self.collection.find_one({"id": payment_id})
        return Payment(**payment)

    async def _mark_payment_failed(self, payment_id: str, error_message: str):
        """Mark payment as failed."""
        await self.collection.update_one(
            {"id": payment_id},
            {
                "$set": {
                    "status": PaymentStatus.FAILED.value,
                    "error_message": error_message,
                    "failed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )

    async def _update_invoice_payment_status(self, invoice_id: str, payment_id: str):
        """Update invoice status when payment completes."""
        from app.models.invoice import InvoiceStatus

        # Get payment to know amount
        payment = await self.collection.find_one({"id": payment_id})

        if payment:
            # Mark invoice as paid
            await self.db.invoices.update_one(
                {"id": invoice_id},
                {
                    "$set": {
                        "status": InvoiceStatus.PAID.value,
                        "paid_amount": payment["amount"],
                        "paid_date": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            logger.info(f"Marked invoice {invoice_id} as paid")

    async def get_payment(self, payment_id: str, organization_id: str) -> Optional[Payment]:
        """Get payment by ID."""
        payment_dict = await self.collection.find_one({
            "id": payment_id,
            "organization_id": organization_id,
            "is_deleted": False
        })

        if not payment_dict:
            return None

        return Payment(**payment_dict)

    async def list_payments(
        self,
        organization_id: str,
        filters: PaymentListFilters
    ) -> PaymentListResponse:
        """List payments with filters."""
        # Build query
        query: Dict[str, Any] = {
            "organization_id": organization_id,
            "is_deleted": False
        }

        # Status filter
        if filters.status:
            query["status"] = {"$in": [s.value for s in filters.status]}

        # Gateway filter
        if filters.gateway:
            query["gateway"] = {"$in": [g.value for g in filters.gateway]}

        # Payment method filter
        if filters.payment_method:
            query["payment_method"] = {"$in": [pm.value for pm in filters.payment_method]}

        # Purpose filter
        if filters.purpose:
            query["purpose"] = {"$in": [p.value for p in filters.purpose]}

        # Customer filter
        if filters.customer_id:
            query["customer_id"] = filters.customer_id

        # Property filter
        if filters.property_id:
            query["metadata.property_id"] = filters.property_id

        # Invoice filter
        if filters.invoice_id:
            query["metadata.invoice_id"] = filters.invoice_id

        # Date range
        if filters.from_date or filters.to_date:
            date_query = {}
            if filters.from_date:
                date_query["$gte"] = filters.from_date
            if filters.to_date:
                date_query["$lte"] = filters.to_date
            query["created_at"] = date_query

        # Amount range
        if filters.min_amount is not None or filters.max_amount is not None:
            amount_query = {}
            if filters.min_amount is not None:
                amount_query["$gte"] = filters.min_amount
            if filters.max_amount is not None:
                amount_query["$lte"] = filters.max_amount
            query["amount"] = amount_query

        # Search
        if filters.search:
            query["$or"] = [
                {"customer_name": {"$regex": filters.search, "$options": "i"}},
                {"description": {"$regex": filters.search, "$options": "i"}}
            ]

        # Get total count
        total = await self.collection.count_documents(query)

        # Build sort
        sort_order = 1 if filters.sort_order == "asc" else -1
        sort = [(filters.sort_by, sort_order)]

        # Query with pagination
        cursor = self.collection.find(query).sort(sort).skip(filters.offset).limit(filters.limit)
        payment_dicts = await cursor.to_list(length=filters.limit)

        payments = [Payment(**p) for p in payment_dicts]

        return PaymentListResponse(
            payments=payments,
            total=total,
            limit=filters.limit,
            offset=filters.offset,
            has_more=(filters.offset + len(payments)) < total
        )

    async def refund_payment(
        self,
        payment_id: str,
        organization_id: str,
        refund_data: PaymentRefund
    ) -> Payment:
        """
        Refund a payment (full or partial).

        Args:
            payment_id: Payment ID
            organization_id: Organization ID
            refund_data: Refund details

        Returns:
            Updated payment

        Raises:
            ValueError: If payment not found or not refundable
        """
        # Get payment
        payment = await self.get_payment(payment_id, organization_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")

        if payment.status != PaymentStatus.COMPLETED:
            raise ValueError("Only completed payments can be refunded")

        # Determine refund amount
        refund_amount = refund_data.amount or payment.amount

        if refund_amount > (payment.amount - payment.refunded_amount):
            raise ValueError("Refund amount exceeds remaining refundable amount")

        # Process refund based on gateway
        if payment.gateway == PaymentGateway.STRIPE:
            await self._process_stripe_refund(payment, refund_amount, refund_data.reason)
        elif payment.gateway == PaymentGateway.FLUTTERWAVE:
            await self._process_flutterwave_refund(payment, refund_amount, refund_data.reason)

        # Update payment record
        new_refunded_amount = payment.refunded_amount + refund_amount
        new_status = PaymentStatus.REFUNDED if new_refunded_amount == payment.amount else PaymentStatus.PARTIALLY_REFUNDED

        await self.collection.update_one(
            {"id": payment_id},
            {
                "$set": {
                    "status": new_status.value,
                    "refunded_amount": new_refunded_amount,
                    "refund_reason": refund_data.reason,
                    "refunded_at": datetime.utcnow(),
                    "notes": refund_data.notes or payment.notes,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        logger.info(f"Refunded {refund_amount} {payment.currency} for payment {payment_id}")

        return await self.get_payment(payment_id, organization_id)

    async def _process_stripe_refund(self, payment: Payment, amount: float, reason: str):
        """Process Stripe refund using shared client."""
        stripe_client = self._get_stripe_client()

        try:
            refund = await stripe_client.refund_payment(
                payment_intent_id=payment.gateway_payment_id,
                amount=Decimal(str(amount)),
                reason="requested_by_customer",
                metadata={"reason": reason}
            )

            logger.info(f"Stripe refund {refund['id']} created for payment {payment.id}")

        except Exception as e:
            logger.error(f"Failed to process Stripe refund: {str(e)}")
            raise ValueError(f"Failed to process refund: {str(e)}")

    async def _process_flutterwave_refund(self, payment: Payment, amount: float, reason: str):
        """Process Flutterwave refund using shared client."""
        flutterwave_client = self._get_flutterwave_client()

        try:
            refund = await flutterwave_client.refund_payment(
                transaction_id=payment.gateway_payment_id,
                amount=Decimal(str(amount)),
                reason=reason
            )

            logger.info(f"Flutterwave refund created for payment {payment.id}")

        except Exception as e:
            logger.error(f"Failed to process Flutterwave refund: {str(e)}")
            raise ValueError(f"Failed to process refund: {str(e)}")

    async def handle_webhook(self, webhook_data: WebhookEvent) -> Dict[str, Any]:
        """
        Handle payment gateway webhook.

        Args:
            webhook_data: Webhook event data

        Returns:
            Processing result
        """
        # Store webhook event
        await self.webhooks_collection.insert_one(webhook_data.dict())

        # Process based on gateway
        if webhook_data.gateway == PaymentGateway.STRIPE:
            return await self._handle_stripe_webhook(webhook_data)
        elif webhook_data.gateway == PaymentGateway.FLUTTERWAVE:
            return await self._handle_flutterwave_webhook(webhook_data)

        return {"status": "ignored"}

    async def _handle_stripe_webhook(self, webhook_data: WebhookEvent) -> Dict[str, Any]:
        """Handle Stripe webhook events."""
        event_type = webhook_data.event_type
        payload = webhook_data.payload

        if event_type == "payment_intent.succeeded":
            # Find payment by gateway_payment_id
            payment_dict = await self.collection.find_one({
                "gateway_payment_id": payload.get("id")
            })

            if payment_dict:
                payment = Payment(**payment_dict)
                await self._confirm_stripe_payment(payment, None)

        # Mark webhook as processed
        await self.webhooks_collection.update_one(
            {"id": webhook_data.id},
            {
                "$set": {
                    "processed": True,
                    "processed_at": datetime.utcnow()
                }
            }
        )

        return {"status": "processed"}

    async def _handle_flutterwave_webhook(self, webhook_data: WebhookEvent) -> Dict[str, Any]:
        """Handle Flutterwave webhook events."""
        event_type = webhook_data.event_type
        payload = webhook_data.payload

        if event_type == "charge.completed":
            # Find payment by transaction reference
            tx_ref = payload.get("txRef") or payload.get("tx_ref")

            if tx_ref and tx_ref.startswith("EST-"):
                payment_id = tx_ref.replace("EST-", "")
                payment_dict = await self.collection.find_one({"id": payment_id})

                if payment_dict:
                    payment = Payment(**payment_dict)
                    confirm_data = PaymentConfirm(gateway_payment_id=str(payload.get("id")))
                    await self._confirm_flutterwave_payment(payment, confirm_data)

        # Mark webhook as processed
        await self.webhooks_collection.update_one(
            {"id": webhook_data.id},
            {
                "$set": {
                    "processed": True,
                    "processed_at": datetime.utcnow()
                }
            }
        )

        return {"status": "processed"}

    async def get_stats(self, organization_id: str, currency: str = "GHS") -> PaymentStats:
        """Get payment statistics."""
        query = {
            "organization_id": organization_id,
            "is_deleted": False,
            "currency": currency
        }

        # Total payments
        total_payments = await self.collection.count_documents(query)

        # Status counts
        completed_count = await self.collection.count_documents({**query, "status": PaymentStatus.COMPLETED})
        pending_count = await self.collection.count_documents({**query, "status": PaymentStatus.PENDING})
        failed_count = await self.collection.count_documents({**query, "status": PaymentStatus.FAILED})
        refunded_count = await self.collection.count_documents({
            **query,
            "status": {"$in": [PaymentStatus.REFUNDED, PaymentStatus.PARTIALLY_REFUNDED]}
        })

        # Revenue aggregation
        revenue_pipeline = [
            {"$match": {**query, "status": PaymentStatus.COMPLETED}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        revenue_result = await self.collection.aggregate(revenue_pipeline).to_list(length=1)
        total_revenue = revenue_result[0]["total"] if revenue_result else 0.0

        # Pending amount
        pending_pipeline = [
            {"$match": {**query, "status": PaymentStatus.PENDING}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        pending_result = await self.collection.aggregate(pending_pipeline).to_list(length=1)
        pending_amount = pending_result[0]["total"] if pending_result else 0.0

        # Failed amount
        failed_pipeline = [
            {"$match": {**query, "status": PaymentStatus.FAILED}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        failed_result = await self.collection.aggregate(failed_pipeline).to_list(length=1)
        failed_amount = failed_result[0]["total"] if failed_result else 0.0

        # Refunded amount
        refunded_pipeline = [
            {"$match": query},
            {"$group": {"_id": None, "total": {"$sum": "$refunded_amount"}}}
        ]
        refunded_result = await self.collection.aggregate(refunded_pipeline).to_list(length=1)
        refunded_amount = refunded_result[0]["total"] if refunded_result else 0.0

        # Revenue by payment method
        method_pipeline = [
            {"$match": {**query, "status": PaymentStatus.COMPLETED}},
            {
                "$group": {
                    "_id": "$payment_method",
                    "total": {"$sum": "$amount"}
                }
            }
        ]
        method_results = await self.collection.aggregate(method_pipeline).to_list(length=10)

        method_revenues = {result["_id"]: result["total"] for result in method_results}

        return PaymentStats(
            total_payments=total_payments,
            total_revenue=round(total_revenue, 2),
            pending_amount=round(pending_amount, 2),
            failed_amount=round(failed_amount, 2),
            refunded_amount=round(refunded_amount, 2),
            completed_count=completed_count,
            pending_count=pending_count,
            failed_count=failed_count,
            refunded_count=refunded_count,
            card_revenue=round(method_revenues.get(PaymentMethod.CARD, 0.0), 2),
            mobile_money_revenue=round(method_revenues.get(PaymentMethod.MOBILE_MONEY, 0.0), 2),
            bank_transfer_revenue=round(method_revenues.get(PaymentMethod.BANK_TRANSFER, 0.0), 2),
            cash_revenue=round(method_revenues.get(PaymentMethod.CASH, 0.0), 2),
            currency=currency
        )
