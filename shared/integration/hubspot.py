"""
HubSpot Integration Module

This module provides integration with HubSpot for CRM automation,
including contact management, deal tracking, email marketing, and sales workflows.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    import requests
    HUBSPOT_AVAILABLE = True
except ImportError:
    HUBSPOT_AVAILABLE = False
    logging.warning("HubSpot APIs not available. Install requests")

logger = logging.getLogger(__name__)


class HubSpotObjectType(Enum):
    """HubSpot object types."""
    CONTACT = "contacts"
    COMPANY = "companies"
    DEAL = "deals"
    TICKET = "tickets"
    TASK = "tasks"
    MEETING = "meetings"
    CALL = "calls"
    EMAIL = "emails"
    NOTE = "notes"


class HubSpotDealStage(Enum):
    """Common HubSpot deal stages."""
    APPOINTMENTSCHEDULED = "appointmentscheduled"
    QUALIFIEDTOBUY = "qualifiedtobuy"
    PRESENTATIONSCHEDULED = "presentationscheduled"
    DECISIONMAKERBOUGHTIN = "decisionmakerboughtin"
    CONTRACTSENT = "contractsent"
    CLOSEDWON = "closedwon"
    CLOSEDLOST = "closedlost"


class HubSpotContactProperty(Enum):
    """Common HubSpot contact properties."""
    EMAIL = "email"
    FIRSTNAME = "firstname"
    LASTNAME = "lastname"
    PHONE = "phone"
    COMPANY = "company"
    WEBSITE = "website"
    JOBTITLE = "jobtitle"
    LIFECYCLESTAGE = "lifecyclestage"
    LEADSOURCE = "leadsource"


@dataclass
class HubSpotConfig:
    """Configuration for HubSpot integration."""
    access_token: str
    portal_id: Optional[str] = None
    timeout: int = 30
    verify_ssl: bool = True
    base_url: str = "https://api.hubapi.com"
    webhook_secret: Optional[str] = None
    scopes: List[str] = field(default_factory=lambda: [
        "contacts", "companies", "deals", "tickets", "automation"
    ])


@dataclass
class HubSpotContact:
    """HubSpot contact data model."""
    id: Optional[str] = None
    email: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    website: Optional[str] = None
    jobtitle: Optional[str] = None
    lifecyclestage: Optional[str] = None
    leadsource: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class HubSpotDeal:
    """HubSpot deal data model."""
    id: Optional[str] = None
    dealname: Optional[str] = None
    amount: Optional[float] = None
    closedate: Optional[datetime] = None
    dealstage: Optional[str] = None
    pipeline: Optional[str] = None
    dealtype: Optional[str] = None
    description: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    associations: Dict[str, List[str]] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class HubSpotCompany:
    """HubSpot company data model."""
    id: Optional[str] = None
    name: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class HubSpotIntegration:
    """
    HubSpot integration for CRM automation and customer management.

    Provides comprehensive HubSpot functionality including:
    - Contact management
    - Deal tracking
    - Company management
    - Email marketing
    - Workflow automation
    - Analytics and reporting
    """

    def __init__(self, config: HubSpotConfig):
        """
        Initialize HubSpot integration.

        Args:
            config: HubSpot configuration with access token and settings
        """
        self.config = config
        self.session = None
        self._authenticated = False

        if not HUBSPOT_AVAILABLE:
            logger.warning("HubSpot library not available. Install requests")
            return

        # Initialize session
        self._setup_session()

    def _setup_session(self):
        """Setup requests session with authentication."""
        self.session = requests.Session()

        # Determine authentication method based on token format
        if self.config.access_token.startswith('pat-'):
            # Private App Token (newer format) - uses Bearer
            self.session.headers.update({
                'Authorization': f'Bearer {self.config.access_token}',
                'Content-Type': 'application/json',
                'User-Agent': 'KasaAI-HubSpot-Integration/1.0'
            })
        elif self.config.access_token.startswith('na1-') or self.config.access_token.startswith('na2-'):
            # Developer API Key (legacy format) - uses hapikey parameter
            self.session.headers.update({
                'Content-Type': 'application/json',
                'User-Agent': 'KasaAI-HubSpot-Integration/1.0'
            })
            # For developer API keys, we'll add hapikey as a query parameter
            self._use_api_key_auth = True
            self._api_key = self.config.access_token
        else:
            # Default to Bearer for any other format
            self.session.headers.update({
                'Authorization': f'Bearer {self.config.access_token}',
                'Content-Type': 'application/json',
                'User-Agent': 'KasaAI-HubSpot-Integration/1.0'
            })
            self._use_api_key_auth = False

        self.session.verify = self.config.verify_ssl

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make authenticated request to HubSpot API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body data
            params: Query parameters

        Returns:
            API response data
        """
        if not self.session:
            raise Exception("HubSpot session not initialized")

        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"

        # Add API key authentication if using legacy developer key
        if hasattr(self, '_use_api_key_auth') and self._use_api_key_auth:
            if params is None:
                params = {}
            params['hapikey'] = self._api_key

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json() if response.text else {}

        except requests.RequestException as e:
            logger.error(f"HubSpot API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test HubSpot API connection.

        Returns:
            Connection test result
        """
        try:
            # First try with a basic endpoint that requires minimal permissions
            try:
                result = self._make_request('GET', '/integrations/v1/me')

                self._authenticated = True
                return {
                    "success": True,
                    "message": "HubSpot connection successful",
                    "portal_id": result.get("portalId"),
                    "account_name": result.get("accountName"),
                    "scopes": result.get("scopes", []),
                    "authentication_method": "Bearer Token" if not hasattr(self, '_use_api_key_auth') else "Developer API Key"
                }

            except requests.RequestException as e:
                # If main endpoint fails due to scopes, try a more basic test
                if "MISSING_SCOPES" in str(e) or "403" in str(e):
                    # Try a basic CRM properties endpoint which usually has lower permission requirements
                    try:
                        result = self._make_request('GET', '/crm/v3/properties/contacts?limit=1')

                        self._authenticated = True
                        return {
                            "success": True,
                            "message": "HubSpot connection successful (limited scope)",
                            "portal_id": self.config.portal_id,
                            "authentication_method": "Bearer Token" if not hasattr(self, '_use_api_key_auth') else "Developer API Key",
                            "note": "API key has limited permissions. Some features may not be available.",
                            "available_contact_properties": len(result.get("results", []))
                        }
                    except:
                        # Authentication is working but no permissions - inform user
                        self._authenticated = True
                        return {
                            "success": False,
                            "message": "HubSpot API key lacks required scopes",
                            "error": "The provided API key does not have sufficient permissions",
                            "required_scopes": ["oauth", "crm.objects.contacts.read", "crm.objects.deals.read", "crm.objects.companies.read"],
                            "help": "Visit https://developers.hubspot.com/scopes to learn more about required scopes",
                            "portal_id": self.config.portal_id,
                            "authentication_method": "Bearer Token" if not hasattr(self, '_use_api_key_auth') else "Developer API Key"
                        }
                else:
                    raise e

        except Exception as e:
            logger.error(f"HubSpot connection test failed: {e}")

            # Check if it's a scope issue
            error_message = str(e)
            if "MISSING_SCOPES" in error_message:
                return {
                    "success": False,
                    "message": "HubSpot API key lacks required scopes",
                    "error": "The provided API key does not have sufficient permissions. Please ensure your HubSpot app has the required OAuth and CRM scopes.",
                    "required_scopes": ["oauth", "crm.objects.contacts.read", "crm.objects.deals.read", "crm.objects.companies.read"],
                    "help": "Visit https://developers.hubspot.com/scopes to learn more about required scopes"
                }

            return {
                "success": False,
                "message": f"HubSpot connection failed: {str(e)}",
                "error": str(e)
            }

    async def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new contact in HubSpot.

        Args:
            contact_data: Contact information

        Returns:
            Created contact information
        """
        try:
            # Format properties for HubSpot API
            properties = {}
            for key, value in contact_data.items():
                if value is not None:
                    properties[key] = str(value)

            data = {"properties": properties}
            result = self._make_request('POST', '/crm/v3/objects/contacts', data=data)

            return {
                "success": True,
                "contact_id": result.get("id"),
                "contact": result,
                "message": "Contact created successfully"
            }

        except Exception as e:
            logger.error(f"HubSpot create contact failed: {e}")
            return {
                "success": False,
                "message": f"Failed to create contact: {str(e)}",
                "error": str(e)
            }

    async def update_contact(self, contact_id: str, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing contact in HubSpot.

        Args:
            contact_id: HubSpot contact ID
            contact_data: Updated contact information

        Returns:
            Update result
        """
        try:
            # Format properties for HubSpot API
            properties = {}
            for key, value in contact_data.items():
                if value is not None:
                    properties[key] = str(value)

            data = {"properties": properties}
            result = self._make_request('PATCH', f'/crm/v3/objects/contacts/{contact_id}', data=data)

            return {
                "success": True,
                "contact_id": contact_id,
                "contact": result,
                "message": "Contact updated successfully"
            }

        except Exception as e:
            logger.error(f"HubSpot update contact failed: {e}")
            return {
                "success": False,
                "message": f"Failed to update contact: {str(e)}",
                "error": str(e)
            }

    async def get_contact(self, contact_id: str, properties: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get contact information from HubSpot.

        Args:
            contact_id: HubSpot contact ID
            properties: List of properties to retrieve

        Returns:
            Contact information
        """
        try:
            params = {}
            if properties:
                params['properties'] = ','.join(properties)

            result = self._make_request('GET', f'/crm/v3/objects/contacts/{contact_id}', params=params)

            return {
                "success": True,
                "contact": result,
                "contact_id": contact_id
            }

        except Exception as e:
            logger.error(f"HubSpot get contact failed: {e}")
            return {
                "success": False,
                "message": f"Failed to get contact: {str(e)}",
                "error": str(e)
            }

    async def search_contacts(self, filters: Dict[str, Any], limit: int = 100) -> Dict[str, Any]:
        """
        Search for contacts in HubSpot.

        Args:
            filters: Search filters
            limit: Maximum number of results

        Returns:
            Search results
        """
        try:
            # Build search request
            filter_groups = []
            for property_name, value in filters.items():
                filter_groups.append({
                    "filters": [{
                        "propertyName": property_name,
                        "operator": "EQ",
                        "value": str(value)
                    }]
                })

            data = {
                "filterGroups": filter_groups,
                "limit": limit
            }

            result = self._make_request('POST', '/crm/v3/objects/contacts/search', data=data)

            return {
                "success": True,
                "contacts": result.get("results", []),
                "total": result.get("total", 0),
                "has_more": result.get("paging", {}).get("next") is not None
            }

        except Exception as e:
            logger.error(f"HubSpot search contacts failed: {e}")
            return {
                "success": False,
                "message": f"Failed to search contacts: {str(e)}",
                "error": str(e)
            }

    async def create_deal(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new deal in HubSpot.

        Args:
            deal_data: Deal information

        Returns:
            Created deal information
        """
        try:
            # Format properties for HubSpot API
            properties = {}
            for key, value in deal_data.items():
                if value is not None:
                    if key == 'amount' and isinstance(value, (int, float)):
                        properties[key] = str(value)
                    elif key == 'closedate' and isinstance(value, datetime):
                        properties[key] = value.strftime('%Y-%m-%d')
                    else:
                        properties[key] = str(value)

            data = {"properties": properties}
            result = self._make_request('POST', '/crm/v3/objects/deals', data=data)

            return {
                "success": True,
                "deal_id": result.get("id"),
                "deal": result,
                "message": "Deal created successfully"
            }

        except Exception as e:
            logger.error(f"HubSpot create deal failed: {e}")
            return {
                "success": False,
                "message": f"Failed to create deal: {str(e)}",
                "error": str(e)
            }

    async def create_company(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new company in HubSpot.

        Args:
            company_data: Company information

        Returns:
            Created company information
        """
        try:
            # Format properties for HubSpot API
            properties = {}
            for key, value in company_data.items():
                if value is not None:
                    properties[key] = str(value)

            data = {"properties": properties}
            result = self._make_request('POST', '/crm/v3/objects/companies', data=data)

            return {
                "success": True,
                "company_id": result.get("id"),
                "company": result,
                "message": "Company created successfully"
            }

        except Exception as e:
            logger.error(f"HubSpot create company failed: {e}")
            return {
                "success": False,
                "message": f"Failed to create company: {str(e)}",
                "error": str(e)
            }

    async def associate_objects(self, from_object_type: str, from_object_id: str,
                              to_object_type: str, to_object_id: str,
                              association_type: str = "default") -> Dict[str, Any]:
        """
        Create an association between two HubSpot objects.

        Args:
            from_object_type: Source object type
            from_object_id: Source object ID
            to_object_type: Target object type
            to_object_id: Target object ID
            association_type: Type of association

        Returns:
            Association result
        """
        try:
            # Determine association type ID based on object types
            association_type_id = self._get_association_type_id(from_object_type, to_object_type, association_type)

            data = {
                "inputs": [{
                    "from": {"id": from_object_id},
                    "to": {"id": to_object_id},
                    "type": association_type_id
                }]
            }

            result = self._make_request(
                'PUT',
                f'/crm/v3/associations/{from_object_type}/{to_object_type}/batch/create',
                data=data
            )

            return {
                "success": True,
                "association": result,
                "message": "Objects associated successfully"
            }

        except Exception as e:
            logger.error(f"HubSpot associate objects failed: {e}")
            return {
                "success": False,
                "message": f"Failed to associate objects: {str(e)}",
                "error": str(e)
            }

    def _get_association_type_id(self, from_type: str, to_type: str, association_type: str) -> int:
        """Get association type ID for object types."""
        # Common association type IDs
        association_map = {
            ("contacts", "companies"): 1,
            ("contacts", "deals"): 3,
            ("companies", "deals"): 5,
            ("deals", "contacts"): 4,
            ("companies", "contacts"): 2,
            ("deals", "companies"): 6
        }

        return association_map.get((from_type, to_type), 1)

    async def send_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send email through HubSpot.

        Args:
            email_data: Email information

        Returns:
            Send result
        """
        try:
            # Format email for HubSpot API
            data = {
                "emailId": email_data.get("template_id"),
                "message": {
                    "to": email_data.get("to"),
                    "from": email_data.get("from"),
                    "subject": email_data.get("subject"),
                    "body": email_data.get("body")
                },
                "contactProperties": email_data.get("contact_properties", {}),
                "customProperties": email_data.get("custom_properties", {})
            }

            result = self._make_request('POST', '/marketing/v3/transactional/single-email/send', data=data)

            return {
                "success": True,
                "email_id": result.get("id"),
                "message": "Email sent successfully"
            }

        except Exception as e:
            logger.error(f"HubSpot send email failed: {e}")
            return {
                "success": False,
                "message": f"Failed to send email: {str(e)}",
                "error": str(e)
            }

    async def get_analytics(self, object_type: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get analytics data from HubSpot.

        Args:
            object_type: Type of object to analyze
            start_date: Start date for analytics
            end_date: End date for analytics

        Returns:
            Analytics data
        """
        try:
            params = {
                "startDate": start_date.strftime('%Y-%m-%d'),
                "endDate": end_date.strftime('%Y-%m-%d')
            }

            result = self._make_request('GET', f'/analytics/v2/reports/{object_type}', params=params)

            return {
                "success": True,
                "analytics": result,
                "object_type": object_type,
                "period": f"{start_date.date()} to {end_date.date()}"
            }

        except Exception as e:
            logger.error(f"HubSpot get analytics failed: {e}")
            return {
                "success": False,
                "message": f"Failed to get analytics: {str(e)}",
                "error": str(e)
            }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get HubSpot integration capabilities."""
        return {
            "service": "hubspot",
            "capabilities": [
                "create_contact", "update_contact", "get_contact", "search_contacts",
                "create_deal", "create_company", "associate_objects",
                "send_email", "get_analytics", "test_connection"
            ],
            "object_types": [obj.value for obj in HubSpotObjectType],
            "supported_operations": [
                "contact_management", "deal_tracking", "company_management",
                "email_marketing", "object_associations", "analytics_reporting"
            ],
            "authentication": "access_token",
            "mcp_enabled": True,
            "configured": self._authenticated
        }


# Factory function for easy instantiation
def create_hubspot_integration(access_token: str, **kwargs) -> HubSpotIntegration:
    """
    Create HubSpot integration with minimal configuration.

    Args:
        access_token: HubSpot access token
        **kwargs: Additional configuration options

    Returns:
        Configured HubSpot integration instance
    """
    config = HubSpotConfig(
        access_token=access_token,
        **kwargs
    )
    return HubSpotIntegration(config)


# Service class for compatibility
class HubSpotService(HubSpotIntegration):
    """Alias for HubSpotIntegration for service consistency."""
    pass