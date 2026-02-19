"""
Voice Lab Dataset Migration Script

Migrates voice-lab datasets from Hetzner storage into the community platform.
Implements comprehensive plan with risk mitigations.

Usage:
    # Dry run (preview without changes)
    python scripts/migrate_voice_lab_datasets.py --dry-run

    # Execute migration
    python scripts/migrate_voice_lab_datasets.py --execute

    # Migrate specific dataset
    python scripts/migrate_voice_lab_datasets.py --execute --dataset twi-akan-fante
"""

import sys
import os
from pathlib import Path
import argparse
import hashlib
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json
import csv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient
from bson import ObjectId


# ============================================================================
# RISK MITIGATION: Hetzner Health Check
# ============================================================================

def check_hetzner_mount() -> Tuple[bool, str]:
    """
    Check if Hetzner storage is mounted and accessible.

    Returns:
        Tuple of (is_healthy, status_message)
    """
    mount_point = "/mnt/hetzner_storage"

    if not os.path.exists(mount_point):
        return False, f"❌ Mount point {mount_point} does not exist"

    if not os.path.ismount(mount_point):
        return False, f"❌ {mount_point} is not mounted"

    # Test write access
    test_file = os.path.join(mount_point, ".health_check")
    try:
        with open(test_file, 'w') as f:
            f.write(str(datetime.now()))
        os.remove(test_file)
        return True, f"✅ Hetzner storage healthy at {mount_point}"
    except Exception as e:
        return False, f"❌ Hetzner storage not writable: {e}"


def verify_backup_complete(dataset_name: str) -> Tuple[bool, str]:
    """
    Verify Twi-Akan-Fante backup completion before migration.

    Risk Mitigation: Wait for backup completion
    """
    if dataset_name != "twi-akan-fante":
        return True, "Not Twi dataset, skipping backup check"

    hetzner_path = "/mnt/hetzner_storage/voice-lab/data/twi-akan-fante/processed"
    if not os.path.exists(hetzner_path):
        return False, "❌ Twi dataset not found on Hetzner - backup incomplete"

    # Check for processed audio directory
    processed_audio = os.path.join(hetzner_path, "processed_audio")
    if not os.path.exists(processed_audio):
        return False, "❌ Processed audio not backed up yet"

    # Check manifest files
    manifests_dir = os.path.join(hetzner_path, "..", "model_manifests")
    if not os.path.exists(manifests_dir):
        return False, "❌ Manifest files not backed up yet"

    return True, "✅ Twi-Akan-Fante backup verified"


# ============================================================================
# Dataset Configuration
# ============================================================================

