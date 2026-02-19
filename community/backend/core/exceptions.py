"""
Custom exceptions for the African Language Community Platform.
"""


class BaseAPIException(Exception):
    """Base exception for all API exceptions."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(BaseAPIException):
    """Exception raised for authentication failures."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(BaseAPIException):
    """Exception raised for authorization failures."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status_code=403)


class ValidationError(BaseAPIException):
    """Exception raised for validation failures."""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status_code=422)


class NotFoundError(BaseAPIException):
    """Exception raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ConflictError(BaseAPIException):
    """Exception raised for resource conflicts."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status_code=409)


class StorageError(BaseAPIException):
    """Exception raised for storage operation failures."""

    def __init__(self, message: str = "Storage operation failed"):
        super().__init__(message, status_code=500)


class RateLimitError(BaseAPIException):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)
