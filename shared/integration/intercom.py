"""
Intercom Integration Module

This module provides integration with Intercom for customer messaging, support automation,
and customer relationship management with comprehensive API support.
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
    INTERCOM_AVAILABLE = True
except ImportError:
    INTERCOM_AVAILABLE = False
    logging.warning("Intercom APIs not available. Install requests")

logger = logging.getLogger(__name__)


class IntercomMessageType(Enum):
    """Intercom message types."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WHATSAPP = "whatsapp"
    MESSENGER = "messenger"
    SLACK = "slack"


class IntercomConversationState(Enum):
    """Intercom conversation states."""
    OPEN = "open"
    CLOSED = "closed"
    PENDING = "pending"


class IntercomContactType(Enum):
    """Intercom contact types."""
    USER = "user"
    LEAD = "lead"


class IntercomEventType(Enum):
    """Intercom event types."""
    CUSTOM = "custom"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    CONVERSATION_CREATED = "conversation.created"
    CONVERSATION_REPLIED = "conversation.replied"
    CONVERSATION_CLOSED = "conversation.closed"


@dataclass
class IntercomConfig:
    """Configuration for Intercom integration."""
    
    access_token: str
    """Intercom access token."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    verify_ssl: bool = True
    """Verify SSL certificates."""
    
    webhook_secret: Optional[str] = None
    """Webhook secret for verification."""


@dataclass
class IntercomContact:
    """Intercom contact data structure."""
    
    id: Optional[str] = None
    """Contact ID."""
    
    type: IntercomContactType = IntercomContactType.USER
    """Contact type."""
    
    email: Optional[str] = None
    """Contact email."""
    
    phone: Optional[str] = None
    """Contact phone number."""
    
    name: Optional[str] = None
    """Contact name."""
    
    user_id: Optional[str] = None
    """User ID."""
    
    external_id: Optional[str] = None
    """External ID."""
    
    avatar: Optional[str] = None
    """Avatar URL."""
    
    location_data: Optional[Dict[str, Any]] = None
    """Location data."""
    
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    """Custom attributes."""
    
    tags: Dict[str, Any] = field(default_factory=dict)
    """Tags."""
    
    companies: Dict[str, Any] = field(default_factory=dict)
    """Companies."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class IntercomConversation:
    """Intercom conversation data structure."""
    
    id: Optional[str] = None
    """Conversation ID."""
    
    type: str = "conversation"
    """Conversation type."""
    
    state: IntercomConversationState = IntercomConversationState.OPEN
    """Conversation state."""
    
    read: bool = False
    """Is read."""
    
    waiting_since: Optional[datetime] = None
    """Waiting since timestamp."""
    
    snoozed_until: Optional[datetime] = None
    """Snoozed until timestamp."""
    
    conversation_rating: Optional[Dict[str, Any]] = None
    """Conversation rating."""
    
    source: Optional[Dict[str, Any]] = None
    """Source information."""
    
    contacts: List[Dict[str, Any]] = field(default_factory=list)
    """Contacts in conversation."""
    
    teammates: List[Dict[str, Any]] = field(default_factory=list)
    """Teammates in conversation."""
    
    title: Optional[str] = None
    """Conversation title."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class IntercomMessage:
    """Intercom message data structure."""
    
    id: Optional[str] = None
    """Message ID."""
    
    type: str = "message"
    """Message type."""
    
    message_type: IntercomMessageType = IntercomMessageType.EMAIL
    """Message type."""
    
    subject: Optional[str] = None
    """Message subject."""
    
    body: str
    """Message body."""
    
    template: Optional[str] = None
    """Template ID."""
    
    from_field: Optional[Dict[str, Any]] = None
    """From field."""
    
    to_field: Optional[Dict[str, Any]] = None
    """To field."""
    
    delivered_as: Optional[str] = None
    """Delivered as."""
    
    conversation_id: Optional[str] = None
    """Conversation ID."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class IntercomEvent:
    """Intercom event data structure."""
    
    id: Optional[str] = None
    """Event ID."""
    
    event_name: str
    """Event name."""
    
    event_type: IntercomEventType = IntercomEventType.CUSTOM
    """Event type."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    user_id: Optional[str] = None
    """User ID."""
    
    email: Optional[str] = None
    """Email."""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Event metadata."""


@dataclass
class IntercomTag:
    """Intercom tag data structure."""
    
    id: Optional[str] = None
    """Tag ID."""
    
    name: str
    """Tag name."""
    
    applied_count: int = 0
    """Applied count."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class IntercomCompany:
    """Intercom company data structure."""
    
    id: Optional[str] = None
    """Company ID."""
    
    name: str
    """Company name."""
    
    company_id: Optional[str] = None
    """Company ID."""
    
    plan: Optional[str] = None
    """Plan."""
    
    size: Optional[int] = None
    """Size."""
    
    website: Optional[str] = None
    """Website."""
    
    industry: Optional[str] = None
    """Industry."""
    
    monthly_spend: Optional[int] = None
    """Monthly spend."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


