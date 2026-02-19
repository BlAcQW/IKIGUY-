"""MongoDB-backed storage utilities for the Developer Platform backend."""

from __future__ import annotations

from typing import List, Dict, Any
from secrets import token_urlsafe
from datetime import datetime, timezone
from uuid import UUID

from .mongo import get_collection
from .models import (
    APIKey,
    APIKeyCreate,
    Quota,
    QuotaCreate,
    Webhook,
    MCPServer,
)

_api_keys = get_collection("api_keys")
_quotas = get_collection("quotas")
_webhooks = get_collection("webhooks")
_mcp_servers = get_collection("mcp_servers")


def _to_doc(model):
    doc = model.model_dump()
    doc["_id"] = str(doc.pop("id"))
    for key, value in list(doc.items()):
        if isinstance(value, UUID):
            doc[key] = str(value)
    return doc


def _from_doc(model_cls, doc):
    doc["id"] = doc["_id"]
    return model_cls.model_validate(doc)


class APIKeyStore:
    """Store API keys in MongoDB."""

    def create(self, payload: APIKeyCreate) -> APIKey:
        """Create and store a new API key."""

        key = APIKey(
            tenant_id=payload.tenant_id,
            scopes=payload.scopes,
            key_prefix=str(payload.tenant_id)[:8],
        )
        _api_keys.insert_one(_to_doc(key))
        return key

    def rotate(self, key_id: UUID) -> APIKey:
        """Rotate the secret for an API key."""

        key = self.get(key_id)
        if not key:
            raise ValueError("API key not found")
        key.secret = token_urlsafe(32)
        key.created_at = datetime.now(timezone.utc)
        _api_keys.replace_one({"_id": str(key_id)}, _to_doc(key))
        return key

    def revoke(self, key_id: UUID) -> APIKey:
        """Revoke an API key."""

        key = self.get(key_id)
        if not key:
            raise ValueError("API key not found")
        key.revoked = True
        _api_keys.replace_one({"_id": str(key_id)}, _to_doc(key))
        return key

    def list(self) -> List[APIKey]:
        """Return all API keys."""

        return [_from_doc(APIKey, doc) for doc in _api_keys.find()]

    def get(self, key_id: UUID) -> APIKey | None:
        """Retrieve an API key by ID."""

        doc = _api_keys.find_one({"_id": str(key_id)})
        return _from_doc(APIKey, doc) if doc else None

    def get_by_secret(self, secret: str) -> APIKey | None:
        """Retrieve an API key by secret."""

        doc = _api_keys.find_one({"secret": secret})
        return _from_doc(APIKey, doc) if doc else None


class QuotaStore:
    """Manage rate limit quotas for API keys."""

    def create_or_update(self, api_key_id: UUID, period: str, limit: int) -> Quota:
        """Create or update a quota record."""

        doc = _quotas.find_one({"api_key_id": str(api_key_id), "period": period})
        if doc:
            quota = _from_doc(Quota, doc)
            quota.limit = limit
        else:
            quota = Quota(api_key_id=api_key_id, period=period, limit=limit)
        _quotas.update_one(
            {"api_key_id": str(api_key_id), "period": period},
            {"$set": _to_doc(quota)},
            upsert=True,
        )
        return quota

    def increment(self, api_key_id: UUID, period: str, amount: int = 1) -> Quota:
        """Increment usage and enforce limit."""

        doc = _quotas.find_one({"api_key_id": str(api_key_id), "period": period})
        if not doc:
            raise ValueError("Quota not configured")
        quota = _from_doc(Quota, doc)
        quota.used += amount
        if quota.used > quota.limit:
            raise RuntimeError("Quota exceeded")
        _quotas.replace_one({"_id": doc["_id"]}, _to_doc(quota))
        return quota

    def get(self, api_key_id: UUID, period: str) -> Quota | None:
        """Retrieve quota for an API key and period."""

        doc = _quotas.find_one({"api_key_id": str(api_key_id), "period": period})
        return _from_doc(Quota, doc) if doc else None


class WebhookStore:
    """Store webhook configurations."""

    def create(self, webhook: Webhook) -> Webhook:
        """Create and store a new webhook."""

        webhook.secret = token_urlsafe(32)
        _webhooks.insert_one(_to_doc(webhook))
        return webhook

    def list(self) -> List[Webhook]:
        """Return all webhooks."""

        return [_from_doc(Webhook, doc) for doc in _webhooks.find()]

    def get(self, webhook_id: UUID) -> Webhook | None:
        """Retrieve a webhook by ID."""

        doc = _webhooks.find_one({"_id": str(webhook_id)})
        return _from_doc(Webhook, doc) if doc else None

    def delete(self, webhook_id: UUID) -> None:
        """Delete a webhook."""

        result = _webhooks.delete_one({"_id": str(webhook_id)})
        if result.deleted_count == 0:
            raise ValueError("Webhook not found")

    def update(self, webhook_id: UUID, **kwargs) -> Webhook:
        """Update a webhook."""

        webhook = self.get(webhook_id)
        if not webhook:
            raise ValueError("Webhook not found")
        for key, value in kwargs.items():
            setattr(webhook, key, value)
        _webhooks.replace_one({"_id": str(webhook_id)}, _to_doc(webhook))
        return webhook


class MCPServerStore:
    """Store MCP server configurations."""

    def create(self, server: MCPServer) -> MCPServer:
        """Create and store a new MCP server."""

        _mcp_servers.insert_one(_to_doc(server))
        return server

    def list(self) -> List[MCPServer]:
        """Return all MCP servers."""

        return [_from_doc(MCPServer, doc) for doc in _mcp_servers.find()]

    def get(self, server_id: UUID) -> MCPServer | None:
        """Retrieve an MCP server by ID."""

        doc = _mcp_servers.find_one({"_id": str(server_id)})
        return _from_doc(MCPServer, doc) if doc else None

    def delete(self, server_id: UUID) -> None:
        """Delete an MCP server."""

        result = _mcp_servers.delete_one({"_id": str(server_id)})
        if result.deleted_count == 0:
            raise ValueError("MCP server not found")

    def update(self, server_id: UUID, **kwargs) -> MCPServer:
        """Update an MCP server."""

        server = self.get(server_id)
        if not server:
            raise ValueError("MCP server not found")
        for key, value in kwargs.items():
            setattr(server, key, value)
        _mcp_servers.replace_one({"_id": str(server_id)}, _to_doc(server))
        return server

    def call_tool(self, server_id: UUID, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on an MCP server (mock)."""

        server = self.get(server_id)
        if not server:
            raise ValueError("MCP server not found")
        return {
            "server_id": str(server_id),
            "tool_name": tool_name,
            "params": params,
            "result": "mock_result",
        }

