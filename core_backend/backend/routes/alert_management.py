"""
Alert Management API Routes

Endpoints for configuring and managing cost analytics alerts.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field, validator
from datetime import datetime
import logging

from ..auth import get_current_user_mongo
from ..mongo import get_database
from apps.shared.services.alert_service import AlertService, AlertChannel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alert-management", tags=["alert-management"])


class AlertConfig(BaseModel):
    """Alert configuration model"""
    email_enabled: bool = Field(True, description="Enable email alerts")
    slack_enabled: bool = Field(False, description="Enable Slack alerts")
    discord_enabled: bool = Field(False, description="Enable Discord alerts")

    # Email settings
    alert_emails: List[str] = Field([], description="Email addresses to send alerts to")
    smtp_host: Optional[str] = Field(None, description="SMTP server host")
    smtp_port: Optional[int] = Field(587, description="SMTP server port")
    smtp_user: Optional[str] = Field(None, description="SMTP username")
    smtp_password: Optional[str] = Field(None, description="SMTP password")
    from_email: Optional[str] = Field(None, description="From email address")

    # Slack settings
    slack_webhook: Optional[str] = Field(None, description="Slack webhook URL")

    # Discord settings
    discord_webhook: Optional[str] = Field(None, description="Discord webhook URL")

    # Alert settings
    cooldown_hours: int = Field(24, ge=1, le=168, description="Cooldown period in hours")
    threshold_critical: float = Field(0.0, description="Critical threshold (negative margin)")
    threshold_high: float = Field(5.0, description="High threshold (< 5% margin)")
    threshold_medium: float = Field(10.0, description="Medium threshold (< 10% margin)")
    threshold_low: float = Field(15.0, description="Low threshold (< 15% margin)")

    @validator('alert_emails')
    def validate_emails(cls, v):
        """Validate email addresses"""
        if v:
            import re
            email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            for email in v:
                if not email_pattern.match(email):
                    raise ValueError(f"Invalid email address: {email}")
        return v

    @validator('slack_webhook', 'discord_webhook')
    def validate_webhook(cls, v):
        """Validate webhook URLs"""
        if v and not v.startswith('https://'):
            raise ValueError("Webhook URL must start with https://")
        return v


class TestAlertRequest(BaseModel):
    """Request model for testing alerts"""
    channel: AlertChannel = Field(..., description="Channel to test")
    provider: str = Field("TEST_PROVIDER", description="Test provider name")


@router.get("/config")
async def get_alert_config(
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get current alert configuration.

    Returns:
        Alert configuration for user's organization
    """
    try:
        db = get_database()
        alert_service = AlertService(db)

        # Get organization ID from user
        organization_id = current_user.get("organization_id")

        # Get configuration
        config = await alert_service._get_alert_config(organization_id)

        # Remove sensitive data
        config.pop("smtp_password", None)

        return {
            "success": True,
            "config": config
        }

    except Exception as e:
        logger.error(f"Failed to get alert config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config")
