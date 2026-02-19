"""
Giving/Donation Models for ChurchFlow

This module defines data models for online giving, donations, pledges, and donor management.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class DonationType(str, Enum):
    """Type of donation"""
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    PLEDGE = "pledge"
    TITHE = "tithe"
    OFFERING = "offering"
    MISSION = "mission"
    BUILDING_FUND = "building_fund"
    SPECIAL_PROJECT = "special_project"


class DonationFrequency(str, Enum):
    """Frequency for recurring donations"""
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class DonationStatus(str, Enum):
    """Status of donation"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    """Payment method for donation"""
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    MOBILE_MONEY = "mobile_money"
    CASH = "cash"
    CHECK = "check"


class Donation(BaseModel):
    """
    Donation model representing a single giving transaction.

    Attributes:
        id: Donation ID
        organization_id: Organization receiving donation
        donor_id: User ID of donor (optional for anonymous)
        donor_name: Name of donor
        donor_email: Email of donor
        donor_phone: Phone of donor
        amount: Donation amount
        currency: Currency code (USD, GHS, etc.)
        donation_type: Type of donation
        frequency: Frequency for recurring donations
        category: Custom category/fund
        payment_method: Payment method used
        stripe_payment_intent_id: Stripe payment intent ID
        stripe_customer_id: Stripe customer ID
        status: Donation status
        is_anonymous: Whether donation is anonymous
        is_recurring: Whether this is recurring
        recurring_donation_id: Parent recurring donation ID
        notes: Donor notes/message
        admin_notes: Admin-only notes
        receipt_sent: Whether receipt was sent
        receipt_url: URL to receipt PDF
        tax_deductible: Whether donation is tax deductible
        metadata: Additional donation data
        created_at: When donation was created
        completed_at: When donation was completed
        failed_reason: Reason for failure
    """
    id: Optional[str] = Field(None, alias="_id")
    organization_id: str
    donor_id: Optional[str] = None
    donor_name: str
    donor_email: Optional[str] = None
    donor_phone: Optional[str] = None
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    donation_type: DonationType
    frequency: Optional[DonationFrequency] = None
    category: str = Field(default="General Fund")
    payment_method: PaymentMethod
    stripe_payment_intent_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    status: DonationStatus = DonationStatus.PENDING
    is_anonymous: bool = False
    is_recurring: bool = False
    recurring_donation_id: Optional[str] = None
    notes: Optional[str] = None
    admin_notes: Optional[str] = None
    receipt_sent: bool = False
    receipt_url: Optional[str] = None
    tax_deductible: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    failed_reason: Optional[str] = None

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "organization_id": "org_123",
                "donor_name": "John Doe",
                "donor_email": "john@example.com",
                "amount": 100.00,
                "currency": "USD",
                "donation_type": "tithe",
                "category": "Tithes & Offerings",
                "payment_method": "card",
                "status": "completed",
                "is_anonymous": False,
                "tax_deductible": True
            }
        }


class RecurringDonation(BaseModel):
    """
    Recurring donation setup.

    Attributes:
        id: Recurring donation ID
        organization_id: Organization receiving donations
        donor_id: User ID of donor
        donor_name: Name of donor
        donor_email: Email of donor
        amount: Recurring donation amount
        currency: Currency code
        frequency: How often to charge
        donation_type: Type of donation
        category: Custom category/fund
        payment_method: Payment method
        stripe_subscription_id: Stripe subscription ID
        stripe_customer_id: Stripe customer ID
        status: active, paused, cancelled
        is_active: Whether currently active
        start_date: When recurring started
        end_date: When recurring ends (optional)
        next_payment_date: Next scheduled payment
        last_payment_date: Last successful payment
        total_donations: Number of donations made
        total_amount: Total amount donated
        metadata: Additional data
        created_at: When created
        cancelled_at: When cancelled
    """
    id: Optional[str] = Field(None, alias="_id")
    organization_id: str
    donor_id: str
    donor_name: str
    donor_email: Optional[str] = None
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    frequency: DonationFrequency
    donation_type: DonationType
    category: str = Field(default="General Fund")
    payment_method: PaymentMethod
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    status: str = Field(default="active")
    is_active: bool = True
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None
    next_payment_date: Optional[datetime] = None
    last_payment_date: Optional[datetime] = None
    total_donations: int = 0
    total_amount: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    cancelled_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class Pledge(BaseModel):
    """
    Pledge/commitment for future donation.

    Attributes:
        id: Pledge ID
        organization_id: Organization receiving pledge
        donor_id: User ID making pledge
        donor_name: Name of donor
        donor_email: Email of donor
        pledged_amount: Total amount pledged
        paid_amount: Amount paid so far
        remaining_amount: Amount still owed
        currency: Currency code
        category: What pledge is for
        start_date: When pledge period starts
        end_date: When pledge should be fulfilled
        payment_schedule: Expected payment schedule
        status: pending, active, completed, cancelled
        is_fulfilled: Whether pledge is fully paid
        donations: List of donation IDs for this pledge
        notes: Donor notes
        admin_notes: Admin notes
        metadata: Additional data
        created_at: When created
        fulfilled_at: When fully paid
    """
    id: Optional[str] = Field(None, alias="_id")
    organization_id: str
    donor_id: str
    donor_name: str
    donor_email: Optional[str] = None
    pledged_amount: float = Field(..., gt=0)
    paid_amount: float = 0.0
    remaining_amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    category: str
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None
    payment_schedule: Optional[str] = None
    status: str = Field(default="active")
    is_fulfilled: bool = False
    donations: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    admin_notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    fulfilled_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class GivingCampaign(BaseModel):
    """
    Giving campaign for special projects/fundraising.

    Attributes:
        id: Campaign ID
        organization_id: Organization running campaign
        name: Campaign name
        description: Campaign description
        goal_amount: Fundraising goal
        current_amount: Amount raised so far
        currency: Currency code
        category: Campaign category
        start_date: When campaign starts
        end_date: When campaign ends
        is_active: Whether campaign is active
        is_public: Whether publicly visible
        image_url: Campaign image
        donor_count: Number of unique donors
        donation_count: Total number of donations
        top_donors: List of top donor info
        updates: Campaign updates
        metadata: Additional data
        created_at: When created
        created_by: User who created campaign
    """
    id: Optional[str] = Field(None, alias="_id")
    organization_id: str
    name: str
    description: Optional[str] = None
    goal_amount: float = Field(..., gt=0)
    current_amount: float = 0.0
    currency: str = Field(default="USD", max_length=3)
    category: str
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None
    is_active: bool = True
    is_public: bool = True
    image_url: Optional[str] = None
    donor_count: int = 0
    donation_count: int = 0
    top_donors: List[Dict[str, Any]] = Field(default_factory=list)
    updates: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str

    class Config:
        populate_by_name = True


class DonorProfile(BaseModel):
    """
    Donor profile with giving history.

    Attributes:
        id: Profile ID (matches user_id)
        organization_id: Organization
        user_id: User ID
        donor_name: Full name
        donor_email: Email
        donor_phone: Phone
        total_donated: Lifetime giving amount
        currency: Primary currency
        donation_count: Total donations made
        first_donation_date: Date of first donation
        last_donation_date: Date of last donation
        average_donation: Average donation amount
        largest_donation: Largest single donation
        giving_frequency: How often they give
        preferred_categories: Preferred giving categories
        is_recurring_donor: Whether has recurring donations
        recurring_donations: List of active recurring donation IDs
        pledges: List of active pledge IDs
        tax_id: Tax ID for receipts
        address: Mailing address
        communication_preferences: How they want to be contacted
        metadata: Additional donor data
        created_at: When profile created
        updated_at: Last update
    """
    id: Optional[str] = Field(None, alias="_id")
    organization_id: str
    user_id: str
    donor_name: str
    donor_email: Optional[str] = None
    donor_phone: Optional[str] = None
    total_donated: float = 0.0
    currency: str = Field(default="USD", max_length=3)
    donation_count: int = 0
    first_donation_date: Optional[datetime] = None
    last_donation_date: Optional[datetime] = None
    average_donation: float = 0.0
    largest_donation: float = 0.0
    giving_frequency: Optional[str] = None
    preferred_categories: List[str] = Field(default_factory=list)
    is_recurring_donor: bool = False
    recurring_donations: List[str] = Field(default_factory=list)
    pledges: List[str] = Field(default_factory=list)
    tax_id: Optional[str] = None
    address: Optional[str] = None
    communication_preferences: Dict[str, bool] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
