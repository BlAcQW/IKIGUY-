"""
FindHelp.org Integration Module

This module provides integration with FindHelp.org for healthcare resource discovery,
social services, and community health support with comprehensive REST API support.
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
    FINDHELP_AVAILABLE = True
except ImportError:
    FINDHELP_AVAILABLE = False
    logging.warning("FindHelp.org APIs not available. Install requests")

logger = logging.getLogger(__name__)


class FindHelpCategory(Enum):
    """FindHelp.org service categories."""
    HEALTHCARE = "healthcare"
    MENTAL_HEALTH = "mental_health"
    SUBSTANCE_ABUSE = "substance_abuse"
    HOUSING = "housing"
    FOOD = "food"
    TRANSPORTATION = "transportation"
    LEGAL = "legal"
    EDUCATION = "education"
    EMPLOYMENT = "employment"
    FINANCIAL = "financial"
    UTILITIES = "utilities"
    CHILDCARE = "childcare"
    SENIOR_SERVICES = "senior_services"
    DISABILITY = "disability"
    VETERANS = "veterans"


class FindHelpServiceType(Enum):
    """FindHelp.org service types."""
    CLINIC = "clinic"
    HOSPITAL = "hospital"
    PHARMACY = "pharmacy"
    COUNSELING = "counseling"
    SHELTER = "shelter"
    FOOD_BANK = "food_bank"
    TRANSPORT = "transport"
    LEGAL_AID = "legal_aid"
    JOB_TRAINING = "job_training"
    FINANCIAL_AID = "financial_aid"
    UTILITY_ASSISTANCE = "utility_assistance"
    CHILDCARE_CENTER = "childcare_center"
    SENIOR_CENTER = "senior_center"
    DISABILITY_SERVICE = "disability_service"
    VETERANS_SERVICE = "veterans_service"


class FindHelpAvailability(Enum):
    """FindHelp.org availability status."""
    AVAILABLE = "available"
    LIMITED = "limited"
    UNAVAILABLE = "unavailable"
    WAITLIST = "waitlist"
    APPOINTMENT_REQUIRED = "appointment_required"


@dataclass
class FindHelpConfig:
    """Configuration for FindHelp.org integration."""
    api_key: str
    organization_id: str
    base_url: str = "https://api.findhelp.org/v1"
    timeout: int = 30
    verify_ssl: bool = True
    api_version: str = "v1"


@dataclass
class FindHelpOrganization:
    """FindHelp.org organization data."""
    organization_id: str
    name: str
    description: str = ""
    category: FindHelpCategory = FindHelpCategory.HEALTHCARE
    service_type: FindHelpServiceType = FindHelpServiceType.CLINIC
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    country: str = "US"
    latitude: float = 0.0
    longitude: float = 0.0
    phone: str = ""
    email: str = ""
    website: str = ""
    hours: Dict[str, str] = field(default_factory=dict)
    availability: FindHelpAvailability = FindHelpAvailability.AVAILABLE
    eligibility_criteria: List[str] = field(default_factory=list)
    required_documents: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    accessibility_features: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FindHelpService:
    """FindHelp.org service data."""
    service_id: str
    organization_id: str
    name: str
    description: str = ""
    category: FindHelpCategory = FindHelpCategory.HEALTHCARE
    service_type: FindHelpServiceType = FindHelpServiceType.CLINIC
    cost: str = "Free"
    eligibility: str = ""
    hours: Dict[str, str] = field(default_factory=dict)
    availability: FindHelpAvailability = FindHelpAvailability.AVAILABLE
    wait_time: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FindHelpSearchResult:
    """FindHelp.org search result data."""
    organizations: List[FindHelpOrganization] = field(default_factory=list)
    services: List[FindHelpService] = field(default_factory=list)
    total_count: int = 0
    page: int = 1
    page_size: int = 20
    search_query: str = ""
    filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FindHelpReferral:
    """FindHelp.org referral data."""
    referral_id: str
    client_id: str
    organization_id: str
    service_id: str
    status: str = "pending"
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FindHelpClient:
    """FindHelp.org client data."""
    client_id: str
    first_name: str
    last_name: str
    email: str = ""
    phone: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    date_of_birth: Optional[datetime] = None
    household_size: int = 1
    income_level: str = ""
    languages: List[str] = field(default_factory=list)
    needs: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class FindHelpIntegration:
    """FindHelp.org integration for healthcare resource discovery."""
    
    def __init__(self, config: FindHelpConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.verify_ssl
        
        self.session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "X-Organization-ID": config.organization_id
        })
        
        self.base_url = f"{config.base_url}/{config.api_version}"
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to FindHelp.org API."""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            raise
    
    async def search_organizations(self, query: str = "", category: Optional[FindHelpCategory] = None,
                                  service_type: Optional[FindHelpServiceType] = None,
                                  location: Optional[str] = None, latitude: Optional[float] = None,
                                  longitude: Optional[float] = None, radius: Optional[float] = None,
                                  page: int = 1, page_size: int = 20) -> FindHelpSearchResult:
        """Search for organizations."""
        params = {
            "query": query,
            "page": page,
            "page_size": page_size
        }
        
        if category:
            params["category"] = category.value
        if service_type:
            params["service_type"] = service_type.value
        if location:
            params["location"] = location
        if latitude and longitude:
            params["latitude"] = latitude
            params["longitude"] = longitude
        if radius:
            params["radius"] = radius
        
        response = await asyncio.to_thread(
            self._make_request, "GET", "organizations/search", params=params
        )
        
        organizations = []
        for org_data in response["organizations"]:
            organizations.append(FindHelpOrganization(
                organization_id=org_data["organization_id"],
                name=org_data["name"],
                description=org_data.get("description", ""),
                category=FindHelpCategory(org_data["category"]),
                service_type=FindHelpServiceType(org_data["service_type"]),
                address=org_data.get("address", ""),
                city=org_data.get("city", ""),
                state=org_data.get("state", ""),
                zip_code=org_data.get("zip_code", ""),
                country=org_data.get("country", "US"),
                latitude=org_data.get("latitude", 0.0),
                longitude=org_data.get("longitude", 0.0),
                phone=org_data.get("phone", ""),
                email=org_data.get("email", ""),
                website=org_data.get("website", ""),
                hours=org_data.get("hours", {}),
                availability=FindHelpAvailability(org_data.get("availability", "available")),
                eligibility_criteria=org_data.get("eligibility_criteria", []),
                required_documents=org_data.get("required_documents", []),
                languages=org_data.get("languages", []),
                accessibility_features=org_data.get("accessibility_features", []),
                is_active=org_data.get("is_active", True),
                created_at=datetime.fromisoformat(org_data["created_at"]),
                updated_at=datetime.fromisoformat(org_data["updated_at"]),
                metadata=org_data
            ))
        
        return FindHelpSearchResult(
            organizations=organizations,
            total_count=response["total_count"],
            page=page,
            page_size=page_size,
            search_query=query,
            filters=params
        )
    
    async def get_organization(self, organization_id: str) -> FindHelpOrganization:
        """Get organization details."""
        response = await asyncio.to_thread(
            self._make_request, "GET", f"organizations/{organization_id}"
        )
        
        return FindHelpOrganization(
            organization_id=response["organization_id"],
            name=response["name"],
            description=response.get("description", ""),
            category=FindHelpCategory(response["category"]),
            service_type=FindHelpServiceType(response["service_type"]),
            address=response.get("address", ""),
            city=response.get("city", ""),
            state=response.get("state", ""),
            zip_code=response.get("zip_code", ""),
            country=response.get("country", "US"),
            latitude=response.get("latitude", 0.0),
            longitude=response.get("longitude", 0.0),
            phone=response.get("phone", ""),
            email=response.get("email", ""),
            website=response.get("website", ""),
            hours=response.get("hours", {}),
            availability=FindHelpAvailability(response.get("availability", "available")),
            eligibility_criteria=response.get("eligibility_criteria", []),
            required_documents=response.get("required_documents", []),
            languages=response.get("languages", []),
            accessibility_features=response.get("accessibility_features", []),
            is_active=response.get("is_active", True),
            created_at=datetime.fromisoformat(response["created_at"]),
            updated_at=datetime.fromisoformat(response["updated_at"]),
            metadata=response
        )
    
    async def get_organization_services(self, organization_id: str) -> List[FindHelpService]:
        """Get services offered by an organization."""
        response = await asyncio.to_thread(
            self._make_request, "GET", f"organizations/{organization_id}/services"
        )
        
        services = []
        for service_data in response["services"]:
            services.append(FindHelpService(
                service_id=service_data["service_id"],
                organization_id=organization_id,
                name=service_data["name"],
                description=service_data.get("description", ""),
                category=FindHelpCategory(service_data["category"]),
                service_type=FindHelpServiceType(service_data["service_type"]),
                cost=service_data.get("cost", "Free"),
                eligibility=service_data.get("eligibility", ""),
                hours=service_data.get("hours", {}),
                availability=FindHelpAvailability(service_data.get("availability", "available")),
                wait_time=service_data.get("wait_time"),
                is_active=service_data.get("is_active", True),
                created_at=datetime.fromisoformat(service_data["created_at"]),
                updated_at=datetime.fromisoformat(service_data["updated_at"]),
                metadata=service_data
            ))
        
        return services
    
    async def search_services(self, query: str = "", category: Optional[FindHelpCategory] = None,
                             service_type: Optional[FindHelpServiceType] = None,
                             location: Optional[str] = None, latitude: Optional[float] = None,
                             longitude: Optional[float] = None, radius: Optional[float] = None,
                             page: int = 1, page_size: int = 20) -> FindHelpSearchResult:
        """Search for services."""
        params = {
            "query": query,
            "page": page,
            "page_size": page_size
        }
        
        if category:
            params["category"] = category.value
        if service_type:
            params["service_type"] = service_type.value
        if location:
            params["location"] = location
        if latitude and longitude:
            params["latitude"] = latitude
            params["longitude"] = longitude
        if radius:
            params["radius"] = radius
        
        response = await asyncio.to_thread(
            self._make_request, "GET", "services/search", params=params
        )
        
        services = []
        for service_data in response["services"]:
            services.append(FindHelpService(
                service_id=service_data["service_id"],
                organization_id=service_data["organization_id"],
                name=service_data["name"],
                description=service_data.get("description", ""),
                category=FindHelpCategory(service_data["category"]),
                service_type=FindHelpServiceType(service_data["service_type"]),
                cost=service_data.get("cost", "Free"),
                eligibility=service_data.get("eligibility", ""),
                hours=service_data.get("hours", {}),
                availability=FindHelpAvailability(service_data.get("availability", "available")),
                wait_time=service_data.get("wait_time"),
                is_active=service_data.get("is_active", True),
                created_at=datetime.fromisoformat(service_data["created_at"]),
                updated_at=datetime.fromisoformat(service_data["updated_at"]),
                metadata=service_data
            ))
        
        return FindHelpSearchResult(
            services=services,
            total_count=response["total_count"],
            page=page,
            page_size=page_size,
            search_query=query,
            filters=params
        )
    
    async def create_client(self, first_name: str, last_name: str, email: str = "",
                           phone: str = "", address: str = "", city: str = "",
                           state: str = "", zip_code: str = "", date_of_birth: Optional[datetime] = None,
                           household_size: int = 1, income_level: str = "",
                           languages: Optional[List[str]] = None, needs: Optional[List[str]] = None) -> FindHelpClient:
        """Create a new client."""
        data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "address": address,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "household_size": household_size,
            "income_level": income_level
        }
        
        if date_of_birth:
            data["date_of_birth"] = date_of_birth.isoformat()
        if languages:
            data["languages"] = languages
        if needs:
            data["needs"] = needs
        
        response = await asyncio.to_thread(
            self._make_request, "POST", "clients", data
        )
        
        return FindHelpClient(
            client_id=response["client_id"],
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            date_of_birth=date_of_birth,
            household_size=household_size,
            income_level=income_level,
            languages=languages or [],
            needs=needs or [],
            created_at=datetime.fromisoformat(response["created_at"]),
            metadata=response
        )
    
    async def get_client(self, client_id: str) -> FindHelpClient:
        """Get client details."""
        response = await asyncio.to_thread(
            self._make_request, "GET", f"clients/{client_id}"
        )
        
        return FindHelpClient(
            client_id=response["client_id"],
            first_name=response["first_name"],
            last_name=response["last_name"],
            email=response.get("email", ""),
            phone=response.get("phone", ""),
            address=response.get("address", ""),
            city=response.get("city", ""),
            state=response.get("state", ""),
            zip_code=response.get("zip_code", ""),
            date_of_birth=datetime.fromisoformat(response["date_of_birth"]) if response.get("date_of_birth") else None,
            household_size=response.get("household_size", 1),
            income_level=response.get("income_level", ""),
            languages=response.get("languages", []),
            needs=response.get("needs", []),
            is_active=response.get("is_active", True),
            created_at=datetime.fromisoformat(response["created_at"]),
            updated_at=datetime.fromisoformat(response["updated_at"]),
            metadata=response
        )
    
    async def create_referral(self, client_id: str, organization_id: str, service_id: str,
                             notes: str = "") -> FindHelpReferral:
        """Create a referral for a client."""
        data = {
            "client_id": client_id,
            "organization_id": organization_id,
            "service_id": service_id,
            "notes": notes
        }
        
        response = await asyncio.to_thread(
            self._make_request, "POST", "referrals", data
        )
        
        return FindHelpReferral(
            referral_id=response["referral_id"],
            client_id=client_id,
            organization_id=organization_id,
            service_id=service_id,
            status=response.get("status", "pending"),
            notes=notes,
            created_at=datetime.fromisoformat(response["created_at"]),
            metadata=response
        )
    
    async def get_client_referrals(self, client_id: str) -> List[FindHelpReferral]:
        """Get referrals for a client."""
        response = await asyncio.to_thread(
            self._make_request, "GET", f"clients/{client_id}/referrals"
        )
        
        referrals = []
        for ref_data in response["referrals"]:
            referrals.append(FindHelpReferral(
                referral_id=ref_data["referral_id"],
                client_id=client_id,
                organization_id=ref_data["organization_id"],
                service_id=ref_data["service_id"],
                status=ref_data.get("status", "pending"),
                notes=ref_data.get("notes", ""),
                created_at=datetime.fromisoformat(ref_data["created_at"]),
                updated_at=datetime.fromisoformat(ref_data["updated_at"]),
                metadata=ref_data
            ))
        
        return referrals
    
    async def update_referral_status(self, referral_id: str, status: str, notes: str = "") -> FindHelpReferral:
        """Update referral status."""
        data = {
            "status": status,
            "notes": notes
        }
        
        response = await asyncio.to_thread(
            self._make_request, "PUT", f"referrals/{referral_id}", data
        )
        
        return FindHelpReferral(
            referral_id=referral_id,
            client_id=response["client_id"],
            organization_id=response["organization_id"],
            service_id=response["service_id"],
            status=status,
            notes=notes,
            created_at=datetime.fromisoformat(response["created_at"]),
            updated_at=datetime.fromisoformat(response["updated_at"]),
            metadata=response
        )
    
    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get available service categories."""
        response = await asyncio.to_thread(
            self._make_request, "GET", "categories"
        )
        
        return response["categories"]
    
    async def get_service_types(self) -> List[Dict[str, Any]]:
        """Get available service types."""
        response = await asyncio.to_thread(
            self._make_request, "GET", "service-types"
        )
        
        return response["service_types"]
    
    async def health_check(self) -> Dict[str, Any]:
        """Test API connectivity and health."""
        try:
            response = await asyncio.to_thread(
                self._make_request, "GET", "health"
            )
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "details": response
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
