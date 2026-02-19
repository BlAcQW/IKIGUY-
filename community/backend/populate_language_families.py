#!/usr/bin/env python3
"""
Comprehensive Language Family and Language Population Script
Populates MongoDB with world language families, subfamilies, and individual languages
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import sys

# Add the backend directory to the path
sys.path.append('/opt/kasaai/apps/community/backend')

from core.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Comprehensive language family data
LANGUAGE_FAMILIES_DATA = {
    # AFRICAN LANGUAGE FAMILIES (Primary Focus)
    "niger-congo": {
        "name": "Niger-Congo",
        "continent": "Africa",
        "total_speakers": 500_000_000,
        "total_languages": 1532,
        "description": "The largest language family in Africa and one of the largest in the world",
        "geographic_distribution": "Sub-Saharan Africa",
        "characteristics": [
            "Noun class systems",
            "Agglutinative morphology",
            "Tone languages",
            "Serial verb constructions"
        ],
        "subfamilies": {
            "kwa": {
                "name": "Kwa",
                "speakers": 45_000_000,
                "languages": 75,
                "description": "West African subfamily including Akan languages",
                "geographic_area": "Ghana, Ivory Coast, Togo",
                "languages": {
                    "twi": {
                        "name": "Twi",
                        "native_name": "Twi",
                        "iso639_3": "twi",
                        "speakers": 9_000_000,
                        "countries": ["Ghana"],
                        "status": "living",
                        "writing_system": ["Latin"],
                        "dialects": ["Asante", "Akuapem", "Kwahu"],
                        "official_status": "national"
                    },
                    "fante": {
                        "name": "Fante",
                        "native_name": "Fante",
                        "iso639_3": "fat",
                        "speakers": 2_500_000,
                        "countries": ["Ghana"],
                        "status": "living",
                        "writing_system": ["Latin"],
                        "dialects": ["Anomabo", "Gomoa", "Agona"]
                    },
                    "ga": {
                        "name": "Ga",
                        "native_name": "Gã",
                        "iso639_3": "gaa",
                        "speakers": 1_000_000,
                        "countries": ["Ghana"],
                        "status": "living",
                        "writing_system": ["Latin"],
                        "dialects": ["Accra Ga", "Teshi Ga"]
                    },
                    "ewe": {
                        "name": "Ewe",
                        "native_name": "Eʋegbe",
                        "iso639_3": "ewe",
                        "speakers": 6_000_000,
                        "countries": ["Ghana", "Togo", "Benin"],
                        "status": "living",
                        "writing_system": ["Latin"],
                        "dialects": ["Anlo", "Tongu", "Inland Ewe"]
                    }
                }
            },
            "yoruboid": {
                "name": "Yoruboid",
                "speakers": 50_000_000,
                "languages": 15,
                "description": "West African subfamily centered on Yoruba",
                "geographic_area": "Nigeria, Benin, Togo",
                "languages": {
                    "yoruba": {
                        "name": "Yoruba",
                        "native_name": "Yorùbá",
                        "iso639_3": "yor",
                        "speakers": 45_000_000,
                        "countries": ["Nigeria", "Benin", "Togo"],
                        "status": "living",
                        "writing_system": ["Latin", "Arabic"],
                        "dialects": ["Lagos", "Ibadan", "Oyo", "Ekiti"],
                        "official_status": "national"
                    },
                    "igala": {
                        "name": "Igala",
                        "native_name": "Igala",
                        "iso639_3": "igl",
                        "speakers": 2_000_000,
                        "countries": ["Nigeria"],
                        "status": "living",
                        "writing_system": ["Latin"]
                    }
                }
            },
            "bantu": {
                "name": "Bantu",
                "speakers": 350_000_000,
                "languages": 535,
                "description": "Largest Niger-Congo subfamily, spread across central and southern Africa",
                "geographic_area": "Central, Eastern, and Southern Africa",
                "languages": {
                    "swahili": {
                        "name": "Swahili",
                        "native_name": "Kiswahili",
                        "iso639_3": "swa",
                        "speakers": 200_000_000,
                        "countries": ["Tanzania", "Kenya", "Uganda", "Rwanda", "Burundi", "DRC"],
                        "status": "living",
                        "writing_system": ["Latin", "Arabic"],
                        "dialects": ["Kiunguja", "Kimvita", "Kiamu"],
                        "official_status": "official"
                    },
                    "zulu": {
                        "name": "Zulu",
                        "native_name": "isiZulu",
                        "iso639_3": "zul",
                        "speakers": 12_000_000,
                        "countries": ["South Africa"],
                        "status": "living",
                        "writing_system": ["Latin"],
                        "dialects": ["Natal Zulu", "Transvaal Zulu"],
                        "official_status": "official"
                    },
                    "xhosa": {
                        "name": "Xhosa",
                        "native_name": "isiXhosa",
                        "iso639_3": "xho",
                        "speakers": 8_200_000,
                        "countries": ["South Africa"],
                        "status": "living",
                        "writing_system": ["Latin"],
                        "dialects": ["Gcaleka", "Ngqika", "Ndlambe"],
                        "official_status": "official"
                    },
                    "shona": {
                        "name": "Shona",
                        "native_name": "chiShona",
                        "iso639_3": "sna",
                        "speakers": 14_200_000,
                        "countries": ["Zimbabwe", "Mozambique"],
                        "status": "living",
                        "writing_system": ["Latin"],
                        "dialects": ["Zezuru", "Karanga", "Manyika", "Ndau"],
                        "official_status": "official"
                    },
                    "kikuyu": {
                        "name": "Kikuyu",
                        "native_name": "Gĩkũyũ",
                        "iso639_3": "kik",
                        "speakers": 8_100_000,
                        "countries": ["Kenya"],
                        "status": "living",
                        "writing_system": ["Latin"]
                    }
                }
            },
            "mande": {
                "name": "Mande",
                "speakers": 25_000_000,
                "languages": 70,
                "description": "West African subfamily including Mandinka and Bambara",
                "geographic_area": "Mali, Senegal, Guinea, Sierra Leone",
                "languages": {
                    "bambara": {
                        "name": "Bambara",
                        "native_name": "Bamanankan",
                        "iso639_3": "bam",
                        "speakers": 14_000_000,
                        "countries": ["Mali", "Burkina Faso", "Senegal"],
                        "status": "living",
                        "writing_system": ["Latin", "N'Ko"],
                        "official_status": "national"
                    },
                    "mandinka": {
                        "name": "Mandinka",
                        "native_name": "Mandinka",
                        "iso639_3": "mnk",
                        "speakers": 2_000_000,
                        "countries": ["Gambia", "Senegal", "Mali", "Guinea-Bissau"],
                        "status": "living",
                        "writing_system": ["Latin", "Arabic", "N'Ko"]
                    }
                }
            }
        }
    },

    "afroasiatic": {
        "name": "Afroasiatic",
        "continent": "Africa & Middle East",
        "total_speakers": 400_000_000,
        "total_languages": 375,
        "description": "Large language family spanning North Africa and the Middle East",
        "geographic_distribution": "North Africa, Horn of Africa, Middle East",
        "characteristics": [
            "Root-and-pattern morphology",
            "Pharyngeal consonants",
            "Triconsonantal roots",
            "VSO word order (many languages)"
        ],
        "subfamilies": {
            "semitic": {
                "name": "Semitic",
                "speakers": 330_000_000,
                "languages": 77,
                "description": "Includes Arabic and Hebrew",
                "geographic_area": "Middle East, North Africa",
                "languages": {
                    "arabic": {
                        "name": "Arabic",
                        "native_name": "العربية",
                        "iso639_3": "ara",
                        "speakers": 310_000_000,
                        "countries": ["Egypt", "Saudi Arabia", "Algeria", "Morocco", "Tunisia", "Libya", "Sudan"],
                        "status": "living",
                        "writing_system": ["Arabic"],
                        "dialects": ["Egyptian", "Levantine", "Gulf", "Maghrebi"],
                        "official_status": "official"
                    },
                    "hebrew": {
                        "name": "Hebrew",
                        "native_name": "עברית",
                        "iso639_3": "heb",
                        "speakers": 9_000_000,
                        "countries": ["Israel"],
                        "status": "living",
                        "writing_system": ["Hebrew"],
                        "official_status": "official"
                    },
                    "tigrinya": {
                        "name": "Tigrinya",
                        "native_name": "ትግርኛ",
                        "iso639_3": "tir",
                        "speakers": 7_000_000,
                        "countries": ["Eritrea", "Ethiopia"],
                        "status": "living",
                        "writing_system": ["Ge'ez"],
                        "official_status": "official"
                    }
                }
            },
            "cushitic": {
                "name": "Cushitic",
                "speakers": 60_000_000,
                "languages": 47,
                "description": "Horn of Africa languages",
                "geographic_area": "Ethiopia, Somalia, Kenya, Djibouti",
                "languages": {
                    "oromo": {
                        "name": "Oromo",
                        "native_name": "Afaan Oromoo",
                        "iso639_3": "orm",
                        "speakers": 37_000_000,
                        "countries": ["Ethiopia", "Kenya"],
                        "status": "living",
                        "writing_system": ["Latin", "Ge'ez"],
                        "dialects": ["Western Oromo", "Eastern Oromo"],
                        "official_status": "regional"
                    },
                    "somali": {
                        "name": "Somali",
                        "native_name": "Soomaali",
                        "iso639_3": "som",
                        "speakers": 21_000_000,
                        "countries": ["Somalia", "Ethiopia", "Kenya", "Djibouti"],
                        "status": "living",
                        "writing_system": ["Latin"],
                        "dialects": ["Northern Somali", "Central Somali", "Southern Somali"],
                        "official_status": "official"
                    },
                    "sidamo": {
                        "name": "Sidamo",
                        "native_name": "Sidaamu Afoo",
                        "iso639_3": "sid",
                        "speakers": 3_000_000,
                        "countries": ["Ethiopia"],
                        "status": "living",
                        "writing_system": ["Ge'ez", "Latin"]
                    }
                }
            },
            "chadic": {
                "name": "Chadic",
                "speakers": 70_000_000,
                "languages": 195,
                "description": "Central African languages including Hausa",
                "geographic_area": "Nigeria, Chad, Cameroon, Niger",
                "languages": {
                    "hausa": {
                        "name": "Hausa",
                        "native_name": "Harshen Hausa",
                        "iso639_3": "hau",
                        "speakers": 70_000_000,
                        "countries": ["Nigeria", "Niger", "Chad", "Ghana"],
                        "status": "living",
                        "writing_system": ["Latin", "Arabic"],
                        "dialects": ["Western Hausa", "Eastern Hausa"],
                        "official_status": "regional"
                    },
                    "kanuri": {
                        "name": "Kanuri",
                        "native_name": "Kanuri",
                        "iso639_3": "knc",
                        "speakers": 4_000_000,
                        "countries": ["Nigeria", "Niger", "Chad", "Cameroon"],
                        "status": "living",
                        "writing_system": ["Latin", "Arabic"]
                    }
                }
            },
            "berber": {
                "name": "Berber",
                "speakers": 25_000_000,
                "languages": 26,
                "description": "North African indigenous languages",
                "geographic_area": "Morocco, Algeria, Tunisia, Libya",
                "languages": {
                    "kabyle": {
                        "name": "Kabyle",
                        "native_name": "Taqbaylit",
                        "iso639_3": "kab",
                        "speakers": 5_500_000,
                        "countries": ["Algeria"],
                        "status": "living",
                        "writing_system": ["Latin", "Tifinagh"]
                    },
                    "tamazight": {
                        "name": "Central Atlas Tamazight",
                        "native_name": "ⵜⴰⵎⴰⵣⵉⵖⵜ",
                        "iso639_3": "tzm",
                        "speakers": 3_000_000,
                        "countries": ["Morocco"],
                        "status": "living",
                        "writing_system": ["Tifinagh", "Latin", "Arabic"],
                        "official_status": "official"
                    }
                }
            }
        }
    },

    "nilo-saharan": {
        "name": "Nilo-Saharan",
        "continent": "Africa",
        "total_speakers": 60_000_000,
        "total_languages": 206,
        "description": "Diverse family spanning central and eastern Africa",
        "geographic_distribution": "Sudan, South Sudan, Uganda, Kenya, Tanzania, Chad",
        "characteristics": [
            "Diverse linguistic features",
            "Agglutinative morphology",
            "Complex verb systems",
            "Tone languages (many)"
        ],
        "subfamilies": {
            "nilotic": {
                "name": "Nilotic",
                "speakers": 30_000_000,
                "languages": 50,
                "description": "Languages of the Nile valley and East Africa",
                "geographic_area": "South Sudan, Uganda, Kenya, Tanzania",
                "languages": {
                    "dinka": {
                        "name": "Dinka",
                        "native_name": "Thuɔŋjäŋ",
                        "iso639_3": "din",
                        "speakers": 4_500_000,
                        "countries": ["South Sudan"],
                        "status": "living",
                        "writing_system": ["Latin"],
                        "dialects": ["Rek", "Malual", "Bor"]
                    },
                    "luo": {
                        "name": "Luo",
                        "native_name": "Dholuo",
                        "iso639_3": "luo",
                        "speakers": 4_200_000,
                        "countries": ["Kenya", "Tanzania"],
                        "status": "living",
                        "writing_system": ["Latin"]
                    },
                    "maasai": {
                        "name": "Maasai",
                        "native_name": "ɔl Maa",
                        "iso639_3": "mas",
                        "speakers": 1_500_000,
                        "countries": ["Kenya", "Tanzania"],
                        "status": "living",
                        "writing_system": ["Latin"]
                    },
                    "nuer": {
                        "name": "Nuer",
                        "native_name": "Thok Naath",
                        "iso639_3": "nus",
                        "speakers": 1_800_000,
                        "countries": ["South Sudan", "Ethiopia"],
                        "status": "living",
                        "writing_system": ["Latin"]
                    }
                }
            },
            "central-sudanic": {
                "name": "Central Sudanic",
                "speakers": 15_000_000,
                "languages": 60,
                "description": "Central African languages",
                "geographic_area": "Chad, CAR, DRC, Sudan",
                "languages": {
                    "sara": {
                        "name": "Sara",
                        "native_name": "Sara",
                        "iso639_3": "sar",
                        "speakers": 3_000_000,
                        "countries": ["Chad", "CAR"],
                        "status": "living",
                        "writing_system": ["Latin"]
                    }
                }
            }
        }
    },

    "khoisan": {
        "name": "Khoisan",
        "continent": "Africa",
        "total_speakers": 300_000,
        "total_languages": 27,
        "description": "Click languages of southern Africa",
        "geographic_distribution": "South Africa, Botswana, Namibia",
        "characteristics": [
            "Click consonants",
            "Complex phoneme inventories",
            "SOV word order",
            "Evidentiality systems"
        ],
        "subfamilies": {
            "khoe": {
                "name": "Khoe",
                "speakers": 200_000,
                "languages": 11,
                "description": "Khoe-Kwadi languages",
                "geographic_area": "Botswana, Namibia",
                "languages": {
                    "nama": {
                        "name": "Nama",
                        "native_name": "Khoekhoegowab",
                        "iso639_3": "naq",
                        "speakers": 200_000,
                        "countries": ["Namibia", "South Africa"],
                        "status": "living",
                        "writing_system": ["Latin"]
                    }
                }
            },
            "tuu": {
                "name": "Tuu",
                "speakers": 10_000,
                "languages": 2,
                "description": "Southern Khoisan languages",
                "geographic_area": "South Africa",
                "languages": {
                    "xun": {
                        "name": "ǃXun",
                        "native_name": "ǃXun",
                        "iso639_3": "knw",
                        "speakers": 8_000,
                        "countries": ["South Africa", "Botswana", "Namibia"],
                        "status": "living",
                        "writing_system": ["Latin"]
                    }
                }
            }
        }
    },

    # MAJOR WORLD LANGUAGE FAMILIES
    "sino-tibetan": {
        "name": "Sino-Tibetan",
        "continent": "Asia",
        "total_speakers": 1_400_000_000,
        "total_languages": 449,
        "description": "Largest language family by number of speakers",
        "geographic_distribution": "China, Tibet, Southeast Asia",
        "characteristics": [
            "Tone languages",
            "Monosyllabic roots",
            "Isolating morphology",
            "SOV/SVO word order"
        ],
        "subfamilies": {
            "sinitic": {
                "name": "Sinitic",
                "speakers": 1_300_000_000,
                "languages": 15,
                "description": "Chinese languages",
                "geographic_area": "China, Taiwan, Singapore",
                "languages": {
                    "mandarin": {
                        "name": "Mandarin Chinese",
                        "native_name": "官话",
                        "iso639_3": "cmn",
                        "speakers": 918_000_000,
                        "countries": ["China", "Taiwan", "Singapore"],
                        "status": "living",
                        "writing_system": ["Chinese"],
                        "official_status": "official"
                    },
                    "wu": {
                        "name": "Wu Chinese",
                        "native_name": "吴语",
                        "iso639_3": "wuu",
                        "speakers": 80_000_000,
                        "countries": ["China"],
                        "status": "living",
                        "writing_system": ["Chinese"]
                    },
                    "cantonese": {
                        "name": "Cantonese",
                        "native_name": "粵語",
                        "iso639_3": "yue",
                        "speakers": 84_000_000,
                        "countries": ["China", "Hong Kong", "Macau"],
                        "status": "living",
                        "writing_system": ["Chinese"]
                    }
                }
            },
            "tibeto-burman": {
                "name": "Tibeto-Burman",
                "speakers": 100_000_000,
                "languages": 434,
                "description": "Tibetan and Burmese languages",
                "geographic_area": "Tibet, Myanmar, Nepal, Bhutan",
                "languages": {
                    "burmese": {
                        "name": "Burmese",
                        "native_name": "မြန်မာစာ",
                        "iso639_3": "mya",
                        "speakers": 33_000_000,
                        "countries": ["Myanmar"],
                        "status": "living",
                        "writing_system": ["Myanmar"],
                        "official_status": "official"
                    },
                    "tibetan": {
                        "name": "Tibetan",
                        "native_name": "བོད་སྐད",
                        "iso639_3": "bod",
                        "speakers": 6_000_000,
                        "countries": ["China", "India", "Nepal", "Bhutan"],
                        "status": "living",
                        "writing_system": ["Tibetan"]
                    }
                }
            }
        }
    },

    "indo-european": {
        "name": "Indo-European",
        "continent": "Global",
        "total_speakers": 3_200_000_000,
        "total_languages": 449,
        "description": "Most widespread language family globally",
        "geographic_distribution": "Europe, Asia, Americas, Oceania",
        "characteristics": [
            "Inflectional morphology",
            "Ablaut patterns",
            "Rich case systems (historically)",
            "Complex verb conjugations"
        ],
        "subfamilies": {
            "germanic": {
                "name": "Germanic",
                "speakers": 515_000_000,
                "languages": 58,
                "description": "North and West European languages",
                "geographic_area": "Northern and Western Europe, North America",
                "languages": {
                    "english": {
                        "name": "English",
                        "native_name": "English",
                        "iso639_3": "eng",
                        "speakers": 1_500_000_000,
                        "countries": ["United States", "United Kingdom", "Canada", "Australia", "New Zealand"],
                        "status": "living",
                        "writing_system": ["Latin"],
                        "official_status": "official"
                    },
                    "german": {
                        "name": "German",
                        "native_name": "Deutsch",
                        "iso639_3": "deu",
                        "speakers": 100_000_000,
                        "countries": ["Germany", "Austria", "Switzerland"],
                        "status": "living",
                        "writing_system": ["Latin"],
                        "official_status": "official"
                    },
                    "dutch": {
                        "name": "Dutch",
                        "native_name": "Nederlands",
                        "iso639_3": "nld",
                        "speakers": 24_000_000,
                        "countries": ["Netherlands", "Belgium"],
                        "status": "living",
                        "writing_system": ["Latin"],
                        "official_status": "official"
                    }
                }
            },
            "romance": {
                "name": "Romance",
                "speakers": 1_000_000_000,
                "languages": 44,
                "description": "Languages descended from Latin",
                "geographic_area": "Southern Europe, Latin America",
                "languages": {
                    "spanish": {
                        "name": "Spanish",
                        "native_name": "Español",
                        "iso639_3": "spa",
                        "speakers": 500_000_000,
                        "countries": ["Spain", "Mexico", "Colombia", "Argentina", "Peru"],
                        "status": "living",
                        "writing_system": ["Latin"],
                        "official_status": "official"
                    },
                    "portuguese": {
                        "name": "Portuguese",
                        "native_name": "Português",
                        "iso639_3": "por",
                        "speakers": 280_000_000,
                        "countries": ["Brazil", "Portugal", "Angola", "Mozambique"],
                        "status": "living",
                        "writing_system": ["Latin"],
                        "official_status": "official"
                    },
                    "french": {
                        "name": "French",
                        "native_name": "Français",
                        "iso639_3": "fra",
                        "speakers": 280_000_000,
                        "countries": ["France", "Canada", "Belgium", "Switzerland", "Senegal"],
                        "status": "living",
                        "writing_system": ["Latin"],
                        "official_status": "official"
                    },
                    "italian": {
                        "name": "Italian",
                        "native_name": "Italiano",
                        "iso639_3": "ita",
                        "speakers": 65_000_000,
                        "countries": ["Italy", "Switzerland", "San Marino", "Vatican City"],
                        "status": "living",
                        "writing_system": ["Latin"],
                        "official_status": "official"
                    }
                }
            },
            "indo-iranian": {
                "name": "Indo-Iranian",
                "speakers": 1_500_000_000,
                "languages": 213,
                "description": "Languages of India, Iran, and Central Asia",
                "geographic_area": "South Asia, Iran, Central Asia",
                "languages": {
                    "hindi": {
                        "name": "Hindi",
                        "native_name": "हिन्दी",
                        "iso639_3": "hin",
                        "speakers": 600_000_000,
                        "countries": ["India"],
                        "status": "living",
                        "writing_system": ["Devanagari"],
                        "official_status": "official"
                    },
                    "bengali": {
                        "name": "Bengali",
                        "native_name": "বাংলা",
                        "iso639_3": "ben",
                        "speakers": 265_000_000,
                        "countries": ["Bangladesh", "India"],
                        "status": "living",
                        "writing_system": ["Bengali"],
                        "official_status": "official"
                    },
                    "persian": {
                        "name": "Persian",
                        "native_name": "فارسی",
                        "iso639_3": "fas",
                        "speakers": 70_000_000,
                        "countries": ["Iran", "Afghanistan", "Tajikistan"],
                        "status": "living",
                        "writing_system": ["Arabic"],
                        "official_status": "official"
                    }
                }
            },
            "slavic": {
                "name": "Slavic",
                "speakers": 315_000_000,
                "languages": 20,
                "description": "Eastern European languages",
                "geographic_area": "Eastern Europe, Balkans",
                "languages": {
                    "russian": {
                        "name": "Russian",
                        "native_name": "Русский",
                        "iso639_3": "rus",
                        "speakers": 258_000_000,
                        "countries": ["Russia", "Belarus", "Kazakhstan", "Kyrgyzstan"],
                        "status": "living",
                        "writing_system": ["Cyrillic"],
                        "official_status": "official"
                    },
                    "polish": {
                        "name": "Polish",
                        "native_name": "Polski",
                        "iso639_3": "pol",
                        "speakers": 45_000_000,
                        "countries": ["Poland"],
                        "status": "living",
                        "writing_system": ["Latin"],
                        "official_status": "official"
                    }
                }
            }
        }
    },

    "austronesian": {
        "name": "Austronesian",
        "continent": "Pacific",
        "total_speakers": 380_000_000,
        "total_languages": 1268,
        "description": "Oceanic and Southeast Asian island languages",
        "geographic_distribution": "Southeast Asia, Pacific Islands, Madagascar",
        "characteristics": [
            "Verb-initial word order",
            "Complex voice systems",
            "Reduplication",
            "No grammatical gender"
        ],
        "subfamilies": {
            "malayo-polynesian": {
                "name": "Malayo-Polynesian",
                "speakers": 370_000_000,
                "languages": 1200,
                "description": "Most Austronesian languages",
                "geographic_area": "Southeast Asia, Pacific",
                "languages": {
                    "indonesian": {
                        "name": "Indonesian",
                        "native_name": "Bahasa Indonesia",
                        "iso639_3": "ind",
                        "speakers": 230_000_000,
                        "countries": ["Indonesia"],
                        "status": "living",
                        "writing_system": ["Latin"],
                        "official_status": "official"
                    },
                    "malay": {
                        "name": "Malay",
                        "native_name": "Bahasa Melayu",
                        "iso639_3": "msa",
                        "speakers": 33_000_000,
                        "countries": ["Malaysia", "Brunei", "Singapore"],
                        "status": "living",
                        "writing_system": ["Latin"],
                        "official_status": "official"
                    },
                    "tagalog": {
                        "name": "Tagalog",
                        "native_name": "Tagalog",
                        "iso639_3": "tgl",
                        "speakers": 28_000_000,
                        "countries": ["Philippines"],
                        "status": "living",
                        "writing_system": ["Latin"],
                        "official_status": "official"
                    },
                    "javanese": {
                        "name": "Javanese",
                        "native_name": "ꦧꦱꦗꦮ",
                        "iso639_3": "jav",
                        "speakers": 68_000_000,
                        "countries": ["Indonesia"],
                        "status": "living",
                        "writing_system": ["Javanese", "Latin"]
                    }
                }
            }
        }
    },

    "japonic": {
        "name": "Japonic",
        "continent": "Asia",
        "total_speakers": 128_000_000,
        "total_languages": 16,
        "description": "Japanese and Ryukyuan languages",
        "geographic_distribution": "Japan, Ryukyu Islands",
        "characteristics": [
            "SOV word order",
            "Agglutinative morphology",
            "Complex honorific system",
            "Pitch accent"
        ],
        "subfamilies": {
            "japanese": {
                "name": "Japanese",
                "speakers": 125_000_000,
                "languages": 1,
                "description": "Standard Japanese",
                "geographic_area": "Japan",
                "languages": {
                    "japanese": {
                        "name": "Japanese",
                        "native_name": "日本語",
                        "iso639_3": "jpn",
                        "speakers": 125_000_000,
                        "countries": ["Japan"],
                        "status": "living",
                        "writing_system": ["Hiragana", "Katakana", "Kanji"],
                        "official_status": "official"
                    }
                }
            },
            "ryukyuan": {
                "name": "Ryukyuan",
                "speakers": 3_000_000,
                "languages": 15,
                "description": "Languages of Ryukyu Islands",
                "geographic_area": "Okinawa, Ryukyu Islands",
                "languages": {
                    "okinawan": {
                        "name": "Okinawan",
                        "native_name": "うちなーぐち",
                        "iso639_3": "ryu",
                        "speakers": 10_000,
                        "countries": ["Japan"],
                        "status": "severely_endangered",
                        "writing_system": ["Hiragana", "Katakana"]
                    }
                }
            }
        }
    },

    "koreanic": {
        "name": "Koreanic",
        "continent": "Asia",
        "total_speakers": 77_000_000,
        "total_languages": 2,
        "description": "Korean and Jeju languages",
        "geographic_distribution": "Korean Peninsula, Jeju Island",
        "characteristics": [
            "SOV word order",
            "Agglutinative morphology",
            "Complex honorific system",
            "No grammatical gender"
        ],
        "subfamilies": {
            "korean": {
                "name": "Korean",
                "speakers": 77_000_000,
                "languages": 2,
                "description": "Korean languages",
                "geographic_area": "South Korea, North Korea",
                "languages": {
                    "korean": {
                        "name": "Korean",
                        "native_name": "한국어",
                        "iso639_3": "kor",
                        "speakers": 77_000_000,
                        "countries": ["South Korea", "North Korea"],
                        "status": "living",
                        "writing_system": ["Hangul"],
                        "official_status": "official"
                    },
                    "jeju": {
                        "name": "Jeju",
                        "native_name": "제주어",
                        "iso639_3": "jje",
                        "speakers": 10_000,
                        "countries": ["South Korea"],
                        "status": "critically_endangered",
                        "writing_system": ["Hangul"]
                    }
                }
            }
        },
        "turkic": {
            "name": "Turkic",
            "continent": "Asia",
            "total_speakers": 200_000_000,
            "total_languages": 35,
            "description": "Family of languages spoken from Eastern Europe to Central Asia",
            "geographic_distribution": "Turkey, Central Asia, Eastern Europe",
            "characteristics": [
                "Agglutinative morphology",
                "Vowel harmony",
                "SOV word order"
            ],
            "subfamilies": {
                "oghuz": {
                    "name": "Oghuz",
                    "speakers": 150_000_000,
                    "languages": 8,
                    "description": "Western Turkic languages",
                    "geographic_area": "Turkey, Azerbaijan, Turkmenistan",
                    "languages": {
                        "turkish": {
                            "name": "Turkish",
                            "native_name": "Türkçe",
                            "iso639_3": "tur",
                            "speakers": 88_000_000,
                            "countries": ["Turkey", "Cyprus", "Bulgaria"],
                            "status": "living",
                            "writing_system": ["Latin"],
                            "dialects": ["Istanbul Turkish", "Anatolian"]
                        },
                        "azerbaijani": {
                            "name": "Azerbaijani",
                            "native_name": "Azərbaycan dili",
                            "iso639_3": "aze",
                            "speakers": 23_000_000,
                            "countries": ["Azerbaijan", "Iran"],
                            "status": "living",
                            "writing_system": ["Latin", "Cyrillic", "Arabic"]
                        }
                    }
                },
                "kipchak": {
                    "name": "Kipchak",
                    "speakers": 35_000_000,
                    "languages": 12,
                    "description": "Central Turkic languages",
                    "geographic_area": "Kazakhstan, Kyrgyzstan, Uzbekistan",
                    "languages": {
                        "kazakh": {
                            "name": "Kazakh",
                            "native_name": "Қазақ тілі",
                            "iso639_3": "kaz",
                            "speakers": 13_000_000,
                            "countries": ["Kazakhstan", "China", "Mongolia"],
                            "status": "living",
                            "writing_system": ["Cyrillic", "Latin"]
                        },
                        "kyrgyz": {
                            "name": "Kyrgyz",
                            "native_name": "Кыргыз тили",
                            "iso639_3": "kir",
                            "speakers": 4_300_000,
                            "countries": ["Kyrgyzstan", "China"],
                            "status": "living",
                            "writing_system": ["Cyrillic", "Arabic"]
                        }
                    }
                }
            }
        },
        "dravidian": {
            "name": "Dravidian",
            "continent": "Asia",
            "total_speakers": 250_000_000,
            "total_languages": 80,
            "description": "Languages of South India and parts of Central India",
            "geographic_distribution": "South India, Sri Lanka",
            "characteristics": [
                "Agglutinative morphology",
                "Retroflex consonants",
                "Complex verbal systems"
            ],
            "subfamilies": {
                "south-dravidian": {
                    "name": "South Dravidian",
                    "speakers": 200_000_000,
                    "languages": 20,
                    "description": "Major Dravidian languages of South India",
                    "geographic_area": "Tamil Nadu, Kerala, Karnataka, Andhra Pradesh",
                    "languages": {
                        "tamil": {
                            "name": "Tamil",
                            "native_name": "தமிழ்",
                            "iso639_3": "tam",
                            "speakers": 77_000_000,
                            "countries": ["India", "Sri Lanka", "Singapore", "Malaysia"],
                            "status": "living",
                            "writing_system": ["Tamil"],
                            "dialects": ["Standard Tamil", "Sri Lankan Tamil"]
                        },
                        "telugu": {
                            "name": "Telugu",
                            "native_name": "తెలుగు",
                            "iso639_3": "tel",
                            "speakers": 82_000_000,
                            "countries": ["India"],
                            "status": "living",
                            "writing_system": ["Telugu"]
                        },
                        "kannada": {
                            "name": "Kannada",
                            "native_name": "ಕನ್ನಡ",
                            "iso639_3": "kan",
                            "speakers": 44_000_000,
                            "countries": ["India"],
                            "status": "living",
                            "writing_system": ["Kannada"]
                        },
                        "malayalam": {
                            "name": "Malayalam",
                            "native_name": "മലയാളം",
                            "iso639_3": "mal",
                            "speakers": 35_000_000,
                            "countries": ["India"],
                            "status": "living",
                            "writing_system": ["Malayalam"]
                        }
                    }
                }
            }
        },
        "uralic": {
            "name": "Uralic",
            "continent": "Europe",
            "total_speakers": 25_000_000,
            "total_languages": 40,
            "description": "Languages of Northern Europe and western Siberia",
            "geographic_distribution": "Finland, Hungary, Estonia, Russia",
            "characteristics": [
                "Agglutinative morphology",
                "Extensive case systems",
                "No grammatical gender"
            ],
            "subfamilies": {
                "finno-ugric": {
                    "name": "Finno-Ugric",
                    "speakers": 24_000_000,
                    "languages": 25,
                    "description": "Major branch of Uralic languages",
                    "geographic_area": "Northern Europe, Hungary",
                    "languages": {
                        "finnish": {
                            "name": "Finnish",
                            "native_name": "Suomi",
                            "iso639_3": "fin",
                            "speakers": 5_400_000,
                            "countries": ["Finland", "Sweden", "Russia"],
                            "status": "living",
                            "writing_system": ["Latin"]
                        },
                        "hungarian": {
                            "name": "Hungarian",
                            "native_name": "Magyar",
                            "iso639_3": "hun",
                            "speakers": 13_000_000,
                            "countries": ["Hungary", "Romania", "Slovakia"],
                            "status": "living",
                            "writing_system": ["Latin"]
                        },
                        "estonian": {
                            "name": "Estonian",
                            "native_name": "Eesti keel",
                            "iso639_3": "est",
                            "speakers": 1_100_000,
                            "countries": ["Estonia", "Latvia", "Russia"],
                            "status": "living",
                            "writing_system": ["Latin"]
                        }
                    }
                }
            }
        },
        "tai-kadai": {
            "name": "Tai-Kadai",
            "continent": "Asia",
            "total_speakers": 93_000_000,
            "total_languages": 95,
            "description": "Languages of Southeast Asia, primarily Thailand and Laos",
            "geographic_distribution": "Thailand, Laos, Southern China, Vietnam",
            "characteristics": [
                "Tonal languages",
                "Monosyllabic tendencies",
                "SVO word order"
            ],
            "subfamilies": {
                "tai": {
                    "name": "Tai",
                    "speakers": 85_000_000,
                    "languages": 76,
                    "description": "Main branch including Thai and Lao",
                    "geographic_area": "Thailand, Laos, Myanmar, China",
                    "languages": {
                        "thai": {
                            "name": "Thai",
                            "native_name": "ภาษาไทย",
                            "iso639_3": "tha",
                            "speakers": 60_000_000,
                            "countries": ["Thailand"],
                            "status": "living",
                            "writing_system": ["Thai"],
                            "dialects": ["Central Thai", "Northern Thai", "Southern Thai"]
                        },
                        "lao": {
                            "name": "Lao",
                            "native_name": "ພາສາລາວ",
                            "iso639_3": "lao",
                            "speakers": 7_000_000,
                            "countries": ["Laos", "Thailand"],
                            "status": "living",
                            "writing_system": ["Lao"]
                        }
                    }
                }
            }
        },
        "quechuan": {
            "name": "Quechuan",
            "continent": "South America",
            "total_speakers": 10_000_000,
            "total_languages": 46,
            "description": "Indigenous languages of the Andes",
            "geographic_distribution": "Peru, Bolivia, Ecuador, Colombia, Argentina",
            "characteristics": [
                "Agglutinative morphology",
                "SOV word order",
                "Evidentiality system"
            ],
            "subfamilies": {
                "central-quechua": {
                    "name": "Central Quechua",
                    "speakers": 8_000_000,
                    "languages": 15,
                    "description": "Main Quechua languages",
                    "geographic_area": "Peru, Bolivia, Ecuador",
                    "languages": {
                        "southern-quechua": {
                            "name": "Southern Quechua",
                            "native_name": "Runasimi",
                            "iso639_3": "que",
                            "speakers": 6_500_000,
                            "countries": ["Peru", "Bolivia", "Argentina"],
                            "status": "living",
                            "writing_system": ["Latin"]
                        },
                        "cusco-quechua": {
                            "name": "Cusco Quechua",
                            "native_name": "Qheswa",
                            "iso639_3": "quz",
                            "speakers": 1_500_000,
                            "countries": ["Peru"],
                            "status": "living",
                            "writing_system": ["Latin"]
                        }
                    }
                }
            }
        },
        "mayan": {
            "name": "Mayan",
            "continent": "North America",
            "total_speakers": 6_000_000,
            "total_languages": 30,
            "description": "Indigenous languages of Mesoamerica",
            "geographic_distribution": "Guatemala, Mexico, Belize, Honduras",
            "characteristics": [
                "Ergative-absolutive alignment",
                "Complex verbal morphology",
                "Hieroglyphic writing system (historical)"
            ],
            "subfamilies": {
                "greater-mayan": {
                    "name": "Greater Mayan",
                    "speakers": 6_000_000,
                    "languages": 30,
                    "description": "All modern Mayan languages",
                    "geographic_area": "Guatemala, Southern Mexico, Belize",
                    "languages": {
                        "kiche": {
                            "name": "K'iche'",
                            "native_name": "K'iche'",
                            "iso639_3": "quc",
                            "speakers": 2_300_000,
                            "countries": ["Guatemala"],
                            "status": "living",
                            "writing_system": ["Latin"]
                        },
                        "yucatec": {
                            "name": "Yucatec Maya",
                            "native_name": "Maaya t'aan",
                            "iso639_3": "yua",
                            "speakers": 800_000,
                            "countries": ["Mexico", "Belize"],
                            "status": "living",
                            "writing_system": ["Latin"]
                        }
                    }
                }
            }
        }
    }
}

# Additional language families to add
ADDITIONAL_FAMILIES = {
    "turkic": {
        "name": "Turkic",
        "continent": "Asia",
        "total_speakers": 200_000_000,
        "total_languages": 35,
        "description": "Family of languages spoken from Eastern Europe to Central Asia",
        "geographic_distribution": "Turkey, Central Asia, Eastern Europe",
        "characteristics": [
            "Agglutinative morphology",
            "Vowel harmony",
            "SOV word order"
        ],
        "subfamilies": {
            "oghuz": {
                "name": "Oghuz",
                "speakers": 150_000_000,
                "languages": 8,
                "description": "Western Turkic languages",
                "geographic_area": "Turkey, Azerbaijan, Turkmenistan",
                "languages": {
                    "turkish": {
                        "name": "Turkish",
                        "native_name": "Türkçe",
                        "iso639_3": "tur",
                        "speakers": 88_000_000,
                        "countries": ["Turkey", "Cyprus", "Bulgaria"],
                        "status": "living",
                        "writing_system": ["Latin"],
                        "dialects": ["Istanbul Turkish", "Anatolian"]
                    },
                    "azerbaijani": {
                        "name": "Azerbaijani",
                        "native_name": "Azərbaycan dili",
                        "iso639_3": "aze",
                        "speakers": 23_000_000,
                        "countries": ["Azerbaijan", "Iran"],
                        "status": "living",
                        "writing_system": ["Latin", "Cyrillic", "Arabic"]
                    }
                }
            }
        }
    },
    "uralic": {
        "name": "Uralic",
        "continent": "Europe",
        "total_speakers": 25_000_000,
        "total_languages": 40,
        "description": "Languages of Northern Europe and western Siberia",
        "geographic_distribution": "Finland, Hungary, Estonia, Russia",
        "characteristics": [
            "Agglutinative morphology",
            "Extensive case systems",
            "No grammatical gender"
        ],
        "subfamilies": {
            "finno-ugric": {
                "name": "Finno-Ugric",
                "speakers": 24_000_000,
                "languages": 25,
                "description": "Major branch of Uralic languages",
                "geographic_area": "Northern Europe, Hungary",
                "languages": {
                    "finnish": {
                        "name": "Finnish",
                        "native_name": "Suomi",
                        "iso639_3": "fin",
                        "speakers": 5_400_000,
                        "countries": ["Finland", "Sweden", "Russia"],
                        "status": "living",
                        "writing_system": ["Latin"]
                    },
                    "hungarian": {
                        "name": "Hungarian",
                        "native_name": "Magyar",
                        "iso639_3": "hun",
                        "speakers": 13_000_000,
                        "countries": ["Hungary", "Romania", "Slovakia"],
                        "status": "living",
                        "writing_system": ["Latin"]
                    }
                }
            }
        }
    },
    "tai-kadai": {
        "name": "Tai-Kadai",
        "continent": "Asia",
        "total_speakers": 93_000_000,
        "total_languages": 95,
        "description": "Languages of Southeast Asia, primarily Thailand and Laos",
        "geographic_distribution": "Thailand, Laos, Southern China, Vietnam",
        "characteristics": [
            "Tonal languages",
            "Monosyllabic tendencies",
            "SVO word order"
        ],
        "subfamilies": {
            "tai": {
                "name": "Tai",
                "speakers": 85_000_000,
                "languages": 76,
                "description": "Main branch including Thai and Lao",
                "geographic_area": "Thailand, Laos, Myanmar, China",
                "languages": {
                    "thai": {
                        "name": "Thai",
                        "native_name": "ภาษาไทย",
                        "iso639_3": "tha",
                        "speakers": 60_000_000,
                        "countries": ["Thailand"],
                        "status": "living",
                        "writing_system": ["Thai"],
                        "dialects": ["Central Thai", "Northern Thai", "Southern Thai"]
                    },
                    "lao": {
                        "name": "Lao",
                        "native_name": "ພາສາລາວ",
                        "iso639_3": "lao",
                        "speakers": 7_000_000,
                        "countries": ["Laos", "Thailand"],
                        "status": "living",
                        "writing_system": ["Lao"]
                    }
                }
            }
        }
    }
}

class LanguageFamilyPopulator:
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.db = None

    async def connect_database(self):
        """Connect to MongoDB database"""
        try:
            self.client = AsyncIOMotorClient(self.settings.MONGODB_URL)
            self.db = self.client[self.settings.DATABASE_NAME]

            # Test connection
            await self.db.command("ping")
            logger.info("Successfully connected to MongoDB")

        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def close_database(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")

    async def clear_existing_data(self):
        """Clear existing language family and language data"""
        try:
            # Clear collections
            await self.db.language_families.delete_many({})
            await self.db.language_subfamilies.delete_many({})
            await self.db.languages.delete_many({})

            logger.info("Cleared existing language data")

        except Exception as e:
            logger.error(f"Error clearing data: {e}")
            raise

    async def populate_language_families(self):
        """Populate language families"""
        try:
            family_docs = []

            # Merge main data with additional families
            all_families = {**LANGUAGE_FAMILIES_DATA, **ADDITIONAL_FAMILIES}
            logger.info(f"Processing {len(all_families)} language families")

            for family_key, family_data in all_families.items():
                family_doc = {
                    "_id": ObjectId(),
                    "name": family_key,
                    "display_name": family_data["name"],
                    "description": family_data["description"],
                    "geographic_region": [family_data["continent"]],
                    "subfamilies": list(family_data["subfamilies"].keys()),
                    "shared_features": {
                        "characteristics": family_data["characteristics"],
                        "geographic_distribution": family_data["geographic_distribution"]
                    },
                    "speaker_count_estimate": family_data["total_speakers"],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                family_docs.append(family_doc)

            # Insert all families
            result = await self.db.language_families.insert_many(family_docs)
            logger.info(f"Inserted {len(result.inserted_ids)} language families")

            return {family_key: family_data["_id"] for family_key, family_data in zip(all_families.keys(), family_docs)}

        except Exception as e:
            logger.error(f"Error populating language families: {e}")
            raise

    async def populate_subfamilies_and_languages(self, family_ids: Dict[str, ObjectId]):
        """Populate subfamilies and languages"""
        try:
            subfamily_docs = []
            language_docs = []
            subfamily_ids = {}

            # Merge main data with additional families
            all_families = {**LANGUAGE_FAMILIES_DATA, **ADDITIONAL_FAMILIES}
            logger.info(f"Processing {len(all_families)} language families")

            for family_key, family_data in all_families.items():
                family_id = family_ids[family_key]

                for subfamily_key, subfamily_data in family_data["subfamilies"].items():
                    # Create subfamily document
                    subfamily_doc = {
                        "_id": ObjectId(),
                        "family_id": family_id,
                        "name": subfamily_key,
                        "display_name": subfamily_data["name"],
                        "description": subfamily_data["description"],
                        "geographic_region": [subfamily_data["geographic_area"]],
                        "languages": list(subfamily_data["languages"].keys()),
                        "shared_features": {
                            "speakers": subfamily_data["speakers"],
                            "total_languages": subfamily_data["languages"]
                        },
                        "transfer_learning_efficiency": {},
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    subfamily_docs.append(subfamily_doc)
                    subfamily_ids[f"{family_key}_{subfamily_key}"] = subfamily_doc["_id"]

                    # Create language documents for this subfamily
                    for lang_key, lang_data in subfamily_data["languages"].items():
                        language_doc = {
                            "_id": ObjectId(),
                            "subfamily_id": subfamily_doc["_id"],
                            "code": lang_data["iso639_3"],
                            "name": lang_data["name"],
                            "native_name": lang_data["native_name"],
                            "alternative_names": [],
                            "countries": lang_data["countries"],
                            "regions": [],
                            "speaker_count": lang_data["speakers"],
                            "total_speakers": lang_data["speakers"],
                            "linguistic_features": {},
                            "phonetic_inventory": {},
                            "tonal_system": None,
                            "writing_systems": lang_data["writing_system"],
                            "cultural_context": {},
                            "dialects": lang_data.get("dialects", []),
                            "data_tier": "tier-3",
                            "voice_support_level": "basic",
                            "training_data_availability": {},
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow(),
                            "last_contribution": None,
                            "active_contributors": 0
                        }
                        language_docs.append(language_doc)

            # Insert subfamilies
            if subfamily_docs:
                result = await self.db.language_subfamilies.insert_many(subfamily_docs)
                logger.info(f"Inserted {len(result.inserted_ids)} language subfamilies")

            # Insert languages
            if language_docs:
                result = await self.db.languages.insert_many(language_docs)
                logger.info(f"Inserted {len(result.inserted_ids)} languages")

            return subfamily_ids

        except Exception as e:
            logger.error(f"Error populating subfamilies and languages: {e}")
            raise

    async def create_indexes(self):
        """Create database indexes for performance"""
        try:
            indexes_to_create = [
                # Language families indexes
                (self.db.language_families, "name", {"unique": True}),
                (self.db.language_families, "geographic_region", {}),
                (self.db.language_families, "speaker_count_estimate", {}),

                # Language subfamilies indexes
                (self.db.language_subfamilies, "family_id", {}),
                (self.db.language_subfamilies, "name", {}),
                (self.db.language_subfamilies, [("family_id", 1), ("name", 1)], {"unique": True}),

                # Languages indexes
                (self.db.languages, "subfamily_id", {}),
                (self.db.languages, "code", {"unique": True}),
                (self.db.languages, "speaker_count", {}),
                (self.db.languages, "countries", {}),
                (self.db.languages, "name", {}),
                (self.db.languages, "data_tier", {}),
            ]

            created_count = 0
            for collection, field, options in indexes_to_create:
                try:
                    await collection.create_index(field, **options)
                    created_count += 1
                except Exception as e:
                    if "already exists" in str(e) or "IndexKeySpecsConflict" in str(e):
                        logger.debug(f"Index on {field} already exists, skipping")
                    else:
                        logger.warning(f"Failed to create index on {field}: {e}")

            logger.info(f"Created {created_count} new database indexes")

        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            raise

    async def generate_summary_statistics(self):
        """Generate summary statistics"""
        try:
            # Count documents
            family_count = await self.db.language_families.count_documents({})
            subfamily_count = await self.db.language_subfamilies.count_documents({})
            language_count = await self.db.languages.count_documents({})

            # Calculate total speakers
            pipeline = [
                {"$group": {"_id": None, "total_speakers": {"$sum": "$speaker_count_estimate"}}}
            ]
            result = await self.db.language_families.aggregate(pipeline).to_list(1)
            total_speakers = result[0]["total_speakers"] if result else 0

            # African language statistics
            african_families = await self.db.language_families.count_documents({
                "geographic_region": {"$regex": "Africa", "$options": "i"}
            })

            # Most spoken languages
            top_languages = await self.db.languages.find(
                {}, {"name": 1, "speaker_count": 1, "countries": 1}
            ).sort("speaker_count", -1).limit(10).to_list(10)

            summary = {
                "total_families": family_count,
                "total_subfamilies": subfamily_count,
                "total_languages": language_count,
                "total_speakers": total_speakers,
                "african_families": african_families,
                "top_languages": [
                    {
                        "name": lang["name"],
                        "speakers": lang["speaker_count"],
                        "countries": lang["countries"]
                    }
                    for lang in top_languages
                ]
            }

            logger.info("Database Population Summary:")
            logger.info(f"  Language Families: {summary['total_families']}")
            logger.info(f"  Language Subfamilies: {summary['total_subfamilies']}")
            logger.info(f"  Individual Languages: {summary['total_languages']}")
            logger.info(f"  Total Speakers: {summary['total_speakers']:,}")
            logger.info(f"  African Families: {summary['african_families']}")
            logger.info("  Top 10 Languages by Speakers:")
            for lang in summary["top_languages"]:
                logger.info(f"    {lang['name']}: {lang['speakers']:,} speakers")

            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            raise

    async def populate_all(self):
        """Main population function"""
        try:
            logger.info("Starting language family database population...")

            # Connect to database
            await self.connect_database()

            # Clear existing data
            await self.clear_existing_data()

            # Populate language families
            family_ids = await self.populate_language_families()

            # Populate subfamilies and languages
            await self.populate_subfamilies_and_languages(family_ids)

            # Create indexes
            await self.create_indexes()

            # Generate summary
            summary = await self.generate_summary_statistics()

            logger.info("Language family database population completed successfully!")
            return summary

        except Exception as e:
            logger.error(f"Population failed: {e}")
            raise
        finally:
            await self.close_database()

async def main():
    """Main function"""
    try:
        populator = LanguageFamilyPopulator()
        summary = await populator.populate_all()

        print("\n" + "="*60)
        print("LANGUAGE FAMILY DATABASE POPULATION COMPLETE")
        print("="*60)
        print(f"✅ Language Families: {summary['total_families']}")
        print(f"✅ Language Subfamilies: {summary['total_subfamilies']}")
        print(f"✅ Individual Languages: {summary['total_languages']}")
        print(f"✅ Total Speakers: {summary['total_speakers']:,}")
        print(f"✅ African Families: {summary['african_families']}")
        print("\n🌍 Ready to focus on African language families!")

    except Exception as e:
        logger.error(f"Population script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())