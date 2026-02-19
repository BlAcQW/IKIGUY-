"""
Authentication utilities.

Local JWT authentication - no external services required.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.config import settings
from app.core.database import get_database

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> Optional[Dict[str, Any]]:
    """Get a user by email from the database."""
    user = await db.users.find_one({"email": email.lower()})
    return user


async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> Optional[Dict[str, Any]]:
    """Get a user by ID from the database."""
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        return user
    except Exception:
        return None


async def authenticate_user(db: AsyncIOMotorDatabase, email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user with email and password.
    
    Args:
        db: Database instance
        email: User email
        password: Plain text password
        
    Returns:
        User dict if authenticated, None otherwise
    """
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.get("password_hash", "")):
        return None
    return user


async def create_user(
    db: AsyncIOMotorDatabase,
    email: str,
    password: str,
    first_name: str = "",
    last_name: str = "",
    role: str = "user",
    organization_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new user in the database.
    
    Args:
        db: Database instance
        email: User email
        password: Plain text password
        first_name: User's first name
        last_name: User's last name
        role: User role (admin, manager, agent, user)
        organization_id: Optional organization ID
        
    Returns:
        Created user dict
    """
    # Check if user already exists
    existing = await get_user_by_email(db, email)
    if existing:
        raise ValueError("User with this email already exists")
    
    user_doc = {
        "email": email.lower(),
        "password_hash": get_password_hash(password),
        "first_name": first_name,
        "last_name": last_name,
        "role": role,
        "organization_id": organization_id,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    
    return user_doc


async def ensure_default_admin(db: AsyncIOMotorDatabase):
    """
    Ensure the default admin user exists.
    Creates it if it doesn't exist.
    """
    admin = await get_user_by_email(db, settings.DEFAULT_ADMIN_EMAIL)
    if not admin:
        try:
            await create_user(
                db,
                email=settings.DEFAULT_ADMIN_EMAIL,
                password=settings.DEFAULT_ADMIN_PASSWORD,
                first_name="Admin",
                last_name="User",
                role="admin"
            )
            logger.info(f"Created default admin user: {settings.DEFAULT_ADMIN_EMAIL}")
        except Exception as e:
            logger.error(f"Failed to create default admin: {e}")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User information dictionary
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise credentials_exception
    
    # Get user from database
    db = await get_database()
    user = await get_user_by_id(db, user_id)
    
    if user is None:
        raise credentials_exception
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    # Return user data in standard format
    return {
        "id": str(user["_id"]),
        "sub": str(user["_id"]),
        "email": user.get("email"),
        "first_name": user.get("first_name", ""),
        "last_name": user.get("last_name", ""),
        "role": user.get("role", "user"),
        "organization_id": user.get("organization_id") or str(user["_id"]),
    }


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict[str, Any]]:
    """
    Get current user if authenticated, None otherwise.
    
    Args:
        credentials: Optional HTTP authorization credentials
        
    Returns:
        User information dictionary or None
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def get_organization_context(
    request: Request,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Get organization context from authenticated user.
    
    Args:
        request: FastAPI request object
        user: Current authenticated user
        
    Returns:
        Organization context dictionary with organization_id
        
    Notes:
        If user doesn't have an organization_id,
        uses their user ID as the organization_id (single-user org).
        
        Admin users can override organization by sending X-Organization-Id header.
    """
    # Get organization_id from user, or use user ID as org ID
    organization_id = user.get("organization_id") or user.get("id") or user.get("sub")
    
    # Allow admin users to override organization via header
    if user.get("role") == "admin":
        override_org_id = request.headers.get("x-organization-id")
        if override_org_id:
            logger.info(f"Admin user {user.get('email')} switched to organization {override_org_id}")
            organization_id = override_org_id
    
    return {
        "organization_id": organization_id,
        "user_id": user.get("id") or user.get("sub")
    }


async def get_optional_organization_context(
    request: Request,
    user: Optional[Dict[str, Any]] = Depends(get_optional_user)
) -> Optional[Dict[str, str]]:
    """
    Get organization context from user if authenticated, None otherwise.
    
    Args:
        request: FastAPI request object
        user: Optional current authenticated user
        
    Returns:
        Organization context dictionary or None
    """
    if not user:
        return None
    
    # Get organization_id from user, or use user ID as org ID
    organization_id = user.get("organization_id") or user.get("id") or user.get("sub")
    
    # Allow admin users to override organization via header
    if user.get("role") == "admin":
        override_org_id = request.headers.get("x-organization-id")
        if override_org_id:
            logger.info(f"Admin user {user.get('email')} switched to organization {override_org_id}")
            organization_id = override_org_id
    
    return {
        "organization_id": organization_id,
        "user_id": user.get("id") or user.get("sub")
    }
