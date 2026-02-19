"""
Unit tests for Ghanaian error handler

Tests error handling, retry mechanisms, and fallback strategies.
"""

import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.shared.ai.ghanaian_error_handler import (
    ErrorHandler,
    ErrorContext,
    ErrorType,
    ErrorSeverity,
    FallbackStrategy,
    RetryConfig,
    FallbackConfig,
    ProcessingError,
    with_error_handling
)


class TestErrorType:
    """Test error type enum"""
    
    def test_error_types(self):
        """Test error type values"""
        assert ErrorType.NETWORK_ERROR.value == "network_error"
        assert ErrorType.API_ERROR.value == "api_error"
        assert ErrorType.AUTHENTICATION_ERROR.value == "authentication_error"
        assert ErrorType.RATE_LIMIT_ERROR.value == "rate_limit_error"
        assert ErrorType.TIMEOUT_ERROR.value == "timeout_error"
        assert ErrorType.VALIDATION_ERROR.value == "validation_error"
        assert ErrorType.PROCESSING_ERROR.value == "processing_error"
        assert ErrorType.MODEL_ERROR.value == "model_error"
        assert ErrorType.CACHE_ERROR.value == "cache_error"
        assert ErrorType.UNKNOWN_ERROR.value == "unknown_error"


class TestErrorSeverity:
    """Test error severity enum"""
    
    def test_error_severities(self):
        """Test error severity values"""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"


class TestFallbackStrategy:
    """Test fallback strategy enum"""
    
    def test_fallback_strategies(self):
        """Test fallback strategy values"""
        assert FallbackStrategy.RETRY.value == "retry"
        assert FallbackStrategy.CACHE.value == "cache"
        assert FallbackStrategy.OFFLINE.value == "offline"
        assert FallbackStrategy.SIMPLIFIED.value == "simplified"
        assert FallbackStrategy.DEFAULT.value == "default"
        assert FallbackStrategy.SKIP.value == "skip"


class TestRetryConfig:
    """Test retry configuration"""
    
    def test_default_config(self):
        """Test default retry configuration"""
        config = RetryConfig()
        
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_backoff is True
        assert config.jitter is True
        assert len(config.retry_on_errors) == 3
        assert ErrorType.NETWORK_ERROR in config.retry_on_errors
        assert ErrorType.TIMEOUT_ERROR in config.retry_on_errors
        assert ErrorType.RATE_LIMIT_ERROR in config.retry_on_errors
    
    def test_custom_config(self):
        """Test custom retry configuration"""
        config = RetryConfig(
            max_retries=5,
            base_delay=2.0,
            max_delay=120.0,
            exponential_backoff=False,
            jitter=False,
            retry_on_errors=[ErrorType.API_ERROR, ErrorType.VALIDATION_ERROR]
        )
        
        assert config.max_retries == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0
        assert config.exponential_backoff is False
        assert config.jitter is False
        assert len(config.retry_on_errors) == 2
        assert ErrorType.API_ERROR in config.retry_on_errors
        assert ErrorType.VALIDATION_ERROR in config.retry_on_errors


class TestFallbackConfig:
    """Test fallback configuration"""
    
    def test_default_config(self):
        """Test default fallback configuration"""
        config = FallbackConfig()
        
        assert config.enable_cache_fallback is True
        assert config.enable_offline_fallback is True
        assert config.enable_simplified_fallback is True
        assert config.enable_default_fallback is True
        assert config.cache_ttl_hours == 24
        assert config.offline_confidence_threshold == 0.6
        assert config.simplified_processing is True
    
    def test_custom_config(self):
        """Test custom fallback configuration"""
        config = FallbackConfig(
            enable_cache_fallback=False,
            enable_offline_fallback=False,
            enable_simplified_fallback=True,
            enable_default_fallback=True,
            cache_ttl_hours=12,
            offline_confidence_threshold=0.8,
            simplified_processing=False
        )
        
        assert config.enable_cache_fallback is False
        assert config.enable_offline_fallback is False
        assert config.enable_simplified_fallback is True
        assert config.enable_default_fallback is True
        assert config.cache_ttl_hours == 12
        assert config.offline_confidence_threshold == 0.8
        assert config.simplified_processing is False


