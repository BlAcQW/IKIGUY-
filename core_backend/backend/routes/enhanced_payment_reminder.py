"""
API routes for enhanced payment reminder functionality.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import logging
from decimal import Decimal

from ..services.enhanced_payment_reminder_service import enhanced_payment_reminder_service
from ..services.payment_analytics_service import payment_analytics_service
from ..auth import get_current_user_mongo
from .ai_prompt_generator import analyze_website_content, analyze_multiple_websites

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enhanced-payment-reminder", tags=["enhanced-payment-reminder"])

class CustomerInfoExtractionRequest(BaseModel):
    """Request model for customer information extraction."""
    url: str
    extraction_type: str = "customer_info"
    account_number: Optional[str] = None

class MultiSourceExtractionRequest(BaseModel):
    """Request model for multi-source customer information extraction."""
    website_urls: List[str]
    customer_documents: Optional[List[Dict[str, str]]] = None
    extraction_type: str = "customer_info"
    account_number: Optional[str] = None

class EnhancedPaymentReminderRequest(BaseModel):
    """Request model for creating enhanced payment reminder campaign."""
    company_name: str
    company_description: Optional[str] = ""
    company_url: str
    debt_collection_settings: Dict[str, Any] = Field(default_factory=dict)
    compliance_settings: Dict[str, Any] = Field(default_factory=dict)
    integrations: Dict[str, Any] = Field(default_factory=dict)
    enable_demo: bool = True
    enable_analytics: bool = True
    tenant_id: str

class PaymentDemoDeploymentRequest(BaseModel):
    """Request model for payment reminder demo deployment."""
    company_name: str
    html: str
    vapi_assistant_id: str
    demo_account_data: Optional[Dict[str, Any]] = None

class PaymentCampaignRequest(BaseModel):
    """Request model for payment campaign execution."""
    campaign_id: str
    customer_list: List[Dict[str, Any]]
    payment_settings: Dict[str, Any]
    compliance_check: bool = True

@router.post("/extract-customer-info")
async def extract_customer_info(
    request: CustomerInfoExtractionRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Extract customer and business information from a website URL for payment campaigns.

    Args:
        request: Customer information extraction request with URL and extraction type
        current_user: Authenticated user information

    Returns:
        Extracted customer and business information for debt collection purposes
    """
    try:
        logger.info(f"Extracting customer info for URL: {request.url}")

        # Use the enhanced AI-powered website analysis
        website_analysis = await analyze_website_content(request.url)

        # Transform the AI analysis to payment reminder format
        company_info = website_analysis["company_info"]
        contact_info = website_analysis.get("contact_info", {})

        # Map AI analysis to Enhanced Payment Reminder format
        extracted_info = {
            "company_name": company_info.get("name", ""),
            "business_type": website_analysis.get("business_type", "general"),
            "services": website_analysis.get("services_products", [])[:8],
            "contact_info": {
                "phone": contact_info.get("phone"),
                "email": contact_info.get("email"),
                "address": contact_info.get("address")
            },
            "business_hours": "Standard business hours",
            "payment_methods": ["Credit Card", "ACH Transfer", "Check"],
            "company_description": company_info.get("description", ""),
            # Payment-specific insights
            "collection_profile": {
                "business_size": website_analysis.get("business_type", "small"),
                "industry_risk": "standard",
                "preferred_contact_method": "phone",
                "estimated_payment_capacity": "standard"
            },
            "compliance_notes": {
                "fdcpa_applicable": True,
                "tcpa_consent_required": True,
                "state_regulations": "standard"
            },
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
                "collection_insights": {
                    "risk_profile": extracted_info["collection_profile"]["industry_risk"],
                    "contact_preference": extracted_info["collection_profile"]["preferred_contact_method"],
                    "capacity_estimate": extracted_info["collection_profile"]["estimated_payment_capacity"]
                },
                "compliance_requirements": {
                    "fdcpa_applicable": extracted_info["compliance_notes"]["fdcpa_applicable"],
                    "tcpa_required": extracted_info["compliance_notes"]["tcpa_consent_required"]
                }
            }
        }

    except Exception as e:
        logger.error(f"Error extracting customer info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract customer information: {str(e)}"
        )

