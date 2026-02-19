"""
Shared models used across multiple routes and services.
"""

from typing import Any, Dict, Optional, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T')


class StandardResponse(BaseModel, Generic[T]):
    """
    Standard response format for API endpoints.

    Attributes:
        success (bool): Whether the operation was successful
        message (str): Human-readable message describing the result
        data (Optional[Dict[str, Any]]): Optional data payload
        error (Optional[str]): Error details if operation failed
    """
    success: bool
    message: str
    data: Optional[T] = None
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """
    Standard error response format.

    Attributes:
        success (bool): Always False for error responses
        error (str): Error message
        details (Optional[Dict[str, Any]]): Additional error details
    """
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    """
    Standard success response format.

    Attributes:
        success (bool): Always True for success responses
        message (str): Success message
        data (Optional[Dict[str, Any]]): Response data
    """
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None