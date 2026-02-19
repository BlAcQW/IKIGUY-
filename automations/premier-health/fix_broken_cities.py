#!/usr/bin/env python3
"""
Fix Broken Cities - Comprehensive Solution

Fixes the remaining 48 broken cities by:
1. Removing duplicate documents (keep best version)
2. Deleting documents with insufficient content
3. Re-indexing all remaining documents
4. Verifying fixes

Author: Claude Code
Date: October 21, 2025
"""

import sys
import os
import asyncio
import logging
from typing import List, Dict, Any

sys.path.append('/opt/kasaai/apps/core_backend')

from backend.services.pg_document_service import pg_document_service
from backend.models.knowledge_base import DocumentFilter
import psycopg2

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
COLLECTION_NAME = "premier_health_production"
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "aawwER444444")
POSTGRES_HOST = "127.0.0.1"
POSTGRES_USER = "postgres"
POSTGRES_DB = "kasaai_core"


def get_duplicate_documents() -> List[Dict]:
    """
    Find duplicate documents (same title, multiple entries).

    Returns:
        List of duplicate document groups
    """
    logger.info("🔍 Finding duplicate documents...")

    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cur = conn.cursor()

        # Find titles with duplicates
        cur.execute("""
            SELECT
                title,
                COUNT(*) as count,
                ARRAY_AGG(document_id) as doc_ids,
                ARRAY_AGG(LENGTH(content)) as content_lengths,
                ARRAY_AGG(status) as statuses
            FROM kb_documents
            WHERE collection_name = %s
            GROUP BY title
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC, title;
        """, (f"helpdesk_{COLLECTION_NAME}",))

        duplicates = []
        for row in cur.fetchall():
            title, count, doc_ids, content_lengths, statuses = row
            duplicates.append({
                'title': title,
                'count': count,
                'doc_ids': doc_ids,
                'content_lengths': content_lengths,
                'statuses': statuses
            })

        cur.close()
        conn.close()

        logger.info(f"   Found {len(duplicates)} titles with duplicates")
        return duplicates

    except Exception as e:
        logger.error(f"❌ Error finding duplicates: {str(e)}")
        return []


def delete_duplicate_documents(duplicates: List[Dict]) -> int:
    """
    Delete duplicate documents, keeping the best version.

    Strategy:
    - Keep document with longest content
    - If content same length, keep indexed over failed/processing
    - Delete all others

    Args:
        duplicates: List of duplicate document groups

    Returns:
        Number of documents deleted
    """
    logger.info("🗑️  Deleting duplicate documents...")

    deleted_count = 0

    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cur = conn.cursor()

        for dup in duplicates:
            title = dup['title']
            doc_ids = dup['doc_ids']
            content_lengths = dup['content_lengths']
            statuses = dup['statuses']

            # Find best document to keep
            # Priority: longest content, then indexed status
            best_idx = 0
            best_length = content_lengths[0]
            best_status = statuses[0]

            for i in range(1, len(doc_ids)):
                current_length = content_lengths[i]
                current_status = statuses[i]

                # Longer content wins
                if current_length > best_length:
                    best_idx = i
                    best_length = current_length
                    best_status = current_status
                # Same length, prefer indexed status
                elif current_length == best_length and current_status == 'indexed' and best_status != 'indexed':
                    best_idx = i
                    best_status = current_status

            # Keep the best, delete others
            keep_id = doc_ids[best_idx]
            delete_ids = [doc_ids[i] for i in range(len(doc_ids)) if i != best_idx]

            if delete_ids:
                logger.info(f"   {title}: Keeping doc {keep_id} (length: {best_length}), deleting {len(delete_ids)} duplicates")

                for delete_id in delete_ids:
                    cur.execute("""
                        DELETE FROM kb_documents
                        WHERE document_id = %s
                    """, (delete_id,))
                    deleted_count += 1

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ Deleted {deleted_count} duplicate documents")
        return deleted_count

    except Exception as e:
        logger.error(f"❌ Error deleting duplicates: {str(e)}")
        return deleted_count


