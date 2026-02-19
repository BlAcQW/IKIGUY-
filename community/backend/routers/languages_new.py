"""
Enhanced language API endpoints for the African Language Community Platform
Provides data for the Languages page frontend
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
import os

from database import get_database

router = APIRouter(tags=["languages"])

class LanguageBasic(BaseModel):
    """Basic language information"""
    code: str
    name: str
    native_name: str
    speakers: int
    progress: int
    tier: str

class LanguageFamilyResponse(BaseModel):
    """Language family with enhanced data"""
    id: str
    name: str
    description: str
    total_speakers: str
    countries: int
    total_contributions: int
    active_contributors: int
    color: str
    featured_languages: List[str]
    priority_level: str
    top_languages: List[LanguageBasic]

class LanguageDetailResponse(BaseModel):
    """Detailed language information"""
    code: str
    name: str
    native_name: str
    family: str
    subfamily: str
    speakers: int
    countries: List[str]
    regions: List[str]
    tier: str
    priority_level: str
    progress: int
    total_contributions: int
    active_contributors: int
    is_featured: bool
    development_status: str
    data_sources_count: int

class NotebookResponse(BaseModel):
    """Notebook information"""
    id: str
    name: str
    description: str
    type: str
    model_type: str
    version: str
    file_url: str
    updated_at: str

@router.get("/", response_model=List[LanguageBasic])
async def get_all_languages(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Get all languages with basic information"""
    try:
        if db is None:
            # Return mock data if database is not connected
            return [
                {
                    "code": "twi",
                    "name": "Twi",
                    "native_name": "Twi",
                    "speakers": 9000000,
                    "progress": 65,
                    "tier": "tier-1"
                },
                {
                    "code": "yor",
                    "name": "Yoruba",
                    "native_name": "Yorùbá",
                    "speakers": 47000000,
                    "progress": 80,
                    "tier": "tier-1"
                }
            ]

        languages = await db.languages.find({}).sort("speakers", -1).limit(50).to_list(None)

        result = []
        for lang in languages:
            result.append(LanguageBasic(
                code=lang["code"],
                name=lang["name"],
                native_name=lang.get("native_name", lang["name"]),
                speakers=lang.get("speakers", 0),
                progress=lang.get("progress", 0),
                tier=lang.get("tier", "tier-3")
            ))

        return result
    except Exception as e:
        print(f"Error in get_all_languages: {e}")
        return []

