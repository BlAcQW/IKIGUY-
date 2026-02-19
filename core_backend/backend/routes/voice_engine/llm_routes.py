"""
LLM provider and model management routes.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException

from .models import (
    LLMProviderCreate, LLMProviderUpdate, LLMModelCreate, LLMModelUpdate
)
from ...models import LLMProvider, LLMModel
from ...services.llm_service import llm_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/llm", tags=["llm"])


@router.get("/providers", response_model=List[LLMProvider])
async def get_llm_providers(active_only: bool = True):
    """
    Get all LLM providers.
    
    Args:
        active_only: Whether to return only active providers
        
    Returns:
        List of LLM providers
    """
    try:
        return await llm_service.get_providers(active_only=active_only)
    except Exception as e:
        logger.error(f"Failed to get LLM providers: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve providers")


@router.post("/providers", response_model=LLMProvider)
async def create_llm_provider(provider: LLMProviderCreate):
    """
    Create a new LLM provider.
    
    Args:
        provider: Provider data
        
    Returns:
        Created provider
    """
    try:
        provider_model = LLMProvider(**provider.model_dump())
        return await llm_service.create_provider(provider_model)
    except Exception as e:
        logger.error(f"Failed to create LLM provider: {e}")
        raise HTTPException(status_code=500, detail="Failed to create provider")


@router.get("/providers/{provider_id}", response_model=LLMProvider)
async def get_llm_provider(provider_id: str):
    """
    Get LLM provider by ID.
    
    Args:
        provider_id: Provider ID
        
    Returns:
        LLM provider
    """
    try:
        provider = await llm_service.get_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        return provider
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get LLM provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve provider")


@router.put("/providers/{provider_id}", response_model=LLMProvider)
async def update_llm_provider(provider_id: str, updates: LLMProviderUpdate):
    """
    Update LLM provider.
    
    Args:
        provider_id: Provider ID
        updates: Updates to apply
        
    Returns:
        Updated provider
    """
    try:
        # Filter out None values
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
        
        provider = await llm_service.update_provider(provider_id, update_data)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        return provider
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update LLM provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update provider")


@router.delete("/providers/{provider_id}")
async def delete_llm_provider(provider_id: str):
    """
    Delete LLM provider.
    
    Args:
        provider_id: Provider ID
        
    Returns:
        Success message
    """
    try:
        success = await llm_service.delete_provider(provider_id)
        if not success:
            raise HTTPException(status_code=404, detail="Provider not found")
        return {"message": "Provider deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete LLM provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete provider")


@router.get("/models", response_model=List[LLMModel])
async def get_llm_models(provider_id: Optional[str] = None, active_only: bool = True):
    """
    Get all LLM models.
    
    Args:
        provider_id: Filter by provider ID
        active_only: Whether to return only active models
        
    Returns:
        List of LLM models
    """
    try:
        return await llm_service.get_models(provider_id=provider_id, active_only=active_only)
    except Exception as e:
        logger.error(f"Failed to get LLM models: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve models")


@router.post("/models", response_model=LLMModel)
async def create_llm_model(model: LLMModelCreate):
    """
    Create a new LLM model.
    
    Args:
        model: Model data
        
    Returns:
        Created model
    """
    try:
        model_obj = LLMModel(**model.model_dump())
        return await llm_service.create_model(model_obj)
    except Exception as e:
        logger.error(f"Failed to create LLM model: {e}")
        raise HTTPException(status_code=500, detail="Failed to create model")


@router.get("/models/{model_id}", response_model=LLMModel)
async def get_llm_model(model_id: str):
    """
    Get LLM model by ID.
    
    Args:
        model_id: Model ID
        
    Returns:
        LLM model
    """
    try:
        model = await llm_service.get_model(model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        return model
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get LLM model {model_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve model")


@router.put("/models/{model_id}", response_model=LLMModel)
async def update_llm_model(model_id: str, updates: LLMModelUpdate):
    """
    Update LLM model.
    
    Args:
        model_id: Model ID
        updates: Updates to apply
        
    Returns:
        Updated model
    """
    try:
        # Filter out None values
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
        
        model = await llm_service.update_model(model_id, update_data)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        return model
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update LLM model {model_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update model")


@router.delete("/models/{model_id}")
async def delete_llm_model(model_id: str):
    """
    Delete LLM model.
    
    Args:
        model_id: Model ID
        
    Returns:
        Success message
    """
    try:
        success = await llm_service.delete_model(model_id)
        if not success:
            raise HTTPException(status_code=404, detail="Model not found")
        return {"message": "Model deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete LLM model {model_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete model")


@router.get("/providers/{provider_id}/models", response_model=List[LLMModel])
async def get_provider_models(provider_id: str):
    """
    Get all models for a specific provider.
    
    Args:
        provider_id: Provider ID
        
    Returns:
        List of models for the provider
    """
    try:
        return await llm_service.get_provider_models(provider_id)
    except Exception as e:
        logger.error(f"Failed to get models for provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve provider models")


@router.get("/default-model", response_model=LLMModel)
async def get_default_model():
    """
    Get the default LLM model.
    
    Returns:
        Default LLM model
    """
    try:
        model = await llm_service.get_default_model()
        if not model:
            raise HTTPException(status_code=404, detail="No default model configured")
        return model
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get default model: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve default model")


@router.post("/models/{model_id}/set-default")
async def set_default_model(model_id: str):
    """
    Set a model as the default.
    
    Args:
        model_id: Model ID to set as default
        
    Returns:
        Success message
    """
    try:
        success = await llm_service.set_default_model(model_id)
        if not success:
            raise HTTPException(status_code=404, detail="Model not found")
        return {"message": "Default model updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set default model {model_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to set default model")