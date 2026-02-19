"""
Streak tracking models for InkWave.

Defines daily listening streak data and tracking.
"""

from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, Field


class ListeningStreak(BaseModel):
    """
    User's daily listening streak.

    Tracks consecutive days of listening activity.
    """

    current_days: int = Field(default=0, description="Current streak length in days")
    longest_days: int = Field(default=0, description="Longest streak ever achieved")
    last_activity_date: Optional[date] = Field(None, description="Last date user listened (YYYY-MM-DD)")
    streak_start_date: Optional[date] = Field(None, description="Date current streak started")
    total_active_days: int = Field(default=0, description="Total days with listening activity")

    # Metadata
    last_checked: datetime = Field(default_factory=datetime.utcnow, description="Last time streak was checked")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Config:
        """Pydantic config."""
        json_encoders = {
            date: lambda v: v.isoformat() if v else None,
            datetime: lambda v: v.isoformat() if v else None
        }
