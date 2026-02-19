"""
Automated Payout Scheduler Service for Affiliate System.

Handles automated payout processing for affiliates based on:
- Auto-payout settings in affiliate profile
- Payout schedule (weekly, monthly)
- Minimum balance thresholds
- Payment provider integration

Author: KasaAI Team
Date: 2025-11-18
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models.affiliate import (
    AffiliateProfile,
    PayoutRequest,
    PayoutMethod,
    PayoutStatus,
    AFFILIATE_PROFILES_COLLECTION,
    PAYOUT_REQUESTS_COLLECTION,
)

logger = logging.getLogger(__name__)


class PayoutScheduler:
    """
    Automated payout scheduler for affiliate system.

    Processes scheduled payouts based on affiliate preferences and balances.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize payout scheduler.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.profiles_collection = db[AFFILIATE_PROFILES_COLLECTION]
        self.payouts_collection = db[PAYOUT_REQUESTS_COLLECTION]

    async def process_scheduled_payouts(self) -> Dict[str, Any]:
        """
        Process all scheduled payouts.

        Finds affiliates eligible for auto-payout and creates payout requests.

        Returns:
            dict: Processing summary with counts and results
        """
        logger.info("🔄 Starting automated payout processing...")

        summary = {
            "total_eligible": 0,
            "payouts_created": 0,
            "payouts_failed": 0,
            "total_amount": Decimal("0.00"),
            "errors": [],
            "processed_at": datetime.utcnow()
        }

        try:
            # Find eligible affiliates
            eligible_affiliates = await self._find_eligible_affiliates()
            summary["total_eligible"] = len(eligible_affiliates)

            logger.info(f"📊 Found {len(eligible_affiliates)} eligible affiliates for auto-payout")

            # Process each affiliate
            for profile in eligible_affiliates:
                try:
                    payout = await self._create_payout_request(profile)

                    if payout:
                        summary["payouts_created"] += 1
                        summary["total_amount"] += payout.amount
                        logger.info(
                            f"✅ Created payout for {profile['user_id']}: "
                            f"${payout.amount} ({payout.payout_method})"
                        )
                except Exception as e:
                    summary["payouts_failed"] += 1
                    summary["errors"].append({
                        "user_id": profile["user_id"],
                        "error": str(e)
                    })
                    logger.error(
                        f"❌ Failed to create payout for {profile['user_id']}: {str(e)}"
                    )

            logger.info(
                f"✅ Automated payout processing complete: "
                f"{summary['payouts_created']} created, "
                f"{summary['payouts_failed']} failed, "
                f"${summary['total_amount']} total"
            )

        except Exception as e:
            logger.error(f"❌ Fatal error in payout processing: {str(e)}")
            summary["errors"].append({"fatal_error": str(e)})

        return summary

    async def _find_eligible_affiliates(self) -> List[Dict[str, Any]]:
        """
        Find affiliates eligible for automated payout.

        Eligibility criteria:
        - auto_payout_enabled = True
        - pending_commissions >= payout_threshold
        - is_active = True
        - is_verified = True
        - Matches payout schedule (weekly/monthly on correct day)

        Returns:
            list: List of eligible affiliate profiles
        """
        today = datetime.utcnow()
        day_of_month = today.day
        day_of_week = today.weekday()  # 0 = Monday, 6 = Sunday

        # Build query
        query = {
            "is_active": True,
            "is_verified": True,
            "auto_payout_enabled": True,
            "$expr": {
                "$gte": [
                    {"$toDecimal": "$pending_commissions"},
                    {"$toDecimal": "$payout_threshold"}
                ]
            }
        }

        # Get all potentially eligible affiliates
        cursor = self.profiles_collection.find(query)
        all_candidates = await cursor.to_list(None)

        # Filter by schedule
        eligible = []
        for profile in all_candidates:
            schedule = profile.get("auto_payout_schedule", "monthly")
            payout_day = profile.get("auto_payout_day", 15)

            if schedule == "weekly":
                # Check if today matches the payout day of week
                if payout_day == day_of_week:
                    eligible.append(profile)

            elif schedule == "monthly":
                # Check if today matches the payout day of month
                # Handle months with fewer days (e.g., Feb 28 instead of 30)
                if day_of_month == payout_day or (
                    payout_day > 28 and day_of_month == self._last_day_of_month(today)
                ):
                    eligible.append(profile)

        return eligible

    async def _create_payout_request(
        self,
        profile: Dict[str, Any]
    ) -> Optional[PayoutRequest]:
        """
        Create automated payout request for an affiliate.

        Args:
            profile: Affiliate profile dictionary

        Returns:
            PayoutRequest: Created payout request, or None if failed
        """
        # Calculate payout amount (all pending commissions)
        amount = Decimal(str(profile["pending_commissions"]))

        if amount < Decimal(str(profile["payout_threshold"])):
            logger.warning(
                f"Skipping payout for {profile['user_id']}: "
                f"amount ${amount} below threshold ${profile['payout_threshold']}"
            )
            return None

        # Calculate processing fee (if applicable)
        processing_fee = self._calculate_processing_fee(
            amount,
            profile.get("payout_method", PayoutMethod.WALLET_CREDIT)
        )
        net_amount = amount - processing_fee

        # Create payout request
        payout = PayoutRequest(
            affiliate_id=profile["user_id"],
            organization_id=profile["organization_id"],
            amount=amount,
            payout_method=profile.get("payout_method", PayoutMethod.WALLET_CREDIT),
            payment_method_id=profile.get("payment_method_id"),
            processing_fee=processing_fee,
            net_amount=net_amount,
            status=PayoutStatus.PENDING,
            notes=f"Automated payout ({profile.get('auto_payout_schedule', 'monthly')})"
        )

        # Insert into database
        payout_dict = payout.dict(by_alias=True)
        payout_dict["_id"] = payout_dict.pop("id")

        await self.payouts_collection.insert_one(payout_dict)

        # Update profile pending_commissions
        await self.profiles_collection.update_one(
            {"_id": profile["_id"]},
            {
                "$set": {
                    "pending_commissions": Decimal("0.00"),
                    "updated_at": datetime.utcnow()
                },
                "$inc": {
                    "total_commissions_paid": amount
                }
            }
        )

        return payout

    def _calculate_processing_fee(
        self,
        amount: Decimal,
        payout_method: PayoutMethod
    ) -> Decimal:
        """
        Calculate processing fee based on payout method.

        Args:
            amount: Payout amount
            payout_method: Payment method

        Returns:
            Decimal: Processing fee amount
        """
        # Fee structure
        fee_rates = {
            PayoutMethod.WALLET_CREDIT: Decimal("0.00"),  # Free
            PayoutMethod.MOBILE_MONEY: Decimal("0.02"),   # 2%
            PayoutMethod.BANK_TRANSFER: Decimal("0.015"),  # 1.5%
            PayoutMethod.PAYPAL: Decimal("0.025"),        # 2.5%
        }

        rate = fee_rates.get(payout_method, Decimal("0.00"))
        fee = amount * rate

        # Minimum fee (except for wallet credit)
        if payout_method != PayoutMethod.WALLET_CREDIT:
            min_fee = Decimal("1.00")
            fee = max(fee, min_fee)

        return fee.quantize(Decimal("0.01"))

    @staticmethod
    def _last_day_of_month(date: datetime) -> int:
        """
        Get the last day of the month for a given date.

        Args:
            date: Date to check

        Returns:
            int: Last day of the month (28-31)
        """
        # Get first day of next month, then subtract one day
        if date.month == 12:
            next_month = datetime(date.year + 1, 1, 1)
        else:
            next_month = datetime(date.year, date.month + 1, 1)

        last_day = (next_month - timedelta(days=1)).day
        return last_day

    async def process_pending_payouts(self) -> Dict[str, Any]:
        """
        Process pending payout requests (integrate with payment providers).

        This method would integrate with actual payment provider APIs:
        - PayPal Mass Payments
        - Stripe Payouts
        - Mobile Money APIs (M-Pesa, MTN, Airtel)
        - Bank transfer APIs

        Returns:
            dict: Processing summary
        """
        logger.info("🔄 Processing pending payout requests...")

        summary = {
            "total_pending": 0,
            "processed": 0,
            "failed": 0,
            "errors": []
        }

        # Get pending payouts
        cursor = self.payouts_collection.find({"status": PayoutStatus.PENDING})
        pending_payouts = await cursor.to_list(None)

        summary["total_pending"] = len(pending_payouts)

        for payout in pending_payouts:
            try:
                # Update status to processing
                await self.payouts_collection.update_one(
                    {"_id": payout["_id"]},
                    {
                        "$set": {
                            "status": PayoutStatus.PROCESSING,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )

                # Process based on payout method
                # NOTE: This is where you would integrate with payment providers
                # For now, we'll just mark wallet credits as completed

                if payout["payout_method"] == PayoutMethod.WALLET_CREDIT:
                    # TODO: Integrate with wallet service to credit balance
                    await self._complete_payout(payout["_id"], None)
                    summary["processed"] += 1
                else:
                    # TODO: Integrate with external payment providers
                    # For now, leave as PROCESSING for manual review
                    logger.info(
                        f"⏳ Payout {payout['_id']} requires external processing "
                        f"({payout['payout_method']})"
                    )

            except Exception as e:
                summary["failed"] += 1
                summary["errors"].append({
                    "payout_id": str(payout["_id"]),
                    "error": str(e)
                })

                # Mark as failed
                await self.payouts_collection.update_one(
                    {"_id": payout["_id"]},
                    {
                        "$set": {
                            "status": PayoutStatus.FAILED,
                            "failure_reason": str(e),
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                logger.error(f"❌ Failed to process payout {payout['_id']}: {str(e)}")

        logger.info(
            f"✅ Payout processing complete: "
            f"{summary['processed']} processed, {summary['failed']} failed"
        )

        return summary

    async def _complete_payout(
        self,
        payout_id: str,
        provider_reference: Optional[str]
    ) -> None:
        """
        Mark a payout as completed.

        Args:
            payout_id: Payout request ID
            provider_reference: External provider transaction reference
        """
        await self.payouts_collection.update_one(
            {"_id": payout_id},
            {
                "$set": {
                    "status": PayoutStatus.COMPLETED,
                    "processed_at": datetime.utcnow(),
                    "provider_reference": provider_reference,
                    "updated_at": datetime.utcnow()
                }
            }
        )
