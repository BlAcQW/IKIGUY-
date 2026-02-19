"""
Zendesk Integration Module

This module provides integration with Zendesk for customer support, ticket management,
and helpdesk automation with comprehensive REST API support.
"""

import asyncio
import json
import logging
import base64
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    import requests
    ZENDESK_AVAILABLE = True
except ImportError:
    ZENDESK_AVAILABLE = False
    logging.warning("Zendesk APIs not available. Install requests")

logger = logging.getLogger(__name__)


class ZendeskPriority(Enum):
    """Zendesk priority levels."""
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class ZendeskStatus(Enum):
    """Zendesk ticket status values."""
    NEW = "new"
    OPEN = "open"
    PENDING = "pending"
    HOLD = "hold"
    SOLVED = "solved"
    CLOSED = "closed"


class ZendeskType(Enum):
    """Zendesk ticket types."""
    INCIDENT = "incident"
    PROBLEM = "problem"
    QUESTION = "question"
    TASK = "task"


class ZendeskUserRole(Enum):
    """Zendesk user roles."""
    END_USER = "end-user"
    AGENT = "agent"
    ADMIN = "admin"


@dataclass
class ZendeskConfig:
    """Configuration for Zendesk integration."""
    
    subdomain: str
    """Zendesk subdomain (e.g., 'company' for company.zendesk.com)."""
    
    email: str
    """Zendesk email address."""
    
    api_token: str
    """Zendesk API token."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    verify_ssl: bool = True
    """Verify SSL certificates."""
    
    api_version: str = "v2"
    """API version to use."""


@dataclass
class ZendeskTicket:
    """Zendesk ticket data structure."""
    
    subject: str
    """Ticket subject."""
    
    description: str
    """Ticket description."""
    
    requester_id: int
    """Requester ID."""
    
    id: Optional[int] = None
    """Ticket ID."""
    
    status: ZendeskStatus = ZendeskStatus.NEW
    """Ticket status."""
    
    priority: ZendeskPriority = ZendeskPriority.NORMAL
    """Ticket priority."""
    
    type: ZendeskType = ZendeskType.INCIDENT
    """Ticket type."""
    
    assignee_id: Optional[int] = None
    """Assignee ID."""
    
    group_id: Optional[int] = None
    """Group ID."""
    
    organization_id: Optional[int] = None
    """Organization ID."""
    
    tags: List[str] = field(default_factory=list)
    """Tags."""
    
    custom_fields: List[Dict[str, Any]] = field(default_factory=list)
    """Custom fields."""
    
    due_at: Optional[datetime] = None
    """Due date."""
    
    created_at: Optional[datetime] = None
    """Created at."""
    
    updated_at: Optional[datetime] = None
    """Updated at."""
    
    solved_at: Optional[datetime] = None
    """Solved at."""
    
    closed_at: Optional[datetime] = None
    """Closed at."""
    
    external_id: Optional[str] = None
    """External ID."""
    
    url: Optional[str] = None
    """Ticket URL."""
    
    has_incidents: bool = False
    """Has incidents."""
    
    is_public: bool = True
    """Is public."""
    
    submitter_id: Optional[int] = None
    """Submitter ID."""
    
    collaborator_ids: List[int] = field(default_factory=list)
    """Collaborator IDs."""
    
    follower_ids: List[int] = field(default_factory=list)
    """Follower IDs."""
    
    email_cc_ids: List[int] = field(default_factory=list)
    """Email CC IDs."""
    
    forum_topic_id: Optional[int] = None
    """Forum topic ID."""
    
    problem_id: Optional[int] = None
    """Problem ID."""
    
    ticket_form_id: Optional[int] = None
    """Ticket form ID."""
    
    brand_id: Optional[int] = None
    """Brand ID."""
    
    satisfaction_rating: Optional[Dict[str, Any]] = None
    """Satisfaction rating."""
    
    sharing_agreement_ids: List[int] = field(default_factory=list)
    """Sharing agreement IDs."""
    
    followup_ids: List[int] = field(default_factory=list)
    """Followup IDs."""
    
    via: Optional[Dict[str, Any]] = None
    """Via information."""
    
    macro_ids: List[int] = field(default_factory=list)
    """Macro IDs."""
    
    ticket_audit_id: Optional[int] = None
    """Ticket audit ID."""


@dataclass
class ZendeskUser:
    """Zendesk user data structure."""
    
    name: str
    """User name."""
    
    email: str
    """User email."""
    
    id: Optional[int] = None
    """User ID."""
    
    role: ZendeskUserRole = ZendeskUserRole.END_USER
    """User role."""
    
    active: bool = True
    """Active status."""
    
    verified: bool = False
    """Verified status."""
    
    shared: bool = False
    """Shared status."""
    
    locale_id: Optional[int] = None
    """Locale ID."""
    
    time_zone: Optional[str] = None
    """Time zone."""
    
    phone: Optional[str] = None
    """Phone number."""
    
    signature: Optional[str] = None
    """Signature."""
    
    details: Optional[str] = None
    """Details."""
    
    notes: Optional[str] = None
    """Notes."""
    
    organization_id: Optional[int] = None
    """Organization ID."""
    
    external_id: Optional[str] = None
    """External ID."""
    
    tags: List[str] = field(default_factory=list)
    """Tags."""
    
    alias: Optional[str] = None
    """Alias."""
    
    moderator: bool = False
    """Moderator status."""
    
    only_private_comments: bool = False
    """Only private comments."""
    
    restricted_agent: bool = False
    """Restricted agent."""
    
    suspended: bool = False
    """Suspended status."""
    
    created_at: Optional[datetime] = None
    """Created at."""
    
    updated_at: Optional[datetime] = None
    """Updated at."""
    
    last_login_at: Optional[datetime] = None
    """Last login at."""
    
    custom_role_id: Optional[int] = None
    """Custom role ID."""
    
    two_factor_auth_enabled: bool = False
    """Two factor auth enabled."""
    
    user_fields: Dict[str, Any] = field(default_factory=dict)
    """User fields."""


@dataclass
class ZendeskComment:
    """Zendesk comment data structure."""
    
    body: str
    """Comment body."""
    
    author_id: int
    """Author ID."""
    
    id: Optional[int] = None
    """Comment ID."""
    
    type: str = "comment"
    """Comment type."""
    
    html_body: Optional[str] = None
    """HTML body."""
    
    plain_body: Optional[str] = None
    """Plain body."""
    
    public: bool = True
    """Public status."""
    
    created_at: Optional[datetime] = None
    """Created at."""
    
    updated_at: Optional[datetime] = None
    """Updated at."""
    
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    """Attachments."""
    
    via: Optional[Dict[str, Any]] = None
    """Via information."""
    
    metadata: Optional[Dict[str, Any]] = None
    """Metadata."""
    
    uploads: List[str] = field(default_factory=list)
    """Uploads."""


@dataclass
class ZendeskOrganization:
    """Zendesk organization data structure."""
    
    name: str
    """Organization name."""
    
    id: Optional[int] = None
    """Organization ID."""
    
    external_id: Optional[str] = None
    """External ID."""
    
    domain_names: List[str] = field(default_factory=list)
    """Domain names."""
    
    shared_tickets: bool = False
    """Shared tickets."""
    
    shared_comments: bool = False
    """Shared comments."""
    
    group_id: Optional[int] = None
    """Group ID."""
    
    tags: List[str] = field(default_factory=list)
    """Tags."""
    
    notes: Optional[str] = None
    """Notes."""
    
    created_at: Optional[datetime] = None
    """Created at."""
    
    updated_at: Optional[datetime] = None
    """Updated at."""
    
    organization_fields: Dict[str, Any] = field(default_factory=dict)
    """Organization fields."""


@dataclass
class ZendeskGroup:
    """Zendesk group data structure."""
    
    name: str
    """Group name."""
    
    id: Optional[int] = None
    """Group ID."""
    
    description: Optional[str] = None
    """Description."""
    
    is_public: bool = True
    """Is public."""
    
    created_at: Optional[datetime] = None
    """Created at."""
    
    updated_at: Optional[datetime] = None
    """Updated at."""


class ZendeskIntegration:
    """Zendesk integration for customer support and helpdesk automation."""
    
    def __init__(self, config: ZendeskConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.verify_ssl
        
        # Set up authentication
        auth_string = f"{config.email}/token:{config.api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        self.session.headers.update({
            "Authorization": f"Basic {auth_b64}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        
        self.base_url = f"https://{config.subdomain}.zendesk.com/api/{config.api_version}"
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the Zendesk API."""
        try:
            url = f"{self.base_url}/{endpoint}"
            
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
            
            if response.content:
                return response.json()
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to make {method} request to {endpoint}: {e}")
            raise
    
    async def create_ticket(self, ticket: ZendeskTicket) -> ZendeskTicket:
        """
        Create a new ticket.
        
        Args:
            ticket: Ticket data
            
        Returns:
            Created ticket
        """
        try:
            data = {
                "ticket": {
                    "subject": ticket.subject,
                    "description": ticket.description,
                    "status": ticket.status.value,
                    "priority": ticket.priority.value,
                    "type": ticket.type.value,
                    "requester_id": ticket.requester_id
                }
            }
            
            if ticket.assignee_id:
                data["ticket"]["assignee_id"] = ticket.assignee_id
            if ticket.group_id:
                data["ticket"]["group_id"] = ticket.group_id
            if ticket.organization_id:
                data["ticket"]["organization_id"] = ticket.organization_id
            if ticket.tags:
                data["ticket"]["tags"] = ticket.tags
            if ticket.custom_fields:
                data["ticket"]["custom_fields"] = ticket.custom_fields
            if ticket.due_at:
                data["ticket"]["due_at"] = ticket.due_at.isoformat()
            if ticket.external_id:
                data["ticket"]["external_id"] = ticket.external_id
            if ticket.submitter_id:
                data["ticket"]["submitter_id"] = ticket.submitter_id
            if ticket.collaborator_ids:
                data["ticket"]["collaborator_ids"] = ticket.collaborator_ids
            if ticket.follower_ids:
                data["ticket"]["follower_ids"] = ticket.follower_ids
            if ticket.email_cc_ids:
                data["ticket"]["email_cc_ids"] = ticket.email_cc_ids
            if ticket.forum_topic_id:
                data["ticket"]["forum_topic_id"] = ticket.forum_topic_id
            if ticket.problem_id:
                data["ticket"]["problem_id"] = ticket.problem_id
            if ticket.ticket_form_id:
                data["ticket"]["ticket_form_id"] = ticket.ticket_form_id
            if ticket.brand_id:
                data["ticket"]["brand_id"] = ticket.brand_id
            if ticket.sharing_agreement_ids:
                data["ticket"]["sharing_agreement_ids"] = ticket.sharing_agreement_ids
            if ticket.followup_ids:
                data["ticket"]["followup_ids"] = ticket.followup_ids
            if ticket.via:
                data["ticket"]["via"] = ticket.via
            if ticket.macro_ids:
                data["ticket"]["macro_ids"] = ticket.macro_ids
            if ticket.ticket_audit_id:
                data["ticket"]["ticket_audit_id"] = ticket.ticket_audit_id
            
            result = self._make_request("POST", "tickets.json", data)
            
            ticket_data = result["ticket"]
            ticket.id = ticket_data["id"]
            ticket.url = ticket_data["url"]
            ticket.created_at = datetime.fromisoformat(ticket_data["created_at"].replace("Z", "+00:00"))
            ticket.updated_at = datetime.fromisoformat(ticket_data["updated_at"].replace("Z", "+00:00"))
            
            self.logger.info(f"Created Zendesk ticket: {ticket.id}")
            return ticket
            
        except Exception as e:
            self.logger.error(f"Failed to create ticket: {e}")
            raise
    
    async def get_ticket(self, ticket_id: int) -> ZendeskTicket:
        """
        Get a ticket by ID.
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            Ticket data
        """
        try:
            result = self._make_request("GET", f"tickets/{ticket_id}.json")
            
            ticket_data = result["ticket"]
            
            return ZendeskTicket(
                id=ticket_data["id"],
                subject=ticket_data["subject"],
                description=ticket_data["description"],
                status=ZendeskStatus(ticket_data["status"]),
                priority=ZendeskPriority(ticket_data["priority"]),
                type=ZendeskType(ticket_data["type"]),
                requester_id=ticket_data["requester_id"],
                assignee_id=ticket_data.get("assignee_id"),
                group_id=ticket_data.get("group_id"),
                organization_id=ticket_data.get("organization_id"),
                tags=ticket_data.get("tags", []),
                custom_fields=ticket_data.get("custom_fields", []),
                due_at=datetime.fromisoformat(ticket_data["due_at"].replace("Z", "+00:00")) if ticket_data.get("due_at") else None,
                created_at=datetime.fromisoformat(ticket_data["created_at"].replace("Z", "+00:00")) if ticket_data.get("created_at") else None,
                updated_at=datetime.fromisoformat(ticket_data["updated_at"].replace("Z", "+00:00")) if ticket_data.get("updated_at") else None,
                solved_at=datetime.fromisoformat(ticket_data["solved_at"].replace("Z", "+00:00")) if ticket_data.get("solved_at") else None,
                closed_at=datetime.fromisoformat(ticket_data["closed_at"].replace("Z", "+00:00")) if ticket_data.get("closed_at") else None,
                external_id=ticket_data.get("external_id"),
                url=ticket_data.get("url"),
                has_incidents=ticket_data.get("has_incidents", False),
                is_public=ticket_data.get("is_public", True),
                submitter_id=ticket_data.get("submitter_id"),
                collaborator_ids=ticket_data.get("collaborator_ids", []),
                follower_ids=ticket_data.get("follower_ids", []),
                email_cc_ids=ticket_data.get("email_cc_ids", []),
                forum_topic_id=ticket_data.get("forum_topic_id"),
                problem_id=ticket_data.get("problem_id"),
                ticket_form_id=ticket_data.get("ticket_form_id"),
                brand_id=ticket_data.get("brand_id"),
                satisfaction_rating=ticket_data.get("satisfaction_rating"),
                sharing_agreement_ids=ticket_data.get("sharing_agreement_ids", []),
                followup_ids=ticket_data.get("followup_ids", []),
                via=ticket_data.get("via"),
                macro_ids=ticket_data.get("macro_ids", []),
                ticket_audit_id=ticket_data.get("ticket_audit_id")
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get ticket: {e}")
            raise
    
    async def update_ticket(self, ticket_id: int, updates: Dict[str, Any]) -> ZendeskTicket:
        """
        Update a ticket.
        
        Args:
            ticket_id: Ticket ID
            updates: Update data
            
        Returns:
            Updated ticket
        """
        try:
            data = {"ticket": updates}
            self._make_request("PUT", f"tickets/{ticket_id}.json", data)
            
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
            self._make_request("DELETE", f"tickets/{ticket_id}.json")
            self.logger.info(f"Deleted Zendesk ticket: {ticket_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete ticket: {e}")
            raise
    
    async def get_tickets(self, filters: Optional[Dict[str, Any]] = None, page: int = 1, per_page: int = 100) -> List[ZendeskTicket]:
        """
        Get tickets with optional filters.
        
        Args:
            filters: Filter parameters
            page: Page number
            per_page: Results per page
            
        Returns:
            List of tickets
        """
        try:
            params = {
                "page": page,
                "per_page": per_page
            }
            
            if filters:
                params.update(filters)
            
            result = self._make_request("GET", "tickets.json", params=params)
            
            tickets = []
            for ticket_data in result["tickets"]:
                ticket = ZendeskTicket(
                    id=ticket_data["id"],
                    subject=ticket_data["subject"],
                    description=ticket_data["description"],
                    status=ZendeskStatus(ticket_data["status"]),
                    priority=ZendeskPriority(ticket_data["priority"]),
                    type=ZendeskType(ticket_data["type"]),
                    requester_id=ticket_data["requester_id"],
                    assignee_id=ticket_data.get("assignee_id"),
                    group_id=ticket_data.get("group_id"),
                    organization_id=ticket_data.get("organization_id"),
                    tags=ticket_data.get("tags", []),
                    custom_fields=ticket_data.get("custom_fields", []),
                    due_at=datetime.fromisoformat(ticket_data["due_at"].replace("Z", "+00:00")) if ticket_data.get("due_at") else None,
                    created_at=datetime.fromisoformat(ticket_data["created_at"].replace("Z", "+00:00")) if ticket_data.get("created_at") else None,
                    updated_at=datetime.fromisoformat(ticket_data["updated_at"].replace("Z", "+00:00")) if ticket_data.get("updated_at") else None,
                    solved_at=datetime.fromisoformat(ticket_data["solved_at"].replace("Z", "+00:00")) if ticket_data.get("solved_at") else None,
                    closed_at=datetime.fromisoformat(ticket_data["closed_at"].replace("Z", "+00:00")) if ticket_data.get("closed_at") else None,
                    external_id=ticket_data.get("external_id"),
                    url=ticket_data.get("url"),
                    has_incidents=ticket_data.get("has_incidents", False),
                    is_public=ticket_data.get("is_public", True),
                    submitter_id=ticket_data.get("submitter_id"),
                    collaborator_ids=ticket_data.get("collaborator_ids", []),
                    follower_ids=ticket_data.get("follower_ids", []),
                    email_cc_ids=ticket_data.get("email_cc_ids", []),
                    forum_topic_id=ticket_data.get("forum_topic_id"),
                    problem_id=ticket_data.get("problem_id"),
                    ticket_form_id=ticket_data.get("ticket_form_id"),
                    brand_id=ticket_data.get("brand_id"),
                    satisfaction_rating=ticket_data.get("satisfaction_rating"),
                    sharing_agreement_ids=ticket_data.get("sharing_agreement_ids", []),
                    followup_ids=ticket_data.get("followup_ids", []),
                    via=ticket_data.get("via"),
                    macro_ids=ticket_data.get("macro_ids", []),
                    ticket_audit_id=ticket_data.get("ticket_audit_id")
                )
                tickets.append(ticket)
            
            return tickets
            
        except Exception as e:
            self.logger.error(f"Failed to get tickets: {e}")
            raise
    
    async def add_comment_to_ticket(self, ticket_id: int, comment: ZendeskComment) -> ZendeskComment:
        """
        Add a comment to a ticket.
        
        Args:
            ticket_id: Ticket ID
            comment: Comment data
            
        Returns:
            Created comment
        """
        try:
            data = {
                "ticket": {
                    "comment": {
                        "body": comment.body,
                        "public": comment.public,
                        "author_id": comment.author_id
                    }
                }
            }
            
            if comment.html_body:
                data["ticket"]["comment"]["html_body"] = comment.html_body
            if comment.plain_body:
                data["ticket"]["comment"]["plain_body"] = comment.plain_body
            if comment.attachments:
                data["ticket"]["comment"]["attachments"] = comment.attachments
            if comment.via:
                data["ticket"]["comment"]["via"] = comment.via
            if comment.metadata:
                data["ticket"]["comment"]["metadata"] = comment.metadata
            if comment.uploads:
                data["ticket"]["comment"]["uploads"] = comment.uploads
            
            result = self._make_request("PUT", f"tickets/{ticket_id}.json", data)
            
            comment_data = result["ticket"]["comment"]
            comment.id = comment_data["id"]
            comment.created_at = datetime.fromisoformat(comment_data["created_at"].replace("Z", "+00:00"))
            comment.updated_at = datetime.fromisoformat(comment_data["updated_at"].replace("Z", "+00:00"))
            
            self.logger.info(f"Added comment to ticket {ticket_id}: {comment.id}")
            return comment
            
        except Exception as e:
            self.logger.error(f"Failed to add comment to ticket: {e}")
            raise
    
    async def get_ticket_comments(self, ticket_id: int) -> List[ZendeskComment]:
        """
        Get comments for a ticket.
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            List of comments
        """
        try:
            result = self._make_request("GET", f"tickets/{ticket_id}/comments.json")
            
            comments = []
            for comment_data in result["comments"]:
                comment = ZendeskComment(
                    id=comment_data["id"],
                    type=comment_data["type"],
                    body=comment_data["body"],
                    html_body=comment_data.get("html_body"),
                    plain_body=comment_data.get("plain_body"),
                    public=comment_data.get("public", True),
                    author_id=comment_data["author_id"],
                    created_at=datetime.fromisoformat(comment_data["created_at"].replace("Z", "+00:00")) if comment_data.get("created_at") else None,
                    updated_at=datetime.fromisoformat(comment_data["updated_at"].replace("Z", "+00:00")) if comment_data.get("updated_at") else None,
                    attachments=comment_data.get("attachments", []),
                    via=comment_data.get("via"),
                    metadata=comment_data.get("metadata"),
                    uploads=comment_data.get("uploads", [])
                )
                comments.append(comment)
            
            return comments
            
        except Exception as e:
            self.logger.error(f"Failed to get ticket comments: {e}")
            raise
    
    async def create_user(self, user: ZendeskUser) -> ZendeskUser:
        """
        Create a new user.
        
        Args:
            user: User data
            
        Returns:
            Created user
        """
        try:
            data = {
                "user": {
                    "name": user.name,
                    "email": user.email,
                    "role": user.role.value,
                    "active": user.active,
                    "verified": user.verified,
                    "shared": user.shared
                }
            }
            
            if user.locale_id:
                data["user"]["locale_id"] = user.locale_id
            if user.time_zone:
                data["user"]["time_zone"] = user.time_zone
            if user.phone:
                data["user"]["phone"] = user.phone
            if user.signature:
                data["user"]["signature"] = user.signature
            if user.details:
                data["user"]["details"] = user.details
            if user.notes:
                data["user"]["notes"] = user.notes
            if user.organization_id:
                data["user"]["organization_id"] = user.organization_id
            if user.external_id:
                data["user"]["external_id"] = user.external_id
            if user.tags:
                data["user"]["tags"] = user.tags
            if user.alias:
                data["user"]["alias"] = user.alias
            if user.moderator:
                data["user"]["moderator"] = user.moderator
            if user.only_private_comments:
                data["user"]["only_private_comments"] = user.only_private_comments
            if user.restricted_agent:
                data["user"]["restricted_agent"] = user.restricted_agent
            if user.suspended:
                data["user"]["suspended"] = user.suspended
            if user.custom_role_id:
                data["user"]["custom_role_id"] = user.custom_role_id
            if user.two_factor_auth_enabled:
                data["user"]["two_factor_auth_enabled"] = user.two_factor_auth_enabled
            if user.user_fields:
                data["user"]["user_fields"] = user.user_fields
            
            result = self._make_request("POST", "users.json", data)
            
            user_data = result["user"]
            user.id = user_data["id"]
            user.created_at = datetime.fromisoformat(user_data["created_at"].replace("Z", "+00:00"))
            user.updated_at = datetime.fromisoformat(user_data["updated_at"].replace("Z", "+00:00"))
            user.last_login_at = datetime.fromisoformat(user_data["last_login_at"].replace("Z", "+00:00")) if user_data.get("last_login_at") else None
            
            self.logger.info(f"Created Zendesk user: {user.id}")
            return user
            
        except Exception as e:
            self.logger.error(f"Failed to create user: {e}")
            raise
    
    async def get_user(self, user_id: int) -> ZendeskUser:
        """
        Get a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User data
        """
        try:
            result = self._make_request("GET", f"users/{user_id}.json")
            
            user_data = result["user"]
            
            return ZendeskUser(
                id=user_data["id"],
                name=user_data["name"],
                email=user_data["email"],
                role=ZendeskUserRole(user_data["role"]),
                active=user_data.get("active", True),
                verified=user_data.get("verified", False),
                shared=user_data.get("shared", False),
                locale_id=user_data.get("locale_id"),
                time_zone=user_data.get("time_zone"),
                phone=user_data.get("phone"),
                signature=user_data.get("signature"),
                details=user_data.get("details"),
                notes=user_data.get("notes"),
                organization_id=user_data.get("organization_id"),
                external_id=user_data.get("external_id"),
                tags=user_data.get("tags", []),
                alias=user_data.get("alias"),
                moderator=user_data.get("moderator", False),
                only_private_comments=user_data.get("only_private_comments", False),
                restricted_agent=user_data.get("restricted_agent", False),
                suspended=user_data.get("suspended", False),
                created_at=datetime.fromisoformat(user_data["created_at"].replace("Z", "+00:00")) if user_data.get("created_at") else None,
                updated_at=datetime.fromisoformat(user_data["updated_at"].replace("Z", "+00:00")) if user_data.get("updated_at") else None,
                last_login_at=datetime.fromisoformat(user_data["last_login_at"].replace("Z", "+00:00")) if user_data.get("last_login_at") else None,
                custom_role_id=user_data.get("custom_role_id"),
                two_factor_auth_enabled=user_data.get("two_factor_auth_enabled", False),
                user_fields=user_data.get("user_fields", {})
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get user: {e}")
            raise
    
    async def search_users(self, query: str, page: int = 1, per_page: int = 100) -> List[ZendeskUser]:
        """
        Search users.
        
        Args:
            query: Search query
            page: Page number
            per_page: Results per page
            
        Returns:
            List of users
        """
        try:
            params = {
                "query": query,
                "page": page,
                "per_page": per_page
            }
            
            result = self._make_request("GET", "users/search.json", params=params)
            
            users = []
            for user_data in result["users"]:
                user = ZendeskUser(
                    id=user_data["id"],
                    name=user_data["name"],
                    email=user_data["email"],
                    role=ZendeskUserRole(user_data["role"]),
                    active=user_data.get("active", True),
                    verified=user_data.get("verified", False),
                    shared=user_data.get("shared", False),
                    locale_id=user_data.get("locale_id"),
                    time_zone=user_data.get("time_zone"),
                    phone=user_data.get("phone"),
                    signature=user_data.get("signature"),
                    details=user_data.get("details"),
                    notes=user_data.get("notes"),
                    organization_id=user_data.get("organization_id"),
                    external_id=user_data.get("external_id"),
                    tags=user_data.get("tags", []),
                    alias=user_data.get("alias"),
                    moderator=user_data.get("moderator", False),
                    only_private_comments=user_data.get("only_private_comments", False),
                    restricted_agent=user_data.get("restricted_agent", False),
                    suspended=user_data.get("suspended", False),
                    created_at=datetime.fromisoformat(user_data["created_at"].replace("Z", "+00:00")) if user_data.get("created_at") else None,
                    updated_at=datetime.fromisoformat(user_data["updated_at"].replace("Z", "+00:00")) if user_data.get("updated_at") else None,
                    last_login_at=datetime.fromisoformat(user_data["last_login_at"].replace("Z", "+00:00")) if user_data.get("last_login_at") else None,
                    custom_role_id=user_data.get("custom_role_id"),
                    two_factor_auth_enabled=user_data.get("two_factor_auth_enabled", False),
                    user_fields=user_data.get("user_fields", {})
                )
                users.append(user)
            
            return users
            
        except Exception as e:
            self.logger.error(f"Failed to search users: {e}")
            raise
    
    async def create_organization(self, organization: ZendeskOrganization) -> ZendeskOrganization:
        """
        Create a new organization.
        
        Args:
            organization: Organization data
            
        Returns:
            Created organization
        """
        try:
            data = {
                "organization": {
                    "name": organization.name,
                    "external_id": organization.external_id,
                    "domain_names": organization.domain_names,
                    "shared_tickets": organization.shared_tickets,
                    "shared_comments": organization.shared_comments
                }
            }
            
            if organization.group_id:
                data["organization"]["group_id"] = organization.group_id
            if organization.tags:
                data["organization"]["tags"] = organization.tags
            if organization.notes:
                data["organization"]["notes"] = organization.notes
            if organization.organization_fields:
                data["organization"]["organization_fields"] = organization.organization_fields
            
            result = self._make_request("POST", "organizations.json", data)
            
            org_data = result["organization"]
            organization.id = org_data["id"]
            organization.created_at = datetime.fromisoformat(org_data["created_at"].replace("Z", "+00:00"))
            organization.updated_at = datetime.fromisoformat(org_data["updated_at"].replace("Z", "+00:00"))
            
            self.logger.info(f"Created Zendesk organization: {organization.id}")
            return organization
            
        except Exception as e:
            self.logger.error(f"Failed to create organization: {e}")
            raise
    
    async def get_organization(self, organization_id: int) -> ZendeskOrganization:
        """
        Get an organization by ID.
        
        Args:
            organization_id: Organization ID
            
        Returns:
            Organization data
        """
        try:
            result = self._make_request("GET", f"organizations/{organization_id}.json")
            
            org_data = result["organization"]
            
            return ZendeskOrganization(
                id=org_data["id"],
                name=org_data["name"],
                external_id=org_data.get("external_id"),
                domain_names=org_data.get("domain_names", []),
                shared_tickets=org_data.get("shared_tickets", False),
                shared_comments=org_data.get("shared_comments", False),
                group_id=org_data.get("group_id"),
                tags=org_data.get("tags", []),
                notes=org_data.get("notes"),
                created_at=datetime.fromisoformat(org_data["created_at"].replace("Z", "+00:00")) if org_data.get("created_at") else None,
                updated_at=datetime.fromisoformat(org_data["updated_at"].replace("Z", "+00:00")) if org_data.get("updated_at") else None,
                organization_fields=org_data.get("organization_fields", {})
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get organization: {e}")
            raise
    
    async def get_groups(self, page: int = 1, per_page: int = 100) -> List[ZendeskGroup]:
        """
        Get groups.
        
        Args:
            page: Page number
            per_page: Results per page
            
        Returns:
            List of groups
        """
        try:
            params = {
                "page": page,
                "per_page": per_page
            }
            
            result = self._make_request("GET", "groups.json", params=params)
            
            groups = []
            for group_data in result["groups"]:
                group = ZendeskGroup(
                    id=group_data["id"],
                    name=group_data["name"],
                    description=group_data.get("description"),
                    is_public=group_data.get("is_public", True),
                    created_at=datetime.fromisoformat(group_data["created_at"].replace("Z", "+00:00")) if group_data.get("created_at") else None,
                    updated_at=datetime.fromisoformat(group_data["updated_at"].replace("Z", "+00:00")) if group_data.get("updated_at") else None
                )
                groups.append(group)
            
            return groups
            
        except Exception as e:
            self.logger.error(f"Failed to get groups: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Zendesk integration.
        
        Returns:
            Health check results
        """
        try:
            # Test API connectivity by getting a single ticket
            params = {"per_page": 1}
            result = self._make_request("GET", "tickets.json", params=params)
            
            return {
                "status": "healthy",
                "subdomain": self.config.subdomain,
                "api_version": self.config.api_version,
                "total_tickets": len(result.get("tickets", [])),
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

