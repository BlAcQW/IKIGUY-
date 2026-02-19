#!/usr/bin/env python3
"""
Index healthcare providers from PostgreSQL into RAG knowledge base.
This makes provider information searchable through AI-powered queries.
"""

import sys
import os
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor

# Add paths for imports
sys.path.append('/opt/kasaai/apps/core_backend')

from backend.services.helpdesk_rag_service import helpdesk_rag_service, KnowledgeDocument

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'kasaai_core',
    'options': '-c search_path=premier_health,public',
    'user': 'postgres',
    'password': os.getenv('POSTGRES_PASSWORD', 'aawwER444444')
}

def fetch_providers():
    """Fetch all healthcare providers from database."""
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id, name, provider_type, phone_primary, phone_secondary,
                    address, area, region, specialties, services_description,
                    is_active, is_emergency
                FROM healthcare_providers
                WHERE is_active = true
                ORDER BY area, name
            """)
            providers = cur.fetchall()
            return providers
    finally:
        conn.close()

def create_provider_documents(providers):
    """Convert provider records to knowledge documents."""
    documents = []

    # Group providers by area for better organization
    providers_by_area = {}
    for provider in providers:
        area = provider['area'] or 'Other Areas'
        if area not in providers_by_area:
            providers_by_area[area] = []
        providers_by_area[area].append(provider)

    # Create area-based summary documents
    for area, area_providers in providers_by_area.items():
        # Create summary of providers in this area
        provider_list = []
        for p in area_providers:
            specialties_str = ', '.join(p['specialties']) if p['specialties'] else 'General'
            provider_info = f"- {p['name']} ({p['provider_type']})"
            if p['specialties']:
                provider_info += f" - Specialties: {specialties_str}"
            if p['phone_primary']:
                provider_info += f" - Phone: {p['phone_primary']}"
            if p['address']:
                provider_info += f" - Location: {p['address']}"
            provider_list.append(provider_info)

        content = f"""
Healthcare Providers in {area}:

This area has {len(area_providers)} healthcare providers available through Premier Health Insurance.

Providers:
{chr(10).join(provider_list)}

Area Information:
- Region: Greater Accra
- Total Providers: {len(area_providers)}
- Provider Types: {', '.join(set(p['provider_type'] for p in area_providers))}
- Emergency Services Available: {'Yes' if any(p.get('is_emergency') for p in area_providers) else 'No'}

All providers listed above accept Premier Health Insurance. Simply present your Premier Health ID card when visiting.
"""

        doc = KnowledgeDocument(
            id=f"providers_area_{area.lower().replace(' ', '_')}",
            title=f"Healthcare Providers in {area}",
            content=content.strip(),
            category="provider_directory",
            source="provider_database",
            tags=["providers", area.lower().replace(' ', '_'), "locations"],
            metadata={
                "area": area,
                "provider_count": len(area_providers),
                "provider_types": list(set(p['provider_type'] for p in area_providers))
            }
        )
        documents.append(doc)

    # Create specialty-based summary documents
    providers_by_specialty = {}
    for provider in providers:
        if provider['specialties']:
            for specialty in provider['specialties']:
                if specialty not in providers_by_specialty:
                    providers_by_specialty[specialty] = []
                providers_by_specialty[specialty].append(provider)

    for specialty, specialty_providers in providers_by_specialty.items():
        provider_list = []
        for p in specialty_providers:
            provider_info = f"- {p['name']} in {p['area']}"
            if p['phone_primary']:
                provider_info += f" - Phone: {p['phone_primary']}"
            if p['address']:
                provider_info += f" - Location: {p['address']}"
            provider_list.append(provider_info)

        content = f"""
{specialty} Specialists - Premier Health Network:

Premier Health Insurance has {len(specialty_providers)} providers offering {specialty} services across Greater Accra.

Available {specialty} Providers:
{chr(10).join(provider_list)}

Coverage Information:
- All listed providers accept Premier Health Insurance
- No referral needed for initial consultation
- Present your Premier Health ID card when visiting
- Services covered under standard policy benefits

Areas Covered:
{', '.join(sorted(set(p['area'] for p in specialty_providers if p['area'])))}

