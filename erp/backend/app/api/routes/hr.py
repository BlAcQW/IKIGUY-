"""HR (Human Resources) Routes."""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import FileResponse
from datetime import datetime
from pathlib import Path

from app.core.database import MongoDB
from app.models.hr import (
    Employee, EmployeeCreate,
    Payroll, PayrollCreate,
    Benefit, BenefitCreate,
    Recruitment, RecruitmentCreate,
    EmploymentStatus
)
from app.services.file_upload_service import get_file_upload_service
from app.config import settings
from apps.shared.dependencies import require_organization_access, OrganizationScoped
from apps.shared.services.email_account_service import (
    get_email_account_service,
    EmailAccountError,
    EmailAlreadyExistsError
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/employees", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_employee(employee_create: EmployeeCreate, scope: OrganizationScoped = Depends()):
    """
    Create a new employee and automatically create email account.

    Returns employee data with temporary password if email was created.
    """
    from datetime import datetime, date

    db = MongoDB.get_database()
    email_service = get_email_account_service()

    # Auto-generate employee_id
    # Find the highest employee number for this organization
    last_employee = await db.employees.find_one(
        {"organization_id": scope.org_id},
        sort=[("employee_id", -1)]
    )

    if last_employee and last_employee.get("employee_id"):
        # Extract number from last employee_id (e.g., "EMP001" -> 1)
        try:
            last_num = int(last_employee["employee_id"].replace("EMP", ""))
            next_num = last_num + 1
        except (ValueError, AttributeError):
            next_num = 1
    else:
        next_num = 1

    employee_id = f"EMP{next_num:03d}"  # Format as EMP001, EMP002, etc.

    employee_data = Employee(
        **employee_create.model_dump(),
        employee_id=employee_id,
        organization_id=scope.org_id,
        created_by=scope.user.get("id") or scope.user.get("sub")
    )

    # Convert date objects to datetime for MongoDB
    employee_dict = employee_data.model_dump()
    for key, value in employee_dict.items():
        if isinstance(value, date) and not isinstance(value, datetime):
            employee_dict[key] = datetime.combine(value, datetime.min.time())

    # Insert employee first (primary data always saved)
    await db.employees.insert_one(employee_dict)
    logger.info(f"Employee {employee_id} created in org {scope.org_id}")

    # Attempt to create email account (non-blocking - employee still created if this fails)
    email_result = {
        "email_created": False,
        "temporary_password": None,
        "email_error": None
    }

    try:
        # Create email account
        account_result = await email_service.create_account(
            first_name=employee_data.first_name,
            last_name=employee_data.last_name,
            email=employee_data.email  # Use the email from employee data
        )

        # Update employee record with email account details
        await db.employees.update_one(
            {"id": employee_data.id},
            {
                "$set": {
                    "email_account_created": True,
                    "email_account_created_at": datetime.utcnow(),
                    "email_account_status": "active",
                    "email_temporary_password": account_result["password"]
                }
            }
        )

        email_result["email_created"] = True
        email_result["temporary_password"] = account_result["password"]
        logger.info(f"Email account created for employee {employee_id}: {account_result['email']}")

        # Log the operation
        await db.email_account_operations.insert_one({
            "organization_id": scope.org_id,
            "employee_id": employee_data.id,
            "employee_number": employee_id,
            "email": account_result["email"],
            "operation": "create",
            "status": "success",
            "created_at": datetime.utcnow(),
            "created_by": scope.user.get("id") or scope.user.get("sub")
        })

    except EmailAlreadyExistsError as e:
        logger.warning(f"Email account already exists for {employee_data.email}: {e}")
        email_result["email_error"] = f"Email account already exists: {str(e)}"

        # Update employee with failed status
        await db.employees.update_one(
            {"id": employee_data.id},
            {"$set": {"email_account_status": "failed"}}
        )

        # Log the error
        await db.email_account_operations.insert_one({
            "organization_id": scope.org_id,
            "employee_id": employee_data.id,
            "employee_number": employee_id,
            "email": employee_data.email,
            "operation": "create",
            "status": "failed",
            "error_message": str(e),
            "created_at": datetime.utcnow(),
            "created_by": scope.user.get("id") or scope.user.get("sub")
        })

    except EmailAccountError as e:
        logger.error(f"Failed to create email account for {employee_id}: {e}")
        email_result["email_error"] = str(e)

        # Update employee with failed status
        await db.employees.update_one(
            {"id": employee_data.id},
            {"$set": {"email_account_status": "failed"}}
        )

        # Log the error
        await db.email_account_operations.insert_one({
            "organization_id": scope.org_id,
            "employee_id": employee_data.id,
            "employee_number": employee_id,
            "email": employee_data.email,
            "operation": "create",
            "status": "failed",
            "error_message": str(e),
            "created_at": datetime.utcnow(),
            "created_by": scope.user.get("id") or scope.user.get("sub")
        })

    # Return employee data with email creation result
    return {
        "employee": employee_data.model_dump(),
        "email_account": email_result
    }


@router.get("/employees", response_model=List[Employee])
async def list_employees(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    department: Optional[str] = None,
    position: Optional[str] = None,
):
    """List all employees."""
    db = MongoDB.get_database()

    query = {"organization_id": org_id, "is_active": True}

    # Search
    if search:
        query["$or"] = [
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"employee_id": {"$regex": search, "$options": "i"}},
        ]

    # Filters
    if department:
        query["department"] = department
    if position:
        query["position"] = position

    cursor = db.employees.find(query).skip(skip).limit(limit).sort("created_at", -1)
    employees = await cursor.to_list(length=limit)
    return [Employee(**e) for e in employees]


