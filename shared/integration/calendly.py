"""
Calendly Scheduling Integration Service.

Provides comprehensive scheduling and calendar management capabilities including
user management, event types, scheduled events, and webhooks.

MCP Support: Limited (no dedicated MCP server identified)
API Documentation: https://developer.calendly.com/api-docs
API Version: v2 (v1 deprecated as of August 2025)
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from enum import Enum

import httpx


class CalendlyEventStatus(str, Enum):
    """Event status values for Calendly."""
    ACTIVE = "active"
    CANCELED = "canceled"


class CalendlyEventType(str, Enum):
    """Event type categories for Calendly."""
    ONE_ON_ONE = "StandardEventType"
    GROUP = "GroupEventType"
    COLLECTIVE = "CollectiveEventType"
    ROUND_ROBIN = "RoundRobinEventType"


@dataclass
class CalendlyConfig:
    """Configuration for Calendly integration."""
    api_key: str  # Personal Access Token or OAuth token
    base_url: str = "https://api.calendly.com"
    timeout: int = 30
    max_retries: int = 3


@dataclass
class CalendlyUser:
    """Calendly user information."""
    uri: str
    name: str
    slug: str
    email: str
    avatar_url: Optional[str] = None
    timezone: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class CalendlyEventType:
    """Calendly event type configuration."""
    uri: str
    name: str
    slug: str
    duration: int  # Duration in minutes
    color: str
    active: bool
    booking_url: str
    description_plain: Optional[str] = None
    description_html: Optional[str] = None
    internal_note: Optional[str] = None
    kind: Optional[str] = None
    pooling_type: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class CalendlyInvitee:
    """Calendly event invitee information."""
    uri: str
    name: str
    email: str
    status: str
    timezone: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    tracking: Optional[Dict[str, Any]] = None
    text_reminder_number: Optional[str] = None
    rescheduled: Optional[bool] = None
    old_invitee: Optional[str] = None
    new_invitee: Optional[str] = None
    cancel_url: Optional[str] = None
    reschedule_url: Optional[str] = None


@dataclass
class CalendlyEvent:
    """Calendly scheduled event."""
    uri: str
    name: str
    status: CalendlyEventStatus
    start_time: str
    end_time: str
    event_type: str
    location: Dict[str, Any]
    invitees_counter: Dict[str, int]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    event_memberships: Optional[List[Dict[str, Any]]] = None
    event_guests: Optional[List[Dict[str, Any]]] = None
    meeting_notes_plain: Optional[str] = None
    meeting_notes_html: Optional[str] = None


@dataclass
class CalendlyWebhook:
    """Calendly webhook configuration."""
    uri: str
    callback_url: str
    state: str
    scope: str
    events: List[str]
    organization: str
    user: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class CalendlyResponse:
    """Response from Calendly API operation."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None
    pagination: Optional[Dict[str, Any]] = None


