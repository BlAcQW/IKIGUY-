"""Campaign management routes."""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional
from uuid import UUID
import httpx
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, Any
import logging

from ..models import Campaign, CampaignCreate
from ..services.campaign_service import create_campaign, get_campaign, list_campaigns, update_campaign, delete_campaign
from ..services.n8n_service import N8NService
from ..services.integration_service import integration_service
from ..auth import get_current_user_mongo
from ..middleware.organization_context import (
    get_organization_context,
    validate_organization_access
)
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

# Initialize n8n service
n8n_service = N8NService()


class CampaignUpdate(BaseModel):
    """Request model for updating a campaign."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    url: Optional[str] = None


class CampaignStats(BaseModel):
    """Campaign statistics model."""
    calls_made: int = 0
    connect_rate: float = 0.0
    conversion_rate: float = 0.0
    progress: float = 0.0
    

class CampaignStartRequest(BaseModel):
    """Request model for starting a campaign."""
    url: str


class CampaignStartResponse(BaseModel):
    """Response model for starting a campaign."""
    success: bool
    message: str
    campaign_id: str
    status: str


@router.post("/", response_model=Campaign)
async def create_new_campaign(
    request: Request,
    payload: CampaignCreate,
    current_user = Depends(get_current_user_mongo)
):
    """
    Create a new campaign with optional n8n workflow integration.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # Set organization_id from context (preferred) or fallback to tenant_id for backward compatibility
        if not hasattr(payload, 'organization_id') or not payload.organization_id:
            # Use org_id from context, or fallback to deprecated tenant_id
            if org_id:
                payload.organization_id = org_id
            elif hasattr(payload, 'tenant_id') and payload.tenant_id:
                payload.organization_id = payload.tenant_id
            else:
                # Last resort: check user's tenant_id
                user_org_id = current_user.get("organization_id") or current_user.get("tenant_id")
                if user_org_id:
                    payload.organization_id = user_org_id
                else:
                    raise HTTPException(status_code=400, detail="Organization ID required")

        logger.info(f"Creating campaign for organization: {payload.organization_id}")

        # Create the campaign first
        campaign = create_campaign(payload)

        # Handle n8n workflow creation if template_id is provided
        if payload.n8n_template_id and n8n_service:
            try:
                # Create workflow from template
                workflow_id = await n8n_service.create_workflow_from_template(
                    payload.n8n_template_id,
                    campaign
                )

                if workflow_id:
                    # Update campaign with workflow information
                    campaign.n8n_workflow_id = workflow_id
                    campaign.n8n_template_id = payload.n8n_template_id

                    # Get workflow details and webhooks
                    workflow_status = await n8n_service.get_workflow_status(workflow_id)
                    if workflow_status:
                        campaign.n8n_config = {
                            "workflow_id": workflow_id,
                            "template_id": payload.n8n_template_id,
                            "webhooks": workflow_status.get("webhooks", []),
                            "active": workflow_status.get("active", False),
                            "created_at": datetime.utcnow().isoformat()
                        }

                    # Update campaign in database
                    update_campaign(campaign.id, {
                        "n8n_workflow_id": workflow_id,
                        "n8n_template_id": payload.n8n_template_id,
                        "n8n_config": campaign.n8n_config
                    })

                    print(f"Created n8n workflow {workflow_id} for campaign {campaign.id}")
                else:
                    print(f"Failed to create n8n workflow for campaign {campaign.id}")

            except Exception as workflow_error:
                print(f"Warning: n8n workflow creation failed: {workflow_error}")
                # Campaign creation continues even if workflow fails

        return campaign

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create campaign: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to create campaign: {str(e)}")


@router.get("/", response_model=List[Campaign])
async def get_campaigns(
    request: Request,
    current_user = Depends(get_current_user_mongo)
):
    """
    Get all campaigns for the current organization.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # Use organization_id, fallback to tenant_id for backward compatibility
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if not organization_id:
            raise HTTPException(status_code=400, detail="Organization ID not found")

        logger.info(f"Getting campaigns for organization: {organization_id}")

        campaigns = list_campaigns(UUID(organization_id))
        return campaigns

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve campaigns: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to retrieve campaigns: {str(e)}")


@router.get("/{campaign_id}", response_model=Campaign)
async def get_campaign_by_id(
    request: Request,
    campaign_id: str,
    current_user = Depends(get_current_user_mongo)
):
    """
    Get a specific campaign by ID.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Getting campaign {campaign_id} for organization: {org_id}")

        campaign = get_campaign(UUID(campaign_id))
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Verify campaign belongs to current organization
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        campaign_org_id = getattr(campaign, 'organization_id', None) or getattr(campaign, 'tenant_id', None)

        if str(campaign_org_id) != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        return campaign

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid campaign ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve campaign: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to retrieve campaign: {str(e)}")


