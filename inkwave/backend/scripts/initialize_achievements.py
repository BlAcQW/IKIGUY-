#!/usr/bin/env python3
"""
Initialize achievement definitions in the database.

Run this script after deploying achievement system to create/update all achievement definitions.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Database
from app.services.achievement_service import AchievementService


async def main():
    """Initialize achievements in database."""
    print("🚀 Initializing InkWave achievement system...")

    try:
        # Connect to database
        await Database.connect()
        print("✅ Connected to MongoDB")

        db = Database.get_database()
        achievement_service = AchievementService(db)

        # Initialize achievements
        count = await achievement_service.initialize_achievements()

        print(f"✅ Successfully initialized {count} new achievements")

        # Show all achievements
        all_achievements = await db.achievements.find({"is_active": True}).to_list(length=None)
        print(f"\n📊 Total active achievements: {len(all_achievements)}")

        print("\n🏆 Achievement categories:")
        categories = {}
        for ach in all_achievements:
            category = ach.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1

        for category, count in sorted(categories.items()):
            print(f"  - {category}: {count} achievements")

        print("\n🎯 Achievement tiers:")
        tiers = {}
        for ach in all_achievements:
            tier = ach.get("tier", "unknown")
            tiers[tier] = tiers.get(tier, 0) + 1

        for tier, count in sorted(tiers.items()):
            print(f"  - {tier}: {count} achievements")

        print("\n✅ Achievement system ready!")

    except Exception as e:
        print(f"❌ Error initializing achievements: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # Disconnect
        await Database.disconnect()
        print("✅ Disconnected from MongoDB")


if __name__ == "__main__":
    asyncio.run(main())
