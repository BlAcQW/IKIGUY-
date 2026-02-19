"""
Enhanced error handling utilities for user management and organization systems.

This module provides comprehensive error handling, validation, and recovery mechanisms
for authentication and organization management operations.
"""

from typing import Dict, Any, Optional, List, Union
from fastapi import HTTPException
from pydantic import ValidationError
import logging
from datetime import datetime, timezone
from enum import Enum
import traceback

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """Standardized error codes for user management operations."""

    # Authentication Errors
    INVALID_CREDENTIALS = "AUTH001"
    ACCOUNT_LOCKED = "AUTH002"
    EMAIL_NOT_VERIFIED = "AUTH003"
    TOKEN_EXPIRED = "AUTH004"
    TOKEN_INVALID = "AUTH005"
    SESSION_EXPIRED = "AUTH006"
    WEAK_PASSWORD = "AUTH007"
    EMAIL_ALREADY_EXISTS = "AUTH008"
    RATE_LIMIT_EXCEEDED = "AUTH009"

    # Organization Errors
    ORG_NOT_FOUND = "ORG001"
    ORG_ACCESS_DENIED = "ORG002"
    ORG_ALREADY_EXISTS = "ORG003"
    ORG_MEMBER_LIMIT_EXCEEDED = "ORG004"
    ORG_INVALID_ROLE = "ORG005"
    ORG_OWNER_REQUIRED = "ORG006"
    ORG_CANNOT_DELETE_LAST_OWNER = "ORG007"

    # User Management Errors
    USER_NOT_FOUND = "USER001"
    USER_ALREADY_EXISTS = "USER002"
    USER_INACTIVE = "USER003"
    USER_PERMISSION_DENIED = "USER004"
    USER_INVALID_DATA = "USER005"

    # Database Errors
    DB_CONNECTION_ERROR = "DB001"
    DB_OPERATION_FAILED = "DB002"
    DB_CONSTRAINT_VIOLATION = "DB003"
    DB_TIMEOUT = "DB004"

    # Validation Errors
    VALIDATION_FAILED = "VAL001"
    INVALID_EMAIL_FORMAT = "VAL002"
    INVALID_PASSWORD_FORMAT = "VAL003"
    REQUIRED_FIELD_MISSING = "VAL004"

    # System Errors
    INTERNAL_ERROR = "SYS001"
    EXTERNAL_SERVICE_ERROR = "SYS002"
    CONFIGURATION_ERROR = "SYS003"


class UserManagementError(Exception):
    """Base exception for user management operations."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.original_error = original_error
        self.timestamp = datetime.now(timezone.utc)
        super().__init__(message)


class AuthenticationError(UserManagementError):
    """Authentication-specific errors."""
    pass


class OrganizationError(UserManagementError):
    """Organization-specific errors."""
    pass


class ValidationError(UserManagementError):
    """Validation-specific errors."""
    pass


class DatabaseError(UserManagementError):
    """Database operation errors."""
    pass


def handle_auth_errors(func):
    """Decorator for handling authentication-related errors."""

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AuthenticationError:
            raise
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise AuthenticationError(
                message="An unexpected authentication error occurred",
                error_code=ErrorCode.INTERNAL_ERROR,
                status_code=500,
                original_error=e
            )

    return wrapper


def handle_organization_errors(func):
    """Decorator for handling organization-related errors."""

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except OrganizationError:
            raise
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise OrganizationError(
                message="An unexpected organization error occurred",
                error_code=ErrorCode.INTERNAL_ERROR,
                status_code=500,
                original_error=e
            )

    return wrapper


def handle_database_errors(func):
    """Decorator for handling database-related errors."""

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except DatabaseError:
            raise
        except Exception as e:
            error_message = str(e).lower()

            if "timeout" in error_message:
                raise DatabaseError(
                    message="Database operation timed out",
                    error_code=ErrorCode.DB_TIMEOUT,
                    status_code=503,
                    original_error=e
                )
            elif "connection" in error_message:
                raise DatabaseError(
                    message="Database connection error",
                    error_code=ErrorCode.DB_CONNECTION_ERROR,
                    status_code=503,
                    original_error=e
                )
            elif "duplicate" in error_message or "unique" in error_message:
                raise DatabaseError(
                    message="Data constraint violation",
                    error_code=ErrorCode.DB_CONSTRAINT_VIOLATION,
                    status_code=409,
                    original_error=e
                )
            else:
                raise DatabaseError(
                    message="Database operation failed",
                    error_code=ErrorCode.DB_OPERATION_FAILED,
                    status_code=500,
                    original_error=e
                )

    return wrapper


class ValidationHelper:
    """Helper class for enhanced validation with detailed error reporting."""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Enhanced email validation."""
        import re

        if not email or not isinstance(email, str):
            raise ValidationError(
                message="Email is required",
                error_code=ErrorCode.REQUIRED_FIELD_MISSING,
                status_code=400
            )

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError(
                message="Invalid email format",
                error_code=ErrorCode.INVALID_EMAIL_FORMAT,
                status_code=400,
                details={"email": email}
            )

        if len(email) > 320:  # RFC 5321 limit
            raise ValidationError(
                message="Email address too long",
                error_code=ErrorCode.INVALID_EMAIL_FORMAT,
                status_code=400
            )

        return True

    @staticmethod
    def validate_password(password: str, min_length: int = 8) -> bool:
        """Enhanced password validation with security requirements."""
        if not password or not isinstance(password, str):
            raise ValidationError(
                message="Password is required",
                error_code=ErrorCode.REQUIRED_FIELD_MISSING,
                status_code=400
            )

        issues = []

        if len(password) < min_length:
            issues.append(f"Password must be at least {min_length} characters long")

        if not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one number")

        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            issues.append("Password must contain at least one special character")

        # Check for common weak patterns
        weak_patterns = ["123456", "password", "qwerty", "abc123"]
        if any(pattern in password.lower() for pattern in weak_patterns):
            issues.append("Password contains common weak patterns")

        if issues:
            raise ValidationError(
                message="Password does not meet security requirements",
                error_code=ErrorCode.WEAK_PASSWORD,
                status_code=400,
                details={"issues": issues}
            )

        return True

    @staticmethod
    def validate_organization_name(name: str) -> bool:
        """Validate organization name."""
        if not name or not isinstance(name, str):
            raise ValidationError(
                message="Organization name is required",
                error_code=ErrorCode.REQUIRED_FIELD_MISSING,
                status_code=400
            )

        name = name.strip()
        if len(name) < 2:
            raise ValidationError(
                message="Organization name must be at least 2 characters long",
                error_code=ErrorCode.VALIDATION_FAILED,
                status_code=400
            )

        if len(name) > 100:
            raise ValidationError(
                message="Organization name cannot exceed 100 characters",
                error_code=ErrorCode.VALIDATION_FAILED,
                status_code=400
            )

        # Check for invalid characters
        import re
        if not re.match(r'^[a-zA-Z0-9\s\-_&.()]+$', name):
            raise ValidationError(
                message="Organization name contains invalid characters",
                error_code=ErrorCode.VALIDATION_FAILED,
                status_code=400,
                details={"allowed_chars": "letters, numbers, spaces, hyphens, underscores, &, ., ()"}
            )

        return True


