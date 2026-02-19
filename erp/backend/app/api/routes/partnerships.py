"""
Partnership Management Routes.

Handles partnerships, proposals, and interactions.
All data is organization-scoped.
Files stored in Hetzner Storage Box.
"""

import logging
import mimetypes
import os
import tempfile
from datetime import datetime
from io import BytesIO
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse

from app.core.database import MongoDB
from app.models.partnerships import Partnership, PartnershipInteraction, PartnershipStage
from app.schemas.partnerships import (
    PartnershipCreate,
    PartnershipUpdate,
    PartnershipInteractionCreate,
    PartnershipInteractionUpdate,
)
from apps.shared.dependencies import require_organization_access, OrganizationScoped
from apps.shared.storage.hetzner_storage_box import get_storage, StorageProtocol

logger = logging.getLogger(__name__)
router = APIRouter()


# Partnership endpoints
@router.post("/partnerships", response_model=Partnership, status_code=status.HTTP_201_CREATED)
async def create_partnership(
    partnership_data: PartnershipCreate,
    scope: OrganizationScoped = Depends(),
):
    """Create a new partnership."""
    db = MongoDB.get_database()

    # Create full Partnership model with organization data
    partnership = Partnership(
        **partnership_data.model_dump(),
        organization_id=scope.org_id,
        created_by=scope.user.get("id") or scope.user.get("sub"),
    )

    await db.partnerships.insert_one(partnership.model_dump())
    logger.info(f"Partnership {partnership.id} created in org {scope.org_id}")
    return partnership


