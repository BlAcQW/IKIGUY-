#!/usr/bin/env python3
"""
AI Voice Agent Query Interface for Healthcare Providers
Handles natural language queries and returns structured responses
"""

import re
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional, Tuple
import openai
from dataclasses import dataclass
import json
import logging
from area_mapping import AreaMapper

# Configure logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@dataclass
class QueryResult:
    providers: List[Dict]
    total_found: int
    search_type: str  # 'text', 'semantic', 'location', 'specialty'
    confidence: float
    suggested_refinements: List[str]

class VoiceAgentQueries:
    def __init__(self, db_config: dict, openai_api_key: str = None):
        self.db_config = db_config
        self.openai_api_key = openai_api_key
        if openai_api_key:
            openai.api_key = openai_api_key

        # Initialize area mapper for better location matching
        self.area_mapper = AreaMapper()

        # Common query patterns for voice recognition - improved for compound names
        self.location_patterns = [
            r'\b(?:in|at|near|around)\s+([a-z\s\-]+?)(?:\s+area|\s*$)',
            r'\b([a-z\s\-]+?)\s+area\b',
            r'\b([a-z\s\-]+?)\s+(?:location|place)\b'
        ]

        self.specialty_patterns = {
            r'\b(?:eye|vision|optical|ophthalmologist)\b': 'Ophthalmology',
            r'\b(?:children|kids|pediatric|pediatrician|paediatric|paedetriciean|pediatriciean)\b': 'Pediatrics',  # Added STT variants
            r'\b(?:women|pregnancy|gynecologist|gynecologists|gynaecologist|womens?\s*health|gynae|gyane)\b': 'Gynecology',
            r'\b(?:obstetrician|obstetrics|maternity|obs)\b': 'Obs',
            r'\b(?:general|family|gp)\s*(?:practice|doctor|physician)?\b': 'General Practice',
            r'\b(?:ear|nose|throat|ent)\b': 'Ear Nose Throat',
            r'\b(?:physio|physiotherapy|physical\s*therapy)\b': 'Physiotherapy',
            r'\b(?:dentist|dental|teeth|oral)\b': 'Dental',
            r'\b(?:pharmacy|pharmacies|chemist|chemists|medication|drugs|pharmaceutical)\b': 'Pharmacy',
            r'\b(?:dermatolog|dermatologist|skin|derm)\b': 'Derm',
            r'\b(?:surgeon|surgery|surgical|surg)\b': 'Surg',
            r'\b(?:urology|urologist|uro)\b': 'Urology',
            r'\b(?:neurology|neurologist|neu)\b': 'Neu',
            r'\b(?:diet|dietitian|nutrition)\b': 'Diet',
            r'\b(?:laboratory|lab|diagnostics|diagnostic)\b': 'Laboratory',
            r'\b(?:scan|ultrasound|ultrascan|radiology)\b': 'Scan',
            r'\b(?:emergency|urgent|accident)\b': 'Emergency'
        }

        # STT confusion patterns - when STT mishears one specialty as another
        self.stt_confusion_fixes = {
            # Common STT mistakes where one specialty is misheard as another
            'pharmacy pediatric': 'Pediatrics',  # "pediatrician" sometimes picked up as "pharmacy" + "pediatric"
            'pharmacy children': 'Pediatrics',   # Similar confusion
            'pharmacy kids': 'Pediatrics',
        }

    def connect_db(self):
        """Connect to PostgreSQL database"""
        return psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)

    def extract_intent(self, query: str) -> Dict[str, any]:
        """Extract intent and entities from natural language query"""
        query_lower = query.lower().strip()

        intent = {
            'action': 'find_provider',
            'specialty': None,
            'location': None,
            'provider_type': None,
            'emergency': False,
            'insurance': True  # Assume they need insurance-covered providers
        }

        # First check for STT confusion patterns in the full query
        query_normalized = ' '.join(query_lower.split())  # Normalize whitespace
        for confusion_pattern, correct_specialty in self.stt_confusion_fixes.items():
            if confusion_pattern in query_normalized:
                intent['specialty'] = correct_specialty
                break

        # If no STT confusion found, extract specialty normally
        if not intent['specialty']:
            for pattern, specialty in self.specialty_patterns.items():
                if re.search(pattern, query_lower, re.IGNORECASE):
                    intent['specialty'] = specialty
                    break

        # Extract location with improved compound name handling
        for pattern in self.location_patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                location = match.group(1).strip()

                # Clean up location - remove trailing prepositions and articles
                location = re.sub(r'\s+(area|place|location)$', '', location, flags=re.IGNORECASE)

                if len(location) > 2:  # Avoid single letters
                    intent['location'] = location.title()
                    break

        # Additional check for compound location names that might be missed
        if not intent['location']:
            # Look for known compound locations directly
            compound_locations = ['east legon', 'north legon', 'korle-bu', 'korlebu', 'tema station', 'greater accra']
            for compound in compound_locations:
                if compound in query_lower:
                    intent['location'] = compound.title()
                    break

        # Fallback: try to find any location-like words after common prepositions
        if not intent['location']:
            fallback_match = re.search(r'\b(?:in|at|near|around)\s+(\w+(?:\s+\w+)?)', query_lower, re.IGNORECASE)
            if fallback_match:
                potential_location = fallback_match.group(1).strip()
                if len(potential_location) > 2 and potential_location not in ['a', 'an', 'the']:
                    intent['location'] = potential_location.title()

        # Detect provider type
        if re.search(r'\bhospital\b', query_lower):
            intent['provider_type'] = 'hospital'
        elif re.search(r'\bclinic\b', query_lower):
            intent['provider_type'] = 'clinic'
        elif re.search(r'\bpharmacy|chemist\b', query_lower):
            intent['provider_type'] = 'pharmacy'

        # Emergency detection
        if re.search(r'\bemergency|urgent|now|immediately|accident\b', query_lower):
            intent['emergency'] = True

        return intent

    def generate_query_embedding(self, query: str) -> Optional[List[float]]:
        """Generate embedding for semantic search"""
        if not self.openai_api_key:
            return None

        try:
            response = openai.embeddings.create(
                model="text-embedding-ada-002",
                input=query
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            return None

    def search_providers(
        self,
        query: str,
        max_results: int = 5,
        use_semantic: bool = True
    ) -> QueryResult:
        """Main search function for voice agent"""

        intent = self.extract_intent(query)
        query_embedding = None

        if use_semantic and self.openai_api_key:
            query_embedding = self.generate_query_embedding(query)

        conn = self.connect_db()
        providers = []

        try:
            with conn.cursor() as cur:
                # Enhanced location matching
                location_to_search = None
                if intent['location']:
                    # Try to normalize the location using area mapper
                    normalized_location = self.area_mapper.normalize_location(intent['location'])
                    if normalized_location:
                        location_to_search = normalized_location
                    else:
                        # Fall back to original location for partial matching
                        location_to_search = intent['location']

                # Prioritize specialty and location over raw query text for better results
                search_text = ""

                # Special handling for emergency queries - search for hospitals instead of "Emergency" specialty
                if intent['emergency'] or (intent['specialty'] and intent['specialty'] == 'Emergency'):
                    search_text = "hospital"
                    intent['specialty'] = None  # Clear emergency specialty, use provider type instead
                    intent['provider_type'] = 'hospital'
                elif intent['specialty']:
                    search_text = intent['specialty'].lower()
                elif intent['provider_type']:
                    search_text = intent['provider_type']
                else:
                    search_text = query

                # Try primary search first
                try:
                    # Ensure all parameters are properly typed (use empty string instead of None for TEXT types)
                    # Reason: PostgreSQL can't infer types when NULL is passed through parameterized queries
                    search_text_param = search_text if search_text is not None else ''
                    location_param = location_to_search if location_to_search is not None else ''
                    specialty_param = intent['specialty'] if intent['specialty'] is not None else ''

                    logger.info(f"Executing search_providers: text='{search_text_param}', location='{location_param}', specialty='{specialty_param}', max={max_results}")
                    cur.execute("""
                        SELECT * FROM search_providers(%s::text, %s::text, %s::text, %s::integer)
                    """, (search_text_param, location_param, specialty_param, max_results))
                    raw_providers = cur.fetchall()
                    logger.info(f"Primary search returned {len(raw_providers)} providers")
                except psycopg2.Error as db_err:
                    logger.error(f"PostgreSQL error in search_providers: {db_err}")
                    logger.error(f"Query parameters: text='{search_text_param}', location='{location_param}', specialty='{specialty_param}', max={max_results}")
                    raise  # Re-raise to be caught by outer exception handler

                # If no results and we had a location, try expanded location search
                if not raw_providers and intent['location']:
                    # Special handling for broad regions like "Greater Accra"
                    if intent['location'].lower() in ['greater accra', 'accra', 'ghana']:
                        # Search without location filter for broad regions
                        specialty_param = intent['specialty'] if intent['specialty'] is not None else ''
                        search_text_param = search_text if search_text is not None else ''
                        cur.execute("""
                            SELECT * FROM search_providers(%s::text, %s::text, %s::text, %s::integer)
                        """, (search_text_param, '', specialty_param, max_results))
                        raw_providers = cur.fetchall()
                    else:
                        # Normal expanded location search
                        expanded_locations = self.area_mapper.expand_location_search(intent['location'])

                        for expanded_location in expanded_locations:
                            if expanded_location != location_to_search:  # Avoid duplicate search
                                search_text_param = search_text if search_text is not None else ''
                                specialty_param = intent['specialty'] if intent['specialty'] is not None else ''
                                expanded_loc_param = expanded_location if expanded_location is not None else ''
                                cur.execute("""
                                    SELECT * FROM search_providers(%s::text, %s::text, %s::text, %s::integer)
                                """, (search_text_param, expanded_loc_param, specialty_param, max_results))
                                additional_providers = cur.fetchall()
                                raw_providers.extend(additional_providers)

                                # Stop if we have enough results
                                if len(raw_providers) >= max_results:
                                    raw_providers = raw_providers[:max_results]
                                    break

                        # If still no results, try fuzzy location matching
                        if not raw_providers:
                            cur.execute("""
                                SELECT DISTINCT area, COUNT(*) as provider_count
                                FROM healthcare_providers
                                WHERE is_active = true
                                AND area ILIKE %s
                                GROUP BY area
                                ORDER BY provider_count DESC
                                LIMIT 3
                            """, (f"%{intent['location']}%",))
                            similar_areas = cur.fetchall()

                            # Try searching in similar areas
                            for similar_area in similar_areas:
                                search_text_param = search_text if search_text is not None else ''
                                specialty_param = intent['specialty'] if intent['specialty'] is not None else ''
                                similar_area_param = similar_area['area'] if similar_area['area'] is not None else ''
                                cur.execute("""
                                    SELECT * FROM search_providers(%s::text, %s::text, %s::text, %s::integer)
                                """, (search_text_param, similar_area_param, specialty_param, max_results))
                                similar_providers = cur.fetchall()
                                raw_providers.extend(similar_providers)
                                if len(raw_providers) >= max_results:
                                    raw_providers = raw_providers[:max_results]
                                    break

                # Add the missing fields for consistency
                providers = []
                for p in raw_providers:
                    enhanced_p = dict(p)
                    enhanced_p['provider_type'] = 'clinic'  # Default
                    enhanced_p['phone_secondary'] = None
                    enhanced_p['operating_hours'] = None
                    enhanced_p['is_emergency'] = False
                    enhanced_p['similarity_score'] = 0.0
                    providers.append(enhanced_p)

                total_count = len(providers)
                search_type = 'text_enhanced'

        except Exception as e:
            logger.error(f"Database error in search_providers: {e}", exc_info=True)
            logger.error(f"Failed query: '{query}', intent: {intent}")
            # Still generate suggestions even on database error
            suggestions = self._generate_suggestions([], intent, query)
            return QueryResult([], 0, 'error', 0.0, suggestions)
        finally:
            conn.close()

        # Calculate confidence score
        confidence = self._calculate_confidence(providers, intent, query)

        # Generate suggestions for refinement
        suggestions = self._generate_suggestions(providers, intent, query)

        return QueryResult(
            providers=[dict(p) for p in providers],
            total_found=total_count,
            search_type=search_type,
            confidence=confidence,
            suggested_refinements=suggestions
        )

    def _calculate_confidence(self, providers: List, intent: Dict, query: str) -> float:
        """Calculate confidence score for the search results"""
        if not providers:
            return 0.0

        # Base confidence from number of results
        result_confidence = min(len(providers) / 5.0, 1.0)

        # Boost confidence if intent extraction was successful
        intent_confidence = 0.0
        if intent['specialty']:
            intent_confidence += 0.3
        if intent['location']:
            intent_confidence += 0.3
        if intent['provider_type']:
            intent_confidence += 0.2

        # Boost confidence based on search scores
        avg_score = 0.0
        if providers and 'similarity_score' in providers[0]:
            scores = [p.get('similarity_score', 0) or p.get('text_rank', 0) for p in providers]
            avg_score = sum(scores) / len(scores) if scores else 0

        return min((result_confidence + intent_confidence + avg_score) / 3.0, 1.0)

    def _generate_suggestions(self, providers: List, intent: Dict, query: str) -> List[str]:
        """Generate suggestions to refine the search"""
        suggestions = []

        if not providers:
            if intent['location']:
                # Get similar location suggestions
                try:
                    conn = self.connect_db()
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT DISTINCT area, COUNT(*) as provider_count
                            FROM healthcare_providers
                            WHERE is_active = true
                            AND area ILIKE %s
                            GROUP BY area
                            ORDER BY provider_count DESC
                            LIMIT 3
                        """, (f"%{intent['location']}%",))
                        similar_areas = cur.fetchall()

                        if similar_areas:
                            area_names = [area['area'] for area in similar_areas]
                            suggestions.append(f"I couldn't find providers in {intent['location']}. Try searching in: {', '.join(area_names)}")
                        else:
                            # Special handling for known out-of-coverage areas
                            location_lower = intent['location'].lower()
                            if any(term in location_lower for term in ['kumasi', 'comassie', 'comasie']):
                                suggestions.append(f"Our healthcare provider network currently covers Greater Accra region only. For providers in {intent['location']}, I recommend contacting Premier Health customer service at 0302-XXX-XXXX for assistance with providers outside Accra.")
                            elif any(term in location_lower for term in ['whitesmith', 'banker']):
                                suggestions.append(f"I couldn't find '{intent['location']}' as a recognized area. Try popular areas like Madina, East Legon, Circle, Airport, or Asylum Down.")
                            else:
                                suggestions.append(f"I couldn't find providers in {intent['location']}. Try popular areas like Madina, East Legon, or Circle")
                    conn.close()
                except:
                    suggestions.append("Try broadening your search by removing specific location requirements")
            else:
                suggestions.append("Try broadening your search by removing specific location or specialty requirements")

        if len(providers) > 10:
            if not intent['location']:
                suggestions.append("Specify a location to narrow down results")
            if not intent['specialty']:
                suggestions.append("Specify what type of medical service you need")

        if intent.get('emergency') and not any(p.get('is_emergency') for p in providers):
            suggestions.append("For emergencies, consider calling emergency services or visiting the nearest hospital")

        return suggestions

    def format_voice_response(self, result: QueryResult, query: str) -> str:
        """Format results for voice agent response"""
        if not result.providers:
            return "I couldn't find any healthcare providers matching your request. You might want to try a different location or service type."

        providers = result.providers[:3]  # Limit to top 3 for voice

        if len(providers) == 1:
            p = providers[0]
            response = f"I found {p['name']}, a {p['provider_type']} in {p['area']}. "
            if p['specialties']:
                response += f"They offer {', '.join(p['specialties'][:2])}. "
            if p['phone_primary']:
                response += f"You can reach them at {p['phone_primary']}."
        else:
            response = f"I found {len(providers)} options for you. "
            for i, p in enumerate(providers, 1):
                response += f"{i}. {p['name']} in {p['area']}"
                if p['phone_primary']:
                    response += f", phone {p['phone_primary']}"
                response += ". "

        if result.suggested_refinements:
            response += f" {result.suggested_refinements[0]}"

        return response

    def search_providers_with_intent(self, query: str, intent: Dict, max_results: int = 5) -> QueryResult:
        """
        Search providers with a pre-defined intent (for tool function integration)

        Args:
            query (str): Search query text
            intent (Dict): Pre-defined intent with location, specialty, etc.
            max_results (int): Maximum number of results

        Returns:
            QueryResult: Search results
        """
        conn = self.connect_db()
        providers = []

        try:
            with conn.cursor() as cur:
                # Enhanced location matching
                location_to_search = None
                if intent.get('location'):
                    normalized_location = self.area_mapper.normalize_location(intent['location'])
                    if normalized_location:
                        location_to_search = normalized_location
                    else:
                        location_to_search = intent['location']

                # Search text priority
                search_text = ""
                if intent.get('emergency') or (intent.get('specialty') == 'Emergency'):
                    search_text = "hospital"
                    intent['specialty'] = None
                    intent['provider_type'] = 'hospital'
                elif intent.get('specialty'):
                    search_text = intent['specialty'].lower()
                elif intent.get('provider_type'):
                    search_text = intent['provider_type']
                else:
                    search_text = query

                # Primary search
                search_text_param = search_text if search_text is not None else ''
                location_param = location_to_search if location_to_search is not None else ''
                specialty_param = intent.get('specialty', '') or ''
                cur.execute("""
                    SELECT * FROM search_providers(%s::text, %s::text, %s::text, %s::integer)
                """, (search_text_param, location_param, specialty_param, max_results))
                raw_providers = cur.fetchall()

                # Fallback searches if needed
                if not raw_providers and intent.get('location'):
                    if intent['location'].lower() in ['greater accra', 'accra', 'ghana']:
                        search_text_param = search_text if search_text is not None else ''
                        specialty_param = intent.get('specialty', '') or ''
                        cur.execute("""
                            SELECT * FROM search_providers(%s::text, %s::text, %s::text, %s::integer)
                        """, (search_text_param, '', specialty_param, max_results))
                        raw_providers = cur.fetchall()
                    else:
                        expanded_locations = self.area_mapper.expand_location_search(intent['location'])
                        for expanded_location in expanded_locations:
                            if expanded_location != location_to_search:
                                search_text_param = search_text if search_text is not None else ''
                                expanded_loc_param = expanded_location if expanded_location is not None else ''
                                specialty_param = intent.get('specialty', '') or ''
                                cur.execute("""
                                    SELECT * FROM search_providers(%s::text, %s::text, %s::text, %s::integer)
                                """, (search_text_param, expanded_loc_param, specialty_param, max_results))
                                additional_providers = cur.fetchall()
                                raw_providers.extend(additional_providers)
                                if len(raw_providers) >= max_results:
                                    raw_providers = raw_providers[:max_results]
                                    break

                # Format providers
                providers = []
                for p in raw_providers:
                    enhanced_p = dict(p)
                    enhanced_p['provider_type'] = 'clinic'
                    enhanced_p['phone_secondary'] = None
                    enhanced_p['operating_hours'] = None
                    enhanced_p['is_emergency'] = False
                    enhanced_p['similarity_score'] = 0.0
                    providers.append(enhanced_p)

                total_count = len(providers)
                search_type = 'intent_based'

        except Exception as e:
            logger.error(f"Database error in search_providers_with_intent: {e}", exc_info=True)
            logger.error(f"Failed query: '{query}', intent: {intent}")
            # Still generate suggestions even on database error
            suggestions = self._generate_suggestions([], intent, query)
            return QueryResult([], 0, 'error', 0.0, suggestions)
        finally:
            conn.close()

        # Calculate confidence and suggestions
        confidence = self._calculate_confidence(providers, intent, query)
        suggestions = self._generate_suggestions(providers, intent, query)

        return QueryResult(
            providers=providers,
            total_found=total_count,
            search_type=search_type,
            confidence=confidence,
            suggested_refinements=suggestions
        )

# Example usage functions
def example_queries():
    """Example voice agent queries"""
    # Initialize (add your OpenAI API key for semantic search)
    agent = VoiceAgentQueries(
        db_config={
            'host': 'localhost',
            'port': 5432,
            'database': 'kasaai_core',
            'options': '-c search_path=premier_health,public',
            'user': 'postgres',
            'password': 'aawwER44444'
        }
        # openai_api_key="your-api-key-here"
    )

    # Example voice queries
    queries = [
        "Find me an eye doctor in Accra",
        "I need a pediatrician near Tesano",
        "Where can I find a pharmacy in Korle-Bu area?",
        "Emergency hospital in Greater Accra",
        "General practice doctor in Dansoman"
    ]

    for query in queries:
        print(f"\\nQuery: '{query}'")
        result = agent.search_providers(query)
        response = agent.format_voice_response(result, query)
        print(f"Response: {response}")
        print(f"Confidence: {result.confidence:.2f}")

if __name__ == "__main__":
    example_queries()