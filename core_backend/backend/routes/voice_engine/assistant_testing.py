"""
Assistant Testing Endpoints
Provides phone testing and shareable link generation for assistants
Uses shared FastRTC services from @apps/shared/integration/webrtc
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

# Import shared FastRTC services (centralized, reusable)
from apps.shared.integration.webrtc import (
    generate_test_phone,
    launch_shareable_ui,
    FASTRTC_AVAILABLE
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assistant-testing", tags=["assistant-testing"])


class GeneratePhoneRequest(BaseModel):
    """Request to generate temporary test phone number"""
    assistant_id: str = Field(..., description="Assistant ID to test")
    ui_title: Optional[str] = Field(None, description="Optional UI title")
    ui_subtitle: Optional[str] = Field(None, description="Optional UI subtitle")


class LaunchUIRequest(BaseModel):
    """Request to launch shareable testing UI"""
    assistant_id: str = Field(..., description="Assistant ID to test")
    ui_title: Optional[str] = Field(None, description="Optional UI title")
    ui_subtitle: Optional[str] = Field(None, description="Optional UI subtitle")
    share: bool = Field(True, description="Create public shareable link")


@router.post("/generate-phone")
async def generate_test_phone_number(request: GeneratePhoneRequest):
    """
    Generate a temporary test phone number for an assistant using FastRTC's .fastphone().

    This creates a free US phone number that expires after a period.
    Perfect for quick testing and demos without setting up Twilio/Vonage.

    **Requirements:**
    - HUGGINGFACE_TOKEN environment variable
    - FastRTC installed with: pip install 'fastrtc[vad,tts]'

    **Example Response:**
    ```json
    {
        "success": true,
        "number": "+1 (555) 123-4567",
        "country": "US",
        "expires_at": "2024-01-15T10:30:00Z",
        "message": "Temporary phone number generated successfully"
    }
    ```

    **Usage:**
    - Call the generated number from any phone
    - Assistant will answer automatically
    - Speak naturally - automatic turn-taking
    - Number expires after period
    """
    if not FASTRTC_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="FastRTC not available. Install with: pip install 'fastrtc[vad,tts]'"
        )

    # Get HuggingFace token from environment
    hf_token = os.getenv('HUGGINGFACE_TOKEN') or os.getenv('HF_TOKEN')
    if not hf_token:
        raise HTTPException(
            status_code=400,
            detail="HUGGINGFACE_TOKEN environment variable not set"
        )

    try:
        logger.info(f"📞 Generating test phone for assistant: {request.assistant_id}")

        # Use shared service
        result = generate_test_phone(
            assistant_id=request.assistant_id,
            hf_token=hf_token,
            ui_title=request.ui_title,
            ui_subtitle=request.ui_subtitle
        )

        if not result or not result.get('success'):
            raise HTTPException(
                status_code=500,
                detail=result.get('message', 'Failed to generate phone number') if result else 'Unknown error'
            )

        logger.info(f"✅ Phone generated: {result['number']}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to generate test phone: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/launch-ui")
async def launch_shareable_test_ui(request: LaunchUIRequest):
    """
    Launch a shareable Gradio UI for testing an assistant using FastRTC's .ui.launch().

    Creates a public shareable link (e.g., https://random-id.gradio.live) that can be
    shared with team members or clients for quick testing.

    **Requirements:**
    - FastRTC installed with: pip install 'fastrtc[vad,tts]'
    - Internet connection (for public shareable links)

    **Example Response:**
    ```json
    {
        "success": true,
        "url": "https://abc123.gradio.live",
        "local_url": "http://localhost:7860",
        "message": "Shareable UI launched successfully",
        "expires_in_hours": 72
    }
    ```

    **Features:**
    - Click "Start" to begin testing
    - Automatic voice detection and turn-taking
    - Low latency (<50ms audio chunks)
    - Barge-in support (interrupt anytime)
    - Link expires in 72 hours

    **Usage:**
    - Share the URL with anyone
    - No authentication required
    - Works on any device with browser
    - Perfect for quick demos
    """
    if not FASTRTC_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="FastRTC not available. Install with: pip install 'fastrtc[vad,tts]'"
        )

    try:
        logger.info(f"🚀 Launching shareable UI for assistant: {request.assistant_id}")

        # Use shared service
        result = launch_shareable_ui(
            assistant_id=request.assistant_id,
            ui_title=request.ui_title,
            ui_subtitle=request.ui_subtitle,
            share=request.share
        )

        if not result or not result.get('success'):
            raise HTTPException(
                status_code=500,
                detail=result.get('message', 'Failed to launch UI') if result else 'Unknown error'
            )

        # Add expiration info
        result['expires_in_hours'] = 72 if request.share else None

        logger.info(f"✅ UI launched: {result.get('url')}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to launch UI: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_testing_status():
    """
    Check if assistant testing features are available.

    Returns:
        dict: Status of FastRTC and required environment variables
    """
    hf_token = os.getenv('HUGGINGFACE_TOKEN') or os.getenv('HF_TOKEN')

    return {
        "fastrtc_available": FASTRTC_AVAILABLE,
        "huggingface_token_set": bool(hf_token),
        "features": {
            "test_phone": FASTRTC_AVAILABLE and bool(hf_token),
            "shareable_ui": FASTRTC_AVAILABLE
        },
        "requirements": {
            "fastrtc": "pip install 'fastrtc[vad,tts]'",
            "huggingface_token": "Set HUGGINGFACE_TOKEN environment variable"
        }
    }


@router.get("/assistant/{assistant_id}/testing-info")
async def get_assistant_testing_info(assistant_id: str):
    """
    Get testing information for a specific assistant.

    Returns current test phone number, shareable link, and expiration times.

    Args:
        assistant_id: Assistant ID

    Returns:
        dict: Testing information including phone number, shareable link, etc.
    """
    # TODO: Fetch from database (Assistant model)
    # For now, return placeholder
    return {
        "assistant_id": assistant_id,
        "test_phone": {
            "number": None,
            "country": None,
            "expires_at": None,
            "active": False
        },
        "shareable_link": {
            "url": None,
            "expires_at": None,
            "active": False
        },
        "message": "No active testing resources for this assistant"
    }
