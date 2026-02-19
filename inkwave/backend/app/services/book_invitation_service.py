"""
Book Invitation Service.

Handles book invitation CRUD operations and redemption logic.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.book_invitation import BookInvitation, BookInvitationInDB
from app.models.user import LibraryBook

logger = logging.getLogger(__name__)


class BookInvitationService:
    """Service for managing book invitations."""

    @staticmethod
    async def create_invitation(
        book_id: str,
        created_by: str,
        created_by_email: Optional[str] = None,
        max_uses: Optional[int] = None,
        expires_in_days: Optional[int] = None,
        welcome_message: Optional[str] = None
    ) -> BookInvitation:
        """
        Create a new book invitation.

        Args:
            book_id: ID of the book to grant access to
            created_by: Admin user ID creating the invitation
            created_by_email: Admin email for reference
            max_uses: Maximum number of uses (None = unlimited)
            expires_in_days: Days until expiration (None = never)
            welcome_message: Custom welcome message

        Returns:
            Created BookInvitation

        Raises:
            ValueError: If book not found
        """
        db = get_db()

        # Get book details
        book = await db.books.find_one({"book_id": book_id})
        if not book:
            raise ValueError(f"Book {book_id} not found")

        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Create invitation
        invitation = BookInvitation(
            book_id=book_id,
            book_title=book.get("title", "Unknown"),
            book_cover_url=book.get("cover_url"),
            created_by=created_by,
            created_by_email=created_by_email,
            max_uses=max_uses,
            expires_at=expires_at,
            welcome_message=welcome_message
        )

        # Save to database
        await db.book_invitations.insert_one(invitation.model_dump())

        logger.info(
            f"Created book invitation {invitation.invitation_id} "
            f"for book {book_id} by {created_by_email or created_by}"
        )

        return invitation

    @staticmethod
    async def get_invitation(invitation_id: str) -> Optional[BookInvitation]:
        """
        Get an invitation by ID/token.

        Args:
            invitation_id: Invitation token

        Returns:
            BookInvitation or None if not found
        """
        db = get_db()
        doc = await db.book_invitations.find_one({"invitation_id": invitation_id})

        if not doc:
            return None

        return BookInvitation(**doc)

    @staticmethod
    async def list_invitations(
        created_by: Optional[str] = None,
        book_id: Optional[str] = None,
        include_inactive: bool = False,
        page: int = 1,
        per_page: int = 20
    ) -> tuple[List[BookInvitation], int]:
        """
        List invitations with optional filters.

        Args:
            created_by: Filter by creator user ID
            book_id: Filter by book ID
            include_inactive: Include revoked/expired invitations
            page: Page number (1-indexed)
            per_page: Items per page

        Returns:
            Tuple of (invitations list, total count)
        """
        db = get_db()
        query: Dict[str, Any] = {}

        if created_by:
            query["created_by"] = created_by

        if book_id:
            query["book_id"] = book_id

        if not include_inactive:
            query["is_active"] = True

        skip = (page - 1) * per_page
        total = await db.book_invitations.count_documents(query)

        cursor = db.book_invitations.find(query).sort(
            "created_at", -1
        ).skip(skip).limit(per_page)

        invitations = []
        async for doc in cursor:
            invitations.append(BookInvitation(**doc))

        return invitations, total

    @staticmethod
    async def revoke_invitation(invitation_id: str) -> bool:
        """
        Revoke an invitation.

        Args:
            invitation_id: Invitation token to revoke

        Returns:
            True if revoked, False if not found
        """
        db = get_db()
        result = await db.book_invitations.update_one(
            {"invitation_id": invitation_id},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )

        if result.modified_count > 0:
            logger.info(f"Revoked invitation {invitation_id}")
            return True

        return False

    @staticmethod
    async def redeem_invitation(
        invitation_id: str,
        user_id: str,
        user_email: str
    ) -> Dict[str, Any]:
        """
        Redeem an invitation for a user.

        Adds the book to the user's library and increments usage count.

        Args:
            invitation_id: Invitation token
            user_id: User ID redeeming the invitation
            user_email: User email for logging

        Returns:
            Dict with redemption result

        Raises:
            ValueError: If invitation invalid or already redeemed by user
        """
        db = get_db()

        # Get invitation
        invitation = await BookInvitationService.get_invitation(invitation_id)
        if not invitation:
            raise ValueError("Invitation not found")

        # Check validity
        if not invitation.is_valid():
            status = invitation.get_status()
            raise ValueError(f"Invitation is {status}")

        # Check if user already redeemed this invitation
        if user_id in invitation.redeemed_by:
            raise ValueError("You have already redeemed this invitation")

        # Check if user already has this book in their library (from any invitation)
        has_access = await BookInvitationService.check_user_has_book_access(
            user_id, invitation.book_id
        )
        if has_access:
            # User already has the book - don't add duplicate but still count redemption
            await db.book_invitations.update_one(
                {"invitation_id": invitation_id},
                {
                    "$inc": {"used_count": 1},
                    "$push": {"redeemed_by": user_id},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            logger.info(
                f"User {user_email} redeemed invitation {invitation_id} "
                f"but already has book {invitation.book_id}"
            )
            return {
                "success": True,
                "book_id": invitation.book_id,
                "book_title": invitation.book_title,
                "book_cover_url": invitation.book_cover_url,
                "message": f"You already have access to '{invitation.book_title}'!"
            }

        # Get book details for library
        book = await db.books.find_one({"book_id": invitation.book_id})
        if not book:
            raise ValueError("Book no longer available")

        # Create library book entry
        library_book = LibraryBook(
            book_id=invitation.book_id,
            book_title=invitation.book_title,
            book_cover_url=invitation.book_cover_url,
            book_author=book.get("author"),
            access_type="invitation",
            invitation_id=invitation_id,
            granted_by=invitation.created_by
        )

        # Add to user's library
        await db.users.update_one(
            {"user_id": user_id},
            {
                "$push": {"library_books": library_book.model_dump()},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        # Update invitation usage
        await db.book_invitations.update_one(
            {"invitation_id": invitation_id},
            {
                "$inc": {"used_count": 1},
                "$push": {"redeemed_by": user_id},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        logger.info(
            f"User {user_email} redeemed invitation {invitation_id} "
            f"for book {invitation.book_id}"
        )

        return {
            "success": True,
            "book_id": invitation.book_id,
            "book_title": invitation.book_title,
            "book_cover_url": invitation.book_cover_url,
            "message": f"'{invitation.book_title}' has been added to your library!"
        }

    @staticmethod
    async def get_user_library(user_id: str) -> List[Dict[str, Any]]:
        """
        Get a user's library books.

        Args:
            user_id: User ID

        Returns:
            List of library book dicts with full book details
        """
        db = get_db()

        user = await db.users.find_one({"user_id": user_id})
        if not user:
            return []

        library_books = user.get("library_books", [])

        # Enrich with current book data
        enriched = []
        for lib_book in library_books:
            book = await db.books.find_one({"book_id": lib_book.get("book_id")})
            if book:
                enriched.append({
                    "id": book["book_id"],
                    "title": book.get("title", lib_book.get("book_title")),
                    "author": book.get("author", lib_book.get("book_author")),
                    "cover_url": book.get("cover_url", lib_book.get("book_cover_url")),
                    "description": book.get("description"),
                    "access_type": lib_book.get("access_type", "invitation"),
                    "granted_at": lib_book.get("granted_at"),
                    "processing_status": book.get("processing_status", "ready")
                })

        return enriched

    @staticmethod
    async def check_user_has_book_access(user_id: str, book_id: str) -> bool:
        """
        Check if a user has access to a specific book.

        Args:
            user_id: User ID
            book_id: Book ID

        Returns:
            True if user has access
        """
        db = get_db()

        user = await db.users.find_one(
            {
                "user_id": user_id,
                "library_books.book_id": book_id
            }
        )

        return user is not None

    @staticmethod
    async def get_invitation_stats() -> Dict[str, Any]:
        """
        Get invitation statistics for admin dashboard.

        Returns:
            Stats dict with counts and usage
        """
        db = get_db()

        total = await db.book_invitations.count_documents({})
        active = await db.book_invitations.count_documents({"is_active": True})

        # Get total redemptions
        pipeline = [
            {"$group": {"_id": None, "total_redemptions": {"$sum": "$used_count"}}}
        ]
        result = await db.book_invitations.aggregate(pipeline).to_list(1)
        total_redemptions = result[0]["total_redemptions"] if result else 0

        # Most shared books
        pipeline = [
            {"$group": {"_id": "$book_id", "count": {"$sum": 1}, "title": {"$first": "$book_title"}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        top_books = await db.book_invitations.aggregate(pipeline).to_list(5)

        return {
            "total_invitations": total,
            "active_invitations": active,
            "total_redemptions": total_redemptions,
            "top_shared_books": top_books
        }


# Global service instance
book_invitation_service = BookInvitationService()