@router.get("/partnerships", response_model=List[Partnership])
async def list_partnerships(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    stage: Optional[PartnershipStage] = None,
    partnership_type: Optional[str] = None,
):
    """List all partnerships in the organization."""
    db = MongoDB.get_database()

    query = {"organization_id": org_id, "is_active": True}

    if search:
        query["$or"] = [
            {"partner_name": {"$regex": search, "$options": "i"}},
            {"primary_contact_name": {"$regex": search, "$options": "i"}},
            {"primary_contact_email": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    if stage:
        query["stage"] = stage

    if partnership_type:
        query["partnership_type"] = partnership_type

    cursor = db.partnerships.find(query).skip(skip).limit(limit).sort("created_at", -1)
    partnerships = await cursor.to_list(length=limit)
    return [Partnership(**p) for p in partnerships]


@router.get("/partnerships/{partnership_id}", response_model=Partnership)
async def get_partnership(
    partnership_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get partnership by ID."""
    db = MongoDB.get_database()
    partnership = await db.partnerships.find_one(
        {"id": partnership_id, "organization_id": org_id}
    )

    if not partnership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Partnership not found"
        )

    return Partnership(**partnership)


@router.patch("/partnerships/{partnership_id}", response_model=Partnership)
async def update_partnership(
    partnership_id: str,
    update_data: PartnershipUpdate,
    scope: OrganizationScoped = Depends(),
):
    """Update partnership."""
    db = MongoDB.get_database()

    # Only include fields that were actually set
    update_dict = update_data.model_dump(exclude_unset=True)
    update_dict["updated_by"] = scope.user.get("id") or scope.user.get("sub")
    update_dict["updated_at"] = datetime.utcnow()

    result = await db.partnerships.update_one(
        {"id": partnership_id, "organization_id": scope.org_id}, {"$set": update_dict}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Partnership not found"
        )

    partnership = await db.partnerships.find_one({"id": partnership_id})
    return Partnership(**partnership)


@router.delete("/partnerships/{partnership_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_partnership(
    partnership_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Soft delete partnership."""
    db = MongoDB.get_database()

    result = await db.partnerships.update_one(
        {"id": partnership_id, "organization_id": org_id}, {"$set": {"is_active": False}}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Partnership not found"
        )

    return None


# File upload endpoints
@router.post("/partnerships/{partnership_id}/upload-proposal")
async def upload_proposal(
    partnership_id: str,
    file: UploadFile = File(...),
    scope: OrganizationScoped = Depends(),
):
    """Upload a proposal file for a partnership."""
    db = MongoDB.get_database()

    # Verify partnership exists and belongs to organization
    partnership = await db.partnerships.find_one(
        {"id": partnership_id, "organization_id": scope.org_id}
    )
    if not partnership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Partnership not found"
        )

    # Get storage instance
    storage = await get_storage(
        protocol=StorageProtocol.WEBDAV,
        base_path="erp/partnerships"
    )

    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else ""
    safe_filename = f"proposal_{timestamp}.{file_ext}" if file_ext else f"proposal_{timestamp}"

    # Create remote path
    remote_path = f"{scope.org_id}/{partnership_id}/proposals/{safe_filename}"

    # Save uploaded file to temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        # Upload to Hetzner Storage Box
        await storage.upload_file(temp_path, remote_path)

        # Update partnership with file reference (store remote path)
        await db.partnerships.update_one(
            {"id": partnership_id, "organization_id": scope.org_id},
            {
                "$push": {"proposal_files": remote_path},
                "$set": {
                    "updated_by": scope.user.get("id") or scope.user.get("sub"),
                    "updated_at": datetime.utcnow(),
                },
            },
        )

        logger.info(f"Proposal uploaded for partnership {partnership_id}: {remote_path}")
        return {"filename": safe_filename, "path": remote_path}

    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@router.post("/partnerships/{partnership_id}/upload-contract")
async def upload_contract(
    partnership_id: str,
    file: UploadFile = File(...),
    scope: OrganizationScoped = Depends(),
):
    """Upload a contract file for a partnership."""
    db = MongoDB.get_database()

    # Verify partnership exists and belongs to organization
    partnership = await db.partnerships.find_one(
        {"id": partnership_id, "organization_id": scope.org_id}
    )
    if not partnership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Partnership not found"
        )

    # Get storage instance
    storage = await get_storage(
        protocol=StorageProtocol.WEBDAV,
        base_path="erp/partnerships"
    )

    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else ""
    safe_filename = f"contract_{timestamp}.{file_ext}" if file_ext else f"contract_{timestamp}"

    # Create remote path
    remote_path = f"{scope.org_id}/{partnership_id}/contracts/{safe_filename}"

    # Save uploaded file to temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        # Upload to Hetzner Storage Box
        await storage.upload_file(temp_path, remote_path)

        # Update partnership with file reference (store remote path)
        await db.partnerships.update_one(
            {"id": partnership_id, "organization_id": scope.org_id},
            {
                "$push": {"contract_files": remote_path},
                "$set": {
                    "updated_by": scope.user.get("id") or scope.user.get("sub"),
                    "updated_at": datetime.utcnow(),
                },
            },
        )

        logger.info(f"Contract uploaded for partnership {partnership_id}: {remote_path}")
        return {"filename": safe_filename, "path": remote_path}

    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@router.post("/partnerships/{partnership_id}/upload-document")
async def upload_document(
    partnership_id: str,
    file: UploadFile = File(...),
    scope: OrganizationScoped = Depends(),
):
    """Upload a general document for a partnership."""
    db = MongoDB.get_database()

    # Verify partnership exists and belongs to organization
    partnership = await db.partnerships.find_one(
        {"id": partnership_id, "organization_id": scope.org_id}
    )
    if not partnership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Partnership not found"
        )

    # Get storage instance
    storage = await get_storage(
        protocol=StorageProtocol.WEBDAV,
        base_path="erp/partnerships"
    )

    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else ""
    safe_filename = f"document_{timestamp}.{file_ext}" if file_ext else f"document_{timestamp}"

    # Create remote path
    remote_path = f"{scope.org_id}/{partnership_id}/documents/{safe_filename}"

    # Save uploaded file to temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        # Upload to Hetzner Storage Box
        await storage.upload_file(temp_path, remote_path)

        # Update partnership with file reference (store remote path)
        await db.partnerships.update_one(
            {"id": partnership_id, "organization_id": scope.org_id},
            {
                "$push": {"other_documents": remote_path},
                "$set": {
                    "updated_by": scope.user.get("id") or scope.user.get("sub"),
                    "updated_at": datetime.utcnow(),
                },
            },
        )

        logger.info(f"Document uploaded for partnership {partnership_id}: {remote_path}")
        return {"filename": safe_filename, "path": remote_path}

    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@router.get("/partnerships/{partnership_id}/files/{file_type}/{filename}")
