"""
Extract location names from Premier Health provider CSV and update VAPI Deepgram configuration.

This script:
1. Reads the premier_health_master_provider_list.csv
2. Extracts unique location/region names
3. Cleans and validates the names
4. Separates single-word keywords from multi-word keyterms
5. Generates configuration for VAPI Deepgram transcriber
"""

import pandas as pd
import re
from typing import List, Tuple

# File path
CSV_PATH = "/opt/kasaai/apps/automations/premier-health/data/premier_health_master_provider_list.csv"

# Words to exclude (these are not location names)
EXCLUDE_WORDS = {
    'GP', 'PHY', 'SRY', 'OBS', 'GYN', 'PED', 'PAED', 'DENTAL', 'PHARMACY',
    'OPTICAL', 'LABORATORY', 'ENT', 'DEM', 'DIET', 'HOSPITAL', 'CENTRE',
    'CENTER', 'BANK', 'CHURCH', 'JUNCTION', 'HIGH', 'SCHOOL', 'FILLING',
    'STATION', 'BEHIND', 'COMM', 'ROAD', 'STREET', 'HOTEL', 'CLINIC',
    'SERVICES', 'HEALTH', 'MEDICAL', 'COMMUNITY', 'GATE', 'OPPOSITE',
    'NEAR', 'AFTER', 'BEFORE'
}


def clean_location_name(location: str) -> str:
    """
    Clean a location name.

    Args:
        location: Raw location string

    Returns:
        Cleaned location string or empty if invalid
    """
    # Remove leading/trailing whitespace
    location = location.strip()

    # Remove trailing quotes and special characters
    location = re.sub(r'["\']$', '', location)
    location = re.sub(r'\([^)]*\)$', '', location).strip()

    # Skip if empty or too short
    if len(location) < 2:
        return ""

    # Skip if it looks like a phone number or other data
    if re.match(r'^[\d\s\-/]+$', location):
        return ""

    # Skip if it's mostly special characters
    if len(re.findall(r'[A-Za-z]', location)) < 2:
        return ""

    # Skip if first word is in exclude list
    first_word = location.split()[0].upper()
    if first_word in EXCLUDE_WORDS:
        return ""

    return location


def extract_locations_from_csv(csv_path: str) -> List[str]:
    """
    Extract unique location names from CSV.

    Args:
        csv_path: Path to the CSV file

    Returns:
        List of unique, cleaned location names
    """
    try:
        # Read CSV
        df = pd.read_csv(csv_path)

        # Get the first column (Region)
        locations = df.iloc[:, 0].dropna().unique()

        # Clean each location
        cleaned_locations = []
        for loc in locations:
            cleaned = clean_location_name(str(loc))
            if cleaned:
                cleaned_locations.append(cleaned)

        # Sort and return unique
        return sorted(list(set(cleaned_locations)))

    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return []


def separate_keywords_keyterms(locations: List[str]) -> Tuple[List[str], List[str]]:
    """
    Separate locations into single-word keywords and multi-word keyterms.

    Args:
        locations: List of location names

    Returns:
        Tuple of (keywords, keyterms)
    """
    keywords = []
    keyterms = []

    for location in locations:
        # Remove extra spaces
        location_clean = ' '.join(location.split())

        # Count words
        word_count = len(location_clean.split())

        if word_count == 1:
            keywords.append(location_clean)
        else:
            keyterms.append(location_clean)

    return keywords, keyterms


def add_medical_specialties(keyterms: List[str]) -> List[str]:
    """
    Add medical specialty terms to keyterms.

    Args:
        keyterms: Existing keyterm list

    Returns:
        Updated keyterm list with medical terms
    """
    medical_specialties = [
        "general practitioner",
        "gynecologist",
        "pediatrician",
        "cardiologist",
        "dermatologist",
        "ophthalmologist",
        "orthopedic surgeon",
        "emergency medicine",
        "family medicine",
        "internal medicine"
    ]

    # Add medical terms that aren't already in the list
    for term in medical_specialties:
        if term not in keyterms:
            keyterms.append(term)

    return keyterms


def main():
    """Main function to extract locations and generate configuration."""
    print("=" * 80)
    print("Premier Health - Deepgram Location Extractor")
    print("=" * 80)

    # Extract locations
    print(f"\n📂 Reading CSV: {CSV_PATH}")
    locations = extract_locations_from_csv(CSV_PATH)
    print(f"✅ Found {len(locations)} unique locations")

    # Separate into keywords and keyterms
    print(f"\n🔍 Separating keywords and keyterms...")
    keywords, keyterms = separate_keywords_keyterms(locations)
    print(f"✅ Single-word keywords: {len(keywords)}")
    print(f"✅ Multi-word keyterms: {len(keyterms)}")

    # Add medical specialties
    keyterms = add_medical_specialties(keyterms)
    print(f"✅ Total keyterms (with medical): {len(keyterms)}")

    # Display results
    print("\n" + "=" * 80)
    print("KEYWORDS (Single Words)")
    print("=" * 80)
    for i, kw in enumerate(keywords[:20], 1):
        print(f"{i:3d}. {kw}")
    if len(keywords) > 20:
        print(f"... and {len(keywords) - 20} more")

    print("\n" + "=" * 80)
    print("KEYTERMS (Multi-Word)")
    print("=" * 80)
    for i, kt in enumerate(keyterms[:20], 1):
        print(f"{i:3d}. {kt}")
    if len(keyterms) > 20:
        print(f"... and {len(keyterms) - 20} more")

    # Generate JSON configuration
    print("\n" + "=" * 80)
    print("JSON CONFIGURATION FOR DEEPGRAM")
    print("=" * 80)

    print('\n"transcriber": {')
    print('  "provider": "deepgram",')
    print('  "model": "nova-3",')
    print('  "language": "en-GB",')
    print('  "keywords": [')
    for i, kw in enumerate(keywords):
        comma = "," if i < len(keywords) - 1 else ""
        print(f'    "{kw}"{comma}')
    print('  ],')
    print('  "keyterm": [')
    for i, kt in enumerate(keyterms):
        comma = "," if i < len(keyterms) - 1 else ""
        print(f'    "{kt}"{comma}')
    print('  ],')
    print('  "smartFormat": true,')
    print('  "endpointing": 300,')
    print('  "numerals": true')
    print('}')

    # Save to files for reference
    with open('/opt/kasaai/apps/automations/examples/deepgram_keywords.txt', 'w') as f:
        f.write('\n'.join(keywords))

    with open('/opt/kasaai/apps/automations/examples/deepgram_keyterms.txt', 'w') as f:
        f.write('\n'.join(keyterms))

    print("\n✅ Saved keywords to: deepgram_keywords.txt")
    print("✅ Saved keyterms to: deepgram_keyterms.txt")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total locations extracted: {len(locations)}")
    print(f"Single-word keywords: {len(keywords)}")
    print(f"Multi-word keyterms: {len(keyterms)}")
    print(f"Total terms for Deepgram: {len(keywords) + len(keyterms)}")
    print("\n💡 Use these in your VAPI assistant configuration to improve")
    print("   speech recognition for all Ghana locations in your database!")
    print("=" * 80)


if __name__ == "__main__":
    main()
