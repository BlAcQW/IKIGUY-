"""
Affiliate Program API Routes.

Provides endpoints for multi-level marketing (MLM) / affiliate program:
- Enrollment and profile management
- Referral tracking and attribution
- Commission tracking
- Payout requests
- Network management

Author: KasaAI Team
Date: 2025-11-18
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from typing import Optional, List
from decimal import Decimal

from ..auth import get_current_user_mongo, get_user_from_header
from ..services.affiliate_service import AffiliateService
from ..mongo import get_database
from ..middleware.organization_context import get_organization_context, require_organization_context
from ..schemas.affiliate import (
    # Request schemas
    JoinProgramRequest,
    UpdateProfileRequest,
    CreateReferralLinkRequest,
    AttributeSignupRequest,
    ProcessCommissionRequest,
    PayoutRequestCreate,
    # Response schemas
    AffiliateProfileResponse,
    AffiliateStatsResponse,
    ReferralLinkResponse,
    ReferralCodeResponse,
    ReferralResponse,
    ReferralListResponse,
    NetworkStatsResponse,
    CommissionRecordResponse,
    CommissionListResponse,
    CommissionSummaryResponse,
    PayoutRequestResponse,
    PayoutListResponse,
    TrackReferralResponse,
    AttributeSignupResponse,
    ProcessCommissionResponse,
)
from ..models.affiliate import CommissionStatus, PayoutMethod


router = APIRouter(prefix="/api/affiliates", tags=["affiliates"])


def get_affiliate_service(db=Depends(get_database)):
    """Dependency to get affiliate service instance."""
    return AffiliateService(db)


# ============================================================================
# Affiliate Profile Management
# ============================================================================

@router.post("/join", response_model=AffiliateProfileResponse)
async def join_program(
    request: Request,
    request_data: JoinProgramRequest,
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Join the affiliate program.

    Enrolls the current user in the affiliate program, generates a unique
    referral code, and optionally links to an upline affiliate.
    """
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")
        organization_id = get_organization_context(request)

        if not organization_id:
            raise HTTPException(
                status_code=400,
                detail="Organization ID required to join affiliate program (X-Organization-Id header)"
            )

        profile = await affiliate_service.join_program(
            user_id=user_id,
            organization_id=organization_id,
            upline_referral_code=request_data.upline_referral_code
        )

        return profile

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to join program: {str(e)}")


@router.get("/profile", response_model=AffiliateProfileResponse)
async def get_profile(
    request: Request,
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Get affiliate profile for current user.

    Returns the affiliate profile including referral code, statistics,
    and payout settings.
    """
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")
        # organization_id = get_organization_context(request)  # TODO: Use for multi-tenancy

        profile = await affiliate_service.get_profile(user_id)

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="User is not enrolled in the affiliate program"
            )

        return profile

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")


@router.patch("/profile", response_model=AffiliateProfileResponse)
async def update_profile(
    updates: UpdateProfileRequest,
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Update affiliate profile settings.

    Allows updating payout method, payout threshold, and payment method.
    """
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")

        # Convert to dict and remove None values
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}

        profile = await affiliate_service.update_profile(user_id, update_dict)

        return profile

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")


@router.get("/stats", response_model=AffiliateStatsResponse)
async def get_stats(
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Get affiliate dashboard statistics.

    Returns comprehensive statistics including:
    - Total earnings and pending commissions
    - This month and last month earnings
    - Referral counts by tier
    - Conversion rates and performance metrics
    """
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")

        stats = await affiliate_service.get_stats(user_id)

        return stats

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


# ============================================================================
# Referral Links
# ============================================================================

@router.get("/referral-links", response_model=List[ReferralLinkResponse])
async def get_referral_links(
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Get all referral links for current affiliate.

    Returns list of referral links with click and conversion statistics.
    """
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")

        links = await affiliate_service.get_referral_links(user_id)

        # Convert to response format with URLs
        base_url = "https://kasaai.ailabsafrica.com"
        response_links = []

        for link in links:
            # Build URL with query parameters
            url = f"{base_url}?ref={link.referral_code}"
            if link.utm_source:
                url += f"&utm_source={link.utm_source}"
            if link.utm_campaign:
                url += f"&utm_campaign={link.utm_campaign}"
            if link.utm_medium:
                url += f"&utm_medium={link.utm_medium}"

            response_links.append(ReferralLinkResponse(
                id=link.id,
                referral_code=link.referral_code,
                url=url,
                utm_source=link.utm_source,
                utm_campaign=link.utm_campaign,
                utm_medium=link.utm_medium,
                click_count=link.click_count,
                conversion_count=link.conversion_count,
                conversion_rate=link.conversion_rate,
                created_at=link.created_at
            ))

        return response_links

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get links: {str(e)}")


@router.post("/referral-links", response_model=ReferralLinkResponse)
async def create_referral_link(
    link_data: CreateReferralLinkRequest,
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Create custom referral link with UTM parameters.

    Allows creating branded referral links with custom UTM tracking
    for different marketing channels.
    """
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")

        link = await affiliate_service.create_referral_link(
            user_id=user_id,
            utm_source=link_data.utm_source,
            utm_campaign=link_data.utm_campaign,
            utm_medium=link_data.utm_medium
        )

        # Build URL
        base_url = "https://kasaai.ailabsafrica.com"
        url = f"{base_url}?ref={link.referral_code}"
        if link.utm_source:
            url += f"&utm_source={link.utm_source}"
        if link.utm_campaign:
            url += f"&utm_campaign={link.utm_campaign}"
        if link.utm_medium:
            url += f"&utm_medium={link.utm_medium}"

        return ReferralLinkResponse(
            id=link.id,
            referral_code=link.referral_code,
            url=url,
            utm_source=link.utm_source,
            utm_campaign=link.utm_campaign,
            utm_medium=link.utm_medium,
            click_count=link.click_count,
            conversion_count=link.conversion_count,
            conversion_rate=link.conversion_rate,
            created_at=link.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create link: {str(e)}")


@router.get("/referral-code", response_model=ReferralCodeResponse)
async def get_referral_code(
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Get primary referral code and URL for current affiliate.

    Returns the main referral code and formatted URL for sharing.
    """
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")

        profile = await affiliate_service.get_profile(user_id)

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="User is not enrolled in the affiliate program"
            )

        base_url = "https://kasaai.ailabsafrica.com"
        full_url = f"{base_url}?ref={profile.referral_code}"

        return ReferralCodeResponse(
            referral_code=profile.referral_code,
            base_url=base_url,
            full_url=full_url
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get referral code: {str(e)}")


# ============================================================================
# Referrals & Network
# ============================================================================

@router.get("/referrals", response_model=ReferralListResponse)
async def get_referrals(
    tier: Optional[int] = Query(None, description="Filter by tier (1, 2, or 3)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Get list of referrals for current affiliate.

    Returns paginated list of referrals with performance metrics.
    Can be filtered by tier level.
    """
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")

        referrals, total = await affiliate_service.get_referrals(
            user_id=user_id,
            tier=tier,
            limit=limit,
            offset=offset
        )

        return ReferralListResponse(
            items=referrals,
            total=total,
            limit=limit,
            offset=offset
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get referrals: {str(e)}")


@router.get("/network/stats", response_model=NetworkStatsResponse)
async def get_network_stats(
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Get network statistics for current affiliate.

    Returns comprehensive network metrics including:
    - Counts by tier (1, 2, 3)
    - Total network size
    - Total network sales and commissions
    """
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")

        stats = await affiliate_service.get_network_stats(user_id)

        return stats

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get network stats: {str(e)}")


@router.get("/network/tree")
async def get_network_tree(
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Get network tree structure for current affiliate.

    Returns the full referral network tree showing all downline affiliates
    organized by tiers.
    """
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")

        tree = await affiliate_service._build_network_tree(user_id)

        return tree

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get network tree: {str(e)}")


# ============================================================================
# Commissions
# ============================================================================

@router.get("/commissions", response_model=CommissionListResponse)
async def get_commissions(
    status: Optional[CommissionStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Get commission records for current affiliate.

    Returns paginated list of commission records with details about
    the purchase, commission amount, and status.
    """
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")

        commissions, total = await affiliate_service.get_commissions(
            user_id=user_id,
            status=status,
            limit=limit,
            offset=offset
        )

        return CommissionListResponse(
            items=commissions,
            total=total,
            limit=limit,
            offset=offset
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get commissions: {str(e)}")


@router.get("/commissions/{commission_id}", response_model=CommissionRecordResponse)
async def get_commission_by_id(
    commission_id: str,
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Get a specific commission record by ID.

    Returns detailed information about a single commission.
    """
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")

        commission = await affiliate_service.get_commission_by_id(
            user_id=user_id,
            commission_id=commission_id
        )

        if not commission:
            raise HTTPException(status_code=404, detail="Commission not found")

        return CommissionRecordResponse(**commission)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get commission: {str(e)}")


@router.get("/commissions/pending")
async def get_pending_commissions(
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Get pending commissions for current affiliate.

    Returns total pending commission amount and count.
    """
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")

        profile = await affiliate_service.get_profile(user_id)

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="User is not enrolled in the affiliate program"
            )

        # Get pending commission records
        commissions, total = await affiliate_service.get_commissions(
            user_id=user_id,
            status=CommissionStatus.APPROVED,  # Approved but not yet paid
            limit=100,
            offset=0
        )

        return {
            "pending_amount": profile.pending_commissions,
            "pending_count": total,
            "records": commissions
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending commissions: {str(e)}")


# ============================================================================
# Payouts
# ============================================================================

@router.get("/payouts", response_model=PayoutListResponse)
async def get_payouts(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service),
    db = Depends(get_database)
):
    """
    Get payout history for current affiliate.

    Returns paginated list of payout requests with status and details.
    """
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")

        # Get payouts from database
        total = await db.payout_requests.count_documents({"affiliate_id": user_id})

        cursor = db.payout_requests.find(
            {"affiliate_id": user_id}
        ).sort("created_at", -1).skip(offset).limit(limit)

        payouts = []
        async for payout_dict in cursor:
            payouts.append(PayoutRequestResponse(
                id=str(payout_dict["_id"]),
                amount=Decimal(str(payout_dict["amount"])),
                payout_method=payout_dict["payout_method"],
                processing_fee=Decimal(str(payout_dict.get("processing_fee", 0))),
                net_amount=Decimal(str(payout_dict["net_amount"])),
                status=payout_dict["status"],
                created_at=payout_dict["created_at"],
                processed_at=payout_dict.get("processed_at"),
                notes=payout_dict.get("notes"),
                failure_reason=payout_dict.get("failure_reason")
            ))

        return PayoutListResponse(
            items=payouts,
            total=total,
            limit=limit,
            offset=offset
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get payouts: {str(e)}")


@router.post("/payouts/request", response_model=PayoutRequestResponse)
async def request_payout(
    payout_data: PayoutRequestCreate,
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Request payout of pending commissions.

    Creates a payout request that will be processed based on the
    selected payout method (wallet credit, mobile money, bank transfer, PayPal).
    """
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")

        payout = await affiliate_service.request_payout(
            user_id=user_id,
            amount=payout_data.amount,
            payout_method=payout_data.payout_method,
            payment_method_id=payout_data.payment_method_id
        )

        return PayoutRequestResponse(
            id=payout.id,
            amount=payout.amount,
            payout_method=payout.payout_method,
            processing_fee=payout.processing_fee,
            net_amount=payout.net_amount,
            status=payout.status,
            created_at=payout.created_at,
            processed_at=payout.processed_at,
            notes=payout.notes,
            failure_reason=payout.failure_reason
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to request payout: {str(e)}")


# ============================================================================
# Public/Internal Endpoints
# ============================================================================

@router.get("/public/track-referral", response_model=TrackReferralResponse)
async def track_referral(
    ref: str = Query(..., description="Referral code"),
    utm_source: Optional[str] = Query(None, description="UTM source"),
    utm_campaign: Optional[str] = Query(None, description="UTM campaign"),
    utm_medium: Optional[str] = Query(None, description="UTM medium"),
    utm_content: Optional[str] = Query(None, description="UTM content"),
    utm_term: Optional[str] = Query(None, description="UTM term"),
    request: Request = None,
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Track referral link click (public endpoint).

    Records a click on a referral link for analytics purposes.
    Should be called when a user lands on the site with a referral code.

    Tracks UTM parameters for campaign attribution and analytics.
    """
    try:
        # Build UTM params dict
        utm_params = {}
        if utm_source:
            utm_params["utm_source"] = utm_source
        if utm_campaign:
            utm_params["utm_campaign"] = utm_campaign
        if utm_medium:
            utm_params["utm_medium"] = utm_medium
        if utm_content:
            utm_params["utm_content"] = utm_content
        if utm_term:
            utm_params["utm_term"] = utm_term

        # Track the click with full metadata
        click = await affiliate_service.track_click(
            referral_code=ref,
            request=request,
            utm_params=utm_params if utm_params else None
        )

        return TrackReferralResponse(
            success=True,
            referral_code=ref,
            message="Click tracked successfully"
        )

    except Exception as e:
        # Don't fail on tracking errors
        return TrackReferralResponse(
            success=False,
            referral_code=ref,
            message=f"Tracking error: {str(e)}"
        )


@router.post("/internal/attribute-signup", response_model=AttributeSignupResponse)
async def attribute_signup(
    request: Request,
    signup_data: AttributeSignupRequest,
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Attribute user signup to affiliate (internal endpoint).

    This endpoint is called after successful user registration to record
    the referral attribution. It should be called by the auth service.
    """
    try:
        attribution = await affiliate_service.attribute_signup(
            user_id=signup_data.user_id,
            organization_id=signup_data.organization_id,
            referral_code=signup_data.referral_code,
            request=request
        )

        if attribution:
            # Mark the click as converted for analytics
            try:
                await affiliate_service.mark_click_converted(
                    referral_code=signup_data.referral_code,
                    converted_user_id=signup_data.user_id
                )
            except Exception as e:
                # Log but don't fail if click marking fails
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to mark click as converted: {str(e)}")

            return AttributeSignupResponse(
                success=True,
                id=attribution.id,
                referred_user_id=attribution.referred_user_id,
                affiliate_id=attribution.affiliate_id,
                referral_code=attribution.referral_code,
                message="Signup attributed successfully"
            )
        else:
            return AttributeSignupResponse(
                success=False,
                referral_code=signup_data.referral_code,
                message="Referral code not found or invalid"
            )

    except HTTPException:
        raise
    except Exception as e:
        return AttributeSignupResponse(
            success=False,
            referral_code=signup_data.referral_code,
            message=f"Attribution error: {str(e)}"
        )


@router.post("/internal/process-commission", response_model=ProcessCommissionResponse)
async def process_commission(
    request: Request,
    commission_data: ProcessCommissionRequest,
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Process commission for a transaction (internal endpoint).

    This endpoint is called internally after a successful purchase
    to calculate and record multi-tier commissions.

    Should be called by wallet service after deposit completion.
    """
    try:
        # Use the commission processor which handles the full flow
        from ..services.affiliate_commission_processor import process_transaction_commission

        result = await process_transaction_commission(
            user_id=commission_data.user_id,
            organization_id=commission_data.organization_id,
            transaction_amount=commission_data.amount,
            transaction_id=commission_data.transaction_id,
            transaction_type="purchase"
        )

        if result["success"]:
            commissions_list = [
                {
                    "id": c.id,
                    "affiliate_id": c.affiliate_id,
                    "tier_level": c.tier_level,
                    "commission_amount": str(c.commission_amount),
                    "commission_rate": str(c.commission_rate)
                }
                for c in result["commission_records"]
            ]
            return ProcessCommissionResponse(
                success=True,
                commissions=commissions_list,
                commissions_created=commissions_list,
                total_commission_amount=result["total_commission_amount"]
            )
        else:
            return ProcessCommissionResponse(
                success=False,
                commissions=[],
                commissions_created=[],
                total_commission_amount=Decimal("0")
            )

    except Exception as e:
        # Log error but don't fail the transaction
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Commission processing failed for transaction {commission_data.transaction_id}: {str(e)}")

        return ProcessCommissionResponse(
            success=False,
            commissions=[],
            commissions_created=[],
            total_commission_amount=Decimal("0")
        )


# =============================================================================
# Leaderboard & Rankings
# =============================================================================

@router.get("/leaderboard")
async def get_leaderboard(
    period: str = Query("all_time", description="Time period: all_time, month, week"),
    metric: str = Query("earnings", description="Metric: earnings, referrals, sales"),
    limit: int = Query(100, le=500, description="Number of top affiliates"),
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Get affiliate leaderboard rankings.

    Shows top performing affiliates ranked by earnings, referrals, or sales.
    """
    try:
        org_id = current_user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="Organization ID required")

        leaderboard = await affiliate_service.get_leaderboard(
            organization_id=org_id,
            period=period,
            metric=metric,
            limit=limit
        )

        return {
            "leaderboard": leaderboard,
            "period": period,
            "metric": metric,
            "total_shown": len(leaderboard)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get leaderboard: {str(e)}"
        )


@router.get("/my-rank")
async def get_my_rank(
    metric: str = Query("earnings", description="Metric: earnings, referrals, sales"),
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Get current user's ranking on the leaderboard.
    """
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")

        rank_info = await affiliate_service.get_affiliate_rank(
            user_id=user_id,
            metric=metric
        )

        return rank_info

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get rank: {str(e)}"
        )


# =============================================================================
# Analytics & Conversion Tracking
# =============================================================================

@router.get("/analytics/conversion-rates")
async def get_conversion_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Get conversion analytics for current affiliate.

    Returns:
    - Overall conversion rate
    - Click-to-signup conversion rate
    - Traffic source breakdown with conversion rates
    - Daily conversion trends
    """
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")

        analytics = await affiliate_service.get_conversion_analytics(
            user_id=user_id,
            days=days
        )

        return analytics

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get conversion analytics: {str(e)}"
        )


@router.get("/analytics/traffic-sources")
async def get_traffic_sources(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Get traffic source breakdown for current affiliate.

    Returns breakdown of clicks and conversions by:
    - UTM source
    - UTM campaign
    - UTM medium
    """
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")

        analytics = await affiliate_service.get_conversion_analytics(
            user_id=user_id,
            days=days
        )

        # Extract just the traffic sources data
        return {
            "traffic_sources": analytics.get("traffic_sources", []),
            "period_days": days,
            "total_clicks": analytics.get("total_clicks", 0),
            "total_conversions": analytics.get("total_conversions", 0)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get traffic sources: {str(e)}"
        )


@router.get("/analytics/link-performance")
async def get_link_performance(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Get performance metrics for individual referral links.

    Returns per-link metrics including:
    - Click count
    - Conversion count
    - Conversion rate
    - UTM parameters
    """
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")

        link_performance = await affiliate_service.get_link_performance(
            user_id=user_id,
            days=days
        )

        return {
            "links": link_performance,
            "period_days": days,
            "total_links": len(link_performance)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get link performance: {str(e)}"
        )

# ========================================================================
# Campaign Management Endpoints
# ========================================================================

@router.get("/campaigns")
async def get_campaigns(
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Get all campaigns for the current affiliate.
    
    Optionally filter by status: draft, active, paused, completed, cancelled
    """
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")

        # Get affiliate profile to get affiliate_id
        profile = await affiliate_service.get_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Affiliate profile not found")

        campaigns = await affiliate_service.get_campaigns(
            affiliate_id=profile.user_id,
            status=status
        )

        return campaigns
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get campaigns: {str(e)}"
        )


@router.get("/campaigns/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """Get a specific campaign by ID."""
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")

        # Get affiliate profile
        profile = await affiliate_service.get_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Affiliate profile not found")

        campaign = await affiliate_service.get_campaign(
            campaign_id=campaign_id,
            affiliate_id=profile.user_id
        )

        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        return campaign
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get campaign: {str(e)}"
        )


@router.post("/campaigns", status_code=201)
async def create_campaign(
    campaign_data: dict,
    current_user: dict = Depends(get_user_from_header),
    organization_id: str = Depends(require_organization_context),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """
    Create a new referral campaign.
    
    Required fields:
    - name: Campaign name
    - campaign_code: Unique code (3-50 chars)
    - start_date: ISO datetime
    - end_date: ISO datetime
    - bonus_rate: Decimal (0.0-1.0, e.g., 0.05 = 5%)
    """
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")
        
        # Get affiliate profile
        profile = await affiliate_service.get_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Affiliate profile not found")
        
        from datetime import datetime
        from decimal import Decimal
        
        # Parse dates
        start_date = datetime.fromisoformat(campaign_data["start_date"].replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(campaign_data["end_date"].replace('Z', '+00:00'))
        
        # Create campaign
        campaign = await affiliate_service.create_campaign(
            affiliate_id=profile["user_id"],
            organization_id=organization_id,
            name=campaign_data["name"],
            description=campaign_data.get("description"),
            campaign_code=campaign_data["campaign_code"],
            start_date=start_date,
            end_date=end_date,
            bonus_rate=Decimal(str(campaign_data["bonus_rate"])),
            target_referrals=campaign_data.get("target_referrals"),
            target_sales=Decimal(str(campaign_data["target_sales"])) if campaign_data.get("target_sales") else None,
            prize=campaign_data.get("prize"),
            landing_page_url=campaign_data.get("landing_page_url"),
            utm_campaign=campaign_data.get("utm_campaign")
        )
        
        # Convert to dict for response
        campaign_dict = campaign.dict(by_alias=True)
        campaign_dict["id"] = str(campaign.id)
        
        return campaign_dict
        
    except HTTPException:
        raise
    except KeyError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required field: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid value: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create campaign: {str(e)}"
        )


@router.patch("/campaigns/{campaign_id}")
async def update_campaign(
    campaign_id: str,
    updates: dict,
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """Update a campaign."""
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")
        
        # Get affiliate profile
        profile = await affiliate_service.get_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Affiliate profile not found")
        
        campaign = await affiliate_service.update_campaign(
            campaign_id=campaign_id,
            affiliate_id=profile["user_id"],
            updates=updates
        )
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        return campaign
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update campaign: {str(e)}"
        )


@router.delete("/campaigns/{campaign_id}", status_code=204)
async def delete_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_user_from_header),
    affiliate_service: AffiliateService = Depends(get_affiliate_service)
):
    """Delete a campaign (sets status to cancelled)."""
    try:
        user_id = current_user.get("sub") or current_user.get("user_id")
        
        # Get affiliate profile
        profile = await affiliate_service.get_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Affiliate profile not found")
        
        # Update status to cancelled instead of actual deletion
        campaign = await affiliate_service.update_campaign(
            campaign_id=campaign_id,
            affiliate_id=profile["user_id"],
            updates={"status": "cancelled"}
        )
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete campaign: {str(e)}"
        )
