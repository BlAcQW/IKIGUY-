"""System Routes (Integrations, Workflows, Audit Logs)."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.core.database import MongoDB
from app.models.system import (
    Integration, Workflow, AuditLog,
    Department, DepartmentCreate,
    CostCenter, CostCenterCreate
)
from apps.shared.dependencies import require_organization_access, require_organization_admin_role, OrganizationScoped

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/integrations", response_model=Integration, status_code=status.HTTP_201_CREATED)
async def create_integration(
    integration_data: Integration,
    org_id: str = Depends(require_organization_admin_role),
    scope: OrganizationScoped = Depends(),
):
    """Create a new integration (admin only)."""
    db = MongoDB.get_database()
    integration_data.organization_id = scope.org_id
    await db.integrations.insert_one(integration_data.model_dump())
    return integration_data


@router.get("/integrations", response_model=List[Integration])
async def list_integrations(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    integration_type: Optional[str] = None,
    is_active: Optional[bool] = None,
):
    """List all integrations."""
    db = MongoDB.get_database()

    query = {"organization_id": org_id}

    # Search
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    # Filters
    if integration_type:
        query["integration_type"] = integration_type
    if is_active is not None:
        query["is_active"] = is_active

    cursor = db.integrations.find(query).skip(skip).limit(limit).sort("created_at", -1)
    integrations = await cursor.to_list(length=limit)
    return [Integration(**i) for i in integrations]


@router.get("/integrations/{integration_id}", response_model=Integration)
async def get_integration(
    integration_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get integration by ID."""
    db = MongoDB.get_database()
    integration = await db.integrations.find_one({"id": integration_id, "organization_id": org_id})

    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")

    return Integration(**integration)


