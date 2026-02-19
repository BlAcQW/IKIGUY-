"""
Internal Cost Tracker for KasaAI Platform

This module tracks ACTUAL costs paid to providers (hidden from users) vs.
what we charge users. Used for profit margin analysis and business metrics.

Features:
- Track actual provider costs (VAPI, Twilio, OpenAI, etc.)
- Compare actual costs vs. customer charges
- Calculate profit margins per service
- Generate internal cost reports
- Monitor cost efficiency across services

IMPORTANT: This data should NEVER be exposed to end users.
For internal/admin use only.

Author: KasaAI Team
Date: 2025-10-27
"""

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Provider(str, Enum):
    """Third-party providers we pay."""

    VAPI = "vapi"
    TWILIO = "twilio"
    VONAGE = "vonage"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    ELEVENLABS = "elevenlabs"
    COQUI = "coqui"
    WHISPER = "whisper"
    DEEPGRAM = "deepgram"
    STRIPE = "stripe"
    PAYSTACK = "paystack"
    FLUTTERWAVE = "flutterwave"
    MPESA = "mpesa"
    AWS = "aws"
    OTHER = "other"


class CostType(str, Enum):
    """Types of costs."""

    VOICE_CALL = "voice_call"
    SMS = "sms"
    AI_TOKENS = "ai_tokens"
    TTS = "tts"
    STT = "stt"
    DOCUMENT_PROCESSING = "document_processing"
    STORAGE = "storage"
    COMPUTE = "compute"
    PAYMENT_PROCESSING = "payment_processing"
    OTHER = "other"


class ActualCost(BaseModel):
    """Record of actual cost paid to a provider."""

    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Provider info
    provider: Provider
    cost_type: CostType

    # Cost details
    quantity: Decimal
    unit: str  # minutes, tokens, characters, requests, MB, etc.
    unit_cost: Decimal  # What we actually pay per unit
    total_cost: Decimal  # Total we paid
    currency: str = "GHS"

    # Link to customer charge
    customer_charge: Optional[Decimal] = None  # What we charged the customer
    profit_margin: Optional[Decimal] = None  # customer_charge - total_cost

    # Metadata
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    call_id: Optional[str] = None
    transaction_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


