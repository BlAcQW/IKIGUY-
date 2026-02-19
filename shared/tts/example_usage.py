"""
Example Usage of Shared TTS Module
Demonstrates how to use the TTS module in Kasaai applications.
"""

import asyncio
from pathlib import Path
from typing import Optional

# Import from shared module
from shared.tts import (
    TTSClient,
    AsyncTTSClient,
    TTSProvider,
    AudioFormat,
    AudioUtils,
)
from shared.tts.websocket import ConversationManager


def example_simple_synthesis():
    """Example: Simple text-to-speech synthesis."""
    print("\n=== Simple Synthesis Example ===")

    client = TTSClient()

    # Synthesize with auto-selected provider
    response = client.synthesize("Hello from Kasaai TTS system!")
    print(f"Provider used: {response.provider.value}")
    print(f"Audio size: {len(response.audio)} bytes")

    # Save to file
    output_path = Path("/tmp/simple_output.wav")
    AudioUtils.save_audio(response.audio, output_path, AudioFormat.WAV)
    print(f"Saved to: {output_path}")


def example_provider_selection():
    """Example: Specific provider selection."""
    print("\n=== Provider Selection Example ===")

    client = TTSClient()

    # Check available providers
    statuses = client.get_all_statuses()
    print("Available providers:")
    for provider_id, status in statuses.items():
        if status.status == "online":
            print(f"  ✅ {status.name}: {status.description}")

    # Use specific provider
    try:
        response = client.synthesize(
            "This is synthesized using F5-TTS",
            provider=TTSProvider.F5TTS,
            language="en"
        )
        print(f"Successfully used {response.provider.value}")
    except Exception as e:
        print(f"Error: {e}")


def example_voice_cloning():
    """Example: Voice cloning with reference audio."""
    print("\n=== Voice Cloning Example ===")

    client = TTSClient()

    # Use Ghanaian voice sample
    reference_path = Path("/opt/kasaai/apps/voice-lab/voices/nana_aba.wav")

    if reference_path.exists():
        # Load reference audio
        reference_audio, _ = AudioUtils.load_audio(reference_path)

        # Clone voice
        try:
            response = client.clone_voice(
                text="This is spoken in Nana Aba's voice",
                reference_audio=reference_audio,
                provider=TTSProvider.F5TTS  # or STYLETTS2
            )
            print(f"Voice cloned successfully using {response.provider.value}")

            # Save output
            output_path = Path("/tmp/cloned_voice.wav")
            AudioUtils.save_audio(response.audio, output_path)
            print(f"Saved to: {output_path}")
        except Exception as e:
            print(f"Voice cloning error: {e}")
    else:
        print("Reference audio not found")


async def example_batch_processing():
    """Example: Batch text processing."""
    print("\n=== Batch Processing Example ===")

    async with AsyncTTSClient() as client:
        texts = [
            "First announcement message",
            "Second announcement message",
            "Third announcement message",
            "Fourth announcement message",
        ]

        # Process in parallel
        batch_response = await client.synthesize_batch(
            texts,
            provider=TTSProvider.F5TTS,
            parallel=True,
            max_workers=3,
            language="en"
        )

        print(f"Total items: {batch_response.total_items}")
        print(f"Successful: {batch_response.successful}")
        print(f"Failed: {batch_response.failed}")
        print(f"Processing time: {batch_response.processing_time:.2f}s")

        # Save all outputs
        for i, result in enumerate(batch_response.results):
            if result:
                output_path = Path(f"/tmp/batch_output_{i}.wav")
                AudioUtils.save_audio(result.audio, output_path)
                print(f"  Saved: {output_path}")


async def example_real_time_conversation():
    """Example: Real-time conversation with Moshi."""
    print("\n=== Real-time Conversation Example ===")

    # Audio callback handlers
    async def on_audio(audio_data: bytes):
        print(f"Received audio: {len(audio_data)} bytes")
        # Here you would play the audio or process it
        # e.g., play_audio(audio_data)

    async def on_text(text: str):
        print(f"Moshi says: {text}")

    # Start conversation
    manager = ConversationManager()

    try:
        client = await manager.start_conversation(
            initial_text="Hello Moshi, can you introduce yourself?",
            on_audio=on_audio,
            on_text=on_text
        )

        print("Conversation started. Waiting for response...")

        # Keep conversation running for 10 seconds
        await asyncio.sleep(10)

        # Send more text
        await client.send_text("What can you help me with?")

        # Wait for response
        await asyncio.sleep(5)

    except Exception as e:
        print(f"Conversation error: {e}")
    finally:
        await manager.stop_conversation()
        print("Conversation ended")


