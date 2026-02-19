"""
Unit tests for analytics service.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.analytics_service import AnalyticsService


class TestAnalyticsService:
    """Test suite for AnalyticsService."""

    @pytest.mark.asyncio
    async def test_get_dashboard_stats(self):
        """Test getting dashboard statistics."""
        with patch('app.services.analytics_service.mongodb') as mock_mongodb:
            # Mock collections
            mock_users = MagicMock()
            mock_sessions = MagicMock()
            mock_questions = MagicMock()
            mock_materials = MagicMock()

            # Mock count_documents calls
            mock_users.count_documents = AsyncMock(side_effect=[
                100,  # total users
                15,   # new users
                10, 40, 30, 20  # users by role (admin, student, parent, teacher)
            ])

            mock_sessions.count_documents = AsyncMock(side_effect=[500, 75])
            mock_questions.count_documents = AsyncMock(side_effect=[2000, 300])
            mock_materials.count_documents = AsyncMock(side_effect=[50, 10])

            # Mock aggregate calls
            session_agg_cursor = MagicMock()
            session_agg_cursor.to_list = AsyncMock(return_value=[{
                "avg_duration": 25.5,
                "total_duration": 12750
            }])
            mock_sessions.aggregate.return_value = session_agg_cursor

            question_agg_cursor = MagicMock()
            question_agg_cursor.to_list = AsyncMock(return_value=[{
                "avg_confidence": 0.85
            }])
            mock_questions.aggregate.return_value = question_agg_cursor

            materials_agg_cursor = MagicMock()
            materials_agg_cursor.to_list = AsyncMock(return_value=[
                {"_id": "Mathematics", "count": 20},
                {"_id": "Science", "count": 15}
            ])
            mock_materials.aggregate.return_value = materials_agg_cursor

            def get_collection(name):
                if "users" in name:
                    return mock_users
                elif "sessions" in name:
                    return mock_sessions
                elif "questions" in name:
                    return mock_questions
                elif "materials" in name:
                    return mock_materials
                return MagicMock()

            mock_mongodb.get_collection.side_effect = get_collection

            # Call the method
            stats = await AnalyticsService.get_dashboard_stats()

            # Assertions
            assert stats["users"]["total"] == 100
            assert stats["users"]["new_in_period"] == 15
            assert stats["sessions"]["total"] == 500
            assert stats["sessions"]["in_period"] == 75
            assert stats["questions"]["total"] == 2000
            assert stats["materials"]["total"] == 50
            assert len(stats["materials"]["by_subject"]) == 2

    @pytest.mark.asyncio
    async def test_get_user_metrics(self):
        """Test getting user engagement metrics."""
        with patch('app.services.analytics_service.mongodb') as mock_mongodb:
            mock_users = MagicMock()
            mock_sessions = MagicMock()

            # Mock user count
            mock_users.count_documents = AsyncMock(return_value=100)

            # Mock new users aggregation
            new_users_cursor = MagicMock()
            new_users_cursor.to_list = AsyncMock(return_value=[
                {"_id": "2025-10-20", "count": 5},
                {"_id": "2025-10-21", "count": 3}
            ])
            mock_users.aggregate.return_value = new_users_cursor

            # Mock active users aggregation
            active_users_cursor = MagicMock()
            active_users_cursor.to_list = AsyncMock(return_value=[
                {"_id": "user1", "session_count": 12, "total_questions": 50},
                {"_id": "user2", "session_count": 7, "total_questions": 30},
                {"_id": "user3", "session_count": 3, "total_questions": 10}
            ])
            mock_sessions.aggregate.return_value = active_users_cursor

            def get_collection(name):
                if "users" in name:
                    return mock_users
                elif "sessions" in name:
                    return mock_sessions
                return MagicMock()

            mock_mongodb.get_collection.side_effect = get_collection

            # Call the method
            metrics = await AnalyticsService.get_user_metrics(days=7)

            # Assertions
            assert metrics["total_users"] == 100
            assert metrics["active_users"] == 3
            assert metrics["activity_rate_percent"] == 3.0
            assert metrics["engagement_levels"]["highly_engaged"] == 1  # user1
            assert metrics["engagement_levels"]["moderately_engaged"] == 1  # user2
            assert metrics["engagement_levels"]["lightly_engaged"] == 1  # user3

    @pytest.mark.asyncio
    async def test_get_content_analytics(self):
        """Test getting content analytics."""
        with patch('app.services.analytics_service.mongodb') as mock_mongodb:
            mock_questions = MagicMock()
            mock_materials = MagicMock()

            # Mock subject stats aggregation
            subject_cursor = MagicMock()
            subject_cursor.to_list = AsyncMock(return_value=[
                {
                    "_id": "Mathematics",
                    "question_count": 100,
                    "avg_confidence": 0.85,
                    "avg_response_time_ms": 1500
                },
                {
                    "_id": "Science",
                    "question_count": 80,
                    "avg_confidence": 0.78,
                    "avg_response_time_ms": 1800
                }
            ])

            # Mock topic stats aggregation
            topic_cursor = MagicMock()
            topic_cursor.to_list = AsyncMock(return_value=[
                {
                    "_id": {"subject": "Mathematics", "topic": "Algebra"},
                    "question_count": 50,
                    "avg_confidence": 0.82
                }
            ])

            # Mock low confidence aggregation
            low_conf_cursor = MagicMock()
            low_conf_cursor.to_list = AsyncMock(return_value=[
                {
                    "_id": "Physics",
                    "low_confidence_count": 15,
                    "avg_confidence": 0.55
                }
            ])

            # Mock material uploads aggregation
            materials_cursor = MagicMock()
            materials_cursor.to_list = AsyncMock(return_value=[
                {"_id": "2025-10-20", "count": 5}
            ])

            # Setup aggregation returns
            aggregate_calls = [subject_cursor, topic_cursor, low_conf_cursor, materials_cursor]
            aggregate_idx = [0]

            def mock_aggregate(pipeline):
                result = aggregate_calls[aggregate_idx[0]]
                aggregate_idx[0] += 1
                return result

            mock_questions.aggregate = mock_aggregate
            mock_materials.aggregate.return_value = materials_cursor

            def get_collection(name):
                if "questions" in name:
                    return mock_questions
                elif "materials" in name:
                    return mock_materials
                return MagicMock()

            mock_mongodb.get_collection.side_effect = get_collection

            # Call the method
            analytics = await AnalyticsService.get_content_analytics(days=7)

            # Assertions
            assert len(analytics["popular_subjects"]) == 2
            assert analytics["popular_subjects"][0]["subject"] == "Mathematics"
            assert analytics["popular_subjects"][0]["question_count"] == 100
            assert len(analytics["popular_topics"]) == 1
            assert len(analytics["low_confidence_areas"]) == 1

    @pytest.mark.asyncio
    async def test_get_system_health(self):
        """Test getting system health metrics."""
        with patch('app.services.analytics_service.mongodb') as mock_mongodb:
            # Mock collections
            mock_users = MagicMock()
            mock_sessions = MagicMock()
            mock_questions = MagicMock()
            mock_materials = MagicMock()

            # Mock count_documents
            mock_users.count_documents = AsyncMock(return_value=100)
            mock_sessions.count_documents = AsyncMock(side_effect=[500, 75])
            mock_questions.count_documents = AsyncMock(side_effect=[2000, 300, 10])
            mock_materials.count_documents = AsyncMock(side_effect=[50, 10])

            # Mock performance aggregation
            perf_cursor = MagicMock()
            perf_cursor.to_list = AsyncMock(return_value=[{
                "avg_response_time": 1500,
                "min_response_time": 500,
                "max_response_time": 5000
            }])
            mock_questions.aggregate.return_value = perf_cursor

            def get_collection(name):
                if "users" in name:
                    return mock_users
                elif "sessions" in name:
                    return mock_sessions
                elif "questions" in name:
                    return mock_questions
                elif "materials" in name:
                    return mock_materials
                return MagicMock()

            mock_mongodb.get_collection.side_effect = get_collection

            # Call the method
            health = await AnalyticsService.get_system_health()

            # Assertions
            assert health["status"] == "healthy"
            assert health["database"]["users_count"] == 100
            assert health["database"]["sessions_count"] == 500
            assert health["recent_activity_24h"]["sessions_24h"] == 75
            assert health["recent_activity_24h"]["questions_24h"] == 300
            assert health["api_performance"]["avg_response_time_ms"] == 1500

    @pytest.mark.asyncio
    async def test_get_financial_analytics(self):
        """Test getting financial analytics."""
        with patch('app.services.analytics_service.mongodb') as mock_mongodb:
            mock_wallets = MagicMock()
            mock_transactions = MagicMock()

            # Mock wallet stats aggregation
            wallet_cursor = MagicMock()
            wallet_cursor.to_list = AsyncMock(return_value=[{
                "total_balance": 50000.0,
                "avg_balance": 500.0,
                "wallet_count": 100
            }])
            mock_wallets.aggregate.return_value = wallet_cursor

            # Mock transaction count
            mock_transactions.count_documents = AsyncMock(return_value=500)

            # Mock transactions by type aggregation
            type_cursor = MagicMock()
            type_cursor.to_list = AsyncMock(return_value=[
                {"_id": "credit", "count": 300, "total_amount": 30000},
                {"_id": "debit", "count": 200, "total_amount": 10000}
            ])

            # Mock daily transactions aggregation
            daily_cursor = MagicMock()
            daily_cursor.to_list = AsyncMock(return_value=[
                {"_id": "2025-10-20", "count": 50, "total_amount": 5000}
            ])

            # Setup aggregate returns
            aggregate_calls = [type_cursor, daily_cursor]
            aggregate_idx = [0]

            def mock_aggregate(pipeline):
                result = aggregate_calls[aggregate_idx[0]]
                aggregate_idx[0] += 1
                return result

            mock_transactions.aggregate = mock_aggregate

            def get_collection(name):
                if "wallets" in name:
                    return mock_wallets
                elif "transactions" in name:
                    return mock_transactions
                return MagicMock()

            mock_mongodb.get_collection.side_effect = get_collection

            # Call the method
            analytics = await AnalyticsService.get_financial_analytics(days=7)

            # Assertions
            assert analytics["wallet_stats"]["total_balance"] == 50000.0
            assert analytics["wallet_stats"]["wallet_count"] == 100
            assert analytics["transactions"]["total_count"] == 500
            assert len(analytics["transactions"]["by_type"]) == 2

    @pytest.mark.asyncio
    async def test_get_top_users_by_questions(self):
        """Test getting top users by question count."""
        with patch('app.services.analytics_service.mongodb') as mock_mongodb:
            mock_questions = MagicMock()
            mock_users = MagicMock()

            # Mock top users aggregation
            top_cursor = MagicMock()
            top_cursor.to_list = AsyncMock(return_value=[
                {"_id": "user1", "question_count": 100, "avg_confidence": 0.85},
                {"_id": "user2", "question_count": 80, "avg_confidence": 0.78}
            ])
            mock_questions.aggregate.return_value = top_cursor

            # Mock user lookups
            mock_users.find_one = AsyncMock(side_effect=[
                {"supabase_user_id": "user1", "full_name": "John Doe", "email": "john@example.com"},
                {"supabase_user_id": "user2", "full_name": "Jane Smith", "email": "jane@example.com"}
            ])

            def get_collection(name):
                if "questions" in name:
                    return mock_questions
                elif "users" in name:
                    return mock_users
                return MagicMock()

            mock_mongodb.get_collection.side_effect = get_collection

            # Call the method
            top_users = await AnalyticsService.get_top_users(metric="questions", limit=10)

            # Assertions
            assert len(top_users) == 2
            assert top_users[0]["user_id"] == "user1"
            assert top_users[0]["name"] == "John Doe"
            assert top_users[0]["question_count"] == 100

    @pytest.mark.asyncio
    async def test_get_top_users_by_sessions(self):
        """Test getting top users by session count."""
        with patch('app.services.analytics_service.mongodb') as mock_mongodb:
            mock_sessions = MagicMock()
            mock_users = MagicMock()

            # Mock top users aggregation
            top_cursor = MagicMock()
            top_cursor.to_list = AsyncMock(return_value=[
                {"_id": "user1", "session_count": 50, "total_questions": 200}
            ])
            mock_sessions.aggregate.return_value = top_cursor

            # Mock user lookup
            mock_users.find_one = AsyncMock(return_value={
                "supabase_user_id": "user1",
                "full_name": "John Doe",
                "email": "john@example.com"
            })

            def get_collection(name):
                if "sessions" in name:
                    return mock_sessions
                elif "users" in name:
                    return mock_users
                return MagicMock()

            mock_mongodb.get_collection.side_effect = get_collection

            # Call the method
            top_users = await AnalyticsService.get_top_users(metric="sessions", limit=10)

            # Assertions
            assert len(top_users) == 1
            assert top_users[0]["session_count"] == 50

    @pytest.mark.asyncio
    async def test_get_top_users_by_learning_time(self):
        """Test getting top users by learning time."""
        with patch('app.services.analytics_service.mongodb') as mock_mongodb:
            mock_sessions = MagicMock()
            mock_users = MagicMock()

            # Mock top users aggregation
            top_cursor = MagicMock()
            top_cursor.to_list = AsyncMock(return_value=[
                {"_id": "user1", "total_learning_time": 500, "session_count": 20}
            ])
            mock_sessions.aggregate.return_value = top_cursor

            # Mock user lookup
            mock_users.find_one = AsyncMock(return_value={
                "supabase_user_id": "user1",
                "full_name": "John Doe",
                "email": "john@example.com"
            })

            def get_collection(name):
                if "sessions" in name:
                    return mock_sessions
                elif "users" in name:
                    return mock_users
                return MagicMock()

            mock_mongodb.get_collection.side_effect = get_collection

            # Call the method
            top_users = await AnalyticsService.get_top_users(metric="learning_time", limit=10)

            # Assertions
            assert len(top_users) == 1
            assert top_users[0]["total_learning_time"] == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