@router.post("/{campaign_id}/start", response_model=CampaignStartResponse)
async def start_campaign(
    http_request: Request,
    campaign_id: str,
    request: CampaignStartRequest,
    current_user = Depends(get_current_user_mongo)
):
    """
    Start a campaign by sending a POST request to the provided URL.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(http_request)
        if org_id:
            await validate_organization_access(http_request, current_user, org_id)

        logger.info(f"Starting campaign {campaign_id} for organization: {org_id}")

        # Get campaign and verify ownership
        campaign = get_campaign(UUID(campaign_id))
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Verify campaign belongs to current organization
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        campaign_org_id = getattr(campaign, 'organization_id', None) or getattr(campaign, 'tenant_id', None)

        if str(campaign_org_id) != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Send POST request to the provided URL to start the campaign
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    request.url,
                    json={
                        "campaign_id": campaign_id,
                        "campaign_name": campaign.name,
                        "organization_id": organization_id,  # Updated from tenant_id
                        "tenant_id": organization_id,  # Keep for backward compatibility
                        "started_at": datetime.utcnow().isoformat()
                    }
                )
                
                if response.status_code == 200:
                    # Update campaign status to active
                    update_campaign(UUID(campaign_id), {"status": "active"})
                    return CampaignStartResponse(
                        success=True,
                        message="Campaign started successfully",
                        campaign_id=campaign_id,
                        status="active"
                    )
                else:
                    return CampaignStartResponse(
                        success=False,
                        message=f"Failed to start campaign: HTTP {response.status_code}",
                        campaign_id=campaign_id,
                        status="failed"
                    )
                    
            except httpx.TimeoutException:
                return CampaignStartResponse(
                    success=False,
                    message="Campaign start request timed out",
                    campaign_id=campaign_id,
                    status="timeout"
                )
            except Exception as e:
                return CampaignStartResponse(
                    success=False,
                    message=f"Failed to start campaign: {str(e)}",
                    campaign_id=campaign_id,
                    status="error"
                )
                
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid campaign ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start campaign: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to start campaign: {str(e)}")


@router.get("/{campaign_id}/stats", response_model=CampaignStats)
async def get_campaign_stats(
    request: Request,
    campaign_id: str,
    current_user = Depends(get_current_user_mongo)
):
    """
    Get campaign statistics and progress.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Getting stats for campaign {campaign_id}, organization: {org_id}")

        # Get campaign and verify ownership
        campaign = get_campaign(UUID(campaign_id))
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Verify campaign belongs to current organization
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        campaign_org_id = getattr(campaign, 'organization_id', None) or getattr(campaign, 'tenant_id', None)

        if str(campaign_org_id) != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # For now, return mock data. In production, this would integrate with
        # your analytics/monitoring system to get real campaign metrics
        stats = CampaignStats(
            calls_made=1240,
            connect_rate=65.3,
            conversion_rate=24.1,
            progress=75.0
        )

        return stats

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid campaign ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve campaign stats: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to retrieve campaign stats: {str(e)}")


@router.post("/{campaign_id}/pause")
async def pause_campaign(
    request: Request,
    campaign_id: str,
    current_user = Depends(get_current_user_mongo)
):
    """
    Pause a running campaign.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Pausing campaign {campaign_id} for organization: {org_id}")

        # Get campaign and verify ownership
        campaign = get_campaign(UUID(campaign_id))
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Verify campaign belongs to current organization
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        campaign_org_id = getattr(campaign, 'organization_id', None) or getattr(campaign, 'tenant_id', None)

        if str(campaign_org_id) != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Update campaign status to paused
        update_campaign(UUID(campaign_id), {"status": "paused"})

        # In production, this would integrate with your campaign management system
        # to actually pause the running automation/n8n workflow

        return {"success": True, "message": "Campaign paused successfully"}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid campaign ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause campaign: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to pause campaign: {str(e)}")


@router.delete("/{campaign_id}")
async def delete_campaign_endpoint(
    request: Request,
    campaign_id: str,
    current_user = Depends(get_current_user_mongo)
):
    """
    Delete a campaign.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Deleting campaign {campaign_id} for organization: {org_id}")

        # Get campaign and verify ownership
        campaign = get_campaign(UUID(campaign_id))
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Verify campaign belongs to current organization
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        campaign_org_id = getattr(campaign, 'organization_id', None) or getattr(campaign, 'tenant_id', None)

        if str(campaign_org_id) != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Delete the campaign
        success = delete_campaign(UUID(campaign_id))
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete campaign")

        return {"success": True, "message": "Campaign deleted successfully"}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid campaign ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete campaign: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to delete campaign: {str(e)}")


