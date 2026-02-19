#!/usr/bin/env python3
"""
Update CityNormalizer Mappings for Separated Cities

This script updates ghana_cities_stt_mapping.py to remove compound city names
and add STT variations for newly separated individual cities.

Changes:
- Remove: SANTASIPATASE, TAFOBREMANG, SOMANYAODUMASE KROBO, BEGOROOSIEM, ABUAKWATANOSO, ASSINSWEDRU
- Add/Ensure: SANTASI, PATASI, TAFO, BREMANG, SOMANYA, ODUMASE, BEGORO, OSIEM, ABUAKWA, ASSIN, SWEDRU
- Update regional groupings

Usage:
    python update_city_normalizer_mappings.py
"""

import os
import re
from pathlib import Path


def update_mapping_file():
    """Update the ghana_cities_stt_mapping.py file."""

    mapping_file = Path("/opt/kasaai/apps/automations/premier-health/ghana_cities_stt_mapping.py")

    print("=" * 80)
    print("Update CityNormalizer Mappings")
    print("=" * 80)
    print()

    # Read current file
    print("📖 Reading current mapping file...")
    with open(mapping_file, 'r') as f:
        content = f.read()

    print(f"   File size: {len(content)} characters")
    print()

    # Remove compound city mappings
    print("🗑️  Removing compound city mappings...")

    compound_patterns = [
        r"    'SANTASIPATASE':[^\n]+\n",
        r"    'TAFOBREMANG':[^\n]+\n",
        r"    'SOMANYAODUMASE KROBO':[^\n]+\n",
        r"    'BEGOROOSIEM':[^\n]+\n",
        r"    'ABUAKWATANOSO':[^\n]+\n",
        r"    'ASSINSWEDRU':[^\n]+\n",
    ]

    removed_count = 0
    for pattern in compound_patterns:
        matches = re.findall(pattern, content)
        if matches:
            for match in matches:
                city_name = match.split("'")[1]
                print(f"   ✓ Removed: {city_name}")
                removed_count += 1
            content = re.sub(pattern, '', content)

    print(f"   Total removed: {removed_count}")
    print()

    # Add PATASI mapping (if not exists)
    print("📝 Adding/Verifying individual city mappings...")

    if "'PATASI':" not in content:
        print("   + Adding PATASI mapping")
        # Add after PATASE line
        patase_line = "    'PATASE': ['pa ta say', 'pata say', 'pa tase', 'patasay'],"
        new_patasi_line = patase_line + "\n    'PATASI': ['pa ta si', 'patasi', 'pata si', 'pah tasi'],"
        content = content.replace(patase_line, new_patasi_line)
    else:
        print("   ✓ PATASI already exists")

    # Verify other individual cities
    individual_cities_to_check = [
        'SANTASI', 'TAFO', 'BREMANG', 'SOMANYA', 'ODUMASE',
        'BEGORO', 'OSIEM', 'ABUAKWA', 'ASSIN', 'SWEDRU'
    ]

    for city in individual_cities_to_check:
        if f"'{city}':" in content:
            print(f"   ✓ {city} exists")
        else:
            print(f"   ⚠️  {city} not found (may need manual addition)")

    print()

    # Update regional groupings
    print("🗺️  Updating regional groupings...")

    # Find ASHANTI regional grouping and remove compounds
    ashanti_pattern = r"('ASHANTI':\s*\[)(.*?)(\n    \],)"
    ashanti_match = re.search(ashanti_pattern, content, re.DOTALL)

    if ashanti_match:
        ashanti_cities = ashanti_match.group(2)

        # Remove compound names
        ashanti_cities = re.sub(r",?\s*'TAFOBREMANG'", '', ashanti_cities)
        ashanti_cities = re.sub(r",?\s*'ABUAKWATANOSO'", '', ashanti_cities)
        ashanti_cities = re.sub(r",?\s*'SANTASIPATASE'", '', ashanti_cities)

        # Change PATASE to PATASI
        ashanti_cities = ashanti_cities.replace("'PATASE'", "'PATASI'")

        # Reconstruct ASHANTI section
        new_ashanti = ashanti_match.group(1) + ashanti_cities + ashanti_match.group(3)
        content = content.replace(ashanti_match.group(0), new_ashanti)

        print("   ✓ Updated ASHANTI region")

    # Update EASTERN regional grouping
    eastern_pattern = r"('EASTERN':\s*\[)(.*?)(\n    \],)"
    eastern_match = re.search(eastern_pattern, content, re.DOTALL)

    if eastern_match:
        eastern_cities = eastern_match.group(2)

        # Remove compound name
        eastern_cities = re.sub(r",?\s*'BEGOROOSIEM'", '', eastern_cities)
        eastern_cities = re.sub(r",?\s*'SOMANYAODUMASE KROBO'", '', eastern_cities)

        # Reconstruct EASTERN section
        new_eastern = eastern_match.group(1) + eastern_cities + eastern_match.group(3)
        content = content.replace(eastern_match.group(0), new_eastern)

        print("   ✓ Updated EASTERN region")

    # Update CENTRAL regional grouping
    central_pattern = r"('CENTRAL':\s*\[)(.*?)(\n    \],)"
    central_match = re.search(central_pattern, content, re.DOTALL)

    if central_match:
        central_cities = central_match.group(2)

        # Remove compound name
        central_cities = re.sub(r",?\s*'ASSINSWEDRU'", '', central_cities)

        # Reconstruct CENTRAL section
        new_central = central_match.group(1) + central_cities + central_match.group(3)
        content = content.replace(central_match.group(0), new_central)

        print("   ✓ Updated CENTRAL region")

    print()

    # Clean up double commas and extra whitespace
    print("🧹 Cleaning up formatting...")
    content = re.sub(r',\s*,', ',', content)  # Double commas
    content = re.sub(r',\s*\n\s*\]', '\n    ]', content)  # Trailing commas before closing bracket
    print("   ✓ Formatting cleaned")
    print()

    # Write updated content
    print("💾 Writing updated mapping file...")
    with open(mapping_file, 'w') as f:
        f.write(content)
    print(f"   ✓ Saved to: {mapping_file}")
    print()

    # Generate summary
    print("=" * 80)
    print("✅ UPDATE COMPLETE!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  - Compound names removed: {removed_count}")
    print(f"  - Individual cities verified: {len(individual_cities_to_check)}")
    print("  - Regional groupings updated: 3 (ASHANTI, EASTERN, CENTRAL)")
    print()
    print("Key separations:")
    print("  • SANTASI ≠ PATASI (removed: SANTASIPATASE)")
    print("  • TAFO ≠ BREMANG (removed: TAFOBREMANG)")
    print("  • SOMANYA ≠ ODUMASE (removed: SOMANYAODUMASE KROBO)")
    print("  • BEGORO ≠ OSIEM (removed: BEGOROOSIEM)")
    print("  • ABUAKWA ≠ TANOSO (removed: ABUAKWATANOSO)")
    print("  • ASSIN ≠ SWEDRU (removed: ASSINSWEDRU)")
    print()
    print("Next steps:")
    print("  1. Test CityNormalizer with new mappings")
    print("  2. Verify STT variations work correctly")
    print("  3. Test real voice queries")
    print("=" * 80)


if __name__ == "__main__":
    update_mapping_file()
