"""API Route Modules."""

from .crm import router as crm_router
from .crm_activities import router as crm_activities_router
from .crm_tasks import router as crm_tasks_router
from .hr import router as hr_router
from .finance import router as finance_router
from .financial_reports import router as financial_reports_router
from .projects import router as project_router
from .bi import router as bi_router
from .system import router as system_router
from .organizations import router as organization_router
from .onboarding import router as onboarding_router
from .legal import router as legal_router
from .partnerships import router as partnerships_router
from .feedback import router as feedback_router
from .export import router as export_router

__all__ = [
    "crm_router",
    "crm_activities_router",
    "crm_tasks_router",
    "hr_router",
    "finance_router",
    "financial_reports_router",
    "project_router",
    "bi_router",
    "system_router",
    "organization_router",
    "onboarding_router",
    "legal_router",
    "partnerships_router",
    "feedback_router",
    "export_router",
]
