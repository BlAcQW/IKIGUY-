"""
Authentication utilities for JWT token handling and password hashing.
"""

from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.models.user import TokenData
from bson import ObjectId

# HTTP Bearer token security
security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)  # Optional authentication (returns None if no token)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password (str): Plain text password.
        hashed_password (str): Hashed password.

    Returns:
        bool: True if password matches, False otherwise.
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """
    Hash a plain password using bcrypt.

    Args:
        password (str): Plain text password.

    Returns:
        str: Hashed password.
    """
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data (dict): Data to encode in the token.
        expires_delta (Optional[timedelta]): Token expiration time delta.

    Returns:
        str: Encoded JWT token.
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token.

    Args:
        data (dict): Data to encode in the token.

    Returns:
        str: Encoded JWT refresh token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """
    Decode and verify a JWT token.

    Args:
        token (str): JWT token to decode.

    Returns:
        TokenData: Decoded token data.

    Raises:
        HTTPException: If token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("user_id")
        email: str = payload.get("email")
        role: str = payload.get("role")

        if user_id is None or email is None:
            raise credentials_exception

        token_data = TokenData(user_id=user_id, email=email, role=role)
        return token_data

    except JWTError:
        raise credentials_exception


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    """
    Get the current authenticated user from the JWT token.

    Args:
        credentials (HTTPAuthorizationCredentials): HTTP Authorization credentials.

    Returns:
        TokenData: Current user token data.

    Raises:
        HTTPException: If token is invalid or expired.
    """
    token = credentials.credentials
    return decode_token(token)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
) -> Optional[TokenData]:
    """
    Get the current authenticated user from the JWT token (optional).
    Returns None if no credentials are provided.

    Args:
        credentials (Optional[HTTPAuthorizationCredentials]): HTTP Authorization credentials.

    Returns:
        Optional[TokenData]: Current user token data or None if not authenticated.

    Raises:
        HTTPException: If token is provided but invalid or expired.
    """
    if credentials is None:
        return None

    token = credentials.credentials
    return decode_token(token)


async def get_current_author(
    current_user: TokenData = Depends(get_current_user),
) -> TokenData:
    """
    Get the current authenticated user (author).
    Any authenticated user can be an author and create devotionals.

    Args:
        current_user (TokenData): Current user from token.

    Returns:
        TokenData: Current user token data.

    Note:
        This function simply ensures the user is authenticated.
        All authenticated users can create devotionals.
    """
    # Any authenticated user can be an author
    return current_user


async def get_current_admin(
    current_user: TokenData = Depends(get_current_user),
) -> TokenData:
    """
    Get the current authenticated admin.
    Ensures the user has the 'admin' role.

    Args:
        current_user (TokenData): Current user from token.

    Returns:
        TokenData: Current admin token data.

    Raises:
        HTTPException: If user is not an admin.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Admin role required.",
        )
    return current_user


async def get_current_author_or_admin(
    current_user: TokenData = Depends(get_current_user),
) -> TokenData:
    """
    Get the current authenticated user (author or admin).
    All authenticated users can create content.
    Admins have additional privileges.

    Args:
        current_user (TokenData): Current user from token.

    Returns:
        TokenData: Current user token data.

    Note:
        This function simply ensures the user is authenticated.
        All authenticated users can be authors.
    """
    # All authenticated users can be authors
    # Admins have role == "admin", regular users have role == "user"
    return current_user


async def verify_devotional_author(
    devotional_author_id: str,
    current_user: TokenData = Depends(get_current_author),
) -> bool:
    """
    Verify that the current user is the author of the devotional.

    Args:
        devotional_author_id (str): Author ID of the devotional.
        current_user (TokenData): Current authenticated user.

    Returns:
        bool: True if user is the author.

    Raises:
        HTTPException: If user is not the author.
    """
    if str(devotional_author_id) != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. You can only edit your own devotionals.",
        )
    return True
