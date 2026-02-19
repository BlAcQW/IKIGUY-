"""
Unit tests for the Community Drive Service.

Tests file management functionality including:
- File upload, download, delete, rename
- Folder management
- Search functionality
- Permissions and sharing
- Statistics
"""

import os
import sys
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import uuid

# Add paths for imports
sys.path.insert(0, '/opt/kasaai/apps')
sys.path.insert(0, '/opt/kasaai/apps/community/backend')

from services.drive_service import (
    CommunityDriveService,
    CommunityDriveError,
    FileNotFoundError as DriveFileNotFoundError,
    PermissionDeniedError,
    get_community_drive_service
)


class TestCommunityDriveServiceInit:
    """Test CommunityDriveService initialization."""

    def test_init_with_db(self):
        """Test initialization with database."""
        mock_db = MagicMock()
        mock_db.drive_items = MagicMock()

        service = CommunityDriveService(db=mock_db)

        assert service.db == mock_db
        assert service.collection == mock_db.drive_items
        assert service.base_path == "african-languages"

    def test_init_with_custom_base_path(self):
        """Test initialization with custom base path."""
        mock_db = MagicMock()

        service = CommunityDriveService(
            db=mock_db,
            base_path="custom-path"
        )

        assert service.base_path == "custom-path"


class TestFilenamesSanitization:
    """Test filename sanitization."""

    def test_sanitize_basic_filename(self):
        """Test sanitizing a basic filename."""
        mock_db = MagicMock()
        service = CommunityDriveService(db=mock_db)

        result = service._sanitize_filename("test_file.wav")
        assert result == "test_file.wav"

    def test_sanitize_dangerous_chars(self):
        """Test sanitizing dangerous characters."""
        mock_db = MagicMock()
        service = CommunityDriveService(db=mock_db)

        result = service._sanitize_filename("test/file<>.wav")
        assert "/" not in result
        assert "<" not in result
        assert ">" not in result

    def test_sanitize_path_traversal(self):
        """Test sanitizing path traversal attempts."""
        mock_db = MagicMock()
        service = CommunityDriveService(db=mock_db)

        result = service._sanitize_filename("../../../etc/passwd")
        assert ".." not in result


class TestStoragePathGeneration:
    """Test storage path generation."""

    def test_generate_storage_path(self):
        """Test file storage path generation."""
        mock_db = MagicMock()
        service = CommunityDriveService(db=mock_db)

        path = service._generate_storage_path(
            file_id="abc123",
            filename="test.wav",
            language_code="twi",
            category="audio",
            owner_id="user456"
        )

        assert "audio" in path
        assert "twi" in path
        assert "user456" in path
        assert "abc123" in path
        assert "test.wav" in path

    def test_generate_folder_path(self):
        """Test folder storage path generation."""
        mock_db = MagicMock()
        service = CommunityDriveService(db=mock_db)

        path = service._generate_folder_path(
            folder_id="folder123",
            name="My Folder",
            language_code="yo",
            category="text"
        )

        assert "text" in path
        assert "yo" in path
        assert "folder123" in path


class TestPermissionChecks:
    """Test permission checking."""

    @pytest.mark.asyncio
    async def test_owner_has_all_permissions(self):
        """Test that owner has all permissions."""
        mock_db = MagicMock()
        service = CommunityDriveService(db=mock_db)

        item_doc = {
            "owner_id": "user123",
            "is_public": False,
            "permissions": []
        }

        assert await service._check_permission(item_doc, "user123", "view")
        assert await service._check_permission(item_doc, "user123", "edit")
        assert await service._check_permission(item_doc, "user123", "manage")

    @pytest.mark.asyncio
    async def test_public_files_viewable(self):
        """Test that public files can be viewed by anyone."""
        mock_db = MagicMock()
        service = CommunityDriveService(db=mock_db)

        item_doc = {
            "owner_id": "user123",
            "is_public": True,
            "permissions": []
        }

        assert await service._check_permission(item_doc, "other_user", "view")
        assert not await service._check_permission(item_doc, "other_user", "edit")

    @pytest.mark.asyncio
    async def test_explicit_permissions(self):
        """Test explicit permission grants."""
        mock_db = MagicMock()
        service = CommunityDriveService(db=mock_db)

        item_doc = {
            "owner_id": "user123",
            "is_public": False,
            "permissions": [
                {"user_id": "user456", "role": "edit"}
            ]
        }

        assert await service._check_permission(item_doc, "user456", "view")
        assert await service._check_permission(item_doc, "user456", "edit")
        assert not await service._check_permission(item_doc, "user456", "manage")


class TestFormatItem:
    """Test item formatting for API response."""

    def test_format_item_basic(self):
        """Test basic item formatting."""
        mock_db = MagicMock()
        service = CommunityDriveService(db=mock_db)

        item_doc = {
            "_id": "file123",
            "name": "test.wav",
            "type": "file",
            "path": "/audio/twi/test.wav",
            "parent_id": None,
            "language_code": "twi",
            "category": "audio",
            "size": 1024,
            "mime_type": "audio/wav",
            "created_at": datetime(2025, 1, 1, 12, 0, 0),
            "modified_at": datetime(2025, 1, 1, 12, 0, 0),
            "owner_id": "user123",
            "is_starred": False,
            "is_public": True,
            "is_deleted": False,
            "permissions": [],
            "tags": ["sample"],
            "download_count": 5,
            "view_count": 10
        }

        result = service._format_item(item_doc)

        assert result["id"] == "file123"
        assert result["name"] == "test.wav"
        assert result["type"] == "file"
        assert result["language_code"] == "twi"
        assert result["size"] == 1024
        assert result["download_count"] == 5
        assert result["is_public"] is True


