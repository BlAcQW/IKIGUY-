"""
Unit tests for the Hetzner Storage Service integration.

Tests the backward-compatible wrapper around shared HetznerStorageBox.
"""

import os
import sys
import pytest
import tempfile
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# Add paths for imports
sys.path.insert(0, '/opt/kasaai/apps')
sys.path.insert(0, '/opt/kasaai/apps/community/backend')

from services.storage_service import (
    HetznerStorageService,
    get_storage_service,
    get_async_storage
)


class TestHetznerStorageServiceInit:
    """Test HetznerStorageService initialization."""

    def test_init_with_explicit_params(self):
        """Test initialization with explicit parameters."""
        service = HetznerStorageService(
            host="test.storage.de",
            username="testuser",
            password="testpass",
            port=23,
            base_path="/test-path"
        )

        assert service.host == "test.storage.de"
        assert service.username == "testuser"
        assert service.password == "testpass"
        assert service.port == 23
        assert service.base_path == "test-path"

    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        with patch.dict(os.environ, {
            "HETZNER_STORAGE_HOST": "env.storage.de",
            "HETZNER_STORAGE_USERNAME": "envuser",
            "HETZNER_STORAGE_PASSWORD": "envpass"
        }):
            service = HetznerStorageService()

            assert service.host == "env.storage.de"
            assert service.username == "envuser"
            assert service.password == "envpass"

    def test_init_default_values(self):
        """Test initialization with default values."""
        service = HetznerStorageService(password="required")

        assert service.host == "u497034-sub1.your-storagebox.de"
        assert service.username == "u497034-sub1"
        assert service.port == 23
        assert service.base_path == "african-languages"

    def test_get_full_path(self):
        """Test full path generation."""
        service = HetznerStorageService(
            password="test",
            base_path="/african-languages"
        )

        full_path = service._get_full_path("datasets/twi/audio/file.wav")
        assert full_path == "/african-languages/datasets/twi/audio/file.wav"

    def test_get_full_path_strips_leading_slash(self):
        """Test full path strips leading slashes from input."""
        service = HetznerStorageService(
            password="test",
            base_path="african-languages"
        )

        full_path = service._get_full_path("/datasets/file.wav")
        assert full_path == "/african-languages/datasets/file.wav"


class TestHetznerStorageServiceChecksum:
    """Test checksum computation."""

    def test_compute_file_checksum(self):
        """Test SHA256 checksum computation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test content for checksum")
            tmp_path = tmp.name

        try:
            checksum = HetznerStorageService._compute_file_checksum(tmp_path)
            # SHA256 of "test content for checksum"
            assert len(checksum) == 64  # SHA256 produces 64 hex chars
            assert checksum.isalnum()
        finally:
            os.remove(tmp_path)

    def test_checksum_different_content(self):
        """Test different content produces different checksums."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp1:
            tmp1.write(b"content 1")
            path1 = tmp1.name

        with tempfile.NamedTemporaryFile(delete=False) as tmp2:
            tmp2.write(b"content 2")
            path2 = tmp2.name

        try:
            checksum1 = HetznerStorageService._compute_file_checksum(path1)
            checksum2 = HetznerStorageService._compute_file_checksum(path2)
            assert checksum1 != checksum2
        finally:
            os.remove(path1)
            os.remove(path2)


class TestHetznerStorageServiceMetadata:
    """Test metadata serialization."""

    def test_serialize_metadata(self):
        """Test metadata serialization to JSON."""
        metadata = {
            "filename": "test.wav",
            "size": 1024,
            "uploaded_at": datetime(2025, 1, 1, 12, 0, 0)
        }

        serialized = HetznerStorageService._serialize_metadata(metadata)

        assert '"filename": "test.wav"' in serialized
        assert '"size": 1024' in serialized
        # datetime should be converted to string
        assert "2025" in serialized

    def test_deserialize_metadata(self):
        """Test metadata deserialization from JSON."""
        json_str = '{"filename": "test.wav", "size": 1024}'

        metadata = HetznerStorageService._deserialize_metadata(json_str)

        assert metadata["filename"] == "test.wav"
        assert metadata["size"] == 1024


class TestHetznerStorageServiceUpload:
    """Test upload functionality."""

    @pytest.fixture
    def mock_storage(self):
        """Create mock storage instance."""
        with patch('services.storage_service.HetznerStorageBox') as MockStorage:
            mock_instance = MagicMock()
            mock_instance.connected = True
            mock_instance.upload_file = AsyncMock(return_value=True)
            MockStorage.return_value = mock_instance
            yield mock_instance

    def test_upload_from_bytes(self, mock_storage):
        """Test uploading bytes content."""
        service = HetznerStorageService(password="test")
        service._storage = mock_storage

        file_content = b"test audio content"
        result = service.upload_from_bytes(
            file_content=file_content,
            remote_path="datasets/test/audio.wav",
            metadata={"language": "twi"}
        )

        assert result["success"] is True
        assert result["file_size"] == len(file_content)
        assert "checksum" in result
        assert len(result["checksum"]) == 64

    def test_upload_file_handles_bytes_input(self, mock_storage):
        """Test upload_file handles bytes input via backward compatibility."""
        service = HetznerStorageService(password="test")
        service._storage = mock_storage

        file_content = b"test content"
        result = service.upload_file(
            local_file_path_or_bytes=file_content,
            remote_path="test/file.txt"
        )

        assert result["success"] is True
        assert result["file_size"] == len(file_content)


