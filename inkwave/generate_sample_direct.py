"""
Generate sample audio for Archbishop voice clone using direct F5-TTS API call.
"""

import asyncio
import aiohttp
import base64
import os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient

# Configuration
F5TTS_URL = "https://f5tts.ailabsafrica.com/clone"
# Use 45-second reference audio (recommended size for voice cloning)
REFERENCE_AUDIO_PATH = "/opt/kasaai/apps/voice-lab/voices/archbishop_1_ref.wav"
SAMPLE_OUTPUT_DIR = "/opt/kasaai/apps/shared/storage/voice_samples"
CLONE_ID = "voice_archbishop_official"
MONGO_URI = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin"


async def generate_sample():
    """Generate sample audio using direct F5-TTS API call."""

    print("=" * 80)
    print("Generating Archbishop Voice Clone Sample Audio (Direct API)")
    print("=" * 80)
    print()

    sample_text = (
        "Welcome to AI Labs Africa voice services. "
        "This is Archbishop Nicholas Duncan-Williams speaking. "
        "May God's grace and peace be with you."
    )

    print(f"📝 Sample text: \"{sample_text}\"")
    print(f"🎤 Provider: F5-TTS")
    print(f"🌐 API URL: {F5TTS_URL}")
    print()

    # Read reference audio
    print("📁 Reading reference audio...")
    reference_path = Path(REFERENCE_AUDIO_PATH)
    if not reference_path.exists():
        print(f"   ❌ ERROR: Reference audio not found: {REFERENCE_AUDIO_PATH}")
        return False

    with open(reference_path, "rb") as f:
        reference_audio_bytes = f.read()

    reference_audio_base64 = base64.b64encode(reference_audio_bytes).decode('utf-8')
    print(f"   ✓ Reference audio loaded: {len(reference_audio_bytes) / (1024 * 1024):.2f} MB")
    print()

    # Call F5-TTS API
    print("🎵 Calling F5-TTS voice cloning API...")
    try:
        async with aiohttp.ClientSession() as session:
            # Prepare FormData for file upload (not JSON!)
            form_data = aiohttp.FormData()
            form_data.add_field(
                'ref_audio',
                reference_audio_bytes,
                filename='reference.wav',
                content_type='audio/wav'
            )
            form_data.add_field('text', sample_text)
            form_data.add_field('language', 'en')
            form_data.add_field('speed', '1.0')
            form_data.add_field('remove_silence', 'true')

            print(f"   Sending FormData request to {F5TTS_URL}...")
            async with session.post(
                F5TTS_URL,
                data=form_data,
                timeout=aiohttp.ClientTimeout(total=120)  # 2 minute timeout
            ) as response:
                if response.status == 200:
                    # F5-TTS returns audio/wav directly, not JSON
                    audio_bytes = await response.read()
                    print(f"   ✓ Audio generated successfully!")
                    print(f"   Audio size: {len(audio_bytes) / 1024:.2f} KB")

                else:
                    error_text = await response.text()
                    print(f"   ❌ ERROR: API returned status {response.status}")
                    print(f"   Response: {error_text}")
                    return False

    except Exception as e:
        print(f"   ❌ ERROR: API call failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()

    # Save sample audio
    print("💾 Saving sample audio...")
    os.makedirs(SAMPLE_OUTPUT_DIR, exist_ok=True)

    sample_filename = "archbishop_sample.wav"
    sample_path = Path(SAMPLE_OUTPUT_DIR) / sample_filename

    # Save audio bytes directly
    with open(sample_path, "wb") as f:
        f.write(audio_bytes)

    sample_url = f"https://api.ailabsafrica.com/storage/voice_samples/{sample_filename}"
    print(f"   ✓ Sample saved: {sample_path}")
    print(f"   Size: {len(audio_bytes) / 1024:.2f} KB")
    print(f"   Public URL: {sample_url}")
    print()

    # Update database
    print("🗄️  Updating database record...")
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client.kasaai_core

        result = await db.voice_clones.update_one(
            {"clone_id": CLONE_ID},
            {"$set": {"sample_audio_url": sample_url}}
        )

        if result.modified_count > 0:
            print(f"   ✓ Database record updated")
        else:
            print(f"   ⚠️  Database record not modified")

        client.close()

    except Exception as e:
        print(f"   ⚠️  Database update failed: {e}")

    print()
    print("=" * 80)
    print("✅ SUCCESS! Sample audio generated!")
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
    import sys
    success = asyncio.run(generate_sample())
    sys.exit(0 if success else 1)
