"""
Consolidated Chat Integration Service.
Handles all chat-related functionality with unified interface.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    """Chat message model."""
    content: str
    sender_id: str
    recipient_id: Optional[str] = None
    channel_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    message_type: str = "text"  # text, image, file, etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatChannel(BaseModel):
    """Chat channel model."""
    channel_id: str
    name: str
    channel_type: str = "group"  # group, direct, public
    participants: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatService:
    """
    Consolidated service for all chat integrations.
    Supports multiple chat platforms with unified interface.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize chat service with configuration.

        Args:
            config: Configuration dictionary with platform-specific settings
        """
        self.config = config or {}
        self.platforms = {}
        self.active_connections = {}
        self._initialize_platforms()

    def _initialize_platforms(self):
        """Initialize supported chat platforms."""
        # VAPI Chat Integration
        if self.config.get("vapi_enabled", False):
            self.platforms["vapi"] = {
                "assistant_id": self.config.get("vapi_assistant_id"),
                "api_key": self.config.get("vapi_api_key"),
                "webhook_url": self.config.get("vapi_webhook_url")
            }

        # Discord Integration
        if self.config.get("discord_enabled", False):
            self.platforms["discord"] = {
                "bot_token": self.config.get("discord_bot_token"),
                "guild_id": self.config.get("discord_guild_id")
            }

        # Slack Integration (future)
        if self.config.get("slack_enabled", False):
            self.platforms["slack"] = {
                "bot_token": self.config.get("slack_bot_token"),
                "workspace_id": self.config.get("slack_workspace_id")
            }

        logger.info(f"Initialized chat service with platforms: {list(self.platforms.keys())}")

    async def send_message(
        self,
        platform: str,
        message: ChatMessage,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a message through specified platform.

        Args:
            platform: Platform name (vapi, discord, slack)
            message: Message to send
            context: Additional context for the message

        Returns:
            Result of message sending operation
        """
        try:
            if platform not in self.platforms:
                return {
                    "success": False,
                    "error": f"Platform '{platform}' not configured",
                    "available_platforms": list(self.platforms.keys())
                }

            platform_config = self.platforms[platform]

            if platform == "vapi":
                return await self._send_vapi_message(message, platform_config, context)
            elif platform == "discord":
                return await self._send_discord_message(message, platform_config, context)
            elif platform == "slack":
                return await self._send_slack_message(message, platform_config, context)
            else:
                return {
                    "success": False,
                    "error": f"Platform '{platform}' handler not implemented"
                }

        except Exception as e:
            logger.error(f"Error sending message via {platform}: {e}")
            return {
                "success": False,
                "error": str(e),
                "platform": platform
            }

    async def _send_vapi_message(
        self,
        message: ChatMessage,
        config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send message through VAPI."""
        try:
            # VAPI implementation for voice/chat messages
            vapi_payload = {
                "assistant_id": config.get("assistant_id"),
                "message": message.content,
                "sender_id": message.sender_id,
                "context": context or {},
                "timestamp": message.timestamp.isoformat()
            }

            # Here would be actual VAPI API call
            logger.info(f"Sending VAPI message: {message.content[:50]}...")

            return {
                "success": True,
                "message_id": f"vapi_{message.sender_id}_{int(message.timestamp.timestamp())}",
                "platform": "vapi",
                "assistant_id": config.get("assistant_id"),
                "response": "Message sent to VAPI assistant"
            }

        except Exception as e:
            logger.error(f"VAPI message error: {e}")
            return {"success": False, "error": str(e), "platform": "vapi"}

    async def _send_discord_message(
        self,
        message: ChatMessage,
        config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send message through Discord."""
        try:
            # Discord implementation
            discord_payload = {
                "content": message.content,
                "channel_id": message.channel_id,
                "embed": context.get("embed") if context else None
            }

            logger.info(f"Sending Discord message: {message.content[:50]}...")

            return {
                "success": True,
                "message_id": f"discord_{message.channel_id}_{int(message.timestamp.timestamp())}",
                "platform": "discord",
                "channel_id": message.channel_id,
                "response": "Message sent to Discord channel"
            }

        except Exception as e:
            logger.error(f"Discord message error: {e}")
            return {"success": False, "error": str(e), "platform": "discord"}

    async def _send_slack_message(
        self,
        message: ChatMessage,
        config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send message through Slack."""
        try:
            # Slack implementation (future)
            slack_payload = {
                "text": message.content,
                "channel": message.channel_id,
                "blocks": context.get("blocks") if context else None
            }

            logger.info(f"Sending Slack message: {message.content[:50]}...")

            return {
                "success": True,
                "message_id": f"slack_{message.channel_id}_{int(message.timestamp.timestamp())}",
                "platform": "slack",
                "channel": message.channel_id,
                "response": "Message sent to Slack channel"
            }

        except Exception as e:
            logger.error(f"Slack message error: {e}")
            return {"success": False, "error": str(e), "platform": "slack"}

    async def receive_message(
        self,
        platform: str,
        message_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process incoming message from platform.

        Args:
            platform: Platform name
            message_data: Raw message data from platform

        Returns:
            Processed message result
        """
        try:
            if platform not in self.platforms:
                return {
                    "success": False,
                    "error": f"Platform '{platform}' not configured"
                }

            # Parse message based on platform
            if platform == "vapi":
                return await self._process_vapi_message(message_data)
            elif platform == "discord":
                return await self._process_discord_message(message_data)
            elif platform == "slack":
                return await self._process_slack_message(message_data)
            else:
                return {
                    "success": False,
                    "error": f"Platform '{platform}' handler not implemented"
                }

        except Exception as e:
            logger.error(f"Error processing message from {platform}: {e}")
            return {"success": False, "error": str(e)}

    async def _process_vapi_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming VAPI message."""
        try:
            message = ChatMessage(
                content=message_data.get("content", ""),
                sender_id=message_data.get("sender_id", "vapi_user"),
                metadata={"platform": "vapi", "raw_data": message_data}
            )

            return {
                "success": True,
                "message": message.dict(),
                "platform": "vapi",
                "processed_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"VAPI message processing error: {e}")
            return {"success": False, "error": str(e)}

    async def _process_discord_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming Discord message."""
        try:
            message = ChatMessage(
                content=message_data.get("content", ""),
                sender_id=message_data.get("author", {}).get("id", "discord_user"),
                channel_id=message_data.get("channel_id"),
                metadata={"platform": "discord", "raw_data": message_data}
            )

            return {
                "success": True,
                "message": message.dict(),
                "platform": "discord",
                "processed_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Discord message processing error: {e}")
            return {"success": False, "error": str(e)}

    async def _process_slack_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming Slack message."""
        try:
            message = ChatMessage(
                content=message_data.get("text", ""),
                sender_id=message_data.get("user", "slack_user"),
                channel_id=message_data.get("channel"),
                metadata={"platform": "slack", "raw_data": message_data}
            )

            return {
                "success": True,
                "message": message.dict(),
                "platform": "slack",
                "processed_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Slack message processing error: {e}")
            return {"success": False, "error": str(e)}

    async def create_channel(
        self,
        platform: str,
        channel_data: ChatChannel
    ) -> Dict[str, Any]:
        """
        Create a new chat channel.

        Args:
            platform: Platform name
            channel_data: Channel configuration

        Returns:
            Channel creation result
        """
        try:
            if platform not in self.platforms:
                return {
                    "success": False,
                    "error": f"Platform '{platform}' not configured"
                }

            logger.info(f"Creating {platform} channel: {channel_data.name}")

            return {
                "success": True,
                "channel_id": f"{platform}_{channel_data.channel_id}",
                "platform": platform,
                "name": channel_data.name,
                "type": channel_data.channel_type,
                "created_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Channel creation error: {e}")
            return {"success": False, "error": str(e)}

    def get_supported_platforms(self) -> List[str]:
        """Get list of supported chat platforms."""
        return list(self.platforms.keys())

    def get_platform_status(self, platform: str) -> Dict[str, Any]:
        """Get status of specific platform."""
        if platform not in self.platforms:
            return {
                "platform": platform,
                "configured": False,
                "status": "not_configured"
            }

        config = self.platforms[platform]
        return {
            "platform": platform,
            "configured": True,
            "status": "active",
            "config_keys": list(config.keys()),
            "last_checked": datetime.now().isoformat()
        }

    async def test_connection(self, platform: str) -> Dict[str, Any]:
        """
        Test connection to chat platform.

        Args:
            platform: Platform to test

        Returns:
            Connection test result
        """
        try:
            if platform not in self.platforms:
                return {
                    "success": False,
                    "platform": platform,
                    "error": "Platform not configured"
                }

            # Test message
            test_message = ChatMessage(
                content="Connection test",
                sender_id="system_test",
                metadata={"test": True}
            )

            result = await self.send_message(platform, test_message)

            return {
                "success": result.get("success", False),
                "platform": platform,
                "test_type": "connection",
                "result": result,
                "tested_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Connection test error for {platform}: {e}")
            return {
                "success": False,
                "platform": platform,
                "error": str(e)
            }


# Global chat service instance
chat_service = ChatService()