async def update_alert_config(
    config: AlertConfig,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Update alert configuration.

    Args:
        config: Alert configuration to save

    Returns:
        Updated configuration
    """
    try:
        db = get_database()
        alert_service = AlertService(db)

        # Get organization ID from user
        organization_id = current_user.get("organization_id")

        # Verify admin access
        user_role = current_user.get("role", "user")
        if user_role not in ["admin", "owner", "universal_admin"]:
            raise HTTPException(
                status_code=403,
                detail="Admin access required to configure alerts"
            )

        # Save configuration
        saved_config = await alert_service.configure_alerts(
            tenant_id=organization_id,
            config=config.dict()
        )

        # Remove sensitive data
        saved_config.pop("smtp_password", None)

        logger.info(f"Alert config updated by {current_user.get('email')}")

        return {
            "success": True,
            "config": saved_config,
            "message": "Alert configuration updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update alert config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_alert_history(
    provider: Optional[str] = Query(None, description="Filter by provider"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get alert history.

    Args:
        provider: Optional provider filter
        limit: Maximum number of records

    Returns:
        List of past alerts
    """
    try:
        db = get_database()
        alert_service = AlertService(db)

        # Get organization ID from user
        organization_id = current_user.get("organization_id")

        # Verify admin access
        user_role = current_user.get("role", "user")
        if user_role not in ["admin", "owner", "universal_admin"]:
            raise HTTPException(
                status_code=403,
                detail="Admin access required to view alert history"
            )

        # Get history
        alerts = await alert_service.get_alert_history(
            tenant_id=organization_id,
            provider=provider,
            limit=limit
        )

        return {
            "success": True,
            "alerts": alerts,
            "count": len(alerts)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_alert(
    request: TestAlertRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Send a test alert to verify configuration.

    Args:
        request: Test alert request with channel

    Returns:
        Success status
    """
    try:
        db = get_database()
        alert_service = AlertService(db)

        # Get organization ID from user
        organization_id = current_user.get("organization_id")

        # Verify admin access
        user_role = current_user.get("role", "user")
        if user_role not in ["admin", "owner", "universal_admin"]:
            raise HTTPException(
                status_code=403,
                detail="Admin access required to test alerts"
            )

        # Create test provider data
        test_data = {
            "provider": request.provider,
            "total_revenue": 100.0,
            "total_costs": 150.0,
            "total_profit": -50.0,
            "profit_margin_percentage": -50.0,
            "transaction_count": 10
        }

        # Send test alert
        await alert_service._send_alert(
            provider=request.provider,
            severity="critical",
            margin=-50.0,
            data=test_data,
            tenant_id=organization_id
        )

        return {
            "success": True,
            "message": f"Test alert sent via {request.channel}",
            "channel": request.channel
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send test alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/acknowledge/{alert_id}")
async def acknowledge_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Mark an alert as acknowledged.

    Args:
        alert_id: Alert ID to acknowledge

    Returns:
        Success status
    """
    try:
        from bson import ObjectId

        db = get_database()
        alert_service = AlertService(db)

        # Get organization ID from user
        organization_id = current_user.get("organization_id")

        # Update alert
        result = await alert_service.collection.update_one(
            {
                "_id": ObjectId(alert_id),
                "tenant_id": organization_id
            },
            {
                "$set": {
                    "acknowledged": True,
                    "acknowledged_by": current_user.get("email"),
                    "acknowledged_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Alert not found")

        return {
            "success": True,
            "message": "Alert acknowledged"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history")
async def clear_alert_history(
    older_than_days: int = Query(90, ge=1, le=365, description="Clear alerts older than N days"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Clear old alert history.

    Args:
        older_than_days: Clear alerts older than this many days

    Returns:
        Number of records deleted
    """
    try:
        from datetime import timedelta

        db = get_database()
        alert_service = AlertService(db)

        # Get organization ID from user
        organization_id = current_user.get("organization_id")

        # Verify admin access
        user_role = current_user.get("role", "user")
        if user_role not in ["admin", "owner", "universal_admin"]:
            raise HTTPException(
                status_code=403,
                detail="Admin access required to clear alert history"
            )

        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

        # Delete old alerts
        result = await alert_service.collection.delete_many({
            "tenant_id": organization_id,
            "sent_at": {"$lt": cutoff_date}
        })

        logger.info(f"Cleared {result.deleted_count} old alerts for {organization_id}")

        return {
            "success": True,
            "deleted_count": result.deleted_count,
            "message": f"Cleared {result.deleted_count} alerts older than {older_than_days} days"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear alert history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_alert_stats(
    days: int = Query(30, ge=1, le=365, description="Stats for last N days"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get alert statistics.

    Args:
        days: Number of days to analyze

    Returns:
        Alert statistics
    """
    try:
        from datetime import timedelta

        db = get_database()
        alert_service = AlertService(db)

        # Get organization ID from user
        organization_id = current_user.get("organization_id")

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get alerts in range
        alerts = await alert_service.collection.find({
            "tenant_id": organization_id,
            "sent_at": {"$gte": start_date, "$lte": end_date}
        }).to_list(length=None)

        # Calculate stats
        total_alerts = len(alerts)
        by_severity = {}
        by_provider = {}
        by_channel = {}

        for alert in alerts:
            # By severity
            severity = alert.get("severity", "unknown")
            by_severity[severity] = by_severity.get(severity, 0) + 1

            # By provider
            provider = alert.get("provider", "unknown")
            by_provider[provider] = by_provider.get(provider, 0) + 1

            # By channel
            for channel in alert.get("channels", []):
                by_channel[channel] = by_channel.get(channel, 0) + 1

        return {
            "success": True,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "stats": {
                "total_alerts": total_alerts,
                "by_severity": by_severity,
                "by_provider": by_provider,
                "by_channel": by_channel,
                "acknowledgment_rate": sum(1 for a in alerts if a.get("acknowledged", False)) / max(total_alerts, 1) * 100
            }
        }

    except Exception as e:
        logger.error(f"Failed to get alert stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/checker-status")
async def get_checker_status(
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get status of the scheduled alert checker.

    Returns:
        Checker status and statistics
    """
    try:
        from ..services.scheduled_alert_checker import get_alert_checker_stats

        # Verify admin access
        user_role = current_user.get("role", "user")
        if user_role not in ["admin", "owner", "universal_admin"]:
            raise HTTPException(
                status_code=403,
                detail="Admin access required to view checker status"
            )

        # Get checker stats
        stats = get_alert_checker_stats()

        return {
            "success": True,
            "checker": stats,
            "message": "Alert checker is running" if stats.get("status") == "active" else "Alert checker not started yet"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get checker status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
