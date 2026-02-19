#!/usr/bin/env python3
"""
Create Northern Regions City Documents

Creates individual city documents for:
- Northern Region: TAMALE
- Upper West Region: WA, LAWRA
- Upper East Region: BOLGATANGA, BAWKU, NAVRONGO
"""

import sys
import asyncio
import csv
from typing import List, Dict
from collections import defaultdict

sys.path.append('/opt/kasaai/apps/core_backend')

from backend.services.pg_document_service import pg_document_service
from backend.models.knowledge_base import DocumentCreate, DocumentFilter, DocumentUpdate

CSV_PATH = '/opt/kasaai/apps/automations/premier-health/all_northern_regions_enriched.csv'


def load_providers() -> List[Dict]:
    """Load providers from CSV."""
    providers = []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            region = row.get('region', '').strip()
            hospital = row.get('NAME OF HOSPITAL / CLINIC', '').strip()
            city = row.get('city', '').strip()

            if region and hospital and city:
                providers.append(row)

    return providers


def group_providers_by_city(providers: List[Dict]) -> Dict[str, List[Dict]]:
    """Group providers by city."""
    grouped = defaultdict(list)
    for provider in providers:
        city = provider.get('city', '').strip()
        if city:
            grouped[city].append(provider)
    return dict(grouped)


def create_document(city: str, providers: List[Dict], region: str) -> DocumentCreate:
    """Create document for a city."""
    city_upper = city.upper()

    content_lines = [
        f"# Healthcare Providers in {city_upper}",
        "",
        f"This document lists all Premier Health Insurance network providers in {city_upper}, {region}, Ghana.",
        ""
    ]

    specialty_map = {
        'GP': 'General Practice', 'PHY': 'Physiotherapy', 'SRY': 'Surgery', 'SUR': 'Surgery',
        'GYN': 'Gynecology', 'GYNAE': 'Gynecology', 'GYNE': 'Gynecology',
        'OBS': 'Obstetrics', 'PED': 'Pediatrics', 'PAED': 'Pediatrics',
        'EYE': 'Ophthalmology', 'DEN': 'Dental', 'DENTAL': 'Dental',
        'ENT': 'Ear Nose Throat',
        'OPTICAL': 'Optical', 'OPTICALS': 'Opticals',
        'PHARMACY': 'Pharmacy',
        'LAB': 'Laboratory', 'LABORATORY': 'Laboratory',
        'DIAGNOSTIC': 'Diagnostic', 'DIAGNOSTICS': 'Diagnostics',
        'PHYIOTHERAPY': 'Physiotherapy', 'PHYS': 'Physiotherapy',
        'SPE': 'Specialist', 'SP': 'Specialist',
        'RGN/BSC/NURSE PRACTITIONER': 'Nursing',
        'DEIT': 'Dietetics',
        'GPS': 'General Practice',
        'Health Centre / Health Post': 'Health Centre'
    }

    def expand_specialties(spec_str: str) -> str:
        if not spec_str:
            return "General Services"
        parts = spec_str.replace('/', ',').split(',')
        expanded = []
        seen = set()
        for part in parts:
            clean = part.strip()
            mapped = specialty_map.get(clean, clean.title())
            if mapped not in seen:
                expanded.append(mapped)
                seen.add(mapped)
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
        content_lines.append(f"**Region**: {region}")
        content_lines.append("")
        content_lines.append("---")
        content_lines.append("")

    content_lines.append(f"\n**Total Providers**: {len(providers)}")

    content = "\n".join(content_lines)

    tags = [
        "providers", "healthcare",
        region.lower().replace(' ', '_').replace(',', ''),
        city_upper.lower().replace(' ', '_')
    ]

    return DocumentCreate(
        company_name="premier_health_production",
        title=f"Healthcare Providers in {city_upper}",
        content=content,
        category="provider_directory",
        tags=tags,
        source="northern_regions_csv",
        source_uri=f"file:{CSV_PATH}",
        created_by="northern_regions_script"
    )


async def main():
    """Main execution."""
    print("🏥 Northern Regions City Document Creation")
    print("=" * 70)

    # Load providers
    print("\n1. Loading providers...")
    providers = load_providers()
    print(f"   ✅ Loaded {len(providers)} providers")

    # Group by city
    print("\n2. Grouping by city...")
    grouped = group_providers_by_city(providers)
    print(f"   ✅ Found {len(grouped)} cities")

    # Get regions
    region_map = {}
    for provider in providers:
        city = provider.get('city', '').strip()
        region = provider.get('region', '').strip()
        if city and region:
            region_map[city] = region

    # Show cities found
    print("\n   Cities:")
    for city in sorted(grouped.keys()):
        print(f"      - {city} ({len(grouped[city])} providers) - {region_map.get(city, 'Unknown')}")

    # Create documents
    print(f"\n3. Creating/updating documents...")
    created = 0
    updated = 0
    failed = 0

    for city, city_providers in grouped.items():
        region = region_map.get(city, "NORTHERN REGION")
        doc = create_document(city, city_providers, region)

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
                    updated_by="northern_regions_script",
                    change_reason="Northern regions data update"
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

    print(f"\n✅ Northern Regions Document Creation Complete!")


if __name__ == "__main__":
    asyncio.run(main())
