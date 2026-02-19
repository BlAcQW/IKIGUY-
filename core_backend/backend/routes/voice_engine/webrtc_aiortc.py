#!/usr/bin/env python3
"""
Manual WebRTC Voice Chat using aiortc
Supports dynamic assistant IDs with full control over WebRTC lifecycle.

This replaces FastRTC entirely - we implement WebRTC from scratch using aiortc.
"""

import logging
import asyncio
import json
import uuid
import numpy as np
import io
import wave
import base64
from typing import Optional, Dict
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCDataChannel
from aiortc.contrib.media import MediaStreamTrack

from apps.core_backend.backend.services.assistant_service import assistant_service
from apps.shared.integration.voice_pipeline import VoicePipeline
from apps.shared.utils.redis_session_store import session_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice/webrtc", tags=["webrtc"])

# Active peer connections (in-memory, fast access)
active_peers: Dict[str, RTCPeerConnection] = {}


class WebRTCOfferRequest(BaseModel):
    """WebRTC SDP offer from client"""
    sdp: str
    type: str  # Should be "offer"
    assistant_id: str
    # Optional provider overrides from voice settings
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    tts_provider: Optional[str] = None
    stt_provider: Optional[str] = None
    language: Optional[str] = None


class WebRTCAnswerResponse(BaseModel):
    """WebRTC SDP answer to client"""
    sdp: str
    type: str  # Will be "answer"
    session_id: str


class AudioOutputTrack(MediaStreamTrack):
    """
    Custom audio track that streams TTS audio to client.

    This receives audio from the VoicePipeline and streams it
    via WebRTC to the client's speakers.
    """
    kind = "audio"

    def __init__(self):
        super().__init__()
        self.queue = asyncio.Queue()
        logger.info("🔊 Audio output track created")

    async def recv(self):
        """
        Receive next audio frame.

        Called by WebRTC to get audio data for streaming.
        """
        frame = await self.queue.get()
        return frame

    async def send_audio(self, audio_data: np.ndarray):
        """
        Send audio data to the track queue.

        Args:
            audio_data: Audio samples as numpy array
        """
        # Convert to audio frame format expected by WebRTC
        # TODO: Implement proper audio frame conversion
        await self.queue.put(audio_data)


async def get_user_id_from_token(authorization: Optional[str] = None) -> str:
    """
    Extract user ID from authorization header.

    Args:
        authorization: Bearer token from request header

    Returns:
        User ID or "anonymous"
    """
    # TODO: Implement proper JWT token parsing
    # For now, return anonymous
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        # Parse JWT and extract user_id
        # This is a placeholder - implement proper JWT parsing
        return "user_from_token"

    return "anonymous"


