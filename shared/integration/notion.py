"""
Notion Integration Module

This module provides integration with Notion for knowledge base management, documentation automation,
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
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    logging.warning("Notion APIs not available. Install requests")

logger = logging.getLogger(__name__)


class NotionObjectType(Enum):
    """Notion object types."""
    PAGE = "page"
    DATABASE = "database"
    BLOCK = "block"
    USER = "user"
    COMMENT = "comment"


class NotionBlockType(Enum):
    """Notion block types."""
    PARAGRAPH = "paragraph"
    HEADING_1 = "heading_1"
    HEADING_2 = "heading_2"
    HEADING_3 = "heading_3"
    BULLETED_LIST_ITEM = "bulleted_list_item"
    NUMBERED_LIST_ITEM = "numbered_list_item"
    TO_DO = "to_do"
    TOGGLE = "toggle"
    CHILD_PAGE = "child_page"
    CHILD_DATABASE = "child_database"
    EMBED = "embed"
    IMAGE = "image"
    VIDEO = "video"
    FILE = "file"
    PDF = "pdf"
    BOOKMARK = "bookmark"
    CALLOUT = "callout"
    QUOTE = "quote"
    EQUATION = "equation"
    DIVIDER = "divider"
    TABLE_OF_CONTENTS = "table_of_contents"
    COLUMN_LIST = "column_list"
    COLUMN = "column"
    LINK_PREVIEW = "link_preview"
    SYNCED_BLOCK = "synced_block"
    TEMPLATE = "template"
    LINK_TO_PAGE = "link_to_page"
    TABLE = "table"
    TABLE_ROW = "table_row"
    CODE = "code"


class NotionPropertyType(Enum):
    """Notion property types."""
    TITLE = "title"
    RICH_TEXT = "rich_text"
    NUMBER = "number"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    DATE = "date"
    PEOPLE = "people"
    FILES = "files"
    CHECKBOX = "checkbox"
    URL = "url"
    EMAIL = "email"
    PHONE_NUMBER = "phone_number"
    FORMULA = "formula"
    RELATION = "relation"
    ROLLUP = "rollup"
    CREATED_TIME = "created_time"
    CREATED_BY = "created_by"
    LAST_EDIT_TIME = "last_edit_time"
    LAST_EDIT_BY = "last_edit_by"


@dataclass
class NotionConfig:
    """Configuration for Notion integration."""
    
    api_key: str
    """Notion API key."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    verify_ssl: bool = True
    """Verify SSL certificates."""
    
    api_version: str = "v1"
    """API version to use."""


@dataclass
class NotionRichText:
    """Notion rich text data structure."""
    
    type: str = "text"
    """Text type."""
    
    text: Dict[str, str]
    """Text content."""
    
    annotations: Optional[Dict[str, bool]] = None
    """Text annotations."""
    
    plain_text: Optional[str] = None
    """Plain text content."""
    
    href: Optional[str] = None
    """Link URL."""


@dataclass
class NotionProperty:
    """Notion property data structure."""
    
    id: str
    """Property ID."""
    
    type: NotionPropertyType
    """Property type."""
    
    title: Optional[List[NotionRichText]] = None
    """Title content."""
    
    rich_text: Optional[List[NotionRichText]] = None
    """Rich text content."""
    
    number: Optional[float] = None
    """Number value."""
    
    select: Optional[Dict[str, Any]] = None
    """Select value."""
    
    multi_select: Optional[List[Dict[str, Any]]] = None
    """Multi-select values."""
    
    date: Optional[Dict[str, str]] = None
    """Date value."""
    
    people: Optional[List[Dict[str, Any]]] = None
    """People values."""
    
    files: Optional[List[Dict[str, Any]]] = None
    """File values."""
    
    checkbox: Optional[bool] = None
    """Checkbox value."""
    
    url: Optional[str] = None
    """URL value."""
    
    email: Optional[str] = None
    """Email value."""
    
    phone_number: Optional[str] = None
    """Phone number value."""
    
    formula: Optional[Dict[str, Any]] = None
    """Formula value."""
    
    relation: Optional[List[Dict[str, str]]] = None
    """Relation values."""
    
    rollup: Optional[Dict[str, Any]] = None
    """Rollup value."""
    
    created_time: Optional[str] = None
    """Created time."""
    
    created_by: Optional[Dict[str, Any]] = None
    """Created by."""
    
    last_edit_time: Optional[str] = None
    """Last edit time."""
    
    last_edit_by: Optional[Dict[str, Any]] = None
    """Last edit by."""


