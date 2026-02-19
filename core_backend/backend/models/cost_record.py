"""
Cost Record MongoDB Model

Stores actual costs paid to providers for profit margin analysis (INTERNAL ONLY).

Author: KasaAI Team
Date: 2025-10-27
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class CostRecordModel(BaseModel):
    """MongoDB model for cost records (INTERNAL ONLY)."""

    id: Optional[str] = Field(None, alias="_id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Provider info
    provider: str  # vapi, twilio, openai, stripe, etc.
    cost_type: str  # voice_call, ai_tokens, payment_processing, etc.

    # Cost details
    quantity: float
    unit: str  # minutes, tokens, characters, requests
    unit_cost: float  # What we pay per unit (USD)
    total_cost: float  # Total we paid (USD)
    total_cost_ghs: float  # Total in GHS
    currency: str = "USD"

    # Customer charge
    customer_charge: Optional[float] = None  # What we charged (GHS)
    profit_margin: Optional[float] = None  # Profit/loss (GHS)
    profit_margin_percentage: Optional[float] = None  # Margin %

    # Links to transactions
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    call_id: Optional[str] = None
    transaction_id: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }


# Database collection name
COST_RECORDS_COLLECTION = "cost_records_internal"
