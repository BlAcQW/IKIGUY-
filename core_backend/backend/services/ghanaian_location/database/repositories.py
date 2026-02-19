"""
Repository layer for Ghanaian Location Services

Provides data access layer for location data with MongoDB backend.
Handles CRUD operations, querying, and learning from user feedback.
"""

import asyncio
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

from .models import (
    GhanaianLocation,
    STTCorrection,
    PronunciationGuide,
    LocationRelationship,
    UserCorrection,
    LocationAnalytics,
    LocationResult,
    ToolContext,
    LanguageContext
)

logger = logging.getLogger(__name__)


class LocationRepository:
    """Repository for managing Ghanaian location data"""

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize repository with MongoDB database connection.

        Args:
            database: AsyncIO MongoDB database instance
        """
        self.db = database
        self.locations = database.ghanaian_locations
        self.stt_corrections = database.stt_corrections
        self.pronunciation_guides = database.pronunciation_guides
        self.location_relationships = database.location_relationships
        self.user_corrections = database.user_corrections
        self.location_analytics = database.location_analytics

    async def setup_indexes(self):
        """Create database indexes for optimal performance"""
        try:
            # Locations collection indexes
            await self.locations.create_index([("canonical_name", 1)], unique=True)
            await self.locations.create_index([("aliases", 1)])
            await self.locations.create_index([("phonetic_codes.soundex", 1)])
            await self.locations.create_index([("phonetic_codes.metaphone", 1)])
            await self.locations.create_index([("is_active", 1)])

            # STT corrections indexes
            await self.stt_corrections.create_index([("misheard_input", 1)])
            await self.stt_corrections.create_index([("correct_location", 1)])
            await self.stt_corrections.create_index([("confidence", -1), ("frequency", -1)])
            await self.stt_corrections.create_index([("is_active", 1)])

            # Pronunciation guides indexes
            await self.pronunciation_guides.create_index([("location_name", 1)])
            await self.pronunciation_guides.create_index([("language", 1)])
            await self.pronunciation_guides.create_index([("difficulty_score", -1)])

            # Relationships indexes
            await self.location_relationships.create_index([("primary_location", 1)])
            await self.location_relationships.create_index([("related_location", 1)])
            await self.location_relationships.create_index([("relationship_type", 1)])

            logger.info("✅ Database indexes created successfully")

        except Exception as e:
            logger.error(f"Failed to create database indexes: {e}")
            raise

    # Location Management Methods

    async def create_location(self, location: GhanaianLocation) -> str:
        """Create a new location record"""
        try:
            result = await self.locations.insert_one(location.dict())
            logger.info(f"Created location: {location.canonical_name}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create location {location.canonical_name}: {e}")
            raise

    async def get_location_by_name(self, name: str) -> Optional[GhanaianLocation]:
        """Get location by canonical name"""
        try:
            doc = await self.locations.find_one({
                "canonical_name": name.upper(),
                "is_active": True
            })
            return GhanaianLocation(**doc) if doc else None
        except Exception as e:
            logger.error(f"Failed to get location {name}: {e}")
            return None

    async def find_locations_by_alias(self, alias: str) -> List[GhanaianLocation]:
        """Find locations that include this alias"""
        try:
            cursor = self.locations.find({
                "aliases": {"$regex": alias.upper(), "$options": "i"},
                "is_active": True
            })
            locations = []
            async for doc in cursor:
                locations.append(GhanaianLocation(**doc))
            return locations
        except Exception as e:
            logger.error(f"Failed to find locations by alias {alias}: {e}")
            return []

    async def find_by_phonetic_code(self, phonetic_code: str, algorithm: str) -> List[GhanaianLocation]:
        """Find locations by phonetic similarity"""
        try:
            cursor = self.locations.find({
                f"phonetic_codes.{algorithm}": phonetic_code,
                "is_active": True
            })
            locations = []
            async for doc in cursor:
                locations.append(GhanaianLocation(**doc))
            return locations
        except Exception as e:
            logger.error(f"Failed to find locations by phonetic code {phonetic_code}: {e}")
            return []

    async def get_all_active_locations(self) -> List[GhanaianLocation]:
        """Get all active locations"""
        try:
            cursor = self.locations.find({"is_active": True})
            locations = []
            async for doc in cursor:
                locations.append(GhanaianLocation(**doc))
            return locations
        except Exception as e:
            logger.error(f"Failed to get all locations: {e}")
            return []

    # STT Correction Methods

    async def get_stt_correction(self, misheard_input: str) -> Optional[STTCorrection]:
        """Get STT correction for misheard input"""
        try:
            doc = await self.stt_corrections.find_one({
                "misheard_input": misheard_input.lower(),
                "is_active": True
            })
            return STTCorrection(**doc) if doc else None
        except Exception as e:
            logger.error(f"Failed to get STT correction for {misheard_input}: {e}")
            return None

    async def find_similar_stt_corrections(self, input_text: str, limit: int = 5) -> List[STTCorrection]:
        """Find STT corrections similar to input text"""
        try:
            # Use regex for partial matching
            cursor = self.stt_corrections.find({
                "misheard_input": {"$regex": input_text.lower(), "$options": "i"},
                "is_active": True
            }).sort([("confidence", -1), ("frequency", -1)]).limit(limit)

            corrections = []
            async for doc in cursor:
                corrections.append(STTCorrection(**doc))
            return corrections
        except Exception as e:
            logger.error(f"Failed to find similar STT corrections for {input_text}: {e}")
            return []

    async def create_stt_correction(self, correction: STTCorrection) -> str:
        """Create a new STT correction"""
        try:
            result = await self.stt_corrections.insert_one(correction.dict())
            logger.info(f"Created STT correction: {correction.misheard_input} -> {correction.correct_location}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create STT correction: {e}")
            raise

    async def update_correction_usage(self, misheard_input: str, success: bool = True):
        """Update correction usage statistics"""
        try:
            correction = await self.get_stt_correction(misheard_input)
            if correction:
                new_frequency = correction.frequency + 1
                if success:
                    # Calculate new success rate
                    total_uses = correction.frequency
                    current_successes = int(correction.success_rate * total_uses)
                    new_success_rate = (current_successes + 1) / new_frequency
                else:
                    current_successes = int(correction.success_rate * correction.frequency)
                    new_success_rate = current_successes / new_frequency

                await self.stt_corrections.update_one(
                    {"misheard_input": misheard_input.lower()},
                    {
                        "$set": {
                            "frequency": new_frequency,
                            "success_rate": new_success_rate,
                            "last_used": datetime.utcnow()
                        }
                    }
                )
        except Exception as e:
            logger.error(f"Failed to update correction usage: {e}")

    # Pronunciation Guide Methods

    async def get_pronunciation_guide(self, location_name: str, language: LanguageContext = LanguageContext.ENGLISH) -> Optional[PronunciationGuide]:
        """Get pronunciation guide for location"""
        try:
            doc = await self.pronunciation_guides.find_one({
                "location_name": location_name.upper(),
                "language": language,
                "is_active": True
            })
            return PronunciationGuide(**doc) if doc else None
        except Exception as e:
            logger.error(f"Failed to get pronunciation guide for {location_name}: {e}")
            return None

    async def create_pronunciation_guide(self, guide: PronunciationGuide) -> str:
        """Create a new pronunciation guide"""
        try:
            result = await self.pronunciation_guides.insert_one(guide.dict())
            logger.info(f"Created pronunciation guide for: {guide.location_name}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create pronunciation guide: {e}")
            raise

    # Location Relationship Methods

    async def get_related_locations(self, location_name: str, relationship_types: List[str] = None) -> List[LocationRelationship]:
        """Get locations related to the given location"""
        try:
            query = {
                "$or": [
                    {"primary_location": location_name.upper()},
                    {"related_location": location_name.upper(), "bidirectional": True}
                ],
                "is_active": True
            }

            if relationship_types:
                query["relationship_type"] = {"$in": relationship_types}

            cursor = self.location_relationships.find(query).sort("relationship_strength", -1)
            relationships = []
            async for doc in cursor:
                relationships.append(LocationRelationship(**doc))
            return relationships
        except Exception as e:
            logger.error(f"Failed to get related locations for {location_name}: {e}")
            return []

    async def create_location_relationship(self, relationship: LocationRelationship) -> str:
        """Create a new location relationship"""
        try:
            result = await self.location_relationships.insert_one(relationship.dict())
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create location relationship: {e}")
            raise

    # User Feedback Methods

    async def record_user_correction(self, correction: UserCorrection) -> str:
        """Record user feedback for learning"""
        try:
            result = await self.user_corrections.insert_one(correction.dict())
            logger.info(f"Recorded user correction: {correction.user_input} -> {correction.user_correction}")

            # If this is a new STT correction, potentially add it to the corrections database
            if correction.user_correction and correction.confidence_before < 0.8:
                await self._learn_from_user_correction(correction)

            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to record user correction: {e}")
            raise

    async def _learn_from_user_correction(self, user_correction: UserCorrection):
        """Learn from user correction and potentially add to STT corrections"""
        try:
            # Check if this correction already exists
            existing = await self.get_stt_correction(user_correction.user_input)

            if existing:
                # Update existing correction
                if existing.correct_location != user_correction.user_correction:
                    logger.warning(
                        f"User correction conflicts with existing: "
                        f"{user_correction.user_input} -> {existing.correct_location} vs {user_correction.user_correction}"
                    )
            else:
                # Create new STT correction
                new_correction = STTCorrection(
                    misheard_input=user_correction.user_input.lower(),
                    correct_location=user_correction.user_correction.upper(),
                    confidence=0.7,  # Start with moderate confidence
                    phonetic_similarity=0.6,  # Will be calculated later
                    frequency=1,
                    verified=False,
                    source="user_feedback"
                )
                await self.create_stt_correction(new_correction)

            # Mark user correction as applied
            await self.user_corrections.update_one(
                {"user_input": user_correction.user_input, "timestamp": user_correction.timestamp},
                {"$set": {"applied_to_training": True}}
            )

        except Exception as e:
            logger.error(f"Failed to learn from user correction: {e}")

    # Analytics and Monitoring

    async def get_location_analytics(self, location_name: str, days: int = 30) -> Optional[LocationAnalytics]:
        """Get analytics for a specific location"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            doc = await self.location_analytics.find_one({
                "location_name": location_name.upper(),
                "reporting_period_start": {"$gte": start_date},
                "reporting_period_end": {"$lte": end_date}
            })
            return LocationAnalytics(**doc) if doc else None
        except Exception as e:
            logger.error(f"Failed to get analytics for {location_name}: {e}")
            return None

    async def update_usage_analytics(self, location_name: str, success: bool, confidence: float,
                                   processing_time_ms: float, context: ToolContext):
        """Update usage analytics for a location"""
        try:
            # This would typically be called after each location processing
            # Implementation would update or create analytics records
            # For now, we'll create a simple update query

            await self.location_analytics.update_one(
                {"location_name": location_name.upper()},
                {
                    "$inc": {
                        "total_queries": 1,
                        "successful_matches": 1 if success else 0,
                        f"context_usage.{context}": 1
                    },
                    "$set": {
                        "last_updated": datetime.utcnow(),
                        "average_processing_time_ms": processing_time_ms  # Simplified - should be rolling average
                    }
                },
                upsert=True
            )
        except Exception as e:
            logger.error(f"Failed to update analytics for {location_name}: {e}")

    # Utility Methods

    async def health_check(self) -> Dict[str, Any]:
        """Check repository health and return statistics"""
        try:
            stats = {
                "total_locations": await self.locations.count_documents({"is_active": True}),
                "total_corrections": await self.stt_corrections.count_documents({"is_active": True}),
                "total_pronunciation_guides": await self.pronunciation_guides.count_documents({"is_active": True}),
                "total_relationships": await self.location_relationships.count_documents({"is_active": True}),
                "database_connected": True,
                "last_checked": datetime.utcnow().isoformat()
            }
            return stats
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "database_connected": False,
                "error": str(e),
                "last_checked": datetime.utcnow().isoformat()
            }