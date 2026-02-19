FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    wget \
    unzip \
    curl \
    ffmpeg \
    libsndfile1 \
    pkg-config \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libavfilter-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip3 install --upgrade pip setuptools wheel

# Clone OpenVoice repository
RUN git clone https://github.com/myshell-ai/OpenVoice.git /app/OpenVoice

WORKDIR /app/OpenVoice

# Patch setup.py to use newer faster-whisper with PyAV 13+ support
# Reason: Original requires faster-whisper==0.9.0 which forces av==10.* (build fails)
RUN sed -i 's/faster-whisper==0.9.0/faster-whisper>=1.0.0/g' setup.py && \
    sed -i 's/av==10.\*/av>=13.0.0/g' requirements.txt 2>/dev/null || true

# Install PyAV 13.1.0 with pre-built binary wheels FIRST
# Reason: PyAV 13.1.0 (Oct 2024) has pre-built wheels for Python 3.10, no Cython build needed
RUN pip3 install av==13.1.0

# Install dependencies
RUN pip3 install -e .

# Install additional dependencies for API server
RUN pip3 install httpx

# Download OpenVoice V1 checkpoints (base TTS models)
# Reason: V1 includes BaseSpeakerTTS models for EN and ZH
RUN mkdir -p checkpoints && \
    wget https://myshell-public-repo-host.s3.amazonaws.com/openvoice/checkpoints_1226.zip && \
    unzip -d /tmp checkpoints_1226.zip && \
    cp -r /tmp/checkpoints/* checkpoints/ && \
    rm -rf checkpoints_1226.zip /tmp/checkpoints

# Download OpenVoice V2 checkpoints (tone color converter and speaker embeddings)
# Reason: V2 has improved tone color converter
RUN wget https://myshell-public-repo-host.s3.amazonaws.com/openvoice/checkpoints_v2_0417.zip && \
    unzip checkpoints_v2_0417.zip && \
    cp checkpoints_v2/converter/checkpoint.pth checkpoints/converter_v2.pth && \
    cp checkpoints_v2/converter/config.json checkpoints/config_v2.json && \
    cp -r checkpoints_v2/base_speakers checkpoints/base_speakers_v2 && \
    rm -rf checkpoints_v2_0417.zip checkpoints_v2

# Download WavMark model (audio watermarking)
# Reason: OpenVoice tries to download this at runtime, causing timeouts and crashes
RUN mkdir -p /root/.cache/torch/hub/checkpoints && \
    wget -O /root/.cache/torch/hub/checkpoints/wavmark_model.pkl \
    https://huggingface.co/M4869/WavMark/resolve/main/step59000_snr39.99_pesq4.35_BERP_none0.30_mean1.81_std1.81.model.pkl || \
    echo "WavMark model download failed - watermarking may not work"

# Verify checkpoint structure
RUN ls -la checkpoints/ && \
    echo "=== Base speakers (V1 - EN/ZH TTS) ===" && \
    ls -la checkpoints/base_speakers/ && \
    echo "=== Converter (V1) ===" && \
    ls -la checkpoints/converter/ && \
    echo "=== EN Base TTS ===" && \
    ls -la checkpoints/base_speakers/EN/ && \
    echo "=== ZH Base TTS ===" && \
    ls -la checkpoints/base_speakers/ZH/ && \
    echo "=== WavMark cache ===" && \
    ls -la /root/.cache/torch/hub/checkpoints/ || echo "WavMark not cached"

# Copy API server
COPY app.py /app/app.py

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Run the application
CMD ["python3", "/app/app.py"]
