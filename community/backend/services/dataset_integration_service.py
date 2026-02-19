"""
External dataset integration service for African Language Community Platform.

Handles integration with Common Voice, OpenSLR, Masakhane, and custom datasets.
"""

import asyncio
import aiohttp
import aiofiles
import tarfile
import zipfile
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import json
import csv
import logging
from bson import ObjectId

from database import get_database
from models.dataset_models import (
    ExternalDataset, ExternalDatasetCreate, DatasetProcessingJob,
    DatasetIntegrationManifest, DatasetStats, ProcessingStatus,
    CommonVoiceIntegration, OpenSLRIntegration, MasakhaneIntegration,
    DatasetIntegrationResponse, DatasetSearchResponse
)
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DatasetIntegrationService:
    """Service for external dataset integration operations."""

    def __init__(self, db=None):
        self.db = db
        self.session = None
        self.download_path = Path(settings.STORAGE_PATH) / "datasets"
        self.download_path.mkdir(parents=True, exist_ok=True)

    async def _get_db(self):
        """Get database connection."""
        if self.db is None:
            self.db = get_database()
        return self.db

    async def _get_session(self):
        """Get HTTP session."""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=3600)  # 1 hour timeout
            )
        return self.session

    async def create_dataset_integration(
        self,
        dataset_data: ExternalDatasetCreate,
        created_by: str
    ) -> DatasetIntegrationResponse:
        """
        Create a new external dataset integration.

        Args:
            dataset_data: Dataset creation data
            created_by: User ID creating the integration

        Returns:
            DatasetIntegrationResponse: Created dataset with processing jobs
        """
        try:
            db = await self._get_db()

            # Check for existing dataset with same source and language
            existing = await db.external_datasets.find_one({
                "source": dataset_data.source,
                "language_code": dataset_data.language_code,
                "source_url": str(dataset_data.source_url) if dataset_data.source_url else None
            })

            if existing:
                raise ValueError(f"Dataset already exists for {dataset_data.source} in {dataset_data.language_code}")

            dataset_doc = {
                "_id": ObjectId(),
                "name": dataset_data.name,
                "source": dataset_data.source,
                "dataset_type": dataset_data.dataset_type,
                "language_code": dataset_data.language_code,
                "language_family": dataset_data.language_family,
                "source_url": str(dataset_data.source_url) if dataset_data.source_url else None,
                "source_version": dataset_data.source_version,
                "source_metadata": dataset_data.source_metadata,
                "license_type": dataset_data.license_type,
                "license_url": str(dataset_data.license_url) if dataset_data.license_url else None,
                "attribution": dataset_data.attribution,
                "commercial_use_allowed": dataset_data.commercial_use_allowed,
                "processing_status": ProcessingStatus.PENDING,
                "processing_started_at": None,
                "processing_completed_at": None,
                "processing_error": None,
                "processing_logs": [],
                "total_files": None,
                "total_size_mb": None,
                "total_duration_hours": None,
                "total_words": None,
                "quality_score": None,
                "files_processed": 0,
                "files_integrated": 0,
                "files_rejected": 0,
                "duplicate_files": 0,
                "auto_process": dataset_data.auto_process,
                "quality_threshold": dataset_data.quality_threshold,
                "max_file_size_mb": dataset_data.max_file_size_mb,
                "target_format": dataset_data.target_format,
                "merge_with_existing": dataset_data.merge_with_existing,
                "priority": dataset_data.priority,
                "description": dataset_data.description,
                "tags": dataset_data.tags,
                "created_by": created_by,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_processed_at": None,
                "integrated_submissions": [],
                "integration_manifest_url": None
            }

            await db.external_datasets.insert_one(dataset_doc)

            # Create initial processing jobs if auto_process is enabled
            processing_jobs = []
            if dataset_data.auto_process:
                processing_jobs = await self._create_processing_jobs(str(dataset_doc["_id"]))

            dataset = ExternalDataset(**dataset_doc)
            return DatasetIntegrationResponse(
                dataset=dataset,
                processing_jobs=processing_jobs,
                estimated_completion_time=datetime.utcnow() + timedelta(hours=2)
            )

        except Exception as e:
            logger.error(f"Error creating dataset integration: {str(e)}")
            raise

    async def get_datasets(
        self,
        source: Optional[str] = None,
        language_code: Optional[str] = None,
        status: Optional[str] = None,
        dataset_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ExternalDataset], int]:
        """
        Get external datasets with filtering.

        Args:
            source: Filter by source
            language_code: Filter by language
            status: Filter by processing status
            dataset_type: Filter by dataset type
            page: Page number
            page_size: Items per page

        Returns:
            Tuple[List[ExternalDataset], int]: Datasets and total count
        """
        try:
            db = await self._get_db()

            # Build filter
            filter_query = {}
            if source:
                filter_query["source"] = source
            if language_code:
                filter_query["language_code"] = language_code
            if status:
                filter_query["processing_status"] = status
            if dataset_type:
                filter_query["dataset_type"] = dataset_type

            # Get total count
            total_count = await db.external_datasets.count_documents(filter_query)

            # Get paginated results
            cursor = db.external_datasets.find(filter_query)
            cursor = cursor.sort("created_at", -1)
            cursor = cursor.skip((page - 1) * page_size).limit(page_size)

            datasets = []
            async for doc in cursor:
                # Convert ObjectId to string for Pydantic
                doc['_id'] = str(doc['_id'])
                datasets.append(ExternalDataset(**doc))

            return datasets, total_count

        except Exception as e:
            logger.error(f"Error getting datasets: {str(e)}")
            raise

    async def start_dataset_processing(self, dataset_id: str) -> bool:
        """
        Start processing a dataset.

        Args:
            dataset_id: Dataset ID

        Returns:
            bool: Success status
        """
        try:
            db = await self._get_db()

            # Update dataset status
            await db.external_datasets.update_one(
                {"_id": ObjectId(dataset_id)},
                {
                    "$set": {
                        "processing_status": ProcessingStatus.DOWNLOADING,
                        "processing_started_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            # Get dataset details
            dataset_doc = await db.external_datasets.find_one({"_id": ObjectId(dataset_id)})
            if not dataset_doc:
                raise ValueError("Dataset not found")

            dataset = ExternalDataset(**dataset_doc)

            # Start processing based on source type
            if dataset.source == "common_voice":
                await self._process_common_voice_dataset(dataset)
            elif dataset.source == "openslr":
                await self._process_openslr_dataset(dataset)
            elif dataset.source == "masakhane":
                await self._process_masakhane_dataset(dataset)
            elif dataset.source == "custom_scrape":
                await self._process_custom_scrape_dataset(dataset)
            else:
                raise ValueError(f"Unsupported dataset source: {dataset.source}")

            return True

        except Exception as e:
            logger.error(f"Error starting dataset processing: {str(e)}")
            # Update dataset with error status
            await self._update_dataset_error(dataset_id, str(e))
            return False

    async def get_dataset_stats(self) -> DatasetStats:
        """
        Get dataset integration statistics.

        Returns:
            DatasetStats: Statistics
        """
        try:
            db = await self._get_db()

            # Aggregate statistics
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_datasets": {"$sum": 1},
                        "datasets_by_source": {
                            "$push": "$source"
                        },
                        "datasets_by_language": {
                            "$push": "$language_code"
                        },
                        "datasets_by_status": {
                            "$push": "$processing_status"
                        },
                        "total_files_integrated": {"$sum": "$files_integrated"},
                        "total_size_gb": {"$sum": {"$divide": ["$total_size_mb", 1024]}},
                        "total_audio_hours": {"$sum": "$total_duration_hours"},
                        "quality_scores": {"$push": "$quality_score"}
                    }
                }
            ]

            result = await db.external_datasets.aggregate(pipeline).to_list(1)

            if not result:
                return DatasetStats(
                    total_datasets=0,
                    datasets_by_source={},
                    datasets_by_language={},
                    datasets_by_status={},
                    total_files_integrated=0,
                    total_size_gb=0.0,
                    total_audio_hours=0.0,
                    average_quality_score=0.0,
                    processing_queue_length=0
                )

            stats = result[0]

            # Count by categories
            datasets_by_source = {}
            for source in stats.get("datasets_by_source", []):
                datasets_by_source[source] = datasets_by_source.get(source, 0) + 1

            datasets_by_language = {}
            for lang in stats.get("datasets_by_language", []):
                datasets_by_language[lang] = datasets_by_language.get(lang, 0) + 1

            datasets_by_status = {}
            for status in stats.get("datasets_by_status", []):
                datasets_by_status[status] = datasets_by_status.get(status, 0) + 1

            # Calculate average quality score
            quality_scores = [score for score in stats.get("quality_scores", []) if score is not None]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

            # Get processing queue length
            queue_length = await db.dataset_processing_jobs.count_documents({
                "status": {"$in": ["pending", "downloading", "processing"]}
            })

            return DatasetStats(
                total_datasets=stats.get("total_datasets", 0),
                datasets_by_source=datasets_by_source,
                datasets_by_language=datasets_by_language,
                datasets_by_status=datasets_by_status,
                total_files_integrated=stats.get("total_files_integrated", 0),
                total_size_gb=stats.get("total_size_gb", 0.0),
                total_audio_hours=stats.get("total_audio_hours", 0.0),
                average_quality_score=avg_quality,
                processing_queue_length=queue_length
            )

        except Exception as e:
            logger.error(f"Error getting dataset stats: {str(e)}")
            raise

    # Source-specific processing methods
    async def _process_common_voice_dataset(self, dataset: ExternalDataset) -> None:
        """Process Common Voice dataset."""
        try:
            logger.info(f"Processing Common Voice dataset: {dataset.name}")

            # Common Voice URLs are predictable
            language = dataset.language_code
            version = dataset.source_metadata.get("version", "11.0")

            download_url = f"https://voice-prod-bundler-ee1969a6ce8178826482b88e843c335139bd3fb4.s3.amazonaws.com/cv-corpus-{version}-2022-09-21/{language}.tar.gz"

            # Download the dataset
            download_path = await self._download_file(download_url, f"cv_{language}_{version}.tar.gz")

            # Extract and process
            await self._extract_and_process_common_voice(dataset, download_path)

            # Update dataset status
            await self._update_dataset_completed(dataset.id)

        except Exception as e:
            logger.error(f"Error processing Common Voice dataset: {str(e)}")
            await self._update_dataset_error(dataset.id, str(e))

    async def _process_openslr_dataset(self, dataset: ExternalDataset) -> None:
        """Process OpenSLR dataset."""
        try:
            logger.info(f"Processing OpenSLR dataset: {dataset.name}")

            if not dataset.source_url:
                raise ValueError("OpenSLR source URL is required")

            # Download the dataset
            filename = Path(dataset.source_url).name
            download_path = await self._download_file(dataset.source_url, filename)

            # Extract and process
            await self._extract_and_process_openslr(dataset, download_path)

            # Update dataset status
            await self._update_dataset_completed(dataset.id)

        except Exception as e:
            logger.error(f"Error processing OpenSLR dataset: {str(e)}")
            await self._update_dataset_error(dataset.id, str(e))

    async def _process_masakhane_dataset(self, dataset: ExternalDataset) -> None:
        """Process Masakhane dataset."""
        try:
            logger.info(f"Processing Masakhane dataset: {dataset.name}")

            # Masakhane datasets are typically on GitHub
            repo_url = dataset.source_metadata.get("repo_url")
            if not repo_url:
                raise ValueError("Masakhane repository URL is required")

            # Clone or download the repository
            await self._download_masakhane_repo(dataset, repo_url)

            # Process the specific dataset
            await self._process_masakhane_files(dataset)

            # Update dataset status
            await self._update_dataset_completed(dataset.id)

        except Exception as e:
            logger.error(f"Error processing Masakhane dataset: {str(e)}")
            await self._update_dataset_error(dataset.id, str(e))

    async def _process_custom_scrape_dataset(self, dataset: ExternalDataset) -> None:
        """Process custom scraped dataset."""
        try:
            logger.info(f"Processing custom scrape dataset: {dataset.name}")

            # Custom scraping logic based on source metadata
            scrape_config = dataset.source_metadata

            if scrape_config.get("type") == "web_scrape":
                await self._scrape_web_content(dataset, scrape_config)
            elif scrape_config.get("type") == "api_fetch":
                await self._fetch_api_content(dataset, scrape_config)
            else:
                raise ValueError("Unknown custom scrape type")

            # Update dataset status
            await self._update_dataset_completed(dataset.id)

        except Exception as e:
            logger.error(f"Error processing custom scrape dataset: {str(e)}")
            await self._update_dataset_error(dataset.id, str(e))

    # Helper methods
    async def _download_file(self, url: str, filename: str) -> Path:
        """Download a file from URL."""
        try:
            session = await self._get_session()
            file_path = self.download_path / filename

            logger.info(f"Downloading {url} to {file_path}")

            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to download: HTTP {response.status}")

                async with aiofiles.open(file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)

            logger.info(f"Download completed: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            raise

    async def _extract_and_process_common_voice(self, dataset: ExternalDataset, archive_path: Path) -> None:
        """Extract and process Common Voice archive."""
        try:
            extract_path = self.download_path / f"cv_{dataset.language_code}"
            extract_path.mkdir(exist_ok=True)

            # Extract tar.gz file
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(extract_path)

            # Find TSV files (train.tsv, dev.tsv, test.tsv)
            cv_dir = extract_path / f"cv-corpus-{dataset.source_metadata.get('version', '11.0')}-2022-09-21" / dataset.language_code

            if not cv_dir.exists():
                raise ValueError(f"Common Voice directory not found: {cv_dir}")

            # Process each split
            for split in ["train", "dev", "test"]:
                tsv_file = cv_dir / f"{split}.tsv"
                if tsv_file.exists():
                    await self._process_common_voice_split(dataset, tsv_file, cv_dir / "clips", split)

        except Exception as e:
            logger.error(f"Error extracting Common Voice: {str(e)}")
            raise

    async def _process_common_voice_split(
        self,
        dataset: ExternalDataset,
        tsv_file: Path,
        clips_dir: Path,
        split: str
    ) -> None:
        """Process a Common Voice split (train/dev/test)."""
        try:
            db = await self._get_db()
            processed_files = 0

            with open(tsv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')

                for row in reader:
                    try:
                        # Extract metadata
                        audio_file = clips_dir / row['path']
                        if not audio_file.exists():
                            continue

                        # Quality filtering
                        up_votes = int(row.get('up_votes', 0))
                        down_votes = int(row.get('down_votes', 0))

                        if up_votes < 2 or down_votes > 0:  # Basic quality filter
                            continue

                        # Create submission in our database
                        submission_doc = {
                            "_id": ObjectId(),
                            "contributor_id": dataset.created_by,
                            "language_code": dataset.language_code,
                            "type": "audio",
                            "tier": "tier-2-reviewed",  # Common Voice is pre-validated
                            "title": f"Common Voice - {row.get('sentence', '')[:50]}",
                            "description": f"From Common Voice {split} split",
                            "file_url": str(audio_file),
                            "metadata": {
                                "source": "common_voice",
                                "split": split,
                                "sentence": row.get('sentence', ''),
                                "client_id": row.get('client_id', ''),
                                "up_votes": up_votes,
                                "down_votes": down_votes,
                                "age": row.get('age', ''),
                                "gender": row.get('gender', ''),
                                "accent": row.get('accent', ''),
                                "locale": row.get('locale', ''),
                                "dataset_id": dataset.id
                            },
                            "quality_scores": {
                                "overall": 0.8,  # Default for Common Voice
                                "audio_quality": 0.8,
                                "transcription_quality": 0.9
                            },
                            "validation_status": "validated",
                            "validations": [],
                            "status": "validated",
                            "created_at": datetime.utcnow(),
                            "external_dataset_id": dataset.id
                        }

                        await db.submissions.insert_one(submission_doc)
                        processed_files += 1

                        # Update progress periodically
                        if processed_files % 100 == 0:
                            await self._update_dataset_progress(dataset.id, f"Processed {processed_files} files from {split}")

                    except Exception as e:
                        logger.warning(f"Error processing Common Voice file {row.get('path', 'unknown')}: {str(e)}")
                        continue

            logger.info(f"Processed {processed_files} files from Common Voice {split} split")

        except Exception as e:
            logger.error(f"Error processing Common Voice split: {str(e)}")
            raise

    async def _create_processing_jobs(self, dataset_id: str) -> List[DatasetProcessingJob]:
        """Create processing jobs for a dataset."""
        try:
            db = await self._get_db()

            # Create download job
            download_job_doc = {
                "_id": ObjectId(),
                "dataset_id": dataset_id,
                "job_type": "download",
                "status": ProcessingStatus.PENDING,
                "config": {},
                "dependencies": [],
                "started_at": None,
                "completed_at": None,
                "progress_percentage": 0.0,
                "current_step": None,
                "result_data": {},
                "error_message": None,
                "logs": [],
                "cpu_time_seconds": None,
                "memory_peak_mb": None,
                "disk_usage_mb": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            await db.dataset_processing_jobs.insert_one(download_job_doc)

            # Create processing job
            process_job_doc = {
                "_id": ObjectId(),
                "dataset_id": dataset_id,
                "job_type": "process",
                "status": ProcessingStatus.PENDING,
                "config": {},
                "dependencies": [str(download_job_doc["_id"])],
                "started_at": None,
                "completed_at": None,
                "progress_percentage": 0.0,
                "current_step": None,
                "result_data": {},
                "error_message": None,
                "logs": [],
                "cpu_time_seconds": None,
                "memory_peak_mb": None,
                "disk_usage_mb": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            await db.dataset_processing_jobs.insert_one(process_job_doc)

            return [
                DatasetProcessingJob(**download_job_doc),
                DatasetProcessingJob(**process_job_doc)
            ]

        except Exception as e:
            logger.error(f"Error creating processing jobs: {str(e)}")
            raise

    async def _update_dataset_progress(self, dataset_id: str, message: str) -> None:
        """Update dataset processing progress."""
        try:
            db = await self._get_db()

            await db.external_datasets.update_one(
                {"_id": ObjectId(dataset_id)},
                {
                    "$push": {"processing_logs": f"{datetime.utcnow().isoformat()}: {message}"},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )

        except Exception as e:
            logger.error(f"Error updating dataset progress: {str(e)}")

    async def _update_dataset_completed(self, dataset_id: str) -> None:
        """Mark dataset processing as completed."""
        try:
            db = await self._get_db()

            await db.external_datasets.update_one(
                {"_id": ObjectId(dataset_id)},
                {
                    "$set": {
                        "processing_status": ProcessingStatus.COMPLETED,
                        "processing_completed_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )

        except Exception as e:
            logger.error(f"Error updating dataset completion: {str(e)}")

    async def _update_dataset_error(self, dataset_id: str, error_message: str) -> None:
        """Mark dataset processing as failed."""
        try:
            db = await self._get_db()

            await db.external_datasets.update_one(
                {"_id": ObjectId(dataset_id)},
                {
                    "$set": {
                        "processing_status": ProcessingStatus.FAILED,
                        "processing_error": error_message,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

        except Exception as e:
            logger.error(f"Error updating dataset error: {str(e)}")

    # Placeholder methods for additional integrations
    async def _extract_and_process_openslr(self, dataset: ExternalDataset, archive_path: Path) -> None:
        """Extract and process OpenSLR archive."""
        # Implementation would depend on specific OpenSLR resource format
        logger.info(f"OpenSLR processing not yet implemented for {dataset.name}")

    async def _download_masakhane_repo(self, dataset: ExternalDataset, repo_url: str) -> None:
        """Download Masakhane repository."""
        # Implementation would use git clone or GitHub API
        logger.info(f"Masakhane repo download not yet implemented for {repo_url}")

    async def _process_masakhane_files(self, dataset: ExternalDataset) -> None:
        """Process Masakhane dataset files."""
        # Implementation would process specific Masakhane dataset format
        logger.info(f"Masakhane processing not yet implemented for {dataset.name}")

    async def _scrape_web_content(self, dataset: ExternalDataset, config: Dict[str, Any]) -> None:
        """Scrape web content."""
        # Implementation would scrape websites based on configuration
        logger.info(f"Web scraping not yet implemented for {dataset.name}")

    async def _fetch_api_content(self, dataset: ExternalDataset, config: Dict[str, Any]) -> None:
        """Fetch content from APIs."""
        # Implementation would fetch from APIs based on configuration
        logger.info(f"API fetching not yet implemented for {dataset.name}")

    # Additional methods needed by API routes
    async def search_datasets(
        self,
        filters: Dict[str, Any],
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[ExternalDataset], int]:
        """Search datasets with filtering."""
        try:
            db = await self._get_db()

            # Get total count
            total_count = await db.external_datasets.count_documents(filters)

            # Get paginated results
            cursor = db.external_datasets.find(filters)
            cursor = cursor.sort("created_at", -1)
            cursor = cursor.skip((page - 1) * limit).limit(limit)

            datasets = []
            async for doc in cursor:
                # Convert ObjectId to string for Pydantic
                doc['_id'] = str(doc['_id'])
                datasets.append(ExternalDataset(**doc))

            return datasets, total_count

        except Exception as e:
            logger.error(f"Error searching datasets: {str(e)}")
            raise

    async def get_dataset_by_id(self, dataset_id: str) -> Optional[ExternalDataset]:
        """Get dataset by ID."""
        try:
            db = await self._get_db()

            doc = await db.external_datasets.find_one({"_id": ObjectId(dataset_id)})
            if doc:
                # Convert ObjectId to string for Pydantic
                doc['_id'] = str(doc['_id'])
                return ExternalDataset(**doc)
            return None

        except Exception as e:
            logger.error(f"Error getting dataset by ID: {str(e)}")
            raise

    async def pause_dataset_processing(self, dataset_id: str) -> bool:
        """Pause dataset processing."""
        try:
            db = await self._get_db()

            result = await db.external_datasets.update_one(
                {"_id": ObjectId(dataset_id)},
                {
                    "$set": {
                        "processing_status": ProcessingStatus.PAUSED,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Error pausing dataset processing: {str(e)}")
            return False

    async def delete_dataset(self, dataset_id: str) -> bool:
        """Delete a dataset."""
        try:
            db = await self._get_db()

            # Delete the dataset
            result = await db.external_datasets.delete_one({"_id": ObjectId(dataset_id)})

            # Delete associated jobs
            await db.dataset_processing_jobs.delete_many({"dataset_id": dataset_id})

            return result.deleted_count > 0

        except Exception as e:
            logger.error(f"Error deleting dataset: {str(e)}")
            return False

    async def get_dataset_jobs(self, dataset_id: str) -> List[DatasetProcessingJob]:
        """Get processing jobs for a dataset."""
        try:
            db = await self._get_db()

            cursor = db.dataset_processing_jobs.find({"dataset_id": dataset_id})
            cursor = cursor.sort("created_at", -1)

            jobs = []
            async for doc in cursor:
                jobs.append(DatasetProcessingJob(**doc))

            return jobs

        except Exception as e:
            logger.error(f"Error getting dataset jobs: {str(e)}")
            raise

    async def get_dataset_manifest(self, dataset_id: str) -> Optional[DatasetIntegrationManifest]:
        """Get dataset integration manifest."""
        try:
            db = await self._get_db()

            doc = await db.dataset_integration_manifests.find_one({"dataset_id": dataset_id})
            if doc:
                return DatasetIntegrationManifest(**doc)
            return None

        except Exception as e:
            logger.error(f"Error getting dataset manifest: {str(e)}")
            raise

    async def export_dataset_manifest(self, dataset_id: str) -> Optional[str]:
        """Export dataset manifest as JSON."""
        try:
            manifest = await self.get_dataset_manifest(dataset_id)
            if manifest:
                return json.dumps(manifest.dict(), indent=2, default=str)
            return None

        except Exception as e:
            logger.error(f"Error exporting dataset manifest: {str(e)}")
            return None

    async def get_dataset_statistics(self) -> DatasetStats:
        """Get dataset statistics."""
        return await self.get_dataset_stats()

    async def get_search_suggestions(self, search_term: str) -> List[str]:
        """Get search suggestions based on search term."""
        try:
            db = await self._get_db()

            # Simple suggestions based on existing data
            suggestions = []

            # Get language suggestions
            languages = await db.external_datasets.distinct("language_code")
            suggestions.extend([lang for lang in languages if search_term.lower() in lang.lower()])

            # Get source suggestions
            sources = await db.external_datasets.distinct("source")
            suggestions.extend([source for source in sources if search_term.lower() in source.lower()])

            return suggestions[:10]  # Limit to 10 suggestions

        except Exception as e:
            logger.error(f"Error getting search suggestions: {str(e)}")
            return []

    # Source-specific integration methods
    async def create_common_voice_integration(
        self,
        integration_data: CommonVoiceIntegration,
        created_by: str
    ) -> DatasetIntegrationResponse:
        """Create Common Voice integration."""
        try:
            # Create base dataset
            dataset_create = ExternalDatasetCreate(
                name=f"Common Voice {integration_data.cv_version} - {', '.join(integration_data.languages)}",
                source="common_voice",
                dataset_type="audio_speech",
                language_code=integration_data.languages[0] if integration_data.languages else "multi",
                license_type="cc0",
                source_metadata={
                    "version": integration_data.cv_version,
                    "languages": integration_data.languages,
                    "splits": integration_data.download_splits
                },
                auto_process=True
            )

            return await self.create_dataset_integration(dataset_create, created_by)

        except Exception as e:
            logger.error(f"Error creating Common Voice integration: {str(e)}")
            raise

    async def create_openslr_integration(
        self,
        integration_data: OpenSLRIntegration,
        created_by: str
    ) -> DatasetIntegrationResponse:
        """Create OpenSLR integration."""
        try:
            dataset_create = ExternalDatasetCreate(
                name=f"OpenSLR {integration_data.slr_resource_id} - {integration_data.language_name}",
                source="openslr",
                dataset_type="audio_speech",
                language_code=integration_data.language_code,
                license_type="cc_by",
                source_url=integration_data.resource_url,
                source_metadata={
                    "slr_resource_id": integration_data.slr_resource_id,
                    "language_name": integration_data.language_name,
                    "dialect_code": integration_data.dialect_code
                },
                auto_process=True
            )

            return await self.create_dataset_integration(dataset_create, created_by)

        except Exception as e:
            logger.error(f"Error creating OpenSLR integration: {str(e)}")
            raise

    async def create_masakhane_integration(
        self,
        integration_data: MasakhaneIntegration,
        created_by: str
    ) -> DatasetIntegrationResponse:
        """Create Masakhane integration."""
        try:
            dataset_create = ExternalDatasetCreate(
                name=f"Masakhane - {integration_data.dataset_name}",
                source="masakhane",
                dataset_type="text_corpus",
                language_code=integration_data.language_pairs[0].split('-')[0] if integration_data.language_pairs else "multi",
                license_type="cc_by",
                source_metadata={
                    "repo": integration_data.masakhane_repo,
                    "dataset_name": integration_data.dataset_name,
                    "task_type": integration_data.task_type,
                    "language_pairs": integration_data.language_pairs
                },
                auto_process=True
            )

            return await self.create_dataset_integration(dataset_create, created_by)

        except Exception as e:
            logger.error(f"Error creating Masakhane integration: {str(e)}")
            raise

    # Background processing methods
    async def process_common_voice_dataset(
        self,
        dataset_id: str,
        integration_data: CommonVoiceIntegration
    ) -> None:
        """Process Common Voice dataset in background."""
        try:
            dataset = await self.get_dataset_by_id(dataset_id)
            if dataset:
                await self._process_common_voice_dataset(dataset)
        except Exception as e:
            logger.error(f"Error in background Common Voice processing: {str(e)}")
            await self._update_dataset_error(dataset_id, str(e))

    async def process_openslr_dataset(
        self,
        dataset_id: str,
        integration_data: OpenSLRIntegration
    ) -> None:
        """Process OpenSLR dataset in background."""
        try:
            dataset = await self.get_dataset_by_id(dataset_id)
            if dataset:
                await self._process_openslr_dataset(dataset)
        except Exception as e:
            logger.error(f"Error in background OpenSLR processing: {str(e)}")
            await self._update_dataset_error(dataset_id, str(e))

    async def process_masakhane_dataset(
        self,
        dataset_id: str,
        integration_data: MasakhaneIntegration
    ) -> None:
        """Process Masakhane dataset in background."""
        try:
            dataset = await self.get_dataset_by_id(dataset_id)
            if dataset:
                await self._process_masakhane_dataset(dataset)
        except Exception as e:
            logger.error(f"Error in background Masakhane processing: {str(e)}")
            await self._update_dataset_error(dataset_id, str(e))

    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()