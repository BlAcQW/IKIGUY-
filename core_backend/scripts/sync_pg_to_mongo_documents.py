#!/usr/bin/env python3
"""
Sync Knowledge Base Documents from PostgreSQL to MongoDB

This script migrates document metadata from PostgreSQL (langchain_pg_embedding)
to MongoDB (knowledge_base_documents) so documents can be browsed in the UI.
"""

import os
import sys
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import json
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# MongoDB connection
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin')

# PostgreSQL connection
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'aawwER444444')
POSTGRES_SERVER = os.getenv('POSTGRES_SERVER', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB_CORE', 'kasaai_core')


def get_postgres_connection():
    """Create PostgreSQL connection."""
    conn_string = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
    return psycopg2.connect(conn_string)


async def get_mongo_client():
    """Create MongoDB client."""
    client = AsyncIOMotorClient(MONGODB_URL)
    return client


def extract_metadata(pg_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract document metadata from PostgreSQL row and format for MongoDB.

    Args:
        pg_row: Row from PostgreSQL with document and cmetadata

    Returns:
        Document dict formatted for MongoDB
    """
    metadata = pg_row.get('cmetadata', {})

    # Extract company name from collection name
    # Format: helpdesk_company_name -> company_name
    collection_name = pg_row.get('collection_name', '')
    company_name = collection_name.replace('helpdesk_', '') if collection_name.startswith('helpdesk_') else collection_name

    # Get document content
    content = pg_row.get('document', '')

    # Get title from metadata or generate from content
    title = metadata.get('title', content[:100] if content else 'Untitled')

    # Get or generate document ID
    doc_id = metadata.get('doc_id', f"pg_sync_{pg_row.get('embedding_id', 'unknown')}")

    # Extract tags
    tags = metadata.get('tags', [])
    if isinstance(tags, str):
        tags = [tags]
    elif not isinstance(tags, list):
        tags = []

    # Determine category
    category = metadata.get('category', metadata.get('type', 'general'))

    # Get timestamps
    indexed_at = metadata.get('indexed_at')
    updated_at = metadata.get('updated_at')

    # Parse timestamps if they're strings
    if indexed_at and isinstance(indexed_at, str):
        try:
            indexed_at = datetime.fromisoformat(indexed_at.replace('Z', '+00:00'))
        except:
            indexed_at = None

    if updated_at and isinstance(updated_at, str):
        try:
            updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        except:
            updated_at = None

    # Use indexed_at or current time for created_at
    created_at = indexed_at or datetime.utcnow()
    updated_at = updated_at or created_at

    # Build document metadata
    doc_metadata = {
        'word_count': len(content.split()) if content else 0,
        'character_count': len(content) if content else 0,
        'chunk_count': metadata.get('total_chunks', 1),
        'chunk_index': metadata.get('chunk_index', 0),
        'source_type': metadata.get('source', 'unknown'),
    }

    # Add optional metadata fields
    for key in ['star_rating', 'accommodation_id', 'city', 'region']:
        if key in metadata:
            doc_metadata[key] = metadata[key]

    # Build final document
    document = {
        'document_id': doc_id,
        'company_name': company_name,
        'title': title,
        'content': content,
        'category': category,
        'tags': tags,
        'status': 'indexed',  # Already indexed in PostgreSQL
        'source': metadata.get('source', 'migration_from_postgres'),
        'created_at': created_at,
        'updated_at': updated_at,
        'indexed_at': indexed_at or created_at,
        'metadata': doc_metadata,
        'is_active': True,
        'is_archived': False,
        'version': 1,
    }

    return document


async def sync_documents():
    """
    Main sync function - read from PostgreSQL and write to MongoDB.
    """
    print("🔄 Starting document sync from PostgreSQL to MongoDB...")

    # Connect to PostgreSQL
    print("📊 Connecting to PostgreSQL...")
    pg_conn = get_postgres_connection()
    pg_cursor = pg_conn.cursor(cursor_factory=RealDictCursor)

    # Connect to MongoDB
    print("🍃 Connecting to MongoDB...")
    mongo_client = await get_mongo_client()
    mongo_db = mongo_client['kasaai_core']
    mongo_collection = mongo_db['knowledge_base_documents']

    # Create indexes
    print("📇 Creating MongoDB indexes...")
    await mongo_collection.create_index([('document_id', 1)], unique=True)
    await mongo_collection.create_index([('company_name', 1)])
    await mongo_collection.create_index([('category', 1)])
    await mongo_collection.create_index([('status', 1)])
    await mongo_collection.create_index([('created_at', -1)])

    # Query all embeddings from helpdesk collections
    print("🔍 Querying PostgreSQL embeddings...")
    query = """
        SELECT
            e.id as embedding_id,
            e.document,
            e.cmetadata,
            c.name as collection_name,
            c.uuid as collection_uuid
        FROM langchain_pg_embedding e
        JOIN langchain_pg_collection c ON e.collection_id = c.uuid
        WHERE c.name LIKE 'helpdesk_%'
        ORDER BY c.name, e.id
    """

    pg_cursor.execute(query)
    rows = pg_cursor.fetchall()

    print(f"📦 Found {len(rows)} documents to sync")

    # Process and insert documents
    inserted_count = 0
    updated_count = 0
    error_count = 0

    for i, row in enumerate(rows, 1):
        try:
            # Extract metadata and build document
            document = extract_metadata(row)

            # Upsert to MongoDB (update if exists, insert if not)
            result = await mongo_collection.update_one(
                {'document_id': document['document_id']},
                {'$set': document},
                upsert=True
            )

            if result.upserted_id:
                inserted_count += 1
            else:
                updated_count += 1

            # Progress update every 50 documents
            if i % 50 == 0:
                print(f"  📝 Processed {i}/{len(rows)} documents...")

        except Exception as e:
            error_count += 1
            print(f"  ❌ Error processing document {row.get('embedding_id')}: {str(e)}")

    # Close connections
    pg_cursor.close()
    pg_conn.close()
    mongo_client.close()

    # Summary
    print("\n" + "="*60)
    print("✅ Sync Complete!")
    print("="*60)
    print(f"📊 Total processed: {len(rows)}")
    print(f"➕ Inserted: {inserted_count}")
    print(f"🔄 Updated: {updated_count}")
    print(f"❌ Errors: {error_count}")
    print("="*60)

    # Show collection stats
    print("\n📈 MongoDB Collection Stats:")
    total_docs = await mongo_collection.count_documents({})
    print(f"  Total documents: {total_docs}")

    # Group by company
    pipeline = [
        {"$group": {
            "_id": "$company_name",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]

    async for result in mongo_collection.aggregate(pipeline):
        company = result['_id']
        count = result['count']
        print(f"  - {company}: {count} documents")


if __name__ == "__main__":
    asyncio.run(sync_documents())
