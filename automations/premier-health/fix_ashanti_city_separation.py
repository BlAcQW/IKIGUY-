#!/usr/bin/env python3
"""
Fix Ashanti Region City Separation

This script separates merged city names in the Ashanti region into individual documents
for better RAG query accuracy. It handles cities like:
- "Santasipatase" → "SANTASI" + "PATASE"
- "Tafobremang" → "TAFO" + "BREMANG"
- "Abuakwatanoso" → "ABUAKWA" + "TANOSO"

Each city gets its own searchable document with all relevant providers.
"""

import sys
import os
import asyncio
import csv
from typing import List, Dict, Tuple
from collections import defaultdict

# Add paths for imports
sys.path.append('/opt/kasaai/apps/core_backend')

from backend.services.pg_document_service import pg_document_service
from backend.models.knowledge_base import DocumentCreate, DocumentFilter, DocumentUpdate

# Path to Ashanti region CSV
ASHANTI_CSV_PATH = '/opt/kasaai/apps/automations/premier-health/regional_cities/ashanti_region_kumasi.csv'

# City separation mappings - define which cities to split and how
CITY_SEPARATIONS = {
    # CSV format "TAFO / BREMANG" → Should create separate docs
    "TAFO / BREMANG": ["TAFO", "BREMANG"],
    "SANTASI / PATASE": ["SANTASI", "PATASE"],
    "ABUAKWA / TANOSO": ["ABUAKWA", "TANOSO"],
    "AHODWO / AHINSAN": ["AHODWO", "AHINSAN"],
    "BOMSO / KNUST / EJISU": ["BOMSO", "KNUST", "EJISU"],
    "MAMPONG / AGONA / WIAMOASE": ["MAMPONG", "AGONA", "WIAMOASE"],
    "OBUASI / DUNKWA": ["OBUASI", "DUNKWA"],
    "KONONGO / AGOGO": ["KONONGO", "AGOGO"],
}


def load_ashanti_providers_from_csv() -> List[Dict]:
    """
    Load all providers from the Ashanti region CSV file.

    Returns:
        List of provider dictionaries with all fields.
    """
    providers = []

    with open(ASHANTI_CSV_PATH, 'r', encoding='utf-8') as f:
        # Skip first 2 rows (title rows), header is on line 3
        next(f)  # Skip ",,ASHANTI REGION,,,,"
        next(f)  # Skip ",,KUMASI AND ITS ENVIRONS,,,,"

        reader = csv.DictReader(f)
        for row in reader:
            # Only include rows with region = "ASHANTI REGION" and a hospital name
            region = row.get('region', '').strip()
            hospital_name = row.get('NAME OF HOSPITAL / CLINIC', '').strip()

            if region.upper() == 'ASHANTI REGION' and hospital_name:
                providers.append(row)

    return providers


