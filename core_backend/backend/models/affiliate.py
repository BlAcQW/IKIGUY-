"""
Affiliate Program Models for KasaAI Core Backend.

MongoDB models for multi-level marketing (MLM) / affiliate system.
Supports 3-tier commission structure for referral tracking.
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal
import uuid


class PayoutMethod(str, Enum):
    """Supported payout methods."""
    WALLET_CREDIT = "wallet_credit"
    MOBILE_MONEY = "mobile_money"
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"


class PayoutStatus(str, Enum):
    """Payout request status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CommissionStatus(str, Enum):
    """Commission record status."""
    PENDING = "pending"
    APPROVED = "approved"
    PAID = "paid"
    CANCELLED = "cancelled"


class AttributionMethod(str, Enum):
    """How the referral was attributed."""
    COOKIE = "cookie"
    URL_PARAM = "url_param"
    MANUAL = "manual"


class AffiliateProfile(BaseModel):
    """
    Affiliate profile for a user enrolled in the affiliate program.

    Tracks referral performance, commission earnings, and payout settings.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="User ID (from users collection)")
    organization_id: str = Field(..., description="Organization ID (multi-tenant)")

    # Referral information
    referral_code: str = Field(..., description="Unique referral code (e.g., ALFRED001)")
    upline_id: Optional[str] = Field(None, description="Parent affiliate user_id")
    tier_level: int = Field(1, description="Depth in the tree (1, 2, or 3)")

    # Commission rates (customizable per affiliate)
    tier1_commission_rate: Decimal = Field(
        Decimal("0.15"),
        description="Commission rate for direct referrals (15%)"
    )
    tier2_commission_rate: Decimal = Field(
        Decimal("0.08"),
        description="Commission rate for tier 2 referrals (8%)"
    )
    tier3_commission_rate: Decimal = Field(
        Decimal("0.03"),
        description="Commission rate for tier 3 referrals (3%)"
    )

    # Statistics
    total_referrals: int = Field(0, description="Total referrals across all tiers")
    direct_referrals: int = Field(0, description="Tier 1 referrals only")
    total_sales: Decimal = Field(Decimal("0.00"), description="Total sales from referrals")
    total_commissions_earned: Decimal = Field(
        Decimal("0.00"),
        description="Total commissions earned (all-time)"
    )
    total_commissions_paid: Decimal = Field(
        Decimal("0.00"),
        description="Total commissions paid out"
    )
    pending_commissions: Decimal = Field(
        Decimal("0.00"),
        description="Pending/unpaid commissions"
    )

    # Status
    is_active: bool = Field(True, description="Affiliate account active")
    is_verified: bool = Field(False, description="Email verified (required for payouts)")
    joined_program_at: datetime = Field(default_factory=datetime.utcnow)
    last_referral_at: Optional[datetime] = Field(None, description="Last successful referral")

    # Payout settings
    payout_method: PayoutMethod = Field(
        PayoutMethod.WALLET_CREDIT,
        description="Preferred payout method"
    )
    payout_threshold: Decimal = Field(
        Decimal("20.00"),
        description="Minimum amount before payout ($20 default)"
    )
    payment_method_id: Optional[str] = Field(
        None,
        description="Payment method ID for automated payouts"
    )
    notification_preferences: Optional[Dict[str, Any]] = Field(
        None,
        description="Notification preferences (email, SMS, etc.)"
    )

    # Automated payout settings
    auto_payout_enabled: bool = Field(
        False,
        description="Enable automated payouts"
    )
    auto_payout_schedule: str = Field(
        "monthly",
        description="Payout schedule: weekly or monthly"
    )
    auto_payout_day: int = Field(
        15,
        description="Day of week (0-6 for weekly) or day of month (1-31 for monthly)"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom fields for extensibility"
    )

    @validator("tier_level")
    def validate_tier_level(cls, v):
        """Validate tier level is between 1 and 3."""
        if v < 1 or v > 3:
            raise ValueError("Tier level must be between 1 and 3")
        return v

    @validator("referral_code")
    def validate_referral_code(cls, v):
        """Validate referral code format."""
        if not v:
            raise ValueError("Referral code is required")
        if len(v) < 4 or len(v) > 20:
            raise ValueError("Referral code must be 4-20 characters")
        # Allow alphanumeric and underscores only
        if not v.replace("_", "").isalnum():
            raise ValueError("Referral code must be alphanumeric")
        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123456",
                "organization_id": "org_abc",
                "referral_code": "ALFRED001",
                "upline_id": "user_789",
                "tier_level": 1,
                "total_referrals": 25,
                "direct_referrals": 10,
                "total_sales": "5000.00",
                "total_commissions_earned": "750.00",
                "pending_commissions": "125.50",
                "payout_method": "wallet_credit"
            }
        }


class ReferralLink(BaseModel):
    """
    Referral link tracking record.

    Tracks individual referral links with UTM parameters for analytics.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    affiliate_id: str = Field(..., description="User ID of affiliate")
    organization_id: str = Field(..., description="Organization ID")
    referral_code: str = Field(..., description="The unique referral code")

    # UTM parameters for tracking
    utm_source: Optional[str] = Field(None, description="Traffic source (e.g., instagram)")
    utm_campaign: Optional[str] = Field(None, description="Campaign name")
    utm_medium: Optional[str] = Field(None, description="Medium (e.g., social)")

    # Performance metrics
    click_count: int = Field(0, description="Total clicks on this link")
    conversion_count: int = Field(0, description="Total conversions (signups)")

    # Timestamps
    last_clicked_at: Optional[datetime] = Field(None, description="Last click timestamp")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def conversion_rate(self) -> float:
        """Calculate conversion rate (signups / clicks)."""
        if self.click_count == 0:
            return 0.0
        return (self.conversion_count / self.click_count) * 100

    class Config:
        json_schema_extra = {
            "example": {
                "affiliate_id": "user_123",
                "organization_id": "org_abc",
                "referral_code": "ALFRED001",
                "utm_source": "instagram",
                "utm_campaign": "q1_2025",
                "click_count": 150,
                "conversion_count": 25
            }
        }


