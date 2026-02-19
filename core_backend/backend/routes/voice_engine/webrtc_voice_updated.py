#!/usr/bin/env python3
"""
WebRTC Voice Chat Handler - UPDATED to use @shared/integration/webrtc

This is a simplified wrapper that uses the shared WebRTC module.
All apps can now use the same WebRTC implementation!
"""

import logging
import os
from fastapi import FastAPI

# Import from shared integration module
from apps.shared.integration.webrtc import setup_webrtc, FASTRTC_AVAILABLE

logger = logging.getLogger(__name__)


def setup_webrtc_routes(
    app: FastAPI,
    assistant_id: str = None,
    mount_path: str = "/voice/webrtc"
):
    """
    Setup WebRTC voice routes on FastAPI app using shared integration.

    This is now a thin wrapper around the shared WebRTC integration,
    making it easy for all KasaAI apps to add voice functionality.

    Args:
        app: FastAPI application instance
        assistant_id: Optional assistant ID (defaults to env var)
        mount_path: URL path to mount WebRTC endpoints (default "/voice/webrtc")

    Returns:
        True if setup successful, False otherwise

    Example:
        ```python
        from fastapi import FastAPI
        from backend.routes.voice_engine.webrtc_voice import setup_webrtc_routes

        app = FastAPI()
        setup_webrtc_routes(app, assistant_id="my-assistant")
        ```
    """
    if not FASTRTC_AVAILABLE:
        logger.error("❌ FastRTC not available - WebRTC routes not configured")
        logger.error("💡 Install with: pip install 'fastrtc[vad,tts]'")
        return False

    logger.info("🚀 Setting up WebRTC voice routes using shared integration...")

    # Get assistant ID from parameter or environment
    if not assistant_id:
        assistant_id = os.environ.get("DEFAULT_ASSISTANT_ID", "default-assistant")
        logger.warning(f"⚠️ No assistant_id provided, using: {assistant_id}")

    # Use the shared integration setup
    success = setup_webrtc(
        app=app,
        assistant_id=assistant_id,
        mount_path=mount_path,
        pause_threshold_ms=1500,
        ui_title="KasaAI Voice Assistant",
        ui_subtitle="Speak naturally - I'll respond when you pause"
    )

    if success:
        logger.info("✅ WebRTC routes configured successfully")
        logger.info(f"📝 Test at: {mount_path}/")
    else:
        logger.error("❌ Failed to configure WebRTC routes")

    return success


# Export for backwards compatibility
__all__ = [
    'setup_webrtc_routes',
    'FASTRTC_AVAILABLE'
]
