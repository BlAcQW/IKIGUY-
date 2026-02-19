"""
Dataset integration API endpoints for African Language Community Platform.

Handles external dataset integration with Common Voice, OpenSLR, Masakhane.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from models.dataset_models import (
    ExternalDatasetCreate,
    ExternalDataset,
    DatasetProcessingJob,
    DatasetIntegrationManifest,
    DatasetStats,
    CommonVoiceIntegration,
    OpenSLRIntegration,
    MasakhaneIntegration,
    DatasetSource,
    DatasetType,
    ProcessingStatus,
    DatasetIntegrationResponse,
    DatasetSearchResponse
)
from services.dataset_integration_service import DatasetIntegrationService
from database import get_database
from routes.auth import get_current_user
from models.user_models import User

logger = logging.getLogger(__name__)
router = APIRouter(tags=["datasets"])


async def get_dataset_service() -> DatasetIntegrationService:
    """Get dataset integration service instance."""
    db = get_database()
    return DatasetIntegrationService(db)


@router.post("/", response_model=DatasetIntegrationResponse)
async def create_dataset_integration(
    dataset: ExternalDatasetCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: DatasetIntegrationService = Depends(get_dataset_service)
):
    """Create new external dataset integration."""
    try:
        result = await service.create_dataset_integration(
            dataset_data=dataset,
            created_by=current_user.id
        )

        # Start background processing if auto_process is enabled
        if dataset.auto_process:
            background_tasks.add_task(
                service.start_dataset_processing,
                result.dataset.id
            )

        logger.info(f"Dataset integration created: {result.dataset.id} by {current_user.id}")
        return result

    except Exception as e:
        logger.error(f"Failed to create dataset integration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=DatasetSearchResponse)
async def list_datasets(
    source: Optional[DatasetSource] = None,
    dataset_type: Optional[DatasetType] = None,
    language_code: Optional[str] = None,
    status: Optional[ProcessingStatus] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: DatasetIntegrationService = Depends(get_dataset_service)
):
    """List and search external datasets."""
    try:
        filters = {}
        if source:
            filters["source"] = source
        if dataset_type:
            filters["dataset_type"] = dataset_type
        if language_code:
            filters["language_code"] = language_code
        if status:
            filters["processing_status"] = status
        if search:
            filters["$text"] = {"$search": search}

        datasets, total_count = await service.search_datasets(
            filters=filters,
            page=page,
            limit=limit
        )

        suggestions = []
        if search and not datasets:
            suggestions = await service.get_search_suggestions(search)

        return DatasetSearchResponse(
            datasets=datasets,
            total_count=total_count,
            filters_applied=filters,
            suggestions=suggestions
        )

    except Exception as e:
        logger.error(f"Failed to list datasets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{dataset_id}", response_model=ExternalDataset)
async def get_dataset(
    dataset_id: str,
    service: DatasetIntegrationService = Depends(get_dataset_service)
):
    """Get dataset by ID."""
    try:
        dataset = await service.get_dataset_by_id(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        return dataset

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dataset {dataset_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{dataset_id}/process")
async def start_dataset_processing(
    dataset_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: DatasetIntegrationService = Depends(get_dataset_service)
):
    """Start processing an external dataset."""
    try:
        dataset = await service.get_dataset_by_id(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        if dataset.processing_status not in [ProcessingStatus.PENDING, ProcessingStatus.FAILED]:
            raise HTTPException(
                status_code=400,
                detail=f"Dataset is already {dataset.processing_status}"
            )

        # Start background processing
        background_tasks.add_task(
            service.start_dataset_processing,
            dataset_id
        )

        logger.info(f"Dataset processing started: {dataset_id} by {current_user.id}")
        return {"message": "Dataset processing started", "dataset_id": dataset_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start processing {dataset_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{dataset_id}/pause")
async def pause_dataset_processing(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    service: DatasetIntegrationService = Depends(get_dataset_service)
):
    """Pause dataset processing."""
    try:
        success = await service.pause_dataset_processing(dataset_id)
        if not success:
            raise HTTPException(status_code=400, detail="Cannot pause dataset processing")

        logger.info(f"Dataset processing paused: {dataset_id} by {current_user.id}")
        return {"message": "Dataset processing paused", "dataset_id": dataset_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause processing {dataset_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    service: DatasetIntegrationService = Depends(get_dataset_service)
):
    """Delete a dataset integration."""
    try:
        dataset = await service.get_dataset_by_id(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        # Check if user has permission to delete
        if dataset.created_by != current_user.id and current_user.role not in ["admin", "guardian"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        success = await service.delete_dataset(dataset_id)
        if not success:
            raise HTTPException(status_code=400, detail="Cannot delete dataset")

        logger.info(f"Dataset deleted: {dataset_id} by {current_user.id}")
        return {"message": "Dataset deleted successfully", "dataset_id": dataset_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete dataset {dataset_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{dataset_id}/jobs", response_model=List[DatasetProcessingJob])
async def get_dataset_jobs(
    dataset_id: str,
    service: DatasetIntegrationService = Depends(get_dataset_service)
):
    """Get processing jobs for a dataset."""
    try:
        jobs = await service.get_dataset_jobs(dataset_id)
        return jobs

    except Exception as e:
        logger.error(f"Failed to get jobs for dataset {dataset_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{dataset_id}/manifest", response_model=DatasetIntegrationManifest)
async def get_dataset_manifest(
    dataset_id: str,
    service: DatasetIntegrationService = Depends(get_dataset_service)
):
    """Get integration manifest for a dataset."""
    try:
        manifest = await service.get_dataset_manifest(dataset_id)
        if not manifest:
            raise HTTPException(status_code=404, detail="Manifest not found")
        return manifest

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get manifest for dataset {dataset_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{dataset_id}/download")
async def download_dataset_manifest(
    dataset_id: str,
    service: DatasetIntegrationService = Depends(get_dataset_service)
):
    """Download dataset manifest file."""
    try:
        manifest_data = await service.export_dataset_manifest(dataset_id)
        if not manifest_data:
            raise HTTPException(status_code=404, detail="Manifest not available")

        def generate_manifest():
            yield manifest_data

        return StreamingResponse(
            generate_manifest(),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=dataset_{dataset_id}_manifest.json"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download manifest for dataset {dataset_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/overview", response_model=DatasetStats)
async def get_dataset_stats(
    service: DatasetIntegrationService = Depends(get_dataset_service)
):
    """Get overview statistics for all datasets."""
    try:
        stats = await service.get_dataset_statistics()
        return stats

    except Exception as e:
        logger.error(f"Failed to get dataset statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Source-specific integration endpoints

@router.post("/common-voice", response_model=DatasetIntegrationResponse)
async def integrate_common_voice(
    integration: CommonVoiceIntegration,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: DatasetIntegrationService = Depends(get_dataset_service)
):
    """Create Common Voice dataset integration."""
    try:
        result = await service.create_common_voice_integration(
            integration_data=integration,
            created_by=current_user.id
        )

        # Start background processing
        background_tasks.add_task(
            service.process_common_voice_dataset,
            result.dataset.id,
            integration
        )

        logger.info(f"Common Voice integration created: {result.dataset.id}")
        return result

    except Exception as e:
        logger.error(f"Failed to create Common Voice integration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/openslr", response_model=DatasetIntegrationResponse)
async def integrate_openslr(
    integration: OpenSLRIntegration,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: DatasetIntegrationService = Depends(get_dataset_service)
):
    """Create OpenSLR dataset integration."""
    try:
        result = await service.create_openslr_integration(
            integration_data=integration,
            created_by=current_user.id
        )

        # Start background processing
        background_tasks.add_task(
            service.process_openslr_dataset,
            result.dataset.id,
            integration
        )

        logger.info(f"OpenSLR integration created: {result.dataset.id}")
        return result

    except Exception as e:
        logger.error(f"Failed to create OpenSLR integration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/masakhane", response_model=DatasetIntegrationResponse)
async def integrate_masakhane(
    integration: MasakhaneIntegration,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: DatasetIntegrationService = Depends(get_dataset_service)
):
    """Create Masakhane dataset integration."""
    try:
        result = await service.create_masakhane_integration(
            integration_data=integration,
            created_by=current_user.id
        )

        # Start background processing
        background_tasks.add_task(
            service.process_masakhane_dataset,
            result.dataset.id,
            integration
        )

        logger.info(f"Masakhane integration created: {result.dataset.id}")
        return result

    except Exception as e:
        logger.error(f"Failed to create Masakhane integration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))