"""
Google Drive Integration Module

This module provides integration with Google Drive for file management,
document storage, and cloud storage automation.
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
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
    import io
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False
    logging.warning("Google Drive APIs not available. Install google-api-python-client and google-auth")

logger = logging.getLogger(__name__)


class GoogleDriveFileType(Enum):
    """Google Drive file types."""
    FOLDER = "application/vnd.google-apps.folder"
    DOCUMENT = "application/vnd.google-apps.document"
    SPREADSHEET = "application/vnd.google-apps.spreadsheet"
    PRESENTATION = "application/vnd.google-apps.presentation"
    FORM = "application/vnd.google-apps.form"
    DRAWING = "application/vnd.google-apps.drawing"
    SITE = "application/vnd.google-apps.site"
    MAP = "application/vnd.google-apps.map"
    SCRIPT = "application/vnd.google-apps.script"
    PDF = "application/pdf"
    TEXT = "text/plain"
    IMAGE = "image/*"
    VIDEO = "video/*"
    AUDIO = "audio/*"


class GoogleDrivePermissionRole(Enum):
    """Google Drive permission roles."""
    OWNER = "owner"
    WRITER = "writer"
    COMMENTER = "commenter"
    READER = "reader"


@dataclass
class GoogleDriveConfig:
    """Configuration for Google Drive integration."""

    service_account_file: Optional[str] = None
    """Path to service account JSON file."""

    scopes: List[str] = field(default_factory=lambda: [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive.metadata.readonly"
    ])
    """Google Drive API scopes."""

    timeout: int = 30
    """Request timeout in seconds."""

    verify_ssl: bool = True
    """Verify SSL certificates."""


@dataclass
class GoogleDriveFile:
    """Google Drive file data structure."""
    
    id: str
    """File ID."""
    
    name: str
    """File name."""
    
    mime_type: GoogleDriveFileType
    """File MIME type."""
    
    size: Optional[int] = None
    """File size in bytes."""
    
    parents: List[str] = field(default_factory=list)
    """Parent folder IDs."""
    
    web_view_link: Optional[str] = None
    """Web view link."""
    
    web_content_link: Optional[str] = None
    """Web content link."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""
    
    modified_by_me_at: Optional[datetime] = None
    """Last modified by me timestamp."""
    
    shared: bool = False
    """Whether file is shared."""
    
    trashed: bool = False
    """Whether file is in trash."""


