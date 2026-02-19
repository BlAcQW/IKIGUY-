"""
Confluence Integration Module

This module provides integration with Confluence for enterprise knowledge base management, documentation automation,
and content collaboration with comprehensive REST API support.
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
    CONFLUENCE_AVAILABLE = True
except ImportError:
    CONFLUENCE_AVAILABLE = False
    logging.warning("Confluence APIs not available. Install requests")

logger = logging.getLogger(__name__)


class ConfluenceContentType(Enum):
    """Confluence content types."""
    PAGE = "page"
    BLOGPOST = "blogpost"
    COMMENT = "comment"
    ATTACHMENT = "attachment"
    SPACE = "space"


class ConfluenceContentStatus(Enum):
    """Confluence content status values."""
    CURRENT = "current"
    TRASHED = "trashed"
    HISTORICAL = "historical"
    DRAFT = "draft"


class ConfluenceSpaceType(Enum):
    """Confluence space types."""
    GLOBAL = "global"
    PERSONAL = "personal"


class ConfluenceSpaceStatus(Enum):
    """Confluence space status values."""
    CURRENT = "current"
    ARCHIVED = "archived"


@dataclass
class ConfluenceConfig:
    """Configuration for Confluence integration."""
    
    base_url: str
    """Confluence base URL (e.g., 'https://company.atlassian.net')."""
    
    username: str
    """Confluence username or email."""
    
    api_token: str
    """Confluence API token."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    verify_ssl: bool = True
    """Verify SSL certificates."""
    
    api_version: str = "v2"
    """API version to use."""


@dataclass
class ConfluenceSpace:
    """Confluence space data structure."""
    
    id: int
    """Space ID."""
    
    key: str
    """Space key."""
    
    name: str
    """Space name."""
    
    type: ConfluenceSpaceType
    """Space type."""
    
    status: ConfluenceSpaceStatus
    """Space status."""
    
    description: Optional[Dict[str, Any]] = None
    """Space description."""
    
    homepage_id: Optional[str] = None
    """Homepage ID."""
    
    created_at: Optional[datetime] = None
    """Created at."""
    
    updated_at: Optional[datetime] = None
    """Updated at."""
    
    expandable: Optional[Dict[str, str]] = None
    """Expandable fields."""
    
    _links: Optional[Dict[str, Any]] = None
    """Links."""


@dataclass
class ConfluenceContent:
    """Confluence content data structure."""
    
    id: str
    """Content ID."""
    
    type: ConfluenceContentType
    """Content type."""
    
    status: ConfluenceContentStatus
    """Content status."""
    
    title: str
    """Content title."""
    
    space_id: Optional[int] = None
    """Space ID."""
    
    space_key: Optional[str] = None
    """Space key."""
    
    space_name: Optional[str] = None
    """Space name."""
    
    space_type: Optional[ConfluenceSpaceType] = None
    """Space type."""
    
    parent_id: Optional[str] = None
    """Parent content ID."""
    
    parent_type: Optional[ConfluenceContentType] = None
    """Parent content type."""
    
    parent_title: Optional[str] = None
    """Parent content title."""
    
    version_number: Optional[int] = None
    """Version number."""
    
    version_message: Optional[str] = None
    """Version message."""
    
    body: Optional[Dict[str, Any]] = None
    """Content body."""
    
    metadata: Optional[Dict[str, Any]] = None
    """Content metadata."""
    
    created_at: Optional[datetime] = None
    """Created at."""
    
    updated_at: Optional[datetime] = None
    """Updated at."""
    
    created_by: Optional[Dict[str, Any]] = None
    """Created by."""
    
    updated_by: Optional[Dict[str, Any]] = None
    """Updated by."""
    
    expandable: Optional[Dict[str, str]] = None
    """Expandable fields."""
    
    _links: Optional[Dict[str, Any]] = None
    """Links."""


