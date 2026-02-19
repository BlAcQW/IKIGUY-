"""
Add Archbishop voice clone to the cloned_voices collection.

This collection is used by the Voice Studio UI and other apps.
"""

import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin"

async def add_to_cloned_voices():
    """Add Archbishop voice to cloned_voices collection."""

    print("=" * 80)
    print("Adding Archbishop Voice to cloned_voices Collection")
    print("=" * 80)
    print()

    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.kasaai_core

    # Check if already exists
    existing = await db.cloned_voices.find_one({"voice_id": "voice_archbishop_official"})
    if existing:
        print("⚠️  Archbishop voice already exists in cloned_voices collection")
        print("   Updating record...")
        await db.cloned_voices.delete_one({"voice_id": "voice_archbishop_official"})
    print()

    # Create record following ClonedVoiceModel schema
    now = datetime.utcnow()
    voice_record = {
        "voice_id": "voice_archbishop_official",
        "name": "Archbishop Nicholas Duncan-Williams",
        "provider": "f5tts",
        "reference_audio_path": "/opt/kasaai/apps/shared/storage/voice_clones/archbishop_56min.wav",
        "reference_audio_size": 595859470,  # 568 MB
        "cloned_at": "2025-11-03T21:21:06.291Z",
        "language": "en",
        "gender": "male",
        "accent": "Ghanaian",
        "description": "Official high-quality voice clone of Archbishop Nicholas Duncan-Williams using 56 minutes of professional studio recordings. Available for church services, sermons, and spiritual content.",
        "capabilities": ["voice_cloning", "multi_language", "high_quality"],
        "status": "completed",
        "error_message": None,
        "created_at": now,
        "updated_at": now,
        # Additional metadata for reference
        "sample_audio_url": "https://api.ailabsafrica.com/storage/voice_samples/archbishop_sample.wav",
        "shared": True,
        "quality": "professional"
    }

    result = await db.cloned_voices.insert_one(voice_record)
    print(f"✅ Archbishop voice added to cloned_voices collection")
    print(f"   Voice ID: voice_archbishop_official")
    print(f"   Database ID: {result.inserted_id}")
    print(f"   Provider: f5tts")
    print(f"   Status: completed")
    print()

    # Verify record
    voice = await db.cloned_voices.find_one({"voice_id": "voice_archbishop_official"})
    if voice:
        print(f"✅ Verified in database:")
        print(f"   Name: {voice['name']}")
        print(f"   Accent: {voice['accent']}")
        print(f"   Language: {voice['language']}")
        print(f"   Description: {voice['description'][:80]}...")
        print()

    # Check total cloned voices
    total = await db.cloned_voices.count_documents({})
    print(f"📊 Total cloned voices in collection: {total}")
    print()

    client.close()

    print("=" * 80)
    print("✅ SUCCESS!")
    print("=" * 80)
    print()
    print("Archbishop voice is now accessible in:")
    print("   ✓ Voice Studio UI (B2C Portal)")
    print("   ✓ ChurchFlow voice selection")
    print("   ✓ StudyFlow voice selection")
    print("   ✓ EventFlow voice selection")
    print("   ✓ InkWave narration")
    print()

    return True


if __name__ == "__main__":
    import sys
    success = asyncio.run(add_to_cloned_voices())
    sys.exit(0 if success else 1)
