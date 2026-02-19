from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from pathlib import Path
from uuid import UUID
import sys
import yaml
import logging
import uuid

logger = logging.getLogger(__name__)

from apps.shared.voice_engine import (
    calculate_energy,
    calculate_wer,
    is_silence,
    synthesize_text,
    synthesize_with_voice,
    get_registered_voices,
    transcribe_samples,
    loop_samples,
    barge_in,
    retry_with_fallback,
    redact_pii,
    detect_consent,
    maybe_retain_audio,
)
from ..services.meta_mms_service import mms_service
from ..services.unified_whisper_service import unified_whisper_service
from apps.shared.african_languages import get_country_languages
from apps.shared.meta_mms_languages import (
    get_meta_mms_languages_for_country,
    get_all_meta_mms_languages,
    get_language_display_name,
    is_meta_mms_supported
)
from apps.shared.config.models import SystemConfig
from ..events import event_bus, EventType
from ..models import VoiceTurn, VoiceSession, LLMProvider, LLMModel, VoiceProvider, Voice, Assistant
from ..services import voice_session_service
from ..services.llm_service import llm_service
from ..services.voice_service import voice_service
from ..services.assistant_service import assistant_service
from ..services.openai_service import openai_service
from ..services.unified_llm_service import unified_llm_service
from ..services.knowledge_base_service import knowledge_base_service
from ..services.voice_creation_service import VoiceCreationService
from ..services.model_cache_service import model_cache_service

# Initialize voice creation service
voice_creation_service = VoiceCreationService()

CONFIG_PATH = Path(__file__).resolve().parents[4] / "shared" / "config" / "system.yaml"
try:
    with open(CONFIG_PATH) as f:
        _cfg = SystemConfig(**yaml.safe_load(f))
        LANGUAGE_DETECT_THRESHOLD = _cfg.language_detect_threshold
except Exception:
    LANGUAGE_DETECT_THRESHOLD = 0.5

AVAILABLE_VOICES = {
    "akuapem_female",
    "asante_male",
    "asante_female",
    "ewe_female",
    "ewe_male",
    "ga_male",
    "ga_female",
    "hausa_male",
    "hausa_female",
    "dagbani_male",
    "dagbani_female",
    "yoruba_male",
    "yoruba_female",
    "igbo_male",
    "igbo_female",
    "swahili_male",
    "swahili_female",
    "kikuyu_male",
    "kikuyu_female",
    "luo_male",
    "luo_female",
    "zulu_male",
    "zulu_female",
    "xhosa_male",
    "xhosa_female",
    "afrikaans_male",
    "afrikaans_female",
}

# Database-only configuration - no static providers

LANGUAGES: List[str] = ["English", "Twi", "Asante Twi", "Akuapem Twi", "Ewe", "Ga", "Dagbani", "Hausa", "Yoruba", "Igbo", "Swahili"]
COUNTRIES: List[str] = ["Ghana", "Kenya"]


def validate_selection(
    provider: str, model: str, language: str, voice: str | None = None
) -> None:
    """Validate provider, model, language, and voice selections."""
    # For now, skip validation since we're only using database providers
    # TODO: Implement validation against database providers
    pass


router = APIRouter(prefix="/voice", tags=["voice"])


# Request/Response models for LLM endpoints
class LLMProviderCreate(BaseModel):
    """Request model for creating LLM provider."""
    name: str = Field(..., description="Provider name")
    display_name: str = Field(..., description="Display name")
    description: str = Field(..., description="Provider description")
    website: str = Field(..., description="Provider website")
    api_base_url: str = Field(..., description="API base URL")
    pricing_model: str = Field(..., description="Pricing model")
    features: List[str] = Field(default_factory=list, description="Available features")
    supported_languages: List[str] = Field(default_factory=list, description="Supported languages")
    max_context_length: int = Field(..., description="Maximum context length")


class LLMModelCreate(BaseModel):
    """Request model for creating LLM model."""
    provider_id: str = Field(..., description="Provider ID")
    name: str = Field(..., description="Model name")
    display_name: str = Field(..., description="Display name")
    description: str = Field(..., description="Model description")
    model_type: str = Field(..., description="Model type")
    context_length: int = Field(..., description="Context length")
    input_cost_per_1k_tokens: float = Field(..., description="Input cost per 1K tokens")
    output_cost_per_1k_tokens: float = Field(..., description="Output cost per 1K tokens")
    capabilities: List[str] = Field(default_factory=list, description="Model capabilities")
    supported_languages: List[str] = Field(default_factory=list, description="Supported languages")
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics")


class LLMProviderUpdate(BaseModel):
    """Request model for updating LLM provider."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    api_base_url: Optional[str] = None
    pricing_model: Optional[str] = None
    features: Optional[List[str]] = None
    supported_languages: Optional[List[str]] = None
    max_context_length: Optional[int] = None
    is_active: Optional[bool] = None


class LLMModelUpdate(BaseModel):
    """Request model for updating LLM model."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    model_type: Optional[str] = None
    context_length: Optional[int] = None
    input_cost_per_1k_tokens: Optional[float] = None
    output_cost_per_1k_tokens: Optional[float] = None
    capabilities: Optional[List[str]] = None
    supported_languages: Optional[List[str]] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


# LLM Provider endpoints
@router.get("/llm/providers", response_model=List[LLMProvider])
async def get_llm_providers(active_only: bool = True):
    """Get all LLM providers.
    
    Args:
        active_only: Whether to return only active providers
        
    Returns:
        List of LLM providers
    """
    return await llm_service.get_providers(active_only=active_only)


@router.post("/llm/providers", response_model=LLMProvider)
async def create_llm_provider(provider: LLMProviderCreate):
    """Create a new LLM provider.
    
    Args:
        provider: Provider data
        
    Returns:
        Created provider
    """
    provider_model = LLMProvider(**provider.model_dump())
    return await llm_service.create_provider(provider_model)


@router.get("/llm/providers/{provider_id}", response_model=LLMProvider)
async def get_llm_provider(provider_id: str):
    """Get LLM provider by ID.
    
    Args:
        provider_id: Provider ID
        
    Returns:
        LLM provider
    """
    provider = await llm_service.get_provider_by_id(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.put("/llm/providers/{provider_id}", response_model=LLMProvider)
async def update_llm_provider(provider_id: str, updates: LLMProviderUpdate):
    """Update LLM provider.
    
    Args:
        provider_id: Provider ID
        updates: Fields to update
        
    Returns:
        Updated provider
    """
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    provider = await llm_service.update_provider(provider_id, update_data)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.delete("/llm/providers/{provider_id}")
async def delete_llm_provider(provider_id: str):
    """Delete LLM provider.
    
    Args:
        provider_id: Provider ID
        
    Returns:
        Success message
    """
    success = await llm_service.delete_provider(provider_id)
    if not success:
        raise HTTPException(status_code=404, detail="Provider not found")
    return {"message": "Provider deleted successfully"}


# LLM Model endpoints
@router.get("/llm/models", response_model=List[LLMModel])
async def get_llm_models(provider_id: Optional[str] = None, active_only: bool = True):
    """Get LLM models.
    
    Args:
        provider_id: Optional provider ID to filter by
        active_only: Whether to return only active models
        
    Returns:
        List of LLM models
    """
    return await llm_service.get_models(provider_id=provider_id, active_only=active_only)


@router.post("/llm/models", response_model=LLMModel)
async def create_llm_model(model: LLMModelCreate):
    """Create a new LLM model.
    
    Args:
        model: Model data
        
    Returns:
        Created model
    """
    model_data = model.model_dump()
    model_obj = LLMModel(**model_data)
    return await llm_service.create_model(model_obj)


@router.get("/llm/models/{model_id}", response_model=LLMModel)
async def get_llm_model(model_id: str):
    """Get LLM model by ID.
    
    Args:
        model_id: Model ID
        
    Returns:
        LLM model
    """
    model = await llm_service.get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.put("/llm/models/{model_id}", response_model=LLMModel)
async def update_llm_model(model_id: str, updates: LLMModelUpdate):
    """Update LLM model.
    
    Args:
        model_id: Model ID
        updates: Fields to update
        
    Returns:
        Updated model
    """
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    model = await llm_service.update_model(model_id, update_data)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.delete("/llm/models/{model_id}")
async def delete_llm_model(model_id: str):
    """Delete LLM model.
    
    Args:
        model_id: Model ID
        
    Returns:
        Success message
    """
    success = await llm_service.delete_model(model_id)
    if not success:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"message": "Model deleted successfully"}


@router.get("/llm/providers/{provider_id}/models", response_model=List[LLMModel])
async def get_provider_models(provider_id: str):
    """Get all models for a specific provider.
    
    Args:
        provider_id: Provider ID
        
    Returns:
        List of models for the provider
    """
    return await llm_service.get_provider_models(provider_id)


@router.get("/llm/default-model", response_model=LLMModel)
async def get_default_model():
    """Get the default LLM model.
    
    Returns:
        Default model
    """
    model = await llm_service.get_default_model()
    if not model:
        raise HTTPException(status_code=404, detail="No default model found")
    return model