class IntercomIntegration:
    """Intercom integration for customer messaging and support automation."""
    
    def __init__(self, config: IntercomConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.verify_ssl
        
        # Set up authentication
        self.session.headers.update({
            "Authorization": f"Bearer {config.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        
        self.base_url = "https://api.intercom.io"
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the Intercom API."""
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
    
    async def create_contact(self, contact: IntercomContact) -> IntercomContact:
        """
        Create a new contact.
        
        Args:
            contact: Contact data
            
        Returns:
            Created contact
        """
        try:
            data = {
                "role": contact.type.value
            }
            
            if contact.email:
                data["email"] = contact.email
            if contact.phone:
                data["phone"] = contact.phone
            if contact.name:
                data["name"] = contact.name
            if contact.user_id:
                data["user_id"] = contact.user_id
            if contact.external_id:
                data["external_id"] = contact.external_id
            if contact.avatar:
                data["avatar"] = contact.avatar
            if contact.location_data:
                data["location_data"] = contact.location_data
            if contact.custom_attributes:
                data["custom_attributes"] = contact.custom_attributes
            if contact.tags:
                data["tags"] = contact.tags
            if contact.companies:
                data["companies"] = contact.companies
            
            result = self._make_request("POST", "contacts", data)
            
            contact.id = result["id"]
            contact.created_at = datetime.fromtimestamp(result["created_at"])
            contact.updated_at = datetime.fromtimestamp(result["updated_at"])
            
            self.logger.info(f"Created Intercom contact: {contact.id}")
            return contact
            
        except Exception as e:
            self.logger.error(f"Failed to create contact: {e}")
            raise
    
    async def get_contact(self, contact_id: str) -> IntercomContact:
        """
        Get a contact by ID.
        
        Args:
            contact_id: Contact ID
            
        Returns:
            Contact data
        """
        try:
            result = self._make_request("GET", f"contacts/{contact_id}")
            
            return IntercomContact(
                id=result["id"],
                type=IntercomContactType(result["role"]),
                email=result.get("email"),
                phone=result.get("phone"),
                name=result.get("name"),
                user_id=result.get("user_id"),
                external_id=result.get("external_id"),
                avatar=result.get("avatar"),
                location_data=result.get("location_data"),
                custom_attributes=result.get("custom_attributes", {}),
                tags=result.get("tags", {}),
                companies=result.get("companies", {}),
                created_at=datetime.fromtimestamp(result["created_at"]),
                updated_at=datetime.fromtimestamp(result["updated_at"])
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get contact: {e}")
            raise
    
    async def update_contact(self, contact_id: str, updates: Dict[str, Any]) -> IntercomContact:
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
    
    async def delete_contact(self, contact_id: str) -> bool:
        """
        Delete a contact.
        
        Args:
            contact_id: Contact ID
            
        Returns:
            Success status
        """
        try:
            self._make_request("DELETE", f"contacts/{contact_id}")
            self.logger.info(f"Deleted Intercom contact: {contact_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete contact: {e}")
            raise
    
    async def search_contacts(self, query: str) -> List[IntercomContact]:
        """
        Search contacts.
        
        Args:
            query: Search query
            
        Returns:
            List of contacts
        """
        try:
            data = {
                "query": query
            }
            
            result = self._make_request("POST", "contacts/search", data)
            
            contacts = []
            for item in result.get("data", []):
                contact = IntercomContact(
                    id=item["id"],
                    type=IntercomContactType(item["role"]),
                    email=item.get("email"),
                    phone=item.get("phone"),
                    name=item.get("name"),
                    user_id=item.get("user_id"),
                    external_id=item.get("external_id"),
                    avatar=item.get("avatar"),
                    location_data=item.get("location_data"),
                    custom_attributes=item.get("custom_attributes", {}),
                    tags=item.get("tags", {}),
                    companies=item.get("companies", {}),
                    created_at=datetime.fromtimestamp(item["created_at"]),
                    updated_at=datetime.fromtimestamp(item["updated_at"])
                )
                contacts.append(contact)
            
            return contacts
            
        except Exception as e:
            self.logger.error(f"Failed to search contacts: {e}")
            raise
    
    async def create_conversation(self, conversation: IntercomConversation) -> IntercomConversation:
        """
        Create a new conversation.
        
        Args:
            conversation: Conversation data
            
        Returns:
            Created conversation
        """
        try:
            data = {
                "message_type": "comment",
                "type": "user",
                "body": conversation.title or "New conversation"
            }
            
            if conversation.contacts:
                data["from"] = conversation.contacts[0]
            
            result = self._make_request("POST", "conversations", data)
            
            conversation.id = result["id"]
            conversation.created_at = datetime.fromtimestamp(result["created_at"])
            conversation.updated_at = datetime.fromtimestamp(result["updated_at"])
            
            self.logger.info(f"Created Intercom conversation: {conversation.id}")
            return conversation
            
        except Exception as e:
            self.logger.error(f"Failed to create conversation: {e}")
            raise
    
    async def get_conversation(self, conversation_id: str) -> IntercomConversation:
        """
        Get a conversation by ID.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation data
        """
        try:
            result = self._make_request("GET", f"conversations/{conversation_id}")
            
            return IntercomConversation(
                id=result["id"],
                type=result["type"],
                state=IntercomConversationState(result["state"]),
                read=result.get("read", False),
                waiting_since=datetime.fromtimestamp(result["waiting_since"]) if result.get("waiting_since") else None,
                snoozed_until=datetime.fromtimestamp(result["snoozed_until"]) if result.get("snoozed_until") else None,
                conversation_rating=result.get("conversation_rating"),
                source=result.get("source"),
                contacts=result.get("contacts", []),
                teammates=result.get("teammates", []),
                title=result.get("title"),
                created_at=datetime.fromtimestamp(result["created_at"]),
                updated_at=datetime.fromtimestamp(result["updated_at"])
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get conversation: {e}")
            raise
    
    async def reply_to_conversation(self, conversation_id: str, message: IntercomMessage) -> IntercomMessage:
        """
        Reply to a conversation.
        
        Args:
            conversation_id: Conversation ID
            message: Message data
            
        Returns:
            Created message
        """
        try:
            data = {
                "message_type": message.message_type.value,
                "type": "admin",
                "body": message.body
            }
            
            if message.subject:
                data["subject"] = message.subject
            if message.template:
                data["template"] = message.template
            if message.from_field:
                data["from"] = message.from_field
            if message.to_field:
                data["to"] = message.to_field
            
            result = self._make_request("POST", f"conversations/{conversation_id}/reply", data)
            
            message.id = result["id"]
            message.conversation_id = conversation_id
            message.created_at = datetime.fromtimestamp(result["created_at"])
            message.updated_at = datetime.fromtimestamp(result["updated_at"])
            
            self.logger.info(f"Replied to conversation {conversation_id}: {message.id}")
            return message
            
        except Exception as e:
            self.logger.error(f"Failed to reply to conversation: {e}")
            raise
    
    async def close_conversation(self, conversation_id: str) -> bool:
        """
        Close a conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Success status
        """
        try:
            data = {
                "message_type": "comment",
                "type": "admin",
                "body": "Conversation closed"
            }
            
            self._make_request("POST", f"conversations/{conversation_id}/reply", data)
            self.logger.info(f"Closed Intercom conversation: {conversation_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to close conversation: {e}")
            raise
    
    async def send_message(self, message: IntercomMessage) -> IntercomMessage:
        """
        Send a message.
        
        Args:
            message: Message data
            
        Returns:
            Sent message
        """
        try:
            data = {
                "message_type": message.message_type.value,
                "type": "admin",
                "body": message.body
            }
            
            if message.subject:
                data["subject"] = message.subject
            if message.template:
                data["template"] = message.template
            if message.from_field:
                data["from"] = message.from_field
            if message.to_field:
                data["to"] = message.to_field
            if message.delivered_as:
                data["delivered_as"] = message.delivered_as
            
            result = self._make_request("POST", "messages", data)
            
            message.id = result["id"]
            message.created_at = datetime.fromtimestamp(result["created_at"])
            message.updated_at = datetime.fromtimestamp(result["updated_at"])
            
            self.logger.info(f"Sent Intercom message: {message.id}")
            return message
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            raise
    
    async def create_event(self, event: IntercomEvent) -> IntercomEvent:
        """
        Create an event.
        
        Args:
            event: Event data
            
        Returns:
            Created event
        """
        try:
            data = {
                "event_name": event.event_name,
                "created_at": int(event.created_at.timestamp()) if event.created_at else int(datetime.now().timestamp())
            }
            
            if event.user_id:
                data["user_id"] = event.user_id
            if event.email:
                data["email"] = event.email
            if event.metadata:
                data["metadata"] = event.metadata
            
            result = self._make_request("POST", "events", data)
            
            event.id = result["id"]
            event.created_at = datetime.fromtimestamp(result["created_at"])
            
            self.logger.info(f"Created Intercom event: {event.id}")
            return event
            
        except Exception as e:
            self.logger.error(f"Failed to create event: {e}")
            raise
    
    async def create_tag(self, tag: IntercomTag) -> IntercomTag:
        """
        Create a tag.
        
        Args:
            tag: Tag data
            
        Returns:
            Created tag
        """
        try:
            data = {
                "name": tag.name
            }
            
            result = self._make_request("POST", "tags", data)
            
            tag.id = result["id"]
            tag.applied_count = result.get("applied_count", 0)
            tag.created_at = datetime.fromtimestamp(result["created_at"])
            tag.updated_at = datetime.fromtimestamp(result["updated_at"])
            
            self.logger.info(f"Created Intercom tag: {tag.id}")
            return tag
            
        except Exception as e:
            self.logger.error(f"Failed to create tag: {e}")
            raise
    
    async def get_tags(self) -> List[IntercomTag]:
        """
        Get all tags.
        
        Returns:
            List of tags
        """
        try:
            result = self._make_request("GET", "tags")
            
            tags = []
            for item in result.get("tags", []):
                tag = IntercomTag(
                    id=item["id"],
                    name=item["name"],
                    applied_count=item.get("applied_count", 0),
                    created_at=datetime.fromtimestamp(item["created_at"]),
                    updated_at=datetime.fromtimestamp(item["updated_at"])
                )
                tags.append(tag)
            
            return tags
            
        except Exception as e:
            self.logger.error(f"Failed to get tags: {e}")
            raise
    
    async def tag_contact(self, contact_id: str, tag_id: str) -> bool:
        """
        Tag a contact.
        
        Args:
            contact_id: Contact ID
            tag_id: Tag ID
            
        Returns:
            Success status
        """
        try:
            data = {
                "id": tag_id
            }
            
            self._make_request("POST", f"contacts/{contact_id}/tags", data)
            self.logger.info(f"Tagged contact {contact_id} with tag {tag_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to tag contact: {e}")
            raise
    
    async def create_company(self, company: IntercomCompany) -> IntercomCompany:
        """
        Create a company.
        
        Args:
            company: Company data
            
        Returns:
            Created company
        """
        try:
            data = {
                "name": company.name
            }
            
            if company.company_id:
                data["company_id"] = company.company_id
            if company.plan:
                data["plan"] = company.plan
            if company.size:
                data["size"] = company.size
            if company.website:
                data["website"] = company.website
            if company.industry:
                data["industry"] = company.industry
            if company.monthly_spend:
                data["monthly_spend"] = company.monthly_spend
            
            result = self._make_request("POST", "companies", data)
            
            company.id = result["id"]
            company.created_at = datetime.fromtimestamp(result["created_at"])
            company.updated_at = datetime.fromtimestamp(result["updated_at"])
            
            self.logger.info(f"Created Intercom company: {company.id}")
            return company
            
        except Exception as e:
            self.logger.error(f"Failed to create company: {e}")
            raise
    
    async def get_company(self, company_id: str) -> IntercomCompany:
        """
        Get a company by ID.
        
        Args:
            company_id: Company ID
            
        Returns:
            Company data
        """
        try:
            result = self._make_request("GET", f"companies/{company_id}")
            
            return IntercomCompany(
                id=result["id"],
                name=result["name"],
                company_id=result.get("company_id"),
                plan=result.get("plan"),
                size=result.get("size"),
                website=result.get("website"),
                industry=result.get("industry"),
                monthly_spend=result.get("monthly_spend"),
                created_at=datetime.fromtimestamp(result["created_at"]),
                updated_at=datetime.fromtimestamp(result["updated_at"])
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get company: {e}")
            raise
    
    async def search_companies(self, query: str) -> List[IntercomCompany]:
        """
        Search companies.
        
        Args:
            query: Search query
            
        Returns:
            List of companies
        """
        try:
            data = {
                "query": query
            }
            
            result = self._make_request("POST", "companies/search", data)
            
            companies = []
            for item in result.get("data", []):
                company = IntercomCompany(
                    id=item["id"],
                    name=item["name"],
                    company_id=item.get("company_id"),
                    plan=item.get("plan"),
                    size=item.get("size"),
                    website=item.get("website"),
                    industry=item.get("industry"),
                    monthly_spend=item.get("monthly_spend"),
                    created_at=datetime.fromtimestamp(item["created_at"]),
                    updated_at=datetime.fromtimestamp(item["updated_at"])
                )
                companies.append(company)
            
            return companies
            
        except Exception as e:
            self.logger.error(f"Failed to search companies: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Intercom integration.
        
        Returns:
            Health check results
        """
        try:
            # Test API connectivity by getting tags
            tags = await self.get_tags()
            
            return {
                "status": "healthy",
                "total_tags": len(tags),
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
