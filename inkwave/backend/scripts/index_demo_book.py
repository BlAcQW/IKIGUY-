"""
Index demo book into RAG system for Q&A capabilities.

This script takes the demo book chunks and creates embeddings
in the pgvector database so users can ask questions about the content.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/opt/kasaai/.env')

# Add parent directory to path
sys.path.append('/opt/kasaai/apps/inkwave/backend')
sys.path.append('/opt/kasaai/apps/shared')

from motor.motor_asyncio import AsyncIOMotorClient
from app.services.rag_service import get_rag_service


async def index_demo_book():
    """
    Index the demo book into RAG system.

    Retrieves chunks from MongoDB and creates vector embeddings
    for semantic search and Q&A.
    """

    print("🔍 Indexing demo book into RAG system...\n")

    # Connect to MongoDB
    mongo_url = 'mongodb://admin:aawwER4444%25@127.0.0.1:27017/?authSource=admin'
    client = AsyncIOMotorClient(mongo_url)
    db = client['inkwave']

    try:
        # Get demo book
        book = await db.books.find_one({"book_id": "demo_the_power_of_faith"})
        if not book:
            print("❌ Demo book not found. Run add_demo_book.py first.")
            return

        print(f"📚 Found book: {book['title']}")
        print(f"   Author: {book['author']}\n")

        # Get all chunks for this book
        chunks = await db.book_chunks.find(
            {"book_id": "demo_the_power_of_faith"}
        ).sort("chunk_index", 1).to_list(100)

        print(f"📄 Found {len(chunks)} chunks to index\n")

        if not chunks:
            print("❌ No chunks found for demo book.")
            return

        # Initialize RAG service
        print("🚀 Initializing RAG service...")
        rag_service = get_rag_service()

        # Prepare documents for indexing
        documents = []
        for chunk in chunks:
            # Prepare document with metadata for better Q&A
            chapter_info = f"Chapter {chunk.get('chapter_id', 0) + 1}"
            doc = {
                "text": chunk["text"],
                "metadata": {
                    "book_id": chunk["book_id"],
                    "chunk_id": chunk["chunk_id"],
                    "chunk_index": chunk["chunk_index"],
                    "chapter": chapter_info,
                    "book_title": book["title"],
                    "author": book["author"],
                    "word_count": chunk.get("word_count", 0)
                }
            }
            documents.append(doc)

        # Initialize knowledge base for this book
        collection_name = f"inkwave_book_{book['book_id']}"

        print(f"📊 Creating knowledge base: {collection_name}")
        print(f"   Provider: OpenAI (text-embedding-3-small)")
        print(f"   Documents: {len(documents)}")
        print(f"   This may take 30-60 seconds...\n")

        # Index documents
        result = await rag_service.initialize_knowledge_base(
            collection_name=collection_name,
            documents=documents,
            force_recreate=True  # Recreate if exists
        )

        print(f"\n✅ Successfully indexed {len(documents)} chunks!")
        print(f"   Collection: {collection_name}")
        print(f"   Vector dimension: 1536 (OpenAI)")
        print(f"\n🎯 Users can now ask questions like:")
        print(f"   • 'What does the book say about faith?'")
        print(f"   • 'Tell me about moving mountains'")
        print(f"   • 'What is Abraham's example of faith?'")
        print(f"   • 'How do I walk in victory?'")
        print(f"   • 'What Scripture talks about conquering?'")

        # Test a sample query
        print(f"\n🧪 Testing Q&A with sample query...")
        test_query = "What is faith according to Hebrews 11:1?"

        test_result = await rag_service.query_knowledge_base(
            collection_name=collection_name,
            query=test_query,
            k=2  # Get top 2 relevant chunks
        )

        print(f"\n📝 Sample Q&A Test:")
        print(f"   Question: {test_query}")
        print(f"   Answer: {test_result['answer'][:200]}...")
        print(f"   Confidence: {test_result.get('confidence', 0):.2f}")
        print(f"   Sources: {len(test_result.get('sources', []))} chunks")

        print(f"\n✨ RAG indexing complete! Book is ready for interactive Q&A.")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(index_demo_book())
