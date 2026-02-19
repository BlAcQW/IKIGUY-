"""
Usage Calculator for KasaAI Shared Services

This module provides comprehensive usage tracking and cost calculation for:
- RAG queries (per token, per query, per document chunk)
- Voice AI calls (per minute, per call)
- TTS/STT operations (per character, per minute)
- Document processing (per page, per document, per MB)
- n8n workflow executions (per execution, per action)
- Custom service usage tracking

Supports multiple pricing tiers (free, basic, premium, enterprise) and
currency conversion for accurate billing.

Usage:
    from apps.shared.integration.usage_calculator import UsageCalculator, PricingTier

    # Initialize calculator
    calculator = UsageCalculator(tier=PricingTier.PREMIUM)

    # Calculate RAG query cost
    rag_cost = calculator.calculate_rag_cost(
        input_tokens=500,
        output_tokens=200,
        num_queries=1
    )

    # Calculate voice AI call cost
    voice_cost = calculator.calculate_voice_call_cost(
        duration_minutes=5.5,
        direction="outbound"
    )

    # Get total cost breakdown
    breakdown = calculator.get_cost_breakdown()
    print(f"Total: {breakdown.total_cost} {breakdown.currency}")

Dependencies:
    No external dependencies required

Author: KasaAI Team
Date: 2025-10-24
"""

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

# Import internal cost tracker for profit analysis
try:
    from .internal_cost_tracker import (
        InternalCostTracker,
        Provider,
        CostType
    )
    COST_TRACKING_ENABLED = True
except ImportError:
    COST_TRACKING_ENABLED = False
    # Graceful degradation if cost tracker not available


class Currency(str, Enum):
    """Supported currencies for billing."""

    GHS = "GHS"  # Ghanaian Cedi
    USD = "USD"  # US Dollar
    EUR = "EUR"  # Euro
    GBP = "GBP"  # British Pound


class PricingTier(str, Enum):
    """Pricing tiers for service usage."""

    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class ServiceType(str, Enum):
    """Types of services that can be billed."""

    RAG_QUERY = "rag_query"
    VOICE_CALL = "voice_call"
    TTS = "tts"  # Text-to-speech
    STT = "stt"  # Speech-to-text
    DOCUMENT_PROCESSING = "document_processing"
    N8N_WORKFLOW = "n8n_workflow"
    VAPI_CALL = "vapi_call"
    CUSTOM = "custom"


class UsageMetric(BaseModel):
    """Individual usage metric record."""

    service_type: ServiceType
    quantity: Decimal
    unit: str  # e.g., "tokens", "minutes", "pages", "calls"
    unit_cost: Decimal
    total_cost: Decimal
    currency: Currency
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @validator("quantity", "unit_cost", "total_cost")
    def round_decimal(cls, v):
        """Round decimal values to 4 decimal places."""
        return v.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


class CostBreakdown(BaseModel):
    """Detailed cost breakdown across all services."""

    metrics: List[UsageMetric]
    subtotals: Dict[ServiceType, Decimal] = Field(default_factory=dict)
    total_cost: Decimal = Decimal('0.00')
    currency: Currency
    pricing_tier: PricingTier
    start_time: datetime
    end_time: datetime

    @property
    def total_rag_cost(self) -> Decimal:
        """Total RAG query cost."""
        return self.subtotals.get(ServiceType.RAG_QUERY, Decimal('0.00'))

    @property
    def total_voice_cost(self) -> Decimal:
        """Total voice call cost."""
        return self.subtotals.get(ServiceType.VOICE_CALL, Decimal('0.00')) + \
               self.subtotals.get(ServiceType.VAPI_CALL, Decimal('0.00'))

    @property
    def total_document_cost(self) -> Decimal:
        """Total document processing cost."""
        return self.subtotals.get(ServiceType.DOCUMENT_PROCESSING, Decimal('0.00'))

    @property
    def total_workflow_cost(self) -> Decimal:
        """Total n8n workflow cost."""
        return self.subtotals.get(ServiceType.N8N_WORKFLOW, Decimal('0.00'))

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


