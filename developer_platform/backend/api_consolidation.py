"""
API Surface Consolidation for KasaAI Developer Platform.

This module provides standardized API responses, error handling, and documentation
for the consolidated API surface.
"""

from typing import Dict, Any, Optional, List, Union
from fastapi import HTTPException
from pydantic import BaseModel, Field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class APIResponseStatus(str, Enum):
    """Standard API response statuses."""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


class ErrorCode(str, Enum):
    """Standard error codes for consistent error handling."""
    # Authentication & Authorization
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    INVALID_API_KEY = "invalid_api_key"
    INSUFFICIENT_PERMISSIONS = "insufficient_permissions"
    
    # Resource Management
    NOT_FOUND = "not_found"
    ALREADY_EXISTS = "already_exists"
    INVALID_RESOURCE = "invalid_resource"
    RESOURCE_CONFLICT = "resource_conflict"
    
    # Rate Limiting & Quotas
    RATE_LIMITED = "rate_limited"
    QUOTA_EXCEEDED = "quota_exceeded"
    
    # Validation
    VALIDATION_ERROR = "validation_error"
    INVALID_PARAMETER = "invalid_parameter"
    
    # External Services
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    
    # Internal Errors
    INTERNAL_ERROR = "internal_error"
    DATABASE_ERROR = "database_error"


