#!/usr/bin/env python3
"""
East Africa Major Languages Dataset
Comprehensive coverage of East African languages with emphasis on regional lingua francas
Adding 300M+ speakers from Kenya, Tanzania, Uganda, Ethiopia, Rwanda, Burundi, Somalia, Eritrea, Djibouti, South Sudan
"""

EAST_AFRICA_MAJOR_LANGUAGES = {
    "swa": {  # Swahili - Regional Lingua Franca
        "language_info": {
            "iso639_3": "swa",
            "name": "Swahili",
            "native_name": "Kiswahili",
            "family": "Niger-Congo",
            "subfamily": "Bantu",
            "speakers": 200_000_000,  # Including L2 speakers across East Africa
            "countries": ["Tanzania", "Kenya", "Uganda", "Rwanda", "Burundi", "Democratic Republic of Congo"],
            "regions": ["East Africa", "Great Lakes", "Indian Ocean Coast"],
            "government_sponsored": True,
            "status": "Official language in Tanzania, Kenya, Uganda; Regional lingua franca"
        },
        "text_corpora": {
            "helsinki_swahili_corpus": {
                "title": "Helsinki Corpus of Swahili",
                "description": "Comprehensive digital corpus of written Swahili from University of Helsinki",
                "url": "https://www.helsinki.fi/en/researchgroups/digital-humanities/helsinki-corpus-of-swahili",
                "type": "Academic corpus",
                "size": "Over 12 million tokens",
                "license": "Academic use",
                "institution": "University of Helsinki",
                "year": 2015,
                "domains": ["literature", "newspapers", "government", "education"],
                "features": ["morphological analysis", "part-of-speech tagging"]
            },
            "dar_es_salaam_swahili_corpus": {
                "title": "Dar es Salaam Swahili Corpus",
                "description": "Urban Swahili varieties from Tanzania's largest city",
                "type": "Sociolinguistic corpus",
                "institution": "University of Dar es Salaam",
                "year": 2018,
                "domains": ["urban speech", "code-switching", "youth language"],
                "features": ["dialectal variation", "contact phenomena"]
            }
        },
        "audio_speech_resources": {
            "global_phone_swahili": {
                "title": "GlobalPhone Swahili Speech Corpus",
                "description": "High-quality Swahili speech data for ASR development",
                "type": "Speech corpus",
                "size": "15+ hours",
                "institution": "Karlsruhe Institute of Technology",
                "year": 2013,
                "domains": ["read speech", "phonetically balanced"],
                "tools": ["speech recognition", "phonetic research"]
            },
            "swahili_speech_database": {
                "title": "Swahili Speech Database - KENET",
                "description": "Kenyan English and Swahili speech corpus",
                "type": "Multilingual speech corpus",
                "institution": "Kenya Education Network",
                "year": 2019,
                "features": ["code-switching", "accent variation"]
            }
        },
        "religious_cultural_texts": {
            "swahili_bible": {
                "title": "Biblia Takatifu (Swahili Bible)",
                "description": "Complete Bible translation in Standard Swahili",
                "type": "Religious text",
                "institution": "Bible Society of Kenya/Tanzania",
                "year": 1989,
                "domains": ["religious", "moral instruction"],
                "features": ["formal register", "standardized orthography"]
            },
            "swahili_poetry_collection": {
                "title": "Classical Swahili Poetry Archive",
                "description": "Traditional and modern Swahili poetry including mashairi",
                "type": "Literary archive",
                "institution": "SOAS University of London",
                "year": 2020,
                "domains": ["poetry", "cultural heritage", "oral literature"],
                "features": ["prosodic patterns", "cultural metaphors"]
            }
        },
        "government_official": {
            "tanzanian_parliament_hansard": {
                "title": "Tanzania Parliament Hansard (Swahili)",
                "description": "Official parliamentary proceedings in Swahili",
                "type": "Government corpus",
                "institution": "Parliament of Tanzania",
                "year": 2021,
                "domains": ["politics", "legislation", "formal discourse"],
                "features": ["political terminology", "formal Swahili"]
            }
        },
        "educational_academic": {
            "swahili_language_technology": {
                "title": "Swahili Language Technology Resources",
                "description": "NLP tools and datasets for Swahili",
                "type": "Technology platform",
                "institution": "Technical University of Kenya",
                "year": 2022,
                "tools": ["machine translation", "POS tagging", "morphological analysis"],
                "features": ["computational linguistics", "AI applications"]
            }
        }
    },

    "amh": {  # Amharic - Ethiopian National Language
        "language_info": {
            "iso639_3": "amh",
            "name": "Amharic",
            "native_name": "አማርኛ (Amarəñña)",
            "family": "Afroasiatic",
            "subfamily": "Semitic",
            "speakers": 57_000_000,  # 31.8M native + 25.1M L2
            "countries": ["Ethiopia"],
            "regions": ["Ethiopian Highlands", "Addis Ababa"],
            "government_sponsored": True,
            "status": "Official national language of Ethiopia"
        },
        "text_corpora": {
            "ethiopian_news_corpus": {
                "title": "Ethiopian Amharic News Corpus",
                "description": "News articles from Ethiopian Broadcasting Corporation and major newspapers",
                "type": "News corpus",
                "size": "50+ million words",
                "institution": "Addis Ababa University",
                "year": 2020,
                "domains": ["news", "politics", "economics", "sports"],
                "features": ["contemporary usage", "formal register"]
            },
            "geez_manuscript_corpus": {
                "title": "Ge'ez and Amharic Manuscript Collection",
                "description": "Historical religious and literary texts in Ge'ez script",
                "type": "Historical corpus",
                "institution": "Institute of Ethiopian Studies",
                "year": 2019,
                "domains": ["religious", "historical", "literary"],
                "features": ["ancient orthography", "religious terminology"]
            }
        },
        "audio_speech_resources": {
            "amharic_speech_corpus": {
                "title": "Amharic Speech Recognition Corpus",
                "description": "High-quality Amharic speech data with Ge'ez script transcription",
                "type": "Speech corpus",
                "size": "100+ hours",
                "institution": "Ethiopian Artificial Intelligence Institute",
                "year": 2021,
                "features": ["Ge'ez script", "regional accents"],
                "tools": ["ASR development", "TTS synthesis"]
            }
        },
        "religious_cultural_texts": {
            "amharic_orthodox_texts": {
                "title": "Ethiopian Orthodox Tewahedo Church Texts",
                "description": "Religious literature and liturgical texts in Amharic",
                "type": "Religious corpus",
                "institution": "Ethiopian Orthodox Tewahedo Church",
                "year": 2018,
                "domains": ["liturgy", "theology", "spiritual guidance"],
                "features": ["religious vocabulary", "formal ecclesiastical language"]
            }
        },
        "government_official": {
            "ethiopian_constitution_amharic": {
                "title": "Constitution of Ethiopia (Amharic)",
                "description": "Official government constitution and legal documents",
                "type": "Legal corpus",
                "institution": "Government of Ethiopia",
                "year": 1995,
                "domains": ["legal", "constitutional", "administrative"],
                "features": ["legal terminology", "formal government language"]
            }
        },
        "educational_academic": {
            "amharic_computational_linguistics": {
                "title": "Amharic Computational Linguistics Resources",
                "description": "NLP tools and morphological analyzers for Amharic",
                "type": "Research platform",
                "institution": "Addis Ababa University",
                "year": 2022,
                "tools": ["morphological analysis", "stemming", "POS tagging"],
                "features": ["Semitic morphology", "Ge'ez script processing"]
            }
        }
    },

    "orm": {  # Oromo - Largest single language in Ethiopia
        "language_info": {
            "iso639_3": "orm",
            "name": "Oromo",
            "native_name": "Afaan Oromoo",
            "family": "Afroasiatic",
            "subfamily": "Cushitic",
            "speakers": 41_700_000,  # 33.8% of Ethiopia
            "countries": ["Ethiopia", "Kenya", "Somalia"],
            "regions": ["Oromia", "Ethiopian Highlands", "Horn of Africa"],
            "government_sponsored": True,
            "status": "Official working language of Oromia Regional State"
        },
        "text_corpora": {
            "oromo_literature_corpus": {
                "title": "Oromo Literature and Oral Tradition Corpus",
                "description": "Traditional stories, songs, and modern Oromo literature",
                "type": "Cultural corpus",
                "institution": "Oromia Culture and Tourism Bureau",
                "year": 2019,
                "domains": ["folklore", "oral tradition", "literature"],
                "features": ["cultural knowledge", "traditional values"]
            }
        },
        "religious_cultural_texts": {
            "oromo_bible_qubee": {
                "title": "Kitaaba Qulqulluu (Oromo Bible)",
                "description": "Complete Bible translation in Oromo using Qubee (Latin) script",
                "type": "Religious text",
                "institution": "Ethiopian Bible Society",
                "year": 2006,
                "features": ["standardized orthography", "religious vocabulary"]
            },
            "gada_system_documentation": {
                "title": "Gada System Cultural Documentation",
                "description": "Traditional Oromo governance system and cultural practices",
                "type": "Cultural archive",
                "institution": "UNESCO/Oromia Cultural Center",
                "year": 2020,
                "domains": ["traditional governance", "cultural practices", "oral history"],
                "features": ["indigenous knowledge", "cultural terminology"]
            }
        },
        "government_official": {
            "oromia_regional_documents": {
                "title": "Oromia Regional Government Documents",
                "description": "Official regional government communications and policies",
                "type": "Government corpus",
                "institution": "Oromia Regional Government",
                "year": 2021,
                "domains": ["administration", "policy", "regional governance"],
                "features": ["official terminology", "administrative language"]
            }
        },
        "educational_academic": {
            "oromo_language_academy": {
                "title": "Oromo Language Academy Resources",
                "description": "Language standardization and educational materials",
                "type": "Academic resource",
                "institution": "Jimma University",
                "year": 2020,
                "domains": ["language planning", "education", "standardization"],
                "features": ["orthographic standards", "pedagogical materials"]
            }
        }
    },

    "som": {  # Somali - Horn of Africa Lingua Franca
        "language_info": {
            "iso639_3": "som",
            "name": "Somali",
            "native_name": "Af-Soomaali",
            "family": "Afroasiatic",
            "subfamily": "Cushitic",
            "speakers": 24_000_000,
            "countries": ["Somalia", "Ethiopia", "Djibouti", "Kenya"],
            "regions": ["Horn of Africa", "Somali Peninsula", "East Africa"],
            "government_sponsored": True,
            "status": "Official in Somalia and Djibouti; Regional official in Ethiopia"
        },
        "text_corpora": {
            "somali_poetry_corpus": {
                "title": "Classical Somali Poetry Collection",
                "description": "Traditional and modern Somali poetry including gabay and buraanbur",
                "type": "Literary corpus",
                "institution": "Somali National University",
                "year": 2018,
                "domains": ["poetry", "oral literature", "cultural heritage"],
                "features": ["alliterative verse", "oral traditions"]
            }
        },
        "religious_cultural_texts": {
            "somali_quran_translation": {
                "title": "Quraanka Kariimka (Somali Quran)",
                "description": "Complete Quran translation and Islamic texts in Somali",
                "type": "Religious text",
                "institution": "Islamic Society of Somalia",
                "year": 2015,
                "features": ["religious vocabulary", "Islamic terminology"]
            },
            "somali_cultural_archive": {
                "title": "Somali Cultural Heritage Archive",
                "description": "Traditional stories, proverbs, and cultural practices",
                "type": "Cultural archive",
                "institution": "Academy of Sciences and Arts of Somalia",
                "year": 2019,
                "domains": ["oral tradition", "proverbs", "cultural practices"],
                "features": ["traditional knowledge", "cultural identity"]
            }
        },
        "government_official": {
            "somali_government_corpus": {
                "title": "Federal Government of Somalia Documents",
                "description": "Official government communications and legislation",
                "type": "Government corpus",
                "institution": "Federal Government of Somalia",
                "year": 2020,
                "domains": ["legislation", "administration", "public policy"],
                "features": ["official terminology", "legal language"]
            }
        },
        "media_communication": {
            "somali_broadcasting_corpus": {
                "title": "Somali Broadcasting Corporation Archive",
                "description": "News broadcasts and cultural programs",
                "type": "Media corpus",
                "institution": "Somali Broadcasting Corporation",
                "year": 2021,
                "domains": ["news", "entertainment", "cultural programs"],
                "features": ["broadcast language", "contemporary usage"]
            }
        }
    },

    "kik": {  # Kikuyu - Kenya's largest ethnic group
        "language_info": {
            "iso639_3": "kik",
            "name": "Kikuyu",
            "native_name": "Gĩkũyũ",
            "family": "Niger-Congo",
            "subfamily": "Bantu",
            "speakers": 8_100_000,  # 17.1% of Kenya
            "countries": ["Kenya"],
            "regions": ["Central Kenya", "Nairobi", "Mount Kenya region"],
            "government_sponsored": True,
            "status": "National language in Kenya"
        },
        "text_corpora": {
            "kikuyu_literature_corpus": {
                "title": "Gĩkũyũ Literature Collection",
                "description": "Traditional and modern Kikuyu literature including Ngũgĩ wa Thiong'o works",
                "type": "Literary corpus",
                "institution": "University of Nairobi",
                "year": 2019,
                "domains": ["literature", "cultural identity", "postcolonial writing"],
                "features": ["literary language", "cultural themes"]
            }
        },
        "religious_cultural_texts": {
            "kikuyu_bible": {
                "title": "Ibuku Ria Ngai (Kikuyu Bible)",
                "description": "Complete Bible translation in Kikuyu",
                "type": "Religious text",
                "institution": "Bible Society of Kenya",
                "year": 2001,
                "features": ["standardized orthography", "religious vocabulary"]
            },
            "kikuyu_oral_traditions": {
                "title": "Kikuyu Oral Traditions Archive",
                "description": "Traditional stories, proverbs, and cultural practices",
                "type": "Cultural archive",
                "institution": "Kenyatta University",
                "year": 2020,
                "domains": ["oral literature", "proverbs", "traditional knowledge"],
                "features": ["cultural wisdom", "traditional values"]
            }
        },
        "educational_academic": {
            "kikuyu_language_research": {
                "title": "Kikuyu Language Documentation Project",
                "description": "Comprehensive linguistic analysis and documentation",
                "type": "Research project",
                "institution": "University of Nairobi",
                "year": 2021,
                "domains": ["linguistics", "phonology", "morphology"],
                "features": ["tonal analysis", "grammatical description"]
            }
        }
    },

    "tir": {  # Tigrinya - Eritrea/Ethiopia major language
        "language_info": {
            "iso639_3": "tir",
            "name": "Tigrinya",
            "native_name": "ትግርኛ (Tigriññā)",
            "family": "Afroasiatic",
            "subfamily": "Semitic",
            "speakers": 9_000_000,  # Ethiopia + Eritrea
            "countries": ["Eritrea", "Ethiopia"],
            "regions": ["Tigray", "Eritrean Highlands"],
            "government_sponsored": True,
            "status": "Co-official in Eritrea; Official working language in Tigray"
        },
        "text_corpora": {
            "tigrinya_news_corpus": {
                "title": "Tigrinya News and Media Corpus",
                "description": "News articles and broadcasts from Eritrea and Ethiopia",
                "type": "News corpus",
                "institution": "Asmara University",
                "year": 2020,
                "domains": ["news", "current affairs", "politics"],
                "features": ["contemporary usage", "media language"]
            }
        },
        "religious_cultural_texts": {
            "tigrinya_orthodox_texts": {
                "title": "Tigrinya Orthodox Church Literature",
                "description": "Religious texts and liturgical materials",
                "type": "Religious corpus",
                "institution": "Eritrean Orthodox Tewahedo Church",
                "year": 2018,
                "domains": ["liturgy", "religious instruction", "spiritual texts"],
                "features": ["ecclesiastical language", "religious terminology"]
            }
        },
        "government_official": {
            "eritrean_constitution_tigrinya": {
                "title": "Constitution of Eritrea (Tigrinya)",
                "description": "Official government constitution and legal documents",
                "type": "Legal corpus",
                "institution": "Government of Eritrea",
                "year": 1997,
                "domains": ["legal", "constitutional", "administrative"],
                "features": ["legal terminology", "official language"]
            }
        },
        "educational_academic": {
            "tigrinya_linguistic_research": {
                "title": "Tigrinya Language Studies",
                "description": "Academic research on Tigrinya phonology and morphology",
                "type": "Academic research",
                "institution": "Mekelle University",
                "year": 2021,
                "domains": ["linguistics", "Semitic studies", "comparative grammar"],
                "features": ["Semitic morphology", "phonological analysis"]
            }
        }
    },

    "kin": {  # Kinyarwanda - Rwanda official language
        "language_info": {
            "iso639_3": "kin",
            "name": "Kinyarwanda",
            "native_name": "Ikinyarwanda",
            "family": "Niger-Congo",
            "subfamily": "Bantu",
            "speakers": 12_000_000,  # Rwanda + diaspora
            "countries": ["Rwanda", "Democratic Republic of Congo", "Uganda"],
            "regions": ["Rwanda", "Great Lakes region"],
            "government_sponsored": True,
            "status": "Official language of Rwanda"
        },
        "text_corpora": {
            "kinyarwanda_literature_corpus": {
                "title": "Kinyarwanda Literature Collection",
                "description": "Traditional and contemporary Rwandan literature",
                "type": "Literary corpus",
                "institution": "University of Rwanda",
                "year": 2019,
                "domains": ["literature", "cultural identity", "national unity"],
                "features": ["literary tradition", "post-genocide literature"]
            }
        },
        "religious_cultural_texts": {
            "kinyarwanda_bible": {
                "title": "Bibiliya Yera (Kinyarwanda Bible)",
                "description": "Complete Bible translation in Kinyarwanda",
                "type": "Religious text",
                "institution": "Bible Society of Rwanda",
                "year": 2003,
                "features": ["standardized orthography", "religious vocabulary"]
            },
            "rwandan_cultural_heritage": {
                "title": "Rwandan Cultural Heritage Archive",
                "description": "Traditional stories, music, and cultural practices",
                "type": "Cultural archive",
                "institution": "Institute of National Museums of Rwanda",
                "year": 2020,
                "domains": ["oral tradition", "music", "cultural practices"],
                "features": ["traditional knowledge", "cultural identity"]
            }
        },
        "government_official": {
            "rwandan_government_corpus": {
                "title": "Government of Rwanda Official Documents",
                "description": "Official government communications and policies",
                "type": "Government corpus",
                "institution": "Government of Rwanda",
                "year": 2021,
                "domains": ["governance", "policy", "national development"],
                "features": ["official terminology", "administrative language"]
            }
        },
        "educational_academic": {
            "kinyarwanda_language_commission": {
                "title": "Rwanda Language Commission Resources",
                "description": "Language planning and standardization materials",
                "type": "Language planning",
                "institution": "Rwanda Language Commission",
                "year": 2020,
                "domains": ["language policy", "standardization", "education"],
                "features": ["linguistic planning", "educational materials"]
            }
        }
    },

    "run": {  # Kirundi - Burundi official language
        "language_info": {
            "iso639_3": "run",
            "name": "Kirundi",
            "native_name": "Ikirundi",
            "family": "Niger-Congo",
            "subfamily": "Bantu",
            "speakers": 9_000_000,
            "countries": ["Burundi", "Democratic Republic of Congo", "Tanzania"],
            "regions": ["Burundi", "Great Lakes region"],
            "government_sponsored": True,
            "status": "Official language of Burundi"
        },
        "text_corpora": {
            "kirundi_oral_literature": {
                "title": "Kirundi Oral Literature Collection",
                "description": "Traditional stories, proverbs, and cultural narratives",
                "type": "Cultural corpus",
                "institution": "University of Burundi",
                "year": 2018,
                "domains": ["oral literature", "proverbs", "traditional stories"],
                "features": ["cultural wisdom", "traditional values"]
            }
        },
        "religious_cultural_texts": {
            "kirundi_bible": {
                "title": "Bibiliya Ntagatifu (Kirundi Bible)",
                "description": "Complete Bible translation in Kirundi",
                "type": "Religious text",
                "institution": "Bible Society of Burundi",
                "year": 2004,
                "features": ["standardized orthography", "religious vocabulary"]
            }
        },
        "government_official": {
            "burundi_constitution_kirundi": {
                "title": "Constitution of Burundi (Kirundi)",
                "description": "Official government constitution and legal documents",
                "type": "Legal corpus",
                "institution": "Government of Burundi",
                "year": 2018,
                "domains": ["legal", "constitutional", "administrative"],
                "features": ["legal terminology", "official language"]
            }
        },
        "educational_academic": {
            "kirundi_linguistic_studies": {
                "title": "Kirundi Language Research",
                "description": "Academic studies on Kirundi grammar and phonology",
                "type": "Academic research",
                "institution": "University of Burundi",
                "year": 2021,
                "domains": ["linguistics", "Bantu studies", "morphology"],
                "features": ["grammatical analysis", "phonological description"]
            }
        }
    }
}

