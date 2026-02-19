"""
Core voice processing routes - STT, TTS, energy, language detection, etc.
"""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from .models import (
    EnergyRequest, EnergyResponse, EchoRequest, EchoResponse, VADResponse,
    LanguagesResponse, LanguageSelection, TranscribeRequest, TranscribeResponse,
    SynthesizeRequest, SynthesizeResponse, OptionsResponse, LoopRequest, LoopResponse,
    BargeInRequest, BargeInResponse, FallbackRequest, FallbackResponse,
    ConsentRequest, ConsentResponse, RetentionRequest, RetentionResponse,
    OfflineModeRequest, OfflineModeResponse
)
from .utils import record_turn, validate_audio_samples, validate_text_input, sanitize_language_code
from .constants import CURRENT_LANGUAGE

from apps.shared.voice_engine import (
    calculate_energy, is_silence, synthesize_text, synthesize_with_voice,
    get_registered_voices, transcribe_samples, loop_samples, barge_in,
    retry_with_fallback, redact_pii, detect_consent, maybe_retain_audio
)
from apps.shared.african_languages import get_country_languages
from apps.shared.meta_mms_languages import (
    get_meta_mms_languages_for_country, get_all_meta_mms_languages,
    get_language_display_name, is_meta_mms_supported
)
from ...services.meta_mms_service import mms_service
from ...services.unified_whisper_service import unified_whisper_service
from ...services.model_cache_service import model_cache_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["voice-core"])


@router.get("/options", response_model=OptionsResponse)
async def get_options() -> OptionsResponse:
    """
    Return available provider and model combinations.
    
    Returns:
        OptionsResponse: Available providers and models
    """
    try:
        # Get registered voice options from voice engine
        voice_options = get_registered_voices()
        
        resp = OptionsResponse(providers=voice_options)
        await record_turn("options", {}, resp.model_dump(), None)
        return resp
    except Exception as e:
        logger.error(f"Failed to get voice options: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve voice options")


@router.post("/energy", response_model=EnergyResponse)
async def get_energy(
    payload: EnergyRequest, session_id: Optional[UUID] = None
) -> EnergyResponse:
    """
    Calculate energy of provided audio samples.
    
    Args:
        payload: Audio samples to analyze
        session_id: Optional session ID for tracking
        
    Returns:
        EnergyResponse: Calculated energy value
    """
    try:
        if not validate_audio_samples(payload.samples):
            raise HTTPException(status_code=400, detail="Invalid audio samples")
            
        energy = calculate_energy(payload.samples)
        resp = EnergyResponse(energy=energy)
        await record_turn("energy", payload.model_dump(), resp.model_dump(), session_id)
        return resp
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate energy: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate energy")


@router.post("/echo", response_model=EchoResponse)
async def echo_audio(
    payload: EchoRequest, session_id: Optional[UUID] = None
) -> EchoResponse:
    """
    Echo back the provided audio samples.
    
    Args:
        payload: Audio samples to echo
        session_id: Optional session ID for tracking
        
    Returns:
        EchoResponse: Echoed audio samples
    """
    try:
        if not validate_audio_samples(payload.samples):
            raise HTTPException(status_code=400, detail="Invalid audio samples")
            
        resp = EchoResponse(samples=payload.samples)
        await record_turn("echo", payload.model_dump(), resp.model_dump(), session_id)
        return resp
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to echo audio: {e}")
        raise HTTPException(status_code=500, detail="Failed to echo audio")


@router.post("/vad", response_model=VADResponse)
async def detect_voice(
    payload: EnergyRequest, session_id: Optional[UUID] = None
) -> VADResponse:
    """
    Detect if provided samples contain voice activity.
    
    Args:
        payload: Audio samples to analyze
        session_id: Optional session ID for tracking
        
    Returns:
        VADResponse: Energy value and whether voice was detected
    """
    try:
        if not validate_audio_samples(payload.samples):
            raise HTTPException(status_code=400, detail="Invalid audio samples")
            
        energy = calculate_energy(payload.samples)
        voice_detected = not is_silence(payload.samples)
        
        resp = VADResponse(energy=energy, voice=voice_detected)
        await record_turn("vad", payload.model_dump(), resp.model_dump(), session_id)
        return resp
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to detect voice activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to detect voice activity")


