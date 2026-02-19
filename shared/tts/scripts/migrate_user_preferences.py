#!/usr/bin/env python3
"""
User Preference Migration Script

Migrates invalid TTS provider IDs in user preferences to canonical snake_case format.
Scans MongoDB collections for legacy provider IDs and updates them to match the standardized format.

Legacy ID Examples:
- "XTTS" → "coqui_xtts"
- "StyleTTS2" → "style_tts2"
- "F5-TTS" → "f5_tts"
- "Melo-TTS" → "melo_tts"

Usage:
    # Dry run (default - no changes made)
    python apps/shared/tts/scripts/migrate_user_preferences.py

    # Execute migration
    python apps/shared/tts/scripts/migrate_user_preferences.py --execute

    # Custom MongoDB connection
    python apps/shared/tts/scripts/migrate_user_preferences.py \
        --mongo-url "mongodb://localhost:27017"  --database "kasaai_core"

Author: KasaAI Team
Date: 2025-11-23
"""

import sys
import os
import argparse
from typing import Dict, List, Set
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId

# Add apps to path
sys.path.insert(0, "/opt/kasaai/apps")

from shared.tts.models import TTSProvider


# Legacy provider ID mappings
LEGACY_PROVIDER_MAP = {
    # Legacy IDs → Canonical IDs
    "XTTS": "coqui_xtts",
    "xtts": "coqui_xtts",
    "Coqui-XTTS": "coqui_xtts",
    "coqui-xtts": "coqui_xtts",

    "StyleTTS2": "styletts2",
    "style-tts2": "styletts2",
    "StyleTTS-2": "styletts2",

    "F5-TTS": "f5tts",
    "f5-tts": "f5tts",
    "F5TTS": "f5tts",

    "Melo-TTS": "melotts",
    "melo-tts": "melotts",
    "MeloTTS": "melotts",

    "Open-Voice": "openvoice",
    "OpenVoice": "openvoice",
    "open-voice": "openvoice",

    "GPT-SoVITS": "gpt_sovits",
    "GPTSoVITS": "gpt_sovits",
    "gpt-sovits": "gpt_sovits",

    "Fish-Speech": "fish_speech",
    "FishSpeech": "fish_speech",
    "fish-speech": "fish_speech",

    "TTS-WebUI": "tts_webui",
    "TTSWebUI": "tts_webui",
    "tts-webui": "tts_webui",

    "Kokoro-TTS": "kokoro",
    "KokoroTTS": "kokoro",

    "VoxCPM": "voxcpm",
    "vox-cpm": "voxcpm",

    "Crawl4AI": "crawl4ai",
    "crawl-4ai": "crawl4ai",

    "IndexTTS": "indextts",
    "index-tts": "indextts",

    "Chatterbox": "chatterbox",
    "ChatterBox": "chatterbox",

    "Zonos": "zonos",
    "ZONOS": "zonos",

    "Moshi": "moshi",
    "MOSHI": "moshi",
}


def get_valid_provider_ids() -> Set[str]:
    """
    Get set of valid provider IDs from TTSProvider enum.

    Returns:
        Set of canonical provider IDs
    """
    return {provider.value for provider in TTSProvider}


def normalize_provider_id(legacy_id: str) -> str:
    """
    Normalize legacy provider ID to canonical format.

    Args:
        legacy_id: Legacy provider ID

    Returns:
        Canonical provider ID or None if invalid
    """
    # Check if already canonical
    valid_ids = get_valid_provider_ids()
    if legacy_id in valid_ids:
        return legacy_id

    # Check legacy mapping
    if legacy_id in LEGACY_PROVIDER_MAP:
        return LEGACY_PROVIDER_MAP[legacy_id]

    # Unknown provider ID
    return None


