#!/usr/bin/env python3
"""
Fix Community Naming and Merge Duplicate Community Files

Fixes:
1. Rename COMM._X, COMM.X to COMMUNITY_X format
2. Merge duplicate community files (COMM._1 + COMMUNITY_1 -> COMMUNITY_1)
3. Update titles to use proper "Community X" format
4. Handle special cases like COMM.6 -> COMMUNITY_6
"""

import os
import re
from pathlib import Path

# Base directory
BASE_DIR = Path("/opt/kasaai/apps/automations/premier-health/processed_data/markdown_documents")

def extract_community_number(filename):
    """Extract community number from various filename formats"""
    # COMM._22 -> 22
    match = re.match(r'COMM\._(\d+)\.md', filename)
    if match:
        return match.group(1)

    # COMM.6 -> 6
    match = re.match(r'COMM\.(\d+)\.md', filename)
    if match:
        return match.group(1)

    # COMMUNITY_25 -> 25
    match = re.match(r'COMMUNITY_(\d+)\.md', filename)
    if match:
        return match.group(1)

    # COMM.md -> None (generic, needs manual handling)
    if filename == 'COMM.md':
        return None

    return None

def read_markdown_file(filepath):
    """Read markdown file content"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def write_markdown_file(filepath, content):
    """Write markdown file content"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def extract_facilities(content):
    """Extract facility sections from markdown content"""
    # Split by ## headers
    sections = re.split(r'\n## ', content)

    # First section is header, skip it
    if len(sections) > 1:
        facilities = []
        for section in sections[1:]:
            facilities.append('## ' + section.strip())
        return facilities
    return []

def merge_community_files(comm_number):
    """Merge COMM._X and COMMUNITY_X files if both exist"""
    old_format = BASE_DIR / f"COMM._{comm_number}.md"
    new_format = BASE_DIR / f"COMMUNITY_{comm_number}.md"

    old_exists = old_format.exists()
    new_exists = new_format.exists()

    if old_exists and new_exists:
        print(f"  Merging COMM._{comm_number} + COMMUNITY_{comm_number}")

        # Read both files
        old_content = read_markdown_file(old_format)
        new_content = read_markdown_file(new_format)

        # Extract facilities
        old_facilities = extract_facilities(old_content)
        new_facilities = extract_facilities(new_content)

        # Combine facilities
        all_facilities = new_facilities + old_facilities

        # Create new content
        header = f"""# Healthcare Providers in Community {comm_number}

This document lists all Premier Health Insurance network providers in Community {comm_number}, Ghana.

"""
        combined_content = header + "\n---\n\n".join(all_facilities) + "\n"

        # Update region references in content
        combined_content = combined_content.replace(f"**Region**: COMM. {comm_number}", f"**Region**: Community {comm_number}")
        combined_content = combined_content.replace(f"**Region**: COMMUNITY {comm_number}", f"**Region**: Community {comm_number}")

        # Write to COMMUNITY_X file
        write_markdown_file(new_format, combined_content)

        # Delete old format file
        old_format.unlink()

        print(f"    ✅ Merged {len(old_facilities)} + {len(new_facilities)} = {len(all_facilities)} facilities")
        return new_format, len(all_facilities)

    elif old_exists:
        print(f"  Renaming COMM._{comm_number} -> COMMUNITY_{comm_number}")

        # Read old file
        content = read_markdown_file(old_format)

        # Update title and region references
        content = content.replace(f"# Healthcare Providers in COMM. {comm_number}",
                                 f"# Healthcare Providers in Community {comm_number}")
        content = content.replace(f"COMM. {comm_number}, Ghana",
                                 f"Community {comm_number}, Ghana")
        content = content.replace(f"**Region**: COMM. {comm_number}",
                                 f"**Region**: Community {comm_number}")

        # Write to new format
        write_markdown_file(new_format, content)

        # Delete old file
        old_format.unlink()

        facilities = extract_facilities(content)
        print(f"    ✅ Renamed with {len(facilities)} facilities")
        return new_format, len(facilities)

    elif new_exists:
        print(f"  Updating COMMUNITY_{comm_number} title format")

        # Read file
        content = read_markdown_file(new_format)

        # Ensure title is correctly formatted
        content = re.sub(r'# Healthcare Providers in COMMUNITY (\d+)',
                        r'# Healthcare Providers in Community \1', content)
        content = content.replace(f"COMMUNITY {comm_number}, Ghana",
                                 f"Community {comm_number}, Ghana")
        content = content.replace(f"**Region**: COMMUNITY {comm_number}",
                                 f"**Region**: Community {comm_number}")

        # Write back
        write_markdown_file(new_format, content)

        facilities = extract_facilities(content)
        print(f"    ✅ Updated title format with {len(facilities)} facilities")
        return new_format, len(facilities)

    return None, 0

