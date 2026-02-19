"""
LLM Provider Service - Centralized LLM Service with Billing Integration

Provides unified access to all LLM providers (Gemini, Ollama models) with integrated billing,
usage tracking, health monitoring, and provider management.

This service wraps the lower-level ai_services LLM infrastructure and adds:
- Automatic cost calculation and wallet deductions
- Provider health monitoring and failover
- Request/response normalization
- Token usage tracking
- Multi-language and streaming support
- Dual-backend support (Cloud API + Local models)

Usage Example (from any app):
    ```python
    from apps.shared.services.llm_provider_service import (
        LLMProviderService,
        ChatRequest,
        ChatMessage
    )

    # Initialize service
    llm_service = LLMProviderService()
    await llm_service.initialize()

    # Chat with automatic billing
    result = await llm_service.chat(
        user_id="user_123",
        request=ChatRequest(
            model_id="kasaai_llama_twi",
            messages=[
                ChatMessage(role="user", content="Hello!")
            ],
            temperature=0.7
        )
    )

    # Streaming chat
    async for chunk in llm_service.chat_stream(
        user_id="user_123",
        request=ChatRequest(
            model_id="llama_32_3b",
            messages=[...],
            stream=True
        )
    ):
        print(chunk.content, end='', flush=True)
    ```

Architecture:
    Apps (B2C Portal, StudyFlow, etc.)
        ↓
    LLMProviderService (this file)
        ↓
    ├─> ProviderRegistry (ai_services)
    ├─> HealthMonitor (ai_services)
    ├─> WalletService (wallet integration)
    ├─> UsageCalculator (cost calculation)
    └─> GeminiService (Gemini API)
        ↓
    LLM Provider Endpoints (Gemini API, Ollama, etc.)
"""

import logging
import asyncio
import os
from typing import Dict, List, Optional, Any, AsyncIterator
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from enum import Enum
import aiohttp
import httpx
import json

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class ChatMessage(BaseModel):
    """Chat message in conversation."""
    role: str  # "system", "user", "assistant"
    content: str


