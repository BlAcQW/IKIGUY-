#!/usr/bin/env python3
"""
OpenAI Service for LLM Integration
Handles chat completions and other OpenAI API interactions
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any
import openai
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for OpenAI API integration."""
    
    def __init__(self):
        """Initialize the OpenAI service."""
        self.client = None
        self.api_key = os.getenv("OPENAI_API_KEY")
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the OpenAI client."""
        if not self.api_key:
            logger.warning("OpenAI API key not found in environment variables")
            logger.debug(f"Environment variables: OPENAI_API_KEY={'***' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
            return
        
        try:
            self.client = AsyncOpenAI(api_key=self.api_key)
            logger.info("✅ OpenAI client initialized successfully")
            logger.debug(f"OpenAI API key loaded: {self.api_key[:10]}...")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI client: {e}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-5-mini",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to OpenAI.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: OpenAI model to use
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt to prepend
            
        Returns:
            Dictionary with response text and metadata
        """
        if not self.client:
            raise Exception("OpenAI client not initialized. Check API key.")
        
        try:
            # Prepare messages
            api_messages = []
            
            # Add system prompt if provided
            if system_prompt:
                api_messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # Add user messages
            api_messages.extend(messages)
            
            # Prepare parameters
            params = {
                "model": model,
                "messages": api_messages,
                "temperature": temperature,
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens
            
            # Make API call
            response = await self.client.chat.completions.create(**params)
            
            # Extract response
            content = response.choices[0].message.content
            usage = response.usage
            
            return {
                "text": content,
                "model": model,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                },
                "finish_reason": response.choices[0].finish_reason
            }
            
        except Exception as e:
            logger.error(f"Error in OpenAI chat completion: {e}")
            raise
    
    async def transcribe_audio(
        self,
        audio_file_path: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio using OpenAI Whisper API.
        
        Args:
            audio_file_path: Path to audio file
            language: Language code (optional)
            prompt: Optional prompt for better transcription
            
        Returns:
            Dictionary with transcription text and metadata
        """
        if not self.client:
            raise Exception("OpenAI client not initialized. Check API key.")
        
        try:
            with open(audio_file_path, "rb") as audio_file:
                params = {
                    "file": audio_file,
                    "model": "whisper-1",
                    "response_format": "verbose_json"
                }
                
                if language:
                    params["language"] = language
                if prompt:
                    params["prompt"] = prompt
                
                response = await self.client.audio.transcriptions.create(**params)
                
                return {
                    "text": response.text,
                    "language": response.language,
                    "duration": response.duration,
                    "segments": response.segments if hasattr(response, 'segments') else []
                }
                
        except Exception as e:
            logger.error(f"Error in OpenAI audio transcription: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if OpenAI service is available."""
        return self.client is not None and self.api_key is not None
    
    async def text_to_speech(
        self,
        text: str,
        voice: str = "alloy",
        model: str = "tts-1",
        response_format: str = "mp3",
        speed: float = 1.0
    ) -> bytes:
        """
        Convert text to speech using OpenAI TTS API.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            model: TTS model to use (tts-1 or tts-1-hd)
            response_format: Audio format (mp3, opus, aac, flac, wav, pcm)
            speed: Speech speed (0.25 to 4.0)
            
        Returns:
            Audio data as bytes
        """
        if not self.client:
            raise Exception("OpenAI client not initialized. Check API key.")
        
        try:
            response = await self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                response_format=response_format,
                speed=speed
            )
            
            # Get audio data
            audio_data = response.content
            return audio_data
            
        except Exception as e:
            logger.error(f"Error in OpenAI text-to-speech: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """Test the OpenAI connection."""
        if not self.is_available():
            return False
        
        try:
            # Simple test with a minimal request
            response = await self.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                model="gpt-4o-mini",
                max_tokens=10
            )
            return True
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False


# Global instance
openai_service = OpenAIService()