@router.get("/languages", response_model=LanguagesResponse)
async def list_languages(
    country: str, session_id: Optional[UUID] = None
) -> LanguagesResponse:
    """
    Return supported languages for a country across Africa and emerging markets.
    
    Args:
        country: Country name
        session_id: Optional session ID for tracking
        
    Returns:
        LanguagesResponse: Country and its languages
        
    Raises:
        HTTPException: If country is not supported
    """
    try:
        languages = get_country_languages(country)
        resp = LanguagesResponse(country=country.title(), languages=languages)
        await record_turn("languages", {"country": country}, resp.model_dump(), session_id)
        return resp
    except KeyError:
        raise HTTPException(status_code=404, detail="Country not supported")
    except Exception as e:
        logger.error(f"Failed to get languages for country {country}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve languages")


@router.get("/language", response_model=LanguageSelection)
async def get_language(session_id: Optional[UUID] = None) -> LanguageSelection:
    """
    Return the current session language.
    
    Args:
        session_id: Optional session ID for tracking
        
    Returns:
        LanguageSelection: Current language
    """
    try:
        resp = LanguageSelection(language=CURRENT_LANGUAGE)
        await record_turn("language_get", {}, resp.model_dump(), session_id)
        return resp
    except Exception as e:
        logger.error(f"Failed to get current language: {e}")
        raise HTTPException(status_code=500, detail="Failed to get current language")


@router.post("/language", response_model=LanguageSelection)
async def set_language(
    selection: LanguageSelection, session_id: Optional[UUID] = None
) -> LanguageSelection:
    """
    Persist a new session language selection.
    
    Args:
        selection: Language selection
        session_id: Optional session ID for tracking
        
    Returns:
        LanguageSelection: Updated language selection
    """
    try:
        # Sanitize language code
        sanitized_language = sanitize_language_code(selection.language)
        selection.language = sanitized_language
        
        # Update global current language (TODO: Replace with proper session management)
        global CURRENT_LANGUAGE
        CURRENT_LANGUAGE = sanitized_language
        
        await record_turn("language_set", selection.model_dump(), selection.model_dump(), session_id)
        return selection
    except Exception as e:
        logger.error(f"Failed to set language: {e}")
        raise HTTPException(status_code=500, detail="Failed to set language")


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    payload: TranscribeRequest, 
    provider: str = "whisper",
    model: str = "base",
    language: Optional[str] = None,
    session_id: Optional[UUID] = None
) -> TranscribeResponse:
    """
    Transcribe audio samples to text using STT.
    
    Args:
        payload: Audio samples to transcribe
        provider: STT provider to use
        model: STT model to use
        language: Target language (optional)
        session_id: Optional session ID for tracking
        
    Returns:
        TranscribeResponse: Transcription result
    """
    try:
        if not validate_audio_samples(payload.samples):
            raise HTTPException(status_code=400, detail="Invalid audio samples")
        
        # Use cached model service for better performance
        try:
            transcript, confidence = await model_cache_service.transcribe(
                payload.samples, provider, model, language
            )
        except Exception as cache_error:
            logger.warning(f"Cache service failed, falling back to direct transcription: {cache_error}")
            transcript, confidence = await transcribe_samples(
                payload.samples, provider, model
            )
        
        # Detect language if not specified
        detected_language = None
        if not language:
            try:
                detected_language = sanitize_language_code(CURRENT_LANGUAGE)
            except Exception:
                detected_language = "en"
        
        resp = TranscribeResponse(
            transcript=transcript,
            is_final=True,
            confidence=confidence,
            language_detected=detected_language
        )
        
        await record_turn("transcribe", payload.model_dump(), resp.model_dump(), session_id)
        return resp
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to transcribe audio: {e}")
        raise HTTPException(status_code=500, detail="Failed to transcribe audio")


