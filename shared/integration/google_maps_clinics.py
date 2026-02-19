"""
Google Maps for Clinics Integration Module

This module provides integration with Google Maps for healthcare location services,
clinic discovery, and medical facility mapping with comprehensive REST API support.
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
    GOOGLE_MAPS_CLINICS_AVAILABLE = True
except ImportError:
    GOOGLE_MAPS_CLINICS_AVAILABLE = False
    logging.warning("Google Maps for Clinics APIs not available. Install requests")

logger = logging.getLogger(__name__)


class ClinicType(Enum):
    """Clinic types."""
    HOSPITAL = "hospital"
    CLINIC = "clinic"
    PHARMACY = "pharmacy"
    LABORATORY = "laboratory"
    DENTAL_CLINIC = "dental_clinic"
    EYE_CLINIC = "eye_clinic"
    MATERNITY_CLINIC = "maternity_clinic"
    PEDIATRIC_CLINIC = "pediatric_clinic"
    EMERGENCY_CENTER = "emergency_center"
    URGENT_CARE = "urgent_care"
    SPECIALIST_CLINIC = "specialist_clinic"
    REHABILITATION_CENTER = "rehabilitation_center"
    MENTAL_HEALTH_CLINIC = "mental_health_clinic"
    VACCINATION_CENTER = "vaccination_center"
    BLOOD_BANK = "blood_bank"


class ClinicSpecialty(Enum):
    """Clinic specialties."""
    GENERAL_MEDICINE = "general_medicine"
    CARDIOLOGY = "cardiology"
    DERMATOLOGY = "dermatology"
    ENDOCRINOLOGY = "endocrinology"
    GASTROENTEROLOGY = "gastroenterology"
    GYNECOLOGY = "gynecology"
    NEUROLOGY = "neurology"
    ONCOLOGY = "oncology"
    ORTHOPEDICS = "orthopedics"
    PEDIATRICS = "pediatrics"
    PSYCHIATRY = "psychiatry"
    RADIOLOGY = "radiology"
    SURGERY = "surgery"
    UROLOGY = "urology"
    OPHTHALMOLOGY = "ophthalmology"
    DENTISTRY = "dentistry"


class ClinicAvailability(Enum):
    """Clinic availability status."""
    OPEN = "open"
    CLOSED = "closed"
    OPEN_24_7 = "open_24_7"
    APPOINTMENT_ONLY = "appointment_only"
    EMERGENCY_ONLY = "emergency_only"
    TEMPORARILY_CLOSED = "temporarily_closed"


class InsuranceType(Enum):
    """Insurance types accepted."""
    PRIVATE = "private"
    PUBLIC = "public"
    MEDICARE = "medicare"
    MEDICAID = "medicaid"
    WORKERS_COMP = "workers_comp"
    AUTO_INSURANCE = "auto_insurance"
    NONE = "none"


@dataclass
class GoogleMapsClinicsConfig:
    """Configuration for Google Maps for Clinics integration."""
    api_key: str
    project_id: str
    base_url: str = "https://maps.googleapis.com/maps/api"
    timeout: int = 30
    verify_ssl: bool = True
    api_version: str = "v1"


@dataclass
class ClinicLocation:
    """Clinic location data."""
    place_id: str
    name: str
    address: str
    city: str
    state: str
    country: str
    postal_code: str
    latitude: float
    longitude: float
    phone: str = ""
    website: str = ""
    email: str = ""
    clinic_type: ClinicType = ClinicType.CLINIC
    specialties: List[ClinicSpecialty] = field(default_factory=list)
    availability: ClinicAvailability = ClinicAvailability.OPEN
    rating: float = 0.0
    review_count: int = 0
    price_level: int = 0
    is_verified: bool = False
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClinicHours:
    """Clinic operating hours."""
    clinic_id: str
    day_of_week: int  # 0=Monday, 6=Sunday
    open_time: str
    close_time: str
    is_closed: bool = False
    is_24_hours: bool = False


@dataclass
class ClinicService:
    """Clinic service data."""
    service_id: str
    clinic_id: str
    name: str
    description: str = ""
    specialty: Optional[ClinicSpecialty] = None
    is_available: bool = True
    price_range: str = ""
    insurance_accepted: List[InsuranceType] = field(default_factory=list)
    appointment_required: bool = False
    wait_time: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClinicReview:
    """Clinic review data."""
    review_id: str
    clinic_id: str
    author_name: str
    rating: int
    text: str = ""
    time: datetime = field(default_factory=datetime.now)
    language: str = "en"
    is_verified: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClinicSearchResult:
    """Clinic search result data."""
    clinics: List[ClinicLocation] = field(default_factory=list)
    total_count: int = 0
    page: int = 1
    page_size: int = 20
    search_query: str = ""
    location: str = ""
    radius: float = 0.0
    filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RouteInfo:
    """Route information to clinic."""
    clinic_id: str
    origin_lat: float
    origin_lng: float
    destination_lat: float
    destination_lng: float
    distance_km: float
    duration_minutes: int
    travel_mode: str = "driving"
    route_polyline: str = ""
    traffic_info: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class GoogleMapsClinicsIntegration:
    """Google Maps for Clinics integration for healthcare location services."""
    
    def __init__(self, config: GoogleMapsClinicsConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.verify_ssl
        
        self.base_url = f"{config.base_url}/{config.api_version}"
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to Google Maps for Clinics API."""
        url = f"{self.base_url}/{endpoint}"
        
        # Add API key to all requests
        if params is None:
            params = {}
        params["key"] = self.config.api_key
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, params=params)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, params=params)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            raise
    
    async def search_clinics(self, query: str = "", location: Optional[str] = None,
                            latitude: Optional[float] = None, longitude: Optional[float] = None,
                            radius: Optional[float] = None, clinic_type: Optional[ClinicType] = None,
                            specialty: Optional[ClinicSpecialty] = None, insurance: Optional[InsuranceType] = None,
                            open_now: bool = False, page: int = 1, page_size: int = 20) -> ClinicSearchResult:
        """Search for clinics."""
        params = {
            "query": query,
            "page": page,
            "page_size": page_size
        }
        
        if location:
            params["location"] = location
        if latitude and longitude:
            params["latitude"] = latitude
            params["longitude"] = longitude
        if radius:
            params["radius"] = radius
        if clinic_type:
            params["clinic_type"] = clinic_type.value
        if specialty:
            params["specialty"] = specialty.value
        if insurance:
            params["insurance"] = insurance.value
        if open_now:
            params["open_now"] = "true"
        
        response = await asyncio.to_thread(
            self._make_request, "GET", "clinics/search", params=params
        )
        
        clinics = []
        for clinic_data in response["clinics"]:
            clinics.append(ClinicLocation(
                place_id=clinic_data["place_id"],
                name=clinic_data["name"],
                address=clinic_data["address"],
                city=clinic_data.get("city", ""),
                state=clinic_data.get("state", ""),
                country=clinic_data.get("country", ""),
                postal_code=clinic_data.get("postal_code", ""),
                latitude=clinic_data["latitude"],
                longitude=clinic_data["longitude"],
                phone=clinic_data.get("phone", ""),
                website=clinic_data.get("website", ""),
                email=clinic_data.get("email", ""),
                clinic_type=ClinicType(clinic_data.get("clinic_type", "clinic")),
                specialties=[ClinicSpecialty(s) for s in clinic_data.get("specialties", [])],
                availability=ClinicAvailability(clinic_data.get("availability", "open")),
                rating=clinic_data.get("rating", 0.0),
                review_count=clinic_data.get("review_count", 0),
                price_level=clinic_data.get("price_level", 0),
                is_verified=clinic_data.get("is_verified", False),
                is_active=clinic_data.get("is_active", True),
                created_at=datetime.fromisoformat(clinic_data["created_at"]),
                updated_at=datetime.fromisoformat(clinic_data["updated_at"]),
                metadata=clinic_data
            ))
        
        return ClinicSearchResult(
            clinics=clinics,
            total_count=response["total_count"],
            page=page,
            page_size=page_size,
            search_query=query,
            location=location or "",
            radius=radius or 0.0,
            filters=params
        )
    
    async def get_clinic_details(self, place_id: str) -> ClinicLocation:
        """Get detailed clinic information."""
        response = await asyncio.to_thread(
            self._make_request, "GET", f"clinics/{place_id}"
        )
        
        return ClinicLocation(
            place_id=response["place_id"],
            name=response["name"],
            address=response["address"],
            city=response.get("city", ""),
            state=response.get("state", ""),
            country=response.get("country", ""),
            postal_code=response.get("postal_code", ""),
            latitude=response["latitude"],
            longitude=response["longitude"],
            phone=response.get("phone", ""),
            website=response.get("website", ""),
            email=response.get("email", ""),
            clinic_type=ClinicType(response.get("clinic_type", "clinic")),
            specialties=[ClinicSpecialty(s) for s in response.get("specialties", [])],
            availability=ClinicAvailability(response.get("availability", "open")),
            rating=response.get("rating", 0.0),
            review_count=response.get("review_count", 0),
            price_level=response.get("price_level", 0),
            is_verified=response.get("is_verified", False),
            is_active=response.get("is_active", True),
            created_at=datetime.fromisoformat(response["created_at"]),
            updated_at=datetime.fromisoformat(response["updated_at"]),
            metadata=response
        )
    
    async def get_clinic_hours(self, place_id: str) -> List[ClinicHours]:
        """Get clinic operating hours."""
        response = await asyncio.to_thread(
            self._make_request, "GET", f"clinics/{place_id}/hours"
        )
        
        hours = []
        for hour_data in response["hours"]:
            hours.append(ClinicHours(
                clinic_id=place_id,
                day_of_week=hour_data["day_of_week"],
                open_time=hour_data.get("open_time", ""),
                close_time=hour_data.get("close_time", ""),
                is_closed=hour_data.get("is_closed", False),
                is_24_hours=hour_data.get("is_24_hours", False)
            ))
        
        return hours
    
    async def get_clinic_services(self, place_id: str) -> List[ClinicService]:
        """Get clinic services."""
        response = await asyncio.to_thread(
            self._make_request, "GET", f"clinics/{place_id}/services"
        )
        
        services = []
        for service_data in response["services"]:
            services.append(ClinicService(
                service_id=service_data["service_id"],
                clinic_id=place_id,
                name=service_data["name"],
                description=service_data.get("description", ""),
                specialty=ClinicSpecialty(service_data["specialty"]) if service_data.get("specialty") else None,
                is_available=service_data.get("is_available", True),
                price_range=service_data.get("price_range", ""),
                insurance_accepted=[InsuranceType(i) for i in service_data.get("insurance_accepted", [])],
                appointment_required=service_data.get("appointment_required", False),
                wait_time=service_data.get("wait_time"),
                metadata=service_data
            ))
        
        return services
    
    async def get_clinic_reviews(self, place_id: str, limit: int = 20) -> List[ClinicReview]:
        """Get clinic reviews."""
        params = {"limit": limit}
        
        response = await asyncio.to_thread(
            self._make_request, "GET", f"clinics/{place_id}/reviews", params=params
        )
        
        reviews = []
        for review_data in response["reviews"]:
            reviews.append(ClinicReview(
                review_id=review_data["review_id"],
                clinic_id=place_id,
                author_name=review_data["author_name"],
                rating=review_data["rating"],
                text=review_data.get("text", ""),
                time=datetime.fromisoformat(review_data["time"]),
                language=review_data.get("language", "en"),
                is_verified=review_data.get("is_verified", False),
                metadata=review_data
            ))
        
        return reviews
    
    async def get_nearby_clinics(self, latitude: float, longitude: float,
                                radius: float = 5000, clinic_type: Optional[ClinicType] = None,
                                specialty: Optional[ClinicSpecialty] = None,
                                open_now: bool = False, limit: int = 20) -> List[ClinicLocation]:
        """Get nearby clinics."""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "radius": radius,
            "limit": limit
        }
        
        if clinic_type:
            params["clinic_type"] = clinic_type.value
        if specialty:
            params["specialty"] = specialty.value
        if open_now:
            params["open_now"] = "true"
        
        response = await asyncio.to_thread(
            self._make_request, "GET", "clinics/nearby", params=params
        )
        
        clinics = []
        for clinic_data in response["clinics"]:
            clinics.append(ClinicLocation(
                place_id=clinic_data["place_id"],
                name=clinic_data["name"],
                address=clinic_data["address"],
                city=clinic_data.get("city", ""),
                state=clinic_data.get("state", ""),
                country=clinic_data.get("country", ""),
                postal_code=clinic_data.get("postal_code", ""),
                latitude=clinic_data["latitude"],
                longitude=clinic_data["longitude"],
                phone=clinic_data.get("phone", ""),
                website=clinic_data.get("website", ""),
                email=clinic_data.get("email", ""),
                clinic_type=ClinicType(clinic_data.get("clinic_type", "clinic")),
                specialties=[ClinicSpecialty(s) for s in clinic_data.get("specialties", [])],
                availability=ClinicAvailability(clinic_data.get("availability", "open")),
                rating=clinic_data.get("rating", 0.0),
                review_count=clinic_data.get("review_count", 0),
                price_level=clinic_data.get("price_level", 0),
                is_verified=clinic_data.get("is_verified", False),
                is_active=clinic_data.get("is_active", True),
                created_at=datetime.fromisoformat(clinic_data["created_at"]),
                updated_at=datetime.fromisoformat(clinic_data["updated_at"]),
                metadata=clinic_data
            ))
        
        return clinics
    
    async def get_route_to_clinic(self, origin_lat: float, origin_lng: float,
                                 destination_lat: float, destination_lng: float,
                                 travel_mode: str = "driving") -> RouteInfo:
        """Get route information to clinic."""
        params = {
            "origin_lat": origin_lat,
            "origin_lng": origin_lng,
            "destination_lat": destination_lat,
            "destination_lng": destination_lng,
            "travel_mode": travel_mode
        }
        
        response = await asyncio.to_thread(
            self._make_request, "GET", "routes/clinic", params=params
        )
        
        return RouteInfo(
            clinic_id=response["clinic_id"],
            origin_lat=origin_lat,
            origin_lng=origin_lng,
            destination_lat=destination_lat,
            destination_lng=destination_lng,
            distance_km=response["distance_km"],
            duration_minutes=response["duration_minutes"],
            travel_mode=travel_mode,
            route_polyline=response.get("route_polyline", ""),
            traffic_info=response.get("traffic_info", {}),
            metadata=response
        )
    
    async def get_emergency_clinics(self, latitude: float, longitude: float,
                                   radius: float = 10000) -> List[ClinicLocation]:
        """Get emergency clinics nearby."""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "radius": radius,
            "clinic_type": ClinicType.EMERGENCY_CENTER.value
        }
        
        response = await asyncio.to_thread(
            self._make_request, "GET", "clinics/emergency", params=params
        )
        
        clinics = []
        for clinic_data in response["clinics"]:
            clinics.append(ClinicLocation(
                place_id=clinic_data["place_id"],
                name=clinic_data["name"],
                address=clinic_data["address"],
                city=clinic_data.get("city", ""),
                state=clinic_data.get("state", ""),
                country=clinic_data.get("country", ""),
                postal_code=clinic_data.get("postal_code", ""),
                latitude=clinic_data["latitude"],
                longitude=clinic_data["longitude"],
                phone=clinic_data.get("phone", ""),
                website=clinic_data.get("website", ""),
                email=clinic_data.get("email", ""),
                clinic_type=ClinicType.EMERGENCY_CENTER,
                specialties=[ClinicSpecialty(s) for s in clinic_data.get("specialties", [])],
                availability=ClinicAvailability(clinic_data.get("availability", "open")),
                rating=clinic_data.get("rating", 0.0),
                review_count=clinic_data.get("review_count", 0),
                price_level=clinic_data.get("price_level", 0),
                is_verified=clinic_data.get("is_verified", False),
                is_active=clinic_data.get("is_active", True),
                created_at=datetime.fromisoformat(clinic_data["created_at"]),
                updated_at=datetime.fromisoformat(clinic_data["updated_at"]),
                metadata=clinic_data
            ))
        
        return clinics
    
    async def get_clinic_by_specialty(self, latitude: float, longitude: float,
                                     specialty: ClinicSpecialty, radius: float = 10000) -> List[ClinicLocation]:
        """Get clinics by specialty."""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "radius": radius,
            "specialty": specialty.value
        }
        
        response = await asyncio.to_thread(
            self._make_request, "GET", "clinics/specialty", params=params
        )
        
        clinics = []
        for clinic_data in response["clinics"]:
            clinics.append(ClinicLocation(
                place_id=clinic_data["place_id"],
                name=clinic_data["name"],
                address=clinic_data["address"],
                city=clinic_data.get("city", ""),
                state=clinic_data.get("state", ""),
                country=clinic_data.get("country", ""),
                postal_code=clinic_data.get("postal_code", ""),
                latitude=clinic_data["latitude"],
                longitude=clinic_data["longitude"],
                phone=clinic_data.get("phone", ""),
                website=clinic_data.get("website", ""),
                email=clinic_data.get("email", ""),
                clinic_type=ClinicType(clinic_data.get("clinic_type", "clinic")),
                specialties=[ClinicSpecialty(s) for s in clinic_data.get("specialties", [])],
                availability=ClinicAvailability(clinic_data.get("availability", "open")),
                rating=clinic_data.get("rating", 0.0),
                review_count=clinic_data.get("review_count", 0),
                price_level=clinic_data.get("price_level", 0),
                is_verified=clinic_data.get("is_verified", False),
                is_active=clinic_data.get("is_active", True),
                created_at=datetime.fromisoformat(clinic_data["created_at"]),
                updated_at=datetime.fromisoformat(clinic_data["updated_at"]),
                metadata=clinic_data
            ))
        
        return clinics
    
    async def add_clinic_review(self, place_id: str, author_name: str, rating: int,
                               text: str = "", language: str = "en") -> ClinicReview:
        """Add a review to a clinic."""
        data = {
            "author_name": author_name,
            "rating": rating,
            "text": text,
            "language": language
        }
        
        response = await asyncio.to_thread(
            self._make_request, "POST", f"clinics/{place_id}/reviews", data
        )
        
        return ClinicReview(
            review_id=response["review_id"],
            clinic_id=place_id,
            author_name=author_name,
            rating=rating,
            text=text,
            time=datetime.fromisoformat(response["time"]),
            language=language,
            is_verified=response.get("is_verified", False),
            metadata=response
        )
    
    async def get_clinic_photos(self, place_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get clinic photos."""
        params = {"limit": limit}
        
        response = await asyncio.to_thread(
            self._make_request, "GET", f"clinics/{place_id}/photos", params=params
        )
        
        return response["photos"]
    
    async def get_clinic_insights(self, place_id: str) -> Dict[str, Any]:
        """Get clinic insights and analytics."""
        response = await asyncio.to_thread(
            self._make_request, "GET", f"clinics/{place_id}/insights"
        )
        
        return response
    
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