class ReferralAttribution(BaseModel):
    """
    Referral attribution record.

    Links a new user to the affiliate who referred them.
    Supports cookie-based and URL parameter-based attribution.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    referred_user_id: str = Field(..., description="New user who signed up")
    affiliate_id: str = Field(..., description="Affiliate who gets credit")
    organization_id: str = Field(..., description="Organization ID")
    referral_code: str = Field(..., description="Referral code used")

    # Attribution details
    attribution_method: AttributionMethod = Field(
        ...,
        description="How referral was tracked"
    )
    cookie_id: Optional[str] = Field(None, description="Cookie identifier")
    ip_address: Optional[str] = Field(None, description="User IP address")
    user_agent: Optional[str] = Field(None, description="Browser user agent")

    # Timestamps
    clicked_at: datetime = Field(..., description="When referral link was clicked")
    signed_up_at: Optional[datetime] = Field(None, description="When user signed up")
    first_purchase_at: Optional[datetime] = Field(None, description="First purchase date")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "referred_user_id": "user_456",
                "affiliate_id": "user_123",
                "organization_id": "org_abc",
                "referral_code": "ALFRED001",
                "attribution_method": "cookie",
                "ip_address": "192.168.1.1",
                "clicked_at": "2025-11-01T10:00:00Z",
                "signed_up_at": "2025-11-01T10:15:00Z"
            }
        }


class CommissionRecord(BaseModel):
    """
    Commission record for affiliate earnings.

    Tracks individual commissions earned from referral purchases.
    Supports multi-tier commission calculation.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    affiliate_id: str = Field(..., description="Affiliate who earns commission")
    organization_id: str = Field(..., description="Organization ID")
    referred_user_id: str = Field(..., description="User who made purchase")
    transaction_id: str = Field(..., description="Purchase transaction ID")

    # Commission details
    sale_amount: Decimal = Field(..., description="Original purchase amount")
    commission_rate: Decimal = Field(..., description="Commission rate applied (0.15 = 15%)")
    commission_amount: Decimal = Field(..., description="Commission earned")
    tier_level: int = Field(..., description="Tier level (1, 2, or 3)")

    # Status
    status: CommissionStatus = Field(
        CommissionStatus.APPROVED,
        description="Commission status"
    )
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    paid_at: Optional[datetime] = Field(None, description="Payment timestamp")
    payout_transaction_id: Optional[str] = Field(
        None,
        description="Transaction ID when commission was paid out"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = Field(None, description="Additional notes")

    @validator("tier_level")
    def validate_tier_level(cls, v):
        """Validate tier level is between 1 and 3."""
        if v < 1 or v > 3:
            raise ValueError("Tier level must be between 1 and 3")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "affiliate_id": "user_123",
                "organization_id": "org_abc",
                "referred_user_id": "user_456",
                "transaction_id": "txn_789",
                "sale_amount": "100.00",
                "commission_rate": "0.15",
                "commission_amount": "15.00",
                "tier_level": 1,
                "status": "approved"
            }
        }