@router.post("/llm/models/{model_id}/set-default")
async def set_default_model(model_id: str):
    """Set a model as the default.
    
    Args:
        model_id: Model ID to set as default
        
    Returns:
        Success message
    """
    success = await llm_service.set_default_model(model_id)
    if not success:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"message": "Default model updated successfully"}


# Updated options endpoint to include LLM data
# This endpoint is now handled by the OptionsResponse version below


async def _record_turn(
    endpoint: str,
    request: Dict[str, Any],
    response: Dict[str, Any],
    session_id: UUID | None,
) -> None:
    """Persist a request/response pair if ``session_id`` is provided."""

    if session_id is None:
        return
    
    # Get the current turn number for this session
    session = voice_session_service.get_session(session_id)
    turn_number = session.total_turns + 1 if session else 1
    
    # Create VoiceTurn with the correct fields
    turn = VoiceTurn(
        session_id=str(session_id),
        turn_number=turn_number,
        user_text=request.get("text", ""),
        assistant_text=response.get("reply", ""),
        stt_provider=request.get("stt_provider", ""),
        stt_model=request.get("stt_model", ""),
        tts_provider=request.get("tts_provider", ""),
        tts_voice=request.get("tts_voice", ""),
        llm_provider=request.get("llm_provider", ""),
        llm_model=request.get("llm_model", ""),
        language=request.get("language", ""),
        country=request.get("country", ""),
        confidence=request.get("confidence", 0.0),
        duration_ms=request.get("duration_ms", 0)
    )
    
    voice_session_service.append_turn(session_id, turn)


# In-memory language setting for demo purposes.
CURRENT_LANGUAGE = "Twi"


class OptionsResponse(BaseModel):
    """Available voice and language configuration options."""

    stt: Dict[str, List[str]]
    tts: Dict[str, List[str]]
    llm: Dict[str, List[str]] # Changed to Dict[str, List[str]] for provider-model mapping
    languages: List[str]
    countries: List[str]


@router.get("/options", response_model=OptionsResponse)
async def get_options() -> OptionsResponse:
    """Return available STT/TTS/LLM providers, languages and countries."""

    # Get LLM providers and models from database
    providers = await llm_service.get_providers()
    models = await llm_service.get_models()
    
    # Group models by provider
    llm_providers = {}
    for provider in providers:
        provider_models = [model for model in models if model.provider_id == provider.id]
        llm_providers[provider.name] = [model.name for model in provider_models]

    # Get voice providers from database
    voice_providers = await voice_service.get_providers(active_only=True)
    stt_providers = await voice_service.get_providers(active_only=True, provider_type="STT")
    tts_providers = await voice_service.get_providers(active_only=True, provider_type="TTS")
    
    # Convert to the expected format
    stt_dict = {p.name: [] for p in stt_providers}  # Empty list for models since we don't have them in voice providers
    tts_dict = {p.name: [] for p in tts_providers}

    return OptionsResponse(
        stt=stt_dict,
        tts=tts_dict,
        llm=llm_providers,
        languages=LANGUAGES,
        countries=COUNTRIES,
    )


class EnergyRequest(BaseModel):
    """Request payload containing PCM16 samples."""

    samples: List[int]


class EnergyResponse(BaseModel):
    """Normalized RMS energy response."""

    energy: float


@router.post("/energy", response_model=EnergyResponse)
async def get_energy(
    payload: EnergyRequest, session_id: UUID | None = None
) -> EnergyResponse:
    """Compute RMS energy for provided samples."""

    resp = EnergyResponse(energy=calculate_energy(payload.samples))
    await _record_turn("energy", payload.model_dump(), resp.model_dump(), session_id)
    return resp


class EchoRequest(BaseModel):
    """Audio payload that will be echoed back."""

    samples: List[int]


class EchoResponse(BaseModel):
    """Response containing the same samples that were provided."""

    samples: List[int]


@router.post("/echo", response_model=EchoResponse)
async def echo_audio(
    payload: EchoRequest, session_id: UUID | None = None
) -> EchoResponse:
    """Return audio samples unchanged to enable echo testing.

    Args:
        payload (EchoRequest): Incoming audio samples.

    Returns:
        EchoResponse: The same audio samples for playback.
    """

    resp = EchoResponse(samples=payload.samples)
    await _record_turn("echo", payload.model_dump(), resp.model_dump(), session_id)
    return resp


class VADResponse(BaseModel):
    """Voice activity detection result."""

    energy: float
    voice: bool


@router.post("/vad", response_model=VADResponse)
async def detect_voice(
    payload: EnergyRequest, session_id: UUID | None = None
) -> VADResponse:
    """Detect if provided samples contain voice activity.

    Args:
        payload (EnergyRequest): Incoming audio samples.

    Returns:
        VADResponse: Energy value and whether voice was detected.
    """

    energy = calculate_energy(payload.samples)
    resp = VADResponse(energy=energy, voice=not is_silence(payload.samples))
    await _record_turn("vad", payload.model_dump(), resp.model_dump(), session_id)
    return resp


class LanguagesResponse(BaseModel):
    """Available languages for a given country."""

    country: str
    languages: List[str]


@router.get("/languages", response_model=LanguagesResponse)
async def list_languages(
    country: str, session_id: UUID | None = None
) -> LanguagesResponse:
    """Return supported languages for a country across Africa and emerging markets.

    Args:
        country (str): Country name.

    Returns:
        LanguagesResponse: Country and its languages.

    Raises:
        HTTPException: If ``country`` is not supported.
    """

    try:
        languages = get_country_languages(country)
    except KeyError as exc:  # pragma: no cover - mapped to HTTP error
        raise HTTPException(status_code=404, detail="country not supported") from exc
    resp = LanguagesResponse(country=country.title(), languages=languages)
    await _record_turn("languages", {"country": country}, resp.model_dump(), session_id)
    return resp


class LanguageSelection(BaseModel):
    """Manually selected session language."""

    language: str = Field(min_length=1)


@router.get("/language", response_model=LanguageSelection)
async def get_language(session_id: UUID | None = None) -> LanguageSelection:
    """Return the current session language."""

    resp = LanguageSelection(language=CURRENT_LANGUAGE)
    await _record_turn("language_get", {}, resp.model_dump(), session_id)
    return resp


@router.post("/language", response_model=LanguageSelection)
async def set_language(
    selection: LanguageSelection, session_id: UUID | None = None
) -> LanguageSelection:
    """Persist a new session language selection."""

    global CURRENT_LANGUAGE
    CURRENT_LANGUAGE = selection.language
    await _record_turn(
        "language_set", selection.model_dump(), selection.model_dump(), session_id
    )
    return selection


class TranscribeRequest(BaseModel):
    """Audio samples to be converted into text."""

    samples: List[int]


class TranscribeResponse(BaseModel):
    """Partial and final transcript."""

    partials: List[str]
    text: str
    language: Optional[str] = None
    confidence: Optional[float] = None


@router.post("/stt", response_model=TranscribeResponse)
async def transcribe_audio(
    payload: TranscribeRequest, session_id: UUID | None = None
) -> TranscribeResponse:
    """Convert PCM16 samples into a simulated transcript.

    Args:
        payload (TranscribeRequest): Incoming audio samples.

    Returns:
        TranscribeResponse: List of partial transcripts and final text.
    """

    # Convert each sample to a Unicode character. This stub treats the samples
    # as direct character codes rather than performing real STT.
    # Reason: keeps Demo 4 lightweight while providing deterministic output.
    partials, text, language, confidence = transcribe_samples(
        payload.samples, detect_language=True
    )

    if language and confidence is not None and confidence >= LANGUAGE_DETECT_THRESHOLD:
        event_bus.emit(
            EventType.LANGUAGE_DETECTED, language=language, confidence=confidence
        )

    resp = TranscribeResponse(
        partials=partials,
        text=text,
        language=language,
        confidence=confidence,
    )
    await _record_turn("stt", payload.model_dump(), resp.model_dump(), session_id)
    return resp


class LLMRequest(BaseModel):
    """Text input to the language model."""

    text: str = Field(min_length=1)


class LLMResponse(BaseModel):
    """Generated reply from the language model."""

    text: str
    provider: str
    model: str
    tokens_used: int
    cost_estimate: float


@router.post("/llm", response_model=LLMResponse)
async def generate_reply(payload: LLMRequest) -> LLMResponse:
    """Return a real LLM reply for provided text."""

    try:
        # Use OpenAI as default provider
        messages = [{"role": "user", "content": payload.text}]
        
        llm_response = await unified_llm_service.chat_completion(
            messages=messages,
            provider="openai",
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=200
        )
        
        response_text = llm_response["text"]
        tokens_used = llm_response["usage"]["total_tokens"]
        cost_estimate = tokens_used * 0.00001  # Rough estimate
        
        return LLMResponse(
            text=response_text,
            provider=llm_response["provider"].capitalize(),
            model=llm_response["model"],
            tokens_used=tokens_used,
            cost_estimate=cost_estimate
        )
        
    except Exception as e:
        logger.error(f"LLM service error: {e}")
        # Fallback to simple response
        response_text = f"Echo: {payload.text}"
        return LLMResponse(
            text=response_text,
            provider="OpenAI",
            model="GPT-4o",
            tokens_used=len(payload.text.split()) + len(response_text.split()),
            cost_estimate=0.001
        )


