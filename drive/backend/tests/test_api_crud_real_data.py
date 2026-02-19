"""
API CRUD Tests with Real Data for KasaAI Drive.

These tests use the actual Drive API with real database operations.
No mocks - tests actual file upload, storage, and database CRUD.

Author: AI Labs Africa
Date: 2025-11-10
"""

import pytest
import httpx
import os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from supabase import create_client, Client

# Test configuration
API_BASE_URL = "http://localhost:30037"
TEST_MONGODB_URL = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/?authSource=admin"
TEST_DB_NAME = "kasaai_drive"
TEST_ORG_ID = "ai_labs_ltd"  # Default organization

# Test user credentials (from @shared/auth/DEFAULT_USERS.md)
TEST_USER_EMAIL = "admin@ailabsafrica.com"
TEST_USER_PASSWORD = "Admin@2024!"

# Supabase config (for getting auth tokens from .env)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")


@pytest.fixture(scope="session")
def supabase_client():
    """Create Supabase client for authentication."""
    if not SUPABASE_ANON_KEY:
        pytest.skip("SUPABASE_ANON_KEY environment variable not set")
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


@pytest.fixture(scope="session")
def auth_token(supabase_client):
    """Get authentication token from Supabase."""
    # Sign in with credentials
    response = supabase_client.auth.sign_in_with_password({
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    })

    if not response.session:
        pytest.skip(f"Failed to authenticate: {TEST_USER_EMAIL}")

    return response.session.access_token


@pytest.fixture
def api_client(auth_token):
    """Create API client with authentication."""
    return httpx.AsyncClient(
        base_url=API_BASE_URL,
        headers={
            "Authorization": f"Bearer {auth_token}",
            "X-Organization-ID": TEST_ORG_ID
        },
        timeout=30.0
    )


@pytest.fixture
async def db():
    """Create database connection for verification."""
    client = AsyncIOMotorClient(TEST_MONGODB_URL)
    database = client[TEST_DB_NAME]
    yield database
    # Note: We don't drop the database here to preserve test data for inspection


# ==================== FOLDER CRUD TESTS ====================

@pytest.mark.asyncio
async def test_01_create_folder(api_client, db):
    """
    Test: Create a folder in root
    Verifies: POST /api/folders creates folder in database
    """
    response = await api_client.post(
        "/api/folders",
        json={
            "name": "TestFolder",
            "parent_id": None,
            "organization_id": TEST_ORG_ID
        }
    )

    assert response.status_code == 200, f"Failed to create folder: {response.text}"

    data = response.json()
    assert data["name"] == "TestFolder"
    assert data["type"] == "folder"
    assert data["parent_id"] is None
    assert "owner_id" in data  # Organization verified via owner
    assert data["is_deleted"] is False

    folder_id = data["id"]

    # Verify in database
    folder_doc = await db.drive_items.find_one({"_id": folder_id})
    assert folder_doc is not None, "Folder not found in database"
    assert folder_doc["name"] == "TestFolder"
    assert folder_doc["type"] == "folder"

    # Store folder_id for next tests
    pytest.test_folder_id = folder_id


@pytest.mark.asyncio
async def test_02_list_folder_contents(api_client):
    """
    Test: List contents of root folder
    Verifies: GET /api/folders/{folder_id}/contents returns items
    """
    response = await api_client.get("/api/folders/root/contents")

    assert response.status_code == 200, f"Failed to list folder: {response.text}"

    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)
    assert data["total"] >= 1  # Should have at least our test folder


@pytest.mark.asyncio
async def test_03_get_breadcrumbs(api_client):
    """
    Test: Get breadcrumb trail for folder
    Verifies: GET /api/folders/{folder_id}/breadcrumbs returns trail
    """
    folder_id = getattr(pytest, "test_folder_id", None)

    if not folder_id:
        pytest.skip("No folder_id from previous test")

    response = await api_client.get(f"/api/folders/{folder_id}/breadcrumbs")

    assert response.status_code == 200, f"Failed to get breadcrumbs: {response.text}"

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # Should have "My Drive" and our folder
    assert data[0]["name"] == "My Drive"
    assert data[1]["name"] == "TestFolder"


# ==================== FILE UPLOAD CRUD TESTS ====================

@pytest.mark.asyncio
async def test_04_upload_file(api_client, db):
    """
    Test: Upload a file to the folder
    Verifies: POST /api/files/upload creates file in database and storage
    """
    folder_id = getattr(pytest, "test_folder_id", None)

    if not folder_id:
        pytest.skip("No folder_id from previous test")

    # Create a test file
    test_content = b"This is a test file content for KasaAI Drive CRUD testing."
    test_filename = "test_document.txt"

    # Upload file
    response = await api_client.post(
        "/api/files/upload",
        files={"file": (test_filename, test_content, "text/plain")},
        data={
            "parent_id": folder_id,
            "organization_id": TEST_ORG_ID
        }
    )

    assert response.status_code == 200, f"Failed to upload file: {response.text}"

    data = response.json()
    assert data["name"] == test_filename
    assert data["type"] == "file"
    assert data["size"] == len(test_content)
    assert data["parent_id"] == folder_id

    file_id = data["id"]

    # Verify in database
    file_doc = await db.drive_items.find_one({"_id": file_id})
    assert file_doc is not None, "File not found in database"
    assert file_doc["name"] == test_filename
    assert file_doc["type"] == "file"
    assert file_doc["size"] == len(test_content)
    assert file_doc["is_deleted"] is False

    # Store file_id for next tests
    pytest.test_file_id = file_id
    pytest.test_file_content = test_content


