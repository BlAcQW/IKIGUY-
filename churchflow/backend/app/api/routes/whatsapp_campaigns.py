"""
WhatsApp Campaign Routes for ChurchFlow

Provides WhatsApp campaign functionality for church communications using
the centralized WhatsApp campaign router from core_backend.
"""

import sys
import os

# Add paths for imports
sys.path.insert(0, "/opt/kasaai/apps")

# Import the centralized WhatsApp campaigns router from core_backend
from core_backend.backend.routes.whatsapp_campaigns import router

# Re-export the router for ChurchFlow
# This allows ChurchFlow to use the centralized WhatsApp campaigns functionality
# while maintaining the same architectural pattern as other routes

__all__ = ["router"]
