#!/usr/bin/env python3
"""
Script to populate database with all providers and models needed for African language assistants.
This includes LLM providers, voice providers, and models for STT/TTS.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the backend directory to the path
backend_path = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_path))

from services.llm_service import llm_service
from services.voice_service import voice_service
from .models import LLMProvider, LLMModel, VoiceProvider, Voice


async def populate_llm_providers():
    """Populate LLM providers for African language support."""
    
    print("Populating LLM providers...")
    
    providers_data = [
        {
            "name": "openai",
            "display_name": "OpenAI",
            "description": "Leading AI research company known for GPT models with excellent multilingual support",
            "website": "https://openai.com",
            "api_base_url": "https://api.openai.com/v1",
            "pricing_model": "per_token",
            "features": ["chat", "completion", "function_calling", "vision", "audio", "multilingual"],
            "supported_languages": ["English", "Twi", "Yoruba", "Swahili", "Xhosa", "Ewe", "Ga", "French", "Spanish", "German", "Chinese", "Japanese", "Korean"],
            "max_context_length": 128000,
            "is_active": True
        },
        {
            "name": "anthropic",
            "display_name": "Anthropic",
            "description": "AI safety company focused on reliable and interpretable AI systems",
            "website": "https://anthropic.com",
            "api_base_url": "https://api.anthropic.com",
            "pricing_model": "per_token",
            "features": ["chat", "completion", "function_calling", "vision", "tool_use", "multilingual"],
            "supported_languages": ["English", "Twi", "Yoruba", "Swahili", "Xhosa", "Ewe", "Ga", "French", "Spanish", "German", "Chinese", "Japanese", "Korean"],
            "max_context_length": 200000,
            "is_active": True
        },
        {
            "name": "google",
            "display_name": "Google",
            "description": "Google's AI division offering Gemini models with extensive language support",
            "website": "https://ai.google.dev",
            "api_base_url": "https://generativelanguage.googleapis.com",
            "pricing_model": "per_token",
            "features": ["chat", "completion", "function_calling", "vision", "audio", "multilingual"],
            "supported_languages": ["English", "Twi", "Yoruba", "Swahili", "Xhosa", "Ewe", "Ga", "French", "Spanish", "German", "Chinese", "Japanese", "Korean"],
            "max_context_length": 1000000,
            "is_active": True
        },
        {
            "name": "meta",
            "display_name": "Meta",
            "description": "Meta's open source AI models including LLaMA with African language support",
            "website": "https://ai.meta.com",
            "api_base_url": "https://api.meta.ai",
            "pricing_model": "per_token",
            "features": ["chat", "completion", "function_calling", "multilingual"],
            "supported_languages": ["English", "Twi", "Yoruba", "Swahili", "Xhosa", "Ewe", "Ga", "French", "Spanish", "German", "Italian", "Portuguese"],
            "max_context_length": 4096,
            "is_active": True
        }
    ]
    
    created_providers = {}
    
    for provider_data in providers_data:
        try:
            provider = LLMProvider(**provider_data)
            created_provider = await llm_service.create_provider(provider)
            created_providers[provider_data["name"]] = created_provider
            print(f"✅ Created LLM provider: {provider_data['display_name']}")
        except Exception as e:
            print(f"❌ Failed to create LLM provider {provider_data['name']}: {e}")
    
    return created_providers


async def populate_llm_models():
    """Populate LLM models for African language support."""
    
    print("Populating LLM models...")
    
    models_data = [
        # OpenAI Models
        {
            "provider_id": "openai",
            "name": "gpt-4o",
            "display_name": "GPT-4o",
            "description": "OpenAI's most advanced model with excellent multilingual capabilities",
            "model_type": "chat",
            "context_length": 128000,
            "input_cost_per_1k_tokens": 0.0025,
            "output_cost_per_1k_tokens": 0.01,
            "capabilities": ["chat", "completion", "function_calling", "vision", "audio", "multilingual"],
            "supported_languages": ["English", "Twi", "Yoruba", "Swahili", "Xhosa", "Ewe", "Ga"],
            "performance_metrics": {"speed": "fast", "accuracy": "highest", "multilingual": "excellent"},
            "is_active": True,
            "is_default": True
        },
        {
            "provider_id": "openai",
            "name": "gpt-4o-mini",
            "display_name": "GPT-4o Mini",
            "description": "Fast and efficient model with good multilingual support",
            "model_type": "chat",
            "context_length": 128000,
            "input_cost_per_1k_tokens": 0.00015,
            "output_cost_per_1k_tokens": 0.0006,
            "capabilities": ["chat", "completion", "function_calling", "multilingual"],
            "supported_languages": ["English", "Twi", "Yoruba", "Swahili", "Xhosa", "Ewe", "Ga"],
            "performance_metrics": {"speed": "very_fast", "accuracy": "high", "multilingual": "good"},
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "openai",
            "name": "gpt-3.5-turbo",
            "display_name": "GPT-3.5 Turbo",
            "description": "Cost-effective model with decent multilingual support",
            "model_type": "chat",
            "context_length": 16385,
            "input_cost_per_1k_tokens": 0.0005,
            "output_cost_per_1k_tokens": 0.0015,
            "capabilities": ["chat", "completion", "function_calling"],
            "supported_languages": ["English", "Twi", "Yoruba", "Swahili", "Xhosa", "Ewe", "Ga"],
            "performance_metrics": {"speed": "very_fast", "accuracy": "medium", "multilingual": "good"},
            "is_active": True,
            "is_default": False
        },
        
        # Anthropic Models
        {
            "provider_id": "anthropic",
            "name": "claude-3-5-sonnet",
            "display_name": "Claude 3.5 Sonnet",
            "description": "Anthropic's most capable model with excellent multilingual support",
            "model_type": "chat",
            "context_length": 200000,
            "input_cost_per_1k_tokens": 0.003,
            "output_cost_per_1k_tokens": 0.015,
            "capabilities": ["chat", "completion", "function_calling", "vision", "tool_use"],
            "supported_languages": ["English", "Twi", "Yoruba", "Swahili", "Xhosa", "Ewe", "Ga"],
            "performance_metrics": {"speed": "fast", "accuracy": "highest", "multilingual": "excellent"},
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "anthropic",
            "name": "claude-3-haiku",
            "display_name": "Claude 3 Haiku",
            "description": "Fast and efficient model with good multilingual support",
            "model_type": "chat",
            "context_length": 200000,
            "input_cost_per_1k_tokens": 0.00025,
            "output_cost_per_1k_tokens": 0.00125,
            "capabilities": ["chat", "completion", "function_calling"],
            "supported_languages": ["English", "Twi", "Yoruba", "Swahili", "Xhosa", "Ewe", "Ga"],
            "performance_metrics": {"speed": "very_fast", "accuracy": "high", "multilingual": "good"},
            "is_active": True,
            "is_default": False
        },
        
        # Google Models
        {
            "provider_id": "google",
            "name": "gemini-1.5-pro",
            "display_name": "Gemini 1.5 Pro",
            "description": "Google's most advanced model with extensive multilingual support",
            "model_type": "chat",
            "context_length": 1000000,
            "input_cost_per_1k_tokens": 0.0025,
            "output_cost_per_1k_tokens": 0.0075,
            "capabilities": ["chat", "completion", "function_calling", "vision", "audio"],
            "supported_languages": ["English", "Twi", "Yoruba", "Swahili", "Xhosa", "Ewe", "Ga"],
            "performance_metrics": {"speed": "fast", "accuracy": "highest", "multilingual": "excellent"},
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "google",
            "name": "gemini-1.5-flash",
            "display_name": "Gemini 1.5 Flash",
            "description": "Fast and efficient model with good multilingual support",
            "model_type": "chat",
            "context_length": 1000000,
            "input_cost_per_1k_tokens": 0.000075,
            "output_cost_per_1k_tokens": 0.0003,
            "capabilities": ["chat", "completion", "function_calling"],
            "supported_languages": ["English", "Twi", "Yoruba", "Swahili", "Xhosa", "Ewe", "Ga"],
            "performance_metrics": {"speed": "very_fast", "accuracy": "high", "multilingual": "good"},
            "is_active": True,
            "is_default": False
        }
    ]
    
    created_models = {}
    
    for model_data in models_data:
        try:
            model = LLMModel(**model_data)
            created_model = await llm_service.create_model(model)
            created_models[model_data["name"]] = created_model
            print(f"✅ Created LLM model: {model_data['display_name']}")
        except Exception as e:
            print(f"❌ Failed to create LLM model {model_data['name']}: {e}")
    
    return created_models


async def populate_voice_providers():
    """Populate voice providers for African language support."""
    
    print("Populating voice providers...")
    
    providers_data = [
        # STT Providers
        {
            "name": "meta_mms",
            "display_name": "Meta MMS",
            "description": "Meta's multilingual speech recognition and synthesis supporting 1,100+ languages including African languages",
            "website": "https://ai.meta.com/research/publications/massively-multilingual-speech/",
            "api_base_url": "https://api.meta.ai/mms",
            "provider_type": "both",
            "pricing_model": "free",
            "features": ["asr", "tts", "lid", "multilingual", "african_languages"],
            "supported_languages": ["twi", "yoruba", "swahili", "xhosa", "ewe", "ga", "hausa", "igbo", "zulu"],
            "supported_voices": 1100,
            "max_audio_length": 300,
            "latency_ms": 2000,
            "is_active": True,
            "is_default": True
        },
        {
            "name": "openai",
            "display_name": "OpenAI Whisper",
            "description": "OpenAI's speech recognition model with excellent multilingual support",
            "website": "https://openai.com/research/whisper",
            "api_base_url": "https://api.openai.com/v1",
            "provider_type": "STT",
            "pricing_model": "per_minute",
            "features": ["asr", "multilingual", "translation"],
            "supported_languages": ["twi", "yoruba", "swahili", "xhosa", "ewe", "ga", "hausa", "igbo", "zulu"],
            "supported_voices": 0,
            "max_audio_length": 300,
            "latency_ms": 1500,
            "is_active": True,
            "is_default": False
        },
        {
            "name": "google",
            "display_name": "Google STT v2",
            "description": "Google's speech recognition with official support for Yoruba, Xhosa, and Swahili",
            "website": "https://cloud.google.com/speech-to-text",
            "api_base_url": "https://speech.googleapis.com/v2",
            "provider_type": "STT",
            "pricing_model": "per_minute",
            "features": ["asr", "multilingual", "official_support"],
            "supported_languages": ["yoruba", "xhosa", "swahili"],
            "supported_voices": 0,
            "max_audio_length": 300,
            "latency_ms": 1000,
            "is_active": True,
            "is_default": False
        },
        {
            "name": "azure",
            "display_name": "Azure Speech",
            "description": "Microsoft's speech services with neural TTS and official Swahili support",
            "website": "https://azure.microsoft.com/en-us/services/cognitive-services/speech-services/",
            "api_base_url": "https://eastus.api.cognitive.microsoft.com/sts/v1.0",
            "provider_type": "both",
            "pricing_model": "per_minute",
            "features": ["asr", "tts", "neural_voices", "official_support"],
            "supported_languages": ["swahili"],
            "supported_voices": 400,
            "max_audio_length": 300,
            "latency_ms": 800,
            "is_active": True,
            "is_default": False
        },
        {
            "name": "aws",
            "display_name": "AWS Transcribe",
            "description": "Amazon's speech recognition service with enterprise features",
            "website": "https://aws.amazon.com/transcribe/",
            "api_base_url": "https://transcribe.amazonaws.com",
            "provider_type": "STT",
            "pricing_model": "per_minute",
            "features": ["asr", "enterprise", "batch_processing"],
            "supported_languages": ["swahili"],
            "supported_voices": 0,
            "max_audio_length": 300,
            "latency_ms": 2000,
            "is_active": True,
            "is_default": False
        },
        {
            "name": "coqui",
            "display_name": "Coqui TTS",
            "description": "Open source text-to-speech with custom African language models",
            "website": "https://coqui.ai",
            "api_base_url": "https://api.coqui.ai",
            "provider_type": "TTS",
            "pricing_model": "free",
            "features": ["tts", "custom_voices", "african_languages", "open_source"],
            "supported_languages": ["twi", "yoruba", "ewe", "ga"],
            "supported_voices": 50,
            "max_audio_length": 600,
            "latency_ms": 3000,
            "is_active": True,
            "is_default": False
        }
    ]
    
    created_providers = {}
    
    for provider_data in providers_data:
        try:
            provider = VoiceProvider(**provider_data)
            created_provider = await voice_service.create_provider(provider)
            created_providers[provider_data["name"]] = created_provider
            print(f"✅ Created voice provider: {provider_data['display_name']}")
        except Exception as e:
            print(f"❌ Failed to create voice provider {provider_data['name']}: {e}")
    
    return created_providers


async def populate_voices():
    """Populate voices for African language support."""
    
    print("Populating voices...")
    
    voices_data = [
        # Twi Voices
        {
            "provider_id": "meta_mms",
            "name": "asante_female",
            "display_name": "Asante Female (Twi)",
            "description": "Female voice for Asante Twi dialect",
            "gender": "female",
            "language": "twi",
            "language_name": "Twi (Akan)",
            "country": "Ghana",
            "country_name": "Ghana",
            "voice_type": "neural",
            "sample_rate": 24000,
            "quality": "high",
            "features": ["african_language", "twi", "asante", "female"],
            "is_active": True,
            "is_default": True
        },
        {
            "provider_id": "meta_mms",
            "name": "asante_male",
            "display_name": "Asante Male (Twi)",
            "description": "Male voice for Asante Twi dialect",
            "gender": "male",
            "language": "twi",
            "language_name": "Twi (Akan)",
            "country": "Ghana",
            "country_name": "Ghana",
            "voice_type": "neural",
            "sample_rate": 24000,
            "quality": "high",
            "features": ["african_language", "twi", "asante", "male"],
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "meta_mms",
            "name": "akuapem_female",
            "display_name": "Akuapem Female (Twi)",
            "description": "Female voice for Akuapem Twi dialect",
            "gender": "female",
            "language": "twi",
            "language_name": "Twi (Akan)",
            "country": "Ghana",
            "country_name": "Ghana",
            "voice_type": "neural",
            "sample_rate": 24000,
            "quality": "high",
            "features": ["african_language", "twi", "akuapem", "female"],
            "is_active": True,
            "is_default": False
        },
        
        # Yoruba Voices
        {
            "provider_id": "meta_mms",
            "name": "yoruba_female",
            "display_name": "Yoruba Female",
            "description": "Female voice for Yoruba language",
            "gender": "female",
            "language": "yo",
            "language_name": "Yoruba",
            "country": "Nigeria",
            "country_name": "Nigeria",
            "voice_type": "neural",
            "sample_rate": 24000,
            "quality": "high",
            "features": ["african_language", "yoruba", "female"],
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "meta_mms",
            "name": "yoruba_male",
            "display_name": "Yoruba Male",
            "description": "Male voice for Yoruba language",
            "gender": "male",
            "language": "yo",
            "language_name": "Yoruba",
            "country": "Nigeria",
            "country_name": "Nigeria",
            "voice_type": "neural",
            "sample_rate": 24000,
            "quality": "high",
            "features": ["african_language", "yoruba", "male"],
            "is_active": True,
            "is_default": False
        },
        
        # Swahili Voices
        {
            "provider_id": "azure",
            "name": "sw-KE-ZuriNeural",
            "display_name": "Zuri (Swahili - Kenya)",
            "description": "Neural voice for Swahili (Kenya)",
            "gender": "female",
            "language": "sw",
            "language_name": "Swahili",
            "country": "Kenya",
            "country_name": "Kenya",
            "voice_type": "neural",
            "sample_rate": 24000,
            "quality": "ultra",
            "features": ["african_language", "swahili", "neural", "female", "official_support"],
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "azure",
            "name": "sw-KE-RafikiNeural",
            "display_name": "Rafiki (Swahili - Kenya)",
            "description": "Neural voice for Swahili (Kenya)",
            "gender": "male",
            "language": "sw",
            "language_name": "Swahili",
            "country": "Kenya",
            "country_name": "Kenya",
            "voice_type": "neural",
            "sample_rate": 24000,
            "quality": "ultra",
            "features": ["african_language", "swahili", "neural", "male", "official_support"],
            "is_active": True,
            "is_default": False
        },
        
        # Xhosa Voices
        {
            "provider_id": "meta_mms",
            "name": "xhosa_female",
            "display_name": "Xhosa Female",
            "description": "Female voice for Xhosa language",
            "gender": "female",
            "language": "xh",
            "language_name": "Xhosa",
            "country": "South Africa",
            "country_name": "South Africa",
            "voice_type": "neural",
            "sample_rate": 24000,
            "quality": "high",
            "features": ["african_language", "xhosa", "female"],
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "meta_mms",
            "name": "xhosa_male",
            "display_name": "Xhosa Male",
            "description": "Male voice for Xhosa language",
            "gender": "male",
            "language": "xh",
            "language_name": "Xhosa",
            "country": "South Africa",
            "country_name": "South Africa",
            "voice_type": "neural",
            "sample_rate": 24000,
            "quality": "high",
            "features": ["african_language", "xhosa", "male"],
            "is_active": True,
            "is_default": False
        },
        
        # Ewe Voices
        {
            "provider_id": "meta_mms",
            "name": "ewe_female",
            "display_name": "Ewe Female",
            "description": "Female voice for Ewe language",
            "gender": "female",
            "language": "ee",
            "language_name": "Ewe",
            "country": "Ghana",
            "country_name": "Ghana",
            "voice_type": "neural",
            "sample_rate": 24000,
            "quality": "high",
            "features": ["african_language", "ewe", "female"],
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "meta_mms",
            "name": "ewe_male",
            "display_name": "Ewe Male",
            "description": "Male voice for Ewe language",
            "gender": "male",
            "language": "ee",
            "language_name": "Ewe",
            "country": "Ghana",
            "country_name": "Ghana",
            "voice_type": "neural",
            "sample_rate": 24000,
            "quality": "high",
            "features": ["african_language", "ewe", "male"],
            "is_active": True,
            "is_default": False
        },
        
        # Ga Voices
        {
            "provider_id": "meta_mms",
            "name": "ga_female",
            "display_name": "Ga Female",
            "description": "Female voice for Ga language",
            "gender": "female",
            "language": "gaa",
            "language_name": "Ga",
            "country": "Ghana",
            "country_name": "Ghana",
            "voice_type": "neural",
            "sample_rate": 24000,
            "quality": "high",
            "features": ["african_language", "ga", "female"],
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "meta_mms",
            "name": "ga_male",
            "display_name": "Ga Male",
            "description": "Male voice for Ga language",
            "gender": "male",
            "language": "gaa",
            "language_name": "Ga",
            "country": "Ghana",
            "country_name": "Ghana",
            "voice_type": "neural",
            "sample_rate": 24000,
            "quality": "high",
            "features": ["african_language", "ga", "male"],
            "is_active": True,
            "is_default": False
        },
        
        # Coqui TTS Voices
        {
            "provider_id": "coqui",
            "name": "asante_twi_female",
            "display_name": "Asante Twi Female (Coqui)",
            "description": "Custom Asante Twi female voice using Coqui TTS",
            "gender": "female",
            "language": "twi",
            "language_name": "Twi (Akan)",
            "country": "Ghana",
            "country_name": "Ghana",
            "voice_type": "custom",
            "sample_rate": 22050,
            "quality": "high",
            "features": ["african_language", "twi", "asante", "female", "custom_voice"],
            "is_active": True,
            "is_default": False
        }
    ]
    
    created_voices = {}
    
    for voice_data in voices_data:
        try:
            voice = Voice(**voice_data)
            created_voice = await voice_service.create_voice(voice)
            created_voices[voice_data["name"]] = created_voice
            print(f"✅ Created voice: {voice_data['display_name']}")
        except Exception as e:
            print(f"❌ Failed to create voice {voice_data['name']}: {e}")
    
    return created_voices


async def main():
    """Main function to populate all data."""
    
    print("🚀 Starting African Language Provider Population...")
    print("=" * 60)
    
    try:
        # Populate LLM providers and models
        print("\n📊 Populating LLM Data...")
        llm_providers = await populate_llm_providers()
        llm_models = await populate_llm_models()
        
        # Populate voice providers and voices
        print("\n🎤 Populating Voice Data...")
        voice_providers = await populate_voice_providers()
        voices = await populate_voices()
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 POPULATION SUMMARY")
        print("=" * 60)
        print(f"✅ LLM Providers: {len(llm_providers)}")
        print(f"✅ LLM Models: {len(llm_models)}")
        print(f"✅ Voice Providers: {len(voice_providers)}")
        print(f"✅ Voices: {len(voices)}")
        
        print(f"\n🎯 African Languages Supported:")
        print(f"   • Twi (Akan) - Ghana")
        print(f"   • Yoruba - Nigeria")
        print(f"   • Swahili - Kenya")
        print(f"   • Xhosa - South Africa")
        print(f"   • Ewe - Ghana/Togo")
        print(f"   • Ga - Ghana")
        
        print(f"\n🔧 Provider Combinations Available:")
        print(f"   • Meta MMS (STT + TTS) - All languages")
        print(f"   • OpenAI Whisper + Coqui TTS - Twi")
        print(f"   • Google STT v2 + MMS TTS - Yoruba, Xhosa")
        print(f"   • Azure Speech - Swahili")
        print(f"   • AWS Transcribe + Coqui TTS - Twi")
        
        print(f"\n💾 Database populated successfully!")
        print(f"🔗 Test assistants at: https://kasaai.ailabsafrica.com")
        
    except Exception as e:
        print(f"❌ Error during population: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
