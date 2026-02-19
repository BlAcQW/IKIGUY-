FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-dev \
    git \
    wget \
    ffmpeg \
    libsndfile1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip3 install --upgrade pip

# Clone Moshi (Kyutai) repository
RUN git clone https://github.com/kyutai-labs/moshi.git /app/moshi || \
    echo "Moshi repository placeholder - update with actual URL"

WORKDIR /app/moshi

# Install PyTorch with CUDA support
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install dependencies
RUN pip3 install fastapi uvicorn pydantic websockets

# Download model weights
RUN mkdir -p checkpoints && \
    echo "Model checkpoints will be downloaded on first run"

# Copy API server
COPY app.py /app/app.py

# Expose port
EXPOSE 8008

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8008/health || exit 1

# Run the application
CMD ["python3", "/app/app.py"]
