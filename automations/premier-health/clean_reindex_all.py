#!/usr/bin/env python3
"""
Complete cleanup and reindex of Premier Health database.
This script:
1. Deletes all existing documents and embeddings
2. Reads original CSV files
3. Properly indexes all documents with correct embeddings
"""

import os
import sys
import csv
from pathlib import Path
from typing import List, Dict

# Set required environment variables
os.environ["MONGODB_URL"] = "mongodb://admin:aawwER444444@127.0.0.1:27017/kasaai_core?authSource=admin"
os.environ["POSTGRES_PASSWORD"] = "aawwER444444"
os.environ["GEMINI_API_KEY"] = "AIzaSyAACjmMMYIVH2Pq8Ns8KbOud-X8oCQMny4"

sys.path.insert(0, '/opt/kasaai')

from apps.core_backend.backend.services.document_management_service import DocumentManagementService
import uuid

COLLECTION_NAME = "helpdesk_premier_health_production"
COMPANY_NAME = "premier_health"
CSV_DIR = Path("/opt/kasaai/apps/automations/premier-health/regional_cities/enriched")


def delete_all_existing_data(doc_service: DocumentManagementService):
    """Delete all existing documents and embeddings for the collection."""
    print("\n🗑️  STEP 1: Deleting all existing data")
    print("=" * 80)

    import psycopg2

    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="kasaai_core",
            user="postgres",
            password=os.getenv("POSTGRES_PASSWORD")
        )
        cur = conn.cursor()

        # Delete from kb_documents
        cur.execute("""
            DELETE FROM kb_documents
            WHERE collection_name = %s
        """, (COLLECTION_NAME,))
        deleted_docs = cur.rowcount
        print(f"✅ Deleted {deleted_docs} documents from kb_documents")

        # Delete from langchain_pg_embedding (find collection_id first)
        cur.execute("""
            SELECT uuid FROM langchain_pg_collection
            WHERE name = %s
        """, (COLLECTION_NAME,))

        result = cur.fetchone()
        if result:
            collection_id = result[0]
            cur.execute("""
                DELETE FROM langchain_pg_embedding
                WHERE collection_id = %s
            """, (collection_id,))
            deleted_embeddings = cur.rowcount
            print(f"✅ Deleted {deleted_embeddings} embeddings from langchain_pg_embedding")
        else:
            print(f"⚠️  No embedding collection found for {COLLECTION_NAME}")

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(f"⚠️  Error deleting data: {e}")

    print("=" * 80)


def read_csv_files() -> List[Dict]:
    """Read all enriched CSV files and extract city documents."""
    print("\n📂 STEP 2: Reading original CSV files")
    print("=" * 80)

    all_cities = {}  # Use dict to group by city
    csv_files = list(CSV_DIR.glob("*_enriched.csv"))

    print(f"Found {len(csv_files)} CSV files")

    for csv_file in csv_files:
        print(f"\n📄 Processing: {csv_file.name}")

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                # Skip first 2 header rows
                next(f)
                next(f)

                reader = csv.DictReader(f)

                for row in reader:
                    region = row.get('region', '').strip()
                    city = row.get('city', '').strip()
                    provider_name = row.get('NAME OF HOSPITAL / CLINIC', '').strip()
                    provider_number = row.get('provider number', '').strip()

                    # Skip empty rows
                    if not city:
                        continue

                    # Skip city header rows (no provider number)
                    if not provider_number:
                        continue

                    # Initialize city if not exists
                    if city not in all_cities:
                        all_cities[city] = {
                            'city': city,
                            'region': region,
                            'providers': []
                        }

                    # Add provider
                    all_cities[city]['providers'].append({
                        'name': provider_name,
                        'specialty': row.get('SPECIALITY', '').strip(),
                        'phone': row.get('CONTACT number', '').strip(),
                        'location': row.get('LOCATION', '').strip(),
                        'plan': ''  # Not in this CSV format
                    })

            print(f"   ✅ Extracted cities from {csv_file.name}")

        except Exception as e:
            print(f"   ❌ Error reading {csv_file.name}: {e}")
            import traceback
            traceback.print_exc()

    cities_list = list(all_cities.values())
    print("=" * 80)
    print(f"📊 Total cities extracted: {len(cities_list)}")
    return cities_list


def format_document_content(city_data: Dict) -> str:
    """Format city data into a clean document."""
    city = city_data['city']
    region = city_data['region']
    providers = city_data['providers']

    content = f"""# Healthcare Providers in {city}

This document lists all Premier Health Insurance network providers in {city}, {region}, Ghana.

**Location**: {city}
**Region**: {region}
**Total Providers**: {len(providers)}

---

"""

    for i, provider in enumerate(providers, 1):
        content += f"""## {i}. {provider['name']}

**Specialties**: {provider['specialty']}
**Phone**: {provider['phone']}
**Location**: {provider['location']}
**Plan**: {provider['plan']}
**City**: {city}
**Region**: {region}

---

"""

    content += f"""
For healthcare services in {city}, refer to the {len(providers)} providers listed above.
"""

    return content


def upload_and_index_documents(doc_service: DocumentManagementService, cities: List[Dict]):
    """Upload and index all city documents."""
    print("\n📤 STEP 3: Uploading and indexing documents")
    print("=" * 80)

    success_count = 0
    fail_count = 0

    for i, city_data in enumerate(cities, 1):
        city = city_data['city']

        try:
            print(f"\n[{i}/{len(cities)}] {city}")

            # Generate document content
            content = format_document_content(city_data)
            document_id = str(uuid.uuid4())
            title = f"Healthcare Providers in {city}"

            print(f"   Content length: {len(content)} chars")
            print(f"   Providers: {len(city_data['providers'])}")

            # Use index_document directly (synchronous method)
            doc_service.index_document(
                document_id=document_id,
                content=content,
                collection_name=COLLECTION_NAME,
                company_name=COMPANY_NAME,
                metadata={
                    "title": title,
                    "city": city,
                    "region": city_data['region'],
                    "provider_count": len(city_data['providers']),
                    "source": "clean_reindex"
                }
            )

            print(f"   ✅ Successfully indexed")
            success_count += 1

        except Exception as e:
            print(f"   ❌ Error: {e}")
            fail_count += 1

    print("\n" + "=" * 80)
    print("📊 UPLOAD SUMMARY")
    print("=" * 80)
    print(f"Successfully indexed: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Success rate: {success_count/len(cities)*100:.1f}%")
    print("=" * 80)


def main():
    """Main execution function."""
    print("🚀 COMPLETE CLEANUP AND REINDEX")
    print("=" * 80)
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Company: {COMPANY_NAME}")
    print(f"CSV Directory: {CSV_DIR}")
    print("=" * 80)

    # Initialize document service
    doc_service = DocumentManagementService()

    # Step 1: Delete all existing data
    delete_all_existing_data(doc_service)

    # Step 2: Read CSV files
    cities = read_csv_files()

    if not cities:
        print("❌ No cities found in CSV files!")
        return

    # Step 3: Upload and index
    upload_and_index_documents(doc_service, cities)

    print("\n✅ COMPLETE! Database has been cleaned and reindexed.")


if __name__ == "__main__":
    main()
