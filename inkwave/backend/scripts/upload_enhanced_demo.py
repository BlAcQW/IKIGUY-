"""
Upload enhanced demo book to InkWave.

This script uploads the enhanced "Binding The Strong Man" demo book
with 4,297 words (~28.6 minutes of audio content).
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Database
from app.services.book_service import BookService


async def main():
    """Upload enhanced demo book."""

    print("\n🚀 Uploading Enhanced Demo Book")
    print("=" * 60)

    try:
        # Connect to database
        print("📡 Connecting to database...")
        await Database.connect()
        print("✅ Database connected\n")

        # Read the enhanced demo book
        book_path = Path(__file__).parent.parent / "test_books" / "binding_the_strong_man_demo.pdf"

        if not book_path.exists():
            print(f"❌ Book file not found: {book_path}")
            return

        print(f"📖 Reading book from: {book_path}")
        with open(book_path, 'rb') as f:
            file_content = f.read()

        print(f"   File size: {len(file_content) / 1024:.2f} KB")

        # Upload with metadata
        print("\n⚙️  Processing and uploading book...")
        result = await BookService.upload_book(
            file_content=file_content,
            filename='binding_the_strong_man_demo.pdf',
            title='Binding The Strong Man - Enhanced Demo',
            author='Archbishop Nicholas Duncan-Williams',
            description='A comprehensive study on spiritual warfare with extended content for audio testing. This enhanced demo includes 4,297 words (~28.6 minutes of audio) packed with detailed biblical teachings on identifying and binding the strong man, spiritual weapons, and breaking free from bondage.',
            uploaded_by='admin',
            cover_url='https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400',
            duration_minutes=29,
            narrator='AI Narrator'
        )

        print("\n" + "=" * 60)
        print("✅ BOOK UPLOADED SUCCESSFULLY!")
        print("=" * 60)
        print(f"📚 Title: {result['title']}")
        print(f"🆔 Book ID: {result['book_id']}")
        print(f"📊 Status: {result['status']}")
        print(f"📑 Chapters: {result['chapters_extracted']}")
        print(f"⏱️  Processing Time: {result['processing_time_seconds']:.2f}s")
        print("\n📖 Content Stats:")
        print("   • Total Words: 4,297")
        print("   • Estimated Audio: ~28.6 minutes")
        print("   • Words per Chapter: ~750-1,000")
        print("   • Audio per Chapter: ~5-7 minutes")
        print("\n🎯 Next Steps:")
        print(f"   1. Navigate to: https://dev-inkwave.ailabsafrica.com/book/{result['book_id']}")
        print("   2. Click 'Start Listening' to test audio generation")
        print("   3. Experience 5+ minutes of continuous AI narration per chapter!")
        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Disconnect from database
        await Database.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
