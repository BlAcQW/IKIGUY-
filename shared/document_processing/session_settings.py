"""
Session/Interaction Settings Service.

Provides per-session/per-interaction settings overrides for:
- TTS (Text-to-Speech) settings
- ASR (Speech Recognition) settings
- LLM settings
- Personalization settings

Settings hierarchy: session > user > organization > system defaults

This is extracted from InkWave's session voice settings feature.

Author: KasaAI Team
Date: 2025-11-28
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TTSSettings(BaseModel):
    """Text-to-Speech settings."""

    provider: Optional[str] = None
    voice: Optional[str] = None
    speed: Optional[float] = Field(None, ge=0.5, le=2.0)
    pitch: Optional[float] = Field(None, ge=0.5, le=2.0)
    language: Optional[str] = None


class ASRSettings(BaseModel):
    """Automatic Speech Recognition settings."""

    provider: Optional[str] = None
    language: Optional[str] = None
    model: Optional[str] = None


class LLMSettings(BaseModel):
    """Large Language Model settings."""

    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=8000)
    system_prompt: Optional[str] = None


class PersonalizationSettings(BaseModel):
    """User personalization settings."""

    reading_level: Optional[str] = None  # beginner, intermediate, advanced
    explanation_depth: Optional[str] = None  # simple, detailed, comprehensive
    language: Optional[str] = None
    interests: List[str] = Field(default_factory=list)


class SessionSettings(BaseModel):
    """Combined session settings."""

    tts: TTSSettings = Field(default_factory=TTSSettings)
    asr: ASRSettings = Field(default_factory=ASRSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    personalization: PersonalizationSettings = Field(
        default_factory=PersonalizationSettings
    )
    custom: Dict[str, Any] = Field(default_factory=dict)


class EffectiveSettings(BaseModel):
    """Effective settings with source tracking."""

    tts: Dict[str, Any] = Field(default_factory=dict)
    asr: Dict[str, Any] = Field(default_factory=dict)
    llm: Dict[str, Any] = Field(default_factory=dict)
    personalization: Dict[str, Any] = Field(default_factory=dict)
    custom: Dict[str, Any] = Field(default_factory=dict)

    # Track where each setting came from
    sources: Dict[str, str] = Field(default_factory=dict)


class SessionSettingsService:
    """
    Service for managing per-session settings with hierarchy.

    Settings are merged in order of precedence:
    1. Session-specific overrides (highest priority)
    2. User defaults
    3. Organization defaults
    4. System defaults (lowest priority)
    """

    # System-wide defaults
    SYSTEM_DEFAULTS = SessionSettings(
        tts=TTSSettings(
            provider="styletts2",
            voice="default",
            speed=1.0,
        ),
        asr=ASRSettings(
            provider="whisper",
            language="en",
        ),
        llm=LLMSettings(
            provider="gemini",
            model="gemini-2.0-flash-exp",
            temperature=0.7,
            max_tokens=1000,
        ),
        personalization=PersonalizationSettings(
            reading_level="intermediate",
            explanation_depth="detailed",
            language="en",
        ),
    )

    def __init__(
        self,
        get_session_settings: Optional[callable] = None,
        get_user_settings: Optional[callable] = None,
        get_org_settings: Optional[callable] = None,
        save_session_settings: Optional[callable] = None,
    ):
        """
        Initialize session settings service.

        Args:
            get_session_settings: Async function to fetch session settings
            get_user_settings: Async function to fetch user settings
            get_org_settings: Async function to fetch org settings
            save_session_settings: Async function to save session settings
        """
        self._get_session = get_session_settings
        self._get_user = get_user_settings
        self._get_org = get_org_settings
        self._save_session = save_session_settings

    @staticmethod
    def _merge_settings(
        base: Dict[str, Any],
        override: Dict[str, Any],
        sources: Dict[str, str],
        source_name: str,
    ) -> Dict[str, Any]:
        """
        Merge settings with source tracking.

        Args:
            base: Base settings dict
            override: Override settings dict
            sources: Source tracking dict (modified in place)
            source_name: Name of this source level

        Returns:
            Merged settings
        """
        result = base.copy()
        for key, value in override.items():
            if value is not None:
                result[key] = value
                sources[key] = source_name
        return result

    async def get_effective_settings(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> EffectiveSettings:
        """
        Get effective settings for a session with hierarchy merge.

        Args:
            session_id: Session identifier
            user_id: User identifier (optional)
            organization_id: Organization identifier (optional)

        Returns:
            EffectiveSettings with merged values and source tracking
        """
        sources = {}

        # Start with system defaults
        effective = EffectiveSettings(
            tts=self.SYSTEM_DEFAULTS.tts.dict(exclude_none=True),
            asr=self.SYSTEM_DEFAULTS.asr.dict(exclude_none=True),
            llm=self.SYSTEM_DEFAULTS.llm.dict(exclude_none=True),
            personalization=self.SYSTEM_DEFAULTS.personalization.dict(
                exclude_none=True
            ),
        )

        # Mark all as system defaults
        for category in ["tts", "asr", "llm", "personalization"]:
            for key in getattr(effective, category, {}).keys():
                sources[f"{category}.{key}"] = "system"

        # Apply organization defaults
        if organization_id and self._get_org:
            try:
                org_settings = await self._get_org(organization_id)
                if org_settings:
                    if org_settings.tts:
                        effective.tts = self._merge_settings(
                            effective.tts,
                            org_settings.tts.dict(exclude_none=True),
                            sources,
                            "organization",
                        )
                    if org_settings.asr:
                        effective.asr = self._merge_settings(
                            effective.asr,
                            org_settings.asr.dict(exclude_none=True),
                            sources,
                            "organization",
                        )
                    if org_settings.llm:
                        effective.llm = self._merge_settings(
                            effective.llm,
                            org_settings.llm.dict(exclude_none=True),
                            sources,
                            "organization",
                        )
            except Exception as e:
                logger.warning(f"Failed to get org settings: {e}")

        # Apply user defaults
        if user_id and self._get_user:
            try:
                user_settings = await self._get_user(user_id)
                if user_settings:
                    if user_settings.tts:
                        effective.tts = self._merge_settings(
                            effective.tts,
                            user_settings.tts.dict(exclude_none=True),
                            sources,
                            "user",
                        )
                    if user_settings.asr:
                        effective.asr = self._merge_settings(
                            effective.asr,
                            user_settings.asr.dict(exclude_none=True),
                            sources,
                            "user",
                        )
                    if user_settings.llm:
                        effective.llm = self._merge_settings(
                            effective.llm,
                            user_settings.llm.dict(exclude_none=True),
                            sources,
                            "user",
                        )
                    if user_settings.personalization:
                        effective.personalization = self._merge_settings(
                            effective.personalization,
                            user_settings.personalization.dict(exclude_none=True),
                            sources,
                            "user",
                        )
            except Exception as e:
                logger.warning(f"Failed to get user settings: {e}")

        # Apply session overrides (highest priority)
        if self._get_session:
            try:
                session_settings = await self._get_session(session_id)
                if session_settings:
                    if session_settings.tts:
                        effective.tts = self._merge_settings(
                            effective.tts,
                            session_settings.tts.dict(exclude_none=True),
                            sources,
                            "session",
                        )
                    if session_settings.asr:
                        effective.asr = self._merge_settings(
                            effective.asr,
                            session_settings.asr.dict(exclude_none=True),
                            sources,
                            "session",
                        )
                    if session_settings.llm:
                        effective.llm = self._merge_settings(
                            effective.llm,
                            session_settings.llm.dict(exclude_none=True),
                            sources,
                            "session",
                        )
                    if session_settings.custom:
                        effective.custom = session_settings.custom
            except Exception as e:
                logger.warning(f"Failed to get session settings: {e}")

        effective.sources = sources
        return effective

    async def update_session_settings(
        self,
        session_id: str,
        updates: SessionSettings,
    ) -> bool:
        """
        Update session-specific settings.

        Args:
            session_id: Session identifier
            updates: Settings to update

        Returns:
            True if successful
        """
        if not self._save_session:
            logger.warning("No save_session_settings callback configured")
            return False

        try:
            await self._save_session(session_id, updates)
            logger.info(f"Updated session settings for {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update session settings: {e}")
            return False

    async def clear_session_settings(self, session_id: str) -> bool:
        """
        Clear session-specific settings (revert to user/org/system defaults).

        Args:
            session_id: Session identifier

        Returns:
            True if successful
        """
        return await self.update_session_settings(
            session_id, SessionSettings()
        )


class PersonalizationBuilder:
    """
    Build personalized prompts based on settings.

    Extracted from InkWave's reading level personalization.
    """

    READING_LEVELS = {
        "beginner": {
            "description": "Use simple language and short sentences.",
            "vocabulary": "basic",
            "examples": "many",
        },
        "intermediate": {
            "description": "Use clear explanations with some technical terms.",
            "vocabulary": "moderate",
            "examples": "some",
        },
        "advanced": {
            "description": "Use technical language and assume prior knowledge.",
            "vocabulary": "technical",
            "examples": "few",
        },
    }

    EXPLANATION_DEPTHS = {
        "simple": "Give brief, concise answers.",
        "detailed": "Provide thorough explanations with context.",
        "comprehensive": "Give in-depth analysis covering all aspects.",
    }

    @classmethod
    def build_system_prompt(
        cls,
        base_prompt: str,
        settings: PersonalizationSettings,
    ) -> str:
        """
        Build a personalized system prompt.

        Args:
            base_prompt: Base system prompt
            settings: Personalization settings

        Returns:
            Personalized system prompt
        """
        additions = []

        # Add reading level guidance
        if settings.reading_level:
            level_info = cls.READING_LEVELS.get(
                settings.reading_level, cls.READING_LEVELS["intermediate"]
            )
            additions.append(f"\n\nReading Level: {level_info['description']}")

        # Add explanation depth guidance
        if settings.explanation_depth:
            depth_info = cls.EXPLANATION_DEPTHS.get(
                settings.explanation_depth, cls.EXPLANATION_DEPTHS["detailed"]
            )
            additions.append(f"\nExplanation Style: {depth_info}")

        # Add language preference
        if settings.language and settings.language != "en":
            additions.append(f"\nRespond in: {settings.language}")

        # Add interest context
        if settings.interests:
            interests_str = ", ".join(settings.interests[:5])
            additions.append(f"\nUser interests: {interests_str}")

        return base_prompt + "".join(additions)
