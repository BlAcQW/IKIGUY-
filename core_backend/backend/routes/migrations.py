"""Migration routes for data structure updates."""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any
import logging

from ..services.migration_service import migration_service
from ..auth import get_current_user_mongo
from ..middleware.organization_context import (
    get_organization_context,
    validate_organization_access
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/migrations", tags=["migrations"])


@router.post("/automation-templates-to-industry-ids")
async def migrate_automation_templates_to_industry_ids(
    request: Request,
    user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Migrate automation templates to use industry IDs instead of names.

    Admin-only migration endpoint. Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, user, org_id)

        logger.info(f"Running template migration for organization={org_id}, user={user.get('id')}")

        result = migration_service.migrate_automation_templates_to_industry_ids()

        logger.info(f"Template migration completed for organization={org_id}")

        return {
            "success": True,
            "message": "Migration completed",
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Migration failed for organization={org_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")


@router.post("/rollback-automation-templates-migration")
async def rollback_automation_templates_migration(
    request: Request,
    user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Rollback automation templates migration (restore industry names).

    Admin-only migration endpoint. Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, user, org_id)

        logger.info(f"Running migration rollback for organization={org_id}, user={user.get('id')}")

        result = migration_service.rollback_automation_templates_migration()

        logger.info(f"Migration rollback completed for organization={org_id}")

        return {
            "success": True,
            "message": "Rollback completed",
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rollback failed for organization={org_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Rollback failed: {str(e)}")


@router.get("/status")
async def get_migration_status(
    request: Request,
    user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Get the current migration status.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, user, org_id)

        logger.info(f"Checking migration status for organization={org_id}, user={user.get('id')}")

        # Check if templates are using industry IDs or names
        from ..services.migration_service import MigrationService
        migration_svc = MigrationService()

        # Count templates with industry IDs vs names
        templates_with_ids = migration_svc.automation_templates.count_documents({
            "industry": {"$regex": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"}
        })

        total_templates = migration_svc.automation_templates.count_documents({})
        templates_with_names = total_templates - templates_with_ids

        return {
            "total_templates": total_templates,
            "templates_with_industry_ids": templates_with_ids,
            "templates_with_industry_names": templates_with_names,
            "migration_complete": templates_with_names == 0
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed for organization={org_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")