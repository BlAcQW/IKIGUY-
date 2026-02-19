"""
Giving Service for ChurchFlow

Handles donation processing, recurring giving, pledges, and donor management.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import stripe

# Add parent directory for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from app.models.giving import (
    Donation,
    RecurringDonation,
    Pledge,
    GivingCampaign,
    DonorProfile,
    DonationStatus,
    PaymentMethod
)
from app.core.config import settings

# Initialize Stripe
stripe.api_key = settings.stripe_secret_key if hasattr(settings, 'stripe_secret_key') else os.getenv('STRIPE_SECRET_KEY')


class GivingService:
    """
    Comprehensive giving service for ChurchFlow.

    Handles:
    - One-time donations
    - Recurring donations
    - Pledges and commitments
    - Giving campaigns
    - Donor profiles and analytics
    - Tax receipts
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize giving service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.donations_collection = db.donations
        self.recurring_donations_collection = db.recurring_donations
        self.pledges_collection = db.pledges
        self.campaigns_collection = db.giving_campaigns
        self.donor_profiles_collection = db.donor_profiles

    # ==================== Donations ====================

    async def create_donation(
        self,
        organization_id: str,
        donor_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Donation:
        """
        Create a new donation.

        Args:
            organization_id: Organization receiving donation
            donor_data: Donation details
            user_id: User ID if authenticated donor

        Returns:
            Created Donation
        """
        donation_dict = {
            **donor_data,
            "organization_id": organization_id,
            "donor_id": user_id,
            "status": DonationStatus.PENDING,
            "created_at": datetime.utcnow()
        }

        result = await self.donations_collection.insert_one(donation_dict)
        donation_dict["_id"] = str(result.inserted_id)

        # Update or create donor profile if user_id exists
        if user_id:
            await self._update_donor_profile(organization_id, user_id, 0.0)  # Will update after payment

        return Donation(**donation_dict)

    async def process_donation_payment(
        self,
        donation_id: str,
        stripe_payment_method_id: str
    ) -> Donation:
        """
        Process payment for a donation using Stripe.

        Args:
            donation_id: Donation ID
            stripe_payment_method_id: Stripe payment method ID

        Returns:
            Updated Donation

        Raises:
            ValueError: If donation not found or payment fails
        """
        # Get donation
        donation_doc = await self.donations_collection.find_one({"_id": ObjectId(donation_id)})
        if not donation_doc:
            raise ValueError(f"Donation {donation_id} not found")

        donation = Donation(**{**donation_doc, "_id": str(donation_doc["_id"])})

        if donation.status != DonationStatus.PENDING:
            raise ValueError(f"Donation {donation_id} is not in pending status")

        try:
            # Update status to processing
            await self.donations_collection.update_one(
                {"_id": ObjectId(donation_id)},
                {"$set": {"status": DonationStatus.PROCESSING}}
            )

            # Create Stripe payment intent
            amount_cents = int(donation.amount * 100)  # Convert to cents

            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=donation.currency.lower(),
                payment_method=stripe_payment_method_id,
                confirm=True,
                description=f"Donation - {donation.category}",
                metadata={
                    "donation_id": donation_id,
                    "organization_id": donation.organization_id,
                    "donor_name": donation.donor_name
                }
            )

            # Update donation with payment intent
            update_data = {
                "stripe_payment_intent_id": payment_intent.id,
                "status": DonationStatus.COMPLETED,
                "completed_at": datetime.utcnow()
            }

            await self.donations_collection.update_one(
                {"_id": ObjectId(donation_id)},
                {"$set": update_data}
            )

            # Update donor profile
            if donation.donor_id:
                await self._update_donor_profile(
                    donation.organization_id,
                    donation.donor_id,
                    donation.amount
                )

            # Get updated donation
            updated_doc = await self.donations_collection.find_one({"_id": ObjectId(donation_id)})
            return Donation(**{**updated_doc, "_id": str(updated_doc["_id"])})

        except stripe.error.CardError as e:
            # Card was declined
            await self.donations_collection.update_one(
                {"_id": ObjectId(donation_id)},
                {
                    "$set": {
                        "status": DonationStatus.FAILED,
                        "failed_reason": str(e)
                    }
                }
            )
            raise ValueError(f"Payment failed: {str(e)}")

        except Exception as e:
            # Other error
            await self.donations_collection.update_one(
                {"_id": ObjectId(donation_id)},
                {
                    "$set": {
                        "status": DonationStatus.FAILED,
                        "failed_reason": str(e)
                    }
                }
            )
            raise ValueError(f"Payment processing error: {str(e)}")

    async def get_donation(self, donation_id: str) -> Optional[Donation]:
        """Get donation by ID"""
        doc = await self.donations_collection.find_one({"_id": ObjectId(donation_id)})
        if doc:
            return Donation(**{**doc, "_id": str(doc["_id"])})
        return None

    async def list_donations(
        self,
        organization_id: str,
        donor_id: Optional[str] = None,
        status: Optional[DonationStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        List donations with filters.

        Returns:
            Dict with donations, total, page info
        """
        query = {"organization_id": organization_id}

        if donor_id:
            query["donor_id"] = donor_id
        if status:
            query["status"] = status
        if start_date or end_date:
            query["created_at"] = {}
            if start_date:
                query["created_at"]["$gte"] = start_date
            if end_date:
                query["created_at"]["$lte"] = end_date

        # Get total count
        total = await self.donations_collection.count_documents(query)

        # Get paginated results
        skip = (page - 1) * page_size
        cursor = self.donations_collection.find(query).sort("created_at", -1).skip(skip).limit(page_size)
        docs = await cursor.to_list(length=page_size)

        donations = [Donation(**{**doc, "_id": str(doc["_id"])}) for doc in docs]

        return {
            "donations": donations,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": skip + len(donations) < total
        }

    # ==================== Recurring Donations ====================

    async def create_recurring_donation(
        self,
        organization_id: str,
        donor_id: str,
        recurring_data: Dict[str, Any]
    ) -> RecurringDonation:
        """
        Create recurring donation with Stripe subscription.

        Args:
            organization_id: Organization ID
            donor_id: Donor user ID
            recurring_data: Recurring donation details including stripe_payment_method_id

        Returns:
            Created RecurringDonation
        """
        # Get user info for donor name
        # Try supabase_id first (for JWT tokens), fallback to MongoDB _id
        user = await self.db.users.find_one({"supabase_id": donor_id})
        if not user:
            try:
                user = await self.db.users.find_one({"_id": ObjectId(donor_id)})
            except:
                pass
        if not user:
            raise ValueError(f"User {donor_id} not found")

        donor_name = user.get("name") or user.get("email")
        donor_email = user.get("email")

        # Create or get Stripe customer
        stripe_customer = await self._get_or_create_stripe_customer(donor_id, donor_email, donor_name)

        # Attach payment method to customer
        stripe_payment_method_id = recurring_data.pop("stripe_payment_method_id")
        stripe.PaymentMethod.attach(
            stripe_payment_method_id,
            customer=stripe_customer.id
        )

        # Set as default payment method
        stripe.Customer.modify(
            stripe_customer.id,
            invoice_settings={"default_payment_method": stripe_payment_method_id}
        )

        # Calculate interval for Stripe
        frequency = recurring_data["frequency"]
        interval_map = {
            "weekly": "week",
            "biweekly": "week",
            "monthly": "month",
            "quarterly": "month",
            "yearly": "year"
        }
        interval = interval_map.get(frequency, "month")
        interval_count = 2 if frequency == "biweekly" else (3 if frequency == "quarterly" else 1)

        # Create Stripe subscription
        amount_cents = int(recurring_data["amount"] * 100)

        # Create price
        price = stripe.Price.create(
            unit_amount=amount_cents,
            currency=recurring_data.get("currency", "USD").lower(),
            recurring={"interval": interval, "interval_count": interval_count},
            product_data={
                "name": f"Recurring Donation - {recurring_data.get('category', 'General Fund')}"
            }
        )

        # Create subscription
        subscription = stripe.Subscription.create(
            customer=stripe_customer.id,
            items=[{"price": price.id}],
            metadata={
                "organization_id": organization_id,
                "donor_id": donor_id,
                "donation_type": recurring_data["donation_type"],
                "category": recurring_data.get("category", "General Fund")
            }
        )

        # Calculate next payment date
        next_payment = datetime.fromtimestamp(subscription.current_period_end)

        # Create recurring donation record
        recurring_dict = {
            **recurring_data,
            "organization_id": organization_id,
            "donor_id": donor_id,
            "donor_name": donor_name,
            "donor_email": donor_email,
            "stripe_subscription_id": subscription.id,
            "stripe_customer_id": stripe_customer.id,
            "status": "active",
            "is_active": True,
            "next_payment_date": next_payment,
            "total_donations": 0,
            "total_amount": 0.0,
            "created_at": datetime.utcnow()
        }

        result = await self.recurring_donations_collection.insert_one(recurring_dict)
        recurring_dict["_id"] = str(result.inserted_id)

        return RecurringDonation(**recurring_dict)

    async def cancel_recurring_donation(
        self,
        recurring_donation_id: str,
        donor_id: str
    ) -> RecurringDonation:
        """Cancel recurring donation"""
        doc = await self.recurring_donations_collection.find_one({
            "_id": ObjectId(recurring_donation_id),
            "donor_id": donor_id
        })

        if not doc:
            raise ValueError(f"Recurring donation {recurring_donation_id} not found")

        recurring = RecurringDonation(**{**doc, "_id": str(doc["_id"])})

        # Cancel Stripe subscription
        if recurring.stripe_subscription_id:
            stripe.Subscription.delete(recurring.stripe_subscription_id)

        # Update status
        await self.recurring_donations_collection.update_one(
            {"_id": ObjectId(recurring_donation_id)},
            {
                "$set": {
                    "status": "cancelled",
                    "is_active": False,
                    "cancelled_at": datetime.utcnow()
                }
            }
        )

        updated_doc = await self.recurring_donations_collection.find_one({"_id": ObjectId(recurring_donation_id)})
        return RecurringDonation(**{**updated_doc, "_id": str(updated_doc["_id"])})

    # ==================== Helper Methods ====================

    async def _get_or_create_stripe_customer(
        self,
        user_id: str,
        email: Optional[str],
        name: str
    ) -> Any:
        """Get existing Stripe customer or create new one"""
        # Check if customer exists in donor profile
        donor = await self.donor_profiles_collection.find_one({"user_id": user_id})

        if donor and donor.get("metadata", {}).get("stripe_customer_id"):
            customer_id = donor["metadata"]["stripe_customer_id"]
            return stripe.Customer.retrieve(customer_id)

        # Create new customer
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata={"user_id": user_id}
        )

        return customer

    async def _update_donor_profile(
        self,
        organization_id: str,
        user_id: str,
        donation_amount: float
    ):
        """Update donor profile after donation"""
        now = datetime.utcnow()

        # Get user info
        # Try supabase_id first (for JWT tokens), fallback to MongoDB _id
        user = await self.db.users.find_one({"supabase_id": user_id})
        if not user:
            try:
                user = await self.db.users.find_one({"_id": ObjectId(user_id)})
            except:
                pass
        if not user:
            return

        donor_name = user.get("name") or user.get("email")
        donor_email = user.get("email")
        donor_phone = user.get("phone")

        # Update or create profile
        await self.donor_profiles_collection.update_one(
            {
                "organization_id": organization_id,
                "user_id": user_id
            },
            {
                "$set": {
                    "donor_name": donor_name,
                    "donor_email": donor_email,
                    "donor_phone": donor_phone,
                    "updated_at": now
                },
                "$inc": {
                    "total_donated": donation_amount,
                    "donation_count": 1 if donation_amount > 0 else 0
                },
                "$max": {"largest_donation": donation_amount},
                "$setOnInsert": {
                    "organization_id": organization_id,
                    "user_id": user_id,
                    "currency": "USD",
                    "first_donation_date": now,
                    "created_at": now
                }
            },
            upsert=True
        )

        # Update average
        profile = await self.donor_profiles_collection.find_one({
            "organization_id": organization_id,
            "user_id": user_id
        })

        if profile and profile["donation_count"] > 0:
            avg = profile["total_donated"] / profile["donation_count"]
            await self.donor_profiles_collection.update_one(
                {"_id": profile["_id"]},
                {"$set": {"average_donation": avg, "last_donation_date": now}}
            )

    async def get_donor_profile(
        self,
        organization_id: str,
        user_id: str
    ) -> Optional[DonorProfile]:
        """Get donor profile"""
        doc = await self.donor_profiles_collection.find_one({
            "organization_id": organization_id,
            "user_id": user_id
        })

        if doc:
            return DonorProfile(**{**doc, "_id": str(doc["_id"])})
        return None

    async def get_giving_analytics(
        self,
        organization_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get giving analytics for organization.

        Returns:
            Analytics data with totals, averages, trends
        """
        query = {
            "organization_id": organization_id,
            "status": DonationStatus.COMPLETED,
            "completed_at": {"$gte": start_date, "$lte": end_date}
        }

        donations = await self.donations_collection.find(query).to_list(length=None)

        total_amount = sum(d["amount"] for d in donations)
        total_donations = len(donations)
        average_donation = total_amount / total_donations if total_donations > 0 else 0

        # Unique donors
        unique_donors = len(set(d.get("donor_id") for d in donations if d.get("donor_id")))

        # Donation types breakdown
        donation_types = {}
        for d in donations:
            dtype = d.get("donation_type", "one_time")
            donation_types[dtype] = donation_types.get(dtype, 0) + d["amount"]

        return {
            "organization_id": organization_id,
            "period_start": start_date,
            "period_end": end_date,
            "total_donations": total_donations,
            "total_amount": total_amount,
            "currency": donations[0]["currency"] if donations else "USD",
            "average_donation": average_donation,
            "unique_donors": unique_donors,
            "donation_types": donation_types,
        }


# Singleton instance
_giving_service: Optional[GivingService] = None


def get_giving_service(db: AsyncIOMotorDatabase) -> GivingService:
    """Get or create giving service singleton"""
    global _giving_service
    if _giving_service is None:
        _giving_service = GivingService(db)
    return _giving_service
