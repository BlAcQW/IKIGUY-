"""
Language management routes for African Language Community Platform.

Handles language families, subfamilies, individual languages, and statistics.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional, List
from bson import ObjectId

from models.language_models import (
    LanguageFamily, LanguageSubfamily, Language, LanguageStats,
    LanguageFamilyCreate, LanguageSubfamilyCreate, LanguageCreate
)
from models.user_models import User
from models.responses import DataResponse, ListResponse
from routes.auth import get_current_user
from services.language_service import LanguageService

router = APIRouter()
language_service = LanguageService()


@router.get("", response_model=ListResponse)
async def get_all_languages(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    include_stats: bool = Query(False, description="Include language statistics")
):
    """
    Get all languages with pagination.

    Args:
        page: Page number (starts from 1)
        page_size: Number of languages per page
        include_stats: Whether to include contribution statistics

    Returns:
        ListResponse: List of all languages with pagination info
    """
    try:
        languages, total_count = await language_service.get_all_languages(
            page=page, page_size=page_size, include_stats=include_stats
        )

        return ListResponse.create(
            items=languages,
            total_count=total_count,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve languages: {str(e)}"
        )


@router.get("/families", response_model=ListResponse)
async def get_language_families(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Get all language families with pagination.

    Args:
        page: Page number (starts from 1)
        page_size: Number of families per page

    Returns:
        ListResponse: List of language families with pagination info
    """
    try:
        families, total_count = await language_service.get_language_families(
            page=page, page_size=page_size
        )

        return ListResponse.create(
            items=families,
            total_count=total_count,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve language families: {str(e)}"
        )


@router.post("/families", response_model=DataResponse)
async def create_language_family(
    family_data: LanguageFamilyCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new language family.

    Requires expert or guardian level permissions.

    Args:
        family_data: Language family information
        current_user: Authenticated user

    Returns:
        DataResponse: Created language family
    """
    try:
        # Check user permissions
        if not await language_service.can_manage_families(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create language families"
            )

        new_family = await language_service.create_language_family(family_data)

        return DataResponse(
            data=new_family,
            message="Language family created successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create language family: {str(e)}"
        )


@router.get("/families/{family_id}", response_model=DataResponse)
async def get_language_family(family_id: str):
    """
    Get detailed information about a specific language family.

    Args:
        family_id: Language family ID

    Returns:
        DataResponse: Language family with subfamilies and languages
    """
    try:
        if not ObjectId.is_valid(family_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid family ID format"
            )

        family = await language_service.get_language_family_with_details(family_id)
        if not family:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Language family not found"
            )

        return DataResponse(
            data=family,
            message="Language family retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve language family: {str(e)}"
        )


@router.get("/families/{family_id}/subfamilies", response_model=ListResponse)
async def get_subfamilies_by_family(
    family_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Get all subfamilies within a language family.

    Args:
        family_id: Language family ID
        page: Page number
        page_size: Items per page

    Returns:
        ListResponse: List of language subfamilies
    """
    try:
        if not ObjectId.is_valid(family_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid family ID format"
            )

        subfamilies, total_count = await language_service.get_subfamilies_by_family(
            family_id, page=page, page_size=page_size
        )

        return ListResponse.create(
            items=subfamilies,
            total_count=total_count,
            page=page,
            page_size=page_size
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve subfamilies: {str(e)}"
        )


@router.get("/subfamilies/{subfamily_id}/languages", response_model=ListResponse)
async def get_languages_by_subfamily(
    subfamily_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_stats: bool = Query(False, description="Include language statistics")
):
    """
    Get all languages within a subfamily.

    Args:
        subfamily_id: Language subfamily ID
        page: Page number
        page_size: Items per page
        include_stats: Whether to include contribution statistics

    Returns:
        ListResponse: List of languages with optional statistics
    """
    try:
        if not ObjectId.is_valid(subfamily_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid subfamily ID format"
            )

        languages, total_count = await language_service.get_languages_by_subfamily(
            subfamily_id, page=page, page_size=page_size, include_stats=include_stats
        )

        return ListResponse.create(
            items=languages,
            total_count=total_count,
            page=page,
            page_size=page_size
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve languages: {str(e)}"
        )


@router.get("/languages/{language_code}", response_model=DataResponse)
async def get_language_by_code(language_code: str):
    """
    Get detailed information about a specific language by ISO code.

    Args:
        language_code: ISO 639-3 language code (e.g., 'twi', 'yor', 'swa')

    Returns:
        DataResponse: Language information with family hierarchy
    """
    try:
        language = await language_service.get_language_by_code(language_code)
        if not language:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Language with code '{language_code}' not found"
            )

        return DataResponse(
            data=language,
            message="Language retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve language: {str(e)}"
        )


@router.get("/languages/{language_code}/stats", response_model=DataResponse)
async def get_language_statistics(language_code: str):
    """
    Get comprehensive statistics for a specific language.

    Args:
        language_code: ISO 639-3 language code

    Returns:
        DataResponse: Language statistics including contributions and quality metrics
    """
    try:
        stats = await language_service.get_language_statistics(language_code)
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Language '{language_code}' not found"
            )

        return DataResponse(
            data=stats,
            message="Language statistics retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve language statistics: {str(e)}"
        )


@router.post("/languages", response_model=DataResponse)
async def create_language(
    language_data: LanguageCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new language entry.

    Requires validator level permissions or higher.

    Args:
        language_data: Language information
        current_user: Authenticated user

    Returns:
        DataResponse: Created language
    """
    try:
        # Check user permissions
        if not await language_service.can_manage_languages(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create languages"
            )

        # Verify language doesn't already exist
        existing_language = await language_service.get_language_by_code(language_data.code)
        if existing_language:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Language with code '{language_data.code}' already exists"
            )

        new_language = await language_service.create_language(language_data)

        return DataResponse(
            data=new_language,
            message="Language created successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create language: {str(e)}"
        )


@router.get("/search", response_model=ListResponse)
async def search_languages(
    query: str = Query(..., min_length=2, description="Search query"),
    family: Optional[str] = Query(None, description="Filter by language family"),
    subfamily: Optional[str] = Query(None, description="Filter by subfamily"),
    country: Optional[str] = Query(None, description="Filter by country"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Search for languages by name, code, or other attributes.

    Args:
        query: Search term (language name, code, or description)
        family: Optional family filter
        subfamily: Optional subfamily filter
        country: Optional country filter
        page: Page number
        page_size: Items per page

    Returns:
        ListResponse: Search results with pagination
    """
    try:
        filters = {}
        if family:
            filters["family"] = family
        if subfamily:
            filters["subfamily"] = subfamily
        if country:
            filters["country"] = country

        results, total_count = await language_service.search_languages(
            query=query,
            filters=filters,
            page=page,
            page_size=page_size
        )

        return ListResponse.create(
            items=results,
            total_count=total_count,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/supported", response_model=DataResponse)
async def get_supported_languages():
    """
    Get list of languages currently supported by the platform.

    Returns languages with active contributions and voice support.

    Returns:
        DataResponse: List of supported languages with support levels
    """
    try:
        supported_languages = await language_service.get_supported_languages()

        return DataResponse(
            data=supported_languages,
            message="Supported languages retrieved successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve supported languages: {str(e)}"
        )