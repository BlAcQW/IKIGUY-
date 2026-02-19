"""Shared FastAPI dependencies for all KasaAI applications."""

from .auth import (
    get_current_user,
    get_current_user_optional,
    require_organization_access,
    require_organization_admin_role,
    get_organization_context_optional,
    OrganizationScoped,
)

__all__ = [
    "get_current_user",
    "get_current_user_optional",
    "require_organization_access",
    "require_organization_admin_role",
    "get_organization_context_optional",
    "OrganizationScoped",
]
