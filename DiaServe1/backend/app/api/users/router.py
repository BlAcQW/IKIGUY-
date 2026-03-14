"""
User API endpoints for EstateFlow.

Provides user management and invitation functionality for admin users.
"""

import logging
import uuid
import secrets
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field, EmailStr

from bson import ObjectId
from app.core.database import get_database
from app.core.auth import get_current_user
from app.integration.email_service import get_email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


def render_invitation_email(template_vars: Dict[str, Any]) -> str:
    """
    Render the invitation email template.

    Args:
        template_vars: Variables to substitute in template

    Returns:
        Rendered HTML email
    """
    # Get template path
    template_path = Path(__file__).parent.parent.parent / "templates" / "emails" / "user_invitation.html"

    # Read template
    with open(template_path, 'r') as f:
        template = f.read()

    # Simple template substitution (for production, use Jinja2 or similar)
    for key, value in template_vars.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))

    # Handle optional fields with Handlebars-style conditionals
    # {{#if user_name}} ... {{/if}}
    import re

    # Process {{#if user_name}} blocks
    if template_vars.get("user_name"):
        template = re.sub(r'\{\{#if user_name\}\}(.*?)\{\{/if\}\}', r'\1', template, flags=re.DOTALL)
    else:
        template = re.sub(r'\{\{#if user_name\}\}.*?\{\{/if\}\}', '', template, flags=re.DOTALL)

    return template


class UserRole(str):
    """User roles in the system."""
    USER = "user"
    AGENT = "agent"
    MANAGER = "manager"
    ADMIN = "admin"


class UserStatus(str):
    """User status in the system."""
    ACTIVE = "active"
    INVITED = "invited"
    SUSPENDED = "suspended"


class UserInvite(BaseModel):
    """User invitation model."""
    email: EmailStr = Field(..., description="Email address of the user to invite")
    name: str | None = Field(None, min_length=1, max_length=200, description="Full name")
    role: str = Field(..., description="User role: user, agent, manager, admin")
    organization_id: str = Field(..., min_length=1, description="Organization ID")


class UserUpdate(BaseModel):
    """User update model."""
    name: str | None = Field(None, min_length=1, max_length=200)
    role: str | None = Field(None, description="User role")
    status: str | None = Field(None, description="User status")
    organization_id: str | None = None


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    name: str | None = None
    role: str
    status: str
    organization_id: str
    created_at: datetime | None = None
    invited_at: datetime | None = None
    last_login: datetime | None = None


class UserListResponse(BaseModel):
    """User list response model."""
    users: List[UserResponse]
    total: int
    limit: int
    offset: int


class InvitationToken(BaseModel):
    """Invitation token stored in database."""
    token: str
    email: str
    name: str | None
    role: str
    organization_id: str
    created_at: datetime
    expires_at: datetime
    used: bool = False


class UserProfile(BaseModel):
    """User profile response model."""
    id: str
    email: str
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserProfileUpdate(BaseModel):
    """User profile update request model."""
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None


