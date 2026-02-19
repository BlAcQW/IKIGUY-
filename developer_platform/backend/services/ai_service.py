"""
AI Service for KasaAI Developer Platform.

This service provides AI capabilities using the shared AI library,
with developer-specific optimizations and extensions.
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json

# Fix import paths for shared library
import sys
import os
# Use centralized import configuration

try:
    from .import_config import get_ai_engine
    AIEngine = get_ai_engine()
    from apps.shared.ai import (
        GhanaianModelFineTuner, GhanaianIntentDetector, GhanaianSentimentAnalyzer,
        GhanaianNERAnalyzer, AIPoweredFeatures, GhanaianE2ETester,
        ErrorHandler, OfflineProcessor, PerformanceBenchmark,
        ModelType, GhanaianDialect, AccentType, IntentType, SentimentType,
        EntityType, CallRoutingDecision, ConversationAnalytics, CallSummary,
        ObjectionType, ConversationSentiment, CallOutcome, TestResult,
        ErrorType, ErrorSeverity, FallbackStrategy, ProcessingMode,
        ModelConfig, BenchmarkConfig
    )
    from ..storage import MemoryStorageBackend, StorageConfig
    SHARED_LIBRARY_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Shared library not available: {e}")
    SHARED_LIBRARY_AVAILABLE = False
    # Create placeholder classes for fallback
    class GhanaianModelFineTuner: pass
    class GhanaianIntentDetector: pass
    class GhanaianSentimentAnalyzer: pass
    class GhanaianNERAnalyzer: pass
    class AIPoweredFeatures: pass
    class GhanaianE2ETester: pass
    class ErrorHandler: pass
    class OfflineProcessor: pass
    class PerformanceBenchmark: pass
    class MemoryStorageBackend: pass
    class StorageConfig: pass


class DeveloperAIService:
    """
    Developer Platform AI Service.
    
    Provides AI capabilities using the shared AI library with
    developer-specific optimizations and extensions.
    """
    
    def __init__(self, storage_backend: Optional[Any] = None):
        self.logger = logging.getLogger("DeveloperAIService")
        
        if not SHARED_LIBRARY_AVAILABLE:
            self.logger.warning("Using fallback AI service - shared library not available")
            self._init_fallback()
            return
            
        if storage_backend is None:
            storage_config = StorageConfig(backend_type="memory")
            self.storage = MemoryStorageBackend(storage_config)
        else:
            self.storage = storage_backend
        
        # Initialize AI components with proper configurations
        try:
            # Model Fine-tuner
            model_config = ModelConfig(
                model_type=ModelType.INTENT,
                base_model="bert-base-multilingual-cased",
                target_dialect=GhanaianDialect.TWI_AKAN,
                output_dir="./models",
                batch_size=8,
                learning_rate=1e-5,
                num_epochs=10
            )
            self.model_finetuner = GhanaianModelFineTuner(model_config)
        except Exception as e:
            self.logger.warning(f"Failed to initialize model fine-tuner: {e}")
            self.model_finetuner = None
        
        try:
            # Intent Detector
            self.intent_detector = GhanaianIntentDetector()
        except Exception as e:
            self.logger.warning(f"Failed to initialize intent detector: {e}")
            self.intent_detector = None
        
        try:
            # Sentiment Analyzer
            self.sentiment_analyzer = GhanaianSentimentAnalyzer()
        except Exception as e:
            self.logger.warning(f"Failed to initialize sentiment analyzer: {e}")
            self.sentiment_analyzer = None
        
        try:
            # NER Analyzer
            self.ner_analyzer = GhanaianNERAnalyzer()
        except Exception as e:
            self.logger.warning(f"Failed to initialize NER analyzer: {e}")
            self.ner_analyzer = None
        
        try:
            # AI Powered Features
            self.ai_features = AIPoweredFeatures()
        except Exception as e:
            self.logger.warning(f"Failed to initialize AI features: {e}")
            self.ai_features = None
        
        try:
            # E2E Tester
            self.e2e_tester = GhanaianE2ETester()
        except Exception as e:
            self.logger.warning(f"Failed to initialize E2E tester: {e}")
            self.e2e_tester = None
        
        try:
            # Error Handler
            self.error_handler = ErrorHandler()
        except Exception as e:
            self.logger.warning(f"Failed to initialize error handler: {e}")
            self.error_handler = None
        
        try:
            # Offline Processor
            self.offline_processor = OfflineProcessor()
        except Exception as e:
            self.logger.warning(f"Failed to initialize offline processor: {e}")
            self.offline_processor = None
        
        try:
            # Performance Benchmark
            self.performance_benchmark = PerformanceBenchmark()
        except Exception as e:
            self.logger.warning(f"Failed to initialize performance benchmark: {e}")
            self.performance_benchmark = None
        
        # Developer-specific configuration
        self.dev_config = self._load_developer_environment_config()
    
    def _init_fallback(self):
        """Initialize fallback components when shared library is not available."""
        self.storage = None
        self.model_finetuner = None
        self.intent_detector = None
        self.sentiment_analyzer = None
        self.ner_analyzer = None
        self.ai_features = None
        self.e2e_tester = None
        self.error_handler = None
        self.offline_processor = None
        self.performance_benchmark = None
        self.dev_config = self._load_developer_environment_config()
    
    def _load_developer_environment_config(self):
        """Load developer-specific environment configuration."""
        return {
            'ai_enabled': os.getenv('DEV_AI_ENABLED', 'true').lower() == 'true',
            'fallback_enabled': os.getenv('DEV_AI_FALLBACK_ENABLED', 'true').lower() == 'true',
            'model_cache_dir': os.getenv('DEV_AI_MODEL_CACHE_DIR', './models'),
            'api_timeout': int(os.getenv('DEV_AI_API_TIMEOUT', '30')),
            'max_retries': int(os.getenv('DEV_AI_MAX_RETRIES', '3')),
            'batch_size': int(os.getenv('DEV_AI_BATCH_SIZE', '10')),
            'log_level': os.getenv('DEV_AI_LOG_LEVEL', 'INFO')
        }
    
    async def start(self):
        """Start the AI service."""
        self.logger.info("Starting Developer AI Service")
    
    async def stop(self):
        """Stop the AI service."""
        self.logger.info("Stopping Developer AI Service")
    
    async def fine_tune_model(
        self,
        model_name: str,
        training_data: List[Dict[str, Any]],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fine-tune an AI model."""
        if not SHARED_LIBRARY_AVAILABLE or self.model_finetuner is None:
            return {
                "model_id": f"fallback_{model_name}",
                "status": "fallback_training",
                "message": "Using fallback fine-tuning"
            }
        
        try:
            result = await self.model_finetuner.fine_tune_model(
                model_name=model_name,
                training_data=training_data,
                config=config or {}
            )
            return result
        except Exception as e:
            self.logger.error(f"Error fine-tuning model: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def detect_intent(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Detect intent from text."""
        if not SHARED_LIBRARY_AVAILABLE or self.intent_detector is None:
            return {
                "intent": "fallback_intent",
                "confidence": 0.5,
                "text": text,
                "fallback": True
            }
        
        try:
            result = await self.intent_detector.detect_intent(text, context or {})
            return result
        except Exception as e:
            self.logger.error(f"Error detecting intent: {e}")
            return {"error": str(e), "intent": "unknown"}
    
    async def analyze_sentiment(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze sentiment from text."""
        if not SHARED_LIBRARY_AVAILABLE or self.sentiment_analyzer is None:
            return {
                "sentiment": "neutral",
                "score": 0.0,
                "text": text,
                "fallback": True
            }
        
        try:
            result = await self.sentiment_analyzer.analyze_sentiment(text, context or {})
            return result
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {e}")
            return {"error": str(e), "sentiment": "unknown"}
    
    async def get_developer_ai_config(self) -> Dict[str, Any]:
        """Get developer AI configuration."""
        return {
            "config": self.dev_config,
            "shared_library_available": SHARED_LIBRARY_AVAILABLE,
            "components": {
                "model_finetuner": self.model_finetuner is not None,
                "intent_detector": self.intent_detector is not None,
                "sentiment_analyzer": self.sentiment_analyzer is not None,
                "ner_analyzer": self.ner_analyzer is not None,
                "ai_features": self.ai_features is not None,
                "e2e_tester": self.e2e_tester is not None,
                "error_handler": self.error_handler is not None,
                "offline_processor": self.offline_processor is not None,
                "performance_benchmark": self.performance_benchmark is not None
            }
        }