EAST_AFRICA_SUMMARY = {
    "region": "East Africa",
    "description": "Fifth flagship region covering East African lingua francas and national languages",
    "countries_covered": ["Kenya", "Tanzania", "Uganda", "Ethiopia", "Rwanda", "Burundi", "Somalia", "Eritrea", "Djibouti"],
    "languages_count": len(EAST_AFRICA_MAJOR_LANGUAGES),
    "total_speakers": sum(lang["language_info"]["speakers"] for lang in EAST_AFRICA_MAJOR_LANGUAGES.values()),
    "language_families": ["Niger-Congo (Bantu)", "Afroasiatic (Semitic)", "Afroasiatic (Cushitic)"],
    "cross_border_languages": ["Swahili", "Somali", "Oromo", "Kinyarwanda", "Kirundi"],
    "regional_significance": "Major East African lingua francas and national languages with government support",
    "cultural_features": ["Ancient Orthodox Christianity", "Islamic traditions", "Bantu cultural systems", "Cushitic pastoralism", "Semitic literary heritage"],
    "unique_aspects": ["Ge'ez script (Amharic, Tigrinya)", "Swahili as pan-African lingua franca", "Ancient Ethiopian civilization", "Great Lakes cultural region", "Horn of Africa languages"],
    "academic_institutions": ["University of Nairobi", "University of Dar es Salaam", "Addis Ababa University", "University of Rwanda", "Makerere University"],
    "government_languages": 8,  # Languages with official status
    "total_data_sources": sum(
        len([resource for category in lang.values() if isinstance(category, dict) and category != lang.get("language_info", {})
             for resource in category.values() if isinstance(resource, dict)])
        for lang in EAST_AFRICA_MAJOR_LANGUAGES.values()
    )
}