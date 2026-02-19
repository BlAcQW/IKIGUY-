"""
Devotional API routes.
Handles devotional CRUD operations, publishing, and listing.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional, Literal
from app.models.devotional import (
    DevotionalCreate,
    DevotionalUpdate,
    DevotionalResponse,
    DevotionalListResponse,
    DevotionalFilters,
)
from app.services.devotional_service import (
    create_devotional,
    get_devotional_by_id,
    get_devotional_by_slug,
    list_devotionals,
    update_devotional,
    delete_devotional,
    bulk_delete_devotionals,
    publish_devotional,
    increment_view_count,
)
from app.utils.auth import get_current_user, get_current_user_optional, get_current_admin, get_current_author
from app.models.user import TokenData
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=DevotionalResponse, status_code=status.HTTP_201_CREATED)
async def create_devotional_endpoint(
    devotional_data: DevotionalCreate,
    current_user: TokenData = Depends(get_current_author),
):
    """
    Create a new devotional.
    Any authenticated user can create devotionals.

    **Headers:**
    - Authorization: Bearer {access_token}

    **Request Body:**
    - title: Devotional title
    - content: List of content blocks (paragraph, scripture, prayer, reflection)
    - scripture_references: List of scripture references
    - categories: List of categories
    - cover_image_url: (optional) Cover image URL
    - audio_url: (optional) Audio URL
    - status: "draft", "scheduled", or "published"
    - scheduled_at: (optional) Publication date for scheduled devotionals

    **Returns:**
    - Created devotional data

    **Raises:**
    - 401: Unauthorized (not logged in)
    - 403: Forbidden (not an admin)
    """
    try:
        logger.info(f"Creating devotional by user {current_user.user_id}")
        logger.debug(f"Devotional data: title={devotional_data.title}, status={devotional_data.status}, content_blocks={len(devotional_data.content)}")
        devotional = await create_devotional(devotional_data, current_user.user_id)
        logger.info(f"Devotional created: {devotional.id}")
        return devotional
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating devotional: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create devotional: {str(e)}",
        )


@router.get("/", response_model=DevotionalListResponse)
async def list_devotionals_endpoint(
    status_filter: Optional[Literal["draft", "scheduled", "published"]] = Query(
        None, alias="status"
    ),
    category: Optional[str] = None,
    author_id: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    days: Optional[int] = Query(None, ge=1, description="Last N days from today"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Literal["created_at", "published_at", "views_count", "likes_count"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    current_user: Optional[TokenData] = Depends(get_current_user_optional),
):
    """
    List devotionals with filters and pagination.

    **Query Parameters:**
    - status: Filter by status ("draft", "scheduled", "published")
    - category: Filter by category
    - author_id: Filter by author
    - search: Full-text search
    - start_date: Filter devotionals published on or after this date (YYYY-MM-DD)
    - end_date: Filter devotionals published on or before this date (YYYY-MM-DD)
    - days: Filter devotionals published in the last N days from today
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - sort_by: Sort field (default: "created_at")
    - sort_order: Sort order ("asc" or "desc", default: "desc")

    **Returns:**
    - Paginated list of devotionals

    **Note:**
    - Drafts are only visible to the author
    - Published devotionals are visible to everyone
    - Date filtering applies to published_at field
    """
    filters = DevotionalFilters(
        status=status_filter,
        category=category,
        author_id=author_id,
        search=search,
        start_date=start_date,
        end_date=end_date,
        days=days,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    logger.info(f"Listing devotionals with filters: {filters.model_dump()}")
    user_id = current_user.user_id if current_user else None
    result = await list_devotionals(filters, user_id=user_id)
    logger.info(f"Found {result.total} devotionals")
    return result


@router.get("/{devotional_id}", response_model=DevotionalResponse)
async def get_devotional_endpoint(
    devotional_id: str,
    current_user: Optional[TokenData] = Depends(get_current_user_optional),
):
    """
    Get a single devotional by ID.

    **Path Parameters:**
    - devotional_id: Devotional ID

    **Returns:**
    - Devotional data

    **Raises:**
    - 404: Devotional not found

    **Note:**
    - Increments view count
    """
    logger.info(f"Getting devotional {devotional_id}")
    user_id = current_user.user_id if current_user else None
    devotional = await get_devotional_by_id(devotional_id, user_id=user_id)

    if not devotional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devotional not found",
        )

    # Increment view count (don't await to not block response)
    await increment_view_count(devotional_id)

    return devotional


@router.get("/slug/{slug}", response_model=DevotionalResponse)
async def get_devotional_by_slug_endpoint(
    slug: str,
    current_user: Optional[TokenData] = Depends(get_current_user),
):
    """
    Get a single devotional by slug.

    **Path Parameters:**
    - slug: Devotional slug (URL-friendly identifier)

    **Returns:**
    - Devotional data

    **Raises:**
    - 404: Devotional not found

    **Note:**
    - Increments view count
    """
    logger.info(f"Getting devotional by slug: {slug}")
    devotional = await get_devotional_by_slug(slug)

    if not devotional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devotional not found",
        )

    # Increment view count
    await increment_view_count(devotional.id)

    return devotional


@router.put("/{devotional_id}", response_model=DevotionalResponse)
async def update_devotional_endpoint(
    devotional_id: str,
    update_data: DevotionalUpdate,
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Update an existing devotional.
    Only admins can update devotionals.

    **Headers:**
    - Authorization: Bearer {access_token}

    **Path Parameters:**
    - devotional_id: Devotional ID

    **Request Body:**
    - Any fields from DevotionalCreate (all optional)

    **Returns:**
    - Updated devotional data

    **Raises:**
    - 401: Unauthorized
    - 403: Forbidden (not an admin)
    - 404: Devotional not found
    """
    logger.info(f"Updating devotional {devotional_id} by user {current_user.user_id}")
    devotional = await update_devotional(devotional_id, update_data, current_user.user_id)
    logger.info(f"Devotional updated: {devotional_id}")
    return devotional


