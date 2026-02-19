"""
Cost Analytics API (INTERNAL/ADMIN ONLY)

Endpoints for viewing internal cost tracking and profit analysis.
IMPORTANT: These endpoints expose sensitive business data and should NEVER
be accessible to end users.

Author: KasaAI Team
Date: 2025-10-27
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from pydantic import BaseModel
import logging

from ..auth import get_current_user_mongo
from apps.shared.integration.internal_cost_tracker import (
    InternalCostTracker,
    Provider,
    CostType,
    ProviderCosts
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/cost-analytics", tags=["admin", "cost-analytics"])


def is_admin_user(user: dict) -> bool:
    """Check if user has admin privileges."""
    user_email = user.get("email", "")
    admin_emails = [
        "ailabsafrica@gmail.com",
        "admin@ailabsafrica.com",
        "support@ailabsafrica.com",
        "alfred.anyan@gmail.com"
    ]

    return (user_email in admin_emails or
            user.get("user_metadata", {}).get("role") == "admin" or
            user.get("app_metadata", {}).get("role") == "admin")


# Response Models
class ProviderCostResponse(BaseModel):
    """Provider cost information."""
    provider: str
    currency: str = "USD"
    costs: Dict[str, float]


class CostSummaryResponse(BaseModel):
    """Cost summary response."""
    total_revenue: float
    total_costs: float
    total_profit: float
    profit_margin_percentage: float
    transaction_count: int
    cost_by_provider: Dict[str, float]
    profit_by_provider: Dict[str, float]


class ProfitAnalysisResponse(BaseModel):
    """Profit analysis response."""
    service_name: str
    total_revenue: float
    total_costs: float
    profit: float
    profit_margin_percentage: float
    customer_count: int
    transaction_count: int
    average_revenue_per_transaction: float
    average_cost_per_transaction: float
    start_date: datetime
    end_date: datetime


# ============================================================================
# PROVIDER COSTS ENDPOINTS (INTERNAL ONLY)
# ============================================================================

@router.get("/provider-costs", response_model=ProviderCostResponse)
async def get_provider_costs(
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get actual costs we pay to providers (INTERNAL ONLY).

    **WARNING**: This endpoint exposes sensitive business data.
    Only accessible to admin users.

    Returns:
        Provider costs in USD with currency conversion rate
    """
    # Verify admin access
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required. This endpoint is internal only."
        )

    costs = ProviderCosts()

    return {
        "provider": "multiple",
        "currency": "USD",
        "costs": {
            # Currency
            "currency_conversion_rate": float(costs.currency_conversion_rate),

            # Voice providers (per minute)
            "vapi_base_cost_per_minute": float(costs.vapi_base_cost_per_minute),
            "vapi_full_stack_cost_per_minute": float(costs.vapi_full_stack_cost_per_minute),
            "twilio_voice_inbound_cost_per_minute": float(costs.twilio_voice_inbound_cost_per_minute),
            "twilio_voice_outbound_cost_per_minute": float(costs.twilio_voice_outbound_cost_per_minute),
            "vonage_voice_cost_per_minute": float(costs.vonage_voice_cost_per_minute),

            # AI providers (per 1K tokens)
            "openai_gpt4_input_cost": float(costs.openai_gpt4_input_cost),
            "openai_gpt4_output_cost": float(costs.openai_gpt4_output_cost),
            "openai_gpt4o_mini_input_cost": float(costs.openai_gpt4o_mini_input_cost),
            "openai_gpt4o_mini_output_cost": float(costs.openai_gpt4o_mini_output_cost),
            "anthropic_claude_input_cost": float(costs.anthropic_claude_input_cost),
            "anthropic_claude_output_cost": float(costs.anthropic_claude_output_cost),
            "google_gemini_input_cost": float(costs.google_gemini_input_cost),
            "google_gemini_output_cost": float(costs.google_gemini_output_cost),

            # TTS/STT
            "openai_tts_cost_per_char": float(costs.openai_tts_cost_per_char),
            "openai_whisper_cost_per_minute": float(costs.openai_whisper_cost_per_minute),
            "elevenlabs_tts_cost_per_char": float(costs.elevenlabs_tts_cost_per_char),
            "deepgram_stt_cost_per_minute": float(costs.deepgram_stt_cost_per_minute),

            # Payment processing
            "stripe_percentage": float(costs.stripe_percentage),
            "stripe_fixed": float(costs.stripe_fixed),
            "paystack_percentage": float(costs.paystack_percentage),
            "mpesa_percentage": float(costs.mpesa_percentage),
        }
    }