@router.post("/invite", status_code=status.HTTP_201_CREATED)
async def invite_user(
    invite_data: UserInvite,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Invite a new user via email (admin only).

    Creates an invitation token and stores it in the database.
    In production, this would also send an email with the invitation link.

    Args:
        invite_data: User invitation data
        database: Database instance
        current_user: Current authenticated user

    Returns:
        Invitation details with token

    Raises:
        HTTPException: If user is not admin or invitation fails
    """
    try:
        # Check if user is admin
        is_admin = (
            current_user.get("email") == "admin@ailabsafrica.com" or
            current_user.get("role") == "admin"
        )

        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can invite users"
            )

        # Validate role
        valid_roles = [UserRole.USER, UserRole.AGENT, UserRole.MANAGER, UserRole.ADMIN]
        if invite_data.role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )

        # Check if organization exists
        organizations_collection = database["organizations"]
        org = await organizations_collection.find_one({"id": invite_data.organization_id})
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization {invite_data.organization_id} not found"
            )

        # Check if user already invited or exists
        invitations_collection = database["user_invitations"]
        existing_invite = await invitations_collection.find_one({
            "email": invite_data.email,
            "used": False,
            "expires_at": {"$gt": datetime.utcnow()}
        })

        if existing_invite:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Active invitation already exists for {invite_data.email}"
            )

        # Generate invitation token (cryptographically secure)
        token = secrets.token_urlsafe(32)
        now = datetime.utcnow()
        expires_at = now + timedelta(days=7)  # Token valid for 7 days

        # Create invitation document
        invitation_doc = {
            "token": token,
            "email": invite_data.email,
            "name": invite_data.name,
            "role": invite_data.role,
            "organization_id": invite_data.organization_id,
            "created_at": now,
            "expires_at": expires_at,
            "used": False,
            "invited_by": current_user.get("email")
        }

        # Insert invitation
        await invitations_collection.insert_one(invitation_doc)

        logger.info(
            f"User invitation created: {invite_data.email} "
            f"for organization {invite_data.organization_id} "
            f"by {current_user.get('email')}"
        )

        # Send invitation email
        try:
            email_service = get_email_service()

            # Prepare template variables
            invitation_url = f"https://estateflow.ailabsafrica.com/invite/{token}"
            role_display = invite_data.role.capitalize()

            template_vars = {
                "user_email": invite_data.email,
                "user_name": invite_data.name or "",
                "user_role": role_display,
                "organization_name": org["name"],
                "invited_by": current_user.get("email"),
                "invitation_url": invitation_url,
                "expiration_date": expires_at.strftime("%B %d, %Y at %H:%M UTC"),
            }

            # Render email HTML
            html_body = render_invitation_email(template_vars)

            # Plain text fallback
            plain_body = f"""
You're Invited to EstateFlow!

Hi{' ' + invite_data.name if invite_data.name else ''},

{current_user.get('email')} has invited you to join {org['name']} on EstateFlow.

Invitation Details:
- Email: {invite_data.email}
- Role: {role_display}
- Organization: {org['name']}

Accept your invitation here:
{invitation_url}

This invitation expires in 7 days ({expires_at.strftime('%B %d, %Y at %H:%M UTC')}).

If you didn't expect this invitation, you can safely ignore this email.

---
EstateFlow by AI Labs Africa
https://estateflow.ailabsafrica.com
"""

            # Send email
            email_result = await email_service.send_email(
                to=invite_data.email,
                subject=f"You're invited to join {org['name']} on EstateFlow",
                body=plain_body,
                html_body=html_body,
                from_email="noreply@ailabsafrica.com",
                from_name="EstateFlow"
            )

            if email_result.get("success"):
                logger.info(f"✅ Invitation email sent successfully to {invite_data.email}")
            else:
                logger.warning(f"⚠️ Failed to send invitation email: {email_result.get('error')}")
                # Don't fail the invitation creation if email fails

        except Exception as email_error:
            logger.error(f"❌ Error sending invitation email: {str(email_error)}")
            # Don't fail the invitation creation if email fails

        return {
            "message": "Invitation created successfully",
            "email": invite_data.email,
            "organization_id": invite_data.organization_id,
            "role": invite_data.role,
            "token": token,  # In production, don't return token in response
            "expires_at": expires_at.isoformat(),
            "invitation_url": f"https://estateflow.ailabsafrica.com/invite/{token}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user invitation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user invitation"
        )


@router.get("", response_model=UserListResponse)
async def list_users(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    organization_id: str | None = Query(None),
    role: str | None = Query(None),
    status: str | None = Query(None),
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List users (admin only).

    Returns users from Supabase auth.users metadata stored in MongoDB.

    Args:
        limit: Page size
        offset: Page offset
        organization_id: Filter by organization
        role: Filter by role
        status: Filter by status
        database: Database instance
        current_user: Current authenticated user

    Returns:
        List of users

    Raises:
        HTTPException: If user is not admin
    """
    try:
        # Check if user is admin
        is_admin = (
            current_user.get("email") == "admin@ailabsafrica.com" or
            current_user.get("role") == "admin"
        )

        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can list all users"
            )

        # Build filter query
        query = {}
        if organization_id:
            query["organization_id"] = organization_id
        if role:
            query["role"] = role
        if status:
            query["status"] = status

        # For now, return mock data
        # In production, this would query Supabase or a users collection
        users_collection = database.get_collection("users_metadata")

        total = await users_collection.count_documents(query)
        cursor = users_collection.find(query).skip(offset).limit(limit)
        users_list = await cursor.to_list(length=limit)

        users = []
        for user in users_list:
            users.append(UserResponse(
                id=user.get("id", user.get("_id")),
                email=user["email"],
                name=user.get("name"),
                role=user.get("role", "user"),
                status=user.get("status", "active"),
                organization_id=user.get("organization_id", ""),
                created_at=user.get("created_at"),
                invited_at=user.get("invited_at"),
                last_login=user.get("last_login")
            ))

        return UserListResponse(
            users=users,
            total=total,
            limit=limit,
            offset=offset
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update user details (admin only).

    Args:
        user_id: User ID
        user_data: User update data
        database: Database instance
        current_user: Current authenticated user

    Returns:
        Updated user details

    Raises:
        HTTPException: If user is not admin or update fails
    """
    try:
        # Check if user is admin
        is_admin = (
            current_user.get("email") == "admin@ailabsafrica.com" or
            current_user.get("role") == "admin"
        )

        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can update users"
            )

        users_collection = database.get_collection("users_metadata")

        # Check if user exists
        user = await users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        # Build update document
        update_data = {"updated_at": datetime.utcnow()}

        if user_data.name is not None:
            update_data["name"] = user_data.name
        if user_data.role is not None:
            # Validate role
            valid_roles = [UserRole.USER, UserRole.AGENT, UserRole.MANAGER, UserRole.ADMIN]
            if user_data.role not in valid_roles:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
                )
            update_data["role"] = user_data.role
        if user_data.status is not None:
            # Validate status
            valid_statuses = [UserStatus.ACTIVE, UserStatus.INVITED, UserStatus.SUSPENDED]
            if user_data.status not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                )
            update_data["status"] = user_data.status
        if user_data.organization_id is not None:
            # Verify organization exists
            organizations_collection = database["organizations"]
            org = await organizations_collection.find_one({"id": user_data.organization_id})
            if not org:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Organization {user_data.organization_id} not found"
                )
            update_data["organization_id"] = user_data.organization_id

        # Update user
        await users_collection.update_one(
            {"id": user_id},
            {"$set": update_data}
        )

        # Fetch updated user
        updated_user = await users_collection.find_one({"id": user_id})

        logger.info(f"User updated: {user_id} by {current_user.get('email')}")

        return UserResponse(
            id=updated_user["id"],
            email=updated_user["email"],
            name=updated_user.get("name"),
            role=updated_user.get("role", "user"),
            status=updated_user.get("status", "active"),
            organization_id=updated_user.get("organization_id", ""),
            created_at=updated_user.get("created_at"),
            invited_at=updated_user.get("invited_at"),
            last_login=updated_user.get("last_login")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.get("/invitations/pending")
async def list_pending_invitations(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List pending invitations (admin only).

    Args:
        limit: Page size
        offset: Page offset
        database: Database instance
        current_user: Current authenticated user

    Returns:
        List of pending invitations

    Raises:
        HTTPException: If user is not admin
    """
    try:
        # Check if user is admin
        is_admin = (
            current_user.get("email") == "admin@ailabsafrica.com" or
            current_user.get("role") == "admin"
        )

        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can list invitations"
            )

        invitations_collection = database["user_invitations"]

        # Get pending invitations (not used and not expired)
        query = {
            "used": False,
            "expires_at": {"$gt": datetime.utcnow()}
        }

        total = await invitations_collection.count_documents(query)
        cursor = invitations_collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
        invitations_list = await cursor.to_list(length=limit)

        invitations = []
        for inv in invitations_list:
            invitations.append({
                "token": inv["token"],
                "email": inv["email"],
                "name": inv.get("name"),
                "role": inv["role"],
                "organization_id": inv["organization_id"],
                "created_at": inv["created_at"].isoformat(),
                "expires_at": inv["expires_at"].isoformat(),
                "invited_by": inv.get("invited_by")
            })

        return {
            "invitations": invitations,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing invitations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list invitations"
        )


