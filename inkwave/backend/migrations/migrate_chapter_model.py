"""
Migration script to update existing books with new chapter model fields.

Updates:
- BookChapter: adds id, order, duration, start_time
- BookChunk: adds chapter_id, chapter_title

Run with:
    MONGODB_URL="mongodb://admin:aawwER4444%@127.0.0.1:27017/inkwave?authSource=admin" \
    python migrations/migrate_chapter_model.py
"""

import asyncio
import os
import sys
from datetime import datetime

# Add app to path
sys.path.insert(0, '/opt/kasaai/apps/inkwave/backend')

from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection
MONGODB_URL = os.getenv(
    "MONGODB_URL",
    "mongodb://admin:aawwER4444%@127.0.0.1:27017/inkwave?authSource=admin"
)


async def migrate_chapters():
    """
    Migrate existing chapters to have id, order, duration, start_time fields.
    """
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.inkwave

    print("=" * 60)
    print("CHAPTER MODEL MIGRATION")
    print("=" * 60)

    # Get all books
    books = await db.books.find({}).to_list(length=None)
    print(f"\nFound {len(books)} books to process")

    updated_books = 0
    updated_chunks = 0

    for book in books:
        book_id = book.get("book_id")
        chapters = book.get("chapters", [])

        if not chapters:
            print(f"\n⏭️  Skipping {book_id}: no chapters")
            continue

        print(f"\n📚 Processing {book_id}: {book.get('title', 'Unknown')}")
        print(f"   Chapters: {len(chapters)}")

        # Check if already migrated
        first_chapter = chapters[0] if chapters else {}
        if "id" in first_chapter and "order" in first_chapter:
            print(f"   ✅ Already migrated")
            # Still update chunks if needed
            chunks_need_update = await db.book_chunks.count_documents({
                "book_id": book_id,
                "chapter_id": {"$exists": False}
            })
            if chunks_need_update == 0:
                continue

        # Update chapters with id, order, duration, start_time
        updated_chapters = []
        for idx, chapter in enumerate(chapters):
            # Add new fields if missing
            if "id" not in chapter:
                chapter["id"] = f"ch_{idx + 1}"
            if "order" not in chapter:
                chapter["order"] = idx + 1
            if "duration" not in chapter:
                chapter["duration"] = None
            if "start_time" not in chapter:
                chapter["start_time"] = None
            updated_chapters.append(chapter)

        # Update book with new chapters
        await db.books.update_one(
            {"book_id": book_id},
            {
                "$set": {
                    "chapters": updated_chapters,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        updated_books += 1
        print(f"   ✅ Updated chapters")

        # Update chunks with chapter_id and chapter_title
        for chapter in updated_chapters:
            start_idx = chapter.get("start_chunk_id", 0)
            end_idx = chapter.get("end_chunk_id", 0)

            result = await db.book_chunks.update_many(
                {
                    "book_id": book_id,
                    "chunk_index": {"$gte": start_idx, "$lte": end_idx}
                },
                {
                    "$set": {
                        "chapter_id": chapter["id"],
                        "chapter_title": chapter.get("title", "")
                    }
                }
            )
            updated_chunks += result.modified_count

        print(f"   ✅ Updated {updated_chunks} chunks")

    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)
    print(f"Books updated: {updated_books}")
    print(f"Chunks updated: {updated_chunks}")

    client.close()


async def calculate_chapter_durations():
    """
    Calculate chapter durations from chunk audio durations.

    This should be run after audio has been generated for chunks.
    """
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.inkwave

    print("\n" + "=" * 60)
    print("CALCULATING CHAPTER DURATIONS FROM AUDIO")
    print("=" * 60)

    books = await db.books.find({"processed": True}).to_list(length=None)
    print(f"\nFound {len(books)} processed books")

    updated_books = 0

    for book in books:
        book_id = book.get("book_id")
        chapters = book.get("chapters", [])

        if not chapters:
            continue

        print(f"\n📚 Processing {book_id}: {book.get('title', 'Unknown')}")

        # Calculate duration for each chapter
        updated_chapters = []
        cumulative_time = 0

        for chapter in chapters:
            chapter_id = chapter.get("id", "")
            start_idx = chapter.get("start_chunk_id", 0)
            end_idx = chapter.get("end_chunk_id", 0)

            # Get total audio duration for chunks in this chapter
            pipeline = [
                {
                    "$match": {
                        "book_id": book_id,
                        "chunk_index": {"$gte": start_idx, "$lte": end_idx},
                        "audio_duration": {"$exists": True, "$ne": None}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_duration": {"$sum": "$audio_duration"}
                    }
                }
            ]

            result = await db.book_chunks.aggregate(pipeline).to_list(length=1)
            chapter_duration = int(result[0]["total_duration"]) if result else None

            # Update chapter with calculated values
            chapter["start_time"] = cumulative_time if chapter_duration else None
            chapter["duration"] = chapter_duration

            if chapter_duration:
                cumulative_time += chapter_duration

            updated_chapters.append(chapter)

        # Check if any chapter has duration
        has_audio = any(c.get("duration") is not None for c in updated_chapters)

        if has_audio:
            await db.books.update_one(
                {"book_id": book_id},
                {
                    "$set": {
                        "chapters": updated_chapters,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            updated_books += 1
            print(f"   ✅ Updated chapter durations")

            # Print chapter info
            for ch in updated_chapters:
                duration_str = f"{ch.get('duration', 0)}s" if ch.get('duration') else "no audio"
                start_str = f"{ch.get('start_time', 0)}s" if ch.get('start_time') is not None else "-"
                print(f"      {ch.get('id')}: {ch.get('title', '')[:30]} - {duration_str} @ {start_str}")
        else:
            print(f"   ⏭️  No audio generated yet")

    print("\n" + "=" * 60)
    print("DURATION CALCULATION COMPLETE")
    print("=" * 60)
    print(f"Books with calculated durations: {updated_books}")

    client.close()


async def main():
    """Run all migrations."""
    print("\n🚀 Starting chapter model migration...\n")

    # Step 1: Migrate chapter structure
    await migrate_chapters()

    # Step 2: Calculate durations (if audio exists)
    await calculate_chapter_durations()

    print("\n✅ Migration completed successfully!\n")


if __name__ == "__main__":
    asyncio.run(main())
