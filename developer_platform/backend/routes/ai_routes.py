"""
AI Routes for KasaAI Developer Platform.

This module provides AI-related API endpoints using the DeveloperAIService.
"""

from fastapi import APIRouter, Header
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import logging

from ..services.ai_service import DeveloperAIService
from ..api_consolidation import (
    StandardAPIResponse,
    create_success_response,
    handle_api_exception,
)

# Create router
router = APIRouter(prefix="/v1/ai", tags=["AI Services"])

# Initialize AI service
ai_service = DeveloperAIService()

# Request models
class FineTuneRequest(BaseModel):
    """Request model for fine-tuning an AI model."""
    config: Dict[str, Any]
    training_data: List[Dict[str, Any]]

class IntentDetectionRequest(BaseModel):
    """Request model for intent detection."""
    text: str
    context: Optional[Dict[str, Any]] = None

class SentimentAnalysisRequest(BaseModel):
    """Request model for sentiment analysis."""
    text: str
    context: Optional[Dict[str, Any]] = None

@router.post("/fine-tune", response_model=StandardAPIResponse)
async def fine_tune_model(
    request: FineTuneRequest,
    x_api_key: str = Header(...)
) -> StandardAPIResponse:
    """Fine-tune an AI model."""
    try:
        result = await ai_service.fine_tune_model(
            model_name=request.config.get("model_name", "default"),
            training_data=request.training_data,
            config=request.config
        )

        return create_success_response(
            data=result,
            message="Model fine-tuning completed successfully"
        )
    except Exception as e:
        return handle_api_exception(e, "Failed to fine-tune model")

@router.post("/intent/detect", response_model=StandardAPIResponse)
async def detect_intent(
    request: IntentDetectionRequest,
    x_api_key: str = Header(...)
) -> StandardAPIResponse:
    """Detect intent from text."""
    try:
        result = await ai_service.detect_intent(request.text, request.context)

        return create_success_response(
            data=result,
            message="Intent detection completed successfully"
        )
    except Exception as e:
        return handle_api_exception(e, "Failed to detect intent")

@router.post("/sentiment/analyze", response_model=StandardAPIResponse)
async def analyze_sentiment(
    request: SentimentAnalysisRequest,
    x_api_key: str = Header(...)
) -> StandardAPIResponse:
    """Analyze sentiment from text."""
    try:
        result = await ai_service.analyze_sentiment(request.text, request.context)

        return create_success_response(
            data=result,
            message="Sentiment analysis completed successfully"
        )
    except Exception as e:
        return handle_api_exception(e, "Failed to analyze sentiment")

@router.get("/config", response_model=StandardAPIResponse)
async def get_ai_config(x_api_key: str = Header(...)) -> StandardAPIResponse:
    """Get AI service configuration."""
    try:
        result = await ai_service.get_developer_ai_config()
        
        return create_success_response(
            data=result,
            message="AI configuration retrieved successfully"
        )
    except Exception as e:
        return handle_api_exception(e, "Failed to get AI configuration")
