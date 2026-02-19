"""
Affiliate Program API Schemas.

Request and response schemas for affiliate API endpoints.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

from ..models.affiliate import PayoutMethod, PayoutStatus, CommissionStatus


# ============================================================================
# Request Schemas
# ============================================================================

class JoinProgramRequest(BaseModel):
    """Request to join affiliate program."""
    upline_referral_code: Optional[str] = Field(
        None,
        description="Referral code of upline affiliate (optional)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "upline_referral_code": "JOHN001"
            }
        }


class UpdateProfileRequest(BaseModel):
    """Request to update affiliate profile settings."""
    payout_method: Optional[PayoutMethod] = Field(None, description="Preferred payout method")
    payout_threshold: Optional[Decimal] = Field(None, description="Minimum payout threshold")
    payment_method_id: Optional[str] = Field(None, description="Payment method ID")
    notification_preferences: Optional[Dict[str, Any]] = Field(None, description="Notification preferences")

    @validator("payout_threshold")
    def validate_payout_threshold(cls, v):
        """Validate payout threshold is reasonable."""
        if v is not None and (v < 10 or v > 10000):
            raise ValueError("Payout threshold must be between $10 and $10,000")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "payout_method": "wallet_credit",
                "payout_threshold": "50.00",
                "payment_method_id": "pm_123456",
                "notification_preferences": {
                    "email_notifications": True,
                    "sms_notifications": False
                }
            }
        }


class CreateReferralLinkRequest(BaseModel):
    """Request to create custom referral link with UTM parameters."""
    utm_source: Optional[str] = Field(None, description="UTM source parameter")
    utm_campaign: Optional[str] = Field(None, description="UTM campaign parameter")
    utm_medium: Optional[str] = Field(None, description="UTM medium parameter")

    class Config:
        json_schema_extra = {
            "example": {
                "utm_source": "instagram",
                "utm_campaign": "q1_2025",
                "utm_medium": "social"
            }
        }


class AttributeSignupRequest(BaseModel):
    """Request to attribute a signup to an affiliate."""
    user_id: str = Field(..., description="New user ID")
    organization_id: str = Field(..., description="Organization ID")
    referral_code: str = Field(..., description="Referral code")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "organization_id": "org456",
                "referral_code": "JOHN001"
            }
        }


class ProcessCommissionRequest(BaseModel):
    """Request to process commission for a transaction."""
    transaction_id: str = Field(..., description="Transaction ID")
    user_id: str = Field(..., description="User ID who made the purchase")
    organization_id: str = Field(..., description="Organization ID")
    amount: Decimal = Field(..., description="Transaction amount")
    currency: str = Field("USD", description="Currency code")
    description: Optional[str] = Field(None, description="Transaction description")

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "txn_123",
                "user_id": "user456",
                "organization_id": "org789",
                "amount": "100.00",
                "currency": "USD",
                "description": "Wallet top-up"
            }
        }


class PayoutRequestCreate(BaseModel):
    """Request to create a payout request."""
    amount: Decimal = Field(..., description="Amount to payout")
    payout_method: PayoutMethod = Field(..., description="Payout method")
    payment_method_id: Optional[str] = Field(
        None,
        description="Payment method ID (required for non-wallet payouts)"
    )

    @validator("amount")
    def validate_amount(cls, v):
        """Validate payout amount is reasonable."""
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        if v > 100000:
            raise ValueError("Maximum payout amount is $100,000")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "amount": "150.00",
                "payout_method": "wallet_credit"
            }
        }


# ============================================================================
# Response Schemas
# ============================================================================

class AffiliateProfileResponse(BaseModel):
    """Affiliate profile response."""
    id: str
    user_id: str
    organization_id: str
    referral_code: str
    upline_id: Optional[str]
    tier_level: int

    # Commission rates
    tier1_commission_rate: Decimal
    tier2_commission_rate: Decimal
    tier3_commission_rate: Decimal

    # Statistics
    total_referrals: int
    direct_referrals: int
    total_sales: Decimal
    total_commissions_earned: Decimal
    total_commissions_paid: Decimal
    pending_commissions: Decimal

    # Status
    is_active: bool
    is_verified: bool
    joined_program_at: datetime
    last_referral_at: Optional[datetime]

    # Payout settings
    payout_method: PayoutMethod
    payout_threshold: Decimal
    payment_method_id: Optional[str]
    notification_preferences: Optional[Dict[str, Any]] = None

    # Metadata
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "aff_123",
                "user_id": "user_123",
                "organization_id": "org_abc",
                "referral_code": "ALFRED001",
                "upline_id": "user_456",
                "tier_level": 1,
                "tier1_commission_rate": "0.15",
                "tier2_commission_rate": "0.08",
                "tier3_commission_rate": "0.03",
                "total_referrals": 25,
                "direct_referrals": 10,
                "total_sales": "5000.00",
                "total_commissions_earned": "750.00",
                "total_commissions_paid": "500.00",
                "pending_commissions": "250.00",
                "is_active": True,
                "is_verified": True,
                "payout_method": "wallet_credit",
                "payout_threshold": "20.00"
            }
        }


class AffiliateStatsResponse(BaseModel):
    """Affiliate statistics dashboard response."""
    # Earnings
    total_earned: Decimal
    total_paid: Decimal
    pending_commissions: Decimal
    this_month_earnings: Decimal
    last_month_earnings: Decimal

    # Referrals
    total_referrals: int
    direct_referrals: int
    tier2_referrals: int
    tier3_referrals: int

    # Performance
    total_sales: Decimal
    conversion_rate: float
    average_commission_per_referral: Decimal

    # Activity
    last_referral_at: Optional[datetime]
    last_commission_at: Optional[datetime]

    class Config:
        json_schema_extra = {
            "example": {
                "total_earned": "750.00",
                "total_paid": "500.00",
                "pending_commissions": "250.00",
                "this_month_earnings": "125.50",
                "last_month_earnings": "342.80",
                "total_referrals": 25,
                "direct_referrals": 10,
                "tier2_referrals": 10,
                "tier3_referrals": 5,
                "total_sales": "5000.00",
                "conversion_rate": 16.67,
                "average_commission_per_referral": "30.00"
            }
        }


class ReferralLinkResponse(BaseModel):
    """Referral link response."""
    id: str
    referral_code: str
    url: str
    utm_source: Optional[str]
    utm_campaign: Optional[str]
    utm_medium: Optional[str]
    click_count: int
    conversion_count: int
    conversion_rate: float
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "link_123",
                "referral_code": "ALFRED001",
                "url": "https://kasaai.ailabsafrica.com?ref=ALFRED001&utm_source=instagram",
                "utm_source": "instagram",
                "utm_campaign": "q1_2025",
                "click_count": 150,
                "conversion_count": 25,
                "conversion_rate": 16.67
            }
        }


class ReferralCodeResponse(BaseModel):
    """Referral code and base URL response."""
    referral_code: str
    base_url: str
    full_url: str

    class Config:
        json_schema_extra = {
            "example": {
                "referral_code": "ALFRED001",
                "base_url": "https://kasaai.ailabsafrica.com",
                "full_url": "https://kasaai.ailabsafrica.com?ref=ALFRED001"
            }
        }


class ReferralResponse(BaseModel):
    """Individual referral response."""
    user_id: str
    referred_user_id: Optional[str] = None  # Alias for user_id
    name: Optional[str] = None
    email: Optional[str] = None
    joined_at: datetime
    tier_level: int
    total_purchases: Decimal
    commissions_earned_from_user: Decimal
    first_purchase_at: Optional[datetime] = None
    is_active: bool

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_456",
                "name": "John Doe",
                "email": "john@example.com",
                "joined_at": "2025-11-01T10:00:00Z",
                "tier_level": 1,
                "total_purchases": "500.00",
                "commissions_earned_from_user": "75.00",
                "is_active": True
            }
        }


class NetworkStatsResponse(BaseModel):
    """Network statistics response."""
    tier1_count: int
    tier2_count: int
    tier3_count: int
    total_network_size: int
    total_network_sales: Decimal
    total_sales: Decimal  # Alias for compatibility
    total_network_commissions: Decimal
    total_commissions: Decimal  # Alias for compatibility

    class Config:
        json_schema_extra = {
            "example": {
                "tier1_count": 10,
                "tier2_count": 25,
                "tier3_count": 50,
                "total_network_size": 85,
                "total_network_sales": "15000.00",
                "total_network_commissions": "1250.00",
                "total_commissions": "1250.00"
            }
        }


class CommissionRecordResponse(BaseModel):
    """Commission record response."""
    id: str
    referred_user_name: Optional[str]
    referred_user_email: Optional[str]
    sale_amount: Decimal
    commission_rate: Decimal
    commission_amount: Decimal
    tier_level: int
    status: CommissionStatus
    created_at: datetime
    approved_at: Optional[datetime]
    paid_at: Optional[datetime]

    class Config:
        json_schema_extra = {
            "example": {
                "id": "comm_123",
                "referred_user_name": "Jane Smith",
                "referred_user_email": "jane@example.com",
                "sale_amount": "100.00",
                "commission_rate": "0.15",
                "commission_amount": "15.00",
                "tier_level": 1,
                "status": "approved",
                "created_at": "2025-11-15T10:00:00Z"
            }
        }


class CommissionSummaryResponse(BaseModel):
    """Commission summary by period."""
    total_earned: Decimal
    total_by_tier: Dict[int, Decimal]
    total_by_month: Dict[str, Decimal]
    total_by_status: Dict[str, Decimal]

    class Config:
        json_schema_extra = {
            "example": {
                "total_earned": "750.00",
                "total_by_tier": {
                    "1": "500.00",
                    "2": "200.00",
                    "3": "50.00"
                },
                "total_by_month": {
                    "2025-11": "250.00",
                    "2025-10": "342.80",
                    "2025-09": "157.20"
                },
                "total_by_status": {
                    "approved": "250.00",
                    "paid": "500.00"
                }
            }
        }


class PayoutRequestResponse(BaseModel):
    """Payout request response."""
    id: str
    amount: Decimal
    payout_method: PayoutMethod
    processing_fee: Decimal
    net_amount: Decimal
    status: PayoutStatus
    created_at: datetime
    processed_at: Optional[datetime]
    notes: Optional[str]
    failure_reason: Optional[str]

    class Config:
        json_schema_extra = {
            "example": {
                "id": "payout_123",
                "amount": "100.00",
                "payout_method": "wallet_credit",
                "processing_fee": "0.00",
                "net_amount": "100.00",
                "status": "completed",
                "created_at": "2025-11-15T10:00:00Z",
                "processed_at": "2025-11-15T10:05:00Z"
            }
        }


class TrackReferralResponse(BaseModel):
    """Track referral click response."""
    success: bool
    referral_code: str
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "referral_code": "ALFRED001",
                "message": "Referral click tracked successfully"
            }
        }


class AttributeSignupResponse(BaseModel):
    """Attribute signup response."""
    success: bool
    id: Optional[str] = None  # Attribution record ID
    referred_user_id: Optional[str] = None  # User who was referred
    affiliate_id: Optional[str] = None  # Affiliate who gets credit
    referral_code: str
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "id": "attr_123",
                "referred_user_id": "user_789",
                "affiliate_id": "user_456",
                "referral_code": "ALFRED001",
                "message": "Signup attributed successfully"
            }
        }


class ProcessCommissionResponse(BaseModel):
    """Process commission response (internal endpoint)."""
    success: bool
    commissions: List[Dict[str, Any]]  # List of commission records
    commissions_created: List[Dict[str, Any]]  # Alias for compatibility
    total_commission_amount: Decimal

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "commissions_created": [
                    {
                        "affiliate_id": "user_123",
                        "tier_level": 1,
                        "commission_amount": "15.00"
                    },
                    {
                        "affiliate_id": "user_456",
                        "tier_level": 2,
                        "commission_amount": "8.00"
                    }
                ],
                "total_commission_amount": "23.00"
            }
        }


# ============================================================================
# List Responses (Paginated)
# ============================================================================

class ReferralListResponse(BaseModel):
    """Paginated list of referrals."""
    items: List[ReferralResponse]
    total: int
    limit: int
    offset: int

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 25,
                "limit": 50,
                "offset": 0
            }
        }


class CommissionListResponse(BaseModel):
    """Paginated list of commission records."""
    items: List[CommissionRecordResponse]
    total: int
    limit: int
    offset: int

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "limit": 50,
                "offset": 0
            }
        }


class PayoutListResponse(BaseModel):
    """Paginated list of payout requests."""
    items: List[PayoutRequestResponse]
    total: int
    limit: int
    offset: int

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 10,
                "limit": 50,
                "offset": 0
            }
        }
