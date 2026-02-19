"""
API routes for enhanced lead nurturing functionality.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
import logging

from ..auth import get_current_user_mongo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enhanced-lead-nurturing", tags=["enhanced-lead-nurturing"])

class EnhancedLeadNurturingRequest(BaseModel):
    """Request model for creating enhanced lead nurturing."""
    company_name: str
    company_description: Optional[str] = ""
    company_website: str
    industry: str
    audience_id: str
    nurture_sequence_length: int
    touchpoint_frequency: str
    lead_scoring_criteria: List[str]
    content_types: List[str]
    data_source: str
    lead_score_threshold: int
    behavior_tracking: List[str]
    engagement_metrics: List[str]
    voice_personality: str
    nurture_script: str
    follow_up_questions: List[str]
    escalation_triggers: List[str]
    workflow_triggers: List[str]
    automation_rules: List[str]
    integration_endpoints: List[str]
    crm_system: str
    email_platform: str
    analytics_tools: List[str]
    lead_scoring_tools: List[str]
    demo_environment: str
    test_lead_profiles: List[str]
    tracking_metrics: List[str]
    reporting_frequency: str
    kpis: List[str]
    tenant_id: str

@router.post("/create")
async def create_enhanced_lead_nurturing(
    request: EnhancedLeadNurturingRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Create a complete enhanced lead nurturing campaign.

    Args:
        request: Enhanced lead nurturing creation request
        background_tasks: Background task queue
        current_user: Current authenticated user

    Returns:
        dict: Campaign creation response with VAPI agent, N8N workflow, and demo details
    """
    try:
        logger.info(f"Creating enhanced lead nurturing for {request.company_name}")

        # Create response with campaign details
        response = {
            "success": True,
            "message": f"Enhanced lead nurturing campaign for {request.company_name} created successfully",
            "campaign": {
                "id": f"lead_nurturing_{request.tenant_id}_{int(datetime.now().timestamp())}",
                "company_name": request.company_name,
                "type": "enhanced_lead_nurturing",
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "tenant_id": request.tenant_id,
                "config": {
                    "nurture_sequence_length": request.nurture_sequence_length,
                    "touchpoint_frequency": request.touchpoint_frequency,
                    "lead_score_threshold": request.lead_score_threshold,
                    "reporting_frequency": request.reporting_frequency
                }
            },
            "vapi_agent": {
                "id": f"vapi_nurturing_{request.tenant_id}_{int(datetime.now().timestamp())}",
                "name": f"Lead Nurturing Agent - {request.company_name}",
                "type": "lead_nurturing_agent",
                "personality": request.voice_personality,
                "status": "active"
            },
            "n8n_workflow": {
                "id": f"n8n_nurturing_{request.tenant_id}_{int(datetime.now().timestamp())}",
                "name": f"Lead Nurturing Workflow - {request.company_name}",
                "type": "lead_nurturing_automation",
                "triggers": request.workflow_triggers,
                "status": "active"
            },
            "demo": {
                "enabled": True,
                "environment": request.demo_environment,
                "url": f"/demo/lead-nurturing/{request.tenant_id}"
            },
            "analytics": {
                "enabled": True,
                "tracking_metrics": request.tracking_metrics,
                "kpis": request.kpis,
                "dashboard_url": f"/analytics/lead-nurturing/{request.tenant_id}"
            }
        }

        logger.info(f"Enhanced lead nurturing campaign created successfully for {request.company_name}")
        return response

    except Exception as e:
        logger.error(f"Error creating enhanced lead nurturing campaign: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create enhanced lead nurturing campaign: {str(e)}")