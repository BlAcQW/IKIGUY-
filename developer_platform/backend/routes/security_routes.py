"""
Security Routes for KasaAI Developer Platform.

This module provides security-related API endpoints using the DeveloperSecurityService.
"""

from fastapi import APIRouter, Header
from typing import Dict, List, Optional, Any
import logging

from ..services.security_service import DeveloperSecurityService
from ..api_consolidation import (
    StandardAPIResponse,
    create_success_response,
    handle_api_exception,
)

# Create router
router = APIRouter(prefix="/v1/security", tags=["Security Services"])

# Initialize security service
security_service = DeveloperSecurityService()

@router.post("/audit/log", response_model=StandardAPIResponse)
async def create_audit_log(
    event_type: str,
    user_id: str,
    resource: str,
    action: str,
    metadata: Optional[Dict[str, Any]] = None,
    x_api_key: str = Header(...)
) -> StandardAPIResponse:
    """Create a security audit log."""
    try:
        result = await security_service.create_audit_log(
            event_type, user_id, resource, action, metadata
        )
        
        return create_success_response(
            data=result,
            message="Audit log created successfully"
        )
    except Exception as e:
        return handle_api_exception(e, "Failed to create audit log")

@router.get("/audit/logs", response_model=StandardAPIResponse)
async def get_audit_logs(
    filters: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = None,
    x_api_key: str = Header(...)
) -> StandardAPIResponse:
    """Get security audit logs."""
    try:
        result = await security_service.get_audit_logs(filters, limit)
        
        return create_success_response(
            data=result,
            message="Audit logs retrieved successfully"
        )
    except Exception as e:
        return handle_api_exception(e, "Failed to get audit logs")

@router.post("/access/check", response_model=StandardAPIResponse)
async def check_access(
    user_id: str,
    resource: str,
    action: str,
    context: Optional[Dict[str, Any]] = None,
    x_api_key: str = Header(...)
) -> StandardAPIResponse:
    """Check if user has access to resource."""
    try:
        result = await security_service.check_access(user_id, resource, action, context)
        
        return create_success_response(
            data=result,
            message="Access check completed successfully"
        )
    except Exception as e:
        return handle_api_exception(e, "Failed to check access")

@router.post("/encrypt", response_model=StandardAPIResponse)
async def encrypt_data(
    data: str,
    key_id: Optional[str] = None,
    algorithm: str = "AES-256",
    x_api_key: str = Header(...)
) -> StandardAPIResponse:
    """Encrypt data."""
    try:
        result = await security_service.encrypt_data(data, key_id, algorithm)
        
        return create_success_response(
            data=result,
            message="Data encrypted successfully"
        )
    except Exception as e:
        return handle_api_exception(e, "Failed to encrypt data")

@router.post("/decrypt", response_model=StandardAPIResponse)
async def decrypt_data(
    encrypted_data: str,
    key_id: Optional[str] = None,
    x_api_key: str = Header(...)
) -> StandardAPIResponse:
    """Decrypt data."""
    try:
        result = await security_service.decrypt_data(encrypted_data, key_id)
        
        return create_success_response(
            data=result,
            message="Data decrypted successfully"
        )
    except Exception as e:
        return handle_api_exception(e, "Failed to decrypt data")

@router.get("/config", response_model=StandardAPIResponse)
async def get_security_config(x_api_key: str = Header(...)) -> StandardAPIResponse:
    """Get security service configuration."""
    try:
        result = await security_service.get_developer_security_config()
        
        return create_success_response(
            data=result,
            message="Security configuration retrieved successfully"
        )
    except Exception as e:
        return handle_api_exception(e, "Failed to get security configuration")