@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize_speech(payload: SynthesizeRequest, session_id: Optional[UUID] = None):
    """
    Synthesize speech from text using TTS.
    
    Args:
        payload: Text synthesis request
        session_id: Optional session ID for tracking
        
    Returns:
        SynthesizeResponse: Synthesized audio
    """
    try:
        if not validate_text_input(payload.text):
            raise HTTPException(status_code=400, detail="Invalid text input")
        
        # Sanitize inputs
        language = sanitize_language_code(payload.language or "en")
        provider = payload.provider or "default"
        model = payload.model or "base"
        
        # Use cached model service for better performance
        try:
            audio_data = await model_cache_service.synthesize(
                payload.text, provider, model, language, payload.voice
            )
        except Exception as cache_error:
            logger.warning(f"Cache service failed, falling back to direct synthesis: {cache_error}")
            if payload.voice:
                audio_data = await synthesize_with_voice(
                    payload.text, provider, model, payload.voice
                )
            else:
                audio_data = await synthesize_text(payload.text, provider, model)
        
        resp = SynthesizeResponse(
            audio_data=audio_data,
            sample_rate=22050,  # Default sample rate
            duration=len(payload.text) * 0.1  # Rough estimate
        )
        
        await record_turn("synthesize", payload.model_dump(), resp.model_dump(), session_id)
        return resp
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to synthesize speech: {e}")
        raise HTTPException(status_code=500, detail="Failed to synthesize speech")


@router.post("/loop", response_model=LoopResponse)
async def voice_loop(payload: LoopRequest, session_id: Optional[UUID] = None) -> LoopResponse:
    """
    Process complete voice loop: STT -> LLM -> TTS.
    
    Args:
        payload: Voice loop request
        session_id: Optional session ID for tracking
        
    Returns:
        LoopResponse: Complete voice loop result
    """
    try:
        if not validate_audio_samples(payload.samples):
            raise HTTPException(status_code=400, detail="Invalid audio samples")
        
        # Sanitize inputs
        language = sanitize_language_code(payload.language)
        
        # Process through voice loop
        transcript, response, audio, energy = await loop_samples(
            payload.samples, payload.provider, payload.model, language, payload.voice
        )
        
        resp = LoopResponse(
            transcript=transcript,
            response=response,
            audio=audio,
            energy=energy,
            is_final=True
        )
        
        await record_turn("loop", payload.model_dump(), resp.model_dump(), session_id)
        return resp
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process voice loop: {e}")
        raise HTTPException(status_code=500, detail="Failed to process voice loop")


@router.post("/barge-in", response_model=BargeInResponse)
async def detect_barge_in(payload: BargeInRequest, session_id: Optional[UUID] = None) -> BargeInResponse:
    """
    Detect if user is trying to interrupt (barge-in).
    
    Args:
        payload: Barge-in detection request
        session_id: Optional session ID for tracking
        
    Returns:
        BargeInResponse: Barge-in detection result
    """
    try:
        if not validate_audio_samples(payload.samples):
            raise HTTPException(status_code=400, detail="Invalid audio samples")
        
        interrupted = await barge_in(payload.samples, payload.threshold)
        energy = calculate_energy(payload.samples)
        
        resp = BargeInResponse(
            interrupted=interrupted,
            energy=energy,
            timestamp=0.0  # TODO: Add proper timestamp
        )
        
        await record_turn("barge_in", payload.model_dump(), resp.model_dump(), session_id)
        return resp
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to detect barge-in: {e}")
        raise HTTPException(status_code=500, detail="Failed to detect barge-in")


