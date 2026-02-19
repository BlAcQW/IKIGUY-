"""
Script to add more Archbishop Duncan-Williams books to InkWave library.

This script adds books with proper metadata including:
- Title and author
- Genres/categories aligned with church recommendations
- Descriptions
- Cover images
- Processing status
"""

import asyncio
import secrets
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from motor.motor_asyncio import AsyncIOMotorClient


# MongoDB connection details
MONGODB_URI = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/"
DB_NAME = "inkwave"


def generate_book_id() -> str:
    """Generate unique book ID."""
    return f"book_{secrets.token_hex(6)}"


# New books to add
NEW_BOOKS = [
    {
        "title": "The Supernatural Powers of a Praying Man",
        "author": "Archbishop Nicholas Duncan-Williams",
        "cover_url": "https://m.media-amazon.com/images/I/51SPQG22Y6L._SL500_.jpg",
        "description": "Discover the supernatural authority and power available to men who pray. Learn how to tap into divine strength and become the spiritual leader God has called you to be.",
        "genre": ["Christian", "Prayer", "Men's Ministry", "Spiritual Growth"],
        "themes": ["Prayer", "Faith", "Leadership", "Spiritual Warfare"],
        "difficulty_level": "intermediate",
        "estimated_reading_time_minutes": 35
    },
    {
        "title": "Divine Timing: Avoiding the Dangers of Premature Exposure",
        "author": "Archbishop Nicholas Duncan-Williams",
        "cover_url": "https://m.media-amazon.com/images/I/51SPQG22Y6L._SL500_.jpg",
        "description": "Understanding God's timing is crucial for success. This powerful teaching reveals the dangers of moving ahead of God's schedule and how to discern His perfect timing for your life.",
        "genre": ["Christian", "Purpose", "Leadership", "Spiritual Growth"],
        "themes": ["Purpose", "Faith", "Leadership", "Wisdom"],
        "difficulty_level": "intermediate",
        "estimated_reading_time_minutes": 30
    },
    {
        "title": "The Price of Greatness: Understanding the Power of Persevering",
        "author": "Archbishop Nicholas Duncan-Williams",
        "cover_url": "https://m.media-amazon.com/images/I/51SPQG22Y6L._SL500_.jpg",
        "description": "Greatness comes at a price. Learn about the power of perseverance, endurance, and staying committed to God's call even when facing challenges and opposition.",
        "genre": ["Christian", "Leadership", "Inspiration", "Purpose"],
        "themes": ["Leadership", "Faith", "Purpose", "Perseverance"],
        "difficulty_level": "intermediate",
        "estimated_reading_time_minutes": 32
    },
    {
        "title": "Understanding the Father Factor",
        "author": "Archbishop Nicholas Duncan-Williams",
        "cover_url": "https://m.media-amazon.com/images/I/51SPQG22Y6L._SL500_.jpg",
        "description": "Explore the powerful impact of the father-child relationship and how understanding God as Father can heal wounds, restore identity, and unlock your destiny.",
        "genre": ["Christian", "Family", "Healing", "Deliverance"],
        "themes": ["Family", "Healing", "Identity", "Restoration"],
        "difficulty_level": "intermediate",
        "estimated_reading_time_minutes": 33
    },
    {
        "title": "When Mothers Pray",
        "author": "Archbishop Nicholas Duncan-Williams",
        "cover_url": "https://m.media-amazon.com/images/I/51SPQG22Y6L._SL500_.jpg",
        "description": "A powerful message honoring the prayers of mothers and revealing the supernatural impact they have on their children, families, and nations.",
        "genre": ["Christian", "Prayer", "Women's Ministry", "Family"],
        "themes": ["Prayer", "Family", "Faith", "Women"],
        "difficulty_level": "beginner",
        "estimated_reading_time_minutes": 28
    },
    {
        "title": "Worship: A Secret Weapon",
        "author": "Archbishop Nicholas Duncan-Williams",
        "cover_url": "https://m.media-amazon.com/images/I/51SPQG22Y6L._SL500_.jpg",
        "description": "Discover how worship is not just singing but a powerful spiritual weapon that defeats the enemy, releases breakthrough, and ushers in God's presence.",
        "genre": ["Christian", "Praise", "Spiritual Warfare", "Worship"],
        "themes": ["Praise", "Faith", "Spiritual Warfare", "Breakthrough"],
        "difficulty_level": "beginner",
        "estimated_reading_time_minutes": 30
    },
    {
        "title": "Don't Fight the Process: Yielding Totally to God's Plan",
        "author": "Archbishop Nicholas Duncan-Williams",
        "cover_url": "https://m.media-amazon.com/images/I/51SPQG22Y6L._SL500_.jpg",
        "description": "God uses processes to prepare us for greatness. Learn to embrace the journey, trust the process, and yield completely to God's transformative work in your life.",
        "genre": ["Christian", "Spiritual Growth", "Purpose", "Faith"],
        "themes": ["Faith", "Purpose", "Growth", "Surrender"],
        "difficulty_level": "intermediate",
        "estimated_reading_time_minutes": 31
    },
    {
        "title": "Providence and Destiny: The Nicholas Duncan-Williams Story",
        "author": "Archbishop Nicholas Duncan-Williams",
        "cover_url": "https://m.media-amazon.com/images/I/51SPQG22Y6L._SL500_.jpg",
        "description": "The inspiring autobiography of Archbishop Duncan-Williams, chronicling his journey from humble beginnings to becoming a spiritual leader impacting nations through prayer and ministry.",
        "genre": ["Christian", "Biography", "Inspiration", "Leadership"],
        "themes": ["Leadership", "Faith", "Purpose", "Testimony"],
        "difficulty_level": "beginner",
        "estimated_reading_time_minutes": 45
    },
    {
        "title": "Building a Memorial",
        "author": "Archbishop Nicholas Duncan-Williams",
        "cover_url": "https://m.media-amazon.com/images/I/51SPQG22Y6L._SL500_.jpg",
        "description": "Learn the importance of building spiritual memorials to remember God's faithfulness, establish covenant markers, and create a legacy of faith for future generations.",
        "genre": ["Christian", "Faith", "Legacy", "Spiritual Growth"],
        "themes": ["Faith", "Legacy", "Covenant", "Remembrance"],
        "difficulty_level": "intermediate",
        "estimated_reading_time_minutes": 29
    },
    {
        "title": "Enforcing Prophetic Decrees Vol. 2: Prayer Watch for Community Transformation",
        "author": "Archbishop Nicholas Duncan-Williams",
        "cover_url": "https://m.media-amazon.com/images/I/51SPQG22Y6L._SL500_.jpg",
        "description": "The second volume on enforcing prophetic decrees, focusing on strategic prayer for transforming communities, cities, and nations through intercession and spiritual warfare.",
        "genre": ["Christian", "Prayer", "Prophecy", "Spiritual Warfare"],
        "themes": ["Prayer", "Prophecy", "Spiritual Warfare", "Transformation"],
        "difficulty_level": "advanced",
        "estimated_reading_time_minutes": 38
    },
    {
        "title": "The Power of the Messenger",
        "author": "Archbishop Nicholas Duncan-Williams",
        "cover_url": "https://m.media-amazon.com/images/I/51SPQG22Y6L._SL500_.jpg",
        "description": "A powerful 2024 sermon on the responsibility, benefits, and blessings of being a messenger of God. Understand your calling to carry and deliver God's message to the world.",
        "genre": ["Christian", "Leadership", "Purpose", "Ministry"],
        "themes": ["Leadership", "Purpose", "Ministry", "Calling"],
        "difficulty_level": "intermediate",
        "estimated_reading_time_minutes": 27
    },
    {
        "title": "Overcoming Fear (Part 1 & 2)",
        "author": "Archbishop Nicholas Duncan-Williams",
        "cover_url": "https://m.media-amazon.com/images/I/51SPQG22Y6L._SL500_.jpg",
        "description": "A two-part 2024 series on overcoming fear. Learn that fear is not merely an emotion but a spirit, and discover how to break free from one of Satan's most potent weapons.",
        "genre": ["Christian", "Deliverance", "Spiritual Warfare", "Faith"],
        "themes": ["Deliverance", "Faith", "Spiritual Warfare", "Freedom"],
        "difficulty_level": "intermediate",
        "estimated_reading_time_minutes": 42
    },
    {
        "title": "Breaking Invisible Barriers",
        "author": "Archbishop Nicholas Duncan-Williams",
        "cover_url": "https://m.media-amazon.com/images/I/51SPQG22Y6L._SL500_.jpg",
        "description": "A prophetic 2024 message declaring war on invisible barriers. Uncover how upbringing, mindset, ignorance, and lack of vision have become obstacles preventing your breakthrough.",
        "genre": ["Christian", "Deliverance", "Breakthrough", "Spiritual Warfare"],
        "themes": ["Deliverance", "Breakthrough", "Faith", "Freedom"],
        "difficulty_level": "intermediate",
        "estimated_reading_time_minutes": 35
    },
    {
        "title": "Living With Eternity In Mind",
        "author": "Archbishop Nicholas Duncan-Williams",
        "cover_url": "https://m.media-amazon.com/images/I/51SPQG22Y6L._SL500_.jpg",
        "description": "Reflecting on King Hezekiah's prayer, this 2024-2025 teaching challenges believers to live with eternal perspective, making decisions that impact both time and eternity.",
        "genre": ["Christian", "Spiritual Growth", "Purpose", "Faith"],
        "themes": ["Faith", "Purpose", "Eternity", "Wisdom"],
        "difficulty_level": "intermediate",
        "estimated_reading_time_minutes": 30
    },
    {
        "title": "Becoming a Strong Christian",
        "author": "Archbishop Nicholas Duncan-Williams",
        "cover_url": "https://m.media-amazon.com/images/I/51SPQG22Y6L._SL500_.jpg",
        "description": "Part of the Duncan-Williams Youth Series. Essential foundations for young believers to build strong faith, develop spiritual discipline, and stand firm in their Christian walk.",
        "genre": ["Christian", "Youth", "Spiritual Growth", "Discipleship"],
        "themes": ["Youth", "Faith", "Growth", "Discipleship"],
        "difficulty_level": "beginner",
        "estimated_reading_time_minutes": 25
    },
    {
        "title": "Setting Yourself Apart unto God",
        "author": "Archbishop Nicholas Duncan-Williams",
        "cover_url": "https://m.media-amazon.com/images/I/51SPQG22Y6L._SL500_.jpg",
        "description": "Youth Series Book 4. Learn the power of consecration and holiness, and discover how setting yourself apart for God's purposes unlocks divine favor and destiny.",
        "genre": ["Christian", "Youth", "Holiness", "Consecration"],
        "themes": ["Youth", "Holiness", "Purpose", "Consecration"],
        "difficulty_level": "beginner",
        "estimated_reading_time_minutes": 26
    },
    {
        "title": "Discovering and Walking in Purpose",
        "author": "Archbishop Nicholas Duncan-Williams",
        "cover_url": "https://m.media-amazon.com/images/I/51SPQG22Y6L._SL500_.jpg",
        "description": "Youth Series Book 5. A guide for young people to discover their God-given purpose, understand their calling, and walk confidently in their divine assignment.",
        "genre": ["Christian", "Youth", "Purpose", "Calling"],
        "themes": ["Youth", "Purpose", "Calling", "Destiny"],
        "difficulty_level": "beginner",
        "estimated_reading_time_minutes": 28
    },
    {
        "title": "Developing Intimacy with God",
        "author": "Archbishop Nicholas Duncan-Williams",
        "cover_url": "https://m.media-amazon.com/images/I/51SPQG22Y6L._SL500_.jpg",
        "description": "Youth Series teaching on cultivating a deep, personal relationship with God. Learn prayer, worship, and spiritual disciplines that bring you closer to the heart of God.",
        "genre": ["Christian", "Youth", "Prayer", "Worship"],
        "themes": ["Youth", "Prayer", "Worship", "Intimacy"],
        "difficulty_level": "beginner",
        "estimated_reading_time_minutes": 27
    },
    {
        "title": "Gratitude: Unlocking God's Blessings and Benefits",
        "author": "Archbishop Nicholas Duncan-Williams",
        "cover_url": "https://m.media-amazon.com/images/I/51SPQG22Y6L._SL500_.jpg",
        "description": "Discover the transformative power of gratitude and thanksgiving. Learn how a grateful heart unlocks divine favor, blessings, and benefits from God.",
        "genre": ["Christian", "Praise", "Faith", "Worship"],
        "themes": ["Praise", "Faith", "Gratitude", "Blessings"],
        "difficulty_level": "beginner",
        "estimated_reading_time_minutes": 24
    },
    {
        "title": "The Lamp: Daily Devotionals Q1 2016",
        "author": "Archbishop Nicholas Duncan-Williams",
        "cover_url": "https://m.media-amazon.com/images/I/51SPQG22Y6L._SL500_.jpg",
        "description": "A collection of daily devotional readings for the first quarter of 2016. Each day provides spiritual insight, encouragement, and practical wisdom for your faith journey.",
        "genre": ["Christian", "Devotional", "Spiritual Growth"],
        "themes": ["Faith", "Growth", "Devotional", "Wisdom"],
        "difficulty_level": "beginner",
        "estimated_reading_time_minutes": 90
    }
]