@router.post("/offer", response_model=WebRTCAnswerResponse)
async def handle_webrtc_offer(
    offer: WebRTCOfferRequest,
    user_id: str = Depends(get_user_id_from_token)
):
    """
    Handle WebRTC SDP offer with dynamic assistant support.

    Flow:
    1. Validate assistant exists
    2. Check connection limits (Redis)
    3. Create RTCPeerConnection
    4. Set remote description (offer)
    5. Create answer
    6. Set local description (answer)
    7. Setup data channel for control messages
    8. Stream first message if configured
    9. Return SDP answer

    Args:
        offer: WebRTC offer with SDP and assistant_id
        user_id: Extracted from JWT token

    Returns:
        WebRTC answer with SDP and session_id

    Raises:
        HTTPException: If validation fails or limits exceeded
    """
    try:
        logger.info(f"📞 WebRTC offer received | User: {user_id} | Assistant: {offer.assistant_id}")

        # 1. Validate assistant exists
        assistant = assistant_service.get_assistant(offer.assistant_id)
        if not assistant:
            logger.error(f"❌ Assistant not found: {offer.assistant_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Assistant {offer.assistant_id} not found"
            )

        logger.info(f"✅ Found assistant: {assistant.name}")

        # 2. Check connection limits
        can_connect, error_msg = await session_store.can_create_connection(user_id)
        if not can_connect:
            logger.warning(f"⚠️ Connection limit exceeded for {user_id}: {error_msg}")
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "too_many_connections",
                    "message": error_msg
                }
            )

        # 3. Create RTCPeerConnection
        peer_connection = RTCPeerConnection()
        session_id = str(uuid.uuid4())

        logger.info(f"🔗 Created peer connection | Session: {session_id}")

        # 4. Create VoicePipeline for this assistant
        # Use provider overrides from voice settings if provided
        pipeline_kwargs = {
            "assistant_id": offer.assistant_id,
            "pause_threshold_ms": 1500,
            "sample_rate": 16000
        }
        if offer.llm_provider:
            pipeline_kwargs["llm_provider"] = offer.llm_provider
        if offer.llm_model:
            pipeline_kwargs["llm_model"] = offer.llm_model
        if offer.tts_provider:
            pipeline_kwargs["tts_provider"] = offer.tts_provider
        if offer.stt_provider:
            pipeline_kwargs["stt_provider"] = offer.stt_provider
        if offer.language:
            pipeline_kwargs["language"] = offer.language
        
        logger.info(f"🎵 Creating VoicePipeline with overrides: {pipeline_kwargs}")
        pipeline = VoicePipeline(**pipeline_kwargs)

        # 5. Setup data channel for control messages
        data_channel: Optional[RTCDataChannel] = None

        @peer_connection.on("datachannel")
        def on_datachannel(channel: RTCDataChannel):
            """Handle data channel from client"""
            nonlocal data_channel
            data_channel = channel
            logger.info(f"📡 Data channel received: {channel.label} | Ready state: {channel.readyState}")

            # If channel is already open, stream immediately
            # Otherwise, wait for open event
            if channel.readyState == "open":
                logger.info(f"✅ Data channel already open: {channel.label}")
                try:
                    # Stream first message immediately
                    asyncio.create_task(stream_first_message_via_datachannel(
                        channel,
                        pipeline,
                        user_id
                    ))
                except Exception as e:
                    logger.error(f"❌ Error starting first message stream: {e}", exc_info=True)
            else:
                # Channel not open yet, wait for open event
                @channel.on("open")
                def on_open():
                    """Data channel is now open - stream first message"""
                    logger.info(f"✅ Data channel opened: {channel.label}")

                    try:
                        # Stream first message when data channel is ready
                        asyncio.create_task(stream_first_message_via_datachannel(
                            channel,
                            pipeline,
                            user_id
                        ))
                    except Exception as e:
                        logger.error(f"❌ Error starting first message stream: {e}", exc_info=True)

            @channel.on("message")
            async def on_message(message):
                """Handle messages from client"""
                try:
                    data = json.loads(message)
                    msg_type = data.get("type")

                    if msg_type == "start_recording":
                        logger.info("🎤 Client started recording")
                    elif msg_type == "stop_recording":
                        logger.info("🛑 Client stopped recording")
                    elif msg_type == "barge_in":
                        logger.info("🚫 Client barge-in (interrupt)")
                    else:
                        logger.debug(f"📨 Client message: {msg_type}")

                except Exception as e:
                    logger.error(f"❌ Error handling data channel message: {e}")

        # 6. Setup connection state handlers
        @peer_connection.on("connectionstatechange")
        async def on_connectionstatechange():
            """Handle connection state changes"""
            state = peer_connection.connectionState
            ice_state = peer_connection.iceConnectionState
            logger.info(
                f"🔌 Connection state: {state} | "
                f"ICE state: {ice_state} | "
                f"Session: {session_id}"
            )

            if state == "connected":
                logger.info(f"✅ WebRTC connected | Session: {session_id}")
                logger.info(f"🔍 Data channel status: {data_channel}")
                # First message will be streamed when data channel opens

            elif state in ["failed", "closed"]:
                logger.warning(
                    f"🔌 Connection {state} | "
                    f"ICE: {ice_state} | "
                    f"Session: {session_id}"
                )
                await cleanup_session(session_id)

        @peer_connection.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            """Handle ICE connection state changes"""
            ice_state = peer_connection.iceConnectionState
            logger.info(f"🧊 ICE state: {ice_state} | Session: {session_id}")

        @peer_connection.on("track")
        def on_track(track):
            """Handle incoming audio track from client (microphone)"""
            logger.info(f"🎤 Received audio track from client: {track.kind}")

            if track.kind == "audio":
                # Start consuming the track to keep connection alive
                # In aiortc, tracks MUST be consumed or connection closes!
                async def consume_audio():
                    """Consume audio frames to keep track alive"""
                    logger.info(f"🎧 Starting to consume audio track...")
                    frame_count = 0
                    try:
                        while peer_connection.connectionState != "closed":
                            try:
                                frame = await track.recv()
                                frame_count += 1
                                if frame_count % 100 == 0:
                                    logger.debug(f"🎧 Consumed {frame_count} audio frames")
                                # TODO: Process frame through VoicePipeline for VAD + STT
                                # For now, just consume to keep connection alive
                            except Exception as e:
                                # Check if connection is still alive
                                if peer_connection.connectionState == "closed":
                                    logger.info(f"🎧 Track ended (connection closed)")
                                    break
                                else:
                                    logger.warning(f"Track recv error (connection still open): {e}")
                                    await asyncio.sleep(0.1)  # Brief pause before retry
                    except Exception as e:
                        logger.error(f"❌ Error in audio consumption loop: {e}", exc_info=True)
                    finally:
                        logger.info(f"🎧 Audio track consumption ended | Frames: {frame_count}")

                # Start consuming in background
                asyncio.create_task(consume_audio())

        # 7. Set remote description (client's offer)
        await peer_connection.setRemoteDescription(
            RTCSessionDescription(sdp=offer.sdp, type=offer.type)
        )

        logger.info("📝 Set remote description (offer)")

        # 8. Create answer
        answer = await peer_connection.createAnswer()
        await peer_connection.setLocalDescription(answer)

        logger.info("📝 Created and set local description (answer)")

        # 9. Store peer connection and register session
        active_peers[session_id] = peer_connection

        await session_store.register_connection(
            session_id=session_id,
            user_id=user_id,
            assistant_id=offer.assistant_id,
            metadata={
                "assistant_name": assistant.name,
                "connection_state": "connecting"
            }
        )

        logger.info(f"✅ WebRTC session created | Session: {session_id}")

        # 10. Return SDP answer
        return WebRTCAnswerResponse(
            sdp=peer_connection.localDescription.sdp,
            type=peer_connection.localDescription.type,
            session_id=session_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error handling WebRTC offer: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process WebRTC offer: {str(e)}"
        )