# Invitation Acceptance Models
class InvitationDetails(BaseModel):
    """Invitation details for validation."""
    token: str
    email: EmailStr
    name: str | None = None
    role: str
    organization_id: str
    organization_name: str
    expires_at: str
    valid: bool


class AcceptInvitationRequest(BaseModel):
    """Request model for accepting invitation."""
    password: str = Field(..., min_length=8, description="Password for new account")


class AcceptInvitationResponse(BaseModel):
    """Response after accepting invitation."""
    success: bool
    message: str
    user_id: str | None = None


@router.get("/invitations/{token}/validate", response_model=InvitationDetails)
async def validate_invitation_token(
    token: str,
    database: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Validate invitation token and return invitation details.

    This is a public endpoint (no auth required) used by the invitation
    acceptance page to show invitation details before the user accepts.

    Args:
        token: Invitation token from URL
        database: Database instance

    Returns:
        Invitation details if valid

    Raises:
        HTTPException: If token invalid, expired, or already used
    """
    try:
        invitations_collection = database["user_invitations"]
        organizations_collection = database["organizations"]

        # Find invitation
        invitation = await invitations_collection.find_one({"token": token})

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )

        # Check if already used
        if invitation.get("used", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation has already been used"
            )

        # Check if expired
        expires_at = invitation.get("expires_at")
        if expires_at and expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation has expired"
            )

        # Get organization details
        org_id = invitation.get("organization_id")
        org = await organizations_collection.find_one({"id": org_id})
        org_name = org.get("name") if org else "Unknown Organization"

        # Return invitation details
        return InvitationDetails(
            token=token,
            email=invitation.get("email"),
            name=invitation.get("name"),
            role=invitation.get("role"),
            organization_id=org_id,
            organization_name=org_name,
            expires_at=expires_at.isoformat() if expires_at else None,
            valid=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating invitation token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate invitation"
        )


@router.post("/invitations/{token}/accept", response_model=AcceptInvitationResponse)
async def accept_invitation(
    token: str,
    request: AcceptInvitationRequest,
    database: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Accept invitation and create user account.

    This is a public endpoint (no auth required) that:
    1. Validates the invitation token
    2. Creates a Supabase user account
    3. Updates user metadata with organization and role
    4. Marks invitation as used

    Args:
        token: Invitation token from URL
        request: Password for new account
        database: Database instance

    Returns:
        Success message with user ID

    Raises:
        HTTPException: If token invalid or user creation fails
    """
    try:
        from supabase import create_client

        invitations_collection = database["user_invitations"]

        # Validate invitation (reuse validation logic)
        invitation = await invitations_collection.find_one({"token": token})

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )

        if invitation.get("used", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation has already been used"
            )

        expires_at = invitation.get("expires_at")
        if expires_at and expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation has expired"
            )

        # Get invitation details
        email = invitation.get("email")
        name = invitation.get("name")
        role = invitation.get("role")
        organization_id = invitation.get("organization_id")

        # Create Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Supabase configuration missing"
            )

        supabase = create_client(supabase_url, supabase_key)

        # Create user in Supabase
        try:
            auth_response = supabase.auth.admin.create_user({
                "email": email,
                "password": request.password,
                "email_confirm": True,  # Auto-confirm email
                "user_metadata": {
                    "name": name,
                    "role": role,
                    "organization_id": organization_id
                }
            })

            user_id = auth_response.user.id

            logger.info(f"Created user account for {email} (ID: {user_id})")

        except Exception as e:
            logger.error(f"Failed to create Supabase user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create user account: {str(e)}"
            )

        # Mark invitation as used
        await invitations_collection.update_one(
            {"token": token},
            {
                "$set": {
                    "used": True,
                    "used_at": datetime.utcnow(),
                    "user_id": user_id
                }
            }
        )

        logger.info(f"Invitation {token} accepted by {email}")

        return AcceptInvitationResponse(
            success=True,
            message="Account created successfully! You can now login.",
            user_id=user_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting invitation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to accept invitation"
        )


