"""
TTS Service for EventFlow.

Provides text-to-speech synthesis for:
- Task reminder voice messages
- Task update audio notifications
- Daily summary voice reports
"""

import base64
import os
import logging
from typing import Dict, Optional, List
from datetime import datetime

from apps.shared.services.tts_provider_service import (
    TTSProviderService,
    SynthesisRequest,
    SynthesisResult
)

logger = logging.getLogger(__name__)


class EventFlowTTSService:
    """
    TTS service for EventFlow voice features.

    Handles:
    - Task reminder voice generation
    - Task update notifications
    - Daily summary audio reports
    - Multi-language support (English, Twi, Ga, French)
    """

    def __init__(self):
        """Initialize TTS service with shared TTSProviderService."""
        self.tts_provider = TTSProviderService(
            enable_billing=True,
            enable_health_monitoring=True,
            enable_email_alerts=False,
            cache_ttl=300  # Cache for 5 minutes
        )
        self._initialized = False

        # Storage path for generated audio
        self.storage_path = os.getenv(
            "EVENTFLOW_AUDIO_PATH",
            "/opt/kasaai/apps/eventflow/backend/storage/audio"
        )
        self.storage_base_url = os.getenv(
            "EVENTFLOW_AUDIO_URL",
            "https://eventflow-api.ailabsafrica.com/storage/audio"
        )

    async def initialize(self) -> bool:
        """
        Initialize TTS service.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        if self._initialized:
            return True

        try:
            await self.tts_provider.initialize()
            self._initialized = True

            # Create storage directory
            os.makedirs(self.storage_path, exist_ok=True)

            logger.info("EventFlowTTSService initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize TTS service: {e}")
            return False

    async def generate_task_reminder(
        self,
        task_title: str,
        task_deadline: datetime,
        responsible_person_name: str,
        event_name: str,
        user_id: str,
        language: str = "en",
        provider_id: str = "coqui_xtts",
        voice_id: Optional[str] = None,
        speed: float = 1.0
    ) -> Optional[Dict]:
        """
        Generate voice reminder for a task.

        Args:
            task_title: Task title
            task_deadline: Task deadline
            responsible_person_name: Person responsible
            event_name: Event name
            user_id: User ID for billing
            language: Language code (en, tw, ga, fr)
            provider_id: TTS provider to use
            voice_id: Voice ID (optional)
            speed: Speech speed (0.5-2.0)

        Returns:
            Dict with audio_url, duration, cost, text, or None if failed
        """
        if not self._initialized:
            await self.initialize()

        # Build reminder text based on language
        days_until_deadline = (task_deadline - datetime.utcnow()).days

        if language == "tw":  # Twi
            reminder_text = f"Akwaaba {responsible_person_name}. Yɛbɔ wo kae sɛ woanya dwuma '{task_title}' wɔ {event_name}. Nna {days_until_deadline} na aka ansa na bereɛ no adu."
        elif language == "ga":  # Ga
            reminder_text = f"Hei {responsible_person_name}, yɛba ko wo ŋmɛɛ sɛ ewɔ wòyɛ '{task_title}' lɛ {event_name}. Eŋmɛɛ {days_until_deadline} shikɛ deadline no."
        elif language == "fr":  # French
            reminder_text = f"Bonjour {responsible_person_name}, c'est Ama d'EventFlow. Je vous rappelle votre tâche '{task_title}' pour {event_name}. Il vous reste {days_until_deadline} jours jusqu'à la date limite."
        else:  # English (default)
            reminder_text = f"Hello {responsible_person_name}, this is Ama from EventFlow. I'm calling to remind you about your task '{task_title}' for {event_name}. You have {days_until_deadline} days until the deadline. Please let us know if you need any help."

        # Synthesize speech
        try:
            synthesis_request = SynthesisRequest(
                provider_id=provider_id,
                text=reminder_text,
                language=language,
                voice_id=voice_id,
                speed=speed,
                pitch=0.0,
                output_format="mp3"
            )

            result: SynthesisResult = await self.tts_provider.synthesize(
                user_id=user_id,
                request=synthesis_request
            )

            # Save audio file
            audio_url = await self._save_audio_file(
                audio_base64=result.audio_base64,
                filename_prefix=f"reminder_{task_title}",
                user_id=user_id
            )

            logger.info(
                f"Generated task reminder for '{task_title}': "
                f"{result.duration:.2f}s, ${result.cost:.4f}"
            )

            return {
                "audio_url": audio_url,
                "text": reminder_text,
                "duration": result.duration,
                "cost": result.cost,
                "provider_used": result.provider_id,
                "language": language
            }

        except Exception as e:
            logger.error(f"Failed to generate task reminder: {e}")
            return None

    async def generate_daily_summary(
        self,
        event_name: str,
        total_tasks: int,
        completed_tasks: int,
        overdue_tasks: int,
        high_priority_tasks: List[str],
        user_id: str,
        language: str = "en",
        provider_id: str = "coqui_xtts",
        voice_id: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Generate voice daily summary for event organizer.

        Args:
            event_name: Event name
            total_tasks: Total number of tasks
            completed_tasks: Number of completed tasks
            overdue_tasks: Number of overdue tasks
            high_priority_tasks: List of high priority task titles
            user_id: User ID for billing
            language: Language code
            provider_id: TTS provider
            voice_id: Voice ID (optional)

        Returns:
            Dict with audio_url, duration, cost, text, or None if failed
        """
        if not self._initialized:
            await self.initialize()

        # Build summary text
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        if language == "tw":  # Twi
            summary_text = f"""
            Maakye! Yɛn summary wɔ {event_name}.

            Woanya nnwuma {total_tasks} nyinaa, na {completed_tasks} awie.
            Ɛyɛ {completion_rate:.0f}% completion rate.

            Nnwuma {overdue_tasks} na ɛrekyɛ na ɛhia attention.
            """
        elif language == "ga":  # Ga
            summary_text = f"""
            Ojekoo! Yɛn summary lɛ {event_name}.

            Ewɔ nnwuma {total_tasks} kɛkɛ, kɛ {completed_tasks} ba wie.
            Ɛyɛ {completion_rate:.0f}% completion rate.

            Nnwuma {overdue_tasks} ba overdue kɛ ɛhia attention.
            """
        else:  # English (default)
            summary_text = f"""
            Good evening! Here's your daily summary for {event_name}.

            You have {total_tasks} tasks in total, with {completed_tasks} completed.
            That's a {completion_rate:.0f}% completion rate.

            {overdue_tasks} tasks are overdue and need attention.
            """

            if high_priority_tasks:
                summary_text += f"\nYour high priority tasks are: {', '.join(high_priority_tasks[:3])}."

            summary_text += "\n\nWould you like to make some calls tomorrow to follow up?"

        # Synthesize
        try:
            synthesis_request = SynthesisRequest(
                provider_id=provider_id,
                text=summary_text.strip(),
                language=language,
                voice_id=voice_id,
                speed=1.0,
                pitch=0.0,
                output_format="mp3"
            )

            result: SynthesisResult = await self.tts_provider.synthesize(
                user_id=user_id,
                request=synthesis_request
            )

            # Save audio
            audio_url = await self._save_audio_file(
                audio_base64=result.audio_base64,
                filename_prefix=f"summary_{event_name}",
                user_id=user_id
            )

            logger.info(
                f"Generated daily summary for '{event_name}': "
                f"{result.duration:.2f}s, ${result.cost:.4f}"
            )

            return {
                "audio_url": audio_url,
                "text": summary_text.strip(),
                "duration": result.duration,
                "cost": result.cost,
                "provider_used": result.provider_id,
                "language": language
            }

        except Exception as e:
            logger.error(f"Failed to generate daily summary: {e}")
            return None

    async def generate_task_update_notification(
        self,
        task_title: str,
        update_text: str,
        updated_by: str,
        event_name: str,
        user_id: str,
        language: str = "en",
        provider_id: str = "coqui_xtts"
    ) -> Optional[Dict]:
        """
        Generate voice notification for task update.

        Args:
            task_title: Task title
            update_text: Update description
            updated_by: Name of person who updated
            event_name: Event name
            user_id: User ID for billing
            language: Language code
            provider_id: TTS provider

        Returns:
            Dict with audio_url, duration, cost, text, or None if failed
        """
        if not self._initialized:
            await self.initialize()

        # Build notification text
        if language == "tw":  # Twi
            notification_text = f"{updated_by} ama '{task_title}' wɔ {event_name} foforo. Asɛm a ɔkaa: {update_text}"
        elif language == "ga":  # Ga
            notification_text = f"{updated_by} ba update '{task_title}' lɛ {event_name}. Ɔkaa: {update_text}"
        else:  # English
            notification_text = f"{updated_by} has updated '{task_title}' for {event_name}. They said: {update_text}"

        try:
            synthesis_request = SynthesisRequest(
                provider_id=provider_id,
                text=notification_text,
                language=language,
                voice_id=None,
                speed=1.0,
                pitch=0.0,
                output_format="mp3"
            )

            result: SynthesisResult = await self.tts_provider.synthesize(
                user_id=user_id,
                request=synthesis_request
            )

            # Save audio
            audio_url = await self._save_audio_file(
                audio_base64=result.audio_base64,
                filename_prefix=f"update_{task_title}",
                user_id=user_id
            )

            return {
                "audio_url": audio_url,
                "text": notification_text,
                "duration": result.duration,
                "cost": result.cost,
                "provider_used": result.provider_id
            }

        except Exception as e:
            logger.error(f"Failed to generate task update notification: {e}")
            return None

    async def get_available_voices(
        self,
        provider_id: str = "coqui_xtts"
    ) -> Dict:
        """
        Get available voices for a provider.

        Args:
            provider_id: TTS provider ID

        Returns:
            Dict with available voices
        """
        if not self._initialized:
            await self.initialize()

        try:
            voices = await self.tts_provider.get_available_voices(provider_id)
            return voices
        except Exception as e:
            logger.error(f"Failed to get available voices: {e}")
            return {"success": False, "error": str(e)}

    async def get_supported_languages(self) -> Dict:
        """
        Get all supported languages across providers.

        Returns:
            Dict mapping providers to supported languages
        """
        if not self._initialized:
            await self.initialize()

        try:
            languages = await self.tts_provider.get_supported_languages()
            return languages
        except Exception as e:
            logger.error(f"Failed to get supported languages: {e}")
            return {"success": False, "error": str(e)}

    async def get_providers_status(self) -> Dict:
        """
        Get status of all TTS providers.

        Returns:
            Dict with provider statuses
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Use get_available_providers from shared service
            providers = await self.tts_provider.get_available_providers(force_refresh=False)
            return {"success": True, "providers": providers}
        except Exception as e:
            logger.error(f"Failed to get providers status: {e}")
            return {"success": False, "error": str(e)}

    async def _save_audio_file(
        self,
        audio_base64: str,
        filename_prefix: str,
        user_id: str
    ) -> str:
        """
        Save audio file to storage and return public URL.

        Args:
            audio_base64: Base64-encoded audio data
            filename_prefix: Prefix for filename
            user_id: User ID (for organizing files)

        Returns:
            Public URL to access the audio file
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            # Sanitize filename prefix
            safe_prefix = "".join(c if c.isalnum() else "_" for c in filename_prefix)[:50]
            filename = f"{safe_prefix}_{user_id}_{timestamp}.mp3"
            file_path = os.path.join(self.storage_path, filename)

            # Decode and save
            audio_bytes = base64.b64decode(audio_base64)
            with open(file_path, "wb") as f:
                f.write(audio_bytes)

            # Return public URL
            audio_url = f"{self.storage_base_url}/{filename}"
            logger.debug(f"Saved audio to {file_path}")

            return audio_url

        except Exception as e:
            logger.error(f"Failed to save audio file: {e}")
            # Fallback to base64 data URL
            return f"data:audio/mp3;base64,{audio_base64}"
