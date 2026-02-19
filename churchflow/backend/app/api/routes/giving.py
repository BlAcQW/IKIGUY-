"""
Giving/Donation API Routes for ChurchFlow

Handles online giving, recurring donations, pledges, and donor management.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies import get_current_user, require_organization_access
from apps.shared.dependencies import require_organization_admin_role
from app.core.database import get_database
from app.services.giving_service import get_giving_service
from app.services.gamification_service import get_gamification_service
from app.schemas.giving import (
    CreateDonationRequest,
    DonationResponse,
    ProcessDonationRequest,
    DonationListResponse,
    CreateRecurringDonationRequest,
    RecurringDonationResponse,
    RecurringDonationListResponse,
    GivingAnalyticsResponse,
    DonorProfileResponse
)
from app.models.giving import DonationStatus

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Donations ====================

@router.post("/donations", response_model=DonationResponse, status_code=status.HTTP_201_CREATED)
async def create_donation(
    donation_data: CreateDonationRequest,
    organization_id: str = Depends(require_organization_access),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Create a new donation.

    Creates a pending donation that needs to be processed with payment.
    """
    try:
        giving_service = get_giving_service(db)
        user_id = current_user.get("id") or current_user.get("sub")

        donation = await giving_service.create_donation(
            organization_id=organization_id,
            donor_data=donation_data.model_dump(),
            user_id=user_id
        )

        logger.info(f"Donation created: {donation.id} for organization {organization_id}")
        return donation

    except Exception as e:
        logger.error(f"Failed to create donation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create donation: {str(e)}"
        )


@router.post("/donations/process", response_model=DonationResponse)
async def process_donation(
    payment_data: ProcessDonationRequest,
    background_tasks: BackgroundTasks,
    organization_id: str = Depends(require_organization_access),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Process payment for a pending donation.

    Charges the payment method and completes the donation.
    Awards gamification points (capped at 50) in background.
    """
    try:
        giving_service = get_giving_service(db)

        donation = await giving_service.process_donation_payment(
            donation_id=payment_data.donation_id,
            stripe_payment_method_id=payment_data.stripe_payment_method_id
        )

        logger.info(f"Donation processed: {donation.id}, amount: {donation.amount}")

        # GAMIFICATION: Award points for donation in background (capped at 50)
        if donation.status == DonationStatus.COMPLETED:
            user_id = str(current_user.get("id"))
            if user_id:
                background_tasks.add_task(
                    award_donation_gamification,
                    user_id=user_id,
                    organization_id=organization_id,
                    donation_id=str(donation.id),
                    amount=float(donation.amount)
                )

        return donation

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to process donation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment processing failed: {str(e)}"
        )


@router.get("/donations/{donation_id}", response_model=DonationResponse)
async def get_donation(
    donation_id: str,
    organization_id: str = Depends(require_organization_access),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get donation by ID"""
    giving_service = get_giving_service(db)
    donation = await giving_service.get_donation(donation_id)

    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Donation {donation_id} not found"
        )

    # Verify organization access
    if donation.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return donation


