#!/usr/bin/env python3
"""
Migration script to ensure all existing users have organizations.
Creates default organizations for users who don't have one.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.core_backend.backend.services.organization_service import organization_service
from apps.core_backend.backend.models import OrganizationCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_supabase_users():
    """Get all users from Supabase auth"""
    try:
        from supabase import create_client, Client

        url = os.getenv("DEMO_SUPABASE_URL")
        key = os.getenv("DEMO_SUPABASE_SUPABASE_KEY")

        if not url or not key:
            logger.error("Missing Supabase configuration")
            return []

        supabase: Client = create_client(url, key)
        query = supabase.auth.admin.list_users()

        if not query:
            return []

        return query.users if hasattr(query, 'users') else []

    except Exception as e:
        logger.error(f"Error fetching users from Supabase: {str(e)}")
        return []

def migrate_users_to_organizations():
    """Create default organizations for users who don't have one"""

    logger.info("Starting user-to-organization migration...")

    # Get all users from Supabase
    supabase_users = get_supabase_users()

    if not supabase_users:
        logger.warning("No users found in Supabase")
        return

    users_without_orgs = []
    users_with_orgs = []

    for user in supabase_users:
        # Check if user already has an organization
        user_orgs = organization_service.get_organizations_for_user(user.id)

        if not user_orgs:
            users_without_orgs.append(user)
        else:
            users_with_orgs.append(user)

    logger.info(f"Found {len(supabase_users)} total users:")
    logger.info(f"  - {len(users_with_orgs)} users with organizations")
    logger.info(f"  - {len(users_without_orgs)} users without organizations")

    if not users_without_orgs:
        logger.info("All users already have organizations. Migration complete!")
        return

    # Create organizations for users without them
    created_orgs = 0

    for user in users_without_orgs:
        try:
            user_name = user.user_metadata.get('name') or user.email.split('@')[0]

            # Create default organization
            default_org = OrganizationCreate(
                name=f"{user_name}'s Organization",
                display_name=f"{user_name}'s Organization",
                description="Default organization created during migration"
            )

            organization = organization_service.create_organization(
                default_org,
                user.id,
                user.email
            )

            logger.info(f"✅ Created organization '{organization.display_name}' for user {user.email}")
            created_orgs += 1

        except Exception as e:
            logger.error(f"❌ Failed to create organization for user {user.email}: {str(e)}")

    logger.info(f"Migration complete! Created {created_orgs} organizations.")

if __name__ == "__main__":
    migrate_users_to_organizations()