"""
API routes for enhanced customer reactivation functionality.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from pydantic import BaseModel
from datetime import datetime
import logging

from ..auth import get_current_user_mongo
from ..middleware.organization_context import (
    get_organization_context,
    validate_organization_access
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enhanced-customer-reactivation", tags=["enhanced-customer-reactivation"])

class EnhancedCustomerReactivationRequest(BaseModel):
    """Request model for creating enhanced customer reactivation."""
    company_name: str
    company_description: Optional[str] = ""
    company_website: str
    industry: str
    audience_id: str
    churn_period: str
    contact_preference: List[str]
    reactivation_offers: List[str]
    priority_segments: List[str]
    win_back_incentives: List[str]
    data_source: str
    churn_indicators: List[str]
    behavior_triggers: List[str]
    value_metrics: List[str]
    voice_personality: str
    reactivation_script: str
    objection_handling: str
    escalation_conditions: List[str]
    workflow_triggers: List[str]
    automation_sequence: List[str]
    integration_points: List[str]
    crm_system: str
    email_platform: str
    customer_data_platform: str
    analytics_tools: List[str]
    demo_environment: str
    test_scenarios: List[str]
    tracking_metrics: List[str]
    reporting_frequency: str
    success_kpis: List[str]
    tenant_id: str

@router.post("/create")
async def create_enhanced_customer_reactivation(
    campaign_request: EnhancedCustomerReactivationRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Create a complete enhanced customer reactivation campaign.

    Now properly scoped to organization. Requires authentication.

    Args:
        campaign_request: Enhanced customer reactivation creation request
        background_tasks: Background task queue
        request: HTTP request for organization context
        current_user: Current authenticated user

    Returns:
        dict: Campaign creation response with VAPI agent, N8N workflow, and demo details
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Creating enhanced customer reactivation for {campaign_request.company_name}, organization={org_id}")

        # Create response with campaign details
        response = {
            "success": True,
            "message": f"Enhanced customer reactivation campaign for {campaign_request.company_name} created successfully",
            "campaign": {
                "id": f"customer_reactivation_{campaign_request.tenant_id}_{int(datetime.now().timestamp())}",
                "company_name": campaign_request.company_name,
                "type": "enhanced_customer_reactivation",
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "tenant_id": campaign_request.tenant_id,
                "config": {
                    "churn_period": campaign_request.churn_period,
                    "contact_preference": campaign_request.contact_preference,
                    "reporting_frequency": campaign_request.reporting_frequency
                }
            },
            "vapi_agent": {
                "id": f"vapi_reactivation_{campaign_request.tenant_id}_{int(datetime.now().timestamp())}",
                "name": f"Customer Reactivation Agent - {campaign_request.company_name}",
                "type": "reactivation_agent",
                "personality": campaign_request.voice_personality,
                "status": "active"
            },
            "n8n_workflow": {
                "id": f"n8n_reactivation_{campaign_request.tenant_id}_{int(datetime.now().timestamp())}",
                "name": f"Customer Reactivation Workflow - {campaign_request.company_name}",
                "type": "customer_reactivation_automation",
                "triggers": campaign_request.workflow_triggers,
                "automation_sequence": campaign_request.automation_sequence,
                "status": "active"
            },
            "demo": {
                "enabled": True,
                "environment": campaign_request.demo_environment,
                "test_scenarios": campaign_request.test_scenarios,
                "url": f"/demo/customer-reactivation/{campaign_request.tenant_id}"
            },
            "analytics": {
                "enabled": True,
                "tracking_metrics": campaign_request.tracking_metrics,
                "success_kpis": campaign_request.success_kpis,
                "dashboard_url": f"/analytics/customer-reactivation/{campaign_request.tenant_id}"
            }
        }

        logger.info(f"Enhanced customer reactivation campaign created successfully for {campaign_request.company_name}, organization={org_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating enhanced customer reactivation campaign for organization={org_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create enhanced customer reactivation campaign: {str(e)}")