"""
Integration tests for Community Features.

Tests submissions, validations, leaderboards, achievements,
and community governance with real MongoDB connections.

TASK-007: Execute community features integration tests

All community, submit, validate, and governance endpoints are now implemented.
"""

import pytest
from datetime import datetime, timedelta
from bson import ObjectId
import uuid

pytestmark = [
    pytest.mark.integration,
    pytest.mark.api,
]


class TestSubmissions:
    """Test community submission workflows."""

    async def test_submit_text_content(
        self, api_client, dev_auth_headers, seeded_language, real_test_db
    ):
        """Test submitting text content to the community."""
        submission_data = {
            "language_code": seeded_language["code"],
            "language_family": "niger-congo",
            "type": "text",
            "category": "proverb",
            "title": "Traditional Akan Proverb",
            "description": "A wisdom saying in Twi",
            "text_content": "Obi nkyere akwadaa Nyame - No one teaches a child about God",
            "translation": "God is known to all, even children",
            "source_attribution": "Traditional folklore",
            "cultural_context": "Used to express universal truths"
        }

        response = await api_client.post(
            "/api/v1/submit/text",
            json=submission_data,
            headers=dev_auth_headers
        )

        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        response_data = response.json()

        # DataResponse wraps the submission in 'data' key
        submission = response_data.get("data", response_data)

        # Verify response
        assert submission.get("type") == "text"
        assert submission.get("language_code") == seeded_language["code"]
        assert submission.get("tier") == "tier-3-submitted"
        assert submission.get("validation_status") == "pending"

        # Verify persisted (if ID is in response)
        if "id" in submission or "_id" in submission:
            sub_id = submission.get("id") or submission.get("_id")
            db_submission = await real_test_db.submissions.find_one({"_id": ObjectId(sub_id)})
            assert db_submission is not None

    async def test_submit_link_content(
        self, api_client, dev_auth_headers, seeded_language, real_test_db
    ):
        """Test submitting external link."""
        submission_data = {
            "language_code": seeded_language["code"],
            "language_family": "niger-congo",
            "type": "link",
            "category": "educational",
            "title": "Twi Learning Resource",
            "description": "Online resource for learning Twi",
            "external_url": "https://example.com/learn-twi",
            "source_attribution": "Example Language Institute"
        }

        response = await api_client.post(
            "/api/v1/submit/link",
            json=submission_data,
            headers=dev_auth_headers
        )

        assert response.status_code in [200, 201]
        response_data = response.json()
        submission = response_data.get("data", response_data)
        assert submission.get("type") == "link"

    async def test_submit_without_auth_fails(self, api_client, seeded_language):
        """Test that submission without authentication fails."""
        submission_data = {
            "language_code": seeded_language["code"],
            "type": "text",
            "category": "proverb",
            "title": "Unauthorized submission"
        }

        response = await api_client.post("/api/v1/submit/text", json=submission_data)
        assert response.status_code == 403

    async def test_get_submission_history(
        self, api_client, dev_auth_headers, seeded_language, real_test_db
    ):
        """Test getting user's submission history."""
        # Create a submission first
        submission_data = {
            "language_code": seeded_language["code"],
            "language_family": "niger-congo",
            "type": "text",
            "category": "story",
            "title": "Test Story",
            "text_content": "Once upon a time...",
            "source_attribution": "Test"
        }
        await api_client.post(
            "/api/v1/submit/text",
            json=submission_data,
            headers=dev_auth_headers
        )

        # Get history
        response = await api_client.get(
            "/api/v1/submit/history",
            headers=dev_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # ListResponse uses 'items' key
        assert "items" in data or "submissions" in data
        items = data.get("items", data.get("submissions", []))
        assert len(items) >= 1


class TestValidation:
    """Test community validation workflows."""

    @pytest.fixture
    async def pending_submission(
        self, real_test_db, test_user_id, seeded_language
    ):
        """Create a pending submission for validation testing."""
        submission_doc = {
            "_id": ObjectId(),
            "contributor_id": str(ObjectId()),  # Different user
            "language_family": "niger-congo",
            "language_code": seeded_language["code"],
            "type": "text",
            "category": "proverb",
            "title": "Pending Proverb",
            "text_content": "Test proverb content",
            "tier": "tier-3-submitted",
            "validation_status": "pending",
            "quality_scores": {},
            "validations": [],
            "created_at": datetime.utcnow()
        }
        await real_test_db.submissions.insert_one(submission_doc)
        return submission_doc

    async def test_get_pending_validations(
        self, api_client, pending_submission, dev_auth_headers
    ):
        """Test getting pending validations queue."""
        response = await api_client.get(
            "/api/v1/validate/pending",
            headers=dev_auth_headers
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "items" in data or "submissions" in data or "pending" in data

    async def test_submit_validation(
        self, api_client, pending_submission, dev_auth_headers, real_test_db
    ):
        """Test submitting a validation for a submission."""
        submission_id = str(pending_submission["_id"])

        validation_data = {
            "submission_id": submission_id,
            "submission_type": "text",
            "action": "approve",
            "category": "content_quality",
            "quality_rating": 4,
            "confidence_level": 0.85,
            "comments": "Good proverb with accurate translation"
        }

        response = await api_client.post(
            f"/api/v1/validate/{submission_id}",
            json=validation_data,
            headers=dev_auth_headers
        )

        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"

        # Verify validation recorded
        validation = await real_test_db.validations.find_one({
            "submission_id": ObjectId(submission_id)
        })
        assert validation is not None

    async def test_get_validator_stats(self, api_client, dev_auth_headers):
        """Test getting validator statistics."""
        response = await api_client.get(
            "/api/v1/validate/stats/validator",
            headers=dev_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # DataResponse wraps data in "data" key
        inner_data = data.get("data", data)
        assert "total_validations" in inner_data or "validations_count" in inner_data

    async def test_get_my_reviews(self, api_client, dev_auth_headers):
        """Test getting user's validation reviews."""
        response = await api_client.get(
            "/api/v1/validate/my-reviews",
            headers=dev_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # ListResponse uses 'items' key
        assert "items" in data or "reviews" in data or "validations" in data


class TestLeaderboard:
    """Test community leaderboard functionality."""

    @pytest.fixture
    async def leaderboard_users(self, real_test_db):
        """Create users with different point totals for leaderboard."""
        users = []
        for i, points in enumerate([1000, 500, 250, 100, 50]):
            user_doc = {
                "_id": ObjectId(),
                "email": f"leaderboard{i}@example.com",
                "username": f"leader{i}",
                "full_name": f"Leaderboard User {i}",
                "total_points": points,
                "level": "expert" if points >= 500 else "contributor",
                "contributions_count": points // 10,
                "validations_count": points // 20,
                "is_active": True,
                "created_at": datetime.utcnow()
            }
            await real_test_db.users.insert_one(user_doc)
            users.append(user_doc)
        return users

    async def test_get_global_leaderboard(self, api_client, leaderboard_users):
        """Test getting global leaderboard."""
        response = await api_client.get("/api/v1/community/leaderboard")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data  # ListResponse uses 'items' key

        # Verify sorted by points (descending)
        if len(data["items"]) >= 2:
            points = [u.get("total_points", 0) for u in data["items"]]
            assert points == sorted(points, reverse=True)

    async def test_get_leaderboard_by_language(
        self, api_client, seeded_language, leaderboard_users
    ):
        """Test getting leaderboard filtered by language."""
        response = await api_client.get(
            "/api/v1/community/leaderboard",
            params={"language": seeded_language["code"]}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    async def test_get_leaderboard_by_family(self, api_client, leaderboard_users):
        """Test getting leaderboard filtered by language family."""
        response = await api_client.get(
            "/api/v1/community/leaderboard",
            params={"family": "niger-congo"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestAchievements:
    """Test community achievements system."""

    @pytest.fixture
    async def achievement_types(self, real_test_db):
        """Create achievement types for testing."""
        achievements = [
            {
                "_id": ObjectId(),
                "code": "first_submission",
                "name": "First Steps",
                "description": "Submit your first contribution",
                "icon": "star",
                "points_awarded": 50,
                "criteria": {"submissions_count": 1},
                "created_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "code": "validator_novice",
                "name": "Validator Novice",
                "description": "Complete 10 validations",
                "icon": "check",
                "points_awarded": 100,
                "criteria": {"validations_count": 10},
                "created_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "code": "language_guardian",
                "name": "Language Guardian",
                "description": "Become an expert in a language",
                "icon": "shield",
                "points_awarded": 500,
                "criteria": {"verified_languages_count": 1},
                "created_at": datetime.utcnow()
            }
        ]
        await real_test_db.achievements.insert_many(achievements)
        return achievements

    async def test_get_all_achievements(self, api_client, achievement_types):
        """Test getting all available achievements."""
        response = await api_client.get("/api/v1/community/achievements")

        assert response.status_code == 200
        data = response.json()
        # DataResponse wraps data in "data" key
        inner_data = data.get("data", data)
        assert "achievements" in inner_data
        assert len(inner_data["achievements"]) >= 3

    async def test_get_user_achievements(
        self, api_client, dev_auth_headers, achievement_types
    ):
        """Test getting user's earned achievements."""
        response = await api_client.get(
            "/api/v1/community/achievements/user",
            headers=dev_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # DataResponse wraps data in "data" key
        inner_data = data.get("data", data)
        assert "earned" in inner_data or "achievements" in inner_data


class TestActivityFeed:
    """Test community activity feed."""

    @pytest.fixture
    async def activity_events(self, real_test_db, test_user_id):
        """Create activity events for testing."""
        events = []
        for i, activity_type in enumerate(["submission", "validation", "achievement"]):
            event_doc = {
                "_id": ObjectId(),
                "user_id": test_user_id,
                "activity_type": activity_type,
                "title": f"Test {activity_type}",
                "description": f"User completed a {activity_type}",
                "metadata": {},
                "points_awarded": 10 * (i + 1),
                "created_at": datetime.utcnow()
            }
            await real_test_db.activity_feed.insert_one(event_doc)
            events.append(event_doc)
        return events

    async def test_get_activity_feed(self, api_client, activity_events):
        """Test getting community activity feed."""
        response = await api_client.get("/api/v1/community/activity/feed")

        assert response.status_code == 200
        data = response.json()
        # ListResponse returns "items" key
        assert "items" in data or "activities" in data or "feed" in data

    async def test_get_activity_feed_by_language(
        self, api_client, activity_events, seeded_language
    ):
        """Test getting activity feed filtered by language."""
        response = await api_client.get(
            "/api/v1/community/activity/feed",
            params={"language": seeded_language["code"]}
        )

        assert response.status_code == 200


class TestCommunityChannels:
    """Test community language channels."""

    @pytest.fixture
    async def language_channels(self, real_test_db, seeded_language):
        """Create language channels for testing."""
        channels = [
            {
                "_id": ObjectId(),
                "language_code": seeded_language["code"],
                "name": f"{seeded_language['name']} Community",
                "description": "Community channel for Twi speakers",
                "member_count": 150,
                "is_active": True,
                "created_at": datetime.utcnow()
            }
        ]
        await real_test_db.community_channels.insert_many(channels)
        return channels

    async def test_get_language_channels(self, api_client, language_channels):
        """Test getting language channels."""
        response = await api_client.get("/api/v1/community/channels")

        assert response.status_code == 200
        data = response.json()
        # DataResponse wraps data, channels are in data.data.channels
        assert "data" in data
        assert "channels" in data["data"]

    async def test_get_channel_by_language(
        self, api_client, language_channels, seeded_language
    ):
        """Test getting specific language channel."""
        response = await api_client.get(
            f"/api/v1/community/channels/{seeded_language['code']}"
        )

        assert response.status_code in [200, 404]


class TestCommunityStats:
    """Test community statistics endpoints."""

    async def test_get_engagement_stats(self, api_client):
        """Test getting community engagement statistics."""
        response = await api_client.get("/api/v1/community/stats/engagement")

        assert response.status_code == 200
        data = response.json()
        # Should include various engagement metrics
        assert isinstance(data, dict)

    async def test_get_language_stats(self, api_client, seeded_language):
        """Test getting language-specific statistics."""
        response = await api_client.get(
            f"/api/v1/community/languages/{seeded_language['code']}/stats"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestProposals:
    """Test community proposal system."""

    async def test_create_proposal(
        self, api_client, dev_auth_headers, real_test_db
    ):
        """Test creating a community proposal."""
        proposal_data = {
            "title": "Add Fante Dialect Support",
            "description": "Proposal to add Fante dialect as a separate language option",
            "proposal_type": "language_addition",
            "details": {
                "language_code": "fat",
                "family": "niger-congo",
                "region": "Ghana"
            }
        }

        response = await api_client.post(
            "/api/v1/community/proposals",
            json=proposal_data,
            headers=dev_auth_headers
        )

        assert response.status_code in [200, 201]
        data = response.json()
        # DataResponse wraps data in "data" key
        inner_data = data.get("data", data)
        assert inner_data["title"] == proposal_data["title"]

    async def test_vote_on_proposal(
        self, api_client, dev_auth_headers, real_test_db
    ):
        """Test voting on a proposal."""
        # Create proposal first with future voting deadline
        proposal_doc = {
            "_id": ObjectId(),
            "title": "Test Proposal",
            "description": "Test description",
            "proposal_type": "feature",
            "status": "active",
            "votes_for": 0,
            "votes_against": 0,
            "voters": [],  # Ensure empty voters list
            "proposer_id": "test-user",
            "voting_deadline": datetime.utcnow() + timedelta(days=7),  # Future deadline
            "created_at": datetime.utcnow()
        }
        await real_test_db.community_proposals.insert_one(proposal_doc)

        # Vote
        response = await api_client.post(
            f"/api/v1/community/proposals/{str(proposal_doc['_id'])}/vote",
            json={"vote": "for"},
            headers=dev_auth_headers
        )

        assert response.status_code in [200, 201]


class TestGovernance:
    """Test community governance features."""

    async def test_get_moderation_dashboard(
        self, api_client, dev_auth_headers
    ):
        """Test getting moderation dashboard."""
        response = await api_client.get(
            "/api/v1/governance/moderation/dashboard",
            headers=dev_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    async def test_get_community_guidelines(self, api_client):
        """Test getting community guidelines."""
        response = await api_client.get("/api/v1/governance/guidelines")

        assert response.status_code == 200
        data = response.json()
        assert "guidelines" in data or isinstance(data, dict)

    async def test_get_disputes(self, api_client, dev_auth_headers):
        """Test getting open disputes."""
        response = await api_client.get(
            "/api/v1/governance/disputes",
            headers=dev_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # ListResponse returns "items" key
        assert "items" in data or "disputes" in data or isinstance(data, list)


class TestUserProfile:
    """Test user profile endpoints."""

    async def test_get_user_statistics(self, api_client, dev_auth_headers):
        """Test getting user statistics."""
        response = await api_client.get(
            "/api/v1/auth/statistics",
            headers=dev_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # DataResponse wraps data in "data" key
        inner_data = data.get("data", data)
        # Returns empty dict if user not found, or stats if found
        assert isinstance(inner_data, dict)

    async def test_get_user_activities(self, api_client, dev_auth_headers):
        """Test getting user activity history."""
        response = await api_client.get(
            "/api/v1/auth/activities",
            headers=dev_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # DataResponse wraps data in "data" key
        inner_data = data.get("data", data)
        assert "activities" in inner_data or isinstance(inner_data, list)

    async def test_update_user_goals(
        self, api_client, dev_auth_headers, real_test_db
    ):
        """Test updating user weekly goals."""
        goals_data = {
            "submissions_target": 10,
            "validations_target": 20
        }

        response = await api_client.put(
            "/api/v1/auth/goals",
            json=goals_data,
            headers=dev_auth_headers
        )

        assert response.status_code == 200


class TestPerformance:
    """Test API performance requirements."""

    async def test_leaderboard_response_time(self, api_client, measure_time):
        """Test that leaderboard responds within acceptable time."""
        with measure_time() as timer:
            response = await api_client.get("/api/v1/community/leaderboard")

        assert response.status_code == 200
        assert timer.elapsed < 1.0, f"Response took {timer.elapsed:.2f}s, expected < 1s"

    async def test_activity_feed_response_time(self, api_client, measure_time):
        """Test that activity feed responds quickly."""
        with measure_time() as timer:
            response = await api_client.get("/api/v1/community/activity/feed")

        assert response.status_code == 200
        assert timer.elapsed < 1.0, f"Response took {timer.elapsed:.2f}s, expected < 1s"

    async def test_validation_queue_response_time(
        self, api_client, dev_auth_headers, measure_time
    ):
        """Test that validation queue responds quickly."""
        with measure_time() as timer:
            response = await api_client.get(
                "/api/v1/validate/pending",
                headers=dev_auth_headers
            )

        assert response.status_code == 200
        assert timer.elapsed < 1.0, f"Response took {timer.elapsed:.2f}s, expected < 1s"
