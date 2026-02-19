"""Authentication utilities for password hashing and JWT management."""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

import bcrypt
import jwt
from fastapi import HTTPException


# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET_KEY", os.getenv("JWT_SECRET", "your-secret-key-change-in-production"))
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_HOURS = 24
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 30


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def generate_access_token(user_data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Generate a JWT access token.

    Args:
        user_data: User data to encode in token
        expires_delta: Custom expiration time

    Returns:
        JWT token string
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=JWT_ACCESS_TOKEN_EXPIRE_HOURS)

    # Create JWT payload
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_data.get("id"),  # Subject (user ID)
        "email": user_data.get("email"),
        "name": user_data.get("display_name", user_data.get("email", "Unknown")),
        "user_metadata": {
            "first_name": user_data.get("first_name", ""),
            "last_name": user_data.get("last_name", ""),
            "avatar_url": user_data.get("avatar_url", "")
        },
        "app_metadata": user_data.get("metadata", {}),
        "role": "authenticated",
        "aud": "kasaai-core",
        "iss": "kasaai-auth",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "organization_id": user_data.get("primary_organization_id")
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def generate_refresh_token() -> str:
    """
    Generate a secure refresh token.

    Returns:
        Random secure token string
    """
    return secrets.token_urlsafe(32)


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        # Debug: Log token info (first 20 chars for security)
        logger.debug(f"Decoding JWT token: {token[:20]}...")
        logger.debug(f"JWT_SECRET configured: {bool(JWT_SECRET and JWT_SECRET != 'your-secret-key-change-in-production')}")

        # Decode without audience verification for now
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"verify_aud": False}
        )

        # Debug: Log decoded payload structure
        logger.debug(f"JWT payload keys: {list(payload.keys())}")
        logger.debug(f"JWT issuer: {payload.get('iss')}")
        logger.debug(f"JWT audience: {payload.get('aud')}")
        logger.debug(f"JWT subject: {payload.get('sub')}")
        logger.debug(f"JWT email: {payload.get('email')}")

        # Validate required fields
        if not payload.get("sub"):
            logger.error("JWT validation failed: missing user ID (sub)")
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")

        if not payload.get("email"):
            logger.error("JWT validation failed: missing email")
            raise HTTPException(status_code=401, detail="Invalid token: missing email")

        return payload

    except jwt.ExpiredSignatureError as e:
        # Reason: JWT expiration is expected behavior, not an error - log as warning
        logger.warning(f"JWT expired: {str(e)}")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        logger.error(f"JWT invalid token error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"JWT unexpected error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Token validation failed: {str(e)}")


def get_access_token_expire_time(remember_me: bool = False) -> datetime:
    """
    Get access token expiration time.

    Args:
        remember_me: If True, extend token duration

    Returns:
        Expiration datetime
    """
    hours = JWT_ACCESS_TOKEN_EXPIRE_HOURS
    if remember_me:
        hours = hours * 7  # 7 days for "remember me"

    return datetime.now(timezone.utc) + timedelta(hours=hours)


def get_refresh_token_expire_time() -> datetime:
    """
    Get refresh token expiration time.

    Returns:
        Expiration datetime
    """
    return datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)


def generate_password_reset_token(email: str) -> str:
    """
    Generate a password reset token.

    Args:
        email: User email

    Returns:
        Password reset token
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=1)  # 1 hour expiry

    payload = {
        "email": email,
        "purpose": "password_reset",
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp())
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_password_reset_token(token: str) -> str:
    """
    Verify and decode a password reset token.

    Args:
        token: Password reset token

    Returns:
        Email from token

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        if payload.get("purpose") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid token purpose")

        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid token: missing email")

        return email

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Password reset token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid password reset token")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token validation failed: {str(e)}")


def validate_password_strength(password: str) -> bool:
    """
    Validate password strength.

    Args:
        password: Password to validate

    Returns:
        True if password meets requirements

    Raises:
        HTTPException: If password doesn't meet requirements
    """
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")

    # Check for at least one number and one letter
    has_digit = any(char.isdigit() for char in password)
    has_letter = any(char.isalpha() for char in password)

    if not (has_digit and has_letter):
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least one letter and one number"
        )

    return True


def sanitize_user_data(user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize user data for client response (remove sensitive fields).

    Args:
        user: User data dictionary

    Returns:
        Sanitized user data
    """
    safe_fields = [
        "id", "email", "first_name", "last_name", "display_name",
        "avatar_url", "is_active", "is_verified", "email_verified_at",
        "primary_organization_id", "last_login_at", "created_at", "updated_at",
        "is_universal_admin"  # Include universal admin role flag
    ]

    return {field: user.get(field) for field in safe_fields if field in user}