#!/usr/bin/env python3
"""
Voice Cloning Script for Juliet Bawuah using Coqui TTS XTTS Models

This script creates voice clones using:
1. Custom Twi XTTS model (xtts_twi_v1_inference)
2. Official XTTS v2 multilingual model

Generates speech in Twi language using Juliet Bawuah's voice reference.
"""

import os
import sys
import logging
import torch
import torchaudio
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths configuration
VOICE_LAB_DIR = Path("/opt/kasaai/apps/voice-lab")
REFERENCE_VOICE = VOICE_LAB_DIR / "voices" / "juliet_bawuah.wav"
TWI_TEXT_FILE = VOICE_LAB_DIR / "voices" / "text" / "twi_text_1.md"
TWI_MODEL_PATH = VOICE_LAB_DIR / "models" / "xtts_twi_v1_inference"
OUTPUT_DIR = VOICE_LAB_DIR / "clones" / "coqui"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_xtts_model(model_path, model_name="XTTS"):
    """
    Load XTTS model from local directory or HuggingFace.

    Args:
        model_path: Path to model directory or HF model name
        model_name: Descriptive name for logging

    Returns:
        Loaded XTTS model instance and config
    """
    from TTS.tts.configs.xtts_config import XttsConfig
    from TTS.tts.models.xtts import Xtts
    from TTS.utils.manage import ModelManager

    logger.info(f"Loading {model_name} model from: {model_path}")

    # Fix for PyTorch 2.6+ weights_only=True default
    # Reason: XTTS checkpoints contain custom TTS classes
    import torch.serialization
    original_load = torch.load

    def safe_load(*args, **kwargs):
        """Wrapper for torch.load that sets weights_only=False for TTS models."""
        kwargs['weights_only'] = False
        return original_load(*args, **kwargs)

    torch.load = safe_load
    logger.info("Configured PyTorch to load XTTS checkpoints with weights_only=False")

    # Handle built-in model names vs local paths
    if isinstance(model_path, str) and model_path.startswith("tts_models/"):
        # Download model if needed
        manager = ModelManager()
        model_dir, config_path, _ = manager.download_model(model_path)
        logger.info(f"Model downloaded to: {model_dir}")
    else:
        # Local model
        model_dir = Path(model_path)
        config_path = model_dir / "config.json"

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

    # Load configuration
    logger.info(f"Loading config from: {config_path}")
    config = XttsConfig()
    config.load_json(str(config_path))

    # Initialize model
    logger.info("Initializing XTTS model...")
    model = Xtts.init_from_config(config)

    # Load checkpoint
    logger.info("Loading checkpoint...")
    model.load_checkpoint(
        config,
        checkpoint_dir=str(model_dir),
        use_deepspeed=False  # Disable for inference
    )

    # Move to CUDA if available
    if torch.cuda.is_available():
        model.cuda()
        logger.info("Model loaded successfully and moved to CUDA")
    else:
        logger.warning("CUDA not available, using CPU (will be slower)")

    return model, config


def synthesize_with_voice_cloning(model, text, reference_audio_path, language, output_path, temperature=0.7, speed=1.0):
    """
    Synthesize speech with voice cloning.

    Args:
        model: Loaded XTTS model
        text: Text to synthesize
        reference_audio_path: Path to reference audio for voice cloning
        language: Target language code (e.g., 'en', 'tw')
        output_path: Path to save output audio
        temperature: Sampling temperature (0.1-1.0)
        speed: Speech speed multiplier (0.5-2.0)

    Returns:
        Path to generated audio file
    """
    logger.info(f"Synthesizing: '{text[:100]}...'")
    logger.info(f"Reference audio: {reference_audio_path}")
    logger.info(f"Parameters: language={language}, temperature={temperature}, speed={speed}")

    # Compute speaker latents from reference audio
    logger.info("Computing speaker latents from reference audio...")
    gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
        audio_path=[str(reference_audio_path)]
    )

    # Synthesize speech
    logger.info("Generating speech with voice cloning...")
    out = model.inference(
        text,
        language,
        gpt_cond_latent,
        speaker_embedding,
        temperature=temperature,
        speed=speed
    )

    # Save output audio
    # Reason: XTTS returns numpy array, convert to tensor for torchaudio
    wav_tensor = torch.tensor(out["wav"]).unsqueeze(0)
    torchaudio.save(str(output_path), wav_tensor, 24000)

    logger.info(f"Audio saved to: {output_path}")
    return output_path


