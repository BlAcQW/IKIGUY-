"""
Zoho CRM Integration Module

This module provides integration with Zoho CRM for customer relationship management,
lead management, and sales automation.
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
    ZOHO_AVAILABLE = True
except ImportError:
    ZOHO_AVAILABLE = False
    logging.warning("Zoho APIs not available. Install requests")

logger = logging.getLogger(__name__)


class ZohoModuleType(Enum):
    """Zoho module types."""
    LEADS = "Leads"
    CONTACTS = "Contacts"
    ACCOUNTS = "Accounts"
    DEALS = "Deals"
    TASKS = "Tasks"
    EVENTS = "Events"
    POTENTIALS = "Potentials"
    CASES = "Cases"


class ZohoLeadStatus(Enum):
    """Zoho lead status."""
    NEW = "New"
    CONTACTED = "Contacted"
    QUALIFIED = "Qualified"
    UNQUALIFIED = "Unqualified"
    CONVERTED = "Converted"
    LOST = "Lost"


class ZohoDealStage(Enum):
    """Zoho deal stages."""
    QUALIFICATION = "Qualification"
    NEED_ANALYSIS = "Need Analysis"
    PROPOSAL = "Proposal"
    NEGOTIATION = "Negotiation"
    CLOSED_WON = "Closed Won"
    CLOSED_LOST = "Closed Lost"


@dataclass
class ZohoConfig:
    """Configuration for Zoho CRM integration."""
    
    client_id: str
    """Zoho client ID."""
    
    client_secret: str
    """Zoho client secret."""
    
    refresh_token: str
    """Zoho refresh token."""
    
    base_url: str = "https://www.zohoapis.com/crm/v3"
    """Zoho CRM API base URL."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    verify_ssl: bool = True
    """Verify SSL certificates."""


