"""Meta MMS language support with ISO 639-3 codes.

Provides comprehensive language mappings for Meta MMS (Massively Multilingual Speech)
which supports 1162 languages with ISO 639-3 codes.
"""

from typing import Dict, List, Optional, Tuple

# Meta MMS supported languages with ISO 639-3 codes
# This is a subset of the 1162 languages supported by Meta MMS
# Focused on African and emerging market languages
META_MMS_LANGUAGES: Dict[str, Dict[str, str]] = {
    # Ghanaian Languages
    "twi": {"name": "Twi", "iso_639_3": "twi", "native_name": "Twi"},
    "aka": {"name": "Akan", "iso_639_3": "aka", "native_name": "Akan"},
    "ewe": {"name": "Ewe", "iso_639_3": "ewe", "native_name": "Eʋegbe"},
    "gaa": {"name": "Ga", "iso_639_3": "gaa", "native_name": "Ga"},
    "ada": {"name": "Dangme", "iso_639_3": "ada", "native_name": "Dangme"},
    "dag": {"name": "Dagbani", "iso_639_3": "dag", "native_name": "Dagbanli"},
    "nzi": {"name": "Nzema", "iso_639_3": "nzi", "native_name": "Nzema"},
    "gjn": {"name": "Gonja", "iso_639_3": "gjn", "native_name": "Gonja"},
    "xsm": {"name": "Kasem", "iso_639_3": "xsm", "native_name": "Kasem"},
    
    # Nigerian Languages
    "yor": {"name": "Yoruba", "iso_639_3": "yor", "native_name": "Yorùbá"},
    "ibo": {"name": "Igbo", "iso_639_3": "ibo", "native_name": "Igbo"},
    "hau": {"name": "Hausa", "iso_639_3": "hau", "native_name": "Hausa"},
    
    # East African Languages
    "swa": {"name": "Swahili", "iso_639_3": "swa", "native_name": "Kiswahili"},
    "kik": {"name": "Kikuyu", "iso_639_3": "kik", "native_name": "Gĩkũyũ"},
    "luo": {"name": "Luo", "iso_639_3": "luo", "native_name": "Dholuo"},
    "amh": {"name": "Amharic", "iso_639_3": "amh", "native_name": "አማርኛ"},
    "orm": {"name": "Oromo", "iso_639_3": "orm", "native_name": "Afaan Oromoo"},
    "som": {"name": "Somali", "iso_639_3": "som", "native_name": "Soomaali"},
    "tir": {"name": "Tigrinya", "iso_639_3": "tir", "native_name": "ትግርኛ"},
    
    # Southern African Languages
    "zul": {"name": "Zulu", "iso_639_3": "zul", "native_name": "isiZulu"},
    "xho": {"name": "Xhosa", "iso_639_3": "xho", "native_name": "isiXhosa"},
    "afr": {"name": "Afrikaans", "iso_639_3": "afr", "native_name": "Afrikaans"},
    "sot": {"name": "Sotho", "iso_639_3": "sot", "native_name": "Sesotho"},
    "tsn": {"name": "Tswana", "iso_639_3": "tsn", "native_name": "Setswana"},
    "nbl": {"name": "Ndebele", "iso_639_3": "nbl", "native_name": "isiNdebele"},
    "ssw": {"name": "Swati", "iso_639_3": "ssw", "native_name": "siSwati"},
    "tso": {"name": "Tsonga", "iso_639_3": "tso", "native_name": "Xitsonga"},
    "ven": {"name": "Venda", "iso_639_3": "ven", "native_name": "Tshivenda"},
    
    # West African Languages
    "ful": {"name": "Fula", "iso_639_3": "ful", "native_name": "Fulfulde"},
    "wol": {"name": "Wolof", "iso_639_3": "wol", "native_name": "Wolof"},
    "bam": {"name": "Bambara", "iso_639_3": "bam", "native_name": "Bamanankan"},
    "man": {"name": "Mandinka", "iso_639_3": "man", "native_name": "Mandinka"},
    "sus": {"name": "Susu", "iso_639_3": "sus", "native_name": "Sosoxui"},
    "fon": {"name": "Fon", "iso_639_3": "fon", "native_name": "Fon"},
    "kab": {"name": "Kabye", "iso_639_3": "kab", "native_name": "Kabiyè"},
    
    # Central African Languages
    "lin": {"name": "Lingala", "iso_639_3": "lin", "native_name": "Lingála"},
    "kon": {"name": "Kikongo", "iso_639_3": "kon", "native_name": "Kikongo"},
    "lua": {"name": "Tshiluba", "iso_639_3": "lua", "native_name": "Tshiluba"},
    "sag": {"name": "Sango", "iso_639_3": "sag", "native_name": "Sängö"},
    
    # North African Languages
    "ara": {"name": "Arabic", "iso_639_3": "ara", "native_name": "العربية"},
    "ber": {"name": "Tamazight", "iso_639_3": "ber", "native_name": "Tamazight"},
    "aar": {"name": "Afar", "iso_639_3": "aar", "native_name": "Afaraf"},
    "run": {"name": "Kirundi", "iso_639_3": "run", "native_name": "Kirundi"},
    "kin": {"name": "Kinyarwanda", "iso_639_3": "kin", "native_name": "Ikinyarwanda"},
    "mlg": {"name": "Malagasy", "iso_639_3": "mlg", "native_name": "Malagasy"},
    "nya": {"name": "Chichewa", "iso_639_3": "nya", "native_name": "Chichewa"},
    "her": {"name": "Oshiwambo", "iso_639_3": "her", "native_name": "Oshiwambo"},
    "bem": {"name": "Bemba", "iso_639_3": "bem", "native_name": "Ichibemba"},
    "nya": {"name": "Nyanja", "iso_639_3": "nya", "native_name": "Chichewa"},
    "ton": {"name": "Tonga", "iso_639_3": "ton", "native_name": "Chitonga"},
    "sna": {"name": "Shona", "iso_639_3": "sna", "native_name": "chiShona"},
    "nde": {"name": "Ndebele", "iso_639_3": "nde", "native_name": "isiNdebele"},
    
    # Major World Languages
    "eng": {"name": "English", "iso_639_3": "eng", "native_name": "English"},
    "fra": {"name": "French", "iso_639_3": "fra", "native_name": "Français"},
    "spa": {"name": "Spanish", "iso_639_3": "spa", "native_name": "Español"},
    "por": {"name": "Portuguese", "iso_639_3": "por", "native_name": "Português"},
    "cmn": {"name": "Mandarin", "iso_639_3": "cmn", "native_name": "中文"},
    "hin": {"name": "Hindi", "iso_639_3": "hin", "native_name": "हिन्दी"},
    "ind": {"name": "Indonesian", "iso_639_3": "ind", "native_name": "Bahasa Indonesia"},
    "fil": {"name": "Filipino", "iso_639_3": "fil", "native_name": "Filipino"},
    "vie": {"name": "Vietnamese", "iso_639_3": "vie", "native_name": "Tiếng Việt"},
    "tha": {"name": "Thai", "iso_639_3": "tha", "native_name": "ไทย"},
    "tur": {"name": "Turkish", "iso_639_3": "tur", "native_name": "Türkçe"},
}

