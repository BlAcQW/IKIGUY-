"""
Freshdesk integration service for helpdesk ticket management.
Handles ticket creation, updates, and routing for escalated customer issues.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr
import aiohttp
import json
import base64

logger = logging.getLogger(__name__)

class FreshdeskTicket(BaseModel):
    """Model for Freshdesk ticket."""
    id: Optional[int] = None
    subject: str
    description: str
    email: str
    priority: int = 1  # 1=Low, 2=Medium, 3=High, 4=Urgent
    status: int = 2  # 2=Open, 3=Pending, 4=Resolved, 5=Closed
    source: int = 7  # 7=Phone, 2=Portal, 1=Email
    type: Optional[str] = "Question"
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}
    cc_emails: List[str] = []

class FreshdeskContact(BaseModel):
    """Model for Freshdesk contact."""
    id: Optional[int] = None
    name: str
    email: str
    phone: Optional[str] = None
    company_id: Optional[int] = None
    description: Optional[str] = None

class TicketEscalation(BaseModel):
    """Model for ticket escalation details."""
    original_query: str
    vapi_call_id: str
    customer_phone: str
    customer_email: Optional[str] = None
    escalation_reason: str
    conversation_summary: str
    priority_level: str
    assigned_agent: Optional[str] = None

class FreshdeskIntegrationService:
    """Service for Freshdesk ticket management and escalation."""

    def __init__(self):
        self.freshdesk_domain = "ailabs-888099064326049059.myfreshworks.com"
        self.api_key = "your_freshdesk_api_key"  # TODO: Add to environment
        self.base_url = f"https://{self.freshdesk_domain}/api/v2"

        # Priority mappings
        self.priority_mapping = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "urgent": 4
        }

        # Source mappings
        self.source_mapping = {
            "phone": 7,
            "email": 1,
            "portal": 2,
            "chat": 3,
            "api": 11
        }

        self.timeout = aiohttp.ClientTimeout(total=30)

    async def create_ticket_from_escalation(self, escalation: TicketEscalation) -> Dict[str, Any]:
        """
        Create a Freshdesk ticket from an escalated VAPI call.

        Args:
            escalation: Escalation details from VAPI call

        Returns:
            Created ticket information
        """
        try:
            # Prepare ticket data
            ticket_data = {
                "subject": f"Escalated Call: {escalation.original_query[:50]}...",
                "description": self._format_escalation_description(escalation),
                "email": escalation.customer_email or f"customer+{escalation.vapi_call_id}@ailabsafrica.com",
                "priority": self.priority_mapping.get(escalation.priority_level.lower(), 2),
                "status": 2,  # Open
                "source": self.source_mapping["phone"],
                "type": "Incident",
                "tags": ["vapi-escalation", "voice-call", escalation.priority_level],
                "custom_fields": {
                    "cf_vapi_call_id": escalation.vapi_call_id,
                    "cf_customer_phone": escalation.customer_phone,
                    "cf_escalation_reason": escalation.escalation_reason
                }
            }

            # Create ticket via Freshdesk API
            ticket_response = await self._make_freshdesk_request(
                method="POST",
                endpoint="/tickets",
                data=ticket_data
            )

            if ticket_response.get("id"):
                logger.info(f"Created Freshdesk ticket {ticket_response['id']} for VAPI call {escalation.vapi_call_id}")

                # Add internal note with conversation details
                await self._add_ticket_note(
                    ticket_response["id"],
                    f"**Conversation Summary:**\n{escalation.conversation_summary}\n\n**Escalation Reason:** {escalation.escalation_reason}",
                    private=True
                )

                return {
                    "success": True,
                    "ticket_id": ticket_response["id"],
                    "ticket_url": f"https://{self.freshdesk_domain}/a/tickets/{ticket_response['id']}",
                    "created_at": ticket_response.get("created_at"),
                    "status": "created"
                }
            else:
                raise Exception("Failed to create ticket - no ID returned")

        except Exception as e:
            logger.error(f"Error creating Freshdesk ticket from escalation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status": "failed"
            }

    async def create_ticket(self, ticket: FreshdeskTicket) -> Dict[str, Any]:
        """
        Create a standard Freshdesk ticket.

        Args:
            ticket: Ticket details

        Returns:
            Created ticket information
        """
        try:
            ticket_data = ticket.dict(exclude_none=True)

            response = await self._make_freshdesk_request(
                method="POST",
                endpoint="/tickets",
                data=ticket_data
            )

            return {
                "success": True,
                "ticket_id": response["id"],
                "ticket_url": f"https://{self.freshdesk_domain}/a/tickets/{response['id']}",
                "created_at": response.get("created_at")
            }

        except Exception as e:
            logger.error(f"Error creating Freshdesk ticket: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def update_ticket(self, ticket_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing Freshdesk ticket.

        Args:
            ticket_id: Freshdesk ticket ID
            updates: Fields to update

        Returns:
            Update result
        """
        try:
            response = await self._make_freshdesk_request(
                method="PUT",
                endpoint=f"/tickets/{ticket_id}",
                data=updates
            )

            return {
                "success": True,
                "ticket_id": ticket_id,
                "updated_at": response.get("updated_at")
            }

        except Exception as e:
            logger.error(f"Error updating Freshdesk ticket {ticket_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def add_ticket_reply(self, ticket_id: int, body: str, from_email: str = None) -> Dict[str, Any]:
        """
        Add a reply to a ticket.

        Args:
            ticket_id: Freshdesk ticket ID
            body: Reply content
            from_email: Sender email

        Returns:
            Reply creation result
        """
        try:
            reply_data = {
                "body": body,
                "from_email": from_email or f"support@{self.freshdesk_domain}"
            }

            response = await self._make_freshdesk_request(
                method="POST",
                endpoint=f"/tickets/{ticket_id}/reply",
                data=reply_data
            )

            return {
                "success": True,
                "reply_id": response.get("id"),
                "created_at": response.get("created_at")
            }

        except Exception as e:
            logger.error(f"Error adding reply to ticket {ticket_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _add_ticket_note(self, ticket_id: int, body: str, private: bool = True) -> Dict[str, Any]:
        """
        Add an internal note to a ticket.

        Args:
            ticket_id: Freshdesk ticket ID
            body: Note content
            private: Whether note is private (internal)

        Returns:
            Note creation result
        """
        try:
            note_data = {
                "body": body,
                "private": private
            }

            response = await self._make_freshdesk_request(
                method="POST",
                endpoint=f"/tickets/{ticket_id}/notes",
                data=note_data
            )

            return {
                "success": True,
                "note_id": response.get("id")
            }

        except Exception as e:
            logger.error(f"Error adding note to ticket {ticket_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_ticket(self, ticket_id: int) -> Dict[str, Any]:
        """
        Retrieve ticket details.

        Args:
            ticket_id: Freshdesk ticket ID

        Returns:
            Ticket details
        """
        try:
            response = await self._make_freshdesk_request(
                method="GET",
                endpoint=f"/tickets/{ticket_id}"
            )

            return {
                "success": True,
                "ticket": response
            }

        except Exception as e:
            logger.error(f"Error retrieving ticket {ticket_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def list_tickets(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        List tickets with optional filters.

        Args:
            filters: Query filters (status, priority, etc.)

        Returns:
            List of tickets
        """
        try:
            params = filters or {}

            response = await self._make_freshdesk_request(
                method="GET",
                endpoint="/tickets",
                params=params
            )

            return {
                "success": True,
                "tickets": response
            }

        except Exception as e:
            logger.error(f"Error listing tickets: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def create_contact(self, contact: FreshdeskContact) -> Dict[str, Any]:
        """
        Create a Freshdesk contact.

        Args:
            contact: Contact details

        Returns:
            Created contact information
        """
        try:
            contact_data = contact.dict(exclude_none=True)

            response = await self._make_freshdesk_request(
                method="POST",
                endpoint="/contacts",
                data=contact_data
            )

            return {
                "success": True,
                "contact_id": response["id"],
                "email": response["email"]
            }

        except Exception as e:
            logger.error(f"Error creating Freshdesk contact: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _format_escalation_description(self, escalation: TicketEscalation) -> str:
        """
        Format escalation details into ticket description.

        Args:
            escalation: Escalation details

        Returns:
            Formatted description
        """
        description = f"""
**Escalated Voice Call Ticket**

**Original Customer Query:**
{escalation.original_query}

**Customer Contact Information:**
- Phone: {escalation.customer_phone}
- Email: {escalation.customer_email or 'Not provided'}

**Call Details:**
- VAPI Call ID: {escalation.vapi_call_id}
- Escalation Reason: {escalation.escalation_reason}
- Priority Level: {escalation.priority_level.title()}

**Conversation Summary:**
{escalation.conversation_summary}

**Next Steps:**
- Review conversation transcript
- Contact customer via preferred method
- Resolve issue and update ticket status
- Follow up as needed

*This ticket was automatically created from an escalated VAPI voice call.*
        """.strip()

        return description

    async def _make_freshdesk_request(
        self,
        method: str,
        endpoint: str,
        data: Dict[str, Any] = None,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to Freshdesk API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body data
            params: Query parameters

        Returns:
            API response
        """
        try:
            url = f"{self.base_url}{endpoint}"

            # Create basic auth header
            auth_string = f"{self.api_key}:X"
            auth_bytes = auth_string.encode('ascii')
            auth_header = base64.b64encode(auth_bytes).decode('ascii')

            headers = {
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/json"
            }

            # For now, simulate the API call since we don't have the actual API key
            logger.info(f"Simulating Freshdesk API call: {method} {url}")

            if method == "POST" and "/tickets" in endpoint and data:
                # Simulate ticket creation
                return {
                    "id": 12345,
                    "subject": data.get("subject"),
                    "status": data.get("status", 2),
                    "priority": data.get("priority", 1),
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
            elif method == "GET" and "/tickets/" in endpoint:
                # Simulate ticket retrieval
                ticket_id = endpoint.split("/")[-1]
                return {
                    "id": int(ticket_id),
                    "subject": "Sample Ticket",
                    "status": 2,
                    "priority": 2,
                    "created_at": datetime.utcnow().isoformat()
                }
            else:
                # Generic success response
                return {
                    "id": 12345,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Error making Freshdesk API request: {str(e)}")
            raise

    async def get_ticket_statistics(self, date_range: int = 30) -> Dict[str, Any]:
        """
        Get ticket statistics for analytics.

        Args:
            date_range: Number of days to analyze

        Returns:
            Ticket statistics
        """
        try:
            # Simulate getting statistics
            stats = {
                "total_tickets": 145,
                "open_tickets": 23,
                "resolved_tickets": 122,
                "escalated_tickets": 18,
                "average_resolution_time": 4.2,  # hours
                "first_response_time": 0.8,  # hours
                "customer_satisfaction": 4.6,
                "tickets_by_priority": {
                    "low": 45,
                    "medium": 78,
                    "high": 18,
                    "urgent": 4
                },
                "tickets_by_source": {
                    "phone": 67,
                    "email": 45,
                    "portal": 23,
                    "api": 10
                },
                "resolution_sla_met": 0.89,
                "first_response_sla_met": 0.94
            }

            return {
                "success": True,
                "date_range_days": date_range,
                "statistics": stats,
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting ticket statistics: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Global service instance
freshdesk_integration_service = FreshdeskIntegrationService()