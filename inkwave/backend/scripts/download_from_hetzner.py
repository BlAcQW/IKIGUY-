"""
Download 'Destined To Make An Impact' PDF from Hetzner storage.

This script connects to Hetzner Storage Box and downloads the PDF file.
"""

import asyncio
import sys
import os
import logging

# Add paths
sys.path.insert(0, '/opt/kasaai/apps')
sys.path.insert(0, '/opt/kasaai/apps/inkwave/backend')

from app.services.storage_service import InkWaveStorageService
from app.core.database import Database, get_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def download_pdf():
    """Download the PDF from Hetzner storage."""

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
            return False

        logger.info(f"📚 Book: {book['title']} by {book['author']}")
        logger.info(f"📄 PDF URL: {book.get('pdf_url', 'Not set')}")

        # Initialize storage service
        storage = InkWaveStorageService()
        await storage.initialize()

        if storage._local_fallback:
            logger.warning("⚠️ Storage is in local fallback mode")
            logger.info(f"Local path: {storage._local_path}")

            # Check local storage
            local_pdf = os.path.join(storage._local_path, "books", f"{book_id}.pdf")
            if os.path.exists(local_pdf):
                logger.info(f"✅ PDF found in local storage: {local_pdf}")
                return local_pdf
            else:
                logger.error(f"❌ PDF not found in local storage: {local_pdf}")
                return None
        else:
            logger.info("📡 Connected to Hetzner storage")

            # Try to download from Hetzner
            remote_path = f"books/{book_id}.pdf"
            local_path = f"/opt/kasaai/apps/inkwave/backend/storage/books/{book_id}.pdf"

            logger.info(f"📥 Downloading from Hetzner: {remote_path}")
            logger.info(f"📁 Saving to: {local_path}")

            # Download file
            try:
                file_content = await storage._storage.download_file(remote_path)

                # Save to local storage
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, 'wb') as f:
                    f.write(file_content)

                logger.info(f"✅ Downloaded {len(file_content)} bytes")
                logger.info(f"✅ Saved to: {local_path}")

                return local_path

            except Exception as e:
                logger.error(f"❌ Download failed: {e}")

                # Try alternative: use curl with WebDAV
                logger.info("🔄 Trying alternative download method with curl...")
                return await download_with_curl(book_id)

    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return None


async def download_with_curl(book_id: str):
    """Download using curl with WebDAV credentials."""
    import subprocess

    # Get credentials from environment
    username = os.getenv("HETZNER_STORAGE_USERNAME", "u497034-sub1")
    password = os.getenv("HETZNER_STORAGE_PASSWORD")

    if not password:
        logger.error("❌ HETZNER_STORAGE_PASSWORD not set")
        return None

    url = f"https://u497034-sub1.your-storagebox.de/kasaai/inkwave/books/{book_id}.pdf"
    output_path = f"/opt/kasaai/apps/inkwave/backend/storage/books/{book_id}.pdf"

    logger.info(f"📥 Downloading from: {url}")

    # Create directory
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Download with curl
    cmd = [
        "curl",
        "-u", f"{username}:{password}",
        "-L",  # Follow redirects
        "-o", output_path,
        url
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0 and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            logger.info(f"✅ Downloaded {file_size} bytes")
            logger.info(f"✅ Saved to: {output_path}")
            return output_path
        else:
            logger.error(f"❌ curl failed: {result.stderr}")
            return None

    except Exception as e:
        logger.error(f"❌ curl error: {e}")
        return None


if __name__ == "__main__":
    result = asyncio.run(download_pdf())

    if result:
        print(f"\n✅ SUCCESS: PDF downloaded to {result}")
        print(f"\nNext step: Run the processing script:")
        print(f"  /opt/kasaai/apps/venv/bin/python scripts/process_destined_impact.py {result}")
        sys.exit(0)
    else:
        print("\n❌ FAILED: Could not download PDF from Hetzner storage")
        sys.exit(1)
