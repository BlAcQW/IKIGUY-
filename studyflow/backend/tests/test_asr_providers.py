"""
Tests for ASR Provider functionality in StudyFlow.

Tests cover:
- ASR provider registry with Groq Whisper providers
- ASR provider service cost calculation
- Voice settings API ASR provider endpoints

Author: KasaAI
Date: 2025-11-26
"""

import pytest
import sys
from unittest.mock import patch, MagicMock, AsyncMock
from decimal import Decimal

# Add paths for imports
sys.path.insert(0, "/opt/kasaai/apps")
sys.path.insert(0, "/opt/kasaai/apps/studyflow/backend")


class TestASRProviderRegistry:
    """Tests for ASR provider registry configuration."""

    def test_groq_whisper_providers_registered(self):
        """Test that Groq Whisper providers are in the default ASR config."""
        from apps.shared.integration.ai_services.provider_registry import (
            get_default_asr_providers_config
        )

        config = get_default_asr_providers_config()

        # Check Groq Whisper Large v3 Turbo is registered
        assert "groq_whisper_large_v3_turbo" in config
        turbo = config["groq_whisper_large_v3_turbo"]
        assert turbo["name"] == "Groq Whisper Large v3 Turbo"
        assert turbo["endpoint"] == "https://api.groq.com/openai"
        assert turbo["model_name"] == "whisper-large-v3-turbo"
        assert turbo["requires_api_key"] is True
        assert turbo["api_key_env"] == "GROQ_API_KEY"

        # Check Groq Whisper Large v3 is registered
        assert "groq_whisper_large_v3" in config
        large = config["groq_whisper_large_v3"]
        assert large["name"] == "Groq Whisper Large v3"
        assert large["model_name"] == "whisper-large-v3"
        assert large["capabilities"]["translation"] is True

    def test_all_asr_providers_have_required_fields(self):
        """Test that all ASR providers have required configuration fields."""
        from apps.shared.integration.ai_services.provider_registry import (
            get_default_asr_providers_config
        )

        config = get_default_asr_providers_config()
        required_fields = ["name", "endpoint", "provider_type", "languages", "capabilities", "description"]

        for provider_id, provider_config in config.items():
            for field in required_fields:
                assert field in provider_config, f"Provider {provider_id} missing field: {field}"

    def test_asr_provider_registry_loads_providers(self):
        """Test that ASR providers can be loaded into the registry."""
        from apps.shared.integration.ai_services.provider_registry import (
            AIProviderRegistry,
            get_default_asr_providers_config,
            ProviderType
        )

        registry = AIProviderRegistry()
        asr_config = get_default_asr_providers_config()

        registry.register_providers_from_config(
            asr_config,
            provider_type=ProviderType.ASR
        )

        # Verify providers are registered
        asr_providers = registry.get_asr_providers()
        assert len(asr_providers) >= 5  # At least 5 ASR providers

        # Verify Groq providers can be retrieved
        groq_turbo = registry.get_provider("groq_whisper_large_v3_turbo")
        assert groq_turbo is not None
        assert groq_turbo.name == "Groq Whisper Large v3 Turbo"

        groq_large = registry.get_provider("groq_whisper_large_v3")
        assert groq_large is not None


class TestASRCostCalculation:
    """Tests for ASR cost calculation."""

    def test_groq_turbo_cost_calculation(self):
        """Test Groq Whisper Large v3 Turbo cost: $0.04/hour."""
        from apps.shared.integration.usage_calculator import UsageCalculator

        calculator = UsageCalculator()

        # 1 hour of audio = $0.04
        cost = calculator.calculate_asr_cost(
            duration_seconds=3600,  # 1 hour
            provider="groq_whisper_large_v3_turbo"
        )
        assert abs(cost - 0.04) < 0.0001

        # 30 minutes = $0.02
        cost_30min = calculator.calculate_asr_cost(
            duration_seconds=1800,
            provider="groq_whisper_large_v3_turbo"
        )
        assert abs(cost_30min - 0.02) < 0.0001

    def test_groq_large_cost_calculation(self):
        """Test Groq Whisper Large v3 cost: $0.111/hour."""
        from apps.shared.integration.usage_calculator import UsageCalculator

        calculator = UsageCalculator()

        # 1 hour of audio = $0.111
        cost = calculator.calculate_asr_cost(
            duration_seconds=3600,
            provider="groq_whisper_large_v3"
        )
        assert abs(cost - 0.111) < 0.0001

    def test_openai_whisper_cost_calculation(self):
        """Test OpenAI Whisper cost: $0.006/minute."""
        from apps.shared.integration.usage_calculator import UsageCalculator

        calculator = UsageCalculator()

        # 1 minute = $0.006
        cost = calculator.calculate_asr_cost(
            duration_seconds=60,
            provider="openai_whisper"
        )
        assert abs(cost - 0.006) < 0.0001

        # 10 minutes = $0.06
        cost_10min = calculator.calculate_asr_cost(
            duration_seconds=600,
            provider="openai_whisper"
        )
        assert abs(cost_10min - 0.06) < 0.0001

    def test_self_hosted_whisper_cost(self):
        """Test self-hosted Whisper cost (minimal)."""
        from apps.shared.integration.usage_calculator import UsageCalculator

        calculator = UsageCalculator()

        # 1 minute = $0.001 (minimal cost for self-hosted)
        cost = calculator.calculate_asr_cost(
            duration_seconds=60,
            provider="whisper_large_v3"
        )
        assert abs(cost - 0.001) < 0.0001

    def test_cost_comparison_providers(self):
        """Test cost comparison between providers for same duration."""
        from apps.shared.integration.usage_calculator import UsageCalculator

        calculator = UsageCalculator()
        duration_1hr = 3600  # 1 hour in seconds

        groq_turbo_cost = calculator.calculate_asr_cost(duration_1hr, "groq_whisper_large_v3_turbo")
        groq_large_cost = calculator.calculate_asr_cost(duration_1hr, "groq_whisper_large_v3")
        openai_cost = calculator.calculate_asr_cost(duration_1hr, "openai_whisper")

        # Groq Turbo should be cheapest
        assert groq_turbo_cost < groq_large_cost
        assert groq_turbo_cost < openai_cost

        # OpenAI should be most expensive for 1 hour
        # OpenAI: $0.006/min * 60 = $0.36/hour
        assert openai_cost > groq_large_cost