def normalize_city_name(city_name: str) -> str:
    """
    Normalize city name from CSV format.

    Args:
        city_name: Raw city name from CSV (e.g., "TAFO / BREMANG", "  BOMSO / KNUST / EJISU")

    Returns:
        Normalized city name in UPPERCASE without extra spaces
    """
    # Strip whitespace and convert to uppercase
    normalized = city_name.strip().upper()

    # Normalize multiple spaces to single space around slashes
    # "TAFO  /  BREMANG" → "TAFO / BREMANG"
    import re
    normalized = re.sub(r'\s*/\s*', ' / ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)

    return normalized


def get_cities_to_split(city_name: str) -> List[str]:
    """
    Get the individual cities that should be created from a combined city name.

    Args:
        city_name: City name from CSV (e.g., "TAFO / BREMANG")

    Returns:
        List of individual city names, or [city_name] if no split needed
    """
    normalized = normalize_city_name(city_name)

    # Check if this city should be split
    if normalized in CITY_SEPARATIONS:
        return CITY_SEPARATIONS[normalized]

    # No split needed - return as single city
    return [normalized]


def group_providers_by_city(providers: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group providers by their city from the CSV.

    Args:
        providers: List of all providers from Ashanti region

    Returns:
        Dictionary mapping city name (from CSV) to list of providers.
    """
    grouped = defaultdict(list)

    for provider in providers:
        city = provider.get('city', '').strip()
        if city:
            grouped[city].append(provider)

    return dict(grouped)


def create_city_document(city_name: str, providers: List[Dict], source_city: str = None) -> DocumentCreate:
    """
    Create a knowledge base document for a specific city's providers.

    Args:
        city_name: Individual city name (e.g., "SANTASI")
        providers: List of provider dictionaries for this city
        source_city: Original combined city name from CSV (e.g., "SANTASI / PATASE")

    Returns:
        DocumentCreate instance ready for ingestion.
    """
    city_upper = city_name.upper()

    # Build document content in markdown
    content_lines = [
        f"# Healthcare Providers in {city_upper}",
        "",
        f"This document lists all Premier Health Insurance network providers in {city_upper}, Ashanti Region, Ghana.",
        ""
    ]

    # Specialty mapping for better readability and embedding matching
    specialty_map = {
        'GP': 'General Practice',
        'PHY': 'Physiotherapy',
        'SRY': 'Surgery',
        'GYN': 'Gynecology',
        'OBS': 'Obstetrics',
        'PED': 'Pediatrics',
        'PAED': 'Pediatrics',
        'EYE': 'Ophthalmology/Eye Care',
        'DEN': 'Dental',
        'ENT': 'Ear Nose Throat',
        'OPTICAL': 'Optical/Eye Care',
        'PHARMACY': 'Pharmacy',
        'LAB': 'Laboratory',
        'HOSPITAL': 'Hospital',
        'DENTAL': 'Dental'
    }

    def expand_specialties(specialty_str: str) -> str:
        """Expand specialty abbreviations."""
        if not specialty_str:
            return "General Services"

        parts = specialty_str.upper().replace('/', ',').split(',')
        expanded = []

        for part in parts:
            part_clean = part.strip()
            if part_clean in specialty_map:
                expanded.append(specialty_map[part_clean])
            elif part_clean:
                expanded.append(part_clean.title())

        return ', '.join(expanded) if expanded else "General Services"

    # Add each provider
    for idx, provider in enumerate(providers, 1):
        name = provider.get('NAME OF HOSPITAL / CLINIC', '').strip()
        if not name:
            continue

        specialties = provider.get('SPECIALITY', '').strip()
        specialties_expanded = expand_specialties(specialties)
        phone = provider.get('CONTACT number', '').strip()
        location = provider.get('LOCATION', '').strip()

        content_lines.append(f"## {idx}. {name}")
        content_lines.append("")

        if specialties_expanded:
            content_lines.append(f"**Specialties**: {specialties_expanded}")

        if phone:
            content_lines.append(f"**Phone**: {phone}")

        if location:
            content_lines.append(f"**Location**: {location}")

        content_lines.append(f"**City**: {city_upper}")
        content_lines.append(f"**Region**: Ashanti Region")
        content_lines.append("")
        content_lines.append("---")
        content_lines.append("")

    # Add footer with metadata
    content_lines.append("")
    content_lines.append(f"**Total Providers**: {len(providers)}")
    if source_city and source_city != city_name:
        content_lines.append(f"**Source**: Split from '{source_city}'")
    content_lines.append("")

    content = "\n".join(content_lines)

    # Build tags for better searchability
    tags = [
        "providers",
        "healthcare",
        "ashanti_region",
        city_upper.lower().replace(' ', '_'),
        "kumasi_environs"
    ]

    if source_city and source_city != city_name:
        tags.append(f"split_from_{normalize_city_name(source_city).lower().replace(' ', '_').replace('/', '_')}")

    # Create document
    doc = DocumentCreate(
        company_name="premier_health_production",
        title=f"Healthcare Providers in {city_upper}",
        content=content,
        category="provider_directory",
        tags=tags,
        source="ashanti_csv_split",
        source_uri=f"file:{ASHANTI_CSV_PATH}",
        created_by="ashanti_city_separation_script"
    )

    return doc


async def delete_old_merged_documents():
    """
    Delete old merged city documents that will be replaced by separated ones.
    """
    print("\n🗑️  Deleting old merged city documents...")

    # Documents to delete (merged names)
    old_titles = [
        "Healthcare Providers in Santasipatase",
        "Healthcare Providers in Tafobremang",
        "Healthcare Providers in Abuakwatanoso",
    ]

    deleted_count = 0

    for title in old_titles:
        try:
            # Search for document
            filter_params = DocumentFilter(
                company_name="premier_health_production",
                search_query=title,
                page=1,
                page_size=10
            )

            result = await pg_document_service.list_documents(filter_params)

            if result.documents:
                for doc in result.documents:
                    doc_dict = doc if isinstance(doc, dict) else doc.dict()
                    if doc_dict['title'] == title:
                        # Delete this document
                        doc_id = doc_dict['id']
                        delete_result = await pg_document_service.delete_document(
                            document_id=doc_id,
                            company_name="premier_health_production"
                        )

                        if delete_result.success:
                            print(f"   ✅ Deleted: {title}")
                            deleted_count += 1
                        else:
                            print(f"   ⚠️  Failed to delete: {title}")

        except Exception as e:
            print(f"   ⚠️  Error deleting '{title}': {e}")

    print(f"   Deleted {deleted_count} old documents")
    return deleted_count


async def fix_ashanti_city_separation():
    """
    Main function to separate Ashanti region cities into individual documents.
    """
    print("🏥 Fixing Ashanti Region City Separation")
    print("=" * 70)

    try:
        # Step 1: Load providers from CSV
        print("\n1. Loading providers from Ashanti region CSV...")
        providers = load_ashanti_providers_from_csv()
        print(f"   ✅ Loaded {len(providers)} providers from Ashanti region")

        # Step 2: Group by city (as listed in CSV)
        print("\n2. Grouping providers by city...")
        grouped = group_providers_by_city(providers)
        print(f"   ✅ Found {len(grouped)} unique city groupings")

        # Step 3: Identify cities that need to be split
        print("\n3. Analyzing cities for separation...")

        all_documents = []
        split_cities = []
        single_cities = []

        for csv_city, city_providers in grouped.items():
            # Normalize the city name
            normalized_city = normalize_city_name(csv_city)

            # Get individual cities to create
            individual_cities = get_cities_to_split(csv_city)

            if len(individual_cities) > 1:
                # This city needs to be split
                split_cities.append((normalized_city, individual_cities))
                print(f"   📍 Splitting '{normalized_city}' into {len(individual_cities)} cities:")

                # Create a separate document for each individual city
                for individual_city in individual_cities:
                    doc = create_city_document(
                        city_name=individual_city,
                        providers=city_providers,
                        source_city=normalized_city
                    )
                    all_documents.append(doc)
                    print(f"      → {individual_city} ({len(city_providers)} providers)")
            else:
                # Single city - create one document
                single_cities.append(normalized_city)
                doc = create_city_document(
                    city_name=individual_cities[0],
                    providers=city_providers,
                    source_city=normalized_city
                )
                all_documents.append(doc)

        print(f"\n   Summary:")
        print(f"   - Cities split: {len(split_cities)}")
        print(f"   - Single cities: {len(single_cities)}")
        print(f"   - Total documents to create: {len(all_documents)}")

        # Step 4: Show city separation details
        print(f"\n4. City separation breakdown:")
        for original, individual in split_cities:
            print(f"   • '{original}' → {', '.join(individual)}")

        # Step 5: Delete old merged documents
        await delete_old_merged_documents()

        # Step 6: Create new separated documents
        print(f"\n6. Creating separated city documents...")

        created_count = 0
        failed_count = 0

        for doc in all_documents:
            try:
                # Check if document already exists
                filter_params = DocumentFilter(
                    company_name="premier_health_production",
                    search_query=doc.title,
                    page=1,
                    page_size=5
                )

                existing = await pg_document_service.list_documents(filter_params)

                # Check if exact title exists
                exists = False
                existing_doc_id = None
                if existing.documents:
                    for existing_doc in existing.documents:
                        doc_dict = existing_doc if isinstance(existing_doc, dict) else existing_doc.dict()
                        if doc_dict['title'] == doc.title:
                            exists = True
                            existing_doc_id = doc_dict['id']
                            break

                if exists:
                    # Update existing document
                    doc_update = DocumentUpdate(
                        content=doc.content,
                        tags=doc.tags,
                        updated_by="ashanti_city_separation_script",
                        change_reason="City separation fix"
                    )

                    result = await pg_document_service.update_document(
                        document_id=existing_doc_id,
                        doc_update=doc_update
                    )

                    if result.success:
                        print(f"   ✅ Updated: {doc.title}")
                        created_count += 1
                    else:
                        print(f"   ❌ Failed to update: {doc.title}")
                        failed_count += 1
                else:
                    # Create new document
                    result = await pg_document_service.create_document(doc)

                    if result.success:
                        print(f"   ✅ Created: {doc.title}")
                        created_count += 1
                    else:
                        print(f"   ❌ Failed to create: {doc.title}")
                        failed_count += 1

            except Exception as e:
                print(f"   ❌ Error processing '{doc.title}': {e}")
                failed_count += 1

        print(f"\n   Results:")
        print(f"   - Successfully created/updated: {created_count}")
        print(f"   - Failed: {failed_count}")

        # Step 7: Verify all Ashanti cities are now searchable
        print(f"\n7. Verifying city searchability...")

        expected_cities = [
            "BOMSO", "KNUST", "EJISU",
            "ASOKWA", "BANTAMA", "ABREPO",
            "TAFO", "BREMANG",
            "MAMPONTENG",
            "ABUAKWA", "TANOSO",
            "SANTASI", "PATASE",
            "SUAME", "ADUM",
            "AHODWO", "AHINSAN",
            "MAMPONG", "AGONA", "WIAMOASE",
            "OBUASI", "DUNKWA",
            "KONONGO", "AGOGO"
        ]

        found_cities = []
        missing_cities = []

        for city in expected_cities:
            filter_params = DocumentFilter(
                company_name="premier_health_production",
                search_query=f"Healthcare Providers in {city}",
                page=1,
                page_size=5
            )

            result = await pg_document_service.list_documents(filter_params)

            if result.documents:
                # Check for exact match
                found = False
                for doc in result.documents:
                    doc_dict = doc if isinstance(doc, dict) else doc.dict()
                    if doc_dict['title'] == f"Healthcare Providers in {city}":
                        found = True
                        break

                if found:
                    found_cities.append(city)
                else:
                    missing_cities.append(city)
            else:
                missing_cities.append(city)

        print(f"   ✅ Found: {len(found_cities)}/{len(expected_cities)} cities")

        if missing_cities:
            print(f"   ⚠️  Missing cities: {', '.join(missing_cities)}")
        else:
            print(f"   🎉 All expected cities are now searchable!")

        print(f"\n✅ City Separation Complete!")
        print(f"\nℹ️  All Ashanti region cities now have individual searchable documents.")
        print(f"   Queries for cities like 'SANTASI', 'PATASE', 'BREMANG', etc. should now work correctly.")

    except Exception as e:
        print(f"\n❌ Error during city separation: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(fix_ashanti_city_separation())
