#!/usr/bin/env python3
"""
Update Community Document Content to Match Standardized Titles

This script updates the CONTENT of community documents to match
the standardized "TEMA COMMUNITY X" format in both headers and section titles.

Author: Claude Code
Date: October 28, 2025
"""

import os
import sys
import psycopg2
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


def update_document_content(cursor, doc_id: str, title: str, old_content: str, community_number: int) -> bool:
    """
    Update document content to use standardized community name.

    Args:
        cursor: Database cursor
        doc_id: Document ID
        title: Document title
        old_content: Current content
        community_number: Community number (1-41)

    Returns:
        bool: True if content was updated, False if no changes needed
    """
    # Pattern variations to replace
    patterns_to_replace = [
        (f"# Healthcare Providers in COMMUNITY {community_number}",
         f"# Healthcare Providers in TEMA COMMUNITY {community_number}"),
        (f"# Healthcare Providers in Community {community_number}",
         f"# Healthcare Providers in TEMA COMMUNITY {community_number}"),
        (f"## COMMUNITY {community_number}",
         f"## TEMA COMMUNITY {community_number}"),
        (f"## Community {community_number}",
         f"## TEMA COMMUNITY {community_number}"),
        (f"providers in COMMUNITY {community_number}",
         f"providers in TEMA COMMUNITY {community_number}"),
        (f"providers in Community {community_number}",
         f"providers in TEMA COMMUNITY {community_number}"),
    ]

    new_content = old_content
    changes_made = False

    for old_pattern, new_pattern in patterns_to_replace:
        if old_pattern in new_content:
            new_content = new_content.replace(old_pattern, new_pattern)
            changes_made = True
            print(f"      Replaced: '{old_pattern}' → '{new_pattern}'")

    if changes_made:
        # Update the document
        cursor.execute("""
            UPDATE kb_documents
            SET content = %s
            WHERE id = %s
        """, (new_content, doc_id))
        return True

    return False


def main():
    """Main execution function."""
    print("=" * 80)
    print("UPDATE COMMUNITY DOCUMENT CONTENT")
    print("=" * 80)
    print(f"Collection: {COLLECTION_NAME}")
    print("Updating content to match standardized 'TEMA COMMUNITY X' format")
    print("=" * 80)
    print()

    # Connect to database
    print("📊 Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # Fetch all community documents
        print("📚 Fetching all community documents...")
        query = f"""
            SELECT id, title, content
            FROM kb_documents
            WHERE collection_name = '{COLLECTION_NAME}'
              AND title LIKE 'Healthcare Providers in TEMA COMMUNITY%'
            ORDER BY title
        """
        cursor.execute(query)

        documents = cursor.fetchall()
        print(f"   Found {len(documents)} community documents")
        print()

        # Update each document's content
        print("✏️  Updating document content:")
        print("-" * 80)

        updated_count = 0
        for row in documents:
            try:
                doc_id = row[0]
                title = row[1]
                content = row[2]

                # Extract community number from title
                match = re.search(r'TEMA COMMUNITY (\d+)', title)
                if not match:
                    print(f"   ⚠️  Skipping {title} - couldn't extract community number")
                    continue

                community_num = int(match.group(1))

                print(f"\n   📄 {title}")

                # Update content
                if update_document_content(cursor, doc_id, title, content, community_num):
                    updated_count += 1
                    print(f"      ✅ Content updated")
                else:
                    print(f"      ℹ️  No changes needed (already standardized)")

            except Exception as e:
                print(f"   ❌ Error processing row: {e}")
                print(f"      Row data: {row}")
                continue

        if updated_count > 0:
            conn.commit()
            print()
            print(f"✅ Updated content in {updated_count} documents")
        else:
            print()
            print("ℹ️  All documents already have standardized content")

        print()
        print("=" * 80)
        print("✅ CONTENT UPDATE COMPLETE")
        print("=" * 80)

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
