"""
API Key Management Service

Provides secure API key generation, validation, and management for programmatic access.

Features:
- Secure key generation with bcrypt hashing
- Scope-based permissions
- Rate limiting per key
- Usage tracking
- Key revocation

Created: 2025-10-27
Sprint 5: Analytics & Ecosystem (Phase 8)
"""

import logging
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pydantic import BaseModel, Field
from bson import ObjectId
import os
import bcrypt

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models
# ============================================================================

class APIKey(BaseModel):
    """API key model with security features."""
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str
    organization_id: Optional[str] = None  # Organization scope for multi-tenant isolation
    name: str  # e.g., "Production", "Development"
    key_hash: str  # bcrypt hash of the full key
    key_prefix: str  # First 8 chars for display (kas_12345678...)
    scopes: List[str] = Field(default_factory=list)  # ["tts:synthesize", "tts:history"]
    rate_limit: int = 100  # Requests per minute
    last_used_at: Optional[datetime] = None
    request_count: int = 0  # Total requests made with this key
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    revoked: bool = False

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }


class APIKeyCreate(BaseModel):
    """Request model for creating a new API key."""
    name: str
    scopes: List[str] = Field(default_factory=lambda: ["tts:synthesize"])
    rate_limit: int = 100
    expires_in_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    """Response model for API key (without sensitive data)."""
    id: str
    name: str
    key_prefix: str
    scopes: List[str]
    rate_limit: int
    last_used_at: Optional[datetime]
    request_count: int
    created_at: datetime
    expires_at: Optional[datetime]
    revoked: bool


class APIKeyWithSecret(APIKeyResponse):
    """Response model with full API key (only returned once at creation)."""
    api_key: str


class APIKeyUsageStats(BaseModel):
    """Usage statistics for an API key."""
    key_id: str
    key_name: str
    total_requests: int
    requests_last_24h: int
    requests_last_7d: int
    last_used_at: Optional[datetime]
    created_at: datetime


# ============================================================================
# API Key Service
# ============================================================================

