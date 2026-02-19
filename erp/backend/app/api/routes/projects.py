"""Project Management Routes."""

import logging
import os
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import FileResponse

from app.core.database import MongoDB
from app.config import settings
from app.models.project import (
    Project,
    Task,
    Resource,
    Timesheet,
    ProjectCreate,
    TaskCreate,
    ResourceCreate,
    TimesheetCreate,
)
from apps.shared.dependencies import require_organization_access, OrganizationScoped
from apps.shared.services.unified_email_service import get_email_service

logger = logging.getLogger(__name__)
router = APIRouter()

# File upload configuration
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024  # Convert MB to bytes
ALLOWED_EXTENSIONS = [ext.strip() for ext in settings.ALLOWED_EXTENSIONS.split(",")]


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(project_data: ProjectCreate, scope: OrganizationScoped = Depends()):
    """Create a new project."""
    db = MongoDB.get_database()

    # Auto-generate project code if not provided
    if not project_data.project_code:
        # Generate code from project name
        name_parts = project_data.project_name.upper().split()
        if len(name_parts) == 1:
            # Single word: take first 3 characters
            base_code = name_parts[0][:3]
        else:
            # Multiple words: take first letter of each word
            base_code = "".join([part[0] for part in name_parts if part])

        # Ensure uniqueness by appending a number if needed
        code = base_code
        counter = 1
        while True:
            existing = await db.projects.find_one({
                "project_code": code,
                "organization_id": scope.org_id,
                "is_active": True
            })
            if not existing:
                break
            code = f"{base_code}{counter}"
            counter += 1

        project_data.project_code = code
    else:
        # Validate manually provided code for uniqueness
        existing = await db.projects.find_one({
            "project_code": project_data.project_code,
            "organization_id": scope.org_id,
            "is_active": True
        })
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project code '{project_data.project_code}' already exists in this organization"
            )

    # Create Project model with organization_id
    user_id = scope.user.get("id") or scope.user.get("sub")
    project = Project(
        **project_data.model_dump(),
        organization_id=scope.org_id,
        created_by=user_id,
    )

    # Convert to dict for MongoDB, handling enum serialization
    project_data_dict = project.model_dump(mode='python')
    # Convert status enum to string
    if 'status' in project_data_dict and hasattr(project_data_dict['status'], 'value'):
        project_data_dict['status'] = project_data_dict['status'].value

    # Convert date objects to datetime for MongoDB compatibility (BSON doesn't support date)
    if project_data_dict.get('start_date') and isinstance(project_data_dict['start_date'], date):
        project_data_dict['start_date'] = datetime.combine(project_data_dict['start_date'], datetime.min.time())
    if project_data_dict.get('end_date') and isinstance(project_data_dict['end_date'], date):
        project_data_dict['end_date'] = datetime.combine(project_data_dict['end_date'], datetime.min.time())
    if project_data_dict.get('actual_start_date') and isinstance(project_data_dict['actual_start_date'], date):
        project_data_dict['actual_start_date'] = datetime.combine(project_data_dict['actual_start_date'], datetime.min.time())
    if project_data_dict.get('actual_end_date') and isinstance(project_data_dict['actual_end_date'], date):
        project_data_dict['actual_end_date'] = datetime.combine(project_data_dict['actual_end_date'], datetime.min.time())

    await db.projects.insert_one(project_data_dict)

    # Send email notification
    try:
        email_service = get_email_service()
        await email_service.send_email(
            to="alfred.anyan@gmail.com",
            subject=f"New Project Created: {project.project_name}",
            body=f"""
A new project has been created in the ERP system.

Project Details:
- Project Name: {project.project_name}
- Project Code: {project.project_code}
- Status: {project.status}
- Start Date: {project.start_date}
- End Date: {project.end_date}
- Budget: {project.currency} {project.budget:,.2f}
- Project Manager ID: {project.project_manager_id}
- Organization ID: {project.organization_id}

Created by: {user_id}
Created at: {project.created_at}
            """,
            html_body=f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">New Project Created</h2>
    <p>A new project has been created in the ERP system.</p>

    <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #1f2937;">Project Details</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 8px 0; font-weight: bold; width: 200px;">Project Name:</td>
                <td style="padding: 8px 0;">{project.project_name}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; font-weight: bold;">Project Code:</td>
                <td style="padding: 8px 0;">{project.project_code}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; font-weight: bold;">Status:</td>
                <td style="padding: 8px 0;"><span style="background-color: #dbeafe; color: #1e40af; padding: 4px 12px; border-radius: 12px;">{project.status}</span></td>
            </tr>
            <tr>
                <td style="padding: 8px 0; font-weight: bold;">Start Date:</td>
                <td style="padding: 8px 0;">{project.start_date}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; font-weight: bold;">End Date:</td>
                <td style="padding: 8px 0;">{project.end_date}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; font-weight: bold;">Budget:</td>
                <td style="padding: 8px 0;">{project.currency} {project.budget:,.2f}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; font-weight: bold;">Project Manager ID:</td>
                <td style="padding: 8px 0;">{project.project_manager_id}</td>
            </tr>
        </table>
    </div>

    <p style="color: #6b7280; font-size: 14px;">
        <strong>Created by:</strong> {user_id}<br>
        <strong>Created at:</strong> {project.created_at}
    </p>
</body>
</html>
            """
        )
        logger.info(f"Email notification sent for project creation: {project.id}")
    except Exception as e:
        logger.error(f"Failed to send email notification for project {project.id}: {str(e)}")
        # Don't fail the request if email sending fails

    return project


@router.get("", response_model=List[Project])
async def list_projects(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
):
    """List all projects."""
    db = MongoDB.get_database()

    query = {"organization_id": org_id, "is_active": True}

    # Search
    if search:
        query["$or"] = [
            {"project_name": {"$regex": search, "$options": "i"}},
            {"project_code": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    # Filter
    if status_filter:
        query["status"] = status_filter

    cursor = db.projects.find(query).skip(skip).limit(limit).sort("created_at", -1)
    projects = await cursor.to_list(length=limit)
    return [Project(**p) for p in projects]


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get project by ID."""
    db = MongoDB.get_database()
    project = await db.projects.find_one({"id": project_id, "organization_id": org_id})

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return Project(**project)


@router.patch("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    update_data: dict,
    scope: OrganizationScoped = Depends(),
):
    """Update project."""
    db = MongoDB.get_database()

    update_data.pop("id", None)
    update_data.pop("organization_id", None)
    update_data.pop("created_at", None)

    result = await db.projects.update_one(
        {"id": project_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    project = await db.projects.find_one({"id": project_id})
    return Project(**project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Soft delete project."""
    db = MongoDB.get_database()

    result = await db.projects.update_one(
        {"id": project_id, "organization_id": org_id},
        {"$set": {"is_active": False}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return None


@router.post("/{project_id}/attachments", status_code=status.HTTP_201_CREATED)
async def upload_project_attachment(
    project_id: str,
    file: UploadFile = File(...),
    scope: OrganizationScoped = Depends(),
):
    """
    Upload a file attachment to a project.

    Supports documents, images, recordings, and other file types.
    """
    db = MongoDB.get_database()

    # Verify project exists and user has access
    project = await db.projects.find_one(
        {"id": project_id, "organization_id": scope.org_id}
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )

    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file contents
    contents = await file.read()

    # Check file size
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    # Create directory structure: uploads/{org_id}/projects/{project_id}/
    project_dir = UPLOAD_DIR / scope.org_id / "projects" / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    attachment_id = str(uuid.uuid4())
    unique_filename = f"{attachment_id}{file_ext}"
    file_path = project_dir / unique_filename

    # Save file to disk
    try:
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file"
        )

    # Create attachment metadata
    user_id = scope.user.get("id") or scope.user.get("sub")
    attachment = {
        "id": attachment_id,
        "original_filename": file.filename,
        "stored_filename": unique_filename,
        "file_path": str(file_path.relative_to(UPLOAD_DIR)),
        "file_size": len(contents),
        "file_type": file_ext,
        "mime_type": file.content_type,
        "uploaded_by": user_id,
        "uploaded_at": datetime.utcnow().isoformat(),
    }

    # Add attachment to project
    await db.projects.update_one(
        {"id": project_id, "organization_id": scope.org_id},
        {"$push": {"attachments": attachment}}
    )

    logger.info(f"File uploaded to project {project_id}: {file.filename}")

    return {
        "message": "File uploaded successfully",
        "attachment": attachment
    }


@router.delete("/{project_id}/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_attachment(
    project_id: str,
    attachment_id: str,
    scope: OrganizationScoped = Depends(),
):
    """Delete a file attachment from a project."""
    db = MongoDB.get_database()

    # Get project
    project = await db.projects.find_one(
        {"id": project_id, "organization_id": scope.org_id}
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Find attachment
    attachment = None
    for att in project.get("attachments", []):
        if att["id"] == attachment_id:
            attachment = att
            break

    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )

    # Delete file from disk
    file_path = UPLOAD_DIR / attachment["file_path"]
    try:
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        logger.error(f"Failed to delete file: {e}")

    # Remove attachment from project
    await db.projects.update_one(
        {"id": project_id, "organization_id": scope.org_id},
        {"$pull": {"attachments": {"id": attachment_id}}}
    )

    logger.info(f"Attachment {attachment_id} deleted from project {project_id}")

    return None


@router.get("/{project_id}/attachments/{attachment_id}/download")
async def download_project_attachment(
    project_id: str,
    attachment_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Download a file attachment from a project."""
    db = MongoDB.get_database()

    # Get project
    project = await db.projects.find_one(
        {"id": project_id, "organization_id": org_id}
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Find attachment
    attachment = None
    for att in project.get("attachments", []):
        if att["id"] == attachment_id:
            attachment = att
            break

    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )

    # Get file path
    file_path = UPLOAD_DIR / attachment["file_path"]

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )

    return FileResponse(
        path=file_path,
        filename=attachment["original_filename"],
        media_type=attachment.get("mime_type", "application/octet-stream")
    )


@router.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(task_data: TaskCreate, scope: OrganizationScoped = Depends()):
    """Create a new task."""
    db = MongoDB.get_database()

    # Convert TaskCreate to Task with organization_id
    user_id = scope.user.get("id") or scope.user.get("sub")
    task = Task(
        **task_data.model_dump(),
        organization_id=scope.org_id,
        created_by=user_id,
    )

    await db.tasks.insert_one(task.model_dump())
    return task


@router.get("/tasks", response_model=List[Task])
async def list_tasks(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    project_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[str] = None,
):
    """List all tasks."""
    db = MongoDB.get_database()

    query = {"organization_id": org_id, "is_active": True}

    # Search
    if search:
        query["$or"] = [
            {"task_name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    # Filters
    if project_id:
        query["project_id"] = project_id
    if status_filter:
        query["status"] = status_filter
    if priority:
        query["priority"] = priority
    if assigned_to:
        query["assigned_to"] = assigned_to

    cursor = db.tasks.find(query).skip(skip).limit(limit).sort("created_at", -1)
    tasks = await cursor.to_list(length=limit)
    return [Task(**t) for t in tasks]


@router.get("/tasks/{task_id}", response_model=Task)
async def get_task(
    task_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get task by ID."""
    db = MongoDB.get_database()
    task = await db.tasks.find_one({"id": task_id, "organization_id": org_id})

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    return Task(**task)


@router.patch("/tasks/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    update_data: dict,
    scope: OrganizationScoped = Depends(),
):
    """Update task."""
    db = MongoDB.get_database()

    update_data.pop("id", None)
    update_data.pop("organization_id", None)
    update_data.pop("created_at", None)

    result = await db.tasks.update_one(
        {"id": task_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    task = await db.tasks.find_one({"id": task_id})
    return Task(**task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Soft delete task."""
    db = MongoDB.get_database()

    result = await db.tasks.update_one(
        {"id": task_id, "organization_id": org_id},
        {"$set": {"is_active": False}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    return None


@router.post("/resources", response_model=Resource, status_code=status.HTTP_201_CREATED)
async def create_resource(resource_data: ResourceCreate, scope: OrganizationScoped = Depends()):
    """Allocate a resource to a project."""
    db = MongoDB.get_database()

    # Convert ResourceCreate to Resource with organization_id
    user_id = scope.user.get("id") or scope.user.get("sub")
    resource = Resource(
        **resource_data.model_dump(),
        organization_id=scope.org_id,
        created_by=user_id,
    )

    await db.resources.insert_one(resource.model_dump())
    return resource


@router.get("/resources", response_model=List[Resource])
async def list_resources(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    project_id: Optional[str] = None,
    employee_id: Optional[str] = None,
):
    """List all resource allocations."""
    db = MongoDB.get_database()
    query = {"organization_id": org_id}

    # Filters
    if project_id:
        query["project_id"] = project_id
    if employee_id:
        query["employee_id"] = employee_id

    cursor = db.resources.find(query).skip(skip).limit(limit).sort("created_at", -1)
    resources = await cursor.to_list(length=limit)
    return [Resource(**r) for r in resources]


@router.get("/resources/{resource_id}", response_model=Resource)
async def get_resource(
    resource_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get resource allocation by ID."""
    db = MongoDB.get_database()
    resource = await db.resources.find_one({"id": resource_id, "organization_id": org_id})

    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    return Resource(**resource)


@router.patch("/resources/{resource_id}", response_model=Resource)
async def update_resource(
    resource_id: str,
    update_data: dict,
    scope: OrganizationScoped = Depends(),
):
    """Update resource allocation."""
    db = MongoDB.get_database()

    update_data.pop("id", None)
    update_data.pop("organization_id", None)
    update_data.pop("created_at", None)

    result = await db.resources.update_one(
        {"id": resource_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    resource = await db.resources.find_one({"id": resource_id})
    return Resource(**resource)


@router.delete("/resources/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Delete resource allocation."""
    db = MongoDB.get_database()

    result = await db.resources.delete_one(
        {"id": resource_id, "organization_id": org_id}
    )

    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    return None


@router.post("/timesheets", response_model=Timesheet, status_code=status.HTTP_201_CREATED)
async def create_timesheet(timesheet_data: TimesheetCreate, scope: OrganizationScoped = Depends()):
    """Log time to a project/task."""
    db = MongoDB.get_database()

    # Convert TimesheetCreate to Timesheet with organization_id
    user_id = scope.user.get("id") or scope.user.get("sub")
    timesheet = Timesheet(
        **timesheet_data.model_dump(),
        organization_id=scope.org_id,
        created_by=user_id,
    )

    await db.timesheets.insert_one(timesheet.model_dump())
    return timesheet


@router.get("/timesheets", response_model=List[Timesheet])
async def list_timesheets(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
    employee_id: Optional[str] = None,
):
    """List all timesheet entries."""
    db = MongoDB.get_database()
    query = {"organization_id": org_id}

    # Filters
    if project_id:
        query["project_id"] = project_id
    if task_id:
        query["task_id"] = task_id
    if employee_id:
        query["employee_id"] = employee_id

    cursor = db.timesheets.find(query).skip(skip).limit(limit).sort("date", -1)
    timesheets = await cursor.to_list(length=limit)
    return [Timesheet(**t) for t in timesheets]


@router.get("/timesheets/{timesheet_id}", response_model=Timesheet)
async def get_timesheet(
    timesheet_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get timesheet entry by ID."""
    db = MongoDB.get_database()
    timesheet = await db.timesheets.find_one({"id": timesheet_id, "organization_id": org_id})

    if not timesheet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Timesheet not found")

    return Timesheet(**timesheet)


@router.patch("/timesheets/{timesheet_id}", response_model=Timesheet)
async def update_timesheet(
    timesheet_id: str,
    update_data: dict,
    scope: OrganizationScoped = Depends(),
):
    """Update timesheet entry."""
    db = MongoDB.get_database()

    update_data.pop("id", None)
    update_data.pop("organization_id", None)
    update_data.pop("created_at", None)

    result = await db.timesheets.update_one(
        {"id": timesheet_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Timesheet not found")

    timesheet = await db.timesheets.find_one({"id": timesheet_id})
    return Timesheet(**timesheet)


@router.delete("/timesheets/{timesheet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timesheet(
    timesheet_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Delete timesheet entry."""
    db = MongoDB.get_database()

    result = await db.timesheets.delete_one(
        {"id": timesheet_id, "organization_id": org_id}
    )

    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Timesheet not found")

    return None
