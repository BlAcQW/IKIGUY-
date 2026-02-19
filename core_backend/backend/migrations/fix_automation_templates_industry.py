"""
Migration to fix automation_templates collection industry field.

This migration:
1. Examines the current 'industry' field in automation_templates
2. Creates separate 'industry_id' and 'industry_name' fields
3. Populates these fields based on the existing 'industry' field content
4. Removes the old 'industry' field after migration
"""

import logging
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from ..mongo import get_collection


logger = logging.getLogger(__name__)


# Industry mapping for standardization
INDUSTRY_MAPPINGS = {
    # Industry Names to IDs
    "Healthcare": "healthcare",
    "Insurance": "insurance",
    "Financial": "financial",
    "Finance": "financial",
    "Retail": "retail",
    "Education": "education",
    "Real Estate": "real_estate",
    "Legal": "legal",
    "Hospitality": "hospitality",
    "Manufacturing": "manufacturing",
    "Automotive": "automotive",
    "Government": "government",
    "Logistics": "logistics",
    "Professional Services": "professional_services",
    "Telecom": "telecom",
    "Utilities": "utilities",
    "Generic": "generic",
    "Workflow": "workflow",

    # Handle existing IDs
    "healthcare": "healthcare",
    "insurance": "insurance",
    "financial": "financial",
    "retail": "retail",
    "education": "education",
    "real_estate": "real_estate",
    "legal": "legal",
    "hospitality": "hospitality",
    "manufacturing": "manufacturing",
    "automotive": "automotive",
    "government": "government",
    "logistics": "logistics",
    "professional_services": "professional_services",
    "telecom": "telecom",
    "utilities": "utilities",
    "generic": "generic",
    "workflow": "workflow"
}

# Reverse mapping for getting display names
ID_TO_NAME_MAPPINGS = {
    "healthcare": "Healthcare",
    "insurance": "Insurance",
    "financial": "Financial",
    "retail": "Retail",
    "education": "Education",
    "real_estate": "Real Estate",
    "legal": "Legal",
    "hospitality": "Hospitality",
    "manufacturing": "Manufacturing",
    "automotive": "Automotive",
    "government": "Government",
    "logistics": "Logistics",
    "professional_services": "Professional Services",
    "telecom": "Telecom",
    "utilities": "Utilities",
    "generic": "Generic",
    "workflow": "Workflow"
}


def normalize_industry_value(industry_value: str) -> Dict[str, str]:
    """
    Normalize an industry value to industry_id and industry_name.

    Args:
        industry_value: The current industry field value

    Returns:
        Dict with 'industry_id' and 'industry_name' keys
    """
    if not industry_value:
        return {"industry_id": "generic", "industry_name": "Generic"}

    # Clean the value
    cleaned_value = industry_value.strip()

    # Check if it's already an ID (lowercase, underscores)
    if cleaned_value.lower() in INDUSTRY_MAPPINGS:
        industry_id = INDUSTRY_MAPPINGS[cleaned_value.lower()]
        industry_name = ID_TO_NAME_MAPPINGS.get(industry_id, cleaned_value.title())
        return {"industry_id": industry_id, "industry_name": industry_name}

    # Check if it's a display name
    if cleaned_value in INDUSTRY_MAPPINGS:
        industry_id = INDUSTRY_MAPPINGS[cleaned_value]
        industry_name = cleaned_value
        return {"industry_id": industry_id, "industry_name": industry_name}

    # Try case-insensitive matching
    for key, value in INDUSTRY_MAPPINGS.items():
        if key.lower() == cleaned_value.lower():
            industry_id = value
            industry_name = ID_TO_NAME_MAPPINGS.get(industry_id, key)
            return {"industry_id": industry_id, "industry_name": industry_name}

    # Handle special cases
    if "health" in cleaned_value.lower():
        return {"industry_id": "healthcare", "industry_name": "Healthcare"}
    elif "bank" in cleaned_value.lower() or "financ" in cleaned_value.lower():
        return {"industry_id": "financial", "industry_name": "Financial"}
    elif "insur" in cleaned_value.lower():
        return {"industry_id": "insurance", "industry_name": "Insurance"}
    elif "retail" in cleaned_value.lower() or "store" in cleaned_value.lower():
        return {"industry_id": "retail", "industry_name": "Retail"}
    elif "school" in cleaned_value.lower() or "educat" in cleaned_value.lower():
        return {"industry_id": "education", "industry_name": "Education"}
    elif "hotel" in cleaned_value.lower() or "restaurant" in cleaned_value.lower():
        return {"industry_id": "hospitality", "industry_name": "Hospitality"}
    elif "manufact" in cleaned_value.lower() or "factor" in cleaned_value.lower():
        return {"industry_id": "manufacturing", "industry_name": "Manufacturing"}
    elif "car" in cleaned_value.lower() or "auto" in cleaned_value.lower():
        return {"industry_id": "automotive", "industry_name": "Automotive"}
    elif "gov" in cleaned_value.lower() or "public" in cleaned_value.lower():
        return {"industry_id": "government", "industry_name": "Government"}
    elif "ship" in cleaned_value.lower() or "transport" in cleaned_value.lower():
        return {"industry_id": "logistics", "industry_name": "Logistics"}
    elif "law" in cleaned_value.lower() or "legal" in cleaned_value.lower():
        return {"industry_id": "legal", "industry_name": "Legal"}
    elif "real" in cleaned_value.lower() and "estate" in cleaned_value.lower():
        return {"industry_id": "real_estate", "industry_name": "Real Estate"}
    elif "telecom" in cleaned_value.lower() or "communication" in cleaned_value.lower():
        return {"industry_id": "telecom", "industry_name": "Telecom"}
    elif "utilit" in cleaned_value.lower() or "energy" in cleaned_value.lower():
        return {"industry_id": "utilities", "industry_name": "Utilities"}

    # Default to generic if no match found
    logger.warning(f"Could not map industry value '{cleaned_value}' to known industry. Using generic.")
    return {"industry_id": "generic", "industry_name": "Generic"}