async def add_books():
    """Add new books to InkWave database."""

    print("🚀 Connecting to MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]

    try:
        # Test connection
        await client.admin.command("ping")
        print("✅ Connected to MongoDB\n")

        # Get current book count
        current_count = await db.books.count_documents({})
        print(f"📚 Current books in library: {current_count}\n")

        # Check for existing titles to avoid duplicates
        existing_titles = set()
        async for book in db.books.find({}, {"title": 1}):
            existing_titles.add(book["title"])

        print(f"🔍 Found {len(existing_titles)} existing titles\n")

        # Add new books
        added_count = 0
        skipped_count = 0

        for book_data in NEW_BOOKS:
            title = book_data["title"]

            # Skip if already exists
            if title in existing_titles:
                print(f"⏭️  Skipping (already exists): {title}")
                skipped_count += 1
                continue

            # Prepare book document
            book_doc = {
                "book_id": generate_book_id(),
                "title": title,
                "author": book_data["author"],
                "cover_url": book_data["cover_url"],
                "description": book_data["description"],
                "metadata": {
                    "genre": book_data["genre"],
                    "themes": book_data["themes"],
                    "summary": book_data["description"],
                    "estimated_reading_time_minutes": book_data["estimated_reading_time_minutes"],
                    "difficulty_level": book_data["difficulty_level"]
                },
                "processed": True,
                "processing_status": "ready",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            # Insert into database
            result = await db.books.insert_one(book_doc)
            print(f"✅ Added: {title} (ID: {book_doc['book_id']})")
            added_count += 1

        print(f"\n{'='*60}")
        print(f"📊 Summary:")
        print(f"  ✅ Books added: {added_count}")
        print(f"  ⏭️  Books skipped (duplicates): {skipped_count}")
        print(f"  📚 Total books now: {current_count + added_count}")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        client.close()
        print("🔌 Disconnected from MongoDB")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("📖 InkWave - Adding Archbishop Duncan-Williams Books")
    print("="*60 + "\n")

    asyncio.run(add_books())

    print("\n✨ Done! Books are now available on InkWave.\n")