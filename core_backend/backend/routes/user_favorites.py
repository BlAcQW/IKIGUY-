"""
User Favorites API Routes
Endpoints for managing user favorite automation templates
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Request
import logging
from datetime import datetime
from ..auth import get_current_user_mongo
from ..middleware.organization_context import (
    get_organization_context,
    validate_organization_access
)
from ..models.user_favorites import (
    UserFavorite,
    UserFavoriteCreate,
    UserFavoriteResponse,
    UserFavoritesListResponse,
    ToggleFavoriteResponse
)
from ..mongo import get_collection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user-favorites", tags=["user-favorites"])

# MongoDB collection
favorites_collection = get_collection("user_favorites")

@router.get("/", response_model=UserFavoritesListResponse)
async def get_user_favorites(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get all favorite templates for the current user.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid user ID")

        logger.info(f"Fetching favorites for user={user_id}, organization={org_id}")

        # Find all favorites for this user (optionally filtered by organization)
        query = {"user_id": user_id}
        if org_id:
            query["organization_id"] = org_id

        favorites_cursor = favorites_collection.find(query)
        favorites_list = list(favorites_cursor)

        # Convert to response model
        favorites_response = []
        for fav in favorites_list:
            favorites_response.append(UserFavoriteResponse(
                id=fav["id"],
                template_id=fav["template_id"],
                created_at=fav["created_at"]
            ))

        return UserFavoritesListResponse(
            favorites=favorites_response,
            total=len(favorites_response)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user favorites for organization={org_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch favorites: {str(e)}")

@router.post("/toggle/{template_id}", response_model=ToggleFavoriteResponse)
async def toggle_favorite(
    template_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Toggle favorite status for a template. Add if not favorite, remove if already favorite.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid user ID")

        logger.info(f"Toggling favorite for user={user_id}, template={template_id}, organization={org_id}")

        # Check if already favorited (with organization scope)
        query = {
            "user_id": user_id,
            "template_id": template_id
        }
        if org_id:
            query["organization_id"] = org_id

        existing_favorite = favorites_collection.find_one(query)

        if existing_favorite:
            # Remove from favorites
            delete_query = {
                "user_id": user_id,
                "template_id": template_id
            }
            if org_id:
                delete_query["organization_id"] = org_id

            favorites_collection.delete_one(delete_query)

            logger.info(f"Removed favorite for user={user_id}, template={template_id}, organization={org_id}")

            return ToggleFavoriteResponse(
                success=True,
                is_favorite=False,
                message="Template removed from favorites"
            )
        else:
            # Add to favorites
            new_favorite_data = {
                "id": f"{user_id}_{template_id}",
                "user_id": user_id,
                "template_id": template_id,
                "created_at": datetime.utcnow().isoformat()
            }
            if org_id:
                new_favorite_data["organization_id"] = org_id

            favorites_collection.insert_one(new_favorite_data)

            logger.info(f"Added favorite for user={user_id}, template={template_id}, organization={org_id}")

            return ToggleFavoriteResponse(
                success=True,
                is_favorite=True,
                message="Template added to favorites"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling favorite for organization={org_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to toggle favorite: {str(e)}")

@router.delete("/{template_id}")
async def remove_favorite(
    template_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Remove a template from user's favorites.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid user ID")

        logger.info(f"Removing favorite for user={user_id}, template={template_id}, organization={org_id}")

        # Remove from favorites (with organization scope)
        delete_query = {
            "user_id": user_id,
            "template_id": template_id
        }
        if org_id:
            delete_query["organization_id"] = org_id

        result = favorites_collection.delete_one(delete_query)

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Favorite not found")

        logger.info(f"Removed favorite for user={user_id}, template={template_id}, organization={org_id}")

        return {"success": True, "message": "Template removed from favorites"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing favorite for organization={org_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to remove favorite: {str(e)}")

@router.get("/check/{template_id}")
async def check_favorite_status(
    template_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Check if a template is favorited by the current user.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid user ID")

        logger.info(f"Checking favorite status for user={user_id}, template={template_id}, organization={org_id}")

        # Check if favorited (with organization scope)
        query = {
            "user_id": user_id,
            "template_id": template_id
        }
        if org_id:
            query["organization_id"] = org_id

        existing_favorite = favorites_collection.find_one(query)

        return {
            "is_favorite": existing_favorite is not None,
            "template_id": template_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking favorite status for organization={org_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check favorite status: {str(e)}")