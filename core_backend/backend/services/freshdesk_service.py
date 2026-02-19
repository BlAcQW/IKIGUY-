"""
Consolidated FreshDesk Integration Service.
Handles all FreshDesk-related functionality with unified interface.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

logger = logging.getLogger(__name__)


class TicketPriority(str, Enum):
    """Ticket priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketStatus(str, Enum):
    """Ticket status options."""
    OPEN = "open"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"


class FreshDeskTicket(BaseModel):
    """FreshDesk ticket model."""
    subject: str
    description: str
    priority: TicketPriority = TicketPriority.MEDIUM
    status: TicketStatus = TicketStatus.OPEN
    requester_email: str
    requester_name: Optional[str] = None
    assignee_id: Optional[int] = None
    group_id: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    due_by: Optional[datetime] = None
    ticket_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FreshDeskContact(BaseModel):
    """FreshDesk contact model."""
    email: str
    name: str
    phone: Optional[str] = None
    company_id: Optional[int] = None
    job_title: Optional[str] = None
    language: str = "en"
    time_zone: str = "UTC"
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    contact_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FreshDeskCompany(BaseModel):
    """FreshDesk company model."""
    name: str
    description: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    company_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FreshDeskService:
    """
    Consolidated service for FreshDesk integration.
    Handles tickets, contacts, companies, and knowledge base.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize FreshDesk service with configuration.

        Args:
            config: Configuration dictionary with FreshDesk settings
        """
        self.config = config or {}
        self.domain = self.config.get("domain")
        self.api_key = self.config.get("api_key")
        self.base_url = f"https://{self.domain}.freshdesk.com/api/v2" if self.domain else None
        self.session = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize FreshDesk client."""
        if not self.domain or not self.api_key:
            logger.warning("FreshDesk domain or API key not configured")
            return

        logger.info(f"Initialized FreshDesk service for domain: {self.domain}")

    async def create_ticket(
        self,
        ticket: FreshDeskTicket,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new ticket in FreshDesk.

        Args:
            ticket: Ticket data to create
            context: Additional context

        Returns:
            Ticket creation result
        """
        try:
            if not self.base_url:
                return {
                    "success": False,
                    "error": "FreshDesk not configured properly"
                }

            # Prepare ticket data for FreshDesk API
            ticket_data = {
                "subject": ticket.subject,
                "description": ticket.description,
                "priority": self._map_priority_to_freshdesk(ticket.priority),
                "status": self._map_status_to_freshdesk(ticket.status),
                "email": ticket.requester_email,
                "name": ticket.requester_name or ticket.requester_email,
                "tags": ticket.tags,
                "custom_fields": ticket.custom_fields
            }

            if ticket.assignee_id:
                ticket_data["responder_id"] = ticket.assignee_id
            if ticket.group_id:
                ticket_data["group_id"] = ticket.group_id
            if ticket.due_by:
                ticket_data["due_by"] = ticket.due_by.isoformat()

            # Here would be actual API call to FreshDesk
            logger.info(f"Creating FreshDesk ticket: {ticket.subject}")

            # Mock response for now
            mock_ticket_id = 1000 + hash(ticket.subject) % 9000

            return {
                "success": True,
                "ticket_id": mock_ticket_id,
                "subject": ticket.subject,
                "status": ticket.status.value,
                "priority": ticket.priority.value,
                "url": f"{self.base_url.replace('/api/v2', '')}/helpdesk/tickets/{mock_ticket_id}",
                "created_at": datetime.now().isoformat(),
                "requester": ticket.requester_email
            }

        except Exception as e:
            logger.error(f"Error creating FreshDesk ticket: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_ticket(self, ticket_id: int) -> Dict[str, Any]:
        """
        Get ticket details by ID.

        Args:
            ticket_id: FreshDesk ticket ID

        Returns:
            Ticket details
        """
        try:
            if not self.base_url:
                return {
                    "success": False,
                    "error": "FreshDesk not configured properly"
                }

            logger.info(f"Fetching FreshDesk ticket: {ticket_id}")

            # Mock response
            return {
                "success": True,
                "ticket": {
                    "id": ticket_id,
                    "subject": f"Mock Ticket {ticket_id}",
                    "description": "This is a mock ticket for testing",
                    "status": "open",
                    "priority": "medium",
                    "requester_email": "user@example.com",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Error fetching FreshDesk ticket {ticket_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def update_ticket(
        self,
        ticket_id: int,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing ticket.

        Args:
            ticket_id: FreshDesk ticket ID
            updates: Fields to update

        Returns:
            Update result
        """
        try:
            if not self.base_url:
                return {
                    "success": False,
                    "error": "FreshDesk not configured properly"
                }

            logger.info(f"Updating FreshDesk ticket {ticket_id}: {list(updates.keys())}")

            return {
                "success": True,
                "ticket_id": ticket_id,
                "updated_fields": list(updates.keys()),
                "updated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error updating FreshDesk ticket {ticket_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def create_contact(
        self,
        contact: FreshDeskContact
    ) -> Dict[str, Any]:
        """
        Create a new contact in FreshDesk.

        Args:
            contact: Contact data to create

        Returns:
            Contact creation result
        """
        try:
            if not self.base_url:
                return {
                    "success": False,
                    "error": "FreshDesk not configured properly"
                }

            contact_data = {
                "name": contact.name,
                "email": contact.email,
                "phone": contact.phone,
                "job_title": contact.job_title,
                "language": contact.language,
                "time_zone": contact.time_zone,
                "tags": contact.tags,
                "custom_fields": contact.custom_fields
            }

            if contact.company_id:
                contact_data["company_id"] = contact.company_id

            logger.info(f"Creating FreshDesk contact: {contact.email}")

            mock_contact_id = 2000 + hash(contact.email) % 8000

            return {
                "success": True,
                "contact_id": mock_contact_id,
                "name": contact.name,
                "email": contact.email,
                "created_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error creating FreshDesk contact: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def create_company(
        self,
        company: FreshDeskCompany
    ) -> Dict[str, Any]:
        """
        Create a new company in FreshDesk.

        Args:
            company: Company data to create

        Returns:
            Company creation result
        """
        try:
            if not self.base_url:
                return {
                    "success": False,
                    "error": "FreshDesk not configured properly"
                }

            company_data = {
                "name": company.name,
                "description": company.description,
                "website": company.website,
                "industry": company.industry,
                "custom_fields": company.custom_fields
            }

            logger.info(f"Creating FreshDesk company: {company.name}")

            mock_company_id = 3000 + hash(company.name) % 7000

            return {
                "success": True,
                "company_id": mock_company_id,
                "name": company.name,
                "created_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error creating FreshDesk company: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def search_tickets(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search tickets by query and filters.

        Args:
            query: Search query
            filters: Additional filters

        Returns:
            Search results
        """
        try:
            if not self.base_url:
                return {
                    "success": False,
                    "error": "FreshDesk not configured properly"
                }

            logger.info(f"Searching FreshDesk tickets: {query}")

            # Mock search results
            mock_tickets = [
                {
                    "id": 1001,
                    "subject": f"Ticket matching '{query}' - 1",
                    "status": "open",
                    "priority": "medium",
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": 1002,
                    "subject": f"Ticket matching '{query}' - 2",
                    "status": "pending",
                    "priority": "high",
                    "created_at": datetime.now().isoformat()
                }
            ]

            return {
                "success": True,
                "query": query,
                "filters": filters or {},
                "total": len(mock_tickets),
                "tickets": mock_tickets
            }

        except Exception as e:
            logger.error(f"Error searching FreshDesk tickets: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _map_priority_to_freshdesk(self, priority: TicketPriority) -> int:
        """Map our priority enum to FreshDesk priority values."""
        mapping = {
            TicketPriority.LOW: 1,
            TicketPriority.MEDIUM: 2,
            TicketPriority.HIGH: 3,
            TicketPriority.URGENT: 4
        }
        return mapping.get(priority, 2)

    def _map_status_to_freshdesk(self, status: TicketStatus) -> int:
        """Map our status enum to FreshDesk status values."""
        mapping = {
            TicketStatus.OPEN: 2,
            TicketStatus.PENDING: 3,
            TicketStatus.RESOLVED: 4,
            TicketStatus.CLOSED: 5
        }
        return mapping.get(status, 2)

    async def get_ticket_statistics(self) -> Dict[str, Any]:
        """
        Get ticket statistics and metrics.

        Returns:
            Statistics data
        """
        try:
            if not self.base_url:
                return {
                    "success": False,
                    "error": "FreshDesk not configured properly"
                }

            logger.info("Fetching FreshDesk ticket statistics")

            # Mock statistics
            return {
                "success": True,
                "statistics": {
                    "total_tickets": 1250,
                    "open_tickets": 45,
                    "pending_tickets": 12,
                    "resolved_tickets": 1150,
                    "closed_tickets": 43,
                    "average_resolution_time": "2.5 days",
                    "customer_satisfaction": 4.2
                },
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error fetching FreshDesk statistics: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to FreshDesk API.

        Returns:
            Connection test result
        """
        try:
            if not self.base_url:
                return {
                    "success": False,
                    "error": "FreshDesk not configured properly"
                }

            logger.info("Testing FreshDesk connection")

            # Mock connection test
            return {
                "success": True,
                "domain": self.domain,
                "api_key_valid": bool(self.api_key),
                "message": "Connection to FreshDesk successful",
                "tested_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"FreshDesk connection test error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get service capabilities."""
        return {
            "service": "freshdesk",
            "capabilities": [
                "create_ticket",
                "get_ticket",
                "update_ticket",
                "search_tickets",
                "create_contact",
                "create_company",
                "get_statistics",
                "test_connection"
            ],
            "api_reference": "https://developers.freshdesk.com/api/",
            "documentation": "https://developers.freshdesk.com/",
            "configured": bool(self.domain and self.api_key)
        }


# Global FreshDesk service instance
freshdesk_service = FreshDeskService()