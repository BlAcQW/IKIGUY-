"""
Premier Health Data Reprocessing - Separate Grouped Cities

This script reprocesses the Premier Health facility data to properly separate
facilities that are grouped under compound region names like "SANTASI/PATASE"
into individual city-based documents.

Issue: CSV groups multiple towns under one header (e.g., SANTASI/PATASE)
       but facilities are actually in specific towns within that group.

Solution: Parse facility addresses to determine actual location and create
         separate documents for each town.

Usage:
    python reprocess_locations.py
"""

import csv
import re
import json
from pathlib import Path
from typing import Dict, List, Set
from datetime import datetime


# Grouped location patterns to split
GROUPED_LOCATIONS = {
    "ABUAKWA/TANOSO": ["ABUAKWA", "TANOSO"],
    "ACCRA CENTRAL / TUDU / MAKOLA": ["ACCRA CENTRAL", "TUDU", "MAKOLA"],
    "AHODWO / AHINSAN": ["AHODWO", "AHINSAN"],
    "AIRPORT RESIDENTIAL AREA / 37 AREA": ["AIRPORT RESIDENTIAL AREA", "37 AREA"],
    "AMANSAMAN / POKUASE": ["AMANSAMAN", "POKUASE"],
    "ASHAIMAN / COMMUNITY 26": ["ASHAIMAN", "COMMUNITY 26"],
    "ASIAKWA / OSINO / ANYINAM / ENYIRESI / KIBI": ["ASIAKWA", "OSINO", "ANYINAM", "ENYIRESI", "KIBI"],
    "ASIKUMA /AJUMAKO": ["ASIKUMA", "AJUMAKO"],
    "ASSIN/SWEDRU": ["ASSIN", "SWEDRU"],
    "BEGORO/OSIEM": ["BEGORO", "OSIEM"],
    "BOMSO / KNUST / EJISU": ["BOMSO", "KNUST", "EJISU"],
    "CIRCLE / KANESHIE / NORTH KANESHIE / INDUSTRIAL AREA": ["CIRCLE", "KANESHIE", "NORTH KANESHIE", "INDUSTRIAL AREA"],
    "COMM. 22 / MICHEL CAMP / AFIENYA ROAD": ["COMMUNITY 22", "MICHEL CAMP", "AFIENYA"],
    "DANSOMAN / MAMPROBI / KORLE-BU": ["DANSOMAN", "MAMPROBI", "KORLE BU"],
    "DOME / HAATSO / ASHONGMAN / KWABENYA": ["DOME", "HAATSO", "ASHONGMAN", "KWABENYA"],
    "EAST LEGON / ADJRINGANOR": ["EAST LEGON", "ADJRINGANOR"],
    "KOKOMLEMLE / MAAMOBI / NIMA": ["KOKOMLEMLE", "MAAMOBI", "NIMA"],
    "KONONGO / AGOGO": ["KONONGO", "AGOGO"],
    "LABONE / LA / TSE ADDO / CANTONMENTS": ["LABONE", "LA", "TSE ADDO", "CANTONMENTS"],
    "LAPAZ / NYAMEKYE / DARKUMAN / ODORKOR": ["LAPAZ", "NYAMEKYE", "DARKUMAN", "ODORKOR"],
    "LATEBIOKOSHIE / MATAHEKO": ["LATEBIOKOSHIE", "MATAHEKO"],
    "MADINA / ADENTA / DODOWA": ["MADINA", "ADENTA", "DODOWA"],
    "MAMPONG / AGONA / WIAMOASE": ["MAMPONG", "AGONA", "WIAMOASE"],
    "OBUASI / DUNKWA": ["OBUASI", "DUNKWA"],
    "SAKUMONO ESTATE / LASHIBI / COMM. 18": ["SAKUMONO", "LASHIBI", "COMMUNITY 18"],
    "SANTASI/PATASE": ["SANTASI", "PATASI"],  # Note: PATASE → PATASI (correct spelling)
    "SOMANYA/ODUMASE KROBO": ["SOMANYA", "ODUMASE"],
    "SPINTEX ROAD / BAATSONA": ["SPINTEX", "BAATSONA"],
    "TAFO/BREMANG": ["TAFO", "BREMANG"],
    "TANTRA HILL / OFANKOR": ["TANTRA HILL", "OFANKOR"],
    "TEMA COMMUNITY 2 / 4": ["TEMA COMMUNITY 2", "TEMA COMMUNITY 4"],
    "TEMA COMMUNITY 4 / 5 / 6 / 9 / 10 / 12": ["TEMA COMMUNITY 4", "TEMA COMMUNITY 5", "TEMA COMMUNITY 6", "TEMA COMMUNITY 9", "TEMA COMMUNITY 10", "TEMA COMMUNITY 12"],
    "WEIJA / KASOA / GBAWE": ["WEIJA", "KASOA", "GBAWE"],
}