class LoopRequest(BaseModel):
    """Audio samples to be transcribed and spoken back."""

    samples: List[int]
    provider: str
    model: str
    voice: str
    language: str


class LoopResponse(BaseModel):
    """Transcription and synthesized audio samples."""

    samples: List[int]
    partials: List[str]
    text: str


@router.post("/loop", response_model=LoopResponse)
async def voice_loop(
    payload: LoopRequest, session_id: UUID | None = None
) -> LoopResponse:
    """Transcribe audio samples and synthesize the transcript back to audio.

    Args:
        payload (LoopRequest): Incoming audio samples.

    Returns:
        LoopResponse: Synthesized samples, partial transcripts, and text.
    """

    validate_selection(payload.provider, payload.model, payload.language, payload.voice)
    samples, partials, text = loop_samples(payload.samples)
    resp = LoopResponse(samples=samples, partials=partials, text=text)
    await _record_turn("loop", payload.model_dump(), resp.model_dump(), session_id)
    return resp


class BargeRequest(BaseModel):
    """Existing TTS audio and new microphone samples."""

    tts: List[int]
    incoming: List[int]


class BargeResponse(BaseModel):
    """Remaining TTS samples after possible interruption."""

    samples: List[int]
    interrupted: bool


@router.post("/barge", response_model=BargeResponse)
async def detect_barge(
    payload: BargeRequest, session_id: UUID | None = None
) -> BargeResponse:
    """Stop TTS playback if new speech is detected.

    Args:
        payload (BargeRequest): Currently playing TTS samples and new audio input.

    Returns:
        BargeResponse: Remaining samples and whether an interruption occurred.
    """

    samples, interrupted = barge_in(payload.tts, payload.incoming)
    resp = BargeResponse(samples=samples, interrupted=interrupted)
    await _record_turn("barge", payload.model_dump(), resp.model_dump(), session_id)
    return resp


class RetryRequest(BaseModel):
    """Parameters to simulate retries and fallback."""

    text: str = Field(min_length=1)
    failures: int = 0
    retries: int = 3
    fallback_text: str = Field(default="fallback")


class RetryResponse(BaseModel):
    """Resulting samples and whether fallback was used."""

    samples: List[int]
    fallback: bool


@router.post("/retry", response_model=RetryResponse)
async def retry_tts(
    payload: RetryRequest, session_id: UUID | None = None
) -> RetryResponse:
    """Synthesize text with retry and fallback logic.

    Args:
        payload (RetryRequest): Text, simulated failure count, retry limit, and fallback text.

    Returns:
        RetryResponse: Generated samples and if the fallback path executed.
    """

    attempts = {"count": 0}  # Reason: allow nested function to modify attempt count

    def operation() -> List[int]:
        attempts["count"] += 1
        if attempts["count"] <= payload.failures:
            raise RuntimeError("simulated failure")
        return synthesize_text(payload.text)

    def fallback() -> List[int]:
        return synthesize_text(payload.fallback_text)

    samples, used_fallback = retry_with_fallback(
        operation, fallback, retries=payload.retries
    )
    resp = RetryResponse(samples=samples, fallback=used_fallback)
    await _record_turn("retry", payload.model_dump(), resp.model_dump(), session_id)
    return resp


class TTSRequest(BaseModel):
    """Text to be synthesized with a selected voice."""

    text: str = Field(min_length=1)
    voice: str = Field(default="akuapem_female")


class TTSResponse(BaseModel):
    """Synthetic PCM16 samples representing the input text."""

    samples: List[int]


@router.post("/tts", response_model=TTSResponse)
async def synthesize_audio(
    payload: TTSRequest, session_id: UUID | None = None
) -> TTSResponse:
    """Convert text into simulated PCM16 audio samples.

    Args:
        payload (TTSRequest): Text and voice to synthesize.

    Returns:
        TTSResponse: PCM16 sample list representing the provided text.

    Raises:
        HTTPException: If ``payload.voice`` is not supported.
    """

    # Use default voice if none provided or if voice is not supported
    voice_to_use = payload.voice
    if not voice_to_use or (
        voice_to_use not in AVAILABLE_VOICES
        and voice_to_use not in get_registered_voices()
    ):
        voice_to_use = "akuapem_female"  # Default voice
        
    resp = TTSResponse(samples=synthesize_with_voice(payload.text, voice_to_use))
    await _record_turn("tts", payload.model_dump(), resp.model_dump(), session_id)
    return resp


class WERRequest(BaseModel):
    """Reference and hypothesis transcripts for WER calculation."""

    reference: str = Field(min_length=1)
    hypothesis: str


class WERResponse(BaseModel):
    """Word error rate between reference and hypothesis."""

    wer: float


@router.post("/wer", response_model=WERResponse)
async def compute_wer(
    payload: WERRequest, session_id: UUID | None = None
) -> WERResponse:
    """Compute word error rate for a transcript pair."""

    resp = WERResponse(wer=calculate_wer(payload.reference, payload.hypothesis))
    await _record_turn("wer", payload.model_dump(), resp.model_dump(), session_id)
    return resp


class ComplianceRequest(BaseModel):
    """Transcript and audio for compliance checks."""

    text: str = Field(min_length=1)
    samples: List[int] = Field(default_factory=list)
    retain_audio: bool = False


class ComplianceResponse(BaseModel):
    """Redacted transcript, consent flag, and optional audio."""

    redacted: str
    consent: bool
    audio: List[int]


@router.post("/compliance", response_model=ComplianceResponse)
async def compliance_check(
    payload: ComplianceRequest, session_id: UUID | None = None
) -> ComplianceResponse:
    """Redact PII, detect consent, and optionally return audio samples."""

    redacted = redact_pii(payload.text)
    consent = detect_consent(payload.text)
    audio = maybe_retain_audio(payload.samples, payload.retain_audio)
    resp = ComplianceResponse(redacted=redacted, consent=consent, audio=audio)
    await _record_turn(
        "compliance", payload.model_dump(), resp.model_dump(), session_id
    )
    return resp


@router.get("/sessions/{session_id}", response_model=VoiceSession)
async def get_session(session_id: UUID) -> VoiceSession:
    """Return a stored voice session."""

    session = voice_session_service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    
    return session


# LLM Provider and Model endpoints
@router.get("/llm/providers", response_model=List[LLMProvider])
async def get_llm_providers(active_only: bool = True) -> List[LLMProvider]:
    """Get all available LLM providers.
    
    Args:
        active_only: Whether to return only active providers
        
    Returns:
        List of LLM providers
    """
    return await llm_service.get_providers(active_only=active_only)


