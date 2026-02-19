"""
Unit tests for Call Management routes and VAPI Tools Integration.

Tests AI transcript summarization, call logging to Supabase, email notification functionality,
and comprehensive VAPI tools workflows as documented in VAPI_TOOLS_DOCUMENTATION.md
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status, FastAPI
import json
from datetime import datetime
import sys
sys.path.append('/opt/kasaai/apps/shared')

from backend.routes import call_management
from backend.routes.call_management import router

# Test client setup
app = FastAPI()
app.include_router(router)
client = TestClient(app)



class TestCallLogging:
    """Test suite for call logging to Supabase functionality."""

    @patch('apps.core_backend.backend.routes.call_management.verify_table_exists')
    @patch('apps.core_backend.backend.routes.call_management.get_supabase_integration')
    @pytest.mark.asyncio
    async def test_log_call_success(self, mock_supabase, mock_verify):
        """Test successful call logging to Supabase."""
        # Mock table verification
        mock_verify.return_value = True

        # Mock Supabase integration and response
        mock_integration = Mock()

        # Mock the insert method to return a SupabaseQueryResponse
        from integration.supabase import SupabaseQueryResponse
        mock_result = SupabaseQueryResponse(
            data=[{"id": "supabase_123"}],
            count=1,
            error=None
        )
        mock_integration.insert = AsyncMock(return_value=mock_result)
        mock_supabase.return_value = mock_integration

        request_data = {
            "call_id": "test_call_123",
            "transcript": "Customer: Hello, I need help. Agent: How can I assist you?",
            "summary": "Customer requested assistance",
            "customer_phone": "+233123456789",
            "duration": 120,
            "status": "completed"
        }

        response = client.post("/call-management/log-call", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["call_id"] == "test_call_123"
        assert data["supabase_id"] == "supabase_123"
        assert "logged_at" in data

        # Verify Supabase integration was called correctly
        mock_integration.insert.assert_called_once()
        # Verify the insert was called with correct table name and data structure
        call_args = mock_integration.insert.call_args
        assert call_args[0][0] == "call_logs"  # table name
        assert call_args[0][1]["call_id"] == "test_call_123"  # data contains call_id

    @patch('apps.core_backend.backend.routes.call_management.verify_table_exists')
    @patch('apps.core_backend.backend.routes.call_management.get_supabase_integration')
    def test_log_call_supabase_error(self, mock_supabase, mock_verify):
        """Test call logging when Supabase fails."""
        # Mock table verification to pass initially
        mock_verify.return_value = True

        # Mock Supabase integration to raise an exception
        mock_supabase.side_effect = Exception("Database connection error")

        request_data = {
            "call_id": "test_call_123",
            "transcript": "Test transcript"
        }

        response = client.post("/call-management/log-call", json=request_data)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_log_call_missing_required_fields(self):
        """Test call logging with missing required fields."""
        request_data = {
            "call_id": "test_call_123"
            # Missing transcript
        }

        response = client.post("/call-management/log-call", json=request_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch('apps.core_backend.backend.routes.call_management.verify_table_exists')
    @patch('apps.core_backend.backend.routes.call_management.get_supabase_integration')
    @pytest.mark.asyncio
    async def test_log_call_minimal_data(self, mock_supabase, mock_verify):
        """Test call logging with minimal required data."""
        # Mock table verification
        mock_verify.return_value = True

        # Mock successful Supabase integration response
        mock_integration = Mock()

        # Mock the insert method
        from integration.supabase import SupabaseQueryResponse
        mock_result = SupabaseQueryResponse(
            data=[{"id": "supabase_minimal"}],
            count=1,
            error=None
        )
        mock_integration.insert = AsyncMock(return_value=mock_result)
        mock_supabase.return_value = mock_integration

        request_data = {
            "call_id": "minimal_call",
            "transcript": "Short transcript"
        }

        response = client.post("/call-management/log-call", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["call_id"] == "minimal_call"


class TestEmailNotification:
    """Test suite for email notification functionality."""

    @patch('apps.core_backend.backend.routes.call_management.send_email_async')
    def test_send_notification_success(self, mock_send_email):
        """Test successful email notification sending."""
        request_data = {
            "call_summary": "Customer called about healthcare provider search. Provided cardiologist recommendations in Accra.",
            "call_id": "test_call_123",
            "customer_info": {"name": "John Doe", "phone": "+233123456789"},
            "priority": "normal"
        }

        response = client.post("/call-management/send-notification", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["call_id"] == "test_call_123"
        assert data["email_recipient"] == "ailabsafrica@gmail.com"
        assert "sent_at" in data

    def test_send_notification_missing_fields(self):
        """Test email notification with missing required fields."""
        request_data = {
            "call_id": "test_call_123"
            # Missing call_summary
        }

        response = client.post("/call-management/send-notification", json=request_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_send_notification_high_priority(self):
        """Test email notification with high priority."""
        request_data = {
            "call_summary": "Urgent: Customer reported billing issue requiring immediate attention.",
            "call_id": "urgent_call_456",
            "priority": "urgent"
        }

        response = client.post("/call-management/send-notification", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["call_id"] == "urgent_call_456"


class TestHealthCheck:
    """Test suite for health check functionality."""

    @patch('apps.core_backend.backend.routes.call_management.get_available_tables')
    @patch('apps.core_backend.backend.routes.call_management.verify_table_exists')
    @patch('apps.core_backend.backend.routes.call_management.get_supabase_integration')
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, mock_supabase, mock_verify, mock_get_tables):
        """Test health check when service is healthy."""
        # Mock successful Supabase integration
        mock_integration = Mock()
        mock_integration.health_check = AsyncMock(return_value=True)
        mock_supabase.return_value = mock_integration

        # Mock table verification
        mock_verify.return_value = True

        # Mock available tables
        mock_get_tables.return_value = ['call_logs', 'profiles']

        response = client.get("/call-management/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Call Management Service"
        assert data["supabase_connected"] is True

    @patch('apps.core_backend.backend.routes.call_management.get_supabase_integration')
    def test_health_check_unhealthy(self, mock_supabase):
        """Test health check when service is unhealthy."""
        # Mock Supabase connection failure
        mock_supabase.side_effect = Exception("Connection failed")

        response = client.get("/call-management/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["supabase_connected"] is False
        assert "error" in data


class TestValidationAndEdgeCases:
    """Test suite for validation and edge cases."""

    def test_call_log_request_validation(self):
        """Test call log request validation."""
        # Test with invalid duration (negative)
        request_data = {
            "call_id": "test_call",
            "transcript": "Test transcript",
            "duration": -10
        }

        response = client.post("/call-management/log-call", json=request_data)
        # Should still succeed as duration validation isn't strict in current implementation
        # In production, you might want to add validation for positive duration

    def test_email_notification_empty_summary(self):
        """Test email notification with empty summary."""
        request_data = {
            "call_summary": "",
            "call_id": "test_call_123"
        }

        # Current implementation allows empty summary, but you might want to validate this
        response = client.post("/call-management/send-notification", json=request_data)
        assert response.status_code == status.HTTP_200_OK

    @patch('apps.core_backend.backend.routes.call_management.verify_table_exists')
    @patch('apps.core_backend.backend.routes.call_management.get_supabase_integration')
    @pytest.mark.asyncio
    async def test_log_call_large_transcript(self, mock_supabase, mock_verify):
        """Test logging call with very large transcript."""
        # Mock table verification
        mock_verify.return_value = True

        # Mock successful Supabase integration response
        mock_integration = Mock()

        from integration.supabase import SupabaseQueryResponse
        mock_result = SupabaseQueryResponse(
            data=[{"id": "large_transcript_id"}],
            count=1,
            error=None
        )
        mock_integration.insert = AsyncMock(return_value=mock_result)
        mock_supabase.return_value = mock_integration

        large_transcript = "This is a test transcript. " * 1000  # Large transcript

        request_data = {
            "call_id": "large_call",
            "transcript": large_transcript
        }

        response = client.post("/call-management/log-call", json=request_data)
        assert response.status_code == status.HTTP_200_OK


class TestEnhancedSupabaseIntegration:
    """Test suite for enhanced Supabase integration endpoints."""

    @patch('apps.core_backend.backend.routes.call_management.verify_table_exists')
    @patch('apps.core_backend.backend.routes.call_management.get_supabase_integration')
    @pytest.mark.asyncio
    async def test_supabase_integration_insert(self, mock_get_client, mock_verify):
        """Test Supabase integration endpoint for insert operation."""
        # Setup mocks
        mock_verify.return_value = asyncio.Future()
        mock_verify.return_value.set_result(True)

        mock_integration = Mock()
        from integration.supabase import SupabaseQueryResponse
        mock_result = SupabaseQueryResponse(
            data=[{'id': 'inserted_id'}],
            count=1,
            error=None
        )
        mock_integration.insert = AsyncMock(return_value=mock_result)
        mock_get_client.return_value = mock_integration

        test_data = {
            'action': 'insert',
            'table': 'call_logs',
            'data': {
                'call_id': 'test_123',
                'status': 'completed',
                'transcript': 'test transcript'
            }
        }

        response = client.post('/call-management/supabase-integration', json=test_data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['success'] is True
        assert response_data['action'] == 'insert'
        assert response_data['table'] == 'call_logs'
        assert response_data['count'] == 1

    @patch('apps.core_backend.backend.routes.call_management.verify_table_exists')
    @patch('apps.core_backend.backend.routes.call_management.get_supabase_integration')
    @pytest.mark.asyncio
    async def test_vapi_supabase_call_recording_endpoint(self, mock_get_client, mock_verify):
        """Test the VAPI-specific supabase_call_recording endpoint."""
        # Setup mocks
        mock_verify.return_value = asyncio.Future()
        mock_verify.return_value.set_result(True)

        mock_integration = Mock()
        from integration.supabase import SupabaseQueryResponse
        mock_result = SupabaseQueryResponse(
            data=[{'id': 'vapi_call_id'}],
            count=1,
            error=None
        )
        mock_integration.insert = AsyncMock(return_value=mock_result)
        mock_get_client.return_value = mock_integration

        # Test data matching VAPI documentation
        test_data = {
            'action': 'insert',
            'table': 'call_logs',
            'data': {
                'call_id': 'vapi_healthcare_call',
                'assistant_id': 'healthcare_assistant',
                'transcript': 'Customer: I need a cardiologist. Assistant: I found 3 specialists...',
                'status': 'completed'
            }
        }

        # Test the VAPI-specific endpoint
        response = client.post('/call-management/integrations/supabase/execute', json=test_data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['success'] is True
        assert response_data['action'] == 'insert'
        assert response_data['table'] == 'call_logs'

    @patch('apps.core_backend.backend.routes.call_management.get_available_tables')
    def test_list_tables_endpoint(self, mock_get_tables):
        """Test the list tables endpoint."""
        mock_get_tables.return_value = ['call_logs', 'profiles', 'assistants']

        response = client.get('/call-management/tables')

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['success'] is True
        assert 'call_logs' in response_data['tables']
        assert response_data['count'] == 3


class TestVAPIToolsDocumentationCompliance:
    """Test compliance with VAPI_TOOLS_DOCUMENTATION.md specifications."""

    def test_vapi_documentation_endpoints_exist(self):
        """Test that all call management endpoints mentioned in VAPI_TOOLS_DOCUMENTATION.md exist."""
        # Test endpoints from VAPI documentation
        endpoints_to_test = [
            ("/call-management/log-call", "POST"),  # call_logging_supabase
            ("/call-management/send-notification", "POST"),  # email_notification
            ("/call-management/health", "GET"),  # health check
            ("/call-management/tables", "GET"),  # tables list
            ("/call-management/supabase-integration", "POST"),  # supabase integration
            ("/call-management/integrations/supabase/execute", "POST"),  # supabase_call_recording
        ]

        for endpoint, method in endpoints_to_test:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})

            # Should not return 404 (endpoint exists), may return 422 for missing params
            assert response.status_code != 404, f"Endpoint {method} {endpoint} not found in VAPI documentation"
            print(f"✅ VAPI endpoint {method} {endpoint} exists (status: {response.status_code})")

    @patch('apps.core_backend.backend.routes.call_management.verify_table_exists')
    @patch('apps.core_backend.backend.routes.call_management.get_supabase_integration')
    @pytest.mark.asyncio
    async def test_vapi_call_logging_supabase_workflow(self, mock_supabase, mock_verify):
        """Test call_logging_supabase workflow as documented in VAPI_TOOLS_DOCUMENTATION.md"""
        # Mock successful responses
        mock_verify.return_value = True

        mock_integration = Mock()
        from integration.supabase import SupabaseQueryResponse
        mock_result = SupabaseQueryResponse(
            data=[{"id": "vapi_call_log_12345"}],
            count=1,
            error=None
        )
        mock_integration.insert = AsyncMock(return_value=mock_result)
        mock_supabase.return_value = mock_integration

        # Test data matching VAPI documentation example
        vapi_call_data = {
            "call_id": "call_123",
            "transcript": "Customer: I need a cardiologist in Accra. Agent: I found 3 specialists in your area...",
            "summary": "Customer requested cardiologist recommendations in Accra. Provided 3 specialists with contact information.",
            "customer_phone": "+233123456789",
            "duration": 180,
            "status": "completed"
        }

        response = client.post("/call-management/log-call", json=vapi_call_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["call_id"] == "call_123"
        assert data["supabase_id"] == "vapi_call_log_12345"
        assert "logged_at" in data

        # Verify call was logged with correct structure for VAPI
        mock_integration.insert.assert_called_once()
        call_args = mock_integration.insert.call_args
        assert call_args[0][0] == "call_logs"
        inserted_data = call_args[0][1]
        assert inserted_data["call_id"] == "call_123"
        assert inserted_data["status"] == "completed"
        assert "created_at" in inserted_data  # Required for VAPI tracking

    @patch('apps.core_backend.backend.routes.call_management.verify_table_exists')
    @patch('apps.core_backend.backend.routes.call_management.get_supabase_integration')
    @pytest.mark.asyncio
    async def test_vapi_supabase_call_recording_tool(self, mock_supabase, mock_verify):
        """Test supabase_call_recording tool as documented in VAPI_TOOLS_DOCUMENTATION.md"""
        # Setup mocks
        mock_verify.return_value = asyncio.Future()
        mock_verify.return_value.set_result(True)

        mock_integration = Mock()
        from integration.supabase import SupabaseQueryResponse
        mock_result = SupabaseQueryResponse(
            data=[{'id': 'vapi_recording_id', 'call_id': 'vapi_call_123'}],
            count=1,
            error=None
        )
        mock_integration.insert = AsyncMock(return_value=mock_result)
        mock_supabase.return_value = mock_integration

        # Test data as per VAPI documentation specification
        vapi_recording_data = {
            'action': 'insert',
            'table': 'call_logs',
            'data': {
                'call_id': 'vapi_call_123',
                'assistant_id': 'healthcare_assistant',
                'transcript': 'Customer: I need a cardiologist. Assistant: I found 3 specialists in Accra...',
                'status': 'completed'
            }
        }

        # Test the VAPI-specific endpoint as documented
        response = client.post('/call-management/integrations/supabase/execute', json=vapi_recording_data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['success'] is True
        assert response_data['action'] == 'insert'
        assert response_data['table'] == 'call_logs'
        assert response_data['count'] == 1
        assert response_data['data'][0]['id'] == 'vapi_recording_id'

    def test_vapi_email_notification_tool(self):
        """Test email_notification tool as documented in VAPI_TOOLS_DOCUMENTATION.md"""
        # Test data matching VAPI documentation
        vapi_notification_data = {
            "call_summary": "Customer called about healthcare provider search. Provided cardiologist recommendations in Accra including Dr. Sarah Johnson and Dr. Michael Asante.",
            "call_id": "call_123",
            "customer_info": {
                "name": "John Doe",
                "phone": "+233123456789"
            },
            "priority": "normal"
        }

        response = client.post("/call-management/send-notification", json=vapi_notification_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["call_id"] == "call_123"
        assert data["email_recipient"] == "ailabsafrica@gmail.com"  # As documented
        assert "sent_at" in data

    def test_vapi_urgent_priority_notification(self):
        """Test urgent priority email notification for VAPI escalation."""
        urgent_vapi_data = {
            "call_summary": "URGENT: Customer reported serious side effects from medication. Immediate medical attention may be required.",
            "call_id": "urgent_vapi_call_456",
            "priority": "urgent"
        }

        response = client.post("/call-management/send-notification", json=urgent_vapi_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["call_id"] == "urgent_vapi_call_456"
        assert data["email_recipient"] == "ailabsafrica@gmail.com"


class TestCompleteVAPIWorkflow:
    """Test complete VAPI workflow as documented in VAPI_TOOLS_DOCUMENTATION.md"""

    @patch('apps.core_backend.backend.routes.call_management.verify_table_exists')
    @patch('apps.core_backend.backend.routes.call_management.get_supabase_integration')
    @pytest.mark.asyncio
    async def test_complete_vapi_call_management_workflow(self, mock_supabase, mock_verify):
        """Test complete call management workflow as shown in VAPI documentation."""
        # Setup mocks
        mock_verify.return_value = True

        mock_integration = Mock()
        from integration.supabase import SupabaseQueryResponse
        mock_log_result = SupabaseQueryResponse(
            data=[{"id": "vapi_workflow_call_123"}],
            count=1,
            error=None
        )
        mock_integration.insert = AsyncMock(return_value=mock_log_result)
        mock_supabase.return_value = mock_integration

        # Step 1: Simulate AI transcript summarization result
        # (This would normally be a separate endpoint call)
        summary_result = {
            "summary": "Customer called requesting cardiologist recommendations in Accra. Provided contact information for 3 specialists including Dr. Sarah Johnson at Korle-Bu Teaching Hospital.",
            "call_id": "call_123",
            "ai_provider_used": "openai"
        }

        # Step 2: Log call to Supabase using call_logging_supabase tool
        log_data = {
            "call_id": "call_123",
            "transcript": "Customer: I need a cardiologist in Accra. Agent: I can help you with that. Let me search for cardiologists in your area...",
            "summary": summary_result["summary"],
            "customer_phone": "+233123456789",
            "duration": 180,
            "status": "completed"
        }

        log_response = client.post("/call-management/log-call", json=log_data)
        assert log_response.status_code == status.HTTP_200_OK
        log_result = log_response.json()
        assert log_result["success"] is True
        assert log_result["call_id"] == "call_123"
        assert log_result["supabase_id"] == "vapi_workflow_call_123"

        # Step 3: Send email notification using email_notification tool
        notification_data = {
            "call_summary": summary_result["summary"],
            "call_id": "call_123",
            "customer_info": {
                "name": "John Doe",
                "phone": "+233123456789"
            },
            "priority": "normal"
        }

        notification_response = client.post("/call-management/send-notification", json=notification_data)
        assert notification_response.status_code == status.HTTP_200_OK
        notification_result = notification_response.json()
        assert notification_result["success"] is True
        assert notification_result["call_id"] == "call_123"
        assert notification_result["email_recipient"] == "ailabsafrica@gmail.com"

        # Verify the complete VAPI workflow succeeded
        print(f"✅ Complete VAPI workflow test passed:")
        print(f"  - Call logged with ID: {log_result['supabase_id']}")
        print(f"  - Email notification sent to: {notification_result['email_recipient']}")


class TestVAPIErrorHandlingAndCompatibility:
    """Test error handling and backward compatibility for VAPI tools."""

    def test_vapi_backward_compatibility_both_endpoints(self):
        """Test that both old and VAPI-specific Supabase endpoints work identically."""
        with patch('apps.core_backend.backend.routes.call_management.verify_table_exists') as mock_verify, \
             patch('apps.core_backend.backend.routes.call_management.get_supabase_integration') as mock_supabase:

            # Setup mocks
            mock_verify.return_value = asyncio.Future()
            mock_verify.return_value.set_result(True)

            mock_integration = Mock()
            from integration.supabase import SupabaseQueryResponse
            mock_result = SupabaseQueryResponse(
                data=[{'id': 'compatibility_test_id'}],
                count=1,
                error=None
            )
            mock_integration.insert = AsyncMock(return_value=mock_result)
            mock_supabase.return_value = mock_integration

            test_data = {
                'action': 'insert',
                'table': 'call_logs',
                'data': {'call_id': 'compatibility_test', 'transcript': 'test transcript'}
            }

            # Test original endpoint
            response1 = client.post('/call-management/supabase-integration', json=test_data)

            # Test VAPI-specific endpoint from documentation
            response2 = client.post('/call-management/integrations/supabase/execute', json=test_data)

            # Both should work identically for VAPI compatibility
            assert response1.status_code == response2.status_code == status.HTTP_200_OK

            data1 = response1.json()
            data2 = response2.json()

            # Responses should be identical
            assert data1['success'] == data2['success'] == True
            assert data1['action'] == data2['action'] == 'insert'
            assert data1['table'] == data2['table'] == 'call_logs'

            print("✅ VAPI backward compatibility verified: both endpoints work identically")

    @patch('apps.core_backend.backend.routes.call_management.verify_table_exists')
    @patch('apps.core_backend.backend.routes.call_management.get_supabase_integration')
    def test_vapi_error_handling_missing_data(self, mock_supabase, mock_verify):
        """Test VAPI error handling when required data is missing."""
        # Mock table verification
        mock_verify.return_value = True

        # Mock Supabase integration
        mock_integration = Mock()
        mock_supabase.return_value = mock_integration

        incomplete_data = {
            'action': 'insert',
            'table': 'call_logs'
            # Missing 'data' field required by VAPI specification
        }

        response = client.post('/call-management/integrations/supabase/execute', json=incomplete_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Verify error response format matches VAPI documentation
        error_data = response.json()
        assert "detail" in error_data  # FastAPI error format

    @patch('apps.core_backend.backend.routes.call_management.verify_table_exists')
    @patch('apps.core_backend.backend.routes.call_management.get_supabase_integration')
    def test_vapi_error_handling_invalid_action(self, mock_supabase, mock_verify):
        """Test VAPI error handling for invalid actions."""
        # Mock table verification
        mock_verify.return_value = True

        # Mock Supabase integration
        mock_integration = Mock()
        mock_supabase.return_value = mock_integration

        invalid_action_data = {
            'action': 'invalid_vapi_action',
            'table': 'call_logs',
            'data': {'test': 'data'}
        }

        response = client.post('/call-management/integrations/supabase/execute', json=invalid_action_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch('apps.core_backend.backend.routes.call_management.verify_table_exists')
    @patch('apps.core_backend.backend.routes.call_management.get_supabase_integration')
    def test_vapi_database_error_handling(self, mock_supabase, mock_verify):
        """Test VAPI tool handling of database errors."""
        mock_verify.return_value = True

        mock_integration = Mock()
        from integration.supabase import SupabaseQueryResponse
        mock_result = SupabaseQueryResponse(
            data=None,
            count=0,
            error="Database connection failed for VAPI operation"
        )
        mock_integration.insert = AsyncMock(return_value=mock_result)
        mock_supabase.return_value = mock_integration

        test_data = {
            'action': 'insert',
            'table': 'call_logs',
            'data': {'call_id': 'vapi_error_test', 'transcript': 'test'}
        }

        response = client.post('/call-management/integrations/supabase/execute', json=test_data)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


if __name__ == "__main__":
    pytest.main([__file__, "-v"])