"""
OpenVoice TTS Gradio Web Interface
User-friendly interface for OpenVoice V2 with voice cloning capabilities.

Supports English and Chinese TTS with 11 pre-loaded voices, plus custom voice cloning.
"""
import gradio as gr
import requests
import tempfile
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
OPENVOICE_API_URL = os.environ.get("OPENVOICE_API_URL", "http://openvoice:8003")

# Available speakers and languages
SPEAKERS = {
    "English (US)": "en-us",
    "English (UK - Default)": "en-default",
    "English (Australia)": "en-au",
    "English (Brazil)": "en-br",
    "English (India)": "en-india",
    "English (Newest)": "en-newest",
    "Spanish": "es",
    "French": "fr",
    "Japanese": "jp",
    "Korean": "kr",
    "Chinese": "zh"
}

LANGUAGES = {
    "English": "English",
    "Chinese": "Chinese"
}


def check_api_health():
    """Check if OpenVoice API is healthy."""
    try:
        response = requests.get(f"{OPENVOICE_API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ OpenVoice API is healthy: {data}")
            return True
        return False
    except Exception as e:
        logger.error(f"❌ OpenVoice API health check failed: {e}")
        return False


def synthesize_with_preset(text, speaker_display, language, speed):
    """
    Synthesize speech using a preset speaker voice.

    Args:
        text: Text to synthesize
        speaker_display: Display name of speaker
        language: Language (English or Chinese)
        speed: Speech speed multiplier

    Returns:
        Audio file path or error message
    """
    if not text or not text.strip():
        return None, "❌ Please enter some text to synthesize."

    if len(text) > 2000:
        return None, f"❌ Text too long ({len(text)} chars). Maximum is 2000 characters."

    try:
        # Get speaker ID from display name
        speaker_id = SPEAKERS.get(speaker_display, "en-default")

        logger.info(f"Synthesizing: '{text[:50]}...' with speaker {speaker_id}, language {language}")

        # Call API
        response = requests.post(
            f"{OPENVOICE_API_URL}/synthesize",
            json={
                "text": text,
                "reference_speaker": speaker_id,
                "language": language,
                "speed": speed
            },
            timeout=60
        )

        if response.status_code == 200:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
                tmp.write(response.content)
                audio_path = tmp.name

            logger.info(f"✅ Synthesis successful: {audio_path}")
            return audio_path, f"✅ Successfully generated speech with {speaker_display}"
        else:
            error_msg = response.json().get("detail", "Unknown error")
            logger.error(f"❌ Synthesis failed: {error_msg}")
            return None, f"❌ Synthesis failed: {error_msg}"

    except Exception as e:
        logger.error(f"❌ Error during synthesis: {e}")
        return None, f"❌ Error: {str(e)}"


def clone_voice(text, reference_audio, language, speed):
    """
    Clone a voice from reference audio and synthesize text.

    Args:
        text: Text to synthesize
        reference_audio: Path to reference audio file
        language: Language (English or Chinese)
        speed: Speech speed multiplier

    Returns:
        Audio file path or error message
    """
    if not text or not text.strip():
        return None, "❌ Please enter some text to synthesize."

    if not reference_audio:
        return None, "❌ Please upload a reference audio file."

    if len(text) > 2000:
        return None, f"❌ Text too long ({len(text)} chars). Maximum is 2000 characters."

    try:
        logger.info(f"Cloning voice from reference audio for: '{text[:50]}...'")

        # Prepare form data
        with open(reference_audio, 'rb') as audio_file:
            files = {'reference_audio': audio_file}
            data = {
                'text': text,
                'language': language,
                'speed': speed
            }

            response = requests.post(
                f"{OPENVOICE_API_URL}/clone_voice",
                files=files,
                data=data,
                timeout=120
            )

        if response.status_code == 200:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
                tmp.write(response.content)
                audio_path = tmp.name

            logger.info(f"✅ Voice cloning successful: {audio_path}")
            return audio_path, "✅ Successfully cloned voice and generated speech"
        else:
            error_msg = response.json().get("detail", "Unknown error")
            logger.error(f"❌ Voice cloning failed: {error_msg}")
            return None, f"❌ Voice cloning failed: {error_msg}"

    except Exception as e:
        logger.error(f"❌ Error during voice cloning: {e}")
        return None, f"❌ Error: {str(e)}"


# Check API health on startup
logger.info("Starting OpenVoice TTS Gradio Interface")
logger.info(f"Connecting to OpenVoice API at: {OPENVOICE_API_URL}")

if check_api_health():
    logger.info("✅ OpenVoice API is healthy and ready")
else:
    logger.warning("⚠️  OpenVoice API is not responding. The interface will still load but synthesis may fail.")


