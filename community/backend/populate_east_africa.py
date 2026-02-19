#!/usr/bin/env python3
"""
East Africa Major Languages Populator
Establishes East Africa as fifth flagship region
Adding 300M+ speakers with comprehensive regional lingua francas and national languages
"""

import asyncio
import sys
import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from core.config import get_settings
from east_africa_major_languages import EAST_AFRICA_MAJOR_LANGUAGES, EAST_AFRICA_SUMMARY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EastAfricaPopulator:
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

    async def ensure_required_subfamilies_exist(self):
        """Ensure required subfamilies exist for East African languages"""
        try:
            subfamilies_to_create = [
                {
                    "name": "bantu",
                    "display_name": "Bantu",
                    "family_name": "niger-congo",
                    "description": "East African Bantu languages including Swahili, Kikuyu, Kinyarwanda, Kirundi",
                    "languages": ["swa", "kik", "kin", "run"]
                },
                {
                    "name": "semitic",
                    "display_name": "Semitic",
                    "family_name": "afroasiatic",
                    "description": "East African Semitic languages including Amharic, Tigrinya",
                    "languages": ["amh", "tir"]
                },
                {
                    "name": "cushitic",
                    "display_name": "Cushitic",
                    "family_name": "afroasiatic",
                    "description": "East African Cushitic languages including Oromo, Somali",
                    "languages": ["orm", "som"]
                }
            ]

            created_count = 0
            for subfamily_info in subfamilies_to_create:
                # Check if subfamily exists
                existing = await self.db.language_subfamilies.find_one({
                    "name": subfamily_info["name"]
                })

                if existing:
                    # Update existing subfamily with East African languages
                    update_languages = list(set(existing.get("languages", []) + subfamily_info["languages"]))
                    await self.db.language_subfamilies.update_one(
                        {"_id": existing["_id"]},
                        {"$set": {"languages": update_languages, "updated_at": datetime.utcnow()}}
                    )
                    logger.info(f"Updated {subfamily_info['display_name']} subfamily with East African languages")
                else:
                    # Find parent family
                    parent_family = await self.db.language_families.find_one({
                        "name": subfamily_info["family_name"]
                    })

                    if parent_family:
                        subfamily_doc = {
                            "_id": ObjectId(),
                            "family_id": parent_family["_id"],
                            "name": subfamily_info["name"],
                            "display_name": subfamily_info["display_name"],
                            "description": subfamily_info["description"],
                            "geographic_region": ["East Africa"],
                            "languages": subfamily_info["languages"],
                            "shared_features": {"speakers": 0, "total_languages": {}},
                            "transfer_learning_efficiency": {},
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }

                        await self.db.language_subfamilies.insert_one(subfamily_doc)
                        logger.info(f"Created {subfamily_info['display_name']} subfamily")
                        created_count += 1

            return created_count
        except Exception as e:
            logger.error(f"Error ensuring subfamilies exist: {e}")
            return 0

    async def add_east_african_language(self, language_code, language_data):
        """Add an East African language to the database"""
        try:
            # Check if language already exists
            existing_language = await self.db.languages.find_one({"code": language_code})
            if existing_language:
                logger.info(f"Language {language_code} already exists, updating with East African data")
                return await self.update_existing_language_data_sources(language_code, language_data)

            # Get subfamily information
            subfamily_name = language_data["language_info"]["subfamily"].lower()

            subfamily = await self.db.language_subfamilies.find_one({
                "name": subfamily_name
            })

            if not subfamily:
                logger.error(f"Subfamily {subfamily_name} not found for {language_code}")
                return False

            # Prepare data sources
            formatted_sources = {}
            total_resources = 0

            for category, resources in language_data.items():
                if category == "language_info":
                    continue

                formatted_sources[category] = {}
                for resource_key, resource_data in resources.items():
                    formatted_sources[category][resource_key] = {
                        "title": resource_data["title"],
                        "description": resource_data["description"],
                        "url": resource_data.get("url", ""),
                        "type": resource_data["type"],
                        "size": resource_data.get("size", ""),
                        "license": resource_data.get("license", ""),
                        "institution": resource_data["institution"],
                        "year": resource_data["year"],
                        "domains": resource_data.get("domains", []),
                        "features": resource_data.get("features", []),
                        "tools": resource_data.get("tools", []),
                        "focus": resource_data.get("focus", []),
                        "speakers": resource_data.get("speakers", ""),
                        "added_date": datetime.utcnow()
                    }
                    total_resources += 1

            # Create language document
            language_doc = {
                "_id": ObjectId(),
                "code": language_code,
                "name": language_data["language_info"]["name"],
                "native_name": language_data["language_info"]["native_name"],
                "family": language_data["language_info"]["family"],
                "subfamily": language_data["language_info"]["subfamily"],
                "subfamily_id": subfamily["_id"],
                "family_id": subfamily["family_id"],
                "speakers": language_data["language_info"]["speakers"],
                "countries": language_data["language_info"]["countries"],
                "regions": language_data["language_info"]["regions"],
                "government_sponsored": language_data["language_info"].get("government_sponsored", False),
                "status": language_data["language_info"].get("status", ""),
                "data_sources": formatted_sources,
                "data_sources_count": total_resources,
                "data_sources_last_updated": datetime.utcnow(),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            # Insert language
            await self.db.languages.insert_one(language_doc)
            logger.info(f"Added {language_data['language_info']['name']} ({language_code}) with {total_resources} data sources and {language_data['language_info']['speakers']:,} speakers")

            return True

        except Exception as e:
            logger.error(f"Error adding language {language_code}: {e}")
            return False

    async def update_existing_language_data_sources(self, language_code, language_data):
        """Update existing language with East African data sources"""
        try:
            # Prepare data sources
            formatted_sources = {}
            total_resources = 0

            for category, resources in language_data.items():
                if category == "language_info":
                    continue

                formatted_sources[category] = {}
                for resource_key, resource_data in resources.items():
                    formatted_sources[category][resource_key] = {
                        "title": resource_data["title"],
                        "description": resource_data["description"],
                        "url": resource_data.get("url", ""),
                        "type": resource_data["type"],
                        "size": resource_data.get("size", ""),
                        "license": resource_data.get("license", ""),
                        "institution": resource_data["institution"],
                        "year": resource_data["year"],
                        "domains": resource_data.get("domains", []),
                        "features": resource_data.get("features", []),
                        "tools": resource_data.get("tools", []),
                        "focus": resource_data.get("focus", []),
                        "speakers": resource_data.get("speakers", ""),
                        "added_date": datetime.utcnow()
                    }
                    total_resources += 1

            # Update the language document
            update_data = {
                "$set": {
                    "speakers": language_data["language_info"]["speakers"],
                    "family": language_data["language_info"]["family"],
                    "subfamily": language_data["language_info"]["subfamily"],
                    "regions": language_data["language_info"]["regions"],
                    "government_sponsored": language_data["language_info"].get("government_sponsored", False),
                    "status": language_data["language_info"].get("status", ""),
                    "data_sources": formatted_sources,
                    "data_sources_count": total_resources,
                    "data_sources_last_updated": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }

            result = await self.db.languages.update_one(
                {"code": language_code},
                update_data
            )

            if result.modified_count > 0:
                logger.info(f"Updated {language_code} with {total_resources} data sources and {language_data['language_info']['speakers']:,} speakers")
                return True
            else:
                logger.warning(f"No changes made to {language_code}")
                return False

        except Exception as e:
            logger.error(f"Error updating {language_code}: {e}")
            return False

    async def create_east_africa_collection(self):
        """Create a comprehensive collection for East African languages"""
        try:
            collection_doc = {
                "_id": ObjectId(),
                "collection_type": "east_africa_major_languages",
                "description": "Major East African languages - fifth flagship region",
                "languages_covered": list(EAST_AFRICA_MAJOR_LANGUAGES.keys()),
                "total_languages": len(EAST_AFRICA_MAJOR_LANGUAGES),
                "summary": EAST_AFRICA_SUMMARY,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "data_sources": EAST_AFRICA_MAJOR_LANGUAGES
            }

            # Remove existing collection document
            await self.db.data_source_collections.delete_many({
                "collection_type": "east_africa_major_languages"
            })

            # Insert new collection document
            await self.db.data_source_collections.insert_one(collection_doc)
            logger.info("Created East Africa major languages collection")
            return True

        except Exception as e:
            logger.error(f"Error creating East Africa collection: {e}")
            return False

    async def generate_east_africa_summary(self):
        """Generate summary of East African language expansion"""
        try:
            # Get all East African languages
            east_african_countries = ['Kenya', 'Tanzania', 'Uganda', 'Ethiopia', 'Rwanda', 'Burundi',
                                    'Somalia', 'Eritrea', 'Djibouti', 'South Sudan']

            all_east_languages = await self.db.languages.find({
                "countries": {"$in": east_african_countries}
            }, {
                "code": 1, "name": 1, "speakers": 1, "countries": 1, "subfamily": 1,
                "data_sources_count": 1, "government_sponsored": 1, "family": 1
            }).sort("speakers", -1).to_list(None)

            summary = {
                "total_east_african_languages": len(all_east_languages),
                "total_speakers": sum(lang.get("speakers", 0) for lang in all_east_languages),
                "languages_with_data_sources": len([lang for lang in all_east_languages
                                                  if lang.get("data_sources_count", 0) > 0]),
                "total_data_sources": sum(lang.get("data_sources_count", 0) for lang in all_east_languages),
                "government_sponsored_count": len([lang for lang in all_east_languages
                                                 if lang.get("government_sponsored", False)]),
                "top_10_by_speakers": [],
                "country_coverage": {},
                "family_distribution": {},
                "enhancement_status": "East Africa established as fifth flagship region"
            }

            # Get top 10 by speakers
            for lang in all_east_languages[:10]:
                summary["top_10_by_speakers"].append({
                    "code": lang["code"],
                    "name": lang["name"],
                    "speakers": lang.get("speakers", 0),
                    "countries": lang.get("countries", []),
                    "family": lang.get("family", "Unknown")
                })

            # Count by country and family
            for lang in all_east_languages:
                # Country coverage
                for country in lang.get("countries", []):
                    if country in east_african_countries:
                        if country not in summary["country_coverage"]:
                            summary["country_coverage"][country] = 0
                        summary["country_coverage"][country] += 1

                # Family distribution
                family = lang.get("family", "Unknown")
                if family not in summary["family_distribution"]:
                    summary["family_distribution"][family] = 0
                summary["family_distribution"][family] += 1

            summary["completion_timestamp"] = datetime.utcnow()
            return summary

        except Exception as e:
            logger.error(f"Error generating East Africa summary: {e}")
            return None

    async def populate_east_africa_languages(self):
        """Populate all major East African languages"""
        try:
            await self.connect_database()

            logger.info("Starting East Africa major languages population...")

            # Ensure required subfamilies exist
            subfamilies_created = await self.ensure_required_subfamilies_exist()

            added_languages = 0
            updated_languages = 0
            total_sources = 0

            # Add each East African language
            for lang_code, lang_data in EAST_AFRICA_MAJOR_LANGUAGES.items():
                # Check if it's an update or addition
                existing = await self.db.languages.find_one({"code": lang_code})

                success = await self.add_east_african_language(lang_code, lang_data)
                if success:
                    if existing:
                        updated_languages += 1
                    else:
                        added_languages += 1

                    # Count sources
                    for category, resources in lang_data.items():
                        if category != "language_info":
                            total_sources += len(resources)

            # Create comprehensive collection
            collection_created = await self.create_east_africa_collection()

            # Generate expansion summary
            expansion_summary = await self.generate_east_africa_summary()

            results = {
                "operation_success": True,
                "languages_added": added_languages,
                "languages_updated": updated_languages,
                "subfamilies_created": subfamilies_created,
                "total_data_sources_added": total_sources,
                "collection_created": collection_created,
                "expansion_summary": expansion_summary
            }

            logger.info("East Africa major languages population completed successfully!")
            return results

        except Exception as e:
            logger.error(f"East Africa population failed: {e}")
            raise
        finally:
            await self.close_database()

async def main():
    """Main execution function"""
    try:
        populator = EastAfricaPopulator()
        results = await populator.populate_east_africa_languages()

        print("\n" + "="*80)
        print("EAST AFRICA MAJOR LANGUAGES POPULATION COMPLETE")
        print("="*80)
        print(f"✅ Languages Added: {results['languages_added']}")
        print(f"✅ Languages Updated: {results['languages_updated']}")
        print(f"✅ Subfamilies Created: {results['subfamilies_created']}")
        print(f"✅ Total Data Sources: {results['total_data_sources_added']}")
        print(f"✅ Collection Created: {'Yes' if results['collection_created'] else 'No'}")

        if results['expansion_summary']:
            summary = results['expansion_summary']
            print(f"\n📊 East Africa Complete Summary:")
            print(f"  Total East African Languages: {summary['total_east_african_languages']}")
            print(f"  Total Speakers: {summary['total_speakers']:,}")
            print(f"  Government Sponsored: {summary['government_sponsored_count']}")
            print(f"  Languages with Data Sources: {summary['languages_with_data_sources']}")
            print(f"  Total Data Sources: {summary['total_data_sources']}")

            print(f"\n🏆 Top East African Languages by Speakers:")
            for lang in summary['top_10_by_speakers']:
                countries = ', '.join(lang['countries'][:2])
                print(f"  {lang['name']} ({lang['code']}): {lang['speakers']:,} speakers - {countries} ({lang['family']})")

            print(f"\n🌍 Country Coverage:")
            for country, count in sorted(summary['country_coverage'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {country}: {count} languages")

            print(f"\n📚 Language Family Distribution:")
            for family, count in sorted(summary['family_distribution'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {family}: {count} languages")

        print(f"\n🌍 East Africa established as fifth flagship region!")
        print("Regional lingua francas and national languages with government support covered!")

    except Exception as e:
        logger.error(f"East Africa population script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())