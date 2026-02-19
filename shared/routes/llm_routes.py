"""
Unified LLM (Language Model) API Routes

Provides standardized LLM endpoints for all backend applications.
Includes chat completion, streaming, provider management, and cost estimation.

Mount in FastAPI app:
    from apps.shared.routes.llm_routes import router as llm_router
    app.include_router(llm_router, prefix="/api/llm", tags=["LLM"])

Endpoints:
    POST   /chat                - Chat completion with billing
    POST   /chat/stream         - Streaming chat (SSE)
    GET    /providers           - List available LLM providers
    GET    /providers/{id}      - Get provider details
    GET    /models              - List all available models
    POST   /estimate-cost       - Estimate chat cost
    GET    /health              - Health check all providers

Author: KasaAI Team
Date: 2025-11-26
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import json

import sys
sys.path.insert(0, "/opt/kasaai/apps")

from shared.services.llm_provider_service import (
    LLMProviderService,
    ChatRequest as LLMChatRequest,
    ChatMessage,
    ChatResponse as LLMChatResponse,
    CostEstimate,
    ProviderHealth,
)
from apps.shared.integration.ai_services.provider_registry import (
    get_global_registry,
    get_default_llm_providers_config,
    ProviderType,
)

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Singleton service instance
_llm_service: Optional[LLMProviderService] = None


async def get_llm_service() -> LLMProviderService:
    """Get or create singleton LLM service instance."""
    global _llm_service
    if _llm_service is None:
        # Ensure registry has LLM providers initialized before creating service
        registry = get_global_registry()
        if not registry.get_llm_providers():
            llm_config = get_default_llm_providers_config()
            registry.register_providers_from_config(llm_config, provider_type=ProviderType.LLM)
            logger.info(f"Registered {len(llm_config)} LLM providers")

        _llm_service = LLMProviderService(
            enable_billing=True,
            enable_health_monitoring=True
        )
        await _llm_service.initialize()
    return _llm_service


# ============================================================================
# Request/Response Models
# ============================================================================

class MessageInput(BaseModel):
    """Chat message in request."""
    role: str = Field(..., description="Message role: 'system', 'user', or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request model for chat completion."""
    model_id: str = Field(
        default="gemini-2.5-flash",
        description="LLM model ID. Default: gemini-2.5-flash"
    )
    messages: List[MessageInput] = Field(..., description="Conversation messages")
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0-2.0). Lower = more deterministic."
    )
    max_tokens: Optional[int] = Field(
        None,
        description="Maximum tokens to generate. None = model default."
    )
    top_p: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Top-p sampling (0.0-1.0)"
    )
    system_prompt: Optional[str] = Field(
        None,
        description="System prompt (prepended to messages)"
    )
    stream: bool = Field(
        default=False,
        description="Enable streaming response"
    )


class ChatResponseModel(BaseModel):
    """Response model for chat completion."""
    message: str = Field(..., description="Assistant response")
    model_id: str = Field(..., description="Model used")
    usage: Dict[str, int] = Field(..., description="Token usage statistics")
    finish_reason: str = Field(..., description="Completion finish reason")
    cost: float = Field(..., description="Cost in USD")
    transaction_id: Optional[str] = Field(None, description="Billing transaction ID")
    processing_time: float = Field(..., description="Processing time in seconds")


class CostEstimateRequest(BaseModel):
    """Request model for cost estimation."""
    model_id: str = Field(
        default="gemini-2.5-flash",
        description="LLM model ID"
    )
    input_tokens: Optional[int] = Field(
        None, description="Number of input tokens (for accurate estimate)"
    )
    messages: Optional[List[MessageInput]] = Field(
        None, description="Messages to estimate (alternative to input_tokens)"
    )
    estimated_output_tokens: int = Field(
        default=500,
        description="Estimated output tokens"
    )


class CostEstimateResponse(BaseModel):
    """Response model for cost estimation."""
    model_id: str
    input_tokens: int
    estimated_output_tokens: int
    input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float
    pricing_note: str


