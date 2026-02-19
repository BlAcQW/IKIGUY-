# Whisper ASR Training Dockerfile for RunPod
# Optimized for Twi-Fante fine-tuning

FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    build-essential \
    libsndfile1 \
    ffmpeg \
    sox \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Install Python dependencies
RUN pip install --no-cache-dir \
    transformers>=4.30.0 \
    datasets>=2.12.0 \
    accelerate>=0.20.0 \
    evaluate>=0.4.0 \
    jiwer \
    librosa \
    soundfile \
    tensorboard \
    wandb \
    gradio \
    peft \
    bitsandbytes

# Install Whisper and dependencies
RUN pip install --no-cache-dir \
    openai-whisper \
    git+https://github.com/huggingface/transformers.git

# Create directories
RUN mkdir -p /workspace/data /workspace/checkpoints /workspace/logs /workspace/outputs

# Set environment variables
ENV TRANSFORMERS_CACHE=/workspace/cache
ENV HF_HOME=/workspace/cache
ENV CUDA_LAUNCH_BLOCKING=0
ENV OMP_NUM_THREADS=8

# Expose TensorBoard port
EXPOSE 6006

# Default command
CMD ["/bin/bash"]
