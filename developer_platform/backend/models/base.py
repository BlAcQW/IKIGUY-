"""Base models for Developer Platform backend."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4
from secrets import token_urlsafe


class PlanTier(str, Enum):
    """API plan tiers."""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class APIKeyCreate(BaseModel):
    """Model for creating a new API key."""
    tenant_id: UUID = Field(..., description="Tenant ID that owns this key")
    scopes: List[str] = Field(default_factory=list, description="Permissions/scopes for this key")


class APIKey(BaseModel):
    """Full API key model matching storage.py expectations."""
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for this key")
    tenant_id: UUID = Field(..., description="Tenant ID that owns this key")
    scopes: List[str] = Field(default_factory=list, description="Permissions/scopes for this key")
    secret: str = Field(default_factory=lambda: token_urlsafe(32), description="The actual API key secret")
    key_prefix: str = Field(..., description="Prefix for identifying the key")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="When created")
    enabled: bool = Field(default=True, description="Whether the key is enabled")
    revoked: bool = Field(default=False, description="Whether the key has been revoked")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
                "scopes": ["read", "write"],
                "secret": "abc123def456...",
                "key_prefix": "123e4567",
                "created_at": "2025-10-23T12:00:00Z",
                "enabled": True,
                "revoked": False
            }
        }


class APIKeyBase(BaseModel):
    """Legacy base for backward compatibility."""
    name: str = Field(..., description="Name/description of the API key")
    plan: PlanTier = Field(default=PlanTier.FREE, description="Plan tier for this key")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class QuotaCreate(BaseModel):
    """Model for creating a new quota."""
    api_key_id: UUID = Field(..., description="API key ID to associate quota with")
    period: str = Field(..., description="Quota period (daily, monthly, etc.)")
    limit: int = Field(..., description="Request limit for this period")


class Quota(BaseModel):
    """Full quota model matching storage.py expectations."""
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    api_key_id: UUID = Field(..., description="API key ID this quota belongs to")
    period: str = Field(..., description="Quota period (daily, monthly, etc.)")
    limit: int = Field(..., description="Request limit for this period")
    used: int = Field(default=0, description="Requests used in current period")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "api_key_id": "123e4567-e89b-12d3-a456-426614174000",
                "period": "daily",
                "limit": 1000,
                "used": 42
            }
        }


class QuotaBase(BaseModel):
    """Legacy base for backward compatibility."""
    plan: PlanTier = Field(..., description="Plan tier")
    daily_limit: int = Field(..., description="Daily request limit")
    monthly_limit: int = Field(..., description="Monthly request limit")
    rate_limit_per_minute: int = Field(..., description="Rate limit per minute")


class Webhook(BaseModel):
    """Webhook model matching storage.py expectations."""
    id: UUID = Field(default_factory=uuid4, description="Unique webhook identifier")
    url: str = Field(..., description="Webhook URL to call")
    events: List[str] = Field(default_factory=list, description="Events to trigger webhook for")
    secret: str = Field(default_factory=lambda: token_urlsafe(32), description="Webhook secret for signatures")
    enabled: bool = Field(default=True, description="Whether webhook is active")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "url": "https://example.com/webhook",
                "events": ["call.started", "call.ended"],
                "secret": "abc123def456...",
                "enabled": True
            }
        }


class WebhookBase(BaseModel):
    """Legacy base for backward compatibility."""
    url: str = Field(..., description="Webhook URL to call")
    events: List[str] = Field(..., description="Events to trigger webhook for")
    is_active: bool = Field(default=True, description="Whether webhook is active")


class MCPServer(BaseModel):
    """MCP server model matching storage.py expectations."""
    id: UUID = Field(default_factory=uuid4, description="Unique server identifier")
    name: str = Field(..., description="MCP server name")
    url: str = Field(..., description="MCP server URL")
    description: Optional[str] = Field(None, description="Server description")
    enabled: bool = Field(default=True, description="Whether server is active")
    capabilities: Dict[str, Any] = Field(default_factory=dict, description="Server capabilities")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "My MCP Server",
                "url": "https://mcp.example.com",
                "description": "Production MCP server",
                "enabled": True,
                "capabilities": {}
            }
        }


class MCPServerBase(BaseModel):
    """Legacy base for backward compatibility."""
    name: str = Field(..., description="MCP server name")
    url: str = Field(..., description="MCP server URL")
    description: Optional[str] = Field(None, description="Server description")
    is_active: bool = Field(default=True, description="Whether server is active")
