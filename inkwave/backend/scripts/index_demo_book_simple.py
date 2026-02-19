"""
Index demo book into RAG system for Q&A capabilities.

Simplified version that directly uses RAG service without app config.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/opt/kasaai/.env')

# Add shared services to path
sys.path.append('/opt/kasaai/apps/shared')

from motor.motor_asyncio import AsyncIOMotorClient
from integration.rag import RAGService, RAGConfig, KnowledgeDocument


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

        # Get credentials from environment
        gemini_key = os.getenv('GEMINI_API_KEY')
        pg_host = os.getenv('POSTGRES_SERVER', 'localhost')
        pg_port = int(os.getenv('POSTGRES_PORT', '5432'))
        pg_user = os.getenv('POSTGRES_USER', 'postgres')
        pg_password = os.getenv('POSTGRES_PASSWORD')
        pg_database = os.getenv('POSTGRES_DB_CORE', 'kasaai_core')

        if not gemini_key:
            print("❌ GEMINI_API_KEY not found in environment")
            return

        if not pg_password:
            print("❌ POSTGRES_PASSWORD not found in environment")
            return

        # Create RAG configuration using Gemini (quota-friendly!)
        rag_config = RAGConfig(
            ai_provider="gemini",
            api_key=gemini_key,
            embedding_model="text-embedding-004",  # Gemini embedding model
            llm_model="gemini-2.0-flash-exp",  # Fast Gemini model
            postgres_host=pg_host,
            postgres_port=str(pg_port),
            postgres_user=pg_user,
            postgres_password=pg_password,
            postgres_db=pg_database
        )

        # Create RAG service
        rag_service = RAGService(config=rag_config)

        # Prepare documents for indexing as KnowledgeDocument objects
        documents = []

        for chunk in chunks:
            # Prepare document with metadata for better Q&A
            chapter_info = f"Chapter {chunk.get('chapter_id', 0) + 1}"

            # Create KnowledgeDocument
            knowledge_doc = KnowledgeDocument(
                id=chunk["chunk_id"],
                title=f"{book['title']} - {chapter_info}",
                content=chunk["text"],
                category="faith_book",
                source=book["title"],
                tags=["faith", "spirituality", "christian"],
                metadata={
                    "book_id": chunk["book_id"],
                    "chunk_id": chunk["chunk_id"],
                    "chunk_index": chunk["chunk_index"],
                    "chapter": chapter_info,
                    "book_title": book["title"],
                    "author": book["author"],
                    "word_count": chunk.get("word_count", 0)
                }
            )
            documents.append(knowledge_doc)

        # Initialize knowledge base for this book
        collection_name = f"inkwave_book_{book['book_id']}"

        print(f"📊 Creating knowledge base: {collection_name}")
        print(f"   Provider: Gemini (text-embedding-004)")
        print(f"   Documents: {len(documents)}")
        print(f"   This may take 30-60 seconds...\n")

        # Index documents
        result = await rag_service.initialize_knowledge_base(
            collection_name=collection_name,
            documents=documents
        )

        print(f"\n✅ Successfully indexed {len(documents)} chunks!")
        print(f"   Collection: {collection_name}")
        print(f"   Vector dimension: 768 (Gemini)")
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
            system_prompt_template="You are a helpful assistant explaining biblical concepts about faith and victory. Answer based only on the provided book content."
        )

        print(f"\n📝 Sample Q&A Test:")
        print(f"   Question: {test_query}")
        print(f"   Answer: {test_result.response[:300]}...")
        print(f"   Confidence: {test_result.confidence_score:.2f}")
        print(f"   Sources: {len(test_result.sources_used)} chunks")
        print(f"   Success: {'✅' if test_result.success else '❌'}")

        print(f"\n✨ RAG indexing complete! Book is ready for interactive Q&A.")
        print(f"\n💡 Users can now ask questions and get AI-powered answers!")
        print(f"   The system will search through all 15 chunks and provide")
        print(f"   accurate answers with biblical references and context.")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(index_demo_book())
