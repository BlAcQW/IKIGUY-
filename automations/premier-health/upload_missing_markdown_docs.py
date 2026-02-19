#!/usr/bin/env python3
"""
Upload missing Premier Health markdown documents to knowledge base.

This script reads all markdown files from processed_data/markdown_documents/
and uploads any that are not yet in the kb_documents table.
"""

import sys
import os
import asyncio
import logging
import hashlib
from typing import List, Dict, Any
from pathlib import Path

# Set required environment variables BEFORE importing services
os.environ["MONGODB_URL"] = "mongodb://admin:aawwER444444@127.0.0.1:27017/kasaai_core?authSource=admin"
os.environ["POSTGRES_PASSWORD"] = "aawwER444444"
os.environ["GEMINI_API_KEY"] = "AIzaSyAACjmMMYIVH2Pq8Ns8KbOud-X8oCQMny4"

# Add paths
sys.path.append('/opt/kasaai/apps/core_backend')

from backend.services.pg_document_service import pg_document_service
from backend.models.knowledge_base import DocumentCreate

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
MARKDOWN_DIR = Path("/opt/kasaai/apps/automations/premier-health/processed_data/markdown_documents")
COLLECTION_NAME = "premier_health_production"  # Service will prepend "helpdesk_"


def extract_metadata_from_markdown(content: str, filename: str) -> Dict[str, Any]:
    """
    Extract metadata from markdown content.

    Args:
        content: Markdown content
        filename: Source filename

    Returns:
        Dictionary with metadata
    """
    lines = content.split('\n')

    # Extract city from title (first line should be "# Healthcare Providers in CITY")
    city = filename.replace('.md', '').replace('_', ' ').upper()
    region = "UNKNOWN"

    # Try to extract region from content
    for line in lines:
        if line.startswith('**Region'):
            parts = line.split(':')
            if len(parts) > 1:
                region = parts[1].strip().replace('*', '')
                break

    # Count providers (count ## headers excluding the first one)
    provider_count = sum(1 for line in lines if line.startswith('## ') and not line.startswith('# '))

    return {
        "city": city,
        "region": region,
        "provider_count": provider_count,
        "source": "markdown_documents"
    }


async def upload_markdown_files():
    """
    Upload all markdown files that don't exist in the database.
    """
    logger.info("=" * 80)
    logger.info("🏥 PREMIER HEALTH - UPLOAD MISSING MARKDOWN DOCUMENTS")
    logger.info("=" * 80)
    logger.info(f"Markdown Directory: {MARKDOWN_DIR}")
    logger.info(f"Collection: {COLLECTION_NAME}")
    logger.info("=" * 80)

    if not MARKDOWN_DIR.exists():
        logger.error(f"❌ Directory not found: {MARKDOWN_DIR}")
        return

    # Get all markdown files
    markdown_files = sorted(MARKDOWN_DIR.glob("*.md"))
    logger.info(f"📄 Found {len(markdown_files)} markdown files")

    # Track results
    uploaded = 0
    skipped = 0
    errors = 0

    # Process each file
    for i, filepath in enumerate(markdown_files, 1):
        try:
            # Read file content
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Skip empty files
            if not content.strip():
                logger.warning(f"[{i}/{len(markdown_files)}] ⏭️  {filepath.name}: Empty file (skipped)")
                skipped += 1
                continue

            # Extract title from filename (remove .md extension)
            city_name = filepath.stem.replace('_', ' ').title()
            title = f"Healthcare Providers in {city_name}"

            # Extract metadata
            metadata = extract_metadata_from_markdown(content, filepath.name)

            # Create content hash for deduplication
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            # Determine tags based on content and metadata
            tags = ["providers", "healthcare", metadata["city"].lower()]
            if metadata["region"] != "UNKNOWN":
                tags.append(metadata["region"].upper())

            # Create document
            doc = DocumentCreate(
                company_name=COLLECTION_NAME,
                title=title,
                content=content,
                content_hash=content_hash,
                category="provider_directory",
                source="markdown_processed",
                tags=tags,
                metadata=metadata
            )

            # Upload to database
            result = await pg_document_service.create_document(doc)

            if result.success:
                uploaded += 1
                logger.info(f"[{i}/{len(markdown_files)}] ✅ {filepath.name}: Uploaded ({metadata['provider_count']} providers, region: {metadata['region']})")
            else:
                if "duplicate" in str(result.error).lower() or "already exists" in str(result.error).lower():
                    skipped += 1
                    logger.info(f"[{i}/{len(markdown_files)}] ⏭️  {filepath.name}: Already exists (skipped)")
                else:
                    errors += 1
                    logger.error(f"[{i}/{len(markdown_files)}] ❌ {filepath.name}: {result.error}")

        except Exception as e:
            errors += 1
            logger.error(f"[{i}/{len(markdown_files)}] ❌ {filepath.name}: {str(e)}")

    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 UPLOAD SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total markdown files: {len(markdown_files)}")
    logger.info(f"✅ Newly uploaded: {uploaded}")
    logger.info(f"⏭️  Already existed: {skipped}")
    logger.info(f"❌ Errors: {errors}")
    logger.info("=" * 80)

    if errors == 0:
        logger.info("✅ ALL MISSING DOCUMENTS UPLOADED SUCCESSFULLY!")
        logger.info("")
        logger.info("🔄 NEXT STEPS:")
        logger.info("1. Run index_all_with_regions.py to create embeddings for new documents")
        logger.info("2. Verify ASAFO and AHINSAN are now searchable")
        logger.info("3. Test queries on VAPI")
    else:
        logger.warning(f"⚠️  Completed with {errors} errors")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(upload_markdown_files())
