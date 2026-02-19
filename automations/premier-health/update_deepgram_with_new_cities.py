#!/usr/bin/env python3
"""
Update Deepgram Keywords with New Individual Cities

This script updates the Deepgram configuration to replace compound city names
with individual city names after the data reprocessing.

Changes:
- Remove old compound names (e.g., "Santasipatase")
- Add new individual city names (e.g., "Santasi", "Patasi")
- Clean up noise words from unique_locations.txt
- Generate updated keywords and keyterms lists

Usage:
    python update_deepgram_with_new_cities.py
"""

import sys
from pathlib import Path
from typing import Set, List

# Current keywords (from deepgram_python_lists.py)
CURRENT_KEYWORDS = [
    "Abelenkpe", "Abirem", "Abrepo", "Abuakwatanoso", "Accra", "Achimota", "Adabraka",
    "Addo", "Adenta", "Adjringanor", "Adum", "Afienya", "Agogo", "Agona", "Ahinsan",
    "Ahodwo", "Airport", "Ajumako", "Akosombo", "Akropong", "Akuapem", "Akwatia",
    "Amansaman", "Anhwiaso", "Anyinam", "Asafo", "Asamankese", "Asankragwa", "Asawinso",
    "Ashaiman", "Ashongman", "Asiakwa", "Asikuma", "Asokwa", "Assinswedru", "Asylum",
    "Baatsona", "Bantama", "Bawku", "Bechem", "Begoroosiem", "Bekwai", "Berekum",
    "Bibiani", "Bodi", "Bogoso", "Bolgatanga", "Bomso", "Bu", "Camp", "Cantonments",
    "Cape", "Central", "Circle", "Coast", "Dadieso", "Dansoman", "Darkuman", "Dodowa",
    "Dome", "Dormaa", "Down", "Drobo", "Duayaw", "Dunkwa", "Dzorwulu", "East", "Ejisu",
    "Elmina", "Enchi", "Environs", "Enyiresi", "Essam", "Gbawe", "Goaso", "Haatso",
    "Hill", "Ho", "Hohoe", "Hwidiem", "Inchaban", "Industrial", "Juaboso", "Kade",
    "Kaneshie", "Kasoa", "Kenyase", "Kibi", "Kintampo", "Knust", "Koforidua",
    "Kokomlemle", "Konongo", "Korle", "Krobo", "Kwabenya", "La", "Labone", "Lapaz",
    "Lashibi", "Latebiokoshie", "Lawra", "Legon", "Maamobi", "Madina", "Makola",
    "Mamfe", "Mampong", "Mamponteng", "Mamprobi", "Mankessim", "Mataheko", "Michel",
    "Navrongo", "New", "Nima", "Nkawkaw", "Nkoranza", "Nkwanta", "North", "Nsawam",
    "Nungua", "Nyamekye", "Obuasi", "Oda", "Odorkor", "Ofankor", "Osino", "Osu",
    "Pokuase", "Residential", "Ridge", "Sakumono", "Sampa", "Samreboi", "Santasipatase",
    "Sefwi", "Sekondi", "Somanyaodumase", "Spintex", "Suaman", "Suame", "Suhum",
    "Sunyani", "Tafo", "Tafobremang", "Takoradi", "Tamale", "Tantra", "Tarkwa",
    "Techiman", "Tema", "Tesano", "Teshie", "Tse", "Tudu", "Wa", "Wassa", "Weija",
    "Wenchi", "Wiamoase", "Wiawso", "Winneba",
]

# Compound names to remove
COMPOUND_NAMES_TO_REMOVE = [
    "Abuakwatanoso",
    "Assinswedru",
    "Begoroosiem",
    "Santasipatase",
    "Somanyaodumase",
    "Tafobremang",
]