async def download_file(
    partnership_id: str,
    file_type: str,
    filename: str,
    org_id: str = Depends(require_organization_access),
):
    """Download a partnership file."""
    db = MongoDB.get_database()

    # Verify partnership exists and belongs to organization
    partnership = await db.partnerships.find_one(
        {"id": partnership_id, "organization_id": org_id}
    )
    if not partnership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Partnership not found"
        )

    # Get storage instance
    storage = await get_storage(
        protocol=StorageProtocol.WEBDAV,
        base_path="erp/partnerships"
    )

    # Construct remote file path
    remote_path = f"{org_id}/{partnership_id}/{file_type}/{filename}"

    # Download to temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        # Download from Hetzner Storage Box
        await storage.download_file(remote_path, temp_path)

        # Read file content
        with open(temp_path, "rb") as f:
            content = f.read()

        # Determine content type based on file extension
        content_type, _ = mimetypes.guess_type(filename)
        if not content_type:
            content_type = "application/octet-stream"

        # Return file as streaming response
        return StreamingResponse(
            BytesIO(content),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logger.error(f"Error downloading file {remote_path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or error downloading file"
        )

    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


# Partnership Interaction endpoints
@router.post(
    "/partnerships/interactions",
    response_model=PartnershipInteraction,
    status_code=status.HTTP_201_CREATED,
)
async def create_interaction(
    interaction_data: PartnershipInteractionCreate,
    scope: OrganizationScoped = Depends(),
):
    """Create a new partnership interaction."""
    db = MongoDB.get_database()

    # Verify partnership exists and belongs to organization
    partnership = await db.partnerships.find_one(
        {"id": interaction_data.partnership_id, "organization_id": scope.org_id}
    )
    if not partnership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Partnership not found"
        )

    # Create interaction
    interaction = PartnershipInteraction(
        **interaction_data.model_dump(),
        organization_id=scope.org_id,
        created_by=scope.user.get("id") or scope.user.get("sub"),
    )

    await db.partnership_interactions.insert_one(interaction.model_dump())

    # Update partnership interaction count and last interaction date
    await db.partnerships.update_one(
        {"id": interaction_data.partnership_id, "organization_id": scope.org_id},
        {
            "$inc": {"interaction_count": 1},
            "$set": {
                "last_interaction_date": interaction.interaction_date,
                "updated_by": scope.user.get("id") or scope.user.get("sub"),
                "updated_at": datetime.utcnow(),
            },
        },
    )

    logger.info(
        f"Interaction {interaction.id} created for partnership {interaction_data.partnership_id}"
    )
    return interaction


@router.get(
    "/partnerships/{partnership_id}/interactions",
    response_model=List[PartnershipInteraction],
)
async def list_interactions(
    partnership_id: str,
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """List all interactions for a partnership."""
    db = MongoDB.get_database()

    # Verify partnership exists and belongs to organization
    partnership = await db.partnerships.find_one(
        {"id": partnership_id, "organization_id": org_id}
    )
    if not partnership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Partnership not found"
        )

    cursor = (
        db.partnership_interactions.find(
            {"partnership_id": partnership_id, "organization_id": org_id, "is_active": True}
        )
        .skip(skip)
        .limit(limit)
        .sort("interaction_date", -1)
    )
    interactions = await cursor.to_list(length=limit)
    return [PartnershipInteraction(**i) for i in interactions]


