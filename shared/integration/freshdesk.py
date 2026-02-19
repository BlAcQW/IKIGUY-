"""
Freshdesk Integration Module

This module provides integration with Freshdesk for helpdesk and ticketing automation,
including ticket management, contact management, and customer support workflows.
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
    FRESHDESK_AVAILABLE = True
except ImportError:
    FRESHDESK_AVAILABLE = False
    logging.warning("Freshdesk APIs not available. Install requests")

logger = logging.getLogger(__name__)


class FreshdeskTicketStatus(Enum):
    """Freshdesk ticket status."""
    OPEN = 2
    PENDING = 3
    RESOLVED = 4
    CLOSED = 5
    WAITING_ON_CUSTOMER = 6
    WAITING_ON_THIRD_PARTY = 7


class FreshdeskTicketPriority(Enum):
    """Freshdesk ticket priority."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class FreshdeskTicketSource(Enum):
    """Freshdesk ticket source."""
    EMAIL = 1
    PORTAL = 2
    PHONE = 3
    CHAT = 4
    FEEDBACK_WIDGET = 5
    OUTBOUND_EMAIL = 6


class FreshdeskTicketType(Enum):
    """Freshdesk ticket type."""
    QUESTION = "Question"
    INCIDENT = "Incident"
    PROBLEM = "Problem"
    FEATURE_REQUEST = "Feature Request"
    BUG = "Bug"


@dataclass
class FreshdeskConfig:
    """Configuration for Freshdesk integration."""
    
    domain: str
    """Freshdesk domain (e.g., 'company.freshdesk.com')."""
    
    api_key: str
    """Freshdesk API key."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    verify_ssl: bool = True
    """Verify SSL certificates."""
    
    webhook_secret: Optional[str] = None
    """Webhook secret for verification."""


@dataclass
class FreshdeskContact:
    """Freshdesk contact data structure."""

    name: str
    """Contact name."""

    email: str
    """Contact email."""

    id: Optional[int] = None
    """Contact ID."""

    phone: Optional[str] = None
    """Contact phone number."""
    
    mobile: Optional[str] = None
    """Contact mobile number."""
    
    company_id: Optional[int] = None
    """Company ID."""
    
    job_title: Optional[str] = None
    """Job title."""
    
    address: Optional[str] = None
    """Address."""
    
    city: Optional[str] = None
    """City."""
    
    state: Optional[str] = None
    """State."""
    
    country: Optional[str] = None
    """Country."""
    
    zipcode: Optional[str] = None
    """Zip code."""
    
    time_zone: Optional[str] = None
    """Time zone."""
    
    language: Optional[str] = None
    """Language."""
    
    avatar: Optional[Dict[str, Any]] = None
    """Avatar information."""
    
    tags: List[str] = field(default_factory=list)
    """Contact tags."""
    
    other_emails: List[str] = field(default_factory=list)
    """Other email addresses."""
    
    twitter_id: Optional[str] = None
    """Twitter ID."""
    
    unique_external_id: Optional[str] = None
    """Unique external ID."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class FreshdeskCompany:
    """Freshdesk company data structure."""

    name: str
    """Company name."""

    id: Optional[int] = None
    """Company ID."""
    
    description: Optional[str] = None
    """Company description."""
    
    note: Optional[str] = None
    """Company note."""
    
    domains: List[str] = field(default_factory=list)
    """Company domains."""
    
    industry: Optional[str] = None
    """Industry."""
    
    health_score: Optional[str] = None
    """Health score."""
    
    account_tier: Optional[str] = None
    """Account tier."""
    
    renewal_date: Optional[datetime] = None
    """Renewal date."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class FreshdeskTicket:
    """Freshdesk ticket data structure."""

    subject: str
    """Ticket subject."""

    description: str
    """Ticket description."""

    email: str
    """Requester email."""

    requester_id: int
    """Requester ID."""

    id: Optional[int] = None
    """Ticket ID."""

    status: FreshdeskTicketStatus = FreshdeskTicketStatus.OPEN
    """Ticket status."""

    priority: FreshdeskTicketPriority = FreshdeskTicketPriority.MEDIUM
    """Ticket priority."""

    source: FreshdeskTicketSource = FreshdeskTicketSource.EMAIL
    """Ticket source."""

    ticket_type: Optional[FreshdeskTicketType] = None
    """Ticket type."""
    
    responder_id: Optional[int] = None
    """Responder ID."""
    
    company_id: Optional[int] = None
    """Company ID."""
    
    group_id: Optional[int] = None
    """Group ID."""
    
    agent_id: Optional[int] = None
    """Agent ID."""
    
    tags: List[str] = field(default_factory=list)
    """Ticket tags."""
    
    cc_emails: List[str] = field(default_factory=list)
    """CC emails."""
    
    bcc_emails: List[str] = field(default_factory=list)
    """BCC emails."""
    
    due_by: Optional[datetime] = None
    """Due by date."""
    
    fr_due_by: Optional[datetime] = None
    """First response due by."""
    
    is_escalated: bool = False
    """Is escalated."""
    
    fr_escalated: bool = False
    """First response escalated."""
    
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    """Custom fields."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class FreshdeskConversation:
    """Freshdesk conversation data structure."""

    body: str
    """Conversation body."""

    id: Optional[int] = None
    """Conversation ID."""
    
    body_text: Optional[str] = None
    """Conversation body text."""
    
    from_email: Optional[str] = None
    """From email."""
    
    to_emails: List[str] = field(default_factory=list)
    """To emails."""
    
    cc_emails: List[str] = field(default_factory=list)
    """CC emails."""
    
    bcc_emails: List[str] = field(default_factory=list)
    """BCC emails."""
    
    user_id: Optional[int] = None
    """User ID."""
    
    incoming: bool = False
    """Is incoming."""
    
    private: bool = False
    """Is private."""
    
    source: int = 0
    """Source."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""


@dataclass
class FreshdeskAgent:
    """Freshdesk agent data structure."""

    first_name: str
    """First name."""

    last_name: str
    """Last name."""

    email: str
    """Email."""

    id: Optional[int] = None
    """Agent ID."""
    
    mobile: Optional[str] = None
    """Mobile number."""
    
    phone: Optional[str] = None
    """Phone number."""
    
    job_title: Optional[str] = None
    """Job title."""
    
    department: Optional[str] = None
    """Department."""
    
    address: Optional[str] = None
    """Address."""
    
    city: Optional[str] = None
    """City."""
    
    state: Optional[str] = None
    """State."""
    
    country: Optional[str] = None
    """Country."""
    
    time_zone: Optional[str] = None
    """Time zone."""
    
    language: Optional[str] = None
    """Language."""
    
    avatar: Optional[Dict[str, Any]] = None
    """Avatar information."""
    
    role_ids: List[int] = field(default_factory=list)
    """Role IDs."""
    
    group_ids: List[int] = field(default_factory=list)
    """Group IDs."""
    
    active: bool = True
    """Is active."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