def extract_location_from_address(address: str) -> str:
    """
    Extract the likely town/area name from a facility address.

    Args:
        address: Full facility address

    Returns:
        Extracted location name (uppercase)
    """
    if not address:
        return "UNKNOWN"

    address_upper = address.upper()

    # Common patterns in addresses
    # Priority order: most specific first
    patterns = [
        # Specific location keywords
        r'\b(SANTASI|PATASI)\b',
        r'\b(MADINA|ADENTA|DODOWA)\b',
        r'\b(TAFO|BREMANG)\b',
        r'\b(BOMSO|KNUST|EJISU)\b',
        r'\b(ABUAKWA|TANOSO)\b',
        r'\b(SOMANYA|ODUMASE)\b',
        r'\b(BEGORO|OSIEM)\b',
        r'\b(KONONGO|AGOGO)\b',
        r'\b(OBUASI|DUNKWA)\b',
        r'\b(ASIAKWA|OSINO|ANYINAM|ENYIRESI|KIBI)\b',
        r'\b(ASIKUMA|AJUMAKO)\b',
        r'\b(AHODWO|AHINSAN)\b',
        r'\b(WEIJA|KASOA|GBAWE)\b',
        r'\b(DANSOMAN|MAMPROBI|KORLE\s*BU)\b',
        r'\b(DOME|HAATSO|ASHONGMAN|KWABENYA)\b',
        r'\b(EAST\s+LEGON|ADJRINGANOR)\b',
        r'\b(KOKOMLEMLE|MAAMOBI|NIMA)\b',
        r'\b(LABONE|LA|TSE\s+ADDO|CANTONMENTS)\b',
        r'\b(LAPAZ|NYAMEKYE|DARKUMAN|ODORKOR)\b',
        r'\b(LATEBIOKOSHIE|MATAHEKO)\b',
        r'\b(TANTRA\s+HILL|OFANKOR)\b',
        r'\b(SPINTEX|BAATSONA)\b',
        r'\b(SAKUMONO|LASHIBI)\b',
        r'\b(AMANSAMAN|POKUASE)\b',
        r'\b(ASHAIMAN)\b',
        r'\b(AIRPORT\s+RESIDENTIAL|37\s+AREA)\b',
        r'\b(ACCRA\s+CENTRAL|TUDU|MAKOLA)\b',
        r'\b(CIRCLE|KANESHIE)\b',
        r'\b(MAMPONG|AGONA|WIAMOASE)\b',
        r'\b(TEMA\s+COMMUNITY\s+\d+)\b',
        r'\b(COMMUNITY\s+\d+)\b',
        r'\b(COMM\.\s*\d+)\b',
    ]

    for pattern in patterns:
        match = re.search(pattern, address_upper)
        if match:
            location = match.group(1)
            # Normalize spacing
            location = re.sub(r'\s+', ' ', location).strip()
            return location

    # Fallback: take first significant word
    words = address_upper.split()
    if words:
        # Skip common prefixes
        skip_words = {'THE', 'A', 'AN', 'NEAR', 'BEHIND', 'OPPOSITE', 'NEXT', 'TO', 'AT', 'IN'}
        for word in words:
            if len(word) > 3 and word not in skip_words:
                return word

    return "UNKNOWN"


