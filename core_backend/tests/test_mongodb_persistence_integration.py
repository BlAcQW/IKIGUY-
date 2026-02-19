"""
Unit tests for MongoDB persistence integration.
Tests automation config creation and persistence functionality.
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from bson import ObjectId

# Add the backend directory to Python path
sys.path.append('/opt/kasaai/apps/core_backend')

from backend.models.automation_config import (
    AutomationConfig,
    AutomationConfigCreate,
    AutomationConfigResponse,
    CompanyInfo,
    VAPIAgent,
    VoiceSettings,
    DemoSettings,
    AutomationStatus
)

class TestMongoDBPersistenceIntegration:
    """Test suite for MongoDB persistence integration."""

    @pytest.fixture
    def sample_company_info(self):
        """Sample company information for testing."""
        return {
            "name": "TechCorp Solutions",
            "description": "Leading technology consulting firm",
            "url": "https://techcorp.com",
            "extracted_info": {
                "services": ["Software Development", "Cloud Migration", "Data Analytics"],
                "businessHours": "Monday-Friday 9AM-6PM",
                "contactInfo": {
                    "phone": "+1-555-0123",
                    "email": "contact@techcorp.com"
                },
                "aboutText": "TechCorp Solutions delivers innovative technology solutions."
            }
        }

    @pytest.fixture
    def sample_vapi_agent(self):
        """Sample VAPI agent configuration for testing."""
        return {
            "assistant_id": "vapi_assistant_123",
            "phone_number_id": "",
            "system_prompt": "You are TechCorp Solutions' AI assistant...",
            "voice_settings": {
                "voice_id": "jennifer",
                "model": "nova-2",
                "max_duration": 600
            },
            "tools": []
        }

    @pytest.fixture
    def sample_demo_settings(self):
        """Sample demo settings for testing."""
        return {
            "enable_demo": True,
            "demo_url": "https://demo.ailabsafrica.com/techcorp-demo-123.html",
            "html_template": "<html><body>Demo page</body></html>"
        }

    @pytest.fixture
    def sample_automation_config_create(self, sample_company_info, sample_vapi_agent, sample_demo_settings):
        """Sample automation config creation request."""
        return {
            "automation_name": "TechCorp VAPI Quick Deploy",
            "company_info": sample_company_info,
            "vapi_agent": sample_vapi_agent,
            "n8n_workflow": {
                "workflow_id": "",
                "workflow_name": "Default Workflow",
                "webhook_url": "",
                "endpoints": {
                    "calendar": "/calendar/availability",
                    "tickets": "/tickets/create",
                    "availability": "/availability/check",
                    "escalation": "/escalation/route",
                    "analytics": "/analytics/track"
                }
            },
            "demo_settings": sample_demo_settings,
            "template_id": "vapi_quick_deploy"
        }

    @pytest.fixture
    def mock_automation_configs_collection(self):
        """Mock MongoDB collection for automation configs."""
        mock_collection = Mock()
        mock_collection.insert_one = Mock()
        mock_collection.find_one = Mock()
        mock_collection.update_one = Mock()
        mock_collection.delete_one = Mock()
        mock_collection.count_documents = Mock()
        mock_collection.find = Mock()
        return mock_collection

    def test_automation_config_model_validation(self, sample_automation_config_create):
        """Test AutomationConfig model validation."""
        # Test valid configuration
        config = AutomationConfigCreate(**sample_automation_config_create)
        assert config.automation_name == "TechCorp VAPI Quick Deploy"
        assert config.company_info.name == "TechCorp Solutions"
        assert config.vapi_agent.assistant_id == "vapi_assistant_123"
        assert config.demo_settings.demo_url == "https://demo.ailabsafrica.com/techcorp-demo-123.html"

        # Test default values
        minimal_config = AutomationConfigCreate(automation_name="Test Automation")
        assert minimal_config.automation_name == "Test Automation"
        assert minimal_config.company_info is None
        assert minimal_config.vapi_agent is None

    def test_demo_settings_model(self, sample_demo_settings):
        """Test DemoSettings model functionality."""
        demo = DemoSettings(**sample_demo_settings)
        assert demo.enable_demo is True
        assert demo.demo_url == "https://demo.ailabsafrica.com/techcorp-demo-123.html"
        assert demo.html_template == "<html><body>Demo page</body></html>"

        # Test defaults
        default_demo = DemoSettings()
        assert default_demo.enable_demo is True
        assert default_demo.demo_url == ""
        assert default_demo.html_template == ""

    def test_company_info_model(self, sample_company_info):
        """Test CompanyInfo model functionality."""
        company = CompanyInfo(**sample_company_info)
        assert company.name == "TechCorp Solutions"
        assert company.description == "Leading technology consulting firm"
        assert company.url == "https://techcorp.com"
        assert company.extracted_info is not None
        assert "services" in company.extracted_info

    def test_vapi_agent_model(self, sample_vapi_agent):
        """Test VAPIAgent model functionality."""
        vapi = VAPIAgent(**sample_vapi_agent)
        assert vapi.assistant_id == "vapi_assistant_123"
        assert vapi.system_prompt.startswith("You are TechCorp Solutions")
        assert vapi.voice_settings.voice_id == "jennifer"
        assert vapi.voice_settings.model == "nova-2"
        assert vapi.voice_settings.max_duration == 600

        # Test defaults
        minimal_vapi = VAPIAgent(
            system_prompt="Test prompt",
            voice_settings=VoiceSettings(voice_id="alloy", model="nova-2")
        )
        assert minimal_vapi.assistant_id == ""
        assert minimal_vapi.phone_number_id == ""
        assert minimal_vapi.tools == []

    @pytest.mark.asyncio
    async def test_automation_config_creation_endpoint_success(
        self,
        sample_automation_config_create,
        mock_automation_configs_collection
    ):
        """Test successful automation config creation via API endpoint."""
        from backend.routes.automation_configs import create_automation_config
        from backend.auth import get_current_user_mongo

        # Mock successful database insertion
        mock_object_id = ObjectId()
        mock_automation_configs_collection.insert_one.return_value.inserted_id = mock_object_id

        # Mock successful document retrieval
        created_doc = {
            "_id": mock_object_id,
            **sample_automation_config_create,
            "status": "draft",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow(),
            "userId": "test_user_123"
        }
        mock_automation_configs_collection.find_one.return_value = created_doc

        # Mock current user
        mock_user = {"id": "test_user_123", "sub": "test_user_123"}

        with patch('backend.routes.automation_configs.automation_configs_collection', mock_automation_configs_collection), \
             patch('backend.routes.automation_configs.get_current_user_mongo', return_value=mock_user):

            request = AutomationConfigCreate(**sample_automation_config_create)
            response = await create_automation_config(request, mock_user)

            # Verify database operations
            mock_automation_configs_collection.insert_one.assert_called_once()
            mock_automation_configs_collection.find_one.assert_called_once_with({"_id": mock_object_id})

            # Verify response
            assert response.automation_name == "TechCorp VAPI Quick Deploy"
            assert response.company_info.name == "TechCorp Solutions"
            assert response.demo_settings.demo_url == "https://demo.ailabsafrica.com/techcorp-demo-123.html"

    @pytest.mark.asyncio
    async def test_automation_config_creation_with_defaults(self, mock_automation_configs_collection):
        """Test automation config creation with default values applied."""
        from backend.routes.automation_configs import create_automation_config

        # Minimal request with only automation name
        minimal_request = AutomationConfigCreate(automation_name="Minimal Test Automation")
        mock_user = {"id": "test_user_123"}

        # Mock database operations
        mock_object_id = ObjectId()
        mock_automation_configs_collection.insert_one.return_value.inserted_id = mock_object_id

        created_doc = {
            "_id": mock_object_id,
            "automation_name": "Minimal Test Automation",
            "status": "draft",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow(),
            "userId": "test_user_123",
            "companyInfo": {"name": "", "description": "", "url": ""},
            "vapiAgent": {
                "assistantId": "",
                "phoneNumberId": "",
                "systemPrompt": "You are a helpful assistant",
                "voiceSettings": {"voiceId": "jennifer", "model": "nova-2", "maxDuration": 600},
                "tools": []
            },
            "demoSettings": {"enableDemo": True, "demoUrl": "", "htmlTemplate": ""}
        }
        mock_automation_configs_collection.find_one.return_value = created_doc

        with patch('backend.routes.automation_configs.automation_configs_collection', mock_automation_configs_collection):
            response = await create_automation_config(minimal_request, mock_user)

            # Verify defaults were applied
            insert_call_args = mock_automation_configs_collection.insert_one.call_args[0][0]
            assert insert_call_args["companyInfo"]["name"] == ""
            assert insert_call_args["vapiAgent"]["systemPrompt"] == "You are a helpful assistant"
            assert insert_call_args["demoSettings"]["enableDemo"] is True

    def test_automation_config_status_transitions(self):
        """Test automation config status transitions."""
        # Test valid status values
        assert AutomationStatus.DRAFT == "draft"
        assert AutomationStatus.DEPLOYED == "deployed"
        assert AutomationStatus.STOPPED == "stopped"

        # Test status in model
        config_data = {
            "automation_name": "Test Automation",
            "company_info": CompanyInfo(name="Test Company", description="Test", url="https://test.com"),
            "vapi_agent": VAPIAgent(
                system_prompt="Test prompt",
                voice_settings=VoiceSettings(voice_id="alloy", model="nova-2")
            ),
            "status": AutomationStatus.DRAFT
        }

        # This should not raise validation errors
        config = AutomationConfig(**config_data)
        assert config.status == AutomationStatus.DRAFT

    @pytest.mark.asyncio
    async def test_automation_config_update_demo_url(self, mock_automation_configs_collection):
        """Test updating automation config with demo URL after deployment."""
        from backend.routes.automation_configs import update_automation_config
        from backend.models.automation_config import AutomationConfigUpdate

        config_id = str(ObjectId())
        mock_user = {"id": "test_user_123"}

        # Update request with demo URL
        update_request = AutomationConfigUpdate(
            demo_settings=DemoSettings(
                enable_demo=True,
                demo_url="https://demo.ailabsafrica.com/techcorp-deployed-456.html",
                html_template="<html>Updated demo</html>"
            ),
            status=AutomationStatus.DEPLOYED
        )

        # Mock successful update
        mock_automation_configs_collection.update_one.return_value.matched_count = 1

        # Mock updated document retrieval
        updated_doc = {
            "_id": ObjectId(config_id),
            "automation_name": "TechCorp VAPI Quick Deploy",
            "status": "deployed",
            "demoSettings": {
                "enableDemo": True,
                "demoUrl": "https://demo.ailabsafrica.com/techcorp-deployed-456.html",
                "htmlTemplate": "<html>Updated demo</html>"
            },
            "updatedAt": datetime.utcnow(),
            "userId": "test_user_123"
        }
        mock_automation_configs_collection.find_one.return_value = updated_doc

        with patch('backend.routes.automation_configs.automation_configs_collection', mock_automation_configs_collection):
            response = await update_automation_config(config_id, update_request, mock_user)

            # Verify update operation
            mock_automation_configs_collection.update_one.assert_called_once()
            update_call_args = mock_automation_configs_collection.update_one.call_args
            assert update_call_args[0][0] == {"_id": ObjectId(config_id), "userId": "test_user_123"}

            # Verify demo URL was updated
            update_data = update_call_args[0][1]["$set"]
            assert "demoSettings" in update_data
            assert update_data["demoSettings"]["demoUrl"] == "https://demo.ailabsafrica.com/techcorp-deployed-456.html"

    @pytest.mark.asyncio
    async def test_automation_config_retrieval_by_id(self, mock_automation_configs_collection):
        """Test retrieving automation config by ID."""
        from backend.routes.automation_configs import get_automation_config

        config_id = str(ObjectId())
        mock_user = {"id": "test_user_123"}

        # Mock document retrieval
        doc = {
            "_id": ObjectId(config_id),
            "automation_name": "TechCorp VAPI Quick Deploy",
            "companyInfo": {"name": "TechCorp Solutions", "description": "Tech consulting", "url": "https://techcorp.com"},
            "vapiAgent": {"assistantId": "vapi_123", "systemPrompt": "Test prompt"},
            "demoSettings": {"enableDemo": True, "demoUrl": "https://demo.ailabsafrica.com/test.html"},
            "status": "deployed",
            "userId": "test_user_123",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        mock_automation_configs_collection.find_one.return_value = doc

        with patch('backend.routes.automation_configs.automation_configs_collection', mock_automation_configs_collection):
            response = await get_automation_config(config_id, mock_user)

            # Verify retrieval operation
            mock_automation_configs_collection.find_one.assert_called_once_with({
                "_id": ObjectId(config_id),
                "userId": "test_user_123"
            })

            # Verify response
            assert response.id == config_id
            assert response.automation_name == "TechCorp VAPI Quick Deploy"
            assert response.demo_settings.demo_url == "https://demo.ailabsafrica.com/test.html"

    @pytest.mark.asyncio
    async def test_automation_config_not_found(self, mock_automation_configs_collection):
        """Test handling of non-existent automation config."""
        from backend.routes.automation_configs import get_automation_config
        from fastapi import HTTPException

        config_id = str(ObjectId())
        mock_user = {"id": "test_user_123"}

        # Mock no document found
        mock_automation_configs_collection.find_one.return_value = None

        with patch('backend.routes.automation_configs.automation_configs_collection', mock_automation_configs_collection):
            with pytest.raises(HTTPException) as exc_info:
                await get_automation_config(config_id, mock_user)

            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail

    def test_data_integrity_validation(self):
        """Test data integrity validation for automation configs."""
        # Test required fields validation
        with pytest.raises(ValueError):
            AutomationConfig()  # Missing required fields

        # Test valid minimal config
        minimal_config = AutomationConfig(
            automation_name="Test",
            company_info=CompanyInfo(name="Test Corp", description="Test", url="https://test.com"),
            vapi_agent=VAPIAgent(
                system_prompt="Test prompt",
                voice_settings=VoiceSettings(voice_id="alloy", model="nova-2")
            ),
            n8n_workflow={
                "workflow_name": "Test Workflow",
                "endpoints": {}
            }
        )
        assert minimal_config.automation_name == "Test"

    @pytest.mark.asyncio
    async def test_bulk_automation_config_operations(self, mock_automation_configs_collection):
        """Test bulk operations on automation configs."""
        from backend.routes.automation_configs import list_automation_configs

        mock_user = {"id": "test_user_123"}

        # Mock multiple documents
        docs = [
            {
                "_id": ObjectId(),
                "automation_name": f"Automation {i}",
                "status": "deployed" if i % 2 == 0 else "draft",
                "userId": "test_user_123",
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }
            for i in range(5)
        ]

        mock_automation_configs_collection.count_documents.return_value = 5
        mock_cursor = Mock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = Mock(return_value=iter(docs))
        mock_automation_configs_collection.find.return_value = mock_cursor

        with patch('backend.routes.automation_configs.automation_configs_collection', mock_automation_configs_collection):
            response = await list_automation_configs(status=None, limit=10, offset=0, current_user=mock_user)

            # Verify query operation
            expected_query = {"userId": "test_user_123", "_id": {"$ne": None, "$exists": True, "$type": "objectId"}}
            mock_automation_configs_collection.find.assert_called_once_with(expected_query)

            # Verify response structure
            assert response["total"] == 5
            assert len(response["configs"]) <= 5  # Some might fail conversion

    def test_model_serialization_deserialization(self, sample_automation_config_create):
        """Test model serialization and deserialization for API compatibility."""
        # Test AutomationConfigCreate serialization
        config_create = AutomationConfigCreate(**sample_automation_config_create)
        config_dict = config_create.dict()

        # Verify all fields are properly serialized
        assert config_dict["automation_name"] == "TechCorp VAPI Quick Deploy"
        assert config_dict["company_info"]["name"] == "TechCorp Solutions"
        assert config_dict["vapi_agent"]["assistant_id"] == "vapi_assistant_123"
        assert config_dict["demo_settings"]["demo_url"] == "https://demo.ailabsafrica.com/techcorp-demo-123.html"

        # Test deserialization from dict
        recreated_config = AutomationConfigCreate(**config_dict)
        assert recreated_config.automation_name == config_create.automation_name
        assert recreated_config.company_info.name == config_create.company_info.name


if __name__ == "__main__":
    pytest.main([__file__])