"""
Pytest configuration and fixtures for African Language Community Platform tests.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import Generator


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


class MockCursor:
    """Mock MongoDB cursor with async iteration and to_list support."""

    def __init__(self, items: list):
        """Initialize with list of items."""
        self.items = items
        self._sorted = False
        self._skip_count = 0
        self._limit_count = None

    def sort(self, *args, **kwargs):
        """Mock sort method."""
        self._sorted = True
        return self

    def skip(self, count: int):
        """Mock skip method."""
        self._skip_count = count
        return self

    def limit(self, count: int):
        """Mock limit method."""
        self._limit_count = count
        return self

    async def to_list(self, length: int = None):
        """Convert cursor to list (async)."""
        result = self.items[self._skip_count:]
        if self._limit_count is not None:
            result = result[:self._limit_count]
        elif length is not None:
            result = result[:length]
        return result

    def __aiter__(self):
        """Support async iteration."""
        result = self.items[self._skip_count:]
        if self._limit_count is not None:
            result = result[:self._limit_count]
        return AsyncIterator(result)


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB database for testing."""
    mock_db = AsyncMock()

    # Mock collections
    collections = [
        'language_families', 'language_subfamilies', 'languages',
        'users', 'submissions', 'validations', 'achievements', 'proposals',
        # MLOps collections
        'ml_models', 'ml_training_pipelines', 'dataset_versions',
        'datasets', 'external_resources', 'user_uploads', 'storage_manifests'
    ]

    for collection_name in collections:
        mock_collection = AsyncMock()
        mock_collection.create_index = AsyncMock()
        mock_collection.find_one = AsyncMock()
        mock_collection.find = AsyncMock()
        mock_collection.insert_one = AsyncMock()
        mock_collection.insert_many = AsyncMock()
        mock_collection.update_one = AsyncMock()
        mock_collection.update_many = AsyncMock()
        mock_collection.delete_one = AsyncMock()
        mock_collection.delete_many = AsyncMock()
        mock_collection.count_documents = AsyncMock()
        mock_collection.aggregate = AsyncMock()

        setattr(mock_db, collection_name, mock_collection)

    return mock_db


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    mock_client = MagicMock()
    mock_client.auth.get_user.return_value = MagicMock(
        user=MagicMock(id="supabase123", email="test@example.com")
    )
    return mock_client


