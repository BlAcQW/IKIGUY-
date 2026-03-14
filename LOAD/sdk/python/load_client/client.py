"""Async Python client for the LOAD API."""

from __future__ import annotations

from typing import Any

import httpx

from .types import Assistant, Call, Campaign, PhoneNumber, Squad, Tool, Webhook


class LoadClient:
    """Async client for the LOAD voice AI platform API.

    Usage::

        async with LoadClient(api_key="load_...") as client:
            assistants = await client.list_assistants()
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.tryload.ai",
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    async def __aenter__(self) -> "LoadClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = await self._client.request(
            method,
            f"/api{path}",
            json=json,
            params=params,
        )
        if response.status_code == 204:
            return {"success": True, "data": None}
        data = response.json()
        if not response.is_success:
            msg = data.get("error", {}).get("message", "Request failed")
            raise LoadAPIError(msg, response.status_code)
        return data

    # -----------------------------------------------------------------------
    # Assistants
    # -----------------------------------------------------------------------

    async def list_assistants(self, page: int = 1, limit: int = 20) -> list[Assistant]:
        data = await self._request("GET", "/assistants", params={"page": page, "limit": limit})
        return [Assistant.model_validate(a) for a in data["data"]]

    async def get_assistant(self, assistant_id: str) -> Assistant:
        data = await self._request("GET", f"/assistants/{assistant_id}")
        return Assistant.model_validate(data["data"])

    async def create_assistant(self, **kwargs: Any) -> Assistant:
        data = await self._request("POST", "/assistants", json=kwargs)
        return Assistant.model_validate(data["data"])

    async def update_assistant(self, assistant_id: str, **kwargs: Any) -> Assistant:
        data = await self._request("PATCH", f"/assistants/{assistant_id}", json=kwargs)
        return Assistant.model_validate(data["data"])

    async def delete_assistant(self, assistant_id: str) -> None:
        await self._request("DELETE", f"/assistants/{assistant_id}")

    # -----------------------------------------------------------------------
    # Calls
    # -----------------------------------------------------------------------

    async def list_calls(self, page: int = 1, limit: int = 20) -> list[Call]:
        data = await self._request("GET", "/calls", params={"page": page, "limit": limit})
        return [Call.model_validate(c) for c in data["data"]]

    async def get_call(self, call_id: str) -> Call:
        data = await self._request("GET", f"/calls/{call_id}")
        return Call.model_validate(data["data"])

    # -----------------------------------------------------------------------
    # Phone Numbers
    # -----------------------------------------------------------------------

    async def list_phone_numbers(self, page: int = 1, limit: int = 20) -> list[PhoneNumber]:
        data = await self._request("GET", "/phone-numbers", params={"page": page, "limit": limit})
        return [PhoneNumber.model_validate(p) for p in data["data"]]

    # -----------------------------------------------------------------------
    # Tools
    # -----------------------------------------------------------------------

    async def list_tools(self, page: int = 1, limit: int = 20) -> list[Tool]:
        data = await self._request("GET", "/tools", params={"page": page, "limit": limit})
        return [Tool.model_validate(t) for t in data["data"]]

    async def create_tool(self, **kwargs: Any) -> Tool:
        data = await self._request("POST", "/tools", json=kwargs)
        return Tool.model_validate(data["data"])

    async def delete_tool(self, tool_id: str) -> None:
        await self._request("DELETE", f"/tools/{tool_id}")

    # -----------------------------------------------------------------------
    # Squads
    # -----------------------------------------------------------------------

    async def list_squads(self, page: int = 1, limit: int = 20) -> list[Squad]:
        data = await self._request("GET", "/squads", params={"page": page, "limit": limit})
        return [Squad.model_validate(s) for s in data["data"]]

    async def create_squad(self, **kwargs: Any) -> Squad:
        data = await self._request("POST", "/squads", json=kwargs)
        return Squad.model_validate(data["data"])

    async def delete_squad(self, squad_id: str) -> None:
        await self._request("DELETE", f"/squads/{squad_id}")

    # -----------------------------------------------------------------------
    # Campaigns
    # -----------------------------------------------------------------------

    async def list_campaigns(self, page: int = 1, limit: int = 20) -> list[Campaign]:
        data = await self._request("GET", "/campaigns", params={"page": page, "limit": limit})
        return [Campaign.model_validate(c) for c in data["data"]]

    async def create_campaign(self, **kwargs: Any) -> Campaign:
        data = await self._request("POST", "/campaigns", json=kwargs)
        return Campaign.model_validate(data["data"])

    async def start_campaign(self, campaign_id: str) -> Campaign:
        data = await self._request("POST", f"/campaigns/{campaign_id}/start")
        return Campaign.model_validate(data["data"])

    async def pause_campaign(self, campaign_id: str) -> Campaign:
        data = await self._request("POST", f"/campaigns/{campaign_id}/pause")
        return Campaign.model_validate(data["data"])

    # -----------------------------------------------------------------------
    # Webhooks
    # -----------------------------------------------------------------------

    async def list_webhooks(self, page: int = 1, limit: int = 20) -> list[Webhook]:
        data = await self._request("GET", "/webhooks", params={"page": page, "limit": limit})
        return [Webhook.model_validate(w) for w in data["data"]]

    async def create_webhook(self, **kwargs: Any) -> Webhook:
        data = await self._request("POST", "/webhooks", json=kwargs)
        return Webhook.model_validate(data["data"])

    async def delete_webhook(self, webhook_id: str) -> None:
        await self._request("DELETE", f"/webhooks/{webhook_id}")


class LoadAPIError(Exception):
    """Raised when the LOAD API returns an error response."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code
