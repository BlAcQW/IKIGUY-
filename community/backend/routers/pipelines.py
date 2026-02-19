"""
Training Pipeline API Router

Handles MLOps pipeline tracking with stage-by-stage progress,
metrics, artifacts, and real-time updates.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional, List
from datetime import datetime
import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from models.training_pipeline_models import (
    TrainingPipeline,
    TrainingPipelineCreate,
    TrainingPipelineUpdate,
    PipelineSearchQuery,
    PipelineListResponse,
    StageUpdate,
    PipelineArtifactUpload,
    PipelineMetricsUpdate,
    PipelineStageProgress,
    PipelineStats,
    CheckpointCreate,
    PipelineCompletion,
    PipelineStage,
    StageStatus,
)
from database import get_database
from core.auth import get_current_user

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


# ========================================
# Helper Functions
# ========================================

def serialize_pipeline(pipeline_doc: dict) -> dict:
    """Convert MongoDB document to API response format."""
    if pipeline_doc:
        pipeline_doc["id"] = str(pipeline_doc["_id"])
        pipeline_doc["_id"] = str(pipeline_doc["_id"])
        # Convert ObjectId fields
        if "created_by" in pipeline_doc and isinstance(pipeline_doc["created_by"], ObjectId):
            pipeline_doc["created_by"] = str(pipeline_doc["created_by"])
        if "team_members" in pipeline_doc:
            pipeline_doc["team_members"] = [str(t) if isinstance(t, ObjectId) else t for t in pipeline_doc["team_members"]]
        if "result_model_id" in pipeline_doc and pipeline_doc["result_model_id"]:
            if isinstance(pipeline_doc["result_model_id"], ObjectId):
                pipeline_doc["result_model_id"] = str(pipeline_doc["result_model_id"])
    return pipeline_doc


def calculate_overall_progress(stages: List[dict], current_stage: str) -> float:
    """
    Calculate overall pipeline progress based on stages.

    Returns progress percentage (0-100).
    """
    if not stages:
        return 0.0

    stage_order = ["data_acquisition", "preprocessing", "training", "evaluation", "deployment"]
    stage_weights = {
        "data_acquisition": 15,
        "preprocessing": 20,
        "training": 40,
        "evaluation": 15,
        "deployment": 10,
    }

    total_progress = 0.0
    for stage in stages:
        stage_name = stage["stage_name"]
        weight = stage_weights.get(stage_name, 20)

        if stage["status"] == "completed":
            total_progress += weight
        elif stage["status"] == "in_progress":
            # Use stage progress if available
            stage_progress = stage.get("progress_percentage", 50)
            total_progress += (weight * stage_progress / 100)

    return min(total_progress, 100.0)


# ========================================
# Pipeline CRUD Operations
# ========================================

@router.post("", response_model=TrainingPipeline, status_code=status.HTTP_201_CREATED)
async def create_pipeline(
    pipeline_data: TrainingPipelineCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new training pipeline.

    Args:
        pipeline_data: Pipeline creation data

    Returns:
        Created pipeline document

    Raises:
        400: Invalid pipeline data
        401: Not authenticated
    """
    # Generate unique pipeline_uuid
    pipeline_uuid = str(uuid.uuid4())

    # Initialize stages
    all_stages = ["data_acquisition", "preprocessing", "training", "evaluation", "deployment"]
    stages = []
    for stage_name in all_stages:
        stage = {
            "stage_name": stage_name,
            "status": "in_progress" if stage_name == pipeline_data.current_stage else "pending",
            "started_at": datetime.utcnow() if stage_name == pipeline_data.current_stage else None,
            "completed_at": None,
            "duration_minutes": None,
            "preprocessing_details": None,
            "training_config": None,
            "evaluation_plan": None,
            "artifacts": [],
            "metrics": {},
            "checkpoints": [],
            "notes": None,
            "logs": [],
            "error_message": None,
            "responsible_user": None,
            "resource_usage": None,
        }
        stages.append(stage)

    # Prepare pipeline document
    pipeline_doc = {
        "pipeline_uuid": pipeline_uuid,
        "name": pipeline_data.name,
        "model_type": pipeline_data.model_type,
        "current_stage": pipeline_data.current_stage,
        "stage_progress": 0.0,
        "stages": stages,
        "target_version": pipeline_data.target_version,
        "result_model_id": None,
        "datasets": [ds.dict() for ds in pipeline_data.datasets],
        "experiment_config": pipeline_data.experiment_config.dict() if pipeline_data.experiment_config else None,
        "team_members": [str(t) for t in pipeline_data.team_members],
        "created_by": str(current_user["id"]),
        "is_active": True,
        "priority": pipeline_data.priority,
        "description": pipeline_data.description,
        "tags": pipeline_data.tags,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "completed_at": None,
    }

    # Insert into database
    result = await db.ml_training_pipelines.insert_one(pipeline_doc)
    pipeline_doc["_id"] = result.inserted_id

    return TrainingPipeline(**serialize_pipeline(pipeline_doc))


