"""
Telegram Integration Module

This module provides integration with Telegram for messaging, bot management,
and channel communication.
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
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logging.warning("Telegram APIs not available. Install requests")

logger = logging.getLogger(__name__)


class TelegramMessageType(Enum):
    """Telegram message types."""
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    VOICE = "voice"
    LOCATION = "location"
    CONTACT = "contact"
    POLL = "poll"


class TelegramChatType(Enum):
    """Telegram chat types."""
    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"


@dataclass
class TelegramConfig:
    """Configuration for Telegram integration."""
    
    bot_token: str
    """Telegram bot token."""
    
    api_base_url: str = "https://api.telegram.org/bot"
    """Telegram API base URL."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    webhook_url: Optional[str] = None
    """Webhook URL for receiving updates."""
    
    allowed_updates: List[str] = field(default_factory=lambda: [
        "message", "edited_message", "channel_post", "edited_channel_post"
    ])
    """Allowed update types."""


@dataclass
class TelegramMessage:
    """Telegram message data structure."""
    
    message_id: int
    """Message ID."""
    
    chat_id: int
    """Chat ID."""
    
    chat_type: TelegramChatType
    """Chat type."""
    
    from_user: Optional[Dict[str, Any]] = None
    """User who sent the message."""
    
    text: Optional[str] = None
    """Message text."""
    
    message_type: TelegramMessageType = TelegramMessageType.TEXT
    """Message type."""
    
    date: datetime = field(default_factory=datetime.now)
    """Message date."""
    
    reply_to_message: Optional[Dict[str, Any]] = None
    """Reply to message."""
    
    forward_from: Optional[Dict[str, Any]] = None
    """Forwarded from user."""
    
    media: Optional[Dict[str, Any]] = None
    """Media information."""
    
    caption: Optional[str] = None
    """Media caption."""
    
    entities: List[Dict[str, Any]] = field(default_factory=list)
    """Message entities (mentions, links, etc.)."""


@dataclass
class TelegramChat:
    """Telegram chat data structure."""
    
    id: int
    """Chat ID."""
    
    type: TelegramChatType
    """Chat type."""
    
    title: Optional[str] = None
    """Chat title."""
    
    username: Optional[str] = None
    """Chat username."""
    
    first_name: Optional[str] = None
    """First name (for private chats)."""
    
    last_name: Optional[str] = None
    """Last name (for private chats)."""
    
    description: Optional[str] = None
    """Chat description."""
    
    invite_link: Optional[str] = None
    """Invite link."""
    
    member_count: Optional[int] = None
    """Member count."""
    
    is_forum: bool = False
    """Whether chat is a forum."""
    
    active_usernames: List[str] = field(default_factory=list)
    """Active usernames."""


@dataclass
class TelegramUser:
    """Telegram user data structure."""
    
    id: int
    """User ID."""
    
    is_bot: bool
    """Whether user is a bot."""
    
    first_name: str
    """First name."""
    
    last_name: Optional[str] = None
    """Last name."""
    
    username: Optional[str] = None
    """Username."""
    
    language_code: Optional[str] = None
    """Language code."""
    
    is_premium: bool = False
    """Whether user has premium."""
    
    added_to_attachment_menu: bool = False
    """Whether user added bot to attachment menu."""


@dataclass
class TelegramUpdate:
    """Telegram update data structure."""
    
    update_id: int
    """Update ID."""
    
    message: Optional[TelegramMessage] = None
    """Message update."""
    
    edited_message: Optional[TelegramMessage] = None
    """Edited message update."""
    
    channel_post: Optional[TelegramMessage] = None
    """Channel post update."""
    
    edited_channel_post: Optional[TelegramMessage] = None
    """Edited channel post update."""
    
    callback_query: Optional[Dict[str, Any]] = None
    """Callback query update."""
    
    inline_query: Optional[Dict[str, Any]] = None
    """Inline query update."""
    
    chosen_inline_result: Optional[Dict[str, Any]] = None
    """Chosen inline result update."""


