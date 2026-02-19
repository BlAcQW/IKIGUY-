"""
Admin API Routes.

Endpoints for admin panel:
- Provider management (STT/TTS configuration)
- Book upload and management
- Usage analytics and metrics
- Provider performance comparison

Requires admin authentication.
"""

import logging
import os
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Header, Request, Query
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# ============================================================================
# SCHEMAS
# ============================================================================

class ProviderConfig(BaseModel):
    """Provider configuration."""
    provider_type: str = Field(..., description="Provider type: stt, tts, llm")
    provider_id: str = Field(..., description="Provider ID: openai, google, elevenlabs, etc.")
    api_key: Optional[str] = Field(None, description="API key (optional, can use env)")
    model: Optional[str] = Field(None, description="Model name")
    voice: Optional[str] = Field(None, description="Voice ID (for TTS)")
    enabled: bool = Field(True, description="Enable/disable provider")
    is_default: bool = Field(False, description="Set as default provider")


class ProviderInfo(BaseModel):
    """Provider information."""
    provider_type: str
    provider_id: str
    name: str
    model: Optional[str] = None
    voice: Optional[str] = None
    enabled: bool = True
    is_default: bool = False
    status: str = "active"  # active, error, disabled
    cost_info: Dict[str, Any] = Field(default_factory=dict)


class BookUploadRequest(BaseModel):
    """Book upload metadata."""
    title: str
    author: str
    description: str
    cover_url: Optional[str] = None
    duration_minutes: Optional[int] = None
    narrator: Optional[str] = None


class BookUploadResponse(BaseModel):
    """Book upload response."""
    book_id: str
    title: str
    status: str  # processing, ready, error
    message: str
    chapters_extracted: int = 0
    processing_time_seconds: Optional[float] = None


class AnalyticsResponse(BaseModel):
    """Admin analytics response."""
    period_start: str
    period_end: str

    # User metrics
    total_users: int
    active_users: int
    new_users: int

    # Usage metrics
    total_events: int
    voice_qa_count: int
    narration_minutes: float
    books_viewed: int
    books_played: int

    # Cost metrics
    total_cost_credits: int
    total_revenue_usd: float
    avg_cost_per_user: int

    # Top books
    top_books: List[Dict[str, Any]]

    # Provider usage
    provider_stats: Dict[str, Any]

    # Time series
    time_series: List[Dict[str, Any]]


class ProviderComparison(BaseModel):
    """Provider performance comparison."""
    stt_providers: List[Dict[str, Any]]
    tts_providers: List[Dict[str, Any]]
    llm_providers: List[Dict[str, Any]]


# ============================================================================
# AUTHENTICATION DEPENDENCY
# ============================================================================

