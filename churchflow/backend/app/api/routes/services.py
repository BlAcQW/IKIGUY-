"""
Church service API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
import logging
from bson import ObjectId

from app.schemas.service import (
    ServiceResponse,
    CreateServiceRequest,
    UpdateServiceRequest,
    ServiceListResponse,
    GenerateRecurringServicesRequest,
    GenerateRecurringServicesResponse,
    ServiceAttendanceSummary
)
from app.services.service_service import service_service
from app.api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create service",
    description="Create a new church service (admin only)."
)
async def create_service(
    request: CreateServiceRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create new service."""
    try:
        service_data = request.model_dump()

        # Convert branch_id to ObjectId
        if "branch_id" in service_data:
            service_data["branch_id"] = ObjectId(service_data["branch_id"])

        service = await service_service.create_service(service_data)

        return ServiceResponse(
            id=str(service.id),
            service_type=service.service_type,
            branch_id=str(service.branch_id),
            organization_id=service.organization_id,
            sermon_title=service.sermon_title,
            series_name=service.series_name,
            scripture_reference=service.scripture_reference,
            speaker=service.speaker,
            sermon_recording_url=service.sermon_recording_url,
            sermon_notes_url=service.sermon_notes_url,
            livestream_link=service.livestream_link,
            service_date=service.service_date,
            start_time=service.start_time,
            end_time=service.end_time,
            status=service.status,
            expected_attendance=service.expected_attendance,
            actual_attendance=service.actual_attendance,
            qr_code=service.qr_code,
            venue_checkin_radius=service.venue_checkin_radius,
            is_recurring=service.is_recurring,
            recurrence_rule=service.recurrence_rule,
            created_at=service.created_at,
            updated_at=service.updated_at,
            created_by=str(service.created_by) if service.created_by else None
        )

    except Exception as e:
        logger.error(f"Failed to create service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create service: {str(e)}"
        )


@router.get(
    "",
    response_model=ServiceListResponse,
    summary="List services",
    description="List church services with optional filters."
)
async def list_services(
    branch_id: Optional[str] = Query(None, description="Filter by branch ID"),
    start_date: Optional[str] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    service_type: Optional[str] = Query(None, description="Filter by service type"),
    status_filter: Optional[str] = Query(None, description="Filter by status", alias="status"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results")
):
    """List services - public endpoint."""
    try:
        # Parse date strings
        parsed_start_date = datetime.fromisoformat(start_date) if start_date else None
        parsed_end_date = datetime.fromisoformat(end_date) if end_date else None

        services = await service_service.list_services(
            branch_id=branch_id,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            service_type=service_type,
            status=status_filter,
            limit=limit
        )

        service_responses = [
            ServiceResponse(
                id=str(svc.id),
                service_type=svc.service_type,
                branch_id=str(svc.branch_id),
                organization_id=svc.organization_id,
                sermon_title=svc.sermon_title,
                series_name=svc.series_name,
                scripture_reference=svc.scripture_reference,
                speaker=svc.speaker,
                sermon_recording_url=svc.sermon_recording_url,
                sermon_notes_url=svc.sermon_notes_url,
                livestream_link=svc.livestream_link,
                service_date=svc.service_date,
                start_time=svc.start_time,
                end_time=svc.end_time,
                status=svc.status,
                expected_attendance=svc.expected_attendance,
                actual_attendance=svc.actual_attendance,
                qr_code=svc.qr_code,
                venue_checkin_radius=svc.venue_checkin_radius,
                is_recurring=svc.is_recurring,
                recurrence_rule=svc.recurrence_rule,
                created_at=svc.created_at,
                updated_at=svc.updated_at,
                created_by=str(svc.created_by) if svc.created_by else None
            )
            for svc in services
        ]

        return ServiceListResponse(
            services=service_responses,
            total=len(service_responses)
        )

    except Exception as e:
        logger.error(f"Failed to list services: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list services: {str(e)}"
        )


@router.get(
    "/{service_id}",
    response_model=ServiceResponse,
    summary="Get service",
    description="Get service details by ID."
)
async def get_service(service_id: str):
    """Get service details - public endpoint."""
    try:
        service = await service_service.get_service(service_id)

        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service not found: {service_id}"
            )

        return ServiceResponse(
            id=str(service.id),
            service_type=service.service_type,
            branch_id=str(service.branch_id),
            organization_id=service.organization_id,
            sermon_title=service.sermon_title,
            series_name=service.series_name,
            scripture_reference=service.scripture_reference,
            speaker=service.speaker,
            sermon_recording_url=service.sermon_recording_url,
            sermon_notes_url=service.sermon_notes_url,
            livestream_link=service.livestream_link,
            service_date=service.service_date,
            start_time=service.start_time,
            end_time=service.end_time,
            status=service.status,
            expected_attendance=service.expected_attendance,
            actual_attendance=service.actual_attendance,
            qr_code=service.qr_code,
            venue_checkin_radius=service.venue_checkin_radius,
            is_recurring=service.is_recurring,
            recurrence_rule=service.recurrence_rule,
            created_at=service.created_at,
            updated_at=service.updated_at,
            created_by=str(service.created_by) if service.created_by else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service: {str(e)}"
        )


