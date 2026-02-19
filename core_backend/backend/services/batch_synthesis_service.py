"""
Batch Synthesis Service

Handles batch TTS synthesis jobs from CSV files.
Processes multiple synthesis requests in the background and generates ZIP files.

Created: 2025-10-27
Sprint 4: Advanced Features (Phase 9)
"""

import os
import csv
import io
import zipfile
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId
from fastapi import UploadFile
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field


class BatchJob(BaseModel):
    """Batch synthesis job"""
    id: str = Field(alias="_id")
    user_id: str
    provider_id: str
    language: str = "en"
    voice_id: Optional[str] = None
    speed: float = 1.0
    pitch: float = 0.0

    # Job metadata
    total_items: int
    completed_items: int = 0
    failed_items: int = 0
    status: str = "pending"  # pending, processing, completed, failed

    # Storage paths
    zip_filename: Optional[str] = None
    zip_path: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Billing
    total_cost: float = 0.0

    class Config:
        populate_by_name = True


class BatchItem(BaseModel):
    """Individual item in a batch job"""
    id: str = Field(alias="_id")
    batch_id: str
    text: str
    filename: str
    status: str = "pending"  # pending, processing, completed, failed
    audio_base64: Optional[str] = None
    error_message: Optional[str] = None
    cost: float = 0.0
    duration_seconds: float = 0.0

    class Config:
        populate_by_name = True


class BatchSynthesisService:
    """Service for managing batch TTS synthesis"""

    def __init__(self, mongodb_url: str, db_name: str = "kasaai_core"):
        """
        Initialize batch synthesis service.

        Args:
            mongodb_url: MongoDB connection URL
            db_name: Database name
        """
        self.client = AsyncIOMotorClient(mongodb_url)
        self.db = self.client[db_name]
        self.jobs_collection = self.db["batch_synthesis_jobs"]
        self.items_collection = self.db["batch_synthesis_items"]

        # Batch storage directory
        self.batch_storage_dir = "/opt/kasaai/apps/voice-lab/batch_outputs"
        os.makedirs(self.batch_storage_dir, exist_ok=True)

    async def parse_csv(self, file: UploadFile) -> List[Dict[str, str]]:
        """
        Parse CSV file and extract text entries.

        Expected CSV format:
        text,filename (optional)
        "Hello world","greeting.wav"
        "Another text","output2.wav"

        Args:
            file: Uploaded CSV file

        Returns:
            List of dictionaries with 'text' and 'filename' keys
        """
        content = await file.read()
        decoded = content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded))

        items = []
        for idx, row in enumerate(reader):
            if 'text' not in row:
                raise ValueError("CSV must have a 'text' column")

            text = row['text'].strip()
            if not text:
                continue

            # Generate filename if not provided
            filename = row.get('filename', f"audio_{idx+1}.wav").strip()
            if not filename.endswith('.wav'):
                filename += '.wav'

            items.append({
                'text': text,
                'filename': filename
            })

        return items

    async def create_batch_job(
        self,
        user_id: str,
        provider_id: str,
        items: List[Dict[str, str]],
        language: str = "en",
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        pitch: float = 0.0
    ) -> str:
        """
        Create a new batch synthesis job.

        Args:
            user_id: User ID
            provider_id: TTS provider ID
            items: List of items to synthesize
            language: Language code
            voice_id: Voice ID (optional)
            speed: Speech speed
            pitch: Speech pitch

        Returns:
            Batch job ID
        """
        # Create batch job
        batch_job = BatchJob(
            _id=str(ObjectId()),
            user_id=user_id,
            provider_id=provider_id,
            total_items=len(items),
            language=language,
            voice_id=voice_id,
            speed=speed,
            pitch=pitch
        )

        await self.jobs_collection.insert_one(batch_job.dict(by_alias=True))

        # Create batch items
        batch_items = []
        for item in items:
            batch_item = BatchItem(
                _id=str(ObjectId()),
                batch_id=batch_job.id,
                text=item['text'],
                filename=item['filename']
            )
            batch_items.append(batch_item.dict(by_alias=True))

        if batch_items:
            await self.items_collection.insert_many(batch_items)

        return batch_job.id

    async def get_batch_job(self, batch_id: str, user_id: str) -> Optional[BatchJob]:
        """
        Get batch job by ID.

        Args:
            batch_id: Batch job ID
            user_id: User ID (for authorization)

        Returns:
            Batch job or None if not found
        """
        job_data = await self.jobs_collection.find_one({
            "_id": batch_id,
            "user_id": user_id
        })

        if job_data:
            return BatchJob(**job_data)
        return None

    async def list_batch_jobs(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[BatchJob]:
        """
        List user's batch jobs.

        Args:
            user_id: User ID
            skip: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            List of batch jobs
        """
        cursor = self.jobs_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).skip(skip).limit(limit)

        jobs = []
        async for job_data in cursor:
            jobs.append(BatchJob(**job_data))

        return jobs

    async def get_batch_items(self, batch_id: str) -> List[BatchItem]:
        """
        Get all items for a batch job.

        Args:
            batch_id: Batch job ID

        Returns:
            List of batch items
        """
        cursor = self.items_collection.find({"batch_id": batch_id})

        items = []
        async for item_data in cursor:
            items.append(BatchItem(**item_data))

        return items

    async def update_batch_job_status(
        self,
        batch_id: str,
        status: str,
        **kwargs
    ):
        """
        Update batch job status.

        Args:
            batch_id: Batch job ID
            status: New status
            **kwargs: Additional fields to update
        """
        update_data = {"status": status}
        update_data.update(kwargs)

        if status == "processing" and "started_at" not in kwargs:
            update_data["started_at"] = datetime.utcnow()
        elif status in ["completed", "failed"] and "completed_at" not in kwargs:
            update_data["completed_at"] = datetime.utcnow()

        await self.jobs_collection.update_one(
            {"_id": batch_id},
            {"$set": update_data}
        )

    async def update_batch_item_status(
        self,
        item_id: str,
        status: str,
        **kwargs
    ):
        """
        Update batch item status.

        Args:
            item_id: Batch item ID
            status: New status
            **kwargs: Additional fields to update (audio_base64, error_message, etc.)
        """
        update_data = {"status": status}
        update_data.update(kwargs)

        await self.items_collection.update_one(
            {"_id": item_id},
            {"$set": update_data}
        )

    async def create_zip_file(self, batch_id: str) -> str:
        """
        Create ZIP file with all completed audio files.

        Args:
            batch_id: Batch job ID

        Returns:
            Path to ZIP file
        """
        # Get all completed items
        items = await self.get_batch_items(batch_id)
        completed_items = [item for item in items if item.status == "completed" and item.audio_base64]

        if not completed_items:
            raise ValueError("No completed items to zip")

        # Create ZIP file
        zip_filename = f"batch_{batch_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
        zip_path = os.path.join(self.batch_storage_dir, zip_filename)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for item in completed_items:
                # Decode base64 audio
                import base64
                audio_data = base64.b64decode(item.audio_base64)

                # Write to ZIP
                zipf.writestr(item.filename, audio_data)

        # Update job with ZIP info
        await self.update_batch_job_status(
            batch_id,
            status="completed",
            zip_filename=zip_filename,
            zip_path=zip_path
        )

        return zip_path

    async def delete_batch_job(self, batch_id: str, user_id: str):
        """
        Delete batch job and all its items.

        Args:
            batch_id: Batch job ID
            user_id: User ID (for authorization)
        """
        # Verify ownership
        job = await self.get_batch_job(batch_id, user_id)
        if not job:
            raise ValueError("Batch job not found")

        # Delete ZIP file if exists
        if job.zip_path and os.path.exists(job.zip_path):
            os.remove(job.zip_path)

        # Delete job and items from database
        await self.items_collection.delete_many({"batch_id": batch_id})
        await self.jobs_collection.delete_one({"_id": batch_id, "user_id": user_id})
