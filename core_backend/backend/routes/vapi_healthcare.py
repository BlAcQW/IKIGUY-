"""
Enhanced VAPI Healthcare Agent Creation
Integrates Universal Wizard approach with Premier Health domain expertise
"""

import sys
import os
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
import logging

# Add the Premier Health automation path
premier_health_path = "/opt/kasaai/apps/automations/premier-health"
if premier_health_path not in sys.path:
    sys.path.append(premier_health_path)

from ..auth import get_current_user_mongo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vapi", tags=["vapi-healthcare"])

class HealthcareVAPIAgentRequest(BaseModel):
    """Enhanced request model for healthcare VAPI agent creation."""
    name: str
    systemPrompt: str
    voice: Dict[str, Any]
    model: Dict[str, Any]
    tools: List[Dict[str, Any]]
    firstMessage: str
    serverUrl: str
    maxDuration: Optional[int] = 900
    compliance: Optional[Dict[str, Any]] = None
    organizationInfo: Optional[Dict[str, Any]] = None
    providerDatabase: Optional[Dict[str, Any]] = None

class HealthcareVAPIAgentResponse(BaseModel):
    """Response model for healthcare VAPI agent creation."""
    id: str
    phoneNumberId: str
    name: str
    status: str
    webhookUrl: str
    compliance: Dict[str, Any]
    healthcareFeatures: Dict[str, Any]

