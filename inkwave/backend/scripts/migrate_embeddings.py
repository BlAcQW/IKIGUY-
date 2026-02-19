#!/usr/bin/env python3
"""
Embedding Migration Script for InkWave.

Generates embeddings for existing books that don't have them yet.
This is a one-time migration script to backfill embeddings for books
uploaded before the embedding feature was implemented.

Usage:
    # Migrate all books without embeddings
    python scripts/migrate_embeddings.py

    # Migrate a specific book
    python scripts/migrate_embeddings.py --book-id book_abc123

    # Dry run (check what would be migrated)
    python scripts/migrate_embeddings.py --dry-run

    # Force re-migration (regenerate even if embeddings exist)
    python scripts/migrate_embeddings.py --force --book-id book_abc123
"""

import asyncio
import argparse
import logging
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, '/opt/kasaai/apps/shared')

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/opt/kasaai/.env')
load_dotenv('/opt/kasaai/apps/inkwave/backend/.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def get_mongodb_client():
    """Get MongoDB client."""
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://admin:aawwER4444%40@127.0.0.1:27017/')
    client = AsyncIOMotorClient(mongodb_uri)
    return client


async def get_books_needing_embeddings(db, book_id: str = None, force: bool = False):
    """
    Get list of books that need embedding generation.

    Args:
        db: MongoDB database
        book_id: Optional specific book ID
        force: If True, include books that already have embeddings

    Returns:
        List of book documents
    """
    # Import embedding service to check existing embeddings
    from app.services.embedding_service import get_embedding_service

    query = {"processing_status": "ready", "processed": True}
    if book_id:
        query["book_id"] = book_id

    books = []
    async for book in db.books.find(query):
        if force:
            books.append(book)
        else:
            # Check if book already has embeddings
            try:
                embedding_service = await get_embedding_service()
                stats = await embedding_service.get_embedding_stats(book["book_id"])
                if stats["embedding_count"] == 0:
                    books.append(book)
                else:
                    logger.info(f"Skipping {book['book_id']} - already has {stats['embedding_count']} embeddings")
            except Exception as e:
                logger.warning(f"Could not check embeddings for {book['book_id']}: {e}")
                books.append(book)  # Include if we can't check

    return books


async def migrate_book_embeddings(db, book: dict, dry_run: bool = False):
    """
    Generate embeddings for a single book.

    Args:
        db: MongoDB database
        book: Book document
        dry_run: If True, only report what would be done

    Returns:
        Number of embeddings generated
    """
    book_id = book["book_id"]
    logger.info(f"Processing book: {book_id} - {book.get('title', 'Untitled')}")

    # Get all chunks for this book
    chunks = []
    async for chunk in db.book_chunks.find({"book_id": book_id}).sort("chunk_index", 1):
        chunks.append({
            "chunk_index": chunk["chunk_index"],
            "text": chunk["text"],
            "chapter_id": chunk.get("chapter_id")
        })

    if not chunks:
        logger.warning(f"No chunks found for book {book_id}")
        return 0

    logger.info(f"Found {len(chunks)} chunks for book {book_id}")

    if dry_run:
        logger.info(f"[DRY RUN] Would generate {len(chunks)} embeddings for book {book_id}")
        return len(chunks)

    # Generate and store embeddings
    from app.services.embedding_service import get_embedding_service

    embedding_service = await get_embedding_service()

    batch_size = 50
    total_stored = 0

    for batch_start in range(0, len(chunks), batch_size):
        batch_end = min(batch_start + batch_size, len(chunks))
        batch_chunks = chunks[batch_start:batch_end]
        batch_texts = [c["text"] for c in batch_chunks]

        try:
            # Generate embeddings
            embeddings = await embedding_service.generate_embeddings(batch_texts)

            # Store in pgvector
            stored = await embedding_service.store_embeddings(
                book_id=book_id,
                chunks=batch_chunks,
                embeddings=embeddings
            )
            total_stored += stored

            logger.info(f"  Batch {batch_start // batch_size + 1}: stored {stored} embeddings")

        except Exception as e:
            logger.error(f"Failed to process batch {batch_start // batch_size + 1}: {e}")

    logger.info(f"Completed book {book_id}: {total_stored} embeddings stored")
    return total_stored


async def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description='Migrate book embeddings for InkWave')
    parser.add_argument('--book-id', type=str, help='Specific book ID to migrate')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--force', action='store_true', help='Regenerate embeddings even if they exist')
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("InkWave Embedding Migration Script")
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")

    if args.force:
        logger.info("FORCE MODE - Will regenerate all embeddings")

    # Connect to MongoDB
    client = await get_mongodb_client()
    db = client['inkwave']

    try:
        # Get books needing migration
        books = await get_books_needing_embeddings(db, args.book_id, args.force)

        if not books:
            logger.info("No books need embedding migration")
            return

        logger.info(f"Found {len(books)} books to process")

        # Process each book
        total_embeddings = 0
        successful_books = 0
        failed_books = 0

        for i, book in enumerate(books, 1):
            logger.info(f"\n[{i}/{len(books)}] Processing book...")
            try:
                count = await migrate_book_embeddings(db, book, args.dry_run)
                total_embeddings += count
                successful_books += 1
            except Exception as e:
                logger.error(f"Failed to migrate book {book['book_id']}: {e}")
                failed_books += 1

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("Migration Summary")
        logger.info("=" * 60)
        logger.info(f"Total books processed: {len(books)}")
        logger.info(f"Successful: {successful_books}")
        logger.info(f"Failed: {failed_books}")
        logger.info(f"Total embeddings: {total_embeddings}")

        if args.dry_run:
            logger.info("\nThis was a DRY RUN - no changes were made")

    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