@router.get("", response_model=PipelineListResponse)
async def list_pipelines(
    query: Optional[str] = None,
    model_type: Optional[str] = None,
    current_stage: Optional[str] = None,
    is_active: Optional[bool] = None,
    priority: Optional[str] = None,
    created_by: Optional[str] = None,
    sort_by: str = "updated_at",
    sort_order: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    List training pipelines with filtering and pagination.

    Query parameters:
        query: Search in name and description
        model_type: Filter by model type
        current_stage: Filter by current stage
        is_active: Filter active/inactive pipelines
        priority: Filter by priority
        created_by: Filter by creator
        sort_by: Sort field
        sort_order: asc or desc
        page: Page number
        page_size: Items per page

    Returns:
        Paginated list of pipelines
    """
    # Build filter query
    filter_query = {}

    if query:
        filter_query["$or"] = [
            {"name": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}},
        ]

    if model_type:
        filter_query["model_type"] = model_type

    if current_stage:
        filter_query["current_stage"] = current_stage

    if is_active is not None:
        filter_query["is_active"] = is_active

    if priority:
        filter_query["priority"] = priority

    if created_by:
        filter_query["created_by"] = created_by

    # Count total
    total = await db.ml_training_pipelines.count_documents(filter_query)

    # Calculate pagination
    skip = (page - 1) * page_size
    total_pages = (total + page_size - 1) // page_size

    # Sort
    sort_direction = -1 if sort_order == "desc" else 1

    # Query pipelines
    cursor = db.ml_training_pipelines.find(filter_query).sort(sort_by, sort_direction).skip(skip).limit(page_size)
    pipelines = await cursor.to_list(length=page_size)

    # Serialize
    pipelines = [TrainingPipeline(**serialize_pipeline(p)) for p in pipelines]

    return PipelineListResponse(
        pipelines=pipelines,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


# ========================================
# Statistics (must be before /{pipeline_id} to avoid route conflicts)
# ========================================

@router.get("/stats", response_model=PipelineStats)
async def get_pipeline_stats(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get aggregated statistics for all pipelines.

    Returns:
        Pipeline statistics
    """
    total_pipelines = await db.ml_training_pipelines.count_documents({})
    active_pipelines = await db.ml_training_pipelines.count_documents({"is_active": True})
    completed_pipelines = await db.ml_training_pipelines.count_documents({"completed_at": {"$ne": None}})

    # Failed pipelines (have error messages in any stage)
    failed_pipeline_query = {"stages.error_message": {"$ne": None, "$exists": True}}
    failed_pipelines = await db.ml_training_pipelines.count_documents(failed_pipeline_query)

    # Pipelines by stage
    stage_pipeline = [
        {"$group": {"_id": "$current_stage", "count": {"$sum": 1}}}
    ]
    pipelines_by_stage = {doc["_id"]: doc["count"] for doc in await db.ml_training_pipelines.aggregate(stage_pipeline).to_list(length=100)}

    # Pipelines by type
    type_pipeline = [
        {"$group": {"_id": "$model_type", "count": {"$sum": 1}}}
    ]
    pipelines_by_type = {doc["_id"]: doc["count"] for doc in await db.ml_training_pipelines.aggregate(type_pipeline).to_list(length=100)}

    # Average duration for completed pipelines
    duration_pipeline = [
        {"$match": {"completed_at": {"$ne": None}}},
        {
            "$project": {
                "duration_days": {
                    "$divide": [
                        {"$subtract": ["$completed_at", "$created_at"]},
                        1000 * 60 * 60 * 24  # Convert ms to days
                    ]
                }
            }
        },
        {"$group": {"_id": None, "avg": {"$avg": "$duration_days"}}}
    ]
    avg_duration_result = await db.ml_training_pipelines.aggregate(duration_pipeline).to_list(length=1)
    average_duration_days = avg_duration_result[0]["avg"] if avg_duration_result else None

    return PipelineStats(
        total_pipelines=total_pipelines,
        active_pipelines=active_pipelines,
        completed_pipelines=completed_pipelines,
        failed_pipelines=failed_pipelines,
        pipelines_by_stage=pipelines_by_stage,
        pipelines_by_type=pipelines_by_type,
        average_duration_days=average_duration_days
    )


# ========================================
# Pipeline CRUD
# ========================================

@router.get("/{pipeline_id}", response_model=TrainingPipeline)
async def get_pipeline(
    pipeline_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get detailed information about a specific pipeline.

    Args:
        pipeline_id: Pipeline ObjectId or UUID

    Returns:
        Pipeline details

    Raises:
        404: Pipeline not found
    """
    # Try to find by UUID first, then by ObjectId
    pipeline = await db.ml_training_pipelines.find_one({"pipeline_uuid": pipeline_id})
    if not pipeline and ObjectId.is_valid(pipeline_id):
        pipeline = await db.ml_training_pipelines.find_one({"_id": ObjectId(pipeline_id)})

    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline with ID {pipeline_id} not found"
        )

    return TrainingPipeline(**serialize_pipeline(pipeline))


@router.put("/{pipeline_id}", response_model=TrainingPipeline)
async def update_pipeline(
    pipeline_id: str,
    update_data: TrainingPipelineUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Update pipeline metadata.

    Args:
        pipeline_id: Pipeline identifier
        update_data: Fields to update

    Returns:
        Updated pipeline

    Raises:
        404: Pipeline not found
        403: Not authorized
    """
    # Find pipeline
    pipeline = await db.ml_training_pipelines.find_one({"pipeline_uuid": pipeline_id})
    if not pipeline and ObjectId.is_valid(pipeline_id):
        pipeline = await db.ml_training_pipelines.find_one({"_id": ObjectId(pipeline_id)})

    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline with ID {pipeline_id} not found"
        )

    # Check authorization
    user_id = str(current_user["id"])
    if str(pipeline["created_by"]) != user_id and user_id not in [str(t) for t in pipeline.get("team_members", [])]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this pipeline"
        )

    # Build update document
    update_doc = {"updated_at": datetime.utcnow()}

    if update_data.name is not None:
        update_doc["name"] = update_data.name
    if update_data.current_stage is not None:
        update_doc["current_stage"] = update_data.current_stage
    if update_data.stage_progress is not None:
        update_doc["stage_progress"] = update_data.stage_progress
    if update_data.priority is not None:
        update_doc["priority"] = update_data.priority
    if update_data.is_active is not None:
        update_doc["is_active"] = update_data.is_active
    if update_data.description is not None:
        update_doc["description"] = update_data.description
    if update_data.tags is not None:
        update_doc["tags"] = update_data.tags

    # Update in database
    await db.ml_training_pipelines.update_one(
        {"_id": pipeline["_id"]},
        {"$set": update_doc}
    )

    # Fetch updated pipeline
    updated_pipeline = await db.ml_training_pipelines.find_one({"_id": pipeline["_id"]})

    return TrainingPipeline(**serialize_pipeline(updated_pipeline))


