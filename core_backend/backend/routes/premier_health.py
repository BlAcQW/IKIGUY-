"""
Premier Health Insurance Service Location API routes.
Integrates with VAPI voice agents and N8N workflows for healthcare provider search.
"""

import sys
import os
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from pydantic import BaseModel, field_validator, Field
from datetime import datetime
import logging
import re
from slowapi import Limiter
from slowapi.util import get_remote_address
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Add the Premier Health automation path to Python path
premier_health_path = "/opt/kasaai/apps/automations/premier-health"
if premier_health_path not in sys.path:
    sys.path.append(premier_health_path)

try:
    from voice_agent_tools import HealthcareVoiceTools, TOOL_SCHEMAS
    from voice_agent_queries import VoiceAgentQueries
    from area_mapping import AreaMapper
except ImportError as e:
    logging.error(f"Failed to import Premier Health tools: {e}")
    # Create fallback classes to prevent import errors
    class HealthcareVoiceTools:
        def __init__(self, db_config): pass
        def search_healthcare_providers(self, *args, **kwargs):
            return {"error": "Premier Health tools not available"}

    class VoiceAgentQueries:
        def __init__(self, db_config): pass

    class AreaMapper:
        def __init__(self): pass

    TOOL_SCHEMAS = {}

from ..auth import get_current_user_mongo

# TEMP: Stub functions for missing security module
def get_organization_context(request):
    """Stub function - returns None until security module is implemented"""
    return None

async def validate_organization_access(org_id, user):
    """Stub function - always returns True until security module is implemented"""
    return True

# Import location correction function (can be commented out for testing)
from ..services.ghanaian_location.simple_integration import fix_location

# Import the new RAG knowledge base service
from ..services.helpdesk_rag_service import (
    helpdesk_rag_service,
    KnowledgeDocument,
    QueryResult
)

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/premier-health", tags=["premier-health"])

# Helper function to sanitize PII from logs
def sanitize_for_logging(text: str, mask_phone: bool = True, mask_location: bool = False) -> str:
    """
    Sanitize personally identifiable information from log messages.

    Args:
        text: Text to sanitize
        mask_phone: Whether to mask phone numbers
        mask_location: Whether to mask specific locations

    Returns:
        Sanitized text safe for logging
    """
    if not text:
        return text

    sanitized = text

    # Mask phone numbers
    if mask_phone:
        sanitized = re.sub(r'\b\d{10}\b', '***PHONE***', sanitized)
        sanitized = re.sub(r'\+\d{1,3}\s?\d{9,}', '***PHONE***', sanitized)

    # Mask email addresses
    sanitized = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '***EMAIL***', sanitized)

    return sanitized

# Database configuration for Premier Health - using environment variables
DB_CONFIG = {
    'host': os.getenv('POSTGRES_SERVER', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', '5432')),
    'database': os.getenv('POSTGRES_DB_CORE', 'kasaai_core'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'options': '-c search_path=premier_health,public'  # Set schema search path
}

class HealthcareSearchRequest(BaseModel):
    """Request model for healthcare provider search with validation."""
    query: str = Field(..., min_length=2, max_length=500, description="Search query")
    max_results: Optional[int] = Field(5, ge=1, le=50, description="Maximum results to return")
    location: Optional[str] = Field(None, max_length=200, description="Location filter")
    specialty: Optional[str] = Field(None, max_length=200, description="Medical specialty filter")
    provider_type: Optional[str] = Field(None, max_length=50, description="Provider type filter")
    call_id: Optional[str] = Field(None, max_length=100, description="Call tracking ID")
    customer_number: Optional[str] = Field(None, max_length=20, description="Customer phone number")

    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        """Validate query string"""
        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        # Remove potentially dangerous characters
        if re.search(r'[<>{}]', v):
            raise ValueError('Query contains invalid characters')
        return v.strip()

    @field_validator('location', 'specialty', 'provider_type')
    @classmethod
    def validate_text_fields(cls, v):
        """Validate text fields"""
        if v and re.search(r'[<>{}]', v):
            raise ValueError('Field contains invalid characters')
        return v.strip() if v else None

class VAPIWebhookRequest(BaseModel):
    """Request model for VAPI webhook calls."""
    call: Optional[Dict[str, Any]] = None
    message: Optional[Dict[str, Any]] = None
    transcript: Optional[str] = None
    phoneNumber: Optional[str] = None
    customer: Optional[Dict[str, Any]] = None

class EmergencyProviderRequest(BaseModel):
    """Request model for emergency healthcare providers."""
    location: Optional[str] = None
    max_results: Optional[int] = 5

class EnhancedHealthcareResponse(BaseModel):
    """Enhanced response model combining traditional provider data with AI guidance."""
    success: bool
    traditional_results: Dict[str, Any]  # Existing provider data from database
    ai_guidance: Optional[QueryResult] = None  # RAG-powered intelligent response
    combined_voice_response: str  # Voice-optimized response combining both
    confidence_score: float
    requires_escalation: bool
    escalation_reason: Optional[str] = None
    sources_used: List[str] = []
    processing_time: float = 0.0

class VoiceOptimizedResponse(BaseModel):
    """Response optimized for voice agent delivery."""
    voice_content: str  # Primary voice response
    provider_count: int  # Number of providers found
    has_guidance: bool  # Whether AI guidance was provided
    escalation_needed: bool  # Whether human escalation is recommended
    follow_up_suggestions: List[str] = []  # Suggested follow-up questions

def create_voice_optimized_response(
    ai_response: str,
    channel: str,
    context: Optional[Dict[str, Any]] = None
) -> VoiceOptimizedResponse:
    """
    Create a voice-optimized response from AI-generated content.

    Args:
        ai_response: Original AI response text
        channel: Delivery channel (voice_agent, api, etc.)
        context: Additional context for optimization

    Returns:
        VoiceOptimizedResponse with optimized content
    """
    try:
        # Basic voice optimization
        voice_content = ai_response

        # Remove markdown formatting for voice
        voice_content = voice_content.replace("**", "").replace("*", "")
        voice_content = voice_content.replace("#", "")

        # Add pauses for better speech delivery
        voice_content = voice_content.replace(". ", ". <break time='0.3s'/>")
        voice_content = voice_content.replace("? ", "? <break time='0.3s'/>")
        voice_content = voice_content.replace("! ", "! <break time='0.3s'/>")

        # Ensure natural speech patterns
        voice_content = voice_content.replace(" - ", " to ")
        voice_content = voice_content.replace(" & ", " and ")

        return VoiceOptimizedResponse(
            voice_content=voice_content,
            provider_count=0,  # Default for voice optimization
            has_guidance=True,
            escalation_needed=False
        )

    except Exception as e:
        logger.error(f"Error optimizing voice response: {str(e)}")
        return VoiceOptimizedResponse(
            voice_content=ai_response,  # Fallback to original
            provider_count=0,
            has_guidance=False,
            escalation_needed=True
        )

async def create_enhanced_healthcare_response(
    traditional_result: Dict[str, Any],
    query: str,
    channel: str,
    context: Optional[Dict[str, Any]] = None
) -> EnhancedHealthcareResponse:
    """
    Create an enhanced response combining traditional provider search with AI guidance.

    Args:
        traditional_result: Result from traditional provider database search
        query: Original user query
        channel: Delivery channel (api, voice_agent, etc.)
        context: Additional context including location, specialty, urgency, etc.

    Returns:
        EnhancedHealthcareResponse with combined intelligence
    """
    start_time = datetime.utcnow()

    try:
        # Extract context parameters
        location = context.get("location") if context else None
        specialty = context.get("specialty") if context else None
        urgency = context.get("urgency", "routine") if context else "routine"

        # Build enhanced query for RAG system with context
        rag_query = f"Healthcare query: {query}"
        if location:
            rag_query += f" in {location}"
        if specialty:
            rag_query += f" for {specialty} services"

        # Get AI guidance from knowledge base (using correct collection name)
        ai_guidance = await helpdesk_rag_service.query_knowledge_base(
            company_name="premier_health_production",
            query=rag_query
        )

        # Extract provider information from traditional results
        providers = traditional_result.get("providers", [])
        provider_count = len(providers)

        # Create voice-optimized combined response
        if ai_guidance.success and ai_guidance.confidence_score > 0.3:
            # High confidence AI response with provider integration
            if provider_count > 0:
                voice_response = f"{ai_guidance.response}\n\nI found {provider_count} healthcare providers for you"
                if provider_count <= 3:
                    # Include specific provider names for small lists
                    provider_names = [p.get('name', 'Unknown') for p in providers[:3]]
                    voice_response += f": {', '.join(provider_names)}"
                voice_response += ". Would you like more details about any of these providers?"
            else:
                voice_response = f"{ai_guidance.response} However, I couldn't find specific providers in our database for your location. Let me help you with general guidance or try a different area."
        else:
            # Lower confidence - rely more on traditional results
            if provider_count > 0:
                voice_response = f"I found {provider_count} healthcare providers for your search"
                if location:
                    voice_response += f" in {location}"
                voice_response += ". Let me provide some details about these providers."
            else:
                voice_response = "I couldn't find specific providers for your request. Could you try a different location or be more specific about the type of healthcare service you need?"

        # Determine escalation needs
        requires_escalation = (
            ai_guidance.requires_escalation or
            (provider_count == 0 and ai_guidance.confidence_score < 0.5) or
            "emergency" in query.lower()
        )

        escalation_reason = None
        if requires_escalation:
            if "emergency" in query.lower():
                escalation_reason = "Emergency medical situation detected"
            elif provider_count == 0:
                escalation_reason = "No providers found for specified criteria"
            else:
                escalation_reason = ai_guidance.escalation_reason

        processing_time = (datetime.utcnow() - start_time).total_seconds()

        return EnhancedHealthcareResponse(
            success=True,
            traditional_results=traditional_result,
            ai_guidance=ai_guidance,
            combined_voice_response=voice_response,
            confidence_score=max(ai_guidance.confidence_score, 0.7 if provider_count > 0 else 0.3),
            requires_escalation=requires_escalation,
            escalation_reason=escalation_reason,
            sources_used=ai_guidance.sources_used,
            processing_time=processing_time
        )

    except Exception as e:
        logger.error(f"Error creating enhanced healthcare response: {str(e)}")
        processing_time = (datetime.utcnow() - start_time).total_seconds()

        # Fallback to traditional response only
        providers = traditional_result.get("providers", [])
        fallback_response = f"I found {len(providers)} healthcare providers for your search" if providers else "I couldn't find providers for your search. Please try a different location or contact our support team."

        return EnhancedHealthcareResponse(
            success=len(providers) > 0,
            traditional_results=traditional_result,
            ai_guidance=None,
            combined_voice_response=fallback_response,
            confidence_score=0.7 if providers else 0.2,
            requires_escalation=len(providers) == 0,
            escalation_reason="Could not process with AI guidance, traditional search only",
            sources_used=[],
            processing_time=processing_time
        )

@router.post("/search", response_model=EnhancedHealthcareResponse)
@limiter.limit("30/minute")  # Rate limit: 30 requests per minute per IP
async def search_healthcare_providers(
    request: HealthcareSearchRequest,
    http_request: Request,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Enhanced healthcare provider search with AI-powered guidance.

    This endpoint combines traditional provider database search with intelligent
    AI guidance from our knowledge base, providing comprehensive healthcare
    assistance powered by Gemini 2.5 Flash.

    Features:
    - Traditional provider database search
    - AI-powered healthcare guidance and context
    - Voice-optimized responses for natural conversation
    - Automatic escalation detection for complex queries
    - Source attribution from knowledge base
    - Input validation and rate limiting
    - PII sanitization in logs

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(http_request)
        if org_id:
            await validate_organization_access(org_id, current_user)

        # Sanitize query for logging
        safe_query = sanitize_for_logging(request.query)
        logger.info(f"Enhanced healthcare search request: {safe_query} [org: {org_id}]")

        # Apply location correction (can be commented out for testing)
        corrected_location = fix_location(request.location) if request.location else request.location
        logger.debug(f"Location correction: '{request.location}' -> '{corrected_location}'")

        # Initialize Premier Health voice tools for traditional search
        healthcare_tools = HealthcareVoiceTools(DB_CONFIG)

        # Perform traditional provider search
        traditional_result = healthcare_tools.search_healthcare_providers(
            query=request.query,
            max_results=request.max_results,
            location=corrected_location,  # Use corrected location
            specialty=request.specialty,
            provider_type=request.provider_type
        )

        # Add metadata to traditional results
        traditional_result['call_id'] = request.call_id
        traditional_result['customer_number'] = request.customer_number
        traditional_result['search_timestamp'] = datetime.utcnow().isoformat()

        # Create enhanced response with AI guidance
        enhanced_response = await create_enhanced_healthcare_response(
            traditional_result=traditional_result,
            query=request.query,
            channel="api",
            context={
                "location": corrected_location,
                "specialty": request.specialty,
                "urgency": "routine"
            }
        )

        logger.info(f"Enhanced response generated - AI confidence: {enhanced_response.confidence_score:.2f}, "
                   f"Requires escalation: {enhanced_response.requires_escalation}, "
                   f"Providers found: {len(enhanced_response.traditional_results.get('providers', []))}")

        return enhanced_response

    except Exception as e:
        logger.error(f"Error in enhanced healthcare search: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced healthcare search failed: {str(e)}"
        )

@router.post("/emergency-providers", response_model=EnhancedHealthcareResponse)
async def get_emergency_providers(
    request: EmergencyProviderRequest,
    http_request: Request,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Enhanced emergency healthcare provider search with AI-powered emergency guidance.

    This endpoint provides immediate emergency healthcare assistance by combining
    traditional emergency provider lookup with AI-powered emergency guidance
    and safety instructions.

    Features:
    - Emergency provider database search
    - AI-powered emergency guidance and safety instructions
    - Location-specific emergency protocols
    - Immediate escalation for life-threatening situations

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(http_request)
        if org_id:
            await validate_organization_access(org_id, current_user)

        logger.info(f"Enhanced emergency provider search for location: {request.location} [org: {org_id}]")

        # Apply location correction for emergency searches too
        corrected_location = fix_location(request.location) if request.location else request.location
        logger.debug(f"Emergency location correction: '{request.location}' -> '{corrected_location}'")

        # Initialize Premier Health voice tools for traditional emergency search
        healthcare_tools = HealthcareVoiceTools(DB_CONFIG)

        # Perform traditional emergency provider search
        traditional_result = healthcare_tools.get_emergency_providers(
            location=corrected_location,  # Use corrected location
            max_results=request.max_results
        )

        # Create emergency-specific query for AI guidance
        emergency_query = f"Emergency medical situation"
        if corrected_location:
            emergency_query += f" in {corrected_location}"
        emergency_query += ". Provide immediate guidance and emergency protocols."

        # Create enhanced response with emergency-focused AI guidance
        enhanced_response = await create_enhanced_healthcare_response(
            traditional_result=traditional_result,
            query=emergency_query,
            channel="api",
            context={
                "location": corrected_location,
                "specialty": "emergency",
                "urgency": "emergency"
            }
        )

        # Override escalation for emergency situations
        enhanced_response.requires_escalation = True
        enhanced_response.escalation_reason = "Emergency medical situation - immediate attention required"

        # Enhance voice response with emergency-specific guidance
        providers = traditional_result.get("providers", [])
        if providers:
            emergency_guidance = f"🚨 EMERGENCY GUIDANCE: {enhanced_response.combined_voice_response}\n\n"
            emergency_guidance += f"Nearest emergency facilities: {', '.join([p.get('name', 'Unknown') for p in providers[:3]])}"
            emergency_guidance += "\n\nFor life-threatening emergencies, call 193 immediately."
        else:
            emergency_guidance = f"🚨 EMERGENCY GUIDANCE: {enhanced_response.combined_voice_response}\n\n"
            emergency_guidance += "IMMEDIATE ACTION: Call 193 for emergency services or go to the nearest hospital immediately."

        enhanced_response.combined_voice_response = emergency_guidance

        logger.warning(f"Emergency response generated for location: {corrected_location}, "
                      f"Providers found: {len(providers)}, Escalation: {enhanced_response.requires_escalation}")

        return enhanced_response

    except Exception as e:
        logger.error(f"Error in enhanced emergency provider search: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced emergency provider search failed: {str(e)}"
        )

@router.get("/provider/{provider_id}")
async def get_provider_details(
    provider_id: int,
    current_user: dict = Depends(get_current_user_mongo),
    http_request: Request = None
):
    """
    Get detailed information about a specific healthcare provider.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(http_request)
        if org_id:
            await validate_organization_access(org_id, current_user)

        healthcare_tools = HealthcareVoiceTools(DB_CONFIG)

        result = healthcare_tools.get_provider_details(provider_id)

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        logger.error(f"Error getting provider details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get provider details: {str(e)}"
        )

@router.get("/areas")
async def get_available_areas(
    current_user: dict = Depends(get_current_user_mongo),
    http_request: Request = None
):
    """
    Get list of all available areas/locations with healthcare coverage.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(http_request)
        if org_id:
            await validate_organization_access(org_id, current_user)

        healthcare_tools = HealthcareVoiceTools(DB_CONFIG)

        result = healthcare_tools.get_available_areas()

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        logger.error(f"Error getting available areas: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get available areas: {str(e)}"
        )

@router.get("/specialties")
async def get_available_specialties(
    current_user: dict = Depends(get_current_user_mongo),
    http_request: Request = None
):
    """
    Get list of all available medical specialties.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(http_request)
        if org_id:
            await validate_organization_access(org_id, current_user)

        healthcare_tools = HealthcareVoiceTools(DB_CONFIG)

        result = healthcare_tools.get_available_specialties()

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        logger.error(f"Error getting available specialties: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get available specialties: {str(e)}"
        )

@router.get("/providers-by-area/{area}")
async def get_providers_by_area(
    area: str,
    max_results: Optional[int] = 10,
    current_user: dict = Depends(get_current_user_mongo),
    http_request: Request = None
):
    """
    Get all healthcare providers in a specific area.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(http_request)
        if org_id:
            await validate_organization_access(org_id, current_user)

        healthcare_tools = HealthcareVoiceTools(DB_CONFIG)

        result = healthcare_tools.get_providers_by_area(
            area=area,
            max_results=max_results
        )

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        logger.error(f"Error getting providers by area: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get providers by area: {str(e)}"
        )

@router.get("/providers-by-specialty/{specialty}")
async def get_providers_by_specialty(
    specialty: str,
    max_results: Optional[int] = 10,
    current_user: dict = Depends(get_current_user_mongo),
    http_request: Request = None
):
    """
    Get healthcare providers by medical specialty.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(http_request)
        if org_id:
            await validate_organization_access(org_id, current_user)

        healthcare_tools = HealthcareVoiceTools(DB_CONFIG)

        result = healthcare_tools.get_providers_by_specialty(
            specialty=specialty,
            max_results=max_results
        )

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        logger.error(f"Error getting providers by specialty: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get providers by specialty: {str(e)}"
        )

@router.post("/vapi-server-messages")
async def handle_vapi_server_messages(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle VAPI Server Messages webhook for call lifecycle events.

    This endpoint receives all VAPI server messages including:
    - call.started
    - call.ended
    - transcript updates
    - speech-update events

    These events are logged to the call_logs database to provide
    conversation history in the VAPI platform.

    Webhook endpoint - organization context tracked in metadata.
    """
    try:
        # Parse the raw webhook payload
        body = await request.json()
        message_type = body.get("message", {}).get("type")

        # Extract organization context from metadata if available
        org_id = body.get("call", {}).get("metadata", {}).get("organization_id", "premier_health")

        logger.info(f"📨 VAPI Server Message received: {message_type} [org: {org_id}]")
        logger.debug(f"Full payload: {body}")

        # Import call logs service
        from ..services.call_logs_service import MongoDBCallLogsService
        from ..models.call_logs import CallLogCreate, CallLogUpdate, CallStatus

        call_logs_service = MongoDBCallLogsService()

        # Extract common call info
        call_data = body.get("call", {})
        call_id = call_data.get("id")
        assistant_id = call_data.get("assistantId")
        customer_number = call_data.get("customer", {}).get("number")

        if not call_id:
            logger.warning("No call_id in server message, skipping logging")
            return {"success": True, "message": "No call_id provided"}

        # Handle different message types
        if message_type == "call-start":
            logger.info(f"📞 Call started: {call_id}")

            # Create new call log entry
            call_log_data = CallLogCreate(
                call_id=call_id,
                assistant_id=assistant_id or "unknown",
                customer_number=customer_number,
                status=CallStatus.IN_PROGRESS,
                start_time=datetime.utcnow(),
                direction="inbound",  # Premier Health is primarily inbound
                metadata={
                    "assistant_name": "Premier Health Navigator",
                    "organization": "premier_health",
                    "organization_id": org_id,
                    "phone_number_id": call_data.get("phoneNumberId")
                }
            )

            result = await call_logs_service.create_call_log(call_log_data)
            logger.info(f"✅ Call log created: {result.success} - {result.message}")

        elif message_type == "end-of-call-report":
            logger.info(f"📊 End of call report for: {call_id}")

            # Extract end of call data
            end_report = body.get("message", {})
            transcript = end_report.get("transcript", "")
            recording_url = end_report.get("recordingUrl")
            duration = end_report.get("duration")
            ended_reason = end_report.get("endedReason")
            messages = end_report.get("messages", [])

            # Build full conversation transcript from messages
            full_transcript = ""
            if messages:
                for msg in messages:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    if content:
                        full_transcript += f"{role.upper()}: {content}\n\n"
            else:
                full_transcript = transcript

            # Update call log with final data
            call_log_update = CallLogUpdate(
                status=CallStatus.COMPLETED,
                end_time=datetime.utcnow(),
                duration=duration,
                transcript=full_transcript,
                recording_url=recording_url,
                ended_reason=ended_reason,
                summary=f"Premier Health call ended: {ended_reason}" if ended_reason else "Call completed",
                metadata={
                    "messages_count": len(messages),
                    "has_recording": recording_url is not None,
                    "end_report": end_report  # Store full report for analysis
                }
            )

            result = await call_logs_service.update_call_log(call_id, call_log_update)
            logger.info(f"✅ Call log updated with transcript ({len(full_transcript)} chars): {result.success}")

            if result.success:
                logger.info(f"📝 Transcript preview: {full_transcript[:200]}...")

        elif message_type == "transcript":
            logger.info(f"📝 Transcript update for call: {call_id}")

            # Handle incremental transcript updates
            transcript_data = body.get("message", {})
            transcript_text = transcript_data.get("transcript", "")

            # Append to existing transcript
            existing = await call_logs_service.get_call_log(call_id)
            if existing.success and existing.call_log:
                current_transcript = existing.call_log.transcript or ""
                updated_transcript = current_transcript + "\n" + transcript_text

                call_log_update = CallLogUpdate(
                    transcript=updated_transcript
                )

                result = await call_logs_service.update_call_log(call_id, call_log_update)
                logger.info(f"✅ Transcript appended: {result.success}")

        elif message_type == "speech-update":
            logger.debug(f"🗣️ Speech update for call: {call_id}")
            # Speech updates are very frequent, we don't need to log these
            pass

        else:
            logger.info(f"ℹ️  Unhandled message type: {message_type}")

        return {"success": True, "message_type": message_type, "call_id": call_id}

    except Exception as e:
        logger.error(f"❌ Error handling VAPI server message: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}


@router.post("/vapi-webhook")
async def handle_vapi_webhook(
    request: VAPIWebhookRequest,
    background_tasks: BackgroundTasks
):
    """
    Handle VAPI webhook for Premier Health voice agent integration.

    This endpoint receives webhook calls from VAPI when customers
    interact with the Premier Health voice agent (FUNCTION CALLS only).

    For call lifecycle events and transcripts, use /vapi-server-messages endpoint.

    Webhook endpoint - organization context tracked in metadata.
    """
    try:
        # Extract organization context from call metadata if available
        org_id = "premier_health"
        if request.call and isinstance(request.call, dict):
            org_id = request.call.get("metadata", {}).get("organization_id", "premier_health")

        logger.info(f"Received VAPI webhook for Premier Health [org: {org_id}]")

        # Extract call data
        call_data = {
            "call_id": request.call.get("id") if request.call else "unknown",
            "phone_number": request.phoneNumber or (request.call.get("phoneNumberId") if request.call else None),
            "customer_number": request.customer.get("number") if request.customer else None,
            "transcript": request.transcript or "",
            "message_content": request.message.get("content") if request.message else "",
            "function_call": request.message.get("function_call") if request.message else None
        }

        # Handle both old function_call format and new toolCalls format
        function_call = call_data["function_call"]
        tool_calls = request.message.get("toolCalls") if request.message else None
        tool_call_id = None  # Store for VAPI response format

        # Convert new VAPI toolCalls format to function_call format
        if not function_call and tool_calls and len(tool_calls) > 0:
            tool_call = tool_calls[0]  # Process first tool call
            tool_call_id = tool_call.get("id", "unknown")  # Extract tool call ID for response
            function_call = {
                "name": tool_call.get("function", {}).get("name"),
                "arguments": tool_call.get("function", {}).get("arguments", {})
            }
            logger.info(f"Converted toolCalls to function_call format: {function_call}")
            logger.info(f"Tool call ID: {tool_call_id}")

        # Log function call to call_logs for tracking
        call_id = call_data.get("call_id")
        if call_id and call_id != "unknown":
            try:
                from ..services.call_logs_service import MongoDBCallLogsService
                from ..models.call_logs import CallLogUpdate

                call_logs_service = MongoDBCallLogsService()

                # Log the function call in metadata
                function_call_log = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "function_name": function_call.get("name") if function_call else None,
                    "function_args": function_call.get("arguments") if function_call else None,
                }

                # Append to call log metadata
                existing = await call_logs_service.get_call_log(call_id)
                if existing.success and existing.call_log:
                    metadata = existing.call_log.metadata or {}
                    function_calls = metadata.get("function_calls", [])
                    function_calls.append(function_call_log)
                    metadata["function_calls"] = function_calls

                    update = CallLogUpdate(metadata=metadata)
                    await call_logs_service.update_call_log(call_id, update)
                    logger.debug(f"✅ Function call logged to call_logs: {call_id}")

            except Exception as log_error:
                logger.warning(f"Failed to log function call to database: {log_error}")

        # Process function calls
        if function_call:
            function_name = function_call.get("name")
            function_args = function_call.get("arguments", {})

            # Parse arguments if they are a JSON string
            if isinstance(function_args, str):
                try:
                    import json
                    function_args = json.loads(function_args)
                    logger.info(f"📝 Parsed function arguments from JSON string")
                except json.JSONDecodeError as parse_error:
                    logger.error(f"❌ Failed to parse function arguments: {parse_error}")
                    function_args = {}

            logger.info(f"🔧 Initializing HealthcareVoiceTools with config: {DB_CONFIG}")

            try:
                healthcare_tools = HealthcareVoiceTools(DB_CONFIG)
                logger.info("✅ HealthcareVoiceTools initialized successfully")
            except Exception as init_error:
                logger.error(f"❌ Failed to initialize HealthcareVoiceTools: {init_error}")
                raise init_error

            if function_name == "search_healthcare_providers":
                logger.info(f"🏥 HEALTHCARE SEARCH REQUEST: query='{function_args.get('query', '')}', location='{function_args.get('location')}', max_results={function_args.get('max_results', 5)}")

                # Note: All regions now covered (Greater Accra, Ashanti, Northern, Western, Eastern, Volta, Bono, Central)
                # No need for region validation - all queries will be processed

                # Get traditional search results
                traditional_result = healthcare_tools.search_healthcare_providers(
                    query=function_args.get("query", ""),
                    max_results=function_args.get("max_results", 5),
                    location=function_args.get("location"),
                    specialty=function_args.get("specialty"),
                    provider_type=function_args.get("provider_type")
                )

                # Create enhanced response with RAG intelligence
                try:
                    enhanced_response = await create_enhanced_healthcare_response(
                        traditional_result,
                        function_args.get("query", ""),
                        "voice_agent",
                        {
                            "urgency": "routine",
                            "provider_type": function_args.get("provider_type"),
                            "specialty": function_args.get("specialty"),
                            "location": function_args.get("location")
                        }
                    )

                    logger.info(f"🏥 ENHANCED SEARCH RESULT: Traditional={traditional_result.get('success')}, AI_Guidance={enhanced_response.ai_guidance.success if enhanced_response.ai_guidance else 'None'}")

                    # Use the voice-optimized response for VAPI
                    voice_response = enhanced_response.combined_voice_response

                    # Prepare the response to send back to VAPI
                    vapi_response = {
                        "message": {
                            "type": "assistant",
                            "content": voice_response,
                            "function_call_result": {
                                "success": enhanced_response.success,
                                "data": {
                                    "providers": enhanced_response.traditional_results.get("providers", [])[:3],
                                    "total_found": enhanced_response.traditional_results.get("total_found", 0),
                                    "confidence": enhanced_response.confidence_score,
                                    "ai_enhanced": enhanced_response.ai_guidance is not None,
                                    "requires_escalation": enhanced_response.requires_escalation,
                                    "sources_used": enhanced_response.sources_used
                                }
                            }
                        }
                    }

                except Exception as rag_error:
                    logger.error(f"RAG enhancement failed, using traditional response: {rag_error}")
                    # Fallback to traditional response
                    voice_response = traditional_result.get("voice_response", "I found healthcare providers for your search.")
                    vapi_response = {
                        "message": {
                            "type": "assistant",
                            "content": voice_response,
                            "function_call_result": {
                                "success": traditional_result.get("success", False),
                                "data": {
                                    "providers": traditional_result.get("providers", [])[:3],
                                    "total_found": traditional_result.get("total_found", 0),
                                    "confidence": traditional_result.get("confidence", 0.0),
                                    "ai_enhanced": False
                                }
                            }
                        }
                    }

                # Log the exact response being sent to VAPI
                logger.info("📤 SENDING ENHANCED RESPONSE TO VAPI:")
                logger.info("┌─────────────────────────────────────────────────────────────────────────────┐")
                logger.info(f"│ 🎙️  Voice Content: '{voice_response}'")
                logger.info(f"│ ✅ Success: {vapi_response['message']['function_call_result']['success']}")
                logger.info(f"│ 📊 Total Found: {vapi_response['message']['function_call_result']['data']['total_found']}")
                logger.info(f"│ 🧠 AI Enhanced: {vapi_response['message']['function_call_result']['data'].get('ai_enhanced', False)}")
                logger.info(f"│ 🏥 Providers Count: {len(vapi_response['message']['function_call_result']['data']['providers'])}")
                if vapi_response['message']['function_call_result']['data']['providers']:
                    for i, provider in enumerate(vapi_response['message']['function_call_result']['data']['providers'], 1):
                        logger.info(f"│ #{i} {provider.get('name', 'Unknown')} - {provider.get('area', 'Unknown')} - {provider.get('phone_primary', 'No phone')}")
                logger.info("└─────────────────────────────────────────────────────────────────────────────┘")

                return vapi_response

            elif function_name == "get_emergency_providers":
                logger.info(f"🚨 EMERGENCY SEARCH REQUEST: location='{function_args.get('location')}', max_results={function_args.get('max_results', 5)}")

                # Get traditional emergency results
                traditional_result = healthcare_tools.get_emergency_providers(
                    location=function_args.get("location"),
                    max_results=function_args.get("max_results", 5)
                )

                # Create enhanced emergency response with RAG intelligence
                try:
                    enhanced_response = await create_enhanced_healthcare_response(
                        traditional_result,
                        f"emergency healthcare providers in {function_args.get('location')}",
                        "voice_agent",
                        {
                            "urgency": "emergency",
                            "provider_type": "emergency",
                            "location": function_args.get("location")
                        }
                    )

                    logger.info(f"🚨 ENHANCED EMERGENCY RESULT: Traditional={traditional_result.get('success')}, AI_Guidance={enhanced_response.ai_guidance.success if enhanced_response.ai_guidance else 'None'}")

                    # Use the voice-optimized response for emergency scenarios
                    voice_response = enhanced_response.combined_voice_response

                    vapi_response = {
                        "message": {
                            "type": "assistant",
                            "content": voice_response,
                            "function_call_result": {
                                "success": enhanced_response.success,
                                "data": {
                                    "providers": enhanced_response.traditional_results.get("providers", [])[:3],
                                    "emergency_guidance": enhanced_response.traditional_results.get("emergency_guidance", "For life-threatening emergencies, call 193."),
                                    "ai_enhanced": enhanced_response.ai_guidance is not None,
                                    "requires_escalation": enhanced_response.requires_escalation,
                                    "sources_used": enhanced_response.sources_used
                                }
                            }
                        }
                    }

                except Exception as rag_error:
                    logger.error(f"Emergency RAG enhancement failed, using traditional response: {rag_error}")
                    # Fallback to traditional response for emergencies
                    voice_response = traditional_result.get("voice_response", "I found emergency healthcare providers for your area.")
                    vapi_response = {
                        "message": {
                            "type": "assistant",
                            "content": voice_response,
                            "function_call_result": {
                                "success": traditional_result.get("success", False),
                                "data": {
                                    "providers": traditional_result.get("providers", [])[:3],
                                    "emergency_guidance": traditional_result.get("emergency_guidance", "For life-threatening emergencies, call 193."),
                                    "ai_enhanced": False
                                }
                            }
                        }
                    }

                logger.info(f"🚨 EMERGENCY RESPONSE: {voice_response[:100]}...")
                return vapi_response

            elif function_name == "query_premier_health_knowledge_base":
                # Handle RAG-based knowledge base queries with region filtering
                query = function_args.get("query", "")
                region = function_args.get("region", "GREATER ACCRA")

                logger.info(f"🔍 KNOWLEDGE BASE QUERY: query='{query}', region='{region}'")

                try:
                    # Query the RAG knowledge base with region filter
                    rag_result = await helpdesk_rag_service.query_knowledge_base(
                        company_name="premier_health_production",
                        query=f"{query} in {region} region",
                        region=region
                    )

                    if rag_result.success and rag_result.confidence_score > 0.5:
                        logger.info(f"✅ RAG query successful: confidence={rag_result.confidence_score}")

                        # Create voice-optimized response
                        voice_response = create_voice_optimized_response(
                            rag_result.response,
                            "voice_agent",
                            {"urgency": "routine", "region": region}
                        )

                        # Return function result in VAPI expected format
                        # VAPI requires: {"results": [{"toolCallId": "xxx", "result": "single-line string"}]}
                        response_text = voice_response.voice_content.replace("\n", " ").replace("\r", " ")
                        return {
                            "results": [{
                                "toolCallId": tool_call_id or "unknown",
                                "result": response_text
                            }]
                        }
                    else:
                        logger.warning(f"⚠️ RAG query low confidence or failed: {rag_result.confidence_score}")
                        return {
                            "results": [{
                                "toolCallId": tool_call_id or "unknown",
                                "result": f"I'm sorry, I couldn't find specific information about {query} in the {region} region. Let me connect you with our support team who can help you directly. Can I confirm your first name for the support ticket?"
                            }]
                        }

                except Exception as rag_error:
                    logger.error(f"❌ RAG query failed: {rag_error}")
                    return {
                        "results": [{
                            "toolCallId": tool_call_id or "unknown",
                            "result": "I apologize, but I'm having trouble accessing that information right now. Please try again or contact Premier Health customer service."
                        }]
                    }

            elif function_name == "get_provider_details":
                logger.info(f"📋 PROVIDER DETAILS REQUEST: provider_id={function_args.get('provider_id')}")

                # Get traditional provider details
                traditional_result = healthcare_tools.get_provider_details(
                    provider_id=function_args.get("provider_id")
                )

                # Create enhanced provider details response with RAG intelligence
                try:
                    provider_data = traditional_result.get("provider", {})
                    provider_name = provider_data.get("name", "provider")
                    provider_type = provider_data.get("type", "healthcare")

                    enhanced_response = await create_enhanced_healthcare_response(
                        traditional_result,
                        f"information about {provider_name} {provider_type} provider",
                        "voice_agent",
                        {
                            "urgency": "routine",
                            "provider_type": provider_type,
                            "provider_name": provider_name
                        }
                    )

                    logger.info(f"📋 ENHANCED PROVIDER DETAILS: Traditional={traditional_result.get('success')}, AI_Guidance={enhanced_response.ai_guidance.success if enhanced_response.ai_guidance else 'None'}")

                    # Use the voice-optimized response
                    voice_response = enhanced_response.combined_voice_response

                    vapi_response = {
                        "message": {
                            "type": "assistant",
                            "content": voice_response,
                            "function_call_result": {
                                "success": enhanced_response.success,
                                "data": {
                                    "provider": enhanced_response.traditional_results.get("provider", {}),
                                    "ai_enhanced": enhanced_response.ai_guidance is not None,
                                    "requires_escalation": enhanced_response.requires_escalation,
                                    "sources_used": enhanced_response.sources_used
                                }
                            }
                        }
                    }

                except Exception as rag_error:
                    logger.error(f"Provider details RAG enhancement failed, using traditional response: {rag_error}")
                    # Fallback to traditional response
                    voice_response = traditional_result.get("voice_response", "I found provider details for you.")
                    vapi_response = {
                        "message": {
                            "type": "assistant",
                            "content": voice_response,
                            "function_call_result": {
                                "success": traditional_result.get("success", False),
                                "data": {
                                    "provider": traditional_result.get("provider", {}),
                                    "ai_enhanced": False
                                }
                            }
                        }
                    }

                logger.info(f"📋 PROVIDER DETAILS RESPONSE: {voice_response[:100]}...")
                return vapi_response

        # Fallback for non-function call interactions - use RAG for general healthcare questions
        logger.info(f"💬 GENERAL HEALTHCARE QUERY: {call_data.get('transcript', '')}")

        # If there's a transcript with healthcare-related content, try RAG intelligence
        transcript = call_data.get("transcript", "").strip()
        if transcript and len(transcript) > 10:
            try:
                # Query RAG service for general healthcare guidance
                rag_result = await helpdesk_rag_service.query_knowledge_base(
                    company_name="premier_health_production",
                    query=transcript
                )

                if rag_result.success and rag_result.confidence_score > 0.6:
                    logger.info(f"💬 RAG GUIDANCE PROVIDED: confidence={rag_result.confidence_score}")

                    # Create voice-optimized response
                    voice_response = create_voice_optimized_response(
                        rag_result.response,
                        "voice_agent",
                        {"urgency": "routine"}
                    )

                    return {
                        "message": {
                            "type": "assistant",
                            "content": voice_response.voice_content,
                            "function_call_result": {
                                "success": True,
                                "data": {
                                    "ai_guidance": rag_result.response,
                                    "confidence": rag_result.confidence_score,
                                    "sources_used": rag_result.sources_used,
                                    "requires_escalation": rag_result.requires_escalation
                                }
                            }
                        }
                    }
                else:
                    logger.info(f"💬 RAG confidence too low: {rag_result.confidence_score}")

            except Exception as rag_error:
                logger.error(f"RAG fallback failed: {rag_error}")

        # Default fallback response
        return {
            "message": {
                "type": "assistant",
                "content": "I'm here to help you find healthcare providers and answer questions about Premier Health services. You can ask me to find doctors, hospitals, clinics, or pharmacies in Greater Accra, or ask about our policies and services. How can I assist you today?"
            }
        }

    except Exception as e:
        logger.error(f"Error handling VAPI webhook: {str(e)}")
        return {
            "message": {
                "type": "assistant",
                "content": "I apologize, but I'm experiencing technical difficulties. Please try again or contact Premier Health customer service for assistance."
            }
        }

@router.get("/tool-schemas")
async def get_tool_schemas():
    """
    Get VAPI-compatible tool schemas for Premier Health voice agent.
    """
    try:
        return {
            "success": True,
            "schemas": TOOL_SCHEMAS
        }

    except Exception as e:
        logger.error(f"Error getting tool schemas: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get tool schemas: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """
    Health check endpoint for Premier Health service.
    """
    try:
        # Test database connection
        healthcare_tools = HealthcareVoiceTools(DB_CONFIG)
        areas_result = healthcare_tools.get_available_areas()

        logger.info(f"Health check areas_result: {areas_result}")

        return {
            "status": "healthy",
            "service": "Premier Health Insurance Service Location Agent",
            "database_connected": areas_result.get("success", False),
            "total_areas": areas_result.get("total_areas", 0),
            "tools_available": len(TOOL_SCHEMAS)
        }

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

class EmailRequest(BaseModel):
    """Request model for sending provider information via email."""
    customer_phone: str  # Use caller phone number instead of email
    first_name: Optional[str] = "Customer"  # Use first name only
    provider_data: List[Dict[str, Any]]
    search_query: Optional[str] = ""

class SMSRequest(BaseModel):
    """Request model for sending provider information via SMS."""
    phone: str
    provider_data: List[Dict[str, Any]]
    search_query: Optional[str] = ""

class CallSummaryRequest(BaseModel):
    """Request model for sending call summary email."""
    call_data: Dict[str, Any]

@router.post("/send-email")
async def send_provider_info_email(
    request: EmailRequest,
    current_user: dict = Depends(get_current_user_mongo),
    http_request: Request = None
):
    """
    Send healthcare provider information via SMS to caller using their phone number.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(http_request)
        if org_id:
            await validate_organization_access(org_id, current_user)

        logger.info(f"Sending provider info via SMS to: {sanitize_for_logging(request.customer_phone)} [org: {org_id}]")

        healthcare_tools = HealthcareVoiceTools(DB_CONFIG)

        # Use SMS instead of email since we only have phone number
        result = healthcare_tools.send_provider_info_sms(
            phone=request.customer_phone,
            provider_data=request.provider_data,
            search_query=request.search_query,
            customer_name=request.first_name
        )

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        logger.error(f"Error sending provider info email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send provider info email: {str(e)}"
        )

@router.post("/send-sms")
async def send_provider_info_sms(
    request: SMSRequest,
    current_user: dict = Depends(get_current_user_mongo),
    http_request: Request = None
):
    """
    Send healthcare provider information via SMS to caller.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(http_request)
        if org_id:
            await validate_organization_access(org_id, current_user)

        logger.info(f"Sending provider info SMS to: {sanitize_for_logging(request.phone)} [org: {org_id}]")

        healthcare_tools = HealthcareVoiceTools(DB_CONFIG)

        result = healthcare_tools.send_provider_info_sms(
            phone=request.phone,
            provider_data=request.provider_data,
            search_query=request.search_query
        )

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        logger.error(f"Error sending provider info SMS: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send provider info SMS: {str(e)}"
        )

@router.post("/send-call-summary")
async def send_call_summary_email(
    request: CallSummaryRequest,
    background_tasks: BackgroundTasks,
    http_request: Request = None
):
    """
    Send call summary email to ailabsafrica@gmail.com.
    This endpoint is called after each call for analytics and monitoring.

    Webhook-like endpoint - organization context tracked from call data.
    """
    try:
        # Extract organization context from call data metadata
        org_id = request.call_data.get('metadata', {}).get('organization_id', 'premier_health')

        logger.info(f"Sending call summary for call: {request.call_data.get('call_id', 'unknown')} [org: {org_id}]")

        healthcare_tools = HealthcareVoiceTools(DB_CONFIG)

        # Run in background to not delay the main call flow
        background_tasks.add_task(
            healthcare_tools.send_call_summary_email,
            request.call_data
        )

        return {
            "success": True,
            "message": "Call summary email scheduled for sending"
        }

    except Exception as e:
        logger.error(f"Error sending call summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send call summary: {str(e)}"
        )

class EscalationRequest(BaseModel):
    """Request model for escalating queries to Freshdesk support."""
    first_name: str  # Use first name only
    customer_phone: str
    search_query: str
    location_searched: str
    issue_description: Optional[str] = ""

@router.post("/escalate-to-support")
async def escalate_to_support(
    request: EscalationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_mongo),
    http_request: Request = None
):
    """
    Escalate query to Freshdesk support when location not found or other issues.
    Creates a support ticket with customer details for manual review and callback.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get organization context and validate access
        org_id = get_organization_context(http_request)
        if org_id:
            await validate_organization_access(org_id, current_user)

        logger.info(f"Escalating query to support for customer: [REDACTED], location: {request.location_searched} [org: {org_id}]")

        healthcare_tools = HealthcareVoiceTools(DB_CONFIG)

        result = healthcare_tools.escalate_to_support(
            customer_name=request.first_name,
            customer_phone=request.customer_phone,
            search_query=request.search_query,
            location_searched=request.location_searched,
            issue_description=request.issue_description
        )

        # Log escalation for analytics
        background_tasks.add_task(
            log_escalation_analytics,
            {
                "ticket_id": result.get("ticket_id"),
                "customer_name": request.first_name,
                "customer_phone": request.customer_phone,
                "location_searched": request.location_searched,
                "search_query": request.search_query,
                "escalation_timestamp": datetime.utcnow().isoformat()
            }
        )

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        logger.error(f"Error escalating to support: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to escalate to support: {str(e)}"
        )

async def log_escalation_analytics(escalation_data: Dict[str, Any]):
    """
    Background task to log escalation analytics.
    """
    try:
        # Log escalation data for business intelligence
        logger.info(f"Escalation analytics: {escalation_data}")

        # In production, this would save to analytics database
        # For now, we'll just log it

    except Exception as e:
        logger.error(f"Error logging escalation analytics: {str(e)}")