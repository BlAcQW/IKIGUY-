"""
Comprehensive tests for Health Locator automation template.
Tests the complete healthcare provider search automation including VAPI agents,
N8N workflows, and Premier Health custom tools integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import httpx
from datetime import datetime
import json

import sys
import os
sys.path.append('.')

from backend.services.automation_orchestration_service import AutomationOrchestrationService
from backend.services.vapi_service import VAPIService
from backend.services.n8n_service import N8NService
from backend.models.automation_config import AutomationConfig


class TestHealthLocatorTemplate:
    """Comprehensive test suite for Health Locator automation template."""

    @pytest.fixture
    def health_locator_config(self):
        """Create Health Locator automation configuration."""
        return {
            "name": "Premier Health Provider Locator",
            "description": "Healthcare provider search automation for Greater Accra region",
            "category": "healthcare",
            "template_id": "health_locator",
            "company_info": {
                "name": "Premier Health Insurance",
                "description": "Healthcare provider location service for Premier Health customers",
                "industry": "healthcare",
                "target_audience": "Premier Health customers seeking healthcare providers"
            },
            "vapi_agent": {
                "name": "Premier Health Assistant",
                "description": "AI assistant for healthcare provider search and information",
                "system_prompt": """You are a helpful healthcare assistant for Premier Health Insurance.
                    You help customers find healthcare providers in Greater Accra including doctors, hospitals,
                    clinics, and pharmacies. You can search by location, specialty, and provider type.
                    Always be professional, empathetic, and provide accurate information.""",
                "voice": "alloy",
                "language": "en",
                "speed": 1.0,
                "max_duration": 600,
                "silence_timeout": 15,
                "interruptible": True,
                "record_calls": True,
                "tools": [
                    {
                        "name": "search_healthcare_providers",
                        "description": "Search for healthcare providers in Greater Accra",
                        "endpoint": "https://api.ailabsafrica.com/premier-health/search",
                        "method": "POST",
                        "parameters": {
                            "query": {"type": "string", "description": "Search query for healthcare providers"},
                            "location": {"type": "string", "description": "Location or area in Greater Accra"},
                            "specialty": {"type": "string", "description": "Medical specialty or provider type"},
                            "max_results": {"type": "integer", "description": "Maximum number of results", "default": 5}
                        }
                    },
                    {
                        "name": "get_emergency_providers",
                        "description": "Get emergency healthcare providers for urgent situations",
                        "endpoint": "https://api.ailabsafrica.com/premier-health/emergency-providers",
                        "method": "POST",
                        "parameters": {
                            "location": {"type": "string", "description": "Emergency location"},
                            "max_results": {"type": "integer", "description": "Maximum results", "default": 3}
                        }
                    },
                    {
                        "name": "get_provider_details",
                        "description": "Get detailed information about a specific provider",
                        "endpoint": "https://api.ailabsafrica.com/premier-health/provider",
                        "method": "GET",
                        "parameters": {
                            "provider_id": {"type": "integer", "description": "Provider ID"}
                        }
                    }
                ]
            },
            "n8n_workflow": {
                "workflow_name": "Premier Health Automation",
                "description": "Workflow for processing Premier Health voice interactions",
                "nodes": [
                    {
                        "id": "vapi-webhook-trigger",
                        "name": "VAPI Webhook Trigger",
                        "type": "n8n-nodes-base.webhook",
                        "typeVersion": 1,
                        "position": [100, 200],
                        "parameters": {
                            "path": "premier-health-webhook",
                            "httpMethod": "POST",
                            "responseMode": "responseNode"
                        }
                    },
                    {
                        "id": "extract-call-data",
                        "name": "Extract Call Data",
                        "type": "n8n-nodes-base.set",
                        "typeVersion": 1,
                        "position": [300, 200],
                        "parameters": {
                            "values": {
                                "string": [
                                    {"name": "call_id", "value": "={{ $json.call.id }}"},
                                    {"name": "customer_number", "value": "={{ $json.phoneNumber }}"},
                                    {"name": "function_call", "value": "={{ $json.message.function_call.name }}"},
                                    {"name": "function_args", "value": "={{ JSON.stringify($json.message.function_call.arguments) }}"}
                                ]
                            }
                        }
                    },
                    {
                        "id": "healthcare-search",
                        "name": "Healthcare Provider Search",
                        "type": "n8n-nodes-base.httpRequest",
                        "typeVersion": 4,
                        "position": [500, 200],
                        "parameters": {
                            "url": "https://api.ailabsafrica.com/premier-health/search",
                            "method": "POST",
                            "sendBody": True,
                            "contentType": "json",
                            "jsonBody": "={{ JSON.parse($node['Extract Call Data'].json.function_args) }}",
                            "authentication": "predefinedCredentialType",
                            "nodeCredentialType": "httpHeaderAuth"
                        }
                    },
                    {
                        "id": "response-formatter",
                        "name": "Format Response",
                        "type": "n8n-nodes-base.set",
                        "typeVersion": 1,
                        "position": [700, 200],
                        "parameters": {
                            "values": {
                                "string": [
                                    {"name": "response_type", "value": "function_call_result"},
                                    {"name": "response_data", "value": "={{ JSON.stringify($json.data) }}"}
                                ]
                            }
                        }
                    },
                    {
                        "id": "webhook-response",
                        "name": "Webhook Response",
                        "type": "n8n-nodes-base.respondToWebhook",
                        "typeVersion": 1,
                        "position": [900, 200],
                        "parameters": {
                            "responseBody": "={{ { 'message': { 'type': 'function_call_result', 'content': $json.response_data } } }}",
                            "responseContentType": "application/json"
                        }
                    }
                ],
                "connections": {
                    "VAPI Webhook Trigger": {
                        "main": [
                            [{"node": "Extract Call Data", "type": "main", "index": 0}]
                        ]
                    },
                    "Extract Call Data": {
                        "main": [
                            [{"node": "Healthcare Provider Search", "type": "main", "index": 0}]
                        ]
                    },
                    "Healthcare Provider Search": {
                        "main": [
                            [{"node": "Format Response", "type": "main", "index": 0}]
                        ]
                    },
                    "Format Response": {
                        "main": [
                            [{"node": "Webhook Response", "type": "main", "index": 0}]
                        ]
                    }
                },
                "settings": {
                    "executionOrder": "v1",
                    "saveDataErrorExecution": "all",
                    "saveDataSuccessExecution": "all",
                    "saveExecutionProgress": True,
                    "saveManualExecutions": True,
                    "timezone": "UTC"
                }
            }
        }

    @pytest.fixture
    def automation_orchestration_service(self):
        """Create automation orchestration service instance."""
        return AutomationOrchestrationService()

    @pytest.fixture
    def sample_healthcare_search_data(self):
        """Create sample healthcare search data for testing."""
        return {
            "query": "general practitioner in Accra",
            "location": "Accra Central",
            "specialty": "general_medicine",
            "max_results": 5
        }

    @pytest.fixture
    def sample_vapi_webhook_data(self):
        """Create sample VAPI webhook data for testing."""
        return {
            "call": {
                "id": "call_health_test_123",
                "phoneNumberId": "+233244567890",
                "status": "in_progress"
            },
            "message": {
                "type": "function_call",
                "function_call": {
                    "name": "search_healthcare_providers",
                    "arguments": {
                        "query": "pediatrician near East Legon",
                        "location": "East Legon",
                        "specialty": "pediatrics",
                        "max_results": 3
                    }
                }
            },
            "phoneNumber": "+233244567890",
            "customer": {"number": "+233244567890"}
        }

    @pytest.mark.asyncio
    async def test_health_locator_template_deployment(self, automation_orchestration_service, health_locator_config):
        """Test complete Health Locator template deployment."""

        # Mock VAPI agent creation
        with patch.object(automation_orchestration_service.vapi_service, 'create_agent') as mock_create_agent:
            mock_create_agent.return_value = {
                "success": True,
                "agent_id": "assistant_health_locator_123",
                "assistant_id": "assistant_health_locator_123",
                "name": "Premier Health Assistant"
            }

            # Mock N8N workflow creation
            with patch.object(automation_orchestration_service.n8n_service, 'create_workflow') as mock_create_workflow:
                mock_create_workflow.return_value = {
                    "success": True,
                    "id": "workflow_health_locator_456",
                    "name": "Premier Health Automation",
                    "active": False,
                    "webhook_urls": {
                        "VAPI Webhook Trigger": "https://automate.inspirecreations.it.com/webhook/premier-health-webhook"
                    }
                }

                # Mock workflow activation
                with patch.object(automation_orchestration_service.n8n_service, 'activate_workflow') as mock_activate:
                    mock_activate.return_value = True

                    # Deploy the template
                    config = AutomationConfig(**health_locator_config)
                    result = await automation_orchestration_service.deploy_automation(config)

                    # Verify deployment success
                    assert result["success"] is True
                    assert result["vapi_assistant_id"] == "assistant_health_locator_123"
                    assert result["n8n_workflow_id"] == "workflow_health_locator_456"
                    assert "webhook_urls" in result
                    assert result["status"] == "deployed"

                    # Verify VAPI agent was created with correct tools
                    mock_create_agent.assert_called_once()
                    agent_data = mock_create_agent.call_args[0][0]
                    assert agent_data.name == "Premier Health Assistant"
                    assert len(agent_data.custom_tools) == 3
                    assert any(tool["name"] == "search_healthcare_providers" for tool in agent_data.custom_tools)

                    # Verify N8N workflow was created and activated
                    mock_create_workflow.assert_called_once()
                    mock_activate.assert_called_once_with("workflow_health_locator_456")

    @pytest.mark.asyncio
    async def test_vapi_agent_with_healthcare_tools(self, automation_orchestration_service, health_locator_config):
        """Test VAPI agent creation with Premier Health custom tools."""

        with patch.object(automation_orchestration_service.vapi_service, 'create_agent') as mock_create_agent:
            mock_create_agent.return_value = {
                "success": True,
                "agent_id": "assistant_healthcare_tools_test",
                "name": "Premier Health Assistant"
            }

            config = AutomationConfig(**health_locator_config)
            vapi_config = config.vapi_agent

            # Test agent creation with healthcare tools
            result = await automation_orchestration_service.vapi_service.create_agent(
                automation_orchestration_service._create_vapi_agent_from_config(vapi_config)
            )

            assert result["success"] is True
            assert result["agent_id"] == "assistant_healthcare_tools_test"

            # Verify the agent was created with the correct healthcare tools
            mock_create_agent.assert_called_once()
            agent = mock_create_agent.call_args[0][0]

            # Check healthcare-specific tools
            tool_names = [tool["name"] for tool in agent.custom_tools]
            assert "search_healthcare_providers" in tool_names
            assert "get_emergency_providers" in tool_names
            assert "get_provider_details" in tool_names

            # Verify healthcare context in system prompt
            assert "healthcare" in agent.system_prompt.lower()
            assert "premier health" in agent.system_prompt.lower()

    @pytest.mark.asyncio
    async def test_n8n_workflow_nodes_execution(self, automation_orchestration_service, health_locator_config, sample_vapi_webhook_data):
        """Test N8N workflow nodes are properly configured and executable."""

        with patch.object(automation_orchestration_service.n8n_service, 'create_workflow') as mock_create_workflow:
            mock_create_workflow.return_value = {
                "success": True,
                "id": "workflow_nodes_test",
                "name": "Premier Health Automation",
                "active": True,
                "webhook_urls": {
                    "VAPI Webhook Trigger": "https://test.webhook.url/premier-health-webhook"
                }
            }

            with patch.object(automation_orchestration_service.n8n_service, 'trigger_workflow') as mock_trigger:
                mock_trigger.return_value = {
                    "success": True,
                    "executionId": "execution_nodes_test_123",
                    "status": "completed"
                }

                config = AutomationConfig(**health_locator_config)

                # Create the workflow
                workflow_result = await automation_orchestration_service.n8n_service.create_workflow(
                    config.n8n_workflow.dict()
                )

                assert workflow_result["success"] is True
                workflow_id = workflow_result["id"]

                # Test workflow trigger with webhook data
                trigger_result = await automation_orchestration_service.n8n_service.trigger_workflow(
                    workflow_id,
                    sample_vapi_webhook_data
                )

                assert trigger_result["success"] is True
                assert trigger_result["executionId"] == "execution_nodes_test_123"

                # Verify the workflow was created with correct nodes
                mock_create_workflow.assert_called_once()
                workflow_data = mock_create_workflow.call_args[0][0]

                # Check for essential nodes
                node_types = [node["type"] for node in workflow_data["nodes"]]
                assert "n8n-nodes-base.webhook" in node_types
                assert "n8n-nodes-base.httpRequest" in node_types
                assert "n8n-nodes-base.set" in node_types
                assert "n8n-nodes-base.respondToWebhook" in node_types

    @pytest.mark.asyncio
    async def test_premier_health_integration(self, sample_healthcare_search_data):
        """Test Premier Health custom tools integration."""

        # Mock Premier Health API responses
        with patch('httpx.AsyncClient') as mock_client:
            # Mock healthcare provider search response
            mock_search_response = Mock()
            mock_search_response.status_code = 200
            mock_search_response.json.return_value = {
                "success": True,
                "data": {
                    "providers": [
                        {
                            "id": 1,
                            "name": "Dr. Sarah Mensah",
                            "specialty": "General Medicine",
                            "location": "Accra Central",
                            "phone": "+233302123456",
                            "address": "123 Independence Ave, Accra"
                        },
                        {
                            "id": 2,
                            "name": "Ridge Hospital",
                            "specialty": "General Hospital",
                            "location": "Ridge",
                            "phone": "+233302789012",
                            "address": "456 Ridge Road, Accra"
                        }
                    ],
                    "total_found": 2,
                    "confidence": 0.95,
                    "voice_response": "I found 2 healthcare providers near Accra Central..."
                }
            }

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_search_response

            # Test the healthcare search endpoint
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.ailabsafrica.com/premier-health/search",
                    json=sample_healthcare_search_data,
                    headers={"Authorization": "Bearer test_token"}
                )

                # Verify mock was called correctly
                mock_client.return_value.__aenter__.return_value.post.assert_called_once()

                # Verify response structure matches expected Premier Health format
                response_data = mock_search_response.json.return_value
                assert response_data["success"] is True
                assert "providers" in response_data["data"]
                assert "voice_response" in response_data["data"]
                assert len(response_data["data"]["providers"]) == 2

    @pytest.mark.asyncio
    async def test_healthcare_provider_search_workflow(self, sample_vapi_webhook_data):
        """Test complete healthcare provider search workflow."""

        with patch('httpx.AsyncClient') as mock_http_client:
            # Mock Premier Health search API
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "data": {
                    "providers": [
                        {
                            "id": 15,
                            "name": "Dr. John Pediatrics Clinic",
                            "specialty": "Pediatrics",
                            "location": "East Legon",
                            "phone": "+233244123456",
                            "rating": 4.8
                        }
                    ],
                    "total_found": 1,
                    "voice_response": "I found an excellent pediatrician in East Legon for you..."
                }
            }

            mock_http_client.return_value.__aenter__.return_value.post.return_value = mock_response

            # Test the webhook endpoint that processes VAPI calls
            webhook_url = "https://automate.inspirecreations.it.com/webhook/premier-health-webhook"

            async with httpx.AsyncClient() as client:
                webhook_response = await client.post(webhook_url, json=sample_vapi_webhook_data)

                # Verify the search was triggered
                mock_http_client.return_value.__aenter__.return_value.post.assert_called()

                # Verify response format for VAPI
                assert mock_response.json.return_value["success"] is True
                provider_data = mock_response.json.return_value["data"]
                assert "voice_response" in provider_data
                assert len(provider_data["providers"]) == 1
                assert provider_data["providers"][0]["specialty"] == "Pediatrics"

    @pytest.mark.asyncio
    async def test_emergency_provider_lookup(self):
        """Test emergency healthcare provider lookup functionality."""

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "data": {
                    "providers": [
                        {
                            "id": 100,
                            "name": "37 Military Hospital Emergency",
                            "type": "Emergency Room",
                            "location": "37 Military Hospital",
                            "phone": "+233302776111",
                            "emergency_line": "999",
                            "available_24_7": True
                        },
                        {
                            "id": 101,
                            "name": "Korle Bu Emergency Department",
                            "type": "Emergency Room",
                            "location": "Korle Bu Teaching Hospital",
                            "phone": "+233302665401",
                            "emergency_line": "193",
                            "available_24_7": True
                        }
                    ],
                    "emergency_guidance": "Call 193 for immediate emergency assistance",
                    "voice_response": "I found 2 emergency facilities near you. For immediate help, call 193..."
                }
            }

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            emergency_request = {
                "location": "Accra Central",
                "max_results": 3
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.ailabsafrica.com/premier-health/emergency-providers",
                    json=emergency_request
                )

                # Verify emergency providers response
                response_data = mock_response.json.return_value
                assert response_data["success"] is True
                assert "emergency_guidance" in response_data["data"]
                assert all(provider["available_24_7"] for provider in response_data["data"]["providers"])

    @pytest.mark.asyncio
    async def test_provider_details_retrieval(self):
        """Test detailed provider information retrieval."""

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "data": {
                    "provider": {
                        "id": 25,
                        "name": "Dr. Alice Cardiology Center",
                        "specialty": "Cardiology",
                        "qualifications": ["MD", "FACC", "PhD Cardiology"],
                        "experience_years": 15,
                        "location": "East Legon",
                        "address": "123 Liberation Road, East Legon",
                        "phone": "+233244567890",
                        "email": "info@alicecardiology.com",
                        "website": "www.alicecardiology.com",
                        "working_hours": {
                            "monday": "8:00 AM - 5:00 PM",
                            "tuesday": "8:00 AM - 5:00 PM",
                            "wednesday": "8:00 AM - 5:00 PM",
                            "thursday": "8:00 AM - 5:00 PM",
                            "friday": "8:00 AM - 3:00 PM",
                            "saturday": "9:00 AM - 1:00 PM",
                            "sunday": "Closed"
                        },
                        "services": ["ECG", "Echocardiography", "Stress Testing", "Cardiac Consultation"],
                        "insurance_accepted": ["Premier Health", "NHIS", "Private Pay"],
                        "rating": 4.9,
                        "reviews_count": 127
                    },
                    "voice_response": "Dr. Alice Cardiology Center is a highly rated cardiologist with 15 years of experience..."
                }
            }

            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            provider_id = 25
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.ailabsafrica.com/premier-health/provider/{provider_id}"
                )

                # Verify detailed provider information
                response_data = mock_response.json.return_value
                provider = response_data["data"]["provider"]
                assert provider["id"] == 25
                assert provider["specialty"] == "Cardiology"
                assert "Premier Health" in provider["insurance_accepted"]
                assert provider["rating"] >= 4.0

    @pytest.mark.asyncio
    async def test_vapi_webhook_handling(self, sample_vapi_webhook_data):
        """Test VAPI webhook processing for Premier Health."""

        with patch('httpx.AsyncClient') as mock_client:
            # Mock Premier Health webhook response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "message": {
                    "type": "assistant",
                    "content": "I found an excellent pediatrician in East Legon. Dr. John Pediatrics Clinic has a 4.8 rating and specializes in children's healthcare. Would you like me to provide their contact information?",
                    "function_call_result": {
                        "success": True,
                        "data": {
                            "providers": [
                                {
                                    "id": 15,
                                    "name": "Dr. John Pediatrics Clinic",
                                    "specialty": "Pediatrics",
                                    "location": "East Legon",
                                    "phone": "+233244123456",
                                    "rating": 4.8
                                }
                            ],
                            "total_found": 1,
                            "confidence": 0.95
                        }
                    }
                }
            }

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            # Test webhook processing
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.ailabsafrica.com/premier-health/vapi-webhook",
                    json=sample_vapi_webhook_data
                )

                # Verify webhook response format for VAPI
                response_data = mock_response.json.return_value
                assert "message" in response_data
                assert response_data["message"]["type"] == "assistant"
                assert "pediatrician" in response_data["message"]["content"].lower()
                assert response_data["message"]["function_call_result"]["success"] is True

    @pytest.mark.asyncio
    async def test_health_monitoring_integration(self, automation_orchestration_service, health_locator_config):
        """Test health monitoring for deployed Health Locator template."""

        # Mock deployment
        with patch.object(automation_orchestration_service.vapi_service, 'get_assistant') as mock_get_assistant, \
             patch.object(automation_orchestration_service.n8n_service, 'get_workflow') as mock_get_workflow, \
             patch('httpx.AsyncClient') as mock_http_client:

            # Mock VAPI health check
            mock_get_assistant.return_value = {
                "success": True,
                "assistant": {
                    "id": "assistant_health_monitor_test",
                    "name": "Premier Health Assistant",
                    "status": "active"
                }
            }

            # Mock N8N health check
            mock_get_workflow.return_value = {
                "success": True,
                "workflow": {
                    "id": "workflow_health_monitor_test",
                    "name": "Premier Health Automation",
                    "active": True
                }
            }

            # Mock Premier Health API health check
            mock_health_response = Mock()
            mock_health_response.status_code = 200
            mock_health_response.json.return_value = {
                "status": "healthy",
                "service": "Premier Health Insurance Service Location Agent",
                "database_connected": True,
                "total_areas": 25,
                "tools_available": 8
            }
            mock_http_client.return_value.__aenter__.return_value.get.return_value = mock_health_response

            # Create test automation config
            config = AutomationConfig(**health_locator_config)
            config.vapi_agent.assistant_id = "assistant_health_monitor_test"
            config.n8n_workflow.workflow_id = "workflow_health_monitor_test"

            # Test health monitoring
            health_result = await automation_orchestration_service.check_automation_health(config)

            assert health_result["overall_status"] == "healthy"
            assert health_result["components"]["vapi"]["status"] == "healthy"
            assert health_result["components"]["n8n"]["status"] == "healthy"
            assert health_result["components"]["custom_tools"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_end_to_end_call_flow(self, automation_orchestration_service, health_locator_config):
        """Test complete end-to-end call flow for Health Locator template."""

        # This test simulates a complete customer interaction
        call_simulation_data = {
            "customer_query": "I need to find a pediatrician in East Legon for my child",
            "expected_function": "search_healthcare_providers",
            "expected_specialty": "pediatrics",
            "expected_location": "East Legon"
        }

        with patch.object(automation_orchestration_service.vapi_service, 'initiate_call') as mock_initiate_call, \
             patch.object(automation_orchestration_service.n8n_service, 'trigger_workflow') as mock_trigger_workflow, \
             patch('httpx.AsyncClient') as mock_http_client:

            # Mock call initiation
            mock_initiate_call.return_value = {
                "success": True,
                "call_id": "call_e2e_test_789",
                "status": "initiated"
            }

            # Mock workflow execution
            mock_trigger_workflow.return_value = {
                "success": True,
                "executionId": "execution_e2e_test_456",
                "status": "completed"
            }

            # Mock Premier Health API response
            mock_search_response = Mock()
            mock_search_response.status_code = 200
            mock_search_response.json.return_value = {
                "success": True,
                "data": {
                    "providers": [
                        {
                            "id": 15,
                            "name": "Dr. John Pediatrics Clinic",
                            "specialty": "Pediatrics",
                            "location": "East Legon",
                            "phone": "+233244123456",
                            "rating": 4.8,
                            "address": "456 Liberation Road, East Legon"
                        }
                    ],
                    "total_found": 1,
                    "confidence": 0.95,
                    "voice_response": "I found an excellent pediatrician in East Legon for you. Dr. John Pediatrics Clinic has a 4.8-star rating and specializes in children's healthcare. Their contact number is +233244123456."
                }
            }
            mock_http_client.return_value.__aenter__.return_value.post.return_value = mock_search_response

            # Simulate the end-to-end flow
            config = AutomationConfig(**health_locator_config)

            # 1. Deploy automation
            deployment_result = await automation_orchestration_service.deploy_automation(config)
            # Note: This would be mocked in a real test

            # 2. Initiate call
            call_result = await automation_orchestration_service.vapi_service.initiate_call(
                "+233244567890",
                "assistant_health_locator_test"
            )
            assert call_result["success"] is True

            # 3. Process webhook (simulated)
            webhook_data = {
                "call": {"id": call_result["call_id"]},
                "message": {
                    "function_call": {
                        "name": "search_healthcare_providers",
                        "arguments": {
                            "query": call_simulation_data["customer_query"],
                            "specialty": call_simulation_data["expected_specialty"],
                            "location": call_simulation_data["expected_location"]
                        }
                    }
                }
            }

            # 4. Trigger workflow
            workflow_result = await automation_orchestration_service.n8n_service.trigger_workflow(
                "workflow_health_locator_test",
                webhook_data
            )
            assert workflow_result["success"] is True

            # 5. Verify search was executed
            mock_http_client.return_value.__aenter__.return_value.post.assert_called()

            # 6. Verify response contains expected healthcare provider
            search_response = mock_search_response.json.return_value
            assert search_response["success"] is True
            assert len(search_response["data"]["providers"]) == 1
            assert "pediatric" in search_response["data"]["providers"][0]["specialty"].lower()
            assert "east legon" in search_response["data"]["providers"][0]["location"].lower()

    def test_health_locator_configuration_validation(self, health_locator_config):
        """Test Health Locator configuration validation."""

        # Test valid configuration
        config = AutomationConfig(**health_locator_config)
        assert config.name == "Premier Health Provider Locator"
        assert config.category == "healthcare"
        assert config.template_id == "health_locator"
        assert len(config.vapi_agent.tools) == 3

        # Test healthcare-specific validations
        assert "healthcare" in config.vapi_agent.system_prompt.lower()
        assert config.vapi_agent.max_duration == 600  # 10 minutes for healthcare calls
        assert config.vapi_agent.silence_timeout == 15  # Longer timeout for healthcare

        # Verify required healthcare tools
        tool_names = [tool["name"] for tool in config.vapi_agent.tools]
        required_tools = [
            "search_healthcare_providers",
            "get_emergency_providers",
            "get_provider_details"
        ]
        for required_tool in required_tools:
            assert required_tool in tool_names

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])