def main():
    """
    Main execution function.
    """
    # Set environment variable to agree to Coqui license
    os.environ['COQUI_TOS_AGREED'] = '1'
    logger.info("Agreed to Coqui non-commercial license (CPML): https://coqui.ai/cpml")

    # Verify reference audio exists
    if not REFERENCE_VOICE.exists():
        logger.error(f"Reference voice file not found: {REFERENCE_VOICE}")
        sys.exit(1)

    # Load Twi text
    if not TWI_TEXT_FILE.exists():
        logger.error(f"Twi text file not found: {TWI_TEXT_FILE}")
        sys.exit(1)

    with open(TWI_TEXT_FILE, 'r', encoding='utf-8') as f:
        twi_text = f.read().strip()

    logger.info(f"Loaded Twi text ({len(twi_text)} characters)")
    logger.info(f"Text preview: {twi_text[:100]}...")

    # Generate timestamp for output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ===================================================================
    # 1. Generate using custom Twi XTTS model (xtts_twi_v1_inference)
    # ===================================================================
    try:
        logger.info("\n" + "="*80)
        logger.info("STEP 1: Voice cloning with custom Twi XTTS model")
        logger.info("="*80 + "\n")

        # Check if Twi model exists
        if not TWI_MODEL_PATH.exists():
            logger.warning(f"Twi model not found at {TWI_MODEL_PATH}, skipping...")
        else:
            # Load Twi model
            twi_model, twi_config = load_xtts_model(TWI_MODEL_PATH, "Twi XTTS v1")

            # Generate speech
            twi_output_path = OUTPUT_DIR / f"juliet_twi_model_{timestamp}.wav"
            synthesize_with_voice_cloning(
                model=twi_model,
                text=twi_text,
                reference_audio_path=REFERENCE_VOICE,
                language="tw",  # Twi language code
                output_path=twi_output_path,
                temperature=0.7,
                speed=1.0
            )

            logger.info(f"✅ Twi model output: {twi_output_path}")

            # Cleanup
            del twi_model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    except Exception as e:
        logger.error(f"Failed to generate with Twi model: {str(e)}", exc_info=True)

    # ===================================================================
    # 2. Generate using official XTTS v2 multilingual model
    # ===================================================================
    try:
        logger.info("\n" + "="*80)
        logger.info("STEP 2: Voice cloning with official XTTS v2 multilingual model")
        logger.info("="*80 + "\n")

        # Load official XTTS v2 model
        xtts_v2_model, xtts_v2_config = load_xtts_model(
            "tts_models/multilingual/multi-dataset/xtts_v2",
            "XTTS v2 Multilingual"
        )

        # Generate speech using closest language code
        # Note: XTTS v2 doesn't have native Twi support, using English as fallback
        # The voice cloning should still work, but pronunciation may not be perfect
        xtts_v2_output_path = OUTPUT_DIR / f"juliet_xtts_v2_{timestamp}.wav"

        # Try with 'en' language code (XTTS v2 may handle Twi text with English phonetics)
        synthesize_with_voice_cloning(
            model=xtts_v2_model,
            text=twi_text,
            reference_audio_path=REFERENCE_VOICE,
            language="en",  # Using English as Twi is not in XTTS v2 language list
            output_path=xtts_v2_output_path,
            temperature=0.7,
            speed=1.0
        )

        logger.info(f"✅ XTTS v2 output: {xtts_v2_output_path}")
        logger.info("Note: XTTS v2 doesn't natively support Twi, using English language code")

        # Cleanup
        del xtts_v2_model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    except Exception as e:
        logger.error(f"Failed to generate with XTTS v2: {str(e)}", exc_info=True)

    # ===================================================================
    # Summary
    # ===================================================================
    logger.info("\n" + "="*80)
    logger.info("VOICE CLONING COMPLETE")
    logger.info("="*80)
    logger.info(f"Reference voice: {REFERENCE_VOICE}")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info("\nGenerated files:")
    for audio_file in sorted(OUTPUT_DIR.glob(f"juliet_*_{timestamp}.wav")):
        file_size = audio_file.stat().st_size / 1024  # KB
        logger.info(f"  - {audio_file.name} ({file_size:.2f} KB)")
    logger.info("="*80 + "\n")


if __name__ == "__main__":
    main()
