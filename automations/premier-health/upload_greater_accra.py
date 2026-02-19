#!/usr/bin/env python3
"""Upload Greater Accra documents only."""

import sys
import asyncio
import pandas as pd
from pathlib import Path
from typing import Dict, List

sys.path.append('/opt/kasaai/apps/core_backend')

from backend.services.pg_document_service import pg_document_service
from backend.models.knowledge_base import DocumentCreate

COLLECTION_NAME = "premier_health_production"

async def upload_greater_accra():
    """Upload Greater Accra documents."""
    print("📤 UPLOADING GREATER ACCRA DOCUMENTS")
    print("=" * 80)
    
    csv_path = Path("/opt/kasaai/apps/automations/premier-health/regional_cities/enriched/greater_accra_region_enriched.csv")
    
    df = pd.read_csv(csv_path)
    cities_data = {}
    
    for _, row in df.iterrows():
        city = str(row.get('city', '')).strip().upper()
        
        if not city or city == 'NAN':
            continue
        
        # Split by slash or ampersand
        if '/' in city:
            individual_cities = [c.strip() for c in city.split('/')]
        elif '&' in city:
            individual_cities = [c.strip() for c in city.split('&')]
        else:
            individual_cities = [city]
        
        provider = {
            'name': str(row.get('NAME OF HOSPITAL / CLINIC', '')).strip(),
            'specialty': str(row.get('SPECIALITY', '')).strip(),
            'contact': str(row.get('CONTACT number', '')).strip(),
            'location': str(row.get('LOCATION', '')).strip(),
        }
        
        if provider['name'] and provider['name'] != 'nan':
            for individual_city in individual_cities:
                if not individual_city:
                    continue
                if individual_city not in cities_data:
                    cities_data[individual_city] = []
                cities_data[individual_city].append(provider)
    
    print(f"Found {len(cities_data)} Greater Accra cities")
    
    uploaded = 0
    for city, providers in cities_data.items():
        content = f"# Healthcare Providers in {city}\n\n"
        content += f"This document lists all Premier Health Insurance network providers in {city}, Ghana.\n\n"
        content += f"## {city}\n"
        content += f"**Region**: GREATER ACCRA\n\n---\n\n"
        
        for provider in providers:
            content += f"## {provider['name']}\n"
            if provider['specialty']:
                content += f"**Specialties**: {provider['specialty']}\n"
            if provider['contact']:
                content += f"**Phone**: {provider['contact']}\n"
            if provider['location']:
                content += f"**Location**: {provider['location']}\n"
            content += f"**Region**: GREATER ACCRA\n\n---\n\n"
        
        doc = DocumentCreate(
            title=f"Healthcare Providers in {city}",
            content=content,
            category="healthcare",
            collection_name=COLLECTION_NAME,
            company_name=COLLECTION_NAME,
            tags=["GREATER ACCRA", "healthcare", "providers"],
            metadata={
                "region": "GREATER ACCRA",
                "city": city,
                "provider_count": len(providers),
                "source": "regional_csv_with_metadata"
            }
        )
        
        try:
            result = await pg_document_service.create_document(doc)
            if result.success:
                print(f"✅ {city} - {len(providers)} providers")
                uploaded += 1
            else:
                print(f"❌ {city} - Error: {result.error}")
        except Exception as e:
            print(f"❌ {city} - Exception: {str(e)}")
    
    print(f"\n✅ Uploaded {uploaded} Greater Accra cities")

if __name__ == "__main__":
    asyncio.run(upload_greater_accra())
