"""
Masakhane & African Language Dataset Migration Script

Migrates datasets from various African NLP sources:
- MasakhaNER 2.0 (Named Entity Recognition)
- LAFAND-MT (Machine Translation)
- MasakhaPOS (Part-of-Speech Tagging)
- Financial Inclusion Speech Dataset (Ashesi University)

Usage:
    # Dry run (preview without changes)
    python scripts/migrate_masakhane_datasets.py --dry-run

    # Execute migration
    python scripts/migrate_masakhane_datasets.py --execute

    # Migrate specific dataset
    python scripts/migrate_masakhane_datasets.py --execute --dataset masakhaner-twi
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

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient
from bson import ObjectId


# ============================================================================
# Dataset Configuration
# ============================================================================

DATASETS_CONFIG = {
    # MasakhaNER 2.0 Datasets (NER)
    "masakhaner-twi": {
        "name": "MasakhaNER 2.0 - Twi Named Entity Recognition",
        "source": "masakhane",
        "dataset_type": "text_corpus",
        "language_code": "tw",
        "language_family": "Niger-Congo (Kwa)",
        "source_url": "https://github.com/masakhane-io/masakhane-ner/tree/main/MasakhaNER2.0/data/twi",
        "description": "Named Entity Recognition dataset for Twi language. Part of MasakhaNER 2.0 covering 20 African languages. Annotated text corpus with person, location, organization, and other entity types.",
        "tags": ["twi", "ner", "masakhane", "ghana", "nlp", "entities"],
        "license_type": "cc_by",
        "commercial_use_allowed": True,
        "github_repo": "masakhane-io/masakhane-ner",
        "github_path": "MasakhaNER2.0/data/twi",
        "task_type": "ner",
        "download_method": "github_raw",
    },
    "masakhaner-ewe": {
        "name": "MasakhaNER 2.0 - Ewe Named Entity Recognition",
        "source": "masakhane",
        "dataset_type": "text_corpus",
        "language_code": "ee",
        "language_family": "Niger-Congo (Kwa)",
        "source_url": "https://github.com/masakhane-io/masakhane-ner/tree/main/MasakhaNER2.0/data/ewe",
        "description": "Named Entity Recognition dataset for Ewe language. Annotated text corpus for NER tasks.",
        "tags": ["ewe", "ner", "masakhane", "ghana", "togo", "nlp", "entities"],
        "license_type": "cc_by",
        "commercial_use_allowed": True,
        "github_repo": "masakhane-io/masakhane-ner",
        "github_path": "MasakhaNER2.0/data/ewe",
        "task_type": "ner",
        "download_method": "github_raw",
    },

    # LAFAND-MT Datasets (Machine Translation)
    "lafand-twi": {
        "name": "MAFAND-MT - Twi Machine Translation Dataset",
        "source": "masakhane",
        "dataset_type": "translation_pairs",
        "language_code": "tw",
        "language_family": "Niger-Congo (Kwa)",
        "source_url": "https://github.com/masakhane-io/lafand-mt",
        "description": "Machine translation dataset in the news domain for Twi. Parallel corpus with English-Twi translation pairs. Part of MAFAND-MT covering 16 African languages.",
        "tags": ["twi", "translation", "mt", "masakhane", "ghana", "nlp", "parallel-corpus"],
        "license_type": "cc_by_nc",
        "commercial_use_allowed": False,
        "github_repo": "masakhane-io/lafand-mt",
        "github_path": "data/twi",
        "task_type": "translation",
        "download_method": "github_raw",
        "paper_citation": "Adelani et al., NAACL 2022",
    },
    "lafand-ewe": {
        "name": "MAFAND-MT - Ewe Machine Translation Dataset",
        "source": "masakhane",
        "dataset_type": "translation_pairs",
        "language_code": "ee",
        "language_family": "Niger-Congo (Kwa)",
        "source_url": "https://github.com/masakhane-io/lafand-mt",
        "description": "Machine translation dataset in the news domain for Ewe. Parallel corpus with English-Ewe translation pairs.",
        "tags": ["ewe", "translation", "mt", "masakhane", "ghana", "togo", "nlp"],
        "license_type": "cc_by_nc",
        "commercial_use_allowed": False,
        "github_repo": "masakhane-io/lafand-mt",
        "github_path": "data/ewe",
        "task_type": "translation",
        "download_method": "github_raw",
    },

    # MasakhaPOS Datasets (Part-of-Speech Tagging)
    # Note: Need to verify which Ghanaian languages are in MasakhaPOS
    "masakhane-pos": {
        "name": "MasakhaPOS - African Languages POS Tagging",
        "source": "masakhane",
        "dataset_type": "text_corpus",
        "language_code": "multi",
        "language_family": "Various African languages",
        "source_url": "https://github.com/masakhane-io/masakhane-pos",
        "description": "Part-of-speech tagging dataset for 20 typologically diverse African languages. Annotated using Universal Dependencies guidelines. Check if Ghanaian languages (Twi, Ga, Ewe) are included.",
        "tags": ["pos", "masakhane", "africa", "nlp", "universal-dependencies"],
        "license_type": "cc_by_nc",
        "commercial_use_allowed": False,
        "github_repo": "masakhane-io/masakhane-pos",
        "github_path": "data",
        "task_type": "pos_tagging",
        "download_method": "github_raw",
        "paper_citation": "ACL 2023",
    },

    # Financial Inclusion Speech Dataset (Ashesi)
    "financial-inclusion-akuapem": {
        "name": "Financial Inclusion - Akuapem Twi Speech",
        "source": "custom_scrape",
        "dataset_type": "audio_speech",
        "language_code": "tw",
        "language_family": "Niger-Congo (Kwa)",
        "source_url": "https://github.com/Ashesi-Org/Financial-Inclusion-Speech-Dataset",
        "description": "~38 hours of Akuapem Twi speech from ~200 speakers. Financial services domain with ~130 sentences per speaker. Format: OGG audio. Total size: ~300MB. Quality: 2.8% low-quality rate.",
        "tags": ["twi", "akuapem", "speech", "asr", "ghana", "financial", "ashesi"],
        "license_type": "cc_by",
        "commercial_use_allowed": True,
        "total_duration_hours": 38.0,
        "total_size_mb": 300,
        "total_files": 26000,  # Estimated: 200 speakers * 130 sentences
        "training_ready": False,
        "download_method": "aws_s3",
        "download_url": "s3://financial-inclusion-dataset/akuapem/",
    },
    "financial-inclusion-asante": {
        "name": "Financial Inclusion - Asante Twi Speech",
        "source": "custom_scrape",
        "dataset_type": "audio_speech",
        "language_code": "tw",
        "language_family": "Niger-Congo (Kwa)",
        "source_url": "https://github.com/Ashesi-Org/Financial-Inclusion-Speech-Dataset",
        "description": "~30 hours of Asante Twi speech from ~200 speakers. Financial services domain. Format: OGG audio. ~238MB. Quality: 1.6% low-quality rate.",
        "tags": ["twi", "asante", "speech", "asr", "ghana", "financial", "ashesi"],
        "license_type": "cc_by",
        "commercial_use_allowed": True,
        "total_duration_hours": 30.0,
        "total_size_mb": 238,
        "total_files": 26000,
        "training_ready": False,
        "download_method": "aws_s3",
        "download_url": "s3://financial-inclusion-dataset/asante/",
    },
    "financial-inclusion-fante": {
        "name": "Financial Inclusion - Fante Speech",
        "source": "custom_scrape",
        "dataset_type": "audio_speech",
        "language_code": "fat",
        "language_family": "Niger-Congo (Kwa)",
        "source_url": "https://github.com/Ashesi-Org/Financial-Inclusion-Speech-Dataset",
        "description": "~39 hours of Fante speech from ~200 speakers. Financial services domain. Format: OGG audio. ~310MB. Quality: 1.3% low-quality rate.",
        "tags": ["fante", "speech", "asr", "ghana", "financial", "ashesi"],
        "license_type": "cc_by",
        "commercial_use_allowed": True,
        "total_duration_hours": 39.0,
        "total_size_mb": 310,
        "total_files": 26000,
        "training_ready": False,
        "download_method": "aws_s3",
        "download_url": "s3://financial-inclusion-dataset/fante/",
    },
    "financial-inclusion-ga": {
        "name": "Financial Inclusion - Ga Speech",
        "source": "custom_scrape",
        "dataset_type": "audio_speech",
        "language_code": "gaa",
        "language_family": "Niger-Congo (Kwa)",
        "source_url": "https://github.com/Ashesi-Org/Financial-Inclusion-Speech-Dataset",
        "description": "~40 hours of Ga speech from ~200 speakers. Financial services domain. Format: OGG audio. ~318MB. Quality: 0.1% low-quality rate (highest quality).",
        "tags": ["ga", "speech", "asr", "ghana", "financial", "ashesi"],
        "license_type": "cc_by",
        "commercial_use_allowed": True,
        "total_duration_hours": 40.0,
        "total_size_mb": 318,
        "total_files": 26000,
        "training_ready": False,
        "download_method": "aws_s3",
        "download_url": "s3://financial-inclusion-dataset/ga/",
    },
}


# ============================================================================
# Utility Functions
# ============================================================================

def check_mongodb_connection() -> Tuple[bool, str]:
    """Check MongoDB connection health."""
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
        client.server_info()
        return True, "✅ MongoDB connection healthy"
    except Exception as e:
        return False, f"❌ MongoDB connection failed: {e}"


def check_github_access() -> Tuple[bool, str]:
    """Check if GitHub API is accessible."""
    try:
        result = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'https://api.github.com'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.stdout.strip() == "200":
            return True, "✅ GitHub API accessible"
        return False, f"❌ GitHub API returned status: {result.stdout.strip()}"
    except Exception as e:
        return False, f"❌ GitHub API check failed: {e}"


def estimate_text_corpus_size(dataset_key: str, config: Dict) -> Tuple[int, float]:
    """
    Estimate text corpus size.

    Returns:
        Tuple of (file_count, size_mb)
    """
    # Rough estimates based on typical NER/MT/POS datasets
    task_type = config.get("task_type", "text")

    estimates = {
        "ner": (3000, 5.0),  # train/dev/test files with annotations
        "translation": (10000, 15.0),  # parallel sentence pairs
        "pos_tagging": (5000, 8.0),  # annotated sentences
    }

    return estimates.get(task_type, (1000, 2.0))


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
    print(f"  📊 Creating document for {dataset_key}...")

    # Get size estimates
    if config["dataset_type"] == "audio_speech":
        total_files = config.get("total_files", 0)
        total_size_mb = config.get("total_size_mb", 0)
        total_duration_hours = config.get("total_duration_hours", 0)
    else:
        total_files, total_size_mb = estimate_text_corpus_size(dataset_key, config)
        total_duration_hours = None

    # Determine storage path
    if config.get("download_method") == "github_raw":
        storage_path = f"/mnt/hetzner_storage/voice-lab/datasets/masakhane/{config['github_path']}"
    elif config.get("download_method") == "aws_s3":
        storage_path = f"/mnt/hetzner_storage/voice-lab/datasets/financial-inclusion/{dataset_key.split('-')[-1]}"
    else:
        storage_path = f"/mnt/hetzner_storage/voice-lab/datasets/external/{dataset_key}"

    # Create document
    doc = {
        "_id": ObjectId(),
        "dataset_uuid": f"{dataset_key}-v1",
        "name": config["name"],
        "source": config["source"],
        "dataset_type": config["dataset_type"],
        "language_code": config["language_code"],
        "language_family": config.get("language_family"),

        # Versioning
        "version": "1.0.0",
        "is_latest_version": True,
        "version_history": [],

        # Source information
        "source_url": config.get("source_url"),
        "source_version": config.get("source_version"),
        "source_metadata": {
            "github_repo": config.get("github_repo"),
            "github_path": config.get("github_path"),
            "task_type": config.get("task_type"),
            "download_method": config.get("download_method"),
            "download_url": config.get("download_url"),
            "paper_citation": config.get("paper_citation"),
        },

        # Storage
        "storage_path": storage_path,
        "manifest_id": None,
        "checksum": None,  # Will be computed after download
        "is_public": True,
        "hosting_type": "external",  # Will change to "local" after download

        # Statistics
        "total_files": total_files,
        "total_size_mb": total_size_mb,
        "total_duration_hours": total_duration_hours,
        "quality_score": None,  # Will be computed after processing

        # Training readiness
        "training_ready": config.get("training_ready", False),
        "has_train_split": False,  # Will update after download
        "has_validation_split": False,
        "has_test_split": False,
        "split_ratios": None,

        # License
        "license_type": config["license_type"],
        "commercial_use_allowed": config["commercial_use_allowed"],

        # Processing status
        "processing_status": "pending",
        "processing_completed_at": None,

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

    print(f"  ✅ Document created:")
    print(f"     Name: {config['name']}")
    print(f"     Type: {config['dataset_type']}")
    print(f"     Language: {config['language_code']}")
    print(f"     Estimated Size: {total_size_mb:.1f} MB")
    if total_duration_hours:
        print(f"     Duration: {total_duration_hours:.1f} hours")

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
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Migrate Masakhane and African language datasets to community platform"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview migration without making changes")
    parser.add_argument("--execute", action="store_true", help="Execute migration (writes to database)")
    parser.add_argument("--dataset", help="Migrate specific dataset only")
    parser.add_argument("--category", choices=["ner", "mt", "pos", "speech", "all"],
                       default="all", help="Migrate datasets by category")

    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("❌ Must specify either --dry-run or --execute")
        sys.exit(1)

    dry_run = args.dry_run

    print("\n" + "="*70)
    print("🚀 MASAKHANE & AFRICAN LANGUAGE DATASET MIGRATION")
    print("="*70)
    print(f"Mode: {'🔍 DRY RUN (Preview Only)' if dry_run else '✅ EXECUTE (Will Modify Database)'}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")

    # Health checks
    print("🏥 Running health checks...")

    mongo_ok, mongo_msg = check_mongodb_connection()
    print(f"  {mongo_msg}")
    if not mongo_ok:
        print("\n❌ Health checks failed. Aborting migration.")
        sys.exit(1)

    github_ok, github_msg = check_github_access()
    print(f"  {github_msg}")
    if not github_ok:
        print("  ⚠️  GitHub API not accessible - downloads may fail")

    # Connect to MongoDB
    print("\n📡 Connecting to MongoDB...")
    try:
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin")
        client = MongoClient(mongodb_url)
        db = client.kasaai_core
        # Test connection
        db.command('ping')
        print("  ✅ Connected to MongoDB (kasaai_core)")
    except Exception as e:
        print(f"  ❌ Failed to connect to MongoDB: {e}")
        sys.exit(1)

    # Get creator user
    creator = db.users.find_one({"email": "alfred.anyan@gmail.com"})
    if not creator:
        print("❌ Creator user not found.")
        sys.exit(1)
    creator_id = creator["_id"]
    print(f"  👤 Creator: {creator.get('full_name', 'Unknown')} ({creator_id})")

    # Determine datasets to migrate
    if args.dataset:
        if args.dataset not in DATASETS_CONFIG:
            print(f"❌ Unknown dataset: {args.dataset}")
            print(f"Available: {', '.join(DATASETS_CONFIG.keys())}")
            sys.exit(1)
        datasets_to_migrate = {args.dataset: DATASETS_CONFIG[args.dataset]}
    elif args.category != "all":
        # Filter by category
        category_map = {
            "ner": ["masakhaner-twi", "masakhaner-ewe"],
            "mt": ["lafand-twi", "lafand-ewe"],
            "pos": ["masakhane-pos"],
            "speech": [
                "financial-inclusion-akuapem",
                "financial-inclusion-asante",
                "financial-inclusion-fante",
                "financial-inclusion-ga"
            ]
        }
        dataset_keys = category_map.get(args.category, [])
        datasets_to_migrate = {k: DATASETS_CONFIG[k] for k in dataset_keys}
    else:
        datasets_to_migrate = DATASETS_CONFIG

    print(f"\n📋 Datasets to migrate: {len(datasets_to_migrate)}")
    for key in datasets_to_migrate.keys():
        print(f"  - {key}")

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
        print(f"   {successful} datasets are now registered in the community platform.")
        print("\n📥 Next steps:")
        print("   1. Download datasets to Hetzner storage")
        print("   2. Process datasets for training readiness")
        print("   3. Update dataset documents with actual statistics")

    print("="*70 + "\n")

    client.close()


if __name__ == "__main__":
    main()
