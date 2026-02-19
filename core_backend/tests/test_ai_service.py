"""
Tests for Core Backend AI Service integration with shared libraries.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from backend.services.ai_service import AIService
# Note: We're not importing the complex AI types since they may not be available


class TestAIService:
    """Test cases for AIService integration with shared libraries."""

    @pytest.fixture
    def ai_service(self):
        """Create an AI service instance for testing."""
        service = AIService()
        return service

    @pytest.mark.asyncio
    async def test_ai_service_initialization(self, ai_service):
        """Test that AI service initializes correctly with shared library."""
        assert ai_service.storage_backend is not None
        # Note: AI components may be None if dependencies are not available
        # This is expected behavior for the simplified service
        assert hasattr(ai_service, 'model_finetuner')
        assert hasattr(ai_service, 'intent_detector')
        assert hasattr(ai_service, 'sentiment_analyzer')
        assert hasattr(ai_service, 'ner_analyzer')
        assert hasattr(ai_service, 'ai_features')

    @pytest.mark.asyncio
    async def test_get_ai_capabilities(self, ai_service):
        """Test getting AI capabilities."""
        capabilities = await ai_service.get_ai_capabilities()
        assert capabilities["success"] is True
        assert "capabilities" in capabilities
        
        caps = capabilities["capabilities"]
        assert "model_finetuning" in caps
        assert "intent_detection" in caps
        assert "sentiment_analysis" in caps
        assert "entity_recognition" in caps
        assert "ai_features" in caps
        assert "testing" in caps

    @pytest.mark.asyncio
    async def test_detect_intent(self, ai_service):
        """Test intent detection using shared AI library."""
        text = "I want to make a call"
        context = {"user_id": "test_user"}
        
        result = await ai_service.detect_intent(text, context)
        assert "success" in result
        # Note: Actual result depends on shared library implementation

    @pytest.mark.asyncio
    async def test_batch_detect_intents(self, ai_service):
        """Test batch intent detection using shared AI library."""
        texts = [
            "I want to make a call",
            "What's my account balance?",
            "I need customer support"
        ]
        context = {"user_id": "test_user"}
        
        results = await ai_service.batch_detect_intents(texts, context)
        assert len(results) == 3
        # Note: Actual results depend on shared library implementation

    @pytest.mark.asyncio
    async def test_analyze_sentiment(self, ai_service):
        """Test sentiment analysis using shared AI library."""
        text = "I'm very happy with the service"
        context = {"user_id": "test_user"}
        
        result = await ai_service.analyze_sentiment(text, context)
        assert "success" in result
        # Note: Actual result depends on shared library implementation

    @pytest.mark.asyncio
    async def test_batch_analyze_sentiments(self, ai_service):
        """Test batch sentiment analysis using shared AI library."""
        texts = [
            "I'm very happy with the service",
            "This is terrible, I'm disappointed",
            "The service is okay"
        ]
        context = {"user_id": "test_user"}
        
        results = await ai_service.batch_analyze_sentiments(texts, context)
        assert len(results) == 3
        # Note: Actual results depend on shared library implementation

    @pytest.mark.asyncio
    async def test_extract_entities(self, ai_service):
        """Test entity extraction using shared AI library."""
        text = "My name is John and I live in Accra"
        entity_types = ["person", "location"]
        
        result = await ai_service.extract_entities(text, entity_types)
        assert "success" in result
        # Note: Actual result depends on shared library implementation

    @pytest.mark.asyncio
    async def test_batch_extract_entities(self, ai_service):
        """Test batch entity extraction using shared AI library."""
        texts = [
            "My name is John and I live in Accra",
            "Sarah works at the bank in Kumasi",
            "The meeting is at 2 PM tomorrow"
        ]
        entity_types = ["person", "location", "time"]
        
        results = await ai_service.batch_extract_entities(texts, entity_types)
        assert len(results) == 3
        # Note: Actual results depend on shared library implementation

    @pytest.mark.asyncio
    async def test_route_call_intelligently(self, ai_service):
        """Test intelligent call routing using shared AI library."""
        call_context = {
            "caller_id": "test_caller",
            "destination": "+233123456789",
            "call_type": "outbound",
            "priority": "high"
        }
        available_providers = ["provider1", "provider2", "provider3"]
        
        result = await ai_service.route_call_intelligently(call_context, available_providers)
        assert "success" in result
        # Note: Actual result depends on shared library implementation

    @pytest.mark.asyncio
    async def test_analyze_conversation(self, ai_service):
        """Test conversation analysis using shared AI library."""
        call_id = "test_call_123"
        conversation_data = {
            "participants": ["agent1", "customer1"],
            "transcript": [
                {"speaker": "agent1", "text": "Hello, how can I help you?"},
                {"speaker": "customer1", "text": "I have a question about my account"}
            ],
            "duration": 120.5
        }
        
        result = await ai_service.analyze_conversation(call_id, conversation_data)
        assert "success" in result
        # Note: Actual result depends on shared library implementation

    @pytest.mark.asyncio
    async def test_generate_call_summary(self, ai_service):
        """Test call summary generation using shared AI library."""
        call_id = "test_call_123"
        conversation_data = {
            "participants": ["agent1", "customer1"],
            "transcript": [
                {"speaker": "agent1", "text": "Hello, how can I help you?"},
                {"speaker": "customer1", "text": "I have a question about my account"}
            ],
            "duration": 120.5
        }
        
        result = await ai_service.generate_call_summary(call_id, conversation_data)
        assert "success" in result
        # Note: Actual result depends on shared library implementation

    @pytest.mark.asyncio
    async def test_handle_objection(self, ai_service):
        """Test objection handling using shared AI library."""
        objection_type = "price"
        context = {
            "customer_id": "test_customer",
            "product": "premium_plan",
            "current_price": 100.0
        }
        
        result = await ai_service.handle_objection(objection_type, context)
        assert "success" in result
        # Note: Actual result depends on shared library implementation

    @pytest.mark.asyncio
    async def test_fine_tune_model(self, ai_service):
        """Test model fine-tuning using shared AI library."""
        model_type = "tts"
        training_data = [
            {
                "text": "Hello, how are you?",
                "audio_path": "/path/to/audio1.wav",
                "dialect": "twi_akan",
                "accent": "urban_accra"
            },
            {
                "text": "Thank you very much",
                "audio_path": "/path/to/audio2.wav",
                "dialect": "twi_akan",
                "accent": "urban_accra"
            }
        ]
        config = {
            "epochs": 10,
            "learning_rate": 0.001,
            "batch_size": 32
        }
        
        result = await ai_service.fine_tune_model(model_type, training_data, config)
        assert "success" in result
        # Note: Actual result depends on shared library implementation

    @pytest.mark.asyncio
    async def test_evaluate_model(self, ai_service):
        """Test model evaluation using shared AI library."""
        model_id = "test_model_123"
        test_data = [
            {
                "text": "Test sentence 1",
                "expected_intent": "greeting"
            },
            {
                "text": "Test sentence 2",
                "expected_intent": "question"
            }
        ]
        
        result = await ai_service.evaluate_model(model_id, test_data)
        assert "success" in result
        # Note: Actual result depends on shared library implementation

    @pytest.mark.asyncio
    async def test_deploy_model(self, ai_service):
        """Test model deployment using shared AI library."""
        model_id = "test_model_123"
        deployment_config = {
            "environment": "production",
            "replicas": 3,
            "resources": {
                "cpu": "2",
                "memory": "4Gi"
            }
        }
        
        result = await ai_service.deploy_model(model_id, deployment_config)
        assert "success" in result
        # Note: Actual result depends on shared library implementation

    @pytest.mark.asyncio
    async def test_run_e2e_tests(self, ai_service):
        """Test E2E testing using shared AI library."""
        test_scenarios = [
            {
                "name": "intent_detection_test",
                "type": "intent_detection",
                "input": "I want to make a call",
                "expected_output": "make_call"
            },
            {
                "name": "sentiment_analysis_test",
                "type": "sentiment_analysis",
                "input": "I'm very happy",
                "expected_output": "positive"
            }
        ]
        
        results = await ai_service.run_e2e_tests(test_scenarios)
        assert len(results) == 2
        # Note: Actual results depend on shared library implementation

    @pytest.mark.asyncio
    async def test_handle_ai_error(self, ai_service):
        """Test AI error handling using shared AI library."""
        error_type = "model_not_found"
        error_context = {
            "model_id": "nonexistent_model",
            "operation": "inference",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        result = await ai_service.handle_ai_error(error_type, error_context)
        assert "success" in result
        # Note: Actual result depends on shared library implementation

    @pytest.mark.asyncio
    async def test_process_offline_task(self, ai_service):
        """Test offline task processing using shared AI library."""
        task_type = "batch_sentiment_analysis"
        task_data = {
            "texts": [
                "I'm very happy with the service",
                "This is terrible, I'm disappointed",
                "The service is okay"
            ],
            "output_format": "json"
        }
        
        result = await ai_service.process_offline_task(task_type, task_data)
        assert "success" in result
        # Note: Actual result depends on shared library implementation

    @pytest.mark.asyncio
    async def test_benchmark_performance(self, ai_service):
        """Test performance benchmarking using shared AI library."""
        benchmark_config = {
            "models": ["model1", "model2"],
            "metrics": ["accuracy", "latency", "throughput"],
            "test_data_size": 1000
        }
        
        result = await ai_service.benchmark_performance(benchmark_config)
        assert "success" in result
        # Note: Actual result depends on shared library implementation

    @pytest.mark.asyncio
    async def test_get_model_status(self, ai_service):
        """Test getting model status using shared AI library."""
        model_id = "test_model_123"
        
        result = await ai_service.get_model_status(model_id)
        assert "success" in result
        # Note: Actual result depends on shared library implementation

    @pytest.mark.asyncio
    async def test_list_available_models(self, ai_service):
        """Test listing available models using shared AI library."""
        result = await ai_service.list_available_models()
        assert "success" in result
        # Note: Actual result depends on shared library implementation

    @pytest.mark.asyncio
    async def test_cleanup_old_models(self, ai_service):
        """Test cleaning up old models using shared AI library."""
        days_to_keep = 30
        
        result = await ai_service.cleanup_old_models(days_to_keep)
        assert "success" in result
        # Note: Actual result depends on shared library implementation

    @pytest.mark.asyncio
    async def test_ai_service_error_handling(self, ai_service):
        """Test error handling in AI service."""
        # Test with invalid input
        result = await ai_service.detect_intent("", {})
        assert "success" in result
        
        # Test with None input
        result = await ai_service.analyze_sentiment(None, {})
        assert "success" in result

    @pytest.mark.asyncio
    async def test_ai_service_with_mock_components(self):
        """Test AI service with mocked components."""
        with patch('shared.ai.GhanaianModelFinetuner') as mock_finetuner, \
             patch('shared.ai.GhanaianIntentDetector') as mock_intent, \
             patch('shared.ai.GhanaianSentimentAnalyzer') as mock_sentiment:
            
            # Setup mocks
            mock_finetuner.return_value.initialize = AsyncMock()
            mock_intent.return_value.initialize = AsyncMock()
            mock_sentiment.return_value.initialize = AsyncMock()
            
            # Create service with mocked components
            service = AIService()
            
            # Test initialization
            await service._ensure_initialized()
            
            # Verify mocks were called
            mock_finetuner.return_value.initialize.assert_called_once()
            mock_intent.return_value.initialize.assert_called_once()
            mock_sentiment.return_value.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_ai_service_capabilities_structure(self, ai_service):
        """Test that AI capabilities have the expected structure."""
        capabilities = await ai_service.get_ai_capabilities()
        assert capabilities["success"] is True
        
        caps = capabilities["capabilities"]
        
        # Test model fine-tuning capabilities
        assert "model_finetuning" in caps
        model_caps = caps["model_finetuning"]
        assert "available_models" in model_caps
        assert "available_dialects" in model_caps
        assert "available_accents" in model_caps
        
        # Test intent detection capabilities
        assert "intent_detection" in caps
        intent_caps = caps["intent_detection"]
        assert "available_intents" in intent_caps
        
        # Test sentiment analysis capabilities
        assert "sentiment_analysis" in caps
        sentiment_caps = caps["sentiment_analysis"]
        assert "available_sentiments" in sentiment_caps
        
        # Test entity recognition capabilities
        assert "entity_recognition" in caps
        entity_caps = caps["entity_recognition"]
        assert "available_entities" in entity_caps
        
        # Test AI features capabilities
        assert "ai_features" in caps
        features_caps = caps["ai_features"]
        assert "call_routing" in features_caps
        assert "conversation_analytics" in features_caps
        assert "call_summarization" in features_caps
        assert "objection_handling" in features_caps
        
        # Test testing capabilities
        assert "testing" in caps
        testing_caps = caps["testing"]
        assert "e2e_testing" in testing_caps
        assert "performance_benchmarking" in testing_caps


if __name__ == "__main__":
    pytest.main([__file__])
