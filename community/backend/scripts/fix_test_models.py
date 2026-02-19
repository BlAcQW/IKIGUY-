#!/usr/bin/env python3
"""
Fix test models to include all required fields for validation.
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://127.0.0.1:27017/african_language_community")

# Mapping of invalid architectures to valid enum values
ARCHITECTURE_MAPPING = {
    "tacotron2": "custom",  # tacotron2 not in enum, use custom
    "wav2vec2": "whisper",  # closest match for ASR
    "fastspeech2": "custom",  # not in enum
    "vits": "custom",  # not in enum
    "transformer": "transformer"  # valid
}


async def fix_models(db):
    """Add required fields to all models."""
    print("🔧 Fixing test models...")

    # Get all models
    models = await db.ml_models.find({}).to_list(length=None)
    print(f"   Found {len(models)} models to update")

    for model in models:
        # Prepare update dict
        update_dict = {}

        # Fix architecture to use valid enum value
        current_arch = model.get("architecture", "custom")
        if current_arch in ARCHITECTURE_MAPPING:
            update_dict["architecture"] = ARCHITECTURE_MAPPING[current_arch]

        # Add primary_language (use first language in list)
        if "primary_language" not in model:
            primary_lang = model.get("languages", ["en"])[0]
            update_dict["primary_language"] = primary_lang

        # Add is_multilingual
        if "is_multilingual" not in model:
            update_dict["is_multilingual"] = len(model.get("languages", [])) > 1

        # Add storage_path
        if "storage_path" not in model:
            update_dict["storage_path"] = f"/models/{model.get('model_type', 'unknown')}/{model.get('model_uuid', 'unknown')}"

        # Add checkpoint_path
        if "checkpoint_path" not in model:
            update_dict["checkpoint_path"] = f"{update_dict.get('storage_path', '/models')}/checkpoint.pt"

        # Add access_level
        if "access_level" not in model:
            update_dict["access_level"] = "public"

        # Fix deployment_status (map invalid values to valid enums)
        current_status = model.get("deployment_status")
        if current_status not in ["experimental", "staging", "production", "deprecated", "archived"]:
            # Map 'beta' and other invalid values to 'experimental'
            update_dict["deployment_status"] = "experimental"

        # Ensure contributors list exists
        if "contributors" not in model:
            update_dict["contributors"] = []

        # Apply updates if there are any
        if update_dict:
            result = await db.ml_models.update_one(
                {"_id": model["_id"]},
                {"$set": update_dict}
            )
            print(f"   ✓ Updated {model.get('name', 'unknown')}: {len(update_dict)} fields")

    print(f"✅ Fixed {len(models)} models")


async def main():
    """Fix all test models."""
    print("\n🚀 Fixing Test Models\n")

    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()

    try:
        # Verify connection
        await client.admin.command('ping')
        print("✅ Connected to MongoDB\n")

        # Fix models
        await fix_models(db)

        # Verify one model
        model = await db.ml_models.find_one({})
        if model:
            print(f"\n📋 Sample Model After Fix:")
            print(f"   Name: {model.get('name')}")
            print(f"   Architecture: {model.get('architecture')}")
            print(f"   Primary Language: {model.get('primary_language')}")
            print(f"   Is Multilingual: {model.get('is_multilingual')}")
            print(f"   Storage Path: {model.get('storage_path')}")
            print(f"   Checkpoint Path: {model.get('checkpoint_path')}")
            print(f"   Access Level: {model.get('access_level')}")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    finally:
        client.close()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
