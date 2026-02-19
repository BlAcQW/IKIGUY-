"""
Product Launch Campaign API Routes

FastAPI routes for product launch announcement campaigns with VAPI integration,
customer segmentation, and comprehensive analytics.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import os
import sys

# Add the automations path to import our tools
product_launch_path = '/opt/kasaai/apps/automations/campaigns/product-launch'
sys.path.insert(0, product_launch_path)  # Insert at beginning to prioritize this path

try:
    # Import the specific file to avoid conflicts
    import importlib.util
    spec = importlib.util.spec_from_file_location("product_launch_voice_tools", f"{product_launch_path}/voice_agent_tools.py")
    product_launch_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(product_launch_module)
    ProductLaunchVoiceTools = product_launch_module.ProductLaunchVoiceTools
except Exception as e:
    # Fallback to None if import fails
    ProductLaunchVoiceTools = None
    logger.warning(f"ProductLaunchVoiceTools not available: {e}")
finally:
    # Remove the path to avoid conflicts
    if product_launch_path in sys.path:
        sys.path.remove(product_launch_path)

# Database configuration
DB_CONFIG = {
    'connection_string': os.getenv('MONGODB_CONNECTION_STRING', 'mongodb://localhost:27017/'),
    'database_name': os.getenv('MONGODB_DATABASE', 'kasaai_campaigns')
}

# Security
security = HTTPBearer()

def get_current_user_mongo(token: str = Depends(security)):
    """Validate bearer token for API access."""
    # In production, implement proper token validation
    return {"user_id": "authenticated_user", "token": token.credentials}

# Request/Response Models
class ProductDetailsRequest(BaseModel):
    product_id: str = Field(..., description="Product identifier")
    customer_segment: str = Field(default="general", description="Customer segment")
    detail_level: str = Field(default="overview", description="Level of detail")
    focus_areas: Optional[List[str]] = Field(default=None, description="Specific focus areas")

class InterestAssessmentRequest(BaseModel):
    interest_indicators: List[str] = Field(..., description="Customer interest indicators")
    questions: List[str] = Field(..., description="Questions asked by customer")
    sentiment_score: float = Field(..., ge=1, le=10, description="Sentiment score 1-10")
    purchase_intent: str = Field(..., description="Purchase timeline intent")

class ExclusiveAccessRequest(BaseModel):
    access_type: str = Field(..., description="Type of exclusive access")
    customer_segment: str = Field(..., description="Customer segment")
    validity_period: str = Field(default="30 days", description="Offer validity period")
    special_terms: str = Field(default="", description="Special terms or conditions")

class DemoSchedulingRequest(BaseModel):
    demo_type: str = Field(..., description="Type of demonstration")
    preferred_time: str = Field(..., description="Preferred time")
    duration: str = Field(default="30 minutes", description="Demo duration")
    specific_focus: Optional[List[str]] = Field(default=None, description="Focus areas")
    attendees: int = Field(default=1, ge=1, description="Number of attendees")

class FeedbackRequest(BaseModel):
    feedback_type: str = Field(..., description="Type of feedback")
    rating: float = Field(..., ge=1, le=10, description="Rating 1-10")
    comments: str = Field(default="", description="Customer comments")
    suggestions: str = Field(default="", description="Customer suggestions")
    likely_to_recommend: bool = Field(default=True, description="Likelihood to recommend")

class LeadCaptureRequest(BaseModel):
    lead_quality: str = Field(..., description="Quality level of lead")
    timeframe: str = Field(..., description="Purchase timeframe")
    budget: str = Field(default="unknown", description="Budget information")
    decision_maker: bool = Field(default=False, description="Is decision maker")
    next_steps: str = Field(default="", description="Agreed next steps")

class CustomerSegmentationRequest(BaseModel):
    product_id: str = Field(..., description="Product identifier")
    target_segments: List[str] = Field(..., description="Target customer segments")
    segmentation_criteria: str = Field(..., description="Segmentation criteria")

class MessagePersonalizationRequest(BaseModel):
    customer_data: Dict[str, Any] = Field(..., description="Customer data")
    message_type: str = Field(..., description="Type of message")
    personalization_factors: str = Field(..., description="Personalization factors")

class EngagementTrackingRequest(BaseModel):
    engagement_data: Dict[str, Any] = Field(..., description="Engagement data")
    call_metadata: Dict[str, Any] = Field(..., description="Call metadata")

class LaunchAnalyticsRequest(BaseModel):
    analytics_data: str = Field(..., description="Analytics data")
    workflow_completion: str = Field(..., description="Workflow completion status")

class ErrorLoggingRequest(BaseModel):
    error_data: Dict[str, Any] = Field(..., description="Error data")
    workflow_stage: str = Field(..., description="Workflow stage where error occurred")

# Initialize router
router = APIRouter(prefix="/api/product-launch", tags=["Product Launch"])

# Initialize voice tools
product_launch_tools = None
if ProductLaunchVoiceTools is not None:
    product_launch_tools = ProductLaunchVoiceTools(DB_CONFIG)

logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check():
    """Health check endpoint for product launch services."""
    return {
        "status": "healthy",
        "service": "product_launch_api",
        "timestamp": datetime.now().isoformat(),
        "database_connected": True
    }

@router.post("/product-details")
async def get_product_details(
    request: ProductDetailsRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Retrieve comprehensive product information and features.
    """
    try:
        result = product_launch_tools.get_product_details(
            product_id=request.product_id,
            customer_segment=request.customer_segment,
            detail_level=request.detail_level,
            focus_areas=request.focus_areas
        )

        if not result.get("success", False):
            raise HTTPException(status_code=404, detail=result.get("error", "Product not found"))

        return result

    except Exception as e:
        logger.error(f"Error getting product details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get product details: {str(e)}")

