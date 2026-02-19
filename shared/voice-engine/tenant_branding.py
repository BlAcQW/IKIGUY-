"""Utilities for tenant-specific branding.

This module provides a simple in-memory mapping of tenant identifiers to
branding tokens such as logo URLs and primary colors. It is a lightweight
placeholder for Demo 22 to show how the voice engine can theme itself per
tenant.
"""
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Branding:
    """Branding assets for a tenant."""
    logo_url: str
    primary_color: str


# Example branding configuration. In production, this would likely be loaded
# from a database or configuration service.
TENANT_BRANDS: Dict[str, Branding] = {
    "acme": Branding(
        logo_url="https://cdn.example.com/acme/logo.png",
        primary_color="#FF5733",
    ),
    "beta": Branding(
        logo_url="https://cdn.example.com/beta/logo.png",
        primary_color="#3366FF",
    ),
}


def get_branding(tenant_id: str) -> Branding:
    """Return branding for ``tenant_id`` or a default theme.

    Args:
        tenant_id: Identifier parsed from the user's JWT or session.

    Returns:
        Branding: The branding configuration for the tenant. Falls back to a
        neutral theme if the tenant is unknown.
    """
    return TENANT_BRANDS.get(
        tenant_id,
        Branding(
            logo_url="https://cdn.example.com/default/logo.png",
            primary_color="#000000",
        ),
    )
