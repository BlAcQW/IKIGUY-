"""
Kyutai Moshi FastAPI Server
Real-time conversational AI with speech-to-speech capabilities
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import torch
import io
import logging
import asyncio
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Kyutai Moshi API", version="1.0.0")

# Initialize
device = 'cuda' if torch.cuda.is_available() else 'cpu'
logger.info(f"Using device: {device}")

# Load Moshi model
model = None
try:
    # TODO: Import and load Moshi model
    # from moshi import load_moshi
    # model = load_moshi(device=device)
    logger.info("Moshi model initialization (placeholder)")
except Exception as e:
    logger.error(f"Error loading model: {e}")


class ConversationRequest(BaseModel):
    """Conversation request model."""
    text: str
    conversation_id: str = None
    context: list = []


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Kyutai Moshi",
        "version": "1.0.0",
        "status": "running",
        "description": "Real-time conversational AI"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    gpu_info = {}
    if torch.cuda.is_available():
        gpu_info = {
            "gpu_name": torch.cuda.get_device_name(0),
            "gpu_memory_allocated_gb": f"{torch.cuda.memory_allocated(0) / 1024**3:.2f}",
            "gpu_memory_total_gb": f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f}"
        }

    return {
        "status": "healthy",
        "device": device,
        "model_loaded": model is not None,
        **gpu_info
    }


@app.post("/converse")
async def converse(request: ConversationRequest):
    """
    Single-turn conversation endpoint.

    Args:
        request: Conversation request with text and context

    Returns:
        Response text and audio
    """
    try:
        logger.info(f"Conversation: '{request.text[:50]}...'")

        # TODO: Implement Moshi conversation
        # response = model.generate_response(
        #     request.text,
        #     context=request.context
        # )

        raise HTTPException(
            status_code=501,
            detail="Moshi conversation not yet implemented - model integration pending"
        )

    except Exception as e:
        logger.error(f"Conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/conversation")
async def websocket_conversation(websocket: WebSocket):
    """
    WebSocket endpoint for real-time bidirectional conversation.

    Supports:
    - Streaming audio input from user
    - Streaming audio/text output from Moshi
    - Real-time interruption handling
    """
    await websocket.accept()
    conversation_id = id(websocket)
    logger.info(f"WebSocket conversation started: {conversation_id}")

    try:
        # Initialize conversation state
        conversation_state = {
            "history": [],
            "active": True
        }

        while conversation_state["active"]:
            try:
                # Receive data from client
                data = await websocket.receive()

                if "text" in data:
                    # Handle text input
                    message = data["text"]
                    logger.info(f"Received text: {message}")

                    # TODO: Process with Moshi
                    # response = await model.generate_response_async(
                    #     message,
                    #     conversation_state
                    # )

                    await websocket.send_json({
                        "type": "text",
                        "content": "Moshi response placeholder",
                        "status": "not_implemented"
                    })

                elif "bytes" in data:
                    # Handle audio input
                    audio_data = data["bytes"]
                    logger.info(f"Received audio: {len(audio_data)} bytes")

                    # TODO: Process audio with Moshi
                    # 1. Transcribe audio
                    # 2. Generate response
                    # 3. Synthesize response audio
                    # 4. Stream back

                    await websocket.send_json({
                        "type": "audio",
                        "status": "not_implemented"
                    })

                elif "json" in data:
                    # Handle JSON commands
                    message = json.loads(data["json"])

                    if message.get("command") == "end":
                        conversation_state["active"] = False
                        await websocket.send_json({
                            "type": "status",
                            "content": "conversation_ended"
                        })
                        break

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {conversation_id}")
                break

            except Exception as e:
                logger.error(f"Error in conversation loop: {e}")
                await websocket.send_json({
                    "type": "error",
                    "content": str(e)
                })

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info(f"WebSocket conversation ended: {conversation_id}")


@app.get("/gpu_stats")
async def gpu_stats():
    """Get GPU utilization statistics."""
    if not torch.cuda.is_available():
        return {"error": "CUDA not available"}

    return {
        "device_count": torch.cuda.device_count(),
        "current_device": torch.cuda.current_device(),
        "device_name": torch.cuda.get_device_name(0),
        "memory_allocated_gb": torch.cuda.memory_allocated(0) / 1024**3,
        "memory_reserved_gb": torch.cuda.memory_reserved(0) / 1024**3,
        "memory_total_gb": torch.cuda.get_device_properties(0).total_memory / 1024**3
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
