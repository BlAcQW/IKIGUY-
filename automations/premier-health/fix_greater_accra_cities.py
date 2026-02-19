#!/usr/bin/env python3
"""
Fix Greater Accra Region City Separation

Separates merged city names in Greater Accra region into individual documents.
Based on successful Ashanti region separation approach.

Examples:
- "ACCRA CENTRAL / TUDU / MAKOLA" → ACCRA CENTRAL, TUDU, MAKOLA
- "KOKOMLEMLE / MAAMOBI / NIMA" → KOKOMLEMLE, MAAMOBI, NIMA
- "LEGON & NORTH LEGON" → LEGON, NORTH LEGON
"""

import sys
import os
import asyncio
import csv
import re
from typing import List, Dict
from collections import defaultdict

sys.path.append('/opt/kasaai/apps/core_backend')

from backend.services.pg_document_service import pg_document_service
from backend.models.knowledge_base import DocumentCreate, DocumentFilter, DocumentUpdate

# Paths
CSV_PATH = '/opt/kasaai/apps/automations/premier-health/greater_accra_region_enriched.csv'

# City separations based on CSV structure
CITY_SEPARATIONS = {
    "ACCRA CENTRAL / TUDU / MAKOLA": ["ACCRA CENTRAL", "TUDU", "MAKOLA"],
    "AIRPORT RESIDENTIAL AREA / 37 AREA": ["AIRPORT RESIDENTIAL AREA", "37 AREA"],
    "CIRCLE / KANESHIE / NORTH KANESHIE / INDUSTRIAL AREA": ["CIRCLE", "KANESHIE", "NORTH KANESHIE", "INDUSTRIAL AREA"],
    "AMANSAMAN / POKUASE": ["AMANSAMAN", "POKUASE"],
    "ASHAIMAN / COMMUNITY 26": ["ASHAIMAN", "COMMUNITY 26"],
    "DANSOMAN / MAMPROBI / KORLE-BU": ["DANSOMAN", "MAMPROBI", "KORLE-BU"],
    "KOKOMLEMLE / MAAMOBI / NIMA": ["KOKOMLEMLE", "MAAMOBI", "NIMA"],
    "LEGON & NORTH LEGON": ["LEGON", "NORTH LEGON"],
    "MADINA / ADENTA / DODOWA": ["MADINA", "ADENTA", "DODOWA"],
    "WEIJA / KASOA / GBAWE": ["WEIJA", "KASOA", "GBAWE"],
    "COMM. 22 / MICHEL CAMP / AFIENYA ROAD": ["COMMUNITY 22", "MICHEL CAMP", "AFIENYA ROAD"],
    "TEMA COMMUNITY 2 / 4": ["TEMA COMMUNITY 2", "TEMA COMMUNITY 4"],
    "TEMA COMMUNITY 4 / 5 / 6 / 9 / 10 / 12": [
        "TEMA COMMUNITY 4", "TEMA COMMUNITY 5", "TEMA COMMUNITY 6",
        "TEMA COMMUNITY 9", "TEMA COMMUNITY 10", "TEMA COMMUNITY 12"
    ],
}


def load_providers() -> List[Dict]:
    """Load providers from Greater Accra CSV."""
    providers = []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        # Skip first 2 header rows
        next(f)
        next(f)
        reader = csv.DictReader(f)
        for row in reader:
            region = row.get('region', '').strip()
            hospital = row.get('NAME OF HOSPITAL / CLINIC', '').strip()
            if region.upper() == 'GREATER ACCRA' and hospital:
                providers.append(row)
    return providers


