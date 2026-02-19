"""
Redis-based Session Manager for persistent conversation sessions
Ensures sessions survive server restarts
"""

import json
import redis
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import os
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class SessionData:
    """Session data structure"""
    session_id: str
    user_id: str
    domain: str
    created_at: str
    last_activity: str
    messages: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    tts_provider: str = "akan"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionData':
        """Create from dictionary"""
        return cls(**data)


class RedisSessionManager:
    """Manages conversation sessions in Redis for persistence"""
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize Redis session manager
        
        Args:
            redis_url: Redis connection URL (defaults to env var)
        """
        # Get Redis URL from environment or use default
        if not redis_url:
            redis_url = os.getenv('REDIS_URL', 'redis://inspireadmin:aawwER444444@localhost:6379/0')
        
        # Parse Redis URL and connect
        try:
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"✅ Connected to Redis for session management: {redis_url}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            logger.warning("⚠️ Falling back to in-memory session storage")
            self.redis_client = None
            self.memory_sessions = {}
        
        # Session configuration
        self.session_prefix = "kasaai:session:"
        self.session_ttl = 3600 * 24  # 24 hours
        
    def create_session(
        self,
        session_id: str,
        user_id: str,
        domain: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
        tts_provider: str = "akan"
    ) -> bool:
        """
        Create a new session in Redis
        
        Args:
            session_id: Unique session ID
            user_id: User ID
            domain: Conversation domain
            metadata: Additional metadata
            tts_provider: TTS provider to use
            
        Returns:
            True if created successfully
        """
        try:
            session_data = SessionData(
                session_id=session_id,
                user_id=user_id,
                domain=domain,
                created_at=datetime.now().isoformat(),
                last_activity=datetime.now().isoformat(),
                messages=[],
                metadata=metadata or {
                    "language": "tw",
                    "dialect": "asante",
                    "total_turns": 0,
                    "total_duration": 0.0
                },
                tts_provider=tts_provider
            )
            
            if self.redis_client:
                # Store in Redis with TTL
                key = f"{self.session_prefix}{session_id}"
                self.redis_client.setex(
                    key,
                    self.session_ttl,
                    json.dumps(session_data.to_dict())
                )
                logger.info(f"📝 Created Redis session: {session_id}")
            else:
                # Fallback to memory
                self.memory_sessions[session_id] = session_data.to_dict()
                logger.info(f"📝 Created in-memory session: {session_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create session {session_id}: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session from Redis
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if not found
        """
        try:
            if self.redis_client:
                key = f"{self.session_prefix}{session_id}"
                data = self.redis_client.get(key)
                if data:
                    # Extend TTL on access
                    self.redis_client.expire(key, self.session_ttl)
                    return json.loads(data)
            else:
                # Fallback to memory
                return self.memory_sessions.get(session_id)
                
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            
        return None
    
    def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update session in Redis
        
        Args:
            session_id: Session ID
            updates: Fields to update
            
        Returns:
            True if updated successfully
        """
        try:
            session = self.get_session(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found")
                return False
            
            # Update fields
            session.update(updates)
            session['last_activity'] = datetime.now().isoformat()
            
            if self.redis_client:
                key = f"{self.session_prefix}{session_id}"
                self.redis_client.setex(
                    key,
                    self.session_ttl,
                    json.dumps(session)
                )
            else:
                self.memory_sessions[session_id] = session
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return False
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        **kwargs
    ) -> bool:
        """
        Add message to session
        
        Args:
            session_id: Session ID
            role: Message role (user/assistant/system)
            content: Message content
            **kwargs: Additional message data
            
        Returns:
            True if added successfully
        """
        try:
            session = self.get_session(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found")
                return False
            
            # Create message
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                **kwargs
            }
            
            # Add to messages
            session['messages'].append(message)
            
            # Update turn count if user message
            if role == "user":
                if 'metadata' not in session:
                    session['metadata'] = {}
                if 'total_turns' not in session['metadata']:
                    session['metadata']['total_turns'] = 0
                session['metadata']['total_turns'] += 1
            
            # Save updated session
            return self.update_session(session_id, session)
            
        except Exception as e:
            logger.error(f"Failed to add message to session {session_id}: {e}")
            return False
    
    def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get messages from session
        
        Args:
            session_id: Session ID
            limit: Max number of messages to return (from end)
            
        Returns:
            List of messages
        """
        try:
            session = self.get_session(session_id)
            if session:
                messages = session.get('messages', [])
                if limit:
                    return messages[-limit:]
                return messages
                
        except Exception as e:
            logger.error(f"Failed to get messages for session {session_id}: {e}")
            
        return []
    
    def update_tts_provider(
        self,
        session_id: str,
        tts_provider: str
    ) -> bool:
        """
        Update TTS provider for session
        
        Args:
            session_id: Session ID
            tts_provider: New TTS provider
            
        Returns:
            True if updated successfully
        """
        return self.update_session(session_id, {"tts_provider": tts_provider})
    
    def get_tts_provider(self, session_id: str) -> str:
        """
        Get TTS provider for session
        
        Args:
            session_id: Session ID
            
        Returns:
            TTS provider or default
        """
        session = self.get_session(session_id)
        if session:
            return session.get('tts_provider', 'akan')
        return 'akan'
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete session from Redis
        
        Args:
            session_id: Session ID
            
        Returns:
            True if deleted successfully
        """
        try:
            if self.redis_client:
                key = f"{self.session_prefix}{session_id}"
                self.redis_client.delete(key)
            else:
                self.memory_sessions.pop(session_id, None)
                
            logger.info(f"🗑️ Deleted session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def list_sessions(self, user_id: Optional[str] = None) -> List[str]:
        """
        List all sessions or sessions for a user
        
        Args:
            user_id: Optional user ID to filter by
            
        Returns:
            List of session IDs
        """
        try:
            if self.redis_client:
                pattern = f"{self.session_prefix}*"
                keys = self.redis_client.keys(pattern)
                session_ids = [key.replace(self.session_prefix, '') for key in keys]
                
                # Filter by user if specified
                if user_id:
                    filtered = []
                    for sid in session_ids:
                        session = self.get_session(sid)
                        if session and session.get('user_id') == user_id:
                            filtered.append(sid)
                    return filtered
                    
                return session_ids
            else:
                # Memory fallback
                if user_id:
                    return [
                        sid for sid, session in self.memory_sessions.items()
                        if session.get('user_id') == user_id
                    ]
                return list(self.memory_sessions.keys())
                
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions (called periodically)
        
        Returns:
            Number of sessions cleaned
        """
        try:
            if not self.redis_client:
                # Manual cleanup for memory storage
                now = datetime.now()
                expired = []
                for sid, session in self.memory_sessions.items():
                    last_activity = datetime.fromisoformat(session['last_activity'])
                    if (now - last_activity).total_seconds() > self.session_ttl:
                        expired.append(sid)
                
                for sid in expired:
                    del self.memory_sessions[sid]
                    
                if expired:
                    logger.info(f"🧹 Cleaned up {len(expired)} expired sessions")
                return len(expired)
            
            # Redis handles TTL automatically
            return 0
            
        except Exception as e:
            logger.error(f"Failed to cleanup sessions: {e}")
            return 0


# Singleton instance
_redis_session_manager = None


def get_redis_session_manager() -> RedisSessionManager:
    """Get or create Redis session manager instance"""
    global _redis_session_manager
    
    if _redis_session_manager is None:
        _redis_session_manager = RedisSessionManager()
    
    return _redis_session_manager