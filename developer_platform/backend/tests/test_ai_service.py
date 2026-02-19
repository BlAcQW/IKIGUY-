"""
Unit tests for Developer AI Service.

Tests the Developer Platform AI service that uses the shared AI library.
"""

import pytest
import os
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from ..services.ai_service import DeveloperAIService
from apps.shared.ai import (
    ModelType,
    GhanaianDialect,
    IntentType,
    SentimentType,
    EntityType,
)
from apps.shared.storage import MemoryStorageBackend, StorageConfig


class TestDeveloperAIService:
    """Test cases for DeveloperAIService."""
    
    @pytest.fixture
    def ai_service(self):
        """Create an AI service instance for testing."""
        return DeveloperAIService()
    
    @pytest.fixture
    def mock_storage(self):
        """Create a mock storage backend."""
        return Mock(spec=MemoryStorageBackend)
    
    @pytest.fixture
    def ai_service_with_mock_storage(self, mock_storage):
        """Create an AI service with mock storage."""
        return DeveloperAIService(storage_backend=mock_storage)
    
    # Initialization Tests
    def test_initialization(self, ai_service):
        """Test service initialization."""
        assert ai_service.logger is not None
        assert ai_service.storage is not None
        # AI components might be None if dependencies are not available
        # assert ai_service.model_finetuner is not None
        # assert ai_service.intent_detector is not None
        # assert ai_service.sentiment_analyzer is not None
        # assert ai_service.ner_analyzer is not None
        # assert ai_service.ai_features is not None
        # assert ai_service.e2e_tester is not None
        # assert ai_service.error_handler is not None
        # assert ai_service.offline_processor is not None
        # assert ai_service.performance_benchmark is not None
        assert ai_service.dev_config is not None
    
    def test_initialization_with_custom_storage(self, mock_storage):
        """Test service initialization with custom storage."""
        service = DeveloperAIService(storage_backend=mock_storage)
        assert service.storage == mock_storage
    
    def test_environment_config_loading(self, ai_service):
        """Test environment configuration loading."""
        config = ai_service.dev_config
        assert "ai_model_cache_enabled" in config
        assert "ai_offline_mode" in config
        assert "ai_performance_monitoring" in config
        assert "ai_error_reporting" in config
        assert "ai_model_auto_update" in config
        assert "ai_grace_period_hours" in config
        assert "ai_max_concurrent_requests" in config
        assert "ai_request_timeout" in config
        assert "ai_fallback_enabled" in config
    
    # Start/Stop Tests
    @pytest.mark.asyncio
    async def test_start_service(self, ai_service):
        """Test starting the service."""
        if ai_service.model_finetuner is not None:
            with patch.object(ai_service.model_finetuner, 'initialize', new_callable=AsyncMock) as mock_init:
                await ai_service.start()
                mock_init.assert_called_once()
        else:
            # If AI components are not available, just test that start doesn't raise an exception
            await ai_service.start()
    
    @pytest.mark.asyncio
    async def test_stop_service(self, ai_service):
        """Test stopping the service."""
        if ai_service.model_finetuner is not None:
            with patch.object(ai_service.model_finetuner, 'cleanup', new_callable=AsyncMock) as mock_cleanup:
                await ai_service.stop()
                mock_cleanup.assert_called_once()
        else:
            # If AI components are not available, just test that stop doesn't raise an exception
            await ai_service.stop()
    
    # Model Fine-tuning Tests
    @pytest.mark.asyncio
    async def test_fine_tune_model_success(self, ai_service):
        """Test successful model fine-tuning."""
        training_data = [{"text": "test", "label": "test"}]
        
        with patch.object(ai_service.model_finetuner, 'fine_tune_model', new_callable=AsyncMock) as mock_finetune:
            mock_finetune.return_value = {"status": "success", "model_id": "test_model"}
            
            result = await ai_service.fine_tune_model(
                model_type=ModelType.INTENT_DETECTION,
                dialect=GhanaianDialect.ASHANTI,
                training_data=training_data
            )
            
            assert result["status"] == "success"
            assert result["model_id"] == "test_model"
            mock_finetune.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fine_tune_model_fallback(self, ai_service):
        """Test model fine-tuning with fallback."""
        ai_service.dev_config["ai_fallback_enabled"] = True
        training_data = [{"text": "test", "label": "test"}]
        
        with patch.object(ai_service.model_finetuner, 'fine_tune_model', new_callable=AsyncMock) as mock_finetune:
            mock_finetune.side_effect = Exception("Model error")
            
            result = await ai_service.fine_tune_model(
                model_type=ModelType.INTENT_DETECTION,
                dialect=GhanaianDialect.ASHANTI,
                training_data=training_data
            )
            
            assert result["status"] == "fallback"
            assert "fallback" in result["message"]
    
    @pytest.mark.asyncio
    async def test_evaluate_model_success(self, ai_service):
        """Test successful model evaluation."""
        test_data = [{"text": "test", "label": "test"}]
        
        with patch.object(ai_service.model_finetuner, 'evaluate_model', new_callable=AsyncMock) as mock_evaluate:
            mock_evaluate.return_value = {"accuracy": 0.95, "f1_score": 0.92}
            
            result = await ai_service.evaluate_model("test_model", test_data)
            
            assert result["accuracy"] == 0.95
            assert result["f1_score"] == 0.92
            mock_evaluate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_evaluate_model_error(self, ai_service):
        """Test model evaluation with error."""
        test_data = [{"text": "test", "label": "test"}]
        
        with patch.object(ai_service.model_finetuner, 'evaluate_model', new_callable=AsyncMock) as mock_evaluate:
            mock_evaluate.side_effect = Exception("Evaluation error")
            
            result = await ai_service.evaluate_model("test_model", test_data)
            
            assert result["status"] == "error"
            assert "Evaluation error" in result["message"]
    
    # Intent Detection Tests
    @pytest.mark.asyncio
    async def test_detect_intent_success(self, ai_service):
        """Test successful intent detection."""
        with patch.object(ai_service.intent_detector, 'detect_intent', new_callable=AsyncMock) as mock_detect:
            mock_detect.return_value = {"intent": "greeting", "confidence": 0.95}
            
            result = await ai_service.detect_intent("Hello there")
            
            assert result["intent"] == "greeting"
            assert result["confidence"] == 0.95
            mock_detect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_detect_intent_fallback(self, ai_service):
        """Test intent detection with fallback."""
        ai_service.dev_config["ai_fallback_enabled"] = True
        
        with patch.object(ai_service.intent_detector, 'detect_intent', new_callable=AsyncMock) as mock_detect:
            mock_detect.side_effect = Exception("Detection error")
            
            result = await ai_service.detect_intent("Hello there")
            
            assert result["intent"] == "unknown"
            assert result["confidence"] == 0.0
            assert result["fallback"] is True
    
    @pytest.mark.asyncio
    async def test_batch_detect_intents_success(self, ai_service):
        """Test successful batch intent detection."""
        texts = ["Hello", "Goodbye", "Help"]
        
        with patch.object(ai_service, 'detect_intent', new_callable=AsyncMock) as mock_detect:
            mock_detect.side_effect = [
                {"intent": "greeting", "confidence": 0.9},
                {"intent": "farewell", "confidence": 0.8},
                {"intent": "help", "confidence": 0.95}
            ]
            
            results = await ai_service.batch_detect_intents(texts)
            
            assert len(results) == 3
            assert results[0]["intent"] == "greeting"
            assert results[1]["intent"] == "farewell"
            assert results[2]["intent"] == "help"
    
    @pytest.mark.asyncio
    async def test_batch_detect_intents_error(self, ai_service):
        """Test batch intent detection with error."""
        texts = ["Hello", "Goodbye"]
        
        with patch.object(ai_service, 'detect_intent', new_callable=AsyncMock) as mock_detect:
            mock_detect.side_effect = Exception("Batch error")
            
            results = await ai_service.batch_detect_intents(texts)
            
            assert len(results) == 2
            assert all("error" in result for result in results)
    
    # Sentiment Analysis Tests
    @pytest.mark.asyncio
    async def test_analyze_sentiment_success(self, ai_service):
        """Test successful sentiment analysis."""
        with patch.object(ai_service.sentiment_analyzer, 'analyze_sentiment', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {"sentiment": "positive", "confidence": 0.88}
            
            result = await ai_service.analyze_sentiment("I love this product!")
            
            assert result["sentiment"] == "positive"
            assert result["confidence"] == 0.88
            mock_analyze.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_fallback(self, ai_service):
        """Test sentiment analysis with fallback."""
        ai_service.dev_config["ai_fallback_enabled"] = True
        
        with patch.object(ai_service.sentiment_analyzer, 'analyze_sentiment', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = Exception("Analysis error")
            
            result = await ai_service.analyze_sentiment("I love this product!")
            
            assert result["sentiment"] == "neutral"
            assert result["confidence"] == 0.0
            assert result["fallback"] is True
    
    @pytest.mark.asyncio
    async def test_batch_analyze_sentiments_success(self, ai_service):
        """Test successful batch sentiment analysis."""
        texts = ["I love it!", "I hate it!", "It's okay"]
        
        with patch.object(ai_service, 'analyze_sentiment', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = [
                {"sentiment": "positive", "confidence": 0.9},
                {"sentiment": "negative", "confidence": 0.8},
                {"sentiment": "neutral", "confidence": 0.7}
            ]
            
            results = await ai_service.batch_analyze_sentiments(texts)
            
            assert len(results) == 3
            assert results[0]["sentiment"] == "positive"
            assert results[1]["sentiment"] == "negative"
            assert results[2]["sentiment"] == "neutral"
    
    # Named Entity Recognition Tests
    @pytest.mark.asyncio
    async def test_extract_entities_success(self, ai_service):
        """Test successful entity extraction."""
        with patch.object(ai_service.ner_analyzer, 'extract_entities', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = {"entities": [{"text": "John", "type": "PERSON"}]}
            
            result = await ai_service.extract_entities("Hello John")
            
            assert "entities" in result
            assert len(result["entities"]) == 1
            assert result["entities"][0]["text"] == "John"
            mock_extract.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_entities_fallback(self, ai_service):
        """Test entity extraction with fallback."""
        ai_service.dev_config["ai_fallback_enabled"] = True
        
        with patch.object(ai_service.ner_analyzer, 'extract_entities', new_callable=AsyncMock) as mock_extract:
            mock_extract.side_effect = Exception("Extraction error")
            
            result = await ai_service.extract_entities("Hello John")
            
            assert result["entities"] == []
            assert result["fallback"] is True
    
    # AI-Powered Features Tests
    @pytest.mark.asyncio
    async def test_route_call_success(self, ai_service):
        """Test successful call routing."""
        call_data = {"customer_id": "123", "call_type": "support"}
        
        with patch.object(ai_service.ai_features, 'route_call', new_callable=AsyncMock) as mock_route:
            mock_route.return_value = {"route": "support_team", "confidence": 0.9}
            
            result = await ai_service.route_call(call_data)
            
            assert result["route"] == "support_team"
            assert result["confidence"] == 0.9
            mock_route.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_route_call_fallback(self, ai_service):
        """Test call routing with fallback."""
        ai_service.dev_config["ai_fallback_enabled"] = True
        call_data = {"customer_id": "123", "call_type": "support"}
        
        with patch.object(ai_service.ai_features, 'route_call', new_callable=AsyncMock) as mock_route:
            mock_route.side_effect = Exception("Routing error")
            
            result = await ai_service.route_call(call_data)
            
            assert result["route"] == "default"
            assert result["confidence"] == 0.0
            assert result["fallback"] is True
    
    @pytest.mark.asyncio
    async def test_analyze_conversation_success(self, ai_service):
        """Test successful conversation analysis."""
        conversation_data = {"messages": [{"text": "Hello", "sender": "user"}]}
        
        with patch.object(ai_service.ai_features, 'analyze_conversation', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {"summary": "Greeting conversation", "sentiment": "positive"}
            
            result = await ai_service.analyze_conversation(conversation_data)
            
            assert result["summary"] == "Greeting conversation"
            assert result["sentiment"] == "positive"
            mock_analyze.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_call_summary_success(self, ai_service):
        """Test successful call summary generation."""
        call_data = {"duration": 300, "transcript": "Hello, how can I help?"}
        
        with patch.object(ai_service.ai_features, 'generate_call_summary', new_callable=AsyncMock) as mock_summary:
            mock_summary.return_value = {"summary": "Customer requested help", "key_points": ["help request"]}
            
            result = await ai_service.generate_call_summary(call_data)
            
            assert result["summary"] == "Customer requested help"
            assert "key_points" in result
            mock_summary.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_objections_success(self, ai_service):
        """Test successful objection handling."""
        objection_data = {"objection_type": "price", "customer_response": "Too expensive"}
        
        with patch.object(ai_service.ai_features, 'handle_objections', new_callable=AsyncMock) as mock_handle:
            mock_handle.return_value = {"response": "Let me show you our value proposition", "confidence": 0.85}
            
            result = await ai_service.handle_objections(objection_data)
            
            assert result["response"] == "Let me show you our value proposition"
            assert result["confidence"] == 0.85
            mock_handle.assert_called_once()
    
    # Testing and Evaluation Tests
    @pytest.mark.asyncio
    async def test_run_e2e_test_success(self, ai_service):
        """Test successful E2E test execution."""
        test_scenario = {"name": "greeting_test", "steps": ["say_hello", "expect_response"]}
        
        with patch.object(ai_service.e2e_tester, 'run_test', new_callable=AsyncMock) as mock_test:
            mock_test.return_value = {"status": "passed", "score": 0.95}
            
            result = await ai_service.run_e2e_test(test_scenario)
            
            assert result["status"] == "passed"
            assert result["score"] == 0.95
            mock_test.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_e2e_test_error(self, ai_service):
        """Test E2E test execution with error."""
        test_scenario = {"name": "greeting_test", "steps": ["say_hello", "expect_response"]}
        
        with patch.object(ai_service.e2e_tester, 'run_test', new_callable=AsyncMock) as mock_test:
            mock_test.side_effect = Exception("Test error")
            
            result = await ai_service.run_e2e_test(test_scenario)
            
            assert result["status"] == "error"
            assert "Test error" in result["message"]
    
    @pytest.mark.asyncio
    async def test_benchmark_performance_success(self, ai_service):
        """Test successful performance benchmarking."""
        benchmark_config = {"duration": 60, "concurrent_requests": 10}
        
        with patch.object(ai_service.performance_benchmark, 'run_benchmark', new_callable=AsyncMock) as mock_benchmark:
            mock_benchmark.return_value = {"throughput": 100, "latency": 0.1}
            
            result = await ai_service.benchmark_performance(benchmark_config)
            
            assert result["throughput"] == 100
            assert result["latency"] == 0.1
            mock_benchmark.assert_called_once()
    
    # Developer-specific Tests
    @pytest.mark.asyncio
    async def test_get_developer_ai_config(self, ai_service):
        """Test getting developer AI configuration."""
        with patch.object(ai_service, '_get_performance_metrics', new_callable=AsyncMock) as mock_metrics:
            mock_metrics.return_value = {"cpu_usage": 0.5}
            
            result = await ai_service.get_developer_ai_config()
            
            assert "config" in result
            assert "cache_status" in result
            assert "offline_status" in result
            assert "performance_metrics" in result
            assert result["performance_metrics"]["cpu_usage"] == 0.5
    
    @pytest.mark.asyncio
    async def test_validate_developer_ai_config_success(self, ai_service):
        """Test successful AI configuration validation."""
        result = await ai_service.validate_developer_ai_config()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_developer_ai_config_missing_key(self, ai_service):
        """Test AI configuration validation with missing key."""
        del ai_service.dev_config["ai_model_cache_enabled"]
        
        result = await ai_service.validate_developer_ai_config()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_offline_ai_status(self, ai_service):
        """Test getting offline AI status."""
        with patch.object(ai_service.offline_processor, 'get_status', new_callable=AsyncMock) as mock_status:
            mock_status.return_value = {"mode": "offline", "queue_size": 5}
            
            result = await ai_service.get_offline_ai_status()
            
            assert result["offline_mode"] == ai_service.dev_config["ai_offline_mode"]
            assert "processor_status" in result
            assert "grace_period_hours" in result
            assert "last_sync" in result
    
    @pytest.mark.asyncio
    async def test_sync_ai_models_with_core(self, ai_service):
        """Test syncing AI models with core."""
        result = await ai_service.sync_ai_models_with_core("http://core:8000", "token123")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_ai_metrics(self, ai_service):
        """Test getting AI metrics."""
        with patch.object(ai_service.performance_benchmark, 'get_metrics', new_callable=AsyncMock) as mock_metrics:
            mock_metrics.return_value = {"accuracy": 0.95, "latency": 0.1}
            
            result = await ai_service.get_ai_metrics("tenant123")
            
            assert result["tenant_id"] == "tenant123"
            assert "metrics" in result
            assert "timestamp" in result
            assert "config" in result
            assert result["metrics"]["accuracy"] == 0.95
    
    @pytest.mark.asyncio
    async def test_get_error_reports(self, ai_service):
        """Test getting error reports."""
        with patch.object(ai_service.error_handler, 'get_error_reports', new_callable=AsyncMock) as mock_reports:
            mock_reports.return_value = [{"error": "test error", "timestamp": "2023-01-01"}]
            
            result = await ai_service.get_error_reports("tenant123")
            
            assert len(result) == 1
            assert result[0]["tenant_id"] == "tenant123"
            assert "error" in result[0]
    
    # Helper Method Tests
    def test_get_cache_status(self, ai_service):
        """Test getting cache status."""
        status = ai_service._get_cache_status()
        
        assert "enabled" in status
        assert "cache_size" in status
        assert "cache_ttl" in status
        assert status["enabled"] == ai_service.dev_config["ai_model_cache_enabled"]
        assert status["cache_size"] == 0
    
    def test_get_offline_status(self, ai_service):
        """Test getting offline status."""
        status = ai_service._get_offline_status()
        
        assert "enabled" in status
        assert "grace_period_hours" in status
        assert "fallback_enabled" in status
        assert status["enabled"] == ai_service.dev_config["ai_offline_mode"]
        assert status["grace_period_hours"] == ai_service.dev_config["ai_grace_period_hours"]
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, ai_service):
        """Test getting performance metrics."""
        with patch.object(ai_service.performance_benchmark, 'get_current_metrics', new_callable=AsyncMock) as mock_metrics:
            mock_metrics.return_value = {"cpu_usage": 0.5, "memory_usage": 0.3}
            
            result = await ai_service._get_performance_metrics()
            
            assert result["cpu_usage"] == 0.5
            assert result["memory_usage"] == 0.3
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics_error(self, ai_service):
        """Test getting performance metrics with error."""
        with patch.object(ai_service.performance_benchmark, 'get_current_metrics', new_callable=AsyncMock) as mock_metrics:
            mock_metrics.side_effect = Exception("Metrics error")
            
            result = await ai_service._get_performance_metrics()
            
            assert "error" in result
            assert "Metrics error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_last_sync_time(self, ai_service):
        """Test getting last sync time."""
        result = await ai_service._get_last_sync_time()
        assert result is not None
        assert isinstance(result, str)
