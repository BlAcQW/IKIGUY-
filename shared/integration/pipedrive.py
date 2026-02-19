"""
Pipedrive CRM Integration Module

This module provides integration with Pipedrive CRM for deal management,
pipeline automation, and sales process optimization.
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
    PIPEDRIVE_AVAILABLE = True
except ImportError:
    PIPEDRIVE_AVAILABLE = False
    logging.warning("Pipedrive APIs not available. Install requests")

logger = logging.getLogger(__name__)


class PipedriveEntityType(Enum):
    """Pipedrive entity types."""
    DEAL = "deal"
    PERSON = "person"
    ORGANIZATION = "organization"
    ACTIVITY = "activity"
    NOTE = "note"
    FILE = "file"


class PipedriveDealStage(Enum):
    """Pipedrive deal stages."""
    QUALIFICATION = "Qualification"
    MEETING_SCHEDULED = "Meeting Scheduled"
    PROPOSAL_SENT = "Proposal Sent"
    NEGOTIATIONS_STARTED = "Negotiations Started"
    CLOSED_WON = "Closed Won"
    CLOSED_LOST = "Closed Lost"


class PipedriveActivityType(Enum):
    """Pipedrive activity types."""
    CALL = "call"
    MEETING = "meeting"
    TASK = "task"
    EMAIL = "email"
    LUNCH = "lunch"


@dataclass
class PipedriveConfig:
    """Configuration for Pipedrive CRM integration."""
    
    api_token: str
    """Pipedrive API token."""
    
    domain: str
    """Pipedrive domain (e.g., 'yourcompany.pipedrive.com')."""
    
    base_url: Optional[str] = None
    """Base URL for API calls."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    verify_ssl: bool = True
    """Verify SSL certificates."""


@dataclass
class PipedriveDeal:
    """Pipedrive deal data structure."""
    
    id: int
    """Deal ID."""
    
    title: str
    """Deal title."""
    
    value: float
    """Deal value."""
    
    currency: str
    """Currency."""
    
    stage_id: int
    """Stage ID."""
    
    stage_name: str
    """Stage name."""
    
    person_id: Optional[int] = None
    """Person ID."""
    
    organization_id: Optional[int] = None
    """Organization ID."""
    
    close_date: Optional[datetime] = None
    """Close date."""
    
    probability: Optional[int] = None
    """Probability percentage."""
    
    status: str
    """Deal status."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class PipedrivePerson:
    """Pipedrive person data structure."""
    
    id: int
    """Person ID."""
    
    name: str
    """Person name."""
    
    email: Optional[str] = None
    """Email address."""
    
    phone: Optional[str] = None
    """Phone number."""
    
    organization_id: Optional[int] = None
    """Organization ID."""
    
    title: Optional[str] = None
    """Job title."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class PipedriveOrganization:
    """Pipedrive organization data structure."""
    
    id: int
    """Organization ID."""
    
    name: str
    """Organization name."""
    
    address: Optional[str] = None
    """Address."""
    
    city: Optional[str] = None
    """City."""
    
    country: Optional[str] = None
    """Country."""
    
    industry: Optional[str] = None
    """Industry."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class PipedriveActivity:
    """Pipedrive activity data structure."""
    
    id: int
    """Activity ID."""
    
    subject: str
    """Activity subject."""
    
    type: PipedriveActivityType
    """Activity type."""
    
    due_date: Optional[datetime] = None
    """Due date."""
    
    duration: Optional[str] = None
    """Duration."""
    
    note: Optional[str] = None
    """Note."""
    
    deal_id: Optional[int] = None
    """Deal ID."""
    
    person_id: Optional[int] = None
    """Person ID."""
    
    organization_id: Optional[int] = None
    """Organization ID."""
    
    done: bool
    """Whether activity is done."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class PipedriveStage:
    """Pipedrive stage data structure."""
    
    id: int
    """Stage ID."""
    
    name: str
    """Stage name."""
    
    pipeline_id: int
    """Pipeline ID."""
    
    order_nr: int
    """Order number."""
    
    probability: int
    """Probability percentage."""
    
    active: bool
    """Whether stage is active."""
    
    deal_probability: int
    """Deal probability percentage."""


