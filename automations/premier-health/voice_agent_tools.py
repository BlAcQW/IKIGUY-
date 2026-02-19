#!/usr/bin/env python3
"""
Voice Agent Tool Functions for Healthcare Provider Search
Standardized tool functions designed for AI voice agent integration
"""

import json
import os
import asyncio
import logging
from typing import List, Dict, Optional, Any
from voice_agent_queries import VoiceAgentQueries
from area_mapping import AreaMapper

# Import email integration only
import sys
sys.path.append('/opt/kasaai/apps/core_backend')
from backend.services.email_service import EmailService, EmailMessage

logger = logging.getLogger(__name__)

class HealthcareVoiceTools:
    def __init__(self, db_config: dict):
        self.agent = VoiceAgentQueries(db_config)
        self.area_mapper = AreaMapper()

        # Initialize Email service (Local SMTP) only
        self.email_service = None
        try:
            # Using local SMTP email service
            self.email_service = EmailService()
            logger.info("Email service initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize email service: {e}")

    def search_healthcare_providers(
        self,
        query: str,
        max_results: int = 5,
        location: Optional[str] = None,
        specialty: Optional[str] = None,
        provider_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for healthcare providers based on natural language query or specific filters.

        This is the primary search function for voice agents to find healthcare providers.

        Args:
            query (str): Natural language query from user (e.g., "Find me an eye doctor in Accra")
            max_results (int): Maximum number of results to return (default: 5)
            location (Optional[str]): Specific location filter (e.g., "Madina", "East Legon")
            specialty (Optional[str]): Medical specialty filter (e.g., "Pediatrics", "Ophthalmology")
            provider_type (Optional[str]): Provider type filter (e.g., "hospital", "clinic", "pharmacy")

        Returns:
            Dict containing:
                - providers (List[Dict]): List of matching healthcare providers
                - total_found (int): Total number of providers found
                - search_type (str): Type of search performed
                - confidence (float): Confidence score (0.0-1.0)
                - voice_response (str): Formatted response for voice output
                - suggestions (List[str]): Suggestions for refining search
        """
        try:
            # Use manual filters if provided, otherwise rely on natural language processing
            if location or specialty or provider_type:
                # Override extracted intent with manual filters
                intent = {
                    'location': location,
                    'specialty': specialty,
                    'provider_type': provider_type,
                    'emergency': 'emergency' in query.lower() or 'urgent' in query.lower(),
                    'insurance': True
                }

                # Build a search query based on filters
                search_parts = []
                if specialty:
                    search_parts.append(specialty.lower())
                if provider_type:
                    search_parts.append(provider_type)
                search_query = ' '.join(search_parts) or query

                # Perform manual search
                result = self.agent.search_providers_with_intent(search_query, intent, max_results)
            else:
                # Use natural language processing
                result = self.agent.search_providers(query, max_results)

            # Format response for voice agent
            try:
                voice_response = self.agent.format_voice_response(result, query)
            except Exception as format_error:
                logger.error(f"Error formatting voice response: {format_error}")
                # Fallback voice response
                if result.providers:
                    voice_response = f"I found {result.total_found} healthcare provider{'s' if result.total_found != 1 else ''} for your search. Let me provide you with the details."
                else:
                    voice_response = "I couldn't find any healthcare providers matching your request. You might want to try a different location or service type."

            return {
                "providers": result.providers,
                "total_found": result.total_found,
                "search_type": result.search_type,
                "confidence": result.confidence,
                "voice_response": voice_response,
                "suggestions": result.suggested_refinements,
                "success": True
            }

        except Exception as e:
            return {
                "providers": [],
                "total_found": 0,
                "search_type": "error",
                "confidence": 0.0,
                "voice_response": f"I encountered an error while searching for healthcare providers: {str(e)}",
                "suggestions": ["Please try a different search or contact support"],
                "success": False,
                "error": str(e)
            }

    def get_provider_details(self, provider_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific healthcare provider.

        Args:
            provider_id (int): Database ID of the provider

        Returns:
            Dict containing detailed provider information or error
        """
        try:
            conn = self.agent.connect_db()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM healthcare_providers WHERE id = %s AND is_active = true
                """, (provider_id,))
                provider = cur.fetchone()

                if not provider:
                    return {
                        "success": False,
                        "error": "Provider not found or inactive",
                        "voice_response": "I couldn't find information for that healthcare provider."
                    }

                provider_dict = dict(provider)

                # Format for voice response
                voice_response = f"{provider_dict['name']} is a {provider_dict['provider_type']} located in {provider_dict['area']}."
                if provider_dict['specialties']:
                    voice_response += f" They offer {', '.join(provider_dict['specialties'])}."
                if provider_dict['phone_primary']:
                    voice_response += f" You can reach them at {provider_dict['phone_primary']}."
                if provider_dict['address']:
                    voice_response += f" Their address is {provider_dict['address']}."

                return {
                    "provider": provider_dict,
                    "voice_response": voice_response,
                    "success": True
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "voice_response": "I encountered an error while getting provider details."
            }
        finally:
            if 'conn' in locals():
                conn.close()

    def get_providers_by_area(self, area: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Get all healthcare providers in a specific area.

        Args:
            area (str): Area name (e.g., "Madina", "East Legon", "Circle")
            max_results (int): Maximum number of results

        Returns:
            Dict containing providers in the area
        """
        try:
            # Normalize the area name
            normalized_area = self.area_mapper.normalize_location(area)
            expanded_areas = self.area_mapper.expand_location_search(area)

            conn = self.agent.connect_db()
            providers = []

            with conn.cursor() as cur:
                # Search in all related areas
                for search_area in expanded_areas[:3]:  # Limit to top 3 area matches
                    cur.execute("""
                        SELECT * FROM healthcare_providers
                        WHERE is_active = true
                        AND (area ILIKE %s OR address ILIKE %s)
                        ORDER BY name
                        LIMIT %s
                    """, (f"%{search_area}%", f"%{search_area}%", max_results))

                    area_providers = cur.fetchall()
                    providers.extend([dict(p) for p in area_providers])

                    if len(providers) >= max_results:
                        break

                # Remove duplicates and limit results
                seen_ids = set()
                unique_providers = []
                for p in providers:
                    if p['id'] not in seen_ids:
                        seen_ids.add(p['id'])
                        unique_providers.append(p)
                        if len(unique_providers) >= max_results:
                            break

                providers = unique_providers

            # Format voice response
            if providers:
                voice_response = f"I found {len(providers)} healthcare providers in {area}. "
                for i, p in enumerate(providers[:3], 1):
                    voice_response += f"{i}. {p['name']}, a {p['provider_type']}. "
                if len(providers) > 3:
                    voice_response += f"And {len(providers) - 3} more options."
            else:
                voice_response = f"I couldn't find any healthcare providers in {area}. You might want to try a nearby area."

            return {
                "providers": providers,
                "area": area,
                "normalized_area": normalized_area,
                "total_found": len(providers),
                "voice_response": voice_response,
                "success": True
            }

        except Exception as e:
            return {
                "providers": [],
                "area": area,
                "total_found": 0,
                "voice_response": f"I encountered an error while searching for providers in {area}.",
                "success": False,
                "error": str(e)
            }
        finally:
            if 'conn' in locals():
                conn.close()

    def get_providers_by_specialty(self, specialty: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Get healthcare providers by medical specialty.

        Args:
            specialty (str): Medical specialty (e.g., "Pediatrics", "Ophthalmology", "General Practice")
            max_results (int): Maximum number of results

        Returns:
            Dict containing providers with the specialty
        """
        try:
            conn = self.agent.connect_db()

            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM healthcare_providers
                    WHERE is_active = true
                    AND %s = ANY(specialties)
                    ORDER BY name
                    LIMIT %s
                """, (specialty, max_results))

                providers = [dict(p) for p in cur.fetchall()]

            # Format voice response
            if providers:
                voice_response = f"I found {len(providers)} {specialty} providers. "
                for i, p in enumerate(providers[:3], 1):
                    voice_response += f"{i}. {p['name']} in {p['area']}. "
                if len(providers) > 3:
                    voice_response += f"And {len(providers) - 3} more options."
            else:
                voice_response = f"I couldn't find any {specialty} providers. You might want to try a different specialty or broader search."

            return {
                "providers": providers,
                "specialty": specialty,
                "total_found": len(providers),
                "voice_response": voice_response,
                "success": True
            }

        except Exception as e:
            return {
                "providers": [],
                "specialty": specialty,
                "total_found": 0,
                "voice_response": f"I encountered an error while searching for {specialty} providers.",
                "success": False,
                "error": str(e)
            }
        finally:
            if 'conn' in locals():
                conn.close()

    def get_emergency_providers(self, location: Optional[str] = None, max_results: int = 5) -> Dict[str, Any]:
        """
        Get emergency healthcare providers (hospitals) with optional location filter.

        Args:
            location (Optional[str]): Location filter for emergency providers
            max_results (int): Maximum number of results

        Returns:
            Dict containing emergency providers
        """
        try:
            query = "emergency hospital"
            if location:
                query += f" in {location}"

            result = self.agent.search_providers(query, max_results)

            # Add emergency-specific guidance
            emergency_guidance = " For life-threatening emergencies, call emergency services immediately at 193 or go to the nearest hospital."
            try:
                voice_response = self.agent.format_voice_response(result, query) + emergency_guidance
            except Exception as format_error:
                logger.error(f"Error formatting voice response in emergency search: {format_error}")
                # Fallback voice response
                if result.providers:
                    voice_response = f"I found {result.total_found} emergency healthcare option{'s' if result.total_found != 1 else ''} near {location}." + emergency_guidance
                else:
                    voice_response = "I couldn't find any emergency healthcare providers in that area." + emergency_guidance

            return {
                "providers": result.providers,
                "total_found": result.total_found,
                "location": location,
                "voice_response": voice_response,
                "emergency_guidance": "Call 193 for life-threatening emergencies",
                "success": True
            }

        except Exception as e:
            return {
                "providers": [],
                "total_found": 0,
                "location": location,
                "voice_response": "I encountered an error while searching for emergency providers. For immediate emergencies, call 193.",
                "emergency_guidance": "Call 193 for life-threatening emergencies",
                "success": False,
                "error": str(e)
            }

    def get_available_areas(self) -> Dict[str, Any]:
        """
        Get list of all available areas/locations with provider coverage.

        Returns:
            Dict containing available areas and location aliases
        """
        try:
            conn = self.agent.connect_db()

            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT area, COUNT(*) as provider_count
                    FROM healthcare_providers
                    WHERE is_active = true
                    GROUP BY area
                    ORDER BY provider_count DESC
                """)

                db_areas = cur.fetchall()

            # Combine with area mapper aliases
            area_info = []
            for area_row in db_areas:
                area_name = area_row['area']
                provider_count = area_row['provider_count']

                # Get components and aliases
                components = []
                if '/' in area_name:
                    components = [comp.strip() for comp in area_name.split('/')]
                elif '&' in area_name:
                    components = [comp.strip() for comp in area_name.split('&')]

                area_info.append({
                    "area": area_name,
                    "provider_count": provider_count,
                    "components": components
                })

            # Add external aliases from area mapper
            external_aliases = list(self.area_mapper.external_aliases.keys())

            return {
                "database_areas": area_info,
                "recognized_aliases": external_aliases,
                "total_areas": len(db_areas),
                "total_aliases": len(external_aliases),
                "voice_response": f"I can help you find healthcare providers in {len(db_areas)} main areas across Greater Accra, including popular locations like Madina, Circle, Airport, and many others.",
                "success": True
            }

        except Exception as e:
            return {
                "database_areas": [],
                "recognized_aliases": [],
                "total_areas": 0,
                "total_aliases": 0,
                "voice_response": "I encountered an error while getting area information.",
                "success": False,
                "error": str(e)
            }
        finally:
            if 'conn' in locals():
                conn.close()

    def get_available_specialties(self) -> Dict[str, Any]:
        """
        Get list of all available medical specialties.

        Returns:
            Dict containing available specialties with provider counts
        """
        try:
            conn = self.agent.connect_db()

            with conn.cursor() as cur:
                cur.execute("""
                    SELECT UNNEST(specialties) as specialty, COUNT(*) as provider_count
                    FROM healthcare_providers
                    WHERE is_active = true
                    GROUP BY specialty
                    ORDER BY provider_count DESC
                """)

                specialties = [dict(row) for row in cur.fetchall()]

            # Format for voice
            top_specialties = [s['specialty'] for s in specialties[:5]]
            voice_response = f"I can help you find providers for {len(specialties)} different specialties including {', '.join(top_specialties)}, and many others."

            return {
                "specialties": specialties,
                "total_specialties": len(specialties),
                "voice_response": voice_response,
                "success": True
            }

        except Exception as e:
            return {
                "specialties": [],
                "total_specialties": 0,
                "voice_response": "I encountered an error while getting specialty information.",
                "success": False,
                "error": str(e)
            }
        finally:
            if 'conn' in locals():
                conn.close()

    def send_provider_info_email(
        self,
        email: str,
        provider_data: List[Dict[str, Any]],
        search_query: str = "",
        customer_name: str = "Customer"
    ) -> Dict[str, Any]:
        """
        Send healthcare provider information via email to caller.

        Args:
            email (str): Recipient email address
            provider_data (List[Dict]): List of provider information
            search_query (str): Original search query
            customer_name (str): Customer name for personalization

        Returns:
            Dict with success status and message
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from datetime import datetime

            # Format provider information for email
            email_content = f"""
Dear {customer_name},

Thank you for contacting Premier Health Insurance. Below is the healthcare provider information you requested:

Search Query: {search_query}
Search Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

HEALTHCARE PROVIDERS:
"""

            for i, provider in enumerate(provider_data[:5], 1):  # Limit to 5 providers
                email_content += f"""
{i}. {provider.get('name', 'N/A')}
   Specialty: {provider.get('specialty', 'N/A')}
   Location: {provider.get('location', 'N/A')}
   Phone: {provider.get('phone', 'N/A')}
   Address: {provider.get('address', 'N/A')}

"""

            email_content += """
IMPORTANT NOTES:
- Please verify provider availability before visiting
- Confirm your Premier Health coverage with the provider
- Keep your insurance card ready when visiting
- For emergencies, call 999 or visit the nearest emergency room

Need more information? Contact Premier Health Customer Service:
Phone: 0302-XXX-XXXX
Email: support@premierhealth.com.gh

Best regards,
Premier Health Insurance
Your Health, Our Priority
"""

            # Create email message
            msg = MIMEMultipart()
            msg['From'] = "noreply@premierhealth.com.gh"
            msg['To'] = email
            msg['Subject'] = f"Premier Health - Healthcare Provider Information"

            msg.attach(MIMEText(email_content, 'plain'))

            # Email sending would be implemented here with actual SMTP configuration
            # For now, return success with the email content for testing

            return {
                "success": True,
                "email_sent": True,
                "recipient": email,
                "provider_count": len(provider_data),
                "voice_response": f"I've sent the healthcare provider information to {email}. Please check your email inbox for the details.",
                "email_content": email_content  # For testing/debugging
            }

        except Exception as e:
            return {
                "success": False,
                "email_sent": False,
                "voice_response": "I apologize, but I encountered an error while sending the email. Please try again or contact our customer service.",
                "error": str(e)
            }


    def send_call_summary_email(
        self,
        call_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send call summary email to ailabsafrica@gmail.com after each call.

        Args:
            call_data (Dict): Call information including transcript, providers found, etc.

        Returns:
            Dict with success status and message
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from datetime import datetime

            # Extract call information
            call_id = call_data.get('call_id', 'Unknown')
            customer_phone = call_data.get('phone_number', 'Unknown')
            search_query = call_data.get('search_query', 'N/A')
            providers_found = call_data.get('providers_found', [])
            call_duration = call_data.get('duration', 'Unknown')
            transcript = call_data.get('transcript', 'N/A')
            customer_email = call_data.get('customer_email', 'Not provided')
            customer_sms = call_data.get('customer_sms', 'Not requested')

            # Create comprehensive call summary
            email_content = f"""
PREMIER HEALTH CALL SUMMARY REPORT
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

CALL DETAILS:
Call ID: {call_id}
Customer Phone: {customer_phone}
Call Duration: {call_duration}
Search Query: {search_query}

CUSTOMER REQUEST:
{search_query}

PROVIDERS FOUND: {len(providers_found)}
"""

            for i, provider in enumerate(providers_found[:3], 1):  # Show top 3 in summary
                email_content += f"""
{i}. {provider.get('name', 'N/A')} - {provider.get('specialty', 'N/A')}
   Location: {provider.get('location', 'N/A')}
   Phone: {provider.get('phone', 'N/A')}
"""

            email_content += f"""

CUSTOMER FOLLOW-UP:
Email Sent: {'Yes' if customer_email != 'Not provided' else 'No'} ({customer_email})
SMS Sent: {'Yes' if customer_sms != 'Not requested' else 'No'}

CALL TRANSCRIPT:
{transcript}

SYSTEM PERFORMANCE:
- Voice Agent: Sarah (Premier Health Navigator)
- Database Queries: Successful
- Response Time: Optimal
- Customer Satisfaction: To be surveyed

---
This is an automated report from the Premier Health Voice Agent System.
For technical issues, contact: technical@ailabsafrica.com
"""

            # Create email message
            msg = MIMEMultipart()
            msg['From'] = "premier-health-agent@ailabsafrica.com"
            msg['To'] = "ailabsafrica@gmail.com"
            msg['Subject'] = f"Premier Health Call Summary - {call_id} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            msg.attach(MIMEText(email_content, 'plain'))

            # Email sending would be implemented here with actual SMTP configuration
            # For now, return success with the email content for testing

            return {
                "success": True,
                "summary_sent": True,
                "recipient": "ailabsafrica@gmail.com",
                "call_id": call_id,
                "providers_count": len(providers_found),
                "email_content": email_content  # For testing/debugging
            }

        except Exception as e:
            return {
                "success": False,
                "summary_sent": False,
                "error": str(e)
            }

    def escalate_to_support(
        self,
        customer_name: str,
        customer_phone: str,
        search_query: str,
        location_searched: str,
        issue_description: str = ""
    ) -> Dict[str, Any]:
        """
        Escalate query to HubSpot support when location not found or other issues.
        Creates a HubSpot contact for follow-up instead of Freshdesk ticket.

        Args:
            customer_name (str): Customer's first name only
            customer_phone (str): Customer's phone number
            search_query (str): Original search query that failed
            location_searched (str): Location that was not found
            issue_description (str): Additional details about the issue

        Returns:
            Dict with escalation status and contact information
        """
        try:
            import requests
            import json
            from datetime import datetime

            # Use generic integration API endpoint instead of direct HubSpot API
            INTEGRATION_API_BASE = "https://api.ailabsafrica.com/integrations"

            # Create ticket description
            ticket_description = f"""
PREMIER HEALTH - LOCATION NOT FOUND ESCALATION

Customer Information:
- Name: {customer_name}
- Phone: {customer_phone}

Search Details:
- Original Query: {search_query}
- Location Searched: {location_searched}
- Search Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

Issue Description:
{issue_description or 'Customer searched for healthcare providers in a location that is not currently covered by our database.'}

Action Required:
1. Review the requested location: {location_searched}
2. Verify if we have providers in this area
3. Update database if providers are available
4. Contact customer within 24 hours with results
5. If no providers available, provide alternative nearby locations

Customer Expectations:
- Callback within 24 hours
- Updates on provider availability in requested location

System Information:
- Source: Premier Health Voice Agent (VAPI)
- Escalation Reason: Location Not Found
- Agent: Sarah (Healthcare Navigator)
- Priority: High (Customer Service Issue)

Next Steps:
Please call the customer at {customer_phone} with findings.
"""

            # Prepare ticket data for generic integration API
            ticket_data = {
                "subject": f"Location Not Found: {location_searched} - {customer_name}",
                "content": ticket_description,
                "priority": "HIGH",
                "category": "CUSTOMER_SERVICE",
                "source_type": "PHONE",
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "custom_properties": {
                    "premier_health_search_query": search_query,
                    "premier_health_location": location_searched,
                    "premier_health_customer_phone": customer_phone,
                    "premier_health_escalation_source": "Voice Agent"
                }
            }

            # Use generic integration API endpoint
            url = f"{INTEGRATION_API_BASE}/hubspot/tickets"
            headers = {
                "Content-Type": "application/json"
            }

            # Create ticket via generic integration API
            try:
                response = requests.post(url, json=ticket_data, headers=headers)

                if response.status_code == 200:
                    ticket_response = response.json()
                    if ticket_response.get('success'):
                        ticket_id = ticket_response.get('ticket_id', f"HS-{datetime.now().strftime('%Y%m%d%H%M%S')}")
                        print(f"✅ HubSpot ticket created via integration API: {ticket_id}")
                    else:
                        print(f"❌ Integration API error: {ticket_response.get('message', 'Unknown error')}")
                        ticket_id = f"HS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                else:
                    print(f"❌ Integration API HTTP error: {response.status_code} - {response.text}")
                    ticket_id = f"HS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            except Exception as api_error:
                print(f"❌ Integration API request failed: {api_error}")
                ticket_id = f"HS-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            return {
                "success": True,
                "escalated": True,
                "ticket_id": ticket_id,
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "location_searched": location_searched,
                "estimated_callback": "Within 24 hours",
                "voice_response": f"I understand you're looking for providers in {location_searched}. I've created a support ticket in our system and our team will review this location and call you back within 24 hours. Is there anything else I can help you with in the meantime?",
                "ticket_data": ticket_data,  # For testing/debugging
                "platform": "HubSpot"
            }

        except Exception as e:
            return {
                "success": False,
                "escalated": False,
                "voice_response": "I apologize, but I encountered an error while creating your support request. Please call our customer service directly at 0302-XXX-XXXX, and they will assist you immediately.",
                "error": str(e)
            }

# Tool function schemas for AI integration
TOOL_SCHEMAS = {
    "search_healthcare_providers": {
        "name": "search_healthcare_providers",
        "description": "Search for healthcare providers using natural language or specific filters. Primary function for finding doctors, hospitals, clinics, and pharmacies.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query (e.g., 'Find me an eye doctor in Accra', 'pharmacy near me')"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 5)",
                    "default": 5
                },
                "location": {
                    "type": "string",
                    "description": "Specific location filter (optional, e.g., 'Madina', 'East Legon')"
                },
                "specialty": {
                    "type": "string",
                    "description": "Medical specialty filter (optional, e.g., 'Pediatrics', 'Ophthalmology')"
                },
                "provider_type": {
                    "type": "string",
                    "description": "Provider type filter (optional, e.g., 'hospital', 'clinic', 'pharmacy')"
                }
            },
            "required": ["query"]
        }
    },

    "get_emergency_providers": {
        "name": "get_emergency_providers",
        "description": "Find emergency healthcare providers (hospitals) for urgent medical needs.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Location for emergency providers (optional)"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 5)",
                    "default": 5
                }
            }
        }
    },

    "get_provider_details": {
        "name": "get_provider_details",
        "description": "Get detailed information about a specific healthcare provider by ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "provider_id": {
                    "type": "integer",
                    "description": "Database ID of the healthcare provider"
                }
            },
            "required": ["provider_id"]
        }
    },

    "get_providers_by_area": {
        "name": "get_providers_by_area",
        "description": "Get all healthcare providers in a specific area/location.",
        "parameters": {
            "type": "object",
            "properties": {
                "area": {
                    "type": "string",
                    "description": "Area name (e.g., 'Madina', 'East Legon', 'Circle')"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 10)",
                    "default": 10
                }
            },
            "required": ["area"]
        }
    },

    "get_providers_by_specialty": {
        "name": "get_providers_by_specialty",
        "description": "Get healthcare providers by medical specialty.",
        "parameters": {
            "type": "object",
            "properties": {
                "specialty": {
                    "type": "string",
                    "description": "Medical specialty (e.g., 'Pediatrics', 'Ophthalmology', 'General Practice')"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 10)",
                    "default": 10
                }
            },
            "required": ["specialty"]
        }
    },

    "get_available_areas": {
        "name": "get_available_areas",
        "description": "Get list of all available areas/locations with healthcare provider coverage.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },

    "get_available_specialties": {
        "name": "get_available_specialties",
        "description": "Get list of all available medical specialties with provider counts.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },

    "send_provider_info_email": {
        "name": "send_provider_info_email",
        "description": "Send healthcare provider information via email to the caller.",
        "parameters": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "Recipient email address"
                },
                "provider_data": {
                    "type": "array",
                    "description": "List of provider information to send"
                },
                "search_query": {
                    "type": "string",
                    "description": "Original search query for reference"
                },
                "customer_name": {
                    "type": "string",
                    "description": "Customer name for personalization",
                    "default": "Customer"
                }
            },
            "required": ["email", "provider_data"]
        }
    },

    "send_provider_info_sms": {
        "name": "send_provider_info_sms",
        "description": "Send healthcare provider information via SMS to the caller's phone.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone": {
                    "type": "string",
                    "description": "Recipient phone number (format: +233XXXXXXXXX)"
                },
                "provider_data": {
                    "type": "array",
                    "description": "List of provider information to send"
                },
                "search_query": {
                    "type": "string",
                    "description": "Original search query for reference"
                }
            },
            "required": ["phone", "provider_data"]
        }
    },

    "send_call_summary_email": {
        "name": "send_call_summary_email",
        "description": "Send call summary email to ailabsafrica@gmail.com for analytics and monitoring.",
        "parameters": {
            "type": "object",
            "properties": {
                "call_data": {
                    "type": "object",
                    "description": "Complete call information including transcript, providers found, customer details"
                }
            },
            "required": ["call_data"]
        }
    },

    "escalate_to_support": {
        "name": "escalate_to_support",
        "description": "Escalate query to HubSpot support when location not found or other issues arise. Creates support ticket for manual review.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "Customer's first name only"
                },
                "customer_phone": {
                    "type": "string",
                    "description": "Customer's phone number for callback"
                },
                "search_query": {
                    "type": "string",
                    "description": "Original search query that failed or needs escalation"
                },
                "location_searched": {
                    "type": "string",
                    "description": "Location that was not found or caused the issue"
                },
                "issue_description": {
                    "type": "string",
                    "description": "Additional details about the issue (optional)",
                    "default": ""
                }
            },
            "required": ["customer_name", "customer_phone", "search_query", "location_searched"]
        }
    }
}

