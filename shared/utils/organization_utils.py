"""
Organization Utilities

Standalone utility functions for organization management that can be used
by any KasaAI application without requiring a service instance.

Usage:
    from apps.shared.utils.organization_utils import generate_org_name_sync

    unique_name = generate_org_name_sync("Action Chapel International", organizations_collection)
"""

import re
from typing import Optional


def slugify_org_name(display_name: str) -> str:
    """
    Convert a display name to a URL-safe slug.

    Args:
        display_name: The display name to convert

    Returns:
        A lowercase, URL-safe slug

    Examples:
        >>> slugify_org_name("Action Chapel International")
        'action-chapel-international'
        >>> slugify_org_name("AI Labs & Co.")
        'ai-labs-co'
    """
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', display_name.lower())
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    # Collapse multiple hyphens
    slug = re.sub(r'-+', '-', slug)
    return slug


def generate_org_name_sync(display_name: str, organizations_collection, max_attempts: int = 1000) -> str:
    """
    Generate a unique organization name synchronously (for non-async MongoDB clients).

    Args:
        display_name: The display name to convert
        organizations_collection: PyMongo collection instance
        max_attempts: Maximum number of attempts before using random suffix

    Returns:
        A unique, lowercase, URL-safe organization name

    Examples:
        >>> from pymongo import MongoClient
        >>> client = MongoClient("mongodb://localhost:27017/")
        >>> db = client.kasaai_core
        >>> unique_name = generate_org_name_sync("My Org", db.organizations)
    """
    base_name = slugify_org_name(display_name)

    # Check if name exists and make it unique
    name = base_name
    counter = 1

    while organizations_collection.find_one({"name": name}):
        # Name exists, try with suffix
        name = f"{base_name}-{counter}"
        counter += 1

        # Safety limit to prevent infinite loop
        if counter > max_attempts:
            # Use a random suffix as fallback
            import uuid
            name = f"{base_name}-{uuid.uuid4().hex[:8]}"
            break

    return name


async def generate_org_name_async(
    display_name: str,
    organizations_collection,
    max_attempts: int = 1000
) -> str:
    """
    Generate a unique organization name asynchronously (for Motor/async MongoDB clients).

    Args:
        display_name: The display name to convert
        organizations_collection: Motor AsyncIOMotorCollection instance
        max_attempts: Maximum number of attempts before using random suffix

    Returns:
        A unique, lowercase, URL-safe organization name

    Examples:
        >>> from motor.motor_asyncio import AsyncIOMotorClient
        >>> client = AsyncIOMotorClient("mongodb://localhost:27017/")
        >>> db = client.kasaai_core
        >>> unique_name = await generate_org_name_async("My Org", db.organizations)
    """
    base_name = slugify_org_name(display_name)

    # Check if name exists and make it unique
    name = base_name
    counter = 1

    while await organizations_collection.find_one({"name": name}):
        # Name exists, try with suffix
        name = f"{base_name}-{counter}"
        counter += 1

        # Safety limit to prevent infinite loop
        if counter > max_attempts:
            # Use a random suffix as fallback
            import uuid
            name = f"{base_name}-{uuid.uuid4().hex[:8]}"
            break

    return name


def validate_org_name(name: str) -> bool:
    """
    Validate that an organization name follows the required format.

    Args:
        name: Organization name to validate

    Returns:
        True if valid, False otherwise

    Rules:
        - Must be lowercase
        - Can only contain letters, numbers, and hyphens
        - Cannot start or end with hyphen
        - No consecutive hyphens

    Examples:
        >>> validate_org_name("action-chapel-international")
        True
        >>> validate_org_name("Action Chapel")
        False
        >>> validate_org_name("-invalid")
        False
    """
    if not name:
        return False

    # Check if lowercase
    if name != name.lower():
        return False

    # Check format
    pattern = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'
    return bool(re.match(pattern, name))


__all__ = [
    'slugify_org_name',
    'generate_org_name_sync',
    'generate_org_name_async',
    'validate_org_name',
]