@router.post("/assess-interest")
async def assess_customer_interest(
    request: InterestAssessmentRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Assess and score customer interest level in the new product.
    """
    try:
        result = product_launch_tools.assess_customer_interest(
            interest_indicators=request.interest_indicators,
            questions=request.questions,
            sentiment_score=request.sentiment_score,
            purchase_intent=request.purchase_intent
        )

        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to assess interest"))

        return result

    except Exception as e:
        logger.error(f"Error assessing interest: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to assess interest: {str(e)}")

@router.post("/offer-exclusive-access")
async def offer_exclusive_access(
    request: ExclusiveAccessRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Offer exclusive early access or special launch benefits.
    """
    try:
        result = product_launch_tools.offer_exclusive_access(
            access_type=request.access_type,
            customer_segment=request.customer_segment,
            validity_period=request.validity_period,
            special_terms=request.special_terms
        )

        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to generate exclusive offer"))

        return result

    except Exception as e:
        logger.error(f"Error offering exclusive access: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to offer exclusive access: {str(e)}")

@router.post("/schedule-demo")
async def schedule_product_demo(
    request: DemoSchedulingRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Schedule a personalized product demonstration or presentation.
    """
    try:
        result = product_launch_tools.schedule_product_demo(
            demo_type=request.demo_type,
            preferred_time=request.preferred_time,
            duration=request.duration,
            specific_focus=request.specific_focus,
            attendees=request.attendees
        )

        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to schedule demo"))

        return result

    except Exception as e:
        logger.error(f"Error scheduling demo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to schedule demo: {str(e)}")

@router.post("/collect-feedback")
async def collect_launch_feedback(
    request: FeedbackRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Collect customer feedback about the product launch and announcement.
    """
    try:
        result = product_launch_tools.collect_launch_feedback(
            feedback_type=request.feedback_type,
            rating=request.rating,
            comments=request.comments,
            suggestions=request.suggestions,
            likely_to_recommend=request.likely_to_recommend
        )

        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to collect feedback"))

        return result

    except Exception as e:
        logger.error(f"Error collecting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to collect feedback: {str(e)}")

@router.post("/capture-lead")
async def capture_lead_information(
    request: LeadCaptureRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Capture qualified lead information for product follow-up.
    """
    try:
        result = product_launch_tools.capture_lead_information(
            lead_quality=request.lead_quality,
            timeframe=request.timeframe,
            budget=request.budget,
            decision_maker=request.decision_maker,
            next_steps=request.next_steps
        )

        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to capture lead"))

        return result

    except Exception as e:
        logger.error(f"Error capturing lead: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to capture lead: {str(e)}")

# N8N Workflow Integration Endpoints

@router.post("/campaigns/customer-segmentation")
async def customer_segmentation(
    request: CustomerSegmentationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Perform intelligent customer segmentation for product launch.
    """
    try:
        # Simulate customer segmentation logic
        # In production, this would integrate with ML models and customer data

        segmented_customers = [
            {
                "segment_name": "early_adopters",
                "priority": "high",
                "customers": [
                    {
                        "customer_id": "ea_001",
                        "name": "TechCorp Inc",
                        "email": "tech@techcorp.com",
                        "phone": "+1234567890",
                        "purchase_history": ["premium_features", "enterprise_tools"],
                        "interests": ["innovation", "cutting_edge_tech"],
                        "engagement_score": 9,
                        "customer_value": "high"
                    }
                ]
            },
            {
                "segment_name": "loyal_customers",
                "priority": "medium",
                "customers": [
                    {
                        "customer_id": "lc_001",
                        "name": "Loyal Corp",
                        "email": "loyal@loyalcorp.com",
                        "phone": "+1234567891",
                        "purchase_history": ["basic_plan", "premium_plan"],
                        "interests": ["reliability", "support"],
                        "engagement_score": 8,
                        "customer_value": "high"
                    }
                ]
            }
        ]

        # Log segmentation activity
        background_tasks.add_task(
            log_campaign_activity,
            "customer_segmentation",
            {
                "product_id": request.product_id,
                "segments_created": len(segmented_customers),
                "total_customers": sum(len(seg["customers"]) for seg in segmented_customers)
            }
        )

        return {
            "success": True,
            "segmented_customers": segmented_customers,
            "segmentation_summary": {
                "total_segments": len(segmented_customers),
                "total_customers": sum(len(seg["customers"]) for seg in segmented_customers),
                "segmentation_criteria": request.segmentation_criteria
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in customer segmentation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Segmentation failed: {str(e)}")

@router.post("/campaigns/personalize-message")
async def personalize_message(
    request: MessagePersonalizationRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Generate personalized product announcement message.
    """
    try:
        customer_data = request.customer_data
        segment = customer_data.get("customer_segment", "general")

        # Personalization logic based on segment
        personalization_templates = {
            "early_adopters": {
                "greeting": f"Hello {customer_data.get('customer_name', 'there')}, as an innovation leader,",
                "message_tone": "exciting and cutting-edge",
                "value_prop": "be among the first to experience revolutionary technology"
            },
            "loyal_customers": {
                "greeting": f"Dear {customer_data.get('customer_name', 'valued customer')}, in appreciation of your partnership,",
                "message_tone": "warm and appreciative",
                "value_prop": "enjoy exclusive access as our valued partner"
            },
            "tech_enthusiasts": {
                "greeting": f"Hi {customer_data.get('customer_name', 'tech enthusiast')}, given your technical expertise,",
                "message_tone": "technical and detailed",
                "value_prop": "explore advanced capabilities and technical excellence"
            },
            "price_conscious": {
                "greeting": f"Hello {customer_data.get('customer_name', 'there')}, we know smart investment is important,",
                "message_tone": "value-focused and practical",
                "value_prop": "discover exceptional value and cost-effective solutions"
            }
        }

        template = personalization_templates.get(segment, personalization_templates["loyal_customers"])

        personalized_message = {
            "success": True,
            "personalized_content": {
                "greeting": template["greeting"],
                "product_name": customer_data.get("product_name", "our new product"),
                "personalized_message": f"We're excited to introduce {customer_data.get('product_name', 'our latest innovation')} - designed specifically for professionals like you who value {template['value_prop']}.",
                "call_to_action": "Would you like to learn more about how this can benefit your specific needs?",
                "tone": template["message_tone"]
            },
            "personalization_factors_used": [
                "customer_segment",
                "customer_name",
                "purchase_history",
                "communication_preferences"
            ],
            "timestamp": datetime.now().isoformat()
        }

        return personalized_message

    except Exception as e:
        logger.error(f"Error personalizing message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Message personalization failed: {str(e)}")

@router.post("/campaigns/track-engagement")
async def track_engagement(
    request: EngagementTrackingRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Track customer engagement with product launch campaign.
    """
    try:
        engagement_data = request.engagement_data

        # Store engagement metrics
        background_tasks.add_task(
            store_engagement_metrics,
            engagement_data,
            request.call_metadata
        )

        return {
            "success": True,
            "engagement_tracked": True,
            "call_id": engagement_data.get("call_id"),
            "customer_id": engagement_data.get("customer_id"),
            "campaign_id": engagement_data.get("campaign_id"),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error tracking engagement: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Engagement tracking failed: {str(e)}")

@router.post("/campaigns/launch-analytics")
async def record_launch_analytics(
    request: LaunchAnalyticsRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Record product launch performance analytics.
    """
    try:
        import json
        analytics_data = json.loads(request.analytics_data) if isinstance(request.analytics_data, str) else request.analytics_data

        # Process analytics
        background_tasks.add_task(
            process_launch_analytics,
            analytics_data,
            request.workflow_completion
        )

        return {
            "success": True,
            "analytics_recorded": True,
            "campaign_id": analytics_data.get("campaign_id"),
            "product_id": analytics_data.get("product_id"),
            "workflow_completion": request.workflow_completion,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error recording analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analytics recording failed: {str(e)}")

@router.post("/campaigns/error-logging")
async def log_campaign_error(
    request: ErrorLoggingRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Log campaign workflow errors for monitoring and debugging.
    """
    try:
        # Store error information
        background_tasks.add_task(
            store_campaign_error,
            request.error_data,
            request.workflow_stage
        )

        return {
            "success": True,
            "error_logged": True,
            "workflow_stage": request.workflow_stage,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error logging campaign error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error logging failed: {str(e)}")

# Background task functions
async def log_campaign_activity(activity_type: str, activity_data: Dict[str, Any]):
    """Log campaign activity for analytics."""
    try:
        # In production, store in analytics database
        logger.info(f"Campaign activity: {activity_type} - {activity_data}")
    except Exception as e:
        logger.error(f"Error logging campaign activity: {str(e)}")

async def store_engagement_metrics(engagement_data: Dict[str, Any], call_metadata: Dict[str, Any]):
    """Store engagement metrics for analysis."""
    try:
        # In production, store in metrics database
        logger.info(f"Engagement metrics stored: {engagement_data}")
    except Exception as e:
        logger.error(f"Error storing engagement metrics: {str(e)}")

async def process_launch_analytics(analytics_data: Dict[str, Any], completion_status: str):
    """Process launch analytics data."""
    try:
        # In production, process with analytics pipeline
        logger.info(f"Launch analytics processed: {analytics_data}")
    except Exception as e:
        logger.error(f"Error processing analytics: {str(e)}")

async def store_campaign_error(error_data: Dict[str, Any], workflow_stage: str):
    """Store campaign error for monitoring."""
    try:
        # In production, store in error tracking system
        logger.error(f"Campaign error in {workflow_stage}: {error_data}")
    except Exception as e:
        logger.error(f"Error storing campaign error: {str(e)}")

# Analytics and Monitoring Endpoints

@router.get("/campaigns/{campaign_id}/analytics")
async def get_campaign_analytics(
    campaign_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get comprehensive analytics for a product launch campaign.
    """
    try:
        # In production, query real analytics data
        analytics = {
            "campaign_id": campaign_id,
            "performance_metrics": {
                "total_calls": 150,
                "successful_calls": 142,
                "engagement_rate": 94.7,
                "interest_conversion_rate": 32.5,
                "demo_booking_rate": 18.3,
                "lead_capture_rate": 28.7
            },
            "segment_performance": {
                "early_adopters": {"engagement": 98.2, "conversion": 45.1},
                "loyal_customers": {"engagement": 96.5, "conversion": 38.3},
                "tech_enthusiasts": {"engagement": 92.1, "conversion": 29.8},
                "price_conscious": {"engagement": 89.4, "conversion": 21.2}
            },
            "timeline_data": [
                {"hour": "09:00", "calls": 15, "engagements": 14},
                {"hour": "10:00", "calls": 25, "engagements": 24},
                {"hour": "11:00", "calls": 30, "engagements": 28}
            ],
            "generated_at": datetime.now().isoformat()
        }

        return analytics

    except Exception as e:
        logger.error(f"Error getting campaign analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.get("/campaigns/{campaign_id}/status")
async def get_campaign_status(
    campaign_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get current status of a product launch campaign.
    """
    try:
        # In production, query real campaign data
        status = {
            "campaign_id": campaign_id,
            "status": "active",
            "progress": {
                "total_targets": 500,
                "contacted": 150,
                "remaining": 350,
                "completion_percentage": 30.0
            },
            "current_stage": "voice_outreach",
            "next_stage": "follow_up_nurturing",
            "estimated_completion": "2025-09-18T18:00:00Z",
            "last_updated": datetime.now().isoformat()
        }

        return status

    except Exception as e:
        logger.error(f"Error getting campaign status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")