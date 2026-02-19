"""
Calendly Consolidated Service with tenant-specific context and analytics.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Avoid circular import - import inside function where needed
# from backend.services.analytics_service import AnalyticsService  # Will implement later

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../shared"))

from integration.calendly import (
    CalendlyIntegration,
    CalendlyConfig,
    CalendlyEventStatus,
    CalendlyResponse,
)


class CalendlyServiceWrapper(CalendlyIntegration):
    """
    Tenant-aware Calendly service with analytics and context tracking.

    Extends CalendlyIntegration to provide tenant-specific scheduling operations,
    analytics tracking, and comprehensive context management.
    """

    def __init__(self, config: CalendlyConfig):
        super().__init__(config)
        # Initialize analytics service if available, otherwise use mock
        try:
            from ..analytics_service import AnalyticsService
            self.analytics_service = AnalyticsService()
        except ImportError:
            # Use mock analytics service
            self.analytics_service = None

    async def get_tenant_user_info(
        self,
        tenant_id: str,
        user_uri: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> CalendlyResponse:
        """
        Get user information with tenant context.

        Args:
            tenant_id (str): Unique identifier for the tenant
            user_uri (Optional[str]): Specific user URI, if None gets current user
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            CalendlyResponse: User information
        """
        start_time = datetime.now()
        operation_id = str(uuid.uuid4())

        try:
            if user_uri:
                result = await self.get_user(user_uri)
            else:
                result = await self.get_current_user()

            await self._record_analytics(
                tenant_id=tenant_id,
                operation="get_user",
                success=result.success,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                user_uri=user_uri
            )

            return result

        except Exception as e:
            await self._record_analytics(
                tenant_id=tenant_id,
                operation="get_user",
                success=False,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                error=str(e)
            )
            raise

    async def get_tenant_event_types(
        self,
        tenant_id: str,
        user_uri: str,
        count: int = 20,
        page_token: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> CalendlyResponse:
        """
        Get event types for tenant with analytics.

        Args:
            tenant_id (str): Unique identifier for the tenant
            user_uri (str): User URI
            count (int): Number of results per page
            page_token (Optional[str]): Pagination token
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            CalendlyResponse: Event types data
        """
        start_time = datetime.now()
        operation_id = str(uuid.uuid4())

        try:
            result = await self.list_event_types(
                user_uri=user_uri,
                count=count,
                page_token=page_token
            )

            await self._record_analytics(
                tenant_id=tenant_id,
                operation="list_event_types",
                success=result.success,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                user_uri=user_uri,
                count=count,
                result_count=len(result.data.get("collection", [])) if result.data else 0
            )

            return result

        except Exception as e:
            await self._record_analytics(
                tenant_id=tenant_id,
                operation="list_event_types",
                success=False,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                error=str(e)
            )
            raise

    async def get_tenant_scheduled_events(
        self,
        tenant_id: str,
        user_uri: Optional[str] = None,
        organization_uri: Optional[str] = None,
        count: int = 20,
        status: Optional[CalendlyEventStatus] = None,
        min_start_time: Optional[str] = None,
        max_start_time: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> CalendlyResponse:
        """
        Get scheduled events for tenant with analytics.

        Args:
            tenant_id (str): Unique identifier for the tenant
            user_uri (Optional[str]): Filter by user URI
            organization_uri (Optional[str]): Filter by organization URI
            count (int): Number of results per page
            status (Optional[CalendlyEventStatus]): Filter by status
            min_start_time (Optional[str]): Minimum start time
            max_start_time (Optional[str]): Maximum start time
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            CalendlyResponse: Scheduled events data
        """
        start_time = datetime.now()
        operation_id = str(uuid.uuid4())

        try:
            result = await self.list_events(
                user_uri=user_uri,
                organization_uri=organization_uri,
                count=count,
                status=status,
                min_start_time=min_start_time,
                max_start_time=max_start_time
            )

            await self._record_analytics(
                tenant_id=tenant_id,
                operation="list_events",
                success=result.success,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                user_uri=user_uri,
                organization_uri=organization_uri,
                count=count,
                status=status.value if status else None,
                result_count=len(result.data.get("collection", [])) if result.data else 0
            )

            return result

        except Exception as e:
            await self._record_analytics(
                tenant_id=tenant_id,
                operation="list_events",
                success=False,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                error=str(e)
            )
            raise

    async def get_tenant_event_details(
        self,
        tenant_id: str,
        event_uuid: str,
        include_invitees: bool = False,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive event details including invitees if requested.

        Args:
            tenant_id (str): Unique identifier for the tenant
            event_uuid (str): Event UUID
            include_invitees (bool): Whether to include invitee information
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            Dict[str, Any]: Complete event information
        """
        start_time = datetime.now()
        operation_id = str(uuid.uuid4())

        try:
            # Get event details
            event_result = await self.get_event(event_uuid)

            response_data = {
                "success": event_result.success,
                "event": event_result.data,
                "invitees": None
            }

            # Get invitees if requested and event fetch was successful
            if include_invitees and event_result.success:
                invitees_result = await self.list_event_invitees(event_uuid)
                response_data["invitees"] = invitees_result.data

            await self._record_analytics(
                tenant_id=tenant_id,
                operation="get_event_details",
                success=event_result.success,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                event_uuid=event_uuid,
                include_invitees=include_invitees
            )

            return response_data

        except Exception as e:
            await self._record_analytics(
                tenant_id=tenant_id,
                operation="get_event_details",
                success=False,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                error=str(e)
            )
            raise

    async def cancel_tenant_event(
        self,
        tenant_id: str,
        event_uuid: str,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> CalendlyResponse:
        """
        Cancel event with tenant context and analytics.

        Args:
            tenant_id (str): Unique identifier for the tenant
            event_uuid (str): Event UUID to cancel
            reason (Optional[str]): Cancellation reason
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            CalendlyResponse: Cancellation result
        """
        start_time = datetime.now()
        operation_id = str(uuid.uuid4())

        try:
            result = await self.cancel_event(event_uuid, reason)

            await self._record_analytics(
                tenant_id=tenant_id,
                operation="cancel_event",
                success=result.success,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                event_uuid=event_uuid,
                reason=reason
            )

            return result

        except Exception as e:
            await self._record_analytics(
                tenant_id=tenant_id,
                operation="cancel_event",
                success=False,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                error=str(e)
            )
            raise

    async def manage_tenant_webhooks(
        self,
        tenant_id: str,
        operation: str,
        callback_url: Optional[str] = None,
        events: Optional[List[str]] = None,
        organization_uri: Optional[str] = None,
        webhook_uuid: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> CalendlyResponse:
        """
        Manage webhooks with tenant context.

        Args:
            tenant_id (str): Unique identifier for the tenant
            operation (str): Operation (create, list, get, delete)
            callback_url (Optional[str]): Webhook callback URL (for create)
            events (Optional[List[str]]): Event types to subscribe to (for create)
            organization_uri (Optional[str]): Organization URI (for create/list)
            webhook_uuid (Optional[str]): Webhook UUID (for get/delete)
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            CalendlyResponse: Webhook operation result
        """
        start_time = datetime.now()
        operation_id = str(uuid.uuid4())

        try:
            result = None

            if operation == "create":
                if not all([callback_url, events, organization_uri]):
                    raise ValueError("callback_url, events, and organization_uri required for create")
                result = await self.create_webhook(callback_url, events, organization_uri)

            elif operation == "list":
                if not organization_uri:
                    raise ValueError("organization_uri required for list")
                result = await self.list_webhooks(organization_uri)

            elif operation == "get":
                if not webhook_uuid:
                    raise ValueError("webhook_uuid required for get")
                result = await self.get_webhook(webhook_uuid)

            elif operation == "delete":
                if not webhook_uuid:
                    raise ValueError("webhook_uuid required for delete")
                result = await self.delete_webhook(webhook_uuid)

            else:
                raise ValueError(f"Unknown webhook operation: {operation}")

            await self._record_analytics(
                tenant_id=tenant_id,
                operation=f"webhook_{operation}",
                success=result.success,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                webhook_uuid=webhook_uuid,
                organization_uri=organization_uri
            )

            return result

        except Exception as e:
            await self._record_analytics(
                tenant_id=tenant_id,
                operation=f"webhook_{operation}",
                success=False,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                error=str(e)
            )
            raise

    async def get_tenant_analytics(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get Calendly analytics for a specific tenant.

        Args:
            tenant_id (str): Unique identifier for the tenant
            start_date (Optional[datetime]): Start date for analytics
            end_date (Optional[datetime]): End date for analytics

        Returns:
            Dict[str, Any]: Analytics data for the tenant
        """
        if self.analytics_service:
            return await self.analytics_service.get_tenant_analytics(
                tenant_id=tenant_id,
                service="calendly",
                start_date=start_date,
                end_date=end_date
            )
        return {
            "tenant_id": tenant_id,
            "service": "calendly",
            "message": "Analytics service not available",
            "data": {}
        }

    async def get_tenant_usage_summary(
        self,
        tenant_id: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get usage summary for tenant.

        Args:
            tenant_id (str): Unique identifier for the tenant
            period_days (int): Number of days to analyze

        Returns:
            Dict[str, Any]: Usage summary data
        """
        try:
            end_date = datetime.now()
            start_date = datetime.now() - timedelta(days=period_days)

            analytics_data = await self.get_tenant_analytics(
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date
            )

            # Calculate usage metrics
            operations = analytics_data.get("operations", [])

            usage_summary = {
                "tenant_id": tenant_id,
                "period_days": period_days,
                "total_operations": len(operations),
                "successful_operations": len([op for op in operations if op.get("success", False)]),
                "failed_operations": len([op for op in operations if not op.get("success", True)]),
                "operation_types": {},
                "average_response_time": 0,
                "last_activity": None
            }

            # Analyze operation types
            for operation in operations:
                op_type = operation.get("operation", "unknown")
                if op_type not in usage_summary["operation_types"]:
                    usage_summary["operation_types"][op_type] = 0
                usage_summary["operation_types"][op_type] += 1

            # Calculate average response time
            response_times = [op.get("duration", 0) for op in operations if op.get("duration")]
            if response_times:
                usage_summary["average_response_time"] = sum(response_times) / len(response_times)

            # Find last activity
            if operations:
                timestamps = [op.get("timestamp") for op in operations if op.get("timestamp")]
                if timestamps:
                    usage_summary["last_activity"] = max(timestamps)

            return usage_summary

        except Exception as e:
            return {
                "tenant_id": tenant_id,
                "error": str(e),
                "period_days": period_days,
                "total_operations": 0
            }

    async def _record_analytics(
        self,
        tenant_id: str,
        operation: str,
        success: bool,
        duration: float,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """
        Record analytics data for Calendly operations.

        Args:
            tenant_id (str): Unique identifier for the tenant
            operation (str): Operation performed
            success (bool): Whether operation was successful
            duration (float): Operation duration in seconds
            context (Optional[Dict[str, Any]]): Additional context
            **kwargs: Additional data to record
        """
        analytics_data = {
            "tenant_id": tenant_id,
            "service": "calendly",
            "operation": operation,
            "success": success,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "context": context or {},
            **kwargs
        }

        if self.analytics_service:
            await self.analytics_service.record_operation(analytics_data)
        # If no analytics service, just log or skip silently


# Global service instance
calendly_consolidated_service: Optional[CalendlyServiceWrapper] = None


async def get_calendly_service() -> CalendlyServiceWrapper:
    """
    Get the global Calendly service instance.

    Returns:
        CalendlyServiceWrapper: The Calendly service instance
    """
    global calendly_consolidated_service

    if calendly_consolidated_service is None:
        # Initialize service from integration service
        from .integration_service import IntegrationService
        integration_service = IntegrationService()
        calendly_integration = await integration_service.get_integration("calendly")

        if not calendly_integration:
            raise RuntimeError("Calendly integration not configured")

        calendly_consolidated_service = CalendlyServiceWrapper(calendly_integration.config)

        # Test connection
        await calendly_consolidated_service.connect()

    return calendly_consolidated_service


async def init_calendly_service() -> None:
    """Initialize the Calendly service on startup."""
    try:
        await get_calendly_service()
        print("✅ Calendly service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Calendly service: {e}")


async def close_calendly_service() -> None:
    """Close the Calendly service on shutdown."""
    global calendly_consolidated_service

    if calendly_consolidated_service:
        await calendly_consolidated_service.disconnect()
        calendly_consolidated_service = None
        print("✅ Calendly service closed successfully")