"""
SIP Manager initialization for core backend startup
"""

import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)


async def initialize_sip_services(app):
    """
    Initialize SIP services (Asterisk and FreeSWITCH) on application startup
    
    Args:
        app: FastAPI application instance
    """
    try:
        from apps.shared.voice_engine.backend.sip_manager import initialize_sip_manager
        
        # Load SIP configuration from environment or config file
        sip_config = {
            # Asterisk configuration
            "asterisk_enabled": os.getenv("ASTERISK_ENABLED", "true").lower() == "true",
            "asterisk_host": os.getenv("ASTERISK_HOST", "localhost"),
            "asterisk_port": int(os.getenv("ASTERISK_PORT", "5060")),
            "asterisk_ami_port": int(os.getenv("ASTERISK_AMI_PORT", "5038")),
            "asterisk_ami_username": os.getenv("ASTERISK_AMI_USERNAME", "admin"),
            "asterisk_ami_password": os.getenv("ASTERISK_AMI_PASSWORD", "kasaai2024"),
            
            # FreeSWITCH configuration
            "freeswitch_enabled": os.getenv("FREESWITCH_ENABLED", "true").lower() == "true",
            "freeswitch_host": os.getenv("FREESWITCH_HOST", "localhost"),
            "freeswitch_port": int(os.getenv("FREESWITCH_PORT", "5080")),
            "freeswitch_esl_port": int(os.getenv("FREESWITCH_ESL_PORT", "8021")),
            "freeswitch_esl_password": os.getenv("FREESWITCH_ESL_PASSWORD", "KasaaiFS2024"),
        }
        
        # Initialize SIP manager
        logger.info("Initializing SIP manager with Asterisk and FreeSWITCH support...")
        sip_manager = await initialize_sip_manager(sip_config)
        
        # Store in app state for access in routes
        app.state.sip_manager = sip_manager
        
        # Get initial status
        status = await sip_manager.get_server_status()
        
        logger.info(f"SIP services initialized: {status['available_servers']} servers available")
        
        # Log server details
        for server_id, server_info in status["servers"].items():
            if server_info["connected"]:
                logger.info(f"  ✓ {server_id}: {server_info['provider']} at {server_info['host']}:{server_info['port']}")
            else:
                logger.warning(f"  ✗ {server_id}: {server_info['provider']} at {server_info['host']}:{server_info['port']} (not connected)")
        
        return sip_manager
        
    except Exception as e:
        logger.error(f"Failed to initialize SIP services: {e}")
        logger.warning("SIP trunking features will be unavailable")
        return None


async def shutdown_sip_services(app):
    """
    Shutdown SIP services on application shutdown
    
    Args:
        app: FastAPI application instance
    """
    try:
        if hasattr(app.state, "sip_manager") and app.state.sip_manager:
            logger.info("Shutting down SIP services...")
            await app.state.sip_manager.shutdown()
            logger.info("SIP services shutdown complete")
    except Exception as e:
        logger.error(f"Error during SIP services shutdown: {e}")