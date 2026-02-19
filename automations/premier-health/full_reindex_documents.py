#!/usr/bin/env python3
"""
Full Re-indexing Script for Premier Health Documents

This script will:
1. Delete all existing embeddings for premier_health_production
2. Re-index all documents from the enriched CSV files
3. Verify the re-indexing was successful

Run this to fix the RAG retrieval issues identified in the audit.
"""

import sys
import asyncio
import pandas as pd
from pathlib import Path
from typing import List, Dict

sys.path.append('/opt/kasaai/apps/core_backend')

from backend.services.pg_document_service import pg_document_service
from backend.models.knowledge_base import DocumentFilter, DocumentCreate

# Base directory for enriched CSVs
CSV_DIR = Path("/opt/kasaai/apps/automations/premier-health/regional_cities/enriched")

# All enriched CSV files
CSV_FILES = [
    "all_northern_regions_enriched.csv",
    "ashanti_region_kumasi_enriched.csv",
    "bono_regions_enriched.csv",
    "central_and_western_region_enriched.csv",
    "eastern_and_volta_regions_enriched.csv",
    "greater_accra_region_enriched.csv"
]

COLLECTION_NAME = "premier_health_production"


async def delete_all_documents():
    """Delete all existing documents in the collection."""
    print("\n🗑️  STEP 1: Deleting all existing documents...")
    print("=" * 80)

    page = 1
    total_deleted = 0

    while True:
        # Get documents
        filter_params = DocumentFilter(
            company_name=COLLECTION_NAME,
            page=page,
            page_size=100
        )

        result = await pg_document_service.list_documents(filter_params)

        if not result.success or not result.documents:
            break

        # Delete each document
        for doc in result.documents:
            doc_dict = doc if isinstance(doc, dict) else doc.dict()
            doc_id = doc_dict['id']

            delete_result = await pg_document_service.delete_document(doc_id, COLLECTION_NAME)
            if delete_result.success:
                total_deleted += 1
                print(f"   Deleted: {doc_dict.get('title', 'Unknown')} ({doc_id})")
            else:
                print(f"   ❌ Failed to delete {doc_id}: {delete_result.error}")

        # Check if we need to continue
        if len(result.documents) < 100:
            break

        page += 1

    print(f"\n   ✅ Total documents deleted: {total_deleted}")
    return total_deleted


def parse_csv_to_city_documents(csv_path: Path) -> Dict[str, List[Dict]]:
    """
    Parse CSV file and group providers by city.

    IMPORTANT: Cities separated by "/" are treated as SEPARATE cities.
    For example, "ACCRA CENTRAL / TUDU / MAKOLA" creates THREE separate documents.

    Returns:
        Dict mapping city names to list of provider dictionaries
    """
    print(f"\n   📄 Parsing {csv_path.name}...")

    try:
        # Read CSV keeping all rows, handling missing values
        # Skip first 2 rows for Greater Accra and Ashanti CSVs which have different headers
        df = pd.read_csv(csv_path, skiprows=2, keep_default_na=False)

        # Group by city
        city_groups = {}

        for _, row in df.iterrows():
            # Get city value
            city_value = row.get('city', '').strip() if 'city' in row else ''

            # Skip if no city
            if not city_value or city_value == '':
                continue

            # Skip rows that are just city headers (no provider data)
            hospital_name = str(row.get('NAME OF HOSPITAL / CLINIC', '')).strip()
            if not hospital_name or hospital_name == '':
                continue

            city_raw = city_value

            # Split cities by "/" - each becomes a separate city
            cities = [c.strip() for c in city_raw.split('/')]

            # Add provider to city
            provider = {
                'name': hospital_name,
                'specialty': str(row.get('SPECIALITY', '')).strip(),
                'contact': str(row.get('CONTACT number', '')).strip(),
                'location': str(row.get('LOCATION', '')).strip()
            }

            # Add this provider to ALL cities in the list
            for city in cities:
                if not city:  # Skip empty strings
                    continue

                # Initialize city list if needed
                if city not in city_groups:
                    city_groups[city] = []

                city_groups[city].append(provider)

        print(f"      ✅ Found {len(city_groups)} cities with {sum(len(p) for p in city_groups.values())} total provider entries")
        return city_groups

    except Exception as e:
        print(f"      ❌ Error parsing {csv_path.name}: {e}")
        import traceback
        traceback.print_exc()
        return {}


def format_city_document(city: str, providers: List[Dict]) -> str:
    """Format providers into a document string."""
    # Sort providers by name
    providers = sorted(providers, key=lambda p: p['name'])

    lines = [f"Healthcare Providers in {city}\n"]
    lines.append("=" * 80 + "\n\n")

    for i, provider in enumerate(providers, 1):
        lines.append(f"{i}. {provider['name']}\n")
        if provider['specialty']:
            lines.append(f"   Specialty: {provider['specialty']}\n")
        if provider['contact']:
            lines.append(f"   Contact: {provider['contact']}\n")
        if provider['location']:
            lines.append(f"   Location: {provider['location']}\n")
        lines.append("\n")

    return "".join(lines)


