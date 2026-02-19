"""
LLM Services Routes

Provides API endpoints for LLM Lab interface with automatic billing and health monitoring.

Enhanced with:
- Custom error classes for user-friendly error messages
- Tier-based rate limiting (free, starter, pro, enterprise)
- Prompt validation (unsafe content detection, token estimation)
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Request, Response, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, AsyncIterator
from datetime import datetime
import logging
import json

from apps.shared.services.llm_provider_service import (
    LLMProviderService,
    ChatRequest,
    ChatMessage,
)
from apps.shared.services.prompt_validation_service import get_validation_service
from ..auth import get_current_user_mongo
from ..middleware.rate_limiting import get_llm_rate_limit
from ..services.chat_history_service import (
    get_chat_history_service,
    ChatHistoryService,
)
from ..exceptions.llm_errors import (
    LLMError,
    InsufficientBalanceError,
    PromptTooLongError,
    InvalidModelError,
    RateLimitExceededError,
    ModelOfflineError,
    UnsafeContentError,
    GenerationTimeoutError,
    InvalidTemperatureError,
    MaxTokensExceededError,
    map_exception_to_llm_error
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/llm", tags=["LLM Services"])


# ============================================================================
# Pydantic Models
# ============================================================================

class ChatRequestAPI(BaseModel):
    """Chat request from API."""
    model_id: str = Field(..., description="LLM model ID")
    messages: List[ChatMessage] = Field(..., description="Conversation messages")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    stream: bool = Field(False, description="Enable streaming response")
    system_prompt: Optional[str] = Field(None, description="System prompt override")


class ChatResponseAPI(BaseModel):
    """Chat response from API."""
    message: str = Field(..., description="Generated message")
    model_id: str = Field(..., description="Model used")
    usage: Dict[str, int] = Field(..., description="Token usage")
    finish_reason: str = Field(..., description="Completion reason")
    cost: float = Field(..., description="Cost in USD")
    transaction_id: Optional[str] = Field(None, description="Transaction ID")
    processing_time: float = Field(..., description="Processing time in seconds")


class CostEstimateRequest(BaseModel):
    """Request for cost estimation."""
    model_id: str
    input_text: str


class CostEstimateResponse(BaseModel):
    """Cost estimation response."""
    estimated_cost: float
    estimated_tokens: int
    model_id: str


# ============================================================================
# API Routes
# ============================================================================

@router.post("/chat", response_model=ChatResponseAPI)
async def chat(
    request: ChatRequestAPI,
    req: Request,
    response: Response,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_llm_rate_limit("chat", "free"))
):
    """
    Chat with LLM model (non-streaming).

    Automatically deducts cost from user wallet.
    Includes rate limiting, prompt validation, and error handling.

    Args:
        request: Chat request with model, messages, and parameters
        req: FastAPI request object
        response: FastAPI response object
        user: Current authenticated user
        rate_limit: Rate limiting check

    Returns:
        ChatResponseAPI: Generated response with cost and transaction info

    Raises:
        LLMError: Custom error with user-friendly message
    """
    try:
        # Step 1: Validate prompt
        validation_service = get_validation_service()
        validation_result = await validation_service.validate_prompt(
            messages=request.messages,
            model_id=request.model_id,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            check_unsafe_content=True
        )

        if not validation_result.valid:
            # Determine error type based on validation errors
            error_messages = validation_result.errors
            if any("unsafe" in err.lower() or "jailbreak" in err.lower() for err in error_messages):
                raise UnsafeContentError(
                    message="; ".join(error_messages),
                    detected_pattern="Multiple unsafe patterns"
                )
            elif any("token" in err.lower() and "exceed" in err.lower() for err in error_messages):
                raise PromptTooLongError(
                    message="; ".join(error_messages),
                    estimated_tokens=validation_result.estimated_tokens
                )
            elif any("temperature" in err.lower() for err in error_messages):
                raise InvalidTemperatureError(
                    message="; ".join(error_messages),
                    provided_temperature=request.temperature
                )
            elif any("max_tokens" in err.lower() for err in error_messages):
                raise MaxTokensExceededError(message="; ".join(error_messages))
            else:
                raise LLMError(message=f"Prompt validation failed: {'; '.join(error_messages)}")

        # Step 2: Get LLM service
        llm_service: LLMProviderService = await get_llm_service()

        # Step 3: Create internal chat request
        chat_request = ChatRequest(
            model_id=request.model_id,
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            stream=False,
            system_prompt=request.system_prompt
        )

        # Step 4: Call service (with billing)
        result = await llm_service.chat(
            user_id=user["id"],
            request=chat_request,
            skip_billing=False
        )

        logger.info(
            f"LLM chat completed: user={user['id']}, model={request.model_id}, "
            f"tokens={result.usage['total_tokens']}, cost=${result.cost:.4f}"
        )

        # Save to chat history (non-blocking)
        try:
            history_service: ChatHistoryService = get_chat_history_service()
            await history_service.add_to_history(
                user_id=user["id"],
                model_id=result.model_id,
                messages=request.messages,
                response=result.message,
                usage=result.usage,
                cost=result.cost,
                processing_time=result.processing_time,
                conversation_id=None  # No conversation threading for now
            )
        except Exception as hist_error:
            # Non-blocking: don't fail request if history save fails
            logger.warning(f"Failed to save chat history: {hist_error}")

        return ChatResponseAPI(
            message=result.message,
            model_id=result.model_id,
            usage=result.usage,
            finish_reason=result.finish_reason,
            cost=result.cost,
            transaction_id=result.transaction_id,
            processing_time=result.processing_time
        )

    except LLMError as e:
        # Already a custom error - re-raise as HTTPException
        logger.warning(f"LLM error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    except ValueError as e:
        # Map generic ValueError to LLM error
        llm_error = map_exception_to_llm_error(e)
        logger.error(f"LLM chat validation error: {e}")
        raise HTTPException(status_code=llm_error.status_code, detail=llm_error.to_dict())
    except Exception as e:
        # Map unknown exception to generic LLM error
        llm_error = map_exception_to_llm_error(e)
        logger.error(f"LLM chat error: {e}")
        raise HTTPException(status_code=llm_error.status_code, detail=llm_error.to_dict())


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequestAPI,
    req: Request,
    response: Response,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_llm_rate_limit("chat_stream", "free"))
):
    """
    Chat with LLM model (streaming).

    Streams tokens as they're generated. Billing occurs after stream completes.
    Includes rate limiting, prompt validation, and error handling.

    Args:
        request: Chat request with model, messages, and parameters
        req: FastAPI request object
        response: FastAPI response object
        user: Current authenticated user
        rate_limit: Rate limiting check

    Returns:
        StreamingResponse: SSE stream of tokens

    Raises:
        LLMError: Custom error with user-friendly message
    """
    try:
        # Step 1: Validate prompt
        validation_service = get_validation_service()
        validation_result = await validation_service.validate_prompt(
            messages=request.messages,
            model_id=request.model_id,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            check_unsafe_content=True
        )

        if not validation_result.valid:
            # Map validation errors to appropriate exceptions
            error_messages = validation_result.errors
            if any("unsafe" in err.lower() or "jailbreak" in err.lower() for err in error_messages):
                raise UnsafeContentError(message="; ".join(error_messages))
            elif any("token" in err.lower() and "exceed" in err.lower() for err in error_messages):
                raise PromptTooLongError(
                    message="; ".join(error_messages),
                    estimated_tokens=validation_result.estimated_tokens
                )
            else:
                raise LLMError(message=f"Prompt validation failed: {'; '.join(error_messages)}")

        # Step 2: Get LLM service
        llm_service: LLMProviderService = await get_llm_service()

        # Step 3: Create internal chat request
        chat_request = ChatRequest(
            model_id=request.model_id,
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            stream=True,
            system_prompt=request.system_prompt
        )

        async def stream_generator() -> AsyncIterator[str]:
            """Generate SSE stream."""
            full_response = ""
            usage_info = {}
            cost = 0.0
            processing_time = 0.0
            start_time = None

            try:
                from datetime import datetime
                start_time = datetime.utcnow()

                async for chunk in llm_service.chat_stream(
                    user_id=user["id"],
                    request=chat_request,
                    skip_billing=False
                ):
                    # Collect response content
                    full_response += chunk.content

                    # Collect metadata from final chunk
                    if chunk.done and hasattr(chunk, 'usage'):
                        usage_info = chunk.usage
                        cost = getattr(chunk, 'cost', 0.0)

                    # Format as SSE
                    data = {
                        "content": chunk.content,
                        "done": chunk.done
                    }
                    yield f"data: {json.dumps(data)}\n\n"

                    if chunk.done:
                        break

                # Calculate processing time
                if start_time:
                    processing_time = (datetime.utcnow() - start_time).total_seconds()

                # Save to chat history (non-blocking)
                try:
                    history_service: ChatHistoryService = get_chat_history_service()
                    await history_service.add_to_history(
                        user_id=user["id"],
                        model_id=request.model_id,
                        messages=request.messages,
                        response=full_response,
                        usage=usage_info,
                        cost=cost,
                        processing_time=processing_time,
                        conversation_id=None  # No conversation threading for now
                    )
                except Exception as hist_error:
                    # Non-blocking: don't fail stream if history save fails
                    logger.warning(f"Failed to save streamed chat history: {hist_error}")

            except Exception as e:
                logger.error(f"Stream error: {e}")
                # Map to LLM error and send as error event
                llm_error = map_exception_to_llm_error(e)
                error_data = {
                    "error": llm_error.to_dict(),
                    "done": True
                }
                yield f"data: {json.dumps(error_data)}\n\n"

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except LLMError as e:
        logger.warning(f"LLM stream validation error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    except ValueError as e:
        llm_error = map_exception_to_llm_error(e)
        logger.error(f"LLM stream validation error: {e}")
        raise HTTPException(status_code=llm_error.status_code, detail=llm_error.to_dict())
    except Exception as e:
        llm_error = map_exception_to_llm_error(e)
        logger.error(f"LLM stream error: {e}")
        raise HTTPException(status_code=llm_error.status_code, detail=llm_error.to_dict())


@router.post("/estimate-cost", response_model=CostEstimateResponse)
async def estimate_cost(
    request: CostEstimateRequest,
    req: Request,
    response: Response,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_llm_rate_limit("estimate", "free"))
):
    """
    Estimate cost of LLM inference before running.

    Includes rate limiting and error handling.

    Args:
        request: Cost estimation request
        req: FastAPI request object
        response: FastAPI response object
        user: Current authenticated user
        rate_limit: Rate limiting check

    Returns:
        CostEstimateResponse: Estimated cost and token count

    Raises:
        LLMError: Custom error with user-friendly message
    """
    try:
        # Get validation service for token estimation
        validation_service = get_validation_service()
        estimated_tokens = validation_service.estimate_tokens(request.input_text)

        # Get LLM service
        llm_service: LLMProviderService = await get_llm_service()

        # Get cost estimate
        estimated_cost = await llm_service.estimate_cost(
            model_id=request.model_id,
            input_tokens=estimated_tokens,
            estimated_output_tokens=1000  # Default assumption
        )

        return CostEstimateResponse(
            estimated_cost=estimated_cost.total_cost,
            estimated_tokens=estimated_tokens,
            model_id=request.model_id
        )

    except ValueError as e:
        llm_error = map_exception_to_llm_error(e)
        logger.error(f"Cost estimation validation error: {e}")
        raise HTTPException(status_code=llm_error.status_code, detail=llm_error.to_dict())
    except Exception as e:
        llm_error = map_exception_to_llm_error(e)
        logger.error(f"Cost estimation error: {e}")
        raise HTTPException(status_code=llm_error.status_code, detail=llm_error.to_dict())


@router.get("/providers")
async def list_providers(
    req: Request,
    response: Response,
    force_refresh: bool = Query(False, description="Force health check refresh"),
    rate_limit: None = Depends(get_llm_rate_limit("info", "free"))
) -> Dict:
    """
    List all available LLM providers with real-time status.

    Includes rate limiting and error handling.

    Args:
        req: FastAPI request object
        response: FastAPI response object
        force_refresh: Force health check even if cached (default: False)
        rate_limit: Rate limiting check

    Returns:
        dict: LLM providers with dynamic status and capabilities

    Raises:
        LLMError: Custom error with user-friendly message
    """
    try:
        # Get LLM service
        llm_service: LLMProviderService = await get_llm_service()

        # Get all available providers with health status
        providers_dict = await llm_service.get_available_providers()

        # Calculate status counts
        online_count = 0
        offline_count = 0
        degraded_count = 0

        for provider_id, provider_info in providers_dict.items():
            health = provider_info.get("health", {})
            status = health.get("status", "unknown")

            if status == "online":
                online_count += 1
            elif status == "offline":
                offline_count += 1
            elif status == "degraded":
                degraded_count += 1

        return {
            "providers": providers_dict,
            "count": len(providers_dict),
            "online_count": online_count,
            "offline_count": offline_count,
            "degraded_count": degraded_count,
        }

    except Exception as e:
        llm_error = map_exception_to_llm_error(e)
        logger.error(f"Error listing LLM providers: {str(e)}")
        raise HTTPException(status_code=llm_error.status_code, detail=llm_error.to_dict())


@router.get("/providers/{provider_id}")
async def get_provider(
    provider_id: str,
    req: Request,
    response: Response,
    rate_limit: None = Depends(get_llm_rate_limit("info", "free"))
) -> Dict:
    """
    Get status of a specific LLM provider.

    Includes rate limiting and error handling.

    Args:
        provider_id: Provider identifier (e.g., 'kasaai_llama_twi', 'llama_32_3b')
        req: FastAPI request object
        response: FastAPI response object
        rate_limit: Rate limiting check

    Returns:
        dict: Provider details with current status

    Raises:
        LLMError: Custom error with user-friendly message
    """
    try:
        # Get LLM service
        llm_service: LLMProviderService = await get_llm_service()

        # Get provider health
        health = await llm_service.get_provider_health(provider_id)

        return {
            "id": health.provider_id,
            "name": health.provider_id.replace("_", " ").title(),
            "endpoint": health.endpoint,
            "status": health.status,
            "last_check": health.last_check.isoformat(),
            "response_time_ms": health.response_time_ms,
            "error_message": health.error_message,
            "provider_type": "llm"
        }

    except ValueError as e:
        # Model not found
        raise HTTPException(
            status_code=404,
            detail=InvalidModelError(
                message=f"Provider {provider_id} not found",
                model_id=provider_id
            ).to_dict()
        )
    except Exception as e:
        llm_error = map_exception_to_llm_error(e)
        logger.error(f"Error getting LLM provider {provider_id}: {str(e)}")
        raise HTTPException(status_code=llm_error.status_code, detail=llm_error.to_dict())


@router.get("/health")
async def health_check() -> Dict:
    """
    Health check for LLM services route.

    Returns:
        dict: Health status
    """
    try:
        # Get LLM service
        llm_service: LLMProviderService = await get_llm_service()

        # Get provider count
        providers = await llm_service.get_available_providers()

        return {
            "status": "healthy",
            "service": "llm-services",
            "providers_count": len(providers),
            "billing_enabled": llm_service.enable_billing,
            "health_monitoring_enabled": llm_service.enable_health_monitoring,
        }

    except Exception as e:
        logger.error(f"LLM health check error: {e}")
        return {
            "status": "unhealthy",
            "service": "llm-services",
            "error": str(e)
        }


# ============================================================================
# Chat History Endpoints
# ============================================================================

@router.get("/history")
async def list_chat_history(
    req: Request,
    response: Response,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_llm_rate_limit("info", "free")),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search text"),
    model_filter: Optional[str] = Query(None, description="Filter by model ID"),
    conversation_id: Optional[str] = Query(None, description="Filter by conversation ID")
) -> Dict:
    """
    List user's chat history with pagination and filters.

    Includes rate limiting and error handling.

    Args:
        req: FastAPI request object
        response: FastAPI response object
        user: Current authenticated user
        rate_limit: Rate limiting check
        page: Page number (default: 1)
        limit: Items per page (default: 20, max: 100)
        search: Full-text search query
        model_filter: Filter by model ID
        conversation_id: Filter by conversation ID

    Returns:
        dict: Paginated chat history with metadata

    Raises:
        LLMError: Custom error with user-friendly message
    """
    try:
        # Get history service
        history_service: ChatHistoryService = get_chat_history_service()

        # Get paginated history
        result = await history_service.get_user_history(
            user_id=user["id"],
            page=page,
            limit=limit,
            search_text=search,
            model_filter=model_filter,
            conversation_id=conversation_id
        )

        return {
            "items": [item.dict() for item in result.items],
            "total": result.total,
            "page": result.page,
            "limit": result.limit,
            "has_more": result.has_more
        }

    except Exception as e:
        llm_error = map_exception_to_llm_error(e)
        logger.error(f"Error listing chat history: {str(e)}")
        raise HTTPException(status_code=llm_error.status_code, detail=llm_error.to_dict())


@router.get("/history/{item_id}")
async def get_chat_history_item(
    item_id: str,
    req: Request,
    response: Response,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_llm_rate_limit("info", "free"))
) -> Dict:
    """
    Get specific chat history item with full details.

    Includes rate limiting and error handling.

    Args:
        item_id: Chat history item ID
        req: FastAPI request object
        response: FastAPI response object
        user: Current authenticated user
        rate_limit: Rate limiting check

    Returns:
        dict: Chat history item with full message content

    Raises:
        LLMError: Custom error with user-friendly message
    """
    try:
        # Get history service
        history_service: ChatHistoryService = get_chat_history_service()

        # Get specific item
        item = await history_service.get_history_item(
            user_id=user["id"],
            item_id=item_id
        )

        if not item:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "HISTORY_NOT_FOUND",
                    "message": "Chat history item not found",
                    "status_code": 404
                }
            )

        return item.dict()

    except HTTPException:
        raise
    except Exception as e:
        llm_error = map_exception_to_llm_error(e)
        logger.error(f"Error getting chat history item {item_id}: {str(e)}")
        raise HTTPException(status_code=llm_error.status_code, detail=llm_error.to_dict())


@router.get("/conversations/{conversation_id}")
async def get_conversation_thread(
    conversation_id: str,
    req: Request,
    response: Response,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_llm_rate_limit("info", "free"))
) -> Dict:
    """
    Get all messages in a conversation thread.

    Includes rate limiting and error handling.

    Args:
        conversation_id: Conversation thread ID
        req: FastAPI request object
        response: FastAPI response object
        user: Current authenticated user
        rate_limit: Rate limiting check

    Returns:
        dict: List of chat history items in conversation order

    Raises:
        LLMError: Custom error with user-friendly message
    """
    try:
        # Get history service
        history_service: ChatHistoryService = get_chat_history_service()

        # Get conversation thread
        items = await history_service.get_conversation_history(
            user_id=user["id"],
            conversation_id=conversation_id
        )

        return {
            "conversation_id": conversation_id,
            "items": [item.dict() for item in items],
            "count": len(items)
        }

    except Exception as e:
        llm_error = map_exception_to_llm_error(e)
        logger.error(f"Error getting conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=llm_error.status_code, detail=llm_error.to_dict())


@router.delete("/history/{item_id}")
async def delete_chat_history_item(
    item_id: str,
    req: Request,
    response: Response,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_llm_rate_limit("info", "free"))
) -> Dict:
    """
    Soft delete a chat history item.

    Includes rate limiting and error handling.

    Args:
        item_id: Chat history item ID
        req: FastAPI request object
        response: FastAPI response object
        user: Current authenticated user
        rate_limit: Rate limiting check

    Returns:
        dict: Success status

    Raises:
        LLMError: Custom error with user-friendly message
    """
    try:
        # Get history service
        history_service: ChatHistoryService = get_chat_history_service()

        # Soft delete item
        success = await history_service.delete_history_item(
            user_id=user["id"],
            item_id=item_id
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "HISTORY_NOT_FOUND",
                    "message": "Chat history item not found or already deleted",
                    "status_code": 404
                }
            )

        return {
            "success": True,
            "message": "Chat history item deleted successfully",
            "item_id": item_id
        }

    except HTTPException:
        raise
    except Exception as e:
        llm_error = map_exception_to_llm_error(e)
        logger.error(f"Error deleting chat history item {item_id}: {str(e)}")
        raise HTTPException(status_code=llm_error.status_code, detail=llm_error.to_dict())


@router.get("/history/stats")
async def get_chat_statistics(
    req: Request,
    response: Response,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_llm_rate_limit("info", "free")),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
) -> Dict:
    """
    Get aggregated chat statistics for the user.

    Includes rate limiting and error handling.

    Args:
        req: FastAPI request object
        response: FastAPI response object
        user: Current authenticated user
        rate_limit: Rate limiting check
        days: Number of days to analyze (default: 30, max: 365)

    Returns:
        dict: User statistics with chat counts, costs, tokens, etc.

    Raises:
        LLMError: Custom error with user-friendly message
    """
    try:
        # Get history service
        history_service: ChatHistoryService = get_chat_history_service()

        # Get statistics
        stats = await history_service.get_user_statistics(
            user_id=user["id"],
            days=days
        )

        return stats.dict()

    except Exception as e:
        llm_error = map_exception_to_llm_error(e)
        logger.error(f"Error getting chat statistics: {str(e)}")
        raise HTTPException(status_code=llm_error.status_code, detail=llm_error.to_dict())


# ============================================================================
# Sample Prompts Endpoints
# ============================================================================

@router.get("/prompts/categories")
async def list_prompt_categories(
    req: Request,
    response: Response,
    rate_limit: None = Depends(get_llm_rate_limit("info", "free"))
) -> Dict:
    """
    List all prompt categories with metadata.

    Returns all available prompt categories from the prompts library,
    including category info and prompt counts.

    Args:
        req: FastAPI request object
        response: FastAPI response object
        rate_limit: Rate limiting check

    Returns:
        dict: List of categories with metadata

    Raises:
        HTTPException: If prompts library cannot be loaded
    """
    try:
        import json
        import os

        # Load prompts library
        prompts_file = os.path.join(
            os.path.dirname(__file__),
            "../../voice-lab/llm_samples/prompts_library.json"
        )

        # Try alternative path if first doesn't work
        if not os.path.exists(prompts_file):
            prompts_file = "/opt/kasaai/apps/voice-lab/llm_samples/prompts_library.json"

        with open(prompts_file, 'r') as f:
            library = json.load(f)

        categories = library.get("categories", [])

        return {
            "categories": categories,
            "total_categories": len(categories),
            "total_prompts": library.get("metadata", {}).get("total_prompts", 0),
            "version": library.get("version", "1.0.0")
        }

    except FileNotFoundError:
        logger.error("Prompts library file not found")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "PROMPTS_LIBRARY_NOT_FOUND",
                "message": "Sample prompts library not found. Please ensure the prompts file exists.",
                "status_code": 404
            }
        )
    except Exception as e:
        logger.error(f"Error loading prompt categories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "PROMPTS_LOAD_ERROR",
                "message": f"Failed to load prompt categories: {str(e)}",
                "status_code": 500
            }
        )


@router.get("/prompts/{category_id}")
async def get_category_prompts(
    category_id: str,
    req: Request,
    response: Response,
    rate_limit: None = Depends(get_llm_rate_limit("info", "free"))
) -> Dict:
    """
    Get all prompts in a specific category.

    Returns all prompts belonging to the specified category,
    including full metadata and prompt text.

    Args:
        category_id: Category identifier (e.g., 'getting_started', 'ghanaian_cultural')
        req: FastAPI request object
        response: FastAPI response object
        rate_limit: Rate limiting check

    Returns:
        dict: Category info and list of prompts

    Raises:
        HTTPException: If category not found or library cannot be loaded
    """
    try:
        import json
        import os

        # Load prompts library
        prompts_file = os.path.join(
            os.path.dirname(__file__),
            "../../voice-lab/llm_samples/prompts_library.json"
        )

        # Try alternative path
        if not os.path.exists(prompts_file):
            prompts_file = "/opt/kasaai/apps/voice-lab/llm_samples/prompts_library.json"

        with open(prompts_file, 'r') as f:
            library = json.load(f)

        # Find category
        categories = library.get("categories", [])
        category = next((c for c in categories if c["id"] == category_id), None)

        if not category:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "CATEGORY_NOT_FOUND",
                    "message": f"Category '{category_id}' not found",
                    "status_code": 404,
                    "available_categories": [c["id"] for c in categories]
                }
            )

        # Filter prompts by category
        prompts = library.get("prompts", [])
        category_prompts = [p for p in prompts if p["category"] == category_id]

        return {
            "category": category,
            "prompts": category_prompts,
            "count": len(category_prompts)
        }

    except HTTPException:
        raise
    except FileNotFoundError:
        logger.error("Prompts library file not found")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "PROMPTS_LIBRARY_NOT_FOUND",
                "message": "Sample prompts library not found",
                "status_code": 404
            }
        )
    except Exception as e:
        logger.error(f"Error loading category prompts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "PROMPTS_LOAD_ERROR",
                "message": f"Failed to load category prompts: {str(e)}",
                "status_code": 500
            }
        )


@router.post("/prompts/{prompt_id}/try")
async def try_sample_prompt(
    prompt_id: str,
    req: Request,
    response: Response,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_llm_rate_limit("chat", "free")),
    model_id: str = Query(..., description="Model to use for this prompt"),
    temperature: float = Query(0.7, ge=0.0, le=2.0, description="Sampling temperature"),
    max_tokens: Optional[int] = Query(None, description="Maximum tokens to generate")
) -> Dict:
    """
    Try a sample prompt with a selected model.

    Executes a sample prompt from the library with the specified model,
    returning both the prompt details and the generated response.

    Args:
        prompt_id: Sample prompt identifier
        req: FastAPI request object
        response: FastAPI response object
        user: Current authenticated user
        rate_limit: Rate limiting check
        model_id: LLM model to use
        temperature: Sampling temperature (0.0-2.0)
        max_tokens: Maximum tokens to generate

    Returns:
        dict: Prompt details and generated response

    Raises:
        HTTPException: If prompt not found or generation fails
    """
    try:
        import json
        import os

        # Load prompts library
        prompts_file = os.path.join(
            os.path.dirname(__file__),
            "../../voice-lab/llm_samples/prompts_library.json"
        )

        # Try alternative path
        if not os.path.exists(prompts_file):
            prompts_file = "/opt/kasaai/apps/voice-lab/llm_samples/prompts_library.json"

        with open(prompts_file, 'r') as f:
            library = json.load(f)

        # Find prompt
        prompts = library.get("prompts", [])
        prompt_data = next((p for p in prompts if p["id"] == prompt_id), None)

        if not prompt_data:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "PROMPT_NOT_FOUND",
                    "message": f"Prompt '{prompt_id}' not found",
                    "status_code": 404
                }
            )

        # Validate prompt text
        validation_service = get_validation_service()
        prompt_text = prompt_data["prompt"]
        messages = [ChatMessage(role="user", content=prompt_text)]

        validation_result = await validation_service.validate_prompt(
            messages=messages,
            model_id=model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            check_unsafe_content=False  # Sample prompts are pre-validated
        )

        if not validation_result.valid:
            raise LLMError(message=f"Prompt validation failed: {'; '.join(validation_result.errors)}")

        # Get LLM service
        llm_service: LLMProviderService = await get_llm_service()

        # Create chat request
        chat_request = ChatRequest(
            model_id=model_id,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False
        )

        # Execute prompt
        result = await llm_service.chat(
            user_id=user["id"],
            request=chat_request,
            skip_billing=False
        )

        logger.info(
            f"Sample prompt executed: user={user['id']}, prompt={prompt_id}, "
            f"model={model_id}, cost=${result.cost:.4f}"
        )

        return {
            "prompt": {
                "id": prompt_data["id"],
                "title": prompt_data["title"],
                "category": prompt_data["category"],
                "difficulty": prompt_data["difficulty"],
                "prompt_text": prompt_text,
                "description": prompt_data["description"]
            },
            "result": {
                "message": result.message,
                "model_id": result.model_id,
                "usage": result.usage,
                "cost": result.cost,
                "processing_time": result.processing_time,
                "finish_reason": result.finish_reason
            }
        }

    except HTTPException:
        raise
    except LLMError as e:
        logger.warning(f"LLM error executing sample prompt: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    except FileNotFoundError:
        logger.error("Prompts library file not found")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "PROMPTS_LIBRARY_NOT_FOUND",
                "message": "Sample prompts library not found",
                "status_code": 404
            }
        )
    except Exception as e:
        llm_error = map_exception_to_llm_error(e)
        logger.error(f"Error executing sample prompt: {str(e)}")
        raise HTTPException(status_code=llm_error.status_code, detail=llm_error.to_dict())


# ============================================================================
# Enhanced Provider Metadata Endpoints
# ============================================================================

@router.get("/providers/{provider_id}/capabilities")
async def get_provider_capabilities(
    provider_id: str,
    req: Request,
    response: Response,
    rate_limit: None = Depends(get_llm_rate_limit("info", "free"))
) -> Dict:
    """
    Get detailed model capabilities and metadata.

    Returns comprehensive information about a specific LLM provider including:
    - Capabilities (streaming, reasoning, code generation, vision, etc.)
    - Supported languages
    - Context window and token limits
    - Pricing information
    - Rate limits
    - Use cases and strengths

    Args:
        provider_id: Provider identifier (e.g., "kasaai_llama_twi", "llama_32_3b")
        req: FastAPI request object
        response: FastAPI response object
        rate_limit: Rate limiting check

    Returns:
        dict: Detailed provider capabilities and metadata

    Raises:
        HTTPException: If provider not found
    """
    try:
        llm_service = await get_llm_service()

        # Get all providers to find the requested one
        providers = await llm_service.get_available_providers()

        if provider_id not in providers:
            raise HTTPException(
                status_code=404,
                detail={"error": "PROVIDER_NOT_FOUND", "message": f"Provider '{provider_id}' not found"}
            )

        provider_info = providers[provider_id]

        # Extract and format provider details
        return {
            "model_id": provider_id,
            "name": provider_info.get("name", "Unknown"),
            "description": provider_info.get("description", ""),
            "icon": provider_info.get("icon", "🤖"),
            "capabilities": provider_info.get("capabilities", {}),
            "languages": {
                "count": provider_info.get("languages", 0),
                "supported": provider_info.get("languageList", [])
            },
            "limits": {
                "contextWindow": provider_info.get("metadata", {}).get("contextWindow", None),
                "maxInputTokens": provider_info.get("metadata", {}).get("limits", {}).get("maxInputTokens", None),
                "maxOutputTokens": provider_info.get("metadata", {}).get("limits", {}).get("maxOutputTokens", None) or provider_info.get("metadata", {}).get("maxOutputTokens", None),
                "rateLimitRPM": provider_info.get("metadata", {}).get("limits", {}).get("rateLimitRPM", None)
            },
            "pricing": provider_info.get("metadata", {}).get("pricing", None),
            "metadata": {
                "baseModel": provider_info.get("metadata", {}).get("baseModel", None),
                "modelSize": provider_info.get("metadata", {}).get("modelSize", None),
                "fineTuned": provider_info.get("metadata", {}).get("fineTuned", False),
                "trainingData": provider_info.get("metadata", {}).get("trainingData", None),
                "lastUpdated": provider_info.get("metadata", {}).get("lastUpdated", None),
                "useCases": provider_info.get("metadata", {}).get("useCases", []),
                "strengths": provider_info.get("metadata", {}).get("strengths", []),
                "limitations": provider_info.get("metadata", {}).get("limitations", [])
            },
            "health": provider_info.get("health", {})
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting provider capabilities: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "CAPABILITIES_FETCH_ERROR", "message": str(e)}
        )


@router.post("/providers/recommend")
async def recommend_provider(
    requirements: Dict = Body(...),
    req: Request = None,
    response: Response = None,
    rate_limit: None = Depends(get_llm_rate_limit("info", "free"))
) -> Dict:
    """
    Recommend best LLM provider based on requirements.

    Analyzes user requirements and returns top recommended providers
    with scoring based on capability matching.

    Args:
        requirements: Dict with optional keys:
            - needs_twi (bool): Requires Twi language support
            - needs_streaming (bool): Requires streaming responses
            - needs_vision (bool): Requires vision/image understanding
            - needs_code (bool): Requires code generation
            - needs_reasoning (bool): Requires advanced reasoning
            - needs_cultural_context (bool): Requires cultural understanding
            - max_cost (float): Maximum cost per 1K tokens
            - min_context_window (int): Minimum context window size
        req: FastAPI request object
        response: FastAPI response object
        rate_limit: Rate limiting check

    Returns:
        dict: List of recommended providers with scores

    Example request:
        {
            "needs_twi": true,
            "needs_streaming": true,
            "needs_code": false
        }

    Example response:
        {
            "recommendations": [
                {
                    "provider_id": "kasaai_llama_twi",
                    "score": 15,
                    "provider": {...},
                    "reasons": ["Supports Twi language", "Streaming enabled"]
                }
            ],
            "total_evaluated": 2
        }
    """
    try:
        llm_service = await get_llm_service()
        all_providers = await llm_service.get_available_providers()

        matches = []

        for provider_id, provider in all_providers.items():
            caps = provider.get("capabilities", {})
            metadata = provider.get("metadata", {})
            score = 0
            reasons = []

            # Language requirements
            if requirements.get("needs_twi"):
                if "tw" in provider.get("languageList", []) or "ak" in provider.get("languageList", []):
                    score += 10
                    reasons.append("Supports Twi/Akan language")

            # Capability requirements
            if requirements.get("needs_streaming") and caps.get("streaming"):
                score += 5
                reasons.append("Streaming enabled")

            if requirements.get("needs_vision") and caps.get("vision"):
                score += 5
                reasons.append("Vision support")

            if requirements.get("needs_code") and caps.get("codeGeneration"):
                score += 3
                reasons.append("Code generation")

            if requirements.get("needs_reasoning") and caps.get("reasoning"):
                score += 3
                reasons.append("Advanced reasoning")

            if requirements.get("needs_cultural_context") and caps.get("culturalContext"):
                score += 8
                reasons.append("Cultural context understanding")

            # Cost requirements
            if requirements.get("max_cost"):
                pricing = metadata.get("pricing", {})
                total_cost = pricing.get("inputPer1kTokens", 0) + pricing.get("outputPer1kTokens", 0)
                if total_cost <= requirements["max_cost"]:
                    score += 2
                    reasons.append("Within budget")
                else:
                    score -= 3
                    reasons.append("Above budget")

            # Context window requirements
            if requirements.get("min_context_window"):
                context_window = metadata.get("contextWindow", 0)
                if context_window >= requirements["min_context_window"]:
                    score += 2
                    reasons.append("Sufficient context window")
                else:
                    score -= 2
                    reasons.append("Context window too small")

            # Health status bonus
            if provider.get("health", {}).get("status") == "online":
                score += 2
                reasons.append("Currently online")

            # Only include providers with positive scores
            if score > 0:
                matches.append({
                    "provider_id": provider_id,
                    "score": score,
                    "provider": provider,
                    "reasons": reasons
                })

        # Sort by score (highest first)
        matches.sort(key=lambda x: x["score"], reverse=True)

        return {
            "recommendations": matches[:5],  # Top 5 recommendations
            "total_evaluated": len(all_providers)
        }

    except Exception as e:
        logger.error(f"Error recommending provider: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "RECOMMENDATION_ERROR", "message": str(e)}
        )


# ============================================================================
# Advanced Features - Phase 5
# ============================================================================

@router.post("/chat/batch")
async def batch_chat(
    requests: List[ChatRequestAPI],
    req: Request,
    response: Response,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_llm_rate_limit("chat", "pro"))
) -> Dict:
    """
    Process multiple chat requests in batch.

    Allows processing up to 20 chat requests simultaneously for efficiency.
    Each request is processed independently - failures don't affect others.

    Args:
        requests: List of chat requests (max 20)
        req: FastAPI request object
        response: FastAPI response object
        user: Current authenticated user
        rate_limit: Rate limiting check (pro tier required)

    Returns:
        dict: Batch results with success/failure counts

    Raises:
        HTTPException: If more than 20 requests or validation fails

    Example request:
        [
            {
                "model_id": "kasaai_llama_twi",
                "messages": [{"role": "user", "content": "Hello"}],
                "temperature": 0.7
            },
            {
                "model_id": "llama_32_3b",
                "messages": [{"role": "user", "content": "Write code"}],
                "temperature": 0.3
            }
        ]

    Example response:
        {
            "results": [
                {"index": 0, "success": true, "result": {...}},
                {"index": 1, "success": false, "error": "Model offline"}
            ],
            "total": 2,
            "successful": 1,
            "failed": 1,
            "processing_time_ms": 1234.56
        }
    """
    import time
    start_time = time.time()

    try:
        # Validate batch size
        if len(requests) > 20:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "BATCH_SIZE_EXCEEDED",
                    "message": "Maximum 20 requests per batch",
                    "limit": 20,
                    "provided": len(requests)
                }
            )

        if len(requests) == 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "EMPTY_BATCH",
                    "message": "Batch must contain at least 1 request"
                }
            )

        llm_service: LLMProviderService = await get_llm_service()
        results = []

        # Process each request
        for idx, chat_req in enumerate(requests):
            try:
                # Validate prompt
                validation_service = get_validation_service()
                validation_result = validation_service.validate_prompt(
                    messages=chat_req.messages,
                    model_id=chat_req.model_id,
                    max_tokens=chat_req.max_tokens
                )

                if not validation_result.valid:
                    results.append({
                        "index": idx,
                        "success": False,
                        "error": validation_result.error,
                        "model_id": chat_req.model_id
                    })
                    continue

                # Create internal chat request
                internal_request = ChatRequest(
                    model_id=chat_req.model_id,
                    messages=chat_req.messages,
                    temperature=chat_req.temperature,
                    max_tokens=chat_req.max_tokens,
                    top_p=chat_req.top_p,
                    stream=False  # Batch mode doesn't support streaming
                )

                # Execute chat
                result = await llm_service.chat(
                    user_id=user["id"],
                    request=internal_request
                )

                results.append({
                    "index": idx,
                    "success": True,
                    "result": result,
                    "model_id": chat_req.model_id
                })

            except Exception as e:
                llm_error = map_exception_to_llm_error(e)
                results.append({
                    "index": idx,
                    "success": False,
                    "error": llm_error.to_dict(),
                    "model_id": chat_req.model_id
                })

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        return {
            "results": results,
            "total": len(requests),
            "successful": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"]),
            "processing_time_ms": round(processing_time, 2)
        }

    except HTTPException:
        raise
    except Exception as e:
        llm_error = map_exception_to_llm_error(e)
        logger.error(f"Batch chat error: {str(e)}")
        raise HTTPException(status_code=llm_error.status_code, detail=llm_error.to_dict())


@router.get("/templates")
async def list_conversation_templates(
    req: Request,
    response: Response,
    rate_limit: None = Depends(get_llm_rate_limit("info", "free"))
) -> Dict:
    """
    Get predefined conversation templates.

    Returns a list of ready-to-use conversation templates with
    pre-configured system prompts and example interactions.

    Args:
        req: FastAPI request object
        response: FastAPI response object
        rate_limit: Rate limiting check

    Returns:
        dict: List of conversation templates

    Example response:
        {
            "templates": [
                {
                    "id": "customer_support",
                    "name": "Customer Support Assistant",
                    "description": "Helpful customer service agent",
                    "system_prompt": "You are a helpful...",
                    "recommended_models": ["llama_32_3b"],
                    "example_messages": [...]
                }
            ],
            "total": 5
        }
    """
    templates = [
        {
            "id": "customer_support",
            "name": "Customer Support Assistant",
            "description": "Friendly and helpful customer service agent for general inquiries",
            "system_prompt": "You are a helpful and professional customer support agent. Be polite, patient, and solution-oriented. Always acknowledge the customer's concerns and provide clear, actionable solutions.",
            "recommended_models": ["llama_32_3b", "kasaai_llama_twi"],
            "difficulty": "beginner",
            "use_cases": ["customer service", "help desk", "support tickets"],
            "example_messages": [
                {"role": "user", "content": "I'm having trouble with my order"},
                {"role": "assistant", "content": "I understand you're experiencing issues with your order. I'm here to help! Could you please provide your order number so I can look into this for you?"}
            ]
        },
        {
            "id": "twi_teacher",
            "name": "Twi Language Teacher",
            "description": "Patient Twi language instructor for learners",
            "system_prompt": "You are a patient and encouraging Twi language teacher. Explain grammar clearly, provide pronunciation guidance, and celebrate student progress. Use examples from Ghanaian culture to make learning relevant.",
            "recommended_models": ["kasaai_llama_twi"],
            "difficulty": "intermediate",
            "use_cases": ["language learning", "Twi education", "cultural training"],
            "example_messages": [
                {"role": "user", "content": "How do I say 'good morning' in Twi?"},
                {"role": "assistant", "content": "Great question! In Twi, 'good morning' is 'Maakye' (pronounced: MAH-cheh). You can also say 'Mema wo maakye' which means 'I say good morning to you.' Would you like to learn other greetings?"}
            ]
        },
        {
            "id": "code_assistant",
            "name": "Programming Assistant",
            "description": "Expert coding helper for software development",
            "system_prompt": "You are an experienced software engineer. Provide clear, well-commented code examples. Explain complex concepts simply. Follow best practices and suggest optimizations when appropriate.",
            "recommended_models": ["llama_32_3b"],
            "difficulty": "advanced",
            "use_cases": ["code generation", "debugging", "code review", "learning programming"],
            "example_messages": [
                {"role": "user", "content": "Write a Python function to check if a string is a palindrome"},
                {"role": "assistant", "content": "Here's a clean Python function to check palindromes:\n\n```python\ndef is_palindrome(text: str) -> bool:\n    # Remove spaces and convert to lowercase\n    cleaned = text.replace(' ', '').lower()\n    # Compare with reversed string\n    return cleaned == cleaned[::-1]\n```"}
            ]
        },
        {
            "id": "creative_writer",
            "name": "Creative Writing Assistant",
            "description": "Imaginative storyteller and creative writing coach",
            "system_prompt": "You are a creative writing coach with a vivid imagination. Help users develop stories, characters, and plots. Provide constructive feedback and encourage experimentation with different writing styles.",
            "recommended_models": ["llama_32_3b"],
            "difficulty": "intermediate",
            "use_cases": ["story writing", "character development", "creative brainstorming"],
            "example_messages": [
                {"role": "user", "content": "Help me create a character for my story set in Accra"},
                {"role": "assistant", "content": "Let's create a compelling character! Here's a starting point:\n\nName: Akosua Mensah\nAge: 28\nBackground: Tech entrepreneur who left a corporate job to start a mobile payment startup in Accra.\n\nWhat makes her interesting? She navigates between traditional family expectations and her modern ambitions..."}
            ]
        },
        {
            "id": "business_advisor",
            "name": "Ghanaian Business Advisor",
            "description": "Strategic business consultant for Ghana market",
            "system_prompt": "You are a business consultant specializing in the Ghanaian market. Provide practical advice considering local economic conditions, cultural factors, and regulatory environment. Focus on sustainable and ethical business practices.",
            "recommended_models": ["kasaai_llama_twi", "llama_32_3b"],
            "difficulty": "advanced",
            "use_cases": ["business planning", "market analysis", "entrepreneurship", "local strategy"],
            "example_messages": [
                {"role": "user", "content": "What are good small business ideas for Kumasi?"},
                {"role": "assistant", "content": "Kumasi offers several promising opportunities:\n\n1. Mobile Food Delivery - Partner with local chop bars\n2. Tech Repair Services - Growing smartphone market\n3. Agricultural Processing - Add value to local produce\n\nConsider factors like startup capital, competition, and local demand..."}
            ]
        }
    ]

    return {
        "templates": templates,
        "total": len(templates)
    }


@router.post("/templates/{template_id}/start")
async def start_from_template(
    template_id: str,
    req: Request,
    response: Response,
    user: dict = Depends(get_current_user_mongo),
    model_id: Optional[str] = Query(None, description="Override recommended model"),
    rate_limit: None = Depends(get_llm_rate_limit("chat", "free"))
) -> Dict:
    """
    Start a new conversation from a template.

    Loads a conversation template and initializes a conversation with
    the template's system prompt and example messages.

    Args:
        template_id: Template identifier
        req: FastAPI request object
        response: FastAPI response object
        user: Current authenticated user
        model_id: Optional model override
        rate_limit: Rate limiting check

    Returns:
        dict: Template details and initial conversation state

    Raises:
        HTTPException: If template not found

    Example response:
        {
            "template": {...},
            "conversation_id": "uuid",
            "model_id": "kasaai_llama_twi",
            "initial_messages": [...]
        }
    """
    try:
        # Get templates
        templates_response = await list_conversation_templates(req, response, rate_limit)
        templates = templates_response["templates"]

        # Find requested template
        template = next((t for t in templates if t["id"] == template_id), None)

        if not template:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "TEMPLATE_NOT_FOUND",
                    "message": f"Template '{template_id}' not found",
                    "available_templates": [t["id"] for t in templates]
                }
            )

        # Determine model to use
        selected_model = model_id if model_id else template["recommended_models"][0]

        # Generate conversation ID
        import uuid
        conversation_id = str(uuid.uuid4())

        # Prepare initial messages (system prompt + examples)
        initial_messages = [
            {"role": "system", "content": template["system_prompt"]}
        ]
        initial_messages.extend(template["example_messages"])

        return {
            "template": {
                "id": template["id"],
                "name": template["name"],
                "description": template["description"]
            },
            "conversation_id": conversation_id,
            "model_id": selected_model,
            "system_prompt": template["system_prompt"],
            "initial_messages": initial_messages,
            "use_cases": template["use_cases"],
            "message": f"Conversation started from template '{template['name']}'. Use the conversation_id in your chat requests to continue this conversation."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting from template: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "TEMPLATE_START_ERROR", "message": str(e)}
        )


@router.get("/history/export")
async def export_chat_history(
    req: Request,
    response: Response,
    format: str = Query("json", regex="^(json|csv|markdown)$"),
    conversation_id: Optional[str] = Query(None),
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_llm_rate_limit("info", "free"))
):
    """
    Export chat history in various formats.

    Exports user's chat history to JSON, CSV, or Markdown format.
    Can export all history or filter by conversation_id.

    Args:
        req: FastAPI request object
        response: FastAPI response object
        format: Export format (json, csv, markdown)
        conversation_id: Optional conversation filter
        user: Current authenticated user
        rate_limit: Rate limiting check

    Returns:
        Exported data in requested format

    Query examples:
        - /api/llm/history/export?format=json
        - /api/llm/history/export?format=csv&conversation_id=abc123
        - /api/llm/history/export?format=markdown

    Formats:
        - json: Structured JSON with all fields
        - csv: Tabular format with key fields
        - markdown: Human-readable conversation format
    """
    try:
        history_service: ChatHistoryService = get_chat_history_service()

        # Get chat history
        if conversation_id:
            items = await history_service.get_conversation_history(
                user_id=user["id"],
                conversation_id=conversation_id
            )
        else:
            result = await history_service.get_user_history(
                user_id=user["id"],
                limit=1000
            )
            items = result["items"]

        if format == "json":
            # Return JSON directly
            return {
                "export_format": "json",
                "export_date": datetime.utcnow().isoformat(),
                "user_id": user["id"],
                "conversation_id": conversation_id,
                "total_items": len(items),
                "items": [item.dict() for item in items]
            }

        elif format == "csv":
            # Convert to CSV
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow([
                "ID", "Created At", "Model", "Conversation ID",
                "Prompt", "Response Preview", "Total Tokens", "Cost"
            ])

            # Write rows
            for item in items:
                prompt_text = " | ".join([f"{m.role}: {m.content[:50]}..." for m in item.messages])
                writer.writerow([
                    str(item.id),
                    item.created_at.isoformat() if item.created_at else "",
                    item.model_id,
                    item.conversation_id or "",
                    prompt_text[:200],
                    item.response_preview,
                    item.usage.total_tokens if item.usage else 0,
                    f"${item.cost:.4f}" if item.cost else "$0.0000"
                ])

            csv_content = output.getvalue()
            output.close()

            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=chat_history_{user['id'][:8]}.csv"
                }
            )

        elif format == "markdown":
            # Convert to Markdown
            md_lines = []
            md_lines.append(f"# Chat History Export")
            md_lines.append(f"\n**User ID:** {user['id']}")
            md_lines.append(f"**Export Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
            if conversation_id:
                md_lines.append(f"**Conversation ID:** {conversation_id}")
            md_lines.append(f"**Total Conversations:** {len(items)}\n")
            md_lines.append("---\n")

            for idx, item in enumerate(items, 1):
                md_lines.append(f"## Conversation {idx}")
                md_lines.append(f"\n**Date:** {item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else 'N/A'}")
                md_lines.append(f"**Model:** {item.model_id}")
                if item.conversation_id:
                    md_lines.append(f"**Conversation ID:** {item.conversation_id}")
                md_lines.append(f"**Tokens:** {item.usage.total_tokens if item.usage else 0}")
                md_lines.append(f"**Cost:** ${item.cost:.4f}" if item.cost else "**Cost:** $0.0000")
                md_lines.append("\n### Messages\n")

                for msg in item.messages:
                    md_lines.append(f"**{msg.role.capitalize()}:**")
                    md_lines.append(f"{msg.content}\n")

                md_lines.append("**Assistant:**")
                md_lines.append(f"{item.response}\n")
                md_lines.append("---\n")

            markdown_content = "\n".join(md_lines)

            return Response(
                content=markdown_content,
                media_type="text/markdown",
                headers={
                    "Content-Disposition": f"attachment; filename=chat_history_{user['id'][:8]}.md"
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "EXPORT_ERROR", "message": str(e)}
        )


async def get_llm_service():
    """Get LLM provider service instance."""
    from apps.shared.services.llm_provider_service import LLMProviderService
    from apps.shared.integration.ai_services.provider_registry import (
        get_global_registry,
        get_default_llm_providers_config,
        ProviderType
    )

    # Load default LLM providers into global registry if not already loaded
    registry = get_global_registry()
    if not registry.get_providers_by_type(ProviderType.LLM):
        llm_providers_config = get_default_llm_providers_config()
        registry.register_providers_from_config(llm_providers_config, ProviderType.LLM)
        logger.info(f"Registered {len(llm_providers_config)} LLM providers into global registry")

    # Create and initialize service
    # Note: Billing disabled for metadata/info endpoints
    llm_service = LLMProviderService(
        enable_billing=False,
        enable_health_monitoring=True
    )

    if not llm_service._initialized:
        await llm_service.initialize()

    return llm_service
