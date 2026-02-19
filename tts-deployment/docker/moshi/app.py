"""
Kyutai Moshi Real-Time Conversational AI API

Moshi is a real-time, full-duplex spoken dialogue framework from Kyutai Labs.
It provides ultra-low latency bidirectional conversation with simultaneous speaking/listening.
"""

import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import torch
import uvicorn
from typing import Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Kyutai Moshi API",
    description="Real-time conversational AI with full-duplex spoken dialogue",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model references
moshi_lm = None
mimi_model = None
device = None

@app.on_event("startup")
async def startup_event():
    """Initialize Moshi models on startup."""
    global moshi_lm, mimi_model, device

    try:
        # Determine device
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")

        if device == "cuda":
            logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
            logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")

        # Import moshi
        from moshi.models import get_moshi_lm, get_mimi
        from huggingface_hub import hf_hub_download

        logger.info(f"HuggingFace cache location: {os.environ.get('HF_HOME', '/app/cache/huggingface')}")

        # Download Moshi LM model (language model)
        logger.info("Loading Moshi LM model from HuggingFace (kyutai/moshiko-pytorch-bf16)...")
        logger.info("This may take 10-15 minutes on first run (downloading ~15GB)...")
        moshi_weight = hf_hub_download(
            repo_id="kyutai/moshiko-pytorch-bf16",
            filename="model.safetensors"
        )
        logger.info(f"Moshi LM model downloaded to: {moshi_weight}")

        # Download Mimi model (audio codec)
        logger.info("Loading Mimi model from HuggingFace (kyutai/moshika-pytorch-bf16)...")
        mimi_weight = hf_hub_download(
            repo_id="kyutai/moshika-pytorch-bf16",
            filename="model.safetensors"
        )
        logger.info(f"Mimi model downloaded to: {mimi_weight}")

        # Load Moshi LM model
        logger.info("Loading Moshi LM model into GPU memory...")
        moshi_lm = get_moshi_lm(
            filename=moshi_weight,
            device=device,
            dtype=torch.bfloat16
        )
        logger.info("Moshi LM model loaded successfully!")

        # Load Mimi model
        logger.info("Loading Mimi audio codec model...")
        mimi_model = get_mimi(
            filename=mimi_weight,
            device=device
        )
        logger.info("Mimi model loaded successfully!")

        # Log GPU memory usage
        if device == "cuda":
            logger.info(f"GPU Memory Allocated: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")
            logger.info(f"GPU Memory Reserved: {torch.cuda.memory_reserved(0) / 1024**3:.2f} GB")

        logger.info("All Moshi models loaded and ready for inference!")

    except Exception as e:
        logger.error(f"Failed to load Moshi models: {e}", exc_info=True)
        logger.error("Moshi will not be available for inference")
        moshi_lm = None
        mimi_model = None

@app.get("/")
async def root():
    """Service information endpoint."""
    return {
        "service": "Kyutai Moshi",
        "version": "1.0.0",
        "model": "Moshiko (7B) + Moshika (Mimi Audio Codec)",
        "status": "online" if (moshi_lm is not None and mimi_model is not None) else "model_loading_failed",
        "description": "Real-time conversational AI with full-duplex spoken dialogue",
        "features": [
            "Real-time bidirectional conversation",
            "Simultaneous speaking and listening",
            "Ultra-low latency (<200ms)",
            "Streaming audio I/O via Mimi codec",
            "Natural conversation flow",
            "Interrupt handling"
        ],
        "models": {
            "moshi_lm": "kyutai/moshiko-pytorch-bf16 (Language Model)",
            "mimi": "kyutai/moshika-pytorch-bf16 (Audio Codec)"
        },
        "endpoints": {
            "/": "Service information",
            "/health": "Health check",
            "/ws/conversation": "WebSocket endpoint for real-time conversation",
            "/gpu_stats": "GPU statistics (if available)"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint with detailed status."""
    gpu_info = {}

    if torch.cuda.is_available():
        gpu_info = {
            "gpu_name": torch.cuda.get_device_name(0),
            "gpu_memory_allocated": f"{torch.cuda.memory_allocated(0) / 1024**3:.2f} GB",
            "gpu_memory_reserved": f"{torch.cuda.memory_reserved(0) / 1024**3:.2f} GB",
            "gpu_memory_total": f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB"
        }

    return {
        "status": "healthy" if (moshi_lm is not None and mimi_model is not None) else "degraded",
        "moshi_lm_loaded": moshi_lm is not None,
        "mimi_loaded": mimi_model is not None,
        "device": str(device),
        **gpu_info
    }

@app.get("/gpu_stats")
async def gpu_stats():
    """Get GPU statistics."""
    if not torch.cuda.is_available():
        raise HTTPException(status_code=503, detail="GPU not available")

    return {
        "gpu_name": torch.cuda.get_device_name(0),
        "gpu_count": torch.cuda.device_count(),
        "current_device": torch.cuda.current_device(),
        "memory_allocated": f"{torch.cuda.memory_allocated(0) / 1024**3:.2f} GB",
        "memory_reserved": f"{torch.cuda.memory_reserved(0) / 1024**3:.2f} GB",
        "memory_total": f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB",
        "memory_free": f"{(torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)) / 1024**3:.2f} GB"
    }

@app.websocket("/ws/conversation")
async def websocket_conversation(websocket: WebSocket):
    """
    WebSocket endpoint for real-time bidirectional conversation.

    Protocol:
    - Client sends audio chunks (bytes) - raw audio or Mimi-encoded
    - Server responds with audio chunks (bytes) - Mimi-encoded audio
    - Both can happen simultaneously (full-duplex)

    TODO: Implement actual Moshi inference pipeline:
    1. Receive audio from client
    2. Encode with Mimi codec
    3. Process with Moshi LM
    4. Decode response with Mimi
    5. Send audio back to client
    """
    await websocket.accept()

    if moshi_lm is None or mimi_model is None:
        await websocket.send_json({
            "error": "Models not loaded",
            "detail": "Moshi models failed to load at startup",
            "moshi_lm_loaded": moshi_lm is not None,
            "mimi_loaded": mimi_model is not None
        })
        await websocket.close()
        return

    try:
        logger.info("WebSocket conversation started")

        # Conversation loop
        while True:
            # Receive audio from client
            audio_data = await websocket.receive_bytes()

            # TODO: Implement Moshi inference pipeline
            # For now, acknowledge receipt
            await websocket.send_json({
                "status": "processing",
                "message": "Moshi real-time inference pipeline not yet implemented",
                "received_bytes": len(audio_data),
                "note": "Full implementation requires audio streaming pipeline with Mimi codec"
            })

    except WebSocketDisconnect:
        logger.info("WebSocket conversation ended")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        await websocket.close()

if __name__ == "__main__":
    # Start server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8008,
        log_level="info"
    )
