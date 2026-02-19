"""
Admin User Management API

MongoDB-based user management system.
All authentication is now handled through MongoDB.

Available endpoints:
- /api/admin/users (GET, POST, PATCH, DELETE) - MongoDB user management
- /api/admin/users/{id}/reset-password - MongoDB password reset
- /api/admin/create-user-organization - MongoDB organization creation
- Universal admin management (uses MongoDB)
- Organization management (uses MongoDB)
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr
import logging
from enum import Enum
import subprocess
import json
import re

from ..auth import get_current_user_mongo, get_current_user_mongo
from ..services.organization_service import organization_service
from ..services.auth_service import get_auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

def is_admin_user(user: dict) -> bool:
    """Check if user has admin privileges"""
    user_email = user.get("email", "")
    admin_emails = [
        "ailabsafrica@gmail.com",
        "admin@ailabsafrica.com",
        "support@ailabsafrica.com",
        "alfred.anyan@gmail.com"
    ]

    # Check email-based admin access or role metadata
    return (user_email in admin_emails or
            user.get("user_metadata", {}).get("role") == "admin" or
            user.get("app_metadata", {}).get("role") == "admin")

# Models
class User(BaseModel):
    id: str
    email: str
    name: str
    role: str = "user"
    status: str = "active"
    created_at: datetime
    last_login: Optional[datetime] = None
    email_verified: bool = False
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None

class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: str = "user"
    sendWelcomeEmail: bool = True

class UpdateUserRequest(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    emailVerified: Optional[bool] = None

class UserResponse(BaseModel):
    users: List[User]
    total: int
    page: int
    per_page: int

# Supabase client removed - using MongoDB only

@router.get("/users", response_model=UserResponse)
async def get_users(
    search: Optional[str] = Query(None, description="Search by email or name"),
    role: Optional[str] = Query(None, description="Filter by role"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user_mongo)
):
    """Get list of users with filtering and pagination"""

    # Check admin privileges
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    try:
        # Use MongoDB auth service
        auth_service = await get_auth_service()

        # Get users from MongoDB
        result = await auth_service.get_all_users(
            search=search,
            role=role,
            status=status,
            page=page,
            per_page=per_page
        )

        # Convert MongoDB users to response format
        users = []
        for user_doc in result["users"]:
            try:
                # Get user's organization
                user_orgs = organization_service.get_organizations_for_user(user_doc["_id"])
                org_id = user_orgs[0].id if user_orgs else None
                org_name = user_orgs[0].display_name if user_orgs else None

                # Ensure all string fields are actually strings
                user_id = str(user_doc["_id"]) if user_doc.get("_id") else ""
                user_email = str(user_doc.get("email", ""))
                user_name = str(user_doc.get("display_name") or user_doc.get("email", ""))

                # Check if user has universal_admin role in organization_users
                # Reason: Universal admin role is stored in organization_users, not on user document
                is_universal_admin = organization_service.is_universal_admin(user_id, user_email)
                user_role = "universal_admin" if is_universal_admin else str(user_doc.get("role", "user"))

                # Debug logging
                if user_email in ["admin@ailabsafrica.com", "alfred.anyan@gmail.com"]:
                    logger.debug(f"User {user_email}: is_universal_admin={is_universal_admin}, role={user_role}, doc_role={user_doc.get('role')}")

                user = User(
                    id=user_id,
                    email=user_email,
                    name=user_name,
                    role=user_role,
                    status="active" if user_doc.get("is_active", True) else "inactive",
                    created_at=user_doc.get("created_at", datetime.now(timezone.utc)),
                    last_login=user_doc.get("last_login_at"),
                    email_verified=user_doc.get("email_verified", False),
                    organization_id=str(org_id) if org_id else None,
                    organization_name=str(org_name) if org_name else None
                )
                users.append(user)
            except Exception as user_error:
                logger.error(f"Error processing user {user_doc.get('email', 'unknown')}: {str(user_error)}")
                # Skip this user and continue with others
                continue

        return UserResponse(
            users=users,
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"]
        )

    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch users: {str(e)}"
        )

@router.post("/users")
async def create_user(
    user_data: CreateUserRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Create a new user"""

    # Check admin privileges
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    try:
        # Use MongoDB auth service
        auth_service = await get_auth_service()
        from ..models import SignupRequest

        # Create user in MongoDB
        signup_data = SignupRequest(
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.name.split(' ')[0] if ' ' in user_data.name else user_data.name,
            last_name=' '.join(user_data.name.split(' ')[1:]) if ' ' in user_data.name else '',
            role=user_data.role
        )

        # Create user and organization
        auth_response = await auth_service.signup(signup_data)

        # Get the created organization
        organization = None
        if auth_response.user.primary_organization_id:
            org_doc = await auth_service.organizations_collection.find_one(
                {"_id": auth_response.user.primary_organization_id}
            )
            if org_doc:
                from ..models import Organization
                organization = Organization(**org_doc)

        # TODO: Send welcome email if requested
        if user_data.sendWelcomeEmail:
            logger.info(f"Welcome email should be sent to {user_data.email}")

        return {
            "success": True,
            "user": {
                "id": auth_response.user.id,
                "email": auth_response.user.email,
                "name": user_data.name,
                "role": user_data.role,
                "organization_id": organization.id if organization else None,
                "organization_name": organization.display_name if organization else None
            }
        }

    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user: {str(e)}"
        )

