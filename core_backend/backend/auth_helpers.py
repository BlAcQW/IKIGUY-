"""
Authentication Helper Functions

Provides utility functions for authorization checks including universal_admin support.
"""

import logging
from typing import Dict, Any, Tuple
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def check_universal_admin_or_owner(
    current_user: Dict[str, Any],
    resource_user_id: str,
    resource_name: str = "resource"
) -> Tuple[bool, str]:
    """
    Check if the current user is a universal admin or owns the resource.

    Args:
        current_user: Current user dict from JWT token
        resource_user_id: User ID who owns the resource
        resource_name: Name of the resource for error messages

    Returns:
        Tuple of (is_authorized, user_id)

    Raises:
        HTTPException: If user is not authorized
    """
    user_id = current_user.get("id") or current_user.get("sub")
    is_universal_admin = current_user.get("is_universal_admin", False)

    # Universal admins can access any resource
    if is_universal_admin:
        logger.info(f"Universal admin {user_id} accessing {resource_name} owned by {resource_user_id}")
        return (True, user_id)

    # Regular users can only access their own resources
    if user_id == resource_user_id:
        return (True, user_id)

    # Not authorized
    raise HTTPException(
        status_code=404,
        detail=f"{resource_name.capitalize()} not found or you don't have permission to access it"
    )


def build_query_with_admin_support(
    current_user: Dict[str, Any],
    base_query: Dict[str, Any] = None
) -> Tuple[Dict[str, Any], bool, str]:
    """
    Build MongoDB query with universal_admin support.

    Args:
        current_user: Current user dict from JWT token
        base_query: Base query dict to add user filter to

    Returns:
        Tuple of (query, is_universal_admin, user_id)
    """
    user_id = current_user.get("id") or current_user.get("sub")
    is_universal_admin = current_user.get("is_universal_admin", False)

    query = base_query.copy() if base_query else {}

    # Regular users only see their own resources
    if not is_universal_admin:
        query["user_id"] = user_id

    return (query, is_universal_admin, user_id)


def log_admin_action(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    details: Dict[str, Any] = None
):
    """
    Log universal admin actions for audit trail.

    Args:
        user_id: Universal admin user ID
        action: Action performed (create, read, update, delete)
        resource_type: Type of resource (automation, campaign, etc.)
        resource_id: ID of the resource
        details: Additional details about the action
    """
    log_message = (
        f"ADMIN ACTION: user={user_id} action={action} "
        f"resource={resource_type}/{resource_id}"
    )

    if details:
        log_message += f" details={details}"

    logger.warning(log_message)  # Use WARNING level for audit visibility


def require_universal_admin(current_user: Dict[str, Any], operation: str = "this operation"):
    """
    Require universal admin access or raise 403.

    Args:
        current_user: Current user dict from JWT token
        operation: Description of the operation for error message

    Raises:
        HTTPException: If user is not a universal admin
    """
    is_universal_admin = current_user.get("is_universal_admin", False)

    if not is_universal_admin:
        raise HTTPException(
            status_code=403,
            detail=f"Universal admin access required for {operation}"
        )

    user_id = current_user.get("id") or current_user.get("sub")
    logger.info(f"Universal admin {user_id} authorized for {operation}")