class TelegramIntegration:
    """Telegram integration for messaging and bot management."""
    
    def __init__(self, config: TelegramConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.base_url = f"{config.api_base_url}{config.bot_token}"
    
    async def get_me(self) -> Dict[str, Any]:
        """
        Get bot information.
        
        Returns:
            Bot information
        """
        try:
            url = f"{self.base_url}/getMe"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            if data["ok"]:
                return data["result"]
            else:
                raise Exception(f"Telegram API error: {data.get('description', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"Failed to get bot info: {e}")
            raise
    
    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        parse_mode: Optional[str] = None,
        disable_web_page_preview: bool = False,
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a text message.
        
        Args:
            chat_id: Chat ID or username
            text: Message text
            parse_mode: Parse mode (HTML, Markdown, MarkdownV2)
            disable_web_page_preview: Disable web page preview
            disable_notification: Disable notification
            reply_to_message_id: Reply to message ID
            reply_markup: Reply markup (keyboard, inline keyboard)
            
        Returns:
            Sent message information
        """
        try:
            url = f"{self.base_url}/sendMessage"
            
            payload = {
                "chat_id": chat_id,
                "text": text
            }
            
            if parse_mode:
                payload["parse_mode"] = parse_mode
            if disable_web_page_preview:
                payload["disable_web_page_preview"] = disable_web_page_preview
            if disable_notification:
                payload["disable_notification"] = disable_notification
            if reply_to_message_id:
                payload["reply_to_message_id"] = reply_to_message_id
            if reply_markup:
                payload["reply_markup"] = json.dumps(reply_markup)
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            if data["ok"]:
                return data["result"]
            else:
                raise Exception(f"Telegram API error: {data.get('description', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            raise
    
    async def send_photo(
        self,
        chat_id: Union[int, str],
        photo: Union[str, bytes],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a photo.
        
        Args:
            chat_id: Chat ID or username
            photo: Photo file ID, URL, or bytes
            caption: Photo caption
            parse_mode: Parse mode for caption
            disable_notification: Disable notification
            reply_to_message_id: Reply to message ID
            reply_markup: Reply markup
            
        Returns:
            Sent message information
        """
        try:
            url = f"{self.base_url}/sendPhoto"
            
            payload = {
                "chat_id": chat_id
            }
            
            if isinstance(photo, str):
                payload["photo"] = photo
            else:
                files = {"photo": ("photo.jpg", photo, "image/jpeg")}
                response = self.session.post(url, data=payload, files=files)
                response.raise_for_status()
                data = response.json()
                if data["ok"]:
                    return data["result"]
                else:
                    raise Exception(f"Telegram API error: {data.get('description', 'Unknown error')}")
            
            if caption:
                payload["caption"] = caption
            if parse_mode:
                payload["parse_mode"] = parse_mode
            if disable_notification:
                payload["disable_notification"] = disable_notification
            if reply_to_message_id:
                payload["reply_to_message_id"] = reply_to_message_id
            if reply_markup:
                payload["reply_markup"] = json.dumps(reply_markup)
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            if data["ok"]:
                return data["result"]
            else:
                raise Exception(f"Telegram API error: {data.get('description', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"Failed to send photo: {e}")
            raise
    
    async def send_document(
        self,
        chat_id: Union[int, str],
        document: Union[str, bytes],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a document.
        
        Args:
            chat_id: Chat ID or username
            document: Document file ID, URL, or bytes
            caption: Document caption
            parse_mode: Parse mode for caption
            disable_notification: Disable notification
            reply_to_message_id: Reply to message ID
            reply_markup: Reply markup
            
        Returns:
            Sent message information
        """
        try:
            url = f"{self.base_url}/sendDocument"
            
            payload = {
                "chat_id": chat_id
            }
            
            if isinstance(document, str):
                payload["document"] = document
            else:
                files = {"document": ("document.pdf", document, "application/pdf")}
                response = self.session.post(url, data=payload, files=files)
                response.raise_for_status()
                data = response.json()
                if data["ok"]:
                    return data["result"]
                else:
                    raise Exception(f"Telegram API error: {data.get('description', 'Unknown error')}")
            
            if caption:
                payload["caption"] = caption
            if parse_mode:
                payload["parse_mode"] = parse_mode
            if disable_notification:
                payload["disable_notification"] = disable_notification
            if reply_to_message_id:
                payload["reply_to_message_id"] = reply_to_message_id
            if reply_markup:
                payload["reply_markup"] = json.dumps(reply_markup)
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            if data["ok"]:
                return data["result"]
            else:
                raise Exception(f"Telegram API error: {data.get('description', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"Failed to send document: {e}")
            raise
    
    async def get_updates(
        self,
        offset: Optional[int] = None,
        limit: int = 100,
        timeout: int = 0
    ) -> List[TelegramUpdate]:
        """
        Get updates from Telegram.
        
        Args:
            offset: Offset for pagination
            limit: Number of updates to return
            timeout: Timeout for long polling
            
        Returns:
            List of updates
        """
        try:
            url = f"{self.base_url}/getUpdates"
            
            params = {
                "limit": limit,
                "timeout": timeout
            }
            
            if offset:
                params["offset"] = offset
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data["ok"]:
                updates = []
                for update_data in data["result"]:
                    update = self._parse_update(update_data)
                    updates.append(update)
                return updates
            else:
                raise Exception(f"Telegram API error: {data.get('description', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"Failed to get updates: {e}")
            raise
    
    async def set_webhook(
        self,
        url: str,
        certificate: Optional[bytes] = None,
        max_connections: int = 40,
        allowed_updates: Optional[List[str]] = None
    ) -> bool:
        """
        Set webhook URL.
        
        Args:
            url: Webhook URL
            certificate: Certificate file
            max_connections: Maximum connections
            allowed_updates: Allowed update types
            
        Returns:
            True if successful
        """
        try:
            webhook_url = f"{self.base_url}/setWebhook"
            
            payload = {
                "url": url,
                "max_connections": max_connections
            }
            
            if allowed_updates:
                payload["allowed_updates"] = allowed_updates
            
            if certificate:
                files = {"certificate": ("certificate.pem", certificate, "application/x-pem-file")}
                response = self.session.post(webhook_url, data=payload, files=files)
            else:
                response = self.session.post(webhook_url, json=payload)
            
            response.raise_for_status()
            
            data = response.json()
            if data["ok"]:
                return data["result"]
            else:
                raise Exception(f"Telegram API error: {data.get('description', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"Failed to set webhook: {e}")
            raise
    
    async def delete_webhook(self, drop_pending_updates: bool = False) -> bool:
        """
        Delete webhook.
        
        Args:
            drop_pending_updates: Drop pending updates
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.base_url}/deleteWebhook"
            
            params = {}
            if drop_pending_updates:
                params["drop_pending_updates"] = drop_pending_updates
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data["ok"]:
                return data["result"]
            else:
                raise Exception(f"Telegram API error: {data.get('description', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"Failed to delete webhook: {e}")
            raise
    
    async def get_webhook_info(self) -> Dict[str, Any]:
        """
        Get webhook information.
        
        Returns:
            Webhook information
        """
        try:
            url = f"{self.base_url}/getWebhookInfo"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            if data["ok"]:
                return data["result"]
            else:
                raise Exception(f"Telegram API error: {data.get('description', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"Failed to get webhook info: {e}")
            raise
    
    async def get_chat(self, chat_id: Union[int, str]) -> TelegramChat:
        """
        Get chat information.
        
        Args:
            chat_id: Chat ID or username
            
        Returns:
            Chat information
        """
        try:
            url = f"{self.base_url}/getChat"
            params = {"chat_id": chat_id}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data["ok"]:
                chat_data = data["result"]
                return TelegramChat(
                    id=chat_data["id"],
                    type=TelegramChatType(chat_data["type"]),
                    title=chat_data.get("title"),
                    username=chat_data.get("username"),
                    first_name=chat_data.get("first_name"),
                    last_name=chat_data.get("last_name"),
                    description=chat_data.get("description"),
                    invite_link=chat_data.get("invite_link"),
                    member_count=chat_data.get("member_count"),
                    is_forum=chat_data.get("is_forum", False),
                    active_usernames=chat_data.get("active_usernames", [])
                )
            else:
                raise Exception(f"Telegram API error: {data.get('description', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"Failed to get chat: {e}")
            raise
    
    async def get_chat_members_count(self, chat_id: Union[int, str]) -> int:
        """
        Get chat members count.
        
        Args:
            chat_id: Chat ID or username
            
        Returns:
            Members count
        """
        try:
            url = f"{self.base_url}/getChatMembersCount"
            params = {"chat_id": chat_id}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data["ok"]:
                return data["result"]
            else:
                raise Exception(f"Telegram API error: {data.get('description', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"Failed to get chat members count: {e}")
            raise
    
    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False,
        url: Optional[str] = None,
        cache_time: int = 0
    ) -> bool:
        """
        Answer callback query.
        
        Args:
            callback_query_id: Callback query ID
            text: Answer text
            show_alert: Show alert
            url: URL to open
            cache_time: Cache time
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.base_url}/answerCallbackQuery"
            
            payload = {
                "callback_query_id": callback_query_id
            }
            
            if text:
                payload["text"] = text
            if show_alert:
                payload["show_alert"] = show_alert
            if url:
                payload["url"] = url
            if cache_time:
                payload["cache_time"] = cache_time
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            if data["ok"]:
                return data["result"]
            else:
                raise Exception(f"Telegram API error: {data.get('description', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"Failed to answer callback query: {e}")
            raise
    
    def _parse_update(self, update_data: Dict[str, Any]) -> TelegramUpdate:
        """Parse update data into TelegramUpdate object."""
        update = TelegramUpdate(update_id=update_data["update_id"])
        
        if "message" in update_data:
            update.message = self._parse_message(update_data["message"])
        if "edited_message" in update_data:
            update.edited_message = self._parse_message(update_data["edited_message"])
        if "channel_post" in update_data:
            update.channel_post = self._parse_message(update_data["channel_post"])
        if "edited_channel_post" in update_data:
            update.edited_channel_post = self._parse_message(update_data["edited_channel_post"])
        if "callback_query" in update_data:
            update.callback_query = update_data["callback_query"]
        if "inline_query" in update_data:
            update.inline_query = update_data["inline_query"]
        if "chosen_inline_result" in update_data:
            update.chosen_inline_result = update_data["chosen_inline_result"]
        
        return update
    
    def _parse_message(self, message_data: Dict[str, Any]) -> TelegramMessage:
        """Parse message data into TelegramMessage object."""
        message = TelegramMessage(
            message_id=message_data["message_id"],
            chat_id=message_data["chat"]["id"],
            chat_type=TelegramChatType(message_data["chat"]["type"]),
            date=datetime.fromtimestamp(message_data["date"])
        )
        
        if "from" in message_data:
            message.from_user = message_data["from"]
        if "text" in message_data:
            message.text = message_data["text"]
            message.message_type = TelegramMessageType.TEXT
        if "reply_to_message" in message_data:
            message.reply_to_message = message_data["reply_to_message"]
        if "forward_from" in message_data:
            message.forward_from = message_data["forward_from"]
        if "caption" in message_data:
            message.caption = message_data["caption"]
        if "entities" in message_data:
            message.entities = message_data["entities"]
        
        # Determine message type
        if "photo" in message_data:
            message.message_type = TelegramMessageType.PHOTO
            message.media = message_data["photo"]
        elif "video" in message_data:
            message.message_type = TelegramMessageType.VIDEO
            message.media = message_data["video"]
        elif "document" in message_data:
            message.message_type = TelegramMessageType.DOCUMENT
            message.media = message_data["document"]
        elif "audio" in message_data:
            message.message_type = TelegramMessageType.AUDIO
            message.media = message_data["audio"]
        elif "voice" in message_data:
            message.message_type = TelegramMessageType.VOICE
            message.media = message_data["voice"]
        elif "location" in message_data:
            message.message_type = TelegramMessageType.LOCATION
            message.media = message_data["location"]
        elif "contact" in message_data:
            message.message_type = TelegramMessageType.CONTACT
            message.media = message_data["contact"]
        elif "poll" in message_data:
            message.message_type = TelegramMessageType.POLL
            message.media = message_data["poll"]
        
        return message
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Telegram integration.
        
        Returns:
            Health check results
        """
        try:
            # Test bot info
            bot_info = await self.get_me()
            
            # Test webhook info
            webhook_info = await self.get_webhook_info()
            
            return {
                "status": "healthy",
                "bot_username": bot_info.get("username"),
                "bot_name": bot_info.get("first_name"),
                "webhook_url": webhook_info.get("url"),
                "webhook_pending_update_count": webhook_info.get("pending_update_count", 0),
                "last_checked": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }

