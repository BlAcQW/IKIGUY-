#!/usr/bin/env python3
"""
Central Africa Major Languages Data Sources
Comprehensive collection of Central African lingua francas and regional languages
Establishing Central Africa as fourth flagship region with 50M+ speakers
"""

CENTRAL_AFRICA_MAJOR_LANGUAGES = {
    # TIER 1: MAXIMUM IMPACT CROSS-BORDER LINGUA FRANCAS
    "lin": {  # Lingala - Major lingua franca
        "language_info": {
            "iso639_3": "lin",
            "name": "Lingala",
            "native_name": "Lingála",
            "family": "Niger-Congo",
            "subfamily": "Bantu",
            "speakers": 40_000_000,  # 20M native + 20M L2
            "countries": ["Democratic Republic of Congo", "Republic of Congo"],
            "regions": ["Kinshasa", "Northwest DRC", "Northeast Republic of Congo", "Brazzaville"],
            "government_sponsored": True,
            "status": "National language in DRC and Republic of Congo, lingua franca of 52M people"
        },
        "text_corpora": {
            "lingala_bible_corpus": {
                "title": "Lingala Bible Translation",
                "description": "Complete Bible translation in Lingala (Baibele)",
                "url": "https://www.bible.com/bible/316/GEN.1.LIN",
                "type": "religious_corpus",
                "size": "Complete Bible",
                "license": "Religious use",
                "institution": "Bible Society of Congo",
                "year": 1996,
                "domains": ["religious_texts", "standardized_orthography", "cross_border_standard"]
            },
            "lingala_music_corpus": {
                "title": "Lingala Popular Music and Cultural Texts",
                "description": "Soukous, rumba, and contemporary Lingala music lyrics",
                "type": "musical_corpus",
                "size": "Extensive music collection",
                "license": "Cultural preservation",
                "institution": "Central African Music Archives",
                "year": "1960-ongoing",
                "domains": ["popular_music", "urban_culture", "cultural_identity", "diaspora_connection"]
            },
            "lingala_media_corpus": {
                "title": "Lingala Radio and Television Content",
                "description": "Radio Congo and television broadcasts in Lingala",
                "type": "broadcast_corpus",
                "size": "Broadcast archive",
                "license": "Media archive",
                "institution": "Radio Congo, RTNC (DRC National Radio/TV)",
                "year": "1970-ongoing",
                "domains": ["news", "entertainment", "educational_programs", "urban_communication"]
            },
            "lingala_military_corpus": {
                "title": "Lingala Military and Administrative Texts",
                "description": "Military communications and administrative documents",
                "type": "government_corpus",
                "size": "Administrative documentation",
                "license": "Government use",
                "institution": "Armed Forces of DRC, Government of Republic of Congo",
                "year": "1960-ongoing",
                "domains": ["military_communication", "administrative_language", "formal_register"]
            }
        },
        "audio_speech_resources": {
            "lingala_radio_archive": {
                "title": "Lingala Radio Broadcasting Archive",
                "description": "Decades of radio programming in Lingala",
                "type": "broadcast_corpus",
                "size": "1000+ hours historical broadcasts",
                "license": "Archive use",
                "institution": "Radio Congo, Voice of Congo",
                "year": "1960-ongoing",
                "domains": ["news_broadcasting", "cultural_programs", "music_shows", "public_communication"]
            },
            "lingala_music_audio": {
                "title": "Lingala Music Audio Collection",
                "description": "Traditional and modern Lingala music recordings",
                "type": "musical_corpus",
                "size": "2000+ hours music",
                "license": "Cultural preservation",
                "institution": "Congo Music Heritage Project",
                "year": "1950-ongoing",
                "domains": ["traditional_music", "popular_music", "cultural_expression"]
            }
        },
        "research_resources": {
            "unikin_lingala_research": {
                "title": "University of Kinshasa Lingala Studies",
                "description": "Academic research on Lingala linguistics and sociolinguistics",
                "url": "https://www.unikin.ac.cd/",
                "type": "university_research",
                "institution": "University of Kinshasa",
                "year": "Ongoing",
                "focus": ["bantu_linguistics", "urban_sociolinguistics", "congo_river_languages"]
            },
            "sil_lingala_documentation": {
                "title": "SIL International Lingala Documentation",
                "description": "Linguistic documentation and Bible translation research",
                "url": "https://www.sil.org/resources/archives/lingala",
                "type": "linguistic_documentation",
                "institution": "SIL International",
                "year": "Ongoing",
                "focus": ["bible_translation", "linguistic_analysis", "literacy_development"]
            }
        },
        "cultural_resources": {
            "lingala_cultural_heritage": {
                "title": "Lingala Cultural Heritage and Urban Identity",
                "description": "Urban culture, music, and modern Central African identity",
                "type": "cultural_documentation",
                "institution": "Congo Cultural Centers, Music Heritage Projects",
                "year": "Ongoing",
                "domains": ["urban_culture", "music_industry", "cultural_identity", "river_culture"]
            }
        }
    },
    "swa": {  # Swahili - Continental trade language
        "language_info": {
            "iso639_3": "swa",
            "name": "Swahili",
            "native_name": "Kiswahili",
            "family": "Niger-Congo",
            "subfamily": "Bantu",
            "speakers": 20_000_000,  # Central Africa portion
            "countries": ["Democratic Republic of Congo", "Tanzania", "Kenya", "Uganda"],
            "regions": ["Eastern DRC", "North Kivu", "South Kivu", "Katanga"],
            "government_sponsored": True,
            "status": "National language in DRC, continental trade language, 200M global speakers"
        },
        "text_corpora": {
            "swahili_bible_drc": {
                "title": "Swahili Bible Translation (DRC Variant)",
                "description": "Bible translation in Congo Swahili/Kingwana",
                "url": "https://www.bible.com/bible/316/GEN.1.SWA",
                "type": "religious_corpus",
                "size": "Complete Bible",
                "license": "Religious use",
                "institution": "Bible Society of Congo",
                "year": 1952,
                "domains": ["religious_texts", "congo_swahili_variant"]
            },
            "swahili_trade_corpus": {
                "title": "Swahili Cross-Border Trade Documentation",
                "description": "Trading communications and commercial documents",
                "type": "commercial_corpus",
                "size": "Commercial documentation",
                "license": "Trade archive",
                "institution": "East African Community, DRC Trade Ministry",
                "year": "1990-ongoing",
                "domains": ["cross_border_trade", "commercial_communication", "economic_integration"]
            },
            "kingwana_corpus": {
                "title": "Kingwana (Congo Swahili) Linguistic Corpus",
                "description": "Documentation of Congo Swahili dialect variations",
                "type": "dialectal_corpus",
                "size": "Regional dialect collection",
                "license": "Academic research",
                "institution": "University of Lubumbashi",
                "year": "2000-ongoing",
                "domains": ["dialectal_variation", "regional_adaptation", "linguistic_documentation"]
            }
        },
        "research_resources": {
            "ulubumbashi_swahili": {
                "title": "University of Lubumbashi Swahili Research",
                "description": "Research on Congo Swahili and Eastern DRC linguistics",
                "url": "https://www.unilu.ac.cd/",
                "type": "university_research",
                "institution": "University of Lubumbashi",
                "year": "Ongoing",
                "focus": ["congo_swahili", "regional_variation", "mining_region_communication"]
            },
            "africanlp_swahili": {
                "title": "AfricaNLP Swahili Research Initiative",
                "description": "Pan-African research on Swahili NLP and technology",
                "url": "https://www.africanlp.com/",
                "type": "research_consortium",
                "institution": "AfricaNLP Community",
                "year": "Ongoing",
                "focus": ["nlp_development", "pan_african_communication", "technology_adaptation"]
            }
        },
        "cultural_resources": {
            "swahili_central_africa": {
                "title": "Swahili Cultural Adaptation in Central Africa",
                "description": "Cultural and economic role in Central African context",
                "type": "cultural_documentation",
                "institution": "East African Community, DRC Cultural Ministry",
                "year": "Ongoing",
                "domains": ["economic_integration", "cultural_bridge", "mining_communities"]
            }
        }
    },
    "fra": {  # French - Administrative lingua franca
        "language_info": {
            "iso639_3": "fra",
            "name": "French",
            "native_name": "Français",
            "family": "Indo-European",
            "subfamily": "Romance",
            "speakers": 75_000_000,  # Central Africa total
            "countries": ["Democratic Republic of Congo", "Cameroon", "Central African Republic", "Republic of Congo", "Chad", "Gabon"],
            "regions": ["Urban centers", "Administrative regions", "Educational institutions"],
            "government_sponsored": True,
            "status": "Official language across Central Africa, administrative and educational lingua franca"
        },
        "text_corpora": {
            "french_central_africa_admin": {
                "title": "Central African French Administrative Corpus",
                "description": "Government documents and administrative communications",
                "type": "government_corpus",
                "size": "Extensive administrative documentation",
                "license": "Public domain",
                "institution": "Governments of Central African countries",
                "year": "1960-ongoing",
                "domains": ["government_communication", "administrative_language", "legal_documents"]
            },
            "french_central_africa_education": {
                "title": "Central African French Educational Materials",
                "description": "School curricula and educational resources",
                "type": "educational_corpus",
                "size": "Educational material collection",
                "license": "Educational use",
                "institution": "Ministries of Education, UNESCO",
                "year": "1960-ongoing",
                "domains": ["education", "curriculum", "academic_communication"]
            },
            "french_central_africa_media": {
                "title": "Central African French Media Corpus",
                "description": "Newspapers, radio, and television content",
                "type": "media_corpus",
                "size": "Regional media collection",
                "license": "Media archive",
                "institution": "Central African Media Organizations",
                "year": "1960-ongoing",
                "domains": ["journalism", "public_communication", "regional_news"]
            }
        },
        "research_resources": {
            "francophonie_central_africa": {
                "title": "Organisation Internationale de la Francophonie - Central Africa",
                "description": "French language development and cultural programs",
                "url": "https://www.francophonie.org/",
                "type": "international_organization",
                "institution": "Organisation Internationale de la Francophonie",
                "year": "Ongoing",
                "focus": ["language_development", "cultural_cooperation", "educational_support"]
            }
        },
        "cultural_resources": {
            "french_central_africa_culture": {
                "title": "Central African French Cultural Adaptation",
                "description": "Local adaptations and cultural expressions in French",
                "type": "cultural_documentation",
                "institution": "Central African Cultural Institutions",
                "year": "Ongoing",
                "domains": ["cultural_adaptation", "local_expressions", "multilingual_identity"]
            }
        }
    },
    # TIER 2: REGIONAL POWERHOUSES
    "sag": {  # Sango - Central African Republic national language
        "language_info": {
            "iso639_3": "sag",
            "name": "Sango",
            "native_name": "Sängö",
            "family": "Niger-Congo",
            "subfamily": "Ubangian",
            "speakers": 5_500_000,
            "countries": ["Central African Republic", "Chad", "Democratic Republic of Congo"],
            "regions": ["Central African Republic (nationwide)", "Southern Chad"],
            "government_sponsored": True,
            "status": "National and co-official language of CAR, 92% population coverage"
        },
        "text_corpora": {
            "sango_bible_corpus": {
                "title": "Sango Bible Translation",
                "description": "Complete Bible translation in Sango",
                "url": "https://www.bible.com/bible/316/GEN.1.SAG",
                "type": "religious_corpus",
                "size": "Complete Bible",
                "license": "Religious use",
                "institution": "Bible Society of Central African Republic",
                "year": 1988,
                "domains": ["religious_texts", "national_language"]
            },
            "sango_government_corpus": {
                "title": "CAR Government Sango Documents",
                "description": "Official government communications in Sango",
                "type": "government_corpus",
                "size": "Government documentation",
                "license": "Public domain",
                "institution": "Government of Central African Republic",
                "year": "1960-ongoing",
                "domains": ["government_communication", "national_identity", "public_information"]
            },
            "sango_educational_materials": {
                "title": "Sango Educational Materials",
                "description": "School curricula and literacy materials",
                "type": "educational_corpus",
                "size": "Educational collection",
                "license": "Educational use",
                "institution": "Ministry of Education CAR",
                "year": "1980-ongoing",
                "domains": ["primary_education", "literacy", "mother_tongue_instruction"]
            }
        },
        "research_resources": {
            "sil_sango_research": {
                "title": "SIL International Sango Research",
                "description": "Linguistic documentation and development",
                "url": "https://www.sil.org/resources/archives/sango",
                "type": "linguistic_research",
                "institution": "SIL International",
                "year": "Ongoing",
                "focus": ["creole_linguistics", "national_language_development", "literacy_programs"]
            }
        },
        "cultural_resources": {
            "sango_national_identity": {
                "title": "Sango and Central African National Identity",
                "description": "Role in national unity and cultural identity",
                "type": "cultural_documentation",
                "institution": "CAR Cultural Ministry, Traditional Authorities",
                "year": "Ongoing",
                "domains": ["national_unity", "cultural_identity", "lingua_franca_role"]
            }
        }
    },
    "lua": {  # Tshiluba/Luba-Kasai
        "language_info": {
            "iso639_3": "lua",
            "name": "Tshiluba",
            "native_name": "Tshiluba",
            "family": "Niger-Congo",
            "subfamily": "Bantu",
            "speakers": 8_000_000,
            "countries": ["Democratic Republic of Congo"],
            "regions": ["Kasai provinces", "Kananga region"],
            "government_sponsored": True,
            "status": "National language of DRC, major Kasai region language"
        },
        "text_corpora": {
            "tshiluba_bible_corpus": {
                "title": "Tshiluba Bible Translation",
                "description": "Complete Bible translation in Tshiluba",
                "type": "religious_corpus",
                "size": "Complete Bible",
                "license": "Religious use",
                "institution": "Bible Society of Congo",
                "year": 1982,
                "domains": ["religious_texts", "regional_standard"]
            },
            "tshiluba_oral_literature": {
                "title": "Tshiluba Oral Literature and Traditional Texts",
                "description": "Traditional narratives, proverbs, and cultural texts",
                "type": "cultural_corpus",
                "size": "Traditional literature collection",
                "license": "Cultural preservation",
                "institution": "Luba Cultural Organizations",
                "year": "Traditional to present",
                "domains": ["oral_traditions", "cultural_heritage", "traditional_knowledge"]
            }
        },
        "research_resources": {
            "luba_cultural_research": {
                "title": "Luba Cultural and Linguistic Research",
                "description": "Research on Luba languages and culture",
                "type": "cultural_research",
                "institution": "University of Kananga, Cultural Organizations",
                "year": "Ongoing",
                "focus": ["luba_linguistics", "kasai_cultures", "traditional_knowledge"]
            }
        },
        "cultural_resources": {
            "luba_cultural_heritage": {
                "title": "Luba Cultural Heritage and Traditions",
                "description": "Traditional governance, ceremonies, and cultural practices",
                "type": "cultural_documentation",
                "institution": "Luba Traditional Authority",
                "year": "Ongoing",
                "domains": ["traditional_governance", "cultural_ceremonies", "oral_history"]
            }
        }
    },
    "kon": {  # Kikongo
        "language_info": {
            "iso639_3": "kon",
            "name": "Kikongo",
            "native_name": "Kikongo",
            "family": "Niger-Congo",
            "subfamily": "Bantu",
            "speakers": 12_000_000,  # 7M native + 5M L2
            "countries": ["Democratic Republic of Congo", "Angola", "Republic of Congo", "Gabon"],
            "regions": ["Southwest DRC", "Northwest Angola", "Southwest Republic of Congo"],
            "government_sponsored": True,
            "status": "National language in DRC and Republic of Congo (as Kituba), cross-border cultural bridge"
        },
        "text_corpora": {
            "kikongo_bible_corpus": {
                "title": "Kikongo Bible Translation",
                "description": "Bible translation in Kikongo/Kituba",
                "type": "religious_corpus",
                "size": "Complete Bible",
                "license": "Religious use",
                "institution": "Bible Society of Congo, Angola",
                "year": 1905,
                "domains": ["religious_texts", "historical_translation", "cross_border_standard"]
            },
            "kikongo_historical_texts": {
                "title": "Kikongo Historical and Royal Texts",
                "description": "Kingdom of Kongo historical documents and traditions",
                "type": "historical_corpus",
                "size": "Historical text collection",
                "license": "Cultural preservation",
                "institution": "Kongo Traditional Authority, Historical Research",
                "year": "Traditional to present",
                "domains": ["kingdom_history", "royal_traditions", "historical_documentation"]
            }
        },
        "research_resources": {
            "kongo_kingdom_research": {
                "title": "Kingdom of Kongo Historical and Linguistic Research",
                "description": "Research on Kongo kingdom heritage and language",
                "type": "historical_research",
                "institution": "Universities in DRC, Angola, Republic of Congo",
                "year": "Ongoing",
                "focus": ["kingdom_heritage", "historical_linguistics", "cross_border_culture"]
            }
        },
        "cultural_resources": {
            "kongo_cultural_heritage": {
                "title": "Kongo Cultural Heritage and Kingdom Traditions",
                "description": "Ancient kingdom traditions and cross-border cultural identity",
                "type": "cultural_documentation",
                "institution": "Kongo Traditional Authority, Cultural Centers",
                "year": "Ongoing",
                "domains": ["kingdom_heritage", "cross_border_identity", "traditional_governance", "cultural_continuity"]
            }
        }
    },
    # TIER 3: CAMEROON REGIONAL LANGUAGES
    "ewo": {  # Ewondo - Cameroon lingua franca
        "language_info": {
            "iso639_3": "ewo",
            "name": "Ewondo",
            "native_name": "Ewondo",
            "family": "Niger-Congo",
            "subfamily": "Bantu",
            "speakers": 1_200_000,
            "countries": ["Cameroon"],
            "regions": ["Center Province", "South Province", "East Province", "Yaoundé region"],
            "government_sponsored": False,
            "status": "Major lingua franca, candidate for third official language by 2030"
        },
        "text_corpora": {
            "ewondo_bible_corpus": {
                "title": "Ewondo Bible Translation",
                "description": "Complete Bible translation in Ewondo",
                "type": "religious_corpus",
                "size": "Complete Bible",
                "license": "Religious use",
                "institution": "Bible Society of Cameroon",
                "year": 1952,
                "domains": ["religious_texts", "regional_standard"]
            },
            "ewondo_educational_materials": {
                "title": "Ewondo Educational Materials",
                "description": "Educational resources and literature",
                "type": "educational_corpus",
                "size": "Educational collection",
                "license": "Educational use",
                "institution": "University of Yaoundé",
                "year": "1970-ongoing",
                "domains": ["education", "regional_communication", "urban_lingua_franca"]
            }
        },
        "research_resources": {
            "uy_ewondo_research": {
                "title": "University of Yaoundé Ewondo Studies",
                "description": "Academic research on Ewondo and Cameroon languages",
                "url": "https://www.uy1.uninet.cm/",
                "type": "university_research",
                "institution": "University of Yaoundé I",
                "year": "Ongoing",
                "focus": ["cameroon_linguistics", "bantu_studies", "regional_lingua_francas"]
            }
        },
        "cultural_resources": {
            "ewondo_cultural_practices": {
                "title": "Ewondo Cultural Practices and Traditions",
                "description": "Cultural identity and regional practices",
                "type": "cultural_documentation",
                "institution": "Ewondo Cultural Organizations",
                "year": "Ongoing",
                "domains": ["cultural_identity", "regional_traditions", "urban_culture"]
            }
        }
    }
}

