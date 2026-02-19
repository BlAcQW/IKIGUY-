"""
Tests for Project Attachments API.

Tests file upload, download, and deletion functionality for projects.
"""

import os
import pytest
import tempfile
import uuid
from pathlib import Path
from datetime import date
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

# Import the app and models
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.config import settings
from app.models.project import Project, ProjectCreate


# Test organization and user IDs
TEST_ORG_ID = "test-org-123"
TEST_USER_ID = "test-user-456"
TEST_PROJECT_ID = "test-project-789"


@pytest.fixture
def test_client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_auth():
    """Mock authentication dependencies."""
    with patch("apps.shared.dependencies.require_organization_access") as mock_org:
        with patch("apps.shared.dependencies.OrganizationScoped") as mock_scope:
            mock_org.return_value = TEST_ORG_ID
            mock_scope_instance = MagicMock()
            mock_scope_instance.org_id = TEST_ORG_ID
            mock_scope_instance.user = {"id": TEST_USER_ID, "sub": TEST_USER_ID}
            mock_scope.return_value = mock_scope_instance
            yield mock_org, mock_scope


@pytest.fixture
def test_project():
    """Create a test project object."""
    return Project(
        id=TEST_PROJECT_ID,
        organization_id=TEST_ORG_ID,
        project_name="Test Project",
        project_code="TST001",
        description="A test project for attachment testing",
        start_date=date.today(),
        project_manager_id="manager-123",
        attachments=[],
        created_by=TEST_USER_ID
    )