@router.put(
    "/{service_id}",
    response_model=ServiceResponse,
    summary="Update service",
    description="Update service details (admin only)."
)
async def update_service(
    service_id: str,
    request: UpdateServiceRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update service."""
    try:
        update_data = request.model_dump(exclude_unset=True)

        service = await service_service.update_service(service_id, update_data)

        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service not found: {service_id}"
            )

        return ServiceResponse(
            id=str(service.id),
            service_type=service.service_type,
            branch_id=str(service.branch_id),
            organization_id=service.organization_id,
            sermon_title=service.sermon_title,
            series_name=service.series_name,
            scripture_reference=service.scripture_reference,
            speaker=service.speaker,
            sermon_recording_url=service.sermon_recording_url,
            sermon_notes_url=service.sermon_notes_url,
            livestream_link=service.livestream_link,
            service_date=service.service_date,
            start_time=service.start_time,
            end_time=service.end_time,
            status=service.status,
            expected_attendance=service.expected_attendance,
            actual_attendance=service.actual_attendance,
            qr_code=service.qr_code,
            venue_checkin_radius=service.venue_checkin_radius,
            is_recurring=service.is_recurring,
            recurrence_rule=service.recurrence_rule,
            created_at=service.created_at,
            updated_at=service.updated_at,
            created_by=str(service.created_by) if service.created_by else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update service: {str(e)}"
        )


@router.delete(
    "/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete service",
    description="Delete service (admin only)."
)
async def delete_service(
    service_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete service."""
    try:
        success = await service_service.delete_service(service_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service not found: {service_id}"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete service: {str(e)}"
        )


@router.post(
    "/generate-recurring",
    response_model=GenerateRecurringServicesResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate recurring services",
    description="Auto-generate weekly services (Sunday 8am, 10am, Wednesday 7pm) for specified weeks ahead."
)
async def generate_recurring_services(
    request: GenerateRecurringServicesRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate recurring services."""
    try:
        stats = await service_service.generate_recurring_services(
            branch_id=request.branch_id,
            organization_id=request.organization_id,
            weeks_ahead=request.weeks_ahead
        )

        return GenerateRecurringServicesResponse(
            success=True,
            message=f"Generated {stats['total']} services for {request.weeks_ahead} weeks",
            stats=stats
        )

    except Exception as e:
        logger.error(f"Failed to generate recurring services: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recurring services: {str(e)}"
        )


@router.get(
    "/{service_id}/attendance",
    response_model=ServiceAttendanceSummary,
    summary="Get service attendance summary",
    description="Get attendance statistics for a service."
)
async def get_service_attendance(service_id: str):
    """Get service attendance summary."""
    try:
        summary = await service_service.get_service_attendance_summary(service_id)

        return ServiceAttendanceSummary(
            service_id=service_id,
            total_attendees=summary["total_attendees"],
            members=summary["members"],
            visitors=summary["visitors"],
            first_timers=summary["first_timers"]
        )

    except Exception as e:
        logger.error(f"Failed to get service attendance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service attendance: {str(e)}"
        )