class PipedriveIntegration:
    """Pipedrive CRM integration for deal management and pipeline automation."""
    
    def __init__(self, config: PipedriveConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.base_url = config.base_url or f"https://{config.domain}/api/v1"
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.verify_ssl
        self.session.headers.update({
            "Content-Type": "application/json"
        })
    
    def _get_auth_params(self) -> Dict[str, str]:
        """Get authentication parameters."""
        return {"api_token": self.config.api_token}
    
    async def create_deal(
        self,
        title: str,
        value: float,
        currency: str = "USD",
        stage_id: Optional[int] = None,
        person_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        close_date: Optional[datetime] = None,
        probability: Optional[int] = None
    ) -> PipedriveDeal:
        """
        Create a deal.
        
        Args:
            title: Deal title
            value: Deal value
            currency: Currency
            stage_id: Stage ID
            person_id: Person ID
            organization_id: Organization ID
            close_date: Close date
            probability: Probability percentage
            
        Returns:
            Deal data
        """
        try:
            url = f"{self.base_url}/deals"
            
            data = {
                "title": title,
                "value": value,
                "currency": currency
            }
            
            if stage_id:
                data["stage_id"] = stage_id
            if person_id:
                data["person_id"] = person_id
            if organization_id:
                data["organization_id"] = organization_id
            if close_date:
                data["close_date"] = close_date.strftime("%Y-%m-%d")
            if probability:
                data["probability"] = probability
            
            params = self._get_auth_params()
            response = self.session.post(url, json=data, params=params)
            response.raise_for_status()
            
            deal_data = response.json()["data"]
            
            return PipedriveDeal(
                id=deal_data["id"],
                title=deal_data["title"],
                value=deal_data["value"],
                currency=deal_data["currency"],
                stage_id=deal_data["stage_id"],
                stage_name=deal_data.get("stage_name", ""),
                person_id=deal_data.get("person_id"),
                organization_id=deal_data.get("organization_id"),
                close_date=datetime.strptime(deal_data["close_date"], "%Y-%m-%d") if deal_data.get("close_date") else None,
                probability=deal_data.get("probability"),
                status=deal_data["status"],
                created_at=datetime.fromisoformat(deal_data["add_time"].replace("Z", "+00:00")) if deal_data.get("add_time") else None,
                updated_at=datetime.fromisoformat(deal_data["update_time"].replace("Z", "+00:00")) if deal_data.get("update_time") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create deal: {e}")
            raise
    
    async def get_deal(self, deal_id: int) -> PipedriveDeal:
        """
        Get deal details.
        
        Args:
            deal_id: Deal ID
            
        Returns:
            Deal data
        """
        try:
            url = f"{self.base_url}/deals/{deal_id}"
            params = self._get_auth_params()
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            deal_data = response.json()["data"]
            
            return PipedriveDeal(
                id=deal_data["id"],
                title=deal_data["title"],
                value=deal_data["value"],
                currency=deal_data["currency"],
                stage_id=deal_data["stage_id"],
                stage_name=deal_data.get("stage_name", ""),
                person_id=deal_data.get("person_id"),
                organization_id=deal_data.get("organization_id"),
                close_date=datetime.strptime(deal_data["close_date"], "%Y-%m-%d") if deal_data.get("close_date") else None,
                probability=deal_data.get("probability"),
                status=deal_data["status"],
                created_at=datetime.fromisoformat(deal_data["add_time"].replace("Z", "+00:00")) if deal_data.get("add_time") else None,
                updated_at=datetime.fromisoformat(deal_data["update_time"].replace("Z", "+00:00")) if deal_data.get("update_time") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get deal: {e}")
            raise
    
    async def get_deals(self, limit: int = 100) -> List[PipedriveDeal]:
        """
        Get all deals.
        
        Args:
            limit: Number of deals to return
            
        Returns:
            List of deals
        """
        try:
            url = f"{self.base_url}/deals"
            params = self._get_auth_params()
            params["limit"] = limit
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            result = response.json()
            deals = []
            
            for deal_data in result.get("data", []):
                deal = PipedriveDeal(
                    id=deal_data["id"],
                    title=deal_data["title"],
                    value=deal_data["value"],
                    currency=deal_data["currency"],
                    stage_id=deal_data["stage_id"],
                    stage_name=deal_data.get("stage_name", ""),
                    person_id=deal_data.get("person_id"),
                    organization_id=deal_data.get("organization_id"),
                    close_date=datetime.strptime(deal_data["close_date"], "%Y-%m-%d") if deal_data.get("close_date") else None,
                    probability=deal_data.get("probability"),
                    status=deal_data["status"],
                    created_at=datetime.fromisoformat(deal_data["add_time"].replace("Z", "+00:00")) if deal_data.get("add_time") else None,
                    updated_at=datetime.fromisoformat(deal_data["update_time"].replace("Z", "+00:00")) if deal_data.get("update_time") else None
                )
                deals.append(deal)
            
            return deals
            
        except Exception as e:
            self.logger.error(f"Failed to get deals: {e}")
            raise
    
    async def update_deal(
        self,
        deal_id: int,
        title: Optional[str] = None,
        value: Optional[float] = None,
        currency: Optional[str] = None,
        stage_id: Optional[int] = None,
        person_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        close_date: Optional[datetime] = None,
        probability: Optional[int] = None
    ) -> PipedriveDeal:
        """
        Update a deal.
        
        Args:
            deal_id: Deal ID
            title: Deal title
            value: Deal value
            currency: Currency
            stage_id: Stage ID
            person_id: Person ID
            organization_id: Organization ID
            close_date: Close date
            probability: Probability percentage
            
        Returns:
            Updated deal data
        """
        try:
            url = f"{self.base_url}/deals/{deal_id}"
            
            data = {}
            
            if title:
                data["title"] = title
            if value:
                data["value"] = value
            if currency:
                data["currency"] = currency
            if stage_id:
                data["stage_id"] = stage_id
            if person_id:
                data["person_id"] = person_id
            if organization_id:
                data["organization_id"] = organization_id
            if close_date:
                data["close_date"] = close_date.strftime("%Y-%m-%d")
            if probability:
                data["probability"] = probability
            
            params = self._get_auth_params()
            response = self.session.put(url, json=data, params=params)
            response.raise_for_status()
            
            deal_data = response.json()["data"]
            
            return PipedriveDeal(
                id=deal_data["id"],
                title=deal_data["title"],
                value=deal_data["value"],
                currency=deal_data["currency"],
                stage_id=deal_data["stage_id"],
                stage_name=deal_data.get("stage_name", ""),
                person_id=deal_data.get("person_id"),
                organization_id=deal_data.get("organization_id"),
                close_date=datetime.strptime(deal_data["close_date"], "%Y-%m-%d") if deal_data.get("close_date") else None,
                probability=deal_data.get("probability"),
                status=deal_data["status"],
                created_at=datetime.fromisoformat(deal_data["add_time"].replace("Z", "+00:00")) if deal_data.get("add_time") else None,
                updated_at=datetime.fromisoformat(deal_data["update_time"].replace("Z", "+00:00")) if deal_data.get("update_time") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update deal: {e}")
            raise
    
    async def create_person(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        organization_id: Optional[int] = None,
        title: Optional[str] = None
    ) -> PipedrivePerson:
        """
        Create a person.
        
        Args:
            name: Person name
            email: Email address
            phone: Phone number
            organization_id: Organization ID
            title: Job title
            
        Returns:
            Person data
        """
        try:
            url = f"{self.base_url}/persons"
            
            data = {"name": name}
            
            if email:
                data["email"] = [{"value": email, "primary": True, "label": "work"}]
            if phone:
                data["phone"] = [{"value": phone, "primary": True, "label": "work"}]
            if organization_id:
                data["org_id"] = organization_id
            if title:
                data["title"] = title
            
            params = self._get_auth_params()
            response = self.session.post(url, json=data, params=params)
            response.raise_for_status()
            
            person_data = response.json()["data"]
            
            return PipedrivePerson(
                id=person_data["id"],
                name=person_data["name"],
                email=person_data.get("email", [{}])[0].get("value") if person_data.get("email") else None,
                phone=person_data.get("phone", [{}])[0].get("value") if person_data.get("phone") else None,
                organization_id=person_data.get("org_id"),
                title=person_data.get("title"),
                created_at=datetime.fromisoformat(person_data["add_time"].replace("Z", "+00:00")) if person_data.get("add_time") else None,
                updated_at=datetime.fromisoformat(person_data["update_time"].replace("Z", "+00:00")) if person_data.get("update_time") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create person: {e}")
            raise
    
    async def create_organization(
        self,
        name: str,
        address: Optional[str] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
        industry: Optional[str] = None
    ) -> PipedriveOrganization:
        """
        Create an organization.
        
        Args:
            name: Organization name
            address: Address
            city: City
            country: Country
            industry: Industry
            
        Returns:
            Organization data
        """
        try:
            url = f"{self.base_url}/organizations"
            
            data = {"name": name}
            
            if address:
                data["address"] = address
            if city:
                data["city"] = city
            if country:
                data["country"] = country
            if industry:
                data["industry"] = industry
            
            params = self._get_auth_params()
            response = self.session.post(url, json=data, params=params)
            response.raise_for_status()
            
            org_data = response.json()["data"]
            
            return PipedriveOrganization(
                id=org_data["id"],
                name=org_data["name"],
                address=org_data.get("address"),
                city=org_data.get("city"),
                country=org_data.get("country"),
                industry=org_data.get("industry"),
                created_at=datetime.fromisoformat(org_data["add_time"].replace("Z", "+00:00")) if org_data.get("add_time") else None,
                updated_at=datetime.fromisoformat(org_data["update_time"].replace("Z", "+00:00")) if org_data.get("update_time") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create organization: {e}")
            raise
    
    async def create_activity(
        self,
        subject: str,
        type: PipedriveActivityType,
        due_date: Optional[datetime] = None,
        duration: Optional[str] = None,
        note: Optional[str] = None,
        deal_id: Optional[int] = None,
        person_id: Optional[int] = None,
        organization_id: Optional[int] = None
    ) -> PipedriveActivity:
        """
        Create an activity.
        
        Args:
            subject: Activity subject
            type: Activity type
            due_date: Due date
            duration: Duration
            note: Note
            deal_id: Deal ID
            person_id: Person ID
            organization_id: Organization ID
            
        Returns:
            Activity data
        """
        try:
            url = f"{self.base_url}/activities"
            
            data = {
                "subject": subject,
                "type": type.value
            }
            
            if due_date:
                data["due_date"] = due_date.strftime("%Y-%m-%d")
            if duration:
                data["duration"] = duration
            if note:
                data["note"] = note
            if deal_id:
                data["deal_id"] = deal_id
            if person_id:
                data["person_id"] = person_id
            if organization_id:
                data["org_id"] = organization_id
            
            params = self._get_auth_params()
            response = self.session.post(url, json=data, params=params)
            response.raise_for_status()
            
            activity_data = response.json()["data"]
            
            return PipedriveActivity(
                id=activity_data["id"],
                subject=activity_data["subject"],
                type=PipedriveActivityType(activity_data["type"]),
                due_date=datetime.strptime(activity_data["due_date"], "%Y-%m-%d") if activity_data.get("due_date") else None,
                duration=activity_data.get("duration"),
                note=activity_data.get("note"),
                deal_id=activity_data.get("deal_id"),
                person_id=activity_data.get("person_id"),
                organization_id=activity_data.get("org_id"),
                done=activity_data.get("done", False),
                created_at=datetime.fromisoformat(activity_data["add_time"].replace("Z", "+00:00")) if activity_data.get("add_time") else None,
                updated_at=datetime.fromisoformat(activity_data["update_time"].replace("Z", "+00:00")) if activity_data.get("update_time") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create activity: {e}")
            raise
    
    async def get_stages(self) -> List[PipedriveStage]:
        """
        Get all stages.
        
        Returns:
            List of stages
        """
        try:
            url = f"{self.base_url}/stages"
            params = self._get_auth_params()
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            result = response.json()
            stages = []
            
            for stage_data in result.get("data", []):
                stage = PipedriveStage(
                    id=stage_data["id"],
                    name=stage_data["name"],
                    pipeline_id=stage_data["pipeline_id"],
                    order_nr=stage_data["order_nr"],
                    probability=stage_data["probability"],
                    active=stage_data.get("active", True),
                    deal_probability=stage_data["deal_probability"]
                )
                stages.append(stage)
            
            return stages
            
        except Exception as e:
            self.logger.error(f"Failed to get stages: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Pipedrive CRM integration.
        
        Returns:
            Health check results
        """
        try:
            # Test API connectivity by getting deals
            deals = await self.get_deals(limit=1)
            
            return {
                "status": "healthy",
                "base_url": self.base_url,
                "deals_count": len(deals),
                "api_connectivity": "successful",
                "last_checked": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }

