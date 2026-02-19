#!/usr/bin/env python3
"""
Fix Tema Community Provider Mappings

This script correctly assigns providers to Tema communities based on their
actual LOCATION field, not the enriched city column which has incorrect mappings.

Author: Claude Code
Date: October 30, 2025
"""

import sys
import os
import asyncio
import csv
import re
from typing import List, Dict, Optional
from collections import defaultdict

# Set environment variables
os.environ["MONGODB_URL"] = "mongodb://admin:aawwER444444@127.0.0.1:27017/kasaai_core?authSource=admin"
os.environ["POSTGRES_PASSWORD"] = "aawwER444444"
os.environ["GEMINI_API_KEY"] = "AIzaSyAACjmMMYIVH2Pq8Ns8KbOud-X8oCQMny4"

sys.path.append('/opt/kasaai/apps/core_backend')

from backend.services.pg_document_service import pg_document_service
from backend.models.knowledge_base import DocumentCreate, DocumentFilter, DocumentUpdate

CSV_PATH = '/opt/kasaai/apps/automations/premier-health/regional_cities/enriched/greater_accra_region_enriched.csv'


def extract_community_from_location(location: str) -> Optional[int]:
    """
    Extract community number from location string.

    Examples:
        "COMMUNITY 4, TEMA" → 4
        "TEMA COMM. 1" → 1
        "TEMA COMM 10 JUNCTION" → 10
        "COMM. 4 & COMM. 9" → 4 (first mentioned)
        "BEHIND COMMUNITY 11 SHELL, TEMA" → 11
        "SITE 13, COMMUNITY ONE, TEMA" → 1
    """
    if not location:
        return None

    location_upper = location.upper()

    # Handle "COMMUNITY ONE" → 1
    if 'COMMUNITY ONE' in location_upper or 'COMM ONE' in location_upper:
        return 1

    # Pattern: COMMUNITY <number> or COMM <number> or COMM. <number>
    patterns = [
        r'COMMUNITY\s+(\d+)',
        r'COMM\.?\s+(\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, location_upper)
        if match:
            return int(match.group(1))

    return None


def load_tema_providers() -> List[Dict]:
    """Load all providers from Greater Accra CSV."""
    providers = []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            region = row.get('region', '').strip()
            city = row.get('city', '').strip()
            hospital = row.get('NAME OF HOSPITAL / CLINIC', '').strip()

            # Only process Greater Accra Tema providers
            if region.upper() == 'GREATER ACCRA' and 'TEMA' in city.upper() and hospital:
                providers.append(row)

    return providers


def group_by_actual_community(providers: List[Dict]) -> Dict[int, List[Dict]]:
    """Group providers by their actual community number from location field."""
    grouped = defaultdict(list)
    unassigned = []

    for provider in providers:
        location = provider.get('LOCATION', '').strip()
        community_num = extract_community_from_location(location)

        if community_num:
            grouped[community_num].append(provider)
        else:
            # Provider doesn't have clear community in location
            # Try to infer from city column
            city = provider.get('city', '').strip()

            # Check if city explicitly mentions single community
            match = re.search(r'TEMA COMMUNITY (\d+)(?:\s|,|$)', city.upper())
            if match and '/' not in city:  # Not a merged group
                community_num = int(match.group(1))
                grouped[community_num].append(provider)
            else:
                unassigned.append(provider)

    return dict(grouped), unassigned


def create_community_document(community_num: int, providers: List[Dict]) -> DocumentCreate:
    """Create document for a Tema community."""

    content_lines = [
        f"# Healthcare Providers in TEMA COMMUNITY {community_num}",
        "",
        f"This document lists all Premier Health Insurance network providers in TEMA COMMUNITY {community_num}, Ghana.",
        "",
        f"## TEMA COMMUNITY {community_num}",
        "**Region**: GREATER ACCRA",
        "",
        "---",
        ""
    ]

    for provider in providers:
        name = provider.get('NAME OF HOSPITAL / CLINIC', '').strip()
        if not name:
            continue

        specialties = provider.get('SPECIALITY', '').strip()
        phone = provider.get('CONTACT number', '').strip()
        location = provider.get('LOCATION', '').strip()

        content_lines.append(f"## {name}")

        if specialties:
            content_lines.append(f"**Specialties**: {specialties}")
        if phone:
            content_lines.append(f"**Phone**: {phone}")
        if location:
            content_lines.append(f"**Location**: {location}")

        content_lines.append(f"**Region**: GREATER ACCRA")
        content_lines.append("")
        content_lines.append("---")
        content_lines.append("")

    content = "\n".join(content_lines)

    return DocumentCreate(
        company_name="premier_health_production",
        title=f"Healthcare Providers in TEMA COMMUNITY {community_num}",
        content=content,
        category="provider_directory",
        tags=[
            "providers", "healthcare", "greater_accra_region",
            f"tema_community_{community_num}", "tema"
        ],
        source="tema_community_location_based_fix",
        source_uri=f"file:{CSV_PATH}",
        created_by="tema_community_fix_script"
    )


async def main():
    """Main execution."""
    print("=" * 80)
    print("TEMA COMMUNITY MAPPING FIX")
    print("=" * 80)
    print("Fixing provider assignments based on actual LOCATION field")
    print("=" * 80)
    print()

    # Load providers
    print("📚 Loading Tema providers from enriched CSV...")
    providers = load_tema_providers()
    print(f"   ✅ Loaded {len(providers)} Tema providers")
    print()

    # Group by actual community
    print("🔍 Analyzing actual community assignments from LOCATION field...")
    grouped, unassigned = group_by_actual_community(providers)
    print(f"   ✅ Found providers in {len(grouped)} communities")

    if unassigned:
        print(f"   ⚠️  {len(unassigned)} providers couldn't be assigned:")
        for p in unassigned:
            print(f"      - {p.get('NAME OF HOSPITAL / CLINIC', 'Unknown')}")
            print(f"        Location: {p.get('LOCATION', 'N/A')}")

    print()
    print("📊 Community Provider Distribution:")
    print("-" * 80)
    for community_num in sorted(grouped.keys()):
        count = len(grouped[community_num])
        print(f"   TEMA COMMUNITY {community_num:2d}: {count:2d} provider(s)")

    print()
    print("🔄 Updating/Creating community documents...")
    print("-" * 80)

    created = 0
    updated = 0
    failed = 0

    for community_num, community_providers in sorted(grouped.items()):
        try:
            doc = create_community_document(community_num, community_providers)

            # Check if document exists
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
                # Update existing document
                doc_update = DocumentUpdate(
                    content=doc.content,
                    tags=doc.tags,
                    updated_by="tema_community_fix_script",
                    change_reason="Fixed provider assignments based on actual location"
                )
                result = await pg_document_service.update_document(existing_id, doc_update)
                if result.success:
                    print(f"   ✅ Updated: TEMA COMMUNITY {community_num} ({len(community_providers)} providers)")
                    updated += 1
                else:
                    print(f"   ❌ Failed to update: TEMA COMMUNITY {community_num}")
                    failed += 1
            else:
                # Create new document
                result = await pg_document_service.create_document(doc)
                if result.success:
                    print(f"   ✅ Created: TEMA COMMUNITY {community_num} ({len(community_providers)} providers)")
                    created += 1
                else:
                    print(f"   ❌ Failed to create: TEMA COMMUNITY {community_num}")
                    failed += 1

        except Exception as e:
            print(f"   ❌ Error processing TEMA COMMUNITY {community_num}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print()
    print("=" * 80)
    print("✅ TEMA COMMUNITY MAPPING FIX COMPLETE")
    print("=" * 80)
    print(f"Created: {created}")
    print(f"Updated: {updated}")
    print(f"Failed: {failed}")
    print("=" * 80)
    print()
    print("ℹ️  Next steps:")
    print("   1. Run reindex_community_documents.py to regenerate embeddings")
    print("   2. Wait 30-60 seconds for indexing to complete")
    print("   3. Test queries like 'providers in community 5'")
    print()


if __name__ == "__main__":
    asyncio.run(main())
