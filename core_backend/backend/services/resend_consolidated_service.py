"""
Resend Consolidated Service with tenant-specific context and analytics.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# from backend.services.integration_service import IntegrationService  # Avoid circular import
from .analytics_service import AnalyticsService

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../shared"))

from integration.resend import (
    ResendIntegration,
    ResendConfig,
    ResendEmail,
    ResendContact,
    ResendDomain,
    ResendResponse,
)


class ResendServiceWrapper(ResendIntegration):
    """
    Tenant-aware Resend service with analytics and context tracking.

    Extends ResendIntegration to provide tenant-specific email operations,
    analytics tracking, and comprehensive context management.
    """

    def __init__(self, config: ResendConfig):
        super().__init__(config)
        self.analytics_service = AnalyticsService()

    async def send_tenant_email(
        self,
        tenant_id: str,
        email: ResendEmail,
        context: Optional[Dict[str, Any]] = None
    ) -> ResendResponse:
        """
        Send email with tenant context and analytics tracking.

        Args:
            tenant_id (str): Unique identifier for the tenant
            email (ResendEmail): Email data to send
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            ResendResponse: Response from email sending operation
        """
        # Add tenant context to email tags
        if not email.tags:
            email.tags = []
        email.tags.append(f"tenant:{tenant_id}")

        # Add timestamp and tracking
        if not email.headers:
            email.headers = {}
        email.headers["X-Tenant-ID"] = tenant_id
        email.headers["X-Tracking-ID"] = str(uuid.uuid4())

        # Track analytics
        start_time = datetime.now()

        try:
            result = await self.send_email(email)

            # Record success analytics
            await self._record_analytics(
                tenant_id=tenant_id,
                operation="send_email",
                success=result.success,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                email_id=result.email_id
            )

            return result

        except Exception as e:
            # Record failure analytics
            await self._record_analytics(
                tenant_id=tenant_id,
                operation="send_email",
                success=False,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                error=str(e)
            )
            raise

    async def send_tenant_batch_emails(
        self,
        tenant_id: str,
        batch: Dict[str, Any],  # ResendBatchEmail not available
        context: Optional[Dict[str, Any]] = None
    ) -> ResendResponse:
        """
        Send batch emails with tenant context and analytics tracking.

        Args:
            tenant_id (str): Unique identifier for the tenant
            batch (ResendBatchEmail): Batch email data to send
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            ResendResponse: Response from batch email operation
        """
        # Add tenant context to each email in batch
        for email in batch.emails:
            if not email.tags:
                email.tags = []
            email.tags.append(f"tenant:{tenant_id}")

            if not email.headers:
                email.headers = {}
            email.headers["X-Tenant-ID"] = tenant_id
            email.headers["X-Batch-ID"] = str(uuid.uuid4())

        start_time = datetime.now()

        try:
            result = await self.send_batch_emails(batch)

            await self._record_analytics(
                tenant_id=tenant_id,
                operation="send_batch_emails",
                success=result.success,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                batch_size=len(batch.emails)
            )

            return result

        except Exception as e:
            await self._record_analytics(
                tenant_id=tenant_id,
                operation="send_batch_emails",
                success=False,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                error=str(e)
            )
            raise

    async def manage_tenant_domain(
        self,
        tenant_id: str,
        domain: ResendDomain,
        operation: str = "add",
        context: Optional[Dict[str, Any]] = None
    ) -> ResendResponse:
        """
        Manage domain with tenant context and analytics tracking.

        Args:
            tenant_id (str): Unique identifier for the tenant
            domain (ResendDomain): Domain data
            operation (str): Operation type (add, remove, verify)
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            ResendResponse: Response from domain operation
        """
        start_time = datetime.now()

        try:
            if operation == "add":
                result = await self.add_domain(domain)
            elif operation == "remove":
                result = await self.remove_domain(domain.name)
            elif operation == "verify":
                result = await self.verify_domain(domain.name)
            else:
                raise ValueError(f"Unknown domain operation: {operation}")

            await self._record_analytics(
                tenant_id=tenant_id,
                operation=f"domain_{operation}",
                success=result.success,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                domain=domain.name
            )

            return result

        except Exception as e:
            await self._record_analytics(
                tenant_id=tenant_id,
                operation=f"domain_{operation}",
                success=False,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                error=str(e)
            )
            raise

    async def manage_tenant_contacts(
        self,
        tenant_id: str,
        audience_id: str,
        contacts: List[ResendContact],
        operation: str = "add",
        context: Optional[Dict[str, Any]] = None
    ) -> ResendResponse:
        """
        Manage contacts with tenant context and analytics tracking.

        Args:
            tenant_id (str): Unique identifier for the tenant
            audience_id (str): Audience identifier
            contacts (List[ResendContact]): List of contacts
            operation (str): Operation type (add, remove)
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            ResendResponse: Response from contact operation
        """
        start_time = datetime.now()

        try:
            if operation == "add":
                result = await self.add_contacts_to_audience(audience_id, contacts)
            elif operation == "remove":
                contact_ids = [contact.id for contact in contacts if contact.id]
                result = await self.remove_contacts_from_audience(audience_id, contact_ids)
            else:
                raise ValueError(f"Unknown contact operation: {operation}")

            await self._record_analytics(
                tenant_id=tenant_id,
                operation=f"contacts_{operation}",
                success=result.success,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                contact_count=len(contacts),
                audience_id=audience_id
            )

            return result

        except Exception as e:
            await self._record_analytics(
                tenant_id=tenant_id,
                operation=f"contacts_{operation}",
                success=False,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
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
        Get Resend analytics for a specific tenant.

        Args:
            tenant_id (str): Unique identifier for the tenant
            start_date (Optional[datetime]): Start date for analytics
            end_date (Optional[datetime]): End date for analytics

        Returns:
            Dict[str, Any]: Analytics data for the tenant
        """
        return await self.analytics_service.get_tenant_analytics(
            tenant_id=tenant_id,
            service="resend",
            start_date=start_date,
            end_date=end_date
        )

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
        Record analytics data for Resend operations.

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
            "service": "resend",
            "operation": operation,
            "success": success,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "context": context or {},
            **kwargs
        }

        await self.analytics_service.record_operation(analytics_data)


# Global service instance
resend_consolidated_service: Optional[ResendServiceWrapper] = None


async def get_resend_service() -> ResendServiceWrapper:
    """
    Get the global Resend service instance.

    Returns:
        ResendServiceWrapper: The Resend service instance
    """
    global resend_consolidated_service

    if resend_consolidated_service is None:
        # Initialize directly with API key from environment
        api_key = os.getenv("RESEND_API_KEY")
        if not api_key:
            raise RuntimeError("Resend API key not configured")

        config = ResendConfig(api_key=api_key)
        resend_consolidated_service = ResendServiceWrapper(config)

        # Test connection
        await resend_consolidated_service.connect()

    return resend_consolidated_service


async def init_resend_service() -> None:
    """Initialize the Resend service on startup."""
    try:
        await get_resend_service()
        print("✅ Resend service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Resend service: {e}")


async def close_resend_service() -> None:
    """Close the Resend service on shutdown."""
    global resend_consolidated_service

    if resend_consolidated_service:
        await resend_consolidated_service.disconnect()
        resend_consolidated_service = None
        print("✅ Resend service closed successfully")