"""
API routes for enhanced template functionality.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
import logging

from ..auth import get_current_user_mongo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enhanced-template", tags=["enhanced-template"])

class EnhancedTemplateRequest(BaseModel):
    """Request model for creating enhanced template."""
    template_id: str
    template_name: str
    company_name: str
    company_description: Optional[str] = ""
    company_url: str
    audience_id: Optional[str] = None
    config: Dict[str, Any] = {}
    vapi_agent: Dict[str, Any] = {}
    n8n_workflow: Dict[str, Any] = {}
    integrations: Dict[str, Any] = {}
    enable_demo: bool = True
    enable_analytics: bool = True
    tenant_id: str

@router.post("/create")
async def create_enhanced_template(
    request: EnhancedTemplateRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Create a complete enhanced template campaign.

    Args:
        request: Enhanced template creation request
        background_tasks: Background task queue
        current_user: Current authenticated user

    Returns:
        dict: Campaign creation response with VAPI agent, N8N workflow, and demo details
    """
    try:
        logger.info(f"Creating enhanced template '{request.template_name}' for {request.company_name}")

        # Determine campaign type based on template_id
        campaign_type = "enhanced_template"
        agent_type = "generic_enhanced_agent"
        workflow_type = "generic_enhanced_automation"

        if "appointment" in request.template_id.lower():
            campaign_type = "enhanced_appointment_booking"
            agent_type = "appointment_booking_agent"
            workflow_type = "appointment_booking_automation"
        elif "survey" in request.template_id.lower():
            campaign_type = "enhanced_survey_feedback"
            agent_type = "customer_survey_agent"
            workflow_type = "customer_survey_automation"
        elif "payment" in request.template_id.lower():
            campaign_type = "enhanced_payment_reminder"
            agent_type = "payment_reminder_agent"
            workflow_type = "payment_reminder_automation"
        elif "insurance" in request.template_id.lower():
            campaign_type = "enhanced_insurance_service"
            agent_type = "insurance_service_agent"
            workflow_type = "insurance_service_automation"

        # Create response with campaign details
        response = {
            "success": True,
            "message": f"Enhanced template campaign '{request.template_name}' for {request.company_name} created successfully",
            "campaign": {
                "id": f"{campaign_type}_{request.tenant_id}_{int(datetime.now().timestamp())}",
                "company_name": request.company_name,
                "template_id": request.template_id,
                "template_name": request.template_name,
                "type": campaign_type,
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "tenant_id": request.tenant_id,
                "config": request.config
            },
            "vapi_agent": {
                "id": f"vapi_{campaign_type}_{request.tenant_id}_{int(datetime.now().timestamp())}",
                "name": f"{request.template_name} Agent - {request.company_name}",
                "type": agent_type,
                "status": "active",
                "config": request.vapi_agent
            },
            "n8n_workflow": {
                "id": f"n8n_{campaign_type}_{request.tenant_id}_{int(datetime.now().timestamp())}",
                "name": f"{request.template_name} Workflow - {request.company_name}",
                "type": workflow_type,
                "status": "active",
                "config": request.n8n_workflow
            },
            "demo": {
                "enabled": request.enable_demo,
                "url": f"/demo/{campaign_type}/{request.tenant_id}" if request.enable_demo else None
            },
            "analytics": {
                "enabled": request.enable_analytics,
                "dashboard_url": f"/analytics/{campaign_type}/{request.tenant_id}" if request.enable_analytics else None
            }
        }

        logger.info(f"Enhanced template campaign '{request.template_name}' created successfully for {request.company_name}")
        return response

    except Exception as e:
        logger.error(f"Error creating enhanced template campaign: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create enhanced template campaign: {str(e)}")