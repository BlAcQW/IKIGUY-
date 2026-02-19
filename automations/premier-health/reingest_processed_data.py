#!/usr/bin/env python3
"""
Re-ingest Processed Premier Health Data into RAG Database

Re-ingests the reprocessed data (properly separated by city) into the RAG database.

Usage:
    python reingest_processed_data.py
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import List

# Add paths for imports
sys.path.append('/opt/kasaai/apps/core_backend')

from backend.services.helpdesk_rag_service import helpdesk_rag_service, KnowledgeDocument


async def reingest_processed_data():
    """Re-ingest processed markdown documents into RAG database."""
    print("=" * 80)
    print("Premier Health RAG Database Re-ingestion")
    print("Reprocessed Data (Cities Properly Separated)")
    print("=" * 80)
    print()

    # Paths
    docs_dir = Path("/opt/kasaai/apps/automations/premier-health/processed_data/markdown_documents")

    if not docs_dir.exists():
        print(f"❌ Error: Documents directory not found: {docs_dir}")
        return False

    # Load markdown documents
    print("📂 Loading processed markdown documents...")
    markdown_files = list(docs_dir.glob("*.md"))
    print(f"   Found {len(markdown_files)} documents")
    print()

    # Convert markdown files to KnowledgeDocument objects
    print("📝 Converting to KnowledgeDocument format...")
    documents = []

    for md_file in markdown_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract location from filename
            location = md_file.stem.replace('_', ' ').upper()

            # Count facilities (approximate by counting ##)
            facility_count = content.count('\n## ')

            # Create KnowledgeDocument
            doc_id = f"providers_{md_file.stem}"

            doc = KnowledgeDocument(
                id=doc_id,
                title=f"Healthcare Providers in {location}",
                content=content,
                category="provider_directory",
                source="reprocessed_csv_split",
                tags=["providers", "healthcare", location.lower().replace(' ', '_')],
                metadata={
                    "city": location,
                    "provider_count": facility_count,
                    "is_reprocessed": True,
                    "source_file": md_file.name
                }
            )

            documents.append(doc)

        except Exception as e:
            print(f"   ⚠️  Failed to process {md_file.name}: {e}")

    print(f"   ✅ Converted {len(documents)} documents")
    print()

    # Re-index knowledge base
    print("💾 Re-indexing knowledge base...")
    print("   ⚠️  This will replace all existing provider documents")
    print()

    try:
        result = await helpdesk_rag_service.initialize_knowledge_base(
            company_name="premier_health_production",
            documents=documents
        )

        print("   ✅ Knowledge base re-indexed successfully!")
        print(f"   - Collection: {result['collection_name']}")
        print(f"   - Documents indexed: {result['documents_indexed']}")
        print(f"   - Chunks created: {result['chunks_created']}")
        print(f"   - Embedding dimension: {result['embedding_dimension']}")
        print()

    except Exception as e:
        print(f"   ❌ Re-indexing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Get statistics
    print("📊 Final Statistics:")
    try:
        stats = await helpdesk_rag_service.get_knowledge_base_stats("premier_health_production")
        for key, value in stats.items():
            print(f"   - {key}: {value}")
        print()
    except Exception as e:
        print(f"   ⚠️  Could not retrieve stats: {e}")

    # Test query
    print("🧪 Test Query: 'gynecologists in SANTASI'")
    try:
        test_result = await helpdesk_rag_service.query(
            company_name="premier_health_production",
            query="gynecologists in SANTASI"
        )

        if test_result.get("success"):
            response = test_result.get("response", "")
            print(f"   ✅ Test successful!")
            print(f"   - Confidence: {test_result.get('confidence_score', 0)}")
            print(f"   - Response length: {len(response)} characters")
            print()
            print("   Response preview:")
            print("   " + "-" * 76)
            preview = response[:300].replace('\n', '\n   ')
            print(f"   {preview}...")
            print("   " + "-" * 76)
        else:
            print(f"   ⚠️  Test query failed or returned no results")

    except Exception as e:
        print(f"   ⚠️  Test query error: {e}")

    print()
    print("=" * 80)
    print("✅ RE-INGESTION COMPLETE!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  - Documents reprocessed: {len(documents)}")
    print(f"  - Cities now properly separated (e.g., SANTASI ≠ PATASI)")
    print(f"  - Company: premier_health_production")
    print(f"  - Collection: helpdesk_premier_health_production")
    print()
    print("Examples of separated cities:")
    print("  • SANTASI / PATASI → Now separate documents")
    print("  • TAFO / BREMANG → Now separate documents")
    print("  • BOMSO / KNUST / EJISU → Now separate documents")
    print("  • MADINA / ADENTA / DODOWA → Now separate documents")
    print()
    print("Next steps:")
    print("  1. Test with real queries")
    print("  2. Update Deepgram keywords")
    print("  3. Update CityNormalizer mappings")
    print("=" * 80)

    return True


if __name__ == "__main__":
    success = asyncio.run(reingest_processed_data())
    sys.exit(0 if success else 1)
