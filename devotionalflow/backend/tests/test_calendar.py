"""
Tests for Calendar View API endpoints.

Tests cover:
- GET /api/v1/calendar/devotionals - Calendar view with date filters
- GET /api/v1/calendar/gaps - Find date gaps
- GET /api/v1/calendar/upcoming - Get upcoming devotionals
- GET /api/v1/calendar/stats - Get publishing statistics
"""

import pytest
from datetime import datetime, timedelta, date
from bson import ObjectId
from tests.conftest import create_auth_header


class TestCalendarView:
    """Test suite for calendar view functionality."""

    @pytest.mark.asyncio
    async def test_get_calendar_devotionals_success(
        self, client, admin_token, test_db
    ):
        """
        Test retrieving devotionals in calendar view.
        Expected: Returns 200 with devotionals grouped by date.
        """
        # Arrange - Create devotionals across different dates
        today = datetime.utcnow()
        devotionals = [
            {
                "_id": ObjectId(),
                "title": f"Test Devotional {i}",
                "content": f"Content {i}",
                "author_id": "693acf37d221b83bb8f2d2a7",
                "status": "published",
                "scheduled_date": today + timedelta(days=i),
                "created_at": today,
                "published_at": today + timedelta(days=i)
            }
            for i in range(5)
        ]

        await test_db.devotionals.insert_many(devotionals)

        # Act
        response = client.get(
            "/api/v1/calendar/devotionals",
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "devotionals" in data
        assert "total" in data

        # Verify devotionals are returned
        assert len(data["devotionals"]) >= 5

        # Cleanup
        await test_db.devotionals.delete_many({
            "_id": {"$in": [d["_id"] for d in devotionals]}
        })

    @pytest.mark.asyncio
    async def test_calendar_with_date_range(
        self, client, admin_token, test_db
    ):
        """
        Test calendar view with specific date range.
        Expected: Returns only devotionals within the date range.
        """
        # Arrange
        today = date.today()
        start_date = today
        end_date = today + timedelta(days=7)

        # Create devotionals - some in range, some out
        in_range_date = datetime.combine(today + timedelta(days=3), datetime.min.time())
        out_range_date = datetime.combine(today + timedelta(days=10), datetime.min.time())

        devotional_in = {
            "_id": ObjectId(),
            "title": "Test In Range",
            "content": "Content",
            "author_id": "693acf37d221b83bb8f2d2a7",
            "status": "published",
            "scheduled_date": in_range_date,
            "created_at": datetime.utcnow(),
            "published_at": in_range_date
        }

        devotional_out = {
            "_id": ObjectId(),
            "title": "Test Out Range",
            "content": "Content",
            "author_id": "693acf37d221b83bb8f2d2a7",
            "status": "published",
            "scheduled_date": out_range_date,
            "created_at": datetime.utcnow(),
            "published_at": out_range_date
        }

        await test_db.devotionals.insert_many([devotional_in, devotional_out])

        # Act
        response = client.get(
            f"/api/v1/calendar/devotionals?start_date={start_date}&end_date={end_date}",
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Should include devotional_in
        titles = [d["title"] for d in data["devotionals"]]
        assert "Test In Range" in titles

        # Cleanup
        await test_db.devotionals.delete_many({
            "_id": {"$in": [devotional_in["_id"], devotional_out["_id"]]}
        })

    @pytest.mark.asyncio
    async def test_calendar_with_status_filter(
        self, client, admin_token, test_db
    ):
        """
        Test calendar view filtered by status.
        Expected: Returns only devotionals with specified status.
        """
        # Arrange
        today = datetime.utcnow()

        published = {
            "_id": ObjectId(),
            "title": "Test Published",
            "content": "Content",
            "author_id": "693acf37d221b83bb8f2d2a7",
            "status": "published",
            "scheduled_date": today,
            "created_at": today,
            "published_at": today
        }

        draft = {
            "_id": ObjectId(),
            "title": "Test Draft",
            "content": "Content",
            "author_id": "693acf37d221b83bb8f2d2a7",
            "status": "draft",
            "scheduled_date": today + timedelta(days=1),
            "created_at": today
        }

        await test_db.devotionals.insert_many([published, draft])

        # Act - Filter for published only
        response = client.get(
            "/api/v1/calendar/devotionals?status=published",
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # All returned devotionals should be published
        for dev in data["devotionals"]:
            if dev["title"] in ["Test Published", "Test Draft"]:
                assert dev["status"] == "published"

        # Cleanup
        await test_db.devotionals.delete_many({
            "_id": {"$in": [published["_id"], draft["_id"]]}
        })

    @pytest.mark.asyncio
    async def test_find_schedule_gaps(
        self, client, admin_token, test_db
    ):
        """
        Test finding gaps in devotional schedule.
        Expected: Returns dates without published devotionals.
        """
        # Arrange - Create devotionals with gaps
        today = datetime.utcnow()

        # Day 0 and Day 2 have devotionals, Day 1 is a gap
        devotionals = [
            {
                "_id": ObjectId(),
                "title": "Day 0 Devotional",
                "content": "Content",
                "author_id": "693acf37d221b83bb8f2d2a7",
                "status": "published",
                "scheduled_date": today,
                "published_at": today,
                "created_at": today
            },
            {
                "_id": ObjectId(),
                "title": "Day 2 Devotional",
                "content": "Content",
                "author_id": "693acf37d221b83bb8f2d2a7",
                "status": "published",
                "scheduled_date": today + timedelta(days=2),
                "published_at": today + timedelta(days=2),
                "created_at": today
            }
        ]

        await test_db.devotionals.insert_many(devotionals)

        # Act
        start_date = today.date()
        end_date = (today + timedelta(days=2)).date()

        response = client.get(
            f"/api/v1/calendar/gaps?start_date={start_date}&end_date={end_date}",
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "gaps" in data
        assert "total_gaps" in data

        # Should find at least 1 gap (Day 1)
        gap_dates = [g["date"] for g in data["gaps"]]
        expected_gap = (today + timedelta(days=1)).date().isoformat()
        assert expected_gap in gap_dates

        # Cleanup
        await test_db.devotionals.delete_many({
            "_id": {"$in": [d["_id"] for d in devotionals]}
        })

    @pytest.mark.asyncio
    async def test_gaps_with_no_gaps(
        self, client, admin_token, test_db
    ):
        """
        Test gap detection when schedule is complete.
        Expected: Returns empty gaps list.
        """
        # Arrange - Create devotionals for consecutive days
        today = datetime.utcnow()

        devotionals = [
            {
                "_id": ObjectId(),
                "title": f"Day {i} Devotional",
                "content": "Content",
                "author_id": "693acf37d221b83bb8f2d2a7",
                "status": "published",
                "scheduled_date": today + timedelta(days=i),
                "published_at": today + timedelta(days=i),
                "created_at": today
            }
            for i in range(3)  # Days 0, 1, 2
        ]

        await test_db.devotionals.insert_many(devotionals)

        # Act
        start_date = today.date()
        end_date = (today + timedelta(days=2)).date()

        response = client.get(
            f"/api/v1/calendar/gaps?start_date={start_date}&end_date={end_date}",
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Should have no gaps in our date range
        assert data["total_gaps"] == 0
        assert len(data["gaps"]) == 0

        # Cleanup
        await test_db.devotionals.delete_many({
            "_id": {"$in": [d["_id"] for d in devotionals]}
        })

    @pytest.mark.asyncio
    async def test_get_upcoming_devotionals(
        self, client, admin_token, test_db
    ):
        """
        Test retrieving upcoming devotionals.
        Expected: Returns devotionals scheduled for future dates.
        """
        # Arrange
        today = datetime.utcnow()
        future_date = today + timedelta(days=7)

        upcoming_dev = {
            "_id": ObjectId(),
            "title": "Test Upcoming Devotional",
            "content": "Content",
            "author_id": "693acf37d221b83bb8f2d2a7",
            "status": "scheduled",
            "scheduled_date": future_date,
            "created_at": today
        }

        await test_db.devotionals.insert_one(upcoming_dev)

        # Act
        response = client.get(
            "/api/v1/calendar/upcoming?days=30",
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "devotionals" in data
        assert "total" in data
        assert "next_30_days" in data

        # Should include our upcoming devotional
        titles = [d["title"] for d in data["devotionals"]]
        assert "Test Upcoming Devotional" in titles

        # Cleanup
        await test_db.devotionals.delete_one({"_id": upcoming_dev["_id"]})

    @pytest.mark.asyncio
    async def test_upcoming_with_limit(
        self, client, admin_token, test_db
    ):
        """
        Test upcoming devotionals with limit parameter.
        Expected: Returns limited number of devotionals.
        """
        # Arrange - Create multiple upcoming devotionals
        today = datetime.utcnow()

        devotionals = [
            {
                "_id": ObjectId(),
                "title": f"Test Upcoming {i}",
                "content": "Content",
                "author_id": "693acf37d221b83bb8f2d2a7",
                "status": "scheduled",
                "scheduled_date": today + timedelta(days=i+1),
                "created_at": today
            }
            for i in range(10)
        ]

        await test_db.devotionals.insert_many(devotionals)

        # Act - Request only 5
        response = client.get(
            "/api/v1/calendar/upcoming?days=30&limit=5",
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Should return at most 5
        test_upcoming = [d for d in data["devotionals"] if d["title"].startswith("Test Upcoming")]
        assert len(test_upcoming) <= 5

        # Cleanup
        await test_db.devotionals.delete_many({
            "_id": {"$in": [d["_id"] for d in devotionals]}
        })

    @pytest.mark.asyncio
    async def test_get_calendar_stats(
        self, client, admin_token, test_db
    ):
        """
        Test retrieving calendar statistics.
        Expected: Returns publishing statistics.
        """
        # Arrange - Create devotionals for stats
        today = datetime.utcnow()

        devotionals = [
            {
                "_id": ObjectId(),
                "title": f"Test Stats {i}",
                "content": "Content",
                "author_id": "693acf37d221b83bb8f2d2a7",
                "status": "published",
                "scheduled_date": today - timedelta(days=i),
                "published_at": today - timedelta(days=i),
                "created_at": today - timedelta(days=i)
            }
            for i in range(5)
        ]

        await test_db.devotionals.insert_many(devotionals)

        # Act
        response = client.get(
            "/api/v1/calendar/stats",
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "total_published" in data
        assert "this_month" in data
        assert "this_week" in data
        assert "today" in data
        assert "upcoming_scheduled" in data
        assert "publishing_streak" in data

        # Should count our test devotionals
        assert data["total_published"] >= 5

        # Cleanup
        await test_db.devotionals.delete_many({
            "_id": {"$in": [d["_id"] for d in devotionals]}
        })

    @pytest.mark.asyncio
    async def test_calendar_stats_time_periods(
        self, client, admin_token, test_db
    ):
        """
        Test calendar stats for different time periods.
        Expected: Correctly counts devotionals by period.
        """
        # Arrange
        today = datetime.utcnow()

        # Create devotionals in different time periods
        today_dev = {
            "_id": ObjectId(),
            "title": "Test Today",
            "content": "Content",
            "author_id": "693acf37d221b83bb8f2d2a7",
            "status": "published",
            "scheduled_date": today,
            "published_at": today,
            "created_at": today
        }

        last_week_dev = {
            "_id": ObjectId(),
            "title": "Test Last Week",
            "content": "Content",
            "author_id": "693acf37d221b83bb8f2d2a7",
            "status": "published",
            "scheduled_date": today - timedelta(days=7),
            "published_at": today - timedelta(days=7),
            "created_at": today - timedelta(days=7)
        }

        await test_db.devotionals.insert_many([today_dev, last_week_dev])

        # Act
        response = client.get(
            "/api/v1/calendar/stats",
            headers=create_auth_header(admin_token)
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Today count should be at least 1
        assert data["today"] >= 1

        # This week should include both
        assert data["this_week"] >= 2

        # Cleanup
        await test_db.devotionals.delete_many({
            "_id": {"$in": [today_dev["_id"], last_week_dev["_id"]]}
        })

    @pytest.mark.asyncio
    async def test_calendar_without_auth(self, client):
        """
        Test accessing calendar endpoints without authentication.
        Expected: Returns 401.
        """
        # Act
        endpoints = [
            "/api/v1/calendar/devotionals",
            "/api/v1/calendar/gaps",
            "/api/v1/calendar/upcoming",
            "/api/v1/calendar/stats"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            # Assert
            assert response.status_code == 401, f"Failed for {endpoint}"

    @pytest.mark.asyncio
    async def test_calendar_complete_workflow(
        self, client, admin_token, test_db
    ):
        """
        Test complete calendar workflow: view -> gaps -> upcoming -> stats.
        Expected: All operations succeed and data is consistent.
        """
        # Arrange - Create test data
        today = datetime.utcnow()

        devotionals = [
            {
                "_id": ObjectId(),
                "title": f"Workflow Test {i}",
                "content": "Content",
                "author_id": "693acf37d221b83bb8f2d2a7",
                "status": "published" if i < 3 else "scheduled",
                "scheduled_date": today + timedelta(days=i),
                "published_at": today + timedelta(days=i) if i < 3 else None,
                "created_at": today
            }
            for i in range(5)
        ]

        await test_db.devotionals.insert_many(devotionals)

        # Step 1: Get calendar view
        calendar_response = client.get(
            "/api/v1/calendar/devotionals",
            headers=create_auth_header(admin_token)
        )
        assert calendar_response.status_code == 200

        # Step 2: Check for gaps
        start_date = today.date()
        end_date = (today + timedelta(days=10)).date()

        gaps_response = client.get(
            f"/api/v1/calendar/gaps?start_date={start_date}&end_date={end_date}",
            headers=create_auth_header(admin_token)
        )
        assert gaps_response.status_code == 200

        # Step 3: Get upcoming
        upcoming_response = client.get(
            "/api/v1/calendar/upcoming?days=30",
            headers=create_auth_header(admin_token)
        )
        assert upcoming_response.status_code == 200

        # Step 4: Get stats
        stats_response = client.get(
            "/api/v1/calendar/stats",
            headers=create_auth_header(admin_token)
        )
        assert stats_response.status_code == 200

        # Verify consistency
        stats_data = stats_response.json()
        assert stats_data["total_published"] >= 3
        assert stats_data["upcoming_scheduled"] >= 2

        # Cleanup
        await test_db.devotionals.delete_many({
            "_id": {"$in": [d["_id"] for d in devotionals]}
        })
