"""
Extract and SPLIT location names from Premier Health provider CSV for better recognition.

This script:
1. Reads the premier_health_master_provider_list.csv
2. Extracts location names from the Region column
3. SPLITS multi-location groupings (e.g., "Dome Haatso Ashongman" → Dome, Haatso, Ashongman)
4. Keeps both individual AND grouped names for comprehensive coverage
5. Separates single-word keywords from multi-word keyterms
"""

import pandas as pd
import re
from typing import List, Tuple, Set

# File path
CSV_PATH = "/opt/kasaai/apps/automations/premier-health/data/premier_health_master_provider_list.csv"

# Words to exclude (these are not location names)
EXCLUDE_WORDS = {
    'GP', 'PHY', 'SRY', 'OBS', 'GYN', 'PED', 'PAED', 'DENTAL', 'PHARMACY',
    'OPTICAL', 'LABORATORY', 'ENT', 'DEM', 'DIET', 'HOSPITAL', 'CENTRE',
    'CENTER', 'BANK', 'CHURCH', 'JUNCTION', 'HIGH', 'SCHOOL', 'FILLING',
    'STATION', 'BEHIND', 'COMM', 'ROAD', 'STREET', 'HOTEL', 'CLINIC',
    'SERVICES', 'HEALTH', 'MEDICAL', 'COMMUNITY', 'GATE', 'OPPOSITE',
    'NEAR', 'AFTER', 'BEFORE', 'AREA', 'ESTATE', 'OTHERS'
}


def is_valid_location(word: str) -> bool:
    """
    Check if a word is a valid location name.

    Args:
        word: Word to check

    Returns:
        True if valid location, False otherwise
    """
    if len(word) < 2:
        return False

    if word.upper() in EXCLUDE_WORDS:
        return False

    # Skip numbers or mostly numbers
    if re.match(r'^\d+$', word):
        return False

    # Must have at least 2 letters
    if len(re.findall(r'[A-Za-z]', word)) < 2:
        return False

    return True


def split_location_group(location_string: str) -> Tuple[Set[str], str]:
    """
    Split a grouped location string into individual locations.

    Args:
        location_string: String like "Dome  Haatso  Ashongman  Kwabenya"

    Returns:
        Tuple of (set of individual locations, original string with hyphens removed)
    """
    # Clean the string
    location_string = location_string.strip()
    location_string = re.sub(r'["\']$', '', location_string)

    # Replace hyphens with spaces (Deepgram doesn't accept hyphens in keywords)
    # "Korle-Bu" → "Korle Bu", "Mamfe-" → "Mamfe"
    location_string = location_string.replace('-', ' ')
    location_string = ' '.join(location_string.split())  # Clean up extra spaces

    # Split by multiple spaces (common separator in the CSV)
    parts = re.split(r'\s{2,}', location_string)

    individual_locations = set()

    for part in parts:
        part = part.strip()

        # Further split by single spaces to get individual words
        words = part.split()

        for word in words:
            word_clean = word.strip()
            if is_valid_location(word_clean):
                individual_locations.add(word_clean)

        # Also keep multi-word parts like "East Legon" as a unit
        if len(words) > 1 and all(is_valid_location(w) for w in words):
            multi_word = ' '.join(words)
            if is_valid_location(words[0]):  # At least first word is valid
                individual_locations.add(multi_word)

    return individual_locations, location_string


def extract_all_locations(csv_path: str) -> Tuple[Set[str], Set[str]]:
    """
    Extract all location names, splitting grouped locations.

    Args:
        csv_path: Path to CSV file

    Returns:
        Tuple of (individual_locations, original_grouped_strings)
    """
    try:
        df = pd.read_csv(csv_path)

        all_individual_locations = set()
        all_grouped_strings = set()

        # Get unique region values
        regions = df.iloc[:, 0].dropna().unique()

        for region in regions:
            region_str = str(region).strip()

            # Skip if it looks like bad data
            if not region_str or re.match(r'^[\d\s\-/]+$', region_str):
                continue

            # Split the region into individual locations
            individual_locs, original = split_location_group(region_str)

            all_individual_locations.update(individual_locs)

            # Keep the original grouped string if it's valid
            if is_valid_location(original.split()[0] if original else ""):
                all_grouped_strings.add(original)

        return all_individual_locations, all_grouped_strings

    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return set(), set()


def separate_keywords_keyterms(locations: Set[str]) -> Tuple[List[str], List[str]]:
    """
    Separate locations into single-word keywords and multi-word keyterms.

    Args:
        locations: Set of location names

    Returns:
        Tuple of (sorted keywords list, sorted keyterms list)
    """
    keywords = []
    keyterms = []

    for location in locations:
        location_clean = ' '.join(location.split())
        word_count = len(location_clean.split())

        if word_count == 1:
            keywords.append(location_clean)
        else:
            keyterms.append(location_clean)

    return sorted(keywords), sorted(keyterms)


