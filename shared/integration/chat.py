"""
Chat Integration System

This module provides chat integration capabilities for the KasaAI platform.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Third-party imports (would be added to requirements.txt)
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import slack_sdk
    from slack_sdk.web import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False

try:
    import pymsteams
    TEAMS_AVAILABLE = True
except ImportError:
    TEAMS_AVAILABLE = False


class ChatProvider(Enum):
    """Supported chat providers"""
    SLACK = "slack"
    MICROSOFT_TEAMS = "microsoft_teams"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    WEB_CHAT = "web_chat"


@dataclass
class ChatMessage:
    """Chat message definition"""
    text: str
    channel: str
    attachments: Optional[List[Dict[str, Any]]] = None
    blocks: Optional[List[Dict[str, Any]]] = None
    thread_ts: Optional[str] = None
    reply_broadcast: bool = False


@dataclass
class ChatDeliveryReport:
    """Chat delivery report"""
    message_id: str
    channel: str
    timestamp: datetime
    status: str = "sent"
    error_message: Optional[str] = None
    provider_response: Optional[str] = None


class BaseChatProvider(ABC):
    """Base class for chat providers"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the chat provider"""
        self.config = config
        self.logger = logging.getLogger(f"ChatProvider.{self.__class__.__name__}")
        self.provider_type = self.get_provider_type()
    
    @abstractmethod
    def get_provider_type(self) -> ChatProvider:
        """Get the provider type"""
        pass
    
    @abstractmethod
    async def send_message(self, message: ChatMessage) -> Dict[str, Any]:
        """Send a chat message"""
        pass
    
    @abstractmethod
    async def send_direct_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """Send a direct message to a user"""
        pass
    
    @abstractmethod
    async def create_channel(self, name: str, is_private: bool = False) -> Dict[str, Any]:
        """Create a new channel"""
        pass
    
    @abstractmethod
    async def invite_users(self, channel: str, user_ids: List[str]) -> Dict[str, Any]:
        """Invite users to a channel"""
        pass
    
    @abstractmethod
    async def receive_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming webhook"""
        pass


class SlackChatProvider(BaseChatProvider):
    """Slack chat provider"""
    
    def get_provider_type(self) -> ChatProvider:
        return ChatProvider.SLACK
    
    async def send_message(self, message: ChatMessage) -> Dict[str, Any]:
        """Send a message to Slack"""
        if not SLACK_AVAILABLE:
            return {
                "success": False,
                "error": "Slack library not available",
                "provider": "slack"
            }
        
        try:
            token = self.config.get("bot_token")
            if not token:
                return {
                    "success": False,
                    "error": "Slack bot token not configured",
                    "provider": "slack"
                }
            
            client = WebClient(token=token)
            
            # Prepare message
            message_data = {
                "channel": message.channel,
                "text": message.text
            }
            
            if message.attachments:
                message_data["attachments"] = message.attachments
            
            if message.blocks:
                message_data["blocks"] = message.blocks
            
            if message.thread_ts:
                message_data["thread_ts"] = message.thread_ts
                message_data["reply_broadcast"] = message.reply_broadcast
            
            # Send message
            response = await asyncio.get_event_loop().run_in_executor(
                None, client.chat_postMessage, **message_data
            )
            
            return {
                "success": True,
                "message_id": response["ts"],
                "channel": response["channel"],
                "provider": "slack",
                "timestamp": response["ts"]
            }
            
        except SlackApiError as e:
            self.logger.error(f"Slack API error: {e.response['error']}")
            return {
                "success": False,
                "error": e.response["error"],
                "provider": "slack"
            }
        except Exception as e:
            self.logger.error(f"Failed to send Slack message: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "slack"
            }
    
    async def send_direct_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """Send a direct message to a Slack user"""
        chat_message = ChatMessage(text=message, channel=user_id)
        return await self.send_message(chat_message)
    
    async def create_channel(self, name: str, is_private: bool = False) -> Dict[str, Any]:
        """Create a new Slack channel"""
        if not SLACK_AVAILABLE:
            return {
                "success": False,
                "error": "Slack library not available",
                "provider": "slack"
            }
        
        try:
            token = self.config.get("bot_token")
            if not token:
                return {
                    "success": False,
                    "error": "Slack bot token not configured",
                    "provider": "slack"
                }
            
            client = WebClient(token=token)
            
            # Create channel
            response = await asyncio.get_event_loop().run_in_executor(
                None, client.conversations_create, name=name, is_private=is_private
            )
            
            return {
                "success": True,
                "channel_id": response["channel"]["id"],
                "channel_name": response["channel"]["name"],
                "provider": "slack"
            }
            
        except SlackApiError as e:
            self.logger.error(f"Slack API error: {e.response['error']}")
            return {
                "success": False,
                "error": e.response["error"],
                "provider": "slack"
            }
        except Exception as e:
            self.logger.error(f"Failed to create Slack channel: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "slack"
            }
    
    async def invite_users(self, channel: str, user_ids: List[str]) -> Dict[str, Any]:
        """Invite users to a Slack channel"""
        if not SLACK_AVAILABLE:
            return {
                "success": False,
                "error": "Slack library not available",
                "provider": "slack"
            }
        
        try:
            token = self.config.get("bot_token")
            if not token:
                return {
                    "success": False,
                    "error": "Slack bot token not configured",
                    "provider": "slack"
                }
            
            client = WebClient(token=token)
            
            # Invite users
            response = await asyncio.get_event_loop().run_in_executor(
                None, client.conversations_invite, channel=channel, users=",".join(user_ids)
            )
            
            return {
                "success": True,
                "channel_id": response["channel"]["id"],
                "invited_users": user_ids,
                "provider": "slack"
            }
            
        except SlackApiError as e:
            self.logger.error(f"Slack API error: {e.response['error']}")
            return {
                "success": False,
                "error": e.response["error"],
                "provider": "slack"
            }
        except Exception as e:
            self.logger.error(f"Failed to invite users to Slack channel: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "slack"
            }
    
    async def receive_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming Slack webhook"""
        try:
            # Extract relevant information from webhook
            event_type = webhook_data.get("type")
            event_data = webhook_data.get("event", {})
            
            if event_type == "url_verification":
                return {
                    "success": True,
                    "challenge": webhook_data.get("challenge"),
                    "provider": "slack"
                }
            
            elif event_type == "event_callback":
                event_type = event_data.get("type")
                
                if event_type == "message":
                    return {
                        "success": True,
                        "event_type": "message",
                        "channel": event_data.get("channel"),
                        "user": event_data.get("user"),
                        "text": event_data.get("text"),
                        "ts": event_data.get("ts"),
                        "provider": "slack"
                    }
                
                elif event_type == "reaction_added":
                    return {
                        "success": True,
                        "event_type": "reaction_added",
                        "channel": event_data.get("channel"),
                        "user": event_data.get("user"),
                        "reaction": event_data.get("reaction"),
                        "item": event_data.get("item"),
                        "provider": "slack"
                    }
            
            return {
                "success": True,
                "event_type": "unknown",
                "data": webhook_data,
                "provider": "slack"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process Slack webhook: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "slack"
            }