class TestHetznerStorageServiceDownloadUrl:
    """Test download URL generation."""

    def test_generate_download_url(self):
        """Test WebDAV URL generation."""
        service = HetznerStorageService(
            host="test.your-storagebox.de",
            password="test",
            base_path="african-languages"
        )

        url = service.generate_download_url("datasets/twi/file.wav")

        assert "test.your-storagebox.de" in url
        assert "african-languages" in url
        assert "file.wav" in url

    def test_generate_download_url_with_env_webdav(self):
        """Test URL generation with custom HETZNER_WEBDAV_URL."""
        with patch.dict(os.environ, {
            "HETZNER_WEBDAV_URL": "https://custom.webdav.com"
        }):
            service = HetznerStorageService(
                password="test",
                base_path="test-path"
            )

            url = service.generate_download_url("path/to/file.txt")

            assert url.startswith("https://custom.webdav.com")


class TestGetStorageServiceFactory:
    """Test factory function."""

    def test_get_storage_service(self):
        """Test get_storage_service factory."""
        with patch.dict(os.environ, {
            "HETZNER_STORAGE_HOST": "factory.host.de",
            "HETZNER_STORAGE_USERNAME": "factoryuser",
            "HETZNER_STORAGE_PASSWORD": "factorypass",
            "HETZNER_STORAGE_PORT": "23",
            "HETZNER_STORAGE_BASE_PATH": "/factory-path"
        }):
            service = get_storage_service()

            assert service.host == "factory.host.de"
            assert service.username == "factoryuser"
            assert service.base_path == "factory-path"


class TestSharedLibraryIntegration:
    """Test integration with shared library."""

    def test_imports_from_shared(self):
        """Test that shared library imports work."""
        from shared.storage.hetzner_storage_box import (
            HetznerStorageBox,
            StorageProtocol,
            HetznerStorageBoxError
        )

        assert HetznerStorageBox is not None
        assert StorageProtocol.SFTP.value == "sftp"
        assert StorageProtocol.WEBDAV.value == "webdav"

    def test_service_uses_shared_protocol(self):
        """Test service uses shared StorageProtocol enum."""
        from shared.storage.hetzner_storage_box import StorageProtocol

        service = HetznerStorageService(password="test")

        assert service.protocol == StorageProtocol.SFTP


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_base_path_stripped(self):
        """Test base path stripping handles various formats."""
        test_cases = [
            ("/path/", "path"),
            ("path/", "path"),
            ("/path", "path"),
            ("path", "path"),
            ("///path///", "path"),
        ]

        for input_path, expected in test_cases:
            service = HetznerStorageService(
                password="test",
                base_path=input_path
            )
            assert service.base_path == expected, f"Failed for input: {input_path}"

    def test_file_exists_returns_bool(self):
        """Test file_exists returns boolean."""
        with patch('services.storage_service.HetznerStorageBox') as MockStorage:
            mock_instance = MagicMock()
            mock_instance.connected = True
            mock_instance.file_exists = AsyncMock(return_value=True)
            MockStorage.return_value = mock_instance

            service = HetznerStorageService(password="test")
            service._storage = mock_instance

            result = service.file_exists("test/file.txt")

            assert isinstance(result, bool)
            assert result is True


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    def test_upload_file_signature_compatible(self):
        """Test upload_file accepts same parameters as original."""
        # Original signature:
        # upload_file(local_file_path, remote_path, metadata=None, compute_checksum=True)

        with patch('services.storage_service.HetznerStorageBox') as MockStorage:
            mock_instance = MagicMock()
            mock_instance.connected = True
            mock_instance.upload_file = AsyncMock(return_value=True)
            MockStorage.return_value = mock_instance

            service = HetznerStorageService(password="test")
            service._storage = mock_instance

            # Create temp file
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(b"test content")
                tmp_path = tmp.name

            try:
                # Call with original signature
                result = service.upload_file(
                    tmp_path,  # local_file_path
                    "remote/path/file.txt",  # remote_path
                    metadata={"key": "value"},  # metadata
                    compute_checksum=True  # compute_checksum
                )

                assert result["success"] is True
            finally:
                os.remove(tmp_path)

    def test_context_manager_compatible(self):
        """Test context manager interface works."""
        with patch('services.storage_service.HetznerStorageBox') as MockStorage:
            mock_instance = MagicMock()
            mock_instance.connected = False
            mock_instance.connect = AsyncMock()
            mock_instance.disconnect = AsyncMock()
            MockStorage.return_value = mock_instance

            service = HetznerStorageService(password="test")
            service._storage = mock_instance

            # Should work as context manager
            with service as s:
                assert s is service


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
