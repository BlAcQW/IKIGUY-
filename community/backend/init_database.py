"""
Initialize African Language Community Platform database.

Populates the database with language families, subfamilies, and supported languages.
"""

import asyncio
from datetime import datetime
from bson import ObjectId
import logging

from database import connect_to_mongo, get_database
from models.language_models import LanguageFamily, LanguageSubfamily, Language

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Language family data structure
LANGUAGE_FAMILIES = {
    "niger-congo": {
        "name": "niger-congo",
        "display_name": "Niger-Congo",
        "description": "The largest language family in Africa, covering much of sub-Saharan Africa",
        "geographic_region": ["West Africa", "Central Africa", "East Africa", "Southern Africa"],
        "shared_features": {
            "noun_classes": True,
            "verb_extensions": True,
            "tone": True,
            "agglutination": True
        },
        "speaker_count_estimate": 700000000,
        "subfamilies": {
            "kwa": {
                "name": "kwa",
                "display_name": "Kwa",
                "description": "Languages primarily spoken in Ghana, Togo, and Benin",
                "geographic_region": ["Ghana", "Togo", "Benin", "Ivory Coast"],
                "shared_features": {
                    "atr_vowel_harmony": True,
                    "serial_verb_constructions": True,
                    "terraced_tone_systems": True,
                    "noun_class_systems": True
                },
                "transfer_learning_efficiency": {
                    "twi_to_fante": 0.85,
                    "twi_to_ga": 0.72,
                    "fante_to_ga": 0.68,
                    "ewe_to_ga": 0.65
                },
                "languages": [
                    {
                        "code": "twi",
                        "name": "Twi (Akan)",
                        "native_name": "Twi",
                        "alternative_names": ["Akan", "Asante Twi", "Akuapem Twi"],
                        "countries": ["Ghana"],
                        "regions": ["Ashanti", "Eastern Region", "Brong-Ahafo"],
                        "speaker_count": 9500000,
                        "total_speakers": 11000000,
                        "linguistic_features": {
                            "tone_levels": 2,
                            "atr_vowel_harmony": True,
                            "serial_verbs": True,
                            "noun_classes": 8
                        },
                        "phonetic_inventory": {
                            "vowels": 10,
                            "consonants": 22,
                            "tones": ["high", "low"]
                        },
                        "tonal_system": {
                            "levels": 2,
                            "contour_tones": False,
                            "grammatical_tone": True
                        },
                        "cultural_context": {
                            "traditional_greetings": ["Akwaaba", "Wo ho te sen?"],
                            "cultural_values": ["respect_for_elders", "community_harmony"],
                            "ceremonial_usage": ["naming_ceremonies", "traditional_festivals"]
                        },
                        "dialects": ["Asante", "Akuapem", "Fante", "Kwahu"],
                        "data_tier": "tier-1"
                    },
                    {
                        "code": "gaa",
                        "name": "Ga",
                        "native_name": "Gã",
                        "alternative_names": ["Ga-Dangme", "Accra"],
                        "countries": ["Ghana"],
                        "regions": ["Greater Accra Region"],
                        "speaker_count": 745000,
                        "total_speakers": 1000000,
                        "linguistic_features": {
                            "tone_levels": 2,
                            "atr_vowel_harmony": False,
                            "serial_verbs": True,
                            "noun_classes": 0
                        },
                        "cultural_context": {
                            "traditional_greetings": ["Baajo", "Woye ke?"],
                            "cultural_significance": "Language of Ghana's capital city"
                        },
                        "dialects": ["Accra Ga", "Tema Ga"],
                        "data_tier": "tier-2"
                    },
                    {
                        "code": "ewe",
                        "name": "Ewe",
                        "native_name": "Eʋegbe",
                        "alternative_names": ["Ewegbe", "Eve"],
                        "countries": ["Ghana", "Togo", "Benin"],
                        "regions": ["Volta Region", "Maritime Region"],
                        "speaker_count": 4500000,
                        "total_speakers": 6000000,
                        "linguistic_features": {
                            "tone_levels": 2,
                            "atr_vowel_harmony": False,
                            "serial_verbs": True
                        },
                        "cultural_context": {
                            "traditional_greetings": ["Ndi", "Efɔa?"],
                            "cross_border_language": True
                        },
                        "dialects": ["Anlo", "Ho", "Kpando"],
                        "data_tier": "tier-2"
                    }
                ]
            },
            "yoruboid": {
                "name": "yoruboid",
                "display_name": "Yoruboid",
                "description": "Languages primarily spoken in Nigeria and Benin",
                "geographic_region": ["Nigeria", "Benin", "Togo"],
                "shared_features": {
                    "nasal_vowels": True,
                    "three_tone_system": True,
                    "verbal_serialization": True
                },
                "languages": [
                    {
                        "code": "yor",
                        "name": "Yoruba",
                        "native_name": "Yorùbá",
                        "alternative_names": ["Yorùbá"],
                        "countries": ["Nigeria", "Benin", "Togo"],
                        "regions": ["Southwest Nigeria", "South Benin"],
                        "speaker_count": 28000000,
                        "total_speakers": 35000000,
                        "linguistic_features": {
                            "tone_levels": 3,
                            "nasal_vowels": True,
                            "serial_verbs": True,
                            "vowel_harmony": False
                        },
                        "phonetic_inventory": {
                            "vowels": 12,
                            "consonants": 18,
                            "tones": ["high", "mid", "low"]
                        },
                        "tonal_system": {
                            "levels": 3,
                            "contour_tones": True,
                            "grammatical_tone": True
                        },
                        "cultural_context": {
                            "traditional_greetings": ["Bawo", "E kaaro", "E ku aaro"],
                            "religious_significance": "Language of Yoruba traditional religion",
                            "diaspora_communities": ["Brazil", "Cuba", "Trinidad"]
                        },
                        "dialects": ["Lagos", "Ibadan", "Oyo", "Egba"],
                        "data_tier": "tier-1"
                    }
                ]
            },
            "bantu": {
                "name": "bantu",
                "display_name": "Bantu",
                "description": "Large subfamily covering much of Central, Eastern, and Southern Africa",
                "geographic_region": ["Central Africa", "East Africa", "Southern Africa"],
                "shared_features": {
                    "noun_class_prefixes": True,
                    "agglutination": True,
                    "subject_object_concord": True
                },
                "languages": [
                    {
                        "code": "swa",
                        "name": "Swahili",
                        "native_name": "Kiswahili",
                        "alternative_names": ["Kiswahili"],
                        "countries": ["Kenya", "Tanzania", "Uganda", "DRC"],
                        "regions": ["East Africa"],
                        "speaker_count": 16000000,
                        "total_speakers": 100000000,
                        "linguistic_features": {
                            "tone_levels": 0,  # Non-tonal
                            "noun_classes": 18,
                            "agglutination": True,
                            "arabic_loanwords": True
                        },
                        "cultural_context": {
                            "traditional_greetings": ["Hujambo", "Habari"],
                            "lingua_franca": True,
                            "official_language": ["Kenya", "Tanzania", "Uganda"]
                        },
                        "dialects": ["Standard Swahili", "Coastal", "Congolese"],
                        "data_tier": "tier-1"
                    },
                    {
                        "code": "xho",
                        "name": "Xhosa",
                        "native_name": "isiXhosa",
                        "alternative_names": ["isiXhosa"],
                        "countries": ["South Africa"],
                        "regions": ["Eastern Cape", "Western Cape"],
                        "speaker_count": 8200000,
                        "total_speakers": 8200000,
                        "linguistic_features": {
                            "click_consonants": True,
                            "noun_classes": 16,
                            "tone_levels": 2
                        },
                        "cultural_context": {
                            "traditional_greetings": ["Molo", "Sawubona"],
                            "official_language": "South Africa"
                        },
                        "dialects": ["Standard", "Mpondo", "Mpondomise"],
                        "data_tier": "tier-2"
                    }
                ]
            }
        }
    },
    "afroasiatic": {
        "name": "afroasiatic",
        "display_name": "Afroasiatic",
        "description": "Language family spanning North Africa, Horn of Africa, and parts of West Africa",
        "geographic_region": ["North Africa", "Horn of Africa", "West Africa"],
        "shared_features": {
            "semitic_root_system": True,
            "pharyngeal_consonants": True,
            "vso_word_order": True
        },
        "speaker_count_estimate": 400000000,
        "subfamilies": {
            "chadic": {
                "name": "chadic",
                "display_name": "Chadic",
                "description": "Languages primarily spoken in Nigeria, Niger, Chad, and Cameroon",
                "geographic_region": ["Nigeria", "Niger", "Chad", "Cameroon"],
                "shared_features": {
                    "tone_languages": True,
                    "verb_aspect_system": True
                },
                "languages": [
                    {
                        "code": "hau",
                        "name": "Hausa",
                        "native_name": "Harshen Hausa",
                        "alternative_names": ["Hausa"],
                        "countries": ["Nigeria", "Niger", "Ghana", "Chad"],
                        "regions": ["Northern Nigeria", "Southern Niger"],
                        "speaker_count": 44000000,
                        "total_speakers": 70000000,
                        "linguistic_features": {
                            "tone_levels": 3,
                            "arabic_script": True,
                            "latin_script": True
                        },
                        "cultural_context": {
                            "traditional_greetings": ["Sannu", "Ina kwana"],
                            "trade_language": True,
                            "lingua_franca": "West Africa"
                        },
                        "dialects": ["Standard", "Kano", "Sokoto"],
                        "data_tier": "tier-2"
                    }
                ]
            },
            "cushitic": {
                "name": "cushitic",
                "display_name": "Cushitic",
                "description": "Languages primarily spoken in the Horn of Africa",
                "geographic_region": ["Ethiopia", "Somalia", "Eritrea", "Kenya"],
                "languages": [
                    {
                        "code": "amh",
                        "name": "Amharic",
                        "native_name": "አማርኛ",
                        "alternative_names": ["Amharic", "Amarigna"],
                        "countries": ["Ethiopia"],
                        "regions": ["Central Ethiopia"],
                        "speaker_count": 21600000,
                        "total_speakers": 25000000,
                        "linguistic_features": {
                            "ethiopic_script": True,
                            "semitic_features": True,
                            "ejective_consonants": True
                        },
                        "writing_systems": ["Ethiopic"],
                        "cultural_context": {
                            "official_language": "Ethiopia",
                            "liturgical_usage": True
                        },
                        "data_tier": "tier-3"
                    }
                ]
            }
        }
    }
}


