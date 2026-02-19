"""
VAPI Assistant Update Helper

Helper endpoint to update VAPI assistant configuration when custom_settings_override
is changed in automation configs.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
import httpx

from ..auth import get_current_user_mongo
from ..mongo import get_collection
from ..services.vapi_assistant_builder import build_vapi_assistant_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vapi/assistant-update", tags=["VAPI Assistant Update"])

VAPI_API_BASE = "https://api.vapi.ai"
VAPI_API_KEY = None


def get_vapi_headers() -> Dict[str, str]:
    """Get headers for VAPI API requests."""
    import os
    global VAPI_API_KEY
    if not VAPI_API_KEY:
        VAPI_API_KEY = os.getenv("VAPI_API_KEY")
    
    if not VAPI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="VAPI_API_KEY not configured in environment"
        )

    return {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }


@router.post("/{config_id}/apply-custom-settings")
async def apply_custom_settings_to_vapi(
    config_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Apply custom_settings_override from automation config to VAPI assistant.
    
    This endpoint reads the automation config, checks for custom_settings_override,
    and updates the VAPI assistant to use custom provider webhooks.
    
    Args:
        config_id: Automation config ID
        
    Returns:
        Update result with assistant ID
    """
    try:
        # Get automation config
        config_collection = get_collection("automation_configs")
        from bson import ObjectId
        
        # Use async find_one
        config = await config_collection.find_one({"_id": ObjectId(config_id)})
        
        if not config:
            raise HTTPException(status_code=404, detail="Automation config not found")
        
        # Get VAPI agent config
        vapi_agent = config.get("vapi_agent") or config.get("vapiAgent", {})
        assistant_id = vapi_agent.get("assistant_id") or vapi_agent.get("assistantId")
        
        if not assistant_id:
            raise HTTPException(
                status_code=400,
                detail="No VAPI assistant ID found in automation config"
            )
        
        # Check if custom settings exist
        custom_override = vapi_agent.get("custom_settings_override") or vapi_agent.get("customSettingsOverride")
        if not custom_override:
            return {
                "success": True,
                "message": "No custom settings override found. Using VAPI defaults.",
                "assistant_id": assistant_id
            }
        
        # Build VAPI assistant config with custom providers
        vapi_config = build_vapi_assistant_config(vapi_agent, assistant_id)
        
        # Update VAPI assistant
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{VAPI_API_BASE}/assistant/{assistant_id}",
                headers=get_vapi_headers(),
                json=vapi_config,
                timeout=30.0
            )
            
            if response.status_code == 200:
                logger.info(f"Updated VAPI assistant {assistant_id} with custom settings")
                return {
                    "success": True,
                    "message": "VAPI assistant updated with custom settings",
                    "assistant_id": assistant_id
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Vapi API error: {response.text}"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to apply custom settings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to apply custom settings: {str(e)}")

