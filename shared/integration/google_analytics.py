"""
Google Analytics Integration Module

This module provides integration with Google Analytics 4 (GA4) for campaign tracking,
user behavior analysis, and performance optimization.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        DateRange,
        Dimension,
        Metric,
        RunReportRequest,
        Filter,
        FilterExpression,
        OrderBy
    )
    from google.oauth2 import service_account
    GOOGLE_ANALYTICS_AVAILABLE = True
except ImportError:
    GOOGLE_ANALYTICS_AVAILABLE = False
    logging.warning("Google Analytics APIs not available. Install google-analytics-data")

logger = logging.getLogger(__name__)


class AnalyticsMetric(Enum):
    """Common Google Analytics metrics."""
    USERS = "totalUsers"
    SESSIONS = "sessions"
    PAGE_VIEWS = "screenPageViews"
    BOUNCE_RATE = "bounceRate"
    SESSION_DURATION = "averageSessionDuration"
    CONVERSIONS = "conversions"
    REVENUE = "totalRevenue"
    TRANSACTIONS = "transactions"
    GOAL_COMPLETIONS = "goalCompletionsAll"


class AnalyticsDimension(Enum):
    """Common Google Analytics dimensions."""
    DATE = "date"
    COUNTRY = "country"
    CITY = "city"
    DEVICE_CATEGORY = "deviceCategory"
    BROWSER = "browser"
    SOURCE = "source"
    MEDIUM = "medium"
    CAMPAIGN = "campaignName"
    PAGE_PATH = "pagePath"
    EVENT_NAME = "eventName"


@dataclass
class GoogleAnalyticsConfig:
    """Configuration for Google Analytics integration."""
    
    property_id: str
    """Google Analytics 4 property ID."""
    
    service_account_file: Optional[str] = None
    """Path to service account JSON file."""
    
    service_account_info: Optional[Dict[str, Any]] = None
    """Service account credentials as dictionary."""
    
    scopes: List[str] = field(default_factory=lambda: [
        "https://www.googleapis.com/auth/analytics.readonly"
    ])
    """OAuth2 scopes for Google Analytics access."""


@dataclass
class AnalyticsReport:
    """Analytics report data structure."""
    
    report_id: str
    """Unique identifier for the report."""
    
    date_range: Dict[str, str]
    """Date range for the report (start_date, end_date)."""
    
    dimensions: List[str]
    """Dimensions included in the report."""
    
    metrics: List[str]
    """Metrics included in the report."""
    
    data: List[Dict[str, Any]]
    """Report data rows."""
    
    row_count: int
    """Number of data rows."""
    
    created_at: datetime = field(default_factory=datetime.now)
    """When the report was created."""


@dataclass
class CampaignData:
    """Campaign performance data."""
    
    campaign_name: str
    """Name of the campaign."""
    
    source: str
    """Traffic source."""
    
    medium: str
    """Traffic medium."""
    
    users: int
    """Number of users."""
    
    sessions: int
    """Number of sessions."""
    
    conversions: int
    """Number of conversions."""
    
    revenue: float
    """Total revenue."""
    
    conversion_rate: float
    """Conversion rate percentage."""
    
    cost_per_conversion: Optional[float] = None
    """Cost per conversion if available."""


@dataclass
class UserBehaviorData:
    """User behavior analysis data."""
    
    page_path: str
    """Page path or URL."""
    
    page_views: int
    """Number of page views."""
    
    unique_users: int
    """Number of unique users."""
    
    average_session_duration: float
    """Average session duration in seconds."""
    
    bounce_rate: float
    """Bounce rate percentage."""
    
    exit_rate: float
    """Exit rate percentage."""


class GoogleAnalyticsIntegration:
    """Google Analytics integration for campaign tracking and optimization."""
    
    def __init__(self, config: GoogleAnalyticsConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Google Analytics client."""
        if not GOOGLE_ANALYTICS_AVAILABLE:
            raise ImportError("Google Analytics libraries not available")
        
        try:
            if self.config.service_account_file:
                credentials = service_account.Credentials.from_service_account_file(
                    self.config.service_account_file,
                    scopes=self.config.scopes
                )
            elif self.config.service_account_info:
                credentials = service_account.Credentials.from_service_account_info(
                    self.config.service_account_info,
                    scopes=self.config.scopes
                )
            else:
                raise ValueError("Either service_account_file or service_account_info must be provided")
            
            self.client = BetaAnalyticsDataClient(credentials=credentials)
            self.logger.info("Google Analytics client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Google Analytics client: {e}")
            raise
    
    async def get_campaign_performance(
        self,
        start_date: datetime,
        end_date: datetime,
        campaign_name: Optional[str] = None
    ) -> List[CampaignData]:
        """
        Get campaign performance data.
        
        Args:
            start_date: Start date for the report
            end_date: End date for the report
            campaign_name: Optional campaign name filter
            
        Returns:
            List of campaign performance data
        """
        try:
            # Build the request
            request = RunReportRequest(
                property=f"properties/{self.config.property_id}",
                date_ranges=[
                    DateRange(
                        start_date=start_date.strftime("%Y-%m-%d"),
                        end_date=end_date.strftime("%Y-%m-%d")
                    )
                ],
                dimensions=[
                    Dimension(name=AnalyticsDimension.CAMPAIGN.value),
                    Dimension(name=AnalyticsDimension.SOURCE.value),
                    Dimension(name=AnalyticsDimension.MEDIUM.value)
                ],
                metrics=[
                    Metric(name=AnalyticsMetric.USERS.value),
                    Metric(name=AnalyticsMetric.SESSIONS.value),
                    Metric(name=AnalyticsMetric.CONVERSIONS.value),
                    Metric(name=AnalyticsMetric.REVENUE.value)
                ]
            )
            
            # Add campaign filter if specified
            if campaign_name:
                request.dimension_filter = FilterExpression(
                    filter=Filter(
                        field_name=AnalyticsDimension.CAMPAIGN.value,
                        string_filter=Filter.StringFilter(value=campaign_name)
                    )
                )
            
            # Run the report
            response = self.client.run_report(request)
            
            # Process results
            campaigns = []
            for row in response.rows:
                campaign_data = CampaignData(
                    campaign_name=row.dimension_values[0].value,
                    source=row.dimension_values[1].value,
                    medium=row.dimension_values[2].value,
                    users=int(row.metric_values[0].value),
                    sessions=int(row.metric_values[1].value),
                    conversions=int(row.metric_values[2].value),
                    revenue=float(row.metric_values[3].value),
                    conversion_rate=(int(row.metric_values[2].value) / int(row.metric_values[1].value) * 100) if int(row.metric_values[1].value) > 0 else 0
                )
                campaigns.append(campaign_data)
            
            return campaigns
            
        except Exception as e:
            self.logger.error(f"Failed to get campaign performance: {e}")
            raise
    
    async def get_user_behavior(
        self,
        start_date: datetime,
        end_date: datetime,
        top_pages: int = 10
    ) -> List[UserBehaviorData]:
        """
        Get user behavior data for top pages.
        
        Args:
            start_date: Start date for the report
            end_date: End date for the report
            top_pages: Number of top pages to return
            
        Returns:
            List of user behavior data
        """
        try:
            # Build the request
            request = RunReportRequest(
                property=f"properties/{self.config.property_id}",
                date_ranges=[
                    DateRange(
                        start_date=start_date.strftime("%Y-%m-%d"),
                        end_date=end_date.strftime("%Y-%m-%d")
                    )
                ],
                dimensions=[
                    Dimension(name=AnalyticsDimension.PAGE_PATH.value)
                ],
                metrics=[
                    Metric(name=AnalyticsMetric.PAGE_VIEWS.value),
                    Metric(name=AnalyticsMetric.USERS.value),
                    Metric(name=AnalyticsMetric.SESSION_DURATION.value),
                    Metric(name=AnalyticsMetric.BOUNCE_RATE.value)
                ],
                order_bys=[
                    OrderBy(
                        metric=OrderBy.MetricOrderBy(
                            metric_name=AnalyticsMetric.PAGE_VIEWS.value
                        ),
                        desc=True
                    )
                ],
                limit=top_pages
            )
            
            # Run the report
            response = self.client.run_report(request)
            
            # Process results
            behavior_data = []
            for row in response.rows:
                behavior = UserBehaviorData(
                    page_path=row.dimension_values[0].value,
                    page_views=int(row.metric_values[0].value),
                    unique_users=int(row.metric_values[1].value),
                    average_session_duration=float(row.metric_values[2].value),
                    bounce_rate=float(row.metric_values[3].value),
                    exit_rate=0.0  # Would need separate query for exit rate
                )
                behavior_data.append(behavior)
            
            return behavior_data
            
        except Exception as e:
            self.logger.error(f"Failed to get user behavior: {e}")
            raise
    
    async def get_traffic_sources(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get traffic sources breakdown.
        
        Args:
            start_date: Start date for the report
            end_date: End date for the report
            
        Returns:
            Traffic sources data
        """
        try:
            # Build the request
            request = RunReportRequest(
                property=f"properties/{self.config.property_id}",
                date_ranges=[
                    DateRange(
                        start_date=start_date.strftime("%Y-%m-%d"),
                        end_date=end_date.strftime("%Y-%m-%d")
                    )
                ],
                dimensions=[
                    Dimension(name=AnalyticsDimension.SOURCE.value),
                    Dimension(name=AnalyticsDimension.MEDIUM.value)
                ],
                metrics=[
                    Metric(name=AnalyticsMetric.USERS.value),
                    Metric(name=AnalyticsMetric.SESSIONS.value),
                    Metric(name=AnalyticsMetric.CONVERSIONS.value)
                ]
            )
            
            # Run the report
            response = self.client.run_report(request)
            
            # Process results
            sources = {}
            for row in response.rows:
                source = row.dimension_values[0].value
                medium = row.dimension_values[1].value
                key = f"{source}/{medium}"
                
                sources[key] = {
                    "source": source,
                    "medium": medium,
                    "users": int(row.metric_values[0].value),
                    "sessions": int(row.metric_values[1].value),
                    "conversions": int(row.metric_values[2].value)
                }
            
            return sources
            
        except Exception as e:
            self.logger.error(f"Failed to get traffic sources: {e}")
            raise
    
    async def get_conversion_funnel(
        self,
        start_date: datetime,
        end_date: datetime,
        funnel_steps: List[str]
    ) -> Dict[str, Any]:
        """
        Get conversion funnel data.
        
        Args:
            start_date: Start date for the report
            end_date: End date for the report
            funnel_steps: List of funnel step event names
            
        Returns:
            Conversion funnel data
        """
        try:
            funnel_data = {}
            
            for i, step in enumerate(funnel_steps):
                # Build request for each funnel step
                request = RunReportRequest(
                    property=f"properties/{self.config.property_id}",
                    date_ranges=[
                        DateRange(
                            start_date=start_date.strftime("%Y-%m-%d"),
                            end_date=end_date.strftime("%Y-%m-%d")
                        )
                    ],
                    dimensions=[
                        Dimension(name=AnalyticsDimension.EVENT_NAME.value)
                    ],
                    metrics=[
                        Metric(name=AnalyticsMetric.USERS.value)
                    ],
                    dimension_filter=FilterExpression(
                        filter=Filter(
                            field_name=AnalyticsDimension.EVENT_NAME.value,
                            string_filter=Filter.StringFilter(value=step)
                        )
                    )
                )
                
                # Run the report
                response = self.client.run_report(request)
                
                # Get the count
                count = 0
                if response.rows:
                    count = int(response.rows[0].metric_values[0].value)
                
                funnel_data[step] = {
                    "step": i + 1,
                    "event_name": step,
                    "users": count
                }
            
            # Calculate conversion rates
            if funnel_data:
                previous_count = None
                for step_data in funnel_data.values():
                    if previous_count is not None and previous_count > 0:
                        step_data["conversion_rate"] = (step_data["users"] / previous_count) * 100
                    else:
                        step_data["conversion_rate"] = 100.0
                    previous_count = step_data["users"]
            
            return funnel_data
            
        except Exception as e:
            self.logger.error(f"Failed to get conversion funnel: {e}")
            raise
    
    async def get_real_time_data(self) -> Dict[str, Any]:
        """
        Get real-time analytics data.
        
        Returns:
            Real-time analytics data
        """
        try:
            # Note: GA4 real-time API is limited compared to Universal Analytics
            # This is a simplified implementation
            
            # Get current date for real-time approximation
            now = datetime.now()
            start_date = now - timedelta(hours=1)
            
            request = RunReportRequest(
                property=f"properties/{self.config.property_id}",
                date_ranges=[
                    DateRange(
                        start_date=start_date.strftime("%Y-%m-%d"),
                        end_date=now.strftime("%Y-%m-%d")
                    )
                ],
                metrics=[
                    Metric(name=AnalyticsMetric.USERS.value),
                    Metric(name=AnalyticsMetric.SESSIONS.value),
                    Metric(name=AnalyticsMetric.PAGE_VIEWS.value)
                ]
            )
            
            response = self.client.run_report(request)
            
            if response.rows:
                row = response.rows[0]
                return {
                    "active_users": int(row.metric_values[0].value),
                    "active_sessions": int(row.metric_values[1].value),
                    "page_views": int(row.metric_values[2].value),
                    "last_updated": now.isoformat()
                }
            
            return {
                "active_users": 0,
                "active_sessions": 0,
                "page_views": 0,
                "last_updated": now.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get real-time data: {e}")
            raise
    
    async def create_custom_report(
        self,
        start_date: datetime,
        end_date: datetime,
        dimensions: List[str],
        metrics: List[str],
        filters: Optional[Dict[str, str]] = None,
        limit: Optional[int] = None
    ) -> AnalyticsReport:
        """
        Create a custom analytics report.
        
        Args:
            start_date: Start date for the report
            end_date: End date for the report
            dimensions: List of dimension names
            metrics: List of metric names
            filters: Optional filters to apply
            limit: Optional row limit
            
        Returns:
            Custom analytics report
        """
        try:
            # Build dimensions
            dimension_objects = [Dimension(name=dim) for dim in dimensions]
            
            # Build metrics
            metric_objects = [Metric(name=metric) for metric in metrics]
            
            # Build request
            request = RunReportRequest(
                property=f"properties/{self.config.property_id}",
                date_ranges=[
                    DateRange(
                        start_date=start_date.strftime("%Y-%m-%d"),
                        end_date=end_date.strftime("%Y-%m-%d")
                    )
                ],
                dimensions=dimension_objects,
                metrics=metric_objects
            )
            
            # Add filters if provided
            if filters:
                filter_expressions = []
                for field, value in filters.items():
                    filter_expressions.append(
                        Filter(
                            field_name=field,
                            string_filter=Filter.StringFilter(value=value)
                        )
                    )
                
                if len(filter_expressions) == 1:
                    request.dimension_filter = FilterExpression(filter=filter_expressions[0])
                else:
                    request.dimension_filter = FilterExpression(
                        and_group=FilterExpression.FilterExpressionList(
                            expressions=[FilterExpression(filter=f) for f in filter_expressions]
                        )
                    )
            
            # Add limit if provided
            if limit:
                request.limit = limit
            
            # Run the report
            response = self.client.run_report(request)
            
            # Process results
            data = []
            for row in response.rows:
                row_data = {}
                
                # Add dimensions
                for i, dim in enumerate(dimensions):
                    row_data[dim] = row.dimension_values[i].value
                
                # Add metrics
                for i, metric in enumerate(metrics):
                    row_data[metric] = row.metric_values[i].value
                
                data.append(row_data)
            
            # Create report object
            report = AnalyticsReport(
                report_id=f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                date_range={
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                },
                dimensions=dimensions,
                metrics=metrics,
                data=data,
                row_count=len(data)
            )
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to create custom report: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Google Analytics integration.
        
        Returns:
            Health check results
        """
        try:
            # Try to get a simple report to test connectivity
            now = datetime.now()
            start_date = now - timedelta(days=1)
            
            request = RunReportRequest(
                property=f"properties/{self.config.property_id}",
                date_ranges=[
                    DateRange(
                        start_date=start_date.strftime("%Y-%m-%d"),
                        end_date=now.strftime("%Y-%m-%d")
                    )
                ],
                metrics=[
                    Metric(name=AnalyticsMetric.USERS.value)
                ]
            )
            
            response = self.client.run_report(request)
            
            return {
                "status": "healthy",
                "property_id": self.config.property_id,
                "client_initialized": self.client is not None,
                "test_query_successful": True,
                "last_checked": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "property_id": self.config.property_id,
                "client_initialized": self.client is not None,
                "test_query_successful": False,
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }

