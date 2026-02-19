"""
Telegram Consolidated Integration Service.
Handles all Telegram-related functionality with unified interface and MCP support.
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
from integration.telegram import TelegramIntegration, TelegramConfig

logger = logging.getLogger(__name__)


class TelegramServiceWrapper(TelegramIntegration):
    """
    Consolidated service for Telegram integration.
    Extends the shared Telegram service with additional functionality and MCP support.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Telegram service with configuration.

        Args:
            config: Configuration dictionary with Telegram settings
        """
        if config:
            # Convert dict config to TelegramConfig
            telegram_config = TelegramConfig(
                bot_token=config.get("bot_token", os.getenv("TELEGRAM_BOT_TOKEN", "")),
                api_base_url=config.get("api_base_url", "https://api.telegram.org"),
                timeout=config.get("timeout", 30),
                webhook_url=config.get("webhook_url"),
                allowed_updates=config.get("allowed_updates", [])
            )
            super().__init__(telegram_config)
        else:
            # Use environment variables with defaults
            telegram_config = TelegramConfig(
                bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
                api_base_url="https://api.telegram.org",
                timeout=30,
                webhook_url=None,
                allowed_updates=[]
            )
            super().__init__(telegram_config)

    # Additional consolidated service methods
    async def get_service_info(self) -> Dict[str, Any]:
        """Get service information and status."""
        try:
            bot_info = await self.get_bot_info()
            return {
                "service_name": "Telegram Consolidated",
                "service_type": "Messaging Platform",
                "version": "1.0.0",
                "bot_info": bot_info,
                "capabilities": [
                    "send_messages",
                    "send_photos",
                    "send_documents",
                    "bot_management",
                    "webhook_support",
                    "inline_keyboards"
                ]
            }
        except Exception as e:
            return {
                "service_name": "Telegram Consolidated",
                "service_type": "Messaging Platform",
                "version": "1.0.0",
                "error": str(e),
                "capabilities": []
            }

    async def bulk_send_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Send multiple messages in batch."""
        results = []
        for message_data in messages:
            try:
                chat_id = message_data.get("chat_id", os.getenv("TELEGRAM_CHAT_ID", ""))
                text = message_data.get("text", "")
                parse_mode = message_data.get("parse_mode", "HTML")

                result = await self.send_message(text, chat_id, parse_mode)
                results.append({"success": True, "data": result, "chat_id": chat_id})
            except Exception as e:
                results.append({
                    "success": False,
                    "error": str(e),
                    "data": message_data,
                    "chat_id": message_data.get("chat_id")
                })
        return results

    async def send_notification_with_retry(self, text: str, max_retries: int = 3) -> Dict[str, Any]:
        """Send notification with automatic retry logic."""
        for attempt in range(max_retries):
            try:
                result = await self.send_message(text)
                return {"success": True, "data": result, "attempts": attempt + 1}
            except Exception as e:
                if attempt == max_retries - 1:
                    return {"success": False, "error": str(e), "attempts": attempt + 1}
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        return {"success": False, "error": "Max retries exceeded"}

    async def get_chat_analytics(self) -> Dict[str, Any]:
        """Get basic chat analytics."""
        try:
            updates = await self.get_updates()
            chat_info = await self.get_chat_info(os.getenv("TELEGRAM_CHAT_ID", ""))

            return {
                "chat_info": chat_info,
                "recent_updates_count": len(updates.get("result", [])),
                "analytics_generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating chat analytics: {e}")
            return {"error": str(e)}


# Create a singleton instance for use throughout the application
def get_telegram_service(config: Optional[Dict[str, Any]] = None) -> TelegramServiceWrapper:
    """Get Telegram service instance."""
    return TelegramServiceWrapper(config)


# For backward compatibility
telegram_consolidated_service = get_telegram_service()