@router.delete("/{devotional_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_devotional_endpoint(
    devotional_id: str,
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Delete a devotional.
    Only admins can delete devotionals.

    **Headers:**
    - Authorization: Bearer {access_token}

    **Path Parameters:**
    - devotional_id: Devotional ID

    **Returns:**
    - 204 No Content

    **Raises:**
    - 401: Unauthorized
    - 403: Forbidden (not an admin)
    - 404: Devotional not found

    **Note:**
    - Also deletes associated comments, likes, bookmarks
    """
    logger.info(f"Deleting devotional {devotional_id} by user {current_user.user_id}")
    await delete_devotional(devotional_id, current_user.user_id)
    logger.info(f"Devotional deleted: {devotional_id}")
    return None


class BulkDeleteRequest(BaseModel):
    """Request model for bulk delete."""
    devotional_ids: list[str]


class BulkDeleteResponse(BaseModel):
    """Response model for bulk delete."""
    deleted_count: int
    failed_ids: list[str]
    errors: list[str]


@router.post("/bulk-delete", response_model=BulkDeleteResponse)
async def bulk_delete_devotionals_endpoint(
    request: BulkDeleteRequest,
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Delete multiple devotionals in bulk.
    Only admins can delete devotionals.

    **Headers:**
    - Authorization: Bearer {access_token}

    **Request Body:**
    - devotional_ids: List of devotional IDs to delete

    **Returns:**
    - deleted_count: Number of successfully deleted devotionals
    - failed_ids: List of IDs that failed to delete
    - errors: List of error messages

    **Raises:**
    - 401: Unauthorized
    - 403: Forbidden (not an admin)
    - 400: No devotional IDs provided

    **Note:**
    - Also deletes associated comments, likes, bookmarks
    """
    logger.info(f"Bulk delete request by user {current_user.user_id} for {len(request.devotional_ids)} devotionals")

    # Check if user is admin (role check)
    is_admin = current_user.role == "admin"

    result = await bulk_delete_devotionals(
        devotional_ids=request.devotional_ids,
        author_id=current_user.user_id,
        is_admin=is_admin,
    )

    logger.info(
        f"Bulk delete completed: {result['deleted_count']} deleted, "
        f"{len(result['failed_ids'])} failed by user {current_user.user_id}"
    )

    return BulkDeleteResponse(**result)


@router.get("/{devotional_id}/download")
async def download_devotional_endpoint(
    devotional_id: str,
    format: Literal["json", "html", "pdf"] = Query("json", description="Download format"),
    current_user: Optional[TokenData] = Depends(get_current_user_optional),
):
    """
    Download a devotional for offline reading.

    **Path Parameters:**
    - devotional_id: Devotional ID

    **Query Parameters:**
    - format: Download format - "json", "html", or "pdf" (default: "json")

    **Returns:**
    - Devotional content in requested format

    **Auth Required:** No (public devotionals only)
    """
    logger.info(f"Downloading devotional {devotional_id} in {format} format")
    devotional = await get_devotional_by_id(devotional_id)

    if not devotional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devotional not found",
        )

    if format == "json":
        from fastapi.responses import JSONResponse
        return JSONResponse(content=devotional.model_dump())

    elif format == "html":
        from fastapi.responses import HTMLResponse
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{devotional.title}</title>
            <style>
                body {{ font-family: 'DM Sans', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ font-family: 'Cormorant Garamond', serif; color: #1a2332; }}
                .meta {{ color: #718096; margin-bottom: 20px; }}
                .content {{ line-height: 1.75; }}
                .scripture {{ background: #f8f6f3; padding: 15px; border-left: 3px solid #d4a650; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>{devotional.title}</h1>
            <div class="meta">
                <p>By {devotional.author_name} | {devotional.published_at.strftime('%B %d, %Y') if devotional.published_at else 'Draft'}</p>
            </div>
            <div class="content">
        """
        for block in devotional.content:
            if block.type == "scripture":
                html_content += f'<div class="scripture"><strong>{block.scripture_reference or "Scripture"}</strong><br>{block.text}</div>'
            elif block.type == "prayer":
                html_content += f'<div style="font-style: italic; margin: 20px 0;"><strong>Prayer:</strong><br>{block.text}</div>'
            else:
                html_content += f"<p>{block.text}</p>"
        html_content += """
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    elif format == "pdf":
        # PDF generation would require reportlab or similar
        # For now, return HTML that can be printed to PDF
        from fastapi.responses import HTMLResponse
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{devotional.title}</title>
            <style>
                @media print {{ @page {{ margin: 1in; }} }}
                body {{ font-family: 'DM Sans', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ font-family: 'Cormorant Garamond', serif; color: #1a2332; }}
            </style>
        </head>
        <body>
            <h1>{devotional.title}</h1>
            <p>By {devotional.author_name} | {devotional.published_at.strftime('%B %d, %Y') if devotional.published_at else 'Draft'}</p>
        """
        for block in devotional.content:
            html_content += f"<p>{block.text}</p>"
        html_content += "</body></html>"
        return HTMLResponse(content=html_content)

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format. Use 'json', 'html', or 'pdf'",
        )


@router.post("/{devotional_id}/publish", response_model=DevotionalResponse)
async def publish_devotional_endpoint(
    devotional_id: str,
    current_user: TokenData = Depends(get_current_author),
):
    """
    Publish a draft devotional.
    Any authenticated user can publish their own devotionals.

    **Headers:**
    - Authorization: Bearer {access_token}

    **Path Parameters:**
    - devotional_id: Devotional ID

    **Returns:**
    - Published devotional data

    **Raises:**
    - 401: Unauthorized
    - 403: Forbidden (not an admin)
    - 404: Devotional not found
    """
    logger.info(f"Publishing devotional {devotional_id} by user {current_user.user_id}")
    devotional = await publish_devotional(devotional_id, current_user.user_id)
    logger.info(f"Devotional published: {devotional_id}")
    
    # Send auto-notification for new devotional
    try:
        from app.services.notification_service import send_new_devotional_notification
        await send_new_devotional_notification(devotional_id, current_user.user_id)
    except Exception as e:
        logger.error(f"Failed to send new devotional notification: {e}", exc_info=True)
        # Don't fail the publish if notification fails
    
    return devotional