@router.get("/llm/providers/{provider_id}", response_model=LLMProvider)
async def get_llm_provider(provider_id: str) -> LLMProvider:
    """Get a specific LLM provider by ID.
    
    Args:
        provider_id: Provider ID
        
    Returns:
        LLM provider
        
    Raises:
        HTTPException: If provider not found
    """
    provider = await llm_service.get_provider_by_id(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.get("/llm/models", response_model=List[LLMModel])
async def get_llm_models(
    provider_id: Optional[str] = None, 
    active_only: bool = True
) -> List[LLMModel]:
    """Get available LLM models.
    
    Args:
        provider_id: Optional provider ID to filter by
        active_only: Whether to return only active models
        
    Returns:
        List of LLM models
    """
    return await llm_service.get_models(provider_id=provider_id, active_only=active_only)


@router.get("/llm/models/{model_id}", response_model=LLMModel)
async def get_llm_model(model_id: str) -> LLMModel:
    """Get a specific LLM model by ID.
    
    Args:
        model_id: Model ID
        
    Returns:
        LLM model
        
    Raises:
        HTTPException: If model not found
    """
    model = await llm_service.get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.get("/llm/providers/{provider_id}/models", response_model=List[LLMModel])
async def get_provider_models(provider_id: str) -> List[LLMModel]:
    """Get all models for a specific provider.
    
    Args:
        provider_id: Provider ID
        
    Returns:
        List of models for the provider
        
    Raises:
        HTTPException: If provider not found
    """
    provider = await llm_service.get_provider_by_id(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    return await llm_service.get_provider_models(provider_id)


@router.get("/llm/default", response_model=LLMModel)
async def get_default_llm_model() -> LLMModel:
    """Get the default LLM model.
    
    Returns:
        Default LLM model
        
    Raises:
        HTTPException: If no default model is set
    """
    model = await llm_service.get_default_model()
    if not model:
        raise HTTPException(status_code=404, detail="No default model set")
    return model


class LLMRequest(BaseModel):
    """Request for LLM interaction."""
    
    text: str = Field(..., min_length=1, description="Input text for the LLM")
    provider_id: Optional[str] = Field(None, description="LLM provider ID")
    model_id: Optional[str] = Field(None, description="LLM model ID")
    system_prompt: Optional[str] = Field(None, description="System prompt")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for generation")
    max_tokens: int = Field(default=1000, ge=1, le=4000, description="Maximum tokens to generate")


class LLMResponse(BaseModel):
    """Response from LLM interaction."""
    
    text: str = Field(..., description="Generated text from LLM")
    provider: str = Field(..., description="Provider used")
    model: str = Field(..., description="Model used")
    tokens_used: int = Field(..., description="Tokens used in the interaction")
    cost_estimate: float = Field(..., description="Estimated cost in USD")


@router.post("/llm/chat", response_model=LLMResponse)
async def chat_with_llm(
    payload: LLMRequest, 
    session_id: UUID | None = None
) -> LLMResponse:
    """Chat with an LLM model.
    
    Args:
        payload: LLM request parameters
        session_id: Optional session ID for tracking
        
    Returns:
        LLM response with generated text and metadata
        
    Raises:
        HTTPException: If model or provider not found
    """
    try:
        # Get the model to use
        if payload.model_id:
            model = await llm_service.get_model_by_id(payload.model_id)
            if not model:
                raise HTTPException(status_code=404, detail="Model not found")
        else:
            # Use default model
            model = await llm_service.get_default_model()
            if not model:
                raise HTTPException(status_code=404, detail="No default model set")
        
        # Get the provider
        provider = await llm_service.get_provider_by_id(model.provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        # Check if OpenAI service is available
        if not openai_service.is_available():
            # Fallback to mock response if OpenAI is not available
            response_text = f"Echo: {payload.text}"
            tokens_used = len(payload.text.split()) + len(response_text.split())
            cost_estimate = (
                tokens_used * model.input_cost_per_1k_tokens / 1000 +
                len(response_text.split()) * model.output_cost_per_1k_tokens / 1000
            )
            
            response = LLMResponse(
                text=response_text,
                provider=provider.display_name,
                model=model.display_name,
                tokens_used=tokens_used,
                cost_estimate=cost_estimate
            )
        else:
            # Use OpenAI service for actual LLM interaction
            messages = [{"role": "user", "content": payload.text}]
            
            # Use system prompt if provided in the model configuration
            system_prompt = None
            if hasattr(model, 'system_prompt') and model.system_prompt:
                system_prompt = model.system_prompt
            
            # Map model names to OpenAI models
            openai_model = "gpt-4o-mini"  # Default
            if "gpt-4" in model.name.lower():
                openai_model = "gpt-4o-mini"
            elif "gpt-3" in model.name.lower():
                openai_model = "gpt-3.5-turbo"
            
            # Call OpenAI
            openai_response = await openai_service.chat_completion(
                messages=messages,
                model=openai_model,
                temperature=0.7,
                system_prompt=system_prompt
            )
            
            # Calculate cost estimate
            usage = openai_response["usage"]
            tokens_used = usage["total_tokens"]
            cost_estimate = (
                usage["prompt_tokens"] * model.input_cost_per_1k_tokens / 1000 +
                usage["completion_tokens"] * model.output_cost_per_1k_tokens / 1000
            )
            
            response = LLMResponse(
                text=openai_response["text"],
                provider=provider.display_name,
                model=model.display_name,
                tokens_used=tokens_used,
                cost_estimate=cost_estimate
            )
        
        # Record the turn if session_id is provided
        await _record_turn("llm_chat", payload.model_dump(), response.model_dump(), session_id)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in LLM chat: {e}")
        raise HTTPException(status_code=500, detail=f"LLM chat failed: {str(e)}")


# Voice Provider endpoints
@router.get("/voice/providers", response_model=List[VoiceProvider])
async def get_voice_providers(active_only: bool = True, provider_type: Optional[str] = None):
    """Get all voice providers.
    
    Args:
        active_only: Whether to return only active providers
        provider_type: Filter by provider type (STT, TTS, or both)
        
    Returns:
        List of voice providers
    """
    return await voice_service.get_providers(active_only=active_only, provider_type=provider_type)


@router.get("/voice/providers/{provider_id}", response_model=VoiceProvider)
async def get_voice_provider(provider_id: str):
    """Get a specific voice provider by ID.
    
    Args:
        provider_id: Provider ID
        
    Returns:
        Voice provider
    """
    providers = await voice_service.get_providers(active_only=False)
    provider = next((p for p in providers if p.id == provider_id), None)
    if not provider:
        raise HTTPException(status_code=404, detail="Voice provider not found")
    return provider


# Voice endpoints
@router.get("/voices", response_model=List[Voice])
async def get_voices(
    provider_id: Optional[str] = None,
    language: Optional[str] = None,
    voice_type: Optional[str] = None,
    active_only: bool = True
):
    """Get all voices with optional filtering.
    
    Args:
        provider_id: Filter by provider ID
        language: Filter by language code
        voice_type: Filter by voice type
        active_only: Whether to return only active voices
        
    Returns:
        List of voices
    """
    return await voice_service.get_voices(
        provider_id=provider_id,
        language=language,
        voice_type=voice_type,
        active_only=active_only
    )


@router.get("/voices/{voice_id}", response_model=Voice)
async def get_voice(voice_id: str):
    """Get a specific voice by ID.
    
    Args:
        voice_id: Voice ID
        
    Returns:
        Voice
    """
    voices = await voice_service.get_voices(active_only=False)
    voice = next((v for v in voices if v.id == voice_id), None)
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    return voice


class VoiceAgentConfig(BaseModel):
    """Complete voice agent configuration for frontend."""
    
    stt_providers: List[VoiceProvider] = Field(..., description="Available STT providers")
    tts_providers: List[VoiceProvider] = Field(..., description="Available TTS providers")
    voice_providers: List[VoiceProvider] = Field(..., description="All voice providers")
    voices: List[Voice] = Field(..., description="Available TTS voices")
    llm_providers: List[LLMProvider] = Field(..., description="Available LLM providers")
    llm_models: List[LLMModel] = Field(..., description="Available LLM models")
    languages: List[str] = Field(..., description="Supported languages")
    countries: List[str] = Field(..., description="Supported countries")
    default_config: Dict[str, str] = Field(..., description="Default configuration")


@router.get("/agent/config", response_model=VoiceAgentConfig)
async def get_voice_agent_config() -> VoiceAgentConfig:
    """Get complete voice agent configuration for frontend.

    Returns:
        Complete configuration including all providers, models, languages, and defaults
    """
    # Get LLM providers and models
    llm_providers = await llm_service.get_providers(active_only=True)
    llm_models = await llm_service.get_models(active_only=True)

    # Get voice providers and voices
    voice_providers = await voice_service.get_providers(active_only=True)
    stt_providers = await voice_service.get_providers(active_only=True, provider_type="STT")
    tts_providers = await voice_service.get_providers(active_only=True, provider_type="TTS")
    voices = await voice_service.get_voices(active_only=True)
    
    # Only use database providers - no static fallbacks

    # Get default model and voice
    default_model = await llm_service.get_default_model()
    default_voice = await voice_service.get_default_voice("elevenlabs", "en") if tts_providers else None

    # Build default configuration
    default_config = {
        "stt_provider": "openai",
        "stt_model": "gpt-4o-transcribe",
        "tts_provider": default_voice.provider_id if default_voice else "elevenlabs",
        "tts_voice": default_voice.id if default_voice else "adam",
        "llm_provider": default_model.provider_id if default_model else "",
        "llm_model": default_model.id if default_model else "",
        "language": "en",
        "country": "US"
    }

    return VoiceAgentConfig(
        stt_providers=[provider.model_dump() for provider in stt_providers] if stt_providers else [],
        tts_providers=[provider.model_dump() for provider in tts_providers] if tts_providers else [],
        voice_providers=[provider.model_dump() for provider in voice_providers] if voice_providers else [],
        voices=[voice.model_dump() for voice in voices] if voices else [],
        llm_providers=[provider.model_dump() for provider in llm_providers] if llm_providers else [],
        llm_models=[model.model_dump() for model in llm_models] if llm_models else [],
        languages=["en", "es", "fr", "de", "it", "pt", "pl", "hi", "ja", "ko", "zh", "ar", "ru", "tr", "twi", "yo", "sw", "xh", "ee", "gaa"],
        countries=["US", "ES", "FR", "DE", "IT", "PT", "PL", "IN", "JP", "KR", "CN", "SA", "RU", "TR", "Ghana", "Nigeria", "Kenya", "South Africa", "Togo"],
        default_config=default_config
    )


# Assistant Management Endpoints

class AssistantCreateRequest(BaseModel):
    """Request model for creating an assistant."""
    name: str = Field(..., description="Assistant name")
    description: str = Field(default="", description="Assistant description")
    user_id: str = Field(..., description="User ID")
    template_id: str = Field(default="blank", description="Template ID")
    
    # Model Configuration
    llm_provider: str = Field(default="", description="LLM provider")
    llm_model: str = Field(default="", description="LLM model")
    first_message_mode: str = Field(default="assistant_first", description="First message mode")
    first_message: str = Field(default="", description="First message text")
    system_prompt: str = Field(default="", description="System prompt")
    
    # Voice Configuration
    tts_provider: str = Field(default="", description="TTS provider")
    tts_voice: str = Field(default="", description="TTS voice")
    language: str = Field(default="en", description="Primary language")
    country: str = Field(default="US", description="Primary country")
    
    # Voice Parameters
    background_sound: str = Field(default="default", description="Background sound setting")
    background_sound_url: str = Field(default="", description="Background sound URL")
    input_min_characters: int = Field(default=30, description="Minimum input characters")
    punctuation_boundaries: str = Field(default="", description="Punctuation boundaries")
    stability: float = Field(default=0.5, description="Voice stability (0-1)")
    clarity_similarity: float = Field(default=0.75, description="Clarity and similarity (0-1)")
    speed: float = Field(default=1.0, description="Voice speed (0.5-2)")
    style_exaggeration: float = Field(default=0.0, description="Style exaggeration (0-1)")
    optimize_streaming_latency: float = Field(default=0.0, description="Optimize streaming latency (0-1)")
    
    # Transcriber Configuration
    stt_provider: str = Field(default="", description="STT provider")
    stt_model: str = Field(default="", description="STT model")
    stt_language: str = Field(default="", description="STT language")
    stt_country: str = Field(default="", description="STT country")
    stt_detect: bool = Field(default=True, description="Enable language detection")
    background_denoising: bool = Field(default=False, description="Enable background denoising")
    confidence_threshold: float = Field(default=0.4, description="Confidence threshold (0-1)")
    use_numerals: bool = Field(default=False, description="Use numerals in transcription")
    
    # Files/Knowledge Base
    knowledge_base_files: List[str] = Field(default_factory=list, description="Knowledge base file IDs")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Assistant metadata")


class AssistantUpdateRequest(BaseModel):
    """Request model for updating an assistant."""
    name: Optional[str] = None
    description: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    first_message_mode: Optional[str] = None
    first_message: Optional[str] = None
    system_prompt: Optional[str] = None
    tts_provider: Optional[str] = None
    tts_voice: Optional[str] = None
    language: Optional[str] = None
    country: Optional[str] = None
    background_sound: Optional[str] = None
    background_sound_url: Optional[str] = None
    input_min_characters: Optional[int] = None
    punctuation_boundaries: Optional[str] = None
    stability: Optional[float] = None
    clarity_similarity: Optional[float] = None
    speed: Optional[float] = None
    style_exaggeration: Optional[float] = None
    optimize_streaming_latency: Optional[float] = None
    stt_provider: Optional[str] = None
    stt_model: Optional[str] = None
    background_denoising: Optional[bool] = None
    confidence_threshold: Optional[float] = None
    use_numerals: Optional[bool] = None
    knowledge_base_files: Optional[List[str]] = None


@router.post("/assistants")
async def create_assistant(assistant_data: AssistantCreateRequest) -> Dict[str, Any]:
    """Create a new assistant.
    
    Args:
        assistant_data: Assistant creation data
        
    Returns:
        Created assistant
    """
    try:
        # Create assistant with full configuration
        assistant = Assistant(
            name=assistant_data.name,
            description=assistant_data.description,
            user_id=assistant_data.user_id,
            template_id=assistant_data.template_id,
            
            # Model Configuration
            llm_provider=assistant_data.llm_provider,
            llm_model=assistant_data.llm_model,
            first_message_mode=assistant_data.first_message_mode,
            first_message=assistant_data.first_message,
            system_prompt=assistant_data.system_prompt,
            
            # Voice Configuration
            tts_provider=assistant_data.tts_provider,
            tts_voice=assistant_data.tts_voice,
            language=assistant_data.language,
            country=assistant_data.country,
            
            # Voice Parameters
            background_sound=assistant_data.background_sound,
            background_sound_url=assistant_data.background_sound_url,
            input_min_characters=assistant_data.input_min_characters,
            punctuation_boundaries=assistant_data.punctuation_boundaries,
            stability=assistant_data.stability,
            clarity_similarity=assistant_data.clarity_similarity,
            speed=assistant_data.speed,
            style_exaggeration=assistant_data.style_exaggeration,
            optimize_streaming_latency=assistant_data.optimize_streaming_latency,
            
            # Transcriber Configuration
            stt_provider=assistant_data.stt_provider,
            stt_model=assistant_data.stt_model,
            background_denoising=assistant_data.background_denoising,
            confidence_threshold=assistant_data.confidence_threshold,
            use_numerals=assistant_data.use_numerals,
            
            # Files/Knowledge Base
            knowledge_base_files=assistant_data.knowledge_base_files,
            
            # Metadata
            metadata=assistant_data.metadata
        )
        
        created_assistant = assistant_service.create_assistant(assistant)
        
        return {
            "success": True,
            "assistant": created_assistant.model_dump(),
            "message": f"Assistant '{assistant_data.name}' created successfully with {assistant_data.language} configuration"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create assistant: {str(e)}")


@router.get("/assistants")
async def get_assistants(user_id: str) -> Dict[str, Any]:
    """Get all assistants for a user.
    
    Args:
        user_id: User ID
        
    Returns:
        List of assistants
    """
    try:
        assistants = assistant_service.get_assistants_by_user(user_id)
        
        return {
            "success": True,
            "assistants": [assistant.model_dump() for assistant in assistants]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get assistants: {str(e)}")


@router.get("/meta-mms/languages/{country}")
async def get_meta_mms_languages(country: str):
    """Get Meta MMS supported languages for a specific country.
    
    Args:
        country (str): Country name
        
    Returns:
        Dict: List of supported languages with ISO 639-3 codes
    """
    try:
        if country.lower() == "all":
            # Return all Meta MMS supported languages
            all_languages = get_all_meta_mms_languages()
            return {
                "success": True,
                "languages": all_languages,
                "count": len(all_languages)
            }
        else:
            # Return languages for specific country
            country_languages = get_meta_mms_languages_for_country(country)
            return {
                "success": True,
                "country": country,
                "languages": country_languages,
                "count": len(country_languages)
            }
    except Exception as e:
        logger.error(f"Error getting Meta MMS languages for {country}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting Meta MMS languages: {str(e)}")

@router.get("/assistants/{assistant_id}")
async def get_assistant(assistant_id: str) -> Dict[str, Any]:
    """Get a specific assistant.
    
    Args:
        assistant_id: Assistant ID
        
    Returns:
        Assistant details
    """
    try:
        assistant = assistant_service.get_assistant(assistant_id)
        
        if not assistant:
            raise HTTPException(status_code=404, detail="Assistant not found")
        
        return {
            "success": True,
            "assistant": assistant.model_dump()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get assistant: {str(e)}")


@router.put("/assistants/{assistant_id}")
async def update_assistant(assistant_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update an assistant.
    
    Args:
        assistant_id: Assistant ID
        updates: Update data
        
    Returns:
        Updated assistant
    """
    try:
        updated_assistant = assistant_service.update_assistant(assistant_id, updates)
        
        if not updated_assistant:
            raise HTTPException(status_code=404, detail="Assistant not found")
        
        return {
            "success": True,
            "assistant": updated_assistant.model_dump(),
            "message": "Assistant updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update assistant: {str(e)}")


@router.post("/assistants/{assistant_id}/publish")
async def publish_assistant(assistant_id: str, configuration: Dict[str, Any]) -> Dict[str, Any]:
    """Publish an assistant with configuration.
    
    Args:
        assistant_id: Assistant ID
        configuration: Assistant configuration
        
    Returns:
        Published assistant
    """
    try:
        published_assistant = assistant_service.publish_assistant(assistant_id, configuration)
        
        if not published_assistant:
            raise HTTPException(status_code=404, detail="Assistant not found")
        
        return {
            "success": True,
            "assistant": published_assistant.model_dump(),
            "message": "Assistant published successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish assistant: {str(e)}")


@router.delete("/assistants/{assistant_id}")
async def delete_assistant(assistant_id: str) -> Dict[str, Any]:
    """Delete an assistant.
    
    Args:
        assistant_id: Assistant ID
        
    Returns:
        Deletion result
    """
    try:
        success = assistant_service.delete_assistant(assistant_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Assistant not found")
        
        return {
            "success": True,
            "message": "Assistant deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete assistant: {str(e)}")


@router.post("/assistants/{assistant_id}/knowledge-base/upload")
async def upload_knowledge_base_file(
    assistant_id: str,
    file_content: str,
    file_name: str,
    user_id: str
) -> Dict[str, Any]:
    """Upload a knowledge base file for an assistant.
    
    Args:
        assistant_id: Assistant ID
        file_content: File content
        file_name: File name
        user_id: User ID
        
    Returns:
        Upload result
    """
    try:
        success = await assistant_service.add_knowledge_base_file(
            assistant_id=assistant_id,
            file_content=file_content,
            file_name=file_name,
            user_id=user_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Assistant not found")
        
        return {
            "success": True,
            "message": "Knowledge base file uploaded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload knowledge base file: {str(e)}")


@router.post("/assistants/{assistant_id}/knowledge-base/search")
async def search_knowledge_base(
    assistant_id: str,
    query: str,
    user_id: str
) -> Dict[str, Any]:
    """Search the knowledge base for an assistant.
    
    Args:
        assistant_id: Assistant ID
        query: Search query
        user_id: User ID
        
    Returns:
        Search results
    """
    try:
        results = await assistant_service.search_knowledge_base(
            assistant_id=assistant_id,
            query=query,
            user_id=user_id
        )
        
        return {
            "success": True,
            "results": results,
            "query": query
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search knowledge base: {str(e)}")


@router.get("/assistants/{assistant_id}/knowledge-base/files")
async def get_knowledge_base_files(
    assistant_id: str,
    user_id: str
) -> Dict[str, Any]:
    """Get knowledge base files for an assistant.
    
    Args:
        assistant_id: Assistant ID
        user_id: User ID
        
    Returns:
        Knowledge base files
    """
    try:
        assistant = assistant_service.get_assistant(assistant_id)
        
        if not assistant:
            raise HTTPException(status_code=404, detail="Assistant not found")
        
        # Get sources from Supabase
        sources = await knowledge_base_service.get_sources(user_id)
        
        # Filter sources that belong to this assistant
        assistant_sources = [
            source for source in sources 
            if source.id in assistant.knowledge_base_files
        ]
        
        return {
            "success": True,
            "files": [source.model_dump() for source in assistant_sources]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get knowledge base files: {str(e)}")


@router.get("/assistants/default-config")
async def get_default_assistant_config() -> Dict[str, Any]:
    """Get default assistant configuration for Twi voice agent.
    
    Returns:
        Default configuration
    """
    try:
        default_config = assistant_service.get_default_twi_config()
        
        return {
            "success": True,
            "config": default_config,
            "message": "Default Twi voice agent configuration"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get default config: {str(e)}")


@router.get("/whisper/implementation")
async def get_whisper_implementation() -> Dict[str, Any]:
    """Get information about the current Whisper implementation.
    
    Returns:
        Implementation information
    """
    return unified_whisper_service.get_implementation_info()


# Meta MMS and Whisper Transcription Endpoints

class TranscriptionRequest(BaseModel):
    """Request model for transcription."""
    audio_path: str = Field(..., description="Path to audio file")
    language: str = Field(default="auto", description="Language code (e.g., 'twi', 'ewe', 'ga')")
    task: str = Field(default="transcribe", description="Task type ('transcribe' or 'translate')")
    model_size: str = Field(default="base", description="Model size for Whisper")
    prompt: str = Field(default=None, description="Optional prompt for better transcription")


class TranscriptionResponse(BaseModel):
    """Response model for transcription."""
    text: str = Field(..., description="Transcribed text")
    language: str = Field(..., description="Detected or specified language")
    confidence: float = Field(..., description="Confidence score")
    duration: float = Field(..., description="Audio duration")
    segments: List[Dict[str, Any]] = Field(default_factory=list, description="Transcription segments")
    task: str = Field(..., description="Task performed")
    provider: str = Field(..., description="Provider used")


@router.post("/transcribe/mms", response_model=TranscriptionResponse)
async def transcribe_with_mms(request: TranscriptionRequest) -> TranscriptionResponse:
    """Transcribe audio using Meta MMS model.
    
    Args:
        request: Transcription request with audio path and options
        
    Returns:
        TranscriptionResponse with results
    """
    try:
        # Initialize MMS service if not already done
        if not mms_service.models_loaded:
            await mms_service.initialize()
        
        # Transcribe audio
        result = await mms_service.transcribe_audio(
            audio_path=request.audio_path,
            language=request.language,
            task=request.task
        )
        
        return TranscriptionResponse(
            text=result.text,
            language=result.language,
            confidence=result.confidence,
            duration=result.duration,
            segments=result.segments,
            task=request.task,
            provider="meta_mms"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MMS transcription failed: {str(e)}")


@router.post("/transcribe/whisper", response_model=TranscriptionResponse)
async def transcribe_with_whisper(request: TranscriptionRequest) -> TranscriptionResponse:
    """Transcribe audio using Unified Whisper model.
    
    Args:
        request: Transcription request with audio path and options
        
    Returns:
        TranscriptionResponse with results
    """
    try:
        # Initialize Whisper service if not already done
        if not unified_whisper_service.service.models_loaded:
            await unified_whisper_service.initialize(request.model_size)
        
        # Transcribe audio
        result = await unified_whisper_service.transcribe_audio(
            audio_path=request.audio_path,
            language=request.language,
            task=request.task,
            model_size=request.model_size,
            prompt=request.prompt
        )
        
        return TranscriptionResponse(
            text=result.text,
            language=result.language,
            confidence=result.confidence,
            duration=result.duration,
            segments=result.segments,
            task=result.task,
            provider=result.implementation
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Whisper transcription failed: {str(e)}")


@router.post("/translate/whisper", response_model=TranscriptionResponse)
async def translate_with_whisper(request: TranscriptionRequest) -> TranscriptionResponse:
    """Translate audio to English using Unified Whisper model.
    
    Args:
        request: Translation request with audio path and options
        
    Returns:
        TranscriptionResponse with translation results
    """
    try:
        # Initialize Whisper service if not already done
        if not unified_whisper_service.service.models_loaded:
            await unified_whisper_service.initialize(request.model_size)
        
        # Translate audio
        result = await unified_whisper_service.translate_audio(
            audio_path=request.audio_path,
            target_language="en",
            model_size=request.model_size
        )
        
        return TranscriptionResponse(
            text=result.text,
            language="en",  # Target language is always English
            confidence=result.confidence,
            duration=result.duration,
            segments=result.segments,
            task="translate",
            provider=result.implementation
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Whisper translation failed: {str(e)}")


@router.post("/detect-language/mms")
async def detect_language_mms(audio_path: str) -> Dict[str, str]:
    """Detect language of audio using Meta MMS model.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Detected language code
    """
    try:
        # Initialize MMS service if not already done
        if not mms_service.models_loaded:
            await mms_service.initialize()
        
        # Detect language
        detected_lang = await mms_service.detect_language(audio_path)
        
        return {"language": detected_lang, "provider": "meta_mms"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MMS language detection failed: {str(e)}")


@router.post("/detect-language/whisper")
async def detect_language_whisper(audio_path: str, model_size: str = "base") -> Dict[str, str]:
    """Detect language of audio using Unified Whisper model.
    
    Args:
        audio_path: Path to audio file
        model_size: Whisper model size
        
    Returns:
        Detected language code
    """
    try:
        # Initialize Whisper service if not already done
        if not unified_whisper_service.service.models_loaded:
            await unified_whisper_service.initialize(model_size)
        
        # Detect language
        detected_lang = await unified_whisper_service.detect_language(audio_path, model_size)
        
        return {"language": detected_lang, "provider": unified_whisper_service.implementation}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Whisper language detection failed: {str(e)}")


@router.get("/languages/mms")
async def get_mms_supported_languages() -> Dict[str, List[str]]:
    """Get list of languages supported by Meta MMS.
    
    Returns:
        List of supported languages
    """
    try:
        languages = mms_service.get_supported_languages()
        return {
            "provider": "meta_mms",
            "languages": languages,
            "total_count": len(languages)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get MMS languages: {str(e)}")


@router.get("/languages/whisper")
async def get_whisper_supported_languages() -> Dict[str, List[str]]:
    """Get list of languages supported by Unified Whisper.
    
    Returns:
        List of supported languages
    """
    try:
        languages = unified_whisper_service.get_supported_ghanaian_languages()
        return {
            "provider": unified_whisper_service.implementation,
            "languages": languages,
            "total_count": len(languages)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Whisper languages: {str(e)}")


@router.get("/models/whisper")
async def get_whisper_models() -> Dict[str, Any]:
    """Get information about available Whisper models.
    
    Returns:
        Whisper model information
    """
    try:
        models = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
        model_info = {}
        
        for model_size in models:
            try:
                info = await unified_whisper_service.get_model_info(model_size)
                model_info[model_size] = info
            except Exception as e:
                model_info[model_size] = {"error": str(e)}
        
        return {
            "provider": unified_whisper_service.implementation,
            "models": model_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Whisper models: {str(e)}")


@router.post("/synthesize/mms")
async def synthesize_with_mms(text: str, language: str, voice_id: str = None) -> Dict[str, Any]:
    """Synthesize speech using Meta MMS TTS model.
    
    Args:
        text: Text to synthesize
        language: Language code
        voice_id: Optional voice identifier
        
    Returns:
        Synthesis result
    """
    try:
        # Initialize MMS service if not already done
        if not mms_service.models_loaded:
            await mms_service.initialize()
        
        # Synthesize speech
        result = await mms_service.synthesize_speech(
            text=text,
            language=language,
            voice_id=voice_id
        )
        
        return {
            "audio_path": result.audio_path,
            "duration": result.duration,
            "language": result.language,
            "text": result.text,
            "provider": "meta_mms"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MMS synthesis failed: {str(e)}")


@router.post("/batch-transcribe/whisper")
async def batch_transcribe_whisper(
    audio_files: List[str],
    language: str = "auto",
    task: str = "transcribe",
    model_size: str = "base"
) -> List[TranscriptionResponse]:
    """Transcribe multiple audio files using Unified Whisper.
    
    Args:
        audio_files: List of audio file paths
        language: Language code
        task: Task type
        model_size: Whisper model size
        
    Returns:
        List of transcription results
    """
    try:
        # Initialize Whisper service if not already done
        if not unified_whisper_service.service.models_loaded:
            await unified_whisper_service.initialize(model_size)
        
        # Batch transcribe
        results = await unified_whisper_service.batch_transcribe(
            audio_files=audio_files,
            language=language,
            task=task,
            model_size=model_size
        )
        
        # Convert to response format
        responses = []
        for i, result in enumerate(results):
            if result:
                responses.append(TranscriptionResponse(
                    text=result.text,
                    language=result.language,
                    confidence=result.confidence,
                    duration=result.duration,
                    segments=result.segments,
                    task=result.task,
                    provider=result.implementation
                ))
            else:
                responses.append(TranscriptionResponse(
                    text="",
                    language="unknown",
                    confidence=0.0,
                    duration=0.0,
                    segments=[],
                    task=task,
                    provider=unified_whisper_service.implementation
                ))
        
        return responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Whisper batch transcription failed: {str(e)}")


class VoiceAssistantRequest(BaseModel):
    """Request for voice assistant conversation."""
    
    user_text: str
    assistant_id: str
    system_prompt: str = ""
    first_message: str = ""
    llm_provider: str
    llm_model: str
    tts_provider: str
    tts_voice: str
    stt_provider: str
    stt_model: str
    language: str = "en"
    conversation_history: List[dict] = []


class VoiceAssistantResponse(BaseModel):
    """Response from voice assistant conversation."""
    
    assistant_reply: str
    audio_samples: List[int]
    conversation_id: str
    tokens_used: int = 0
    cost_estimate: float = 0.0


@router.post("/assistant/chat", response_model=VoiceAssistantResponse)
async def voice_assistant_chat(payload: VoiceAssistantRequest) -> VoiceAssistantResponse:
    """Handle voice assistant conversation using selected configuration."""
    
    try:
        # Prepare conversation messages for LLM
        messages = []
        
        # Add conversation history (last 5 messages to keep context manageable)
        for msg in payload.conversation_history[-5:]:
            role = "user" if msg['type'] == 'user' else "assistant"
            messages.append({
                "role": role,
                "content": msg['text']
            })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": payload.user_text
        })
        
        # Generate LLM response using the selected provider and model
        try:
            llm_response = await unified_llm_service.chat_completion(
                messages=messages,
                provider=payload.llm_provider,
                model=payload.llm_model,
                system_prompt=payload.system_prompt if payload.system_prompt else None,
                temperature=0.7,
                max_tokens=500  # Reasonable limit for voice responses
            )
            
            assistant_reply = llm_response["text"]
            tokens_used = llm_response["usage"]["total_tokens"]
            
            # Estimate cost (rough calculation)
            cost_estimate = tokens_used * 0.00001  # Very rough estimate
            
        except Exception as llm_error:
            logger.error(f"LLM service error: {llm_error}")
            # Fallback to simple response if LLM fails
            assistant_reply = f"I understand you said: '{payload.user_text}'. How can I help you further?"
            tokens_used = len(assistant_reply.split()) + len(payload.user_text.split())
            cost_estimate = 0.001
        
        # Generate TTS audio using the selected voice
        audio_samples = synthesize_with_voice(assistant_reply, payload.tts_voice)
        
        # Generate conversation ID
        conversation_id = str(uuid.uuid4())
        
        return VoiceAssistantResponse(
            assistant_reply=assistant_reply,
            audio_samples=audio_samples,
            conversation_id=conversation_id,
            tokens_used=tokens_used,
            cost_estimate=cost_estimate
        )
        
    except Exception as e:
        logger.error(f"Error in voice assistant chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Voice assistant error: {str(e)}")


# Voice Creation and Cloning Endpoints

class VoiceCreationRequest(BaseModel):
    """Request model for voice creation."""
    
    text: str = Field(..., description="Text to synthesize")
    language: str = Field(default="en", description="Target language (en, twi, aka, ewe, ga, etc.)")
    accent: str = Field(default="neutral", description="Target accent (ghanaian, kenyan, nigerian, etc.)")
    voice_type: str = Field(default="female", description="Voice gender (male, female)")
    model: str = Field(default="openvoice_v2", description="TTS model to use")
    reference_audio: Optional[str] = Field(None, description="Base64 encoded reference audio for cloning")
    voice_id: Optional[str] = Field(None, description="Existing voice ID to use")
    emotion: str = Field(default="neutral", description="Emotional tone (neutral, happy, sad, excited)")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed multiplier")
    pitch_shift: float = Field(default=0.0, ge=-12.0, le=12.0, description="Pitch shift in semitones")
    quality: str = Field(default="medium", description="Quality level (low, medium, high)")


class VoiceCloneRequest(BaseModel):
    """Request model for voice cloning from audio upload."""
    
    audio_data: str = Field(..., description="Base64 encoded audio file")
    voice_name: str = Field(..., description="Name for the cloned voice")
    language: str = Field(default="en", description="Primary language for the voice")
    description: str = Field(default="", description="Description of the voice")
    user_id: str = Field(..., description="User ID who owns the voice")


class VoiceTrainingRequest(BaseModel):
    """Request model for voice training from dataset."""
    
    dataset_id: str = Field(..., description="ID of the dataset to use for training")
    voice_name: str = Field(..., description="Name for the trained voice")
    language: str = Field(..., description="Primary language for the voice")
    user_id: str = Field(..., description="User ID who owns the voice")
    training_config: Dict[str, Any] = Field(default_factory=dict, description="Training configuration")


class VoiceSynthesisRequest(BaseModel):
    """Request model for speech synthesis with custom voice."""
    
    voice_id: str = Field(..., description="ID of the voice to use")
    text: str = Field(..., description="Text to synthesize")
    language: Optional[str] = Field(None, description="Language override")


@router.get("/voice-creation/datasets")
async def get_available_datasets():
    """Get list of available training datasets.
    
    Returns:
        Dict of available datasets with metadata
    """
    try:
        datasets = voice_creation_service.get_available_datasets()
        
        return {
            "success": True,
            "datasets": datasets,
            "total_count": len(datasets)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get datasets: {str(e)}")


@router.post("/voice-creation/clone")
async def clone_voice(request: VoiceCloneRequest):
    """Clone a voice from uploaded audio.
    
    Args:
        request: Voice cloning request with audio data and metadata
        
    Returns:
        Voice metadata and cloning results
    """
    try:
        # Decode base64 audio data
        import base64
        audio_bytes = base64.b64decode(request.audio_data)
        
        # Clone the voice
        voice_metadata = await voice_creation_service.clone_voice_from_audio(
            audio_file=audio_bytes,
            voice_name=request.voice_name,
            language=request.language,
            description=request.description,
            user_id=request.user_id
        )
        
        return {
            "success": True,
            "voice": voice_metadata,
            "message": f"Voice '{request.voice_name}' cloned successfully"
        }
        
    except Exception as e:
        logger.error(f"Voice cloning failed: {e}")
        raise HTTPException(status_code=500, detail=f"Voice cloning failed: {str(e)}")


@router.post("/voice-creation/train")
async def train_voice(request: VoiceTrainingRequest):
    """Train a voice using a selected dataset.
    
    Args:
        request: Voice training request with dataset and configuration
        
    Returns:
        Training job information
    """
    try:
        # Start voice training
        voice_metadata = await voice_creation_service.train_voice_from_dataset(
            dataset_id=request.dataset_id,
            voice_name=request.voice_name,
            language=request.language,
            training_config=request.training_config,
            user_id=request.user_id
        )
        
        return {
            "success": True,
            "voice": voice_metadata,
            "message": f"Voice training started for '{request.voice_name}'"
        }
        
    except Exception as e:
        logger.error(f"Voice training failed: {e}")
        raise HTTPException(status_code=500, detail=f"Voice training failed: {str(e)}")


@router.get("/voice-creation/voices/{voice_id}")
async def get_voice_info(voice_id: str):
    """Get information about a specific voice.
    
    Args:
        voice_id: ID of the voice to get info for
        
    Returns:
        Voice metadata and status
    """
    try:
        voice_info = await voice_creation_service.get_voice_info(voice_id)
        
        return {
            "success": True,
            "voice": voice_info
        }
        
    except Exception as e:
        logger.error(f"Failed to get voice info: {e}")
        raise HTTPException(status_code=404, detail=f"Voice not found: {str(e)}")


@router.get("/voice-creation/voices/{voice_id}/progress")
async def get_training_progress(voice_id: str):
    """Get training progress for a voice.
    
    Args:
        voice_id: ID of the voice being trained
        
    Returns:
        Training progress information
    """
    try:
        progress = await voice_creation_service.get_training_progress(voice_id)
        
        return {
            "success": True,
            "progress": progress
        }
        
    except Exception as e:
        logger.error(f"Failed to get training progress: {e}")
        raise HTTPException(status_code=404, detail=f"Voice not found: {str(e)}")


@router.post("/voice-creation/synthesize")
async def synthesize_with_custom_voice(request: VoiceSynthesisRequest):
    """Synthesize speech using a custom voice.
    
    Args:
        request: Synthesis request with voice ID and text
        
    Returns:
        Generated audio data
    """
    try:
        # Synthesize speech with custom voice
        audio, sample_rate = await voice_creation_service.synthesize_with_voice(
            voice_id=request.voice_id,
            text=request.text,
            language=request.language
        )
        
        # Convert numpy array to list for JSON serialization
        audio_samples = audio.tolist() if hasattr(audio, 'tolist') else audio
        
        return {
            "success": True,
            "audio_samples": audio_samples,
            "sample_rate": sample_rate,
            "voice_id": request.voice_id,
            "text": request.text
        }
        
    except Exception as e:
        logger.error(f"Voice synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Voice synthesis failed: {str(e)}")


@router.get("/voice-creation/voices")
async def list_user_voices(user_id: str):
    """List all voices created by a user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        List of user's voices
    """
    try:
        voices = await voice_creation_service.list_user_voices(user_id)
        
        return {
            "success": True,
            "voices": voices,
            "total_count": len(voices)
        }
        
    except Exception as e:
        logger.error(f"Failed to list user voices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list voices: {str(e)}")


@router.delete("/voice-creation/voices/{voice_id}")
async def delete_voice(voice_id: str, user_id: Optional[str] = None):
    """Delete a custom voice.
    
    Args:
        voice_id: ID of the voice to delete
        user_id: Optional user ID for ownership verification
        
    Returns:
        Deletion confirmation
    """
    try:
        success = await voice_creation_service.delete_voice(voice_id, user_id)
        
        if success:
            return {
                "success": True,
                "message": f"Voice {voice_id} deleted successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to delete voice")
            
    except Exception as e:
        logger.error(f"Voice deletion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Voice deletion failed: {str(e)}")


@router.get("/voice-creation/models")
async def get_voice_creation_models():
    """Get information about available voice creation models.
    
    Returns:
        Model information and capabilities
    """
    try:
        # This would come from the voice creation service
        models = {
            "openvoice_v2": {
                "name": "OpenVoice V2",
                "description": "Advanced voice cloning with emotion control",
                "supports_cloning": True,
                "supports_emotions": True,
                "languages": ["en", "es", "fr", "zh", "ja", "ko"],
                "quality": "high",
                "latency": "medium"
            },
            "meta_mms": {
                "name": "Meta MMS",
                "description": "Multilingual TTS supporting 1000+ languages",
                "supports_cloning": False,
                "supports_emotions": False,
                "languages": ["twi", "aka", "ewe", "ga", "dag", "hau", "yo", "ig", "sw"],
                "quality": "medium",
                "latency": "fast"
            },
            "coqui_xtts": {
                "name": "Coqui XTTS-v2",
                "description": "Cross-lingual voice cloning and synthesis",
                "supports_cloning": True,
                "supports_emotions": True,
                "languages": ["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh", "ja", "hu", "ko"],
                "quality": "high",
                "latency": "slow"
            },
            "abena_ai": {
                "name": "Abena AI",
                "description": "Specialized African language TTS",
                "supports_cloning": False,
                "supports_emotions": False,
                "languages": ["twi", "ga", "pidgin"],
                "quality": "high",
                "latency": "fast"
            }
        }
        
        return {
            "success": True,
            "models": models,
            "total_count": len(models)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")


@router.get("/voice-creation/accents")
async def get_available_accents():
    """Get list of available accent profiles.
    
    Returns:
        Available accent profiles with metadata
    """
    try:
        accents = {
            "ghanaian_english": {
                "name": "Ghanaian English",
                "language": "English",
                "country": "Ghana",
                "description": "Natural Ghanaian English accent with local pronunciation patterns"
            },
            "asante_twi": {
                "name": "Asante Twi",
                "language": "Twi",
                "country": "Ghana", 
                "region": "Ashanti",
                "description": "Traditional Asante Twi dialect from the Ashanti region"
            },
            "akuapem_twi": {
                "name": "Akuapem Twi",
                "language": "Twi",
                "country": "Ghana",
                "region": "Eastern",
                "description": "Akuapem Twi dialect from the Eastern region"
            },
            "kenyan_english": {
                "name": "Kenyan English",
                "language": "English",
                "country": "Kenya",
                "description": "Kenyan English accent with local speech patterns"
            },
            "nigerian_english": {
                "name": "Nigerian English",
                "language": "English", 
                "country": "Nigeria",
                "description": "Nigerian English accent variations"
            }
        }
        
        return {
            "success": True,
            "accents": accents,
            "total_count": len(accents)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get accents: {str(e)}")


# Model Cache and Fallback Endpoints

@router.get("/model-cache/stats")
async def get_model_cache_stats():
    """Get model cache statistics and status.
    
    Returns:
        Cache statistics including loaded models and usage
    """
    try:
        stats = model_cache_service.get_cache_stats()
        
        return {
            "success": True,
            "cache_stats": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


@router.get("/model-cache/models")
async def get_model_info():
    """Get information about available models and their configurations.
    
    Returns:
        Model information and availability status
    """
    try:
        info = model_cache_service.get_model_info()
        
        return {
            "success": True,
            "model_info": info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")


@router.post("/model-cache/load/{model_key}")
async def load_model(model_key: str):
    """Load a specific model into cache.
    
    Args:
        model_key: Key identifying the model to load
        
    Returns:
        Load status and timing information
    """
    try:
        import time
        start_time = time.time()
        
        success = await model_cache_service.load_model(model_key)
        load_time = time.time() - start_time
        
        if success:
            return {
                "success": True,
                "message": f"Model {model_key} loaded successfully",
                "load_time": load_time,
                "model_key": model_key
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to load model {model_key}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model loading error: {str(e)}")


@router.post("/model-cache/synthesize")
async def synthesize_with_cache(
    text: str,
    language: str = "twi",
    quality: str = "high"
):
    """Synthesize speech using cached models with fallback.
    
    Args:
        text: Text to synthesize
        language: Preferred language for synthesis
        quality: Desired quality level (high, medium, low)
        
    Returns:
        Generated audio with model information
    """
    try:
        result = await model_cache_service.synthesize_with_fallback(
            text=text,
            preferred_language=language,
            voice_quality=quality
        )
        
        return {
            "success": result.get("success", True),
            "audio_samples": result.get("audio_samples", []),
            "sample_rate": result.get("sample_rate", 22050),
            "text": result.get("text", text),
            "model_used": result.get("model_used"),
            "model_type": result.get("model_type"),
            "fallback_attempts": result.get("fallback_attempts", 0),
            "note": result.get("note")
        }
        
    except Exception as e:
        logger.error(f"Cached synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


@router.delete("/model-cache/clear")
async def clear_model_cache(model_key: Optional[str] = None):
    """Clear model cache.
    
    Args:
        model_key: Optional specific model to clear, or all if not provided
        
    Returns:
        Cache clearing confirmation
    """
    try:
        await model_cache_service.clear_cache(model_key)
        
        message = f"Cleared cache for {model_key}" if model_key else "Cleared all model cache"
        
        return {
            "success": True,
            "message": message,
            "model_key": model_key
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache clearing failed: {str(e)}")


@router.post("/voice/synthesize-smart")
async def smart_voice_synthesis(
    text: str,
    language: str = "twi",
    accent: str = "ghanaian", 
    quality: str = "high",
    fallback_enabled: bool = True
):
    """Smart voice synthesis with automatic model selection and fallbacks.
    
    This endpoint automatically selects the best available model for the requested
    language and quality, with intelligent fallbacks if the primary model fails.
    
    Args:
        text: Text to synthesize
        language: Target language (twi, ewe, hausa, en)
        accent: Target accent (ghanaian, kenyan, nigerian)
        quality: Quality level (high, medium, low) 
        fallback_enabled: Whether to use fallback models if primary fails
        
    Returns:
        Generated audio with detailed model information
    """
    try:
        if fallback_enabled:
            # Use smart caching with fallbacks
            result = await model_cache_service.synthesize_with_fallback(
                text=text,
                preferred_language=language,
                voice_quality=quality
            )
        else:
            # Try direct synthesis without fallbacks
            model_key = model_cache_service._select_best_model(language, quality)
            result = await model_cache_service._synthesize_with_model(text, model_key)
            result["model_used"] = model_key
            result["fallback_attempts"] = 0
        
        # Add accent information
        result["accent_requested"] = accent
        result["language_requested"] = language
        result["quality_requested"] = quality
        
        return {
            "success": result.get("success", True),
            "audio_samples": result.get("audio_samples", []),
            "sample_rate": result.get("sample_rate", 22050),
            "text": result.get("text", text),
            "model_used": result.get("model_used"),
            "model_type": result.get("model_type"),
            "fallback_attempts": result.get("fallback_attempts", 0),
            "accent_requested": accent,
            "language_requested": language,
            "quality_requested": quality,
            "processing_info": {
                "fallback_enabled": fallback_enabled,
                "note": result.get("note")
            }
        }
        
    except Exception as e:
        logger.error(f"Smart synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Smart synthesis failed: {str(e)}")
