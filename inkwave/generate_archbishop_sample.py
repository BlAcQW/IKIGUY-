"""
Generate sample audio for Archbishop Nicholas Duncan-Williams voice clone.
"""

import asyncio
import base64
import os
import sys
from pathlib import Path

# Add parent directory to path for shared imports
sys.path.insert(0, "/opt/kasaai/apps")

from motor.motor_asyncio import AsyncIOMotorClient
from shared.services.tts_provider_service import (
    TTSProviderService,
    VoiceCloneRequest
)

# MongoDB connection
MONGO_URI = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin"

# Paths
REFERENCE_AUDIO_PATH = "/opt/kasaai/apps/shared/storage/voice_clones/archbishop_56min.wav"
SAMPLE_OUTPUT_DIR = "/opt/kasaai/apps/shared/storage/voice_samples"
CLONE_ID = "voice_archbishop_official"


async def generate_sample():
    """Generate sample audio using F5-TTS voice cloning."""

    print("=" * 80)
    print("Generating Archbishop Voice Clone Sample Audio")
    print("=" * 80)
    print()

    # Sample text
    sample_text = (
        "Welcome to AI Labs Africa voice services. "
        "This is Archbishop Nicholas Duncan-Williams speaking. "
        "May God's grace and peace be with you."
    )

    print(f"📝 Sample text: \"{sample_text}\"")
    print(f"🎤 Provider: F5-TTS (voice cloning)")
    print()

    # Read reference audio
    print("📁 Reading reference audio...")
    reference_audio_path = Path(REFERENCE_AUDIO_PATH)
    if not reference_audio_path.exists():
        print(f"   ❌ ERROR: Reference audio not found: {REFERENCE_AUDIO_PATH}")
        return False

    with open(reference_audio_path, "rb") as f:
        reference_audio_bytes = f.read()

    reference_audio_base64 = base64.b64encode(reference_audio_bytes).decode('utf-8')
    print(f"   ✓ Reference audio loaded: {len(reference_audio_bytes) / (1024 * 1024):.2f} MB")
    print()

    # Initialize TTS service
    print("🔧 Initializing TTS service...")
    try:
        tts_service = TTSProviderService(enable_billing=False)
        await tts_service.initialize()
        print("   ✓ TTS service initialized")
    except Exception as e:
        print(f"   ❌ ERROR: TTS service initialization failed: {e}")
        return False
    print()

    # Generate audio
    print("🎵 Generating audio with voice cloning...")
    try:
        result = await tts_service.synthesize_with_voice_cloning(
            user_id="system",
            request=VoiceCloneRequest(
                provider_id="f5tts",
                text=sample_text,
                reference_audio_base64=reference_audio_base64,
                language="en",
                speed=1.0
            ),
            skip_billing=True
        )

        print(f"   ✓ Audio generated successfully!")
        print(f"   Duration: {result.duration:.2f} seconds")
        print(f"   Provider: {result.provider_id}")
        print()

    except Exception as e:
        print(f"   ❌ ERROR: Audio generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Save sample audio
    print("💾 Saving sample audio...")
    os.makedirs(SAMPLE_OUTPUT_DIR, exist_ok=True)

    sample_filename = "archbishop_sample.wav"
    sample_path = Path(SAMPLE_OUTPUT_DIR) / sample_filename

    # Decode base64 audio and save
    audio_bytes = base64.b64decode(result.audio_base64)
    with open(sample_path, "wb") as f:
        f.write(audio_bytes)

    sample_url = f"https://api.ailabsafrica.com/storage/voice_samples/{sample_filename}"
    print(f"   ✓ Sample saved: {sample_path}")
    print(f"   Size: {len(audio_bytes) / 1024:.2f} KB")
    print(f"   Public URL: {sample_url}")
    print()

    # Update database record
    print("🗄️  Updating database record...")
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client.kasaai_core

        result = await db.voice_clones.update_one(
            {"clone_id": CLONE_ID},
            {"$set": {"sample_audio_url": sample_url}}
        )

        if result.modified_count > 0:
            print(f"   ✓ Database record updated with sample URL")
        else:
            print(f"   ⚠️  Database record not modified (may already have sample URL)")

    except Exception as e:
        print(f"   ⚠️  Database update failed: {e}")

    print()
    print("=" * 80)
    print("✅ SUCCESS! Sample audio generated and saved!")
    print("=" * 80)
    print()
    print("🔊 Sample Audio URL:")
    print(f"   {sample_url}")
    print()
    print("📁 Local File:")
    print(f"   {sample_path}")
    print()

    return True


if __name__ == "__main__":
    success = asyncio.run(generate_sample())
    sys.exit(0 if success else 1)
