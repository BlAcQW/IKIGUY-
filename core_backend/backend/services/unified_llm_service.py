#!/usr/bin/env python3
"""
Unified LLM Service
Handles LLM interactions across different providers (OpenAI, Anthropic, Gemini, Ollama)
"""

import logging
from typing import Dict, List, Optional, Any
from .openai_service import openai_service
from .anthropic_service import anthropic_service
from .gemini_service import get_gemini_service
from .ollama_service import get_ollama_service

logger = logging.getLogger(__name__)


class UnifiedLLMService:
    """Unified service for LLM interactions across providers."""

    def __init__(self):
        """Initialize the unified LLM service."""
        self.providers = {
            "openai": openai_service,
            "anthropic": anthropic_service,
            "gemini": get_gemini_service(),
            "ollama": get_ollama_service(),
        }
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        provider: str = "openai",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to the specified LLM provider.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            provider: LLM provider ('openai' or 'anthropic')
            model: Model to use (will use default if not specified)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            
        Returns:
            Dictionary with response text and metadata
        """
        # Normalize provider name
        provider = provider.lower()
        
        if provider not in self.providers:
            raise ValueError(f"Unsupported LLM provider: {provider}. Supported providers: {list(self.providers.keys())}")
        
        service = self.providers[provider]
        
        if not service.is_available():
            raise Exception(f"{provider.capitalize()} service not available. Check API key configuration.")
        
        # Set default models if not specified
        if not model:
            if provider == "openai":
                model = "gpt-4o-mini"
            elif provider == "anthropic":
                model = "claude-3-5-sonnet-20241022"
            elif provider == "gemini":
                model = "gemini-2.5-flash"
            elif provider == "ollama":
                model = "llama3.2:3b"
        
        try:
            response = await service.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt
            )
            
            # Add provider info to response
            response["provider"] = provider
            
            return response
            
        except Exception as e:
            logger.error(f"Error in {provider} chat completion: {e}")
            raise
    
    def is_provider_available(self, provider: str) -> bool:
        """Check if a specific provider is available."""
        provider = provider.lower()
        if provider not in self.providers:
            return False
        return self.providers[provider].is_available()
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        return [provider for provider, service in self.providers.items() if service.is_available()]
    
    async def test_provider_connection(self, provider: str) -> bool:
        """Test connection to a specific provider."""
        provider = provider.lower()
        if provider not in self.providers:
            return False
        return await self.providers[provider].test_connection()
    
    def get_default_model(self, provider: str) -> str:
        """Get the default model for a provider."""
        provider = provider.lower()
        if provider == "openai":
            return "gpt-4o-mini"
        elif provider == "anthropic":
            return "claude-3-5-sonnet-20241022"
        elif provider == "gemini":
            return "gemini-2.5-flash"
        elif provider == "ollama":
            return "llama3.2:3b"
        else:
            raise ValueError(f"Unknown provider: {provider}")


# Global instance
unified_llm_service = UnifiedLLMService()






