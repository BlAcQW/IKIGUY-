#!/usr/bin/env python3
"""
Language Data Sources for Twi, Ga, Ewe, and Hausa
Comprehensive collection of datasets, corpora, audio resources, and research links
"""

LANGUAGE_DATA_SOURCES = {
    "twi": {
        "language_info": {
            "iso639_3": "twi",
            "name": "Twi",
            "native_name": "Twi",
            "family": "Niger-Congo",
            "subfamily": "Kwa",
            "speakers": 9_000_000,
            "countries": ["Ghana"],
            "regions": ["Ashanti", "Eastern", "Western Ghana"]
        },
        "text_corpora": {
            "english_twi_parallel_corpus": {
                "title": "English-Twi Parallel Corpus for Machine Translation",
                "description": "Large-scale parallel corpus with 35,833 sentence pairs",
                "url": "https://www.researchgate.net/publication/350483888_English-Twi_Parallel_Corpus_for_Machine_Translation",
                "type": "parallel_corpus",
                "size": "35,833 sentence pairs",
                "license": "Research use",
                "institution": "Ghana universities",
                "year": 2021,
                "domains": ["general", "news", "literature"]
            },
            "twi_english_synthetic_50m": {
                "title": "Twi-English Parallel Synthetic Dataset (50M)",
                "description": "Large-scale synthetically generated Twi-English parallel corpus",
                "url": "https://huggingface.co/datasets/michsethowusu/twi-english-parallel-synthetic-50m",
                "type": "synthetic_parallel_corpus",
                "size": "50 million sentence pairs",
                "license": "Apache 2.0",
                "institution": "HuggingFace Community",
                "year": 2024,
                "domains": ["synthetic", "machine_translation"]
            },
            "twi_2_eng_corpus": {
                "title": "Twi-2-ENG Multiple Domain Parallel Corpus",
                "description": "Multiple domain Twi to English parallel corpus with digital dictionary",
                "url": "https://link.springer.com/article/10.1007/s10791-024-09451-8",
                "type": "parallel_corpus",
                "size": "Large-scale",
                "license": "Academic use",
                "institution": "Ghanaian Research Institutions",
                "year": 2024,
                "domains": ["multiple", "dictionary", "lexicon"]
            },
            "asante_twi_senti": {
                "title": "AsanteTwiSenti: Sentiment Dataset",
                "description": "Sentiment dataset of Ghanaian Asante Twi tweets in multilingual context",
                "url": "https://www.researchgate.net/publication/389835544_AsanteTwiSenti_A_Sentiment_Dataset_of_Ghanaian_Asante_Twi_Tweets_in_a_Multilingual_Context",
                "type": "sentiment_corpus",
                "size": "10,095 tweets (8,438 labeled)",
                "license": "Research use",
                "institution": "Ghanaian Universities",
                "year": 2024,
                "domains": ["social_media", "sentiment_analysis"]
            }
        },
        "audio_speech_resources": {
            "akan_ga_financial_dataset": {
                "title": "Akan (Twi) and Ga Financial Speech Dataset",
                "description": "104,000 utterances across Akan dialects and Ga with ~200 speakers per dialect",
                "url": "https://lacunafund.org/datasets/language/",
                "type": "speech_corpus",
                "size": "148 hours total speech",
                "speakers": "~200 per dialect",
                "license": "CC BY-NC-ND 4.0",
                "institution": "Asheshi University & Nokwary Technologies",
                "year": 2020,
                "domains": ["financial_services", "digital_inclusion"]
            },
            "uiowa_twi_audio": {
                "title": "University of Iowa Twi Audio Resources",
                "description": "Audio lessons, phonetics, and beginner resources for Twi",
                "url": "https://clcl.uiowa.edu/language-resources/twi-language-and-culture-resources",
                "type": "educational_audio",
                "size": "Multiple audio lessons",
                "license": "Educational use",
                "institution": "University of Iowa",
                "year": "Ongoing",
                "domains": ["education", "phonetics", "cultural_learning"]
            }
        },
        "dictionaries_lexicons": {
            "twi_digital_dictionary": {
                "title": "Twi Digital Dictionary",
                "description": "Digital dictionary with 1,367 words, available online and mobile app",
                "url": "https://k4all.org/project/twi-language/",
                "type": "digital_dictionary",
                "size": "1,367 words",
                "license": "Open access",
                "institution": "Knowledge 4 All Foundation",
                "year": 2020,
                "features": ["mobile_app", "online_access", "open_source"]
            },
            "christaller_dictionary": {
                "title": "Dictionary of the Asante and Fante Language (Christaller)",
                "description": "Traditional comprehensive dictionary by J.G. Christaller",
                "url": "https://aclanthology.org/2020.sltu-1.41.pdf",
                "type": "traditional_dictionary",
                "size": "Comprehensive",
                "license": "Public domain",
                "institution": "Historical/Academic",
                "year": 1881,
                "features": ["historical_reference", "comprehensive", "traditional"]
            }
        },
        "nlp_tools": {
            "nlp_ghana": {
                "title": "NLP Ghana Initiative",
                "description": "Open-source organization for Ghanaian language NLP development",
                "url": "https://nlpghana.org/",
                "type": "nlp_organization",
                "license": "Open source",
                "institution": "NLP Ghana",
                "year": "Ongoing",
                "tools": ["language_models", "machine_translation", "text_classification"]
            }
        }
    },
    "gaa": {
        "language_info": {
            "iso639_3": "gaa",
            "name": "Ga",
            "native_name": "Gã",
            "family": "Niger-Congo",
            "subfamily": "Kwa",
            "speakers": 1_000_000,
            "countries": ["Ghana"],
            "regions": ["Greater Accra"]
        },
        "audio_speech_resources": {
            "akan_ga_financial_dataset": {
                "title": "Akan and Ga Financial Speech Dataset",
                "description": "104,000 utterances including Ga with ~200 speakers",
                "url": "https://lacunafund.org/datasets/language/",
                "type": "speech_corpus",
                "size": "148 hours total (includes Ga portion)",
                "speakers": "~200 Ga speakers",
                "license": "CC BY-NC-ND 4.0",
                "institution": "Asheshi University & Nokwary Technologies",
                "year": 2020,
                "domains": ["financial_services", "digital_inclusion"]
            }
        },
        "research_resources": {
            "ug_linguistics_dept": {
                "title": "University of Ghana Linguistics Department",
                "description": "Research on Ghanaian languages including Ga",
                "url": "https://www.ug.edu.gh/linguistics/",
                "type": "academic_research",
                "institution": "University of Ghana",
                "year": "Ongoing",
                "focus": ["linguistics_research", "documentation", "analysis"]
            }
        },
        "cultural_resources": {
            "ga_cultural_documentation": {
                "title": "Ga Cultural and Language Documentation",
                "description": "Cultural context and traditional usage documentation",
                "type": "cultural_documentation",
                "institution": "Ghana Cultural Centers",
                "year": "Ongoing",
                "domains": ["oral_traditions", "ceremonial_language", "cultural_practices"]
            }
        }
    },
    "ewe": {
        "language_info": {
            "iso639_3": "ewe",
            "name": "Ewe",
            "native_name": "Eʋegbe",
            "family": "Niger-Congo",
            "subfamily": "Kwa",
            "speakers": 6_000_000,
            "countries": ["Ghana", "Togo", "Benin"],
            "regions": ["Volta Region (Ghana)", "Southern Togo"]
        },
        "audio_speech_resources": {
            "ug_speech_data": {
                "title": "UGSpeechData - Ewe Language Corpus",
                "description": "1000 hours of Ewe audio speech with 100 hours transcribed",
                "url": "https://hci-lab-ugspeechdata.github.io/speech_data_ghana_ug/",
                "type": "speech_corpus",
                "size": "1000 hours audio, 100 hours transcribed",
                "speakers": "Indigenous Ewe speakers",
                "license": "CC BY-NC-ND 4.0",
                "institution": "University of Ghana HCI Lab",
                "year": 2025,
                "domains": ["asr", "speech_synthesis", "linguistics"]
            },
            "ewe_audio_descriptions": {
                "title": "Ewe Cultural Image Audio Descriptions",
                "description": "Spoken descriptions of 1000 culturally relevant images",
                "url": "https://pure.ug.edu.gh/en/publications/advancing-automatic-speech-recognition-for-low-resource-ghanaian-",
                "type": "descriptive_speech",
                "size": "15-30 second audio clips",
                "license": "CC BY-NC-ND 4.0",
                "institution": "University of Ghana",
                "year": 2025,
                "domains": ["cultural_context", "image_description", "speech_recognition"]
            }
        },
        "text_corpora": {
            "french_ewe_parallel": {
                "title": "French-Ewe Parallel Corpus",
                "description": "Parallel corpus for machine translation between French and Ewe",
                "url": "https://www.freecodecamp.org/news/african-language-datasets-for-data-science-projects/",
                "type": "parallel_corpus",
                "size": "23,000 French-Ewe sentence pairs",
                "license": "Research use",
                "institution": "African NLP Research",
                "year": 2021,
                "domains": ["machine_translation", "news", "conversations", "web_content"]
            }
        },
        "research_resources": {
            "ug_speech_research": {
                "title": "University of Ghana Speech Recognition Research",
                "description": "Advancing automatic speech recognition for Ewe and other Ghanaian languages",
                "url": "https://www.sciencedirect.com/science/article/pii/S2352340925006043",
                "type": "academic_research",
                "institution": "University of Ghana",
                "year": 2025,
                "focus": ["asr", "low_resource_languages", "speech_technology"]
            },
            "github_ug_speech": {
                "title": "University of Ghana HCI Lab GitHub",
                "description": "Open source code and resources for Ghanaian language speech processing",
                "url": "https://github.com/HCI-LAB-UGSPEECHDATA",
                "type": "code_repository",
                "institution": "University of Ghana HCI Lab",
                "year": "Ongoing",
                "tools": ["speech_processing", "data_collection", "mobile_apps"]
            }
        }
    },
    "hau": {
        "language_info": {
            "iso639_3": "hau",
            "name": "Hausa",
            "native_name": "Harshen Hausa",
            "family": "Afroasiatic",
            "subfamily": "Chadic",
            "speakers": 70_000_000,
            "countries": ["Nigeria", "Niger", "Chad", "Ghana"],
            "regions": ["Northern Nigeria", "Southern Niger"]
        },
        "text_corpora": {
            "hausa_large_collection": {
                "title": "First Large Scale Collection of Diverse Hausa Datasets",
                "description": "Comprehensive collection of curated datasets for various Hausa NLP tasks",
                "url": "https://www.researchgate.net/publication/349335324_The_first_large_scale_collection_of_diverse_Hausa_language_datasets",
                "type": "diverse_text_corpus",
                "size": "Large-scale collection",
                "license": "Research use",
                "institution": "AfricaNLP/Bayero University Kano collaboration",
                "year": 2021,
                "domains": ["social_media", "formal_text", "websites", "news"]
            },
            "hausa_sentiment_lexicon": {
                "title": "Hausa Augmented Lexicon Sentiment Analysis Dataset",
                "description": "Comprehensive sentiment analysis dataset with 14,663 entries",
                "url": "https://www.sciencedirect.com/science/article/pii/S2352340924000969",
                "type": "sentiment_lexicon",
                "size": "14,663 entries (4,154 positive, 4,310 negative, 6,199 neutral)",
                "license": "Academic use",
                "institution": "Nigerian Universities",
                "year": 2024,
                "domains": ["sentiment_analysis", "social_media", "opinion_mining"]
            },
            "masakhaner_hausa": {
                "title": "MasakhaNER Hausa Named Entity Recognition",
                "description": "Largest NER corpus for African languages including Hausa",
                "url": "https://github.com/masakhane-io/masakhane-ner",
                "type": "ner_corpus",
                "size": "1,504 sentences for Hausa",
                "license": "Apache 2.0",
                "institution": "Masakhane Research Foundation",
                "year": 2021,
                "domains": ["named_entity_recognition", "news", "radio"]
            },
            "hausa_twitter_sentiment": {
                "title": "Hausa Twitter Sentiment Dataset",
                "description": "First large-scale human-annotated Twitter sentiment dataset for Hausa",
                "url": "https://lacunafund.org/2021-african-language-awardees/",
                "type": "social_media_sentiment",
                "size": "Large-scale Twitter dataset",
                "license": "Research use",
                "institution": "Lacuna Fund Awardees",
                "year": 2021,
                "domains": ["social_media", "sentiment_analysis", "twitter"]
            }
        },
        "audio_speech_resources": {
            "hausa_read_speech": {
                "title": "Hausa Language Read-Speech Dataset",
                "description": "47 hours of recorded Hausa audio speech by native speakers",
                "url": "https://www.sciencedirect.com/science/article/pii/S2352340922000324",
                "type": "read_speech_corpus",
                "size": "47 hours",
                "speakers": "Native Hausa speakers",
                "license": "Academic use",
                "institution": "Nile University of Nigeria",
                "year": 2022,
                "domains": ["asr", "speech_synthesis", "tts", "speech_to_text"]
            },
            "alffa_hausa": {
                "title": "ALFFA Hausa ASR Dataset",
                "description": "Automatic Speech Recognition dataset for Hausa",
                "url": "https://github.com/getalp/ALFFA_PUBLIC",
                "type": "asr_corpus",
                "size": "Part of multilingual ASR dataset",
                "license": "Academic use",
                "institution": "GETALP Laboratory",
                "year": 2017,
                "domains": ["automatic_speech_recognition", "multilingual"]
            },
            "commonvoice_hausa": {
                "title": "CommonVoice Hausa Dataset",
                "description": "Crowd-sourced voice dataset including Hausa",
                "url": "https://commonvoice.mozilla.org/",
                "type": "crowdsourced_speech",
                "size": "Part of 60+ languages",
                "license": "CC-0",
                "institution": "Mozilla Foundation",
                "year": "Ongoing",
                "domains": ["crowd_sourcing", "voice_recognition", "open_source"]
            }
        },
        "research_institutions": {
            "bayero_university": {
                "title": "Bayero University Kano (BUK) Hausa NLP Research",
                "description": "Leading research institution for Hausa language computational linguistics",
                "url": "https://www.buk.edu.ng/",
                "type": "academic_institution",
                "institution": "Bayero University Kano",
                "year": "Ongoing",
                "focus": ["hausa_nlp", "computational_linguistics", "language_technology"]
            },
            "hausa_nlp_initiative": {
                "title": "HausaNLP: Current Status and Future Directions",
                "description": "Comprehensive review of Hausa NLP research and challenges",
                "url": "https://arxiv.org/html/2505.14311",
                "type": "research_review",
                "institution": "Collaborative Research",
                "year": 2025,
                "focus": ["nlp_challenges", "future_directions", "resource_development"]
            }
        },
        "nlp_tools": {
            "africanlp_datasets": {
                "title": "AfricanNLP Public Datasets Repository",
                "description": "Repository for publicly available African language NLP datasets including Hausa",
                "url": "https://github.com/Andrews2017/africanlp-public-datasets",
                "type": "dataset_repository",
                "license": "Various open licenses",
                "institution": "African NLP Community",
                "year": "Ongoing",
                "tools": ["dataset_access", "nlp_resources", "collaborative_platform"]
            }
        },
        "funding_initiatives": {
            "lacuna_fund": {
                "title": "Lacuna Fund African Language Datasets",
                "description": "Funding initiative for African language dataset development including Hausa",
                "url": "https://lacunafund.org/datasets/language/",
                "type": "funding_initiative",
                "institution": "Lacuna Fund",
                "year": "2020-ongoing",
                "focus": ["dataset_funding", "african_languages", "nlp_development"]
            }
        }
    }
}