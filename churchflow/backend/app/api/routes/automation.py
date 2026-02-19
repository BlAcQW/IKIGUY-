"""
Automation API Routes

API endpoints for managing automated workflows and reminder sequences.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta

from app.api.dependencies import get_current_user, require_organization_access
from app.core.database import get_database
from app.services.automation_service import AutomationService
from app.schemas.automation import (
    CreateAutomationWorkflowRequest,
    UpdateAutomationWorkflowRequest,
    AutomationWorkflowResponse,
    ScheduledReminderResponse,
    AutomationDashboardResponse,
    ExecuteWorkflowRequest,
    BulkScheduleRemindersRequest
)
from app.models.automation import AutomationType, AutomationStatus

router = APIRouter()


@router.post("/workflows", response_model=AutomationWorkflowResponse, status_code=201)
async def create_automation_workflow(
    request: CreateAutomationWorkflowRequest,
    organization_id: str = Depends(require_organization_access),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Create a new automation workflow.

    Requires: coordinator or admin role
    """
    service = AutomationService(db)

    workflow = await service.create_workflow(
        organization_id=organization_id,
        user_id=current_user["sub"],
        automation_type=request.automation_type,
        name=request.name,
        description=request.description,
        event_reminder_config=request.event_reminder_config,
        conference_id=request.conference_id
    )

    return AutomationWorkflowResponse(
        _id=workflow.id,
        organization_id=workflow.organization_id,
        automation_type=workflow.automation_type,
        name=workflow.name,
        description=workflow.description,
        event_reminder_config=workflow.event_reminder_config,
        member_onboarding_config=workflow.member_onboarding_config,
        conference_id=workflow.conference_id,
        branch_id=workflow.branch_id,
        status=workflow.status,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
        created_by=workflow.created_by,
        total_executions=workflow.total_executions,
        successful_executions=workflow.successful_executions,
        failed_executions=workflow.failed_executions,
        last_execution_at=workflow.last_execution_at,
        next_execution_at=workflow.next_execution_at
    )


@router.post("/workflows/default-event-reminder", response_model=AutomationWorkflowResponse, status_code=201)
async def create_default_event_reminder_workflow(
    conference_id: str,
    organization_id: str = Depends(require_organization_access),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Create a default event reminder workflow for a conference.

    Creates workflow with standard 7d, 3d, 1d reminders.

    Requires: coordinator or admin role
    """
    # Get conference
    from bson import ObjectId
    conference = await db.conferences.find_one({"_id": ObjectId(conference_id)})
    if not conference:
        raise HTTPException(status_code=404, detail="Conference not found")

    service = AutomationService(db)

    workflow = await service.create_default_event_reminder_workflow(
        organization_id=organization_id,
        user_id=current_user["sub"],
        conference_id=conference_id,
        conference_name=conference["name"]
    )

    # Automatically schedule reminders
    await service.schedule_conference_reminders(
        workflow_id=workflow.id,
        conference_id=conference_id,
        organization_id=organization_id
    )

    return AutomationWorkflowResponse(
        _id=workflow.id,
        organization_id=workflow.organization_id,
        automation_type=workflow.automation_type,
        name=workflow.name,
        description=workflow.description,
        event_reminder_config=workflow.event_reminder_config,
        member_onboarding_config=workflow.member_onboarding_config,
        conference_id=workflow.conference_id,
        branch_id=workflow.branch_id,
        status=workflow.status,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
        created_by=workflow.created_by,
        total_executions=workflow.total_executions,
        successful_executions=workflow.successful_executions,
        failed_executions=workflow.failed_executions,
        last_execution_at=workflow.last_execution_at,
        next_execution_at=workflow.next_execution_at
    )


@router.get("/workflows", response_model=List[AutomationWorkflowResponse])
async def list_automation_workflows(
    organization_id: str = Depends(require_organization_access),
    automation_type: Optional[AutomationType] = Query(None),
    status: Optional[AutomationStatus] = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    List automation workflows for an organization.

    Optionally filter by automation_type and status.

    Requires: coordinator or admin role
    """
    service = AutomationService(db)

    workflows = await service.list_workflows(
        organization_id=organization_id,
        automation_type=automation_type,
        status=status
    )

    return [
        AutomationWorkflowResponse(
            _id=w.id,
            organization_id=w.organization_id,
            automation_type=w.automation_type,
            name=w.name,
            description=w.description,
            event_reminder_config=w.event_reminder_config,
            member_onboarding_config=w.member_onboarding_config,
            conference_id=w.conference_id,
            branch_id=w.branch_id,
            status=w.status,
            created_at=w.created_at,
            updated_at=w.updated_at,
            created_by=w.created_by,
            total_executions=w.total_executions,
            successful_executions=w.successful_executions,
            failed_executions=w.failed_executions,
            last_execution_at=w.last_execution_at,
            next_execution_at=w.next_execution_at
        )
        for w in workflows
    ]


@router.get("/workflows/{workflow_id}", response_model=AutomationWorkflowResponse)
async def get_automation_workflow(
    workflow_id: str,
    organization_id: str = Depends(require_organization_access),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get a specific automation workflow.

    Requires: coordinator or admin role
    """
    service = AutomationService(db)

    workflow = await service.get_workflow(workflow_id, organization_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return AutomationWorkflowResponse(
        _id=workflow.id,
        organization_id=workflow.organization_id,
        automation_type=workflow.automation_type,
        name=workflow.name,
        description=workflow.description,
        event_reminder_config=workflow.event_reminder_config,
        member_onboarding_config=workflow.member_onboarding_config,
        conference_id=workflow.conference_id,
        branch_id=workflow.branch_id,
        status=workflow.status,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
        created_by=workflow.created_by,
        total_executions=workflow.total_executions,
        successful_executions=workflow.successful_executions,
        failed_executions=workflow.failed_executions,
        last_execution_at=workflow.last_execution_at,
        next_execution_at=workflow.next_execution_at
    )


@router.put("/workflows/{workflow_id}/status", response_model=dict)
async def update_workflow_status(
    workflow_id: str,
    status: AutomationStatus,
    organization_id: str = Depends(require_organization_access),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update workflow status (active, paused, cancelled).

    Requires: coordinator or admin role
    """
    service = AutomationService(db)

    success = await service.update_workflow_status(workflow_id, organization_id, status)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {"success": True, "message": f"Workflow status updated to {status}"}


@router.delete("/workflows/{workflow_id}", status_code=204)
async def delete_automation_workflow(
    workflow_id: str,
    organization_id: str = Depends(require_organization_access),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Delete an automation workflow and its scheduled reminders.

    Requires: coordinator or admin role
    """
    service = AutomationService(db)

    success = await service.delete_workflow(workflow_id, organization_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return None


@router.post("/workflows/{workflow_id}/schedule-reminders", response_model=List[ScheduledReminderResponse])
async def schedule_reminders(
    workflow_id: str,
    conference_id: str,
    organization_id: str = Depends(require_organization_access),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Schedule reminders for a conference based on workflow configuration.

    Requires: coordinator or admin role
    """
    service = AutomationService(db)

    try:
        reminders = await service.schedule_conference_reminders(
            workflow_id=workflow_id,
            conference_id=conference_id,
            organization_id=organization_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return [
        ScheduledReminderResponse(
            _id=r.id,
            workflow_id=r.workflow_id,
            organization_id=r.organization_id,
            conference_id=r.conference_id,
            reminder_step=r.reminder_step,
            scheduled_at=r.scheduled_at,
            recipient_count=r.recipient_count,
            status=r.status,
            executed_at=r.executed_at,
            sms_campaign_id=r.sms_campaign_id,
            sent_count=r.sent_count,
            delivered_count=r.delivered_count,
            failed_count=r.failed_count,
            error_message=r.error_message,
            created_at=r.created_at,
            updated_at=r.updated_at
        )
        for r in reminders
    ]


@router.get("/dashboard", response_model=AutomationDashboardResponse)
async def get_automation_dashboard(
    organization_id: str = Depends(require_organization_access),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get automation dashboard statistics.

    Requires: coordinator or admin role
    """
    service = AutomationService(db)

    # Get workflow counts
    all_workflows = await service.list_workflows(organization_id)
    active_workflows = [w for w in all_workflows if w.status == AutomationStatus.ACTIVE]
    paused_workflows = [w for w in all_workflows if w.status == AutomationStatus.PAUSED]

    # Get reminder statistics
    pending_reminders = await service.get_pending_reminders_count(organization_id)
    upcoming_reminders = await service.get_upcoming_reminders(organization_id, hours=24)

    # Calculate success rate for last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_workflows = [
        w for w in all_workflows
        if w.last_execution_at and w.last_execution_at >= thirty_days_ago
    ]

    total_executions_30d = sum(w.total_executions for w in recent_workflows)
    successful_executions_30d = sum(w.successful_executions for w in recent_workflows)
    failed_executions_30d = sum(w.failed_executions for w in recent_workflows)

    success_rate = (
        successful_executions_30d / total_executions_30d
        if total_executions_30d > 0
        else 1.0
    )

    # Get recent workflows (limit to 5)
    recent_workflows_limited = sorted(all_workflows, key=lambda w: w.created_at, reverse=True)[:5]

    return AutomationDashboardResponse(
        total_workflows=len(all_workflows),
        active_workflows=len(active_workflows),
        paused_workflows=len(paused_workflows),
        pending_reminders=pending_reminders,
        upcoming_reminders_24h=len(upcoming_reminders),
        total_executions_30d=total_executions_30d,
        successful_executions_30d=successful_executions_30d,
        failed_executions_30d=failed_executions_30d,
        success_rate=success_rate,
        recent_workflows=[
            AutomationWorkflowResponse(
                _id=w.id,
                organization_id=w.organization_id,
                automation_type=w.automation_type,
                name=w.name,
                description=w.description,
                event_reminder_config=w.event_reminder_config,
                member_onboarding_config=w.member_onboarding_config,
                conference_id=w.conference_id,
                branch_id=w.branch_id,
                status=w.status,
                created_at=w.created_at,
                updated_at=w.updated_at,
                created_by=w.created_by,
                total_executions=w.total_executions,
                successful_executions=w.successful_executions,
                failed_executions=w.failed_executions,
                last_execution_at=w.last_execution_at,
                next_execution_at=w.next_execution_at
            )
            for w in recent_workflows_limited
        ],
        upcoming_reminders=[
            ScheduledReminderResponse(
                _id=r.id,
                workflow_id=r.workflow_id,
                organization_id=r.organization_id,
                conference_id=r.conference_id,
                reminder_step=r.reminder_step,
                scheduled_at=r.scheduled_at,
                recipient_count=r.recipient_count,
                status=r.status,
                executed_at=r.executed_at,
                sms_campaign_id=r.sms_campaign_id,
                sent_count=r.sent_count,
                delivered_count=r.delivered_count,
                failed_count=r.failed_count,
                error_message=r.error_message,
                created_at=r.created_at,
                updated_at=r.updated_at
            )
            for r in upcoming_reminders[:10]  # Limit to 10
        ]
    )


@router.post("/execute-pending", response_model=dict)
async def execute_pending_reminders(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Execute all pending reminders that are due.

    This endpoint should be called by a scheduled task/cron job.
    For security, this should be protected by API key or internal-only access.

    Returns execution statistics.
    """
    service = AutomationService(db)

    results = await service.execute_pending_reminders()

    return {
        "success": True,
        "executed": results["executed"],
        "successful": results["successful"],
        "failed": results["failed"],
        "timestamp": datetime.utcnow().isoformat()
    }
