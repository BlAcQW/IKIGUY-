FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    git \
    wget \
    curl \
    ffmpeg \
    libsndfile1 \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.11 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Upgrade pip
RUN pip3 install --upgrade pip setuptools wheel

# Copy Chatterbox repository
COPY ./chatterbox /app/chatterbox

WORKDIR /app/chatterbox

# Temporarily modify pyproject.toml to remove problematic dependency
RUN sed -i '/russian-text-stresser/d' pyproject.toml

# Install Chatterbox dependencies
RUN pip3 install -e .

# Install russian-text-stresser separately (optional for Russian support)
# This has a dependency conflict with gradio, but we'll install it after
RUN pip3 install --no-deps git+https://github.com/Vuizur/add-stress-to-epub || true

# Remove the auto-launch from multilingual_app.py so we can control it
RUN sed -i 's/^demo\.launch(mcp_server=True)$/# demo.launch(mcp_server=True) # Disabled - launched via app.py/' multilingual_app.py

# Copy launch script
COPY ./docker/chatterbox/app.py /app/app.py

# Create outputs directory
RUN mkdir -p /app/outputs

# Expose Gradio port
EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8004/ || exit 1

# Run the Gradio application
CMD ["python3", "/app/app.py"]
