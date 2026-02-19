#!/usr/bin/env python3
"""
Upload all regional data with proper region metadata.

This script processes all regional CSV files and uploads them with region tags
to enable proper geographic filtering in RAG queries.
"""

import sys
import asyncio
import pandas as pd
from pathlib import Path
from typing import Dict, List

sys.path.append('/opt/kasaai/apps/core_backend')

from backend.services.pg_document_service import pg_document_service
from backend.models.knowledge_base import DocumentCreate

COLLECTION_NAME = "premier_health_production"

# Regional CSV files and their corresponding regions
REGION_FILES = {
    "all_northern_regions_enriched.csv": ["NORTHERN", "UPPER WEST", "UPPER EAST", "NORTH EAST", "SAVANNAH"],
    "ashanti_region_kumasi_enriched.csv": ["ASHANTI"],
    "bono_regions_enriched.csv": ["BONO", "BONO EAST", "AHAFO"],
    "central_and_western_region_enriched.csv": ["CENTRAL", "WESTERN", "WESTERN NORTH"],
    "eastern_and_volta_regions_enriched.csv": ["EASTERN", "VOLTA", "OTI"],
    "greater_accra_region_enriched.csv": ["GREATER ACCRA"],
}

# Manual region assignments for known cities
CITY_TO_REGION = {
    # Greater Accra
    "ACCRA CENTRAL": "GREATER ACCRA", "TUDU": "GREATER ACCRA", "MAKOLA": "GREATER ACCRA",
    "KANESHIE": "GREATER ACCRA", "CIRCLE": "GREATER ACCRA", "KOKOMLEMLE": "GREATER ACCRA",
    "DZORWULU": "GREATER ACCRA", "ASYLUM DOWN": "GREATER ACCRA", "ADABRAKA": "GREATER ACCRA",
    "37 AREA": "GREATER ACCRA", "AIRPORT RESIDENTIAL AREA": "GREATER ACCRA",
    "EAST LEGON": "GREATER ACCRA", "CANTONMENTS": "GREATER ACCRA", "LABONE": "GREATER ACCRA",
    "OSU": "GREATER ACCRA", "TESANO": "GREATER ACCRA", "ABELENKPE": "GREATER ACCRA",
    "ACHIMOTA & NEW ACHIMOTA": "GREATER ACCRA", "DOME": "GREATER ACCRA",
    "ASHONGMAN": "GREATER ACCRA", "MADINA": "GREATER ACCRA", "ADENTA": "GREATER ACCRA",
    "HAATSO": "GREATER ACCRA", "TANTRA HILL": "GREATER ACCRA", "ADJRINGANOR": "GREATER ACCRA",
    "TSE ADDO": "GREATER ACCRA", "NUNGUA": "GREATER ACCRA", "TESHIE & NUNGUA": "GREATER ACCRA",
    "SPINTEX": "GREATER ACCRA", "BAATSONA": "GREATER ACCRA", "SAKUMONO": "GREATER ACCRA",
    "TEMA": "GREATER ACCRA", "ASHAIMAN": "GREATER ACCRA", "DODOWA": "GREATER ACCRA",
    "KASOA": "GREATER ACCRA", "WEIJA": "GREATER ACCRA", "GBAWE": "GREATER ACCRA",
    "DANSOMAN": "GREATER ACCRA", "DARKUMAN": "GREATER ACCRA", "AMANSAMAN": "GREATER ACCRA",
    "POKUASE": "GREATER ACCRA", "AMASAMAN": "GREATER ACCRA", "KWABENYA": "GREATER ACCRA",
    "INDUSTRIAL AREA": "GREATER ACCRA", "AFIENYA ROAD": "GREATER ACCRA",
    
    # Tema Communities and numbered areas
    "TEMA COMMUNITY 2": "GREATER ACCRA", "TEMA COMMUNITY 3": "GREATER ACCRA",
    "TEMA COMMUNITY 4": "GREATER ACCRA", "TEMA COMMUNITY 5": "GREATER ACCRA",
    "TEMA COMMUNITY 6": "GREATER ACCRA", "TEMA COMMUNITY 7": "GREATER ACCRA",
    "TEMA COMMUNITY 8": "GREATER ACCRA", "TEMA COMMUNITY 9": "GREATER ACCRA",
    "4": "GREATER ACCRA", "5": "GREATER ACCRA", "6": "GREATER ACCRA",
    "7": "GREATER ACCRA", "8": "GREATER ACCRA", "9": "GREATER ACCRA",
    "10": "GREATER ACCRA", "12": "GREATER ACCRA", "13": "GREATER ACCRA",
    "14": "GREATER ACCRA", "15": "GREATER ACCRA", "16": "GREATER ACCRA",
    "17": "GREATER ACCRA", "18": "GREATER ACCRA", "19": "GREATER ACCRA",
    "20": "GREATER ACCRA", "21": "GREATER ACCRA", "22": "GREATER ACCRA",
    "23": "GREATER ACCRA", "24": "GREATER ACCRA", "25": "GREATER ACCRA",
    "26": "GREATER ACCRA", "27": "GREATER ACCRA",
    "COMMUNITY 26": "GREATER ACCRA", "COMMUNITY 27": "GREATER ACCRA",
    "COMMUNITY 28": "GREATER ACCRA", "COMMUNITY 29": "GREATER ACCRA",
    "COMMUNITY 30": "GREATER ACCRA", "COMMUNITY 31": "GREATER ACCRA",
    "COMMUNITY 32": "GREATER ACCRA", "COMMUNITY 33": "GREATER ACCRA",
    "COMMUNITY 34": "GREATER ACCRA", "COMMUNITY 35": "GREATER ACCRA",
    "COMMUNITY 36": "GREATER ACCRA", "COMMUNITY 37": "GREATER ACCRA",
    "COMMUNITY 38": "GREATER ACCRA", "COMMUNITY 39": "GREATER ACCRA",
    "COMMUNITY 40": "GREATER ACCRA", "COMMUNITY 41": "GREATER ACCRA",
    "COMM. 18,19,21": "GREATER ACCRA", "COMM. 18,19,22": "GREATER ACCRA",
    "COMM. 18,19,23": "GREATER ACCRA", "COMM. 18,19,24": "GREATER ACCRA",
    "COMM. 18,19,25": "GREATER ACCRA", "COMM. 18,19,26": "GREATER ACCRA",
    "COMM. 18,19,27": "GREATER ACCRA", "COMM. 18,19,28": "GREATER ACCRA",
    "COMM. 18,19,29": "GREATER ACCRA", "COMM. 18,19,30": "GREATER ACCRA",
    "COMM. 18,19,31": "GREATER ACCRA", "COMM. 18,19,32": "GREATER ACCRA",
    "COMM. 18,19,33": "GREATER ACCRA", "COMM. 18,19,34": "GREATER ACCRA",
    "COMM. 18,19,35": "GREATER ACCRA", "COMM. 18,19,36": "GREATER ACCRA",
    "COMM. 18,19,37": "GREATER ACCRA", "COMM. 18,19,38": "GREATER ACCRA",
    "COMM. 22": "GREATER ACCRA",
    
    # Ashanti
    "ABREPO": "ASHANTI", "ADUM": "ASHANTI", "AHINSAN": "ASHANTI",
    "AHODWO": "ASHANTI", "ASOKWA": "ASHANTI", "BANTAMA": "ASHANTI",
    "BOMSO": "ASHANTI", "BREMANG": "ASHANTI", "EJISU": "ASHANTI",
    "KNUST": "ASHANTI", "KONONGO": "ASHANTI", "MAMPONG": "ASHANTI",
    "TANOSO": "ASHANTI", "WIAMOASE": "ASHANTI", "AGOGO": "ASHANTI",
    
    # Central
    "ASSIN": "CENTRAL", "SWEDRU": "CENTRAL", "AJUMAKO": "CENTRAL",
    "ASIKUMA": "CENTRAL",
    
    # Western
    "ABUAKWA": "WESTERN",
    
    # Eastern
    "ANYINAM": "EASTERN", "BEGORO": "EASTERN", "ENYIRESI": "EASTERN",
    "KIBI": "EASTERN", "OSINO": "EASTERN", "ASIAKWA": "EASTERN",
}