@router.get(
    "/partnerships/interactions/{interaction_id}",
    response_model=PartnershipInteraction,
)
async def get_interaction(
    interaction_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get interaction by ID."""
    db = MongoDB.get_database()
    interaction = await db.partnership_interactions.find_one(
        {"id": interaction_id, "organization_id": org_id}
    )

    if not interaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Interaction not found"
        )

    return PartnershipInteraction(**interaction)


@router.patch(
    "/partnerships/interactions/{interaction_id}",
    response_model=PartnershipInteraction,
)
async def update_interaction(
    interaction_id: str,
    update_data: PartnershipInteractionUpdate,
    scope: OrganizationScoped = Depends(),
):
    """Update interaction."""
    db = MongoDB.get_database()

    # Only include fields that were actually set
    update_dict = update_data.model_dump(exclude_unset=True)
    update_dict["updated_by"] = scope.user.get("id") or scope.user.get("sub")
    update_dict["updated_at"] = datetime.utcnow()

    result = await db.partnership_interactions.update_one(
        {"id": interaction_id, "organization_id": scope.org_id}, {"$set": update_dict}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Interaction not found"
        )

    interaction = await db.partnership_interactions.find_one({"id": interaction_id})
    return PartnershipInteraction(**interaction)


@router.delete(
    "/partnerships/interactions/{interaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_interaction(
    interaction_id: str,
    scope: OrganizationScoped = Depends(),
):
    """Soft delete interaction."""
    db = MongoDB.get_database()

    # Get interaction to update partnership counts
    interaction = await db.partnership_interactions.find_one(
        {"id": interaction_id, "organization_id": scope.org_id}
    )
    if not interaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Interaction not found"
        )

    # Soft delete interaction
    await db.partnership_interactions.update_one(
        {"id": interaction_id, "organization_id": scope.org_id},
        {"$set": {"is_active": False}},
    )

    # Decrement partnership interaction count
    await db.partnerships.update_one(
        {"id": interaction["partnership_id"], "organization_id": scope.org_id},
        {"$inc": {"interaction_count": -1}},
    )

    return None


# Statistics endpoint
@router.get("/partnerships/stats/summary")
async def get_partnership_stats(
    org_id: str = Depends(require_organization_access),
):
    """Get partnership statistics for the organization."""
    db = MongoDB.get_database()

    # Total partnerships by stage
    pipeline = [
        {"$match": {"organization_id": org_id, "is_active": True}},
        {"$group": {"_id": "$stage", "count": {"$sum": 1}}},
    ]
    stage_counts = await db.partnerships.aggregate(pipeline).to_list(length=None)

    # Total partnerships by type
    pipeline = [
        {"$match": {"organization_id": org_id, "is_active": True}},
        {"$group": {"_id": "$partnership_type", "count": {"$sum": 1}}},
    ]
    type_counts = await db.partnerships.aggregate(pipeline).to_list(length=None)

    # Total expected revenue
    pipeline = [
        {"$match": {"organization_id": org_id, "is_active": True}},
        {"$group": {"_id": None, "total": {"$sum": "$expected_revenue"}}},
    ]
    revenue_result = await db.partnerships.aggregate(pipeline).to_list(length=None)
    total_expected_revenue = revenue_result[0]["total"] if revenue_result else 0

    # Total actual revenue
    pipeline = [
        {"$match": {"organization_id": org_id, "is_active": True}},
        {"$group": {"_id": None, "total": {"$sum": "$actual_revenue"}}},
    ]
    actual_revenue_result = await db.partnerships.aggregate(pipeline).to_list(length=None)
    total_actual_revenue = actual_revenue_result[0]["total"] if actual_revenue_result else 0

    # Total partnerships
    total_partnerships = await db.partnerships.count_documents(
        {"organization_id": org_id, "is_active": True}
    )

    # Interactions in last 30 days
    from datetime import timedelta

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_interactions = await db.partnership_interactions.count_documents(
        {
            "organization_id": org_id,
            "is_active": True,
            "interaction_date": {"$gte": thirty_days_ago},
        }
    )

    return {
        "total_partnerships": total_partnerships,
        "by_stage": {item["_id"]: item["count"] for item in stage_counts},
        "by_type": {item["_id"]: item["count"] for item in type_counts},
        "total_expected_revenue": total_expected_revenue or 0,
        "total_actual_revenue": total_actual_revenue or 0,
        "recent_interactions_30_days": recent_interactions,
    }
