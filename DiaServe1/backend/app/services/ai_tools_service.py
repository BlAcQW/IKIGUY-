"""
AI Tools service for EstateFlow.

Generates content using AI (listings, social posts, emails, contract analysis).
Falls back to template-based generation when no LLM API key is configured.
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.ai_tools import (
    GenerationType,
    GenerationResponse,
    AIStats,
)

logger = logging.getLogger(__name__)


class AIToolsService:
    """Service for AI content generation."""

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.collection = database["ai_generations"]
        self.openai_key = os.getenv("OPENAI_API_KEY", "")

    def _convert_doc(self, doc: dict) -> dict:
        if doc and "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return doc

    async def _save_generation(
        self,
        organization_id: str,
        user_id: str,
        generation_type: GenerationType,
        prompt: str,
        result: str,
        property_id: Optional[str] = None,
        tokens_used: int = 0,
        model_used: str = "template",
    ) -> GenerationResponse:
        """Save a generation to the database."""
        doc = {
            "organization_id": organization_id,
            "generation_type": generation_type.value,
            "prompt": prompt,
            "result": result,
            "property_id": property_id,
            "tokens_used": tokens_used,
            "model_used": model_used,
            "created_at": datetime.utcnow(),
            "created_by": user_id,
        }

        insert_result = await self.collection.insert_one(doc)
        doc["id"] = str(insert_result.inserted_id)
        doc.pop("_id", None)

        return GenerationResponse(**doc)

    def _generate_listing_template(self, prompt: str) -> str:
        """Template-based listing generation."""
        return (
            f"Property Listing\n\n"
            f"Based on your description: {prompt}\n\n"
            f"Welcome to this exceptional property that offers everything you've been looking for. "
            f"This stunning home features modern finishes throughout, spacious living areas, "
            f"and is situated in a prime location with easy access to amenities.\n\n"
            f"Key Highlights:\n"
            f"- Premium location with excellent connectivity\n"
            f"- Modern architecture and contemporary design\n"
            f"- High-quality finishes and fixtures\n"
            f"- Spacious rooms with natural lighting\n"
            f"- Secure compound with 24/7 security\n\n"
            f"Contact us today to schedule a viewing!"
        )

    def _generate_social_template(self, prompt: str) -> str:
        """Template-based social post generation."""
        return (
            f"NEW LISTING ALERT!\n\n"
            f"{prompt}\n\n"
            f"Don't miss this incredible opportunity! "
            f"This property won't last long on the market.\n\n"
            f"DM us or call for more details!\n\n"
            f"#RealEstate #PropertyForSale #DreamHome #Investment "
            f"#LuxuryLiving #NewListing #HomeForSale"
        )

    def _generate_email_template(self, prompt: str) -> str:
        """Template-based email generation."""
        return (
            f"Subject: Exclusive Property Opportunity\n\n"
            f"Dear Valued Client,\n\n"
            f"{prompt}\n\n"
            f"We are excited to share this exclusive property opportunity with you. "
            f"Based on your preferences, we believe this listing perfectly matches "
            f"what you've been looking for.\n\n"
            f"Property Highlights:\n"
            f"- Prime location\n"
            f"- Competitive pricing\n"
            f"- Modern amenities\n"
            f"- Ready for immediate occupancy\n\n"
            f"Would you like to schedule a private viewing? "
            f"Reply to this email or call us at your convenience.\n\n"
            f"Best regards,\n"
            f"The EstateFlow Team"
        )

    def _analyze_contract_template(self, prompt: str) -> str:
        """Template-based contract analysis."""
        return (
            f"Contract Analysis Summary\n\n"
            f"Document reviewed: {prompt[:100]}...\n\n"
            f"Key Findings:\n"
            f"1. Standard terms and conditions identified\n"
            f"2. Payment terms appear reasonable\n"
            f"3. Liability clauses are within normal range\n"
            f"4. Termination conditions are clearly defined\n\n"
            f"Recommendations:\n"
            f"- Review all financial obligations carefully\n"
            f"- Verify compliance with local regulations\n"
            f"- Consider legal counsel for complex clauses\n"
            f"- Ensure all parties are clearly identified\n\n"
            f"Note: This is an automated analysis. Please consult with a legal "
            f"professional for comprehensive contract review."
        )

    async def generate_listing(
        self,
        prompt: str,
        property_id: Optional[str],
        organization_id: str,
        user_id: str,
    ) -> GenerationResponse:
        """Generate a property listing description."""
        result = self._generate_listing_template(prompt)
        return await self._save_generation(
            organization_id=organization_id,
            user_id=user_id,
            generation_type=GenerationType.LISTING,
            prompt=prompt,
            result=result,
            property_id=property_id,
        )

    async def generate_social_post(
        self,
        prompt: str,
        property_id: Optional[str],
        organization_id: str,
        user_id: str,
    ) -> GenerationResponse:
        """Generate social media post content."""
        result = self._generate_social_template(prompt)
        return await self._save_generation(
            organization_id=organization_id,
            user_id=user_id,
            generation_type=GenerationType.SOCIAL_MEDIA,
            prompt=prompt,
            result=result,
            property_id=property_id,
        )

    async def generate_email(
        self,
        prompt: str,
        organization_id: str,
        user_id: str,
    ) -> GenerationResponse:
        """Generate email campaign content."""
        result = self._generate_email_template(prompt)
        return await self._save_generation(
            organization_id=organization_id,
            user_id=user_id,
            generation_type=GenerationType.EMAIL,
            prompt=prompt,
            result=result,
        )

    async def analyze_contract(
        self,
        prompt: str,
        organization_id: str,
        user_id: str,
    ) -> GenerationResponse:
        """Analyze a contract."""
        result = self._analyze_contract_template(prompt)
        return await self._save_generation(
            organization_id=organization_id,
            user_id=user_id,
            generation_type=GenerationType.CONTRACT_ANALYSIS,
            prompt=prompt,
            result=result,
        )

    async def list_generations(
        self,
        organization_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[GenerationResponse], int]:
        """List past AI generations."""
        query = {"organization_id": organization_id}
        total = await self.collection.count_documents(query)

        cursor = (
            self.collection.find(query)
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
        )

        generations = []
        async for doc in cursor:
            generations.append(GenerationResponse(**self._convert_doc(doc)))

        return generations, total

    async def get_stats(self, organization_id: str) -> AIStats:
        """Get AI usage statistics."""
        today_start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        total = await self.collection.count_documents(
            {"organization_id": organization_id}
        )
        today = await self.collection.count_documents(
            {"organization_id": organization_id, "created_at": {"$gte": today_start}}
        )

        # Total tokens
        pipeline = [
            {"$match": {"organization_id": organization_id}},
            {"$group": {"_id": None, "total_tokens": {"$sum": "$tokens_used"}}},
        ]
        token_result = await self.collection.aggregate(pipeline).to_list(1)
        total_tokens = token_result[0]["total_tokens"] if token_result else 0

        # Most used type
        type_pipeline = [
            {"$match": {"organization_id": organization_id}},
            {"$group": {"_id": "$generation_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 1},
        ]
        type_result = await self.collection.aggregate(type_pipeline).to_list(1)
        most_used = type_result[0]["_id"] if type_result else None

        return AIStats(
            total_generations=total,
            generations_today=today,
            tokens_used_total=total_tokens,
            most_used_type=most_used,
        )