class TestFileUpload:
    """Test file upload functionality."""

    @pytest.mark.asyncio
    async def test_upload_validates_file_size(self):
        """Test that upload validates file size."""
        mock_db = MagicMock()
        mock_db.drive_items = MagicMock()
        mock_db.drive_items.insert_one = AsyncMock()

        # Create mock storage
        mock_storage = MagicMock()
        mock_storage.upload_file = AsyncMock()

        service = CommunityDriveService(db=mock_db, storage=mock_storage)

        # Create content larger than audio max size (100MB)
        audio_content = b"x" * (150 * 1024 * 1024)  # 150MB > 100MB limit

        with pytest.raises(CommunityDriveError) as exc_info:
            await service.upload_file(
                file_content=audio_content,
                filename="large_audio.wav",
                owner_id="user123",
                language_code="twi",
                category="audio"
            )

        assert "exceeds" in str(exc_info.value).lower()


class TestFileCategories:
    """Test file category validation."""

    def test_supported_categories(self):
        """Test that supported categories are defined."""
        assert "audio" in CommunityDriveService.SUPPORTED_CATEGORIES
        assert "text" in CommunityDriveService.SUPPORTED_CATEGORIES
        assert "model" in CommunityDriveService.SUPPORTED_CATEGORIES
        assert "notebook" in CommunityDriveService.SUPPORTED_CATEGORIES

    def test_max_file_sizes_defined(self):
        """Test that max file sizes are defined for categories."""
        assert "audio" in CommunityDriveService.MAX_FILE_SIZES
        assert "text" in CommunityDriveService.MAX_FILE_SIZES
        assert "model" in CommunityDriveService.MAX_FILE_SIZES
        assert CommunityDriveService.MAX_FILE_SIZES["audio"] <= 100 * 1024 * 1024


class TestSearchFunctionality:
    """Test search functionality."""

    @pytest.mark.asyncio
    async def test_search_builds_correct_query(self):
        """Test that search builds correct MongoDB query."""
        mock_db = MagicMock()

        # Create proper async mock cursor
        mock_cursor = MagicMock()
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[])

        mock_db.drive_items.find = MagicMock(return_value=mock_cursor)
        mock_db.drive_items.count_documents = AsyncMock(return_value=0)

        service = CommunityDriveService(db=mock_db)

        await service.search_files(
            query="test audio",
            user_id="user123",
            language_code="twi",
            category="audio"
        )

        # Verify find was called
        mock_db.drive_items.find.assert_called_once()

        # Get the query that was passed
        call_args = mock_db.drive_items.find.call_args
        query = call_args[0][0]

        assert query.get("language_code") == "twi"
        assert query.get("category") == "audio"
        assert query.get("is_deleted") is False


class TestStatistics:
    """Test statistics functionality."""

    @pytest.mark.asyncio
    async def test_get_storage_stats(self):
        """Test storage statistics aggregation."""
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=[
            {"_id": "audio", "count": 10, "total_size": 1024000, "total_downloads": 50},
            {"_id": "text", "count": 5, "total_size": 10240, "total_downloads": 20}
        ])
        mock_db.drive_items.aggregate = MagicMock(return_value=mock_cursor)

        service = CommunityDriveService(db=mock_db)

        stats = await service.get_storage_stats()

        assert stats["total_files"] == 15
        assert stats["total_size_bytes"] == 1034240
        assert stats["total_downloads"] == 70
        assert "audio" in stats["by_category"]
        assert "text" in stats["by_category"]


class TestFileDownload:
    """Test file download functionality."""

    @pytest.mark.asyncio
    async def test_download_requires_permission(self):
        """Test that download checks permissions."""
        mock_db = MagicMock()

        # File owned by different user, not public
        file_doc = {
            "_id": "file123",
            "name": "private.wav",
            "path": "/audio/private.wav",
            "mime_type": "audio/wav",
            "owner_id": "other_user",
            "is_public": False,
            "is_deleted": False,
            "permissions": []
        }

        mock_db.drive_items.find_one = AsyncMock(return_value=file_doc)

        service = CommunityDriveService(db=mock_db)

        with pytest.raises(PermissionDeniedError):
            await service.download_file(
                file_id="file123",
                user_id="user123"
            )


class TestFolderCreation:
    """Test folder creation functionality."""

    @pytest.mark.asyncio
    async def test_create_folder_generates_id(self):
        """Test that folder creation generates unique ID."""
        mock_db = MagicMock()
        mock_db.drive_items.find_one = AsyncMock(return_value=None)
        mock_db.drive_items.insert_one = AsyncMock()

        mock_storage = MagicMock()
        mock_storage.create_directory = AsyncMock()

        service = CommunityDriveService(db=mock_db, storage=mock_storage)

        result = await service.create_folder(
            name="Test Folder",
            owner_id="user123",
            language_code="twi",
            category="audio"
        )

        assert result["id"] is not None
        assert result["name"] == "Test Folder"
        assert result["type"] == "folder"
        assert result["language_code"] == "twi"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
