"""
VAPI Custom Provider Webhooks

Webhook endpoints for custom TTS, LLM, and ASR providers when using custom_settings_override
in automation configs. These endpoints handle requests from VAPI and route them to the
appropriate services based on the automation configuration.
"""

import os
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request, Header, Depends, Query
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from datetime import datetime

from ..auth import get_current_user_mongo
from ..mongo import get_collection
from ..middleware.organization_context import get_organization_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vapi/custom-providers", tags=["VAPI Custom Providers"])

# Get API base URL for building webhook URLs
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.ailabsafrica.com")
VAPI_API_KEY = os.getenv("VAPI_API_KEY")


# Pydantic models for requests
class VAPILLMRequest(BaseModel):
    """VAPI custom LLM request format"""
    messages: list[Dict[str, str]] = Field(..., description="Chat messages")
    model: Optional[str] = Field(None, description="Model name (for reference)")
    temperature: Optional[float] = Field(0.7, description="Temperature")
    max_tokens: Optional[int] = Field(None, description="Max tokens")
    assistant: Optional[Dict[str, Any]] = Field(None, description="Assistant metadata")
    call: Optional[Dict[str, Any]] = Field(None, description="Call metadata")


class VAPITTSRequest(BaseModel):
    """VAPI custom TTS request format"""
    message: Dict[str, Any] = Field(..., description="TTS message with text and sampleRate")
    timestamp: Optional[int] = Field(None, description="Request timestamp")
    call: Optional[Dict[str, Any]] = Field(None, description="Call metadata")
    assistant: Optional[Dict[str, Any]] = Field(None, description="Assistant metadata")
    customer: Optional[Dict[str, Any]] = Field(None, description="Customer metadata")


class VAPIASRRequest(BaseModel):
    """VAPI custom ASR request format"""
    audio: Optional[bytes] = Field(None, description="Audio data")
    audio_url: Optional[str] = Field(None, description="Audio URL")
    language: Optional[str] = Field("en", description="Language code")
    assistant: Optional[Dict[str, Any]] = Field(None, description="Assistant metadata")
    call: Optional[Dict[str, Any]] = Field(None, description="Call metadata")


async def get_assistant_config(assistant_id: str) -> Optional[Dict[str, Any]]:
    """
    Get automation config for a VAPI assistant ID.

    Args:
        assistant_id: VAPI assistant ID

    Returns:
        Automation config with custom_settings_override if exists
    """
    try:
        config_collection = get_collection("automation_configs")
        # Try both snake_case and camelCase fields - use async find_one
        config = await config_collection.find_one({
            "$or": [
                {"vapi_agent.assistant_id": assistant_id},
                {"vapiAgent.assistant_id": assistant_id},
                {"vapi_agent.assistantId": assistant_id},
                {"vapiAgent.assistantId": assistant_id},
            ]
        })

        if config:
            # Check both formats
            vapi_agent = config.get("vapi_agent") or config.get("vapiAgent", {})
            if vapi_agent.get("custom_settings_override") or vapi_agent.get("customSettingsOverride"):
                return config
        return None
    except Exception as e:
        logger.error(f"Error fetching assistant config: {e}")
        return None


@router.post("/llm")
async def vapi_custom_llm_webhook(
    request: Request,
    authorization: Optional[str] = Header(None),
    assistant_id: Optional[str] = None  # Can be passed as query param
) -> Dict[str, Any]:
    """
    Custom LLM webhook endpoint for VAPI.
    
    Receives chat completion requests from VAPI and routes them to the configured
    LLM provider based on custom_settings_override in the automation config.
    
    Request format (from VAPI):
    ```json
    {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ],
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 150,
        "assistant": {"id": "asst_123", "organizationId": "org_abc"}
    }
    ```
    
    Response format (OpenAI-compatible):
    ```json
    {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-4",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you?"
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
    }
    """
    try:
        # Parse request body
        request_data = await request.json()
        
        # Extract assistant ID from request data or query param
        if not assistant_id:
            assistant_id = request_data.get("assistant", {}).get("id") if request_data.get("assistant") else None
        
        if not assistant_id:
            raise HTTPException(status_code=400, detail="Assistant ID required in request or query parameter")
        
        # Parse request into structured format
        messages = request_data.get("messages", [])
        model = request_data.get("model")
        temperature = request_data.get("temperature", 0.7)
        max_tokens = request_data.get("max_tokens")

        # Get automation config to find custom LLM settings
        config = await get_assistant_config(assistant_id)
        if not config:
            raise HTTPException(
                status_code=404,
                detail="Automation config not found for this assistant"
            )
        
        # Check both snake_case and camelCase
        vapi_agent = config.get("vapi_agent") or config.get("vapiAgent", {})
        override = vapi_agent.get("custom_settings_override") or vapi_agent.get("customSettingsOverride")
        
        if not override:
            raise HTTPException(
                status_code=404,
                detail="No custom LLM settings found for this assistant"
            )
        llm_config = override.get("llm", {})
        
        # Get LLM model from override or use default
        llm_model = llm_config.get("model") or request.model or "gpt-4o-mini"
        temperature = llm_config.get("temperature", request.temperature or 0.7)
        max_tokens = llm_config.get("maxTokens", request.max_tokens or 150)
        
        # Route to LLM service based on provider
        from apps.shared.services.llm_provider_service import get_llm_service, ChatMessage
        from apps.shared.services.llm_provider_service import ChatRequest
        
        llm_service = await get_llm_service()
        
        # Convert messages format
        chat_messages: list[ChatMessage] = [
            ChatMessage(role=msg["role"], content=msg["content"])
            for msg in messages
        ]
        
        # Create chat request
        chat_request = ChatRequest(
            model_id=llm_model,
            messages=chat_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False
        )
        
        # Call LLM service
        response = await llm_service.chat(chat_request)
        
        # Format response in OpenAI-compatible format
        return {
            "id": f"chatcmpl-{int(datetime.now().timestamp())}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": llm_model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response.message
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": response.usage.get("prompt_tokens", 0),
                "completion_tokens": response.usage.get("completion_tokens", 0),
                "total_tokens": response.usage.get("total_tokens", 0)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Custom LLM webhook failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"LLM request failed: {str(e)}")


