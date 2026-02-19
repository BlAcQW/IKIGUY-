"""
Chat routes for assistant conversations.
"""

import logging
import time
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, File, UploadFile
from pydantic import BaseModel

from ...services.assistant_service import assistant_service
from ...services.unified_llm_service import UnifiedLLMService
from apps.shared.integration.ai_services import UnifiedTTSService
from ...services.unified_asr_service import UnifiedASRService
from ...services.conversation_manager import get_conversation_manager

logger = logging.getLogger(__name__)

# Initialize unified services
llm_service = UnifiedLLMService()
tts_service = UnifiedTTSService()
asr_service = UnifiedASRService()
conversation_manager = get_conversation_manager()

router = APIRouter(prefix="/assistant", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request model."""
    user_text: str
    assistant_id: str
    system_prompt: Optional[str] = None
    first_message: Optional[str] = None
    llm_provider: Optional[str] = "openai"
    llm_model: Optional[str] = "gpt-4o-mini"
    tts_provider: Optional[str] = "meta_mms"
    tts_voice: Optional[str] = "mms-tts-aka"
    stt_provider: Optional[str] = "meta_mms"
    stt_model: Optional[str] = "mms-1b-all"
    language: Optional[str] = "en"
    conversation_history: Optional[List[Dict[str, str]]] = []


class ChatResponse(BaseModel):
    """Chat response model."""
    assistant_reply: str
    audio_samples: Optional[List[float]] = []
    audio_url: Optional[str] = None
    conversation_id: Optional[str] = None
    processing_time: Optional[float] = None


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(request: ChatRequest):
    """
    Process a chat message with an assistant.
    
    Args:
        request: Chat request with user text and assistant configuration
        
    Returns:
        Assistant's reply with optional audio
    """
    try:
        # Get the assistant configuration if ID provided
        assistant = None
        if request.assistant_id:
            assistant = assistant_service.get_assistant(request.assistant_id)
            if not assistant:
                logger.warning(f"Assistant {request.assistant_id} not found")
        
        # Use assistant config if available, otherwise use request params
        if assistant:
            system_prompt = assistant.system_prompt or request.system_prompt
            llm_provider = assistant.llm_provider or request.llm_provider
            llm_model = assistant.llm_model or request.llm_model
            tts_provider = assistant.tts_provider or request.tts_provider
            tts_voice = assistant.tts_voice or request.tts_voice
            language = assistant.language or request.language
        else:
            system_prompt = request.system_prompt
            llm_provider = request.llm_provider
            llm_model = request.llm_model
            tts_provider = request.tts_provider
            tts_voice = request.tts_voice
            language = request.language
        
        # Generate LLM response
        # For now, we'll create a simple mock response
        # In production, this would call the actual LLM service
        assistant_reply = await generate_llm_response(
            user_text=request.user_text,
            system_prompt=system_prompt,
            llm_provider=llm_provider,
            llm_model=llm_model,
            conversation_history=request.conversation_history
        )
        
        # Generate audio if TTS is configured
        audio_samples = []
        audio_url = None

        if tts_provider and tts_voice:
            try:
                # Generate TTS audio using UnifiedTTSService
                tts_result = await tts_service.synthesize(
                    text=assistant_reply,
                    voice_id=tts_voice,
                    model=tts_provider,
                    language=language
                )

                # Convert base64 audio to URL or samples
                audio_url = f"data:audio/wav;base64,{tts_result.audio_base64}"
                logger.info(f"TTS generated with {tts_provider}/{tts_voice} in {tts_result.processing_time:.2f}s")

            except Exception as e:
                logger.error(f"Failed to generate TTS: {e}")
                # Continue without audio
        
        return ChatResponse(
            assistant_reply=assistant_reply,
            audio_samples=audio_samples,
            audio_url=audio_url,
            conversation_id=f"conv_{request.assistant_id}",
            processing_time=0.5
        )
        
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def generate_llm_response(
    user_text: str,
    system_prompt: str,
    llm_provider: str,
    llm_model: str,
    conversation_history: List[Dict[str, str]]
) -> str:
    """
    Generate LLM response based on user input using real LLM providers.

    Supports: OpenAI, Anthropic, Gemini, Ollama
    """
    try:
        # Build messages array from conversation history
        messages = []

        # Add conversation history
        for msg in conversation_history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })

        # Add current user message
        messages.append({
            "role": "user",
            "content": user_text
        })

        # Call the unified LLM service
        response = await llm_service.chat_completion(
            messages=messages,
            provider=llm_provider,
            model=llm_model,
            system_prompt=system_prompt,
            temperature=0.7
        )

        # Extract text from response
        return response.get("text", "I'm sorry, I couldn't generate a response.")

    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        # Fallback response
        return f"I apologize, but I'm having trouble processing your request. Error: {str(e)}"


@router.post("/transcribe")
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    stt_provider: str = "akan-whisper",
    language: str = "tw"
):
    """
    Transcribe audio to text using UnifiedASRService.

    Args:
        audio_file: Audio file to transcribe
        stt_provider: STT provider to use (akan-whisper, faster-whisper, meta-mms, etc.)
        language: Language code (tw, en, etc.)

    Returns:
        Transcribed text with confidence and metadata
    """
    try:
        # Read audio file
        audio_data = await audio_file.read()

        # Use UnifiedASRService for transcription
        asr_result = await asr_service.transcribe(
            audio_data=audio_data,
            model=stt_provider,
            language=language
        )

        return {
            "text": asr_result.text,
            "confidence": asr_result.confidence,
            "language": asr_result.language,
            "dialect": asr_result.dialect,
            "provider": asr_result.model,
            "processing_time": asr_result.processing_time,
            "segments": asr_result.segments,
            "timestamps": asr_result.timestamps
        }

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Get conversation history from Redis/MongoDB.

    Args:
        conversation_id: Conversation ID

    Returns:
        Conversation history with messages and metadata
    """
    try:
        # Get session from conversation manager
        session = conversation_manager.get_session(conversation_id)

        if not session:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")

        return {
            "conversation_id": conversation_id,
            "user_id": session.user_id,
            "domain": session.domain,
            "messages": session.messages,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "metadata": session.metadata,
            "statistics": conversation_manager.get_statistics(conversation_id)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversation/create")
async def create_conversation(
    user_id: str,
    domain: str = "general",
    language: str = "en",
    tts_provider: str = "coqui-tts"
):
    """
    Create a new conversation session.

    Args:
        user_id: User ID
        domain: Conversation domain (general, healthcare, education, finance)
        language: Language code (en, tw, etc.)
        tts_provider: TTS provider to use

    Returns:
        New conversation session ID
    """
    try:
        session_id = await conversation_manager.create_session(
            user_id=user_id,
            domain=domain,
            metadata={"language": language},
            tts_provider=tts_provider
        )

        return {
            "conversation_id": session_id,
            "user_id": user_id,
            "domain": domain,
            "language": language,
            "tts_provider": tts_provider,
            "created_at": time.time()
        }

    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversation/{conversation_id}")
async def end_conversation(conversation_id: str):
    """
    End a conversation session and return final statistics.

    Args:
        conversation_id: Conversation ID

    Returns:
        Final conversation data and statistics
    """
    try:
        session_data = conversation_manager.end_session(conversation_id)

        if not session_data:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")

        return {
            "conversation_id": conversation_id,
            "session_data": session_data,
            "statistics": conversation_manager.get_statistics(conversation_id),
            "ended_at": time.time()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))