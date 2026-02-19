"""
Fraud Detection Models for Wallet System

This module defines models for fraud detection including fraud rules,
fraud checks, risk profiles, and fraud detection decisions.

Author: KasaAI Team
Date: 2025-10-27
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from decimal import Decimal
from pydantic import BaseModel, Field


class FraudRuleType(str, Enum):
    """Types of fraud detection rules."""

    VELOCITY = "velocity"  # Transaction frequency checks
    AMOUNT = "amount"  # Amount anomaly detection
    PATTERN = "pattern"  # Behavioral pattern analysis
    LOCATION = "location"  # Geographic anomalies
    DEVICE = "device"  # Device fingerprinting
    TIME = "time"  # Time-based patterns


class FraudAction(str, Enum):
    """Actions to take when fraud is detected."""

    APPROVE = "approve"  # Allow transaction
    ALERT = "alert"  # Send alert but allow
    REVIEW = "review"  # Flag for manual review
    BLOCK = "block"  # Block transaction
    FREEZE = "freeze"  # Temporarily freeze account


class FraudCheckDecision(str, Enum):
    """Fraud check decision outcomes."""

    APPROVED = "approved"  # Transaction approved
    FLAGGED = "flagged"  # Flagged for review
    BLOCKED = "blocked"  # Transaction blocked
    PENDING_REVIEW = "pending_review"  # Awaiting manual review


class FraudCheckStatus(str, Enum):
    """Status of fraud check."""

    PENDING = "pending"
    COMPLETED = "completed"
    REVIEWED = "reviewed"
    APPEALED = "appealed"


class RiskLevel(str, Enum):
    """Risk level categories."""

    LOW = "low"  # 0-30
    MEDIUM = "medium"  # 31-60
    HIGH = "high"  # 61-80
    CRITICAL = "critical"  # 81-100


class FraudRule(BaseModel):
    """
    Fraud detection rule definition.

    Rules are evaluated against transactions to calculate risk scores.
    """

    id: str
    name: str
    description: str
    rule_type: FraudRuleType

    # Rule condition (flexible JSON structure)
    condition: Dict[str, Any]

    # Risk score to add if rule triggers (1-100)
    risk_score: int = Field(ge=1, le=100)

    # Action to take if rule triggers
    action: FraudAction

    # Rule configuration
    enabled: bool = True
    priority: int = 0  # Higher priority rules evaluated first

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FraudCheck(BaseModel):
    """
    Fraud check result for a transaction.

    Records the fraud detection analysis for a specific transaction.
    """

    id: str
    transaction_id: str
    wallet_id: str
    user_id: str

    # Risk assessment
    risk_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel

    # Triggered rules
    triggered_rules: List[str] = Field(default_factory=list)  # Rule IDs
    rule_details: List[Dict[str, Any]] = Field(default_factory=list)

    # Decision
    decision: FraudCheckDecision
    action_taken: FraudAction

    # Review information
    requires_review: bool = False
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    review_decision: Optional[str] = None

    # Appeal information
    appealed: bool = False
    appeal_reason: Optional[str] = None
    appeal_reviewed_by: Optional[str] = None
    appeal_decision: Optional[str] = None

    # Additional context
    transaction_data: Optional[Dict[str, Any]] = None
    user_risk_profile: Optional[Dict[str, Any]] = None

    # Status
    status: FraudCheckStatus = FraudCheckStatus.PENDING

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserRiskProfile(BaseModel):
    """
    User's risk profile based on historical behavior.

    Tracks user behavior patterns to help detect anomalies.
    """

    user_id: str
    wallet_id: str

    # Transaction statistics
    total_transactions: int = 0
    successful_transactions: int = 0
    failed_transactions: int = 0
    total_amount: Decimal = Decimal("0.00")
    average_amount: Decimal = Decimal("0.00")
    max_amount: Decimal = Decimal("0.00")
    min_amount: Decimal = Decimal("0.00")

    # Velocity metrics
    transactions_last_hour: int = 0
    transactions_last_day: int = 0
    transactions_last_week: int = 0
    transactions_last_month: int = 0

    # Failure tracking
    failed_attempts_last_hour: int = 0
    failed_attempts_last_day: int = 0
    consecutive_failures: int = 0
    last_failure_at: Optional[datetime] = None

    # Behavioral patterns
    common_transaction_times: List[int] = Field(default_factory=list)  # Hours of day
    common_transaction_amounts: List[float] = Field(default_factory=list)
    common_payment_methods: List[str] = Field(default_factory=list)

    # Risk indicators
    risk_score: int = 0  # Current risk score (0-100)
    risk_level: RiskLevel = RiskLevel.LOW
    trusted: bool = False  # Manually marked as trusted
    suspicious: bool = False  # Flagged as suspicious

    # Account age
    account_created_at: datetime
    first_transaction_at: Optional[datetime] = None
    last_transaction_at: Optional[datetime] = None

    # Fraud history
    fraud_checks_count: int = 0
    flagged_transactions_count: int = 0
    blocked_transactions_count: int = 0

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class VelocityCheck(BaseModel):
    """Result of velocity check."""

    user_id: str
    check_type: str  # "hourly", "daily", "weekly"

    transaction_count: int
    time_window_minutes: int
    threshold: int

    exceeded: bool
    risk_score: int

    created_at: datetime = Field(default_factory=datetime.utcnow)


class AmountAnomalyCheck(BaseModel):
    """Result of amount anomaly detection."""

    user_id: str
    transaction_amount: Decimal
    average_amount: Decimal
    max_amount: Decimal

    multiplier: float  # transaction_amount / average_amount
    threshold_multiplier: float  # e.g., 5x average

    is_anomaly: bool
    risk_score: int

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class PatternAnomalyCheck(BaseModel):
    """Result of pattern anomaly detection."""

    user_id: str
    anomaly_type: str  # "unusual_time", "new_payment_method", "rapid_changes"

    details: Dict[str, Any]
    is_anomaly: bool
    risk_score: int

    created_at: datetime = Field(default_factory=datetime.utcnow)


class FraudReviewRequest(BaseModel):
    """Request for manual fraud review."""

    fraud_check_id: str
    reviewer_id: str
    decision: str  # "approve", "reject", "request_more_info"
    notes: str
    additional_actions: Optional[List[str]] = None  # e.g., ["notify_user", "freeze_account"]


class FraudStats(BaseModel):
    """Fraud detection statistics."""

    period_start: datetime
    period_end: datetime

    # Check statistics
    total_checks: int = 0
    approved_count: int = 0
    flagged_count: int = 0
    blocked_count: int = 0
    review_count: int = 0

    # Risk distribution
    low_risk_count: int = 0
    medium_risk_count: int = 0
    high_risk_count: int = 0
    critical_risk_count: int = 0

    # Rule triggers
    most_triggered_rules: List[Dict[str, Any]] = Field(default_factory=list)

    # Performance metrics
    average_risk_score: float = 0.0
    false_positive_rate: Optional[float] = None
    false_negative_rate: Optional[float] = None

    # Amount statistics
    total_amount_flagged: Decimal = Decimal("0.00")
    total_amount_blocked: Decimal = Decimal("0.00")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }
