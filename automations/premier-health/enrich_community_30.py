#!/usr/bin/env python3
"""
Enrich Community 30 Content and Re-embed

This script enriches the sparse Community 30 document with more descriptive
content to improve vector search recall, then re-generates embeddings.

Author: Claude Code
Date: October 30, 2025
"""

import os
import sys
import asyncio
from typing import Optional

# Add project root to path
sys.path.insert(0, '/opt/kasaai')

import psycopg2
from psycopg2.extras import RealDictCursor
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector
from langchain_core.documents import Document


# Database configuration
DB_CONFIG = {
    "host": "127.0.0.1",
    "database": "kasaai_core",
    "user": "postgres",
    "password": os.getenv("POSTGRES_PASSWORD", "aawwER444444")
}

COLLECTION_NAME = "helpdesk_premier_health_production"
DOCUMENT_ID = 1877  # Community 30 document ID


def get_enriched_content() -> str:
    """
    Create enriched content for Community 30 with more descriptive text
    to improve vector embedding quality.

    Returns:
        Enriched markdown content
    """
    return """# Healthcare Providers in TEMA COMMUNITY 30

This document lists all Premier Health Insurance network providers in TEMA COMMUNITY 30, Ghana.

## TEMA COMMUNITY 30
**Region**: GREATER ACCRA
**Area**: TEMA COMMUNITY 30 is a residential area in Tema, Greater Accra Region, located along the Official Town Road. It is one of the numbered communities in the Tema metropolitan area.

**Alternative Names**: Community 30, TEMA COMM 30, TEMA COMMUNITY THIRTY

---

## LENA PHARMACY
**Specialties**: PHARMACY
**Services**: Retail pharmacy services, prescription medications, over-the-counter medicines, pharmaceutical care
**Phone**: Contact through Premier Health hotline for updated contact information
**Location**: OFFICIAL TOWN ROAD, TEMA COMMUNITY 30
**Region**: GREATER ACCRA

**About**: LENA PHARMACY is a retail pharmacy provider serving residents of Community 30 and surrounding areas. The pharmacy provides prescription dispensing, pharmaceutical consultations, and general pharmacy services for Premier Health Insurance members.

**Access**: Located on Official Town Road in Community 30, easily accessible to residents seeking pharmaceutical services and medications in the Tema Community 30 area.

---

## Summary
TEMA COMMUNITY 30 currently has 1 Premier Health Insurance network provider:
- 1 Pharmacy (LENA PHARMACY on Official Town Road)

Residents of Community 30 seeking healthcare services can visit LENA PHARMACY for pharmaceutical needs, or contact nearby communities (Community 28, 31, 33, 35) for additional medical services.
"""


def update_document_content(enriched_content: str) -> bool:
    """
    Update the Community 30 document in the database with enriched content.

    Args:
        enriched_content: The enriched markdown content

    Returns:
        True if successful, False otherwise
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Update the document content
        update_query = """
        UPDATE kb_documents
        SET content = %s,
            updated_at = NOW()
        WHERE id = %s
        AND collection_name = %s
        """

        cursor.execute(update_query, (enriched_content, DOCUMENT_ID, COLLECTION_NAME))
        conn.commit()

        rows_updated = cursor.rowcount
        cursor.close()
        conn.close()

        print(f"✅ Updated document {DOCUMENT_ID} - {rows_updated} rows affected")
        return rows_updated > 0

    except Exception as e:
        print(f"❌ Error updating document: {e}")
        return False


def delete_existing_embeddings() -> int:
    """
    Delete existing embeddings for Community 30 document.

    Returns:
        Number of embeddings deleted
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Delete embeddings with Community 30 in title
        delete_query = """
        DELETE FROM langchain_pg_embedding
        WHERE cmetadata->>'title' = 'Healthcare Providers in TEMA COMMUNITY 30'
        AND collection_id = (
            SELECT uuid FROM langchain_pg_collection
            WHERE name = %s
        )
        """

        cursor.execute(delete_query, (COLLECTION_NAME,))
        conn.commit()

        rows_deleted = cursor.rowcount
        cursor.close()
        conn.close()

        print(f"✅ Deleted {rows_deleted} existing embeddings for Community 30")
        return rows_deleted

    except Exception as e:
        print(f"❌ Error deleting embeddings: {e}")
        return 0


