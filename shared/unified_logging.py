"""
Unified Logging for KasaAI Platform

Provides consistent logging across all KasaAI applications with:
- Structured logging (JSON format for production)
- Human-readable format for development
- Correlation IDs for request tracking
- Performance metrics
- Standardized formatting
- Exception tracking with full traceback

Usage:
    from apps.shared.unified_logging import get_logger, set_correlation_id

    # Get a logger
    logger = get_logger(__name__)

    # Log with extra context
    logger.info("Processing request", user_id="123", action="upload")

    # Log exceptions
    try:
        risky_operation()
    except Exception as e:
        logger.exception("Operation failed", operation="upload", file_id="abc")

FastAPI Integration:
    from apps.shared.unified_logging import CorrelationIdMiddleware

    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
import traceback
from contextvars import ContextVar
from pathlib import Path

# Correlation ID context for request tracking across async calls
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)

# Environment detection
_is_production = False
_is_development = True


def set_environment(production: bool = False):
    """
    Set the logging environment

    Args:
        production: If True, use JSON structured logging. If False, use human-readable format
    """
    global _is_production, _is_development
    _is_production = production
    _is_development = not production


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging in production"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.thread,
        }

        # Add correlation ID if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_data["correlation_id"] = correlation_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else "Unknown",
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add extra fields from logger calls
        if hasattr(record, 'extra_data'):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for human-readable logging in development"""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        # Color the level name
        level_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{level_color}{record.levelname:8s}{self.RESET}"

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')

        # Build the base message
        parts = [
            f"{self.BOLD}{timestamp}{self.RESET}",
            record.levelname,
            f"{record.name}",
            f"{record.getMessage()}"
        ]

        # Add correlation ID if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            parts.insert(3, f"[{correlation_id[:8]}]")

        message = " | ".join(parts)

        # Add extra fields if present
        if hasattr(record, 'extra_data') and record.extra_data:
            extra_str = " ".join(f"{k}={v}" for k, v in record.extra_data.items())
            message += f" | {extra_str}"

        # Add exception info if present
        if record.exc_info:
            message += "\n" + "".join(traceback.format_exception(*record.exc_info))

        return message


class KasaAILogger:
    """
    Unified logger for KasaAI applications

    Provides structured logging with correlation IDs and extra context.
    Automatically uses JSON format in production and colored output in development.

    Args:
        name: Logger name (usually __name__)
        level: Logging level (default: INFO)

    Example:
        logger = get_logger(__name__)
        logger.info("User logged in", user_id="123", ip="1.2.3.4")
        logger.error("Upload failed", file_size=1024, error_code="E001")
    """

    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False  # Don't propagate to root logger

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Add appropriate handler based on environment
        handler = logging.StreamHandler(sys.stdout)

        if _is_production:
            handler.setFormatter(StructuredFormatter())
        else:
            handler.setFormatter(ColoredFormatter())

        self.logger.addHandler(handler)

    def _log(self, level: int, message: str, exc_info: Any = None, **kwargs):
        """
        Internal logging method

        Args:
            level: Log level
            message: Log message
            exc_info: Exception info tuple
            **kwargs: Additional context as key-value pairs
        """
        extra = {'extra_data': kwargs} if kwargs else None
        self.logger.log(level, message, exc_info=exc_info, extra=extra)

    def debug(self, message: str, **kwargs):
        """
        Log debug message with optional context

        Args:
            message: Debug message
            **kwargs: Additional context
        """
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """
        Log info message with optional context

        Args:
            message: Info message
            **kwargs: Additional context
        """
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """
        Log warning message with optional context

        Args:
            message: Warning message
            **kwargs: Additional context
        """
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """
        Log error message with optional context

        Args:
            message: Error message
            **kwargs: Additional context
        """
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """
        Log critical message with optional context

        Args:
            message: Critical message
            **kwargs: Additional context
        """
        self._log(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs):
        """
        Log exception with full traceback

        Args:
            message: Exception message
            **kwargs: Additional context

        Example:
            try:
                dangerous_operation()
            except Exception:
                logger.exception("Operation failed", user_id="123")
        """
        self._log(logging.ERROR, message, exc_info=True, **kwargs)


# Cache for logger instances
_logger_cache: Dict[str, KasaAILogger] = {}


def get_logger(name: str, level: int = logging.INFO) -> KasaAILogger:
    """
    Get a KasaAI logger instance (cached)

    Args:
        name: Logger name (usually __name__)
        level: Logging level (default: INFO)

    Returns:
        KasaAILogger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Application started")
    """
    if name not in _logger_cache:
        _logger_cache[name] = KasaAILogger(name, level)
    return _logger_cache[name]


def set_correlation_id(correlation_id: str):
    """
    Set correlation ID for request tracking

    Args:
        correlation_id: Unique ID to track request across services

    Example:
        set_correlation_id("req-123-456")
        logger.info("Processing request")  # Will include correlation_id
    """
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """
    Get current correlation ID

    Returns:
        Current correlation ID or None
    """
    return correlation_id_var.get()


def clear_correlation_id():
    """Clear the current correlation ID"""
    correlation_id_var.set(None)


# FastAPI Middleware for automatic correlation ID injection
class CorrelationIdMiddleware:
    """
    Middleware to automatically add correlation IDs to all requests

    Adds X-Correlation-ID header to responses and sets correlation ID
    in logging context for the entire request lifecycle.

    Usage in FastAPI:
        from fastapi import FastAPI
        from apps.shared.unified_logging import CorrelationIdMiddleware

        app = FastAPI()
        app.add_middleware(CorrelationIdMiddleware)
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            import uuid

            # Try to get correlation ID from request header, or generate new one
            headers = dict(scope.get("headers", []))
            correlation_id = headers.get(b"x-correlation-id", b"").decode() or str(uuid.uuid4())

            set_correlation_id(correlation_id)

            # Add correlation ID to response headers
            async def send_with_correlation_id(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.append((b"x-correlation-id", correlation_id.encode()))
                    message["headers"] = headers
                await send(message)

            try:
                await self.app(scope, receive, send_with_correlation_id)
            finally:
                # Clean up correlation ID after request
                clear_correlation_id()
        else:
            await self.app(scope, receive, send)


# Performance tracking helper
class LogTimer:
    """
    Context manager for timing operations

    Usage:
        logger = get_logger(__name__)
        with LogTimer(logger, "Database query", query="SELECT * FROM users"):
            result = db.execute(query)
    """

    def __init__(self, logger: KasaAILogger, operation: str, **kwargs):
        """
        Initialize timer

        Args:
            logger: Logger instance
            operation: Operation name
            **kwargs: Additional context
        """
        self.logger = logger
        self.operation = operation
        self.context = kwargs
        self.start_time = None

    def __enter__(self):
        """Start timing"""
        import time
        self.start_time = time.perf_counter()
        self.logger.debug(f"Starting {self.operation}", **self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and log duration"""
        import time
        duration = time.perf_counter() - self.start_time

        if exc_type:
            self.logger.error(
                f"{self.operation} failed",
                duration_seconds=duration,
                error=str(exc_val),
                **self.context
            )
        else:
            self.logger.info(
                f"{self.operation} completed",
                duration_seconds=duration,
                **self.context
            )