async def migrate_automation_templates_industry() -> Dict[str, Any]:
    """
    Migrate automation_templates collection to use industry_id and industry_name fields.

    Returns:
        Migration result with statistics
    """
    try:
        templates_collection = get_collection("automation_templates")

        # Get all templates
        templates = list(templates_collection.find({}))

        if not templates:
            return {
                "success": True,
                "message": "No templates found to migrate",
                "migrated_count": 0,
                "total_count": 0
            }

        migrated_count = 0
        errors = []
        industry_stats = {}

        logger.info(f"Starting migration of {len(templates)} automation templates")

        for template in templates:
            try:
                template_id = template.get("_id")
                current_industry = template.get("industry")

                # Check if already migrated
                if template.get("industry_id") and template.get("industry_name"):
                    logger.info(f"Template {template_id} already migrated, skipping")
                    continue

                # Normalize industry value
                normalized = normalize_industry_value(current_industry)

                # Update template
                update_fields = {
                    "industry_id": normalized["industry_id"],
                    "industry_name": normalized["industry_name"],
                    "migrated_at": datetime.now(timezone.utc)
                }

                # Update in database
                result = templates_collection.update_one(
                    {"_id": template_id},
                    {"$set": update_fields}
                )

                if result.modified_count > 0:
                    migrated_count += 1

                    # Track industry statistics
                    industry_id = normalized["industry_id"]
                    if industry_id not in industry_stats:
                        industry_stats[industry_id] = 0
                    industry_stats[industry_id] += 1

                    logger.info(
                        f"Migrated template {template_id}: "
                        f"'{current_industry}' -> '{normalized['industry_id']}' / '{normalized['industry_name']}'"
                    )
                else:
                    logger.warning(f"Failed to update template {template_id}")

            except Exception as e:
                error_msg = f"Error migrating template {template.get('_id', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # After successful migration, remove old industry field
        if migrated_count > 0 and not errors:
            logger.info("Removing old 'industry' field from migrated templates")
            templates_collection.update_many(
                {"industry_id": {"$exists": True}},
                {"$unset": {"industry": ""}}
            )

        migration_result = {
            "success": True,
            "message": f"Successfully migrated {migrated_count} templates",
            "migrated_count": migrated_count,
            "total_count": len(templates),
            "industry_distribution": industry_stats,
            "errors": errors
        }

        logger.info(f"Migration completed: {migration_result}")
        return migration_result

    except Exception as e:
        error_msg = f"Migration failed: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "migrated_count": 0
        }


async def verify_migration() -> Dict[str, Any]:
    """
    Verify the migration was successful.

    Returns:
        Verification result
    """
    try:
        templates_collection = get_collection("automation_templates")

        # Count templates
        total_templates = templates_collection.count_documents({})
        migrated_templates = templates_collection.count_documents({
            "industry_id": {"$exists": True},
            "industry_name": {"$exists": True}
        })
        old_field_remaining = templates_collection.count_documents({
            "industry": {"$exists": True}
        })

        # Get industry distribution
        pipeline = [
            {"$group": {
                "_id": "$industry_id",
                "count": {"$sum": 1},
                "industry_name": {"$first": "$industry_name"}
            }},
            {"$sort": {"count": -1}}
        ]

        industry_distribution = list(templates_collection.aggregate(pipeline))

        # Get templates with missing fields
        missing_fields = list(templates_collection.find({
            "$or": [
                {"industry_id": {"$exists": False}},
                {"industry_name": {"$exists": False}}
            ]
        }, {"_id": 1, "template_name": 1, "industry": 1}))

        verification_result = {
            "total_templates": total_templates,
            "migrated_templates": migrated_templates,
            "migration_complete": migrated_templates == total_templates,
            "old_field_remaining": old_field_remaining,
            "industry_distribution": [
                {
                    "industry_id": item["_id"],
                    "industry_name": item.get("industry_name", "Unknown"),
                    "count": item["count"]
                }
                for item in industry_distribution
            ],
            "templates_missing_fields": [
                {
                    "id": str(template["_id"]),
                    "name": template.get("template_name", "Unknown"),
                    "old_industry": template.get("industry")
                }
                for template in missing_fields
            ]
        }

        logger.info(f"Migration verification: {verification_result}")
        return verification_result

    except Exception as e:
        error_msg = f"Verification failed: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}


if __name__ == "__main__":
    import asyncio

    async def main():
        print("Starting automation templates industry field migration...")

        # Run migration
        result = await migrate_automation_templates_industry()
        print(f"Migration result: {result}")

        # Verify migration
        verification = await verify_migration()
        print(f"Verification result: {verification}")

    asyncio.run(main())