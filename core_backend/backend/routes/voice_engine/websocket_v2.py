#!/usr/bin/env python3
"""
WebSocket v2: Voice Chat using VoicePipeline (Phase 3)

This is a simplified, cleaner WebSocket handler that uses VoicePipeline
to eliminate manual state machine complexity.

Comparison:
- WebSocket v1: 1500+ lines with manual state machine
- WebSocket v2: ~150 lines using VoicePipeline

Benefits:
- Cleaner code (10x reduction)
- Easier to maintain
- Consistent with WebRTC handler
- Future-proof architecture
"""

import logging
import base64
from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from apps.shared.integration.voice_pipeline import create_voice_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws/v2", tags=["websocket-v2"])

# Active connections
active_connections: Dict[str, WebSocket] = {}


@router.websocket("/voice-chat/{assistant_id}")
async def voice_chat_v2(websocket: WebSocket, assistant_id: str):
    """
    WebSocket v2 endpoint for real-time voice chat using VoicePipeline.

    Protocol:
    - Client sends:
        {"type": "pcm_chunk", "data": "base64_pcm_audio"}

    - Server sends:
        {"type": "transcription", "data": {"text": "...", "is_final": bool}}
        {"type": "text_response", "data": "..."}
        {"type": "audio_chunk", "data": "base64_wav"}
        {"type": "audio_complete", "data": {...}}
        {"type": "error", "data": "..."}
        {"type": "status", "data": "..."}

    Args:
        websocket: WebSocket connection
        assistant_id: ID of assistant to use
    """
    connection_id = f"{assistant_id}_{id(websocket)}"

    try:
        # Accept connection
        await websocket.accept()
        active_connections[connection_id] = websocket

        logger.info(f"✅ WebSocket v2 connection established for assistant: {assistant_id}")

        # Send welcome message
        await websocket.send_json({
            "type": "status",
            "data": "Connected - Using VoicePipeline (v2)"
        })

        # Create voice pipeline for this assistant
        pipeline = create_voice_pipeline(
            assistant_id=assistant_id,
            pause_threshold_ms=1500,
            sample_rate=16000
        )

        logger.info(f"🎵 VoicePipeline created for assistant: {assistant_id}")

        # Audio buffer for collecting PCM chunks before turn processing
        audio_buffer = []
        turn_in_progress = False

        # Main message loop
        while True:
            try:
                # Receive message from client
                message = await websocket.receive_json()
                message_type = message.get("type")
                message_data = message.get("data")

                if message_type == "pcm_chunk":
                    # Collect audio chunks
                    audio_buffer.append(message_data)
                    logger.debug(f"🎤 Received PCM chunk (buffer: {len(audio_buffer)} chunks)")

                elif message_type == "turn_complete":
                    # Process complete turn when client signals end of utterance
                    if audio_buffer and not turn_in_progress:
                        turn_in_progress = True

                        logger.info(f"🔄 Processing turn ({len(audio_buffer)} audio chunks)")

                        # Create audio stream generator
                        async def audio_stream():
                            for pcm_base64 in audio_buffer:
                                # Decode base64 to bytes
                                pcm_bytes = base64.b64decode(pcm_base64)
                                yield pcm_bytes

                        # Process turn through pipeline
                        try:
                            async for pipeline_message in pipeline.process_turn(audio_stream()):
                                # Forward pipeline message to WebSocket client
                                await websocket.send_json(pipeline_message)

                        except Exception as e:
                            logger.error(f"❌ Error processing turn: {e}")
                            await websocket.send_json({
                                "type": "error",
                                "data": str(e)
                            })

                        finally:
                            # Clear buffer and reset turn flag
                            audio_buffer.clear()
                            turn_in_progress = False

                            # Notify client ready for next turn
                            await websocket.send_json({
                                "type": "ready_for_turn",
                                "data": "Ready for next utterance"
                            })

                elif message_type == "reset":
                    # Reset pipeline for new conversation
                    pipeline.reset()
                    audio_buffer.clear()
                    turn_in_progress = False

                    await websocket.send_json({
                        "type": "status",
                        "data": "Pipeline reset - ready for new conversation"
                    })

                elif message_type == "ping":
                    # Keep-alive ping
                    await websocket.send_json({
                        "type": "pong",
                        "data": "alive"
                    })

                else:
                    logger.warning(f"⚠️ Unknown message type: {message_type}")
                    await websocket.send_json({
                        "type": "error",
                        "data": f"Unknown message type: {message_type}"
                    })

            except WebSocketDisconnect:
                logger.info(f"📴 WebSocket disconnected: {connection_id}")
                break

            except Exception as e:
                logger.error(f"❌ Error in message loop: {e}")
                import traceback
                traceback.print_exc()

                try:
                    await websocket.send_json({
                        "type": "error",
                        "data": str(e)
                    })
                except:
                    break

    except Exception as e:
        logger.error(f"❌ WebSocket connection error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up connection
        if connection_id in active_connections:
            del active_connections[connection_id]

        logger.info(f"🔌 WebSocket connection closed: {connection_id}")


# Export router
__all__ = ['router']
