FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Set working directory
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

# Clone MeloTTS repository
RUN git clone https://github.com/myshell-ai/MeloTTS.git /app/MeloTTS

# Install MeloTTS dependencies
WORKDIR /app/MeloTTS
RUN pip3 install -e .
RUN python3 -m unidic download

# Download required NLTK data
RUN pip3 install nltk && \
    python3 -c "import nltk; \
    nltk.download('punkt'); \
    nltk.download('averaged_perceptron_tagger'); \
    nltk.download('averaged_perceptron_tagger_eng'); \
    nltk.download('cmudict')"

# Create API server script
COPY app.py /app/app.py

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the application
CMD ["python3", "/app/app.py"]