class StandardAPIResponse(BaseModel):
    """Standard API response format for all endpoints."""
    
    status: APIResponseStatus = Field(..., description="Response status")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[Dict[str, Any]] = Field(None, description="Error information")
    meta: Optional[Dict[str, Any]] = Field(None, description="Metadata about the response")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "data": {"id": "123", "name": "example"},
                "meta": {"timestamp": "2025-01-27T10:00:00Z", "version": "v1"}
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response format."""
    
    code: ErrorCode = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    
    class Config:
        schema_extra = {
            "example": {
                "code": "not_found",
                "message": "Resource not found",
                "details": {"resource_type": "api_key", "resource_id": "123"},
                "request_id": "req_123456"
            }
        }


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""
    
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class APIEndpointInfo(BaseModel):
    """Information about an API endpoint for documentation."""
    
    path: str = Field(..., description="Endpoint path")
    method: str = Field(..., description="HTTP method")
    description: str = Field(..., description="Endpoint description")
    version: str = Field(..., description="API version")
    requires_auth: bool = Field(..., description="Whether authentication is required")
    rate_limited: bool = Field(..., description="Whether endpoint is rate limited")


def create_success_response(
    data: Optional[Dict[str, Any]] = None,
    meta: Optional[Dict[str, Any]] = None,
    message: Optional[str] = None
) -> StandardAPIResponse:
    """
    Create a standardized success response.
    
    Args:
        data: Response data
        meta: Response metadata
        message: Optional success message
        
    Returns:
        StandardAPIResponse: Standardized success response
    """
    if meta is None:
        meta = {}
    
    if message:
        meta["message"] = message
    
    return StandardAPIResponse(
        status=APIResponseStatus.SUCCESS,
        data=data,
        meta=meta
    )


def create_error_response(
    code: ErrorCode,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> StandardAPIResponse:
    """
    Create a standardized error response.
    
    Args:
        code: Error code
        message: Error message
        details: Additional error details
        request_id: Request ID for tracking
        
    Returns:
        StandardAPIResponse: Standardized error response
    """
    error = ErrorResponse(
        code=code,
        message=message,
        details=details,
        request_id=request_id
    )
    
    return StandardAPIResponse(
        status=APIResponseStatus.ERROR,
        error=error.dict()
    )


def create_paginated_response(
    items: List[Dict[str, Any]],
    page: int,
    per_page: int,
    total: int,
    meta: Optional[Dict[str, Any]] = None
) -> StandardAPIResponse:
    """
    Create a standardized paginated response.
    
    Args:
        items: List of items
        page: Current page number
        per_page: Items per page
        total: Total number of items
        meta: Additional metadata
        
    Returns:
        StandardAPIResponse: Standardized paginated response
    """
    total_pages = (total + per_page - 1) // per_page
    
    pagination_meta = PaginationMeta(
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )
    
    if meta is None:
        meta = {}
    
    meta["pagination"] = pagination_meta.dict()
    
    return StandardAPIResponse(
        status=APIResponseStatus.SUCCESS,
        data={"items": items},
        meta=meta
    )


def handle_api_exception(
    exc: Exception,
    request_id: Optional[str] = None,
    context: Optional[str] = None
) -> HTTPException:
    """
    Handle API exceptions and convert to standardized HTTP exceptions.
    
    Args:
        exc: The exception to handle
        request_id: Request ID for tracking
        context: Additional context about the operation
        
    Returns:
        HTTPException: Standardized HTTP exception
    """
    logger.error(f"API Error: {exc}", extra={
        "request_id": request_id,
        "context": context,
        "exception_type": type(exc).__name__
    })
    
    if isinstance(exc, HTTPException):
        return exc
    
    if isinstance(exc, ValueError):
        return HTTPException(
            status_code=400,
            detail=create_error_response(
                ErrorCode.VALIDATION_ERROR,
                str(exc),
                request_id=request_id
            ).dict()
        )
    
    if isinstance(exc, KeyError):
        return HTTPException(
            status_code=400,
            detail=create_error_response(
                ErrorCode.INVALID_PARAMETER,
                f"Missing required parameter: {exc}",
                request_id=request_id
            ).dict()
        )
    
    # Default internal error
    return HTTPException(
        status_code=500,
        detail=create_error_response(
            ErrorCode.INTERNAL_ERROR,
            "An internal error occurred",
            request_id=request_id
        ).dict()
    )


# API Endpoint Registry for Documentation
API_ENDPOINTS: List[APIEndpointInfo] = [
    # Core Management
    APIEndpointInfo(
        path="/v1/api-keys",
        method="POST",
        description="Create a new API key",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/api-keys",
        method="GET",
        description="List all API keys",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/api-keys/{key_id}",
        method="GET",
        description="Get API key details",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/api-keys/{key_id}",
        method="DELETE",
        description="Revoke an API key",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    
    # Telephony APIs
    APIEndpointInfo(
        path="/v1/calls",
        method="POST",
        description="Create a new call",
        version="v1",
        requires_auth=True,
        rate_limited=True
    ),
    APIEndpointInfo(
        path="/v1/calls",
        method="GET",
        description="List calls for a tenant",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/calls/{call_id}",
        method="GET",
        description="Get call details",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/calls/{call_id}/transfer",
        method="POST",
        description="Transfer a call",
        version="v1",
        requires_auth=True,
        rate_limited=True
    ),
    APIEndpointInfo(
        path="/v1/calls/{call_id}/conference",
        method="POST",
        description="Create a conference call",
        version="v1",
        requires_auth=True,
        rate_limited=True
    ),
    APIEndpointInfo(
        path="/v1/calls/{call_id}/record",
        method="POST",
        description="Start call recording",
        version="v1",
        requires_auth=True,
        rate_limited=True
    ),
    APIEndpointInfo(
        path="/v1/calls/{call_id}/record",
        method="DELETE",
        description="Stop call recording",
        version="v1",
        requires_auth=True,
        rate_limited=True
    ),
    
    # Provider Management
    APIEndpointInfo(
        path="/v1/providers",
        method="GET",
        description="List available telephony providers",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/providers/{provider_id}/health",
        method="GET",
        description="Get provider health status",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/providers/{provider_id}/costs",
        method="GET",
        description="Get provider cost data",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/providers/comparison",
        method="GET",
        description="Compare available providers",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    
    # DID Management
    APIEndpointInfo(
        path="/v1/dids",
        method="GET",
        description="List DIDs for a tenant",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/dids/{did_id}/assign",
        method="POST",
        description="Assign a DID to a specific use case",
        version="v1",
        requires_auth=True,
        rate_limited=True
    ),
    APIEndpointInfo(
        path="/v1/dids/available",
        method="GET",
        description="Get available DIDs for purchase",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    
    # Analytics
    APIEndpointInfo(
        path="/v1/analytics/calls",
        method="GET",
        description="Get call analytics",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/analytics/quality",
        method="GET",
        description="Get call quality metrics",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/analytics/usage",
        method="GET",
        description="Get usage analytics",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    
    # Configuration
    APIEndpointInfo(
        path="/v1/config/tenant/{tenant_id}",
        method="GET",
        description="Get tenant configuration",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/config/features/{tenant_id}",
        method="GET",
        description="Get feature flags for a tenant",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    
    # Usage Tracking
    APIEndpointInfo(
        path="/v1/usage/summary/{tenant_id}",
        method="GET",
        description="Get usage summary for a tenant",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/usage/record/{tenant_id}",
        method="POST",
        description="Record usage for a feature",
        version="v1",
        requires_auth=True,
        rate_limited=True
    ),
    
    # License Management
    APIEndpointInfo(
        path="/v1/license/info/{tenant_id}",
        method="GET",
        description="Get license information for a tenant",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/license/validate/{tenant_id}",
        method="POST",
        description="Validate license for a tenant",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    
    # Monitoring
    APIEndpointInfo(
        path="/v1/monitoring/health/{tenant_id}",
        method="GET",
        description="Get monitoring health status for a tenant",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/monitoring/metrics/{tenant_id}",
        method="GET",
        description="Get monitoring metrics for a tenant",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/monitoring/log/{tenant_id}",
        method="POST",
        description="Log an event",
        version="v1",
        requires_auth=True,
        rate_limited=True
    ),
    
    # Module System
    APIEndpointInfo(
        path="/v1/modules/loaded/{tenant_id}",
        method="GET",
        description="Get loaded modules for a tenant",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/modules/available",
        method="GET",
        description="Get available modules",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/modules/load/{tenant_id}/{module_name}",
        method="POST",
        description="Load a module for a tenant",
        version="v1",
        requires_auth=True,
        rate_limited=True
    ),
    
    # Core Backend Proxy
    APIEndpointInfo(
        path="/v1/assistants",
        method="POST",
        description="Create an assistant via Core backend",
        version="v1",
        requires_auth=True,
        rate_limited=True
    ),
    APIEndpointInfo(
        path="/v1/assistants",
        method="GET",
        description="List assistants via Core backend",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/assistants/{assistant_id}",
        method="GET",
        description="Get an assistant via Core backend",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/assistants/{assistant_id}",
        method="PATCH",
        description="Update an assistant via Core backend",
        version="v1",
        requires_auth=True,
        rate_limited=True
    ),
    APIEndpointInfo(
        path="/v1/assistants/{assistant_id}",
        method="DELETE",
        description="Delete an assistant via Core backend",
        version="v1",
        requires_auth=True,
        rate_limited=True
    ),
    APIEndpointInfo(
        path="/v1/campaigns",
        method="POST",
        description="Create a campaign via Core backend",
        version="v1",
        requires_auth=True,
        rate_limited=True
    ),
    APIEndpointInfo(
        path="/v1/campaigns",
        method="GET",
        description="List campaigns via Core backend",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/campaigns/{campaign_id}",
        method="GET",
        description="Get a campaign via Core backend",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/campaigns/{campaign_id}",
        method="POST",
        description="Perform an action on a campaign",
        version="v1",
        requires_auth=True,
        rate_limited=True
    ),
    
    # Webhook Management
    APIEndpointInfo(
        path="/v1/webhooks",
        method="POST",
        description="Create a new webhook",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/webhooks",
        method="GET",
        description="List all webhooks",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/webhooks/{webhook_id}",
        method="GET",
        description="Get webhook details",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/webhooks/{webhook_id}",
        method="DELETE",
        description="Delete a webhook",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    
    # MCP Server Management
    APIEndpointInfo(
        path="/v1/mcp/servers",
        method="POST",
        description="Register a new MCP server",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/mcp/servers",
        method="GET",
        description="List all MCP servers",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/mcp/servers/{server_id}",
        method="GET",
        description="Get MCP server details",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/mcp/servers/{server_id}",
        method="DELETE",
        description="Delete an MCP server",
        version="v1",
        requires_auth=True,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/mcp/call",
        method="POST",
        description="Call a tool on an MCP server",
        version="v1",
        requires_auth=True,
        rate_limited=True
    ),
    
    # System Information
    APIEndpointInfo(
        path="/v1/health",
        method="GET",
        description="Health check endpoint",
        version="v1",
        requires_auth=False,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/capabilities/languages",
        method="GET",
        description="Get supported languages",
        version="v1",
        requires_auth=False,
        rate_limited=False
    ),
    APIEndpointInfo(
        path="/v1/endpoints",
        method="GET",
        description="Get all available API endpoints",
        version="v1",
        requires_auth=False,
        rate_limited=False
    ),
]


def get_api_endpoints() -> List[APIEndpointInfo]:
    """
    Get all available API endpoints for documentation.
    
    Returns:
        List[APIEndpointInfo]: List of all API endpoints
    """
    return API_ENDPOINTS


def get_api_endpoints_by_category() -> Dict[str, List[APIEndpointInfo]]:
    """
    Get API endpoints grouped by category.
    
    Returns:
        Dict[str, List[APIEndpointInfo]]: Endpoints grouped by category
    """
    categories = {
        "Core Management": [],
        "Telephony": [],
        "Analytics": [],
        "Configuration": [],
        "Usage Tracking": [],
        "License Management": [],
        "Monitoring": [],
        "Module System": [],
        "Core Backend Proxy": [],
        "Webhook Management": [],
        "MCP Server Management": [],
        "System Information": []
    }
    
    for endpoint in API_ENDPOINTS:
        if "api-keys" in endpoint.path:
            categories["Core Management"].append(endpoint)
        elif "calls" in endpoint.path or "providers" in endpoint.path or "dids" in endpoint.path:
            categories["Telephony"].append(endpoint)
        elif "analytics" in endpoint.path:
            categories["Analytics"].append(endpoint)
        elif "config" in endpoint.path:
            categories["Configuration"].append(endpoint)
        elif "usage" in endpoint.path:
            categories["Usage Tracking"].append(endpoint)
        elif "license" in endpoint.path:
            categories["License Management"].append(endpoint)
        elif "monitoring" in endpoint.path:
            categories["Monitoring"].append(endpoint)
        elif "modules" in endpoint.path:
            categories["Module System"].append(endpoint)
        elif "assistants" in endpoint.path or "campaigns" in endpoint.path:
            categories["Core Backend Proxy"].append(endpoint)
        elif "webhooks" in endpoint.path:
            categories["Webhook Management"].append(endpoint)
        elif "mcp" in endpoint.path:
            categories["MCP Server Management"].append(endpoint)
        else:
            categories["System Information"].append(endpoint)
    
    return categories

