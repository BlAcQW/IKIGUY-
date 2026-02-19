#!/usr/bin/env python3
"""
Ghana Tourism Board - Voice Agent Tool Functions
Comprehensive tourism tools for helping visitors to Ghana

Tools cover: Destinations, Accommodation, Transport, Food, Activities,
Culture, Practical Info, Emergency Services, and Communication
"""

import json
import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import asyncio

# Import email service for communication tools
import sys
sys.path.append('/opt/kasaai/apps/core_backend')
from backend.services.email_service import EmailService, EmailMessage

logger = logging.getLogger(__name__)


class GhanaTourismTools:
    """
    Ghana Tourism Board voice agent tools.

    Provides comprehensive tourism information and services for visitors to Ghana.
    """

    def __init__(self):
        """Initialize tourism tools with data sources."""
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.data_path = os.path.join(self.base_path, 'data')

        # Load static data
        self.destinations_data = self._load_json('destinations.json')
        self.accommodations_data = self._load_json('accommodations.json')
        self.practical_info_data = self._load_json('practical_info.json')

        # Load expanded data (October 2025 additions)
        self.transportation_data = self._load_json('transportation.json')
        self.restaurants_data = self._load_json('restaurants.json')

        # Load all regional expansions
        regional_files = [
            'ashanti_region.json',
            'upper_east_region.json',
            'northern_region_extended.json',
            'western_region_extended.json',
            'eastern_region_extended.json'
        ]

        total_new_destinations = 0
        total_new_accommodations = 0

        for filename in regional_files:
            regional_data = self._load_json(filename)
            if regional_data:
                if 'destinations' in regional_data and 'destinations' in self.destinations_data:
                    self.destinations_data['destinations'].extend(regional_data['destinations'])
                    total_new_destinations += len(regional_data['destinations'])
                if 'accommodations' in regional_data and 'accommodations' in self.accommodations_data:
                    self.accommodations_data['accommodations'].extend(regional_data['accommodations'])
                    total_new_accommodations += len(regional_data['accommodations'])

        logger.info(f"Loaded {total_new_destinations} additional destinations from regional files")
        logger.info(f"Loaded {total_new_accommodations} additional accommodations from regional files")
        logger.info(f"Total destinations: {len(self.destinations_data.get('destinations', []))}")
        logger.info(f"Total accommodations: {len(self.accommodations_data.get('accommodations', []))}")

        # Initialize email service
        try:
            self.email_service = EmailService()
            logger.info("Email service initialized")
        except Exception as e:
            logger.warning(f"Email service initialization failed: {e}")
            self.email_service = None

    def _load_json(self, filename: str) -> Dict[str, Any]:
        """
        Load JSON data file.

        Args:
            filename: Name of JSON file in data directory

        Returns:
            Parsed JSON data or empty dict if file not found
        """
        try:
            filepath = os.path.join(self.data_path, filename)
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {filename}: {e}")
            return {}

    # ========== DESTINATION TOOLS ==========

    def search_destinations(
        self,
        query: str,
        region: Optional[str] = None,
        category: Optional[str] = None,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search for tourist destinations in Ghana.

        Args:
            query: Natural language search query (e.g., "beaches near Accra", "historical sites")
            region: Specific region (e.g., "Greater Accra", "Ashanti", "Central")
            category: Type of destination (beach, historical, nature, cultural, adventure, wildlife)
            max_results: Maximum number of results to return

        Returns:
            Dict containing matching destinations with details and voice-friendly response
        """
        try:
            query_lower = query.lower()
            destinations = self.destinations_data.get('destinations', [])

            # Filter by region if specified
            if region:
                destinations = [d for d in destinations if d.get('region', '').lower() == region.lower()]

            # Filter by category if specified
            if category:
                destinations = [d for d in destinations if category.lower() in [c.lower() for c in d.get('category', [])]]

            # Search by query keywords
            matched = []
            for dest in destinations:
                score = 0
                search_text = f"{dest.get('name', '')} {dest.get('description', '')} {' '.join(dest.get('highlights', []))}".lower()

                # Simple keyword matching
                for word in query_lower.split():
                    if word in search_text:
                        score += 1

                if score > 0:
                    dest_copy = dest.copy()
                    dest_copy['relevance_score'] = score
                    matched.append(dest_copy)

            # Sort by relevance and limit
            matched.sort(key=lambda x: x['relevance_score'], reverse=True)
            results = matched[:max_results]

            # Generate voice response
            if not results:
                voice_response = f"I couldn't find any destinations matching '{query}'. Would you like me to suggest popular destinations in Ghana?"
            elif len(results) == 1:
                dest = results[0]
                voice_response = f"I found {dest['name']} in {dest['region']} region. {dest['description']}"
            else:
                dest_names = [d['name'] for d in results]
                voice_response = f"I found {len(results)} destinations: {', '.join(dest_names[:3])}"
                if len(results) > 3:
                    voice_response += f" and {len(results) - 3} more"

            return {
                "success": True,
                "destinations": results,
                "total_found": len(results),
                "query": query,
                "filters": {"region": region, "category": category},
                "voice_response": voice_response
            }

        except Exception as e:
            logger.error(f"Error searching destinations: {e}")
            return {
                "success": False,
                "error": str(e),
                "voice_response": "I'm having trouble searching for destinations right now. Please try again."
            }

    def get_destination_details(self, destination_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific destination.

        Args:
            destination_name: Name of the destination

        Returns:
            Detailed destination information including entry fees, activities, contact info
        """
        try:
            destinations = self.destinations_data.get('destinations', [])

            # Find destination by name (case-insensitive partial match)
            destination = None
            name_lower = destination_name.lower()

            for dest in destinations:
                if name_lower in dest.get('name', '').lower():
                    destination = dest
                    break

            if not destination:
                return {
                    "success": False,
                    "voice_response": f"I couldn't find details for '{destination_name}'. Could you check the spelling or try a different destination?"
                }

            # Format voice response
            voice_response = f"{destination['name']} is located in {destination['region']} region. "
            voice_response += f"{destination['description']} "

            if destination.get('entry_fee'):
                voice_response += f"Entry fee is {destination['entry_fee']}. "

            if destination.get('best_time_to_visit'):
                voice_response += f"Best time to visit is {destination['best_time_to_visit']}."

            return {
                "success": True,
                "destination": destination,
                "voice_response": voice_response
            }

        except Exception as e:
            logger.error(f"Error getting destination details: {e}")
            return {
                "success": False,
                "error": str(e),
                "voice_response": "I'm having trouble getting those details right now."
            }

    # ========== ACCOMMODATION TOOLS ==========

    def search_accommodation(
        self,
        location: str,
        accommodation_type: Optional[str] = None,
        budget_max_ghs: Optional[int] = None,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search for accommodation options.

        Args:
            location: City or area (e.g., "Accra", "Cape Coast", "Mole")
            accommodation_type: Type (hotel, resort, lodge, guesthouse)
            budget_max_ghs: Maximum price per night in GHS
            max_results: Maximum results to return

        Returns:
            List of accommodation options with prices and amenities
        """
        try:
            accommodations = self.accommodations_data.get('accommodations', [])
            location_lower = location.lower()

            # Filter by location
            matched = []
            for acc in accommodations:
                acc_location = f"{acc.get('city', '')} {acc.get('region', '')}".lower()
                if location_lower in acc_location:
                    matched.append(acc)

            # Filter by type
            if accommodation_type:
                matched = [a for a in matched if a.get('type', '').lower() == accommodation_type.lower()]

            # Filter by budget (check minimum price of cheapest room)
            if budget_max_ghs:
                budget_matched = []
                for acc in matched:
                    room_types = acc.get('room_types', [])
                    if room_types:
                        # Parse min price from price_range_ghs
                        min_price = min([int(rt.get('price_range_ghs', '999-999').split('-')[0]) for rt in room_types])
                        if min_price <= budget_max_ghs:
                            budget_matched.append(acc)
                matched = budget_matched

            results = matched[:max_results]

            # Generate voice response
            if not results:
                voice_response = f"I couldn't find accommodation in {location}"
                if budget_max_ghs:
                    voice_response += f" within your budget of {budget_max_ghs} cedis"
                voice_response += ". Would you like to try a different location or adjust your budget?"
            else:
                voice_response = f"I found {len(results)} accommodation options in {location}. "
                if len(results) >= 1:
                    first = results[0]
                    voice_response += f"For example, {first['name']} is a {first['star_rating']}-star {first['type']}. "

            return {
                "success": True,
                "accommodations": results,
                "total_found": len(results),
                "location": location,
                "voice_response": voice_response
            }

        except Exception as e:
            logger.error(f"Error searching accommodation: {e}")
            return {
                "success": False,
                "error": str(e),
                "voice_response": "I'm having trouble searching for accommodation right now."
            }

    def get_accommodation_details(self, accommodation_name: str) -> Dict[str, Any]:
        """
        Get detailed information about specific accommodation.

        Args:
            accommodation_name: Name of hotel/resort/lodge

        Returns:
            Detailed information including amenities, room types, prices, contact info
        """
        try:
            accommodations = self.accommodations_data.get('accommodations', [])
            name_lower = accommodation_name.lower()

            accommodation = None
            for acc in accommodations:
                if name_lower in acc.get('name', '').lower():
                    accommodation = acc
                    break

            if not accommodation:
                return {
                    "success": False,
                    "voice_response": f"I couldn't find details for '{accommodation_name}'."
                }

            # Format voice response
            voice_response = f"{accommodation['name']} is a {accommodation['star_rating']}-star {accommodation['type']} in {accommodation['city']}. "
            voice_response += f"{accommodation['description']} "

            amenities = accommodation.get('amenities', [])
            if amenities:
                voice_response += f"Amenities include {', '.join(amenities[:5])}. "

            room_types = accommodation.get('room_types', [])
            if room_types:
                first_room = room_types[0]
                voice_response += f"Rooms start from around {first_room['price_range_ghs']} cedis per night. "

            contact = accommodation.get('contact', {})
            if contact.get('phone'):
                voice_response += f"You can contact them at {contact['phone']}."

            return {
                "success": True,
                "accommodation": accommodation,
                "voice_response": voice_response
            }

        except Exception as e:
            logger.error(f"Error getting accommodation details: {e}")
            return {
                "success": False,
                "error": str(e),
                "voice_response": "I'm having trouble getting those details."
            }

    # ========== PRACTICAL INFORMATION TOOLS ==========

    def get_visa_requirements(self, nationality: Optional[str] = None) -> Dict[str, Any]:
        """
        Get visa requirements for visiting Ghana.

        Args:
            nationality: Visitor's nationality/country (optional)

        Returns:
            Visa requirements, fees, application process
        """
        try:
            visa_info = self.practical_info_data.get('visa_requirements', {})

            # Build response based on nationality if provided
            if nationality:
                nationality_lower = nationality.lower()

                # Check visa-free countries
                visa_free_countries = [c.lower() for c in visa_info.get('visa_free', {}).get('countries', [])]
                if any(nationality_lower in country for country in visa_free_countries):
                    voice_response = f"Great news! As a {nationality} citizen, you can visit Ghana visa-free for up to 90 days."
                else:
                    voice_response = f"As a {nationality} citizen, you'll need a visa to visit Ghana. "
                    voice_response += "You can apply for an e-visa online or get visa on arrival. "
            else:
                voice_response = "Ghana offers several visa options: visa on arrival for African Union citizens and some other countries, "
                voice_response += "e-visa for most nationalities, or visa-free entry for ECOWAS members. "

            evisa = visa_info.get('e_visa', {})
            voice_response += f"E-visa costs about {evisa.get('fee_usd', 150)} US dollars and takes {evisa.get('processing_time_days', '3-5')} business days. "
            voice_response += f"Apply at {evisa.get('website', 'the Ghana Immigration Service website')}."

            return {
                "success": True,
                "visa_info": visa_info,
                "nationality_checked": nationality,
                "voice_response": voice_response
            }

        except Exception as e:
            logger.error(f"Error getting visa requirements: {e}")
            return {
                "success": False,
                "error": str(e),
                "voice_response": "I'm having trouble getting visa information right now. Please visit the Ghana Immigration Service website."
            }

    def get_sim_card_info(self, preferred_provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about buying SIM cards and mobile data in Ghana.

        Args:
            preferred_provider: Specific provider (MTN, Vodafone, AirtelTigo) or None for all

        Returns:
            SIM card providers, data plans, prices, where to buy
        """
        try:
            sim_info = self.practical_info_data.get('mobile_sim_cards', {})
            providers = sim_info.get('providers', [])
            general = sim_info.get('general_info', {})

            if preferred_provider:
                # Filter to specific provider
                provider_lower = preferred_provider.lower()
                providers = [p for p in providers if provider_lower in p.get('name', '').lower()]

            if not providers:
                return {
                    "success": False,
                    "voice_response": f"I couldn't find information about {preferred_provider if preferred_provider else 'SIM cards'}."
                }

            # Build voice response
            voice_response = f"You can buy SIM cards at {general.get('airport_availability', 'the airport')}. "
            voice_response += "The main providers are MTN, Vodafone, and AirtelTigo. "

            if len(providers) == 1:
                provider = providers[0]
                voice_response += f"{provider['name']} has {provider['coverage']}. "
                tourist_pkg = provider.get('tourist_package', {})
                if tourist_pkg:
                    voice_response += f"They offer a tourist package for {tourist_pkg['price_ghs']} cedis which includes {tourist_pkg['includes']}. "
            else:
                voice_response += "All providers have tourist packages around 40-50 cedis with data and calls. "

            voice_response += f"You'll need your passport to register. SIM card itself costs about 1 cedi."

            return {
                "success": True,
                "providers": providers,
                "general_info": general,
                "voice_response": voice_response
            }

        except Exception as e:
            logger.error(f"Error getting SIM card info: {e}")
            return {
                "success": False,
                "error": str(e),
                "voice_response": "I'm having trouble getting SIM card information."
            }

    def get_safety_security_tips(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Get safety and security tips for tourists.

        Args:
            category: Specific category (general, health, road, scams) or None for all

        Returns:
            Safety tips, emergency contacts, health recommendations
        """
        try:
            safety_info = self.practical_info_data.get('safety_security', {})

            # Build voice response based on category
            voice_response = "Ghana is one of the safest countries in West Africa. "

            if category == 'health' or not category:
                health = safety_info.get('health_safety', {})
                voice_response += "Yellow fever vaccination is mandatory and you'll need proof at entry. "
                voice_response += "Take malaria prophylaxis and use insect repellent. Drink only bottled water. "

            if category == 'general' or not category:
                general = safety_info.get('general_safety', {})
                voice_response += "Keep valuables secure, use hotel safes, and be cautious in crowded areas. "
                voice_response += "Use registered taxis or ride-sharing apps like Uber or Bolt. "

            if category == 'scams' or not category:
                voice_response += "Avoid too-good-to-be-true offers, agree on taxi prices before entering, and use licensed tour guides. "

            # Add emergency contacts
            emergency = safety_info.get('emergency_contacts', {})
            voice_response += f"Emergency numbers: Police {emergency.get('police', '191')}, Ambulance {emergency.get('ambulance', '193')}."

            return {
                "success": True,
                "safety_info": safety_info,
                "category": category,
                "voice_response": voice_response
            }

        except Exception as e:
            logger.error(f"Error getting safety tips: {e}")
            return {
                "success": False,
                "error": str(e),
                "voice_response": "I'm having trouble getting safety information."
            }

    def get_emergency_contacts(self) -> Dict[str, Any]:
        """
        Get emergency contact numbers for tourists.

        Returns:
            Police, ambulance, fire, tourist police, embassy contacts
        """
        try:
            safety_info = self.practical_info_data.get('safety_security', {})
            emergency = safety_info.get('emergency_contacts', {})

            voice_response = "Here are important emergency numbers in Ghana: "
            voice_response += f"Police: {emergency.get('police', '191 or 18555')}, "
            voice_response += f"Ambulance: {emergency.get('ambulance', '193')}, "
            voice_response += f"Fire Service: {emergency.get('fire_service', '192')}. "

            if emergency.get('tourist_police_accra'):
                voice_response += f"For tourist-specific issues in Accra, call Tourist Police at {emergency['tourist_police_accra']}."

            return {
                "success": True,
                "emergency_contacts": emergency,
                "voice_response": voice_response
            }

        except Exception as e:
            logger.error(f"Error getting emergency contacts: {e}")
            return {
                "success": False,
                "error": str(e),
                "voice_response": "Emergency numbers in Ghana are: Police 191, Ambulance 193, Fire 192."
            }

    def get_currency_exchange_info(self) -> Dict[str, Any]:
        """
        Get information about Ghana's currency and where to exchange money.

        Returns:
            Currency info, exchange rates, where to exchange, ATM availability
        """
        try:
            currency_info = self.practical_info_data.get('currency_exchange', {})

            voice_response = f"Ghana's currency is the {currency_info.get('currency', 'Ghana Cedi')}, symbol {currency_info.get('symbol', 'GH₵')}. "

            rates = currency_info.get('exchange_rate_approximation', {})
            voice_response += f"Currently, 1 US dollar is approximately {rates.get('usd_to_ghs', '12-13')} cedis. "

            voice_response += "You can exchange money at banks, licensed forex bureaus, or hotels. "
            voice_response += "Forex bureaus usually offer better rates than banks, and much better than hotels. "

            atm_info = currency_info.get('atms', {})
            voice_response += f"ATMs are widely available in cities. Major banks accept Visa and Mastercard. "
            voice_response += "Mobile money like MTN MoMo is also very popular in Ghana."

            return {
                "success": True,
                "currency_info": currency_info,
                "voice_response": voice_response
            }

        except Exception as e:
            logger.error(f"Error getting currency info: {e}")
            return {
                "success": False,
                "error": str(e),
                "voice_response": "Ghana uses the Ghana Cedi. You can exchange money at banks and forex bureaus."
            }

    # ========== COMMUNICATION TOOLS ==========

    def send_tourism_info_email(
        self,
        recipient_email: str,
        subject: str,
        destinations: Optional[List[str]] = None,
        accommodations: Optional[List[str]] = None,
        additional_info: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send tourism information via email.

        Args:
            recipient_email: Tourist's email address
            subject: Email subject line
            destinations: List of destination names to include
            accommodations: List of accommodation names to include
            additional_info: Any additional information to include

        Returns:
            Success status and confirmation message
        """
        try:
            if not self.email_service:
                return {
                    "success": False,
                    "voice_response": "Email service is not available right now. Please note down the information."
                }

            # Build email body
            body = f"Hello,\n\nHere's the tourism information you requested for Ghana:\n\n"

            if destinations:
                body += "DESTINATIONS:\n"
                for dest_name in destinations:
                    dest = self.get_destination_details(dest_name)
                    if dest.get('success') and dest.get('destination'):
                        d = dest['destination']
                        body += f"\n• {d['name']} ({d['region']} region)\n"
                        body += f"  {d['description']}\n"
                        if d.get('entry_fee'):
                            body += f"  Entry Fee: {d['entry_fee']}\n"
                        if d.get('contact'):
                            body += f"  Contact: {d['contact'].get('phone', 'N/A')}\n"
                body += "\n"

            if accommodations:
                body += "ACCOMMODATIONS:\n"
                for acc_name in accommodations:
                    acc = self.get_accommodation_details(acc_name)
                    if acc.get('success') and acc.get('accommodation'):
                        a = acc['accommodation']
                        body += f"\n• {a['name']} - {a['star_rating']} star {a['type']}\n"
                        body += f"  Location: {a['city']}, {a['region']} region\n"
                        room_types = a.get('room_types', [])
                        if room_types:
                            body += f"  Price Range: {room_types[0]['price_range_ghs']} GHS\n"
                        if a.get('contact'):
                            body += f"  Phone: {a['contact'].get('phone', 'N/A')}\n"
                body += "\n"

            if additional_info:
                body += f"ADDITIONAL INFORMATION:\n{additional_info}\n\n"

            body += "Have a wonderful time in Ghana!\n\n"
            body += "Best regards,\n"
            body += "Ghana Tourism Board\n"
            body += "Visit Ghana - Experience Africa's Warm Hospitality"

            # Send email
            email_message = EmailMessage(
                to=recipient_email,
                subject=subject,
                body=body,
                from_email="noreply@ghanatoursim.gov.gh"
            )

            result = self.email_service.send_email(email_message)

            if result.get('success'):
                voice_response = f"I've sent the tourism information to {recipient_email}. Please check your inbox."
            else:
                voice_response = "There was a problem sending the email. Please try again or note down the information."

            return {
                "success": result.get('success', False),
                "voice_response": voice_response
            }

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {
                "success": False,
                "error": str(e),
                "voice_response": "I couldn't send the email. Please note down the information."
            }

    def escalate_to_tourism_officer(
        self,
        issue_type: str,
        description: str,
        contact_info: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Escalate complex queries to human tourism officer.

        Args:
            issue_type: Type of issue (booking, complaint, special_request, emergency, other)
            description: Description of the issue
            contact_info: Tourist's contact information

        Returns:
            Escalation confirmation and next steps
        """
        try:
            # Log escalation (in production, this would create a ticket)
            logger.info(f"Tourism escalation: {issue_type} - {description}")

            voice_response = "I understand this requires special attention. I'm connecting you to a tourism officer who will assist you. "

            if issue_type == 'emergency':
                voice_response += "For immediate emergencies, please call Police 191 or Ambulance 193. "
            else:
                voice_response += "A tourism officer will contact you shortly. "

            if not contact_info:
                voice_response += "Please provide your phone number or email so we can reach you."

            return {
                "success": True,
                "escalated": True,
                "issue_type": issue_type,
                "timestamp": datetime.now().isoformat(),
                "voice_response": voice_response
            }

        except Exception as e:
            logger.error(f"Error escalating to officer: {e}")
            return {
                "success": False,
                "error": str(e),
                "voice_response": "Please call the Ghana Tourism Board directly for assistance."
            }


# Initialize global instance
ghana_tourism_tools = GhanaTourismTools()


# Export tool functions for VAPI integration
def search_destinations(query: str, region: str = None, category: str = None, max_results: int = 5):
    """Search for tourist destinations in Ghana."""
    return ghana_tourism_tools.search_destinations(query, region, category, max_results)


def get_destination_details(destination_name: str):
    """Get detailed information about a specific destination."""
    return ghana_tourism_tools.get_destination_details(destination_name)


def search_accommodation(location: str, accommodation_type: str = None, budget_max_ghs: int = None, max_results: int = 5):
    """Search for accommodation options."""
    return ghana_tourism_tools.search_accommodation(location, accommodation_type, budget_max_ghs, max_results)


def get_accommodation_details(accommodation_name: str):
    """Get detailed information about specific accommodation."""
    return ghana_tourism_tools.get_accommodation_details(accommodation_name)


def get_visa_requirements(nationality: str = None):
    """Get visa requirements for visiting Ghana."""
    return ghana_tourism_tools.get_visa_requirements(nationality)


def get_sim_card_info(preferred_provider: str = None):
    """Get information about buying SIM cards in Ghana."""
    return ghana_tourism_tools.get_sim_card_info(preferred_provider)


def get_safety_security_tips(category: str = None):
    """Get safety and security tips for tourists."""
    return ghana_tourism_tools.get_safety_security_tips(category)


def get_emergency_contacts():
    """Get emergency contact numbers."""
    return ghana_tourism_tools.get_emergency_contacts()


def get_currency_exchange_info():
    """Get information about currency exchange."""
    return ghana_tourism_tools.get_currency_exchange_info()


def send_tourism_info_email(recipient_email: str, subject: str, destinations: List[str] = None,
                            accommodations: List[str] = None, additional_info: str = None):
    """Send tourism information via email."""
    return ghana_tourism_tools.send_tourism_info_email(recipient_email, subject, destinations,
                                                       accommodations, additional_info)


def escalate_to_tourism_officer(issue_type: str, description: str, contact_info: str = None):
    """Escalate to human tourism officer."""
    return ghana_tourism_tools.escalate_to_tourism_officer(issue_type, description, contact_info)


# Tool schemas for VAPI integration
TOOL_SCHEMAS = {
    "search_destinations": {
        "description": "Search for tourist destinations in Ghana by query, region, or category",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query (e.g., 'beaches near Accra', 'historical sites')"
                },
                "region": {
                    "type": "string",
                    "enum": ["Greater Accra", "Ashanti", "Western", "Eastern", "Volta", "Northern", "Upper East", "Upper West", "Central", "Brong Ahafo"],
                    "description": "Specific region to search in"
                },
                "category": {
                    "type": "string",
                    "enum": ["beach", "historical", "nature", "cultural", "adventure", "wildlife"],
                    "description": "Type of destination"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    "get_destination_details": {
        "description": "Get detailed information about a specific tourist destination",
        "parameters": {
            "type": "object",
            "properties": {
                "destination_name": {
                    "type": "string",
                    "description": "Name of the destination"
                }
            },
            "required": ["destination_name"]
        }
    },
    "search_accommodation": {
        "description": "Search for accommodation (hotels, resorts, lodges) in Ghana",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City or area to search in"
                },
                "accommodation_type": {
                    "type": "string",
                    "enum": ["hotel", "resort", "lodge", "guesthouse"],
                    "description": "Type of accommodation"
                },
                "budget_max_ghs": {
                    "type": "integer",
                    "description": "Maximum budget per night in Ghana Cedis"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 5
                }
            },
            "required": ["location"]
        }
    },
    "get_accommodation_details": {
        "description": "Get detailed information about specific accommodation",
        "parameters": {
            "type": "object",
            "properties": {
                "accommodation_name": {
                    "type": "string",
                    "description": "Name of the hotel/resort/lodge"
                }
            },
            "required": ["accommodation_name"]
        }
    },
    "get_visa_requirements": {
        "description": "Get visa requirements for visiting Ghana based on nationality",
        "parameters": {
            "type": "object",
            "properties": {
                "nationality": {
                    "type": "string",
                    "description": "Tourist's nationality/country"
                }
            }
        }
    },
    "get_sim_card_info": {
        "description": "Get information about buying SIM cards and mobile data plans in Ghana",
        "parameters": {
            "type": "object",
            "properties": {
                "preferred_provider": {
                    "type": "string",
                    "enum": ["MTN", "Vodafone", "AirtelTigo"],
                    "description": "Preferred mobile provider"
                }
            }
        }
    },
    "get_safety_security_tips": {
        "description": "Get safety and security tips for tourists visiting Ghana",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["general", "health", "road", "scams"],
                    "description": "Specific safety category"
                }
            }
        }
    },
    "get_emergency_contacts": {
        "description": "Get emergency contact numbers (police, ambulance, fire, tourist police)",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    "get_currency_exchange_info": {
        "description": "Get information about Ghana's currency, exchange rates, and where to exchange money",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    "send_tourism_info_email": {
        "description": "Send tourism information (destinations, hotels, itinerary) to tourist's email",
        "parameters": {
            "type": "object",
            "properties": {
                "recipient_email": {
                    "type": "string",
                    "description": "Tourist's email address"
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line"
                },
                "destinations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of destination names to include"
                },
                "accommodations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of accommodation names to include"
                },
                "additional_info": {
                    "type": "string",
                    "description": "Additional information to include"
                }
            },
            "required": ["recipient_email", "subject"]
        }
    },
    "escalate_to_tourism_officer": {
        "description": "Escalate complex queries or issues to a human tourism officer",
        "parameters": {
            "type": "object",
            "properties": {
                "issue_type": {
                    "type": "string",
                    "enum": ["booking", "complaint", "special_request", "emergency", "other"],
                    "description": "Type of issue"
                },
                "description": {
                    "type": "string",
                    "description": "Description of the issue or request"
                },
                "contact_info": {
                    "type": "string",
                    "description": "Tourist's contact information (phone or email)"
                }
            },
            "required": ["issue_type", "description"]
        }
    }
}
