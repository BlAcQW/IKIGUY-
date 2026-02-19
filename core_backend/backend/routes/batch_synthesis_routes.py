"""
Batch Synthesis Routes

API endpoints for batch TTS synthesis from CSV files.

Created: 2025-10-27
Sprint 4: Advanced Features (Phase 9)
"""

import os
import asyncio
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..services.batch_synthesis_service import BatchSynthesisService, BatchJob
from ..services.tts_service import TTSService
from ..services.billing_service import BillingService
from ..middleware.auth_middleware import get_current_user


router = APIRouter(prefix="/api/tts/batch", tags=["batch-synthesis"])


# Initialize services
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
batch_service = BatchSynthesisService(MONGODB_URL)
tts_service = TTSService(MONGODB_URL)
billing_service = BillingService(MONGODB_URL)


class CreateBatchRequest(BaseModel):
    """Request to create a batch synthesis job"""
    provider_id: str
    language: str = "en"
    voice_id: str | None = None
    speed: float = 1.0
    pitch: float = 0.0


class BatchJobResponse(BaseModel):
    """Batch job response"""
    id: str
    status: str
    total_items: int
    completed_items: int
    failed_items: int
    total_cost: float
    zip_filename: str | None = None
    created_at: str
    completed_at: str | None = None


async def process_batch_job(batch_id: str):
    """
    Process batch synthesis job in the background.

    Args:
        batch_id: Batch job ID
    """
    try:
        # Get batch job
        job = await batch_service.jobs_collection.find_one({"_id": batch_id})
        if not job:
            return

        # Update status to processing
        await batch_service.update_batch_job_status(batch_id, "processing")

        # Get all items
        items = await batch_service.get_batch_items(batch_id)

        # Process each item
        completed = 0
        failed = 0
        total_cost = 0.0

        for item in items:
            try:
                # Synthesize audio
                result = await tts_service.synthesize(
                    provider_id=job["provider_id"],
                    text=item.text,
                    language=job.get("language", "en"),
                    voice_id=job.get("voice_id"),
                    speed=job.get("speed", 1.0),
                    pitch=job.get("pitch", 0.0),
                    user_id=job["user_id"]
                )

                if result:
                    # Update item status
                    await batch_service.update_batch_item_status(
                        item.id,
                        "completed",
                        audio_base64=result.get("audio_base64"),
                        duration_seconds=result.get("duration_seconds", 0.0),
                        cost=result.get("cost", 0.0)
                    )
                    completed += 1
                    total_cost += result.get("cost", 0.0)
                else:
                    await batch_service.update_batch_item_status(
                        item.id,
                        "failed",
                        error_message="Synthesis failed"
                    )
                    failed += 1

            except Exception as e:
                await batch_service.update_batch_item_status(
                    item.id,
                    "failed",
                    error_message=str(e)
                )
                failed += 1

        # Update job progress
        await batch_service.jobs_collection.update_one(
            {"_id": batch_id},
            {"$set": {
                "completed_items": completed,
                "failed_items": failed,
                "total_cost": total_cost
            }}
        )

        # Create ZIP file
        if completed > 0:
            await batch_service.create_zip_file(batch_id)
        else:
            await batch_service.update_batch_job_status(batch_id, "failed")

    except Exception as e:
        print(f"Error processing batch job {batch_id}: {e}")
        await batch_service.update_batch_job_status(
            batch_id,
            "failed",
            error_message=str(e)
        )


@router.post("/upload", response_model=BatchJobResponse)
async def create_batch_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    provider_id: str = "coqui_xtts",
    language: str = "en",
    voice_id: str | None = None,
    speed: float = 1.0,
    pitch: float = 0.0,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new batch synthesis job from CSV file.

    Expected CSV format:
    ```
    text,filename
    "Hello world","greeting.wav"
    "Another text","output2.wav"
    ```

    The filename column is optional. If not provided, files will be named audio_1.wav, audio_2.wav, etc.
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    try:
        # Parse CSV
        items = await batch_service.parse_csv(file)

        if not items:
            raise HTTPException(status_code=400, detail="CSV file is empty or invalid")

        if len(items) > 1000:
            raise HTTPException(status_code=400, detail="Maximum 1000 items per batch")

        # Create batch job
        batch_id = await batch_service.create_batch_job(
            user_id=current_user["user_id"],
            provider_id=provider_id,
            items=items,
            language=language,
            voice_id=voice_id,
            speed=speed,
            pitch=pitch
        )

        # Start background processing
        background_tasks.add_task(process_batch_job, batch_id)

        # Return batch job
        job = await batch_service.get_batch_job(batch_id, current_user["user_id"])
        return BatchJobResponse(
            id=job.id,
            status=job.status,
            total_items=job.total_items,
            completed_items=job.completed_items,
            failed_items=job.failed_items,
            total_cost=job.total_cost,
            zip_filename=job.zip_filename,
            created_at=job.created_at.isoformat(),
            completed_at=job.completed_at.isoformat() if job.completed_at else None
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create batch job: {str(e)}")


@router.get("/{batch_id}", response_model=BatchJobResponse)
async def get_batch_job(
    batch_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get batch job status and details.
    """
    job = await batch_service.get_batch_job(batch_id, current_user["user_id"])

    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found")

    return BatchJobResponse(
        id=job.id,
        status=job.status,
        total_items=job.total_items,
        completed_items=job.completed_items,
        failed_items=job.failed_items,
        total_cost=job.total_cost,
        zip_filename=job.zip_filename,
        created_at=job.created_at.isoformat(),
        completed_at=job.completed_at.isoformat() if job.completed_at else None
    )


@router.get("/{batch_id}/download")
async def download_batch_result(
    batch_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Download batch synthesis results as ZIP file.
    """
    job = await batch_service.get_batch_job(batch_id, current_user["user_id"])

    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found")

    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Batch job is not completed yet")

    if not job.zip_path or not os.path.exists(job.zip_path):
        raise HTTPException(status_code=404, detail="ZIP file not found")

    return FileResponse(
        job.zip_path,
        media_type="application/zip",
        filename=job.zip_filename
    )


@router.get("", response_model=List[BatchJobResponse])
async def list_batch_jobs(
    skip: int = 0,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """
    List user's batch jobs.
    """
    jobs = await batch_service.list_batch_jobs(
        current_user["user_id"],
        skip=skip,
        limit=limit
    )

    return [
        BatchJobResponse(
            id=job.id,
            status=job.status,
            total_items=job.total_items,
            completed_items=job.completed_items,
            failed_items=job.failed_items,
            total_cost=job.total_cost,
            zip_filename=job.zip_filename,
            created_at=job.created_at.isoformat(),
            completed_at=job.completed_at.isoformat() if job.completed_at else None
        )
        for job in jobs
    ]


@router.delete("/{batch_id}")
async def delete_batch_job(
    batch_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete batch job and all its data.
    """
    try:
        await batch_service.delete_batch_job(batch_id, current_user["user_id"])
        return {"message": "Batch job deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete batch job: {str(e)}")
