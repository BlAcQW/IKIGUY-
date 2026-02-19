#!/usr/bin/env python3
"""
African Language Families Enhancement Populator
Adds detailed linguistic, cultural, and AI-training data to African language families
"""

import asyncio
import sys
import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from core.config import get_settings
from african_languages_enhancement import AFRICAN_LANGUAGE_ENHANCEMENTS, AFRICAN_LANGUAGE_TRANSFER_LEARNING

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AfricanLanguageEnhancer:
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.db = None

    async def connect_database(self):
        """Connect to MongoDB database"""
        try:
            self.client = AsyncIOMotorClient(self.settings.MONGODB_URL)
            self.db = self.client[self.settings.DATABASE_NAME]
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

    async def enhance_african_families(self):
        """Add enhanced data to African language families"""
        try:
            enhanced_count = 0

            for family_key, enhancement_data in AFRICAN_LANGUAGE_ENHANCEMENTS.items():
                # Update family document with enhanced data
                family_update = {
                    "$set": {
                        "linguistic_features": enhancement_data.get("linguistic_features", {}),
                        "cultural_context": enhancement_data.get("cultural_context", {}),
                        "ai_learning_data": enhancement_data.get("ai_learning_data", {}),
                        "endangerment_data": enhancement_data.get("endangerment_data", {}),
                        "revitalization_efforts": enhancement_data.get("revitalization_efforts", {}),
                        "updated_at": datetime.utcnow()
                    }
                }

                result = await self.db.language_families.update_one(
                    {"name": family_key},
                    family_update
                )

                if result.modified_count > 0:
                    enhanced_count += 1
                    logger.info(f"Enhanced {family_key} family data")

            logger.info(f"Enhanced {enhanced_count} African language families")
            return enhanced_count

        except Exception as e:
            logger.error(f"Error enhancing African families: {e}")
            raise

    async def add_enhanced_languages(self):
        """Add new enhanced language entries"""
        try:
            added_languages = 0

            for family_key, family_data in AFRICAN_LANGUAGE_ENHANCEMENTS.items():
                enhanced_languages = family_data.get("enhanced_languages", {})

                if not enhanced_languages:
                    continue

                # Get family document to get subfamily mappings
                family_doc = await self.db.language_families.find_one({"name": family_key})
                if not family_doc:
                    logger.warning(f"Family {family_key} not found")
                    continue

                for lang_key, lang_data in enhanced_languages.items():
                    # Find appropriate subfamily
                    subfamily_doc = await self.db.language_subfamilies.find_one({
                        "family_id": family_doc["_id"],
                        "name": {"$regex": lang_data.get("subfamily_hint", ""), "$options": "i"}
                    })

                    if not subfamily_doc:
                        # Use first subfamily as fallback
                        subfamily_doc = await self.db.language_subfamilies.find_one({
                            "family_id": family_doc["_id"]
                        })

                    if not subfamily_doc:
                        logger.warning(f"No subfamily found for {lang_key}")
                        continue

                    # Check if language already exists
                    existing_lang = await self.db.languages.find_one({
                        "code": lang_data["iso639_3"]
                    })

                    if existing_lang:
                        # Update existing language with enhanced data
                        language_update = {
                            "$set": {
                                "tonal_system": lang_data.get("tonal_system"),
                                "click_system": lang_data.get("click_system"),
                                "script_features": lang_data.get("script_features"),
                                "cultural_features": lang_data.get("cultural_features"),
                                "endangerment_status": lang_data.get("endangerment_status"),
                                "threats": lang_data.get("threats", []),
                                "revitalization_efforts": lang_data.get("revitalization_efforts", []),
                                "updated_at": datetime.utcnow()
                            }
                        }

                        await self.db.languages.update_one(
                            {"_id": existing_lang["_id"]},
                            language_update
                        )
                        logger.info(f"Enhanced existing language: {lang_data['name']}")

                    else:
                        # Create new language document
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
                            "tonal_system": lang_data.get("tonal_system"),
                            "click_system": lang_data.get("click_system"),
                            "script_features": lang_data.get("script_features"),
                            "writing_systems": lang_data["writing_system"],
                            "cultural_context": {},
                            "cultural_features": lang_data.get("cultural_features", {}),
                            "dialects": lang_data.get("dialects", []),
                            "endangerment_status": lang_data.get("endangerment_status", "stable"),
                            "threats": lang_data.get("threats", []),
                            "revitalization_efforts": lang_data.get("revitalization_efforts", []),
                            "data_tier": "tier-2",
                            "voice_support_level": "enhanced",
                            "training_data_availability": {},
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow(),
                            "last_contribution": None,
                            "active_contributors": 0
                        }

                        await self.db.languages.insert_one(language_doc)
                        added_languages += 1
                        logger.info(f"Added new enhanced language: {lang_data['name']}")

            logger.info(f"Added {added_languages} enhanced languages")
            return added_languages

        except Exception as e:
            logger.error(f"Error adding enhanced languages: {e}")
            raise

    async def add_transfer_learning_data(self):
        """Add cross-linguistic transfer learning efficiency data"""
        try:
            # Create collection for transfer learning data if it doesn't exist
            transfer_learning_doc = {
                "_id": ObjectId(),
                "type": "african_language_transfer_efficiency",
                "within_family_efficiency": AFRICAN_LANGUAGE_TRANSFER_LEARNING["within_family_efficiency"],
                "cross_family_efficiency": AFRICAN_LANGUAGE_TRANSFER_LEARNING["cross_family_efficiency"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            # Remove existing transfer learning data
            await self.db.transfer_learning_data.delete_many({
                "type": "african_language_transfer_efficiency"
            })

            # Insert new data
            await self.db.transfer_learning_data.insert_one(transfer_learning_doc)
            logger.info("Added transfer learning efficiency data")

            return 1

        except Exception as e:
            logger.error(f"Error adding transfer learning data: {e}")
            raise

    async def create_african_language_indexes(self):
        """Create specialized indexes for African language features"""
        try:
            indexes_created = 0

            # Indexes for enhanced language features
            language_indexes = [
                ("endangerment_status", {}),
                ("tonal_system.is_tonal", {}),
                ("click_system.total_consonants", {}),
                ("cultural_features.oral_literature", {}),
                ([("endangerment_status", 1), ("speaker_count", -1)], {}),
                ([("tonal_system.is_tonal", 1), ("subfamily_id", 1)], {})
            ]

            for index_spec, options in language_indexes:
                try:
                    await self.db.languages.create_index(index_spec, **options)
                    indexes_created += 1
                except Exception as e:
                    if "already exists" in str(e) or "IndexKeySpecsConflict" in str(e):
                        logger.debug(f"Index on {index_spec} already exists, skipping")
                    else:
                        logger.warning(f"Failed to create index on {index_spec}: {e}")

            # Indexes for family enhancements
            family_indexes = [
                ("linguistic_features.tonal_system.is_tonal", {}),
                ("endangerment_data.threat_level", {}),
                ("cultural_context.oral_traditions", {})
            ]

            for index_spec, options in family_indexes:
                try:
                    await self.db.language_families.create_index(index_spec, **options)
                    indexes_created += 1
                except Exception as e:
                    if "already exists" in str(e) or "IndexKeySpecsConflict" in str(e):
                        logger.debug(f"Index on {index_spec} already exists, skipping")
                    else:
                        logger.warning(f"Failed to create index on {index_spec}: {e}")

            logger.info(f"Created {indexes_created} new specialized indexes")
            return indexes_created

        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            raise

    async def generate_enhancement_summary(self):
        """Generate summary of African language enhancements"""
        try:
            # Count enhanced families
            enhanced_families = await self.db.language_families.count_documents({
                "linguistic_features": {"$exists": True}
            })

            # Count languages with tonal systems
            tonal_languages = await self.db.languages.count_documents({
                "tonal_system.is_tonal": True
            })

            # Count endangered languages
            endangered_languages = await self.db.languages.count_documents({
                "endangerment_status": {"$in": ["endangered", "severely endangered", "critically endangered"]}
            })

            # Count languages with click systems
            click_languages = await self.db.languages.count_documents({
                "click_system": {"$exists": True}
            })

            # Get transfer learning data
            transfer_data = await self.db.transfer_learning_data.find_one({
                "type": "african_language_transfer_efficiency"
            })

            summary = {
                "enhanced_families": enhanced_families,
                "tonal_languages": tonal_languages,
                "endangered_languages": endangered_languages,
                "click_languages": click_languages,
                "has_transfer_learning_data": transfer_data is not None,
                "enhancement_timestamp": datetime.utcnow()
            }

            logger.info("African Language Enhancement Summary:")
            logger.info(f"  Enhanced Families: {summary['enhanced_families']}")
            logger.info(f"  Tonal Languages: {summary['tonal_languages']}")
            logger.info(f"  Endangered Languages: {summary['endangered_languages']}")
            logger.info(f"  Click Languages: {summary['click_languages']}")
            logger.info(f"  Transfer Learning Data: {'Yes' if summary['has_transfer_learning_data'] else 'No'}")

            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            raise

    async def enhance_all(self):
        """Run all enhancement operations"""
        try:
            await self.connect_database()

            logger.info("Starting African language families enhancement...")

            # Enhance family data
            enhanced_families = await self.enhance_african_families()

            # Add enhanced languages
            added_languages = await self.add_enhanced_languages()

            # Add transfer learning data
            transfer_data_added = await self.add_transfer_learning_data()

            # Create specialized indexes
            indexes_created = await self.create_african_language_indexes()

            # Generate summary
            summary = await self.generate_enhancement_summary()

            summary.update({
                "operations_completed": {
                    "enhanced_families": enhanced_families,
                    "added_languages": added_languages,
                    "transfer_data_added": transfer_data_added,
                    "indexes_created": indexes_created
                }
            })

            logger.info("African language enhancement completed successfully!")
            return summary

        except Exception as e:
            logger.error(f"Enhancement failed: {e}")
            raise
        finally:
            await self.close_database()

async def main():
    """Main execution function"""
    try:
        enhancer = AfricanLanguageEnhancer()
        summary = await enhancer.enhance_all()

        print("\n" + "="*60)
        print("AFRICAN LANGUAGE FAMILIES ENHANCEMENT COMPLETE")
        print("="*60)
        print(f"✅ Enhanced African Families: {summary['enhanced_families']}")
        print(f"✅ Added Enhanced Languages: {summary['operations_completed']['added_languages']}")
        print(f"✅ Tonal Languages: {summary['tonal_languages']}")
        print(f"✅ Endangered Languages: {summary['endangered_languages']}")
        print(f"✅ Click Languages: {summary['click_languages']}")
        print(f"✅ Transfer Learning Data: {'Added' if summary['has_transfer_learning_data'] else 'Missing'}")
        print(f"✅ Specialized Indexes: {summary['operations_completed']['indexes_created']}")
        print("\n🌍 African Language Community Platform enhanced with detailed linguistic data!")

    except Exception as e:
        logger.error(f"Enhancement script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())