@router.post("/extract-multi-source-info")
async def extract_multi_source_info(
    request: MultiSourceExtractionRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Extract comprehensive customer information from multiple sources for payment campaigns.

    Args:
        request: Multi-source extraction request with URLs and optional documents
        current_user: Authenticated user information

    Returns:
        Combined extracted customer information from multiple sources
    """
    try:
        logger.info(f"Extracting multi-source info for URLs: {request.website_urls}")

        # Use the enhanced AI-powered multiple website analysis
        combined_analysis = await analyze_multiple_websites(request.website_urls)

        # Transform the AI analysis to Enhanced Payment Reminder format
        company_info = combined_analysis["company_info"]
        contact_info = combined_analysis.get("contact_info", {})

        # Enhanced mapping with multi-source data
        extracted_info = {
            "company_name": company_info.get("name", ""),
            "business_type": combined_analysis.get("business_type", "general"),
            "services": combined_analysis.get("services_products", [])[:15],
            "contact_info": {
                "phone": contact_info.get("phone"),
                "email": contact_info.get("email"),
                "address": contact_info.get("address")
            },
            "business_hours": "Standard business hours",
            "payment_methods": ["Credit Card", "ACH Transfer", "Wire Transfer", "Check", "Cash"],
            "company_description": company_info.get("description", ""),
            # Enhanced payment-specific insights from multiple sources
            "collection_profile": {
                "business_size": combined_analysis.get("business_type", "medium"),
                "industry_risk": "evaluated",
                "preferred_contact_method": "phone",
                "estimated_payment_capacity": "above_average",
                "credit_indicators": combined_analysis.get("financial_indicators", [])
            },
            "compliance_notes": {
                "fdcpa_applicable": True,
                "tcpa_consent_required": True,
                "state_regulations": "comprehensive",
                "special_requirements": []
            },
            "ai_enhanced": True,
            "multi_source": True,
            "sources_analyzed": len(request.website_urls),
            "analysis_timestamp": combined_analysis.get("scraped_at"),
            "comprehensive_summary": company_info.get("full_content", "")[:500] + "..." if len(company_info.get("full_content", "")) > 500 else company_info.get("full_content", "")
        }

        return {
            "success": True,
            "data": extracted_info,
            "extraction_type": request.extraction_type,
            "urls": request.website_urls,
            "ai_powered": True,
            "multi_source_analysis": True,
            "enhanced_analysis": {
                "collection_insights": {
                    "risk_profile": extracted_info["collection_profile"]["industry_risk"],
                    "contact_preference": extracted_info["collection_profile"]["preferred_contact_method"],
                    "capacity_estimate": extracted_info["collection_profile"]["estimated_payment_capacity"],
                    "financial_strength": len(extracted_info["collection_profile"]["credit_indicators"])
                },
                "compliance_requirements": {
                    "fdcpa_applicable": extracted_info["compliance_notes"]["fdcpa_applicable"],
                    "tcpa_required": extracted_info["compliance_notes"]["tcpa_consent_required"],
                    "regulatory_complexity": extracted_info["compliance_notes"]["state_regulations"]
                },
                "data_quality": {
                    "sources_combined": len(request.website_urls),
                    "content_depth": len(company_info.get("full_content", "")),
                    "reliability_score": min(100, len(company_info.get("full_content", "")) / 25)
                }
            }
        }

    except Exception as e:
        logger.error(f"Error extracting multi-source info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract multi-source information: {str(e)}"
        )

@router.post("/create")
async def create_enhanced_payment_reminder(
    request: EnhancedPaymentReminderRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Create a complete enhanced payment reminder campaign.

    Args:
        request: Enhanced payment reminder creation request
        background_tasks: Background task queue
        current_user: Authenticated user information

    Returns:
        Created payment reminder configuration and resources
    """
    try:
        logger.info(f"Creating enhanced payment reminder for {request.company_name}")

        # Create the enhanced payment reminder
        result = await enhanced_payment_reminder_service.create_enhanced_payment_reminder(
            company_url=request.company_url,
            company_name=request.company_name,
            company_description=request.company_description,
            debt_collection_settings=request.debt_collection_settings,
            compliance_settings=request.compliance_settings,
            integrations=request.integrations,
            enable_demo=request.enable_demo,
            enable_analytics=request.enable_analytics
        )

        if not result.get('success'):
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Failed to create enhanced payment reminder')
            )

        # Add tenant information
        result['tenant_id'] = request.tenant_id
        result['created_by'] = current_user.get('id')

        # TODO: Save to database in background
        # background_tasks.add_task(save_payment_reminder_to_db, result)

        return {
            "success": True,
            "message": "Enhanced payment reminder created successfully",
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating enhanced payment reminder: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create enhanced payment reminder: {str(e)}"
        )