@router.get("/employees/{employee_id}", response_model=Employee)
async def get_employee(employee_id: str, org_id: str = Depends(require_organization_access)):
    """Get employee by ID."""
    db = MongoDB.get_database()
    employee = await db.employees.find_one({"id": employee_id, "organization_id": org_id})
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return Employee(**employee)


@router.patch("/employees/{employee_id}", response_model=Dict[str, Any])
async def update_employee(
    employee_id: str,
    update_data: dict,
    scope: OrganizationScoped = Depends(),
):
    """
    Update employee.

    Automatically disables email account if employment_status changes to 'terminated'.
    """
    db = MongoDB.get_database()
    email_service = get_email_account_service()

    # Get current employee data to check status change
    current_employee = await db.employees.find_one({"id": employee_id, "organization_id": scope.org_id})
    if not current_employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    # Remove fields that shouldn't be updated
    update_data.pop("id", None)
    update_data.pop("organization_id", None)
    update_data.pop("created_at", None)
    update_data["updated_by"] = scope.user.get("id") or scope.user.get("sub")

    # Check if employment status is changing to terminated
    status_changed_to_terminated = (
        "employment_status" in update_data and
        update_data["employment_status"] == EmploymentStatus.TERMINATED.value and
        current_employee.get("employment_status") != EmploymentStatus.TERMINATED.value
    )

    result = await db.employees.update_one(
        {"id": employee_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    # Disable email account if employee was terminated
    email_result = {"email_disabled": False, "email_error": None}

    if status_changed_to_terminated:
        employee_email = current_employee.get("email")
        if employee_email and current_employee.get("email_account_created"):
            try:
                await email_service.disable_account(employee_email)

                # Update employee with disabled status
                await db.employees.update_one(
                    {"id": employee_id},
                    {"$set": {"email_account_status": "disabled"}}
                )

                email_result["email_disabled"] = True
                logger.info(f"Email account disabled for terminated employee: {employee_email}")

                # Log the operation
                await db.email_account_operations.insert_one({
                    "organization_id": scope.org_id,
                    "employee_id": employee_id,
                    "employee_number": current_employee.get("employee_id"),
                    "email": employee_email,
                    "operation": "disable",
                    "status": "success",
                    "reason": "employee_terminated",
                    "created_at": datetime.utcnow(),
                    "created_by": scope.user.get("id") or scope.user.get("sub")
                })

            except EmailAccountError as e:
                logger.error(f"Failed to disable email account for {employee_email}: {e}")
                email_result["email_error"] = str(e)

                # Log the error
                await db.email_account_operations.insert_one({
                    "organization_id": scope.org_id,
                    "employee_id": employee_id,
                    "employee_number": current_employee.get("employee_id"),
                    "email": employee_email,
                    "operation": "disable",
                    "status": "failed",
                    "error_message": str(e),
                    "reason": "employee_terminated",
                    "created_at": datetime.utcnow(),
                    "created_by": scope.user.get("id") or scope.user.get("sub")
                })

    employee = await db.employees.find_one({"id": employee_id})

    return {
        "employee": Employee(**employee).model_dump(),
        "email_action": email_result
    }


@router.delete("/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: str,
    scope: OrganizationScoped = Depends(),
):
    """
    Soft delete employee.

    Automatically disables the email account when employee is deactivated.
    """
    db = MongoDB.get_database()
    email_service = get_email_account_service()

    # Get employee data first
    employee = await db.employees.find_one({"id": employee_id, "organization_id": scope.org_id})
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    # Disable email account if it was created
    employee_email = employee.get("email")
    if employee_email and employee.get("email_account_created"):
        try:
            await email_service.disable_account(employee_email)
            logger.info(f"Email account disabled for deleted employee: {employee_email}")

            # Log the operation
            await db.email_account_operations.insert_one({
                "organization_id": scope.org_id,
                "employee_id": employee_id,
                "employee_number": employee.get("employee_id"),
                "email": employee_email,
                "operation": "disable",
                "status": "success",
                "reason": "employee_deleted",
                "created_at": datetime.utcnow(),
                "created_by": scope.user.get("id") or scope.user.get("sub")
            })

        except EmailAccountError as e:
            logger.error(f"Failed to disable email account for {employee_email}: {e}")
            # Continue with deletion even if email disable fails

    # Soft delete employee
    result = await db.employees.update_one(
        {"id": employee_id, "organization_id": scope.org_id},
        {"$set": {
            "is_active": False,
            "email_account_status": "disabled"
        }}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    return None


@router.post("/payroll", response_model=Payroll, status_code=status.HTTP_201_CREATED)
async def create_payroll(payroll_create: PayrollCreate, scope: OrganizationScoped = Depends()):
    """Create a payroll record."""
    from datetime import datetime, date

    db = MongoDB.get_database()

    payroll_data = Payroll(
        **payroll_create.model_dump(),
        organization_id=scope.org_id
    )

    # Convert date objects to datetime for MongoDB
    payroll_dict = payroll_data.model_dump()
    for key, value in payroll_dict.items():
        if isinstance(value, date) and not isinstance(value, datetime):
            payroll_dict[key] = datetime.combine(value, datetime.min.time())

    await db.payroll.insert_one(payroll_dict)
    return payroll_data


@router.get("/payroll", response_model=List[Payroll])
async def list_payroll(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    employee_id: Optional[str] = None,
):
    """List payroll records."""
    db = MongoDB.get_database()

    query = {"organization_id": org_id, "is_active": True}
    if employee_id:
        query["employee_id"] = employee_id

    cursor = db.payroll.find(query).skip(skip).limit(limit).sort("pay_period_start", -1)
    records = await cursor.to_list(length=limit)
    return [Payroll(**r) for r in records]


@router.get("/payroll/{payroll_id}", response_model=Payroll)
async def get_payroll(
    payroll_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get payroll record by ID."""
    db = MongoDB.get_database()
    payroll = await db.payroll.find_one({"id": payroll_id, "organization_id": org_id})

    if not payroll:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payroll record not found")

    return Payroll(**payroll)


@router.patch("/payroll/{payroll_id}", response_model=Payroll)
async def update_payroll(
    payroll_id: str,
    update_data: dict,
    scope: OrganizationScoped = Depends(),
):
    """Update payroll record."""
    db = MongoDB.get_database()

    # Remove fields that shouldn't be updated
    update_data.pop("id", None)
    update_data.pop("organization_id", None)
    update_data.pop("created_at", None)

    result = await db.payroll.update_one(
        {"id": payroll_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payroll record not found")

    payroll = await db.payroll.find_one({"id": payroll_id})
    return Payroll(**payroll)


@router.delete("/payroll/{payroll_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payroll(
    payroll_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Soft delete payroll record."""
    db = MongoDB.get_database()

    result = await db.payroll.update_one(
        {"id": payroll_id, "organization_id": org_id},
        {"$set": {"is_active": False}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payroll record not found")

    return None


@router.post("/benefits", response_model=Benefit, status_code=status.HTTP_201_CREATED)
async def create_benefit(
    benefit_create: BenefitCreate,
    scope: OrganizationScoped = Depends(),
):
    """Create a new benefit."""
    db = MongoDB.get_database()

    benefit_data = Benefit(
        **benefit_create.model_dump(),
        organization_id=scope.org_id,
        created_by=scope.user.get("id") or scope.user.get("sub")
    )

    await db.benefits.insert_one(benefit_data.model_dump())
    logger.info(f"Benefit {benefit_data.id} created in org {scope.org_id}")
    return benefit_data


@router.get("/benefits", response_model=List[Benefit])
async def list_benefits(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    benefit_type: Optional[str] = None,
):
    """List all benefits."""
    db = MongoDB.get_database()

    query = {"organization_id": org_id, "is_active": True}

    # Search
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    # Filter
    if benefit_type:
        query["benefit_type"] = benefit_type

    cursor = db.benefits.find(query).skip(skip).limit(limit).sort("created_at", -1)
    benefits = await cursor.to_list(length=limit)
    return [Benefit(**b) for b in benefits]


@router.get("/benefits/{benefit_id}", response_model=Benefit)
async def get_benefit(
    benefit_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get benefit by ID."""
    db = MongoDB.get_database()
    benefit = await db.benefits.find_one({"id": benefit_id, "organization_id": org_id})

    if not benefit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benefit not found")

    return Benefit(**benefit)


@router.patch("/benefits/{benefit_id}", response_model=Benefit)
async def update_benefit(
    benefit_id: str,
    update_data: dict,
    scope: OrganizationScoped = Depends(),
):
    """Update benefit."""
    db = MongoDB.get_database()

    # Remove fields that shouldn't be updated
    update_data.pop("id", None)
    update_data.pop("organization_id", None)
    update_data.pop("created_at", None)
    update_data["updated_by"] = scope.user.get("id") or scope.user.get("sub")

    result = await db.benefits.update_one(
        {"id": benefit_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benefit not found")

    benefit = await db.benefits.find_one({"id": benefit_id})
    return Benefit(**benefit)


@router.delete("/benefits/{benefit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_benefit(
    benefit_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Soft delete benefit."""
    db = MongoDB.get_database()

    result = await db.benefits.update_one(
        {"id": benefit_id, "organization_id": org_id},
        {"$set": {"is_active": False}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benefit not found")

    return None


@router.post("/recruitment", response_model=Recruitment, status_code=status.HTTP_201_CREATED)
async def create_job_opening(recruitment_create: RecruitmentCreate, scope: OrganizationScoped = Depends()):
    """Create a job opening."""
    from datetime import datetime, date

    db = MongoDB.get_database()

    recruitment_data = Recruitment(
        **recruitment_create.model_dump(),
        organization_id=scope.org_id
    )

    # Convert date objects to datetime for MongoDB
    recruitment_dict = recruitment_data.model_dump()
    for key, value in recruitment_dict.items():
        if isinstance(value, date) and not isinstance(value, datetime):
            recruitment_dict[key] = datetime.combine(value, datetime.min.time())

    await db.recruitment.insert_one(recruitment_dict)
    return recruitment_data


@router.get("/recruitment", response_model=List[Recruitment])
async def list_job_openings(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    department: Optional[str] = None,
):
    """List all job openings."""
    db = MongoDB.get_database()

    query = {"organization_id": org_id, "is_active": True}

    # Search
    if search:
        query["$or"] = [
            {"job_title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    # Filters
    if status_filter:
        query["status"] = status_filter
    if department:
        query["department"] = department

    cursor = db.recruitment.find(query).skip(skip).limit(limit).sort("posted_date", -1)
    openings = await cursor.to_list(length=limit)
    return [Recruitment(**o) for o in openings]


@router.get("/recruitment/{recruitment_id}", response_model=Recruitment)
async def get_job_opening(
    recruitment_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get job opening by ID."""
    db = MongoDB.get_database()
    opening = await db.recruitment.find_one({"id": recruitment_id, "organization_id": org_id})

    if not opening:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job opening not found")

    return Recruitment(**opening)


@router.patch("/recruitment/{recruitment_id}", response_model=Recruitment)
async def update_job_opening(
    recruitment_id: str,
    update_data: dict,
    scope: OrganizationScoped = Depends(),
):
    """Update job opening."""
    db = MongoDB.get_database()

    # Remove fields that shouldn't be updated
    update_data.pop("id", None)
    update_data.pop("organization_id", None)
    update_data.pop("created_at", None)

    result = await db.recruitment.update_one(
        {"id": recruitment_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job opening not found")

    opening = await db.recruitment.find_one({"id": recruitment_id})
    return Recruitment(**opening)


@router.delete("/recruitment/{recruitment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_opening(
    recruitment_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Soft delete job opening."""
    db = MongoDB.get_database()

    result = await db.recruitment.update_one(
        {"id": recruitment_id, "organization_id": org_id},
        {"$set": {"is_active": False}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job opening not found")

    return None


# ============================================================================
# FILE UPLOAD ENDPOINTS
# ============================================================================

@router.post("/employees/{employee_id}/upload-cv", response_model=Dict[str, Any])
async def upload_employee_cv(
    employee_id: str,
    file: UploadFile = File(...),
    scope: OrganizationScoped = Depends(),
):
    """
    Upload CV for an employee.

    Args:
        employee_id: Employee ID
        file: CV file (PDF, DOC, DOCX)
        scope: Organization scope

    Returns:
        Updated employee data with CV URL
    """
    db = MongoDB.get_database()
    file_service = get_file_upload_service()

    # Check if employee exists
    employee = await db.employees.find_one({"id": employee_id, "organization_id": scope.org_id})
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    # Delete old CV if exists
    if employee.get("cv_url"):
        file_service.delete_file(employee["cv_url"])

    # Save new CV
    try:
        cv_path = await file_service.save_file(
            file=file,
            organization_id=scope.org_id,
            employee_id=employee_id,
            file_type="cv"
        )

        # Update employee record
        await db.employees.update_one(
            {"id": employee_id},
            {"$set": {"cv_url": cv_path, "updated_by": scope.user.get("id") or scope.user.get("sub")}}
        )

        logger.info(f"CV uploaded for employee {employee_id}")

        return {
            "success": True,
            "message": "CV uploaded successfully",
            "cv_url": cv_path
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload CV: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload CV: {str(e)}"
        )


@router.post("/employees/{employee_id}/upload-certificate", response_model=Dict[str, Any])
async def upload_employee_certificate(
    employee_id: str,
    certificate_name: str = Query(..., description="Name/title of the certificate"),
    file: UploadFile = File(...),
    scope: OrganizationScoped = Depends(),
):
    """
    Upload certificate for an employee.

    Args:
        employee_id: Employee ID
        certificate_name: Name/title of certificate
        file: Certificate file (PDF, JPG, PNG)
        scope: Organization scope

    Returns:
        Updated employee data with certificate added
    """
    db = MongoDB.get_database()
    file_service = get_file_upload_service()

    # Check if employee exists
    employee = await db.employees.find_one({"id": employee_id, "organization_id": scope.org_id})
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    # Save certificate file
    try:
        cert_path = await file_service.save_file(
            file=file,
            organization_id=scope.org_id,
            employee_id=employee_id,
            file_type="certificates"
        )

        # Add certificate to employee's certificates list
        certificate_entry = {
            "name": certificate_name,
            "url": cert_path,
            "uploaded_at": datetime.utcnow().isoformat()
        }

        certificates = employee.get("certificates", [])
        certificates.append(certificate_entry)

        # Update employee record
        await db.employees.update_one(
            {"id": employee_id},
            {
                "$set": {
                    "certificates": certificates,
                    "updated_by": scope.user.get("id") or scope.user.get("sub")
                }
            }
        )

        logger.info(f"Certificate '{certificate_name}' uploaded for employee {employee_id}")

        return {
            "success": True,
            "message": "Certificate uploaded successfully",
            "certificate": certificate_entry
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload certificate: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload certificate: {str(e)}"
        )


@router.delete("/employees/{employee_id}/certificates/{certificate_index}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee_certificate(
    employee_id: str,
    certificate_index: int,
    scope: OrganizationScoped = Depends(),
):
    """
    Delete a certificate from employee's certificates list.

    Args:
        employee_id: Employee ID
        certificate_index: Index of certificate in the list
        scope: Organization scope
    """
    db = MongoDB.get_database()
    file_service = get_file_upload_service()

    # Check if employee exists
    employee = await db.employees.find_one({"id": employee_id, "organization_id": scope.org_id})
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    certificates = employee.get("certificates", [])

    if certificate_index < 0 or certificate_index >= len(certificates):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")

    # Delete file from disk
    cert_to_delete = certificates[certificate_index]
    file_service.delete_file(cert_to_delete["url"])

    # Remove from list
    certificates.pop(certificate_index)

    # Update employee record
    await db.employees.update_one(
        {"id": employee_id},
        {
            "$set": {
                "certificates": certificates,
                "updated_by": scope.user.get("id") or scope.user.get("sub")
            }
        }
    )

    logger.info(f"Certificate deleted for employee {employee_id}")
    return None


@router.get("/files/{file_path:path}")
async def get_file(
    file_path: str,
    org_id: str = Depends(require_organization_access),
):
    """
    Serve uploaded files.

    Args:
        file_path: Relative path to file
        org_id: Organization ID (for access control)

    Returns:
        File response
    """
    # Construct full path
    full_path = Path(settings.UPLOAD_DIR) / file_path

    # Security check: ensure file is within upload directory
    try:
        full_path = full_path.resolve()
        upload_dir = Path(settings.UPLOAD_DIR).resolve()
        if not str(full_path).startswith(str(upload_dir)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid file path")

    # Check if file exists
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    # Verify organization access (file path should contain org_id)
    if org_id not in str(file_path):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return FileResponse(full_path)
