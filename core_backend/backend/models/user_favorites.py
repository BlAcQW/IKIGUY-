"""
User Favorites Models
Models for managing user favorite automation templates
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class UserFavorite(BaseModel):
    """User favorite template entry"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # From Supabase auth
    template_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserFavoriteCreate(BaseModel):
    """Request model for creating user favorites"""
    template_id: str

class UserFavoriteResponse(BaseModel):
    """Response model for user favorites"""
    id: str
    template_id: str
    created_at: datetime

class UserFavoritesListResponse(BaseModel):
    """Response model for listing user favorites"""
    favorites: List[UserFavoriteResponse]
    total: int

class ToggleFavoriteResponse(BaseModel):
    """Response model for toggling favorites"""
    success: bool
    is_favorite: bool
    message: str