@router.post("/deploy-demo")
async def deploy_payment_demo(
    request: PaymentDemoDeploymentRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Deploy a demo page for the payment reminder system.

    Args:
        request: Payment demo deployment request
        current_user: Authenticated user information

    Returns:
        Demo deployment information
    """
    try:
        logger.info(f"Deploying payment demo for {request.company_name}")

        # In a real implementation, this would deploy to a hosting service
        import uuid
        demo_id = f"payment-demo-{uuid.uuid4().hex[:8]}"
        demo_url = f"https://demos.ailabsafrica.com/{demo_id}"

        # TODO: Actually deploy the HTML to a hosting service
        # await deploy_html_to_hosting(request.html, demo_id)

        return {
            "success": True,
            "url": demo_url,
            "demo_id": demo_id,
            "company_name": request.company_name,
            "vapi_assistant_id": request.vapi_assistant_id,
            "demo_type": "payment_reminder"
        }

    except Exception as e:
        logger.error(f"Error deploying payment demo: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to deploy payment demo: {str(e)}"
        )

@router.post("/execute-campaign")
async def execute_payment_campaign(
    request: PaymentCampaignRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Execute a payment reminder campaign for a list of customers.

    Args:
        request: Payment campaign execution request
        background_tasks: Background task queue
        current_user: Authenticated user information

    Returns:
        Campaign execution status and tracking information
    """
    try:
        logger.info(f"Executing payment campaign {request.campaign_id}")

        # Validate compliance requirements before execution
        if request.compliance_check:
            compliance_result = await enhanced_payment_reminder_service.validate_compliance(
                request.customer_list, request.payment_settings
            )
            if not compliance_result.get('valid'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Compliance validation failed: {compliance_result.get('error')}"
                )

        # Execute the campaign in background
        background_tasks.add_task(
            enhanced_payment_reminder_service.execute_campaign,
            request.campaign_id,
            request.customer_list,
            request.payment_settings
        )

        return {
            "success": True,
            "message": "Payment campaign initiated successfully",
            "campaign_id": request.campaign_id,
            "customers_count": len(request.customer_list),
            "execution_status": "initiated",
            "estimated_completion": (datetime.utcnow() + timedelta(hours=2)).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing payment campaign: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute payment campaign: {str(e)}"
        )

@router.get("/list")
async def list_payment_reminders(
    tenant_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    List all payment reminder campaigns for a tenant.

    Args:
        tenant_id: Optional tenant ID filter
        current_user: Authenticated user information

    Returns:
        List of payment reminder campaigns
    """
    try:
        # TODO: Implement database query to list payment reminders
        # For now, return mock data
        mock_campaigns = [
            {
                "id": "payment-001",
                "company_name": "GLICO Financial Services",
                "status": "active",
                "demo_url": "https://demos.ailabsafrica.com/payment-demo-glico001",
                "analytics_url": "https://analytics.ailabsafrica.com/payment/vapi-payment-glico001",
                "vapi_assistant_id": "vapi-payment-glico001",
                "created_at": "2024-01-15T10:30:00Z",
                "campaign_type": "payment_reminder",
                "stats": {
                    "total_calls": 850,
                    "successful_calls": 765,
                    "payments_collected": 425,
                    "payment_plans_arranged": 180,
                    "total_recovered": 125000.00,
                    "compliance_score": 98.5
                }
            }
        ]

        return {
            "success": True,
            "data": mock_campaigns,
            "total": len(mock_campaigns)
        }

    except Exception as e:
        logger.error(f"Error listing payment reminders: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list payment reminders: {str(e)}"
        )

@router.get("/{campaign_id}")
async def get_payment_reminder(
    campaign_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get detailed information about a specific payment reminder campaign.

    Args:
        campaign_id: Payment reminder campaign ID
        current_user: Authenticated user information

    Returns:
        Detailed payment reminder campaign information
    """
    try:
        # TODO: Implement database query to get campaign details
        # For now, return mock data
        mock_campaign = {
            "id": campaign_id,
            "company_name": "GLICO Financial Services",
            "company_url": "https://www.glicofinance.com.gh",
            "status": "active",
            "demo_url": "https://demos.ailabsafrica.com/payment-demo-glico001",
            "analytics_url": "https://analytics.ailabsafrica.com/payment/vapi-payment-glico001",
            "vapi_assistant": {
                "id": "vapi-payment-glico001",
                "name": "GLICO Payment Reminder Assistant",
                "phone_number": "+1555PAYMENT01"
            },
            "n8n_workflow": {
                "id": "workflow-payment-glico001",
                "name": "GLICO Payment Reminder Automation",
                "webhook_url": "https://automate.inspirecreations.it.com/webhook/payment/workflow-payment-glico001"
            },
            "debt_collection_settings": {
                "max_call_attempts": 3,
                "escalation_threshold": 30,
                "minimum_payment_amount": 25.00,
                "payment_plan_options": True
            },
            "compliance_settings": {
                "fdcpa_enabled": True,
                "tcpa_enabled": True,
                "call_time_restrictions": "8AM-9PM",
                "cease_desist_respect": True
            },
            "integrations": {
                "quickbooks": {"enabled": True},
                "stripe": {"enabled": True},
                "freshdesk": {"enabled": True},
                "vonage": {"enabled": True}
            },
            "analytics": {
                "total_calls": 850,
                "successful_calls": 765,
                "success_rate": 90.0,
                "avg_call_duration": 6.2,
                "payments_collected": 425,
                "payment_plans_arranged": 180,
                "total_recovered": 125000.00,
                "avg_recovery_amount": 294.12,
                "compliance_score": 98.5,
                "escalation_rate": 12.5
            },
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-20T14:45:00Z"
        }

        return {
            "success": True,
            "data": mock_campaign
        }

    except Exception as e:
        logger.error(f"Error getting payment reminder {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get payment reminder: {str(e)}"
        )

@router.get("/{campaign_id}/analytics")
async def get_payment_analytics(
    campaign_id: str,
    period_days: int = 7,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get comprehensive analytics data for a specific payment reminder campaign.

    Args:
        campaign_id: Payment reminder campaign ID
        period_days: Number of days for analytics period (default: 7)
        current_user: Authenticated user information

    Returns:
        Comprehensive payment analytics data
    """
    try:
        logger.info(f"Getting payment analytics for campaign {campaign_id}")

        # Get comprehensive analytics from the service
        analytics = await payment_analytics_service.get_comprehensive_analytics(
            campaign_id, period_days
        )

        return {
            "success": True,
            "data": analytics.dict(),
            "campaign_id": campaign_id,
            "period_days": period_days
        }

    except Exception as e:
        logger.error(f"Error getting payment analytics for campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get payment analytics: {str(e)}"
        )

@router.get("/{campaign_id}/compliance-report")
async def get_compliance_report(
    campaign_id: str,
    period_days: int = 30,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get compliance report for a payment reminder campaign.

    Args:
        campaign_id: Payment reminder campaign ID
        period_days: Number of days for compliance report (default: 30)
        current_user: Authenticated user information

    Returns:
        Detailed compliance report
    """
    try:
        logger.info(f"Getting compliance report for campaign {campaign_id}")

        # Get compliance report from the service
        compliance_report = await enhanced_payment_reminder_service.get_compliance_report(
            campaign_id, period_days
        )

        return {
            "success": True,
            "data": compliance_report,
            "campaign_id": campaign_id,
            "period_days": period_days,
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting compliance report for campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get compliance report: {str(e)}"
        )

@router.post("/{campaign_id}/toggle")
async def toggle_campaign_status(
    campaign_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Toggle payment reminder campaign active/inactive status.

    Args:
        campaign_id: Payment reminder campaign ID
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
            "message": f"Payment reminder campaign status updated to {new_status}",
            "campaign_id": campaign_id,
            "status": new_status
        }

    except Exception as e:
        logger.error(f"Error toggling campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to toggle campaign status: {str(e)}"
        )

@router.delete("/{campaign_id}")
async def delete_payment_reminder(
    campaign_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Delete a payment reminder campaign.

    Args:
        campaign_id: Payment reminder campaign ID
        current_user: Authenticated user information

    Returns:
        Deletion confirmation
    """
    try:
        # TODO: Implement deletion of VAPI assistant, N8N workflow, demo page, etc.
        # For now, return mock response

        return {
            "success": True,
            "message": "Payment reminder campaign deleted successfully",
            "campaign_id": campaign_id
        }

    except Exception as e:
        logger.error(f"Error deleting payment reminder {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete payment reminder: {str(e)}"
        )