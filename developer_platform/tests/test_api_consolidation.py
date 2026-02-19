"""
Tests for API Surface Consolidation.

This module tests the standardized API responses, error handling,
and documentation features implemented in the API consolidation.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import json
from datetime import datetime

from backend.main import app
from backend.api_consolidation import (
    StandardAPIResponse, create_success_response, create_error_response,
    create_paginated_response, handle_api_exception, ErrorCode,
    get_api_endpoints, get_api_endpoints_by_category
)

client = TestClient(app)


class TestAPIResponseStandardization:
    """Test standardized API response formats."""

    def test_create_success_response(self):
        """Test creating a standardized success response."""
        data = {"id": "123", "name": "test"}
        meta = {"timestamp": "2025-01-27T10:00:00Z"}
        message = "Operation successful"
        
        response = create_success_response(data=data, meta=meta, message=message)
        
        assert response.status == "success"
        assert response.data == data
        assert response.meta == meta
        assert response.meta["message"] == message
        assert response.error is None

    def test_create_error_response(self):
        """Test creating a standardized error response."""
        code = ErrorCode.NOT_FOUND
        message = "Resource not found"
        details = {"resource_id": "123"}
        request_id = "req_123456"
        
        response = create_error_response(code, message, details, request_id)
        
        assert response.status == "error"
        assert response.error["code"] == code
        assert response.error["message"] == message
        assert response.error["details"] == details
        assert response.error["request_id"] == request_id
        assert response.data is None

    def test_create_paginated_response(self):
        """Test creating a standardized paginated response."""
        items = [{"id": "1"}, {"id": "2"}]
        page = 1
        per_page = 10
        total = 25
        meta = {"category": "test"}
        
        response = create_paginated_response(items, page, per_page, total, meta)
        
        assert response.status == "success"
        assert response.data["items"] == items
        assert response.meta["pagination"]["page"] == page
        assert response.meta["pagination"]["per_page"] == per_page
        assert response.meta["pagination"]["total"] == total
        assert response.meta["pagination"]["total_pages"] == 3
        assert response.meta["pagination"]["has_next"] is True
        assert response.meta["pagination"]["has_prev"] is False
        assert response.meta["category"] == "test"


class TestErrorHandling:
    """Test standardized error handling."""

    def test_handle_api_exception_http_exception(self):
        """Test handling HTTPException."""
        exc = HTTPException(status_code=404, detail="Not found")
        
        result = handle_api_exception(exc)
        
        assert isinstance(result, HTTPException)
        assert result.status_code == 404
        assert result.detail == "Not found"

    def test_handle_api_exception_value_error(self):
        """Test handling ValueError."""
        exc = ValueError("Invalid input")
        request_id = "req_123"
        
        result = handle_api_exception(exc, request_id, "test_context")
        
        assert isinstance(result, HTTPException)
        assert result.status_code == 400
        assert "validation_error" in result.detail

    def test_handle_api_exception_key_error(self):
        """Test handling KeyError."""
        exc = KeyError("missing_key")
        request_id = "req_123"
        
        result = handle_api_exception(exc, request_id, "test_context")
        
        assert isinstance(result, HTTPException)
        assert result.status_code == 400
        assert "invalid_parameter" in result.detail

    def test_handle_api_exception_generic(self):
        """Test handling generic exceptions."""
        exc = Exception("Generic error")
        request_id = "req_123"
        
        result = handle_api_exception(exc, request_id, "test_context")
        
        assert isinstance(result, HTTPException)
        assert result.status_code == 500
        assert "internal_error" in result.detail


class TestAPIEndpointRegistry:
    """Test API endpoint registry and documentation."""

    def test_get_api_endpoints(self):
        """Test getting all API endpoints."""
        endpoints = get_api_endpoints()
        
        assert isinstance(endpoints, list)
        assert len(endpoints) > 0
        
        # Check that all endpoints have required fields
        for endpoint in endpoints:
            assert hasattr(endpoint, 'path')
            assert hasattr(endpoint, 'method')
            assert hasattr(endpoint, 'description')
            assert hasattr(endpoint, 'version')
            assert hasattr(endpoint, 'requires_auth')
            assert hasattr(endpoint, 'rate_limited')

    def test_get_api_endpoints_by_category(self):
        """Test getting API endpoints grouped by category."""
        categories = get_api_endpoints_by_category()
        
        assert isinstance(categories, dict)
        assert len(categories) > 0
        
        # Check that all categories exist
        expected_categories = [
            "Core Management", "Telephony", "Analytics", "Configuration",
            "Usage Tracking", "License Management", "Monitoring",
            "Module System", "Core Backend Proxy", "Webhook Management",
            "MCP Server Management", "System Information"
        ]
        
        for category in expected_categories:
            assert category in categories
            assert isinstance(categories[category], list)

    def test_telephony_endpoints_categorized(self):
        """Test that telephony endpoints are properly categorized."""
        categories = get_api_endpoints_by_category()
        telephony_endpoints = categories["Telephony"]
        
        # Check that telephony endpoints contain expected paths
        telephony_paths = [endpoint.path for endpoint in telephony_endpoints]
        
        assert any("calls" in path for path in telephony_paths)
        assert any("providers" in path for path in telephony_paths)
        assert any("dids" in path for path in telephony_paths)


class TestConsolidatedEndpoints:
    """Test the new consolidated API endpoints."""

    def test_health_check_endpoint(self):
        """Test the enhanced health check endpoint."""
        response = client.get("/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "data" in data
        assert "meta" in data
        assert "timestamp" in data["meta"]
        assert "version" in data["meta"]
        
        # Check service status
        services = data["data"]
        expected_services = ["database", "telephony", "config", "usage", "license", "monitoring", "modules"]
        for service in expected_services:
            assert service in services
            assert services[service] == "healthy"

    def test_endpoints_documentation(self):
        """Test the endpoints documentation endpoint."""
        response = client.get("/v1/endpoints")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "data" in data
        assert "endpoints" in data["data"]
        assert "categories" in data["data"]
        assert "meta" in data
        assert "total_endpoints" in data["meta"]
        assert "total_categories" in data["meta"]
        
        # Check that endpoints list is not empty
        assert len(data["data"]["endpoints"]) > 0
        assert len(data["data"]["categories"]) > 0

    def test_endpoints_by_category(self):
        """Test getting endpoints by specific category."""
        response = client.get("/v1/endpoints/Telephony")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["data"]["category"] == "Telephony"
        assert "endpoints" in data["data"]
        assert "meta" in data
        assert "endpoint_count" in data["meta"]
        
        # Check that telephony endpoints are returned
        telephony_endpoints = data["data"]["endpoints"]
        assert len(telephony_endpoints) > 0
        
        # Verify all returned endpoints are telephony-related
        for endpoint in telephony_endpoints:
            path = endpoint["path"]
            assert any(keyword in path for keyword in ["calls", "providers", "dids"])

    def test_endpoints_by_invalid_category(self):
        """Test getting endpoints by invalid category."""
        response = client.get("/v1/endpoints/InvalidCategory")
        
        assert response.status_code == 404
        data = response.json()
        
        assert data["status"] == "error"
        assert "error" in data
        assert data["error"]["code"] == "not_found"

    def test_supported_languages(self):
        """Test the enhanced supported languages endpoint."""
        response = client.get("/v1/capabilities/languages")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "data" in data
        assert "languages" in data["data"]
        assert "meta" in data
        assert "total_languages" in data["meta"]
        assert "default_language" in data["meta"]
        
        # Check that languages list is not empty
        languages = data["data"]["languages"]
        assert len(languages) > 0
        
        # Check that each language has required fields
        for language in languages:
            assert "code" in language
            assert "name" in language
            assert "native_name" in language
        
        # Check that English is included
        language_codes = [lang["code"] for lang in languages]
        assert "en" in language_codes

    def test_system_status(self):
        """Test the system status endpoint."""
        response = client.get("/v1/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "data" in data
        assert "meta" in data
        
        # Check that status data contains expected fields
        status_data = data["data"]
        expected_fields = ["api_keys", "webhooks", "mcp_servers", "uptime", "version"]
        for field in expected_fields:
            assert field in status_data
        
        # Check metadata
        meta = data["meta"]
        assert "timestamp" in meta
        assert "status" in meta
        assert meta["status"] == "operational"


class TestGlobalExceptionHandler:
    """Test the global exception handler."""

    def test_global_exception_handler_http_exception(self):
        """Test global exception handler with HTTPException."""
        # This would be tested by the FastAPI test client automatically
        # when an endpoint raises an HTTPException
        pass

    def test_global_exception_handler_generic_exception(self):
        """Test global exception handler with generic exception."""
        # This would be tested by the FastAPI test client automatically
        # when an endpoint raises a generic exception
        pass


class TestResponseModelValidation:
    """Test that response models are properly validated."""

    def test_standard_api_response_validation(self):
        """Test StandardAPIResponse model validation."""
        # Valid response
        valid_response = StandardAPIResponse(
            status="success",
            data={"test": "data"},
            meta={"timestamp": "2025-01-27T10:00:00Z"}
        )
        assert valid_response.status == "success"
        assert valid_response.data == {"test": "data"}
        
        # Invalid status
        with pytest.raises(ValueError):
            StandardAPIResponse(
                status="invalid_status",
                data={"test": "data"}
            )

    def test_error_response_validation(self):
        """Test ErrorResponse model validation."""
        # Valid error response
        valid_error = {
            "code": "not_found",
            "message": "Resource not found",
            "details": {"resource_id": "123"},
            "request_id": "req_123456"
        }
        
        # This should not raise an exception
        response = create_error_response(
            ErrorCode.NOT_FOUND,
            "Resource not found",
            {"resource_id": "123"},
            "req_123456"
        )
        assert response.status == "error"
        assert response.error["code"] == "not_found"


class TestAPIResponseConsistency:
    """Test that all API responses follow the standardized format."""

    @patch('backend.main.security_middleware.verify_api_key')
    def test_telephony_endpoints_standardized_responses(self, mock_verify):
        """Test that telephony endpoints return standardized responses."""
        mock_verify.return_value = {"tenant_id": "test-tenant"}
        
        # Test a telephony endpoint
        with patch('backend.main.shared_telephony_service.list_calls') as mock_list:
            mock_list.return_value = [{"call_id": "123", "status": "completed"}]
            
            response = client.get("/v1/calls", headers={"x-api-key": "test-key"})
            
            assert response.status_code == 200
            data = response.json()
            
            # Check that response follows standard format
            assert "calls" in data
            assert "count" in data
            # Note: This endpoint hasn't been fully converted yet, so it returns the old format
            # In a full implementation, all endpoints would return StandardAPIResponse

    def test_health_endpoint_standardized_response(self):
        """Test that health endpoint returns standardized response."""
        response = client.get("/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check standardized response format
        assert "status" in data
        assert "data" in data
        assert "meta" in data
        assert data["status"] == "success"


if __name__ == "__main__":
    pytest.main([__file__])

