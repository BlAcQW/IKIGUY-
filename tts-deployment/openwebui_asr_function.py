"""
title: KasaAI ASR Integration
author: KasaAI Team
version: 1.0.0
description: Integrate KasaAI ASR (Automatic Speech Recognition) services with Open WebUI for Ghanaian languages
"""

import requests
import json
import base64
from typing import Optional, Literal

class Tools:
    """
    KasaAI ASR Tools for Open WebUI

    This class provides functions to transcribe audio using various ASR models
    specialized for Ghanaian languages (Twi/Akan).
    """

    def __init__(self):
        self.api_base_url = "https://api.ailabsafrica.com/api/voice-lab"
        self.models = {
            "akan-whisper": {
                "name": "Akan Whisper",
                "description": "92.9% accuracy for Twi/Akan languages",
                "accuracy": 0.929,
                "languages": ["tw"],
                "dialects": ["asante", "akuapem", "fante"],
                "best_for": "Production use - highest accuracy"
            },
            "faster-whisper": {
                "name": "Faster Whisper",
                "description": "Fast general-purpose transcription",
                "accuracy": 0.85,
                "languages": ["tw", "en", "multiple"],
                "dialects": [],
                "best_for": "Fast transcription, multilingual support"
            },
            "meta-mms": {
                "name": "Meta MMS-1B",
                "description": "Meta's multilingual speech model",
                "accuracy": 0.82,
                "languages": ["tw", "en", "1000+ languages"],
                "dialects": [],
                "best_for": "Wide language coverage"
            },
            "wav2vec2-akan": {
                "name": "Wav2Vec2 Akan",
                "description": "Specialized for Akan languages",
                "accuracy": 0.87,
                "languages": ["tw"],
                "dialects": ["asante", "akuapem"],
                "best_for": "Akan language specialization"
            }
        }

    def transcribe_audio(
        self,
        audio_base64: str,
        model: Literal["akan-whisper", "faster-whisper", "meta-mms", "wav2vec2-akan"] = "akan-whisper",
        language: str = "tw",
        dialect: str = "asante",
        return_timestamps: bool = False,
        enhance_text: bool = True
    ) -> str:
        """
        Transcribe audio to text using KasaAI ASR models.

        Args:
            audio_base64: Base64 encoded audio data (WAV, MP3, etc.)
            model: ASR model to use
                - akan-whisper: Best accuracy for Twi/Akan (92.9%)
                - faster-whisper: Fast multilingual
                - meta-mms: Wide language support
                - wav2vec2-akan: Akan specialist
            language: Language code (tw for Twi, en for English)
            dialect: Dialect (asante, akuapem, fante)
            return_timestamps: Get word-level timestamps
            enhance_text: Apply text enhancements (numbers, dates, etc.)

        Returns:
            Transcription result with text and metadata

        Examples:
            transcribe_audio(audio_base64, "akan-whisper", "tw", "asante")
            transcribe_audio(audio_base64, "faster-whisper", "en")
        """

        if model not in self.models:
            available = ", ".join(self.models.keys())
            return f"❌ Error: Unknown model '{model}'. Available: {available}"

        model_info = self.models[model]

        try:
            # Prepare request
            payload = {
                "audio_base64": audio_base64,
                "language": language,
                "dialect": dialect,
                "model": model,
                "return_timestamps": return_timestamps,
                "enhance_text": enhance_text
            }

            # Make API request
            endpoint = f"{self.api_base_url}/transcribe"
            response = requests.post(
                endpoint,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()

                # Format response
                output = f"""✅ **Transcription Complete!**

**Model:** {model_info['name']} ({model_info['accuracy']*100:.1f}% accuracy)
**Language:** {language}
**Dialect:** {dialect if dialect else 'Auto-detect'}
**Duration:** {result.get('duration', 0):.2f}s
**Processing Time:** {result.get('processing_time', 0):.2f}s
**Confidence:** {result.get('confidence', 0):.2%}

**Transcribed Text:**
{result.get('text', '')}
"""

                # Add enhanced text if available
                if result.get('enhanced_text') and result['enhanced_text'] != result.get('text'):
                    output += f"\n**Enhanced Text:**\n{result['enhanced_text']}\n"

                # Add timestamps if requested
                if return_timestamps and result.get('timestamps'):
                    output += "\n**Timestamps:**\n```\n"
                    for ts in result['timestamps'][:10]:  # Show first 10
                        output += f"{ts['start']:.2f}s - {ts['end']:.2f}s: {ts['word']}\n"
                    if len(result['timestamps']) > 10:
                        output += f"... and {len(result['timestamps']) - 10} more\n"
                    output += "```"

                return output

            else:
                return f"❌ Error {response.status_code}: {response.text}"

        except requests.exceptions.Timeout:
            return f"⏱️ Error: Request timed out. Audio might be too long."
        except requests.exceptions.ConnectionError:
            return f"🔌 Error: Could not connect to {self.api_base_url}. Service might be offline."
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def list_asr_models(self) -> str:
        """
        List all available ASR models and their capabilities.

        Returns:
            Detailed information about available ASR models
        """

        info = "🎤 **KasaAI ASR Models** (4 Total)\n\n"

        for model_id, model_info in self.models.items():
            info += f"## **{model_info['name']}** (`{model_id}`)\n\n"
            info += f"- **Description:** {model_info['description']}\n"
            info += f"- **Accuracy:** {model_info['accuracy']*100:.1f}%\n"
            info += f"- **Languages:** {', '.join(model_info['languages'])}\n"
            if model_info['dialects']:
                info += f"- **Dialects:** {', '.join(model_info['dialects'])}\n"
            info += f"- **Best For:** {model_info['best_for']}\n\n"

        info += "\n## 🌟 **Recommendations**\n\n"
        info += "- **Twi/Akan Speech:** Use `akan-whisper` (highest accuracy)\n"
        info += "- **Fast Transcription:** Use `faster-whisper`\n"
        info += "- **Multiple Languages:** Use `meta-mms`\n"
        info += "- **Akan Specialist:** Use `wav2vec2-akan`\n\n"

        info += "## 📝 **Usage**\n\n"
        info += "```python\n"
        info += "# Transcribe Twi audio\n"
        info += 'transcribe_audio(audio_base64, "akan-whisper", "tw", "asante")\n\n'
        info += "# Fast English transcription\n"
        info += 'transcribe_audio(audio_base64, "faster-whisper", "en")\n\n'
        info += "# With timestamps\n"
        info += 'transcribe_audio(audio_base64, "akan-whisper", "tw", "asante", return_timestamps=True)\n'
        info += "```"

        return info

    def list_supported_languages(self, model: str = "akan-whisper") -> str:
        """
        List supported languages for a specific ASR model.

        Args:
            model: ASR model name

        Returns:
            List of supported languages and dialects
        """

        if model not in self.models:
            available = ", ".join(self.models.keys())
            return f"❌ Error: Unknown model '{model}'. Available: {available}"

        model_info = self.models[model]

        info = f"🌍 **Languages for {model_info['name']}**\n\n"
        info += f"**Supported Languages:**\n"
        for lang in model_info['languages']:
            info += f"- {lang}\n"

        if model_info['dialects']:
            info += f"\n**Supported Dialects:**\n"
            for dialect in model_info['dialects']:
                info += f"- {dialect}\n"

        return info

    def get_model_info(self, model: str = "akan-whisper") -> str:
        """
        Get detailed information about a specific ASR model.

        Args:
            model: ASR model name

        Returns:
            Detailed model information
        """

        if model not in self.models:
            available = ", ".join(self.models.keys())
            return f"❌ Error: Unknown model '{model}'. Available: {available}"

        model_info = self.models[model]

        info = f"ℹ️ **{model_info['name']}** Model Info\n\n"
        info += f"**Model ID:** `{model}`\n"
        info += f"**Description:** {model_info['description']}\n"
        info += f"**Accuracy:** {model_info['accuracy']*100:.1f}%\n"
        info += f"**Languages:** {', '.join(model_info['languages'])}\n"
        if model_info['dialects']:
            info += f"**Dialects:** {', '.join(model_info['dialects'])}\n"
        info += f"**Best For:** {model_info['best_for']}\n\n"

        info += "**Usage Example:**\n```python\n"
        info += f'transcribe_audio(your_audio_base64, "{model}", "tw", "asante")\n'
        info += "```"

        return info

    def help(self) -> str:
        """
        Show help information for KasaAI ASR tools.

        Returns:
            Help and usage information
        """

        return """🎤 **KasaAI ASR Tools - Help**

## Available Functions

### 1. transcribe_audio()
Transcribe audio to text using Ghanaian ASR models.

**Parameters:**
- `audio_base64`: Base64 encoded audio
- `model`: ASR model (akan-whisper, faster-whisper, etc.)
- `language`: Language code (tw, en)
- `dialect`: Dialect (asante, akuapem, fante)
- `return_timestamps`: Get word timestamps (default: False)
- `enhance_text`: Apply text enhancements (default: True)

**Example:**
```
Transcribe this audio: [provide base64 audio]
Transcribe with Akan Whisper model in Asante Twi
```

### 2. list_asr_models()
List all available ASR models and their capabilities.

**Example:**
```
Show me all ASR models
List available transcription models
```

### 3. list_supported_languages()
Show supported languages for a specific model.

**Example:**
```
What languages does akan-whisper support?
List languages for faster-whisper
```

### 4. get_model_info()
Get detailed information about a specific model.

**Example:**
```
Tell me about the akan-whisper model
Get info for faster-whisper
```

## Quick Start

**Best for Twi/Akan:**
```
transcribe_audio(audio, "akan-whisper", "tw", "asante")
```

**Fast multilingual:**
```
transcribe_audio(audio, "faster-whisper", "en")
```

**With timestamps:**
```
transcribe_audio(audio, "akan-whisper", "tw", "asante", return_timestamps=True)
```

## Supported Languages

- **Twi/Akan** (asante, akuapem, fante dialects)
- **English**
- **1000+ languages** (with meta-mms model)

## Features

✅ 92.9% accuracy for Twi/Akan (best in Ghana!)
✅ Word-level timestamps
✅ Text enhancement (numbers, dates)
✅ Dialect-specific models
✅ Fast transcription
✅ Production-ready

**API Endpoint:** https://api.ailabsafrica.com/api/voice-lab/transcribe
"""


# For testing
if __name__ == "__main__":
    tools = Tools()

    # Show available models
    print(tools.list_asr_models())