@dataclass
class NotionPage:
    """Notion page data structure."""
    
    id: str
    """Page ID."""
    
    object: str = "page"
    """Object type."""
    
    created_time: str
    """Created time."""
    
    last_edited_time: str
    """Last edited time."""
    
    created_by: Optional[Dict[str, Any]] = None
    """Created by."""
    
    last_edited_by: Optional[Dict[str, Any]] = None
    """Last edited by."""
    
    parent: Dict[str, Any]
    """Parent object."""
    
    archived: bool = False
    """Archived status."""
    
    properties: Dict[str, NotionProperty] = field(default_factory=dict)
    """Page properties."""
    
    url: Optional[str] = None
    """Page URL."""
    
    public_url: Optional[str] = None
    """Public URL."""
    
    icon: Optional[Dict[str, Any]] = None
    """Page icon."""
    
    cover: Optional[Dict[str, Any]] = None
    """Page cover."""


@dataclass
class NotionDatabase:
    """Notion database data structure."""
    
    id: str
    """Database ID."""
    
    object: str = "database"
    """Object type."""
    
    created_time: str
    """Created time."""
    
    last_edited_time: str
    """Last edited time."""
    
    created_by: Optional[Dict[str, Any]] = None
    """Created by."""
    
    last_edited_by: Optional[Dict[str, Any]] = None
    """Last edited by."""
    
    parent: Dict[str, Any]
    """Parent object."""
    
    archived: bool = False
    """Archived status."""
    
    properties: Dict[str, NotionProperty] = field(default_factory=dict)
    """Database properties."""
    
    title: List[NotionRichText] = field(default_factory=list)
    """Database title."""
    
    description: List[NotionRichText] = field(default_factory=list)
    """Database description."""
    
    url: Optional[str] = None
    """Database URL."""
    
    public_url: Optional[str] = None
    """Public URL."""
    
    icon: Optional[Dict[str, Any]] = None
    """Database icon."""
    
    cover: Optional[Dict[str, Any]] = None
    """Database cover."""


@dataclass
class NotionBlock:
    """Notion block data structure."""
    
    id: str
    """Block ID."""
    
    object: str = "block"
    """Object type."""
    
    created_time: str
    """Created time."""
    
    last_edited_time: str
    """Last edited time."""
    
    created_by: Optional[Dict[str, Any]] = None
    """Created by."""
    
    last_edited_by: Optional[Dict[str, Any]] = None
    """Last edited by."""
    
    parent: Dict[str, Any]
    """Parent object."""
    
    archived: bool = False
    """Archived status."""
    
    type: NotionBlockType
    """Block type."""
    
    paragraph: Optional[Dict[str, Any]] = None
    """Paragraph content."""
    
    heading_1: Optional[Dict[str, Any]] = None
    """Heading 1 content."""
    
    heading_2: Optional[Dict[str, Any]] = None
    """Heading 2 content."""
    
    heading_3: Optional[Dict[str, Any]] = None
    """Heading 3 content."""
    
    bulleted_list_item: Optional[Dict[str, Any]] = None
    """Bulleted list item content."""
    
    numbered_list_item: Optional[Dict[str, Any]] = None
    """Numbered list item content."""
    
    to_do: Optional[Dict[str, Any]] = None
    """To-do content."""
    
    toggle: Optional[Dict[str, Any]] = None
    """Toggle content."""
    
    child_page: Optional[Dict[str, Any]] = None
    """Child page content."""
    
    child_database: Optional[Dict[str, Any]] = None
    """Child database content."""
    
    embed: Optional[Dict[str, Any]] = None
    """Embed content."""
    
    image: Optional[Dict[str, Any]] = None
    """Image content."""
    
    video: Optional[Dict[str, Any]] = None
    """Video content."""
    
    file: Optional[Dict[str, Any]] = None
    """File content."""
    
    pdf: Optional[Dict[str, Any]] = None
    """PDF content."""
    
    bookmark: Optional[Dict[str, Any]] = None
    """Bookmark content."""
    
    callout: Optional[Dict[str, Any]] = None
    """Callout content."""
    
    quote: Optional[Dict[str, Any]] = None
    """Quote content."""
    
    equation: Optional[Dict[str, Any]] = None
    """Equation content."""
    
    divider: Optional[Dict[str, Any]] = None
    """Divider content."""
    
    table_of_contents: Optional[Dict[str, Any]] = None
    """Table of contents content."""
    
    column_list: Optional[Dict[str, Any]] = None
    """Column list content."""
    
    column: Optional[Dict[str, Any]] = None
    """Column content."""
    
    link_preview: Optional[Dict[str, Any]] = None
    """Link preview content."""
    
    synced_block: Optional[Dict[str, Any]] = None
    """Synced block content."""
    
    template: Optional[Dict[str, Any]] = None
    """Template content."""
    
    link_to_page: Optional[Dict[str, Any]] = None
    """Link to page content."""
    
    table: Optional[Dict[str, Any]] = None
    """Table content."""
    
    table_row: Optional[Dict[str, Any]] = None
    """Table row content."""
    
    code: Optional[Dict[str, Any]] = None
    """Code content."""


