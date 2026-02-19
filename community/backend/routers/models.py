"""
ML Model Registry API Router

Handles CRUD operations for trained models with versioning,
multi-language support, and authenticated downloads.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional, List
from datetime import datetime, timedelta
import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from models.ml_models import (
    MLModel,
    MLModelCreate,
    MLModelUpdate,
    ModelSearchQuery,
    ModelListResponse,
    ModelVersion,
    ModelVersionCreate,
    ModelIssueCreate,
    ModelDownloadRequest,
    ModelDownloadResponse,
    ModelStats,
    KnownIssue,
    ModelType,
)
from database import get_database
from core.auth import get_current_user
from services.storage_service import HetznerStorageService
import os

router = APIRouter(prefix="/models", tags=["models"])


# ========================================
# Helper Functions
# ========================================

def serialize_model(model_doc: dict) -> dict:
    """Convert MongoDB document to API response format."""
    if model_doc:
        model_doc["id"] = str(model_doc["_id"])
        model_doc["_id"] = str(model_doc["_id"])
        # Convert ObjectId fields to strings
        if "created_by" in model_doc and isinstance(model_doc["created_by"], ObjectId):
            model_doc["created_by"] = str(model_doc["created_by"])
        if "contributors" in model_doc:
            model_doc["contributors"] = [str(c) if isinstance(c, ObjectId) else c for c in model_doc["contributors"]]
        if "language_ids" in model_doc:
            model_doc["language_ids"] = [str(l) if isinstance(l, ObjectId) else l for l in model_doc["language_ids"]]
        if "pipeline_id" in model_doc and model_doc["pipeline_id"]:
            if isinstance(model_doc["pipeline_id"], ObjectId):
                model_doc["pipeline_id"] = str(model_doc["pipeline_id"])
    return model_doc


async def get_language_ids(db: AsyncIOMotorDatabase, language_codes: List[str]) -> List[str]:
    """Get language ObjectIds from language codes."""
    languages = await db.languages.find({"code": {"$in": language_codes}}).to_list(length=100)
    return [str(lang["_id"]) for lang in languages]


# ========================================
# Model CRUD Operations
# ========================================

@router.post("", response_model=MLModel, status_code=status.HTTP_201_CREATED)
async def create_model(
    model_data: MLModelCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Register a new ML model in the registry.

    Args:
        model_data: Model creation data

    Returns:
        Created model document

    Raises:
        400: Invalid model data or duplicate model_uuid
        401: Not authenticated
    """
    # Generate unique model_uuid
    model_uuid = str(uuid.uuid4())

    # Get language ObjectIds
    language_ids = await get_language_ids(db, model_data.languages)

    # Prepare model document
    model_doc = {
        "model_uuid": model_uuid,
        "name": model_data.name,
        "model_type": model_data.model_type,
        "architecture": model_data.architecture,
        "version": model_data.version,
        "version_history": [],

        # Language support
        "languages": model_data.languages,
        "language_ids": language_ids,
        "primary_language": model_data.primary_language,
        "is_multilingual": model_data.is_multilingual,

        # Training references
        "pipeline_id": model_data.pipeline_id,
        "parent_model_id": model_data.parent_model_id,
        "base_model": model_data.base_model,

        # Storage
        "storage_path": model_data.storage_path,
        "checkpoint_path": model_data.checkpoint_path,
        "config_path": model_data.config_path,
        "model_size_mb": None,

        # Performance
        "performance_metrics": model_data.performance_metrics.dict() if model_data.performance_metrics else {},

        # Datasets
        "training_datasets": [ds.dict() for ds in model_data.training_datasets],
        "evaluation_datasets": [ds.dict() for ds in model_data.evaluation_datasets],

        # Deployment
        "deployment_status": model_data.deployment_status,
        "deployment_url": str(model_data.deployment_url) if model_data.deployment_url else None,
        "docker_image": model_data.docker_image,

        # Access & licensing
        "license": model_data.license,
        "is_public": model_data.is_public,
        "access_level": model_data.access_level,
        "download_count": 0,

        # Contributors
        "created_by": str(current_user["id"]),
        "contributors": [],

        # Known issues
        "known_issues": [],

        # Metadata
        "tags": model_data.tags,
        "description": model_data.description,
        "paper_url": str(model_data.paper_url) if model_data.paper_url else None,
        "demo_url": str(model_data.demo_url) if model_data.demo_url else None,

        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "published_at": datetime.utcnow() if model_data.is_public else None,
    }

    # Insert into database
    result = await db.ml_models.insert_one(model_doc)
    model_doc["_id"] = result.inserted_id

    # Update language collection with model reference
    await db.languages.update_many(
        {"code": {"$in": model_data.languages}},
        {
            "$addToSet": {"available_models": str(result.inserted_id)},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )

    return MLModel(**serialize_model(model_doc))


@router.get("", response_model=ModelListResponse)
async def list_models(
    query: Optional[str] = None,
    model_type: Optional[str] = None,
    architecture: Optional[str] = None,
    languages: Optional[List[str]] = Query(None),
    deployment_status: Optional[str] = None,
    is_public: Optional[bool] = None,
    min_performance: Optional[float] = None,
    tags: Optional[List[str]] = Query(None),
    sort_by: str = "updated_at",
    sort_order: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    List models with optional filtering and pagination.

    Query parameters:
        query: Search in name and description
        model_type: Filter by model type (tts, asr, llm, nmt, etc.)
        architecture: Filter by architecture
        languages: Filter by supported languages
        deployment_status: Filter by deployment status
        is_public: Filter public/private models
        min_performance: Minimum performance score
        tags: Filter by tags
        sort_by: Sort field (default: updated_at)
        sort_order: asc or desc
        page: Page number (default: 1)
        page_size: Items per page (default: 20, max: 100)

    Returns:
        Paginated list of models
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

    if architecture:
        filter_query["architecture"] = architecture

    if languages:
        filter_query["languages"] = {"$in": languages}

    if deployment_status:
        filter_query["deployment_status"] = deployment_status

    if is_public is not None:
        filter_query["is_public"] = is_public

    if tags:
        filter_query["tags"] = {"$in": tags}

    # TODO: Implement min_performance filter (requires complex query on metrics)

    # Count total
    total = await db.ml_models.count_documents(filter_query)

    # Calculate pagination
    skip = (page - 1) * page_size
    total_pages = (total + page_size - 1) // page_size

    # Sort
    sort_direction = -1 if sort_order == "desc" else 1

    # Query models
    cursor = db.ml_models.find(filter_query).sort(sort_by, sort_direction).skip(skip).limit(page_size)
    models = await cursor.to_list(length=page_size)

    # Serialize
    models = [MLModel(**serialize_model(m)) for m in models]

    return ModelListResponse(
        models=models,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/search", response_model=ModelListResponse)
async def search_models(
    search_query: ModelSearchQuery = Depends(),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Advanced model search with complex filtering.

    This is an alias for GET /models with better query structure.
    """
    return await list_models(
        query=search_query.query,
        model_type=search_query.model_type,
        architecture=search_query.architecture,
        languages=search_query.languages,
        deployment_status=search_query.deployment_status,
        is_public=search_query.is_public,
        min_performance=search_query.min_performance,
        tags=search_query.tags,
        sort_by=search_query.sort_by,
        sort_order=search_query.sort_order,
        page=search_query.page,
        page_size=search_query.page_size,
        db=db
    )


# ========================================
# Model Statistics (must be before /{model_uuid} to avoid route conflicts)
# ========================================

@router.get("/stats", response_model=ModelStats)
async def get_model_stats(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get aggregated statistics for all models.

    Returns:
        Model statistics
    """
    total_models = await db.ml_models.count_documents({})

    # Models by type
    type_pipeline = [
        {"$group": {"_id": "$model_type", "count": {"$sum": 1}}}
    ]
    models_by_type = {doc["_id"]: doc["count"] for doc in await db.ml_models.aggregate(type_pipeline).to_list(length=100)}

    # Models by language
    lang_pipeline = [
        {"$unwind": "$languages"},
        {"$group": {"_id": "$languages", "count": {"$sum": 1}}}
    ]
    models_by_language = {doc["_id"]: doc["count"] for doc in await db.ml_models.aggregate(lang_pipeline).to_list(length=100)}

    # Models by status
    status_pipeline = [
        {"$group": {"_id": "$deployment_status", "count": {"$sum": 1}}}
    ]
    models_by_status = {doc["_id"]: doc["count"] for doc in await db.ml_models.aggregate(status_pipeline).to_list(length=100)}

    # Total downloads
    download_pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$download_count"}}}
    ]
    total_downloads_result = await db.ml_models.aggregate(download_pipeline).to_list(length=1)
    total_downloads = total_downloads_result[0]["total"] if total_downloads_result else 0

    # Multilingual models
    multilingual_models = await db.ml_models.count_documents({"is_multilingual": True})

    return ModelStats(
        total_models=total_models,
        models_by_type=models_by_type,
        models_by_language=models_by_language,
        models_by_status=models_by_status,
        total_downloads=total_downloads,
        multilingual_models=multilingual_models,
        average_performance={}  # TODO: Calculate average performance metrics
    )


# ========================================
# Model CRUD Operations
# ========================================

@router.get("/{model_uuid}", response_model=MLModel)
async def get_model(
    model_uuid: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get detailed information about a specific model.

    Args:
        model_uuid: Unique model identifier

    Returns:
        Model details

    Raises:
        404: Model not found
    """
    model = await db.ml_models.find_one({"model_uuid": model_uuid})

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with UUID {model_uuid} not found"
        )

    # Increment view count (async, don't wait)
    await db.ml_models.update_one(
        {"model_uuid": model_uuid},
        {"$inc": {"view_count": 1}}
    )

    return MLModel(**serialize_model(model))


@router.put("/{model_uuid}", response_model=MLModel)
async def update_model(
    model_uuid: str,
    update_data: MLModelUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Update model information (not the model file itself).

    Args:
        model_uuid: Model identifier
        update_data: Fields to update

    Returns:
        Updated model

    Raises:
        404: Model not found
        403: Not authorized to update
    """
    # Find model
    model = await db.ml_models.find_one({"model_uuid": model_uuid})
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with UUID {model_uuid} not found"
        )

    # Check authorization (must be creator or contributor)
    user_id = str(current_user["id"])
    if str(model["created_by"]) != user_id and user_id not in [str(c) for c in model.get("contributors", [])]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this model"
        )

    # Build update document
    update_doc = {"updated_at": datetime.utcnow()}

    if update_data.name is not None:
        update_doc["name"] = update_data.name
    if update_data.description is not None:
        update_doc["description"] = update_data.description
    if update_data.tags is not None:
        update_doc["tags"] = update_data.tags
    if update_data.deployment_status is not None:
        update_doc["deployment_status"] = update_data.deployment_status
    if update_data.deployment_url is not None:
        update_doc["deployment_url"] = str(update_data.deployment_url)
    if update_data.docker_image is not None:
        update_doc["docker_image"] = update_data.docker_image
    if update_data.is_public is not None:
        update_doc["is_public"] = update_data.is_public
        if update_data.is_public and not model.get("published_at"):
            update_doc["published_at"] = datetime.utcnow()
    if update_data.access_level is not None:
        update_doc["access_level"] = update_data.access_level
    if update_data.performance_metrics is not None:
        update_doc["performance_metrics"] = update_data.performance_metrics.dict()
    if update_data.paper_url is not None:
        update_doc["paper_url"] = str(update_data.paper_url)
    if update_data.demo_url is not None:
        update_doc["demo_url"] = str(update_data.demo_url)

    # Update in database
    await db.ml_models.update_one(
        {"model_uuid": model_uuid},
        {"$set": update_doc}
    )

    # Fetch updated model
    updated_model = await db.ml_models.find_one({"model_uuid": model_uuid})

    return MLModel(**serialize_model(updated_model))


@router.delete("/{model_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_uuid: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a model (admin only).

    Args:
        model_uuid: Model identifier

    Raises:
        404: Model not found
        403: Not admin
    """
    result = await db.ml_models.delete_one({"model_uuid": model_uuid})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with UUID {model_uuid} not found"
        )

    # Remove from language references
    await db.languages.update_many(
        {},
        {"$pull": {"available_models": model_uuid}}
    )


# ========================================
# Model Versions
# ========================================

@router.post("/{model_uuid}/versions", response_model=MLModel, status_code=status.HTTP_201_CREATED)
async def create_model_version(
    model_uuid: str,
    version_data: ModelVersionCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new version of an existing model.

    Args:
        model_uuid: Model identifier
        version_data: New version data

    Returns:
        Updated model with new version in history

    Raises:
        404: Model not found
        400: Version already exists
        403: Not authorized
    """
    # Find model
    model = await db.ml_models.find_one({"model_uuid": model_uuid})
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with UUID {model_uuid} not found"
        )

    # Check authorization
    user_id = str(current_user["id"])
    if str(model["created_by"]) != user_id and user_id not in [str(c) for c in model.get("contributors", [])]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create versions for this model"
        )

    # Check if version already exists
    existing_versions = model.get("version_history", [])
    if any(v["version"] == version_data.version for v in existing_versions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Version {version_data.version} already exists"
        )

    # Create new version entry
    new_version = {
        "version": version_data.version,
        "released_at": datetime.utcnow(),
        "changelog": version_data.changelog,
        "storage_path": version_data.storage_path,
        "performance_metrics": version_data.performance_metrics.dict() if version_data.performance_metrics else {},
        "model_size_mb": version_data.model_size_mb,
        "is_stable": version_data.is_stable,
        "is_deprecated": False,
        "deprecation_reason": None,
    }

    # Add current version to history before updating
    current_version_entry = {
        "version": model["version"],
        "released_at": model.get("created_at", datetime.utcnow()),
        "changelog": f"Version {model['version']}",
        "storage_path": model["storage_path"],
        "performance_metrics": model.get("performance_metrics", {}),
        "model_size_mb": model.get("model_size_mb"),
        "is_stable": True,
        "is_deprecated": False,
    }

    # Update model with new version
    update_doc = {
        "version": version_data.version,
        "storage_path": version_data.storage_path,
        "checkpoint_path": version_data.checkpoint_path,
        "config_path": version_data.config_path,
        "model_size_mb": version_data.model_size_mb,
        "performance_metrics": version_data.performance_metrics.dict() if version_data.performance_metrics else {},
        "updated_at": datetime.utcnow(),
    }

    await db.ml_models.update_one(
        {"model_uuid": model_uuid},
        {
            "$set": update_doc,
            "$push": {"version_history": current_version_entry}
        }
    )

    # Fetch updated model
    updated_model = await db.ml_models.find_one({"model_uuid": model_uuid})

    return MLModel(**serialize_model(updated_model))


@router.get("/{model_uuid}/versions", response_model=List[ModelVersion])
async def get_model_versions(
    model_uuid: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get all versions of a model.

    Args:
        model_uuid: Model identifier

    Returns:
        List of model versions sorted by release date (newest first)

    Raises:
        404: Model not found
    """
    model = await db.ml_models.find_one({"model_uuid": model_uuid})
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with UUID {model_uuid} not found"
        )

    # Return version history sorted by release date (newest first)
    version_history = model.get("version_history", [])

    # Add current version to the list if not already in history
    versions = []
    for v in version_history:
        versions.append(ModelVersion(**v))

    # Sort by released_at descending
    versions.sort(key=lambda x: x.released_at, reverse=True)

    return versions


@router.get("/{model_uuid}/versions/{version_number}")
async def get_model_version_details(
    model_uuid: str,
    version_number: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get detailed information about a specific model version.

    Args:
        model_uuid: Model identifier
        version_number: Version string (e.g., "1.0.0")

    Returns:
        Model version details with additional metadata

    Raises:
        404: Model or version not found
    """
    model = await db.ml_models.find_one({"model_uuid": model_uuid})
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with UUID {model_uuid} not found"
        )

    # Check if this is the current version
    if model["version"] == version_number:
        return {
            "version_number": model["version"],
            "released_at": model.get("created_at", datetime.utcnow()),
            "changelog": f"Current version: {model['version']}",
            "storage_path": model.get("storage_path"),
            "performance_metrics": model.get("performance_metrics", {}),
            "model_size_mb": model.get("model_size_mb"),
            "is_stable": True,
            "is_deprecated": False,
            "author_name": model.get("created_by_name", "Unknown"),
            "created_at": model.get("created_at", datetime.utcnow())
        }

    # Search in version history
    version_history = model.get("version_history", [])
    for v in version_history:
        if v.get("version") == version_number:
            return {
                "version_number": v["version"],
                "released_at": v.get("released_at", datetime.utcnow()),
                "changelog": v.get("changelog", ""),
                "storage_path": v.get("storage_path"),
                "performance_metrics": v.get("performance_metrics", {}),
                "model_size_mb": v.get("model_size_mb"),
                "is_stable": v.get("is_stable", True),
                "is_deprecated": v.get("is_deprecated", False),
                "deprecation_reason": v.get("deprecation_reason"),
                "author_name": model.get("created_by_name", "Unknown"),
                "created_at": v.get("released_at", datetime.utcnow())
            }

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Version {version_number} not found for model {model_uuid}"
    )


