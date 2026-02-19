"""API Routes Package."""

from fastapi import APIRouter
from .routes import (
    crm_router,
    crm_activities_router,
    crm_tasks_router,
    hr_router,
    finance_router,
    financial_reports_router,
    project_router,
    bi_router,
    system_router,
    organization_router,
    onboarding_router,
    legal_router,
    partnerships_router,
    feedback_router,
    export_router,
)

api_router = APIRouter()

# Include all module routers
api_router.include_router(organization_router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(crm_router, prefix="/crm", tags=["CRM"])
api_router.include_router(crm_activities_router, prefix="/crm", tags=["CRM Activities"])
api_router.include_router(crm_tasks_router, prefix="/crm", tags=["CRM Tasks"])
api_router.include_router(hr_router, prefix="/hr", tags=["HR"])
api_router.include_router(finance_router, prefix="/finance", tags=["Finance"])
api_router.include_router(financial_reports_router, prefix="/finance", tags=["Financial Reports"])
api_router.include_router(project_router, prefix="/projects", tags=["Projects"])
api_router.include_router(bi_router, prefix="/bi", tags=["Business Intelligence"])
api_router.include_router(system_router, prefix="/system", tags=["System"])
api_router.include_router(onboarding_router, prefix="/onboarding", tags=["Onboarding"])
api_router.include_router(legal_router, prefix="/legal", tags=["Legal Documents"])
api_router.include_router(partnerships_router, prefix="/partnerships", tags=["Partnerships"])
api_router.include_router(feedback_router, tags=["Feedback"])
api_router.include_router(export_router, prefix="/export", tags=["Export"])

__all__ = ["api_router"]
