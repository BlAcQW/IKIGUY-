"""
Settings service for managing platform configuration.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from app.db.mongodb import get_database
from app.models.settings import (
    PlatformSettings,
    PlatformSettingsUpdate,
    EmailSettings,
    NotificationSettings,
    ContentModerationSettings,
    UserManagementSettings,
)


class SettingsService:
    """Service for platform settings management."""

    def __init__(self):
        self.db = get_database()
        self.settings_collection = self.db.settings

    async def get_settings(self) -> PlatformSettings:
        """
        Get current platform settings.

        Returns:
            PlatformSettings: Current platform settings

        Raises:
            ValueError: If settings not found (will create default settings)
        """
        settings_doc = await self.settings_collection.find_one({"_id": "platform_settings"})

        if not settings_doc:
            # Create default settings
            default_settings = self._get_default_settings()
            await self.settings_collection.insert_one(
                {
                    "_id": "platform_settings",
                    **default_settings.dict(),
                }
            )
            return default_settings

        # Remove MongoDB _id field
        settings_doc.pop("_id", None)
        return PlatformSettings(**settings_doc)

    async def update_settings(
        self, settings_update: PlatformSettingsUpdate, admin_user_id: str
    ) -> PlatformSettings:
        """
        Update platform settings.

        Args:
            settings_update: Settings to update
            admin_user_id: ID of admin user making the update

        Returns:
            PlatformSettings: Updated settings

        Raises:
            ValueError: If update fails
        """
        # Get current settings
        current_settings = await self.get_settings()

        # Prepare update data (only update fields that are provided)
        update_data = {}

        # Update platform info fields
        if settings_update.platform_name is not None:
            update_data["platform_name"] = settings_update.platform_name
        if settings_update.platform_description is not None:
            update_data["platform_description"] = settings_update.platform_description
        if settings_update.platform_logo_url is not None:
            update_data["platform_logo_url"] = settings_update.platform_logo_url
        if settings_update.support_email is not None:
            update_data["support_email"] = settings_update.support_email
        if settings_update.contact_phone is not None:
            update_data["contact_phone"] = settings_update.contact_phone

        # Update feature flags
        if settings_update.enable_ai_features is not None:
            update_data["enable_ai_features"] = settings_update.enable_ai_features
        if settings_update.enable_audio_devotionals is not None:
            update_data["enable_audio_devotionals"] = settings_update.enable_audio_devotionals
        if settings_update.enable_comments is not None:
            update_data["enable_comments"] = settings_update.enable_comments
        if settings_update.enable_likes is not None:
            update_data["enable_likes"] = settings_update.enable_likes
        if settings_update.enable_sharing is not None:
            update_data["enable_sharing"] = settings_update.enable_sharing

        # Update nested settings
        if settings_update.email is not None:
            update_data["email"] = settings_update.email.dict()
        if settings_update.notifications is not None:
            update_data["notifications"] = settings_update.notifications.dict()
        if settings_update.moderation is not None:
            update_data["moderation"] = settings_update.moderation.dict()
        if settings_update.users is not None:
            update_data["users"] = settings_update.users.dict()

        # Add metadata
        update_data["updated_at"] = datetime.utcnow()
        update_data["updated_by"] = admin_user_id

        # Update in database
        result = await self.settings_collection.update_one(
            {"_id": "platform_settings"},
            {"$set": update_data},
        )

        if result.modified_count == 0 and result.matched_count == 0:
            raise ValueError("Failed to update settings")

        # Return updated settings
        return await self.get_settings()

    async def reset_to_defaults(self, admin_user_id: str) -> PlatformSettings:
        """
        Reset settings to default values.

        Args:
            admin_user_id: ID of admin user performing the reset

        Returns:
            PlatformSettings: Default settings
        """
        default_settings = self._get_default_settings()
        default_settings.updated_by = admin_user_id
        default_settings.updated_at = datetime.utcnow()

        await self.settings_collection.update_one(
            {"_id": "platform_settings"},
            {"$set": default_settings.dict()},
            upsert=True,
        )

        return default_settings

    def _get_default_settings(self) -> PlatformSettings:
        """
        Get default platform settings.

        Returns:
            PlatformSettings: Default settings
        """
        return PlatformSettings(
            platform_name="FreshManna",
            platform_description="Daily devotionals for spiritual growth",
            platform_logo_url=None,
            support_email="support@freshmanna.com",
            contact_phone=None,
            enable_ai_features=True,
            enable_audio_devotionals=True,
            enable_comments=True,
            enable_likes=True,
            enable_sharing=True,
            email=EmailSettings(
                smtp_host="smtp.gmail.com",
                smtp_port=587,
                smtp_username="noreply@freshmanna.com",
                smtp_password="changeme",  # Should be updated
                smtp_use_tls=True,
                from_email="noreply@freshmanna.com",
                from_name="FreshManna",
            ),
            notifications=NotificationSettings(
                enable_email_notifications=True,
                enable_push_notifications=True,
                enable_daily_devotional_reminders=True,
                reminder_time="08:00",
                enable_comment_notifications=True,
                enable_like_notifications=True,
                enable_subscription_drip_feed=True,
                subscription_drip_feed_time="08:00",
                subscription_drip_feed_timezone="UTC",
            ),
            moderation=ContentModerationSettings(
                auto_approve_devotionals=False,
                require_pastor_verification=True,
                enable_profanity_filter=True,
                enable_spam_detection=True,
                min_devotional_length=100,
                max_devotional_length=5000,
            ),
            users=UserManagementSettings(
                allow_public_signup=True,
                require_email_verification=True,
                allow_pastor_self_registration=False,
                auto_approve_pastors=False,
                max_failed_login_attempts=5,
                account_lockout_duration_minutes=30,
            ),
        )
