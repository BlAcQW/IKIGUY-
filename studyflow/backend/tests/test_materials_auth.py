"""
Test authentication for materials endpoints.

Verifies that all materials endpoints require proper authentication
and role-based access control.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.models.user import UserRole


client = TestClient(app)


class TestMaterialsAuthentication:
    """Test authentication on materials endpoints."""

    def test_upload_without_auth_returns_401(self):
        """
        Test that uploading without authentication returns 401.
        """
        # Prepare upload data
        files = {"file": ("test.pdf", b"test content", "application/pdf")}
        data = {
            "title": "Test Material",
            "subject": "Mathematics",
            "description": "Test description"
        }

        # Make request without auth header
        response = client.post("/api/v1/materials/upload", files=files, data=data)

        # Should return 401 or 403 (depending on security middleware)
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_upload_with_student_role_returns_403(self):
        """
        Test that students cannot upload materials.
        """
        # Mock JWT token with student role
        with patch("app.core.auth.supabase_auth.verify_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "student-123",
                "user_metadata": {"role": UserRole.STUDENT.value}
            }

            files = {"file": ("test.pdf", b"test content", "application/pdf")}
            data = {
                "title": "Test Material",
                "subject": "Mathematics"
            }

            # Make request with auth header
            response = client.post(
                "/api/v1/materials/upload",
                files=files,
                data=data,
                headers={"Authorization": "Bearer fake-token"}
            )

            # Should return 403
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Access denied" in response.json().get("detail", "")

    def test_upload_with_teacher_role_succeeds(self):
        """
        Test that teachers can upload materials.
        """
        # Mock JWT token with teacher role
        with patch("app.core.auth.supabase_auth.verify_token") as mock_verify:
            with patch("app.services.material_service.MaterialService.save_uploaded_file") as mock_save:
                with patch("app.services.material_service.MaterialService.create_material") as mock_create:
                    # Setup mocks
                    mock_verify.return_value = {
                        "sub": "teacher-123",
                        "user_metadata": {"role": UserRole.TEACHER.value}
                    }

                    mock_save.return_value = ("/path/to/file.pdf", 1024)

                    from app.models.material import StudyMaterial, ProcessingStatus
                    from datetime import datetime

                    mock_material = StudyMaterial(
                        id="material-123",
                        title="Test Material",
                        subject="Mathematics",
                        file_name="test.pdf",
                        file_path="/path/to/file.pdf",
                        file_size=1024,
                        file_type="pdf",
                        uploaded_by="teacher-123",
                        status=ProcessingStatus.PENDING,
                        created_at=datetime.utcnow()
                    )
                    mock_create.return_value = mock_material

                    files = {"file": ("test.pdf", b"test content", "application/pdf")}
                    data = {
                        "title": "Test Material",
                        "subject": "Mathematics"
                    }

                    # Make request
                    response = client.post(
                        "/api/v1/materials/upload",
                        files=files,
                        data=data,
                        headers={"Authorization": "Bearer fake-token"}
                    )

                    # Should succeed
                    assert response.status_code == status.HTTP_201_CREATED
                    assert response.json()["title"] == "Test Material"

    def test_upload_with_admin_role_succeeds(self):
        """
        Test that admins can upload materials.
        """
        # Mock JWT token with admin role
        with patch("app.core.auth.supabase_auth.verify_token") as mock_verify:
            with patch("app.services.material_service.MaterialService.save_uploaded_file") as mock_save:
                with patch("app.services.material_service.MaterialService.create_material") as mock_create:
                    # Setup mocks
                    mock_verify.return_value = {
                        "sub": "admin-123",
                        "user_metadata": {"role": UserRole.ADMIN.value}
                    }

                    mock_save.return_value = ("/path/to/file.pdf", 1024)

                    from app.models.material import StudyMaterial, ProcessingStatus
                    from datetime import datetime

                    mock_material = StudyMaterial(
                        id="material-456",
                        title="Admin Material",
                        subject="Science",
                        file_name="test.pdf",
                        file_path="/path/to/file.pdf",
                        file_size=1024,
                        file_type="pdf",
                        uploaded_by="admin-123",
                        status=ProcessingStatus.PENDING,
                        created_at=datetime.utcnow()
                    )
                    mock_create.return_value = mock_material

                    files = {"file": ("test.pdf", b"test content", "application/pdf")}
                    data = {
                        "title": "Admin Material",
                        "subject": "Science"
                    }

                    # Make request
                    response = client.post(
                        "/api/v1/materials/upload",
                        files=files,
                        data=data,
                        headers={"Authorization": "Bearer fake-token"}
                    )

                    # Should succeed
                    assert response.status_code == status.HTTP_201_CREATED
                    assert response.json()["title"] == "Admin Material"

    def test_list_materials_requires_auth(self):
        """
        Test that listing materials requires authentication.
        """
        response = client.get("/api/v1/materials/")

        # Should return 401 or 403
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_get_material_requires_auth(self):
        """
        Test that getting a material requires authentication.
        """
        response = client.get("/api/v1/materials/test-id")

        # Should return 401 or 403
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_delete_material_requires_teacher_or_admin(self):
        """
        Test that deleting materials requires teacher or admin role.
        """
        # Test without auth
        response = client.delete("/api/v1/materials/test-id")
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

        # Test with student role
        with patch("app.core.auth.supabase_auth.verify_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "student-123",
                "user_metadata": {"role": UserRole.STUDENT.value}
            }

            response = client.delete(
                "/api/v1/materials/test-id",
                headers={"Authorization": "Bearer fake-token"}
            )

            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_upload_with_organization_header_succeeds(self):
        """
        Test that upload succeeds when X-Organization-Id header is provided.

        This test verifies the fix for the 403 error where the frontend
        was not sending the organization context.
        """
        # Mock JWT token with teacher role and organization context
        with patch("app.core.auth.supabase_auth.verify_token") as mock_verify:
            with patch("app.services.material_service.MaterialService.save_uploaded_file") as mock_save:
                with patch("app.services.material_service.MaterialService.create_material") as mock_create:
                    with patch("apps.shared.services.organization_service.get_organization_service") as mock_org_service:
                        # Setup mocks
                        mock_verify.return_value = {
                            "sub": "teacher-123",
                            "email": "teacher@example.com",
                            "user_metadata": {
                                "role": UserRole.TEACHER.value,
                                "organization_id": "org-456"
                            }
                        }

                        # Mock organization service
                        mock_org_svc = MagicMock()
                        mock_org_svc.is_universal_admin.return_value = False
                        mock_org_service.return_value = mock_org_svc

                        mock_save.return_value = ("/path/to/file.pdf", 1024)

                        from app.models.material import StudyMaterial, ProcessingStatus
                        from datetime import datetime

                        mock_material = StudyMaterial(
                            id="material-789",
                            organization_id="org-456",
                            title="Test Material with Org",
                            subject="Mathematics",
                            file_name="test.pdf",
                            file_path="/path/to/file.pdf",
                            file_size=1024,
                            file_type="pdf",
                            uploaded_by="teacher-123",
                            status=ProcessingStatus.PENDING,
                            created_at=datetime.utcnow()
                        )
                        mock_create.return_value = mock_material

                        files = {"file": ("test.pdf", b"test content", "application/pdf")}
                        data = {
                            "title": "Test Material with Org",
                            "subject": "Mathematics"
                        }

                        # Make request with both Authorization and X-Organization-Id headers
                        response = client.post(
                            "/api/v1/materials/upload",
                            files=files,
                            data=data,
                            headers={
                                "Authorization": "Bearer fake-token",
                                "X-Organization-Id": "org-456"
                            }
                        )

                        # Should succeed
                        assert response.status_code == status.HTTP_201_CREATED
                        result = response.json()
                        assert result["title"] == "Test Material with Org"
                        assert result["organization_id"] == "org-456"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
