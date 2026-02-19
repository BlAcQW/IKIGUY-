#!/usr/bin/env python3
"""
Properly reindex broken cities by deleting old embeddings and creating new ones.
This uses the DocumentManagementService to ensure proper indexing.
"""

import os
import sys

# Set required environment variables
os.environ["MONGODB_URL"] = "mongodb://admin:aawwER444444@127.0.0.1:27017/kasaai_core?authSource=admin"
os.environ["POSTGRES_PASSWORD"] = "aawwER444444"
os.environ["GEMINI_API_KEY"] = "AIzaSyAACjmMMYIVH2Pq8Ns8KbOud-X8oCQMny4"

sys.path.insert(0, '/opt/kasaai')

from apps.core_backend.backend.services.document_management_service import DocumentManagementService
import psycopg2

# Target cities to reindex
TARGET_CITIES = [
    'TUDU', 'MAKOLA', 'ACCRA CENTRAL', 'DZORWULU',
    'AKWATIA', 'AKOSOMBO', 'SUHUM', 'KOKOMLEMLE',
    'AMANSAMAN', 'BOGOSO', 'MANKESSIM', 'ADABRAKA'
]

COLLECTION_NAME = "helpdesk_premier_health_production"


def get_db_connection():
    """Get PostgreSQL database connection."""
    return psycopg2.connect(
        host="127.0.0.1",
        database="kasaai_core",
        user="postgres",
        password=os.getenv("POSTGRES_PASSWORD")
    )


def reindex_cities():
    """Reindex target cities properly."""
    doc_service = DocumentManagementService()
    conn = get_db_connection()
    cur = conn.cursor()

    print("🔄 REINDEXING BROKEN CITIES")
    print("=" * 80)
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Target cities: {len(TARGET_CITIES)}")
    print("=" * 80)

    success_count = 0
    fail_count = 0

    for i, city in enumerate(TARGET_CITIES, 1):
        try:
            print(f"\n[{i}/{len(TARGET_CITIES)}] Processing {city}...")

            # Find documents for this city
            cur.execute("""
                SELECT document_id, title, content, company_name
                FROM kb_documents
                WHERE collection_name = %s
                AND title ILIKE %s
            """, (COLLECTION_NAME, f"%{city}%"))

            docs = cur.fetchall()

            if not docs:
                print(f"   ⚠️  No documents found for {city}")
                fail_count += 1
                continue

            for document_id, title, content, company_name in docs:
                print(f"   📄 {title}")
                print(f"      Document ID: {document_id}")
                print(f"      Content length: {len(content)} chars")

                try:
                    # Delete old embeddings for this document
                    print(f"      🗑️  Deleting old embeddings...")
                    doc_service.delete_document(
                        document_id=document_id,
                        collection_name=COLLECTION_NAME,
                        company_name=company_name
                    )

                    # Reindex with new content
                    print(f"      ✨ Creating new embeddings...")
                    doc_service.index_document(
                        document_id=document_id,
                        content=content,
                        collection_name=COLLECTION_NAME,
                        company_name=company_name,
                        metadata={
                            "title": title,
                            "source": "reindex_fix",
                            "city": city
                        }
                    )

                    print(f"      ✅ Reindexed successfully")
                    success_count += 1

                except Exception as e:
                    print(f"      ❌ Error reindexing: {e}")
                    fail_count += 1

        except Exception as e:
            print(f"   ❌ Error processing {city}: {e}")
            fail_count += 1

    cur.close()
    conn.close()

    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Successfully reindexed: {success_count}")
    print(f"Failed: {fail_count}")
    print("=" * 80)


if __name__ == "__main__":
    reindex_cities()
