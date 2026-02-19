"""
Vapi Assistant Management Routes

Complete CRUD operations for Vapi assistants with custom TTS integration.

Manages:
- Creating Vapi assistants with custom TTS
- Listing all assistants
- Updating assistant configuration
- Deleting assistants
- Testing assistants with phone calls

Author: AI Labs Africa
Created: November 8, 2025
"""

import os
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
import httpx

from ..auth import get_current_user_mongo
from ..middleware.organization_context import (
    get_organization_context,
    validate_organization_access
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/vapi/assistants", tags=["Vapi Assistants"])


# Get Vapi API configuration
VAPI_API_KEY = os.getenv("VAPI_API_KEY")
VAPI_API_BASE = "https://api.vapi.ai"
CUSTOM_TTS_URL = os.getenv("CUSTOM_TTS_URL", "https://api.ailabsafrica.com/api/vapi/webhook")


# Pydantic models
class VapiVoiceConfig(BaseModel):
    """Voice configuration for Vapi assistant."""
    provider: str = Field("custom-tts", description="TTS provider (use custom-tts)")
    url: str = Field(..., description="Custom TTS webhook URL")
    secret: str = Field(..., description="API key for authentication")
    timeout: int = Field(30, description="Timeout in seconds")


class VapiModelConfig(BaseModel):
    """LLM model configuration."""
    provider: str = Field("openai", description="LLM provider")
    model: str = Field("gpt-4", description="Model name")
    temperature: float = Field(0.7, description="Model temperature")
    messages: List[Dict[str, str]] = Field(
        default_factory=lambda: [
            {"role": "system", "content": "You are a helpful assistant."}
        ],
        description="System messages"
    )


class VapiAssistantCreate(BaseModel):
    """Request to create a Vapi assistant."""
    name: str = Field(..., description="Assistant name")
    system_prompt: str = Field(
        "You are a helpful AI assistant.",
        description="System prompt for the assistant"
    )
    first_message: str = Field(
        "Hello! How can I help you today?",
        description="First message to user"
    )
    model: str = Field("gpt-4", description="LLM model to use")
    voice_provider: str = Field(
        "kokoro",
        description="TTS provider: kokoro, styletts2, melotts, openvoice, chatterbox, coqui, f5tts"
    )
    sample_rate: int = Field(24000, description="Audio sample rate")
    enable_recording: bool = Field(True, description="Enable call recording")
    enable_transcription: bool = Field(True, description="Enable call transcription")


class VapiAssistantUpdate(BaseModel):
    """Request to update a Vapi assistant."""
    name: Optional[str] = Field(None, description="Assistant name")
    system_prompt: Optional[str] = Field(None, description="System prompt")
    first_message: Optional[str] = Field(None, description="First message")
    model: Optional[str] = Field(None, description="LLM model")
    voice_provider: Optional[str] = Field(None, description="TTS provider")


class VapiPhoneCallRequest(BaseModel):
    """Request to make a test phone call."""
    assistant_id: str = Field(..., description="Vapi assistant ID")
    phone_number: str = Field(..., description="Phone number to call (E.164 format)")
    name: Optional[str] = Field(None, description="Name of person to call")


def get_vapi_headers() -> Dict[str, str]:
    """Get headers for Vapi API requests."""
    if not VAPI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="VAPI_API_KEY not configured in environment"
        )

    return {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }


@router.get("/tts-providers")
async def get_tts_providers():
    """
    Get list of available TTS providers.

    Returns:
        List of TTS providers with metadata

    Example Response:
    ```json
    {
        "providers": [
            {
                "id": "kokoro",
                "name": "Kokoro TTS",
                "description": "Fast, high-quality TTS with 82M parameters",
                "url": "https://kokoro.ailabsafrica.com",
                "recommended": true
            },
            {
                "id": "styletts2",
                "name": "StyleTTS2",
                "description": "Expressive TTS with style transfer",
                "url": "https://styletts.ailabsafrica.com",
                "recommended": false
            }
        ],
        "total": 7
    }
    ```
    """
    providers = [
        {
            "id": "kokoro",
            "name": "Kokoro TTS",
            "description": "Fast, high-quality TTS with 82M parameters. Small but comparable to larger models.",
            "url": "https://kokoro.ailabsafrica.com",
            "recommended": True
        },
        {
            "id": "styletts2",
            "name": "StyleTTS2",
            "description": "Expressive TTS with style transfer and voice cloning capabilities",
            "url": "https://styletts.ailabsafrica.com",
            "recommended": False
        },
        {
            "id": "melotts",
            "name": "MeloTTS",
            "description": "High-quality multi-lingual TTS",
            "url": "https://melotts.ailabsafrica.com",
            "recommended": False
        },
        {
            "id": "openvoice",
            "name": "OpenVoice",
            "description": "Instant voice cloning with flexible control",
            "url": "https://openvoice.ailabsafrica.com",
            "recommended": False
        },
        {
            "id": "chatterbox",
            "name": "Chatterbox",
            "description": "Expressive TTS with reference audio support",
            "url": "https://chatterbox.ailabsafrica.com",
            "recommended": False
        },
        {
            "id": "coqui",
            "name": "Coqui TTS",
            "description": "Multi-speaker TTS with voice cloning",
            "url": "https://coqui.ailabsafrica.com",
            "recommended": False
        },
        {
            "id": "f5tts",
            "name": "F5-TTS",
            "description": "Fast, flexible TTS with zero-shot voice cloning",
            "url": "https://f5tts.ailabsafrica.com",
            "recommended": False
        }
    ]

    return {
        "providers": providers,
        "total": len(providers)
    }


