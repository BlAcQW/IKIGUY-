"""
Enhanced error handling and fallback system for Ghanaian language processing

This module provides intelligent error handling, retry mechanisms, and fallback
strategies for Ghanaian language processing operations.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from functools import wraps

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorType(Enum):
    """Error types for Ghanaian language processing"""
    NETWORK_ERROR = "network_error"
    API_ERROR = "api_error"
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    TIMEOUT_ERROR = "timeout_error"
    VALIDATION_ERROR = "validation_error"
    PROCESSING_ERROR = "processing_error"
    MODEL_ERROR = "model_error"
    CACHE_ERROR = "cache_error"
    UNKNOWN_ERROR = "unknown_error"


class FallbackStrategy(Enum):
    """Fallback strategies"""
    RETRY = "retry"
    CACHE = "cache"
    OFFLINE = "offline"
    SIMPLIFIED = "simplified"
    DEFAULT = "default"
    SKIP = "skip"


@dataclass
class ErrorContext:
    """Context information for errors"""
    operation: str
    language: str
    text: Optional[str] = None
    provider: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    retry_count: int = 0
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetryConfig:
    """Configuration for retry mechanisms"""
    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_backoff: bool = True
    jitter: bool = True
    retry_on_errors: List[ErrorType] = field(default_factory=lambda: [
        ErrorType.NETWORK_ERROR,
        ErrorType.TIMEOUT_ERROR,
        ErrorType.RATE_LIMIT_ERROR
    ])


@dataclass
class FallbackConfig:
    """Configuration for fallback mechanisms"""
    enable_cache_fallback: bool = True
    enable_offline_fallback: bool = True
    enable_simplified_fallback: bool = True
    enable_default_fallback: bool = True
    cache_ttl_hours: int = 24
    offline_confidence_threshold: float = 0.6
    simplified_processing: bool = True


class ProcessingError(BaseModel):
    """Processing error model"""
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    context: ErrorContext
    original_error: Optional[str] = None
    stack_trace: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorHandler:
    """
    Enhanced error handler for Ghanaian language processing
    
    Provides intelligent error handling, retry mechanisms, and fallback strategies.
    """
    
    def __init__(
        self,
        retry_config: RetryConfig = None,
        fallback_config: FallbackConfig = None,
        error_callbacks: Dict[ErrorType, List[Callable]] = None
    ):
        """
        Initialize error handler
        
        Args:
            retry_config: Retry configuration
            fallback_config: Fallback configuration
            error_callbacks: Custom error callbacks
        """
        self.retry_config = retry_config or RetryConfig()
        self.fallback_config = fallback_config or FallbackConfig()
        self.error_callbacks = error_callbacks or {}
        
        # Error tracking
        self.error_history: List[ProcessingError] = []
        self.error_counts: Dict[ErrorType, int] = {}
        self.recovery_stats = {
            "successful_retries": 0,
            "successful_fallbacks": 0,
            "failed_recoveries": 0
        }
    
    async def handle_operation(
        self,
        operation: Callable,
        operation_name: str,
        language: str,
        *args,
        context: Optional[ErrorContext] = None,
        **kwargs
    ) -> Tuple[Any, bool]:
        """
        Handle operation with error handling and fallbacks
        
        Args:
            operation: Operation to execute
            operation_name: Name of the operation
            language: Language code
            *args: Operation arguments
            context: Error context
            **kwargs: Operation keyword arguments
            
        Returns:
            Tuple of (result, success_flag)
        """
        error_context = context or ErrorContext(
            operation=operation_name,
            language=language
        )
        
        try:
            # Try primary operation
            result = await operation(*args, **kwargs)
            return result, True
            
        except Exception as e:
            # Handle error with retries and fallbacks
            return await self._handle_error(e, error_context, operation, *args, **kwargs)
    
    async def _handle_error(
        self,
        error: Exception,
        context: ErrorContext,
        operation: Callable,
        *args,
        **kwargs
    ) -> Tuple[Any, bool]:
        """
        Handle error with retries and fallbacks
        
        Args:
            error: The exception that occurred
            context: Error context
            operation: Original operation
            *args: Operation arguments
            **kwargs: Operation keyword arguments
            
        Returns:
            Tuple of (result, success_flag)
        """
        # Classify error
        error_type = self._classify_error(error)
        severity = self._determine_severity(error_type, error)
        
        # Create processing error
        processing_error = ProcessingError(
            error_type=error_type,
            severity=severity,
            message=str(error),
            context=context,
            original_error=type(error).__name__,
            stack_trace=self._get_stack_trace(error)
        )
        
        # Log error
        self._log_error(processing_error)
        
        # Track error
        self._track_error(processing_error)
        
        # Execute custom callbacks
        await self._execute_error_callbacks(processing_error)
        
        # Try retry mechanism
        if self._should_retry(error_type, context):
            result = await self._retry_operation(operation, context, *args, **kwargs)
            if result is not None:
                self.recovery_stats["successful_retries"] += 1
                return result, True
        
        # Try fallback mechanisms
        result = await self._try_fallbacks(context, operation, *args, **kwargs)
        if result is not None:
            self.recovery_stats["successful_fallbacks"] += 1
            return result, True
        
        # All recovery attempts failed
        self.recovery_stats["failed_recoveries"] += 1
        return None, False
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify error type based on exception"""
        error_name = type(error).__name__.lower()
        error_message = str(error).lower()
        
        if any(keyword in error_name or keyword in error_message for keyword in ["timeout", "timedout"]):
            return ErrorType.TIMEOUT_ERROR
        elif any(keyword in error_name or keyword in error_message for keyword in ["network", "connection", "unreachable"]):
            return ErrorType.NETWORK_ERROR
        elif any(keyword in error_name or keyword in error_message for keyword in ["auth", "unauthorized", "forbidden"]):
            return ErrorType.AUTHENTICATION_ERROR
        elif any(keyword in error_name or keyword in error_message for keyword in ["rate", "limit", "quota"]):
            return ErrorType.RATE_LIMIT_ERROR
        elif any(keyword in error_name or keyword in error_message for keyword in ["validation", "invalid"]):
            return ErrorType.VALIDATION_ERROR
        elif any(keyword in error_name or keyword in error_message for keyword in ["model", "inference"]):
            return ErrorType.MODEL_ERROR
        elif any(keyword in error_name or keyword in error_message for keyword in ["cache", "storage"]):
            return ErrorType.CACHE_ERROR
        elif any(keyword in error_name or keyword in error_message for keyword in ["api", "http", "response"]):
            return ErrorType.API_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR
    
    def _determine_severity(self, error_type: ErrorType, error: Exception) -> ErrorSeverity:
        """Determine error severity"""
        if error_type in [ErrorType.AUTHENTICATION_ERROR, ErrorType.CRITICAL]:
            return ErrorSeverity.CRITICAL
        elif error_type in [ErrorType.NETWORK_ERROR, ErrorType.TIMEOUT_ERROR]:
            return ErrorSeverity.HIGH
        elif error_type in [ErrorType.RATE_LIMIT_ERROR, ErrorType.API_ERROR]:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def _should_retry(self, error_type: ErrorType, context: ErrorContext) -> bool:
        """Determine if operation should be retried"""
        return (
            error_type in self.retry_config.retry_on_errors and
            context.retry_count < self.retry_config.max_retries
        )
    
    async def _retry_operation(
        self,
        operation: Callable,
        context: ErrorContext,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """Retry operation with exponential backoff"""
        for attempt in range(context.retry_count + 1, self.retry_config.max_retries + 1):
            try:
                # Calculate delay
                delay = self._calculate_retry_delay(attempt)
                
                logger.info(f"Retrying operation {context.operation} (attempt {attempt}/{self.retry_config.max_retries}) after {delay}s")
                
                # Wait before retry
                await asyncio.sleep(delay)
                
                # Update context
                context.retry_count = attempt
                context.timestamp = datetime.utcnow()
                
                # Execute operation
                result = await operation(*args, **kwargs)
                logger.info(f"Retry successful for operation {context.operation}")
                return result
                
            except Exception as e:
                logger.warning(f"Retry attempt {attempt} failed for operation {context.operation}: {e}")
                continue
        
        logger.error(f"All retry attempts failed for operation {context.operation}")
        return None
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff and jitter"""
        if self.retry_config.exponential_backoff:
            delay = min(
                self.retry_config.base_delay * (2 ** (attempt - 1)),
                self.retry_config.max_delay
            )
        else:
            delay = self.retry_config.base_delay
        
        if self.retry_config.jitter:
            # Add jitter (±25% of delay)
            import random
            jitter = delay * 0.25 * random.uniform(-1, 1)
            delay += jitter
        
        return max(0.1, delay)  # Minimum 0.1 second
    
    async def _try_fallbacks(
        self,
        context: ErrorContext,
        operation: Callable,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """Try fallback mechanisms in order of preference"""
        fallback_strategies = [
            (FallbackStrategy.CACHE, self._cache_fallback),
            (FallbackStrategy.OFFLINE, self._offline_fallback),
            (FallbackStrategy.SIMPLIFIED, self._simplified_fallback),
            (FallbackStrategy.DEFAULT, self._default_fallback)
        ]
        
        for strategy, fallback_func in fallback_strategies:
            if self._is_fallback_enabled(strategy):
                try:
                    result = await fallback_func(context, operation, *args, **kwargs)
                    if result is not None:
                        logger.info(f"Fallback {strategy.value} successful for operation {context.operation}")
                        return result
                except Exception as e:
                    logger.warning(f"Fallback {strategy.value} failed for operation {context.operation}: {e}")
                    continue
        
        logger.error(f"All fallback strategies failed for operation {context.operation}")
        return None
    
    def _is_fallback_enabled(self, strategy: FallbackStrategy) -> bool:
        """Check if fallback strategy is enabled"""
        if strategy == FallbackStrategy.CACHE:
            return self.fallback_config.enable_cache_fallback
        elif strategy == FallbackStrategy.OFFLINE:
            return self.fallback_config.enable_offline_fallback
        elif strategy == FallbackStrategy.SIMPLIFIED:
            return self.fallback_config.enable_simplified_fallback
        elif strategy == FallbackStrategy.DEFAULT:
            return self.fallback_config.enable_default_fallback
        return False
    
    async def _cache_fallback(
        self,
        context: ErrorContext,
        operation: Callable,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """Cache fallback strategy"""
        # This would integrate with the offline processor cache
        # For now, return None to indicate no cached result
        return None
    
    async def _offline_fallback(
        self,
        context: ErrorContext,
        operation: Callable,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """Offline fallback strategy"""
        # This would use offline models for processing
        # For now, return a basic fallback result
        if context.operation == "sentiment":
            return {
                "sentiment": "neutral",
                "confidence": 0.5,
                "source": "offline_fallback"
            }
        elif context.operation == "ner":
            return {
                "entities": [],
                "confidence": 0.3,
                "source": "offline_fallback"
            }
        elif context.operation == "intent":
            return {
                "intent": "unknown",
                "confidence": 0.4,
                "source": "offline_fallback"
            }
        return None
    
    async def _simplified_fallback(
        self,
        context: ErrorContext,
        operation: Callable,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """Simplified processing fallback"""
        # Use simplified processing rules
        if context.operation == "sentiment":
            return self._simplified_sentiment_analysis(context.text or "")
        elif context.operation == "ner":
            return self._simplified_ner_analysis(context.text or "")
        elif context.operation == "intent":
            return self._simplified_intent_detection(context.text or "")
        return None
    
    def _simplified_sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """Simplified sentiment analysis using basic patterns"""
        positive_words = ["good", "nice", "great", "excellent", "happy", "ɛyɛ", "yɛ", "pa"]
        negative_words = ["bad", "terrible", "awful", "sad", "angry", "nyɛ", "ɛnyɛ", "bone"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
            confidence = min(0.7, 0.3 + (positive_count * 0.1))
        elif negative_count > positive_count:
            sentiment = "negative"
            confidence = min(0.7, 0.3 + (negative_count * 0.1))
        else:
            sentiment = "neutral"
            confidence = 0.5
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "source": "simplified_fallback"
        }
    
    def _simplified_ner_analysis(self, text: str) -> Dict[str, Any]:
        """Simplified NER analysis using basic patterns"""
        entities = []
        
        # Basic name detection (capitalized words)
        import re
        name_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
        names = re.findall(name_pattern, text)
        for name in names:
            entities.append({
                "text": name,
                "type": "PERSON",
                "confidence": 0.6
            })
        
        # Basic location detection
        location_words = ["accra", "kumasi", "tamale", "ghana", "africa"]
        text_lower = text.lower()
        for location in location_words:
            if location in text_lower:
                entities.append({
                    "text": location,
                    "type": "LOCATION",
                    "confidence": 0.7
                })
        
        return {
            "entities": entities,
            "confidence": 0.5 if entities else 0.3,
            "source": "simplified_fallback"
        }
    
    def _simplified_intent_detection(self, text: str) -> Dict[str, Any]:
        """Simplified intent detection using basic patterns"""
        text_lower = text.lower()
        
        # Basic intent patterns
        if any(word in text_lower for word in ["hello", "hi", "ɛte sɛn", "wo ho te sɛn"]):
            intent = "greeting"
            confidence = 0.8
        elif any(word in text_lower for word in ["bye", "goodbye", "yɛbɛhyia bio", "kɔ yie"]):
            intent = "farewell"
            confidence = 0.8
        elif any(word in text_lower for word in ["help", "support", "kyerɛ me", "boa me"]):
            intent = "request"
            confidence = 0.7
        elif any(word in text_lower for word in ["thank", "thanks", "meda wo ase", "da wo ase"]):
            intent = "thanks"
            confidence = 0.8
        else:
            intent = "unknown"
            confidence = 0.4
        
        return {
            "intent": intent,
            "confidence": confidence,
            "source": "simplified_fallback"
        }
    
    async def _default_fallback(
        self,
        context: ErrorContext,
        operation: Callable,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """Default fallback strategy"""
        # Return safe default values
        if context.operation == "sentiment":
            return {
                "sentiment": "neutral",
                "confidence": 0.5,
                "source": "default_fallback"
            }
        elif context.operation == "ner":
            return {
                "entities": [],
                "confidence": 0.0,
                "source": "default_fallback"
            }
        elif context.operation == "intent":
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "source": "default_fallback"
            }
        return None
    
    def _log_error(self, error: ProcessingError):
        """Log error with appropriate level"""
        log_message = f"Error in {error.context.operation}: {error.message} (Type: {error.error_type.value}, Severity: {error.severity.value})"
        
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _track_error(self, error: ProcessingError):
        """Track error for analytics"""
        self.error_history.append(error)
        self.error_counts[error.error_type] = self.error_counts.get(error.error_type, 0) + 1
        
        # Keep only recent errors (last 1000)
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]
    
    async def _execute_error_callbacks(self, error: ProcessingError):
        """Execute custom error callbacks"""
        callbacks = self.error_callbacks.get(error.error_type, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(error)
                else:
                    callback(error)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")
    
    def _get_stack_trace(self, error: Exception) -> str:
        """Get stack trace from exception"""
        import traceback
        return "".join(traceback.format_exception(type(error), error, error.__traceback__))
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            "total_errors": len(self.error_history),
            "error_counts": self.error_counts,
            "recovery_stats": self.recovery_stats,
            "recent_errors": [
                {
                    "type": error.error_type.value,
                    "severity": error.severity.value,
                    "operation": error.context.operation,
                    "timestamp": error.timestamp.isoformat()
                }
                for error in self.error_history[-10:]  # Last 10 errors
            ]
        }
    
    def clear_error_history(self):
        """Clear error history"""
        self.error_history.clear()
        self.error_counts.clear()
        self.recovery_stats = {
            "successful_retries": 0,
            "successful_fallbacks": 0,
            "failed_recoveries": 0
        }


def with_error_handling(
    error_handler: ErrorHandler,
    operation_name: str,
    language: str = "auto"
):
    """
    Decorator for adding error handling to functions
    
    Args:
        error_handler: Error handler instance
        operation_name: Name of the operation
        language: Language code
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract language from kwargs or use default
            lang = kwargs.get('language', language)
            
            # Create context
            context = ErrorContext(
                operation=operation_name,
                language=lang
            )
            
            # Handle operation with error handling
            result, success = await error_handler.handle_operation(
                func, operation_name, lang, *args, context=context, **kwargs
            )
            
            if not success:
                logger.error(f"Operation {operation_name} failed after all recovery attempts")
            
            return result
        
        return wrapper
    return decorator
