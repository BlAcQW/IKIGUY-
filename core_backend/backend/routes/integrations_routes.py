"""
API routes for managing integrations and API keys
"""

import os
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services.integration_service import integration_service
from ..services.hubspot_consolidated_service import hubspot_consolidated_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["integrations"])


class IntegrationConfig(BaseModel):
    """Model for integration configuration."""
    provider: str
    api_key: str
    test: bool = False


class IntegrationTestRequest(BaseModel):
    """Model for integration test request."""
    integration_type: str
    config: Dict[str, Any]
    tenant_id: str = "default"


class IntegrationTestResult(BaseModel):
    """Model for integration test result."""
    success: bool
    message: str
    provider: str


class TicketCreationRequest(BaseModel):
    """Model for ticket creation request."""
    subject: str
    content: str
    priority: Optional[str] = "MEDIUM"
    category: Optional[str] = "CUSTOMER_SERVICE"
    source_type: Optional[str] = "API"
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    custom_properties: Optional[Dict[str, Any]] = None


class TicketCreationResult(BaseModel):
    """Model for ticket creation result."""
    success: bool
    message: str
    ticket_id: Optional[str] = None
    provider: str = "hubspot"
    ticket_url: Optional[str] = None


@router.post("/configure")
async def configure_integration(config: IntegrationConfig) -> Dict[str, Any]:
    """
    Configure an integration with API key.
    
    Args:
        config: Integration configuration with provider and API key
        
    Returns:
        Configuration status
    """
    try:
        provider = config.provider.upper()
        
        # Map provider names to environment variables
        env_var_map = {
            "OPENAI": "OPENAI_API_KEY",
            "ANTHROPIC": "ANTHROPIC_API_KEY",
            "GEMINI": "GOOGLE_API_KEY",
            "GHANANLP": "GHANANLP_API_KEY",
            "ABENA_AI": "ABENA_AI_API_KEY",
            "ELEVENLABS": "ELEVENLABS_API_KEY",
            "DEEPGRAM": "DEEPGRAM_API_KEY",
        }
        
        if provider not in env_var_map:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {config.provider}")
        
        # Set environment variable
        env_var = env_var_map[provider]
        os.environ[env_var] = config.api_key
        
        # Optionally test the integration
        if config.test:
            test_result = await test_integration(config.provider)
            return {
                "success": True,
                "provider": config.provider,
                "configured": True,
                "test_result": test_result
            }
        
        return {
            "success": True,
            "provider": config.provider,
            "configured": True
        }
        
    except Exception as e:
        logger.error(f"Failed to configure integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/{provider}")
async def test_integration(provider: str) -> IntegrationTestResult:
    """
    Test an integration connection.
    
    Args:
        provider: Provider name to test
        
    Returns:
        Test result
    """
    try:
        provider_lower = provider.lower()
        
        if provider_lower == "openai":
            from ..services.openai_service import openai_service
            
            # Re-initialize with new key if set
            openai_service._initialize_client()
            
            # Test connection
            try:
                response = await openai_service.chat_completion(
                    messages=[{"role": "user", "content": "Hello"}],
                    model="gpt-3.5-turbo",
                    max_tokens=10
                )
                return IntegrationTestResult(
                    success=True,
                    message="OpenAI connection successful",
                    provider=provider
                )
            except Exception as e:
                return IntegrationTestResult(
                    success=False,
                    message=f"OpenAI connection failed: {str(e)}",
                    provider=provider
                )
                
        elif provider_lower == "anthropic":
            from ..services.anthropic_service import anthropic_service
            
            # Re-initialize with new key if set
            anthropic_service._initialize_client()
            
            # Test connection
            success = await anthropic_service.test_connection()
            return IntegrationTestResult(
                success=success,
                message="Anthropic connection successful" if success else "Anthropic connection failed",
                provider=provider
            )
            
        elif provider_lower == "elevenlabs":
            # Test ElevenLabs connection
            # This would require implementing ElevenLabs service
            return IntegrationTestResult(
                success=False,
                message="ElevenLabs integration not yet implemented",
                provider=provider
            )
            
        elif provider_lower == "gemini":
            # Test Google Gemini connection
            # This would require implementing Gemini service
            return IntegrationTestResult(
                success=False,
                message="Google Gemini integration not yet implemented",
                provider=provider
            )
            
        elif provider_lower == "ghananlp":
            # Test GhanaNLP connection
            return IntegrationTestResult(
                success=False,
                message="GhanaNLP integration not yet implemented",
                provider=provider
            )
            
        elif provider_lower == "abena_ai":
            # Test Abena AI connection
            return IntegrationTestResult(
                success=False,
                message="Abena AI integration not yet implemented",
                provider=provider
            )
            
        else:
            return IntegrationTestResult(
                success=False,
                message=f"Unknown provider: {provider}",
                provider=provider
            )
            
    except Exception as e:
        logger.error(f"Integration test error: {e}")
        return IntegrationTestResult(
            success=False,
            message=f"Test error: {str(e)}",
            provider=provider
        )


