"""
AI API routes for devotional features.
Handles TTS generation, summarization, and scripture explanations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
import logging

from app.services.ai_service import get_ai_service
from app.services.devotional_service import get_devotional_by_id
from app.utils.auth import get_current_user
from app.models.user import TokenData

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== REQUEST/RESPONSE MODELS ====================


class TTSRequest(BaseModel):
    """Request model for TTS generation."""

    provider_id: str = Field(
        "f5tts", description="TTS provider ID (f5tts, coqui_xtts, openai_tts, etc.)"
    )
    voice_id: Optional[str] = Field(None, description="Voice ID (provider-specific)")
    speed: float = Field(1.0, ge=0.5, le=2.0, description="Speech speed (0.5-2.0)")
    language: str = Field("en", description="Language code")
    force_regenerate: bool = Field(False, description="Force regeneration even if cached")


class TTSResponse(BaseModel):
    """Response model for TTS generation."""

    audio_url: str
    duration: float
    cost: float
    provider_used: str
    cached: bool


# ==================== TTS ENDPOINTS ====================


@router.post("/devotionals/{devotional_id}/tts", response_model=TTSResponse)
async def generate_devotional_tts(
    devotional_id: str,
    request: TTSRequest,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Generate text-to-speech audio for a devotional.

    **Path Parameters:**
    - devotional_id: Devotional ID

    **Request Body:**
    - provider_id: TTS provider (default: f5tts)
    - voice_id: Voice ID (optional, uses provider default)
    - speed: Speech speed 0.5-2.0 (default: 1.0)
    - language: Language code (default: en)
    - force_regenerate: Force regeneration (default: false)

    **Returns:**
    - audio_url: URL to MP3 audio file
    - duration: Audio duration in seconds
    - cost: Generation cost in USD
    - provider_used: TTS provider that was used
    - cached: Whether audio was cached

    **Raises:**
    - 404: Devotional not found
    - 500: TTS generation failed

    **Note:**
    - Audio is cached and reused unless force_regenerate=true
    - Falls back to alternative providers if primary fails
    """
    logger.info(f"TTS generation request for devotional {devotional_id} by user {current_user.user_id}")

    # Get devotional
    devotional = await get_devotional_by_id(devotional_id)
    if not devotional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devotional not found",
        )

    # Extract text from content blocks
    text_parts = []
    for block in devotional.content:
        text_parts.append(block.text)

    full_text = " ".join(text_parts)

    if not full_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Devotional has no text content",
        )

    # Get AI service
    ai_service = await get_ai_service()

    try:
        # Generate audio
        result = await ai_service.generate_devotional_audio(
            devotional_id=devotional_id,
            text=full_text,
            user_id=current_user.user_id,
            provider_id=request.provider_id,
            voice_id=request.voice_id,
            speed=request.speed,
            language=request.language,
            force_regenerate=request.force_regenerate,
        )

        logger.info(
            f"TTS generated for devotional {devotional_id}: "
            f"{result['provider_used']}, {result['duration']:.2f}s, ${result['cost']:.4f}"
        )

        return TTSResponse(**result)

    except Exception as e:
        logger.error(f"TTS generation failed for devotional {devotional_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS generation failed: {str(e)}",
        )


# ==================== BIBLE SCRIPTURE ENDPOINTS ====================


class ScriptureRequest(BaseModel):
    """Request model for fetching scripture."""

    reference: str = Field(..., description="Scripture reference (e.g., 'John 3:16')")
    translation: str = Field("kjv", description="Bible translation (kjv, web, oeb-us, etc.)")


class ScriptureResponse(BaseModel):
    """Response model for scripture."""

    reference: str
    text: str
    translation_id: str
    translation_name: str


class BibleTranslation(BaseModel):
    """Bible translation metadata."""

    id: str
    name: str
    abbreviation: str
    language: str
    description: Optional[str] = None


