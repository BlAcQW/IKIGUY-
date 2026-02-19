"""
Audit log models for MongoDB.

Tracks administrative actions and book visibility changes for accountability.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from bson import ObjectId


class AuditAction(str, Enum):
    """Types of actions that can be logged."""

    VISIBILITY_CHANGED = "visibility_changed"
    BOOK_HIDDEN = "book_hidden"
    BOOK_UNHIDDEN = "book_unhidden"
    BOOK_DELETED = "book_deleted"
    BOOK_RESTORED = "book_restored"
    BOOK_PERMANENTLY_DELETED = "book_permanently_deleted"
    BOOK_CREATED = "book_created"


class AuditLog(BaseModel):
    """
    Audit log document model.

    Represents an action taken on a book by an admin or author.
    Used for accountability and compliance tracking.
    """

    audit_id: str = Field(..., description="Unique audit log identifier")
    action: AuditAction = Field(..., description="Type of action performed")
    entity_type: str = Field(default="book", description="Type of entity (book, user, etc)")
    entity_id: str = Field(..., description="ID of the affected entity (book_id)")
    actor_id: str = Field(..., description="User ID of person performing action")
    actor_email: str = Field(..., description="Email of person performing action")
    actor_role: str = Field(..., description="Role of person performing action")
    reason: Optional[str] = Field(None, description="Reason for the action")
    changes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Field changes: {field: {before: X, after: Y}}"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the action"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }
        populate_by_name = True


class AuditLogInDB(AuditLog):
    """
    Audit log model with MongoDB _id.

    Used for documents retrieved from database.
    """

    id: Optional[str] = Field(None, alias="_id")

    @classmethod
    def from_mongo(cls, doc: Dict[str, Any]) -> "AuditLogInDB":
        """
        Convert MongoDB document to AuditLogInDB.

        Handles ObjectId conversion for _id field.
        """
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return cls(**doc)

    class Config:
        """Pydantic config."""

        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }
