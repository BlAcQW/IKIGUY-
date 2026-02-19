#!/usr/bin/env python3
"""
Copy embeddings from helpdesk_helpdesk_premier_health_production
to helpdesk_premier_health_production so RAG API can find them.
"""

import psycopg2
import psycopg2.extras

POSTGRES_PASSWORD = "aawwER444444"
SOURCE_COLLECTION = "helpdesk_helpdesk_premier_health_production"
TARGET_COLLECTION = "helpdesk_premier_health_production"


def get_db_connection():
    """Get PostgreSQL database connection."""
    return psycopg2.connect(
        host="127.0.0.1",
        database="kasaai_core",
        user="postgres",
        password=POSTGRES_PASSWORD
    )


def copy_embeddings():
    """Copy all embeddings to the correct collection."""
    print("🔄 COPYING EMBEDDINGS TO CORRECT COLLECTION")
    print("=" * 80)

    conn = get_db_connection()
    cur = conn.cursor()

    # Get source and target collection UUIDs
    cur.execute("""
        SELECT uuid FROM langchain_pg_collection
        WHERE name = %s
    """, (SOURCE_COLLECTION,))
    source_uuid = cur.fetchone()

    if not source_uuid:
        print(f"❌ Source collection {SOURCE_COLLECTION} not found!")
        return

    source_uuid = source_uuid[0]
    print(f"Source collection UUID: {source_uuid}")

    cur.execute("""
        SELECT uuid FROM langchain_pg_collection
        WHERE name = %s
    """, (TARGET_COLLECTION,))
    target_uuid = cur.fetchone()

    if not target_uuid:
        print(f"❌ Target collection {TARGET_COLLECTION} not found!")
        return

    target_uuid = target_uuid[0]
    print(f"Target collection UUID: {target_uuid}")
    print("=" * 80)

    # Get all embeddings from source collection
    cur.execute("""
        SELECT id, embedding, document, cmetadata
        FROM langchain_pg_embedding
        WHERE collection_id = %s
    """, (source_uuid,))

    embeddings = cur.fetchall()
    total = len(embeddings)

    print(f"Found {total} embeddings to copy")
    print("=" * 80)

    success_count = 0
    skip_count = 0

    for i, (embedding_id, embedding, document, cmetadata) in enumerate(embeddings, 1):
        try:
            # Check if embedding already exists in target collection
            cur.execute("""
                SELECT id FROM langchain_pg_embedding
                WHERE collection_id = %s AND id = %s
            """, (target_uuid, embedding_id))

            if cur.fetchone():
                print(f"[{i}/{total}] Skipping {embedding_id} (already exists)")
                skip_count += 1
                continue

            # Copy embedding to target collection
            # Convert cmetadata to JSON if it's a dict
            if isinstance(cmetadata, dict):
                cmetadata = psycopg2.extras.Json(cmetadata)

            cur.execute("""
                INSERT INTO langchain_pg_embedding (id, collection_id, embedding, document, cmetadata)
                VALUES (%s, %s, %s, %s, %s)
            """, (embedding_id, target_uuid, embedding, document, cmetadata))

            conn.commit()

            if i % 50 == 0 or i == total:
                print(f"[{i}/{total}] Copied {success_count} embeddings...")

            success_count += 1

        except Exception as e:
            print(f"[{i}/{total}] ❌ Error copying {embedding_id}: {e}")
            conn.rollback()

    cur.close()
    conn.close()

    print("\n" + "=" * 80)
    print("📊 COPY SUMMARY")
    print("=" * 80)
    print(f"Total embeddings: {total}")
    print(f"Successfully copied: {success_count}")
    print(f"Skipped (already exist): {skip_count}")
    print(f"Success rate: {(success_count/total*100):.1f}%")
    print("=" * 80)


if __name__ == "__main__":
    copy_embeddings()