def normalize_specialty_codes(specialty_str: str) -> Dict[str, str]:
    """
    Parse and normalize specialty codes.

    Args:
        specialty_str: Specialty string (e.g., "GP/PHY/SRY/GYN/OBS/PED")

    Returns:
        Dictionary with codes and full names
    """
    specialty_names = {
        "GP": "General Practice (GP)",
        "PHY": "Physiotherapy (PHY)",
        "SRY": "Surgery (SRY)",
        "GYN": "Gynecology (GYN)",
        "OBS": "Obstetrics (OBS)",
        "PED": "Pediatrics (PED)",
        "ENT": "Ear Nose Throat (ENT)",
        "DERM": "Dermatology (DERM)",
        "CARD": "Cardiology (CARD)",
        "OPH": "Ophthalmology (OPH)",
        "ORT": "Orthopedics (ORT)",
        "PHARMACY": "Pharmacy",
        "OPTICAL": "Optical Services",
        "DENTAL": "Dental Care",
        "LAB": "Laboratory Services",
        "IMAGING": "Medical Imaging",
        "PHYSIO": "Physiotherapy",
        "DIETETICS": "Dietetics",
    }

    codes = [c.strip() for c in specialty_str.split('/')]
    full_names = [specialty_names.get(code, code) for code in codes]

    return {
        "codes": specialty_str,
        "names": ", ".join(full_names)
    }


def process_csv_to_location_groups(csv_file: Path) -> Dict[str, List[Dict]]:
    """
    Process CSV and group facilities by actual location.

    Args:
        csv_file: Path to CSV file

    Returns:
        Dictionary mapping location names to lists of facilities
    """
    location_groups = {}
    current_region = None

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header

        for row in reader:
            if not row or len(row) < 7:
                continue

            # Check if this is a region header
            if row[0] == '' and row[1] == '' and row[2] == '' and row[3]:
                current_region = row[3].strip()
                continue

            # Skip if not a facility row
            if row[2] == '' or not row[3]:
                continue

            # Extract facility data
            facility_name = row[3].strip()
            specialty = row[4].strip() if len(row) > 4 else ""
            phone = row[5].strip() if len(row) > 5 else ""
            address = row[6].strip() if len(row) > 6 else ""

            if not facility_name:
                continue

            # Extract actual location from address
            actual_location = extract_location_from_address(address)

            # Parse specialties
            specialty_info = normalize_specialty_codes(specialty)

            # Create facility entry
            facility = {
                "name": facility_name,
                "specialty_codes": specialty_info["codes"],
                "specialties": specialty_info["names"],
                "phone": phone,
                "address": address,
                "original_region": current_region,
                "actual_location": actual_location
            }

            # Group by actual location
            if actual_location not in location_groups:
                location_groups[actual_location] = []
            location_groups[actual_location].append(facility)

    return location_groups


def generate_markdown_documents(location_groups: Dict[str, List[Dict]]) -> Dict[str, str]:
    """
    Generate markdown documents for each location.

    Args:
        location_groups: Dictionary mapping locations to facilities

    Returns:
        Dictionary mapping location names to markdown content
    """
    documents = {}

    for location, facilities in sorted(location_groups.items()):
        if location == "UNKNOWN":
            continue

        # Generate markdown
        lines = []
        lines.append(f"# Healthcare Providers in {location}")
        lines.append("")
        lines.append(f"This document lists all Premier Health Insurance network providers in {location}, Ghana.")
        lines.append("")

        for facility in facilities:
            lines.append(f"## {facility['name']}")
            lines.append(f"**Specialties**: {facility['specialties']}")
            lines.append(f"**Specialty Codes**: {facility['specialty_codes']}")
            if facility['phone']:
                lines.append(f"**Phone**: {facility['phone']}")
            lines.append(f"**Location**: {facility['address']}")
            lines.append(f"**Region**: {location}")
            lines.append("")
            lines.append("---")
            lines.append("")

        documents[location] = "\n".join(lines)

    return documents


