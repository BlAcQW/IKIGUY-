FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3.10-dev \
    git \
    wget \
    curl \
    ffmpeg \
    libsndfile1 \
    espeak-ng \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip3 install --upgrade pip

# Install PyTorch with CUDA support first
# Reason: DeepSpeed requires specific PyTorch version with CUDA
RUN pip3 install torch==2.1.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu121

# Install DeepSpeed
# Reason: Provides 2-3x performance boost for XTTS v2 inference
# Using 0.12.6 for Pydantic v2 compatibility
RUN pip3 install deepspeed==0.12.6

# Install Coqui TTS
RUN pip3 install TTS

# Fix transformers version for XTTS v2 compatibility
# Reason: BeamSearchScorer was moved in transformers 4.37+
# XTTS v2 needs it at the old import location
# Also install compatible numpy and scipy versions
RUN pip3 install numpy==1.22.0 scipy==1.11.4 transformers==4.36.2 --force-reinstall

# Install FastAPI for API server
RUN pip3 install fastapi uvicorn pydantic python-multipart

# Create directories
RUN mkdir -p /app/models /app/outputs

# Copy DeepSpeed-optimized API server
COPY app_deepspeed.py /app/app.py

# Expose port
EXPOSE 8005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8005/health || exit 1

# Run the application
CMD ["python3", "/app/app.py"]
