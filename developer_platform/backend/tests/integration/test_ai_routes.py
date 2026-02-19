"""
Integration tests for AI routes.

Tests the AI-related API endpoints using the DeveloperAIService.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json

from main import app

client = TestClient(app)

class TestAIRoutes:
    """Test cases for AI routes."""
    
    @pytest.fixture
    def mock_api_key(self):
        """Mock API key for testing."""
        return "test_api_key_123"
    
    @pytest.fixture
    def mock_tenant_info(self):
        """Mock tenant information."""
        return {"tenant_id": "test_tenant", "api_key": "test_api_key_123"}
    
    def test_fine_tune_model_success(self, mock_api_key):
        """Test successful model fine-tuning."""
        with patch('routes.ai_routes.ai_service.fine_tune_model', new_callable=AsyncMock) as mock_finetune:
            mock_finetune.return_value = {"model_id": "model_123", "status": "training"}
            
            response = client.post(
                "/v1/ai/fine-tune",
                headers={"x-api-key": mock_api_key},
                json={
                    "model_config": {"model_name": "test_model"},
                    "training_data": [{"text": "test", "label": "test"}]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["model_id"] == "model_123"
    
    def test_detect_intent_success(self, mock_api_key):
        """Test successful intent detection."""
        with patch('routes.ai_routes.ai_service.detect_intent', new_callable=AsyncMock) as mock_detect:
            mock_detect.return_value = {"intent": "greeting", "confidence": 0.95}
            
            response = client.post(
                "/v1/ai/intent/detect",
                headers={"x-api-key": mock_api_key},
                json={"text": "Hello there"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["intent"] == "greeting"
    
    def test_analyze_sentiment_success(self, mock_api_key):
        """Test successful sentiment analysis."""
        with patch('routes.ai_routes.ai_service.analyze_sentiment', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {"sentiment": "positive", "score": 0.8}
            
            response = client.post(
                "/v1/ai/sentiment/analyze",
                headers={"x-api-key": mock_api_key},
                json={"text": "I love this product!"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["sentiment"] == "positive"
    
    def test_get_ai_config_success(self, mock_api_key):
        """Test successful AI config retrieval."""
        with patch('routes.ai_routes.ai_service.get_developer_ai_config', new_callable=AsyncMock) as mock_config:
            mock_config.return_value = {"ai_enabled": True, "fallback_enabled": True}
            
            response = client.get(
                "/v1/ai/config",
                headers={"x-api-key": mock_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["ai_enabled"] is True