DATASETS_CONFIG = {
    "twi-akan-fante": {
        "name": "Twi-Akan-Fante Combined Speech Dataset",
        "language_code": "tw",
        "language_family": "Niger-Congo (Kwa)",
        "base_path": "/mnt/hetzner_storage/voice-lab/data/twi-akan-fante",
        "description": "Multi-dialect Twi (Asante, Akuapem) and Fante speech dataset with 212,469 transcribed samples. Processed at 16kHz for ASR and 44kHz for TTS training. Includes manifests for Whisper, MeloTTS, F5-TTS, Moshi, ChatTTS, and more.",
        "tags": ["twi", "fante", "akan", "asr", "tts", "ghana", "processed"],
        "training_ready": True,
        "has_manifests": True,
        "license_type": "cc_by",
        "commercial_use_allowed": True,
    },
    "ugdata-akan": {
        "name": "UGData Akan Speech Collection",
        "language_code": "ak",
        "language_family": "Niger-Congo (Kwa)",
        "base_path": "/mnt/hetzner_storage/voice-lab/datasets/ugdata_extracted/Akan",
        "description": "University of Ghana Akan speech dataset. Raw MP3 recordings requiring preprocessing for training use.",
        "tags": ["akan", "ghana", "raw", "ugdata"],
        "training_ready": False,
        "has_manifests": False,
        "license_type": "cc_by",
        "commercial_use_allowed": True,
    },
    "ugdata-dagaare": {
        "name": "UGData Dagaare Speech Collection",
        "language_code": "dga",
        "language_family": "Niger-Congo (Gur)",
        "base_path": "/mnt/hetzner_storage/voice-lab/datasets/ugdata_extracted/Dagaare",
        "description": "University of Ghana Dagaare speech dataset. Raw MP3 recordings.",
        "tags": ["dagaare", "ghana", "raw", "ugdata"],
        "training_ready": False,
        "has_manifests": False,
        "license_type": "cc_by",
        "commercial_use_allowed": True,
    },
    "ugdata-dagbani": {
        "name": "UGData Dagbani Speech Collection",
        "language_code": "dag",
        "language_family": "Niger-Congo (Gur)",
        "base_path": "/mnt/hetzner_storage/voice-lab/datasets/ugdata_extracted/Dagbani",
        "description": "University of Ghana Dagbani speech dataset with 18,200 MP3 files.",
        "tags": ["dagbani", "ghana", "raw", "ugdata"],
        "training_ready": False,
        "has_manifests": False,
        "license_type": "cc_by",
        "commercial_use_allowed": True,
    },
    "ugdata-ewe": {
        "name": "UGData Ewe Speech Collection",
        "language_code": "ee",
        "language_family": "Niger-Congo (Kwa)",
        "base_path": "/mnt/hetzner_storage/voice-lab/datasets/ugdata_extracted/Ewe",
        "description": "University of Ghana Ewe speech dataset with 19,152 MP3 files.",
        "tags": ["ewe", "ghana", "togo", "raw", "ugdata"],
        "training_ready": False,
        "has_manifests": False,
        "license_type": "cc_by",
        "commercial_use_allowed": True,
    },
    "ugdata-ikposo": {
        "name": "UGData Ikposo Speech Collection",
        "language_code": "kpo",
        "language_family": "Niger-Congo (Kwa)",
        "base_path": "/mnt/hetzner_storage/voice-lab/datasets/ugdata_extracted/Ikposo",
        "description": "University of Ghana Ikposo speech dataset with 18,175 MP3 files.",
        "tags": ["ikposo", "ghana", "togo", "raw", "ugdata"],
        "training_ready": False,
        "has_manifests": False,
        "license_type": "cc_by",
        "commercial_use_allowed": True,
    },
}


# ============================================================================
# Utility Functions
# ============================================================================

