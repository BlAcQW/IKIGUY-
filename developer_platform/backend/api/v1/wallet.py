"""
Wallet and Billing API v1 Endpoints

Public, versioned, stable API for wallet management and billing operations.

**Version:** 1.0.0
**Stability:** Stable - no breaking changes allowed
**Rate Limits:** 20 requests/minute (Free tier)
**Authentication:** API Key required (X-API-Key header)

Breaking changes require releasing v2.
"""

import logging
import httpx
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from decimal import Decimal

# Import middleware
from ...middleware.api_key_auth import verify_api_key
from ...middleware.rate_limiter import get_rate_limit_dependency

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/wallet",
    tags=["Wallet & Billing v1"],
    responses={
        401: {"description": "Invalid API key"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    }
)

# ============================================================================
# Pydantic Models
# ============================================================================

class WalletBalance(BaseModel):
    """Wallet balance information."""
    user_id: str = Field(..., description="User ID")
    balance: float = Field(..., description="Current balance in USD")
    currency: str = Field("USD", description="Currency code")
    status: str = Field(..., description="Wallet status (active, suspended, closed)")
    low_balance_threshold: float = Field(..., description="Low balance alert threshold")
    is_low_balance: bool = Field(..., description="Whether balance is below threshold")
    last_updated: str = Field(..., description="Last update timestamp")


class Transaction(BaseModel):
    """Transaction record."""
    id: str = Field(..., description="Transaction ID")
    wallet_id: str = Field(..., description="Wallet ID")
    type: str = Field(..., description="Transaction type (credit, debit, refund)")
    amount: float = Field(..., description="Transaction amount")
    currency: str = Field(..., description="Currency code")
    status: str = Field(..., description="Transaction status")
    description: str = Field(..., description="Transaction description")
    balance_before: float = Field(..., description="Balance before transaction")
    balance_after: float = Field(..., description="Balance after transaction")
    created_at: str = Field(..., description="Creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TransactionListResponse(BaseModel):
    """List of transactions with pagination."""
    transactions: List[Transaction]
    pagination: Dict[str, Any]
    total_credit: float
    total_debit: float


class TopUpRequest(BaseModel):
    """Request to initiate wallet top-up."""
    amount: float = Field(..., gt=0, description="Amount to top up (must be positive)")
    payment_method: str = Field("paystack", description="Payment method (paystack, stripe)")
    currency: str = Field("USD", description="Currency code")
    callback_url: Optional[str] = Field(None, description="URL to redirect after payment")


class TopUpResponse(BaseModel):
    """Response from top-up initiation."""
    success: bool
    payment_url: Optional[str] = None
    reference: str
    amount: float
    currency: str
    gateway: str
    message: Optional[str] = None


# ============================================================================
# Helper Functions
# ============================================================================

async def get_core_backend_url() -> str:
    """Get Core Backend URL from environment or default."""
    import os
    return os.getenv("CORE_BACKEND_URL", "https://api.ailabsafrica.com")


async def call_core_backend(
    endpoint: str,
    method: str = "GET",
    json_data: Optional[Dict] = None,
    user_id: Optional[str] = None,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """
    Call Core Backend API.

    Args:
        endpoint: API endpoint path
        method: HTTP method
        json_data: JSON payload
        user_id: User ID for authentication
        timeout: Request timeout in seconds

    Returns:
        Response data

    Raises:
        HTTPException: If request fails
    """
    base_url = await get_core_backend_url()
    url = f"{base_url}{endpoint}"

    headers = {"Content-Type": "application/json"}

    # If user_id is provided, pass it via custom header
    if user_id:
        headers["X-User-Id"] = user_id

    logger.info(f"Calling Core Backend: {method} {url}")

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, json=json_data, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            if response.status_code >= 400:
                error_text = response.text
                logger.error(f"Core Backend error: {response.status_code} - {error_text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail={
                        "error": {
                            "code": "BACKEND_ERROR",
                            "message": f"Core Backend error: {error_text}"
                        },
                        "request_id": f"req_{datetime.utcnow().timestamp()}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

            return response.json()

        except httpx.RequestError as e:
            logger.error(f"Core Backend request failed: {e}")
            raise HTTPException(
                status_code=503,
                detail={
                    "error": {
                        "code": "SERVICE_UNAVAILABLE",
                        "message": "Core Backend service unavailable"
                    },
                    "request_id": f"req_{datetime.utcnow().timestamp()}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )


# ============================================================================
# API Routes
# ============================================================================

@router.get(
    "/balance",
    response_model=WalletBalance,
    summary="Get wallet balance",
    description="""
    Get current wallet balance and status.

    **Rate Limit:** 20 requests/minute
    **Cost:** Free

    **Example Response:**
    ```json
    {
        "user_id": "user_123",
        "balance": 45.50,
        "currency": "USD",
        "status": "active",
        "low_balance_threshold": 10.00,
        "is_low_balance": false,
        "last_updated": "2025-10-26T12:00:00"
    }
    ```
    """,
    response_description="Current wallet balance and status"
)
async def get_balance(
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """Get current wallet balance."""
    try:
        logger.info("Fetching wallet balance")

        # Get user ID from API key info
        user_id = api_key.get("tenant_id")

        # Call Core Backend
        result = await call_core_backend(
            endpoint="/api/wallet/balance",
            method="GET",
            user_id=user_id
        )

        return WalletBalance(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching wallet balance: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred"
                },
                "request_id": f"req_{datetime.utcnow().timestamp()}",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/transactions",
    response_model=TransactionListResponse,
    summary="Get transaction history",
    description="""
    Get paginated transaction history for your wallet.

    **Rate Limit:** 20 requests/minute
    **Cost:** Free

    **Query Parameters:**
    - `limit`: Number of transactions to return (default: 50, max: 100)
    - `offset`: Offset for pagination (default: 0)
    - `transaction_type`: Filter by type (credit, debit, refund)
    - `start_date`: Filter transactions after this date (ISO 8601)
    - `end_date`: Filter transactions before this date (ISO 8601)

    **Example Response:**
    ```json
    {
        "transactions": [
            {
                "id": "txn_123",
                "type": "debit",
                "amount": 0.50,
                "description": "TTS synthesis - 100 chars",
                "balance_before": 45.50,
                "balance_after": 45.00,
                "created_at": "2025-10-26T12:00:00",
                "metadata": {"service": "tts", "provider": "coqui_xtts"}
            }
        ],
        "pagination": {
            "limit": 50,
            "offset": 0,
            "total": 150
        },
        "total_credit": 100.00,
        "total_debit": 54.50
    }
    ```
    """,
    response_description="Transaction history with pagination"
)
async def get_transactions(
    limit: int = Query(50, ge=1, le=100, description="Number of transactions to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    transaction_type: Optional[str] = Query(None, description="Filter by type"),
    start_date: Optional[str] = Query(None, description="Start date (ISO 8601)"),
    end_date: Optional[str] = Query(None, description="End date (ISO 8601)"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """Get transaction history."""
    try:
        logger.info(f"Fetching transactions: limit={limit}, offset={offset}")

        # Get user ID from API key info
        user_id = api_key.get("tenant_id")

        # Build query parameters
        params = {
            "limit": limit,
            "offset": offset
        }
        if transaction_type:
            params["transaction_type"] = transaction_type
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        # Call Core Backend
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        result = await call_core_backend(
            endpoint=f"/api/wallet/transactions?{query_string}",
            method="GET",
            user_id=user_id
        )

        return TransactionListResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/topup",
    response_model=TopUpResponse,
    summary="Initiate wallet top-up",
    description="""
    Initiate a wallet top-up payment.

    **Rate Limit:** 20 requests/minute
    **Cost:** Free

    **Supported Payment Methods:**
    - `paystack`: Paystack payment gateway
    - `stripe`: Stripe payment gateway

    **Example Request:**
    ```json
    {
        "amount": 50.00,
        "payment_method": "paystack",
        "currency": "USD",
        "callback_url": "https://yourapp.com/payment/success"
    }
    ```

    **Example Response:**
    ```json
    {
        "success": true,
        "payment_url": "https://checkout.paystack.com/xyz123",
        "reference": "topup-wallet_123-abc456",
        "amount": 50.00,
        "currency": "USD",
        "gateway": "paystack",
        "message": "Redirect user to payment_url to complete payment"
    }
    ```

    **Process:**
    1. Call this endpoint to initiate payment
    2. Redirect user to `payment_url`
    3. User completes payment on gateway
    4. Gateway redirects to `callback_url`
    5. Wallet is automatically credited via webhook
    """,
    response_description="Payment initiation result with payment URL"
)
async def initiate_topup(
    request: TopUpRequest,
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """Initiate wallet top-up payment."""
    try:
        logger.info(f"Initiating top-up: amount={request.amount}, method={request.payment_method}")

        # Get user ID from API key info
        user_id = api_key.get("tenant_id")

        # Call Core Backend
        result = await call_core_backend(
            endpoint="/api/wallet/topup",
            method="POST",
            json_data=request.dict(),
            user_id=user_id
        )

        return TopUpResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating top-up: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/health",
    summary="Health check for wallet service",
    description="""
    Health check for wallet service.

    **Rate Limit:** None
    **Cost:** Free

    **Example Response:**
    ```json
    {
        "status": "healthy",
        "service": "wallet",
        "payment_gateways": ["paystack", "stripe"],
        "timestamp": "2025-10-26T12:00:00"
    }
    ```
    """,
    response_description="Health status"
)
async def health_check():
    """Health check for wallet service."""
    try:
        # Call Core Backend health endpoint
        result = await call_core_backend(
            endpoint="/api/wallet/health",
            method="GET"
        )

        return result

    except HTTPException:
        # If Core Backend is down, return unhealthy
        return {
            "status": "unhealthy",
            "service": "wallet",
            "error": "Core Backend unavailable",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Wallet health check error: {e}")
        return {
            "status": "unhealthy",
            "service": "wallet",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Export router
__all__ = ["router"]