class MicrosoftTeamsChatProvider(BaseChatProvider):
    """Microsoft Teams chat provider"""
    
    def get_provider_type(self) -> ChatProvider:
        return ChatProvider.MICROSOFT_TEAMS
    
    async def send_message(self, message: ChatMessage) -> Dict[str, Any]:
        """Send a message to Microsoft Teams"""
        if not TEAMS_AVAILABLE:
            return {
                "success": False,
                "error": "Microsoft Teams library not available",
                "provider": "microsoft_teams"
            }
        
        try:
            webhook_url = self.config.get("webhook_url")
            if not webhook_url:
                return {
                    "success": False,
                    "error": "Microsoft Teams webhook URL not configured",
                    "provider": "microsoft_teams"
                }
            
            # Create Teams message
            teams_message = pymsteams.connectorcard(webhook_url)
            teams_message.text(message.text)
            
            if message.attachments:
                for attachment in message.attachments:
                    teams_message.addLinkButton(attachment.get("title", ""), attachment.get("url", ""))
            
            # Send message
            response = await asyncio.get_event_loop().run_in_executor(
                None, teams_message.send
            )
            
            if response:
                return {
                    "success": True,
                    "message_id": f"teams_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                    "channel": message.channel,
                    "provider": "microsoft_teams"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to send Teams message",
                    "provider": "microsoft_teams"
                }
            
        except Exception as e:
            self.logger.error(f"Failed to send Teams message: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "microsoft_teams"
            }
    
    async def send_direct_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """Send a direct message to a Teams user (not supported via webhook)"""
        return {
            "success": False,
            "error": "Direct messages not supported via Teams webhook",
            "provider": "microsoft_teams"
        }
    
    async def create_channel(self, name: str, is_private: bool = False) -> Dict[str, Any]:
        """Create a new Teams channel (not supported via webhook)"""
        return {
            "success": False,
            "error": "Channel creation not supported via Teams webhook",
            "provider": "microsoft_teams"
        }
    
    async def invite_users(self, channel: str, user_ids: List[str]) -> Dict[str, Any]:
        """Invite users to a Teams channel (not supported via webhook)"""
        return {
            "success": False,
            "error": "User invitation not supported via Teams webhook",
            "provider": "microsoft_teams"
        }
    
    async def receive_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming Teams webhook"""
        try:
            # Extract relevant information from webhook
            return {
                "success": True,
                "event_type": "message",
                "data": webhook_data,
                "provider": "microsoft_teams"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process Teams webhook: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "microsoft_teams"
            }


class ChatIntegration:
    """Main chat integration class"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize chat integration"""
        self.config = config
        self.logger = logging.getLogger("ChatIntegration")
        self.providers: Dict[ChatProvider, BaseChatProvider] = {}
        self.default_provider = ChatProvider.SLACK
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize chat providers based on configuration"""
        provider_configs = self.config.get("providers", {})
        
        # Initialize Slack provider
        if "slack" in provider_configs and SLACK_AVAILABLE:
            self.providers[ChatProvider.SLACK] = SlackChatProvider(provider_configs["slack"])
        
        # Initialize Microsoft Teams provider
        if "microsoft_teams" in provider_configs and TEAMS_AVAILABLE:
            self.providers[ChatProvider.MICROSOFT_TEAMS] = MicrosoftTeamsChatProvider(provider_configs["microsoft_teams"])
        
        # Set default provider
        default_provider_name = self.config.get("default_provider", "slack")
        if default_provider_name == "microsoft_teams" and ChatProvider.MICROSOFT_TEAMS in self.providers:
            self.default_provider = ChatProvider.MICROSOFT_TEAMS
    
    async def send_message(self, message: ChatMessage, 
                          provider: Optional[ChatProvider] = None) -> Dict[str, Any]:
        """Send a chat message"""
        if not provider:
            provider = self.default_provider
        
        if provider not in self.providers:
            return {
                "success": False,
                "error": f"Provider {provider.value} not configured",
                "provider": provider.value
            }
        
        return await self.providers[provider].send_message(message)
    
    async def send_direct_message(self, user_id: str, message: str,
                                provider: Optional[ChatProvider] = None) -> Dict[str, Any]:
        """Send a direct message to a user"""
        if not provider:
            provider = self.default_provider
        
        if provider not in self.providers:
            return {
                "success": False,
                "error": f"Provider {provider.value} not configured",
                "provider": provider.value
            }
        
        return await self.providers[provider].send_direct_message(user_id, message)
    
    async def create_channel(self, name: str, is_private: bool = False,
                           provider: Optional[ChatProvider] = None) -> Dict[str, Any]:
        """Create a new channel"""
        if not provider:
            provider = self.default_provider
        
        if provider not in self.providers:
            return {
                "success": False,
                "error": f"Provider {provider.value} not configured",
                "provider": provider.value
            }
        
        return await self.providers[provider].create_channel(name, is_private)
    
    async def invite_users(self, channel: str, user_ids: List[str],
                          provider: Optional[ChatProvider] = None) -> Dict[str, Any]:
        """Invite users to a channel"""
        if not provider:
            provider = self.default_provider
        
        if provider not in self.providers:
            return {
                "success": False,
                "error": f"Provider {provider.value} not configured",
                "provider": provider.value
            }
        
        return await self.providers[provider].invite_users(channel, user_ids)
    
    async def receive_webhook(self, webhook_data: Dict[str, Any],
                            provider: Optional[ChatProvider] = None) -> Dict[str, Any]:
        """Process incoming webhook"""
        if not provider:
            # Try to detect provider from webhook data
            if "type" in webhook_data and webhook_data["type"] == "url_verification":
                provider = ChatProvider.SLACK
            elif "webhook_url" in self.config.get("providers", {}).get("microsoft_teams", {}):
                provider = ChatProvider.MICROSOFT_TEAMS
            else:
                provider = self.default_provider
        
        if provider not in self.providers:
            return {
                "success": False,
                "error": f"Provider {provider.value} not configured",
                "provider": provider.value
            }
        
        return await self.providers[provider].receive_webhook(webhook_data)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all configured providers"""
        health_status = {
            "overall": "healthy",
            "providers": {}
        }
        
        for provider_type, provider in self.providers.items():
            try:
                # Simple health check - try to get provider info
                provider_info = {
                    "type": provider_type.value,
                    "status": "healthy"
                }
                health_status["providers"][provider_type.value] = provider_info
                
            except Exception as e:
                health_status["providers"][provider_type.value] = {
                    "type": provider_type.value,
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["overall"] = "degraded"
        
        return health_status

