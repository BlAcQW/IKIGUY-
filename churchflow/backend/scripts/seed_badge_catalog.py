"""
Seed badge catalog for ChurchFlow gamification system.

Populates the gamification_badges collection with predefined badge definitions
across attendance, engagement, and special categories.

Usage:
    python scripts/seed_badge_catalog.py [--organization-id <id>] [--global]
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings

settings = get_settings()


# ============================================================================
# BADGE CATALOG DEFINITION
# ============================================================================

BADGE_CATALOG: List[Dict[str, Any]] = [
    # ========================================================================
    # ATTENDANCE BADGES
    # ========================================================================
    {
        "badge_id": "early_bird",
        "name": "Early Bird",
        "description": "Attend 10 services",
        "category": "attendance",
        "icon_emoji": "🐦",
        "requirement_type": "count",
        "requirement_field": "total_services_attended",
        "requirement_value": 10,
        "points_reward": 50,
        "tier": "bronze",
        "is_active": True,
        "is_hidden": False,
        "order": 1
    },
    {
        "badge_id": "committed",
        "name": "Committed",
        "description": "Attend 25 services",
        "category": "attendance",
        "icon_emoji": "⭐",
        "requirement_type": "count",
        "requirement_field": "total_services_attended",
        "requirement_value": 25,
        "points_reward": 100,
        "tier": "silver",
        "is_active": True,
        "is_hidden": False,
        "order": 2
    },
    {
        "badge_id": "faithful",
        "name": "Faithful",
        "description": "Attend 52 services (1 year of Sundays)",
        "category": "attendance",
        "icon_emoji": "🏆",
        "requirement_type": "count",
        "requirement_field": "total_services_attended",
        "requirement_value": 52,
        "points_reward": 250,
        "tier": "gold",
        "is_active": True,
        "is_hidden": False,
        "order": 3
    },
    {
        "badge_id": "century_club",
        "name": "Century Club",
        "description": "Attend 100 services",
        "category": "attendance",
        "icon_emoji": "💯",
        "requirement_type": "count",
        "requirement_field": "total_services_attended",
        "requirement_value": 100,
        "points_reward": 500,
        "tier": "platinum",
        "is_active": True,
        "is_hidden": False,
        "order": 4
    },
    {
        "badge_id": "perfect_month",
        "name": "Perfect Month",
        "description": "Attended every service in a calendar month",
        "category": "attendance",
        "icon_emoji": "✨",
        "requirement_type": "special",
        "requirement_field": None,
        "requirement_value": None,
        "points_reward": 200,
        "tier": "gold",
        "is_active": True,
        "is_hidden": False,
        "order": 5
    },

    # ========================================================================
    # STREAK BADGES
    # ========================================================================
    {
        "badge_id": "four_week_streak",
        "name": "One Month Strong",
        "description": "Maintain a 4-week attendance streak",
        "category": "attendance",
        "icon_emoji": "🔥",
        "requirement_type": "streak",
        "requirement_field": "current_streak",
        "requirement_value": 4,
        "points_reward": 40,
        "tier": "bronze",
        "is_active": True,
        "is_hidden": False,
        "order": 6
    },
    {
        "badge_id": "quarter_streak",
        "name": "Quarter Commitment",
        "description": "Maintain a 13-week attendance streak",
        "category": "attendance",
        "icon_emoji": "🔥",
        "requirement_type": "streak",
        "requirement_field": "current_streak",
        "requirement_value": 13,
        "points_reward": 130,
        "tier": "silver",
        "is_active": True,
        "is_hidden": False,
        "order": 7
    },
    {
        "badge_id": "half_year_streak",
        "name": "Half Year Hero",
        "description": "Maintain a 26-week attendance streak",
        "category": "attendance",
        "icon_emoji": "🔥",
        "requirement_type": "streak",
        "requirement_field": "current_streak",
        "requirement_value": 26,
        "points_reward": 260,
        "tier": "gold",
        "is_active": True,
        "is_hidden": False,
        "order": 8
    },
    {
        "badge_id": "year_of_devotion",
        "name": "Year of Devotion",
        "description": "Maintain a 52-week attendance streak",
        "category": "attendance",
        "icon_emoji": "🔥",
        "requirement_type": "streak",
        "requirement_field": "current_streak",
        "requirement_value": 52,
        "points_reward": 520,
        "tier": "platinum",
        "is_active": True,
        "is_hidden": False,
        "order": 9
    },

    # ========================================================================
    # ENGAGEMENT BADGES
    # ========================================================================
    {
        "badge_id": "first_timer",
        "name": "First Timer",
        "description": "Recorded your first visit",
        "category": "engagement",
        "icon_emoji": "👋",
        "requirement_type": "milestone",
        "requirement_field": None,
        "requirement_value": None,
        "points_reward": 10,
        "tier": "bronze",
        "is_active": True,
        "is_hidden": False,
        "order": 10
    },
    {
        "badge_id": "volunteer_hero",
        "name": "Volunteer Hero",
        "description": "Volunteer for 10 hours",
        "category": "engagement",
        "icon_emoji": "🦸",
        "requirement_type": "count",
        "requirement_field": "total_volunteer_hours",
        "requirement_value": 10,
        "points_reward": 100,
        "tier": "silver",
        "is_active": True,
        "is_hidden": False,
        "order": 11
    },
    {
        "badge_id": "generous_giver",
        "name": "Generous Giver",
        "description": "Make 10 donations",
        "category": "engagement",
        "icon_emoji": "💝",
        "requirement_type": "count",
        "requirement_field": "total_donations_count",
        "requirement_value": 10,
        "points_reward": 75,
        "tier": "silver",
        "is_active": True,
        "is_hidden": False,
        "order": 12
    },
    {
        "badge_id": "friend_bringer",
        "name": "Friend Bringer",
        "description": "Invite 3 first-time visitors",
        "category": "engagement",
        "icon_emoji": "🤝",
        "requirement_type": "count",
        "requirement_field": "visitors_brought",
        "requirement_value": 3,
        "points_reward": 150,
        "tier": "gold",
        "is_active": True,
        "is_hidden": False,
        "order": 13
    },
    {
        "badge_id": "cell_group_member",
        "name": "Cell Group Member",
        "description": "Join a cell group",
        "category": "engagement",
        "icon_emoji": "👥",
        "requirement_type": "milestone",
        "requirement_field": None,
        "requirement_value": None,
        "points_reward": 50,
        "tier": "bronze",
        "is_active": True,
        "is_hidden": False,
        "order": 14
    },

    # ========================================================================
    # SPECIAL BADGES
    # ========================================================================
    {
        "badge_id": "event_enthusiast",
        "name": "Event Enthusiast",
        "description": "Attend 5 special conferences or events",
        "category": "special",
        "icon_emoji": "🎊",
        "requirement_type": "count",
        "requirement_field": "conferences_attended",
        "requirement_value": 5,
        "points_reward": 125,
        "tier": "silver",
        "is_active": True,
        "is_hidden": False,
        "order": 15
    },
    {
        "badge_id": "multi_branch",
        "name": "Branch Explorer",
        "description": "Visit 5 different branch locations",
        "category": "special",
        "icon_emoji": "🗺️",
        "requirement_type": "special",
        "requirement_field": None,
        "requirement_value": None,
        "points_reward": 100,
        "tier": "silver",
        "is_active": True,
        "is_hidden": False,
        "order": 16
    },
    {
        "badge_id": "early_adopter",
        "name": "Early Adopter",
        "description": "Using ChurchFlow in the first month of launch",
        "category": "special",
        "icon_emoji": "🚀",
        "requirement_type": "special",
        "requirement_field": None,
        "requirement_value": None,
        "points_reward": 150,
        "tier": "gold",
        "is_active": True,
        "is_hidden": True,  # Secret badge!
        "order": 17
    },
]


# ============================================================================
# SEEDING FUNCTIONS
# ============================================================================

async def seed_badges(
    db,
    organization_id: Optional[str] = None,
    is_global: bool = False
) -> Dict[str, Any]:
    """
    Seed badge catalog into database.

    Args:
        db: MongoDB database instance
        organization_id: Organization ID for organization-specific badges (None for global)
        is_global: If True, creates global badges (available to all organizations)

    Returns:
        Dictionary with seeding results
    """
    collection = db.gamification_badges

    inserted_count = 0
    updated_count = 0
    skipped_count = 0

    print("\n" + "="*70)
    print("  Badge Catalog Seeding")
    print("="*70)

    if is_global:
        print("📢 Seeding GLOBAL badges (available to all organizations)")
        org_id = None
    elif organization_id:
        print(f"🏢 Seeding badges for organization: {organization_id}")
        from bson import ObjectId
        org_id = ObjectId(organization_id)
    else:
        print("⚠️  No organization specified and not global. Seeding as global.")
        org_id = None

    print(f"\n🎖️  Processing {len(BADGE_CATALOG)} badge definitions...")
    print()

    for badge_def in BADGE_CATALOG:
        badge_id = badge_def["badge_id"]

        # Add organization_id to badge
        badge_doc = {
            **badge_def,
            "organization_id": org_id,
            "created_at": datetime.utcnow()
        }

        # Check if badge already exists
        existing_badge = await collection.find_one({
            "badge_id": badge_id,
            "organization_id": org_id
        })

        if existing_badge:
            # Update existing badge
            result = await collection.update_one(
                {"_id": existing_badge["_id"]},
                {"$set": badge_doc}
            )

            if result.modified_count > 0:
                print(f"  ✏️  Updated: {badge_def['name']} ({badge_def['icon_emoji']})")
                updated_count += 1
            else:
                print(f"  ⏭️  Skipped (unchanged): {badge_def['name']}")
                skipped_count += 1
        else:
            # Insert new badge
            await collection.insert_one(badge_doc)
            print(f"  ✅ Inserted: {badge_def['name']} ({badge_def['icon_emoji']}) - {badge_def['tier'].upper()}")
            inserted_count += 1

    # Create indexes
    print("\n📊 Creating database indexes...")
    await collection.create_index([("badge_id", 1), ("organization_id", 1)], unique=True)
    await collection.create_index([("category", 1)])
    await collection.create_index([("is_active", 1)])
    await collection.create_index([("order", 1)])
    print("  ✅ Indexes created")

    # Summary
    print("\n" + "="*70)
    print("📈 SEEDING SUMMARY")
    print("="*70)
    print(f"  Inserted: {inserted_count}")
    print(f"  Updated:  {updated_count}")
    print(f"  Skipped:  {skipped_count}")
    print(f"  Total:    {len(BADGE_CATALOG)}")
    print("="*70)

    # Category breakdown
    print("\n📊 Badge Categories:")
    category_counts = {}
    for badge in BADGE_CATALOG:
        category = badge["category"]
        category_counts[category] = category_counts.get(category, 0) + 1

    for category, count in sorted(category_counts.items()):
        print(f"  {category.capitalize()}: {count} badges")

    # Tier breakdown
    print("\n🏅 Badge Tiers:")
    tier_counts = {}
    for badge in BADGE_CATALOG:
        tier = badge["tier"]
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    for tier in ["bronze", "silver", "gold", "platinum"]:
        count = tier_counts.get(tier, 0)
        if count > 0:
            print(f"  {tier.capitalize()}: {count} badges")

    return {
        "inserted": inserted_count,
        "updated": updated_count,
        "skipped": skipped_count,
        "total": len(BADGE_CATALOG)
    }


async def list_existing_badges(db):
    """
    List all existing badges in database.

    Args:
        db: MongoDB database instance
    """
    collection = db.gamification_badges
    badges = await collection.find().sort("order", 1).to_list(length=None)

    if not badges:
        print("\n⚠️  No badges found in database.")
        return

    print("\n" + "="*70)
    print(f"  Existing Badges in Database ({len(badges)} total)")
    print("="*70)

    for badge in badges:
        org_scope = "GLOBAL" if badge.get("organization_id") is None else str(badge.get("organization_id"))
        print(f"  {badge['icon_emoji']} {badge['name']}")
        print(f"     ID: {badge['badge_id']}")
        print(f"     Tier: {badge['tier'].upper()} | Category: {badge['category']}")
        print(f"     Scope: {org_scope}")
        print(f"     Active: {'Yes' if badge['is_active'] else 'No'} | Hidden: {'Yes' if badge['is_hidden'] else 'No'}")
        print()


async def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="Seed ChurchFlow badge catalog")
    parser.add_argument("--organization-id", type=str, help="Organization ID for organization-specific badges")
    parser.add_argument("--global", dest="is_global", action="store_true", help="Create global badges (for all organizations)")
    parser.add_argument("--list", action="store_true", help="List existing badges without seeding")

    args = parser.parse_args()

    # Connect to database
    print("\n🔌 Connecting to MongoDB...")
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client.churchflow
    print("  ✅ Connected")

    try:
        if args.list:
            # List existing badges
            await list_existing_badges(db)
        else:
            # Seed badges
            results = await seed_badges(
                db,
                organization_id=args.organization_id,
                is_global=args.is_global
            )

            print("\n✅ Badge catalog seeding complete!")

            if results["inserted"] > 0 or results["updated"] > 0:
                print("\n💡 Next steps:")
                print("1. Verify badges in the gamification_badges collection")
                print("2. Test badge unlocking logic")
                print("3. Update frontend badge showcase component")

    finally:
        client.close()
        print("\n👋 Database connection closed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏸️  Seeding interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
