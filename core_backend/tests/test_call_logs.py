"""
Tests for Call Logs Management Routes

Tests the call logging, retrieval, and analysis capabilities
for VAPI interactions and automation monitoring.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone, timedelta
from bson import ObjectId

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from backend.routes.call_logs import (
    CallLogService,
    CallLogEntry,
    CallLogFilters,
    CallLogStats,
    ToolCallAnalysis
)


class TestCallLogService:
    """Test suite for call log service."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = Mock()
        db.call_logs = Mock()
        db.tool_calls = Mock()
        return db

    @pytest.fixture
    def call_log_service(self, mock_db):
        """Create call log service with mock database."""
        return CallLogService(mock_db)

    @pytest.fixture
    def sample_call_data(self):
        """Sample call data for testing."""
        return {
            "call_id": "call_12345",
            "assistant_id": "assistant_67890",
            "automation_id": "automation_abc",
            "campaign_id": "campaign_xyz",
            "phone_number": "+1234567890",
            "call_status": "completed",
            "call_duration": 120.5,
            "cost": 0.045,
            "transcript": "Customer: Hello, I need help. Agent: How can I assist you?",
            "summary": "Customer requested assistance with product information",
            "sentiment_score": 0.75,
            "tool_calls": [
                {
                    "tool_name": "search_providers",
                    "success": True,
                    "execution_time": 2.3
                },
                {
                    "tool_name": "send_email",
                    "success": False,
                    "error": "Email service unavailable"
                }
            ],
            "webhook_data": {"type": "call_ended"},
            "metadata": {"source": "web_widget"}
        }

    @pytest.mark.asyncio
    async def test_create_call_log_success(self, call_log_service, sample_call_data):
        """Test successful call log creation."""
        # Mock successful database insertion
        mock_result = Mock()
        mock_result.inserted_id = ObjectId()
        call_log_service.call_logs_collection.insert_one = AsyncMock(return_value=mock_result)

        log_id = await call_log_service.create_call_log(sample_call_data)

        assert log_id == str(mock_result.inserted_id)
        call_log_service.call_logs_collection.insert_one.assert_called_once()

        # Verify the call data structure
        insert_call = call_log_service.call_logs_collection.insert_one.call_args[0][0]
        assert insert_call["call_id"] == "call_12345"
        assert insert_call["call_status"] == "completed"
        assert insert_call["call_duration"] == 120.5
        assert len(insert_call["tool_calls"]) == 2

    @pytest.mark.asyncio
    async def test_create_call_log_with_defaults(self, call_log_service):
        """Test call log creation with minimal data and defaults."""
        minimal_data = {
            "call_id": "call_minimal"
        }

        mock_result = Mock()
        mock_result.inserted_id = ObjectId()
        call_log_service.call_logs_collection.insert_one = AsyncMock(return_value=mock_result)

        log_id = await call_log_service.create_call_log(minimal_data)

        insert_call = call_log_service.call_logs_collection.insert_one.call_args[0][0]
        assert insert_call["call_status"] == "unknown"  # Default value
        assert insert_call["tool_calls"] == []  # Default empty list
        assert "created_at" in insert_call
        assert "updated_at" in insert_call

    @pytest.mark.asyncio
    async def test_get_call_logs_with_filters(self, call_log_service):
        """Test call log retrieval with filters."""
        filters = CallLogFilters(
            assistant_id="assistant_123",
            call_status="completed",
            start_date=datetime.now(timezone.utc) - timedelta(days=7),
            end_date=datetime.now(timezone.utc),
            has_transcript=True
        )

        # Mock database responses
        call_log_service.call_logs_collection.count_documents = AsyncMock(return_value=25)

        # Mock cursor for find operation
        mock_cursor = Mock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor

        # Sample log data
        sample_logs = [
            {
                "_id": ObjectId(),
                "call_id": "call_1",
                "assistant_id": "assistant_123",
                "call_status": "completed",
                "call_duration": 90,
                "transcript": "Test transcript",
                "created_at": datetime.now(timezone.utc)
            },
            {
                "_id": ObjectId(),
                "call_id": "call_2",
                "assistant_id": "assistant_123",
                "call_status": "completed",
                "call_duration": 150,
                "transcript": "Another transcript",
                "created_at": datetime.now(timezone.utc)
            }
        ]

        async def mock_cursor_iteration():
            for log in sample_logs:
                yield log

        mock_cursor.__aiter__ = mock_cursor_iteration
        call_log_service.call_logs_collection.find.return_value = mock_cursor

        result = await call_log_service.get_call_logs(filters, page=1, per_page=10)

        # Verify results
        assert len(result["logs"]) == 2
        assert result["pagination"]["total"] == 25
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["per_page"] == 10

        # Verify query was built correctly
        call_log_service.call_logs_collection.find.assert_called_once()
        query_arg = call_log_service.call_logs_collection.find.call_args[0][0]
        assert query_arg["assistant_id"] == "assistant_123"
        assert query_arg["call_status"] == "completed"
        assert "created_at" in query_arg  # Date range filter

    @pytest.mark.asyncio
    async def test_get_call_logs_with_duration_filters(self, call_log_service):
        """Test call log retrieval with duration filters."""
        filters = CallLogFilters(
            min_duration=60.0,
            max_duration=300.0
        )

        call_log_service.call_logs_collection.count_documents = AsyncMock(return_value=0)

        mock_cursor = Mock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__aiter__ = lambda self: iter([])
        call_log_service.call_logs_collection.find.return_value = mock_cursor

        await call_log_service.get_call_logs(filters)

        # Verify duration filter was applied
        query_arg = call_log_service.call_logs_collection.find.call_args[0][0]
        assert "call_duration" in query_arg
        assert query_arg["call_duration"]["$gte"] == 60.0
        assert query_arg["call_duration"]["$lte"] == 300.0

    @pytest.mark.asyncio
    async def test_get_call_log_stats(self, call_log_service):
        """Test call log statistics aggregation."""
        filters = CallLogFilters(
            start_date=datetime.now(timezone.utc) - timedelta(days=30)
        )

        # Mock aggregation result
        stats_data = {
            "_id": None,
            "total_calls": 150,
            "successful_calls": 120,
            "failed_calls": 30,
            "total_duration": 18000.0,
            "total_cost": 75.50,
            "avg_sentiment": 0.72,
            "total_tool_calls": 450,
            "unique_assistants": ["assistant_1", "assistant_2"],
            "unique_phone_numbers": ["+1111111111", "+2222222222", "+3333333333"],
            "min_date": datetime.now(timezone.utc) - timedelta(days=25),
            "max_date": datetime.now(timezone.utc)
        }

        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=[stats_data])
        call_log_service.call_logs_collection.aggregate.return_value = mock_cursor

        stats = await call_log_service.get_call_log_stats(filters)

        # Verify calculated statistics
        assert stats.total_calls == 150
        assert stats.successful_calls == 120
        assert stats.failed_calls == 30
        assert stats.avg_duration == 120.0  # 18000 / 150
        assert stats.avg_cost == 0.5033  # 75.50 / 150 (approximately)
        assert stats.success_rate == 80.0  # 120 / 150 * 100
        assert stats.unique_assistants == 2
        assert stats.unique_phone_numbers == 3

    @pytest.mark.asyncio
    async def test_get_call_log_stats_empty_data(self, call_log_service):
        """Test call log statistics with no data."""
        filters = CallLogFilters()

        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        call_log_service.call_logs_collection.aggregate.return_value = mock_cursor

        stats = await call_log_service.get_call_log_stats(filters)

        # Verify empty stats
        assert stats.total_calls == 0
        assert stats.successful_calls == 0
        assert stats.failed_calls == 0
        assert stats.avg_duration == 0.0
        assert stats.avg_cost == 0.0
        assert stats.success_rate == 0.0

    @pytest.mark.asyncio
    async def test_get_tool_call_analysis(self, call_log_service):
        """Test tool call performance analysis."""
        filters = CallLogFilters(assistant_id="assistant_123")

        # Mock aggregation result for tool analysis
        tool_analysis_data = [
            {
                "_id": "search_providers",
                "tool_name": "search_providers",
                "total_calls": 100,
                "success_rate": 95.0,
                "avg_execution_time": 2.5,
                "error_rate": 5.0,
                "common_errors": ["Provider not found", "Timeout error"]
            },
            {
                "_id": "send_email",
                "tool_name": "send_email",
                "total_calls": 75,
                "success_rate": 88.0,
                "avg_execution_time": 1.8,
                "error_rate": 12.0,
                "common_errors": ["Email service unavailable"]
            }
        ]

        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=tool_analysis_data)
        call_log_service.call_logs_collection.aggregate.return_value = mock_cursor

        analysis = await call_log_service.get_tool_call_analysis(filters)

        # Verify analysis results
        assert len(analysis) == 2

        search_tool = analysis[0]
        assert search_tool.tool_name == "search_providers"
        assert search_tool.total_calls == 100
        assert search_tool.success_rate == 95.0
        assert search_tool.error_rate == 5.0
        assert len(search_tool.common_errors) == 2

        email_tool = analysis[1]
        assert email_tool.tool_name == "send_email"
        assert email_tool.total_calls == 75
        assert email_tool.success_rate == 88.0

    @pytest.mark.asyncio
    async def test_update_call_log_success(self, call_log_service):
        """Test successful call log update."""
        log_id = str(ObjectId())
        update_data = {
            "summary": "Updated summary",
            "sentiment_score": 0.85
        }

        mock_result = Mock()
        mock_result.modified_count = 1
        call_log_service.call_logs_collection.update_one = AsyncMock(return_value=mock_result)

        success = await call_log_service.update_call_log(log_id, update_data)

        assert success is True
        call_log_service.call_logs_collection.update_one.assert_called_once()

        # Verify update operation
        update_call = call_log_service.call_logs_collection.update_one.call_args
        assert update_call[0][0]["_id"] == ObjectId(log_id)
        assert update_call[0][1]["$set"]["summary"] == "Updated summary"
        assert "updated_at" in update_call[0][1]["$set"]

    @pytest.mark.asyncio
    async def test_update_call_log_not_found(self, call_log_service):
        """Test call log update when log doesn't exist."""
        log_id = str(ObjectId())
        update_data = {"summary": "Updated summary"}

        mock_result = Mock()
        mock_result.modified_count = 0
        call_log_service.call_logs_collection.update_one = AsyncMock(return_value=mock_result)

        success = await call_log_service.update_call_log(log_id, update_data)

        assert success is False

    @pytest.mark.asyncio
    async def test_delete_call_log_success(self, call_log_service):
        """Test successful call log deletion."""
        log_id = str(ObjectId())

        mock_result = Mock()
        mock_result.deleted_count = 1
        call_log_service.call_logs_collection.delete_one = AsyncMock(return_value=mock_result)

        success = await call_log_service.delete_call_log(log_id)

        assert success is True
        call_log_service.call_logs_collection.delete_one.assert_called_once_with(
            {"_id": ObjectId(log_id)}
        )

    @pytest.mark.asyncio
    async def test_delete_call_log_not_found(self, call_log_service):
        """Test call log deletion when log doesn't exist."""
        log_id = str(ObjectId())

        mock_result = Mock()
        mock_result.deleted_count = 0
        call_log_service.call_logs_collection.delete_one = AsyncMock(return_value=mock_result)

        success = await call_log_service.delete_call_log(log_id)

        assert success is False

    def test_build_query_from_filters(self, call_log_service):
        """Test query building from filters."""
        filters = CallLogFilters(
            assistant_id="assistant_123",
            call_status="completed",
            phone_number="+1234567890",
            start_date=datetime.now(timezone.utc) - timedelta(days=7),
            end_date=datetime.now(timezone.utc)
        )

        query = call_log_service._build_query_from_filters(filters)

        assert query["assistant_id"] == "assistant_123"
        assert query["call_status"] == "completed"
        assert query["phone_number"] == "+1234567890"
        assert "created_at" in query
        assert "$gte" in query["created_at"]
        assert "$lte" in query["created_at"]

    def test_build_query_empty_filters(self, call_log_service):
        """Test query building with empty filters."""
        filters = CallLogFilters()
        query = call_log_service._build_query_from_filters(filters)

        # Should return empty query for no filters
        assert query == {}


class TestCallLogModels:
    """Test call log data models."""

    def test_call_log_entry_model(self):
        """Test CallLogEntry model validation."""
        entry = CallLogEntry(
            id="log_123",
            call_id="call_456",
            assistant_id="assistant_789",
            phone_number="+1234567890",
            call_status="completed",
            call_duration=120.5,
            cost=0.045,
            transcript="Test transcript",
            sentiment_score=0.75,
            created_at="2025-09-22T10:00:00Z"
        )

        assert entry.id == "log_123"
        assert entry.call_id == "call_456"
        assert entry.assistant_id == "assistant_789"
        assert entry.call_status == "completed"
        assert entry.call_duration == 120.5
        assert entry.sentiment_score == 0.75

    def test_call_log_filters_model(self):
        """Test CallLogFilters model validation."""
        filters = CallLogFilters(
            assistant_id="assistant_123",
            has_transcript=True,
            min_duration=60.0,
            sentiment_range=[0.5, 0.9]
        )

        assert filters.assistant_id == "assistant_123"
        assert filters.has_transcript is True
        assert filters.min_duration == 60.0
        assert filters.sentiment_range == [0.5, 0.9]

    def test_call_log_stats_model(self):
        """Test CallLogStats model validation."""
        stats = CallLogStats(
            total_calls=150,
            successful_calls=120,
            failed_calls=30,
            total_duration=18000.0,
            total_cost=75.50,
            avg_duration=120.0,
            avg_cost=0.50,
            success_rate=80.0,
            total_tool_calls=450,
            unique_assistants=2,
            unique_phone_numbers=3,
            date_range={
                "start": datetime.now(timezone.utc) - timedelta(days=30),
                "end": datetime.now(timezone.utc)
            }
        )

        assert stats.total_calls == 150
        assert stats.success_rate == 80.0
        assert stats.avg_duration == 120.0
        assert stats.unique_assistants == 2

    def test_tool_call_analysis_model(self):
        """Test ToolCallAnalysis model validation."""
        analysis = ToolCallAnalysis(
            tool_name="search_providers",
            total_calls=100,
            success_rate=95.0,
            avg_execution_time=2.5,
            error_rate=5.0,
            common_errors=["Provider not found", "Timeout error"]
        )

        assert analysis.tool_name == "search_providers"
        assert analysis.total_calls == 100
        assert analysis.success_rate == 95.0
        assert analysis.error_rate == 5.0
        assert len(analysis.common_errors) == 2


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])