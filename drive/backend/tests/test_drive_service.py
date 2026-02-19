"""
Unit tests for Drive Service.

Tests all file and folder operations, permissions, sharing, and search functionality.

Author: AI Labs Africa
Date: 2025-11-10
"""

import pytest
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from apps.shared.services.drive_service import (
    DriveService,
    FileNotFoundError,
    PermissionDeniedError,
    get_drive_service
)


# Test configuration
TEST_MONGODB_URL = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/?authSource=admin"
TEST_DB_NAME = "kasaai_drive_test"
TEST_ORG_ID = "test_org_123"
TEST_USER_ID = "test_user_456"
TEST_USER_ID_2 = "test_user_789"


@pytest.fixture
async def db():
    """Create test database connection."""
    client = AsyncIOMotorClient(TEST_MONGODB_URL)
    database = client[TEST_DB_NAME]

    yield database

    # Cleanup: drop test database after tests
    await client.drop_database(TEST_DB_NAME)
    client.close()


@pytest.fixture
async def drive_service(db):
    """Create drive service instance."""
    service = DriveService(db, organization_id=TEST_ORG_ID)
    await service.initialize()
    return service


# ==================== FILE UPLOAD TESTS ====================

@pytest.mark.asyncio
async def test_upload_file_success(drive_service):
    """Test successful file upload."""
    file_content = b"Test file content"
    filename = "test_document.pdf"

    result = await drive_service.upload_file(
        file_content=file_content,
        filename=filename,
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    assert result["name"] == filename
    assert result["type"] == "file"
    assert result["size"] == len(file_content)
    assert result["owner_id"] == TEST_USER_ID
    assert result["organization_id"] == TEST_ORG_ID
    assert result["parent_id"] is None
    assert result["is_deleted"] is False


@pytest.mark.asyncio
async def test_upload_file_in_folder(drive_service):
    """Test file upload inside a folder."""
    # Create folder first
    folder = await drive_service.create_folder(
        name="Test Folder",
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    # Upload file in folder
    file_content = b"Test content"
    result = await drive_service.upload_file(
        file_content=file_content,
        filename="nested_file.txt",
        parent_id=folder["id"],
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    assert result["parent_id"] == folder["id"]


@pytest.mark.asyncio
async def test_upload_file_sanitizes_filename(drive_service):
    """Test that dangerous characters in filename are sanitized."""
    file_content = b"Test"
    dangerous_filename = "test<>file:name?.pdf"

    result = await drive_service.upload_file(
        file_content=file_content,
        filename=dangerous_filename,
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    # Dangerous characters should be replaced
    assert "<" not in result["name"]
    assert ">" not in result["name"]
    assert ":" not in result["name"]
    assert "?" not in result["name"]


# ==================== FILE DOWNLOAD TESTS ====================

@pytest.mark.asyncio
async def test_download_file_success(drive_service):
    """Test successful file download."""
    # Upload file first
    file_content = b"Download test content"
    upload_result = await drive_service.upload_file(
        file_content=file_content,
        filename="download_test.txt",
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    # Download file
    content, filename, mime_type = await drive_service.download_file(
        file_id=upload_result["id"],
        user_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    assert content == file_content
    assert filename == "download_test.txt"


@pytest.mark.asyncio
async def test_download_file_not_found(drive_service):
    """Test download of non-existent file."""
    with pytest.raises(FileNotFoundError):
        await drive_service.download_file(
            file_id="nonexistent_id",
            user_id=TEST_USER_ID,
            organization_id=TEST_ORG_ID
        )


@pytest.mark.asyncio
async def test_download_file_permission_denied(drive_service):
    """Test download without permission."""
    # Upload file as user 1
    file_content = b"Private content"
    upload_result = await drive_service.upload_file(
        file_content=file_content,
        filename="private.txt",
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    # Try to download as user 2 (should fail)
    with pytest.raises(PermissionDeniedError):
        await drive_service.download_file(
            file_id=upload_result["id"],
            user_id=TEST_USER_ID_2,
            organization_id=TEST_ORG_ID
        )


# ==================== FILE DELETE TESTS ====================

@pytest.mark.asyncio
async def test_delete_file_soft_delete(drive_service):
    """Test soft delete (move to trash)."""
    # Upload file
    file_content = b"Delete me"
    upload_result = await drive_service.upload_file(
        file_content=file_content,
        filename="trash_me.txt",
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    # Soft delete
    delete_result = await drive_service.delete_file(
        file_id=upload_result["id"],
        user_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID,
        permanent=False
    )

    assert delete_result["status"] == "trashed"

    # File should still exist in database but marked as deleted
    file_info = await drive_service.collection.find_one({"_id": upload_result["id"]})
    assert file_info["is_deleted"] is True


@pytest.mark.asyncio
async def test_delete_file_permanent(drive_service):
    """Test permanent delete."""
    # Upload file
    file_content = b"Permanent delete"
    upload_result = await drive_service.upload_file(
        file_content=file_content,
        filename="permanent_delete.txt",
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    # Permanent delete
    delete_result = await drive_service.delete_file(
        file_id=upload_result["id"],
        user_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID,
        permanent=True
    )

    assert delete_result["status"] == "permanently_deleted"

    # File should not exist in database
    file_info = await drive_service.collection.find_one({"_id": upload_result["id"]})
    assert file_info is None


# ==================== FILE RENAME TESTS ====================

@pytest.mark.asyncio
async def test_rename_file_success(drive_service):
    """Test successful file rename."""
    # Upload file
    file_content = b"Rename test"
    upload_result = await drive_service.upload_file(
        file_content=file_content,
        filename="old_name.txt",
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    # Rename file
    new_name = "new_name.txt"
    rename_result = await drive_service.rename_file(
        file_id=upload_result["id"],
        new_name=new_name,
        user_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    assert rename_result["name"] == new_name


# ==================== FILE MOVE TESTS ====================

@pytest.mark.asyncio
async def test_move_file_to_folder(drive_service):
    """Test moving file to a different folder."""
    # Create folders
    folder1 = await drive_service.create_folder(
        name="Folder1",
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    folder2 = await drive_service.create_folder(
        name="Folder2",
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    # Upload file in folder1
    file_content = b"Move test"
    upload_result = await drive_service.upload_file(
        file_content=file_content,
        filename="move_me.txt",
        parent_id=folder1["id"],
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    # Move to folder2
    move_result = await drive_service.move_file(
        file_id=upload_result["id"],
        new_parent_id=folder2["id"],
        user_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    assert move_result["parent_id"] == folder2["id"]


# ==================== FOLDER TESTS ====================

@pytest.mark.asyncio
async def test_create_folder_success(drive_service):
    """Test successful folder creation."""
    folder = await drive_service.create_folder(
        name="Test Folder",
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    assert folder["name"] == "Test Folder"
    assert folder["type"] == "folder"
    assert folder["owner_id"] == TEST_USER_ID


@pytest.mark.asyncio
async def test_create_nested_folder(drive_service):
    """Test creating nested folders."""
    # Create parent folder
    parent = await drive_service.create_folder(
        name="Parent",
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    # Create child folder
    child = await drive_service.create_folder(
        name="Child",
        parent_id=parent["id"],
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    assert child["parent_id"] == parent["id"]


@pytest.mark.asyncio
async def test_get_folder_contents(drive_service):
    """Test getting folder contents."""
    # Create folder
    folder = await drive_service.create_folder(
        name="Test Folder",
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    # Add files to folder
    for i in range(3):
        await drive_service.upload_file(
            file_content=f"Content {i}".encode(),
            filename=f"file_{i}.txt",
            parent_id=folder["id"],
            owner_id=TEST_USER_ID,
            organization_id=TEST_ORG_ID
        )

    # Get folder contents
    contents = await drive_service.get_folder_contents(
        folder_id=folder["id"],
        user_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    assert len(contents["items"]) == 3
    assert contents["total"] == 3


@pytest.mark.asyncio
async def test_get_breadcrumbs(drive_service):
    """Test breadcrumb trail generation."""
    # Create nested folders
    parent = await drive_service.create_folder(
        name="Parent",
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    child = await drive_service.create_folder(
        name="Child",
        parent_id=parent["id"],
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    # Get breadcrumbs
    breadcrumbs = await drive_service.get_breadcrumbs(
        folder_id=child["id"],
        organization_id=TEST_ORG_ID
    )

    assert len(breadcrumbs) == 3  # Root, Parent, Child
    assert breadcrumbs[0]["name"] == "My Drive"
    assert breadcrumbs[1]["name"] == "Parent"
    assert breadcrumbs[2]["name"] == "Child"


# ==================== SEARCH TESTS ====================

@pytest.mark.asyncio
async def test_search_files(drive_service):
    """Test file search functionality."""
    # Upload files with different names
    await drive_service.upload_file(
        file_content=b"Report content",
        filename="monthly_report.pdf",
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    await drive_service.upload_file(
        file_content=b"Invoice content",
        filename="invoice_2025.pdf",
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    # Search for "report"
    results = await drive_service.search_files(
        query="report",
        user_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    assert len(results["items"]) >= 1
    assert any("report" in item["name"].lower() for item in results["items"])


@pytest.mark.asyncio
async def test_get_recent_files(drive_service):
    """Test getting recent files."""
    # Upload files
    for i in range(5):
        await drive_service.upload_file(
            file_content=f"Content {i}".encode(),
            filename=f"recent_{i}.txt",
            parent_id=None,
            owner_id=TEST_USER_ID,
            organization_id=TEST_ORG_ID
        )

    # Get recent files
    recent = await drive_service.get_recent_files(
        user_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID,
        limit=3
    )

    assert len(recent) == 3


@pytest.mark.asyncio
async def test_toggle_star(drive_service):
    """Test starring/unstarring files."""
    # Upload file
    upload_result = await drive_service.upload_file(
        file_content=b"Star me",
        filename="star_test.txt",
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    # Star the file
    star_result = await drive_service.toggle_star(
        item_id=upload_result["id"],
        user_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    assert star_result["is_starred"] is True

    # Unstar the file
    unstar_result = await drive_service.toggle_star(
        item_id=upload_result["id"],
        user_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    assert unstar_result["is_starred"] is False


# ==================== SHARING TESTS ====================

@pytest.mark.asyncio
async def test_share_with_user(drive_service):
    """Test sharing file with another user."""
    # Upload file
    upload_result = await drive_service.upload_file(
        file_content=b"Shared content",
        filename="shared.txt",
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    # Share with user 2
    share_result = await drive_service.share_item(
        item_id=upload_result["id"],
        user_id=TEST_USER_ID,
        target_user_id=TEST_USER_ID_2,
        role="view",
        organization_id=TEST_ORG_ID
    )

    assert len(share_result["permissions"]) == 1
    assert share_result["permissions"][0]["user_id"] == TEST_USER_ID_2
    assert share_result["permissions"][0]["role"] == "view"


@pytest.mark.asyncio
async def test_create_share_link(drive_service):
    """Test creating public share link."""
    # Upload file
    upload_result = await drive_service.upload_file(
        file_content=b"Public content",
        filename="public.txt",
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    # Create share link
    link_result = await drive_service.create_share_link(
        item_id=upload_result["id"],
        user_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID,
        expires_in_days=7,
        is_public=True
    )

    assert link_result["share_token"] is not None
    assert link_result["is_public"] is True


@pytest.mark.asyncio
async def test_revoke_share_link(drive_service):
    """Test revoking share link."""
    # Upload file and create share link
    upload_result = await drive_service.upload_file(
        file_content=b"Content",
        filename="revoke_test.txt",
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    await drive_service.create_share_link(
        item_id=upload_result["id"],
        user_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    # Revoke link
    revoke_result = await drive_service.revoke_share_link(
        item_id=upload_result["id"],
        user_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    assert revoke_result["status"] == "revoked"


# ==================== PERMISSION TESTS ====================

@pytest.mark.asyncio
async def test_owner_has_all_permissions(drive_service):
    """Test that file owner has all permissions."""
    # Upload file
    upload_result = await drive_service.upload_file(
        file_content=b"Owner test",
        filename="owner_test.txt",
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    # Owner should be able to download
    content, _, _ = await drive_service.download_file(
        file_id=upload_result["id"],
        user_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    assert content == b"Owner test"

    # Owner should be able to delete
    await drive_service.delete_file(
        file_id=upload_result["id"],
        user_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )


# ==================== EDGE CASES ====================

@pytest.mark.asyncio
async def test_upload_empty_file(drive_service):
    """Test uploading empty file."""
    result = await drive_service.upload_file(
        file_content=b"",
        filename="empty.txt",
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    assert result["size"] == 0


@pytest.mark.asyncio
async def test_create_folder_with_same_name(drive_service):
    """Test creating folders with duplicate names (should succeed)."""
    await drive_service.create_folder(
        name="Duplicate",
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    # Creating another folder with same name should succeed
    result = await drive_service.create_folder(
        name="Duplicate",
        parent_id=None,
        owner_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID
    )

    assert result["name"] == "Duplicate"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