@dataclass
class NotionUser:
    """Notion user data structure."""
    
    id: str
    """User ID."""
    
    object: str = "user"
    """Object type."""
    
    name: Optional[str] = None
    """User name."""
    
    avatar_url: Optional[str] = None
    """Avatar URL."""
    
    type: str
    """User type."""
    
    person: Optional[Dict[str, Any]] = None
    """Person data."""
    
    bot: Optional[Dict[str, Any]] = None
    """Bot data."""


@dataclass
class NotionComment:
    """Notion comment data structure."""
    
    id: str
    """Comment ID."""
    
    object: str = "comment"
    """Object type."""
    
    created_time: str
    """Created time."""
    
    last_edited_time: str
    """Last edited time."""
    
    created_by: Dict[str, Any]
    """Created by."""
    
    last_edited_by: Optional[Dict[str, Any]] = None
    """Last edited by."""
    
    parent: Dict[str, Any]
    """Parent object."""
    
    rich_text: List[NotionRichText]
    """Comment text."""


class NotionIntegration:
    """Notion integration for knowledge base management and documentation automation."""
    
    def __init__(self, config: NotionConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.verify_ssl
        
        self.session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        })
        
        self.base_url = f"https://api.notion.com/{config.api_version}"
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the Notion API."""
        try:
            url = f"{self.base_url}/{endpoint}"
            
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, params=params)
            elif method.upper() == "PATCH":
                response = self.session.patch(url, json=data, params=params)
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
    
    def _parse_rich_text(self, rich_text_data: List[Dict[str, Any]]) -> List[NotionRichText]:
        """Parse rich text data."""
        rich_texts = []
        for item in rich_text_data:
            rich_text = NotionRichText(
                type=item.get("type", "text"),
                text=item.get("text", {}),
                annotations=item.get("annotations"),
                plain_text=item.get("plain_text"),
                href=item.get("href")
            )
            rich_texts.append(rich_text)
        return rich_texts
    
    def _parse_property(self, property_id: str, property_data: Dict[str, Any]) -> NotionProperty:
        """Parse property data."""
        property_type = NotionPropertyType(property_data["type"])
        
        property_obj = NotionProperty(
            id=property_id,
            type=property_type
        )
        
        if property_type == NotionPropertyType.TITLE:
            property_obj.title = self._parse_rich_text(property_data.get("title", []))
        elif property_type == NotionPropertyType.RICH_TEXT:
            property_obj.rich_text = self._parse_rich_text(property_data.get("rich_text", []))
        elif property_type == NotionPropertyType.NUMBER:
            property_obj.number = property_data.get("number")
        elif property_type == NotionPropertyType.SELECT:
            property_obj.select = property_data.get("select")
        elif property_type == NotionPropertyType.MULTI_SELECT:
            property_obj.multi_select = property_data.get("multi_select", [])
        elif property_type == NotionPropertyType.DATE:
            property_obj.date = property_data.get("date")
        elif property_type == NotionPropertyType.PEOPLE:
            property_obj.people = property_data.get("people", [])
        elif property_type == NotionPropertyType.FILES:
            property_obj.files = property_data.get("files", [])
        elif property_type == NotionPropertyType.CHECKBOX:
            property_obj.checkbox = property_data.get("checkbox")
        elif property_type == NotionPropertyType.URL:
            property_obj.url = property_data.get("url")
        elif property_type == NotionPropertyType.EMAIL:
            property_obj.email = property_data.get("email")
        elif property_type == NotionPropertyType.PHONE_NUMBER:
            property_obj.phone_number = property_data.get("phone_number")
        elif property_type == NotionPropertyType.FORMULA:
            property_obj.formula = property_data.get("formula")
        elif property_type == NotionPropertyType.RELATION:
            property_obj.relation = property_data.get("relation", [])
        elif property_type == NotionPropertyType.ROLLUP:
            property_obj.rollup = property_data.get("rollup")
        elif property_type == NotionPropertyType.CREATED_TIME:
            property_obj.created_time = property_data.get("created_time")
        elif property_type == NotionPropertyType.CREATED_BY:
            property_obj.created_by = property_data.get("created_by")
        elif property_type == NotionPropertyType.LAST_EDIT_TIME:
            property_obj.last_edit_time = property_data.get("last_edit_time")
        elif property_type == NotionPropertyType.LAST_EDIT_BY:
            property_obj.last_edit_by = property_data.get("last_edit_by")
        
        return property_obj
    
    async def create_page(self, parent_id: str, properties: Dict[str, Any], content: Optional[List[Dict[str, Any]]] = None) -> NotionPage:
        """
        Create a new page.
        
        Args:
            parent_id: Parent page or database ID
            properties: Page properties
            content: Page content blocks
            
        Returns:
            Created page
        """
        try:
            data = {
                "parent": {"page_id": parent_id} if parent_id.startswith("page_") else {"database_id": parent_id},
                "properties": properties
            }
            
            if content:
                data["children"] = content
            
            result = self._make_request("POST", "pages", data)
            
            # Parse properties
            parsed_properties = {}
            for prop_id, prop_data in result.get("properties", {}).items():
                parsed_properties[prop_id] = self._parse_property(prop_id, prop_data)
            
            page = NotionPage(
                id=result["id"],
                object=result["object"],
                created_time=result["created_time"],
                last_edited_time=result["last_edited_time"],
                created_by=result.get("created_by"),
                last_edited_by=result.get("last_edited_by"),
                parent=result["parent"],
                archived=result.get("archived", False),
                properties=parsed_properties,
                url=result.get("url"),
                public_url=result.get("public_url"),
                icon=result.get("icon"),
                cover=result.get("cover")
            )
            
            self.logger.info(f"Created Notion page: {page.id}")
            return page
            
        except Exception as e:
            self.logger.error(f"Failed to create page: {e}")
            raise
    
    async def get_page(self, page_id: str) -> NotionPage:
        """
        Get a page by ID.
        
        Args:
            page_id: Page ID
            
        Returns:
            Page data
        """
        try:
            result = self._make_request("GET", f"pages/{page_id}")
            
            # Parse properties
            parsed_properties = {}
            for prop_id, prop_data in result.get("properties", {}).items():
                parsed_properties[prop_id] = self._parse_property(prop_id, prop_data)
            
            return NotionPage(
                id=result["id"],
                object=result["object"],
                created_time=result["created_time"],
                last_edited_time=result["last_edited_time"],
                created_by=result.get("created_by"),
                last_edited_by=result.get("last_edited_by"),
                parent=result["parent"],
                archived=result.get("archived", False),
                properties=parsed_properties,
                url=result.get("url"),
                public_url=result.get("public_url"),
                icon=result.get("icon"),
                cover=result.get("cover")
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get page: {e}")
            raise
    
    async def update_page(self, page_id: str, properties: Dict[str, Any]) -> NotionPage:
        """
        Update a page.
        
        Args:
            page_id: Page ID
            properties: Updated properties
            
        Returns:
            Updated page
        """
        try:
            data = {"properties": properties}
            self._make_request("PATCH", f"pages/{page_id}", data)
            
            return await self.get_page(page_id)
            
        except Exception as e:
            self.logger.error(f"Failed to update page: {e}")
            raise
    
    async def create_database(self, parent_id: str, title: List[Dict[str, Any]], properties: Dict[str, Any]) -> NotionDatabase:
        """
        Create a new database.
        
        Args:
            parent_id: Parent page ID
            title: Database title
            properties: Database properties
            
        Returns:
            Created database
        """
        try:
            data = {
                "parent": {"page_id": parent_id},
                "title": title,
                "properties": properties
            }
            
            result = self._make_request("POST", "databases", data)
            
            # Parse properties
            parsed_properties = {}
            for prop_id, prop_data in result.get("properties", {}).items():
                parsed_properties[prop_id] = self._parse_property(prop_id, prop_data)
            
            database = NotionDatabase(
                id=result["id"],
                object=result["object"],
                created_time=result["created_time"],
                last_edited_time=result["last_edited_time"],
                created_by=result.get("created_by"),
                last_edited_by=result.get("last_edited_by"),
                parent=result["parent"],
                archived=result.get("archived", False),
                properties=parsed_properties,
                title=self._parse_rich_text(result.get("title", [])),
                description=self._parse_rich_text(result.get("description", [])),
                url=result.get("url"),
                public_url=result.get("public_url"),
                icon=result.get("icon"),
                cover=result.get("cover")
            )
            
            self.logger.info(f"Created Notion database: {database.id}")
            return database
            
        except Exception as e:
            self.logger.error(f"Failed to create database: {e}")
            raise
    
    async def get_database(self, database_id: str) -> NotionDatabase:
        """
        Get a database by ID.
        
        Args:
            database_id: Database ID
            
        Returns:
            Database data
        """
        try:
            result = self._make_request("GET", f"databases/{database_id}")
            
            # Parse properties
            parsed_properties = {}
            for prop_id, prop_data in result.get("properties", {}).items():
                parsed_properties[prop_id] = self._parse_property(prop_id, prop_data)
            
            return NotionDatabase(
                id=result["id"],
                object=result["object"],
                created_time=result["created_time"],
                last_edited_time=result["last_edited_time"],
                created_by=result.get("created_by"),
                last_edited_by=result.get("last_edited_by"),
                parent=result["parent"],
                archived=result.get("archived", False),
                properties=parsed_properties,
                title=self._parse_rich_text(result.get("title", [])),
                description=self._parse_rich_text(result.get("description", [])),
                url=result.get("url"),
                public_url=result.get("public_url"),
                icon=result.get("icon"),
                cover=result.get("cover")
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get database: {e}")
            raise
    
    async def query_database(self, database_id: str, filters: Optional[Dict[str, Any]] = None, sorts: Optional[List[Dict[str, Any]]] = None, page_size: int = 100) -> List[NotionPage]:
        """
        Query a database.
        
        Args:
            database_id: Database ID
            filters: Query filters
            sorts: Sort options
            page_size: Results per page
            
        Returns:
            List of pages
        """
        try:
            data = {"page_size": page_size}
            
            if filters:
                data["filter"] = filters
            if sorts:
                data["sorts"] = sorts
            
            result = self._make_request("POST", f"databases/{database_id}/query", data)
            
            pages = []
            for page_data in result.get("results", []):
                # Parse properties
                parsed_properties = {}
                for prop_id, prop_data in page_data.get("properties", {}).items():
                    parsed_properties[prop_id] = self._parse_property(prop_id, prop_data)
                
                page = NotionPage(
                    id=page_data["id"],
                    object=page_data["object"],
                    created_time=page_data["created_time"],
                    last_edited_time=page_data["last_edited_time"],
                    created_by=page_data.get("created_by"),
                    last_edited_by=page_data.get("last_edited_by"),
                    parent=page_data["parent"],
                    archived=page_data.get("archived", False),
                    properties=parsed_properties,
                    url=page_data.get("url"),
                    public_url=page_data.get("public_url"),
                    icon=page_data.get("icon"),
                    cover=page_data.get("cover")
                )
                pages.append(page)
            
            return pages
            
        except Exception as e:
            self.logger.error(f"Failed to query database: {e}")
            raise
    
    async def get_block_children(self, block_id: str, page_size: int = 100) -> List[NotionBlock]:
        """
        Get children of a block.
        
        Args:
            block_id: Block ID
            page_size: Results per page
            
        Returns:
            List of blocks
        """
        try:
            params = {"page_size": page_size}
            result = self._make_request("GET", f"blocks/{block_id}/children", params=params)
            
            blocks = []
            for block_data in result.get("results", []):
                block = NotionBlock(
                    id=block_data["id"],
                    object=block_data["object"],
                    created_time=block_data["created_time"],
                    last_edited_time=block_data["last_edited_time"],
                    created_by=block_data.get("created_by"),
                    last_edited_by=block_data.get("last_edited_by"),
                    parent=block_data["parent"],
                    archived=block_data.get("archived", False),
                    type=NotionBlockType(block_data["type"]),
                    paragraph=block_data.get("paragraph"),
                    heading_1=block_data.get("heading_1"),
                    heading_2=block_data.get("heading_2"),
                    heading_3=block_data.get("heading_3"),
                    bulleted_list_item=block_data.get("bulleted_list_item"),
                    numbered_list_item=block_data.get("numbered_list_item"),
                    to_do=block_data.get("to_do"),
                    toggle=block_data.get("toggle"),
                    child_page=block_data.get("child_page"),
                    child_database=block_data.get("child_database"),
                    embed=block_data.get("embed"),
                    image=block_data.get("image"),
                    video=block_data.get("video"),
                    file=block_data.get("file"),
                    pdf=block_data.get("pdf"),
                    bookmark=block_data.get("bookmark"),
                    callout=block_data.get("callout"),
                    quote=block_data.get("quote"),
                    equation=block_data.get("equation"),
                    divider=block_data.get("divider"),
                    table_of_contents=block_data.get("table_of_contents"),
                    column_list=block_data.get("column_list"),
                    column=block_data.get("column"),
                    link_preview=block_data.get("link_preview"),
                    synced_block=block_data.get("synced_block"),
                    template=block_data.get("template"),
                    link_to_page=block_data.get("link_to_page"),
                    table=block_data.get("table"),
                    table_row=block_data.get("table_row"),
                    code=block_data.get("code")
                )
                blocks.append(block)
            
            return blocks
            
        except Exception as e:
            self.logger.error(f"Failed to get block children: {e}")
            raise
    
    async def append_block_children(self, block_id: str, children: List[Dict[str, Any]]) -> List[NotionBlock]:
        """
        Append children to a block.
        
        Args:
            block_id: Block ID
            children: Children blocks
            
        Returns:
            List of created blocks
        """
        try:
            data = {"children": children}
            result = self._make_request("PATCH", f"blocks/{block_id}/children", data)
            
            blocks = []
            for block_data in result.get("results", []):
                block = NotionBlock(
                    id=block_data["id"],
                    object=block_data["object"],
                    created_time=block_data["created_time"],
                    last_edited_time=block_data["last_edited_time"],
                    created_by=block_data.get("created_by"),
                    last_edited_by=block_data.get("last_edited_by"),
                    parent=block_data["parent"],
                    archived=block_data.get("archived", False),
                    type=NotionBlockType(block_data["type"]),
                    paragraph=block_data.get("paragraph"),
                    heading_1=block_data.get("heading_1"),
                    heading_2=block_data.get("heading_2"),
                    heading_3=block_data.get("heading_3"),
                    bulleted_list_item=block_data.get("bulleted_list_item"),
                    numbered_list_item=block_data.get("numbered_list_item"),
                    to_do=block_data.get("to_do"),
                    toggle=block_data.get("toggle"),
                    child_page=block_data.get("child_page"),
                    child_database=block_data.get("child_database"),
                    embed=block_data.get("embed"),
                    image=block_data.get("image"),
                    video=block_data.get("video"),
                    file=block_data.get("file"),
                    pdf=block_data.get("pdf"),
                    bookmark=block_data.get("bookmark"),
                    callout=block_data.get("callout"),
                    quote=block_data.get("quote"),
                    equation=block_data.get("equation"),
                    divider=block_data.get("divider"),
                    table_of_contents=block_data.get("table_of_contents"),
                    column_list=block_data.get("column_list"),
                    column=block_data.get("column"),
                    link_preview=block_data.get("link_preview"),
                    synced_block=block_data.get("synced_block"),
                    template=block_data.get("template"),
                    link_to_page=block_data.get("link_to_page"),
                    table=block_data.get("table"),
                    table_row=block_data.get("table_row"),
                    code=block_data.get("code")
                )
                blocks.append(block)
            
            self.logger.info(f"Appended {len(blocks)} children to block {block_id}")
            return blocks
            
        except Exception as e:
            self.logger.error(f"Failed to append block children: {e}")
            raise
    
    async def update_block(self, block_id: str, block_data: Dict[str, Any]) -> NotionBlock:
        """
        Update a block.
        
        Args:
            block_id: Block ID
            block_data: Updated block data
            
        Returns:
            Updated block
        """
        try:
            result = self._make_request("PATCH", f"blocks/{block_id}", block_data)
            
            return NotionBlock(
                id=result["id"],
                object=result["object"],
                created_time=result["created_time"],
                last_edited_time=result["last_edited_time"],
                created_by=result.get("created_by"),
                last_edited_by=result.get("last_edited_by"),
                parent=result["parent"],
                archived=result.get("archived", False),
                type=NotionBlockType(result["type"]),
                paragraph=result.get("paragraph"),
                heading_1=result.get("heading_1"),
                heading_2=result.get("heading_2"),
                heading_3=result.get("heading_3"),
                bulleted_list_item=result.get("bulleted_list_item"),
                numbered_list_item=result.get("numbered_list_item"),
                to_do=result.get("to_do"),
                toggle=result.get("toggle"),
                child_page=result.get("child_page"),
                child_database=result.get("child_database"),
                embed=result.get("embed"),
                image=result.get("image"),
                video=result.get("video"),
                file=result.get("file"),
                pdf=result.get("pdf"),
                bookmark=result.get("bookmark"),
                callout=result.get("callout"),
                quote=result.get("quote"),
                equation=result.get("equation"),
                divider=result.get("divider"),
                table_of_contents=result.get("table_of_contents"),
                column_list=result.get("column_list"),
                column=result.get("column"),
                link_preview=result.get("link_preview"),
                synced_block=result.get("synced_block"),
                template=result.get("template"),
                link_to_page=result.get("link_to_page"),
                table=result.get("table"),
                table_row=result.get("table_row"),
                code=result.get("code")
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update block: {e}")
            raise
    
    async def delete_block(self, block_id: str) -> bool:
        """
        Delete a block.
        
        Args:
            block_id: Block ID
            
        Returns:
            Success status
        """
        try:
            self._make_request("DELETE", f"blocks/{block_id}")
            self.logger.info(f"Deleted Notion block: {block_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete block: {e}")
            raise
    
    async def search(self, query: str, filter_type: Optional[str] = None, page_size: int = 100) -> List[Union[NotionPage, NotionDatabase]]:
        """
        Search for pages and databases.
        
        Args:
            query: Search query
            filter_type: Filter by type (page, database)
            page_size: Results per page
            
        Returns:
            List of pages and databases
        """
        try:
            data = {
                "query": query,
                "page_size": page_size
            }
            
            if filter_type:
                data["filter"] = {"property": "object", "value": filter_type}
            
            result = self._make_request("POST", "search", data)
            
            items = []
            for item_data in result.get("results", []):
                if item_data["object"] == "page":
                    # Parse properties
                    parsed_properties = {}
                    for prop_id, prop_data in item_data.get("properties", {}).items():
                        parsed_properties[prop_id] = self._parse_property(prop_id, prop_data)
                    
                    item = NotionPage(
                        id=item_data["id"],
                        object=item_data["object"],
                        created_time=item_data["created_time"],
                        last_edited_time=item_data["last_edited_time"],
                        created_by=item_data.get("created_by"),
                        last_edited_by=item_data.get("last_edited_by"),
                        parent=item_data["parent"],
                        archived=item_data.get("archived", False),
                        properties=parsed_properties,
                        url=item_data.get("url"),
                        public_url=item_data.get("public_url"),
                        icon=item_data.get("icon"),
                        cover=item_data.get("cover")
                    )
                else:  # database
                    # Parse properties
                    parsed_properties = {}
                    for prop_id, prop_data in item_data.get("properties", {}).items():
                        parsed_properties[prop_id] = self._parse_property(prop_id, prop_data)
                    
                    item = NotionDatabase(
                        id=item_data["id"],
                        object=item_data["object"],
                        created_time=item_data["created_time"],
                        last_edited_time=item_data["last_edited_time"],
                        created_by=item_data.get("created_by"),
                        last_edited_by=item_data.get("last_edited_by"),
                        parent=item_data["parent"],
                        archived=item_data.get("archived", False),
                        properties=parsed_properties,
                        title=self._parse_rich_text(item_data.get("title", [])),
                        description=self._parse_rich_text(item_data.get("description", [])),
                        url=item_data.get("url"),
                        public_url=item_data.get("public_url"),
                        icon=item_data.get("icon"),
                        cover=item_data.get("cover")
                    )
                
                items.append(item)
            
            return items
            
        except Exception as e:
            self.logger.error(f"Failed to search: {e}")
            raise
    
    async def get_user(self, user_id: str) -> NotionUser:
        """
        Get a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User data
        """
        try:
            result = self._make_request("GET", f"users/{user_id}")
            
            return NotionUser(
                id=result["id"],
                object=result["object"],
                name=result.get("name"),
                avatar_url=result.get("avatar_url"),
                type=result["type"],
                person=result.get("person"),
                bot=result.get("bot")
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get user: {e}")
            raise
    
    async def list_users(self, page_size: int = 100) -> List[NotionUser]:
        """
        List users.
        
        Args:
            page_size: Results per page
            
        Returns:
            List of users
        """
        try:
            params = {"page_size": page_size}
            result = self._make_request("GET", "users", params=params)
            
            users = []
            for user_data in result.get("results", []):
                user = NotionUser(
                    id=user_data["id"],
                    object=user_data["object"],
                    name=user_data.get("name"),
                    avatar_url=user_data.get("avatar_url"),
                    type=user_data["type"],
                    person=user_data.get("person"),
                    bot=user_data.get("bot")
                )
                users.append(user)
            
            return users
            
        except Exception as e:
            self.logger.error(f"Failed to list users: {e}")
            raise
    
    async def create_comment(self, parent_id: str, rich_text: List[Dict[str, Any]]) -> NotionComment:
        """
        Create a comment.
        
        Args:
            parent_id: Parent page or block ID
            rich_text: Comment text
            
        Returns:
            Created comment
        """
        try:
            data = {
                "parent": {"page_id": parent_id} if parent_id.startswith("page_") else {"block_id": parent_id},
                "rich_text": rich_text
            }
            
            result = self._make_request("POST", "comments", data)
            
            comment = NotionComment(
                id=result["id"],
                object=result["object"],
                created_time=result["created_time"],
                last_edited_time=result["last_edited_time"],
                created_by=result["created_by"],
                last_edited_by=result.get("last_edited_by"),
                parent=result["parent"],
                rich_text=self._parse_rich_text(result.get("rich_text", []))
            )
            
            self.logger.info(f"Created Notion comment: {comment.id}")
            return comment
            
        except Exception as e:
            self.logger.error(f"Failed to create comment: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Notion integration.
        
        Returns:
            Health check results
        """
        try:
            # Test API connectivity by getting current user
            result = self._make_request("GET", "users/me")
            
            return {
                "status": "healthy",
                "api_version": self.config.api_version,
                "user_id": result.get("id"),
                "user_name": result.get("name"),
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
