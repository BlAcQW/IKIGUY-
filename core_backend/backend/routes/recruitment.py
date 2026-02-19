"""
Recruitment Routes for AI Labs Africa

API endpoints for job application submissions.

Author: AI Labs Africa
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks

from ..services.recruitment_service import get_recruitment_service, RecruitmentService
from ..mongo import get_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recruitment", tags=["recruitment"])


def get_service() -> RecruitmentService:
    """Get recruitment service with database connection."""
    service = get_recruitment_service()
    db = get_database()
    if db is not None:
        service.set_db(db)
    return service


@router.post("/apply")
async def submit_application(
    background_tasks: BackgroundTasks,
    name: str = Form(..., description="Full name of applicant"),
    email: str = Form(..., description="Email address"),
    phone: str = Form(..., description="Phone number"),
    position: str = Form(..., description="Position applying for"),
    cover_letter: str = Form(..., description="Cover letter"),
    linkedin: Optional[str] = Form(None, description="LinkedIn profile URL"),
    portfolio: Optional[str] = Form(None, description="Portfolio/website URL"),
    resume: Optional[UploadFile] = File(None, description="Resume/CV file")
):
    """
    Submit a job application.

    Accepts form data with optional resume file upload.
    - Validates required fields
    - Uploads resume to storage
    - Saves application to MongoDB
    - Sends email notification to careers@ailabsafrica.com

    Args:
        name: Full name of applicant
        email: Email address
        phone: Phone number
        position: Position applying for
        cover_letter: Cover letter text
        linkedin: LinkedIn profile URL (optional)
        portfolio: Portfolio URL (optional)
        resume: Resume file (optional, PDF/DOC/DOCX, max 5MB)

    Returns:
        Application ID and status
    """
    try:
        service = get_service()

        # Process resume file if provided
        resume_content = None
        resume_filename = None

        if resume:
            # Validate file size (max 5MB)
            content = await resume.read()
            if len(content) > 5 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail="Resume file too large. Maximum size is 5MB."
                )

            # Validate file type
            filename = resume.filename.lower()
            if not any(filename.endswith(ext) for ext in ['.pdf', '.doc', '.docx']):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file type. Accepted formats: PDF, DOC, DOCX"
                )

            resume_content = content
            resume_filename = resume.filename

        # Submit application
        result = await service.submit_application(
            name=name,
            email=email,
            phone=phone,
            position=position,
            cover_letter=cover_letter,
            linkedin=linkedin,
            portfolio=portfolio,
            resume_content=resume_content,
            resume_filename=resume_filename
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to submit application")
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Application submission error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit application: {str(e)}"
        )


@router.get("/positions")
async def get_positions():
    """
    Get list of available job positions.

    Returns:
        List of valid position titles
    """
    service = get_service()
    return {
        "success": True,
        "positions": service.get_positions()
    }


@router.get("/applications")
async def list_applications(
    status: Optional[str] = None,
    position: Optional[str] = None,
    limit: int = 50,
    skip: int = 0
):
    """
    List job applications (admin endpoint).

    Args:
        status: Filter by status (new, reviewing, interviewed, hired, rejected)
        position: Filter by position
        limit: Maximum number of results
        skip: Number of results to skip

    Returns:
        List of applications
    """
    try:
        service = get_service()
        result = await service.get_applications(
            status=status,
            position=position,
            limit=limit,
            skip=skip
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error")
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing applications: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/applications/{application_id}")
async def get_application(application_id: str):
    """
    Get a specific application by ID.

    Args:
        application_id: Application ID (e.g., APP-20251125-ABCD1234)

    Returns:
        Application details
    """
    try:
        service = get_service()
        result = await service.get_application(application_id)

        if not result.get("success"):
            raise HTTPException(
                status_code=404,
                detail=result.get("error")
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting application: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.patch("/applications/{application_id}/status")
async def update_application_status(
    application_id: str,
    status: str = Form(..., description="New status"),
    notes: Optional[str] = Form(None, description="Notes about status change")
):
    """
    Update application status (admin endpoint).

    Args:
        application_id: Application ID
        status: New status (new, reviewing, interviewed, hired, rejected)
        notes: Optional notes

    Returns:
        Updated status
    """
    try:
        service = get_service()
        result = await service.update_status(
            application_id=application_id,
            status=status,
            notes=notes
        )

        if not result.get("success"):
            status_code = 404 if "not found" in result.get("error", "").lower() else 400
            raise HTTPException(
                status_code=status_code,
                detail=result.get("error")
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating application: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/statuses")
async def get_statuses():
    """
    Get list of valid application statuses.

    Returns:
        List of valid statuses
    """
    service = get_service()
    return {
        "success": True,
        "statuses": service.get_statuses()
    }