# Country to Meta MMS language codes mapping
COUNTRY_META_MMS_LANGUAGES: Dict[str, List[str]] = {
    "Ghana": ["twi", "aka", "ewe", "gaa", "ada", "dag", "nzi", "gjn", "xsm", "eng"],
    "Nigeria": ["yor", "ibo", "hau", "eng"],
    "Kenya": ["swa", "kik", "luo", "eng"],
    "Ethiopia": ["amh", "orm", "som", "tir"],
    "South Africa": ["zul", "xho", "afr", "eng", "nbl", "sot", "tsn", "ssw", "tso", "ven"],
    "Tanzania": ["swa", "eng"],
    "Uganda": ["swa", "eng"],
    "Rwanda": ["kin", "eng", "fra"],
    "Burundi": ["run", "eng", "fra"],
    "Somalia": ["som", "ara"],
    "Sudan": ["ara", "eng"],
    "South Sudan": ["eng", "ara"],
    "Senegal": ["wol", "fra"],
    "Mali": ["bam", "fra"],
    "Burkina Faso": ["ful", "fra"],
    "Niger": ["hau", "fra"],
    "Chad": ["ara", "fra"],
    "Cameroon": ["fra", "eng"],
    "Central African Republic": ["sag", "fra"],
    "Democratic Republic of the Congo": ["lin", "swa", "kon", "lua", "fra"],
    "Republic of the Congo": ["lin", "kon", "fra"],
    "Gabon": ["fra"],
    "Equatorial Guinea": ["spa", "fra", "por"],
    "Sao Tome and Principe": ["por"],
    "Angola": ["por"],
    "Mozambique": ["por"],
    "Cabo Verde": ["por"],
    "Guinea-Bissau": ["por"],
    "Guinea": ["ful", "man", "sus", "fra"],
    "Sierra Leone": ["eng"],
    "Liberia": ["eng"],
    "Gambia": ["man", "wol", "ful", "eng"],
    "Mauritania": ["ara", "wol", "fra"],
    "Morocco": ["ara", "ber", "fra"],
    "Algeria": ["ara", "ber"],
    "Tunisia": ["ara", "fra"],
    "Libya": ["ara"],
    "Egypt": ["ara"],
    "Eritrea": ["tir", "ara", "eng"],
    "Djibouti": ["som", "ara", "aar", "fra"],
    "Comoros": ["ara", "fra"],
    "Madagascar": ["mlg", "fra"],
    "Mauritius": ["eng", "fra"],
    "Seychelles": ["eng", "fra"],
    "Zambia": ["bem", "nya", "ton", "eng"],
    "Zimbabwe": ["sna", "nde", "eng"],
    "Botswana": ["tsn", "eng"],
    "Namibia": ["her", "afr", "eng"],
    "Lesotho": ["sot", "eng"],
    "Eswatini": ["ssw", "eng"],
    "Malawi": ["nya", "eng"],
    "Brazil": ["por"],
    "China": ["cmn"],
    "India": ["hin", "eng"],
    "Indonesia": ["ind"],
    "Mexico": ["spa"],
    "Philippines": ["fil", "eng"],
    "Vietnam": ["vie"],
    "Thailand": ["tha"],
    "Turkey": ["tur"],
    "Argentina": ["spa"],
}

