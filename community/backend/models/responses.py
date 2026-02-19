"""
Response models for African Language Community Platform API.

Defines standard response formats for all API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from datetime import datetime


class BaseResponse(BaseModel):
    """Base response model with common fields."""

    success: bool = True
    message: str = "Operation completed successfully"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseResponse):
    """Health check response model."""

    status: str = "healthy"
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    """Error response model for handling API errors."""

    success: bool = False
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DataResponse(BaseResponse):
    """Generic data response with payload."""

    data: Any
    total_count: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None


class ListResponse(BaseResponse):
    """Response model for list endpoints with pagination."""

    items: List[Any]
    total_count: int
    page: int = 1
    page_size: int = 20
    total_pages: int

    @classmethod
    def create(cls, items: List[Any], total_count: int, page: int = 1, page_size: int = 20):
        """
        Create paginated list response.

        Args:
            items: List of items for current page
            total_count: Total number of items
            page: Current page number
            page_size: Items per page

        Returns:
            ListResponse: Formatted response with pagination info
        """
        total_pages = (total_count + page_size - 1) // page_size
        return cls(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )