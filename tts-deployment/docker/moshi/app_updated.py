"""
Kyutai Moshi FastAPI Server
Real-time conversational AI with speech-to-speech capabilities
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import torch
import io
import logging
import asyncio
import json
import traceback
from pathlib import Path
import os

# Import Moshi components
try:
    from moshi.models import loaders
    from moshi.run_inference import get_condition_tensors
    MOSHI_AVAILABLE = True
except ImportError:
    MOSHI_AVAILABLE = False
    loaders = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Kyutai Moshi API", version="1.0.0")

# Initialize
device = 'cuda' if torch.cuda.is_available() else 'cpu'
logger.info(f"Using device: {device}")

# Global model variables
model_lm = None
model_mimi = None
text_tokenizer = None
lm_gen = None
model_loaded = False
model_loading_error = None

async def load_models():
    """Load Moshi models asynchronously."""
    global model_lm, model_mimi, text_tokenizer, lm_gen, model_loaded, model_loading_error

    if not MOSHI_AVAILABLE:
        model_loading_error = "Moshi package not available"
        logger.error(model_loading_error)
        return

    try:
        logger.info("Starting Moshi model loading...")

        # Default HF repository
        hf_repo = os.environ.get('MOSHI_HF_REPO', 'kyutai/moshiko-pytorch-bf16')

        logger.info(f"Loading models from HuggingFace repository: {hf_repo}")

        # Load the models
        model_lm = loaders.load_model(
            hf_repo=hf_repo,
            device=device
        )

        # Load Mimi (audio codec)
        logger.info("Loading Mimi audio codec...")
        model_mimi = loaders.load_mimi(
            hf_repo='kyutai/moshika-pytorch-bf16',  # Mimi model repo
            device=device
        )

        # Load tokenizer
        logger.info("Loading tokenizer...")
        text_tokenizer = model_lm.text_tokenizer if hasattr(model_lm, 'text_tokenizer') else None

        # Setup generation
        cfg_coef = 1.0
        condition_tensors = get_condition_tensors('moshi', model_lm, batch_size=1, cfg_coef=cfg_coef)

        from moshi.models import LMGen
        lm_gen = LMGen(model_lm, cfg_coef=cfg_coef, condition_tensors=condition_tensors)

        model_loaded = True
        logger.info("✅ Moshi models loaded successfully!")

        # Log memory usage
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated(0) / 1024**3
            reserved = torch.cuda.memory_reserved(0) / 1024**3
            logger.info(f"GPU Memory - Allocated: {allocated:.2f}GB, Reserved: {reserved:.2f}GB")

    except Exception as e:
        model_loading_error = f"Error loading models: {str(e)}"
        logger.error(model_loading_error)
        logger.error(traceback.format_exc())


# Start model loading in background when server starts
@app.on_event("startup")
async def startup_event():
    """Load models on startup."""
    asyncio.create_task(load_models())


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
        "status": "running" if model_loaded else "loading",
        "description": "Real-time conversational AI with ultra-low latency",
        "capabilities": {
            "real_time": True,
            "full_duplex": True,
            "latency_ms": 200,
            "languages": ["en"],
            "websocket": "/ws/conversation"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    gpu_info = {}
    if torch.cuda.is_available():
        gpu_info = {
            "gpu_name": torch.cuda.get_device_name(0),
            "gpu_memory_allocated_gb": f"{torch.cuda.memory_allocated(0) / 1024**3:.2f}",
            "gpu_memory_reserved_gb": f"{torch.cuda.memory_reserved(0) / 1024**3:.2f}",
            "gpu_memory_total_gb": f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f}"
        }

    status = "healthy" if model_loaded else ("loading" if not model_loading_error else "error")

    return {
        "status": status,
        "device": device,
        "model_loaded": model_loaded,
        "moshi_available": MOSHI_AVAILABLE,
        "error": model_loading_error,
        **gpu_info
    }


@app.get("/gpu_stats")
async def gpu_stats():
    """Get detailed GPU statistics."""
    if not torch.cuda.is_available():
        return {"error": "CUDA not available"}

    return {
        "device_name": torch.cuda.get_device_name(0),
        "device_count": torch.cuda.device_count(),
        "current_device": torch.cuda.current_device(),
        "memory": {
            "allocated_gb": torch.cuda.memory_allocated(0) / 1024**3,
            "reserved_gb": torch.cuda.memory_reserved(0) / 1024**3,
            "total_gb": torch.cuda.get_device_properties(0).total_memory / 1024**3,
            "free_gb": (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)) / 1024**3
        },
        "utilization": torch.cuda.utilization() if hasattr(torch.cuda, 'utilization') else "N/A"
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
    if not model_loaded:
        raise HTTPException(
            status_code=503,
            detail=f"Models not loaded. Status: {model_loading_error or 'Loading in progress...'}"
        )

    try:
        logger.info(f"Conversation: '{request.text[:50]}...'")

        # TODO: Implement actual Moshi conversation logic here
        # This would use model_lm, model_mimi, and lm_gen

        raise HTTPException(
            status_code=501,
            detail="Single-turn conversation endpoint not fully implemented. Use WebSocket endpoint for real-time conversation."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/conversation")
async def websocket_conversation(websocket: WebSocket):
    """
    WebSocket endpoint for real-time bidirectional conversation.
    Full-duplex audio streaming with ultra-low latency.
    """
    await websocket.accept()

    if not model_loaded:
        await websocket.send_json({
            "type": "error",
            "message": f"Models not loaded. Status: {model_loading_error or 'Loading in progress...'}"
        })
        await websocket.close()
        return

    try:
        logger.info("WebSocket connection established for real-time conversation")

        # Send initial handshake
        await websocket.send_json({
            "type": "connected",
            "message": "Moshi real-time conversation ready"
        })

        # TODO: Implement full WebSocket conversation logic
        # This would handle:
        # - Incoming audio stream processing
        # - Model inference
        # - Outgoing audio stream generation
        # - Bidirectional communication

        while True:
            data = await websocket.receive()

            if data["type"] == "websocket.disconnect":
                break

            # Echo for now (placeholder)
            await websocket.send_json({
                "type": "info",
                "message": "WebSocket conversation handler not fully implemented"
            })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        logger.info("WebSocket connection closed")


if __name__ == "__main__":
    import uvicorn

    # Set environment variables for model loading
    os.environ['HF_HOME'] = '/workspace/.cache/huggingface'
    os.environ['TORCH_HOME'] = '/workspace/.cache/torch'

    uvicorn.run(app, host="0.0.0.0", port=8008, log_level="info")