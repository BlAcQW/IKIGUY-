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

# Install Python packages
RUN pip3 install --no-cache-dir \
    torch==2.1.0 \
    torchaudio==2.1.0 \
    --index-url https://download.pytorch.org/whl/cu121

RUN pip3 install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    pydantic==2.5.0 \
    numpy \
    scipy \
    librosa \
    soundfile \
    transformers \
    einops \
    tqdm

# Clone F5-TTS repository
RUN git clone https://github.com/SWivid/F5-TTS.git /app/F5-TTS

# Install F5-TTS dependencies
WORKDIR /app/F5-TTS
RUN pip3 install --no-cache-dir .

# Copy FastAPI wrapper
COPY app.py /app/app.py

WORKDIR /app

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
  CMD curl -f http://localhost:8002/health || exit 1

# Run the application
CMD ["python3", "app.py"]
