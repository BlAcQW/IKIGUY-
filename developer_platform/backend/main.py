from __future__ import annotations

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from uuid import UUID
from typing import Optional, List, Dict, Any
import os
import uuid
import time
import logging
from .settings import settings

from .models import (
    APIKey,
    APIKeyCreate,
    Quota,
    QuotaCreate,
    Webhook,
    MCPServer,
)
from .storage import APIKeyStore, QuotaStore, WebhookStore, MCPServerStore
from .core_proxy import init_core_proxy, get_core_proxy
from .security import security_middleware

# Import shared services with fallback
try:
    from .services.shared import (
        SharedTelephonyService,
        SharedConfigService,
        SharedUsageService,
        SharedLicenseService,
        SharedMonitoringService,
        SharedModuleService,
    )

    SHARED_SERVICES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Shared services not available: {e}")

    # Create placeholder classes for fallback
    class SharedTelephonyService:
        def __init__(self):
            pass

    class SharedConfigService:
        def __init__(self):
            pass

    class SharedUsageService:
        def __init__(self):
            pass

    class SharedLicenseService:
        def __init__(self):
            pass

    class SharedMonitoringService:
        def __init__(self):
            pass

    class SharedModuleService:
        def __init__(self):
            pass

    SHARED_SERVICES_AVAILABLE = False

# Import AI service
try:
    from .services.ai_service import DeveloperAIService

    AI_SERVICE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"AI service not available: {e}")

    class DeveloperAIService:
        def __init__(self):
            pass

    AI_SERVICE_AVAILABLE = False

# Import analytics service
try:
    from .services.analytics_service import DeveloperAnalyticsService

    ANALYTICS_SERVICE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Analytics service not available: {e}")

    class DeveloperAnalyticsService:
        def __init__(self):
            pass

    ANALYTICS_SERVICE_AVAILABLE = False

# Import security service
try:
    from .services.security_service import DeveloperSecurityService

    SECURITY_SERVICE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Security service not available: {e}")

    class DeveloperSecurityService:
        def __init__(self):
            pass

    SECURITY_SERVICE_AVAILABLE = False

# Import API consolidation utilities
from .api_consolidation import (
    StandardAPIResponse,
    create_success_response,
    create_error_response,
    create_paginated_response,
    handle_api_exception,
    ErrorCode,
    get_api_endpoints,
    get_api_endpoints_by_category,
)

# Import import failure monitoring
try:
    from .services.import_config import get_import_failures, clear_import_failures

    IMPORT_MONITORING_AVAILABLE = True
except ImportError:
    IMPORT_MONITORING_AVAILABLE = False

app = FastAPI(
    title="KasaAI Developer Platform",
    description="Comprehensive API for KasaAI voice + chat automation platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

logger = logging.getLogger(__name__)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
from .middleware import rate_limit_middleware, usage_tracking_middleware
app.middleware("http")(usage_tracking_middleware)
app.middleware("http")(rate_limit_middleware)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint used by startup tests."""
    return {"status": "ok"}


# Global exception handler for standardized error responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for standardized error responses."""
    request_id = str(uuid.uuid4())

    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=create_error_response(
                ErrorCode.INTERNAL_ERROR, exc.detail, request_id=request_id
            ).dict(),
        )

    # Handle other exceptions
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            ErrorCode.INTERNAL_ERROR,
            "An internal error occurred",
            request_id=request_id,
        ).dict(),
    )


store = APIKeyStore()
quota_store = QuotaStore()
webhook_store = WebhookStore()
mcp_store = MCPServerStore()

# Initialize Core Backend proxy
core_url = os.getenv("CORE_BACKEND_URL", "http://localhost:8000")
cert_path = os.getenv("MTLS_CERT_PATH", "./certs/client.crt")
key_path = os.getenv("MTLS_KEY_PATH", "./certs/client.key")
ca_path = os.getenv("MTLS_CA_PATH", "./certs/ca.crt")

# Initialize Core Backend proxy
init_core_proxy(core_url, cert_path, key_path, ca_path)

# Initialize shared services
shared_telephony_service = SharedTelephonyService()
shared_config_service = SharedConfigService()
shared_usage_service = SharedUsageService()
shared_license_service = SharedLicenseService()
shared_monitoring_service = SharedMonitoringService()
shared_module_service = SharedModuleService()

# Log startup import health status
if IMPORT_MONITORING_AVAILABLE:
    import_failures = get_import_failures()
    if import_failures["failure_count"] > 0:
        logger.warning(
            f"STARTUP: {import_failures['failure_count']} shared library import failures detected"
        )
        for module, failure in import_failures["shared_libraries"].items():
            logger.warning(f"STARTUP: Failed to import {module}: {failure['error']}")
    else:
        logger.info("STARTUP: All shared libraries imported successfully")
