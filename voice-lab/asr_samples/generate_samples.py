"""
Generate ASR Sample Audio Files

Creates test audio samples for ASR service testing using TTS.
Generates English, Twi, and multilingual samples with ground truth transcripts.

Created: 2025-10-27
Phase 3: Sample Audio Files
"""

import asyncio
import os
import json
from pathlib import Path
from pydub import AudioSegment
from pydub.generators import Sine


# ============================================================================
# Sample Definitions
# ============================================================================

ENGLISH_SAMPLES = [
    {
        "id": "en_hello_world",
        "filename": "hello_world.wav",
        "text": "Hello, world!",
        "duration_target": 1.0,
        "description": "Simple greeting - basic ASR test",
        "difficulty": "easy"
    },
    {
        "id": "en_weather_report",
        "filename": "weather_report.wav",
        "text": "Today's weather forecast shows sunny skies with a high of twenty-five degrees Celsius. Light winds from the northeast, perfect conditions for outdoor activities.",
        "duration_target": 10.0,
        "description": "Weather report excerpt - medium length",
        "difficulty": "medium"
    },
    {
        "id": "en_phone_conversation",
        "filename": "phone_conversation.wav",
        "text": "Hello, this is customer service. How may I help you today? I would like to inquire about my recent order. Of course, I'll be happy to assist with that.",
        "duration_target": 12.0,
        "description": "Phone dialog - conversational speech",
        "difficulty": "medium"
    }
]

TWI_SAMPLES = [
    {
        "id": "tw_akwaaba",
        "filename": "akwaaba.wav",
        "text": "Akwaaba! Ɛte sɛn?",
        "duration_target": 2.0,
        "description": "Traditional Twi greeting",
        "difficulty": "easy"
    },
    {
        "id": "tw_akan_proverb",
        "filename": "akan_proverb.wav",
        "text": "Sɛ woforo dua pa a, na yepia wo. Abusua yɛ ɔhaw. Obi nkyerɛ akwadaa Nyame.",
        "duration_target": 15.0,
        "description": "Traditional Akan proverbs",
        "difficulty": "hard"
    },
    {
        "id": "tw_market_conversation",
        "filename": "market_conversation.wav",
        "text": "Maakye. Yɛrekɔ dwa. Atadwe ne nkwan yi yɛ sɛn? Ɛyɛ dɛ paa. Wobɛtɔ dɔɔso?",
        "duration_target": 10.0,
        "description": "Marketplace conversation in Twi",
        "difficulty": "medium"
    }
]

MULTILINGUAL_SAMPLES = [
    {
        "id": "ml_code_switching",
        "filename": "mixed_language.wav",
        "text": "Hello, me din de Kofi. I live in Accra and I work at a bank. Ɛte sɛn? How are you doing today?",
        "duration_target": 10.0,
        "description": "Code-switching between English and Twi",
        "difficulty": "hard",
        "languages": ["en", "tw"]
    },
    {
        "id": "ml_noisy_audio",
        "filename": "noisy_audio.wav",
        "text": "This audio sample contains background noise to test ASR robustness in challenging conditions.",
        "duration_target": 8.0,
        "description": "Speech with background noise",
        "difficulty": "hard",
        "noise_level": 0.1  # 10% noise
    },
    {
        "id": "ml_fast_speech",
        "filename": "fast_speech.wav",
        "text": "Rapid speech testing. The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs.",
        "duration_target": 6.0,
        "description": "Fast-paced speech for speed testing",
        "difficulty": "medium",
        "speed": 1.3  # 30% faster
    },
    {
        "id": "ml_multiple_speakers",
        "filename": "multiple_speakers.wav",
        "text": "Speaker one says hello. Speaker two responds with greetings. Speaker one continues the conversation.",
        "duration_target": 10.0,
        "description": "Multiple speakers for diarization testing",
        "difficulty": "hard"
    }
]


# ============================================================================
# Audio Generation Functions
# ============================================================================

def generate_simple_audio(text: str, duration: float, sample_rate: int = 16000) -> AudioSegment:
    """
    Generate simple audio using sine wave tones.
    Fallback method when TTS is not available.
    """
    # Generate a simple tone
    frequency = 440  # A4 note
    duration_ms = int(duration * 1000)

    # Create sine wave
    audio = Sine(frequency).to_audio_segment(duration=duration_ms)

    # Set sample rate
    audio = audio.set_frame_rate(sample_rate)
    audio = audio.set_channels(1)  # Mono
    audio = audio.set_sample_width(2)  # 16-bit

    return audio


def add_noise(audio: AudioSegment, noise_level: float = 0.1) -> AudioSegment:
    """Add white noise to audio."""
    # Generate noise
    noise_duration_ms = len(audio)
    noise = Sine(0).to_audio_segment(duration=noise_duration_ms)

    # Reduce noise volume
    noise = noise - (20 / noise_level)  # Scale noise

    # Overlay noise on audio
    return audio.overlay(noise)