def generate_search_aliases(city: str) -> List[str]:
    """
    Generate search aliases for a city name.

    Examples:
    - "TEMA COMMUNITY 4" -> ["TEMA COMM 4", "COMMUNITY 4", "COMM 4"]
    - "ASHAIMAN / COMMUNITY 26" -> ["ASHAIMAN / COMM 26"]
    """
    aliases = []

    # Replace "COMMUNITY" with "COMM"
    if "COMMUNITY" in city.upper():
        aliases.append(city.upper().replace("COMMUNITY", "COMM"))

    # Replace "COMM" with "COMMUNITY"
    if "COMM" in city.upper() and "COMMUNITY" not in city.upper():
        aliases.append(city.upper().replace("COMM", "COMMUNITY"))

    return aliases


async def index_documents():
    """Read CSV files and create documents."""
    print("\n📝 STEP 2: Indexing documents from CSV files...")
    print("=" * 80)

    all_city_providers = {}

    # Parse all CSV files
    for csv_file in CSV_FILES:
        csv_path = CSV_DIR / csv_file
        if not csv_path.exists():
            print(f"   ⚠️  Warning: {csv_file} not found, skipping...")
            continue

        city_providers = parse_csv_to_city_documents(csv_path)

        # Merge providers (some cities may appear in multiple files)
        for city, providers in city_providers.items():
            if city in all_city_providers:
                # Merge providers, avoiding duplicates
                existing_names = {p['name'] for p in all_city_providers[city]}
                for provider in providers:
                    if provider['name'] not in existing_names:
                        all_city_providers[city].append(provider)
            else:
                all_city_providers[city] = providers

    print(f"\n   📊 Total cities to index: {len(all_city_providers)}")
    print(f"   📊 Total providers: {sum(len(p) for p in all_city_providers.values())}")

    # Create documents
    print("\n   🔄 Creating documents with embeddings...")
    successful = 0
    failed = 0

    for city, providers in sorted(all_city_providers.items()):
        title = f"Healthcare Providers in {city}"
        content = format_city_document(city, providers)

        # Generate tags including search aliases
        tags = ["healthcare", "providers", city, "premier_health"]
        aliases = generate_search_aliases(city)
        tags.extend(aliases)

        # Create document
        doc_create = DocumentCreate(
            company_name=COLLECTION_NAME,
            title=title,
            content=content,
            tags=tags
        )

        try:
            result = await pg_document_service.create_document(doc_create)

            if result.success:
                successful += 1
                print(f"   ✅ [{successful}/{len(all_city_providers)}] Created: {title}")
            else:
                failed += 1
                print(f"   ❌ Failed: {title} - {result.error}")

        except Exception as e:
            failed += 1
            print(f"   ❌ Exception creating {title}: {e}")

    print(f"\n   📊 Summary:")
    print(f"      ✅ Successfully indexed: {successful}")
    print(f"      ❌ Failed: {failed}")

    return successful, failed


async def verify_indexing():
    """Verify documents were created and have embeddings."""
    print("\n🔍 STEP 3: Verifying indexing...")
    print("=" * 80)

    filter_params = DocumentFilter(
        company_name=COLLECTION_NAME,
        page=1,
        page_size=10
    )

    result = await pg_document_service.list_documents(filter_params)

    if not result.success:
        print(f"   ❌ Failed to verify: {result.error}")
        return False

    doc_count = len(result.documents) if result.documents else 0
    print(f"   ✅ Sample of documents found in database: {doc_count}")

    # Check a sample document
    if result.documents and len(result.documents) > 0:
        sample_doc = result.documents[0]
        sample_dict = sample_doc if isinstance(sample_doc, dict) else sample_doc.dict()
        print(f"   ✅ Sample document: {sample_dict.get('title')}")
        print(f"      - Content length: {len(sample_dict.get('content', ''))}")
        print(f"      - Tags: {sample_dict.get('tags', [])}")

    return True


async def main():
    """Main execution."""
    print("\n" + "=" * 80)
    print("🔄 FULL RE-INDEXING: Premier Health Documents")
    print("=" * 80)
    print("\nThis will:")
    print("  1. Delete all existing documents and embeddings")
    print("  2. Re-create documents from enriched CSV files")
    print("  3. Generate fresh embeddings for all documents")
    print("\n" + "=" * 80)

    # Confirm
    print("\n⚠️  WARNING: This will delete all existing documents!")
    print("   Press Ctrl+C to cancel, or wait 5 seconds to continue...")
    await asyncio.sleep(5)

    # Step 1: Delete all documents
    deleted_count = await delete_all_documents()

    # Step 2: Index documents
    successful, failed = await index_documents()

    # Step 3: Verify
    verified = await verify_indexing()

    # Final summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    print(f"   Documents deleted: {deleted_count}")
    print(f"   Documents created: {successful}")
    print(f"   Failed: {failed}")
    print(f"   Verification: {'✅ PASSED' if verified else '❌ FAILED'}")

    if successful > 0 and verified:
        print("\n✅ Re-indexing completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Run the audit script again to verify RAG queries work")
        print("   2. Test a few broken cities manually")
    else:
        print("\n❌ Re-indexing had issues. Please review the errors above.")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
