"""
MCP (Model Context Protocol) integration for Core Backend.

This module handles routing tool calls through the Developer Platform
to external MCP servers without storing secrets in Core.
"""

import httpx
import asyncio
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for making MCP tool calls through the Developer Platform."""
    
    def __init__(self, dev_platform_url: str, service_token: str):
        self.dev_platform_url = dev_platform_url.rstrip('/')
        self.service_token = service_token
        self.timeout = httpx.Timeout(30.0)
        self.circuit_breaker_failures = 0
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_reset_time = datetime.utcnow()
        
    async def call_tool(
        self, 
        server_id: UUID, 
        tool_name: str, 
        params: Dict[str, Any],
        tenant_id: UUID
    ) -> Dict[str, Any]:
        """
        Call a tool on an MCP server through the Developer Platform.
        
        Args:
            server_id: The MCP server ID
            tool_name: The name of the tool to call
            params: Parameters to pass to the tool
            tenant_id: The tenant ID for context
            
        Returns:
            The result from the MCP tool call
            
        Raises:
            HTTPException: If the call fails
        """
        # Check circuit breaker
        if self._is_circuit_breaker_open():
            raise HTTPException(
                status_code=503, 
                detail="MCP service temporarily unavailable"
            )
            
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.dev_platform_url}/mcp/call",
                    headers={
                        "Authorization": f"Bearer {self.service_token}",
                        "X-Tenant-ID": str(tenant_id),
                        "Content-Type": "application/json"
                    },
                    json={
                        "server_id": str(server_id),
                        "tool_name": tool_name,
                        "params": params
                    }
                )
                
                if response.status_code == 200:
                    self._reset_circuit_breaker()
                    return response.json()
                else:
                    self._increment_circuit_breaker()
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"MCP call failed: {response.text}"
                    )
                    
        except httpx.TimeoutException:
            self._increment_circuit_breaker()
            raise HTTPException(
                status_code=504,
                detail="MCP call timed out"
            )
        except httpx.RequestError as e:
            self._increment_circuit_breaker()
            raise HTTPException(
                status_code=502,
                detail=f"MCP service error: {str(e)}"
            )
            
    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open."""
        if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
            # Check if reset time has passed
            if datetime.utcnow() > self.circuit_breaker_reset_time:
                self._reset_circuit_breaker()
                return False
            return True
        return False
        
    def _increment_circuit_breaker(self) -> None:
        """Increment circuit breaker failure count."""
        self.circuit_breaker_failures += 1
        if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
            # Set reset time to 30 seconds from now
            self.circuit_breaker_reset_time = datetime.utcnow() + timedelta(seconds=30)
            
    def _reset_circuit_breaker(self) -> None:
        """Reset circuit breaker."""
        self.circuit_breaker_failures = 0
        self.circuit_breaker_reset_time = datetime.utcnow()


