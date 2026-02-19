"""
Resources Router for African Language Community Platform.

Handles external resource links and file uploads with Hetzner Storage Box integration.
"""

import os
import uuid
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

import httpx
from bson import ObjectId
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.auth import get_current_user
from database import get_database
from models.resource_models import (
    FileUpload,
    FileUploadCreate,
    Platform,
    ProcessingStatus,
    ResourceLink,
    ResourceLinkCreate,
    ResourceLinkUpdate,
    ResourceStats,
    ResourceType,
    ResourceVerification,
    ResourceVote,
    UploadProgressUpdate,
    UploadType,
    VerificationStatus,
)
from services.storage_service import HetznerStorageService

router = APIRouter(prefix="/resources", tags=["resources"])


def serialize_resource(doc: dict) -> dict:
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
        if "submitted_by" in doc and isinstance(doc["submitted_by"], ObjectId):
            doc["submitted_by"] = str(doc["submitted_by"])
        if "uploaded_by" in doc and isinstance(doc["uploaded_by"], ObjectId):
            doc["uploaded_by"] = str(doc["uploaded_by"])
        if "verified_by" in doc and isinstance(doc["verified_by"], ObjectId):
            doc["verified_by"] = str(doc["verified_by"])
        if "language_ids" in doc:
            doc["language_ids"] = [
                str(lid) if isinstance(lid, ObjectId) else lid
                for lid in doc.get("language_ids", [])
            ]
        if "language_id" in doc and isinstance(doc["language_id"], ObjectId):
            doc["language_id"] = str(doc["language_id"])
    return doc


async def get_language_ids(
    db: AsyncIOMotorDatabase, language_codes: List[str]
) -> List[str]:
    """
    Resolve language codes to ObjectIds.

    Args:
        db: Database connection
        language_codes: List of language codes (e.g., ["twi", "yo"])

    Returns:
        List[str]: List of language ObjectIds as strings
    """
    language_ids = []
    for code in language_codes:
        lang = await db.languages.find_one({"code": code})
        if lang:
            language_ids.append(str(lang["_id"]))
    return language_ids


# ============================================================================
# EXTERNAL RESOURCE LINK ENDPOINTS
# ============================================================================


