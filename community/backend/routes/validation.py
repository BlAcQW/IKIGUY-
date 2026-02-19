"""
Validation routes for African Language Community Platform.

Handles community validation, quality assessment, and tier promotion.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional, List
from bson import ObjectId

from models.validation_models import ValidationCreate, ValidationSummary
from models.user_models import User
from models.responses import DataResponse, ListResponse
from routes.auth import get_current_user
from services.validation_service import ValidationService

router = APIRouter()
validation_service = ValidationService()


@router.get("/pending", response_model=ListResponse)
async def get_pending_validations(
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    language_code: Optional[str] = Query(None, description="Filter by language"),
    submission_type: Optional[str] = Query(None, description="Filter by submission type")
):
    """
    Get submissions pending validation that the current user can review.

    Args:
        current_user: Authenticated user (must be validator)
        page: Page number
        page_size: Items per page
        language_code: Optional language filter
        submission_type: Optional type filter

    Returns:
        ListResponse: Submissions needing validation
    """
    try:
        # Check if user can validate
        if not current_user.can_validate:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have validation permissions"
            )

        pending_submissions, total_count = await validation_service.get_pending_validations(
            validator_id=current_user.id,
            page=page,
            page_size=page_size,
            language_code=language_code,
            submission_type=submission_type
        )

        return ListResponse.create(
            items=pending_submissions,
            total_count=total_count,
            page=page,
            page_size=page_size
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve pending validations: {str(e)}"
        )


@router.post("/{submission_id}", response_model=DataResponse)
async def validate_submission(
    submission_id: str,
    validation_data: ValidationCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Submit validation for a specific submission.

    Args:
        submission_id: ID of submission to validate
        validation_data: Validation scores and feedback
        current_user: Authenticated user (must be validator)

    Returns:
        DataResponse: Validation result and submission status
    """
    try:
        # Check if user can validate
        if not current_user.can_validate:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have validation permissions"
            )

        # Verify submission exists and user can validate it
        can_validate = await validation_service.can_user_validate_submission(
            user_id=current_user.id,
            submission_id=submission_id,
            submission_type=None,  # Will be fetched from submission
            user_level=current_user.level
        )

        if not can_validate:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot validate this submission"
            )

        # Create validation
        validation_result = await validation_service.create_validation(
            validation_data=validation_data,
            validator_id=current_user.id
        )

        return DataResponse(
            data=validation_result,
            message="Validation submitted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation submission failed: {str(e)}"
        )


@router.get("/my-reviews", response_model=ListResponse)
async def get_user_validations(
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Get current user's validation history.

    Args:
        current_user: Authenticated user
        page: Page number
        page_size: Items per page

    Returns:
        ListResponse: User's validation history
    """
    try:
        validations, total_count = await validation_service.get_user_validations(
            validator_id=current_user.id,
            page=page,
            page_size=page_size
        )

        return ListResponse.create(
            items=validations,
            total_count=total_count,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve validation history: {str(e)}"
        )


@router.get("/consensus/{submission_id}", response_model=DataResponse)
async def get_validation_consensus(
    submission_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get validation consensus summary for a submission.

    Args:
        submission_id: Submission ID
        current_user: Authenticated user

    Returns:
        DataResponse: Validation consensus and tier eligibility
    """
    try:
        if not ObjectId.is_valid(submission_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid submission ID format"
            )

        consensus = await validation_service.get_validation_consensus(submission_id)

        if not consensus:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )

        return DataResponse(
            data=consensus,
            message="Validation consensus retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve consensus: {str(e)}"
        )


@router.post("/promote/{submission_id}", response_model=DataResponse)
async def promote_submission_tier(
    submission_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Promote submission to higher quality tier based on validations.

    Requires expert or guardian level permissions.

    Args:
        submission_id: Submission ID
        current_user: Authenticated user with promotion rights

    Returns:
        DataResponse: Promotion result
    """
    try:
        # Check permissions
        if current_user.level not in ["expert", "guardian"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to promote submissions"
            )

        if not ObjectId.is_valid(submission_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid submission ID format"
            )

        # Attempt promotion
        promotion_result = await validation_service.promote_submission_tier(
            submission_id, current_user.id
        )

        if not promotion_result["promoted"]:
            return DataResponse(
                data=promotion_result,
                message="Submission does not meet promotion requirements"
            )

        return DataResponse(
            data=promotion_result,
            message=f"Submission promoted to {promotion_result['new_tier']}"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Promotion failed: {str(e)}"
        )


@router.get("/queue/summary", response_model=DataResponse)
async def get_validation_queue_summary(
    current_user: User = Depends(get_current_user)
):
    """
    Get summary of validation queue for current user.

    Args:
        current_user: Authenticated user (must be validator)

    Returns:
        DataResponse: Queue summary with counts by language and type
    """
    try:
        if not current_user.can_validate:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have validation permissions"
            )

        queue_summary = await validation_service.get_validation_queue_summary(
            current_user.id
        )

        return DataResponse(
            data=queue_summary,
            message="Validation queue summary retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve queue summary: {str(e)}"
        )


@router.get("/stats/validator", response_model=DataResponse)
async def get_validator_statistics(
    current_user: User = Depends(get_current_user)
):
    """
    Get validation statistics for current user.

    Args:
        current_user: Authenticated user

    Returns:
        DataResponse: Validator performance statistics
    """
    try:
        stats = await validation_service.get_validator_statistics(current_user.id)

        return DataResponse(
            data=stats,
            message="Validator statistics retrieved successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve validator statistics: {str(e)}"
        )


@router.post("/dispute/{validation_id}", response_model=DataResponse)
async def dispute_validation(
    validation_id: str,
    dispute_reason: str,
    current_user: User = Depends(get_current_user)
):
    """
    Dispute a validation decision (for submission contributors).

    Args:
        validation_id: Validation ID to dispute
        dispute_reason: Reason for dispute
        current_user: Authenticated user

    Returns:
        DataResponse: Dispute submission result
    """
    try:
        if not ObjectId.is_valid(validation_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid validation ID format"
            )

        # Check if user can dispute this validation
        can_dispute = await validation_service.can_user_dispute_validation(
            validation_id, current_user.id
        )

        if not can_dispute:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot dispute this validation"
            )

        # Submit dispute
        dispute_result = await validation_service.create_validation_dispute(
            validation_id=validation_id,
            disputer_id=current_user.id,
            reason=dispute_reason
        )

        return DataResponse(
            data=dispute_result,
            message="Validation dispute submitted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dispute submission failed: {str(e)}"
        )