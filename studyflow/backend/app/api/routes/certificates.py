"""
Certificate API Routes for StudyFlow.

Provides certificate generation, verification, and management capabilities.

Features:
- Auto-generate certificates on course completion
- Public certificate verification
- PDF download
- Certificate revocation (admin)
- QR code verification

Author: KasaAI
Created: 2025-11-07
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import sys
import base64

# Add shared services to path
sys.path.insert(0, "/opt/kasaai/apps")

from apps.shared.services.certificate_service import (
    CertificateService,
    CertificateData
)

from app.core.database import MongoDB
from app.core.auth import get_current_user_with_org, OrganizationRoleChecker
from app.models.user import UserRole

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/certificates", tags=["Certificates"])

# Admin-only actions
require_admin = OrganizationRoleChecker([UserRole.ADMIN, UserRole.TEACHER])


# ============================================================================
# Request/Response Models
# ============================================================================

class CertificateGenerateRequest(BaseModel):
    """Request to generate certificate."""
    student_id: str
    student_name: str
    course_name: str = "Software Engineering Developer Onboarding"
    template: str = Field(default="default", description="Certificate template (default, professional, modern)")
    grade: Optional[float] = None
    instructor_name: Optional[str] = None


class CertificateResponse(BaseModel):
    """Certificate response."""
    certificate_id: str
    student_name: str
    course_name: str
    organization_name: str
    completion_date: datetime
    verification_url: str
    grade: Optional[float] = None
    issued_at: datetime
    is_verified: bool


class CertificateVerificationResponse(BaseModel):
    """Public certificate verification response."""
    valid: bool
    certificate_id: Optional[str] = None
    student_name: Optional[str] = None
    course_name: Optional[str] = None
    organization_name: Optional[str] = None
    completion_date: Optional[datetime] = None
    grade: Optional[float] = None
    issued_at: Optional[datetime] = None


# ============================================================================
# Helper Functions
# ============================================================================

def get_certificate_service() -> CertificateService:
    """Get certificate service instance."""
    return CertificateService(
        verification_base_url="https://studyflow.ailabsafrica.com/verify"
    )


async def check_course_completion(
    student_id: str,
    organization_id: str,
    db
) -> tuple[bool, float]:
    """
    Check if student has completed all required modules.

    Args:
        student_id: Student identifier
        organization_id: Organization identifier
        db: Database connection

    Returns:
        Tuple of (is_complete, average_score)
    """
    # Get all assessments for student
    assessments = await db["assessment_sessions"].find({
        "organization_id": organization_id,
        "user_id": student_id,
        "status": "completed"
    }).to_list(None)

    # Check if completed all 10 modules
    completed_modules = set()
    total_score = 0.0
    score_count = 0

    for assessment in assessments:
        module_num = assessment.get("metadata", {}).get("module_number")
        if module_num:
            completed_modules.add(module_num)
            score = assessment.get("overall_score", 0)
            total_score += score
            score_count += 1

    # Require all 10 modules to be completed
    is_complete = len(completed_modules) >= 10

    # Calculate average score (as percentage)
    avg_score = (total_score / score_count * 100) if score_count > 0 else 0

    return is_complete, avg_score


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/generate", response_model=CertificateResponse, status_code=status.HTTP_201_CREATED)
async def generate_certificate(
    request: CertificateGenerateRequest,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Generate certificate for student upon course completion.

    This endpoint is typically called automatically when a student completes
    all required modules. Can also be called manually by admins.

    Args:
        request: Certificate generation request
        user_context: User context with organization info

    Returns:
        Certificate information with verification URL

    Raises:
        HTTPException: If student hasn't completed course or certificate already exists
    """
    try:
        organization_id = user_context["organization_id"]
        db = MongoDB.get_database()

        # Check if student has completed the course
        is_complete, avg_score = await check_course_completion(
            request.student_id,
            organization_id,
            db
        )

        if not is_complete:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student has not completed all required modules"
            )

        # Get organization details
        org = await db["organizations"].find_one({"_id": organization_id})
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        organization_name = org.get("name", "KasaAI")

        # Generate certificate ID
        cert_service = get_certificate_service()
        completion_date = datetime.utcnow()

        certificate_id = cert_service.generate_certificate_id(
            request.student_id,
            "developer_onboarding",
            completion_date
        )

        # Check if certificate already exists
        existing = await db["certificates"].find_one({"certificate_id": certificate_id})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Certificate already exists for this student"
            )

        # Use provided grade or calculated average
        final_grade = request.grade if request.grade is not None else avg_score

        # Create certificate data
        cert_data = CertificateData(
            student_name=request.student_name,
            course_name=request.course_name,
            organization_name=organization_name,
            completion_date=completion_date,
            certificate_id=certificate_id,
            grade=final_grade,
            instructor_name=request.instructor_name,
            custom_fields={
                "student_id": request.student_id,
                "organization_id": organization_id,
                "course_id": "developer_onboarding"
            }
        )

        # Generate PDF
        pdf_bytes = cert_service.generate_pdf(cert_data, template=request.template)

        # Store certificate
        certificate_record = await cert_service.store_certificate(
            certificate_id,
            pdf_bytes,
            cert_data,
            db
        )

        # TODO: Send email with certificate

        logger.info(f"Certificate generated: {certificate_id} for student {request.student_id}")

        return CertificateResponse(
            certificate_id=certificate_id,
            student_name=request.student_name,
            course_name=request.course_name,
            organization_name=organization_name,
            completion_date=completion_date,
            verification_url=f"https://studyflow.ailabsafrica.com/verify/{certificate_id}",
            grade=final_grade,
            issued_at=datetime.utcnow(),
            is_verified=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate certificate: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate certificate: {str(e)}"
        )