class PayoutRequest(BaseModel):
    """
    Payout request from affiliate.

    Tracks payout requests and processing status.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    affiliate_id: str = Field(..., description="Affiliate requesting payout")
    organization_id: str = Field(..., description="Organization ID")

    # Payout details
    amount: Decimal = Field(..., description="Payout amount requested")
    payout_method: PayoutMethod = Field(..., description="Payout method")
    payment_method_id: Optional[str] = Field(
        None,
        description="Payment method for payout (if applicable)"
    )

    # Processing fee (deducted from payout amount)
    processing_fee: Decimal = Field(
        Decimal("0.00"),
        description="Processing fee charged"
    )
    net_amount: Decimal = Field(..., description="Net amount after fees")

    # Status tracking
    status: PayoutStatus = Field(PayoutStatus.PENDING, description="Payout status")
    processed_by: Optional[str] = Field(None, description="Admin user who processed")
    processed_at: Optional[datetime] = Field(None, description="Processing timestamp")

    # Transaction reference
    transaction_id: Optional[str] = Field(
        None,
        description="Wallet transaction ID (for wallet credit payouts)"
    )
    provider_reference: Optional[str] = Field(
        None,
        description="External provider reference (for MoMo, PayPal, etc.)"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = Field(None, description="Admin notes")
    failure_reason: Optional[str] = Field(None, description="Failure reason if failed")

    @validator("amount", "net_amount")
    def validate_positive_amount(cls, v):
        """Validate amount is positive."""
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "affiliate_id": "user_123",
                "organization_id": "org_abc",
                "amount": "100.00",
                "payout_method": "wallet_credit",
                "processing_fee": "0.00",
                "net_amount": "100.00",
                "status": "pending"
            }
        }


# Database collection names
AFFILIATE_PROFILES_COLLECTION = "affiliate_profiles"
REFERRAL_LINKS_COLLECTION = "referral_links"
REFERRAL_ATTRIBUTIONS_COLLECTION = "referral_attributions"
COMMISSION_RECORDS_COLLECTION = "commission_records"
PAYOUT_REQUESTS_COLLECTION = "payout_requests"
REFERRAL_CLICKS_COLLECTION = "referral_clicks"
REFERRAL_CAMPAIGNS_COLLECTION = "referral_campaigns"


# ============================================================================
# Analytics Models
# ============================================================================

class ReferralClick(BaseModel):
    """
    Click tracking for referral links.

    Tracks every click on referral links for analytics and conversion tracking.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    referral_code: str = Field(..., description="Referral code that was clicked")
    affiliate_id: str = Field(..., description="Affiliate who owns the link")
    organization_id: str = Field(..., description="Organization ID")

    # Click metadata
    clicked_at: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Browser user agent")
    referrer: Optional[str] = Field(None, description="HTTP referrer")

    # UTM parameters
    utm_source: Optional[str] = Field(None, description="Traffic source")
    utm_campaign: Optional[str] = Field(None, description="Campaign name")
    utm_medium: Optional[str] = Field(None, description="Marketing medium")
    utm_content: Optional[str] = Field(None, description="Ad content")
    utm_term: Optional[str] = Field(None, description="Search term")

    # Conversion tracking
    converted: bool = Field(False, description="Whether click resulted in signup")
    converted_user_id: Optional[str] = Field(None, description="User who signed up")
    converted_at: Optional[datetime] = Field(None, description="Conversion timestamp")

    # Session tracking
    session_id: Optional[str] = Field(None, description="Browser session ID")

    class Config:
        json_schema_extra = {
            "example": {
                "referral_code": "ALFRED001",
                "affiliate_id": "user_123",
                "organization_id": "org_abc",
                "ip_address": "192.168.1.1",
                "utm_source": "instagram",
                "utm_campaign": "q1_2025",
                "converted": True,
                "converted_user_id": "user_456"
            }
        }


