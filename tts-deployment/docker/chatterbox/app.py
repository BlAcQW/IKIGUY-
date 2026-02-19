"""
Chatterbox TTS Gradio Web Interface Launcher

Launches the multilingual Chatterbox TTS Gradio interface for text-to-speech synthesis
supporting 23 languages with voice cloning capabilities.
"""

import sys
import os
import logging

# Add chatterbox to Python path
sys.path.insert(0, '/app/chatterbox')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the multilingual demo
logger.info("Importing Chatterbox multilingual demo...")
from multilingual_app import demo

if __name__ == "__main__":
    logger.info("Starting Chatterbox Multilingual TTS Gradio Interface")
    logger.info("Supported languages: 23 (Arabic, Chinese, English, French, German, Spanish, and more)")
    logger.info("Server will be available at http://0.0.0.0:8004")

    # Launch Gradio with proper configuration
    demo.queue(
        max_size=50,
        default_concurrency_limit=2
    ).launch(
        server_name="0.0.0.0",
        server_port=8004,
        share=False,
        show_error=True,
        quiet=False
    )
