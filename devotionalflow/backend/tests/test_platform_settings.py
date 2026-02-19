"""
Tests for Platform Settings API endpoints.

Tests cover:
- GET /api/v1/admin/settings - Retrieve platform settings
- PUT /api/v1/admin/settings - Update platform settings
"""

import pytest
from datetime import datetime
from tests.conftest import create_auth_header


class TestPlatformSettings:
    """Test suite for platform settings management."""

    @pytest.mark.asyncio
    async def test_get_platform_settings_success(self, client, admin_token, test_db):
        """
        Test retrieving platform settings successfully.
        Expected: Returns 200 with settings data.
        """
        # Act
        response = client.get(
            "/api/v1/admin/settings",
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "platform_name" in data
        assert "ai_generation" in data
        assert "content_moderation" in data
        assert "email_notifications" in data
        assert "analytics" in data

        # Verify AI generation settings
        assert "enabled" in data["ai_generation"]
        assert "model" in data["ai_generation"]
        assert "features" in data["ai_generation"]

    @pytest.mark.asyncio
    async def test_get_settings_without_auth(self, client):
        """
        Test retrieving settings without authentication.
        Expected: Returns 401 Unauthorized.
        """
        # Act
        response = client.get("/api/v1/admin/settings")

        # Assert
        assert response.status_code == 401
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_update_platform_settings_success(
        self, client, admin_token, test_db, cleanup_collections
    ):
        """
        Test updating platform settings successfully.
        Expected: Updates settings and returns 200 with updated data.
        """
        # Arrange - Get current settings first
        get_response = client.get(
            "/api/v1/admin/settings",
            headers=create_auth_header(admin_token)
        )
        current_settings = get_response.json()

        # Prepare update data
        update_data = {
            "platform_name": "Test FreshManna Platform",
            "platform_description": "Test platform for spiritual growth",
            "ai_generation": {
                "enabled": True,
                "model": "gpt-4",
                "features": {
                    "scripture_suggestions": True,
                    "content_enhancement": True,
                    "translation": False
                }
            },
            "content_moderation": {
                "enabled": True,
                "auto_flag_threshold": 0.85,
                "require_review": True
            }
        }

        # Act - Update settings
        response = client.put(
            "/api/v1/admin/settings",
            json=update_data,
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify updates
        assert data["platform_name"] == "Test FreshManna Platform"
        assert data["platform_description"] == "Test platform for spiritual growth"
        assert data["ai_generation"]["model"] == "gpt-4"
        assert data["ai_generation"]["features"]["scripture_suggestions"] is True
        assert data["content_moderation"]["auto_flag_threshold"] == 0.85

        # Verify in database
        db_settings = await test_db.platform_settings.find_one({})
        assert db_settings is not None
        assert db_settings["platform_name"] == "Test FreshManna Platform"

        # Cleanup - Restore original settings
        restore_response = client.put(
            "/api/v1/admin/settings",
            json=current_settings,
            headers=create_auth_header(admin_token)
        )
        assert restore_response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_settings_partial(
        self, client, admin_token, test_db, cleanup_collections
    ):
        """
        Test updating only some fields in settings.
        Expected: Updates specified fields, keeps others unchanged.
        """
        # Arrange - Get current settings
        get_response = client.get(
            "/api/v1/admin/settings",
            headers=create_auth_header(admin_token)
        )
        current_settings = get_response.json()
        original_platform_name = current_settings["platform_name"]

        # Update only AI generation settings
        update_data = {
            "ai_generation": {
                "enabled": False,
                "model": "gpt-3.5-turbo"
            }
        }

        # Act
        response = client.put(
            "/api/v1/admin/settings",
            json=update_data,
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify AI generation was updated
        assert data["ai_generation"]["enabled"] is False
        assert data["ai_generation"]["model"] == "gpt-3.5-turbo"

        # Verify platform_name unchanged
        assert data["platform_name"] == original_platform_name

        # Cleanup - Restore settings
        restore_response = client.put(
            "/api/v1/admin/settings",
            json=current_settings,
            headers=create_auth_header(admin_token)
        )
        assert restore_response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_settings_invalid_data(self, client, admin_token):
        """
        Test updating settings with invalid data.
        Expected: Returns 422 validation error.
        """
        # Arrange - Invalid threshold value (should be 0-1)
        update_data = {
            "content_moderation": {
                "enabled": True,
                "auto_flag_threshold": 1.5  # Invalid: > 1
            }
        }

        # Act
        response = client.put(
            "/api/v1/admin/settings",
            json=update_data,
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_settings_non_admin(self, client, author_token):
        """
        Test updating settings as non-admin user.
        Expected: Returns 403 Forbidden.
        """
        # Arrange
        update_data = {
            "platform_name": "Unauthorized Update"
        }

        # Act
        response = client.put(
            "/api/v1/admin/settings",
            json=update_data,
            headers=create_auth_header(author_token)
        )

        # Assert - Should be forbidden for non-admin
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_settings_persistence(
        self, client, admin_token, test_db, cleanup_collections
    ):
        """
        Test that settings persist across requests.
        Expected: Settings remain after multiple get requests.
        """
        # Arrange - Update settings
        update_data = {
            "platform_name": "Test Persistence Platform",
            "ai_generation": {
                "enabled": True,
                "model": "gpt-4-turbo"
            }
        }

        update_response = client.put(
            "/api/v1/admin/settings",
            json=update_data,
            headers=create_auth_header(admin_token)
        )
        assert update_response.status_code == 200

        # Act - Get settings multiple times
        response1 = client.get(
            "/api/v1/admin/settings",
            headers=create_auth_header(admin_token)
        )
        response2 = client.get(
            "/api/v1/admin/settings",
            headers=create_auth_header(admin_token)
        )

        # Assert - Both responses should have the same updated values
        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        assert data1["platform_name"] == "Test Persistence Platform"
        assert data2["platform_name"] == "Test Persistence Platform"
        assert data1["ai_generation"]["model"] == "gpt-4-turbo"
        assert data2["ai_generation"]["model"] == "gpt-4-turbo"

        # Verify in database
        db_settings = await test_db.platform_settings.find_one({})
        assert db_settings["platform_name"] == "Test Persistence Platform"
