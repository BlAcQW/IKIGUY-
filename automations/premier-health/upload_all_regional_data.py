#!/usr/bin/env python3
"""
Upload ALL regional Premier Health data from enriched CSV files to database.

This script processes all 6 regional CSV files:
1. Greater Accra (already uploaded, will check for duplicates)
2. Northern Regions (TAMALE, WA, BOLGATANGA)
3. Ashanti Region (KUMASI, OBUASI)
4. Bono Regions (SUNYANI, TECHIMAN)
5. Central & Western (CAPE COAST, TAKORADI)
6. Eastern & Volta (KOFORIDUA, HO)

Author: Claude Code
Date: October 21, 2025
"""

import sys
import os
import asyncio
import logging
import csv
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
CSV_DIR = Path("/opt/kasaai/apps/automations/premier-health/regional_cities/enriched")
COLLECTION_NAME = "helpdesk_premier_health_production"  # Fixed: was "premier_health_production"

# Regional CSV files
REGIONAL_FILES = [
    "greater_accra_region_enriched.csv",
    "all_northern_regions_enriched.csv",
    "ashanti_region_kumasi_enriched.csv",
    "bono_regions_enriched.csv",
    "central_and_western_region_enriched.csv",
    "eastern_and_volta_regions_enriched.csv"
]


def parse_csv_file(filepath: Path) -> Dict[str, List[Dict]]:
    """
    Parse enriched CSV file and group providers by city.

    IMPORTANT: Splits compound city names (e.g., "BOMSO / KNUST / EJISU" → 3 cities)

    Args:
        filepath: Path to CSV file

    Returns:
        Dictionary mapping city names to provider lists
    """
    cities_data = {}

    with open(filepath, 'r', encoding='utf-8') as f:
        # Read all lines
        lines = f.readlines()

        # Find the header row
        header_index = 0
        for i, line in enumerate(lines):
            if line.startswith('region,city'):
                header_index = i
                break

        # Parse from header row onwards
        from io import StringIO
        csv_content = ''.join(lines[header_index:])
        csv_file = StringIO(csv_content)
        reader = csv.DictReader(csv_file)

        for row in reader:
            city = row.get('city', '').strip().upper()

            # Skip header rows or empty cities
            if not city or city == row.get('region', '').upper():
                continue

            # Extract provider data
            provider = {
                'name': row.get('NAME OF HOSPITAL / CLINIC', '').strip(),
                'specialty': row.get('SPECIALITY', '').strip(),
                'contact': row.get('CONTACT number', '').strip(),
                'location': row.get('LOCATION', '').strip(),
                'region': row.get('region', '').strip()
            }

            # Only add if we have actual provider data
            if provider['name']:
                # Split compound cities (e.g., "BOMSO / KNUST / EJISU" → ["BOMSO", "KNUST", "EJISU"])
                if '/' in city:
                    individual_cities = [c.strip() for c in city.split('/')]
                else:
                    individual_cities = [city]

                # Add provider to each individual city
                for individual_city in individual_cities:
                    if not individual_city:  # Skip empty strings
                        continue
                    if individual_city not in cities_data:
                        cities_data[individual_city] = []
                    cities_data[individual_city].append(provider)

    return cities_data


def format_city_document(city: str, providers: List[Dict], region: str) -> str:
    """
    Format city providers into markdown document.

    Args:
        city: City name
        providers: List of provider dictionaries
        region: Region name

    Returns:
        Formatted markdown content
    """
    content = f"# Healthcare Providers in {city}\n\n"
    content += f"This document lists all Premier Health Insurance network providers in {city}, Ghana.\n\n"

    for i, provider in enumerate(providers, 1):
        content += f"## {provider['name']}\n"
        if provider['specialty']:
            content += f"**Specialties**: {provider['specialty']}\n"
        if provider['contact']:
            content += f"**Phone**: {provider['contact']}\n"
        if provider['location']:
            content += f"**Location**: {provider['location']}\n"
        content += f"**Region**: {city}\n"
        content += "\n---\n\n"

    return content