# ========================================
# Stage Management
# ========================================

@router.put("/{pipeline_id}/stages/{stage_name}", response_model=TrainingPipeline)
async def update_pipeline_stage(
    pipeline_id: str,
    stage_name: str,
    stage_update: StageUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a specific pipeline stage.

    Args:
        pipeline_id: Pipeline identifier
        stage_name: Stage name (data_acquisition, preprocessing, etc.)
        stage_update: Stage update data

    Returns:
        Updated pipeline

    Raises:
        404: Pipeline or stage not found
        403: Not authorized
    """
    # Find pipeline
    pipeline = await db.ml_training_pipelines.find_one({"pipeline_uuid": pipeline_id})
    if not pipeline and ObjectId.is_valid(pipeline_id):
        pipeline = await db.ml_training_pipelines.find_one({"_id": ObjectId(pipeline_id)})

    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline with ID {pipeline_id} not found"
        )

    # Check authorization
    user_id = str(current_user["id"])
    if str(pipeline["created_by"]) != user_id and user_id not in [str(t) for t in pipeline.get("team_members", [])]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this pipeline"
        )

    # Find stage in stages array
    stages = pipeline.get("stages", [])
    stage_index = next((i for i, s in enumerate(stages) if s["stage_name"] == stage_name), None)

    if stage_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stage {stage_name} not found in pipeline"
        )

    # Update stage
    stage = stages[stage_index]
    stage["status"] = stage_update.status
    stage["updated_at"] = datetime.utcnow()

    if stage_update.status == "in_progress" and not stage.get("started_at"):
        stage["started_at"] = datetime.utcnow()

    if stage_update.status == "completed" and not stage.get("completed_at"):
        stage["completed_at"] = datetime.utcnow()
        if stage.get("started_at"):
            duration = (stage["completed_at"] - stage["started_at"]).total_seconds() / 60
            stage["duration_minutes"] = int(duration)

    if stage_update.progress_percentage is not None:
        stage["progress_percentage"] = stage_update.progress_percentage

    if stage_update.metrics is not None:
        stage["metrics"].update(stage_update.metrics)

    if stage_update.notes is not None:
        stage["notes"] = stage_update.notes

    if stage_update.error_message is not None:
        stage["error_message"] = stage_update.error_message

    stages[stage_index] = stage

    # Calculate overall progress
    overall_progress = calculate_overall_progress(stages, pipeline["current_stage"])

    # Update pipeline
    await db.ml_training_pipelines.update_one(
        {"_id": pipeline["_id"]},
        {
            "$set": {
                "stages": stages,
                "stage_progress": overall_progress,
                "updated_at": datetime.utcnow()
            }
        }
    )

    # Fetch updated pipeline
    updated_pipeline = await db.ml_training_pipelines.find_one({"_id": pipeline["_id"]})

    return TrainingPipeline(**serialize_pipeline(updated_pipeline))


# ========================================
# Artifacts & Metrics
# ========================================

@router.post("/{pipeline_id}/artifacts", status_code=status.HTTP_201_CREATED)
async def upload_pipeline_artifact(
    pipeline_id: str,
    artifact: PipelineArtifactUpload,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Register an artifact for a pipeline stage.

    Args:
        pipeline_id: Pipeline identifier
        artifact: Artifact metadata

    Returns:
        Success message

    Raises:
        404: Pipeline not found
        403: Not authorized
    """
    # Find pipeline
    pipeline = await db.ml_training_pipelines.find_one({"pipeline_uuid": pipeline_id})
    if not pipeline and ObjectId.is_valid(pipeline_id):
        pipeline = await db.ml_training_pipelines.find_one({"_id": ObjectId(pipeline_id)})

    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline with ID {pipeline_id} not found"
        )

    # Check authorization
    user_id = str(current_user["id"])
    if str(pipeline["created_by"]) != user_id and user_id not in [str(t) for t in pipeline.get("team_members", [])]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add artifacts to this pipeline"
        )

    # Find stage
    stages = pipeline.get("stages", [])
    stage_index = next((i for i, s in enumerate(stages) if s["stage_name"] == artifact.stage_name), None)

    if stage_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stage {artifact.stage_name} not found"
        )

    # Add artifact to stage
    artifact_doc = {
        "name": artifact.artifact_name,
        "path": artifact.file_path,
        "artifact_type": artifact.artifact_type,
        "description": artifact.description,
        "metadata": artifact.metadata,
        "created_at": datetime.utcnow(),
    }

    stages[stage_index]["artifacts"].append(artifact_doc)

    # Update pipeline
    await db.ml_training_pipelines.update_one(
        {"_id": pipeline["_id"]},
        {
            "$set": {
                "stages": stages,
                "updated_at": datetime.utcnow()
            }
        }
    )

    return {"message": "Artifact added successfully", "artifact": artifact_doc}


