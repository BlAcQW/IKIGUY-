"""
Gemini AI Service for EstateFlow.

Wraps Google's Generative AI SDK to provide text generation
for the property chat feature. Gracefully degrades when
API key is not configured.
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Google Gemini AI client.

    Used by PropertyChatService to generate AI-powered
    responses about property listings.
    """

    def __init__(self, model: str = "gemini-2.0-flash-exp"):
        """
        Initialize Gemini service.

        Args:
            model: Gemini model ID to use for generation.
        """
        self.model_name = model
        self._api_key = os.getenv("GOOGLE_API_KEY")
        self._client = None
        self._model = None

        if self._api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self._api_key)
                self._client = genai
                self._model = genai.GenerativeModel(self.model_name)
                logger.info(f"Gemini service initialized with model: {self.model_name}")
            except ImportError:
                logger.warning(
                    "google-generativeai package not installed. "
                    "Install with: pip install google-generativeai"
                )
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
        else:
            logger.warning("GOOGLE_API_KEY not set - Gemini chat will use fallback responses")

    def is_available(self) -> bool:
        """
        Check if Gemini API is configured and ready.

        Returns:
            True if API key is set and SDK is loaded.
        """
        return self._model is not None

    async def generate_content(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_output_tokens: int = 500,
        timeout: float = 30.0,
        system_instruction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate text content using Gemini.

        Args:
            prompt: The full prompt to send.
            temperature: Sampling temperature (0.0 - 1.0).
            max_output_tokens: Maximum tokens in the response.
            timeout: Request timeout in seconds.
            system_instruction: Optional system-level instruction.

        Returns:
            Dict with keys: success (bool), content (str), model (str).
        """
        if not self.is_available():
            return {
                "success": False,
                "content": "",
                "model": "unavailable",
                "error": "Gemini API not configured"
            }

        try:
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
            }

            response = await self._model.generate_content_async(
                prompt,
                generation_config=generation_config,
            )

            if response and response.text:
                return {
                    "success": True,
                    "content": response.text,
                    "model": self.model_name,
                }
            else:
                # Response was blocked or empty
                block_reason = ""
                if hasattr(response, "prompt_feedback"):
                    block_reason = str(response.prompt_feedback)
                return {
                    "success": False,
                    "content": "",
                    "model": self.model_name,
                    "error": f"Empty response from Gemini. {block_reason}",
                }

        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            return {
                "success": False,
                "content": "",
                "model": self.model_name,
                "error": str(e),
            }