# ============================================================================
# Campaign Models
# ============================================================================

class CampaignStatus(str, Enum):
    """Campaign status."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReferralCampaign(BaseModel):
    """
    Referral campaign for time-limited promotions.

    Allows affiliates to run special campaigns with:
    - Custom landing pages
    - Bonus commission rates
    - Contest mechanics
    - Campaign-specific tracking
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    affiliate_id: str = Field(..., description="Affiliate running the campaign")
    organization_id: str = Field(..., description="Organization ID")

    # Campaign details
    name: str = Field(..., description="Campaign name")
    description: Optional[str] = Field(None, description="Campaign description")
    campaign_code: str = Field(..., description="Unique campaign code for tracking")

    # Time frame
    start_date: datetime = Field(..., description="Campaign start date")
    end_date: datetime = Field(..., description="Campaign end date")

    # Bonus commission
    bonus_rate: Decimal = Field(
        Decimal("0.00"),
        description="Extra commission percentage (e.g., 0.05 = 5% bonus)"
    )

    # Goals and prizes
    target_referrals: Optional[int] = Field(None, description="Target number of referrals")
    target_sales: Optional[Decimal] = Field(None, description="Target sales amount")
    prize: Optional[str] = Field(None, description="Prize for reaching targets")

    # Status
    status: CampaignStatus = Field(
        CampaignStatus.DRAFT,
        description="Campaign status"
    )
    is_active: bool = Field(True, description="Whether campaign is currently active")

    # Performance tracking
    total_clicks: int = Field(0, description="Total clicks on campaign links")
    total_conversions: int = Field(0, description="Total conversions from campaign")
    total_sales: Decimal = Field(Decimal("0.00"), description="Total sales from campaign")
    total_bonus_earned: Decimal = Field(
        Decimal("0.00"),
        description="Total bonus commission earned"
    )

    # Custom settings
    landing_page_url: Optional[str] = Field(None, description="Custom landing page URL")
    utm_campaign: Optional[str] = Field(None, description="UTM campaign parameter")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(None, description="When campaign was started")
    completed_at: Optional[datetime] = Field(None, description="When campaign was completed")

    @validator("campaign_code")
    def validate_campaign_code(cls, v):
        """Validate campaign code format."""
        if not v:
            raise ValueError("Campaign code is required")
        if len(v) < 3 or len(v) > 50:
            raise ValueError("Campaign code must be 3-50 characters")
        # Allow alphanumeric, hyphens, and underscores
        if not all(c.isalnum() or c in ['-', '_'] for c in v):
            raise ValueError("Campaign code must be alphanumeric with hyphens/underscores")
        return v.upper()

    @validator("end_date")
    def validate_end_date(cls, v, values):
        """Validate end date is after start date."""
        if "start_date" in values and v <= values["start_date"]:
            raise ValueError("End date must be after start date")
        return v

    @property
    def is_ongoing(self) -> bool:
        """Check if campaign is currently running."""
        now = datetime.utcnow()
        return (
            self.status == CampaignStatus.ACTIVE and
            self.start_date <= now <= self.end_date
        )

    @property
    def conversion_rate(self) -> float:
        """Calculate campaign conversion rate."""
        if self.total_clicks == 0:
            return 0.0
        return (self.total_conversions / self.total_clicks) * 100

    class Config:
        json_schema_extra = {
            "example": {
                "affiliate_id": "user_123",
                "organization_id": "org_abc",
                "name": "Q1 2025 Flash Sale",
                "description": "Special 10% bonus for Q1 referrals",
                "campaign_code": "Q1_FLASH_2025",
                "start_date": "2025-01-01T00:00:00Z",
                "end_date": "2025-03-31T23:59:59Z",
                "bonus_rate": "0.10",
                "target_referrals": 100,
                "target_sales": "10000.00",
                "prize": "$500 cash bonus",
                "status": "active"
            }
        }
