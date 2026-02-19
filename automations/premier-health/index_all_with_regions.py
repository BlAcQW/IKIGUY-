#!/usr/bin/env python3
"""
Index all Premier Health documents with region metadata in embeddings.
This script generates embeddings for documents and stores them with proper region metadata.
"""

import os
import sys
import uuid
import psycopg2
import psycopg2.extras
import google.generativeai as genai
from typing import List, Dict
import json
import time

# Configuration
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "aawwER444444")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAACjmMMYIVH2Pq8Ns8KbOud-X8oCQMny4")
COLLECTION_NAME = "helpdesk_premier_health_production"

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


def get_db_connection():
    """Get PostgreSQL database connection."""
    return psycopg2.connect(
        host="127.0.0.1",
        database="kasaai_core",
        user="postgres",
        password=POSTGRES_PASSWORD
    )


def generate_embedding(text: str) -> List[float]:
    """Generate embedding using Gemini API."""
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"      ❌ Error generating embedding: {e}")
        return None


def index_all_documents():
    """Index all documents with region metadata."""
    print("🔧 INDEXING ALL DOCUMENTS WITH REGION METADATA")
    print("=" * 80)

    conn = get_db_connection()
    cur = conn.cursor()

    # Get collection UUID
    cur.execute("""
        SELECT uuid FROM langchain_pg_collection
        WHERE name = %s
    """, (COLLECTION_NAME,))

    result = cur.fetchone()
    if not result:
        print(f"❌ Collection {COLLECTION_NAME} not found!")
        return

    collection_uuid = result[0]
    print(f"✅ Collection UUID: {collection_uuid}")
    print(f"📚 Collection Name: {COLLECTION_NAME}")

    # Find all documents that need indexing (no status filter or empty status)
    cur.execute("""
        SELECT id, document_id, title, content, metadata, tags
        FROM kb_documents
        WHERE collection_name = %s
        AND (vector_ids IS NULL OR array_length(vector_ids, 1) IS NULL)
        ORDER BY id
    """, (COLLECTION_NAME,))

    documents = cur.fetchall()
    total = len(documents)

    print(f"\n📊 Found {total} documents to index")
    print("=" * 80)

    if total == 0:
        print("✅ No documents need indexing!")
        return

    success_count = 0
    fail_count = 0

    for i, (doc_id, document_id, title, content, metadata, tags) in enumerate(documents, 1):
        try:
            # Parse metadata
            if isinstance(metadata, str):
                metadata_dict = json.loads(metadata)
            else:
                metadata_dict = metadata if metadata else {}

            region = metadata_dict.get('region', 'UNKNOWN')
            city = metadata_dict.get('city', 'UNKNOWN')

            print(f"\n[{i}/{total}] {title}")
            print(f"   Region: {region}")
            print(f"   City: {city}")
            print(f"   Content: {len(content)} chars")

            # Generate embedding
            print(f"   🔄 Generating embedding...")
            embedding = generate_embedding(content)

            if not embedding:
                print(f"   ❌ Failed to generate embedding")
                fail_count += 1
                continue

            # Prepare embedding metadata with region information
            embedding_metadata = {
                'title': title,
                'document_id': document_id,
                'region': region,
                'city': city,
                'provider_count': metadata_dict.get('provider_count', 0),
                'source': metadata_dict.get('source', 'unknown'),
                'tags': tags if tags else []
            }

            # Insert embedding into langchain_pg_embedding
            embedding_uuid = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO langchain_pg_embedding (id, collection_id, embedding, document, cmetadata)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                embedding_uuid,
                collection_uuid,
                embedding,
                content,
                psycopg2.extras.Json(embedding_metadata)
            ))

            embedding_id = cur.fetchone()[0]
            print(f"   ✅ Embedding ID: {embedding_id[:16]}...")

            # Update document with vector_id and status
            cur.execute("""
                UPDATE kb_documents
                SET
                    vector_ids = ARRAY[%s],
                    status = 'indexed',
                    indexed_at = NOW()
                WHERE id = %s
            """, (embedding_id, doc_id))

            conn.commit()
            print(f"   ✅ Successfully indexed")
            success_count += 1

            # Small delay every 10 documents to avoid rate limiting
            if i % 10 == 0:
                print(f"\n   ⏸️  Pausing for 1 second (processed {i}/{total})...")
                time.sleep(1)

        except Exception as e:
            print(f"   ❌ Error: {e}")
            fail_count += 1
            conn.rollback()

    cur.close()
    conn.close()

    print("\n" + "=" * 80)
    print("📊 INDEXING SUMMARY")
    print("=" * 80)
    print(f"Total documents: {total}")
    print(f"✅ Successfully indexed: {success_count}")
    print(f"❌ Failed: {fail_count}")
    if total > 0:
        print(f"📈 Success rate: {(success_count/total*100):.1f}%")
    print("=" * 80)

    if success_count > 0:
        print("\n✅ NEXT STEPS:")
        print("1. Verify region tags are properly set")
        print("2. Update RAG service to use region filtering")
        print("3. Clear cache and restart backend")
        print("4. Test region-based queries")


if __name__ == "__main__":
    print(f"Using collection: {COLLECTION_NAME}")
    print(f"GEMINI_API_KEY configured: {'✅ Yes' if GEMINI_API_KEY else '❌ No'}")
    print(f"POSTGRES_PASSWORD configured: {'✅ Yes' if POSTGRES_PASSWORD else '❌ No'}")
    print()

    if not GEMINI_API_KEY:
        print("❌ ERROR: GEMINI_API_KEY not set!")
        sys.exit(1)

    if not POSTGRES_PASSWORD:
        print("❌ ERROR: POSTGRES_PASSWORD not set!")
        sys.exit(1)

    index_all_documents()
