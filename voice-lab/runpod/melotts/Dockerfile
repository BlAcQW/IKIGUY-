# MeloTTS Training Dockerfile for RunPod
# Optimized for RTX 4090 / A100 GPUs

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
    numpy \
    scipy \
    librosa \
    matplotlib \
    tensorboard \
    phonemizer \
    unidecode \
    inflect \
    eng_to_ipa \
    jamo \
    pypinyin \
    cn2an \
    jieba \
    protobuf \
    gradio

# Clone MeloTTS repository
RUN git clone https://github.com/myshell-ai/MeloTTS.git /workspace/MeloTTS

# Install MeloTTS dependencies
WORKDIR /workspace/MeloTTS
RUN pip install -e .

# Install additional training dependencies
RUN pip install --no-cache-dir \
    wandb \
    pydub

# Create directories for data and checkpoints
RUN mkdir -p /workspace/data /workspace/checkpoints /workspace/logs

# Set environment variables for optimal training
ENV CUDA_LAUNCH_BLOCKING=0
ENV OMP_NUM_THREADS=8
ENV PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Expose TensorBoard port
EXPOSE 6006

# Default command
CMD ["/bin/bash"]
