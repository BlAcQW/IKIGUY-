"""Employee Onboarding Routes."""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime, date, timedelta

from app.core.database import MongoDB
from app.models.onboarding import (
    EmployeeOnboarding,
    EmployeeOnboardingCreate,
    OnboardingTemplate,
    OnboardingTemplateCreate,
    OnboardingStatus,
    TaskStatus,
    OnboardingTaskUpdate,
    OnboardingUpdate,
)
from apps.shared.dependencies import require_organization_access, OrganizationScoped

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# ONBOARDING TEMPLATES
# ============================================================================

@router.post("/templates", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_onboarding_template(
    template_create: OnboardingTemplateCreate,
    scope: OrganizationScoped = Depends()
):
    """
    Create a new onboarding template.

    Templates define department-specific onboarding workflows.
    """
    db = MongoDB.get_database()

    template_data = OnboardingTemplate(
        **template_create.model_dump(),
        organization_id=scope.org_id,
        created_by=scope.user.get("id") or scope.user.get("sub")
    )

    template_dict = template_data.model_dump()
    for key, value in template_dict.items():
        if isinstance(value, date) and not isinstance(value, datetime):
            template_dict[key] = datetime.combine(value, datetime.min.time())

    await db.onboarding_templates.insert_one(template_dict)
    logger.info(f"Onboarding template created for {template_data.department} in org {scope.org_id}")

    return template_dict


@router.get("/templates", response_model=List[Dict[str, Any]])
async def list_onboarding_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department: Optional[str] = Query(None, description="Filter by department"),
    scope: OrganizationScoped = Depends()
):
    """List all onboarding templates for the organization."""
    db = MongoDB.get_database()

    query = {"organization_id": scope.org_id, "is_active": True}
    if department:
        query["department"] = department

    cursor = db.onboarding_templates.find(query).skip(skip).limit(limit).sort("created_at", -1)
    templates = await cursor.to_list(length=limit)

    return templates


@router.get("/templates/{template_id}", response_model=Dict[str, Any])
async def get_onboarding_template(template_id: str, scope: OrganizationScoped = Depends()):
    """Get a specific onboarding template."""
    db = MongoDB.get_database()

    template = await db.onboarding_templates.find_one({
        "id": template_id,
        "organization_id": scope.org_id
    })

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template


