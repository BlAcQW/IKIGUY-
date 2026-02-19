"""Migration service for updating automation templates to use industry IDs."""

import os
from typing import Dict, Any
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from .industry_service import industry_service


class MigrationService:
    """Service for handling data migrations."""

    def __init__(self):
        """Initialize the migration service."""
        self.client = None
        self.db = None
        self.automation_templates = None
        self._connect()

    def _connect(self):
        """Connect to MongoDB."""
        try:
            mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
            database_name = os.getenv("MONGO_CORE_DATABASE", "kasaai_core")

            self.client = MongoClient(mongodb_url)
            self.db = self.client[database_name]
            self.automation_templates = self.db["automation_templates"]

        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise

    def migrate_automation_templates_to_industry_ids(self) -> Dict[str, Any]:
        """Migrate automation templates to use industry IDs instead of names.

        Returns:
            Dict with migration results.
        """
        # Get all industries to create name -> ID mapping
        industries = industry_service.list_industries()
        industry_name_to_id = {industry.name: industry.id for industry in industries}

        print(f"Found {len(industries)} industries for mapping")
        print("Industry mappings:", industry_name_to_id)

        # Get all automation templates
        templates = list(self.automation_templates.find({}))
        print(f"Found {len(templates)} automation templates to migrate")

        migration_results = {
            "total_templates": len(templates),
            "successful_migrations": 0,
            "failed_migrations": 0,
            "errors": [],
            "mapping_issues": []
        }

        for template in templates:
            try:
                template_id = template.get("id") or template.get("_id")
                current_industry = template.get("industry")

                if not current_industry:
                    migration_results["mapping_issues"].append({
                        "template_id": str(template_id),
                        "issue": "No industry field found"
                    })
                    continue

                # Check if industry is already an ID (UUID format)
                if len(current_industry) == 36 and "-" in current_industry:
                    print(f"Template {template_id} already has industry ID: {current_industry}")
                    continue

                # Map industry name to ID
                industry_id = industry_name_to_id.get(current_industry)

                if not industry_id:
                    migration_results["mapping_issues"].append({
                        "template_id": str(template_id),
                        "current_industry": current_industry,
                        "issue": f"No industry ID found for name '{current_industry}'"
                    })
                    continue

                # Update the template
                result = self.automation_templates.update_one(
                    {"id": template.get("id")} if template.get("id") else {"_id": template.get("_id")},
                    {
                        "$set": {
                            "industry_id": industry_id,
                            "industry_name": current_industry,  # Keep original name for reference
                            "industry": industry_id  # Update industry field to use ID
                        }
                    }
                )

                if result.modified_count > 0:
                    migration_results["successful_migrations"] += 1
                    print(f"Migrated template {template_id}: {current_industry} -> {industry_id}")
                else:
                    migration_results["failed_migrations"] += 1
                    migration_results["errors"].append({
                        "template_id": str(template_id),
                        "error": "Update operation did not modify document"
                    })

            except Exception as e:
                migration_results["failed_migrations"] += 1
                migration_results["errors"].append({
                    "template_id": str(template_id) if template_id else "unknown",
                    "error": str(e)
                })
                print(f"Error migrating template {template_id}: {e}")

        print(f"Migration completed: {migration_results['successful_migrations']} successful, "
              f"{migration_results['failed_migrations']} failed")

        return migration_results

    def rollback_automation_templates_migration(self) -> Dict[str, Any]:
        """Rollback automation templates to use industry names instead of IDs.

        Returns:
            Dict with rollback results.
        """
        # Get all automation templates with industry_name field
        templates = list(self.automation_templates.find({"industry_name": {"$exists": True}}))
        print(f"Found {len(templates)} automation templates to rollback")

        rollback_results = {
            "total_templates": len(templates),
            "successful_rollbacks": 0,
            "failed_rollbacks": 0,
            "errors": []
        }

        for template in templates:
            try:
                template_id = template.get("id") or template.get("_id")
                industry_name = template.get("industry_name")

                if not industry_name:
                    continue

                # Restore industry field to use name
                result = self.automation_templates.update_one(
                    {"id": template.get("id")} if template.get("id") else {"_id": template.get("_id")},
                    {
                        "$set": {"industry": industry_name},
                        "$unset": {"industry_id": "", "industry_name": ""}
                    }
                )

                if result.modified_count > 0:
                    rollback_results["successful_rollbacks"] += 1
                    print(f"Rolled back template {template_id}: ID -> {industry_name}")
                else:
                    rollback_results["failed_rollbacks"] += 1

            except Exception as e:
                rollback_results["failed_rollbacks"] += 1
                rollback_results["errors"].append({
                    "template_id": str(template_id) if template_id else "unknown",
                    "error": str(e)
                })

        return rollback_results


# Global service instance
migration_service = MigrationService()