def example_audio_processing():
    """Example: Audio processing utilities."""
    print("\n=== Audio Processing Example ===")

    # Generate test audio (440Hz sine wave)
    import numpy as np
    sample_rate = 22050
    duration = 2.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_array = np.sin(2 * np.pi * 440 * t).astype(np.float32) * 0.3

    # Convert to WAV
    wav_data = AudioUtils.numpy_to_bytes(
        audio_array,
        AudioFormat.WAV,
        sample_rate
    )
    print(f"Generated WAV: {len(wav_data)} bytes")

    # Get duration
    duration = AudioUtils.get_audio_duration(wav_data, AudioFormat.WAV, sample_rate)
    print(f"Duration: {duration:.2f} seconds")

    # Normalize audio
    normalized = AudioUtils.normalize_audio(
        wav_data,
        AudioFormat.WAV,
        sample_rate,
        target_db=-20.0
    )
    print("Audio normalized to -20dB")

    # Resample
    resampled = AudioUtils.resample(
        wav_data,
        AudioFormat.WAV,
        input_rate=22050,
        output_rate=16000
    )
    print("Resampled from 22050Hz to 16000Hz")

    # Convert to base64 for transmission
    encoded = AudioUtils.encode_base64(wav_data)
    print(f"Base64 encoded: {len(encoded)} characters")


async def example_multi_language():
    """Example: Multi-language synthesis."""
    print("\n=== Multi-language Example ===")

    async with AsyncTTSClient() as client:
        languages = [
            ("en", "Hello, welcome to Kasaai"),
            ("zh", "欢迎来到Kasaai"),
            ("ja", "Kasaaiへようこそ"),
            ("ko", "Kasaai에 오신 것을 환영합니다"),
        ]

        for lang, text in languages:
            try:
                response = await client.synthesize(
                    text,
                    provider=TTSProvider.F5TTS,  # Supports multiple languages
                    language=lang
                )
                print(f"{lang}: Synthesized {len(response.audio)} bytes")

                # Save each language
                output_path = Path(f"/tmp/multilang_{lang}.wav")
                AudioUtils.save_audio(response.audio, output_path)

            except Exception as e:
                print(f"{lang}: Failed - {e}")


async def example_error_handling():
    """Example: Proper error handling."""
    print("\n=== Error Handling Example ===")

    from shared.tts import (
        ProviderNotAvailableError,
        AudioProcessingError,
        InvalidRequestError,
    )

    async with AsyncTTSClient() as client:
        # Handle provider not available
        try:
            response = await client.synthesize(
                "Test",
                provider=TTSProvider.COQUI_XTTS  # Currently offline
            )
        except ProviderNotAvailableError as e:
            print(f"Provider error: {e}")
            # Fallback to auto-selection
            print("Falling back to auto-selection...")
            response = await client.synthesize("Test")
            print(f"Used provider: {response.provider.value}")

        # Handle invalid request
        try:
            response = await client.synthesize(
                "",  # Empty text
                provider=TTSProvider.F5TTS
            )
        except InvalidRequestError as e:
            print(f"Invalid request: {e}")

        # Handle audio processing error
        try:
            # Simulate bad audio data
            AudioUtils.bytes_to_numpy(
                b"invalid_audio_data",
                AudioFormat.WAV,
                22050
            )
        except AudioProcessingError as e:
            print(f"Audio processing error: {e}")


def main():
    """Run all examples."""
    print("=" * 50)
    print("TTS Module Examples")
    print("=" * 50)

    # Synchronous examples
    example_simple_synthesis()
    example_provider_selection()
    example_voice_cloning()
    example_audio_processing()

    # Asynchronous examples
    print("\nRunning async examples...")
    asyncio.run(example_batch_processing())
    asyncio.run(example_multi_language())
    asyncio.run(example_error_handling())

    # Real-time conversation (requires Moshi to be online)
    try:
        asyncio.run(example_real_time_conversation())
    except Exception as e:
        print(f"Conversation example skipped: {e}")

    print("\n" + "=" * 50)
    print("Examples completed!")


if __name__ == "__main__":
    main()