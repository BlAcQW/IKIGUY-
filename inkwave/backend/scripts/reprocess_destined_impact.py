"""
Reprocess 'Destined To Make An Impact' with updated filtering.

This script reprocesses the book to apply the new publisher review page filtering.
"""

import asyncio
import sys
import os
import logging

# Add paths
sys.path.insert(0, '/opt/kasaai/apps')
sys.path.insert(0, '/opt/kasaai/apps/inkwave/backend')

from app.core.database import Database, get_db
from app.services.book_processing_service import get_book_processing_service
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def reprocess_book():
    """Reprocess the Destined To Make An Impact book."""

    book_id = "book_ab5214413fb1"

    # Connect to database
    await Database.connect()
    logger.info("✅ Connected to database")

    try:
        db = get_db()

        # Get book info
        book = await db.books.find_one({"book_id": book_id})
        if not book:
            logger.error(f"Book {book_id} not found")
            return

        logger.info(f"📚 Found book: {book['title']} by {book['author']}")

        # Delete existing chunks and embeddings
        logger.info(f"🗑️ Deleting existing chunks...")
        deleted_chunks = await db.book_chunks.delete_many({"book_id": book_id})
        logger.info(f"✅ Deleted {deleted_chunks.deleted_count} chunks")

        # Note: Embeddings in pgvector need to be deleted separately
        # For now, we'll focus on MongoDB chunks

        # Get the PDF path
        pdf_path = book.get('pdf_url', '').replace('/api/v1/storage/', '')
        if not pdf_path.startswith('/'):
            pdf_path = f"/opt/kasaai/apps/inkwave/backend/storage/{pdf_path}"

        logger.info(f"📄 PDF path: {pdf_path}")

        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return

        # Prepare metadata
        book_metadata = {
            "title": book['title'],
            "author": book['author'],
            "cover_url": book.get('cover_url'),
            "genre": book.get('genre', 'Religious'),
            "description": book.get('description', '')
        }

        # Reset book status
        await db.books.update_one(
            {"book_id": book_id},
            {
                "$set": {
                    "processed": False,
                    "processing_status": "processing",
                    "processing_stage": "initializing",
                    "processing_progress": 0,
                    "processing_message": "Reprocessing with updated filters..."
                }
            }
        )

        logger.info(f"🔄 Starting reprocessing...")

        # Process the book
        service = await get_book_processing_service()
        result = await service.process_book_file(
            file_path=pdf_path,
            book_metadata=book_metadata,
            uploaded_by=book['uploaded_by'],
            book_id=book_id,
            use_ai_chapter_detection=False
        )

        logger.info(f"✅ Reprocessing completed!")
        logger.info(f"📊 Chapters: {len(result.chapters)}")

        # Show first few chunks
        chunks = await db.book_chunks.find(
            {"book_id": book_id}
        ).sort("chunk_index", 1).limit(5).to_list(5)

        logger.info(f"\n📖 First {len(chunks)} chunks:")
        for chunk in chunks:
            text_preview = chunk['text'][:100].replace('\n', ' ')
            logger.info(f"  [{chunk['chunk_index']}] {text_preview}...")

    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(reprocess_book())
