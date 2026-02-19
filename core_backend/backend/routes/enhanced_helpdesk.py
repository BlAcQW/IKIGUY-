"""
API routes for enhanced helpdesk functionality.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from datetime import datetime
import logging

from ..services.enhanced_helpdesk_service import enhanced_helpdesk_service
from ..services.helpdesk_analytics_service import helpdesk_analytics_service
from ..auth import get_current_user_mongo
from .ai_prompt_generator import analyze_website_content, analyze_multiple_websites

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enhanced-helpdesk", tags=["enhanced-helpdesk"])

class SiteExtractionRequest(BaseModel):
    """Request model for site extraction."""
    url: str
    extraction_type: str = "company_info"

class MultiSiteExtractionRequest(BaseModel):
    """Request model for multi-site extraction using AI analysis."""
    website_urls: List[str]
    documents: Optional[List[Dict[str, str]]] = None
    extraction_type: str = "company_info"

class EnhancedHelpdeskRequest(BaseModel):
    """Request model for creating enhanced helpdesk."""
    company_name: str
    company_description: Optional[str] = ""
    company_url: str
    integrations: Dict[str, Any] = {}
    enable_demo: bool = True
    enable_analytics: bool = True
    tenant_id: str

class DemoDeploymentRequest(BaseModel):
    """Request model for demo deployment."""
    company_name: str
    html: str
    vapi_assistant_id: str

@router.post("/extract-site-info")
async def extract_site_info(
    request: SiteExtractionRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Extract company information from a website URL using AI-powered analysis.

    Args:
        request: Site extraction request with URL and extraction type
        current_user: Authenticated user information

    Returns:
        Extracted company information using enhanced AI analysis
    """
    try:
        logger.info(f"Extracting site info for URL: {request.url}")

        # Use the enhanced AI-powered website analysis
        website_analysis = await analyze_website_content(request.url)

        # Transform the AI analysis to match the expected format
        company_info = website_analysis["company_info"]
        contact_info = website_analysis.get("contact_info", {})

        # Map AI analysis to Enhanced Helpdesk format
        extracted_info = {
            "company_name": company_info.get("name", ""),
            "services": website_analysis.get("services_products", [])[:8],
            "business_hours": "Please contact us for business hours",
            "contact_info": {
                "phone": contact_info.get("phone"),
                "email": contact_info.get("email"),
                "address": None
            },
            "about_text": company_info.get("description", ""),
            "meta_description": company_info.get("description", ""),
            # Additional AI-powered insights
            "business_type": website_analysis.get("business_type", "general"),
            "tone_style": website_analysis.get("tone_style", "professional"),
            "target_audience": website_analysis.get("target_audience", "general"),
            "key_content": website_analysis.get("key_content", []),
            "ai_enhanced": True,
            "analysis_timestamp": website_analysis.get("scraped_at")
        }

        return {
            "success": True,
            "data": extracted_info,
            "extraction_type": request.extraction_type,
            "url": request.url,
            "ai_powered": True,
            "enhanced_analysis": {
                "business_insights": {
                    "type": website_analysis.get("business_type"),
                    "tone": website_analysis.get("tone_style"),
                    "audience": website_analysis.get("target_audience")
                },
                "content_analysis": {
                    "key_themes": website_analysis.get("key_content", []),
                    "services_count": len(website_analysis.get("services_products", [])),
                    "content_depth": len(company_info.get("full_content", ""))
                }
            }
        }

    except Exception as e:
        logger.error(f"Error extracting site info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract site information: {str(e)}"
        )

