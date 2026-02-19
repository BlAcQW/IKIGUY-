"""
VAPI Assistant Builder Service

Helper functions to build VAPI assistant configurations from automation configs,
including support for custom_settings_override.

VAPI Custom Provider Configuration:
- custom-voice: HTTP endpoint that returns raw 1-channel 16-bit PCM audio
- custom-transcriber: WebSocket endpoint (wss://) for real-time streaming
- custom-llm: OpenAI-compatible /chat/completions endpoint

Our Implementation:
- TTS: Use our VAPI webhook that calls our TTS providers and converts to PCM
- ASR: Use our WebSocket ASR endpoint (wss://api.ailabsafrica.com/ws/asr/stream)
  with Faster Whisper (hosted at whisper.ailabsafrica.com)
- LLM: Use our Ollama endpoint (ollama.ailabsafrica.com) with custom models
  or VAPI's built-in providers for OpenAI/Anthropic models
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.ailabsafrica.com")
WS_BASE_URL = API_BASE_URL.replace("https://", "wss://").replace("http://", "ws://")
VAPI_API_KEY = os.getenv("VAPI_API_KEY") or os.getenv("VAPI_PUBLIC_KEY") or os.getenv("VAPI_PRIVATE_KEY")

# TTS Providers that we support via our custom VAPI webhook
# The webhook at /api/vapi/custom-providers/tts will route to these
SUPPORTED_CUSTOM_TTS_PROVIDERS = {
    "kokoro", "styletts", "styletts2", "chatterbox",
    "f5tts", "f5-tts", "openvoice", "mars5"
}

# ASR Providers we host via WebSocket streaming at /ws/asr/stream
# Our Faster Whisper is hosted at whisper.ailabsafrica.com
SUPPORTED_CUSTOM_ASR_PROVIDERS = {
    "faster_whisper": "faster_whisper_large",
    "faster_whisper_small": "faster_whisper_small",
    "faster_whisper_medium": "faster_whisper_medium",
    "faster_whisper_large": "faster_whisper_large",
    "whisper": "faster_whisper_large",
    "giftmark-akan-whisper": "giftmark-akan-whisper",  # Akan language model
}

# LLM Providers - our Ollama instance hosts custom models
# Ollama endpoint: ollama.ailabsafrica.com/api/chat (OpenAI-compatible at /v1/chat/completions)
OLLAMA_MODELS = {
    "kasaai_llama_twi": "kasaai_llama_twi:v1.0",
    "kasaai_aya_ghana": "kasaai_aya_ghana:v1.0",
    "kasaai_mistral_ghana": "kasaai_mistral_ghana:v1.0",
    "llama_32_3b": "llama3.2:3b",
    "aya_23_8b": "aya:8b",
    "mistral_7b": "mistral:7b",
}

# VAPI's built-in LLM providers (for OpenAI, Anthropic, Groq models)
VAPI_LLM_PROVIDERS = {
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
    "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
    "groq": ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
    "gemini": ["gemini-2.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"],
}


def build_vapi_assistant_config(
    vapi_agent_config: Dict[str, Any],
    assistant_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build VAPI assistant configuration from automation config.
    
    If custom_settings_override is present, uses custom provider webhooks.
    Otherwise, uses VAPI default providers.
    
    Args:
        vapi_agent_config: VAPIAgent configuration from automation config
        assistant_id: Optional VAPI assistant ID (for building custom provider URLs)
        
    Returns:
        VAPI API-compatible assistant configuration
    """
    custom_override = vapi_agent_config.get("custom_settings_override")
    
    # Base configuration
    config = {
        "name": vapi_agent_config.get("assistant_name") or "Automation Assistant",
        "firstMessage": vapi_agent_config.get("first_message", "Hello! How can I help you?"),
        "recordingEnabled": vapi_agent_config.get("recording_enabled", True),
    }
    
    # System prompt / messages
    system_prompt = vapi_agent_config.get("system_prompt", "")
    if system_prompt:
        config["model"] = {
            "messages": [
                {"role": "system", "content": system_prompt}
            ]
        }
    
    # Voice configuration
    if custom_override and custom_override.get("tts"):
        tts_config = custom_override["tts"]
        tts_provider = tts_config.get("provider", "").lower()

        if tts_provider in SUPPORTED_CUSTOM_TTS_PROVIDERS:
            # Use our custom TTS webhook which handles PCM conversion
            # VAPI expects raw 1-channel 16-bit PCM audio from custom-voice
            tts_webhook_url = f"{API_BASE_URL}/api/vapi/custom-providers/tts"
            if assistant_id:
                tts_webhook_url += f"?assistant_id={assistant_id}"

            logger.info(f"Configuring custom TTS: {tts_provider} via webhook {tts_webhook_url}")
            config["voice"] = {
                "provider": "custom-voice",
                "server": {
                    "url": tts_webhook_url,
                    "timeoutSeconds": 30
                }
            }
            # Store custom settings in metadata for the webhook to read
            config.setdefault("metadata", {})["custom_tts"] = {
                "provider": tts_provider,
                "voice": tts_config.get("voice"),
                "speed": tts_config.get("speed", 1.0),
                "pitch": tts_config.get("pitch", 0.0),
            }
            if assistant_id:
                config["metadata"]["assistant_id"] = assistant_id
        else:
            # Provider not in our custom list - use VAPI's built-in providers
            logger.info(f"TTS provider {tts_provider} not custom, using VAPI defaults")
            voice_settings = vapi_agent_config.get("voice_settings", {})
            voice_id = voice_settings.get("voice_id", "jennifer")
            model = voice_settings.get("model", "eleven_flash_v2_5")

            config["voice"] = {
                "provider": "11labs",
                "voiceId": voice_id,
                "model": model
            }
    else:
        # Use VAPI default voice settings
        voice_settings = vapi_agent_config.get("voice_settings", {})
        voice_id = voice_settings.get("voice_id", "jennifer")
        model = voice_settings.get("model", "eleven_flash_v2_5")
        
        config["voice"] = {
            "provider": "11labs",
            "voiceId": voice_id,
            "model": model
        }
    
    # Model/LLM configuration
    # Use our Ollama endpoint for custom models, VAPI built-in for others
    if custom_override and custom_override.get("llm"):
        llm_config = custom_override["llm"]
        custom_model = llm_config.get("model", "") if llm_config.get("model") else None
        temperature = llm_config.get("temperature", 0.7)
        max_tokens = llm_config.get("maxTokens", 150)

        # Check if this is one of our Ollama models
        ollama_model = OLLAMA_MODELS.get(custom_model) if custom_model else None

        if ollama_model:
            # Use our Ollama endpoint with custom-llm provider
            # Ollama provides OpenAI-compatible endpoint at /v1/chat/completions
            ollama_url = "https://ollama.ailabsafrica.com/v1/chat/completions"
            logger.info(f"Configuring custom LLM: {custom_model} ({ollama_model}) via Ollama at {ollama_url}")

            config["model"] = {
                "provider": "custom-llm",
                "url": ollama_url,
                "model": ollama_model,
                "temperature": temperature,
                "maxTokens": max_tokens,
            }
            if system_prompt:
                config["model"]["messages"] = [
                    {"role": "system", "content": system_prompt}
                ]
            config.setdefault("metadata", {})["custom_llm"] = {
                "provider": "ollama",
                "model_id": custom_model,
                "ollama_model": ollama_model,
            }
        else:
            # Use VAPI's built-in providers for OpenAI/Anthropic/Groq/Gemini
            custom_model_lower = custom_model.lower() if custom_model else ""
            model_provider = "openai"  # default
            model_name = custom_model or "gpt-4o-mini"

            if "claude" in custom_model_lower:
                model_provider = "anthropic"
            elif "gemini" in custom_model_lower:
                model_provider = "google"  # VAPI uses "google" for Gemini
            elif "llama" in custom_model_lower or "mixtral" in custom_model_lower:
                model_provider = "groq"
            elif "gpt" in custom_model_lower:
                model_provider = "openai"

            logger.info(f"Configuring VAPI LLM: {model_provider}/{model_name} temp={temperature} maxTokens={max_tokens}")
            config["model"] = {
                "provider": model_provider,
                "model": model_name,
                "temperature": temperature,
                "maxTokens": max_tokens,
            }
            if system_prompt:
                config["model"]["messages"] = [
                    {"role": "system", "content": system_prompt}
                ]
    else:
        # Use VAPI default model settings
        model_settings = vapi_agent_config.get("model_settings", {})
        model_provider = model_settings.get("provider", "openai")
        model_name = model_settings.get("model", "gpt-4o-mini")
        temperature = model_settings.get("temperature", 0.7)
        max_tokens = model_settings.get("max_tokens", 150)
        
        config["model"] = {
            "provider": model_provider,
            "model": model_name,
            "temperature": temperature,
            "maxTokens": max_tokens,
        }
        if system_prompt:
            config["model"]["messages"] = [
                {"role": "system", "content": system_prompt}
            ]
    
    # Transcriber/ASR configuration
    # We have WebSocket ASR streaming at wss://api.ailabsafrica.com/ws/asr/stream
    # with Faster Whisper hosted at whisper.ailabsafrica.com
    if custom_override and custom_override.get("asr"):
        asr_config = custom_override["asr"]
        asr_provider_requested = asr_config.get("provider", "").lower()
        custom_language = asr_config.get("language", "en")

        # Check if this is one of our supported custom ASR providers
        provider_id = SUPPORTED_CUSTOM_ASR_PROVIDERS.get(asr_provider_requested)

        if provider_id:
            # Use our VAPI-compatible WebSocket ASR endpoint
            # This endpoint handles binary PCM audio from VAPI and returns transcriptions
            asr_ws_url = f"{WS_BASE_URL}/ws/asr/vapi-transcriber?provider_id={provider_id}&language={custom_language}"
            logger.info(f"Configuring custom ASR: {asr_provider_requested} via VAPI transcriber {asr_ws_url}")

            config["transcriber"] = {
                "provider": "custom-transcriber",
                "server": {
                    "url": asr_ws_url,
                    "timeoutSeconds": 30
                }
            }
            config.setdefault("metadata", {})["custom_asr"] = {
                "provider": asr_provider_requested,
                "provider_id": provider_id,
                "language": custom_language,
            }
            if assistant_id:
                config["metadata"]["assistant_id"] = assistant_id
        else:
            # Fall back to VAPI's Deepgram for unsupported providers
            logger.info(f"ASR provider {asr_provider_requested} not custom, using Deepgram with language={custom_language}")
            config["transcriber"] = {
                "provider": "deepgram",
                "model": "nova-2",
                "language": custom_language
            }
    else:
        # Use VAPI default transcriber
        transcriber_settings = vapi_agent_config.get("transcriber", {})
        transcriber_provider = transcriber_settings.get("provider", "deepgram")
        transcriber_model = transcriber_settings.get("model", "nova-2")
        transcriber_language = transcriber_settings.get("language", "en")
        
        config["transcriber"] = {
            "provider": transcriber_provider,
            "model": transcriber_model,
            "language": transcriber_language
        }
    
    # Additional settings
    if vapi_agent_config.get("silence_timeout_seconds"):
        config["silenceTimeoutSeconds"] = vapi_agent_config["silence_timeout_seconds"]
    
    if vapi_agent_config.get("max_duration_seconds"):
        config["maxDurationSeconds"] = vapi_agent_config["max_duration_seconds"]
    
    if vapi_agent_config.get("background_denoising_enabled") is not None:
        config["backgroundDenoising"] = vapi_agent_config["background_denoising_enabled"]
    
    # Tools
    tools = vapi_agent_config.get("tools", [])
    if tools:
        config["model"]["tools"] = tools
    
    return config

