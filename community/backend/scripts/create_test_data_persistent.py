#!/usr/bin/env python3
"""
Create Persistent Test Data for Frontend Testing

Creates realistic test data in MongoDB that persists for frontend component testing.
Data includes:
- 5 Models (TTS, ASR, NMT) with versions and metrics
- 3 Training Pipelines at different stages
- 4 External Resources with votes and clicks
- Test users

This data stays in the database for manual frontend testing.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/african_language_community?authSource=admin")


async def create_test_users(db):
    """Create test users"""
    print("📝 Creating test users...")

    users = [
        {
            "_id": ObjectId(),
            "supabase_id": f"frontend-test-user-{uuid.uuid4()}",
            "email": "john.doe@example.com",
            "username": "john_doe",
            "role": "user",
            "is_active": True,
            "created_at": datetime.utcnow() - timedelta(days=30),
            "total_points": 450
        },
        {
            "_id": ObjectId(),
            "supabase_id": f"frontend-test-user-{uuid.uuid4()}",
            "email": "jane.smith@example.com",
            "username": "jane_smith",
            "role": "contributor",
            "is_active": True,
            "created_at": datetime.utcnow() - timedelta(days=60),
            "total_points": 1200
        }
    ]

    result = await db.users.insert_many(users)
    print(f"   ✓ Created {len(result.inserted_ids)} users")
    return users


async def create_test_models(db, users):
    """Create test ML models"""
    print("\n🤖 Creating test models...")

    # Get language ID for Twi
    twi_lang = await db.languages.find_one({"code": "twi"})
    twi_id = str(twi_lang["_id"]) if twi_lang else None

    models = [
        {
            "_id": ObjectId(),
            "model_uuid": str(uuid.uuid4()),
            "name": "Twi TTS Tacotron2",
            "model_type": "tts",
            "architecture": "tacotron2",
            "languages": ["twi"],
            "language_ids": [twi_id] if twi_id else [],
            "description": "High-quality Text-to-Speech model for Twi language trained on 50 hours of speech data",
            "framework": "pytorch",
            "version": "2.1.0",
            "license": "MIT",
            "performance_metrics": {
                "mos": 4.2,  # Mean Opinion Score
                "inference_time_ms": 180,
                "model_size_mb": 45.3
            },
            "created_by": users[0]["_id"],
            "created_at": datetime.utcnow() - timedelta(days=15),
            "updated_at": datetime.utcnow() - timedelta(days=2),
            "download_count": 234,
            "view_count": 1523,
            "is_public": True,
            "deployment_status": "production",
            "tags": ["twi", "tts", "tacotron", "voice-synthesis"],
            "versions": [
                {
                    "version": "1.0.0",
                    "changelog": "Initial release",
                    "created_at": datetime.utcnow() - timedelta(days=60),
                    "performance_metrics": {"mos": 3.8, "inference_time_ms": 250}
                },
                {
                    "version": "2.0.0",
                    "changelog": "Improved prosody and naturalness",
                    "created_at": datetime.utcnow() - timedelta(days=30),
                    "performance_metrics": {"mos": 4.0, "inference_time_ms": 200}
                },
                {
                    "version": "2.1.0",
                    "changelog": "Optimized inference speed by 10%",
                    "created_at": datetime.utcnow() - timedelta(days=15),
                    "performance_metrics": {"mos": 4.2, "inference_time_ms": 180}
                }
            ]
        },
        {
            "_id": ObjectId(),
            "model_uuid": str(uuid.uuid4()),
            "name": "Twi ASR Wav2Vec2",
            "model_type": "asr",
            "architecture": "wav2vec2",
            "languages": ["twi"],
            "language_ids": [twi_id] if twi_id else [],
            "description": "Automatic Speech Recognition model for Twi with word error rate of 12%",
            "framework": "pytorch",
            "version": "1.5.0",
            "license": "Apache-2.0",
            "performance_metrics": {
                "wer": 0.12,  # Word Error Rate
                "cer": 0.08,  # Character Error Rate
                "inference_time_ms": 320,
                "model_size_mb": 315.7
            },
            "created_by": users[1]["_id"],
            "created_at": datetime.utcnow() - timedelta(days=45),
            "updated_at": datetime.utcnow() - timedelta(days=10),
            "download_count": 189,
            "view_count": 892,
            "is_public": True,
            "deployment_status": "production",
            "tags": ["twi", "asr", "wav2vec2", "speech-recognition"],
            "versions": [
                {
                    "version": "1.0.0",
                    "changelog": "Initial release with 15% WER",
                    "created_at": datetime.utcnow() - timedelta(days=90),
                    "performance_metrics": {"wer": 0.15, "cer": 0.10}
                },
                {
                    "version": "1.5.0",
                    "changelog": "Improved WER to 12% with expanded training data",
                    "created_at": datetime.utcnow() - timedelta(days=45),
                    "performance_metrics": {"wer": 0.12, "cer": 0.08}
                }
            ]
        },
        {
            "_id": ObjectId(),
            "model_uuid": str(uuid.uuid4()),
            "name": "English-Twi NMT Transformer",
            "model_type": "nmt",
            "architecture": "transformer",
            "languages": ["en", "twi"],
            "language_ids": [twi_id] if twi_id else [],
            "description": "Neural Machine Translation model for English to Twi translation",
            "framework": "tensorflow",
            "version": "1.0.0",
            "license": "MIT",
            "performance_metrics": {
                "bleu_score": 34.2,
                "inference_time_ms": 150,
                "model_size_mb": 256.9
            },
            "created_by": users[0]["_id"],
            "created_at": datetime.utcnow() - timedelta(days=20),
            "updated_at": datetime.utcnow() - timedelta(days=5),
            "download_count": 67,
            "view_count": 423,
            "is_public": True,
            "deployment_status": "beta",
            "tags": ["translation", "nmt", "english", "twi", "transformer"],
            "versions": []
        },
        {
            "_id": ObjectId(),
            "model_uuid": str(uuid.uuid4()),
            "name": "Twi TTS FastSpeech2",
            "model_type": "tts",
            "architecture": "fastspeech2",
            "languages": ["twi"],
            "language_ids": [twi_id] if twi_id else [],
            "description": "Fast and efficient TTS model optimized for real-time applications",
            "framework": "pytorch",
            "version": "1.2.0",
            "license": "MIT",
            "performance_metrics": {
                "mos": 4.0,
                "inference_time_ms": 95,
                "model_size_mb": 32.1
            },
            "created_by": users[1]["_id"],
            "created_at": datetime.utcnow() - timedelta(days=8),
            "updated_at": datetime.utcnow() - timedelta(days=1),
            "download_count": 45,
            "view_count": 234,
            "is_public": True,
            "deployment_status": "testing",
            "tags": ["twi", "tts", "fastspeech", "real-time"],
            "versions": []
        },
        {
            "_id": ObjectId(),
            "model_uuid": str(uuid.uuid4()),
            "name": "Twi Voice Cloning VITS",
            "model_type": "tts",
            "architecture": "vits",
            "languages": ["twi"],
            "language_ids": [twi_id] if twi_id else [],
            "description": "Advanced voice cloning model with few-shot learning capability",
            "framework": "pytorch",
            "version": "0.9.0",
            "license": "Apache-2.0",
            "performance_metrics": {
                "mos": 4.5,
                "inference_time_ms": 450,
                "model_size_mb": 128.3,
                "similarity_score": 0.92
            },
            "created_by": users[0]["_id"],
            "created_at": datetime.utcnow() - timedelta(days=3),
            "updated_at": datetime.utcnow(),
            "download_count": 12,
            "view_count": 89,
            "is_public": True,
            "deployment_status": "experimental",
            "tags": ["twi", "voice-cloning", "vits", "few-shot"],
            "versions": []
        }
    ]

    result = await db.ml_models.insert_many(models)
    print(f"   ✓ Created {len(result.inserted_ids)} models")
    return models


async def create_test_pipelines(db, users):
    """Create test training pipelines"""
    print("\n🔄 Creating test pipelines...")

    pipelines = [
        {
            "_id": ObjectId(),
            "pipeline_uuid": str(uuid.uuid4()),
            "name": "Yoruba TTS Training - Q4 2025",
            "description": "Training Tacotron2 model for Yoruba language with 100 hours of data",
            "model_type": "tts",
            "target_languages": ["yo"],
            "framework": "pytorch",
            "current_stage": "training",
            "status": "active",
            "priority": "high",
            "is_active": True,
            "created_by": users[0]["_id"],
            "created_at": datetime.utcnow() - timedelta(days=12),
            "updated_at": datetime.utcnow() - timedelta(hours=3),
            "stages": {
                "data_acquisition": {
                    "stage_name": "data_acquisition",
                    "status": "completed",
                    "started_at": datetime.utcnow() - timedelta(days=12),
                    "completed_at": datetime.utcnow() - timedelta(days=10),
                    "duration_minutes": 2880,
                    "metrics": {
                        "samples_collected": 105000,
                        "total_hours": 102.5,
                        "speakers": 45
                    },
                    "notes": "Successfully collected 102.5 hours from 45 speakers"
                },
                "preprocessing": {
                    "stage_name": "preprocessing",
                    "status": "completed",
                    "started_at": datetime.utcnow() - timedelta(days=10),
                    "completed_at": datetime.utcnow() - timedelta(days=8),
                    "duration_minutes": 2160,
                    "metrics": {
                        "samples_processed": 105000,
                        "samples_filtered": 3200,
                        "final_samples": 101800
                    },
                    "notes": "Filtered 3% of samples for quality issues"
                },
                "training": {
                    "stage_name": "training",
                    "status": "in_progress",
                    "started_at": datetime.utcnow() - timedelta(days=8),
                    "metrics": {
                        "current_epoch": 145,
                        "total_epochs": 300,
                        "train_loss": 0.342,
                        "val_loss": 0.389,
                        "learning_rate": 0.0001,
                        "samples_per_second": 12.5
                    },
                    "notes": "Training progressing well, loss decreasing steadily"
                },
                "evaluation": {
                    "stage_name": "evaluation",
                    "status": "pending",
                    "metrics": {}
                },
                "deployment": {
                    "stage_name": "deployment",
                    "status": "pending",
                    "metrics": {}
                }
            },
            "progress_percentage": 58,
            "estimated_completion": datetime.utcnow() + timedelta(days=6)
        },
        {
            "_id": ObjectId(),
            "pipeline_uuid": str(uuid.uuid4()),
            "name": "Igbo ASR Fine-tuning",
            "description": "Fine-tuning Wav2Vec2 on Igbo speech corpus",
            "model_type": "asr",
            "target_languages": ["ig"],
            "framework": "pytorch",
            "current_stage": "preprocessing",
            "status": "active",
            "priority": "medium",
            "is_active": True,
            "created_by": users[1]["_id"],
            "created_at": datetime.utcnow() - timedelta(days=5),
            "updated_at": datetime.utcnow() - timedelta(hours=1),
            "stages": {
                "data_acquisition": {
                    "stage_name": "data_acquisition",
                    "status": "completed",
                    "started_at": datetime.utcnow() - timedelta(days=5),
                    "completed_at": datetime.utcnow() - timedelta(days=3),
                    "duration_minutes": 1920,
                    "metrics": {
                        "samples_collected": 42000,
                        "total_hours": 38.5
                    }
                },
                "preprocessing": {
                    "stage_name": "preprocessing",
                    "status": "in_progress",
                    "started_at": datetime.utcnow() - timedelta(days=3),
                    "metrics": {
                        "samples_processed": 28000,
                        "samples_remaining": 14000,
                        "progress": 66.7
                    }
                },
                "training": {
                    "stage_name": "training",
                    "status": "pending",
                    "metrics": {}
                }
            },
            "progress_percentage": 33
        },
        {
            "_id": ObjectId(),
            "pipeline_uuid": str(uuid.uuid4()),
            "name": "Swahili Translation Model",
            "description": "Training English-Swahili NMT transformer",
            "model_type": "nmt",
            "target_languages": ["sw", "en"],
            "framework": "tensorflow",
            "current_stage": "evaluation",
            "status": "paused",
            "priority": "low",
            "is_active": False,
            "created_by": users[0]["_id"],
            "created_at": datetime.utcnow() - timedelta(days=25),
            "updated_at": datetime.utcnow() - timedelta(days=3),
            "stages": {
                "data_acquisition": {
                    "stage_name": "data_acquisition",
                    "status": "completed",
                    "completed_at": datetime.utcnow() - timedelta(days=20),
                    "metrics": {
                        "parallel_sentences": 2500000
                    }
                },
                "preprocessing": {
                    "stage_name": "preprocessing",
                    "status": "completed",
                    "completed_at": datetime.utcnow() - timedelta(days=18),
                    "metrics": {
                        "tokenized_pairs": 2500000
                    }
                },
                "training": {
                    "stage_name": "training",
                    "status": "completed",
                    "completed_at": datetime.utcnow() - timedelta(days=5),
                    "metrics": {
                        "final_loss": 1.234,
                        "epochs_completed": 50
                    }
                },
                "evaluation": {
                    "stage_name": "evaluation",
                    "status": "in_progress",
                    "started_at": datetime.utcnow() - timedelta(days=5),
                    "metrics": {
                        "bleu_score": 28.4,
                        "test_samples_evaluated": 5000
                    }
                }
            },
            "progress_percentage": 85,
            "notes": "Paused for resource reallocation"
        }
    ]

    result = await db.ml_training_pipelines.insert_many(pipelines)
    print(f"   ✓ Created {len(result.inserted_ids)} pipelines")
    return pipelines


async def create_test_resources(db, users):
    """Create test external resources"""
    print("\n📚 Creating test resources...")

    resources = [
        {
            "_id": ObjectId(),
            "link_uuid": str(uuid.uuid4()),
            "title": "Mozilla Common Voice - Twi",
            "url": "https://commonvoice.mozilla.org/twi",
            "description": "Open-source, multi-lingual dataset of voices for speech recognition",
            "language_code": "twi",
            "resource_type": "dataset",
            "source_attribution": "Mozilla Foundation",
            "submitted_by": users[0]["_id"],
            "submitted_at": datetime.utcnow() - timedelta(days=60),
            "verification_status": "verified",
            "is_verified": True,
            "verified_at": datetime.utcnow() - timedelta(days=58),
            "verified_by": users[1]["_id"],
            "upvotes": 45,
            "downvotes": 2,
            "click_count": 234,
            "is_active": True,
            "tags": ["speech", "open-source", "crowdsourced"]
        },
        {
            "_id": ObjectId(),
            "link_uuid": str(uuid.uuid4()),
            "title": "Akan (Twi) Bible Corpus",
            "url": "https://github.com/bible-technology/akan-bible",
            "description": "Parallel text corpus of Akan Bible translations, useful for NLP research",
            "language_code": "twi",
            "resource_type": "dataset",
            "source_attribution": "Bible Technology",
            "submitted_by": users[1]["_id"],
            "submitted_at": datetime.utcnow() - timedelta(days=45),
            "verification_status": "verified",
            "is_verified": True,
            "verified_at": datetime.utcnow() - timedelta(days=43),
            "upvotes": 28,
            "downvotes": 1,
            "click_count": 156,
            "is_active": True,
            "tags": ["text", "parallel-corpus", "religious"]
        },
        {
            "_id": ObjectId(),
            "link_uuid": str(uuid.uuid4()),
            "title": "Coqui TTS Twi Model",
            "url": "https://huggingface.co/coqui/tts-twi",
            "description": "Pre-trained Coqui TTS model for Twi language on HuggingFace",
            "language_code": "twi",
            "resource_type": "model",
            "source_attribution": "Coqui AI",
            "submitted_by": users[0]["_id"],
            "submitted_at": datetime.utcnow() - timedelta(days=30),
            "verification_status": "pending",
            "is_verified": False,
            "upvotes": 18,
            "downvotes": 0,
            "click_count": 98,
            "is_active": True,
            "tags": ["tts", "pre-trained", "huggingface"]
        },
        {
            "_id": ObjectId(),
            "link_uuid": str(uuid.uuid4()),
            "title": "Twi Language Processing Toolkit",
            "url": "https://github.com/akan-nlp/toolkit",
            "description": "Python toolkit for Twi NLP with tokenizers, POS taggers, and utilities",
            "language_code": "twi",
            "resource_type": "tool",
            "source_attribution": "Akan NLP Community",
            "submitted_by": users[1]["_id"],
            "submitted_at": datetime.utcnow() - timedelta(days=15),
            "verification_status": "verified",
            "is_verified": True,
            "verified_at": datetime.utcnow() - timedelta(days=12),
            "upvotes": 34,
            "downvotes": 3,
            "click_count": 187,
            "is_active": True,
            "tags": ["nlp", "toolkit", "python", "open-source"]
        }
    ]

    result = await db.external_resources.insert_many(resources)
    print(f"   ✓ Created {len(result.inserted_ids)} resources")
    return resources


async def print_summary(models, pipelines, resources, users):
    """Print summary of created data"""
    print("\n" + "="*60)
    print("📊 TEST DATA SUMMARY")
    print("="*60)
    print(f"\n👥 Users: {len(users)}")
    for user in users:
        print(f"   - {user['username']} ({user['email']})")

    print(f"\n🤖 Models: {len(models)}")
    for model in models:
        print(f"   - {model['name']} ({model['model_type'].upper()}) - {model['deployment_status']}")
        print(f"     UUID: {model['model_uuid']}")
        print(f"     Downloads: {model['download_count']}, Views: {model['view_count']}")

    print(f"\n🔄 Pipelines: {len(pipelines)}")
    for pipeline in pipelines:
        print(f"   - {pipeline['name']} ({pipeline['model_type'].upper()}) - {pipeline['status']}")
        print(f"     UUID: {pipeline['pipeline_uuid']}")
        print(f"     Stage: {pipeline['current_stage']} ({pipeline['progress_percentage']}%)")

    print(f"\n📚 Resources: {len(resources)}")
    for resource in resources:
        print(f"   - {resource['title']} ({resource['resource_type']})")
        print(f"     UUID: {resource['link_uuid']}")
        print(f"     Upvotes: {resource['upvotes']}, Clicks: {resource['click_count']}")

    print("\n" + "="*60)
    print("✅ Frontend test data created successfully!")
    print("="*60)
    print("\nTest the frontend at: http://localhost:3000")
    print("API endpoints: http://localhost:8020/api/v1/\n")


async def main():
    """Create all test data"""
    print("\n🚀 Creating Persistent Test Data for Frontend Testing\n")

    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()  # Use database from connection string

    try:
        # Verify connection
        await client.admin.command('ping')
        print("✅ Connected to MongoDB\n")

        # Create test data
        users = await create_test_users(db)
        models = await create_test_models(db, users)
        pipelines = await create_test_pipelines(db, users)
        resources = await create_test_resources(db, users)

        # Print summary
        await print_summary(models, pipelines, resources, users)

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    finally:
        client.close()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