@router.post("/extract-multi-site-info")
async def extract_multi_site_info(
    request: MultiSiteExtractionRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Extract comprehensive company information from multiple website URLs using AI analysis.

    Args:
        request: Multi-site extraction request with URLs and optional documents
        current_user: Authenticated user information

    Returns:
        Combined extracted company information from multiple sources
    """
    try:
        logger.info(f"Extracting multi-site info for URLs: {request.website_urls}")

        # Use the enhanced AI-powered multiple website analysis
        combined_analysis = await analyze_multiple_websites(request.website_urls)

        # Transform the AI analysis to Enhanced Helpdesk format
        company_info = combined_analysis["company_info"]
        contact_info = combined_analysis.get("contact_info", {})

        # Enhanced mapping with multi-source data
        extracted_info = {
            "company_name": company_info.get("name", ""),
            "services": combined_analysis.get("services_products", [])[:15],  # More services from multiple sites
            "business_hours": "Please contact us for business hours",
            "contact_info": {
                "phone": contact_info.get("phone"),
                "email": contact_info.get("email"),
                "address": None
            },
            "about_text": company_info.get("description", ""),
            "meta_description": company_info.get("description", ""),
            # Enhanced AI insights from multiple sources
            "business_type": combined_analysis.get("business_type", "general"),
            "tone_style": combined_analysis.get("tone_style", "professional"),
            "target_audience": combined_analysis.get("target_audience", "general"),
            "key_content": combined_analysis.get("key_content", []),
            "ai_enhanced": True,
            "multi_source": True,
            "sources_analyzed": len(request.website_urls),
            "analysis_timestamp": combined_analysis.get("scraped_at"),
            "full_content_summary": company_info.get("full_content", "")[:500] + "..." if len(company_info.get("full_content", "")) > 500 else company_info.get("full_content", "")
        }

        return {
            "success": True,
            "data": extracted_info,
            "extraction_type": request.extraction_type,
            "urls": request.website_urls,
            "ai_powered": True,
            "multi_source_analysis": True,
            "enhanced_analysis": {
                "business_insights": {
                    "type": combined_analysis.get("business_type"),
                    "tone": combined_analysis.get("tone_style"),
                    "audience": combined_analysis.get("target_audience")
                },
                "content_analysis": {
                    "key_themes": combined_analysis.get("key_content", []),
                    "services_count": len(combined_analysis.get("services_products", [])),
                    "content_depth": len(company_info.get("full_content", "")),
                    "sources_combined": len(request.website_urls),
                    "comprehensive_score": min(100, len(company_info.get("full_content", "")) / 20)  # Score out of 100
                }
            }
        }

    except Exception as e:
        logger.error(f"Error extracting multi-site info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract multi-site information: {str(e)}"
        )

@router.post("/create")
async def create_enhanced_helpdesk(
    request: EnhancedHelpdeskRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Create a complete enhanced helpdesk campaign.

    Args:
        request: Enhanced helpdesk creation request
        background_tasks: Background task queue
        current_user: Authenticated user information

    Returns:
        Created helpdesk configuration and resources
    """
    try:
        logger.info(f"Creating enhanced helpdesk for {request.company_name}")

        # Create the enhanced helpdesk
        result = await enhanced_helpdesk_service.create_enhanced_helpdesk(
            company_url=request.company_url,
            company_name=request.company_name,
            company_description=request.company_description,
            integrations=request.integrations,
            enable_demo=request.enable_demo,
            enable_analytics=request.enable_analytics
        )

        if not result.get('success'):
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Failed to create enhanced helpdesk')
            )

        # Add tenant information
        result['tenant_id'] = request.tenant_id
        result['created_by'] = current_user.get('id')

        # TODO: Save to database in background
        # background_tasks.add_task(save_helpdesk_to_db, result)

        return {
            "success": True,
            "message": "Enhanced helpdesk created successfully",
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating enhanced helpdesk: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create enhanced helpdesk: {str(e)}"
        )



@router.get("/list")
async def list_helpdesks(
    tenant_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    List all helpdesk campaigns for a tenant.

    Args:
        tenant_id: Optional tenant ID filter
        current_user: Authenticated user information

    Returns:
        List of helpdesk campaigns
    """
    try:
        # TODO: Implement database query to list helpdesks
        # For now, return mock data
        mock_helpdesks = [
            {
                "id": "helpdesk-001",
                "company_name": "GLICO Life Insurance",
                "status": "active",
                "demo_url": "https://demos.ailabsafrica.com/demo-glico001",
                "analytics_url": "https://analytics.ailabsafrica.com/helpdesk/vapi-glico001",
                "vapi_assistant_id": "vapi-glico001",
                "created_at": "2024-01-15T10:30:00Z",
                "stats": {
                    "total_calls": 1250,
                    "successful_calls": 1125,
                    "appointments_booked": 340,
                    "tickets_created": 180,
                    "customer_satisfaction": 4.7
                }
            }
        ]

        return {
            "success": True,
            "data": mock_helpdesks,
            "total": len(mock_helpdesks)
        }

    except Exception as e:
        logger.error(f"Error listing helpdesks: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list helpdesks: {str(e)}"
        )

@router.get("/{helpdesk_id}")
async def get_helpdesk(
    helpdesk_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get detailed information about a specific helpdesk.

    Args:
        helpdesk_id: Helpdesk ID
        current_user: Authenticated user information

    Returns:
        Detailed helpdesk information
    """
    try:
        # TODO: Implement database query to get helpdesk details
        # For now, return mock data
        mock_helpdesk = {
            "id": helpdesk_id,
            "company_name": "GLICO Life Insurance",
            "company_url": "https://www.glico.com.gh",
            "status": "active",
            "demo_url": "https://demos.ailabsafrica.com/demo-glico001",
            "analytics_url": "https://analytics.ailabsafrica.com/helpdesk/vapi-glico001",
            "vapi_assistant": {
                "id": "vapi-glico001",
                "name": "GLICO Life Helpdesk Assistant",
                "phone_number": "+1555GLICO01"
            },
            "n8n_workflow": {
                "id": "workflow-glico001",
                "name": "GLICO Life Helpdesk Automation",
                "webhook_url": "https://automate.inspirecreations.it.com/webhook/helpdesk/workflow-glico001"
            },
            "integrations": {
                "calendly": {"enabled": True},
                "supabase": {"enabled": True},
                "tavily": {"enabled": True},
                "resend": {"enabled": True},
                "vonage": {"enabled": True}
            },
            "analytics": {
                "total_calls": 1250,
                "successful_calls": 1125,
                "success_rate": 90.0,
                "avg_call_duration": 4.5,
                "appointments_booked": 340,
                "tickets_created": 180,
                "customer_satisfaction": 4.7,
                "escalation_rate": 8.5
            },
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-20T14:45:00Z"
        }

        return {
            "success": True,
            "data": mock_helpdesk
        }

    except Exception as e:
        logger.error(f"Error getting helpdesk {helpdesk_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get helpdesk: {str(e)}"
        )

@router.get("/{helpdesk_id}/analytics")
async def get_helpdesk_analytics(
    helpdesk_id: str,
    period_days: int = 7,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get comprehensive analytics data for a specific helpdesk.

    Args:
        helpdesk_id: Helpdesk ID
        period_days: Number of days for analytics period (default: 7)
        current_user: Authenticated user information

    Returns:
        Comprehensive analytics data
    """
    try:
        logger.info(f"Getting analytics for helpdesk {helpdesk_id}")

        # Get comprehensive analytics from the service
        analytics = await helpdesk_analytics_service.get_comprehensive_analytics(
            helpdesk_id, period_days
        )

        return {
            "success": True,
            "data": analytics.dict(),
            "helpdesk_id": helpdesk_id,
            "period_days": period_days
        }

    except Exception as e:
        logger.error(f"Error getting analytics for helpdesk {helpdesk_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get analytics: {str(e)}"
        )

@router.get("/{helpdesk_id}/real-time")
async def get_real_time_metrics(
    helpdesk_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get real-time metrics for monitoring dashboard.

    Args:
        helpdesk_id: Helpdesk ID
        current_user: Authenticated user information

    Returns:
        Real-time metrics data
    """
    try:
        logger.info(f"Getting real-time metrics for helpdesk {helpdesk_id}")

        # Get real-time metrics from the service
        metrics = await helpdesk_analytics_service.get_real_time_metrics(helpdesk_id)

        return {
            "success": True,
            "data": metrics,
            "helpdesk_id": helpdesk_id,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting real-time metrics for helpdesk {helpdesk_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get real-time metrics: {str(e)}"
        )

@router.post("/{helpdesk_id}/toggle")
async def toggle_helpdesk_status(
    helpdesk_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Toggle helpdesk active/inactive status.

    Args:
        helpdesk_id: Helpdesk ID
        current_user: Authenticated user information

    Returns:
        Updated status
    """
    try:
        # TODO: Implement status toggle in database and VAPI
        # For now, return mock response
        new_status = "inactive"  # This would be determined by current status

        return {
            "success": True,
            "message": f"Helpdesk status updated to {new_status}",
            "helpdesk_id": helpdesk_id,
            "status": new_status
        }

    except Exception as e:
        logger.error(f"Error toggling helpdesk {helpdesk_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to toggle helpdesk status: {str(e)}"
        )

@router.delete("/{helpdesk_id}")
async def delete_helpdesk(
    helpdesk_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Delete a helpdesk campaign.

    Args:
        helpdesk_id: Helpdesk ID
        current_user: Authenticated user information

    Returns:
        Deletion confirmation
    """
    try:
        # TODO: Implement deletion of VAPI assistant, N8N workflow, demo page, etc.
        # For now, return mock response

        return {
            "success": True,
            "message": "Helpdesk deleted successfully",
            "helpdesk_id": helpdesk_id
        }

    except Exception as e:
        logger.error(f"Error deleting helpdesk {helpdesk_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete helpdesk: {str(e)}"
        )