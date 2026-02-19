#!/usr/bin/env python3
"""
Regional City Segmentation for VAPI Squad Implementation
Segments 295+ cities into 6 regions for multi-assistant routing
"""

# Ghana Regional City Mapping
# Based on actual Ghana regions and Premier Health facility locations

REGIONAL_CITIES = {
    "Greater Accra": [
        # Major cities
        "ACCRA", "TEMA", "MADINA", "ADENTA", "LEGON",

        # Accra suburbs and districts
        "ACHIMOTA", "ADABRAKA", "DANSOMAN", "KANESHIE", "ASHAIMAN",
        "TESHIE", "LABADI", "SPINTEX", "ASHONGMAN", "OSU",
        "LABONE", "DZORWULU", "HAATSO", "DOME", "KASOA",
        "WEIJA", "GBAWE", "KWABENYA", "NUNGUA", "SAKUMONO",
        "LASHIBI", "AWOSHIE", "BUBUASHIE", "LAPAZ", "KOKOMLEMLE",
        "DARKUMAN", "MAMPROBI", "KORLE", "BU", "CANTONMENT",
        "TESANO", "KANDA", "ASYLUM", "CAIRO", "CANTONMENTS",
        "LA", "LAKESIDE", "KISSEMAN", "KLAGON", "LEDZOKUKU",
        "OFANKOR", "POKUASE", "AMASAMAN", "KWABENYA", "TAIFA",
        "ADDO", "ADJRINGANOR", "ADJIRINGANOR", "ADJOATE", "ADJUCENT",
        "BAATSONA", "DAWHENYA", "DODOWA", "GBETSILE", "GLALAH",
        "KANTON", "KOTOBABI", "KWASHIEMAN", "LARTERBIOKOSHIE",
        "LATERBIOKORSHIE", "LARAMART", "LASHIBI", "LAWSEC",
        "MATAHEKO", "MCCARTHY", "NIMA", "OKAI", "PADMORE",
        "PANKRONUM", "SAKUMONO", "TANTRA", "TSE", "TUBA",
        "UPSA", "ADIESENT", "ADJAPOMAA", "ADEIBEBA", "ADIETEM",
        "DARKWA", "DEME", "KOTWI", "KRONUN", "LEBANON",
        "NARH", "NYAMEKYE", "NYANYO", "SAHID", "SRODAE",
        "SSNIT", "WESTLINE", "ZENU",
    ],

    "Ashanti": [
        # Major cities
        "KUMASI", "OBUASI", "MAMPONG", "KONONGO",

        # Kumasi districts
        "AHODWO", "ASOKWA", "BANTAMA", "ADUM", "TAFO",
        "SUAME", "SANTASI", "BOMSO", "BREMANG", "PATASI",
        "AFRANCHO", "ABREPO", "ASANTEWAA", "BEKWAI", "AGOGO",
        "KOKOBEN", "EJISU", "AFARI", "AFARIWA", "AHENEMA",
        "AHENSAN", "AHINSAN", "ANYINAM", "ASENEMASO", "ATASOMANSO",
        "ATEKYEM", "BESEASE", "DWENEASE", "KEJETIA", "KENYASE",
        "KENYASI", "KETAN", "KNUST", "KOJO", "KOTWI",
        "KWADASO", "MAAME", "MANGO", "MANKESSIM", "MEDUMA",
        "MENSVIC", "MOKOSE", "NYOHINI", "ODUOM", "PEPRAN",
        "SANTASIPATASE", "KENTINKRONO", "APUTUGYA", "BRAZZA",
        "BUOKROM", "DAKWADWOM", "DANYAME", "FIDELITY", "KENTINKRONO",
        "KOKROMPE", "MEDLOVE", "NALURO", "NANA", "OHENE",
        "OPPT", "PARAKUO", "PENTECOST", "TAFOBREMANG", "TANOSO",
        "TREDE", "YAKASI",
    ],

    "Northern Regions": [
        # Northern Region
        "TAMALE", "YENDI", "SAVELUGU", "TOLON", "KUMBUNGU",
        "LAMASHEGU", "KANVILLI", "JISONAYILI", "NYOHINI", "SAWAABA",
        "TAMSO",

        # Upper East
        "BOLGATANGA", "BOLGA", "BAWKU", "NAVRONGO", "PAGA",
        "KATARIGA", "KPAGURI", "KPAKPA", "KPANVO", "SOE",
        "SABONKUDI", "ZUARUNGU",

        # Upper West
        "WA", "LAWRA", "WALEWALE", "BIMBILLA",

        # North East/Savannah
        "SALAGA", "DAMONGO", "BOLE",
    ],

    "Western and Central": [
        # Western Region
        "TAKORADI", "SEKONDI", "TARKWA", "PRESTEA", "BOGOSO",
        "BIBIANI", "ESSIKADO", "FIJAI", "EFFIA", "ANAJI",
        "KETAN", "SAMREBOI", "SEFWI", "SHAMA", "GLOOVY",
        "ABOADZE", "AGONA", "ASSIN", "ASSINSWEDRU", "DADIESO",
        "EFIAKWANTA", "ENCHI", "EWIM", "INCHABAN", "NFROFUL",
        "WASSA", "WIAWSO", "APSONIC", "EMINA", "POUHUN",
        "SDD", "SEBREPOR", "SECONDI", "TAKWA",

        # Central Region
        "CAPE COAST", "WINNEBA", "ELMINA", "SALTPOND", "MANKESSIM",
        "AGONA", "ASIKUMA", "ABURI", "ABUAKWA", "ABOTANSO",
        "DODOWA", "KASOA", "WEIJA", "AWUTU", "GOMOA",
        "OPEIKUMA", "SWEDRU",
    ],

    "Eastern and Volta": [
        # Eastern Region
        "KOFORIDUA", "NKAWKAW", "NSAWAM", "AKOSOMBO", "SOMANYA",
        "KIBI", "BEGORO", "ASIAKWA", "SUHUM", "ASAMANKESE",
        "ABURI", "AKWATIA", "ANYINAM", "KADE", "KUKRANTUMI",
        "MAMFE", "ODA", "ODUMASE", "ODUMASI", "OSIEM",
        "OSINO", "ABAASE", "ABIREM", "ADAMA", "ADDOGONNO",
        "ADOAGYIRI", "KAKASUNANKA", "MPREASO", "TUOBODOM",
        "BEGOROROSIEM", "KORDIABE", "ENYIRESI",

        # Volta Region
        "HO", "HOHOE", "KETA", "ANLOGA", "AFLAO",
        "SOGAKOPE", "AKATSI", "KPANDO", "DEME",
    ],

    "Bono Regions": [
        # Bono Region
        "SUNYANI", "BEREKUM", "DORMAA", "WENCHI", "SAMPA",
        "FIAPRE", "DROBO", "GOASO", "HWIDIEM", "KENYASI",

        # Bono East
        "TECHIMAN", "KINTAMPO", "ATEBUBU", "NKORANZA", "JAMAN",
        "JAMASE", "JAMERA", "JEMA", "PRANG",

        # Ahafo
        "DUAYAW", "BECHEM", "ACHERENSUA", "KUKUOM",

        # Additional smaller towns
        "ANAPUA", "ANHWIANKWATA", "APATRAPA", "BADU", "BAMAHU",
        "BETHEL", "BINEY", "JUABOSO", "JUKWA", "KENKEY",
        "LOKKO", "OPEIKUMA", "SAMPA",
    ],
}