async def get_current_admin_user(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Get current admin user (requires admin role).

    Validates Supabase JWT token and checks admin role.
    Skips authentication for OPTIONS requests (CORS preflight).

    Args:
        request: FastAPI request object (for checking method)
        authorization: Authorization header with Bearer token

    Returns:
        User object (dict) with full user information

    Raises:
        HTTPException: If user is not admin or token invalid
    """
    # Skip authentication for OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        return {"email": "preflight", "sub": "preflight"}

    from app.core.auth import get_current_user
    # Get authenticated user
    user = await get_current_user(authorization)
    # Check if user is admin
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    # Return full user dict for endpoints that need user.get()
    return {
        "sub": user.user_id,
        "id": user.user_id,
        "email": user.email,
        "is_admin": user.is_admin,
        "user_metadata": {"role": "admin"},
        "app_metadata": {"role": "admin"}
    }


# ============================================================================
# PROVIDER MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/providers", response_model=List[ProviderInfo])
async def list_providers(
    provider_type: Optional[str] = None,
    admin_user = Depends(get_current_admin_user)
):
    """
    List all configured providers.

    Args:
        provider_type: Filter by type (stt, tts, llm)
        admin_user: Admin user (from auth)

    Returns:
        List of provider configurations
    """
    from app.services.provider_service import ProviderService

    # Get providers from database
    provider_configs = await ProviderService.list_providers(provider_type)

    # Convert to response model
    providers = []
    for config in provider_configs:
        providers.append(
            ProviderInfo(
                provider_type=config.provider_type,
                provider_id=config.provider_id,
                name=config.name,
                model=config.model,
                voice=config.voice,
                enabled=config.enabled,
                is_default=config.is_default,
                status=config.status,
                cost_info=config.cost_info.model_dump(exclude_none=True)
            )
        )

    logger.info(f"Admin {admin_user.get('email')} listed providers, type={provider_type}, count={len(providers)}")
    return providers


@router.post("/providers", response_model=ProviderInfo)
async def update_provider_config(
    config: ProviderConfig,
    admin_user = Depends(get_current_admin_user)
):
    """
    Update provider configuration.

    Args:
        config: Provider configuration
        admin_user: Admin user (from auth)

    Returns:
        Updated provider info
    """
    from app.services.provider_service import ProviderService
    from app.models.provider import ProviderConfig as ProviderConfigModel, CostInfo

    logger.info(f"Admin {admin_user.get('email')} updating provider: {config.provider_type}/{config.provider_id}")

    # Validate provider type
    if config.provider_type not in ["stt", "tts", "llm"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider type: {config.provider_type}"
        )

    # Get existing provider to preserve fields
    existing = await ProviderService.get_provider(config.provider_type, config.provider_id)

    # Create provider config model
    provider_data = {
        "provider_type": config.provider_type,
        "provider_id": config.provider_id,
        "name": existing.name if existing else f"{config.provider_id.title()} Provider",
        "model": config.model,
        "voice": config.voice,
        "enabled": config.enabled,
        "is_default": config.is_default,
        "status": "active" if config.enabled else "disabled",
        "cost_info": existing.cost_info if existing else CostInfo()
    }

    # If setting as default, update that first
    if config.is_default:
        await ProviderService.set_default_provider(config.provider_type, config.provider_id)

    # Update provider
    updated_provider = await ProviderService.create_or_update_provider(
        ProviderConfigModel(**provider_data)
    )

    # Return updated provider info
    return ProviderInfo(
        provider_type=updated_provider.provider_type,
        provider_id=updated_provider.provider_id,
        name=updated_provider.name,
        model=updated_provider.model,
        voice=updated_provider.voice,
        enabled=updated_provider.enabled,
        is_default=updated_provider.is_default,
        status=updated_provider.status,
        cost_info=updated_provider.cost_info.model_dump(exclude_none=True)
    )


@router.get("/providers/comparison", response_model=ProviderComparison)
async def get_provider_comparison(
    admin_user: str = Depends(get_current_admin_user)
):
    """
    Get provider performance comparison.

    Args:
        admin_user: Admin user (from auth)

    Returns:
        Provider comparison metrics
    """
    # Get analytics service
    try:
        import sys
        sys.path.append('/opt/kasaai/apps/shared')
        from integration.analytics_service import get_analytics_service

        analytics = get_analytics_service()
        comparison_data = await analytics.get_provider_comparison()

        logger.info(f"Admin {admin_user.get('email', admin_user)} retrieved provider comparison")
        return ProviderComparison(**comparison_data)

    except Exception as e:
        logger.error(f"Failed to get provider comparison: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve provider comparison: {str(e)}"
        )


# ============================================================================
# BOOK MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/books/upload", response_model=BookUploadResponse)
async def upload_book(
    title: str = Form(...),
    author: str = Form(...),
    description: str = Form(...),
    cover_image: Optional[UploadFile] = File(None, description="Cover image file (JPG, PNG, WebP)"),
    cover_url: Optional[str] = Form(None, description="Cover image URL (if no file uploaded)"),
    duration_minutes: Optional[int] = Form(None),
    narrator: Optional[str] = Form(None),
    file: UploadFile = File(...),
    admin_user = Depends(get_current_admin_user)
):
    """
    Upload a new book.

    Accepts PDF or EPUB files, processes chapters, and generates embeddings.

    Args:
        title: Book title
        author: Author name
        description: Book description
        cover_image: Cover image file (JPG, PNG, WebP, max 5MB, optional)
        cover_url: Cover image URL (optional, if no file uploaded)
        duration_minutes: Estimated narration duration (optional)
        narrator: Narrator name (optional)
        file: Book file (PDF or EPUB)
        admin_user: Admin user (from auth)

    Returns:
        Upload status and book ID
    """
    import uuid
    from pathlib import Path

    logger.info(f"Admin {admin_user.get('email')} uploading book: {title} by {author}")

    # Validate file type
    allowed_types = ["application/pdf", "application/epub+zip"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file.content_type}. Allowed: PDF, EPUB"
        )

    # Handle cover image upload
    final_cover_url = cover_url
    cover_path = None
    try:
        if cover_image:
            # Validate cover image
            allowed_image_types = ["image/jpeg", "image/png", "image/webp"]
            if cover_image.content_type not in allowed_image_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid cover image format. Allowed: JPG, PNG, WebP"
                )

            # Check file size (max 5MB)
            cover_bytes = await cover_image.read()
            if len(cover_bytes) > 5 * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cover image too large. Maximum size: 5MB"
                )

            # Generate unique filename
            file_ext = cover_image.filename.split('.')[-1] if cover_image.filename and '.' in cover_image.filename else 'jpg'
            cover_filename = f"cover_{uuid.uuid4().hex}.{file_ext}"

            # Save to static/covers directory
            covers_dir = Path(__file__).parent.parent.parent.parent / "static" / "covers"
            covers_dir.mkdir(parents=True, exist_ok=True)
            cover_path = covers_dir / cover_filename

            with open(cover_path, "wb") as f:
                f.write(cover_bytes)

            # Set cover URL to static path
            final_cover_url = f"/static/covers/{cover_filename}"
            logger.info(f"Cover image saved: {final_cover_url}")

        # Read file
        contents = await file.read()
        file_size_mb = len(contents) / (1024 * 1024)

        logger.info(f"Received file: {file.filename}, size={file_size_mb:.2f}MB, type={file.content_type}")

        # Process book file
        from app.services.book_processing_service import BookProcessingService
        import tempfile

        # Save PDF temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name

        processing_service = BookProcessingService()
        await processing_service.initialize()

        book = await processing_service.process_book_file(
            file_path=temp_path,
            book_metadata={
                "title": title,
                "author": author,
                "description": description,
                "cover_url": final_cover_url
            },
            uploaded_by=admin_user.get('sub') or admin_user.get('id')
        )

        # Clean up temp file
        os.remove(temp_path)

        logger.info(f"Book {book.book_id} uploaded successfully")

        return BookUploadResponse(
            book_id=book.book_id,
            title=book.title,
            status=book.processing_status,
            message="Book uploaded and processing started",
            chapters_extracted=len(book.chapters) if book.chapters else 0,
            processing_time_seconds=None
        )

    except HTTPException:
        # Clean up cover image on validation error
        if cover_path and cover_path.exists():
            os.unlink(cover_path)
        raise
    except Exception as e:
        # Clean up cover image on error
        if cover_path and cover_path.exists():
            os.unlink(cover_path)
        logger.error(f"Book upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process book: {str(e)}"
        )


@router.get("/books/{book_id}/status")
async def get_book_processing_status(
    book_id: str,
    admin_user = Depends(get_current_admin_user)
):
    """
    Get book processing status.

    Args:
        book_id: Book ID
        admin_user: Admin user (from auth)

    Returns:
        Processing status
    """
    from app.services.book_processing_service import get_book_processing_service

    processing_service = await get_book_processing_service()
    status_info = await processing_service.get_processing_status(book_id)

    return status_info


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/analytics", response_model=AnalyticsResponse)
async def get_admin_analytics(
    period: str = "month",  # day, week, month, year, all
    admin_user: str = Depends(get_current_admin_user)
):
    """
    Get admin-level analytics (all users).

    Args:
        period: Time period (day, week, month, year, all)
        admin_user: Admin user (from auth)

    Returns:
        Admin analytics data
    """
    try:
        from app.core.database import get_db
        from datetime import datetime, timedelta, timezone
        
        db = get_db()
        
        # Calculate date range based on period
        now = datetime.now(timezone.utc)
        if period == "day":
            start_date = now - timedelta(days=1)
        elif period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now - timedelta(days=30)
        elif period == "year":
            start_date = now - timedelta(days=365)
        else:  # all
            start_date = None
        
        # Get user statistics from MongoDB (consistent with user-stats endpoint)
        total_users = await db.users.count_documents({})
        
        # Active users in the period
        if start_date:
            active_users_query = {
                "last_active": {"$gte": start_date}
            }
        else:
            active_users_query = {
                "last_active": {"$exists": True, "$ne": None}
            }
        active_users = await db.users.count_documents(active_users_query)
        
        # New users in the period
        if start_date:
            new_users_query = {
                "created_at": {"$gte": start_date}
            }
        else:
            new_users_query = {}
        new_users = await db.users.count_documents(new_users_query)
        
        # Get reading sessions in period
        if start_date:
            sessions_query = {
                "last_accessed": {"$gte": start_date}
            }
        else:
            sessions_query = {}
        
        sessions_cursor = db.reading_sessions.find(sessions_query)
        all_sessions = await sessions_cursor.to_list(length=10000)
        
        # Calculate metrics
        total_events = len(all_sessions)
        narration_minutes = sum(s.get("total_time_spent_minutes", 0) for s in all_sessions)
        
        # Get interactions count
        if start_date:
            interactions_query = {
                "created_at": {"$gte": start_date}
            }
        else:
            interactions_query = {}
        voice_qa_count = await db.interactions.count_documents(interactions_query)
        
        # Get unique books accessed
        unique_books_accessed = len(set(
            s.get("book_id") for s in all_sessions if s.get("book_id")
        ))
        
        # Get books viewed (books with at least one session)
        books_viewed = unique_books_accessed
        books_played = unique_books_accessed
        
        # Try to get cost/revenue from shared service, but don't fail if unavailable
        total_cost_credits = 0
        total_revenue_usd = 0.0
        try:
            import sys
            sys.path.append('/opt/kasaai/apps/shared')
            from integration.analytics_service import get_analytics_service
            analytics = get_analytics_service()
            if analytics and hasattr(analytics, 'get_admin_analytics'):
                shared_data = await analytics.get_admin_analytics(period)
                total_cost_credits = shared_data.get("total_cost_credits", 0)
                total_revenue_usd = shared_data.get("total_revenue_usd", 0.0)
        except Exception as e:
            logger.warning(f"Could not get cost/revenue from shared analytics service: {e}")
        
        avg_cost_per_user = int(total_cost_credits / max(active_users, 1))
        
        # Get top books (simplified - can be enhanced)
        top_books = []
        book_stats = {}
        for session in all_sessions:
            book_id = session.get("book_id")
            if book_id:
                if book_id not in book_stats:
                    book_stats[book_id] = {"plays": 0, "qa_count": 0}
                book_stats[book_id]["plays"] += 1
        
        # Get book titles
        books_cursor = db.books.find({})
        books_list = await books_cursor.to_list(length=1000)
        books_dict = {b.get("book_id"): b for b in books_list}
        
        for book_id, stats in sorted(book_stats.items(), key=lambda x: x[1]["plays"], reverse=True)[:10]:
            book_info = books_dict.get(book_id, {})
            top_books.append({
                "book_id": book_id,
                "title": book_info.get("title", "Unknown Book"),
                "plays": stats["plays"],
                "qa_count": stats["qa_count"],
                "avg_rating": None  # Not tracked yet
            })
        
        # Provider stats (simplified - can be enhanced from usage logs)
        provider_stats = {
            "stt": {},
            "tts": {},
            "llm": {}
        }
        
        # Time series (simplified - can be enhanced)
        time_series = []
        
        logger.info(f"Admin {admin_user.get('email', admin_user)} retrieved analytics for period={period}")
        
        return AnalyticsResponse(
            period_start=start_date.isoformat() if start_date else "",
            period_end=now.isoformat(),
            total_users=total_users,
            active_users=active_users,
            new_users=new_users,
            total_events=total_events,
            voice_qa_count=voice_qa_count,
            narration_minutes=narration_minutes,
            books_viewed=books_viewed,
            books_played=books_played,
            total_cost_credits=total_cost_credits,
            total_revenue_usd=total_revenue_usd,
            avg_cost_per_user=avg_cost_per_user,
            top_books=top_books,
            provider_stats=provider_stats,
            time_series=time_series
        )

    except Exception as e:
        logger.error(f"Failed to get analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analytics: {str(e)}"
        )


@router.get("/analytics/users")
async def get_user_analytics(
    limit: int = 50,
    sort_by: str = "usage",  # usage, revenue, signup_date
    admin_user: str = Depends(get_current_admin_user)
):
    """
    Get per-user analytics using MongoDB aggregation for better performance.

    Args:
        limit: Number of users to return
        sort_by: Sort criteria (usage, revenue, signup_date)
        admin_user: Admin user (from auth)

    Returns:
        User analytics data
    """
    try:
        from app.core.database import get_db
        from datetime import datetime

        db = get_db()

        # Use MongoDB aggregation pipeline for efficient data processing
        # This aggregates at the database level instead of loading everything into memory
        pipeline = [
            # Stage 1: Group sessions by user_id to calculate metrics
            {
                "$group": {
                    "_id": "$user_id",
                    "total_listening_minutes": {"$sum": "$total_time_spent_minutes"},
                    "unique_books": {"$addToSet": "$book_id"},
                    "sessions_count": {"$sum": 1}
                }
            },
            # Stage 2: Project to format the data
            {
                "$project": {
                    "user_id": "$_id",
                    "total_listening_minutes": 1,
                    "unique_books_count": {"$size": "$unique_books"},
                    "sessions_count": 1,
                    "_id": 0
                }
            }
        ]

        # Execute aggregation
        sessions_agg = db.reading_sessions.aggregate(pipeline)
        sessions_by_user = {doc["user_id"]: doc async for doc in sessions_agg}

        # Get user documents with selected fields only
        users_cursor = db.users.find(
            {},
            {
                "user_id": 1,
                "email": 1,
                "display_name": 1,
                "created_at": 1,
                "last_active": 1,
                "credits": 1
            }
        )
        users_list = await users_cursor.to_list(length=None)  # Get all users

        # Merge user data with session analytics
        users_analytics = []
        for user_doc in users_list:
            user_id = user_doc.get("user_id")
            if not user_id:
                continue

            # Get session stats from aggregation
            session_stats = sessions_by_user.get(user_id, {})

            # Format timestamps
            last_active = user_doc.get("last_active")
            if isinstance(last_active, datetime):
                last_active = last_active.isoformat()
            elif last_active:
                last_active = str(last_active)
            else:
                last_active = None

            created_at = user_doc.get("created_at")
            if isinstance(created_at, datetime):
                signup_date = created_at.isoformat()
            elif created_at:
                signup_date = str(created_at)
            else:
                signup_date = None

            users_analytics.append({
                "user_id": user_id,
                "email": user_doc.get("email", "unknown"),
                "display_name": user_doc.get("display_name"),
                "signup_date": signup_date,
                "last_active": last_active,
                "total_listening_minutes": session_stats.get("total_listening_minutes", 0),
                "unique_books_count": session_stats.get("unique_books_count", 0),
                "sessions_count": session_stats.get("sessions_count", 0),
                "wallet_balance": user_doc.get("credits", 0)
            })

        # Sort users (Python-side for now, could move to aggregation pipeline)
        if sort_by == "usage":
            users_analytics.sort(key=lambda x: x["total_listening_minutes"], reverse=True)
        elif sort_by == "signup_date":
            users_analytics.sort(key=lambda x: x["signup_date"] or "", reverse=True)
        elif sort_by == "revenue":
            # Note: This sorts by current wallet balance (credits), not actual revenue/payments
            # wallet_balance is user's current credit balance, not total amount paid
            users_analytics.sort(key=lambda x: x["wallet_balance"], reverse=True)

        logger.info(f"Admin {admin_user.get('email', admin_user)} retrieved user analytics, limit={limit}, sort={sort_by}")

        return {
            "users": users_analytics[:limit],
            "total_count": len(users_analytics),
            "sort_by": sort_by
        }

    except Exception as e:
        logger.error(f"Failed to get user analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user analytics: {str(e)}"
        )


@router.get("/analytics/user-stats")
async def get_user_stats(
    admin_user: str = Depends(get_current_admin_user)
):
    """
    Get overall user statistics.
    
    Returns:
        - total_signed_up: Total number of users who signed up
        - total_logged_in: Number of users who have logged in (have last_active)
        - active_users_30d: Users active in last 30 days
        - active_users_7d: Users active in last 7 days
    """
    try:
        from app.core.database import get_db
        from datetime import datetime, timedelta, timezone
        
        db = get_db()
        
        # Total signed up users
        total_signed_up = await db.users.count_documents({})
        
        # Users who have logged in (have last_active set)
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)
        
        # Users with last_active in last 30 days
        active_30d = await db.users.count_documents({
            "last_active": {"$gte": thirty_days_ago}
        })
        
        # Users with last_active in last 7 days
        active_7d = await db.users.count_documents({
            "last_active": {"$gte": seven_days_ago}
        })
        
        # Users who have ever logged in (have last_active)
        total_logged_in = await db.users.count_documents({
            "last_active": {"$exists": True, "$ne": None}
        })
        
        logger.info(f"Admin {admin_user.get('email', admin_user)} retrieved user stats")
        
        return {
            "total_signed_up": total_signed_up,
            "total_logged_in": total_logged_in,
            "active_users_30d": active_30d,
            "active_users_7d": active_7d
        }
        
    except Exception as e:
        logger.error(f"Failed to get user stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user stats: {str(e)}"
        )


@router.get("/analytics/user-activity")
async def get_user_activity_analytics(
    admin_user: str = Depends(get_current_admin_user)
):
    """
    Get analytics on where users spend most of their time.
    
    Returns:
        - page_views: Most visited pages/routes
        - feature_usage: Most used features
        - time_spent_by_feature: Time spent per feature
    """
    try:
        from app.core.database import get_db
        from datetime import datetime, timedelta, timezone
        
        db = get_db()
        
        # Get reading sessions to understand where users spend time
        sessions_cursor = db.reading_sessions.find({})
        all_sessions = await sessions_cursor.to_list(length=10000)
        
        # Calculate total time spent in reading sessions
        total_reading_time = sum(
            s.get("total_time_spent_minutes", 0) for s in all_sessions
        )
        
        # Get interactions count (Q&A usage)
        interactions_count = await db.interactions.count_documents({})
        
        # Get books accessed count
        unique_books_accessed = len(set(
            s.get("book_id") for s in all_sessions if s.get("book_id")
        ))
        
        # Calculate average session duration
        sessions_with_time = [s for s in all_sessions if s.get("total_time_spent_minutes", 0) > 0]
        avg_session_duration = 0
        if sessions_with_time:
            avg_session_duration = sum(
                s.get("total_time_spent_minutes", 0) for s in sessions_with_time
            ) / len(sessions_with_time)

        # Provide descriptive activity breakdown instead of oversimplified "primary"
        # Show hours of reading vs number of Q&A interactions for admin to interpret
        reading_hours = round(total_reading_time / 60, 1)
        primary_activity = f"Reading: {reading_hours}h | Q&A: {interactions_count} interactions"

        logger.info(f"Admin {admin_user.get('email', admin_user)} retrieved user activity analytics")

        return {
            "total_reading_time_minutes": total_reading_time,
            "total_interactions": interactions_count,
            "unique_books_accessed": unique_books_accessed,
            "total_sessions": len(all_sessions),
            "average_session_duration_minutes": round(avg_session_duration, 2),
            "primary_activity": primary_activity
        }
        
    except Exception as e:
        logger.error(f"Failed to get user activity analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user activity analytics: {str(e)}"
        )


@router.get("/analytics/currently-logged-in")
async def get_currently_logged_in_users(
    admin_user: str = Depends(get_current_admin_user)
):
    """
    Get users who are currently logged in (active in last 15 minutes).

    Returns:
        - count: Number of currently logged in users
        - users: List of user details with last activity
    """
    try:
        from app.core.database import get_db
        from datetime import datetime, timedelta, timezone

        db = get_db()

        # Consider users logged in if active in last 15 minutes
        now = datetime.now(timezone.utc)
        fifteen_minutes_ago = now - timedelta(minutes=15)

        # Find users with recent activity
        users_cursor = db.users.find({
            "last_active": {"$gte": fifteen_minutes_ago}
        })
        users_list = await users_cursor.to_list(length=None)

        # Format user data
        logged_in_users = []
        for user in users_list:
            last_active = user.get("last_active")
            if isinstance(last_active, datetime):
                # Ensure last_active is timezone-aware for comparison
                if last_active.tzinfo is None:
                    last_active = last_active.replace(tzinfo=timezone.utc)
                last_active_str = last_active.isoformat()
                minutes_ago = int((now - last_active).total_seconds() / 60)
            else:
                last_active_str = None
                minutes_ago = None

            logged_in_users.append({
                "user_id": user.get("user_id"),
                "email": user.get("email", "unknown"),
                "display_name": user.get("display_name"),
                "last_active": last_active_str,
                "minutes_ago": minutes_ago
            })

        # Sort by most recent activity
        logged_in_users.sort(key=lambda x: x["minutes_ago"] if x["minutes_ago"] is not None else 999)

        logger.info(f"Admin {admin_user.get('email', admin_user)} retrieved currently logged in users: {len(logged_in_users)}")

        return {
            "count": len(logged_in_users),
            "users": logged_in_users,
            "threshold_minutes": 15
        }

    except Exception as e:
        logger.error(f"Failed to get currently logged in users: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve currently logged in users: {str(e)}"
        )


@router.get("/analytics/currently-listening")
async def get_currently_listening_users(
    admin_user: str = Depends(get_current_admin_user)
):
    """
    Get users who are currently listening to books (active session in last 3 minutes).

    Returns:
        - count: Number of currently listening users
        - users: List of user details with book being listened to
    """
    try:
        from app.core.database import get_db
        from datetime import datetime, timedelta, timezone

        db = get_db()

        # Consider users listening if session updated in last 3 minutes
        now = datetime.now(timezone.utc)
        three_minutes_ago = now - timedelta(minutes=3)

        # Find recently active reading sessions
        sessions_cursor = db.reading_sessions.find({
            "last_accessed": {"$gte": three_minutes_ago},
            "completed": False
        })
        active_sessions = await sessions_cursor.to_list(length=None)

        # Get unique users and their sessions
        user_session_map = {}
        for session in active_sessions:
            user_id = session.get("user_id")
            if user_id and user_id not in user_session_map:
                user_session_map[user_id] = session
            elif user_id and session.get("last_accessed", datetime.min) > user_session_map[user_id].get("last_accessed", datetime.min):
                # Keep most recent session if user has multiple
                user_session_map[user_id] = session

        # Get user and book details
        user_ids = list(user_session_map.keys())
        users_cursor = db.users.find({"user_id": {"$in": user_ids}})
        users_list = await users_cursor.to_list(length=None)
        users_dict = {u.get("user_id"): u for u in users_list}

        book_ids = [s.get("book_id") for s in user_session_map.values() if s.get("book_id")]
        books_cursor = db.books.find({"book_id": {"$in": book_ids}})
        books_list = await books_cursor.to_list(length=None)
        books_dict = {b.get("book_id"): b for b in books_list}

        # Format listening data
        listening_users = []
        for user_id, session in user_session_map.items():
            user_info = users_dict.get(user_id, {})
            book_id = session.get("book_id")
            book_info = books_dict.get(book_id, {})

            last_accessed = session.get("last_accessed")
            if isinstance(last_accessed, datetime):
                # Ensure last_accessed is timezone-aware for comparison
                if last_accessed.tzinfo is None:
                    last_accessed = last_accessed.replace(tzinfo=timezone.utc)
                last_accessed_str = last_accessed.isoformat()
                seconds_ago = int((now - last_accessed).total_seconds())
            else:
                last_accessed_str = None
                seconds_ago = None

            # Calculate progress
            current_chunk = session.get("current_chunk_index", 0)
            total_chunks = book_info.get("total_chunks", 0)
            if total_chunks > 0:
                progress_percentage = round(((current_chunk + 1) / total_chunks) * 100, 2)
            else:
                progress_percentage = 0

            listening_users.append({
                "user_id": user_id,
                "email": user_info.get("email", "unknown"),
                "display_name": user_info.get("display_name"),
                "book_id": book_id,
                "book_title": book_info.get("title", "Unknown Book"),
                "book_author": book_info.get("author", "Unknown Author"),
                "book_cover_url": book_info.get("cover_url"),
                "current_chunk_index": current_chunk,
                "total_chunks": total_chunks,
                "progress_percentage": progress_percentage,
                "last_accessed": last_accessed_str,
                "seconds_ago": seconds_ago
            })

        # Sort by most recent activity
        listening_users.sort(key=lambda x: x["seconds_ago"] if x["seconds_ago"] is not None else 999)

        logger.info(f"Admin {admin_user.get('email', admin_user)} retrieved currently listening users: {len(listening_users)}")

        return {
            "count": len(listening_users),
            "users": listening_users,
            "threshold_minutes": 3
        }

    except Exception as e:
        logger.error(f"Failed to get currently listening users: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve currently listening users: {str(e)}"
        )


@router.get("/analytics/user-book-progress")
async def get_user_book_progress(
    user_id: Optional[str] = None,
    limit: int = 100,
    admin_user: str = Depends(get_current_admin_user)
):
    """
    Get book playback progress for users.
    
    Args:
        user_id: Optional user ID to filter by (if not provided, returns all users)
        limit: Maximum number of records to return
        
    Returns:
        List of user-book progress records showing how much each user has played of each book
    """
    try:
        from app.core.database import get_db
        from datetime import datetime
        
        db = get_db()
        
        # Build query
        query = {}
        if user_id:
            query["user_id"] = user_id
        
        # Get reading sessions with book information
        sessions_cursor = db.reading_sessions.find(query)
        sessions = await sessions_cursor.to_list(length=limit * 2)
        
        # Get book information
        books_cursor = db.books.find({})
        books_list = await books_cursor.to_list(length=1000)
        books_dict = {b.get("book_id"): b for b in books_list}
        
        # Get user information
        users_cursor = db.users.find({})
        users_list = await users_cursor.to_list(length=1000)
        users_dict = {u.get("user_id"): u for u in users_list}
        
        # Aggregate sessions by user+book combination
        user_book_map = {}
        for session in sessions:
            user_id_val = session.get("user_id")
            book_id = session.get("book_id")

            if not user_id_val or not book_id:
                continue

            key = f"{user_id_val}:{book_id}"

            # Get session data
            current_chunk = session.get("current_chunk_index", 0)
            time_spent = session.get("total_time_spent_minutes", 0)
            is_completed = session.get("completed", False)
            last_accessed = session.get("last_accessed")

            # Aggregate: sum time, keep latest chunk position
            if key in user_book_map:
                user_book_map[key]["time_spent_minutes"] += time_spent
                user_book_map[key]["is_completed"] = user_book_map[key]["is_completed"] or is_completed
                # Keep the most advanced progress
                if current_chunk > user_book_map[key]["current_chunk_index"]:
                    user_book_map[key]["current_chunk_index"] = current_chunk
                # Keep most recent access time
                if last_accessed and (not user_book_map[key]["last_accessed"] or last_accessed > user_book_map[key]["last_accessed"]):
                    user_book_map[key]["last_accessed"] = last_accessed
            else:
                user_info = users_dict.get(user_id_val, {})
                book_info = books_dict.get(book_id, {})

                # Get total_chunks from book, fallback to counting chunks
                total_chunks = book_info.get("total_chunks")
                if not total_chunks or total_chunks == 0:
                    # Fallback: count actual chunks in book_chunks collection
                    total_chunks = await db.book_chunks.count_documents({"book_id": book_id})

                progress_percentage = 0
                if total_chunks > 0:
                    # Add 1 to current_chunk since chunks are 0-indexed
                    # Chunk 0 means user has listened to 1 chunk (the first one)
                    progress_percentage = round(((current_chunk + 1) / total_chunks) * 100, 2)

                user_book_map[key] = {
                    "user_id": user_id_val,
                    "user_email": user_info.get("email", "unknown"),
                    "user_display_name": user_info.get("display_name"),
                    "book_id": book_id,
                    "book_title": book_info.get("title", "Unknown Book"),
                    "book_author": book_info.get("author", "Unknown Author"),
                    "current_chunk_index": current_chunk,
                    "total_chunks": total_chunks,
                    "progress_percentage": progress_percentage,
                    "time_spent_minutes": time_spent,
                    "is_completed": is_completed,
                    "last_accessed": last_accessed
                }

        # Convert to list and format
        progress_records = []
        for record in user_book_map.values():
            # Recalculate progress percentage with final chunk position
            # Add 1 to current_chunk_index since chunks are 0-indexed
            if record["total_chunks"] > 0:
                record["progress_percentage"] = round(((record["current_chunk_index"] + 1) / record["total_chunks"]) * 100, 2)

            # Add progress validation flag to detect suspicious patterns
            # Estimate: ~3-5 minutes per chunk on average for typical audiobooks
            # If progress is high but time spent is very low, likely skipped ahead
            progress_quality = "normal"
            if record["total_chunks"] > 0 and record["progress_percentage"] > 0:
                # Calculate chunks listened (current_chunk_index + 1 since 0-indexed)
                chunks_listened = record["current_chunk_index"] + 1
                # Estimate minimum expected time: 2 minutes per chunk (very fast reading)
                expected_min_time = chunks_listened * 2
                time_spent = record["time_spent_minutes"]

                if record["progress_percentage"] >= 90 and time_spent < expected_min_time * 0.3:
                    progress_quality = "likely_skipped"  # High progress, very low time
                elif time_spent < expected_min_time * 0.5:
                    progress_quality = "suspicious"  # Progress faster than realistic
                elif time_spent >= expected_min_time:
                    progress_quality = "sequential"  # Realistic progression

            record["progress_quality"] = progress_quality

            # Format last_accessed
            last_accessed = record["last_accessed"]
            if isinstance(last_accessed, datetime):
                record["last_accessed"] = last_accessed.isoformat()
            elif last_accessed:
                record["last_accessed"] = str(last_accessed)
            else:
                record["last_accessed"] = None

            progress_records.append(record)

        # Sort by time spent (descending) - users with most listening time first
        progress_records.sort(key=lambda x: x["time_spent_minutes"], reverse=True)
        
        logger.info(f"Admin {admin_user.get('email', admin_user)} retrieved book progress for {len(progress_records)} records")
        
        return {
            "progress_records": progress_records[:limit],
            "total_count": len(progress_records),
            "filtered_by_user": user_id is not None
        }
        
    except Exception as e:
        logger.error(f"Failed to get user book progress: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user book progress: {str(e)}"
        )


# ============================================================================
# BOOK MODERATION ENDPOINTS
# ============================================================================

@router.post("/books/{book_id}/hide")
async def hide_book(
    book_id: str,
    reason: str = Query(..., min_length=10, description="Reason for hiding the book"),
    user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """
    Hide a book (admin action - soft delete).

    The book will be hidden from public listings but remain visible to the uploader
    with a "Hidden by Admin" badge.

    Args:
        book_id: Book identifier
        reason: Reason for hiding (minimum 10 characters)
        user: Admin user (from auth dependency)

    Returns:
        Success message
    """
    try:
        from app.services.book_service import BookService
        from app.core.database import get_db

        # Extract admin info
        admin_id = user.get("sub") or user.get("id")
        admin_email = user.get("email", "")
        user_metadata = user.get("user_metadata", {})
        app_metadata = user.get("app_metadata", {})
        admin_role = user_metadata.get("role") or app_metadata.get("role") or "admin"

        db = get_db()
        book_service = BookService()

        # Hide the book
        success = await book_service.hide_book(
            book_id=book_id,
            admin_id=admin_id,
            admin_email=admin_email,
            admin_role=admin_role,
            reason=reason
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail="Book not found or could not be hidden"
            )

        logger.info(f"Admin {admin_email} hid book {book_id}: {reason}")

        return {
            "success": True,
            "message": f"Book hidden successfully",
            "book_id": book_id,
            "reason": reason
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to hide book: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to hide book: {str(e)}"
        )


@router.post("/books/{book_id}/unhide")
async def unhide_book(
    book_id: str,
    reason: Optional[str] = Query(None, description="Optional reason for unhiding"),
    user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """
    Unhide a previously hidden book (admin action).

    Restores the book to its previous visibility state.

    Args:
        book_id: Book identifier
        reason: Optional reason for unhiding
        user: Admin user (from auth dependency)

    Returns:
        Success message
    """
    try:
        from app.services.book_service import BookService
        from app.core.database import get_db

        # Extract admin info
        admin_id = user.get("sub") or user.get("id")
        admin_email = user.get("email", "")
        user_metadata = user.get("user_metadata", {})
        app_metadata = user.get("app_metadata", {})
        admin_role = user_metadata.get("role") or app_metadata.get("role") or "admin"

        db = get_db()
        book_service = BookService()

        # Unhide the book
        success = await book_service.unhide_book(
            book_id=book_id,
            admin_id=admin_id,
            admin_email=admin_email,
            admin_role=admin_role,
            reason=reason
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail="Book not found or could not be unhidden"
            )

        logger.info(f"Admin {admin_email} unhid book {book_id}")

        return {
            "success": True,
            "message": f"Book unhidden successfully",
            "book_id": book_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unhide book: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to unhide book: {str(e)}"
        )


@router.delete("/books/{book_id}/permanent")
async def permanently_delete_book(
    book_id: str,
    reason: str = Query(..., min_length=10, description="Reason for permanent deletion"),
    confirm: bool = Query(..., description="Must be true to confirm deletion"),
    user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """
    Permanently delete a book (admin action - cannot be undone).

    WARNING: This action is permanent and cannot be reversed.
    All book data, chapters, audio files, and embeddings will be deleted.

    Args:
        book_id: Book identifier
        reason: Reason for deletion (minimum 10 characters)
        confirm: Must be true to confirm (safety check)
        user: Admin user (from auth dependency)

    Returns:
        Success message
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must set confirm=true to permanently delete a book"
        )

    try:
        from app.services.book_service import book_service
        from app.services.audit_log_service import AuditLogService
        from app.models.audit_log import AuditAction
        from app.core.database import get_db

        # Extract admin info
        admin_id = user.get("sub") or user.get("id")
        admin_email = user.get("email", "")
        user_metadata = user.get("user_metadata", {})
        app_metadata = user.get("app_metadata", {})
        admin_role = user_metadata.get("role") or app_metadata.get("role") or "admin"

        db = get_db()

        # Get book info before deletion for audit log
        book = await db.books.find_one({"book_id": book_id})
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        # Create audit log BEFORE deletion
        audit_service = AuditLogService(db)
        await audit_service.log_action(
            action=AuditAction.BOOK_PERMANENTLY_DELETED,
            entity_id=book_id,
            actor_id=admin_id,
            actor_email=admin_email,
            actor_role=admin_role,
            reason=reason,
            changes={},
            metadata={
                "book_title": book.get("title"),
                "book_author": book.get("author"),
                "uploader_id": book.get("uploaded_by"),
                "visibility": book.get("visibility"),
                "warning": "PERMANENT DELETION - CANNOT BE UNDONE"
            }
        )

        # Permanently delete the book
        result = await book_service.delete_book_complete(book_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Book not found or could not be deleted"
            )

        logger.warning(f"Admin {admin_email} PERMANENTLY DELETED book {book_id}: {reason}")

        return {
            "success": True,
            "message": f"Book permanently deleted",
            "book_id": book_id,
            "warning": "This action cannot be undone"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to permanently delete book: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete book: {str(e)}"
        )