class PricingConfig(BaseModel):
    """Pricing configuration for a specific tier."""

    tier: PricingTier
    currency: Currency = Currency.GHS

    # RAG pricing (per 1000 tokens)
    rag_input_token_cost: Decimal = Decimal('0.0005')  # per 1K input tokens
    rag_output_token_cost: Decimal = Decimal('0.0015')  # per 1K output tokens
    rag_query_base_cost: Decimal = Decimal('0.01')  # base cost per query

    # Voice AI pricing (per minute) - Includes VAPI, Vonage, Twilio network costs
    voice_inbound_cost: Decimal = Decimal('2.50')  # per minute
    voice_outbound_cost: Decimal = Decimal('2.50')  # per minute

    # TTS/STT pricing
    tts_cost_per_char: Decimal = Decimal('0.00001')  # per character
    stt_cost_per_minute: Decimal = Decimal('0.10')  # per minute

    # Document processing pricing
    doc_processing_cost_per_page: Decimal = Decimal('0.05')  # per page
    doc_processing_cost_per_mb: Decimal = Decimal('0.20')  # per MB

    # n8n workflow pricing
    n8n_execution_cost: Decimal = Decimal('0.02')  # per execution
    n8n_action_cost: Decimal = Decimal('0.001')  # per workflow action

    # VAPI specific pricing (same as voice calls - includes all platform costs)
    vapi_call_cost_per_minute: Decimal = Decimal('2.50')  # per minute

    @validator("*", pre=True)
    def round_costs(cls, v):
        """Round all cost values to 4 decimal places."""
        if isinstance(v, (Decimal, float, int)) and not isinstance(v, bool):
            return Decimal(str(v)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        return v

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class UsageCalculator:
    """
    Calculator for tracking usage and computing costs across KasaAI services.

    Supports multiple pricing tiers, detailed usage tracking, and
    comprehensive cost breakdowns.
    """

    # Predefined pricing configurations for each tier
    PRICING_CONFIGS = {
        PricingTier.FREE: PricingConfig(
            tier=PricingTier.FREE,
            rag_input_token_cost=Decimal('0.0000'),  # Free tier has no costs
            rag_output_token_cost=Decimal('0.0000'),
            rag_query_base_cost=Decimal('0.0000'),
            voice_inbound_cost=Decimal('0.0000'),
            voice_outbound_cost=Decimal('0.0000'),
            tts_cost_per_char=Decimal('0.0000'),
            stt_cost_per_minute=Decimal('0.0000'),
            doc_processing_cost_per_page=Decimal('0.0000'),
            doc_processing_cost_per_mb=Decimal('0.0000'),
            n8n_execution_cost=Decimal('0.0000'),
            n8n_action_cost=Decimal('0.0000'),
            vapi_call_cost_per_minute=Decimal('0.0000')
        ),
        PricingTier.BASIC: PricingConfig(
            tier=PricingTier.BASIC,
            currency=Currency.GHS,
            rag_input_token_cost=Decimal('0.0005'),
            rag_output_token_cost=Decimal('0.0015'),
            rag_query_base_cost=Decimal('0.01'),
            voice_inbound_cost=Decimal('2.50'),
            voice_outbound_cost=Decimal('2.50'),
            tts_cost_per_char=Decimal('0.00001'),
            stt_cost_per_minute=Decimal('0.10'),
            doc_processing_cost_per_page=Decimal('0.05'),
            doc_processing_cost_per_mb=Decimal('0.20'),
            n8n_execution_cost=Decimal('0.02'),
            n8n_action_cost=Decimal('0.001'),
            vapi_call_cost_per_minute=Decimal('2.50')
        ),
        PricingTier.PREMIUM: PricingConfig(
            tier=PricingTier.PREMIUM,
            currency=Currency.GHS,
            rag_input_token_cost=Decimal('0.0004'),  # 20% discount
            rag_output_token_cost=Decimal('0.0012'),
            rag_query_base_cost=Decimal('0.008'),
            voice_inbound_cost=Decimal('2.50'),
            voice_outbound_cost=Decimal('2.50'),
            tts_cost_per_char=Decimal('0.000008'),
            stt_cost_per_minute=Decimal('0.10'),
            doc_processing_cost_per_page=Decimal('0.04'),
            doc_processing_cost_per_mb=Decimal('0.16'),
            n8n_execution_cost=Decimal('0.015'),
            n8n_action_cost=Decimal('0.0008'),
            vapi_call_cost_per_minute=Decimal('2.50')
        ),
        PricingTier.ENTERPRISE: PricingConfig(
            tier=PricingTier.ENTERPRISE,
            currency=Currency.GHS,
            rag_input_token_cost=Decimal('0.0003'),  # 40% discount
            rag_output_token_cost=Decimal('0.0009'),
            rag_query_base_cost=Decimal('0.005'),
            voice_inbound_cost=Decimal('2.50'),
            voice_outbound_cost=Decimal('2.50'),
            tts_cost_per_char=Decimal('0.000005'),
            stt_cost_per_minute=Decimal('0.10'),
            doc_processing_cost_per_page=Decimal('0.03'),
            doc_processing_cost_per_mb=Decimal('0.12'),
            n8n_execution_cost=Decimal('0.01'),
            n8n_action_cost=Decimal('0.0005'),
            vapi_call_cost_per_minute=Decimal('2.50')
        )
    }

    def __init__(
        self,
        tier: PricingTier = PricingTier.BASIC,
        custom_pricing: Optional[PricingConfig] = None,
        tenant_id: Optional[str] = None,
        enable_cost_tracking: bool = True
    ):
        """
        Initialize usage calculator.

        Args:
            tier: Pricing tier to use (ignored if custom_pricing provided)
            custom_pricing: Custom pricing configuration (overrides tier)
            tenant_id: Tenant/organization ID for cost tracking
            enable_cost_tracking: Whether to track internal costs (default: True)
        """
        self.pricing = custom_pricing if custom_pricing else self.PRICING_CONFIGS[tier]
        self.metrics: List[UsageMetric] = []
        self.start_time = datetime.utcnow()
        self.tenant_id = tenant_id

        # Initialize internal cost tracker if enabled
        self.cost_tracking_enabled = enable_cost_tracking and COST_TRACKING_ENABLED
        if self.cost_tracking_enabled:
            self.cost_tracker = InternalCostTracker()
        else:
            self.cost_tracker = None

    def _record_metric(
        self,
        service_type: ServiceType,
        quantity: Decimal,
        unit: str,
        unit_cost: Decimal,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UsageMetric:
        """
        Record a usage metric.

        Args:
            service_type: Type of service
            quantity: Quantity of units used
            unit: Unit of measurement
            unit_cost: Cost per unit
            metadata: Additional metadata

        Returns:
            UsageMetric object
        """
        total_cost = quantity * unit_cost
        total_cost = total_cost.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)

        metric = UsageMetric(
            service_type=service_type,
            quantity=quantity,
            unit=unit,
            unit_cost=unit_cost,
            total_cost=total_cost,
            currency=self.pricing.currency,
            metadata=metadata or {}
        )

        self.metrics.append(metric)
        return metric

    def calculate_rag_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        num_queries: int = 1,
        provider: str = "openai",
        model: str = "gpt-4o-mini"
    ) -> UsageMetric:
        """
        Calculate cost for RAG query usage.

        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            num_queries: Number of queries made
            provider: AI provider (openai, gemini, anthropic)
            model: Model name

        Returns:
            UsageMetric with total RAG cost
        """
        # Calculate token costs (pricing is per 1000 tokens)
        input_cost = (Decimal(input_tokens) / 1000) * self.pricing.rag_input_token_cost
        output_cost = (Decimal(output_tokens) / 1000) * self.pricing.rag_output_token_cost
        base_cost = Decimal(num_queries) * self.pricing.rag_query_base_cost

        total_tokens = input_tokens + output_tokens
        total_token_cost = input_cost + output_cost
        total_cost = total_token_cost + base_cost

        # Record metric
        return self._record_metric(
            service_type=ServiceType.RAG_QUERY,
            quantity=Decimal(total_tokens),
            unit="tokens",
            unit_cost=total_cost / Decimal(total_tokens) if total_tokens > 0 else Decimal('0'),
            metadata={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "num_queries": num_queries,
                "provider": provider,
                "model": model,
                "input_cost": float(input_cost),
                "output_cost": float(output_cost),
                "base_cost": float(base_cost)
            }
        )

    def calculate_llm_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "gemini-2.5-flash"
    ) -> float:
        """
        Calculate cost for LLM usage.

        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            model: Model name/ID

        Returns:
            Total cost in USD as a float
        """
        # Pricing per 1M tokens (convert to per-token)
        pricing = {
            # Gemini models
            "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
            "gemini-2.0-flash-exp": {"input": 0.0, "output": 0.0},  # Free tier
            # Ollama models (local, very low cost)
            "llama_32_3b": {"input": 0.00015, "output": 0.0003},
            "llama_31_8b": {"input": 0.0002, "output": 0.0004},
            "aya_8b": {"input": 0.0001, "output": 0.0002},
            "mistral_7b": {"input": 0.00015, "output": 0.0003},
        }

        # Get pricing for model, default to low cost for unknown
        model_pricing = pricing.get(model, {"input": 0.0001, "output": 0.0002})

        # Calculate cost (pricing is per 1M tokens)
        input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (output_tokens / 1_000_000) * model_pricing["output"]

        return input_cost + output_cost

    def calculate_voice_call_cost(
        self,
        duration_minutes: float,
        direction: str = "outbound",  # outbound or inbound
        platform: str = "generic",
        call_id: Optional[str] = None
    ) -> UsageMetric:
        """
        Calculate cost for voice call.

        Args:
            duration_minutes: Call duration in minutes
            direction: Call direction (outbound/inbound)
            platform: Platform used (generic, vapi, twilio, vonage)
            call_id: Call identifier for cost tracking

        Returns:
            UsageMetric with voice call cost
        """
        duration = Decimal(str(duration_minutes))

        # Choose cost based on direction and platform
        if platform == "vapi":
            unit_cost = self.pricing.vapi_call_cost_per_minute
            service_type = ServiceType.VAPI_CALL
        else:
            unit_cost = (self.pricing.voice_outbound_cost
                        if direction == "outbound"
                        else self.pricing.voice_inbound_cost)
            service_type = ServiceType.VOICE_CALL

        metric = self._record_metric(
            service_type=service_type,
            quantity=duration,
            unit="minutes",
            unit_cost=unit_cost,
            metadata={
                "direction": direction,
                "platform": platform,
                "duration_minutes": float(duration_minutes)
            }
        )

        # Track internal costs for profit analysis
        if self.cost_tracking_enabled and self.tenant_id:
            customer_charge = metric.total_cost  # What we charged the customer

            try:
                if platform == "vapi":
                    # Track VAPI call cost
                    self.cost_tracker.record_vapi_call_cost(
                        duration_minutes=duration_minutes,
                        customer_charge=customer_charge,
                        tenant_id=self.tenant_id,
                        call_id=call_id,
                        use_full_stack_cost=True,  # Assume full stack by default
                        metadata={"direction": direction}
                    )
                elif platform in ["twilio", "generic"]:
                    # Track Twilio call cost
                    self.cost_tracker.record_twilio_call_cost(
                        duration_minutes=duration_minutes,
                        customer_charge=customer_charge,
                        tenant_id=self.tenant_id,
                        call_id=call_id,
                        is_inbound=(direction == "inbound"),
                        metadata={"platform": platform}
                    )
                # Note: Vonage tracking can be added when needed
            except Exception as e:
                # Don't fail billing if cost tracking fails
                pass

        return metric

    def calculate_tts_cost(
        self,
        num_characters: int,
        provider: str = "openai",
        voice: str = "default"
    ) -> UsageMetric:
        """
        Calculate cost for text-to-speech conversion.

        Args:
            num_characters: Number of characters converted
            provider: TTS provider (openai, google, coqui)
            voice: Voice name/ID used

        Returns:
            UsageMetric with TTS cost
        """
        return self._record_metric(
            service_type=ServiceType.TTS,
            quantity=Decimal(num_characters),
            unit="characters",
            unit_cost=self.pricing.tts_cost_per_char,
            metadata={
                "provider": provider,
                "voice": voice,
                "num_characters": num_characters
            }
        )

    def calculate_stt_cost(
        self,
        duration_minutes: float,
        provider: str = "openai",
        language: str = "en"
    ) -> UsageMetric:
        """
        Calculate cost for speech-to-text conversion.

        Args:
            duration_minutes: Audio duration in minutes
            provider: STT provider (openai, google, whisper)
            language: Language code

        Returns:
            UsageMetric with STT cost
        """
        return self._record_metric(
            service_type=ServiceType.STT,
            quantity=Decimal(str(duration_minutes)),
            unit="minutes",
            unit_cost=self.pricing.stt_cost_per_minute,
            metadata={
                "provider": provider,
                "language": language,
                "duration_minutes": float(duration_minutes)
            }
        )

    def calculate_asr_cost(
        self,
        duration_seconds: float,
        provider: str = "openai_whisper"
    ) -> float:
        """
        Calculate cost for ASR (Automatic Speech Recognition).

        Args:
            duration_seconds: Audio duration in seconds
            provider: ASR provider ID (e.g., 'openai_whisper', 'groq_whisper_large_v3_turbo')

        Returns:
            Cost in USD
        """
        # Convert seconds to hours for Groq pricing (they charge per hour)
        duration_hours = duration_seconds / 3600
        # Convert seconds to minutes for OpenAI pricing
        duration_minutes = duration_seconds / 60

        # Provider-specific pricing
        # Groq Whisper Large v3 Turbo: $0.04/hour
        if provider == 'groq_whisper_large_v3_turbo':
            return duration_hours * 0.04
        # Groq Whisper Large v3: $0.111/hour
        elif provider == 'groq_whisper_large_v3':
            return duration_hours * 0.111
        # OpenAI Whisper: $0.006 per minute
        elif 'openai' in provider.lower():
            return duration_minutes * 0.006
        # Self-hosted Whisper (whisper.ailabsafrica.com): minimal cost
        elif provider == 'whisper_large_v3':
            return duration_minutes * 0.001
        # Akan Whisper (specialized): minimal cost
        elif provider == 'akan_whisper_giftmark':
            return duration_minutes * 0.001
        # Default fallback
        else:
            return duration_minutes * 0.001

    def calculate_document_processing_cost(
        self,
        num_pages: int,
        file_size_mb: float,
        document_type: str = "pdf"
    ) -> UsageMetric:
        """
        Calculate cost for document processing.

        Args:
            num_pages: Number of pages processed
            file_size_mb: File size in megabytes
            document_type: Type of document (pdf, docx, txt)

        Returns:
            UsageMetric with document processing cost
        """
        # Calculate based on both pages and size, take the higher cost
        # Reason: Some documents have many pages but small size, others have few pages but large size
        page_cost = Decimal(num_pages) * self.pricing.doc_processing_cost_per_page
        size_cost = Decimal(str(file_size_mb)) * self.pricing.doc_processing_cost_per_mb

        # Use the higher of the two costs
        total_cost = max(page_cost, size_cost)

        # Calculate effective unit cost
        unit_cost = total_cost / Decimal(num_pages) if num_pages > 0 else Decimal('0')

        return self._record_metric(
            service_type=ServiceType.DOCUMENT_PROCESSING,
            quantity=Decimal(num_pages),
            unit="pages",
            unit_cost=unit_cost,
            metadata={
                "num_pages": num_pages,
                "file_size_mb": float(file_size_mb),
                "document_type": document_type,
                "page_cost": float(page_cost),
                "size_cost": float(size_cost)
            }
        )

    def calculate_n8n_workflow_cost(
        self,
        num_executions: int,
        num_actions: int,
        workflow_name: Optional[str] = None
    ) -> UsageMetric:
        """
        Calculate cost for n8n workflow execution.

        Args:
            num_executions: Number of workflow executions
            num_actions: Total number of actions executed
            workflow_name: Name of the workflow

        Returns:
            UsageMetric with workflow cost
        """
        execution_cost = Decimal(num_executions) * self.pricing.n8n_execution_cost
        action_cost = Decimal(num_actions) * self.pricing.n8n_action_cost
        total_cost = execution_cost + action_cost

        # Use executions as the quantity
        unit_cost = total_cost / Decimal(num_executions) if num_executions > 0 else Decimal('0')

        return self._record_metric(
            service_type=ServiceType.N8N_WORKFLOW,
            quantity=Decimal(num_executions),
            unit="executions",
            unit_cost=unit_cost,
            metadata={
                "num_executions": num_executions,
                "num_actions": num_actions,
                "workflow_name": workflow_name,
                "execution_cost": float(execution_cost),
                "action_cost": float(action_cost)
            }
        )

    def calculate_custom_cost(
        self,
        quantity: Decimal,
        unit: str,
        unit_cost: Decimal,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UsageMetric:
        """
        Calculate cost for custom service usage.

        Args:
            quantity: Quantity of units used
            unit: Unit of measurement
            unit_cost: Cost per unit
            description: Description of the custom service
            metadata: Additional metadata

        Returns:
            UsageMetric with custom cost
        """
        meta = metadata or {}
        meta['description'] = description

        return self._record_metric(
            service_type=ServiceType.CUSTOM,
            quantity=quantity,
            unit=unit,
            unit_cost=unit_cost,
            metadata=meta
        )

    def get_cost_breakdown(self) -> CostBreakdown:
        """
        Get detailed cost breakdown across all services.

        Returns:
            CostBreakdown with subtotals and total cost
        """
        subtotals: Dict[ServiceType, Decimal] = {}

        # Calculate subtotals by service type
        for metric in self.metrics:
            service_type = metric.service_type
            subtotals[service_type] = subtotals.get(service_type, Decimal('0.00')) + metric.total_cost

        # Calculate total cost
        total_cost = sum(subtotals.values(), Decimal('0.00'))
        total_cost = total_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return CostBreakdown(
            metrics=self.metrics,
            subtotals=subtotals,
            total_cost=total_cost,
            currency=self.pricing.currency,
            pricing_tier=self.pricing.tier,
            start_time=self.start_time,
            end_time=datetime.utcnow()
        )

    def get_internal_cost_summary(self) -> Optional[Dict[str, Any]]:
        """
        Get internal cost tracking summary (ADMIN ONLY).

        This shows actual costs paid to providers vs. what we charged customers.
        Returns None if cost tracking is disabled.

        Returns:
            Dictionary with cost summary and profit margins, or None
        """
        if not self.cost_tracking_enabled or not self.cost_tracker:
            return None

        try:
            return self.cost_tracker.get_summary()
        except Exception as e:
            # Return None if there's an error
            return None

    def reset(self):
        """Reset all metrics and start a new calculation session."""
        self.metrics = []
        self.start_time = datetime.utcnow()

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get summary of usage metrics.

        Returns:
            Dictionary with usage statistics
        """
        breakdown = self.get_cost_breakdown()

        # Count metrics by service type
        service_counts: Dict[ServiceType, int] = {}
        for metric in self.metrics:
            service_counts[metric.service_type] = service_counts.get(metric.service_type, 0) + 1

        return {
            "total_cost": float(breakdown.total_cost),
            "currency": breakdown.currency,
            "pricing_tier": breakdown.pricing_tier,
            "total_metrics": len(self.metrics),
            "service_counts": {k.value: v for k, v in service_counts.items()},
            "subtotals": {k.value: float(v) for k, v in breakdown.subtotals.items()},
            "start_time": breakdown.start_time.isoformat(),
            "end_time": breakdown.end_time.isoformat(),
            "duration_minutes": (breakdown.end_time - breakdown.start_time).total_seconds() / 60
        }

    async def flush_cost_tracker(self) -> int:
        """
        Flush pending internal cost records to database.

        This method saves all queued cost records to MongoDB for profit analysis.
        Call this after calculating costs to persist data.

        Returns:
            Number of cost records saved to database

        Example:
            calculator = UsageCalculator(tenant_id="org_123")
            calculator.calculate_voice_call_cost(5.5, platform="vapi")
            saved_count = await calculator.flush_cost_tracker()
            print(f"Saved {saved_count} cost records")
        """
        if self.cost_tracker and hasattr(self.cost_tracker, 'flush_pending_saves'):
            try:
                return await self.cost_tracker.flush_pending_saves()
            except Exception as e:
                # Log but don't raise - cost tracking should not break operations
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to flush cost tracker: {e}")
                return 0
        return 0


# Helper function to create calculator with custom pricing
def create_custom_calculator(
    tier: PricingTier,
    overrides: Dict[str, Decimal]
) -> UsageCalculator:
    """
    Create a usage calculator with custom pricing overrides.

    Args:
        tier: Base pricing tier
        overrides: Dictionary of pricing field overrides

    Returns:
        UsageCalculator with custom pricing

    Example:
        calculator = create_custom_calculator(
            tier=PricingTier.BASIC,
            overrides={
                "rag_query_base_cost": Decimal('0.02'),
                "voice_outbound_cost": Decimal('0.75')
            }
        )
    """
    base_config = UsageCalculator.PRICING_CONFIGS[tier].dict()
    base_config.update(overrides)

    custom_pricing = PricingConfig(**base_config)
    return UsageCalculator(custom_pricing=custom_pricing)