class ErrorRecovery:
    """Helper class for error recovery and fallback mechanisms."""

    @staticmethod
    async def retry_database_operation(
        operation,
        max_retries: int = 3,
        delay: float = 1.0,
        backoff_factor: float = 2.0
    ):
        """Retry database operations with exponential backoff."""
        import asyncio

        for attempt in range(max_retries):
            try:
                return await operation()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise DatabaseError(
                        message=f"Database operation failed after {max_retries} attempts",
                        error_code=ErrorCode.DB_OPERATION_FAILED,
                        status_code=503,
                        original_error=e
                    )

                wait_time = delay * (backoff_factor ** attempt)
                logger.warning(f"Database operation failed (attempt {attempt + 1}), retrying in {wait_time}s: {str(e)}")
                await asyncio.sleep(wait_time)

    @staticmethod
    def create_safe_fallback_response(
        operation_name: str,
        error: Exception,
        fallback_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a safe fallback response for failed operations."""
        logger.error(f"Operation {operation_name} failed: {str(error)}")

        return {
            "success": False,
            "error": {
                "code": getattr(error, 'error_code', ErrorCode.INTERNAL_ERROR),
                "message": str(error),
                "operation": operation_name,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "data": fallback_data or {}
        }


def convert_to_http_exception(error: UserManagementError) -> HTTPException:
    """Convert custom errors to FastAPI HTTPException."""
    return HTTPException(
        status_code=error.status_code,
        detail={
            "code": error.error_code,
            "message": error.message,
            "details": error.details,
            "timestamp": error.timestamp.isoformat()
        }
    )


class SecurityMonitor:
    """Monitor and handle security-related errors and suspicious activities."""

    def __init__(self):
        self.failed_attempts = {}
        self.suspicious_ips = set()

    def record_failed_login(self, email: str, ip_address: str) -> bool:
        """Record failed login attempt and check for suspicious activity."""
        key = f"{email}:{ip_address}"
        current_time = datetime.now(timezone.utc)

        if key not in self.failed_attempts:
            self.failed_attempts[key] = []

        self.failed_attempts[key].append(current_time)

        # Clean old attempts (older than 1 hour)
        self.failed_attempts[key] = [
            attempt for attempt in self.failed_attempts[key]
            if (current_time - attempt).total_seconds() < 3600
        ]

        # Check if too many failed attempts
        if len(self.failed_attempts[key]) >= 5:
            self.suspicious_ips.add(ip_address)
            logger.warning(f"Suspicious activity detected: {email} from {ip_address}")
            return True

        return False

    def is_ip_suspicious(self, ip_address: str) -> bool:
        """Check if IP address is marked as suspicious."""
        return ip_address in self.suspicious_ips

    def clear_failed_attempts(self, email: str, ip_address: str) -> None:
        """Clear failed attempts for successful login."""
        key = f"{email}:{ip_address}"
        if key in self.failed_attempts:
            del self.failed_attempts[key]


# Global security monitor instance
security_monitor = SecurityMonitor()