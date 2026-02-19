"""
Shared startup initialization modules.

Provides common startup logic that can be used across all KasaAI applications.
"""

from .default_organization import initialize_default_organization

__all__ = ["initialize_default_organization"]
