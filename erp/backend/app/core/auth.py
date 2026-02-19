"""
Authentication configuration.
"""

import logging
from app.config import settings

logger = logging.getLogger(__name__)


def initialize_auth():
    """
    Initialize authentication.

    Validates Supabase configuration.
    """
    if not settings.SUPABASE_URL:
        logger.warning("SUPABASE_URL not configured")

    if not settings.SUPABASE_ANON_KEY:
        logger.warning("SUPABASE_ANON_KEY not configured")

    logger.info("✅ Authentication initialized (Supabase)")