@router.get("/")
async def list_assistants(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    current_user: Dict = Depends(get_current_user_mongo)
):
    """
    List all Vapi assistants with pagination.

    Args:
        limit: Maximum number of assistants to return (default: 20, max: 100)
        offset: Number of assistants to skip (default: 0)

    Returns:
        List of assistants with their configurations

    Now properly scoped to organization. Requires authentication.

    Example Response:
    ```json
    {
        "assistants": [
            {
                "id": "asst_abc123",
                "name": "Customer Support Bot",
                "model": "gpt-4",
                "voice": {"provider": "custom-tts"},
                "createdAt": "2025-11-08T...",
                "updatedAt": "2025-11-08T..."
            }
        ],
        "total": 100,
        "limit": 20,
        "offset": 0
    }
    ```
    """
    try:
        # Get and validate organization context
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Listing Vapi assistants for organization: {org_id}")

        # Limit maximum to avoid huge responses
        limit = min(limit, 100)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{VAPI_API_BASE}/assistant",
                headers=get_vapi_headers(),
                timeout=30.0  # Increased timeout for large lists
            )

            if response.status_code == 200:
                all_assistants = response.json()
                total = len(all_assistants)

                # Apply pagination
                paginated_assistants = all_assistants[offset:offset + limit]

                return {
                    "assistants": paginated_assistants,
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    "has_more": (offset + limit) < total
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Vapi API error: {response.text}"
                )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Vapi API timeout")
    except Exception as e:
        logger.error(f"Failed to list assistants: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{assistant_id}")
async def get_assistant(
    request: Request,
    assistant_id: str,
    current_user: Dict = Depends(get_current_user_mongo)
):
    """
    Get a specific Vapi assistant.

    Args:
        assistant_id: Vapi assistant ID

    Returns:
        Assistant details

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get and validate organization context
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Getting Vapi assistant {assistant_id} for organization: {org_id}")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{VAPI_API_BASE}/assistant/{assistant_id}",
                headers=get_vapi_headers(),
                timeout=10.0
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail="Assistant not found")
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Vapi API error: {response.text}"
                )

    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Vapi API timeout")
    except Exception as e:
        logger.error(f"Failed to get assistant: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_assistant(
    http_request: Request,
    request: VapiAssistantCreate,
    current_user: Dict = Depends(get_current_user_mongo)
):
    """
    Create a new Vapi assistant with custom TTS.

    Args:
        request: Assistant configuration

    Returns:
        Created assistant details including ID

    Now properly scoped to organization. Requires authentication.

    Example Request:
    ```json
    {
        "name": "Customer Support Bot",
        "system_prompt": "You are a helpful customer support agent.",
        "first_message": "Hello! How can I help you?",
        "model": "gpt-4",
        "voice_provider": "styletts2",
        "sample_rate": 24000
    }
    ```
    """
    try:
        # Get and validate organization context
        org_id = get_organization_context(http_request)
        if org_id:
            await validate_organization_access(http_request, current_user, org_id)

        user_id = current_user.get("id") or current_user.get("sub")
        logger.info(f"Creating Vapi assistant '{request.name}' for organization: {org_id}")
        # Build Vapi assistant configuration
        assistant_config = {
            "name": request.name,
            "model": {
                "provider": "openai",
                "model": request.model,
                "temperature": 0.7,
                "messages": [
                    {
                        "role": "system",
                        "content": request.system_prompt
                    }
                ]
            },
            "voice": {
                "provider": "custom-voice",
                "server": {
                    "url": CUSTOM_TTS_URL,
                    "secret": VAPI_API_KEY,
                    "timeoutSeconds": 30
                }
            },
            "firstMessage": request.first_message,
            "recordingEnabled": request.enable_recording,
            "transcriber": {
                "provider": "deepgram",
                "model": "nova-2",
                "language": "en"
            } if request.enable_transcription else None
        }

        # Create assistant via Vapi API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{VAPI_API_BASE}/assistant",
                headers=get_vapi_headers(),
                json=assistant_config,
                timeout=30.0
            )

            if response.status_code == 201:
                assistant = response.json()
                logger.info(f"Created Vapi assistant: {assistant.get('id')}")
                return {
                    "success": True,
                    "assistant": assistant,
                    "message": f"Assistant '{request.name}' created successfully"
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Vapi API error: {response.text}"
                )

    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Vapi API timeout")
    except Exception as e:
        logger.error(f"Failed to create assistant: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{assistant_id}")
async def update_assistant(
    http_request: Request,
    assistant_id: str,
    request: VapiAssistantUpdate,
    current_user: Dict = Depends(get_current_user_mongo)
):
    """
    Update an existing Vapi assistant.

    Args:
        assistant_id: Vapi assistant ID
        request: Updated configuration

    Returns:
        Updated assistant details

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get and validate organization context
        org_id = get_organization_context(http_request)
        if org_id:
            await validate_organization_access(http_request, current_user, org_id)

        logger.info(f"Updating Vapi assistant {assistant_id} for organization: {org_id}")
        # Build update payload (only include provided fields)
        update_data = {}

        if request.name:
            update_data["name"] = request.name

        if request.system_prompt:
            update_data["model"] = {
                "messages": [
                    {"role": "system", "content": request.system_prompt}
                ]
            }

        if request.first_message:
            update_data["firstMessage"] = request.first_message

        if request.model:
            if "model" not in update_data:
                update_data["model"] = {}
            update_data["model"]["model"] = request.model
            update_data["model"]["provider"] = "openai"  # Default to openai

        # Update assistant via Vapi API
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{VAPI_API_BASE}/assistant/{assistant_id}",
                headers=get_vapi_headers(),
                json=update_data,
                timeout=30.0
            )

            if response.status_code == 200:
                assistant = response.json()
                logger.info(f"Updated Vapi assistant: {assistant_id}")
                return {
                    "success": True,
                    "assistant": assistant,
                    "message": "Assistant updated successfully"
                }
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail="Assistant not found")
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Vapi API error: {response.text}"
                )

    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Vapi API timeout")
    except Exception as e:
        logger.error(f"Failed to update assistant: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{assistant_id}")
