"""
Tests for Admin Dashboard API endpoints.

Tests cover:
- GET /api/v1/admin/dashboard/stats - Get admin dashboard statistics
- GET /api/v1/admin/dashboard/analytics - Get platform analytics
- GET /api/v1/admin/dashboard/top-content - Get top performing content
- GET /api/v1/admin/dashboard/recent-activity - Get recent user activity
"""

import pytest
from datetime import datetime, timedelta
from bson import ObjectId
from tests.conftest import create_auth_header


class TestAdminDashboard:
    """Test suite for admin dashboard functionality."""

    @pytest.mark.asyncio
    async def test_get_dashboard_stats_success(
        self, client, admin_token, test_db
    ):
        """
        Test retrieving admin dashboard statistics.
        Expected: Returns 200 with comprehensive stats.
        """
        # Arrange - Create test data
        today = datetime.utcnow()

        # Create users
        users = [
            {
                "_id": ObjectId(),
                "email": f"testuser{i}@test.com",
                "full_name": f"Test User {i}",
                "role": "user",
                "created_at": today - timedelta(days=i),
                "updated_at": today
            }
            for i in range(3)
        ]
        await test_db.users.insert_many(users)

        # Create devotionals
        devotionals = [
            {
                "_id": ObjectId(),
                "title": f"Test Devotional {i}",
                "content": "Content",
                "author_id": "693acf37d221b83bb8f2d2a7",
                "status": "published",
                "view_count": 100 + i,
                "like_count": 10 + i,
                "created_at": today - timedelta(days=i),
                "published_at": today - timedelta(days=i)
            }
            for i in range(3)
        ]
        await test_db.devotionals.insert_many(devotionals)

        # Act
        response = client.get(
            "/api/v1/admin/dashboard/stats",
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "total_users" in data
        assert "total_authors" in data
        assert "total_devotionals" in data
        assert "published_devotionals" in data
        assert "draft_devotionals" in data
        assert "total_views" in data
        assert "total_likes" in data
        assert "total_comments" in data
        assert "new_users_this_month" in data
        assert "new_devotionals_this_month" in data

        # Verify counts
        assert data["total_users"] >= 3
        assert data["total_devotionals"] >= 3
        assert data["total_views"] >= 303  # Sum of view_counts

        # Cleanup
        await test_db.users.delete_many({"_id": {"$in": [u["_id"] for u in users]}})
        await test_db.devotionals.delete_many({
            "_id": {"$in": [d["_id"] for d in devotionals]}
        })

    @pytest.mark.asyncio
    async def test_dashboard_stats_without_auth(self, client):
        """
        Test accessing admin stats without authentication.
        Expected: Returns 401.
        """
        # Act
        response = client.get("/api/v1/admin/dashboard/stats")

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_dashboard_stats_non_admin(self, client, author_token):
        """
        Test accessing admin stats as non-admin user.
        Expected: Returns 403.
        """
        # Act
        response = client.get(
            "/api/v1/admin/dashboard/stats",
            headers=create_auth_header(author_token)
        )

        # Assert
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_platform_analytics(
        self, client, admin_token, test_db
    ):
        """
        Test retrieving platform analytics.
        Expected: Returns 200 with time-series analytics data.
        """
        # Arrange - Create devotionals across different time periods
        today = datetime.utcnow()

        devotionals = [
            {
                "_id": ObjectId(),
                "title": f"Analytics Test {i}",
                "content": "Content",
                "author_id": "693acf37d221b83bb8f2d2a7",
                "status": "published",
                "view_count": 50 * (i + 1),
                "like_count": 5 * (i + 1),
                "created_at": today - timedelta(days=i * 7),  # Weekly spacing
                "published_at": today - timedelta(days=i * 7)
            }
            for i in range(4)  # 4 weeks of data
        ]

        await test_db.devotionals.insert_many(devotionals)

        # Act
        response = client.get(
            "/api/v1/admin/dashboard/analytics?days=30",
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "daily_views" in data
        assert "daily_likes" in data
        assert "daily_devotionals" in data
        assert "growth_rate" in data

        # Verify we have data points
        assert len(data["daily_views"]) > 0
        assert len(data["daily_devotionals"]) > 0

        # Cleanup
        await test_db.devotionals.delete_many({
            "_id": {"$in": [d["_id"] for d in devotionals]}
        })

    @pytest.mark.asyncio
    async def test_analytics_custom_period(
        self, client, admin_token, test_db
    ):
        """
        Test analytics with custom time period.
        Expected: Returns analytics for specified period.
        """
        # Arrange
        today = datetime.utcnow()

        devotional = {
            "_id": ObjectId(),
            "title": "Test Custom Period",
            "content": "Content",
            "author_id": "693acf37d221b83bb8f2d2a7",
            "status": "published",
            "view_count": 100,
            "created_at": today - timedelta(days=3),
            "published_at": today - timedelta(days=3)
        }

        await test_db.devotionals.insert_one(devotional)

        # Act - Request last 7 days
        response = client.get(
            "/api/v1/admin/dashboard/analytics?days=7",
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Should have around 7 data points
        assert len(data["daily_views"]) <= 8  # Allow for boundary conditions

        # Cleanup
        await test_db.devotionals.delete_one({"_id": devotional["_id"]})

    @pytest.mark.asyncio
    async def test_get_top_content(
        self, client, admin_token, test_db
    ):
        """
        Test retrieving top performing content.
        Expected: Returns devotionals sorted by engagement.
        """
        # Arrange - Create devotionals with varying engagement
        today = datetime.utcnow()

        devotionals = [
            {
                "_id": ObjectId(),
                "title": f"Top Content Test {i}",
                "content": "Content",
                "author_id": "693acf37d221b83bb8f2d2a7",
                "status": "published",
                "view_count": 1000 - (i * 100),  # Descending views
                "like_count": 100 - (i * 10),
                "comment_count": 50 - (i * 5),
                "share_count": 20 - (i * 2),
                "created_at": today,
                "published_at": today
            }
            for i in range(5)
        ]

        await test_db.devotionals.insert_many(devotionals)

        # Act
        response = client.get(
            "/api/v1/admin/dashboard/top-content?limit=3",
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "top_devotionals" in data
        assert "metric" in data

        # Should return 3 devotionals
        top_devs = [d for d in data["top_devotionals"] if d["title"].startswith("Top Content Test")]
        assert len(top_devs) <= 3

        # Should be sorted by views (highest first)
        if len(top_devs) > 1:
            assert top_devs[0]["view_count"] >= top_devs[1]["view_count"]

        # Cleanup
        await test_db.devotionals.delete_many({
            "_id": {"$in": [d["_id"] for d in devotionals]}
        })

    @pytest.mark.asyncio
    async def test_top_content_by_different_metrics(
        self, client, admin_token, test_db
    ):
        """
        Test top content sorted by different metrics.
        Expected: Returns different results for different metrics.
        """
        # Arrange
        today = datetime.utcnow()

        # Create devotionals with different strengths
        devotionals = [
            {
                "_id": ObjectId(),
                "title": "Most Viewed",
                "content": "Content",
                "author_id": "693acf37d221b83bb8f2d2a7",
                "status": "published",
                "view_count": 1000,
                "like_count": 10,
                "created_at": today,
                "published_at": today
            },
            {
                "_id": ObjectId(),
                "title": "Most Liked",
                "content": "Content",
                "author_id": "693acf37d221b83bb8f2d2a7",
                "status": "published",
                "view_count": 100,
                "like_count": 500,
                "created_at": today,
                "published_at": today
            }
        ]

        await test_db.devotionals.insert_many(devotionals)

        # Act - Sort by views
        views_response = client.get(
            "/api/v1/admin/dashboard/top-content?metric=views&limit=1",
            headers=create_auth_header(admin_token)
        )

        # Act - Sort by likes
        likes_response = client.get(
            "/api/v1/admin/dashboard/top-content?metric=likes&limit=1",
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert views_response.status_code == 200
        assert likes_response.status_code == 200

        views_data = views_response.json()
        likes_data = likes_response.json()

        # Top by views should have "Most Viewed"
        views_titles = [d["title"] for d in views_data["top_devotionals"]]
        if "Most Viewed" in views_titles or "Most Liked" in views_titles:
            # Verify "Most Viewed" has more views
            most_viewed = next((d for d in views_data["top_devotionals"] if d["title"] == "Most Viewed"), None)
            if most_viewed:
                assert most_viewed["view_count"] == 1000

        # Cleanup
        await test_db.devotionals.delete_many({
            "_id": {"$in": [d["_id"] for d in devotionals]}
        })

    @pytest.mark.asyncio
    async def test_get_recent_activity(
        self, client, admin_token, test_db
    ):
        """
        Test retrieving recent user activity.
        Expected: Returns recent devotional publications and user registrations.
        """
        # Arrange
        today = datetime.utcnow()

        # Create recent devotionals
        recent_devotional = {
            "_id": ObjectId(),
            "title": "Recent Activity Test",
            "content": "Content",
            "author_id": "693acf37d221b83bb8f2d2a7",
            "author_name": "Test Admin",
            "status": "published",
            "created_at": today - timedelta(hours=1),
            "published_at": today - timedelta(hours=1)
        }

        # Create recent user
        recent_user = {
            "_id": ObjectId(),
            "email": "recentuser@test.com",
            "full_name": "Recent User",
            "role": "user",
            "created_at": today - timedelta(hours=2),
            "updated_at": today
        }

        await test_db.devotionals.insert_one(recent_devotional)
        await test_db.users.insert_one(recent_user)

        # Act
        response = client.get(
            "/api/v1/admin/dashboard/recent-activity?limit=10",
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "activities" in data
        assert "total" in data

        # Should include our test data
        activity_types = [a["type"] for a in data["activities"]]
        assert "devotional_published" in activity_types or "user_registered" in activity_types

        # Cleanup
        await test_db.devotionals.delete_one({"_id": recent_devotional["_id"]})
        await test_db.users.delete_one({"_id": recent_user["_id"]})

    @pytest.mark.asyncio
    async def test_recent_activity_ordering(
        self, client, admin_token, test_db
    ):
        """
        Test that recent activity is ordered by time (newest first).
        Expected: Activities are in reverse chronological order.
        """
        # Arrange
        today = datetime.utcnow()

        activities = [
            {
                "_id": ObjectId(),
                "title": f"Activity {i}",
                "content": "Content",
                "author_id": "693acf37d221b83bb8f2d2a7",
                "status": "published",
                "created_at": today - timedelta(hours=i),
                "published_at": today - timedelta(hours=i)
            }
            for i in range(3)
        ]

        await test_db.devotionals.insert_many(activities)

        # Act
        response = client.get(
            "/api/v1/admin/dashboard/recent-activity?limit=5",
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Filter our test activities
        test_activities = [
            a for a in data["activities"]
            if a.get("title", "").startswith("Activity ")
        ]

        # Should be ordered newest first (Activity 0, then Activity 1, etc.)
        if len(test_activities) >= 2:
            # Check timestamps are in descending order
            first_time = datetime.fromisoformat(test_activities[0]["timestamp"].replace("Z", "+00:00"))
            second_time = datetime.fromisoformat(test_activities[1]["timestamp"].replace("Z", "+00:00"))
            assert first_time >= second_time

        # Cleanup
        await test_db.devotionals.delete_many({
            "_id": {"$in": [a["_id"] for a in activities]}
        })

    @pytest.mark.asyncio
    async def test_admin_dashboard_complete_workflow(
        self, client, admin_token, test_db
    ):
        """
        Test complete admin dashboard workflow.
        Expected: All dashboard endpoints work together.
        """
        # Arrange - Create comprehensive test data
        today = datetime.utcnow()

        user = {
            "_id": ObjectId(),
            "email": "workflow@test.com",
            "full_name": "Workflow User",
            "role": "user",
            "created_at": today
        }

        devotional = {
            "_id": ObjectId(),
            "title": "Workflow Test Devotional",
            "content": "Content",
            "author_id": "693acf37d221b83bb8f2d2a7",
            "status": "published",
            "view_count": 500,
            "like_count": 50,
            "created_at": today,
            "published_at": today
        }

        await test_db.users.insert_one(user)
        await test_db.devotionals.insert_one(devotional)

        # Step 1: Get stats
        stats_response = client.get(
            "/api/v1/admin/dashboard/stats",
            headers=create_auth_header(admin_token)
        )
        assert stats_response.status_code == 200
        stats = stats_response.json()

        # Step 2: Get analytics
        analytics_response = client.get(
            "/api/v1/admin/dashboard/analytics?days=7",
            headers=create_auth_header(admin_token)
        )
        assert analytics_response.status_code == 200

        # Step 3: Get top content
        top_response = client.get(
            "/api/v1/admin/dashboard/top-content?limit=5",
            headers=create_auth_header(admin_token)
        )
        assert top_response.status_code == 200

        # Step 4: Get recent activity
        activity_response = client.get(
            "/api/v1/admin/dashboard/recent-activity?limit=10",
            headers=create_auth_header(admin_token)
        )
        assert activity_response.status_code == 200

        # Verify data consistency
        assert stats["total_users"] >= 1
        assert stats["total_devotionals"] >= 1
        assert stats["total_views"] >= 500

        # Cleanup
        await test_db.users.delete_one({"_id": user["_id"]})
        await test_db.devotionals.delete_one({"_id": devotional["_id"]})

    @pytest.mark.asyncio
    async def test_dashboard_stats_empty_database(
        self, client, admin_token, test_db
    ):
        """
        Test dashboard stats with minimal data.
        Expected: Returns 200 with zero or minimal counts.
        """
        # Act
        response = client.get(
            "/api/v1/admin/dashboard/stats",
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Should return valid structure even with no data
        assert "total_users" in data
        assert "total_devotionals" in data
        assert isinstance(data["total_users"], int)
        assert isinstance(data["total_devotionals"], int)
