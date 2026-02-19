"""
Member Portal Schemas for ChurchFlow

Request/response schemas for member self-service portal.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr


# ==================== Profile Schemas ====================

class MemberProfileResponse(BaseModel):
    """Member's own profile information"""
    id: str = Field(..., alias="_id")
    supabase_id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    name: Optional[str] = None  # Legacy
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    occupation: Optional[str] = None
    employer: Optional[str] = None
    marital_status: Optional[str] = None
    spouse_name: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    branch_id: Optional[str] = None
    member_status: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    volunteer_roles: List[str] = Field(default_factory=list)
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = None
    joined_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class UpdateMemberProfileRequest(BaseModel):
    """Request to update member profile"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    occupation: Optional[str] = None
    employer: Optional[str] = None
    marital_status: Optional[str] = None
    spouse_name: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    profile_picture_url: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """Request to change password"""
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


# ==================== Preferences Schemas ====================

class NotificationPreferences(BaseModel):
    """Notification preferences"""
    email_notifications: bool = True
    sms_notifications: bool = True
    push_notifications: bool = True
    event_reminders: bool = True
    giving_receipts: bool = True
    newsletter: bool = True
    prayer_requests: bool = True


class PrivacyPreferences(BaseModel):
    """Privacy preferences"""
    show_profile_in_directory: bool = True
    show_phone_number: bool = False
    show_email: bool = False
    show_address: bool = False
    allow_contact_from_members: bool = True


class MemberPreferencesResponse(BaseModel):
    """Member preferences"""
    user_id: str
    notifications: NotificationPreferences = Field(default_factory=NotificationPreferences)
    privacy: PrivacyPreferences = Field(default_factory=PrivacyPreferences)
    language: str = "en"
    timezone: str = "UTC"
    updated_at: datetime


class UpdatePreferencesRequest(BaseModel):
    """Request to update preferences"""
    notifications: Optional[NotificationPreferences] = None
    privacy: Optional[PrivacyPreferences] = None
    language: Optional[str] = None
    timezone: Optional[str] = None


# ==================== Activity Schemas ====================

class MemberActivityResponse(BaseModel):
    """Member's recent activity"""
    conferences_attended: int
    events_registered: int
    donations_made: int
    volunteer_hours: float
    cell_group: Optional[str] = None
    last_attendance: Optional[datetime] = None
    last_donation: Optional[datetime] = None
    member_since: Optional[datetime] = None


class ConferenceRegistrationSummary(BaseModel):
    """Summary of member's conference registrations"""
    conference_id: str
    conference_name: str
    start_date: datetime
    end_date: datetime
    registration_date: datetime
    checked_in: bool
    qr_code: Optional[str] = None


class MemberDashboardResponse(BaseModel):
    """Member dashboard overview"""
    profile: MemberProfileResponse
    activity: MemberActivityResponse
    upcoming_conferences: List[ConferenceRegistrationSummary]
    recent_donations: List[Any]  # Will use giving schemas
    notification_count: int
    unread_messages: int


# ==================== Directory Schemas ====================

class MemberDirectoryEntry(BaseModel):
    """Public member directory entry"""
    id: str = Field(..., alias="_id")
    full_name: str
    profile_picture_url: Optional[str] = None
    email: Optional[str] = None  # Only if privacy allows
    phone: Optional[str] = None  # Only if privacy allows
    cell_group: Optional[str] = None
    volunteer_roles: List[str] = Field(default_factory=list)
    joined_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class MemberDirectoryResponse(BaseModel):
    """Paginated member directory"""
    members: List[MemberDirectoryEntry]
    total: int
    page: int
    page_size: int
    has_more: bool


# ==================== Volunteer Schemas ====================

class VolunteerOpportunity(BaseModel):
    """Volunteer opportunity"""
    id: str
    title: str
    description: str
    department: str
    time_commitment: str
    requirements: List[str]
    contact_person: str
    is_active: bool
    created_at: datetime


class VolunteerApplication(BaseModel):
    """Member's volunteer application"""
    opportunity_id: str
    message: str
    availability: str
    experience: Optional[str] = None


class MyVolunteerRolesResponse(BaseModel):
    """Member's current volunteer roles"""
    active_roles: List[Dict[str, Any]]
    applications_pending: int
    total_hours: float
    departments: List[str]


# ==================== Event Registration Schemas ====================

class MyRegistrationsResponse(BaseModel):
    """Member's event registrations"""
    upcoming: List[ConferenceRegistrationSummary]
    past: List[ConferenceRegistrationSummary]
    total_registered: int
    total_attended: int
    attendance_rate: float


# ==================== Small Groups / Cell Groups Schemas ====================

class CellGroupMembership(BaseModel):
    """Member's cell group membership"""
    cell_group_id: str
    cell_group_name: str
    leader_name: str
    meeting_day: str
    meeting_time: str
    location: str
    members_count: int
    joined_at: datetime


# ==================== Prayer Request Schemas ====================

class CreatePrayerRequestRequest(BaseModel):
    """Request to create prayer request"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    is_anonymous: bool = False
    is_private: bool = False  # Private = only leadership sees
    category: Optional[str] = None


class PrayerRequestResponse(BaseModel):
    """Prayer request"""
    id: str = Field(..., alias="_id")
    user_id: str
    title: str
    description: str
    is_anonymous: bool
    is_private: bool
    category: Optional[str] = None
    status: str  # "active", "answered", "archived"
    prayer_count: int
    created_at: datetime
    answered_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class MyPrayerRequestsResponse(BaseModel):
    """Member's prayer requests"""
    my_requests: List[PrayerRequestResponse]
    prayers_received: int
    answered_count: int