@router.post("/scriptures/fetch", response_model=ScriptureResponse)
async def fetch_scripture_text(request: ScriptureRequest):
    """
    Fetch scripture text from Bible API.
    Public endpoint - no authentication required.

    **Request Body:**
    - reference: Scripture reference (e.g., "John 3:16", "Psalm 23:1-6")
    - translation: Bible translation (default: kjv)

    **Returns:**
    - reference: Normalized scripture reference
    - text: Scripture text
    - translation_id: Translation ID used
    - translation_name: Full translation name
    """
    from app.services.bible_service import fetch_scripture, format_scripture_for_display

    logger.info(f"Fetching scripture: {request.reference} ({request.translation})")

    scripture_data = await fetch_scripture(request.reference, request.translation)

    if not scripture_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not fetch scripture: {request.reference}",
        )

    # Format text for display (remove verse numbers)
    formatted_text = format_scripture_for_display(scripture_data)

    return ScriptureResponse(
        reference=scripture_data["reference"],
        text=formatted_text,
        translation_id=scripture_data["translation_id"],
        translation_name=scripture_data["translation_name"],
    )


@router.get("/scriptures/{reference:path}", response_model=ScriptureResponse)
async def get_scripture(reference: str, translation: str = "kjv"):
    """
    Fetch scripture text (GET version).
    Public endpoint - no authentication required.

    **Path Parameters:**
    - reference: Scripture reference (e.g., "John 3:16", "1 Timothy 1:22")
      Note: Use :path to allow slashes and special characters in the reference

    **Query Parameters:**
    - translation: Bible translation (default: kjv)

    **Returns:**
    - Scripture text and metadata
    """
    from urllib.parse import unquote
    from app.services.bible_service import fetch_scripture, format_scripture_for_display

    # URL decode the reference in case it was double-encoded or has special characters
    reference = unquote(reference)
    reference = reference.strip()

    logger.info(f"Fetching scripture: {reference} ({translation})")

    scripture_data = await fetch_scripture(reference, translation)

    if not scripture_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not fetch scripture: {reference}",
        )

    formatted_text = format_scripture_for_display(scripture_data)

    return ScriptureResponse(
        reference=scripture_data["reference"],
        text=formatted_text,
        translation_id=scripture_data["translation_id"],
        translation_name=scripture_data["translation_name"],
    )


@router.get("/bibles/available", response_model=list[BibleTranslation])
async def get_available_bibles(language: Optional[str] = None):
    """
    Fetch list of available Bible translations from API.Bible.
    Public endpoint - no authentication required.

    **Query Parameters:**
    - language: Filter by language code (e.g., 'eng' for English, 'spa' for Spanish)

    **Returns:**
    - List of available Bible translations with metadata
    """
    from app.services.bible_service import fetch_available_bibles

    logger.info(f"Fetching available Bibles (language: {language or 'all'})")

    bibles = await fetch_available_bibles(language=language)

    return bibles


# ==================== ESV-SPECIFIC ENDPOINTS ====================


class ESVHtmlResponse(BaseModel):
    """Response model for ESV HTML scripture."""

    reference: str
    html: str
    translation_id: str
    translation_name: str


class ESVAudioResponse(BaseModel):
    """Response model for ESV audio URL."""

    reference: str
    audio_url: Optional[str]
    translation_id: str
    translation_name: str


class ESVSearchResult(BaseModel):
    """Individual ESV search result."""

    reference: str
    content: str


class ESVSearchResponse(BaseModel):
    """Response model for ESV search."""

    query: str
    page: int
    total_results: int
    total_pages: int
    results: list[ESVSearchResult]
    translation_id: str
    translation_name: str


# Note: Search endpoint MUST be before parameterized /{reference} routes
@router.get("/esv/search", response_model=ESVSearchResponse)
async def search_esv_bible(
    q: str,
    page_size: int = 20,
    page: int = 1,
):
    """
    Search the ESV Bible for keywords or phrases.
    Public endpoint - no authentication required.

    **Query Parameters:**
    - q: Search query (word or phrase)
    - page_size: Results per page (max 100, default 20)
    - page: Page number (default 1)

    **Returns:**
    - Search results with references and matching content
    """
    from app.services.bible_service import search_esv

    logger.info(f"Searching ESV for: {q}")

    result = await search_esv(q, page_size=page_size, page=page)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Search failed for query: {q}",
        )

    return ESVSearchResponse(
        query=result["query"],
        page=result["page"],
        total_results=result["total_results"],
        total_pages=result.get("total_pages", 0),
        results=[
            ESVSearchResult(reference=r["reference"], content=r["content"])
            for r in result["results"]
        ],
        translation_id=result["translation_id"],
        translation_name=result["translation_name"],
    )


