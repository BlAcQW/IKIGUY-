"""
Gemini AI Service

Centralized service for interacting with Google's Gemini API using direct HTTP requests.
Provides a unified interface for all Gemini-based AI operations across the application.
"""

import httpx
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Service for interacting with Google's Gemini API.

    Provides methods for generating content using Gemini models with
    proper error handling, timeout management, and response parsing.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        """
        Initialize the Gemini service.

        Args:
            api_key (Optional[str]): Gemini API key. If None, will use GEMINI_API_KEY env var
            model (str): Gemini model to use. Defaults to gemini-2.5-flash
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

        if not self.api_key:
            logger.warning("Gemini API key not configured")

    def is_available(self) -> bool:
        """
        Check if the Gemini service is available.

        Returns:
            bool: True if API key is configured, False otherwise
        """
        return bool(self.api_key)

    async def generate_content(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_output_tokens: int = 1000,
        timeout: float = 60.0,
        max_input_length: int = 20000
    ) -> Dict[str, Any]:
        """
        Generate content using Gemini API.

        Args:
            prompt (str): The input prompt for content generation
            temperature (float): Controls randomness (0.0 = deterministic, 1.0 = creative)
            max_output_tokens (int): Maximum tokens to generate
            timeout (float): Request timeout in seconds
            max_input_length (int): Maximum input prompt length to prevent token overflow

        Returns:
            Dict[str, Any]: Response containing generated content and metadata

        Raises:
            Exception: If API call fails or returns invalid response
        """
        if not self.is_available():
            raise Exception("Gemini API key not configured")

        # Truncate prompt if too long
        truncated_prompt = prompt[:max_input_length] if len(prompt) > max_input_length else prompt
        if len(prompt) > max_input_length:
            logger.warning(f"Prompt truncated from {len(prompt)} to {max_input_length} characters")

        endpoint = f"{self.base_url}/{self.model}:generateContent"

        request_payload = {
            "contents": [{
                "parts": [{
                    "text": truncated_prompt
                }]
            }],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens,
            }
        }

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

        try:
            logger.info(f"Generating content with Gemini {self.model} (prompt length: {len(truncated_prompt)})")

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    endpoint,
                    headers=headers,
                    json=request_payload
                )

                if response.status_code == 200:
                    response_data = response.json()

                    # Parse response structure (Gemini 2.5 has different structure)
                    candidates = response_data.get("candidates", [])
                    if candidates and len(candidates) > 0:
                        candidate = candidates[0]
                        content = candidate.get("content", {})

                        # Check for finish_reason and safety ratings
                        finish_reason = candidate.get("finishReason", "UNKNOWN")
                        safety_ratings = candidate.get("safetyRatings", [])

                        # Log important metadata
                        if finish_reason != "STOP":
                            logger.warning(f"Gemini finish_reason: {finish_reason} (not STOP - may indicate truncation)")

                        # Check if blocked by safety filters
                        blocked = any(rating.get("blocked", False) for rating in safety_ratings)
                        if blocked:
                            logger.error(f"Gemini response blocked by safety filters: {safety_ratings}")
                            raise Exception("Response blocked by Gemini safety filters")

                        # Try new structure first (parts with text)
                        parts = content.get("parts", [])
                        if parts and len(parts) > 0:
                            generated_text = parts[0].get("text")
                            if generated_text:
                                logger.info(f"Gemini content generation successful, length: {len(generated_text)}, finish_reason: {finish_reason}")

                                # Warn if truncated
                                if finish_reason in ["MAX_TOKENS", "RECITATION", "OTHER"]:
                                    logger.warning(f"⚠️  Gemini response may be incomplete. Reason: {finish_reason}, Requested: {max_output_tokens} tokens")

                                return {
                                    "success": True,
                                    "content": generated_text.strip(),
                                    "model": self.model,
                                    "input_length": len(truncated_prompt),
                                    "output_length": len(generated_text),
                                    "temperature": temperature,
                                    "max_tokens": max_output_tokens,
                                    "finish_reason": finish_reason,
                                    "generated_at": datetime.utcnow().isoformat()
                                }

                        # Try alternative structure (role only, no parts - happens with MAX_TOKENS)
                        # This happens when output is cut due to token limit
                        if content.get("role") == "model" and not parts:
                            # Check if there's thought tokens or alternative content
                            usage = response_data.get("usageMetadata", {})
                            thought_tokens = usage.get("thoughtsTokenCount", 0)
                            if thought_tokens > 0:
                                # Model thought but didn't produce output text (token limit)
                                logger.warning(f"Gemini hit token limit: {usage}")
                                return {
                                    "success": True,
                                    "content": "[Response truncated - increase max_output_tokens]",
                                    "model": self.model,
                                    "input_length": len(truncated_prompt),
                                    "output_length": 0,
                                    "temperature": temperature,
                                    "max_tokens": max_output_tokens,
                                    "generated_at": datetime.utcnow().isoformat()
                                }

                    # If we get here, response structure was unexpected
                    logger.error(f"Unexpected Gemini response structure: {response_data}")
                    raise Exception("No content in Gemini response")

                else:
                    error_text = response.text
                    logger.error(f"Gemini API failed with status {response.status_code}: {error_text}")
                    raise Exception(f"Gemini API failed with status {response.status_code}: {error_text}")

        except httpx.TimeoutException:
            logger.error(f"Gemini API request timed out after {timeout} seconds")
            raise Exception(f"Gemini API request timed out after {timeout} seconds")
        except httpx.RequestError as e:
            logger.error(f"Gemini API request error: {str(e)}")
            raise Exception(f"Gemini API request error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in Gemini content generation: {str(e)}")
            raise

    async def generate_system_prompt(
        self,
        prompt: str,
        max_output_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """
        Generate a system prompt using optimized settings.

        Args:
            prompt (str): The input prompt
            max_output_tokens (int): Maximum tokens for system prompt
            temperature (float): Temperature for creativity

        Returns:
            str: Generated system prompt
        """
        result = await self.generate_content(
            prompt=prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            max_input_length=20000
        )
        return result["content"]

    async def generate_summary(
        self,
        content: str,
        max_output_tokens: int = 500,
        temperature: float = 0.3
    ) -> str:
        """
        Generate a summary using optimized settings for consistency.

        Args:
            content (str): Content to summarize
            max_output_tokens (int): Maximum tokens for summary
            temperature (float): Lower temperature for consistency

        Returns:
            str: Generated summary
        """
        result = await self.generate_content(
            prompt=content,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            max_input_length=15000
        )
        return result["content"]

    async def extract_structured_data(
        self,
        prompt: str,
        max_output_tokens: int = 1500,
        temperature: float = 0.1
    ) -> str:
        """
        Extract structured data using optimized settings for consistency.

        Args:
            prompt (str): Extraction prompt
            max_output_tokens (int): Maximum tokens for extraction
            temperature (float): Very low temperature for consistency

        Returns:
            str: Extracted structured data
        """
        result = await self.generate_content(
            prompt=prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            max_input_length=20000
        )
        return result["content"]

    def update_model(self, model: str) -> None:
        """
        Update the Gemini model being used.

        Args:
            model (str): New model name (e.g., 'gemini-2.5-flash', 'gemini-2.5-pro')
        """
        old_model = self.model
        self.model = model
        logger.info(f"Gemini model updated from {old_model} to {model}")


# Global service instance
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """
    Get the global Gemini service instance.

    Returns:
        GeminiService: The global service instance
    """
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service


def set_gemini_model(model: str) -> None:
    """
    Update the global Gemini model.

    Args:
        model (str): New model name
    """
    service = get_gemini_service()
    service.update_model(model)


# Convenience functions for common operations
async def generate_content_with_gemini(
    prompt: str,
    temperature: float = 0.7,
    max_output_tokens: int = 1000
) -> str:
    """
    Convenience function for generating content with Gemini.

    Args:
        prompt (str): Input prompt
        temperature (float): Generation temperature
        max_output_tokens (int): Maximum output tokens

    Returns:
        str: Generated content

    Raises:
        Exception: If Gemini is not available or generation fails
    """
    service = get_gemini_service()
    if not service.is_available():
        raise Exception("Gemini service not available - API key not configured")

    result = await service.generate_content(
        prompt=prompt,
        temperature=temperature,
        max_output_tokens=max_output_tokens
    )
    return result["content"]