async def stream_first_message_via_datachannel(
    channel: Optional[RTCDataChannel],
    pipeline: VoicePipeline,
    user_id: str
):
    """
    Stream first message via data channel (like FastRTC startup_fn).

    This is the PROPER implementation - streams audio chunks in real-time
    as they're generated, NOT pre-generated.

    Args:
        channel: WebRTC data channel
        pipeline: VoicePipeline for the assistant
        user_id: User identifier for billing
    """
    if not channel:
        logger.warning("⚠️ No data channel available for first message")
        return

    try:
        logger.info("🎬 Streaming first message via data channel...")

        chunk_count = 0
        start_time = datetime.now()
        first_chunk_time = None

        # Stream chunks in real-time as they're generated
        async for message in pipeline.send_first_message(user_id=user_id):
            message_type = message["type"]

            if message_type == "text_response":
                # Send text response to frontend
                if channel.readyState == "open":
                    channel.send(json.dumps({
                        "type": "text_response",
                        "data": message["data"]
                    }))
                    logger.info(f"💬 First message text sent: '{message['data'][:50]}...'")
                else:
                    logger.warning(f"⚠️ Cannot send text - channel state: {channel.readyState}")
                    break  # Stop streaming if channel closed

            elif message_type == "audio_chunk":
                chunk_count += 1

                # Record first chunk latency
                if first_chunk_time is None:
                    first_chunk_time = (datetime.now() - start_time).total_seconds()
                    logger.info(f"⚡ First audio chunk latency: {first_chunk_time:.3f}s")

                # Send audio chunk immediately via data channel (real-time streaming!)
                if channel.readyState == "open":
                    channel.send(json.dumps({
                        "type": "audio_chunk",
                        "data": message["data"]
                    }))
                    logger.debug(f"🔊 Streamed audio chunk #{chunk_count}")
                else:
                    logger.warning(f"⚠️ Cannot send audio chunk - channel state: {channel.readyState}")
                    break  # Stop streaming if channel closed

            elif message_type == "audio_complete":
                # Notify completion
                total_time = (datetime.now() - start_time).total_seconds()
                if channel.readyState == "open":
                    channel.send(json.dumps({
                        "type": "audio_complete",
                        "data": {
                            "chunks": chunk_count,
                            "first_chunk_latency": first_chunk_time,
                            "total_duration": total_time
                        }
                    }))
                    logger.info(
                        f"✅ First message streaming complete | "
                        f"Chunks: {chunk_count} | "
                        f"First chunk: {first_chunk_time:.3f}s | "
                        f"Total: {total_time:.3f}s"
                    )
                else:
                    logger.warning(f"⚠️ Cannot send completion - channel state: {channel.readyState}")

        # Signal ready for user input
        if channel.readyState == "open":
            channel.send(json.dumps({
                "type": "ready_to_listen",
                "data": "Your turn - speak now"
            }))

    except Exception as e:
        # FAIL LOUDLY - no silent fallbacks
        error_msg = f"First message streaming failed: {str(e)}"
        logger.error(f"❌ CRITICAL: {error_msg}", exc_info=True)

        # Send error to frontend so user sees it
        try:
            if channel.readyState == "open":
                channel.send(json.dumps({
                    "type": "error",
                    "data": error_msg
                }))
        except:
            pass  # Channel might be dead

        raise  # Re-raise to fail loudly


async def cleanup_session(session_id: str):
    """
    Cleanup WebRTC session resources.

    Args:
        session_id: Session identifier
    """
    try:
        # Close peer connection
        if session_id in active_peers:
            peer = active_peers.pop(session_id)
            await peer.close()
            logger.info(f"🔌 Closed peer connection: {session_id}")

        # Cleanup Redis session
        await session_store.cleanup_connection(session_id)

    except Exception as e:
        logger.error(f"❌ Error cleaning up session {session_id}: {e}")


@router.get("/stats")
async def get_webrtc_stats():
    """
    Get WebRTC connection statistics.

    Returns:
        Statistics about active connections
    """
    global_stats = await session_store.get_global_stats()

    return {
        **global_stats,
        "active_peers": len(active_peers),
        "timestamp": datetime.now().isoformat()
    }


@router.delete("/session/{session_id}")
async def close_session(session_id: str):
    """
    Manually close a WebRTC session.

    Args:
        session_id: Session identifier

    Returns:
        Success message
    """
    if session_id in active_peers:
        await cleanup_session(session_id)
        return {"message": "Session closed successfully", "session_id": session_id}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


# Export router
__all__ = ['router']