@router.get("/books/hidden")
async def list_hidden_books(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """
    List all hidden books (admin only).

    Shows books that have been hidden by admins with hide reason and timestamp.

    Args:
        page: Page number (1-indexed)
        per_page: Items per page
        user: Admin user (from auth dependency)

    Returns:
        List of hidden books with moderation info
    """
    try:
        from app.core.database import get_db

        db = get_db()

        # Query for hidden books
        query = {
            "is_hidden": True,
            "is_deleted": {"$ne": True}
        }

        # Calculate skip
        skip = (page - 1) * per_page

        # Get total count
        total = await db.books.count_documents(query)

        # Get hidden books
        cursor = db.books.find(query).sort("hidden_at", -1).skip(skip).limit(per_page)
        books = []

        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            books.append({
                "id": doc["book_id"],
                "title": doc["title"],
                "author": doc["author"],
                "description": doc.get("description"),
                "cover_url": doc.get("cover_url"),
                "uploaded_by": doc.get("uploaded_by"),
                "visibility": doc.get("visibility", "private"),
                "hidden_by": doc.get("hidden_by"),
                "hidden_by_email": doc.get("hidden_by_email"),
                "hidden_at": doc.get("hidden_at").isoformat() if doc.get("hidden_at") else None,
                "hidden_reason": doc.get("hidden_reason")
            })

        logger.info(f"Admin {user.get('email')} listed {len(books)} hidden books")

        return {
            "books": books,
            "total": total,
            "page": page,
            "per_page": per_page
        }

    except Exception as e:
        logger.error(f"Failed to list hidden books: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list hidden books: {str(e)}"
        )


@router.get("/audit-log")
async def get_audit_log(
    book_id: Optional[str] = Query(None, description="Filter by book ID"),
    admin_id: Optional[str] = Query(None, description="Filter by admin user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    limit: int = Query(50, ge=1, le=500, description="Number of records to return"),
    user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """
    Get audit log of admin actions (admin only).

    Shows all moderation actions (hide, unhide, delete, restore) with full details.

    Args:
        book_id: Optional book ID filter
        admin_id: Optional admin user ID filter
        action: Optional action type filter
        limit: Number of records to return
        user: Admin user (from auth dependency)

    Returns:
        List of audit log entries
    """
    try:
        from app.services.audit_log_service import AuditLogService
        from app.core.database import get_db

        db = get_db()
        audit_service = AuditLogService(db)

        if book_id:
            # Get audit trail for specific book
            logs = await audit_service.get_book_audit_trail(book_id, limit=limit)
        else:
            # Get admin activity logs
            logs = await audit_service.get_admin_activity(
                admin_id=admin_id,
                action=action,
                limit=limit
            )

        logger.info(f"Admin {user.get('email')} retrieved audit log (filters: book_id={book_id}, admin_id={admin_id}, action={action})")

        return {
            "logs": logs,
            "total": len(logs),
            "filters": {
                "book_id": book_id,
                "admin_id": admin_id,
                "action": action
            }
        }

    except Exception as e:
        logger.error(f"Failed to get audit log: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve audit log: {str(e)}"
        )
