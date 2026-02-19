"""
Giving API Schemas for ChurchFlow

Request/response schemas for online giving endpoints.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from app.models.giving import (
    DonationType,
    DonationFrequency,
    DonationStatus,
    PaymentMethod
)


# ==================== Donation Schemas ====================

class CreateDonationRequest(BaseModel):
    """Request to create a new donation"""
    donor_name: str = Field(..., min_length=1, max_length=200)
    donor_email: Optional[EmailStr] = None
    donor_phone: Optional[str] = None
    amount: float = Field(..., gt=0, description="Donation amount")
    currency: str = Field(default="USD", max_length=3)
    donation_type: DonationType
    category: str = Field(default="General Fund")
    payment_method: PaymentMethod
    is_anonymous: bool = False
    notes: Optional[str] = Field(None, max_length=1000)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DonationResponse(BaseModel):
    """Donation response"""
    id: str = Field(..., alias="_id")
    organization_id: str
    donor_id: Optional[str]
    donor_name: str
    donor_email: Optional[str]
    donor_phone: Optional[str]
    amount: float
    currency: str
    donation_type: DonationType
    category: str
    payment_method: PaymentMethod
    status: DonationStatus
    is_anonymous: bool
    is_recurring: bool
    stripe_payment_intent_id: Optional[str]
    receipt_sent: bool
    receipt_url: Optional[str]
    tax_deductible: bool
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        populate_by_name = True


class ProcessDonationRequest(BaseModel):
    """Request to process a donation payment"""
    donation_id: str
    stripe_payment_method_id: str


# ==================== Recurring Donation Schemas ====================

class CreateRecurringDonationRequest(BaseModel):
    """Request to create recurring donation"""
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    frequency: DonationFrequency
    donation_type: DonationType
    category: str = Field(default="General Fund")
    payment_method: PaymentMethod
    stripe_payment_method_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class RecurringDonationResponse(BaseModel):
    """Recurring donation response"""
    id: str = Field(..., alias="_id")
    organization_id: str
    donor_id: str
    donor_name: str
    amount: float
    currency: str
    frequency: DonationFrequency
    donation_type: DonationType
    category: str
    status: str
    is_active: bool
    next_payment_date: Optional[datetime]
    total_donations: int
    total_amount: float
    created_at: datetime

    class Config:
        populate_by_name = True


class UpdateRecurringDonationRequest(BaseModel):
    """Request to update recurring donation"""
    amount: Optional[float] = Field(None, gt=0)
    frequency: Optional[DonationFrequency] = None
    category: Optional[str] = None


# ==================== Pledge Schemas ====================

class CreatePledgeRequest(BaseModel):
    """Request to create a pledge"""
    pledged_amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    category: str
    end_date: Optional[datetime] = None
    payment_schedule: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)


class PledgeResponse(BaseModel):
    """Pledge response"""
    id: str = Field(..., alias="_id")
    organization_id: str
    donor_id: str
    donor_name: str
    pledged_amount: float
    paid_amount: float
    remaining_amount: float
    currency: str
    category: str
    start_date: datetime
    end_date: Optional[datetime]
    status: str
    is_fulfilled: bool
    donation_count: int
    created_at: datetime

    class Config:
        populate_by_name = True


class RecordPledgePaymentRequest(BaseModel):
    """Request to record a pledge payment"""
    pledge_id: str
    amount: float = Field(..., gt=0)
    payment_method: PaymentMethod
    stripe_payment_method_id: Optional[str] = None
    notes: Optional[str] = None


# ==================== Campaign Schemas ====================

class CreateCampaignRequest(BaseModel):
    """Request to create giving campaign"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    goal_amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    category: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_public: bool = True
    image_url: Optional[str] = None


class CampaignResponse(BaseModel):
    """Campaign response"""
    id: str = Field(..., alias="_id")
    organization_id: str
    name: str
    description: Optional[str]
    goal_amount: float
    current_amount: float
    currency: str
    category: str
    start_date: datetime
    end_date: Optional[datetime]
    is_active: bool
    is_public: bool
    image_url: Optional[str]
    donor_count: int
    donation_count: int
    progress_percentage: float
    created_at: datetime

    class Config:
        populate_by_name = True


class UpdateCampaignRequest(BaseModel):
    """Request to update campaign"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    goal_amount: Optional[float] = Field(None, gt=0)
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    image_url: Optional[str] = None


class CampaignUpdateRequest(BaseModel):
    """Request to add campaign update"""
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=2000)


# ==================== Donor Profile Schemas ====================

class DonorProfileResponse(BaseModel):
    """Donor profile response"""
    id: str = Field(..., alias="_id")
    organization_id: str
    user_id: str
    donor_name: str
    donor_email: Optional[str]
    donor_phone: Optional[str]
    total_donated: float
    currency: str
    donation_count: int
    first_donation_date: Optional[datetime]
    last_donation_date: Optional[datetime]
    average_donation: float
    largest_donation: float
    is_recurring_donor: bool
    active_recurring_count: int
    active_pledge_count: int
    created_at: datetime

    class Config:
        populate_by_name = True


class UpdateDonorProfileRequest(BaseModel):
    """Request to update donor profile"""
    donor_name: Optional[str] = Field(None, min_length=1, max_length=200)
    donor_email: Optional[EmailStr] = None
    donor_phone: Optional[str] = None
    tax_id: Optional[str] = None
    address: Optional[str] = None
    communication_preferences: Optional[Dict[str, bool]] = None


# ==================== Analytics Schemas ====================

class GivingAnalyticsResponse(BaseModel):
    """Giving analytics for organization"""
    organization_id: str
    period_start: datetime
    period_end: datetime
    total_donations: int
    total_amount: float
    currency: str
    average_donation: float
    unique_donors: int
    new_donors: int
    recurring_donors: int
    donation_types: Dict[str, float]
    top_categories: List[Dict[str, Any]]
    monthly_trend: List[Dict[str, Any]]
    donor_retention_rate: float
    active_campaigns: int
    total_pledges: float
    fulfilled_pledges: float


class DonationReceiptResponse(BaseModel):
    """Tax receipt for donation"""
    donation_id: str
    organization_name: str
    donor_name: str
    donor_address: Optional[str]
    donor_tax_id: Optional[str]
    amount: float
    currency: str
    donation_date: datetime
    tax_deductible: bool
    receipt_number: str
    receipt_url: str
    organization_tax_id: Optional[str]


# ==================== List Responses ====================

class DonationListResponse(BaseModel):
    """Paginated donation list"""
    donations: List[DonationResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class RecurringDonationListResponse(BaseModel):
    """Paginated recurring donation list"""
    recurring_donations: List[RecurringDonationResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class PledgeListResponse(BaseModel):
    """Paginated pledge list"""
    pledges: List[PledgeResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class CampaignListResponse(BaseModel):
    """Paginated campaign list"""
    campaigns: List[CampaignResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
