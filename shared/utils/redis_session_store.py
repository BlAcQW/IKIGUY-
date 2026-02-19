#!/usr/bin/env python3
"""
Redis Session Store for WebRTC Connections
Manages connection limits, session persistence, and cleanup.
"""

import logging
import redis.asyncio as redis
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# Connection limits
PER_USER_LIMIT = 2  # Max concurrent connections per user
GLOBAL_LIMIT = 100  # Max total concurrent connections
SESSION_TTL = 3600  # 1 hour session timeout
RATE_LIMIT_WINDOW = 60  # 1 minute
RATE_LIMIT_MAX = 5  # Max 5 connection attempts per minute


class RedisSessionStore:
    """
    Manages WebRTC session state in Redis.

    Handles:
    - Connection counting and limits
    - Session metadata persistence
    - Automatic cleanup of stale sessions
    - Rate limiting
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize Redis session store.

        Args:
            redis_url: Redis connection URL (defaults to env var)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client: Optional[redis.Redis] = None
        logger.info(f"🔴 Redis session store initialized (URL: {self.redis_url})")

    async def connect(self):
        """Connect to Redis."""
        if not self.redis_client:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("✅ Connected to Redis")

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            logger.info("🔌 Disconnected from Redis")

    async def can_create_connection(self, user_id: str) -> Tuple[bool, str]:
        """
        Check if user can create a new WebRTC connection.

        Validates:
        1. Per-user connection limit
        2. Global connection limit
        3. Rate limiting

        Args:
            user_id: User identifier

        Returns:
            (allowed, error_message) - allowed=True if can connect
        """
        await self.connect()

        # Check rate limiting first
        rate_key = f"webrtc:ratelimit:{user_id}"
        rate_count = await self.redis_client.incr(rate_key)

        if rate_count == 1:
            # First attempt in this window - set TTL
            await self.redis_client.expire(rate_key, RATE_LIMIT_WINDOW)

        if rate_count > RATE_LIMIT_MAX:
            logger.warning(f"⚠️ Rate limit exceeded for user {user_id}: {rate_count}/{RATE_LIMIT_MAX}")
            return False, f"Too many connection attempts. Please wait {RATE_LIMIT_WINDOW} seconds."

        # Check per-user limit
        user_key = f"webrtc:user:{user_id}:connections"
        user_count = await self.redis_client.scard(user_key)

        if user_count >= PER_USER_LIMIT:
            logger.warning(f"⚠️ Per-user limit reached for {user_id}: {user_count}/{PER_USER_LIMIT}")
            return False, f"Maximum concurrent connections reached ({PER_USER_LIMIT}). Close other tabs."

        # Check global limit
        global_key = "webrtc:global:connections"
        global_count = await self.redis_client.scard(global_key)

        if global_count >= GLOBAL_LIMIT:
            logger.warning(f"⚠️ Global limit reached: {global_count}/{GLOBAL_LIMIT}")
            return False, "Server at capacity. Please try again later."

        logger.info(f"✅ Connection allowed for {user_id} (user: {user_count}/{PER_USER_LIMIT}, global: {global_count}/{GLOBAL_LIMIT})")
        return True, ""

    async def register_connection(
        self,
        session_id: str,
        user_id: str,
        assistant_id: str,
        metadata: Optional[Dict] = None
    ):
        """
        Register a new WebRTC connection.

        Args:
            session_id: Unique session identifier
            user_id: User identifier
            assistant_id: Assistant being used
            metadata: Additional session metadata
        """
        await self.connect()

        # Add to user's connection set
        user_key = f"webrtc:user:{user_id}:connections"
        await self.redis_client.sadd(user_key, session_id)

        # Add to global connection set
        global_key = "webrtc:global:connections"
        await self.redis_client.sadd(global_key, session_id)

        # Store session metadata with TTL
        session_data = {
            "user_id": user_id,
            "assistant_id": assistant_id,
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat()
        }

        if metadata:
            session_data.update(metadata)

        session_key = f"webrtc:session:{session_id}"
        await self.redis_client.hset(session_key, mapping=session_data)
        await self.redis_client.expire(session_key, SESSION_TTL)

        logger.info(f"📝 Registered connection: {session_id} (user: {user_id}, assistant: {assistant_id})")

    async def update_last_active(self, session_id: str):
        """
        Update session's last active timestamp.

        Args:
            session_id: Session identifier
        """
        await self.connect()

        session_key = f"webrtc:session:{session_id}"
        await self.redis_client.hset(
            session_key,
            "last_active",
            datetime.now().isoformat()
        )
        # Refresh TTL
        await self.redis_client.expire(session_key, SESSION_TTL)

    async def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session metadata.

        Args:
            session_id: Session identifier

        Returns:
            Session data dictionary or None if not found
        """
        await self.connect()

        session_key = f"webrtc:session:{session_id}"
        session_data = await self.redis_client.hgetall(session_key)

        return dict(session_data) if session_data else None

    async def cleanup_connection(self, session_id: str):
        """
        Cleanup WebRTC connection from Redis.

        Args:
            session_id: Session identifier
        """
        await self.connect()

        # Get session data to find user_id
        session_key = f"webrtc:session:{session_id}"
        session_data = await self.redis_client.hgetall(session_key)

        if not session_data:
            logger.warning(f"⚠️ Session not found for cleanup: {session_id}")
            return

        user_id = session_data.get("user_id")

        # Remove from user's connection set
        if user_id:
            user_key = f"webrtc:user:{user_id}:connections"
            await self.redis_client.srem(user_key, session_id)

        # Remove from global connection set
        global_key = "webrtc:global:connections"
        await self.redis_client.srem(global_key, session_id)

        # Delete session data
        await self.redis_client.delete(session_key)

        logger.info(f"🗑️ Cleaned up connection: {session_id} (user: {user_id})")

    async def get_user_connections(self, user_id: str) -> List[str]:
        """
        Get all active connection session IDs for a user.

        Args:
            user_id: User identifier

        Returns:
            List of session IDs
        """
        await self.connect()

        user_key = f"webrtc:user:{user_id}:connections"
        sessions = await self.redis_client.smembers(user_key)

        return list(sessions) if sessions else []

    async def get_global_stats(self) -> Dict:
        """
        Get global connection statistics.

        Returns:
            Dictionary with connection stats
        """
        await self.connect()

        global_key = "webrtc:global:connections"
        global_count = await self.redis_client.scard(global_key)

        return {
            "total_connections": global_count,
            "limit": GLOBAL_LIMIT,
            "utilization": f"{(global_count / GLOBAL_LIMIT * 100):.1f}%",
            "available": GLOBAL_LIMIT - global_count
        }

    async def cleanup_stale_sessions(self):
        """
        Cleanup stale sessions that have expired.

        This is a maintenance task that should run periodically.
        Redis TTL handles most cleanup, but this ensures consistency.
        """
        await self.connect()

        global_key = "webrtc:global:connections"
        all_sessions = await self.redis_client.smembers(global_key)

        cleaned = 0
        for session_id in all_sessions:
            session_key = f"webrtc:session:{session_id}"
            exists = await self.redis_client.exists(session_key)

            if not exists:
                # Session expired but still in global set - cleanup
                await self.cleanup_connection(session_id)
                cleaned += 1

        if cleaned > 0:
            logger.info(f"🧹 Cleaned up {cleaned} stale sessions")

        return cleaned


# Global instance
session_store = RedisSessionStore()


# Export
__all__ = ['RedisSessionStore', 'session_store', 'PER_USER_LIMIT', 'GLOBAL_LIMIT']
