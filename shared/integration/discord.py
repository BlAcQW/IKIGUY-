"""
Discord Integration Module

This module provides integration with Discord for messaging, bot management,
and server communication.
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
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    logging.warning("Discord APIs not available. Install requests")

logger = logging.getLogger(__name__)


class DiscordMessageType(Enum):
    """Discord message types."""
    TEXT = 0
    RECIPIENT_ADD = 1
    RECIPIENT_REMOVE = 2
    CALL = 3
    CHANNEL_NAME_CHANGE = 4
    CHANNEL_ICON_CHANGE = 5
    CHANNEL_PINNED_MESSAGE = 6
    GUILD_MEMBER_JOIN = 7
    USER_PREMIUM_GUILD_SUBSCRIPTION = 8
    USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_1 = 9
    USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_2 = 10
    USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_3 = 11
    CHANNEL_FOLLOW_ADD = 12
    GUILD_DISCOVERY_DISQUALIFIED = 14
    GUILD_DISCOVERY_REQUALIFIED = 15
    GUILD_DISCOVERY_GRACE_PERIOD_INITIAL_WARNING = 16
    GUILD_DISCOVERY_GRACE_PERIOD_FINAL_WARNING = 17
    THREAD_CREATED = 18
    REPLY = 19
    CHAT_INPUT_COMMAND = 20
    THREAD_STARTER_MESSAGE = 21
    GUILD_INVITE_REMINDER = 22
    CONTEXT_MENU_COMMAND = 23
    AUTO_MODERATION_ACTION = 24


class DiscordChannelType(Enum):
    """Discord channel types."""
    GUILD_TEXT = 0
    DM = 1
    GUILD_VOICE = 2
    GROUP_DM = 3
    GUILD_CATEGORY = 4
    GUILD_NEWS = 5
    GUILD_NEWS_THREAD = 10
    GUILD_PUBLIC_THREAD = 11
    GUILD_PRIVATE_THREAD = 12
    GUILD_STAGE_VOICE = 13
    GUILD_DIRECTORY = 14
    GUILD_FORUM = 15


@dataclass
class DiscordConfig:
    """Configuration for Discord integration."""
    
    bot_token: str
    """Discord bot token."""
    
    api_base_url: str = "https://discord.com/api/v10"
    """Discord API base URL."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    application_id: Optional[str] = None
    """Application ID for slash commands."""
    
    guild_id: Optional[str] = None
    """Guild ID for guild-specific commands."""


@dataclass
class DiscordMessage:
    """Discord message data structure."""
    
    id: str
    """Message ID."""
    
    channel_id: str
    """Channel ID."""
    
    author: Dict[str, Any]
    """Message author."""
    
    content: str
    """Message content."""
    
    timestamp: datetime
    """Message timestamp."""
    
    guild_id: Optional[str] = None
    """Guild ID."""
    
    edited_timestamp: Optional[datetime] = None
    """Edited timestamp."""
    
    tts: bool = False
    """Text-to-speech."""
    
    mention_everyone: bool = False
    """Mention everyone."""
    
    mentions: List[Dict[str, Any]] = field(default_factory=list)
    """User mentions."""
    
    mention_roles: List[str] = field(default_factory=list)
    """Role mentions."""
    
    mention_channels: List[Dict[str, Any]] = field(default_factory=list)
    """Channel mentions."""
    
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    """Attachments."""
    
    embeds: List[Dict[str, Any]] = field(default_factory=list)
    """Embeds."""
    
    reactions: List[Dict[str, Any]] = field(default_factory=list)
    """Reactions."""
    
    nonce: Optional[Union[str, int]] = None
    """Nonce."""
    
    pinned: bool = False
    """Pinned message."""
    
    webhook_id: Optional[str] = None
    """Webhook ID."""
    
    type: DiscordMessageType = DiscordMessageType.TEXT
    """Message type."""
    
    activity: Optional[Dict[str, Any]] = None
    """Activity."""
    
    application: Optional[Dict[str, Any]] = None
    """Application."""
    
    application_id: Optional[str] = None
    """Application ID."""
    
    message_reference: Optional[Dict[str, Any]] = None
    """Message reference."""
    
    flags: Optional[int] = None
    """Message flags."""
    
    referenced_message: Optional[Dict[str, Any]] = None
    """Referenced message."""
    
    interaction: Optional[Dict[str, Any]] = None
    """Interaction."""
    
    thread: Optional[Dict[str, Any]] = None
    """Thread."""
    
    components: List[Dict[str, Any]] = field(default_factory=list)
    """Components."""
    
    sticker_items: List[Dict[str, Any]] = field(default_factory=list)
    """Sticker items."""
    
    position: Optional[int] = None
    """Position."""