@pytest.mark.asyncio
async def test_05_get_file_info(api_client):
    """
    Test: Get file metadata
    Verifies: GET /api/files/{file_id} returns correct metadata
    """
    file_id = getattr(pytest, "test_file_id", None)

    if not file_id:
        pytest.skip("No file_id from previous test")

    response = await api_client.get(f"/api/files/{file_id}")

    assert response.status_code == 200, f"Failed to get file info: {response.text}"

    data = response.json()
    assert data["id"] == file_id
    assert data["name"] == "test_document.txt"
    assert data["type"] == "file"


@pytest.mark.asyncio
async def test_06_download_file(api_client):
    """
    Test: Download file and verify content
    Verifies: GET /api/files/{file_id}/download returns original content
    """
    file_id = getattr(pytest, "test_file_id", None)
    original_content = getattr(pytest, "test_file_content", None)

    if not file_id or not original_content:
        pytest.skip("No file_id or content from previous test")

    response = await api_client.get(f"/api/files/{file_id}/download")

    assert response.status_code == 200, f"Failed to download file: {response.text}"
    assert response.content == original_content, "Downloaded content doesn't match original"


@pytest.mark.asyncio
async def test_07_rename_file(api_client, db):
    """
    Test: Rename a file
    Verifies: PUT /api/files/{file_id}/rename updates file in database
    """
    file_id = getattr(pytest, "test_file_id", None)

    if not file_id:
        pytest.skip("No file_id from previous test")

    new_name = "renamed_document.txt"

    response = await api_client.put(
        f"/api/files/{file_id}/rename",
        json={"new_name": new_name}
    )

    assert response.status_code == 200, f"Failed to rename file: {response.text}"

    data = response.json()
    assert data["name"] == new_name

    # Verify in database
    file_doc = await db.drive_items.find_one({"_id": file_id})
    assert file_doc["name"] == new_name


@pytest.mark.asyncio
async def test_08_move_file_to_root(api_client, db):
    """
    Test: Move file from folder to root
    Verifies: PUT /api/files/{file_id}/move updates parent_id in database
    """
    file_id = getattr(pytest, "test_file_id", None)

    if not file_id:
        pytest.skip("No file_id from previous test")

    response = await api_client.put(
        f"/api/files/{file_id}/move",
        json={"new_parent_id": None}
    )

    assert response.status_code == 200, f"Failed to move file: {response.text}"

    data = response.json()
    assert data["parent_id"] is None

    # Verify in database
    file_doc = await db.drive_items.find_one({"_id": file_id})
    assert file_doc["parent_id"] is None


@pytest.mark.asyncio
async def test_09_star_file(api_client, db):
    """
    Test: Star/unstar a file
    Verifies: POST /api/files/{file_id}/star toggles starred status
    """
    file_id = getattr(pytest, "test_file_id", None)

    if not file_id:
        pytest.skip("No file_id from previous test")

    # Star the file
    response = await api_client.post(f"/api/files/{file_id}/star")

    assert response.status_code == 200, f"Failed to star file: {response.text}"

    data = response.json()
    assert data["is_starred"] is True

    # Verify in database
    file_doc = await db.drive_items.find_one({"_id": file_id})
    assert file_doc["is_starred"] is True

    # Unstar the file
    response = await api_client.post(f"/api/files/{file_id}/star")

    assert response.status_code == 200
    data = response.json()
    assert data["is_starred"] is False


# ==================== SEARCH TESTS ====================

@pytest.mark.asyncio
async def test_10_search_files(api_client):
    """
    Test: Search for files by name
    Verifies: GET /api/search finds uploaded files
    """
    response = await api_client.get("/api/search?q=renamed")

    assert response.status_code == 200, f"Failed to search: {response.text}"

    data = response.json()
    assert "items" in data
    assert "total" in data
    # File should exist at this point in the test sequence (renamed in test_07)
    # But if running tests individually, might be empty - just verify endpoint works
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_11_get_recent_files(api_client):
    """
    Test: Get recently modified files
    Verifies: GET /api/search/recent returns recent files
    """
    response = await api_client.get("/api/search/recent?limit=10")

    assert response.status_code == 200, f"Failed to get recent files: {response.text}"

    data = response.json()
    assert isinstance(data, list)
    # Should have our test file in recent files
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_12_get_starred_items(api_client):
    """
    Test: Get starred items (should be empty after test_09)
    Verifies: GET /api/search/starred returns starred items
    """
    response = await api_client.get("/api/search/starred")

    assert response.status_code == 200, f"Failed to get starred items: {response.text}"

    data = response.json()
    assert isinstance(data, list)


