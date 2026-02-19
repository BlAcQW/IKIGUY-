"""Country language mappings for Africa and other emerging markets.

Provides helper functions for retrieving language options by country.
"""
from typing import Dict, List

AFRICAN_COUNTRY_LANGUAGES: Dict[str, List[str]] = {
    "Algeria": ["Arabic", "Tamazight"],
    "Angola": ["Portuguese"],
    "Benin": ["French", "Fon", "Yoruba"],
    "Botswana": ["English", "Tswana"],
    "Burkina Faso": ["French", "Moore", "Dioula"],
    "Burundi": ["Kirundi", "French", "English"],
    "Cabo Verde": ["Portuguese", "Kabuverdianu"],
    "Cameroon": ["French", "English"],
    "Central African Republic": ["French", "Sango"],
    "Chad": ["French", "Arabic"],
    "Comoros": ["Arabic", "French", "Comorian"],
    "Democratic Republic of the Congo": [
        "French",
        "Lingala",
        "Swahili",
        "Kikongo",
        "Tshiluba",
    ],
    "Republic of the Congo": ["French", "Lingala", "Kikongo"],
    "Djibouti": ["French", "Arabic", "Somali", "Afar"],
    "Egypt": ["Arabic"],
    "Equatorial Guinea": ["Spanish", "French", "Portuguese"],
    "Eritrea": ["Tigrinya", "Arabic", "English"],
    "Eswatini": ["English", "Swati"],
    "Ethiopia": ["Amharic", "Oromo", "Somali", "Tigrinya"],
    "Gabon": ["French"],
    "Gambia": ["English", "Mandinka", "Wolof", "Fula"],
    "Ghana": ["English", "Akan", "Ewe", "Ga", "Dagbani", "Hausa"],
    "Guinea": ["French", "Fula", "Maninka", "Susu"],
    "Guinea-Bissau": ["Portuguese", "Kriol"],
    "Ivory Coast": ["French"],
    "Kenya": ["English", "Swahili"],
    "Lesotho": ["English", "Sesotho"],
    "Liberia": ["English"],
    "Libya": ["Arabic"],
    "Madagascar": ["Malagasy", "French"],
    "Malawi": ["English", "Chichewa"],
    "Mali": ["French", "Bambara"],
    "Mauritania": ["Arabic", "French", "Wolof"],
    "Mauritius": ["English", "French", "Mauritian Creole"],
    "Morocco": ["Arabic", "Tamazight", "French"],
    "Mozambique": ["Portuguese"],
    "Namibia": ["English", "Afrikaans", "German", "Oshiwambo"],
    "Niger": ["French", "Hausa", "Zarma"],
    "Nigeria": ["English", "Hausa", "Yoruba", "Igbo"],
    "Rwanda": ["Kinyarwanda", "French", "English", "Swahili"],
    "Sao Tome and Principe": ["Portuguese"],
    "Senegal": ["French", "Wolof"],
    "Seychelles": ["Seychellois Creole", "English", "French"],
    "Sierra Leone": ["English", "Krio"],
    "Somalia": ["Somali", "Arabic"],
    "South Africa": [
        "Zulu",
        "Xhosa",
        "Afrikaans",
        "English",
        "Ndebele",
        "Northern Sotho",
        "Sotho",
        "Swati",
        "Tsonga",
        "Tswana",
        "Venda",
    ],
    "South Sudan": ["English", "Arabic"],
    "Sudan": ["Arabic", "English"],
    "Tanzania": ["Swahili", "English"],
    "Togo": ["French", "Ewe", "Kabye"],
    "Tunisia": ["Arabic", "French"],
    "Uganda": ["English", "Swahili"],
    "Zambia": ["English", "Bemba", "Nyanja", "Tonga"],
    "Zimbabwe": ["English", "Shona", "Ndebele"],
}

EMERGING_COUNTRY_LANGUAGES: Dict[str, List[str]] = {
    "Brazil": ["Portuguese"],
    "China": ["Mandarin"],
    "India": ["Hindi", "English"],
    "Indonesia": ["Indonesian"],
    "Mexico": ["Spanish"],
    "Philippines": ["Filipino", "English"],
    "Vietnam": ["Vietnamese"],
    "Thailand": ["Thai"],
    "Turkey": ["Turkish"],
    "Argentina": ["Spanish"],
}

ALL_COUNTRY_LANGUAGES: Dict[str, List[str]] = {
    **AFRICAN_COUNTRY_LANGUAGES,
    **EMERGING_COUNTRY_LANGUAGES,
}


def get_country_languages(country: str) -> List[str]:
    """Return languages spoken in the specified country.

    Args:
        country (str): Country name. Case-insensitive.

    Returns:
        List[str]: List of languages for the country.

    Raises:
        KeyError: If ``country`` is not recognized.
    """
    key = country.strip().title()
    return ALL_COUNTRY_LANGUAGES[key]
