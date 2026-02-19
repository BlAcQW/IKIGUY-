"""
Notebook management routes for African Language Community Platform.

Handles AI model notebooks for training and inference.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional, List
from bson import ObjectId

from models.responses import DataResponse, ListResponse

router = APIRouter()


@router.get("")
async def get_notebooks(
    language_code: Optional[str] = Query(None, description="Filter by language code"),
    type: Optional[str] = Query(None, description="Filter by notebook type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
) -> List[dict]:
    """
    Get all AI model notebooks with optional filtering.

    Args:
        language_code: Optional language code filter
        type: Optional notebook type filter
        page: Page number (starts from 1)
        page_size: Number of notebooks per page

    Returns:
        List[dict]: List of notebooks
    """
    try:
        # Mock data for now - replace with actual database queries
        mock_notebooks = [
            {
                "id": "notebook_1",
                "name": "Twi ASR Training",
                "type": "data_acquisition",
                "language_code": "twi",
                "version": "1.0.0",
                "model_type": "asr",
                "description": "Automatic Speech Recognition training notebook for Twi language",
                "file_url": "https://example.com/notebooks/twi_asr_training.ipynb",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-20T15:30:00Z"
            },
            {
                "id": "notebook_2",
                "name": "Yoruba TTS Model",
                "type": "training",
                "language_code": "yor",
                "version": "2.1.0",
                "model_type": "tts",
                "description": "Text-to-Speech model training for Yoruba language",
                "file_url": "https://example.com/notebooks/yoruba_tts.ipynb",
                "created_at": "2024-02-01T09:00:00Z",
                "updated_at": "2024-02-10T14:15:00Z"
            },
            {
                "id": "notebook_3",
                "name": "Swahili Language Processing",
                "type": "data_processing",
                "language_code": "swa",
                "version": "1.5.0",
                "model_type": "llm",
                "description": "Data preprocessing and cleaning for Swahili corpus",
                "file_url": "https://example.com/notebooks/swahili_processing.ipynb",
                "created_at": "2024-01-10T08:30:00Z",
                "updated_at": "2024-01-25T16:45:00Z"
            }
        ]

        # Apply filters
        filtered_notebooks = mock_notebooks
        if language_code:
            filtered_notebooks = [nb for nb in filtered_notebooks if nb["language_code"] == language_code]
        if type:
            filtered_notebooks = [nb for nb in filtered_notebooks if nb["type"] == type]

        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_notebooks = filtered_notebooks[start_idx:end_idx]

        return paginated_notebooks

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve notebooks: {str(e)}"
        )


@router.get("/{notebook_id}", response_model=DataResponse)
async def get_notebook(notebook_id: str):
    """
    Get detailed information about a specific notebook.

    Args:
        notebook_id: Notebook ID

    Returns:
        DataResponse: Notebook information
    """
    try:
        # Mock notebook data - replace with actual database query
        mock_notebook = {
            "id": notebook_id,
            "name": "Twi ASR Training",
            "type": "data_acquisition",
            "language_code": "twi",
            "version": "1.0.0",
            "model_type": "asr",
            "description": "Automatic Speech Recognition training notebook for Twi language",
            "file_url": "https://example.com/notebooks/twi_asr_training.ipynb",
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-20T15:30:00Z",
            "tags": ["speech-recognition", "twi", "training"],
            "author": "Language AI Team",
            "requirements": ["torch", "transformers", "datasets"],
            "metrics": {
                "accuracy": 0.85,
                "wer": 0.15,
                "training_time_hours": 24
            }
        }

        return DataResponse(
            data=mock_notebook,
            message="Notebook retrieved successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve notebook: {str(e)}"
        )


@router.get("/language/{language_code}/model/{model_type}")
async def get_notebooks_by_language_and_model(
    language_code: str,
    model_type: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
) -> List[dict]:
    """
    Get notebooks filtered by language and model type.

    Args:
        language_code: Language code (e.g., 'twi', 'yor')
        model_type: Model type (e.g., 'asr', 'tts', 'llm')
        page: Page number
        page_size: Items per page

    Returns:
        List[dict]: Filtered notebooks
    """
    try:
        # Mock filtered data - replace with actual database query
        mock_notebooks = [
            {
                "id": "filtered_notebook_1",
                "name": f"{language_code.title()} {model_type.upper()} Model",
                "type": "training",
                "language_code": language_code,
                "version": "1.0.0",
                "model_type": model_type,
                "description": f"{model_type.upper()} model for {language_code} language",
                "file_url": f"https://example.com/notebooks/{language_code}_{model_type}.ipynb",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-20T15:30:00Z"
            }
        ]

        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        return mock_notebooks[start_idx:end_idx]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve notebooks: {str(e)}"
        )