class TestErrorContext:
    """Test error context"""
    
    def test_default_context(self):
        """Test default error context"""
        context = ErrorContext(
            operation="test_operation",
            language="tw"
        )
        
        assert context.operation == "test_operation"
        assert context.language == "tw"
        assert context.text is None
        assert context.provider is None
        assert context.retry_count == 0
        assert context.user_id is None
        assert context.session_id is None
        assert context.metadata == {}
    
    def test_custom_context(self):
        """Test custom error context"""
        context = ErrorContext(
            operation="sentiment_analysis",
            language="en-GH",
            text="test text",
            provider="abena_ai",
            retry_count=2,
            user_id="user123",
            session_id="session456",
            metadata={"key": "value"}
        )
        
        assert context.operation == "sentiment_analysis"
        assert context.language == "en-GH"
        assert context.text == "test text"
        assert context.provider == "abena_ai"
        assert context.retry_count == 2
        assert context.user_id == "user123"
        assert context.session_id == "session456"
        assert context.metadata == {"key": "value"}


class TestProcessingError:
    """Test processing error model"""
    
    def test_processing_error_creation(self):
        """Test processing error creation"""
        context = ErrorContext(operation="test", language="tw")
        error = ProcessingError(
            error_type=ErrorType.NETWORK_ERROR,
            severity=ErrorSeverity.HIGH,
            message="Connection failed",
            context=context,
            original_error="ConnectionError",
            stack_trace="traceback..."
        )
        
        assert error.error_type == ErrorType.NETWORK_ERROR
        assert error.severity == ErrorSeverity.HIGH
        assert error.message == "Connection failed"
        assert error.context == context
        assert error.original_error == "ConnectionError"
        assert error.stack_trace == "traceback..."


