"""
Core Backend proxy service for Developer Platform.

Handles secure communication with Core Backend using mTLS and JWT authentication.
Provides request validation, normalization, and structured error mapping.
"""

import asyncio
from typing import Dict, Any, Optional, List
from uuid import UUID
import logging
from fastapi import HTTPException
import httpx

from .security import MTLSClient, jwt_manager, security_middleware

logger = logging.getLogger(__name__)


class CoreBackendProxy:
    """Proxy service for Core Backend communication."""
    
    def __init__(self, core_url: str, cert_path: str, key_path: str, ca_path: str):
        """
        Initialize Core Backend proxy.
        
        Args:
            core_url: Core Backend URL
            cert_path: Path to client certificate
            key_path: Path to client private key
            ca_path: Path to CA certificate
        """
        self.core_url = core_url
        self.cert_path = cert_path
        self.key_path = key_path
        self.ca_path = ca_path
        self._mclient: Optional[MTLSClient] = None
        
    async def _get_mtls_client(self) -> MTLSClient:
        """Get or create mTLS client."""
        if not self._mclient:
            self._mclient = MTLSClient(
                self.core_url, 
                self.cert_path, 
                self.key_path, 
                self.ca_path
            )
        return self._mclient
        
    async def _create_auth_headers(self, tenant_id: UUID, scopes: List[str]) -> Dict[str, str]:
        """
        Create authenticated headers for Core Backend request.
        
        Args:
            tenant_id: Tenant ID for the request
            scopes: Required scopes for the operation
            
        Returns:
            Dict containing authentication headers
        """
        # Create service JWT token
        token = jwt_manager.create_service_token(tenant_id, scopes)
        
        # Create tenant context headers
        tenant_headers = security_middleware.inject_tenant_context(str(tenant_id))
        
        return {
            "Authorization": f"Bearer {token}",
            **tenant_headers
        }
        
    def _validate_assistant_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize assistant data.
        
        Args:
            data: Raw assistant data
            
        Returns:
            Normalized assistant data
        """
        required_fields = ["name", "type", "languages"]
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
                
        # Normalize data
        normalized = {
            "name": data["name"].strip(),
            "type": data["type"],
            "languages": data["languages"] if isinstance(data["languages"], list) else [data["languages"]],
            "voice_pace": data.get("voice_pace", "normal"),
            "guardrails": data.get("guardrails", {}),
            "knowledge_base_id": data.get("knowledge_base_id"),
            "settings": data.get("settings", {})
        }
        
        # Validate guardrails
        if "guardrails" in normalized:
            allowed_guardrails = ["consent", "grounding", "profanity", "pii"]
            for key in normalized["guardrails"]:
                if key not in allowed_guardrails:
                    raise HTTPException(status_code=400, detail=f"Invalid guardrail: {key}")
                    
        return normalized
        
    def _validate_campaign_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize campaign data.
        
        Args:
            data: Raw campaign data
            
        Returns:
            Normalized campaign data
        """
        required_fields = ["name", "assistant_id", "goal"]
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
                
        # Normalize data
        normalized = {
            "name": data["name"].strip(),
            "assistant_id": data["assistant_id"],
            "goal": data["goal"],
            "audience": data.get("audience", {}),
            "schedule": data.get("schedule", {}),
            "throttle": data.get("throttle", {}),
            "retry_policy": data.get("retry_policy", {})
        }
        
        # Validate goal
        allowed_goals = ["sales", "collections", "renewals", "helpdesk", "surveys"]
        if normalized["goal"] not in allowed_goals:
            raise HTTPException(status_code=400, detail=f"Invalid goal: {normalized['goal']}")
            
        return normalized
        
    def _map_core_error(self, status_code: int, error_detail: str) -> HTTPException:
        """
        Map Core Backend errors to appropriate HTTP exceptions.
        
        Args:
            status_code: HTTP status code from Core
            error_detail: Error detail from Core
            
        Returns:
            HTTPException with appropriate status and detail
        """
        # Map common Core Backend errors
        if status_code == 400:
            return HTTPException(status_code=400, detail=f"Invalid request: {error_detail}")
        elif status_code == 401:
            return HTTPException(status_code=401, detail="Authentication failed")
        elif status_code == 403:
            return HTTPException(status_code=403, detail="Insufficient permissions")
        elif status_code == 404:
            return HTTPException(status_code=404, detail="Resource not found")
        elif status_code == 409:
            return HTTPException(status_code=409, detail="Resource conflict")
        elif status_code == 422:
            return HTTPException(status_code=422, detail=f"Validation error: {error_detail}")
        elif status_code >= 500:
            return HTTPException(status_code=503, detail="Core Backend service unavailable")
        else:
            return HTTPException(status_code=status_code, detail=error_detail)
            
    async def create_assistant(self, tenant_id: UUID, assistant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an assistant via Core Backend.
        
        Args:
            tenant_id: Tenant ID
            assistant_data: Assistant data
            
        Returns:
            Created assistant data
        """
        try:
            # Validate and normalize data
            normalized_data = self._validate_assistant_data(assistant_data)
            
            # Create authenticated headers
            headers = await self._create_auth_headers(
                tenant_id, 
                ["assistants:write"]
            )
            
            # Make request to Core Backend
            client = await self._get_mtls_client()
            response = await client.request(
                method="POST",
                endpoint="/internal/assistants",
                data=normalized_data,
                headers=headers
            )
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Core Backend error: {e.response.status_code} - {e.response.text}")
            raise self._map_core_error(e.response.status_code, e.response.text)
        except Exception as e:
            logger.error(f"Unexpected error creating assistant: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
            
    async def list_assistants(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List assistants via Core Backend.
        
        Args:
            tenant_id: Tenant ID
            limit: Maximum number of assistants to return
            offset: Number of assistants to skip
            
        Returns:
            List of assistants
        """
        try:
            # Create authenticated headers
            headers = await self._create_auth_headers(
                tenant_id, 
                ["assistants:read"]
            )
            
            # Add query parameters
            params = f"?limit={limit}&offset={offset}"
            
            # Make request to Core Backend
            client = await self._get_mtls_client()
            response = await client.request(
                method="GET",
                endpoint=f"/internal/assistants{params}",
                headers=headers
            )
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Core Backend error: {e.response.status_code} - {e.response.text}")
            raise self._map_core_error(e.response.status_code, e.response.text)
        except Exception as e:
            logger.error(f"Unexpected error listing assistants: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
            
    async def get_assistant(self, tenant_id: UUID, assistant_id: UUID) -> Dict[str, Any]:
        """
        Get an assistant via Core Backend.
        
        Args:
            tenant_id: Tenant ID
            assistant_id: Assistant ID
            
        Returns:
            Assistant data
        """
        try:
            # Create authenticated headers
            headers = await self._create_auth_headers(
                tenant_id, 
                ["assistants:read"]
            )
            
            # Make request to Core Backend
            client = await self._get_mtls_client()
            response = await client.request(
                method="GET",
                endpoint=f"/internal/assistants/{assistant_id}",
                headers=headers
            )
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Core Backend error: {e.response.status_code} - {e.response.text}")
            raise self._map_core_error(e.response.status_code, e.response.text)
        except Exception as e:
            logger.error(f"Unexpected error getting assistant: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
            
    async def update_assistant(self, tenant_id: UUID, assistant_id: UUID, assistant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an assistant via Core Backend.
        
        Args:
            tenant_id: Tenant ID
            assistant_id: Assistant ID
            assistant_data: Updated assistant data
            
        Returns:
            Updated assistant data
        """
        try:
            # Validate and normalize data
            normalized_data = self._validate_assistant_data(assistant_data)
            
            # Create authenticated headers
            headers = await self._create_auth_headers(
                tenant_id, 
                ["assistants:write"]
            )
            
            # Make request to Core Backend
            client = await self._get_mtls_client()
            response = await client.request(
                method="PATCH",
                endpoint=f"/internal/assistants/{assistant_id}",
                data=normalized_data,
                headers=headers
            )
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Core Backend error: {e.response.status_code} - {e.response.text}")
            raise self._map_core_error(e.response.status_code, e.response.text)
        except Exception as e:
            logger.error(f"Unexpected error updating assistant: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
            
    async def delete_assistant(self, tenant_id: UUID, assistant_id: UUID) -> Dict[str, Any]:
        """
        Delete an assistant via Core Backend.
        
        Args:
            tenant_id: Tenant ID
            assistant_id: Assistant ID
            
        Returns:
            Deletion confirmation
        """
        try:
            # Create authenticated headers
            headers = await self._create_auth_headers(
                tenant_id, 
                ["assistants:write"]
            )
            
            # Make request to Core Backend
            client = await self._get_mtls_client()
            response = await client.request(
                method="DELETE",
                endpoint=f"/internal/assistants/{assistant_id}",
                headers=headers
            )
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Core Backend error: {e.response.status_code} - {e.response.text}")
            raise self._map_core_error(e.response.status_code, e.response.text)
        except Exception as e:
            logger.error(f"Unexpected error deleting assistant: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
            
    async def create_campaign(self, tenant_id: UUID, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a campaign via Core Backend.
        
        Args:
            tenant_id: Tenant ID
            campaign_data: Campaign data
            
        Returns:
            Created campaign data
        """
        try:
            # Validate and normalize data
            normalized_data = self._validate_campaign_data(campaign_data)
            
            # Create authenticated headers
            headers = await self._create_auth_headers(
                tenant_id, 
                ["campaigns:write"]
            )
            
            # Make request to Core Backend
            client = await self._get_mtls_client()
            response = await client.request(
                method="POST",
                endpoint="/internal/campaigns",
                data=normalized_data,
                headers=headers
            )
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Core Backend error: {e.response.status_code} - {e.response.text}")
            raise self._map_core_error(e.response.status_code, e.response.text)
        except Exception as e:
            logger.error(f"Unexpected error creating campaign: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
            
    async def list_campaigns(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List campaigns via Core Backend.
        
        Args:
            tenant_id: Tenant ID
            limit: Maximum number of campaigns to return
            offset: Number of campaigns to skip
            
        Returns:
            List of campaigns
        """
        try:
            # Create authenticated headers
            headers = await self._create_auth_headers(
                tenant_id, 
                ["campaigns:read"]
            )
            
            # Add query parameters
            params = f"?limit={limit}&offset={offset}"
            
            # Make request to Core Backend
            client = await self._get_mtls_client()
            response = await client.request(
                method="GET",
                endpoint=f"/internal/campaigns{params}",
                headers=headers
            )
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Core Backend error: {e.response.status_code} - {e.response.text}")
            raise self._map_core_error(e.response.status_code, e.response.text)
        except Exception as e:
            logger.error(f"Unexpected error listing campaigns: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
            
    async def get_campaign(self, tenant_id: UUID, campaign_id: UUID) -> Dict[str, Any]:
        """
        Get a campaign via Core Backend.
        
        Args:
            tenant_id: Tenant ID
            campaign_id: Campaign ID
            
        Returns:
            Campaign data
        """
        try:
            # Create authenticated headers
            headers = await self._create_auth_headers(
                tenant_id, 
                ["campaigns:read"]
            )
            
            # Make request to Core Backend
            client = await self._get_mtls_client()
            response = await client.request(
                method="GET",
                endpoint=f"/internal/campaigns/{campaign_id}",
                headers=headers
            )
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Core Backend error: {e.response.status_code} - {e.response.text}")
            raise self._map_core_error(e.response.status_code, e.response.text)
        except Exception as e:
            logger.error(f"Unexpected error getting campaign: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
            
    async def campaign_action(self, tenant_id: UUID, campaign_id: UUID, action: str) -> Dict[str, Any]:
        """
        Perform an action on a campaign via Core Backend.
        
        Args:
            tenant_id: Tenant ID
            campaign_id: Campaign ID
            action: Action to perform (start/stop/pause/resume)
            
        Returns:
            Action result
        """
        try:
            # Validate action
            allowed_actions = ["start", "stop", "pause", "resume"]
            if action not in allowed_actions:
                raise HTTPException(status_code=400, detail=f"Invalid action: {action}")
                
            # Create authenticated headers
            headers = await self._create_auth_headers(
                tenant_id, 
                ["campaigns:write"]
            )
            
            # Make request to Core Backend
            client = await self._get_mtls_client()
            response = await client.request(
                method="POST",
                endpoint=f"/internal/campaigns/{campaign_id}?action={action}",
                headers=headers
            )
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Core Backend error: {e.response.status_code} - {e.response.text}")
            raise self._map_core_error(e.response.status_code, e.response.text)
        except Exception as e:
            logger.error(f"Unexpected error performing campaign action: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")


# Global proxy instance
core_proxy: Optional[CoreBackendProxy] = None


def init_core_proxy(core_url: str, cert_path: str, key_path: str, ca_path: str):
    """Initialize the global Core Backend proxy."""
    global core_proxy
    core_proxy = CoreBackendProxy(core_url, cert_path, key_path, ca_path)


def get_core_proxy() -> CoreBackendProxy:
    """Get the global Core Backend proxy instance."""
    if not core_proxy:
        raise RuntimeError("Core Backend proxy not initialized")
    return core_proxy 