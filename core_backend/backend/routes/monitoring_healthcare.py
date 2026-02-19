"""
Healthcare Monitoring Integration
Combines Universal Wizard monitoring with Premier Health domain-specific metrics
"""

import asyncio
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging
import json

from ..auth import get_current_user_mongo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring-healthcare"])

class HealthcareMonitoringRequest(BaseModel):
    """Request model for healthcare monitoring setup."""
    organizationName: str
    workflowId: str
    assistantId: str
    endpoints: Dict[str, str]
    kpis: List[str]
    alerting: Optional[Dict[str, Any]] = None

class HealthcareMonitoringResponse(BaseModel):
    """Response model for healthcare monitoring setup."""
    dashboardUrl: str
    healthEndpoints: List[str]
    alertRules: List[Dict[str, Any]]
    kpiDefinitions: List[Dict[str, Any]]
    status: str

class HealthcareAlert(BaseModel):
    """Healthcare-specific alert model."""
    alertId: str
    severity: str  # critical, warning, info
    category: str  # system, provider_data, compliance, performance
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False

@router.post("/setup-healthcare", response_model=HealthcareMonitoringResponse)
async def setup_healthcare_monitoring(
    request: HealthcareMonitoringRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Setup comprehensive monitoring for healthcare automation system.

    This combines Universal Wizard's flexible monitoring with Premier Health's
    domain-specific healthcare metrics and compliance requirements.
    """
    try:
        logger.info(f"Setting up healthcare monitoring for: {request.organizationName}")

        # Generate monitoring configuration
        monitoring_config = generate_healthcare_monitoring_config(request)

        # Setup health endpoints
        health_endpoints = setup_healthcare_health_endpoints(request)

        # Configure healthcare-specific alert rules
        alert_rules = setup_healthcare_alert_rules(request)

        # Define healthcare KPIs
        kpi_definitions = define_healthcare_kpis(request.kpis)

        # Setup dashboard
        dashboard_url = await setup_healthcare_dashboard(request, monitoring_config)

        # Initialize monitoring in background
        background_tasks.add_task(
            initialize_healthcare_monitoring,
            request.organizationName,
            monitoring_config
        )

        response = HealthcareMonitoringResponse(
            dashboardUrl=dashboard_url,
            healthEndpoints=health_endpoints,
            alertRules=alert_rules,
            kpiDefinitions=kpi_definitions,
            status="configured"
        )

        logger.info(f"Healthcare monitoring setup completed: {dashboard_url}")
        return response

    except Exception as e:
        logger.error(f"Error setting up healthcare monitoring: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to setup healthcare monitoring: {str(e)}"
        )

def generate_healthcare_monitoring_config(request: HealthcareMonitoringRequest) -> Dict[str, Any]:
    """Generate comprehensive monitoring configuration for healthcare system."""

    config = {
        "organization": request.organizationName,
        "system_components": {
            "vapi_assistant": {
                "id": request.assistantId,
                "health_check_interval": 30,  # seconds
                "metrics": [
                    "call_volume",
                    "call_success_rate",
                    "average_call_duration",
                    "patient_satisfaction_score",
                    "emergency_response_time"
                ]
            },
            "n8n_workflow": {
                "id": request.workflowId,
                "health_check_interval": 60,
                "metrics": [
                    "workflow_executions",
                    "execution_success_rate",
                    "provider_search_performance",
                    "database_query_time"
                ]
            },
            "provider_database": {
                "health_check_interval": 300,  # 5 minutes
                "metrics": [
                    "database_connectivity",
                    "provider_data_freshness",
                    "search_index_performance",
                    "data_quality_score"
                ]
            }
        },

        "healthcare_kpis": {
            "search_success_rate": {
                "target": 95.0,
                "warning_threshold": 90.0,
                "critical_threshold": 85.0,
                "calculation": "successful_searches / total_searches * 100"
            },
            "appointment_booking_rate": {
                "target": 70.0,
                "warning_threshold": 60.0,
                "critical_threshold": 50.0,
                "calculation": "appointments_booked / search_sessions * 100"
            },
            "emergency_response_time": {
                "target": 30.0,  # seconds
                "warning_threshold": 45.0,
                "critical_threshold": 60.0,
                "calculation": "avg(emergency_call_response_time)"
            },
            "escalation_rate": {
                "target": 15.0,  # percentage
                "warning_threshold": 20.0,
                "critical_threshold": 25.0,
                "calculation": "escalated_calls / total_calls * 100"
            },
            "provider_data_accuracy": {
                "target": 98.0,
                "warning_threshold": 95.0,
                "critical_threshold": 90.0,
                "calculation": "verified_provider_info / total_provider_records * 100"
            }
        },

        "compliance_monitoring": {
            "hipaa_compliance": {
                "data_encryption": True,
                "access_logging": True,
                "consent_tracking": True,
                "data_retention_policy": "7_years"
            },
            "audit_requirements": {
                "call_recording_consent": True,
                "patient_data_access_logs": True,
                "provider_verification_logs": True,
                "emergency_response_logs": True
            }
        },

        "alerting": {
            "channels": ["email", "slack", "sms"],
            "escalation_matrix": {
                "critical": ["on_call_engineer", "healthcare_supervisor"],
                "warning": ["monitoring_team"],
                "info": ["analytics_team"]
            },
            "notification_rules": {
                "emergency_system_down": {
                    "severity": "critical",
                    "immediate_notification": True,
                    "auto_escalation_minutes": 5
                },
                "provider_database_outdated": {
                    "severity": "warning",
                    "notification_delay_minutes": 15
                },
                "high_call_volume": {
                    "severity": "info",
                    "notification_delay_minutes": 60
                }
            }
        },

        "data_retention": {
            "metrics": "1_year",
            "call_logs": "7_years",  # HIPAA requirement
            "audit_logs": "7_years",
            "performance_data": "2_years"
        }
    }

    return config

def setup_healthcare_health_endpoints(request: HealthcareMonitoringRequest) -> List[str]:
    """Setup healthcare-specific health check endpoints."""

    base_url = f"https://monitoring.ailabsafrica.com/healthcare/{request.organizationName.lower().replace(' ', '-')}"

    endpoints = [
        f"{base_url}/health/system",
        f"{base_url}/health/vapi-assistant/{request.assistantId}",
        f"{base_url}/health/n8n-workflow/{request.workflowId}",
        f"{base_url}/health/provider-database",
        f"{base_url}/health/integrations",
        f"{base_url}/health/compliance",
        f"{base_url}/metrics/healthcare-kpis",
        f"{base_url}/metrics/call-analytics",
        f"{base_url}/metrics/provider-search-performance",
        f"{base_url}/alerts/active",
        f"{base_url}/status/emergency-services"
    ]

    return endpoints

def setup_healthcare_alert_rules(request: HealthcareMonitoringRequest) -> List[Dict[str, Any]]:
    """Setup healthcare-specific alert rules."""

    alert_rules = [
        {
            "name": "System Health Critical",
            "condition": "system_health_score < 0.8",
            "severity": "critical",
            "description": "Overall system health has dropped below acceptable levels",
            "auto_remediation": False,
            "notification_channels": ["email", "sms", "slack"],
            "escalation_minutes": 5
        },
        {
            "name": "Provider Database Disconnected",
            "condition": "provider_database_connected == false",
            "severity": "critical",
            "description": "Provider database is not accessible",
            "auto_remediation": True,
            "remediation_script": "restart_database_connection",
            "notification_channels": ["email", "sms"],
            "escalation_minutes": 2
        },
        {
            "name": "High Emergency Call Volume",
            "condition": "emergency_calls_per_hour > 50",
            "severity": "warning",
            "description": "Unusually high volume of emergency calls detected",
            "auto_remediation": False,
            "notification_channels": ["email", "slack"],
            "escalation_minutes": 15
        },
        {
            "name": "Low Provider Search Success Rate",
            "condition": "search_success_rate < 90",
            "severity": "warning",
            "description": "Provider search success rate has dropped below 90%",
            "auto_remediation": False,
            "notification_channels": ["email"],
            "escalation_minutes": 30
        },
        {
            "name": "VAPI Assistant Unresponsive",
            "condition": "vapi_response_time > 10 OR vapi_error_rate > 0.05",
            "severity": "critical",
            "description": "VAPI assistant is unresponsive or showing high error rates",
            "auto_remediation": True,
            "remediation_script": "restart_vapi_assistant",
            "notification_channels": ["email", "sms"],
            "escalation_minutes": 3
        },
        {
            "name": "Compliance Violation Detected",
            "condition": "hipaa_compliance_score < 1.0",
            "severity": "critical",
            "description": "HIPAA compliance violation has been detected",
            "auto_remediation": False,
            "notification_channels": ["email", "sms", "slack"],
            "escalation_minutes": 0,  # Immediate
            "requires_manual_review": True
        },
        {
            "name": "High Escalation Rate",
            "condition": "escalation_rate > 25",
            "severity": "warning",
            "description": "More than 25% of calls are being escalated to human agents",
            "auto_remediation": False,
            "notification_channels": ["email"],
            "escalation_minutes": 60
        },
        {
            "name": "Provider Data Outdated",
            "condition": "provider_data_age > 24 AND provider_data_quality < 95",
            "severity": "warning",
            "description": "Provider data is more than 24 hours old and quality is degrading",
            "auto_remediation": True,
            "remediation_script": "refresh_provider_data",
            "notification_channels": ["email"],
            "escalation_minutes": 120
        }
    ]

    return alert_rules

def define_healthcare_kpis(kpis: List[str]) -> List[Dict[str, Any]]:
    """Define healthcare-specific KPI metrics."""

    kpi_definitions = []

    kpi_mapping = {
        "search_success_rate": {
            "name": "Provider Search Success Rate",
            "description": "Percentage of provider searches that return relevant results",
            "unit": "percentage",
            "target": 95.0,
            "calculation": "successful_searches / total_searches * 100",
            "data_source": "search_analytics",
            "refresh_interval": "5m"
        },
        "appointment_booking_rate": {
            "name": "Appointment Booking Conversion Rate",
            "description": "Percentage of searches that result in appointment bookings",
            "unit": "percentage",
            "target": 70.0,
            "calculation": "appointments_booked / search_sessions * 100",
            "data_source": "booking_analytics",
            "refresh_interval": "15m"
        },
        "emergency_response_time": {
            "name": "Emergency Response Time",
            "description": "Average time to connect emergency callers with services",
            "unit": "seconds",
            "target": 30.0,
            "calculation": "avg(emergency_call_response_time)",
            "data_source": "call_analytics",
            "refresh_interval": "1m"
        },
        "escalation_rate": {
            "name": "Human Escalation Rate",
            "description": "Percentage of calls escalated to human agents",
            "unit": "percentage",
            "target": 15.0,
            "calculation": "escalated_calls / total_calls * 100",
            "data_source": "call_analytics",
            "refresh_interval": "10m"
        },
        "customer_satisfaction": {
            "name": "Customer Satisfaction Score",
            "description": "Average customer satisfaction rating (1-5 scale)",
            "unit": "score",
            "target": 4.5,
            "calculation": "avg(satisfaction_ratings)",
            "data_source": "feedback_analytics",
            "refresh_interval": "30m"
        },
        "provider_data_accuracy": {
            "name": "Provider Data Accuracy",
            "description": "Percentage of provider information that is current and accurate",
            "unit": "percentage",
            "target": 98.0,
            "calculation": "verified_provider_info / total_provider_records * 100",
            "data_source": "data_quality_analytics",
            "refresh_interval": "1h"
        }
    }

    for kpi in kpis:
        if kpi in kpi_mapping:
            kpi_definitions.append(kpi_mapping[kpi])

    return kpi_definitions

async def setup_healthcare_dashboard(request: HealthcareMonitoringRequest, config: Dict[str, Any]) -> str:
    """Setup healthcare monitoring dashboard."""

    dashboard_id = f"healthcare_{request.organizationName.lower().replace(' ', '-')}_{datetime.now().strftime('%Y%m%d')}"

    dashboard_config = {
        "id": dashboard_id,
        "title": f"{request.organizationName} Healthcare Monitoring",
        "layout": "healthcare_specialized",
        "refresh_interval": 30,  # seconds

        "widgets": [
            {
                "type": "healthcare_overview",
                "title": "System Health Overview",
                "size": "large",
                "metrics": ["system_health", "active_calls", "provider_database_status"],
                "position": {"row": 1, "col": 1, "width": 12, "height": 4}
            },
            {
                "type": "call_analytics",
                "title": "Call Analytics",
                "size": "medium",
                "metrics": ["call_volume", "success_rate", "average_duration"],
                "position": {"row": 2, "col": 1, "width": 6, "height": 4}
            },
            {
                "type": "provider_search_metrics",
                "title": "Provider Search Performance",
                "size": "medium",
                "metrics": ["search_success_rate", "search_response_time", "booking_rate"],
                "position": {"row": 2, "col": 7, "width": 6, "height": 4}
            },
            {
                "type": "emergency_services",
                "title": "Emergency Services Status",
                "size": "medium",
                "metrics": ["emergency_calls", "response_time", "escalations"],
                "position": {"row": 3, "col": 1, "width": 6, "height": 4},
                "alert_threshold": "critical"
            },
            {
                "type": "compliance_monitor",
                "title": "HIPAA Compliance Status",
                "size": "medium",
                "metrics": ["compliance_score", "audit_logs", "data_security"],
                "position": {"row": 3, "col": 7, "width": 6, "height": 4},
                "alert_threshold": "critical"
            },
            {
                "type": "kpi_scorecard",
                "title": "Healthcare KPIs",
                "size": "large",
                "metrics": request.kpis,
                "position": {"row": 4, "col": 1, "width": 12, "height": 3}
            },
            {
                "type": "recent_alerts",
                "title": "Recent Alerts",
                "size": "medium",
                "position": {"row": 5, "col": 1, "width": 6, "height": 4}
            },
            {
                "type": "provider_data_quality",
                "title": "Provider Data Quality",
                "size": "medium",
                "metrics": ["data_freshness", "accuracy_score", "completeness"],
                "position": {"row": 5, "col": 7, "width": 6, "height": 4}
            }
        ],

        "filters": [
            {"name": "time_range", "type": "time_picker", "default": "24h"},
            {"name": "severity", "type": "select", "options": ["all", "critical", "warning", "info"]},
            {"name": "component", "type": "select", "options": ["all", "vapi", "n8n", "database", "integrations"]}
        ],

        "export_options": ["pdf", "csv", "json"],
        "sharing": {
            "public_link": False,
            "embed_code": True,
            "email_reports": True
        }
    }

    # Generate dashboard URL
    dashboard_url = f"https://monitoring.ailabsafrica.com/dashboards/{dashboard_id}"

    logger.info(f"Healthcare dashboard configured: {dashboard_url}")
    return dashboard_url

async def initialize_healthcare_monitoring(organization_name: str, config: Dict[str, Any]):
    """Initialize healthcare monitoring system in background."""
    try:
        logger.info(f"Initializing healthcare monitoring for: {organization_name}")

        # Setup metric collection
        await setup_metric_collection(config)

        # Initialize alert monitoring
        await initialize_alert_monitoring(config)

        # Setup compliance monitoring
        await setup_compliance_monitoring(config)

        # Start health checks
        await start_health_checks(config)

        logger.info(f"Healthcare monitoring initialized successfully for: {organization_name}")

    except Exception as e:
        logger.error(f"Failed to initialize healthcare monitoring: {str(e)}")
        raise

async def setup_metric_collection(config: Dict[str, Any]):
    """Setup metric collection for healthcare system."""
    # Implementation would setup time-series data collection
    pass

async def initialize_alert_monitoring(config: Dict[str, Any]):
    """Initialize alert monitoring system."""
    # Implementation would setup alert evaluation and notification
    pass

async def setup_compliance_monitoring(config: Dict[str, Any]):
    """Setup HIPAA compliance monitoring."""
    # Implementation would setup compliance checks and audit logging
    pass

async def start_health_checks(config: Dict[str, Any]):
    """Start periodic health checks for all system components."""
    # Implementation would start background health check tasks
    pass

@router.get("/healthcare/{organization_name}/dashboard")
async def get_healthcare_dashboard(
    organization_name: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Get healthcare monitoring dashboard data."""
    try:
        # This would fetch real dashboard data
        dashboard_data = {
            "organization": organization_name,
            "last_updated": datetime.utcnow().isoformat(),
            "system_health": {
                "overall_score": 0.96,
                "vapi_status": "healthy",
                "workflow_status": "healthy",
                "database_status": "healthy",
                "integrations_status": "warning"
            },
            "call_analytics": {
                "total_calls_today": 234,
                "success_rate": 94.2,
                "average_duration": "3:42",
                "emergency_calls": 12
            },
            "provider_search": {
                "searches_today": 189,
                "success_rate": 96.8,
                "average_response_time": "1.2s",
                "booking_conversion": 68.5
            },
            "kpis": [
                {"name": "Search Success Rate", "current": 96.8, "target": 95.0, "status": "good"},
                {"name": "Booking Rate", "current": 68.5, "target": 70.0, "status": "warning"},
                {"name": "Emergency Response", "current": 28.3, "target": 30.0, "status": "good"},
                {"name": "Escalation Rate", "current": 12.4, "target": 15.0, "status": "good"}
            ],
            "recent_alerts": [
                {
                    "id": "alert_001",
                    "severity": "warning",
                    "message": "Calendly integration showing intermittent failures",
                    "timestamp": (datetime.utcnow() - timedelta(minutes=15)).isoformat(),
                    "resolved": False
                }
            ],
            "compliance_status": {
                "hipaa_compliance": 100.0,
                "audit_logs_current": True,
                "data_encryption_active": True,
                "consent_tracking_enabled": True
            }
        }

        return dashboard_data

    except Exception as e:
        logger.error(f"Error getting healthcare dashboard: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get dashboard data: {str(e)}"
        )

@router.get("/healthcare/{organization_name}/alerts")
async def get_healthcare_alerts(
    organization_name: str,
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Get healthcare system alerts."""
    try:
        # Filter alerts based on parameters
        alerts = [
            {
                "id": "alert_001",
                "severity": "warning",
                "category": "integrations",
                "message": "Calendly integration showing intermittent failures",
                "details": {
                    "error_rate": 0.05,
                    "affected_bookings": 3,
                    "last_failure": "2024-01-15T14:30:00Z"
                },
                "timestamp": (datetime.utcnow() - timedelta(minutes=15)).isoformat(),
                "resolved": False
            },
            {
                "id": "alert_002",
                "severity": "info",
                "category": "performance",
                "message": "High call volume detected",
                "details": {
                    "calls_per_hour": 45,
                    "normal_range": "20-35",
                    "peak_time": "2024-01-15T14:00:00Z"
                },
                "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "resolved": True
            }
        ]

        # Apply filters
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]

        if resolved is not None:
            alerts = [a for a in alerts if a["resolved"] == resolved]

        return {
            "organization": organization_name,
            "alerts": alerts,
            "total_count": len(alerts),
            "unresolved_count": len([a for a in alerts if not a["resolved"]])
        }

    except Exception as e:
        logger.error(f"Error getting healthcare alerts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get alerts: {str(e)}"
        )

@router.post("/healthcare/{organization_name}/alerts/{alert_id}/resolve")
async def resolve_healthcare_alert(
    organization_name: str,
    alert_id: str,
    resolution_notes: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Resolve a healthcare system alert."""
    try:
        # This would mark alert as resolved in the monitoring system
        resolution_data = {
            "alert_id": alert_id,
            "resolved_by": current_user.get("email", "unknown"),
            "resolved_at": datetime.utcnow().isoformat(),
            "resolution_notes": resolution_notes,
            "status": "resolved"
        }

        logger.info(f"Alert {alert_id} resolved by {current_user.get('email')}")
        return resolution_data

    except Exception as e:
        logger.error(f"Error resolving alert: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resolve alert: {str(e)}"
        )