@router.get("/esv/{reference}", response_model=ScriptureResponse)
async def get_esv_scripture(
    reference: str,
    include_verse_numbers: bool = True,
    include_footnotes: bool = False,
    include_headings: bool = False,
):
    """
    Fetch scripture text from ESV API (English Standard Version).
    Public endpoint - no authentication required.

    **Path Parameters:**
    - reference: Scripture reference (e.g., "John 3:16", "Psalm 23:1-6")

    **Query Parameters:**
    - include_verse_numbers: Include verse numbers (default: true)
    - include_footnotes: Include footnote markers (default: false)
    - include_headings: Include section headings (default: false)

    **Returns:**
    - Scripture text from ESV translation
    """
    from app.services.bible_service import fetch_scripture_from_esv, format_scripture_for_display

    logger.info(f"Fetching ESV scripture: {reference}")

    scripture_data = await fetch_scripture_from_esv(
        reference,
        include_verse_numbers=include_verse_numbers,
        include_footnotes=include_footnotes,
        include_headings=include_headings,
    )

    if not scripture_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not fetch ESV scripture: {reference}",
        )

    formatted_text = format_scripture_for_display(scripture_data)

    return ScriptureResponse(
        reference=scripture_data["reference"],
        text=formatted_text,
        translation_id=scripture_data["translation_id"],
        translation_name=scripture_data["translation_name"],
    )


@router.get("/esv/{reference}/html", response_model=ESVHtmlResponse)
async def get_esv_html(
    reference: str,
    include_footnotes: bool = True,
    include_headings: bool = True,
    include_css_link: bool = True,
):
    """
    Fetch scripture as formatted HTML from ESV API.
    Public endpoint - no authentication required.

    **Path Parameters:**
    - reference: Scripture reference (e.g., "John 3:16", "Psalm 23")

    **Query Parameters:**
    - include_footnotes: Include footnotes (default: true)
    - include_headings: Include section headings (default: true)
    - include_css_link: Include ESV stylesheet link (default: true)

    **Returns:**
    - Formatted HTML content with optional CSS styling
    """
    from app.services.bible_service import fetch_esv_html

    logger.info(f"Fetching ESV HTML: {reference}")

    result = await fetch_esv_html(
        reference,
        include_footnotes=include_footnotes,
        include_headings=include_headings,
        include_css_link=include_css_link,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not fetch ESV HTML: {reference}",
        )

    return ESVHtmlResponse(
        reference=result["reference"],
        html=result["html"],
        translation_id=result["translation_id"],
        translation_name=result["translation_name"],
    )


@router.get("/esv/{reference}/audio", response_model=ESVAudioResponse)
async def get_esv_audio(reference: str):
    """
    Get audio URL for scripture passage from ESV API.
    Public endpoint - no authentication required.

    **Path Parameters:**
    - reference: Scripture reference (e.g., "John 3:16", "Psalm 23")

    **Returns:**
    - Audio URL for the scripture passage (MP3 format)
    """
    from app.services.bible_service import fetch_esv_audio_url

    logger.info(f"Fetching ESV audio URL: {reference}")

    result = await fetch_esv_audio_url(reference)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not fetch ESV audio URL: {reference}",
        )

    return ESVAudioResponse(
        reference=result["reference"],
        audio_url=result.get("audio_url"),
        translation_id=result["translation_id"],
        translation_name=result["translation_name"],
    )


# ==================== FUTURE AI ENDPOINTS ====================


# @router.post("/devotionals/{devotional_id}/summarize")
# async def summarize_devotional(
#     devotional_id: str,
#     current_user: TokenData = Depends(get_current_user),
# ):
#     """
#     Generate AI summary of devotional (1 paragraph).
#     Future implementation with GPT-4 or similar.
#     """
#     pass


# @router.post("/scriptures/explain")
# async def explain_scripture(
#     scripture_reference: str,
#     current_user: TokenData = Depends(get_current_user),
# ):
#     """
#     Generate AI explanation of scripture verse.
#     Includes historical context, meaning, and modern application.
#     Future implementation with GPT-4 or similar.
#     """
#     pass


# @router.post("/ai/assist")
# async def ai_writing_assistance(
#     prompt: str,
#     current_user: TokenData = Depends(get_current_pastor),
# ):
#     """
#     AI writing assistance for pastors.
#     Suggests improvements, scripture references, and tone analysis.
#     Future implementation with GPT-4 or similar.
#     """
#     pass
