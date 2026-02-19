#!/usr/bin/env python3
"""Script to populate voice providers and voices with latest data."""

import sys
import asyncio
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(backend_dir))

from backend.models import VoiceProvider, Voice
from backend.services.voice_service import voice_service


async def populate_voice_data():
    """Populate voice providers and voices with latest data."""
    
    print("Clearing existing voice data...")
    await voice_service.clear_all()
    
    print("Creating voice providers...")
    
    # ElevenLabs - Latest TTS provider
    elevenlabs_provider = VoiceProvider(
        name="elevenlabs",
        display_name="ElevenLabs",
        description="Leading AI voice generation platform with 1000+ voices across 70+ languages. Features real-time voice cloning and emotional control.",
        website="https://elevenlabs.io",
        api_base_url="https://api.elevenlabs.io/v1",
        provider_type="TTS",
        pricing_model="per_character",
        features=[
            "voice_cloning",
            "emotion_control",
            "real_time_generation",
            "multilingual_support",
            "voice_design",
            "voice_library"
        ],
        supported_languages=[
            "en", "es", "fr", "de", "it", "pt", "pl", "hi", "ja", "ko", "zh", "ar", "ru", "tr", "nl", "sv", "da", "no", "fi", "cs", "sk", "hu", "ro", "bg", "hr", "sl", "et", "lv", "lt", "mt", "el", "he", "th", "vi", "id", "ms", "tl", "bn", "ur", "fa", "ps", "ku", "am", "sw", "yo", "ig", "ha", "zu", "xh", "af", "st", "tn", "ts", "ss", "ve", "nd", "sn", "rw", "lg", "ak", "tw", "ee", "ki", "lu", "ny", "mg", "km", "lo", "my", "ka", "mn", "ky", "uz", "kk", "tg", "tk", "az", "hy", "mk", "sq", "bs", "me", "sr", "hr", "sl", "sk", "cs", "pl", "uk", "be", "ru", "bg", "ro", "md", "al", "gr", "tr", "cy", "ga", "is", "fo", "no", "sv", "da", "fi", "et", "lv", "lt", "mt", "it", "es", "pt", "fr", "de", "nl", "be", "lu", "ch", "at", "li", "mc", "ad", "va", "sm", "it", "va", "sm", "ad", "mc", "li", "at", "ch", "lu", "be", "nl", "de", "fr", "pt", "es", "it", "mt", "lt", "lv", "et", "fi", "da", "sv", "no", "fo", "is", "ga", "cy", "tr", "gr", "al", "md", "ro", "bg", "ru", "be", "uk", "pl", "cs", "sk", "sl", "hr", "sr", "me", "bs", "sq", "mk", "hy", "az", "tk", "tg", "kk", "uz", "ky", "mn", "ka", "my", "lo", "km", "mg", "ny", "lu", "ki", "ee", "tw", "ak", "lg", "rw", "sn", "nd", "ve", "ss", "ts", "tn", "st", "af", "xh", "zu", "ha", "ig", "yo", "sw", "am", "ku", "ps", "fa", "ur", "bn", "tl", "ms", "id", "vi", "th", "he", "el", "mt", "lt", "lv", "et", "fi", "no", "sv", "da", "fo", "is", "ga", "cy", "tr", "gr", "al", "md", "ro", "bg", "ru", "be", "uk", "pl", "cs", "sk", "sl", "hr", "sr", "me", "bs", "sq", "mk", "hy", "az", "tk", "tg", "kk", "uz", "ky", "mn", "ka", "my", "lo", "km", "mg", "ny", "lu", "ki", "ee", "tw", "ak", "lg", "rw", "sn", "nd", "ve", "ss", "ts", "tn", "st", "af", "xh", "zu", "ha", "ig", "yo", "sw", "am", "ku", "ps", "fa", "ur", "bn", "tl", "ms", "id", "vi", "th", "he", "el"
        ],
        supported_voices=1000,
        max_audio_length=2500,
        latency_ms=75,
        is_active=True,
        is_default=True
    )
    
    elevenlabs_provider = await voice_service.create_provider(elevenlabs_provider)
    
    # Google Cloud Speech - STT and TTS
    google_provider = VoiceProvider(
        name="google_cloud",
        display_name="Google Cloud Speech",
        description="Google's comprehensive speech AI platform with 220+ voices across 40+ languages. Features advanced neural models and real-time processing.",
        website="https://cloud.google.com/speech",
        api_base_url="https://speech.googleapis.com",
        provider_type="both",
        pricing_model="per_minute",
        features=[
            "neural_voices",
            "real_time_processing",
            "multilingual_support",
            "custom_voices",
            "voice_cloning",
            "speech_adaptation",
            "profanity_filtering",
            "speaker_diarization"
        ],
        supported_languages=[
            "en", "es", "fr", "de", "it", "pt", "pl", "hi", "ja", "ko", "zh", "ar", "ru", "tr", "nl", "sv", "da", "no", "fi", "cs", "sk", "hu", "ro", "bg", "hr", "sl", "et", "lv", "lt", "mt", "el", "he", "th", "vi", "id", "ms", "tl", "bn", "ur", "fa", "ps", "ku", "am", "sw", "yo", "ig", "ha", "zu", "xh", "af", "st", "tn", "ts", "ss", "ve", "nd", "sn", "rw", "lg", "ak", "tw", "ee", "ki", "lu", "ny", "mg", "km", "lo", "my", "ka", "mn", "ky", "uz", "kk", "tg", "tk", "az", "hy", "mk", "sq", "bs", "me", "sr", "hr", "sl", "sk", "cs", "pl", "uk", "be", "ru", "bg", "ro", "md", "al", "gr", "tr", "cy", "ga", "is", "fo", "no", "sv", "da", "fi", "et", "lv", "lt", "mt", "it", "es", "pt", "fr", "de", "nl", "be", "lu", "ch", "at", "li", "mc", "ad", "va", "sm", "it", "va", "sm", "ad", "mc", "li", "at", "ch", "lu", "be", "nl", "de", "fr", "pt", "es", "it", "mt", "lt", "lv", "et", "fi", "da", "sv", "no", "fo", "is", "ga", "cy", "tr", "gr", "al", "md", "ro", "bg", "ru", "be", "uk", "pl", "cs", "sk", "sl", "hr", "sr", "me", "bs", "sq", "mk", "hy", "az", "tk", "tg", "kk", "uz", "ky", "mn", "ka", "my", "lo", "km", "mg", "ny", "lu", "ki", "ee", "tw", "ak", "lg", "rw", "sn", "nd", "ve", "ss", "ts", "tn", "st", "af", "xh", "zu", "ha", "ig", "yo", "sw", "am", "ku", "ps", "fa", "ur", "bn", "tl", "ms", "id", "vi", "th", "he", "el"
        ],
        supported_voices=220,
        max_audio_length=300,
        latency_ms=100,
        is_active=True,
        is_default=False
    )
    
    google_provider = await voice_service.create_provider(google_provider)
    
    # Azure Speech Service - STT and TTS
    azure_provider = VoiceProvider(
        name="azure_speech",
        display_name="Azure Speech Service",
        description="Microsoft's enterprise-grade speech AI platform with HD voices, custom voice training, and advanced speech recognition capabilities.",
        website="https://azure.microsoft.com/speech",
        api_base_url="https://eastus.api.cognitive.microsoft.com",
        provider_type="both",
        pricing_model="per_hour",
        features=[
            "hd_voices",
            "custom_voice_training",
            "neural_voices",
            "real_time_processing",
            "multilingual_support",
            "voice_cloning",
            "speech_adaptation",
            "profanity_filtering",
            "speaker_diarization",
            "multi_talker_voices"
        ],
        supported_languages=[
            "en", "es", "fr", "de", "it", "pt", "pl", "hi", "ja", "ko", "zh", "ar", "ru", "tr", "nl", "sv", "da", "no", "fi", "cs", "sk", "hu", "ro", "bg", "hr", "sl", "et", "lv", "lt", "mt", "el", "he", "th", "vi", "id", "ms", "tl", "bn", "ur", "fa", "ps", "ku", "am", "sw", "yo", "ig", "ha", "zu", "xh", "af", "st", "tn", "ts", "ss", "ve", "nd", "sn", "rw", "lg", "ak", "tw", "ee", "ki", "lu", "ny", "mg", "km", "lo", "my", "ka", "mn", "ky", "uz", "kk", "tg", "tk", "az", "hy", "mk", "sq", "bs", "me", "sr", "hr", "sl", "sk", "cs", "pl", "uk", "be", "ru", "bg", "ro", "md", "al", "gr", "tr", "cy", "ga", "is", "fo", "no", "sv", "da", "fi", "et", "lv", "lt", "mt", "it", "es", "pt", "fr", "de", "nl", "be", "lu", "ch", "at", "li", "mc", "ad", "va", "sm", "it", "va", "sm", "ad", "mc", "li", "at", "ch", "lu", "be", "nl", "de", "fr", "pt", "es", "it", "mt", "lt", "lv", "et", "fi", "da", "sv", "no", "fo", "is", "ga", "cy", "tr", "gr", "al", "md", "ro", "bg", "ru", "be", "uk", "pl", "cs", "sk", "sl", "hr", "sr", "me", "bs", "sq", "mk", "hy", "az", "tk", "tg", "kk", "uz", "ky", "mn", "ka", "my", "lo", "km", "mg", "ny", "lu", "ki", "ee", "tw", "ak", "lg", "rw", "sn", "nd", "ve", "ss", "ts", "tn", "st", "af", "xh", "zu", "ha", "ig", "yo", "sw", "am", "ku", "ps", "fa", "ur", "bn", "tl", "ms", "id", "vi", "th", "he", "el"
        ],
        supported_voices=400,
        max_audio_length=600,
        latency_ms=150,
        is_active=True,
        is_default=False
    )
    
    azure_provider = await voice_service.create_provider(azure_provider)
    
    # Deepgram - STT specialist
    deepgram_provider = VoiceProvider(
        name="deepgram",
        display_name="Deepgram",
        description="Specialized speech-to-text platform with Nova-3 model offering 53.4% reduction in word error rate and real-time transcription.",
        website="https://deepgram.com",
        api_base_url="https://api.deepgram.com/v1",
        provider_type="STT",
        pricing_model="per_hour",
        features=[
            "nova_3_model",
            "real_time_transcription",
            "speaker_diarization",
            "punctuation",
            "profanity_filtering",
            "custom_models",
            "language_detection",
            "utterance_end_detection"
        ],
        supported_languages=[
            "en", "es", "fr", "de", "it", "pt", "pl", "hi", "ja", "ko", "zh", "ar", "ru", "tr", "nl", "sv", "da", "no", "fi", "cs", "sk", "hu", "ro", "bg", "hr", "sl", "et", "lv", "lt", "mt", "el", "he", "th", "vi", "id", "ms", "tl", "bn", "ur", "fa", "ps", "ku", "am", "sw", "yo", "ig", "ha", "zu", "xh", "af", "st", "tn", "ts", "ss", "ve", "nd", "sn", "rw", "lg", "ak", "tw", "ee", "ki", "lu", "ny", "mg", "km", "lo", "my", "ka", "mn", "ky", "uz", "kk", "tg", "tk", "az", "hy", "mk", "sq", "bs", "me", "sr", "hr", "sl", "sk", "cs", "pl", "uk", "be", "ru", "bg", "ro", "md", "al", "gr", "tr", "cy", "ga", "is", "fo", "no", "sv", "da", "fi", "et", "lv", "lt", "mt", "it", "es", "pt", "fr", "de", "nl", "be", "lu", "ch", "at", "li", "mc", "ad", "va", "sm", "it", "va", "sm", "ad", "mc", "li", "at", "ch", "lu", "be", "nl", "de", "fr", "pt", "es", "it", "mt", "lt", "lv", "et", "fi", "da", "sv", "no", "fo", "is", "ga", "cy", "tr", "gr", "al", "md", "ro", "bg", "ru", "be", "uk", "pl", "cs", "sk", "sl", "hr", "sr", "me", "bs", "sq", "mk", "hy", "az", "tk", "tg", "kk", "uz", "ky", "mn", "ka", "my", "lo", "km", "mg", "ny", "lu", "ki", "ee", "tw", "ak", "lg", "rw", "sn", "nd", "ve", "ss", "ts", "tn", "st", "af", "xh", "zu", "ha", "ig", "yo", "sw", "am", "ku", "ps", "fa", "ur", "bn", "tl", "ms", "id", "vi", "th", "he", "el"
        ],
        supported_voices=0,
        max_audio_length=0,
        latency_ms=50,
        is_active=True,
        is_default=False
    )
    
    deepgram_provider = await voice_service.create_provider(deepgram_provider)
    
    # OpenAI Whisper - STT specialist
    openai_whisper_provider = VoiceProvider(
        name="openai_whisper",
        display_name="OpenAI Whisper",
        description="OpenAI's advanced speech recognition model with multilingual support and high accuracy across diverse accents and environments.",
        website="https://openai.com/whisper",
        api_base_url="https://api.openai.com/v1",
        provider_type="STT",
        pricing_model="per_minute",
        features=[
            "multilingual_support",
            "high_accuracy",
            "noise_reduction",
            "accent_handling",
            "punctuation",
            "language_detection",
            "timestamp_alignment"
        ],
        supported_languages=[
            "en", "es", "fr", "de", "it", "pt", "pl", "hi", "ja", "ko", "zh", "ar", "ru", "tr", "nl", "sv", "da", "no", "fi", "cs", "sk", "hu", "ro", "bg", "hr", "sl", "et", "lv", "lt", "mt", "el", "he", "th", "vi", "id", "ms", "tl", "bn", "ur", "fa", "ps", "ku", "am", "sw", "yo", "ig", "ha", "zu", "xh", "af", "st", "tn", "ts", "ss", "ve", "nd", "sn", "rw", "lg", "ak", "tw", "ee", "ki", "lu", "ny", "mg", "km", "lo", "my", "ka", "mn", "ky", "uz", "kk", "tg", "tk", "az", "hy", "mk", "sq", "bs", "me", "sr", "hr", "sl", "sk", "cs", "pl", "uk", "be", "ru", "bg", "ro", "md", "al", "gr", "tr", "cy", "ga", "is", "fo", "no", "sv", "da", "fi", "et", "lv", "lt", "mt", "it", "es", "pt", "fr", "de", "nl", "be", "lu", "ch", "at", "li", "mc", "ad", "va", "sm", "it", "va", "sm", "ad", "mc", "li", "at", "ch", "lu", "be", "nl", "de", "fr", "pt", "es", "it", "mt", "lt", "lv", "et", "fi", "da", "sv", "no", "fo", "is", "ga", "cy", "tr", "gr", "al", "md", "ro", "bg", "ru", "be", "uk", "pl", "cs", "sk", "sl", "hr", "sr", "me", "bs", "sq", "mk", "hy", "az", "tk", "tg", "kk", "uz", "ky", "mn", "ka", "my", "lo", "km", "mg", "ny", "lu", "ki", "ee", "tw", "ak", "lg", "rw", "sn", "nd", "ve", "ss", "ts", "tn", "st", "af", "xh", "zu", "ha", "ig", "yo", "sw", "am", "ku", "ps", "fa", "ur", "bn", "tl", "ms", "id", "vi", "th", "he", "el"
        ],
        supported_voices=0,
        max_audio_length=0,
        latency_ms=200,
        is_active=True,
        is_default=False
    )
    
    openai_whisper_provider = await voice_service.create_provider(openai_whisper_provider)
    
    print("Creating voices...")
    
    # ElevenLabs voices
    elevenlabs_voices = [
        Voice(
            provider_id=elevenlabs_provider.id,
            name="adam",
            display_name="Adam",
            description="Professional male voice with clear articulation",
            gender="male",
            language="en",
            language_name="English",
            country="US",
            country_name="United States",
            voice_type="neural",
            sample_rate=44100,
            quality="hd",
            features=["emotion_control", "voice_cloning"],
            is_active=True,
            is_default=True
        ),
        Voice(
            provider_id=elevenlabs_provider.id,
            name="bella",
            display_name="Bella",
            description="Warm and friendly female voice",
            gender="female",
            language="en",
            language_name="English",
            country="US",
            country_name="United States",
            voice_type="neural",
            sample_rate=44100,
            quality="hd",
            features=["emotion_control", "voice_cloning"],
            is_active=True,
            is_default=False
        ),
        Voice(
            provider_id=elevenlabs_provider.id,
            name="carlos",
            display_name="Carlos",
            description="Spanish male voice with natural accent",
            gender="male",
            language="es",
            language_name="Spanish",
            country="ES",
            country_name="Spain",
            voice_type="neural",
            sample_rate=44100,
            quality="hd",
            features=["emotion_control", "voice_cloning"],
            is_active=True,
            is_default=True
        ),
        Voice(
            provider_id=elevenlabs_provider.id,
            name="maria",
            display_name="Maria",
            description="Spanish female voice with clear pronunciation",
            gender="female",
            language="es",
            language_name="Spanish",
            country="ES",
            country_name="Spain",
            voice_type="neural",
            sample_rate=44100,
            quality="hd",
            features=["emotion_control", "voice_cloning"],
            is_active=True,
            is_default=False
        ),
        Voice(
            provider_id=elevenlabs_provider.id,
            name="pierre",
            display_name="Pierre",
            description="French male voice with authentic accent",
            gender="male",
            language="fr",
            language_name="French",
            country="FR",
            country_name="France",
            voice_type="neural",
            sample_rate=44100,
            quality="hd",
            features=["emotion_control", "voice_cloning"],
            is_active=True,
            is_default=True
        ),
        Voice(
            provider_id=elevenlabs_provider.id,
            name="sophie",
            display_name="Sophie",
            description="French female voice with elegant tone",
            gender="female",
            language="fr",
            language_name="French",
            country="FR",
            country_name="France",
            voice_type="neural",
            sample_rate=44100,
            quality="hd",
            features=["emotion_control", "voice_cloning"],
            is_active=True,
            is_default=False
        ),
        Voice(
            provider_id=elevenlabs_provider.id,
            name="hans",
            display_name="Hans",
            description="German male voice with clear pronunciation",
            gender="male",
            language="de",
            language_name="German",
            country="DE",
            country_name="Germany",
            voice_type="neural",
            sample_rate=44100,
            quality="hd",
            features=["emotion_control", "voice_cloning"],
            is_active=True,
            is_default=True
        ),
        Voice(
            provider_id=elevenlabs_provider.id,
            name="anna",
            display_name="Anna",
            description="German female voice with warm tone",
            gender="female",
            language="de",
            language_name="German",
            country="DE",
            country_name="Germany",
            voice_type="neural",
            sample_rate=44100,
            quality="hd",
            features=["emotion_control", "voice_cloning"],
            is_active=True,
            is_default=False
        ),
        Voice(
            provider_id=elevenlabs_provider.id,
            name="marco",
            display_name="Marco",
            description="Italian male voice with expressive tone",
            gender="male",
            language="it",
            language_name="Italian",
            country="IT",
            country_name="Italy",
            voice_type="neural",
            sample_rate=44100,
            quality="hd",
            features=["emotion_control", "voice_cloning"],
            is_active=True,
            is_default=True
        ),
        Voice(
            provider_id=elevenlabs_provider.id,
            name="lucia",
            display_name="Lucia",
            description="Italian female voice with melodic tone",
            gender="female",
            language="it",
            language_name="Italian",
            country="IT",
            country_name="Italy",
            voice_type="neural",
            sample_rate=44100,
            quality="hd",
            features=["emotion_control", "voice_cloning"],
            is_active=True,
            is_default=False
        )
    ]
    
    for voice in elevenlabs_voices:
        await voice_service.create_voice(voice)
    
    # Google Cloud voices
    google_voices = [
        Voice(
            provider_id=google_provider.id,
            name="en-US-Neural2-A",
            display_name="US English (Neural2-A)",
            description="US English male voice with neural quality",
            gender="male",
            language="en",
            language_name="English",
            country="US",
            country_name="United States",
            voice_type="neural",
            sample_rate=24000,
            quality="hd",
            features=["neural_quality", "real_time"],
            is_active=True,
            is_default=True
        ),
        Voice(
            provider_id=google_provider.id,
            name="en-US-Neural2-F",
            display_name="US English (Neural2-F)",
            description="US English female voice with neural quality",
            gender="female",
            language="en",
            language_name="English",
            country="US",
            country_name="United States",
            voice_type="neural",
            sample_rate=24000,
            quality="hd",
            features=["neural_quality", "real_time"],
            is_active=True,
            is_default=False
        ),
        Voice(
            provider_id=google_provider.id,
            name="es-ES-Neural2-A",
            display_name="Spanish (Neural2-A)",
            description="Spanish male voice with neural quality",
            gender="male",
            language="es",
            language_name="Spanish",
            country="ES",
            country_name="Spain",
            voice_type="neural",
            sample_rate=24000,
            quality="hd",
            features=["neural_quality", "real_time"],
            is_active=True,
            is_default=True
        ),
        Voice(
            provider_id=google_provider.id,
            name="es-ES-Neural2-B",
            display_name="Spanish (Neural2-B)",
            description="Spanish female voice with neural quality",
            gender="female",
            language="es",
            language_name="Spanish",
            country="ES",
            country_name="Spain",
            voice_type="neural",
            sample_rate=24000,
            quality="hd",
            features=["neural_quality", "real_time"],
            is_active=True,
            is_default=False
        ),
        Voice(
            provider_id=google_provider.id,
            name="fr-FR-Neural2-A",
            display_name="French (Neural2-A)",
            description="French male voice with neural quality",
            gender="male",
            language="fr",
            language_name="French",
            country="FR",
            country_name="France",
            voice_type="neural",
            sample_rate=24000,
            quality="hd",
            features=["neural_quality", "real_time"],
            is_active=True,
            is_default=True
        ),
        Voice(
            provider_id=google_provider.id,
            name="fr-FR-Neural2-B",
            display_name="French (Neural2-B)",
            description="French female voice with neural quality",
            gender="female",
            language="fr",
            language_name="French",
            country="FR",
            country_name="France",
            voice_type="neural",
            sample_rate=24000,
            quality="hd",
            features=["neural_quality", "real_time"],
            is_active=True,
            is_default=False
        ),
        Voice(
            provider_id=google_provider.id,
            name="de-DE-Neural2-A",
            display_name="German (Neural2-A)",
            description="German male voice with neural quality",
            gender="male",
            language="de",
            language_name="German",
            country="DE",
            country_name="Germany",
            voice_type="neural",
            sample_rate=24000,
            quality="hd",
            features=["neural_quality", "real_time"],
            is_active=True,
            is_default=True
        ),
        Voice(
            provider_id=google_provider.id,
            name="de-DE-Neural2-B",
            display_name="German (Neural2-B)",
            description="German female voice with neural quality",
            gender="female",
            language="de",
            language_name="German",
            country="DE",
            country_name="Germany",
            voice_type="neural",
            sample_rate=24000,
            quality="hd",
            features=["neural_quality", "real_time"],
            is_active=True,
            is_default=False
        ),
        Voice(
            provider_id=google_provider.id,
            name="it-IT-Neural2-A",
            display_name="Italian (Neural2-A)",
            description="Italian male voice with neural quality",
            gender="male",
            language="it",
            language_name="Italian",
            country="IT",
            country_name="Italy",
            voice_type="neural",
            sample_rate=24000,
            quality="hd",
            features=["neural_quality", "real_time"],
            is_active=True,
            is_default=True
        ),
        Voice(
            provider_id=google_provider.id,
            name="it-IT-Neural2-B",
            display_name="Italian (Neural2-B)",
            description="Italian female voice with neural quality",
            gender="female",
            language="it",
            language_name="Italian",
            country="IT",
            country_name="Italy",
            voice_type="neural",
            sample_rate=24000,
            quality="hd",
            features=["neural_quality", "real_time"],
            is_active=True,
            is_default=False
        )
    ]
    
    for voice in google_voices:
        await voice_service.create_voice(voice)
    
    # Azure voices
    azure_voices = [
        Voice(
            provider_id=azure_provider.id,
            name="en-US-JennyNeural",
            display_name="Jenny (Neural)",
            description="US English female neural voice",
            gender="female",
            language="en",
            language_name="English",
            country="US",
            country_name="United States",
            voice_type="neural",
            sample_rate=24000,
            quality="hd",
            features=["neural_quality", "real_time", "emotion_control"],
            is_active=True,
            is_default=True
        ),
        Voice(
            provider_id=azure_provider.id,
            name="en-US-GuyNeural",
            display_name="Guy (Neural)",
            description="US English male neural voice",
            gender="male",
            language="en",
            language_name="English",
            country="US",
            country_name="United States",
            voice_type="neural",
            sample_rate=24000,
            quality="hd",
            features=["neural_quality", "real_time", "emotion_control"],
            is_active=True,
            is_default=False
        ),
        Voice(
            provider_id=azure_provider.id,
            name="es-ES-ElviraNeural",
            display_name="Elvira (Neural)",
            description="Spanish female neural voice",
            gender="female",
            language="es",
            language_name="Spanish",
            country="ES",
            country_name="Spain",
            voice_type="neural",
            sample_rate=24000,
            quality="hd",
            features=["neural_quality", "real_time", "emotion_control"],
            is_active=True,
            is_default=True
        ),
        Voice(
            provider_id=azure_provider.id,
            name="es-ES-AlvaroNeural",
            display_name="Alvaro (Neural)",
            description="Spanish male neural voice",
            gender="male",
            language="es",
            language_name="Spanish",
            country="ES",
            country_name="Spain",
            voice_type="neural",
            sample_rate=24000,
            quality="hd",
            features=["neural_quality", "real_time", "emotion_control"],
            is_active=True,
            is_default=False
        ),
        Voice(
            provider_id=azure_provider.id,
            name="fr-FR-DeniseNeural",
            display_name="Denise (Neural)",
            description="French female neural voice",
            gender="female",
            language="fr",
            language_name="French",
            country="FR",
            country_name="France",
            voice_type="neural",
            sample_rate=24000,
            quality="hd",
            features=["neural_quality", "real_time", "emotion_control"],
            is_active=True,
            is_default=True
        ),
        Voice(
            provider_id=azure_provider.id,
            name="fr-FR-HenriNeural",
            display_name="Henri (Neural)",
            description="French male neural voice",
            gender="male",
            language="fr",
            language_name="French",
            country="FR",
            country_name="France",
            voice_type="neural",
            sample_rate=24000,
            quality="hd",
            features=["neural_quality", "real_time", "emotion_control"],
            is_active=True,
            is_default=False
        ),
        Voice(
            provider_id=azure_provider.id,
            name="de-DE-KatjaNeural",
            display_name="Katja (Neural)",
            description="German female neural voice",
            gender="female",
            language="de",
            language_name="German",
            country="DE",
            country_name="Germany",
            voice_type="neural",
            sample_rate=24000,
            quality="hd",
            features=["neural_quality", "real_time", "emotion_control"],
            is_active=True,
            is_default=True
        ),
        Voice(
            provider_id=azure_provider.id,
            name="de-DE-ConradNeural",
            display_name="Conrad (Neural)",
            description="German male neural voice",
            gender="male",
            language="de",
            language_name="German",
            country="DE",
            country_name="Germany",
            voice_type="neural",
            sample_rate=24000,
            quality="hd",
            features=["neural_quality", "real_time", "emotion_control"],
            is_active=True,
            is_default=False
        ),
        Voice(
            provider_id=azure_provider.id,
            name="it-IT-IsabellaNeural",
            display_name="Isabella (Neural)",
            description="Italian female neural voice",
            gender="female",
            language="it",
            language_name="Italian",
            country="IT",
            country_name="Italy",
            voice_type="neural",
            sample_rate=24000,
            quality="hd",
            features=["neural_quality", "real_time", "emotion_control"],
            is_active=True,
            is_default=True
        ),
        Voice(
            provider_id=azure_provider.id,
            name="it-IT-DiegoNeural",
            display_name="Diego (Neural)",
            description="Italian male neural voice",
            gender="male",
            language="it",
            language_name="Italian",
            country="IT",
            country_name="Italy",
            voice_type="neural",
            sample_rate=24000,
            quality="hd",
            features=["neural_quality", "real_time", "emotion_control"],
            is_active=True,
            is_default=False
        )
    ]
    
    for voice in azure_voices:
        await voice_service.create_voice(voice)
    
    print("Voice data population completed successfully!")
    print(f"Created {len([elevenlabs_provider, google_provider, azure_provider, deepgram_provider, openai_whisper_provider])} voice providers")
    print(f"Created {len(elevenlabs_voices) + len(google_voices) + len(azure_voices)} voices")


if __name__ == "__main__":
    asyncio.run(populate_voice_data())