class APIKeyService:
    """Service for managing API keys."""

    # Available scopes
    AVAILABLE_SCOPES = [
        "tts:synthesize",      # Can synthesize speech
        "tts:clone",           # Can use voice cloning
        "tts:history",         # Can access history
        "tts:estimate",        # Can estimate costs
        "tts:providers",       # Can list providers
        "tts:voices",          # Can list voices
    ]

    # Key format constants
    KEY_PREFIX = "kas_"
    KEY_LENGTH = 32  # Length of random part (in bytes)

    def __init__(self):
        """Initialize API key service with MongoDB connection."""
        # MongoDB connection
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.client = AsyncIOMotorClient(mongodb_url)
        self.db = self.client[os.getenv("MONGODB_DATABASE", "kasaai_core")]
        self.collection: AsyncIOMotorCollection = self.db["api_keys"]

        logger.info("APIKeyService initialized")

    async def create_indexes(self):
        """Create database indexes for efficient queries."""
        try:
            # Index for organization + user queries
            await self.collection.create_index([
                ("organization_id", 1),
                ("user_id", 1),
                ("revoked", 1)
            ])

            # Index for user queries (backward compatibility)
            await self.collection.create_index([
                ("user_id", 1),
                ("revoked", 1)
            ])

            # Index for organization queries
            await self.collection.create_index("organization_id")

            # Index for key prefix lookup (for display)
            await self.collection.create_index("key_prefix")

            # Index for key hash lookup (for authentication)
            await self.collection.create_index("key_hash")

            # TTL index for expired keys
            await self.collection.create_index(
                "expires_at",
                expireAfterSeconds=0
            )

            logger.info("API key indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")

    def _generate_api_key(self) -> tuple[str, str, str]:
        """
        Generate a new API key.

        Returns:
            tuple: (full_key, key_hash, key_prefix)
        """
        # Generate random bytes
        random_bytes = secrets.token_bytes(self.KEY_LENGTH)

        # Convert to hex string
        random_hex = random_bytes.hex()

        # Create full key with prefix
        full_key = f"{self.KEY_PREFIX}{random_hex}"

        # Hash the key with bcrypt
        key_hash = bcrypt.hashpw(full_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Create display prefix (first 8 chars after prefix)
        key_prefix = f"{self.KEY_PREFIX}{random_hex[:8]}..."

        return full_key, key_hash, key_prefix

    async def create_api_key(
        self,
        user_id: str,
        name: str,
        scopes: List[str] = None,
        rate_limit: int = 100,
        expires_in_days: Optional[int] = None,
        organization_id: Optional[str] = None
    ) -> APIKeyWithSecret:
        """
        Create a new API key for a user.

        Args:
            user_id: User ID
            name: Descriptive name for the key
            scopes: List of permission scopes
            rate_limit: Requests per minute
            expires_in_days: Optional expiration in days
            organization_id: Organization ID for multi-tenant isolation

        Returns:
            APIKeyWithSecret: Created API key with full secret
        """
        try:
            # Validate scopes
            if scopes is None:
                scopes = ["tts:synthesize"]

            invalid_scopes = [s for s in scopes if s not in self.AVAILABLE_SCOPES]
            if invalid_scopes:
                raise ValueError(f"Invalid scopes: {invalid_scopes}")

            # Generate key
            full_key, key_hash, key_prefix = self._generate_api_key()

            # Calculate expiration
            expires_at = None
            if expires_in_days:
                expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

            # Create API key document
            api_key = APIKey(
                user_id=user_id,
                organization_id=organization_id,
                name=name,
                key_hash=key_hash,
                key_prefix=key_prefix,
                scopes=scopes,
                rate_limit=rate_limit,
                expires_at=expires_at,
                revoked=False
            )

            # Insert into database
            # Convert to dict and ensure _id is ObjectId (not string)
            doc = api_key.dict(by_alias=True)
            if "_id" in doc and isinstance(doc["_id"], str):
                doc["_id"] = ObjectId(doc["_id"])
            result = await self.collection.insert_one(doc)

            logger.info(
                f"Created API key: user={user_id}, organization={organization_id}, "
                f"name={name}, scopes={scopes}, prefix={key_prefix}"
            )

            # Return with full key (only time it's shown)
            return APIKeyWithSecret(
                id=str(result.inserted_id),
                name=api_key.name,
                key_prefix=api_key.key_prefix,
                scopes=api_key.scopes,
                rate_limit=api_key.rate_limit,
                last_used_at=api_key.last_used_at,
                request_count=api_key.request_count,
                created_at=api_key.created_at,
                expires_at=api_key.expires_at,
                revoked=api_key.revoked,
                api_key=full_key
            )

        except Exception as e:
            logger.error(f"Error creating API key for organization={organization_id}: {e}")
            raise

    async def verify_api_key(self, api_key: str) -> Optional[APIKey]:
        """
        Verify an API key and return its details.

        Args:
            api_key: Full API key string

        Returns:
            Optional[APIKey]: API key details if valid, None otherwise
        """
        try:
            # Find all non-revoked keys (we need to check hash for each)
            cursor = self.collection.find({
                "revoked": False
            })

            async for doc in cursor:
                stored_hash = doc.get("key_hash")

                # Check if key matches hash
                if bcrypt.checkpw(api_key.encode('utf-8'), stored_hash.encode('utf-8')):
                    # Check expiration
                    if doc.get("expires_at"):
                        expires_at = doc["expires_at"]
                        if datetime.now(timezone.utc) > expires_at:
                            logger.warning(f"API key expired: {doc['key_prefix']}")
                            return None

                    # Update last used timestamp and request count
                    await self.collection.update_one(
                        {"_id": doc["_id"]},
                        {
                            "$set": {"last_used_at": datetime.now(timezone.utc)},
                            "$inc": {"request_count": 1}
                        }
                    )

                    # Convert to APIKey model
                    doc["_id"] = str(doc["_id"])
                    return APIKey(**doc)

            return None

        except Exception as e:
            logger.error(f"Error verifying API key: {e}")
            return None

    async def list_user_keys(
        self,
        user_id: str,
        organization_id: Optional[str] = None
    ) -> List[APIKeyResponse]:
        """
        List all API keys for a user, optionally filtered by organization.

        Args:
            user_id: User ID
            organization_id: Optional organization ID for filtering

        Returns:
            List[APIKeyResponse]: List of API keys (without secrets)
        """
        try:
            # Build query filter
            query_filter = {"user_id": user_id}
            if organization_id:
                query_filter["organization_id"] = organization_id

            cursor = self.collection.find(query_filter).sort("created_at", -1)

            keys = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                doc["id"] = doc["_id"]
                keys.append(APIKeyResponse(**doc))

            logger.info(f"Listed {len(keys)} API keys for user={user_id}, organization={organization_id}")
            return keys

        except Exception as e:
            logger.error(f"Error listing API keys for organization={organization_id}: {e}")
            return []

    async def get_api_key(
        self,
        user_id: str,
        key_id: str,
        organization_id: Optional[str] = None
    ) -> Optional[APIKeyResponse]:
        """
        Get a specific API key by ID.

        Args:
            user_id: User ID (for authorization)
            key_id: API key ID
            organization_id: Optional organization ID for validation

        Returns:
            Optional[APIKeyResponse]: API key details or None
        """
        try:
            # Build query filter
            query_filter = {
                "_id": ObjectId(key_id),
                "user_id": user_id
            }
            if organization_id:
                query_filter["organization_id"] = organization_id

            doc = await self.collection.find_one(query_filter)

            if doc:
                doc["_id"] = str(doc["_id"])
                doc["id"] = doc["_id"]
                logger.info(f"Retrieved API key {key_id} for user={user_id}, organization={organization_id}")
                return APIKeyResponse(**doc)

            logger.warning(f"API key {key_id} not found for user={user_id}, organization={organization_id}")
            return None

        except Exception as e:
            logger.error(f"Error getting API key {key_id} for organization={organization_id}: {e}")
            return None

    async def revoke_api_key(
        self,
        user_id: str,
        key_id: str,
        organization_id: Optional[str] = None
    ) -> bool:
        """
        Revoke an API key (soft delete).

        Args:
            user_id: User ID (for authorization)
            key_id: API key ID
            organization_id: Optional organization ID for validation

        Returns:
            bool: True if revoked, False if not found
        """
        try:
            # Build query filter
            query_filter = {
                "_id": ObjectId(key_id),
                "user_id": user_id
            }
            if organization_id:
                query_filter["organization_id"] = organization_id

            result = await self.collection.update_one(
                query_filter,
                {
                    "$set": {"revoked": True}
                }
            )

            if result.modified_count > 0:
                logger.info(f"Revoked API key: {key_id} for user={user_id}, organization={organization_id}")
                return True

            logger.warning(f"Failed to revoke API key {key_id} for user={user_id}, organization={organization_id}")
            return False

        except Exception as e:
            logger.error(f"Error revoking API key {key_id} for organization={organization_id}: {e}")
            return False

    async def get_usage_stats(
        self,
        user_id: str,
        key_id: str,
        organization_id: Optional[str] = None
    ) -> Optional[APIKeyUsageStats]:
        """
        Get usage statistics for an API key.

        Args:
            user_id: User ID (for authorization)
            key_id: API key ID
            organization_id: Optional organization ID for validation

        Returns:
            Optional[APIKeyUsageStats]: Usage statistics or None
        """
        try:
            # Build query filter
            query_filter = {
                "_id": ObjectId(key_id),
                "user_id": user_id
            }
            if organization_id:
                query_filter["organization_id"] = organization_id

            doc = await self.collection.find_one(query_filter)

            if not doc:
                logger.warning(f"API key {key_id} not found for usage stats, organization={organization_id}")
                return None

            # For now, return basic stats
            # TODO: Implement detailed usage tracking with separate collection
            logger.info(f"Retrieved usage stats for API key {key_id}, organization={organization_id}")
            return APIKeyUsageStats(
                key_id=str(doc["_id"]),
                key_name=doc["name"],
                total_requests=doc.get("request_count", 0),
                requests_last_24h=0,  # TODO: Implement
                requests_last_7d=0,   # TODO: Implement
                last_used_at=doc.get("last_used_at"),
                created_at=doc["created_at"]
            )

        except Exception as e:
            logger.error(f"Error getting usage stats for key {key_id}, organization={organization_id}: {e}")
            return None


# ============================================================================
# Global Service Instance
# ============================================================================

_api_key_service: Optional[APIKeyService] = None


async def get_api_key_service() -> APIKeyService:
    """Get or create API key service singleton."""
    global _api_key_service

    if _api_key_service is None:
        _api_key_service = APIKeyService()
        await _api_key_service.create_indexes()

    return _api_key_service