def add_medical_specialties(keyterms: List[str]) -> List[str]:
    """Add medical specialty terms."""
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

    for term in medical_specialties:
        if term not in keyterms:
            keyterms.append(term)

    return sorted(keyterms)


def main():
    """Main function."""
    print("=" * 80)
    print("Premier Health - IMPROVED Location Extractor (with splitting)")
    print("=" * 80)

    print(f"\n📂 Reading CSV: {CSV_PATH}")
    individual_locs, grouped_locs = extract_all_locations(CSV_PATH)

    print(f"\n✅ Extracted locations:")
    print(f"   Individual location names: {len(individual_locs)}")
    print(f"   Original grouped strings: {len(grouped_locs)}")

    # Combine individual and grouped for comprehensive coverage
    all_locations = individual_locs.union(grouped_locs)
    print(f"   Total unique terms: {len(all_locations)}")

    # Separate into keywords and keyterms
    keywords, keyterms = separate_keywords_keyterms(all_locations)
    print(f"\n🔍 Categorized:")
    print(f"   Single-word keywords: {len(keywords)}")
    print(f"   Multi-word keyterms (before medical): {len(keyterms)}")

    # Add medical specialties
    keyterms = add_medical_specialties(keyterms)
    print(f"   Multi-word keyterms (with medical): {len(keyterms)}")

    # Show examples
    print("\n" + "=" * 80)
    print("EXAMPLE: How 'Dome Haatso Ashongman Kwabenya' is now handled")
    print("=" * 80)
    example_splits = {
        "Dome Haatso Ashongman Kwabenya": ["Dome", "Haatso", "Ashongman", "Kwabenya"],
        "Madina Adenta Dodowa": ["Madina", "Adenta", "Dodowa"],
        "East Legon Adjringanor": ["East Legon", "Adjringanor"]
    }

    for grouped, split in example_splits.items():
        if grouped in all_locations:
            print(f"\n'{grouped}' →")
            for loc in split:
                if loc in keywords:
                    print(f"  ✓ {loc} (keyword)")
                elif loc in keyterms:
                    print(f"  ✓ {loc} (keyterm)")

    # Display results
    print("\n" + "=" * 80)
    print("KEYWORDS (Single Words) - First 30")
    print("=" * 80)
    for i, kw in enumerate(keywords[:30], 1):
        print(f"{i:3d}. {kw}")
    if len(keywords) > 30:
        print(f"... and {len(keywords) - 30} more")

    print("\n" + "=" * 80)
    print("KEYTERMS (Multi-Word) - First 30")
    print("=" * 80)
    for i, kt in enumerate(keyterms[:30], 1):
        print(f"{i:3d}. {kt}")
    if len(keyterms) > 30:
        print(f"... and {len(keyterms) - 30} more")

    # Save to files
    with open('/opt/kasaai/apps/automations/examples/deepgram_keywords_split.txt', 'w') as f:
        f.write('\n'.join(keywords))

    with open('/opt/kasaai/apps/automations/examples/deepgram_keyterms_split.txt', 'w') as f:
        f.write('\n'.join(keyterms))

    # Generate Python lists for easy copy-paste
    with open('/opt/kasaai/apps/automations/examples/deepgram_python_lists.py', 'w') as f:
        f.write('# Generated location lists for VAPI Deepgram configuration\n\n')
        f.write('KEYWORDS = [\n')
        for kw in keywords:
            f.write(f'    "{kw}",\n')
        f.write(']\n\n')
        f.write('KEYTERMS = [\n')
        for kt in keyterms:
            f.write(f'    "{kt}",\n')
        f.write(']\n')

    print("\n✅ Files saved:")
    print("   - deepgram_keywords_split.txt")
    print("   - deepgram_keyterms_split.txt")
    print("   - deepgram_python_lists.py")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total location terms: {len(all_locations)}")
    print(f"Single-word keywords: {len(keywords)}")
    print(f"Multi-word keyterms: {len(keyterms)}")
    print(f"Total for Deepgram: {len(keywords) + len(keyterms)}")
    print("\n💡 KEY IMPROVEMENT:")
    print("   Now recognizes BOTH individual towns (Haatso, Dome, Madina)")
    print("   AND grouped regions (Dome Haatso Ashongman Kwabenya)")
    print("   Users can say any specific town name and be understood!")
    print("=" * 80)


if __name__ == "__main__":
    main()