# Noise words to filter out from unique_locations.txt
NOISE_WORDS = {
    "OPP.", "OPP", "ADJACENT", "ALONG", "AFTER", "OPPOSITE", "NEAR", "BEHIND",
    "NEXT", "AROUND", "CLOSE", "METRES", "MILE", "STOP", "JUNCTION", "HOUSE",
    "ROAD", "STREET", "AVENUE", "LANE", "DRIVE", "PLOT", "H/NO", "H/NO.",
    "HSE/NO", "FLOOR,", "SHOP", "SITE", "ESTATES", "LOCATION", "DISTRICT",
    "REGIONAL", "MUNICIPAL", "COUNCIL", "HOSPITAL", "HOSPITAL,", "CLINIC",
    "PHARMACY", "OFFICE,", "BUILDING", "BLOCK", "TOWER", "COMPLEX", "CENTRE",
    "CENTER", "MALL", "SHOPPING", "EMPORIUM,", "MARKET", "STORE", "STATION",
    "POST", "POLICE", "FIRE", "CHURCH", "CHAPEL", "CATHOLIC", "PRESBY",
    "PENTECOST", "MOSQUE", "SCHOOL", "COLLEGE", "UNIVERSITY", "HOSPITAL",
    "CLINIC", "PHARMACY", "10TH", "18TH", "133,", "37-OPPOSITE", "6MRS/6BN,",
    "ADABRAKA,", "ADDOGONNO-NUNGUA", "ADIESENT", "ADJOATE", "ADJUCENT",
    "ANAGOKORDZI,", "ANWOMASO,KUMASI", "ASHIAMAN,", "AT/F41", "BETHLEHEM,",
    "BLUESTREET,", "BOLGA,", "BOLGA-SOE", "BUBUASHIE.", "C914/3", "CAIRO",
    "CEDI", "CHARLES", "CLAY", "COCOA", "COMM", "COMM.", "COMM.6", "COUNTRY",
    "DA-ROCHA,", "DARKWA", "DORMAA,DROBO,BEREKUM,KINTAMPO,DUAYAW", "E.P.",
    "EMINA", "EXCLUSIVE", "EXIT", "FIAPRE,", "FIDELITY", "FORMER", "G.P.R.T.U",
    "GENERAL", "GHANA", "GLOBAL", "GOLF", "GRAPHIC", "GREENLIGHT", "GUINNESS",
    "HABOUR", "HERITAGE", "HILA", "HO-DEME", "HYGIENCE", "ISD-FILM", "JACKSON",
    "JAMAN", "JAMASE", "JAMERA", "JISONAYILI", "JOHN", "JOSEPTH", "KANTON",
    "KEJETIA", "KENKEY", "KENTON", "KLAGON-", "KOFORIDUA-FEW", "KOJO",
    "KORDIABE,SHAI-OSUDOKU", "KORLE-", "KORLE-BU,", "KOTWI", "KPAKPA",
    "KPANVO-", "KRONUN", "LAKESIDE", "LARAMART", "LAWSEC", "LEBANON",
    "LEDZOKUKU", "LIBERATION", "LIBRATION", "LOKKO", "MAAME", "MANGO",
    "MEDLOVE", "MEDUMA", "MENSVIC", "MORTUARY", "MPREASO-", "NALURO", "NANA",
    "NARH", "NKAWKAW,", "NOBISCO", "NS-151-7998", "NSAWAM,", "NSAWAM-ADOAGYIRI",
    "NT-0150-1711", "NYANYO", "NYOHINI", "ODUMASI", "ODUOM", "OFFICIAL",
    "OHENE-GYAN", "OPEIKUMA", "OPP.ROYAL", "OPPT.SUNYANI", "OPPT.TAMALE",
    "OSU,", "OXFORD", "P29/13", "PADMORE", "PALOMA,", "PARAKUO", "PEPRAN",
    "POUHUN", "PRESTIGE", "PRIMARY/JHS", "QUEENS", "RAILS", "ROBERT", "ROMAN",
    "RUSSIAN", "SABONKUDI", "SAHID", "SAMPA,BEREKUM,DROBO,SUNYANI,FIAPRE,ABESIM,WEN",
    "SAWAABA", "SAWMILL,", "SDD-", "SEBREPOR", "SECONDI", "SHAMA,", "SNITT",
    "SOMBO,", "SOUTH", "SRODAE-", "SSNIT", "STARTLETS", "STATE", "SUNNY",
    "SUNYANI,", "SUNYANI,BEREKUM", "TAKWA", "TAMALE-AROUND", "TAMALE-BOLGA",
    "TAMOHEC,ABOSO", "TAMSO-ESTATE", "TAKORADI-GLOOVY", "TECHNICAL", "THEATER",
    "TOPMAN", "TOTAL", "TRAFFIC", "TUBA", "UPSA", "WEST", "WESTLINE", "WOODIN",
    "WORKERS", "YAKASI", "YIYIWA", "ZENU", "ABAASE", "ABOTANSO", "ADEIBEBA",
    "ADIETEM-NORTH", "ADJAPOMAA", "ADJESENT", "ADJIRINGANOR", "AFARI", "AFARIWA",
    "AFRANCHO", "AHENEMA", "AHENSAN", "AMASAMAN", "AMEEN", "ANAJI", "ANAPUA",
    "ANHWIANKWATA", "APATRAPA", "APSONIC", "APUTUGYA", "ASANTEWAA", "ASENEMASO",
    "ASHALEY", "ASHFOAM", "ATASOMANSO", "ATEKYEM", "AVIATION", "AWOSHIE", "BADU",
    "BAKE", "BAMAHU", "BESEASE", "BETHEL", "BIMBILLA", "BINEY", "BOLGA", "BRAZZA",
    "BUBUASHIE", "BUOKROM", "CANTONMENT", "CAPE", "COMM. 1", "COMM. 2", "COMM. 21",
    "COMM. 22", "COMM. 25", "COMM. 3", "COMM. 4", "COMMUNITY", "COMMUNITY 1",
    "COMMUNITY 10", "COMMUNITY 11", "COMMUNITY 25", "COMMUNITY 4", "COMMUNITY 9",
    "DAKWADWOM", "DANYAME", "DAWHENYA", "DWENEASE", "DZORWULU", "EFIAKWANTA",
    "EWIM", "GBETSILE", "GLALAH", "HWIDIEM", "JEMA", "JUKWA", "KAKASUNANKA",
    "KANVILLI", "KATARIGA", "KENYASI", "KENYASI-NEWMONT", "KETAN", "KISSEMAN",
    "KOKOBEN", "KORDIABE", "KOTOBABI", "KPAGURI", "KUKRANTUMI", "KWASHIEMAN",
    "LAMASHEGU", "LARTERBIOKOSHIE", "LATERBIOKORSHIE", "MEDUMA", "MOKOSE",
    "NFROFUL", "ODUOM", "PAGA", "PANKRONUM", "SAVELUGU", "SAMPA", "TANOSO",
    "TREDE", "WALEWALE", "YENDI", "ZONGO", "ZUARUNGU"
}