def get_directory_size_mb(path: str) -> float:
    """Get directory size in MB."""
    try:
        result = subprocess.run(
            ['du', '-sm', path],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            return float(result.stdout.split()[0])
    except:
        pass
    return 0.0


def count_files(path: str, extension: str = "*") -> int:
    """Count files in directory with given extension."""
    try:
        if extension == "*":
            result = subprocess.run(
                ['find', path, '-type', 'f'],
                capture_output=True,
                text=True,
                timeout=300
            )
        else:
            result = subprocess.run(
                ['find', path, '-name', f'*.{extension}'],
                capture_output=True,
                text=True,
                timeout=300
            )
        if result.returncode == 0:
            return len([line for line in result.stdout.strip().split('\n') if line])
    except:
        pass
    return 0


def compute_directory_checksum(path: str, sample_size: int = 100) -> str:
    """
    Compute checksum for directory by sampling files.

    Risk Mitigation: Incremental checksum computation
    """
    try:
        # Get list of files
        result = subprocess.run(
            ['find', path, '-type', 'f', '-name', '*.wav', '-o', '-name', '*.mp3'],
            capture_output=True,
            text=True,
            timeout=60
        )
        files = [f for f in result.stdout.strip().split('\n') if f]

        # Sample files if too many
        if len(files) > sample_size:
            import random
            files = random.sample(files, sample_size)

        # Compute combined checksum
        hasher = hashlib.sha256()
        for file_path in sorted(files)[:sample_size]:
            try:
                with open(file_path, 'rb') as f:
                    hasher.update(f.read(1024 * 1024))  # Read first 1MB
            except:
                continue

        return hasher.hexdigest()
    except:
        return "unknown"


def find_manifest_files(base_path: str) -> List[str]:
    """Find all manifest files in dataset."""
    manifests = []
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith(('.csv', '.txt')) and 'manifest' in root.lower():
                manifests.append(os.path.join(root, file))
    return manifests


# ============================================================================
# Migration Logic
# ============================================================================

def create_dataset_document(
    dataset_key: str,
    config: Dict,
    creator_id: ObjectId
) -> Dict:
    """
    Create dataset document for MongoDB.

    Args:
        dataset_key: Dataset identifier key
        config: Dataset configuration
        creator_id: User ID who created this dataset

    Returns:
        Dataset document ready for insertion
    """
    base_path = config["base_path"]

    # Gather statistics
    print(f"  📊 Gathering statistics for {dataset_key}...")
    total_files = count_files(base_path)
    total_size_mb = get_directory_size_mb(base_path)

    # Count audio files specifically
    wav_count = count_files(base_path, "wav")
    mp3_count = count_files(base_path, "mp3")
    audio_files = wav_count + mp3_count

    # Compute checksum
    print(f"  🔐 Computing checksum (sampling)...")
    checksum = compute_directory_checksum(base_path)

    # Find manifests
    manifest_files = find_manifest_files(base_path)

    # Estimate duration (rough estimate: 1 file = ~3 seconds average)
    estimated_duration_hours = (audio_files * 3) / 3600

    # Create document
    doc = {
        "_id": ObjectId(),
        "dataset_uuid": f"{dataset_key}-v1",
        "name": config["name"],
        "source": "manual_upload",
        "dataset_type": "audio_speech",
        "language_code": config["language_code"],
        "language_family": config.get("language_family"),

        # Versioning
        "version": "1.0.0",
        "is_latest_version": True,
        "version_history": [],

        # Storage
        "storage_path": base_path,
        "manifest_id": None,  # Will be set after manifest creation
        "checksum": checksum,
        "is_public": True,

        # Statistics
        "total_files": audio_files,
        "total_size_mb": total_size_mb,
        "total_duration_hours": round(estimated_duration_hours, 2),
        "quality_score": 0.85,  # Placeholder

        # Training readiness
        "training_ready": config["training_ready"],
        "has_train_split": config["has_manifests"],
        "has_validation_split": config["has_manifests"],
        "has_test_split": False,
        "split_ratios": {"train": 0.9, "val": 0.1} if config["has_manifests"] else None,

        # License
        "license_type": config["license_type"],
        "commercial_use_allowed": config["commercial_use_allowed"],

        # Processing status
        "processing_status": "completed" if config["training_ready"] else "pending",
        "processing_completed_at": datetime.utcnow() if config["training_ready"] else None,

        # MLOps tracking
        "used_in_pipelines": [],
        "used_in_models": [],

        # Metadata
        "description": config["description"],
        "tags": config["tags"],
        "created_by": str(creator_id),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),

        # Downloads
        "download_count": 0,
        "view_count": 0,
    }

    print(f"  ✅ Dataset document created:")
    print(f"     Files: {audio_files:,} | Size: {total_size_mb:,.0f} MB | Duration: ~{estimated_duration_hours:.1f}h")
    print(f"     Manifests: {len(manifest_files)}")

    return doc


def migrate_dataset(
    dataset_key: str,
    config: Dict,
    db,
    creator_id: ObjectId,
    dry_run: bool = True
) -> bool:
    """
    Migrate a single dataset.

    Args:
        dataset_key: Dataset identifier
        config: Dataset configuration
        db: MongoDB database connection
        creator_id: User ID creating the dataset
        dry_run: If True, don't actually insert

    Returns:
        Success boolean
    """
    print(f"\n{'='*70}")
    print(f"📦 Migrating: {config['name']}")
    print(f"{'='*70}")

    # Pre-flight checks
    print("🔍 Running pre-flight checks...")

    # Check if dataset already exists
    existing = db.external_datasets.find_one({"dataset_uuid": f"{dataset_key}-v1"})
    if existing:
        print(f"  ⚠️  Dataset already exists with ID: {existing['_id']}")
        print(f"  Skipping migration.")
        return False

    # Verify backup if Twi dataset
    if dataset_key == "twi-akan-fante":
        is_complete, msg = verify_backup_complete(dataset_key)
        print(f"  {msg}")
        if not is_complete:
            print(f"  ❌ Cannot migrate - backup incomplete")
            return False

    # Check if path exists
    if not os.path.exists(config["base_path"]):
        print(f"  ❌ Dataset path does not exist: {config['base_path']}")
        return False

    # Create dataset document
    try:
        dataset_doc = create_dataset_document(dataset_key, config, creator_id)
    except Exception as e:
        print(f"  ❌ Failed to create dataset document: {e}")
        return False

    # Insert into database
    if not dry_run:
        try:
            result = db.external_datasets.insert_one(dataset_doc)
            print(f"\n  ✅ Dataset inserted with ID: {result.inserted_id}")
            return True
        except Exception as e:
            print(f"\n  ❌ Failed to insert dataset: {e}")
            return False
    else:
        print(f"\n  🔍 DRY RUN - Would insert dataset with UUID: {dataset_doc['dataset_uuid']}")
        print(f"     Document preview:")
        print(f"     {json.dumps({k: v for k, v in dataset_doc.items() if k not in ['_id']}, indent=2, default=str)[:500]}...")
        return True