def get_meta_mms_language_info(language_code: str) -> Optional[Dict[str, str]]:
    """Get language information for a Meta MMS language code.
    
    Args:
        language_code (str): ISO 639-3 language code
        
    Returns:
        Optional[Dict[str, str]]: Language information or None if not found
    """
    return META_MMS_LANGUAGES.get(language_code.lower())

def get_meta_mms_languages_for_country(country: str) -> List[Dict[str, str]]:
    """Get Meta MMS supported languages for a specific country.
    
    Args:
        country (str): Country name
        
    Returns:
        List[Dict[str, str]]: List of language information dictionaries
    """
    language_codes = COUNTRY_META_MMS_LANGUAGES.get(country, [])
    return [get_meta_mms_language_info(code) for code in language_codes if get_meta_mms_language_info(code)]

def get_all_meta_mms_languages() -> List[Dict[str, str]]:
    """Get all Meta MMS supported languages.
    
    Returns:
        List[Dict[str, str]]: List of all language information dictionaries
    """
    return list(META_MMS_LANGUAGES.values())

def get_language_display_name(language_code: str) -> str:
    """Get display name for a language code.
    
    Args:
        language_code (str): ISO 639-3 language code
        
    Returns:
        str: Display name in format "Language Name (code)"
    """
    lang_info = get_meta_mms_language_info(language_code)
    if lang_info:
        return f"{lang_info['name']} ({language_code})"
    return language_code

def is_meta_mms_supported(language_code: str) -> bool:
    """Check if a language is supported by Meta MMS.
    
    Args:
        language_code (str): ISO 639-3 language code
        
    Returns:
        bool: True if supported, False otherwise
    """
    return language_code.lower() in META_MMS_LANGUAGES