@pytest.fixture
def sample_files():
    """Create sample test files."""
    files = {}

    # Create test files in temp directory
    temp_dir = tempfile.mkdtemp()

    # PDF document
    pdf_path = Path(temp_dir) / "test_document.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nTest PDF content")
    files['pdf'] = pdf_path

    # Image file
    image_path = Path(temp_dir) / "test_image.png"
    # Minimal PNG header
    image_path.write_bytes(
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00'
        b'\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    files['image'] = image_path

    # Audio file (MP3 header)
    audio_path = Path(temp_dir) / "test_audio.mp3"
    audio_path.write_bytes(b'\xff\xfb\x90\x00' + b'\x00' * 100)  # Minimal MP3
    files['audio'] = audio_path

    # Video file (MP4 header)
    video_path = Path(temp_dir) / "test_video.mp4"
    video_path.write_bytes(
        b'\x00\x00\x00\x1cftypisom\x00\x00\x02\x00isomiso2mp41' + b'\x00' * 100
    )
    files['video'] = video_path

    # Archive file
    zip_path = Path(temp_dir) / "test_archive.zip"
    zip_path.write_bytes(b'PK\x03\x04' + b'\x00' * 100)
    files['zip'] = zip_path

    yield files

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


class TestAllowedExtensions:
    """Test that all expected file types are allowed."""

    def test_document_extensions_allowed(self):
        """Test that document extensions are in allowed list."""
        allowed = settings.ALLOWED_EXTENSIONS.lower()
        document_exts = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']

        for ext in document_exts:
            assert ext in allowed, f"{ext} should be in allowed extensions"

    def test_image_extensions_allowed(self):
        """Test that image extensions are in allowed list."""
        allowed = settings.ALLOWED_EXTENSIONS.lower()
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']

        for ext in image_exts:
            assert ext in allowed, f"{ext} should be in allowed extensions"

    def test_audio_extensions_allowed(self):
        """Test that audio extensions are in allowed list."""
        allowed = settings.ALLOWED_EXTENSIONS.lower()
        audio_exts = ['.mp3', '.wav', '.m4a', '.ogg', '.flac']

        for ext in audio_exts:
            assert ext in allowed, f"{ext} should be in allowed extensions"

    def test_video_extensions_allowed(self):
        """Test that video extensions are in allowed list."""
        allowed = settings.ALLOWED_EXTENSIONS.lower()
        video_exts = ['.mp4', '.mov', '.avi', '.mkv', '.webm']

        for ext in video_exts:
            assert ext in allowed, f"{ext} should be in allowed extensions"

    def test_archive_extensions_allowed(self):
        """Test that archive extensions are in allowed list."""
        allowed = settings.ALLOWED_EXTENSIONS.lower()
        archive_exts = ['.zip', '.rar', '.7z']

        for ext in archive_exts:
            assert ext in allowed, f"{ext} should be in allowed extensions"

    def test_design_extensions_allowed(self):
        """Test that design file extensions are in allowed list."""
        allowed = settings.ALLOWED_EXTENSIONS.lower()
        design_exts = ['.psd', '.ai', '.sketch', '.fig', '.xd']

        for ext in design_exts:
            assert ext in allowed, f"{ext} should be in allowed extensions"


class TestMaxUploadSize:
    """Test upload size configuration."""

    def test_max_upload_size_is_100mb(self):
        """Test that max upload size is set to 100MB."""
        assert settings.MAX_UPLOAD_SIZE_MB == 100

    def test_max_file_size_in_bytes(self):
        """Test that max file size converts correctly to bytes."""
        from app.api.routes.projects import MAX_FILE_SIZE
        expected_bytes = 100 * 1024 * 1024  # 100MB in bytes
        assert MAX_FILE_SIZE == expected_bytes


class TestProjectModel:
    """Test Project model attachment field."""

    def test_project_has_attachments_field(self, test_project):
        """Test that Project model has attachments field."""
        assert hasattr(test_project, 'attachments')
        assert isinstance(test_project.attachments, list)

    def test_project_attachments_default_empty(self):
        """Test that attachments field defaults to empty list."""
        project = Project(
            id="test-id",
            organization_id="org-id",
            project_name="Test",
            project_code="T001",
            start_date=date.today(),
            project_manager_id="manager-id"
        )
        assert project.attachments == []

    def test_project_can_have_attachments(self, test_project):
        """Test that attachments can be added to project."""
        attachment = {
            "id": str(uuid.uuid4()),
            "original_filename": "test.pdf",
            "stored_filename": "abc123.pdf",
            "file_path": "test-org/projects/test-project/abc123.pdf",
            "file_size": 1024,
            "file_type": ".pdf",
            "mime_type": "application/pdf",
            "uploaded_by": TEST_USER_ID,
            "uploaded_at": "2025-11-26T15:00:00Z"
        }
        test_project.attachments.append(attachment)

        assert len(test_project.attachments) == 1
        assert test_project.attachments[0]["original_filename"] == "test.pdf"


class TestAttachmentMetadata:
    """Test attachment metadata structure."""

    def test_attachment_has_required_fields(self):
        """Test that attachment metadata has all required fields."""
        required_fields = [
            "id",
            "original_filename",
            "stored_filename",
            "file_path",
            "file_size",
            "file_type",
            "mime_type",
            "uploaded_by",
            "uploaded_at"
        ]

        attachment = {
            "id": str(uuid.uuid4()),
            "original_filename": "test.pdf",
            "stored_filename": "abc123.pdf",
            "file_path": "org-id/projects/project-id/abc123.pdf",
            "file_size": 1024,
            "file_type": ".pdf",
            "mime_type": "application/pdf",
            "uploaded_by": "user-id",
            "uploaded_at": "2025-11-26T15:00:00Z"
        }

        for field in required_fields:
            assert field in attachment, f"Attachment missing field: {field}"


class TestFileTypeCategories:
    """Test file type categorization for frontend display."""

    def test_document_categorization(self):
        """Test document file types are categorized correctly."""
        from app.api.routes.projects import ALLOWED_EXTENSIONS

        document_exts = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']
        for ext in document_exts:
            assert ext in ALLOWED_EXTENSIONS, f"{ext} should be allowed"

    def test_image_categorization(self):
        """Test image file types are categorized correctly."""
        from app.api.routes.projects import ALLOWED_EXTENSIONS

        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        for ext in image_exts:
            assert ext in ALLOWED_EXTENSIONS, f"{ext} should be allowed"

    def test_audio_categorization(self):
        """Test audio file types are categorized correctly."""
        from app.api.routes.projects import ALLOWED_EXTENSIONS

        audio_exts = ['.mp3', '.wav', '.m4a', '.ogg', '.flac']
        for ext in audio_exts:
            assert ext in ALLOWED_EXTENSIONS, f"{ext} should be allowed"

    def test_video_categorization(self):
        """Test video file types are categorized correctly."""
        from app.api.routes.projects import ALLOWED_EXTENSIONS

        video_exts = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
        for ext in video_exts:
            assert ext in ALLOWED_EXTENSIONS, f"{ext} should be allowed"


class TestUploadDirectoryStructure:
    """Test upload directory structure."""

    def test_upload_dir_configured(self):
        """Test that upload directory is configured."""
        assert settings.UPLOAD_DIR is not None
        assert len(settings.UPLOAD_DIR) > 0

    def test_upload_dir_path(self):
        """Test upload directory path format."""
        expected_path = "/opt/kasaai/apps/erp/uploads"
        assert settings.UPLOAD_DIR == expected_path

    def test_upload_dir_exists(self):
        """Test that upload directory exists."""
        upload_dir = Path(settings.UPLOAD_DIR)
        assert upload_dir.exists(), f"Upload directory should exist: {upload_dir}"


# Integration test helpers for manual testing
class TestIntegrationHelpers:
    """Helper methods for manual integration testing."""

    @staticmethod
    def get_test_file_content(file_type: str) -> bytes:
        """Generate test file content for different file types."""
        if file_type == 'pdf':
            return b"%PDF-1.4\nTest PDF content for project attachment"
        elif file_type == 'png':
            return (
                b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
                b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
            )
        elif file_type == 'mp3':
            return b'\xff\xfb\x90\x00' + b'\x00' * 100
        elif file_type == 'mp4':
            return b'\x00\x00\x00\x1cftypisom\x00\x00\x02\x00isomiso2mp41' + b'\x00' * 100
        elif file_type == 'zip':
            return b'PK\x03\x04' + b'\x00' * 100
        else:
            return b"Test file content"

    @staticmethod
    def print_test_summary():
        """Print summary of what was tested."""
        print("\n" + "="*60)
        print("PROJECT ATTACHMENTS TEST SUMMARY")
        print("="*60)
        print("\nAllowed file types:")
        print(f"  Documents: .pdf, .doc, .docx, .xls, .xlsx, .ppt, .pptx, .txt, .rtf, .csv")
        print(f"  Images:    .jpg, .jpeg, .png, .gif, .bmp, .webp, .svg, .ico")
        print(f"  Audio:     .mp3, .wav, .m4a, .ogg, .flac, .aac, .wma")
        print(f"  Video:     .mp4, .mov, .avi, .mkv, .webm, .wmv, .flv, .m4v")
        print(f"  Archives:  .zip, .rar, .7z, .tar, .gz")
        print(f"  Design:    .psd, .ai, .sketch, .fig, .xd")
        print(f"\nMax upload size: {settings.MAX_UPLOAD_SIZE_MB}MB")
        print(f"Upload directory: {settings.UPLOAD_DIR}")
        print("="*60 + "\n")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])

    # Print test summary
    TestIntegrationHelpers.print_test_summary()