@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    updates: UpdateUserRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Update user information"""

    # Check admin privileges
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    try:
        # Use MongoDB auth service
        auth_service = await get_auth_service()

        # Get user details for email (needed for universal_admin operations)
        user_doc = await auth_service.users_collection.find_one({"_id": user_id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        user_email = user_doc.get("email", "")

        # Build update object for MongoDB
        update_data = {}

        if updates.email is not None:
            update_data["email"] = updates.email
            user_email = updates.email  # Update email for universal_admin operations

        if updates.name is not None:
            # Split name into first and last name
            name_parts = updates.name.split(' ', 1)
            update_data["first_name"] = name_parts[0]
            update_data["last_name"] = name_parts[1] if len(name_parts) > 1 else ''
            update_data["display_name"] = updates.name

        # Handle role updates specially for universal_admin
        # Reason: universal_admin is stored in organization_users, not on user document
        if updates.role is not None:
            current_is_universal_admin = organization_service.is_universal_admin(user_id, user_email)
            logger.info(f"Updating user {user_email} role from {'universal_admin' if current_is_universal_admin else 'regular'} to {updates.role}")

            if updates.role == "universal_admin":
                # Add universal_admin role if not already set
                if not current_is_universal_admin:
                    success = organization_service.add_universal_admin(user_id, user_email)
                    logger.info(f"Added universal_admin role for {user_email}: {success}")
            else:
                # Remove universal_admin role if currently set
                if current_is_universal_admin:
                    success = organization_service.remove_universal_admin(user_id)
                    logger.info(f"Removed universal_admin role for {user_email}: {success}")
                # Store regular role on user document
                update_data["role"] = updates.role
                logger.info(f"Setting regular role {updates.role} on user document for {user_email}")

        if updates.status is not None:
            update_data["is_active"] = updates.status == "active"

        if updates.emailVerified is not None:
            update_data["email_verified"] = updates.emailVerified

        # Update user in MongoDB
        updated_user = await auth_service.update_user(user_id, update_data)

        if not updated_user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        return {
            "success": True,
            "message": "User updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update user: {str(e)}"
        )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Delete a user"""

    # Check admin privileges
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    try:
        # Use MongoDB auth service
        auth_service = await get_auth_service()

        # Delete user from MongoDB
        result = await auth_service.delete_user(user_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        return {
            "success": True,
            "message": "User deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete user: {str(e)}"
        )

@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    new_password: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Reset user password"""

    # Check admin privileges
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    try:
        # Use MongoDB auth service
        auth_service = await get_auth_service()

        # Update password in MongoDB
        result = await auth_service.update_user_password(user_id, new_password)

        if not result:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        return {
            "success": True,
            "message": "Password reset successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset password: {str(e)}"
        )

@router.post("/users/{user_id}/verify-email")
async def verify_user_email(
    user_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Manually verify user email"""

    # Check admin privileges
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    try:
        # Use MongoDB auth service
        auth_service = await get_auth_service()

        # Verify email in MongoDB
        result = await auth_service.update_user(user_id, {"email_verified": True})

        if not result:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        return {
            "success": True,
            "message": "Email verified successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to verify email: {str(e)}"
        )

@router.post("/create-user-organization")
async def create_user_organization(
    current_user: dict = Depends(get_current_user_mongo)
):
    """Create default organization for current authenticated user if they don't have one"""

    try:
        user_id = current_user.get("tenant_id") or current_user.get("account_id")
        user_email = current_user.get("email")
        user_name = current_user.get("name", user_email)

        if not user_id or not user_email:
            raise HTTPException(
                status_code=400,
                detail="User ID and email are required"
            )

        # Check if user already has an organization
        user_orgs = organization_service.get_organizations_for_user(user_id)

        if user_orgs:
            return {
                "success": True,
                "message": "User already has an organization",
                "organization": {
                    "id": user_orgs[0].id,
                    "name": user_orgs[0].display_name
                }
            }

        # Create default organization
        from ..models import OrganizationCreate
        default_org = OrganizationCreate(
            name=f"{user_name}'s Organization",
            display_name=f"{user_name}'s Organization",
            description="Default organization created during signup"
        )

        organization = organization_service.create_organization(
            default_org,
            user_id,
            user_email
        )

        return {
            "success": True,
            "message": "Organization created successfully",
            "organization": {
                "id": organization.id,
                "name": organization.display_name
            }
        }

    except Exception as e:
        logger.error(f"Error creating user organization: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create organization: {str(e)}"
        )

@router.post("/migrate-users-to-organizations")
async def migrate_users_to_organizations(
    current_user: dict = Depends(get_current_user_mongo)
):
    """Migrate existing users to have default organizations (for current mock system)"""

    # Check admin privileges
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    try:
        logger.info("Starting user-to-organization migration for mock system...")

        # For now, create some demo organizations since we're using mock auth
        # This will be updated when real Supabase integration is complete

        demo_users = [
            {"id": "demo-user-1", "email": "alfred.anyan@gmail.com", "name": "Alfred Anyan"},
            {"id": "demo-user-2", "email": "demo@ailabsafrica.com", "name": "Demo User"},
            {"id": "demo-user-3", "email": "test@ailabsafrica.com", "name": "Test User"},
        ]

        created_orgs = 0

        for user_data in demo_users:
            try:
                # Check if user already has an organization
                user_orgs = organization_service.get_organizations_for_user(user_data["id"])

                if not user_orgs:
                    # Create default organization
                    from ..models import OrganizationCreate
                    default_org = OrganizationCreate(
                        name=f"{user_data['name']}'s Organization",
                        display_name=f"{user_data['name']}'s Organization",
                        description="Default organization created during migration"
                    )

                    organization = organization_service.create_organization(
                        default_org,
                        user_data["id"],
                        user_data["email"]
                    )

                    logger.info(f"✅ Created organization '{organization.display_name}' for user {user_data['email']}")
                    created_orgs += 1
                else:
                    logger.info(f"✅ User {user_data['email']} already has organization: {user_orgs[0].display_name}")

            except Exception as e:
                logger.error(f"❌ Failed to create organization for user {user_data['email']}: {str(e)}")

        return {
            "success": True,
            "message": f"Migration completed. Created {created_orgs} organizations.",
            "organizations_created": created_orgs
        }

    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to migrate users: {str(e)}"
        )

