"""
Seed devotionals from Fresh Manna content into MongoDB.
Parses the Fresh Manna text file and creates devotional entries.
"""

import asyncio
import re
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/devotionalflow?authSource=admin")

# Admin user ID (from create_default_users script)
ADMIN_USER_ID = "693acf37d221b83bb8f2d2a7"

# Categories mapping based on content keywords
CATEGORY_KEYWORDS = {
    "faith": ["faith", "believe", "trust", "confidence"],
    "prayer": ["prayer", "pray", "praying"],
    "hope": ["hope", "hopeful"],
    "love": ["love", "loving", "beloved"],
    "purpose": ["purpose", "calling", "mission"],
    "healing": ["healing", "heal", "restore"],
    "wisdom": ["wisdom", "wise", "understanding"],
    "courage": ["courage", "courageous", "brave", "strength"],
    "gratitude": ["gratitude", "grateful", "thankful", "thanks"],
    "forgiveness": ["forgiveness", "forgive", "mercy"],
}


def parse_devotionals_from_file(file_path: str) -> list:
    """
    Parse devotionals from Fresh Manna text file.

    Args:
        file_path: Path to the Fresh Manna content text file

    Returns:
        List of devotional dictionaries
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by devotional numbers (1\n, 2\n, 3\n, etc.)
    devotionals_raw = re.split(r'\n(\d+)\s*\n', content)

    devotionals = []

    # Start from index 1 (skip the content before first number)
    for i in range(1, len(devotionals_raw), 2):
        if i + 1 >= len(devotionals_raw):
            break

        number = devotionals_raw[i].strip()
        devotional_text = devotionals_raw[i + 1].strip()

        if not devotional_text:
            continue

        # Parse devotional components
        devotional = parse_single_devotional(number, devotional_text)
        if devotional:
            devotionals.append(devotional)

    return devotionals


def parse_single_devotional(number: str, text: str) -> dict:
    """
    Parse a single devotional from text.

    Args:
        number: Devotional number
        text: Devotional text content

    Returns:
        Devotional dictionary
    """
    lines = text.split('\n')

    # Extract title
    title = ""
    content_start = 0

    for i, line in enumerate(lines):
        line_clean = line.strip()
        if line_clean.startswith("Title:"):
            title = line_clean.replace("Title:", "").strip()
            content_start = i + 1
            break
        elif i == 0 and line_clean:
            # First line might be the title
            title = line_clean
            content_start = 1
            break

    if not title:
        title = f"Daily Devotional #{number}"

    # Clean title
    title = re.sub(r'^["\']|["\']$', '', title)

    # Extract scripture references
    scripture_refs = []
    scripture_pattern = r'([A-Z][a-z]+(?: [A-Z][a-z]+)*) (\d+):(\d+(?:-\d+)?)'

    # Look for scripture in first few lines
    for line in lines[:5]:
        matches = re.findall(scripture_pattern, line)
        for match in matches:
            ref = f"{match[0]} {match[1]}:{match[2]}"
            if ref not in scripture_refs:
                scripture_refs.append(ref)

    # Extract content paragraphs
    content_blocks = []
    current_paragraph = []
    in_prayer = False

    for line in lines[content_start:]:
        line_clean = line.strip()

        if not line_clean:
            if current_paragraph:
                para_text = ' '.join(current_paragraph)
                if in_prayer:
                    content_blocks.append({
                        "type": "prayer",
                        "text": para_text
                    })
                    in_prayer = False
                else:
                    content_blocks.append({
                        "type": "paragraph",
                        "text": para_text
                    })
                current_paragraph = []
            continue

        if line_clean.lower().startswith("prayer"):
            in_prayer = True
            continue

        current_paragraph.append(line_clean)

    # Add last paragraph if exists
    if current_paragraph:
        para_text = ' '.join(current_paragraph)
        if in_prayer:
            content_blocks.append({
                "type": "prayer",
                "text": para_text
            })
        else:
            content_blocks.append({
                "type": "paragraph",
                "text": para_text
            })

    # Detect categories based on keywords
    categories = detect_categories(title + " " + text)

    if not categories:
        categories = ["faith"]

    return {
        "title": title,
        "content": content_blocks,
        "scripture_references": scripture_refs,
        "categories": categories,
        "number": int(number) if number.isdigit() else 0
    }


def detect_categories(text: str) -> list:
    """
    Detect categories based on keyword matching.

    Args:
        text: Text to analyze

    Returns:
        List of category strings
    """
    text_lower = text.lower()
    detected = []

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                detected.append(category)
                break

    return detected[:3]  # Max 3 categories


async def seed_devotionals():
    """Seed devotionals into MongoDB."""

    print("=" * 60)
    print("FRESH MANNA DEVOTIONALS SEEDING")
    print("=" * 60)

    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client.get_database()

    print(f"\n✓ Connected to MongoDB")

    # Parse devotionals from file
    file_path = "/tmp/fresh_manna_content.txt"
    print(f"\n📖 Parsing devotionals from {file_path}...")

    devotionals = parse_devotionals_from_file(file_path)
    print(f"✓ Parsed {len(devotionals)} devotionals")

    # Check existing count
    existing_count = await db.devotionals.count_documents({})
    print(f"\n📊 Existing devotionals in database: {existing_count}")

    if existing_count > 0:
        response = input(f"\n⚠️  Database already has {existing_count} devotionals. Delete and reseed? (yes/no): ")
        if response.lower() == 'yes':
            result = await db.devotionals.delete_many({})
            print(f"✓ Deleted {result.deleted_count} existing devotionals")
        else:
            print("❌ Seeding cancelled")
            return

    # Insert devotionals
    print(f"\n💾 Inserting {len(devotionals)} devotionals...")

    base_date = datetime.now() - timedelta(days=len(devotionals))
    inserted_count = 0

    for i, dev_data in enumerate(devotionals):
        try:
            # Create devotional document
            devotional = {
                "_id": str(ObjectId()),
                "title": dev_data["title"],
                "content": dev_data["content"],
                "scripture_references": dev_data["scripture_references"],
                "categories": dev_data["categories"],
                "author_id": ADMIN_USER_ID,
                "status": "published",
                "cover_image_url": None,
                "audio_url": None,
                "views_count": 0,
                "likes_count": 0,
                "comments_count": 0,
                "shares_count": 0,
                "bookmarks_count": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "published_at": base_date + timedelta(days=i),
                "scheduled_at": None,
            }

            await db.devotionals.insert_one(devotional)
            inserted_count += 1

            if inserted_count % 10 == 0:
                print(f"  → Inserted {inserted_count}/{len(devotionals)} devotionals...")

        except Exception as e:
            print(f"  ✗ Error inserting devotional #{dev_data.get('number', '?')}: {e}")
            continue

    print(f"\n✅ Successfully inserted {inserted_count}/{len(devotionals)} devotionals")

    # Create indexes
    print(f"\n🔍 Creating indexes...")
    await db.devotionals.create_index("author_id")
    await db.devotionals.create_index("status")
    await db.devotionals.create_index("published_at")
    await db.devotionals.create_index("categories")
    await db.devotionals.create_index([("title", "text"), ("content", "text")])
    print(f"✓ Indexes created")

    # Show statistics
    print(f"\n" + "=" * 60)
    print("SEEDING COMPLETE")
    print("=" * 60)
    print(f"Total devotionals: {inserted_count}")
    print(f"Categories used: {set([cat for dev in devotionals for cat in dev['categories']])}")
    print(f"Date range: {base_date.date()} to {datetime.now().date()}")
    print("=" * 60)

    client.close()


if __name__ == "__main__":
    asyncio.run(seed_devotionals())