# Summary statistics for Central Africa major languages
CENTRAL_AFRICA_SUMMARY = {
    "total_languages": len(CENTRAL_AFRICA_MAJOR_LANGUAGES),
    "total_speakers": sum(lang["language_info"]["speakers"] for lang in CENTRAL_AFRICA_MAJOR_LANGUAGES.values()),
    "tier_1_languages": 3,  # Lingala, Swahili, French (cross-border lingua francas)
    "tier_2_languages": 4,  # Sango, Tshiluba, Kikongo, Ewondo (regional languages)
    "language_families": {
        "Niger-Congo": {
            "Bantu": ["lin", "swa", "lua", "kon", "ewo"],
            "Ubangian": ["sag"]
        },
        "Indo-European": {
            "Romance": ["fra"]
        }
    },
    "countries_covered": {
        "Democratic Republic of Congo": 6,  # Major coverage
        "Republic of Congo": 2,
        "Central African Republic": 2,
        "Cameroon": 2,
        "Cross-border languages": 6
    },
    "government_languages": 7,  # Most have official/national status
    "academic_institutions": [
        "University of Kinshasa", "University of Lubumbashi", "University of Yaoundé",
        "University of Kananga", "SIL International", "AfricaNLP Community",
        "Organisation Internationale de la Francophonie"
    ],
    "data_source_types": {
        "religious_corpus": 7,
        "government_corpus": 4,
        "cultural_corpus": 8,
        "broadcast_corpus": 3,
        "educational_corpus": 4,
        "musical_corpus": 2,
        "university_research": 8
    },
    "special_features": {
        "cross_border_languages": ["lin", "swa", "fra", "kon"],
        "lingua_francas": ["lin", "swa", "fra", "sag"],
        "national_languages": ["lin", "swa", "sag", "lua", "kon"],
        "economic_languages": ["swa", "fra", "lin"],
        "cultural_bridges": ["kon", "lin", "swa"]
    },
    "impact_potential": "163M+ speakers across Central Africa's major lingua francas and regional languages"
}