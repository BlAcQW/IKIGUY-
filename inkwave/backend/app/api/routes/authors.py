"""
Authors API routes.

Endpoints for managing authors, searching authors, and author profiles.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr
import uuid

from app.core.auth import get_current_user
from app.core.database import get_db


router = APIRouter(prefix="/authors", tags=["authors"])


class AuthorCreateRequest(BaseModel):
    """Request to create a new author."""

    display_name: str
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class AuthorResponse(BaseModel):
    """Author information response."""

    user_id: str
    display_name: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    username: Optional[str] = None
    books_count: int = 0
    created_at: datetime


class AuthorSearchResponse(BaseModel):
    """Author search results."""

    authors: List[AuthorResponse]
    total: int


@router.get("/search", response_model=AuthorSearchResponse)
async def search_authors(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """
    Search for authors by name.

    Searches display_name, first_name, last_name, and username fields.
    Returns authors matching the query with their book counts.

    Args:
        q: Search query string
        limit: Maximum number of results to return (1-50)
        current_user: Current authenticated user

    Returns:
        AuthorSearchResponse with matching authors and total count
    """
    db = get_db()

    # Create case-insensitive regex search
    search_regex = {"$regex": q, "$options": "i"}

    # Search query - find users with author role matching the query
    search_query = {
        "role": "author",
        "$or": [
            {"display_name": search_regex},
            {"first_name": search_regex},
            {"last_name": search_regex},
            {"username": search_regex}
        ]
    }

    # Get matching authors
    authors_cursor = db.users.find(search_query).limit(limit)
    authors = await authors_cursor.to_list(length=limit)

    # Get total count
    total = await db.users.count_documents(search_query)

    # Get book counts for each author
    author_responses = []
    for author in authors:
        # Count books by this author
        books_count = await db.books.count_documents({
            "author_id": author["user_id"]
        })

        author_responses.append(AuthorResponse(
            user_id=author["user_id"],
            display_name=author.get("display_name", "Unknown Author"),
            email=author.get("email"),
            first_name=author.get("first_name"),
            last_name=author.get("last_name"),
            bio=author.get("bio"),
            avatar_url=author.get("avatar_url"),
            username=author.get("username"),
            books_count=books_count,
            created_at=author.get("created_at", datetime.utcnow())
        ))

    return AuthorSearchResponse(authors=author_responses, total=total)


@router.get("/", response_model=AuthorSearchResponse)
async def list_authors(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """
    List all authors.

    Returns paginated list of all users with author role.

    Args:
        limit: Maximum number of results (1-100)
        offset: Number of results to skip for pagination
        current_user: Current authenticated user

    Returns:
        AuthorSearchResponse with authors and total count
    """
    db = get_db()

    # Query for all authors
    query = {"role": "author"}

    # Get authors with pagination
    authors_cursor = db.users.find(query).skip(offset).limit(limit).sort("display_name", 1)
    authors = await authors_cursor.to_list(length=limit)

    # Get total count
    total = await db.users.count_documents(query)

    # Get book counts for each author
    author_responses = []
    for author in authors:
        books_count = await db.books.count_documents({
            "author_id": author["user_id"]
        })

        author_responses.append(AuthorResponse(
            user_id=author["user_id"],
            display_name=author.get("display_name", "Unknown Author"),
            email=author.get("email"),
            first_name=author.get("first_name"),
            last_name=author.get("last_name"),
            bio=author.get("bio"),
            avatar_url=author.get("avatar_url"),
            username=author.get("username"),
            books_count=books_count,
            created_at=author.get("created_at", datetime.utcnow())
        ))

    return AuthorSearchResponse(authors=author_responses, total=total)


@router.post("/", response_model=AuthorResponse)
async def create_author(
    author_data: AuthorCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new author account.

    Only admins can create author accounts.
    Generates a unique user_id and email if not provided.

    Args:
        author_data: Author information
        current_user: Current authenticated user (must be admin)

    Returns:
        AuthorResponse with created author information

    Raises:
        HTTPException: If user is not admin or author already exists
    """
    db = get_db()

    # Check if user is admin
    user = await db.users.find_one({"user_id": current_user["sub"]})
    if not user or (user.get("role") not in ["admin", "superadmin"] and not user.get("is_admin")):
        raise HTTPException(status_code=403, detail="Only admins can create author accounts")

    # Check if author with same display_name already exists
    existing = await db.users.find_one({
        "display_name": author_data.display_name,
        "role": "author"
    })
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Author '{author_data.display_name}' already exists"
        )

    # Generate user_id
    author_user_id = f"author_{uuid.uuid4().hex[:12]}"

    # Generate email if not provided
    if not author_data.email:
        # Create email from display_name
        email_name = author_data.display_name.lower().replace(" ", ".")
        author_email = f"{email_name}@inkwave.author"
    else:
        author_email = author_data.email

    # Generate username from display_name
    username = author_data.display_name.lower().replace(" ", "_").replace("-", "_")
    username = ''.join(c for c in username if c.isalnum() or c == '_')

    # Create author document
    author_doc = {
        "user_id": author_user_id,
        "email": author_email,
        "display_name": author_data.display_name,
        "first_name": author_data.first_name,
        "last_name": author_data.last_name,
        "bio": author_data.bio,
        "avatar_url": author_data.avatar_url,
        "username": username,
        "role": "author",
        "is_admin": False,
        "credits": 0,
        "wallet_id": None,
        "library_books": [],
        "profile": {
            "preferred_voice": "nova",
            "playback_speed": 1.0,
            "reading_level": "intermediate",
            "voice_preferences": {
                "provider_id": "coqui_xtts",
                "voice_id": "nova",
                "speed": 1.0,
                "language": "en"
            },
            "interaction_preferences": {
                "explanation_depth": "detailed",
                "discussion_topics": ["themes", "characters", "context"]
            }
        },
        "privacy_settings": {
            "profile_visibility": "public",
            "show_currently_reading": True,
            "show_reading_history": True,
            "show_library": True,
            "show_listening_stats": True,
            "show_followers_list": True,
            "show_following_list": True,
            "show_follower_count": True,
            "show_following_count": True,
            "appear_in_leaderboard": False,
            "leaderboard_display_mode": "opt_out",
            "discoverable_by_search": True,
            "allow_follow_requests": True,
            "require_follow_approval": False,
            "updated_at": datetime.utcnow()
        },
        "social_stats": {
            "followers_count": 0,
            "following_count": 0,
            "total_listening_hours": 0.0,
            "books_completed": 0,
            "current_streak_days": 0,
            "last_stats_update": datetime.utcnow()
        },
        "created_at": datetime.utcnow(),
        "last_active": datetime.utcnow()
    }

    # Insert into database
    await db.users.insert_one(author_doc)

    return AuthorResponse(
        user_id=author_user_id,
        display_name=author_data.display_name,
        email=author_email,
        first_name=author_data.first_name,
        last_name=author_data.last_name,
        bio=author_data.bio,
        avatar_url=author_data.avatar_url,
        username=username,
        books_count=0,
        created_at=author_doc["created_at"]
    )


@router.get("/{author_id}", response_model=AuthorResponse)
async def get_author(
    author_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get author details by ID.

    Args:
        author_id: Author user_id
        current_user: Current authenticated user

    Returns:
        AuthorResponse with author information

    Raises:
        HTTPException: If author not found
    """
    db = get_db()

    # Find author
    author = await db.users.find_one({"user_id": author_id, "role": "author"})
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    # Get book count
    books_count = await db.books.count_documents({"author_id": author_id})

    return AuthorResponse(
        user_id=author["user_id"],
        display_name=author.get("display_name", "Unknown Author"),
        email=author.get("email"),
        first_name=author.get("first_name"),
        last_name=author.get("last_name"),
        bio=author.get("bio"),
        avatar_url=author.get("avatar_url"),
        username=author.get("username"),
        books_count=books_count,
        created_at=author.get("created_at", datetime.utcnow())
    )
