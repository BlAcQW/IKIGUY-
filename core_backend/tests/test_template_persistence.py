"""
Tests for automation template MongoDB persistence
"""
import pytest
from unittest.mock import MagicMock, patch
from backend.routes.automation_templates import (
    create_default_templates,
    router
)
from backend.models.automation_template import (
    AutomationTemplate,
    TemplateIndustry,
    TemplateCategory
)
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestTemplatePersistence:
    """Test MongoDB persistence for automation templates."""

    @patch('apps.core_backend.backend.routes.automation_templates.get_collection')
    @patch('apps.core_backend.backend.routes.automation_templates.get_current_user_mongo')
    def test_create_template_stores_in_mongodb(self, mock_auth, mock_collection):
        """Test that creating a template stores it in MongoDB."""
        mock_auth.return_value = {"email": "test@example.com"}
        mock_collection_instance = MagicMock()
        mock_collection.return_value = mock_collection_instance

        template_data = {
            "template_name": "Test Template",
            "industry": "Healthcare",
            "category": "helpdesk",
            "description": "Test description",
            "company_name": "Test Company"
        }

        response = client.post("/automation-templates/create", json=template_data)

        # Verify the response
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["message"] == "Template created successfully"

        # Verify MongoDB was called
        mock_collection.assert_called_with("automation_templates")
        mock_collection_instance.insert_one.assert_called_once()

        # Verify the inserted document structure
        insert_call = mock_collection_instance.insert_one.call_args[0][0]
        assert insert_call["template_name"] == "Test Template"
        assert insert_call["industry"] == "Healthcare"
        assert "_id" in insert_call

    @patch('apps.core_backend.backend.routes.automation_templates.get_collection')
    @patch('apps.core_backend.backend.routes.automation_templates.get_current_user_mongo')
    def test_list_templates_from_mongodb(self, mock_auth, mock_collection):
        """Test that listing templates retrieves from MongoDB."""
        mock_auth.return_value = {"email": "test@example.com"}
        mock_collection_instance = MagicMock()
        mock_collection.return_value = mock_collection_instance

        # Mock MongoDB response
        mock_collection_instance.find.return_value.sort.return_value = [
            {
                "_id": "test-id-1",
                "template_name": "Test Template 1",
                "industry": "Healthcare",
                "category": "helpdesk",
                "description": "Test description",
                "company_name": "Test Company",
                "system_prompt": "Test prompt",
                "knowledge_base_docs": [],
                "custom_tool_names": [],
                "integrations": [],
                "vapi_config": {
                    "model": "gpt-4o",
                    "voice_id": "jennifer",
                    "voice_provider": "11labs",
                    "temperature": 0.3,
                    "max_tokens": 250,
                    "max_duration": 600,
                    "first_message": "Hello",
                    "end_call_message": "Goodbye",
                    "tools": [],
                    "compliance_level": "Standard"
                },
                "n8n_config": {
                    "workflow_name": "Test Workflow",
                    "webhook_path": "/test",
                    "nodes": [],
                    "connections": {},
                    "endpoints": {}
                },
                "demo_config": {
                    "enabled": True,
                    "theme": "default",
                    "brand_colors": ["#2563eb"],
                    "interactive_features": [],
                    "emergency_simulation": False
                },
                "monitoring_config": {
                    "enabled": True,
                    "kpis": [],
                    "alert_rules": [],
                    "dashboard_widgets": [],
                    "compliance_monitoring": False
                },
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "created_by": "system",
                "is_active": True,
                "usage_count": 0,
                "version": "1.0.0"
            }
        ]

        response = client.get("/automation-templates/list")

        # Verify the response
        assert response.status_code == 200
        templates = response.json()
        assert len(templates) == 1
        assert templates[0]["template_name"] == "Test Template 1"
        assert templates[0]["id"] == "test-id-1"

        # Verify MongoDB was queried correctly
        mock_collection.assert_called_with("automation_templates")
        mock_collection_instance.find.assert_called_once()

    @patch('apps.core_backend.backend.routes.automation_templates.get_collection')
    @patch('apps.core_backend.backend.routes.automation_templates.get_current_user_mongo')
    def test_update_template_in_mongodb(self, mock_auth, mock_collection):
        """Test that updating a template modifies it in MongoDB."""
        mock_auth.return_value = {"email": "test@example.com"}
        mock_collection_instance = MagicMock()
        mock_collection.return_value = mock_collection_instance

        # Mock finding the template
        mock_collection_instance.find_one.side_effect = [
            {"_id": "test-id", "template_name": "Original Name"},  # First call (check exists)
            {  # Second call (get updated)
                "_id": "test-id",
                "template_name": "Updated Name",
                "industry": "Healthcare",
                "category": "helpdesk",
                "description": "Test description",
                "company_name": "Test Company",
                "system_prompt": "Test prompt",
                "knowledge_base_docs": [],
                "custom_tool_names": [],
                "integrations": [],
                "vapi_config": {
                    "model": "gpt-4o",
                    "voice_id": "jennifer",
                    "voice_provider": "11labs",
                    "temperature": 0.3,
                    "max_tokens": 250,
                    "max_duration": 600,
                    "first_message": "Hello",
                    "end_call_message": "Goodbye",
                    "tools": [],
                    "compliance_level": "Standard"
                },
                "n8n_config": {
                    "workflow_name": "Test Workflow",
                    "webhook_path": "/test",
                    "nodes": [],
                    "connections": {},
                    "endpoints": {}
                },
                "demo_config": {
                    "enabled": True,
                    "theme": "default",
                    "brand_colors": ["#2563eb"],
                    "interactive_features": [],
                    "emergency_simulation": False
                },
                "monitoring_config": {
                    "enabled": True,
                    "kpis": [],
                    "alert_rules": [],
                    "dashboard_widgets": [],
                    "compliance_monitoring": False
                },
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "created_by": "system",
                "is_active": True,
                "usage_count": 0,
                "version": "1.0.0"
            }
        ]

        update_data = {
            "template_name": "Updated Name"
        }

        response = client.put("/automation-templates/test-id", json=update_data)

        # Verify the response
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["template"]["template_name"] == "Updated Name"

        # Verify MongoDB update was called
        mock_collection_instance.update_one.assert_called_once()
        update_call = mock_collection_instance.update_one.call_args
        assert update_call[0][0] == {"_id": "test-id"}  # Filter
        assert "template_name" in update_call[0][1]["$set"]  # Update data

    @patch('apps.core_backend.backend.routes.automation_templates.get_collection')
    @patch('apps.core_backend.backend.routes.automation_templates.get_current_user_mongo')
    def test_delete_template_from_mongodb(self, mock_auth, mock_collection):
        """Test that deleting a template removes it from MongoDB."""
        mock_auth.return_value = {"email": "test@example.com"}
        mock_collection_instance = MagicMock()
        mock_collection.return_value = mock_collection_instance

        # Mock finding the template
        mock_collection_instance.find_one.return_value = {"_id": "test-id"}
        mock_collection_instance.delete_one.return_value.deleted_count = 1

        response = client.delete("/automation-templates/test-id")

        # Verify the response
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["message"] == "Template deleted successfully"

        # Verify MongoDB delete was called
        mock_collection_instance.delete_one.assert_called_once_with({"_id": "test-id"})

    @patch('apps.core_backend.backend.routes.automation_templates.get_collection')
    @patch('apps.core_backend.backend.routes.automation_templates.get_current_user_mongo')
    def test_populate_defaults_clears_and_inserts(self, mock_auth, mock_collection):
        """Test that populating defaults clears existing and inserts new templates."""
        mock_auth.return_value = {"email": "test@example.com"}
        mock_collection_instance = MagicMock()
        mock_collection.return_value = mock_collection_instance

        response = client.post("/automation-templates/populate-defaults")

        # Verify the response
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "Created 12 default templates" in result["message"]

        # Verify MongoDB operations
        mock_collection_instance.delete_many.assert_called_once_with({})
        mock_collection_instance.insert_many.assert_called_once()

        # Verify 12 templates were inserted
        insert_call = mock_collection_instance.insert_many.call_args[0][0]
        assert len(insert_call) == 12

    @patch('apps.core_backend.backend.routes.automation_templates.get_collection')
    @patch('apps.core_backend.backend.routes.automation_templates.get_current_user_mongo')
    def test_get_template_increments_usage_count(self, mock_auth, mock_collection):
        """Test that getting a template increments its usage count."""
        mock_auth.return_value = {"email": "test@example.com"}
        mock_collection_instance = MagicMock()
        mock_collection.return_value = mock_collection_instance

        # Mock finding the template
        mock_collection_instance.find_one.return_value = {
            "_id": "test-id",
            "template_name": "Test Template",
            "industry": "Healthcare",
            "category": "helpdesk",
            "description": "Test description",
            "company_name": "Test Company",
            "system_prompt": "Test prompt",
            "knowledge_base_docs": [],
            "custom_tool_names": [],
            "integrations": [],
            "vapi_config": {
                "model": "gpt-4o",
                "voice_id": "jennifer",
                "voice_provider": "11labs",
                "temperature": 0.3,
                "max_tokens": 250,
                "max_duration": 600,
                "first_message": "Hello",
                "end_call_message": "Goodbye",
                "tools": [],
                "compliance_level": "Standard"
            },
            "n8n_config": {
                "workflow_name": "Test Workflow",
                "webhook_path": "/test",
                "nodes": [],
                "connections": {},
                "endpoints": {}
            },
            "demo_config": {
                "enabled": True,
                "theme": "default",
                "brand_colors": ["#2563eb"],
                "interactive_features": [],
                "emergency_simulation": False
            },
            "monitoring_config": {
                "enabled": True,
                "kpis": [],
                "alert_rules": [],
                "dashboard_widgets": [],
                "compliance_monitoring": False
            },
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "created_by": "system",
            "is_active": True,
            "usage_count": 5,
            "version": "1.0.0"
        }

        response = client.get("/automation-templates/test-id")

        # Verify the response
        assert response.status_code == 200
        template = response.json()
        assert template["usage_count"] == 6  # Incremented

        # Verify usage count was incremented in MongoDB
        mock_collection_instance.update_one.assert_called_once_with(
            {"_id": "test-id"},
            {"$inc": {"usage_count": 1}}
        )