@pytest.fixture
def sample_language_family():
    """Sample language family data for testing."""
    return {
        "_id": "507f1f77bcf86cd799439011",
        "name": "niger-congo",
        "display_name": "Niger-Congo Languages",
        "description": "The largest language family in Africa",
        "geographic_region": ["West Africa", "Central Africa"],
        "subfamilies": ["kwa", "bantu", "yoruboid"],
        "shared_features": {
            "noun_classes": True,
            "tone_language": True
        },
        "speaker_count_estimate": 700000000,
        "created_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_language():
    """Sample language data for testing."""
    return {
        "_id": "507f1f77bcf86cd799439012",
        "subfamily_id": "507f1f77bcf86cd799439011",
        "code": "twi",
        "name": "Twi (Akan)",
        "native_name": "Twi",
        "alternative_names": ["Akan", "Asante Twi"],
        "countries": ["Ghana"],
        "regions": ["Ashanti Region", "Brong-Ahafo Region"],
        "speaker_count": 9000000,
        "linguistic_features": {
            "word_order": "SVO",
            "tone_levels": 2
        },
        "phonetic_inventory": {
            "vowels": 10,
            "consonants": 20
        },
        "tonal_system": {
            "levels": ["high", "low"],
            "contours": ["falling", "rising"]
        },
        "writing_systems": ["Latin", "Adinkra"],
        "cultural_context": {
            "primary_use": "daily_communication",
            "ceremonial_use": True
        },
        "dialects": ["Asante", "Akuapem", "Fante"],
        "data_tier": "tier-1-validated",
        "voice_support_level": "full",
        "active_contributors": 156,
        "created_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_user():
    """Sample user data for testing."""
    return {
        "_id": "507f1f77bcf86cd799439013",
        "supabase_id": "supabase123",
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "avatar_url": None,
        "bio": "Test user bio",
        "location": "Ghana",
        "languages_spoken": ["twi", "eng"],
        "level": "newcomer",
        "total_points": 0,
        "achievements": [],
        "badges": [],
        "language_expertise": [],
        "verified_languages": [],
        "can_validate": False,
        "can_moderate": False,
        "can_create_proposals": False,
        "contributions_count": 0,
        "validations_count": 0,
        "quality_rating": 0.0,
        "reputation_score": 0.0,
        "is_active": True,
        "member_since": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_submission():
    """Sample submission data for testing."""
    return {
        "_id": "507f1f77bcf86cd799439014",
        "contributor_id": "507f1f77bcf86cd799439013",
        "language_family": "niger-congo",
        "language_subfamily": "kwa",
        "language_code": "twi",
        "dialect": "asante",
        "type": "audio",
        "category": "story",
        "title": "Traditional Akan Story",
        "description": "A traditional story told in Twi",
        "file_url": "/uploads/audio/story123.wav",
        "file_size": 1048576,
        "file_format": "wav",
        "duration_seconds": 60,
        "text_content": None,
        "translation": "This is a traditional story...",
        "transliteration": None,
        "external_url": None,
        "source_attribution": "Traditional folklore",
        "tier": "tier-3-submitted",
        "validation_status": "pending",
        "quality_scores": {},
        "cultural_context": "Traditional storytelling context",
        "usage_context": "Educational use",
        "cultural_appropriateness": None,
        "view_count": 0,
        "upvotes": 0,
        "downvotes": 0,
        "is_flagged": False,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": None
    }


@pytest.fixture
def auth_headers():
    """Sample authentication headers for testing."""
    return {
        "Authorization": "Bearer test_token"
    }


@pytest.fixture
def mock_file_upload():
    """Mock file upload for testing."""
    mock_file = MagicMock()
    mock_file.filename = "test_audio.wav"
    mock_file.content_type = "audio/wav"
    mock_file.size = 1048576
    mock_file.read.return_value = b"mock_audio_data"
    return mock_file


class AsyncIterator:
    """Helper class for creating async iterators in tests."""

    def __init__(self, items):
        self.items = iter(items)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.items)
        except StopIteration:
            raise StopAsyncIteration


@pytest.fixture
def async_iterator_factory():
    """Factory for creating async iterators in tests."""
    return AsyncIterator


@pytest.fixture
def mock_cursor_factory():
    """Factory for creating mock cursors in tests."""
    return MockCursor


# ============================================================================
# MLOps Platform Fixtures
# ============================================================================


@pytest.fixture
def sample_ml_model():
    """Sample ML model data for testing."""
    from datetime import datetime
    return {
        "_id": "507f1f77bcf86cd799439020",
        "model_uuid": "model-uuid-123",
        "name": "Twi TTS Model",
        "description": "Text-to-speech model for Twi language",
        "model_type": "tts",
        "architecture": "melotts",
        "version": "1.0.0",
        "languages": ["twi"],
        "primary_language": "twi",  # Fix: Added required field
        "is_multilingual": False,  # Fix: Added required field
        "language_ids": ["507f1f77bcf86cd799439012"],
        "framework": "pytorch",
        "framework_version": "2.0.0",
        "performance_metrics": {
            "mos": 4.2,
            "rtf": 0.3
        },
        "training_datasets": [],  # Fix: Changed from training_dataset_ids
        "evaluation_datasets": [],  # Fix: Added required field
        "storage_path": "models/tts/model-uuid-123/v1.0.0",
        "checkpoint_path": "models/tts/model-uuid-123/v1.0.0/checkpoint.pt",  # Fix: Added required field
        "deployment_status": "experimental",  # Fix: Added required field
        "is_public": True,  # Fix: Added required field
        "access_level": "public",  # Fix: Added required field
        "created_by": "507f1f77bcf86cd799439013",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "download_count": 0,
        "view_count": 0,
        "upvotes": 0,
        "downvotes": 0,
        "license": "MIT",
        "tags": ["tts", "melotts", "twi"],
        "file_size_mb": 250.5,
        "model_size_mb": 250.5,  # Fix: Added for compatibility
        "versions": [],
        "known_issues": []
    }


@pytest.fixture
def sample_pipeline():
    """Sample training pipeline data for testing."""
    from datetime import datetime
    return {
        "_id": "507f1f77bcf86cd799439021",
        "pipeline_uuid": "pipeline-uuid-123",
        "name": "Twi TTS Training",
        "description": "Training pipeline for Twi TTS model",
        "model_type": "tts",  # Fixed: Changed from task_type to model_type
        "target_version": "1.0.0",  # Fixed: Added required field
        "priority": "medium",  # Fixed: Added required field
        "current_stage": "training",
        "overall_status": "in_progress",
        "overall_progress": 45.0,
        "stages": [
            {
                "stage_name": "data_acquisition",
                "status": "completed",
                "progress_percentage": 100,
                "started_at": datetime.utcnow(),
                "completed_at": datetime.utcnow(),
                "duration_minutes": 30,
                "artifacts": [],
                "metrics": {},
                "logs": []
            },
            {
                "stage_name": "training",
                "status": "in_progress",
                "progress_percentage": 45,
                "started_at": datetime.utcnow(),
                "artifacts": [],
                "metrics": {"loss": 0.25},
                "logs": []
            }
        ],
        "created_by": "507f1f77bcf86cd799439013",
        "team_members": ["507f1f77bcf86cd799439013"],
        "datasets": [],  # Fixed: Added required field
        "experiment_config": None,  # Fixed: Added field
        "tags": [],  # Fixed: Added field
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_dataset_version():
    """Sample dataset version data for testing."""
    from datetime import datetime
    return {
        "_id": "507f1f77bcf86cd799439022",
        "dataset_id": "dataset-uuid-123",
        "version": "1.0.0",
        "storage_path": "datasets/twi/audio/dataset-uuid-123/v1.0.0",
        "manifest_url": "datasets/twi/audio/dataset-uuid-123/v1.0.0/manifest.json",
        "changelog": "Initial release",
        "diff_summary": {
            "files_added": 1000,
            "files_removed": 0,
            "files_modified": 0,
            "size_change_mb": 500.0
        },
        "checksum": "abc123def456",
        "created_by": "507f1f77bcf86cd799439013",
        "created_at": datetime.utcnow(),
        "download_count": 0,
        "file_count": 1000,
        "total_size_mb": 500.0,
        "quality_report": {
            "validation_passed": True,
            "error_count": 0
        }
    }


@pytest.fixture
def sample_external_resource():
    """Sample external resource link data for testing."""
    from datetime import datetime
    return {
        "_id": "507f1f77bcf86cd799439023",
        "link_uuid": "link-uuid-123",
        "title": "Twi Speech Dataset",
        "url": "https://github.com/example/twi-speech",
        "resource_type": "dataset",
        "platform": "github",
        "languages": ["twi"],
        "language_ids": ["507f1f77bcf86cd799439012"],
        "is_multilingual": False,
        "description": "Open source Twi speech dataset",
        "tags": ["speech", "twi", "dataset"],
        "license": "MIT",
        "verification_status": "unverified",
        "is_available": True,
        "submitted_by": "507f1f77bcf86cd799439013",
        "upvotes": 0,
        "downvotes": 0,
        "view_count": 0,
        "click_count": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_file_upload():
    """Sample file upload data for testing."""
    from datetime import datetime
    return {
        "_id": "507f1f77bcf86cd799439024",
        "upload_uuid": "upload-uuid-123",
        "uploaded_by": "507f1f77bcf86cd799439013",
        "upload_type": "dataset",
        "original_filename": "twi_audio.tar.gz",
        "file_type": "audio",
        "mime_type": "application/gzip",
        "file_size_mb": 100.5,
        "storage_path": "user-uploads/507f1f77bcf86cd799439013/upload-uuid-123/twi_audio.tar.gz",
        "access_url": "https://storage.example.com/user-uploads/...",
        "processing_status": "completed",
        "language_code": "twi",
        "language_id": "507f1f77bcf86cd799439012",
        "tags": ["audio", "speech"],
        "description": "Twi audio recordings",
        "license": "CC-BY-4.0",
        "created_at": datetime.utcnow()
    }


@pytest.fixture
def mock_storage_service():
    """Mock Hetzner Storage Service for testing."""
    from unittest.mock import MagicMock
    mock_storage = MagicMock()
    mock_storage.connect = MagicMock()
    mock_storage.disconnect = MagicMock()
    mock_storage.upload_file = MagicMock(return_value={"checksum": "abc123"})
    mock_storage.generate_download_url = MagicMock(return_value="https://download.example.com/file")
    return mock_storage


@pytest.fixture
def admin_user():
    """Sample admin user for testing."""
    return {
        "_id": "507f1f77bcf86cd799439015",
        "supabase_id": "admin-supabase-123",
        "email": "admin@example.com",
        "username": "adminuser",
        "role": "admin",
        "can_validate": True,
        "can_moderate": True,
        "is_active": True
    }


@pytest.fixture
def moderator_user():
    """Sample moderator user for testing."""
    return {
        "_id": "507f1f77bcf86cd799439016",
        "supabase_id": "moderator-supabase-123",
        "email": "moderator@example.com",
        "username": "moderatoruser",
        "role": "moderator",
        "can_validate": True,
        "can_moderate": True,
        "is_active": True
    }