# Common words/descriptors to exclude (not actual cities)
EXCLUDE_WORDS = [
    "ADJACENT", "ALONG", "AIRPORT", "AROUND", "AT", "AFTER",
    "BAKE", "CAPE", "CEDI", "CLAY", "CLOSE", "COAST", "COCOA",
    "COMM", "COMMUNITY", "COUNCIL", "DISTRICT", "EAST", "FILM",
    "FORMER", "GENERAL", "GHANA", "GLOBAL", "GOLF", "GRAPHIC",
    "GREENLIGHT", "GUINNESS", "HABOUR", "HERITAGE", "HILA",
    "HOSPITAL", "HOUSE", "HSE", "HYGIENCE", "H_NO", "ISD",
    "JACKSON", "JOHN", "JOSEPTH", "JUNCTION", "MILE", "MORTUARY",
    "MUNICIPAL", "NEWMONT", "NOBISCO", "NT", "OFFICIAL", "PLAT",
    "PLOT", "POLICE", "POST", "PRESBY", "PRESTIGE", "PRIMARY",
    "QUEENS", "RAILS", "REGIONAL", "RESIDENTIAL", "RIDGE",
    "ROBERT", "ROMAN", "RUSSIAN", "SHOP", "SHOPPING", "SITE",
    "SNITT", "SOUTH", "STARTLETS", "STATE", "STATION", "STOP",
    "SUNNY", "TECHNICAL", "THEATER", "TOPMAN", "TOTAL", "TOWER",
    "TRAFFIC", "WEST", "WOODIN", "WORKERS", "YIYIWA", "ZONGO",
]


