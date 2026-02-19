#!/usr/bin/env python3
"""
African Language Families Enhancement Data
Comprehensive data for the African Language Community Platform
"""

# Enhanced African language families with detailed linguistic and cultural data
AFRICAN_LANGUAGE_ENHANCEMENTS = {
    "niger-congo": {
        "linguistic_features": {
            "tonal_system": {
                "is_tonal": True,
                "tone_levels": ["High", "Low", "Mid", "Rising", "Falling"],
                "tone_complexity": "complex",
                "description": "Most Niger-Congo languages are tonal with 2-5 tone levels"
            },
            "phonetic_complexity": {
                "consonant_inventory_size": "medium",
                "vowel_system": "7-10 vowels typical",
                "syllable_structure": "mainly open syllables (CV)",
                "distinctive_features": ["nasal harmony", "ATR vowel harmony", "labial-velar consonants"]
            },
            "morphological_features": {
                "word_order": "SVO predominant",
                "noun_class_system": True,
                "verb_aspect": "rich aspectual marking",
                "agglutination": "moderate"
            }
        },
        "cultural_context": {
            "oral_traditions": [
                "Griots tradition (West Africa)",
                "Praise poetry",
                "Folktales and proverbs",
                "Historical narratives",
                "Religious chants"
            ],
            "modern_usage": {
                "education": "Growing use in primary education",
                "media": "Radio, television, and digital content",
                "literature": "Rich contemporary literature",
                "official_status": "Several are national languages"
            },
            "cultural_significance": {
                "identity_marker": "Strong linguistic identity",
                "community_bonding": "Central to community life",
                "ceremonial_use": "Traditional ceremonies and rituals"
            }
        },
        "ai_learning_data": {
            "data_availability": {
                "tier_1_languages": ["Swahili", "Yoruba", "Zulu"],
                "tier_2_languages": ["Twi", "Shona", "Kikuyu", "Xhosa"],
                "tier_3_languages": ["Fante", "Ga", "Bambara", "Mandinka"]
            },
            "training_challenges": [
                "Tonal marking in text",
                "Dialectal variation",
                "Limited written corpora",
                "Code-switching with colonial languages"
            ],
            "voice_features": {
                "tonal_recognition": "Critical for accuracy",
                "nasalization": "Important feature",
                "click_adaptation": "In contact languages like Xhosa, Zulu"
            }
        },
        "enhanced_languages": {
            "igbo": {
                "name": "Igbo",
                "native_name": "Asụsụ Igbo",
                "iso639_3": "ibo",
                "speakers": 27_000_000,
                "countries": ["Nigeria"],
                "status": "living",
                "writing_system": ["Latin"],
                "tonal_system": {
                    "type": "terraced",
                    "levels": ["High", "Low", "Downstep"],
                    "contours": ["Rising", "Falling"]
                },
                "dialects": ["Onitsha", "Owerri", "Umuahia", "Afikpo"],
                "cultural_features": {
                    "oral_literature": "Rich proverb tradition",
                    "music_integration": "Talking drums mirror tones",
                    "ceremonial_use": "Traditional titles and ceremonies"
                },
                "endangerment_status": "stable",
                "revitalization_efforts": [
                    "Igbo Language Advocacy",
                    "Digital learning platforms",
                    "University programs"
                ]
            },
            "akan": {
                "name": "Akan",
                "native_name": "Akan kasa",
                "iso639_3": "aka",
                "speakers": 12_000_000,
                "countries": ["Ghana", "Ivory Coast"],
                "status": "living",
                "writing_system": ["Latin"],
                "tonal_system": {
                    "type": "level",
                    "levels": ["High", "Mid", "Low"],
                    "contours": ["High-Low", "Low-High"]
                },
                "dialects": ["Asante", "Fante", "Akuapem", "Akyem"],
                "cultural_features": {
                    "oral_literature": "Anansi stories",
                    "music_integration": "Adinkra symbols in written form",
                    "ceremonial_use": "Royal court language"
                },
                "endangerment_status": "stable",
                "revitalization_efforts": [
                    "Ghana education policy",
                    "Cultural festivals",
                    "Media production"
                ]
            }
        }
    },
    "afroasiatic": {
        "linguistic_features": {
            "tonal_system": {
                "is_tonal": False,
                "tone_levels": [],
                "tone_complexity": "none",
                "description": "Generally non-tonal except some Chadic languages"
            },
            "phonetic_complexity": {
                "consonant_inventory_size": "large",
                "vowel_system": "3-vowel root system",
                "syllable_structure": "CVC roots predominant",
                "distinctive_features": ["pharyngeal consonants", "ejectives", "emphatic consonants"]
            },
            "morphological_features": {
                "word_order": "VSO/SVO",
                "root_pattern": "triconsonantal roots",
                "verb_aspect": "perfect/imperfect",
                "agglutination": "templatic morphology"
            }
        },
        "cultural_context": {
            "oral_traditions": [
                "Islamic scholarly tradition",
                "Berber oral poetry",
                "Ethiopian religious chants",
                "Nomadic storytelling",
                "Historical chronicles"
            ],
            "modern_usage": {
                "education": "Widely used in education",
                "media": "Extensive media presence",
                "literature": "Ancient and modern literature",
                "official_status": "Many are official languages"
            },
            "cultural_significance": {
                "religious_importance": "Languages of major religions",
                "trade_languages": "Historical trade lingua francas",
                "scholarly_tradition": "Scientific and literary tradition"
            }
        },
        "enhanced_languages": {
            "amharic": {
                "name": "Amharic",
                "native_name": "አማርኛ",
                "iso639_3": "amh",
                "speakers": 33_000_000,
                "countries": ["Ethiopia"],
                "status": "living",
                "writing_system": ["Ge'ez"],
                "tonal_system": {
                    "type": "none",
                    "levels": [],
                    "description": "Non-tonal"
                },
                "script_features": {
                    "type": "abugida",
                    "characters": 276,
                    "direction": "left-to-right",
                    "ancient_heritage": "Derived from Ge'ez script"
                },
                "cultural_features": {
                    "oral_literature": "Orthodox Christian literature",
                    "music_integration": "Traditional church music",
                    "ceremonial_use": "Ethiopian Orthodox ceremonies"
                },
                "endangerment_status": "stable",
                "revitalization_efforts": [
                    "Ethiopian national language",
                    "Educational curriculum",
                    "Digital content creation"
                ]
            }
        }
    },
    "nilo-saharan": {
        "linguistic_features": {
            "tonal_system": {
                "is_tonal": True,
                "tone_levels": ["High", "Low", "Mid"],
                "tone_complexity": "complex",
                "description": "All Nilo-Saharan languages are tonal"
            },
            "phonetic_complexity": {
                "consonant_inventory_size": "medium",
                "vowel_system": "ATR vowel harmony",
                "syllable_structure": "CV predominant",
                "distinctive_features": ["ATR harmony", "length distinction", "breathy voice"]
            },
            "morphological_features": {
                "word_order": "SOV/SVO",
                "noun_marking": "case marking",
                "verb_aspect": "rich aspectual system",
                "agglutination": "agglutinative"
            }
        },
        "cultural_context": {
            "oral_traditions": [
                "Cattle songs and praise",
                "Migration narratives",
                "Seasonal ceremonies",
                "Age-grade traditions",
                "Oral historical accounts"
            ],
            "modern_usage": {
                "education": "Limited formal education use",
                "media": "Some radio programming",
                "literature": "Growing written literature",
                "official_status": "Some regional recognition"
            }
        },
        "enhanced_languages": {
            "acholi": {
                "name": "Acholi",
                "native_name": "Lwo",
                "iso639_3": "ach",
                "speakers": 1_700_000,
                "countries": ["Uganda", "South Sudan"],
                "status": "living",
                "writing_system": ["Latin"],
                "tonal_system": {
                    "type": "register",
                    "levels": ["High", "Low"],
                    "contours": ["Falling"]
                },
                "cultural_features": {
                    "oral_literature": "Epic narratives",
                    "music_integration": "Traditional dances",
                    "ceremonial_use": "Cleansing ceremonies"
                },
                "endangerment_status": "stable",
                "revitalization_efforts": [
                    "Cultural associations",
                    "Radio programs",
                    "Educational materials"
                ]
            }
        }
    },
    "khoisan": {
        "linguistic_features": {
            "tonal_system": {
                "is_tonal": True,
                "tone_levels": ["High", "Low", "Mid", "Rising", "Falling"],
                "tone_complexity": "highly complex",
                "description": "Complex tonal systems with up to 5 levels"
            },
            "phonetic_complexity": {
                "consonant_inventory_size": "extremely large",
                "click_consonants": {
                    "types": ["dental", "alveolar", "palatal", "lateral"],
                    "count": "9-126 consonants total",
                    "complexity": "world's largest consonant inventories"
                },
                "vowel_system": "complex with nasalization",
                "syllable_structure": "CV/CVC",
                "distinctive_features": ["clicks", "complex nasalization", "pharyngealization"]
            },
            "morphological_features": {
                "word_order": "SOV",
                "noun_marking": "complex case systems",
                "verb_aspect": "rich aspectual marking",
                "agglutination": "agglutinative"
            }
        },
        "cultural_context": {
            "oral_traditions": [
                "San creation myths",
                "Hunting narratives",
                "Trance dance songs",
                "Astronomical knowledge",
                "Medicinal plant traditions"
            ],
            "modern_usage": {
                "education": "Very limited",
                "media": "Minimal presence",
                "literature": "Mainly oral",
                "official_status": "No official status"
            },
            "cultural_significance": {
                "ancient_heritage": "Oldest language families",
                "hunter_gatherer_tradition": "Specialized vocabulary",
                "spiritual_practices": "Trance healing ceremonies"
            }
        },
        "endangerment_data": {
            "threat_level": "critically endangered",
            "causes": [
                "Language shift to dominant languages",
                "Cultural assimilation",
                "Geographic displacement",
                "Economic pressure",
                "Educational policies"
            ],
            "speaker_decline": "Rapid decline in all languages",
            "intergenerational_transmission": "Very limited"
        },
        "revitalization_efforts": {
            "documentation_projects": [
                "DoBeS endangered languages",
                "University research programs",
                "Audio-visual archives",
                "Dictionary projects"
            ],
            "community_initiatives": [
                "Cultural preservation groups",
                "Traditional healing schools",
                "Tourism-based cultural programs",
                "Land rights advocacy"
            ],
            "technological_support": [
                "Digital recording projects",
                "Mobile learning apps",
                "Online dictionaries",
                "Social media presence"
            ]
        },
        "enhanced_languages": {
            "juǀʼhoan": {
                "name": "Juǀ'hoan",
                "native_name": "ǃXun",
                "iso639_3": "ktz",
                "speakers": 8_000,
                "countries": ["Botswana", "Namibia"],
                "status": "severely endangered",
                "writing_system": ["Latin (limited)"],
                "click_system": {
                    "total_consonants": 105,
                    "click_types": 4,
                    "click_accompaniments": ["simple", "nasalized", "glottalized"],
                    "complexity_rank": "among world's most complex"
                },
                "tonal_system": {
                    "type": "register",
                    "levels": ["High", "Low", "Mid"],
                    "contours": ["Rising", "Falling", "Dipping"]
                },
                "cultural_features": {
                    "hunting_traditions": "Specialized hunting vocabulary",
                    "astronomical_knowledge": "Star navigation systems",
                    "medicinal_practices": "Traditional healing terminology"
                },
                "endangerment_status": "severely endangered",
                "threats": [
                    "Youth language shift",
                    "Education in dominant languages",
                    "Economic marginalization"
                ],
                "revitalization_efforts": [
                    "Documentation by linguists",
                    "Cultural tourism programs",
                    "Traditional knowledge preservation"
                ]
            }
        }
    }
}

