"""
Kokoro TTS Gradio Web Interface

User-friendly interface for Kokoro-82M TTS with multi-voice support.
Fast, high-quality voice synthesis with 11 unique voices.
"""

import gradio as gr
import requests
import tempfile
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
KOKORO_API_URL = os.getenv("KOKORO_API_URL", "http://kokoro:8010")

def check_api_health():
    """Check if Kokoro API is accessible."""
    try:
        response = requests.get(f"{KOKORO_API_URL}/health", timeout=5)
        return response.json().get("status") == "healthy"
    except Exception as e:
        logger.error(f"API health check failed: {e}")
        return False

def get_available_voices():
    """Fetch available voices from the API."""
    try:
        response = requests.get(f"{KOKORO_API_URL}/voices", timeout=5)
        if response.status_code == 200:
            data = response.json()
            voices = data.get("voices", [])
            # Return dict of {id: name} for dropdown
            return {v["id"]: v["name"] for v in voices}
        else:
            logger.error(f"Failed to fetch voices: {response.status_code}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching voices: {e}")
        return {}

def synthesize_speech(text, voice, speed, pitch):
    """
    Synthesize speech using Kokoro TTS.

    Args:
        text (str): Text to synthesize (max 5000 characters)
        voice (str): Voice ID to use
        speed (float): Speaking speed (0.5-2.0)
        pitch (float): Voice pitch (0.5-2.0)

    Returns:
        tuple: (audio_path, status_message)
    """
    if not text:
        return None, "⚠️ Please enter some text to synthesize."

    if len(text) > 5000:
        return None, "⚠️ Text is too long. Maximum 5000 characters allowed."

    try:
        logger.info(f"Synthesizing text: '{text[:50]}...' with voice: {voice}")

        # Prepare the request
        payload = {
            'text': text,
            'voice': voice,
            'speed': speed,
            'pitch': pitch
        }

        # Call Kokoro API
        response = requests.post(
            f"{KOKORO_API_URL}/synthesize",
            json=payload,
            timeout=300  # 5 minutes timeout for long text
        )

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
    logger.info("✅ Kokoro API is healthy and ready")
    voices_dict = get_available_voices()
    logger.info(f"Loaded {len(voices_dict)} voices")
else:
    logger.warning("⚠️ Kokoro API is not responding. Please ensure the API container is running.")
    voices_dict = {}

# Create Gradio interface
with gr.Blocks(title="Kokoro TTS - Voice Synthesis", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🎙️ Kokoro-82M TTS - Multi-Voice Synthesis

        **Fast, high-quality text-to-speech** with multiple unique voices

        ### How to use:
        1. **Select** your preferred voice from the dropdown
        2. **Type** the text you want to synthesize (up to 5000 characters)
        3. **Adjust** speed and pitch if desired
        4. **Click** Generate to create speech

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
                lines=8,
                max_lines=15
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

            gr.Markdown("### 🎤 Voice Selection")

            voice_select = gr.Dropdown(
                choices=list(voices_dict.keys()),
                value=list(voices_dict.keys())[0] if voices_dict else "af_heart",
                label="Voice (Select the voice for text-to-speech)"
            )

            # Show selected voice description
            if voices_dict:
                default_voice = list(voices_dict.keys())[0]
                default_desc = voices_dict[default_voice]
            else:
                default_desc = "No voices available"

            voice_description = gr.Markdown(f"**Selected:** {default_desc}")

            def update_voice_description(voice_id):
                return f"**Selected:** {voices_dict.get(voice_id, 'Unknown')}"

            voice_select.change(
                fn=update_voice_description,
                inputs=[voice_select],
                outputs=[voice_description]
            )

            gr.Markdown("### ⚙️ Voice Parameters")

            speed_slider = gr.Slider(
                minimum=0.5,
                maximum=2.0,
                value=1.0,
                step=0.1,
                label="Speaking Speed (Lower = slower, Higher = faster)"
            )

            pitch_slider = gr.Slider(
                minimum=0.5,
                maximum=2.0,
                value=1.0,
                step=0.1,
                label="Voice Pitch (Lower = deeper, Higher = higher)"
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
                f"""
                ### 🎭 Available Voices ({len(voices_dict)})

                **American English:**
                - Heart (female) • Bella (female) • Nicole (female) • Sarah (female) • Sky (female)
                - Adam (male) • Michael (male)

                **British English:**
                - Emma (female) • Isabella (female)
                - George (male) • Lewis (male)

                ---

                ### ℹ️ About Kokoro-82M

                **Kokoro-82M** is a fast, high-quality text-to-speech model featuring:
                - 🎭 11 unique voices (7 American, 4 British)
                - ⚡ Ultra-fast generation (~1-2 seconds for short texts)
                - 🎚️ Adjustable speed and pitch
                - 📱 Lightweight 82M parameter model
                - 🎯 Natural prosody and emotion

                **Model:** [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
                """
            )

    # Connect the generate button
    generate_btn.click(
        fn=synthesize_speech,
        inputs=[text_input, voice_select, speed_slider, pitch_slider],
        outputs=[audio_output, status_msg]
    )

    gr.Markdown(
        """
        ---
        **Powered by:** Kokoro-82M | **API Endpoint:** `{}`
        """.format(KOKORO_API_URL)
    )

if __name__ == "__main__":
    logger.info("Starting Kokoro TTS Gradio Interface")
    logger.info(f"Connecting to Kokoro API at: {KOKORO_API_URL}")

    demo.queue(
        max_size=50,
        default_concurrency_limit=2
    ).launch(
        server_name="0.0.0.0",
        server_port=8020,
        share=False,
        show_error=True
    )