@router.get("/{model_uuid}/versions/compare")
async def compare_model_versions(
    model_uuid: str,
    v1: str,
    v2: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Compare two versions of a model.

    Args:
        model_uuid: Model identifier
        v1: First version number
        v2: Second version number

    Returns:
        Comparison data showing differences in performance metrics

    Raises:
        404: Model or versions not found
    """
    model = await db.ml_models.find_one({"model_uuid": model_uuid})
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with UUID {model_uuid} not found"
        )

    # Helper function to get version data
    def get_version_data(version_num: str):
        if model["version"] == version_num:
            return {
                "version": model["version"],
                "released_at": model.get("created_at"),
                "performance_metrics": model.get("performance_metrics", {}),
                "model_size_mb": model.get("model_size_mb")
            }

        for v in model.get("version_history", []):
            if v.get("version") == version_num:
                return {
                    "version": v["version"],
                    "released_at": v.get("released_at"),
                    "performance_metrics": v.get("performance_metrics", {}),
                    "model_size_mb": v.get("model_size_mb")
                }
        return None

    version1_data = get_version_data(v1)
    version2_data = get_version_data(v2)

    if not version1_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {v1} not found"
        )

    if not version2_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {v2} not found"
        )

    # Compare performance metrics
    metrics_comparison = {}
    all_metrics = set(version1_data["performance_metrics"].keys()) | set(version2_data["performance_metrics"].keys())

    for metric in all_metrics:
        val1 = version1_data["performance_metrics"].get(metric)
        val2 = version2_data["performance_metrics"].get(metric)

        if val1 is not None and val2 is not None:
            difference = val2 - val1
            metrics_comparison[metric] = {
                "v1": val1,
                "v2": val2,
                "difference": difference,
                "improvement": difference > 0
            }
        elif val1 is not None:
            metrics_comparison[metric] = {
                "v1": val1,
                "v2": None,
                "difference": None,
                "improvement": None
            }
        else:
            metrics_comparison[metric] = {
                "v1": None,
                "v2": val2,
                "difference": None,
                "improvement": None
            }

    return {
        "model_uuid": model_uuid,
        "model_name": model["name"],
        "version1": v1,
        "version2": v2,
        "metrics_comparison": metrics_comparison,
        "size_comparison": {
            "v1_mb": version1_data.get("model_size_mb"),
            "v2_mb": version2_data.get("model_size_mb")
        },
        "summary": f"Comparing {v1} vs {v2}: {len([m for m in metrics_comparison.values() if m.get('improvement')])} metrics improved"
    }


# ========================================
# Model Downloads
# ========================================

@router.get("/{model_uuid}/download", response_model=ModelDownloadResponse)
async def get_model_download_url(
    model_uuid: str,
    version: Optional[str] = None,
    include_config: bool = True,
    include_checksum: bool = True,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Get authenticated download URL for model files.

    Args:
        model_uuid: Model identifier
        version: Specific version (default: latest)
        include_config: Include config file URL
        include_checksum: Include checksum file

    Returns:
        Download URLs with expiration

    Raises:
        404: Model not found
        403: Not authorized to download
    """
    # Find model
    model = await db.ml_models.find_one({"model_uuid": model_uuid})
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with UUID {model_uuid} not found"
        )

    # Check access level
    if model["access_level"] == "private" and str(model["created_by"]) != str(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This model is private"
        )

    # Get storage service
    storage = HetznerStorageService(
        host=os.getenv("HETZNER_STORAGE_HOST"),
        username=os.getenv("HETZNER_STORAGE_USERNAME"),
        password=os.getenv("HETZNER_STORAGE_PASSWORD"),
        port=int(os.getenv("HETZNER_STORAGE_PORT", "23")),
    )

    # Determine version to download
    if version:
        # Find specific version
        version_entry = next((v for v in model.get("version_history", []) if v["version"] == version), None)
        if not version_entry:
            # Check if it's the current version
            if model["version"] != version:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Version {version} not found"
                )
            version_entry = {
                "version": model["version"],
                "storage_path": model["storage_path"],
                "model_size_mb": model.get("model_size_mb"),
            }
    else:
        # Use current version
        version = model["version"]
        version_entry = {
            "version": model["version"],
            "storage_path": model["storage_path"],
            "model_size_mb": model.get("model_size_mb"),
        }

    # Generate presigned URLs
    expiry_hours = 1
    checkpoint_path = f"{version_entry['storage_path']}/final/checkpoint.pt"
    download_url = storage.generate_download_url(checkpoint_path, expiry_hours=expiry_hours)

    config_url = None
    if include_config and model.get("config_path"):
        config_url = storage.generate_download_url(model["config_path"], expiry_hours=expiry_hours)

    # TODO: Implement checksum retrieval

    # Increment download count (async)
    await db.ml_models.update_one(
        {"model_uuid": model_uuid},
        {"$inc": {"download_count": 1}}
    )

    return ModelDownloadResponse(
        model_uuid=model_uuid,
        version=version,
        download_url=download_url,
        config_url=config_url,
        checksum=None,  # TODO
        expires_at=datetime.utcnow() + timedelta(hours=expiry_hours),
        file_size_mb=version_entry.get("model_size_mb", 0.0)
    )


# ========================================
# Model Issues
# ========================================

@router.post("/{model_uuid}/issues", status_code=status.HTTP_201_CREATED)
async def report_model_issue(
    model_uuid: str,
    issue_data: ModelIssueCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Report a known issue with a model.

    Args:
        model_uuid: Model identifier
        issue_data: Issue details

    Returns:
        Success message

    Raises:
        404: Model not found
    """
    # Find model
    model = await db.ml_models.find_one({"model_uuid": model_uuid})
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with UUID {model_uuid} not found"
        )

    # Create issue entry
    issue = {
        "issue": issue_data.issue,
        "severity": issue_data.severity,
        "reported_by": str(current_user["id"]),
        "reported_at": datetime.utcnow(),
        "workaround": issue_data.workaround,
        "is_resolved": False,
    }

    # Add to model
    await db.ml_models.update_one(
        {"model_uuid": model_uuid},
        {"$push": {"known_issues": issue}}
    )

    return {"message": "Issue reported successfully", "issue": issue}


