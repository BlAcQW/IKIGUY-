"""
Ollama LLM Service
Provides integration with Ollama for local GPU-based language models.

Supported models:
- llama3.2:3b (2GB, 128K context)
- mistral:7b (4.4GB, 32K context)
- aya:8b (4.8GB, 8K context, 23 languages)
- llama3.1:8b (4.9GB, 128K context)
"""

import logging
import os
import aiohttp
from typing import Dict, List, Any, Optional, AsyncIterator
import json

logger = logging.getLogger(__name__)


class OllamaService:
    """Service for interacting with Ollama API."""

    def __init__(self, endpoint: str = None):
        """
        Initialize Ollama service.

        Args:
            endpoint: Ollama API endpoint (defaults to env var or https://ollama.ailabsafrica.com)
        """
        self.endpoint = endpoint or os.getenv(
            "OLLAMA_ENDPOINT",
            "https://ollama.ailabsafrica.com"
        )
        self.default_model = "llama3.2:3b"

        logger.info(f"Ollama service initialized with endpoint: {self.endpoint}")

    def is_available(self) -> bool:
        """
        Check if Ollama service is available.

        Returns:
            True if service is reachable, False otherwise
        """
        try:
            import requests
            response = requests.get(f"{self.endpoint}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama service not available: {e}")
            return False

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available Ollama models.

        Returns:
            List of model dictionaries with name, size, and details
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.endpoint}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("models", [])
                    else:
                        logger.error(f"Failed to list models: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 1000,
        system_prompt: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a chat completion using Ollama.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (llama3.2:3b, mistral:7b, aya:8b, llama3.1:8b)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt (prepended to messages)
            stream: Whether to stream the response

        Returns:
            Dict with 'content', 'model', 'tokens', and metadata
        """
        model = model or self.default_model

        try:
            # Prepare messages
            ollama_messages = []

            # Add system prompt if provided
            if system_prompt:
                ollama_messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            # Add conversation messages
            ollama_messages.extend(messages)

            # Prepare request payload
            payload = {
                "model": model,
                "messages": ollama_messages,
                "stream": stream,
                "options": {
                    "temperature": temperature,
                }
            }

            if max_tokens:
                payload["options"]["num_predict"] = max_tokens

            logger.info(f"🤖 Ollama request: model={model}, messages={len(ollama_messages)}, temp={temperature}")

            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.endpoint}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ollama API error {response.status}: {error_text}")
                        raise Exception(f"Ollama API error: {error_text}")

                    if stream:
                        # Handle streaming response
                        full_content = ""
                        async for line in response.content:
                            if line:
                                try:
                                    chunk = json.loads(line.decode('utf-8'))
                                    if 'message' in chunk and 'content' in chunk['message']:
                                        full_content += chunk['message']['content']
                                except json.JSONDecodeError:
                                    continue

                        result = {
                            "content": full_content,
                            "model": model,
                            "finish_reason": "stop",
                            "tokens": {
                                "prompt": 0,
                                "completion": 0,
                                "total": 0
                            }
                        }
                    else:
                        # Handle non-streaming response
                        data = await response.json()

                        message_content = data.get("message", {}).get("content", "")

                        result = {
                            "content": message_content,
                            "model": model,
                            "finish_reason": data.get("done_reason", "stop"),
                            "tokens": {
                                "prompt": data.get("prompt_eval_count", 0),
                                "completion": data.get("eval_count", 0),
                                "total": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                            },
                            "total_duration_ms": data.get("total_duration", 0) / 1_000_000,
                            "eval_duration_ms": data.get("eval_duration", 0) / 1_000_000,
                        }

                    logger.info(f"✅ Ollama response: {len(result['content'])} chars, {result['tokens']['total']} tokens")
                    return result

        except Exception as e:
            logger.error(f"❌ Ollama chat completion error: {e}")
            raise Exception(f"Ollama error: {str(e)}")

    async def generate_content(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_output_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Simple completion interface (compatible with Gemini service).

        Args:
            prompt: Text prompt
            model: Model name
            temperature: Sampling temperature
            max_output_tokens: Maximum tokens to generate

        Returns:
            Dict with 'content' key
        """
        messages = [{"role": "user", "content": prompt}]

        result = await self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_output_tokens
        )

        return {"content": result["content"]}

    async def test_connection(self) -> bool:
        """
        Test connection to Ollama service.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            models = await self.list_models()
            return len(models) > 0
        except Exception as e:
            logger.error(f"Ollama connection test failed: {e}")
            return False

    def get_supported_models(self) -> List[str]:
        """
        Get list of supported model names.

        Returns:
            List of model name strings
        """
        return [
            "llama3.2:3b",
            "llama3.1:8b",
            "mistral:7b",
            "aya:8b",
            "kasaai-llama-twi",  # When available
            "kasaai-aya-ghana",  # When available
            "kasaai-mistral-ghana",  # When available
        ]


# Global instance
ollama_service = OllamaService()


def get_ollama_service() -> OllamaService:
    """
    Get the global Ollama service instance.

    Returns:
        OllamaService instance
    """
    return ollama_service
