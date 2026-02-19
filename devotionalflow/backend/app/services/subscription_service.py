"""
Subscription service for DevotionalFlow.

Handles email, WhatsApp, and Facebook group subscriptions for drip feed content delivery.
"""

import logging
import sys
import secrets
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from bson import ObjectId
from fastapi import HTTPException, status

from app.db.mongodb import get_database
from app.models.subscription import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionInDB,
    SubscriptionResponse,
    SubscriptionListResponse,
    UnsubscribeRequest,
)
from app.config import settings

# Add shared path for integrations
sys.path.insert(0, "/opt/kasaai")

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for managing subscriptions and drip feed content delivery."""

    def __init__(self):
        """Initialize subscription service."""
        self.db = get_database()
        self.subscriptions_collection = self.db.subscriptions
        self.drip_feed_queue_collection = self.db.drip_feed_queue

    async def create_subscription(self, subscription_data: SubscriptionCreate) -> SubscriptionResponse:
        """
        Create a new subscription.

        Args:
            subscription_data: Subscription creation data

        Returns:
            SubscriptionResponse: Created subscription

        Raises:
            HTTPException: If email or WhatsApp already exists
        """
        # Check if email already exists
        if subscription_data.email:
            existing = await self.subscriptions_collection.find_one(
                {"email": subscription_data.email, "is_active": True}
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already subscribed"
                )

        # Check if WhatsApp already exists
        if subscription_data.whatsapp:
            existing = await self.subscriptions_collection.find_one(
                {"whatsapp": subscription_data.whatsapp, "is_active": True}
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="WhatsApp number already subscribed"
                )

        # Create subscription document
        subscription_dict = {
            "name": subscription_data.name,
            "email": subscription_data.email,
            "whatsapp": subscription_data.whatsapp,
            "facebook_group": subscription_data.facebook_group,
            "is_active": True,
            "verified_email": False,
            "verified_whatsapp": False,
            "preferences": subscription_data.preferences or {},
            "last_sent_at": None,
            "last_sent_content_id": None,
            "total_sent": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "unsubscribed_at": None,
        }

        result = await self.subscriptions_collection.insert_one(subscription_dict)
        subscription_dict["_id"] = result.inserted_id

        # Send verification email if email provided
        if subscription_data.email:
            await self._send_verification_email(subscription_dict["_id"], subscription_data.email)

        # Send verification WhatsApp if WhatsApp provided
        if subscription_data.whatsapp:
            await self._send_verification_whatsapp(subscription_dict["_id"], subscription_data.whatsapp)

        logger.info(f"Created subscription: {result.inserted_id} for {subscription_data.email or subscription_data.whatsapp}")

        return self._to_response(subscription_dict)

    async def get_subscription(self, subscription_id: str) -> SubscriptionResponse:
        """
        Get a subscription by ID.

        Args:
            subscription_id: Subscription ID

        Returns:
            SubscriptionResponse: Subscription data

        Raises:
            HTTPException: If subscription not found
        """
        if not ObjectId.is_valid(subscription_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid subscription ID"
            )

        subscription = await self.subscriptions_collection.find_one(
            {"_id": ObjectId(subscription_id)}
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        return self._to_response(subscription)

    async def list_subscriptions(
        self,
        page: int = 1,
        page_size: int = 50,
        is_active: Optional[bool] = None,
        channel: Optional[str] = None
    ) -> SubscriptionListResponse:
        """
        List subscriptions with pagination and filters.

        Args:
            page: Page number
            page_size: Items per page
            is_active: Filter by active status
            channel: Filter by channel (email, whatsapp, facebook)

        Returns:
            SubscriptionListResponse: Paginated subscriptions
        """
        query = {}

        if is_active is not None:
            query["is_active"] = is_active

        if channel == "email":
            query["email"] = {"$ne": None}
        elif channel == "whatsapp":
            query["whatsapp"] = {"$ne": None}
        elif channel == "facebook":
            query["facebook_group"] = True

        total = await self.subscriptions_collection.count_documents(query)

        skip = (page - 1) * page_size
        cursor = (
            self.subscriptions_collection.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(page_size)
        )

        subscriptions = []
        async for sub in cursor:
            subscriptions.append(self._to_response(sub))

        total_pages = (total + page_size - 1) // page_size

        return SubscriptionListResponse(
            subscriptions=subscriptions,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update_subscription(
        self,
        subscription_id: str,
        update_data: SubscriptionUpdate
    ) -> SubscriptionResponse:
        """
        Update subscription preferences.

        Args:
            subscription_id: Subscription ID
            update_data: Update data

        Returns:
            SubscriptionResponse: Updated subscription

        Raises:
            HTTPException: If subscription not found
        """
        if not ObjectId.is_valid(subscription_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid subscription ID"
            )

        update_dict = {"updated_at": datetime.utcnow()}

        if update_data.name is not None:
            update_dict["name"] = update_data.name
        if update_data.email is not None:
            update_dict["email"] = update_data.email
            update_dict["verified_email"] = False  # Require re-verification
        if update_data.whatsapp is not None:
            update_dict["whatsapp"] = update_data.whatsapp
            update_dict["verified_whatsapp"] = False  # Require re-verification
        if update_data.facebook_group is not None:
            update_dict["facebook_group"] = update_data.facebook_group
        if update_data.preferences is not None:
            update_dict["preferences"] = update_data.preferences
        if update_data.is_active is not None:
            update_dict["is_active"] = update_data.is_active
            if not update_data.is_active:
                update_dict["unsubscribed_at"] = datetime.utcnow()

        result = await self.subscriptions_collection.update_one(
            {"_id": ObjectId(subscription_id)},
            {"$set": update_dict}
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        # Get updated subscription
        subscription = await self.subscriptions_collection.find_one(
            {"_id": ObjectId(subscription_id)}
        )

        return self._to_response(subscription)

    async def unsubscribe(self, unsubscribe_data: UnsubscribeRequest) -> Dict[str, Any]:
        """
        Unsubscribe a user (by email, WhatsApp, or token).

        Args:
            unsubscribe_data: Unsubscribe request data

        Returns:
            Dict with success status
        """
        query = {}

        if unsubscribe_data.email:
            query["email"] = unsubscribe_data.email
        elif unsubscribe_data.whatsapp:
            query["whatsapp"] = unsubscribe_data.whatsapp
        elif unsubscribe_data.token:
            # Token-based unsubscribe (from email link)
            query["unsubscribe_token"] = unsubscribe_data.token
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email, WhatsApp, or token required"
            )

        result = await self.subscriptions_collection.update_many(
            query,
            {
                "$set": {
                    "is_active": False,
                    "unsubscribed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            }
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        logger.info(f"Unsubscribed {result.matched_count} subscription(s)")

        return {
            "success": True,
            "message": "Successfully unsubscribed",
            "unsubscribed_count": result.matched_count,
        }

    async def verify_subscription(
        self,
        subscription_id: str,
        channel: str,
        token: str
    ) -> Dict[str, Any]:
        """
        Verify subscription channel (email or WhatsApp).

        Args:
            subscription_id: Subscription ID
            channel: Channel to verify (email or whatsapp)
            token: Verification token

        Returns:
            Dict with success status
        """
        if not ObjectId.is_valid(subscription_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid subscription ID"
            )

        subscription = await self.subscriptions_collection.find_one(
            {"_id": ObjectId(subscription_id)}
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        # Verify token (in production, store token in subscription and verify)
        # For now, we'll just mark as verified
        update_field = f"verified_{channel}"
        if channel not in ["email", "whatsapp"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid channel. Use 'email' or 'whatsapp'"
            )

        await self.subscriptions_collection.update_one(
            {"_id": ObjectId(subscription_id)},
            {"$set": {update_field: True, "updated_at": datetime.utcnow()}}
        )

        return {"success": True, "message": f"{channel.capitalize()} verified"}

    async def get_active_subscribers(
        self,
        channel: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all active subscribers for drip feed delivery.

        Args:
            channel: Filter by channel (email, whatsapp, facebook)

        Returns:
            List of subscriber dictionaries
        """
        query = {"is_active": True}

        if channel == "email":
            query["email"] = {"$ne": None}
            query["verified_email"] = True
        elif channel == "whatsapp":
            query["whatsapp"] = {"$ne": None}
            query["verified_whatsapp"] = True
        elif channel == "facebook":
            query["facebook_group"] = True

        subscribers = []
        async for sub in self.subscriptions_collection.find(query):
            subscribers.append({
                "id": str(sub["_id"]),
                "name": sub.get("name", ""),
                "email": sub.get("email"),
                "whatsapp": sub.get("whatsapp"),
                "facebook_group": sub.get("facebook_group", False),
                "preferences": sub.get("preferences", {}),
                "last_sent_at": sub.get("last_sent_at"),
            })

        return subscribers

    async def _send_verification_email(self, subscription_id: ObjectId, email: str) -> None:
        """Send verification email to subscriber."""
        try:
            from apps.shared.services.unified_email_service import get_email_service

            email_service = get_email_service()
            unsubscribe_token = secrets.token_urlsafe(32)

            # Store unsubscribe token
            await self.subscriptions_collection.update_one(
                {"_id": subscription_id},
                {"$set": {"unsubscribe_token": unsubscribe_token}}
            )

            verification_url = f"{settings.FRONTEND_URL}/subscriptions/verify?token={unsubscribe_token}&id={str(subscription_id)}"
            unsubscribe_url = f"{settings.FRONTEND_URL}/subscriptions/unsubscribe?token={unsubscribe_token}"

            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Verify Your Subscription</title>
            </head>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #4CAF50;">FreshManna</h1>
                </div>
                <div style="background-color: #ffffff; padding: 30px; border-radius: 10px;">
                    <h2>Verify Your Subscription</h2>
                    <p>Thank you for subscribing to FreshManna daily devotionals!</p>
                    <p>Please verify your email address by clicking the button below:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_url}"
                           style="display: inline-block; background-color: #4CAF50; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                            Verify Email
                        </a>
                    </div>
                    <p style="font-size: 12px; color: #999;">
                        If you didn't subscribe, you can <a href="{unsubscribe_url}">unsubscribe here</a>.
                    </p>
                </div>
            </body>
            </html>
            """

            text_body = f"""
