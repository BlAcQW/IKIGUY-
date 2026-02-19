"""
Discovery Router for African Language Community Platform.

Language-based resource discovery with advanced filtering and recommendations.
"""

from typing import Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from database import get_database
from models.ml_models import MLModel
from models.resource_models import ResourceLink

router = APIRouter(prefix="/discovery", tags=["discovery"])


def serialize_document(doc: dict) -> dict:
    """
    Convert MongoDB ObjectIds to strings for API response.

    Args:
        doc (dict): MongoDB document

    Returns:
        dict: Serialized document
    """
    if doc:
        doc["id"] = str(doc["_id"])
        doc["_id"] = str(doc["_id"])

        # Handle ObjectId fields
        for field in ["created_by", "uploaded_by", "submitted_by", "verified_by"]:
            if field in doc and isinstance(doc[field], ObjectId):
                doc[field] = str(doc[field])

        # Handle ObjectId lists
        if "language_ids" in doc:
            doc["language_ids"] = [
                str(lid) if isinstance(lid, ObjectId) else lid
                for lid in doc.get("language_ids", [])
            ]

    return doc


# ============================================================================
# LANGUAGE-BASED DISCOVERY
# ============================================================================


@router.get("/languages/{language_code}")
async def discover_by_language(
    language_code: str,
    include_datasets: bool = Query(True, description="Include datasets"),
    include_models: bool = Query(True, description="Include models"),
    include_resources: bool = Query(True, description="Include external resources"),
    include_pipelines: bool = Query(False, description="Include training pipelines"),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Discover all resources available for a specific language.

    Returns a comprehensive view of datasets, models, external resources,
    and training pipelines for the specified language.

    Args:
        language_code: Language code (e.g., "twi", "yo")
        include_datasets: Include datasets
        include_models: Include models
        include_resources: Include external resources
        include_pipelines: Include training pipelines
        db: Database connection

    Returns:
        dict: Dictionary of resources by type
    """
    # Get language info
    language = await db.languages.find_one({"code": language_code})
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language {language_code} not found",
        )

    result = {
        "language": {
            "code": language["code"],
            "name": language["name"],
            "native_name": language.get("native_name"),
            "family": language.get("family"),
            "iso_639_3": language.get("iso_639_3"),
        },
        "statistics": {},
        "resources": {},
    }

    # Discover datasets
    if include_datasets:
        datasets_cursor = db.datasets.find({"languages": language_code}).sort(
            "created_at", -1
        )
        datasets = []
        async for doc in datasets_cursor:
            doc = serialize_document(doc)
            datasets.append(doc)

        result["resources"]["datasets"] = datasets
        result["statistics"]["total_datasets"] = len(datasets)

    # Discover models
    if include_models:
        models_cursor = db.ml_models.find({"languages": language_code}).sort(
            "created_at", -1
        )
        models = []
        async for doc in models_cursor:
            doc = serialize_document(doc)
            models.append(doc)

        result["resources"]["models"] = models
        result["statistics"]["total_models"] = len(models)

    # Discover external resources
    if include_resources:
        resources_cursor = db.external_resources.find({"languages": language_code}).sort(
            "created_at", -1
        )
        resources = []
        async for doc in resources_cursor:
            doc = serialize_document(doc)
            resources.append(doc)

        result["resources"]["external_resources"] = resources
        result["statistics"]["total_external_resources"] = len(resources)

    # Discover training pipelines
    if include_pipelines:
        pipelines_cursor = db.ml_training_pipelines.find(
            {"target_language": language_code}
        ).sort("created_at", -1)
        pipelines = []
        async for doc in pipelines_cursor:
            doc = serialize_document(doc)
            pipelines.append(doc)

        result["resources"]["training_pipelines"] = pipelines
        result["statistics"]["total_pipelines"] = len(pipelines)

    return result


@router.get("/languages/{language_code}/datasets")
async def discover_datasets_by_language(
    language_code: str,
    data_type: Optional[str] = Query(None, description="Filter by data type"),
    min_size_mb: Optional[float] = Query(None, description="Minimum size in MB"),
    max_size_mb: Optional[float] = Query(None, description="Maximum size in MB"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Discover datasets for a specific language with filtering.

    Args:
        language_code: Language code
        data_type: Filter by data type (text, audio, parallel, etc.)
        min_size_mb: Minimum dataset size in MB
        max_size_mb: Maximum dataset size in MB
        skip: Number of records to skip
        limit: Maximum records to return
        db: Database connection

    Returns:
        List[dict]: List of datasets
    """
    # Verify language exists
    language = await db.languages.find_one({"code": language_code})
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language {language_code} not found",
        )

    # Build query
    query = {"languages": language_code}

    if data_type:
        query["data_type"] = data_type

    if min_size_mb is not None or max_size_mb is not None:
        query["total_size_mb"] = {}
        if min_size_mb is not None:
            query["total_size_mb"]["$gte"] = min_size_mb
        if max_size_mb is not None:
            query["total_size_mb"]["$lte"] = max_size_mb

    # Query database
    cursor = db.datasets.find(query).sort("created_at", -1).skip(skip).limit(limit)

    datasets = []
    async for doc in cursor:
        doc = serialize_document(doc)
        datasets.append(doc)

    return {
        "language_code": language_code,
        "total": len(datasets),
        "datasets": datasets,
    }


