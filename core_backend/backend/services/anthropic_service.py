#!/usr/bin/env python3
"""
Anthropic Service for LLM Integration
Handles chat completions and other Anthropic API interactions
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any
import anthropic

logger = logging.getLogger(__name__)


class AnthropicService:
    """Service for Anthropic API integration."""
    
    def __init__(self):
        """Initialize the Anthropic service."""
        self.client = None
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Anthropic client."""
        if not self.api_key:
            logger.warning("Anthropic API key not found in environment variables")
            logger.debug(f"Environment variables: ANTHROPIC_API_KEY={'***' if os.getenv('ANTHROPIC_API_KEY') else 'NOT SET'}")
            return
        
        try:
            self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
            logger.info("✅ Anthropic client initialized successfully")
            logger.debug(f"Anthropic API key loaded: {self.api_key[:10]}...")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Anthropic client: {e}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-sonnet-4",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to Anthropic.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Anthropic model to use
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt to prepend
            
        Returns:
            Dictionary with response text and metadata
        """
        if not self.client:
            raise Exception("Anthropic client not initialized. Check API key.")
        
        try:
            # Prepare messages for Anthropic format
            # Anthropic uses a different message format than OpenAI
            anthropic_messages = []
            
            # Add system prompt if provided
            if system_prompt:
                anthropic_messages.append({
                    "role": "user",
                    "content": f"System: {system_prompt}\n\nUser: {messages[0]['content'] if messages else ''}"
                })
                # Skip the first user message since we included it above
                for msg in messages[1:]:
                    anthropic_messages.append(msg)
            else:
                anthropic_messages = messages
            
            # Prepare parameters
            params = {
                "model": model,
                "messages": anthropic_messages,
                "temperature": temperature,
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens
            
            # Make API call
            response = await self.client.messages.create(**params)
            
            # Extract response
            content = response.content[0].text if response.content else ""
            usage = response.usage
            
            return {
                "text": content,
                "model": model,
                "usage": {
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "total_tokens": usage.input_tokens + usage.output_tokens
                },
                "finish_reason": response.stop_reason
            }
            
        except Exception as e:
            logger.error(f"Error in Anthropic chat completion: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Anthropic service is available."""
        return self.client is not None and self.api_key is not None
    
    async def test_connection(self) -> bool:
        """Test the Anthropic connection."""
        if not self.is_available():
            return False
        
        try:
            # Simple test with a minimal request using cheapest model
            response = await self.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                model="claude-3-haiku-20240307",
                max_tokens=10
            )
            return True
        except Exception as e:
            error_msg = str(e)
            if "credit balance" in error_msg.lower():
                logger.warning("Anthropic API key is valid but has insufficient credits")
                # Consider this a successful connection test (API key is valid)
                return True
            logger.error(f"Anthropic connection test failed: {e}")
            return False


# Global instance
anthropic_service = AnthropicService()