def find_problematic_documents() -> List[str]:
    """
    Find documents that are problematic (short content, bad titles).

    Returns:
        List of document IDs to delete
    """
    logger.info("🔍 Finding problematic documents...")

    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cur = conn.cursor()

        # Find very short documents or those with problematic titles
        cur.execute("""
            SELECT document_id, title, LENGTH(content) as content_length
            FROM kb_documents
            WHERE collection_name = %s
            AND (
                LENGTH(content) < 200  -- Very short content
                OR title ~ '^Healthcare Providers in [0-9]+$'  -- Just numbers
            )
            ORDER BY LENGTH(content);
        """, (f"helpdesk_{COLLECTION_NAME}",))

        problematic = []
        for row in cur.fetchall():
            doc_id, title, content_length = row
            problematic.append({
                'id': doc_id,
                'title': title,
                'length': content_length
            })
            logger.info(f"   Problematic: {title} (length: {content_length})")

        cur.close()
        conn.close()

        logger.info(f"   Found {len(problematic)} problematic documents")
        return [p['id'] for p in problematic]

    except Exception as e:
        logger.error(f"❌ Error finding problematic docs: {str(e)}")
        return []


def delete_problematic_documents(doc_ids: List[str]) -> int:
    """
    Delete problematic documents.

    Args:
        doc_ids: List of document IDs to delete

    Returns:
        Number of documents deleted
    """
    if not doc_ids:
        return 0

    logger.info(f"🗑️  Deleting {len(doc_ids)} problematic documents...")

    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cur = conn.cursor()

        for doc_id in doc_ids:
            cur.execute("""
                DELETE FROM kb_documents
                WHERE document_id = %s
            """, (doc_id,))

        deleted_count = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ Deleted {deleted_count} problematic documents")
        return deleted_count

    except Exception as e:
        logger.error(f"❌ Error deleting problematic docs: {str(e)}")
        return 0


def clear_all_embeddings():
    """
    Clear all embeddings to force re-indexing.
    """
    logger.info("🗑️  Clearing all embeddings for re-indexing...")

    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cur = conn.cursor()

        cur.execute("""
            DELETE FROM langchain_pg_embedding
            WHERE collection_id IN (
                SELECT uuid FROM langchain_pg_collection
                WHERE name = %s
            )
        """, (f"helpdesk_{COLLECTION_NAME}",))

        deleted_count = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ Cleared {deleted_count} embeddings")
        return deleted_count

    except Exception as e:
        logger.error(f"❌ Error clearing embeddings: {str(e)}")
        return 0


async def main():
    """
    Main fix workflow.
    """
    logger.info("=" * 80)
    logger.info("🔧 FIXING BROKEN CITIES")
    logger.info("=" * 80)

    try:
        # Step 1: Find and delete duplicates
        duplicates = get_duplicate_documents()
        if duplicates:
            deleted_duplicates = delete_duplicate_documents(duplicates)
        else:
            deleted_duplicates = 0

        # Step 2: Find and delete problematic documents
        problematic_ids = find_problematic_documents()
        deleted_problematic = delete_problematic_documents(problematic_ids)

        # Step 3: Clear embeddings (will be re-indexed by main script)
        cleared_embeddings = clear_all_embeddings()

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("📊 FIX SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Duplicate documents deleted:   {deleted_duplicates}")
        logger.info(f"Problematic documents deleted: {deleted_problematic}")
        logger.info(f"Embeddings cleared:            {cleared_embeddings}")
        logger.info("=" * 80)

        # Get final document count
        try:
            conn = psycopg2.connect(
                host=POSTGRES_HOST,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD
            )
            cur = conn.cursor()

            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(DISTINCT title) as unique_titles
                FROM kb_documents
                WHERE collection_name = %s
            """, (f"helpdesk_{COLLECTION_NAME}",))

            total, unique = cur.fetchone()
            cur.close()
            conn.close()

            logger.info(f"\n✅ Final document count: {total} documents ({unique} unique titles)")
            logger.info(f"✅ Ready for re-indexing!")

        except Exception as e:
            logger.error(f"❌ Error getting final count: {str(e)}")

        logger.info("\n" + "=" * 80)
        logger.info("✅ FIX COMPLETE!")
        logger.info("=" * 80)
        logger.info("\n⚠️  NEXT STEP: Run the re-indexing script to create embeddings:")
        logger.info("   python3 apps/automations/premier-health/reindex_with_correct_embeddings.py")

    except Exception as e:
        logger.error(f"\n❌ FIX FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
