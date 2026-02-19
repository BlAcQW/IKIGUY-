"""MongoDB-based authentication service."""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

from fastapi import HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ..models import (
    User, UserSession, SignupRequest, SigninRequest, AuthResponse,
    Organization, OrganizationUser, OrganizationRole
)
from ..utils.auth import (
    hash_password, verify_password, generate_access_token, generate_refresh_token,
    decode_access_token, get_access_token_expire_time, get_refresh_token_expire_time,
    validate_password_strength, sanitize_user_data
)


class AuthService:
    """MongoDB-based authentication service."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users_collection = db.users
        self.sessions_collection = db.user_sessions
        self.organizations_collection = db.organizations
        self.organization_users_collection = db.organization_users

    async def signup(self, signup_data: SignupRequest, request: Request = None) -> AuthResponse:
        """
        Register a new user and create their organization.

        Args:
            signup_data: User signup data
            request: HTTP request for device info

        Returns:
            Authentication response with tokens

        Raises:
            HTTPException: If email already exists or validation fails
        """
        # Validate password strength
        validate_password_strength(signup_data.password)

        # Check if email already exists
        existing_user = await self.users_collection.find_one({"email": signup_data.email.lower()})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create user
        now = datetime.now(timezone.utc)
        from uuid import uuid4
        user_id = str(uuid4())  # Generate UUID for user ID

        user = User(
            id=user_id,
            email=signup_data.email.lower(),
            password_hash=hash_password(signup_data.password),
            first_name=signup_data.first_name or "",
            last_name=signup_data.last_name or "",
            display_name=f"{signup_data.first_name} {signup_data.last_name}".strip() or signup_data.email,
            is_active=True,
            is_verified=False,  # Email verification can be added later
            created_at=now,
            updated_at=now
        )

        # Create organization for the user
        org_name = signup_data.organization_name or f"{user.display_name}'s Organization"
        organization = Organization(
            name=org_name.lower().replace(" ", "-"),
            display_name=org_name,
            description=f"Organization for {user.display_name}",
            is_active=True,
            created_at=now,
            updated_at=now
        )

        # Save user and organization
        try:
            # Insert user
            user_doc = user.model_dump()
            user_doc["_id"] = user_id
            await self.users_collection.insert_one(user_doc)

            # Insert organization
            org_doc = organization.model_dump()
            org_doc["_id"] = organization.id
            await self.organizations_collection.insert_one(org_doc)

            # Create organization membership
            org_user = OrganizationUser(
                organization_id=organization.id,
                user_id=user_id,
                email=user.email,
                role=OrganizationRole.OWNER,
                first_name=user.first_name,
                last_name=user.last_name,
                display_name=user.display_name,
                is_active=True,
                joined_at=now,
                created_at=now,
                updated_at=now
            )

            org_user_doc = org_user.model_dump()
            org_user_doc["_id"] = org_user.id
            await self.organization_users_collection.insert_one(org_user_doc)

            # Update user with primary organization
            await self.users_collection.update_one(
                {"_id": user_id},
                {"$set": {"primary_organization_id": organization.id}}
            )
            user.primary_organization_id = organization.id

        except Exception as e:
            # Cleanup on error
            await self.users_collection.delete_one({"_id": user_id})
            await self.organizations_collection.delete_one({"_id": organization.id})
            await self.organization_users_collection.delete_one({"user_id": user_id})
            raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

        # Generate tokens and create session
        return await self._create_user_session(user, organization, request)

    async def signin(self, signin_data: SigninRequest, request: Request = None) -> AuthResponse:
        """
        Authenticate user and create session.

        Args:
            signin_data: User signin data
            request: HTTP request for device info

        Returns:
            Authentication response with tokens

        Raises:
            HTTPException: If credentials are invalid
        """
        # Find user by email
        user_doc = await self.users_collection.find_one({"email": signin_data.email.lower()})
        if not user_doc:
            # Log for debugging (don't reveal if email exists to prevent enumeration)
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Login attempt with non-existent email: {signin_data.email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")

        user = User(**user_doc)

        # Verify password
        if not verify_password(signin_data.password, user.password_hash):
            # Log for debugging (don't reveal password was wrong to prevent enumeration)
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed password attempt for user: {signin_data.email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Check if user is active
        if not user.is_active:
            raise HTTPException(status_code=401, detail="Account is deactivated")

        # Get user's primary organization
        organization = None
        if user.primary_organization_id:
            org_doc = await self.organizations_collection.find_one({"_id": user.primary_organization_id})
            if org_doc:
                organization = Organization(**org_doc)

        # Update last login
        await self.users_collection.update_one(
            {"_id": user.id},
            {"$set": {"last_login_at": datetime.now(timezone.utc)}}
        )

        # Generate tokens and create session
        return await self._create_user_session(user, organization, request, signin_data.remember_me)

    async def signout(self, token: str) -> Dict[str, Any]:
        """
        Sign out user by invalidating session.

        Args:
            token: JWT access token

        Returns:
            Success message
        """
        try:
            # Decode token to get session info
            payload = decode_access_token(token)
            user_id = payload.get("sub")

            # Invalidate all active sessions for this user
            await self.sessions_collection.update_many(
                {"user_id": user_id, "is_active": True},
                {"$set": {"is_active": False}}
            )

            return {"success": True, "message": "Signed out successfully"}

        except Exception:
            # Even if token is invalid, return success for security
            return {"success": True, "message": "Signed out successfully"}

    async def refresh_token(self, refresh_token: str) -> AuthResponse:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New authentication response

        Raises:
            HTTPException: If refresh token is invalid
        """
        # Find session by refresh token
        session_doc = await self.sessions_collection.find_one({
            "refresh_token": refresh_token,
            "is_active": True,
            "refresh_expires_at": {"$gt": datetime.now(timezone.utc)}
        })

        if not session_doc:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        session = UserSession(**session_doc)

        # Get user
        user_doc = await self.users_collection.find_one({"_id": session.user_id})
        if not user_doc:
            raise HTTPException(status_code=401, detail="User not found")

        user = User(**user_doc)

        # Get organization
        organization = None
        if user.primary_organization_id:
            org_doc = await self.organizations_collection.find_one({"_id": user.primary_organization_id})
            if org_doc:
                organization = Organization(**org_doc)

        # Check if user has universal_admin role
        is_universal_admin = await self._check_user_universal_admin(user.id)

        # Generate new tokens
        user_data = user.model_dump()
        user_data["is_universal_admin"] = is_universal_admin
        access_token = generate_access_token(user_data)
        new_refresh_token = generate_refresh_token()

        # Update session
        expires_at = get_access_token_expire_time()
        refresh_expires_at = get_refresh_token_expire_time()

        await self.sessions_collection.update_one(
            {"_id": session.id},
            {"$set": {
                "token": access_token,
                "refresh_token": new_refresh_token,
                "expires_at": expires_at,
                "refresh_expires_at": refresh_expires_at,
                "last_used_at": datetime.now(timezone.utc)
            }}
        )

        return AuthResponse(
            success=True,
            user=sanitize_user_data(user_data),
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_at=expires_at,
            organization=organization.model_dump() if organization else None,
            message="Token refreshed successfully"
        )

    async def get_current_user(self, token: str) -> Dict[str, Any]:
        """
        Get current user from JWT token.

        Args:
            token: JWT access token

        Returns:
            User data including organization role

        Raises:
            HTTPException: If token is invalid
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.debug(f"Getting current user for token: {token[:20]}...")

        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            logger.debug(f"JWT decoded successfully, user_id: {user_id}")

            # Verify session is still active
            session_query = {
                "user_id": user_id,
                "token": token,
                "is_active": True,
                "expires_at": {"$gt": datetime.now(timezone.utc)}
            }
            logger.debug(f"Looking for session with token check")

            session = await self.sessions_collection.find_one(session_query)

            if not session:
                logger.error(f"No active session found for user {user_id}")
                # Debug: Check if session exists without token match
                session_without_token = await self.sessions_collection.find_one({
                    "user_id": user_id,
                    "is_active": True
                })
                if session_without_token:
                    logger.debug(f"Found session for user but token mismatch. Session token: {session_without_token.get('token', '')[:20]}...")
                else:
                    logger.debug(f"No active session found at all for user {user_id}")
                raise HTTPException(status_code=401, detail="Session expired or invalid")

            logger.debug(f"Session found successfully for user {user_id}")

            # Update last used
            await self.sessions_collection.update_one(
                {"_id": session["_id"]},
                {"$set": {"last_used_at": datetime.now(timezone.utc)}}
            )

            # Get user's organization roles
            org_users = await self.organization_users_collection.find({
                "user_id": user_id,
                "is_active": True
            }).to_list(length=100)

            # Check if user has universal_admin role
            # First check user document directly
            user_doc = await self.users_collection.find_one({"_id": user_id})
            is_universal_admin = user_doc.get("is_universal_admin", False) if user_doc else False

            # Also check organization roles
            roles = [org_user.get("role") for org_user in org_users]
            if not is_universal_admin:
                is_universal_admin = "universal_admin" in roles or "UNIVERSAL_ADMIN" in roles

            # Add role information to payload
            payload["roles"] = roles
            payload["is_universal_admin"] = is_universal_admin
            payload["organization_ids"] = [org_user.get("organization_id") for org_user in org_users]

            logger.debug(f"User roles: {roles}, is_universal_admin: {is_universal_admin}")

            return payload
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in get_current_user: {str(e)}")
            raise

    async def _check_user_universal_admin(self, user_id: str) -> bool:
        """
        Check if user has universal_admin role.

        Args:
            user_id: User ID to check

        Returns:
            True if user has universal_admin role
        """
        # First, check if user has is_universal_admin field set to True
        user_doc = await self.users_collection.find_one({"_id": user_id})
        if user_doc and user_doc.get("is_universal_admin"):
            return True

        # Also check organization memberships for universal_admin role
        org_users = await self.organization_users_collection.find({
            "user_id": user_id,
            "is_active": True
        }).to_list(length=100)

        roles = [org_user.get("role") for org_user in org_users]
        return "universal_admin" in roles or "UNIVERSAL_ADMIN" in roles

    async def _create_user_session(
        self,
        user: User,
        organization: Optional[Organization] = None,
        request: Request = None,
        remember_me: bool = False
    ) -> AuthResponse:
        """
        Create user session and generate tokens.

        Args:
            user: User instance
            organization: User's organization
            request: HTTP request for device info
            remember_me: Extend session duration

        Returns:
            Authentication response
        """
        # Check if user has universal_admin role
        is_universal_admin = await self._check_user_universal_admin(user.id)

        # Generate tokens
        user_data = user.model_dump()
        user_data["is_universal_admin"] = is_universal_admin
        access_token = generate_access_token(user_data)
        refresh_token = generate_refresh_token()

        # Get expiration times
        expires_at = get_access_token_expire_time(remember_me)
        refresh_expires_at = get_refresh_token_expire_time()

        # Create session
        device_info = {}
        user_agent = ""
        ip_address = ""

        if request:
            user_agent = request.headers.get("user-agent", "")
            ip_address = request.client.host if request.client else ""
            device_info = {
                "user_agent": user_agent,
                "ip": ip_address
            }

        session = UserSession(
            user_id=user.id,
            token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            refresh_expires_at=refresh_expires_at,
            device_info=device_info,
            user_agent=user_agent,
            ip_address=ip_address,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            last_used_at=datetime.now(timezone.utc)
        )

        # Save session
        session_doc = session.model_dump()
        session_doc["_id"] = session.id
        await self.sessions_collection.insert_one(session_doc)

        return AuthResponse(
            success=True,
            user=sanitize_user_data(user_data),
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            organization=organization.model_dump() if organization else None,
            message="Authentication successful"
        )

    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        result = await self.sessions_collection.delete_many({
            "expires_at": {"$lt": datetime.now(timezone.utc)}
        })
        return result.deleted_count

    # =============================================================================
    # ADMIN MANAGEMENT FUNCTIONS
    # =============================================================================

    async def get_all_users(
        self,
        search: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """
        Get all users with filtering and pagination (admin function).

        Args:
            search: Search term for email or name
            role: Role filter (not used in MongoDB implementation)
            status: Status filter (active/inactive)
            page: Page number
            per_page: Items per page

        Returns:
            Dictionary with users, total count, and pagination info
        """
        # Build query filters
        query = {}

        if search:
            query["$or"] = [
                {"email": {"$regex": search, "$options": "i"}},
                {"display_name": {"$regex": search, "$options": "i"}}
            ]

        if status:
            query["is_active"] = status == "active"

        # Get total count
        total = await self.users_collection.count_documents(query)

        # Get paginated results
        skip = (page - 1) * per_page
        cursor = self.users_collection.find(query).sort("created_at", -1).skip(skip).limit(per_page)
        users = await cursor.to_list(length=per_page)

        return {
            "users": users,
            "total": total,
            "page": page,
            "per_page": per_page
        }

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user (admin function).

        Args:
            user_data: User creation data

        Returns:
            Created user data

        Raises:
            HTTPException: If email already exists or validation fails
        """
        # Validate password strength
        validate_password_strength(user_data["password"])

        # Check if email already exists
        existing_user = await self.users_collection.find_one({"email": user_data["email"].lower()})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create user object
        import uuid
        user_id = str(uuid.uuid4())

        user = User(
            id=user_id,
            email=user_data["email"].lower(),
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            display_name=f"{user_data['first_name']} {user_data['last_name']}",
            password_hash=hash_password(user_data["password"]),
            is_active=True,
            is_verified=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        # Create organization if specified
        organization = None
        if user_data.get("organization_name"):
            org_id = str(uuid.uuid4())
            organization = Organization(
                id=org_id,
                name=user_data["organization_name"].lower().replace(" ", "-"),
                display_name=user_data["organization_name"],
                description=f"Organization for {user.display_name}",
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )

            # Save organization
            org_doc = organization.model_dump()
            org_doc["_id"] = organization.id
            await self.organizations_collection.insert_one(org_doc)

            user.primary_organization_id = org_id

        # Save user
        user_doc = user.model_dump()
        user_doc["_id"] = user.id
        await self.users_collection.insert_one(user_doc)

        return sanitize_user_data(user_doc)

    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing user (admin function).

        Args:
            user_id: User ID to update
            update_data: Data to update

        Returns:
            Updated user data

        Raises:
            HTTPException: If user not found
        """
        # Reason: Support both string UUIDs and ObjectId for user_id
        try:
            if len(user_id) == 24:  # MongoDB ObjectId is 24 hex characters
                query_id = ObjectId(user_id)
            else:
                query_id = user_id
        except:
            query_id = user_id

        # Prepare update data
        update_fields = {}

        if "first_name" in update_data:
            update_fields["first_name"] = update_data["first_name"]

        if "last_name" in update_data:
            update_fields["last_name"] = update_data["last_name"]

        # Handle display_name - prefer explicit value over auto-generated
        if "display_name" in update_data:
            update_fields["display_name"] = update_data["display_name"]
        elif "first_name" in update_data or "last_name" in update_data:
            # Auto-generate display_name from first_name and last_name if not explicitly provided
            # Reason: Need to get current user data to build complete display_name
            current_user = await self.users_collection.find_one({"_id": query_id})
            if current_user:
                first_name = update_data.get("first_name", current_user.get("first_name", ""))
                last_name = update_data.get("last_name", current_user.get("last_name", ""))
                update_fields["display_name"] = f"{first_name} {last_name}".strip()

        if "is_active" in update_data:
            update_fields["is_active"] = update_data["is_active"]

        if "role" in update_data:
            update_fields["role"] = update_data["role"]

        if "email" in update_data:
            update_fields["email"] = update_data["email"].lower()

        if "email_verified" in update_data:
            update_fields["email_verified"] = update_data["email_verified"]

        update_fields["updated_at"] = datetime.now(timezone.utc)

        # Update user
        result = await self.users_collection.update_one(
            {"_id": query_id},
            {"$set": update_fields}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")

        # Get updated user
        updated_user = await self.users_collection.find_one({"_id": query_id})
        return sanitize_user_data(updated_user)

    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user (admin function).

        Args:
            user_id: User ID to delete

        Returns:
            True if user was deleted

        Raises:
            HTTPException: If user not found
        """
        # Reason: Support both string UUIDs and ObjectId for user_id
        # Try to convert to ObjectId if it looks like a MongoDB ObjectId
        try:
            if len(user_id) == 24:  # MongoDB ObjectId is 24 hex characters
                query_id = ObjectId(user_id)
            else:
                query_id = user_id
        except:
            query_id = user_id

        # Delete user sessions first (try both formats)
        await self.sessions_collection.delete_many({"user_id": user_id})
        await self.sessions_collection.delete_many({"user_id": query_id})

        # Delete user
        result = await self.users_collection.delete_one({"_id": query_id})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")

        return True

    async def reset_password(self, user_id: str, new_password: str) -> bool:
        """
        Reset a user's password (admin function).

        Args:
            user_id: User ID
            new_password: New password

        Returns:
            True if password was reset

        Raises:
            HTTPException: If user not found or validation fails
        """
        # Validate password strength
        validate_password_strength(new_password)

        # Update password
        result = await self.users_collection.update_one(
            {"_id": user_id},
            {"$set": {
                "password_hash": hash_password(new_password),
                "updated_at": datetime.now(timezone.utc)
            }}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")

        # Invalidate all user sessions
        await self.sessions_collection.delete_many({"user_id": user_id})

        return True


# Global service instance
auth_service: Optional[AuthService] = None


async def get_auth_service() -> AuthService:
    """Get the global auth service instance."""
    global auth_service

    if auth_service is None:
        # Initialize MongoDB connection
        import os
        from motor.motor_asyncio import AsyncIOMotorClient

        mongodb_url = os.getenv("MONGODB_URL", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin")
        client = AsyncIOMotorClient(mongodb_url)
        db = client.kasaai_core

        auth_service = AuthService(db)

    return auth_service