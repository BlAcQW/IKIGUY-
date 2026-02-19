#!/usr/bin/env python3
"""
Delete all existing documents and embeddings for premier_health_production collection.
"""

import psycopg2

POSTGRES_PASSWORD = "aawwER444444"
COLLECTION_NAME = "helpdesk_premier_health_production"


def delete_all_documents():
    """Delete all documents and their embeddings."""
    print("🗑️  DELETING ALL EXISTING DOCUMENTS")
    print("=" * 80)
    
    conn = psycopg2.connect(
        host="127.0.0.1",
        database="kasaai_core",
        user="postgres",
        password=POSTGRES_PASSWORD
    )
    cur = conn.cursor()
    
    # Get count before deletion
    cur.execute("""
        SELECT COUNT(*) FROM kb_documents
        WHERE collection_name = %s
    """, (COLLECTION_NAME,))
    doc_count = cur.fetchone()[0]
    
    # Get collection UUID
    cur.execute("""
        SELECT uuid FROM langchain_pg_collection
        WHERE name = %s
    """, (COLLECTION_NAME,))
    result = cur.fetchone()
    
    if result:
        collection_uuid = result[0]
        
        # Count embeddings
        cur.execute("""
            SELECT COUNT(*) FROM langchain_pg_embedding
            WHERE collection_id = %s
        """, (collection_uuid,))
        embedding_count = cur.fetchone()[0]
        
        print(f"📊 Current state:")
        print(f"   Documents: {doc_count}")
        print(f"   Embeddings: {embedding_count}")
        
        # Delete embeddings first
        print(f"\n🗑️  Deleting {embedding_count} embeddings...")
        cur.execute("""
            DELETE FROM langchain_pg_embedding
            WHERE collection_id = %s
        """, (collection_uuid,))
        print(f"   ✅ Deleted {cur.rowcount} embeddings")
    else:
        print(f"⚠️  Collection {COLLECTION_NAME} not found in langchain_pg_collection")
    
    # Delete documents
    print(f"\n🗑️  Deleting {doc_count} documents...")
    cur.execute("""
        DELETE FROM kb_documents
        WHERE collection_name = %s
    """, (COLLECTION_NAME,))
    print(f"   ✅ Deleted {cur.rowcount} documents")
    
    conn.commit()
    
    # Verify deletion
    cur.execute("""
        SELECT COUNT(*) FROM kb_documents
        WHERE collection_name = %s
    """, (COLLECTION_NAME,))
    remaining_docs = cur.fetchone()[0]
    
    if result:
        cur.execute("""
            SELECT COUNT(*) FROM langchain_pg_embedding
            WHERE collection_id = %s
        """, (collection_uuid,))
        remaining_embeddings = cur.fetchone()[0]
    else:
        remaining_embeddings = 0
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("📊 DELETION SUMMARY")
    print("=" * 80)
    print(f"Documents remaining: {remaining_docs}")
    print(f"Embeddings remaining: {remaining_embeddings}")
    print("=" * 80)
    
    if remaining_docs == 0 and remaining_embeddings == 0:
        print("✅ All documents and embeddings successfully deleted!")
    else:
        print("⚠️  Warning: Some documents or embeddings may still remain")


if __name__ == "__main__":
    delete_all_documents()
