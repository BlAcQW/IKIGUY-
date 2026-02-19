"""
TTS Provider Implementations
Base class and specific provider implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, AsyncGenerator
import aiohttp
import asyncio
import json
import logging
from datetime import datetime

from .models import (
    TTSProvider,
    TTSRequest,
    TTSResponse,
    VoiceCloneRequest,
    ConversationRequest,
    ProviderStatus,
    AudioFormat,
)
from .config import TTSProviderConfig, get_provider_config
from .exceptions import (
    ProviderNotAvailableError,
    ModelNotLoadedError,
    AudioProcessingError,
    ConnectionError,
    TimeoutError,
)

logger = logging.getLogger(__name__)


class BaseTTSProvider(ABC):
    """Base class for TTS providers."""

    def __init__(self, config: Optional[TTSProviderConfig] = None):
        """Initialize TTS provider.

        Args:
            config: Provider configuration (uses default if not provided)
        """
        self.config = config or self._get_default_config()
        self.session: Optional[aiohttp.ClientSession] = None
        self._is_available = False
        self._last_health_check: Optional[datetime] = None

    @abstractmethod
    def _get_default_config(self) -> TTSProviderConfig:
        """Get default configuration for this provider."""
        pass

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self):
        """Establish connection to the provider."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.config.endpoint.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        await self.check_health()

    async def disconnect(self):
        """Close connection to the provider."""
        if self.session:
            await self.session.close()
            self.session = None

    async def check_health(self) -> ProviderStatus:
        """Check provider health status.

        Returns:
            Provider status

        Raises:
            ConnectionError: If health check fails
        """
        try:
            url = f"{self.config.endpoint.base_url}{self.config.endpoint.health_path}"

            if not self.session:
                await self.connect()

            async with self.session.get(url) as response:
                if response.status == 200:
                    # Try to parse as JSON, but accept HTML responses for Gradio/web interfaces
                    content_type = response.headers.get("content-type", "").lower()

                    if "application/json" in content_type:
                        data = await response.json()
                    elif "text/html" in content_type:
                        # HTML response (Gradio apps) - just confirm it's responding
                        await response.text()  # Consume the response
                        data = {}  # Empty dict for HTML responses
                    else:
                        # Unknown content type, try JSON first
                        try:
                            data = await response.json()
                        except:
                            await response.text()  # Consume as text
                            data = {}

                    self._is_available = True
                    self._last_health_check = datetime.utcnow()

                    return ProviderStatus(
                        provider=self.config.id,
                        name=self.config.name,
                        endpoint=self.config.endpoint.base_url,
                        status="online",
                        capabilities=self.config.capabilities,
                        description=self.config.description,
                        model_loaded=data.get("model_loaded", False),
                        gpu_memory_gb=self._parse_gpu_memory(data),
                        error=data.get("error"),
                        last_check=self._last_health_check
                    )
                else:
                    self._is_available = False
                    raise ConnectionError(
                        self.config.id.value,
                        self.config.endpoint.base_url,
                        f"Health check returned {response.status}"
                    )

        except aiohttp.ClientError as e:
            self._is_available = False
            raise ConnectionError(
                self.config.id.value,
                self.config.endpoint.base_url,
                str(e)
            )

    def _parse_gpu_memory(self, data: Dict[str, Any]) -> Optional[float]:
        """Parse GPU memory from health check response."""
        for key in ["gpu_memory_allocated_gb", "gpu_memory_gb", "memory_gb"]:
            if key in data:
                try:
                    return float(str(data[key]).replace("GB", "").strip())
                except (ValueError, TypeError):
                    pass
        return None

    @abstractmethod
    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        """Synthesize speech from text.

        Args:
            request: TTS request

        Returns:
            TTS response with audio

        Raises:
            ProviderNotAvailableError: If provider is not available
            AudioProcessingError: If synthesis fails
        """
        pass

    async def synthesize_with_clone(self, request: VoiceCloneRequest) -> TTSResponse:
        """Synthesize speech with voice cloning.

        Args:
            request: Voice clone request

        Returns:
            TTS response with cloned audio

        Raises:
            NotImplementedError: If provider doesn't support voice cloning
        """
        if not self.config.capabilities.voice_cloning:
            raise NotImplementedError(
                f"Provider {self.config.name} does not support voice cloning"
            )
        raise NotImplementedError("Voice cloning not implemented for this provider")


class F5TTSProvider(BaseTTSProvider):
    """F5-TTS provider implementation with Gradio API support."""

    def _get_default_config(self) -> TTSProviderConfig:
        """Get default F5-TTS configuration."""
        return get_provider_config(TTSProvider.F5TTS)

    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        """Synthesize speech using F5-TTS."""
        if not self._is_available:
            raise ProviderNotAvailableError(self.config.id.value)

        url = f"{self.config.endpoint.base_url}{self.config.endpoint.synthesize_path}"

        payload = {
            "text": request.text,
            "language": request.language,
            "speed": request.speed,
            "format": request.output_format.value,
            "sample_rate": request.sample_rate,
        }

        if request.speaker:
            payload["speaker"] = request.speaker

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    content_type = response.headers.get("content-type", "")

                    if "audio" in content_type:
                        audio_data = await response.read()
                        return TTSResponse(
                            audio=audio_data,
                            format=request.output_format,
                            sample_rate=request.sample_rate,
                            provider=self.config.id,
                            language=request.language,
                            speaker=request.speaker
                        )
                    else:
                        data = await response.json()
                        return TTSResponse(
                            audio_url=data.get("audio_url"),
                            format=request.output_format,
                            sample_rate=request.sample_rate,
                            provider=self.config.id,
                            language=request.language,
                            speaker=request.speaker,
                            metadata=data
                        )
                else:
                    error_text = await response.text()
                    raise AudioProcessingError(
                        f"Synthesis failed: {error_text}",
                        provider=self.config.id.value
                    )

        except asyncio.TimeoutError:
            raise TimeoutError(self.config.id.value, self.config.endpoint.timeout)
        except aiohttp.ClientError as e:
            raise ConnectionError(self.config.id.value, url, str(e))

    async def synthesize_with_clone(self, request: VoiceCloneRequest) -> TTSResponse:
        """Synthesize speech with voice cloning using Gradio API.

        Args:
            request: Voice clone request with reference audio

        Returns:
            TTS response with cloned audio
        """
        try:
            from gradio_client import Client, handle_file
            import tempfile
            import os

            # Save reference audio to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
                f.write(request.reference_audio)
                temp_path = f.name

            try:
                # Connect to Gradio app (base_url is the full Gradio URL)
                client = Client(self.config.endpoint.base_url)

                # Reference text to bypass ASR (CRITICAL for F5-TTS)
                ref_text = "This is a reference audio sample for voice cloning."

                # Call Gradio API
                result = client.predict(
                    handle_file(temp_path),  # ref_audio_input
                    ref_text,  # ref_text_input (MUST be non-empty)
                    request.text,  # gen_text_input
                    True,  # remove_silence
                    True,  # randomize_seed
                    0,  # seed_input
                    0.15,  # cross_fade_duration_slider
                    32,  # nfe_slider
                    1.0,  # speed_slider
                    api_name="/basic_tts"
                )

                # Read generated audio
                if result and result[0]:
                    with open(result[0], 'rb') as f:
                        audio_data = f.read()

                    return TTSResponse(
                        audio=audio_data,
                        format=request.output_format,
                        sample_rate=request.sample_rate,
                        provider=TTSProvider.F5TTS,
                        language=request.language,
                        metadata={"cloned": True, "method": "gradio_api"}
                    )
                else:
                    raise AudioProcessingError(
                        "No audio returned from F5-TTS",
                        provider=TTSProvider.F5TTS
                    )

            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            logger.error(f"F5-TTS voice cloning error: {e}")
            raise AudioProcessingError(
                f"F5-TTS voice cloning failed: {str(e)}",
                provider=TTSProvider.F5TTS
            ) from e