else:
    logger.warning(
        "STARTUP: Import monitoring not available - cannot verify shared library health"
    )

# Initialize AI, analytics, and security services
ai_service = DeveloperAIService()
analytics_service = DeveloperAnalyticsService()
security_service = DeveloperSecurityService()


async def verify_api_key_and_get_tenant(api_key: str) -> Dict[str, Any]:
    """
    Verify API key and return tenant information.

    Args:
        api_key: API key to verify

    Returns:
        Dict containing tenant information

    Raises:
        HTTPException: If API key is invalid
    """
    try:
        key_info = await security_middleware.verify_api_key(api_key)
        return key_info
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# API Key Management
@app.post("/api-keys", response_model=APIKey)
async def create_api_key(payload: APIKeyCreate) -> APIKey:
    """Create a new API key."""
    return store.create(payload)


@app.get("/api-keys", response_model=list[APIKey])
async def list_api_keys() -> list[APIKey]:
    """List all API keys."""
    return store.list()


@app.get("/api-keys/{key_id}", response_model=APIKey)
async def get_api_key(key_id: UUID) -> APIKey:
    """Retrieve an API key by ID."""
    key = store.get(key_id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    return key


@app.post("/api-keys/{key_id}/rotate", response_model=APIKey)
async def rotate_api_key(key_id: UUID) -> APIKey:
    """Rotate the secret for an API key."""
    try:
        return store.rotate(key_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="API key not found")


@app.delete("/api-keys/{key_id}")
async def revoke_api_key(key_id: UUID) -> dict:
    """Revoke an API key."""
    try:
        store.revoke(key_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"status": "revoked"}


@app.post("/api-keys/{key_id}/quota", response_model=Quota)
async def set_quota(key_id: UUID, payload: QuotaCreate) -> Quota:
    """Create or update a quota for an API key."""
    if key_id != payload.api_key_id:
        raise HTTPException(status_code=400, detail="Mismatched api_key_id")
    return quota_store.create_or_update(key_id, payload.period, payload.limit)


@app.get("/api-keys/{key_id}/quota/{period}", response_model=Quota)
async def get_quota(key_id: UUID, period: str) -> Quota:
    """Retrieve quota information."""
    quota = quota_store.get(key_id, period)
    if not quota:
        raise HTTPException(status_code=404, detail="Quota not found")
    return quota


@app.post("/api-keys/{key_id}/quota/{period}/increment", response_model=Quota)
async def increment_quota(key_id: UUID, period: str) -> Quota:
    """Increment usage for a quota."""
    try:
        return quota_store.increment(key_id, period)
    except ValueError:
        raise HTTPException(status_code=404, detail="Quota not found")
    except RuntimeError:
        raise HTTPException(status_code=429, detail="Quota exceeded")


# Webhook Management
@app.post("/webhooks", response_model=Webhook)
async def create_webhook(webhook: Webhook) -> Webhook:
    """Create a new webhook."""
    return webhook_store.create(webhook)


@app.get("/webhooks", response_model=list[Webhook])
async def list_webhooks() -> list[Webhook]:
    """List all webhooks."""
    return webhook_store.list()


@app.get("/webhooks/{webhook_id}", response_model=Webhook)
async def get_webhook(webhook_id: UUID) -> Webhook:
    """Retrieve a webhook by ID."""
    webhook = webhook_store.get(webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook


@app.delete("/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: UUID) -> dict:
    """Delete a webhook."""
    try:
        webhook_store.delete(webhook_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"status": "deleted"}


# MCP Server Management
@app.post("/mcp/servers", response_model=MCPServer)
async def create_mcp_server(server: MCPServer) -> MCPServer:
    """Register a new MCP server."""
    return mcp_store.create(server)


@app.get("/mcp/servers", response_model=list[MCPServer])
async def list_mcp_servers() -> list[MCPServer]:
    """List all MCP servers."""
    return mcp_store.list()


@app.get("/mcp/servers/{server_id}", response_model=MCPServer)
async def get_mcp_server(server_id: UUID) -> MCPServer:
    """Retrieve an MCP server by ID."""
    server = mcp_store.get(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return server


@app.delete("/mcp/servers/{server_id}")
async def delete_mcp_server(server_id: UUID) -> dict:
    """Delete an MCP server."""
    try:
        mcp_store.delete(server_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return {"status": "deleted"}


@app.post("/mcp/call")
async def call_mcp_tool(server_id: UUID, tool_name: str, params: dict) -> dict:
    """Call a tool on an MCP server."""
    try:
        result = mcp_store.call_tool(server_id, tool_name, params)
        return {"result": result}
    except ValueError:
        raise HTTPException(status_code=404, detail="MCP server not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCP call failed: {str(e)}")


# Public API Endpoints (Proxy to Core)
@app.post("/assistants")
async def create_assistant(assistant_data: dict, x_api_key: str = Header(...)) -> dict:
    """Create an assistant via Core backend."""
    # Verify API key and get tenant context
    key_info = await security_middleware.verify_api_key(x_api_key)
    tenant_id = UUID(key_info["tenant_id"])

    # Use Core Backend proxy
    proxy = get_core_proxy()
    result = await proxy.create_assistant(tenant_id, assistant_data)
    return result


@app.get("/assistants")
async def list_assistants(x_api_key: str = Header(...)) -> list[dict]:
    """List assistants via Core backend."""
    # Verify API key and get tenant context
    key_info = await security_middleware.verify_api_key(x_api_key)
    tenant_id = UUID(key_info["tenant_id"])

    # Use Core Backend proxy
    proxy = get_core_proxy()
    result = await proxy.list_assistants(tenant_id)
    return result


@app.get("/assistants/{assistant_id}")
async def get_assistant(assistant_id: UUID, x_api_key: str = Header(...)) -> dict:
    """Get an assistant via Core backend."""
    # Verify API key and get tenant context
    key_info = await security_middleware.verify_api_key(x_api_key)
    tenant_id = UUID(key_info["tenant_id"])

    # Use Core Backend proxy
    proxy = get_core_proxy()
    result = await proxy.get_assistant(tenant_id, assistant_id)
    return result


@app.patch("/assistants/{assistant_id}")
async def update_assistant(
    assistant_id: UUID, assistant_data: dict, x_api_key: str = Header(...)
) -> dict:
    """Update an assistant via Core backend."""
    # Verify API key and get tenant context
    key_info = await security_middleware.verify_api_key(x_api_key)
    tenant_id = UUID(key_info["tenant_id"])

    # Use Core Backend proxy
    proxy = get_core_proxy()
    result = await proxy.update_assistant(tenant_id, assistant_id, assistant_data)
    return result


@app.delete("/assistants/{assistant_id}")
async def delete_assistant(assistant_id: UUID, x_api_key: str = Header(...)) -> dict:
    """Delete an assistant via Core backend."""
    # Verify API key and get tenant context
    key_info = await security_middleware.verify_api_key(x_api_key)
    tenant_id = UUID(key_info["tenant_id"])

    # Use Core Backend proxy
    proxy = get_core_proxy()
    result = await proxy.delete_assistant(tenant_id, assistant_id)
    return result


@app.post("/campaigns")
async def create_campaign(campaign_data: dict, x_api_key: str = Header(...)) -> dict:
    """Create a campaign via Core backend."""
    # Verify API key and get tenant context
    key_info = await security_middleware.verify_api_key(x_api_key)
    tenant_id = UUID(key_info["tenant_id"])

    # Use Core Backend proxy
    proxy = get_core_proxy()
    result = await proxy.create_campaign(tenant_id, campaign_data)
    return result


@app.get("/campaigns")
async def list_campaigns(x_api_key: str = Header(...)) -> list[dict]:
    """List campaigns via Core backend."""
    # Verify API key and get tenant context
    key_info = await security_middleware.verify_api_key(x_api_key)
    tenant_id = UUID(key_info["tenant_id"])

    # Use Core Backend proxy
    proxy = get_core_proxy()
    result = await proxy.list_campaigns(tenant_id)
    return result


@app.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: UUID, x_api_key: str = Header(...)) -> dict:
    """Get a campaign via Core backend."""
    # Verify API key and get tenant context
    key_info = await security_middleware.verify_api_key(x_api_key)
    tenant_id = UUID(key_info["tenant_id"])

    # Use Core Backend proxy
    proxy = get_core_proxy()
    result = await proxy.get_campaign(tenant_id, campaign_id)
    return result


@app.post("/campaigns/{campaign_id}")
async def campaign_action(
    campaign_id: UUID, action: str, x_api_key: str = Header(...)
) -> dict:
    """Perform an action on a campaign (start/stop/pause/resume)."""
    # Verify API key and get tenant context
    key_info = await security_middleware.verify_api_key(x_api_key)
    tenant_id = UUID(key_info["tenant_id"])

    # Use Core Backend proxy
    proxy = get_core_proxy()
    result = await proxy.campaign_action(tenant_id, campaign_id, action)
    return result


@app.get("/capabilities/languages")
async def get_languages() -> list[str]:
    """Get supported languages."""
    return [
        "en",
        "es",
        "fr",
        "de",
        "pt",
        "ar",
        "zh",
        "ja",
        "ko",
        "hi",
        "bn",
        "ur",
        "sw",
        "yo",
        "ig",
        "ha",
        "tw",
    ]


# ============================================================================
# TELEPHONY APIs - Phase 2 Implementation
# ============================================================================


# Core Telephony APIs
@app.post("/v1/calls")
async def create_call(call_data: dict, x_api_key: str = Header(...)) -> dict:
    """Create a new call."""
    try:
        key_info = await verify_api_key_and_get_tenant(x_api_key)
        tenant_id = key_info["tenant_id"]

        # Use shared telephony service
        call_result = await shared_telephony_service.create_call(tenant_id, call_data)
        return call_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/calls")
async def list_calls(
    limit: int = 100, status: Optional[str] = None, x_api_key: str = Header(...)
) -> dict:
    """List calls for a tenant."""
    try:
        key_info = await verify_api_key_and_get_tenant(x_api_key)
        tenant_id = key_info["tenant_id"]

        calls = await shared_telephony_service.list_calls(
            tenant_id, limit=limit, status=status
        )
        return {"calls": calls, "count": len(calls)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/calls/{call_id}")
async def get_call(call_id: str, x_api_key: str = Header(...)) -> dict:
    """Get call details."""
    try:
        key_info = await verify_api_key_and_get_tenant(x_api_key)
        tenant_id = key_info["tenant_id"]

        call = await shared_telephony_service.get_call(tenant_id, call_id)
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        return call
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/calls/{call_id}/transfer")
async def transfer_call(
    call_id: str, transfer_data: dict, x_api_key: str = Header(...)
) -> dict:
    """Transfer a call."""
    try:
        key_info = await verify_api_key_and_get_tenant(x_api_key)
        tenant_id = key_info["tenant_id"]

        result = await shared_telephony_service.transfer_call(
            tenant_id, call_id, transfer_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/calls/{call_id}/conference")
async def create_conference(
    call_id: str, conference_data: dict, x_api_key: str = Header(...)
) -> dict:
    """Create a conference call."""
    try:
        key_info = await verify_api_key_and_get_tenant(x_api_key)
        tenant_id = key_info["tenant_id"]

        result = await shared_telephony_service.create_conference(
            tenant_id, call_id, conference_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/calls/{call_id}/record")
async def start_recording(
    call_id: str, recording_data: dict, x_api_key: str = Header(...)
) -> dict:
    """Start call recording."""
    try:
        key_info = await verify_api_key_and_get_tenant(x_api_key)
        tenant_id = key_info["tenant_id"]

        result = await shared_telephony_service.start_recording(
            tenant_id, call_id, recording_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/v1/calls/{call_id}/record")
async def stop_recording(call_id: str, x_api_key: str = Header(...)) -> dict:
    """Stop call recording."""
    try:
        key_info = await verify_api_key_and_get_tenant(x_api_key)
        tenant_id = key_info["tenant_id"]

        result = await shared_telephony_service.stop_recording(tenant_id, call_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Provider Management APIs
@app.get("/v1/providers")
async def list_providers(x_api_key: str = Header(...)) -> dict:
    """List available telephony providers."""
    try:
        key_info = await verify_api_key_and_get_tenant(x_api_key)
        tenant_id = key_info["tenant_id"]

        providers = await shared_telephony_service.list_providers(tenant_id)
        return {"providers": providers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/providers/{provider_id}/health")
async def get_provider_health(provider_id: str, x_api_key: str = Header(...)) -> dict:
    """Get provider health status."""
    try:
        key_info = await verify_api_key_and_get_tenant(x_api_key)
        tenant_id = key_info["tenant_id"]

        health = await shared_telephony_service.get_provider_health(
            tenant_id, provider_id
        )
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/providers/{provider_id}/costs")
async def get_provider_costs(
    provider_id: str, period: str = "monthly", x_api_key: str = Header(...)
) -> dict:
    """Get provider cost data."""
    try:
        key_info = await verify_api_key_and_get_tenant(x_api_key)
        tenant_id = key_info["tenant_id"]

        costs = await shared_telephony_service.get_provider_costs(
            tenant_id, provider_id, period
        )
        return costs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/providers/comparison")
async def compare_providers(x_api_key: str = Header(...)) -> dict:
    """Compare available providers."""
    try:
        key_info = await verify_api_key_and_get_tenant(x_api_key)
        tenant_id = key_info["tenant_id"]

        comparison = await shared_telephony_service.compare_providers(tenant_id)
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# DID Management APIs
@app.get("/v1/dids")
async def list_dids(x_api_key: str = Header(...)) -> dict:
    """List DIDs for a tenant."""
    try:
        key_info = await verify_api_key_and_get_tenant(x_api_key)
        tenant_id = key_info["tenant_id"]

        dids = await shared_telephony_service.list_dids(tenant_id)
        return {"dids": dids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/dids/{did_id}/assign")
async def assign_did(
    did_id: str, assignment_data: dict, x_api_key: str = Header(...)
) -> dict:
    """Assign a DID to a specific use case."""
    try:
        key_info = await verify_api_key_and_get_tenant(x_api_key)
        tenant_id = key_info["tenant_id"]

        result = await shared_telephony_service.assign_did(
            tenant_id, did_id, assignment_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/dids/available")
async def get_available_dids(
    country: Optional[str] = None, x_api_key: str = Header(...)
) -> dict:
    """Get available DIDs for purchase."""
    try:
        key_info = await verify_api_key_and_get_tenant(x_api_key)
        tenant_id = key_info["tenant_id"]

        dids = await shared_telephony_service.get_available_dids(tenant_id, country)
        return {"available_dids": dids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Analytics APIs
@app.get("/v1/analytics/calls")
async def get_call_analytics(
    period: str = "daily",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    x_api_key: str = Header(...),
) -> dict:
    """Get call analytics."""
    try:
        key_info = await verify_api_key_and_get_tenant(x_api_key)
        tenant_id = key_info["tenant_id"]

        analytics = await shared_telephony_service.get_call_analytics(
            tenant_id, period, start_date, end_date
        )
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/analytics/quality")
async def get_quality_metrics(
    period: str = "daily", x_api_key: str = Header(...)
) -> dict:
    """Get call quality metrics."""
    try:
        key_info = await verify_api_key_and_get_tenant(x_api_key)
        tenant_id = key_info["tenant_id"]

        metrics = await shared_telephony_service.get_quality_metrics(tenant_id, period)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/analytics/usage")
async def get_usage_analytics(
    period: str = "daily", x_api_key: str = Header(...)
) -> dict:
    """Get usage analytics."""
    try:
        key_info = await verify_api_key_and_get_tenant(x_api_key)
        tenant_id = key_info["tenant_id"]

        analytics = await shared_usage_service.get_usage_summary(
            tenant_id, period=period
        )
        return analytics.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Analytics and Monitoring
@app.get("/analytics/usage")
async def get_usage_analytics(x_api_key: str = Header(...)) -> dict:
    """Get usage analytics for an API key."""
    # TODO: Implement usage analytics
    return {"status": "not implemented"}


@app.get("/analytics/errors")
async def get_error_analytics(x_api_key: str = Header(...)) -> dict:
    """Get error analytics for an API key."""
    # TODO: Implement error analytics
    return {"status": "not implemented"}


# Shared Library Integration Endpoints


@app.get("/v1/telephony/health/{tenant_id}")
async def get_telephony_health(tenant_id: str, x_api_key: str = Header(...)) -> dict:
    """Get telephony provider health status."""
    try:
        # Verify API key and get tenant context
        await verify_api_key_and_get_tenant(x_api_key)

        health_status = await shared_telephony_service.get_provider_health(tenant_id)
        return health_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/telephony/calls/{tenant_id}")
async def get_call_history(
    tenant_id: str, limit: int = 100, x_api_key: str = Header(...)
) -> dict:
    """Get call history for a tenant."""
    try:
        # Verify API key and get tenant context
        await verify_api_key_and_get_tenant(x_api_key)

        calls = await shared_telephony_service.get_call_history(tenant_id, limit)
        return {"calls": calls, "count": len(calls)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/config/tenant/{tenant_id}")
async def get_tenant_config(tenant_id: str, x_api_key: str = Header(...)) -> dict:
    """Get tenant configuration."""
    try:
        # Verify API key and get tenant context
        await verify_api_key_and_get_tenant(x_api_key)

        config = await shared_config_service.get_tenant_config(tenant_id)
        if config:
            return config.dict()
        else:
            return {"tenant_id": tenant_id, "config": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/config/features/{tenant_id}")
async def get_feature_flags(tenant_id: str, x_api_key: str = Header(...)) -> dict:
    """Get feature flags for a tenant."""
    try:
        # Verify API key and get tenant context
        await verify_api_key_and_get_tenant(x_api_key)

        features = await shared_config_service.get_feature_flags(tenant_id)
        return features.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/usage/summary/{tenant_id}")
async def get_usage_summary(
    tenant_id: str, period: str = "daily", x_api_key: str = Header(...)
) -> dict:
    """Get usage summary for a tenant."""
    try:
        # Verify API key and get tenant context
        await verify_api_key_and_get_tenant(x_api_key)

        summary = await shared_usage_service.get_usage_summary(tenant_id, period=period)
        return summary.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/license/info/{tenant_id}")
async def get_license_info(tenant_id: str, x_api_key: str = Header(...)) -> dict:
    """Get license information for a tenant."""
    try:
        # Verify API key and get tenant context
        await verify_api_key_and_get_tenant(x_api_key)

        license_info = await shared_license_service.get_license_info(tenant_id)
        if license_info:
            return license_info
        else:
            return {"tenant_id": tenant_id, "license": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/license/validate/{tenant_id}")
async def validate_license(tenant_id: str, x_api_key: str = Header(...)) -> dict:
    """Validate license for a tenant."""
    try:
        # Verify API key and get tenant context
        await verify_api_key_and_get_tenant(x_api_key)

        validation = await shared_license_service.validate_license(tenant_id)
        return validation.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/monitoring/health/{tenant_id}")
async def get_monitoring_health(tenant_id: str, x_api_key: str = Header(...)) -> dict:
    """Get monitoring health status for a tenant."""
    try:
        # Verify API key and get tenant context
        await verify_api_key_and_get_tenant(x_api_key)

        health_status = await shared_monitoring_service.get_health_status(tenant_id)
        return health_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/monitoring/metrics/{tenant_id}")
async def get_monitoring_metrics(
    tenant_id: str, metric_names: Optional[str] = None, x_api_key: str = Header(...)
) -> dict:
    """Get monitoring metrics for a tenant."""
    try:
        # Verify API key and get tenant context
        await verify_api_key_and_get_tenant(x_api_key)

        names = metric_names.split(",") if metric_names else None
        metrics = await shared_monitoring_service.get_metrics(
            tenant_id, metric_names=names
        )
        return {"metrics": [metric.dict() for metric in metrics]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/modules/loaded/{tenant_id}")
async def get_loaded_modules(tenant_id: str, x_api_key: str = Header(...)) -> dict:
    """Get loaded modules for a tenant."""
    try:
        # Verify API key and get tenant context
        await verify_api_key_and_get_tenant(x_api_key)

        modules = await shared_module_service.get_loaded_modules(tenant_id)
        return {"modules": [module.dict() for module in modules]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/modules/available")
async def get_available_modules(
    category: Optional[str] = None, x_api_key: str = Header(...)
) -> dict:
    """Get available modules."""
    try:
        # Verify API key and get tenant context
        await verify_api_key_and_get_tenant(x_api_key)

        modules = await shared_module_service.list_available_modules(category=category)
        return {"modules": [module.dict() for module in modules]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/modules/load/{tenant_id}/{module_name}")
async def load_module(
    tenant_id: str, module_name: str, x_api_key: str = Header(...)
) -> dict:
    """Load a module for a tenant."""
    try:
        # Verify API key and get tenant context
        await verify_api_key_and_get_tenant(x_api_key)

        module_instance = await shared_module_service.load_module(
            module_name, tenant_id
        )
        if module_instance:
            return {"success": True, "module": module_instance.dict()}
        else:
            return {"success": False, "error": "Failed to load module"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/usage/record/{tenant_id}")
async def record_usage(
    tenant_id: str, feature: str, quantity: int = 1, x_api_key: str = Header(...)
) -> dict:
    """Record usage for a feature."""
    try:
        # Verify API key and get tenant context
        await verify_api_key_and_get_tenant(x_api_key)

        success = await shared_usage_service.record_usage(tenant_id, feature, quantity)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/monitoring/log/{tenant_id}")
async def log_event(
    tenant_id: str,
    event_type: str,
    data: Optional[dict] = None,
    level: str = "info",
    x_api_key: str = Header(...),
) -> StandardAPIResponse:
    """Log an event."""
    try:
        # Verify API key and get tenant context
        await verify_api_key_and_get_tenant(x_api_key)

        success = await shared_monitoring_service.log_event(
            event_type, tenant_id, data, level
        )
        return create_success_response(
            data={"success": success}, message="Event logged successfully"
        )
    except Exception as e:
        raise handle_api_exception(e, context="log_event")


# ============================================================================
# CONSOLIDATED API ENDPOINTS - Standardized Responses
# ============================================================================


@app.get("/v1/health", response_model=StandardAPIResponse)
async def health_check() -> StandardAPIResponse:
    """Enhanced health check with detailed status."""
    try:
        # Check all services
        services_status = {
            "database": "healthy",
            "telephony": "healthy",
            "config": "healthy",
            "usage": "healthy",
            "license": "healthy",
            "monitoring": "healthy",
            "modules": "healthy",
        }

        return create_success_response(
            data=services_status,
            meta={"timestamp": time.time(), "version": "1.0.0"},
            message="All services healthy",
        )
    except Exception as e:
        raise handle_api_exception(e, context="health_check")


@app.get("/v1/endpoints", response_model=StandardAPIResponse)
async def get_endpoints() -> StandardAPIResponse:
    """Get all available API endpoints with documentation."""
    try:
        endpoints = get_api_endpoints()
        categories = get_api_endpoints_by_category()

        return create_success_response(
            data={
                "endpoints": [endpoint.dict() for endpoint in endpoints],
                "categories": {
                    category: [endpoint.dict() for endpoint in category_endpoints]
                    for category, category_endpoints in categories.items()
                },
            },
            meta={
                "total_endpoints": len(endpoints),
                "total_categories": len(categories),
            },
        )
    except Exception as e:
        raise handle_api_exception(e, context="get_endpoints")


@app.get("/v1/endpoints/{category}", response_model=StandardAPIResponse)
async def get_endpoints_by_category(category: str) -> StandardAPIResponse:
    """Get API endpoints for a specific category."""
    try:
        categories = get_api_endpoints_by_category()

        if category not in categories:
            raise HTTPException(
                status_code=404,
                detail=create_error_response(
                    ErrorCode.NOT_FOUND,
                    f"Category '{category}' not found",
                    details={"available_categories": list(categories.keys())},
                ).dict(),
            )

        category_endpoints = categories[category]

        return create_success_response(
            data={
                "category": category,
                "endpoints": [endpoint.dict() for endpoint in category_endpoints],
            },
            meta={"endpoint_count": len(category_endpoints)},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise handle_api_exception(e, context="get_endpoints_by_category")


@app.get("/v1/capabilities/languages", response_model=StandardAPIResponse)
async def get_supported_languages() -> StandardAPIResponse:
    """Get supported languages with additional metadata."""
    try:
        languages = [
            {"code": "en", "name": "English", "native_name": "English"},
            {"code": "es", "name": "Spanish", "native_name": "Español"},
            {"code": "fr", "name": "French", "native_name": "Français"},
            {"code": "de", "name": "German", "native_name": "Deutsch"},
            {"code": "pt", "name": "Portuguese", "native_name": "Português"},
            {"code": "ar", "name": "Arabic", "native_name": "العربية"},
            {"code": "zh", "name": "Chinese", "native_name": "中文"},
            {"code": "ja", "name": "Japanese", "native_name": "日本語"},
            {"code": "ko", "name": "Korean", "native_name": "한국어"},
            {"code": "hi", "name": "Hindi", "native_name": "हिन्दी"},
            {"code": "bn", "name": "Bengali", "native_name": "বাংলা"},
            {"code": "ur", "name": "Urdu", "native_name": "اردو"},
            {"code": "sw", "name": "Swahili", "native_name": "Kiswahili"},
            {"code": "yo", "name": "Yoruba", "native_name": "Yorùbá"},
            {"code": "ig", "name": "Igbo", "native_name": "Igbo"},
            {"code": "ha", "name": "Hausa", "native_name": "Hausa"},
            {"code": "tw", "name": "Twi", "native_name": "Twi"},
        ]

        return create_success_response(
            data={"languages": languages},
            meta={"total_languages": len(languages), "default_language": "en"},
        )
    except Exception as e:
        raise handle_api_exception(e, context="get_supported_languages")


@app.get("/v1/status", response_model=StandardAPIResponse)
async def get_system_status() -> StandardAPIResponse:
    """Get comprehensive system status and statistics."""
    try:
        # Get system statistics
        stats = {
            "api_keys": len(store.list()),
            "webhooks": len(webhook_store.list()),
            "mcp_servers": len(mcp_store.list()),
            "uptime": time.time(),  # Would be calculated from start time
            "version": "1.0.0",
        }

        # Add import failure status if monitoring is available
        if IMPORT_MONITORING_AVAILABLE:
            import_failures = get_import_failures()
            stats["import_failures"] = import_failures
            stats["shared_libraries_healthy"] = import_failures["failure_count"] == 0

        return create_success_response(
            data=stats,
            meta={
                "timestamp": time.time(),
                "status": "operational"
                if not IMPORT_MONITORING_AVAILABLE
                or import_failures["failure_count"] == 0
                else "degraded",
            },
        )
    except Exception as e:
        raise handle_api_exception(e, context="get_system_status")


@app.get("/v1/health/imports", response_model=StandardAPIResponse)
async def get_import_health() -> StandardAPIResponse:
    """Get detailed import health status for shared libraries."""
    try:
        if not IMPORT_MONITORING_AVAILABLE:
            return create_success_response(
                data={"message": "Import monitoring not available"},
                meta={"status": "unknown"},
            )

        import_failures = get_import_failures()

        # Determine overall health status
        if import_failures["failure_count"] == 0:
            status = "healthy"
            message = "All shared libraries imported successfully"
        elif import_failures["failure_count"] < 3:
            status = "degraded"
            message = f"Some shared libraries failed to import ({import_failures['failure_count']} failures)"
        else:
            status = "critical"
            message = f"Multiple shared library import failures ({import_failures['failure_count']} failures)"

        return create_success_response(
            data={
                "status": status,
                "message": message,
                "failures": import_failures["shared_libraries"],
                "failure_count": import_failures["failure_count"],
                "last_check": import_failures["last_check"],
            },
            meta={"timestamp": time.time(), "overall_status": status},
        )
    except Exception as e:
        raise handle_api_exception(e, context="get_import_health")


@app.post("/v1/health/imports/clear", response_model=StandardAPIResponse)
async def clear_import_failures_endpoint() -> StandardAPIResponse:
    """Clear import failure tracking (useful for testing)."""
    try:
        if not IMPORT_MONITORING_AVAILABLE:
            return create_success_response(
                data={"message": "Import monitoring not available"},
                meta={"status": "unknown"},
            )

        clear_import_failures()

        return create_success_response(
            data={"message": "Import failure tracking cleared"},
            meta={"status": "cleared"},
        )
    except Exception as e:
        raise handle_api_exception(e, context="clear_import_failures")


# Include AI, analytics, security, and email routes
from .routes.ai_routes import router as ai_router
from .routes.analytics_routes import router as analytics_router
from .routes.security_routes import router as security_router
from .routes.email_routes import router as email_router

app.include_router(ai_router)
app.include_router(analytics_router)
app.include_router(security_router)
app.include_router(email_router)

# ============================================================================
# API v1 ROUTES - Public Developer API
# ============================================================================

# Import v1 API routers
from .api.v1.vapi import router as vapi_v1_router, calls_router as vapi_calls_router
from .api.v1.n8n import router as n8n_v1_router, executions_router as n8n_executions_router
from .api.v1.usage import router as usage_v1_router
from .api.v1.tts import router as tts_v1_router
from .api.v1.asr import router as asr_v1_router
from .api.v1.llm import router as llm_v1_router
from .api.v1.wallet import router as wallet_v1_router
from .api.v1.analytics import router as analytics_v1_router
from .api.v1.storage import router as storage_v1_router

# Register v1 routers with OpenAPI tags for organization
app.include_router(
    vapi_v1_router,
    prefix="/api/v1",
    tags=["Voice Assistants (v1)"]
)
app.include_router(
    vapi_calls_router,
    prefix="/api/v1",
    tags=["Voice Calls (v1)"]
)
app.include_router(
    n8n_v1_router,
    prefix="/api/v1",
    tags=["Workflows (v1)"]
)
app.include_router(
    n8n_executions_router,
    prefix="/api/v1",
    tags=["Workflow Executions (v1)"]
)
app.include_router(
    usage_v1_router,
    tags=["Usage & Analytics (v1)"]
)

# AI Services Routers
app.include_router(
    tts_v1_router,
    tags=["TTS Services (v1)"]
)
app.include_router(
    asr_v1_router,
    tags=["ASR Services (v1)"]
)
app.include_router(
    llm_v1_router,
    tags=["LLM Services (v1)"]
)

# Wallet & Analytics Routers
app.include_router(
    wallet_v1_router,
    tags=["Wallet & Billing (v1)"]
)
app.include_router(
    analytics_v1_router,
    tags=["Analytics (v1)"]
)

# Storage Router
app.include_router(
    storage_v1_router,
    tags=["File Storage (v1)"]
)


# ==========================================
# Feedback & Bug Report Endpoints
# ==========================================

from pydantic import BaseModel
from typing import Optional
import sys
import os

# Ensure shared services path is available
if "/opt/kasaai/apps" not in sys.path:
    sys.path.insert(0, "/opt/kasaai/apps")

from apps.shared.services.bug_report_service import submit_bug_report as shared_submit_bug_report


class BugReport(BaseModel):
    """Bug report submission from frontend."""
    title: str
    description: str
    type: str  # bug, crash, ui, feature, other
    url: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    browser: Optional[str] = None
    timestamp: str


@app.post("/api/v1/feedback/bug-report", tags=["Feedback"])
async def submit_bug_report_endpoint(bug_report: BugReport) -> dict:
    """
    Submit a bug report.

    The report is sent to Slack and Linear via centralized service.

    Args:
        bug_report: Bug report details

    Returns:
        Success message with Linear issue details
    """
    try:
        # Use centralized bug report service
        result = await shared_submit_bug_report(
            title=bug_report.title,
            description=bug_report.description,
            bug_type=bug_report.type,
            url=bug_report.url,
            user_email=bug_report.user_email,
            user_id=bug_report.user_id,
            browser=bug_report.browser,
            timestamp=bug_report.timestamp,
            app_name="Developer Platform"
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Failed to submit bug report")
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting bug report: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to submit bug report. Please try again or contact support."
        )