class MCPManager:
    """Manager for MCP operations in Core Backend."""
    
    def __init__(self, dev_platform_url: str, service_token: str):
        self.client = MCPClient(dev_platform_url, service_token)
        
    async def create_crm_lead(
        self, 
        tenant_id: UUID, 
        lead_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a lead in CRM via MCP.
        
        Args:
            tenant_id: The tenant ID
            lead_data: Lead data (name, email, phone, etc.)
            
        Returns:
            The created lead information
        """
        # This would typically look up the appropriate MCP server for CRM
        # For now, we'll use a mock server ID
        server_id = UUID("00000000-0000-0000-0000-000000000001")
        
        return await self.client.call_tool(
            server_id=server_id,
            tool_name="crm.createLead",
            params=lead_data,
            tenant_id=tenant_id
        )
        
    async def update_crm_contact(
        self, 
        tenant_id: UUID, 
        contact_id: str,
        contact_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a contact in CRM via MCP.
        
        Args:
            tenant_id: The tenant ID
            contact_id: The contact ID to update
            contact_data: Updated contact data
            
        Returns:
            The updated contact information
        """
        server_id = UUID("00000000-0000-0000-0000-000000000001")
        
        return await self.client.call_tool(
            server_id=server_id,
            tool_name="crm.updateContact",
            params={"contact_id": contact_id, **contact_data},
            tenant_id=tenant_id
        )
        
    async def create_helpdesk_ticket(
        self, 
        tenant_id: UUID, 
        ticket_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a helpdesk ticket via MCP.
        
        Args:
            tenant_id: The tenant ID
            ticket_data: Ticket data (subject, description, priority, etc.)
            
        Returns:
            The created ticket information
        """
        server_id = UUID("00000000-0000-0000-0000-000000000002")
        
        return await self.client.call_tool(
            server_id=server_id,
            tool_name="helpdesk.createTicket",
            params=ticket_data,
            tenant_id=tenant_id
        )
        
    async def process_payment(
        self, 
        tenant_id: UUID, 
        payment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a payment via MCP.
        
        Args:
            tenant_id: The tenant ID
            payment_data: Payment data (amount, currency, method, etc.)
            
        Returns:
            The payment result
        """
        server_id = UUID("00000000-0000-0000-0000-000000000003")
        
        return await self.client.call_tool(
            server_id=server_id,
            tool_name="payments.processPayment",
            params=payment_data,
            tenant_id=tenant_id
        )

    async def send_email(
        self, 
        tenant_id: UUID, 
        email_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send an email via MCP.
        
        Args:
            tenant_id: The tenant ID
            email_data: Email data (to, subject, body, etc.)
            
        Returns:
            The email sending result
        """
        server_id = UUID("00000000-0000-0000-0000-000000000004")
        
        return await self.client.call_tool(
            server_id=server_id,
            tool_name="email.send",
            params=email_data,
            tenant_id=tenant_id
        )

    async def send_sms(
        self, 
        tenant_id: UUID, 
        sms_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send an SMS via MCP.
        
        Args:
            tenant_id: The tenant ID
            sms_data: SMS data (to, message, etc.)
            
        Returns:
            The SMS sending result
        """
        server_id = UUID("00000000-0000-0000-0000-000000000005")
        
        return await self.client.call_tool(
            server_id=server_id,
            tool_name="sms.send",
            params=sms_data,
            tenant_id=tenant_id
        )

    async def create_calendar_event(
        self, 
        tenant_id: UUID, 
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a calendar event via MCP.
        
        Args:
            tenant_id: The tenant ID
            event_data: Event data (title, start_time, end_time, attendees, etc.)
            
        Returns:
            The created event information
        """
        server_id = UUID("00000000-0000-0000-0000-000000000006")
        
        return await self.client.call_tool(
            server_id=server_id,
            tool_name="calendar.createEvent",
            params=event_data,
            tenant_id=tenant_id
        )

    async def list_calendar_events(
        self, 
        tenant_id: UUID, 
        start_date: str = None,
        end_date: str = None
    ) -> Dict[str, Any]:
        """
        List calendar events via MCP.
        
        Args:
            tenant_id: The tenant ID
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            List of calendar events
        """
        server_id = UUID("00000000-0000-0000-0000-000000000006")
        
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        return await self.client.call_tool(
            server_id=server_id,
            tool_name="calendar.listEvents",
            params=params,
            tenant_id=tenant_id
        )

    async def upload_document(
        self, 
        tenant_id: UUID, 
        document_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Upload a document via MCP.
        
        Args:
            tenant_id: The tenant ID
            document_data: Document data (file, name, folder, etc.)
            
        Returns:
            The uploaded document information
        """
        server_id = UUID("00000000-0000-0000-0000-000000000007")
        
        return await self.client.call_tool(
            server_id=server_id,
            tool_name="documents.upload",
            params=document_data,
            tenant_id=tenant_id
        )

    async def list_documents(
        self, 
        tenant_id: UUID, 
        folder_id: str = None
    ) -> Dict[str, Any]:
        """
        List documents via MCP.
        
        Args:
            tenant_id: The tenant ID
            folder_id: Optional folder ID to filter by
            
        Returns:
            List of documents
        """
        server_id = UUID("00000000-0000-0000-0000-000000000007")
        
        params = {}
        if folder_id:
            params["folder_id"] = folder_id
        
        return await self.client.call_tool(
            server_id=server_id,
            tool_name="documents.list",
            params=params,
            tenant_id=tenant_id
        )

    async def track_analytics(
        self, 
        tenant_id: UUID, 
        analytics_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Track analytics event via MCP.
        
        Args:
            tenant_id: The tenant ID
            analytics_data: Analytics data (event_name, properties, etc.)
            
        Returns:
            The tracking result
        """
        server_id = UUID("00000000-0000-0000-0000-000000000008")
        
        return await self.client.call_tool(
            server_id=server_id,
            tool_name="analytics.track",
            params=analytics_data,
            tenant_id=tenant_id
        )

    async def get_analytics_report(
        self, 
        tenant_id: UUID, 
        report_type: str,
        start_date: str = None,
        end_date: str = None
    ) -> Dict[str, Any]:
        """
        Get analytics report via MCP.
        
        Args:
            tenant_id: The tenant ID
            report_type: Type of report to generate
            start_date: Start date for the report
            end_date: End date for the report
            
        Returns:
            The analytics report
        """
        server_id = UUID("00000000-0000-0000-0000-000000000008")
        
        params = {"report_type": report_type}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        return await self.client.call_tool(
            server_id=server_id,
            tool_name="analytics.getReport",
            params=params,
            tenant_id=tenant_id
        )

    async def generate_ai_content(
        self, 
        tenant_id: UUID, 
        generation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate AI content via MCP.
        
        Args:
            tenant_id: The tenant ID
            generation_data: Generation data (prompt, model, parameters, etc.)
            
        Returns:
            The generated content
        """
        server_id = UUID("00000000-0000-0000-0000-000000000009")
        
        return await self.client.call_tool(
            server_id=server_id,
            tool_name="ai.generate",
            params=generation_data,
            tenant_id=tenant_id
        )

    async def analyze_with_ai(
        self, 
        tenant_id: UUID, 
        analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze content with AI via MCP.
        
        Args:
            tenant_id: The tenant ID
            analysis_data: Analysis data (content, analysis_type, etc.)
            
        Returns:
            The analysis result
        """
        server_id = UUID("00000000-0000-0000-0000-000000000009")
        
        return await self.client.call_tool(
            server_id=server_id,
            tool_name="ai.analyze",
            params=analysis_data,
            tenant_id=tenant_id
        )


# Global MCP manager instance
mcp_manager: Optional[MCPManager] = None


def init_mcp_manager(dev_platform_url: str, service_token: str) -> None:
    """Initialize the global MCP manager."""
    global mcp_manager
    mcp_manager = MCPManager(dev_platform_url, service_token)


def get_mcp_manager() -> MCPManager:
    """Get the global MCP manager instance."""
    if mcp_manager is None:
        raise RuntimeError("MCP manager not initialized")
    return mcp_manager 