@router.get("/families", response_model=List[LanguageFamilyResponse])
async def get_language_families(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Get all language families with enhanced data"""

    if db is None:
        # Return mock data if database is not connected
        return []

    families = await db.language_families.find({
        "name": {"$in": ["niger-congo", "afroasiatic", "nilo-saharan", "khoisan", "indo-european"]}
    }).to_list(None)

    result = []
    for family in families:
        # Get top languages for this family
        top_languages = await db.languages.find({
            "family": family["name"].title().replace("-", "-")
        }).sort("speakers", -1).limit(4).to_list(None)

        top_languages_formatted = []
        for lang in top_languages:
            top_languages_formatted.append(LanguageBasic(
                code=lang["code"],
                name=lang["name"],
                native_name=lang.get("native_name", lang["name"]),
                speakers=lang.get("speakers", 0),
                progress=lang.get("progress", 0),
                tier=lang.get("tier", "tier-3")
            ))

        family_response = LanguageFamilyResponse(
            id=family["name"],
            name=family["name"].title().replace("-", "-"),
            description=family["description"],
            total_speakers=family.get("total_speakers", "Unknown"),
            countries=family.get("countries", 0),
            total_contributions=family.get("total_contributions", 0),
            active_contributors=family.get("active_contributors", 0),
            color=family.get("color", "primary"),
            featured_languages=family.get("featured_languages", []),
            priority_level=family.get("priority_level", "medium"),
            top_languages=top_languages_formatted
        )
        result.append(family_response)

    return result

@router.get("/featured", response_model=List[LanguageDetailResponse])
async def get_featured_languages(
    limit: int = Query(6, ge=1, le=20),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get featured languages"""

    languages = await db.languages.find({
        "is_featured": True
    }).sort("speakers", -1).limit(limit).to_list(None)

    result = []
    for lang in languages:
        result.append(LanguageDetailResponse(
            code=lang["code"],
            name=lang["name"],
            native_name=lang.get("native_name", lang["name"]),
            family=lang.get("family", "Unknown"),
            subfamily=lang.get("subfamily", "Unknown"),
            speakers=lang.get("speakers", 0),
            countries=lang.get("countries", []),
            regions=lang.get("regions", []),
            tier=lang.get("tier", "tier-3"),
            priority_level=lang.get("priority_level", "medium"),
            progress=lang.get("progress", 0),
            total_contributions=lang.get("total_contributions", 0),
            active_contributors=lang.get("active_contributors", 0),
            is_featured=lang.get("is_featured", False),
            development_status=lang.get("development_status", "submitted"),
            data_sources_count=lang.get("data_sources_count", 0)
        ))

    return result

@router.get("/search")
async def search_languages(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Search languages by name or code"""

    # Create text search query
    query = {
        "$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"native_name": {"$regex": q, "$options": "i"}},
            {"code": {"$regex": q, "$options": "i"}}
        ]
    }

    languages = await db.languages.find(query).sort("speakers", -1).limit(limit).to_list(None)

    result = []
    for lang in languages:
        result.append({
            "code": lang["code"],
            "name": lang["name"],
            "native_name": lang.get("native_name", lang["name"]),
            "speakers": lang.get("speakers", 0),
            "family": lang.get("family", "Unknown"),
            "tier": lang.get("tier", "tier-3")
        })

    return result

@router.get("/families/{family_id}", response_model=LanguageFamilyResponse)
async def get_language_family_detail(
    family_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get detailed information about a specific language family"""

    family = await db.language_families.find_one({"name": family_id})
    if not family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language family '{family_id}' not found"
        )

    # Get top languages for this family
    top_languages = await db.languages.find({
        "family": family["name"].title().replace("-", "-")
    }).sort("speakers", -1).limit(4).to_list(None)

    top_languages_formatted = []
    for lang in top_languages:
        top_languages_formatted.append(LanguageBasic(
            code=lang["code"],
            name=lang["name"],
            native_name=lang.get("native_name", lang["name"]),
            speakers=lang.get("speakers", 0),
            progress=lang.get("progress", 0),
            tier=lang.get("tier", "tier-3")
        ))

    return LanguageFamilyResponse(
        id=family["name"],
        name=family["name"].title().replace("-", "-"),
        description=family["description"],
        total_speakers=family.get("total_speakers", "Unknown"),
        countries=family.get("countries", 0),
        total_contributions=family.get("total_contributions", 0),
        active_contributors=family.get("active_contributors", 0),
        color=family.get("color", "primary"),
        featured_languages=family.get("featured_languages", []),
        priority_level=family.get("priority_level", "medium"),
        top_languages=top_languages_formatted
    )

@router.get("/families/{family_id}/languages", response_model=List[LanguageBasic])
async def get_family_languages(
    family_id: str,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get all languages in a specific family"""

    # Verify family exists
    family = await db.language_families.find_one({"name": family_id})
    if not family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language family '{family_id}' not found"
        )

    # Get all languages in this family
    languages = await db.languages.find({
        "family": family["name"].title().replace("-", "-")
    }).sort("speakers", -1).limit(limit).to_list(None)

    result = []
    for lang in languages:
        result.append(LanguageBasic(
            code=lang["code"],
            name=lang["name"],
            native_name=lang.get("native_name", lang["name"]),
            speakers=lang.get("speakers", 0),
            progress=lang.get("progress", 0),
            tier=lang.get("tier", "tier-3")
        ))

    return result

@router.get("/stats")
async def get_language_stats_simple(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Get simple language statistics for frontend header"""
    try:
        if db is None:
            # Return mock data if database is not connected
            return {
                "total_languages": 125,
                "total_families": 13,
                "most_contributed": "twi",
                "total_hours": 1250
            }

        # Total languages
        total_languages = await db.languages.count_documents({})

        # Total families
        total_families = await db.language_families.count_documents({})

        # Most contributed language (mock for now)
        most_contributed = "twi"

        # Total hours (mock for now)
        total_hours = 1250

        return {
            "total_languages": total_languages,
            "total_families": total_families,
            "most_contributed": most_contributed,
            "total_hours": total_hours
        }
    except Exception as e:
        print(f"Error in get_language_stats_simple: {e}")
        return {
            "total_languages": 125,
            "total_families": 13,
            "most_contributed": "twi",
            "total_hours": 1250
        }

@router.get("/stats/overview")
async def get_language_stats(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Get overall language statistics"""

    # Total languages
    total_languages = await db.languages.count_documents({})

    # Total speakers
    pipeline = [
        {"$group": {"_id": None, "total_speakers": {"$sum": "$speakers"}}}
    ]
    speaker_result = await db.languages.aggregate(pipeline).to_list(None)
    total_speakers = speaker_result[0]["total_speakers"] if speaker_result else 0

    # Language family distribution
    family_pipeline = [
        {"$group": {"_id": "$family", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    family_distribution = await db.languages.aggregate(family_pipeline).to_list(None)

    # Featured languages count
    featured_count = await db.languages.count_documents({"is_featured": True})

    # Countries represented
    countries_pipeline = [
        {"$unwind": "$countries"},
        {"$group": {"_id": "$countries"}},
        {"$count": "total"}
    ]
    countries_result = await db.languages.aggregate(countries_pipeline).to_list(None)
    total_countries = countries_result[0]["total"] if countries_result else 0

    return {
        "total_languages": total_languages,
        "total_speakers": total_speakers,
        "total_countries": total_countries,
        "featured_languages": featured_count,
        "family_distribution": family_distribution
    }

@router.get("/{language_code}", response_model=LanguageDetailResponse)
async def get_language_detail(
    language_code: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get detailed information about a specific language"""

    language = await db.languages.find_one({"code": language_code})
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language with code '{language_code}' not found"
        )

    return LanguageDetailResponse(
        code=language["code"],
        name=language["name"],
        native_name=language.get("native_name", language["name"]),
        family=language.get("family", "Unknown"),
        subfamily=language.get("subfamily", "Unknown"),
        speakers=language.get("speakers", 0),
        countries=language.get("countries", []),
        regions=language.get("regions", []),
        tier=language.get("tier", "tier-3"),
        priority_level=language.get("priority_level", "medium"),
        progress=language.get("progress", 0),
        total_contributions=language.get("total_contributions", 0),
        active_contributors=language.get("active_contributors", 0),
        is_featured=language.get("is_featured", False),
        development_status=language.get("development_status", "submitted"),
        data_sources_count=language.get("data_sources_count", 0)
    )

@router.get("/{language_code}/notebooks", response_model=List[NotebookResponse])
async def get_language_notebooks(
    language_code: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get notebooks for a specific language"""

    # First verify language exists
    language = await db.languages.find_one({"code": language_code})
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language with code '{language_code}' not found"
        )

    # Get notebooks for this language
    notebooks = await db.language_notebooks.find({
        "language_code": language_code
    }).to_list(None)

    result = []
    for notebook in notebooks:
        result.append(NotebookResponse(
            id=str(notebook.get("_id", "")),
            name=notebook["name"],
            description=notebook["description"],
            type=notebook["type"],
            model_type=notebook.get("model_type", "general"),
            version=notebook["version"],
            file_url=notebook["file_url"],
            updated_at=notebook["updated_at"].isoformat()
        ))

    return result

@router.get("/notebooks/file/{language_code}/{filename}")
async def serve_notebook_file(language_code: str, filename: str):
    """Serve notebook files from the voice-lab directory"""

    # Security: only allow specific file extensions
    if not filename.endswith(('.py', '.ipynb', '.md')):
        raise HTTPException(status_code=400, detail="Invalid file type")

    # Map database filenames to actual files - prefer .ipynb, fallback to .py
    file_mapping = {
        "001_phase1_data_acquisition.ipynb": [
            "/opt/kasaai/apps/voice-lab/voice_lab_essential/notebooks/001_phase1_data_acquisition.ipynb",
            "/opt/kasaai/apps/voice-lab/notebooks/process_common_voice_twi.py"
        ],
        "002_enhanced_multi_rate_data_processing.ipynb": [
            "/opt/kasaai/apps/voice-lab/voice_lab_essential/notebooks/002_phase1_data_processing_enhanced.ipynb",
            "/opt/kasaai/apps/voice-lab/notebooks/000_enhanced_twi_processor.py"
        ],
        "010_coqui_training_updated_real_self_contained.ipynb": [
            "/opt/kasaai/apps/voice-lab/notebooks/final/010_coqui_training_with_manifests.ipynb",
            "/opt/kasaai/apps/voice-lab/notebooks/enhanced_twi_processor.py"
        ]
    }

    # Get actual file path - try .ipynb first, then .py
    file_paths = file_mapping.get(filename, [])
    file_path = None
    actual_filename = filename

    for path in file_paths:
        if os.path.exists(path):
            file_path = path
            actual_filename = os.path.basename(path)
            break

    # If no mapped file found, try default locations
    if not file_path:
        base_paths = [
            "/opt/kasaai/apps/voice-lab/notebooks",
            "/opt/kasaai/apps/voice-lab/voice_lab_essential/notebooks",
            "/opt/kasaai/apps/voice-lab/notebooks/final"
        ]
        for base_path in base_paths:
            test_path = os.path.join(base_path, filename)
            if os.path.exists(test_path):
                file_path = test_path
                actual_filename = filename
                break

    # Check if file was found
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Security: ensure the file is within allowed directories
    allowed_paths = [
        "/opt/kasaai/apps/voice-lab/notebooks",
        "/opt/kasaai/apps/voice-lab/voice_lab_essential/notebooks",
        "/opt/kasaai/apps/voice-lab/notebooks/final"
    ]

    is_allowed = any(
        os.path.abspath(file_path).startswith(os.path.abspath(path))
        for path in allowed_paths
    )

    if not is_allowed:
        raise HTTPException(status_code=400, detail="Invalid file path")

    # Return the file
    return FileResponse(
        path=file_path,
        filename=actual_filename,
        media_type='application/octet-stream'
    )