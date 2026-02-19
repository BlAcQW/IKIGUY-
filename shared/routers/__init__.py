"""
Shared FastAPI Routers

Reusable FastAPI routers for common functionality across all KasaAI apps.

Available Routers:
- vapi_webhook_router: Vapi TTS webhook integration

Author: AI Labs Africa
Created: November 8, 2025
"""

from .vapi_webhook_router import router as vapi_webhook_router

__all__ = ["vapi_webhook_router"]
