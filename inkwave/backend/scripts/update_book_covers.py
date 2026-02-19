"""
Update all books with proper cover images for a better UI experience.

This script updates existing books with appropriate cover images.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient


# Cover image mappings for existing books
BOOK_COVERS = {
    "Binding the Strongman": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&h=900&fit=crop",
    "Enforcing Prophetic Decrees": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=600&h=900&fit=crop",
    "Praying Through the Promises of God": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=600&h=900&fit=crop",
    "Prayer Moves God": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=600&h=900&fit=crop",
    "The Incredible Power of a Praying Woman": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=600&h=900&fit=crop",
    "Powers Behind the Scenes": "https://images.unsplash.com/photo-1507591064344-4c6ce005b128?w=600&h=900&fit=crop",
    "Turning Pain to Power": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=600&h=900&fit=crop",
    "Destined to Make an Impact": "https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=600&h=900&fit=crop",
    "The Power of Faith: A Journey to Spiritual Victory": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=600&h=900&fit=crop"
}


async def update_covers():
    """Update book covers in database."""

    print("🎨 Updating book cover images...\n")

    # Connect to MongoDB
    mongo_url = 'mongodb://admin:aawwER4444%25@127.0.0.1:27017/?authSource=admin'
    client = AsyncIOMotorClient(mongo_url)
    db = client['inkwave']

    try:
        # Get all books
        books = await db.books.find().to_list(100)
        updated_count = 0

        for book in books:
            title = book.get('title', '')
            current_cover = book.get('cover_url', '')

            # Get cover URL from mapping
            new_cover = BOOK_COVERS.get(title)

            if new_cover and (not current_cover or current_cover != new_cover):
                # Update book cover
                result = await db.books.update_one(
                    {'book_id': book['book_id']},
                    {'$set': {'cover_url': new_cover}}
                )

                if result.modified_count > 0:
                    print(f"✅ Updated: {title}")
                    print(f"   Cover: {new_cover[:60]}...")
                    updated_count += 1
            else:
                print(f"⏭️  Skipped: {title} (cover already set or no mapping found)")

        print(f"\n📊 Summary:")
        print(f"   Total books: {len(books)}")
        print(f"   Updated: {updated_count}")
        print(f"   Skipped: {len(books) - updated_count}")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(update_covers())