Verify Your Subscription

Thank you for subscribing to FreshManna daily devotionals!

Please verify your email address by visiting:
{verification_url}

If you didn't subscribe, you can unsubscribe here:
{unsubscribe_url}
"""

            await email_service.send_email(
                to=email,
                subject="Verify Your FreshManna Subscription",
                body=text_body,
                html_body=html_body,
                from_email="noreply@ailabsafrica.com",
                from_name="FreshManna"
            )

            logger.info(f"Verification email sent to {email}")

        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {e}")

    async def _send_verification_whatsapp(self, subscription_id: ObjectId, whatsapp: str) -> None:
        """Send verification WhatsApp message to subscriber."""
        try:
            from twilio.rest import Client as TwilioClient
            from twilio.base.exceptions import TwilioRestException

            # Check if Twilio is configured
            if not hasattr(settings, "TWILIO_ACCOUNT_SID") or not settings.TWILIO_ACCOUNT_SID:
                logger.warning("Twilio not configured - skipping WhatsApp verification")
                return

            # Initialize Twilio client
            twilio_client = TwilioClient(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
            from_number = settings.TWILIO_WHATSAPP_NUMBER if hasattr(settings, "TWILIO_WHATSAPP_NUMBER") else None

            if not from_number:
                logger.warning("Twilio WhatsApp number not configured")
                return

            unsubscribe_token = secrets.token_urlsafe(32)

            # Store unsubscribe token
            await self.subscriptions_collection.update_one(
                {"_id": subscription_id},
                {"$set": {"unsubscribe_token": unsubscribe_token}}
            )

            verification_url = f"{settings.FRONTEND_URL}/subscriptions/verify?token={unsubscribe_token}&id={str(subscription_id)}"

            message = f"""Welcome to FreshManna! 🙏