@router.post("/tts")
async def vapi_custom_tts_webhook(
    request: Request,
    authorization: Optional[str] = Header(None),
    assistant_id: Optional[str] = Query(None)  # Can be passed as query param
) -> Response:
    """
    Custom TTS webhook endpoint for VAPI.
    
    Receives TTS requests from VAPI and routes them to the configured
    TTS provider based on custom_settings_override in the automation config.
    
    This endpoint uses TTSProviderService to synthesize with the custom provider.
    
    VAPI sends requests in this format:
    {
      "message": {
        "type": "voice-request",
        "text": "Hello world",
        "sampleRate": 24000
      },
      "assistant": {"id": "assistant_id"},
      ...
    }
    """
    try:
        logger.info("📞 Custom TTS webhook called")
        # Parse request body
        request_data = await request.json()
        
        # Extract assistant ID from request data or query param
        if not assistant_id:
            assistant_id = request_data.get("assistant", {}).get("id") if request_data.get("assistant") else None
        
        if not assistant_id:
            raise HTTPException(status_code=400, detail="Assistant ID required in request or query parameter")
        
        # Get automation config to find custom TTS settings
        config = await get_assistant_config(assistant_id)
        if not config:
            raise HTTPException(
                status_code=404,
                detail="Automation config not found for this assistant"
            )
        
        # Check both snake_case and camelCase
        vapi_agent = config.get("vapi_agent") or config.get("vapiAgent", {})
        override = vapi_agent.get("custom_settings_override") or vapi_agent.get("customSettingsOverride")
        
        if not override:
            raise HTTPException(
                status_code=404,
                detail="No custom TTS settings found for this assistant"
            )
        tts_config = override.get("tts", {})
        
        # Get TTS provider and voice from override
        tts_provider = tts_config.get("provider")
        tts_voice = tts_config.get("voice")

        # Get reference voice for voice cloning (if configured)
        reference_voice_id = override.get("referenceVoice")

        if not tts_provider:
            raise HTTPException(
                status_code=400,
                detail="TTS provider required in custom settings"
            )

        # Voice is required unless we have a reference voice for cloning
        if not tts_voice and not reference_voice_id:
            raise HTTPException(
                status_code=400,
                detail="TTS voice or reference voice required in custom settings"
            )

        # Extract message and other fields from request
        message = request_data.get("message", {})
        text = message.get("text", "")
        sample_rate = message.get("sampleRate", 24000)

        if not text:
            raise HTTPException(status_code=400, detail="Missing text in message")

        logger.info(f"Synthesizing with provider={tts_provider}, voice={tts_voice}, reference_voice={reference_voice_id}, text_length={len(text)}")

        # Use the async TTS client directly (bypasses health check issues)
        from apps.shared.tts.client import AsyncTTSClient
        from apps.shared.tts.models import TTSProvider

        # Convert provider string to enum
        try:
            provider_enum = TTSProvider(tts_provider)
        except ValueError:
            # Try uppercase version
            try:
                provider_enum = TTSProvider[tts_provider.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown TTS provider: {tts_provider}"
                )

        # Synthesize using the async client with proper initialization
        async with AsyncTTSClient() as tts_client:
            # Check if we should use voice cloning
            if reference_voice_id:
                # Load reference audio file
                reference_audio_path = f"/opt/kasaai/apps/voice-lab/voices/{reference_voice_id}"

                # Check if path has extension, if not try common extensions
                if not os.path.exists(reference_audio_path):
                    for ext in ['.wav', '.mp3', '.flac']:
                        if os.path.exists(f"{reference_audio_path}{ext}"):
                            reference_audio_path = f"{reference_audio_path}{ext}"
                            break

                if not os.path.exists(reference_audio_path):
                    raise HTTPException(
                        status_code=404,
                        detail=f"Reference audio not found: {reference_voice_id}"
                    )

                # Read reference audio
                with open(reference_audio_path, 'rb') as f:
                    reference_audio = f.read()

                logger.info(f"Using voice cloning with reference: {reference_audio_path} ({len(reference_audio)} bytes)")

                # Use clone_voice for voice cloning providers
                tts_response = await tts_client.clone_voice(
                    text=text,
                    reference_audio=reference_audio,
                    provider=provider_enum,
                    speed=tts_config.get("speed", 1.0)
                )
            else:
                # Use standard synthesize
                tts_response = await tts_client.synthesize(
                    text=text,
                    provider=provider_enum,
                    language="en",
                    speaker=tts_voice,
                    speed=tts_config.get("speed", 1.0)
                )

        if not tts_response.audio:
            raise HTTPException(status_code=500, detail="TTS synthesis returned no audio")

        # Convert audio to raw PCM format using the existing webhook service converter
        from apps.shared.services.vapi_tts_webhook import get_vapi_webhook_service
        vapi_webhook_service = get_vapi_webhook_service()

        # Use the webhook service's PCM converter (handles WAV parsing, resampling, etc.)
        pcm_audio = vapi_webhook_service._convert_to_pcm(
            audio_data=tts_response.audio,
            target_sample_rate=sample_rate
        )

        # Return raw PCM audio as per VAPI requirements
        logger.info(f"Returning PCM audio: {len(pcm_audio)} bytes at {sample_rate}Hz")
        return Response(
            content=pcm_audio,
            media_type="application/octet-stream",
            headers={
                "Content-Type": "application/octet-stream"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Custom TTS webhook failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")


@router.post("/asr")
async def vapi_custom_asr_webhook(
    request: Request,
    authorization: Optional[str] = Header(None),
    assistant_id: Optional[str] = None  # Can be passed as query param
) -> Dict[str, Any]:
    """
    Custom ASR webhook endpoint for VAPI (if supported).
    
    Receives audio transcription requests from VAPI and routes them to the configured
    ASR provider based on custom_settings_override in the automation config.
    
    Note: VAPI may not support custom ASR providers. This endpoint is prepared for
    future support.
    """
    try:
        body = await request.json()
        
        # Extract assistant ID from request data or query param
        if not assistant_id:
            assistant_id = body.get("assistant", {}).get("id") if body.get("assistant") else None
        
        if not assistant_id:
            raise HTTPException(status_code=400, detail="Assistant ID required in request or query parameter")

        # Get automation config
        config = await get_assistant_config(assistant_id)
        if not config:
            raise HTTPException(
                status_code=404,
                detail="Automation config not found for this assistant"
            )

        # Check both snake_case and camelCase
        vapi_agent = config.get("vapi_agent") or config.get("vapiAgent", {})
        override = vapi_agent.get("custom_settings_override") or vapi_agent.get("customSettingsOverride")

        if not override:
            raise HTTPException(
                status_code=404,
                detail="No custom ASR settings found for this assistant"
            )
        asr_config = override.get("asr", {})

        # Get ASR provider and language
        asr_provider = asr_config.get("provider")
        language = asr_config.get("language", "en")

        if not asr_provider:
            raise HTTPException(
                status_code=400,
                detail="ASR provider required in custom settings"
            )

        # Use ASRProviderService with the custom provider from settings
        from apps.shared.services.asr_provider_service import ASRProviderService

        # Get audio from request - VAPI may send audio in different formats
        audio_data = body.get("audio")
        audio_url = body.get("audioUrl")

        if not audio_data and not audio_url:
            raise HTTPException(status_code=400, detail="Missing audio data or URL in request")

        # Initialize ASR provider service
        asr_service = ASRProviderService()
        await asr_service.initialize()

        # If we have a URL, fetch the audio first
        if audio_url and not audio_data:
            import httpx
            async with httpx.AsyncClient() as client:
                audio_response = await client.get(audio_url, timeout=30.0)
                if audio_response.status_code != 200:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to fetch audio from URL: {audio_response.status_code}"
                    )
                audio_data = audio_response.content

        # Handle base64 encoded audio
        if isinstance(audio_data, str):
            import base64
            try:
                audio_data = base64.b64decode(audio_data)
            except Exception:
                # Might already be bytes
                pass

        # Transcribe using the custom ASR provider
        logger.info(f"Transcribing with provider={asr_provider}, language={language}")

        transcription_result = await asr_service.transcribe(
            user_id="vapi_call",
            audio_data=audio_data,
            provider_id=asr_provider,
            language=language
        )

        logger.info(f"Transcription complete: {len(transcription_result.get('text', ''))} chars")

        # Return in VAPI expected format
        return {
            "text": transcription_result.get("text", ""),
            "language": transcription_result.get("language", language),
            "confidence": transcription_result.get("confidence"),
            "duration": transcription_result.get("duration"),
            "provider": asr_provider
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Custom ASR webhook failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"ASR transcription failed: {str(e)}")


def build_custom_provider_url(provider_type: str, assistant_id: str) -> str:
    """
    Build webhook URL for custom provider.
    
    Args:
        provider_type: "tts", "llm", or "asr"
        assistant_id: VAPI assistant ID
        
    Returns:
        Webhook URL
    """
    return f"{API_BASE_URL}/vapi/custom-providers/{provider_type}?assistant_id={assistant_id}"

