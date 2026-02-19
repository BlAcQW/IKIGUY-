#!/usr/bin/env python3
"""
Migration script to optimize voice parameters for all existing assistants.

This script updates voice parameters (stability, clarity, speed, etc.) for all
assistants in the database to use optimized values based on their TTS provider
and language configuration.

Usage:
    python optimize_voice_parameters.py [--dry-run] [--use-case CASE]
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient
from urllib.parse import quote_plus
from services.voice_parameter_optimizer import voice_parameter_optimizer


def connect_to_mongodb():
    """Connect to MongoDB and return collection."""
    # Get credentials from environment
    username = quote_plus(os.getenv("MONGO_USERNAME", "admin"))
    password = quote_plus(os.getenv("MONGO_PASSWORD", "aawwER4444%"))
    host = os.getenv("MONGO_HOST", "127.0.0.1")
    port = os.getenv("MONGO_PORT", "27017")
    database = os.getenv("MONGO_CORE_DATABASE", "kasaai_core")

    mongodb_url = f"mongodb://{username}:{password}@{host}:{port}/"

    client = MongoClient(mongodb_url)
    db = client[database]
    collection = db["assistants"]

    return collection


def determine_use_case(assistant_dict):
    """
    Determine the use case from assistant name or system prompt.

    Returns:
        Use case string (customer_service, sales, conversational, etc.)
    """
    name_lower = assistant_dict.get("name", "").lower()
    prompt_lower = assistant_dict.get("system_prompt", "").lower()

    # Check for customer service keywords
    if any(word in name_lower or word in prompt_lower for word in [
        "customer", "support", "service", "help", "assist"
    ]):
        return "customer_service"

    # Check for sales keywords
    if any(word in name_lower or word in prompt_lower for word in [
        "sales", "sell", "product", "offer", "deal"
    ]):
        return "sales"

    # Default to conversational
    return "conversational"


def optimize_assistant_parameters(
    assistant_dict,
    use_case_override=None,
    dry_run=False
):
    """
    Optimize voice parameters for a single assistant.

    Args:
        assistant_dict: Assistant document from MongoDB
        use_case_override: Optional use case override
        dry_run: If True, don't update database

    Returns:
        Tuple of (updated_dict, changes_made)
    """
    assistant_id = assistant_dict.get("id", "Unknown")
    name = assistant_dict.get("name", "Unnamed")
    tts_provider = assistant_dict.get("tts_provider", "openai")
    language = assistant_dict.get("language", "en")

    # Determine use case
    use_case = use_case_override or determine_use_case(assistant_dict)

    # Get current parameters
    current_params = {
        "stability": assistant_dict.get("stability"),
        "clarity_similarity": assistant_dict.get("clarity_similarity"),
        "speed": assistant_dict.get("speed"),
        "style_exaggeration": assistant_dict.get("style_exaggeration"),
        "optimize_streaming_latency": assistant_dict.get("optimize_streaming_latency"),
    }

    # Get optimized parameters
    optimized_params = voice_parameter_optimizer.get_optimized_parameters(
        tts_provider=tts_provider,
        use_case=use_case,
        language=language
    )

    # Check what changed
    changes = {}
    for key, new_value in optimized_params.items():
        old_value = current_params.get(key)
        if old_value != new_value:
            changes[key] = {"old": old_value, "new": new_value}

    # Update assistant dict
    updated_dict = assistant_dict.copy()
    updated_dict.update(optimized_params)

    # Log changes
    if changes:
        print(f"\n📝 {name} ({assistant_id[:20]}...)")
        print(f"   Provider: {tts_provider} | Language: {language} | Use Case: {use_case}")
        for param, change in changes.items():
            print(f"   • {param}: {change['old']} → {change['new']}")
    else:
        print(f"✅ {name} - No changes needed")

    return updated_dict, bool(changes)


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(
        description="Optimize voice parameters for all assistants"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without updating database"
    )
    parser.add_argument(
        "--use-case",
        choices=["customer_service", "sales", "conversational"],
        help="Override use case detection for all assistants"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("🎙️  VOICE PARAMETER OPTIMIZATION MIGRATION")
    print("=" * 80)

    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made to database\n")
    else:
        print("⚠️  LIVE MODE - Database will be updated\n")

    # Connect to MongoDB
    try:
        collection = connect_to_mongodb()
        print(f"✅ Connected to MongoDB\n")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        sys.exit(1)

    # Get all assistants
    assistants = list(collection.find({}))
    total_count = len(assistants)
    print(f"📊 Found {total_count} assistants to process\n")

    # Process each assistant
    updated_count = 0
    no_change_count = 0

    for assistant_dict in assistants:
        try:
            updated_dict, has_changes = optimize_assistant_parameters(
                assistant_dict,
                use_case_override=args.use_case,
                dry_run=args.dry_run
            )

            if has_changes:
                updated_count += 1

                if not args.dry_run:
                    # Update in database
                    collection.update_one(
                        {"_id": assistant_dict["_id"]},
                        {"$set": {
                            "stability": updated_dict["stability"],
                            "clarity_similarity": updated_dict["clarity_similarity"],
                            "speed": updated_dict["speed"],
                            "style_exaggeration": updated_dict["style_exaggeration"],
                            "optimize_streaming_latency": updated_dict["optimize_streaming_latency"],
                        }}
                    )
            else:
                no_change_count += 1

        except Exception as e:
            print(f"❌ Error processing assistant {assistant_dict.get('name', 'Unknown')}: {e}")
            continue

    # Summary
    print("\n" + "=" * 80)
    print("📈 SUMMARY")
    print("=" * 80)
    print(f"Total assistants: {total_count}")
    print(f"Updated: {updated_count}")
    print(f"No changes: {no_change_count}")

    if args.dry_run:
        print("\n💡 Run without --dry-run to apply these changes")
    else:
        print("\n✅ Migration completed successfully!")


if __name__ == "__main__":
    main()
