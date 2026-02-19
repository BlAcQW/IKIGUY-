#!/usr/bin/env python3
"""
Language Data Sources Populator
Populates comprehensive data sources for Twi, Ga, Ewe, and Hausa languages
"""

import asyncio
import sys
import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from core.config import get_settings
from language_data_sources import LANGUAGE_DATA_SOURCES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LanguageDataSourcesPopulator:
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

    async def update_language_with_data_sources(self, language_code, data_sources):
        """Update language document with data sources"""
        try:
            # Find the language by ISO 639-3 code
            language_doc = await self.db.languages.find_one({"code": language_code})

            if not language_doc:
                logger.warning(f"Language with code {language_code} not found in database")
                return False

            # Prepare data sources for database storage
            formatted_sources = {}
            total_resources = 0

            for category, resources in data_sources.items():
                if category == "language_info":
                    continue  # Skip language info as it's already in the language doc

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
                    "data_sources": formatted_sources,
                    "data_sources_count": total_resources,
                    "data_sources_last_updated": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }

            result = await self.db.languages.update_one(
                {"_id": language_doc["_id"]},
                update_data
            )

            if result.modified_count > 0:
                logger.info(f"Updated {language_code} with {total_resources} data sources")
                return True
            else:
                logger.warning(f"No changes made to {language_code}")
                return False

        except Exception as e:
            logger.error(f"Error updating {language_code} with data sources: {e}")
            return False

    async def create_data_sources_collection(self):
        """Create a separate collection for detailed data source information"""
        try:
            collection_doc = {
                "_id": ObjectId(),
                "collection_type": "language_data_sources",
                "description": "Comprehensive data sources for African languages",
                "languages_covered": list(LANGUAGE_DATA_SOURCES.keys()),
                "total_languages": len(LANGUAGE_DATA_SOURCES),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "data_sources": LANGUAGE_DATA_SOURCES
            }

            # Remove existing collection document
            await self.db.data_source_collections.delete_many({
                "collection_type": "language_data_sources"
            })

            # Insert new collection document
            await self.db.data_source_collections.insert_one(collection_doc)
            logger.info("Created comprehensive data sources collection")
            return True

        except Exception as e:
            logger.error(f"Error creating data sources collection: {e}")
            return False

    async def create_data_sources_indexes(self):
        """Create indexes for efficient data source queries"""
        try:
            indexes_created = 0

            # Indexes for language data sources
            language_indexes = [
                ("data_sources_count", {}),
                ("data_sources_last_updated", {}),
                ([("code", 1), ("data_sources_count", -1)], {}),
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

            # Indexes for data source collections
            collection_indexes = [
                ("collection_type", {}),
                ("languages_covered", {}),
                ("created_at", {}),
            ]

            for index_spec, options in collection_indexes:
                try:
                    await self.db.data_source_collections.create_index(index_spec, **options)
                    indexes_created += 1
                except Exception as e:
                    if "already exists" in str(e) or "IndexKeySpecsConflict" in str(e):
                        logger.debug(f"Index on {index_spec} already exists, skipping")
                    else:
                        logger.warning(f"Failed to create index on {index_spec}: {e}")

            logger.info(f"Created {indexes_created} new data source indexes")
            return indexes_created

        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            return 0

    async def generate_data_sources_summary(self):
        """Generate summary of populated data sources"""
        try:
            summary = {
                "languages_with_sources": 0,
                "total_data_sources": 0,
                "source_types": {},
                "institutions": set(),
                "license_types": set(),
                "languages_details": {}
            }

            # Check each language for data sources
            for lang_code in LANGUAGE_DATA_SOURCES.keys():
                language_doc = await self.db.languages.find_one(
                    {"code": lang_code},
                    {"name": 1, "data_sources_count": 1, "data_sources": 1}
                )

                if language_doc and language_doc.get("data_sources_count", 0) > 0:
                    summary["languages_with_sources"] += 1
                    count = language_doc["data_sources_count"]
                    summary["total_data_sources"] += count

                    summary["languages_details"][lang_code] = {
                        "name": language_doc["name"],
                        "sources_count": count
                    }

                    # Analyze source types from the original data
                    lang_data = LANGUAGE_DATA_SOURCES[lang_code]
                    for category, resources in lang_data.items():
                        if category == "language_info":
                            continue

                        for resource_key, resource_data in resources.items():
                            # Count source types
                            source_type = resource_data["type"]
                            summary["source_types"][source_type] = summary["source_types"].get(source_type, 0) + 1

                            # Collect institutions and licenses
                            summary["institutions"].add(resource_data["institution"])
                            if "license" in resource_data:
                                summary["license_types"].add(resource_data["license"])

            # Convert sets to lists for JSON serialization
            summary["institutions"] = list(summary["institutions"])
            summary["license_types"] = list(summary["license_types"])

            # Get collection info
            collection_doc = await self.db.data_source_collections.find_one({
                "collection_type": "language_data_sources"
            })

            summary["collection_exists"] = collection_doc is not None
            summary["summary_timestamp"] = datetime.utcnow()

            logger.info("Data Sources Summary:")
            logger.info(f"  Languages with data sources: {summary['languages_with_sources']}")
            logger.info(f"  Total data sources: {summary['total_data_sources']}")
            logger.info(f"  Source types: {len(summary['source_types'])}")
            logger.info(f"  Institutions: {len(summary['institutions'])}")
            logger.info(f"  License types: {len(summary['license_types'])}")

            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return None

    async def populate_all_data_sources(self):
        """Populate data sources for all target languages"""
        try:
            await self.connect_database()

            logger.info("Starting data sources population for Twi, Ga, Ewe, and Hausa...")

            updated_languages = 0
            total_sources = 0

            # Update each language with its data sources
            for lang_code, data_sources in LANGUAGE_DATA_SOURCES.items():
                success = await self.update_language_with_data_sources(lang_code, data_sources)
                if success:
                    updated_languages += 1
                    # Count total sources for this language
                    for category, resources in data_sources.items():
                        if category != "language_info":
                            total_sources += len(resources)

            # Create comprehensive data sources collection
            collection_created = await self.create_data_sources_collection()

            # Create indexes for efficient querying
            indexes_created = await self.create_data_sources_indexes()

            # Generate summary
            summary = await self.generate_data_sources_summary()

            summary.update({
                "operations_completed": {
                    "updated_languages": updated_languages,
                    "total_sources_added": total_sources,
                    "collection_created": collection_created,
                    "indexes_created": indexes_created
                }
            })

            logger.info("Data sources population completed successfully!")
            return summary

        except Exception as e:
            logger.error(f"Data sources population failed: {e}")
            raise
        finally:
            await self.close_database()

async def main():
    """Main execution function"""
    try:
        populator = LanguageDataSourcesPopulator()
        summary = await populator.populate_all_data_sources()

        print("\n" + "="*70)
        print("LANGUAGE DATA SOURCES POPULATION COMPLETE")
        print("="*70)
        print(f"✅ Languages Updated: {summary['languages_with_sources']}")
        print(f"✅ Total Data Sources: {summary['total_data_sources']}")
        print(f"✅ Source Types: {len(summary['source_types'])}")
        print(f"✅ Institutions: {len(summary['institutions'])}")
        print(f"✅ License Types: {len(summary['license_types'])}")
        print(f"✅ Collection Created: {'Yes' if summary['collection_exists'] else 'No'}")
        print(f"✅ Indexes Created: {summary['operations_completed']['indexes_created']}")

        print(f"\n📊 Language Details:")
        for lang_code, details in summary['languages_details'].items():
            print(f"  {details['name']} ({lang_code}): {details['sources_count']} sources")

        print(f"\n🔗 Source Types:")
        for source_type, count in summary['source_types'].items():
            print(f"  {source_type}: {count}")

        print(f"\n🏛️ Top Institutions:")
        for institution in list(summary['institutions'])[:10]:
            print(f"  - {institution}")

        print("\n🌍 Comprehensive data sources added for Twi, Ga, Ewe, and Hausa!")

    except Exception as e:
        logger.error(f"Data sources population script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())