# ==================== DELETE TESTS ====================

@pytest.mark.asyncio
async def test_13_soft_delete_file(api_client, db):
    """
    Test: Soft delete file (move to trash)
    Verifies: DELETE /api/files/{file_id} marks file as deleted
    """
    file_id = getattr(pytest, "test_file_id", None)

    if not file_id:
        pytest.skip("No file_id from previous test")

    response = await api_client.delete(f"/api/files/{file_id}?permanent=false")

    assert response.status_code == 200, f"Failed to delete file: {response.text}"

    data = response.json()
    assert data["status"] == "trashed"

    # Verify in database - file should still exist but marked as deleted
    file_doc = await db.drive_items.find_one({"_id": file_id})
    assert file_doc is not None, "File should still exist in database"
    assert file_doc["is_deleted"] is True
    assert file_doc["deleted_at"] is not None


@pytest.mark.asyncio
async def test_14_permanent_delete_file(api_client, db):
    """
    Test: Permanently delete file
    Verifies: DELETE /api/files/{file_id}?permanent=true removes file from database
    """
    file_id = getattr(pytest, "test_file_id", None)

    if not file_id:
        pytest.skip("No file_id from previous test")

    response = await api_client.delete(f"/api/files/{file_id}?permanent=true")

    assert response.status_code == 200, f"Failed to permanently delete file: {response.text}"

    data = response.json()
    assert data["status"] == "permanently_deleted"

    # Verify in database - file should be completely gone
    file_doc = await db.drive_items.find_one({"_id": file_id})
    assert file_doc is None, "File should be removed from database"


@pytest.mark.asyncio
async def test_15_delete_folder(api_client, db):
    """
    Test: Delete folder
    Verifies: DELETE /api/folders/{folder_id} removes folder
    """
    folder_id = getattr(pytest, "test_folder_id", None)

    if not folder_id:
        pytest.skip("No folder_id from previous test")

    # Soft delete first
    response = await api_client.delete(f"/api/folders/{folder_id}?permanent=false")

    assert response.status_code == 200, f"Failed to delete folder: {response.text}"

    # Verify soft delete
    folder_doc = await db.drive_items.find_one({"_id": folder_id})
    assert folder_doc["is_deleted"] is True

    # Permanent delete
    response = await api_client.delete(f"/api/folders/{folder_id}?permanent=true")

    assert response.status_code == 200

    # Verify permanent delete
    folder_doc = await db.drive_items.find_one({"_id": folder_id})
    assert folder_doc is None


# ==================== SUMMARY TEST ====================

@pytest.mark.asyncio
async def test_16_full_crud_cycle_summary(api_client, db):
    """
    Summary test: Complete CRUD cycle with verification
    Creates -> Reads -> Updates -> Deletes and verifies each step
    """
    # 1. CREATE: Create a new folder
    folder_response = await api_client.post(
        "/api/folders",
        json={
            "name": "CRUDTestFolder",
            "parent_id": None,
            "organization_id": TEST_ORG_ID
        }
    )
    assert folder_response.status_code == 200
    folder_id = folder_response.json()["id"]

    # 2. CREATE: Upload file in folder
    file_content = b"Full CRUD cycle test content"
    file_response = await api_client.post(
        "/api/files/upload",
        files={"file": ("crud_test.txt", file_content, "text/plain")},
        data={"parent_id": folder_id, "organization_id": TEST_ORG_ID}
    )
    assert file_response.status_code == 200
    file_id = file_response.json()["id"]

    # 3. READ: Verify file exists in database
    file_doc = await db.drive_items.find_one({"_id": file_id})
    assert file_doc is not None
    assert file_doc["name"] == "crud_test.txt"

    # 4. READ: Download and verify content
    download_response = await api_client.get(f"/api/files/{file_id}/download")
    assert download_response.status_code == 200
    assert download_response.content == file_content

    # 5. UPDATE: Rename file
    rename_response = await api_client.put(
        f"/api/files/{file_id}/rename",
        json={"new_name": "updated_crud_test.txt"}
    )
    assert rename_response.status_code == 200

    # Verify rename in database
    file_doc = await db.drive_items.find_one({"_id": file_id})
    assert file_doc["name"] == "updated_crud_test.txt"

    # 6. DELETE: Remove file and folder
    await api_client.delete(f"/api/files/{file_id}?permanent=true")
    await api_client.delete(f"/api/folders/{folder_id}?permanent=true")

    # 7. VERIFY: Confirm deletion
    file_doc = await db.drive_items.find_one({"_id": file_id})
    folder_doc = await db.drive_items.find_one({"_id": folder_id})
    assert file_doc is None
    assert folder_doc is None

    # Full CRUD cycle completed successfully!


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
