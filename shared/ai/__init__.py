"""
AI and Machine Learning Services

This package contains AI and ML capabilities for the KasaAI platform:
- Ghanaian model fine-tuning
- Intent detection and sentiment analysis
- AI-powered features for call handling
- Real-time conversation analytics
"""

from .ghanaian_model_finetuner import (
    GhanaianModelFineTuner,
    ModelType,
    GhanaianDialect,
    AccentType,
    TrainingData,
    ModelConfig,
    ModelEvaluation,
    GhanaianModelManager
)

from .ghanaian_intent_detector import (
    GhanaianIntentDetector,
    IntentType,
    IntentResult
)

from .ghanaian_sentiment_analyzer import (
    GhanaianSentimentAnalyzer,
    SentimentResult,
    SentimentType
)

from .ghanaian_ner_analyzer import (
    GhanaianNERAnalyzer,
    NERResult,
    EntityType
)

from .ai_powered_features import (
    AIPoweredFeatures,
    CallRoutingDecision,
    ConversationAnalytics,
    CallSummary,
    ObjectionType,
    ConversationSentiment,
    CallOutcome
)

from .ghanaian_e2e_tester import (
    GhanaianE2ETester,
    TestResult,
    TestScenario,
    TestCase,
    E2ETestReport
)

from .ghanaian_error_handler import (
    ErrorHandler,
    ErrorType,
    ErrorSeverity,
    FallbackStrategy,
    ProcessingError
)

from .ghanaian_offline_processor import (
    OfflineProcessor,
    ProcessingMode,
    CacheStrategy,
    OfflineModelConfig
)

from .ghanaian_performance_benchmark import (
    PerformanceBenchmark,
    BenchmarkResult,
    PerformanceMetrics,
    BenchmarkConfig,
    ResourceMonitor
)

__all__ = [
    # Model Fine-tuning
    "GhanaianModelFineTuner",
    "ModelType",
    "GhanaianDialect", 
    "AccentType",
    "TrainingData",
    "ModelConfig",
    "ModelEvaluation",
    "GhanaianModelManager",
    
    # Intent Detection
    "GhanaianIntentDetector",
    "IntentType",
    "IntentResult",
    
    # Sentiment Analysis
    "GhanaianSentimentAnalyzer",
    "SentimentResult",
    "SentimentType",
    
    # Named Entity Recognition
    "GhanaianNERAnalyzer",
    "NERResult",
    "EntityType",
    
    # AI-Powered Features
    "AIPoweredFeatures",
    "CallRoutingDecision",
    "ConversationAnalytics",
    "CallSummary",
    "ObjectionType",
    "ConversationSentiment",
    "CallOutcome",
    
    # Testing and Evaluation
    "GhanaianE2ETester",
    "TestResult",
    "TestScenario",
    "TestCase",
    "E2ETestReport",
    
    # Error Handling
    "ErrorHandler",
    "ErrorType",
    "ErrorSeverity",
    "FallbackStrategy",
    "ProcessingError",
    
    # Offline Processing
    "OfflineProcessor",
    "ProcessingMode",
    "CacheStrategy",
    "OfflineModelConfig",
    
    # Performance Benchmarking
    "PerformanceBenchmark",
    "BenchmarkResult",
    "PerformanceMetrics",
    "BenchmarkConfig",
    "ResourceMonitor"
]
