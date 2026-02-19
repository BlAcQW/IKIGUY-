FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    wget \
    curl \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip3 install --upgrade pip

# Clone Kokoro TTS repository
RUN git clone https://github.com/hexgrad/kokoro.git /app/kokoro

WORKDIR /app/kokoro

# Install PyTorch with CUDA support
RUN pip3 install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install FastAPI and related dependencies
RUN pip3 install fastapi uvicorn pydantic soundfile

# Install Kokoro package and its dependencies from pyproject.toml
# Reason: Kokoro uses pyproject.toml with dependencies: transformers, huggingface_hub, misaki[en], loguru
RUN pip3 install -e .

# Copy API server
COPY app.py /app/app.py

# Expose port
EXPOSE 8010

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8010/health || exit 1

# Run the application
CMD ["python3", "/app/app.py"]
