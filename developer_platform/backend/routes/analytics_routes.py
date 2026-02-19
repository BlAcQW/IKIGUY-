"""
Analytics Routes for KasaAI Developer Platform.

This module provides analytics-related API endpoints using the DeveloperAnalyticsService.
"""

from fastapi import APIRouter, Header
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import logging

from ..services.analytics_service import DeveloperAnalyticsService
from ..api_consolidation import (
    StandardAPIResponse,
    create_success_response,
    handle_api_exception,
)

# Create router
router = APIRouter(prefix="/v1/analytics", tags=["Analytics Services"])

# Initialize analytics service
analytics_service = DeveloperAnalyticsService()

# Request models
class CreateDashboardRequest(BaseModel):
    """Request model for creating a dashboard."""
    dashboard_config: Dict[str, Any]
    metrics: List[Dict[str, Any]]

class GenerateReportRequest(BaseModel):
    """Request model for generating a report."""
    report_type: str
    data: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None

class TrackKPIRequest(BaseModel):
    """Request model for tracking a KPI."""
    kpi_name: str
    value: float
    category: str
    metadata: Optional[Dict[str, Any]] = None

class PredictCallOutcomeRequest(BaseModel):
    """Request model for predicting call outcome."""
    call_data: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None

@router.post("/dashboard/create", response_model=StandardAPIResponse)
async def create_dashboard(
    request: CreateDashboardRequest,
    x_api_key: str = Header(...)
) -> StandardAPIResponse:
    """Create a dashboard."""
    try:
        result = await analytics_service.create_dashboard(request.dashboard_config, request.metrics)

        return create_success_response(
            data=result,
            message="Dashboard created successfully"
        )
    except Exception as e:
        return handle_api_exception(e, "Failed to create dashboard")

@router.post("/report/generate", response_model=StandardAPIResponse)
async def generate_report(
    request: GenerateReportRequest,
    x_api_key: str = Header(...)
) -> StandardAPIResponse:
    """Generate a report."""
    try:
        result = await analytics_service.generate_report(request.report_type, request.data, request.config)

        return create_success_response(
            data=result,
            message="Report generated successfully"
        )
    except Exception as e:
        return handle_api_exception(e, "Failed to generate report")

@router.post("/kpi/track", response_model=StandardAPIResponse)
async def track_kpi(
    request: TrackKPIRequest,
    x_api_key: str = Header(...)
) -> StandardAPIResponse:
    """Track a KPI."""
    try:
        result = await analytics_service.track_kpi(request.kpi_name, request.value, request.category, request.metadata)

        return create_success_response(
            data=result,
            message="KPI tracked successfully"
        )
    except Exception as e:
        return handle_api_exception(e, "Failed to track KPI")

@router.post("/prediction/call-outcome", response_model=StandardAPIResponse)
async def predict_call_outcome(
    request: PredictCallOutcomeRequest,
    x_api_key: str = Header(...)
) -> StandardAPIResponse:
    """Predict call outcome."""
    try:
        result = await analytics_service.predict_call_outcome(request.call_data, request.config)

        return create_success_response(
            data=result,
            message="Call outcome prediction completed successfully"
        )
    except Exception as e:
        return handle_api_exception(e, "Failed to predict call outcome")

@router.get("/config", response_model=StandardAPIResponse)
async def get_analytics_config(x_api_key: str = Header(...)) -> StandardAPIResponse:
    """Get analytics service configuration."""
    try:
        result = await analytics_service.get_developer_analytics_config()
        
        return create_success_response(
            data=result,
            message="Analytics configuration retrieved successfully"
        )
    except Exception as e:
        return handle_api_exception(e, "Failed to get analytics configuration")
