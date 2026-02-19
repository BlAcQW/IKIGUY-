"""
Content moderation service for flagging and reviewing content.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bson import ObjectId
from app.db.mongodb import get_database
from app.models.moderation import (
    FlagContent,
    ContentFlag,
    ModerationAction,
    ModerationRecord,
    ModerationQueueFilters,
    ModerationQueueResponse,
    ModerationStats,
)


class ModerationService:
    """Service for content moderation operations."""

    def __init__(self):
        self.db = get_database()
        self.flags_collection = self.db.content_flags
        self.moderation_records_collection = self.db.moderation_records
        self.devotionals_collection = self.db.devotionals
        self.comments_collection = self.db.comments
        self.users_collection = self.db.users

    async def flag_content(
        self, flag_data: FlagContent, user_id: str
    ) -> Dict[str, Any]:
        """
        Flag content for moderation.

        Args:
            flag_data: Content flag data
            user_id: ID of user flagging the content

        Returns:
            Dict with flag ID and success status

        Raises:
            ValueError: If content not found or already flagged by user
        """
        # Check if content exists
        if flag_data.content_type == "devotional":
            content = await self.devotionals_collection.find_one(
                {"_id": ObjectId(flag_data.content_id)}
            )
        else:  # comment
            content = await self.comments_collection.find_one(
                {"_id": ObjectId(flag_data.content_id)}
            )

        if not content:
            raise ValueError(f"{flag_data.content_type.capitalize()} not found")

        # Check if user already flagged this content
        existing_flag = await self.flags_collection.find_one(
            {
                "content_id": flag_data.content_id,
                "content_type": flag_data.content_type,
                "flagged_by_user_id": user_id,
            }
        )

        if existing_flag:
            raise ValueError("You have already flagged this content")

        # Get user info
        user = await self.users_collection.find_one({"_id": ObjectId(user_id)})

        # Get content preview
        if flag_data.content_type == "devotional":
            content_preview = content.get("content", "")[:200]
        else:
            content_preview = content.get("text", "")[:200]

        # Create flag record
        flag_doc = {
            "content_id": flag_data.content_id,
            "content_type": flag_data.content_type,
            "flagged_by_user_id": user_id,
            "flagged_by_user_name": user.get("name", "Unknown"),
            "flagged_by_user_email": user.get("email", ""),
            "reason": flag_data.reason.dict(),
            "status": "pending",
            "content_preview": content_preview,
            "created_at": datetime.utcnow(),
        }

        result = await self.flags_collection.insert_one(flag_doc)

        return {
            "success": True,
            "flag_id": str(result.inserted_id),
            "message": "Content flagged for review",
        }

    async def get_moderation_queue(
        self, filters: ModerationQueueFilters
    ) -> ModerationQueueResponse:
        """
        Get moderation queue with filters and pagination.

        Args:
            filters: Filter parameters

        Returns:
            ModerationQueueResponse: Paginated list of flagged content
        """
        # Build query
        query = {}

        if filters.status:
            query["status"] = filters.status

        if filters.content_type:
            query["content_type"] = filters.content_type

        if filters.reason_category:
            query["reason.category"] = filters.reason_category

        # Count total matching documents
        total = await self.flags_collection.count_documents(query)

        # Calculate pagination
        skip = (filters.page - 1) * filters.page_size
        total_pages = (total + filters.page_size - 1) // filters.page_size

        # Sort configuration
        sort_direction = 1 if filters.sort_order == "asc" else -1

        # Get flags with pagination
        flags_cursor = (
            self.flags_collection.find(query)
            .sort(filters.sort_by, sort_direction)
            .skip(skip)
            .limit(filters.page_size)
        )

        flags = await flags_cursor.to_list(length=filters.page_size)

        # Convert to ContentFlag models with enriched data
        content_flags = []
        for flag in flags:
            # Get content title
            content_title = ""
            if flag["content_type"] == "devotional":
                content = await self.devotionals_collection.find_one(
                    {"_id": ObjectId(flag["content_id"])}
                )
                if content:
                    content_title = content.get("title", "Untitled")
            else:  # comment
                content = await self.comments_collection.find_one(
                    {"_id": ObjectId(flag["content_id"])}
                )
                if content:
                    # For comments, show preview text as title
                    content_title = content.get("text", "")[:50] + "..."

            # Build enriched flag data for frontend compatibility
            flag_data = {
                "flag_id": str(flag["_id"]),  # Frontend expects flag_id
                "devotional_id": flag["content_id"],  # Frontend expects devotional_id
                "content_id": flag["content_id"],  # Keep for backend compatibility
                "content_type": flag["content_type"],
                "devotional_title": content_title,  # Add title for frontend
                "content_title": content_title,  # Alternative field name
                "reason": flag["reason"]["category"],  # Frontend expects string
                "details": flag["reason"].get("details"),  # Separate details field
                "reason_obj": flag["reason"],  # Keep full reason object
                "severity": "medium",  # Default severity (not tracked in current backend)
                "status": flag["status"],
                "flagged_by": flag["flagged_by_user_name"],  # Frontend expects flagged_by
                "flagged_by_user_id": flag["flagged_by_user_id"],
                "flagged_by_user_name": flag["flagged_by_user_name"],
                "flagged_by_user_email": flag["flagged_by_user_email"],
                "flagged_at": flag["created_at"].isoformat(),  # Frontend expects flagged_at
                "created_at": flag["created_at"],  # Keep for backend compatibility
                "content_preview": flag["content_preview"],
            }

            content_flags.append(flag_data)

        return {
            "flags": content_flags,
            "total": total,
            "page": filters.page,
            "page_size": filters.page_size,
            "total_pages": total_pages,
        }

    async def moderate_content(
        self, flag_id: str, action: ModerationAction, moderator_user_id: str
    ) -> Dict[str, Any]:
        """
        Take moderation action on flagged content.

        Args:
            flag_id: ID of the flag
            action: Moderation action to take
            moderator_user_id: ID of moderator

        Returns:
            Dict with success status and message

        Raises:
            ValueError: If flag not found or invalid action
        """
        # Get flag
        flag = await self.flags_collection.find_one({"_id": ObjectId(flag_id)})
        if not flag:
            raise ValueError("Flag not found")

        # Get moderator info
        moderator = await self.users_collection.find_one(
            {"_id": ObjectId(moderator_user_id)}
        )

        # Execute action
        message = ""
        new_status = "reviewed"

        if action.action == "approve":
            # Mark content as approved (no changes needed to content)
            message = "Content approved and flag dismissed"
            new_status = "dismissed"

        elif action.action == "delete":
            # Delete the content
            if flag["content_type"] == "devotional":
                await self.devotionals_collection.delete_one(
                    {"_id": ObjectId(flag["content_id"])}
                )
            else:  # comment
                await self.comments_collection.delete_one(
                    {"_id": ObjectId(flag["content_id"])}
                )
            message = f"{flag['content_type'].capitalize()} deleted"
            new_status = "action_taken"

        elif action.action == "hide":
            # Hide content (add is_hidden flag)
            if flag["content_type"] == "devotional":
                await self.devotionals_collection.update_one(
                    {"_id": ObjectId(flag["content_id"])},
                    {"$set": {"is_hidden": True, "hidden_at": datetime.utcnow()}},
                )
            else:  # comment
                await self.comments_collection.update_one(
                    {"_id": ObjectId(flag["content_id"])},
                    {"$set": {"is_hidden": True, "hidden_at": datetime.utcnow()}},
                )
            message = f"{flag['content_type'].capitalize()} hidden"
            new_status = "action_taken"

        elif action.action == "warn_author":
            # Send warning to author (implementation depends on notification system)
            message = "Warning sent to author"
            new_status = "action_taken"

        elif action.action == "suspend_author":
            # Suspend the author
            if flag["content_type"] == "devotional":
                devotional = await self.devotionals_collection.find_one(
                    {"_id": ObjectId(flag["content_id"])}
                )
                author_id = devotional.get("author_id")
            else:  # comment
                comment = await self.comments_collection.find_one(
                    {"_id": ObjectId(flag["content_id"])}
                )
                author_id = comment.get("user_id")

            if author_id:
                await self.users_collection.update_one(
                    {"_id": ObjectId(author_id)},
                    {
                        "$set": {
                            "is_suspended": True,
                            "suspended_at": datetime.utcnow(),
                            "suspension_reason": action.reason or "Content moderation",
                        }
                    },
                )
            message = "Author suspended"
            new_status = "action_taken"

        elif action.action == "dismiss_flag":
            message = "Flag dismissed"
            new_status = "dismissed"

        # Update flag status
        await self.flags_collection.update_one(
            {"_id": ObjectId(flag_id)},
            {"$set": {"status": new_status, "updated_at": datetime.utcnow()}},
        )

        # Create moderation record
        moderation_record = {
            "flag_id": flag_id,
            "content_id": flag["content_id"],
            "content_type": flag["content_type"],
            "action": action.action,
            "reason": action.reason,
            "notes": action.notes,
            "moderated_by_user_id": moderator_user_id,
            "moderated_by_user_name": moderator.get("name", "Unknown"),
            "moderated_at": datetime.utcnow(),
        }

        await self.moderation_records_collection.insert_one(moderation_record)

        return {"success": True, "message": message}

    async def get_moderation_stats(self) -> ModerationStats:
        """
        Get moderation statistics.

        Returns:
            ModerationStats: Statistics about flagged content
        """
        # Total flags
        total_flags = await self.flags_collection.count_documents({})

        # By status
        pending_flags = await self.flags_collection.count_documents({"status": "pending"})
        reviewed_flags = await self.flags_collection.count_documents({"status": "reviewed"})
        dismissed_flags = await self.flags_collection.count_documents({"status": "dismissed"})
        action_taken_flags = await self.flags_collection.count_documents(
            {"status": "action_taken"}
        )

        # By content type
        devotional_flags = await self.flags_collection.count_documents(
            {"content_type": "devotional"}
        )
        comment_flags = await self.flags_collection.count_documents(
            {"content_type": "comment"}
        )

        # By reason category
        spam_flags = await self.flags_collection.count_documents(
            {"reason.category": "spam"}
        )
        inappropriate_flags = await self.flags_collection.count_documents(
            {"reason.category": "inappropriate"}
        )
        offensive_flags = await self.flags_collection.count_documents(
            {"reason.category": "offensive"}
        )
        plagiarism_flags = await self.flags_collection.count_documents(
            {"reason.category": "plagiarism"}
        )
        misleading_flags = await self.flags_collection.count_documents(
            {"reason.category": "misleading"}
        )
        other_flags = await self.flags_collection.count_documents(
            {"reason.category": "other"}
        )

        # Recent activity
        now = datetime.utcnow()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        flags_last_24h = await self.flags_collection.count_documents(
            {"created_at": {"$gte": day_ago}}
        )
        flags_last_7d = await self.flags_collection.count_documents(
            {"created_at": {"$gte": week_ago}}
        )
        flags_last_30d = await self.flags_collection.count_documents(
            {"created_at": {"$gte": month_ago}}
        )

        return ModerationStats(
            total_flags=total_flags,
            pending_flags=pending_flags,
            reviewed_flags=reviewed_flags,
            dismissed_flags=dismissed_flags,
            action_taken_flags=action_taken_flags,
            devotional_flags=devotional_flags,
            comment_flags=comment_flags,
            spam_flags=spam_flags,
            inappropriate_flags=inappropriate_flags,
            offensive_flags=offensive_flags,
            plagiarism_flags=plagiarism_flags,
            misleading_flags=misleading_flags,
            other_flags=other_flags,
            flags_last_24h=flags_last_24h,
            flags_last_7d=flags_last_7d,
            flags_last_30d=flags_last_30d,
        )

    async def get_flag_details(self, flag_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a flag including full content and moderation history.

        Args:
            flag_id: ID of the flag

        Returns:
            Dict with flag details and related content

        Raises:
            ValueError: If flag not found
        """
        # Get flag
        flag = await self.flags_collection.find_one({"_id": ObjectId(flag_id)})
        if not flag:
            raise ValueError("Flag not found")

        # Get full content
        if flag["content_type"] == "devotional":
            content = await self.devotionals_collection.find_one(
                {"_id": ObjectId(flag["content_id"])}
            )
            content_data = {
                "title": content.get("title", ""),
                "content": content.get("content", ""),
                "author_id": content.get("author_id", ""),
                "category": content.get("category", ""),
                "status": content.get("status", ""),
                "created_at": content.get("created_at"),
            }
        else:  # comment
            content = await self.comments_collection.find_one(
                {"_id": ObjectId(flag["content_id"])}
            )
            content_data = {
                "text": content.get("text", ""),
                "user_id": content.get("user_id", ""),
                "devotional_id": content.get("devotional_id", ""),
                "created_at": content.get("created_at"),
            }

        # Get moderation history
        moderation_history = await self.moderation_records_collection.find(
            {"flag_id": flag_id}
        ).to_list(length=None)

        return {
            "flag": {
                "id": str(flag["_id"]),
                "content_id": flag["content_id"],
                "content_type": flag["content_type"],
                "flagged_by_user_id": flag["flagged_by_user_id"],
                "flagged_by_user_name": flag["flagged_by_user_name"],
                "flagged_by_user_email": flag["flagged_by_user_email"],
                "reason": flag["reason"],
                "status": flag["status"],
                "created_at": flag["created_at"],
            },
            "content": content_data,
            "moderation_history": [
                {
                    "action": record.get("action"),
                    "reason": record.get("reason"),
                    "notes": record.get("notes"),
                    "moderated_by": record.get("moderated_by_user_name"),
                    "moderated_at": record.get("moderated_at"),
                }
                for record in moderation_history
            ],
        }
