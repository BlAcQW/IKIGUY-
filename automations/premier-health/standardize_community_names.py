#!/usr/bin/env python3
"""
Standardize Community Document Names in Knowledge Base

This script standardizes all community document names to "TEMA COMMUNITY X" format
and removes duplicates by keeping the version with more providers.

Author: Claude Code
Date: October 28, 2025
"""

import os
import sys
import psycopg2
from typing import List, Dict, Tuple
import re

# Database configuration
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "aawwER444444")
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "user": "postgres",
    "password": POSTGRES_PASSWORD,
    "database": "kasaai_core"
}

COLLECTION_NAME = "helpdesk_premier_health_production"
STANDARD_FORMAT = "TEMA COMMUNITY"


def extract_community_number(title: str) -> int:
    """Extract community number from title."""
    match = re.search(r'(\d+)', title)
    return int(match.group(1)) if match else 0


def count_providers(content: str) -> int:
    """Count number of providers in document content."""
    # Providers are marked with "## PROVIDER_NAME"
    return len(re.findall(r'\n## [A-Z]', content))


def get_all_community_documents(cursor) -> List[Dict]:
    """Fetch all community documents from KB."""
    cursor.execute("""
        SELECT id, title, content, LENGTH(content) as content_length
        FROM kb_documents
        WHERE collection_name = %s
          AND (title ILIKE '%%tema community%%' OR title ILIKE '%%community%%')
        ORDER BY title
    """, (COLLECTION_NAME,))

    documents = []
    rows = cursor.fetchall()

    for row in rows:
        try:
            doc_id = row[0]
            title = row[1]
            content = row[2]
            content_length = row[3]

            provider_count = count_providers(content)
            comm_num = extract_community_number(title)

            documents.append({
                'id': doc_id,
                'title': title,
                'content': content,
                'content_length': content_length,
                'provider_count': provider_count,
                'community_number': comm_num
            })
        except Exception as e:
            print(f"Error processing row: {e}")
            continue

    return documents


def find_duplicates(documents: List[Dict]) -> Dict[int, List[Dict]]:
    """Group documents by community number to find duplicates."""
    grouped = {}
    for doc in documents:
        num = doc['community_number']
        if num not in grouped:
            grouped[num] = []
        grouped[num].append(doc)

    # Return only groups with duplicates
    return {num: docs for num, docs in grouped.items() if len(docs) > 1}


def choose_best_version(docs: List[Dict]) -> Tuple[Dict, List[Dict]]:
    """
    Choose the best version to keep (most providers) and return others to delete.

    Returns:
        (best_doc, docs_to_delete)
    """
    # Sort by provider count (descending), then by content length
    sorted_docs = sorted(docs, key=lambda d: (d['provider_count'], d['content_length']), reverse=True)

    best = sorted_docs[0]
    to_delete = sorted_docs[1:]

    return best, to_delete


def standardize_title(community_number: int) -> str:
    """Create standardized title."""
    return f"Healthcare Providers in {STANDARD_FORMAT} {community_number}"


def main():
    """Main execution function."""
    print("="*80)
    print("COMMUNITY DOCUMENT STANDARDIZATION")
    print("="*80)
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Standard Format: {STANDARD_FORMAT} X")
    print("="*80)
    print()

    # Connect to database
    print("📊 Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # Fetch all documents
        print("📚 Fetching all community documents...")
        documents = get_all_community_documents(cursor)
        print(f"   Found {len(documents)} community documents")
        print()

        # Find duplicates
        print("🔍 Analyzing for duplicates...")
        duplicates = find_duplicates(documents)
        print(f"   Found {len(duplicates)} sets of duplicates")
        print()

        # Process duplicates
        if duplicates:
            print("🗑️  Processing duplicates:")
            print("-"*80)

            for comm_num, docs in sorted(duplicates.items()):
                print(f"\n📌 Community {comm_num} ({len(docs)} versions):")

                for doc in docs:
                    print(f"   - {doc['title']}")
                    print(f"     Providers: {doc['provider_count']}, Length: {doc['content_length']}")

                # Choose best version
                best, to_delete = choose_best_version(docs)

                print(f"\n   ✅ KEEP: {best['title']} ({best['provider_count']} providers)")
                for doc in to_delete:
                    print(f"   ❌ DELETE: {doc['title']} ({doc['provider_count']} providers)")

                # Delete duplicates
                for doc in to_delete:
                    cursor.execute("""
                        DELETE FROM kb_documents
                        WHERE id = %s
                    """, (doc['id'],))
                    print(f"      ✓ Deleted: {doc['title']}")

            conn.commit()
            print()
            print(f"✅ Deleted {sum(len(docs)-1 for docs in duplicates.values())} duplicate documents")
            print()

        # Refresh document list after deletes
        documents = get_all_community_documents(cursor)

        # Standardize all titles
        print("📝 Standardizing document titles:")
        print("-"*80)

        renamed_count = 0
        for doc in documents:
            standard_title = standardize_title(doc['community_number'])

            if doc['title'] != standard_title:
                print(f"   {doc['title']}")
                print(f"   → {standard_title}")

                cursor.execute("""
                    UPDATE kb_documents
                    SET title = %s
                    WHERE id = %s
                """, (standard_title, doc['id']))

                renamed_count += 1

        if renamed_count > 0:
            conn.commit()
            print()
            print(f"✅ Renamed {renamed_count} documents to standard format")
        else:
            print("   All documents already in standard format")

        print()

        # Final verification
        print("✅ Verification:")
        print("-"*80)
        cursor.execute("""
            SELECT title
            FROM kb_documents
            WHERE collection_name = %s
              AND title LIKE %s
            ORDER BY title
        """, (COLLECTION_NAME, f'%{STANDARD_FORMAT}%'))

        final_docs = cursor.fetchall()
        print(f"   Total standardized documents: {len(final_docs)}")

        if final_docs:
            print("\n   Standard documents:")
            for row in final_docs[:5]:  # Show first 5
                print(f"      ✓ {row[0]}")
            if len(final_docs) > 5:
                print(f"      ... and {len(final_docs) - 5} more")

        # Check for any remaining non-standard docs
        cursor.execute("""
            SELECT title
            FROM kb_documents
            WHERE collection_name = %s
              AND (title ILIKE '%%community%%')
              AND title NOT LIKE %s
            ORDER BY title
        """, (COLLECTION_NAME, f'%{STANDARD_FORMAT}%'))

        non_standard = cursor.fetchall()
        if non_standard:
            print(f"\n   ⚠️  WARNING: {len(non_standard)} non-standard documents found:")
            for row in non_standard:
                print(f"      - {row[0]}")
        else:
            print("\n   ✅ All community documents are now standardized!")

        print()
        print("="*80)
        print("✅ STANDARDIZATION COMPLETE")
        print("="*80)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        sys.exit(1)

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
