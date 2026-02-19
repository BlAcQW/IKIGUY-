"""
Voice Library API endpoints for InkWave.

Uses shared voice library routes from @shared/routes/voice_library_routes.py
"""

import sys
import os

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))

from apps.shared.routes.voice_library_routes import create_voice_library_router
from apps.shared.dependencies.auth import get_current_user
from app.core.auth import get_current_admin_user
from app.core.database import get_db

# Create router using shared voice library routes
router = create_voice_library_router(
    get_current_user_func=get_current_user,
    get_database_func=get_db,
    require_admin_func=get_current_admin_user
)
