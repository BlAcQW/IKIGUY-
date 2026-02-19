"""
Tests for Content Moderation API endpoints.

Tests cover:
- POST /api/v1/devotionals/{devotional_id}/flag - Flag devotional
- GET /api/v1/moderation/flags - List flags
- GET /api/v1/moderation/flags/{flag_id} - Get flag details
- PUT /api/v1/moderation/flags/{flag_id}/resolve - Resolve flag
- GET /api/v1/moderation/stats - Get moderation statistics
"""

import pytest
from datetime import datetime
from bson import ObjectId
from tests.conftest import create_auth_header


class TestModerationSystem:
    """Test suite for content moderation system."""

    @pytest.mark.asyncio
    async def test_flag_devotional_success(
        self, client, admin_token, test_devotional, test_db
    ):
        """
        Test flagging a devotional for review.
        Expected: Creates flag and returns 201.
        """
        # Arrange
        devotional_id = str(test_devotional["_id"])
        flag_data = {
            "reason": "Test flag: Inappropriate content",
            "details": "This is a test flag for testing purposes",
            "severity": "medium"
        }

        # Act
        response = client.post(
            f"/api/v1/devotionals/{devotional_id}/flag",
            json=flag_data,
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "flag_id" in data
        assert data["message"] == "Content flagged successfully"
        assert data["devotional_id"] == devotional_id

        # Verify in database
        flag = await test_db.flags.find_one({"_id": ObjectId(data["flag_id"])})
        assert flag is not None
        assert flag["devotional_id"] == devotional_id
        assert flag["reason"] == "Test flag: Inappropriate content"
        assert flag["status"] == "pending"
        assert flag["severity"] == "medium"

        # Cleanup
        await test_db.flags.delete_one({"_id": ObjectId(data["flag_id"])})

    @pytest.mark.asyncio
    async def test_flag_nonexistent_devotional(self, client, admin_token):
        """
        Test flagging a non-existent devotional.
        Expected: Returns 404.
        """
        # Arrange
        fake_id = str(ObjectId())
        flag_data = {
            "reason": "Test flag",
            "details": "Details",
            "severity": "low"
        }

        # Act
        response = client.post(
            f"/api/v1/devotionals/{fake_id}/flag",
            json=flag_data,
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_flag_without_auth(self, client, test_devotional):
        """
        Test flagging without authentication.
        Expected: Returns 401.
        """
        # Arrange
        devotional_id = str(test_devotional["_id"])
        flag_data = {
            "reason": "Test flag",
            "details": "Details",
            "severity": "low"
        }

        # Act
        response = client.post(
            f"/api/v1/devotionals/{devotional_id}/flag",
            json=flag_data
        )

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_all_flags_success(
        self, client, admin_token, test_devotional, test_db
    ):
        """
        Test retrieving all flags with pagination.
        Expected: Returns 200 with flags list.
        """
        # Arrange - Create test flags
        flag1 = {
            "_id": ObjectId(),
            "devotional_id": str(test_devotional["_id"]),
            "reason": "Test Flag 1",
            "details": "First test flag",
            "severity": "high",
            "status": "pending",
            "flagged_by": "693acf37d221b83bb8f2d2a7",
            "flagged_at": datetime.utcnow()
        }
        flag2 = {
            "_id": ObjectId(),
            "devotional_id": str(test_devotional["_id"]),
            "reason": "Test Flag 2",
            "details": "Second test flag",
            "severity": "low",
            "status": "pending",
            "flagged_by": "693acf37d221b83bb8f2d2a7",
            "flagged_at": datetime.utcnow()
        }

        await test_db.flags.insert_many([flag1, flag2])

        # Act
        response = client.get(
            "/api/v1/moderation/flags?page=1&page_size=10",
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "flags" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

        # Verify our test flags are in the results
        flag_reasons = [f["reason"] for f in data["flags"]]
        assert "Test Flag 1" in flag_reasons
        assert "Test Flag 2" in flag_reasons

        # Cleanup
        await test_db.flags.delete_many({"_id": {"$in": [flag1["_id"], flag2["_id"]]}})

    @pytest.mark.asyncio
    async def test_get_flags_with_filters(
        self, client, admin_token, test_devotional, test_db
    ):
        """
        Test retrieving flags with status filter.
        Expected: Returns only flags matching the filter.
        """
        # Arrange - Create flags with different statuses
        pending_flag = {
            "_id": ObjectId(),
            "devotional_id": str(test_devotional["_id"]),
            "reason": "Test Pending Flag",
            "severity": "medium",
            "status": "pending",
            "flagged_by": "693acf37d221b83bb8f2d2a7",
            "flagged_at": datetime.utcnow()
        }
        resolved_flag = {
            "_id": ObjectId(),
            "devotional_id": str(test_devotional["_id"]),
            "reason": "Test Resolved Flag",
            "severity": "low",
            "status": "resolved",
            "flagged_by": "693acf37d221b83bb8f2d2a7",
            "flagged_at": datetime.utcnow(),
            "resolved_at": datetime.utcnow(),
            "resolved_by": "693acf37d221b83bb8f2d2a7"
        }

        await test_db.flags.insert_many([pending_flag, resolved_flag])

        # Act - Filter for pending only
        response = client.get(
            "/api/v1/moderation/flags?status=pending",
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # All returned flags should be pending
        for flag in data["flags"]:
            if flag["reason"] in ["Test Pending Flag", "Test Resolved Flag"]:
                assert flag["status"] == "pending"

        # Cleanup
        await test_db.flags.delete_many({
            "_id": {"$in": [pending_flag["_id"], resolved_flag["_id"]]}
        })

    @pytest.mark.asyncio
    async def test_get_flag_details_success(
        self, client, admin_token, test_devotional, test_db
    ):
        """
        Test retrieving specific flag details.
        Expected: Returns 200 with flag details.
        """
        # Arrange - Create a test flag
        flag = {
            "_id": ObjectId(),
            "devotional_id": str(test_devotional["_id"]),
            "reason": "Test Flag Details",
            "details": "Detailed information about the flag",
            "severity": "high",
            "status": "pending",
            "flagged_by": "693acf37d221b83bb8f2d2a7",
            "flagged_at": datetime.utcnow()
        }

        await test_db.flags.insert_one(flag)

        # Act
        response = client.get(
            f"/api/v1/moderation/flags/{str(flag['_id'])}",
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["flag_id"] == str(flag["_id"])
        assert data["reason"] == "Test Flag Details"
        assert data["severity"] == "high"
        assert data["status"] == "pending"

        # Cleanup
        await test_db.flags.delete_one({"_id": flag["_id"]})

    @pytest.mark.asyncio
    async def test_get_nonexistent_flag(self, client, admin_token):
        """
        Test retrieving a non-existent flag.
        Expected: Returns 404.
        """
        # Arrange
        fake_id = str(ObjectId())

        # Act
        response = client.get(
            f"/api/v1/moderation/flags/{fake_id}",
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_resolve_flag_success(
        self, client, admin_token, test_devotional, test_db
    ):
        """
        Test resolving a flag successfully.
        Expected: Updates flag status and returns 200.
        """
        # Arrange - Create a pending flag
        flag = {
            "_id": ObjectId(),
            "devotional_id": str(test_devotional["_id"]),
            "reason": "Test Flag to Resolve",
            "severity": "medium",
            "status": "pending",
            "flagged_by": "693acf37d221b83bb8f2d2a7",
            "flagged_at": datetime.utcnow()
        }

        await test_db.flags.insert_one(flag)

        # Resolution data
        resolution_data = {
            "action_taken": "reviewed",
            "admin_notes": "Test resolution - no action needed",
            "content_updated": False
        }

        # Act
        response = client.put(
            f"/api/v1/moderation/flags/{str(flag['_id'])}/resolve",
            json=resolution_data,
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["message"] == "Flag resolved successfully"
        assert data["flag_id"] == str(flag["_id"])

        # Verify in database
        updated_flag = await test_db.flags.find_one({"_id": flag["_id"]})
        assert updated_flag["status"] == "resolved"
        assert updated_flag["action_taken"] == "reviewed"
        assert updated_flag["admin_notes"] == "Test resolution - no action needed"
        assert "resolved_at" in updated_flag
        assert "resolved_by" in updated_flag

        # Cleanup
        await test_db.flags.delete_one({"_id": flag["_id"]})

    @pytest.mark.asyncio
    async def test_resolve_already_resolved_flag(
        self, client, admin_token, test_devotional, test_db
    ):
        """
        Test resolving an already resolved flag.
        Expected: Returns 400 or updates anyway.
        """
        # Arrange - Create a resolved flag
        flag = {
            "_id": ObjectId(),
            "devotional_id": str(test_devotional["_id"]),
            "reason": "Already Resolved Flag",
            "severity": "low",
            "status": "resolved",
            "flagged_by": "693acf37d221b83bb8f2d2a7",
            "flagged_at": datetime.utcnow(),
            "resolved_at": datetime.utcnow(),
            "resolved_by": "693acf37d221b83bb8f2d2a7",
            "action_taken": "reviewed"
        }

        await test_db.flags.insert_one(flag)

        # Resolution data
        resolution_data = {
            "action_taken": "content_removed",
            "admin_notes": "Additional action",
            "content_updated": True
        }

        # Act
        response = client.put(
            f"/api/v1/moderation/flags/{str(flag['_id'])}/resolve",
            json=resolution_data,
            headers=create_auth_header(admin_token)
        )

        # Assert - Should either succeed or return 400
        assert response.status_code in [200, 400]

        # Cleanup
        await test_db.flags.delete_one({"_id": flag["_id"]})

    @pytest.mark.asyncio
    async def test_get_moderation_stats(
        self, client, admin_token, test_devotional, test_db
    ):
        """
        Test retrieving moderation statistics.
        Expected: Returns 200 with statistics.
        """
        # Arrange - Create test flags for statistics
        flags = [
            {
                "_id": ObjectId(),
                "devotional_id": str(test_devotional["_id"]),
                "reason": "Test Stats Flag 1",
                "severity": "high",
                "status": "pending",
                "flagged_by": "693acf37d221b83bb8f2d2a7",
                "flagged_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "devotional_id": str(test_devotional["_id"]),
                "reason": "Test Stats Flag 2",
                "severity": "medium",
                "status": "resolved",
                "flagged_by": "693acf37d221b83bb8f2d2a7",
                "flagged_at": datetime.utcnow(),
                "resolved_at": datetime.utcnow(),
                "resolved_by": "693acf37d221b83bb8f2d2a7"
            }
        ]

        await test_db.flags.insert_many(flags)

        # Act
        response = client.get(
            "/api/v1/moderation/stats",
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "total_flags" in data
        assert "pending_flags" in data
        assert "resolved_flags" in data
        assert "flags_by_severity" in data
        assert "recent_flags" in data

        # Verify our test data is counted
        assert data["total_flags"] >= 2

        # Cleanup
        await test_db.flags.delete_many({
            "_id": {"$in": [f["_id"] for f in flags]}
        })

    @pytest.mark.asyncio
    async def test_moderation_workflow_complete(
        self, client, admin_token, test_devotional, test_db
    ):
        """
        Test complete moderation workflow: flag -> list -> details -> resolve.
        Expected: All operations succeed in sequence.
        """
        # Step 1: Flag a devotional
        flag_data = {
            "reason": "Test Complete Workflow",
            "details": "Testing end-to-end moderation",
            "severity": "medium"
        }

        flag_response = client.post(
            f"/api/v1/devotionals/{str(test_devotional['_id'])}/flag",
            json=flag_data,
            headers=create_auth_header(admin_token)
        )
        assert flag_response.status_code == 201
        flag_id = flag_response.json()["flag_id"]

        # Step 2: Verify flag in list
        list_response = client.get(
            "/api/v1/moderation/flags",
            headers=create_auth_header(admin_token)
        )
        assert list_response.status_code == 200
        flags = list_response.json()["flags"]
        assert any(f["flag_id"] == flag_id for f in flags)

        # Step 3: Get flag details
        details_response = client.get(
            f"/api/v1/moderation/flags/{flag_id}",
            headers=create_auth_header(admin_token)
        )
        assert details_response.status_code == 200
        assert details_response.json()["status"] == "pending"

        # Step 4: Resolve the flag
        resolution_data = {
            "action_taken": "reviewed",
            "admin_notes": "Workflow test completed",
            "content_updated": False
        }

        resolve_response = client.put(
            f"/api/v1/moderation/flags/{flag_id}/resolve",
            json=resolution_data,
            headers=create_auth_header(admin_token)
        )
        assert resolve_response.status_code == 200

        # Step 5: Verify flag is resolved in database
        resolved_flag = await test_db.flags.find_one({"_id": ObjectId(flag_id)})
        assert resolved_flag["status"] == "resolved"

        # Cleanup
        await test_db.flags.delete_one({"_id": ObjectId(flag_id)})