Thank you for subscribing to daily devotionals.

To verify your subscription, please visit:
{verification_url}

You'll receive daily spiritual content via WhatsApp.

To unsubscribe, reply STOP or visit: {settings.FRONTEND_URL}/subscriptions/unsubscribe?token={unsubscribe_token}"""

            # Ensure phone number has 'whatsapp:' prefix
            to_phone = whatsapp if whatsapp.startswith("whatsapp:") else f"whatsapp:{whatsapp}"

            # Send WhatsApp via Twilio
            twilio_message = twilio_client.messages.create(
                to=to_phone,
                from_=from_number,
                body=message
            )

            logger.info(f"Verification WhatsApp sent to {whatsapp}, SID: {twilio_message.sid}")

        except TwilioRestException as e:
            logger.error(f"Twilio error sending verification WhatsApp to {whatsapp}: {e.code} - {e.msg}")
        except Exception as e:
            logger.error(f"Failed to send verification WhatsApp to {whatsapp}: {e}")

    def _to_response(self, subscription_dict: dict) -> SubscriptionResponse:
        """Convert subscription dict to response model."""
        return SubscriptionResponse(
            id=str(subscription_dict["_id"]),
            name=subscription_dict.get("name", ""),
            email=subscription_dict.get("email"),
            whatsapp=subscription_dict.get("whatsapp"),
            facebook_group=subscription_dict.get("facebook_group", False),
            is_active=subscription_dict.get("is_active", True),
            verified_email=subscription_dict.get("verified_email", False),
            verified_whatsapp=subscription_dict.get("verified_whatsapp", False),
            preferences=subscription_dict.get("preferences", {}),
            last_sent_at=subscription_dict.get("last_sent_at").isoformat() if subscription_dict.get("last_sent_at") else None,
            total_sent=subscription_dict.get("total_sent", 0),
            created_at=subscription_dict.get("created_at", datetime.utcnow()).isoformat(),
            updated_at=subscription_dict.get("updated_at", datetime.utcnow()).isoformat(),
        )


# Global service instance
_subscription_service: Optional[SubscriptionService] = None


def get_subscription_service() -> SubscriptionService:
    """Get or create subscription service instance."""
    global _subscription_service
    if _subscription_service is None:
        _subscription_service = SubscriptionService()
    return _subscription_service