class CalendlyIntegration:
    """
    Calendly scheduling integration service.

    Provides comprehensive scheduling and calendar management capabilities
    including user management, event types, scheduled events, and webhooks.
    """

    def __init__(self, config: CalendlyConfig):
        """
        Initialize Calendly integration.

        Args:
            config (CalendlyConfig): Calendly configuration
        """
        self.config = config
        self._connected = False
        self.session = httpx.AsyncClient(
            timeout=config.timeout,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json"
            }
        )

    async def connect(self) -> bool:
        """
        Test connection to Calendly API.

        Returns:
            bool: True if connection successful
        """
        try:
            # Test with current user endpoint
            response = await self.get_current_user()
            self._connected = response.success
            return self._connected
        except Exception as e:
            print(f"Calendly connection test failed: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Close connection to Calendly API."""
        if self.session:
            await self.session.aclose()
        self._connected = False

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None
    ) -> CalendlyResponse:
        """
        Make HTTP request to Calendly API.

        Args:
            method (str): HTTP method
            endpoint (str): API endpoint
            data (Optional[Dict[str, Any]]): Request data
            params (Optional[Dict[str, str]]): Query parameters

        Returns:
            CalendlyResponse: API response
        """
        try:
            url = f"{self.config.base_url}/{endpoint}"

            response = await self.session.request(
                method=method,
                url=url,
                json=data,
                params=params
            )

            response.raise_for_status()
            response_data = response.json()

            return CalendlyResponse(
                success=True,
                data=response_data,
                message="Request successful"
            )

        except httpx.HTTPStatusError as e:
            error_data = {}
            try:
                error_data = e.response.json()
            except:
                pass

            return CalendlyResponse(
                success=False,
                error=f"HTTP {e.response.status_code}: {error_data.get('message', e.response.text)}",
                data=error_data
            )
        except Exception as e:
            return CalendlyResponse(
                success=False,
                error=f"Request failed: {str(e)}"
            )

    # User Management
    async def get_current_user(self) -> CalendlyResponse:
        """
        Get current user information.

        Returns:
            CalendlyResponse: Current user data
        """
        return await self._make_request("GET", "users/me")

    async def get_user(self, user_uri: str) -> CalendlyResponse:
        """
        Get user by URI.

        Args:
            user_uri (str): User URI

        Returns:
            CalendlyResponse: User data
        """
        # Extract UUID from URI for API call
        user_uuid = user_uri.split("/")[-1]
        return await self._make_request("GET", f"users/{user_uuid}")

    # Event Types Management
    async def list_event_types(
        self,
        user_uri: str,
        count: int = 20,
        page_token: Optional[str] = None,
        sort: str = "name:asc"
    ) -> CalendlyResponse:
        """
        List user's event types.

        Args:
            user_uri (str): User URI
            count (int): Number of results per page
            page_token (Optional[str]): Pagination token
            sort (str): Sort order

        Returns:
            CalendlyResponse: Event types list
        """
        params = {
            "user": user_uri,
            "count": str(count),
            "sort": sort
        }
        if page_token:
            params["page_token"] = page_token

        return await self._make_request("GET", "event_types", params=params)

    async def get_event_type(self, event_type_uuid: str) -> CalendlyResponse:
        """
        Get event type by UUID.

        Args:
            event_type_uuid (str): Event type UUID

        Returns:
            CalendlyResponse: Event type data
        """
        return await self._make_request("GET", f"event_types/{event_type_uuid}")

    # Scheduled Events Management
    async def list_events(
        self,
        user_uri: Optional[str] = None,
        organization_uri: Optional[str] = None,
        count: int = 20,
        page_token: Optional[str] = None,
        sort: str = "start_time:asc",
        status: Optional[CalendlyEventStatus] = None,
        min_start_time: Optional[str] = None,
        max_start_time: Optional[str] = None
    ) -> CalendlyResponse:
        """
        List scheduled events.

        Args:
            user_uri (Optional[str]): Filter by user URI
            organization_uri (Optional[str]): Filter by organization URI
            count (int): Number of results per page
            page_token (Optional[str]): Pagination token
            sort (str): Sort order
            status (Optional[CalendlyEventStatus]): Filter by status
            min_start_time (Optional[str]): Minimum start time (ISO 8601)
            max_start_time (Optional[str]): Maximum start time (ISO 8601)

        Returns:
            CalendlyResponse: Events list
        """
        params = {
            "count": str(count),
            "sort": sort
        }

        if user_uri:
            params["user"] = user_uri
        if organization_uri:
            params["organization"] = organization_uri
        if page_token:
            params["page_token"] = page_token
        if status:
            params["status"] = status.value
        if min_start_time:
            params["min_start_time"] = min_start_time
        if max_start_time:
            params["max_start_time"] = max_start_time

        return await self._make_request("GET", "scheduled_events", params=params)

    async def get_event(self, event_uuid: str) -> CalendlyResponse:
        """
        Get scheduled event by UUID.

        Args:
            event_uuid (str): Event UUID

        Returns:
            CalendlyResponse: Event data
        """
        return await self._make_request("GET", f"scheduled_events/{event_uuid}")

    async def cancel_event(self, event_uuid: str, reason: Optional[str] = None) -> CalendlyResponse:
        """
        Cancel a scheduled event.

        Args:
            event_uuid (str): Event UUID
            reason (Optional[str]): Cancellation reason

        Returns:
            CalendlyResponse: Cancellation result
        """
        data = {}
        if reason:
            data["reason"] = reason

        return await self._make_request("DELETE", f"scheduled_events/{event_uuid}", data=data)

    # Invitees Management
    async def list_event_invitees(
        self,
        event_uuid: str,
        count: int = 20,
        page_token: Optional[str] = None,
        email: Optional[str] = None,
        status: Optional[str] = None
    ) -> CalendlyResponse:
        """
        List invitees for an event.

        Args:
            event_uuid (str): Event UUID
            count (int): Number of results per page
            page_token (Optional[str]): Pagination token
            email (Optional[str]): Filter by email
            status (Optional[str]): Filter by status

        Returns:
            CalendlyResponse: Invitees list
        """
        params = {
            "count": str(count)
        }
        if page_token:
            params["page_token"] = page_token
        if email:
            params["email"] = email
        if status:
            params["status"] = status

        return await self._make_request("GET", f"scheduled_events/{event_uuid}/invitees", params=params)

    async def get_invitee(self, invitee_uuid: str) -> CalendlyResponse:
        """
        Get invitee by UUID.

        Args:
            invitee_uuid (str): Invitee UUID

        Returns:
            CalendlyResponse: Invitee data
        """
        return await self._make_request("GET", f"scheduled_events/invitees/{invitee_uuid}")

    # Webhooks Management
    async def create_webhook(
        self,
        callback_url: str,
        events: List[str],
        organization_uri: str,
        scope: str = "organization",
        user_uri: Optional[str] = None
    ) -> CalendlyResponse:
        """
        Create a webhook subscription.

        Args:
            callback_url (str): Webhook callback URL
            events (List[str]): Event types to subscribe to
            organization_uri (str): Organization URI
            scope (str): Webhook scope
            user_uri (Optional[str]): User URI for user-scoped webhooks

        Returns:
            CalendlyResponse: Webhook creation result
        """
        data = {
            "url": callback_url,
            "events": events,
            "organization": organization_uri,
            "scope": scope
        }
        if user_uri:
            data["user"] = user_uri

        return await self._make_request("POST", "webhook_subscriptions", data=data)

    async def list_webhooks(
        self,
        organization_uri: str,
        scope: str = "organization",
        user_uri: Optional[str] = None
    ) -> CalendlyResponse:
        """
        List webhook subscriptions.

        Args:
            organization_uri (str): Organization URI
            scope (str): Webhook scope
            user_uri (Optional[str]): User URI for user-scoped webhooks

        Returns:
            CalendlyResponse: Webhooks list
        """
        params = {
            "organization": organization_uri,
            "scope": scope
        }
        if user_uri:
            params["user"] = user_uri

        return await self._make_request("GET", "webhook_subscriptions", params=params)

    async def get_webhook(self, webhook_uuid: str) -> CalendlyResponse:
        """
        Get webhook by UUID.

        Args:
            webhook_uuid (str): Webhook UUID

        Returns:
            CalendlyResponse: Webhook data
        """
        return await self._make_request("GET", f"webhook_subscriptions/{webhook_uuid}")

    async def delete_webhook(self, webhook_uuid: str) -> CalendlyResponse:
        """
        Delete webhook subscription.

        Args:
            webhook_uuid (str): Webhook UUID

        Returns:
            CalendlyResponse: Deletion result
        """
        return await self._make_request("DELETE", f"webhook_subscriptions/{webhook_uuid}")

    # Organization Management
    async def get_organization_membership(self, membership_uuid: str) -> CalendlyResponse:
        """
        Get organization membership.

        Args:
            membership_uuid (str): Membership UUID

        Returns:
            CalendlyResponse: Membership data
        """
        return await self._make_request("GET", f"organization_memberships/{membership_uuid}")

    async def list_organization_memberships(
        self,
        organization_uri: str,
        count: int = 20,
        page_token: Optional[str] = None,
        email: Optional[str] = None
    ) -> CalendlyResponse:
        """
        List organization memberships.

        Args:
            organization_uri (str): Organization URI
            count (int): Number of results per page
            page_token (Optional[str]): Pagination token
            email (Optional[str]): Filter by email

        Returns:
            CalendlyResponse: Memberships list
        """
        params = {
            "organization": organization_uri,
            "count": str(count)
        }
        if page_token:
            params["page_token"] = page_token
        if email:
            params["email"] = email

        return await self._make_request("GET", "organization_memberships", params=params)

    # Availability and Scheduling
    async def get_user_availability(
        self,
        user_uri: str,
        start_time: str,
        end_time: str
    ) -> CalendlyResponse:
        """
        Get user availability (Note: This might require premium features).

        Args:
            user_uri (str): User URI
            start_time (str): Start time (ISO 8601)
            end_time (str): End time (ISO 8601)

        Returns:
            CalendlyResponse: Availability data
        """
        params = {
            "user": user_uri,
            "start_time": start_time,
            "end_time": end_time
        }

        return await self._make_request("GET", "user_availability_schedules", params=params)

    async def get_event_type_available_times(
        self,
        event_type_uri: str,
        start_time: str,
        end_time: str
    ) -> CalendlyResponse:
        """
        Get available times for a specific event type.

        Args:
            event_type_uri (str): Event type URI
            start_time (str): Start time (ISO 8601)
            end_time (str): End time (ISO 8601)

        Returns:
            CalendlyResponse: Available time slots
        """
        params = {
            "event_type": event_type_uri,
            "start_time": start_time,
            "end_time": end_time
        }
        return await self._make_request("GET", "event_type_available_times", params=params)

    async def generate_scheduling_link(
        self,
        event_type_uri: str,
        start_time: Optional[str] = None,
        prefill_data: Optional[Dict[str, Any]] = None
    ) -> CalendlyResponse:
        """
        Generate a scheduling link for an event type.
        Since direct booking via API is limited, this creates a scheduling URL
        that can be used to complete the booking.

        Args:
            event_type_uri (str): Event type URI
            start_time (Optional[str]): Pre-selected start time (ISO 8601)
            prefill_data (Optional[Dict[str, Any]]): Data to prefill in the form

        Returns:
            CalendlyResponse: Scheduling link and details
        """
        try:
            # Get event type details to construct scheduling URL
            event_type_response = await self.get_event_type(event_type_uri.split('/')[-1])

            if not event_type_response.success:
                return event_type_response

            event_type_data = event_type_response.data.get('resource', {})
            scheduling_url = event_type_data.get('scheduling_url', '')

            # Build URL with prefill parameters
            url_params = []
            if start_time:
                url_params.append(f"date={start_time[:10]}")  # YYYY-MM-DD format
                url_params.append(f"time={start_time[11:16]}")  # HH:MM format

            if prefill_data:
                if prefill_data.get('name'):
                    url_params.append(f"name={prefill_data['name']}")
                if prefill_data.get('email'):
                    url_params.append(f"email={prefill_data['email']}")

            if url_params:
                scheduling_url += "?" + "&".join(url_params)

            return CalendlyResponse(
                success=True,
                data={
                    "scheduling_url": scheduling_url,
                    "event_type": event_type_data,
                    "prefill_data": prefill_data or {},
                    "note": "Complete booking by visiting the scheduling URL"
                },
                message="Scheduling link generated successfully"
            )

        except Exception as e:
            return CalendlyResponse(
                success=False,
                error=f"Failed to generate scheduling link: {str(e)}"
            )

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Calendly service health and capabilities.

        Returns:
            Dict[str, Any]: Health status and capabilities
        """
        try:
            # Test current user endpoint
            test_result = await self.get_current_user()

            capabilities = [
                "user_management",
                "event_types",
                "scheduled_events",
                "invitee_management",
                "webhook_subscriptions",
                "organization_management",
                "event_cancellation"
            ]

            return {
                "connected": test_result.success,
                "service": "calendly",
                "capabilities": capabilities,
                "api_version": "v2",
                "api_key_configured": bool(self.config.api_key),
                "base_url": self.config.base_url,
                "last_test": datetime.now().isoformat(),
                "test_result": test_result.success
            }

        except Exception as e:
            return {
                "connected": False,
                "service": "calendly",
                "error": str(e),
                "capabilities": [],
                "api_key_configured": bool(self.config.api_key)
            }

    async def get_capabilities(self) -> Dict[str, Any]:
        """
        Get detailed service capabilities.

        Returns:
            Dict[str, Any]: Service capabilities and features
        """
        return {
            "service": "calendly",
            "provider": "Calendly",
            "version": "2.0.0",
            "api_version": "v2",
            "capabilities": {
                "user_management": {
                    "get_current_user": True,
                    "get_user_by_uri": True,
                    "user_profiles": True
                },
                "event_types": {
                    "list_event_types": True,
                    "get_event_type": True,
                    "event_type_configuration": True
                },
                "scheduled_events": {
                    "list_events": True,
                    "get_event": True,
                    "cancel_event": True,
                    "event_filtering": True,
                    "time_range_filtering": True
                },
                "invitees": {
                    "list_invitees": True,
                    "get_invitee": True,
                    "invitee_filtering": True
                },
                "webhooks": {
                    "create_webhook": True,
                    "list_webhooks": True,
                    "get_webhook": True,
                    "delete_webhook": True,
                    "organization_scope": True,
                    "user_scope": True
                },
                "organization": {
                    "organization_memberships": True,
                    "membership_management": True
                }
            },
            "limitations": {
                "no_direct_scheduling": "API does not support direct event scheduling",
                "no_event_creation": "Cannot create events via API",
                "read_mostly": "Primarily read-only with limited write operations"
            },
            "mcp_support": {
                "available": False,
                "server": None,
                "description": "No dedicated MCP server identified"
            },
            "authentication": {
                "type": "oauth2_or_pat",
                "methods": ["personal_access_token", "oauth2"],
                "required": True
            },
            "rate_limits": {
                "requests_per_minute": "Varies by plan",
                "note": "See Calendly documentation for specific limits"
            }
        }


def create_calendly_integration(api_key: Optional[str] = None) -> CalendlyIntegration:
    """
    Create Calendly integration instance.

    Args:
        api_key (Optional[str]): Calendly API key, if not provided uses environment variable

    Returns:
        CalendlyIntegration: Configured Calendly integration
    """
    if not api_key:
        api_key = os.getenv("CALENDLY_API_KEY")

    if not api_key:
        raise ValueError("Calendly API key is required")

    config = CalendlyConfig(api_key=api_key)
    return CalendlyIntegration(config)


# Export key classes
__all__ = [
    "CalendlyIntegration",
    "CalendlyConfig",
    "CalendlyUser",
    "CalendlyEventType",
    "CalendlyEvent",
    "CalendlyInvitee",
    "CalendlyWebhook",
    "CalendlyResponse",
    "CalendlyEventStatus",
    "CalendlyEventType",
    "create_calendly_integration"
]