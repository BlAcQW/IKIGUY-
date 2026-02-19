#!/usr/bin/env python3
"""
Extract topics from existing materials using their RAG content.

For materials that already have embeddings, query the RAG to get content
and extract accurate topics based on actual document content.

Created: 2025-11-19
Author: KasaAI
"""

import asyncio
import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient

# Add paths
sys.path.insert(0, "/opt/kasaai/apps/studyflow/backend")
sys.path.insert(0, "/opt/kasaai/apps")

# Load .env
from dotenv import load_dotenv
env_path = Path("/opt/kasaai/apps/studyflow/backend/.env")
load_dotenv(env_path)

from app.core.database import MongoDB
from app.services.exercise_service import ExerciseService
from app.utils.topic_extraction import extract_topics_from_content
from bson import ObjectId


async def extract_topics_from_rag():
    """Extract topics from materials using their RAG content."""
    # Connect to MongoDB
    await MongoDB.connect()
    client = AsyncIOMotorClient('mongodb://admin:aawwER4444%25@127.0.0.1:27017/')
    db = client['studyflow']
    materials = db['materials']

    print("🔍 Extracting topics from material content via RAG...\n")

    # Get materials with embedding collections
    updated_count = 0
    failed_count = 0

    async for material in materials.find({"embedding_collection": {"$exists": True, "$ne": None}}):
        material_id = str(material['_id'])
        title = material.get('title', 'Unknown')
        subject = material.get('subject', '')
        current_topics = material.get('topics', [])
        embedding_collection = material.get('embedding_collection')

        print(f"📚 {title}")
        print(f"   Current topics: {current_topics}")

        try:
            # Query RAG to get material content
            rag = ExerciseService.get_rag_service()
            rag_result = await rag.query_knowledge_base(
                collection_name=embedding_collection,
                query=f"Summarize the main concepts covered in: {title}"
            )

            if not rag_result.success:
                print(f"   ❌ RAG query failed: {rag_result.error_message}\n")
                failed_count += 1
                continue

            # Extract topics from content
            new_topics = await extract_topics_from_content(
                content=rag_result.response,
                title=title,
                subject=subject
            )

            if new_topics and len(new_topics) > 0:
                # Update material
                result = await materials.update_one(
                    {'_id': ObjectId(material_id)},
                    {'$set': {'topics': new_topics}}
                )

                if result.modified_count > 0:
                    print(f"   ✅ New topics: {new_topics}\n")
                    updated_count += 1
                else:
                    print(f"   ⚠️  Topics unchanged\n")
            else:
                print(f"   ❌ No topics extracted\n")
                failed_count += 1

        except Exception as e:
            print(f"   ❌ Error: {str(e)}\n")
            failed_count += 1

    print(f"✅ Summary:")
    print(f"   Updated: {updated_count}")
    print(f"   Failed: {failed_count}")

    client.close()


if __name__ == "__main__":
    asyncio.run(extract_topics_from_rag())