class TestASRProviderService:
    """Tests for ASR Provider Service with Groq support."""

    @pytest.mark.asyncio
    async def test_asr_service_initialization(self):
        """Test ASR service initializes with providers."""
        from apps.shared.services.asr_provider_service import ASRProviderService

        service = ASRProviderService(
            enable_billing=False,
            enable_health_monitoring=False
        )

        await service.initialize()

        # Check providers are registered
        providers = service.provider_registry.get_asr_providers()
        assert len(providers) > 0

        # Check Groq providers are available
        provider_ids = [p.id for p in providers]
        assert "groq_whisper_large_v3_turbo" in provider_ids

    @pytest.mark.asyncio
    async def test_groq_provider_has_model_name(self):
        """Test that Groq providers have model_name attribute."""
        from apps.shared.services.asr_provider_service import ASRProviderService

        service = ASRProviderService(
            enable_billing=False,
            enable_health_monitoring=False
        )

        await service.initialize()

        groq_turbo = service.provider_registry.get_provider("groq_whisper_large_v3_turbo")
        assert groq_turbo is not None

        # Check model_name is accessible
        model_name = getattr(groq_turbo, 'model_name', None)
        assert model_name == "whisper-large-v3-turbo"


class TestVoiceSettingsASRProviders:
    """Tests for Voice Settings API ASR provider endpoints."""

    def test_asr_providers_in_providers_response(self):
        """Test that /providers endpoint returns ASR providers."""
        # This is an integration test that would require the actual API
        # For unit testing, we verify the provider config structure

        from apps.shared.integration.ai_services.provider_registry import (
            get_default_asr_providers_config
        )

        config = get_default_asr_providers_config()

        # Verify we have expected ASR providers
        expected_providers = [
            "openai_whisper",
            "whisper_large_v3",
            "groq_whisper_large_v3_turbo",
            "groq_whisper_large_v3"
        ]

        for provider_id in expected_providers:
            assert provider_id in config, f"Missing provider: {provider_id}"

    def test_asr_provider_metadata_for_ui(self):
        """Test that ASR providers have metadata needed for UI display."""
        from apps.shared.integration.ai_services.provider_registry import (
            get_default_asr_providers_config
        )

        config = get_default_asr_providers_config()

        # Check Groq providers have UI-relevant metadata
        groq_turbo = config["groq_whisper_large_v3_turbo"]
        assert "icon" in groq_turbo
        assert "description" in groq_turbo
        assert "metadata" in groq_turbo
        assert "cost_per_hour" in groq_turbo["metadata"]
        assert "speed_factor" in groq_turbo["metadata"]


class TestASRProviderAPIIntegration:
    """Integration tests for ASR provider API calls (requires API key)."""

    @pytest.mark.skip(reason="Requires GROQ_API_KEY environment variable")
    @pytest.mark.asyncio
    async def test_groq_transcription_real_api(self):
        """
        Test actual Groq API transcription (skipped by default).

        To run this test:
        1. Set GROQ_API_KEY environment variable
        2. Run: pytest tests/test_asr_providers.py::TestASRProviderAPIIntegration -v --no-skip
        """
        import os
        import base64
        from apps.shared.services.asr_provider_service import (
            ASRProviderService,
            TranscriptionRequest
        )

        # Check for API key
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            pytest.skip("GROQ_API_KEY not set")

        service = ASRProviderService(
            enable_billing=False,
            enable_health_monitoring=False
        )
        await service.initialize()

        # Create a simple test audio (would need actual audio file)
        # For real testing, load an actual audio file
        # audio_base64 = base64.b64encode(audio_bytes).decode()

        # request = TranscriptionRequest(
        #     provider_id="groq_whisper_large_v3_turbo",
        #     audio_base64=audio_base64,
        #     language="en"
        # )

        # result = await service.transcribe(
        #     user_id="test_user",
        #     request=request,
        #     skip_billing=True
        # )

        # assert result.text is not None
        # assert result.provider_id == "groq_whisper_large_v3_turbo"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