# Cross-linguistic learning efficiency data for African languages
AFRICAN_LANGUAGE_TRANSFER_LEARNING = {
    "within_family_efficiency": {
        "niger-congo": {
            "bantu_cluster": {
                "high_efficiency": [
                    ("Swahili", "Kikuyu", 0.75),
                    ("Zulu", "Xhosa", 0.85),
                    ("Shona", "Ndebele", 0.70)
                ],
                "moderate_efficiency": [
                    ("Swahili", "Zulu", 0.55),
                    ("Kikuyu", "Shona", 0.50)
                ]
            },
            "west_african_cluster": {
                "high_efficiency": [
                    ("Yoruba", "Igala", 0.80),
                    ("Twi", "Fante", 0.90),
                    ("Akan", "Ga", 0.60)
                ]
            }
        },
        "afroasiatic": {
            "cushitic_cluster": {
                "high_efficiency": [
                    ("Oromo", "Somali", 0.65),
                    ("Amharic", "Tigrinya", 0.70)
                ]
            },
            "chadic_cluster": {
                "moderate_efficiency": [
                    ("Hausa", "Kanuri", 0.45)
                ]
            }
        }
    },
    "cross_family_efficiency": {
        "low_efficiency": [
            ("Niger-Congo", "Afroasiatic", 0.20),
            ("Niger-Congo", "Nilo-Saharan", 0.15),
            ("Khoisan", "Niger-Congo", 0.10)
        ]
    }
}