@dataclass
class ConfluenceComment:
    """Confluence comment data structure."""
    
    id: str
    """Comment ID."""
    
    type: str = "comment"
    """Comment type."""
    
    title: Optional[str] = None
    """Comment title."""
    
    body: Optional[Dict[str, Any]] = None
    """Comment body."""
    
    parent_id: Optional[str] = None
    """Parent content ID."""
    
    parent_type: Optional[ConfluenceContentType] = None
    """Parent content type."""
    
    space_id: Optional[int] = None
    """Space ID."""
    
    space_key: Optional[str] = None
    """Space key."""
    
    version_number: Optional[int] = None
    """Version number."""
    
    created_at: Optional[datetime] = None
    """Created at."""
    
    updated_at: Optional[datetime] = None
    """Updated at."""
    
    created_by: Optional[Dict[str, Any]] = None
    """Created by."""
    
    updated_by: Optional[Dict[str, Any]] = None
    """Updated by."""
    
    expandable: Optional[Dict[str, str]] = None
    """Expandable fields."""
    
    _links: Optional[Dict[str, Any]] = None
    """Links."""


@dataclass
class ConfluenceAttachment:
    """Confluence attachment data structure."""
    
    id: str
    """Attachment ID."""
    
    title: str
    """Attachment title."""
    
    file_name: str
    """File name."""
    
    media_type: str
    """Media type."""
    
    file_size: Optional[int] = None
    """File size in bytes."""
    
    comment: Optional[str] = None
    """Attachment comment."""
    
    parent_id: Optional[str] = None
    """Parent content ID."""
    
    space_id: Optional[int] = None
    """Space ID."""
    
    space_key: Optional[str] = None
    """Space key."""
    
    version_number: Optional[int] = None
    """Version number."""
    
    created_at: Optional[datetime] = None
    """Created at."""
    
    updated_at: Optional[datetime] = None
    """Updated at."""
    
    created_by: Optional[Dict[str, Any]] = None
    """Created by."""
    
    updated_by: Optional[Dict[str, Any]] = None
    """Updated by."""
    
    expandable: Optional[Dict[str, str]] = None
    """Expandable fields."""
    
    _links: Optional[Dict[str, Any]] = None
    """Links."""


@dataclass
class ConfluenceUser:
    """Confluence user data structure."""
    
    account_id: str
    """Account ID."""
    
    account_type: str
    """Account type."""
    
    email: Optional[str] = None
    """Email address."""
    
    public_name: Optional[str] = None
    """Public name."""
    
    display_name: Optional[str] = None
    """Display name."""
    
    profile_picture: Optional[Dict[str, Any]] = None
    """Profile picture."""
    
    time_zone: Optional[str] = None
    """Time zone."""
    
    is_external_collaborator: Optional[bool] = None
    """Is external collaborator."""
    
    is_anonymous: Optional[bool] = None
    """Is anonymous."""
    
    _links: Optional[Dict[str, Any]] = None
    """Links."""


class ConfluenceIntegration:
    """Confluence integration for enterprise knowledge base management and documentation automation."""
    
    def __init__(self, config: ConfluenceConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.verify_ssl
        
        # Set up authentication
        self.session.auth = (config.username, config.api_token)
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        
        self.base_url = f"{config.base_url}/wiki/rest/api/{config.api_version}"
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the Confluence API."""
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
    
    def _parse_datetime(self, date_string: str) -> Optional[datetime]:
        """Parse datetime string from Confluence API."""
        if not date_string:
            return None
        try:
            return datetime.fromisoformat(date_string.replace("Z", "+00:00"))
        except ValueError:
            return None
    
    def _parse_space(self, space_data: Dict[str, Any]) -> ConfluenceSpace:
        """Parse space data."""
        return ConfluenceSpace(
            id=space_data["id"],
            key=space_data["key"],
            name=space_data["name"],
            type=ConfluenceSpaceType(space_data["type"]),
            status=ConfluenceSpaceStatus(space_data["status"]),
            description=space_data.get("description"),
            homepage_id=space_data.get("homepageId"),
            created_at=self._parse_datetime(space_data.get("createdAt")),
            updated_at=self._parse_datetime(space_data.get("updatedAt")),
            expandable=space_data.get("_expandable"),
            _links=space_data.get("_links")
        )
    
    def _parse_content(self, content_data: Dict[str, Any]) -> ConfluenceContent:
        """Parse content data."""
        return ConfluenceContent(
            id=content_data["id"],
            type=ConfluenceContentType(content_data["type"]),
            status=ConfluenceContentStatus(content_data["status"]),
            title=content_data["title"],
            space_id=content_data.get("spaceId"),
            space_key=content_data.get("spaceKey"),
            space_name=content_data.get("spaceName"),
            space_type=ConfluenceSpaceType(content_data["space"]["type"]) if content_data.get("space") else None,
            parent_id=content_data.get("parentId"),
            parent_type=ConfluenceContentType(content_data["parent"]["type"]) if content_data.get("parent") else None,
            parent_title=content_data.get("parentTitle"),
            version_number=content_data.get("version", {}).get("number"),
            version_message=content_data.get("version", {}).get("message"),
            body=content_data.get("body"),
            metadata=content_data.get("metadata"),
            created_at=self._parse_datetime(content_data.get("createdAt")),
            updated_at=self._parse_datetime(content_data.get("updatedAt")),
            created_by=content_data.get("createdBy"),
            updated_by=content_data.get("updatedBy"),
            expandable=content_data.get("_expandable"),
            _links=content_data.get("_links")
        )
    
    def _parse_comment(self, comment_data: Dict[str, Any]) -> ConfluenceComment:
        """Parse comment data."""
        return ConfluenceComment(
            id=comment_data["id"],
            type=comment_data["type"],
            title=comment_data.get("title"),
            body=comment_data.get("body"),
            parent_id=comment_data.get("parentId"),
            parent_type=ConfluenceContentType(comment_data["parent"]["type"]) if comment_data.get("parent") else None,
            space_id=comment_data.get("spaceId"),
            space_key=comment_data.get("spaceKey"),
            version_number=comment_data.get("version", {}).get("number"),
            created_at=self._parse_datetime(comment_data.get("createdAt")),
            updated_at=self._parse_datetime(comment_data.get("updatedAt")),
            created_by=comment_data.get("createdBy"),
            updated_by=comment_data.get("updatedBy"),
            expandable=comment_data.get("_expandable"),
            _links=comment_data.get("_links")
        )
    
    def _parse_attachment(self, attachment_data: Dict[str, Any]) -> ConfluenceAttachment:
        """Parse attachment data."""
        return ConfluenceAttachment(
            id=attachment_data["id"],
            title=attachment_data["title"],
            file_name=attachment_data["fileName"],
            media_type=attachment_data["mediaType"],
            file_size=attachment_data.get("fileSize"),
            comment=attachment_data.get("comment"),
            parent_id=attachment_data.get("parentId"),
            space_id=attachment_data.get("spaceId"),
            space_key=attachment_data.get("spaceKey"),
            version_number=attachment_data.get("version", {}).get("number"),
            created_at=self._parse_datetime(attachment_data.get("createdAt")),
            updated_at=self._parse_datetime(attachment_data.get("updatedAt")),
            created_by=attachment_data.get("createdBy"),
            updated_by=attachment_data.get("updatedBy"),
            expandable=attachment_data.get("_expandable"),
            _links=attachment_data.get("_links")
        )
    
    async def get_spaces(self, space_type: Optional[ConfluenceSpaceType] = None, status: Optional[ConfluenceSpaceStatus] = None, limit: int = 100) -> List[ConfluenceSpace]:
        """
        Get spaces.
        
        Args:
            space_type: Filter by space type
            status: Filter by space status
            limit: Maximum number of results
            
        Returns:
            List of spaces
        """
        try:
            params = {"limit": limit}
            
            if space_type:
                params["type"] = space_type.value
            if status:
                params["status"] = status.value
            
            result = self._make_request("GET", "space", params=params)
            
            spaces = []
            for space_data in result.get("results", []):
                spaces.append(self._parse_space(space_data))
            
            return spaces
            
        except Exception as e:
            self.logger.error(f"Failed to get spaces: {e}")
            raise
    
    async def get_space(self, space_key: str) -> ConfluenceSpace:
        """
        Get a space by key.
        
        Args:
            space_key: Space key
            
        Returns:
            Space data
        """
        try:
            result = self._make_request("GET", f"space/{space_key}")
            return self._parse_space(result)
            
        except Exception as e:
            self.logger.error(f"Failed to get space: {e}")
            raise
    
    async def create_space(self, space_key: str, name: str, space_type: ConfluenceSpaceType = ConfluenceSpaceType.GLOBAL, description: Optional[str] = None) -> ConfluenceSpace:
        """
        Create a new space.
        
        Args:
            space_key: Space key
            name: Space name
            space_type: Space type
            description: Space description
            
        Returns:
            Created space
        """
        try:
            data = {
                "key": space_key,
                "name": name,
                "type": space_type.value
            }
            
            if description:
                data["description"] = {"plain": {"value": description}}
            
            result = self._make_request("POST", "space", data)
            
            space = self._parse_space(result)
            self.logger.info(f"Created Confluence space: {space.key}")
            return space
            
        except Exception as e:
            self.logger.error(f"Failed to create space: {e}")
            raise
    
    async def create_page(self, space_key: str, title: str, content: str, parent_id: Optional[str] = None, content_type: str = "storage") -> ConfluenceContent:
        """
        Create a new page.
        
        Args:
            space_key: Space key
            title: Page title
            content: Page content (HTML or storage format)
            parent_id: Parent page ID
            content_type: Content type (storage, view, export_view)
            
        Returns:
            Created page
        """
        try:
            data = {
                "type": "page",
                "title": title,
                "space": {"key": space_key},
                "body": {
                    content_type: {
                        "value": content,
                        "representation": content_type
                    }
                }
            }
            
            if parent_id:
                data["ancestors"] = [{"id": parent_id}]
            
            result = self._make_request("POST", "content", data)
            
            page = self._parse_content(result)
            self.logger.info(f"Created Confluence page: {page.id}")
            return page
            
        except Exception as e:
            self.logger.error(f"Failed to create page: {e}")
            raise
    
    async def get_page(self, page_id: str, expand: Optional[List[str]] = None) -> ConfluenceContent:
        """
        Get a page by ID.
        
        Args:
            page_id: Page ID
            expand: Fields to expand
            
        Returns:
            Page data
        """
        try:
            params = {}
            if expand:
                params["expand"] = ",".join(expand)
            
            result = self._make_request("GET", f"content/{page_id}", params=params)
            return self._parse_content(result)
            
        except Exception as e:
            self.logger.error(f"Failed to get page: {e}")
            raise
    
    async def update_page(self, page_id: str, title: str, content: str, version_number: int, content_type: str = "storage") -> ConfluenceContent:
        """
        Update a page.
        
        Args:
            page_id: Page ID
            title: Page title
            content: Page content
            version_number: Current version number
            content_type: Content type (storage, view, export_view)
            
        Returns:
            Updated page
        """
        try:
            data = {
                "version": {"number": version_number + 1},
                "title": title,
                "type": "page",
                "body": {
                    content_type: {
                        "value": content,
                        "representation": content_type
                    }
                }
            }
            
            result = self._make_request("PUT", f"content/{page_id}", data)
            
            page = self._parse_content(result)
            self.logger.info(f"Updated Confluence page: {page.id}")
            return page
            
        except Exception as e:
            self.logger.error(f"Failed to update page: {e}")
            raise
    
    async def delete_page(self, page_id: str) -> bool:
        """
        Delete a page.
        
        Args:
            page_id: Page ID
            
        Returns:
            Success status
        """
        try:
            self._make_request("DELETE", f"content/{page_id}")
            self.logger.info(f"Deleted Confluence page: {page_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete page: {e}")
            raise
    
    async def get_page_children(self, page_id: str, expand: Optional[List[str]] = None, limit: int = 100) -> List[ConfluenceContent]:
        """
        Get children of a page.
        
        Args:
            page_id: Page ID
            expand: Fields to expand
            limit: Maximum number of results
            
        Returns:
            List of child pages
        """
        try:
            params = {"limit": limit}
            if expand:
                params["expand"] = ",".join(expand)
            
            result = self._make_request("GET", f"content/{page_id}/child/page", params=params)
            
            pages = []
            for page_data in result.get("results", []):
                pages.append(self._parse_content(page_data))
            
            return pages
            
        except Exception as e:
            self.logger.error(f"Failed to get page children: {e}")
            raise
    
    async def search_content(self, cql: str, expand: Optional[List[str]] = None, limit: int = 100) -> List[ConfluenceContent]:
        """
        Search content using CQL (Confluence Query Language).
        
        Args:
            cql: CQL query string
            expand: Fields to expand
            limit: Maximum number of results
            
        Returns:
            List of content
        """
        try:
            params = {
                "cql": cql,
                "limit": limit
            }
            if expand:
                params["expand"] = ",".join(expand)
            
            result = self._make_request("GET", "content/search", params=params)
            
            content_list = []
            for content_data in result.get("results", []):
                content_list.append(self._parse_content(content_data))
            
            return content_list
            
        except Exception as e:
            self.logger.error(f"Failed to search content: {e}")
            raise
    
    async def create_comment(self, page_id: str, content: str, parent_id: Optional[str] = None, content_type: str = "storage") -> ConfluenceComment:
        """
        Create a comment on a page.
        
        Args:
            page_id: Page ID
            content: Comment content
            parent_id: Parent comment ID
            content_type: Content type (storage, view, export_view)
            
        Returns:
            Created comment
        """
        try:
            data = {
                "type": "comment",
                "title": "Comment",
                "body": {
                    content_type: {
                        "value": content,
                        "representation": content_type
                    }
                },
                "container": {
                    "id": page_id,
                    "type": "page"
                }
            }
            
            if parent_id:
                data["ancestors"] = [{"id": parent_id}]
            
            result = self._make_request("POST", "content", data)
            
            comment = self._parse_comment(result)
            self.logger.info(f"Created Confluence comment: {comment.id}")
            return comment
            
        except Exception as e:
            self.logger.error(f"Failed to create comment: {e}")
            raise
    
    async def get_comments(self, page_id: str, expand: Optional[List[str]] = None, limit: int = 100) -> List[ConfluenceComment]:
        """
        Get comments for a page.
        
        Args:
            page_id: Page ID
            expand: Fields to expand
            limit: Maximum number of results
            
        Returns:
            List of comments
        """
        try:
            params = {"limit": limit}
            if expand:
                params["expand"] = ",".join(expand)
            
            result = self._make_request("GET", f"content/{page_id}/child/comment", params=params)
            
            comments = []
            for comment_data in result.get("results", []):
                comments.append(self._parse_comment(comment_data))
            
            return comments
            
        except Exception as e:
            self.logger.error(f"Failed to get comments: {e}")
            raise
    
    async def create_attachment(self, page_id: str, file_path: str, comment: Optional[str] = None) -> ConfluenceAttachment:
        """
        Create an attachment on a page.
        
        Args:
            page_id: Page ID
            file_path: Path to file
            comment: Attachment comment
            
        Returns:
            Created attachment
        """
        try:
            # Get the page to get current version
            page = await self.get_page(page_id)
            
            # Prepare multipart data
            files = {"file": open(file_path, "rb")}
            data = {
                "comment": comment or "",
                "minorEdit": "true"
            }
            
            # Make the request
            url = f"{self.base_url}/content/{page_id}/child/attachment"
            response = self.session.post(url, data=data, files=files)
            response.raise_for_status()
            
            attachment_data = response.json()
            attachment = self._parse_attachment(attachment_data)
            
            self.logger.info(f"Created Confluence attachment: {attachment.id}")
            return attachment
            
        except Exception as e:
            self.logger.error(f"Failed to create attachment: {e}")
            raise
    
    async def get_attachments(self, page_id: str, expand: Optional[List[str]] = None, limit: int = 100) -> List[ConfluenceAttachment]:
        """
        Get attachments for a page.
        
        Args:
            page_id: Page ID
            expand: Fields to expand
            limit: Maximum number of results
            
        Returns:
            List of attachments
        """
        try:
            params = {"limit": limit}
            if expand:
                params["expand"] = ",".join(expand)
            
            result = self._make_request("GET", f"content/{page_id}/child/attachment", params=params)
            
            attachments = []
            for attachment_data in result.get("results", []):
                attachments.append(self._parse_attachment(attachment_data))
            
            return attachments
            
        except Exception as e:
            self.logger.error(f"Failed to get attachments: {e}")
            raise
    
    async def get_user(self, account_id: str) -> ConfluenceUser:
        """
        Get a user by account ID.
        
        Args:
            account_id: Account ID
            
        Returns:
            User data
        """
        try:
            result = self._make_request("GET", f"user", params={"accountId": account_id})
            return ConfluenceUser(
                account_id=result["accountId"],
                account_type=result["accountType"],
                email=result.get("email"),
                public_name=result.get("publicName"),
                display_name=result.get("displayName"),
                profile_picture=result.get("profilePicture"),
                time_zone=result.get("timeZone"),
                is_external_collaborator=result.get("isExternalCollaborator"),
                is_anonymous=result.get("isAnonymous"),
                _links=result.get("_links")
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get user: {e}")
            raise
    
    async def get_current_user(self) -> ConfluenceUser:
        """
        Get the current user.
        
        Returns:
            Current user data
        """
        try:
            result = self._make_request("GET", "user/current")
            return ConfluenceUser(
                account_id=result["accountId"],
                account_type=result["accountType"],
                email=result.get("email"),
                public_name=result.get("publicName"),
                display_name=result.get("displayName"),
                profile_picture=result.get("profilePicture"),
                time_zone=result.get("timeZone"),
                is_external_collaborator=result.get("isExternalCollaborator"),
                is_anonymous=result.get("isAnonymous"),
                _links=result.get("_links")
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get current user: {e}")
            raise
    
    async def get_page_history(self, page_id: str, limit: int = 100) -> List[ConfluenceContent]:
        """
        Get page history.
        
        Args:
            page_id: Page ID
            limit: Maximum number of results
            
        Returns:
            List of page versions
        """
        try:
            params = {"limit": limit}
            result = self._make_request("GET", f"content/{page_id}/history", params=params)
            
            versions = []
            for version_data in result.get("results", []):
                versions.append(self._parse_content(version_data))
            
            return versions
            
        except Exception as e:
            self.logger.error(f"Failed to get page history: {e}")
            raise
    
    async def get_space_content(self, space_key: str, content_type: Optional[ConfluenceContentType] = None, expand: Optional[List[str]] = None, limit: int = 100) -> List[ConfluenceContent]:
        """
        Get content in a space.
        
        Args:
            space_key: Space key
            content_type: Filter by content type
            expand: Fields to expand
            limit: Maximum number of results
            
        Returns:
            List of content
        """
        try:
            params = {"limit": limit}
            
            if content_type:
                params["type"] = content_type.value
            if expand:
                params["expand"] = ",".join(expand)
            
            result = self._make_request("GET", f"content", params=params)
            
            content_list = []
            for content_data in result.get("results", []):
                if content_data.get("space", {}).get("key") == space_key:
                    content_list.append(self._parse_content(content_data))
            
            return content_list
            
        except Exception as e:
            self.logger.error(f"Failed to get space content: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Confluence integration.
        
        Returns:
            Health check results
        """
        try:
            # Test API connectivity by getting current user
            result = self._make_request("GET", "user/current")
            
            return {
                "status": "healthy",
                "base_url": self.config.base_url,
                "api_version": self.config.api_version,
                "user_account_id": result.get("accountId"),
                "user_display_name": result.get("displayName"),
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