@router.get("/verify/{certificate_id}", response_model=CertificateVerificationResponse)
async def verify_certificate(certificate_id: str):
    """
    Verify certificate by ID (public endpoint).

    This endpoint is publicly accessible and can be used to verify the
    authenticity of a certificate using its ID or QR code.

    Args:
        certificate_id: Certificate identifier

    Returns:
        Certificate verification data
    """
    try:
        db = MongoDB.get_database()
        cert_service = get_certificate_service()

        # Verify certificate
        certificate = await cert_service.verify_certificate(certificate_id, db)

        if certificate:
            return CertificateVerificationResponse(
                valid=True,
                certificate_id=certificate["certificate_id"],
                student_name=certificate["student_name"],
                course_name=certificate["course_name"],
                organization_name=certificate["organization_name"],
                completion_date=certificate["completion_date"],
                grade=certificate.get("grade"),
                issued_at=certificate["issued_at"]
            )
        else:
            return CertificateVerificationResponse(valid=False)

    except Exception as e:
        logger.error(f"Failed to verify certificate: {str(e)}", exc_info=True)
        return CertificateVerificationResponse(valid=False)


@router.get("/me", response_model=List[CertificateResponse])
async def get_my_certificates(
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get all certificates for current user.

    Returns:
        List of user's certificates
    """
    try:
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]
        db = MongoDB.get_database()

        cert_service = get_certificate_service()

        # Get certificates
        certificates = await cert_service.get_student_certificates(
            user_id,
            organization_id,
            db
        )

        # Convert to response models
        response = []
        for cert in certificates:
            response.append(CertificateResponse(
                certificate_id=cert["certificate_id"],
                student_name=cert["student_name"],
                course_name=cert["course_name"],
                organization_name=cert["organization_name"],
                completion_date=cert["completion_date"],
                verification_url=cert["verification_url"],
                grade=cert.get("grade"),
                issued_at=cert["issued_at"],
                is_verified=cert.get("is_verified", True)
            ))

        return response

    except Exception as e:
        logger.error(f"Failed to get certificates: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get certificates: {str(e)}"
        )


@router.get("/{certificate_id}/download")
async def download_certificate(
    certificate_id: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Download certificate PDF.

    Args:
        certificate_id: Certificate identifier
        user_context: User context

    Returns:
        PDF file
    """
    try:
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]
        db = MongoDB.get_database()

        # Get certificate
        certificate = await db["certificates"].find_one({"certificate_id": certificate_id})

        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificate not found"
            )

        # Check ownership (students can only download their own)
        if certificate.get("custom_fields", {}).get("student_id") != user_id:
            # Check if user is admin
            is_admin = user_context.get("role") in [UserRole.ADMIN, UserRole.TEACHER]
            if not is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to download this certificate"
                )

        # Regenerate PDF (or retrieve from storage)
        cert_service = get_certificate_service()
        cert_data = CertificateData(
            student_name=certificate["student_name"],
            course_name=certificate["course_name"],
            organization_name=certificate["organization_name"],
            completion_date=certificate["completion_date"],
            certificate_id=certificate["certificate_id"],
            grade=certificate.get("grade"),
            instructor_name=certificate.get("instructor_name"),
            custom_fields=certificate.get("custom_fields")
        )

        pdf_bytes = cert_service.generate_pdf(cert_data)

        # Return PDF
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="certificate_{certificate_id}.pdf"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download certificate: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download certificate: {str(e)}"
        )


@router.post("/{certificate_id}/revoke")
async def revoke_certificate(
    certificate_id: str,
    reason: str,
    user_context: dict = Depends(require_admin)
):
    """
    Revoke a certificate (admin only).

    Args:
        certificate_id: Certificate identifier
        reason: Revocation reason
        user_context: Admin user context

    Returns:
        Success message
    """
    try:
        db = MongoDB.get_database()
        cert_service = get_certificate_service()

        # Revoke certificate
        success = await cert_service.revoke_certificate(certificate_id, reason, db)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificate not found"
            )

        return {
            "message": "Certificate revoked successfully",
            "certificate_id": certificate_id,
            "reason": reason
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke certificate: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke certificate: {str(e)}"
        )


@router.get("/organization/all", response_model=List[CertificateResponse])
async def get_organization_certificates(
    user_context: dict = Depends(require_admin)
):
    """
    Get all certificates for organization (admin only).

    Returns:
        List of all certificates in organization
    """
    try:
        organization_id = user_context["organization_id"]
        db = MongoDB.get_database()

        # Get all certificates for organization
        certificates = await db["certificates"].find({
            "custom_fields.organization_id": organization_id
        }).to_list(None)

        # Convert to response models
        response = []
        for cert in certificates:
            response.append(CertificateResponse(
                certificate_id=cert["certificate_id"],
                student_name=cert["student_name"],
                course_name=cert["course_name"],
                organization_name=cert["organization_name"],
                completion_date=cert["completion_date"],
                verification_url=cert["verification_url"],
                grade=cert.get("grade"),
                issued_at=cert["issued_at"],
                is_verified=cert.get("is_verified", True)
            ))

        return response

    except Exception as e:
        logger.error(f"Failed to get organization certificates: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get organization certificates: {str(e)}"
        )