class UserPreferenceMigration:
    """Migrates user TTS preferences to canonical provider IDs."""

    def __init__(
        self,
        mongo_url: str,
        database_name: str,
        dry_run: bool = True,
        backup: bool = True
    ):
        """
        Initialize migration.

        Args:
            mongo_url: MongoDB connection URL
            database_name: Database name
            dry_run: If True, only report changes without applying them
            backup: If True, create backup before migration
        """
        self.mongo_url = mongo_url
        self.database_name = database_name
        self.dry_run = dry_run
        self.backup = backup

        # Connect to MongoDB
        self.client = MongoClient(mongo_url)
        self.db = self.client[database_name]

        # Collections to scan (customize based on your schema)
        self.collections_to_scan = [
            "user_preferences",
            "tts_settings",
            "voice_profiles",
            "voice_settings",
            "tts_configurations",
        ]

        # Migration stats
        self.stats = {
            "collections_scanned": 0,
            "documents_scanned": 0,
            "documents_with_invalid_providers": 0,
            "documents_updated": 0,
            "documents_failed": 0,
            "invalid_providers_found": {},
            "backup_created": False,
        }

    def run(self):
        """Execute migration."""
        print("=" * 70)
        print(f"TTS User Preference Migration")
        print("=" * 70)
        print(f"Database: {self.database_name}")
        print(f"Mode: {'DRY RUN (no changes)' if self.dry_run else 'EXECUTE'}")
        print(f"Backup: {'enabled' if self.backup else 'disabled'}")
        print("=" * 70)
        print()

        # Create backup if requested
        if self.backup and not self.dry_run:
            self._create_backup()

        # Scan collections
        for collection_name in self.collections_to_scan:
            self._scan_collection(collection_name)

        # Print summary
        self._print_summary()

    def _create_backup(self):
        """Create backup of collections before migration."""
        print("Creating backup...")

        for collection_name in self.collections_to_scan:
            if collection_name not in self.db.list_collection_names():
                continue

            backup_name = f"{collection_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            try:
                # Copy collection
                pipeline = [{"$match": {}}, {"$out": backup_name}]
                self.db[collection_name].aggregate(pipeline)

                print(f"  ✓ Backup created: {backup_name}")
                self.stats["backup_created"] = True

            except Exception as e:
                print(f"  ✗ Backup failed for {collection_name}: {str(e)}")

        print()

    def _scan_collection(self, collection_name: str):
        """
        Scan collection for invalid provider IDs.

        Args:
            collection_name: Name of collection to scan
        """
        # Check if collection exists
        if collection_name not in self.db.list_collection_names():
            return

        collection = self.db[collection_name]
        self.stats["collections_scanned"] += 1

        print(f"Scanning collection: {collection_name}")

        # Find documents with provider_id field
        cursor = collection.find({
            "$or": [
                {"provider_id": {"$exists": True}},
                {"tts_provider": {"$exists": True}},
                {"preferred_provider": {"$exists": True}},
            ]
        })

        doc_count = 0
        update_count = 0

        for doc in cursor:
            doc_count += 1
            self.stats["documents_scanned"] += 1

            # Check various provider ID fields
            provider_fields = ["provider_id", "tts_provider", "preferred_provider"]
            needs_update = False
            updates = {}

            for field in provider_fields:
                if field not in doc:
                    continue

                legacy_id = doc[field]

                if not legacy_id:
                    continue

                # Normalize provider ID
                canonical_id = normalize_provider_id(legacy_id)

                # Check if different from legacy ID
                if canonical_id != legacy_id:
                    needs_update = True

                    # Track invalid provider
                    if legacy_id not in self.stats["invalid_providers_found"]:
                        self.stats["invalid_providers_found"][legacy_id] = 0
                    self.stats["invalid_providers_found"][legacy_id] += 1

                    if canonical_id:
                        updates[field] = canonical_id
                        print(f"  → Document {doc['_id']}: {field} '{legacy_id}' → '{canonical_id}'")
                    else:
                        # Unknown provider - set to None
                        updates[field] = None
                        print(f"  → Document {doc['_id']}: {field} '{legacy_id}' → None (unknown)")

            # Update document if needed
            if needs_update:
                self.stats["documents_with_invalid_providers"] += 1

                if not self.dry_run:
                    try:
                        collection.update_one(
                            {"_id": doc["_id"]},
                            {"$set": updates}
                        )
                        self.stats["documents_updated"] += 1
                        update_count += 1

                    except Exception as e:
                        print(f"  ✗ Failed to update document {doc['_id']}: {str(e)}")
                        self.stats["documents_failed"] += 1

        print(f"  Scanned: {doc_count} documents")
        if not self.dry_run:
            print(f"  Updated: {update_count} documents")
        print()

    def _print_summary(self):
        """Print migration summary."""
        print("=" * 70)
        print("Migration Summary")
        print("=" * 70)
        print(f"Collections scanned: {self.stats['collections_scanned']}")
        print(f"Documents scanned: {self.stats['documents_scanned']}")
        print(f"Documents with invalid providers: {self.stats['documents_with_invalid_providers']}")

        if not self.dry_run:
            print(f"Documents updated: {self.stats['documents_updated']}")
            print(f"Documents failed: {self.stats['documents_failed']}")

        if self.stats["invalid_providers_found"]:
            print("\nInvalid provider IDs found:")
            for provider_id, count in sorted(
                self.stats["invalid_providers_found"].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                canonical = normalize_provider_id(provider_id)
                canonical_str = f"→ {canonical}" if canonical else "→ None (unknown)"
                print(f"  {provider_id}: {count} occurrences {canonical_str}")

        print("=" * 70)

        if self.dry_run:
            print("\n⚠️  DRY RUN MODE - No changes were made")
            print("Run with --execute flag to apply changes")
        else:
            print("\n✓ Migration completed successfully")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate user TTS preferences to canonical provider IDs"
    )
    parser.add_argument(
        "--mongo-url",
        default=os.getenv("MONGODB_URL", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/?authSource=admin"),
        help="MongoDB connection URL"
    )
    parser.add_argument(
        "--database",
        default="kasaai_core",
        help="Database name (default: kasaai_core)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute migration (default is dry run)"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip backup before migration"
    )

    args = parser.parse_args()

    try:
        migration = UserPreferenceMigration(
            mongo_url=args.mongo_url,
            database_name=args.database,
            dry_run=not args.execute,
            backup=not args.no_backup
        )

        migration.run()

        return 0

    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
