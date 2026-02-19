#!/usr/bin/env python3
"""
Fix broken city embeddings by regenerating them with improved content structure.
The issue is that some cities have content but poor embeddings that don't match queries.
"""

import os
import sys
import psycopg2
import google.generativeai as genai
from typing import List, Dict, Tuple

# Configuration
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "aawwER444444")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
COLLECTION_NAME = "helpdesk_premier_health_production"

# List of broken cities from audit
BROKEN_CITIES = [
    'AKWATIA', 'AKOSOMBO', 'SUHUM', 'SEFWI ASAWINSO', 'SEFWI BEKWAI',
    'SEFWI ANHWIASO', 'ASANKRAGWA', 'BOGOSO', 'AJUMAKO', 'ASIKUMA',
    'MANKESSIM', 'ASSIN', 'WENCHI', 'KENYASE', 'TSE ADDO', 'RIDGE',
    'MAKOLA', 'LATEBIOKOSHIE', 'LA', 'KWABENYA', 'KOKOMLEMLE',
    'DARKUMAN', 'COMMUNITY 38', 'AMANSAMAN', 'ADJRINGANOR', 'ADABRAKA',
    'ACCRA CENTRAL', 'ABELENKPE', 'Akosombo', 'Adabraka'
]

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


def get_db_connection():
    """Get PostgreSQL database connection."""
    return psycopg2.connect(
        host="127.0.0.1",
        database="kasaai_core",
        user="postgres",
        password=POSTGRES_PASSWORD
    )


def generate_embedding(text: str) -> List[float]:
    """Generate embedding using Gemini API."""
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None


def improve_content_for_embedding(title: str, content: str) -> str:
    """
    Improve content structure to generate better embeddings.
    Add city name repetition and clear structure.
    """
    # Extract city name from title
    city_name = title.replace("Healthcare Providers in ", "")

    # Create improved content with city name prominence
    improved = f"""# Healthcare Providers in {city_name}

This document contains information about healthcare facilities, hospitals, clinics, and medical centers located in {city_name}, Ghana.

If you're looking for healthcare providers, hospitals, clinics, doctors, or medical facilities in {city_name}, this document has the complete list.

Location: {city_name}
Region: Ghana

{content}

---
For healthcare services in {city_name}, refer to the providers listed above.
"""

    return improved


def fix_broken_city_embeddings(dry_run: bool = False):
    """Fix embeddings for broken cities."""
    conn = get_db_connection()
    cur = conn.cursor()

    print("🔧 FIXING BROKEN CITY EMBEDDINGS")
    print("=" * 80)
    print(f"Total broken cities to fix: {len(BROKEN_CITIES)}")
    print("=" * 80)

    fixed_count = 0
    failed_count = 0

    for i, city in enumerate(BROKEN_CITIES, 1):
        try:
            # Find documents for this city
            cur.execute("""
                SELECT id, title, content
                FROM kb_documents
                WHERE collection_name = %s
                AND title ILIKE %s
            """, (COLLECTION_NAME, f"%{city}%"))

            docs = cur.fetchall()

            if not docs:
                print(f"[{i}/{len(BROKEN_CITIES)}] ⚠️  {city}: No documents found")
                failed_count += 1
                continue

            for doc_id, title, content in docs:
                print(f"\n[{i}/{len(BROKEN_CITIES)}] Processing: {title}")
                print(f"   Document ID: {doc_id}")
                print(f"   Original content length: {len(content)} chars")

                # Improve content for better embedding
                improved_content = improve_content_for_embedding(title, content)
                print(f"   Improved content length: {len(improved_content)} chars")

                if dry_run:
                    print(f"   [DRY RUN] Would regenerate embedding")
                    continue

                # Generate new embedding
                embedding = generate_embedding(improved_content)

                if not embedding:
                    print(f"   ❌ Failed to generate embedding")
                    failed_count += 1
                    continue

                # Update document content in kb_documents
                cur.execute("""
                    UPDATE kb_documents
                    SET content = %s
                    WHERE id = %s
                """, (improved_content, doc_id))

                # Update embedding in langchain_pg_embedding table
                # Find the embedding record by document_id
                cur.execute("""
                    UPDATE langchain_pg_embedding
                    SET
                        embedding = %s::vector,
                        document = %s
                    WHERE id IN (
                        SELECT unnest(vector_ids)
                        FROM kb_documents
                        WHERE id = %s
                    )
                """, (embedding, improved_content, doc_id))

                conn.commit()
                print(f"   ✅ Updated successfully")
                fixed_count += 1

        except Exception as e:
            print(f"   ❌ Error processing {city}: {e}")
            failed_count += 1
            conn.rollback()

    cur.close()
    conn.close()

    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Total cities processed: {len(BROKEN_CITIES)}")
    print(f"Successfully fixed: {fixed_count}")
    print(f"Failed: {failed_count}")
    print("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Fix broken city embeddings')
    parser.add_argument('--dry-run', action='store_true', help='Run without making changes')
    args = parser.parse_args()

    fix_broken_city_embeddings(dry_run=args.dry_run)
