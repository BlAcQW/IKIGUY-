"""
Affiliate Service for Multi-Level Marketing (MLM) Program.

Handles all affiliate program business logic including:
- Enrollment and referral code generation
- Referral tracking and attribution
- Multi-tier commission calculation (3 levels: 15%, 8%, 3%)
- Payout processing
- Network management

Author: KasaAI Team
Date: 2025-11-18
"""

import logging
import random
import string
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from fastapi import HTTPException, Request

from ..models.affiliate import (
    AffiliateProfile,
    ReferralLink,
    ReferralAttribution,
    CommissionRecord,
    PayoutRequest,
    ReferralClick,
    ReferralCampaign,
    PayoutMethod,
    PayoutStatus,
    CommissionStatus,
    CampaignStatus,
    AttributionMethod,
    AFFILIATE_PROFILES_COLLECTION,
    REFERRAL_LINKS_COLLECTION,
    REFERRAL_ATTRIBUTIONS_COLLECTION,
    COMMISSION_RECORDS_COLLECTION,
    PAYOUT_REQUESTS_COLLECTION,
    REFERRAL_CLICKS_COLLECTION,
    REFERRAL_CAMPAIGNS_COLLECTION,
)

logger = logging.getLogger(__name__)


class AffiliateService:
    """
    Affiliate program service.

    Manages all affiliate program operations with MongoDB for persistence.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize affiliate service.

        Args:
            db: MongoDB database connection
        """
        self.db = db
        self.profiles_collection = db[AFFILIATE_PROFILES_COLLECTION]
        self.links_collection = db[REFERRAL_LINKS_COLLECTION]
        self.attributions_collection = db[REFERRAL_ATTRIBUTIONS_COLLECTION]
        self.commissions_collection = db[COMMISSION_RECORDS_COLLECTION]
        self.payouts_collection = db[PAYOUT_REQUESTS_COLLECTION]
        self.clicks_collection = db[REFERRAL_CLICKS_COLLECTION]
        self.users_collection = db.users
        self.transactions_collection = db.transactions

    # ========================================================================
    # Affiliate Profile Management
    # ========================================================================

    async def join_program(
        self,
        user_id: str,
        organization_id: str,
        upline_referral_code: Optional[str] = None
    ) -> AffiliateProfile:
        """
        Enroll user in affiliate program.

        Args:
            user_id: User ID enrolling
            organization_id: User's organization ID
            upline_referral_code: Optional upline affiliate code

        Returns:
            Created affiliate profile

        Raises:
            HTTPException: If already enrolled or upline not found
        """
        # Check if already enrolled
        existing = await self.profiles_collection.find_one({"user_id": user_id})
        if existing:
            raise HTTPException(
                status_code=400,
                detail="User is already enrolled in the affiliate program"
            )

        # Validate and get upline if provided
        upline_id = None
        tier_level = 1

        if upline_referral_code:
            upline = await self.profiles_collection.find_one(
                {"referral_code": upline_referral_code.upper()}
            )
            if not upline:
                raise HTTPException(
                    status_code=404,
                    detail=f"Upline referral code '{upline_referral_code}' not found"
                )

            upline_id = upline["user_id"]
            upline_tier = upline.get("tier_level", 1)

            # Calculate tier level (max 3)
            tier_level = min(upline_tier + 1, 3)

        # Generate unique referral code
        referral_code = await self._generate_unique_referral_code(user_id)

        # Create affiliate profile
        profile = AffiliateProfile(
            user_id=user_id,
            organization_id=organization_id,
            referral_code=referral_code,
            upline_id=upline_id,
            tier_level=tier_level,
        )

        # Insert into database
        profile_dict = profile.dict(by_alias=True)
        profile_dict["_id"] = profile_dict.pop("id")

        # Convert Decimal to float for MongoDB
        for key, value in profile_dict.items():
            if isinstance(value, Decimal):
                profile_dict[key] = float(value)

        await self.profiles_collection.insert_one(profile_dict)

        # Update user document to mark as affiliate
        try:
            await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"is_affiliate": True}}
            )
        except Exception:
            # user_id is not a valid ObjectId (e.g., in tests), skip user update
            pass

        # Create default referral link
        await self._create_referral_link(user_id, organization_id, referral_code)

        # Update upline's direct referral count
        if upline_id:
            await self._update_affiliate_stats(upline_id, increment_referrals=True)

        logger.info(f"User {user_id} joined affiliate program with code {referral_code}")

        return profile

    async def _generate_unique_referral_code(self, user_id: str) -> str:
        """
        Generate unique referral code for user.

        Format: First 4 chars of user_id + 3 random digits
        Example: USER001, ABCD123

        Args:
            user_id: User ID

        Returns:
            Unique referral code

        Raises:
            HTTPException: If unable to generate unique code after retries
        """
        # Get user details for personalization
        user = None
        try:
            user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
        except Exception:
            # user_id is not a valid ObjectId (e.g., in tests), skip user lookup
            pass

        max_attempts = 10
        for attempt in range(max_attempts):
            if user and user.get("first_name"):
                # Use first name + random number
                base = user["first_name"][:4].upper()
            else:
                # Use random letters
                base = ''.join(random.choices(string.ascii_uppercase, k=4))

            # Add random digits
            suffix = ''.join(random.choices(string.digits, k=3))
            code = f"{base}{suffix}"

            # Check uniqueness
            existing = await self.profiles_collection.find_one({"referral_code": code})
            if not existing:
                return code

        # Fallback: fully random code
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        existing = await self.profiles_collection.find_one({"referral_code": code})
        if existing:
            raise HTTPException(
                status_code=500,
                detail="Unable to generate unique referral code. Please try again."
            )

        return code

    async def get_profile(self, user_id: str) -> Optional[AffiliateProfile]:
        """
        Get affiliate profile for user.

        Args:
            user_id: User ID

        Returns:
            Affiliate profile or None if not enrolled
        """
        profile_dict = await self.profiles_collection.find_one({"user_id": user_id})

        if not profile_dict:
            return None

        # Convert MongoDB document to Pydantic model
        profile_dict["id"] = str(profile_dict.pop("_id"))

        # Convert floats back to Decimal
        for key in ["tier1_commission_rate", "tier2_commission_rate", "tier3_commission_rate",
                    "total_sales", "total_commissions_earned", "total_commissions_paid",
                    "pending_commissions", "payout_threshold"]:
            if key in profile_dict and profile_dict[key] is not None:
                profile_dict[key] = Decimal(str(profile_dict[key]))

        return AffiliateProfile(**profile_dict)

    async def update_profile(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> AffiliateProfile:
        """
        Update affiliate profile settings.

        Args:
            user_id: User ID
            updates: Fields to update

        Returns:
            Updated profile

        Raises:
            HTTPException: If not enrolled
        """
        profile = await self.get_profile(user_id)
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="User is not enrolled in the affiliate program"
            )

        # Convert Decimal to float for MongoDB
        mongo_updates = {}
        for key, value in updates.items():
            if isinstance(value, Decimal):
                mongo_updates[key] = float(value)
            elif isinstance(value, PayoutMethod):
                mongo_updates[key] = value.value
            else:
                mongo_updates[key] = value

        mongo_updates["updated_at"] = datetime.utcnow()

        # Update in database
        await self.profiles_collection.update_one(
            {"user_id": user_id},
            {"$set": mongo_updates}
        )

        # Return updated profile
        return await self.get_profile(user_id)

    async def get_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Calculate affiliate statistics for dashboard.

        Args:
            user_id: User ID

        Returns:
            Dictionary with statistics

        Raises:
            HTTPException: If not enrolled
        """
        profile = await self.get_profile(user_id)
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="User is not enrolled in the affiliate program"
            )

        # Get this month's earnings
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)

        this_month_commissions = await self.commissions_collection.aggregate([
            {
                "$match": {
                    "affiliate_id": user_id,
                    "created_at": {"$gte": month_start}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$commission_amount"}
                }
            }
        ]).to_list(1)

        last_month_commissions = await self.commissions_collection.aggregate([
            {
                "$match": {
                    "affiliate_id": user_id,
                    "created_at": {
                        "$gte": last_month_start,
                        "$lt": month_start
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$commission_amount"}
                }
            }
        ]).to_list(1)

        this_month_earnings = Decimal(str(this_month_commissions[0]["total"])) if this_month_commissions else Decimal("0")
        last_month_earnings = Decimal(str(last_month_commissions[0]["total"])) if last_month_commissions else Decimal("0")

        # Get network size by tier
        tier_counts = await self._get_network_tier_counts(user_id)

        # Get last commission date
        last_commission = await self.commissions_collection.find_one(
            {"affiliate_id": user_id},
            sort=[("created_at", -1)]
        )

        # Calculate conversion rate (simplified)
        total_clicks = await self.links_collection.aggregate([
            {"$match": {"affiliate_id": user_id}},
            {"$group": {"_id": None, "total": {"$sum": "$click_count"}}}
        ]).to_list(1)

        total_click_count = total_clicks[0]["total"] if total_clicks else 0
        conversion_rate = (profile.total_referrals / total_click_count * 100) if total_click_count > 0 else 0.0

        # Average commission per referral
        avg_commission = (
            profile.total_commissions_earned / profile.total_referrals
            if profile.total_referrals > 0 else Decimal("0")
        )

        return {
            "total_earned": profile.total_commissions_earned,
            "total_paid": profile.total_commissions_paid,
            "pending_commissions": profile.pending_commissions,
            "this_month_earnings": this_month_earnings,
            "last_month_earnings": last_month_earnings,
            "total_referrals": profile.total_referrals,
            "direct_referrals": profile.direct_referrals,
            "tier2_referrals": tier_counts.get(2, 0),
            "tier3_referrals": tier_counts.get(3, 0),
            "total_sales": profile.total_sales,
            "conversion_rate": round(conversion_rate, 2),
            "average_commission_per_referral": avg_commission,
            "last_referral_at": profile.last_referral_at,
            "last_commission_at": last_commission["created_at"] if last_commission else None,
        }

    # ========================================================================
    # Referral Link Management
    # ========================================================================

    async def _create_referral_link(
        self,
        affiliate_id: str,
        organization_id: str,
        referral_code: str,
        utm_source: Optional[str] = None,
        utm_campaign: Optional[str] = None,
        utm_medium: Optional[str] = None
    ) -> ReferralLink:
        """
        Create referral link.

        Args:
            affiliate_id: Affiliate user ID
            organization_id: Organization ID
            referral_code: Referral code
            utm_source: UTM source parameter
            utm_campaign: UTM campaign parameter
            utm_medium: UTM medium parameter

        Returns:
            Created referral link
        """
        link = ReferralLink(
            affiliate_id=affiliate_id,
            organization_id=organization_id,
            referral_code=referral_code,
            utm_source=utm_source,
            utm_campaign=utm_campaign,
            utm_medium=utm_medium,
        )

        link_dict = link.dict(by_alias=True)
        link_dict["_id"] = link_dict.pop("id")

        await self.links_collection.insert_one(link_dict)

        return link

    async def create_referral_link(
        self,
        user_id: str,
        utm_source: Optional[str] = None,
        utm_campaign: Optional[str] = None,
        utm_medium: Optional[str] = None
    ) -> ReferralLink:
        """
        Create custom referral link with UTM parameters.

        Args:
            user_id: Affiliate user ID
            utm_source: UTM source
            utm_campaign: UTM campaign
            utm_medium: UTM medium

        Returns:
            Created referral link

        Raises:
            HTTPException: If not enrolled
        """
        profile = await self.get_profile(user_id)
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="User is not enrolled in the affiliate program"
            )

        return await self._create_referral_link(
            affiliate_id=user_id,
            organization_id=profile.organization_id,
            referral_code=profile.referral_code,
            utm_source=utm_source,
            utm_campaign=utm_campaign,
            utm_medium=utm_medium
        )

    async def get_referral_links(self, user_id: str) -> List[ReferralLink]:
        """
        Get all referral links for affiliate.

        Args:
            user_id: Affiliate user ID

        Returns:
            List of referral links
        """
        cursor = self.links_collection.find({"affiliate_id": user_id})
        links = []

        async for link_dict in cursor:
            link_dict["id"] = str(link_dict.pop("_id"))
            links.append(ReferralLink(**link_dict))

        return links

    # ========================================================================
    # Referral Tracking & Attribution
    # ========================================================================

    async def track_click(
        self,
        referral_code: str,
        request: Request
    ) -> Dict[str, Any]:
        """
        Track referral link click.

        Args:
            referral_code: Referral code
            request: HTTP request for metadata

        Returns:
            Tracking result
        """
        # Verify referral code exists
        profile = await self.profiles_collection.find_one(
            {"referral_code": referral_code.upper()}
        )

        if not profile:
            logger.warning(f"Invalid referral code: {referral_code}")
            return {"success": False, "error": "Invalid referral code"}

        # Increment click count
        await self.links_collection.update_one(
            {"referral_code": referral_code.upper()},
            {
                "$inc": {"click_count": 1},
                "$set": {"last_clicked_at": datetime.utcnow()}
            }
        )

        logger.info(f"Tracked click for referral code: {referral_code}")

        return {
            "success": True,
            "referral_code": referral_code.upper(),
            "message": "Referral click tracked successfully"
        }

    async def attribute_signup(
        self,
        user_id: str,
        organization_id: str,
        referral_code: Optional[str] = None,
        request: Optional[Request] = None
    ) -> Optional[ReferralAttribution]:
        """
        Attribute new user signup to affiliate.

        Args:
            user_id: New user ID
            organization_id: User's organization ID
            referral_code: Referral code (from cookie or URL)
            request: HTTP request for metadata

        Returns:
            Attribution record or None if no attribution
        """
        if not referral_code:
            return None

        # Get affiliate profile
        affiliate = await self.profiles_collection.find_one(
            {"referral_code": referral_code.upper()}
        )

        if not affiliate:
            logger.warning(f"Invalid referral code during signup: {referral_code}")
            return None

        # Check if user is trying to refer themselves
        if affiliate["user_id"] == user_id:
            logger.warning(f"User {user_id} attempted self-referral")
            raise HTTPException(
                status_code=403,
                detail="You cannot refer yourself"
            )

        # Check if already attributed
        existing = await self.attributions_collection.find_one(
            {"referred_user_id": user_id}
        )

        if existing:
            logger.warning(f"User {user_id} already attributed to affiliate")
            return None

        # Create attribution record
        attribution = ReferralAttribution(
            referred_user_id=user_id,
            affiliate_id=affiliate["user_id"],
            organization_id=organization_id,
            referral_code=referral_code.upper(),
            attribution_method=AttributionMethod.URL_PARAM,
            clicked_at=datetime.utcnow(),
            signed_up_at=datetime.utcnow(),
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
        )

        attr_dict = attribution.dict(by_alias=True)
        attr_dict["_id"] = attr_dict.pop("id")

        await self.attributions_collection.insert_one(attr_dict)

        # Update affiliate stats
        await self._update_affiliate_stats(
            affiliate["user_id"],
            increment_referrals=True,
            last_referral_at=datetime.utcnow()
        )

        # Update referral link conversion count
        await self.links_collection.update_one(
            {"referral_code": referral_code.upper()},
            {"$inc": {"conversion_count": 1}}
        )

        logger.info(f"Attributed user {user_id} to affiliate {affiliate['user_id']}")

        return attribution

    # ========================================================================
    async def _get_attribution_for_user(
        self,
        user_id: str,
        organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get attribution record for a user.

        This is a helper method used by the commission processor to check
        if a user was referred by an affiliate.

        Args:
            user_id: User ID
            organization_id: Organization ID

        Returns:
            Attribution record dict or None
        """
        attribution = await self.attributions_collection.find_one({
            "referred_user_id": user_id,
            "organization_id": organization_id
        })

        return attribution

    # Commission Calculation
    # ========================================================================

    async def calculate_commission(self, transaction_id: str) -> List[CommissionRecord]:
        """
        Calculate multi-tier commissions for a purchase.

        Calculates commissions for up to 3 tiers:
        - Tier 1 (direct): 15%
        - Tier 2 (sub-affiliate): 8%
        - Tier 3 (sub-sub-affiliate): 3%

        Args:
            transaction_id: Purchase transaction ID

        Returns:
            List of commission records created

        Raises:
            HTTPException: If transaction not found
        """
        # Get transaction details
        transaction = await self.transactions_collection.find_one(
            {"_id": ObjectId(transaction_id)}
        )

        if not transaction:
            raise HTTPException(
                status_code=404,
                detail=f"Transaction {transaction_id} not found"
            )

        # Only process completed deposits
        if transaction.get("transaction_type") != "deposit" or transaction.get("status") != "completed":
            logger.info(f"Skipping commission for transaction {transaction_id} - not a completed deposit")
            return []

        buyer_user_id = transaction["user_id"]
        sale_amount = Decimal(str(transaction["amount"]))

        # Check if buyer was referred
        attribution = await self.attributions_collection.find_one(
            {"referred_user_id": buyer_user_id}
        )

        if not attribution:
            logger.info(f"No attribution found for user {buyer_user_id}")
            return []

        # Update attribution with first purchase date
        if not attribution.get("first_purchase_at"):
            await self.attributions_collection.update_one(
                {"_id": attribution["_id"]},
                {"$set": {"first_purchase_at": datetime.utcnow()}}
            )

        # Get affiliate chain (up to 3 tiers)
        affiliate_chain = await self._get_affiliate_chain(
            attribution["affiliate_id"],
            max_tiers=3
        )

        commissions = []

        for tier_level, affiliate_id in enumerate(affiliate_chain, start=1):
            # Get affiliate profile for commission rate
            affiliate = await self.profiles_collection.find_one({"user_id": affiliate_id})

            if not affiliate:
                logger.warning(f"Affiliate {affiliate_id} not found, skipping tier {tier_level}")
                continue

            # Get commission rate for this tier
            rate_key = f"tier{tier_level}_commission_rate"
            commission_rate = Decimal(str(affiliate.get(rate_key, 0)))

            if commission_rate == 0:
                logger.info(f"Zero commission rate for affiliate {affiliate_id} tier {tier_level}")
                continue

            commission_amount = sale_amount * commission_rate

            # Create commission record
            commission = CommissionRecord(
                affiliate_id=affiliate_id,
                organization_id=affiliate["organization_id"],
                referred_user_id=buyer_user_id,
                transaction_id=transaction_id,
                sale_amount=sale_amount,
                commission_rate=commission_rate,
                commission_amount=commission_amount,
                tier_level=tier_level,
                status=CommissionStatus.APPROVED,  # Auto-approve for now
                approved_at=datetime.utcnow(),
            )

            comm_dict = commission.dict(by_alias=True)
            comm_dict["_id"] = comm_dict.pop("id")

            # Convert Decimals to float for MongoDB
            for key in ["sale_amount", "commission_rate", "commission_amount"]:
                if key in comm_dict:
                    comm_dict[key] = float(comm_dict[key])

            result = await self.commissions_collection.insert_one(comm_dict)
            commission.id = str(result.inserted_id)

            # Update affiliate stats
            await self._update_affiliate_stats(
                affiliate_id,
                commission_amount=commission_amount,
                sale_amount=sale_amount
            )

            commissions.append(commission)

            logger.info(
                f"Created commission: {commission_amount} for affiliate {affiliate_id} "
                f"(tier {tier_level}) from transaction {transaction_id}"
            )

        return commissions

    async def _get_affiliate_chain(
        self,
        affiliate_id: str,
        max_tiers: int = 3
    ) -> List[str]:
        """
        Get affiliate upline chain.

        Args:
            affiliate_id: Starting affiliate user ID
            max_tiers: Maximum tiers to traverse

        Returns:
            List of affiliate IDs from current to top (tier 1, 2, 3)
        """
        chain = [affiliate_id]

        current_id = affiliate_id
        for _ in range(max_tiers - 1):
            affiliate = await self.profiles_collection.find_one({"user_id": current_id})

            if not affiliate or not affiliate.get("upline_id"):
                break

            upline_id = affiliate["upline_id"]
            chain.append(upline_id)
            current_id = upline_id

        return chain

    # ========================================================================
    # Referrals & Network
    # ========================================================================

    async def get_referrals(
        self,
        user_id: str,
        tier: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get list of referrals for affiliate.

        Args:
            user_id: Affiliate user ID
            tier: Filter by tier level (1, 2, or 3)
            limit: Max results
            offset: Offset for pagination

        Returns:
            Tuple of (referrals list, total count)
        """
        # Get all affiliates in network
        if tier == 1:
            # Direct referrals only
            query = {"upline_id": user_id}
        else:
            # Get full network then filter by tier
            network = await self._build_network_tree(user_id)
            network_ids = [
                aff["user_id"]
                for aff in network
                if tier is None or aff.get("tier_from_root") == tier
            ]
            query = {"user_id": {"$in": network_ids}}

        # Count total
        total = await self.profiles_collection.count_documents(query)

        # Get referrals with pagination
        cursor = self.profiles_collection.find(query).skip(offset).limit(limit)

        referrals = []
        async for aff in cursor:
            # Get user details
            user = None
            try:
                user = await self.users_collection.find_one({"_id": ObjectId(aff["user_id"])})
            except Exception:
                # user_id is not a valid ObjectId (e.g., in tests), skip user lookup
                pass

            # Get total purchases (from attributions + transactions)
            attribution = await self.attributions_collection.find_one(
                {"referred_user_id": aff["user_id"]}
            )

            total_purchases = Decimal("0")
            if attribution:
                # Sum all completed deposit transactions
                pipeline = [
                    {
                        "$match": {
                            "user_id": aff["user_id"],
                            "transaction_type": "deposit",
                            "status": "completed"
                        }
                    },
                    {
                        "$group": {
                            "_id": None,
                            "total": {"$sum": "$amount"}
                        }
                    }
                ]

                result = await self.transactions_collection.aggregate(pipeline).to_list(1)
                if result:
                    total_purchases = Decimal(str(result[0]["total"]))

            # Get commissions earned from this user
            pipeline = [
                {
                    "$match": {
                        "affiliate_id": user_id,
                        "referred_user_id": aff["user_id"]
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": "$commission_amount"}
                    }
                }
            ]

            comm_result = await self.commissions_collection.aggregate(pipeline).to_list(1)
            commissions_earned = Decimal(str(comm_result[0]["total"])) if comm_result else Decimal("0")

            # Determine tier level relative to current user
            # If this is a direct referral (upline_id == user_id), they're tier 1
            # Otherwise use tier_from_root if available (set by _build_network_tree)
            tier_level_relative = aff.get("tier_from_root", 1 if aff.get("upline_id") == user_id else aff["tier_level"])

            referrals.append({
                "user_id": aff["user_id"],
                "referred_user_id": aff["user_id"],  # Add alias for compatibility
                "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() if user else None,
                "email": user.get("email") if user else None,
                "joined_at": aff["joined_program_at"],
                "tier_level": tier_level_relative,
                "total_purchases": total_purchases,
                "commissions_earned_from_user": commissions_earned,
                "first_purchase_at": attribution.get("first_purchase_at") if attribution else None,
                "is_active": aff.get("is_active", True),
            })

        return referrals, total

    async def _build_network_tree(
        self,
        affiliate_id: str,
        current_tier: int = 0,
        max_tiers: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Build network tree recursively.

        Args:
            affiliate_id: Root affiliate ID
            current_tier: Current tier level
            max_tiers: Maximum tiers to traverse

        Returns:
            List of all affiliates in network with tier info
        """
        if current_tier >= max_tiers:
            return []

        # Get direct referrals
        cursor = self.profiles_collection.find({"upline_id": affiliate_id})

        network = []
        async for aff in cursor:
            aff["tier_from_root"] = current_tier + 1
            network.append(aff)

            # Recursively get sub-network
            sub_network = await self._build_network_tree(
                aff["user_id"],
                current_tier + 1,
                max_tiers
            )
            network.extend(sub_network)

        return network

    async def _get_network_tier_counts(self, user_id: str) -> Dict[int, int]:
        """
        Get count of affiliates by tier in network.

        Args:
            user_id: Root affiliate user ID

        Returns:
            Dictionary mapping tier level to count
        """
        network = await self._build_network_tree(user_id)

        counts = {1: 0, 2: 0, 3: 0}
        for aff in network:
            tier = aff.get("tier_from_root", 1)
            if tier in counts:
                counts[tier] += 1

        return counts

    async def get_network_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get network statistics.

        Args:
            user_id: Affiliate user ID

        Returns:
            Network statistics
        """
        network = await self._build_network_tree(user_id)

        tier_counts = {1: 0, 2: 0, 3: 0}
        for aff in network:
            tier = aff.get("tier_from_root", 1)
            if tier in tier_counts:
                tier_counts[tier] += 1

        # Get total network sales and commissions
        network_ids = [aff["user_id"] for aff in network]

        total_sales = Decimal("0")
        total_commissions = Decimal("0")

        if network_ids:
            # Get total sales from network
            sales_pipeline = [
                {
                    "$match": {
                        "referred_user_id": {"$in": network_ids}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": "$sale_amount"}
                    }
                }
            ]

            sales_result = await self.commissions_collection.aggregate(sales_pipeline).to_list(1)
            if sales_result:
                total_sales = Decimal(str(sales_result[0]["total"]))

            # Get total commissions from network
            comm_pipeline = [
                {
                    "$match": {
                        "affiliate_id": user_id
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": "$commission_amount"}
                    }
                }
            ]

            comm_result = await self.commissions_collection.aggregate(comm_pipeline).to_list(1)
            if comm_result:
                total_commissions = Decimal(str(comm_result[0]["total"]))

        return {
            "tier1_count": tier_counts[1],
            "tier2_count": tier_counts[2],
            "tier3_count": tier_counts[3],
            "total_network_size": len(network),
            "total_network_sales": total_sales,
            "total_sales": total_sales,  # Alias for compatibility
            "total_network_commissions": total_commissions,
            "total_commissions": total_commissions,  # Alias for compatibility
        }

    # ========================================================================
    # Commissions
    # ========================================================================

    async def get_commissions(
        self,
        user_id: str,
        status: Optional[CommissionStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get commission records for affiliate.

        Args:
            user_id: Affiliate user ID
            status: Filter by status
            limit: Max results
            offset: Offset for pagination

        Returns:
            Tuple of (commissions list, total count)
        """
        query = {"affiliate_id": user_id}
        if status:
            query["status"] = status.value

        total = await self.commissions_collection.count_documents(query)

        cursor = self.commissions_collection.find(query).sort("created_at", -1).skip(offset).limit(limit)

        commissions = []
        async for comm in cursor:
            # Get referred user details
            user = None
            try:
                user = await self.users_collection.find_one({"_id": ObjectId(comm["referred_user_id"])})
            except Exception:
                # user_id is not a valid ObjectId (e.g., in tests), skip user lookup
                pass

            commissions.append({
                "id": str(comm["_id"]),
                "referred_user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() if user else None,
                "referred_user_email": user.get("email") if user else None,
                "sale_amount": Decimal(str(comm["sale_amount"])),
                "commission_rate": Decimal(str(comm["commission_rate"])),
                "commission_amount": Decimal(str(comm["commission_amount"])),
                "tier_level": comm["tier_level"],
                "status": comm["status"],
                "created_at": comm["created_at"],
                "approved_at": comm.get("approved_at"),
                "paid_at": comm.get("paid_at"),
            })

        return commissions, total

    async def get_commission_by_id(
        self,
        user_id: str,
        commission_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single commission record by ID.

        Args:
            user_id: Affiliate user ID (for authorization)
            commission_id: Commission record ID (UUID string)

        Returns:
            Commission record dict or None if not found

        Raises:
            HTTPException: If commission doesn't belong to user
        """
        # Commission IDs are UUID strings, not ObjectIds
        comm = await self.commissions_collection.find_one({"_id": commission_id})

        if not comm:
            return None

        # Verify commission belongs to the requesting user
        if comm["affiliate_id"] != user_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to view this commission"
            )

        # Get referred user details
        user = None
        try:
            user = await self.users_collection.find_one({"_id": ObjectId(comm["referred_user_id"])})
        except Exception:
            pass

        return {
            "id": str(comm["_id"]),
            "referred_user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() if user else None,
            "referred_user_email": user.get("email") if user else None,
            "sale_amount": Decimal(str(comm["sale_amount"])),
            "commission_rate": Decimal(str(comm["commission_rate"])),
            "commission_amount": Decimal(str(comm["commission_amount"])),
            "tier_level": comm["tier_level"],
            "status": comm["status"],
            "created_at": comm["created_at"],
            "approved_at": comm.get("approved_at"),
            "paid_at": comm.get("paid_at"),
        }

    # ========================================================================
    # Payouts
    # ========================================================================

    async def request_payout(
        self,
        user_id: str,
        amount: Decimal,
        payout_method: PayoutMethod,
        payment_method_id: Optional[str] = None
    ) -> PayoutRequest:
        """
        Create payout request.

        Args:
            user_id: Affiliate user ID
            amount: Payout amount
            payout_method: Payout method
            payment_method_id: Payment method ID (for non-wallet payouts)

        Returns:
            Created payout request

        Raises:
            HTTPException: If insufficient balance or invalid request
        """
        profile = await self.get_profile(user_id)
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="User is not enrolled in the affiliate program"
            )

        # Check minimum threshold
        if amount < profile.payout_threshold:
            raise HTTPException(
                status_code=400,
                detail=f"Minimum payout amount is ${profile.payout_threshold}"
            )

        # Check available balance
        if amount > profile.pending_commissions:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient balance. Available: ${profile.pending_commissions}"
            )

        # Calculate processing fee
        processing_fee = self._calculate_processing_fee(amount, payout_method)
        net_amount = amount - processing_fee

        # Create payout request
        payout = PayoutRequest(
            affiliate_id=user_id,
            organization_id=profile.organization_id,
            amount=amount,
            payout_method=payout_method,
            payment_method_id=payment_method_id,
            processing_fee=processing_fee,
            net_amount=net_amount,
            status=PayoutStatus.PENDING,
        )

        payout_dict = payout.dict(by_alias=True)
        payout_dict["_id"] = payout_dict.pop("id")

        # Convert Decimals to float
        for key in ["amount", "processing_fee", "net_amount"]:
            if key in payout_dict:
                payout_dict[key] = float(payout_dict[key])

        result = await self.payouts_collection.insert_one(payout_dict)
        payout.id = str(result.inserted_id)

        logger.info(f"Payout request created: {payout.id} for affiliate {user_id}")

        return payout

    def _calculate_processing_fee(self, amount: Decimal, method: PayoutMethod) -> Decimal:
        """
        Calculate processing fee for payout.

        Args:
            amount: Payout amount
            method: Payout method

        Returns:
            Processing fee
        """
        if method == PayoutMethod.WALLET_CREDIT:
            return Decimal("0.00")  # Free
        elif method == PayoutMethod.MOBILE_MONEY:
            return max(amount * Decimal("0.025"), Decimal("0.25"))  # 2.5% or $0.25 min
        elif method == PayoutMethod.BANK_TRANSFER:
            return Decimal("5.00")  # $5 fixed
        elif method == PayoutMethod.PAYPAL:
            return amount * Decimal("0.029") + Decimal("0.30")  # 2.9% + $0.30
        else:
            return Decimal("0.00")

    async def _update_affiliate_stats(
        self,
        user_id: str,
        increment_referrals: bool = False,
        commission_amount: Optional[Decimal] = None,
        sale_amount: Optional[Decimal] = None,
        last_referral_at: Optional[datetime] = None
    ):
        """
        Update affiliate profile statistics.

        Args:
            user_id: Affiliate user ID
            increment_referrals: Whether to increment referral count
            commission_amount: Commission amount to add
            sale_amount: Sale amount to add
            last_referral_at: Update last referral timestamp
        """
        updates = {"updated_at": datetime.utcnow()}
        increments = {}

        if increment_referrals:
            increments["total_referrals"] = 1
            increments["direct_referrals"] = 1

        if commission_amount:
            increments["total_commissions_earned"] = float(commission_amount)
            increments["pending_commissions"] = float(commission_amount)

        if sale_amount:
            increments["total_sales"] = float(sale_amount)

        if last_referral_at:
            updates["last_referral_at"] = last_referral_at

        update_query = {}
        if updates:
            update_query["$set"] = updates
        if increments:
            update_query["$inc"] = increments

        if update_query:
            await self.profiles_collection.update_one(
                {"user_id": user_id},
                update_query
            )

    # ========================================================================
    # Leaderboard & Rankings
    # ========================================================================

    async def get_leaderboard(
        self,
        organization_id: str,
        period: str = "all_time",  # all_time, month, week
        metric: str = "earnings",  # earnings, referrals, sales
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get affiliate leaderboard rankings.

        Args:
            organization_id: Organization ID
            period: Time period (all_time, month, week)
            metric: Ranking metric (earnings, referrals, sales)
            limit: Number of top affiliates to return

        Returns:
            List of affiliate rankings with stats
        """
        # Determine sort field based on metric
        sort_field_map = {
            "earnings": "total_commissions_earned",
            "referrals": "total_referrals",
            "sales": "total_sales"
        }
        sort_field = sort_field_map.get(metric, "total_commissions_earned")

        # For time-based filtering, we'd need to aggregate commissions
        # For now, implement all_time leaderboard from profile stats
        if period != "all_time":
            # TODO: Implement time-based filtering with commission aggregation
            logger.warning(f"Period '{period}' not yet implemented, using all_time")

        # Get top affiliates
        cursor = self.profiles_collection.find(
            {"organization_id": organization_id, "is_active": True}
        ).sort(sort_field, -1).limit(limit)

        affiliates = await cursor.to_list(limit)

        # Build leaderboard with rankings
        leaderboard = []
        for rank, aff in enumerate(affiliates, 1):
            # Get user details if available
            user = None
            try:
                user = await self.users_collection.find_one(
                    {"_id": ObjectId(aff["user_id"])}
                )
            except Exception:
                pass

            leaderboard.append({
                "rank": rank,
                "user_id": aff["user_id"],
                "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() if user else None,
                "email": user.get("email") if user else None,
                "referral_code": aff["referral_code"],
                "tier_level": aff["tier_level"],
                "total_earnings": Decimal(str(aff.get("total_commissions_earned", 0))),
                "total_referrals": aff.get("total_referrals", 0),
                "total_sales": Decimal(str(aff.get("total_sales", 0))),
                "direct_referrals": aff.get("direct_referrals", 0),
                "joined_at": aff.get("joined_program_at"),
            })

        return leaderboard

    async def get_affiliate_rank(
        self,
        user_id: str,
        metric: str = "earnings"
    ) -> Dict[str, Any]:
        """
        Get specific affiliate's ranking.

        Args:
            user_id: Affiliate user ID
            metric: Ranking metric

        Returns:
            Rank information
        """
        profile = await self.get_profile(user_id)
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Affiliate not found"
            )

        # Get leaderboard
        leaderboard = await self.get_leaderboard(
            profile.organization_id,
            metric=metric,
            limit=1000  # Get more to find user's position
        )

        # Find user's rank
        user_rank = None
        for entry in leaderboard:
            if entry["user_id"] == user_id:
                user_rank = entry
                break

        if not user_rank:
            # User not in top 1000
            total_affiliates = await self.profiles_collection.count_documents({
                "organization_id": profile.organization_id,
                "is_active": True
            })
            user_rank = {
                "rank": total_affiliates,  # Estimate
                "user_id": user_id,
                "total_earnings": profile.total_commissions_earned,
                "total_referrals": profile.total_referrals,
                "total_sales": profile.total_sales,
            }

        return user_rank

    # ========================================================================
    # Analytics & Conversion Tracking
    # ========================================================================

    async def track_click(
        self,
        referral_code: str,
        request: Request,
        utm_params: Optional[Dict[str, str]] = None
    ) -> ReferralClick:
        """
        Track a referral link click.

        Args:
            referral_code: Referral code that was clicked
            request: FastAPI request object for metadata
            utm_params: UTM parameters from the link

        Returns:
            Created click record
        """
        # Find affiliate by referral code
        profile = await self.profiles_collection.find_one({"referral_code": referral_code})
        if not profile:
            raise HTTPException(status_code=404, detail="Referral code not found")

        # Extract request metadata
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        referrer = request.headers.get("referer")

        # Create click record
        click = ReferralClick(
            referral_code=referral_code,
            affiliate_id=profile["user_id"],
            organization_id=profile["organization_id"],
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            utm_source=utm_params.get("utm_source") if utm_params else None,
            utm_campaign=utm_params.get("utm_campaign") if utm_params else None,
            utm_medium=utm_params.get("utm_medium") if utm_params else None,
            utm_content=utm_params.get("utm_content") if utm_params else None,
            utm_term=utm_params.get("utm_term") if utm_params else None,
        )

        # Store in database
        click_dict = click.dict(by_alias=True)
        click_dict["_id"] = click_dict.pop("id")

        await self.clicks_collection.insert_one(click_dict)

        logger.info(f"Tracked click for referral code {referral_code}")
        return click

    async def mark_click_converted(
        self,
        referral_code: str,
        user_id: str
    ):
        """
        Mark recent clicks as converted when user signs up.

        Args:
            referral_code: Referral code used
            user_id: New user who signed up
        """
        # Find recent unconverted clicks (last 30 days)
        cutoff = datetime.utcnow() - timedelta(days=30)

        await self.clicks_collection.update_many(
            {
                "referral_code": referral_code,
                "converted": False,
                "clicked_at": {"$gte": cutoff}
            },
            {
                "$set": {
                    "converted": True,
                    "converted_user_id": user_id,
                    "converted_at": datetime.utcnow()
                }
            }
        )

    async def get_conversion_analytics(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get conversion analytics for an affiliate.

        Args:
            user_id: Affiliate user ID
            days: Number of days to analyze

        Returns:
            Analytics data with conversion rates and traffic sources
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Get total clicks
        total_clicks = await self.clicks_collection.count_documents({
            "affiliate_id": user_id,
            "clicked_at": {"$gte": cutoff}
        })

        # Get converted clicks
        converted_clicks = await self.clicks_collection.count_documents({
            "affiliate_id": user_id,
            "clicked_at": {"$gte": cutoff},
            "converted": True
        })

        # Calculate conversion rate
        conversion_rate = (converted_clicks / total_clicks * 100) if total_clicks > 0 else 0

        # Traffic sources breakdown
        traffic_sources = await self.clicks_collection.aggregate([
            {
                "$match": {
                    "affiliate_id": user_id,
                    "clicked_at": {"$gte": cutoff}
                }
            },
            {
                "$group": {
                    "_id": "$utm_source",
                    "clicks": {"$sum": 1},
                    "conversions": {
                        "$sum": {"$cond": ["$converted", 1, 0]}
                    }
                }
            },
            {
                "$project": {
                    "source": {"$ifNull": ["$_id", "direct"]},
                    "clicks": 1,
                    "conversions": 1,
                    "conversion_rate": {
                        "$multiply": [
                            {"$divide": ["$conversions", "$clicks"]},
                            100
                        ]
                    }
                }
            },
            {"$sort": {"clicks": -1}}
        ]).to_list(100)

        # Campaign performance
        campaigns = await self.clicks_collection.aggregate([
            {
                "$match": {
                    "affiliate_id": user_id,
                    "clicked_at": {"$gte": cutoff},
                    "utm_campaign": {"$ne": None}
                }
            },
            {
                "$group": {
                    "_id": "$utm_campaign",
                    "clicks": {"$sum": 1},
                    "conversions": {
                        "$sum": {"$cond": ["$converted", 1, 0]}
                    }
                }
            },
            {
                "$project": {
                    "campaign": "$_id",
                    "clicks": 1,
                    "conversions": 1,
                    "conversion_rate": {
                        "$multiply": [
                            {"$divide": ["$conversions", "$clicks"]},
                            100
                        ]
                    }
                }
            },
            {"$sort": {"clicks": -1}}
        ]).to_list(50)

        return {
            "period_days": days,
            "total_clicks": total_clicks,
            "total_conversions": converted_clicks,
            "converted_clicks": converted_clicks,  # Keep for backwards compatibility
            "conversion_rate": round(conversion_rate, 2),
            "traffic_sources": traffic_sources,
            "campaigns": campaigns
        }

    async def get_link_performance(
        self,
        user_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get performance metrics for each referral link.

        Args:
            user_id: Affiliate user ID
            days: Number of days to analyze

        Returns:
            List of link performance data
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Get all links for user
        links = await self.links_collection.find({"user_id": user_id}).to_list(100)

        performance = []
        for link in links:
            # Get clicks for this link
            clicks = await self.clicks_collection.count_documents({
                "referral_code": link["referral_code"],
                "clicked_at": {"$gte": cutoff}
            })

            conversions = await self.clicks_collection.count_documents({
                "referral_code": link["referral_code"],
                "clicked_at": {"$gte": cutoff},
                "converted": True
            })

            conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0

            performance.append({
                "link_id": link["_id"],
                "referral_code": link["referral_code"],
                "url": link["url"],
                "utm_source": link.get("utm_source"),
                "utm_campaign": link.get("utm_campaign"),
                "clicks": clicks,
                "conversions": conversions,
                "conversion_rate": round(conversion_rate, 2)
            })

        # Sort by clicks
        performance.sort(key=lambda x: x["clicks"], reverse=True)

        return performance


    # ========================================================================
    # Analytics & Conversion Tracking
    # ========================================================================

    async def track_click(
        self,
        referral_code: str,
        request: Request,
        utm_params: Optional[Dict[str, str]] = None
    ) -> ReferralClick:
        """
        Track a referral link click.

        Args:
            referral_code: Referral code that was clicked
            request: FastAPI request object for metadata
            utm_params: UTM parameters from the link

        Returns:
            Created click record
        """
        # Find affiliate by referral code
        profile = await self.profiles_collection.find_one({"referral_code": referral_code})
        if not profile:
            raise HTTPException(status_code=404, detail="Referral code not found")

        # Extract request metadata
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        referrer = request.headers.get("referer")

        # Create click record
        click = ReferralClick(
            referral_code=referral_code,
            affiliate_id=profile["user_id"],
            organization_id=profile["organization_id"],
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            utm_source=utm_params.get("utm_source") if utm_params else None,
            utm_campaign=utm_params.get("utm_campaign") if utm_params else None,
            utm_medium=utm_params.get("utm_medium") if utm_params else None,
            utm_content=utm_params.get("utm_content") if utm_params else None,
            utm_term=utm_params.get("utm_term") if utm_params else None,
        )

        # Store in database
        click_dict = click.dict(by_alias=True)
        click_dict["_id"] = click_dict.pop("id")

        await self.clicks_collection.insert_one(click_dict)

        logger.info(f"Tracked click for referral code {referral_code}")
        return click

    async def mark_click_converted(
        self,
        referral_code: str,
        user_id: str,
        session_id: Optional[str] = None
    ):
        """
        Mark a click as converted when user signs up.

        Args:
            referral_code: Referral code used
            user_id: New user who signed up
            session_id: Session ID to match click
        """
        # Find recent unconverted clicks (within 30 days)
        cutoff = datetime.utcnow() - timedelta(days=30)

        # Try to match by session_id first if provided
        query = {
            "referral_code": referral_code,
            "converted": False,
            "clicked_at": {"$gte": cutoff}
        }

        if session_id:
            query["session_id"] = session_id

        # Find and update the click
        result = await self.clicks_collection.update_many(
            query,
            {
                "$set": {
                    "converted": True,
                    "converted_user_id": user_id,
                    "converted_at": datetime.utcnow()
                }
            }
        )

        logger.info(f"Marked {result.modified_count} clicks as converted for user {user_id}")


    # ========================================================================
    # Campaign Management
    # ========================================================================

    async def create_campaign(
        self,
        affiliate_id: str,
        organization_id: str,
        name: str,
        description: Optional[str],
        campaign_code: str,
        start_date: datetime,
        end_date: datetime,
        bonus_rate: Decimal,
        target_referrals: Optional[int] = None,
        target_sales: Optional[Decimal] = None,
        prize: Optional[str] = None,
        landing_page_url: Optional[str] = None,
        utm_campaign: Optional[str] = None
    ) -> ReferralCampaign:
        """
        Create a new referral campaign.

        Args:
            affiliate_id: Affiliate running the campaign
            organization_id: Organization ID
            name: Campaign name
            description: Campaign description
            campaign_code: Unique campaign code
            start_date: Campaign start date
            end_date: Campaign end date
            bonus_rate: Bonus commission rate
            target_referrals: Target number of referrals
            target_sales: Target sales amount
            prize: Prize for reaching targets
            landing_page_url: Custom landing page URL
            utm_campaign: UTM campaign parameter

        Returns:
            Created campaign
        """
        # Check for duplicate campaign code
        existing = await self.db[REFERRAL_CAMPAIGNS_COLLECTION].find_one({
            "campaign_code": campaign_code.upper(),
            "organization_id": organization_id
        })

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Campaign code {campaign_code} already exists"
            )

        # Create campaign
        campaign = ReferralCampaign(
            affiliate_id=affiliate_id,
            organization_id=organization_id,
            name=name,
            description=description,
            campaign_code=campaign_code,
            start_date=start_date,
            end_date=end_date,
            bonus_rate=bonus_rate,
            target_referrals=target_referrals,
            target_sales=target_sales,
            prize=prize,
            landing_page_url=landing_page_url,
            utm_campaign=utm_campaign
        )

        # Store in database
        campaign_dict = campaign.dict(by_alias=True)
        campaign_dict["_id"] = campaign_dict.pop("id")

        await self.db[REFERRAL_CAMPAIGNS_COLLECTION].insert_one(campaign_dict)

        logger.info(f"Created campaign {campaign.name} ({campaign.campaign_code}) for affiliate {affiliate_id}")
        return campaign

    async def get_campaigns(
        self,
        affiliate_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all campaigns for an affiliate.

        Args:
            affiliate_id: Affiliate user ID
            status: Filter by status (optional)

        Returns:
            List of campaigns
        """
        from ..models.affiliate import REFERRAL_CAMPAIGNS_COLLECTION

        query = {"affiliate_id": affiliate_id}
        if status:
            query["status"] = status

        cursor = self.db[REFERRAL_CAMPAIGNS_COLLECTION].find(query).sort("created_at", -1)
        campaigns = await cursor.to_list(100)

        # Convert _id to id for response
        for campaign in campaigns:
            campaign["id"] = campaign.pop("_id")

        return campaigns

    async def get_campaign(
        self,
        campaign_id: str,
        affiliate_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific campaign.

        Args:
            campaign_id: Campaign ID
            affiliate_id: Affiliate user ID (for authorization)

        Returns:
            Campaign data or None
        """
        from ..models.affiliate import REFERRAL_CAMPAIGNS_COLLECTION

        campaign = await self.db[REFERRAL_CAMPAIGNS_COLLECTION].find_one({
            "_id": campaign_id,
            "affiliate_id": affiliate_id
        })

        if campaign:
            campaign["id"] = campaign.pop("_id")

        return campaign

    async def update_campaign(
        self,
        campaign_id: str,
        affiliate_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a campaign.

        Args:
            campaign_id: Campaign ID
            affiliate_id: Affiliate user ID (for authorization)
            updates: Fields to update

        Returns:
            Updated campaign or None
        """
        from ..models.affiliate import REFERRAL_CAMPAIGNS_COLLECTION

        # Add updated_at timestamp
        updates["updated_at"] = datetime.utcnow()

        result = await self.db[REFERRAL_CAMPAIGNS_COLLECTION].find_one_and_update(
            {"_id": campaign_id, "affiliate_id": affiliate_id},
            {"$set": updates},
            return_document=True
        )

        if result:
            result["id"] = result.pop("_id")

        return result

    async def get_active_campaigns(
        self,
        organization_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all currently active campaigns for an organization.

        Args:
            organization_id: Organization ID

        Returns:
            List of active campaigns
        """
        from ..models.affiliate import REFERRAL_CAMPAIGNS_COLLECTION, CampaignStatus

        now = datetime.utcnow()

        campaigns = await self.db[REFERRAL_CAMPAIGNS_COLLECTION].find({
            "organization_id": organization_id,
            "status": CampaignStatus.ACTIVE,
            "start_date": {"$lte": now},
            "end_date": {"$gte": now}
        }).to_list(100)

        for campaign in campaigns:
            campaign["id"] = campaign.pop("_id")

        return campaigns

    async def get_campaign_by_code(
        self,
        campaign_code: str,
        organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get campaign by campaign code.

        Args:
            campaign_code: Campaign code
            organization_id: Organization ID

        Returns:
            Campaign data or None
        """
        from ..models.affiliate import REFERRAL_CAMPAIGNS_COLLECTION

        campaign = await self.db[REFERRAL_CAMPAIGNS_COLLECTION].find_one({
            "campaign_code": campaign_code.upper(),
            "organization_id": organization_id
        })

        if campaign:
            campaign["id"] = campaign.pop("_id")

        return campaign
