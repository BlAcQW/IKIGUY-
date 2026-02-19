"""
Default Organization Initialization.

Creates the default "AI Labs Ltd." organization if it doesn't exist,
and ensures all universal admins are added as organization admins.

This module is idempotent and safe to run on every app startup.
"""

import logging
from typing import Optional
from apps.shared.models import OrganizationCreate, OrganizationRole
from apps.shared.services.organization_service import get_organization_service

logger = logging.getLogger(__name__)

# Default organization details
DEFAULT_ORG_NAME = "ai-labs-ltd"
DEFAULT_ORG_DISPLAY_NAME = "AI Labs Ltd."
DEFAULT_ORG_DESCRIPTION = "Default organization for AI Labs Africa"
DEFAULT_ORG_INDUSTRY = "Technology"
DEFAULT_ORG_WEBSITE = "https://ailabsafrica.com"

# Default admin users (must exist in Supabase)
DEFAULT_ADMINS = [
    {
        "user_id": "65715ad2-bcfa-42aa-ab21-e0b06f19b3e4",
        "email": "alfred.anyan@gmail.com",
        "display_name": "Alfred Anyan",
    },
    {
        "user_id": "4a6252e7-3dc7-483a-92c3-59a0a814a169",
        "email": "admin@ailabsafrica.com",
        "display_name": "Admin User",
    },
    {
        "user_id": "a1d7c822-847f-40ec-9fed-cc3cd9155c06",
        "email": "user@ailabsafrica.com",
        "display_name": "Regular User",
    },
]


async def initialize_default_organization() -> Optional[str]:
    """
    Initialize the default organization "AI Labs Ltd." with universal admins.

    This function is idempotent and safe to call on every application startup.
    It will:
    1. Check if the default organization already exists
    2. Create it if it doesn't exist
    3. Ensure all default admins are added with ADMIN role
    4. Skip gracefully if already initialized

    Returns:
        str: Organization ID if created/found, None if error occurred
    """
    try:
        org_service = get_organization_service()

        # Check if default organization already exists
        existing_org = await org_service.organizations.find_one(
            {"name": DEFAULT_ORG_NAME}
        )

        if existing_org:
            org_id = existing_org.get("id")
            logger.info(
                f"✅ Default organization '{DEFAULT_ORG_DISPLAY_NAME}' already exists (ID: {org_id})"
            )

            # Ensure all admins are still members
            await _ensure_admins_are_members(org_service, org_id)

            return org_id

        # Create default organization with first admin as creator
        logger.info(f"Creating default organization '{DEFAULT_ORG_DISPLAY_NAME}'...")

        first_admin = DEFAULT_ADMINS[0]
        org_data = OrganizationCreate(
            name=DEFAULT_ORG_NAME,
            display_name=DEFAULT_ORG_DISPLAY_NAME,
            description=DEFAULT_ORG_DESCRIPTION,
            industry=DEFAULT_ORG_INDUSTRY,
            website=DEFAULT_ORG_WEBSITE,
        )

        organization = await org_service.create_organization(
            org_data=org_data,
            creator_user_id=first_admin["user_id"],
            creator_email=first_admin["email"],
        )

        logger.info(
            f"✅ Created default organization '{DEFAULT_ORG_DISPLAY_NAME}' (ID: {organization.id})"
        )

        # Add remaining admins
        for admin in DEFAULT_ADMINS[1:]:
            try:
                # Check if user already exists in organization
                existing_user = await org_service.organization_users.find_one(
                    {
                        "organization_id": organization.id,
                        "user_id": admin["user_id"],
                    }
                )

                if not existing_user:
                    await org_service.add_user_to_organization(
                        organization_id=organization.id,
                        user_id=admin["user_id"],
                        email=admin["email"],
                        role=OrganizationRole.ADMIN,
                        display_name=admin.get("display_name"),
                    )
                    logger.info(
                        f"✅ Added {admin['email']} as admin to default organization"
                    )
                else:
                    logger.info(
                        f"ℹ️  {admin['email']} already in default organization"
                    )

            except Exception as e:
                logger.warning(
                    f"⚠️  Failed to add {admin['email']} to default organization: {e}"
                )

        return organization.id

    except Exception as e:
        logger.error(f"❌ Failed to initialize default organization: {e}")
        logger.exception(e)
        return None


async def _ensure_admins_are_members(org_service, org_id: str):
    """
    Ensure all default admins are members of the organization.

    Args:
        org_service: Organization service instance
        org_id: Organization ID to check
    """
    for admin in DEFAULT_ADMINS:
        try:
            existing_user = await org_service.organization_users.find_one(
                {"organization_id": org_id, "user_id": admin["user_id"]}
            )

            if not existing_user:
                await org_service.add_user_to_organization(
                    organization_id=org_id,
                    user_id=admin["user_id"],
                    email=admin["email"],
                    role=OrganizationRole.ADMIN,
                    display_name=admin.get("display_name"),
                )
                logger.info(
                    f"✅ Added missing admin {admin['email']} to default organization"
                )
            else:
                # Ensure they have ADMIN role
                if existing_user.get("role") != OrganizationRole.ADMIN:
                    await org_service.update_user_role(
                        organization_id=org_id,
                        user_id=admin["user_id"],
                        role=OrganizationRole.ADMIN,
                    )
                    logger.info(
                        f"✅ Updated {admin['email']} role to ADMIN in default organization"
                    )

        except Exception as e:
            logger.warning(
                f"⚠️  Failed to ensure {admin['email']} is admin: {e}"
            )
