"""
Collection management routes for StudyFlow.

Handles RAG collection viewing, statistics, and administrative operations.
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status

from app.services.collection_service import CollectionService, CollectionInfo
from app.models.user import UserRole
from app.core.auth import get_current_user_with_org, OrganizationRoleChecker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/collections", tags=["Collections"])

# Only teachers and admins can manage collections
require_teacher_or_admin = OrganizationRoleChecker([UserRole.ADMIN, UserRole.TEACHER])


@router.get("/", response_model=List[Dict[str, Any]])
async def list_collections(
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    List all RAG collections for the current organization.

    Shows collection statistics including document counts, subjects, and grades.

    Args:
        user_context: User context with organization info

    Returns:
        List of collections with metadata
    """
    organization_id = user_context["organization_id"]

    try:
        collections = await CollectionService.list_organization_collections(organization_id)

        return [collection.to_dict() for collection in collections]

    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list collections: {str(e)}"
        )


@router.get("/{collection_name}/stats")
async def get_collection_stats(
    collection_name: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get detailed statistics for a specific collection.

    Args:
        collection_name: Collection name
        user_context: User context with organization info

    Returns:
        Detailed collection statistics

    Raises:
        HTTPException: If collection not found or access denied
    """
    organization_id = user_context["organization_id"]

    # Verify collection belongs to organization
    if organization_id not in collection_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this collection"
        )

    try:
        stats = await CollectionService.get_collection_stats(collection_name)

        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found or empty"
            )

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection stats: {str(e)}"
        )


@router.delete("/{collection_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_name: str,
    user_context: dict = Depends(require_teacher_or_admin)
):
    """
    Delete a RAG collection and mark materials for reprocessing.

    CAUTION: This operation cannot be undone. All embeddings will be removed.

    Args:
        collection_name: Collection to delete
        user_context: User context with organization info

    Raises:
        HTTPException: If deletion fails or access denied
    """
    organization_id = user_context["organization_id"]
    user_id = user_context["user_id"]

    # Verify collection belongs to organization
    if organization_id not in collection_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this collection"
        )

    try:
        success = await CollectionService.delete_collection(
            collection_name,
            organization_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete collection"
            )

        logger.info(f"Collection deleted: {collection_name} by user {user_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting collection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete collection: {str(e)}"
        )


@router.post("/{collection_name}/reindex")
async def reindex_collection(
    collection_name: str,
    user_context: dict = Depends(require_teacher_or_admin)
):
    """
    Reindex all materials in a collection.

    Useful when RAG configuration changes or embedding model is upgraded.
    Materials will be marked for reprocessing.

    Args:
        collection_name: Collection to reindex
        user_context: User context with organization info

    Returns:
        Reindexing status and material IDs

    Raises:
        HTTPException: If reindexing fails or access denied
    """
    organization_id = user_context["organization_id"]
    user_id = user_context["user_id"]

    # Verify collection belongs to organization
    if organization_id not in collection_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this collection"
        )

    try:
        result = await CollectionService.reindex_collection(
            collection_name,
            organization_id
        )

        logger.info(
            f"Collection reindex initiated: {collection_name} by user {user_id}, "
            f"{result['materials_marked_for_reindex']} materials queued"
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reindexing collection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reindex collection: {str(e)}"
        )


@router.get("/{collection_name}/parse")
async def parse_collection_name(
    collection_name: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Parse a collection name into its components.

    Useful for debugging and understanding collection naming structure.

    Args:
        collection_name: Collection name to parse
        user_context: User context with organization info

    Returns:
        Parsed collection components
    """
    result = CollectionService.parse_collection_name(collection_name)

    return {
        "collection_name": collection_name,
        **result
    }
