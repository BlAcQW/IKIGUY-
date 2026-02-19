"""Pydantic data models for the Developer Platform backend."""

from __future__ import annotations

from datetime import datetime, timezone
from secrets import token_urlsafe
from typing import List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class APIKey(BaseModel):
    """Represents an issued API key."""

    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    key_prefix: str
    secret: str = Field(default_factory=lambda: token_urlsafe(32))
    scopes: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    revoked: bool = False


class APIKeyCreate(BaseModel):
    """Payload to create an API key."""

    tenant_id: UUID
    scopes: List[str]


class Webhook(BaseModel):
    """Webhook registration."""

    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    url: str
    secret: str = Field(default_factory=lambda: token_urlsafe(32))
    events: List[str] = Field(default_factory=list)
    enabled: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MCPServer(BaseModel):
    """Registered MCP server."""

    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    url: str
    tool_names: List[str] = Field(default_factory=list)
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Quota(BaseModel):
    """Rate limit quota per API key."""

    id: UUID = Field(default_factory=uuid4)
    api_key_id: UUID
    period: str
    limit: int
    used: int = 0


class QuotaCreate(BaseModel):
    """Payload to create or update a quota."""

    api_key_id: UUID
    period: str
    limit: int


class APIRequestLog(BaseModel):
    """Request log for analytics and abuse checks."""

    id: UUID = Field(default_factory=uuid4)
    api_key_id: UUID
    route: str
    status: int
    latency_ms: int
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

