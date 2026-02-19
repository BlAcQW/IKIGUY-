#!/usr/bin/env python3
"""
Add region metadata to all documents based on source CSV files.

This will enable proper filtering by region in RAG queries.
"""

import pandas as pd
import psycopg2
from pathlib import Path
import json

POSTGRES_PASSWORD = "aawwER444444"
COLLECTION_NAME = "helpdesk_premier_health_production"

# Mapping of CSV files to their regions
REGION_FILES = {
    "all_northern_regions_enriched.csv": ["NORTHERN", "UPPER WEST", "UPPER EAST", "NORTH EAST", "SAVANNAH"],
    "ashanti_region_kumasi_enriched.csv": ["ASHANTI"],
    "bono_regions_enriched.csv": ["BONO", "BONO EAST", "AHAFO"],
    "central_and_western_region_enriched.csv": ["CENTRAL", "WESTERN", "WESTERN NORTH"],
    "eastern_and_volta_regions_enriched.csv": ["EASTERN", "VOLTA", "OTI"],
    "greater_accra_region_enriched.csv": ["GREATER ACCRA"],
}

def get_db_connection():
    """Get PostgreSQL database connection."""
    return psycopg2.connect(
        host="127.0.0.1",
        database="kasaai_core",
        user="postgres",
        password=POSTGRES_PASSWORD
    )


def extract_city_to_region_mapping():
    """Extract city to region mapping from CSV files."""
    csv_dir = Path("/opt/kasaai/apps/automations/premier-health/regional_cities/enriched/")
    city_to_region = {}

    for csv_file, possible_regions in REGION_FILES.items():
        csv_path = csv_dir / csv_file
        if not csv_path.exists():
            print(f"⚠️  Skipping {csv_file} - file not found")
            continue

        print(f"\n📄 Processing {csv_file}...")
        df = pd.read_csv(csv_path)

        # Get unique city-region pairs
        if 'region' in df.columns and 'city' in df.columns:
            for _, row in df.iterrows():
                city = str(row.get('city', '')).strip().upper()
                region = str(row.get('region', '')).strip().upper()

                if city and region and city != 'NAN' and region != 'NAN':
                    # Check for conflicts
                    if city in city_to_region and city_to_region[city] != region:
                        print(f"   ⚠️  City {city} appears in multiple regions: {city_to_region[city]} and {region}")
                    else:
                        city_to_region[city] = region

    print(f"\n✅ Extracted {len(city_to_region)} city-region mappings")
    return city_to_region


def add_region_metadata():
    """Add region metadata to all documents."""
    print("🏷️  ADDING REGION METADATA TO DOCUMENTS")
    print("=" * 80)

    # Get city to region mapping
    city_to_region = extract_city_to_region_mapping()

    # Connect to database
    conn = get_db_connection()
    cur = conn.cursor()

    # Get all documents
    cur.execute("""
        SELECT id, title, tags
        FROM kb_documents
        WHERE collection_name = %s
        ORDER BY title
    """, (COLLECTION_NAME,))

    documents = cur.fetchall()
    print(f"\n📄 Found {len(documents)} documents to update")

    updated_count = 0
    no_match_count = 0
    no_match_cities = []

    for doc_id, title, tags in documents:
        # Extract city name from title
        if not title.startswith("Healthcare Providers in "):
            print(f"⚠️  Skipping {title} - unexpected format")
            continue

        city = title.replace("Healthcare Providers in ", "").strip().upper()

        # Find region for this city
        region = city_to_region.get(city)

        if region:
            # Update tags to include region
            current_tags = tags if tags else []

            # Add region tag if not already present
            if region not in current_tags:
                new_tags = current_tags + [region]

                cur.execute("""
                    UPDATE kb_documents
                    SET tags = %s
                    WHERE id = %s
                """, (new_tags, doc_id))

                print(f"✅ {city} → {region}")
                updated_count += 1
        else:
            no_match_count += 1
            no_match_cities.append(city)
            print(f"❌ No region found for: {city}")

    conn.commit()

    # Also update embeddings metadata
    print("\n🔄 Updating embeddings metadata...")

    # Get collection UUID
    cur.execute("""
        SELECT uuid FROM langchain_pg_collection
        WHERE name = %s
    """, (COLLECTION_NAME,))
    collection_uuid = cur.fetchone()[0]

    cur.execute("""
        SELECT DISTINCT
            d.id,
            d.title,
            d.tags,
            d.vector_ids
        FROM kb_documents d
        WHERE d.collection_name = %s
        AND d.tags IS NOT NULL
        AND array_length(d.vector_ids, 1) > 0
    """, (COLLECTION_NAME,))

    docs_with_regions = cur.fetchall()
    embeddings_updated = 0

    for doc_id, title, tags, vector_ids in docs_with_regions:
        # Extract region from tags
        regions = [tag for tag in tags if tag in set(city_to_region.values())]

        if regions:
            region = regions[0]  # Use first region if multiple

            # Update embeddings cmetadata
            for vector_id in vector_ids:
                cur.execute("""
                    UPDATE langchain_pg_embedding
                    SET cmetadata = jsonb_set(
                        COALESCE(cmetadata, '{}'::jsonb),
                        '{region}',
                        %s::jsonb
                    )
                    WHERE id = %s
                    AND collection_id = %s
                """, (json.dumps(region), str(vector_id), collection_uuid))

                embeddings_updated += 1

    conn.commit()
    cur.close()
    conn.close()

    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Documents updated: {updated_count}")
    print(f"Embeddings updated: {embeddings_updated}")
    print(f"No region match: {no_match_count}")

    if no_match_cities:
        print(f"\n❌ Cities without region mapping ({len(no_match_cities)}):")
        for city in sorted(no_match_cities)[:20]:  # Show first 20
            print(f"   - {city}")
        if len(no_match_cities) > 20:
            print(f"   ... and {len(no_match_cities) - 20} more")

    print("=" * 80)


if __name__ == "__main__":
    add_region_metadata()