class FreshdeskIntegration:
    """Freshdesk integration for helpdesk and ticketing automation."""
    
    def __init__(self, config: FreshdeskConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.verify_ssl
        
        # Set up authentication
        import base64
        auth_string = f"{config.api_key}:X"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        self.session.headers.update({
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/json"
        })
        
        self.base_url = f"https://{config.domain}/api/v2"
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the Freshdesk API."""
        try:
            url = f"{self.base_url}/{endpoint}"
            
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to make {method} request to {endpoint}: {e}")
            raise
    
    async def create_ticket(self, ticket: FreshdeskTicket) -> FreshdeskTicket:
        """
        Create a new ticket.
        
        Args:
            ticket: Ticket data
            
        Returns:
            Created ticket
        """
        try:
            data = {
                "subject": ticket.subject,
                "description": ticket.description,
                "status": ticket.status.value,
                "priority": ticket.priority.value,
                "source": ticket.source.value,
                "requester_id": ticket.requester_id
            }
            
            if ticket.ticket_type:
                data["type"] = ticket.ticket_type.value
            if ticket.responder_id:
                data["responder_id"] = ticket.responder_id
            if ticket.company_id:
                data["company_id"] = ticket.company_id
            if ticket.group_id:
                data["group_id"] = ticket.group_id
            if ticket.agent_id:
                data["agent_id"] = ticket.agent_id
            if ticket.tags:
                data["tags"] = ticket.tags
            if ticket.cc_emails:
                data["cc_emails"] = ticket.cc_emails
            if ticket.bcc_emails:
                data["bcc_emails"] = ticket.bcc_emails
            if ticket.due_by:
                data["due_by"] = ticket.due_by.isoformat()
            if ticket.fr_due_by:
                data["fr_due_by"] = ticket.fr_due_by.isoformat()
            if ticket.custom_fields:
                data.update(ticket.custom_fields)
            
            result = self._make_request("POST", "tickets", data)
            
            ticket.id = result["id"]
            ticket.created_at = datetime.fromisoformat(result["created_at"].replace("Z", "+00:00"))
            ticket.updated_at = datetime.fromisoformat(result["updated_at"].replace("Z", "+00:00"))
            
            self.logger.info(f"Created Freshdesk ticket: {ticket.id}")
            return ticket
            
        except Exception as e:
            self.logger.error(f"Failed to create ticket: {e}")
            raise
    
    async def get_ticket(self, ticket_id: int) -> FreshdeskTicket:
        """
        Get a ticket by ID.
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            Ticket data
        """
        try:
            result = self._make_request("GET", f"tickets/{ticket_id}")
            
            return FreshdeskTicket(
                id=result["id"],
                subject=result["subject"],
                description=result["description"],
                status=FreshdeskTicketStatus(result["status"]),
                priority=FreshdeskTicketPriority(result["priority"]),
                source=FreshdeskTicketSource(result["source"]),
                ticket_type=FreshdeskTicketType(result["type"]) if result.get("type") else None,
                requester_id=result["requester_id"],
                responder_id=result.get("responder_id"),
                company_id=result.get("company_id"),
                group_id=result.get("group_id"),
                agent_id=result.get("agent_id"),
                tags=result.get("tags", []),
                cc_emails=result.get("cc_emails", []),
                bcc_emails=result.get("bcc_emails", []),
                due_by=datetime.fromisoformat(result["due_by"].replace("Z", "+00:00")) if result.get("due_by") else None,
                fr_due_by=datetime.fromisoformat(result["fr_due_by"].replace("Z", "+00:00")) if result.get("fr_due_by") else None,
                is_escalated=result.get("is_escalated", False),
                fr_escalated=result.get("fr_escalated", False),
                custom_fields={k: v for k, v in result.items() if k.startswith("custom_field_")},
                created_at=datetime.fromisoformat(result["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(result["updated_at"].replace("Z", "+00:00"))
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get ticket: {e}")
            raise
    
    async def update_ticket(self, ticket_id: int, updates: Dict[str, Any]) -> FreshdeskTicket:
        """
        Update a ticket.
        
        Args:
            ticket_id: Ticket ID
            updates: Update data
            
        Returns:
            Updated ticket
        """
        try:
            result = self._make_request("PUT", f"tickets/{ticket_id}", updates)
            
            return await self.get_ticket(ticket_id)
            
        except Exception as e:
            self.logger.error(f"Failed to update ticket: {e}")
            raise
    
    async def delete_ticket(self, ticket_id: int) -> bool:
        """
        Delete a ticket.
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            Success status
        """
        try:
            self._make_request("DELETE", f"tickets/{ticket_id}")
            self.logger.info(f"Deleted Freshdesk ticket: {ticket_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete ticket: {e}")
            raise
    
    async def get_tickets(self, filters: Optional[Dict[str, Any]] = None) -> List[FreshdeskTicket]:
        """
        Get tickets with optional filters.
        
        Args:
            filters: Filter parameters
            
        Returns:
            List of tickets
        """
        try:
            endpoint = "tickets"
            if filters:
                query_params = "&".join([f"{k}={v}" for k, v in filters.items()])
                endpoint = f"{endpoint}?{query_params}"
            
            result = self._make_request("GET", endpoint)
            
            tickets = []
            for item in result:
                ticket = FreshdeskTicket(
                    id=item["id"],
                    subject=item["subject"],
                    description=item["description"],
                    status=FreshdeskTicketStatus(item["status"]),
                    priority=FreshdeskTicketPriority(item["priority"]),
                    source=FreshdeskTicketSource(item["source"]),
                    ticket_type=FreshdeskTicketType(item["type"]) if item.get("type") else None,
                    requester_id=item["requester_id"],
                    responder_id=item.get("responder_id"),
                    company_id=item.get("company_id"),
                    group_id=item.get("group_id"),
                    agent_id=item.get("agent_id"),
                    tags=item.get("tags", []),
                    cc_emails=item.get("cc_emails", []),
                    bcc_emails=item.get("bcc_emails", []),
                    due_by=datetime.fromisoformat(item["due_by"].replace("Z", "+00:00")) if item.get("due_by") else None,
                    fr_due_by=datetime.fromisoformat(item["fr_due_by"].replace("Z", "+00:00")) if item.get("fr_due_by") else None,
                    is_escalated=item.get("is_escalated", False),
                    fr_escalated=item.get("fr_escalated", False),
                    custom_fields={k: v for k, v in item.items() if k.startswith("custom_field_")},
                    created_at=datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00"))
                )
                tickets.append(ticket)
            
            return tickets
            
        except Exception as e:
            self.logger.error(f"Failed to get tickets: {e}")
            raise
    
    async def add_conversation(self, ticket_id: int, conversation: FreshdeskConversation) -> FreshdeskConversation:
        """
        Add a conversation to a ticket.
        
        Args:
            ticket_id: Ticket ID
            conversation: Conversation data
            
        Returns:
            Created conversation
        """
        try:
            data = {
                "body": conversation.body,
                "body_text": conversation.body_text,
                "incoming": conversation.incoming,
                "private": conversation.private
            }
            
            if conversation.from_email:
                data["from_email"] = conversation.from_email
            if conversation.to_emails:
                data["to_emails"] = conversation.to_emails
            if conversation.cc_emails:
                data["cc_emails"] = conversation.cc_emails
            if conversation.bcc_emails:
                data["bcc_emails"] = conversation.bcc_emails
            if conversation.user_id:
                data["user_id"] = conversation.user_id
            if conversation.source:
                data["source"] = conversation.source
            
            result = self._make_request("POST", f"tickets/{ticket_id}/conversations", data)
            
            conversation.id = result["id"]
            conversation.created_at = datetime.fromisoformat(result["created_at"].replace("Z", "+00:00"))
            
            self.logger.info(f"Added conversation to ticket {ticket_id}: {conversation.id}")
            return conversation
            
        except Exception as e:
            self.logger.error(f"Failed to add conversation: {e}")
            raise
    
    async def create_contact(self, contact: FreshdeskContact) -> FreshdeskContact:
        """
        Create a new contact.
        
        Args:
            contact: Contact data
            
        Returns:
            Created contact
        """
        try:
            data = {
                "name": contact.name,
                "email": contact.email
            }
            
            if contact.phone:
                data["phone"] = contact.phone
            if contact.mobile:
                data["mobile"] = contact.mobile
            if contact.company_id:
                data["company_id"] = contact.company_id
            if contact.job_title:
                data["job_title"] = contact.job_title
            if contact.address:
                data["address"] = contact.address
            if contact.city:
                data["city"] = contact.city
            if contact.state:
                data["state"] = contact.state
            if contact.country:
                data["country"] = contact.country
            if contact.zipcode:
                data["zipcode"] = contact.zipcode
            if contact.time_zone:
                data["time_zone"] = contact.time_zone
            if contact.language:
                data["language"] = contact.language
            if contact.tags:
                data["tags"] = contact.tags
            if contact.other_emails:
                data["other_emails"] = contact.other_emails
            if contact.twitter_id:
                data["twitter_id"] = contact.twitter_id
            if contact.unique_external_id:
                data["unique_external_id"] = contact.unique_external_id
            
            result = self._make_request("POST", "contacts", data)
            
            contact.id = result["id"]
            contact.created_at = datetime.fromisoformat(result["created_at"].replace("Z", "+00:00"))
            contact.updated_at = datetime.fromisoformat(result["updated_at"].replace("Z", "+00:00"))
            
            self.logger.info(f"Created Freshdesk contact: {contact.id}")
            return contact
            
        except Exception as e:
            self.logger.error(f"Failed to create contact: {e}")
            raise
    
    async def get_contact(self, contact_id: int) -> FreshdeskContact:
        """
        Get a contact by ID.
        
        Args:
            contact_id: Contact ID
            
        Returns:
            Contact data
        """
        try:
            result = self._make_request("GET", f"contacts/{contact_id}")
            
            return FreshdeskContact(
                id=result["id"],
                name=result["name"],
                email=result["email"],
                phone=result.get("phone"),
                mobile=result.get("mobile"),
                company_id=result.get("company_id"),
                job_title=result.get("job_title"),
                address=result.get("address"),
                city=result.get("city"),
                state=result.get("state"),
                country=result.get("country"),
                zipcode=result.get("zipcode"),
                time_zone=result.get("time_zone"),
                language=result.get("language"),
                avatar=result.get("avatar"),
                tags=result.get("tags", []),
                other_emails=result.get("other_emails", []),
                twitter_id=result.get("twitter_id"),
                unique_external_id=result.get("unique_external_id"),
                created_at=datetime.fromisoformat(result["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(result["updated_at"].replace("Z", "+00:00"))
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get contact: {e}")
            raise
    
    async def update_contact(self, contact_id: int, updates: Dict[str, Any]) -> FreshdeskContact:
        """
        Update a contact.
        
        Args:
            contact_id: Contact ID
            updates: Update data
            
        Returns:
            Updated contact
        """
        try:
            result = self._make_request("PUT", f"contacts/{contact_id}", updates)
            
            return await self.get_contact(contact_id)
            
        except Exception as e:
            self.logger.error(f"Failed to update contact: {e}")
            raise
    
    async def delete_contact(self, contact_id: int) -> bool:
        """
        Delete a contact.
        
        Args:
            contact_id: Contact ID
            
        Returns:
            Success status
        """
        try:
            self._make_request("DELETE", f"contacts/{contact_id}")
            self.logger.info(f"Deleted Freshdesk contact: {contact_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete contact: {e}")
            raise
    
    async def create_company(self, company: FreshdeskCompany) -> FreshdeskCompany:
        """
        Create a new company.
        
        Args:
            company: Company data
            
        Returns:
            Created company
        """
        try:
            data = {
                "name": company.name
            }
            
            if company.description:
                data["description"] = company.description
            if company.note:
                data["note"] = company.note
            if company.domains:
                data["domains"] = company.domains
            if company.industry:
                data["industry"] = company.industry
            if company.health_score:
                data["health_score"] = company.health_score
            if company.account_tier:
                data["account_tier"] = company.account_tier
            if company.renewal_date:
                data["renewal_date"] = company.renewal_date.isoformat()
            
            result = self._make_request("POST", "companies", data)
            
            company.id = result["id"]
            company.created_at = datetime.fromisoformat(result["created_at"].replace("Z", "+00:00"))
            company.updated_at = datetime.fromisoformat(result["updated_at"].replace("Z", "+00:00"))
            
            self.logger.info(f"Created Freshdesk company: {company.id}")
            return company
            
        except Exception as e:
            self.logger.error(f"Failed to create company: {e}")
            raise
    
    async def get_company(self, company_id: int) -> FreshdeskCompany:
        """
        Get a company by ID.
        
        Args:
            company_id: Company ID
            
        Returns:
            Company data
        """
        try:
            result = self._make_request("GET", f"companies/{company_id}")
            
            return FreshdeskCompany(
                id=result["id"],
                name=result["name"],
                description=result.get("description"),
                note=result.get("note"),
                domains=result.get("domains", []),
                industry=result.get("industry"),
                health_score=result.get("health_score"),
                account_tier=result.get("account_tier"),
                renewal_date=datetime.fromisoformat(result["renewal_date"].replace("Z", "+00:00")) if result.get("renewal_date") else None,
                created_at=datetime.fromisoformat(result["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(result["updated_at"].replace("Z", "+00:00"))
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get company: {e}")
            raise
    
    async def get_agents(self) -> List[FreshdeskAgent]:
        """
        Get all agents.
        
        Returns:
            List of agents
        """
        try:
            result = self._make_request("GET", "agents")
            
            agents = []
            for item in result:
                agent = FreshdeskAgent(
                    id=item["id"],
                    first_name=item["first_name"],
                    last_name=item["last_name"],
                    email=item["email"],
                    mobile=item.get("mobile"),
                    phone=item.get("phone"),
                    job_title=item.get("job_title"),
                    department=item.get("department"),
                    address=item.get("address"),
                    city=item.get("city"),
                    state=item.get("state"),
                    country=item.get("country"),
                    time_zone=item.get("time_zone"),
                    language=item.get("language"),
                    avatar=item.get("avatar"),
                    role_ids=item.get("role_ids", []),
                    group_ids=item.get("group_ids", []),
                    active=item.get("active", True),
                    created_at=datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00"))
                )
                agents.append(agent)
            
            return agents
            
        except Exception as e:
            self.logger.error(f"Failed to get agents: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Freshdesk integration.
        
        Returns:
            Health check results
        """
        try:
            # Test API connectivity by getting agents
            agents = await self.get_agents()
            
            return {
                "status": "healthy",
                "domain": self.config.domain,
                "total_agents": len(agents),
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

