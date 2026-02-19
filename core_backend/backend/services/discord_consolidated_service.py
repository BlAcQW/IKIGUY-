"""
Discord Consolidated Integration Service.
Handles all Discord-related functionality with unified interface and MCP support.
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field

# Import from shared integration
import sys
sys.path.append('/opt/kasaai/apps/shared')
from integration.discord import DiscordIntegration, DiscordConfig

logger = logging.getLogger(__name__)


class DiscordServiceWrapper(DiscordIntegration):
    """
    Consolidated service for Discord integration.
    Extends the shared Discord service with additional functionality and MCP support.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Discord service with configuration.

        Args:
            config: Configuration dictionary with Discord settings
        """
        if config:
            # Convert dict config to DiscordConfig
            discord_config = DiscordConfig(
                bot_token=config.get("bot_token", os.getenv("DISCORD_BOT_TOKEN", "")),
                guild_id=config.get("guild_id", os.getenv("DISCORD_GUILD_ID", "")),
                timeout=config.get("timeout", 30)
            )
            super().__init__(discord_config)
        else:
            # Use environment variables with defaults
            discord_config = DiscordConfig(
                bot_token=os.getenv("DISCORD_BOT_TOKEN", ""),
                guild_id=os.getenv("DISCORD_GUILD_ID", ""),
                timeout=30
            )
            super().__init__(discord_config)

    # Additional consolidated service methods
    async def get_service_info(self) -> Dict[str, Any]:
        """Get service information and status."""
        try:
            guild_info = await self.get_guild_info()
            return {
                "service_name": "Discord Consolidated",
                "service_type": "Gaming/Community Platform",
                "version": "1.0.0",
                "guild_info": guild_info,
                "capabilities": [
                    "send_messages",
                    "send_embeds",
                    "manage_channels",
                    "manage_roles",
                    "webhook_support",
                    "voice_integration",
                    "bot_commands"
                ]
            }
        except Exception as e:
            return {
                "service_name": "Discord Consolidated",
                "service_type": "Gaming/Community Platform",
                "version": "1.0.0",
                "error": str(e),
                "capabilities": []
            }

    async def bulk_send_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Send multiple messages in batch."""
        results = []
        for message_data in messages:
            try:
                channel_id = message_data.get("channel_id", self.config.channel_id)
                content = message_data.get("content", "")
                embed = message_data.get("embed")

                if embed:
                    result = await self.send_embed(embed, channel_id)
                else:
                    result = await self.send_message(content, channel_id)

                results.append({"success": True, "data": result, "channel_id": channel_id})
            except Exception as e:
                results.append({
                    "success": False,
                    "error": str(e),
                    "data": message_data,
                    "channel_id": message_data.get("channel_id")
                })
        return results

    async def send_notification_with_retry(self, content: str, max_retries: int = 3) -> Dict[str, Any]:
        """Send notification with automatic retry logic."""
        for attempt in range(max_retries):
            try:
                result = await self.send_message(content)
                return {"success": True, "data": result, "attempts": attempt + 1}
            except Exception as e:
                if attempt == max_retries - 1:
                    return {"success": False, "error": str(e), "attempts": attempt + 1}
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        return {"success": False, "error": "Max retries exceeded"}

    async def get_server_analytics(self) -> Dict[str, Any]:
        """Get basic server analytics."""
        try:
            guild_info = await self.get_guild_info()
            channels = await self.get_channels()
            roles = await self.get_roles()

            return {
                "guild_info": guild_info,
                "channels_count": len(channels),
                "roles_count": len(roles),
                "analytics_generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating server analytics: {e}")
            return {"error": str(e)}

    async def create_announcement_embed(self, title: str, description: str, color: int = 0x00ff00) -> Dict[str, Any]:
        """Create a formatted announcement embed."""
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "Powered by KasaAI"
            }
        }
        return embed


# Create a singleton instance for use throughout the application
def get_discord_service(config: Optional[Dict[str, Any]] = None) -> DiscordServiceWrapper:
    """Get Discord service instance."""
    return DiscordServiceWrapper(config)


# For backward compatibility
discord_consolidated_service = get_discord_service()