@router.get("/donations", response_model=DonationListResponse)
async def list_donations(
    organization_id: str = Depends(require_organization_access),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
    donor_id: Optional[str] = Query(None, description="Filter by donor ID"),
    status_filter: Optional[DonationStatus] = Query(None, alias="status", description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page")
):
    """
    List donations for organization.

    Supports filtering by donor, status, and date range.
    """
    giving_service = get_giving_service(db)

    result = await giving_service.list_donations(
        organization_id=organization_id,
        donor_id=donor_id,
        status=status_filter,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size
    )

    return result


@router.get("/donations/my/history", response_model=DonationListResponse)
async def get_my_donation_history(
    organization_id: str = Depends(require_organization_access),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Get current user's donation history.

    Returns all donations made by the authenticated user.
    """
    giving_service = get_giving_service(db)
    user_id = current_user.get("id") or current_user.get("sub")

    result = await giving_service.list_donations(
        organization_id=organization_id,
        donor_id=user_id,
        page=page,
        page_size=page_size
    )

    return result


# ==================== Recurring Donations ====================

@router.post("/recurring-donations", response_model=RecurringDonationResponse, status_code=status.HTTP_201_CREATED)
async def create_recurring_donation(
    recurring_data: CreateRecurringDonationRequest,
    organization_id: str = Depends(require_organization_access),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Create a recurring donation with Stripe subscription.

    Sets up automatic recurring payments.
    """
    try:
        giving_service = get_giving_service(db)
        user_id = current_user.get("id") or current_user.get("sub")

        recurring = await giving_service.create_recurring_donation(
            organization_id=organization_id,
            donor_id=user_id,
            recurring_data=recurring_data.model_dump()
        )

        logger.info(f"Recurring donation created: {recurring.id}, amount: {recurring.amount}")
        return recurring

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create recurring donation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create recurring donation: {str(e)}"
        )


@router.delete("/recurring-donations/{recurring_id}", response_model=RecurringDonationResponse)
async def cancel_recurring_donation(
    recurring_id: str,
    organization_id: str = Depends(require_organization_access),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Cancel a recurring donation.

    Cancels the Stripe subscription and stops future payments.
    """
    try:
        giving_service = get_giving_service(db)
        user_id = current_user.get("id") or current_user.get("sub")

        recurring = await giving_service.cancel_recurring_donation(
            recurring_donation_id=recurring_id,
            donor_id=user_id
        )

        logger.info(f"Recurring donation cancelled: {recurring.id}")
        return recurring

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to cancel recurring donation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel recurring donation: {str(e)}"
        )


@router.get("/recurring-donations/my/active", response_model=RecurringDonationListResponse)
async def get_my_recurring_donations(
    organization_id: str = Depends(require_organization_access),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get current user's active recurring donations.
    """
    user_id = current_user.get("id") or current_user.get("sub")

    cursor = db.recurring_donations.find({
        "organization_id": organization_id,
        "donor_id": user_id,
        "is_active": True
    }).sort("created_at", -1)

    docs = await cursor.to_list(length=100)

    from app.models.giving import RecurringDonation
    recurring_donations = [
        RecurringDonation(**{**doc, "_id": str(doc["_id"])})
        for doc in docs
    ]

    return {
        "recurring_donations": recurring_donations,
        "total": len(recurring_donations),
        "page": 1,
        "page_size": 100,
        "has_more": False
    }


# ==================== Donor Profile ====================

@router.get("/donor-profile/me", response_model=DonorProfileResponse)
async def get_my_donor_profile(
    organization_id: str = Depends(require_organization_access),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get current user's donor profile.

    Returns giving history and statistics.
    """
    giving_service = get_giving_service(db)
    user_id = current_user.get("id") or current_user.get("sub")

    profile = await giving_service.get_donor_profile(
        organization_id=organization_id,
        user_id=user_id
    )

    if not profile:
        # Return empty profile
        from app.models.giving import DonorProfile
        profile = DonorProfile(
            id=user_id,
            organization_id=organization_id,
            user_id=user_id,
            donor_name=current_user.get("name", ""),
            donor_email=current_user.get("email"),
            donor_phone=current_user.get("phone")
        )

    # Add active counts
    active_recurring = await db.recurring_donations.count_documents({
        "organization_id": organization_id,
        "donor_id": user_id,
        "is_active": True
    })

    active_pledges = await db.pledges.count_documents({
        "organization_id": organization_id,
        "donor_id": user_id,
        "is_fulfilled": False
    })

    profile_dict = profile.model_dump()
    profile_dict["active_recurring_count"] = active_recurring
    profile_dict["active_pledge_count"] = active_pledges

    return profile_dict


# ==================== Analytics ====================

@router.get("/analytics", response_model=GivingAnalyticsResponse)
async def get_giving_analytics(
    organization_id: str = Depends(require_organization_admin_role),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
    period: str = Query("30d", description="Period: 7d, 30d, 90d, 1y, custom"),
    start_date: Optional[datetime] = Query(None, description="Custom start date"),
    end_date: Optional[datetime] = Query(None, description="Custom end date")
):
    """
    Get giving analytics for organization.

    Admin only. Returns comprehensive giving statistics.

    Requires organization admin role - only admins can view giving analytics.
    """

    giving_service = get_giving_service(db)

    # Calculate date range
    now = datetime.utcnow()
    if period == "custom" and start_date and end_date:
        period_start = start_date
        period_end = end_date
    elif period == "7d":
        period_start = now - timedelta(days=7)
        period_end = now
    elif period == "90d":
        period_start = now - timedelta(days=90)
        period_end = now
    elif period == "1y":
        period_start = now - timedelta(days=365)
        period_end = now
    else:  # default 30d
        period_start = now - timedelta(days=30)
        period_end = now

    analytics = await giving_service.get_giving_analytics(
        organization_id=organization_id,
        start_date=period_start,
        end_date=period_end
    )

    return analytics


# ============================================================================
# GAMIFICATION BACKGROUND TASKS
# ============================================================================

async def award_donation_gamification(
    user_id: str,
    organization_id: str,
    donation_id: str,
    amount: float
):
    """
    Background task to award gamification points for donations.

    IMPORTANT: Points are capped at 50 to prevent pay-to-win dynamics.
    Formula: min(amount * 0.1, 50)

    Args:
        user_id: User ID who made donation
        organization_id: Organization ID
        donation_id: Donation record ID
        amount: Donation amount
    """
    try:
        from app.core.database import get_database
        from bson import ObjectId

        db = get_database()
        gamification_service = get_gamification_service(db)

        # Calculate points (capped at 50)
        from app.services.gamification_points_service import POINT_RULES
        multiplier = POINT_RULES["donation_base_multiplier"]
        max_points = POINT_RULES["donation_max_points"]
        points = int(min(amount * multiplier, max_points))

        # Award points
        points_result = await gamification_service.award_points(
            user_id=user_id,
            organization_id=organization_id,
            points=points,
            action="donation_made",
            reference_id=donation_id,
            reference_type="donation",
            metadata={"amount": amount}
        )

        logger.info(
            f"[Donation] Gamification points awarded: user={user_id}, "
            f"amount=${amount:.2f}, points={points_result['points_awarded']}, "
            f"level_up={points_result['level_up']}"
        )

        # Update donation count statistic
        await db.gamification_profiles.update_one(
            {"user_id": ObjectId(user_id), "organization_id": ObjectId(organization_id)},
            {
                "$inc": {"total_donations_count": 1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        logger.info(f"[Donation] Donation count updated for user={user_id}")

    except Exception as e:
        # Log error but don't fail the donation
        logger.error(f"Donation gamification error: {e}", exc_info=True)
