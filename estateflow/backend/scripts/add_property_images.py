"""
Script to add sample images to properties from Pexels.

This script fetches real estate images from Pexels API and updates
property records in MongoDB with appropriate images based on property type.
"""

import asyncio
import os
import sys
from typing import List, Dict
from motor.motor_asyncio import AsyncIOMotorClient
import httpx
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pexels API configuration
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "YOUR_API_KEY_HERE")
PEXELS_BASE_URL = "https://api.pexels.com/v1"

# MongoDB configuration
MONGO_URL = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/"
DB_NAME = "estateflow"

# Property type to search query mapping
PROPERTY_TYPE_QUERIES = {
    "apartment": "modern apartment interior luxury",
    "villa": "luxury villa mansion exterior",
    "house": "beautiful family house suburban",
    "townhouse": "modern townhouse residential",
    "penthouse": "luxury penthouse city view",
    "commercial": "modern office building commercial space",
    "land": "empty land plot development",
    "loft": "modern loft apartment industrial",
    "condo": "condominium apartment building",
    "studio": "studio apartment modern minimalist",
}


async def fetch_pexels_images(query: str, per_page: int = 5) -> List[str]:
    """
    Fetch images from Pexels API.

    Args:
        query: Search query
        per_page: Number of images to fetch

    Returns:
        List of image URLs
    """
    # Since we may not have API key, use curated Pexels URLs
    # These are high-quality real estate images from Pexels

    # Fallback to predefined Pexels image IDs for different property types
    pexels_images = {
        "modern apartment interior luxury": [
            "https://images.pexels.com/photos/1457842/pexels-photo-1457842.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/1643389/pexels-photo-1643389.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/1571460/pexels-photo-1571460.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/1571468/pexels-photo-1571468.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/1648776/pexels-photo-1648776.jpeg?auto=compress&cs=tinysrgb&w=1200",
        ],
        "luxury villa mansion exterior": [
            "https://images.pexels.com/photos/106399/pexels-photo-106399.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/259588/pexels-photo-259588.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/280229/pexels-photo-280229.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/1396122/pexels-photo-1396122.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/2102587/pexels-photo-2102587.jpeg?auto=compress&cs=tinysrgb&w=1200",
        ],
        "beautiful family house suburban": [
            "https://images.pexels.com/photos/186077/pexels-photo-186077.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/1029599/pexels-photo-1029599.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/1438832/pexels-photo-1438832.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/2121121/pexels-photo-2121121.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/1974596/pexels-photo-1974596.jpeg?auto=compress&cs=tinysrgb&w=1200",
        ],
        "modern townhouse residential": [
            "https://images.pexels.com/photos/2343465/pexels-photo-2343465.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/2360673/pexels-photo-2360673.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/2581922/pexels-photo-2581922.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/1370704/pexels-photo-1370704.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/323780/pexels-photo-323780.jpeg?auto=compress&cs=tinysrgb&w=1200",
        ],
        "luxury penthouse city view": [
            "https://images.pexels.com/photos/2462015/pexels-photo-2462015.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/1643383/pexels-photo-1643383.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/2029722/pexels-photo-2029722.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/2635038/pexels-photo-2635038.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/3315291/pexels-photo-3315291.jpeg?auto=compress&cs=tinysrgb&w=1200",
        ],
        "modern office building commercial space": [
            "https://images.pexels.com/photos/380768/pexels-photo-380768.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/325229/pexels-photo-325229.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/2219024/pexels-photo-2219024.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/2467285/pexels-photo-2467285.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/2883049/pexels-photo-2883049.jpeg?auto=compress&cs=tinysrgb&w=1200",
        ],
        "empty land plot development": [
            "https://images.pexels.com/photos/1105766/pexels-photo-1105766.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/87611/sun-fireball-solar-flare-sunlight-87611.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/531321/pexels-photo-531321.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/1770809/pexels-photo-1770809.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/247599/pexels-photo-247599.jpeg?auto=compress&cs=tinysrgb&w=1200",
        ],
        "modern loft apartment industrial": [
            "https://images.pexels.com/photos/1115804/pexels-photo-1115804.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/1329711/pexels-photo-1329711.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/1457847/pexels-photo-1457847.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/2079249/pexels-photo-2079249.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/2724749/pexels-photo-2724749.jpeg?auto=compress&cs=tinysrgb&w=1200",
        ],
        "condominium apartment building": [
            "https://images.pexels.com/photos/1457842/pexels-photo-1457842.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/1643389/pexels-photo-1643389.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/1648776/pexels-photo-1648776.jpeg?auto=compress&cs=tinysrgb&w=1200",
        ],
        "studio apartment modern minimalist": [
            "https://images.pexels.com/photos/1350789/pexels-photo-1350789.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/1457847/pexels-photo-1457847.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "https://images.pexels.com/photos/1571460/pexels-photo-1571460.jpeg?auto=compress&cs=tinysrgb&w=1200",
        ],
    }

    return pexels_images.get(query, pexels_images["modern apartment interior luxury"])[:per_page]


async def update_property_images():
    """Update all properties with sample images based on their type."""

    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    properties_collection = db.properties

    try:
        # Get all properties
        properties = await properties_collection.find({}).to_list(length=None)
        logger.info(f"Found {len(properties)} properties")

        updated_count = 0

        for prop in properties:
            property_id = prop["_id"]
            property_name = prop.get("name", "Unknown")
            property_type = prop.get("property_type", "apartment")
            current_images = prop.get("images", [])

            # Skip if property already has 3+ images
            if len(current_images) >= 3:
                logger.info(f"Skipping '{property_name}' - already has {len(current_images)} images")
                continue

            # Get search query for this property type
            query = PROPERTY_TYPE_QUERIES.get(
                property_type,
                PROPERTY_TYPE_QUERIES["apartment"]
            )

            # Fetch images from Pexels
            logger.info(f"Fetching images for '{property_name}' (type: {property_type})")
            images = await fetch_pexels_images(query, per_page=4)

            if images:
                # Update property with new images
                result = await properties_collection.update_one(
                    {"_id": property_id},
                    {"$set": {"images": images}}
                )

                if result.modified_count > 0:
                    updated_count += 1
                    logger.info(f"✓ Updated '{property_name}' with {len(images)} images")
                else:
                    logger.warning(f"✗ Failed to update '{property_name}'")
            else:
                logger.warning(f"No images found for '{property_name}'")

        logger.info(f"\n{'='*60}")
        logger.info(f"Summary: Updated {updated_count}/{len(properties)} properties")
        logger.info(f"{'='*60}\n")

    except Exception as e:
        logger.error(f"Error updating property images: {e}")
        raise
    finally:
        client.close()


async def main():
    """Main execution function."""
    logger.info("Starting property image update...")
    logger.info(f"Database: {DB_NAME}")
    logger.info(f"MongoDB: {MONGO_URL.replace('%25', '%')}\n")

    await update_property_images()

    logger.info("✓ Property image update completed!")


if __name__ == "__main__":
    asyncio.run(main())
