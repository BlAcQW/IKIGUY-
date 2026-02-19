#!/usr/bin/env python3
"""
Fix AMASAMAN Spelling in RAG Database

Issue: AMANSAMAN was misspelled as AMANSAMAN in the database
Correct spelling: AMASAMAN

Also separate AMASAMAN / POKUASE into individual cities:
- AMASAMAN (providers 1, 2, 4)
- POKUASE (provider 3)
"""

import sys
import asyncio

sys.path.append('/opt/kasaai/apps/core_backend')

from backend.services.pg_document_service import pg_document_service
from backend.models.knowledge_base import DocumentCreate, DocumentFilter, DocumentUpdate

# Provider data for AMASAMAN / POKUASE
AMASAMAN_PROVIDERS = [
    {
        "name": "M AND D CLINIC",
        "specialties": "GP/PHY",
        "phone": "0302939939 / 0249697350",
        "location": "AMASAMAN"
    },
    {
        "name": "OBEYEYIE MEDICAL CENTRE",
        "specialties": "GP/PHY/OBS/GYNAE",
        "phone": "0303938127/0244995802",
        "location": "AMASAMAN ACCRA"
    },
    {
        "name": "BLOOMINGALE MEDICAL CENTRE",
        "specialties": "GP/GYN/PHY/SGR",
        "phone": "0554543131",
        "location": "HERITAGE CHRISTIAN COLLEGE, AMASAMAN STADIUM ROAD"
    }
]

POKUASE_PROVIDERS = [
    {
        "name": "HOBEM CLINIC",
        "specialties": "GP",
        "phone": "0302905212/ 0501010105",
        "location": "POKUASE, BEHIND FESTUS HOTEL"
    }
]


def expand_specialties(spec_str: str) -> str:
    """Expand specialty abbreviations."""
    specialty_map = {
        'GP': 'General Practice',
        'PHY': 'Physiotherapy',
        'OBS': 'Obstetrics',
        'GYNAE': 'Gynecology',
        'GYN': 'Gynecology',
        'SGR': 'Surgery',
        'SUR': 'Surgery'
    }

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


def create_city_document(city: str, providers: list) -> DocumentCreate:
    """Create document for a city."""
    city_upper = city.upper()

    content_lines = [
        f"# Healthcare Providers in {city_upper}",
        "",
        f"This document lists all Premier Health Insurance network providers in {city_upper}, Greater Accra Region, Ghana.",
        ""
    ]

    for idx, p in enumerate(providers, 1):
        content_lines.append(f"## {idx}. {p['name']}")
        content_lines.append("")
        content_lines.append(f"**Specialties**: {expand_specialties(p['specialties'])}")
        content_lines.append(f"**Phone**: {p['phone']}")
        content_lines.append(f"**Location**: {p['location']}")
        content_lines.append(f"**City**: {city_upper}")
        content_lines.append(f"**Region**: Greater Accra Region")
        content_lines.append("")
        content_lines.append("---")
        content_lines.append("")

    content_lines.append(f"\n**Total Providers**: {len(providers)}")
    content_lines.append(f"**Source**: Split from 'AMASAMAN / POKUASE'")

    content = "\n".join(content_lines)

    tags = [
        "providers",
        "healthcare",
        "greater_accra_region",
        city_upper.lower().replace(' ', '_'),
        "split_from_amasaman_pokuase"
    ]

    return DocumentCreate(
        company_name="premier_health_production",
        title=f"Healthcare Providers in {city_upper}",
        content=content,
        category="provider_directory",
        tags=tags,
        source="amasaman_spelling_fix",
        source_uri="manual_correction",
        created_by="amasaman_spelling_fix_script"
    )


