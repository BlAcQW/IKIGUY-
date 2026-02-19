#!/usr/bin/env python3
"""
Clean up duplicate documents and optimize the database.
This script:
1. Removes duplicate documents (keeps newest version)
2. Deletes orphaned embeddings
3. Provides statistics
"""

import psycopg2
from collections import defaultdict

POSTGRES_PASSWORD = "aawwER444444"
COLLECTION_NAME = "helpdesk_premier_health_production"


def get_db_connection():
    """Get PostgreSQL database connection."""
    return psycopg2.connect(
        host="127.0.0.1",
        database="kasaai_core",
        user="postgres",
        password=POSTGRES_PASSWORD
    )


def cleanup_duplicates():
    """Remove duplicate documents, keeping only the newest version."""
    print("🧹 CLEANING UP DUPLICATE DOCUMENTS")
    print("=" * 80)

    conn = get_db_connection()
    cur = conn.cursor()

    # Find duplicates (documents with same title)
    cur.execute("""
        SELECT
            title,
            COUNT(*) as count,
            array_agg(id ORDER BY created_at DESC) as ids,
            array_agg(created_at ORDER BY created_at DESC) as dates
        FROM kb_documents
        WHERE collection_name = %s
        GROUP BY title
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    """, (COLLECTION_NAME,))

    duplicates = cur.fetchall()

    print(f"\n📊 Found {len(duplicates)} titles with duplicates:")
    print("=" * 80)

    total_deleted_docs = 0
    total_deleted_embeddings = 0

    for title, count, ids, dates in duplicates:
        print(f"\n{title}: {count} copies")
        print(f"   Keeping ID {ids[0]} (created: {dates[0]})")
        print(f"   Deleting {count - 1} older copies...")

        # Keep the first (newest), delete the rest
        ids_to_delete = ids[1:]

        for doc_id in ids_to_delete:
            # Get vector_ids to delete embeddings
            cur.execute("""
                SELECT vector_ids FROM kb_documents
                WHERE id = %s
            """, (doc_id,))

            result = cur.fetchone()
            if result and result[0]:
                vector_ids = result[0]

                # Delete embeddings
                cur.execute("""
                    DELETE FROM langchain_pg_embedding
                    WHERE id = ANY(%s)
                """, (vector_ids,))

                deleted_emb = cur.rowcount
                total_deleted_embeddings += deleted_emb
                print(f"      Deleted {deleted_emb} embeddings for doc ID {doc_id}")

            # Delete document
            cur.execute("""
                DELETE FROM kb_documents
                WHERE id = %s
            """, (doc_id,))

            total_deleted_docs += 1

    conn.commit()

    # Get final stats
    cur.execute("""
        SELECT COUNT(DISTINCT title) as unique_titles,
               COUNT(*) as total_docs
        FROM kb_documents
        WHERE collection_name = %s
    """, (COLLECTION_NAME,))

    unique_titles, total_docs = cur.fetchone()

    cur.execute("""
        SELECT COUNT(*) FROM langchain_pg_embedding
        WHERE collection_id = (
            SELECT uuid FROM langchain_pg_collection
            WHERE name = %s
        )
    """, (COLLECTION_NAME,))

    total_embeddings = cur.fetchone()[0]

    cur.close()
    conn.close()

    print("\n" + "=" * 80)
    print("📊 CLEANUP SUMMARY")
    print("=" * 80)
    print(f"Documents deleted: {total_deleted_docs}")
    print(f"Embeddings deleted: {total_deleted_embeddings}")
    print(f"\nFinal state:")
    print(f"  Unique titles: {unique_titles}")
    print(f"  Total documents: {total_docs}")
    print(f"  Total embeddings: {total_embeddings}")
    print(f"  Documents per title: {total_docs / unique_titles:.2f}")
    print("=" * 80)


if __name__ == "__main__":
    cleanup_duplicates()