@router.patch("/templates/{template_id}", response_model=Dict[str, Any])
async def update_onboarding_template(
    template_id: str,
    template_update: Dict[str, Any],
    scope: OrganizationScoped = Depends()
):
    """Update an onboarding template."""
    db = MongoDB.get_database()

    # Remove fields that shouldn't be updated
    template_update.pop("id", None)
    template_update.pop("organization_id", None)
    template_update.pop("created_at", None)
    template_update.pop("created_by", None)

    template_update["updated_at"] = datetime.utcnow()
    template_update["updated_by"] = scope.user.get("id") or scope.user.get("sub")

    result = await db.onboarding_templates.update_one(
        {"id": template_id, "organization_id": scope.org_id},
        {"$set": template_update}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")

    updated_template = await db.onboarding_templates.find_one({
        "id": template_id,
        "organization_id": scope.org_id
    })

    return updated_template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_onboarding_template(template_id: str, scope: OrganizationScoped = Depends()):
    """Delete an onboarding template (soft delete)."""
    db = MongoDB.get_database()

    result = await db.onboarding_templates.update_one(
        {"id": template_id, "organization_id": scope.org_id},
        {
            "$set": {
                "is_active": False,
                "updated_at": datetime.utcnow(),
                "updated_by": scope.user.get("id") or scope.user.get("sub")
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")


# ============================================================================
# EMPLOYEE ONBOARDING
# ============================================================================

@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_employee_onboarding(
    onboarding_create: EmployeeOnboardingCreate,
    scope: OrganizationScoped = Depends()
):
    """
    Create a new employee onboarding record.

    Can optionally auto-populate tasks from a template.
    """
    db = MongoDB.get_database()

    # If no tasks provided, try to load from template
    if not onboarding_create.tasks and onboarding_create.department:
        template = await db.onboarding_templates.find_one({
            "organization_id": scope.org_id,
            "department": onboarding_create.department,
            "is_active": True
        })

        if template:
            # Copy tasks from template and calculate due dates
            start_date = onboarding_create.start_date
            tasks = []
            for task in template.get("tasks", []):
                task_dict = dict(task)
                # Calculate due date based on order (each task gets 1-2 days after start)
                days_offset = task.get("order", 0) * 2  # 2 days per task
                task_dict["due_date"] = start_date + timedelta(days=days_offset)
                tasks.append(task_dict)

            onboarding_create.tasks = tasks

            # Also copy other template defaults
            if not onboarding_create.equipment_list:
                onboarding_create.equipment_list = template.get("standard_equipment", [])
            if not onboarding_create.access_systems:
                onboarding_create.access_systems = template.get("required_systems", [])
            if not onboarding_create.training_sessions:
                onboarding_create.training_sessions = template.get("required_training", [])

            # Set expected completion date
            if not onboarding_create.expected_completion_date:
                estimated_days = template.get("estimated_days", 30)
                onboarding_create.expected_completion_date = start_date + timedelta(days=estimated_days)

    # Calculate progress
    total_tasks = len(onboarding_create.tasks)
    completed_tasks = sum(1 for task in onboarding_create.tasks if task.status == TaskStatus.COMPLETED)
    progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    onboarding_data = EmployeeOnboarding(
        **onboarding_create.model_dump(),
        organization_id=scope.org_id,
        created_by=scope.user.get("id") or scope.user.get("sub"),
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        progress_percentage=progress_percentage
    )

    onboarding_dict = onboarding_data.model_dump()
    for key, value in onboarding_dict.items():
        if isinstance(value, date) and not isinstance(value, datetime):
            onboarding_dict[key] = datetime.combine(value, datetime.min.time())

    await db.employee_onboarding.insert_one(onboarding_dict)
    logger.info(f"Onboarding created for employee {onboarding_data.employee_id} in org {scope.org_id}")

    return onboarding_dict


@router.get("/", response_model=List[Dict[str, Any]])
async def list_employee_onboardings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[OnboardingStatus] = Query(None, description="Filter by status"),
    department: Optional[str] = Query(None, description="Filter by department"),
    scope: OrganizationScoped = Depends()
):
    """List all employee onboarding records for the organization."""
    db = MongoDB.get_database()

    query = {"organization_id": scope.org_id}
    if status:
        query["onboarding_status"] = status
    if department:
        query["department"] = department

    cursor = db.employee_onboarding.find(query).skip(skip).limit(limit).sort("start_date", -1)
    onboardings = await cursor.to_list(length=limit)

    return onboardings


@router.get("/{onboarding_id}", response_model=Dict[str, Any])
async def get_employee_onboarding(onboarding_id: str, scope: OrganizationScoped = Depends()):
    """Get a specific employee onboarding record."""
    db = MongoDB.get_database()

    onboarding = await db.employee_onboarding.find_one({
        "id": onboarding_id,
        "organization_id": scope.org_id
    })

    if not onboarding:
        raise HTTPException(status_code=404, detail="Onboarding record not found")

    return onboarding


@router.get("/employee/{employee_id}", response_model=Dict[str, Any])
async def get_onboarding_by_employee(employee_id: str, scope: OrganizationScoped = Depends()):
    """Get onboarding record for a specific employee."""
    db = MongoDB.get_database()

    onboarding = await db.employee_onboarding.find_one({
        "employee_id": employee_id,
        "organization_id": scope.org_id
    })

    if not onboarding:
        raise HTTPException(status_code=404, detail="Onboarding record not found for this employee")

    return onboarding


@router.patch("/{onboarding_id}", response_model=Dict[str, Any])
async def update_employee_onboarding(
    onboarding_id: str,
    onboarding_update: OnboardingUpdate,
    scope: OrganizationScoped = Depends()
):
    """Update an employee onboarding record."""
    db = MongoDB.get_database()

    update_data = onboarding_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_data["updated_at"] = datetime.utcnow()
    update_data["updated_by"] = scope.user.get("id") or scope.user.get("sub")

    # If status is being set to completed, set completion date
    if update_data.get("onboarding_status") == OnboardingStatus.COMPLETED:
        update_data["actual_completion_date"] = datetime.utcnow()

    result = await db.employee_onboarding.update_one(
        {"id": onboarding_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Onboarding record not found")

    updated_onboarding = await db.employee_onboarding.find_one({
        "id": onboarding_id,
        "organization_id": scope.org_id
    })

    return updated_onboarding


@router.patch("/{onboarding_id}/tasks/{task_id}", response_model=Dict[str, Any])
async def update_onboarding_task(
    onboarding_id: str,
    task_id: str,
    task_update: OnboardingTaskUpdate,
    scope: OrganizationScoped = Depends()
):
    """
    Update a specific task within an onboarding record.

    Automatically recalculates progress percentage.
    """
    db = MongoDB.get_database()

    # Get current onboarding record
    onboarding = await db.employee_onboarding.find_one({
        "id": onboarding_id,
        "organization_id": scope.org_id
    })

    if not onboarding:
        raise HTTPException(status_code=404, detail="Onboarding record not found")

    # Find and update the specific task
    tasks = onboarding.get("tasks", [])
    task_found = False
    for task in tasks:
        if task.get("task_id") == task_id:
            task_found = True
            update_dict = task_update.model_dump(exclude_unset=True)

            # If marking as completed, set completion details
            if update_dict.get("status") == TaskStatus.COMPLETED:
                update_dict["completed_date"] = datetime.utcnow()
                update_dict["completed_by"] = scope.user.get("id") or scope.user.get("sub")

            task.update(update_dict)
            break

    if not task_found:
        raise HTTPException(status_code=404, detail="Task not found in onboarding record")

    # Recalculate progress
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task.get("status") == TaskStatus.COMPLETED)
    progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Determine overall status
    onboarding_status = onboarding.get("onboarding_status", OnboardingStatus.NOT_STARTED)
    if progress_percentage == 100:
        onboarding_status = OnboardingStatus.COMPLETED
    elif progress_percentage > 0:
        onboarding_status = OnboardingStatus.IN_PROGRESS

    # Update the onboarding record
    result = await db.employee_onboarding.update_one(
        {"id": onboarding_id, "organization_id": scope.org_id},
        {
            "$set": {
                "tasks": tasks,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "progress_percentage": progress_percentage,
                "onboarding_status": onboarding_status,
                "updated_at": datetime.utcnow(),
                "updated_by": scope.user.get("id") or scope.user.get("sub")
            }
        }
    )

    updated_onboarding = await db.employee_onboarding.find_one({
        "id": onboarding_id,
        "organization_id": scope.org_id
    })

    return updated_onboarding


@router.delete("/{onboarding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee_onboarding(onboarding_id: str, scope: OrganizationScoped = Depends()):
    """Delete an employee onboarding record."""
    db = MongoDB.get_database()

    result = await db.employee_onboarding.delete_one({
        "id": onboarding_id,
        "organization_id": scope.org_id
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Onboarding record not found")


# ============================================================================
# HELPER ENDPOINTS
# ============================================================================

@router.get("/stats/overview", response_model=Dict[str, Any])
async def get_onboarding_stats(scope: OrganizationScoped = Depends()):
    """Get onboarding statistics for the organization."""
    db = MongoDB.get_database()

    total = await db.employee_onboarding.count_documents({"organization_id": scope.org_id})
    not_started = await db.employee_onboarding.count_documents({
        "organization_id": scope.org_id,
        "onboarding_status": OnboardingStatus.NOT_STARTED
    })
    in_progress = await db.employee_onboarding.count_documents({
        "organization_id": scope.org_id,
        "onboarding_status": OnboardingStatus.IN_PROGRESS
    })
    completed = await db.employee_onboarding.count_documents({
        "organization_id": scope.org_id,
        "onboarding_status": OnboardingStatus.COMPLETED
    })
    on_hold = await db.employee_onboarding.count_documents({
        "organization_id": scope.org_id,
        "onboarding_status": OnboardingStatus.ON_HOLD
    })

    # Get upcoming onboardings (starting in next 30 days)
    today = datetime.utcnow()
    thirty_days = today + timedelta(days=30)
    upcoming = await db.employee_onboarding.count_documents({
        "organization_id": scope.org_id,
        "start_date": {"$gte": today, "$lte": thirty_days},
        "onboarding_status": {"$ne": OnboardingStatus.COMPLETED}
    })

    return {
        "total": total,
        "not_started": not_started,
        "in_progress": in_progress,
        "completed": completed,
        "on_hold": on_hold,
        "upcoming": upcoming,
    }


@router.post("/init-default-templates", response_model=Dict[str, Any])
async def initialize_default_templates(scope: OrganizationScoped = Depends()):
    """
    Initialize default onboarding templates for common departments.

    Creates templates for: Development, Sales & Marketing, Finance, HR, Operations.
    """
    db = MongoDB.get_database()

    # Define default templates with role-based requirements
    default_templates = [
        {
            "template_name": "Development Team Onboarding",
            "department": "Development",
            "description": "Standard onboarding for software developers and engineers",
            "estimated_days": 30,
            "tasks": [
                # CRITICAL LEGAL & COMPLIANCE (All employees)
                {"task_id": "all_1", "title": "Sign NDA electronically", "description": "Review and electronically sign Non-Disclosure Agreement", "category": "legal", "status": "pending", "order": 1},
                {"task_id": "all_2", "title": "Sign employment contract", "description": "Review and sign employment contract", "category": "legal", "status": "pending", "order": 2},
                {"task_id": "all_3", "title": "Review AI Labs Overview", "description": "Read and acknowledge understanding of AI Labs Africa mission, values, and operations", "category": "training", "status": "pending", "order": 3},
                {"task_id": "all_4", "title": "Complete employee paperwork", "description": "Fill out tax forms, benefits enrollment, emergency contacts", "category": "documents", "status": "pending", "order": 4},

                # ACCOUNT CREATION (All + Dev-specific)
                {"task_id": "all_5", "title": "Email account created", "description": "Email account created (@ailabsafrica.com)", "category": "it_setup", "status": "pending", "order": 5},
                {"task_id": "all_6", "title": "Slack account created", "description": "Join company Slack workspace", "category": "it_setup", "status": "pending", "order": 6},
                {"task_id": "dev_1", "title": "Jira account created", "description": "Create Jira account for task tracking and project management", "category": "it_setup", "status": "pending", "order": 7},
                {"task_id": "dev_2", "title": "GitHub account setup", "description": "Create GitHub account and get added to organization", "category": "it_setup", "status": "pending", "order": 8},

                # DEV-SPECIFIC ONBOARDING
                {"task_id": "dev_3", "title": "Review Developer Onboarding Guide", "description": "Read /opt/kasaai/DEV_INTERN_ONBOARDING_GUIDE.md - Complete guide to KasaAI architecture and development", "category": "training", "status": "pending", "order": 9},
                {"task_id": "dev_4", "title": "Setup development workstation", "description": "Receive laptop, monitor, keyboard, mouse, headset", "category": "it_setup", "status": "pending", "order": 10},
                {"task_id": "dev_5", "title": "Install development tools", "description": "IDE, Docker, Git, database clients, Python, Node.js", "category": "it_setup", "status": "pending", "order": 11},
                {"task_id": "dev_6", "title": "Code repository access", "description": "Clone repositories, setup SSH keys, configure Git", "category": "it_setup", "status": "pending", "order": 12},
                {"task_id": "dev_7", "title": "Review architecture documentation", "description": "Study system architecture, shared library structure (@shared/), and microservices", "category": "training", "status": "pending", "order": 13},
                {"task_id": "dev_8", "title": "Coding standards training", "description": "Learn team coding standards, PEP8, type hints, and best practices", "category": "training", "status": "pending", "order": 14},
                {"task_id": "dev_9", "title": "First code review", "description": "Submit first pull request for review", "category": "milestone", "status": "pending", "order": 15},
                {"task_id": "dev_10", "title": "Deploy first feature", "description": "Successfully deploy a feature to staging environment", "category": "milestone", "status": "pending", "order": 16},
            ],
            "welcome_kit_items": ["Company handbook", "Team directory", "Welcome letter", "Dev stickers"],
            "standard_equipment": ["Laptop", "Monitor", "Keyboard", "Mouse", "Headset"],
            "required_systems": ["Email", "Slack", "Jira", "GitHub", "AWS"],
            "required_training": [
                {"name": "NDA Signing", "duration": "15 minutes"},
                {"name": "Contract Signing", "duration": "30 minutes"},
                {"name": "AI Labs Overview", "duration": "1 hour"},
                {"name": "Security Training", "duration": "2 hours"},
                {"name": "Development Workflow", "duration": "4 hours"},
                {"name": "Code Review Process", "duration": "1 hour"},
                {"name": "Architecture Deep Dive", "duration": "3 hours"},
            ]
        },
        {
            "template_name": "Sales & Marketing Onboarding",
            "department": "Sales & Marketing",
            "description": "Standard onboarding for sales and marketing team members",
            "estimated_days": 21,
            "tasks": [
                # CRITICAL LEGAL & COMPLIANCE (All employees)
                {"task_id": "all_1", "title": "Sign NDA electronically", "description": "Review and electronically sign Non-Disclosure Agreement", "category": "legal", "status": "pending", "order": 1},
                {"task_id": "all_2", "title": "Sign employment contract", "description": "Review and sign employment contract", "category": "legal", "status": "pending", "order": 2},
                {"task_id": "all_3", "title": "Review AI Labs Overview", "description": "Read and acknowledge understanding of AI Labs Africa mission, values, and operations", "category": "training", "status": "pending", "order": 3},
                {"task_id": "all_4", "title": "Complete employee paperwork", "description": "Fill out tax forms, benefits enrollment, emergency contacts", "category": "documents", "status": "pending", "order": 4},

                # ACCOUNT CREATION (All + Sales-specific)
                {"task_id": "all_5", "title": "Email account created", "description": "Email account created (@ailabsafrica.com)", "category": "it_setup", "status": "pending", "order": 5},
                {"task_id": "all_6", "title": "Slack account created", "description": "Join company Slack workspace", "category": "it_setup", "status": "pending", "order": 6},
                {"task_id": "sales_1", "title": "CRM account setup", "description": "Create CRM account (Salesforce/HubSpot) for sales tracking", "category": "it_setup", "status": "pending", "order": 7},

                # SALES-SPECIFIC ONBOARDING
                {"task_id": "sales_2", "title": "Setup workstation", "description": "Receive laptop, phone, and headset", "category": "it_setup", "status": "pending", "order": 8},
                {"task_id": "sales_3", "title": "CRM system overview and training", "description": "Learn to use CRM system for lead tracking and sales pipeline management", "category": "training", "status": "pending", "order": 9},
                {"task_id": "sales_4", "title": "Product knowledge training", "description": "Learn about AI Labs products, services, and value propositions", "category": "training", "status": "pending", "order": 10},
                {"task_id": "sales_5", "title": "Sales process training", "description": "Understand sales funnel, qualification process, and closing techniques", "category": "training", "status": "pending", "order": 11},
                {"task_id": "sales_6", "title": "Review pricing and packages", "description": "Learn pricing structure, package options, and discount policies", "category": "training", "status": "pending", "order": 12},
                {"task_id": "sales_7", "title": "Shadow senior sales team member", "description": "Observe sales calls, demos, and client meetings", "category": "training", "status": "pending", "order": 13},
                {"task_id": "sales_8", "title": "First client demo/interaction", "description": "Conduct first sales call or product demo (with supervision)", "category": "milestone", "status": "pending", "order": 14},
            ],
            "welcome_kit_items": ["Company handbook", "Product catalog", "Sales playbook", "Business cards"],
            "standard_equipment": ["Laptop", "Phone", "Headset", "Mobile hotspot"],
            "required_systems": ["Email", "Slack", "CRM", "Calendar", "LinkedIn Sales Navigator"],
            "required_training": [
                {"name": "NDA Signing", "duration": "15 minutes"},
                {"name": "Contract Signing", "duration": "30 minutes"},
                {"name": "AI Labs Overview", "duration": "1 hour"},
                {"name": "Product Training", "duration": "8 hours"},
                {"name": "Sales Methodology", "duration": "4 hours"},
                {"name": "CRM Usage", "duration": "2 hours"},
                {"name": "Pricing and Packages", "duration": "2 hours"},
            ]
        },
        {
            "template_name": "Finance Team Onboarding",
            "department": "Finance",
            "description": "Standard onboarding for finance and accounting team members",
            "estimated_days": 21,
            "tasks": [
                {"task_id": "fin_1", "title": "Complete employee paperwork", "description": "Fill out tax forms, benefits enrollment, emergency contacts", "category": "documents", "status": "pending", "order": 1},
                {"task_id": "fin_2", "title": "Setup workstation", "description": "Receive laptop and accessories", "category": "it_setup", "status": "pending", "order": 2},
                {"task_id": "fin_3", "title": "Accounting software training", "description": "Learn QuickBooks/NetSuite", "category": "training", "status": "pending", "order": 3},
                {"task_id": "fin_4", "title": "Financial policies review", "description": "Review company financial policies and procedures", "category": "training", "status": "pending", "order": 4},
                {"task_id": "fin_5", "title": "Chart of accounts review", "description": "Understand company chart of accounts", "category": "training", "status": "pending", "order": 5},
                {"task_id": "fin_6", "title": "Compliance training", "description": "SOX compliance and regulatory requirements", "category": "training", "status": "pending", "order": 6},
            ],
            "welcome_kit_items": ["Company handbook", "Financial policies", "Compliance guide"],
            "standard_equipment": ["Laptop", "Dual monitors", "Calculator"],
            "required_systems": ["Email", "Accounting Software", "Slack", "Banking Portal"],
            "required_training": [
                {"name": "Accounting Software", "duration": "4 hours"},
                {"name": "Financial Policies", "duration": "2 hours"},
                {"name": "Compliance", "duration": "4 hours"},
            ]
        },
        {
            "template_name": "HR Team Onboarding",
            "department": "Human Resources",
            "description": "Standard onboarding for HR team members",
            "estimated_days": 21,
            "tasks": [
                {"task_id": "hr_1", "title": "Complete employee paperwork", "description": "Fill out tax forms, benefits enrollment, emergency contacts", "category": "documents", "status": "pending", "order": 1},
                {"task_id": "hr_2", "title": "Setup workstation", "description": "Receive laptop and accessories", "category": "it_setup", "status": "pending", "order": 2},
                {"task_id": "hr_3", "title": "HRIS system training", "description": "Learn HR information system", "category": "training", "status": "pending", "order": 3},
                {"task_id": "hr_4", "title": "HR policies review", "description": "Review all HR policies and procedures", "category": "training", "status": "pending", "order": 4},
                {"task_id": "hr_5", "title": "Employment law training", "description": "Understand relevant employment laws", "category": "training", "status": "pending", "order": 5},
                {"task_id": "hr_6", "title": "Benefits administration", "description": "Learn benefits programs and administration", "category": "training", "status": "pending", "order": 6},
            ],
            "welcome_kit_items": ["Company handbook", "HR policies", "Legal compliance guide"],
            "standard_equipment": ["Laptop", "Phone", "Printer access"],
            "required_systems": ["Email", "HRIS", "Slack", "Benefits Portal"],
            "required_training": [
                {"name": "HRIS Training", "duration": "4 hours"},
                {"name": "Employment Law", "duration": "8 hours"},
                {"name": "Benefits Administration", "duration": "4 hours"},
            ]
        },
        {
            "template_name": "Operations Team Onboarding",
            "department": "Operations",
            "description": "Standard onboarding for operations team members",
            "estimated_days": 21,
            "tasks": [
                {"task_id": "ops_1", "title": "Complete employee paperwork", "description": "Fill out tax forms, benefits enrollment, emergency contacts", "category": "documents", "status": "pending", "order": 1},
                {"task_id": "ops_2", "title": "Setup workstation", "description": "Receive laptop and accessories", "category": "it_setup", "status": "pending", "order": 2},
                {"task_id": "ops_3", "title": "Process documentation review", "description": "Review operational processes and SOPs", "category": "training", "status": "pending", "order": 3},
                {"task_id": "ops_4", "title": "Systems training", "description": "Learn operational systems and tools", "category": "training", "status": "pending", "order": 4},
                {"task_id": "ops_5", "title": "Quality standards training", "description": "Understand quality control processes", "category": "training", "status": "pending", "order": 5},
                {"task_id": "ops_6", "title": "Shadow operations team", "description": "Observe daily operations", "category": "training", "status": "pending", "order": 6},
            ],
            "welcome_kit_items": ["Company handbook", "Operations manual", "Safety guidelines"],
            "standard_equipment": ["Laptop", "Safety equipment"],
            "required_systems": ["Email", "Operations Software", "Slack"],
            "required_training": [
                {"name": "Operations Overview", "duration": "4 hours"},
                {"name": "Systems Training", "duration": "8 hours"},
                {"name": "Safety Training", "duration": "2 hours"},
            ]
        }
    ]

    created_count = 0
    for template_data in default_templates:
        # Check if template already exists
        existing = await db.onboarding_templates.find_one({
            "organization_id": scope.org_id,
            "department": template_data["department"]
        })

        if not existing:
            template = OnboardingTemplate(
                **template_data,
                organization_id=scope.org_id,
                created_by=scope.user.get("id") or scope.user.get("sub")
            )

            await db.onboarding_templates.insert_one(template.model_dump())
            created_count += 1

    return {
        "message": f"Initialized {created_count} default templates",
        "created_count": created_count
    }
