"""
AI Tools API router for EstateFlow.

Provides endpoints for AI content generation, analysis, and usage statistics.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.ai_tools import (
    GenerationRequest,
    GenerationResponse,
    GenerationListResponse,
    AIStats,
)
from app.services.ai_tools_service import AIToolsService
from app.core.auth import get_current_user, get_organization_context
from app.core.database import get_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai-tools"])


@router.post(
    "/generate/listing",
    response_model=GenerationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a property listing",
)
async def generate_listing(
    request: GenerationRequest,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context),
):
    """Generate a property listing description using AI."""
    service = AIToolsService(database)
    organization_id = org_context["organization_id"]
    user_id = current_user.get("user_id", current_user.get("id", "unknown"))

    try:
        return await service.generate_listing(
            prompt=request.prompt,
            property_id=request.property_id,
            organization_id=organization_id,
            user_id=user_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate listing: {str(e)}",
        )


@router.post(
    "/generate/social",
    response_model=GenerationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate social media content",
)
async def generate_social_post(
    request: GenerationRequest,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context),
):
    """Generate social media post content using AI."""
    service = AIToolsService(database)
    organization_id = org_context["organization_id"]
    user_id = current_user.get("user_id", current_user.get("id", "unknown"))

    try:
        return await service.generate_social_post(
            prompt=request.prompt,
            property_id=request.property_id,
            organization_id=organization_id,
            user_id=user_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate social post: {str(e)}",
        )


@router.post(
    "/generate/email",
    response_model=GenerationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate email content",
)
async def generate_email(
    request: GenerationRequest,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context),
):
    """Generate email campaign content using AI."""
    service = AIToolsService(database)
    organization_id = org_context["organization_id"]
    user_id = current_user.get("user_id", current_user.get("id", "unknown"))

    try:
        return await service.generate_email(
            prompt=request.prompt,
            organization_id=organization_id,
            user_id=user_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate email: {str(e)}",
        )


@router.post(
    "/analyze/contract",
    response_model=GenerationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyze a contract",
)
async def analyze_contract(
    request: GenerationRequest,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context),
):
    """Analyze a contract using AI."""
    service = AIToolsService(database)
    organization_id = org_context["organization_id"]
    user_id = current_user.get("user_id", current_user.get("id", "unknown"))

    try:
        return await service.analyze_contract(
            prompt=request.prompt,
            organization_id=organization_id,
            user_id=user_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze contract: {str(e)}",
        )


@router.get(
    "/generations",
    response_model=GenerationListResponse,
    summary="List AI generations",
)
async def list_generations(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context),
):
    """List past AI generations for the organization."""
    service = AIToolsService(database)
    organization_id = org_context["organization_id"]

    generations, total = await service.list_generations(
        organization_id=organization_id,
        limit=limit,
        offset=offset,
    )

    return GenerationListResponse(
        generations=generations,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/stats",
    response_model=AIStats,
    summary="Get AI usage statistics",
)
async def get_ai_stats(
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context),
):
    """Get AI usage statistics for the organization."""
    service = AIToolsService(database)
    organization_id = org_context["organization_id"]
    return await service.get_stats(organization_id)