@dataclass
class GoogleDrivePermission:
    """Google Drive permission data structure."""
    
    id: str
    """Permission ID."""
    
    type: str
    """Permission type (user, group, domain, anyone)."""
    
    role: GoogleDrivePermissionRole
    """Permission role."""
    
    email_address: Optional[str] = None
    """Email address for user/group permissions."""
    
    domain: Optional[str] = None
    """Domain for domain permissions."""
    
    allow_file_discovery: bool = True
    """Whether to allow file discovery."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""


class GoogleDriveIntegration:
    """Google Drive integration for file management and storage."""
    
    def __init__(self, config: GoogleDriveConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Drive service."""
        try:
            # Try to get credentials from environment if not provided
            service_account_file = self.config.service_account_file
            if not service_account_file:
                import os
                service_account_file = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_PATH")
                if not service_account_file:
                    credentials_json_str = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_JSON")
                    if credentials_json_str:
                        import json
                        credentials_json = json.loads(credentials_json_str)
                        credentials = Credentials.from_service_account_info(
                            credentials_json, scopes=self.config.scopes
                        )
                    else:
                        raise ValueError("No Google service account credentials found in config or environment")
                else:
                    credentials = Credentials.from_service_account_file(
                        service_account_file, scopes=self.config.scopes
                    )
            else:
                credentials = Credentials.from_service_account_file(
                    service_account_file, scopes=self.config.scopes
                )

            self.service = build('drive', 'v3', credentials=credentials)
            self.logger.info("Successfully initialized Google Drive service")

        except Exception as e:
            self.logger.error(f"Failed to initialize Google Drive service: {e}")
            raise
    
    async def create_folder(
        self,
        name: str,
        parent_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> GoogleDriveFile:
        """
        Create a folder.
        
        Args:
            name: Folder name
            parent_id: Parent folder ID
            description: Folder description
            
        Returns:
            Folder data
        """
        try:
            file_metadata = {
                'name': name,
                'mimeType': GoogleDriveFileType.FOLDER.value
            }
            
            if parent_id:
                file_metadata['parents'] = [parent_id]
            if description:
                file_metadata['description'] = description
            
            file = self.service.files().create(
                body=file_metadata,
                fields='id,name,mimeType,size,parents,webViewLink,webContentLink,createdTime,modifiedTime,modifiedByMeTime,shared,trashed'
            ).execute()
            
            return GoogleDriveFile(
                id=file['id'],
                name=file['name'],
                mime_type=GoogleDriveFileType(file['mimeType']),
                size=file.get('size'),
                parents=file.get('parents', []),
                web_view_link=file.get('webViewLink'),
                web_content_link=file.get('webContentLink'),
                created_at=datetime.fromisoformat(file['createdTime'].replace('Z', '+00:00')) if file.get('createdTime') else None,
                updated_at=datetime.fromisoformat(file['modifiedTime'].replace('Z', '+00:00')) if file.get('modifiedTime') else None,
                modified_by_me_at=datetime.fromisoformat(file['modifiedByMeTime'].replace('Z', '+00:00')) if file.get('modifiedByMeTime') else None,
                shared=file.get('shared', False),
                trashed=file.get('trashed', False)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create folder: {e}")
            raise
    
    async def upload_file(
        self,
        name: str,
        content: Union[str, bytes],
        mime_type: GoogleDriveFileType,
        parent_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> GoogleDriveFile:
        """
        Upload a file.
        
        Args:
            name: File name
            content: File content
            mime_type: File MIME type
            parent_id: Parent folder ID
            description: File description
            
        Returns:
            File data
        """
        try:
            file_metadata = {
                'name': name,
                'mimeType': mime_type.value
            }
            
            if parent_id:
                file_metadata['parents'] = [parent_id]
            if description:
                file_metadata['description'] = description
            
            # Convert content to bytes if it's a string
            if isinstance(content, str):
                content = content.encode('utf-8')
            
            media = MediaIoBaseUpload(
                io.BytesIO(content),
                mimetype=mime_type.value,
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,mimeType,size,parents,webViewLink,webContentLink,createdTime,modifiedTime,modifiedByMeTime,shared,trashed'
            ).execute()
            
            return GoogleDriveFile(
                id=file['id'],
                name=file['name'],
                mime_type=GoogleDriveFileType(file['mimeType']),
                size=file.get('size'),
                parents=file.get('parents', []),
                web_view_link=file.get('webViewLink'),
                web_content_link=file.get('webContentLink'),
                created_at=datetime.fromisoformat(file['createdTime'].replace('Z', '+00:00')) if file.get('createdTime') else None,
                updated_at=datetime.fromisoformat(file['modifiedTime'].replace('Z', '+00:00')) if file.get('modifiedTime') else None,
                modified_by_me_at=datetime.fromisoformat(file['modifiedByMeTime'].replace('Z', '+00:00')) if file.get('modifiedByMeTime') else None,
                shared=file.get('shared', False),
                trashed=file.get('trashed', False)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to upload file: {e}")
            raise
    
    async def get_file(self, file_id: str) -> GoogleDriveFile:
        """
        Get file details.
        
        Args:
            file_id: File ID
            
        Returns:
            File data
        """
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='id,name,mimeType,size,parents,webViewLink,webContentLink,createdTime,modifiedTime,modifiedByMeTime,shared,trashed'
            ).execute()
            
            return GoogleDriveFile(
                id=file['id'],
                name=file['name'],
                mime_type=GoogleDriveFileType(file['mimeType']),
                size=file.get('size'),
                parents=file.get('parents', []),
                web_view_link=file.get('webViewLink'),
                web_content_link=file.get('webContentLink'),
                created_at=datetime.fromisoformat(file['createdTime'].replace('Z', '+00:00')) if file.get('createdTime') else None,
                updated_at=datetime.fromisoformat(file['modifiedTime'].replace('Z', '+00:00')) if file.get('modifiedTime') else None,
                modified_by_me_at=datetime.fromisoformat(file['modifiedByMeTime'].replace('Z', '+00:00')) if file.get('modifiedByMeTime') else None,
                shared=file.get('shared', False),
                trashed=file.get('trashed', False)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get file: {e}")
            raise
    
    async def download_file(self, file_id: str) -> bytes:
        """
        Download file content.
        
        Args:
            file_id: File ID
            
        Returns:
            File content as bytes
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                self.logger.info(f"Download {int(status.progress() * 100)}%")
            
            return file.getvalue()
            
        except Exception as e:
            self.logger.error(f"Failed to download file: {e}")
            raise
    
    async def list_files(
        self,
        folder_id: Optional[str] = None,
        query: Optional[str] = None,
        page_size: int = 100
    ) -> List[GoogleDriveFile]:
        """
        List files.
        
        Args:
            folder_id: Parent folder ID
            query: Search query
            page_size: Number of files to return
            
        Returns:
            List of files
        """
        try:
            # Build query
            q_parts = []
            
            if folder_id:
                q_parts.append(f"'{folder_id}' in parents")
            else:
                q_parts.append("'root' in parents")
            
            if query:
                q_parts.append(f"name contains '{query}'")
            
            q_parts.append("trashed = false")
            
            q = " and ".join(q_parts)
            
            results = self.service.files().list(
                q=q,
                pageSize=page_size,
                fields="nextPageToken, files(id,name,mimeType,size,parents,webViewLink,webContentLink,createdTime,modifiedTime,modifiedByMeTime,shared,trashed)"
            ).execute()
            
            files = []
            for file in results.get('files', []):
                drive_file = GoogleDriveFile(
                    id=file['id'],
                    name=file['name'],
                    mime_type=GoogleDriveFileType(file['mimeType']),
                    size=file.get('size'),
                    parents=file.get('parents', []),
                    web_view_link=file.get('webViewLink'),
                    web_content_link=file.get('webContentLink'),
                    created_at=datetime.fromisoformat(file['createdTime'].replace('Z', '+00:00')) if file.get('createdTime') else None,
                    updated_at=datetime.fromisoformat(file['modifiedTime'].replace('Z', '+00:00')) if file.get('modifiedTime') else None,
                    modified_by_me_at=datetime.fromisoformat(file['modifiedByMeTime'].replace('Z', '+00:00')) if file.get('modifiedByMeTime') else None,
                    shared=file.get('shared', False),
                    trashed=file.get('trashed', False)
                )
                files.append(drive_file)
            
            return files
            
        except Exception as e:
            self.logger.error(f"Failed to list files: {e}")
            raise
    
    async def update_file(
        self,
        file_id: str,
        name: Optional[str] = None,
        content: Optional[Union[str, bytes]] = None,
        description: Optional[str] = None
    ) -> GoogleDriveFile:
        """
        Update a file.
        
        Args:
            file_id: File ID
            name: New file name
            content: New file content
            description: New file description
            
        Returns:
            Updated file data
        """
        try:
            file_metadata = {}
            
            if name:
                file_metadata['name'] = name
            if description:
                file_metadata['description'] = description
            
            if content:
                # Convert content to bytes if it's a string
                if isinstance(content, str):
                    content = content.encode('utf-8')
                
                media = MediaIoBaseUpload(
                    io.BytesIO(content),
                    resumable=True
                )
                
                file = self.service.files().update(
                    fileId=file_id,
                    body=file_metadata,
                    media_body=media,
                    fields='id,name,mimeType,size,parents,webViewLink,webContentLink,createdTime,modifiedTime,modifiedByMeTime,shared,trashed'
                ).execute()
            else:
                file = self.service.files().update(
                    fileId=file_id,
                    body=file_metadata,
                    fields='id,name,mimeType,size,parents,webViewLink,webContentLink,createdTime,modifiedTime,modifiedByMeTime,shared,trashed'
                ).execute()
            
            return GoogleDriveFile(
                id=file['id'],
                name=file['name'],
                mime_type=GoogleDriveFileType(file['mimeType']),
                size=file.get('size'),
                parents=file.get('parents', []),
                web_view_link=file.get('webViewLink'),
                web_content_link=file.get('webContentLink'),
                created_at=datetime.fromisoformat(file['createdTime'].replace('Z', '+00:00')) if file.get('createdTime') else None,
                updated_at=datetime.fromisoformat(file['modifiedTime'].replace('Z', '+00:00')) if file.get('modifiedTime') else None,
                modified_by_me_at=datetime.fromisoformat(file['modifiedByMeTime'].replace('Z', '+00:00')) if file.get('modifiedByMeTime') else None,
                shared=file.get('shared', False),
                trashed=file.get('trashed', False)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update file: {e}")
            raise
    
    async def delete_file(self, file_id: str) -> bool:
        """
        Delete a file.
        
        Args:
            file_id: File ID
            
        Returns:
            True if successful
        """
        try:
            self.service.files().delete(fileId=file_id).execute()
            self.logger.info(f"Successfully deleted file: {file_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete file: {e}")
            return False
    
    async def share_file(
        self,
        file_id: str,
        email: str,
        role: GoogleDrivePermissionRole,
        send_notification: bool = True
    ) -> GoogleDrivePermission:
        """
        Share a file.
        
        Args:
            file_id: File ID
            email: Email address
            role: Permission role
            send_notification: Whether to send notification email
            
        Returns:
            Permission data
        """
        try:
            permission = {
                'type': 'user',
                'role': role.value,
                'emailAddress': email
            }
            
            result = self.service.permissions().create(
                fileId=file_id,
                body=permission,
                sendNotificationEmail=send_notification,
                fields='id,type,role,emailAddress,domain,allowFileDiscovery,createdTime'
            ).execute()
            
            return GoogleDrivePermission(
                id=result['id'],
                type=result['type'],
                role=GoogleDrivePermissionRole(result['role']),
                email_address=result.get('emailAddress'),
                domain=result.get('domain'),
                allow_file_discovery=result.get('allowFileDiscovery', True),
                created_at=datetime.fromisoformat(result['createdTime'].replace('Z', '+00:00')) if result.get('createdTime') else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to share file: {e}")
            raise
    
    async def get_permissions(self, file_id: str) -> List[GoogleDrivePermission]:
        """
        Get file permissions.
        
        Args:
            file_id: File ID
            
        Returns:
            List of permissions
        """
        try:
            results = self.service.permissions().list(
                fileId=file_id,
                fields='permissions(id,type,role,emailAddress,domain,allowFileDiscovery,createdTime)'
            ).execute()
            
            permissions = []
            for permission in results.get('permissions', []):
                drive_permission = GoogleDrivePermission(
                    id=permission['id'],
                    type=permission['type'],
                    role=GoogleDrivePermissionRole(permission['role']),
                    email_address=permission.get('emailAddress'),
                    domain=permission.get('domain'),
                    allow_file_discovery=permission.get('allowFileDiscovery', True),
                    created_at=datetime.fromisoformat(permission['createdTime'].replace('Z', '+00:00')) if permission.get('createdTime') else None
                )
                permissions.append(drive_permission)
            
            return permissions
            
        except Exception as e:
            self.logger.error(f"Failed to get permissions: {e}")
            raise
    
    async def search_files(
        self,
        query: str,
        mime_type: Optional[GoogleDriveFileType] = None,
        page_size: int = 100
    ) -> List[GoogleDriveFile]:
        """
        Search files.
        
        Args:
            query: Search query
            mime_type: Filter by MIME type
            page_size: Number of files to return
            
        Returns:
            List of files
        """
        try:
            # Build query
            q_parts = [f"name contains '{query}'"]
            
            if mime_type:
                q_parts.append(f"mimeType = '{mime_type.value}'")
            
            q_parts.append("trashed = false")
            
            q = " and ".join(q_parts)
            
            results = self.service.files().list(
                q=q,
                pageSize=page_size,
                fields="nextPageToken, files(id,name,mimeType,size,parents,webViewLink,webContentLink,createdTime,modifiedTime,modifiedByMeTime,shared,trashed)"
            ).execute()
            
            files = []
            for file in results.get('files', []):
                drive_file = GoogleDriveFile(
                    id=file['id'],
                    name=file['name'],
                    mime_type=GoogleDriveFileType(file['mimeType']),
                    size=file.get('size'),
                    parents=file.get('parents', []),
                    web_view_link=file.get('webViewLink'),
                    web_content_link=file.get('webContentLink'),
                    created_at=datetime.fromisoformat(file['createdTime'].replace('Z', '+00:00')) if file.get('createdTime') else None,
                    updated_at=datetime.fromisoformat(file['modifiedTime'].replace('Z', '+00:00')) if file.get('modifiedTime') else None,
                    modified_by_me_at=datetime.fromisoformat(file['modifiedByMeTime'].replace('Z', '+00:00')) if file.get('modifiedByMeTime') else None,
                    shared=file.get('shared', False),
                    trashed=file.get('trashed', False)
                )
                files.append(drive_file)
            
            return files
            
        except Exception as e:
            self.logger.error(f"Failed to search files: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Google Drive integration.
        
        Returns:
            Health check results
        """
        try:
            # Test API connectivity by listing files
            files = await self.list_files(page_size=1)
            
            # Test about endpoint
            about = self.service.about().get(fields="user,storageQuota").execute()
            
            return {
                "status": "healthy",
                "user_email": about.get("user", {}).get("emailAddress"),
                "storage_quota": about.get("storageQuota"),
                "files_count": len(files),
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