@dataclass
class DiscordChannel:
    """Discord channel data structure."""
    
    id: str
    """Channel ID."""
    
    type: DiscordChannelType
    """Channel type."""
    
    guild_id: Optional[str] = None
    """Guild ID."""
    
    position: Optional[int] = None
    """Position."""
    
    permission_overwrites: List[Dict[str, Any]] = field(default_factory=list)
    """Permission overwrites."""
    
    name: Optional[str] = None
    """Channel name."""
    
    topic: Optional[str] = None
    """Channel topic."""
    
    nsfw: bool = False
    """NSFW channel."""
    
    last_message_id: Optional[str] = None
    """Last message ID."""
    
    bitrate: Optional[int] = None
    """Bitrate (voice channels)."""
    
    user_limit: Optional[int] = None
    """User limit (voice channels)."""
    
    rate_limit_per_user: Optional[int] = None
    """Rate limit per user."""
    
    recipients: List[Dict[str, Any]] = field(default_factory=list)
    """Recipients (DM channels)."""
    
    icon: Optional[str] = None
    """Channel icon."""
    
    owner_id: Optional[str] = None
    """Owner ID."""
    
    application_id: Optional[str] = None
    """Application ID."""
    
    managed: bool = False
    """Managed channel."""
    
    parent_id: Optional[str] = None
    """Parent ID."""
    
    last_pin_timestamp: Optional[datetime] = None
    """Last pin timestamp."""
    
    rtc_region: Optional[str] = None
    """RTC region."""
    
    video_quality_mode: Optional[int] = None
    """Video quality mode."""
    
    message_count: Optional[int] = None
    """Message count."""
    
    member_count: Optional[int] = None
    """Member count."""
    
    thread_metadata: Optional[Dict[str, Any]] = None
    """Thread metadata."""
    
    member: Optional[Dict[str, Any]] = None
    """Thread member."""
    
    default_auto_archive_duration: Optional[int] = None
    """Default auto archive duration."""
    
    permissions: Optional[str] = None
    """Permissions."""
    
    flags: Optional[int] = None
    """Channel flags."""
    
    total_message_sent: Optional[int] = None
    """Total messages sent."""
    
    available_tags: List[Dict[str, Any]] = field(default_factory=list)
    """Available tags."""
    
    applied_tags: List[str] = field(default_factory=list)
    """Applied tags."""
    
    default_reaction_emoji: Optional[Dict[str, Any]] = None
    """Default reaction emoji."""
    
    default_thread_rate_limit_per_user: Optional[int] = None
    """Default thread rate limit per user."""
    
    default_sort_order: Optional[int] = None
    """Default sort order."""
    
    default_forum_layout: Optional[int] = None
    """Default forum layout."""