To schedule an appointment, contact the provider directly using the phone numbers listed above.
"""

        doc = KnowledgeDocument(
            id=f"providers_specialty_{specialty.lower().replace(' ', '_').replace('/', '_')}",
            title=f"{specialty} Providers - Premier Health Network",
            content=content.strip(),
            category="specialty_directory",
            source="provider_database",
            tags=["providers", "specialty", specialty.lower().replace(' ', '_')],
            metadata={
                "specialty": specialty,
                "provider_count": len(specialty_providers),
                "areas": list(set(p['area'] for p in specialty_providers if p['area']))
            }
        )
        documents.append(doc)

    # Create provider type documents (hospitals, clinics, pharmacies)
    providers_by_type = {}
    for provider in providers:
        ptype = provider['provider_type'] or 'Other'
        if ptype not in providers_by_type:
            providers_by_type[ptype] = []
        providers_by_type[ptype].append(provider)

    for ptype, type_providers in providers_by_type.items():
        provider_list = []
        for p in type_providers:
            provider_info = f"- {p['name']} in {p['area']}"
            if p['specialties']:
                provider_info += f" - Services: {', '.join(p['specialties'][:3])}"
            if p['phone_primary']:
                provider_info += f" - Phone: {p['phone_primary']}"
            provider_list.append(provider_info)

        content = f"""
{ptype.title()} Facilities - Premier Health Network:

Premier Health Insurance partners with {len(type_providers)} {ptype} facilities across Greater Accra.

Available {ptype.title()} Facilities:
{chr(10).join(provider_list)}

Facility Type: {ptype.title()}
Total Locations: {len(type_providers)}
Coverage: All Greater Accra Region

What to Expect:
- Present your Premier Health ID card upon arrival
- All listed facilities are verified network providers
- Services billed directly to Premier Health
- No upfront payment required for covered services

Geographic Distribution:
{', '.join(sorted(set(p['area'] for p in type_providers if p['area'])))}
"""

        doc = KnowledgeDocument(
            id=f"providers_type_{ptype.lower().replace(' ', '_')}",
            title=f"{ptype.title()} Facilities - Premier Health Network",
            content=content.strip(),
            category="provider_type",
            source="provider_database",
            tags=["providers", ptype.lower(), "facilities"],
            metadata={
                "provider_type": ptype,
                "provider_count": len(type_providers),
                "areas": list(set(p['area'] for p in type_providers if p['area']))
            }
        )
        documents.append(doc)

    return documents

async def index_providers_to_rag():
    """Index healthcare providers into RAG knowledge base."""
    print("🏥 Indexing Healthcare Providers to RAG Knowledge Base")
    print("=" * 60)

    try:
        # Fetch providers from database
        print("\n1. Fetching providers from database...")
        providers = fetch_providers()
        print(f"   Found {len(providers)} active providers")

        # Create knowledge documents
        print("\n2. Creating knowledge documents...")
        documents = create_provider_documents(providers)
        print(f"   Created {len(documents)} knowledge documents")

        # Show document breakdown
        area_docs = [d for d in documents if d.category == "provider_directory"]
        specialty_docs = [d for d in documents if d.category == "specialty_directory"]
        type_docs = [d for d in documents if d.category == "provider_type"]

        print(f"   - Area-based documents: {len(area_docs)}")
        print(f"   - Specialty-based documents: {len(specialty_docs)}")
        print(f"   - Provider type documents: {len(type_docs)}")

        # Update knowledge base
        print("\n3. Indexing documents to RAG system...")
        result = await helpdesk_rag_service.update_knowledge_base(
            company_name="premier_health_production",
            documents=documents
        )

        print(f"\n✅ Providers Indexed Successfully!")
        print(f"   Documents updated: {result['documents_updated']}")
        print(f"   Chunks created: {result['chunks_updated']}")
        print(f"   Collection: {result['collection_name']}")
        print(f"   Updated at: {result['updated_at']}")

        # Show sample documents
        print(f"\n📋 Sample Indexed Documents:")
        for doc in documents[:3]:
            print(f"   - {doc.title} ({doc.category})")

        print(f"\n✅ Provider Indexing Complete!")

    except Exception as e:
        print(f"\n❌ Error indexing providers: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(index_providers_to_rag())