class ChatRequest(BaseModel):
    """Request for LLM chat completion."""
    model_id: str
    messages: List[ChatMessage]
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 0.9
    stream: bool = False
    system_prompt: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from LLM chat completion."""
    message: str
    model_id: str
    usage: Dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    finish_reason: str
    cost: float
    transaction_id: Optional[str] = None
    processing_time: float


class StreamChunk(BaseModel):
    """Chunk from streaming LLM response."""
    content: str
    done: bool = False
    finish_reason: Optional[str] = None


class CostEstimate(BaseModel):
    """Cost estimate for LLM operation."""
    input_cost: float
    output_cost: float  # Estimated
    total_cost: float  # Estimated
    model_id: str
    input_tokens: int
    estimated_output_tokens: int


class ProviderHealth(BaseModel):
    """Health status of an LLM provider."""
    model_id: str
    model_name: str
    status: str  # online, offline, degraded
    response_time_ms: Optional[float] = None
    last_checked: datetime
    error: Optional[str] = None


# ============================================================================
# Main Service Class
# ============================================================================

class LLMProviderService:
    """
    Centralized LLM Provider Service with billing integration.

    Manages all LLM providers (Ollama models), handles chat requests, tracks usage,
    and integrates with wallet service for automatic billing.
    """

    def __init__(
        self,
        enable_billing: bool = True,
        enable_health_monitoring: bool = True,
        cache_ttl: int = 30
    ):
        """
        Initialize LLM Provider Service.

        Args:
            enable_billing: Enable automatic wallet billing
            enable_health_monitoring: Enable provider health monitoring
            cache_ttl: Provider status cache TTL in seconds
        """
        self.enable_billing = enable_billing
        self.enable_health_monitoring = enable_health_monitoring
        self.cache_ttl = cache_ttl

        # Services (initialized in initialize())
        self.provider_registry = None
        self.health_monitor = None
        self.wallet_service = None
        self.usage_calculator = None
        self.gemini_service = None  # Gemini API client
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        # Provider cache
        self.providers_cache = {}
        self.cache_timestamp = None

        # Initialized flag
        self._initialized = False

        logger.info(f"LLMProviderService created (billing={enable_billing}, health={enable_health_monitoring})")

        # Check Gemini availability
        if self.gemini_api_key:
            logger.info("✓ Gemini API key found")
        else:
            logger.warning("⚠ Gemini API key not configured")

    async def initialize(self):
        """
        Initialize the service (load providers, start monitoring).

        Must be called before using the service.
        """
        if self._initialized:
            logger.warning("LLMProviderService already initialized")
            return

        try:
            # Import here to avoid circular dependencies
            from apps.shared.integration.ai_services.provider_registry import get_global_registry
            from apps.shared.integration.ai_services.health_monitor_service import HealthMonitorService
            from apps.shared.integration.wallet import create_wallet_service_from_env
            from apps.shared.integration.usage_calculator import UsageCalculator

            # Get provider registry
            self.provider_registry = get_global_registry()

            # Initialize health monitor if enabled
            if self.enable_health_monitoring:
                self.health_monitor = HealthMonitorService(
                    registry=self.provider_registry,
                    check_interval=60,  # Check every 60 seconds
                    timeout=5
                )
                await self.health_monitor.start()
                logger.info("Health monitor started")

            # Initialize wallet service if billing enabled
            if self.enable_billing:
                try:
                    self.wallet_service = await create_wallet_service_from_env()
                    logger.info("✓ LLM Wallet service initialized")
                except Exception as e:
                    logger.warning(f"LLM WalletService initialization failed: {e}")
                    self.enable_billing = False

            # Initialize usage calculator
            self.usage_calculator = UsageCalculator()
            logger.info("Usage calculator initialized")

            # Initialize Gemini service if API key available
            if self.gemini_api_key:
                from apps.shared.integration.gemini_service import GeminiService
                self.gemini_service = GeminiService(api_key=self.gemini_api_key)
                logger.info("✓ Gemini service initialized")

            # Load providers into cache
            await self.refresh_providers()

            self._initialized = True
            logger.info("✓ LLMProviderService initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize LLMProviderService: {str(e)}")
            raise

    async def refresh_providers(self, force: bool = False) -> Dict[str, Any]:
        """
        Refresh provider cache from registry.

        Args:
            force: Force refresh even if cache is valid

        Returns:
            Dictionary of providers
        """
        # Check cache validity
        if not force and self.cache_timestamp:
            age = (datetime.utcnow() - self.cache_timestamp).total_seconds()
            if age < self.cache_ttl:
                logger.debug(f"Using cached providers (age: {age:.1f}s)")
                return self.providers_cache

        try:
            # Get all LLM providers from registry
            from apps.shared.integration.ai_services.provider_registry import ProviderType

            providers = self.provider_registry.get_providers_by_type(ProviderType.LLM)

            # Convert to dict and add health status
            providers_dict = {}
            for provider in providers:
                provider_dict = provider.dict()

                # Add health status if monitoring enabled
                if self.enable_health_monitoring and self.health_monitor:
                    health_result = await self.health_monitor.check_provider_health(provider)
                    provider_dict['health'] = {
                        'status': 'online' if health_result.healthy else 'offline',
                        'response_time_ms': health_result.response_time_ms,
                        'last_checked': health_result.timestamp.isoformat(),
                        'error': health_result.error
                    }

                providers_dict[provider.id] = provider_dict

            # Update cache
            self.providers_cache = providers_dict
            self.cache_timestamp = datetime.utcnow()

            logger.info(f"Refreshed {len(providers_dict)} LLM providers")
            return providers_dict

        except Exception as e:
            logger.error(f"Failed to refresh providers: {str(e)}")
            return self.providers_cache

    async def get_available_providers(self) -> Dict[str, Any]:
        """Get all available LLM providers with status."""
        return await self.refresh_providers()

    async def get_provider_health(self, model_id: str) -> ProviderHealth:
        """
        Get health status for a specific provider.

        Args:
            model_id: Model ID

        Returns:
            ProviderHealth object
        """
        provider = self.provider_registry.get_provider(model_id)
        if not provider:
            raise ValueError(f"Provider {model_id} not found")

        if self.health_monitor:
            health_result = await self.health_monitor.check_provider_health(provider)
            return ProviderHealth(
                model_id=provider.id,
                model_name=provider.name,
                status='online' if health_result.healthy else 'offline',
                response_time_ms=health_result.response_time_ms,
                last_checked=health_result.timestamp,
                error=health_result.error
            )
        else:
            return ProviderHealth(
                model_id=provider.id,
                model_name=provider.name,
                status='unknown',
                last_checked=datetime.utcnow()
            )

    async def estimate_cost(
        self,
        model_id: str,
        input_tokens: int,
        estimated_output_tokens: int = 1000
    ) -> CostEstimate:
        """
        Estimate cost for LLM operation.

        Args:
            model_id: Model ID
            input_tokens: Number of input tokens
            estimated_output_tokens: Estimated output tokens

        Returns:
            CostEstimate object
        """
        # Get provider
        provider = self.provider_registry.get_provider(model_id)
        if not provider:
            raise ValueError(f"Provider {model_id} not found")

        # Calculate costs
        input_cost = self.usage_calculator.calculate_llm_cost(
            input_tokens=input_tokens,
            output_tokens=0,
            model=model_id
        )

        output_cost = self.usage_calculator.calculate_llm_cost(
            input_tokens=0,
            output_tokens=estimated_output_tokens,
            model=model_id
        )

        total_cost = input_cost + output_cost

        return CostEstimate(
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            model_id=model_id,
            input_tokens=input_tokens,
            estimated_output_tokens=estimated_output_tokens
        )

    async def chat(
        self,
        user_id: str,
        request: ChatRequest,
        skip_billing: bool = False
    ) -> ChatResponse:
        """
        Chat with LLM model with automatic billing.

        Supports both Gemini (cloud API) and Ollama (local) models.
        Routes based on model_id prefix:
        - "gemini-*" → Gemini API
        - other → Ollama

        Args:
            user_id: User ID for billing
            request: ChatRequest object
            skip_billing: Skip billing (for testing)

        Returns:
            ChatResponse object

        Raises:
            ValueError: If provider not found or offline
            Exception: If chat fails
        """
        start_time = datetime.utcnow()

        # Route to appropriate provider based on model_id
        if request.model_id.startswith("gemini-"):
            # Route to Gemini
            return await self._chat_with_gemini(
                user_id=user_id,
                request=request,
                skip_billing=skip_billing,
                start_time=start_time
            )
        else:
            # Route to Ollama (existing logic)
            return await self._chat_with_ollama(
                user_id=user_id,
                request=request,
                skip_billing=skip_billing,
                start_time=start_time
            )

    async def _chat_with_ollama(
        self,
        user_id: str,
        request: ChatRequest,
        skip_billing: bool,
        start_time: datetime
    ) -> ChatResponse:
        """
        Chat with Ollama model (existing implementation).

        Args:
            user_id: User ID for billing
            request: ChatRequest object
            skip_billing: Skip billing
            start_time: Request start time

        Returns:
            ChatResponse object
        """
        # Get provider
        logger.info(f"Looking for model: {request.model_id}")
        logger.info(f"Registry has {len(self.provider_registry.get_all_providers())} providers")
        provider = self.provider_registry.get_provider(request.model_id)
        if not provider:
            available = list(self.provider_registry.get_all_providers().keys())
            logger.error(f"Model {request.model_id} not found. Available: {available}")
            raise ValueError(f"Model {request.model_id} not found")

        # Check provider health
        if self.enable_health_monitoring and self.health_monitor:
            health = await self.get_provider_health(request.model_id)
            if health.status == 'offline':
                raise ValueError(f"Model {request.model_id} is offline")

        # Call Ollama API
        try:
            # Get max_tokens from metadata or use default
            default_max_tokens = provider.metadata.get('limits', {}).get('maxOutputTokens', 4096)
            result = await self._call_ollama_chat(
                endpoint=provider.endpoint,
                model_name=provider.model_name,
                messages=request.messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens or default_max_tokens,
                top_p=request.top_p
            )

            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()

            # Extract usage
            usage = {
                'prompt_tokens': result.get('prompt_eval_count', 0),
                'completion_tokens': result.get('eval_count', 0),
                'total_tokens': result.get('prompt_eval_count', 0) + result.get('eval_count', 0)
            }

            # Calculate cost
            cost = self.usage_calculator.calculate_llm_cost(
                input_tokens=usage['prompt_tokens'],
                output_tokens=usage['completion_tokens'],
                model=request.model_id
            )

            # Deduct from wallet if billing enabled
            transaction_id = None
            if self.enable_billing and not skip_billing and cost > 0:
                transaction_id = await self._bill_user(
                    user_id=user_id,
                    cost=cost,
                    description=f"LLM chat - {request.model_id}",
                    metadata={
                        'model_id': request.model_id,
                        'input_tokens': usage['prompt_tokens'],
                        'output_tokens': usage['completion_tokens'],
                        'total_tokens': usage['total_tokens']
                    }
                )
                if transaction_id:
                    logger.info(f"Wallet debited: ${cost:.4f} for user {user_id}, txn={transaction_id}")

            return ChatResponse(
                message=result['message']['content'],
                model_id=request.model_id,
                usage=usage,
                finish_reason=result.get('done_reason', 'stop'),
                cost=cost,
                transaction_id=transaction_id,
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"Chat failed for model {request.model_id}: {str(e)}")
            raise

    async def _chat_with_gemini(
        self,
        user_id: str,
        request: ChatRequest,
        skip_billing: bool,
        start_time: datetime
    ) -> ChatResponse:
        """
        Chat with Gemini model.

        Args:
            user_id: User ID for billing
            request: ChatRequest object
            skip_billing: Skip billing
            start_time: Request start time

        Returns:
            ChatResponse object
        """
        if not self.gemini_service or not self.gemini_api_key:
            raise ValueError("Gemini API not configured (missing GEMINI_API_KEY)")

        try:
            # Convert messages to Gemini format
            # Gemini expects: contents[{role, parts[{text}]}]
            gemini_messages = []
            for msg in request.messages:
                # Map roles: "system" and "user" → "user", "assistant" → "model"
                gemini_role = "model" if msg.role == "assistant" else "user"
                gemini_messages.append({
                    "role": gemini_role,
                    "parts": [{"text": msg.content}]
                })

            # Merge system prompt if provided
            if request.system_prompt:
                gemini_messages.insert(0, {
                    "role": "user",
                    "parts": [{"text": f"System: {request.system_prompt}"}]
                })

            # Call Gemini API
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{request.model_id}:generateContent"

            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.gemini_api_key
            }

            payload = {
                "contents": gemini_messages,
                "generationConfig": {
                    "temperature": request.temperature,
                    "topP": request.top_p,
                    "maxOutputTokens": request.max_tokens or 2048
                }
            }

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(endpoint, headers=headers, json=payload)

                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"Gemini API error {response.status_code}: {error_text}")
                    raise Exception(f"Gemini API error: {response.status_code}")

                result = response.json()

            # Parse Gemini response
            candidates = result.get("candidates", [])
            if not candidates:
                raise Exception("No candidates in Gemini response")

            candidate = candidates[0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])

            if not parts or not parts[0].get("text"):
                raise Exception("No text content in Gemini response")

            message_text = parts[0]["text"]
            finish_reason = candidate.get("finishReason", "STOP")

            # Extract token usage from metadata
            usage_metadata = result.get("usageMetadata", {})
            prompt_tokens = usage_metadata.get("promptTokenCount", 0)
            completion_tokens = usage_metadata.get("candidatesTokenCount", 0)
            total_tokens = usage_metadata.get("totalTokenCount", prompt_tokens + completion_tokens)

            usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }

            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()

            # Calculate cost (Gemini pricing)
            cost = self._calculate_gemini_cost(
                model_id=request.model_id,
                input_tokens=prompt_tokens,
                output_tokens=completion_tokens
            )

            # Deduct from wallet if billing enabled
            transaction_id = None
            if self.enable_billing and not skip_billing and cost > 0:
                transaction_id = await self._bill_user(
                    user_id=user_id,
                    cost=cost,
                    description=f"LLM chat - {request.model_id}",
                    metadata={
                        'model_id': request.model_id,
                        'input_tokens': prompt_tokens,
                        'output_tokens': completion_tokens,
                        'total_tokens': total_tokens,
                        'provider': 'gemini'
                    }
                )
                if transaction_id:
                    logger.info(f"Gemini chat completed: ${cost:.4f} for user {user_id}, txn={transaction_id}")

            return ChatResponse(
                message=message_text,
                model_id=request.model_id,
                usage=usage,
                finish_reason=finish_reason,
                cost=cost,
                transaction_id=transaction_id,
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"Gemini chat failed for model {request.model_id}: {str(e)}")
            raise

    async def _chat_stream_with_gemini(
        self,
        user_id: str,
        request: ChatRequest,
        skip_billing: bool
    ) -> AsyncIterator[StreamChunk]:
        """
        Streaming chat with Gemini model.

        Args:
            user_id: User ID for billing
            request: ChatRequest object
            skip_billing: Skip billing

        Yields:
            StreamChunk objects
        """
        if not self.gemini_service or not self.gemini_api_key:
            raise ValueError("Gemini API not configured (missing GEMINI_API_KEY)")

        start_time = datetime.utcnow()
        total_tokens = 0
        prompt_tokens = 0
        completion_tokens = 0

        try:
            # Convert messages to Gemini format
            gemini_messages = []
            for msg in request.messages:
                gemini_role = "model" if msg.role == "assistant" else "user"
                gemini_messages.append({
                    "role": gemini_role,
                    "parts": [{"text": msg.content}]
                })

            # Merge system prompt if provided
            if request.system_prompt:
                gemini_messages.insert(0, {
                    "role": "user",
                    "parts": [{"text": f"System: {request.system_prompt}"}]
                })

            # Call Gemini streaming API
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{request.model_id}:streamGenerateContent?alt=sse"

            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.gemini_api_key
            }

            payload = {
                "contents": gemini_messages,
                "generationConfig": {
                    "temperature": request.temperature,
                    "topP": request.top_p,
                    "maxOutputTokens": request.max_tokens or 2048
                }
            }

            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", endpoint, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"Gemini streaming API error {response.status_code}: {error_text}")
                        raise Exception(f"Gemini API error: {response.status_code}")

                    # Process server-sent events
                    async for line in response.aiter_lines():
                        if not line or not line.startswith('data: '):
                            continue

                        # Parse JSON from SSE data field
                        json_str = line[6:]  # Remove 'data: ' prefix
                        try:
                            chunk_data = json.loads(json_str)
                        except json.JSONDecodeError:
                            continue

                        # Extract content from Gemini response
                        candidates = chunk_data.get("candidates", [])
                        if not candidates:
                            continue

                        candidate = candidates[0]
                        content = candidate.get("content", {})
                        parts = content.get("parts", [])

                        if parts and parts[0].get("text"):
                            text = parts[0]["text"]

                            # Check if done
                            finish_reason = candidate.get("finishReason")
                            done = finish_reason is not None

                            # Track tokens from usage metadata (only in final chunk)
                            if "usageMetadata" in chunk_data:
                                usage_metadata = chunk_data["usageMetadata"]
                                prompt_tokens = usage_metadata.get("promptTokenCount", 0)
                                completion_tokens = usage_metadata.get("candidatesTokenCount", 0)
                                total_tokens = usage_metadata.get("totalTokenCount", 0)

                            # Yield chunk
                            yield StreamChunk(
                                content=text,
                                done=done,
                                finish_reason=finish_reason
                            )

                            if done:
                                break

            # Calculate cost and bill after streaming completes
            cost = self._calculate_gemini_cost(
                model_id=request.model_id,
                input_tokens=prompt_tokens,
                output_tokens=completion_tokens
            )

            # Deduct from wallet if billing enabled
            if self.enable_billing and not skip_billing and cost > 0:
                transaction_id = await self._bill_user(
                    user_id=user_id,
                    cost=cost,
                    description=f"LLM chat stream - {request.model_id}",
                    metadata={
                        'model_id': request.model_id,
                        'prompt_tokens': prompt_tokens,
                        'completion_tokens': completion_tokens,
                        'total_tokens': total_tokens,
                        'streaming': True,
                        'provider': 'gemini'
                    }
                )
                if transaction_id:
                    logger.info(f"Gemini streaming completed: ${cost:.4f} for user {user_id}, txn={transaction_id}")

        except Exception as e:
            logger.error(f"Gemini streaming failed for model {request.model_id}: {str(e)}")
            raise

    def _calculate_gemini_cost(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Calculate cost for Gemini API usage.

        Pricing (as of 2025):
        - Gemini 2.5 Flash: $0.075/1M input tokens, $0.30/1M output tokens
        - Gemini 2.0 Flash Exp: Free tier available

        Args:
            model_id: Gemini model ID
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        # Gemini 2.5 Flash pricing
        if "2.5-flash" in model_id:
            input_cost_per_m = 0.075  # $0.075 per 1M tokens
            output_cost_per_m = 0.30   # $0.30 per 1M tokens
        # Gemini 2.0 Flash (experimental, free tier)
        elif "2.0-flash" in model_id:
            input_cost_per_m = 0.0
            output_cost_per_m = 0.0
        # Gemini Pro models (higher cost)
        elif "pro" in model_id:
            input_cost_per_m = 0.35
            output_cost_per_m = 1.40
        else:
            # Default to Flash pricing
            input_cost_per_m = 0.075
            output_cost_per_m = 0.30

        input_cost = (input_tokens / 1_000_000) * input_cost_per_m
        output_cost = (output_tokens / 1_000_000) * output_cost_per_m

        return input_cost + output_cost

    async def _bill_user(
        self,
        user_id: str,
        cost: float,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Bill a user for LLM usage.

        Gets or creates the user's wallet and debits the cost.

        Args:
            user_id: User ID
            cost: Cost in USD
            description: Transaction description
            metadata: Additional metadata

        Returns:
            Transaction ID if successful, None otherwise
        """
        if not self.wallet_service or cost <= 0:
            return None

        try:
            from apps.shared.integration.wallet import Currency

            # Get or create wallet for user
            try:
                wallet = await self.wallet_service.get_wallet_by_user(
                    user_id=user_id,
                    currency=Currency.USD,
                    tenant_id="core_backend"
                )
            except Exception:
                # Create wallet if doesn't exist
                wallet = await self.wallet_service.create_wallet(
                    user_id=user_id,
                    currency=Currency.USD,
                    tenant_id="core_backend"
                )

            # Debit from wallet
            transaction = await self.wallet_service.debit(
                wallet_id=wallet.id,
                amount=Decimal(str(cost)),
                description=description,
                metadata=metadata or {},
                allow_negative=True  # Allow negative for LLM usage to not block users
            )

            return transaction.id

        except Exception as e:
            logger.warning(f"Billing failed for user {user_id}: {e}")
            # Don't fail the chat request if billing fails
            return None

    async def chat_stream(
        self,
        user_id: str,
        request: ChatRequest,
        skip_billing: bool = False
    ) -> AsyncIterator[StreamChunk]:
        """
        Streaming chat with LLM model with automatic billing.

        Currently supports Ollama models only.
        Gemini streaming will be added in future update.

        Args:
            user_id: User ID for billing
            request: ChatRequest object (must have stream=True)
            skip_billing: Skip billing (for testing)

        Yields:
            StreamChunk objects

        Raises:
            ValueError: If provider not found or doesn't support streaming
        """
        # Check if Gemini and route to streaming implementation
        if request.model_id.startswith("gemini-"):
            async for chunk in self._chat_stream_with_gemini(
                user_id=user_id,
                request=request,
                skip_billing=skip_billing
            ):
                yield chunk
            return

        # Get provider
        provider = self.provider_registry.get_provider(request.model_id)
        if not provider:
            raise ValueError(f"Model {request.model_id} not found")

        # Check streaming capability
        has_streaming = getattr(provider.capabilities, 'streaming', False)
        if not has_streaming:
            raise ValueError(f"Model {request.model_id} does not support streaming")

        # Track tokens for billing
        total_tokens = 0
        prompt_tokens = 0
        completion_tokens = 0

        try:
            # Get max_tokens from metadata or use default
            default_max_tokens = provider.metadata.get('limits', {}).get('maxOutputTokens', 4096)

            # Call Ollama streaming API
            async for chunk_data in self._call_ollama_chat_stream(
                endpoint=provider.endpoint,
                model_name=provider.model_name,
                messages=request.messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens or default_max_tokens,
                top_p=request.top_p
            ):
                # Extract content
                content = chunk_data.get('message', {}).get('content', '')
                done = chunk_data.get('done', False)

                # Track tokens
                if 'prompt_eval_count' in chunk_data:
                    prompt_tokens = chunk_data['prompt_eval_count']
                if 'eval_count' in chunk_data:
                    completion_tokens = chunk_data['eval_count']

                # Yield chunk
                yield StreamChunk(
                    content=content,
                    done=done,
                    finish_reason=chunk_data.get('done_reason') if done else None
                )

                if done:
                    break

            # Calculate cost and bill after streaming completes
            total_tokens = prompt_tokens + completion_tokens
            cost = self.usage_calculator.calculate_llm_cost(
                input_tokens=prompt_tokens,
                output_tokens=completion_tokens,
                model=request.model_id
            )

            # Deduct from wallet if billing enabled
            if self.enable_billing and not skip_billing and cost > 0:
                transaction_id = await self._bill_user(
                    user_id=user_id,
                    cost=cost,
                    description=f"LLM chat stream - {request.model_id}",
                    metadata={
                        'model_id': request.model_id,
                        'prompt_tokens': prompt_tokens,
                        'completion_tokens': completion_tokens,
                        'total_tokens': total_tokens,
                        'streaming': True
                    }
                )
                if transaction_id:
                    logger.info(f"Streaming chat completed, wallet debited: ${cost:.4f}, txn={transaction_id}")

        except Exception as e:
            logger.error(f"Streaming chat failed for model {request.model_id}: {str(e)}")
            raise

    async def _call_ollama_chat(
        self,
        endpoint: str,
        model_name: str,
        messages: List[ChatMessage],
        temperature: float,
        max_tokens: int,
        top_p: float
    ) -> Dict[str, Any]:
        """
        Call Ollama chat API (non-streaming).

        Args:
            endpoint: Ollama endpoint URL
            model_name: Model name (e.g., "kasaai-llama-twi:v1.0")
            messages: List of ChatMessage objects
            temperature: Temperature
            max_tokens: Max tokens
            top_p: Top-p

        Returns:
            Ollama API response dict
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{endpoint}/api/chat",
                json={
                    'model': model_name,
                    'messages': [{'role': m.role, 'content': m.content} for m in messages],
                    'stream': False,
                    'options': {
                        'temperature': temperature,
                        'num_predict': max_tokens,
                        'top_p': top_p
                    }
                },
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error: {response.status} - {error_text}")

                return await response.json()

    async def _call_ollama_chat_stream(
        self,
        endpoint: str,
        model_name: str,
        messages: List[ChatMessage],
        temperature: float,
        max_tokens: int,
        top_p: float
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Call Ollama chat API (streaming).

        Args:
            endpoint: Ollama endpoint URL
            model_name: Model name
            messages: List of ChatMessage objects
            temperature: Temperature
            max_tokens: Max tokens
            top_p: Top-p

        Yields:
            Ollama API response chunks
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{endpoint}/api/chat",
                json={
                    'model': model_name,
                    'messages': [{'role': m.role, 'content': m.content} for m in messages],
                    'stream': True,
                    'options': {
                        'temperature': temperature,
                        'num_predict': max_tokens,
                        'top_p': top_p
                    }
                },
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama streaming API error: {response.status} - {error_text}")

                # Read streaming response line by line
                async for line in response.content:
                    if line:
                        try:
                            chunk_data = json.loads(line)
                            yield chunk_data
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse streaming chunk: {e}")
                            continue

    async def stop(self):
        """Stop the service (cleanup)."""
        if self.health_monitor:
            await self.health_monitor.stop()
            logger.info("Health monitor stopped")

        self._initialized = False
        logger.info("LLMProviderService stopped")