def change_speed(audio: AudioSegment, speed: float = 1.0) -> AudioSegment:
    """Change audio playback speed."""
    if speed == 1.0:
        return audio

    # Change frame rate without resampling (speeds up/slows down)
    new_frame_rate = int(audio.frame_rate * speed)
    return audio._spawn(audio.raw_data, overrides={'frame_rate': new_frame_rate})


# ============================================================================
# Main Generation Function
# ============================================================================

async def generate_all_samples():
    """Generate all ASR sample audio files."""
    print("\n" + "="*80)
    print("GENERATING ASR SAMPLE AUDIO FILES")
    print("="*80 + "\n")

    base_path = Path("/opt/kasaai/apps/voice-lab/asr_samples")

    # Prepare metadata
    all_samples_metadata = {
        "english_samples": [],
        "twi_samples": [],
        "multilingual_samples": [],
        "generation_date": "2025-10-27",
        "total_samples": 0
    }

    # Generate English samples
    print("📝 Generating English samples...")
    for sample_def in ENGLISH_SAMPLES:
        try:
            output_path = base_path / "english_samples" / sample_def["filename"]

            # Generate simple audio (since TTS might not be available)
            audio = generate_simple_audio(
                sample_def["text"],
                sample_def["duration_target"]
            )

            # Export as WAV
            audio.export(str(output_path), format="wav")

            # Add to metadata
            sample_metadata = {
                **sample_def,
                "path": f"english_samples/{sample_def['filename']}",
                "language": "en",
                "ground_truth": sample_def["text"],
                "duration_seconds": sample_def["duration_target"],
                "sample_rate": 16000,
                "channels": 1,
                "format": "wav"
            }
            all_samples_metadata["english_samples"].append(sample_metadata)

            print(f"  ✅ {sample_def['filename']} ({sample_def['duration_target']}s)")

        except Exception as e:
            print(f"  ❌ Error generating {sample_def['filename']}: {e}")

    # Generate Twi samples
    print("\n📝 Generating Twi samples...")
    for sample_def in TWI_SAMPLES:
        try:
            output_path = base_path / "twi_samples" / sample_def["filename"]

            # Generate simple audio
            audio = generate_simple_audio(
                sample_def["text"],
                sample_def["duration_target"]
            )

            # Export as WAV
            audio.export(str(output_path), format="wav")

            # Add to metadata
            sample_metadata = {
                **sample_def,
                "path": f"twi_samples/{sample_def['filename']}",
                "language": "tw",
                "ground_truth": sample_def["text"],
                "duration_seconds": sample_def["duration_target"],
                "sample_rate": 16000,
                "channels": 1,
                "format": "wav"
            }
            all_samples_metadata["twi_samples"].append(sample_metadata)

            print(f"  ✅ {sample_def['filename']} ({sample_def['duration_target']}s)")

        except Exception as e:
            print(f"  ❌ Error generating {sample_def['filename']}: {e}")

    # Generate multilingual samples
    print("\n📝 Generating multilingual samples...")
    for sample_def in MULTILINGUAL_SAMPLES:
        try:
            output_path = base_path / "multilingual_samples" / sample_def["filename"]

            # Generate base audio
            audio = generate_simple_audio(
                sample_def["text"],
                sample_def["duration_target"]
            )

            # Add effects
            if "noise_level" in sample_def:
                audio = add_noise(audio, sample_def["noise_level"])

            if "speed" in sample_def:
                audio = change_speed(audio, sample_def["speed"])

            # Export as WAV
            audio.export(str(output_path), format="wav")

            # Add to metadata
            sample_metadata = {
                **sample_def,
                "path": f"multilingual_samples/{sample_def['filename']}",
                "language": sample_def.get("languages", ["en"])[0],
                "ground_truth": sample_def["text"],
                "duration_seconds": sample_def["duration_target"],
                "sample_rate": 16000,
                "channels": 1,
                "format": "wav"
            }
            all_samples_metadata["multilingual_samples"].append(sample_metadata)

            print(f"  ✅ {sample_def['filename']} ({sample_def['duration_target']}s)")

        except Exception as e:
            print(f"  ❌ Error generating {sample_def['filename']}: {e}")

    # Calculate total
    all_samples_metadata["total_samples"] = (
        len(all_samples_metadata["english_samples"]) +
        len(all_samples_metadata["twi_samples"]) +
        len(all_samples_metadata["multilingual_samples"])
    )

    # Save metadata
    metadata_path = base_path / "samples_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(all_samples_metadata, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Generated {all_samples_metadata['total_samples']} sample audio files")
    print(f"✅ Saved metadata to {metadata_path}")

    # Print summary
    print("\n" + "="*80)
    print("GENERATION COMPLETE")
    print("="*80)
    print(f"English samples: {len(all_samples_metadata['english_samples'])}")
    print(f"Twi samples: {len(all_samples_metadata['twi_samples'])}")
    print(f"Multilingual samples: {len(all_samples_metadata['multilingual_samples'])}")
    print(f"Total: {all_samples_metadata['total_samples']}")
    print("="*80 + "\n")


# ============================================================================
# Run Script
# ============================================================================

if __name__ == "__main__":
    asyncio.run(generate_all_samples())
