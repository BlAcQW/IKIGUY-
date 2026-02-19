#!/usr/bin/env python3
"""
Re-index Premier Health documents with correct embedding model (text-embedding-004).

Problem: Documents were indexed with embedding-001, but queries use text-embedding-004.
Solution: Delete old embeddings and re-index with text-embedding-004.

Author: Claude Code
Date: October 21, 2025
"""

import sys
import os
import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime

# Add paths
sys.path.append('/opt/kasaai/apps/core_backend')

from backend.services.pg_document_service import pg_document_service
from backend.models.knowledge_base import DocumentFilter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import psycopg2

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
COLLECTION_NAME = "helpdesk_premier_health_production"
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "aawwER444444")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAACjmMMYIVH2Pq8Ns8KbOud-X8oCQMny4")
POSTGRES_HOST = "127.0.0.1"
POSTGRES_USER = "postgres"
POSTGRES_DB = "kasaai_core"

CONNECTION_STRING = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}"


async def get_all_documents() -> List[Dict]:
    """
    Fetch all Premier Health documents from kb_documents table.

    Returns:
        List of document dictionaries
    """
    logger.info("📥 Fetching all documents from database...")

    documents = []
    page = 1
    page_size = 100

    while True:
        filter_params = DocumentFilter(
            company_name="premier_health_production",
            page=page,
            page_size=page_size
        )

        result = await pg_document_service.list_documents(filter_params)

        if not result.success:
            logger.error(f"❌ Failed to fetch documents: {result.error}")
            break

        if not result.documents or len(result.documents) == 0:
            break

        for doc in result.documents:
            doc_dict = doc if isinstance(doc, dict) else doc.dict()
            documents.append(doc_dict)

        logger.info(f"   Fetched page {page}: {len(result.documents)} documents")

        if len(result.documents) < page_size:
            break

        page += 1

    logger.info(f"✅ Total documents fetched: {len(documents)}")
    return documents