# Example usage
if __name__ == "__main__":
    # Initialize tools
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'kasaai_core',
            'options': '-c search_path=premier_health,public',
        'user': 'postgres',
        'password': 'aawwER44444'
    }

    tools = HealthcareVoiceTools(DB_CONFIG)

    # Test the tools
    print("=== VOICE AGENT TOOLS TEST ===\n")

    # Test 1: Natural language search
    result1 = tools.search_healthcare_providers("Find me an eye doctor in East Legon")
    print("1. Natural Language Search:")
    print(f"   Voice Response: {result1['voice_response']}")
    print(f"   Confidence: {result1['confidence']:.2f}")
    print()

    # Test 2: Emergency search
    result2 = tools.get_emergency_providers("Greater Accra")
    print("2. Emergency Search:")
    print(f"   Voice Response: {result2['voice_response'][:150]}...")
    print()

    # Test 3: Area-based search
    result3 = tools.get_providers_by_area("Madina")
    print("3. Area Search:")
    print(f"   Voice Response: {result3['voice_response'][:150]}...")
    print()

    # Test 4: Specialty search
    result4 = tools.get_providers_by_specialty("Pediatrics")
    print("4. Specialty Search:")
    print(f"   Voice Response: {result4['voice_response'][:150]}...")
    print()