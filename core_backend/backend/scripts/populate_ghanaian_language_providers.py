#!/usr/bin/env python3
"""Script to populate MongoDB with Meta MMS and Whisper providers for Ghanaian languages."""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.models import LLMProvider, LLMModel, VoiceProvider, Voice
from backend.services.llm_service import llm_service
from backend.services.voice_service import voice_service


async def populate_ghanaian_language_providers():
    """Populate the database with Meta MMS and Whisper providers for Ghanaian languages."""
    
    print("🔄 Populating Ghanaian language providers (Meta MMS and Whisper)...")
    
    # Ghanaian languages supported by both MMS and Whisper
    ghanaian_languages = [
        "Twi", "Asante Twi", "Akuapem Twi", "Ewe", "Ga", "Dagbani", 
        "Hausa", "Yoruba", "Igbo", "Swahili", "English"
    ]
    
    # 1. Add Meta MMS as LLM Provider
    mms_provider_data = {
        "name": "meta_mms",
        "display_name": "Meta MMS",
        "description": "Meta's Massively Multilingual Speech (MMS) - supports over 1,100 languages including Ghanaian languages",
        "website": "https://ai.meta.com/blog/multilingual-model-speech-recognition/",
        "api_base_url": "https://huggingface.co/facebook/mms-1b-all",
        "pricing_model": "open_source",
        "features": ["speech_recognition", "text_to_speech", "language_detection", "multilingual"],
        "supported_languages": ghanaian_languages,
        "max_context_length": 32000
    }
    
    # 2. Add OpenAI Whisper as LLM Provider
    whisper_provider_data = {
        "name": "openai_whisper",
        "display_name": "OpenAI Whisper",
        "description": "OpenAI's Whisper - robust speech recognition model supporting multiple languages including Ghanaian languages",
        "website": "https://openai.com/research/whisper",
        "api_base_url": "https://github.com/openai/whisper",
        "pricing_model": "open_source",
        "features": ["speech_recognition", "translation", "language_detection", "multilingual"],
        "supported_languages": ghanaian_languages,
        "max_context_length": 48000
    }
    
    # 3. Add GhanaNLP as LLM Provider
    ghananlp_provider_data = {
        "name": "ghananlp",
        "display_name": "GhanaNLP",
        "description": "Ghana-focused natural language processing models and APIs for Ghanaian languages. Includes Khaya AI for translation and speech recognition",
        "website": "https://translation.ghananlp.org/",
        "api_base_url": "https://translation.ghananlp.org/api",
        "pricing_model": "api_credits",
        "features": ["speech_recognition", "text_to_speech", "translation", "nlp", "ghanaian_languages", "khaya_ai"],
        "supported_languages": ghanaian_languages,
        "max_context_length": 4096  # Updated based on latest API
    }
    
    # 4. Add ABENA as LLM Provider (BERT model, not speech service)
    abena_provider_data = {
        "name": "abena",
        "display_name": "ABENA",
        "description": "African BERT for Enhanced Natural language processing - BERT model specialized for Ghanaian languages (Twi, Ewe, Ga)",
        "website": "https://huggingface.co/Ghana-NLP/abena-base-asante-twi-uncased",
        "api_base_url": "https://huggingface.co/Ghana-NLP",
        "pricing_model": "open_source",
        "features": ["nlp", "bert", "ghanaian_languages", "text_embedding", "language_model"],
        "supported_languages": ghanaian_languages,
        "max_context_length": 512  # BERT standard context length
    }
    
    # 5. Add Khaya AI as a separate provider
    khaya_provider_data = {
        "name": "khaya",
        "display_name": "Khaya AI",
        "description": "Khaya AI - First translation app for Ghanaian languages with speech recognition and text-to-speech capabilities",
        "website": "https://translate.ghananlp.org/",
        "api_base_url": "https://translate.ghananlp.org/api",
        "pricing_model": "freemium",
        "features": ["translation", "speech_recognition", "text_to_speech", "ghanaian_languages", "african_languages"],
        "supported_languages": ghanaian_languages + ["Yoruba", "Gurene", "Kikuyu", "Kimeru", "Luo"],
        "max_context_length": 2048
    }
    
    # Create providers
    providers_to_create = [mms_provider_data, whisper_provider_data, ghananlp_provider_data, abena_provider_data, khaya_provider_data]
    
    for provider_data in providers_to_create:
        try:
            # Check if provider already exists
            existing_provider = await llm_service.get_provider_by_name(provider_data["name"])
            if existing_provider:
                print(f"✅ Provider {provider_data['display_name']} already exists")
                continue
            
            # Create provider
            provider = LLMProvider(**provider_data)
            created_provider = await llm_service.create_provider(provider)
            print(f"✅ Created provider: {created_provider.display_name}")
            
        except Exception as e:
            print(f"❌ Error creating provider {provider_data['name']}: {e}")
    
    # 3. Add Meta MMS Models
    mms_models_data = [
        {
            "provider_id": "meta_mms",
            "name": "mms-1b-all",
            "display_name": "MMS 1B All Languages",
            "description": "Meta's 1B parameter model supporting 1,100+ languages including Twi, Ewe, Ga, and other Ghanaian languages",
            "model_type": "speech_recognition",
            "context_length": 32000,
            "input_cost_per_1k_tokens": 0.0,  # Open source
            "output_cost_per_1k_tokens": 0.0,
            "capabilities": ["speech_to_text", "text_to_speech", "language_detection"],
            "supported_languages": ghanaian_languages,
            "performance_metrics": {
                "word_error_rate": 0.15,
                "character_error_rate": 0.08,
                "language_coverage": 1100,
                "supported_ghanaian_languages": ["twi", "ewe", "ga", "dagbani", "hausa"]
            },
            "is_active": True,
            "is_default": True
        },
        {
            "provider_id": "meta_mms",
            "name": "mms-tts-all",
            "display_name": "MMS TTS All Languages",
            "description": "Meta's text-to-speech model for 1,100+ languages with Ghanaian language support",
            "model_type": "text_to_speech",
            "context_length": 32000,
            "input_cost_per_1k_tokens": 0.0,
            "output_cost_per_1k_tokens": 0.0,
            "capabilities": ["text_to_speech", "voice_synthesis"],
            "supported_languages": ghanaian_languages,
            "performance_metrics": {
                "speech_quality": 4.2,
                "naturalness": 4.0,
                "language_coverage": 1100
            },
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "meta_mms",
            "name": "mms-lid-126",
            "display_name": "MMS Language Detection",
            "description": "Meta's language identification model supporting 4,000+ languages",
            "model_type": "language_detection",
            "context_length": 32000,
            "input_cost_per_1k_tokens": 0.0,
            "output_cost_per_1k_tokens": 0.0,
            "capabilities": ["language_detection", "multilingual"],
            "supported_languages": ghanaian_languages,
            "performance_metrics": {
                "accuracy": 0.95,
                "language_coverage": 4000,
                "detection_speed": "real_time"
            },
            "is_active": True,
            "is_default": False
        }
    ]
    
    # 4. Add Whisper Models
    whisper_models_data = [
        {
            "provider_id": "openai_whisper",
            "name": "whisper-tiny",
            "display_name": "Whisper Tiny",
            "description": "Fastest Whisper model for real-time transcription of Ghanaian languages",
            "model_type": "speech_recognition",
            "context_length": 48000,
            "input_cost_per_1k_tokens": 0.0,
            "output_cost_per_1k_tokens": 0.0,
            "capabilities": ["speech_to_text", "translation", "language_detection"],
            "supported_languages": ghanaian_languages,
            "performance_metrics": {
                "word_error_rate": 0.25,
                "speed": "fastest",
                "model_size": "39M",
                "memory_usage": "1GB"
            },
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "openai_whisper",
            "name": "whisper-base",
            "display_name": "Whisper Base",
            "description": "Balanced Whisper model for good accuracy and speed with Ghanaian languages",
            "model_type": "speech_recognition",
            "context_length": 48000,
            "input_cost_per_1k_tokens": 0.0,
            "output_cost_per_1k_tokens": 0.0,
            "capabilities": ["speech_to_text", "translation", "language_detection"],
            "supported_languages": ghanaian_languages,
            "performance_metrics": {
                "word_error_rate": 0.20,
                "speed": "fast",
                "model_size": "74M",
                "memory_usage": "1GB"
            },
            "is_active": True,
            "is_default": True
        },
        {
            "provider_id": "openai_whisper",
            "name": "whisper-small",
            "display_name": "Whisper Small",
            "description": "High-quality Whisper model for accurate transcription of Ghanaian languages",
            "model_type": "speech_recognition",
            "context_length": 48000,
            "input_cost_per_1k_tokens": 0.0,
            "output_cost_per_1k_tokens": 0.0,
            "capabilities": ["speech_to_text", "translation", "language_detection"],
            "supported_languages": ghanaian_languages,
            "performance_metrics": {
                "word_error_rate": 0.15,
                "speed": "medium",
                "model_size": "244M",
                "memory_usage": "2GB"
            },
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "openai_whisper",
            "name": "whisper-medium",
            "display_name": "Whisper Medium",
            "description": "High-accuracy Whisper model for professional transcription of Ghanaian languages",
            "model_type": "speech_recognition",
            "context_length": 48000,
            "input_cost_per_1k_tokens": 0.0,
            "output_cost_per_1k_tokens": 0.0,
            "capabilities": ["speech_to_text", "translation", "language_detection"],
            "supported_languages": ghanaian_languages,
            "performance_metrics": {
                "word_error_rate": 0.10,
                "speed": "slow",
                "model_size": "769M",
                "memory_usage": "5GB"
            },
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "openai_whisper",
            "name": "whisper-large-v3",
            "display_name": "Whisper Large v3",
            "description": "Highest accuracy Whisper model for research and professional use with Ghanaian languages",
            "model_type": "speech_recognition",
            "context_length": 48000,
            "input_cost_per_1k_tokens": 0.0,
            "output_cost_per_1k_tokens": 0.0,
            "capabilities": ["speech_to_text", "translation", "language_detection"],
            "supported_languages": ghanaian_languages,
            "performance_metrics": {
                "word_error_rate": 0.05,
                "speed": "slowest",
                "model_size": "1550M",
                "memory_usage": "10GB"
            },
            "is_active": True,
            "is_default": False
        }
    ]
    
    # 5. Add GhanaNLP Models
    ghananlp_models_data = [
        {
            "provider_id": "ghananlp",
            "name": "ghana-asr",
            "display_name": "GhanaNLP ASR",
            "description": "GhanaNLP speech recognition model for Ghanaian languages",
            "model_type": "speech_recognition",
            "context_length": 2048,
            "input_cost_per_1k_tokens": 0.0,
            "output_cost_per_1k_tokens": 0.0,
            "capabilities": ["speech_to_text", "ghanaian_languages"],
            "supported_languages": ghanaian_languages,
            "performance_metrics": {
                "word_error_rate": 0.18,
                "language_coverage": 10,
                "ghanaian_optimized": True
            },
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "ghananlp",
            "name": "ghana-tts",
            "display_name": "GhanaNLP TTS",
            "description": "GhanaNLP text-to-speech model for Ghanaian languages",
            "model_type": "text_to_speech",
            "context_length": 2048,
            "input_cost_per_1k_tokens": 0.0,
            "output_cost_per_1k_tokens": 0.0,
            "capabilities": ["text_to_speech", "ghanaian_languages"],
            "supported_languages": ghanaian_languages,
            "performance_metrics": {
                "speech_quality": 4.0,
                "naturalness": 3.8,
                "ghanaian_optimized": True
            },
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "ghananlp",
            "name": "ghana-translate",
            "display_name": "GhanaNLP Translation",
            "description": "GhanaNLP translation model for Ghanaian languages",
            "model_type": "translation",
            "context_length": 2048,
            "input_cost_per_1k_tokens": 0.0,
            "output_cost_per_1k_tokens": 0.0,
            "capabilities": ["translation", "ghanaian_languages"],
            "supported_languages": ghanaian_languages,
            "performance_metrics": {
                "translation_quality": 4.2,
                "language_pairs": 45,
                "ghanaian_optimized": True
            },
            "is_active": True,
            "is_default": False
        }
    ]
    
    # 6. Add ABENA Models (BERT-based, not speech models)
    abena_models_data = [
        {
            "provider_id": "abena",
            "name": "abena-base-asante-twi-uncased",
            "display_name": "ABENA Base Asante Twi (Uncased)",
            "description": "ABENA BERT model for Asante Twi language - African BERT for Enhanced Natural language processing",
            "model_type": "language_model",
            "context_length": 512,
            "input_cost_per_1k_tokens": 0.0,
            "output_cost_per_1k_tokens": 0.0,
            "capabilities": ["nlp", "bert", "text_embedding", "language_model", "ghanaian_languages"],
            "supported_languages": ["Twi", "Asante Twi"],
            "performance_metrics": {
                "accuracy": 0.92,
                "language_coverage": 1,
                "ghanaian_optimized": True,
                "model_type": "bert"
            },
            "is_active": True,
            "is_default": True
        },
        {
            "provider_id": "abena",
            "name": "abena-base-akuapem-twi-cased",
            "display_name": "ABENA Base Akuapem Twi (Cased)",
            "description": "ABENA BERT model for Akuapem Twi language - African BERT for Enhanced Natural language processing",
            "model_type": "language_model",
            "context_length": 512,
            "input_cost_per_1k_tokens": 0.0,
            "output_cost_per_1k_tokens": 0.0,
            "capabilities": ["nlp", "bert", "text_embedding", "language_model", "ghanaian_languages"],
            "supported_languages": ["Twi", "Akuapem Twi"],
            "performance_metrics": {
                "accuracy": 0.90,
                "language_coverage": 1,
                "ghanaian_optimized": True,
                "model_type": "bert"
            },
            "is_active": True,
            "is_default": False
        }
    ]
    
    # 7. Add Khaya AI Models
    khaya_models_data = [
        {
            "provider_id": "khaya",
            "name": "khaya-translation",
            "display_name": "Khaya Translation",
            "description": "Khaya AI translation model for Ghanaian and African languages",
            "model_type": "translation",
            "context_length": 2048,
            "input_cost_per_1k_tokens": 0.0,
            "output_cost_per_1k_tokens": 0.0,
            "capabilities": ["translation", "ghanaian_languages", "african_languages"],
            "supported_languages": ghanaian_languages + ["Yoruba", "Gurene", "Kikuyu", "Kimeru", "Luo"],
            "performance_metrics": {
                "translation_quality": 4.5,
                "language_coverage": 15,
                "african_optimized": True,
                "user_feedback_improved": True
            },
            "is_active": True,
            "is_default": True
        },
        {
            "provider_id": "khaya",
            "name": "khaya-speech-recognition",
            "display_name": "Khaya Speech Recognition",
            "description": "Khaya AI speech recognition for Twi and Yoruba with automatic speech recognition capabilities",
            "model_type": "speech_recognition",
            "context_length": 2048,
            "input_cost_per_1k_tokens": 0.0,
            "output_cost_per_1k_tokens": 0.0,
            "capabilities": ["speech_to_text", "ghanaian_languages", "african_languages"],
            "supported_languages": ["Twi", "Yoruba"],
            "performance_metrics": {
                "word_error_rate": 0.16,
                "language_coverage": 2,
                "african_optimized": True,
                "asr_capabilities": True
            },
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "khaya",
            "name": "khaya-text-to-speech",
            "display_name": "Khaya Text-to-Speech",
            "description": "Khaya AI text-to-speech with pronunciation for Twi, Ewe, and Kikuyu",
            "model_type": "text_to_speech",
            "context_length": 2048,
            "input_cost_per_1k_tokens": 0.0,
            "output_cost_per_1k_tokens": 0.0,
            "capabilities": ["text_to_speech", "pronunciation", "ghanaian_languages", "african_languages"],
            "supported_languages": ["Twi", "Ewe", "Kikuyu"],
            "performance_metrics": {
                "speech_quality": 4.3,
                "naturalness": 4.1,
                "pronunciation_accuracy": 0.95,
                "african_optimized": True
            },
            "is_active": True,
            "is_default": False
        }
    ]
    
    # Create all models
    all_models = mms_models_data + whisper_models_data + ghananlp_models_data + abena_models_data + khaya_models_data
    
    for model_data in all_models:
        try:
            # Check if model already exists
            existing_model = await llm_service.get_model_by_name(model_data["name"])
            if existing_model:
                print(f"✅ Model {model_data['display_name']} already exists")
                continue
            
            # Create model
            model = LLMModel(**model_data)
            created_model = await llm_service.create_model(model)
            print(f"✅ Created model: {created_model.display_name}")
            
        except Exception as e:
            print(f"❌ Error creating model {model_data['name']}: {e}")
    
    # 5. Add Voice Providers for Ghanaian Languages
    voice_providers_data = [
        {
            "name": "meta_mms_voices",
            "display_name": "Meta MMS Voices",
            "description": "Meta MMS text-to-speech voices for Ghanaian languages",
            "website": "https://ai.meta.com/blog/multilingual-model-speech-recognition/",
            "api_base_url": "https://huggingface.co/facebook/mms-tts-all",
            "provider_type": "TTS",
            "pricing_model": "open_source",
            "features": ["text_to_speech", "multilingual", "ghanaian_languages"],
            "supported_languages": ghanaian_languages,
            "supported_voices": 4,
            "max_audio_length": 300,
            "latency_ms": 500,
            "is_active": True
        },
        {
            "name": "coqui_ghanaian",
            "display_name": "Coqui Ghanaian Voices",
            "description": "Coqui TTS voices specifically trained for Ghanaian languages",
            "website": "https://coqui.ai",
            "api_base_url": "https://api.coqui.ai",
            "provider_type": "TTS",
            "pricing_model": "freemium",
            "features": ["text_to_speech", "voice_cloning", "ghanaian_languages"],
            "supported_languages": ghanaian_languages,
            "supported_voices": 2,
            "max_audio_length": 600,
            "latency_ms": 300,
            "is_active": True
        },
        {
            "name": "ghananlp",
            "display_name": "GhanaNLP",
            "description": "GhanaNLP voice synthesis for Ghanaian languages",
            "website": "https://translation.ghananlp.org/",
            "api_base_url": "https://translation.ghananlp.org/api",
            "provider_type": "TTS",
            "pricing_model": "api_credits",
            "features": ["text_to_speech", "ghanaian_languages", "voice_cloning"],
            "supported_languages": ghanaian_languages,
            "supported_voices": 6,
            "max_audio_length": 300,
            "latency_ms": 800,
            "is_active": True
        },
        {
            "name": "khaya",
            "display_name": "Khaya AI",
            "description": "Khaya AI voice synthesis for Ghanaian and African languages with pronunciation",
            "website": "https://translate.ghananlp.org/",
            "api_base_url": "https://translate.ghananlp.org/api",
            "provider_type": "TTS",
            "pricing_model": "freemium",
            "features": ["text_to_speech", "pronunciation", "ghanaian_languages", "african_languages"],
            "supported_languages": ghanaian_languages + ["Yoruba", "Gurene", "Kikuyu", "Kimeru", "Luo"],
            "supported_voices": 8,
            "max_audio_length": 300,
            "latency_ms": 600,
            "is_active": True
        }
    ]
    
    for provider_data in voice_providers_data:
        try:
            # Check if provider already exists
            existing_provider = await voice_service.get_provider_by_name(provider_data["name"])
            if existing_provider:
                print(f"✅ Voice provider {provider_data['display_name']} already exists")
                continue
            
            # Create provider
            provider = VoiceProvider(**provider_data)
            created_provider = await voice_service.create_provider(provider)
            print(f"✅ Created voice provider: {created_provider.display_name}")
            
        except Exception as e:
            print(f"❌ Error creating voice provider {provider_data['name']}: {e}")
    
    # 6. Add Ghanaian Voices
    ghanaian_voices_data = [
        # Meta MMS Voices
        {
            "provider_id": "meta_mms_voices",
            "name": "mms_twi_male",
            "display_name": "Twi Male (MMS)",
            "description": "Meta MMS male voice for Twi language",
            "language": "Twi",
            "language_name": "Twi (Akan)",
            "gender": "male",
            "voice_type": "natural",
            "features": ["text_to_speech", "multilingual"],
            "quality": "standard",
            "sample_rate": 22050,
            "is_active": True,
            "is_default": True
        },
        {
            "provider_id": "meta_mms_voices",
            "name": "mms_twi_female",
            "display_name": "Twi Female (MMS)",
            "description": "Meta MMS female voice for Twi language",
            "language": "Twi",
            "language_name": "Twi (Akan)",
            "gender": "female",
            "voice_type": "natural",
            "features": ["text_to_speech", "multilingual"],
            "quality": "standard",
            "sample_rate": 22050,
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "meta_mms_voices",
            "name": "mms_ewe_male",
            "display_name": "Ewe Male (MMS)",
            "description": "Meta MMS male voice for Ewe language",
            "language": "Ewe",
            "language_name": "Ewe",
            "gender": "male",
            "voice_type": "natural",
            "features": ["text_to_speech", "multilingual"],
            "quality": "standard",
            "sample_rate": 22050,
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "meta_mms_voices",
            "name": "mms_ga_female",
            "display_name": "Ga Female (MMS)",
            "description": "Meta MMS female voice for Ga language",
            "language": "Ga",
            "language_name": "Ga",
            "gender": "female",
            "voice_type": "natural",
            "features": ["text_to_speech", "multilingual"],
            "quality": "standard",
            "sample_rate": 22050,
            "is_active": True,
            "is_default": False
        },
        # Coqui Ghanaian Voices
        {
            "provider_id": "coqui_ghanaian",
            "name": "coqui_twi_male",
            "display_name": "Twi Male (Coqui)",
            "description": "Coqui male voice for Twi language",
            "language": "Twi",
            "language_name": "Twi (Akan)",
            "gender": "male",
            "voice_type": "natural",
            "features": ["text_to_speech", "voice_cloning"],
            "quality": "hd",
            "sample_rate": 22050,
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "coqui_ghanaian",
            "name": "coqui_twi_female",
            "display_name": "Twi Female (Coqui)",
            "description": "Coqui female voice for Twi language",
            "language": "Twi",
            "language_name": "Twi (Akan)",
            "gender": "female",
            "voice_type": "natural",
            "features": ["text_to_speech", "voice_cloning"],
            "quality": "hd",
            "sample_rate": 22050,
            "is_active": True,
            "is_default": False
        },
        # GhanaNLP Voices
        {
            "provider_id": "ghananlp",
            "name": "ghana_twi_male",
            "display_name": "Twi Male (GhanaNLP)",
            "description": "GhanaNLP male voice for Twi language",
            "language": "Twi",
            "language_name": "Twi (Akan)",
            "gender": "male",
            "voice_type": "natural",
            "features": ["text_to_speech", "ghanaian_languages"],
            "quality": "standard",
            "sample_rate": 22050,
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "ghananlp",
            "name": "ghana_twi_female",
            "display_name": "Twi Female (GhanaNLP)",
            "description": "GhanaNLP female voice for Twi language",
            "language": "Twi",
            "language_name": "Twi (Akan)",
            "gender": "female",
            "voice_type": "natural",
            "features": ["text_to_speech", "ghanaian_languages"],
            "quality": "standard",
            "sample_rate": 22050,
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "ghananlp",
            "name": "ghana_ewe_male",
            "display_name": "Ewe Male (GhanaNLP)",
            "description": "GhanaNLP male voice for Ewe language",
            "language": "Ewe",
            "language_name": "Ewe",
            "gender": "male",
            "voice_type": "natural",
            "features": ["text_to_speech", "ghanaian_languages"],
            "quality": "standard",
            "sample_rate": 22050,
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "ghananlp",
            "name": "ghana_ewe_female",
            "display_name": "Ewe Female (GhanaNLP)",
            "description": "GhanaNLP female voice for Ewe language",
            "language": "Ewe",
            "language_name": "Ewe",
            "gender": "female",
            "voice_type": "natural",
            "features": ["text_to_speech", "ghanaian_languages"],
            "quality": "standard",
            "sample_rate": 22050,
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "ghananlp",
            "name": "ghana_ga_male",
            "display_name": "Ga Male (GhanaNLP)",
            "description": "GhanaNLP male voice for Ga language",
            "language": "Ga",
            "language_name": "Ga",
            "gender": "male",
            "voice_type": "natural",
            "features": ["text_to_speech", "ghanaian_languages"],
            "quality": "standard",
            "sample_rate": 22050,
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "ghananlp",
            "name": "ghana_ga_female",
            "display_name": "Ga Female (GhanaNLP)",
            "description": "GhanaNLP female voice for Ga language",
            "language": "Ga",
            "language_name": "Ga",
            "gender": "female",
            "voice_type": "natural",
            "features": ["text_to_speech", "ghanaian_languages"],
            "quality": "standard",
            "sample_rate": 22050,
            "is_active": True,
            "is_default": False
        },
        # Khaya AI Voices
        {
            "provider_id": "khaya",
            "name": "khaya_twi_male",
            "display_name": "Twi Male (Khaya)",
            "description": "Khaya AI male voice for Twi language with pronunciation",
            "language": "Twi",
            "language_name": "Twi (Akan)",
            "gender": "male",
            "voice_type": "natural",
            "features": ["text_to_speech", "pronunciation", "ghanaian_languages"],
            "quality": "premium",
            "sample_rate": 22050,
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "khaya",
            "name": "khaya_twi_female",
            "display_name": "Twi Female (Khaya)",
            "description": "Khaya AI female voice for Twi language with pronunciation",
            "language": "Twi",
            "language_name": "Twi (Akan)",
            "gender": "female",
            "voice_type": "natural",
            "features": ["text_to_speech", "pronunciation", "ghanaian_languages"],
            "quality": "premium",
            "sample_rate": 22050,
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "khaya",
            "name": "khaya_ewe_male",
            "display_name": "Ewe Male (Khaya)",
            "description": "Khaya AI male voice for Ewe language with pronunciation",
            "language": "Ewe",
            "language_name": "Ewe",
            "gender": "male",
            "voice_type": "natural",
            "features": ["text_to_speech", "pronunciation", "ghanaian_languages"],
            "quality": "premium",
            "sample_rate": 22050,
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "khaya",
            "name": "khaya_ewe_female",
            "display_name": "Ewe Female (Khaya)",
            "description": "Khaya AI female voice for Ewe language with pronunciation",
            "language": "Ewe",
            "language_name": "Ewe",
            "gender": "female",
            "voice_type": "natural",
            "features": ["text_to_speech", "pronunciation", "ghanaian_languages"],
            "quality": "premium",
            "sample_rate": 22050,
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "khaya",
            "name": "khaya_yoruba_male",
            "display_name": "Yoruba Male (Khaya)",
            "description": "Khaya AI male voice for Yoruba language with pronunciation",
            "language": "Yoruba",
            "language_name": "Yoruba",
            "gender": "male",
            "voice_type": "natural",
            "features": ["text_to_speech", "pronunciation", "african_languages"],
            "quality": "premium",
            "sample_rate": 22050,
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": "khaya",
            "name": "khaya_kikuyu_female",
            "display_name": "Kikuyu Female (Khaya)",
            "description": "Khaya AI female voice for Kikuyu language with pronunciation",
            "language": "Kikuyu",
            "language_name": "Kikuyu",
            "gender": "female",
            "voice_type": "natural",
            "features": ["text_to_speech", "pronunciation", "african_languages"],
            "quality": "premium",
            "sample_rate": 22050,
            "is_active": True,
            "is_default": False
        }
    ]
    
    for voice_data in ghanaian_voices_data:
        try:
            # Check if voice already exists
            existing_voice = await voice_service.get_voice_by_name(voice_data["name"])
            if existing_voice:
                print(f"✅ Voice {voice_data['display_name']} already exists")
                continue
            
            # Create voice
            voice = Voice(**voice_data)
            created_voice = await voice_service.create_voice(voice)
            print(f"✅ Created voice: {created_voice.display_name}")
            
        except Exception as e:
            print(f"❌ Error creating voice {voice_data['name']}: {e}")
    
    print("✅ Ghanaian language providers population completed!")


if __name__ == "__main__":
    asyncio.run(populate_ghanaian_language_providers())