# ========================= SAVED PROPERTIES ENDPOINTS =========================

class SavedPropertyResponse(BaseModel):
    """Response model for saved property."""
    id: str
    user_id: str
    user_email: str
    property_id: str
    saved_at: datetime
    property: Dict[str, Any] | None = None  # Optional property details


class SavedPropertiesListResponse(BaseModel):
    """Response model for list of saved properties."""
    saved_properties: List[SavedPropertyResponse]
    total: int
    limit: int
    offset: int


class IsSavedResponse(BaseModel):
    """Response model for checking if property is saved."""
    is_saved: bool
    saved_at: datetime | None = None


@router.post("/me/saved-properties/{property_id}", status_code=status.HTTP_201_CREATED)
async def save_property(
    property_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Save a property to user's favorites.

    Args:
        property_id: Property ID to save
        database: Database instance
        current_user: Current authenticated user

    Returns:
        Success message and saved property details

    Raises:
        HTTPException: If property not found or already saved
    """
    try:
        user_id = current_user.get("id")
        user_email = current_user.get("email")

        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User email is required to save properties"
            )

        # Check if property exists
        properties_collection = database["properties"]
        property_doc = await properties_collection.find_one({"_id": ObjectId(property_id)})

        if not property_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property {property_id} not found"
            )

        saved_properties_collection = database["saved_properties"]

        # Check if already saved
        existing = await saved_properties_collection.find_one({
            "user_id": user_id,
            "property_id": property_id
        })

        if existing:
            # Already saved, return existing record (idempotent)
            logger.info(f"Property {property_id} already saved by user {user_id}")
            return {
                "message": "Property already saved",
                "id": existing.get("id"),
                "user_email": existing.get("user_email", user_email),
                "property_id": property_id,
                "saved_at": existing.get("saved_at").isoformat()
            }

        # Create saved property document
        saved_id = str(uuid.uuid4())
        now = datetime.utcnow()

        saved_doc = {
            "id": saved_id,
            "user_id": user_id,
            "user_email": user_email,
            "property_id": property_id,
            "saved_at": now,
            "created_at": now
        }

        # Insert saved property
        await saved_properties_collection.insert_one(saved_doc)

        # Auto-create warm lead (non-blocking)
        try:
            from app.services.lead_service import LeadService
            org_id = property_doc.get("organization_id")
            if org_id:
                lead_service = LeadService(database)
                user_name = current_user.get("name") or user_email.split("@")[0]
                await lead_service.upsert_lead(
                    organization_id=org_id,
                    name=user_name,
                    email=user_email,
                    phone=current_user.get("phone"),
                    interest_status="warm",
                    source="property_save",
                    property_id=property_id,
                    property_name=property_doc.get("title") or property_doc.get("name"),
                )
        except Exception as lead_err:
            logger.warning(f"Failed to create lead from property save: {lead_err}")

        logger.info(f"Property {property_id} saved by user {user_id}")

        return {
            "message": "Property saved successfully",
            "id": saved_id,
            "user_email": user_email,
            "property_id": property_id,
            "saved_at": now.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving property: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save property"
        )


@router.delete("/me/saved-properties/{property_id}", status_code=status.HTTP_200_OK)
async def unsave_property(
    property_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Remove a property from user's favorites.

    Args:
        property_id: Property ID to unsave
        database: Database instance
        current_user: Current authenticated user

    Returns:
        Success message

    Raises:
        HTTPException: If property not saved
    """
    try:
        user_id = current_user.get("id")

        saved_properties_collection = database["saved_properties"]

        # Delete saved property
        result = await saved_properties_collection.delete_one({
            "user_id": user_id,
            "property_id": property_id
        })

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not in saved list"
            )

        logger.info(f"Property {property_id} unsaved by user {user_id}")

        return {
            "message": "Property removed from saved list",
            "property_id": property_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsaving property: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unsave property"
        )