# Known location names that are clearly cities/towns
KNOWN_CITIES = {
    "ABREPO", "ABUAKWA", "ABURI", "ACCRA", "ACCRA CENTRAL", "ACHIMOTA", "ADABRAKA",
    "ADAMA", "ADDO", "ADENTA", "ADJRINGANOR", "ADUM", "AGOGO", "AGONA", "AHINSAN",
    "AHODWO", "AIRPORT", "AIRPORT RESIDENTIAL", "AKOSOMBO", "AKWATIA", "ANYINAM",
    "ASAFO", "ASAMANKESE", "ASANKRAGWA", "ASHAIMAN", "ASHONGMAN", "ASIAKWA",
    "ASIKUMA", "ASOKWA", "ASSIN", "ASYLUM", "BANTAMA", "BAWKU", "BEGORO", "BEKWAI",
    "BEREKUM", "BIBIANI", "BOGOSO", "BOLGATANGA", "BOMSO", "BREMANG", "CANTONMENTS",
    "CIRCLE", "DADIESO", "DANSOMAN", "DARKUMAN", "DODOWA", "DOME", "DORMAA",
    "DUAYAW", "DZORWULU", "EAST LEGON", "EJISU", "ELMINA", "ENCHI", "ENYIRESI",
    "GBAWE", "GOASO", "HAATSO", "HOHOE", "KADE", "KANESHIE", "KASOA", "KENYASE",
    "KIBI", "KINTAMPO", "KNUST", "KOFORIDUA", "KOKOMLEMLE", "KONONGO", "KORLE BU",
    "KWABENYA", "LA", "LABONE", "LAPAZ", "LASHIBI", "LAWRA", "LEGON", "MADINA",
    "MAMPONG", "MAMPROBI", "MANKESSIM", "MATAHEKO", "NAVRONGO", "NIMA", "NKAWKAW",
    "NKORANZA", "NSAWAM", "NUNGUA", "NYAMEKYE", "OBUASI", "ODUMASE", "OFANKOR",
    "OSIEM", "OSINO", "PATASI", "POKUASE", "SAKUMONO", "SAMPA", "SANTASI",
    "SEKONDI", "SOMANYA", "SPINTEX", "SUAME", "SUHUM", "SUNYANI", "SWEDRU", "TAFO",
    "TAKORADI", "TAMALE", "TANTRA", "TARKWA", "TECHIMAN", "TEMA", "TESANO",
    "TESHIE", "TSE ADDO", "WEIJA", "WENCHI", "WIAMOASE", "WINNEBA"
}


def clean_location_list(locations_file: Path) -> Set[str]:
    """
    Clean the unique_locations.txt file to extract valid city names.

    Args:
        locations_file: Path to unique_locations.txt

    Returns:
        Set of clean city names
    """
    clean_locations = set()

    with open(locations_file, 'r') as f:
        for line in f:
            location = line.strip()

            # Skip empty lines
            if not location:
                continue

            # Skip noise words
            if location in NOISE_WORDS:
                continue

            # Skip very short words (likely noise)
            if len(location) < 3:
                continue

            # Skip words with numbers or special characters (except spaces and hyphens)
            if any(char.isdigit() or char in ['(', ')', ',', '.', '/', '\\', '"', "'"] for char in location):
                continue

            # Add known cities
            if location in KNOWN_CITIES:
                clean_locations.add(location)
                continue

            # Add if it looks like a proper location name
            # (title case or uppercase, reasonable length)
            if location.istitle() or location.isupper():
                if 3 <= len(location) <= 25:
                    clean_locations.add(location)

    return clean_locations


def generate_updated_keywords(clean_locations: Set[str]) -> List[str]:
    """
    Generate updated keywords list.

    Args:
        clean_locations: Set of clean location names

    Returns:
        Updated keywords list
    """
    # Start with current keywords
    keywords_set = set(CURRENT_KEYWORDS)

    # Remove compound names
    for compound in COMPOUND_NAMES_TO_REMOVE:
        keywords_set.discard(compound)

    # Add new individual cities (convert to title case)
    for location in clean_locations:
        # Convert to title case for consistency
        title_case = location.title().replace(' ', '').replace('-', '')
        # Only add if it's alphanumeric (no special characters)
        if title_case.isalnum():
            keywords_set.add(title_case)

    # Sort alphabetically
    return sorted(keywords_set)


def main():
    """Main processing function."""
    print("=" * 80)
    print("Update Deepgram Keywords with New Individual Cities")
    print("=" * 80)
    print()

    # Paths
    locations_file = Path("/opt/kasaai/apps/automations/premier-health/processed_data/unique_locations.txt")
    output_file = Path("/opt/kasaai/apps/automations/premier-health/deepgram_keywords_updated.py")

    # Clean location list
    print("🧹 Cleaning location list...")
    clean_locations = clean_location_list(locations_file)
    print(f"   ✅ Extracted {len(clean_locations)} clean city names")
    print()

    # Show examples of removed compound names
    print("❌ Removing compound names:")
    for compound in COMPOUND_NAMES_TO_REMOVE:
        print(f"   - {compound}")
    print()

    # Show examples of new additions
    print("✅ New cities being added (examples):")
    new_cities = []
    for loc in sorted(clean_locations):
        title_case = loc.title().replace(' ', '')
        if title_case not in CURRENT_KEYWORDS and title_case not in COMPOUND_NAMES_TO_REMOVE:
            new_cities.append(title_case)

    for city in new_cities[:20]:  # Show first 20
        print(f"   + {city}")
    print(f"   ... and {len(new_cities) - 20} more" if len(new_cities) > 20 else "")
    print()

    # Generate updated keywords
    print("📝 Generating updated keywords list...")
    updated_keywords = generate_updated_keywords(clean_locations)
    print(f"   ✅ Total keywords: {len(updated_keywords)} (was {len(CURRENT_KEYWORDS)})")
    print()

    # Write updated file
    print("💾 Writing updated configuration...")
    with open(output_file, 'w') as f:
        f.write("# Updated location keywords for VAPI Deepgram configuration\n")
        f.write("# Generated after reprocessing Premier Health data to separate grouped cities\n")
        f.write("\n")
        f.write("KEYWORDS = [\n")
        for keyword in updated_keywords:
            f.write(f'    "{keyword}",\n')
        f.write("]\n")
        f.write("\n")
        f.write("# Note: Key individual cities now separate:\n")
        f.write("#   - Santasi and Patasi (was: Santasipatase)\n")
        f.write("#   - Tafo and Bremang (was: Tafobremang)\n")
        f.write("#   - Somanya and Odumase (was: Somanyaodumase)\n")
        f.write("#   - Begoro and Osiem (was: Begoroosiem)\n")
        f.write("#   - Abuakwa and Tanoso (was: Abuakwatanoso)\n")
        f.write("#   - Assin and Swedru (was: Assinswedru)\n")

    print(f"   ✅ Saved to: {output_file}")
    print()

    # Summary
    print("=" * 80)
    print("✅ KEYWORDS UPDATE COMPLETE!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  - Compound names removed: {len(COMPOUND_NAMES_TO_REMOVE)}")
    print(f"  - New individual cities added: {len(new_cities)}")
    print(f"  - Total keywords: {len(updated_keywords)}")
    print()
    print("Next steps:")
    print("  1. Review deepgram_keywords_updated.py")
    print("  2. Update VAPI Deepgram configuration via API")
    print("  3. Update CityNormalizer mappings")
    print("  4. Test with real queries")
    print("=" * 80)


if __name__ == "__main__":
    main()
