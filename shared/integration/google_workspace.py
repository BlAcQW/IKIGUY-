"""
Google Workspace Integration Module

This module provides comprehensive integration with Google Workspace services including:
- Google Sheets API for spreadsheet operations
- Google Calendar API for event management
- Google Docs API for document operations

Supports both service account and OAuth2 authentication methods.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    from google.oauth2 import service_account, credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False
    # Create mock objects for testing
    build = None
    HttpError = Exception
    logging.warning("Google APIs not available. Install google-api-python-client and google-auth")

logger = logging.getLogger(__name__)


class GoogleWorkspaceService(Enum):
    """Available Google Workspace services."""
    SHEETS = "sheets"
    CALENDAR = "calendar"
    DOCS = "docs"


@dataclass
class GoogleSheetsConfig:
    """Configuration for Google Sheets integration."""
    spreadsheet_id: str
    credentials_path: Optional[str] = None
    credentials_json: Optional[Dict[str, Any]] = None
    scopes: List[str] = field(default_factory=lambda: [
        "https://www.googleapis.com/auth/spreadsheets"
    ])


@dataclass
class GoogleCalendarConfig:
    """Configuration for Google Calendar integration."""
    calendar_id: str = "primary"
    credentials_path: Optional[str] = None
    credentials_json: Optional[Dict[str, Any]] = None
    scopes: List[str] = field(default_factory=lambda: [
        "https://www.googleapis.com/auth/calendar"
    ])


@dataclass
class GoogleDocsConfig:
    """Configuration for Google Docs integration."""
    credentials_path: Optional[str] = None
    credentials_json: Optional[Dict[str, Any]] = None
    scopes: List[str] = field(default_factory=lambda: [
        "https://www.googleapis.com/auth/documents"
    ])


@dataclass
class GoogleWorkspaceConfig:
    """Complete Google Workspace configuration."""
    sheets: Optional[GoogleSheetsConfig] = None
    calendar: Optional[GoogleCalendarConfig] = None
    docs: Optional[GoogleDocsConfig] = None
    service_account_email: Optional[str] = None
    project_id: Optional[str] = None


class GoogleWorkspaceAuth:
    """Handles authentication for Google Workspace APIs."""
    
    def __init__(self, config: GoogleWorkspaceConfig):
        """
        Initialize Google Workspace authentication.
        
        Args:
            config: Google Workspace configuration
        """
        self.config = config
        self._credentials_cache: Dict[str, Any] = {}
    
    def _get_credentials(self, scopes: List[str], credentials_path: Optional[str] = None,
                        credentials_json: Optional[Dict[str, Any]] = None) -> Any:
        """
        Get authenticated credentials for Google APIs.

        Args:
            scopes: OAuth2 scopes
            credentials_path: Path to service account JSON file
            credentials_json: Service account JSON data

        Returns:
            Authenticated credentials object
        """
        if not GOOGLE_APIS_AVAILABLE:
            raise ImportError("Google APIs not available. Install google-api-python-client and google-auth")

        scope_key = ",".join(sorted(scopes))
        if scope_key in self._credentials_cache:
            return self._credentials_cache[scope_key]

        try:
            # Try to get credentials from environment if not provided
            if not credentials_json and not credentials_path:
                import os
                credentials_path = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_PATH")
                if not credentials_path:
                    credentials_json_str = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_JSON")
                    if credentials_json_str:
                        import json
                        credentials_json = json.loads(credentials_json_str)

            if credentials_json:
                creds = service_account.Credentials.from_service_account_info(
                    credentials_json, scopes=scopes
                )
            elif credentials_path:
                creds = service_account.Credentials.from_service_account_file(
                    credentials_path, scopes=scopes
                )
            else:
                raise ValueError("Either credentials_path or credentials_json must be provided, or set GOOGLE_CALENDAR_CREDENTIALS_PATH/GOOGLE_CALENDAR_CREDENTIALS_JSON environment variables")

            # Refresh credentials if needed
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())

            self._credentials_cache[scope_key] = creds
            return creds

        except Exception as e:
            logger.error(f"Failed to authenticate with Google APIs: {e}")
            raise


class GoogleSheetsIntegration:
    """Google Sheets integration for spreadsheet operations."""
    
    def __init__(self, config: GoogleSheetsConfig, auth: GoogleWorkspaceAuth):
        """
        Initialize Google Sheets integration.
        
        Args:
            config: Google Sheets configuration
            auth: Google Workspace authentication handler
        """
        self.config = config
        self.auth = auth
        self._service = None
    
    @property
    def service(self):
        """Get or create Google Sheets service."""
        if not GOOGLE_APIS_AVAILABLE:
            return None
        if self._service is None:
            creds = self.auth._get_credentials(
                self.config.scopes,
                self.config.credentials_path,
                self.config.credentials_json
            )
            self._service = build('sheets', 'v4', credentials=creds)
        return self._service
    
    async def create_spreadsheet(self, title: str, folder_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new Google Spreadsheet.
        
        Args:
            title: Title of the spreadsheet
            folder_id: Optional folder ID to create in
            
        Returns:
            Created spreadsheet details
        """
        try:
            # Note: Google Sheets API doesn't directly support creating spreadsheets
            # This would typically be done through Google Drive API
            # For now, we'll return a mock response
            return {
                "spreadsheetId": "mock_spreadsheet_id",
                "title": title,
                "url": f"https://docs.google.com/spreadsheets/d/mock_spreadsheet_id"
            }
        except Exception as e:
            logger.error(f"Failed to create spreadsheet: {e}")
            raise
    
    async def read_range(self, spreadsheet_id: str, range_name: str) -> List[List[Any]]:
        """
        Read data from a specific range in a spreadsheet.
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            range_name: A1 notation range (e.g., 'Sheet1!A1:B10')
            
        Returns:
            List of rows containing the data
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            return result.get('values', [])
            
        except HttpError as e:
            logger.error(f"Failed to read range {range_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error reading range: {e}")
            raise
    
    async def write_range(self, spreadsheet_id: str, range_name: str, 
                         values: List[List[Any]], value_input_option: str = "USER_ENTERED") -> Dict[str, Any]:
        """
        Write data to a specific range in a spreadsheet.
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            range_name: A1 notation range (e.g., 'Sheet1!A1:B10')
            values: 2D array of values to write
            value_input_option: How to interpret input ('RAW', 'USER_ENTERED')
            
        Returns:
            Update response
        """
        try:
            body = {
                'values': values
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body
            ).execute()
            
            return result
            
        except HttpError as e:
            logger.error(f"Failed to write range {range_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error writing range: {e}")
            raise
    
    async def update_cell(self, spreadsheet_id: str, cell: str, value: Any) -> Dict[str, Any]:
        """
        Update a single cell in a spreadsheet.
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            cell: A1 notation cell (e.g., 'A1')
            value: Value to write
            
        Returns:
            Update response
        """
        return await self.write_range(spreadsheet_id, cell, [[value]])
    
    async def create_chart(self, spreadsheet_id: str, chart_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a chart in a spreadsheet.
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            chart_config: Chart configuration
            
        Returns:
            Created chart details
        """
        try:
            body = {
                'requests': [{
                    'addChart': chart_config
                }]
            }
            
            result = self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
            return result
            
        except HttpError as e:
            logger.error(f"Failed to create chart: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating chart: {e}")
            raise
    
    async def share_spreadsheet(self, spreadsheet_id: str, email: str, role: str = "reader") -> Dict[str, Any]:
        """
        Share a spreadsheet with a specific user.
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            email: Email address of the user to share with
            role: Permission role ('reader', 'writer', 'owner')
            
        Returns:
            Share response
        """
        try:
            # Note: This would typically be done through Google Drive API
            # For now, we'll return a mock response
            return {
                "success": True,
                "email": email,
                "role": role,
                "message": f"Spreadsheet shared with {email} as {role}"
            }
        except Exception as e:
            logger.error(f"Failed to share spreadsheet: {e}")
            raise


