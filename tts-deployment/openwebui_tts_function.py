"""
title: KasaAI TTS Integration
author: KasaAI Team
version: 1.0.0
description: Integrate KasaAI TTS services (Coqui, MeloTTS, OpenVoice, Kokoro) with Open WebUI
"""

import requests
import json
from typing import Optional, Literal

class Tools:
    """
    KasaAI TTS Tools for Open WebUI

    This class provides functions to synthesize speech using various TTS providers
    deployed in the KasaAI infrastructure.
    """

    def __init__(self):
        self.providers = {
            # Local GPU Services
            "coqui": {
                "url": "https://coqui.ailabsafrica.com",
                "description": "XTTS v2 - Voice cloning with Ghanaian voices (Twi support)",
                "default_speaker": "twi_female_1",
                "location": "Local GPU"
            },
            "melotts": {
                "url": "https://melotts.ailabsafrica.com",
                "description": "Fast multilingual TTS",
                "default_speaker": "EN-US",
                "location": "Local GPU"
            },
            "openvoice": {
                "url": "https://openvoice.ailabsafrica.com",
                "description": "Voice cloning TTS",
                "default_speaker": None,
                "location": "Local GPU"
            },
            "chatterbox": {
                "url": "https://chatterbox.ailabsafrica.com",
                "description": "Resemble.ai TTS system",
                "default_speaker": None,
                "location": "Local GPU"
            },
            "kokoro": {
                "url": "https://kokoro.ailabsafrica.com",
                "description": "High-quality TTS",
                "default_speaker": None,
                "location": "Local GPU"
            },
            # RunPod GPU Services
            "f5tts": {
                "url": "https://f5tts.ailabsafrica.com",
                "description": "Flow-matching based TTS",
                "default_speaker": None,
                "location": "RunPod GPU"
            },
            "styletts": {
                "url": "https://styletts.ailabsafrica.com",
                "description": "High-quality expressive TTS",
                "default_speaker": None,
                "location": "RunPod GPU"
            },
            "kyutai": {
                "url": "https://kyutai.ailabsafrica.com",
                "description": "Real-time conversational AI with TTS",
                "default_speaker": None,
                "location": "RunPod GPU"
            }
        }

    def synthesize_speech(
        self,
        text: str,
        provider: Literal["coqui", "melotts", "openvoice", "chatterbox", "kokoro", "f5tts", "styletts", "kyutai"] = "coqui",
        language: str = "en",
        speaker: Optional[str] = None,
        speed: float = 1.0
    ) -> str:
        """
        Synthesize speech using KasaAI TTS services.

        Args:
            text: Text to synthesize
            provider: TTS provider to use
                - Local GPU: coqui, melotts, openvoice, chatterbox, kokoro
                - RunPod GPU: f5tts, styletts, kyutai
            language: Language code (en, tw for Twi, etc.)
            speaker: Speaker/voice ID (optional, uses provider default)
            speed: Speech speed multiplier (0.5-2.0)

        Returns:
            Result message with audio URL or error

        Examples:
            synthesize_speech("Hello, welcome to KasaAI", "coqui", "en")
            synthesize_speech("Akwaaba", "coqui", "tw", "twi_female_1")
            synthesize_speech("High quality speech", "styletts", "en")
        """

        if provider not in self.providers:
            available = ", ".join(self.providers.keys())
            return f"❌ Error: Unknown provider '{provider}'. Available: {available}"

        provider_config = self.providers[provider]

        try:
            # Prepare request payload
            payload = {
                "text": text,
                "language": language,
                "speed": speed
            }

            # Add speaker if provided, otherwise use default
            if speaker:
                payload["speaker_id"] = speaker
            elif provider_config["default_speaker"]:
                payload["speaker_id"] = provider_config["default_speaker"]

            # Make API request
            endpoint = f"{provider_config['url']}/synthesize"
            response = requests.post(
                endpoint,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                audio_url = result.get("audio_url", "")

                return f"""✅ Speech synthesized successfully!

**Provider:** {provider.upper()}
**Language:** {language}
**Text:** {text[:100]}{'...' if len(text) > 100 else ''}

**Audio URL:** {audio_url}

You can download or play the audio from the URL above.
"""
            else:
                return f"❌ Error {response.status_code}: {response.text}"

        except requests.exceptions.Timeout:
            return f"⏱️ Error: Request timed out. The text might be too long or the service is busy."
        except requests.exceptions.ConnectionError:
            return f"🔌 Error: Could not connect to {provider_config['url']}. Service might be offline."
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def list_voices(
        self,
        provider: Literal["coqui", "melotts", "openvoice", "chatterbox", "kokoro", "f5tts", "styletts", "kyutai"] = "coqui"
    ) -> str:
        """
        List available voices/speakers for a TTS provider.

        Args:
            provider: TTS provider (coqui, melotts, openvoice, kokoro)

        Returns:
            List of available voices
        """

        if provider not in self.providers:
            available = ", ".join(self.providers.keys())
            return f"❌ Error: Unknown provider '{provider}'. Available: {available}"

        provider_config = self.providers[provider]

        try:
            endpoint = f"{provider_config['url']}/speakers"
            response = requests.get(endpoint, timeout=10)

            if response.status_code == 200:
                result = response.json()
                speakers = result.get("speakers", [])

                if not speakers:
                    return f"ℹ️ No speaker list available for {provider}"

                speaker_list = "\n".join([f"- {s}" for s in speakers])
                return f"""📢 Available voices for {provider.upper()}:

{speaker_list}

Use these speaker IDs in the synthesize_speech function.
"""
            else:
                return f"⚠️ Could not fetch speaker list: {response.status_code}"

        except Exception as e:
            return f"❌ Error: {str(e)}"

    def list_languages(
        self,
        provider: Literal["coqui", "melotts", "openvoice", "chatterbox", "kokoro", "f5tts", "styletts", "kyutai"] = "coqui"
    ) -> str:
        """
        List supported languages for a TTS provider.

        Args:
            provider: TTS provider (coqui, melotts, openvoice, kokoro)

        Returns:
            List of supported languages
        """

        if provider not in self.providers:
            available = ", ".join(self.providers.keys())
            return f"❌ Error: Unknown provider '{provider}'. Available: {available}"

        provider_config = self.providers[provider]

        try:
            endpoint = f"{provider_config['url']}/languages"
            response = requests.get(endpoint, timeout=10)

            if response.status_code == 200:
                result = response.json()
                languages = result.get("languages", [])

                if not languages:
                    return f"ℹ️ No language list available for {provider}"

                lang_list = "\n".join([f"- {lang}" for lang in languages])
                return f"""🌍 Supported languages for {provider.upper()}:

{lang_list}

Use these language codes in the synthesize_speech function.
"""
            else:
                return f"⚠️ Could not fetch language list: {response.status_code}"

        except Exception as e:
            return f"❌ Error: {str(e)}"

    def get_provider_info(self) -> str:
        """
        Get information about all available TTS providers.

        Returns:
            Information about all TTS providers
        """

        info = "🎙️ **KasaAI TTS Providers** (8 Total)\n\n"

        # Group by location
        local_providers = {k: v for k, v in self.providers.items() if v['location'] == 'Local GPU'}
        runpod_providers = {k: v for k, v in self.providers.items() if v['location'] == 'RunPod GPU'}

        # Local GPU providers
        info += "## 🖥️ Local GPU Services (20GB VRAM)\n\n"
        for name, config in local_providers.items():
            info += f"**{name.upper()}**\n"
            info += f"- URL: {config['url']}\n"
            info += f"- Description: {config['description']}\n"
            if config['default_speaker']:
                info += f"- Default Speaker: {config['default_speaker']}\n"
            info += "\n"

        # RunPod GPU providers
        info += "\n## ☁️ RunPod GPU Services (48GB VRAM)\n\n"
        for name, config in runpod_providers.items():
            info += f"**{name.upper()}**\n"
            info += f"- URL: {config['url']}\n"
            info += f"- Description: {config['description']}\n"
            if config['default_speaker']:
                info += f"- Default Speaker: {config['default_speaker']}\n"
            info += "\n"

        info += "\n## 📝 Usage Examples\n\n"
        info += '```python\n'
        info += '# Local GPU - Coqui with Twi support\n'
        info += 'synthesize_speech("Hello from Ghana!", "coqui", "en")\n'
        info += 'synthesize_speech("Akwaaba", "coqui", "tw", "twi_female_1")\n\n'
        info += '# Local GPU - Fast MeloTTS\n'
        info += 'synthesize_speech("Quick synthesis", "melotts", "en")\n\n'
        info += '# RunPod GPU - High quality StyleTTS2\n'
        info += 'synthesize_speech("Expressive speech", "styletts", "en")\n\n'
        info += '# List voices and languages\n'
        info += 'list_voices("coqui")\n'
        info += 'list_languages("melotts")\n'
        info += '```\n\n'
        info += '**💡 Tip:** Use local GPU providers for faster responses, RunPod for highest quality!'

        return info


# For testing
if __name__ == "__main__":
    tools = Tools()

    # Test synthesize
    result = tools.synthesize_speech(
        "Hello, this is a test from KasaAI TTS",
        provider="coqui",
        language="en"
    )
    print(result)
