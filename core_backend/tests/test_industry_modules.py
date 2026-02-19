"""
Unit tests for Industry Module Service and API endpoints.

This module tests the industry module functionality including initialization,
capability execution, workflow management, and analytics.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any

from backend.services.industry_modules import IndustryModuleService
from backend.routes.industry_modules import (
    ModuleInitializeRequest,
    CapabilityExecuteRequest,
    WorkflowExecuteRequest
)


class TestIndustryModuleService:
    """Test cases for IndustryModuleService."""

    @pytest.fixture
    def service(self):
        """Create a service instance for testing."""
        return IndustryModuleService()

    @pytest.fixture
    def mock_module(self):
        """Create a mock industry module."""
        mock = Mock()
        mock.name = "Test Module"
        mock.description = "Test module description"
        mock.category = "test"
        
        # Mock async methods
        mock.get_capabilities = AsyncMock(return_value=[
            {"id": "cap1", "name": "Test Capability", "description": "Test capability"}
        ])
        mock.get_automation_workflows = AsyncMock(return_value=[
            {"id": "workflow1", "name": "Test Workflow", "description": "Test workflow"}
        ])
        mock.get_industry_specific_analytics = AsyncMock(return_value={
            "metric1": 100,
            "metric2": 200
        })
        mock.get_compliance_frameworks = AsyncMock(return_value=[
            {"id": "compliance1", "name": "Test Compliance", "description": "Test compliance"}
        ])
        mock.get_integration_points = AsyncMock(return_value=[
            {"id": "integration1", "name": "Test Integration", "description": "Test integration"}
        ])
        mock.execute_capability = AsyncMock(return_value={"result": "success"})
        mock.execute_workflow = AsyncMock(return_value={"result": "success"})
        
        return mock

    @pytest.mark.asyncio
    async def test_initialize_module_success(self, service, mock_module):
        """Test successful module initialization."""
        with patch.object(service, '_module_classes', {'education': Mock(return_value=mock_module)}):
            result = await service.initialize_module(
                tenant_id="test_tenant",
                industry="education",
                settings={"setting1": "value1"}
            )
            
            assert result["capabilities"] == [
                {"id": "cap1", "name": "Test Capability", "description": "Test capability"}
            ]
            assert result["workflows"] == [
                {"id": "workflow1", "name": "Test Workflow", "description": "Test workflow"}
            ]
            assert result["settings"] == {"setting1": "value1"}
            assert "initialized_at" in result

    @pytest.mark.asyncio
    async def test_initialize_module_unsupported_industry(self, service):
        """Test initialization with unsupported industry."""
        with pytest.raises(ValueError, match="Unsupported industry"):
            await service.initialize_module(
                tenant_id="test_tenant",
                industry="unsupported_industry",
                settings={}
            )

    @pytest.mark.asyncio
    async def test_execute_capability_success(self, service, mock_module):
        """Test successful capability execution."""
        with patch.object(service, '_module_classes', {'education': Mock(return_value=mock_module)}):
            # Initialize module first
            await service.initialize_module("test_tenant", "education", {})
            
            result = await service.execute_capability(
                tenant_id="test_tenant",
                industry="education",
                capability="test_capability",
                params={"param1": "value1"}
            )
            
            assert result["success"] is True
            assert result["capability"] == "test_capability"
            assert result["result"] == {"result": "success"}
            assert "executed_at" in result

    @pytest.mark.asyncio
    async def test_execute_workflow_success(self, service, mock_module):
        """Test successful workflow execution."""
        with patch.object(service, '_module_classes', {'education': Mock(return_value=mock_module)}):
            # Initialize module first
            await service.initialize_module("test_tenant", "education", {})
            
            result = await service.execute_workflow(
                tenant_id="test_tenant",
                industry="education",
                workflow="workflow1",
                params={"param1": "value1"}
            )
            
            assert result["success"] is True
            assert result["workflow"] == "workflow1"
            assert result["result"] == {"result": "success"}
            assert "executed_at" in result

    @pytest.mark.asyncio
    async def test_get_module_capabilities(self, service, mock_module):
        """Test getting module capabilities."""
        with patch.object(service, '_module_classes', {'education': Mock(return_value=mock_module)}):
            # Initialize module first
            await service.initialize_module("test_tenant", "education", {})
            
            capabilities = await service.get_module_capabilities(
                tenant_id="test_tenant",
                industry="education"
            )
            
            assert len(capabilities) == 1
            assert capabilities[0]["id"] == "cap1"
            assert capabilities[0]["name"] == "Test Capability"

    @pytest.mark.asyncio
    async def test_get_module_workflows(self, service, mock_module):
        """Test getting module workflows."""
        with patch.object(service, '_module_classes', {'education': Mock(return_value=mock_module)}):
            # Initialize module first
            await service.initialize_module("test_tenant", "education", {})
            
            workflows = await service.get_module_workflows(
                tenant_id="test_tenant",
                industry="education"
            )
            
            assert len(workflows) == 1
            assert workflows[0]["id"] == "workflow1"
            assert workflows[0]["name"] == "Test Workflow"

    @pytest.mark.asyncio
    async def test_get_module_analytics(self, service, mock_module):
        """Test getting module analytics."""
        with patch.object(service, '_module_classes', {'education': Mock(return_value=mock_module)}):
            # Initialize module first
            await service.initialize_module("test_tenant", "education", {})
            
            analytics = await service.get_module_analytics(
                tenant_id="test_tenant",
                industry="education",
                metrics=["metric1", "metric2"],
                time_range="7d",
                filters={"filter1": "value1"}
            )
            
            assert analytics["industry"] == "education"
            assert analytics["metrics"]["metric1"] == 100
            assert analytics["metrics"]["metric2"] == 200
            assert analytics["time_range"] == "7d"
            assert analytics["filters"] == {"filter1": "value1"}

    @pytest.mark.asyncio
    async def test_get_module_compliance(self, service, mock_module):
        """Test getting module compliance information."""
        with patch.object(service, '_module_classes', {'education': Mock(return_value=mock_module)}):
            # Initialize module first
            await service.initialize_module("test_tenant", "education", {})
            
            compliance = await service.get_module_compliance(
                tenant_id="test_tenant",
                industry="education"
            )
            
            assert compliance["industry"] == "education"
            assert len(compliance["compliance_frameworks"]) == 1
            assert compliance["compliance_frameworks"][0]["id"] == "compliance1"

    @pytest.mark.asyncio
    async def test_get_module_integrations(self, service, mock_module):
        """Test getting module integration points."""
        with patch.object(service, '_module_classes', {'education': Mock(return_value=mock_module)}):
            # Initialize module first
            await service.initialize_module("test_tenant", "education", {})
            
            integrations = await service.get_module_integrations(
                tenant_id="test_tenant",
                industry="education"
            )
            
            assert integrations["industry"] == "education"
            assert len(integrations["integration_points"]) == 1
            assert integrations["integration_points"][0]["id"] == "integration1"

    @pytest.mark.asyncio
    async def test_get_module_health_initialized(self, service, mock_module):
        """Test getting health status for initialized module."""
        with patch.object(service, '_module_classes', {'education': Mock(return_value=mock_module)}):
            # Initialize module first
            await service.initialize_module("test_tenant", "education", {})
            
            health = await service.get_module_health(
                tenant_id="test_tenant",
                industry="education"
            )
            
            assert health["status"] == "healthy"
            assert health["module_id"] == "education_test_tenant"
            assert health["industry"] == "education"
            assert health["capabilities_count"] == 1
            assert health["workflows_count"] == 1

    @pytest.mark.asyncio
    async def test_get_module_health_not_initialized(self, service):
        """Test getting health status for non-initialized module."""
        health = await service.get_module_health(
            tenant_id="test_tenant",
            industry="education"
        )
        
        assert health["status"] == "not_initialized"
        assert "not initialized" in health["message"]

    @pytest.mark.asyncio
    async def test_get_available_industries(self, service, mock_module):
        """Test getting available industries."""
        with patch.object(service, '_module_classes', {'education': Mock(return_value=mock_module)}):
            industries = await service.get_available_industries()
            
            # Find education industry
            education_industry = next((i for i in industries if i["id"] == "education"), None)
            assert education_industry is not None
            assert education_industry["available"] is True
            assert education_industry["name"] == "Test Module"
            assert education_industry["description"] == "Test module description"


class TestIndustryModuleRequestModels:
    """Test cases for request models."""

    def test_module_initialize_request(self):
        """Test ModuleInitializeRequest model."""
        request = ModuleInitializeRequest(
            settings={"setting1": "value1", "setting2": "value2"},
            tenant_config={"config1": "value1"}
        )
        
        assert request.settings == {"setting1": "value1", "setting2": "value2"}
        assert request.tenant_config == {"config1": "value1"}

    def test_capability_execute_request(self):
        """Test CapabilityExecuteRequest model."""
        request = CapabilityExecuteRequest(
            params={"param1": "value1"},
            context={"context1": "value1"}
        )
        
        assert request.params == {"param1": "value1"}
        assert request.context == {"context1": "value1"}

    def test_workflow_execute_request(self):
        """Test WorkflowExecuteRequest model."""
        request = WorkflowExecuteRequest(
            params={"param1": "value1"},
            context={"context1": "value1"}
        )
        
        assert request.params == {"param1": "value1"}
        assert request.context == {"context1": "value1"}


class TestIndustryModuleServiceEdgeCases:
    """Test edge cases for IndustryModuleService."""

    @pytest.fixture
    def service(self):
        """Create a service instance for testing."""
        return IndustryModuleService()

    @pytest.mark.asyncio
    async def test_execute_capability_module_not_initialized(self, service, mock_module):
        """Test capability execution when module is not initialized."""
        with patch.object(service, '_module_classes', {'education': Mock(return_value=mock_module)}):
            result = await service.execute_capability(
                tenant_id="test_tenant",
                industry="education",
                capability="test_capability",
                params={"param1": "value1"}
            )
            
            # Should auto-initialize and execute
            assert result["success"] is True
            assert result["capability"] == "test_capability"

    @pytest.mark.asyncio
    async def test_execute_workflow_module_not_initialized(self, service, mock_module):
        """Test workflow execution when module is not initialized."""
        with patch.object(service, '_module_classes', {'education': Mock(return_value=mock_module)}):
            result = await service.execute_workflow(
                tenant_id="test_tenant",
                industry="education",
                workflow="workflow1",
                params={"param1": "value1"}
            )
            
            # Should auto-initialize and execute
            assert result["success"] is True
            assert result["workflow"] == "workflow1"

    @pytest.mark.asyncio
    async def test_get_module_analytics_filtered_metrics(self, service, mock_module):
        """Test analytics with filtered metrics."""
        with patch.object(service, '_module_classes', {'education': Mock(return_value=mock_module)}):
            # Initialize module first
            await service.initialize_module("test_tenant", "education", {})
            
            analytics = await service.get_module_analytics(
                tenant_id="test_tenant",
                industry="education",
                metrics=["metric1"],  # Only request metric1
                time_range="7d"
            )
            
            assert "metric1" in analytics["metrics"]
            assert "metric2" not in analytics["metrics"]  # Should be filtered out

    @pytest.mark.asyncio
    async def test_get_module_analytics_no_filters(self, service, mock_module):
        """Test analytics without filters."""
        with patch.object(service, '_module_classes', {'education': Mock(return_value=mock_module)}):
            # Initialize module first
            await service.initialize_module("test_tenant", "education", {})
            
            analytics = await service.get_module_analytics(
                tenant_id="test_tenant",
                industry="education",
                metrics=["metric1", "metric2"],
                time_range="7d"
            )
            
            assert analytics["filters"] == {}  # Should be empty dict when no filters provided


if __name__ == "__main__":
    pytest.main([__file__])
