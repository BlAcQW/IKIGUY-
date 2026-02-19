"""
Series API routes.
Handles series listing and retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from app.services.series_service import (
    get_series_by_id,
    list_series,
    get_series_devotionals,
    create_series,
    update_series,
    delete_series,
    schedule_series_devotionals,
    reorder_devotionals,
    remove_devotional_from_series,
)
from app.models.series import SeriesCreate, SeriesUpdate, SeriesResponse
from app.utils.auth import get_current_user_optional, get_current_author, TokenData
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[dict])
async def list_series_endpoint(
    author_id: Optional[str] = Query(None, description="Filter by author ID"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of series to return"),
    current_user: Optional[TokenData] = Depends(get_current_user_optional),
):
    """
    List all series.

    Returns a list of devotional series, optionally filtered by author.
    """
    try:
        series_list = await list_series(author_id=author_id, limit=limit)
        return series_list
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing series: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list series: {str(e)}",
        )


@router.get("/{series_id}", response_model=dict)
async def get_series_endpoint(
    series_id: str,
    current_user: Optional[TokenData] = Depends(get_current_user_optional),
):
    """
    Get series by ID.

    Returns detailed information about a series including all devotionals in the series.
    """
    try:
        series = await get_series_by_id(series_id)
        if not series:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Series not found",
            )
        return series
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting series: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get series: {str(e)}",
        )


@router.get("/{series_id}/devotionals", response_model=List[dict])
async def get_series_devotionals_endpoint(
    series_id: str,
    current_user: Optional[TokenData] = Depends(get_current_user_optional),
):
    """
    Get all devotionals in a series.

    Returns a list of devotionals in the series, sorted by part number.
    """
    try:
        devotionals = await get_series_devotionals(series_id)
        return devotionals
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting series devotionals: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get series devotionals: {str(e)}",
        )


@router.post("/", response_model=SeriesResponse, status_code=status.HTTP_201_CREATED)
async def create_series_endpoint(
    series_data: SeriesCreate,
    current_user: TokenData = Depends(get_current_author),
):
    """
    Create a new series.

    Requires authentication. Any authenticated user (author or admin) can create a series.
    """
    try:
        series = await create_series(series_data, current_user.user_id)
        return series
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating series: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create series: {str(e)}",
        )


@router.put("/{series_id}", response_model=SeriesResponse)
async def update_series_endpoint(
    series_id: str,
    update_data: SeriesUpdate,
    current_user: TokenData = Depends(get_current_author),
):
    """
    Update series metadata.

    Only the series author or an admin can update a series.
    If start_date is changed, all devotionals will be rescheduled automatically.
    """
    try:
        is_admin = (current_user.role == "admin")
        series = await update_series(series_id, update_data, current_user.user_id, is_admin)
        return series
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating series: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update series: {str(e)}",
        )


@router.delete("/{series_id}")
async def delete_series_endpoint(
    series_id: str,
    orphan_devotionals: bool = Query(
        True,
        description="If true, unlink devotionals from series; if false, fail if devotionals exist"
    ),
    current_user: TokenData = Depends(get_current_author),
):
    """
    Delete a series.

    Only the series author or an admin can delete a series.
    By default (orphan_devotionals=true), devotionals are unlinked from the series.
    If orphan_devotionals=false, deletion will fail if the series has devotionals.
    """
    try:
        is_admin = (current_user.role == "admin")
        result = await delete_series(series_id, orphan_devotionals, current_user.user_id, is_admin)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting series: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete series: {str(e)}",
        )


@router.post("/{series_id}/move")
async def move_series_endpoint(
    series_id: str,
    new_start_date: str = Query(..., description="New start date in YYYY-MM-DD format"),
    current_user: TokenData = Depends(get_current_author),
):
    """
    Move a series to a new start date.
    This will reschedule all devotionals in the series to maintain their relative spacing.
    
    **Headers:**
    - Authorization: Bearer {access_token}
    
    **Path Parameters:**
    - series_id: Series ID
    
    **Query Parameters:**
    - new_start_date: New start date (YYYY-MM-DD)
    
    **Returns:**
    - Series with updated start_date and rescheduled devotionals count
    
    **Raises:**
    - 401: Unauthorized
    - 404: Series not found
    """
    from datetime import datetime
    from app.services.series_service import update_series, reschedule_series_devotionals
    
    try:
        # Parse new start date
        new_date = datetime.fromisoformat(new_start_date)
        # Set to 8 AM
        new_date = new_date.replace(hour=8, minute=0, second=0, microsecond=0)
        
        # Update series start_date
        updated_series = await update_series(
            series_id,
            {"start_date": new_date},
            current_user.user_id,
            is_admin=current_user.role == "admin"
        )
        
        # Reschedule all devotionals
        rescheduled_count = await reschedule_series_devotionals(series_id)
        
        return {
            "series": updated_series,
            "rescheduled_count": rescheduled_count,
            "message": f"Series moved to {new_start_date}. {rescheduled_count} devotionals rescheduled."
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error moving series: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to move series: {str(e)}"
        )


@router.post("/{series_id}/schedule")
async def schedule_series_endpoint(
    series_id: str,
    current_user: TokenData = Depends(get_current_author),
):
    """
    Schedule all devotionals in the series.

    Calculates scheduled_at for each devotional based on:
    scheduled_at = series.start_date + (part_number - 1) days

    Skips already published devotionals.
    Only the series author or an admin can schedule a series.
    """
    try:
        is_admin = (current_user.role == "admin")
        result = await schedule_series_devotionals(series_id, current_user.user_id, is_admin)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling series: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule series: {str(e)}",
        )


@router.post("/{series_id}/reorder")
async def reorder_devotionals_endpoint(
    series_id: str,
    devotional_order: List[str],
    current_user: TokenData = Depends(get_current_author),
):
    """
    Reorder devotionals in a series.

    Provide a list of devotional IDs in the desired order.
    Part numbers will be updated automatically (1, 2, 3, ...).
    Uses MongoDB bulk_write for atomic updates.

    Only the series author or an admin can reorder devotionals.
    """
    try:
        is_admin = (current_user.role == "admin")
        result = await reorder_devotionals(series_id, devotional_order, current_user.user_id, is_admin)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reordering devotionals: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reorder devotionals: {str(e)}",
        )


@router.delete("/{series_id}/devotionals/{devotional_id}")
async def remove_devotional_from_series_endpoint(
    series_id: str,
    devotional_id: str,
    auto_renumber: bool = Query(
        True,
        description="If true, auto-renumber remaining devotionals; if false, leave gaps in part numbers"
    ),
    current_user: TokenData = Depends(get_current_author),
):
    """
    Remove a devotional from a series.

    By default (auto_renumber=true), remaining devotionals are renumbered automatically.
    For example, if Part 3 is removed from a 5-part series:
    - Parts 4 and 5 become Parts 3 and 4

    Only the series author or an admin can remove devotionals.
    """
    try:
        is_admin = (current_user.role == "admin")
        result = await remove_devotional_from_series(
            series_id, devotional_id, auto_renumber, current_user.user_id, is_admin
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing devotional from series: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove devotional from series: {str(e)}",
        )