def save_processed_data(location_groups: Dict[str, List[Dict]], output_dir: Path):
    """
    Save processed data to files.

    Args:
        location_groups: Processed location groups
        output_dir: Output directory
    """
    output_dir.mkdir(exist_ok=True)

    # Save JSON summary
    summary = {
        "processing_date": datetime.now().isoformat(),
        "total_locations": len(location_groups),
        "total_facilities": sum(len(facilities) for facilities in location_groups.values()),
        "locations": {
            location: len(facilities)
            for location, facilities in sorted(location_groups.items())
        }
    }

    with open(output_dir / "processing_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)

    # Save detailed JSON
    with open(output_dir / "facilities_by_location.json", 'w') as f:
        json.dump(location_groups, f, indent=2)

    # Generate markdown documents
    documents = generate_markdown_documents(location_groups)

    # Save markdown files
    docs_dir = output_dir / "markdown_documents"
    docs_dir.mkdir(exist_ok=True)

    for location, content in documents.items():
        filename = location.replace('/', '_').replace(' ', '_') + ".md"
        with open(docs_dir / filename, 'w') as f:
            f.write(content)

    return documents, summary


def extract_unique_locations(location_groups: Dict[str, List[Dict]]) -> Set[str]:
    """
    Extract unique location names for keyword/keyterm updates.

    Args:
        location_groups: Processed location groups

    Returns:
        Set of unique location names
    """
    locations = set()

    for location in location_groups.keys():
        if location == "UNKNOWN":
            continue

        # Add the location itself
        locations.add(location)

        # For multi-word locations, also add individual significant words
        words = location.split()
        for word in words:
            if len(word) > 3 and word not in {'AREA', 'ROAD', 'HILL', 'ESTATE', 'CAMP'}:
                locations.add(word)

    return locations


def main():
    """Main processing function."""
    print("=" * 80)
    print("Premier Health Data Reprocessing - Separate Grouped Cities")
    print("=" * 80)
    print()

    # Paths
    base_dir = Path("/opt/kasaai/apps/automations/premier-health")
    csv_file = base_dir / "premier_health_full_list.csv"
    output_dir = base_dir / "processed_data"

    print(f"📂 Input: {csv_file}")
    print(f"📁 Output: {output_dir}")
    print()

    # Process CSV
    print("📊 Processing CSV data...")
    location_groups = process_csv_to_location_groups(csv_file)
    print(f"✅ Processed {len(location_groups)} unique locations")
    print()

    # Save processed data
    print("💾 Saving processed data...")
    documents, summary = save_processed_data(location_groups, output_dir)
    print(f"✅ Generated {len(documents)} markdown documents")
    print()

    # Extract unique locations
    print("🗺️  Extracting unique location names...")
    unique_locations = extract_unique_locations(location_groups)
    print(f"✅ Found {len(unique_locations)} unique location names")
    print()

    # Save location names for keyword updates
    with open(output_dir / "unique_locations.txt", 'w') as f:
        for location in sorted(unique_locations):
            f.write(f"{location}\n")

    # Print summary
    print("=" * 80)
    print("PROCESSING SUMMARY")
    print("=" * 80)
    print(f"Total Locations: {summary['total_locations']}")
    print(f"Total Facilities: {summary['total_facilities']}")
    print()
    print("Top 10 locations by facility count:")
    sorted_locs = sorted(summary['locations'].items(), key=lambda x: x[1], reverse=True)
    for location, count in sorted_locs[:10]:
        print(f"  {location}: {count} facilities")
    print()

    print("📍 Example: SANTASI vs PATASI separation:")
    if "SANTASI" in location_groups:
        print(f"   SANTASI: {len(location_groups['SANTASI'])} facilities")
    if "PATASI" in location_groups:
        print(f"   PATASI: {len(location_groups['PATASI'])} facilities")
    print()

    print("=" * 80)
    print("✅ Processing complete!")
    print()
    print("Next steps:")
    print("1. Review generated markdown documents")
    print("2. Re-ingest into RAG database")
    print("3. Update Deepgram keywords/keyterms")
    print("4. Update CityNormalizer mappings")
    print("=" * 80)


if __name__ == "__main__":
    main()