class TestErrorHandler:
    """Test error handler functionality"""
    
    @pytest.fixture
    def retry_config(self):
        """Create retry configuration for testing"""
        return RetryConfig(
            max_retries=2,
            base_delay=0.1,  # Short delay for testing
            max_delay=1.0,
            exponential_backoff=True,
            jitter=False  # Disable jitter for predictable tests
        )
    
    @pytest.fixture
    def fallback_config(self):
        """Create fallback configuration for testing"""
        return FallbackConfig(
            enable_cache_fallback=True,
            enable_offline_fallback=True,
            enable_simplified_fallback=True,
            enable_default_fallback=True
        )
    
    @pytest.fixture
    def error_handler(self, retry_config, fallback_config):
        """Create error handler instance"""
        return ErrorHandler(retry_config, fallback_config)
    
    def test_initialization(self, retry_config, fallback_config):
        """Test error handler initialization"""
        handler = ErrorHandler(retry_config, fallback_config)
        
        assert handler.retry_config == retry_config
        assert handler.fallback_config == fallback_config
        assert handler.error_callbacks == {}
        assert handler.error_history == []
        assert handler.error_counts == {}
        assert handler.recovery_stats["successful_retries"] == 0
        assert handler.recovery_stats["successful_fallbacks"] == 0
        assert handler.recovery_stats["failed_recoveries"] == 0
    
    def test_error_classification(self, error_handler):
        """Test error classification"""
        # Test timeout error
        timeout_error = Exception("Request timed out")
        error_type = error_handler._classify_error(timeout_error)
        assert error_type == ErrorType.TIMEOUT_ERROR
        
        # Test network error
        network_error = Exception("Connection refused")
        error_type = error_handler._classify_error(network_error)
        assert error_type == ErrorType.NETWORK_ERROR
        
        # Test authentication error
        auth_error = Exception("Unauthorized access")
        error_type = error_handler._classify_error(auth_error)
        assert error_type == ErrorType.AUTHENTICATION_ERROR
        
        # Test rate limit error
        rate_error = Exception("Rate limit exceeded")
        error_type = error_handler._classify_error(rate_error)
        assert error_type == ErrorType.RATE_LIMIT_ERROR
        
        # Test unknown error
        unknown_error = Exception("Some random error")
        error_type = error_handler._classify_error(unknown_error)
        assert error_type == ErrorType.UNKNOWN_ERROR
    
    def test_severity_determination(self, error_handler):
        """Test error severity determination"""
        # Test critical severity
        severity = error_handler._determine_severity(ErrorType.AUTHENTICATION_ERROR, Exception())
        assert severity == ErrorSeverity.CRITICAL
        
        # Test high severity
        severity = error_handler._determine_severity(ErrorType.NETWORK_ERROR, Exception())
        assert severity == ErrorSeverity.HIGH
        
        # Test medium severity
        severity = error_handler._determine_severity(ErrorType.RATE_LIMIT_ERROR, Exception())
        assert severity == ErrorSeverity.MEDIUM
        
        # Test low severity
        severity = error_handler._determine_severity(ErrorType.VALIDATION_ERROR, Exception())
        assert severity == ErrorSeverity.LOW
    
    def test_retry_delay_calculation(self, error_handler):
        """Test retry delay calculation"""
        # Test exponential backoff
        delay1 = error_handler._calculate_retry_delay(1)
        delay2 = error_handler._calculate_retry_delay(2)
        delay3 = error_handler._calculate_retry_delay(3)
        
        assert delay1 == 0.1  # base_delay
        assert delay2 == 0.2  # base_delay * 2
        assert delay3 == 0.4  # base_delay * 4
        
        # Test with jitter disabled (should be deterministic)
        assert delay1 == error_handler._calculate_retry_delay(1)
    
    def test_should_retry(self, error_handler):
        """Test retry decision logic"""
        context = ErrorContext(operation="test", language="tw")
        
        # Should retry for retryable error with retries remaining
        should_retry = error_handler._should_retry(ErrorType.NETWORK_ERROR, context)
        assert should_retry is True
        
        # Should not retry for non-retryable error
        should_retry = error_handler._should_retry(ErrorType.AUTHENTICATION_ERROR, context)
        assert should_retry is False
        
        # Should not retry when max retries reached
        context.retry_count = 2
        should_retry = error_handler._should_retry(ErrorType.NETWORK_ERROR, context)
        assert should_retry is False
    
    @pytest.mark.asyncio
    async def test_successful_operation(self, error_handler):
        """Test successful operation handling"""
        async def successful_operation():
            return "success"
        
        result, success = await error_handler.handle_operation(
            successful_operation, "test_operation", "tw"
        )
        
        assert result == "success"
        assert success is True
        assert len(error_handler.error_history) == 0
    
    @pytest.mark.asyncio
    async def test_retry_success(self, error_handler):
        """Test successful retry after failure"""
        call_count = 0
        
        async def failing_then_successful_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Connection timeout")
            return "success after retry"
        
        result, success = await error_handler.handle_operation(
            failing_then_successful_operation, "test_operation", "tw"
        )
        
        assert result == "success after retry"
        assert success is True
        assert call_count == 2
        assert error_handler.recovery_stats["successful_retries"] == 1
    
    @pytest.mark.asyncio
    async def test_retry_failure(self, error_handler):
        """Test retry failure"""
        async def always_failing_operation():
            raise Exception("Persistent network error")
        
        result, success = await error_handler.handle_operation(
            always_failing_operation, "test_operation", "tw"
        )
        
        assert result is None
        assert success is False
        assert error_handler.recovery_stats["failed_recoveries"] == 1
    
    @pytest.mark.asyncio
    async def test_simplified_fallback_sentiment(self, error_handler):
        """Test simplified fallback for sentiment analysis"""
        context = ErrorContext(
            operation="sentiment",
            language="tw",
            text="ɛyɛ adeɛ pa"  # "It is good" in Twi
        )
        
        async def failing_operation():
            raise Exception("API error")
        
        result = await error_handler._simplified_fallback(
            context, failing_operation
        )
        
        assert result is not None
        assert result["sentiment"] == "positive"
        assert result["confidence"] > 0.3
        assert result["source"] == "simplified_fallback"
    
    @pytest.mark.asyncio
    async def test_simplified_fallback_ner(self, error_handler):
        """Test simplified fallback for NER"""
        context = ErrorContext(
            operation="ner",
            language="en-GH",
            text="John Doe lives in Accra"
        )
        
        async def failing_operation():
            raise Exception("API error")
        
        result = await error_handler._simplified_fallback(
            context, failing_operation
        )
        
        assert result is not None
        assert "entities" in result
        assert result["source"] == "simplified_fallback"
        
        # Should detect "John Doe" as person and "Accra" as location
        entities = result["entities"]
        person_entities = [e for e in entities if e["type"] == "PERSON"]
        location_entities = [e for e in entities if e["type"] == "LOCATION"]
        
        assert len(person_entities) > 0
        assert len(location_entities) > 0
    
    @pytest.mark.asyncio
    async def test_simplified_fallback_intent(self, error_handler):
        """Test simplified fallback for intent detection"""
        context = ErrorContext(
            operation="intent",
            language="tw",
            text="ɛte sɛn"  # "How are you?" in Twi
        )
        
        async def failing_operation():
            raise Exception("API error")
        
        result = await error_handler._simplified_fallback(
            context, failing_operation
        )
        
        assert result is not None
        assert result["intent"] == "greeting"
        assert result["confidence"] > 0.7
        assert result["source"] == "simplified_fallback"
    
    @pytest.mark.asyncio
    async def test_offline_fallback(self, error_handler):
        """Test offline fallback"""
        context = ErrorContext(operation="sentiment", language="tw")
        
        async def failing_operation():
            raise Exception("API error")
        
        result = await error_handler._offline_fallback(
            context, failing_operation
        )
        
        assert result is not None
        assert result["sentiment"] == "neutral"
        assert result["confidence"] == 0.5
        assert result["source"] == "offline_fallback"
    
    @pytest.mark.asyncio
    async def test_default_fallback(self, error_handler):
        """Test default fallback"""
        context = ErrorContext(operation="sentiment", language="tw")
        
        async def failing_operation():
            raise Exception("API error")
        
        result = await error_handler._default_fallback(
            context, failing_operation
        )
        
        assert result is not None
        assert result["sentiment"] == "neutral"
        assert result["confidence"] == 0.5
        assert result["source"] == "default_fallback"
    
    @pytest.mark.asyncio
    async def test_fallback_strategy_order(self, error_handler):
        """Test fallback strategy execution order"""
        context = ErrorContext(operation="sentiment", language="tw")
        
        async def failing_operation():
            raise Exception("API error")
        
        # Mock fallback methods to track execution order
        execution_order = []
        
        async def mock_cache_fallback(*args, **kwargs):
            execution_order.append("cache")
            return None
        
        async def mock_offline_fallback(*args, **kwargs):
            execution_order.append("offline")
            return None
        
        async def mock_simplified_fallback(*args, **kwargs):
            execution_order.append("simplified")
            return {"sentiment": "positive", "confidence": 0.6, "source": "simplified"}
        
        # Replace fallback methods
        error_handler._cache_fallback = mock_cache_fallback
        error_handler._offline_fallback = mock_offline_fallback
        error_handler._simplified_fallback = mock_simplified_fallback
        
        result = await error_handler._try_fallbacks(
            context, failing_operation
        )
        
        # Should try cache, offline, then simplified (which succeeds)
        assert execution_order == ["cache", "offline", "simplified"]
        assert result is not None
        assert result["source"] == "simplified"
    
    def test_error_tracking(self, error_handler):
        """Test error tracking functionality"""
        context = ErrorContext(operation="test", language="tw")
        error = ProcessingError(
            error_type=ErrorType.NETWORK_ERROR,
            severity=ErrorSeverity.HIGH,
            message="Test error",
            context=context
        )
        
        # Track error
        error_handler._track_error(error)
        
        assert len(error_handler.error_history) == 1
        assert error_handler.error_counts[ErrorType.NETWORK_ERROR] == 1
        
        # Track another error
        error_handler._track_error(error)
        assert len(error_handler.error_history) == 2
        assert error_handler.error_counts[ErrorType.NETWORK_ERROR] == 2
    
    def test_get_error_stats(self, error_handler):
        """Test error statistics retrieval"""
        # Add some errors
        context = ErrorContext(operation="test", language="tw")
        error1 = ProcessingError(
            error_type=ErrorType.NETWORK_ERROR,
            severity=ErrorSeverity.HIGH,
            message="Error 1",
            context=context
        )
        error2 = ProcessingError(
            error_type=ErrorType.API_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message="Error 2",
            context=context
        )
        
        error_handler._track_error(error1)
        error_handler._track_error(error2)
        
        stats = error_handler.get_error_stats()
        
        assert stats["total_errors"] == 2
        assert stats["error_counts"][ErrorType.NETWORK_ERROR] == 1
        assert stats["error_counts"][ErrorType.API_ERROR] == 1
        assert "recovery_stats" in stats
        assert "recent_errors" in stats
        assert len(stats["recent_errors"]) == 2
    
    def test_clear_error_history(self, error_handler):
        """Test error history clearing"""
        # Add some errors
        context = ErrorContext(operation="test", language="tw")
        error = ProcessingError(
            error_type=ErrorType.NETWORK_ERROR,
            severity=ErrorSeverity.HIGH,
            message="Test error",
            context=context
        )
        
        error_handler._track_error(error)
        assert len(error_handler.error_history) == 1
        
        # Clear history
        error_handler.clear_error_history()
        assert len(error_handler.error_history) == 0
        assert len(error_handler.error_counts) == 0
        assert error_handler.recovery_stats["successful_retries"] == 0
    
    @pytest.mark.asyncio
    async def test_error_callbacks(self, error_handler):
        """Test error callback execution"""
        callback_called = False
        callback_error = None
        
        def test_callback(error):
            nonlocal callback_called, callback_error
            callback_called = True
            callback_error = error
        
        # Register callback
        error_handler.error_callbacks[ErrorType.NETWORK_ERROR] = [test_callback]
        
        # Create error
        context = ErrorContext(operation="test", language="tw")
        error = ProcessingError(
            error_type=ErrorType.NETWORK_ERROR,
            severity=ErrorSeverity.HIGH,
            message="Test error",
            context=context
        )
        
        # Execute callbacks
        await error_handler._execute_error_callbacks(error)
        
        assert callback_called is True
        assert callback_error == error
    
    @pytest.mark.asyncio
    async def test_async_error_callbacks(self, error_handler):
        """Test async error callback execution"""
        callback_called = False
        callback_error = None
        
        async def test_async_callback(error):
            nonlocal callback_called, callback_error
            callback_called = True
            callback_error = error
        
        # Register callback
        error_handler.error_callbacks[ErrorType.NETWORK_ERROR] = [test_async_callback]
        
        # Create error
        context = ErrorContext(operation="test", language="tw")
        error = ProcessingError(
            error_type=ErrorType.NETWORK_ERROR,
            severity=ErrorSeverity.HIGH,
            message="Test error",
            context=context
        )
        
        # Execute callbacks
        await error_handler._execute_error_callbacks(error)
        
        assert callback_called is True
        assert callback_error == error


class TestErrorHandlerDecorator:
    """Test error handler decorator"""
    
    @pytest.fixture
    def error_handler(self):
        """Create error handler for decorator tests"""
        return ErrorHandler()
    
    @pytest.mark.asyncio
    async def test_decorator_success(self, error_handler):
        """Test decorator with successful operation"""
        @with_error_handling(error_handler, "test_operation", "tw")
        async def test_function():
            return "success"
        
        result = await test_function()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_decorator_with_fallback(self, error_handler):
        """Test decorator with fallback"""
        @with_error_handling(error_handler, "sentiment", "tw")
        async def failing_function():
            raise Exception("API error")
        
        result = await failing_function()
        
        # Should get fallback result
        assert result is not None
        assert "sentiment" in result
        assert result["source"] in ["offline_fallback", "simplified_fallback", "default_fallback"]
    
    @pytest.mark.asyncio
    async def test_decorator_with_language_parameter(self, error_handler):
        """Test decorator with language parameter"""
        @with_error_handling(error_handler, "test_operation", "auto")
        async def test_function(language="tw"):
            return f"success in {language}"
        
        result = await test_function(language="en-GH")
        assert result == "success in en-GH"