def get_region_from_csv_row(row: pd.Series, csv_file: str) -> str:
    """Extract region from CSV row."""
    # Try to get region from CSV
    if 'region' in row.index and pd.notna(row['region']):
        return str(row['region']).strip().upper()
    
    # Fall back to file-based region mapping
    regions = REGION_FILES.get(csv_file, [])
    return regions[0] if regions else "UNKNOWN"


def process_csv_to_documents(csv_path: Path) -> Dict[str, List[Dict]]:
    """Process CSV and group providers by city with region metadata."""
    print(f"\n📄 Processing {csv_path.name}...")

    df = pd.read_csv(csv_path)
    cities_data = {}

    for _, row in df.iterrows():
        # Extract city name
        city = str(row.get('city', '')).strip().upper() if 'city' in row.index else ''

        if not city or city == 'NAN':
            continue

        # Get region
        region = get_region_from_csv_row(row, csv_path.name)

        # Split compound city names by slash or ampersand
        # Examples: "ACCRA CENTRAL / TUDU / MAKOLA" or "TESHIE & NUNGUA"
        # Reason: Allow separate searches for each city
        if '/' in city:
            individual_cities = [c.strip() for c in city.split('/')]
        elif '&' in city:
            individual_cities = [c.strip() for c in city.split('&')]
        else:
            individual_cities = [city]

        # Add provider
        provider = {
            'name': str(row.get('NAME OF HOSPITAL / CLINIC', '')).strip(),
            'specialty': str(row.get('SPECIALITY', '')).strip(),
            'contact': str(row.get('CONTACT number', '') or row.get('CONTACT #', '')).strip(),
            'location': str(row.get('LOCATION', '')).strip(),
        }

        if provider['name'] and provider['name'] != 'nan':
            # Add provider to each individual city
            for individual_city in individual_cities:
                if not individual_city:  # Skip empty strings
                    continue

                # Initialize city data if not exists
                if individual_city not in cities_data:
                    cities_data[individual_city] = {
                        'providers': [],
                        'region': region
                    }

                cities_data[individual_city]['providers'].append(provider)

    print(f"   ✅ Found {len(cities_data)} cities (after splitting compound names)")
    return cities_data


