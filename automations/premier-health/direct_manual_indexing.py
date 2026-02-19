#!/usr/bin/env python3
"""
Direct manual indexing using Gemini API and PostgreSQL only.
No MongoDB, no async complexity - just generate embeddings and update the database.
"""

import os
import sys
import uuid
import psycopg2
import psycopg2.extras
import google.generativeai as genai
from typing import List

# Configuration
POSTGRES_PASSWORD = "aawwER444444"
GEMINI_API_KEY = "AIzaSyAACjmMMYIVH2Pq8Ns8KbOud-X8oCQMny4"
COLLECTION_NAME = "helpdesk_helpdesk_premier_health_production"

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
        print(f"      Error generating embedding: {e}")
        return None


def manual_index_all_documents():
    """Manually index all documents by generating embeddings and updating PostgreSQL."""
    print("🔧 DIRECT MANUAL INDEXING")
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
    print(f"Collection UUID: {collection_uuid}")

    # Find all documents that need indexing
    cur.execute("""
        SELECT id, document_id, title, content
        FROM kb_documents
        WHERE collection_name = %s
        AND status = 'processing'
        AND (vector_ids IS NULL OR array_length(vector_ids, 1) IS NULL)
        ORDER BY id
    """, (COLLECTION_NAME,))

    documents = cur.fetchall()
    total = len(documents)

    print(f"Found {total} documents to index")
    print("=" * 80)

    success_count = 0
    fail_count = 0

    for i, (doc_id, document_id, title, content) in enumerate(documents, 1):
        try:
            print(f"\n[{i}/{total}] {title}")
            print(f"   Content length: {len(content)} chars")

            # Generate embedding
            print(f"   Generating embedding...")
            embedding = generate_embedding(content)

            if not embedding:
                print(f"   ❌ Failed to generate embedding")
                fail_count += 1
                continue

            # Insert embedding into langchain_pg_embedding
            embedding_uuid = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO langchain_pg_embedding (id, collection_id, embedding, document, cmetadata)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (embedding_uuid, collection_uuid, embedding, content, psycopg2.extras.Json({
                'title': title,
                'document_id': document_id,
                'source': 'direct_manual_indexing'
            })))

            embedding_id = cur.fetchone()[0]
            print(f"   Created embedding ID: {embedding_id}")

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

            # Small delay to avoid overwhelming API
            if i % 10 == 0:
                import time
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
    print(f"Total documents processed: {total}")
    print(f"Successfully indexed: {success_count}")
    print(f"Failed: {fail_count}")
    if total > 0:
        print(f"Success rate: {(success_count/total*100):.1f}%")
    print("=" * 80)


if __name__ == "__main__":
    manual_index_all_documents()