# Build Gradio interface
with gr.Blocks(
    title="OpenVoice TTS",
    theme=gr.themes.Soft()
) as demo:
    gr.Markdown("""
    # 🎙️ OpenVoice TTS

    **Advanced Voice Cloning & Text-to-Speech**

    Choose between preset voices or clone any voice from a reference audio file.
    """)

    with gr.Tabs():
        # Tab 1: Preset Voices
        with gr.Tab("🎵 Preset Voices"):
            gr.Markdown("### Use Pre-loaded Voice Presets")

            with gr.Row():
                with gr.Column(scale=2):
                    preset_text = gr.Textbox(
                        label="Text to Synthesize (Maximum 2000 characters)",
                        placeholder="Enter the text you want to convert to speech...",
                        lines=6,
                        max_lines=12
                    )

                    preset_char_count = gr.Markdown("**Characters:** 0 / 2000")

                    with gr.Row():
                        preset_speaker = gr.Dropdown(
                            choices=list(SPEAKERS.keys()),
                            value="English (US)",
                            label="Voice Preset (Select a pre-loaded voice)"
                        )

                        preset_language = gr.Dropdown(
                            choices=list(LANGUAGES.keys()),
                            value="English",
                            label="Language (English or Chinese)"
                        )

                    preset_speed = gr.Slider(
                        minimum=0.5,
                        maximum=2.0,
                        value=1.0,
                        step=0.1,
                        label="Speed"
                    )

                    preset_btn = gr.Button("🎵 Generate Speech", variant="primary", size="lg")

                with gr.Column(scale=1):
                    gr.Markdown("### 🔊 Output")
                    preset_audio_output = gr.Audio(
                        label="Generated Speech",
                        type="filepath"
                    )
                    preset_status = gr.Markdown("")

        # Tab 2: Voice Cloning
        with gr.Tab("🎤 Voice Cloning"):
            gr.Markdown("### Clone Any Voice from Reference Audio")

            with gr.Row():
                with gr.Column(scale=2):
                    clone_text = gr.Textbox(
                        label="Text to Synthesize (Maximum 2000 characters)",
                        placeholder="Enter the text you want to convert to speech...",
                        lines=6,
                        max_lines=12
                    )

                    clone_char_count = gr.Markdown("**Characters:** 0 / 2000")

                    clone_reference = gr.Audio(
                        label="Reference Audio File (Upload or record your voice sample)",
                        type="filepath",
                        sources=["upload", "microphone"]
                    )

                    with gr.Row():
                        clone_language = gr.Dropdown(
                            choices=list(LANGUAGES.keys()),
                            value="English",
                            label="Language (English or Chinese)"
                        )

                        clone_speed = gr.Slider(
                            minimum=0.5,
                            maximum=2.0,
                            value=1.0,
                            step=0.1,
                            label="Speed"
                        )

                    clone_btn = gr.Button("🎤 Clone Voice & Generate", variant="primary", size="lg")

                with gr.Column(scale=1):
                    gr.Markdown("### 🔊 Output")
                    clone_audio_output = gr.Audio(
                        label="Generated Speech with Cloned Voice",
                        type="filepath"
                    )
                    clone_status = gr.Markdown("")

        # Tab 3: Help & Info
        with gr.Tab("ℹ️ Help"):
            gr.Markdown("""
            ## How to Use OpenVoice TTS

            ### 🎵 Preset Voices Tab

            Use this tab for quick text-to-speech with pre-loaded voices:

            1. **Enter your text** (up to 2000 characters)
            2. **Select a voice preset** from the dropdown (11 voices available)
            3. **Choose language** (English or Chinese)
            4. **Adjust speed** if needed (0.5x - 2.0x)
            5. **Click "Generate Speech"** to create audio
            6. **Play or download** the generated audio

            **Available Voices:**
            - English: US, UK, Australia, Brazil, India, Newest
            - Spanish, French, Japanese, Korean, Chinese

            ---

            ### 🎤 Voice Cloning Tab

            Clone any voice from a reference audio file:

            1. **Enter your text** (up to 2000 characters)
            2. **Upload reference audio** or record with microphone
               - Recommended: 5-30 seconds of clear speech
               - Formats: WAV, MP3, or other common audio formats
            3. **Select language** for synthesis
            4. **Adjust speed** if needed
            5. **Click "Clone Voice & Generate"**
            6. **Play or download** the cloned voice output

            **Tips for Best Results:**
            - Use clear, high-quality reference audio
            - Remove background noise if possible
            - Speak naturally in the reference recording
            - Longer reference audio (10-30 seconds) generally gives better results

            ---

            ### 📊 Technical Details

            - **Model:** OpenVoice V2
            - **Languages:** English, Chinese (base TTS)
            - **Voice Cloning:** Works with any language
            - **Speed Control:** 0.5x to 2.0x
            - **Output Format:** WAV (high quality)
            - **Max Text Length:** 2000 characters

            ---

            ### 🔧 API Information

            This interface connects to: `{OPENVOICE_API_URL}`

            For programmatic access, use the REST API directly:
            - POST `/synthesize` - Generate with preset voice
            - POST `/clone_voice` - Clone voice from audio
            - GET `/speakers` - List available speakers
            """.replace("{OPENVOICE_API_URL}", OPENVOICE_API_URL))

    # Character counter updates
    preset_text.change(
        lambda text: f"**Characters:** {len(text)} / 2000",
        inputs=preset_text,
        outputs=preset_char_count
    )

    clone_text.change(
        lambda text: f"**Characters:** {len(text)} / 2000",
        inputs=clone_text,
        outputs=clone_char_count
    )

    # Button click handlers
    preset_btn.click(
        synthesize_with_preset,
        inputs=[preset_text, preset_speaker, preset_language, preset_speed],
        outputs=[preset_audio_output, preset_status]
    )

    clone_btn.click(
        clone_voice,
        inputs=[clone_text, clone_reference, clone_language, clone_speed],
        outputs=[clone_audio_output, clone_status]
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=8013,
        share=False
    )
