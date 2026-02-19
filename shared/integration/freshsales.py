"""
Freshsales CRM Integration Module

This module provides integration with Freshsales CRM for lead management,
contact management, and sales automation.
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
    FRESHSALES_AVAILABLE = True
except ImportError:
    FRESHSALES_AVAILABLE = False
    logging.warning("Freshsales APIs not available. Install requests")

logger = logging.getLogger(__name__)


class FreshsalesModuleType(Enum):
    """Freshsales module types."""
    LEADS = "leads"
    CONTACTS = "contacts"
    ACCOUNTS = "accounts"
    DEALS = "deals"
    TASKS = "tasks"
    EVENTS = "events"
    CASES = "cases"


class FreshsalesLeadStatus(Enum):
    """Freshsales lead status."""
    NEW = "New"
    CONTACTED = "Contacted"
    QUALIFIED = "Qualified"
    UNQUALIFIED = "Unqualified"
    CONVERTED = "Converted"
    LOST = "Lost"


class FreshsalesDealStage(Enum):
    """Freshsales deal stages."""
    QUALIFICATION = "Qualification"
    NEED_ANALYSIS = "Need Analysis"
    PROPOSAL = "Proposal"
    NEGOTIATION = "Negotiation"
    CLOSED_WON = "Closed Won"
    CLOSED_LOST = "Closed Lost"


@dataclass
class FreshsalesConfig:
    """Configuration for Freshsales CRM integration."""
    
    domain: str
    """Freshsales domain (e.g., 'yourcompany.freshsales.com')."""
    
    api_key: str
    """Freshsales API key."""
    
    base_url: Optional[str] = None
    """Base URL for API calls."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    verify_ssl: bool = True
    """Verify SSL certificates."""


@dataclass
class FreshsalesLead:
    """Freshsales lead data structure."""
    
    id: int
    """Lead ID."""
    
    first_name: str
    """First name."""
    
    last_name: str
    """Last name."""
    
    status: FreshsalesLeadStatus
    """Lead status."""
    
    email: Optional[str] = None
    """Email address."""
    
    phone: Optional[str] = None
    """Phone number."""
    
    company: Optional[str] = None
    """Company name."""
    
    source: Optional[str] = None
    """Lead source."""
    
    description: Optional[str] = None
    """Lead description."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class FreshsalesContact:
    """Freshsales contact data structure."""
    
    id: int
    """Contact ID."""
    
    first_name: str
    """First name."""
    
    last_name: str
    """Last name."""
    
    email: Optional[str] = None
    """Email address."""
    
    phone: Optional[str] = None
    """Phone number."""
    
    account_id: Optional[int] = None
    """Account ID."""
    
    title: Optional[str] = None
    """Job title."""
    
    department: Optional[str] = None
    """Department."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class FreshsalesDeal:
    """Freshsales deal data structure."""
    
    id: int
    """Deal ID."""
    
    name: str
    """Deal name."""
    
    amount: float
    """Deal amount."""
    
    stage: FreshsalesDealStage
    """Deal stage."""
    
    account_id: Optional[int] = None
    """Account ID."""
    
    contact_id: Optional[int] = None
    """Contact ID."""
    
    closing_date: Optional[datetime] = None
    """Closing date."""
    
    probability: Optional[int] = None
    """Probability percentage."""
    
    description: Optional[str] = None
    """Deal description."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class FreshsalesTask:
    """Freshsales task data structure."""
    
    id: int
    """Task ID."""
    
    title: str
    """Task title."""
    
    status: str
    """Task status."""
    
    priority: str
    """Task priority."""
    
    description: Optional[str] = None
    """Task description."""
    
    due_date: Optional[datetime] = None
    """Due date."""
    
    related_to_id: Optional[int] = None
    """Related record ID."""
    
    related_to_type: Optional[str] = None
    """Related record type."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