def create_document_content(city: str, region: str, providers: List[Dict]) -> str:
    """Create markdown document content."""
    content = f"# Healthcare Providers in {city}\n\n"
    content += f"This document lists all Premier Health Insurance network providers in {city}, Ghana.\n\n"
    content += f"## {city}\n"
    content += f"**Region**: {region}\n\n"
    content += "---\n\n"
    
    for provider in providers:
        content += f"## {provider['name']}\n"
        if provider['specialty']:
            content += f"**Specialties**: {provider['specialty']}\n"
        if provider['contact']:
            content += f"**Phone**: {provider['contact']}\n"
        if provider['location']:
            content += f"**Location**: {provider['location']}\n"
        content += f"**Region**: {region}\n"
        content += "\n---\n\n"
    
    return content


async def upload_documents():
    """Upload all documents with region metadata."""
    print("📤 UPLOADING DOCUMENTS WITH REGION METADATA")
    print("=" * 80)
    
    csv_dir = Path("/opt/kasaai/apps/automations/premier-health/regional_cities/enriched/")
    
    total_cities = 0
    total_uploaded = 0
    total_errors = 0
    
    for csv_file in REGION_FILES.keys():
        csv_path = csv_dir / csv_file
        
        if not csv_path.exists():
            print(f"⚠️  Skipping {csv_file} - not found")
            continue
        
        # Process CSV
        cities_data = process_csv_to_documents(csv_path)
        total_cities += len(cities_data)
        
        # Upload each city document
        for city, data in cities_data.items():
            # Get region (from CSV or manual mapping)
            region = data['region']
            if city in CITY_TO_REGION:
                region = CITY_TO_REGION[city]
            
            # Create document content
            content = create_document_content(city, region, data['providers'])
            
            # Create document
            doc = DocumentCreate(
                title=f"Healthcare Providers in {city}",
                content=content,
                category="healthcare",
                collection_name=COLLECTION_NAME,
                company_name=COLLECTION_NAME,
                tags=[region, "healthcare", "providers"],  # Region tag here!
                metadata={
                    "region": region,
                    "city": city,
                    "provider_count": len(data['providers']),
                    "source": "regional_csv_with_metadata"
                }
            )
            
            # Upload
            try:
                result = await pg_document_service.create_document(doc)
                if result.success:
                    print(f"✅ {city} ({region}) - {len(data['providers'])} providers")
                    total_uploaded += 1
                else:
                    print(f"❌ {city} - Error: {result.error}")
                    total_errors += 1
            except Exception as e:
                print(f"❌ {city} - Exception: {str(e)}")
                total_errors += 1
    
    print("\n" + "=" * 80)
    print("📊 UPLOAD SUMMARY")
    print("=" * 80)
    print(f"Total cities processed: {total_cities}")
    print(f"Successfully uploaded: {total_uploaded}")
    print(f"Errors: {total_errors}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(upload_documents())