@dataclass
class ZohoLead:
    """Zoho lead data structure."""
    
    id: str
    """Lead ID."""
    
    first_name: str
    """First name."""
    
    last_name: str
    """Last name."""
    
    status: ZohoLeadStatus
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
class ZohoContact:
    """Zoho contact data structure."""
    
    id: str
    """Contact ID."""
    
    first_name: str
    """First name."""
    
    last_name: str
    """Last name."""
    
    email: Optional[str] = None
    """Email address."""
    
    phone: Optional[str] = None
    """Phone number."""
    
    account_id: Optional[str] = None
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
class ZohoDeal:
    """Zoho deal data structure."""
    
    id: str
    """Deal ID."""
    
    deal_name: str
    """Deal name."""
    
    amount: float
    """Deal amount."""
    
    stage: ZohoDealStage
    """Deal stage."""
    
    account_id: Optional[str] = None
    """Account ID."""
    
    contact_id: Optional[str] = None
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
class ZohoTask:
    """Zoho task data structure."""
    
    id: str
    """Task ID."""
    
    subject: str
    """Task subject."""
    
    status: str
    """Task status."""
    
    priority: str
    """Task priority."""
    
    description: Optional[str] = None
    """Task description."""
    
    due_date: Optional[datetime] = None
    """Due date."""
    
    related_to_id: Optional[str] = None
    """Related record ID."""
    
    related_to_type: Optional[str] = None
    """Related record type."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


class ZohoIntegration:
    """Zoho CRM integration for customer relationship management."""
    
    def __init__(self, config: ZohoConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.access_token = None
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.verify_ssl
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        return {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Zoho CRM.
        
        Returns:
            True if successful
        """
        try:
            url = "https://accounts.zoho.com/oauth/v2/token"
            
            data = {
                "refresh_token": self.config.refresh_token,
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "grant_type": "refresh_token"
            }
            
            response = self.session.post(url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            
            self.logger.info("Successfully authenticated with Zoho CRM")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to authenticate with Zoho CRM: {e}")
            return False
    
    async def create_lead(
        self,
        first_name: str,
        last_name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        status: ZohoLeadStatus = ZohoLeadStatus.NEW,
        source: Optional[str] = None,
        description: Optional[str] = None
    ) -> ZohoLead:
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
            url = f"{self.config.base_url}/Leads"
            
            data = {
                "data": [{
                    "First_Name": first_name,
                    "Last_Name": last_name,
                    "Status": status.value
                }]
            }
            
            if email:
                data["data"][0]["Email"] = email
            if phone:
                data["data"][0]["Phone"] = phone
            if company:
                data["data"][0]["Company"] = company
            if source:
                data["data"][0]["Lead_Source"] = source
            if description:
                data["data"][0]["Description"] = description
            
            response = self.session.post(url, json=data, headers=self._get_headers())
            response.raise_for_status()
            
            result = response.json()
            lead_data = result["data"][0]["details"]
            
            return ZohoLead(
                id=lead_data["id"],
                first_name=lead_data["First_Name"],
                last_name=lead_data["Last_Name"],
                email=lead_data.get("Email"),
                phone=lead_data.get("Phone"),
                company=lead_data.get("Company"),
                status=ZohoLeadStatus(lead_data["Status"]),
                source=lead_data.get("Lead_Source"),
                description=lead_data.get("Description"),
                created_at=datetime.fromisoformat(lead_data["Created_Time"].replace("Z", "+00:00")) if lead_data.get("Created_Time") else None,
                updated_at=datetime.fromisoformat(lead_data["Modified_Time"].replace("Z", "+00:00")) if lead_data.get("Modified_Time") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create lead: {e}")
            raise
    
    async def get_lead(self, lead_id: str) -> ZohoLead:
        """
        Get lead details.
        
        Args:
            lead_id: Lead ID
            
        Returns:
            Lead data
        """
        try:
            url = f"{self.config.base_url}/Leads/{lead_id}"
            response = self.session.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            lead_data = response.json()["data"][0]
            
            return ZohoLead(
                id=lead_data["id"],
                first_name=lead_data["First_Name"],
                last_name=lead_data["Last_Name"],
                email=lead_data.get("Email"),
                phone=lead_data.get("Phone"),
                company=lead_data.get("Company"),
                status=ZohoLeadStatus(lead_data["Status"]),
                source=lead_data.get("Lead_Source"),
                description=lead_data.get("Description"),
                created_at=datetime.fromisoformat(lead_data["Created_Time"].replace("Z", "+00:00")) if lead_data.get("Created_Time") else None,
                updated_at=datetime.fromisoformat(lead_data["Modified_Time"].replace("Z", "+00:00")) if lead_data.get("Modified_Time") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get lead: {e}")
            raise
    
    async def get_leads(self, limit: int = 100) -> List[ZohoLead]:
        """
        Get all leads.
        
        Args:
            limit: Number of leads to return
            
        Returns:
            List of leads
        """
        try:
            url = f"{self.config.base_url}/Leads"
            params = {"per_page": limit}
            
            response = self.session.get(url, params=params, headers=self._get_headers())
            response.raise_for_status()
            
            result = response.json()
            leads = []
            
            for lead_data in result["data"]:
                lead = ZohoLead(
                    id=lead_data["id"],
                    first_name=lead_data["First_Name"],
                    last_name=lead_data["Last_Name"],
                    email=lead_data.get("Email"),
                    phone=lead_data.get("Phone"),
                    company=lead_data.get("Company"),
                    status=ZohoLeadStatus(lead_data["Status"]),
                    source=lead_data.get("Lead_Source"),
                    description=lead_data.get("Description"),
                    created_at=datetime.fromisoformat(lead_data["Created_Time"].replace("Z", "+00:00")) if lead_data.get("Created_Time") else None,
                    updated_at=datetime.fromisoformat(lead_data["Modified_Time"].replace("Z", "+00:00")) if lead_data.get("Modified_Time") else None
                )
                leads.append(lead)
            
            return leads
            
        except Exception as e:
            self.logger.error(f"Failed to get leads: {e}")
            raise
    
    async def update_lead(
        self,
        lead_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        status: Optional[ZohoLeadStatus] = None,
        source: Optional[str] = None,
        description: Optional[str] = None
    ) -> ZohoLead:
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
            url = f"{self.config.base_url}/Leads/{lead_id}"
            
            data = {"data": [{"id": lead_id}]}
            
            if first_name:
                data["data"][0]["First_Name"] = first_name
            if last_name:
                data["data"][0]["Last_Name"] = last_name
            if email:
                data["data"][0]["Email"] = email
            if phone:
                data["data"][0]["Phone"] = phone
            if company:
                data["data"][0]["Company"] = company
            if status:
                data["data"][0]["Status"] = status.value
            if source:
                data["data"][0]["Lead_Source"] = source
            if description:
                data["data"][0]["Description"] = description
            
            response = self.session.put(url, json=data, headers=self._get_headers())
            response.raise_for_status()
            
            result = response.json()
            lead_data = result["data"][0]["details"]
            
            return ZohoLead(
                id=lead_data["id"],
                first_name=lead_data["First_Name"],
                last_name=lead_data["Last_Name"],
                email=lead_data.get("Email"),
                phone=lead_data.get("Phone"),
                company=lead_data.get("Company"),
                status=ZohoLeadStatus(lead_data["Status"]),
                source=lead_data.get("Lead_Source"),
                description=lead_data.get("Description"),
                created_at=datetime.fromisoformat(lead_data["Created_Time"].replace("Z", "+00:00")) if lead_data.get("Created_Time") else None,
                updated_at=datetime.fromisoformat(lead_data["Modified_Time"].replace("Z", "+00:00")) if lead_data.get("Modified_Time") else None
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
        account_id: Optional[str] = None,
        title: Optional[str] = None,
        department: Optional[str] = None
    ) -> ZohoContact:
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
            url = f"{self.config.base_url}/Contacts"
            
            data = {
                "data": [{
                    "First_Name": first_name,
                    "Last_Name": last_name
                }]
            }
            
            if email:
                data["data"][0]["Email"] = email
            if phone:
                data["data"][0]["Phone"] = phone
            if account_id:
                data["data"][0]["Account_Name"] = {"id": account_id}
            if title:
                data["data"][0]["Title"] = title
            if department:
                data["data"][0]["Department"] = department
            
            response = self.session.post(url, json=data, headers=self._get_headers())
            response.raise_for_status()
            
            result = response.json()
            contact_data = result["data"][0]["details"]
            
            return ZohoContact(
                id=contact_data["id"],
                first_name=contact_data["First_Name"],
                last_name=contact_data["Last_Name"],
                email=contact_data.get("Email"),
                phone=contact_data.get("Phone"),
                account_id=contact_data.get("Account_Name", {}).get("id"),
                title=contact_data.get("Title"),
                department=contact_data.get("Department"),
                created_at=datetime.fromisoformat(contact_data["Created_Time"].replace("Z", "+00:00")) if contact_data.get("Created_Time") else None,
                updated_at=datetime.fromisoformat(contact_data["Modified_Time"].replace("Z", "+00:00")) if contact_data.get("Modified_Time") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create contact: {e}")
            raise
    
    async def create_deal(
        self,
        deal_name: str,
        amount: float,
        stage: ZohoDealStage,
        account_id: Optional[str] = None,
        contact_id: Optional[str] = None,
        closing_date: Optional[datetime] = None,
        probability: Optional[int] = None,
        description: Optional[str] = None
    ) -> ZohoDeal:
        """
        Create a deal.
        
        Args:
            deal_name: Deal name
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
            url = f"{self.config.base_url}/Deals"
            
            data = {
                "data": [{
                    "Deal_Name": deal_name,
                    "Amount": amount,
                    "Stage": stage.value
                }]
            }
            
            if account_id:
                data["data"][0]["Account_Name"] = {"id": account_id}
            if contact_id:
                data["data"][0]["Contact_Name"] = {"id": contact_id}
            if closing_date:
                data["data"][0]["Closing_Date"] = closing_date.strftime("%Y-%m-%d")
            if probability:
                data["data"][0]["Probability"] = probability
            if description:
                data["data"][0]["Description"] = description
            
            response = self.session.post(url, json=data, headers=self._get_headers())
            response.raise_for_status()
            
            result = response.json()
            deal_data = result["data"][0]["details"]
            
            return ZohoDeal(
                id=deal_data["id"],
                deal_name=deal_data["Deal_Name"],
                amount=deal_data["Amount"],
                stage=ZohoDealStage(deal_data["Stage"]),
                account_id=deal_data.get("Account_Name", {}).get("id"),
                contact_id=deal_data.get("Contact_Name", {}).get("id"),
                closing_date=datetime.strptime(deal_data["Closing_Date"], "%Y-%m-%d") if deal_data.get("Closing_Date") else None,
                probability=deal_data.get("Probability"),
                description=deal_data.get("Description"),
                created_at=datetime.fromisoformat(deal_data["Created_Time"].replace("Z", "+00:00")) if deal_data.get("Created_Time") else None,
                updated_at=datetime.fromisoformat(deal_data["Modified_Time"].replace("Z", "+00:00")) if deal_data.get("Modified_Time") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create deal: {e}")
            raise
    
    async def create_task(
        self,
        subject: str,
        description: Optional[str] = None,
        due_date: Optional[datetime] = None,
        status: str = "Not Started",
        priority: str = "Medium",
        related_to_id: Optional[str] = None,
        related_to_type: Optional[str] = None
    ) -> ZohoTask:
        """
        Create a task.
        
        Args:
            subject: Task subject
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
            url = f"{self.config.base_url}/Tasks"
            
            data = {
                "data": [{
                    "Subject": subject,
                    "Status": status,
                    "Priority": priority
                }]
            }
            
            if description:
                data["data"][0]["Description"] = description
            if due_date:
                data["data"][0]["Due_Date"] = due_date.strftime("%Y-%m-%d")
            if related_to_id and related_to_type:
                data["data"][0]["What_Id"] = {"id": related_to_id}
            
            response = self.session.post(url, json=data, headers=self._get_headers())
            response.raise_for_status()
            
            result = response.json()
            task_data = result["data"][0]["details"]
            
            return ZohoTask(
                id=task_data["id"],
                subject=task_data["Subject"],
                description=task_data.get("Description"),
                due_date=datetime.strptime(task_data["Due_Date"], "%Y-%m-%d") if task_data.get("Due_Date") else None,
                status=task_data["Status"],
                priority=task_data["Priority"],
                related_to_id=task_data.get("What_Id", {}).get("id"),
                related_to_type=task_data.get("What_Id", {}).get("name"),
                created_at=datetime.fromisoformat(task_data["Created_Time"].replace("Z", "+00:00")) if task_data.get("Created_Time") else None,
                updated_at=datetime.fromisoformat(task_data["Modified_Time"].replace("Z", "+00:00")) if task_data.get("Modified_Time") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create task: {e}")
            raise
    
    async def get_modules(self) -> List[Dict[str, Any]]:
        """
        Get available modules.
        
        Returns:
            List of modules
        """
        try:
            url = f"{self.config.base_url}/settings/modules"
            response = self.session.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            result = response.json()
            return result.get("modules", [])
            
        except Exception as e:
            self.logger.error(f"Failed to get modules: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Zoho CRM integration.
        
        Returns:
            Health check results
        """
        try:
            # Test API connectivity by getting modules
            modules = await self.get_modules()
            
            # Test lead retrieval
            leads = await self.get_leads(limit=1)
            
            return {
                "status": "healthy",
                "base_url": self.config.base_url,
                "modules_count": len(modules),
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