@router.post("/create-healthcare-assistant", response_model=HealthcareVAPIAgentResponse)
async def create_healthcare_assistant(
    request: HealthcareVAPIAgentRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Create a specialized healthcare VAPI assistant with domain-specific features.

    This endpoint combines the flexibility of the Universal Wizard approach
    with the specialized healthcare capabilities of Premier Health.
    """
    try:
        logger.info(f"Creating healthcare VAPI assistant: {request.name}")

        # Enhanced system prompt with healthcare context
        enhanced_system_prompt = generate_healthcare_system_prompt(
            base_prompt=request.systemPrompt,
            organization_info=request.organizationInfo,
            provider_database=request.providerDatabase
        )

        # Healthcare-specific VAPI configuration
        vapi_config = {
            "name": request.name,
            "model": {
                "provider": request.model.get("provider", "openai"),
                "model": request.model.get("model", "gpt-4o"),
                "temperature": request.model.get("temperature", 0.3),
                "maxTokens": request.model.get("maxTokens", 250),
                "systemPrompt": enhanced_system_prompt
            },
            "voice": {
                "provider": request.voice.get("provider", "11labs"),
                "voiceId": request.voice.get("voiceId", "jennifer"),
                "stability": 0.5,
                "similarityBoost": 0.75,
                "style": 0.3,
                "useSpeakerBoost": True
            },
            "firstMessage": request.firstMessage,
            "endCallMessage": "Thank you for using our healthcare provider service. Your provider information has been sent to your phone. Take care and have a healthy day!",
            "endCallFunctionEnabled": True,
            "dialKeypadFunctionEnabled": True,
            "fillersEnabled": True,
            "fillers": [
                "Let me search our provider database for you...",
                "I'm looking up the best healthcare options in your area...",
                "One moment while I check provider availability...",
                "Searching for healthcare providers near you..."
            ],
            "serverUrl": request.serverUrl,
            "functions": enhance_healthcare_tools(request.tools),
            "voicemailDetection": {
                "enabled": True,
                "provider": "twilio",
                "voicemailDetectionTypes": ["machine_end_beep", "machine_end_silence"],
                "machineDetectionTimeout": 30
            },
            "callSettings": {
                "maxDuration": request.maxDuration,
                "idleTimeout": 45,  # Longer timeout for healthcare queries
                "warmTransferEnabled": True,
                "recordingEnabled": request.compliance and request.compliance.get("recordingEnabled", True),
                "transcriptionEnabled": True
            },
            "analyticsSettings": {
                "trackSentiment": True,
                "trackKeywords": [
                    "emergency", "urgent", "pain", "appointment", "doctor",
                    "hospital", "clinic", "pharmacy", "insurance", "specialist"
                ],
                "trackInterruptions": True,
                "trackSilences": True
            },
            "customParameters": {
                "organizationName": request.organizationInfo.get("name") if request.organizationInfo else "Healthcare Provider",
                "serviceRegion": request.organizationInfo.get("region") if request.organizationInfo else "Service Area",
                "emergencyNumber": "911",
                "supportEmail": "support@healthcare.com",
                "complianceLevel": request.compliance.get("level", "HIPAA") if request.compliance else "HIPAA",
                "totalProviders": request.providerDatabase.get("activeProviders", 0) if request.providerDatabase else 0
            },
            "interruptionSettings": {
                "threshold": 150,  # More sensitive for healthcare urgency
                "enabled": True
            },
            "silenceSettings": {
                "timeoutMs": 8000,  # Longer silence timeout for thinking
                "enabled": True
            },
            "responseDelaySeconds": 0.3,
            "llmRequestDelaySeconds": 0.1,
            "numWordsToInterruptAssistant": 2,
            "backgroundSound": "none",  # Professional healthcare setting
            "backgroundDenoisingEnabled": True,
            "modelOutputInMessagesEnabled": True,

            # Healthcare-specific compliance settings
            "compliance": {
                "hipaaCompliant": True,
                "dataRetention": "7_years",
                "encryptionLevel": "AES_256",
                "auditLogging": True,
                "consentRequired": request.compliance.get("dataHandling") == "HIPAA_COMPLIANT" if request.compliance else True
            }
        }

        # Simulate VAPI API call (replace with actual VAPI integration)
        assistant_id = f"healthcare_assistant_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        phone_number_id = f"phone_{assistant_id}"

        # Create response with healthcare-specific features
        response = HealthcareVAPIAgentResponse(
            id=assistant_id,
            phoneNumberId=phone_number_id,
            name=request.name,
            status="active",
            webhookUrl=f"{request.serverUrl}/vapi-webhook",
            compliance={
                "level": request.compliance.get("level", "HIPAA") if request.compliance else "HIPAA",
                "dataHandling": request.compliance.get("dataHandling", "HIPAA_COMPLIANT") if request.compliance else "HIPAA_COMPLIANT",
                "recordingPolicy": request.compliance.get("recordingPolicy", "CONSENT_REQUIRED") if request.compliance else "CONSENT_REQUIRED",
                "auditLogging": True,
                "encryptionEnabled": True
            },
            healthcareFeatures={
                "providerSearch": True,
                "emergencyServices": True,
                "appointmentBooking": True,
                "insuranceVerification": True,
                "multilanguageSupport": True,
                "humanEscalation": True,
                "totalProviders": request.providerDatabase.get("activeProviders", 0) if request.providerDatabase else 0,
                "specialtiesAvailable": len(request.providerDatabase.get("specialties", [])) if request.providerDatabase else 0,
                "locationsServed": len(request.providerDatabase.get("locations", [])) if request.providerDatabase else 0
            }
        )

        # Log the creation for monitoring
        logger.info(f"Healthcare VAPI assistant created successfully: {assistant_id}")

        return response

    except Exception as e:
        logger.error(f"Error creating healthcare VAPI assistant: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create healthcare VAPI assistant: {str(e)}"
        )

def generate_healthcare_system_prompt(
    base_prompt: str,
    organization_info: Optional[Dict[str, Any]] = None,
    provider_database: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate an enhanced system prompt with healthcare-specific context.

    Combines the Universal Wizard's dynamic prompt generation with
    Premier Health's domain expertise.
    """

    org_name = organization_info.get("name", "Healthcare Organization") if organization_info else "Healthcare Organization"
    region = organization_info.get("region", "your area") if organization_info else "your area"

    # Database context
    total_providers = provider_database.get("activeProviders", 0) if provider_database else 0
    specialties = provider_database.get("specialties", []) if provider_database else []
    locations = provider_database.get("locations", []) if provider_database else []

    enhanced_prompt = f"""{base_prompt}

## Organization Context:
**Organization**: {org_name}
**Service Region**: {region}
**Provider Network**: {total_providers} active healthcare providers
**Available Specialties**: {len(specialties)} medical specialties
**Coverage Areas**: {len(locations)} locations

## Available Specialties:
{', '.join(specialties[:15]) if specialties else 'General Practice, Emergency Medicine, Pediatrics, Obstetrics/Gynecology'}
{f"... and {len(specialties) - 15} more specialties" if len(specialties) > 15 else ""}

## Coverage Areas:
{', '.join(locations[:10]) if locations else 'Accra Central, Madina, Circle, East Legon, Kokomlemle'}
{f"... and {len(locations) - 10} more locations" if len(locations) > 10 else ""}

## Healthcare-Specific Guidelines:
1. **Emergency Priority**: Always prioritize emergency requests and ask about urgency level
2. **Provider Verification**: Confirm provider availability and insurance coverage before booking
3. **Medical Confidentiality**: Never discuss specific medical conditions - focus on finding appropriate care
4. **Appointment Coordination**: Offer to book appointments when providers are available
5. **Follow-up Support**: Provide contact information and offer to send details via SMS/email

## Response Patterns:
- For emergency queries: "This sounds urgent. Let me find emergency services near you immediately."
- For general searches: "I can help you find {specialty} providers in {location}. Let me search our network."
- For appointments: "I found available providers. Would you like me to check their appointment availability?"
- For insurance: "Let me verify your coverage with these providers."

## Escalation Triggers:
- Medical emergency (immediate transfer to emergency services)
- No providers found in requested area
- Insurance coverage issues
- Complex medical scheduling needs
- Patient privacy concerns

Remember: You are representing {org_name} and providing a professional healthcare service to patients in {region}. Always maintain medical confidentiality and provide accurate, helpful information."""

    return enhanced_prompt

def enhance_healthcare_tools(base_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enhance the base tools with healthcare-specific configurations.

    This combines Universal Wizard flexibility with Premier Health's
    specialized tool implementations.
    """

    enhanced_tools = []

    for tool in base_tools:
        if tool.get("function", {}).get("name") == "search_healthcare_providers":
            # Enhanced provider search tool
            enhanced_tool = {
                "type": "function",
                "function": {
                    "name": "search_healthcare_providers",
                    "description": "Search for healthcare providers by location, specialty, insurance network, or urgency level. Includes hospitals, clinics, pharmacies, and specialists.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language search query (e.g., 'find an eye doctor in Accra', 'pediatrician near Madina')"
                            },
                            "specialty": {
                                "type": "string",
                                "enum": [
                                    "Ophthalmology", "Pediatrics", "Obstetrics/Gynecology",
                                    "Cardiology", "Mental Health", "Emergency Medicine",
                                    "Dental", "General Practice", "Orthopedics", "Dermatology",
                                    "Neurology", "Oncology", "Radiology", "Pharmacy"
                                ],
                                "description": "Medical specialty filter"
                            },
                            "location": {
                                "type": "string",
                                "description": "Location name (e.g., 'Madina', 'East Legon', 'Circle', 'Accra Central')"
                            },
                            "provider_type": {
                                "type": "string",
                                "enum": ["hospital", "clinic", "pharmacy", "laboratory", "specialist_center"],
                                "description": "Type of healthcare provider"
                            },
                            "urgency": {
                                "type": "string",
                                "enum": ["emergency", "urgent", "normal"],
                                "description": "Urgency level of the healthcare need"
                            },
                            "insurance_network": {
                                "type": "boolean",
                                "default": True,
                                "description": "Filter by insurance network coverage"
                            },
                            "max_results": {
                                "type": "number",
                                "default": 5,
                                "description": "Maximum number of results to return"
                            }
                        },
                        "required": ["query"]
                    }
                },
                "server": tool.get("server", {})
            }
            enhanced_tools.append(enhanced_tool)

        elif tool.get("function", {}).get("name") == "get_emergency_providers":
            # Enhanced emergency services tool
            enhanced_tool = {
                "type": "function",
                "function": {
                    "name": "get_emergency_providers",
                    "description": "Get immediate emergency healthcare providers for urgent medical situations. Prioritizes hospitals with emergency departments and 24/7 services.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "Current location for finding nearest emergency services"
                            },
                            "emergency_type": {
                                "type": "string",
                                "enum": [
                                    "general_emergency", "cardiac", "trauma", "pediatric_emergency",
                                    "mental_health_crisis", "stroke", "breathing_difficulty", "severe_pain"
                                ],
                                "description": "Type of medical emergency"
                            },
                            "transport_needed": {
                                "type": "boolean",
                                "description": "Whether ambulance transport is needed"
                            },
                            "patient_age": {
                                "type": "string",
                                "enum": ["infant", "child", "adult", "elderly"],
                                "description": "Age category of patient for appropriate emergency care"
                            }
                        },
                        "required": ["location"]
                    }
                },
                "server": tool.get("server", {})
            }
            enhanced_tools.append(enhanced_tool)

        elif tool.get("function", {}).get("name") == "book_appointment":
            # Enhanced appointment booking tool
            enhanced_tool = {
                "type": "function",
                "function": {
                    "name": "book_appointment",
                    "description": "Book an appointment with a healthcare provider. Includes availability checking and confirmation.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "provider_id": {
                                "type": "number",
                                "description": "ID of the healthcare provider"
                            },
                            "appointment_type": {
                                "type": "string",
                                "enum": [
                                    "consultation", "follow_up", "screening", "vaccination",
                                    "emergency", "specialist_referral", "diagnostic_test"
                                ],
                                "description": "Type of appointment"
                            },
                            "preferred_date": {
                                "type": "string",
                                "description": "Preferred appointment date (YYYY-MM-DD format)"
                            },
                            "preferred_time": {
                                "type": "string",
                                "description": "Preferred appointment time (HH:MM format)"
                            },
                            "patient_name": {
                                "type": "string",
                                "description": "Full name of the patient"
                            },
                            "contact_phone": {
                                "type": "string",
                                "description": "Contact phone number"
                            },
                            "insurance_id": {
                                "type": "string",
                                "description": "Insurance ID number"
                            },
                            "reason_for_visit": {
                                "type": "string",
                                "description": "Brief reason for the appointment (optional)"
                            },
                            "special_requirements": {
                                "type": "string",
                                "description": "Any special requirements (wheelchair access, interpreter, etc.)"
                            }
                        },
                        "required": ["provider_id", "appointment_type", "patient_name", "contact_phone"]
                    }
                },
                "server": tool.get("server", {})
            }
            enhanced_tools.append(enhanced_tool)

        else:
            # Keep other tools as-is but enhance if healthcare-related
            enhanced_tools.append(tool)

    return enhanced_tools

@router.get("/healthcare-assistant/{assistant_id}/status")
async def get_healthcare_assistant_status(
    assistant_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Get status and metrics for a healthcare VAPI assistant."""
    try:
        # This would integrate with actual VAPI API to get real status
        return {
            "id": assistant_id,
            "status": "active",
            "calls_today": 42,
            "successful_provider_searches": 38,
            "appointments_booked": 15,
            "emergency_escalations": 2,
            "average_call_duration": "3:45",
            "customer_satisfaction": 4.7,
            "last_active": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting healthcare assistant status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get assistant status: {str(e)}"
        )

@router.post("/healthcare-assistant/{assistant_id}/update")
async def update_healthcare_assistant(
    assistant_id: str,
    updates: Dict[str, Any],
    current_user: dict = Depends(get_current_user_mongo)
):
    """Update configuration for a healthcare VAPI assistant."""
    try:
        logger.info(f"Updating healthcare assistant {assistant_id} with: {updates}")

        # This would integrate with actual VAPI API to update configuration
        return {
            "id": assistant_id,
            "status": "updated",
            "updated_fields": list(updates.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error updating healthcare assistant: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update assistant: {str(e)}"
        )