class ProviderCosts(BaseModel):
    """Actual costs we pay to providers (INTERNAL ONLY - DO NOT EXPOSE TO USERS).

    All costs in USD. Use currency_conversion_rate to convert to local currency.
    Pricing verified: 2025-10-27
    """

    # Currency conversion (USD to GHS)
    currency_conversion_rate: Decimal = Decimal('10.785')  # 1 USD = 10.785 GHS (2025-10-27)

    # Voice/Telephony providers (USD per minute)
    # VAPI: $0.05/min base + transport + TTS + STT costs
    vapi_base_cost_per_minute: Decimal = Decimal('0.05')  # VAPI platform fee only
    vapi_full_stack_cost_per_minute: Decimal = Decimal('0.20')  # VAPI + transport + TTS + STT estimate

    # Twilio Ghana pricing (verified 2025-10-27)
    twilio_voice_inbound_cost_per_minute: Decimal = Decimal('0.1355')  # Ghana inbound
    twilio_voice_outbound_cost_per_minute: Decimal = Decimal('0.4070')  # Ghana outbound mobile
    twilio_sms_cost: Decimal = Decimal('0.05')  # Per SMS

    # Vonage (estimated, varies by country)
    vonage_voice_cost_per_minute: Decimal = Decimal('0.014')  # Base rate

    # AI providers (USD per 1K tokens) - verified 2025-10-27
    openai_gpt4_input_cost: Decimal = Decimal('0.01')  # Per 1K input tokens
    openai_gpt4_output_cost: Decimal = Decimal('0.03')  # Per 1K output tokens
    openai_gpt4o_mini_input_cost: Decimal = Decimal('0.00015')  # GPT-4o-mini
    openai_gpt4o_mini_output_cost: Decimal = Decimal('0.0006')  # GPT-4o-mini
    anthropic_claude_input_cost: Decimal = Decimal('0.003')  # Claude Sonnet
    anthropic_claude_output_cost: Decimal = Decimal('0.015')  # Claude Sonnet
    google_gemini_input_cost: Decimal = Decimal('0.000125')  # Gemini Pro
    google_gemini_output_cost: Decimal = Decimal('0.000375')  # Gemini Pro

    # TTS/STT providers (USD) - verified 2025-10-27
    openai_tts_cost_per_char: Decimal = Decimal('0.000015')  # $15 per 1M chars
    openai_tts_hd_cost_per_char: Decimal = Decimal('0.00003')  # $30 per 1M chars
    elevenlabs_tts_cost_per_char: Decimal = Decimal('0.00018')  # $180 per 1M chars
    openai_whisper_cost_per_minute: Decimal = Decimal('0.006')  # $0.006/min
    deepgram_stt_cost_per_minute: Decimal = Decimal('0.0043')  # $0.0043/min

    # Payment processing fees
    stripe_percentage: Decimal = Decimal('0.029')  # 2.9%
    stripe_fixed: Decimal = Decimal('0.30')  # $0.30
    paystack_percentage: Decimal = Decimal('0.015')  # 1.5%
    mpesa_percentage: Decimal = Decimal('0.01')  # 1%

    # Infrastructure
    aws_storage_per_gb: Decimal = Decimal('0.023')  # Per GB/month
    aws_compute_per_hour: Decimal = Decimal('0.10')  # t3.medium

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class ProfitAnalysis(BaseModel):
    """Profit margin analysis for a service."""

    service_name: str
    total_revenue: Decimal  # What we charged customers
    total_costs: Decimal  # What we paid providers
    profit: Decimal  # Revenue - Costs
    profit_margin_percentage: Decimal  # (Profit / Revenue) * 100

    # Breakdown
    customer_count: int
    transaction_count: int
    average_revenue_per_transaction: Decimal
    average_cost_per_transaction: Decimal

    # Time period
    start_date: datetime
    end_date: datetime

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


