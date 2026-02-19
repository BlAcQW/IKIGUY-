"""
Subscription routes for DevotionalFlow.

Handles subscription management (subscribe, unsubscribe, list) and drip feed delivery.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Dict, Any, Optional
import logging

from app.models.subscription import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
    SubscriptionListResponse,
    UnsubscribeRequest,
)
from app.services.subscription_service import get_subscription_service
from app.services.drip_feed_service import get_drip_feed_service
from app.utils.auth import get_current_admin, TokenData

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/subscribe",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subscribe to daily devotionals",
    description="Subscribe to receive daily devotionals via email, WhatsApp, or join Facebook group"
)
async def subscribe(
    subscription_data: SubscriptionCreate
):
    """
    Subscribe to daily devotionals.

    You can subscribe via:
    - Email: Provide email address
    - WhatsApp: Provide WhatsApp number (E.164 format, e.g., +233123456789)
    - Facebook Group: Set facebook_group to true (you'll join manually)

    At least one channel must be provided.
    """
    if not subscription_data.email and not subscription_data.whatsapp and not subscription_data.facebook_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one subscription channel (email, whatsapp, or facebook_group) must be provided"
        )

    service = get_subscription_service()
    return await service.create_subscription(subscription_data)


@router.get(
    "/subscriptions",
    response_model=SubscriptionListResponse,
    summary="List subscriptions (Admin only)",
    description="Get paginated list of all subscriptions. Admin only."
)
async def list_subscriptions(
    page: int = 1,
    page_size: int = 50,
    is_active: Optional[bool] = None,
    channel: Optional[str] = None,
    current_admin: TokenData = Depends(get_current_admin),
):
    """
    List all subscriptions with pagination and filters.

    **Requires admin role.**

    Query parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 50)
    - is_active: Filter by active status (true/false)
    - channel: Filter by channel (email, whatsapp, facebook)
    """
    service = get_subscription_service()
    return await service.list_subscriptions(
        page=page,
        page_size=page_size,
        is_active=is_active,
        channel=channel
    )


@router.get(
    "/subscriptions/{subscription_id}",
    response_model=SubscriptionResponse,
    summary="Get subscription details (Admin only)",
    description="Get a specific subscription by ID. Admin only."
)
async def get_subscription(
    subscription_id: str,
    current_admin: TokenData = Depends(get_current_admin),
):
    """Get subscription details by ID. Admin only."""
    service = get_subscription_service()
    return await service.get_subscription(subscription_id)


@router.put(
    "/subscriptions/{subscription_id}",
    response_model=SubscriptionResponse,
    summary="Update subscription (Admin only)",
    description="Update subscription preferences. Admin only."
)
async def update_subscription(
    subscription_id: str,
    update_data: SubscriptionUpdate,
    current_admin: TokenData = Depends(get_current_admin),
):
    """Update subscription preferences. Admin only."""
    service = get_subscription_service()
    return await service.update_subscription(subscription_id, update_data)


@router.post(
    "/unsubscribe",
    response_model=Dict[str, Any],
    summary="Unsubscribe from daily devotionals",
    description="Unsubscribe using email, WhatsApp, or unsubscribe token"
)
async def unsubscribe(
    unsubscribe_data: UnsubscribeRequest
):
    """
    Unsubscribe from daily devotionals.

    You can unsubscribe using:
    - Email: Provide your email address
    - WhatsApp: Provide your WhatsApp number
    - Token: Provide unsubscribe token from email/WhatsApp link
    """
    service = get_subscription_service()
    return await service.unsubscribe(unsubscribe_data)


@router.get(
    "/subscriptions/verify/{subscription_id}",
    response_model=Dict[str, Any],
    summary="Verify subscription",
    description="Verify subscription channel (email or WhatsApp) using token"
)
async def verify_subscription(
    subscription_id: str,
    channel: str,
    token: str
):
    """
    Verify subscription channel.

    Query parameters:
    - channel: Channel to verify (email or whatsapp)
    - token: Verification token from email/WhatsApp
    """
    service = get_subscription_service()
    return await service.verify_subscription(subscription_id, channel, token)


@router.post(
    "/admin/subscriptions/drip-feed/send",
    response_model=Dict[str, Any],
    summary="Send daily devotional to subscribers (Admin only)",
    description="Manually trigger drip feed delivery. Admin only."
)
async def send_daily_devotional(
    current_admin: TokenData = Depends(get_current_admin),
):
    """
    Manually trigger drip feed delivery of today's devotional.

    **Requires admin role.**

    This sends today's published devotional to all active subscribers
    via their preferred channels (email, WhatsApp, Facebook group).
    """
    logger.info(f"Admin {current_admin.email} triggered drip feed delivery")
    service = get_drip_feed_service()
    return await service.send_daily_devotional_to_subscribers()


@router.post(
    "/admin/subscriptions/drip-feed/custom",
    response_model=Dict[str, Any],
    summary="Send custom content to subscribers (Admin only)",
    description="Send custom content to subscribers. Admin only."
)
async def send_custom_content(
    content: Dict[str, Any] = Body(...),
    channel: Optional[str] = None,
    current_admin: TokenData = Depends(get_current_admin),
):
    """
    Send custom content to subscribers.

    **Requires admin role.**

    Request body should include:
    - title: Content title
    - body: Content body/text
    - link: Optional link URL

    Query parameters:
    - channel: Filter by channel (email, whatsapp, facebook)
    """
    logger.info(f"Admin {current_admin.email} sending custom content to subscribers")
    service = get_drip_feed_service()
    return await service.send_custom_content_to_subscribers(content, channel)

