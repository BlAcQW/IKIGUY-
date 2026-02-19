"""
Shared Document Processing Module for KasaAI Applications.

This module provides reusable document processing components:
- Base models for documents and processing status
- Topic extraction (AI-powered)
- Collection naming utilities
- Background processing pipeline
- Organization-scoped document management

Usage:
    from shared.document_processing import (
        ProcessingStatus,
        BaseDocument,
        DocumentProcessingPipeline,
        TopicExtractor,
        CollectionNaming
    )

Author: KasaAI Team
Date: 2025-11-28
"""

from .models import (
    ProcessingStatus,
    DocumentType,
    BaseDocument,
    BaseDocumentCreate,
    BaseDocumentUpdate,
    ProcessingResult,
    DocumentChunk,
    EmbeddingMetadata,
    QueryFilter,
)
from .topic_extractor import TopicExtractor, extract_topics
from .collection_naming import (
    CollectionNaming,
    collection_for_book,
    collection_for_material,
)
from .pipeline import (
    DocumentProcessingPipeline,
    DocumentProcessorBase,
    ProcessingConfig,
    process_document_worker,
)
from .session_settings import (
    SessionSettings,
    SessionSettingsService,
    EffectiveSettings,
    TTSSettings,
    ASRSettings,
    LLMSettings,
    PersonalizationSettings,
    PersonalizationBuilder,
)

__all__ = [
    # Models
    "ProcessingStatus",
    "DocumentType",
    "BaseDocument",
    "BaseDocumentCreate",
    "BaseDocumentUpdate",
    "ProcessingResult",
    "DocumentChunk",
    "EmbeddingMetadata",
    "QueryFilter",
    # Topic Extraction
    "TopicExtractor",
    "extract_topics",
    # Collection Naming
    "CollectionNaming",
    "collection_for_book",
    "collection_for_material",
    # Processing Pipeline
    "DocumentProcessingPipeline",
    "DocumentProcessorBase",
    "ProcessingConfig",
    "process_document_worker",
    # Session Settings (InkWave advantage)
    "SessionSettings",
    "SessionSettingsService",
    "EffectiveSettings",
    "TTSSettings",
    "ASRSettings",
    "LLMSettings",
    "PersonalizationSettings",
    "PersonalizationBuilder",
]