@router.patch("/integrations/{integration_id}", response_model=Integration)
async def update_integration(
    integration_id: str,
    update_data: dict,
    org_id: str = Depends(require_organization_admin_role),
    scope: OrganizationScoped = Depends(),
):
    """Update integration (admin only)."""
    db = MongoDB.get_database()

    update_data.pop("id", None)
    update_data.pop("organization_id", None)
    update_data.pop("created_at", None)

    result = await db.integrations.update_one(
        {"id": integration_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")

    integration = await db.integrations.find_one({"id": integration_id})
    return Integration(**integration)


@router.delete("/integrations/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    integration_id: str,
    org_id: str = Depends(require_organization_admin_role),
):
    """Delete integration (admin only)."""
    db = MongoDB.get_database()

    result = await db.integrations.delete_one(
        {"id": integration_id, "organization_id": org_id}
    )

    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")

    return None


@router.post("/workflows", response_model=Workflow, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow_data: Workflow,
    org_id: str = Depends(require_organization_admin_role),
    scope: OrganizationScoped = Depends(),
):
    """Create a new workflow (admin only)."""
    db = MongoDB.get_database()
    workflow_data.organization_id = scope.org_id
    await db.workflows.insert_one(workflow_data.model_dump())
    return workflow_data


@router.get("/workflows", response_model=List[Workflow])
async def list_workflows(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    trigger_type: Optional[str] = None,
):
    """List all workflows."""
    db = MongoDB.get_database()

    query = {"organization_id": org_id}

    # Search
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    # Filters
    if is_active is not None:
        query["is_active"] = is_active
    if trigger_type:
        query["trigger_type"] = trigger_type

    cursor = db.workflows.find(query).skip(skip).limit(limit).sort("created_at", -1)
    workflows = await cursor.to_list(length=limit)
    return [Workflow(**w) for w in workflows]


@router.get("/workflows/{workflow_id}", response_model=Workflow)
async def get_workflow(
    workflow_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get workflow by ID."""
    db = MongoDB.get_database()
    workflow = await db.workflows.find_one({"id": workflow_id, "organization_id": org_id})

    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    return Workflow(**workflow)


@router.patch("/workflows/{workflow_id}", response_model=Workflow)
async def update_workflow(
    workflow_id: str,
    update_data: dict,
    org_id: str = Depends(require_organization_admin_role),
    scope: OrganizationScoped = Depends(),
):
    """Update workflow (admin only)."""
    db = MongoDB.get_database()

    update_data.pop("id", None)
    update_data.pop("organization_id", None)
    update_data.pop("created_at", None)

    result = await db.workflows.update_one(
        {"id": workflow_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    workflow = await db.workflows.find_one({"id": workflow_id})
    return Workflow(**workflow)


@router.delete("/workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: str,
    org_id: str = Depends(require_organization_admin_role),
):
    """Delete workflow (admin only)."""
    db = MongoDB.get_database()

    result = await db.workflows.delete_one(
        {"id": workflow_id, "organization_id": org_id}
    )

    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    return None


@router.get("/audit-logs", response_model=List[AuditLog])
async def list_audit_logs(
    org_id: str = Depends(require_organization_admin_role),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    resource_type: Optional[str] = None,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
):
    """List audit logs (admin only)."""
    db = MongoDB.get_database()

    query = {"organization_id": org_id}

    # Filters
    if resource_type:
        query["resource_type"] = resource_type
    if user_id:
        query["user_id"] = user_id
    if action:
        query["action"] = action

    cursor = db.audit_logs.find(query).skip(skip).limit(limit).sort("created_at", -1)
    logs = await cursor.to_list(length=limit)
    return [AuditLog(**log) for log in logs]


# ============================================================================
# DEPARTMENTS
# ============================================================================

@router.post("/departments", response_model=Department, status_code=status.HTTP_201_CREATED)
async def create_department(department_create: DepartmentCreate, scope: OrganizationScoped = Depends()):
    """Create a new department."""
    db = MongoDB.get_database()

    # Auto-generate code if not provided
    if not department_create.code:
        # Generate code from department name (e.g., "Human Resources" -> "HR", "IT Department" -> "IT")
        name_parts = department_create.name.upper().split()
        if len(name_parts) == 1:
            base_code = name_parts[0][:3]  # Take first 3 characters
        else:
            # Take first letter of each word
            base_code = "".join([part[0] for part in name_parts if part])

        # Ensure uniqueness by appending a number if needed
        code = base_code
        counter = 1
        while True:
            existing = await db.departments.find_one({
                "code": code,
                "organization_id": scope.org_id,
                "is_active": True
            })
            if not existing:
                break
            code = f"{base_code}{counter}"
            counter += 1

        department_create.code = code
    else:
        # Check for duplicate code if manually provided
        existing = await db.departments.find_one({
            "code": department_create.code,
            "organization_id": scope.org_id,
            "is_active": True
        })
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Department with code '{department_create.code}' already exists"
            )

    department_data = Department(
        **department_create.model_dump(),
        organization_id=scope.org_id,
        created_by=scope.user.get("id") or scope.user.get("sub")
    )

    await db.departments.insert_one(department_data.model_dump())
    logger.info(f"Department {department_data.id} created in org {scope.org_id} with code {department_data.code}")
    return department_data


@router.get("/departments", response_model=List[Department])
async def list_departments(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    parent_id: Optional[str] = None,
):
    """List all departments."""
    db = MongoDB.get_database()

    query = {"organization_id": org_id, "is_active": True}

    # Search
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    # Filter by parent
    if parent_id:
        query["parent_department_id"] = parent_id

    cursor = db.departments.find(query).skip(skip).limit(limit).sort("name", 1)
    departments = await cursor.to_list(length=limit)
    return [Department(**d) for d in departments]


@router.get("/departments/{department_id}", response_model=Department)
async def get_department(department_id: str, org_id: str = Depends(require_organization_access)):
    """Get department by ID."""
    db = MongoDB.get_database()
    department = await db.departments.find_one({"id": department_id, "organization_id": org_id})
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return Department(**department)


@router.patch("/departments/{department_id}", response_model=Department)
async def update_department(
    department_id: str,
    update_data: dict,
    scope: OrganizationScoped = Depends(),
):
    """Update department."""
    db = MongoDB.get_database()

    # Remove fields that shouldn't be updated
    update_data.pop("id", None)
    update_data.pop("organization_id", None)
    update_data.pop("created_at", None)
    update_data["updated_by"] = scope.user.get("id") or scope.user.get("sub")

    # Check for duplicate code if updating code
    if "code" in update_data:
        existing = await db.departments.find_one({
            "code": update_data["code"],
            "organization_id": scope.org_id,
            "id": {"$ne": department_id},
            "is_active": True
        })
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Department with code '{update_data['code']}' already exists"
            )

    result = await db.departments.update_one(
        {"id": department_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    department = await db.departments.find_one({"id": department_id})
    return Department(**department)


@router.delete("/departments/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Soft delete department."""
    db = MongoDB.get_database()

    # Check if any employees are in this department
    employee_count = await db.employees.count_documents({
        "department": department_id,
        "organization_id": org_id,
        "is_active": True
    })
    if employee_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete department with {employee_count} active employees"
        )

    result = await db.departments.update_one(
        {"id": department_id, "organization_id": org_id},
        {"$set": {"is_active": False}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    return None


# ============================================================================
# COST CENTERS
# ============================================================================

@router.post("/cost-centers", response_model=CostCenter, status_code=status.HTTP_201_CREATED)
async def create_cost_center(cost_center_create: CostCenterCreate, scope: OrganizationScoped = Depends()):
    """Create a new cost center."""
    db = MongoDB.get_database()

    # Check for duplicate code
    existing = await db.cost_centers.find_one({
        "code": cost_center_create.code,
        "organization_id": scope.org_id,
        "is_active": True
    })
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cost center with code '{cost_center_create.code}' already exists"
        )

    cost_center_data = CostCenter(
        **cost_center_create.model_dump(),
        organization_id=scope.org_id,
        created_by=scope.user.get("id") or scope.user.get("sub")
    )

    await db.cost_centers.insert_one(cost_center_data.model_dump())
    logger.info(f"Cost center {cost_center_data.id} created in org {scope.org_id}")
    return cost_center_data


@router.get("/cost-centers", response_model=List[CostCenter])
async def list_cost_centers(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    cost_center_type: Optional[str] = None,
    department_id: Optional[str] = None,
):
    """List all cost centers."""
    db = MongoDB.get_database()

    query = {"organization_id": org_id, "is_active": True}

    # Search
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    # Filters
    if cost_center_type:
        query["cost_center_type"] = cost_center_type
    if department_id:
        query["department_id"] = department_id

    cursor = db.cost_centers.find(query).skip(skip).limit(limit).sort("name", 1)
    cost_centers = await cursor.to_list(length=limit)
    return [CostCenter(**cc) for cc in cost_centers]


@router.get("/cost-centers/{cost_center_id}", response_model=CostCenter)
async def get_cost_center(cost_center_id: str, org_id: str = Depends(require_organization_access)):
    """Get cost center by ID."""
    db = MongoDB.get_database()
    cost_center = await db.cost_centers.find_one({"id": cost_center_id, "organization_id": org_id})
    if not cost_center:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cost center not found")
    return CostCenter(**cost_center)


@router.patch("/cost-centers/{cost_center_id}", response_model=CostCenter)
async def update_cost_center(
    cost_center_id: str,
    update_data: dict,
    scope: OrganizationScoped = Depends(),
):
    """Update cost center."""
    db = MongoDB.get_database()

    # Remove fields that shouldn't be updated
    update_data.pop("id", None)
    update_data.pop("organization_id", None)
    update_data.pop("created_at", None)
    update_data["updated_by"] = scope.user.get("id") or scope.user.get("sub")

    # Check for duplicate code if updating code
    if "code" in update_data:
        existing = await db.cost_centers.find_one({
            "code": update_data["code"],
            "organization_id": scope.org_id,
            "id": {"$ne": cost_center_id},
            "is_active": True
        })
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cost center with code '{update_data['code']}' already exists"
            )

    result = await db.cost_centers.update_one(
        {"id": cost_center_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cost center not found")

    cost_center = await db.cost_centers.find_one({"id": cost_center_id})
    return CostCenter(**cost_center)


@router.delete("/cost-centers/{cost_center_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cost_center(
    cost_center_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Soft delete cost center."""
    db = MongoDB.get_database()

    result = await db.cost_centers.update_one(
        {"id": cost_center_id, "organization_id": org_id},
        {"$set": {"is_active": False}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cost center not found")

    return None