def fix_comm_dot_files():
    """Fix COMM.6 style files"""
    # Find all COMM.X files (not COMM._X)
    comm_dot_files = list(BASE_DIR.glob("COMM.[0-9]*.md"))

    for old_file in comm_dot_files:
        # Extract number from COMM.6 -> 6
        match = re.match(r'COMM\.(\d+)\.md', old_file.name)
        if match:
            comm_number = match.group(1)
            new_file = BASE_DIR / f"COMMUNITY_{comm_number}.md"

            if new_file.exists():
                print(f"  Merging COMM.{comm_number} into existing COMMUNITY_{comm_number}")

                # Read both files
                old_content = read_markdown_file(old_file)
                new_content = read_markdown_file(new_file)

                # Extract facilities
                old_facilities = extract_facilities(old_content)
                new_facilities = extract_facilities(new_content)

                # Combine
                all_facilities = new_facilities + old_facilities

                # Create new content
                header = f"""# Healthcare Providers in Community {comm_number}

This document lists all Premier Health Insurance network providers in Community {comm_number}, Ghana.

"""
                combined_content = header + "\n---\n\n".join(all_facilities) + "\n"
                combined_content = combined_content.replace(f"**Region**: COMM. {comm_number}", f"**Region**: Community {comm_number}")
                combined_content = combined_content.replace(f"**Region**: COMM {comm_number}", f"**Region**: Community {comm_number}")

                write_markdown_file(new_file, combined_content)
                old_file.unlink()

                print(f"    ✅ Merged {len(old_facilities)} + {len(new_facilities)} = {len(all_facilities)} facilities")
            else:
                print(f"  Renaming COMM.{comm_number} -> COMMUNITY_{comm_number}")

                content = read_markdown_file(old_file)
                content = content.replace(f"# Healthcare Providers in COMM. {comm_number}",
                                         f"# Healthcare Providers in Community {comm_number}")
                content = content.replace(f"# Healthcare Providers in COMM {comm_number}",
                                         f"# Healthcare Providers in Community {comm_number}")
                content = content.replace(f"**Region**: COMM. {comm_number}",
                                         f"**Region**: Community {comm_number}")
                content = content.replace(f"**Region**: COMM {comm_number}",
                                         f"**Region**: Community {comm_number}")

                write_markdown_file(new_file, content)
                old_file.unlink()

                facilities = extract_facilities(content)
                print(f"    ✅ Renamed with {len(facilities)} facilities")

def main():
    """Main execution function"""
    print("=" * 70)
    print("FIXING COMMUNITY FILE NAMES AND MERGING DUPLICATES")
    print("=" * 70)
    print()

    os.chdir(BASE_DIR)

    # Find all community numbers
    all_files = list(BASE_DIR.glob("COMM*.md")) + list(BASE_DIR.glob("COMMUNITY*.md"))
    community_numbers = set()

    for file in all_files:
        num = extract_community_number(file.name)
        if num:
            community_numbers.add(num)

    print(f"Found community numbers: {sorted(community_numbers, key=int)}")
    print()

    # Fix COMM.X files first
    print("Step 1: Fix COMM.X files")
    print("-" * 70)
    fix_comm_dot_files()
    print()

    # Merge/rename all community files
    print("Step 2: Merge/rename COMM._X files")
    print("-" * 70)
    total_facilities = 0
    processed_files = []

    for comm_number in sorted(community_numbers, key=int):
        file_path, count = merge_community_files(comm_number)
        if file_path:
            total_facilities += count
            processed_files.append((comm_number, count))

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Communities processed: {len(processed_files)}")
    print(f"Total facilities: {total_facilities}")
    print()
    print("Community breakdown:")
    for comm_num, count in processed_files:
        print(f"  Community {comm_num}: {count} facilities")
    print()
    print("✅ All community files fixed and ready for RAG ingestion")
    print()
    print("Next steps:")
    print("1. Run reingest_processed_data.py to update RAG database")
    print("2. Update ghana_cities_stt_mapping.py with voice recognition for communities")

if __name__ == "__main__":
    main()