def backup_old_embeddings():
    """
    Create backup of old embeddings (optional safety measure).
    """
    logger.info("💾 Creating backup of old embeddings...")

    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cur = conn.cursor()

        # Get count of embeddings to backup
        cur.execute("""
            SELECT COUNT(*)
            FROM langchain_pg_embedding e
            JOIN langchain_pg_collection c ON e.collection_id = c.uuid
            WHERE c.name = %s
        """, (COLLECTION_NAME,))

        count = cur.fetchone()[0]
        logger.info(f"   Found {count} embeddings to backup")

        # Create backup table
        backup_table = f"langchain_pg_embedding_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        cur.execute(f"""
            CREATE TABLE {backup_table} AS
            SELECT e.*
            FROM langchain_pg_embedding e
            JOIN langchain_pg_collection c ON e.collection_id = c.uuid
            WHERE c.name = %s
        """, (COLLECTION_NAME,))

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ Backup created: {backup_table}")
        return backup_table

    except Exception as e:
        logger.error(f"❌ Backup failed: {str(e)}")
        return None


def delete_old_embeddings():
    """
    Delete old embeddings with wrong embedding model.
    """
    logger.info("🗑️  Deleting old embeddings (embedding-001)...")

    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cur = conn.cursor()

        # Delete embeddings for this collection
        cur.execute("""
            DELETE FROM langchain_pg_embedding
            WHERE collection_id IN (
                SELECT uuid FROM langchain_pg_collection
                WHERE name = %s
            )
        """, (COLLECTION_NAME,))

        deleted_count = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ Deleted {deleted_count} old embeddings")
        return deleted_count

    except Exception as e:
        logger.error(f"❌ Failed to delete embeddings: {str(e)}")
        raise


async def reindex_documents(documents: List[Dict]):
    """
    Re-index documents with text-embedding-004 model.

    Args:
        documents: List of document dictionaries to index
    """
    logger.info("🔄 Re-indexing documents with text-embedding-004...")

    # Initialize embeddings with CORRECT model
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=GEMINI_API_KEY
    )

    logger.info("✅ Using text-embedding-004 model")

    # Initialize text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )

    # Initialize PGVector
    vectorstore = PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
        use_jsonb=True,
        pre_delete_collection=False
    )

    # Convert to LangChain documents and add to vector store
    langchain_docs = []

    for doc in documents:
        # Split content into chunks
        text_chunks = text_splitter.split_text(doc['content'])

        for i, chunk in enumerate(text_chunks):
            langchain_doc = Document(
                page_content=chunk,
                metadata={
                    "title": doc['title'],
                    "doc_id": doc.get('document_id', ''),
                    "category": doc.get('category', ''),
                    "source": doc.get('source', ''),
                    "company": "premier_health_production",
                    "tags": doc.get('tags', []),
                    "chunk_index": i,
                    "total_chunks": len(text_chunks)
                }
            )
            langchain_docs.append(langchain_doc)

    logger.info(f"   Prepared {len(langchain_docs)} chunks from {len(documents)} documents")

    # Add documents to vector store in batches
    batch_size = 50
    total_batches = (len(langchain_docs) + batch_size - 1) // batch_size

    for i in range(0, len(langchain_docs), batch_size):
        batch = langchain_docs[i:i+batch_size]
        batch_num = (i // batch_size) + 1

        logger.info(f"   Indexing batch {batch_num}/{total_batches} ({len(batch)} chunks)...")

        try:
            vectorstore.add_documents(batch)
        except Exception as e:
            logger.error(f"❌ Failed to index batch {batch_num}: {str(e)}")
            raise

    logger.info(f"✅ Successfully re-indexed {len(langchain_docs)} chunks")
    return len(langchain_docs)


async def verify_reindexing():
    """
    Verify that re-indexing was successful.
    """
    logger.info("🔍 Verifying re-indexing...")

    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cur = conn.cursor()

        # Count embeddings
        cur.execute("""
            SELECT COUNT(*)
            FROM langchain_pg_embedding e
            JOIN langchain_pg_collection c ON e.collection_id = c.uuid
            WHERE c.name = %s
        """, (COLLECTION_NAME,))

        new_count = cur.fetchone()[0]

        # Check unique titles
        cur.execute("""
            SELECT COUNT(DISTINCT cmetadata->>'title')
            FROM langchain_pg_embedding e
            JOIN langchain_pg_collection c ON e.collection_id = c.uuid
            WHERE c.name = %s
        """, (COLLECTION_NAME,))

        unique_titles = cur.fetchone()[0]

        cur.close()
        conn.close()

        logger.info(f"✅ Verification complete:")
        logger.info(f"   - Total embeddings: {new_count}")
        logger.info(f"   - Unique documents: {unique_titles}")

        return new_count, unique_titles

    except Exception as e:
        logger.error(f"❌ Verification failed: {str(e)}")
        return 0, 0


async def test_sample_queries():
    """
    Test sample queries to verify embeddings work correctly.
    """
    logger.info("🧪 Testing sample queries...")

    # Initialize embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=GEMINI_API_KEY
    )

    # Initialize vector store
    vectorstore = PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
        use_jsonb=True,
    )

    # Test queries
    test_queries = [
        "healthcare providers in KOKOMLEMLE",
        "healthcare providers in MAKOLA",
        "healthcare providers in NIMA",
        "healthcare providers in MAAMOBI"
    ]

    for query in test_queries:
        logger.info(f"\n   Query: '{query}'")
        results = vectorstore.similarity_search_with_score(query, k=3)

        for i, (doc, score) in enumerate(results, 1):
            title = doc.metadata.get('title', 'N/A')
            # Lower score = more similar for distance metrics
            logger.info(f"      {i}. {title} (score: {score:.4f})")


async def main():
    """
    Main re-indexing workflow.
    """
    logger.info("=" * 80)
    logger.info("🚀 PREMIER HEALTH RE-INDEXING WITH CORRECT EMBEDDINGS")
    logger.info("=" * 80)
    logger.info(f"Collection: {COLLECTION_NAME}")
    logger.info(f"Embedding Model: text-embedding-004 (CORRECT)")
    logger.info(f"Old Model: embedding-001 (WRONG - being replaced)")
    logger.info("=" * 80)

    try:
        # Step 1: Get all documents
        documents = await get_all_documents()

        if not documents:
            logger.error("❌ No documents found. Aborting.")
            return

        # Step 2: Backup old embeddings
        backup_table = backup_old_embeddings()

        # Step 3: Delete old embeddings
        deleted_count = delete_old_embeddings()

        # Step 4: Re-index with correct model
        indexed_count = await reindex_documents(documents)

        # Step 5: Verify
        new_count, unique_titles = await verify_reindexing()

        # Step 6: Test queries
        await test_sample_queries()

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("📊 RE-INDEXING SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Documents processed:     {len(documents)}")
        logger.info(f"Old embeddings deleted:  {deleted_count}")
        logger.info(f"New embeddings created:  {new_count}")
        logger.info(f"Unique documents:        {unique_titles}")
        if backup_table:
            logger.info(f"Backup table:            {backup_table}")
        logger.info("=" * 80)
        logger.info("✅ RE-INDEXING COMPLETE!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"\n❌ RE-INDEXING FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