def normalize_city(city: str) -> str:
    """Normalize city name."""
    normalized = city.strip().upper()
    normalized = re.sub(r'\s*/\s*', ' / ', normalized)
    normalized = re.sub(r'\s*&\s*', ' & ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized


def get_cities_to_split(city: str) -> List[str]:
    """Get individual cities from combined name."""
    normalized = normalize_city(city)
    return CITY_SEPARATIONS.get(normalized, [normalized])


def group_providers_by_city(providers: List[Dict]) -> Dict[str, List[Dict]]:
    """Group providers by city."""
    grouped = defaultdict(list)
    for provider in providers:
        city = provider.get('city', '').strip()
        if city:
            grouped[city].append(provider)
    return dict(grouped)


def create_document(city: str, providers: List[Dict], source_city: str = None) -> DocumentCreate:
    """Create document for a city."""
    city_upper = city.upper()

    content_lines = [
        f"# Healthcare Providers in {city_upper}",
        "",
        f"This document lists all Premier Health Insurance network providers in {city_upper}, Greater Accra Region, Ghana.",
        ""
    ]

    specialty_map = {
        'GP': 'General Practice', 'PHY': 'Physiotherapy', 'SRY': 'Surgery',
        'GYN': 'Gynecology', 'OBS': 'Obstetrics', 'PED': 'Pediatrics',
        'PAED': 'Pediatrics', 'EYE': 'Ophthalmology', 'DEN': 'Dental',
        'ENT': 'Ear Nose Throat', 'OPTICAL': 'Optical/Eye Care',
        'PHARMACY': 'Pharmacy', 'LAB': 'Laboratory', 'DIET': 'Dietetics',
        'GU': 'Genitourinary', 'ANAES': 'Anesthesiology'
    }

    def expand_specialties(spec_str: str) -> str:
        if not spec_str:
            return "General Services"
        parts = spec_str.upper().replace('/', ',').split(',')
        expanded = []
        for part in parts:
            clean = part.strip()
            expanded.append(specialty_map.get(clean, clean.title()))
        return ', '.join(expanded) if expanded else "General Services"

    for idx, p in enumerate(providers, 1):
        name = p.get('NAME OF HOSPITAL / CLINIC', '').strip()
        if not name:
            continue

        specialties = p.get('SPECIALITY', '').strip()
        phone = p.get('CONTACT number', '').strip()
        location = p.get('LOCATION', '').strip()

        content_lines.append(f"## {idx}. {name}")
        content_lines.append("")

        if specialties:
            content_lines.append(f"**Specialties**: {expand_specialties(specialties)}")
        if phone:
            content_lines.append(f"**Phone**: {phone}")
        if location:
            content_lines.append(f"**Location**: {location}")

        content_lines.append(f"**City**: {city_upper}")
        content_lines.append(f"**Region**: Greater Accra Region")
        content_lines.append("")
        content_lines.append("---")
        content_lines.append("")

    content_lines.append(f"\n**Total Providers**: {len(providers)}")
    if source_city and source_city != city:
        content_lines.append(f"**Source**: Split from '{source_city}'")

    content = "\n".join(content_lines)

    tags = [
        "providers", "healthcare", "greater_accra_region",
        city_upper.lower().replace(' ', '_')
    ]

    if source_city and source_city != city:
        tags.append(f"split_from_{normalize_city(source_city).lower().replace(' ', '_').replace('/', '_').replace('&', '_')}")

    return DocumentCreate(
        company_name="premier_health_production",
        title=f"Healthcare Providers in {city_upper}",
        content=content,
        category="provider_directory",
        tags=tags,
        source="greater_accra_csv_split",
        source_uri=f"file:{CSV_PATH}",
        created_by="greater_accra_city_separation_script"
    )


async def main():
    """Main execution."""
    print("🏥 Greater Accra Region City Separation")
    print("=" * 70)

    # Load providers
    print("\n1. Loading providers...")
    providers = load_providers()
    print(f"   ✅ Loaded {len(providers)} providers")

    # Group by city
    print("\n2. Grouping by city...")
    grouped = group_providers_by_city(providers)
    print(f"   ✅ Found {len(grouped)} city groupings")

    # Process separations
    print("\n3. Processing city separations...")
    all_docs = []
    split_count = 0

    for csv_city, city_providers in grouped.items():
        normalized = normalize_city(csv_city)
        individual_cities = get_cities_to_split(csv_city)

        if len(individual_cities) > 1:
            split_count += 1
            print(f"   📍 Splitting '{normalized}' into {len(individual_cities)} cities")
            for city in individual_cities:
                doc = create_document(city, city_providers, normalized)
                all_docs.append(doc)
                print(f"      → {city} ({len(city_providers)} providers)")
        else:
            doc = create_document(individual_cities[0], city_providers, normalized)
            all_docs.append(doc)

    print(f"\n   Summary:")
    print(f"   - Cities split: {split_count}")
    print(f"   - Total documents to create: {len(all_docs)}")

    # Create documents
    print(f"\n4. Creating documents...")
    created = 0
    updated = 0
    failed = 0

    for doc in all_docs:
        try:
            filter_params = DocumentFilter(
                company_name="premier_health_production",
                search_query=doc.title,
                page=1,
                page_size=5
            )

            existing = await pg_document_service.list_documents(filter_params)
            exists = False
            existing_id = None

            if existing.documents:
                for ex_doc in existing.documents:
                    doc_dict = ex_doc if isinstance(ex_doc, dict) else ex_doc.dict()
                    if doc_dict['title'] == doc.title:
                        exists = True
                        existing_id = doc_dict['id']
                        break

            if exists:
                doc_update = DocumentUpdate(
                    content=doc.content,
                    tags=doc.tags,
                    updated_by="greater_accra_separation_script",
                    change_reason="City separation fix"
                )
                result = await pg_document_service.update_document(existing_id, doc_update)
                if result.success:
                    print(f"   ✅ Updated: {doc.title}")
                    updated += 1
                else:
                    print(f"   ❌ Failed to update: {doc.title}")
                    failed += 1
            else:
                result = await pg_document_service.create_document(doc)
                if result.success:
                    print(f"   ✅ Created: {doc.title}")
                    created += 1
                else:
                    print(f"   ❌ Failed to create: {doc.title}")
                    failed += 1

        except Exception as e:
            print(f"   ❌ Error processing '{doc.title}': {e}")
            failed += 1

    print(f"\n   Results:")
    print(f"   - Created: {created}")
    print(f"   - Updated: {updated}")
    print(f"   - Failed: {failed}")

    print(f"\n✅ Greater Accra City Separation Complete!")
    print(f"\nℹ️  All cities now have individual searchable documents.")


if __name__ == "__main__":
    asyncio.run(main())