class IntegrationTestRequest(BaseModel):
    """Request model for testing integrations."""
    integration_type: str = Field(..., description="Type of integration (crm, email, sms, etc.)")
    config: Dict[str, Any] = Field(..., description="Integration configuration")


class IntegrationTestResponse(BaseModel):
    """Response model for integration tests."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


@router.post("/integrations/test", response_model=IntegrationTestResponse)
async def test_campaign_integration(
    http_request: Request,
    request: IntegrationTestRequest,
    current_user = Depends(get_current_user_mongo)
):
    """
    Test a campaign integration configuration.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(http_request)
        if org_id:
            await validate_organization_access(http_request, current_user, org_id)

        # Use organization_id, fallback to tenant_id for backward compatibility
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if not organization_id:
            raise HTTPException(status_code=400, detail="Organization ID not found")

        logger.info(f"Testing integration {request.integration_type} for organization: {organization_id}")

        # Test the specific integration using our consolidated integration service
        test_result = await integration_service.test_integration(
            integration_name=request.integration_type,
            config=request.config,
            organization_id=organization_id  # Updated from tenant_id
        )

        return IntegrationTestResponse(
            success=test_result.get("success", False),
            message=test_result.get("message", "Integration test completed"),
            details=test_result.get("details", {})
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Integration test failed: {str(e)}")
        return IntegrationTestResponse(
            success=False,
            message=f"Integration test failed: {str(e)}",
            details={"error": str(e)}
        )


class CampaignTemplateResponse(BaseModel):
    """Response model for campaign templates."""
    templates: List[Dict[str, Any]]


@router.get("/templates", response_model=CampaignTemplateResponse)
async def get_campaign_templates():
    """Get available campaign templates."""
    # These would typically be stored in a database or configuration file
    templates = [
        {
            "id": "sales_cold_outreach",
            "name": "Sales Cold Outreach",
            "description": "Reach out to potential customers with personalized sales pitches",
            "category": "sales",
            "difficulty": "intermediate",
            "estimated_setup_time": "15-20 minutes",
            "features": ["Lead qualification", "Appointment booking", "CRM integration", "Follow-up scheduling"],
            "default_integrations": ["pipedrive", "email", "google_workspace", "sms"],
            "sample_data": {
                "expected_responses": 35,
                "conversion_rate": "8-12%",
                "avg_call_duration": "3-5 minutes"
            }
        },
        {
            "id": "customer_survey",
            "name": "Customer Satisfaction Survey",
            "description": "Collect valuable feedback from your customers post-purchase or service",
            "category": "survey",
            "difficulty": "beginner",
            "estimated_setup_time": "10-15 minutes",
            "features": ["Automated survey", "Rating collection", "Feedback analysis", "Report generation"],
            "default_integrations": ["google_drive", "email", "notion", "zapier"],
            "sample_data": {
                "expected_responses": 65,
                "conversion_rate": "45-60%",
                "avg_call_duration": "2-3 minutes"
            }
        },
        {
            "id": "appointment_booking",
            "name": "Appointment Booking",
            "description": "Book appointments for consultations, services, or meetings",
            "category": "sales",
            "difficulty": "beginner",
            "estimated_setup_time": "10-15 minutes",
            "features": ["Calendar integration", "Time zone handling", "Confirmation emails", "Reminder notifications"],
            "default_integrations": ["google_workspace", "email", "sms", "whatsapp"],
            "sample_data": {
                "expected_responses": 40,
                "conversion_rate": "25-35%",
                "avg_call_duration": "2-4 minutes"
            }
        }
    ]
    
    return CampaignTemplateResponse(templates=templates)


@router.post("/{campaign_id}/n8n/activate")
async def activate_campaign_workflow(
    request: Request,
    campaign_id: str,
    current_user = Depends(get_current_user_mongo)
):
    """
    Activate the n8n workflow for a campaign.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Activating n8n workflow for campaign {campaign_id}, organization: {org_id}")

        # Get campaign and verify ownership
        campaign = get_campaign(UUID(campaign_id))
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Verify campaign belongs to current organization
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        campaign_org_id = getattr(campaign, 'organization_id', None) or getattr(campaign, 'tenant_id', None)

        if str(campaign_org_id) != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        if not campaign.n8n_workflow_id:
            raise HTTPException(status_code=400, detail="No n8n workflow associated with this campaign")

        if not n8n_service:
            raise HTTPException(status_code=503, detail="n8n service not available")

        success = await n8n_service.activate_workflow(campaign.n8n_workflow_id)

        if success:
            # Update campaign config
            n8n_config = campaign.n8n_config or {}
            n8n_config["active"] = True
            update_campaign(campaign.id, {"n8n_config": n8n_config})

            return {"success": True, "message": "Workflow activated"}
        else:
            raise HTTPException(status_code=400, detail="Failed to activate workflow")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate workflow: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to activate workflow: {str(e)}")


@router.post("/{campaign_id}/n8n/deactivate")
async def deactivate_campaign_workflow(
    request: Request,
    campaign_id: str,
    current_user = Depends(get_current_user_mongo)
):
    """
    Deactivate the n8n workflow for a campaign.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Deactivating n8n workflow for campaign {campaign_id}, organization: {org_id}")

        # Get campaign and verify ownership
        campaign = get_campaign(UUID(campaign_id))
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Verify campaign belongs to current organization
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        campaign_org_id = getattr(campaign, 'organization_id', None) or getattr(campaign, 'tenant_id', None)

        if str(campaign_org_id) != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        if not campaign.n8n_workflow_id:
            raise HTTPException(status_code=400, detail="No n8n workflow associated with this campaign")

        if not n8n_service:
            raise HTTPException(status_code=503, detail="n8n service not available")

        success = await n8n_service.deactivate_workflow(campaign.n8n_workflow_id)

        if success:
            # Update campaign config
            n8n_config = campaign.n8n_config or {}
            n8n_config["active"] = False
            update_campaign(campaign.id, {"n8n_config": n8n_config})

            return {"success": True, "message": "Workflow deactivated"}
        else:
            raise HTTPException(status_code=400, detail="Failed to deactivate workflow")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate workflow: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to deactivate workflow: {str(e)}")


@router.get("/{campaign_id}/n8n/status")
async def get_campaign_workflow_status(
    request: Request,
    campaign_id: str,
    current_user = Depends(get_current_user_mongo)
):
    """
    Get the n8n workflow status for a campaign.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Getting n8n workflow status for campaign {campaign_id}, organization: {org_id}")

        # Get campaign and verify ownership
        campaign = get_campaign(UUID(campaign_id))
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Verify campaign belongs to current organization
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        campaign_org_id = getattr(campaign, 'organization_id', None) or getattr(campaign, 'tenant_id', None)

        if str(campaign_org_id) != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        if not campaign.n8n_workflow_id:
            return {"has_workflow": False, "message": "No n8n workflow associated"}

        if not n8n_service:
            raise HTTPException(status_code=503, detail="n8n service not available")

        status = await n8n_service.get_workflow_status(campaign.n8n_workflow_id)

        if status:
            return {
                "has_workflow": True,
                "workflow_id": campaign.n8n_workflow_id,
                "template_id": campaign.n8n_template_id,
                "status": status
            }
        else:
            return {"has_workflow": True, "error": "Could not fetch workflow status"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow status: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to get workflow status: {str(e)}")


@router.post("/{campaign_id}/n8n/trigger")
async def trigger_campaign_workflow(
    request: Request,
    campaign_id: str,
    data: Dict[str, Any] = {},
    current_user = Depends(get_current_user_mongo)
):
    """
    Trigger the n8n workflow for a campaign.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Triggering n8n workflow for campaign {campaign_id}, organization: {org_id}")

        # Get campaign and verify ownership
        campaign = get_campaign(UUID(campaign_id))
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Verify campaign belongs to current organization
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        campaign_org_id = getattr(campaign, 'organization_id', None) or getattr(campaign, 'tenant_id', None)

        if str(campaign_org_id) != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        if not campaign.n8n_workflow_id:
            raise HTTPException(status_code=400, detail="No n8n workflow associated with this campaign")

        if not n8n_service:
            raise HTTPException(status_code=503, detail="n8n service not available")

        # Add campaign context to trigger data
        trigger_data = {
            "campaign": {
                "id": str(campaign.id),
                "name": campaign.name,
                "category": campaign.category
            },
            **data
        }

        result = await n8n_service.trigger_workflow(campaign.n8n_workflow_id, trigger_data)

        if result:
            return {"success": True, "execution": result}
        else:
            raise HTTPException(status_code=400, detail="Failed to trigger workflow")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger workflow: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to trigger workflow: {str(e)}")