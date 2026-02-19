"""
StyleTTS2 Gradio Web Interface
User-friendly interface for StyleTTS2 high-quality expressive text-to-speech.

Features voice cloning and style transfer with fine-grained control.
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
STYLETTS_API_URL = os.environ.get("STYLETTS_API_URL", "http://styletts2:8006")


def check_api_health():
    """Check if StyleTTS2 API is healthy."""
    try:
        response = requests.get(f"{STYLETTS_API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ StyleTTS2 API is healthy: {data}")
            return True, data
        return False, {}
    except Exception as e:
        logger.error(f"❌ StyleTTS2 API health check failed: {e}")
        return False, {}


def synthesize_speech(text, alpha, beta, diffusion_steps, embedding_scale):
    """
    Synthesize speech from text with style controls.

    Args:
        text: Text to synthesize
        alpha: Timbre control (0-1)
        beta: Prosody control (0-1)
        diffusion_steps: Quality vs speed tradeoff (3-10)
        embedding_scale: Style strength (0.5-2.0)

    Returns:
        Audio file path or error message
    """
    if not text or not text.strip():
        return None, "❌ Please enter some text to synthesize."

    if len(text) > 5000:
        return None, f"❌ Text too long ({len(text)} chars). Maximum is 5000 characters."

    try:
        logger.info(f"Synthesizing: '{text[:50]}...' with alpha={alpha}, beta={beta}")

        # Call API
        response = requests.post(
            f"{STYLETTS_API_URL}/synthesize",
            json={
                "text": text,
                "alpha": alpha,
                "beta": beta,
                "diffusion_steps": diffusion_steps,
                "embedding_scale": embedding_scale
            },
            timeout=120
        )

        if response.status_code == 200:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
                tmp.write(response.content)
                audio_path = tmp.name

            logger.info(f"✅ Synthesis successful: {audio_path}")
            return audio_path, f"✅ Successfully generated high-quality speech ({len(text)} chars)"
        else:
            error_msg = response.json().get("detail", "Unknown error")
            logger.error(f"❌ Synthesis failed: {error_msg}")
            return None, f"❌ Synthesis failed: {error_msg}"

    except Exception as e:
        logger.error(f"❌ Error during synthesis: {e}")
        return None, f"❌ Error: {str(e)}"


def clone_voice(text, reference_audio, alpha, beta, diffusion_steps):
    """
    Clone voice from reference audio.

    Args:
        text: Text to synthesize
        reference_audio: Path to reference audio file
        alpha: Timbre control
        beta: Prosody control
        diffusion_steps: Quality control

    Returns:
        Audio file path or error message
    """
    if not text or not text.strip():
        return None, "❌ Please enter some text to synthesize."

    if not reference_audio:
        return None, "❌ Please upload a reference audio file."

    if len(text) > 5000:
        return None, f"❌ Text too long ({len(text)} chars). Maximum is 5000 characters."

    try:
        logger.info(f"Voice cloning: '{text[:50]}...' with reference audio")

        # Prepare files for upload
        with open(reference_audio, 'rb') as audio_file:
            files = {'reference_audio': audio_file}
            data = {
                'text': text,
                'alpha': alpha,
                'beta': beta,
                'diffusion_steps': diffusion_steps
            }

            response = requests.post(
                f"{STYLETTS_API_URL}/clone_voice",
                files=files,
                data=data,
                timeout=180
            )

        if response.status_code == 200:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
                tmp.write(response.content)
                audio_path = tmp.name

            logger.info(f"✅ Voice cloning successful: {audio_path}")
            return audio_path, f"✅ Successfully cloned voice and generated speech!"
        else:
            error_msg = response.json().get("detail", "Unknown error")
            logger.error(f"❌ Voice cloning failed: {error_msg}")
            return None, f"❌ Voice cloning failed: {error_msg}"

    except Exception as e:
        logger.error(f"❌ Error during voice cloning: {e}")
        return None, f"❌ Error: {str(e)}"


# Check API health on startup
logger.info("Starting StyleTTS2 Gradio Interface")
logger.info(f"Connecting to StyleTTS2 API at: {STYLETTS_API_URL}")

api_healthy, health_data = check_api_health()
if api_healthy:
    logger.info("✅ StyleTTS2 API is healthy and ready")
    logger.info(f"   Device: {health_data.get('device', 'unknown')}")
    logger.info(f"   Model loaded: {health_data.get('model_loaded', False)}")
else:
    logger.warning("⚠️  StyleTTS2 API is not responding. The interface will still load but synthesis may fail.")


# Build Gradio interface
with gr.Blocks(
    title="StyleTTS2",
    theme=gr.themes.Soft()
) as demo:
    gr.Markdown("""
    # 🎭 StyleTTS2 - High-Quality Expressive Text-to-Speech

    **State-of-the-art TTS with voice cloning and style transfer**

    Generate natural, expressive speech with fine-grained control over timbre and prosody.
    """)

    with gr.Tabs():
        # Tab 1: Standard Synthesis
        with gr.TabItem("🎵 Text-to-Speech"):
            with gr.Row():
                with gr.Column(scale=2):
                    gr.Markdown("### 📝 Input")

                    text_input = gr.Textbox(
                        label="Text to Synthesize (Maximum 5000 characters)",
                        placeholder="Enter the text you want to convert to speech...",
                        lines=8,
                        max_lines=15
                    )

                    char_count = gr.Markdown("**Characters:** 0 / 5000")

                    with gr.Row():
                        alpha_slider = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            value=0.3,
                            step=0.05,
                            label="Alpha - Timbre Control (Lower = more variation)",
                            info="Controls voice timbre and character"
                        )

                        beta_slider = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            value=0.7,
                            step=0.05,
                            label="Beta - Prosody Control (Lower = more expressive)",
                            info="Controls speech rhythm and intonation"
                        )

                    with gr.Row():
                        diffusion_steps = gr.Slider(
                            minimum=3,
                            maximum=10,
                            value=5,
                            step=1,
                            label="Diffusion Steps (Higher = better quality, slower)",
                            info="Quality vs speed tradeoff"
                        )

                        embedding_scale = gr.Slider(
                            minimum=0.5,
                            maximum=2.0,
                            value=1.0,
                            step=0.1,
                            label="Embedding Scale (Style strength)",
                            info="Controls overall style intensity"
                        )

                    generate_btn = gr.Button("🎵 Generate Speech", variant="primary", size="lg")

                with gr.Column(scale=1):
                    gr.Markdown("### 🔊 Output")

                    audio_output = gr.Audio(
                        label="Generated Speech",
                        type="filepath"
                    )

                    status_output = gr.Markdown("")

        # Tab 2: Voice Cloning
        with gr.TabItem("🎤 Voice Cloning"):
            with gr.Row():
                with gr.Column(scale=2):
                    gr.Markdown("### 📝 Input")

                    clone_text = gr.Textbox(
                        label="Text to Synthesize (Maximum 5000 characters)",
                        placeholder="Enter the text you want the cloned voice to speak...",
                        lines=6,
                        max_lines=12
                    )

                    clone_char_count = gr.Markdown("**Characters:** 0 / 5000")

                    reference_audio = gr.Audio(
                        label="Reference Audio (Upload voice sample to clone)",
                        type="filepath",
                        sources=["upload", "microphone"]
                    )

                    gr.Markdown("""
                    **Tips for best results:**
                    - Use clear, high-quality audio (3-30 seconds)
                    - Single speaker only
                    - Minimal background noise
                    - Natural speech (not singing or whispering)
                    """)

                    with gr.Row():
                        clone_alpha = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            value=0.3,
                            step=0.05,
                            label="Alpha - Timbre Control"
                        )

                        clone_beta = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            value=0.7,
                            step=0.05,
                            label="Beta - Prosody Control"
                        )

                    clone_diffusion = gr.Slider(
                        minimum=3,
                        maximum=10,
                        value=7,
                        step=1,
                        label="Diffusion Steps (Higher for better clone quality)"
                    )

                    clone_btn = gr.Button("🎤 Clone Voice & Generate", variant="primary", size="lg")

                with gr.Column(scale=1):
                    gr.Markdown("### 🔊 Output")

                    clone_audio_output = gr.Audio(
                        label="Cloned Voice Speech",
                        type="filepath"
                    )

                    clone_status_output = gr.Markdown("")

    # Help section
    with gr.Accordion("ℹ️ Help & Information", open=False):
        gr.Markdown(f"""
        ## How to Use StyleTTS2

        ### Text-to-Speech Tab

        1. **Enter your text** in the text box (up to 5000 characters)
        2. **Adjust style controls:**
           - **Alpha (Timbre):** Lower values = more natural variation
           - **Beta (Prosody):** Lower values = more expressive speech
           - **Diffusion Steps:** Higher = better quality (but slower)
           - **Embedding Scale:** Adjust overall style strength
        3. **Click "Generate Speech"** to create audio
        4. **Play or download** the generated audio

        ---

        ### Voice Cloning Tab

        1. **Upload a reference audio** (3-30 seconds of clear speech)
        2. **Enter the text** you want spoken in the cloned voice
        3. **Adjust controls** (use higher diffusion steps for better cloning)
        4. **Click "Clone Voice & Generate"**
        5. **Listen to the result** - the voice should match your reference!

        ---

        ### Understanding the Controls

        **Alpha (Timbre Control):**
        - Controls voice characteristics and timbre
        - **0.0-0.3:** More natural variation (recommended)
        - **0.4-0.7:** Balanced
        - **0.8-1.0:** More consistent/monotone

        **Beta (Prosody Control):**
        - Controls rhythm, intonation, and expressiveness
        - **0.0-0.5:** Very expressive and dynamic
        - **0.6-0.8:** Balanced (recommended)
        - **0.9-1.0:** More monotone/flat

        **Diffusion Steps:**
        - Quality vs speed tradeoff
        - **3-5:** Fast, good quality
        - **5-7:** Balanced (recommended)
        - **8-10:** Highest quality, slower

        **Embedding Scale:**
        - Controls style strength
        - **0.5-1.0:** Subtle style
        - **1.0:** Default (recommended)
        - **1.5-2.0:** Strong style emphasis

        ---

        ### Technical Details

        - **Model:** StyleTTS2
        - **Quality:** High-fidelity, expressive synthesis
        - **Features:** Voice cloning, style transfer, fine control
        - **Output Format:** WAV (24kHz, high quality)
        - **Max Text Length:** 5000 characters
        - **Processing:** GPU-accelerated (CUDA)

        ---

        ### Tips for Best Results

        **Text-to-Speech:**
        - Use natural, well-punctuated sentences
        - Experiment with alpha and beta to find your preferred style
        - Start with default settings (alpha=0.3, beta=0.7)
        - Increase diffusion steps for important audio

        **Voice Cloning:**
        - Use high-quality reference audio (clear, no noise)
        - 5-15 seconds of speech is ideal
        - Single speaker only (no background voices)
        - Natural conversational speech works best
        - Increase diffusion steps (7-10) for better cloning

        ---

        ### API Information

        This interface connects to: `{STYLETTS_API_URL}`

        For programmatic access, use the REST API:
        - POST `/synthesize` - Generate speech
        - POST `/clone_voice` - Clone voice from reference
        - GET `/health` - Check API status
        - GET `/docs` - Interactive API documentation

        ---

        ### Use Cases

        - **Audiobooks & Narration:** High-quality, expressive reading
        - **Voice Acting:** Create character voices with style control
        - **Accessibility:** Convert text to natural speech
        - **Content Creation:** Generate voiceovers for videos
        - **Voice Cloning:** Clone your own or others' voices
        - **Language Learning:** Hear text in natural speech
        """)

    # Event handlers
    text_input.change(
        lambda text: f"**Characters:** {len(text)} / 5000",
        inputs=text_input,
        outputs=char_count
    )

    clone_text.change(
        lambda text: f"**Characters:** {len(text)} / 5000",
        inputs=clone_text,
        outputs=clone_char_count
    )

    generate_btn.click(
        synthesize_speech,
        inputs=[text_input, alpha_slider, beta_slider, diffusion_steps, embedding_scale],
        outputs=[audio_output, status_output]
    )

    clone_btn.click(
        clone_voice,
        inputs=[clone_text, reference_audio, clone_alpha, clone_beta, clone_diffusion],
        outputs=[clone_audio_output, clone_status_output]
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=8014,
        share=False
    )
