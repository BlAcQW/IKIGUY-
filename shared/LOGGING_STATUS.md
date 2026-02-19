# Shared Logging Status

## Current State

### Existing Files
- `/opt/kasaai/apps/shared/unified_logging.py` - Exists but only contains a docstring, no implementation
- `/opt/kasaai/apps/shared/config/` - Configuration engine exists with basic logging setup

### Current Practice
All applications currently use Python's standard `logging` module directly:

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Message")
logger.error("Error message")
```

### Examples from Codebase

**Drive Service:**
```python
# apps/shared/services/drive_service.py
self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
```

**Configuration Engine:**
```python
# apps/shared/config/engine.py
self.logger = logging.getLogger("ConfigurationEngine")
```

**Hetzner Storage:**
```python
# apps/shared/storage/hetzner_storage_box.py
self.logger = logging.getLogger(f"apps.shared.storage.hetzner_storage_box.{self.__class__.__name__}")
```

## Recommendation

### Option 1: Implement Unified Logging (Recommended)
Create a proper shared logging utility with:
- Consistent log formatting across all apps
- Structured logging (JSON) for production
- Log levels per module
- Correlation IDs for request tracking
- Integration with monitoring tools (e.g., ELK, CloudWatch)
- Performance metrics logging

### Option 2: Continue with Standard Logging
Keep using Python's built-in logging module with:
- Standardized naming convention
- Consistent log format configuration in each app
- Document best practices in CLAUDE.md

## Proposed Implementation (Option 1)

```python
# /opt/kasaai/apps/shared/unified_logging.py
"""
Unified Logging for KasaAI Platform

Provides consistent logging across all KasaAI applications with:
- Structured logging (JSON)
- Correlation IDs
- Performance tracking
- Standardized formatting
"""

import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional
import traceback
from contextvars import ContextVar

# Correlation ID context for request tracking
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add correlation ID if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_data["correlation_id"] = correlation_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


class KasaAILogger:
    """
    Unified logger for KasaAI applications

    Usage:
        from apps.shared.unified_logging import get_logger

        logger = get_logger(__name__)
        logger.info("Processing request", extra_data={"user_id": "123"})
    """

    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Add handler if not already configured
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(handler)

    def _log(self, level: int, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Internal logging method"""
        if extra_data:
            self.logger.log(level, message, extra={'extra_data': extra_data})
        else:
            self.logger.log(level, message)

    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, kwargs)

    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, kwargs)

    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, kwargs)

    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, kwargs)

    def critical(self, message: str, **kwargs):
        self._log(logging.CRITICAL, message, kwargs)

    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, extra={'extra_data': kwargs} if kwargs else None)


def get_logger(name: str, level: int = logging.INFO) -> KasaAILogger:
    """
    Get a KasaAI logger instance

    Args:
        name: Logger name (usually __name__)
        level: Logging level (default: INFO)

    Returns:
        KasaAILogger instance
    """
    return KasaAILogger(name, level)


def set_correlation_id(correlation_id: str):
    """Set correlation ID for request tracking"""
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID"""
    return correlation_id_var.get()


# FastAPI middleware for correlation IDs
class CorrelationIdMiddleware:
    """
    Middleware to add correlation IDs to requests

    Usage in FastAPI:
        app.add_middleware(CorrelationIdMiddleware)
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            import uuid
            correlation_id = str(uuid.uuid4())
            set_correlation_id(correlation_id)

            # Add to response headers
            async def send_with_correlation_id(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.append((b"x-correlation-id", correlation_id.encode()))
                    message["headers"] = headers
                await send(message)

            await self.app(scope, receive, send_with_correlation_id)
        else:
            await self.app(scope, receive, send)
```

## Migration Plan

If we implement unified logging:

1. **Phase 1**: Implement the shared logging module
2. **Phase 2**: Update one app (e.g., Drive) to use it
3. **Phase 3**: Gradually migrate other apps
4. **Phase 4**: Add monitoring integration (optional)

## Decision Needed

Should we:
1. Implement the unified logging system? (Better for production monitoring)
2. Document standard logging practices and keep current approach? (Simpler)

Let me know your preference and I can implement accordingly.