@router.post("/users/{user_id}/make-universal-admin")
async def make_user_universal_admin(
    user_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Make a user a universal admin."""

    # Check admin privileges
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    try:
        # Use MongoDB auth service
        auth_service = await get_auth_service()

        # Get user details from MongoDB
        user = await auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        user_email = user.get("email")

        # Add universal admin role
        success = organization_service.add_universal_admin(user_id, user_email)

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to add universal admin role"
            )

        return {
            "success": True,
            "message": f"User {user_email} is now a universal admin",
            "user_id": user_id,
            "email": user_email
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error making user universal admin: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to make user universal admin: {str(e)}"
        )

@router.delete("/users/{user_id}/universal-admin")
async def remove_user_universal_admin(
    user_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Remove universal admin role from a user."""

    # Check admin privileges
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    try:
        success = organization_service.remove_universal_admin(user_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail="User not found or not a universal admin"
            )

        return {
            "success": True,
            "message": "Universal admin role removed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing universal admin role: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove universal admin role: {str(e)}"
        )

@router.get("/users/{user_id}/universal-admin-status")
async def check_universal_admin_status(
    user_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Check if a user is a universal admin."""

    # Check admin privileges
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    try:
        # Get user email for fallback check
        auth_service = await get_auth_service()
        user_doc = await auth_service.get_user_by_id(user_id)
        user_email = user_doc.get("email", "") if user_doc else ""

        is_universal_admin = organization_service.is_universal_admin(user_id, user_email)

        return {
            "user_id": user_id,
            "is_universal_admin": is_universal_admin
        }

    except Exception as e:
        logger.error(f"Error checking universal admin status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check universal admin status: {str(e)}"
        )


# =============================================================================
# NEW MONGODB-BASED ADMIN FUNCTIONS
# =============================================================================

@router.get("/mongo/users", response_model=UserResponse)
async def get_mongo_users(
    search: Optional[str] = Query(None, description="Search by email or name"),
    role: Optional[str] = Query(None, description="Filter by role"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user_mongo)
):
    """Get list of users from MongoDB with filtering and pagination"""

    # Check admin privileges
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    try:
        # Get users from MongoDB
        auth_service = await get_auth_service()
        users_data = await auth_service.get_all_users(
            search=search,
            role=role,
            status=status,
            page=page,
            per_page=per_page
        )

        # Convert to our User model format
        users = []
        for user_data in users_data.get('users', []):
            # Get organization info
            org_info = None
            if user_data.get('primary_organization_id'):
                org_info = organization_service.get_organization_by_id(
                    user_data['primary_organization_id']
                )

            user = User(
                id=user_data['id'],
                email=user_data['email'],
                name=user_data['display_name'],
                role="authenticated",  # Default role for MongoDB users
                status="active" if user_data.get('is_active') else "inactive",
                created_at=user_data.get('created_at'),
                last_login=user_data.get('last_login_at'),
                organization=org_info.dict() if org_info else None
            )
            users.append(user)

        return UserResponse(
            users=users,
            total=users_data.get('total', len(users)),
            page=page,
            per_page=per_page
        )

    except Exception as e:
        logger.error(f"Error getting MongoDB users: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get users: {str(e)}"
        )


@router.post("/mongo/users")
async def create_mongo_user(
    user_data: CreateUserRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Create a new user in MongoDB"""

    # Check admin privileges
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    try:
        # Create user using MongoDB auth service
        auth_service = await get_auth_service()
        new_user = await auth_service.create_user({
            "email": user_data.email,
            "password": user_data.password,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "organization_name": user_data.organization_name
        })

        return {
            "message": "User created successfully",
            "user": new_user,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error creating MongoDB user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user: {str(e)}"
        )


@router.patch("/mongo/users/{user_id}")
async def update_mongo_user(
    user_id: str,
    update_data: UpdateUserRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Update a user in MongoDB"""

    # Check admin privileges
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    try:
        # Update user using MongoDB auth service
        auth_service = await get_auth_service()
        updated_user = await auth_service.update_user(user_id, {
            "first_name": update_data.first_name,
            "last_name": update_data.last_name,
            "is_active": update_data.status == "active"
        })

        return {
            "message": "User updated successfully",
            "user": updated_user,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error updating MongoDB user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/mongo/users/{user_id}")
async def delete_mongo_user(
    user_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Delete a user from MongoDB"""

    # Check admin privileges
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    try:
        # Delete user using MongoDB auth service
        auth_service = await get_auth_service()
        await auth_service.delete_user(user_id)

        return {
            "message": "User deleted successfully",
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error deleting MongoDB user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.post("/mongo/users/{user_id}/reset-password")
async def reset_mongo_user_password(
    user_id: str,
    password_data: dict,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Reset password for a MongoDB user"""

    # Check admin privileges
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    try:
        # Reset password using MongoDB auth service
        auth_service = await get_auth_service()
        await auth_service.reset_password(user_id, password_data.get('new_password'))

        return {
            "message": "Password reset successfully",
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error resetting MongoDB user password: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset password: {str(e)}"
        )


# =============================================================================
# ADMIN ACCESS CHECK ENDPOINT
# =============================================================================

class AdminAccessResponse(BaseModel):
    """Response model for admin access check"""
    is_admin: bool
    is_universal_admin: bool
    admin_organizations: List[Dict[str, Any]]
    can_access_admin: bool

@router.get("/check-access", response_model=AdminAccessResponse)
async def check_admin_access(
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Check if current user has admin access.

    Returns information about:
    - Is hardcoded admin (email-based)
    - Is universal admin (cross-org access)
    - Organizations where user is ADMIN or OWNER
    - Overall admin access permission
    """
    try:
        user_id = current_user.get("id") or current_user.get("sub") or current_user.get("tenant_id")
        user_email = current_user.get("email", "")

        # Check if user is hardcoded admin
        is_hardcoded_admin = is_admin_user(current_user)

        # Check if user is universal admin
        is_universal = organization_service.is_universal_admin(user_id, user_email)

        # Get organizations where user has admin/owner role
        admin_orgs = []
        try:
            user_orgs = organization_service.get_organizations_for_user(user_id)
            for org_membership in user_orgs:
                if org_membership.role in ['ADMIN', 'OWNER']:
                    admin_orgs.append({
                        "id": org_membership.organization.id,
                        "name": org_membership.organization.display_name,
                        "role": org_membership.role
                    })
        except Exception as e:
            logger.warning(f"Error fetching user organizations: {e}")

        # User can access admin if they are:
        # 1. Hardcoded admin (email-based)
        # 2. Universal admin
        # 3. ADMIN or OWNER in at least one organization
        can_access = is_hardcoded_admin or is_universal or len(admin_orgs) > 0

        return AdminAccessResponse(
            is_admin=is_hardcoded_admin,
            is_universal_admin=is_universal,
            admin_organizations=admin_orgs,
            can_access_admin=can_access
        )

    except Exception as e:
        logger.error(f"Error checking admin access: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check admin access: {str(e)}"
        )


# =============================================================================
# SYSTEM LOGS ENDPOINT
# =============================================================================

class LogEntry(BaseModel):
    id: str
    timestamp: str
    level: str
    category: str
    message: str
    user: Optional[str] = None
    source: str
    details: Optional[str] = None

class LogsResponse(BaseModel):
    logs: List[LogEntry]
    total: int
    page: int
    per_page: int

@router.get("/logs", response_model=LogsResponse)
async def get_system_logs(
    level: Optional[str] = Query(None, description="Filter by log level"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search logs"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    current_user: dict = Depends(get_current_user_mongo)
):
    """Get system logs from journalctl and application logs"""

    # Check admin privileges
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    try:
        logs = []

        # Fetch logs from journalctl for kasaai services
        services = [
            "kasaai-core-backend",
            "kasaai-edge-node",
            "kasaai-dev-backend"
        ]

        for service in services:
            try:
                # Get logs from journalctl (last 1000 lines)
                cmd = [
                    "journalctl",
                    "-u", f"{service}.service",
                    "-n", "500",
                    "--output=json",
                    "--no-pager"
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0 and result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        if not line:
                            continue
                        try:
                            log_entry = json.loads(line)
                            message = log_entry.get('MESSAGE', '')

                            # Skip empty messages
                            if not message:
                                continue

                            # Parse log level from message
                            level_match = re.search(r'\b(INFO|WARNING|ERROR|CRITICAL|DEBUG)\b', message, re.IGNORECASE)
                            log_level = level_match.group(1).lower() if level_match else 'info'

                            # Determine category from message content
                            category = 'system'
                            if 'auth' in message.lower() or 'login' in message.lower():
                                category = 'auth'
                            elif 'database' in message.lower() or 'mongo' in message.lower() or 'postgres' in message.lower():
                                category = 'database'
                            elif 'api' in message.lower() or 'request' in message.lower():
                                category = 'api'
                            elif 'automation' in message.lower():
                                category = 'automation'
                            elif 'user' in message.lower():
                                category = 'user'

                            # Extract timestamp
                            timestamp_usec = int(log_entry.get('__REALTIME_TIMESTAMP', '0'))
                            timestamp = datetime.fromtimestamp(timestamp_usec / 1000000).strftime('%Y-%m-%d %H:%M:%S')

                            logs.append(LogEntry(
                                id=f"{service}-{timestamp_usec}",
                                timestamp=timestamp,
                                level=log_level,
                                category=category,
                                message=message[:200],  # Limit message length
                                source=service,
                                details=message if len(message) > 200 else None
                            ))
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            logger.debug(f"Error parsing log entry: {e}")
                            continue

            except subprocess.TimeoutExpired:
                logger.warning(f"Timeout fetching logs for {service}")
                continue
            except Exception as e:
                logger.warning(f"Error fetching logs for {service}: {e}")
                continue

        # Sort logs by timestamp (newest first)
        logs.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply filters
        filtered_logs = logs

        if level and level != 'all':
            filtered_logs = [log for log in filtered_logs if log.level == level]

        if category and category != 'all':
            filtered_logs = [log for log in filtered_logs if log.category == category]

        if search:
            search_lower = search.lower()
            filtered_logs = [
                log for log in filtered_logs
                if search_lower in log.message.lower() or
                   search_lower in log.source.lower() or
                   (log.details and search_lower in log.details.lower()) or
                   (log.user and search_lower in log.user.lower())
            ]

        # Pagination
        total = len(filtered_logs)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_logs = filtered_logs[start_idx:end_idx]

        return LogsResponse(
            logs=paginated_logs,
            total=total,
            page=page,
            per_page=per_page
        )

    except Exception as e:
        logger.error(f"Error fetching system logs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch system logs: {str(e)}"
        )


# ============================================================================
# BILLING SYNC ENDPOINTS
# ============================================================================

@router.post("/billing/sync-now")
async def trigger_billing_sync_now(
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Manually trigger billing sync for all automations (ADMIN ONLY).

    This endpoint allows admins to manually run the billing sync task
    instead of waiting for the scheduled midnight run.

    Useful for:
    - Testing the billing sync system
    - Immediately billing recent calls
    - Recovering from sync failures

    Returns:
        Summary of sync results including calls synced and billing records created
    """
    # Verify admin access
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required to trigger billing sync"
        )

    try:
        logger.info(f"🔄 Manual billing sync triggered by user: {current_user.get('email')}")

        # Import and run the billing sync task
        from ..tasks.billing_sync import sync_and_bill_all_automations

        result = await sync_and_bill_all_automations()

        if result.get("success"):
            return {
                "success": True,
                "message": "Billing sync completed successfully",
                "summary": result.get("summary"),
                "results": result.get("results"),
                "errors": result.get("errors", []),
                "completed_at": result.get("completed_at")
            }
        else:
            return {
                "success": False,
                "message": "Billing sync failed",
                "error": result.get("error"),
                "completed_at": result.get("completed_at")
            }

    except Exception as e:
        logger.error(f"❌ Error triggering billing sync: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger billing sync: {str(e)}"
        )


@router.get("/billing/sync-status")
async def get_billing_sync_status(
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get the status of the scheduled billing sync task (ADMIN ONLY).

    Returns information about:
    - When the task last ran
    - Next scheduled run time
    - Task configuration

    Returns:
        Billing sync task status and schedule information
    """
    # Verify admin access
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required to view billing sync status"
        )

    try:
        # Get scheduler from main module
        from ..main import scheduler

        # Get the billing sync job
        job = scheduler.get_job('billing_sync')

        if not job:
            return {
                "success": False,
                "message": "Billing sync job not found in scheduler",
                "scheduled": False
            }

        return {
            "success": True,
            "scheduled": True,
            "job_id": job.id,
            "job_name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
            "pending": job.pending
        }

    except Exception as e:
        logger.error(f"❌ Error getting billing sync status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get billing sync status: {str(e)}"
        )


# ============================================================================
# WALLET AUTO-RELOAD ENDPOINTS
# ============================================================================

@router.post("/wallet/auto-reload-now")
async def trigger_auto_reload_now(
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Manually trigger wallet auto-reload check for all wallets (ADMIN ONLY).

    This endpoint allows admins to manually run the auto-reload task
    instead of waiting for the scheduled 5-minute run.

    Useful for:
    - Testing the auto-reload system
    - Immediately processing pending reloads
    - Recovering from system downtime

    Returns:
        Summary of auto-reload results including wallets reloaded and amounts
    """
    # Verify admin access
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required to trigger auto-reload"
        )

    try:
        logger.info(f"🔄 Manual auto-reload triggered by user: {current_user.get('email')}")

        # Import and run the auto-reload task
        from ..tasks.wallet_auto_reload import check_and_reload_wallets

        result = await check_and_reload_wallets()

        if result.get("success"):
            return {
                "success": True,
                "message": "Auto-reload check completed successfully",
                "summary": result.get("summary"),
                "results": result.get("results"),
                "errors": result.get("errors", []),
                "completed_at": result.get("completed_at")
            }
        else:
            return {
                "success": False,
                "message": "Auto-reload check failed",
                "error": result.get("error"),
                "completed_at": result.get("completed_at")
            }

    except Exception as e:
        logger.error(f"❌ Error triggering auto-reload: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger auto-reload: {str(e)}"
        )


@router.get("/wallet/auto-reload-status")
async def get_auto_reload_status(
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get the status of the scheduled auto-reload task (ADMIN ONLY).

    Returns information about:
    - When the task last ran
    - Next scheduled run time
    - Task configuration
    - Statistics on wallets with auto-reload enabled

    Returns:
        Auto-reload task status and statistics
    """
    # Verify admin access
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required to view auto-reload status"
        )

    try:
        # Get scheduler from main module
        from ..main import scheduler
        from ..mongo import get_database

        db = get_database()

        # Get the auto-reload job
        job = scheduler.get_job('wallet_auto_reload')

        if not job:
            return {
                "success": False,
                "message": "Auto-reload job not found in scheduler",
                "scheduled": False
            }

        # Get statistics on wallets with auto-reload enabled
        total_wallets = await db.wallets.count_documents({"status": "active"})
        auto_reload_enabled_count = await db.wallets.count_documents({
            "status": "active",
            "auto_reload_enabled": True
        })
        auto_reload_ready_count = await db.wallets.count_documents({
            "status": "active",
            "auto_reload_enabled": True,
            "auto_reload_payment_method_id": {"$exists": True, "$ne": None}
        })

        # Get count of wallets currently below threshold
        wallets_below_threshold = await db.wallets.count_documents({
            "status": "active",
            "auto_reload_enabled": True,
            "auto_reload_payment_method_id": {"$exists": True, "$ne": None},
            "$expr": {"$lte": ["$balance", "$auto_reload_threshold"]}
        })

        return {
            "success": True,
            "scheduled": True,
            "job_id": job.id,
            "job_name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
            "pending": job.pending,
            "statistics": {
                "total_active_wallets": total_wallets,
                "auto_reload_enabled": auto_reload_enabled_count,
                "auto_reload_ready": auto_reload_ready_count,
                "currently_below_threshold": wallets_below_threshold,
                "percentage_enabled": round((auto_reload_enabled_count / total_wallets * 100), 2) if total_wallets > 0 else 0
            }
        }

    except Exception as e:
        logger.error(f"❌ Error getting auto-reload status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get auto-reload status: {str(e)}"
        )


# ============================================================================
# USER INVITATION ENDPOINTS
# ============================================================================

@router.post("/invitations")
async def create_user_invitation(
    request: Dict[str, Any],
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Create a user invitation (ADMIN ONLY).

    Sends an invitation email to the specified email address.
    When the user accepts, they will be automatically registered as an affiliate
    with the inviter's referral code.

    Request body:
        {
            "email": "newuser@example.com",
            "role": "user",  # user, admin, moderator, universal_admin
            "message": "Welcome to our platform!",  # optional
            "send_email": true  # optional, default true
        }

    Returns:
        Invitation details including the invitation token
    """
    # Check admin privileges
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required to invite users"
        )

    try:
        from ..services.invitation_service import get_invitation_service
        from ..models.invitation import InviteUserRequest

        invitation_service = await get_invitation_service()

        # Get inviter details
        inviter_user_id = current_user.get("tenant_id") or current_user.get("account_id") or current_user.get("sub")
        inviter_email = current_user.get("email", "")
        inviter_name = current_user.get("name", inviter_email)

        # Create invitation request
        invite_request = InviteUserRequest(**request)

        # Create invitation
        invitation = await invitation_service.create_invitation(
            request=invite_request,
            inviter_user_id=inviter_user_id,
            inviter_email=inviter_email,
            inviter_name=inviter_name,
        )

        return {
            "success": True,
            "message": f"Invitation sent to {invitation.email}",
            "invitation": {
                "id": invitation.id,
                "email": invitation.email,
                "token": invitation.token,
                "role": invitation.role,
                "status": invitation.status,
                "expires_at": invitation.expires_at.isoformat(),
                "invited_by": invitation.invited_by_name,
                "referral_code": invitation.inviter_referral_code,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating invitation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create invitation: {str(e)}"
        )


@router.get("/invitations")
async def get_user_invitations(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get list of user invitations (ADMIN ONLY).

    Returns all invitations with optional filtering by status.

    Query parameters:
        - status: Filter by invitation status (pending, accepted, expired, cancelled)
        - limit: Maximum number of results (default 100)
        - skip: Number of results to skip for pagination (default 0)

    Returns:
        List of invitations with statistics
    """
    # Check admin privileges
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required to view invitations"
        )

    try:
        from ..services.invitation_service import get_invitation_service
        from ..models.invitation import InvitationStatus

        invitation_service = await get_invitation_service()

        # Parse status filter
        status_filter = None
        if status and status != "all":
            try:
                status_filter = InvitationStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status: {status}"
                )

        # Get invitations
        response = await invitation_service.get_invitations(
            status=status_filter,
            limit=limit,
            skip=skip,
        )

        return {
            "success": True,
            "invitations": response.invitations,
            "stats": {
                "total": response.total,
                "pending": response.pending,
                "accepted": response.accepted,
                "expired": response.expired,
                "cancelled": response.cancelled,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching invitations: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch invitations: {str(e)}"
        )


@router.delete("/invitations/{invitation_id}")
async def cancel_user_invitation(
    invitation_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Cancel a pending invitation (ADMIN ONLY).

    Cancels a pending invitation so it can no longer be accepted.

    Path parameters:
        - invitation_id: ID of the invitation to cancel

    Returns:
        Success message
    """
    # Check admin privileges
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required to cancel invitations"
        )

    try:
        from ..services.invitation_service import get_invitation_service

        invitation_service = await get_invitation_service()

        # Cancel invitation
        success = await invitation_service.cancel_invitation(invitation_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail="Invitation not found or already processed"
            )

        return {
            "success": True,
            "message": "Invitation cancelled successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error cancelling invitation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel invitation: {str(e)}"
        )


@router.post("/invitations/{invitation_id}/resend")
async def resend_user_invitation(
    invitation_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Resend an invitation email (ADMIN ONLY).

    Resends the invitation email for a pending invitation.

    Path parameters:
        - invitation_id: ID of the invitation to resend

    Returns:
        Success message
    """
    # Check admin privileges
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required to resend invitations"
        )

    try:
        from ..services.invitation_service import get_invitation_service

        invitation_service = await get_invitation_service()

        # Resend invitation
        success = await invitation_service.resend_invitation(invitation_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail="Invitation not found"
            )

        return {
            "success": True,
            "message": "Invitation email resent successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error resending invitation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resend invitation: {str(e)}"
        )