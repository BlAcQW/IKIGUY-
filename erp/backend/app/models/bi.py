"""
Business Intelligence Models.

Handles reports, dashboards, and KPIs.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field
from enum import Enum

from .base import BaseModel


class ReportType(str, Enum):
    """Report type enumeration."""

    FINANCIAL = "financial"
    SALES = "sales"
    HR = "hr"
    PROJECT = "project"
    CUSTOM = "custom"


class ReportFrequency(str, Enum):
    """Report frequency enumeration."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ON_DEMAND = "on_demand"


class KPITrend(str, Enum):
    """KPI trend enumeration."""

    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class Report(BaseModel):
    """
    Report model.

    Saved reports and report configurations.
    """

    # Report details
    name: str = Field(..., description="Report name")
    report_type: ReportType = Field(..., description="Report type")
    description: Optional[str] = Field(None, description="Report description")

    # Configuration
    data_source: str = Field(..., description="Data source (collection/table name)")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Report filters")
    aggregations: List[Dict[str, Any]] = Field(default_factory=list, description="Aggregations to perform")
    columns: List[str] = Field(default_factory=list, description="Columns to include")

    # Scheduling
    frequency: ReportFrequency = Field(default=ReportFrequency.ON_DEMAND)
    next_run_date: Optional[datetime] = Field(None, description="Next scheduled run")
    last_run_date: Optional[datetime] = Field(None, description="Last run date")

    # Distribution
    recipients: List[str] = Field(default_factory=list, description="Email recipients")
    auto_send: bool = Field(default=False, description="Auto-send on schedule")

    # Access
    is_public: bool = Field(default=False, description="Visible to all users")
    allowed_users: List[str] = Field(default_factory=list, description="Allowed user IDs")
    allowed_roles: List[str] = Field(default_factory=list, description="Allowed roles")


class Dashboard(BaseModel):
    """
    Dashboard model.

    Custom dashboards with widgets and charts.
    """

    # Dashboard details
    name: str = Field(..., description="Dashboard name")
    description: Optional[str] = Field(None, description="Dashboard description")

    # Layout
    layout: Dict[str, Any] = Field(default_factory=dict, description="Dashboard layout configuration")
    widgets: List[Dict[str, Any]] = Field(default_factory=list, description="Dashboard widgets")

    # Access
    is_public: bool = Field(default=False, description="Visible to all users")
    is_default: bool = Field(default=False, description="Default dashboard for organization")
    allowed_users: List[str] = Field(default_factory=list, description="Allowed user IDs")

    # Refresh
    auto_refresh: bool = Field(default=False, description="Auto-refresh enabled")
    refresh_interval: int = Field(default=300, description="Refresh interval in seconds")


class KPI(BaseModel):
    """
    Key Performance Indicator model.

    Tracks important business metrics.
    """

    # KPI details
    name: str = Field(..., description="KPI name")
    description: Optional[str] = Field(None, description="KPI description")
    category: str = Field(..., description="KPI category (sales, finance, hr, etc.)")

    # Measurement
    metric_type: str = Field(..., description="Metric type (revenue, count, percentage, etc.)")
    current_value: float = Field(..., description="Current value")
    target_value: Optional[float] = Field(None, description="Target value")
    unit: str = Field(default="number", description="Unit of measurement")

    # Trend
    trend: KPITrend = Field(default=KPITrend.STABLE, description="Current trend")
    previous_value: Optional[float] = Field(None, description="Previous period value")
    change_percentage: Optional[float] = Field(None, description="Percentage change")

    # Period
    period_start: datetime = Field(..., description="Measurement period start")
    period_end: datetime = Field(..., description="Measurement period end")

    # Calculation
    calculation_formula: Optional[str] = Field(None, description="Formula for calculation")
    data_source: Optional[str] = Field(None, description="Data source query")

    # Display
    display_format: str = Field(default="number", description="Display format (number, currency, percentage)")
    color_coding: Dict[str, Any] = Field(
        default_factory=dict, description="Color coding rules (red/yellow/green thresholds)"
    )

    # Tracking
    history: List[Dict[str, Any]] = Field(default_factory=list, description="Historical values")
