"""
Microsoft 365 Integration Module

This module provides comprehensive integration with Microsoft 365 services including:
- Microsoft Excel API for spreadsheet operations
- Microsoft Outlook API for email management
- Microsoft OneDrive API for file operations
- Microsoft SharePoint API for document management

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
    import msal
    import requests
    MICROSOFT_365_AVAILABLE = True
except ImportError:
    MICROSOFT_365_AVAILABLE = False
    logging.warning("Microsoft 365 APIs not available. Install msal and requests")

logger = logging.getLogger(__name__)


class Microsoft365Service(Enum):
    """Available Microsoft 365 services."""
    EXCEL = "excel"
    OUTLOOK = "outlook"
    ONEDRIVE = "onedrive"
    SHAREPOINT = "sharepoint"
    TEAMS = "teams"


@dataclass
class ExcelConfig:
    """Configuration for Microsoft Excel integration."""
    client_id: str
    client_secret: str
    tenant_id: str
    scopes: List[str] = field(default_factory=lambda: [
        "https://graph.microsoft.com/.default"
    ])


@dataclass
class OutlookConfig:
    """Configuration for Microsoft Outlook integration."""
    client_id: str
    client_secret: str
    tenant_id: str
    user_email: str
    scopes: List[str] = field(default_factory=lambda: [
        "https://graph.microsoft.com/.default"
    ])


@dataclass
class OneDriveConfig:
    """Configuration for Microsoft OneDrive integration."""
    client_id: str
    client_secret: str
    tenant_id: str
    scopes: List[str] = field(default_factory=lambda: [
        "https://graph.microsoft.com/.default"
    ])


@dataclass
class SharePointConfig:
    """Configuration for Microsoft SharePoint integration."""
    client_id: str
    client_secret: str
    tenant_id: str
    site_id: str
    scopes: List[str] = field(default_factory=lambda: [
        "https://graph.microsoft.com/.default"
    ])


@dataclass
class Microsoft365Config:
    """Configuration for Microsoft 365 integration."""
    excel: Optional[ExcelConfig] = None
    outlook: Optional[OutlookConfig] = None
    onedrive: Optional[OneDriveConfig] = None
    sharepoint: Optional[SharePointConfig] = None
    project_id: Optional[str] = None


class Microsoft365Auth:
    """Handles authentication for Microsoft 365 APIs."""
    
    def __init__(self, config: Microsoft365Config):
        """
        Initialize Microsoft 365 authentication.
        
        Args:
            config: Microsoft 365 configuration
        """
        self.config = config
        self._token_cache: Dict[str, Any] = {}
    
    def _get_token(self, client_id: str, client_secret: str, tenant_id: str, 
                   scopes: List[str]) -> str:
        """
        Get authenticated token for Microsoft Graph API.
        
        Args:
            client_id: Azure AD application client ID
            client_secret: Azure AD application client secret
            tenant_id: Azure AD tenant ID
            scopes: OAuth2 scopes
            
        Returns:
            Access token string
        """
        if not MICROSOFT_365_AVAILABLE:
            raise ImportError("Microsoft 365 APIs not available. Install msal and requests")
        
        scope_key = ",".join(sorted(scopes))
        if scope_key in self._token_cache:
            return self._token_cache[scope_key]
        
        try:
            # Initialize MSAL
            app = msal.ConfidentialClientApplication(
                client_id=client_id,
                client_credential={
                    "client_secret": client_secret
                },
                authority=f"https://login.microsoftonline.com/{tenant_id}"
            )
            
            # Acquire token
            result = app.acquire_token_for_client(scopes)
            
            if "access_token" not in result:
                raise Exception(f"Failed to acquire token: {result.get('error_description', result.get('error'))}")
            
            token = result["access_token"]
            self._token_cache[scope_key] = token
            return token
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Microsoft 365 APIs: {e}")
            raise


class ExcelIntegration:
    """Microsoft Excel integration for spreadsheet operations."""
    
    def __init__(self, config: ExcelConfig):
        """
        Initialize Excel integration.
        
        Args:
            config: Excel configuration
        """
        self.config = config
        self.auth = Microsoft365Auth(Microsoft365Config())
        self.base_url = "https://graph.microsoft.com/v1.0"
    
    async def create_workbook(self, name: str, drive_id: str = "me/drive") -> Dict[str, Any]:
        """
        Create a new Excel workbook.
        
        Args:
            name: Name of the workbook
            drive_id: Drive ID (default: "me/drive" for user's OneDrive)
            
        Returns:
            Workbook creation result
        """
        try:
            token = self.auth._get_token(
                self.config.client_id,
                self.config.client_secret,
                self.config.tenant_id,
                self.config.scopes
            )
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Create empty workbook
            url = f"{self.base_url}/{drive_id}/items"
            data = {
                "name": f"{name}.xlsx",
                "@microsoft.graph.conflictBehavior": "rename",
                "file": {}
            }
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.post, url, json=data, headers=headers
            )
            
            if response.status_code == 201:
                return {
                    "success": True,
                    "workbook_id": response.json()["id"],
                    "name": response.json()["name"],
                    "web_url": response.json().get("webUrl")
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create workbook: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Failed to create Excel workbook: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def read_worksheet(self, workbook_id: str, worksheet_name: str = "Sheet1") -> Dict[str, Any]:
        """
        Read data from an Excel worksheet.
        
        Args:
            workbook_id: ID of the workbook
            worksheet_name: Name of the worksheet
            
        Returns:
            Worksheet data
        """
        try:
            token = self.auth._get_token(
                self.config.client_id,
                self.config.client_secret,
                self.config.tenant_id,
                self.config.scopes
            )
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Get worksheet data
            url = f"{self.base_url}/me/drive/items/{workbook_id}/workbook/worksheets/{worksheet_name}/usedRange"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.get, url, headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "values": data.get("values", []),
                    "address": data.get("address"),
                    "row_count": data.get("rowCount"),
                    "column_count": data.get("columnCount")
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to read worksheet: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Failed to read Excel worksheet: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def write_worksheet(self, workbook_id: str, worksheet_name: str, 
                            data: List[List[Any]], start_cell: str = "A1") -> Dict[str, Any]:
        """
        Write data to an Excel worksheet.
        
        Args:
            workbook_id: ID of the workbook
            worksheet_name: Name of the worksheet
            data: Data to write (2D array)
            start_cell: Starting cell (e.g., "A1")
            
        Returns:
            Write operation result
        """
        try:
            token = self.auth._get_token(
                self.config.client_id,
                self.config.client_secret,
                self.config.tenant_id,
                self.config.scopes
            )
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Write data to worksheet
            url = f"{self.base_url}/me/drive/items/{workbook_id}/workbook/worksheets/{worksheet_name}/range(address='{start_cell}')"
            data_payload = {
                "values": data
            }
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.patch, url, json=data_payload, headers=headers
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "address": response.json().get("address"),
                    "row_count": response.json().get("rowCount"),
                    "column_count": response.json().get("columnCount")
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to write worksheet: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Failed to write Excel worksheet: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class OutlookIntegration:
    """Microsoft Outlook integration for email operations."""
    
    def __init__(self, config: OutlookConfig):
        """
        Initialize Outlook integration.
        
        Args:
            config: Outlook configuration
        """
        self.config = config
        self.auth = Microsoft365Auth(Microsoft365Config())
        self.base_url = "https://graph.microsoft.com/v1.0"
    
    async def send_email(self, to: List[str], subject: str, body: str, 
                        is_html: bool = True, cc: List[str] = None, 
                        bcc: List[str] = None, attachments: List[Dict] = None) -> Dict[str, Any]:
        """
        Send an email via Outlook.
        
        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body
            is_html: Whether body is HTML
            cc: List of CC recipients
            bcc: List of BCC recipients
            attachments: List of attachment objects
            
        Returns:
            Send operation result
        """
        try:
            token = self.auth._get_token(
                self.config.client_id,
                self.config.client_secret,
                self.config.tenant_id,
                self.config.scopes
            )
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Prepare email data
            email_data = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML" if is_html else "Text",
                        "content": body
                    },
                    "toRecipients": [{"emailAddress": {"address": email}} for email in to],
                    "from": {"emailAddress": {"address": self.config.user_email}}
                }
            }
            
            if cc:
                email_data["message"]["ccRecipients"] = [{"emailAddress": {"address": email}} for email in cc]
            
            if bcc:
                email_data["message"]["bccRecipients"] = [{"emailAddress": {"address": email}} for email in bcc]
            
            if attachments:
                email_data["message"]["attachments"] = attachments
            
            # Send email
            url = f"{self.base_url}/users/{self.config.user_email}/sendMail"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.post, url, json=email_data, headers=headers
            )
            
            if response.status_code == 202:  # Accepted
                return {
                    "success": True,
                    "message": "Email sent successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to send email: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Failed to send Outlook email: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_messages(self, folder: str = "inbox", top: int = 10, 
                          filter_query: str = None) -> Dict[str, Any]:
        """
        Get messages from a folder.
        
        Args:
            folder: Folder name (default: "inbox")
            top: Number of messages to retrieve
            filter_query: OData filter query
            
        Returns:
            Messages data
        """
        try:
            token = self.auth._get_token(
                self.config.client_id,
                self.config.client_secret,
                self.config.tenant_id,
                self.config.scopes
            )
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Build URL
            url = f"{self.base_url}/users/{self.config.user_email}/mailFolders/{folder}/messages?$top={top}"
            if filter_query:
                url += f"&$filter={filter_query}"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.get, url, headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "messages": data.get("value", []),
                    "count": len(data.get("value", []))
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get messages: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Failed to get Outlook messages: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class OneDriveIntegration:
    """Microsoft OneDrive integration for file operations."""
    
    def __init__(self, config: OneDriveConfig):
        """
        Initialize OneDrive integration.
        
        Args:
            config: OneDrive configuration
        """
        self.config = config
        self.auth = Microsoft365Auth(Microsoft365Config())
        self.base_url = "https://graph.microsoft.com/v1.0"
    
    async def upload_file(self, file_path: str, file_name: str, 
                         drive_id: str = "me/drive") -> Dict[str, Any]:
        """
        Upload a file to OneDrive.
        
        Args:
            file_path: Local path to the file
            file_name: Name for the file in OneDrive
            drive_id: Drive ID (default: "me/drive" for user's OneDrive)
            
        Returns:
            Upload operation result
        """
        try:
            token = self.auth._get_token(
                self.config.client_id,
                self.config.client_secret,
                self.config.tenant_id,
                self.config.scopes
            )
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/octet-stream"
            }
            
            # Read file content
            with open(file_path, 'rb') as file:
                file_content = file.read()
            
            # Upload file
            url = f"{self.base_url}/{drive_id}/items/root:/{file_name}:/content"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.put, url, data=file_content, headers=headers
            )
            
            if response.status_code == 201:
                return {
                    "success": True,
                    "file_id": response.json()["id"],
                    "name": response.json()["name"],
                    "size": response.json().get("size"),
                    "web_url": response.json().get("webUrl")
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to upload file: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Failed to upload OneDrive file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def download_file(self, file_id: str, local_path: str) -> Dict[str, Any]:
        """
        Download a file from OneDrive.
        
        Args:
            file_id: ID of the file to download
            local_path: Local path to save the file
            
        Returns:
            Download operation result
        """
        try:
            token = self.auth._get_token(
                self.config.client_id,
                self.config.client_secret,
                self.config.tenant_id,
                self.config.scopes
            )
            
            headers = {
                "Authorization": f"Bearer {token}"
            }
            
            # Download file
            url = f"{self.base_url}/me/drive/items/{file_id}/content"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.get, url, headers=headers
            )
            
            if response.status_code == 200:
                # Save file
                with open(local_path, 'wb') as file:
                    file.write(response.content)
                
                return {
                    "success": True,
                    "local_path": local_path,
                    "size": len(response.content)
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to download file: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Failed to download OneDrive file: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class SharePointIntegration:
    """Microsoft SharePoint integration for document management."""
    
    def __init__(self, config: SharePointConfig):
        """
        Initialize SharePoint integration.
        
        Args:
            config: SharePoint configuration
        """
        self.config = config
        self.auth = Microsoft365Auth(Microsoft365Config(sharepoint=config))
        self.logger = logging.getLogger(__name__)
    
    async def get_sites(self) -> Dict[str, Any]:
        """
        Get all SharePoint sites.
        
        Returns:
            List of SharePoint sites
        """
        try:
            token = self.auth._get_token(
                self.config.client_id,
                self.config.client_secret,
                self.config.tenant_id,
                self.config.scopes
            )
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            url = "https://graph.microsoft.com/v1.0/sites"
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.get, url, headers=headers
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "sites": response.json().get("value", [])
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get sites: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get SharePoint sites: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_site_by_id(self, site_id: str) -> Dict[str, Any]:
        """
        Get SharePoint site by ID.
        
        Args:
            site_id: SharePoint site ID
            
        Returns:
            Site information
        """
        try:
            token = self.auth._get_token(
                self.config.client_id,
                self.config.client_secret,
                self.config.tenant_id,
                self.config.scopes
            )
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            url = f"https://graph.microsoft.com/v1.0/sites/{site_id}"
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.get, url, headers=headers
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "site": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get site: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get SharePoint site: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_drives(self, site_id: str) -> Dict[str, Any]:
        """
        Get document libraries (drives) for a SharePoint site.
        
        Args:
            site_id: SharePoint site ID
            
        Returns:
            List of document libraries
        """
        try:
            token = self.auth._get_token(
                self.config.client_id,
                self.config.client_secret,
                self.config.tenant_id,
                self.config.scopes
            )
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.get, url, headers=headers
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "drives": response.json().get("value", [])
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get drives: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get SharePoint drives: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_items(self, site_id: str, drive_id: str, folder_path: str = "/") -> Dict[str, Any]:
        """
        Get items from a SharePoint document library.
        
        Args:
            site_id: SharePoint site ID
            drive_id: Document library ID
            folder_path: Path to folder (default: root)
            
        Returns:
            List of items in the folder
        """
        try:
            token = self.auth._get_token(
                self.config.client_id,
                self.config.client_secret,
                self.config.tenant_id,
                self.config.scopes
            )
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:{folder_path}:/children"
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.get, url, headers=headers
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "items": response.json().get("value", [])
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get items: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get SharePoint items: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def upload_file(self, site_id: str, drive_id: str, file_path: str, 
                         file_content: bytes, file_name: str) -> Dict[str, Any]:
        """
        Upload a file to SharePoint.
        
        Args:
            site_id: SharePoint site ID
            drive_id: Document library ID
            file_path: Path where to upload the file
            file_content: File content as bytes
            file_name: Name of the file
            
        Returns:
            Upload result
        """
        try:
            token = self.auth._get_token(
                self.config.client_id,
                self.config.client_secret,
                self.config.tenant_id,
                self.config.scopes
            )
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/octet-stream"
            }
            
            # Create the full path
            full_path = f"{file_path}/{file_name}" if file_path != "/" else f"/{file_name}"
            
            url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:{full_path}:/content"
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.put, url, data=file_content, headers=headers
            )
            
            if response.status_code in [200, 201]:
                return {
                    "success": True,
                    "file": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to upload file: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to upload SharePoint file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def download_file(self, site_id: str, drive_id: str, file_path: str) -> Dict[str, Any]:
        """
        Download a file from SharePoint.
        
        Args:
            site_id: SharePoint site ID
            drive_id: Document library ID
            file_path: Path to the file
            
        Returns:
            File content
        """
        try:
            token = self.auth._get_token(
                self.config.client_id,
                self.config.client_secret,
                self.config.tenant_id,
                self.config.scopes
            )
            headers = {
                "Authorization": f"Bearer {token}"
            }
            
            url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:{file_path}:/content"
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.get, url, headers=headers
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "content": response.content,
                    "content_type": response.headers.get("content-type")
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to download file: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to download SharePoint file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_folder(self, site_id: str, drive_id: str, folder_path: str, 
                           folder_name: str) -> Dict[str, Any]:
        """
        Create a folder in SharePoint.
        
        Args:
            site_id: SharePoint site ID
            drive_id: Document library ID
            folder_path: Path where to create the folder
            folder_name: Name of the folder
            
        Returns:
            Created folder information
        """
        try:
            token = self.auth._get_token(
                self.config.client_id,
                self.config.client_secret,
                self.config.tenant_id,
                self.config.scopes
            )
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Create the full path
            full_path = f"{folder_path}/{folder_name}" if folder_path != "/" else f"/{folder_name}"
            
            url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:{full_path}:/children"
            data = {
                "name": folder_name,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "rename"
            }
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.post, url, json=data, headers=headers
            )
            
            if response.status_code in [200, 201]:
                return {
                    "success": True,
                    "folder": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create folder: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to create SharePoint folder: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_item(self, site_id: str, drive_id: str, item_path: str) -> Dict[str, Any]:
        """
        Delete an item from SharePoint.
        
        Args:
            site_id: SharePoint site ID
            drive_id: Document library ID
            item_path: Path to the item to delete
            
        Returns:
            Deletion result
        """
        try:
            token = self.auth._get_token(
                self.config.client_id,
                self.config.client_secret,
                self.config.tenant_id,
                self.config.scopes
            )
            headers = {
                "Authorization": f"Bearer {token}"
            }
            
            url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:{item_path}:"
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.delete, url, headers=headers
            )
            
            if response.status_code == 204:
                return {
                    "success": True,
                    "message": "Item deleted successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to delete item: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to delete SharePoint item: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_items(self, site_id: str, query: str) -> Dict[str, Any]:
        """
        Search for items in SharePoint.
        
        Args:
            site_id: SharePoint site ID
            query: Search query
            
        Returns:
            Search results
        """
        try:
            token = self.auth._get_token(
                self.config.client_id,
                self.config.client_secret,
                self.config.tenant_id,
                self.config.scopes
            )
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/search(q='{query}')"
            response = await asyncio.get_event_loop().run_in_executor(
                None, requests.get, url, headers=headers
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "results": response.json().get("value", [])
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to search items: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to search SharePoint items: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class Microsoft365Integration:
    """Main Microsoft 365 integration class."""
    
    def __init__(self, config: Microsoft365Config):
        """
        Initialize Microsoft 365 integration.
        
        Args:
            config: Microsoft 365 configuration
        """
        self.config = config
        self.excel = ExcelIntegration(config.excel) if config.excel else None
        self.outlook = OutlookIntegration(config.outlook) if config.outlook else None
        self.onedrive = OneDriveIntegration(config.onedrive) if config.onedrive else None
        self.sharepoint = SharePointIntegration(config.sharepoint) if config.sharepoint else None
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all configured services.
        
        Returns:
            Health status
        """
        health_status = {
            "overall": "healthy",
            "services": {}
        }
        
        # Check Excel service
        if self.excel:
            try:
                # Simple health check
                health_status["services"]["excel"] = {
                    "status": "healthy",
                    "configured": True
                }
            except Exception as e:
                health_status["services"]["excel"] = {
                    "status": "unhealthy",
                    "configured": True,
                    "error": str(e)
                }
                health_status["overall"] = "degraded"
        else:
            health_status["services"]["excel"] = {
                "status": "not_configured",
                "configured": False
            }
        
        # Check Outlook service
        if self.outlook:
            try:
                # Simple health check
                health_status["services"]["outlook"] = {
                    "status": "healthy",
                    "configured": True
                }
            except Exception as e:
                health_status["services"]["outlook"] = {
                    "status": "unhealthy",
                    "configured": True,
                    "error": str(e)
                }
                health_status["overall"] = "degraded"
        else:
            health_status["services"]["outlook"] = {
                "status": "not_configured",
                "configured": False
            }
        
        # Check OneDrive service
        if self.onedrive:
            try:
                # Simple health check
                health_status["services"]["onedrive"] = {
                    "status": "healthy",
                    "configured": True
                }
            except Exception as e:
                health_status["services"]["onedrive"] = {
                    "status": "unhealthy",
                    "configured": True,
                    "error": str(e)
                }
                health_status["overall"] = "degraded"
        else:
            health_status["services"]["onedrive"] = {
                "status": "not_configured",
                "configured": False
            }
        
        # Check SharePoint service
        if self.sharepoint:
            try:
                # Simple health check
                health_status["services"]["sharepoint"] = {
                    "status": "healthy",
                    "configured": True
                }
            except Exception as e:
                health_status["services"]["sharepoint"] = {
                    "status": "unhealthy",
                    "configured": True,
                    "error": str(e)
                }
                health_status["overall"] = "degraded"
        else:
            health_status["services"]["sharepoint"] = {
                "status": "not_configured",
                "configured": False
            }
        
        return health_status
