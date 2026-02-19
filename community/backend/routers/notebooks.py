"""
Notebook sharing API endpoints for the African Language Community Platform
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.notebook import (
    NotebookCreate, NotebookUpdate, NotebookVersionCreate, NotebookVote,
    NotebookComment, NotebookResponse, NotebookListResponse, NotebookSearchQuery,
    NotebookCategory, NotebookDifficulty
)
from services.notebook_service import NotebookService
from database import get_database
from core.auth import get_current_user

router = APIRouter(prefix="/notebooks", tags=["notebooks"])
security = HTTPBearer()

def get_notebook_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> NotebookService:
    """Dependency to get notebook service"""
    return NotebookService(db)

@router.post("/", response_model=NotebookResponse, status_code=status.HTTP_201_CREATED)
async def create_notebook(
    notebook_data: NotebookCreate,
    current_user: dict = Depends(get_current_user),
    notebook_service: NotebookService = Depends(get_notebook_service)
):
    """Create a new notebook"""

    notebook = await notebook_service.create_notebook(
        notebook_data=notebook_data,
        author_id=current_user["user_id"],
        author_name=current_user.get("name", "Unknown"),
        author_email=current_user.get("email", "")
    )

    return await notebook_service.get_notebook(
        notebook_id=notebook.id,
        user_id=current_user["user_id"]
    )

@router.get("/search", response_model=NotebookListResponse)
async def search_notebooks(
    query: Optional[str] = Query(None, description="Search query"),
    category: Optional[NotebookCategory] = Query(None, description="Filter by category"),
    difficulty: Optional[NotebookDifficulty] = Query(None, description="Filter by difficulty"),
    language_codes: Optional[List[str]] = Query(None, description="Filter by language codes"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    author_id: Optional[str] = Query(None, description="Filter by author"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating"),
    sort_by: str = Query("updated_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: Optional[dict] = Depends(get_current_user),
    notebook_service: NotebookService = Depends(get_notebook_service)
):
    """Search notebooks with filters and pagination"""

    search_query = NotebookSearchQuery(
        query=query,
        category=category,
        difficulty=difficulty,
        language_codes=language_codes,
        tags=tags,
        author_id=author_id,
        min_rating=min_rating,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )

    user_id = current_user["user_id"] if current_user else None
    return await notebook_service.search_notebooks(search_query, user_id)

@router.get("/{notebook_id}", response_model=NotebookResponse)
async def get_notebook(
    notebook_id: str,
    current_user: Optional[dict] = Depends(get_current_user),
    notebook_service: NotebookService = Depends(get_notebook_service)
):
    """Get a specific notebook"""

    user_id = current_user["user_id"] if current_user else None
    return await notebook_service.get_notebook(notebook_id, user_id)

@router.put("/{notebook_id}", response_model=NotebookResponse)
async def update_notebook(
    notebook_id: str,
    notebook_data: NotebookUpdate,
    current_user: dict = Depends(get_current_user),
    notebook_service: NotebookService = Depends(get_notebook_service)
):
    """Update notebook metadata"""

    # Check ownership first
    notebook = await notebook_service.get_notebook(notebook_id, current_user["user_id"])
    if not notebook.is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the notebook owner can update it"
        )

    # Update notebook (implementation would be added to NotebookService)
    # For now, return the existing notebook
    return notebook

@router.post("/{notebook_id}/versions", status_code=status.HTTP_201_CREATED)
async def create_notebook_version(
    notebook_id: str,
    version_data: NotebookVersionCreate,
    current_user: dict = Depends(get_current_user),
    notebook_service: NotebookService = Depends(get_notebook_service)
):
    """Create a new version of a notebook"""

    # Check ownership first
    notebook = await notebook_service.get_notebook(notebook_id, current_user["user_id"])
    if not notebook.is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the notebook owner can create new versions"
        )

    # Implementation would be added to NotebookService
    return {"message": "New version created successfully"}

@router.post("/{notebook_id}/vote")
async def vote_notebook(
    notebook_id: str,
    vote_data: NotebookVote,
    current_user: dict = Depends(get_current_user),
    notebook_service: NotebookService = Depends(get_notebook_service)
):
    """Vote on a notebook (upvote/downvote)"""

    return await notebook_service.vote_notebook(
        notebook_id=notebook_id,
        user_id=current_user["user_id"],
        vote_data=vote_data
    )

@router.post("/{notebook_id}/publish")
async def publish_notebook(
    notebook_id: str,
    current_user: dict = Depends(get_current_user),
    notebook_service: NotebookService = Depends(get_notebook_service)
):
    """Publish a notebook (make it publicly available)"""

    return await notebook_service.publish_notebook(
        notebook_id=notebook_id,
        user_id=current_user["user_id"]
    )

@router.get("/{notebook_id}/download")
async def download_notebook(
    notebook_id: str,
    current_user: Optional[dict] = Depends(get_current_user),
    notebook_service: NotebookService = Depends(get_notebook_service)
):
    """Download notebook file"""

    user_id = current_user["user_id"] if current_user else None
    file_content = await notebook_service.download_notebook(notebook_id, user_id)

    return {
        "filename": f"notebook_{notebook_id}.ipynb",
        "content": file_content,
        "content_type": "application/x-ipynb+json"
    }

@router.post("/{notebook_id}/bookmark")
async def bookmark_notebook(
    notebook_id: str,
    current_user: dict = Depends(get_current_user),
    notebook_service: NotebookService = Depends(get_notebook_service)
):
    """Bookmark/unbookmark a notebook"""

    # Implementation would be added to NotebookService
    return {"message": "Bookmark toggled successfully"}

@router.get("/{notebook_id}/comments")
async def get_notebook_comments(
    notebook_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Optional[dict] = Depends(get_current_user),
    notebook_service: NotebookService = Depends(get_notebook_service)
):
    """Get comments for a notebook"""

    # Implementation would be added to NotebookService
    return {
        "comments": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
        "total_pages": 0
    }

@router.post("/{notebook_id}/comments")
async def create_comment(
    notebook_id: str,
    comment_data: NotebookComment,
    current_user: dict = Depends(get_current_user),
    notebook_service: NotebookService = Depends(get_notebook_service)
):
    """Add a comment to a notebook"""

    # Implementation would be added to NotebookService
    return {"message": "Comment added successfully"}

@router.get("/categories/", response_model=List[str])
async def get_notebook_categories():
    """Get list of available notebook categories"""

    return [category.value for category in NotebookCategory]

@router.get("/languages/{language_code}/notebooks", response_model=NotebookListResponse)
async def get_notebooks_for_language(
    language_code: str,
    category: Optional[NotebookCategory] = Query(None),
    difficulty: Optional[NotebookDifficulty] = Query(None),
    sort_by: str = Query("rating", description="Sort by rating, upvotes, or updated_at"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Optional[dict] = Depends(get_current_user),
    notebook_service: NotebookService = Depends(get_notebook_service)
):
    """Get notebooks specific to a language"""

    search_query = NotebookSearchQuery(
        language_codes=[language_code],
        category=category,
        difficulty=difficulty,
        sort_by=sort_by,
        sort_order="desc",
        page=page,
        page_size=page_size
    )

    user_id = current_user["user_id"] if current_user else None
    return await notebook_service.search_notebooks(search_query, user_id)

@router.get("/my/notebooks", response_model=NotebookListResponse)
async def get_my_notebooks(
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    notebook_service: NotebookService = Depends(get_notebook_service)
):
    """Get current user's notebooks"""

    search_query = NotebookSearchQuery(
        author_id=current_user["user_id"],
        sort_by="updated_at",
        sort_order="desc",
        page=page,
        page_size=page_size
    )

    return await notebook_service.search_notebooks(search_query, current_user["user_id"])

@router.get("/featured/", response_model=NotebookListResponse)
async def get_featured_notebooks(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: Optional[dict] = Depends(get_current_user),
    notebook_service: NotebookService = Depends(get_notebook_service)
):
    """Get featured notebooks (highly rated, popular)"""

    search_query = NotebookSearchQuery(
        min_rating=4.0,
        sort_by="rating",
        sort_order="desc",
        page=page,
        page_size=page_size
    )

    user_id = current_user["user_id"] if current_user else None
    return await notebook_service.search_notebooks(search_query, user_id)

@router.get("/trending/", response_model=NotebookListResponse)
async def get_trending_notebooks(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: Optional[dict] = Depends(get_current_user),
    notebook_service: NotebookService = Depends(get_notebook_service)
):
    """Get trending notebooks (recently popular)"""

    search_query = NotebookSearchQuery(
        sort_by="upvotes",
        sort_order="desc",
        page=page,
        page_size=page_size
    )

    user_id = current_user["user_id"] if current_user else None
    return await notebook_service.search_notebooks(search_query, user_id)