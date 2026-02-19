"""
Conversation Manager for Voice Lab
Manages conversation context, history, and orchestrates ASR-LLM-TTS pipeline
"""

import uuid
import asyncio
import logging
from typing import Optional, Dict, List, Any, AsyncGenerator
from datetime import datetime, timedelta
from collections import deque
import json

from .twi_whisper_service import get_twi_whisper_service
from .twi_llm_service import get_llm_service, LLMProvider
from .redis_session_manager import get_redis_session_manager
from .audio_converter import AudioConverter

logger = logging.getLogger(__name__)


class ConversationSession:
    """Represents a single conversation session"""
    
    def __init__(self, session_id: str, user_id: str, domain: str = "general"):
        self.session_id = session_id
        self.user_id = user_id
        self.domain = domain
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
        # Conversation history
        self.messages: List[Dict[str, Any]] = []
        
        # Context window (last N messages for LLM context)
        self.context_window = 10
        
        # Session metadata
        self.metadata = {
            "language": "tw",
            "dialect": "asante",
            "total_turns": 0,
            "total_duration": 0.0
        }
        
    def add_message(self, role: str, content: str, **kwargs):
        """Add message to conversation history"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        self.messages.append(message)
        self.last_activity = datetime.now()
        
        if role == "user":
            self.metadata["total_turns"] += 1
            
    def get_context(self) -> List[Dict[str, str]]:
        """Get recent messages for LLM context"""
        recent_messages = self.messages[-self.context_window:]
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in recent_messages
            if msg["role"] in ["user", "assistant"]
        ]
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "domain": self.domain,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "messages": self.messages,
            "metadata": self.metadata
        }


class ConversationManager:
    """Manages conversation sessions and orchestrates voice AI pipeline"""
    
    def __init__(self):
        """Initialize conversation manager"""
        # Services - Use Akan Whisper model (92.9% accuracy)
        self.whisper_service = get_twi_whisper_service(model_name="akan")
        # Use GOOGLE provider for Gemini
        self.llm_service = get_llm_service(LLMProvider.GOOGLE)
        
        # Redis session manager for persistent storage
        self.redis_manager = get_redis_session_manager()
        
        # Local cache for active sessions
        self.sessions: Dict[str, ConversationSession] = {}
        
        # Session timeout (30 minutes)
        self.session_timeout = timedelta(minutes=30)
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_sessions())
        
    async def create_session(
        self,
        user_id: str,
        domain: str = "general",
        metadata: Optional[Dict] = None,
        tts_provider: str = "akan"
    ) -> str:
        """
        Create new conversation session
        
        Args:
            user_id: User ID
            domain: Conversation domain
            metadata: Additional metadata
            tts_provider: TTS provider to use
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        # Create session in Redis for persistence
        self.redis_manager.create_session(
            session_id=session_id,
            user_id=user_id,
            domain=domain,
            metadata=metadata,
            tts_provider=tts_provider
        )
        
        # Also create local session for fast access
        session = ConversationSession(session_id, user_id, domain)
        if metadata:
            session.metadata.update(metadata)
        
        self.sessions[session_id] = session
        
        # Add welcome message
        welcome_message = await self._get_welcome_message(domain)
        session.add_message("assistant", welcome_message)
        
        # Save welcome message to Redis
        self.redis_manager.add_message(
            session_id,
            "assistant",
            welcome_message
        )
        
        logger.info(f"Created session {session_id} for user {user_id} with TTS: {tts_provider}")
        return session_id
        
    async def _get_welcome_message(self, domain: str) -> str:
        """Get domain-specific welcome message"""
        messages = {
            "general": "Akwaaba! Me yɛ AI assistant. Mete Twi ne English. Dɛn na metumi aboa wo?",
            "healthcare": "Akwaaba! Me yɛ apɔmuden ho AI assistant. Metumi aboa wo wɔ wo apɔmuden ho nsɛm mu. Ɛte sɛn?",
            "education": "Akwaaba! Me yɛ adesua AI assistant. Metumi akyerɛkyerɛ wo adeɛ pii. Dɛn na wobɛpɛ sɛ yɛsua nnɛ?",
            "finance": "Akwaaba! Me yɛ sika ho AI assistant. Metumi aboa wo wɔ wo sika ho nsɛm mu. Dɛn na wobɛpɛ sɛ yɛkasa fa ho?"
        }
        return messages.get(domain, messages["general"])
        
    async def process_voice_message(
        self,
        session_id: str,
        audio_data: bytes,
        sample_rate: int = 16000
    ) -> Dict[str, Any]:
        """
        Process voice message through ASR-LLM-TTS pipeline
        
        Args:
            session_id: Session ID
            audio_data: Audio bytes
            sample_rate: Audio sample rate
            
        Returns:
            Response with transcription and AI response
        """
        # Try local cache first
        session = self.sessions.get(session_id)
        
        # If not in local cache, try Redis
        if not session:
            redis_session = self.redis_manager.get_session(session_id)
            if redis_session:
                # Recreate local session from Redis data
                session = ConversationSession(
                    session_id,
                    redis_session['user_id'],
                    redis_session['domain']
                )
                session.messages = redis_session['messages']
                session.metadata = redis_session['metadata']
                self.sessions[session_id] = session
                logger.info(f"Restored session {session_id} from Redis")
            else:
                raise ValueError(f"Session {session_id} not found")
            
        # Step 1: Convert audio format and transcribe using Akan Whisper
        import numpy as np
        
        # Convert audio to PCM format
        try:
            audio_array, detected_sample_rate = AudioConverter.convert_to_pcm(audio_data)
            logger.info(f"✅ Audio converted to PCM: {len(audio_array)} samples at {detected_sample_rate}Hz")
            
            # Use detected sample rate if different from expected
            if detected_sample_rate != sample_rate:
                logger.info(f"Using detected sample rate: {detected_sample_rate}Hz instead of {sample_rate}Hz")
                sample_rate = detected_sample_rate
        except Exception as e:
            logger.error(f"Failed to convert audio: {e}")
            # Fallback to direct conversion
            if len(audio_data) % 2 != 0:
                logger.warning(f"Audio data has odd number of bytes ({len(audio_data)}), padding with zero")
                audio_data = audio_data + b'\x00'
            
            try:
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            except ValueError as e2:
                logger.error(f"Failed to convert audio buffer: {e2}")
                raise ValueError(f"Unable to process audio data: {e2}")
        
        # Use Akan Whisper's transcribe method
        transcription_result = self.whisper_service.transcribe(
            audio_array,
            sample_rate,
            language=session.metadata.get("language", "tw")
        )
        
        user_text = transcription_result["text"]
        
        # Add user message to session
        session.add_message(
            "user",
            user_text,
            transcription=transcription_result
        )
        
        # Save to Redis
        self.redis_manager.add_message(
            session_id,
            "user",
            user_text,
            transcription=transcription_result
        )
        
        # Step 2: Generate LLM response
        context = session.get_context()
        
        llm_response = await self.llm_service.generate_response(
            user_text,
            context=context,
            domain=session.domain
        )
        
        # Add assistant message to session
        session.add_message("assistant", llm_response)
        
        # Save to Redis
        self.redis_manager.add_message(
            session_id,
            "assistant",
            llm_response
        )
        
        return {
            "session_id": session_id,
            "transcription": user_text,
            "response": llm_response,
            "confidence": transcription_result["confidence"],
            "language": transcription_result["language"],
            "turn_number": session.metadata["total_turns"]
        }
        
    async def process_text_message(
        self,
        session_id: str,
        text: str
    ) -> Dict[str, Any]:
        """
        Process text message through LLM
        
        Args:
            session_id: Session ID
            text: User text
            
        Returns:
            AI response
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
            
        # Add user message
        session.add_message("user", text)
        
        # Generate response
        context = session.get_context()
        
        llm_response = await self.llm_service.generate_response(
            text,
            context=context,
            domain=session.domain
        )
        
        # Add assistant message
        session.add_message("assistant", llm_response)
        
        return {
            "session_id": session_id,
            "response": llm_response,
            "turn_number": session.metadata["total_turns"]
        }
        
    async def stream_voice_conversation(
        self,
        session_id: str,
        audio_stream: AsyncGenerator[bytes, None],
        sample_rate: int = 16000
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream voice conversation with real-time transcription and response
        
        Args:
            session_id: Session ID
            audio_stream: Async generator of audio chunks
            sample_rate: Audio sample rate
            
        Yields:
            Conversation updates
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
            
        # Stream transcription
        async for transcription in self.whisper_service.stream_transcribe(
            audio_stream,
            sample_rate
        ):
            # Yield partial transcription
            yield {
                "type": "partial_transcription",
                "text": transcription["text"],
                "is_final": transcription.get("is_final", False)
            }
            
            # If final transcription, generate response
            if transcription.get("is_final"):
                user_text = transcription["text"]
                
                # Add to session
                session.add_message("user", user_text, transcription=transcription)
                
                # Generate LLM response
                context = session.get_context()
                
                # Stream LLM response
                response_text = ""
                async for chunk in self.llm_service.stream_response(
                    user_text,
                    context=context,
                    domain=session.domain
                ):
                    response_text += chunk
                    yield {
                        "type": "response_chunk",
                        "text": chunk
                    }
                    
                # Add complete response to session
                session.add_message("assistant", response_text)
                
                # Yield final response
                yield {
                    "type": "response_complete",
                    "text": response_text,
                    "turn_number": session.metadata["total_turns"]
                }
                
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get session by ID"""
        return self.sessions.get(session_id)
        
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for session"""
        session = self.sessions.get(session_id)
        if not session:
            return []
        return session.messages
        
    def update_session_domain(self, session_id: str, domain: str):
        """Update session domain"""
        session = self.sessions.get(session_id)
        if session:
            session.domain = domain
            logger.info(f"Updated session {session_id} domain to {domain}")
            
    def clear_session_context(self, session_id: str):
        """Clear session context while keeping metadata"""
        session = self.sessions.get(session_id)
        if session:
            session.messages = []
            session.metadata["total_turns"] = 0
            logger.info(f"Cleared context for session {session_id}")
            
    def end_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """End and return session data"""
        session = self.sessions.pop(session_id, None)
        if session:
            logger.info(f"Ended session {session_id}")
            return session.to_dict()
        return None
        
    async def _cleanup_sessions(self):
        """Cleanup inactive sessions periodically"""
        while True:
            await asyncio.sleep(300)  # Check every 5 minutes
            
            now = datetime.now()
            expired_sessions = []
            
            for session_id, session in self.sessions.items():
                if now - session.last_activity > self.session_timeout:
                    expired_sessions.append(session_id)
                    
            for session_id in expired_sessions:
                self.end_session(session_id)
                logger.info(f"Cleaned up expired session {session_id}")
                
    def export_session(self, session_id: str, format: str = "json") -> str:
        """
        Export session data
        
        Args:
            session_id: Session ID
            format: Export format (json, text)
            
        Returns:
            Exported data
        """
        session = self.sessions.get(session_id)
        if not session:
            return ""
            
        if format == "json":
            return json.dumps(session.to_dict(), indent=2, ensure_ascii=False)
        elif format == "text":
            lines = []
            lines.append(f"Conversation Session: {session.session_id}")
            lines.append(f"Domain: {session.domain}")
            lines.append(f"Started: {session.created_at}")
            lines.append("-" * 50)
            
            for msg in session.messages:
                role = "User" if msg["role"] == "user" else "Assistant"
                lines.append(f"\n[{role}] {msg['timestamp']}")
                lines.append(msg["content"])
                
            return "\n".join(lines)
        else:
            return ""
            
    def get_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get session statistics"""
        session = self.sessions.get(session_id)
        if not session:
            return {}
            
        total_messages = len(session.messages)
        user_messages = sum(1 for m in session.messages if m["role"] == "user")
        assistant_messages = sum(1 for m in session.messages if m["role"] == "assistant")
        
        # Calculate average message length
        avg_user_length = 0
        avg_assistant_length = 0
        
        if user_messages > 0:
            avg_user_length = sum(
                len(m["content"]) for m in session.messages if m["role"] == "user"
            ) / user_messages
            
        if assistant_messages > 0:
            avg_assistant_length = sum(
                len(m["content"]) for m in session.messages if m["role"] == "assistant"
            ) / assistant_messages
            
        duration = (session.last_activity - session.created_at).total_seconds()
        
        return {
            "session_id": session_id,
            "domain": session.domain,
            "total_messages": total_messages,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "total_turns": session.metadata["total_turns"],
            "avg_user_message_length": avg_user_length,
            "avg_assistant_message_length": avg_assistant_length,
            "duration_seconds": duration,
            "language": session.metadata.get("language", "tw"),
            "dialect": session.metadata.get("dialect", "asante")
        }


# Singleton instance
_conversation_manager = None


def get_conversation_manager() -> ConversationManager:
    """Get or create conversation manager instance"""
    global _conversation_manager
    
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
        
    return _conversation_manager