def load_all_cities():
    """Load all cities from PREMIER_CITIES_MIN.md"""
    with open('/opt/kasaai/apps/automations/premier-health/PREMIER_CITIES_MIN.md', 'r') as f:
        content = f.read()
        cities = content.split()
    return cities


def segment_cities():
    """
    Segment all cities into regions

    Returns:
        dict: Regional city assignments with counts
    """
    all_cities = load_all_cities()

    # Track which cities are assigned
    assigned_cities = set()
    unassigned_cities = []

    # Flatten regional cities for tracking
    for region, cities in REGIONAL_CITIES.items():
        assigned_cities.update(cities)

    # Find unassigned cities
    for city in all_cities:
        if city not in assigned_cities and city not in EXCLUDE_WORDS:
            unassigned_cities.append(city)

    # Print summary
    print("=" * 80)
    print("REGIONAL CITY SEGMENTATION SUMMARY")
    print("=" * 80)
    print(f"\nTotal cities in database: {len(all_cities)}")
    print(f"Cities assigned to regions: {len(assigned_cities)}")
    print(f"Excluded common words: {len([c for c in all_cities if c in EXCLUDE_WORDS])}")
    print(f"Unassigned cities: {len(unassigned_cities)}\n")

    for region, cities in REGIONAL_CITIES.items():
        count = len(cities)
        status = "✓" if count <= 100 else "⚠"
        print(f"{status} {region:30} {count:3} cities")

    if unassigned_cities:
        print(f"\n⚠ UNASSIGNED CITIES ({len(unassigned_cities)}):")
        print(", ".join(unassigned_cities[:20]))
        if len(unassigned_cities) > 20:
            print(f"... and {len(unassigned_cities) - 20} more")

    print("\n" + "=" * 80)

    return REGIONAL_CITIES, unassigned_cities


def get_region_keyterms(region_name):
    """
    Get keyterm list for a specific region (max 100)

    Args:
        region_name (str): Name of region

    Returns:
        list: List of city keyterms for the region
    """
    cities = REGIONAL_CITIES.get(region_name, [])

    # Limit to 100 for Deepgram
    if len(cities) > 100:
        print(f"⚠ Warning: {region_name} has {len(cities)} cities, truncating to 100")
        cities = cities[:100]

    return cities


def export_regional_cities(output_file="regional_cities_export.json"):
    """
    Export regional city assignments to JSON file

    Args:
        output_file (str): Output filename
    """
    import json

    export_data = {
        "metadata": {
            "total_cities": sum(len(cities) for cities in REGIONAL_CITIES.values()),
            "regions": len(REGIONAL_CITIES),
            "generated": "2025-10-20"
        },
        "regions": {}
    }

    for region, cities in REGIONAL_CITIES.items():
        export_data["regions"][region] = {
            "count": len(cities),
            "cities": sorted(cities),
            "within_limit": len(cities) <= 100
        }

    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)

    print(f"\n✓ Exported regional city data to {output_file}")


if __name__ == "__main__":
    regional_cities, unassigned = segment_cities()
    export_regional_cities("/opt/kasaai/apps/automations/premier-health/regional_cities_export.json")

    print("\n✓ Regional city segmentation complete!")
    print(f"✓ Ready for VAPI Squad implementation with {len(REGIONAL_CITIES)} regional assistants")
