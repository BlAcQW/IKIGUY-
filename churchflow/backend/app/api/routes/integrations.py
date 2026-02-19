"""
Integration API Routes for ChurchFlow

RESTful API endpoints for managing external integrations:
- Google Calendar sync
- Zapier webhooks
- Integration dashboard
"""

from fastapi import APIRouter, HTTPException, Depends, Body, Query
from typing import List, Optional
from datetime import datetime

from app.core.database import get_database
from app.api.dependencies import get_current_user, require_organization_access
from app.services.calendar_integration_service import CalendarIntegrationService
from app.services.zapier_webhook_service import ZapierWebhookService
from app.models.integration import (
    IntegrationConfig,
    GoogleCalendarConfig,
    ZapierWebhookConfig,
    WebhookDelivery,
    WebhookEventType,
    IntegrationDashboard,
    IntegrationHealth,
    IntegrationType,
    IntegrationStatus
)
from app.models.conference import Conference

router = APIRouter(prefix="/integrations", tags=["Integrations"])


# ============================================================================
# Google Calendar Integration Endpoints
# ============================================================================

@router.post("/google-calendar/configure")
async def configure_google_calendar(
    config: GoogleCalendarConfig = Body(..., description="Google Calendar configuration"),
    credentials: dict = Body(..., description="Service account credentials JSON"),
    organization_id: str = Depends(require_organization_access),
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Configure Google Calendar integration for an organization.

    Requires service account credentials JSON from Google Cloud Console.
    """
    try:
        service = CalendarIntegrationService(db)
        integration = await service.save_integration_config(
            organization_id=organization_id,
            config=config,
            credentials_json=credentials
        )

        return {
            "status": "success",
            "message": "Google Calendar integration configured successfully",
            "integration": integration.dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure Google Calendar: {str(e)}")


@router.post("/google-calendar/sync/{conference_id}")
async def sync_conference_to_calendar(
    conference_id: str,
    organization_id: str = Depends(require_organization_access),
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Sync a specific conference to Google Calendar.

    Creates or updates the calendar event.
    """
    try:
        # Get conference
        conference_data = await db.conferences.find_one({
            "_id": conference_id,
            "organization_id": organization_id
        })

        if not conference_data:
            raise HTTPException(status_code=404, detail="Conference not found")

        conference_data["id"] = str(conference_data.pop("_id"))
        conference = Conference(**conference_data)

        # Sync to calendar
        service = CalendarIntegrationService(db)
        result = await service.sync_conference_to_calendar(
            conference=conference,
            organization_id=organization_id
        )

        return {
            "status": "success",
            "message": f"Conference {result['action']} in Google Calendar",
            "event_id": result["event_id"],
            "event_link": result.get("event_link", "")
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync conference: {str(e)}")


@router.post("/google-calendar/batch-sync")
async def batch_sync_conferences(
    limit: int = Query(50, ge=1, le=100, description="Maximum conferences to sync"),
    organization_id: str = Depends(require_organization_access),
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Batch sync all conferences to Google Calendar.

    Useful for initial setup or re-syncing after configuration changes.
    """
    try:
        service = CalendarIntegrationService(db)
        result = await service.batch_sync_conferences(
            organization_id=organization_id,
            limit=limit
        )

        return {
            "status": "success",
            "message": f"Synced {result['successful']} of {result['total_processed']} conferences",
            "summary": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch sync failed: {str(e)}")


@router.delete("/google-calendar/events/{conference_id}")
async def delete_calendar_event(
    conference_id: str,
    organization_id: str = Depends(require_organization_access),
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a calendar event for a conference.

    Used when a conference is deleted.
    """
    try:
        service = CalendarIntegrationService(db)
        success = await service.delete_calendar_event(
            conference_id=conference_id,
            organization_id=organization_id
        )

        if success:
            return {
                "status": "success",
                "message": "Calendar event deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Calendar event not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete calendar event: {str(e)}")


@router.post("/google-calendar/test")
async def test_google_calendar_connection(
    organization_id: str = Depends(require_organization_access),
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Test Google Calendar connection.

    Verifies credentials and calendar access.
    """
    try:
        service = CalendarIntegrationService(db)
        result = await service.test_connection(organization_id=organization_id)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")


# ============================================================================
# Zapier Webhook Integration Endpoints
# ============================================================================

@router.post("/zapier/configure")
async def configure_zapier_webhook(
    config: ZapierWebhookConfig = Body(..., description="Zapier webhook configuration"),
    organization_id: str = Depends(require_organization_access),
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Configure Zapier webhook integration.

    Provide the webhook URL from Zapier and select events to trigger.
    """
    try:
        service = ZapierWebhookService(db)
        integration = await service.save_webhook_config(
            organization_id=organization_id,
            config=config
        )

        return {
            "status": "success",
            "message": "Zapier webhook configured successfully",
            "integration": integration.dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure Zapier webhook: {str(e)}")


@router.post("/zapier/test")
async def test_zapier_webhook(
    webhook_url: str = Body(..., embed=True, description="Webhook URL to test"),
    organization_id: str = Depends(require_organization_access),
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Test Zapier webhook connection.

    Sends a test payload to verify the webhook is working.
    """
    try:
        service = ZapierWebhookService(db)
        result = await service.test_webhook(
            organization_id=organization_id,
            webhook_url=webhook_url
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook test failed: {str(e)}")


@router.get("/zapier/deliveries", response_model=List[WebhookDelivery])
async def get_webhook_deliveries(
    event_type: Optional[WebhookEventType] = Query(None, description="Filter by event type"),
    webhook_url: Optional[str] = Query(None, description="Filter by webhook URL"),
    limit: int = Query(50, ge=1, le=100, description="Maximum deliveries to return"),
    organization_id: str = Depends(require_organization_access),
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Get webhook delivery history.

    Shows successful and failed delivery attempts.
    """
    try:
        service = ZapierWebhookService(db)
        deliveries = await service.get_delivery_history(
            organization_id=organization_id,
            event_type=event_type,
            webhook_url=webhook_url,
            limit=limit
        )

        return deliveries

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get delivery history: {str(e)}")


@router.get("/zapier/stats")
async def get_webhook_stats(
    webhook_url: Optional[str] = Query(None, description="Filter by webhook URL"),
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    organization_id: str = Depends(require_organization_access),
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Get webhook delivery statistics.

    Provides success rate, failure count, and average attempts.
    """
    try:
        service = ZapierWebhookService(db)
        stats = await service.get_delivery_stats(
            organization_id=organization_id,
            webhook_url=webhook_url,
            days=days
        )

        return {
            "status": "success",
            "stats": stats,
            "period_days": days
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get webhook stats: {str(e)}")


@router.delete("/zapier/{webhook_url:path}")
async def delete_zapier_webhook(
    webhook_url: str,
    organization_id: str = Depends(require_organization_access),
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a Zapier webhook configuration.
    """
    try:
        service = ZapierWebhookService(db)
        success = await service.delete_webhook_config(
            organization_id=organization_id,
            webhook_url=webhook_url
        )

        if success:
            return {
                "status": "success",
                "message": "Webhook deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Webhook not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete webhook: {str(e)}")


# ============================================================================
# Integration Dashboard Endpoints
# ============================================================================

@router.get("/dashboard", response_model=IntegrationDashboard)
async def get_integration_dashboard(
    organization_id: str = Depends(require_organization_access),
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Get integration dashboard showing all integrations for an organization.

    Displays status, health, and statistics for each integration.
    """
    try:
        # Get organization name
        org = await db.organizations.find_one({"_id": organization_id})
        org_name = org.get("name", "Unknown") if org else "Unknown"

        # Get all integrations for this organization
        integrations_cursor = db.integrations.find({"organization_id": organization_id})
        integrations = await integrations_cursor.to_list(length=100)

        integration_healths = []
        active_count = 0
        inactive_count = 0
        error_count = 0

        for integration_data in integrations:
            health = IntegrationHealth(
                integration_type=integration_data["integration_type"],
                status=integration_data["status"],
                last_sync_at=integration_data.get("last_sync_at"),
                error_message=integration_data.get("error_message"),
                total_syncs=integration_data.get("sync_count", 0),
                successful_syncs=integration_data.get("sync_count", 0),  # TODO: Track failures separately
                failed_syncs=0,  # TODO: Track failures
                success_rate=1.0 if integration_data.get("sync_count", 0) > 0 else 0.0
            )

            integration_healths.append(health)

            # Count by status
            if integration_data["status"] == IntegrationStatus.ACTIVE:
                active_count += 1
            elif integration_data["status"] == IntegrationStatus.INACTIVE:
                inactive_count += 1
            elif integration_data["status"] == IntegrationStatus.ERROR:
                error_count += 1

        dashboard = IntegrationDashboard(
            organization_id=organization_id,
            organization_name=org_name,
            integrations=integration_healths,
            total_active_integrations=active_count,
            total_inactive_integrations=inactive_count,
            total_error_integrations=error_count
        )

        return dashboard

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get integration dashboard: {str(e)}")


@router.get("/config/{integration_type}", response_model=IntegrationConfig)
async def get_integration_config(
    integration_type: IntegrationType,
    organization_id: str = Depends(require_organization_access),
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Get integration configuration for a specific integration type.
    """
    try:
        config_data = await db.integrations.find_one({
            "organization_id": organization_id,
            "integration_type": integration_type
        })

        if not config_data:
            raise HTTPException(status_code=404, detail=f"Integration {integration_type} not configured")

        config_data["id"] = str(config_data.pop("_id"))
        return IntegrationConfig(**config_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get integration config: {str(e)}")


@router.delete("/config/{integration_type}")
async def delete_integration_config(
    integration_type: IntegrationType,
    organization_id: str = Depends(require_organization_access),
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete an integration configuration.
    """
    try:
        result = await db.integrations.delete_many({
            "organization_id": organization_id,
            "integration_type": integration_type
        })

        if result.deleted_count > 0:
            return {
                "status": "success",
                "message": f"Integration {integration_type} deleted successfully",
                "deleted_count": result.deleted_count
            }
        else:
            raise HTTPException(status_code=404, detail=f"Integration {integration_type} not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete integration: {str(e)}")
