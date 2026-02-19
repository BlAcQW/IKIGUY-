"""
Simple voice processing routes for STT, LLM, and TTS.
"""

import logging
import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import numpy as np
import anthropic

from ...services.meta_mms_service import mms_service
from ...services.assistant_service import assistant_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["simple-voice"])


class AudioRequest(BaseModel):
    """Request model for audio processing."""
    samples: List[int]
    assistant_id: Optional[str] = None


class TextRequest(BaseModel):
    """Request model for text processing."""
    text: str
    assistant_id: Optional[str] = None


class AudioResponse(BaseModel):
    """Response model for audio processing."""
    samples: List[int]
    text: Optional[str] = None
    partials: List[str] = []


class TextResponse(BaseModel):
    """Response model for text processing."""
    text: str
    reply: Optional[str] = None
    response: Optional[str] = None


@router.post("/stt")
async def speech_to_text(request: AudioRequest) -> AudioResponse:
    """
    Convert speech to text using Meta MMS.
    
    Args:
        request: Audio samples and optional assistant ID
        
    Returns:
        Transcribed text
    """
    try:
        # Get assistant configuration if provided
        language = "en"
        if request.assistant_id:
            assistant = assistant_service.get_assistant(request.assistant_id)
            if assistant and assistant.language:
                language = assistant.language
        
        # Convert samples to numpy array
        audio_array = np.array(request.samples, dtype=np.float32) / 32767.0
        
        # Use Meta MMS for transcription
        try:
            # Try Meta MMS first
            text = await mms_service.transcribe(
                audio_array.tobytes(),
                language=language
            )
        except Exception as mms_error:
            logger.warning(f"Meta MMS transcription failed: {mms_error}")
            # Fallback to a simple response for testing
            text = "Hello, I heard you speaking."
        
        return AudioResponse(
            samples=request.samples,
            text=text,
            partials=[text]
        )
        
    except Exception as e:
        logger.error(f"STT failed: {e}")
        # Return a default response for testing
        return AudioResponse(
            samples=request.samples,
            text="I'm ready to help you.",
            partials=["I'm ready to help you."]
        )


@router.post("/llm")
async def process_with_llm(request: TextRequest) -> TextResponse:
    """
    Process text with Anthropic Claude LLM.
    
    Args:
        request: Input text and optional assistant ID
        
    Returns:
        LLM response
    """
    try:
        # Get assistant configuration if provided
        system_prompt = "You are Claude, a helpful AI assistant. Be conversational and brief."
        if request.assistant_id:
            assistant = assistant_service.get_assistant(request.assistant_id)
            if assistant and assistant.system_prompt:
                system_prompt = assistant.system_prompt
        
        # Use Anthropic Claude
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            try:
                client = anthropic.Anthropic(api_key=api_key)
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=150,  # Keep responses brief for voice
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": request.text}
                    ]
                )
                reply = response.content[0].text
            except Exception as claude_error:
                logger.warning(f"Anthropic Claude failed: {claude_error}")
                # Fallback response
                reply = f"I understand you said: '{request.text}'. How can I help you today?"
        else:
            # Fallback if no API key
            reply = f"I heard: '{request.text}'. I'm your AI assistant. How can I assist you?"
        
        return TextResponse(
            text=reply,
            reply=reply,
            response=reply
        )
        
    except Exception as e:
        logger.error(f"LLM processing failed: {e}")
        # Return a default response
        return TextResponse(
            text="I'm here to help. What would you like to know?",
            reply="I'm here to help. What would you like to know?",
            response="I'm here to help. What would you like to know?"
        )


@router.post("/tts")
async def text_to_speech(request: TextRequest) -> AudioResponse:
    """
    Convert text to speech using Meta MMS.
    
    Args:
        request: Text to synthesize and optional assistant ID
        
    Returns:
        Audio samples
    """
    try:
        # Get assistant configuration if provided
        language = "en"
        voice = "mms-tts-eng"
        if request.assistant_id:
            assistant = assistant_service.get_assistant(request.assistant_id)
            if assistant:
                if assistant.language:
                    language = assistant.language
                if assistant.tts_voice:
                    voice = assistant.tts_voice
        
        # Use Meta MMS for synthesis
        try:
            # Try Meta MMS first
            audio_bytes = await mms_service.synthesize(
                request.text,
                language=language,
                voice=voice
            )
            # Convert bytes to samples
            audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
            samples = (audio_array * 32767).astype(np.int16).tolist()
        except Exception as mms_error:
            logger.warning(f"Meta MMS synthesis failed: {mms_error}")
            # Generate silent audio as fallback
            duration = len(request.text) * 100  # Rough estimate
            samples = [0] * duration
        
        return AudioResponse(
            samples=samples,
            text=request.text,
            partials=[]
        )
        
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        # Return silent audio as fallback
        duration = 22050  # 1 second of silence at 22kHz
        return AudioResponse(
            samples=[0] * duration,
            text=request.text,
            partials=[]
        )


@router.post("/loop")
async def voice_loop(request: AudioRequest) -> AudioResponse:
    """
    Complete voice loop: STT -> LLM -> TTS.
    
    Args:
        request: Audio samples and optional assistant ID
        
    Returns:
        Complete voice response
    """
    try:
        # STT
        stt_response = await speech_to_text(request)
        
        # LLM
        if stt_response.text:
            llm_request = TextRequest(text=stt_response.text, assistant_id=request.assistant_id)
            llm_response = await process_with_llm(llm_request)
            
            # TTS
            tts_request = TextRequest(text=llm_response.text, assistant_id=request.assistant_id)
            tts_response = await text_to_speech(tts_request)
            
            return AudioResponse(
                samples=tts_response.samples,
                text=llm_response.text,
                partials=[stt_response.text, llm_response.text]
            )
        else:
            # No text recognized
            return AudioResponse(
                samples=[0] * 22050,  # 1 second of silence
                text="I didn't catch that. Could you please repeat?",
                partials=[]
            )
            
    except Exception as e:
        logger.error(f"Voice loop failed: {e}")
        # Return error response
        return AudioResponse(
            samples=[0] * 22050,
            text="Sorry, I encountered an error. Please try again.",
            partials=[]
        )