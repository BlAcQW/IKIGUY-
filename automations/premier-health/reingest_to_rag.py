"""
Re-ingest Processed Premier Health Data into RAG Database

This script re-ingests the reprocessed Premier Health facility data
(now properly separated by individual cities) into the pgvector RAG database.

Usage:
    python reingest_to_rag.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add apps directory to path
sys.path.append('/opt/kasaai/apps')

# Import RAG service
from core_backend.backend.services.helpdesk_rag_service import HelpdeskRAGService


def reingest_data():
    """Re-ingest processed data into RAG database."""
    print("=" * 80)
    print("Premier Health RAG Database Re-ingestion")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Paths
    docs_dir = Path("/opt/kasaai/apps/automations/premier-health/processed_data/markdown_documents")

    if not docs_dir.exists():
        print(f"❌ Error: Documents directory not found: {docs_dir}")
        return False

    # Count documents
    markdown_files = list(docs_dir.glob("*.md"))
    print(f"📂 Found {len(markdown_files)} markdown documents to ingest")
    print()

    # Initialize RAG service
    print("🔧 Initializing RAG service...")
    try:
        rag_service = HelpdeskRAGService()
        print("✅ RAG service initialized")
    except Exception as e:
        print(f"❌ Failed to initialize RAG service: {e}")
        return False
    print()

    # Company name
    company_name = "premier_health_production"

    # Clear existing collection
    print(f"🗑️  Clearing existing collection: {company_name}")
    try:
        # This will remove all existing documents
        collection_name = f"helpdesk_{company_name}"

        # Import postgres utilities
        from core_backend.backend.config.postgres_config import get_postgres_connection

        conn = get_postgres_connection()
        cursor = conn.cursor()

        # Get collection UUID
        cursor.execute("""
            SELECT uuid FROM langchain_pg_collection
            WHERE name = %s
        """, (collection_name,))

        result = cursor.fetchone()
        if result:
            collection_uuid = result[0]

            # Delete all embeddings for this collection
            cursor.execute("""
                DELETE FROM langchain_pg_embedding
                WHERE collection_id = %s
            """, (collection_uuid,))

            deleted_count = cursor.rowcount
            conn.commit()

            print(f"✅ Deleted {deleted_count} existing embeddings")
        else:
            print("ℹ️  Collection doesn't exist yet - will be created")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"⚠️  Warning: Could not clear collection: {e}")
        print("   Continuing with ingestion...")
    print()

    # Read all markdown documents
    print("📖 Reading markdown documents...")
    documents = []
    for md_file in markdown_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract location from filename
            location = md_file.stem.replace('_', ' ')

            documents.append({
                "content": content,
                "location": location,
                "source_file": md_file.name
            })
        except Exception as e:
            print(f"⚠️  Failed to read {md_file.name}: {e}")

    print(f"✅ Read {len(documents)} documents")
    print()

    # Ingest documents
    print("💾 Ingesting documents into RAG database...")
    try:
        # Prepare documents for ingestion
        doc_texts = [doc["content"] for doc in documents]

        # Use the ingest_documents method
        result = rag_service.ingest_documents(
            company_name=company_name,
            documents=doc_texts,
            metadata_list=None  # Metadata is already in the markdown
        )

        if result.get("success"):
            print(f"✅ Successfully ingested {result.get('documents_processed', 0)} documents")
            print(f"   Processing time: {result.get('processing_time_seconds', 0):.2f}s")
        else:
            print(f"❌ Ingestion failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ Ingestion error: {e}")
        import traceback
        traceback.print_exc()
        return False
    print()

    # Verify ingestion
    print("🔍 Verifying ingestion...")
    try:
        conn = get_postgres_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM langchain_pg_embedding
            WHERE collection_id = (
                SELECT uuid FROM langchain_pg_collection
                WHERE name = %s
            )
        """, (f"helpdesk_{company_name}",))

        count = cursor.fetchone()[0]
        print(f"✅ Database now contains {count} document chunks")

        # Test query
        print()
        print("🧪 Test query: 'gynecologists in SANTASI'")
        test_result = rag_service.query(
            company_name=company_name,
            query="gynecologists in SANTASI"
        )

        if test_result.get("success"):
            response = test_result.get("response", "")
            print(f"✅ Test query successful")
            print(f"   Response length: {len(response)} characters")
            print(f"   Confidence: {test_result.get('confidence_score', 0)}")
            print(f"   Response preview: {response[:200]}...")
        else:
            print(f"⚠️  Test query returned no results")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"⚠️  Verification warning: {e}")
    print()

    print("=" * 80)
    print("✅ RE-INGESTION COMPLETE!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  - Documents processed: {len(documents)}")
    print(f"  - Company: {company_name}")
    print(f"  - Collection: helpdesk_{company_name}")
    print()
    print("Next steps:")
    print("  1. Test queries with actual calls")
    print("  2. Update Deepgram keywords")
    print("  3. Update CityNormalizer mappings")
    print("=" * 80)

    return True


if __name__ == "__main__":
    success = reingest_data()
    sys.exit(0 if success else 1)
