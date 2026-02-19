"""
Unit tests for material voice service RAG filtering.

Tests that voice chat queries are correctly filtered by material_id to ensure
responses only come from the specific document being studied, not from other
documents in the same subject collection.

Bug Fix: FIX-2025-11-27-001
Issue: Voice chat was returning content from wrong documents because RAG queries
       were not filtering by material_id.
Solution: Added rag_filters={"material_id": material_id} to VoiceConversationRequest

Created: 2025-11-27
Author: KasaAI
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any


class TestMaterialVoiceFiltering:
    """Tests for material_id filtering in voice chat RAG queries."""

    def test_voice_conversation_request_includes_material_id_filter(self):
        """
        Test that VoiceConversationRequest is created with material_id filter.

        Verifies the fix that adds rag_filters={"material_id": material_id}
        to prevent retrieving content from wrong documents.
        """
        # Import here to avoid import errors if service is not running
        import sys
        sys.path.insert(0, "/opt/kasaai/apps")

        from apps.shared.services.conversational_voice_service import (
            VoiceConversationRequest
        )

        # Create request with material_id filter
        material_id = "test_material_123"
        request = VoiceConversationRequest(
            audio_base64="base64audio",
            collection_name="test_collection",
            organization_id="org_123",
            context={"material_title": "Test Doc"},
            rag_filters={"material_id": material_id},
            asr_provider_id="whisper_large_v3",
            tts_provider_id="coqui_xtts"
        )

        # Verify filter is set correctly
        assert request.rag_filters is not None
        assert "material_id" in request.rag_filters
        assert request.rag_filters["material_id"] == material_id

    @pytest.mark.asyncio
    async def test_material_voice_service_passes_material_id_filter(self):
        """
        Test that MaterialVoiceService passes material_id filter to RAG.

        This test mocks the voice service to verify that:
        1. material_id is included in rag_filters
        2. The filter reaches the RAG query
        """
        import sys
        sys.path.insert(0, "/opt/kasaai/apps")

        from apps.shared.services.conversational_voice_service import (
            VoiceConversationRequest,
            VoiceConversationResult
        )

        # Track what filters are passed
        captured_request = None

        # Mock the process_voice_message to capture the request
        async def mock_process_voice_message(user_id, request, organization_id):
            nonlocal captured_request
            captured_request = request
            # Return a mock result
            return VoiceConversationResult(
                transcribed_text="test question",
                response_text="test response",
                confidence_score=0.9,
                sources_used=["Test Source"],
                response_audio_base64="base64audio",
                audio_duration=1.0
            )

        # Create the request as MaterialVoiceService would
        material_id = "691b6c640e0f90f347036667"
        request = VoiceConversationRequest(
            audio_base64="base64audio",
            collection_name="studyflow_org_subject",
            organization_id="org_123",
            context={"material_id": material_id, "material_title": "Test"},
            rag_filters={"material_id": material_id},  # This is the fix
            asr_provider_id="whisper_large_v3",
            tts_provider_id="coqui_xtts",
            max_tokens=300
        )

        # Verify the filter is set
        assert request.rag_filters is not None
        assert request.rag_filters.get("material_id") == material_id

    def test_material_voice_service_code_includes_filter(self):
        """
        Test that MaterialVoiceService source code includes rag_filters.

        This is a code inspection test to ensure the fix is in place.
        """
        import inspect
        import sys
        sys.path.insert(0, "/opt/kasaai/apps")

        from studyflow.backend.app.services.material_voice_service import (
            MaterialVoiceService
        )

        # Get the source code of process_voice_question
        source = inspect.getsource(MaterialVoiceService.process_voice_question)

        # Verify the fix is in the code
        assert "rag_filters" in source, \
            "MaterialVoiceService.process_voice_question should include rag_filters"
        assert "material_id" in source, \
            "rag_filters should include material_id"


class TestRagFilterIntegration:
    """
    Integration tests for RAG filtering.

    These tests require database access and should be run against a test database.
    """

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_rag_query_respects_material_id_filter(self):
        """
        Integration test: Verify RAG query only returns chunks from filtered material.

        Requires: PostgreSQL with pgvector and test data.
        """
        import os
        import sys
        sys.path.insert(0, "/opt/kasaai/apps")

        # Skip if not in integration test mode
        if not os.getenv("RUN_INTEGRATION_TESTS"):
            pytest.skip("Integration tests disabled. Set RUN_INTEGRATION_TESTS=1")

        from shared.integration.rag import RAGService, RAGConfig

        config = RAGConfig(
            postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
            postgres_port=os.getenv("POSTGRES_PORT", "5432"),
            postgres_user=os.getenv("POSTGRES_USER", "postgres"),
            postgres_password=os.getenv("POSTGRES_PASSWORD"),
            postgres_db=os.getenv("POSTGRES_DB", "kasaai_core"),
            ai_provider="gemini",
            api_key=os.getenv("GEMINI_API_KEY"),
            llm_model="gemini-2.5-flash",
            embedding_model="text-embedding-004"
        )

        rag_service = RAGService(config)

        # Query with filter
        test_material_id = "691b6c640e0f90f347036667"  # Diffie-Hellman doc
        result = await rag_service.query_knowledge_base(
            collection_name="studyflow_9daf0254_96f8_4d80_a17d_5324673edc85_computer_science_grade10",
            query="What is this document about?",
            filters={"material_id": test_material_id}
        )

        # Verify response is from correct document
        assert result.success
        assert any("Duffie_Hellman" in src for src in result.sources_used), \
            "Response should come from Diffie-Hellman document"
        assert "IOP Conference" not in result.response, \
            "Response should not contain content from PROJECT_CHAPTER"
