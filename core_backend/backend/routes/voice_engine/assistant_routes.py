"""
Assistant configuration and management routes.
"""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException

from .models import AssistantConfigRequest, AssistantConfigUpdate
from ...models import Assistant
from ...services.assistant_service import assistant_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assistants", tags=["assistants"])


@router.get("/", response_model=List[Assistant])
async def get_assistants(user_id: str = None, active_only: bool = True):
    """
    Get all voice assistants.
    
    Args:
        user_id: Optional user ID to filter assistants
        active_only: Whether to return only active assistants
        
    Returns:
        List of assistants
    """
    try:
        if user_id:
            assistants = assistant_service.get_assistants_by_user(user_id)
            if active_only:
                assistants = [a for a in assistants if a.status == 'active']
            return assistants
        else:
            # Return all assistants when no user_id provided
            assistants = assistant_service.get_all_assistants()
            if active_only:
                assistants = [a for a in assistants if a.status == 'active']
            return assistants
    except Exception as e:
        logger.error(f"Failed to get assistants: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve assistants")


@router.post("/", response_model=Assistant)
async def create_assistant(config: AssistantConfigRequest):
    """
    Create a new voice assistant configuration.
    
    Args:
        config: Assistant configuration
        
    Returns:
        Created assistant
    """
    try:
        assistant = Assistant(**config.model_dump())
        # Don't await since create_assistant is not async
        return assistant_service.create_assistant(assistant)
    except Exception as e:
        logger.error(f"Failed to create assistant: {e}")
        raise HTTPException(status_code=500, detail="Failed to create assistant")


@router.get("/{assistant_id}", response_model=Assistant)
async def get_assistant(assistant_id: str):
    """
    Get assistant by ID.
    
    Args:
        assistant_id: Assistant ID
        
    Returns:
        Assistant configuration
    """
    try:
        # Don't await since get_assistant is not async
        assistant = assistant_service.get_assistant(assistant_id)
        if not assistant:
            raise HTTPException(status_code=404, detail="Assistant not found")
        return assistant
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get assistant {assistant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve assistant")


@router.put("/{assistant_id}", response_model=Assistant)
async def update_assistant(assistant_id: str, updates: AssistantConfigUpdate):
    """
    Update assistant configuration.
    
    Args:
        assistant_id: Assistant ID
        updates: Updates to apply
        
    Returns:
        Updated assistant
    """
    try:
        # Filter out None values
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
        
        # Don't await since update_assistant is not async
        assistant = assistant_service.update_assistant(assistant_id, update_data)
        if not assistant:
            raise HTTPException(status_code=404, detail="Assistant not found")
        return assistant
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update assistant {assistant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update assistant")


@router.delete("/{assistant_id}")
async def delete_assistant(assistant_id: str):
    """
    Delete assistant.
    
    Args:
        assistant_id: Assistant ID
        
    Returns:
        Success message
    """
    try:
        # Don't await since delete_assistant is not async
        success = assistant_service.delete_assistant(assistant_id)
        if not success:
            raise HTTPException(status_code=404, detail="Assistant not found")
        return {"message": "Assistant deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete assistant {assistant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete assistant")


@router.post("/{assistant_id}/activate")
async def activate_assistant(assistant_id: str):
    """
    Activate an assistant.
    
    Args:
        assistant_id: Assistant ID
        
    Returns:
        Success message
    """
    try:
        # Don't await since activate_assistant is not async
        success = assistant_service.activate_assistant(assistant_id)
        if not success:
            raise HTTPException(status_code=404, detail="Assistant not found")
        return {"message": "Assistant activated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate assistant {assistant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to activate assistant")


@router.post("/{assistant_id}/deactivate")
async def deactivate_assistant(assistant_id: str):
    """
    Deactivate an assistant.
    
    Args:
        assistant_id: Assistant ID
        
    Returns:
        Success message
    """
    try:
        # Don't await since deactivate_assistant is not async
        success = assistant_service.deactivate_assistant(assistant_id)
        if not success:
            raise HTTPException(status_code=404, detail="Assistant not found")
        return {"message": "Assistant deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate assistant {assistant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to deactivate assistant")


@router.get("/{assistant_id}/test")
async def test_assistant(assistant_id: str, test_input: str = "Hello, how are you?"):
    """
    Test an assistant configuration with sample input.
    
    Args:
        assistant_id: Assistant ID
        test_input: Test input text
        
    Returns:
        Test result
    """
    try:
        # Don't await since get_assistant is not async
        assistant = assistant_service.get_assistant(assistant_id)
        if not assistant:
            raise HTTPException(status_code=404, detail="Assistant not found")
        
        # TODO: Implement actual assistant testing logic
        test_result = {
            "assistant_id": assistant_id,
            "test_input": test_input,
            "test_output": f"Test response from {assistant.name}: {test_input}",
            "status": "success",
            "response_time": 0.5,
            "voice_synthesis": "completed",
            "llm_response": "completed"
        }
        
        return test_result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test assistant {assistant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to test assistant")