"""
Voice provider and voice management routes.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException

from .models import VoiceProviderCreate, VoiceProviderUpdate, VoiceCreate, VoiceUpdate
from ...models import VoiceProvider, Voice
from ...services.voice_service import voice_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice-providers", tags=["voice-providers"])


@router.get("/", response_model=List[VoiceProvider])
async def get_voice_providers(active_only: bool = True):
    """
    Get all voice providers.
    
    Args:
        active_only: Whether to return only active providers
        
    Returns:
        List of voice providers
    """
    try:
        return await voice_service.get_providers(active_only=active_only)
    except Exception as e:
        logger.error(f"Failed to get voice providers: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve providers")


@router.post("/", response_model=VoiceProvider)
async def create_voice_provider(provider: VoiceProviderCreate):
    """
    Create a new voice provider.
    
    Args:
        provider: Provider data
        
    Returns:
        Created provider
    """
    try:
        provider_model = VoiceProvider(**provider.model_dump())
        return await voice_service.create_provider(provider_model)
    except Exception as e:
        logger.error(f"Failed to create voice provider: {e}")
        raise HTTPException(status_code=500, detail="Failed to create provider")


@router.get("/{provider_id}", response_model=VoiceProvider)
async def get_voice_provider(provider_id: str):
    """
    Get voice provider by ID.
    
    Args:
        provider_id: Provider ID
        
    Returns:
        Voice provider
    """
    try:
        provider = await voice_service.get_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        return provider
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get voice provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve provider")


@router.put("/{provider_id}", response_model=VoiceProvider)
async def update_voice_provider(provider_id: str, updates: VoiceProviderUpdate):
    """
    Update voice provider.
    
    Args:
        provider_id: Provider ID
        updates: Updates to apply
        
    Returns:
        Updated provider
    """
    try:
        # Filter out None values
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
        
        provider = await voice_service.update_provider(provider_id, update_data)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        return provider
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update voice provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update provider")


@router.delete("/{provider_id}")
async def delete_voice_provider(provider_id: str):
    """
    Delete voice provider.
    
    Args:
        provider_id: Provider ID
        
    Returns:
        Success message
    """
    try:
        success = await voice_service.delete_provider(provider_id)
        if not success:
            raise HTTPException(status_code=404, detail="Provider not found")
        return {"message": "Provider deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete voice provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete provider")


@router.get("/{provider_id}/voices", response_model=List[Voice])
async def get_provider_voices(provider_id: str, active_only: bool = True):
    """
    Get all voices for a specific provider.
    
    Args:
        provider_id: Provider ID
        active_only: Whether to return only active voices
        
    Returns:
        List of voices for the provider
    """
    try:
        return await voice_service.get_provider_voices(provider_id, active_only=active_only)
    except Exception as e:
        logger.error(f"Failed to get voices for provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve provider voices")


# Voice management routes
voices_router = APIRouter(prefix="/voices", tags=["voices"])


@voices_router.get("/", response_model=List[Voice])
async def get_voices(provider_id: Optional[str] = None, language: Optional[str] = None, active_only: bool = True):
    """
    Get all voices with optional filtering.
    
    Args:
        provider_id: Filter by provider ID
        language: Filter by language code
        active_only: Whether to return only active voices
        
    Returns:
        List of voices
    """
    try:
        return await voice_service.get_voices(
            provider_id=provider_id, 
            language=language, 
            active_only=active_only
        )
    except Exception as e:
        logger.error(f"Failed to get voices: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve voices")


@voices_router.post("/", response_model=Voice)
async def create_voice(voice: VoiceCreate):
    """
    Create a new voice.
    
    Args:
        voice: Voice data
        
    Returns:
        Created voice
    """
    try:
        voice_model = Voice(**voice.model_dump())
        return await voice_service.create_voice(voice_model)
    except Exception as e:
        logger.error(f"Failed to create voice: {e}")
        raise HTTPException(status_code=500, detail="Failed to create voice")


@voices_router.get("/{voice_id}", response_model=Voice)
async def get_voice(voice_id: str):
    """
    Get voice by ID.
    
    Args:
        voice_id: Voice ID
        
    Returns:
        Voice
    """
    try:
        voice = await voice_service.get_voice(voice_id)
        if not voice:
            raise HTTPException(status_code=404, detail="Voice not found")
        return voice
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get voice {voice_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve voice")


@voices_router.put("/{voice_id}", response_model=Voice)
async def update_voice(voice_id: str, updates: VoiceUpdate):
    """
    Update voice.
    
    Args:
        voice_id: Voice ID
        updates: Updates to apply
        
    Returns:
        Updated voice
    """
    try:
        # Filter out None values
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
        
        voice = await voice_service.update_voice(voice_id, update_data)
        if not voice:
            raise HTTPException(status_code=404, detail="Voice not found")
        return voice
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update voice {voice_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update voice")


@voices_router.delete("/{voice_id}")
async def delete_voice(voice_id: str):
    """
    Delete voice.
    
    Args:
        voice_id: Voice ID
        
    Returns:
        Success message
    """
    try:
        success = await voice_service.delete_voice(voice_id)
        if not success:
            raise HTTPException(status_code=404, detail="Voice not found")
        return {"message": "Voice deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete voice {voice_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete voice")


# Include both routers - voice providers and voices
voice_management_routers = [router, voices_router]