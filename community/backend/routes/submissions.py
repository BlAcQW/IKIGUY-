"""
Data submission routes for African Language Community Platform.

Handles audio, text, and link submissions with file upload and quality processing.
"""

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form, status
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import json

from models.submission_models import (
    SubmissionCreate, SubmissionUpdate, Submission, SubmissionStats
)
from models.user_models import User
from models.responses import DataResponse, ListResponse
from routes.auth import get_current_user
from services.submission_service import SubmissionService

router = APIRouter()
submission_service = SubmissionService()


@router.post("/audio", response_model=DataResponse)
async def submit_audio(
    audio_file: UploadFile = File(...),
    language_code: str = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    dialect: Optional[str] = Form(None),
    cultural_context: Optional[str] = Form(None),
    usage_context: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """
    Submit audio data for a specific language.

    Args:
        audio_file: Audio file upload
        language_code: ISO 639-3 language code
        title: Submission title
        description: Optional description
        category: Content category
        dialect: Specific dialect
        cultural_context: Cultural significance
        usage_context: Usage context
        current_user: Authenticated user

    Returns:
        DataResponse: Created submission data
    """
    try:
        # Validate audio file
        if not audio_file.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an audio format"
            )

        # Create submission data
        submission_data = SubmissionCreate(
            language_code=language_code,
            type="audio",
            title=title,
            description=description,
            category=category,
            dialect=dialect,
            cultural_context=cultural_context,
            usage_context=usage_context
        )

        # Process submission
        submission = await submission_service.create_audio_submission(
            submission_data, audio_file, current_user.id
        )

        return DataResponse(
            data=submission,
            message="Audio submission created successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio submission failed: {str(e)}"
        )


@router.post("/text", response_model=DataResponse)
async def submit_text(
    submission_data: SubmissionCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Submit text content for a specific language.

    Args:
        submission_data: Text submission data
        current_user: Authenticated user

    Returns:
        DataResponse: Created submission data
    """
    try:
        # Validate text submission
        if submission_data.type != "text":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Submission type must be 'text'"
            )

        if not submission_data.text_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text content is required for text submissions"
            )

        # Process submission
        submission = await submission_service.create_text_submission(
            submission_data, current_user.id
        )

        return DataResponse(
            data=submission,
            message="Text submission created successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text submission failed: {str(e)}"
        )


@router.post("/link", response_model=DataResponse)
async def submit_link(
    submission_data: SubmissionCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Submit external link/resource for a specific language.

    Args:
        submission_data: Link submission data
        current_user: Authenticated user

    Returns:
        DataResponse: Created submission data
    """
    try:
        # Validate link submission
        if submission_data.type != "link":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Submission type must be 'link'"
            )

        if not submission_data.external_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="External URL is required for link submissions"
            )

        # Process submission
        submission = await submission_service.create_link_submission(
            submission_data, current_user.id
        )

        return DataResponse(
            data=submission,
            message="Link submission created successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Link submission failed: {str(e)}"
        )


@router.get("/history", response_model=ListResponse)
async def get_user_submissions(
    current_user: User = Depends(get_current_user),
    page: int = 1,
    page_size: int = 20,
    submission_type: Optional[str] = None,
    language_code: Optional[str] = None
):
    """
    Get current user's submission history.

    Args:
        current_user: Authenticated user
        page: Page number
        page_size: Items per page
        submission_type: Filter by type
        language_code: Filter by language

    Returns:
        ListResponse: User's submissions with pagination
    """
    try:
        submissions, total_count = await submission_service.get_user_submissions(
            user_id=current_user.id,
            page=page,
            page_size=page_size,
            submission_type=submission_type,
            language_code=language_code
        )

        return ListResponse.create(
            items=submissions,
            total_count=total_count,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve submissions: {str(e)}"
        )


@router.get("/{submission_id}", response_model=DataResponse)
async def get_submission(
    submission_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific submission.

    Args:
        submission_id: Submission ID
        current_user: Authenticated user

    Returns:
        DataResponse: Submission details
    """
    try:
        submission = await submission_service.get_submission_details(
            submission_id, current_user.id
        )

        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )

        return DataResponse(
            data=submission,
            message="Submission retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve submission: {str(e)}"
        )


@router.put("/{submission_id}", response_model=DataResponse)
async def update_submission(
    submission_id: str,
    updates: SubmissionUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update submission information (only by original contributor).

    Args:
        submission_id: Submission ID
        updates: Fields to update
        current_user: Authenticated user

    Returns:
        DataResponse: Updated submission
    """
    try:
        # Verify ownership
        submission = await submission_service.get_submission_by_id(submission_id)
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )

        if str(submission.contributor_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only update your own submissions"
            )

        # Update submission
        updated_submission = await submission_service.update_submission(
            submission_id, updates
        )

        return DataResponse(
            data=updated_submission,
            message="Submission updated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update submission: {str(e)}"
        )


@router.delete("/{submission_id}", response_model=DataResponse)
async def delete_submission(
    submission_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete submission (only by original contributor or moderator).

    Args:
        submission_id: Submission ID
        current_user: Authenticated user

    Returns:
        DataResponse: Deletion confirmation
    """
    try:
        # Verify ownership or moderation rights
        submission = await submission_service.get_submission_by_id(submission_id)
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )

        if (str(submission.contributor_id) != str(current_user.id) and
            not current_user.can_moderate):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to delete submission"
            )

        # Delete submission
        await submission_service.delete_submission(submission_id)

        return DataResponse(
            data={"deleted": True},
            message="Submission deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete submission: {str(e)}"
        )


@router.get("/language/{language_code}/browse", response_model=ListResponse)
async def browse_language_submissions(
    language_code: str,
    page: int = 1,
    page_size: int = 20,
    tier: Optional[str] = None,
    category: Optional[str] = None,
    submission_type: Optional[str] = None
):
    """
    Browse submissions for a specific language.

    Args:
        language_code: Language code
        page: Page number
        page_size: Items per page
        tier: Filter by quality tier
        category: Filter by category
        submission_type: Filter by type

    Returns:
        ListResponse: Language submissions with pagination
    """
    try:
        filters = {}
        if tier:
            filters["tier"] = tier
        if category:
            filters["category"] = category
        if submission_type:
            filters["type"] = submission_type

        submissions, total_count = await submission_service.browse_language_submissions(
            language_code=language_code,
            page=page,
            page_size=page_size,
            filters=filters
        )

        return ListResponse.create(
            items=submissions,
            total_count=total_count,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to browse submissions: {str(e)}"
        )


@router.get("/stats/overview", response_model=DataResponse)
async def get_submission_stats():
    """
    Get platform-wide submission statistics.

    Returns:
        DataResponse: Submission statistics and metrics
    """
    try:
        stats = await submission_service.get_submission_statistics()

        return DataResponse(
            data=stats,
            message="Statistics retrieved successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )