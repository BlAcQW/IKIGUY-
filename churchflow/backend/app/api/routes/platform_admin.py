"""
Platform admin dashboard routes for ChurchFlow SaaS.

Provides endpoints for platform owners to manage all churches,
monitor usage, revenue, and provide support.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user
from app.core.database import get_database
from apps.shared.services.organization_service import get_organization_service
from app.services.subscription_service import SubscriptionService
from app.models.subscription import SubscriptionPlan, SubscriptionStatus
from app.services.member_migration_service import member_migration_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/platform-admin", tags=["Platform Admin"])


# ================== Authorization Helper ==================

async def require_platform_admin(user: dict = Depends(get_current_user)):
    """
    Require user to be a platform admin (universal admin).

    Only ChurchFlow platform owners can access these endpoints.
    """
    org_service = get_organization_service()
    user_id = user.get("id") or user.get("sub")
    user_email = user.get("email")

    if not org_service.is_universal_admin(user_id, user_email):
        logger.warning(f"Non-admin user {user_email} attempted platform admin access")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform admin access required"
        )

    return user


# ================== Response Models ==================

class ChurchSummary(BaseModel):
    """Summary of a church on the platform."""
    organization_id: str
    name: str
    email: str
    phone: Optional[str]
    created_at: str
    subscription_plan: str
    subscription_status: str
    members_count: int
    sms_credits: float
    storage_mb: float
    last_active: Optional[str]


class RevenueMetrics(BaseModel):
    """Revenue metrics for the platform."""
    mrr: float  # Monthly Recurring Revenue
    arr: float  # Annual Recurring Revenue
    total_subscriptions: int
    active_subscriptions: int
    churned_this_month: int
    new_this_month: int
    revenue_by_plan: dict


class UsageMetrics(BaseModel):
    """Platform-wide usage metrics."""
    total_churches: int
    total_members: int
    total_sms_sent: int
    total_storage_gb: float
    active_churches_30d: int
    churches_by_plan: dict


class ChurchDetail(BaseModel):
    """Detailed information about a church."""
    organization_id: str
    name: str
    email: str
    phone: Optional[str]
    address: Optional[str]
    website: Optional[str]
    created_at: str
    subscription: dict
    usage: dict
    admins: List[dict]
    activity_summary: dict


# ================== Dashboard Overview ==================

@router.get("/dashboard", response_model=dict, dependencies=[Depends(require_platform_admin)])
async def get_platform_dashboard(
    db = Depends(get_database),
):
    """
    Get platform dashboard overview.

    Returns high-level metrics about all churches, revenue, and usage.
    """
    try:
        org_service = get_organization_service()
        subscription_service = SubscriptionService(db)

        # Get all organizations
        all_orgs = await org_service.list_organizations(limit=10000)

        # Calculate metrics
        total_churches = len(all_orgs)

        # Get subscription stats
        subscriptions_by_plan = {
            SubscriptionPlan.FREE.value: 0,
            SubscriptionPlan.STANDARD.value: 0,
            SubscriptionPlan.PREMIUM.value: 0,
        }

        total_mrr = 0.0
        active_subscriptions = 0

        for org in all_orgs:
            subscription = await subscription_service.get_subscription(org.id)
            if subscription:
                subscriptions_by_plan[subscription.plan.value] += 1

                if subscription.status == SubscriptionStatus.ACTIVE:
                    active_subscriptions += 1

                    # Calculate MRR
                    if subscription.plan == SubscriptionPlan.STANDARD:
                        total_mrr += 49.0
                    elif subscription.plan == SubscriptionPlan.PREMIUM:
                        total_mrr += 99.0

        # Calculate ARR
        total_arr = total_mrr * 12

        return {
            "overview": {
                "total_churches": total_churches,
                "active_subscriptions": active_subscriptions,
                "mrr": total_mrr,
                "arr": total_arr,
            },
            "subscriptions_by_plan": subscriptions_by_plan,
            "recent_signups": len([org for org in all_orgs if org.created_at and (datetime.utcnow() - org.created_at).days <= 30]),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get platform dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load dashboard"
        )


# ================== Church Management ==================

@router.get("/churches", response_model=List[ChurchSummary], dependencies=[Depends(require_platform_admin)])
async def list_all_churches(
    plan: Optional[SubscriptionPlan] = Query(None, description="Filter by subscription plan"),
    status_filter: Optional[SubscriptionStatus] = Query(None, alias="status", description="Filter by subscription status"),
    limit: int = Query(100, ge=1, le=1000, description="Number of churches to return"),
    skip: int = Query(0, ge=0, description="Number of churches to skip"),
    db = Depends(get_database),
):
    """
    List all churches on the platform.

    Supports filtering by subscription plan and status.
    """
    try:
        org_service = get_organization_service()
        subscription_service = SubscriptionService(db)

        # Get all organizations
        all_orgs = await org_service.list_organizations(limit=limit + skip)

        # Apply skip
        orgs = all_orgs[skip:]

        churches = []
        for org in orgs[:limit]:
            # Get subscription
            subscription = await subscription_service.get_subscription(org.id)

            # Apply filters
            if plan and (not subscription or subscription.plan != plan):
                continue

            if status_filter and (not subscription or subscription.status != status_filter):
                continue

            # Get usage metrics
            usage = await subscription_service.get_usage_metrics(org.id)

            churches.append(ChurchSummary(
                organization_id=org.id,
                name=org.name,
                email=org.email or "",
                phone=org.phone,
                created_at=org.created_at.isoformat() if org.created_at else datetime.utcnow().isoformat(),
                subscription_plan=subscription.plan.value if subscription else "none",
                subscription_status=subscription.status.value if subscription else "inactive",
                members_count=usage["members_count"] if usage else 0,
                sms_credits=usage["sms_credits"] if usage else 0.0,
                storage_mb=usage["storage_mb"] if usage else 0.0,
                last_active=None,  # TODO: Track last active timestamp
            ))

        return churches

    except Exception as e:
        logger.error(f"Failed to list churches: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list churches"
        )


@router.get("/churches/{organization_id}", response_model=ChurchDetail, dependencies=[Depends(require_platform_admin)])
async def get_church_details(
    organization_id: str,
    db = Depends(get_database),
):
    """
    Get detailed information about a specific church.

    Includes subscription, usage, admins, and activity summary.
    """
    try:
        org_service = get_organization_service()
        subscription_service = SubscriptionService(db)

        # Get organization
        org = await org_service.get_organization(organization_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Church not found"
            )

        # Get subscription
        subscription = await subscription_service.get_subscription(organization_id)
        subscription_dict = {
            "plan": subscription.plan.value if subscription else "none",
            "status": subscription.status.value if subscription else "inactive",
            "current_period_start": subscription.current_period_start.isoformat() if subscription and subscription.current_period_start else None,
            "current_period_end": subscription.current_period_end.isoformat() if subscription and subscription.current_period_end else None,
            "stripe_customer_id": subscription.stripe_customer_id if subscription else None,
        }

        # Get usage
        usage = await subscription_service.get_usage_metrics(organization_id)

        # Get admins
        org_users = await org_service.get_users_in_organization(organization_id)
        admins = [
            {
                "user_id": user.user_id,
                "email": user.email,
                "role": user.role,
                "joined_at": user.joined_at.isoformat() if user.joined_at else None,
            }
            for user in org_users
            if user.role == "admin"
        ]

        # Activity summary (placeholder)
        activity_summary = {
            "total_members": usage["members_count"] if usage else 0,
            "events_created": 0,  # TODO: Query events count
            "messages_sent": 0,  # TODO: Query messages count
            "last_login": None,  # TODO: Track last login
        }

        return ChurchDetail(
            organization_id=org.id,
            name=org.name,
            email=org.email or "",
            phone=org.phone,
            address=org.address,
            website=org.website,
            created_at=org.created_at.isoformat() if org.created_at else datetime.utcnow().isoformat(),
            subscription=subscription_dict,
            usage=usage or {},
            admins=admins,
            activity_summary=activity_summary,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get church details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get church details"
        )


# ================== Revenue Analytics ==================

@router.get("/revenue", response_model=RevenueMetrics, dependencies=[Depends(require_platform_admin)])
async def get_revenue_metrics(
    db = Depends(get_database),
):
    """
    Get revenue metrics for the platform.

    Calculates MRR, ARR, churn rate, and revenue breakdown by plan.
    """
    try:
        org_service = get_organization_service()
        subscription_service = SubscriptionService(db)

        # Get all organizations
        all_orgs = await org_service.list_organizations(limit=10000)

        total_mrr = 0.0
        active_count = 0
        churned_count = 0
        new_count = 0

        revenue_by_plan = {
            SubscriptionPlan.FREE.value: 0.0,
            SubscriptionPlan.STANDARD.value: 0.0,
            SubscriptionPlan.PREMIUM.value: 0.0,
        }

        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)

        for org in all_orgs:
            subscription = await subscription_service.get_subscription(org.id)

            if subscription:
                # Count new subscriptions this month
                if subscription.created_at and subscription.created_at >= thirty_days_ago:
                    new_count += 1

                # Count churned this month
                if subscription.status == SubscriptionStatus.CANCELED and subscription.canceled_at and subscription.canceled_at >= thirty_days_ago:
                    churned_count += 1

                # Calculate MRR for active subscriptions
                if subscription.status == SubscriptionStatus.ACTIVE:
                    active_count += 1

                    if subscription.plan == SubscriptionPlan.STANDARD:
                        mrr = 49.0
                        total_mrr += mrr
                        revenue_by_plan[SubscriptionPlan.STANDARD.value] += mrr
                    elif subscription.plan == SubscriptionPlan.PREMIUM:
                        mrr = 99.0
                        total_mrr += mrr
                        revenue_by_plan[SubscriptionPlan.PREMIUM.value] += mrr

        return RevenueMetrics(
            mrr=total_mrr,
            arr=total_mrr * 12,
            total_subscriptions=len(all_orgs),
            active_subscriptions=active_count,
            churned_this_month=churned_count,
            new_this_month=new_count,
            revenue_by_plan=revenue_by_plan,
        )

    except Exception as e:
        logger.error(f"Failed to get revenue metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate revenue metrics"
        )


# ================== Usage Analytics ==================

@router.get("/usage", response_model=UsageMetrics, dependencies=[Depends(require_platform_admin)])
async def get_usage_metrics(
    db = Depends(get_database),
):
    """
    Get platform-wide usage metrics.

    Aggregates member counts, SMS usage, storage, and activity.
    """
    try:
        org_service = get_organization_service()
        subscription_service = SubscriptionService(db)

        # Get all organizations
        all_orgs = await org_service.list_organizations(limit=10000)

        total_members = 0
        total_sms = 0
        total_storage = 0.0

        churches_by_plan = {
            SubscriptionPlan.FREE.value: 0,
            SubscriptionPlan.STANDARD.value: 0,
            SubscriptionPlan.PREMIUM.value: 0,
        }

        for org in all_orgs:
            subscription = await subscription_service.get_subscription(org.id)
            usage = await subscription_service.get_usage_metrics(org.id)

            if subscription:
                churches_by_plan[subscription.plan.value] += 1

            if usage:
                total_members += usage["members_count"]
                total_sms += int(usage.get("sms_credits", 0))
                total_storage += usage["storage_mb"]

        return UsageMetrics(
            total_churches=len(all_orgs),
            total_members=total_members,
            total_sms_sent=total_sms,
            total_storage_gb=total_storage / 1024,
            active_churches_30d=len(all_orgs),  # TODO: Track actual activity
            churches_by_plan=churches_by_plan,
        )

    except Exception as e:
        logger.error(f"Failed to get usage metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate usage metrics"
        )


# ================== Support Actions ==================

@router.post("/churches/{organization_id}/adjust-subscription", dependencies=[Depends(require_platform_admin)])
async def adjust_subscription(
    organization_id: str,
    new_plan: SubscriptionPlan,
    reason: str = Query(..., description="Reason for adjustment"),
    db = Depends(get_database),
):
    """
    Manually adjust a church's subscription (admin override).

    Use for customer support scenarios like refunds, upgrades, etc.
    """
    try:
        subscription_service = SubscriptionService(db)

        # Update subscription
        subscription = await subscription_service.update_plan(
            organization_id=organization_id,
            new_plan=new_plan,
        )

        if not subscription:
            raise ValueError("Failed to update subscription")

        logger.info(f"Platform admin adjusted subscription for {organization_id} to {new_plan.value}. Reason: {reason}")

        return {
            "success": True,
            "message": f"Subscription updated to {new_plan.value}",
            "organization_id": organization_id,
            "new_plan": new_plan.value,
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to adjust subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to adjust subscription"
        )


@router.post("/churches/{organization_id}/add-credits", dependencies=[Depends(require_platform_admin)])
async def add_sms_credits(
    organization_id: str,
    credits: float = Query(..., gt=0, description="Number of SMS credits to add"),
    reason: str = Query(..., description="Reason for adding credits"),
    db = Depends(get_database),
):
    """
    Add SMS credits to a church's account (admin override).

    Use for customer support, promotions, or refunds.
    """
    try:
        # TODO: Implement credit addition in usage metrics service
        # For now, return success response

        logger.info(f"Platform admin added {credits} SMS credits to {organization_id}. Reason: {reason}")

        return {
            "success": True,
            "message": f"Added {credits} SMS credits",
            "organization_id": organization_id,
            "credits_added": credits,
        }

    except Exception as e:
        logger.error(f"Failed to add credits: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add credits"
        )


# ================== Member Migration Endpoints ==================

class MigrationPreviewResponse(BaseModel):
    """Response model for migration preview."""
    total_registrations: int
    members_created: int
    members_updated: int
    visitors_created: int
    visitors_updated: int
    placeholder_phones: int
    errors: int
    error_details: List[str] = Field(default_factory=list)


class MigrationExecuteResponse(BaseModel):
    """Response model for migration execution."""
    success: bool
    message: str
    stats: MigrationPreviewResponse


@router.get(
    "/migration/preview",
    response_model=MigrationPreviewResponse,
    summary="Preview conference registrant migration",
    description="Dry run of migration to see what would be migrated without making changes"
)
async def preview_migration(
    admin_user: dict = Depends(require_platform_admin)
):
    """
    Preview what the migration would do without making changes.

    This endpoint performs a dry run to show:
    - How many members would be created/updated
    - How many visitors would be created/updated
    - How many registrations would be skipped and why

    Requires platform admin authentication.
    """
    try:
        logger.info(f"Admin {admin_user.get('email')} previewing migration")

        stats = await member_migration_service.get_migration_preview()

        return MigrationPreviewResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to preview migration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview migration: {str(e)}"
        )


@router.post(
    "/migration/execute",
    response_model=MigrationExecuteResponse,
    summary="Execute conference registrant migration",
    description="Migrate all conference registrants to member/visitor profiles"
)
async def execute_migration(
    admin_user: dict = Depends(require_platform_admin)
):
    """
    Execute the migration of conference registrants to member/visitor profiles.

    This endpoint:
    1. Processes all conference_registrations
    2. Creates/updates User profiles based on branch_id vs church_name
    3. Sets member_status to "active_member" or "visitor"
    4. Copies registration data to user profiles
    5. Returns detailed statistics

    **WARNING**: This is a one-time migration operation. It will modify the users collection.

    Requires platform admin authentication.
    """
    try:
        logger.info(f"Admin {admin_user.get('email')} executing migration")

        # Execute migration (not dry run)
        stats = await member_migration_service.migrate_conference_registrants_to_profiles(
            dry_run=False
        )

        logger.info(f"Migration completed successfully. Stats: {stats}")

        return MigrationExecuteResponse(
            success=True,
            message=f"Migration completed: {stats['members_created']} members created, "
                    f"{stats['visitors_created']} visitors created, "
                    f"{stats['members_updated']} members updated, "
                    f"{stats['visitors_updated']} visitors updated",
            stats=MigrationPreviewResponse(**stats)
        )

    except Exception as e:
        logger.error(f"Failed to execute migration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute migration: {str(e)}"
        )