async def main():
    """Main execution."""
    print("🔧 Fixing AMASAMAN Spelling in RAG Database")
    print("=" * 70)

    # Step 1: Check for existing misspelled documents
    print("\n1. Checking for misspelled AMANSAMAN documents...")
    filter_params = DocumentFilter(
        company_name="premier_health_production",
        search_query="AMANSAMAN",
        page=1,
        page_size=10
    )

    existing = await pg_document_service.list_documents(filter_params)

    if existing.documents:
        print(f"   ⚠️  Found {len(existing.documents)} document(s) with AMANSAMAN")
        for doc in existing.documents:
            doc_dict = doc if isinstance(doc, dict) else doc.dict()
            print(f"      - {doc_dict['title']}")
    else:
        print(f"   ✅ No documents found with AMANSAMAN spelling")

    # Step 2: Create correct AMASAMAN document
    print("\n2. Creating AMASAMAN document (correct spelling)...")
    amasaman_doc = create_city_document("AMASAMAN", AMASAMAN_PROVIDERS)

    # Check if AMASAMAN already exists
    filter_params = DocumentFilter(
        company_name="premier_health_production",
        search_query=amasaman_doc.title,
        page=1,
        page_size=5
    )

    existing = await pg_document_service.list_documents(filter_params)
    exists = False
    existing_id = None

    if existing.documents:
        for ex_doc in existing.documents:
            doc_dict = ex_doc if isinstance(ex_doc, dict) else ex_doc.dict()
            if doc_dict['title'] == amasaman_doc.title:
                exists = True
                existing_id = doc_dict['id']
                break

    if exists:
        doc_update = DocumentUpdate(
            content=amasaman_doc.content,
            tags=amasaman_doc.tags,
            updated_by="amasaman_spelling_fix_script",
            change_reason="Fixed spelling from AMANSAMAN to AMASAMAN"
        )
        result = await pg_document_service.update_document(existing_id, doc_update)
        if result.success:
            print(f"   ✅ Updated: {amasaman_doc.title}")
        else:
            print(f"   ❌ Failed to update AMASAMAN")
    else:
        result = await pg_document_service.create_document(amasaman_doc)
        if result.success:
            print(f"   ✅ Created: {amasaman_doc.title}")
        else:
            print(f"   ❌ Failed to create AMASAMAN")

    # Step 3: Create POKUASE document
    print("\n3. Creating POKUASE document...")
    pokuase_doc = create_city_document("POKUASE", POKUASE_PROVIDERS)

    # Check if POKUASE already exists
    filter_params = DocumentFilter(
        company_name="premier_health_production",
        search_query=pokuase_doc.title,
        page=1,
        page_size=5
    )

    existing = await pg_document_service.list_documents(filter_params)
    exists = False
    existing_id = None

    if existing.documents:
        for ex_doc in existing.documents:
            doc_dict = ex_doc if isinstance(ex_doc, dict) else ex_doc.dict()
            if doc_dict['title'] == pokuase_doc.title:
                exists = True
                existing_id = doc_dict['id']
                break

    if exists:
        doc_update = DocumentUpdate(
            content=pokuase_doc.content,
            tags=pokuase_doc.tags,
            updated_by="amasaman_spelling_fix_script",
            change_reason="Separated from AMASAMAN / POKUASE"
        )
        result = await pg_document_service.update_document(existing_id, doc_update)
        if result.success:
            print(f"   ✅ Updated: {pokuase_doc.title}")
        else:
            print(f"   ❌ Failed to update POKUASE")
    else:
        result = await pg_document_service.create_document(pokuase_doc)
        if result.success:
            print(f"   ✅ Created: {pokuase_doc.title}")
        else:
            print(f"   ❌ Failed to create POKUASE")

    # Step 4: Delete old misspelled documents
    print("\n4. Deleting old misspelled AMANSAMAN documents...")
    deleted_count = 0

    # Get all documents with AMANSAMAN
    filter_params = DocumentFilter(
        company_name="premier_health_production",
        search_query="AMANSAMAN",
        page=1,
        page_size=10
    )

    existing = await pg_document_service.list_documents(filter_params)

    if existing.documents:
        for doc in existing.documents:
            doc_dict = doc if isinstance(doc, dict) else doc.dict()
            doc_id = doc_dict['id']
            doc_title = doc_dict['title']

            # Delete if it has AMANSAMAN in the title
            if 'AMANSAMAN' in doc_title.upper():
                try:
                    result = await pg_document_service.delete_document(
                        doc_id,
                        "premier_health_production"
                    )
                    if result.success:
                        print(f"   ✅ Deleted: {doc_title} (ID: {doc_id})")
                        deleted_count += 1
                    else:
                        print(f"   ❌ Failed to delete: {doc_title}")
                except Exception as e:
                    print(f"   ❌ Error deleting '{doc_title}': {e}")

    print(f"   Deleted {deleted_count} misspelled document(s)")

    print("\n✅ AMASAMAN Spelling Fix Complete!")
    print("\nChanges:")
    print("  - Created/Updated 'Healthcare Providers in AMASAMAN' with 3 providers")
    print("  - Created/Updated 'Healthcare Providers in POKUASE' with 1 provider")
    print(f"  - Deleted {deleted_count} old misspelled AMANSAMAN documents")
    print("  - Correct spelling: AMASAMAN (not AMANSAMAN)")


if __name__ == "__main__":
    asyncio.run(main())
