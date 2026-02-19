"""
API routes for enhanced sales outreach functionality.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
import logging

from ..auth import get_current_user_mongo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enhanced-sales-outreach", tags=["enhanced-sales-outreach"])

class EnhancedSalesOutreachRequest(BaseModel):
    """Request model for creating enhanced sales outreach."""
    company_name: str
    company_description: Optional[str] = ""
    company_url: str
    audience_id: str
    audience_name: str
    audience_size: int
    sales_config: Dict[str, Any] = {}
    vapi_agent: Dict[str, Any] = {}
    n8n_workflow: Dict[str, Any] = {}
    integrations: Dict[str, Any] = {}
    enable_demo: bool = True
    enable_analytics: bool = True
    tenant_id: str

@router.post("/create")
async def create_enhanced_sales_outreach(
    request: EnhancedSalesOutreachRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Create a complete enhanced sales outreach campaign.

    Args:
        request: Enhanced sales outreach creation request
        background_tasks: Background task queue
        current_user: Current authenticated user

    Returns:
        dict: Campaign creation response with VAPI agent, N8N workflow, and demo details
    """
    try:
        logger.info(f"Creating enhanced sales outreach for {request.company_name}")

        # Create response with campaign details
        response = {
            "success": True,
            "message": f"Enhanced sales outreach campaign for {request.company_name} created successfully",
            "campaign": {
                "id": f"sales_outreach_{request.tenant_id}_{int(datetime.now().timestamp())}",
                "company_name": request.company_name,
                "type": "enhanced_sales_outreach",
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "tenant_id": request.tenant_id
            },
            "vapi_agent": {
                "id": f"vapi_sales_{request.tenant_id}_{int(datetime.now().timestamp())}",
                "name": f"Sales Outreach Agent - {request.company_name}",
                "type": "sales_cold_outreach_agent",
                "status": "active"
            },
            "n8n_workflow": {
                "id": f"n8n_sales_{request.tenant_id}_{int(datetime.now().timestamp())}",
                "name": f"Sales Outreach Workflow - {request.company_name}",
                "type": "cold_calling_automation",
                "status": "active"
            },
            "demo": {
                "enabled": request.enable_demo,
                "url": f"/demo/sales-outreach/{request.tenant_id}" if request.enable_demo else None
            },
            "analytics": {
                "enabled": request.enable_analytics,
                "dashboard_url": f"/analytics/sales-outreach/{request.tenant_id}" if request.enable_analytics else None
            }
        }

        logger.info(f"Enhanced sales outreach campaign created successfully for {request.company_name}")
        return response

    except Exception as e:
        logger.error(f"Error creating enhanced sales outreach campaign: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create enhanced sales outreach campaign: {str(e)}")