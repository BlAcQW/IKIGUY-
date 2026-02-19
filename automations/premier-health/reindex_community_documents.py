#!/usr/bin/env python3
"""
Re-index Community Documents to Regenerate Embeddings

This script triggers re-indexing for all community documents to regenerate
embeddings after content updates.

Author: Claude Code
Date: October 28, 2025
"""

import sys
import os
import asyncio
import logging

# Set required environment variables BEFORE importing services
os.environ["MONGODB_URL"] = "mongodb://admin:aawwER444444@127.0.0.1:27017/kasaai_core?authSource=admin"
os.environ["POSTGRES_PASSWORD"] = "aawwER444444"
os.environ["GEMINI_API_KEY"] = "AIzaSyAACjmMMYIVH2Pq8Ns8KbOud-X8oCQMny4"

# Add paths
sys.path.append('/opt/kasaai/apps/core_backend')

from backend.services.pg_document_service import pg_document_service
from backend.models.knowledge_base import DocumentUpdate

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

COLLECTION_NAME = "premier_health_production"


async def reindex_all_communities():
    """
    Re-index all community documents to regenerate embeddings.
    """
    print("=" * 80)
    print("RE-INDEX COMMUNITY DOCUMENTS")
    print("=" * 80)
    print(f"Collection: helpdesk_{COLLECTION_NAME}")
    print("Regenerating embeddings for all TEMA COMMUNITY documents")
    print("=" * 80)
    print()

    try:
        # Get all community documents
        print("📚 Fetching all community documents...")

        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(
            host="127.0.0.1",
            port=5432,
            user="postgres",
            password=os.getenv("POSTGRES_PASSWORD"),
            database="kasaai_core"
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = f"""
            SELECT document_id, title, content, company_name
            FROM kb_documents
            WHERE collection_name = 'helpdesk_{COLLECTION_NAME}'
              AND title LIKE 'Healthcare Providers in TEMA COMMUNITY%'
            ORDER BY title
        """
        cursor.execute(query)

        documents = cursor.fetchall()
        cursor.close()
        conn.close()

        print(f"   Found {len(documents)} community documents")
        print()

        # Re-index each document by doing a "no-op" content update
        # This triggers the re-indexing logic in update_document
        print("🔄 Re-indexing documents (regenerating embeddings):")
        print("-" * 80)

        success_count = 0
        error_count = 0

        for doc in documents:
            doc_id = doc['document_id']
            title = doc['title']
            content = doc['content']

            print(f"\n   📄 {title}")

            try:
                # Update document with same content to trigger re-indexing
                doc_update = DocumentUpdate(content=content)

                result = await pg_document_service.update_document(
                    document_id=doc_id,
                    doc_update=doc_update
                )

                if result.success:
                    print(f"      ✅ Re-indexed successfully")
                    success_count += 1
                    # Small delay to avoid overwhelming the system
                    await asyncio.sleep(0.5)
                else:
                    print(f"      ❌ Failed: {result.message}")
                    error_count += 1

            except Exception as e:
                print(f"      ❌ Error: {e}")
                error_count += 1

        print()
        print("=" * 80)
        print(f"✅ RE-INDEXING COMPLETE")
        print(f"   Success: {success_count}")
        print(f"   Errors: {error_count}")
        print("=" * 80)
        print()
        print("⏳ Embeddings are being regenerated in the background...")
        print("   Please wait 30-60 seconds before testing queries.")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(reindex_all_communities())
