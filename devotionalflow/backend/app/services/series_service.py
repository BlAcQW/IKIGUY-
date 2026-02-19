"""
Series service for managing devotional series.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from bson import ObjectId
from pymongo import UpdateOne

from app.db.mongodb import get_database
from app.models.series import (
    SeriesCreate,
    SeriesUpdate,
    SeriesResponse,
    generate_slug
)
import logging

logger = logging.getLogger(__name__)


async def get_series_by_id(series_id: str) -> Optional[dict]:
    """
    Get series by ID.

    Args:
        series_id (str): Series ID.

    Returns:
        Optional[dict]: Series data if found, None otherwise.
    """
    db = get_database()

    if not ObjectId.is_valid(series_id):
        return None

    series_doc = await db.series.find_one({"_id": ObjectId(series_id)})
    if not series_doc:
        return None

    # Get devotionals in this series
    devotionals = await db.devotionals.find(
        {"series_id": ObjectId(series_id)},
        {"_id": 1, "title": 1, "part_number": 1, "status": 1, "published_at": 1}
    ).sort("part_number", 1).to_list(length=100)

    series_doc["devotionals"] = [
        {
            "id": str(d["_id"]),
            "title": d.get("title"),
            "part_number": d.get("part_number"),
            "status": d.get("status"),
            "published_at": d.get("published_at"),
        }
        for d in devotionals
    ]

    series_doc["id"] = str(series_doc["_id"])
    return series_doc


async def list_series(author_id: Optional[str] = None, limit: int = 50) -> List[dict]:
    """
    List all series.

    Args:
        author_id (Optional[str]): Filter by author ID.
        limit (int): Maximum number of series to return.

    Returns:
        List[dict]: List of series.
    """
    db = get_database()

    query = {}
    if author_id:
        if not ObjectId.is_valid(author_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid author ID",
            )
        query["author_id"] = ObjectId(author_id)

    cursor = db.series.find(query).sort("created_at", -1).limit(limit)
    series_list = await cursor.to_list(length=limit)

    # Get devotionals count for each series
    result = []
    for series in series_list:
        series_id = series["_id"]
        count = await db.devotionals.count_documents({"series_id": series_id})

        # Convert to JSON-serializable format
        start_date = series.get("start_date")
        if start_date:
            if isinstance(start_date, datetime):
                start_date = start_date.isoformat()
            elif hasattr(start_date, 'isoformat'):
                start_date = start_date.isoformat()
        
        result.append({
            "id": str(series["_id"]),
            "name": series.get("name"),
            "slug": series.get("slug"),
            "description": series.get("description"),
            "cover_image_url": series.get("cover_image_url"),
            "author_id": str(series.get("author_id")) if series.get("author_id") else None,
            "total_parts": series.get("total_parts", 0),
            "devotionals_count": count,
            "start_date": start_date,
            "created_at": series.get("created_at"),
            "updated_at": series.get("updated_at"),
        })

    return result


async def get_series_devotionals(series_id: str) -> List[dict]:
    """
    Get all devotionals in a series.

    Args:
        series_id (str): Series ID.

    Returns:
        List[dict]: List of devotionals in the series.
    """
    db = get_database()

    if not ObjectId.is_valid(series_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid series ID",
        )

    cursor = db.devotionals.find(
        {"series_id": ObjectId(series_id)},
        {
            "_id": 1,
            "title": 1,
            "slug": 1,
            "part_number": 1,
            "status": 1,
            "published_at": 1,
            "excerpt": 1,
            "cover_image_url": 1,
        }
    ).sort("part_number", 1)

    devotionals = await cursor.to_list(length=100)

    return [
        {
            "id": str(d["_id"]),
            "title": d.get("title"),
            "slug": d.get("slug"),
            "part_number": d.get("part_number"),
            "status": d.get("status"),
            "published_at": d.get("published_at"),
            "excerpt": d.get("excerpt"),
            "cover_image_url": d.get("cover_image_url"),
        }
        for d in devotionals
    ]


async def verify_series_authorization(
    series_id: str,
    user_id: str,
    is_admin: bool = False
) -> dict:
    """
    Verify user authorization to modify a series.

    Args:
        series_id (str): Series ID.
        user_id (str): User ID.
        is_admin (bool): Whether user is admin.

    Returns:
        dict: Series document if authorized.

    Raises:
        HTTPException: If not authorized or series not found.
    """
    db = get_database()

    if not ObjectId.is_valid(series_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid series ID"
        )

    series = await db.series.find_one({"_id": ObjectId(series_id)})
    if not series:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Series not found"
        )

    # Admin bypass
    if is_admin:
        return series

    # Check authorship
    if str(series["author_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this series"
        )

    return series


async def create_series(series_data: SeriesCreate, author_id: str) -> SeriesResponse:
    """
    Create a new series.

    Args:
        series_data (SeriesCreate): Series creation data.
        author_id (str): Author user ID.

    Returns:
        SeriesResponse: Created series data.

    Raises:
        HTTPException: If author not found or validation fails.
    """
    db = get_database()

    # Validate author
    if not ObjectId.is_valid(author_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid author ID"
        )

    author = await db.users.find_one({"_id": ObjectId(author_id)})
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found"
        )

    # Generate slug
    slug = generate_slug(series_data.name)

    # Check for slug conflicts (same author)
    existing = await db.series.find_one({"slug": slug, "author_id": ObjectId(author_id)})
    if existing:
        # Add timestamp to make unique
        slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

    # Create series document
    series_dict = {
        "name": series_data.name,
        "slug": slug,
        "description": series_data.description,
        "cover_image_url": series_data.cover_image_url,
        "author_id": ObjectId(author_id),
        "start_date": series_data.start_date,
        "total_parts": 0,  # Will be updated when devotionals added
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    result = await db.series.insert_one(series_dict)
    series_dict["_id"] = result.inserted_id

    logger.info(f"Series created: {result.inserted_id} by author {author_id}")

    # Convert to response model
    return SeriesResponse(
        id=str(series_dict["_id"]),
        name=series_dict["name"],
        slug=series_dict["slug"],
        description=series_dict["description"],
        cover_image_url=series_dict["cover_image_url"],
        author_id=str(series_dict["author_id"]),
        author_name=author.get("name", "Unknown Author"),
        start_date=series_dict["start_date"],
        total_parts=series_dict["total_parts"],
        devotionals_count=0,
        created_at=series_dict["created_at"],
        updated_at=series_dict["updated_at"]
    )


async def update_series(
    series_id: str,
    update_data: SeriesUpdate,
    user_id: str,
    is_admin: bool = False
) -> SeriesResponse:
    """
    Update series metadata.

    Args:
        series_id (str): Series ID.
        update_data (SeriesUpdate): Updated data.
        user_id (str): Current user ID.
        is_admin (bool): Whether user is admin.

    Returns:
        SeriesResponse: Updated series data.

    Raises:
        HTTPException: If not authorized or series not found.
    """
    db = get_database()

    # Authorization check
    series = await verify_series_authorization(series_id, user_id, is_admin)

    # Build update dict
    update_dict = update_data.model_dump(exclude_unset=True)

    # Check if start_date changed
    start_date_changed = False
    if "start_date" in update_dict and update_dict["start_date"] != series.get("start_date"):
        start_date_changed = True

    # Update slug if name changed
    if "name" in update_dict:
        new_slug = generate_slug(update_dict["name"])
        # Check conflicts (excluding current series)
        existing = await db.series.find_one({
            "slug": new_slug,
            "author_id": series["author_id"],
            "_id": {"$ne": ObjectId(series_id)}
        })
        if existing:
            new_slug = f"{new_slug}-{int(datetime.utcnow().timestamp())}"
        update_dict["slug"] = new_slug

    update_dict["updated_at"] = datetime.utcnow()

    # Update series
    await db.series.update_one(
        {"_id": ObjectId(series_id)},
        {"$set": update_dict}
    )

    # Reschedule if start_date changed
    rescheduled_count = 0
    if start_date_changed:
        rescheduled_count = await reschedule_series_devotionals(series_id)
        logger.info(f"Rescheduled {rescheduled_count} devotionals due to start_date change")

    # Get updated series
    updated_series = await db.series.find_one({"_id": ObjectId(series_id)})

    # Get author info
    author = await db.users.find_one({"_id": updated_series["author_id"]})

    # Get devotionals count
    devotionals_count = await db.devotionals.count_documents({"series_id": ObjectId(series_id)})

    return SeriesResponse(
        id=str(updated_series["_id"]),
        name=updated_series["name"],
        slug=updated_series["slug"],
        description=updated_series.get("description"),
        cover_image_url=updated_series.get("cover_image_url"),
        author_id=str(updated_series["author_id"]),
        author_name=author.get("name", "Unknown Author") if author else "Unknown Author",
        start_date=updated_series.get("start_date"),
        total_parts=updated_series["total_parts"],
        devotionals_count=devotionals_count,
        created_at=updated_series["created_at"],
        updated_at=updated_series["updated_at"]
    )


async def delete_series(
    series_id: str,
    orphan_devotionals: bool,
    user_id: str,
    is_admin: bool = False
) -> Dict[str, Any]:
    """
    Delete a series.

    Args:
        series_id (str): Series ID.
        orphan_devotionals (bool): If True, unlink devotionals; if False, fail if devotionals exist.
        user_id (str): Current user ID.
        is_admin (bool): Whether user is admin.

    Returns:
        Dict[str, Any]: Deletion summary.

    Raises:
        HTTPException: If not authorized, series not found, or devotionals exist (when orphan_devotionals=False).
    """
    db = get_database()

    # Authorization check
    series = await verify_series_authorization(series_id, user_id, is_admin)

    # Count devotionals in series
    devotionals_count = await db.devotionals.count_documents({"series_id": ObjectId(series_id)})

    if devotionals_count > 0 and not orphan_devotionals:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete series with {devotionals_count} devotionals. Set orphan_devotionals=true to unlink them."
        )

    # Orphan devotionals if needed
    if orphan_devotionals and devotionals_count > 0:
        await db.devotionals.update_many(
            {"series_id": ObjectId(series_id)},
            {
                "$unset": {
                    "series_id": "",
                    "series_name": "",
                    "part_number": ""
                },
                "$set": {
                    "updated_at": datetime.utcnow()
                }
            }
        )
        logger.info(f"Orphaned {devotionals_count} devotionals from series {series_id}")

    # Delete series document
    await db.series.delete_one({"_id": ObjectId(series_id)})

    logger.info(f"Series deleted: {series_id} by user {user_id}")

    return {
        "message": "Series deleted successfully",
        "orphaned_devotionals": devotionals_count if orphan_devotionals else 0
    }


async def reschedule_series_devotionals(series_id: str) -> int:
    """
    Internal helper: reschedule all devotionals when start_date changes.

    Args:
        series_id (str): Series ID.

    Returns:
        int: Count of rescheduled devotionals.
    """
    db = get_database()

    # Get series start_date
    series = await db.series.find_one({"_id": ObjectId(series_id)})
    if not series or not series.get("start_date"):
        return 0

    start_date = series["start_date"]

    # Get all devotionals in series
    devotionals = await db.devotionals.find(
        {"series_id": ObjectId(series_id)}
    ).to_list(length=None)

    rescheduled_count = 0

    for devotional in devotionals:
        # Skip published devotionals
        if devotional.get("status") == "published":
            continue

        part_number = devotional.get("part_number", 1)
        scheduled_at = start_date + timedelta(days=(part_number - 1))

        # Update devotional
        await db.devotionals.update_one(
            {"_id": devotional["_id"]},
            {
                "$set": {
                    "status": "scheduled",
                    "scheduled_at": scheduled_at,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        rescheduled_count += 1

    return rescheduled_count


async def schedule_series_devotionals(
    series_id: str,
    user_id: str,
    is_admin: bool = False
) -> Dict[str, Any]:
    """
    Schedule all devotionals in series based on start_date + part_number.

    Algorithm: scheduled_at = series.start_date + timedelta(days=(part_number - 1))

    Args:
        series_id (str): Series ID.
        user_id (str): Current user ID.
        is_admin (bool): Whether user is admin.

    Returns:
        Dict[str, Any]: Scheduling summary.

    Raises:
        HTTPException: If not authorized or series not found.
    """
    db = get_database()

    # Authorization check
    series = await verify_series_authorization(series_id, user_id, is_admin)

    # Get start_date
    start_date = series.get("start_date")
    if not start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Series must have a start_date to schedule devotionals"
        )

    # Fetch all devotionals in series
    devotionals = await db.devotionals.find(
        {"series_id": ObjectId(series_id)}
    ).to_list(length=None)

    scheduled_count = 0
    skipped_count = 0
    results = []

    for devotional in devotionals:
        part_number = devotional.get("part_number", 1)
        current_status = devotional.get("status")

        # Skip already published devotionals
        if current_status == "published":
            skipped_count += 1
            results.append({
                "id": str(devotional["_id"]),
                "title": devotional["title"],
                "part_number": part_number,
                "status": "skipped",
                "reason": "Already published"
            })
            continue

        # Calculate scheduled_at
        scheduled_at = start_date + timedelta(days=(part_number - 1))

        # Update devotional
        await db.devotionals.update_one(
            {"_id": devotional["_id"]},
            {
                "$set": {
                    "status": "scheduled",
                    "scheduled_at": scheduled_at,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        scheduled_count += 1
        results.append({
            "id": str(devotional["_id"]),
            "title": devotional["title"],
            "part_number": part_number,
            "scheduled_at": scheduled_at,
            "status": "scheduled"
        })

    return {
        "series_id": str(series_id),
        "series_name": series["name"],
        "start_date": start_date,
        "scheduled_count": scheduled_count,
        "skipped_count": skipped_count,
        "total_devotionals": len(devotionals),
        "devotionals": results
    }


async def reorder_devotionals(
    series_id: str,
    devotional_order: List[str],
    user_id: str,
    is_admin: bool = False
) -> Dict[str, Any]:
    """
    Reorder devotionals in a series using bulk write for atomicity.

    Args:
        series_id (str): Series ID.
        devotional_order (List[str]): List of devotional IDs in new order.
        user_id (str): Current user ID.
        is_admin (bool): Whether user is admin.

    Returns:
        Dict[str, Any]: Reorder summary.

    Raises:
        HTTPException: If not authorized, series not found, or invalid devotional IDs.
    """
    db = get_database()

    # Authorization check
    series = await verify_series_authorization(series_id, user_id, is_admin)

    # Validate all devotionals belong to series
    devotional_ids = [ObjectId(d_id) for d_id in devotional_order if ObjectId.is_valid(d_id)]
    if len(devotional_ids) != len(devotional_order):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid devotional IDs in reorder request"
        )

    actual_devotionals = await db.devotionals.find({
        "_id": {"$in": devotional_ids},
        "series_id": ObjectId(series_id)
    }).to_list(length=len(devotional_ids))

    if len(actual_devotionals) != len(devotional_order):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not all devotional IDs belong to this series"
        )

    # Build bulk write operations
    bulk_ops = []
    for idx, devotional_id in enumerate(devotional_order, start=1):
        bulk_ops.append(
            UpdateOne(
                {"_id": ObjectId(devotional_id)},
                {"$set": {"part_number": idx, "updated_at": datetime.utcnow()}}
            )
        )

    # Execute bulk write (ATOMIC)
    if bulk_ops:
        result = await db.devotionals.bulk_write(bulk_ops)

        # Update series total_parts
        await db.series.update_one(
            {"_id": ObjectId(series_id)},
            {
                "$set": {
                    "total_parts": len(devotional_order),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        logger.info(f"Reordered {result.modified_count} devotionals in series {series_id}")

        return {
            "updated_count": result.modified_count,
            "devotionals": [
                {"id": str(dev["_id"]), "title": dev["title"], "part_number": idx + 1}
                for idx, dev in enumerate(actual_devotionals)
            ]
        }

    return {"updated_count": 0, "devotionals": []}


async def remove_devotional_from_series(
    series_id: str,
    devotional_id: str,
    auto_renumber: bool,
    user_id: str,
    is_admin: bool = False
) -> Dict[str, Any]:
    """
    Remove devotional from series with optional auto-renumbering.

    Args:
        series_id (str): Series ID.
        devotional_id (str): Devotional ID to remove.
        auto_renumber (bool): If True, auto-renumber remaining devotionals.
        user_id (str): Current user ID.
        is_admin (bool): Whether user is admin.

    Returns:
        Dict[str, Any]: Removal summary.

    Raises:
        HTTPException: If not authorized, series/devotional not found, or invalid IDs.
    """
    db = get_database()

    # Authorization
    series = await verify_series_authorization(series_id, user_id, is_admin)

    # Validate devotional
    if not ObjectId.is_valid(devotional_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid devotional ID"
        )

    devotional = await db.devotionals.find_one({"_id": ObjectId(devotional_id)})
    if not devotional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devotional not found"
        )

    # Verify devotional belongs to this series
    if devotional.get("series_id") != ObjectId(series_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Devotional does not belong to this series"
        )

    removed_part_number = devotional.get("part_number", 1)

    # Remove series fields from devotional
    await db.devotionals.update_one(
        {"_id": ObjectId(devotional_id)},
        {
            "$unset": {
                "series_id": "",
                "series_name": "",
                "part_number": ""
            },
            "$set": {
                "updated_at": datetime.utcnow()
            }
        }
    )

    renumbered_count = 0

    # Auto-renumber remaining devotionals
    if auto_renumber:
        # Find all devotionals with part_number > removed part
        result = await db.devotionals.update_many(
            {
                "series_id": ObjectId(series_id),
                "part_number": {"$gt": removed_part_number}
            },
            {
                "$inc": {"part_number": -1},  # Decrement by 1
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        renumbered_count = result.modified_count

        # Recalculate total_parts (current max part_number)
        max_part_result = await db.devotionals.find_one(
            {"series_id": ObjectId(series_id)},
            sort=[("part_number", -1)]
        )

        new_total_parts = max_part_result["part_number"] if max_part_result else 0

        await db.series.update_one(
            {"_id": ObjectId(series_id)},
            {
                "$set": {
                    "total_parts": new_total_parts,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    else:
        # Just decrement total_parts by 1 (no renumbering)
        await db.series.update_one(
            {"_id": ObjectId(series_id)},
            {
                "$inc": {"total_parts": -1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

    logger.info(f"Removed devotional {devotional_id} from series {series_id}, auto_renumber={auto_renumber}, renumbered={renumbered_count}")

    return {
        "message": "Devotional removed from series",
        "renumbered_count": renumbered_count,
        "new_total_parts": series["total_parts"] - 1 if not auto_renumber else (series["total_parts"] - 1) if renumbered_count == 0 else series["total_parts"] - 1
    }




