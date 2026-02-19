"""
Migration 001: Add MLOps Collections

Creates new collections for MLOps platform:
- ml_models: ML model registry with versioning
- ml_training_pipelines: Training pipeline tracking
- dataset_versions: Dataset version control
- file_uploads: User upload tracking
- resource_links: External resource management
- model_language_associations: Multi-language model linking
- storage_manifests: File system indexing

Run: python 001_add_mlops_collections.py
"""

import os
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


async def create_indexes(db):
    """Create indexes for new collections."""

    print("Creating indexes for ml_models...")
    await db.ml_models.create_index("model_uuid", unique=True)
    await db.ml_models.create_index("model_type")
    await db.ml_models.create_index("architecture")
    await db.ml_models.create_index("deployment_status")
    await db.ml_models.create_index("version")
    await db.ml_models.create_index([("languages", 1)])
    await db.ml_models.create_index([("language_ids", 1)])
    await db.ml_models.create_index([("tags", 1)])
    await db.ml_models.create_index([("created_at", -1)])
    await db.ml_models.create_index([("updated_at", -1)])
    # Compound indexes for common queries
    await db.ml_models.create_index([("model_type", 1), ("deployment_status", 1)])
    await db.ml_models.create_index([("is_public", 1), ("deployment_status", 1)])

    print("Creating indexes for ml_training_pipelines...")
    await db.ml_training_pipelines.create_index("pipeline_uuid", unique=True)
    await db.ml_training_pipelines.create_index("current_stage")
    await db.ml_training_pipelines.create_index("is_active")
    await db.ml_training_pipelines.create_index("priority")
    await db.ml_training_pipelines.create_index("created_by")
    await db.ml_training_pipelines.create_index([("model_type", 1)])
    await db.ml_training_pipelines.create_index([("created_at", -1)])
    await db.ml_training_pipelines.create_index([("updated_at", -1)])
    # Compound indexes
    await db.ml_training_pipelines.create_index([("is_active", 1), ("current_stage", 1)])
    await db.ml_training_pipelines.create_index([("model_type", 1), ("is_active", 1)])

    print("Creating indexes for dataset_versions...")
    await db.dataset_versions.create_index([("dataset_id", 1), ("version", 1)], unique=True)
    await db.dataset_versions.create_index("dataset_id")
    await db.dataset_versions.create_index("version")
    await db.dataset_versions.create_index("is_stable")
    await db.dataset_versions.create_index("is_deprecated")
    await db.dataset_versions.create_index([("released_at", -1)])
    await db.dataset_versions.create_index([("created_at", -1)])
    # Compound indexes
    await db.dataset_versions.create_index([("dataset_id", 1), ("is_stable", 1)])
    await db.dataset_versions.create_index([("dataset_id", 1), ("is_deprecated", 1)])

    print("Creating indexes for file_uploads...")
    await db.file_uploads.create_index("upload_uuid", unique=True)
    await db.file_uploads.create_index("uploaded_by")
    await db.file_uploads.create_index("upload_type")
    await db.file_uploads.create_index("processing_status")
    await db.file_uploads.create_index("language_code")
    await db.file_uploads.create_index("is_quarantined")
    await db.file_uploads.create_index([("created_at", -1)])
    await db.file_uploads.create_index([("expires_at", 1)])  # For TTL cleanup
    # Compound indexes
    await db.file_uploads.create_index([("uploaded_by", 1), ("processing_status", 1)])
    await db.file_uploads.create_index([("upload_type", 1), ("processing_status", 1)])

    print("Creating indexes for resource_links...")
    await db.resource_links.create_index("link_uuid", unique=True)
    await db.resource_links.create_index("url")
    await db.resource_links.create_index("resource_type")
    await db.resource_links.create_index("platform")
    await db.resource_links.create_index("verification_status")
    await db.resource_links.create_index("submitted_by")
    await db.resource_links.create_index([("languages", 1)])
    await db.resource_links.create_index([("language_ids", 1)])
    await db.resource_links.create_index([("tags", 1)])
    await db.resource_links.create_index([("created_at", -1)])
    await db.resource_links.create_index([("quality_rating", -1)])
    # Compound indexes
    await db.resource_links.create_index([("resource_type", 1), ("verification_status", 1)])
    await db.resource_links.create_index([("platform", 1), ("resource_type", 1)])

    print("Creating indexes for model_language_associations...")
    await db.model_language_associations.create_index([("model_id", 1), ("language_id", 1)], unique=True)
    await db.model_language_associations.create_index("model_uuid")
    await db.model_language_associations.create_index("language_id")
    await db.model_language_associations.create_index("language_code")
    await db.model_language_associations.create_index("language_family_id")
    await db.model_language_associations.create_index("association_type")
    await db.model_language_associations.create_index("is_primary_language")
    await db.model_language_associations.create_index("support_quality")
    # Compound indexes
    await db.model_language_associations.create_index([("model_id", 1), ("is_primary_language", 1)])
    await db.model_language_associations.create_index([("language_family_id", 1), ("support_quality", 1)])

    print("Creating indexes for storage_manifests...")
    await db.storage_manifests.create_index("manifest_uuid", unique=True)
    await db.storage_manifests.create_index([("entity_type", 1), ("entity_id", 1), ("version", 1)], unique=True)
    await db.storage_manifests.create_index("entity_type")
    await db.storage_manifests.create_index("entity_id")
    await db.storage_manifests.create_index("storage_backend")
    await db.storage_manifests.create_index([("created_at", -1)])
    await db.storage_manifests.create_index([("last_verified_at", 1)])  # For verification scheduling
    # Compound indexes
    await db.storage_manifests.create_index([("entity_type", 1), ("entity_id", 1)])

    print("✅ All indexes created successfully")


async def migrate_existing_collections(db):
    """Add new fields to existing collections."""

    print("\nMigrating existing collections...")

    # Migrate external_datasets collection
    print("Updating external_datasets collection...")
    result = await db.external_datasets.update_many(
        {},
        {
            "$set": {
                "dataset_uuid": {"$toString": "$_id"},  # Generate UUID from ObjectId
                "version": "1.0.0",
                "is_latest_version": True,
                "version_history": [],
                "storage_path": None,
                "manifest_id": None,
                "checksum": None,
                "download_url": None,
                "is_public": True,
                "used_in_pipelines": [],
                "used_in_models": [],
                "training_ready": False,
                "has_train_split": False,
                "has_validation_split": False,
                "has_test_split": False,
                "split_ratios": None,
                "published_at": None,
                "download_count": 0,
                "view_count": 0,
                "citation_count": 0,
                "language_id": None
            }
        }
    )
    print(f"  Updated {result.modified_count} documents in external_datasets")

    # Migrate languages collection
    print("Updating languages collection...")
    result = await db.languages.update_many(
        {},
        {
            "$set": {
                "available_datasets": [],
                "available_models": [],
                "active_pipelines": [],
                "total_audio_hours": 0.0,
                "total_text_samples": 0,
                "best_asr_wer": None,
                "best_tts_mos": None,
                "best_model_references": {}
            }
        }
    )
    print(f"  Updated {result.modified_count} documents in languages")

    print("✅ Existing collections migrated successfully")


async def create_validation_rules(db):
    """Create validation rules for new collections."""

    print("\nCreating validation rules...")

    # ML Models validation
    await db.command({
        "collMod": "ml_models",
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["model_uuid", "name", "model_type", "architecture", "version"],
                "properties": {
                    "model_uuid": {"bsonType": "string"},
                    "name": {"bsonType": "string", "minLength": 3, "maxLength": 200},
                    "model_type": {"enum": ["tts", "asr", "llm", "nmt", "ner", "pos", "sentiment", "custom"]},
                    "version": {"bsonType": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"}
                }
            }
        },
        "validationLevel": "moderate"
    })
    print("  ✓ ml_models validation rules")

    # Dataset Versions validation
    await db.command({
        "collMod": "dataset_versions",
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["dataset_id", "version", "changelog"],
                "properties": {
                    "version": {"bsonType": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
                    "changelog": {"bsonType": "string", "minLength": 10, "maxLength": 2000}
                }
            }
        },
        "validationLevel": "moderate"
    })
    print("  ✓ dataset_versions validation rules")

    print("✅ Validation rules created successfully")


async def run_migration():
    """Execute the migration."""

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

        # Create indexes
        await create_indexes(db)

        # Migrate existing collections
        await migrate_existing_collections(db)

        # Create validation rules
        await create_validation_rules(db)

        # Record migration
        await db.migrations.insert_one({
            "migration_id": "001_add_mlops_collections",
            "description": "Add MLOps collections and enhance existing models",
            "executed_at": datetime.utcnow(),
            "status": "completed"
        })

        print("\n" + "="*60)
        print("✅ Migration 001 completed successfully!")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(run_migration())