@router.get("/me/saved-properties", response_model=SavedPropertiesListResponse)
async def get_saved_properties(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    include_property_details: bool = Query(True, description="Include full property details"),
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get user's saved properties.

    Args:
        limit: Page size
        offset: Page offset
        include_property_details: Whether to include full property details
        database: Database instance
        current_user: Current authenticated user

    Returns:
        List of saved properties with optional property details

    Raises:
        HTTPException: If query fails
    """
    try:
        user_id = current_user.get("id")

        saved_properties_collection = database["saved_properties"]
        properties_collection = database["properties"]

        # Get saved properties for this user
        query = {"user_id": user_id}

        total = await saved_properties_collection.count_documents(query)
        cursor = saved_properties_collection.find(query).sort("saved_at", -1).skip(offset).limit(limit)
        saved_list = await cursor.to_list(length=limit)

        saved_properties = []

        for saved_item in saved_list:
            property_details = None

            if include_property_details:
                # Fetch property details
                property_doc = await properties_collection.find_one({"_id": ObjectId(saved_item["property_id"])})
                if property_doc:
                    # Convert MongoDB document to dict, remove _id
                    property_details = dict(property_doc)
                    property_details.pop("_id", None)

            saved_properties.append(SavedPropertyResponse(
                id=saved_item["id"],
                user_id=saved_item["user_id"],
                user_email=saved_item.get("user_email", ""),
                property_id=saved_item["property_id"],
                saved_at=saved_item["saved_at"],
                property=property_details
            ))

        return SavedPropertiesListResponse(
            saved_properties=saved_properties,
            total=total,
            limit=limit,
            offset=offset
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting saved properties: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get saved properties"
        )


@router.get("/me/saved-properties/{property_id}/check", response_model=IsSavedResponse)
async def check_property_saved(
    property_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Check if a property is saved by the current user.

    Args:
        property_id: Property ID to check
        database: Database instance
        current_user: Current authenticated user

    Returns:
        Whether property is saved and when it was saved

    Raises:
        HTTPException: If check fails
    """
    try:
        user_id = current_user.get("id")

        saved_properties_collection = database["saved_properties"]

        # Check if property is saved
        saved_item = await saved_properties_collection.find_one({
            "user_id": user_id,
            "property_id": property_id
        })

        if saved_item:
            return IsSavedResponse(
                is_saved=True,
                saved_at=saved_item.get("saved_at")
            )
        else:
            return IsSavedResponse(
                is_saved=False,
                saved_at=None
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking saved property: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check saved property"
        )


# ========================= BOOKED PROPERTIES ENDPOINTS =========================

@router.get(
    "/me/booked-properties",
    response_model=List[Dict[str, Any]],
    summary="Get properties user has bookings for"
)
async def get_user_booked_properties(
    status_filter: Optional[str] = Query(None, description="Filter by booking status"),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all properties that the current user has bookings for.

    Uses MongoDB aggregation to join bookings with properties.
    Excludes cancelled and no-show bookings by default unless specified.

    Args:
        status_filter: Optional booking status filter
        limit: Maximum number of properties to return (1-100)
        offset: Number of properties to skip
        database: Database instance
        current_user: Current authenticated user

    Returns:
        List of properties with booking information

    Raises:
        HTTPException: If there's an error fetching booked properties
    """
    try:
        user_id = current_user.get("id")

        # Build match criteria
        match_criteria = {"contact_id": user_id}
        if status_filter:
            match_criteria["status"] = status_filter
        else:
            # Default: exclude cancelled and no-show
            match_criteria["status"] = {
                "$nin": ["cancelled", "no-show"]
            }

        # MongoDB aggregation pipeline
        pipeline = [
            {"$match": match_criteria},
            {"$sort": {"scheduled_at": -1}},
            {
                "$lookup": {
                    "from": "properties",
                    "localField": "property_id",
                    "foreignField": "id",
                    "as": "property"
                }
            },
            {"$unwind": "$property"},
            {
                "$group": {
                    "_id": "$property_id",
                    "property": {"$first": "$property"},
                    "booking_count": {"$sum": 1},
                    "latest_booking": {"$first": "$$ROOT"}
                }
            },
            {"$skip": offset},
            {"$limit": limit}
        ]

        bookings_collection = database["bookings"]
        results = await bookings_collection.aggregate(pipeline).to_list(length=limit)

        # Format response
        booked_properties = []
        for result in results:
            property_data = result["property"]
            # Remove MongoDB _id if present
            if "_id" in property_data:
                del property_data["_id"]

            property_data["booking_count"] = result["booking_count"]
            property_data["latest_booking_date"] = result["latest_booking"]["scheduled_at"].isoformat()
            property_data["latest_booking_status"] = result["latest_booking"]["status"]
            booked_properties.append(property_data)

        logger.info(f"Retrieved {len(booked_properties)} booked properties for user {user_id}")
        return booked_properties

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching booked properties: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch booked properties"
        )


# ========================= USER PROFILE ENDPOINTS =========================

@router.get("/me/profile", response_model=UserProfile)
async def get_user_profile(
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get current user's profile information.

    Returns user data from Supabase auth combined with custom profile data
    from MongoDB if it exists.

    Args:
        database: Database instance
        current_user: Current authenticated user from Supabase

    Returns:
        UserProfile with combined data from Supabase and MongoDB
    """
    try:
        user_id = current_user.get("id")
        user_email = current_user.get("email")

        # Try to get profile data from MongoDB users collection
        users_collection = database["users"]
        user_doc = await users_collection.find_one({"id": user_id})

        if user_doc:
            # User profile exists in MongoDB
            return UserProfile(
                id=user_id,
                email=user_email,
                first_name=user_doc.get("first_name"),
                last_name=user_doc.get("last_name"),
                phone=user_doc.get("phone"),
                avatar_url=user_doc.get("avatar_url"),
                created_at=user_doc.get("created_at"),
                updated_at=user_doc.get("updated_at")
            )
        else:
            # No profile in MongoDB yet, return data from Supabase only
            return UserProfile(
                id=user_id,
                email=user_email,
                first_name=None,
                last_name=None,
                phone=None,
                avatar_url=None,
                created_at=datetime.utcnow(),
                updated_at=None
            )

    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )


@router.put("/me/profile", response_model=UserProfile)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update current user's profile information.

    Stores or updates profile data in MongoDB users collection.
    Email cannot be changed through this endpoint (managed by Supabase).

    Args:
        profile_data: Profile fields to update
        database: Database instance
        current_user: Current authenticated user

    Returns:
        Updated UserProfile

    Raises:
        HTTPException: If update fails
    """
    try:
        user_id = current_user.get("id")
        user_email = current_user.get("email")
        users_collection = database["users"]

        # Check if user profile exists
        existing_user = await users_collection.find_one({"id": user_id})

        now = datetime.utcnow()

        if existing_user:
            # Update existing profile
            update_doc = {
                "$set": {
                    "updated_at": now
                }
            }

            # Only update fields that were provided
            if profile_data.first_name is not None:
                update_doc["$set"]["first_name"] = profile_data.first_name
            if profile_data.last_name is not None:
                update_doc["$set"]["last_name"] = profile_data.last_name
            if profile_data.phone is not None:
                update_doc["$set"]["phone"] = profile_data.phone

            await users_collection.update_one(
                {"id": user_id},
                update_doc
            )

            # Get updated profile
            updated_user = await users_collection.find_one({"id": user_id})

            return UserProfile(
                id=user_id,
                email=user_email,
                first_name=updated_user.get("first_name"),
                last_name=updated_user.get("last_name"),
                phone=updated_user.get("phone"),
                avatar_url=updated_user.get("avatar_url"),
                created_at=updated_user.get("created_at"),
                updated_at=updated_user.get("updated_at")
            )
        else:
            # Create new profile
            new_user_doc = {
                "id": user_id,
                "email": user_email,
                "first_name": profile_data.first_name,
                "last_name": profile_data.last_name,
                "phone": profile_data.phone,
                "avatar_url": None,
                "created_at": now,
                "updated_at": now
            }

            await users_collection.insert_one(new_user_doc)

            return UserProfile(
                id=user_id,
                email=user_email,
                first_name=profile_data.first_name,
                last_name=profile_data.last_name,
                phone=profile_data.phone,
                avatar_url=None,
                created_at=now,
                updated_at=now
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )
