"""
Coqui TTS Gradio Web Interface

User-friendly interface for Coqui XTTS v2 with voice cloning capabilities.
Supports 17 languages and zero-shot voice cloning from reference audio.
"""

import gradio as gr
import requests
import tempfile
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
COQUI_API_URL = os.getenv("COQUI_API_URL", "http://coqui:8005")

# XTTS v2 supported languages
LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "pl": "Polish",
    "tr": "Turkish",
    "ru": "Russian",
    "nl": "Dutch",
    "cs": "Czech",
    "ar": "Arabic",
    "zh-cn": "Chinese (Simplified)",
    "ja": "Japanese",
    "hu": "Hungarian",
    "ko": "Korean",
    "hi": "Hindi"
}

def check_api_health():
    """Check if Coqui API is accessible."""
    try:
        response = requests.get(f"{COQUI_API_URL}/health", timeout=5)
        return response.json().get("status") == "healthy"
    except Exception as e:
        logger.error(f"API health check failed: {e}")
        return False

def synthesize_speech(text, reference_audio, language):
    """
    Synthesize speech using Coqui XTTS v2 with voice cloning.

    Args:
        text (str): Text to synthesize (max 5000 characters)
        reference_audio: Audio file for voice cloning
        language (str): Language code

    Returns:
        str: Path to generated audio file or error message
    """
    if not text:
        return None, "⚠️ Please enter some text to synthesize."

    if not reference_audio:
        return None, "⚠️ Please provide a reference audio file for voice cloning (5-30 seconds recommended)."

    if len(text) > 5000:
        return None, "⚠️ Text is too long. Maximum 5000 characters allowed."

    try:
        logger.info(f"Synthesizing text: '{text[:50]}...' in language: {language}")

        # Prepare the request
        files = {
            'reference_audio': open(reference_audio, 'rb')
        }
        data = {
            'text': text,
            'language': language
        }

        # Call Coqui API
        response = requests.post(
            f"{COQUI_API_URL}/synthesize_with_reference",
            files=files,
            data=data,
            timeout=300  # 5 minutes timeout for long text
        )

        files['reference_audio'].close()

        if response.status_code == 200:
            # Save the audio file
            output_path = tempfile.mktemp(suffix=".wav")
            with open(output_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"Synthesis successful: {output_path}")
            return output_path, "✅ Speech generated successfully!"
        else:
            error_msg = f"❌ API Error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return None, error_msg

    except requests.exceptions.Timeout:
        error_msg = "⏱️ Request timed out. Please try with shorter text."
        logger.error(error_msg)
        return None, error_msg
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        logger.error(error_msg)
        return None, error_msg

# Check API health on startup
api_healthy = check_api_health()
if api_healthy:
    logger.info("✅ Coqui API is healthy and ready")
else:
    logger.warning("⚠️ Coqui API is not responding. Please ensure the API container is running.")

# Create Gradio interface
with gr.Blocks(title="Coqui TTS - Voice Cloning", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🎙️ Coqui XTTS v2 - Voice Cloning TTS

        **Zero-shot voice cloning** with multilingual support (17 languages)

        ### How to use:
        1. **Upload** a reference audio file (5-30 seconds of clean speech recommended)
        2. **Select** the target language
        3. **Type** the text you want to synthesize (up to 5000 characters)
        4. **Click** Generate to create speech in the cloned voice

        ---
        """
    )

    # API Status indicator
    api_status = "🟢 API Connected" if api_healthy else "🔴 API Disconnected"
    gr.Markdown(f"**Status:** {api_status}")

    with gr.Row():
        with gr.Column(scale=1):
            # Input controls
            gr.Markdown("### 📝 Input")

            text_input = gr.Textbox(
                label="Text to Synthesize (Maximum 5000 characters)",
                placeholder="Enter the text you want to convert to speech...",
                lines=6,
                max_lines=10
            )

            char_count = gr.Markdown("**Characters:** 0 / 5000")

            # Update character count
            def update_char_count(text):
                count = len(text) if text else 0
                color = "green" if count <= 5000 else "red"
                return f'<span style="color: {color};">**Characters:** {count} / 5000</span>'

            text_input.change(
                fn=update_char_count,
                inputs=[text_input],
                outputs=[char_count]
            )

            language_select = gr.Dropdown(
                choices=list(LANGUAGES.keys()),
                value="en",
                label="Language (Select the language for text-to-speech)"
            )

            # Show selected language name
            language_name = gr.Markdown(f"**Selected:** {LANGUAGES['en']}")

            def update_language_name(lang_code):
                return f"**Selected:** {LANGUAGES.get(lang_code, 'Unknown')}"

            language_select.change(
                fn=update_language_name,
                inputs=[language_select],
                outputs=[language_name]
            )

            gr.Markdown("### 🎤 Reference Audio")
            gr.Markdown(
                """
                Upload a clear audio sample of the voice you want to clone.

                **Tips for best results:**
                - 📏 Duration: 5-30 seconds
                - 🎧 Quality: Clear speech, minimal background noise
                - 🗣️ Content: Natural speaking, not singing
                - 🌍 Language: Can be in any language (cross-lingual cloning supported)
                """
            )

            reference_audio = gr.Audio(
                label="Reference Audio File (WAV, MP3, or other audio formats)",
                type="filepath",
                sources=["upload", "microphone"]
            )

            generate_btn = gr.Button(
                "🎵 Generate Speech",
                variant="primary",
                size="lg"
            )

        with gr.Column(scale=1):
            # Output controls
            gr.Markdown("### 🔊 Output")

            status_msg = gr.Markdown("")

            audio_output = gr.Audio(
                label="Generated Speech",
                type="filepath",
                interactive=False
            )

            gr.Markdown(
                """
                ### 📚 Supported Languages

                🇬🇧 English • 🇪🇸 Spanish • 🇫🇷 French • 🇩🇪 German • 🇮🇹 Italian • 🇵🇹 Portuguese
                🇵🇱 Polish • 🇹🇷 Turkish • 🇷🇺 Russian • 🇳🇱 Dutch • 🇨🇿 Czech • 🇸🇦 Arabic
                🇨🇳 Chinese • 🇯🇵 Japanese • 🇭🇺 Hungarian • 🇰🇷 Korean • 🇮🇳 Hindi

                ---

                ### ℹ️ About XTTS v2

                **Coqui XTTS v2** is a state-of-the-art text-to-speech model featuring:
                - ✨ Zero-shot voice cloning (clone any voice from a sample)
                - 🌍 17 language support with cross-lingual cloning
                - 🎭 Natural prosody and emotion
                - ⚡ Fast generation (~5-10 seconds for short texts)

                **License:** [Coqui Public Model License (CPML)](https://coqui.ai/cpml) - Non-commercial use
                """
            )

    # Connect the generate button
    generate_btn.click(
        fn=synthesize_speech,
        inputs=[text_input, reference_audio, language_select],
        outputs=[audio_output, status_msg]
    )

    gr.Markdown(
        """
        ---
        **Powered by:** Coqui XTTS v2 | **API Endpoint:** `{}`
        """.format(COQUI_API_URL)
    )

if __name__ == "__main__":
    logger.info("Starting Coqui TTS Gradio Interface")
    logger.info(f"Connecting to Coqui API at: {COQUI_API_URL}")

    demo.queue(
        max_size=50,
        default_concurrency_limit=2
    ).launch(
        server_name="0.0.0.0",
        server_port=8015,
        share=False,
        show_error=True
    )
