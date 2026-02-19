#!/usr/bin/env python3
"""
Speech-to-Speech Comparison API
Provides endpoints to test both implementations:
1. Our custom VoicePipeline
2. HF Speech-to-Speech approach

Allows side-by-side comparison of performance, quality, and features.
Includes FastRTC endpoints for real-time testing.
"""

import logging
import asyncio
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, FastAPI
from pydantic import BaseModel
from typing import Optional, Literal

# Import both implementations
from apps.shared.integration.voice_pipeline import VoicePipeline
from apps.shared.integration.hf_speech_to_speech import (
    HFSpeechToSpeechPipeline,
    HF_S2S_AVAILABLE
)
from apps.shared.integration.webrtc import create_webrtc_stream, FASTRTC_AVAILABLE

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/speech-to-speech", tags=["speech-to-speech"])


class ComparisonRequest(BaseModel):
    """Request for speech-to-speech comparison."""
    assistant_id: str
    audio_base64: str  # Base64 encoded audio (PCM float32)
    sample_rate: int = 16000
    implementation: Literal["custom", "hf", "both"] = "both"


class ComparisonResponse(BaseModel):
    """Response with comparison results."""
    custom_result: Optional[dict] = None
    hf_result: Optional[dict] = None
    comparison: Optional[dict] = None


@router.post("/compare", response_model=ComparisonResponse)
async def compare_implementations(request: ComparisonRequest):
    """
    Compare custom VoicePipeline vs HF Speech-to-Speech.

    This endpoint processes audio through both implementations
    and returns results for comparison.

    Args:
        request: Comparison request with audio and config

    Returns:
        Results from both implementations
    """
    import base64
    import time

    logger.info(
        f"🔄 Comparison request | "
        f"Assistant: {request.assistant_id} | "
        f"Mode: {request.implementation}"
    )

    # Decode audio
    try:
        audio_bytes = base64.b64decode(request.audio_base64)
        audio_data = np.frombuffer(audio_bytes, dtype=np.float32)
        logger.info(f"📊 Audio decoded: {len(audio_data)} samples")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid audio data: {e}")

    results = {}

    # Test Custom Implementation
    if request.implementation in ["custom", "both"]:
        logger.info("🚀 Testing Custom VoicePipeline...")
        custom_start = time.time()

        try:
            pipeline = VoicePipeline(
                assistant_id=request.assistant_id,
                pause_threshold_ms=1500,
                sample_rate=request.sample_rate
            )

            # Create audio stream
            async def audio_stream():
                yield audio_data.tobytes()

            # Collect results
            custom_messages = []
            async for message in pipeline.process_turn(audio_stream()):
                custom_messages.append(message)

            custom_duration = time.time() - custom_start

            results["custom_result"] = {
                "implementation": "custom",
                "duration": custom_duration,
                "messages": custom_messages,
                "transcription": next(
                    (m["data"]["text"] for m in custom_messages if m["type"] == "transcription"),
                    None
                ),
                "response": next(
                    (m["data"] for m in custom_messages if m["type"] == "text_response"),
                    None
                ),
                "audio_chunks": len([m for m in custom_messages if m["type"] == "audio_chunk"])
            }

            logger.info(f"✅ Custom complete in {custom_duration:.2f}s")

        except Exception as e:
            logger.error(f"❌ Custom pipeline error: {e}", exc_info=True)
            results["custom_result"] = {
                "implementation": "custom",
                "error": str(e)
            }

    # Test HF Implementation
    if request.implementation in ["hf", "both"]:
        logger.info("🎯 Testing HF Speech-to-Speech...")
        hf_start = time.time()

        try:
            pipeline = HFSpeechToSpeechPipeline(
                assistant_id=request.assistant_id,
                stt_model="base",
                tts_model="parler"
            )

            # Collect results
            hf_messages = []
            async for message in pipeline.process_audio(audio_data, request.sample_rate):
                hf_messages.append(message)

            hf_duration = time.time() - hf_start

            results["hf_result"] = {
                "implementation": "hf",
                "duration": hf_duration,
                "messages": hf_messages,
                "transcription": next(
                    (m["data"]["text"] for m in hf_messages if m["type"] == "transcription"),
                    None
                ),
                "response": next(
                    (m["data"] for m in hf_messages if m["type"] == "text_response"),
                    None
                ),
                "audio_chunks": len([m for m in hf_messages if m["type"] == "audio_chunk"])
            }

            logger.info(f"✅ HF complete in {hf_duration:.2f}s")

        except Exception as e:
            logger.error(f"❌ HF pipeline error: {e}", exc_info=True)
            results["hf_result"] = {
                "implementation": "hf",
                "error": str(e)
            }

    # Generate comparison
    if "custom_result" in results and "hf_result" in results:
        custom = results["custom_result"]
        hf = results["hf_result"]

        results["comparison"] = {
            "custom_faster": custom.get("duration", 999) < hf.get("duration", 999),
            "duration_difference": abs(
                custom.get("duration", 0) - hf.get("duration", 0)
            ),
            "both_succeeded": (
                "error" not in custom and
                "error" not in hf
            ),
            "transcriptions_match": (
                custom.get("transcription") == hf.get("transcription")
            ),
            "audio_chunks_difference": abs(
                custom.get("audio_chunks", 0) - hf.get("audio_chunks", 0)
            )
        }

    return ComparisonResponse(**results)


