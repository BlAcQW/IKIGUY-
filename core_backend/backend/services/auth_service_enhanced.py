"""Enhanced MongoDB-based authentication service with comprehensive error handling."""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple, List
import asyncio
import logging

from fastapi import HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError, ConnectionFailure, ServerSelectionTimeoutError

from ..models import (
    User, UserSession, SignupRequest, SigninRequest, AuthResponse,
    Organization, OrganizationUser, OrganizationRole, OrganizationCreate
)
from ..utils.auth import (
    hash_password, verify_password, generate_access_token, generate_refresh_token,
    decode_access_token, get_access_token_expire_time, get_refresh_token_expire_time,
    validate_password_strength, sanitize_user_data
)
from ..utils.error_handling import (
    handle_auth_errors, handle_database_errors, AuthenticationError, DatabaseError,
    ValidationError, ErrorCode, ValidationHelper, ErrorRecovery, security_monitor
)

logger = logging.getLogger(__name__)


class EnhancedAuthService:
    """Enhanced MongoDB-based authentication service with comprehensive error handling."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users_collection = db.users
        self.sessions_collection = db.user_sessions
        self.organizations_collection = db.organizations
        self.organization_users_collection = db.organization_users
        self.password_reset_collection = db.password_resets
        self.email_verification_collection = db.email_verifications

    @handle_auth_errors
    @handle_database_errors
    async def signup(self, signup_data: SignupRequest, request: Request = None) -> AuthResponse:
        """
        Register a new user with enhanced validation and error handling.

        Args:
            signup_data: User signup data
            request: HTTP request for device info

        Returns:
            Authentication response with tokens

        Raises:
            AuthenticationError: If signup fails
            ValidationError: If data validation fails
            DatabaseError: If database operation fails
        """
        try:
            # Enhanced validation
            ValidationHelper.validate_email(signup_data.email)
            ValidationHelper.validate_password(signup_data.password)

            # Sanitize email
            email = signup_data.email.lower().strip()

            # Check for existing user with retry mechanism
            existing_user = await ErrorRecovery.retry_database_operation(
                lambda: self.users_collection.find_one({"email": email})
            )

            if existing_user:
                raise AuthenticationError(
                    message="Email address is already registered",
                    error_code=ErrorCode.EMAIL_ALREADY_EXISTS,
                    status_code=409,
                    details={"email": email}
                )

            # Check for rate limiting
            ip_address = self._get_client_ip(request)
            if security_monitor.is_ip_suspicious(ip_address):
                raise AuthenticationError(
                    message="Too many signup attempts from this IP address",
                    error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
                    status_code=429
                )

            # Create user with enhanced data
            user = User(
                email=email,
                password_hash=hash_password(signup_data.password),
                display_name=signup_data.display_name or email.split('@')[0],
                first_name=signup_data.first_name or "",
                last_name=signup_data.last_name or "",
                is_active=True,
                email_verified=False,  # Require email verification
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                last_login_at=None,
                login_count=0,
                failed_login_attempts=0
            )

            # Create organization
            org_name = signup_data.organization_name or f"{user.display_name}'s Organization"
            ValidationHelper.validate_organization_name(org_name)

            organization = Organization(
                name=org_name,
                display_name=org_name,
                description="Default organization created during signup",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                is_active=True
            )

            # Use transaction for atomicity
            async with await self.db.client.start_session() as session:
                async with session.start_transaction():
                    # Insert user
                    try:
                        await self.users_collection.insert_one(
                            user.model_dump(), session=session
                        )
                    except DuplicateKeyError:
                        raise AuthenticationError(
                            message="Email address is already registered",
                            error_code=ErrorCode.EMAIL_ALREADY_EXISTS,
                            status_code=409
                        )

                    # Insert organization
                    await self.organizations_collection.insert_one(
                        organization.model_dump(), session=session
                    )

                    # Create organization membership
                    org_user = OrganizationUser(
                        organization_id=organization.id,
                        user_id=user.id,
                        email=user.email,
                        role=OrganizationRole.OWNER,
                        display_name=user.display_name,
                        is_active=True,
                        joined_at=datetime.now(timezone.utc)
                    )

                    await self.organization_users_collection.insert_one(
                        org_user.model_dump(), session=session
                    )

                    # Update user with organization ID
                    await self.users_collection.update_one(
                        {"_id": user.id},
                        {"$set": {"primary_organization_id": organization.id}},
                        session=session
                    )

            # Generate tokens
            user_data = sanitize_user_data(user.model_dump())
            access_token = generate_access_token(user_data)
            refresh_token = generate_refresh_token()

            # Create session
            await self._create_session(user.id, access_token, refresh_token, request)

            # Schedule email verification (async)
            asyncio.create_task(self._send_verification_email(user.email, user.id))

            logger.info(f"User successfully registered: {user.email}")

            return AuthResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                user=user_data,
                organization=organization.model_dump()
            )

        except (AuthenticationError, ValidationError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error during signup: {str(e)}")
            raise AuthenticationError(
                message="Signup failed due to an internal error",
                error_code=ErrorCode.INTERNAL_ERROR,
                status_code=500,
                original_error=e
            )

    @handle_auth_errors
    @handle_database_errors
    async def signin(self, signin_data: SigninRequest, request: Request = None) -> AuthResponse:
        """
        Authenticate user with enhanced security and error handling.

        Args:
            signin_data: User signin data
            request: HTTP request for device info

        Returns:
            Authentication response with tokens

        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Validate input
            ValidationHelper.validate_email(signin_data.email)
            email = signin_data.email.lower().strip()
            ip_address = self._get_client_ip(request)

            # Check for suspicious activity
            if security_monitor.is_ip_suspicious(ip_address):
                raise AuthenticationError(
                    message="Account temporarily locked due to suspicious activity",
                    error_code=ErrorCode.ACCOUNT_LOCKED,
                    status_code=423
                )

            # Find user with retry mechanism
            user_doc = await ErrorRecovery.retry_database_operation(
                lambda: self.users_collection.find_one({"email": email})
            )

            if not user_doc:
                # Record failed attempt even for non-existent users
                security_monitor.record_failed_login(email, ip_address)
                raise AuthenticationError(
                    message="Invalid email or password",
                    error_code=ErrorCode.INVALID_CREDENTIALS,
                    status_code=401
                )

            user = User(**user_doc)

            # Check if user is active
            if not user.is_active:
                raise AuthenticationError(
                    message="Account has been deactivated",
                    error_code=ErrorCode.USER_INACTIVE,
                    status_code=403
                )

            # Check if account is locked
            if user.locked_until and user.locked_until > datetime.now(timezone.utc):
                raise AuthenticationError(
                    message="Account is temporarily locked due to multiple failed login attempts",
                    error_code=ErrorCode.ACCOUNT_LOCKED,
                    status_code=423,
                    details={"locked_until": user.locked_until.isoformat()}
                )

            # Verify password
            if not verify_password(signin_data.password, user.password_hash):
                # Record failed attempt
                is_suspicious = security_monitor.record_failed_login(email, ip_address)

                # Update failed login attempts
                failed_attempts = user.failed_login_attempts + 1
                update_data = {
                    "failed_login_attempts": failed_attempts,
                    "updated_at": datetime.now(timezone.utc)
                }

                # Lock account after 5 failed attempts
                if failed_attempts >= 5:
                    lock_duration = timedelta(minutes=15)  # Lock for 15 minutes
                    update_data["locked_until"] = datetime.now(timezone.utc) + lock_duration

                await self.users_collection.update_one(
                    {"_id": user.id},
                    {"$set": update_data}
                )

                raise AuthenticationError(
                    message="Invalid email or password",
                    error_code=ErrorCode.INVALID_CREDENTIALS,
                    status_code=401,
                    details={"attempts_remaining": max(0, 5 - failed_attempts)}
                )

            # Check email verification (optional enforcement)
            if not user.email_verified:
                logger.warning(f"User {email} signed in without email verification")
                # Could enforce email verification here if needed

            # Clear security flags on successful login
            security_monitor.clear_failed_attempts(email, ip_address)

            # Reset failed login attempts
            await self.users_collection.update_one(
                {"_id": user.id},
                {
                    "$set": {
                        "failed_login_attempts": 0,
                        "last_login_at": datetime.now(timezone.utc),
                        "login_count": user.login_count + 1,
                        "updated_at": datetime.now(timezone.utc)
                    },
                    "$unset": {"locked_until": ""}
                }
            )

            # Get organization
            organization = None
            if user.primary_organization_id:
                org_doc = await self.organizations_collection.find_one(
                    {"_id": user.primary_organization_id}
                )
                if org_doc:
                    organization = Organization(**org_doc)

            # Generate tokens
            user_data = sanitize_user_data(user.model_dump())
            access_token = generate_access_token(user_data)
            refresh_token = generate_refresh_token()

            # Create session
            await self._create_session(user.id, access_token, refresh_token, request)

            logger.info(f"User successfully signed in: {user.email}")

            return AuthResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                user=user_data,
                organization=organization.model_dump() if organization else None
            )

        except (AuthenticationError, ValidationError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error during signin: {str(e)}")
            raise AuthenticationError(
                message="Sign in failed due to an internal error",
                error_code=ErrorCode.INTERNAL_ERROR,
                status_code=500,
                original_error=e
            )

    @handle_auth_errors
    @handle_database_errors
    async def refresh_token(self, refresh_token: str) -> AuthResponse:
        """
        Refresh access token with enhanced validation.

        Args:
            refresh_token: Refresh token

        Returns:
            New authentication response

        Raises:
            AuthenticationError: If refresh token is invalid
        """
        try:
            # Find session by refresh token with retry
            session_doc = await ErrorRecovery.retry_database_operation(
                lambda: self.sessions_collection.find_one({
                    "refresh_token": refresh_token,
                    "is_active": True,
                    "refresh_expires_at": {"$gt": datetime.now(timezone.utc)}
                })
            )

            if not session_doc:
                raise AuthenticationError(
                    message="Invalid or expired refresh token",
                    error_code=ErrorCode.TOKEN_INVALID,
                    status_code=401
                )

            session = UserSession(**session_doc)

            # Get user
            user_doc = await self.users_collection.find_one({"_id": session.user_id})
            if not user_doc:
                raise AuthenticationError(
                    message="User not found",
                    error_code=ErrorCode.USER_NOT_FOUND,
                    status_code=401
                )

            user = User(**user_doc)

            # Check if user is still active
            if not user.is_active:
                # Deactivate all sessions for inactive user
                await self.sessions_collection.update_many(
                    {"user_id": user.id},
                    {"$set": {"is_active": False}}
                )
                raise AuthenticationError(
                    message="Account has been deactivated",
                    error_code=ErrorCode.USER_INACTIVE,
                    status_code=403
                )

            # Get organization
            organization = None
            if user.primary_organization_id:
                org_doc = await self.organizations_collection.find_one(
                    {"_id": user.primary_organization_id}
                )
                if org_doc:
                    organization = Organization(**org_doc)

            # Generate new tokens
            user_data = sanitize_user_data(user.model_dump())
            new_access_token = generate_access_token(user_data)
            new_refresh_token = generate_refresh_token()

            # Update session
            expires_at = get_access_token_expire_time()
            refresh_expires_at = get_refresh_token_expire_time()

            await self.sessions_collection.update_one(
                {"_id": session.id},
                {
                    "$set": {
                        "access_token": new_access_token,
                        "refresh_token": new_refresh_token,
                        "expires_at": expires_at,
                        "refresh_expires_at": refresh_expires_at,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )

            logger.info(f"Token refreshed for user: {user.email}")

            return AuthResponse(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                user=user_data,
                organization=organization.model_dump() if organization else None
            )

        except (AuthenticationError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {str(e)}")
            raise AuthenticationError(
                message="Token refresh failed due to an internal error",
                error_code=ErrorCode.INTERNAL_ERROR,
                status_code=500,
                original_error=e
            )

    @handle_auth_errors
    @handle_database_errors
    async def get_current_user(self, token: str) -> Dict[str, Any]:
        """
        Get current user from access token with enhanced validation.

        Args:
            token: Access token

        Returns:
            User data

        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            # Decode token
            try:
                payload = decode_access_token(token)
            except Exception:
                raise AuthenticationError(
                    message="Invalid access token",
                    error_code=ErrorCode.TOKEN_INVALID,
                    status_code=401
                )

            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationError(
                    message="Invalid token payload",
                    error_code=ErrorCode.TOKEN_INVALID,
                    status_code=401
                )

            # Check if session exists and is active
            session_doc = await self.sessions_collection.find_one({
                "user_id": user_id,
                "access_token": token,
                "is_active": True,
                "expires_at": {"$gt": datetime.now(timezone.utc)}
            })

            if not session_doc:
                raise AuthenticationError(
                    message="Session not found or expired",
                    error_code=ErrorCode.SESSION_EXPIRED,
                    status_code=401
                )

            # Get user
            user_doc = await ErrorRecovery.retry_database_operation(
                lambda: self.users_collection.find_one({"_id": user_id})
            )

            if not user_doc:
                raise AuthenticationError(
                    message="User not found",
                    error_code=ErrorCode.USER_NOT_FOUND,
                    status_code=401
                )

            user = User(**user_doc)

            # Check if user is still active
            if not user.is_active:
                raise AuthenticationError(
                    message="Account has been deactivated",
                    error_code=ErrorCode.USER_INACTIVE,
                    status_code=403
                )

            # Update last activity
            await self.sessions_collection.update_one(
                {"_id": session_doc["_id"]},
                {"$set": {"last_activity": datetime.now(timezone.utc)}}
            )

            return sanitize_user_data(user.model_dump())

        except (AuthenticationError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting current user: {str(e)}")
            raise AuthenticationError(
                message="Failed to get current user",
                error_code=ErrorCode.INTERNAL_ERROR,
                status_code=500,
                original_error=e
            )

    @handle_auth_errors
    @handle_database_errors
    async def signout(self, access_token: str) -> Dict[str, str]:
        """
        Sign out user and invalidate session.

        Args:
            access_token: Access token

        Returns:
            Success message
        """
        try:
            # Find and deactivate session
            result = await self.sessions_collection.update_one(
                {"access_token": access_token, "is_active": True},
                {
                    "$set": {
                        "is_active": False,
                        "signed_out_at": datetime.now(timezone.utc)
                    }
                }
            )

            if result.modified_count == 0:
                logger.warning("Attempted to sign out with invalid or already inactive token")

            return {"message": "Successfully signed out"}

        except Exception as e:
            logger.error(f"Error during signout: {str(e)}")
            # Don't raise error for signout - just log and return success
            return {"message": "Successfully signed out"}

    async def _create_session(
        self,
        user_id: str,
        access_token: str,
        refresh_token: str,
        request: Request = None
    ) -> UserSession:
        """Create a new user session with device tracking."""
        device_info = self._extract_device_info(request) if request else {}

        session = UserSession(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=get_access_token_expire_time(),
            refresh_expires_at=get_refresh_token_expire_time(),
            ip_address=self._get_client_ip(request),
            user_agent=device_info.get("user_agent", ""),
            device_id=device_info.get("device_id", ""),
            is_active=True,
            created_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc)
        )

        await self.sessions_collection.insert_one(session.model_dump())
        return session

    def _get_client_ip(self, request: Request = None) -> str:
        """Extract client IP address from request."""
        if not request:
            return "unknown"

        # Check for forwarded IP first (reverse proxy)
        forwarded_ip = request.headers.get("X-Forwarded-For")
        if forwarded_ip:
            return forwarded_ip.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return getattr(request.client, "host", "unknown")

    def _extract_device_info(self, request: Request) -> Dict[str, str]:
        """Extract device information from request headers."""
        if not request:
            return {}

        user_agent = request.headers.get("User-Agent", "")
        device_id = request.headers.get("X-Device-ID", "")

        return {
            "user_agent": user_agent,
            "device_id": device_id
        }

    async def _send_verification_email(self, email: str, user_id: str):
        """Send email verification (placeholder for email service integration)."""
        # TODO: Implement email service integration
        logger.info(f"Email verification should be sent to {email} for user {user_id}")

    # Additional methods for password reset, email verification, etc.
    # These would be implemented as part of the full migration plan