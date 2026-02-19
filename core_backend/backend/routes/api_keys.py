"""
API Keys Management Routes

Provides endpoints for generating, managing, and revoking API keys.

Created: 2025-10-27
Sprint 5: Analytics & Ecosystem (Phase 8)
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional
import logging

from ..auth import get_current_user_mongo
from ..middleware.rate_limiting import get_tts_rate_limit
from ..middleware.organization_context import (
    get_organization_context,
    validate_organization_access
)
from ..services.api_key_service import (
    get_api_key_service,
    APIKeyService,
    APIKeyCreate,
    APIKeyResponse,
    APIKeyWithSecret,
    APIKeyUsageStats,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/keys", tags=["API Keys"])


# ============================================================================
# API Key Management Endpoints
# ============================================================================

@router.post("/", response_model=APIKeyWithSecret)
async def create_api_key(
    request: Request,
    key_data: APIKeyCreate,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_tts_rate_limit("info", "free"))
):
    """
    Generate a new API key.

    **IMPORTANT:** The full API key is only shown once at creation.
    Store it securely - you won't be able to see it again!

    Args:
        key_data: API key configuration (name, scopes, rate limit, expiration)
        user: Current authenticated user

    Returns:
        APIKeyWithSecret: Created API key with full secret

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, user, org_id)

        logger.info(f"Creating API key for user={user['id']}, organization={org_id}, name={key_data.name}")

        service = await get_api_key_service()

        api_key = await service.create_api_key(
            user_id=user["id"],
            name=key_data.name,
            scopes=key_data.scopes,
            rate_limit=key_data.rate_limit,
            expires_in_days=key_data.expires_in_days,
            organization_id=org_id
        )

        logger.info(f"Created API key for user={user['id']}, organization={org_id}, name={key_data.name}")

        return api_key

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"API key creation validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating API key for organization={org_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.get("/", response_model=List[APIKeyResponse])
async def list_api_keys(
    request: Request,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_tts_rate_limit("info", "free"))
):
    """
    List all API keys for the current user.

    Keys are returned without their secrets (only prefix shown).

    Args:
        user: Current authenticated user

    Returns:
        List[APIKeyResponse]: List of API keys

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, user, org_id)

        logger.info(f"Listing API keys for user={user['id']}, organization={org_id}")

        service = await get_api_key_service()

        keys = await service.list_user_keys(user_id=user["id"], organization_id=org_id)

        logger.info(f"Listed {len(keys)} API keys for user={user['id']}, organization={org_id}")

        return keys

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing API keys for organization={org_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list API keys: {str(e)}"
        )


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: str,
    request: Request,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_tts_rate_limit("info", "free"))
):
    """
    Get details for a specific API key.

    Args:
        key_id: API key ID
        user: Current authenticated user

    Returns:
        APIKeyResponse: API key details

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, user, org_id)

        logger.info(f"Getting API key {key_id} for user={user['id']}, organization={org_id}")

        service = await get_api_key_service()

        api_key = await service.get_api_key(user_id=user["id"], key_id=key_id, organization_id=org_id)

        if not api_key:
            raise HTTPException(
                status_code=404,
                detail=f"API key '{key_id}' not found"
            )

        logger.info(f"Retrieved API key {key_id} for user={user['id']}, organization={org_id}")

        return api_key

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting API key {key_id} for organization={org_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get API key: {str(e)}"
        )


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str,
    request: Request,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_tts_rate_limit("info", "free"))
):
    """
    Revoke an API key.

    Once revoked, the key can no longer be used for authentication.
    This action cannot be undone.

    Args:
        key_id: API key ID
        user: Current authenticated user

    Returns:
        dict: Success message

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, user, org_id)

        logger.info(f"Revoking API key {key_id} for user={user['id']}, organization={org_id}")

        service = await get_api_key_service()

        success = await service.revoke_api_key(user_id=user["id"], key_id=key_id, organization_id=org_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"API key '{key_id}' not found"
            )

        logger.info(f"Revoked API key {key_id} for user={user['id']}, organization={org_id}")

        return {
            "success": True,
            "message": "API key revoked successfully",
            "key_id": key_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking API key {key_id} for organization={org_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to revoke API key: {str(e)}"
        )


@router.get("/{key_id}/usage", response_model=APIKeyUsageStats)
async def get_api_key_usage(
    key_id: str,
    request: Request,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_tts_rate_limit("info", "free"))
):
    """
    Get usage statistics for an API key.

    Shows total requests, recent activity, and last used timestamp.

    Args:
        key_id: API key ID
        user: Current authenticated user

    Returns:
        APIKeyUsageStats: Usage statistics

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, user, org_id)

        logger.info(f"Getting usage stats for key {key_id}, user={user['id']}, organization={org_id}")

        service = await get_api_key_service()

        stats = await service.get_usage_stats(user_id=user["id"], key_id=key_id, organization_id=org_id)

        if not stats:
            raise HTTPException(
                status_code=404,
                detail=f"API key '{key_id}' not found"
            )

        logger.info(f"Retrieved usage stats for key {key_id}, user={user['id']}, organization={org_id}")

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting usage stats for key {key_id}, organization={org_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get usage statistics: {str(e)}"
        )


@router.get("/scopes/available")
async def list_available_scopes(
    request: Request,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_tts_rate_limit("info", "free"))
):
    """
    List all available API key scopes.

    Scopes define what actions an API key can perform.

    Args:
        user: Current authenticated user

    Returns:
        dict: Available scopes with descriptions

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, user, org_id)

        logger.info(f"Listing available API scopes for user={user['id']}, organization={org_id}")

        scopes = {
            "tts:synthesize": "Generate speech from text",
            "tts:clone": "Use voice cloning features",
            "tts:history": "Access synthesis history",
            "tts:estimate": "Estimate synthesis costs",
            "tts:providers": "List available TTS providers",
            "tts:voices": "List available voices",
        }

        return {
            "scopes": scopes,
            "count": len(scopes)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing scopes for organization={org_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list scopes: {str(e)}"
        )
