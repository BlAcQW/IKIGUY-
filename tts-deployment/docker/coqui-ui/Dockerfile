FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    gradio==5.44.1 \
    requests==2.32.3

# Copy application
COPY app.py /app/app.py

# Expose Gradio port
EXPOSE 8015

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8015/ || exit 1

# Run the application
CMD ["python", "/app/app.py"]
