#!/usr/bin/env python3
"""
Manually complete indexing for all documents in helpdesk_helpdesk_premier_health_production.
This script:
1. Finds all documents with status='processing' and no vector_ids
2. Generates embeddings using the existing DocumentManagementService
3. Updates documents with vector_ids and status='indexed'
"""

import os
import sys
import asyncio

# Set required environment variables BEFORE importing services
os.environ["MONGODB_URL"] = "mongodb://admin:aawwER444444%25@127.0.0.1:27017/kasaai_core?authSource=admin"
os.environ["POSTGRES_PASSWORD"] = "aawwER444444"
os.environ["GEMINI_API_KEY"] = "AIzaSyAACjmMMYIVH2Pq8Ns8KbOud-X8oCQMny4"

# Add paths
sys.path.insert(0, '/opt/kasaai')
sys.path.insert(0, '/opt/kasaai/apps/core_backend')

from apps.core_backend.backend.services.document_management_service import DocumentManagementService
import psycopg2

COLLECTION_NAME = "helpdesk_helpdesk_premier_health_production"
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")


def get_db_connection():
    """Get PostgreSQL database connection."""
    return psycopg2.connect(
        host="127.0.0.1",
        database="kasaai_core",
        user="postgres",
        password=POSTGRES_PASSWORD
    )


async def manually_index_documents():
    """Manually index all pending documents."""
    print("🔧 MANUAL DOCUMENT INDEXING")
    print("=" * 80)

    # Initialize document management service
    doc_service = DocumentManagementService()

    # Get database connection
    conn = get_db_connection()
    cur = conn.cursor()

    # Find all documents that need indexing
    cur.execute("""
        SELECT id, document_id, title, content, company_name
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

    for i, (doc_id, document_id, title, content, company_name) in enumerate(documents, 1):
        try:
            print(f"\n[{i}/{total}] {title}")
            print(f"   Document ID: {document_id}")
            print(f"   Content length: {len(content)} chars")

            # Create a document object
            from backend.models.knowledge_base import KnowledgeDocument
            from datetime import datetime

            doc = KnowledgeDocument(
                id=str(doc_id),
                document_id=document_id,
                company_name=company_name,
                collection_name=COLLECTION_NAME,
                title=title,
                content=content,
                content_hash="",
                category="healthcare_providers",
                tags=[],
                status="processing",
                source="manual_reindex",
                source_uri=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                indexed_at=None,
                metadata={},
                vector_ids=[],
                is_active=True,
                is_archived=False,
                current_version=1,
                created_by=None,
                updated_by=None
            )

            # Index the document using the service
            await doc_service._index_document_async(doc)

            print(f"   ✅ Successfully indexed")
            success_count += 1

            # Small delay to avoid overwhelming the API
            if i % 10 == 0:
                await asyncio.sleep(1)

        except Exception as e:
            print(f"   ❌ Error: {e}")
            fail_count += 1

    cur.close()
    conn.close()

    print("\n" + "=" * 80)
    print("📊 INDEXING SUMMARY")
    print("=" * 80)
    print(f"Total documents: {total}")
    print(f"Successfully indexed: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Success rate: {(success_count/total*100):.1f}%")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(manually_index_documents())
