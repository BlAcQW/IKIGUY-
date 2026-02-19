#!/usr/bin/env python3
"""
Fix collection names by updating documents from
helpdesk_helpdesk_premier_health_production to helpdesk_premier_health_production
and updating embeddings to point to the correct collection.
"""

import psycopg2

POSTGRES_PASSWORD = "aawwER444444"
OLD_COLLECTION = "helpdesk_helpdesk_premier_health_production"
NEW_COLLECTION = "helpdesk_premier_health_production"


def get_db_connection():
    """Get PostgreSQL database connection."""
    return psycopg2.connect(
        host="127.0.0.1",
        database="kasaai_core",
        user="postgres",
        password=POSTGRES_PASSWORD
    )


def fix_collection_names():
    """Update collection names for documents and embeddings."""
    print("🔧 FIXING COLLECTION NAMES")
    print("=" * 80)

    conn = get_db_connection()
    cur = conn.cursor()

    # Get collection UUIDs
    cur.execute("""
        SELECT uuid FROM langchain_pg_collection
        WHERE name = %s
    """, (OLD_COLLECTION,))
    old_uuid = cur.fetchone()

    cur.execute("""
        SELECT uuid FROM langchain_pg_collection
        WHERE name = %s
    """, (NEW_COLLECTION,))
    new_uuid = cur.fetchone()

    if not old_uuid or not new_uuid:
        print("❌ Could not find both collection UUIDs!")
        if not old_uuid:
            print(f"   Old collection not found: {OLD_COLLECTION}")
        if not new_uuid:
            print(f"   New collection not found: {NEW_COLLECTION}")
        return

    old_uuid = old_uuid[0]
    new_uuid = new_uuid[0]

    print(f"Old collection UUID: {old_uuid}")
    print(f"New collection UUID: {new_uuid}")
    print("=" * 80)

    # Update kb_documents to use new collection name
    print("\n1. Updating kb_documents collection_name...")
    cur.execute("""
        UPDATE kb_documents
        SET collection_name = %s
        WHERE collection_name = %s
    """, (NEW_COLLECTION, OLD_COLLECTION))

    docs_updated = cur.rowcount
    print(f"   Updated {docs_updated} documents")

    # Update embeddings to point to new collection
    print("\n2. Updating langchain_pg_embedding collection_id...")
    cur.execute("""
        UPDATE langchain_pg_embedding
        SET collection_id = %s
        WHERE collection_id = %s
    """, (new_uuid, old_uuid))

    embeddings_updated = cur.rowcount
    print(f"   Updated {embeddings_updated} embeddings")

    conn.commit()
    cur.close()
    conn.close()

    print("\n" + "=" * 80)
    print("📊 FIX SUMMARY")
    print("=" * 80)
    print(f"Documents updated: {docs_updated}")
    print(f"Embeddings updated: {embeddings_updated}")
    print(f"Collection changed from: {OLD_COLLECTION}")
    print(f"Collection changed to: {NEW_COLLECTION}")
    print("=" * 80)


if __name__ == "__main__":
    fix_collection_names()
