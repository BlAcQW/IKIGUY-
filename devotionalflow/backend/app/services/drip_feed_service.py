"""
Drip feed service for DevotionalFlow.

Handles scheduled delivery of devotionals to subscribers via email, WhatsApp, and Facebook group.
"""

import logging
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from bson import ObjectId

from app.db.mongodb import get_database
from app.config import settings

# Add shared path for integrations
sys.path.insert(0, "/opt/kasaai")

logger = logging.getLogger(__name__)


class DripFeedService:
    """Service for managing drip feed content delivery to subscribers."""

    def __init__(self):
        """Initialize drip feed service."""
        self.db = get_database()
        self.subscriptions_collection = self.db.subscriptions
        self.devotionals_collection = self.db.devotionals
        self.drip_feed_log_collection = self.db.drip_feed_log

    async def send_daily_devotional_to_subscribers(self) -> Dict[str, Any]:
        """
        Send today's devotional to all active subscribers.

        This is called by the scheduler daily.

        Returns:
            Dict with delivery statistics
        """
        # Get today's devotional
        today = datetime.utcnow().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())

        devotional = await self.devotionals_collection.find_one({
            "published_at": {"$gte": start_of_day, "$lte": end_of_day},
            "status": "published"
        })

        if not devotional:
            logger.info("No devotional published for today, skipping drip feed")
            return {
                "success": True,
                "message": "No devotional published for today",
                "sent": 0,
            }

        # Get all active subscribers
        subscribers = await self._get_active_subscribers()

        stats = {
            "email_sent": 0,
            "email_failed": 0,
            "whatsapp_sent": 0,
            "whatsapp_failed": 0,
            "facebook_notified": 0,
            "total_subscribers": len(subscribers),
        }

        # Send to each subscriber
        for subscriber in subscribers:
            try:
                # Send via email if subscribed
                if subscriber.get("email") and subscriber.get("verified_email"):
                    result = await self._send_via_email(
                        subscriber["id"],
                        subscriber["email"],
                        subscriber.get("name", "Friend"),
                        devotional
                    )
                    if result.get("success"):
                        stats["email_sent"] += 1
                        await self._update_subscription_sent(
                            subscriber["id"],
                            str(devotional["_id"])
                        )
                    else:
                        stats["email_failed"] += 1
                        logger.error(f"Failed to send email to {subscriber['email']}: {result.get('error')}")

                # Send via WhatsApp if subscribed
                if subscriber.get("whatsapp") and subscriber.get("verified_whatsapp"):
                    result = await self._send_via_whatsapp(
                        subscriber["id"],
                        subscriber["whatsapp"],
                        subscriber.get("name", "Friend"),
                        devotional
                    )
                    if result.get("success"):
                        stats["whatsapp_sent"] += 1
                        await self._update_subscription_sent(
                            subscriber["id"],
                            str(devotional["_id"])
                        )
                    else:
                        stats["whatsapp_failed"] += 1
                        logger.error(f"Failed to send WhatsApp to {subscriber['whatsapp']}: {result.get('error')}")

                # Track Facebook group preference (they join manually)
                if subscriber.get("facebook_group"):
                    stats["facebook_notified"] += 1
                    # Log that they should see it in the group
                    await self._log_facebook_notification(subscriber["id"], str(devotional["_id"]))

            except Exception as e:
                logger.error(f"Error sending to subscriber {subscriber.get('id')}: {e}")

        # Log drip feed run
        await self._log_drip_feed_run(devotional["_id"], stats)

        logger.info(
            f"Drip feed completed: {stats['email_sent']} emails, "
            f"{stats['whatsapp_sent']} WhatsApp, {stats['facebook_notified']} Facebook"
        )

        return {
            "success": True,
            "devotional_id": str(devotional["_id"]),
            "devotional_title": devotional.get("title", ""),
            "stats": stats,
        }

    async def send_custom_content_to_subscribers(
        self,
        content: Dict[str, Any],
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send custom content to subscribers (for manual drip feed).

        Args:
            content: Content to send (title, body, link, etc.)
            channel: Filter by channel (email, whatsapp, facebook)

        Returns:
            Dict with delivery statistics
        """
        subscribers = await self._get_active_subscribers(channel=channel)

        stats = {
            "email_sent": 0,
            "email_failed": 0,
            "whatsapp_sent": 0,
            "whatsapp_failed": 0,
            "facebook_notified": 0,
        }

        for subscriber in subscribers:
            try:
                if subscriber.get("email") and subscriber.get("verified_email"):
                    result = await self._send_custom_email(
                        subscriber["id"],
                        subscriber["email"],
                        subscriber.get("name", "Friend"),
                        content
                    )
                    if result.get("success"):
                        stats["email_sent"] += 1
                    else:
                        stats["email_failed"] += 1

                if subscriber.get("whatsapp") and subscriber.get("verified_whatsapp"):
                    result = await self._send_custom_whatsapp(
                        subscriber["id"],
                        subscriber["whatsapp"],
                        subscriber.get("name", "Friend"),
                        content
                    )
                    if result.get("success"):
                        stats["whatsapp_sent"] += 1
                    else:
                        stats["whatsapp_failed"] += 1

                if subscriber.get("facebook_group"):
                    stats["facebook_notified"] += 1

            except Exception as e:
                logger.error(f"Error sending custom content to subscriber {subscriber.get('id')}: {e}")

        return {
            "success": True,
            "stats": stats,
        }

    async def _get_active_subscribers(self, channel: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active subscribers, optionally filtered by channel."""
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
                "verified_email": sub.get("verified_email", False),
                "verified_whatsapp": sub.get("verified_whatsapp", False),
                "preferences": sub.get("preferences", {}),
            })

        return subscribers

    async def _send_via_email(
        self,
        subscriber_id: str,
        email: str,
        name: str,
        devotional: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send devotional via email."""
        try:
            from apps.shared.services.unified_email_service import get_email_service

            email_service = get_email_service()

            # Get devotional URL
            devotional_url = f"{settings.FRONTEND_URL}/devotional/{devotional['_id']}"

            # Get unsubscribe token
            subscription = await self.subscriptions_collection.find_one(
                {"_id": ObjectId(subscriber_id)}
            )
            unsubscribe_token = subscription.get("unsubscribe_token", "")
            unsubscribe_url = f"{settings.FRONTEND_URL}/subscriptions/unsubscribe?token={unsubscribe_token}"

            # Format devotional content
            title = devotional.get("title", "Daily Devotional")
            excerpt = devotional.get("excerpt", "")
            if not excerpt and devotional.get("content"):
                # Extract first paragraph
                content_blocks = devotional.get("content", [])
                for block in content_blocks:
                    if block.get("type") == "paragraph":
                        excerpt = block.get("content", "")[:200]
                        break

            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>{title}</title>
            </head>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; line-height: 1.6;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #4CAF50;">FreshManna</h1>
                    <p style="color: #666;">Daily Devotional</p>
                </div>
                <div style="background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #333; margin-top: 0;">{title}</h2>
                    {f'<p style="color: #666; font-style: italic;">{excerpt}</p>' if excerpt else ''}
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{devotional_url}"
                           style="display: inline-block; background-color: #4CAF50; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                            Read Full Devotional
                        </a>
                    </div>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 25px 0;">
                    <p style="font-size: 12px; color: #999; text-align: center;">
                        <a href="{unsubscribe_url}" style="color: #999;">Unsubscribe</a>
                    </p>
                </div>
            </body>
            </html>
            """

            text_body = f"""
FreshManna - Daily Devotional

{title}

{excerpt if excerpt else ''}

Read full devotional: {devotional_url}

---
Unsubscribe: {unsubscribe_url}
"""

            result = await email_service.send_email(
                to=email,
                subject=f"FreshManna Daily Devotional: {title}",
                body=text_body,
                html_body=html_body,
                from_email="noreply@ailabsafrica.com",
                from_name="FreshManna"
            )

            return result

        except Exception as e:
            logger.error(f"Error sending email to {email}: {e}")
            return {"success": False, "error": str(e)}

    async def _send_via_whatsapp(
        self,
        subscriber_id: str,
        whatsapp: str,
        name: str,
        devotional: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send devotional via WhatsApp."""
        try:
            from twilio.rest import Client as TwilioClient
            from twilio.base.exceptions import TwilioRestException

            # Check if Twilio is configured
            if not hasattr(settings, "TWILIO_ACCOUNT_SID") or not settings.TWILIO_ACCOUNT_SID:
                return {
                    "success": False,
                    "error": "Twilio not configured",
                    "provider": "twilio"
                }

            # Initialize Twilio client
            twilio_client = TwilioClient(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
            from_number = settings.TWILIO_WHATSAPP_NUMBER if hasattr(settings, "TWILIO_WHATSAPP_NUMBER") else None

            if not from_number:
                return {
                    "success": False,
                    "error": "Twilio WhatsApp number not configured",
                    "provider": "twilio"
                }

            devotional_url = f"{settings.FRONTEND_URL}/devotional/{devotional['_id']}"
            title = devotional.get("title", "Daily Devotional")
            excerpt = devotional.get("excerpt", "")
            if not excerpt and devotional.get("content"):
                content_blocks = devotional.get("content", [])
                for block in content_blocks:
                    if block.get("type") == "paragraph":
                        excerpt = block.get("content", "")[:300]
                        break

            excerpt_text = excerpt if excerpt else "Read today's devotional"
            message = f"""🙏 FreshManna Daily Devotional

*{title}*

{excerpt_text}

Read full: {devotional_url}

---
Reply STOP to unsubscribe"""

            # Ensure phone number has 'whatsapp:' prefix
            to_phone = whatsapp if whatsapp.startswith("whatsapp:") else f"whatsapp:{whatsapp}"

            # Send WhatsApp via Twilio
            twilio_message = twilio_client.messages.create(
                to=to_phone,
                from_=from_number,
                body=message
            )

            return {
                "success": True,
                "channel": "whatsapp",
                "to": to_phone,
                "message_sid": twilio_message.sid,
                "status": twilio_message.status,
                "provider": "twilio"
            }

        except TwilioRestException as e:
            logger.error(f"Twilio error sending WhatsApp to {whatsapp}: {e.code} - {e.msg}")
            return {
                "success": False,
                "error": f"Twilio error {e.code}: {e.msg}",
                "provider": "twilio"
            }
        except Exception as e:
            logger.error(f"Error sending WhatsApp to {whatsapp}: {e}")
            return {"success": False, "error": str(e), "provider": "twilio"}

    async def _send_custom_email(
        self,
        subscriber_id: str,
        email: str,
        name: str,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send custom content via email."""
        try:
            from apps.shared.services.unified_email_service import get_email_service

            email_service = get_email_service()

            title = content.get("title", "FreshManna Update")
            body = content.get("body", "")
            link = content.get("link", settings.FRONTEND_URL)

            html_body = f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #4CAF50;">FreshManna</h1>
                <h2>{title}</h2>
                <div>{body}</div>
                {f'<p><a href="{link}">Learn More</a></p>' if link else ''}
            </body>
            </html>
            """

            result = await email_service.send_email(
                to=email,
                subject=title,
                body=body,
                html_body=html_body,
                from_email="noreply@ailabsafrica.com",
                from_name="FreshManna"
            )

            return result

        except Exception as e:
            logger.error(f"Error sending custom email: {e}")
            return {"success": False, "error": str(e)}

    async def _send_custom_whatsapp(
        self,
        subscriber_id: str,
        whatsapp: str,
        name: str,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send custom content via WhatsApp."""
        try:
            from twilio.rest import Client as TwilioClient
            from twilio.base.exceptions import TwilioRestException

            # Check if Twilio is configured
            if not hasattr(settings, "TWILIO_ACCOUNT_SID") or not settings.TWILIO_ACCOUNT_SID:
                return {
                    "success": False,
                    "error": "Twilio not configured",
                    "provider": "twilio"
                }

            # Initialize Twilio client
            twilio_client = TwilioClient(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
            from_number = settings.TWILIO_WHATSAPP_NUMBER if hasattr(settings, "TWILIO_WHATSAPP_NUMBER") else None

            if not from_number:
                return {
                    "success": False,
                    "error": "Twilio WhatsApp number not configured",
                    "provider": "twilio"
                }

            title = content.get("title", "FreshManna Update")
            body = content.get("body", "")
            link = content.get("link", "")

            message = f"""🙏 FreshManna

*{title}*

{body}

{f'Learn more: {link}' if link else ''}

---
Reply STOP to unsubscribe"""

            # Ensure phone number has 'whatsapp:' prefix
            to_phone = whatsapp if whatsapp.startswith("whatsapp:") else f"whatsapp:{whatsapp}"

            # Send WhatsApp via Twilio
            twilio_message = twilio_client.messages.create(
                to=to_phone,
                from_=from_number,
                body=message
            )

            return {
                "success": True,
                "channel": "whatsapp",
                "to": to_phone,
                "message_sid": twilio_message.sid,
                "status": twilio_message.status,
                "provider": "twilio"
            }

        except TwilioRestException as e:
            logger.error(f"Twilio error sending custom WhatsApp: {e.code} - {e.msg}")
            return {
                "success": False,
                "error": f"Twilio error {e.code}: {e.msg}",
                "provider": "twilio"
            }
        except Exception as e:
            logger.error(f"Error sending custom WhatsApp: {e}")
            return {"success": False, "error": str(e), "provider": "twilio"}

    async def _update_subscription_sent(self, subscriber_id: str, content_id: str) -> None:
        """Update subscription with last sent information."""
        await self.subscriptions_collection.update_one(
            {"_id": ObjectId(subscriber_id)},
            {
                "$set": {
                    "last_sent_at": datetime.utcnow(),
                    "last_sent_content_id": content_id,
                },
                "$inc": {"total_sent": 1},
            }
        )

    async def _log_facebook_notification(self, subscriber_id: str, content_id: str) -> None:
        """Log Facebook group notification (they see it in the group)."""
        await self.drip_feed_log_collection.insert_one({
            "subscriber_id": ObjectId(subscriber_id),
            "content_id": content_id,
            "channel": "facebook",
            "sent_at": datetime.utcnow(),
            "status": "notified",
        })

    async def _log_drip_feed_run(self, devotional_id: ObjectId, stats: Dict[str, Any]) -> None:
        """Log drip feed run statistics."""
        await self.drip_feed_log_collection.insert_one({
            "devotional_id": devotional_id,
            "run_at": datetime.utcnow(),
            "stats": stats,
            "type": "daily_devotional",
        })


# Global service instance
_drip_feed_service: Optional[DripFeedService] = None


def get_drip_feed_service() -> DripFeedService:
    """Get or create drip feed service instance."""
    global _drip_feed_service
    if _drip_feed_service is None:
        _drip_feed_service = DripFeedService()
    return _drip_feed_service

