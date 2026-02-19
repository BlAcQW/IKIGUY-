"""
Devotional service for devotional CRUD operations and management.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from bson import ObjectId

from app.db.mongodb import get_database
from app.models.devotional import (
    DevotionalCreate,
    DevotionalUpdate,
    DevotionalInDB,
    DevotionalResponse,
    DevotionalListResponse,
    DevotionalFilters,
    generate_slug,
    generate_excerpt,
    estimate_reading_time,
)
import logging

logger = logging.getLogger(__name__)


async def _get_series_max_part(db, series_id: ObjectId) -> int:
    """Get the maximum part number for a series."""
    result = await db.devotionals.find_one(
        {"series_id": series_id},
        sort=[("part_number", -1)]
    )
    if result and result.get("part_number"):
        return result["part_number"]
    return 0


async def create_devotional(devotional_data: DevotionalCreate, author_id: str) -> DevotionalResponse:
    """
    Create a new devotional.

    Args:
        devotional_data (DevotionalCreate): Devotional creation data.
        author_id (str): Author user ID.

    Returns:
        DevotionalResponse: Created devotional data.
    """
    try:
        db = get_database()

        # Validate author_id
        if not ObjectId.is_valid(author_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid author ID",
            )

        # Get author information
        author = await db.users.find_one({"_id": ObjectId(author_id)})
        if not author:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Author not found",
            )

        # Generate slug from title
        slug = generate_slug(devotional_data.title)

        # Check if slug already exists
        existing = await db.devotionals.find_one({"slug": slug})
        if existing:
            # Append timestamp to make unique
            slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

        # Generate excerpt
        excerpt = generate_excerpt(devotional_data.content)

        # Estimate reading time
        reading_time = estimate_reading_time(devotional_data.content)

        # Handle series creation/assignment
        series_id = None
        series_name = None
        if devotional_data.series_id:
            # Use existing series
            if not ObjectId.is_valid(devotional_data.series_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid series ID",
                )
            series_id = ObjectId(devotional_data.series_id)
            # Get series name from existing series
            series = await db.series.find_one({"_id": series_id})
            if not series:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Series not found",
                )
            series_name = series.get("name")
        elif devotional_data.series_name:
            # Create new series
            series_slug = generate_slug(devotional_data.series_name)
            # Check if series with same name exists
            existing_series = await db.series.find_one({"slug": series_slug, "author_id": ObjectId(author_id)})
            if existing_series:
                series_id = existing_series["_id"]
                series_name = existing_series.get("name")
            else:
                # Create new series
                # If this is part 1 and has scheduled_at, use it as start_date
                series_start_date = None
                if devotional_data.part_number == 1 and devotional_data.scheduled_at:
                    series_start_date = devotional_data.scheduled_at
                
                new_series = {
                    "name": devotional_data.series_name,
                    "slug": series_slug,
                    "author_id": ObjectId(author_id),
                    "description": None,
                    "cover_image_url": None,
                    "total_parts": 0,
                    "start_date": series_start_date,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
                result = await db.series.insert_one(new_series)
                series_id = result.inserted_id
                series_name = devotional_data.series_name

        # Create devotional document
        devotional_dict = devotional_data.model_dump(mode="json")
        # Content blocks are already dicts from model_dump(mode="json")
        # Ensure content blocks have all required fields
        for block in devotional_dict.get("content", []):
            if isinstance(block, dict):
                if "type" not in block:
                    raise ValueError("Content block missing 'type' field")
                if "text" not in block:
                    raise ValueError("Content block missing 'text' field")
                # Ensure scripture_reference is None (not missing) for non-scripture blocks
                if block.get("type") != "scripture" and "scripture_reference" not in block:
                    block["scripture_reference"] = None
        
        devotional_dict["author_id"] = ObjectId(author_id)
        devotional_dict["author_name"] = author.get("name", "Unknown Author")
        devotional_dict["author_avatar"] = author.get("avatar_url")
        devotional_dict["slug"] = slug
        devotional_dict["excerpt"] = excerpt
        devotional_dict["reading_time_minutes"] = reading_time
        devotional_dict["created_at"] = datetime.utcnow()
        devotional_dict["updated_at"] = datetime.utcnow()
        
        # Add series fields
        if series_id:
            devotional_dict["series_id"] = series_id
            devotional_dict["series_name"] = series_name
            devotional_dict["part_number"] = devotional_data.part_number or 1
            # Update series total_parts if needed
            if devotional_data.part_number:
                await db.series.update_one(
                    {"_id": series_id},
                    {"$set": {"total_parts": max(devotional_data.part_number, await _get_series_max_part(db, series_id))}}
                )
        else:
            # Remove series fields if not part of series
            devotional_dict.pop("series_id", None)
            devotional_dict.pop("series_name", None)
            devotional_dict.pop("part_number", None)

        # Set published_at if status is published
        if devotional_data.status == "published":
            # Use provided published_at if available, otherwise use current time
            devotional_dict["published_at"] = devotional_data.published_at or datetime.utcnow()
        
        # Set scheduled_at if provided (for calendar view)
        # This allows calendar to show devotionals even if they're published
        if devotional_data.scheduled_at:
            devotional_dict["scheduled_at"] = devotional_data.scheduled_at
        elif devotional_data.status == "scheduled" and not devotional_data.scheduled_at:
            # If status is scheduled but no scheduled_at provided, use published_at or current time
            devotional_dict["scheduled_at"] = devotional_data.published_at or datetime.utcnow()

        # Calculate day of year (1-365 or 1-366)
        # Use scheduled_at if available, otherwise published_at, otherwise current date
        from datetime import date as date_type
        date_for_day = devotional_dict.get("scheduled_at") or devotional_dict.get("published_at") or datetime.utcnow()
        
        # Convert to date object
        if isinstance(date_for_day, datetime):
            date_obj = date_for_day.date()
        elif isinstance(date_for_day, date_type):
            date_obj = date_for_day
        else:
            date_obj = datetime.utcnow().date()
        
        # Calculate day of year
        start_of_year = date_type(date_obj.year, 1, 1)
        day_of_year = (date_obj - start_of_year).days + 1
        
        # Check if leap year
        is_leap = (date_obj.year % 4 == 0 and date_obj.year % 100 != 0) or (date_obj.year % 400 == 0)
        total_days = 366 if is_leap else 365
        
        devotional_dict["day_of_year"] = day_of_year
        devotional_dict["day_of_year_total"] = total_days

        # Initialize engagement metrics
        devotional_dict["views_count"] = 0
        devotional_dict["likes_count"] = 0
        devotional_dict["comments_count"] = 0
        devotional_dict["shares_count"] = 0
        devotional_dict["bookmarks_count"] = 0

        # Insert into database
        result = await db.devotionals.insert_one(devotional_dict)
        devotional_dict["_id"] = result.inserted_id

        logger.info(f"Devotional created: {result.inserted_id} by author {author_id}")

        # Convert to response model
        return devotional_dict_to_response(devotional_dict)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating devotional: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create devotional: {str(e)}",
        )


async def get_devotional_by_id(devotional_id: str, user_id: Optional[str] = None) -> Optional[DevotionalResponse]:
    """
    Get devotional by ID.

    Args:
        devotional_id (str): Devotional ID.
        user_id (Optional[str]): Current user ID for personalized engagement data.

    Returns:
        Optional[DevotionalResponse]: Devotional data if found, None otherwise.
    """
    db = get_database()

    devotional_doc = await db.devotionals.find_one({"_id": ObjectId(devotional_id)})
    if not devotional_doc:
        return None

    # Ensure author info is present
    if "author_name" not in devotional_doc or not devotional_doc.get("author_name"):
        author = await db.users.find_one({"_id": devotional_doc["author_id"]})
        if author:
            devotional_doc["author_name"] = author.get("name", "Unknown Author")
            devotional_doc["author_avatar"] = author.get("avatar_url")
        else:
            devotional_doc["author_name"] = "Unknown Author"
            devotional_doc["author_avatar"] = None

    # Add user-specific engagement data
    if user_id:
        user_oid = ObjectId(user_id)
        devotional_doc["is_liked"] = await db.likes.find_one({
            "user_id": user_oid,
            "target_id": ObjectId(devotional_id),
            "target_type": "devotional"
        }) is not None
        devotional_doc["is_bookmarked"] = await db.bookmarks.find_one({
            "user_id": user_oid,
            "devotional_id": ObjectId(devotional_id)
        }) is not None

        # Add reading progress data
        reading_history = await db.reading_history.find_one({
            "user_id": user_oid,
            "devotional_id": ObjectId(devotional_id)
        })
        if reading_history:
            devotional_doc["reading_progress"] = reading_history.get("reading_progress", 0)
            devotional_doc["is_read"] = reading_history.get("reading_progress", 0) >= 100
        else:
            devotional_doc["reading_progress"] = 0
            devotional_doc["is_read"] = False
    else:
        # For public users, set default engagement values
        devotional_doc["is_liked"] = False
        devotional_doc["is_bookmarked"] = False
        devotional_doc["reading_progress"] = 0
        devotional_doc["is_read"] = False

    return devotional_dict_to_response(devotional_doc)


async def get_devotional_by_slug(slug: str) -> Optional[DevotionalResponse]:
    """
    Get devotional by slug.

    Args:
        slug (str): Devotional slug.

    Returns:
        Optional[DevotionalResponse]: Devotional data if found, None otherwise.
    """
    db = get_database()

    devotional_doc = await db.devotionals.find_one({"slug": slug})
    if not devotional_doc:
        return None

    return devotional_dict_to_response(devotional_doc)


async def list_devotionals(filters: DevotionalFilters, user_id: Optional[str] = None) -> DevotionalListResponse:
    """
    List devotionals with filters and pagination.

    Args:
        filters (DevotionalFilters): Query filters and pagination params.
        user_id (Optional[str]): Current user ID for personalized engagement data.

    Returns:
        DevotionalListResponse: Paginated list of devotionals.
    """
    db = get_database()

    # Build query
    query = {}

    if filters.status:
        query["status"] = filters.status

    if filters.category:
        query["categories"] = filters.category

    if filters.author_id:
        query["author_id"] = ObjectId(filters.author_id)

    if filters.search:
        query["$text"] = {"$search": filters.search}

    # Date filtering on published_at field
    # Reason: Filter by date range to show recent devotionals (e.g., last 30 days)
    if filters.days or filters.start_date or filters.end_date:
        date_filter = {}

        # If days is specified, calculate start_date from today
        if filters.days:
            start_datetime = datetime.utcnow() - timedelta(days=filters.days)
            date_filter["$gte"] = start_datetime

        # If explicit start_date provided, override days-based start_date
        if filters.start_date:
            try:
                start_datetime = datetime.fromisoformat(filters.start_date)
                date_filter["$gte"] = start_datetime
            except ValueError:
                logger.warning(f"Invalid start_date format: {filters.start_date}")

        # If end_date provided, add upper bound
        if filters.end_date:
            try:
                end_datetime = datetime.fromisoformat(filters.end_date)
                # Set to end of day (23:59:59)
                end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
                date_filter["$lte"] = end_datetime
            except ValueError:
                logger.warning(f"Invalid end_date format: {filters.end_date}")

        # Apply date filter to published_at field
        if date_filter:
            query["published_at"] = date_filter

    # Count total matching documents
    total = await db.devotionals.count_documents(query)

    # Build sort
    sort_order = 1 if filters.sort_order == "asc" else -1
    sort_field = filters.sort_by

    # Calculate pagination
    skip = (filters.page - 1) * filters.page_size
    limit = filters.page_size

    # Query devotionals
    cursor = db.devotionals.find(query).sort(sort_field, sort_order).skip(skip).limit(limit)
    devotional_docs = await cursor.to_list(length=limit)

    # Ensure author info is present for all devotionals
    author_ids = set(str(doc["author_id"]) for doc in devotional_docs if "author_name" not in doc or not doc.get("author_name"))
    if author_ids:
        authors = {}
        authors_cursor = db.users.find({"_id": {"$in": [ObjectId(aid) for aid in author_ids]}})
        async for author in authors_cursor:
            authors[str(author["_id"])] = author
        
        for doc in devotional_docs:
            if "author_name" not in doc or not doc.get("author_name"):
                author = authors.get(str(doc["author_id"]))
                if author:
                    doc["author_name"] = author.get("name", "Unknown Author")
                    doc["author_avatar"] = author.get("avatar_url")
                else:
                    doc["author_name"] = "Unknown Author"
                    doc["author_avatar"] = None

    # Add user-specific engagement data (batch query for performance)
    if user_id and devotional_docs:
        user_oid = ObjectId(user_id)
        devotional_ids = [doc["_id"] for doc in devotional_docs]

        # Batch check likes
        liked_ids = set()
        likes_cursor = db.likes.find({
            "user_id": user_oid,
            "target_id": {"$in": devotional_ids},
            "target_type": "devotional"
        })
        async for like in likes_cursor:
            liked_ids.add(str(like["target_id"]))

        # Batch check bookmarks
        bookmarked_ids = set()
        bookmarks_cursor = db.bookmarks.find({
            "user_id": user_oid,
            "devotional_id": {"$in": devotional_ids}
        })
        async for bookmark in bookmarks_cursor:
            bookmarked_ids.add(str(bookmark["devotional_id"]))

        # Batch check reading progress
        reading_progress_map = {}
        reading_cursor = db.reading_history.find({
            "user_id": user_oid,
            "devotional_id": {"$in": devotional_ids}
        })
        async for reading in reading_cursor:
            devotional_id_str = str(reading["devotional_id"])
            reading_progress_map[devotional_id_str] = reading.get("reading_progress", 0)

        # Add flags to documents
        for doc in devotional_docs:
            doc_id_str = str(doc["_id"])
            doc["is_liked"] = doc_id_str in liked_ids
            doc["is_bookmarked"] = doc_id_str in bookmarked_ids
            doc["reading_progress"] = reading_progress_map.get(doc_id_str, 0)
            doc["is_read"] = reading_progress_map.get(doc_id_str, 0) >= 100
    else:
        # For public users, set default engagement values
        for doc in devotional_docs:
            doc["is_liked"] = False
            doc["is_bookmarked"] = False
            doc["reading_progress"] = 0
            doc["is_read"] = False

    # Convert to response models
    devotionals = [devotional_dict_to_response(doc) for doc in devotional_docs]

    # Calculate total pages
    total_pages = (total + filters.page_size - 1) // filters.page_size

    return DevotionalListResponse(
        items=devotionals,  # Changed from 'devotionals' to 'items'
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=total_pages,
    )


async def update_devotional(
    devotional_id: str, update_data: DevotionalUpdate, author_id: str
) -> DevotionalResponse:
    """
    Update an existing devotional.

    Args:
        devotional_id (str): Devotional ID.
        update_data (DevotionalUpdate): Updated devotional data.
        author_id (str): Author user ID (for authorization).

    Returns:
        DevotionalResponse: Updated devotional data.

    Raises:
        HTTPException: If devotional not found or user is not the author.
    """
    db = get_database()

    # Get existing devotional
    devotional_doc = await db.devotionals.find_one({"_id": ObjectId(devotional_id)})
    if not devotional_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devotional not found",
        )

    # Verify author
    if str(devotional_doc["author_id"]) != author_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this devotional",
        )

    # Build update dict
    update_dict = update_data.model_dump(exclude_unset=True)

    # Handle series updates
    if "series_id" in update_dict or "series_name" in update_dict:
        series_id = None
        series_name = None
        if update_dict.get("series_id"):
            # Use existing series
            if not ObjectId.is_valid(update_dict["series_id"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid series ID",
                )
            series_id = ObjectId(update_dict["series_id"])
            series = await db.series.find_one({"_id": series_id})
            if not series:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Series not found",
                )
            series_name = series.get("name")
        elif update_dict.get("series_name"):
            # Create new series
            series_slug = generate_slug(update_dict["series_name"])
            existing_series = await db.series.find_one({"slug": series_slug, "author_id": ObjectId(author_id)})
            if existing_series:
                series_id = existing_series["_id"]
                series_name = existing_series.get("name")
            else:
                new_series = {
                    "name": update_dict["series_name"],
                    "slug": series_slug,
                    "author_id": ObjectId(author_id),
                    "description": None,
                    "cover_image_url": None,
                    "total_parts": 0,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
                result = await db.series.insert_one(new_series)
                series_id = result.inserted_id
                series_name = update_dict["series_name"]
        
        if series_id:
            update_dict["series_id"] = series_id
            update_dict["series_name"] = series_name
            if "part_number" not in update_dict or not update_dict.get("part_number"):
                # If part_number not provided, use existing or default to 1
                existing_part = devotional_doc.get("part_number")
                update_dict["part_number"] = existing_part if existing_part else 1
            # Update series total_parts
            max_part = await _get_series_max_part(db, series_id)
            await db.series.update_one(
                {"_id": series_id},
                {"$set": {"total_parts": max(update_dict["part_number"], max_part)}}
            )
        else:
            # Remove series fields
            update_dict.pop("series_id", None)
            update_dict.pop("series_name", None)
            update_dict.pop("part_number", None)

    # Update slug if title changed
    if "title" in update_dict:
        update_dict["slug"] = generate_slug(update_dict["title"])

    # Update excerpt and reading time if content changed
    if "content" in update_dict:
        # Content blocks should already be dicts from model_dump
        # But ensure they're in the right format
        if isinstance(update_dict["content"], list) and len(update_dict["content"]) > 0:
            # If first item is a dict, they're already serialized
            if not isinstance(update_dict["content"][0], dict):
                # Convert ContentBlock objects to dicts
                from app.models.devotional import ContentBlock
                update_dict["content"] = [block.model_dump(mode="json") if isinstance(block, ContentBlock) else block for block in update_dict["content"]]
        update_dict["excerpt"] = generate_excerpt(update_dict["content"])
        update_dict["reading_time_minutes"] = estimate_reading_time(update_dict["content"])

    # Update published_at if status changed to published
    if "status" in update_dict and update_dict["status"] == "published":
        if devotional_doc.get("status") != "published":
            update_dict["published_at"] = datetime.utcnow()

    # Recalculate day of year if scheduled_at or published_at changed
    if "scheduled_at" in update_dict or "published_at" in update_dict or "status" in update_dict:
        from datetime import date as date_type
        date_for_day = update_dict.get("scheduled_at") or update_dict.get("published_at") or devotional_doc.get("scheduled_at") or devotional_doc.get("published_at") or datetime.utcnow()
        
        # Convert to date object
        if isinstance(date_for_day, datetime):
            date_obj = date_for_day.date()
        elif isinstance(date_for_day, date_type):
            date_obj = date_for_day
        else:
            date_obj = datetime.utcnow().date()
        
        # Calculate day of year
        start_of_year = date_type(date_obj.year, 1, 1)
        day_of_year = (date_obj - start_of_year).days + 1
        
        # Check if leap year
        is_leap = (date_obj.year % 4 == 0 and date_obj.year % 100 != 0) or (date_obj.year % 400 == 0)
        total_days = 366 if is_leap else 365
        
        update_dict["day_of_year"] = day_of_year
        update_dict["day_of_year_total"] = total_days

    update_dict["updated_at"] = datetime.utcnow()

    # Update devotional
    await db.devotionals.update_one({"_id": ObjectId(devotional_id)}, {"$set": update_dict})

    # Get updated devotional
    updated_doc = await db.devotionals.find_one({"_id": ObjectId(devotional_id)})

    # Ensure author info is present
    if "author_name" not in updated_doc or not updated_doc.get("author_name"):
        author = await db.users.find_one({"_id": updated_doc["author_id"]})
        if author:
            updated_doc["author_name"] = author.get("name", "Unknown Author")
            updated_doc["author_avatar"] = author.get("avatar_url")
        else:
            updated_doc["author_name"] = "Unknown Author"
            updated_doc["author_avatar"] = None

    logger.info(f"Devotional updated: {devotional_id} by author {author_id}")

    return devotional_dict_to_response(updated_doc)


async def delete_devotional(devotional_id: str, author_id: str) -> bool:
    """
    Delete a devotional.

    Args:
        devotional_id (str): Devotional ID.
        author_id (str): Author user ID (for authorization).

    Returns:
        bool: True if deleted successfully.

    Raises:
        HTTPException: If devotional not found or user is not the author.
    """
    db = get_database()

    # Get existing devotional
    devotional_doc = await db.devotionals.find_one({"_id": ObjectId(devotional_id)})
    if not devotional_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devotional not found",
        )

    # Verify author
    if str(devotional_doc["author_id"]) != author_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this devotional",
        )

    # Delete devotional
    await db.devotionals.delete_one({"_id": ObjectId(devotional_id)})

    # Also delete associated comments, likes, bookmarks
    await db.comments.delete_many({"devotional_id": ObjectId(devotional_id)})
    await db.likes.delete_many({"target_type": "devotional", "target_id": ObjectId(devotional_id)})
    await db.bookmarks.delete_many({"devotional_id": ObjectId(devotional_id)})
    await db.reading_history.delete_many({"devotional_id": ObjectId(devotional_id)})

    logger.info(f"Devotional deleted: {devotional_id} by author {author_id}")

    return True


async def bulk_delete_devotionals(devotional_ids: list[str], author_id: str, is_admin: bool = False) -> dict:
    """
    Delete multiple devotionals in bulk.

    Args:
        devotional_ids (list[str]): List of devotional IDs to delete.
        author_id (str): Author user ID (for authorization).
        is_admin (bool): Whether the user is an admin (can delete any devotional).

    Returns:
        dict: Summary of deletion results.
            {
                "deleted_count": int,
                "failed_ids": list[str],
                "errors": list[str]
            }

    Raises:
        HTTPException: If no valid IDs provided.
    """
    if not devotional_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No devotional IDs provided",
        )

    db = get_database()
    deleted_count = 0
    failed_ids = []
    errors = []

    for devotional_id in devotional_ids:
        try:
            # Validate ObjectId
            if not ObjectId.is_valid(devotional_id):
                failed_ids.append(devotional_id)
                errors.append(f"Invalid ID format: {devotional_id}")
                continue

            # Get existing devotional
            devotional_doc = await db.devotionals.find_one({"_id": ObjectId(devotional_id)})
            if not devotional_doc:
                failed_ids.append(devotional_id)
                errors.append(f"Devotional not found: {devotional_id}")
                continue

            # Verify author (skip check if admin)
            if not is_admin and str(devotional_doc["author_id"]) != author_id:
                failed_ids.append(devotional_id)
                errors.append(f"Not authorized to delete: {devotional_id}")
                continue

            # Delete devotional
            await db.devotionals.delete_one({"_id": ObjectId(devotional_id)})

            # Also delete associated comments, likes, bookmarks, reading history
            await db.comments.delete_many({"devotional_id": ObjectId(devotional_id)})
            await db.likes.delete_many({"target_type": "devotional", "target_id": ObjectId(devotional_id)})
            await db.bookmarks.delete_many({"devotional_id": ObjectId(devotional_id)})
            await db.reading_history.delete_many({"devotional_id": ObjectId(devotional_id)})

            deleted_count += 1
            logger.info(f"Devotional deleted in bulk: {devotional_id} by {author_id}")

        except Exception as e:
            failed_ids.append(devotional_id)
            errors.append(f"Error deleting {devotional_id}: {str(e)}")
            logger.error(f"Bulk delete error for {devotional_id}: {e}")

    logger.info(f"Bulk delete complete: {deleted_count} deleted, {len(failed_ids)} failed")

    return {
        "deleted_count": deleted_count,
        "failed_ids": failed_ids,
        "errors": errors,
    }


async def publish_devotional(devotional_id: str, author_id: str) -> DevotionalResponse:
    """
    Publish a draft devotional.

    Args:
        devotional_id (str): Devotional ID.
        author_id (str): Author user ID (for authorization).

    Returns:
        DevotionalResponse: Published devotional data.

    Raises:
        HTTPException: If devotional not found or user is not the author.
    """
    update_data = DevotionalUpdate(status="published")
    return await update_devotional(devotional_id, update_data, author_id)


async def increment_view_count(devotional_id: str) -> bool:
    """
    Increment view count for a devotional.

    Args:
        devotional_id (str): Devotional ID.

    Returns:
        bool: True if updated successfully.
    """
    db = get_database()

    result = await db.devotionals.update_one(
        {"_id": ObjectId(devotional_id)}, {"$inc": {"views_count": 1}}
    )

    return result.modified_count > 0


def devotional_dict_to_response(devotional_dict: dict) -> DevotionalResponse:
    """
    Convert devotional document dict to DevotionalResponse model.

    Args:
        devotional_dict (dict): Devotional document from MongoDB.

    Returns:
        DevotionalResponse: Devotional response model.
    """
    from app.models.devotional import ContentBlock
    
    # Convert content from dict to ContentBlock objects
    content_blocks = []
    for block_data in devotional_dict.get("content", []):
        try:
            if isinstance(block_data, dict):
                # Ensure all required fields are present
                if "type" not in block_data or "text" not in block_data:
                    logger.warning(f"Invalid content block: {block_data}")
                    continue
                # Ensure scripture_reference is None (not missing) for non-scripture blocks
                if block_data.get("type") != "scripture" and "scripture_reference" not in block_data:
                    block_data["scripture_reference"] = None
                content_blocks.append(ContentBlock(**block_data))
            elif isinstance(block_data, ContentBlock):
                content_blocks.append(block_data)
            else:
                logger.warning(f"Unexpected content block type: {type(block_data)}")
        except Exception as e:
            logger.error(f"Error parsing content block: {e}, block_data: {block_data}", exc_info=True)
            # Re-raise the error instead of skipping - we need valid content blocks
            raise ValueError(f"Invalid content block: {str(e)}")
    
    # Ensure we have at least one content block
    if not content_blocks:
        logger.error(f"No valid content blocks found in devotional {devotional_dict.get('_id')}")
        raise ValueError("Devotional must have at least one valid content block")
    
    # Ensure slug exists (generate if missing)
    slug = devotional_dict.get("slug")
    if not slug:
        slug = generate_slug(devotional_dict.get("title", "untitled"))
        logger.warning(f"Missing slug for devotional {devotional_dict.get('_id')}, generated: {slug}")
    
    return DevotionalResponse(
        id=str(devotional_dict["_id"]),
        author_id=str(devotional_dict["author_id"]),
        author_name=devotional_dict.get("author_name", "FreshManna Team"),
        author_avatar=devotional_dict.get("author_avatar"),
        title=devotional_dict.get("title", "Untitled"),
        slug=slug,
        content=content_blocks,
        excerpt=devotional_dict.get("excerpt", ""),
        scripture_references=devotional_dict.get("scripture_references", []),
        categories=devotional_dict.get("categories", []),
        cover_image_url=devotional_dict.get("cover_image_url"),
        audio_url=devotional_dict.get("audio_url"),
        video_url=devotional_dict.get("video_url"),
        summary=devotional_dict.get("summary"),
        status=devotional_dict.get("status", "draft"),
        scheduled_at=devotional_dict.get("scheduled_at"),
        published_at=devotional_dict.get("published_at"),
        views_count=devotional_dict.get("views_count", 0),
        likes_count=devotional_dict.get("likes_count", 0),
        comments_count=devotional_dict.get("comments_count", 0),
        shares_count=devotional_dict.get("shares_count", 0),
        bookmarks_count=devotional_dict.get("bookmarks_count", 0),
        is_liked=devotional_dict.get("is_liked"),
        is_bookmarked=devotional_dict.get("is_bookmarked"),
        reading_time_minutes=devotional_dict.get("reading_time_minutes", 0),
        series_id=str(devotional_dict["series_id"]) if devotional_dict.get("series_id") else None,
        series_name=devotional_dict.get("series_name"),
        part_number=devotional_dict.get("part_number"),
        created_at=devotional_dict.get("created_at", datetime.utcnow()),
        updated_at=devotional_dict.get("updated_at", datetime.utcnow()),
    )
