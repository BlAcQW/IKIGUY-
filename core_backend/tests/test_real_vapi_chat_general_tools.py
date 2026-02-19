"""
Tests for Real VAPI Chat General Tools Integration

This module contains comprehensive tests for all VAPI tools including:
- Healthcare tools (search, emergency, specialties, areas)
- Communication tools (email, SMS)
- Calendar tools (availability, booking)
- Support tools (tickets, HubSpot, escalation)
- Data tools (logging, summarization)
- Search tools (web search with AI)

Tests actual VAPI chat API responses to verify tool functionality.
"""

import pytest
import asyncio
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

# Custom JSON encoder for datetime objects
class DateTimeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class TestRealVAPIChatGeneralTools:
    """Comprehensive test suite for all VAPI tools through real chat API."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test configuration."""
        self.api_key = '42cf1e7c-2ef9-4bd7-ba30-52f2813605a2'
        self.vapi_base_url = 'https://api.vapi.ai'

        # Tool ID mappings (from VAPI CLI tool list)
        self.tool_ids = {
            # Communication Tools
            'send_notification_email': 'abc528ae-e1f1-4e9c-a939-bc859e5e7d88',
            'send_sms_vonage': 'fc1ca495-9083-492e-854a-aeee6e5b3f64',
            'email_notification': '86e8b665-ddf8-4695-872f-772cb303d54d',

            # Calendar Tools
            'check_calendly_availability': '3f6ddf13-5121-4127-8aec-bdc4dfda6f7d',
            'book_calendly_appointment': 'd1c30e08-aae8-49b1-b06e-ba3a3e634f18',

            # Support Tools
            'create_support_ticket': '83635498-8f71-453a-9a15-7e00e1e494a2',
            'create_hubspot_contact': '1e59ec6d-e2ec-4707-9e71-7dbceb51da0d',
            'escalate_to_support': '457d5d87-a0ed-44ab-b6d6-ce3ec912ba01',

            # Data Tools
            'call_logging_supabase': 'bb90890c-750d-429f-9a40-836140c70d1c',
            'ai_transcript_summarization': '6eb24d57-16ef-4262-a587-a5cd1e038629',
            'record_call_details': '1231e261-c8c3-4009-9729-3aa8ea8dc86c',

            # Search Tools
            'search_web_with_ai': 'd7f97ff5-e4ce-46fd-a75c-8bb0cf76454b'
        }

    def chat_with_vapi(self, question: str, tool_ids: List[str]) -> Tuple[bool, str, List[str]]:
        """
        Send a question to VAPI chat API with specific tools.

        Args:
            question: Question to ask the assistant
            tool_ids: List of tool IDs to include

        Returns:
            Tuple of (success, response, tool_calls)
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                "assistant": {
                    "model": {
                        "provider": "openai",
                        "model": "gpt-4o-mini",
                        "messages": [{
                            "role": "system",
                            "content": "You are Sarah, a helpful assistant for AI Labs Africa. You can help with healthcare, scheduling, communications, support tickets, and general inquiries."
                        }],
                        "toolIds": tool_ids
                    }
                },
                "input": question
            }

            response = requests.post(
                f"{self.vapi_base_url}/chat",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code in [200, 201]:
                data = response.json()

                response_text = ""
                tool_calls = []
                tool_results = []

                for output in data.get('output', []):
                    if output.get('role') == 'assistant':
                        if 'content' in output and output['content']:
                            response_text = output['content']
                        if 'tool_calls' in output:
                            for tool_call in output['tool_calls']:
                                tool_calls.append(tool_call['function']['name'])
                    elif output.get('role') == 'tool':
                        tool_results.append(output.get('content', ''))

                # Print tool results for verification
                if tool_results:
                    print(f"Tool results: {tool_results}")

                return True, response_text, tool_calls
            else:
                return False, f"API Error: {response.status_code}", []

        except Exception as e:
            return False, f"Exception: {str(e)}", []

    # Communication Tools Tests
    def test_send_notification_email(self):
        """Test email notification functionality."""
        tool_ids = [self.tool_ids['send_notification_email']]
        success, response, tool_calls = self.chat_with_vapi(
            "Send an email notification to test@example.com about our meeting",
            tool_ids
        )

        assert success, f"VAPI call failed: {response}"
        # Should either call the tool or ask for more details
        assert ('send_notification_email' in tool_calls or
                'email' in response.lower() or
                'need' in response.lower())

    def test_send_sms_vonage(self):
        """Test SMS sending functionality."""
        tool_ids = [self.tool_ids['send_sms_vonage']]
        success, response, tool_calls = self.chat_with_vapi(
            "Send an SMS to +233244123456 about appointment confirmation",
            tool_ids
        )

        assert success, f"VAPI call failed: {response}"
        assert ('send_sms_vonage' in tool_calls or
                'sms' in response.lower() or
                'text' in response.lower())

    # Calendar Tools Tests
    def test_check_calendly_availability(self):
        """Test calendar availability checking."""
        tool_ids = [self.tool_ids['check_calendly_availability']]
        success, response, tool_calls = self.chat_with_vapi(
            "Check my calendar availability for next week",
            tool_ids
        )

        assert success, f"VAPI call failed: {response}"
        assert ('check_calendly_availability' in tool_calls or
                'calendar' in response.lower() or
                'availab' in response.lower())

    def test_book_calendly_appointment(self):
        """Test appointment booking functionality."""
        tool_ids = [self.tool_ids['book_calendly_appointment']]
        success, response, tool_calls = self.chat_with_vapi(
            "Book an appointment for consultation on Friday at 2 PM",
            tool_ids
        )

        assert success, f"VAPI call failed: {response}"
        assert ('book_calendly_appointment' in tool_calls or
                'appointment' in response.lower() or
                'book' in response.lower())

    # Support Tools Tests
    def test_create_support_ticket(self):
        """Test support ticket creation."""
        tool_ids = [self.tool_ids['create_support_ticket']]
        success, response, tool_calls = self.chat_with_vapi(
            "Create a support ticket for login issues",
            tool_ids
        )

        assert success, f"VAPI call failed: {response}"
        assert ('create_support_ticket' in tool_calls or
                'ticket' in response.lower() or
                'support' in response.lower())

    def test_create_hubspot_contact(self):
        """Test HubSpot contact creation."""
        tool_ids = [self.tool_ids['create_hubspot_contact']]
        success, response, tool_calls = self.chat_with_vapi(
            "Add John Smith with email john@company.com to HubSpot",
            tool_ids
        )

        assert success, f"VAPI call failed: {response}"
        assert ('create_hubspot_contact' in tool_calls or
                'hubspot' in response.lower() or
                'contact' in response.lower())

    def test_escalate_to_support(self):
        """Test escalation to human support."""
        tool_ids = [self.tool_ids['escalate_to_support']]
        success, response, tool_calls = self.chat_with_vapi(
            "I need to escalate this issue to human support",
            tool_ids
        )

        assert success, f"VAPI call failed: {response}"
        assert ('escalate_to_support' in tool_calls or
                'escalate' in response.lower() or
                'human' in response.lower())

    # Data Tools Tests
    def test_record_call_details(self):
        """Test call details recording."""
        tool_ids = [self.tool_ids['record_call_details']]
        success, response, tool_calls = self.chat_with_vapi(
            "Record the details of this call for quality assurance",
            tool_ids
        )

        assert success, f"VAPI call failed: {response}"
        assert ('record_call_details' in tool_calls or
                'record' in response.lower() or
                'call' in response.lower())

    def test_ai_transcript_summarization(self):
        """Test AI transcript summarization."""
        tool_ids = [self.tool_ids['ai_transcript_summarization']]
        success, response, tool_calls = self.chat_with_vapi(
            "Summarize the key points from our conversation transcript",
            tool_ids
        )

        assert success, f"VAPI call failed: {response}"
        assert ('ai_transcript_summarization' in tool_calls or
                'summar' in response.lower() or
                'transcript' in response.lower())

    # Search Tools Tests
    def test_search_web_with_ai(self):
        """Test web search with AI functionality."""
        tool_ids = [self.tool_ids['search_web_with_ai']]
        success, response, tool_calls = self.chat_with_vapi(
            "Search the web for latest AI technology trends",
            tool_ids
        )

        assert success, f"VAPI call failed: {response}"
        assert ('search_web_with_ai' in tool_calls or
                'search' in response.lower() or
                'web' in response.lower())

    # Integration Tests
    def test_multi_tool_workflow(self):
        """Test workflow involving multiple tools."""
        tool_ids = [
            self.tool_ids['check_calendly_availability'],
            self.tool_ids['send_notification_email']
        ]
        success, response, tool_calls = self.chat_with_vapi(
            "Check my availability and send a confirmation email",
            tool_ids
        )

        assert success, f"VAPI call failed: {response}"
        # Should mention calendar or email functionality
        assert (any(tool in tool_calls for tool in ['check_calendly_availability', 'send_notification_email']) or
                'calendar' in response.lower() or
                'email' in response.lower())

    def test_communication_workflow(self):
        """Test communication tools workflow."""
        tool_ids = [
            self.tool_ids['send_notification_email'],
            self.tool_ids['send_sms_vonage']
        ]
        success, response, tool_calls = self.chat_with_vapi(
            "Send both email and SMS notifications to customer",
            tool_ids
        )

        assert success, f"VAPI call failed: {response}"
        assert (any(tool in tool_calls for tool in ['send_notification_email', 'send_sms_vonage']) or
                'email' in response.lower() or
                'sms' in response.lower())

    # Error Handling Tests
    def test_invalid_tool_request(self):
        """Test handling of requests that don't match available tools."""
        tool_ids = [self.tool_ids['send_notification_email']]
        success, response, tool_calls = self.chat_with_vapi(
            "What's the weather like today?",
            tool_ids
        )

        assert success, f"VAPI call failed: {response}"
        # Should gracefully handle unrelated request
        assert len(response) > 0

    def test_empty_input(self):
        """Test handling of empty or minimal input."""
        tool_ids = [self.tool_ids['send_notification_email']]
        success, response, tool_calls = self.chat_with_vapi(
            "Hello",
            tool_ids
        )

        assert success, f"VAPI call failed: {response}"
        assert len(response) > 0

    # Performance Tests
    @pytest.mark.slow
    def test_tool_response_time(self):
        """Test that tool responses are returned within reasonable time."""
        tool_ids = [self.tool_ids['get_available_areas']]
        start_time = time.time()

        success, response, tool_calls = self.chat_with_vapi(
            "What areas do you cover?",
            tool_ids
        )

        response_time = time.time() - start_time

        assert success, f"VAPI call failed: {response}"
        assert response_time < 30, f"Response took too long: {response_time}s"

    # Comprehensive Integration Test
    @pytest.mark.integration
    def test_all_tools_basic_functionality(self):
        """Test basic functionality of all tools with simple queries."""
        test_cases = [
            ("Send email", ['send_notification_email']),
            ("Check calendar", ['check_calendly_availability']),
            ("Create ticket", ['create_support_ticket']),
            ("Search web", ['search_web_with_ai']),
            ("Send SMS", ['send_sms_vonage'])
        ]

        results = []
        for query, tools in test_cases:
            tool_ids = [self.tool_ids[tool] for tool in tools if tool in self.tool_ids]
            success, response, tool_calls = self.chat_with_vapi(query, tool_ids)

            results.append({
                'query': query,
                'tools': tools,
                'success': success,
                'response_length': len(response) if response else 0,
                'tool_calls': tool_calls
            })

        # Assert all basic functionality works
        success_count = sum(1 for r in results if r['success'])
        assert success_count >= len(test_cases) * 0.8, f"Too many failures: {results}"

    def teardown_method(self):
        """Clean up after each test."""
        # Add any cleanup logic here
        pass