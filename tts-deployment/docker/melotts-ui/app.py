"""
MeloTTS Gradio Web Interface
User-friendly interface for MeloTTS multilingual text-to-speech.

Supports 6 languages (EN, ES, FR, ZH, JP, KR) with multiple speakers per language.
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
MELOTTS_API_URL = os.environ.get("MELOTTS_API_URL", "http://melotts:8001")

# Language mapping for display
LANGUAGES = {
    "English": "EN",
    "Spanish": "ES",
    "French": "FR",
    "Chinese": "ZH",
    "Japanese": "JP",
    "Korean": "KR"
}

# Cache for speakers per language
SPEAKERS_CACHE = {}


def check_api_health():
    """Check if MeloTTS API is healthy."""
    try:
        response = requests.get(f"{MELOTTS_API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ MeloTTS API is healthy: {data}")
            return True
        return False
    except Exception as e:
        logger.error(f"❌ MeloTTS API health check failed: {e}")
        return False


def load_speakers(language_code: str):
    """
    Load speakers for a specific language.

    Args:
        language_code: Language code (EN, ES, FR, ZH, JP, KR)

    Returns:
        Dictionary mapping speaker display names to IDs
    """
    if language_code in SPEAKERS_CACHE:
        return SPEAKERS_CACHE[language_code]

    try:
        response = requests.get(f"{MELOTTS_API_URL}/speakers/{language_code}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            speakers = data.get("speakers", {})
            SPEAKERS_CACHE[language_code] = speakers
            logger.info(f"Loaded {len(speakers)} speakers for {language_code}")
            return speakers
        else:
            logger.error(f"Failed to load speakers for {language_code}: {response.status_code}")
            return {}
    except Exception as e:
        logger.error(f"Error loading speakers for {language_code}: {e}")
        return {}


def update_speaker_dropdown(language_display):
    """
    Update speaker dropdown when language changes.

    Args:
        language_display: Display name of language

    Returns:
        Updated dropdown with speaker choices
    """
    language_code = LANGUAGES.get(language_display, "EN")
    speakers = load_speakers(language_code)

    if speakers:
        speaker_choices = list(speakers.keys())
        return gr.Dropdown(choices=speaker_choices, value=speaker_choices[0])
    else:
        return gr.Dropdown(choices=["Default"], value="Default")


def synthesize_speech(text, language_display, speaker_name, speed):
    """
    Synthesize speech from text.

    Args:
        text: Text to synthesize
        language_display: Display name of language
        speaker_name: Name of speaker
        speed: Speech speed multiplier

    Returns:
        Audio file path or error message
    """
    if not text or not text.strip():
        return None, "❌ Please enter some text to synthesize."

    if len(text) > 3000:
        return None, f"❌ Text too long ({len(text)} chars). Maximum is 3000 characters."

    try:
        language_code = LANGUAGES.get(language_display, "EN")
        speakers = load_speakers(language_code)

        # Get speaker ID from name
        if speaker_name in speakers:
            speaker_id = speakers[speaker_name]
        else:
            speaker_id = 0  # Default to first speaker

        logger.info(f"Synthesizing: '{text[:50]}...' in {language_code} with speaker {speaker_name} (ID: {speaker_id})")

        # Call API
        response = requests.post(
            f"{MELOTTS_API_URL}/synthesize",
            json={
                "text": text,
                "language": language_code,
                "speaker_id": speaker_id,
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
            return audio_path, f"✅ Successfully generated speech in {language_display} with {speaker_name}"
        else:
            error_msg = response.json().get("detail", "Unknown error")
            logger.error(f"❌ Synthesis failed: {error_msg}")
            return None, f"❌ Synthesis failed: {error_msg}"

    except Exception as e:
        logger.error(f"❌ Error during synthesis: {e}")
        return None, f"❌ Error: {str(e)}"


# Check API health on startup
logger.info("Starting MeloTTS Gradio Interface")
logger.info(f"Connecting to MeloTTS API at: {MELOTTS_API_URL}")

if check_api_health():
    logger.info("✅ MeloTTS API is healthy and ready")
    # Pre-load English speakers
    load_speakers("EN")
else:
    logger.warning("⚠️  MeloTTS API is not responding. The interface will still load but synthesis may fail.")


# Build Gradio interface
with gr.Blocks(
    title="MeloTTS",
    theme=gr.themes.Soft()
) as demo:
    gr.Markdown("""
    # 🎵 MeloTTS - Fast Multilingual Text-to-Speech

    **High-quality TTS in 6 languages with multiple voice options**

    Generate natural-sounding speech in English, Spanish, French, Chinese, Japanese, and Korean.
    """)

    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### 📝 Input")

            text_input = gr.Textbox(
                label="Text to Synthesize (Maximum 3000 characters)",
                placeholder="Enter the text you want to convert to speech...",
                lines=6,
                max_lines=12
            )

            char_count = gr.Markdown("**Characters:** 0 / 3000")

            with gr.Row():
                language_select = gr.Dropdown(
                    choices=list(LANGUAGES.keys()),
                    value="English",
                    label="Language (Select synthesis language)"
                )

                speaker_select = gr.Dropdown(
                    choices=["EN-US", "EN-BR", "EN_INDIA", "EN-AU", "EN-Default"],
                    value="EN-US",
                    label="Voice (Select speaker voice)"
                )

            speed_slider = gr.Slider(
                minimum=0.5,
                maximum=2.0,
                value=1.0,
                step=0.1,
                label="Speed (Adjust speech speed)"
            )

            generate_btn = gr.Button("🎵 Generate Speech", variant="primary", size="lg")

        with gr.Column(scale=1):
            gr.Markdown("### 🔊 Output")

            audio_output = gr.Audio(
                label="Generated Speech",
                type="filepath"
            )

            status_output = gr.Markdown("")

    # Help section
    with gr.Accordion("ℹ️ Help & Information", open=False):
        gr.Markdown("""
        ## How to Use MeloTTS

        ### Quick Start

        1. **Enter your text** in the text box (up to 3000 characters)
        2. **Select a language** from the dropdown
        3. **Choose a speaker voice** (available voices vary by language)
        4. **Adjust speed** if needed (0.5x - 2.0x, default 1.0x)
        5. **Click "Generate Speech"** to create audio
        6. **Play or download** the generated audio

        ---

        ### Supported Languages & Speakers

        **English (EN):**
        - EN-US (American English)
        - EN-BR (Brazilian English)
        - EN_INDIA (Indian English)
        - EN-AU (Australian English)
        - EN-Default (General English)

        **Spanish (ES):**
        - Multiple Spanish voices

        **French (FR):**
        - Multiple French voices

        **Chinese (ZH):**
        - Multiple Chinese voices

        **Japanese (JP):**
        - Multiple Japanese voices

        **Korean (KR):**
        - Multiple Korean voices

        *Note: Speaker voices are automatically loaded when you select a language.*

        ---

        ### Speed Control

        Adjust the speech speed from 0.5x (slower) to 2.0x (faster):
        - **0.5x - 0.8x:** Slower, clearer speech (good for learning)
        - **1.0x:** Normal speed (recommended)
        - **1.2x - 2.0x:** Faster speech (good for quick listening)

        ---

        ### Technical Details

        - **Model:** MeloTTS
        - **Languages:** 6 (EN, ES, FR, ZH, JP, KR)
        - **Speed Range:** 0.5x - 2.0x
        - **Output Format:** WAV (high quality)
        - **Max Text Length:** 3000 characters
        - **Processing:** GPU-accelerated (CUDA)

        ---

        ### Tips for Best Results

        - Keep sentences natural and well-punctuated
        - Avoid very long sentences (split into shorter ones)
        - Use appropriate punctuation for natural pauses
        - Experiment with different voices to find your favorite
        - Adjust speed based on your listening preference

        ---

        ### API Information

        This interface connects to: `{MELOTTS_API_URL}`

        For programmatic access, use the REST API:
        - POST `/synthesize` - Generate speech
        - GET `/languages` - List supported languages
        - GET `/speakers/{language}` - List speakers for a language
        """.replace("{MELOTTS_API_URL}", MELOTTS_API_URL))

    # Event handlers
    text_input.change(
        lambda text: f"**Characters:** {len(text)} / 3000",
        inputs=text_input,
        outputs=char_count
    )

    language_select.change(
        update_speaker_dropdown,
        inputs=language_select,
        outputs=speaker_select
    )

    generate_btn.click(
        synthesize_speech,
        inputs=[text_input, language_select, speaker_select, speed_slider],
        outputs=[audio_output, status_output]
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=8011,
        share=False
    )