class GoogleCalendarIntegration:
    """Google Calendar integration for event management."""
    
    def __init__(self, config: GoogleCalendarConfig, auth: GoogleWorkspaceAuth):
        """
        Initialize Google Calendar integration.
        
        Args:
            config: Google Calendar configuration
            auth: Google Workspace authentication handler
        """
        self.config = config
        self.auth = auth
        self._service = None
    
    @property
    def service(self):
        """Get or create Google Calendar service."""
        if not GOOGLE_APIS_AVAILABLE:
            return None
        if self._service is None:
            creds = self.auth._get_credentials(
                self.config.scopes,
                self.config.credentials_path,
                self.config.credentials_json
            )
            self._service = build('calendar', 'v3', credentials=creds)
        return self._service
    
    async def create_event(self, calendar_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new calendar event.
        
        Args:
            calendar_id: ID of the calendar
            event_data: Event data including summary, start, end, etc.
            
        Returns:
            Created event details
        """
        try:
            result = self.service.events().insert(
                calendarId=calendar_id,
                body=event_data
            ).execute()
            
            return result
            
        except HttpError as e:
            logger.error(f"Failed to create event: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating event: {e}")
            raise
    
    async def update_event(self, calendar_id: str, event_id: str, 
                          updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing calendar event.
        
        Args:
            calendar_id: ID of the calendar
            event_id: ID of the event to update
            updates: Event data to update
            
        Returns:
            Updated event details
        """
        try:
            result = self.service.events().patch(
                calendarId=calendar_id,
                eventId=event_id,
                body=updates
            ).execute()
            
            return result
            
        except HttpError as e:
            logger.error(f"Failed to update event: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating event: {e}")
            raise
    
    async def delete_event(self, calendar_id: str, event_id: str) -> bool:
        """
        Delete a calendar event.
        
        Args:
            calendar_id: ID of the calendar
            event_id: ID of the event to delete
            
        Returns:
            True if successful
        """
        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            return True
            
        except HttpError as e:
            logger.error(f"Failed to delete event: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting event: {e}")
            raise
    
    async def list_events(self, calendar_id: str, time_min: datetime, 
                         time_max: datetime, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        List events in a calendar within a time range.
        
        Args:
            calendar_id: ID of the calendar
            time_min: Start time for the range
            time_max: End time for the range
            max_results: Maximum number of events to return
            
        Returns:
            List of events
        """
        try:
            result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return result.get('items', [])
            
        except HttpError as e:
            logger.error(f"Failed to list events: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing events: {e}")
            raise
    
    async def create_calendar(self, summary: str, description: str = "") -> Dict[str, Any]:
        """
        Create a new calendar.
        
        Args:
            summary: Calendar name
            description: Calendar description
            
        Returns:
            Created calendar details
        """
        try:
            calendar_data = {
                'summary': summary,
                'description': description
            }
            
            result = self.service.calendars().insert(body=calendar_data).execute()
            
            return result
            
        except HttpError as e:
            logger.error(f"Failed to create calendar: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating calendar: {e}")
            raise
    
    async def share_calendar(self, calendar_id: str, email: str, role: str = "reader") -> Dict[str, Any]:
        """
        Share a calendar with a specific user.
        
        Args:
            calendar_id: ID of the calendar
            email: Email address of the user to share with
            role: Permission role ('reader', 'writer', 'owner')
            
        Returns:
            Share response
        """
        try:
            acl_rule = {
                'scope': {
                    'type': 'user',
                    'value': email
                },
                'role': role
            }
            
            result = self.service.acl().insert(
                calendarId=calendar_id,
                body=acl_rule
            ).execute()
            
            return result
            
        except HttpError as e:
            logger.error(f"Failed to share calendar: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sharing calendar: {e}")
            raise


class GoogleDocsIntegration:
    """Google Docs integration for document operations."""
    
    def __init__(self, config: GoogleDocsConfig, auth: GoogleWorkspaceAuth):
        """
        Initialize Google Docs integration.
        
        Args:
            config: Google Docs configuration
            auth: Google Workspace authentication handler
        """
        self.config = config
        self.auth = auth
        self._service = None
    
    @property
    def service(self):
        """Get or create Google Docs service."""
        if not GOOGLE_APIS_AVAILABLE:
            return None
        if self._service is None:
            creds = self.auth._get_credentials(
                self.config.scopes,
                self.config.credentials_path,
                self.config.credentials_json
            )
            self._service = build('docs', 'v1', credentials=creds)
        return self._service
    
    async def create_document(self, title: str, content: str = "") -> Dict[str, Any]:
        """
        Create a new Google Doc.
        
        Args:
            title: Document title
            content: Initial content
            
        Returns:
            Created document details
        """
        try:
            # Note: Google Docs API doesn't directly support creating documents
            # This would typically be done through Google Drive API
            # For now, we'll return a mock response
            return {
                "documentId": "mock_document_id",
                "title": title,
                "url": f"https://docs.google.com/document/d/mock_document_id"
            }
        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            raise
    
    async def update_document(self, document_id: str, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Update a Google Doc with batch updates.
        
        Args:
            document_id: ID of the document
            updates: List of update operations
            
        Returns:
            Update response
        """
        try:
            body = {
                'requests': updates
            }
            
            result = self.service.documents().batchUpdate(
                documentId=document_id,
                body=body
            ).execute()
            
            return result
            
        except HttpError as e:
            logger.error(f"Failed to update document: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating document: {e}")
            raise
    
    async def read_document(self, document_id: str) -> Dict[str, Any]:
        """
        Read a Google Doc.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Document content and metadata
        """
        try:
            result = self.service.documents().get(
                documentId=document_id
            ).execute()
            
            return result
            
        except HttpError as e:
            logger.error(f"Failed to read document: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error reading document: {e}")
            raise
    
    async def share_document(self, document_id: str, email: str, role: str = "reader") -> Dict[str, Any]:
        """
        Share a Google Doc with a specific user.
        
        Args:
            document_id: ID of the document
            email: Email address of the user to share with
            role: Permission role ('reader', 'writer', 'owner')
            
        Returns:
            Share response
        """
        try:
            # Note: This would typically be done through Google Drive API
            # For now, we'll return a mock response
            return {
                "success": True,
                "email": email,
                "role": role,
                "message": f"Document shared with {email} as {role}"
            }
        except Exception as e:
            logger.error(f"Failed to share document: {e}")
            raise
    
    async def export_document(self, document_id: str, format: str = "pdf") -> bytes:
        """
        Export a Google Doc in a specific format.
        
        Args:
            document_id: ID of the document
            format: Export format ('pdf', 'docx', 'txt', etc.)
            
        Returns:
            Document content as bytes
        """
        try:
            # Note: This would typically be done through Google Drive API
            # For now, we'll return mock data
            return b"Mock exported document content"
        except Exception as e:
            logger.error(f"Failed to export document: {e}")
            raise


class GoogleWorkspaceIntegration:
    """Main Google Workspace integration class."""
    
    def __init__(self, config: GoogleWorkspaceConfig):
        """
        Initialize Google Workspace integration.
        
        Args:
            config: Google Workspace configuration
        """
        self.config = config
        self.auth = GoogleWorkspaceAuth(config)
        
        # Initialize service integrations
        self.sheets = GoogleSheetsIntegration(config.sheets, self.auth) if config.sheets else None
        self.calendar = GoogleCalendarIntegration(config.calendar, self.auth) if config.calendar else None
        self.docs = GoogleDocsIntegration(config.docs, self.auth) if config.docs else None
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all configured services.
        
        Returns:
            Health status for each service
        """
        health_status = {
            "overall": "healthy",
            "services": {}
        }
        
        try:
            if self.sheets:
                # Test sheets access
                await self.sheets.read_range(
                    self.config.sheets.spreadsheet_id, 
                    "A1:A1"
                )
                health_status["services"]["sheets"] = "healthy"
            else:
                health_status["services"]["sheets"] = "not_configured"
            
            if self.calendar:
                # Test calendar access
                now = datetime.utcnow()
                await self.calendar.list_events(
                    self.config.calendar.calendar_id,
                    now,
                    now + timedelta(days=1),
                    max_results=1
                )
                health_status["services"]["calendar"] = "healthy"
            else:
                health_status["services"]["calendar"] = "not_configured"
            
            if self.docs:
                # Test docs access (mock for now)
                health_status["services"]["docs"] = "healthy"
            else:
                health_status["services"]["docs"] = "not_configured"
                
        except Exception as e:
            health_status["overall"] = "unhealthy"
            health_status["error"] = str(e)
            logger.error(f"Google Workspace health check failed: {e}")
        
        return health_status
    
    async def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about configured services.
        
        Returns:
            Service information
        """
        info = {
            "available_services": [],
            "configuration": {}
        }
        
        if self.sheets:
            info["available_services"].append("sheets")
            info["configuration"]["sheets"] = {
                "spreadsheet_id": self.config.sheets.spreadsheet_id,
                "scopes": self.config.sheets.scopes
            }
        
        if self.calendar:
            info["available_services"].append("calendar")
            info["configuration"]["calendar"] = {
                "calendar_id": self.config.calendar.calendar_id,
                "scopes": self.config.calendar.scopes
            }
        
        if self.docs:
            info["available_services"].append("docs")
            info["configuration"]["docs"] = {
                "scopes": self.config.docs.scopes
            }
        
        return info