@router.get("/status")
async def get_integration_status() -> Dict[str, Any]:
    """
    Get status of all configured integrations.
    
    Returns:
        Status of all integrations
    """
    providers = ["openai", "anthropic", "elevenlabs", "gemini", "ghananlp", "abena_ai", "deepgram"]
    status = {}
    
    for provider in providers:
        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GOOGLE_API_KEY",
            "ghananlp": "GHANANLP_API_KEY",
            "abena_ai": "ABENA_AI_API_KEY",
            "elevenlabs": "ELEVENLABS_API_KEY",
            "deepgram": "DEEPGRAM_API_KEY",
        }
        
        env_var = env_var_map.get(provider)
        if env_var:
            api_key = os.getenv(env_var)
            status[provider] = {
                "configured": bool(api_key),
                "has_key": bool(api_key),
                "key_preview": f"{api_key[:10]}..." if api_key else None
            }
        else:
            status[provider] = {
                "configured": False,
                "has_key": False,
                "key_preview": None
            }
    
    return status


@router.post("/test")
async def test_integration_extended(request: IntegrationTestRequest) -> Dict[str, Any]:
    """
    Test an integration using the extended integration service.
    
    Args:
        request: Integration test request with type, config, and tenant ID
        
    Returns:
        Test result from integration service
    """
    try:
        result = await integration_service.test_integration(
            integration_type=request.integration_type,
            config=request.config,
            tenant_id=request.tenant_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Extended integration test error: {e}")
        raise HTTPException(status_code=500, detail=f"Integration test failed: {str(e)}")


@router.get("/supported_types")
async def get_supported_integration_types() -> Dict[str, Any]:
    """
    Get all supported integration types from the consolidated service.

    Returns:
        Comprehensive list of supported integration types with metadata
    """
    return integration_service.get_supported_integrations()


@router.get("/list")
async def list_integrations(category: Optional[str] = None, has_mcp: Optional[bool] = None) -> Dict[str, Any]:
    """
    List all available integrations with filtering options.

    Args:
        category: Filter by category (optional)
        has_mcp: Filter by MCP availability (optional)

    Returns:
        List of integrations with metadata
    """
    integrations = integration_service.list_integrations(category=category, has_mcp=has_mcp)
    return {
        "integrations": integrations,
        "total": len(integrations),
        "filtered": category is not None or has_mcp is not None
    }


@router.get("/capabilities/{integration_name}")
async def get_integration_capabilities(integration_name: str) -> Dict[str, Any]:
    """
    Get capabilities and available methods for a specific integration.

    Args:
        integration_name: Name of the integration

    Returns:
        Integration capabilities and method information
    """
    return integration_service.get_integration_capabilities(integration_name)


@router.get("/mcp")
async def get_mcp_integrations() -> Dict[str, Any]:
    """
    Get all MCP-enabled integrations.

    Returns:
        MCP integrations with server and endpoint information
    """
    return integration_service.get_mcp_integrations()


@router.post("/execute")
async def execute_integration_action(
    integration_name: str,
    action: str,
    config: Dict[str, Any],
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute an action on a specific integration.

    Args:
        integration_name: Name of the integration
        action: Action method to execute
        config: Integration configuration
        data: Optional data for the action

    Returns:
        Execution result
    """
    try:
        result = await integration_service.execute_integration(
            integration_name=integration_name,
            action=action,
            config=config,
            data=data
        )
        return result
    except Exception as e:
        logger.error(f"Integration execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Integration execution failed: {str(e)}")


# N8N-specific endpoints
@router.get("/n8n/workflows")
async def get_n8n_workflows(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get N8N workflows using either direct integration or MCP.

    Args:
        config: Optional N8N configuration

    Returns:
        N8N workflows or MCP endpoint information
    """
    try:
        result = await integration_service.get_n8n_workflows(config)
        return result
    except Exception as e:
        logger.error(f"N8N workflows error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get N8N workflows: {str(e)}")


@router.post("/n8n/workflow/create")
async def create_n8n_workflow_from_template(
    template_id: int,
    campaign_data: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create N8N workflow from template with campaign customization.

    Args:
        template_id: N8N template ID
        campaign_data: Campaign data for customization
        config: Optional N8N configuration

    Returns:
        Workflow creation result
    """
    try:
        result = await integration_service.create_n8n_workflow_from_template(
            template_id=template_id,
            campaign_data=campaign_data,
            config=config
        )
        return result
    except Exception as e:
        logger.error(f"N8N workflow creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create N8N workflow: {str(e)}")


@router.post("/n8n/workflow/{workflow_id}/trigger")
async def trigger_n8n_workflow(
    workflow_id: str,
    data: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Trigger N8N workflow execution.

    Args:
        workflow_id: N8N workflow ID
        data: Data to pass to the workflow
        config: Optional N8N configuration

    Returns:
        Workflow execution result
    """
    try:
        result = await integration_service.trigger_n8n_workflow(
            workflow_id=workflow_id,
            data=data,
            config=config
        )
        return result
    except Exception as e:
        logger.error(f"N8N workflow trigger error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger N8N workflow: {str(e)}")


@router.get("/n8n/workflow/{workflow_id}/status")
async def get_n8n_workflow_status(
    workflow_id: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get N8N workflow status and execution history.

    Args:
        workflow_id: N8N workflow ID
        config: Optional N8N configuration

    Returns:
        Workflow status information
    """
    try:
        result = await integration_service.get_n8n_workflow_status(
            workflow_id=workflow_id,
            config=config
        )
        return result
    except Exception as e:
        logger.error(f"N8N workflow status error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get N8N workflow status: {str(e)}")


@router.get("/n8n/templates/search")
async def search_n8n_templates(
    query: str,
    category: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search N8N templates using either direct integration or MCP.

    Args:
        query: Search query
        category: Optional category filter
        limit: Maximum number of results

    Returns:
        N8N template search results
    """
    try:
        result = await integration_service.search_n8n_templates(
            query=query,
            category=category,
            limit=limit
        )
        return result
    except Exception as e:
        logger.error(f"N8N template search error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search N8N templates: {str(e)}")


@router.post("/hubspot/tickets", response_model=TicketCreationResult)
async def create_hubspot_ticket(request: TicketCreationRequest) -> TicketCreationResult:
    """
    Create a HubSpot support ticket through the generic integration route.

    Args:
        request: Ticket creation request with subject, content, priority, etc.

    Returns:
        Ticket creation result with success status and ticket ID
    """
    try:
        logger.info(f"Creating HubSpot ticket: {request.subject}")

        # Prepare ticket data for HubSpot service
        ticket_data = {
            "subject": request.subject,
            "content": request.content,
            "priority": request.priority,
            "category": request.category,
            "source_type": request.source_type,
            "custom_properties": request.custom_properties or {}
        }

        # Add customer information to custom properties if provided
        if request.customer_name or request.customer_phone:
            ticket_data["custom_properties"].update({
                "customer_name": request.customer_name,
                "customer_phone": request.customer_phone
            })

        # Create ticket via HubSpot consolidated service
        result = await hubspot_consolidated_service.create_ticket(ticket_data)

        return TicketCreationResult(
            success=result.get("success", False),
            message=result.get("message", ""),
            ticket_id=result.get("ticket_id"),
            provider="hubspot",
            ticket_url=result.get("hubspot_url")
        )

    except Exception as e:
        logger.error(f"HubSpot ticket creation error: {e}")
        return TicketCreationResult(
            success=False,
            message=f"Failed to create HubSpot ticket: {str(e)}",
            provider="hubspot"
        )