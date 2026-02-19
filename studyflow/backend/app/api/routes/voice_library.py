"""
Voice Library API endpoints for StudyFlow.

Uses shared voice library routes from @shared/routes/voice_library_routes.py
"""

import sys
import os

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))

from apps.shared.routes.voice_library_routes import create_voice_library_router
from app.core.auth import get_current_user, require_admin
from app.core.database import mongodb

# Create router using shared voice library routes
router = create_voice_library_router(
    get_current_user_func=get_current_user,
    get_database_func=mongodb.get_database,
    require_admin_func=require_admin
)
