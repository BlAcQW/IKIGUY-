#!/usr/bin/env python3
"""
Script to trigger audio pre-generation for reprocessed books.
"""
import asyncio
import sys
import os

# Add paths
sys.path.insert(0, '/opt/kasaai/apps')
sys.path.insert(0, '/opt/kasaai/apps/inkwave/backend')

# Set environment variables
os.environ.setdefault('SUPABASE_URL', 'https://supabase.ailabsafrica.com')
os.environ.setdefault('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0')
os.environ.setdefault('MONGODB_URI', 'mongodb://admin:aawwER4444%40@127.0.0.1:27017/?authSource=admin')
os.environ.setdefault('MONGODB_DB_NAME', 'inkwave')


async def main():
    """Trigger audio pre-generation for reprocessed books."""
    from app.core.database import Database
    from app.services.audio_pregeneration_service import get_audio_pregeneration_service

    # Books to process
    books = [
        ('book_0abbea43dbcf', 'Gratitude'),
        ('book_da6dd62d1a91', 'Dont Fight the Process'),
        ('book_da7705efdff4', 'Understanding the End Times')
    ]

    user_id = 'admin-test-user'

    print("Connecting to MongoDB...")
    await Database.connect()
    print("Connected!\n")

    service = await get_audio_pregeneration_service()

    for book_id, title in books:
        print(f"=== {title} ({book_id}) ===")

        # Default voice settings
        voice_settings = {
            "provider_id": "kokoro",
            "voice_id": "am_michael",
            "speed": 1.0,
            "language": "en"
        }

        try:
            print(f"Starting audio pre-generation...")
            result = await service.pregenerate_book_audio(
                book_id=book_id,
                user_id=user_id,
                voice_settings=voice_settings,
                max_chunks=10  # Start with first 10 playable chunks
            )

            print(f"✓ Success!")
            print(f"  Generated: {result.get('generated_count', 0)}")
            print(f"  Skipped: {result.get('skipped_count', 0)}")
            print(f"  Failed: {result.get('failed_count', 0)}")
            print()

        except Exception as e:
            print(f"✗ Error: {e}\n")

    await Database.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