class InternalCostTracker:
    """
    Tracker for actual costs paid to providers.

    IMPORTANT: This is for internal use only. Do NOT expose to end users.
    """

    # Default provider costs
    PROVIDER_COSTS = ProviderCosts()

    def __init__(self, cost_record_service=None):
        """
        Initialize cost tracker.

        Args:
            cost_record_service: Optional CostRecordService for persisting costs to database.
                                 If provided, costs will be queued for async database saves.
        """
        self.cost_records: List[ActualCost] = []
        self.cost_record_service = cost_record_service
        self._pending_saves: List[ActualCost] = []  # Queue for async database saves

    def _queue_save(self, cost: ActualCost):
        """
        Queue a cost record for async database save.

        Args:
            cost: ActualCost object to save
        """
        if self.cost_record_service:
            self._pending_saves.append(cost)

    async def flush_pending_saves(self):
        """
        Save all queued cost records to database.

        Call this method periodically to persist costs to MongoDB.

        Returns:
            Number of records saved
        """
        if not self.cost_record_service or not self._pending_saves:
            return 0

        saved_count = 0
        errors = []

        for cost in self._pending_saves:
            try:
                await self.cost_record_service.save_cost_record(cost)
                saved_count += 1
            except Exception as e:
                errors.append(f"Error saving cost {cost.id}: {e}")

        # Clear pending saves
        self._pending_saves.clear()

        if errors:
            # Log errors but don't raise - cost tracking should not break operations
            import logging
            logger = logging.getLogger(__name__)
            for error in errors:
                logger.warning(error)

        return saved_count

    def _convert_usd_to_ghs(self, usd_amount: Decimal) -> Decimal:
        """
        Convert USD to GHS using current exchange rate.

        Args:
            usd_amount: Amount in USD

        Returns:
            Amount in GHS
        """
        ghs_amount = usd_amount * self.PROVIDER_COSTS.currency_conversion_rate
        return ghs_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def record_vapi_call_cost(
        self,
        duration_minutes: float,
        customer_charge: Decimal,
        tenant_id: str,
        call_id: Optional[str] = None,
        use_full_stack_cost: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ActualCost:
        """
        Record actual cost of VAPI call.

        Args:
            duration_minutes: Call duration
            customer_charge: What we charged the customer (in GHS)
            tenant_id: Tenant/organization ID
            call_id: Call identifier
            use_full_stack_cost: If True, use full stack cost (VAPI + transport + TTS + STT)
                                 If False, use base VAPI cost only
            metadata: Additional metadata

        Returns:
            ActualCost record
        """
        duration = Decimal(str(duration_minutes))

        # Get cost per minute in USD
        if use_full_stack_cost:
            unit_cost_usd = self.PROVIDER_COSTS.vapi_full_stack_cost_per_minute
        else:
            unit_cost_usd = self.PROVIDER_COSTS.vapi_base_cost_per_minute

        # Calculate total cost in USD, then convert to GHS
        total_cost_usd = duration * unit_cost_usd
        total_cost = self._convert_usd_to_ghs(total_cost_usd)
        unit_cost = self._convert_usd_to_ghs(unit_cost_usd)

        profit_margin = customer_charge - total_cost

        cost = ActualCost(
            provider=Provider.VAPI,
            cost_type=CostType.VOICE_CALL,
            quantity=duration,
            unit="minutes",
            unit_cost=unit_cost,
            total_cost=total_cost,
            customer_charge=customer_charge,
            profit_margin=profit_margin,
            tenant_id=tenant_id,
            call_id=call_id,
            metadata=metadata or {}
        )

        self.cost_records.append(cost)
        self._queue_save(cost)  # Queue for database save
        return cost

    def record_twilio_call_cost(
        self,
        duration_minutes: float,
        customer_charge: Decimal,
        tenant_id: str,
        call_id: Optional[str] = None,
        is_inbound: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ActualCost:
        """
        Record actual cost of Twilio call.

        Args:
            duration_minutes: Call duration
            customer_charge: What we charged the customer (in GHS)
            tenant_id: Tenant/organization ID
            call_id: Call identifier
            is_inbound: True for inbound calls, False for outbound
            metadata: Additional metadata

        Returns:
            ActualCost record
        """
        duration = Decimal(str(duration_minutes))

        # Get cost per minute in USD based on call direction
        if is_inbound:
            unit_cost_usd = self.PROVIDER_COSTS.twilio_voice_inbound_cost_per_minute
        else:
            unit_cost_usd = self.PROVIDER_COSTS.twilio_voice_outbound_cost_per_minute

        # Calculate total cost in USD, then convert to GHS
        total_cost_usd = duration * unit_cost_usd
        total_cost = self._convert_usd_to_ghs(total_cost_usd)
        unit_cost = self._convert_usd_to_ghs(unit_cost_usd)

        profit_margin = customer_charge - total_cost

        cost = ActualCost(
            provider=Provider.TWILIO,
            cost_type=CostType.VOICE_CALL,
            quantity=duration,
            unit="minutes",
            unit_cost=unit_cost,
            total_cost=total_cost,
            customer_charge=customer_charge,
            profit_margin=profit_margin,
            tenant_id=tenant_id,
            call_id=call_id,
            metadata=metadata or {}
        )

        self.cost_records.append(cost)
        self._queue_save(cost)  # Queue for database save
        return cost

    def record_ai_token_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        provider: Provider,
        model: str,
        customer_charge: Decimal,
        tenant_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ActualCost:
        """
        Record actual cost of AI token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            provider: AI provider (openai, anthropic, google)
            model: Model name
            customer_charge: What we charged the customer
            tenant_id: Tenant/organization ID
            metadata: Additional metadata

        Returns:
            ActualCost record
        """
        # Calculate costs based on provider and model (all in USD)
        if provider == Provider.OPENAI:
            if "gpt-4o-mini" in model.lower():
                input_cost_usd = (Decimal(input_tokens) / 1000) * self.PROVIDER_COSTS.openai_gpt4o_mini_input_cost
                output_cost_usd = (Decimal(output_tokens) / 1000) * self.PROVIDER_COSTS.openai_gpt4o_mini_output_cost
            else:  # GPT-4
                input_cost_usd = (Decimal(input_tokens) / 1000) * self.PROVIDER_COSTS.openai_gpt4_input_cost
                output_cost_usd = (Decimal(output_tokens) / 1000) * self.PROVIDER_COSTS.openai_gpt4_output_cost
        elif provider == Provider.ANTHROPIC:
            input_cost_usd = (Decimal(input_tokens) / 1000) * self.PROVIDER_COSTS.anthropic_claude_input_cost
            output_cost_usd = (Decimal(output_tokens) / 1000) * self.PROVIDER_COSTS.anthropic_claude_output_cost
        elif provider == Provider.GOOGLE:
            input_cost_usd = (Decimal(input_tokens) / 1000) * self.PROVIDER_COSTS.google_gemini_input_cost
            output_cost_usd = (Decimal(output_tokens) / 1000) * self.PROVIDER_COSTS.google_gemini_output_cost
        else:
            input_cost_usd = Decimal('0')
            output_cost_usd = Decimal('0')

        # Convert to GHS
        total_cost_usd = input_cost_usd + output_cost_usd
        total_cost = self._convert_usd_to_ghs(total_cost_usd)

        total_tokens = input_tokens + output_tokens
        unit_cost = total_cost / Decimal(total_tokens) if total_tokens > 0 else Decimal('0')

        profit_margin = customer_charge - total_cost

        cost = ActualCost(
            provider=provider,
            cost_type=CostType.AI_TOKENS,
            quantity=Decimal(total_tokens),
            unit="tokens",
            unit_cost=unit_cost,
            total_cost=total_cost,
            customer_charge=customer_charge,
            profit_margin=profit_margin,
            tenant_id=tenant_id,
            metadata={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": model,
                "input_cost_usd": float(input_cost_usd),
                "output_cost_usd": float(output_cost_usd),
                "input_cost_ghs": float(self._convert_usd_to_ghs(input_cost_usd)),
                "output_cost_ghs": float(self._convert_usd_to_ghs(output_cost_usd)),
                **(metadata or {})
            }
        )

        self.cost_records.append(cost)
        self._queue_save(cost)  # Queue for database save
        return cost

    def record_payment_processing_cost(
        self,
        transaction_amount: Decimal,
        provider: Provider,
        customer_charge: Decimal,
        tenant_id: str,
        transaction_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ActualCost:
        """
        Record payment processing fees.

        Args:
            transaction_amount: Transaction amount
            provider: Payment provider (stripe, paystack, mpesa)
            customer_charge: What we charged for payment processing
            tenant_id: Tenant/organization ID
            transaction_id: Transaction identifier
            metadata: Additional metadata

        Returns:
            ActualCost record
        """
        # Calculate fees based on provider
        if provider == Provider.STRIPE:
            percentage_fee = transaction_amount * self.PROVIDER_COSTS.stripe_percentage
            total_cost = percentage_fee + self.PROVIDER_COSTS.stripe_fixed
        elif provider == Provider.PAYSTACK:
            total_cost = transaction_amount * self.PROVIDER_COSTS.paystack_percentage
        elif provider == Provider.MPESA:
            total_cost = transaction_amount * self.PROVIDER_COSTS.mpesa_percentage
        else:
            total_cost = Decimal('0')

        total_cost = total_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        unit_cost = total_cost / transaction_amount if transaction_amount > 0 else Decimal('0')

        profit_margin = customer_charge - total_cost

        cost = ActualCost(
            provider=provider,
            cost_type=CostType.PAYMENT_PROCESSING,
            quantity=transaction_amount,
            unit="GHS",
            unit_cost=unit_cost,
            total_cost=total_cost,
            customer_charge=customer_charge,
            profit_margin=profit_margin,
            tenant_id=tenant_id,
            transaction_id=transaction_id,
            metadata=metadata or {}
        )

        self.cost_records.append(cost)
        self._queue_save(cost)  # Queue for database save
        return cost

    def calculate_profit_analysis(
        self,
        service_name: str,
        start_date: datetime,
        end_date: datetime,
        cost_type: Optional[CostType] = None
    ) -> ProfitAnalysis:
        """
        Calculate profit analysis for a service/time period.

        Args:
            service_name: Name of service to analyze
            start_date: Start of analysis period
            end_date: End of analysis period
            cost_type: Filter by specific cost type

        Returns:
            ProfitAnalysis with margins and breakdown
        """
        # Filter records
        filtered_records = [
            r for r in self.cost_records
            if start_date <= r.timestamp <= end_date
        ]

        if cost_type:
            filtered_records = [r for r in filtered_records if r.cost_type == cost_type]

        # Calculate totals
        total_revenue = sum(r.customer_charge or Decimal('0') for r in filtered_records)
        total_costs = sum(r.total_cost for r in filtered_records)
        profit = total_revenue - total_costs

        profit_margin_percentage = (profit / total_revenue * 100) if total_revenue > 0 else Decimal('0')
        profit_margin_percentage = profit_margin_percentage.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Get unique customers
        customer_count = len(set(r.tenant_id for r in filtered_records if r.tenant_id))
        transaction_count = len(filtered_records)

        avg_revenue = total_revenue / transaction_count if transaction_count > 0 else Decimal('0')
        avg_cost = total_costs / transaction_count if transaction_count > 0 else Decimal('0')

        return ProfitAnalysis(
            service_name=service_name,
            total_revenue=total_revenue,
            total_costs=total_costs,
            profit=profit,
            profit_margin_percentage=profit_margin_percentage,
            customer_count=customer_count,
            transaction_count=transaction_count,
            average_revenue_per_transaction=avg_revenue,
            average_cost_per_transaction=avg_cost,
            start_date=start_date,
            end_date=end_date
        )

    def get_cost_breakdown_by_provider(self) -> Dict[Provider, Decimal]:
        """
        Get total costs broken down by provider.

        Returns:
            Dictionary mapping provider to total cost paid
        """
        breakdown: Dict[Provider, Decimal] = {}

        for record in self.cost_records:
            provider = record.provider
            breakdown[provider] = breakdown.get(provider, Decimal('0')) + record.total_cost

        return breakdown

    def get_profit_breakdown_by_provider(self) -> Dict[Provider, Decimal]:
        """
        Get total profit broken down by provider.

        Returns:
            Dictionary mapping provider to total profit margin
        """
        breakdown: Dict[Provider, Decimal] = {}

        for record in self.cost_records:
            provider = record.provider
            profit = record.profit_margin or Decimal('0')
            breakdown[provider] = breakdown.get(provider, Decimal('0')) + profit

        return breakdown

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of all tracked costs.

        Returns:
            Dictionary with summary statistics
        """
        total_revenue = sum(r.customer_charge or Decimal('0') for r in self.cost_records)
        total_costs = sum(r.total_cost for r in self.cost_records)
        total_profit = total_revenue - total_costs

        profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else Decimal('0')

        cost_by_provider = self.get_cost_breakdown_by_provider()
        profit_by_provider = self.get_profit_breakdown_by_provider()

        return {
            "total_revenue": float(total_revenue),
            "total_costs": float(total_costs),
            "total_profit": float(total_profit),
            "profit_margin_percentage": float(profit_margin),
            "transaction_count": len(self.cost_records),
            "cost_by_provider": {k.value: float(v) for k, v in cost_by_provider.items()},
            "profit_by_provider": {k.value: float(v) for k, v in profit_by_provider.items()}
        }

    def reset(self):
        """Clear all cost records."""
        self.cost_records = []


# Helper function to create tracker with custom provider costs
def create_custom_cost_tracker(cost_overrides: Dict[str, Decimal]) -> InternalCostTracker:
    """
    Create cost tracker with custom provider costs.

    Args:
        cost_overrides: Dictionary of cost field overrides

    Returns:
        InternalCostTracker with custom costs

    Example:
        tracker = create_custom_cost_tracker({
            "vapi_cost_per_minute": Decimal('0.50'),
            "openai_gpt4_input_cost": Decimal('0.012')
        })
    """
    tracker = InternalCostTracker()

    # Update provider costs
    for key, value in cost_overrides.items():
        if hasattr(tracker.PROVIDER_COSTS, key):
            setattr(tracker.PROVIDER_COSTS, key, value)

    return tracker