async def init_language_families():
    """Initialize language families in the database."""
    db = get_database()

    logger.info("Initializing language families...")

    for family_key, family_data in LANGUAGE_FAMILIES.items():
        # Create language family
        family_doc = {
            "name": family_data["name"],
            "display_name": family_data["display_name"],
            "description": family_data["description"],
            "geographic_region": family_data["geographic_region"],
            "subfamilies": list(family_data["subfamilies"].keys()),
            "shared_features": family_data["shared_features"],
            "speaker_count_estimate": family_data.get("speaker_count_estimate"),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # Insert or update family
        existing_family = await db.language_families.find_one({"name": family_data["name"]})
        if existing_family:
            await db.language_families.update_one(
                {"name": family_data["name"]},
                {"$set": family_doc}
            )
            family_id = existing_family["_id"]
            logger.info(f"Updated language family: {family_data['display_name']}")
        else:
            result = await db.language_families.insert_one(family_doc)
            family_id = result.inserted_id
            logger.info(f"Created language family: {family_data['display_name']}")

        # Create subfamilies
        for subfamily_key, subfamily_data in family_data["subfamilies"].items():
            subfamily_doc = {
                "family_id": family_id,
                "name": subfamily_data["name"],
                "display_name": subfamily_data["display_name"],
                "description": subfamily_data["description"],
                "geographic_region": subfamily_data["geographic_region"],
                "languages": [lang["code"] for lang in subfamily_data["languages"]],
                "shared_features": subfamily_data.get("shared_features", {}),
                "transfer_learning_efficiency": subfamily_data.get("transfer_learning_efficiency", {}),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            # Insert or update subfamily
            existing_subfamily = await db.language_subfamilies.find_one({
                "family_id": family_id,
                "name": subfamily_data["name"]
            })

            if existing_subfamily:
                await db.language_subfamilies.update_one(
                    {"family_id": family_id, "name": subfamily_data["name"]},
                    {"$set": subfamily_doc}
                )
                subfamily_id = existing_subfamily["_id"]
                logger.info(f"Updated subfamily: {subfamily_data['display_name']}")
            else:
                result = await db.language_subfamilies.insert_one(subfamily_doc)
                subfamily_id = result.inserted_id
                logger.info(f"Created subfamily: {subfamily_data['display_name']}")

            # Create languages
            for language_data in subfamily_data["languages"]:
                language_doc = {
                    "subfamily_id": subfamily_id,
                    "code": language_data["code"],
                    "name": language_data["name"],
                    "native_name": language_data["native_name"],
                    "alternative_names": language_data.get("alternative_names", []),
                    "countries": language_data.get("countries", []),
                    "regions": language_data.get("regions", []),
                    "speaker_count": language_data.get("speaker_count"),
                    "total_speakers": language_data.get("total_speakers"),
                    "linguistic_features": language_data.get("linguistic_features", {}),
                    "phonetic_inventory": language_data.get("phonetic_inventory", {}),
                    "tonal_system": language_data.get("tonal_system"),
                    "writing_systems": language_data.get("writing_systems", ["Latin"]),
                    "cultural_context": language_data.get("cultural_context", {}),
                    "dialects": language_data.get("dialects", []),
                    "data_tier": language_data.get("data_tier", "tier-3"),
                    "voice_support_level": "basic",
                    "training_data_availability": {},
                    "active_contributors": 0,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }

                # Insert or update language
                existing_language = await db.languages.find_one({"code": language_data["code"]})
                if existing_language:
                    await db.languages.update_one(
                        {"code": language_data["code"]},
                        {"$set": language_doc}
                    )
                    logger.info(f"Updated language: {language_data['name']}")
                else:
                    await db.languages.insert_one(language_doc)
                    logger.info(f"Created language: {language_data['name']}")


async def main():
    """Main initialization function."""
    logger.info("Starting African Language Community Platform database initialization...")

    try:
        # Connect to database
        await connect_to_mongo()
        logger.info("Connected to MongoDB")

        # Initialize language families
        await init_language_families()

        logger.info("Database initialization completed successfully!")

    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())