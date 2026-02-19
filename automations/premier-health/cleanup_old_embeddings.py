#!/usr/bin/env python3
"""
Clean up old duplicate embeddings, keeping only the latest ones from direct_manual_indexing.
"""

import psycopg2

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


def cleanup_old_embeddings():
    """Delete old embeddings from previous indexing attempts."""
    print("🧹 CLEANING UP OLD DUPLICATE EMBEDDINGS")
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

    # Count embeddings by source
    cur.execute("""
        SELECT
            cmetadata->>'source' as source,
            COUNT(*) as count
        FROM langchain_pg_embedding
        WHERE collection_id = %s
        GROUP BY cmetadata->>'source'
        ORDER BY count DESC
    """, (collection_uuid,))

    sources = cur.fetchall()
    print("\n📊 Current embeddings by source:")
    for source, count in sources:
        print(f"   {source}: {count}")

    # Delete embeddings NOT from direct_manual_indexing
    print("\n🗑️  Deleting old embeddings...")
    cur.execute("""
        DELETE FROM langchain_pg_embedding
        WHERE collection_id = %s
        AND (
            cmetadata->>'source' = 'manual_reindex'
            OR cmetadata->>'source' = 'regional_csv_enriched'
        )
    """, (collection_uuid,))

    deleted_count = cur.rowcount
    print(f"   Deleted {deleted_count} old embeddings")

    # Update kb_documents to remove vector_ids that no longer exist
    print("\n🔄 Cleaning up vector_ids in kb_documents...")
    cur.execute("""
        UPDATE kb_documents d
        SET vector_ids = ARRAY(
            SELECT unnest(vector_ids)
            WHERE unnest(vector_ids)::text IN (
                SELECT id::text FROM langchain_pg_embedding
                WHERE collection_id = %s
            )
        )
        WHERE collection_name = %s
        AND vector_ids IS NOT NULL
    """, (collection_uuid, COLLECTION_NAME))

    updated_docs = cur.rowcount
    print(f"   Updated {updated_docs} documents")

    conn.commit()

    # Final count
    cur.execute("""
        SELECT COUNT(*) FROM langchain_pg_embedding
        WHERE collection_id = %s
    """, (collection_uuid,))

    final_count = cur.fetchone()[0]

    cur.close()
    conn.close()

    print("\n" + "=" * 80)
    print("📊 CLEANUP SUMMARY")
    print("=" * 80)
    print(f"Deleted embeddings: {deleted_count}")
    print(f"Updated documents: {updated_docs}")
    print(f"Remaining embeddings: {final_count}")
    print("=" * 80)


if __name__ == "__main__":
    cleanup_old_embeddings()
