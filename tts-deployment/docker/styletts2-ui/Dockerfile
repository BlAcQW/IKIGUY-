# StyleTTS2 Gradio UI Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    gradio==5.7.1 \
    requests==2.32.3

# Copy application
COPY app.py .

# Expose Gradio port
EXPOSE 8014

# Run Gradio app
CMD ["python", "app.py"]