@router.get("/{pipeline_id}/metrics")
async def get_pipeline_metrics(
    pipeline_id: str,
    stage_name: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get metrics for a pipeline or specific stage.

    Args:
        pipeline_id: Pipeline identifier
        stage_name: Optional stage name filter

    Returns:
        Metrics dictionary

    Raises:
        404: Pipeline not found
    """
    # Find pipeline
    pipeline = await db.ml_training_pipelines.find_one({"pipeline_uuid": pipeline_id})
    if not pipeline and ObjectId.is_valid(pipeline_id):
        pipeline = await db.ml_training_pipelines.find_one({"_id": ObjectId(pipeline_id)})

    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline with ID {pipeline_id} not found"
        )

    if stage_name:
        # Return metrics for specific stage
        stage = next((s for s in pipeline.get("stages", []) if s["stage_name"] == stage_name), None)
        if not stage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stage {stage_name} not found"
            )
        return {"stage": stage_name, "metrics": stage.get("metrics", {})}
    else:
        # Return metrics for all stages
        metrics = {}
        for stage in pipeline.get("stages", []):
            metrics[stage["stage_name"]] = stage.get("metrics", {})
        return {"metrics": metrics}


@router.post("/{pipeline_id}/complete", response_model=TrainingPipeline)
async def complete_pipeline(
    pipeline_id: str,
    completion_data: PipelineCompletion,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Mark pipeline as complete with final results.

    Args:
        pipeline_id: Pipeline identifier
        completion_data: Completion data including result model

    Returns:
        Updated pipeline

    Raises:
        404: Pipeline not found
        403: Not authorized
    """
    # Find pipeline
    pipeline = await db.ml_training_pipelines.find_one({"pipeline_uuid": pipeline_id})
    if not pipeline and ObjectId.is_valid(pipeline_id):
        pipeline = await db.ml_training_pipelines.find_one({"_id": ObjectId(pipeline_id)})

    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline with ID {pipeline_id} not found"
        )

    # Check authorization
    user_id = str(current_user["id"])
    if str(pipeline["created_by"]) != user_id and user_id not in [str(t) for t in pipeline.get("team_members", [])]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to complete this pipeline"
        )

    # Update pipeline
    update_doc = {
        "is_active": False,
        "completed_at": datetime.utcnow(),
        "result_model_id": completion_data.result_model_id,
        "current_stage": "deployment",
        "stage_progress": 100.0,
        "updated_at": datetime.utcnow(),
    }

    # Add completion notes to deployment stage
    stages = pipeline.get("stages", [])
    deployment_stage = next((s for s in stages if s["stage_name"] == "deployment"), None)
    if deployment_stage:
        deployment_stage["status"] = "completed" if completion_data.success else "failed"
        deployment_stage["completed_at"] = datetime.utcnow()
        deployment_stage["notes"] = completion_data.completion_notes
        deployment_stage["metrics"] = completion_data.final_metrics
        update_doc["stages"] = stages

    await db.ml_training_pipelines.update_one(
        {"_id": pipeline["_id"]},
        {"$set": update_doc}
    )

    # Fetch updated pipeline
    updated_pipeline = await db.ml_training_pipelines.find_one({"_id": pipeline["_id"]})

    return TrainingPipeline(**serialize_pipeline(updated_pipeline))