@router.get("/provider-costs/comparison")
async def get_provider_cost_comparison(
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Compare provider costs for common operations (INTERNAL ONLY).

    Shows cost comparison for a 10-minute voice call across different providers.
    """
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    costs = ProviderCosts()
    duration = Decimal('10')  # 10 minutes

    # Calculate costs in USD for 10-min call
    vapi_base = float(duration * costs.vapi_base_cost_per_minute)
    vapi_full = float(duration * costs.vapi_full_stack_cost_per_minute)
    twilio_in = float(duration * costs.twilio_voice_inbound_cost_per_minute)
    twilio_out = float(duration * costs.twilio_voice_outbound_cost_per_minute)
    vonage = float(duration * costs.vonage_voice_cost_per_minute)

    # Calculate costs in GHS
    conversion_rate = float(costs.currency_conversion_rate)
    customer_charge_ghs = 10 * 2.50  # Customer pays 2.50 GHS/min

    return {
        "scenario": "10-minute voice call",
        "customer_charge_ghs": customer_charge_ghs,
        "providers": {
            "vapi_base": {
                "cost_usd": vapi_base,
                "cost_ghs": vapi_base * conversion_rate,
                "profit_ghs": customer_charge_ghs - (vapi_base * conversion_rate),
                "margin_percent": ((customer_charge_ghs - (vapi_base * conversion_rate)) / customer_charge_ghs * 100),
                "includes": "VAPI platform fee only"
            },
            "vapi_full_stack": {
                "cost_usd": vapi_full,
                "cost_ghs": vapi_full * conversion_rate,
                "profit_ghs": customer_charge_ghs - (vapi_full * conversion_rate),
                "margin_percent": ((customer_charge_ghs - (vapi_full * conversion_rate)) / customer_charge_ghs * 100),
                "includes": "VAPI + transport + TTS + STT"
            },
            "twilio_inbound": {
                "cost_usd": twilio_in,
                "cost_ghs": twilio_in * conversion_rate,
                "profit_ghs": customer_charge_ghs - (twilio_in * conversion_rate),
                "margin_percent": ((customer_charge_ghs - (twilio_in * conversion_rate)) / customer_charge_ghs * 100),
                "includes": "Twilio inbound calls (Ghana)"
            },
            "twilio_outbound": {
                "cost_usd": twilio_out,
                "cost_ghs": twilio_out * conversion_rate,
                "profit_ghs": customer_charge_ghs - (twilio_out * conversion_rate),
                "margin_percent": ((customer_charge_ghs - (twilio_out * conversion_rate)) / customer_charge_ghs * 100),
                "includes": "Twilio outbound mobile (Ghana)",
                "warning": "⚠️ LOSING MONEY!"
            },
            "vonage": {
                "cost_usd": vonage,
                "cost_ghs": vonage * conversion_rate,
                "profit_ghs": customer_charge_ghs - (vonage * conversion_rate),
                "margin_percent": ((customer_charge_ghs - (vonage * conversion_rate)) / customer_charge_ghs * 100),
                "includes": "Vonage voice"
            }
        },
        "recommendations": [
            "✅ Use VAPI base + Vonage for maximum profit (92% margin)",
            "✅ VAPI full stack is profitable but low margin (13%)",
            "❌ NEVER use Twilio outbound in Ghana (we lose money!)",
            "✅ Twilio inbound is acceptable (41% margin)"
        ]
    }


# ============================================================================
# COST TRACKING ENDPOINTS (Placeholder - requires integration)
# ============================================================================

@router.get("/summary")
async def get_cost_summary(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get overall cost summary (INTERNAL ONLY).

    NOTE: This is a placeholder. Requires integration with actual cost tracking
    in the usage/billing system to record costs as they occur.
    """
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    # Placeholder response
    return {
        "status": "not_implemented",
        "message": "Cost tracking integration required. This endpoint will show actual tracked costs once integrated with the billing system.",
        "integration_steps": [
            "1. Import InternalCostTracker in usage calculation",
            "2. Call tracker.record_vapi_call_cost() when billing VAPI calls",
            "3. Call tracker.record_twilio_call_cost() when billing Twilio calls",
            "4. Call tracker.record_ai_token_cost() when billing AI usage",
            "5. Call tracker.record_payment_processing_cost() when processing payments",
            "6. Store cost records in database for persistence",
            "7. Query stored records in this endpoint"
        ],
        "example_integration": {
            "file": "apps/shared/integration/usage_calculator.py",
            "method": "calculate_voice_cost",
            "add_code": """
# After calculating customer charge:
from apps.shared.integration.internal_cost_tracker import InternalCostTracker
tracker = InternalCostTracker()
tracker.record_vapi_call_cost(
    duration_minutes=duration,
    customer_charge=customer_charge,
    tenant_id=tenant_id,
    call_id=call_id
)
            """
        }
    }


@router.get("/profit-analysis")
async def get_profit_analysis(
    service_name: str = Query(..., description="Service name (e.g., 'Voice Calls')"),
    cost_type: Optional[str] = Query(None, description="Filter by cost type"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get profit analysis for a service (INTERNAL ONLY).

    NOTE: Placeholder - requires integration.
    """
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    return {
        "status": "not_implemented",
        "message": "Requires integration with cost tracking system",
        "requested_analysis": {
            "service_name": service_name,
            "cost_type": cost_type,
            "start_date": start_date,
            "end_date": end_date
        }
    }


@router.get("/health")
async def cost_analytics_health():
    """
    Health check for cost analytics endpoints.

    This endpoint is public for monitoring purposes.
    """
    return {
        "status": "healthy",
        "service": "cost_analytics",
        "version": "1.0.0",
        "features": {
            "provider_costs": "active",
            "cost_comparison": "active",
            "cost_tracking": "requires_integration",
            "profit_analysis": "requires_integration"
        },
        "timestamp": datetime.utcnow().isoformat()
    }
