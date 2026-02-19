"""
Voice Library API endpoints for ChurchFlow.

Uses shared voice library routes from @shared/routes/voice_library_routes.py
"""

from apps.shared.routes.voice_library_routes import create_voice_library_router
from app.api.dependencies import get_current_user, require_admin
from app.core.database import get_database

# Create router using shared voice library routes
router = create_voice_library_router(
    get_current_user_func=get_current_user,
    get_database_func=get_database,
    require_admin_func=require_admin
)
