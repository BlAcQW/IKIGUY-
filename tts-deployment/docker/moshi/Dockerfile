# Moshi (Kyutai) - Real-time Conversational AI
# Requires: 15-20GB VRAM, 20GB+ disk space for models

FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3.11-venv \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create Python virtual environment
RUN python3.11 -m venv /app/venv

# Activate venv and install Python dependencies
ENV PATH="/app/venv/bin:$PATH"

# Upgrade pip
RUN pip install --upgrade pip

# Install PyTorch with CUDA support
RUN pip install torch==2.5.1+cu121 torchaudio==2.5.1+cu121 \
    --index-url https://download.pytorch.org/whl/cu121

# Install Moshi and dependencies
RUN pip install moshi fastapi uvicorn pydantic websockets huggingface-hub

# Copy application code
COPY app.py /app/app.py

# Create cache directory for HuggingFace models
RUN mkdir -p /app/cache/huggingface

# Set HuggingFace cache location
ENV HF_HOME=/app/cache/huggingface
ENV TRANSFORMERS_CACHE=/app/cache/huggingface/transformers
ENV HF_DATASETS_CACHE=/app/cache/huggingface/datasets

# Expose port
EXPOSE 8008

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
  CMD curl -f http://localhost:8008/health || exit 1

# Run the application
CMD ["python", "app.py"]
