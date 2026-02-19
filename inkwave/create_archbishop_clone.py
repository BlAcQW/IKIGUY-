"""
Create Archbishop Nicholas Duncan-Williams voice clone for shared use across all apps.

This script:
1. Copies the 56-minute reference audio to shared storage
2. Creates voice clone record in kasaai_core database (accessible to all apps)
3. Generates sample audio using F5-TTS
4. Saves sample audio to publicly accessible location
"""

import asyncio
import base64
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv("/opt/kasaai/.env")

# MongoDB connection
MONGO_URI = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin"

# File paths
ARCHBISHOP_SOURCE = "/opt/kasaai/apps/voice-lab/voices/archbishop_1.wav"
SHARED_STORAGE = "/opt/kasaai/apps/shared/storage"
VOICE_CLONES_DIR = f"{SHARED_STORAGE}/voice_clones"
VOICE_SAMPLES_DIR = f"{SHARED_STORAGE}/voice_samples"

# Voice clone configuration
CLONE_ID = "voice_archbishop_official"
VOICE_NAME = "Archbishop Nicholas Duncan-Williams (Official)"
DESCRIPTION = "Official high-quality voice clone using 56 minutes of professional studio recordings"
USER_ID = "system"  # System-level voice clone accessible to all users


async def create_archbishop_clone():
    """Create Archbishop voice clone and generate sample audio."""

    print("=" * 80)
    print("Creating Archbishop Nicholas Duncan-Williams Voice Clone")
    print("=" * 80)
    print()

    # 1. Setup storage directories
    print("📁 Step 1: Setting up storage directories...")
    os.makedirs(VOICE_CLONES_DIR, exist_ok=True)
    os.makedirs(VOICE_SAMPLES_DIR, exist_ok=True)
    print(f"   ✓ Voice clones directory: {VOICE_CLONES_DIR}")
    print(f"   ✓ Voice samples directory: {VOICE_SAMPLES_DIR}")
    print()

    # 2. Copy reference audio
    print("📋 Step 2: Copying 56-minute reference audio...")
    source_path = Path(ARCHBISHOP_SOURCE)
    if not source_path.exists():
        print(f"   ❌ ERROR: Source audio not found: {ARCHBISHOP_SOURCE}")
        return False

    source_size_mb = source_path.stat().st_size / (1024 * 1024)
    print(f"   Source: {ARCHBISHOP_SOURCE}")
    print(f"   Size: {source_size_mb:.2f} MB")

    dest_path = Path(VOICE_CLONES_DIR) / "archbishop_56min.wav"
    shutil.copy2(source_path, dest_path)
    print(f"   ✓ Copied to: {dest_path}")
    print()

    # 3. Connect to MongoDB
    print("🗄️  Step 3: Connecting to kasaai_core database...")
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client.kasaai_core

        # Test connection
        await db.command("ping")
        print("   ✓ Connected to MongoDB (kasaai_core database)")
    except Exception as e:
        print(f"   ❌ ERROR: MongoDB connection failed: {e}")
        return False
    print()

    # 4. Create voice clone record
    print("💾 Step 4: Creating voice clone database record...")

    # Check if clone already exists
    existing = await db.voice_clones.find_one({"clone_id": CLONE_ID})
    if existing:
        print(f"   ⚠️  Voice clone already exists: {CLONE_ID}")
        print("   Updating existing record...")
        await db.voice_clones.delete_one({"clone_id": CLONE_ID})

    voice_clone_record = {
        "clone_id": CLONE_ID,
        "user_id": USER_ID,
        "voice_name": VOICE_NAME,
        "description": DESCRIPTION,
        "reference_audio_path": str(dest_path),
        "reference_audio_url": f"https://api.ailabsafrica.com/storage/voice_clones/archbishop_56min.wav",
        "sample_audio_url": None,  # Will be updated after sample generation
        "provider": "f5tts",
        "language": "en",
        "duration_seconds": 3377,  # 56:17 = 3377 seconds
        "file_size_bytes": int(source_size_mb * 1024 * 1024),
        "quality": "professional",
        "shared": True,  # Available to all apps
        "created_at": datetime.utcnow(),
        "metadata": {
            "recording_quality": "studio",
            "sample_rate": "44.1kHz",
            "bit_depth": "16-bit",
            "channels": "stereo",
            "source": "voice-lab/voices/archbishop_1.wav"
        }
    }

    result = await db.voice_clones.insert_one(voice_clone_record)
    print(f"   ✓ Voice clone record created: {CLONE_ID}")
    print(f"   Database ID: {result.inserted_id}")
    print()

    # 5. Generate sample audio using F5-TTS
    print("🎤 Step 5: Generating sample audio with F5-TTS...")
    sample_text = (
        "Welcome to AI Labs Africa voice services. "
        "This is Archbishop Nicholas Duncan-Williams speaking. "
        "May God's grace and peace be with you."
    )
    print(f"   Sample text: \"{sample_text}\"")
    print(f"   Provider: F5-TTS (voice cloning enabled)")

    try:
        # Import shared TTS service
        from apps.shared.services.tts_provider_service import (
            TTSProviderService,
            VoiceCloneRequest
        )

        # Read reference audio
        with open(dest_path, "rb") as f:
            reference_audio_bytes = f.read()

        reference_audio_base64 = base64.b64encode(reference_audio_bytes).decode('utf-8')
        print(f"   Reference audio size: {len(reference_audio_bytes) / (1024 * 1024):.2f} MB")

        # Initialize TTS service (no billing for system clone creation)
        tts_service = TTSProviderService(enable_billing=False)
        await tts_service.initialize()

        # Generate sample audio
        print("   Calling F5-TTS voice cloning service...")
        result = await tts_service.synthesize_with_voice_cloning(
            user_id=USER_ID,
            request=VoiceCloneRequest(
                provider_id="f5tts",
                text=sample_text,
                reference_audio_base64=reference_audio_base64,
                language="en",
                speed=1.0
            ),
            skip_billing=True
        )

        print(f"   ✓ Sample audio generated!")
        print(f"   Duration: {result.duration:.2f} seconds")
        print(f"   Provider: {result.provider_id}")

        # Save sample audio
        sample_filename = "archbishop_sample.wav"
        sample_path = Path(VOICE_SAMPLES_DIR) / sample_filename

        # Decode base64 audio and save
        audio_bytes = base64.b64decode(result.audio_base64)
        with open(sample_path, "wb") as f:
            f.write(audio_bytes)

        sample_url = f"https://api.ailabsafrica.com/storage/voice_samples/{sample_filename}"
        print(f"   ✓ Sample saved: {sample_path}")
        print(f"   Public URL: {sample_url}")

        # Update voice clone record with sample URL
        await db.voice_clones.update_one(
            {"clone_id": CLONE_ID},
            {"$set": {"sample_audio_url": sample_url}}
        )
        print(f"   ✓ Database record updated with sample URL")

    except Exception as e:
        print(f"   ⚠️  Sample audio generation failed: {e}")
        print(f"   Voice clone created but no sample available")
        sample_url = None

    print()

    # 6. Verify record in database
    print("✅ Step 6: Verifying voice clone...")
    final_record = await db.voice_clones.find_one({"clone_id": CLONE_ID})
    if final_record:
        print(f"   ✓ Voice clone verified in kasaai_core.voice_clones")
        print(f"   Clone ID: {final_record['clone_id']}")
        print(f"   Voice Name: {final_record['voice_name']}")
        print(f"   Provider: {final_record['provider']}")
        print(f"   Shared: {final_record['shared']}")
        print(f"   Reference Audio: {final_record['reference_audio_url']}")
        if final_record.get('sample_audio_url'):
            print(f"   Sample Audio: {final_record['sample_audio_url']}")
    else:
        print(f"   ❌ ERROR: Voice clone not found in database!")
        return False

    print()
    print("=" * 80)
    print("✨ SUCCESS! Archbishop voice clone created successfully!")
    print("=" * 80)
    print()
    print("🎯 Voice Clone Details:")
    print(f"   Clone ID: {CLONE_ID}")
    print(f"   Voice Name: {VOICE_NAME}")
    print(f"   Database: kasaai_core.voice_clones (shared across all apps)")
    print(f"   Reference Audio: 56 minutes, 569 MB, professional studio quality")
    print(f"   Provider: F5-TTS (best for voice cloning)")
    print()

    if sample_url:
        print("🔊 Sample Audio:")
        print(f"   URL: {sample_url}")
        print(f"   File: {sample_path}")
        print()

    print("📱 Accessible In:")
    print("   ✓ InkWave - Book narration")
    print("   ✓ ChurchFlow - Voice greetings")
    print("   ✓ StudyFlow - Study materials")
    print("   ✓ EventFlow - Ama assistant")
    print("   ✓ B2C Portal - Voice Studio")
    print()

    return True


if __name__ == "__main__":
    success = asyncio.run(create_archbishop_clone())
    sys.exit(0 if success else 1)