def regenerate_embeddings() -> bool:
    """
    Re-generate embeddings for the enriched Community 30 document.

    Returns:
        True if successful, False otherwise
    """
    try:
        # Get Gemini API key
        gemini_api_key = os.getenv("GEMINI_API_KEY", "AIzaSyAACjmMMYIVH2Pq8Ns8KbOud-X8oCQMny4")

        # Initialize embeddings
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=gemini_api_key,
            task_type="retrieval_document"
        )

        # Initialize vector store
        connection_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"

        vector_store = PGVector(
            embeddings=embeddings,
            collection_name=COLLECTION_NAME,
            connection=connection_string,
            use_jsonb=True,
        )

        # Get enriched content from database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            "SELECT title, content FROM kb_documents WHERE id = %s",
            (DOCUMENT_ID,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            print(f"❌ Document {DOCUMENT_ID} not found")
            return False

        # Create document object
        doc = Document(
            page_content=row['content'],
            metadata={
                "title": row['title'],
                "source": "premier_health_kb",
                "document_id": DOCUMENT_ID
            }
        )

        # Add to vector store (will chunk and embed) - use synchronous method
        print(f"🔄 Generating embeddings for enriched Community 30 content...")
        ids = vector_store.add_documents([doc])

        print(f"✅ Generated {len(ids)} embeddings for Community 30")
        return True

    except Exception as e:
        print(f"❌ Error regenerating embeddings: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main enrichment workflow"""
    print("=" * 80)
    print("Community 30 Content Enrichment & Re-embedding")
    print("=" * 80)
    print()

    # Step 1: Create enriched content
    print("📝 Step 1: Creating enriched content...")
    enriched_content = get_enriched_content()
    print(f"   Original length: ~318 characters")
    print(f"   Enriched length: {len(enriched_content)} characters")
    print(f"   Increase: +{len(enriched_content) - 318} characters ({((len(enriched_content) - 318) / 318 * 100):.1f}%)")
    print()

    # Step 2: Update document in database
    print("💾 Step 2: Updating document in database...")
    if not update_document_content(enriched_content):
        print("❌ Failed to update document")
        return 1
    print()

    # Step 3: Delete existing embeddings
    print("🗑️  Step 3: Deleting existing embeddings...")
    deleted_count = delete_existing_embeddings()
    print()

    # Step 4: Regenerate embeddings
    print("🔄 Step 4: Regenerating embeddings...")
    if not regenerate_embeddings():
        print("❌ Failed to regenerate embeddings")
        return 1
    print()

    # Step 5: Verify
    print("✅ Step 5: Verifying new embeddings...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM langchain_pg_embedding
            WHERE cmetadata->>'title' = 'Healthcare Providers in TEMA COMMUNITY 30'
        """)
        new_count = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        print(f"   Old embeddings: {deleted_count}")
        print(f"   New embeddings: {new_count}")
        print(f"   Change: {'+' if new_count >= deleted_count else ''}{new_count - deleted_count}")
        print()

    except Exception as e:
        print(f"⚠️  Could not verify embeddings: {e}")
        print()

    print("=" * 80)
    print("✅ Community 30 enrichment complete!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Clear Redis cache: redis-cli --user inspireadmin --pass aawwER444444 FLUSHDB")
    print("2. Test query: curl -X POST 'https://api.ailabsafrica.com/knowledge-base/premier_health_production/query' -H 'Content-Type: application/json' -d '{\"query\": \"providers in community 30\"}'")
    print()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
