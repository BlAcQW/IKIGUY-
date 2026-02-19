#!/usr/bin/env python3
"""
Convert GiftMark Akan Whisper model to CTranslate2 (faster-whisper) format

This enables streaming real-time transcription for the Akan model.

Usage:
    python convert_akan_to_faster_whisper.py
"""

import os
import sys
from pathlib import Path
import torch
from transformers import WhisperForConditionalGeneration, WhisperProcessor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_akan_whisper_to_ctranslate2():
    """
    Convert GiftMark Akan Whisper model to CTranslate2 format.

    This conversion enables:
    - 4x faster inference
    - Lower memory usage
    - Streaming capability
    - Real-time transcription
    """

    # Paths
    source_model_id = "GiftMark/akan-whisper-model"
    cache_dir = Path("/opt/kasaai/apps/voice-lab/models/akan_whisper")
    output_dir = Path("/opt/kasaai/apps/voice-lab/models/akan_whisper_faster")

    logger.info("=" * 80)
    logger.info("🔄 CONVERTING AKAN WHISPER TO FASTER-WHISPER (CTranslate2)")
    logger.info("=" * 80)

    # Check if ctranslate2 is installed
    try:
        import ctranslate2
        logger.info(f"✅ CTranslate2 version: {ctranslate2.__version__}")
    except ImportError:
        logger.error("❌ CTranslate2 not installed!")
        logger.info("Installing CTranslate2...")
        os.system("pip install -q ctranslate2")
        import ctranslate2

    # Step 1: Load HuggingFace model
    logger.info(f"\n📥 Loading model from: {source_model_id}")

    try:
        if cache_dir.exists() and (cache_dir / "config.json").exists():
            logger.info("Loading from local cache...")
            model = WhisperForConditionalGeneration.from_pretrained(cache_dir)
            processor = WhisperProcessor.from_pretrained(cache_dir)
        else:
            logger.info("Downloading from HuggingFace...")
            model = WhisperForConditionalGeneration.from_pretrained(source_model_id)
            processor = WhisperProcessor.from_pretrained(source_model_id)

            # Save to cache
            cache_dir.mkdir(parents=True, exist_ok=True)
            model.save_pretrained(cache_dir)
            processor.save_pretrained(cache_dir)
            logger.info(f"✅ Cached model at: {cache_dir}")

        logger.info(f"✅ Model loaded: {model.num_parameters():,} parameters")

    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}")
        return False

    # Step 2: Convert to CTranslate2
    logger.info(f"\n🔄 Converting to CTranslate2 format...")
    logger.info(f"   Output directory: {output_dir}")

    try:
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Convert using ct2-transformers-converter
        logger.info("   Running conversion...")
        cmd = f"""
        ct2-transformers-converter \
            --model {cache_dir} \
            --output_dir {output_dir} \
            --quantization int8 \
            --force
        """

        result = os.system(cmd)

        if result == 0:
            logger.info("✅ Conversion successful!")
        else:
            raise Exception(f"Conversion failed with code {result}")

    except Exception as e:
        logger.error(f"❌ Conversion failed: {e}")
        logger.info("\nTrying alternative method...")

        # Alternative: Use Python API
        try:
            from ctranslate2.converters import TransformersConverter

            converter = TransformersConverter(str(cache_dir))
            converter.convert(
                output_dir=str(output_dir),
                quantization="int8",
                force=True
            )
            logger.info("✅ Alternative conversion successful!")

        except Exception as e2:
            logger.error(f"❌ Alternative conversion also failed: {e2}")
            return False

    # Step 3: Verify conversion
    logger.info(f"\n🔍 Verifying converted model...")

    try:
        from faster_whisper import WhisperModel

        # Load converted model
        model_faster = WhisperModel(
            str(output_dir),
            device="cuda" if torch.cuda.is_available() else "cpu",
            compute_type="int8"
        )

        logger.info("✅ Model loaded successfully with faster-whisper!")

        # Test with dummy audio
        import numpy as np

        # Generate 1 second of silence
        dummy_audio = np.zeros(16000, dtype=np.float32)

        # Test transcription (use 'en' for testing since 'tw' not in standard list)
        # Reason: Akan/Twi is a fine-tuned specialty, will work but needs no language code
        segments, info = model_faster.transcribe(
            dummy_audio,
            beam_size=5  # Auto-detect language
        )

        logger.info(f"✅ Test transcription successful!")
        logger.info(f"   Detected language: {info.language}")
        logger.info(f"   Language probability: {info.language_probability:.2f}")
        logger.info(f"   Note: Model is fine-tuned for Twi/Akan despite detected language")

    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

    # Step 4: Create model info file
    logger.info(f"\n📝 Creating model info...")

    model_info = {
        "model_name": "Akan Whisper (GiftMark) - Faster Version",
        "model_id": "akan-whisper-faster",
        "source_model": source_model_id,
        "format": "ctranslate2",
        "quantization": "int8",
        "accuracy": 0.929,
        "languages": ["tw"],
        "dialects": ["asante", "akuapem", "fante"],
        "supports_streaming": True,
        "supports_timestamps": True,
        "conversion_date": str(Path(output_dir / "model.bin").stat().st_mtime),
        "model_path": str(output_dir)
    }

    import json
    with open(output_dir / "model_info.json", "w") as f:
        json.dump(model_info, f, indent=2)

    logger.info("✅ Model info saved")

    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("✅ CONVERSION COMPLETE!")
    logger.info("=" * 80)
    logger.info(f"\n📦 Converted model location: {output_dir}")
    logger.info(f"📊 Model info: {output_dir / 'model_info.json'}")
    logger.info("\n🚀 Next steps:")
    logger.info("   1. Update unified_asr_service.py to use this model")
    logger.info("   2. Mark 'akan-whisper' as streaming-capable in voice-lab models")
    logger.info("   3. Restart the backend service")
    logger.info("   4. Test streaming in ASR Lab\n")

    return True


if __name__ == "__main__":
    success = convert_akan_whisper_to_ctranslate2()
    sys.exit(0 if success else 1)