class StyleTTS2Provider(BaseTTSProvider):
    """StyleTTS2 provider implementation with Gradio API support."""

    def _get_default_config(self) -> TTSProviderConfig:
        """Get default StyleTTS2 configuration."""
        return get_provider_config(TTSProvider.STYLETTS2)

    async def _poll_gradio_result(
        self,
        base_url: str,
        endpoint_path: str,
        event_id: str,
        max_polls: int = 60,
        poll_interval: float = 0.5
    ) -> dict:
        """Poll Gradio event-based API for result.

        Gradio's /gradio_api/call/ endpoints use an event-based async pattern:
        1. POST to /gradio_api/call/{endpoint} returns {"event_id": "..."}
        2. Poll GET /gradio_api/call/{endpoint}/{event_id} until complete
        3. Response contains {"data": [...]} when ready

        Args:
            base_url: Base URL of the Gradio service
            endpoint_path: The endpoint path (e.g., "/gradio_api/call/basic_tts")
            event_id: Event ID returned from initial POST
            max_polls: Maximum number of polling attempts (default: 60)
            poll_interval: Seconds between polls (default: 0.5)

        Returns:
            The complete Gradio response dict containing "data" field

        Raises:
            AudioProcessingError: If polling fails or times out
        """
        poll_url = f"{base_url}{endpoint_path}/{event_id}"

        for attempt in range(max_polls):
            try:
                async with self.session.get(poll_url) as response:
                    if response.status == 200:
                        # Gradio returns Server-Sent Events (SSE) format
                        content_type = response.headers.get("content-type", "")

                        if content_type and "text/event-stream" in content_type:
                            # Parse SSE stream line by line
                            try:
                                async for line_bytes in response.content:
                                    try:
                                        line_text = line_bytes.decode('utf-8').strip()
                                        if line_text.startswith("data:"):
                                            data_json = line_text[5:].strip()
                                            if data_json and data_json != "[DONE]":
                                                try:
                                                    event_data = json.loads(data_json)
                                                    # Check if it's the final "complete" event with data
                                                    if isinstance(event_data, dict) and "data" in event_data:
                                                        logger.info(f"Gradio polling complete on attempt {attempt + 1}")
                                                        return event_data
                                                except json.JSONDecodeError:
                                                    continue
                                    except UnicodeDecodeError:
                                        continue
                            except (aiohttp.ClientPayloadError, aiohttp.ClientError):
                                # Incomplete stream - keep polling
                                pass
                        else:
                            # Regular JSON response
                            try:
                                result = await response.json()
                                if "data" in result:
                                    logger.info(f"Gradio polling complete on attempt {attempt + 1}")
                                    return result
                            except (json.JSONDecodeError, aiohttp.ContentTypeError):
                                # Invalid response - keep polling
                                pass
                    elif response.status == 404:
                        # Event not found yet, keep polling
                        pass
                    else:
                        # Log non-200/404 status but keep polling
                        try:
                            error_text = await response.text()
                            logger.debug(f"Gradio polling attempt {attempt + 1}: {response.status} - {error_text}")
                        except:
                            pass

                # Wait before next poll
                await asyncio.sleep(poll_interval)

            except asyncio.CancelledError:
                raise
            except Exception as e:
                # Log but continue polling
                logger.debug(f"Gradio polling attempt {attempt + 1} error: {type(e).__name__}")
                await asyncio.sleep(poll_interval)

        raise AudioProcessingError(
            f"Gradio polling timed out after {max_polls * poll_interval}s",
            provider=self.config.id.value
        )

    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        """Synthesize speech using StyleTTS2 via Gradio event polling."""
        if not self._is_available:
            raise ProviderNotAvailableError(self.config.id.value)

        url = f"{self.config.endpoint.base_url}{self.config.endpoint.synthesize_path}"

        # StyleTTS2 uses Gradio event-based API
        # The basic_tts endpoint expects: [text, emotion/style, speed]
        payload = {
            "data": [
                request.text,
                request.emotion or "neutral",  # emotion/style parameter
                request.speed or 1.0
            ]
        }

        logger.info(
            f"StyleTTS2 synthesis: text_length={len(request.text)}, "
            f"emotion={request.emotion}, speed={request.speed}"
        )

        try:
            # Step 1: Initiate synthesis and get event_id
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    init_result = await response.json()

                    if "event_id" not in init_result:
                        raise AudioProcessingError(
                            "No event_id in StyleTTS2 response",
                            provider=self.config.id.value
                        )

                    event_id = init_result["event_id"]
                    logger.info(f"StyleTTS2 event_id: {event_id}")
                else:
                    error_text = await response.text()
                    raise AudioProcessingError(
                        f"StyleTTS2 synthesis failed: {error_text}",
                        provider=self.config.id.value
                    )

            # Step 2: Poll for result
            result = await self._poll_gradio_result(
                base_url=self.config.endpoint.base_url,
                endpoint_path=self.config.endpoint.synthesize_path,
                event_id=event_id,
                max_polls=120,  # 60 seconds max (120 * 0.5s)
                poll_interval=0.5
            )

            # Step 3: Extract audio from result
            if "data" in result and len(result["data"]) > 0:
                audio_info = result["data"][0]

                # Check if it's a URL
                if isinstance(audio_info, str) and audio_info.startswith("http"):
                    async with self.session.get(audio_info) as audio_response:
                        if audio_response.status == 200:
                            audio_data = await audio_response.read()
                        else:
                            raise AudioProcessingError(
                                f"Failed to download audio from {audio_info}",
                                provider=self.config.id.value
                            )
                elif isinstance(audio_info, dict) and "name" in audio_info:
                    # It's a file reference, download it
                    file_url = f"{self.config.endpoint.base_url}/file={audio_info['name']}"
                    async with self.session.get(file_url) as audio_response:
                        if audio_response.status == 200:
                            audio_data = await audio_response.read()
                        else:
                            raise AudioProcessingError(
                                f"Failed to download audio file: {audio_info['name']}",
                                provider=self.config.id.value
                            )
                else:
                    raise AudioProcessingError(
                        f"Unexpected audio format from StyleTTS2: {type(audio_info)}",
                        provider=self.config.id.value
                    )

                return TTSResponse(
                    audio=audio_data,
                    format=AudioFormat.WAV,
                    sample_rate=24000,  # StyleTTS2 default
                    provider=self.config.id,
                    language=request.language,
                    metadata={
                        "emotion": request.emotion,
                        "style_transfer": True
                    }
                )
            else:
                raise AudioProcessingError(
                    "No audio data in StyleTTS2 response",
                    provider=self.config.id.value
                )

        except AudioProcessingError:
            raise
        except asyncio.TimeoutError:
            raise TimeoutError(self.config.id.value, self.config.endpoint.timeout)
        except aiohttp.ClientError as e:
            raise ConnectionError(self.config.id.value, url, str(e))
        except Exception as e:
            logger.error(f"StyleTTS2 synthesis error: {e}")
            raise AudioProcessingError(
                f"StyleTTS2 synthesis error: {str(e)}",
                provider=self.config.id.value
            ) from e

    async def synthesize_with_clone(self, request: VoiceCloneRequest) -> TTSResponse:
        """Synthesize speech with voice cloning using Gradio API.

        Args:
            request: Voice clone request with reference audio

        Returns:
            TTS response with cloned audio
        """
        try:
            from gradio_client import Client, handle_file
            import tempfile
            import os

            # Save reference audio to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
                f.write(request.reference_audio)
                temp_path = f.name

            try:
                # Connect to Gradio app
                client = Client(f"{self.config.endpoint.base_url}/styletts2")

                # Discover API endpoints
                api_info = client.view_api(return_format="dict")
                endpoints = list(api_info.get('named_endpoints', {}).keys())

                # Find appropriate endpoint
                endpoint = None
                for pattern in ['/synthesize', '/tts', '/generate', '/predict']:
                    if pattern in endpoints:
                        endpoint = pattern
                        break

                if not endpoint and endpoints:
                    endpoint = endpoints[0]

                if not endpoint:
                    raise AudioProcessingError(
                        "No API endpoints found for StyleTTS2",
                        provider=TTSProvider.STYLETTS2
                    )

                # Call Gradio API
                result = client.predict(
                    handle_file(temp_path),
                    request.text,
                    api_name=endpoint
                )

                # Read generated audio
                if result and result[0]:
                    with open(result[0], 'rb') as f:
                        audio_data = f.read()

                    return TTSResponse(
                        audio=audio_data,
                        format=request.output_format,
                        sample_rate=request.sample_rate,
                        provider=TTSProvider.STYLETTS2,
                        language=request.language,
                        metadata={"cloned": True, "method": "gradio_api", "endpoint": endpoint}
                    )
                else:
                    raise AudioProcessingError(
                        "No audio returned from StyleTTS2",
                        provider=TTSProvider.STYLETTS2
                    )

            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            logger.error(f"StyleTTS2 voice cloning error: {e}")
            raise AudioProcessingError(
                f"StyleTTS2 voice cloning failed: {str(e)}",
                provider=TTSProvider.STYLETTS2
            ) from e