@router.websocket("/ws/custom/{assistant_id}")
async def websocket_custom(websocket: WebSocket, assistant_id: str):
    """
    WebSocket for real-time custom VoicePipeline testing.

    Send audio chunks and receive streaming responses.
    """
    await websocket.accept()
    logger.info(f"🔌 Custom WebSocket connected: {assistant_id}")

    try:
        pipeline = VoicePipeline(
            assistant_id=assistant_id,
            pause_threshold_ms=1500,
            sample_rate=16000
        )

        while True:
            # Receive audio data
            data = await websocket.receive_bytes()
            audio_data = np.frombuffer(data, dtype=np.float32)

            # Create audio stream
            async def audio_stream():
                yield audio_data.tobytes()

            # Process and send results
            async for message in pipeline.process_turn(audio_stream()):
                await websocket.send_json(message)

    except WebSocketDisconnect:
        logger.info(f"🔌 Custom WebSocket disconnected: {assistant_id}")
    except Exception as e:
        logger.error(f"❌ Custom WebSocket error: {e}", exc_info=True)
        await websocket.close(code=1011, reason=str(e))


@router.websocket("/ws/hf/{assistant_id}")
async def websocket_hf(websocket: WebSocket, assistant_id: str):
    """
    WebSocket for real-time HF Speech-to-Speech testing.

    Send audio chunks and receive streaming responses.
    """
    await websocket.accept()
    logger.info(f"🔌 HF WebSocket connected: {assistant_id}")

    try:
        pipeline = HFSpeechToSpeechPipeline(
            assistant_id=assistant_id,
            stt_model="base",
            tts_model="parler"
        )

        while True:
            # Receive audio data
            data = await websocket.receive_bytes()
            audio_data = np.frombuffer(data, dtype=np.float32)

            # Process and send results
            async for message in pipeline.process_audio(audio_data, 16000):
                await websocket.send_json(message)

    except WebSocketDisconnect:
        logger.info(f"🔌 HF WebSocket disconnected: {assistant_id}")
    except Exception as e:
        logger.error(f"❌ HF WebSocket error: {e}", exc_info=True)
        await websocket.close(code=1011, reason=str(e))


@router.get("/status")
async def get_status():
    """
    Get status of both implementations.

    Returns availability and configuration info.
    """
    return {
        "custom": {
            "available": True,
            "name": "Custom VoicePipeline",
            "description": "Our optimized implementation with 20+ TTS providers",
            "features": [
                "Streaming TTS",
                "20+ TTS providers",
                "Voice cloning",
                "Multi-language",
                "Production-tested"
            ]
        },
        "hf": {
            "available": HF_S2S_AVAILABLE,
            "name": "HuggingFace Speech-to-Speech",
            "description": "Reference implementation from HF",
            "features": [
                "Modular architecture",
                "Parler-TTS",
                "MeloTTS support",
                "ChatTTS support",
                "Open source"
            ]
        }
    }


def setup_fastrtc_comparison(app: FastAPI, assistant_id: str = "default-assistant"):
    """
    Setup FastRTC streams for real-time speech-to-speech comparison.

    Creates two FastRTC endpoints:
    - /speech-to-speech/webrtc/custom - Custom VoicePipeline implementation
    - /speech-to-speech/webrtc/hf - HuggingFace implementation

    Both use the same assistant_id for fair comparison.

    Args:
        app: FastAPI application instance
        assistant_id: Assistant ID to use for both implementations

    Returns:
        True if setup successful, False otherwise
    """
    if not FASTRTC_AVAILABLE:
        logger.warning("⚠️ FastRTC not available - skipping WebRTC comparison setup")
        return False

    logger.info(f"🚀 Setting up FastRTC comparison for assistant: {assistant_id}")

    # Create Custom VoicePipeline stream
    custom_stream = create_webrtc_stream(
        assistant_id=assistant_id,
        pause_threshold_ms=1500,
        sample_rate=16000,
        ui_title="🚀 Custom VoicePipeline",
        ui_subtitle="Our optimized implementation with 20+ TTS providers"
    )

    if custom_stream:
        custom_stream.mount(app, path="/speech-to-speech/webrtc/custom")
        logger.info("✅ Custom VoicePipeline FastRTC mounted at /speech-to-speech/webrtc/custom")

    # Create HF Speech-to-Speech stream
    if HF_S2S_AVAILABLE:
        hf_stream = create_webrtc_stream(
            assistant_id=assistant_id,
            pause_threshold_ms=1500,
            sample_rate=16000,
            ui_title="🎯 HF Speech-to-Speech",
            ui_subtitle="HuggingFace reference implementation"
        )

        if hf_stream:
            hf_stream.mount(app, path="/speech-to-speech/webrtc/hf")
            logger.info("✅ HF Speech-to-Speech FastRTC mounted at /speech-to-speech/webrtc/hf")
    else:
        logger.warning("⚠️ HF Speech-to-Speech not available - skipping HF FastRTC setup")

    return True


# Export router and setup function
__all__ = ['router', 'setup_fastrtc_comparison']
