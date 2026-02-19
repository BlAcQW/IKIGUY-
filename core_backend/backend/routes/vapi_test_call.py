"""
Test endpoint for making calls with custom voice settings.
"""

import os
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Header
import aiohttp
from pydantic import BaseModel

from ..auth import get_current_user_mongo
from ..mongo import get_collection
from ..services.vapi_assistant_builder import build_vapi_assistant_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vapi/test-call", tags=["VAPI Test Calls"])

VAPI_API_BASE = "https://api.vapi.ai"
VAPI_API_KEY = os.getenv("VAPI_API_KEY")


class TestCallRequest(BaseModel):
    """Request model for test call."""
    assistant_id: str
    phone_number_id: str
    customer_number: str
    tts_provider: Optional[str] = "kokoro"
    tts_voice: Optional[str] = "af_heart"
    asr_provider: Optional[str] = "faster_whisper"
    llm_model: Optional[str] = "llama3.2:3b"


@router.post("/with-custom-settings")
async def test_call_with_custom_settings(
    request: TestCallRequest,
    current_user: dict = Depends(get_current_user_mongo),
    # Allow bypass for testing with API key header
    x_test_api_key: Optional[str] = Header(None, alias="X-Test-API-Key")
):
    """
    Make a test call with custom voice settings.
    
    This endpoint:
    1. Finds the automation config for the assistant_id
    2. Updates it with the provided custom settings
    3. Applies the settings to the VAPI assistant
    4. Makes a test call
    
    Example:
    {
        "assistant_id": "f24f0871-daab-42e5-b9a9-3f582e8f686f",
        "phone_number_id": "0ae5655c-7ade-4136-a7a8-680f5b3d20f7",
        "customer_number": "+233500603563",
        "tts_provider": "kokoro",
        "tts_voice": "af_heart",
        "asr_provider": "faster_whisper",
        "llm_model": "llama3.2:3b"
    }
    """
    try:
        if not VAPI_API_KEY:
            raise HTTPException(status_code=500, detail="VAPI_API_KEY not configured")
        
        # Allow test API key bypass for testing (check environment variable)
        test_api_key = os.getenv("TEST_API_KEY")
        if x_test_api_key and test_api_key and x_test_api_key == test_api_key:
            # Bypass auth for testing - create a minimal user dict
            current_user = {"id": "test_user", "email": "test@example.com"}
        
        from bson import ObjectId
        
        # Step 1: Find automation config
        config_collection = get_collection("automation_configs")
        config = await config_collection.find_one({
            "$or": [
                {"vapi_agent.assistant_id": request.assistant_id},
                {"vapiAgent.assistant_id": request.assistant_id},
                {"vapi_agent.assistantId": request.assistant_id},
                {"vapiAgent.assistantId": request.assistant_id},
            ]
        })
        
        custom_settings = {
            "tts": {
                "provider": request.tts_provider,
                "voice": request.tts_voice,
                "speed": 1.0,
                "pitch": 0.0
            },
            "asr": {
                "provider": request.asr_provider,
                "language": "en"
            },
            "llm": {
                "model": request.llm_model,
                "temperature": 0.7,
                "maxTokens": 2000
            },
            "referenceVoice": None
        }
        
        # Step 2: Update automation config if found
        if config:
            config_id = str(config["_id"])
            vapi_agent = config.get("vapi_agent") or config.get("vapiAgent", {})
            
            await config_collection.update_one(
                {"_id": ObjectId(config_id)},
                {
                    "$set": {
                        "vapi_agent.custom_settings_override": custom_settings,
                        "vapiAgent.custom_settings_override": custom_settings,
                    }
                }
            )
            logger.info(f"Updated automation config {config_id} with custom settings")
        else:
            logger.warning(f"No automation config found for assistant {request.assistant_id}, using direct config")
            vapi_agent = {"assistant_id": request.assistant_id}
        
        # Step 3: Apply settings to VAPI assistant
        vapi_config = build_vapi_assistant_config(
            {**vapi_agent, "custom_settings_override": custom_settings},
            request.assistant_id
        )
        
        headers = {
            "Authorization": f"Bearer {VAPI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            # Update assistant
            import json as json_lib
            logger.info(f"📤 Updating VAPI assistant {request.assistant_id} with custom voice settings:")
            logger.info(json_lib.dumps(vapi_config.get("voice", {}), indent=2))
            
            async with session.patch(
                f"{VAPI_API_BASE}/assistant/{request.assistant_id}",
                headers=headers,
                json=vapi_config,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_text = await response.text()
                if response.status != 200:
                    logger.error(f"❌ Failed to update VAPI assistant: {response.status} - {response_text}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to update VAPI assistant: {response_text}"
                    )
                else:
                    logger.info(f"✅ Successfully updated VAPI assistant {request.assistant_id}")
                    # Verify the update
                    async with session.get(
                        f"{VAPI_API_BASE}/assistant/{request.assistant_id}",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as verify_response:
                        if verify_response.status == 200:
                            assistant_config = await verify_response.json()
                            voice_config = assistant_config.get("voice", {})
                            voice_provider = voice_config.get("provider")
                            voice_server = voice_config.get("server", {})
                            voice_url = voice_server.get("url", "N/A")
                            
                            logger.info(f"✅ Verified: voice provider={voice_provider}, webhook_url={voice_url}")
                            if voice_provider != "custom-voice":
                                logger.warning(f"⚠️  Voice provider is '{voice_provider}', expected 'custom-voice'")
                        else:
                            logger.warning(f"Could not verify assistant update: {verify_response.status}")
        
        # Step 4: Make test call
        call_payload = {
            "assistantId": request.assistant_id,
            "phoneNumberId": request.phone_number_id,
            "customer": {
                "number": request.customer_number
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{VAPI_API_BASE}/call/phone",
                headers=headers,
                json=call_payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 201:
                    call_result = await response.json()
                    return {
                        "success": True,
                        "call_id": call_result.get("id"),
                        "status": call_result.get("status"),
                        "message": f"Test call initiated to {request.customer_number}",
                        "custom_settings_applied": {
                            "tts": f"{request.tts_provider}/{request.tts_voice}",
                            "asr": request.asr_provider,
                            "llm": request.llm_model
                        },
                        "call_details": call_result
                    }
                else:
                    text = await response.text()
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Failed to make call: {text}"
                    )
                    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test call failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Test call failed: {str(e)}")