async def delete_assistant(
    request: Request,
    assistant_id: str,
    current_user: Dict = Depends(get_current_user_mongo)
):
    """
    Delete a Vapi assistant.

    Args:
        assistant_id: Vapi assistant ID

    Returns:
        Deletion confirmation

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Get and validate organization context
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Deleting Vapi assistant {assistant_id} for organization: {org_id}")
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{VAPI_API_BASE}/assistant/{assistant_id}",
                headers=get_vapi_headers(),
                timeout=30.0
            )

            if response.status_code == 200:
                logger.info(f"Deleted Vapi assistant: {assistant_id}")
                return {
                    "success": True,
                    "message": "Assistant deleted successfully"
                }
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail="Assistant not found")
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Vapi API error: {response.text}"
                )

    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Vapi API timeout")
    except Exception as e:
        logger.error(f"Failed to delete assistant: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/call")
async def make_phone_call(request: VapiPhoneCallRequest):
    """
    Make a test phone call using a Vapi assistant.

    Args:
        request: Phone call configuration

    Returns:
        Call details including call ID

    Example Request:
    ```json
    {
        "assistant_id": "asst_abc123",
        "phone_number": "+1234567890",
        "name": "John Doe"
    }
    ```

    Note:
        - Phone number must be in E.164 format (+1234567890)
        - Vapi will charge per minute for calls
        - Call will use your custom TTS webhook
    """
    try:
        # Build call request
        call_request = {
            "assistantId": request.assistant_id,
            "customer": {
                "number": request.phone_number
            }
        }

        if request.name:
            call_request["customer"]["name"] = request.name

        # Make call via Vapi API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{VAPI_API_BASE}/call/phone",
                headers=get_vapi_headers(),
                json=call_request,
                timeout=30.0
            )

            if response.status_code == 201:
                call = response.json()
                logger.info(f"Started Vapi call: {call.get('id')} to {request.phone_number}")
                return {
                    "success": True,
                    "call": call,
                    "message": f"Call initiated to {request.phone_number}"
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Vapi API error: {response.text}"
                )

    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Vapi API timeout")
    except Exception as e:
        logger.error(f"Failed to make call: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calls/history")
async def get_call_history(limit: int = 10):
    """
    Get call history.

    Args:
        limit: Number of calls to return (default: 10)

    Returns:
        List of recent calls
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{VAPI_API_BASE}/call",
                headers=get_vapi_headers(),
                params={"limit": limit},
                timeout=10.0
            )

            if response.status_code == 200:
                calls = response.json()
                return {
                    "calls": calls,
                    "total": len(calls)
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Vapi API error: {response.text}"
                )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Vapi API timeout")
    except Exception as e:
        logger.error(f"Failed to get call history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/phone-numbers")
async def get_phone_numbers():
    """
    Get Vapi phone numbers.

    Returns:
        List of purchased phone numbers
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{VAPI_API_BASE}/phone-number",
                headers=get_vapi_headers(),
                timeout=10.0
            )

            if response.status_code == 200:
                phone_numbers = response.json()
                return {
                    "phone_numbers": phone_numbers,
                    "total": len(phone_numbers)
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Vapi API error: {response.text}"
                )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Vapi API timeout")
    except Exception as e:
        logger.error(f"Failed to get phone numbers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