@router.post(
    "/links", response_model=ResourceLink, status_code=status.HTTP_201_CREATED
)
async def submit_resource_link(
    link_data: ResourceLinkCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """
    Submit an external resource link (GitHub, Hugging Face, Zenodo, etc.).

    Supported platforms:
    - github.com
    - huggingface.co
    - kaggle.com
    - zenodo.org
    - arxiv.org
    - openslr.org
    - commonvoice.mozilla.org

    Args:
        link_data: Resource link data
        db: Database connection
        current_user: Current authenticated user

    Returns:
        ResourceLink: Created resource link
    """
    # Get language IDs
    language_ids = await get_language_ids(db, link_data.languages)

    # Determine platform from URL if not specified
    parsed_url = urlparse(str(link_data.url))
    platform = link_data.platform

    if platform == Platform.CUSTOM:
        # Auto-detect platform
        if "github.com" in parsed_url.netloc:
            platform = Platform.GITHUB
        elif "huggingface.co" in parsed_url.netloc:
            platform = Platform.HUGGINGFACE
        elif "kaggle.com" in parsed_url.netloc:
            platform = Platform.KAGGLE
        elif "zenodo.org" in parsed_url.netloc:
            platform = Platform.ZENODO
        elif "arxiv.org" in parsed_url.netloc:
            platform = Platform.ARXIV
        elif "openslr.org" in parsed_url.netloc:
            platform = Platform.OPENSLR
        elif "commonvoice.mozilla.org" in parsed_url.netloc:
            platform = Platform.COMMONVOICE

    # Create resource link document
    link_doc = {
        "link_uuid": str(uuid.uuid4()),
        "title": link_data.title,
        "url": str(link_data.url),
        "resource_type": link_data.resource_type,
        "platform": platform,
        "model_type": link_data.model_type,
        "data_type": link_data.data_type,
        "languages": link_data.languages,
        "language_ids": [ObjectId(lid) for lid in language_ids],
        "is_multilingual": link_data.is_multilingual,
        "description": link_data.description,
        "tags": link_data.tags,
        "license": link_data.license,
        "citation": link_data.citation,
        "quality_rating": 0.0,
        "verification_status": VerificationStatus.UNVERIFIED,
        "verified_by": None,
        "verified_at": None,
        "last_checked": None,
        "is_available": True,
        "availability_checks": 0,
        "downtime_count": 0,
        "submitted_by": ObjectId(current_user["id"]) if ObjectId.is_valid(current_user["id"]) else current_user["id"],
        "upvotes": 0,
        "downvotes": 0,
        "view_count": 0,
        "click_count": 0,
        "used_in_pipelines": [],
        "used_in_models": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    # Insert into database
    result = await db.external_resources.insert_one(link_doc)

    # Update language collection with resource reference
    await db.languages.update_many(
        {"code": {"$in": link_data.languages}},
        {"$addToSet": {"external_resources": str(result.inserted_id)}},
    )

    # Fetch and return
    link_doc = await db.external_resources.find_one({"_id": result.inserted_id})
    link_doc = serialize_resource(link_doc)

    return ResourceLink(**link_doc)


@router.get("/links", response_model=List[ResourceLink])
async def browse_resource_links(
    resource_type: Optional[ResourceType] = Query(None, description="Filter by type"),
    platform: Optional[Platform] = Query(None, description="Filter by platform"),
    languages: Optional[str] = Query(
        None, description="Filter by language codes (comma-separated)"
    ),
    verification_status: Optional[VerificationStatus] = Query(
        None, description="Filter by verification status"
    ),
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    data_type: Optional[str] = Query(None, description="Filter by data type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Browse external resource links with filtering.

    Args:
        resource_type: Filter by resource type
        platform: Filter by platform
        languages: Comma-separated language codes
        verification_status: Filter by verification status
        model_type: Filter by model type (tts, asr, llm, etc.)
        data_type: Filter by data type (audio, text, etc.)
        skip: Number of records to skip
        limit: Maximum records to return
        db: Database connection

    Returns:
        List[ResourceLink]: List of resource links
    """
    # Build query
    query = {}

    if resource_type:
        query["resource_type"] = resource_type

    if platform:
        query["platform"] = platform

    if languages:
        lang_list = [lang.strip() for lang in languages.split(",") if lang.strip()]
        query["languages"] = {"$in": lang_list}

    if verification_status:
        query["verification_status"] = verification_status

    if model_type:
        query["model_type"] = model_type

    if data_type:
        query["data_type"] = data_type

    # Query database
    cursor = (
        db.external_resources.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    links = []
    async for doc in cursor:
        doc = serialize_resource(doc)
        links.append(ResourceLink(**doc))

    return links


@router.get("/links/{link_uuid}", response_model=ResourceLink)
async def get_resource_link(
    link_uuid: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get resource link details and increment view count.

    Args:
        link_uuid: Link UUID
        db: Database connection

    Returns:
        ResourceLink: Resource link details
    """
    link = await db.external_resources.find_one({"link_uuid": link_uuid})

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource link {link_uuid} not found",
        )

    # Increment view count
    await db.external_resources.update_one(
        {"link_uuid": link_uuid}, {"$inc": {"view_count": 1}}
    )

    link = serialize_resource(link)
    return ResourceLink(**link)


@router.put("/links/{link_uuid}", response_model=ResourceLink)
async def update_resource_link(
    link_uuid: str,
    link_update: ResourceLinkUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """
    Update resource link (submitter only).

    Args:
        link_uuid: Link UUID
        link_update: Update data
        db: Database connection
        current_user: Current authenticated user

    Returns:
        ResourceLink: Updated resource link
    """
    link = await db.external_resources.find_one({"link_uuid": link_uuid})

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource link {link_uuid} not found",
        )

    # Check authorization
    if str(link["submitted_by"]) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the submitter can update this resource link",
        )

    # Build update document
    update_doc = {"updated_at": datetime.utcnow()}

    if link_update.title is not None:
        update_doc["title"] = link_update.title

    if link_update.description is not None:
        update_doc["description"] = link_update.description

    if link_update.tags is not None:
        update_doc["tags"] = link_update.tags

    if link_update.license is not None:
        update_doc["license"] = link_update.license

    if link_update.citation is not None:
        update_doc["citation"] = link_update.citation

    # Update database
    await db.external_resources.update_one(
        {"link_uuid": link_uuid}, {"$set": update_doc}
    )

    # Fetch and return
    link = await db.external_resources.find_one({"link_uuid": link_uuid})
    link = serialize_resource(link)

    return ResourceLink(**link)


@router.delete("/links/{link_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource_link(
    link_uuid: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a resource link (submitter or admin only).

    Args:
        link_uuid: Link UUID to delete
        db: Database connection
        current_user: Current authenticated user

    Returns:
        None (204 No Content)
    """
    link = await db.external_resources.find_one({"link_uuid": link_uuid})

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource link {link_uuid} not found",
        )

    # Check authorization - must be submitter or admin
    user_role = current_user.get("role", "user")
    is_owner = str(link["submitted_by"]) == current_user["id"]
    is_admin = user_role == "admin"

    if not is_owner and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the submitter or admin can delete this resource link",
        )

    # Remove resource reference from languages
    await db.languages.update_many(
        {"external_resources": str(link["_id"])},
        {"$pull": {"external_resources": str(link["_id"])}},
    )

    # Delete the resource
    await db.external_resources.delete_one({"link_uuid": link_uuid})

    return None


@router.post("/links/{link_uuid}/verify", response_model=ResourceVerification)
async def verify_resource_link(
    link_uuid: str,
    verification_notes: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """
    Verify a resource link by checking its availability (moderators/admins only).

    Performs HTTP HEAD request to check if URL is accessible.

    Args:
        link_uuid: Link UUID
        verification_notes: Optional verification notes
        db: Database connection
        current_user: Current authenticated user

    Returns:
        ResourceVerification: Verification result
    """
    # Check if user is moderator or admin
    user_role = current_user.get("role", "user")
    if user_role not in ["moderator", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only moderators and admins can verify resource links",
        )

    link = await db.external_resources.find_one({"link_uuid": link_uuid})

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource link {link_uuid} not found",
        )

    # Perform URL accessibility check
    is_available = False
    status_code = None
    response_time_ms = None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            start_time = datetime.utcnow()
            response = await client.head(link["url"], follow_redirects=True)
            end_time = datetime.utcnow()

            status_code = response.status_code
            response_time_ms = (end_time - start_time).total_seconds() * 1000
            is_available = response.status_code == 200
    except Exception:
        is_available = False

    # Update link verification status
    verification_status = (
        VerificationStatus.VERIFIED
        if is_available
        else VerificationStatus.BROKEN
    )

    await db.external_resources.update_one(
        {"link_uuid": link_uuid},
        {
            "$set": {
                "verification_status": verification_status,
                "verified_by": ObjectId(current_user["id"]) if ObjectId.is_valid(current_user["id"]) else current_user["id"],
                "verified_at": datetime.utcnow(),
                "last_checked": datetime.utcnow(),
                "is_available": is_available,
                "updated_at": datetime.utcnow(),
            },
            "$inc": {"availability_checks": 1},
        },
    )

    # Increment downtime count if broken
    if not is_available:
        await db.external_resources.update_one(
            {"link_uuid": link_uuid}, {"$inc": {"downtime_count": 1}}
        )

    return ResourceVerification(
        is_available=is_available,
        status_code=status_code,
        response_time_ms=response_time_ms,
        verification_notes=verification_notes,
    )


@router.post("/links/{link_uuid}/vote")
async def vote_on_resource(
    link_uuid: str,
    vote: ResourceVote,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """
    Vote on a resource link (upvote or downvote).

    Args:
        link_uuid: Link UUID
        vote: Vote data
        db: Database connection
        current_user: Current authenticated user

    Returns:
        dict: Updated vote counts
    """
    link = await db.external_resources.find_one({"link_uuid": link_uuid})

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource link {link_uuid} not found",
        )

    # Update vote count
    if vote.vote_type == "upvote":
        await db.external_resources.update_one(
            {"link_uuid": link_uuid}, {"$inc": {"upvotes": 1}}
        )
    else:
        await db.external_resources.update_one(
            {"link_uuid": link_uuid}, {"$inc": {"downvotes": 1}}
        )

    # Fetch updated link
    link = await db.external_resources.find_one({"link_uuid": link_uuid})

    return {
        "link_uuid": link_uuid,
        "upvotes": link["upvotes"],
        "downvotes": link["downvotes"],
        "vote_type": vote.vote_type,
    }


@router.post("/links/{link_uuid}/click")
async def track_resource_click(
    link_uuid: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Track when a user clicks on a resource link.

    Args:
        link_uuid: Link UUID
        db: Database connection

    Returns:
        dict: Updated click count
    """
    link = await db.external_resources.find_one({"link_uuid": link_uuid})

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource link {link_uuid} not found",
        )

    # Increment click count
    await db.external_resources.update_one(
        {"link_uuid": link_uuid}, {"$inc": {"click_count": 1}}
    )

    link = await db.external_resources.find_one({"link_uuid": link_uuid})

    return {"link_uuid": link_uuid, "click_count": link["click_count"]}


# ============================================================================
# FILE UPLOAD ENDPOINTS
# ============================================================================


@router.post("/upload", response_model=FileUpload, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    upload_type: str = Form(...),
    file_type: str = Form(...),
    language_code: str = Form(...),
    description: str = Form(...),
    tags: Optional[str] = Form(None),
    license: str = Form("CC-BY-4.0"),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a file to Hetzner Storage Box.

    Supported upload types: dataset, model, notebook, resource
    Supported file types: audio, text, model, notebook

    Args:
        file: File to upload
        upload_type: Upload type
        file_type: File type
        language_code: Language code
        description: File description
        tags: Comma-separated tags
        license: License (default: CC-BY-4.0)
        db: Database connection
        current_user: Current authenticated user

    Returns:
        FileUpload: Upload tracking information
    """
    # Validate upload type
    try:
        upload_type_enum = UploadType(upload_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid upload_type. Must be one of: {', '.join([t.value for t in UploadType])}",
        )

    # Parse tags
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []

    # Get language info
    language = await db.languages.find_one({"code": language_code})
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language {language_code} not found",
        )

    # Generate unique upload ID
    upload_uuid = str(uuid.uuid4())
    user_id = current_user["id"]

    # Calculate file size
    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)

    # Determine storage path
    storage_path = f"user-uploads/{user_id}/{upload_uuid}/{file.filename}"

    try:
        # Initialize storage service
        storage = HetznerStorageService(
            host=os.getenv("HETZNER_STORAGE_HOST"),
            username=os.getenv("HETZNER_STORAGE_USERNAME"),
            password=os.getenv("HETZNER_STORAGE_PASSWORD"),
            port=int(os.getenv("HETZNER_STORAGE_PORT", "23")),
        )

        # Upload file
        storage.connect()
        upload_result = storage.upload_file(file_content, storage_path, compute_checksum=True)
        storage.disconnect()

        # Generate WebDAV access URL
        webdav_base = os.getenv("HETZNER_WEBDAV_URL", "https://u361018.your-storagebox.de")
        access_url = f"{webdav_base}/{storage_path}"

        # Create upload document
        upload_doc = {
            "upload_uuid": upload_uuid,
            "uploaded_by": ObjectId(user_id),
            "upload_type": upload_type_enum,
            "original_filename": file.filename,
            "file_type": file_type,
            "mime_type": file.content_type or "application/octet-stream",
            "file_size_mb": round(file_size_mb, 2),
            "storage_path": storage_path,
            "access_url": access_url,
            "is_temporary": False,
            "processing_status": ProcessingStatus.COMPLETED,
            "processing_started_at": datetime.utcnow(),
            "processing_completed_at": datetime.utcnow(),
            "processing_error": None,
            "validation_results": None,
            "language_code": language_code,
            "language_id": str(language["_id"]),
            "tags": tag_list,
            "description": description,
            "integrated_into_dataset": None,
            "integrated_at": None,
            "access_level": "authenticated",
            "license": license,
            "is_quarantined": False,
            "virus_scan_result": None,
            "scanned_at": None,
            "created_at": datetime.utcnow(),
            "expires_at": None,
        }

        # Insert into database
        result = await db.user_uploads.insert_one(upload_doc)

        # Fetch and return
        upload_doc = await db.user_uploads.find_one({"_id": result.inserted_id})
        upload_doc = serialize_resource(upload_doc)

        return FileUpload(**upload_doc)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}",
        )


@router.get("/uploads/{upload_uuid}", response_model=FileUpload)
async def get_upload_status(
    upload_uuid: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """
    Track upload status and details.

    Args:
        upload_uuid: Upload UUID
        db: Database connection
        current_user: Current authenticated user

    Returns:
        FileUpload: Upload details
    """
    upload = await db.user_uploads.find_one({"upload_uuid": upload_uuid})

    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload {upload_uuid} not found",
        )

    upload = serialize_resource(upload)
    return FileUpload(**upload)


@router.get("/uploads", response_model=List[FileUpload])
async def list_user_uploads(
    upload_type: Optional[UploadType] = Query(None, description="Filter by upload type"),
    processing_status: Optional[ProcessingStatus] = Query(None, description="Filter by status"),
    language_code: Optional[str] = Query(None, description="Filter by language"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """
    List user's uploads with filtering.

    Args:
        upload_type: Filter by upload type
        processing_status: Filter by processing status
        language_code: Filter by language code
        skip: Number of records to skip
        limit: Maximum records to return
        db: Database connection
        current_user: Current authenticated user

    Returns:
        List[FileUpload]: List of uploads
    """
    # Build query
    user_id = ObjectId(current_user["id"]) if ObjectId.is_valid(current_user["id"]) else current_user["id"]
    query = {"uploaded_by": user_id}

    if upload_type:
        query["upload_type"] = upload_type

    if processing_status:
        query["processing_status"] = processing_status

    if language_code:
        query["language_code"] = language_code

    # Query database
    cursor = (
        db.user_uploads.find(query).sort("created_at", -1).skip(skip).limit(limit)
    )

    uploads = []
    async for doc in cursor:
        doc = serialize_resource(doc)
        uploads.append(FileUpload(**doc))

    return uploads


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================


@router.get("/stats", response_model=ResourceStats)
async def get_resource_statistics(
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get comprehensive resource statistics.

    Returns statistics for external links and uploads by type, platform, language, etc.

    Args:
        db: Database connection

    Returns:
        ResourceStats: Resource statistics
    """
    # Count total links
    total_links = await db.external_resources.count_documents({})

    # Links by type
    links_by_type_pipeline = [
        {"$group": {"_id": "$resource_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    links_by_type = {}
    async for doc in db.external_resources.aggregate(links_by_type_pipeline):
        links_by_type[doc["_id"]] = doc["count"]

    # Links by platform
    links_by_platform_pipeline = [
        {"$group": {"_id": "$platform", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    links_by_platform = {}
    async for doc in db.external_resources.aggregate(links_by_platform_pipeline):
        links_by_platform[doc["_id"]] = doc["count"]

    # Links by language
    links_by_language_pipeline = [
        {"$unwind": "$languages"},
        {"$group": {"_id": "$languages", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20},  # Top 20 languages
    ]
    links_by_language = {}
    async for doc in db.external_resources.aggregate(links_by_language_pipeline):
        links_by_language[doc["_id"]] = doc["count"]

    # Verified links count
    verified_links = await db.external_resources.count_documents(
        {"verification_status": VerificationStatus.VERIFIED}
    )

    # Broken links count
    broken_links = await db.external_resources.count_documents(
        {"verification_status": VerificationStatus.BROKEN}
    )

    # Count total uploads
    total_uploads = await db.user_uploads.count_documents({})

    # Uploads by type
    uploads_by_type_pipeline = [
        {"$group": {"_id": "$upload_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    uploads_by_type = {}
    async for doc in db.user_uploads.aggregate(uploads_by_type_pipeline):
        uploads_by_type[doc["_id"]] = doc["count"]

    # Uploads by status
    uploads_by_status_pipeline = [
        {"$group": {"_id": "$processing_status", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    uploads_by_status = {}
    async for doc in db.user_uploads.aggregate(uploads_by_status_pipeline):
        uploads_by_status[doc["_id"]] = doc["count"]

    # Total storage used
    storage_pipeline = [
        {"$group": {"_id": None, "total_size_mb": {"$sum": "$file_size_mb"}}}
    ]
    total_storage_mb = 0.0
    async for doc in db.user_uploads.aggregate(storage_pipeline):
        total_storage_mb = doc["total_size_mb"]

    total_storage_gb = round(total_storage_mb / 1024, 2)

    return ResourceStats(
        total_links=total_links,
        links_by_type=links_by_type,
        links_by_platform=links_by_platform,
        links_by_language=links_by_language,
        verified_links=verified_links,
        broken_links=broken_links,
        total_uploads=total_uploads,
        uploads_by_type=uploads_by_type,
        uploads_by_status=uploads_by_status,
        total_storage_used_gb=total_storage_gb,
    )