class FreshsalesIntegration:
    """Freshsales CRM integration for lead management and sales automation."""
    
    def __init__(self, config: FreshsalesConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.base_url = config.base_url or f"https://{config.domain}/api"
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.verify_ssl
        self.session.headers.update({
            "Authorization": f"Token token={config.api_key}",
            "Content-Type": "application/json"
        })
    
    async def create_lead(
        self,
        first_name: str,
        last_name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        status: FreshsalesLeadStatus = FreshsalesLeadStatus.NEW,
        source: Optional[str] = None,
        description: Optional[str] = None
    ) -> FreshsalesLead:
        """
        Create a lead.
        
        Args:
            first_name: First name
            last_name: Last name
            email: Email address
            phone: Phone number
            company: Company name
            status: Lead status
            source: Lead source
            description: Lead description
            
        Returns:
            Lead data
        """
        try:
            url = f"{self.base_url}/leads"
            
            data = {
                "lead": {
                    "first_name": first_name,
                    "last_name": last_name,
                    "status": status.value
                }
            }
            
            if email:
                data["lead"]["email"] = email
            if phone:
                data["lead"]["phone"] = phone
            if company:
                data["lead"]["company"] = company
            if source:
                data["lead"]["source"] = source
            if description:
                data["lead"]["description"] = description
            
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            lead_data = response.json()["lead"]
            
            return FreshsalesLead(
                id=lead_data["id"],
                first_name=lead_data["first_name"],
                last_name=lead_data["last_name"],
                email=lead_data.get("email"),
                phone=lead_data.get("phone"),
                company=lead_data.get("company"),
                status=FreshsalesLeadStatus(lead_data["status"]),
                source=lead_data.get("source"),
                description=lead_data.get("description"),
                created_at=datetime.fromisoformat(lead_data["created_at"].replace("Z", "+00:00")) if lead_data.get("created_at") else None,
                updated_at=datetime.fromisoformat(lead_data["updated_at"].replace("Z", "+00:00")) if lead_data.get("updated_at") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create lead: {e}")
            raise
    
    async def get_lead(self, lead_id: int) -> FreshsalesLead:
        """
        Get lead details.
        
        Args:
            lead_id: Lead ID
            
        Returns:
            Lead data
        """
        try:
            url = f"{self.base_url}/leads/{lead_id}"
            response = self.session.get(url)
            response.raise_for_status()
            
            lead_data = response.json()["lead"]
            
            return FreshsalesLead(
                id=lead_data["id"],
                first_name=lead_data["first_name"],
                last_name=lead_data["last_name"],
                email=lead_data.get("email"),
                phone=lead_data.get("phone"),
                company=lead_data.get("company"),
                status=FreshsalesLeadStatus(lead_data["status"]),
                source=lead_data.get("source"),
                description=lead_data.get("description"),
                created_at=datetime.fromisoformat(lead_data["created_at"].replace("Z", "+00:00")) if lead_data.get("created_at") else None,
                updated_at=datetime.fromisoformat(lead_data["updated_at"].replace("Z", "+00:00")) if lead_data.get("updated_at") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get lead: {e}")
            raise
    
    async def get_leads(self, limit: int = 100) -> List[FreshsalesLead]:
        """
        Get all leads.
        
        Args:
            limit: Number of leads to return
            
        Returns:
            List of leads
        """
        try:
            url = f"{self.base_url}/leads"
            params = {"per_page": limit}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            result = response.json()
            leads = []
            
            for lead_data in result.get("leads", []):
                lead = FreshsalesLead(
                    id=lead_data["id"],
                    first_name=lead_data["first_name"],
                    last_name=lead_data["last_name"],
                    email=lead_data.get("email"),
                    phone=lead_data.get("phone"),
                    company=lead_data.get("company"),
                    status=FreshsalesLeadStatus(lead_data["status"]),
                    source=lead_data.get("source"),
                    description=lead_data.get("description"),
                    created_at=datetime.fromisoformat(lead_data["created_at"].replace("Z", "+00:00")) if lead_data.get("created_at") else None,
                    updated_at=datetime.fromisoformat(lead_data["updated_at"].replace("Z", "+00:00")) if lead_data.get("updated_at") else None
                )
                leads.append(lead)
            
            return leads
            
        except Exception as e:
            self.logger.error(f"Failed to get leads: {e}")
            raise
    
    async def update_lead(
        self,
        lead_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        status: Optional[FreshsalesLeadStatus] = None,
        source: Optional[str] = None,
        description: Optional[str] = None
    ) -> FreshsalesLead:
        """
        Update a lead.
        
        Args:
            lead_id: Lead ID
            first_name: First name
            last_name: Last name
            email: Email address
            phone: Phone number
            company: Company name
            status: Lead status
            source: Lead source
            description: Lead description
            
        Returns:
            Updated lead data
        """
        try:
            url = f"{self.base_url}/leads/{lead_id}"
            
            data = {"lead": {}}
            
            if first_name:
                data["lead"]["first_name"] = first_name
            if last_name:
                data["lead"]["last_name"] = last_name
            if email:
                data["lead"]["email"] = email
            if phone:
                data["lead"]["phone"] = phone
            if company:
                data["lead"]["company"] = company
            if status:
                data["lead"]["status"] = status.value
            if source:
                data["lead"]["source"] = source
            if description:
                data["lead"]["description"] = description
            
            response = self.session.put(url, json=data)
            response.raise_for_status()
            
            lead_data = response.json()["lead"]
            
            return FreshsalesLead(
                id=lead_data["id"],
                first_name=lead_data["first_name"],
                last_name=lead_data["last_name"],
                email=lead_data.get("email"),
                phone=lead_data.get("phone"),
                company=lead_data.get("company"),
                status=FreshsalesLeadStatus(lead_data["status"]),
                source=lead_data.get("source"),
                description=lead_data.get("description"),
                created_at=datetime.fromisoformat(lead_data["created_at"].replace("Z", "+00:00")) if lead_data.get("created_at") else None,
                updated_at=datetime.fromisoformat(lead_data["updated_at"].replace("Z", "+00:00")) if lead_data.get("updated_at") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update lead: {e}")
            raise
    
    async def create_contact(
        self,
        first_name: str,
        last_name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        account_id: Optional[int] = None,
        title: Optional[str] = None,
        department: Optional[str] = None
    ) -> FreshsalesContact:
        """
        Create a contact.
        
        Args:
            first_name: First name
            last_name: Last name
            email: Email address
            phone: Phone number
            account_id: Account ID
            title: Job title
            department: Department
            
        Returns:
            Contact data
        """
        try:
            url = f"{self.base_url}/contacts"
            
            data = {
                "contact": {
                    "first_name": first_name,
                    "last_name": last_name
                }
            }
            
            if email:
                data["contact"]["email"] = email
            if phone:
                data["contact"]["phone"] = phone
            if account_id:
                data["contact"]["account_id"] = account_id
            if title:
                data["contact"]["title"] = title
            if department:
                data["contact"]["department"] = department
            
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            contact_data = response.json()["contact"]
            
            return FreshsalesContact(
                id=contact_data["id"],
                first_name=contact_data["first_name"],
                last_name=contact_data["last_name"],
                email=contact_data.get("email"),
                phone=contact_data.get("phone"),
                account_id=contact_data.get("account_id"),
                title=contact_data.get("title"),
                department=contact_data.get("department"),
                created_at=datetime.fromisoformat(contact_data["created_at"].replace("Z", "+00:00")) if contact_data.get("created_at") else None,
                updated_at=datetime.fromisoformat(contact_data["updated_at"].replace("Z", "+00:00")) if contact_data.get("updated_at") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create contact: {e}")
            raise
    
    async def create_deal(
        self,
        name: str,
        amount: float,
        stage: FreshsalesDealStage,
        account_id: Optional[int] = None,
        contact_id: Optional[int] = None,
        closing_date: Optional[datetime] = None,
        probability: Optional[int] = None,
        description: Optional[str] = None
    ) -> FreshsalesDeal:
        """
        Create a deal.
        
        Args:
            name: Deal name
            amount: Deal amount
            stage: Deal stage
            account_id: Account ID
            contact_id: Contact ID
            closing_date: Closing date
            probability: Probability percentage
            description: Deal description
            
        Returns:
            Deal data
        """
        try:
            url = f"{self.base_url}/deals"
            
            data = {
                "deal": {
                    "name": name,
                    "amount": amount,
                    "stage": stage.value
                }
            }
            
            if account_id:
                data["deal"]["account_id"] = account_id
            if contact_id:
                data["deal"]["contact_id"] = contact_id
            if closing_date:
                data["deal"]["closing_date"] = closing_date.strftime("%Y-%m-%d")
            if probability:
                data["deal"]["probability"] = probability
            if description:
                data["deal"]["description"] = description
            
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            deal_data = response.json()["deal"]
            
            return FreshsalesDeal(
                id=deal_data["id"],
                name=deal_data["name"],
                amount=deal_data["amount"],
                stage=FreshsalesDealStage(deal_data["stage"]),
                account_id=deal_data.get("account_id"),
                contact_id=deal_data.get("contact_id"),
                closing_date=datetime.strptime(deal_data["closing_date"], "%Y-%m-%d") if deal_data.get("closing_date") else None,
                probability=deal_data.get("probability"),
                description=deal_data.get("description"),
                created_at=datetime.fromisoformat(deal_data["created_at"].replace("Z", "+00:00")) if deal_data.get("created_at") else None,
                updated_at=datetime.fromisoformat(deal_data["updated_at"].replace("Z", "+00:00")) if deal_data.get("updated_at") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create deal: {e}")
            raise
    
    async def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        due_date: Optional[datetime] = None,
        status: str = "Open",
        priority: str = "Medium",
        related_to_id: Optional[int] = None,
        related_to_type: Optional[str] = None
    ) -> FreshsalesTask:
        """
        Create a task.
        
        Args:
            title: Task title
            description: Task description
            due_date: Due date
            status: Task status
            priority: Task priority
            related_to_id: Related record ID
            related_to_type: Related record type
            
        Returns:
            Task data
        """
        try:
            url = f"{self.base_url}/tasks"
            
            data = {
                "task": {
                    "title": title,
                    "status": status,
                    "priority": priority
                }
            }
            
            if description:
                data["task"]["description"] = description
            if due_date:
                data["task"]["due_date"] = due_date.strftime("%Y-%m-%d")
            if related_to_id and related_to_type:
                data["task"]["related_to_id"] = related_to_id
                data["task"]["related_to_type"] = related_to_type
            
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            task_data = response.json()["task"]
            
            return FreshsalesTask(
                id=task_data["id"],
                title=task_data["title"],
                description=task_data.get("description"),
                due_date=datetime.strptime(task_data["due_date"], "%Y-%m-%d") if task_data.get("due_date") else None,
                status=task_data["status"],
                priority=task_data["priority"],
                related_to_id=task_data.get("related_to_id"),
                related_to_type=task_data.get("related_to_type"),
                created_at=datetime.fromisoformat(task_data["created_at"].replace("Z", "+00:00")) if task_data.get("created_at") else None,
                updated_at=datetime.fromisoformat(task_data["updated_at"].replace("Z", "+00:00")) if task_data.get("updated_at") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create task: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Freshsales CRM integration.
        
        Returns:
            Health check results
        """
        try:
            # Test API connectivity by getting leads
            leads = await self.get_leads(limit=1)
            
            return {
                "status": "healthy",
                "base_url": self.base_url,
                "leads_count": len(leads),
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