def main():
    parser = argparse.ArgumentParser(description="Migrate voice-lab datasets to community platform")
    parser.add_argument("--dry-run", action="store_true", help="Preview migration without making changes")
    parser.add_argument("--execute", action="store_true", help="Execute migration (writes to database)")
    parser.add_argument("--dataset", help="Migrate specific dataset only")

    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("❌ Must specify either --dry-run or --execute")
        sys.exit(1)

    dry_run = args.dry_run

    print("\n" + "="*70)
    print("🚀 VOICE LAB DATASET MIGRATION")
    print("="*70)
    print(f"Mode: {'🔍 DRY RUN (Preview Only)' if dry_run else '✅ EXECUTE (Will Modify Database)'}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")

    # Health checks
    print("🏥 Running health checks...")
    is_healthy, msg = check_hetzner_mount()
    print(f"  {msg}")
    if not is_healthy:
        print("\n❌ Health checks failed. Aborting migration.")
        sys.exit(1)

    # Connect to MongoDB
    print("\n📡 Connecting to MongoDB...")
    try:
        client = MongoClient("mongodb://localhost:27017/ailabsafrica")
        db = client.ailabsafrica
        print("  ✅ Connected to MongoDB")
    except Exception as e:
        print(f"  ❌ Failed to connect to MongoDB: {e}")
        sys.exit(1)

    # Get creator user
    creator = db.users.find_one({"email": "alfred.anyan@gmail.com"})
    if not creator:
        print("❌ Creator user not found. Run create_user.py first.")
        sys.exit(1)
    creator_id = creator["_id"]
    print(f"  👤 Creator: {creator['full_name']} ({creator_id})")

    # Determine datasets to migrate
    if args.dataset:
        if args.dataset not in DATASETS_CONFIG:
            print(f"❌ Unknown dataset: {args.dataset}")
            print(f"Available: {', '.join(DATASETS_CONFIG.keys())}")
            sys.exit(1)
        datasets_to_migrate = {args.dataset: DATASETS_CONFIG[args.dataset]}
    else:
        datasets_to_migrate = DATASETS_CONFIG

    print(f"\n📋 Datasets to migrate: {len(datasets_to_migrate)}")

    # Migrate each dataset
    results = {}
    for dataset_key, config in datasets_to_migrate.items():
        success = migrate_dataset(dataset_key, config, db, creator_id, dry_run)
        results[dataset_key] = success

    # Summary
    print("\n" + "="*70)
    print("📊 MIGRATION SUMMARY")
    print("="*70)
    successful = sum(1 for v in results.values() if v)
    failed = len(results) - successful

    for dataset_key, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {dataset_key}")

    print(f"\n  Total: {len(results)} | Successful: {successful} | Failed/Skipped: {failed}")

    if dry_run:
        print("\n🔍 This was a DRY RUN - no changes were made.")
        print("   Run with --execute to perform actual migration.")
    else:
        print("\n✅ Migration complete!")
        print(f"   {successful} datasets are now available in the community platform.")

    print("="*70 + "\n")

    client.close()


if __name__ == "__main__":
    main()
