#!/usr/bin/env python3
"""
Ghana Tourism Board - RAG-Enhanced Voice Agent Tools
Uses Gemini-powered semantic search for intelligent tourism recommendations.

This version enhances the original tools with RAG (Retrieval-Augmented Generation)
for more natural, context-aware responses powered by Google Gemini.
"""

import json
import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import asyncio
import sys

# Add paths
sys.path.append('/opt/kasaai')
sys.path.append('/opt/kasaai/apps/core_backend')

from backend.services.helpdesk_rag_service import (
    helpdesk_rag_service,
    QueryResult
)
from backend.services.email_service import EmailService, EmailMessage

# Import original tools as fallback
from voice_agent_tools import GhanaTourismTools as OriginalTools

logger = logging.getLogger(__name__)

# RAG collection name
GHANA_TOURISM_COLLECTION = "ghana_tourism_production"


class GhanaTourismToolsRAG(OriginalTools):
    """
    Enhanced Ghana Tourism tools with Gemini RAG semantic search.

    Extends original tools with AI-powered intelligence for better responses.
    Falls back to original methods if RAG fails.
    """

    def __init__(self):
        """Initialize RAG-enhanced tourism tools."""
        super().__init__()
        self.rag_enabled = True
        logger.info("Ghana Tourism RAG tools initialized with Gemini")

    async def _query_rag(self, query: str, context: Optional[Dict[str, Any]] = None) -> Optional[QueryResult]:
        """
        Query the RAG knowledge base with context.

        Args:
            query: Natural language query
            context: Additional context (location, category, etc.)

        Returns:
            QueryResult or None if RAG fails
        """
        try:
            # Enhance query with context
            enhanced_query = query
            if context:
                if context.get('region'):
                    enhanced_query += f" in {context['region']} region"
                if context.get('category'):
                    enhanced_query += f" {context['category']} type"
                if context.get('budget'):
                    enhanced_query += f" with budget around GHS {context['budget']}"

            # Query RAG knowledge base
            result = await helpdesk_rag_service.query_knowledge_base(
                company_name=GHANA_TOURISM_COLLECTION,
                query=enhanced_query
            )

            return result if result.success else None

        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return None

    def search_destinations(
        self,
        query: str,
        region: Optional[str] = None,
        category: Optional[str] = None,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search destinations with RAG-enhanced semantic understanding.

        Args:
            query: Natural language query
            region: Specific region filter
            category: Destination category
            max_results: Maximum results

        Returns:
            Enhanced search results with AI-powered insights
        """
        try:
            # Get traditional results
            traditional_result = super().search_destinations(
                query=query,
                region=region,
                category=category,
                max_results=max_results
            )

            # If RAG is disabled, return traditional results
            if not self.rag_enabled:
                return traditional_result

            # Enhance with RAG intelligence
            context = {
                'region': region,
                'category': category,
                'type': 'destination'
            }

            rag_result = asyncio.run(self._query_rag(query, context))

            if rag_result and rag_result.confidence_score > 0.6:
                # Combine RAG insights with traditional results
                destinations = traditional_result.get('destinations', [])

                if destinations:
                    voice_response = f"{rag_result.response}\n\n"
                    voice_response += f"I found {len(destinations)} destinations that match your interests:\n"

                    for i, dest in enumerate(destinations[:3], 1):
                        voice_response += f"\n{i}. {dest['name']} in {dest['region']} - "
                        voice_response += f"{dest['description'][:100]}..."

                    if len(destinations) > 3:
                        voice_response += f"\n\nAnd {len(destinations) - 3} more options."
                else:
                    voice_response = rag_result.response

                traditional_result['voice_response'] = voice_response
                traditional_result['ai_enhanced'] = True
                traditional_result['confidence_score'] = rag_result.confidence_score
                traditional_result['sources'] = rag_result.sources_used

                logger.info(f"RAG-enhanced destination search: {len(destinations)} results, confidence={rag_result.confidence_score:.2f}")
            else:
                traditional_result['ai_enhanced'] = False
                logger.info("Using traditional destination search (RAG confidence low)")

            return traditional_result

        except Exception as e:
            logger.error(f"Error in RAG destination search: {e}")
            # Fallback to traditional
            result = super().search_destinations(query, region, category, max_results)
            result['ai_enhanced'] = False
            return result

    def get_destination_details(self, destination_name: str) -> Dict[str, Any]:
        """
        Get destination details with RAG-enhanced context and recommendations.

        Args:
            destination_name: Name of destination

        Returns:
            Enhanced destination details with AI insights
        """
        try:
            # Get traditional details
            traditional_result = super().get_destination_details(destination_name)

            if not self.rag_enabled or not traditional_result.get('success'):
                return traditional_result

            # Enhance with RAG context
            query = f"Tell me about {destination_name} tourist destination in Ghana, including what makes it special and travel tips"
            rag_result = asyncio.run(self._query_rag(query))

            if rag_result and rag_result.confidence_score > 0.6:
                dest = traditional_result.get('destination', {})

                # Create enhanced voice response
                voice_response = f"Let me tell you about {dest.get('name', destination_name)}.\n\n"
                voice_response += rag_result.response

                traditional_result['voice_response'] = voice_response
                traditional_result['ai_enhanced'] = True
                traditional_result['confidence_score'] = rag_result.confidence_score

                logger.info(f"RAG-enhanced destination details for {destination_name}")
            else:
                traditional_result['ai_enhanced'] = False

            return traditional_result

        except Exception as e:
            logger.error(f"Error in RAG destination details: {e}")
            result = super().get_destination_details(destination_name)
            result['ai_enhanced'] = False
            return result

    def search_accommodation(
        self,
        location: Optional[str] = None,
        accommodation_type: Optional[str] = None,
        budget_max_ghs: Optional[int] = None,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search accommodations with RAG-enhanced recommendations.

        Args:
            location: City or region
            accommodation_type: hotel, resort, lodge, etc.
            budget_max_ghs: Maximum budget per night
            max_results: Maximum results

        Returns:
            Enhanced accommodation search with AI recommendations
        """
        try:
            # Get traditional results
            traditional_result = super().search_accommodation(
                location=location,
                accommodation_type=accommodation_type,
                budget_max_ghs=budget_max_ghs,
                max_results=max_results
            )

            if not self.rag_enabled:
                return traditional_result

            # Build RAG query
            query_parts = ["accommodation in Ghana"]
            if location:
                query_parts.append(f"in {location}")
            if accommodation_type:
                query_parts.append(f"{accommodation_type} type")
            if budget_max_ghs:
                query_parts.append(f"budget friendly under GHS {budget_max_ghs}")

            query = " ".join(query_parts)

            context = {
                'location': location,
                'type': accommodation_type,
                'budget': budget_max_ghs
            }

            rag_result = asyncio.run(self._query_rag(query, context))

            if rag_result and rag_result.confidence_score > 0.6:
                accommodations = traditional_result.get('accommodations', [])

                if accommodations:
                    voice_response = f"{rag_result.response}\n\n"
                    voice_response += f"I found {len(accommodations)} accommodations:\n"

                    for i, acc in enumerate(accommodations[:3], 1):
                        room_types = acc.get('room_types', [])
                        price_info = ""
                        if room_types:
                            price_info = f" (from GHS {room_types[0].get('price_range_ghs', 'N/A')} per night)"

                        voice_response += f"\n{i}. {acc['name']} - {acc['star_rating']}-star {acc['type']} in {acc['city']}{price_info}"

                    if len(accommodations) > 3:
                        voice_response += f"\n\nPlus {len(accommodations) - 3} more options."
                else:
                    voice_response = rag_result.response

                traditional_result['voice_response'] = voice_response
                traditional_result['ai_enhanced'] = True
                traditional_result['confidence_score'] = rag_result.confidence_score

                logger.info(f"RAG-enhanced accommodation search: {len(accommodations)} results")
            else:
                traditional_result['ai_enhanced'] = False

            return traditional_result

        except Exception as e:
            logger.error(f"Error in RAG accommodation search: {e}")
            result = super().search_accommodation(location, accommodation_type, budget_max_ghs, max_results)
            result['ai_enhanced'] = False
            return result

    def get_visa_requirements(self, nationality: Optional[str] = None) -> Dict[str, Any]:
        """
        Get visa requirements with RAG-enhanced guidance.

        Args:
            nationality: Country of citizenship

        Returns:
            Enhanced visa information with AI guidance
        """
        try:
            # Get traditional info
            traditional_result = super().get_visa_requirements(nationality)

            if not self.rag_enabled:
                return traditional_result

            # Enhance with RAG
            query = f"Ghana visa requirements"
            if nationality:
                query += f" for {nationality} citizens"

            rag_result = asyncio.run(self._query_rag(query))

            if rag_result and rag_result.confidence_score > 0.6:
                traditional_result['voice_response'] = rag_result.response
                traditional_result['ai_enhanced'] = True
                traditional_result['confidence_score'] = rag_result.confidence_score

                logger.info(f"RAG-enhanced visa info for {nationality or 'general'}")
            else:
                traditional_result['ai_enhanced'] = False

            return traditional_result

        except Exception as e:
            logger.error(f"Error in RAG visa info: {e}")
            result = super().get_visa_requirements(nationality)
            result['ai_enhanced'] = False
            return result

    def get_general_tourism_guidance(self, query: str) -> Dict[str, Any]:
        """
        Get general tourism guidance using RAG for any question.

        This is a new method that provides intelligent answers to
        any tourism-related question using the Gemini RAG system.

        Args:
            query: Any tourism-related question

        Returns:
            AI-powered response with sources
        """
        try:
            if not self.rag_enabled:
                return {
                    "success": False,
                    "error": "RAG system not available",
                    "voice_response": "I can help with specific queries about destinations, accommodations, and travel information. Please ask about a specific topic."
                }

            # Query RAG directly
            rag_result = asyncio.run(helpdesk_rag_service.query_knowledge_base(
                company_name=GHANA_TOURISM_COLLECTION,
                query=query
            ))

            if rag_result.success and rag_result.confidence_score > 0.5:
                return {
                    "success": True,
                    "query": query,
                    "voice_response": rag_result.response,
                    "confidence_score": rag_result.confidence_score,
                    "sources": rag_result.sources_used,
                    "requires_escalation": rag_result.requires_escalation,
                    "ai_enhanced": True
                }
            else:
                return {
                    "success": False,
                    "query": query,
                    "voice_response": "I don't have specific information about that. Could you ask about destinations, accommodations, visa requirements, or other travel essentials?",
                    "confidence_score": rag_result.confidence_score if rag_result else 0.0,
                    "requires_escalation": True,
                    "ai_enhanced": False
                }

        except Exception as e:
            logger.error(f"Error in general RAG guidance: {e}")
            return {
                "success": False,
                "error": str(e),
                "voice_response": "I'm having trouble processing that question. Please try asking about specific destinations, accommodations, or travel information."
            }


# Export the RAG-enhanced tools
__all__ = ['GhanaTourismToolsRAG', 'GHANA_TOURISM_COLLECTION']