@dataclass
class DiscordGuild:
    """Discord guild data structure."""
    
    id: str
    """Guild ID."""
    
    name: str
    """Guild name."""
    
    owner_id: str
    """Owner ID."""
    
    icon: Optional[str] = None
    """Guild icon."""
    
    icon_hash: Optional[str] = None
    """Icon hash."""
    
    splash: Optional[str] = None
    """Splash."""
    
    discovery_splash: Optional[str] = None
    """Discovery splash."""
    
    owner: bool = False
    """Owner."""
    
    permissions: Optional[str] = None
    """Permissions."""
    
    region: Optional[str] = None
    """Region."""
    
    afk_channel_id: Optional[str] = None
    """AFK channel ID."""
    
    afk_timeout: int = 300
    """AFK timeout."""
    
    widget_enabled: bool = False
    """Widget enabled."""
    
    widget_channel_id: Optional[str] = None
    """Widget channel ID."""
    
    verification_level: int = 0
    """Verification level."""
    
    default_message_notifications: int = 0
    """Default message notifications."""
    
    explicit_content_filter: int = 0
    """Explicit content filter."""
    
    roles: List[Dict[str, Any]] = field(default_factory=list)
    """Roles."""
    
    emojis: List[Dict[str, Any]] = field(default_factory=list)
    """Emojis."""
    
    features: List[str] = field(default_factory=list)
    """Features."""
    
    mfa_level: int = 0
    """MFA level."""
    
    application_id: Optional[str] = None
    """Application ID."""
    
    system_channel_id: Optional[str] = None
    """System channel ID."""
    
    system_channel_flags: int = 0
    """System channel flags."""
    
    rules_channel_id: Optional[str] = None
    """Rules channel ID."""
    
    max_presences: Optional[int] = None
    """Max presences."""
    
    max_members: Optional[int] = None
    """Max members."""
    
    vanity_url_code: Optional[str] = None
    """Vanity URL code."""
    
    description: Optional[str] = None
    """Description."""
    
    banner: Optional[str] = None
    """Banner."""
    
    premium_tier: int = 0
    """Premium tier."""
    
    premium_subscription_count: Optional[int] = None
    """Premium subscription count."""
    
    preferred_locale: str = "en-US"
    """Preferred locale."""
    
    public_updates_channel_id: Optional[str] = None
    """Public updates channel ID."""
    
    max_video_channel_users: Optional[int] = None
    """Max video channel users."""
    
    max_stage_video_channel_users: Optional[int] = None
    """Max stage video channel users."""
    
    approximate_member_count: Optional[int] = None
    """Approximate member count."""
    
    approximate_presence_count: Optional[int] = None
    """Approximate presence count."""
    
    welcome_screen: Optional[Dict[str, Any]] = None
    """Welcome screen."""
    
    nsfw_level: int = 0
    """NSFW level."""
    
    stickers: List[Dict[str, Any]] = field(default_factory=list)
    """Stickers."""
    
    premium_progress_bar_enabled: bool = False
    """Premium progress bar enabled."""


class DiscordIntegration:
    """Discord integration for messaging and bot management."""
    
    def __init__(self, config: DiscordConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bot {config.bot_token}",
            "Content-Type": "application/json"
        })
        self.session.timeout = config.timeout
    
    async def get_current_user(self) -> Dict[str, Any]:
        """
        Get current bot user information.
        
        Returns:
            Bot user information
        """
        try:
            url = f"{self.config.api_base_url}/users/@me"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to get current user: {e}")
            raise
    
    async def send_message(
        self,
        channel_id: str,
        content: str,
        tts: bool = False,
        embeds: Optional[List[Dict[str, Any]]] = None,
        allowed_mentions: Optional[Dict[str, Any]] = None,
        message_reference: Optional[Dict[str, Any]] = None,
        components: Optional[List[Dict[str, Any]]] = None,
        sticker_ids: Optional[List[str]] = None,
        files: Optional[List[Dict[str, Any]]] = None,
        payload_json: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        flags: Optional[int] = None
    ) -> DiscordMessage:
        """
        Send a message to a channel.
        
        Args:
            channel_id: Channel ID
            content: Message content
            tts: Text-to-speech
            embeds: Message embeds
            allowed_mentions: Allowed mentions
            message_reference: Message reference
            components: Message components
            sticker_ids: Sticker IDs
            files: Files to upload
            payload_json: Payload JSON
            attachments: Attachments
            flags: Message flags
            
        Returns:
            Sent message
        """
        try:
            url = f"{self.config.api_base_url}/channels/{channel_id}/messages"
            
            payload = {
                "content": content,
                "tts": tts
            }
            
            if embeds:
                payload["embeds"] = embeds
            if allowed_mentions:
                payload["allowed_mentions"] = allowed_mentions
            if message_reference:
                payload["message_reference"] = message_reference
            if components:
                payload["components"] = components
            if sticker_ids:
                payload["sticker_ids"] = sticker_ids
            if attachments:
                payload["attachments"] = attachments
            if flags:
                payload["flags"] = flags
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            message_data = response.json()
            return self._parse_message(message_data)
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            raise
    
    async def edit_message(
        self,
        channel_id: str,
        message_id: str,
        content: Optional[str] = None,
        embeds: Optional[List[Dict[str, Any]]] = None,
        allowed_mentions: Optional[Dict[str, Any]] = None,
        components: Optional[List[Dict[str, Any]]] = None,
        files: Optional[List[Dict[str, Any]]] = None,
        payload_json: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        flags: Optional[int] = None
    ) -> DiscordMessage:
        """
        Edit a message.
        
        Args:
            channel_id: Channel ID
            message_id: Message ID
            content: New content
            embeds: New embeds
            allowed_mentions: Allowed mentions
            components: New components
            files: Files to upload
            payload_json: Payload JSON
            attachments: New attachments
            flags: Message flags
            
        Returns:
            Edited message
        """
        try:
            url = f"{self.config.api_base_url}/channels/{channel_id}/messages/{message_id}"
            
            payload = {}
            
            if content is not None:
                payload["content"] = content
            if embeds is not None:
                payload["embeds"] = embeds
            if allowed_mentions:
                payload["allowed_mentions"] = allowed_mentions
            if components is not None:
                payload["components"] = components
            if attachments is not None:
                payload["attachments"] = attachments
            if flags is not None:
                payload["flags"] = flags
            
            response = self.session.patch(url, json=payload)
            response.raise_for_status()
            
            message_data = response.json()
            return self._parse_message(message_data)
            
        except Exception as e:
            self.logger.error(f"Failed to edit message: {e}")
            raise
    
    async def delete_message(self, channel_id: str, message_id: str) -> bool:
        """
        Delete a message.
        
        Args:
            channel_id: Channel ID
            message_id: Message ID
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.config.api_base_url}/channels/{channel_id}/messages/{message_id}"
            response = self.session.delete(url)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete message: {e}")
            raise
    
    async def get_channel(self, channel_id: str) -> DiscordChannel:
        """
        Get channel information.
        
        Args:
            channel_id: Channel ID
            
        Returns:
            Channel information
        """
        try:
            url = f"{self.config.api_base_url}/channels/{channel_id}"
            response = self.session.get(url)
            response.raise_for_status()
            
            channel_data = response.json()
            return self._parse_channel(channel_data)
            
        except Exception as e:
            self.logger.error(f"Failed to get channel: {e}")
            raise
    
    async def get_guild(self, guild_id: str) -> DiscordGuild:
        """
        Get guild information.
        
        Args:
            guild_id: Guild ID
            
        Returns:
            Guild information
        """
        try:
            url = f"{self.config.api_base_url}/guilds/{guild_id}"
            response = self.session.get(url)
            response.raise_for_status()
            
            guild_data = response.json()
            return self._parse_guild(guild_data)
            
        except Exception as e:
            self.logger.error(f"Failed to get guild: {e}")
            raise
    
    async def get_guild_channels(self, guild_id: str) -> List[DiscordChannel]:
        """
        Get guild channels.
        
        Args:
            guild_id: Guild ID
            
        Returns:
            List of channels
        """
        try:
            url = f"{self.config.api_base_url}/guilds/{guild_id}/channels"
            response = self.session.get(url)
            response.raise_for_status()
            
            channels_data = response.json()
            channels = []
            for channel_data in channels_data:
                channel = self._parse_channel(channel_data)
                channels.append(channel)
            return channels
            
        except Exception as e:
            self.logger.error(f"Failed to get guild channels: {e}")
            raise
    
    async def create_channel(
        self,
        guild_id: str,
        name: str,
        type: DiscordChannelType = DiscordChannelType.GUILD_TEXT,
        topic: Optional[str] = None,
        bitrate: Optional[int] = None,
        user_limit: Optional[int] = None,
        rate_limit_per_user: Optional[int] = None,
        position: Optional[int] = None,
        permission_overwrites: Optional[List[Dict[str, Any]]] = None,
        parent_id: Optional[str] = None,
        nsfw: bool = False,
        reason: Optional[str] = None
    ) -> DiscordChannel:
        """
        Create a channel.
        
        Args:
            guild_id: Guild ID
            name: Channel name
            type: Channel type
            topic: Channel topic
            bitrate: Bitrate (voice channels)
            user_limit: User limit (voice channels)
            rate_limit_per_user: Rate limit per user
            position: Position
            permission_overwrites: Permission overwrites
            parent_id: Parent ID
            nsfw: NSFW channel
            reason: Audit log reason
            
        Returns:
            Created channel
        """
        try:
            url = f"{self.config.api_base_url}/guilds/{guild_id}/channels"
            
            payload = {
                "name": name,
                "type": type.value
            }
            
            if topic:
                payload["topic"] = topic
            if bitrate:
                payload["bitrate"] = bitrate
            if user_limit:
                payload["user_limit"] = user_limit
            if rate_limit_per_user:
                payload["rate_limit_per_user"] = rate_limit_per_user
            if position:
                payload["position"] = position
            if permission_overwrites:
                payload["permission_overwrites"] = permission_overwrites
            if parent_id:
                payload["parent_id"] = parent_id
            if nsfw:
                payload["nsfw"] = nsfw
            
            headers = {}
            if reason:
                headers["X-Audit-Log-Reason"] = reason
            
            response = self.session.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            channel_data = response.json()
            return self._parse_channel(channel_data)
            
        except Exception as e:
            self.logger.error(f"Failed to create channel: {e}")
            raise
    
    async def delete_channel(self, channel_id: str, reason: Optional[str] = None) -> bool:
        """
        Delete a channel.
        
        Args:
            channel_id: Channel ID
            reason: Audit log reason
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.config.api_base_url}/channels/{channel_id}"
            
            headers = {}
            if reason:
                headers["X-Audit-Log-Reason"] = reason
            
            response = self.session.delete(url, headers=headers)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete channel: {e}")
            raise
    
    async def get_guild_members(
        self,
        guild_id: str,
        limit: int = 1,
        after: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get guild members.
        
        Args:
            guild_id: Guild ID
            limit: Number of members to return
            after: Get members after this user ID
            
        Returns:
            List of members
        """
        try:
            url = f"{self.config.api_base_url}/guilds/{guild_id}/members"
            
            params = {"limit": limit}
            if after:
                params["after"] = after
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to get guild members: {e}")
            raise
    
    async def create_slash_command(
        self,
        name: str,
        description: str,
        options: Optional[List[Dict[str, Any]]] = None,
        default_member_permissions: Optional[str] = None,
        dm_permission: bool = True,
        type: int = 1
    ) -> Dict[str, Any]:
        """
        Create a slash command.
        
        Args:
            name: Command name
            description: Command description
            options: Command options
            default_member_permissions: Default member permissions
            dm_permission: DM permission
            type: Command type
            
        Returns:
            Created command
        """
        try:
            if not self.config.application_id:
                raise ValueError("Application ID is required for slash commands")
            
            url = f"{self.config.api_base_url}/applications/{self.config.application_id}/commands"
            
            payload = {
                "name": name,
                "description": description,
                "type": type,
                "dm_permission": dm_permission
            }
            
            if options:
                payload["options"] = options
            if default_member_permissions:
                payload["default_member_permissions"] = default_member_permissions
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to create slash command: {e}")
            raise
    
    async def get_slash_commands(self) -> List[Dict[str, Any]]:
        """
        Get slash commands.
        
        Returns:
            List of commands
        """
        try:
            if not self.config.application_id:
                raise ValueError("Application ID is required for slash commands")
            
            url = f"{self.config.api_base_url}/applications/{self.config.application_id}/commands"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to get slash commands: {e}")
            raise
    
    def _parse_message(self, message_data: Dict[str, Any]) -> DiscordMessage:
        """Parse message data into DiscordMessage object."""
        message = DiscordMessage(
            id=message_data["id"],
            channel_id=message_data["channel_id"],
            guild_id=message_data.get("guild_id"),
            author=message_data["author"],
            content=message_data["content"],
            timestamp=datetime.fromisoformat(message_data["timestamp"].replace("Z", "+00:00")),
            tts=message_data.get("tts", False),
            mention_everyone=message_data.get("mention_everyone", False),
            mentions=message_data.get("mentions", []),
            mention_roles=message_data.get("mention_roles", []),
            mention_channels=message_data.get("mention_channels", []),
            attachments=message_data.get("attachments", []),
            embeds=message_data.get("embeds", []),
            reactions=message_data.get("reactions", []),
            pinned=message_data.get("pinned", False),
            webhook_id=message_data.get("webhook_id"),
            type=DiscordMessageType(message_data.get("type", 0)),
            components=message_data.get("components", []),
            sticker_items=message_data.get("sticker_items", [])
        )
        
        if "edited_timestamp" in message_data and message_data["edited_timestamp"]:
            message.edited_timestamp = datetime.fromisoformat(message_data["edited_timestamp"].replace("Z", "+00:00"))
        
        if "nonce" in message_data:
            message.nonce = message_data["nonce"]
        if "activity" in message_data:
            message.activity = message_data["activity"]
        if "application" in message_data:
            message.application = message_data["application"]
        if "application_id" in message_data:
            message.application_id = message_data["application_id"]
        if "message_reference" in message_data:
            message.message_reference = message_data["message_reference"]
        if "flags" in message_data:
            message.flags = message_data["flags"]
        if "referenced_message" in message_data:
            message.referenced_message = message_data["referenced_message"]
        if "interaction" in message_data:
            message.interaction = message_data["interaction"]
        if "thread" in message_data:
            message.thread = message_data["thread"]
        if "position" in message_data:
            message.position = message_data["position"]
        
        return message
    
    def _parse_channel(self, channel_data: Dict[str, Any]) -> DiscordChannel:
        """Parse channel data into DiscordChannel object."""
        channel = DiscordChannel(
            id=channel_data["id"],
            type=DiscordChannelType(channel_data["type"]),
            guild_id=channel_data.get("guild_id"),
            position=channel_data.get("position"),
            permission_overwrites=channel_data.get("permission_overwrites", []),
            name=channel_data.get("name"),
            topic=channel_data.get("topic"),
            nsfw=channel_data.get("nsfw", False),
            last_message_id=channel_data.get("last_message_id"),
            bitrate=channel_data.get("bitrate"),
            user_limit=channel_data.get("user_limit"),
            rate_limit_per_user=channel_data.get("rate_limit_per_user"),
            recipients=channel_data.get("recipients", []),
            icon=channel_data.get("icon"),
            owner_id=channel_data.get("owner_id"),
            application_id=channel_data.get("application_id"),
            managed=channel_data.get("managed", False),
            parent_id=channel_data.get("parent_id"),
            rtc_region=channel_data.get("rtc_region"),
            video_quality_mode=channel_data.get("video_quality_mode"),
            message_count=channel_data.get("message_count"),
            member_count=channel_data.get("member_count"),
            thread_metadata=channel_data.get("thread_metadata"),
            member=channel_data.get("member"),
            default_auto_archive_duration=channel_data.get("default_auto_archive_duration"),
            permissions=channel_data.get("permissions"),
            flags=channel_data.get("flags"),
            total_message_sent=channel_data.get("total_message_sent"),
            available_tags=channel_data.get("available_tags", []),
            applied_tags=channel_data.get("applied_tags", []),
            default_reaction_emoji=channel_data.get("default_reaction_emoji"),
            default_thread_rate_limit_per_user=channel_data.get("default_thread_rate_limit_per_user"),
            default_sort_order=channel_data.get("default_sort_order"),
            default_forum_layout=channel_data.get("default_forum_layout")
        )
        
        if "last_pin_timestamp" in channel_data and channel_data["last_pin_timestamp"]:
            channel.last_pin_timestamp = datetime.fromisoformat(channel_data["last_pin_timestamp"].replace("Z", "+00:00"))
        
        return channel
    
    def _parse_guild(self, guild_data: Dict[str, Any]) -> DiscordGuild:
        """Parse guild data into DiscordGuild object."""
        guild = DiscordGuild(
            id=guild_data["id"],
            name=guild_data["name"],
            icon=guild_data.get("icon"),
            icon_hash=guild_data.get("icon_hash"),
            splash=guild_data.get("splash"),
            discovery_splash=guild_data.get("discovery_splash"),
            owner=guild_data.get("owner", False),
            owner_id=guild_data["owner_id"],
            permissions=guild_data.get("permissions"),
            region=guild_data.get("region"),
            afk_channel_id=guild_data.get("afk_channel_id"),
            afk_timeout=guild_data.get("afk_timeout", 300),
            widget_enabled=guild_data.get("widget_enabled", False),
            widget_channel_id=guild_data.get("widget_channel_id"),
            verification_level=guild_data.get("verification_level", 0),
            default_message_notifications=guild_data.get("default_message_notifications", 0),
            explicit_content_filter=guild_data.get("explicit_content_filter", 0),
            roles=guild_data.get("roles", []),
            emojis=guild_data.get("emojis", []),
            features=guild_data.get("features", []),
            mfa_level=guild_data.get("mfa_level", 0),
            application_id=guild_data.get("application_id"),
            system_channel_id=guild_data.get("system_channel_id"),
            system_channel_flags=guild_data.get("system_channel_flags", 0),
            rules_channel_id=guild_data.get("rules_channel_id"),
            max_presences=guild_data.get("max_presences"),
            max_members=guild_data.get("max_members"),
            vanity_url_code=guild_data.get("vanity_url_code"),
            description=guild_data.get("description"),
            banner=guild_data.get("banner"),
            premium_tier=guild_data.get("premium_tier", 0),
            premium_subscription_count=guild_data.get("premium_subscription_count"),
            preferred_locale=guild_data.get("preferred_locale", "en-US"),
            public_updates_channel_id=guild_data.get("public_updates_channel_id"),
            max_video_channel_users=guild_data.get("max_video_channel_users"),
            max_stage_video_channel_users=guild_data.get("max_stage_video_channel_users"),
            approximate_member_count=guild_data.get("approximate_member_count"),
            approximate_presence_count=guild_data.get("approximate_presence_count"),
            welcome_screen=guild_data.get("welcome_screen"),
            nsfw_level=guild_data.get("nsfw_level", 0),
            stickers=guild_data.get("stickers", []),
            premium_progress_bar_enabled=guild_data.get("premium_progress_bar_enabled", False)
        )
        
        return guild
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Discord integration.
        
        Returns:
            Health check results
        """
        try:
            # Test bot info
            bot_info = await self.get_current_user()
            
            return {
                "status": "healthy",
                "bot_username": bot_info.get("username"),
                "bot_id": bot_info.get("id"),
                "bot_discriminator": bot_info.get("discriminator"),
                "bot_verified": bot_info.get("verified", False),
                "last_checked": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }

