"""
Unit tests for call logs schema compatibility with MongoDB.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from backend.main import app
from backend.routes.call_logs import CallLogEntry, CallLogFilters


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_call_log_data():
    """Mock call log data matching MongoDB schema."""
    return {
        "_id": "68d1aebd77fc5874d797328e",
        "id": "698041c3-2376-424d-bf18-823d4e49e2a9",
        "call_id": "test-mongo-dual-logging",
        "assistant_id": "baa69b3a-8944-4557-9ef9-3a5aa6956eb3",
        "assistant_name": None,
        "status": "completed",
        "direction": "inbound",
        "from_phone": None,
        "to_phone": None,
        "start_time": datetime.fromisoformat("2025-09-22T20:17:01.171Z".replace("Z", "+00:00")),
        "end_time": None,
        "duration": 120,
        "cost": None,
        "transcript": "Testing dual MongoDB and Supabase logging",
        "summary": "Test call for dual database logging",
        "sentiment": None,
        "sentiment_score": None,
        "tool_calls": [],
        "webhook_data": None,
        "metadata": {},
        "customer_id": None,
        "created_at": datetime.fromisoformat("2025-09-22T20:17:01.171Z".replace("Z", "+00:00")),
        "updated_at": datetime.fromisoformat("2025-09-22T20:17:01.171Z".replace("Z", "+00:00"))
    }


class TestCallLogSchema:
    """Test call log schema compatibility."""

    def test_call_log_entry_model_validation(self, mock_call_log_data):
        """Test that CallLogEntry model can handle MongoDB data structure."""
        # Test that our model can parse MongoDB data correctly
        call_log = CallLogEntry(**mock_call_log_data)

        assert call_log.id == "698041c3-2376-424d-bf18-823d4e49e2a9"
        assert call_log.call_id == "test-mongo-dual-logging"
        assert call_log.status == "completed"
        assert call_log.direction == "inbound"
        assert call_log.duration == 120
        assert call_log.transcript == "Testing dual MongoDB and Supabase logging"

    def test_call_log_filters_model(self):
        """Test CallLogFilters model with new schema fields."""
        filters = CallLogFilters(
            assistant_id="test-assistant",
            status="completed",
            direction="inbound",
            from_phone="+1234567890",
            to_phone="+0987654321",
            customer_id="customer-123"
        )

        assert filters.assistant_id == "test-assistant"
        assert filters.status == "completed"
        assert filters.direction == "inbound"
        assert filters.from_phone == "+1234567890"
        assert filters.to_phone == "+0987654321"
        assert filters.customer_id == "customer-123"

    @patch('backend.routes.call_logs.get_current_user_mongo')
    @patch('backend.routes.call_logs.CallLogService')
    def test_get_call_logs_endpoint_parameters(self, mock_service, mock_get_user, client):
        """Test that GET endpoint accepts correct parameters."""
        mock_get_user.return_value = {"user_id": "test_user"}
        mock_service_instance = MagicMock()
        mock_service.return_value = mock_service_instance
        mock_service_instance.get_call_logs = AsyncMock(return_value={
            "logs": [],
            "pagination": {"page": 1, "per_page": 5, "total": 0, "pages": 0}
        })

        # Test with new schema parameters
        response = client.get(
            "/call-logs/?assistant_id=test&status=completed&direction=inbound&page=1&per_page=5&sort_by=start_time&sort_order=desc",
            headers={"Authorization": "Bearer dummy"}
        )

        # Should not return 422 for parameter validation
        assert response.status_code != 422

        # Verify service was called with correct filters
        mock_service_instance.get_call_logs.assert_called_once()
        call_args = mock_service_instance.get_call_logs.call_args
        filters = call_args[0][0]  # First argument is filters

        assert filters.assistant_id == "test"
        assert filters.status == "completed"
        assert filters.direction == "inbound"

    def test_call_log_entry_required_fields(self):
        """Test CallLogEntry with minimal required fields."""
        minimal_data = {
            "id": "test-id",
            "call_id": "test-call-id",
            "status": "completed",
            "direction": "inbound"
        }

        call_log = CallLogEntry(**minimal_data)
        assert call_log.id == "test-id"
        assert call_log.call_id == "test-call-id"
        assert call_log.status == "completed"
        assert call_log.direction == "inbound"

        # Optional fields should be None
        assert call_log.assistant_id is None
        assert call_log.from_phone is None
        assert call_log.duration is None

    def test_call_log_filters_optional_fields(self):
        """Test CallLogFilters with all optional fields."""
        filters = CallLogFilters()

        # All fields should be None/default
        assert filters.assistant_id is None
        assert filters.status is None
        assert filters.direction is None
        assert filters.from_phone is None
        assert filters.to_phone is None
        assert filters.customer_id is None
        assert filters.start_date is None
        assert filters.end_date is None
        assert filters.has_transcript is None
        assert filters.sentiment is None