@router.get("/languages/{language_code}/models")
async def discover_models_by_language(
    language_code: str,
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    architecture: Optional[str] = Query(None, description="Filter by architecture"),
    min_download_count: Optional[int] = Query(None, description="Minimum downloads"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Discover models for a specific language with filtering.

    Args:
        language_code: Language code
        model_type: Filter by model type (tts, asr, llm, etc.)
        architecture: Filter by architecture
        min_download_count: Minimum download count
        skip: Number of records to skip
        limit: Maximum records to return
        db: Database connection

    Returns:
        dict: Dictionary with models list and metadata
    """
    # Verify language exists
    language = await db.languages.find_one({"code": language_code})
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language {language_code} not found",
        )

    # Build query
    query = {"languages": language_code}

    if model_type:
        query["model_type"] = model_type

    if architecture:
        query["architecture"] = architecture

    if min_download_count is not None:
        query["download_count"] = {"$gte": min_download_count}

    # Query database
    cursor = db.ml_models.find(query).sort("download_count", -1).skip(skip).limit(limit)

    models = []
    async for doc in cursor:
        doc = serialize_document(doc)
        models.append(doc)

    return {
        "language_code": language_code,
        "total": len(models),
        "models": models,
    }


@router.get("/languages/{language_code}/resources")
async def discover_external_resources_by_language(
    language_code: str,
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    verified_only: bool = Query(False, description="Show only verified resources"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Discover external resources for a specific language.

    Args:
        language_code: Language code
        resource_type: Filter by resource type
        platform: Filter by platform
        verified_only: Show only verified resources
        skip: Number of records to skip
        limit: Maximum records to return
        db: Database connection

    Returns:
        dict: Dictionary with resources list and metadata
    """
    # Verify language exists
    language = await db.languages.find_one({"code": language_code})
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language {language_code} not found",
        )

    # Build query
    query = {"languages": language_code}

    if resource_type:
        query["resource_type"] = resource_type

    if platform:
        query["platform"] = platform

    if verified_only:
        query["verification_status"] = "verified"

    # Query database
    cursor = (
        db.external_resources.find(query)
        .sort("click_count", -1)
        .skip(skip)
        .limit(limit)
    )

    resources = []
    async for doc in cursor:
        doc = serialize_document(doc)
        resources.append(doc)

    return {
        "language_code": language_code,
        "total": len(resources),
        "resources": resources,
    }


# ============================================================================
# TASK-BASED DISCOVERY
# ============================================================================


@router.get("/tasks/{task_type}")
async def discover_by_task(
    task_type: str,
    language_code: Optional[str] = Query(None, description="Filter by language"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Discover resources by ML task type (tts, asr, nmt, llm, etc.).

    Returns models, datasets, and pipelines suitable for the specified task.

    Args:
        task_type: Task type (tts, asr, nmt, llm, etc.)
        language_code: Optional language filter
        skip: Number of records to skip
        limit: Maximum records to return
        db: Database connection

    Returns:
        dict: Resources organized by type
    """
    # Build query
    query = {"model_type": task_type}
    if language_code:
        query["languages"] = language_code

    # Get models for this task
    models_cursor = db.ml_models.find(query).sort("download_count", -1).limit(limit)
    models = []
    async for doc in models_cursor:
        doc = serialize_document(doc)
        models.append(doc)

    # Get datasets for this task
    dataset_query = {}
    if language_code:
        dataset_query["languages"] = language_code

    # Map task type to dataset type
    task_to_data_type = {
        "tts": "audio",
        "asr": "audio",
        "nmt": "parallel",
        "llm": "text",
    }

    data_type = task_to_data_type.get(task_type)
    if data_type:
        dataset_query["data_type"] = data_type

    datasets_cursor = db.datasets.find(dataset_query).sort("created_at", -1).limit(limit)
    datasets = []
    async for doc in datasets_cursor:
        doc = serialize_document(doc)
        datasets.append(doc)

    # Get training pipelines for this task
    pipeline_query = {"task_type": task_type}
    if language_code:
        pipeline_query["target_language"] = language_code

    pipelines_cursor = (
        db.ml_training_pipelines.find(pipeline_query)
        .sort("created_at", -1)
        .limit(limit)
    )
    pipelines = []
    async for doc in pipelines_cursor:
        doc = serialize_document(doc)
        pipelines.append(doc)

    return {
        "task_type": task_type,
        "language_code": language_code,
        "models": models,
        "datasets": datasets,
        "training_pipelines": pipelines,
        "statistics": {
            "total_models": len(models),
            "total_datasets": len(datasets),
            "total_pipelines": len(pipelines),
        },
    }


# ============================================================================
# TRENDING & POPULAR
# ============================================================================


@router.get("/trending/models")
async def discover_trending_models(
    language_code: Optional[str] = Query(None, description="Filter by language"),
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Discover trending models based on download count.

    Args:
        language_code: Optional language filter
        model_type: Optional model type filter
        limit: Maximum models to return
        db: Database connection

    Returns:
        List[dict]: List of trending models
    """
    # Build query
    query = {}
    if language_code:
        query["languages"] = language_code
    if model_type:
        query["model_type"] = model_type

    # Get top models by download count
    cursor = db.ml_models.find(query).sort("download_count", -1).limit(limit)

    models = []
    async for doc in cursor:
        doc = serialize_document(doc)
        models.append(doc)

    return {"trending_models": models, "total": len(models)}


@router.get("/trending/datasets")
async def discover_trending_datasets(
    language_code: Optional[str] = Query(None, description="Filter by language"),
    data_type: Optional[str] = Query(None, description="Filter by data type"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Discover trending datasets based on download count.

    Args:
        language_code: Optional language filter
        data_type: Optional data type filter
        limit: Maximum datasets to return
        db: Database connection

    Returns:
        dict: Dictionary with trending datasets
    """
    # Build query
    query = {}
    if language_code:
        query["languages"] = language_code
    if data_type:
        query["data_type"] = data_type

    # Get top datasets by download count
    cursor = db.datasets.find(query).sort("download_count", -1).limit(limit)

    datasets = []
    async for doc in cursor:
        doc = serialize_document(doc)
        datasets.append(doc)

    return {"trending_datasets": datasets, "total": len(datasets)}


@router.get("/trending/resources")
async def discover_trending_resources(
    language_code: Optional[str] = Query(None, description="Filter by language"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Discover trending external resources based on click count.

    Args:
        language_code: Optional language filter
        resource_type: Optional resource type filter
        limit: Maximum resources to return
        db: Database connection

    Returns:
        dict: Dictionary with trending resources
    """
    # Build query
    query = {}
    if language_code:
        query["languages"] = language_code
    if resource_type:
        query["resource_type"] = resource_type

    # Get top resources by click count
    cursor = db.external_resources.find(query).sort("click_count", -1).limit(limit)

    resources = []
    async for doc in cursor:
        doc = serialize_document(doc)
        resources.append(doc)

    return {"trending_resources": resources, "total": len(resources)}


# ============================================================================
# RECOMMENDATIONS
# ============================================================================


@router.get("/recommendations/models/{model_uuid}/similar")
async def recommend_similar_models(
    model_uuid: str,
    limit: int = Query(5, ge=1, le=20),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Recommend similar models based on language, type, and architecture.

    Recommendation algorithm:
    1. Same languages
    2. Same model type
    3. Similar architecture
    4. High download count

    Args:
        model_uuid: Model UUID
        limit: Maximum recommendations
        db: Database connection

    Returns:
        dict: Dictionary with similar models
    """
    # Get source model
    model = await db.ml_models.find_one({"model_uuid": model_uuid})
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_uuid} not found",
        )

    # Build recommendation query
    # Reason: Find models with same languages and type, exclude the source model
    query = {
        "model_uuid": {"$ne": model_uuid},
        "languages": {"$in": model["languages"]},
        "model_type": model["model_type"],
    }

    # Prefer same architecture
    if model.get("architecture"):
        query["architecture"] = model["architecture"]

    # Get similar models sorted by download count
    cursor = db.ml_models.find(query).sort("download_count", -1).limit(limit)

    similar_models = []
    async for doc in cursor:
        doc = serialize_document(doc)
        similar_models.append(doc)

    # If not enough results, relax architecture constraint
    if len(similar_models) < limit:
        fallback_query = {
            "model_uuid": {"$ne": model_uuid},
            "languages": {"$in": model["languages"]},
            "model_type": model["model_type"],
        }

        # Exclude already found models
        if similar_models:
            found_uuids = [m["model_uuid"] for m in similar_models]
            fallback_query["model_uuid"]["$nin"] = found_uuids

        remaining = limit - len(similar_models)
        fallback_cursor = (
            db.ml_models.find(fallback_query).sort("download_count", -1).limit(remaining)
        )

        async for doc in fallback_cursor:
            doc = serialize_document(doc)
            similar_models.append(doc)

    return {
        "source_model": {
            "model_uuid": model["model_uuid"],
            "name": model["name"],
            "languages": model["languages"],
        },
        "recommendations": similar_models,
        "total": len(similar_models),
    }


@router.get("/recommendations/datasets/{dataset_uuid}/compatible-models")
async def recommend_compatible_models(
    dataset_uuid: str,
    limit: int = Query(10, ge=1, le=20),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Recommend models compatible with a dataset.

    Matches models by:
    1. Same languages
    2. Compatible data type (audio datasets → tts/asr models, etc.)

    Args:
        dataset_uuid: Dataset UUID
        limit: Maximum recommendations
        db: Database connection

    Returns:
        dict: Dictionary with compatible models
    """
    # Get source dataset
    dataset = await db.datasets.find_one({"dataset_uuid": dataset_uuid})
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_uuid} not found",
        )

    # Map data type to model types
    # Reason: Audio datasets work with TTS and ASR models, text with LLM, etc.
    data_to_model_type = {
        "audio": ["tts", "asr"],
        "text": ["llm", "nmt"],
        "parallel": ["nmt"],
    }

    model_types = data_to_model_type.get(dataset.get("data_type"), [])

    # Build query
    query = {
        "languages": {"$in": dataset["languages"]},
    }

    if model_types:
        query["model_type"] = {"$in": model_types}

    # Get compatible models
    cursor = db.ml_models.find(query).sort("download_count", -1).limit(limit)

    compatible_models = []
    async for doc in cursor:
        doc = serialize_document(doc)
        compatible_models.append(doc)

    return {
        "source_dataset": {
            "dataset_uuid": dataset["dataset_uuid"],
            "name": dataset["name"],
            "languages": dataset["languages"],
            "data_type": dataset.get("data_type"),
        },
        "compatible_models": compatible_models,
        "total": len(compatible_models),
    }


# ============================================================================
# STATISTICS & OVERVIEW
# ============================================================================


@router.get("/overview")
async def get_platform_overview(
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get comprehensive platform overview with statistics.

    Returns:
        dict: Platform statistics
    """
    # Count totals
    total_languages = await db.languages.count_documents({})
    total_datasets = await db.datasets.count_documents({})
    total_models = await db.ml_models.count_documents({})
    total_resources = await db.external_resources.count_documents({})
    total_pipelines = await db.ml_training_pipelines.count_documents({})

    # Get top languages by resource count
    top_languages_pipeline = [
        {"$unwind": "$languages"},
        {"$group": {"_id": "$languages", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]

    top_languages = []
    async for doc in db.datasets.aggregate(top_languages_pipeline):
        lang_doc = await db.languages.find_one({"code": doc["_id"]})
        if lang_doc:
            top_languages.append({
                "code": doc["_id"],
                "name": lang_doc.get("name"),
                "resource_count": doc["count"],
            })

    # Get models by type
    models_by_type_pipeline = [
        {"$group": {"_id": "$model_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]

    models_by_type = {}
    async for doc in db.ml_models.aggregate(models_by_type_pipeline):
        models_by_type[doc["_id"]] = doc["count"]

    # Get datasets by type
    datasets_by_type_pipeline = [
        {"$group": {"_id": "$data_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]

    datasets_by_type = {}
    async for doc in db.datasets.aggregate(datasets_by_type_pipeline):
        datasets_by_type[doc["_id"] or "unknown"] = doc["count"]

    return {
        "totals": {
            "languages": total_languages,
            "datasets": total_datasets,
            "models": total_models,
            "external_resources": total_resources,
            "training_pipelines": total_pipelines,
        },
        "top_languages": top_languages,
        "models_by_type": models_by_type,
        "datasets_by_type": datasets_by_type,
    }


@router.get("/search")
async def global_search(
    query: str = Query(..., min_length=2, description="Search query"),
    search_datasets: bool = Query(True, description="Search datasets"),
    search_models: bool = Query(True, description="Search models"),
    search_resources: bool = Query(True, description="Search external resources"),
    language_code: Optional[str] = Query(None, description="Filter by language"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Global search across all resource types.

    Searches in titles, descriptions, and tags using text search.

    Args:
        query: Search query
        search_datasets: Include datasets in results
        search_models: Include models in results
        search_resources: Include external resources in results
        language_code: Optional language filter
        limit: Maximum results per type
        db: Database connection

    Returns:
        dict: Search results organized by type
    """
    results = {}

    # Build text search query
    # Reason: MongoDB text search with optional language filter
    text_query = {"$text": {"$search": query}}

    if language_code:
        text_query["languages"] = language_code

    # Search datasets
    if search_datasets:
        try:
            datasets_cursor = (
                db.datasets.find(text_query)
                .sort([("score", {"$meta": "textScore"})])
                .limit(limit)
            )
            datasets = []
            async for doc in datasets_cursor:
                doc = serialize_document(doc)
                datasets.append(doc)
            results["datasets"] = datasets
        except Exception:
            # Fallback to regex search if text index doesn't exist
            regex_query = {
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                ]
            }
            if language_code:
                regex_query["languages"] = language_code

            datasets_cursor = db.datasets.find(regex_query).limit(limit)
            datasets = []
            async for doc in datasets_cursor:
                doc = serialize_document(doc)
                datasets.append(doc)
            results["datasets"] = datasets

    # Search models
    if search_models:
        try:
            models_cursor = (
                db.ml_models.find(text_query)
                .sort([("score", {"$meta": "textScore"})])
                .limit(limit)
            )
            models = []
            async for doc in models_cursor:
                doc = serialize_document(doc)
                models.append(doc)
            results["models"] = models
        except Exception:
            # Fallback to regex search
            regex_query = {
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                ]
            }
            if language_code:
                regex_query["languages"] = language_code

            models_cursor = db.ml_models.find(regex_query).limit(limit)
            models = []
            async for doc in models_cursor:
                doc = serialize_document(doc)
                models.append(doc)
            results["models"] = models

    # Search external resources
    if search_resources:
        try:
            resources_cursor = (
                db.external_resources.find(text_query)
                .sort([("score", {"$meta": "textScore"})])
                .limit(limit)
            )
            resources = []
            async for doc in resources_cursor:
                doc = serialize_document(doc)
                resources.append(doc)
            results["external_resources"] = resources
        except Exception:
            # Fallback to regex search
            regex_query = {
                "$or": [
                    {"title": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                ]
            }
            if language_code:
                regex_query["languages"] = language_code

            resources_cursor = db.external_resources.find(regex_query).limit(limit)
            resources = []
            async for doc in resources_cursor:
                doc = serialize_document(doc)
                resources.append(doc)
            results["external_resources"] = resources

    # Calculate totals
    totals = {
        "datasets": len(results.get("datasets", [])),
        "models": len(results.get("models", [])),
        "external_resources": len(results.get("external_resources", [])),
    }

    return {
        "query": query,
        "language_code": language_code,
        "results": results,
        "totals": totals,
        "total_results": sum(totals.values()),
    }