class MoshiProvider(BaseTTSProvider):
    """Moshi provider implementation with WebSocket support."""

    def _get_default_config(self) -> TTSProviderConfig:
        """Get default Moshi configuration."""
        return get_provider_config(TTSProvider.MOSHI)

    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        """Synthesize speech using Moshi (single turn)."""
        if not self._is_available:
            raise ProviderNotAvailableError(self.config.id.value)

        url = f"{self.config.endpoint.base_url}{self.config.endpoint.synthesize_path}"

        payload = {
            "text": request.text,
            "language": request.language,
        }

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return TTSResponse(
                        audio=None,  # Moshi primarily uses WebSocket
                        format=AudioFormat.PCM,
                        sample_rate=24000,
                        provider=self.config.id,
                        language=request.language,
                        metadata=data
                    )
                else:
                    error_text = await response.text()
                    raise AudioProcessingError(
                        f"Synthesis failed: {error_text}",
                        provider=self.config.id.value
                    )

        except asyncio.TimeoutError:
            raise TimeoutError(self.config.id.value, self.config.endpoint.timeout)
        except aiohttp.ClientError as e:
            raise ConnectionError(self.config.id.value, url, str(e))

    async def start_conversation(
        self,
        request: ConversationRequest
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Start real-time conversation via WebSocket.

        Args:
            request: Conversation request

        Yields:
            WebSocket messages
        """
        if not self.config.endpoint.websocket_path:
            raise NotImplementedError("WebSocket endpoint not configured")

        ws_url = self.config.endpoint.base_url.replace("https", "wss")
        ws_url = f"{ws_url}{self.config.endpoint.websocket_path}"

        try:
            async with self.session.ws_connect(ws_url) as ws:
                # Send initial message if text provided
                if request.text:
                    await ws.send_json({
                        "type": "text",
                        "data": request.text,
                        "session_id": request.session_id
                    })

                # Handle messages
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        yield data
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        logger.error(f"WebSocket error: {ws.exception()}")
                        break
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        break

        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise ConnectionError(self.config.id.value, ws_url, str(e))


# Export provider classes
__all__ = [
    'BaseTTSProvider',
    'F5TTSProvider',
    'StyleTTS2Provider',
    'MoshiProvider',
]


# Additional providers can be added here
class CoquiXTTSProvider(BaseTTSProvider):
    """Coqui XTTS v2 provider implementation.

    Coqui XTTS is a multilingual TTS model with voice cloning support.
    Supports 18+ languages including English, Spanish, French, German, etc.
    """

    def _get_default_config(self) -> TTSProviderConfig:
        return get_provider_config(TTSProvider.COQUI_XTTS)

    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        """Synthesize speech using Coqui XTTS v2.

        Args:
            request: TTS request

        Returns:
            TTS response with generated audio

        Raises:
            ProviderNotAvailableError: If provider is not available
            AudioProcessingError: If synthesis fails
        """
        if not self._is_available:
            raise ProviderNotAvailableError(self.config.id.value)

        url = f"{self.config.endpoint.base_url}{self.config.endpoint.synthesize_path}"

        payload = {
            "text": request.text,
            "language": request.language or "en",
            "speed": request.speed,
            "format": request.output_format.value,
            "sample_rate": request.sample_rate,
        }

        if request.speaker:
            payload["speaker"] = request.speaker

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    content_type = response.headers.get("content-type", "")

                    if "audio" in content_type:
                        audio_data = await response.read()
                        return TTSResponse(
                            audio=audio_data,
                            format=request.output_format,
                            sample_rate=request.sample_rate,
                            provider=self.config.id,
                            language=request.language,
                            speaker=request.speaker
                        )
                    else:
                        data = await response.json()
                        return TTSResponse(
                            audio_url=data.get("audio_url"),
                            format=request.output_format,
                            sample_rate=request.sample_rate,
                            provider=self.config.id,
                            language=request.language,
                            speaker=request.speaker,
                            metadata=data
                        )
                else:
                    error_text = await response.text()
                    raise AudioProcessingError(
                        f"Coqui XTTS synthesis failed: {error_text}",
                        provider=self.config.id.value
                    )

        except asyncio.TimeoutError:
            raise TimeoutError(self.config.id.value, self.config.endpoint.timeout)
        except aiohttp.ClientError as e:
            raise ConnectionError(self.config.id.value, url, str(e))


class MeloTTSProvider(BaseTTSProvider):
    """MeloTTS provider implementation.

    MeloTTS is a fast multilingual TTS model with multi-speaker support.
    Supports multiple languages: EN, ES, FR, ZH, JP, KR.
    """

    def _get_default_config(self) -> TTSProviderConfig:
        return get_provider_config(TTSProvider.MELOTTS)

    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        """Synthesize speech using MeloTTS.

        Args:
            request: TTS request

        Returns:
            TTS response with generated audio

        Raises:
            ProviderNotAvailableError: If provider is not available
            AudioProcessingError: If synthesis fails
        """
        if not self._is_available:
            raise ProviderNotAvailableError(self.config.id.value)

        url = f"{self.config.endpoint.base_url}{self.config.endpoint.synthesize_path}"

        # MeloTTS requires uppercase language codes (EN, ES, FR, ZH, JP, KR)
        language_upper = request.language.upper() if request.language else "EN"

        payload = {
            "text": request.text,
            "language": language_upper,
            "speed": request.speed,
            "format": request.output_format.value,
            "sample_rate": request.sample_rate,
        }

        if request.speaker:
            payload["speaker"] = request.speaker

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    content_type = response.headers.get("content-type", "")

                    if "audio" in content_type:
                        audio_data = await response.read()
                        return TTSResponse(
                            audio=audio_data,
                            format=request.output_format,
                            sample_rate=request.sample_rate,
                            provider=self.config.id,
                            language=request.language,
                            speaker=request.speaker
                        )
                    else:
                        data = await response.json()
                        return TTSResponse(
                            audio_url=data.get("audio_url"),
                            format=request.output_format,
                            sample_rate=request.sample_rate,
                            provider=self.config.id,
                            language=request.language,
                            speaker=request.speaker,
                            metadata=data
                        )
                else:
                    error_text = await response.text()
                    raise AudioProcessingError(
                        f"MeloTTS synthesis failed: {error_text}",
                        provider=self.config.id.value
                    )

        except asyncio.TimeoutError:
            raise TimeoutError(self.config.id.value, self.config.endpoint.timeout)
        except aiohttp.ClientError as e:
            raise ConnectionError(self.config.id.value, url, str(e))


class KokoroTTSProvider(BaseTTSProvider):
    """Kokoro TTS provider implementation.

    Kokoro-82M is a fast, high-quality TTS model with natural prosody.
    Supports 11 voice packs (American and British English).

    Example:
        ```python
        async with KokoroTTSProvider() as provider:
            # Synthesize with default voice (Heart - female American)
            response = await provider.synthesize(
                TTSRequest(
                    text="Hello, this is Kokoro TTS!",
                    speaker="af_heart",
                    speed=1.0,
                    pitch=1.0
                )
            )

            # Use British male voice
            response = await provider.synthesize(
                TTSRequest(
                    text="Good day from London!",
                    speaker="bm_george"
                )
            )
        ```
    """

    def _get_default_config(self) -> TTSProviderConfig:
        """Get default configuration for Kokoro TTS."""
        return get_provider_config(TTSProvider.KOKORO)

    async def synthesize(
        self,
        request: TTSRequest
    ) -> TTSResponse:
        """Synthesize speech using Kokoro TTS.

        Args:
            request: TTS synthesis request

        Returns:
            TTS response with audio data

        Raises:
            ProviderNotAvailableError: If provider is not available
            AudioProcessingError: If synthesis fails
        """
        if not self._is_available:
            await self.check_health()

        try:
            url = f"{self.config.endpoint.base_url}{self.config.endpoint.synthesize_path}"

            # Map speaker parameter (default to Heart if not specified)
            speaker = request.speaker or "af_heart"

            payload = {
                "text": request.text,
                "voice": speaker,
                "speed": request.speed,
                "pitch": request.pitch
            }

            logger.info(f"Synthesizing with Kokoro: '{request.text[:50]}...', voice={speaker}")

            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    audio_data = await response.read()

                    return TTSResponse(
                        audio=audio_data,
                        format=AudioFormat.WAV,
                        sample_rate=24000,  # Kokoro default
                        provider=TTSProvider.KOKORO,
                        language=request.language,
                        speaker=speaker,
                        metadata={"voice_pack": speaker}
                    )
                else:
                    error_msg = await response.text()
                    logger.error(f"Kokoro synthesis failed: {response.status} - {error_msg}")
                    raise AudioProcessingError(
                        f"Kokoro synthesis failed: {error_msg}",
                        provider=TTSProvider.KOKORO
                    )

        except AudioProcessingError:
            raise
        except Exception as e:
            logger.error(f"Kokoro synthesis error: {e}")
            raise AudioProcessingError(
                f"Kokoro synthesis error: {str(e)}",
                provider=TTSProvider.KOKORO
            ) from e


class TTSWebUIProvider(BaseTTSProvider):
    """TTS-WebUI comprehensive platform provider implementation.

    TTS-WebUI provides access to 20+ TTS models through a unified OpenAI-compatible API.
    Supports multiple models including StyleTTS2, F5-TTS, XTTS, RVC, and many more.

    Example:
        ```python
        async with TTSWebUIProvider() as provider:
            # Synthesize with StyleTTS2 model
            response = await provider.synthesize(
                TTSRequest(
                    text="Hello from TTS-WebUI!",
                    model="styletts2",
                    voice="default",
                    language="en"
                )
            )

            # Use F5-TTS with voice cloning
            response = await provider.synthesize(
                TTSRequest(
                    text="Advanced synthesis with F5-TTS",
                    model="f5-tts",
                    language="en"
                )
            )

            # Generate music with MusicGen
            response = await provider.synthesize(
                TTSRequest(
                    text="upbeat electronic dance music",
                    model="musicgen"
                )
            )
        ```

    Available Models:
        - Core: styletts2, rvc, bark, tortoise, melotts, mms
        - Advanced: f5-tts, xtts_v2, openvoice, kokoro, parler-tts
        - Specialty: whisper, musicgen, stable-audio, demucs
        - Experimental: gpt-sovits, chatterbox, mahaTTS, vall-e-x
    """

    def _get_default_config(self) -> TTSProviderConfig:
        """Get default configuration for TTS-WebUI."""
        return get_provider_config(TTSProvider.TTS_WEBUI)

    async def synthesize(
        self,
        request: TTSRequest
    ) -> TTSResponse:
        """Synthesize speech using TTS-WebUI platform.

        Args:
            request: TTS synthesis request with model selection

        Returns:
            TTS response with audio data

        Raises:
            ProviderNotAvailableError: If provider is not available
            AudioProcessingError: If synthesis fails
            ValueError: If model is not specified or not supported
        """
        if not self._is_available:
            await self.check_health()

        # Validate model is specified
        if not request.model:
            raise ValueError(
                "Model must be specified for TTS-WebUI. "
                f"Available models: {', '.join(self.config.capabilities.available_models[:5])}... "
                "See config.capabilities.available_models for full list."
            )

        try:
            url = f"{self.config.endpoint.base_url}{self.config.endpoint.synthesize_path}"

            # Build OpenAI-compatible payload
            voice = request.voice or request.speaker or "default"

            payload = {
                "model": request.model,
                "input": request.text,
                "voice": voice,
                "response_format": request.output_format.value,
                "speed": request.speed
            }

            # Add optional parameters
            if request.language:
                payload["language"] = request.language

            logger.info(
                f"Synthesizing with TTS-WebUI: '{request.text[:50]}...', "
                f"model={request.model}, voice={voice}"
            )

            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    audio_data = await response.read()

                    return TTSResponse(
                        audio=audio_data,
                        format=request.output_format,
                        sample_rate=request.sample_rate,
                        provider=TTSProvider.TTS_WEBUI,
                        model_version=request.model,
                        language=request.language,
                        speaker=voice,
                        metadata={
                            "model": request.model,
                            "platform": "tts-webui",
                            "voice": voice
                        }
                    )
                else:
                    error_msg = await response.text()
                    logger.error(f"TTS-WebUI synthesis failed: {response.status} - {error_msg}")
                    raise AudioProcessingError(
                        f"TTS-WebUI synthesis failed: {error_msg}",
                        provider=TTSProvider.TTS_WEBUI
                    )

        except AudioProcessingError:
            raise
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"TTS-WebUI synthesis error: {e}")
            raise AudioProcessingError(
                f"TTS-WebUI synthesis error: {str(e)}",
                provider=TTSProvider.TTS_WEBUI
            ) from e

    async def stream_synthesize(
        self,
        request: TTSRequest
    ) -> AsyncGenerator[bytes, None]:
        """Stream synthesized speech sentence-by-sentence using TTS-WebUI.

        Args:
            request: TTS synthesis request with model selection

        Yields:
            Audio chunks as bytes (WAV format)

        Raises:
            ProviderNotAvailableError: If provider is not available
            ValueError: If model is not specified
        """
        if not self._is_available:
            await self.check_health()

        # Validate model is specified
        if not request.model:
            raise ValueError(
                "Model must be specified for TTS-WebUI. "
                f"Available models: {', '.join(self.config.capabilities.available_models[:5])}... "
            )

        url = f"{self.config.endpoint.base_url}/synthesize/stream"

        voice = request.voice or request.speaker or "default"

        payload = {
            "model": request.model,
            "text": request.text,
            "voice": voice,
            "language": request.language,
            "speed": request.speed,
            "output_format": request.output_format.value
        }

        try:
            logger.info(
                f"[TTS-WEBUI STREAM] Streaming with model={request.model}, "
                f"text_length={len(request.text)}"
            )

            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    # Fallback to blocking synthesis
                    logger.warning(
                        f"[TTS-WEBUI STREAM] Endpoint returned {response.status}, "
                        "falling back to blocking mode"
                    )
                    blocking_response = await self.synthesize(request)
                    yield blocking_response.audio
                    return

                # Stream audio chunks
                chunk_count = 0
                async for chunk in response.content.iter_chunked(8192):
                    if chunk:
                        chunk_count += 1
                        logger.debug(f"[TTS-WEBUI STREAM] Yielding chunk {chunk_count}: {len(chunk)} bytes")
                        yield chunk

                logger.info(f"[TTS-WEBUI STREAM] Completed: {chunk_count} chunks sent")

        except Exception as e:
            logger.error(f"[TTS-WEBUI STREAM] Error: {e}, falling back to blocking mode")
            # Fallback to blocking synthesis on error
            blocking_response = await self.synthesize(request)
            yield blocking_response.audio


class FishSpeechProvider(BaseTTSProvider):
    """Fish Speech provider implementation.

    Fish Speech is a zero-shot voice cloning TTS model with fast inference
    and natural speech generation. Community #2 favorite.

    Features:
    - Zero-shot and few-shot voice cloning
    - Multilingual support (8 languages)
    - Fast inference (5-6x real-time)
    - Natural prosody and expressiveness

    Example usage:
        provider = FishSpeechProvider()
        async with provider:
            # Standard synthesis
            request = TTSRequest(
                text="Natural speech with Fish Speech",
                language="en"
            )
            response = await provider.synthesize(request)

            # Voice cloning
            with open("reference.wav", "rb") as f:
                ref_audio = f.read()

            clone_request = VoiceCloneRequest(
                text="Clone this voice naturally",
                reference_audio=ref_audio,
                language="en"
            )
            response = await provider.clone_voice(clone_request)
    """

    def _get_default_config(self) -> TTSProviderConfig:
        return get_provider_config(TTSProvider.FISH_SPEECH)

    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        """Synthesize speech using Fish Speech.

        Args:
            request: TTS synthesis request

        Returns:
            TTS response with generated audio
        """
        if not self._is_available:
            await self.check_health()

        url = f"{self.config.endpoint.base_url}{self.config.endpoint.synthesize_path}"

        payload = {
            "text": request.text,
            "language": request.language,
            "speed": request.speed
        }

        if request.speaker:
            payload["speaker"] = request.speaker

        logger.info(
            f"Fish Speech synthesis: text_length={len(request.text)}, "
            f"language={request.language}, speed={request.speed}"
        )

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    audio_data = await response.read()

                    return TTSResponse(
                        audio=audio_data,
                        format=AudioFormat.WAV,
                        sample_rate=24000,
                        provider=TTSProvider.FISH_SPEECH,
                        language=request.language,
                        speaker=request.speaker,
                        metadata={
                            "zero_shot": True,
                            "inference_type": "fast"
                        }
                    )
                else:
                    error_msg = await response.text()
                    logger.error(f"Fish Speech synthesis failed: {response.status} - {error_msg}")
                    raise AudioProcessingError(
                        f"Fish Speech synthesis failed: {error_msg}",
                        provider=TTSProvider.FISH_SPEECH
                    )

        except AudioProcessingError:
            raise
        except Exception as e:
            logger.error(f"Fish Speech synthesis error: {e}")
            raise AudioProcessingError(
                f"Fish Speech synthesis error: {str(e)}",
                provider=TTSProvider.FISH_SPEECH
            ) from e

    async def clone_voice(self, request: VoiceCloneRequest) -> TTSResponse:
        """Clone voice using Fish Speech zero-shot capability.

        Args:
            request: Voice cloning request with reference audio

        Returns:
            TTS response with cloned voice audio
        """
        if not self._is_available:
            await self.check_health()

        url = f"{self.config.endpoint.base_url}{self.config.endpoint.voice_clone_path}"

        # Encode reference audio as base64
        import base64
        ref_audio_b64 = base64.b64encode(request.reference_audio).decode()

        payload = {
            "text": request.text,
            "reference_audio": ref_audio_b64,
            "language": request.language,
            "speed": request.speed,
            "enhance": request.enhance
        }

        logger.info(
            f"Fish Speech voice cloning: text_length={len(request.text)}, "
            f"ref_audio_size={len(request.reference_audio)}"
        )

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    audio_data = await response.read()

                    return TTSResponse(
                        audio=audio_data,
                        format=request.output_format,
                        sample_rate=request.sample_rate,
                        provider=TTSProvider.FISH_SPEECH,
                        language=request.language,
                        metadata={
                            "cloned": True,
                            "zero_shot": True,
                            "enhanced": request.enhance
                        }
                    )
                else:
                    error_msg = await response.text()
                    logger.error(f"Fish Speech cloning failed: {response.status} - {error_msg}")
                    raise AudioProcessingError(
                        f"Fish Speech cloning failed: {error_msg}",
                        provider=TTSProvider.FISH_SPEECH
                    )

        except AudioProcessingError:
            raise
        except Exception as e:
            logger.error(f"Fish Speech cloning error: {e}")
            raise AudioProcessingError(
                f"Fish Speech cloning error: {str(e)}",
                provider=TTSProvider.FISH_SPEECH
            ) from e

    async def stream_synthesize(
        self,
        request: TTSRequest
    ) -> AsyncGenerator[bytes, None]:
        """Stream synthesized speech sentence-by-sentence.

        Args:
            request: TTS synthesis request

        Yields:
            Audio chunks as WAV bytes (sentence-level streaming)
        """
        url = f"{self.config.endpoint.base_url}/synthesize/stream"

        payload = {
            "text": request.text,
            "language": request.language,
            "speed": request.speed
        }

        if request.speaker:
            payload["speaker"] = request.speaker

        logger.info(
            f"Fish Speech streaming: text_length={len(request.text)}, "
            f"language={request.language}"
        )

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Fish Speech streaming failed: {response.status} - {error_text}")
                    # Fallback to blocking mode
                    logger.warning("Falling back to blocking synthesis")
                    blocking_response = await self.synthesize(request)
                    yield blocking_response.audio
                    return

                # Stream chunks
                chunk_count = 0
                async for chunk in response.content.iter_chunked(8192):
                    if chunk:
                        chunk_count += 1
                        logger.debug(f"Fish Speech chunk {chunk_count}: {len(chunk)} bytes")
                        yield chunk

                logger.info(f"Fish Speech streaming complete: {chunk_count} chunks")

        except Exception as e:
            logger.error(f"Fish Speech streaming error: {e}")
            # Fallback to blocking mode on error
            logger.warning("Falling back to blocking synthesis due to error")
            blocking_response = await self.synthesize(request)
            yield blocking_response.audio


class ZonosTTSProvider(BaseTTSProvider):
    """Zonos TTS provider implementation.

    Zonos is an experimental TTS model with emotion control sliders
    for highly customizable prosody and expressiveness.

    Features:
    - Emotion control sliders
    - Prosody customization
    - Expressiveness control
    - English language support

    Example usage:
        provider = ZonosTTSProvider()
        async with provider:
            request = TTSRequest(
                text="Expressive speech with emotion control",
                language="en",
                emotion="happy",  # Custom emotion parameter
                speed=1.1,
                pitch=1.05
            )
            response = await provider.synthesize(request)
    """

    def _get_default_config(self) -> TTSProviderConfig:
        return get_provider_config(TTSProvider.ZONOS)

    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        """Synthesize speech using Zonos TTS with emotion control.

        Args:
            request: TTS synthesis request (supports emotion parameter)

        Returns:
            TTS response with generated audio
        """
        if not self._is_available:
            await self.check_health()

        url = f"{self.config.endpoint.base_url}{self.config.endpoint.synthesize_path}"

        payload = {
            "text": request.text,
            "speed": request.speed,
            "pitch": request.pitch
        }

        # Add emotion control if specified
        if request.emotion:
            payload["emotion"] = request.emotion

        logger.info(
            f"Zonos TTS synthesis: text_length={len(request.text)}, "
            f"speed={request.speed}, pitch={request.pitch}, emotion={request.emotion}"
        )

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    audio_data = await response.read()

                    return TTSResponse(
                        audio=audio_data,
                        format=AudioFormat.WAV,
                        sample_rate=22050,
                        provider=TTSProvider.ZONOS,
                        language=request.language,
                        metadata={
                            "emotion": request.emotion,
                            "experimental": True,
                            "prosody_control": True
                        }
                    )
                else:
                    error_msg = await response.text()
                    logger.error(f"Zonos TTS synthesis failed: {response.status} - {error_msg}")
                    raise AudioProcessingError(
                        f"Zonos TTS synthesis failed: {error_msg}",
                        provider=TTSProvider.ZONOS
                    )

        except AudioProcessingError:
            raise
        except Exception as e:
            logger.error(f"Zonos TTS synthesis error: {e}")
            raise AudioProcessingError(
                f"Zonos TTS synthesis error: {str(e)}",
                provider=TTSProvider.ZONOS
            ) from e

    async def stream_synthesize(
        self,
        request: TTSRequest
    ) -> AsyncGenerator[bytes, None]:
        """Stream synthesized speech sentence-by-sentence.

        Args:
            request: TTS synthesis request

        Yields:
            Audio chunks as WAV bytes (sentence-level streaming)
        """
        url = f"{self.config.endpoint.base_url}/synthesize/stream"

        payload = {
            "text": request.text,
            "speed": request.speed,
            "pitch": request.pitch
        }

        if request.emotion:
            payload["emotion"] = request.emotion

        logger.info(
            f"Zonos TTS streaming: text_length={len(request.text)}, "
            f"emotion={request.emotion}"
        )

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Zonos streaming failed: {response.status} - {error_text}")
                    # Fallback to blocking mode
                    logger.warning("Falling back to blocking synthesis")
                    blocking_response = await self.synthesize(request)
                    yield blocking_response.audio
                    return

                # Stream chunks
                chunk_count = 0
                async for chunk in response.content.iter_chunked(8192):
                    if chunk:
                        chunk_count += 1
                        logger.debug(f"Zonos chunk {chunk_count}: {len(chunk)} bytes")
                        yield chunk

                logger.info(f"Zonos streaming complete: {chunk_count} chunks")

        except Exception as e:
            logger.error(f"Zonos streaming error: {e}")
            # Fallback to blocking mode on error
            logger.warning("Falling back to blocking synthesis due to error")
            blocking_response = await self.synthesize(request)
            yield blocking_response.audio


class OpenVoiceProvider(BaseTTSProvider):
    """OpenVoice provider implementation with Gradio API support."""

    def _get_default_config(self) -> TTSProviderConfig:
        return get_provider_config(TTSProvider.OPENVOICE)

    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        """Synthesize speech using OpenVoice."""
        if not self._is_available:
            raise ProviderNotAvailableError(self.config.id.value)

        url = f"{self.config.endpoint.base_url}{self.config.endpoint.synthesize_path}"

        # OpenVoice requires full language names: "English" or "Chinese"
        language_map = {
            "en": "English",
            "EN": "English",
            "zh": "Chinese",
            "ZH": "Chinese",
            "zh-cn": "Chinese",
            "chinese": "Chinese",
            "english": "English"
        }
        language_name = language_map.get(request.language.lower() if request.language else "en", "English")

        payload = {
            "text": request.text,
            "language": language_name,
            "speed": request.speed,
            "format": request.output_format.value,
        }

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    return TTSResponse(
                        audio=audio_data,
                        format=request.output_format,
                        sample_rate=request.sample_rate,
                        provider=self.config.id,
                        language=request.language
                    )
                else:
                    error_text = await response.text()
                    raise AudioProcessingError(
                        f"Synthesis failed: {error_text}",
                        provider=self.config.id.value
                    )

        except asyncio.TimeoutError:
            raise TimeoutError(self.config.id.value, self.config.endpoint.timeout)
        except aiohttp.ClientError as e:
            raise ConnectionError(self.config.id.value, url, str(e))

    async def synthesize_with_clone(self, request: VoiceCloneRequest) -> TTSResponse:
        """Synthesize speech with voice cloning using Gradio API.

        Args:
            request: Voice clone request with reference audio

        Returns:
            TTS response with cloned audio
        """
        try:
            from gradio_client import Client, handle_file
            import tempfile
            import os

            # Save reference audio to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
                f.write(request.reference_audio)
                temp_path = f.name

            try:
                # Connect to Gradio app
                client = Client(f"{self.config.endpoint.base_url}/openvoice")

                # Discover API endpoints
                api_info = client.view_api(return_format="dict")
                endpoints = list(api_info.get('named_endpoints', {}).keys())

                # Find appropriate endpoint
                endpoint = None
                for pattern in ['/predict', '/tts', '/synthesize', '/clone']:
                    if pattern in endpoints:
                        endpoint = pattern
                        break

                if not endpoint and endpoints:
                    endpoint = endpoints[0]

                if not endpoint:
                    raise AudioProcessingError(
                        "No API endpoints found for OpenVoice",
                        provider=TTSProvider.OPENVOICE
                    )

                # Call Gradio API
                result = client.predict(
                    handle_file(temp_path),
                    request.text,
                    api_name=endpoint
                )

                # Read generated audio
                if result and result[0]:
                    with open(result[0], 'rb') as f:
                        audio_data = f.read()

                    return TTSResponse(
                        audio=audio_data,
                        format=request.output_format,
                        sample_rate=request.sample_rate,
                        provider=TTSProvider.OPENVOICE,
                        language=request.language,
                        metadata={"cloned": True, "method": "gradio_api", "endpoint": endpoint}
                    )
                else:
                    raise AudioProcessingError(
                        "No audio returned from OpenVoice",
                        provider=TTSProvider.OPENVOICE
                    )

            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            logger.error(f"OpenVoice voice cloning error: {e}")
            raise AudioProcessingError(
                f"OpenVoice voice cloning failed: {str(e)}",
                provider=TTSProvider.OPENVOICE
            ) from e


class IndexTTSProvider(BaseTTSProvider):
    """IndexTTS 2.0 provider implementation."""

    def _get_default_config(self) -> TTSProviderConfig:
        return get_provider_config(TTSProvider.INDEXTTS)

    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        """Synthesize speech using IndexTTS 2.0.

        Args:
            request: TTS request

        Returns:
            TTS response with audio

        Raises:
            ProviderNotAvailableError: If provider is offline
            AudioProcessingError: If synthesis fails
        """
        if not self._is_available:
            raise ProviderNotAvailableError(
                f"IndexTTS 2.0 provider is not available at {self.config.endpoint.base_url}"
            )

        try:
            url = f"{self.config.endpoint.base_url}{self.config.endpoint.synthesize_path}"

            # Use OpenAI-compatible API format for TTS-WebUI
            voice = request.speaker or "default"
            payload = {
                "model": "indextts",  # IndexTTS model in TTS-WebUI
                "input": request.text,  # OpenAI uses "input" not "text"
                "voice": voice,
                "response_format": request.output_format.value,
                "speed": request.speed or 1.0
            }

            # Add language if provided
            if request.language:
                payload["language"] = request.language

            # Add emotion control (IndexTTS feature)
            if request.emotion:
                payload["emotion"] = request.emotion

            logger.info(
                f"IndexTTS synthesis via TTS-WebUI: text_length={len(request.text)}, "
                f"voice={voice}, emotion={request.emotion}"
            )

            # Send synthesis request
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    audio_data = await response.read()

                    return TTSResponse(
                        audio=audio_data,
                        format=request.output_format,
                        sample_rate=request.sample_rate,
                        provider=TTSProvider.INDEXTTS,
                        language=request.language,
                        speaker=voice,
                        metadata={
                            "model": "indextts",
                            "platform": "tts-webui",
                            "emotion": request.emotion
                        }
                    )
                else:
                    error_msg = await response.text()
                    logger.error(f"IndexTTS synthesis failed: {response.status} - {error_msg}")
                    raise AudioProcessingError(
                        f"IndexTTS synthesis failed: {error_msg}",
                        provider=TTSProvider.INDEXTTS
                    )

        except aiohttp.ClientError as e:
            logger.error(f"IndexTTS synthesis error: {e}")
            raise AudioProcessingError(
                f"IndexTTS synthesis error: {str(e)}",
                provider=TTSProvider.INDEXTTS
            ) from e

    async def synthesize_with_voice_cloning(
        self, request: VoiceCloneRequest
    ) -> TTSResponse:
        """Synthesize speech with voice cloning.

        Args:
            request: Voice cloning request

        Returns:
            TTS response with cloned voice

        Raises:
            ProviderNotAvailableError: If provider is offline
            AudioProcessingError: If cloning fails
        """
        if not self._is_available:
            raise ProviderNotAvailableError(
                f"IndexTTS 2.0 provider is not available at {self.config.endpoint.base_url}"
            )

        try:
            url = f"{self.config.endpoint.base_url}{self.config.endpoint.voice_clone_path}"

            # Prepare multipart form data
            form_data = aiohttp.FormData()
            form_data.add_field("text", request.text)
            form_data.add_field("language", request.language)
            form_data.add_field("speed", str(request.speed))
            form_data.add_field("model", "indextts")
            form_data.add_field(
                "reference_audio",
                request.reference_audio,
                filename="reference.wav",
                content_type=f"audio/{request.reference_format.value}"
            )

            async with self.session.post(url, data=form_data) as response:
                if response.status == 200:
                    audio_data = await response.read()

                    return TTSResponse(
                        audio=audio_data,
                        format=request.output_format,
                        sample_rate=request.sample_rate,
                        provider=TTSProvider.INDEXTTS,
                        language=request.language,
                        metadata={
                            "provider": "IndexTTS 2.0",
                            "platform": "TTS-WebUI",
                            "voice_cloning": True
                        }
                    )
                else:
                    error_msg = await response.text()
                    raise AudioProcessingError(
                        f"IndexTTS voice cloning failed: {error_msg}",
                        provider=TTSProvider.INDEXTTS
                    )

        except aiohttp.ClientError as e:
            logger.error(f"IndexTTS voice cloning error: {e}")
            raise AudioProcessingError(
                f"IndexTTS voice cloning error: {str(e)}",
                provider=TTSProvider.INDEXTTS
            ) from e


class VoxCPMProvider(BaseTTSProvider):
    """VoxCPM provider implementation."""

    def _get_default_config(self) -> TTSProviderConfig:
        return get_provider_config(TTSProvider.VOXCPM)

    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        """Synthesize speech using VoxCPM.

        Args:
            request: TTS request

        Returns:
            TTS response with audio

        Raises:
            ProviderNotAvailableError: If provider is offline
            AudioProcessingError: If synthesis fails
        """
        if not self._is_available:
            raise ProviderNotAvailableError(
                f"VoxCPM provider is not available at {self.config.endpoint.base_url}"
            )

        try:
            url = f"{self.config.endpoint.base_url}{self.config.endpoint.synthesize_path}"

            # Use OpenAI-compatible API format for TTS-WebUI
            voice = request.speaker or "default"
            payload = {
                "model": "voxcpm",  # VoxCPM model in TTS-WebUI
                "input": request.text,  # OpenAI uses "input" not "text"
                "voice": voice,
                "response_format": request.output_format.value,
                "speed": request.speed or 1.0
            }

            # Add language if provided
            if request.language:
                payload["language"] = request.language

            logger.info(
                f"VoxCPM synthesis via TTS-WebUI: text_length={len(request.text)}, "
                f"voice={voice}, language={request.language}"
            )

            # Send synthesis request
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    audio_data = await response.read()

                    return TTSResponse(
                        audio=audio_data,
                        format=request.output_format,
                        sample_rate=request.sample_rate,
                        provider=TTSProvider.VOXCPM,
                        language=request.language,
                        speaker=voice,
                        metadata={"provider": "VoxCPM", "platform": "TTS-WebUI", "model_family": "CPM"}
                    )
                else:
                    error_msg = await response.text()
                    raise AudioProcessingError(
                        f"VoxCPM synthesis failed: {error_msg}",
                        provider=TTSProvider.VOXCPM
                    )

        except aiohttp.ClientError as e:
            logger.error(f"VoxCPM synthesis error: {e}")
            raise AudioProcessingError(
                f"VoxCPM synthesis error: {str(e)}",
                provider=TTSProvider.VOXCPM
            ) from e

    async def synthesize_with_voice_cloning(
        self, request: VoiceCloneRequest
    ) -> TTSResponse:
        """Synthesize speech with voice cloning.

        Args:
            request: Voice cloning request

        Returns:
            TTS response with cloned voice

        Raises:
            ProviderNotAvailableError: If provider is offline
            AudioProcessingError: If cloning fails
        """
        if not self._is_available:
            raise ProviderNotAvailableError(
                f"VoxCPM provider is not available at {self.config.endpoint.base_url}"
            )

        try:
            url = f"{self.config.endpoint.base_url}{self.config.endpoint.voice_clone_path}"

            # Prepare multipart form data
            form_data = aiohttp.FormData()
            form_data.add_field("text", request.text)
            form_data.add_field("language", request.language)
            form_data.add_field("speed", str(request.speed))
            form_data.add_field("model", "voxcpm")
            form_data.add_field(
                "reference_audio",
                request.reference_audio,
                filename="reference.wav",
                content_type=f"audio/{request.reference_format.value}"
            )

            async with self.session.post(url, data=form_data) as response:
                if response.status == 200:
                    audio_data = await response.read()

                    return TTSResponse(
                        audio=audio_data,
                        format=request.output_format,
                        sample_rate=request.sample_rate,
                        provider=TTSProvider.VOXCPM,
                        language=request.language,
                        metadata={
                            "provider": "VoxCPM",
                            "platform": "TTS-WebUI",
                            "model_family": "CPM",
                            "voice_cloning": True
                        }
                    )
                else:
                    error_msg = await response.text()
                    raise AudioProcessingError(
                        f"VoxCPM voice cloning failed: {error_msg}",
                        provider=TTSProvider.VOXCPM
                    )

        except aiohttp.ClientError as e:
            logger.error(f"VoxCPM voice cloning error: {e}")
            raise AudioProcessingError(
                f"VoxCPM voice cloning error: {str(e)}",
                provider=TTSProvider.VOXCPM
            ) from e


class GPTSoVITSProvider(BaseTTSProvider):
    """GPT-SoVITS provider implementation with Gradio API support.

    GPT-SoVITS is a powerful zero-shot voice cloning model.
    """

    def _get_default_config(self) -> TTSProviderConfig:
        return get_provider_config(TTSProvider.GPT_SOVITS)

    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        """Synthesize speech using GPT-SoVITS via TTS Provider Hub.

        GPT-SoVITS is available on the TTS Provider Hub (port 8010).
        """
        if not self._is_available:
            raise ProviderNotAvailableError(self.config.id.value)

        url = f"{self.config.endpoint.base_url}{self.config.endpoint.synthesize_path}"

        # GPT-SoVITS endpoint format (may vary from OpenAI format)
        voice = request.speaker or "default"
        payload = {
            "text": request.text,
            "language": request.language or "en",
            "speed": request.speed or 1.0,
            "voice": voice
        }

        logger.info(
            f"GPT-SoVITS synthesis: text_length={len(request.text)}, "
            f"language={request.language}, voice={voice}"
        )

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    return TTSResponse(
                        audio=audio_data,
                        format=request.output_format,
                        sample_rate=request.sample_rate,
                        provider=self.config.id,
                        language=request.language,
                        speaker=voice,
                        metadata={
                            "platform": "tts-provider-hub",
                            "zero_shot_cloning": True
                        }
                    )
                else:
                    error_text = await response.text()
                    logger.error(f"GPT-SoVITS synthesis failed: {response.status} - {error_text}")
                    raise AudioProcessingError(
                        f"Synthesis failed: {error_text}",
                        provider=self.config.id.value
                    )

        except asyncio.TimeoutError:
            raise TimeoutError(self.config.id.value, self.config.endpoint.timeout)
        except aiohttp.ClientError as e:
            raise ConnectionError(self.config.id.value, url, str(e))

    async def synthesize_with_clone(self, request: VoiceCloneRequest) -> TTSResponse:
        """Synthesize speech with voice cloning using Gradio API.

        Args:
            request: Voice clone request with reference audio

        Returns:
            TTS response with cloned audio
        """
        try:
            from gradio_client import Client, handle_file
            import tempfile
            import os

            # Save reference audio to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
                f.write(request.reference_audio)
                temp_path = f.name

            try:
                # Connect to Gradio app
                client = Client("https://jzfmzviw26huka-8010.proxy.runpod.net/gptsovits")

                # Discover API endpoints
                api_info = client.view_api(return_format="dict")
                endpoints = list(api_info.get('named_endpoints', {}).keys())

                # Find appropriate endpoint
                endpoint = None
                for pattern in ['/tts', '/predict', '/synthesize', '/infer', '/clone']:
                    if pattern in endpoints:
                        endpoint = pattern
                        break

                if not endpoint and endpoints:
                    endpoint = endpoints[0]

                if not endpoint:
                    raise AudioProcessingError(
                        "No API endpoints found for GPT-SoVITS",
                        provider=TTSProvider.GPT_SOVITS
                    )

                logger.info(f"Using GPT-SoVITS endpoint: {endpoint}")

                # Call Gradio API
                result = client.predict(
                    handle_file(temp_path),
                    request.text,
                    api_name=endpoint
                )

                # Read generated audio
                if result and result[0]:
                    with open(result[0], 'rb') as f:
                        audio_data = f.read()

                    return TTSResponse(
                        audio=audio_data,
                        format=request.output_format,
                        sample_rate=request.sample_rate,
                        provider=TTSProvider.GPT_SOVITS,
                        language=request.language,
                        metadata={"cloned": True, "method": "gradio_api", "endpoint": endpoint}
                    )
                else:
                    raise AudioProcessingError(
                        "No audio returned from GPT-SoVITS",
                        provider=TTSProvider.GPT_SOVITS
                    )

            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            logger.error(f"GPT-SoVITS voice cloning error: {e}")
            raise AudioProcessingError(
                f"GPT-SoVITS voice cloning failed: {str(e)}",
                provider=TTSProvider.GPT_SOVITS
            ) from e

    async def stream_synthesize(
        self,
        request: TTSRequest
    ) -> AsyncGenerator[bytes, None]:
        """Stream synthesized speech sentence-by-sentence.

        Args:
            request: TTS synthesis request

        Yields:
            Audio chunks as WAV bytes (sentence-level streaming)
        """
        url = f"{self.config.endpoint.base_url}/synthesize/stream"

        payload = {
            "text": request.text,
            "language": request.language,
            "speed": request.speed
        }

        logger.info(
            f"GPT-SoVITS streaming: text_length={len(request.text)}, "
            f"language={request.language}"
        )

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"GPT-SoVITS streaming failed: {response.status} - {error_text}")
                    # Fallback to blocking mode
                    logger.warning("Falling back to blocking synthesis")
                    blocking_response = await self.synthesize(request)
                    yield blocking_response.audio
                    return

                # Stream chunks
                chunk_count = 0
                async for chunk in response.content.iter_chunked(8192):
                    if chunk:
                        chunk_count += 1
                        logger.debug(f"GPT-SoVITS chunk {chunk_count}: {len(chunk)} bytes")
                        yield chunk

                logger.info(f"GPT-SoVITS streaming complete: {chunk_count} chunks")

        except Exception as e:
            logger.error(f"GPT-SoVITS streaming error: {e}")
            # Fallback to blocking mode on error
            logger.warning("Falling back to blocking synthesis due to error")
            blocking_response = await self.synthesize(request)
            yield blocking_response.audio


class ChatterboxProvider(BaseTTSProvider):
    """Chatterbox TTS provider implementation.

    Chatterbox is an expressive multilingual TTS model with reference audio support
    for voice cloning. Supports 23 languages including Arabic, Chinese, English,
    French, German, Spanish, and more.

    Features:
    - Voice cloning with reference audio
    - 23 language support
    - Expressive speech synthesis
    - Gradio-based API

    Example usage:
        ```python
        async with ChatterboxProvider() as provider:
            # Standard synthesis
            request = TTSRequest(
                text="Hello from Chatterbox!",
                language="en",
                speed=1.0
            )
            response = await provider.synthesize(request)

            # Voice cloning with reference audio
            with open("reference.wav", "rb") as f:
                reference_audio = f.read()

            clone_request = VoiceCloneRequest(
                text="This is cloned speech",
                reference_audio=reference_audio,
                language="en"
            )
            response = await provider.clone_voice_from_request(clone_request)
        ```

    Supported Languages (23):
        Arabic, Chinese, Czech, Dutch, English, Finnish, French, German,
        Greek, Hindi, Hungarian, Italian, Japanese, Korean, Polish, Portuguese,
        Russian, Spanish, Swedish, Turkish, Ukrainian, and more.
    """

    def _get_default_config(self) -> TTSProviderConfig:
        """Get default configuration for Chatterbox."""
        return get_provider_config(TTSProvider.CHATTERBOX)

    async def _poll_gradio_result(
        self,
        base_url: str,
        endpoint_path: str,
        event_id: str,
        max_polls: int = 60,
        poll_interval: float = 0.5
    ) -> dict:
        """Poll Gradio event-based API for result.

        Gradio's /gradio_api/call/ endpoints use an event-based async pattern:
        1. POST to /gradio_api/call/{endpoint} returns {"event_id": "..."}
        2. Poll GET /gradio_api/call/{endpoint}/{event_id} until complete
        3. Response contains {"data": [...]} when ready

        Args:
            base_url: Base URL of the Gradio service
            endpoint_path: The endpoint path (e.g., "/gradio_api/call/generate_tts_audio")
            event_id: Event ID returned from initial POST
            max_polls: Maximum number of polling attempts (default: 60)
            poll_interval: Seconds between polls (default: 0.5)

        Returns:
            The complete Gradio response dict containing "data" field

        Raises:
            AudioProcessingError: If polling fails or times out
        """
        poll_url = f"{base_url}{endpoint_path}/{event_id}"

        for attempt in range(max_polls):
            try:
                async with self.session.get(poll_url) as response:
                    if response.status == 200:
                        # Gradio returns Server-Sent Events (SSE) format
                        content_type = response.headers.get("content-type", "")

                        if content_type and "text/event-stream" in content_type:
                            # Parse SSE stream line by line
                            try:
                                async for line_bytes in response.content:
                                    try:
                                        line_text = line_bytes.decode('utf-8').strip()
                                        if line_text.startswith("data:"):
                                            data_json = line_text[5:].strip()
                                            if data_json and data_json != "[DONE]":
                                                try:
                                                    event_data = json.loads(data_json)
                                                    # Check if it's the final "complete" event with data
                                                    if isinstance(event_data, dict) and "data" in event_data:
                                                        logger.info(f"Gradio polling complete on attempt {attempt + 1}")
                                                        return event_data
                                                except json.JSONDecodeError:
                                                    continue
                                    except UnicodeDecodeError:
                                        continue
                            except (aiohttp.ClientPayloadError, aiohttp.ClientError):
                                # Incomplete stream - keep polling
                                pass
                        else:
                            # Regular JSON response
                            try:
                                result = await response.json()
                                if "data" in result:
                                    logger.info(f"Gradio polling complete on attempt {attempt + 1}")
                                    return result
                            except (json.JSONDecodeError, aiohttp.ContentTypeError):
                                # Invalid response - keep polling
                                pass
                    elif response.status == 404:
                        # Event not found yet, keep polling
                        pass
                    else:
                        # Log non-200/404 status but keep polling
                        try:
                            error_text = await response.text()
                            logger.debug(f"Gradio polling attempt {attempt + 1}: {response.status} - {error_text}")
                        except:
                            pass

                # Wait before next poll
                await asyncio.sleep(poll_interval)

            except asyncio.CancelledError:
                raise
            except Exception as e:
                # Log but continue polling
                logger.debug(f"Gradio polling attempt {attempt + 1} error: {type(e).__name__}")
                await asyncio.sleep(poll_interval)

        raise AudioProcessingError(
            f"Gradio polling timed out after {max_polls * poll_interval}s",
            provider=self.config.id.value
        )

    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        """Synthesize speech using Chatterbox TTS with Gradio event polling.

        Args:
            request: TTS synthesis request

        Returns:
            TTS response with generated audio

        Raises:
            ProviderNotAvailableError: If provider is not available
            AudioProcessingError: If synthesis fails
        """
        if not self._is_available:
            await self.check_health()

        url = f"{self.config.endpoint.base_url}{self.config.endpoint.synthesize_path}"

        # Chatterbox uses Gradio event-based API
        # API format: {"data": [text, language, speed, reference_audio (optional)]}
        payload = {
            "data": [
                request.text,
                request.language or "en",
                request.speed or 1.0,
                None  # No reference audio for standard synthesis
            ]
        }

        logger.info(
            f"Chatterbox synthesis: text_length={len(request.text)}, "
            f"language={request.language}, speed={request.speed}"
        )

        try:
            # Step 1: Initiate synthesis and get event_id
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    init_result = await response.json()

                    if "event_id" not in init_result:
                        raise AudioProcessingError(
                            "No event_id in Chatterbox response",
                            provider=TTSProvider.CHATTERBOX
                        )

                    event_id = init_result["event_id"]
                    logger.info(f"Chatterbox event_id: {event_id}")
                else:
                    error_msg = await response.text()
                    logger.error(f"Chatterbox synthesis initiation failed: {response.status} - {error_msg}")
                    raise AudioProcessingError(
                        f"Chatterbox synthesis failed: {error_msg}",
                        provider=TTSProvider.CHATTERBOX
                    )

            # Step 2: Poll for result
            result = await self._poll_gradio_result(
                base_url=self.config.endpoint.base_url,
                endpoint_path=self.config.endpoint.synthesize_path,
                event_id=event_id,
                max_polls=120,  # 60 seconds max (120 * 0.5s)
                poll_interval=0.5
            )

            # Step 3: Extract audio from result
            if "data" in result and len(result["data"]) > 0:
                audio_info = result["data"][0]

                # Check if it's a URL or file reference
                if isinstance(audio_info, str) and audio_info.startswith("http"):
                    # Download audio from URL
                    async with self.session.get(audio_info) as audio_response:
                        if audio_response.status == 200:
                            audio_data = await audio_response.read()
                        else:
                            raise AudioProcessingError(
                                f"Failed to download audio from {audio_info}",
                                provider=TTSProvider.CHATTERBOX
                            )
                elif isinstance(audio_info, dict) and "name" in audio_info:
                    # It's a file reference, download it
                    file_url = f"{self.config.endpoint.base_url}/file={audio_info['name']}"
                    async with self.session.get(file_url) as audio_response:
                        if audio_response.status == 200:
                            audio_data = await audio_response.read()
                        else:
                            raise AudioProcessingError(
                                f"Failed to download audio file: {audio_info['name']}",
                                provider=TTSProvider.CHATTERBOX
                            )
                else:
                    raise AudioProcessingError(
                        f"Unexpected audio format from Chatterbox: {type(audio_info)}",
                        provider=TTSProvider.CHATTERBOX
                    )

                return TTSResponse(
                    audio=audio_data,
                    format=AudioFormat.WAV,
                    sample_rate=22050,  # Chatterbox default
                    provider=TTSProvider.CHATTERBOX,
                    language=request.language,
                    metadata={
                        "multilingual": True,
                        "voice_cloning_capable": True,
                        "languages_supported": 23
                    }
                )
            else:
                raise AudioProcessingError(
                    "No audio data in Chatterbox response",
                    provider=TTSProvider.CHATTERBOX
                )

        except AudioProcessingError:
            raise
        except Exception as e:
            logger.error(f"Chatterbox synthesis error: {e}")
            raise AudioProcessingError(
                f"Chatterbox synthesis error: {str(e)}",
                provider=TTSProvider.CHATTERBOX
            ) from e

    async def clone_voice(
        self,
        request: "VoiceCloneRequest"
    ) -> TTSResponse:
        """Clone a voice using reference audio with Chatterbox.

        Args:
            request: Voice cloning request with reference audio

        Returns:
            TTS response with cloned voice audio

        Raises:
            ProviderNotAvailableError: If provider is not available
            AudioProcessingError: If voice cloning fails
        """
        if not self._is_available:
            await self.check_health()

        url = f"{self.config.endpoint.base_url}{self.config.endpoint.voice_clone_path}"

        # Chatterbox Gradio format: {"data": [text, language, speed, reference_audio_file]}
        # Reference audio needs to be uploaded first or sent as base64
        import base64

        # Convert reference audio to base64
        reference_b64 = base64.b64encode(request.reference_audio).decode('utf-8')

        payload = {
            "data": [
                request.text,
                request.language or "en",
                request.speed or 1.0,
                f"data:audio/wav;base64,{reference_b64}"  # Base64 audio
            ]
        }

        logger.info(
            f"Chatterbox voice cloning: text_length={len(request.text)}, "
            f"language={request.language}, reference_audio_size={len(request.reference_audio)} bytes"
        )

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()

                    if "data" in result and len(result["data"]) > 0:
                        audio_info = result["data"][0]

                        # Handle different response formats (same as synthesize)
                        if isinstance(audio_info, str) and audio_info.startswith("http"):
                            async with self.session.get(audio_info) as audio_response:
                                audio_data = await audio_response.read()
                        elif isinstance(audio_info, dict) and "name" in audio_info:
                            file_url = f"{self.config.endpoint.base_url}/file={audio_info['name']}"
                            async with self.session.get(file_url) as audio_response:
                                audio_data = await audio_response.read()
                        else:
                            raise AudioProcessingError(
                                f"Unexpected audio format: {type(audio_info)}",
                                provider=TTSProvider.CHATTERBOX
                            )

                        return TTSResponse(
                            audio=audio_data,
                            format=AudioFormat.WAV,
                            sample_rate=22050,
                            provider=TTSProvider.CHATTERBOX,
                            language=request.language,
                            metadata={
                                "cloned_voice": True,
                                "reference_audio_used": True
                            }
                        )
                    else:
                        raise AudioProcessingError(
                            "No audio data in Chatterbox clone response",
                            provider=TTSProvider.CHATTERBOX
                        )
                else:
                    error_msg = await response.text()
                    logger.error(f"Chatterbox voice cloning failed: {response.status} - {error_msg}")
                    raise AudioProcessingError(
                        f"Chatterbox voice cloning failed: {error_msg}",
                        provider=TTSProvider.CHATTERBOX
                    )

        except AudioProcessingError:
            raise
        except Exception as e:
            logger.error(f"Chatterbox voice cloning error: {e}")
            raise AudioProcessingError(
                f"Chatterbox voice cloning error: {str(e)}",
                provider=TTSProvider.CHATTERBOX
            ) from e

class BarkProvider(BaseTTSProvider):
    """Bark TTS provider via TTS-WebUI.
    
    Bark is a multi-language generative TTS model with music and sound effects capabilities.
    Accessed via TTS-WebUI platform using OpenAI-compatible API.
    """
    
    def _get_default_config(self) -> TTSProviderConfig:
        """Get default configuration for Bark."""
        return get_provider_config(TTSProvider.BARK)
    
    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        """Synthesize speech using Bark via TTS-WebUI.
        
        Args:
            request: TTS synthesis request
            
        Returns:
            TTS response with audio data
        """
        if not self._is_available:
            await self.check_health()
        
        url = f"{self.config.endpoint.base_url}{self.config.endpoint.synthesize_path}"
        
        voice = request.speaker or "default"
        payload = {
            "model": "bark",
            "input": request.text,
            "voice": voice,
            "response_format": request.output_format.value,
            "speed": request.speed or 1.0
        }
        
        if request.language:
            payload["language"] = request.language
        
        logger.info(f"Bark synthesis via TTS-WebUI: text_length={len(request.text)}, language={request.language}")
        
        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    return TTSResponse(
                        audio=audio_data,
                        format=request.output_format,
                        sample_rate=request.sample_rate,
                        provider=TTSProvider.BARK,
                        language=request.language,
                        speaker=voice,
                        metadata={"model": "bark", "platform": "tts-webui"}
                    )
                else:
                    error_msg = await response.text()
                    logger.error(f"Bark synthesis failed: {response.status} - {error_msg}")
                    raise AudioProcessingError(f"Bark synthesis failed: {error_msg}", provider=TTSProvider.BARK)
        except AudioProcessingError:
            raise
        except Exception as e:
            logger.error(f"Bark synthesis error: {e}")
            raise AudioProcessingError(f"Bark synthesis error: {str(e)}", provider=TTSProvider.BARK) from e


class TortoiseProvider(BaseTTSProvider):
    """Tortoise TTS provider via TTS-WebUI.
    
    Tortoise is a high-quality but slower TTS model with excellent voice cloning.
    Accessed via TTS-WebUI platform using OpenAI-compatible API.
    """
    
    def _get_default_config(self) -> TTSProviderConfig:
        """Get default configuration for Tortoise."""
        return get_provider_config(TTSProvider.TORTOISE)
    
    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        """Synthesize speech using Tortoise via TTS-WebUI.
        
        Args:
            request: TTS synthesis request
            
        Returns:
            TTS response with audio data
        """
        if not self._is_available:
            await self.check_health()
        
        url = f"{self.config.endpoint.base_url}{self.config.endpoint.synthesize_path}"
        
        voice = request.speaker or "default"
        payload = {
            "model": "tortoise",
            "input": request.text,
            "voice": voice,
            "response_format": request.output_format.value,
            "speed": request.speed or 1.0
        }
        
        logger.info(f"Tortoise synthesis via TTS-WebUI: text_length={len(request.text)}")
        
        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    return TTSResponse(
                        audio=audio_data,
                        format=request.output_format,
                        sample_rate=request.sample_rate,
                        provider=TTSProvider.TORTOISE,
                        language=request.language,
                        speaker=voice,
                        metadata={"model": "tortoise", "platform": "tts-webui", "quality": "high"}
                    )
                else:
                    error_msg = await response.text()
                    logger.error(f"Tortoise synthesis failed: {response.status} - {error_msg}")
                    raise AudioProcessingError(f"Tortoise synthesis failed: {error_msg}", provider=TTSProvider.TORTOISE)
        except AudioProcessingError:
            raise
        except Exception as e:
            logger.error(f"Tortoise synthesis error: {e}")
            raise AudioProcessingError(f"Tortoise synthesis error: {str(e)}", provider=TTSProvider.TORTOISE) from e


class MahaTTSProvider(BaseTTSProvider):
    """MahaTTS provider via TTS-WebUI.
    
    MahaTTS supports Indic languages including Hindi, Tamil, Telugu, and more.
    Accessed via TTS-WebUI platform using OpenAI-compatible API.
    """
    
    def _get_default_config(self) -> TTSProviderConfig:
        """Get default configuration for MahaTTS."""
        return get_provider_config(TTSProvider.MAHATTS)
    
    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        """Synthesize speech using MahaTTS via TTS-WebUI.
        
        Args:
            request: TTS synthesis request
            
        Returns:
            TTS response with audio data
        """
        if not self._is_available:
            await self.check_health()
        
        url = f"{self.config.endpoint.base_url}{self.config.endpoint.synthesize_path}"
        
        voice = request.speaker or "default"
        payload = {
            "model": "mahatts",
            "input": request.text,
            "voice": voice,
            "response_format": request.output_format.value,
            "speed": request.speed or 1.0
        }
        
        if request.language:
            payload["language"] = request.language
        
        logger.info(f"MahaTTS synthesis via TTS-WebUI: text_length={len(request.text)}, language={request.language}")
        
        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    return TTSResponse(
                        audio=audio_data,
                        format=request.output_format,
                        sample_rate=request.sample_rate,
                        provider=TTSProvider.MAHATTS,
                        language=request.language,
                        speaker=voice,
                        metadata={"model": "mahatts", "platform": "tts-webui", "indic": True}
                    )
                else:
                    error_msg = await response.text()
                    logger.error(f"MahaTTS synthesis failed: {response.status} - {error_msg}")
                    raise AudioProcessingError(f"MahaTTS synthesis failed: {error_msg}", provider=TTSProvider.MAHATTS)
        except AudioProcessingError:
            raise
        except Exception as e:
            logger.error(f"MahaTTS synthesis error: {e}")
            raise AudioProcessingError(f"MahaTTS synthesis error: {str(e)}", provider=TTSProvider.MAHATTS) from e


class MMSProvider(BaseTTSProvider):
    """MMS provider via TTS-WebUI.
    
    Meta's Massively Multilingual Speech model supporting 1000+ languages.
    Accessed via TTS-WebUI platform using OpenAI-compatible API.
    """
    
    def _get_default_config(self) -> TTSProviderConfig:
        """Get default configuration for MMS."""
        return get_provider_config(TTSProvider.MMS)
    
    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        """Synthesize speech using MMS via TTS-WebUI.
        
        Args:
            request: TTS synthesis request
            
        Returns:
            TTS response with audio data
        """
        if not self._is_available:
            await self.check_health()
        
        url = f"{self.config.endpoint.base_url}{self.config.endpoint.synthesize_path}"
        
        voice = request.speaker or "default"
        payload = {
            "model": "mms",
            "input": request.text,
            "voice": voice,
            "response_format": request.output_format.value,
            "speed": request.speed or 1.0
        }
        
        if request.language:
            payload["language"] = request.language
        
        logger.info(f"MMS synthesis via TTS-WebUI: text_length={len(request.text)}, language={request.language}")
        
        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    return TTSResponse(
                        audio=audio_data,
                        format=request.output_format,
                        sample_rate=request.sample_rate,
                        provider=TTSProvider.MMS,
                        language=request.language,
                        speaker=voice,
                        metadata={"model": "mms", "platform": "tts-webui", "multilingual": "1000+"}
                    )
                else:
                    error_msg = await response.text()
                    logger.error(f"MMS synthesis failed: {response.status} - {error_msg}")
                    raise AudioProcessingError(f"MMS synthesis failed: {error_msg}", provider=TTSProvider.MMS)
        except AudioProcessingError:
            raise
        except Exception as e:
            logger.error(f"MMS synthesis error: {e}")
            raise AudioProcessingError(f"MMS synthesis error: {str(e)}", provider=TTSProvider.MMS) from e


class ValleXProvider(BaseTTSProvider):
    """VALL-E X provider via TTS-WebUI.
    
    Zero-shot voice cloning with cross-lingual support.
    Accessed via TTS-WebUI platform using OpenAI-compatible API.
    """
    
    def _get_default_config(self) -> TTSProviderConfig:
        """Get default configuration for VALL-E X."""
        return get_provider_config(TTSProvider.VALLE_X)
    
    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        """Synthesize speech using VALL-E X via TTS-WebUI.
        
        Args:
            request: TTS synthesis request
            
        Returns:
            TTS response with audio data
        """
        if not self._is_available:
            await self.check_health()
        
        url = f"{self.config.endpoint.base_url}{self.config.endpoint.synthesize_path}"
        
        voice = request.speaker or "default"
        payload = {
            "model": "valle-x",
            "input": request.text,
            "voice": voice,
            "response_format": request.output_format.value,
            "speed": request.speed or 1.0
        }
        
        if request.language:
            payload["language"] = request.language
        
        logger.info(f"VALL-E X synthesis via TTS-WebUI: text_length={len(request.text)}, language={request.language}")
        
        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    return TTSResponse(
                        audio=audio_data,
                        format=request.output_format,
                        sample_rate=request.sample_rate,
                        provider=TTSProvider.VALLE_X,
                        language=request.language,
                        speaker=voice,
                        metadata={"model": "valle-x", "platform": "tts-webui", "zero_shot": True}
                    )
                else:
                    error_msg = await response.text()
                    logger.error(f"VALL-E X synthesis failed: {response.status} - {error_msg}")
                    raise AudioProcessingError(f"VALL-E X synthesis failed: {error_msg}", provider=TTSProvider.VALLE_X)
        except AudioProcessingError:
            raise
        except Exception as e:
            logger.error(f"VALL-E X synthesis error: {e}")
            raise AudioProcessingError(f"VALL-E X synthesis error: {str(e)}", provider=TTSProvider.VALLE_X) from e