class TestTemplateFiltering:
    """Test template filtering and querying functionality."""

    @patch('apps.core_backend.backend.routes.automation_templates.get_collection')
    @patch('apps.core_backend.backend.routes.automation_templates.get_current_user_mongo')
    def test_filter_by_industry(self, mock_auth, mock_collection):
        """Test filtering templates by industry."""
        mock_auth.return_value = {"email": "test@example.com"}
        mock_collection_instance = MagicMock()
        mock_collection.return_value = mock_collection_instance

        # Mock empty result
        mock_collection_instance.find.return_value.sort.return_value = []

        response = client.get("/automation-templates/list?industry=Healthcare")

        # Verify the filter was applied
        mock_collection_instance.find.assert_called_with({"industry": "Healthcare", "is_active": True})

    @patch('apps.core_backend.backend.routes.automation_templates.get_collection')
    @patch('apps.core_backend.backend.routes.automation_templates.get_current_user_mongo')
    def test_filter_by_category(self, mock_auth, mock_collection):
        """Test filtering templates by category."""
        mock_auth.return_value = {"email": "test@example.com"}
        mock_collection_instance = MagicMock()
        mock_collection.return_value = mock_collection_instance

        # Mock empty result
        mock_collection_instance.find.return_value.sort.return_value = []

        response = client.get("/automation-templates/list?category=helpdesk")

        # Verify the filter was applied
        mock_collection_instance.find.assert_called_with({"category": "helpdesk", "is_active": True})

    @patch('apps.core_backend.backend.routes.automation_templates.get_collection')
    @patch('apps.core_backend.backend.routes.automation_templates.get_current_user_mongo')
    def test_include_inactive_templates(self, mock_auth, mock_collection):
        """Test including inactive templates when active_only=false."""
        mock_auth.return_value = {"email": "test@example.com"}
        mock_collection_instance = MagicMock()
        mock_collection.return_value = mock_collection_instance

        # Mock empty result
        mock_collection_instance.find.return_value.sort.return_value = []

        response = client.get("/automation-templates/list?active_only=false")

        # Verify no active filter was applied
        mock_collection_instance.find.assert_called_with({})


if __name__ == "__main__":
    pytest.main([__file__])