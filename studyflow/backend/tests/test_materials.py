"""
Unit tests for materials routes.

Tests material upload, listing, retrieval, update, and deletion.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from io import BytesIO
from bson import ObjectId

from app.models.material import ProcessingStatus, MaterialType
from app.models.user import UserRole


class TestMaterialsRoutes:
    """Test materials API endpoints."""

    @pytest.mark.asyncio
    async def test_upload_material_success(self, client, mock_mongodb):
        """
        Test successful material upload.

        Expected: 201 status, material data returned, background task queued
        """
        # Mock teacher auth
        with patch("app.core.auth.supabase_auth.verify_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "teacher-id-123",
                "user_metadata": {"role": UserRole.TEACHER.value}
            }

            # Mock MongoDB insert
            mock_result = MagicMock()
            mock_result.inserted_id = ObjectId()
            mock_mongodb.insert_one = AsyncMock(return_value=mock_result)

            # Mock file
            file_content = b"Sample PDF content"
            files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}
            data = {
                "title": "Python Basics",
                "subject": "Computer Science",
                "description": "Introduction to Python",
                "topics": "variables,functions",
                "grade": 10
            }

            with patch("pathlib.Path.write_bytes"), \
                 patch("pathlib.Path.mkdir"):
                response = client.post(
                    "/api/v1/materials/upload",
                    files=files,
                    data=data,
                    headers={"Authorization": "Bearer teacher-token"}
                )

        assert response.status_code == 201
        result = response.json()
        assert result["title"] == "Python Basics"
        assert result["status"] == ProcessingStatus.PENDING.value

    @pytest.mark.asyncio
    async def test_upload_material_unauthorized(self, client, mock_mongodb):
        """
        Test material upload by student (unauthorized).

        Expected: 403 status, access denied
        """
        # Mock student auth
        with patch("app.core.auth.supabase_auth.verify_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "student-id-123",
                "user_metadata": {"role": UserRole.STUDENT.value}
            }

            file_content = b"Sample content"
            files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}
            data = {
                "title": "Test Material",
                "subject": "Math"
            }

            response = client.post(
                "/api/v1/materials/upload",
                files=files,
                data=data,
                headers={"Authorization": "Bearer student-token"}
            )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_upload_empty_file(self, client, mock_mongodb):
        """
        Test uploading empty file.

        Expected: 400 status, error message
        """
        with patch("app.core.auth.supabase_auth.verify_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "teacher-id-123",
                "user_metadata": {"role": UserRole.TEACHER.value}
            }

            # Empty file
            files = {"file": ("empty.pdf", BytesIO(b""), "application/pdf")}
            data = {
                "title": "Test",
                "subject": "Math"
            }

            response = client.post(
                "/api/v1/materials/upload",
                files=files,
                data=data,
                headers={"Authorization": "Bearer teacher-token"}
            )

        assert response.status_code == 400
        assert "Empty file" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_materials_success(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test listing materials.

        Expected: 200 status, list of materials
        """
        # Mock materials data
        materials = [
            {
                "_id": ObjectId(),
                "title": "Python Basics",
                "subject": "Computer Science",
                "grade": 10,
                "status": ProcessingStatus.COMPLETED.value,
                "file_type": MaterialType.PDF.value,
                "chunks_count": 5
            },
            {
                "_id": ObjectId(),
                "title": "Algebra Intro",
                "subject": "Mathematics",
                "grade": 9,
                "status": ProcessingStatus.COMPLETED.value,
                "file_type": MaterialType.PDF.value,
                "chunks_count": 8
            }
        ]

        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.__aiter__.return_value = iter(materials)

        mock_mongodb.find.return_value = mock_cursor

        response = client.get(
            "/api/v1/materials/",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "Python Basics"

    @pytest.mark.asyncio
    async def test_list_materials_with_filters(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test listing materials with subject filter.

        Expected: 200 status, filtered materials
        """
        materials = [
            {
                "_id": ObjectId(),
                "title": "Python Basics",
                "subject": "Computer Science",
                "grade": 10,
                "status": ProcessingStatus.COMPLETED.value,
                "file_type": MaterialType.PDF.value
            }
        ]

        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.__aiter__.return_value = iter(materials)

        mock_mongodb.find.return_value = mock_cursor

        response = client.get(
            "/api/v1/materials/?subject=Computer%20Science&grade=10",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["subject"] == "Computer Science"

    @pytest.mark.asyncio
    async def test_get_material_by_id_success(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test getting material by ID.

        Expected: 200 status, material details
        """
        material_id = str(ObjectId())
        material_data = {
            "_id": ObjectId(material_id),
            "title": "Python Basics",
            "subject": "Computer Science",
            "status": ProcessingStatus.COMPLETED.value,
            "file_type": MaterialType.PDF.value,
            "chunks_count": 5
        }

        mock_mongodb.find_one = AsyncMock(return_value=material_data)

        response = client.get(
            f"/api/v1/materials/{material_id}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Python Basics"

    @pytest.mark.asyncio
    async def test_get_material_not_found(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test getting non-existent material.

        Expected: 404 status
        """
        material_id = str(ObjectId())
        mock_mongodb.find_one = AsyncMock(return_value=None)

        response = client.get(
            f"/api/v1/materials/{material_id}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_material_success(self, client, mock_mongodb):
        """
        Test updating material metadata.

        Expected: 200 status, updated material
        """
        with patch("app.core.auth.supabase_auth.verify_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "teacher-id-123",
                "user_metadata": {"role": UserRole.TEACHER.value}
            }

            material_id = str(ObjectId())
            material_data = {
                "_id": ObjectId(material_id),
                "title": "Python Basics",
                "subject": "Computer Science",
                "status": ProcessingStatus.COMPLETED.value,
                "file_type": MaterialType.PDF.value
            }

            mock_mongodb.find_one = AsyncMock(return_value=material_data)
            mock_mongodb.update_one = AsyncMock()

            update_data = {
                "title": "Advanced Python",
                "description": "Updated description"
            }

            response = client.put(
                f"/api/v1/materials/{material_id}",
                json=update_data,
                headers={"Authorization": "Bearer teacher-token"}
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_material_success(self, client, mock_mongodb):
        """
        Test deleting material.

        Expected: 204 status, no content
        """
        with patch("app.core.auth.supabase_auth.verify_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "teacher-id-123",
                "user_metadata": {"role": UserRole.TEACHER.value}
            }

            material_id = str(ObjectId())
            material_data = {
                "_id": ObjectId(material_id),
                "file_path": "/tmp/test.pdf"
            }

            mock_mongodb.find_one = AsyncMock(return_value=material_data)
            mock_mongodb.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))

            with patch("pathlib.Path.unlink"):
                response = client.delete(
                    f"/api/v1/materials/{material_id}",
                    headers={"Authorization": "Bearer teacher-token"}
                )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_material_unauthorized(self, client, mock_mongodb):
        """
        Test deleting material as student (unauthorized).

        Expected: 403 status
        """
        with patch("app.core.auth.supabase_auth.verify_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "student-id-123",
                "user_metadata": {"role": UserRole.STUDENT.value}
            }

            material_id = str(ObjectId())

            response = client.delete(
                f"/api/v1/materials/{material_id}",
                headers={"Authorization": "Bearer student-token"}
            )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_download_material_success(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test downloading material file.

        Expected: 200 status, file content
        """
        material_id = str(ObjectId())
        material_data = {
            "_id": ObjectId(material_id),
            "file_path": "/tmp/test.pdf",
            "file_name": "test.pdf"
        }

        mock_mongodb.find_one = AsyncMock(return_value=material_data)

        with patch("pathlib.Path.exists", return_value=True), \
             patch("fastapi.responses.FileResponse"):
            response = client.get(
                f"/api/v1/materials/{material_id}/download",
                headers={"Authorization": "Bearer test-token"}
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_download_material_file_not_found(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test downloading material when file doesn't exist.

        Expected: 404 status
        """
        material_id = str(ObjectId())
        material_data = {
            "_id": ObjectId(material_id),
            "file_path": "/tmp/nonexistent.pdf",
            "file_name": "test.pdf"
        }

        mock_mongodb.find_one = AsyncMock(return_value=material_data)

        with patch("pathlib.Path.exists", return_value=False):
            response = client.get(
                f"/api/v1/materials/{material_id}/download",
                headers={"Authorization": "Bearer test-token"}
            )

        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]