class LLMProviderInfo(BaseModel):
    """Provider information for LLM."""
    id: str
    name: str
    endpoint: str
    status: str
    capabilities: Dict[str, bool]
    description: str
    context_length: Optional[int] = None
    is_default: bool = False


class ProvidersResponse(BaseModel):
    """Response for provider listing."""
    providers: Dict[str, LLMProviderInfo]
    count: int
    default_provider: str
    timestamp: str


# ============================================================================
# Authentication Helper
# ============================================================================

async def get_user_id_from_header(authorization: str = Header(None)) -> Optional[str]:
    """
    Extract user ID from JWT token for billing.

    Falls back to anonymous if no valid token provided.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.replace("Bearer ", "")

    try:
        import jwt
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("sub") or decoded.get("user_id")
    except Exception:
        return None


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/chat", response_model=ChatResponseModel)
async def chat_completion(
    request: ChatRequest,
    authorization: str = Header(None),
    skip_billing: bool = Query(
        default=False,
        description="Skip wallet billing (for testing/free tier)"
    ),
):
    """
    Chat with LLM model.

    Supports multiple providers:
    - Gemini models (gemini-2.5-flash, gemini-2.0-flash-exp, etc.)
    - Ollama models (local inference)

    Default model: gemini-2.5-flash (fast, cost-effective, culturally aware)

    Note: For streaming responses, use /chat/stream endpoint instead.
    """
    try:
        # Check if streaming requested
        if request.stream:
            raise HTTPException(
                status_code=400,
                detail="For streaming, use POST /chat/stream endpoint"
            )

        # Get user ID for billing
        user_id = await get_user_id_from_header(authorization)
        if not user_id:
            user_id = "anonymous"
            skip_billing = True

        # Get LLM service
        llm_service = await get_llm_service()

        # Convert messages
        messages = [
            ChatMessage(role=m.role, content=m.content)
            for m in request.messages
        ]

        # Create LLM request
        llm_request = LLMChatRequest(
            model_id=request.model_id,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            system_prompt=request.system_prompt,
            stream=False
        )

        # Chat
        result = await llm_service.chat(
            user_id=user_id,
            request=llm_request,
            skip_billing=skip_billing
        )

        return ChatResponseModel(
            message=result.message,
            model_id=result.model_id,
            usage=result.usage,
            finish_reason=result.finish_reason,
            cost=result.cost,
            transaction_id=result.transaction_id,
            processing_time=result.processing_time
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    authorization: str = Header(None),
    skip_billing: bool = Query(default=False),
):
    """
    Streaming chat with LLM model.

    Returns Server-Sent Events (SSE) stream.

    Currently supports:
    - Ollama models (streaming)

    Note: Gemini streaming is not yet supported. Use non-streaming /chat endpoint.
    """
    try:
        # Get user ID for billing
        user_id = await get_user_id_from_header(authorization)
        if not user_id:
            user_id = "anonymous"
            skip_billing = True

        # Get LLM service
        llm_service = await get_llm_service()

        # Convert messages
        messages = [
            ChatMessage(role=m.role, content=m.content)
            for m in request.messages
        ]

        # Create LLM request
        llm_request = LLMChatRequest(
            model_id=request.model_id,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            system_prompt=request.system_prompt,
            stream=True
        )

        async def generate_sse():
            """Generate SSE events from stream."""
            try:
                async for chunk in llm_service.chat_stream(
                    user_id=user_id,
                    request=llm_request,
                    skip_billing=skip_billing
                ):
                    # Format as SSE
                    data = json.dumps({
                        "content": chunk.content,
                        "done": chunk.done,
                        "finish_reason": chunk.finish_reason
                    })
                    yield f"data: {data}\n\n"

                # Send final event
                yield f"data: [DONE]\n\n"

            except ValueError as e:
                # Handle Gemini streaming not supported
                error_data = json.dumps({"error": str(e)})
                yield f"data: {error_data}\n\n"
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                error_data = json.dumps({"error": str(e)})
                yield f"data: {error_data}\n\n"

        return StreamingResponse(
            generate_sse(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Stream setup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers", response_model=ProvidersResponse)
async def list_llm_providers(
    online_only: bool = Query(
        default=False,
        description="Filter to show only online providers"
    ),
):
    """
    List all available LLM providers.

    Returns provider info including:
    - Model capabilities (streaming, reasoning, etc.)
    - Context length
    - Current status
    - Default provider marker
    """
    try:
        # Ensure registry has LLM providers initialized
        registry = get_global_registry()
        if not registry.get_llm_providers():
            llm_config = get_default_llm_providers_config()
            registry.register_providers_from_config(llm_config, provider_type=ProviderType.LLM)

        # Get LLM service for health status
        llm_service = await get_llm_service()
        providers_data = await llm_service.get_available_providers()

        # Build provider list
        providers = {}
        llm_providers = registry.get_llm_providers()

        for provider in llm_providers:
            # Get status from service cache if available
            status = "unknown"
            if provider.id in providers_data:
                health = providers_data[provider.id].get("health", {})
                status = health.get("status", "unknown")

            # Skip offline providers if online_only
            if online_only and status != "online":
                continue

            # Extract capabilities
            capabilities = {}
            if provider.capabilities:
                caps = provider.capabilities
                capabilities = {
                    "multiLanguage": getattr(caps, "multiLanguage", False),
                    "streaming": getattr(caps, "streaming", False),
                    "reasoning": getattr(caps, "reasoning", False),
                    "codeGeneration": getattr(caps, "codeGeneration", False),
                    "functionCalling": getattr(caps, "functionCalling", False),
                    "vision": getattr(caps, "vision", False),
                    "culturalContext": getattr(caps, "culturalContext", False),
                    "longContext": getattr(caps, "longContext", False),
                }
                capabilities = {k: v for k, v in capabilities.items() if v}

            providers[provider.id] = LLMProviderInfo(
                id=provider.id,
                name=provider.name,
                endpoint=provider.endpoint,
                status=status,
                capabilities=capabilities,
                description=provider.description or "",
                context_length=getattr(provider, "max_tokens", None),
                is_default=provider.id == "gemini-2.5-flash",
            )

        return ProvidersResponse(
            providers=providers,
            count=len(providers),
            default_provider="gemini-2.5-flash",
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"Error listing LLM providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers/{provider_id}")
async def get_llm_provider(provider_id: str):
    """
    Get details for a specific LLM provider.

    Returns detailed capabilities, context length, and current status.
    """
    try:
        registry = get_global_registry()
        provider = registry.get_provider(provider_id)

        if not provider:
            raise HTTPException(
                status_code=404,
                detail=f"LLM provider not found: {provider_id}"
            )

        # Get health status
        llm_service = await get_llm_service()
        try:
            health = await llm_service.get_provider_health(provider_id)
            status = health.status
            response_time = health.response_time_ms
        except Exception:
            status = "unknown"
            response_time = None

        # Extract capabilities
        capabilities = {}
        if provider.capabilities:
            caps = provider.capabilities
            capabilities = {
                "multiLanguage": getattr(caps, "multiLanguage", False),
                "streaming": getattr(caps, "streaming", False),
                "reasoning": getattr(caps, "reasoning", False),
                "codeGeneration": getattr(caps, "codeGeneration", False),
                "functionCalling": getattr(caps, "functionCalling", False),
                "vision": getattr(caps, "vision", False),
                "culturalContext": getattr(caps, "culturalContext", False),
                "longContext": getattr(caps, "longContext", False),
            }

        return {
            "id": provider.id,
            "name": provider.name,
            "endpoint": provider.endpoint,
            "status": status,
            "capabilities": capabilities,
            "description": provider.description or "",
            "model_name": getattr(provider, "model_name", None),
            "context_length": getattr(provider, "max_tokens", None),
            "is_default": provider_id == "gemini-2.5-flash",
            "response_time_ms": response_time,
            "provider_type": "gemini" if provider_id.startswith("gemini-") else "ollama",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting LLM provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def list_models():
    """
    List all available LLM models.

    Simplified view of available models for frontend dropdowns.
    """
    try:
        registry = get_global_registry()
        llm_providers = registry.get_llm_providers()

        models = []
        for provider in llm_providers:
            models.append({
                "id": provider.id,
                "name": provider.name,
                "description": provider.description or "",
                "is_default": provider.id == "gemini-2.5-flash",
                "provider_type": "gemini" if provider.id.startswith("gemini-") else "ollama",
            })

        return {
            "models": models,
            "count": len(models),
            "default_model": "gemini-2.5-flash",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/estimate-cost", response_model=CostEstimateResponse)
async def estimate_chat_cost(request: CostEstimateRequest):
    """
    Estimate chat cost before processing.

    Provide either:
    - input_tokens: Known token count for direct calculation
    - messages: Conversation to estimate (tokens will be approximated)

    Pricing varies by model:
    - Gemini 2.5 Flash: $0.075/1M input, $0.30/1M output
    - Gemini 2.0 Flash Exp: Free tier
    - Ollama models: Local inference, minimal cost
    """
    try:
        # Calculate input tokens
        if request.input_tokens:
            input_tokens = request.input_tokens
        elif request.messages:
            # Estimate tokens from messages (rough: 4 chars = 1 token)
            total_chars = sum(len(m.content) for m in request.messages)
            input_tokens = max(total_chars // 4, 1)
        else:
            raise HTTPException(
                status_code=400,
                detail="Provide either input_tokens or messages"
            )

        # Calculate cost based on model (inline pricing calculation)
        # This avoids dependency on provider registry for cost estimation
        model_id = request.model_id
        estimated_output = request.estimated_output_tokens

        # Gemini pricing (per 1M tokens)
        if "2.5-flash" in model_id:
            input_cost_per_m = 0.075
            output_cost_per_m = 0.30
            pricing_note = "Gemini 2.5 Flash - fast, cost-effective"
        elif "2.0-flash" in model_id:
            input_cost_per_m = 0.0
            output_cost_per_m = 0.0
            pricing_note = "Gemini 2.0 Flash Exp - free tier available"
        elif "pro" in model_id:
            input_cost_per_m = 0.35
            output_cost_per_m = 1.40
            pricing_note = "Gemini Pro - higher capability, higher cost"
        elif model_id.startswith("gemini-"):
            input_cost_per_m = 0.075
            output_cost_per_m = 0.30
            pricing_note = "Gemini - cloud inference"
        else:
            # Ollama/local models - minimal cost
            input_cost_per_m = 0.001  # $0.001 per 1M tokens
            output_cost_per_m = 0.001
            pricing_note = "Ollama - local inference, minimal cost"

        input_cost = (input_tokens / 1_000_000) * input_cost_per_m
        output_cost = (estimated_output / 1_000_000) * output_cost_per_m
        total_cost = input_cost + output_cost

        return CostEstimateResponse(
            model_id=model_id,
            input_tokens=input_tokens,
            estimated_output_tokens=estimated_output,
            input_cost_usd=input_cost,
            output_cost_usd=output_cost,
            total_cost_usd=total_cost,
            pricing_note=pricing_note,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cost estimation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def check_llm_health():
    """
    Health check for all LLM providers.

    Returns status summary for monitoring and alerting.
    """
    try:
        llm_service = await get_llm_service()
        providers_data = await llm_service.refresh_providers(force=True)

        online_count = 0
        offline_count = 0
        providers_status = {}

        for provider_id, provider_info in providers_data.items():
            health = provider_info.get("health", {})
            status = health.get("status", "unknown")

            if status == "online":
                online_count += 1
            else:
                offline_count += 1

            providers_status[provider_id] = {
                "status": status,
                "response_time_ms": health.get("response_time_ms"),
                "error": health.get("error"),
            }

        return {
            "status": "healthy" if online_count > 0 else "degraded",
            "total_providers": len(providers_data),
            "online": online_count,
            "offline": offline_count,
            "providers": providers_status,
            "default_provider": "gemini-2.5-flash",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


# ============================================================================
# Initialization Helper
# ============================================================================

def initialize_llm_routes():
    """
    Initialize LLM routes on app startup.

    Call this from your app's startup event to pre-warm the LLM service.
    """
    logger.info("LLM routes initialized")
