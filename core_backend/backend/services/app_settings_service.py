"""App settings service for managing global application configuration in MongoDB."""

import os
from typing import Optional, Dict, Any
from datetime import datetime
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from ..models import (
    AppSettings, AppSettingsCreate, AppSettingsUpdate,
    AutomationSettings, BrandingSettings
)
from .industry_service import industry_service


class MongoDBAppSettingsService:
    """MongoDB-based app settings service."""

    def __init__(self):
        """Initialize the app settings service."""
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.app_settings: Optional[Collection] = None
        self._connect()

    def _connect(self):
        """Connect to MongoDB."""
        try:
            mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
            database_name = os.getenv("MONGO_CORE_DATABASE", "kasaai_core")

            self.client = MongoClient(mongodb_url)
            self.db = self.client[database_name]
            self.app_settings = self.db["app_settings"]

            # Create indexes
            try:
                self.app_settings.create_index("deployment_name", unique=True)
                self.app_settings.create_index("is_active")
                self.app_settings.create_index("environment")
            except Exception as e:
                # Indexes might already exist
                pass

        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise

    def get_app_settings(self) -> Optional[AppSettings]:
        """Get the current active app settings.

        Returns:
            AppSettings: Current app settings if found, None otherwise.
        """
        doc = self.app_settings.find_one({"is_active": True})
        return AppSettings(**doc) if doc else None

    def create_app_settings(self, settings_data: AppSettingsCreate, creator_user_id: str) -> AppSettings:
        """Create new app settings.

        Args:
            settings_data: App settings creation data.
            creator_user_id: User ID creating the settings.

        Returns:
            AppSettings: The created settings.
        """
        # Deactivate existing settings
        self.app_settings.update_many(
            {"is_active": True},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )

        # Create new settings
        settings = AppSettings(
            deployment_name=settings_data.deployment_name,
            deployment_description=settings_data.deployment_description or "",
            environment=settings_data.environment or "production",
            automation_settings=settings_data.automation_settings or AutomationSettings(),
            branding_settings=settings_data.branding_settings or BrandingSettings(),
            created_by=creator_user_id,
            updated_by=creator_user_id
        )

        # Insert settings
        self.app_settings.insert_one(settings.model_dump())
        return settings

    def update_app_settings(self, update_data: AppSettingsUpdate, updater_user_id: str) -> Optional[AppSettings]:
        """Update the current active app settings.

        Args:
            update_data: Update data.
            updater_user_id: User ID updating the settings.

        Returns:
            AppSettings: Updated settings if found, None otherwise.
        """
        # Get current settings
        current_settings = self.get_app_settings()
        if not current_settings:
            return None

        # Prepare update data
        update_dict = {}
        for field, value in update_data.model_dump(exclude_unset=True).items():
            if value is not None:
                update_dict[field] = value

        if not update_dict:
            return current_settings

        update_dict["updated_at"] = datetime.utcnow()
        update_dict["updated_by"] = updater_user_id

        # Update settings
        result = self.app_settings.update_one(
            {"id": current_settings.id},
            {"$set": update_dict}
        )

        if result.modified_count > 0:
            return self.get_app_settings()
        return None

    def get_automation_settings(self) -> Optional[AutomationSettings]:
        """Get current automation settings.

        Returns:
            AutomationSettings: Current automation settings if found, None otherwise.
        """
        app_settings = self.get_app_settings()
        return app_settings.automation_settings if app_settings else None

    def update_automation_settings(self, automation_settings: AutomationSettings, updater_user_id: str) -> Optional[AutomationSettings]:
        """Update automation settings.

        Args:
            automation_settings: New automation settings.
            updater_user_id: User ID updating the settings.

        Returns:
            AutomationSettings: Updated automation settings if successful, None otherwise.
        """
        current_settings = self.get_app_settings()
        if not current_settings:
            return None

        # Update automation settings
        result = self.app_settings.update_one(
            {"id": current_settings.id},
            {
                "$set": {
                    "automation_settings": automation_settings.model_dump(),
                    "updated_at": datetime.utcnow(),
                    "updated_by": updater_user_id
                }
            }
        )

        if result.modified_count > 0:
            updated_settings = self.get_app_settings()
            return updated_settings.automation_settings if updated_settings else None
        return None

    def get_branding_settings(self) -> Optional[BrandingSettings]:
        """Get current branding settings.

        Returns:
            BrandingSettings: Current branding settings if found, None otherwise.
        """
        app_settings = self.get_app_settings()
        return app_settings.branding_settings if app_settings else None

    def update_branding_settings(self, branding_settings: BrandingSettings, updater_user_id: str) -> Optional[BrandingSettings]:
        """Update branding settings.

        Args:
            branding_settings: New branding settings.
            updater_user_id: User ID updating the settings.

        Returns:
            BrandingSettings: Updated branding settings if successful, None otherwise.
        """
        current_settings = self.get_app_settings()
        if not current_settings:
            return None

        # Update branding settings
        result = self.app_settings.update_one(
            {"id": current_settings.id},
            {
                "$set": {
                    "branding_settings": branding_settings.model_dump(),
                    "updated_at": datetime.utcnow(),
                    "updated_by": updater_user_id
                }
            }
        )

        if result.modified_count > 0:
            updated_settings = self.get_app_settings()
            return updated_settings.branding_settings if updated_settings else None
        return None

    def get_enabled_industries(self) -> list[str]:
        """Get list of enabled industries for automation.

        Returns:
            list[str]: List of enabled industry types.
        """
        automation_settings = self.get_automation_settings()
        return automation_settings.enabled_industries if automation_settings else []

    def get_enabled_templates(self) -> list[str]:
        """Get list of enabled automation template IDs.

        Returns:
            list[str]: List of enabled automation template IDs.
        """
        automation_settings = self.get_automation_settings()
        return automation_settings.enabled_templates if automation_settings else []

    def is_industry_enabled(self, industry: str) -> bool:
        """Check if a specific industry is enabled for automation.

        Args:
            industry: Industry name to check.

        Returns:
            bool: True if industry is enabled, False otherwise.
        """
        enabled_industries = self.get_enabled_industries()
        return industry in enabled_industries

    def is_template_enabled(self, template_id: str) -> bool:
        """Check if a specific automation template is enabled.

        Args:
            template_id: Template ID to check.

        Returns:
            bool: True if template is enabled, False otherwise.
        """
        enabled_templates = self.get_enabled_templates()
        return template_id in enabled_templates

    def get_automation_templates(self) -> list[dict]:
        """Get all automation templates from the database with industry details.

        Returns:
            list[dict]: List of automation templates with industry information resolved.
        """
        try:
            # Get automation templates collection
            automation_templates = self.db["automation_templates"]

            # Fetch all active templates
            templates = list(automation_templates.find({
                "is_active": True
            }, {
                "id": 1,
                "template_name": 1,
                "industry": 1,
                "category": 1,
                "description": 1,
                "version": 1,
                "created_at": 1,
                "updated_at": 1
            }).sort("industry", 1))

            # Resolve industry IDs to industry details
            industries_map = {industry.id: industry for industry in industry_service.list_industries()}

            for template in templates:
                industry_id = template.get("industry")
                if industry_id and industry_id in industries_map:
                    industry = industries_map[industry_id]
                    template["industry_details"] = {
                        "id": industry.id,
                        "name": industry.name,
                        "description": industry.description,
                        "icon": industry.icon,
                        "color": industry.color
                    }
                    # Keep industry field as ID for backward compatibility
                    template["industry_name"] = industry.name
                else:
                    template["industry_details"] = None
                    template["industry_name"] = "Unknown"

            return templates
        except Exception as e:
            print(f"Failed to get automation templates: {e}")
            return []

    def get_templates_by_industry(self) -> dict[str, dict]:
        """Get automation templates grouped by industry with industry details.

        Returns:
            dict[str, dict]: Templates grouped by industry with industry metadata.
        """
        templates = self.get_automation_templates()
        templates_by_industry = {}

        for template in templates:
            industry_details = template.get("industry_details")
            if industry_details:
                industry_id = industry_details["id"]
                industry_name = industry_details["name"]

                if industry_id not in templates_by_industry:
                    templates_by_industry[industry_id] = {
                        "industry": industry_details,
                        "templates": []
                    }

                templates_by_industry[industry_id]["templates"].append(template)
            else:
                # Handle templates without valid industry references
                if "unknown" not in templates_by_industry:
                    templates_by_industry["unknown"] = {
                        "industry": {
                            "id": "unknown",
                            "name": "Unknown",
                            "description": "Templates without valid industry references",
                            "icon": "QuestionMark",
                            "color": "#6b7280"
                        },
                        "templates": []
                    }
                templates_by_industry["unknown"]["templates"].append(template)

        return templates_by_industry

    def get_available_industries(self) -> list[str]:
        """Get list of all available industries from the industries collection.

        Returns:
            list[str]: List of industry IDs that have templates.
        """
        try:
            # Get all active industries that have templates
            templates = self.get_automation_templates()
            used_industry_ids = set()

            for template in templates:
                industry_id = template.get("industry")
                if industry_id:
                    used_industry_ids.add(industry_id)

            return sorted(list(used_industry_ids))
        except Exception as e:
            print(f"Failed to get available industries: {e}")
            return []

    def initialize_default_settings(self, creator_user_id: str = "system") -> AppSettings:
        """Initialize default app settings if none exist.

        Args:
            creator_user_id: User ID creating the default settings.

        Returns:
            AppSettings: Default settings.
        """
        existing_settings = self.get_app_settings()
        if existing_settings:
            return existing_settings

        # Get available industries and templates from database
        available_industries = self.get_available_industries()
        available_templates = self.get_automation_templates()
        template_ids = [template["id"] for template in available_templates]

        # Create default settings with all available industries and templates enabled
        default_automation_settings = AutomationSettings(
            enabled_industries=available_industries,
            enabled_templates=template_ids
        )

        default_branding_settings = BrandingSettings()

        default_settings_data = AppSettingsCreate(
            deployment_name="KasaAI",
            deployment_description="AI-powered voice automation platform",
            environment="production",
            automation_settings=default_automation_settings,
            branding_settings=default_branding_settings
        )

        return self.create_app_settings(default_settings_data, creator_user_id)


# Global service instance
app_settings_service = MongoDBAppSettingsService()