@router.post("/fallback", response_model=FallbackResponse)
async def process_with_fallback(payload: FallbackRequest, session_id: Optional[UUID] = None) -> FallbackResponse:
    """
    Process audio with fallback provider support.
    
    Args:
        payload: Fallback processing request
        session_id: Optional session ID for tracking
        
    Returns:
        FallbackResponse: Processing result with fallback info
    """
    try:
        if not validate_audio_samples(payload.samples):
            raise HTTPException(status_code=400, detail="Invalid audio samples")
        
        transcript, provider_used, fallback_triggered = await retry_with_fallback(
            payload.samples, payload.primary_provider, payload.fallback_provider, payload.model
        )
        
        resp = FallbackResponse(
            transcript=transcript,
            provider_used=provider_used,
            fallback_triggered=fallback_triggered,
            error_details=None
        )
        
        await record_turn("fallback", payload.model_dump(), resp.model_dump(), session_id)
        return resp
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process with fallback: {e}")
        raise HTTPException(status_code=500, detail="Failed to process with fallback")


@router.post("/consent", response_model=ConsentResponse)
async def detect_consent(payload: ConsentRequest, session_id: Optional[UUID] = None) -> ConsentResponse:
    """
    Detect consent phrases in audio.
    
    Args:
        payload: Consent detection request
        session_id: Optional session ID for tracking
        
    Returns:
        ConsentResponse: Consent detection result
    """
    try:
        if not validate_audio_samples(payload.samples):
            raise HTTPException(status_code=400, detail="Invalid audio samples")
        
        consent_detected = await detect_consent(payload.samples, payload.consent_phrases)
        
        resp = ConsentResponse(
            consent_detected=consent_detected,
            confidence=0.9 if consent_detected else 0.1,
            detected_phrases=[],  # TODO: Return actual detected phrases
            timestamp=0.0  # TODO: Add proper timestamp
        )
        
        await record_turn("consent", payload.model_dump(), resp.model_dump(), session_id)
        return resp
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to detect consent: {e}")
        raise HTTPException(status_code=500, detail="Failed to detect consent")


@router.post("/retention", response_model=RetentionResponse)
async def handle_retention(payload: RetentionRequest, session_id: Optional[UUID] = None) -> RetentionResponse:
    """
    Handle audio retention based on policy.
    
    Args:
        payload: Audio retention request
        session_id: Optional session ID for tracking
        
    Returns:
        RetentionResponse: Retention result
    """
    try:
        if not validate_audio_samples(payload.samples):
            raise HTTPException(status_code=400, detail="Invalid audio samples")
        
        retained = await maybe_retain_audio(
            payload.samples, payload.user_id, payload.session_id, payload.retention_policy
        )
        
        resp = RetentionResponse(
            retained=retained,
            retention_id=f"ret_{payload.session_id}" if retained else None,
            expiry_date="2024-12-31" if retained else None  # TODO: Calculate proper expiry
        )
        
        await record_turn("retention", payload.model_dump(), resp.model_dump(), session_id)
        return resp
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to handle retention: {e}")
        raise HTTPException(status_code=500, detail="Failed to handle retention")


@router.post("/offline", response_model=OfflineModeResponse)
async def process_offline(payload: OfflineModeRequest, session_id: Optional[UUID] = None) -> OfflineModeResponse:
    """
    Process audio in offline mode using local models.
    
    Args:
        payload: Offline mode request
        session_id: Optional session ID for tracking
        
    Returns:
        OfflineModeResponse: Offline processing result
    """
    try:
        if not validate_audio_samples(payload.samples):
            raise HTTPException(status_code=400, detail="Invalid audio samples")
        
        # Use local models for offline processing
        transcript, confidence = await transcribe_samples(payload.samples, "whisper", "base")
        
        resp = OfflineModeResponse(
            transcript=transcript,
            models_used=payload.offline_models or ["whisper-base"],
            offline_mode=True
        )
        
        await record_turn("offline", payload.model_dump(), resp.model_dump(), session_id)
        return resp
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process in offline mode: {e}")
        raise HTTPException(status_code=500, detail="Failed to process in offline mode")