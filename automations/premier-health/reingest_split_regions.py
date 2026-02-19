#!/usr/bin/env python3
"""
Re-ingest Premier Health provider data with split regions.
Splits combined city names (e.g., "Obuasi  Dunkwa") into separate documents for each city.
This improves RAG query accuracy when users ask about specific cities.
"""

import sys
import os
import asyncio
import csv
from typing import List, Dict
from collections import defaultdict

# Add paths for imports
sys.path.append('/opt/kasaai/apps/core_backend')

from backend.services.helpdesk_rag_service import helpdesk_rag_service, KnowledgeDocument

# Path to master CSV
MASTER_CSV_PATH = '/opt/kasaai/apps/automations/premier-health/data/premier_health_master_provider_list.csv'


def load_providers_from_csv() -> List[Dict]:
    """
    Load all providers from the master CSV file.

    Returns:
        List of provider dictionaries with all fields.
    """
    providers = []

    with open(MASTER_CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            providers.append(row)

    return providers


def split_region_name(region: str) -> List[str]:
    """
    Split combined region names into individual cities.

    Args:
        region: Region name (e.g., "Obuasi  Dunkwa", "Accra Central  Tudu  Makola")

    Returns:
        List of individual city names.

    Examples:
        >>> split_region_name("Obuasi  Dunkwa")
        ['Obuasi', 'Dunkwa']
        >>> split_region_name("Madina")
        ['Madina']
    """
    # Check if region contains double spaces (indicates combined cities)
    if '  ' in region:
        # Split by double spaces and clean each part
        cities = [city.strip() for city in region.split('  ') if city.strip()]
        return cities
    else:
        # Single city
        return [region.strip()]


def create_provider_document(city: str, providers: List[Dict], original_region: str = None) -> KnowledgeDocument:
    """
    Create a knowledge document for a specific city's providers.

    Args:
        city: City name
        providers: List of provider dictionaries
        original_region: Original combined region name (for reference)

    Returns:
        KnowledgeDocument instance.
    """
    # Normalize city name to UPPERCASE to match STT normalizer output
    # Reason: CityNormalizer returns UPPERCASE names (e.g., "MADINA", "OBUASI")
    city_upper = city.upper()

    # Build document content
    content_lines = [
        f"# Healthcare Providers in {city_upper}",
        "",
        f"This document lists all Premier Health Insurance network providers in {city_upper}, Ghana.",
        ""
    ]

    # Specialty abbreviation mapping for better embedding matching
    specialty_expansions = {
        'GP': 'General Practice (GP)',
        'PHY': 'Physiotherapy (PHY)',
        'SRY': 'Surgery (SRY)',
        'GYN': 'Gynecology (GYN)',
        'OBS': 'Obstetrics (OBS)',
        'PED': 'Pediatrics (PED)',
        'PAED': 'Pediatrics (PAED)',
        'DEN': 'Dental (DEN)',
        'PHARMACY': 'Pharmacy',
        'OPTICAL': 'Optical/Eye Care',
        'ENT': 'Ear Nose Throat (ENT)',
        'OPTHALMOLOGY': 'Ophthalmology',
        'ANAES': 'Anesthesiology (ANAES)',
        'DIET': 'Dietetics (DIET)'
    }

    def expand_specialties(specialty_str: str) -> str:
        """Expand specialty abbreviations for better semantic matching."""
        if not specialty_str:
            return ""

        # Split by common delimiters
        parts = specialty_str.replace('/', ', ').replace('&', ', ').split(', ')
        expanded = []

        for part in parts:
            part_clean = part.strip().upper()
            if part_clean in specialty_expansions:
                expanded.append(specialty_expansions[part_clean])
            elif part_clean:
                expanded.append(part.strip())

        return ', '.join(expanded)

    # Add each provider
    for provider in providers:
        name = provider['Hospital/Clinic']
        specialties = provider.get('Speciality', '').strip()
        specialties_expanded = expand_specialties(specialties)
        phone = provider.get('Contact', '').strip()
        location = provider.get('Location', '').strip()

        content_lines.append(f"## {name}")

        if specialties_expanded:
            content_lines.append(f"**Specialties**: {specialties_expanded}")
            # Also add original for reference
            if specialties != specialties_expanded:
                content_lines.append(f"**Specialty Codes**: {specialties}")

        if phone:
            content_lines.append(f"**Phone**: {phone}")

        if location:
            content_lines.append(f"**Location**: {location}")

        content_lines.append(f"**Region**: {city_upper}")
        content_lines.append("")
        content_lines.append("---")
        content_lines.append("")

    content = "\n".join(content_lines)

    # Create knowledge document
    doc_id = f"providers_{city_upper.lower().replace(' ', '_').replace('/', '_')}"

    # Build tags
    tags = ["providers", "healthcare", city_upper.lower().replace(' ', '_')]
    if original_region and original_region != city:
        tags.append(f"from_{original_region.lower().replace(' ', '_')}")

    doc = KnowledgeDocument(
        id=doc_id,
        title=f"Healthcare Providers in {city_upper}",
        content=content,
        category="provider_directory",
        source="master_csv_split",
        tags=tags,
        metadata={
            "city": city_upper,
            "provider_count": len(providers),
            "original_region": original_region or city,
            "is_split": original_region != city if original_region else False
        }
    )

    return doc


def group_providers_by_region(providers: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group providers by their region.

    Args:
        providers: List of all providers

    Returns:
        Dictionary mapping region name to list of providers.
    """
    grouped = defaultdict(list)

    for provider in providers:
        region = provider.get('Region', '').strip()
        if region:
            grouped[region].append(provider)

    return dict(grouped)


async def reingest_providers_with_split_regions():
    """
    Main function to re-ingest provider data with split regions.
    """
    print("🏥 Re-ingesting Premier Health Provider Data with Split Regions")
    print("=" * 70)

    try:
        # Step 1: Load providers from CSV
        print("\n1. Loading providers from master CSV...")
        providers = load_providers_from_csv()
        print(f"   ✅ Loaded {len(providers)} providers")

        # Step 2: Group by region
        print("\n2. Grouping providers by region...")
        grouped = group_providers_by_region(providers)
        print(f"   ✅ Found {len(grouped)} unique regions")

        # Step 3: Identify combined regions and split
        print("\n3. Processing regions and splitting combined cities...")
        all_documents = []
        combined_regions = []
        single_regions = []

        for region, region_providers in grouped.items():
            cities = split_region_name(region)

            if len(cities) > 1:
                # Combined region - split into separate documents
                combined_regions.append(region)
                print(f"   📍 Splitting '{region}' into {len(cities)} cities: {', '.join(cities)}")

                # Create a document for each city with ALL providers from the combined region
                # Reason: Providers in combined regions typically serve all cities in that group
                for city in cities:
                    doc = create_provider_document(city, region_providers, original_region=region)
                    all_documents.append(doc)
            else:
                # Single city - create one document
                single_regions.append(region)
                doc = create_provider_document(cities[0], region_providers)
                all_documents.append(doc)

        print(f"\n   Summary:")
        print(f"   - Combined regions split: {len(combined_regions)}")
        print(f"   - Single city regions: {len(single_regions)}")
        print(f"   - Total documents created: {len(all_documents)}")

        # Step 4: Show some examples of split regions
        print(f"\n4. Examples of split regions:")
        for region in combined_regions[:10]:
            cities = split_region_name(region)
            print(f"   • '{region}' → {cities}")
        if len(combined_regions) > 10:
            print(f"   ... and {len(combined_regions) - 10} more")

        # Step 5: Delete existing collection and re-index
        print(f"\n5. Re-indexing knowledge base...")
        print(f"   ⚠️  This will replace all existing provider documents")

        # Initialize knowledge base with new documents
        result = await helpdesk_rag_service.initialize_knowledge_base(
            company_name="premier_health_production",
            documents=all_documents
        )

        print(f"\n   ✅ Knowledge base re-indexed successfully!")
        print(f"   - Collection: {result['collection_name']}")
        print(f"   - Documents indexed: {result['documents_indexed']}")
        print(f"   - Chunks created: {result['chunks_created']}")
        print(f"   - Embedding dimension: {result['embedding_dimension']}")

        # Step 6: Show statistics
        print(f"\n6. Final Statistics:")
        stats = await helpdesk_rag_service.get_knowledge_base_stats("premier_health_production")
        for key, value in stats.items():
            print(f"   - {key}: {value}")

        print(f"\n✅ Re-ingestion Complete!")
        print(f"\nℹ️  Combined regions have been split into individual city documents.")
        print(f"   Queries for cities like 'OBUASI', 'DUNKWA', 'MADINA', etc. should now work correctly.")

    except Exception as e:
        print(f"\n❌ Error during re-ingestion: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(reingest_providers_with_split_regions())
