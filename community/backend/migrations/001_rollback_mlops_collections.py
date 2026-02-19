"""
Rollback Migration 001: Remove MLOps Collections

Rolls back the changes made by 001_add_mlops_collections.py:
- Drops new collections
- Removes new fields from existing collections

Run: python 001_rollback_mlops_collections.py
"""

import os
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()


async def drop_collections(db):
    """Drop new collections created by migration 001."""

    print("Dropping new collections...")

    collections_to_drop = [
        "ml_models",
        "ml_training_pipelines",
        "dataset_versions",
        "file_uploads",
        "resource_links",
        "model_language_associations",
        "storage_manifests"
    ]

    for collection_name in collections_to_drop:
        try:
            await db.drop_collection(collection_name)
            print(f"  ✓ Dropped {collection_name}")
        except Exception as e:
            print(f"  ⚠ Could not drop {collection_name}: {e}")

    print("✅ Collections dropped")


async def rollback_existing_collections(db):
    """Remove new fields from existing collections."""

    print("\nRolling back existing collections...")

    # Rollback external_datasets collection
    print("Rolling back external_datasets collection...")
    result = await db.external_datasets.update_many(
        {},
        {
            "$unset": {
                "dataset_uuid": "",
                "version": "",
                "is_latest_version": "",
                "version_history": "",
                "storage_path": "",
                "manifest_id": "",
                "checksum": "",
                "download_url": "",
                "is_public": "",
                "used_in_pipelines": "",
                "used_in_models": "",
                "training_ready": "",
                "has_train_split": "",
                "has_validation_split": "",
                "has_test_split": "",
                "split_ratios": "",
                "published_at": "",
                "download_count": "",
                "view_count": "",
                "citation_count": "",
                "language_id": ""
            }
        }
    )
    print(f"  Updated {result.modified_count} documents in external_datasets")

    # Rollback languages collection
    print("Rolling back languages collection...")
    result = await db.languages.update_many(
        {},
        {
            "$unset": {
                "available_datasets": "",
                "available_models": "",
                "active_pipelines": "",
                "total_audio_hours": "",
                "total_text_samples": "",
                "best_asr_wer": "",
                "best_tts_mos": "",
                "best_model_references": ""
            }
        }
    )
    print(f"  Updated {result.modified_count} documents in languages")

    print("✅ Existing collections rolled back successfully")


async def run_rollback():
    """Execute the rollback."""

    # Get MongoDB connection from environment
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://admin:aawwER444444@127.0.0.1:27017/")
    db_name = os.getenv("MONGODB_DATABASE", "african_language_community")

    print(f"Connecting to MongoDB: {db_name}")
    client = AsyncIOMotorClient(mongodb_url)
    db = client[db_name]

    try:
        # Test connection
        await db.command("ping")
        print("✅ Connected to MongoDB\n")

        # Confirm rollback
        print("⚠️  WARNING: This will remove all MLOps collections and data!")
        print("Collections to be dropped:")
        print("  - ml_models")
        print("  - ml_training_pipelines")
        print("  - dataset_versions")
        print("  - file_uploads")
        print("  - resource_links")
        print("  - model_language_associations")
        print("  - storage_manifests")
        print()

        confirmation = input("Type 'ROLLBACK' to confirm: ")
        if confirmation != "ROLLBACK":
            print("❌ Rollback cancelled")
            return

        # Drop collections
        await drop_collections(db)

        # Rollback existing collections
        await rollback_existing_collections(db)

        # Record rollback
        await db.migrations.update_one(
            {"migration_id": "001_add_mlops_collections"},
            {
                "$set": {
                    "rolled_back_at": datetime.utcnow(),
                    "status": "rolled_back"
                }
            }
        )

        print("\n" + "="*60)
        print("✅ Rollback completed successfully!")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Rollback failed: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(run_rollback())
