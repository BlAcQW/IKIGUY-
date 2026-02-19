"""
Initialize MongoDB indexes for voice_settings collection

Run this script once to create the necessary indexes for voice settings.

Usage:
    python -m apps.shared.services.init_voice_settings_indexes
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from voice_settings_service import VoiceSettingsService


async def init_indexes():
    """Initialize MongoDB indexes for voice_settings."""
    # Get MongoDB connection from environment
    # Use proper URL encoding for password
    from urllib.parse import quote_plus
    password = quote_plus("aawwER4444")
    mongodb_uri = os.getenv("MONGODB_URI", f"mongodb://admin:{password}@127.0.0.1:27017/")

    # Connect to all databases that need voice_settings
    databases = ["inkwave", "studyflow", "eventflow", "churchflow", "kasaai_core"]

    client = AsyncIOMotorClient(mongodb_uri)

    for db_name in databases:
        try:
            print(f"\n🔧 Initializing indexes for {db_name}...")
            db = client[db_name]
            service = VoiceSettingsService(db)
            await service.ensure_indexes()
            print(f"✅ Indexes created for {db_name}")
        except Exception as e:
            print(f"❌ Error creating indexes for {db_name}: {e}")

    client.close()
    print("\n✨ Index initialization complete!")


if __name__ == "__main__":
    asyncio.run(init_indexes())