async def upload_regional_file(filepath: Path) -> Dict[str, Any]:
    """
    Upload all cities from a regional CSV file.

    Args:
        filepath: Path to regional CSV file

    Returns:
        Upload statistics
    """
    logger.info(f"📁 Processing: {filepath.name}")

    # Parse CSV
    cities_data = parse_csv_file(filepath)
    logger.info(f"   Found {len(cities_data)} cities with {sum(len(p) for p in cities_data.values())} providers")

    # Track results
    uploaded = 0
    skipped = 0
    errors = 0

    # Upload each city
    for city, providers in cities_data.items():
        try:
            # Create document content
            region = providers[0]['region'] if providers else 'Unknown'
            content = format_city_document(city, providers, region)

            # Create content hash for deduplication
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            # Create document
            doc = DocumentCreate(
                company_name=COLLECTION_NAME,
                title=f"Healthcare Providers in {city}",
                content=content,
                content_hash=content_hash,
                category="provider_directory",
                source="regional_csv_enriched",
                tags=["providers", "healthcare", city.lower(), f"region_{region.lower().replace(' ', '_')}"],
                metadata={
                    "city": city,
                    "region": region,
                    "provider_count": len(providers),
                    "source_file": filepath.name
                }
            )

            # Upload to database
            result = await pg_document_service.create_document(doc)

            if result.success:
                uploaded += 1
                logger.info(f"   ✅ {city}: {len(providers)} providers uploaded")
            else:
                if "duplicate" in str(result.error).lower():
                    skipped += 1
                    logger.info(f"   ⏭️  {city}: Already exists (skipped)")
                else:
                    errors += 1
                    logger.error(f"   ❌ {city}: {result.error}")

        except Exception as e:
            errors += 1
            logger.error(f"   ❌ {city}: {str(e)}")

    return {
        "file": filepath.name,
        "cities": len(cities_data),
        "uploaded": uploaded,
        "skipped": skipped,
        "errors": errors
    }


async def main():
    """
    Main upload workflow for all regional data.
    """
    logger.info("=" * 80)
    logger.info("🌍 PREMIER HEALTH - UPLOAD ALL REGIONAL DATA")
    logger.info("=" * 80)
    logger.info(f"CSV Directory: {CSV_DIR}")
    logger.info(f"Collection: {COLLECTION_NAME}")
    logger.info("=" * 80)

    all_results = []

    # Process each regional file
    for filename in REGIONAL_FILES:
        filepath = CSV_DIR / filename

        if not filepath.exists():
            logger.error(f"❌ File not found: {filepath}")
            continue

        try:
            result = await upload_regional_file(filepath)
            all_results.append(result)
            logger.info("")  # Blank line between files

        except Exception as e:
            logger.error(f"❌ Failed to process {filename}: {str(e)}")
            import traceback
            traceback.print_exc()

    # Summary
    logger.info("=" * 80)
    logger.info("📊 UPLOAD SUMMARY")
    logger.info("=" * 80)

    total_cities = sum(r['cities'] for r in all_results)
    total_uploaded = sum(r['uploaded'] for r in all_results)
    total_skipped = sum(r['skipped'] for r in all_results)
    total_errors = sum(r['errors'] for r in all_results)

    for result in all_results:
        logger.info(f"\n📁 {result['file']}")
        logger.info(f"   Cities: {result['cities']}")
        logger.info(f"   Uploaded: {result['uploaded']}")
        logger.info(f"   Skipped: {result['skipped']}")
        logger.info(f"   Errors: {result['errors']}")

    logger.info(f"\n" + "=" * 80)
    logger.info(f"🎯 TOTALS")
    logger.info(f"=" * 80)
    logger.info(f"Total cities: {total_cities}")
    logger.info(f"Newly uploaded: {total_uploaded}")
    logger.info(f"Already existed: {total_skipped}")
    logger.info(f"Errors: {total_errors}")
    logger.info("=" * 80)

    if total_errors == 0:
        logger.info("✅ ALL REGIONAL DATA UPLOADED SUCCESSFULLY!")
    else:
        logger.warning(f"⚠️  Completed with {total_errors} errors")

    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
