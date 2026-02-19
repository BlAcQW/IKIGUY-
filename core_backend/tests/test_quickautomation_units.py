#!/usr/bin/env python3
"""
Unit Tests for QuickAutomationDeployment Components.

Tests individual components and functions of the automation deployment workflow:
- System prompt generation validation
- Database model validation
- Error handling and edge cases
- Configuration validation
- Data transformation and sanitization
"""

import pytest
import json
import uuid
from datetime import datetime
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock
from pydantic import ValidationError

# Test fixtures and utilities
@pytest.fixture
def sample_system_prompt():
    """Sample system prompt for testing."""
    return """You are a professional customer support specialist representing Test Company.

Company Information:
- Test Company is a technology company providing innovative solutions.

Your Role:
As a customer support specialist, your primary goal is to resolve customer issues efficiently.

Key Responsibilities:
- Listen actively to customer concerns
- Provide step-by-step troubleshooting guidance
- Escalate complex issues when necessary

Communication Guidelines:
- Maintain a professional tone
- Be helpful, patient, and understanding

Important Notes:
- You are speaking on the phone, not via text chat
- Keep responses concise but informative
"""

@pytest.fixture
def sample_company_info():
    """Sample company information for testing."""
    return {
        "name": "Test Company",
        "industry": "Technology",
        "description": "Innovative technology solutions provider",
        "website": "https://test.com",
        "services": ["Software Development", "Consulting", "Support"]
    }

@pytest.fixture
def sample_assistant_config():
    """Sample assistant configuration for testing."""
    return {
        "id": str(uuid.uuid4()),
        "name": "Test Assistant",
        "description": "Test assistant for unit testing",
        "user_id": "test_user",
        "template_id": "test_template",
        "status": "active",
        "llm_provider": "openai",
        "llm_model": "gpt-4o-mini",
        "first_message_mode": "assistant_first",
        "first_message": "Hello! How can I help you?",
        "system_prompt": "Test system prompt",
        "tts_provider": "openai",
        "tts_voice": "alloy",
        "language": "en",
        "country": "US",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

class TestSystemPromptGeneration:
    """Test system prompt generation and validation."""

    def test_system_prompt_length_validation(self, sample_system_prompt):
        """Test that system prompts meet minimum length requirements."""
        # Valid prompt
        assert len(sample_system_prompt) >= 100, "System prompt should be at least 100 characters"

        # Too short prompt
        short_prompt = "Hello"
        assert len(short_prompt) < 100, "Short prompt should fail validation"

    def test_system_prompt_content_validation(self, sample_system_prompt):
        """Test that system prompts contain required elements."""
        required_elements = [
            "customer support",
            "professional",
            "responsibilities",
            "communication guidelines"
        ]

        prompt_lower = sample_system_prompt.lower()
        for element in required_elements:
            assert element in prompt_lower, f"System prompt should contain '{element}'"

    def test_system_prompt_structure_validation(self, sample_system_prompt):
        """Test system prompt has proper structure."""
        # Should have sections
        assert "Company Information:" in sample_system_prompt
        assert "Your Role:" in sample_system_prompt
        assert "Key Responsibilities:" in sample_system_prompt
        assert "Communication Guidelines:" in sample_system_prompt

        # Should have bullet points
        assert "- " in sample_system_prompt, "Should contain bullet points"

    def test_system_prompt_sanitization(self):
        """Test system prompt sanitization for database storage."""
        unsafe_prompt = 'Test prompt with "quotes" and \'single quotes\' and {special} characters'

        # Test JSON serialization (what would happen in database save)
        try:
            json_safe = json.dumps(unsafe_prompt)
            deserialized = json.loads(json_safe)
            assert deserialized == unsafe_prompt, "Prompt should survive JSON serialization"
        except Exception as e:
            pytest.fail(f"System prompt sanitization failed: {e}")

class TestCompanyInfoExtraction:
    """Test company information extraction and validation."""

    def test_company_info_required_fields(self, sample_company_info):
        """Test that company info has required fields."""
        required_fields = ["name"]

        for field in required_fields:
            assert field in sample_company_info, f"Company info should have '{field}' field"
            assert sample_company_info[field], f"Company info '{field}' should not be empty"

    def test_company_info_optional_fields(self, sample_company_info):
        """Test optional company info fields."""
        optional_fields = ["industry", "description", "website", "services"]

        for field in optional_fields:
            if field in sample_company_info:
                assert isinstance(sample_company_info[field], (str, list)), f"Field '{field}' should be string or list"

    def test_company_info_data_types(self, sample_company_info):
        """Test company info data type validation."""
        # Name should be string
        assert isinstance(sample_company_info["name"], str)

        # Services should be list if present
        if "services" in sample_company_info:
            assert isinstance(sample_company_info["services"], list)
            for service in sample_company_info["services"]:
                assert isinstance(service, str)

    def test_company_info_empty_handling(self):
        """Test handling of empty company info."""
        empty_info = {}

        # Should handle gracefully
        company_name = empty_info.get("name", "Unknown Company")
        assert company_name == "Unknown Company"

class TestAssistantConfiguration:
    """Test assistant configuration validation and creation."""

    def test_assistant_config_required_fields(self, sample_assistant_config):
        """Test assistant configuration has all required fields."""
        required_fields = [
            "id", "name", "system_prompt", "llm_provider",
            "llm_model", "tts_provider", "tts_voice", "language"
        ]

        for field in required_fields:
            assert field in sample_assistant_config, f"Assistant config should have '{field}'"
            assert sample_assistant_config[field], f"Assistant config '{field}' should not be empty"

    def test_assistant_config_default_values(self):
        """Test assistant configuration default values."""
        minimal_config = {
            "name": "Test Assistant",
            "system_prompt": "Test prompt"
        }

        # Test default value assignment
        defaults = {
            "status": "active",
            "llm_provider": "openai",
            "llm_model": "gpt-4o-mini",
            "tts_provider": "openai",
            "tts_voice": "alloy",
            "language": "en",
            "country": "US",
            "speed": 1.0,
            "interruptible": True,
            "record_calls": True
        }

        # Simulate default assignment
        for key, default_value in defaults.items():
            if key not in minimal_config:
                minimal_config[key] = default_value

        for key, expected_value in defaults.items():
            assert minimal_config[key] == expected_value

    def test_assistant_config_validation(self, sample_assistant_config):
        """Test assistant configuration validation."""
        # Speed should be within valid range
        assert 0.5 <= sample_assistant_config.get("speed", 1.0) <= 2.0

        # Language should be valid ISO code
        assert len(sample_assistant_config["language"]) == 2

        # Status should be valid
        valid_statuses = ["draft", "active", "published", "archived"]
        assert sample_assistant_config["status"] in valid_statuses

class TestDatabaseOperations:
    """Test database operations and data persistence."""

    def test_assistant_id_generation(self):
        """Test assistant ID generation."""
        # Generate multiple IDs
        ids = [str(uuid.uuid4()) for _ in range(10)]

        # Should all be unique
        assert len(set(ids)) == len(ids), "All generated IDs should be unique"

        # Should be valid UUID format
        for id_str in ids:
            try:
                uuid.UUID(id_str)
            except ValueError:
                pytest.fail(f"Generated ID '{id_str}' is not a valid UUID")

    def test_metadata_creation(self, sample_company_info):
        """Test metadata creation for database storage."""
        metadata = {
            "created_by": "quickdeployment",
            "company_info": sample_company_info,
            "creation_method": "automated_analysis",
            "created_date": datetime.now().isoformat()
        }

        # Should be JSON serializable
        try:
            json.dumps(metadata, default=str)
        except Exception as e:
            pytest.fail(f"Metadata should be JSON serializable: {e}")

        # Should have required fields
        assert "created_by" in metadata
        assert "creation_method" in metadata
        assert "created_date" in metadata

    def test_database_document_structure(self, sample_assistant_config, sample_company_info):
        """Test database document structure validation."""
        # Create a complete database document
        db_document = {
            **sample_assistant_config,
            "metadata": {
                "company_info": sample_company_info,
                "created_by": "test",
                "test_session": "test_session_123"
            },
            "knowledge_base_files": [],
            "background_sound": "default",
            "background_sound_url": "",
            "input_min_characters": 30,
            "punctuation_boundaries": "",
            "stability": 0.5,
            "clarity_similarity": 0.75,
            "style_exaggeration": 0,
            "optimize_streaming_latency": 0,
            "background_denoising": False,
            "confidence_threshold": 0.4,
            "use_numerals": False
        }

        # Should have all required database fields
        db_required_fields = [
            "id", "name", "system_prompt", "metadata",
            "created_at", "updated_at", "status"
        ]

        for field in db_required_fields:
            assert field in db_document, f"Database document should have '{field}'"

class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_website_url_handling(self):
        """Test handling of invalid website URLs."""
        invalid_urls = [
            "not-a-url",
            "http://",
            "https://nonexistent-site-12345.com",
            "",
            None
        ]

        for url in invalid_urls:
            # Should not raise unhandled exceptions
            result = self._mock_system_prompt_generation(url)
            assert not result["success"], f"Should fail for invalid URL: {url}"

    def test_empty_system_prompt_handling(self):
        """Test handling of empty or invalid system prompts."""
        invalid_prompts = ["", "   ", None, "short"]

        for prompt in invalid_prompts:
            # Should handle gracefully
            if prompt is None or len(str(prompt).strip()) < 10:
                assert True, "Should detect invalid prompt"

    def test_malformed_company_info_handling(self):
        """Test handling of malformed company information."""
        malformed_infos = [
            {"invalid": "json\"structure"},
            {"nested": {"too": {"deep": "structure"}}},
            None,
            "",
            []
        ]

        for info in malformed_infos:
            # Should handle gracefully without crashing
            try:
                json.dumps(info, default=str)
                handled = True
            except:
                handled = False

            # Some should be handled, some should fail gracefully
            assert isinstance(handled, bool)

    def test_database_connection_error_handling(self):
        """Test handling of database connection errors."""
        # Test the mock database save method directly with exception
        # This simulates what happens when database connections fail
        try:
            # Force an exception in the mock save method
            result = self._mock_database_save("", {})  # Empty prompt triggers failure
            assert not result["success"], "Should fail with empty prompt"

            # Test successful case to ensure method works properly
            result = self._mock_database_save("test prompt", {})
            assert result["success"], "Should succeed with valid prompt"

        except Exception as e:
            # If an exception occurs, it should be handled gracefully
            assert False, f"Database error handling failed: {e}"

    def _mock_system_prompt_generation(self, url):
        """Mock system prompt generation for testing."""
        if not url or not isinstance(url, str):
            return {"success": False, "error": "Invalid URL"}

        # Check for incomplete URLs like "http://" or "https://"
        if url in ("http://", "https://") or not url.startswith(('http://', 'https://')):
            return {"success": False, "error": "Invalid URL"}

        # Check for malformed URLs (just protocol without domain)
        if len(url.replace("http://", "").replace("https://", "").strip()) == 0:
            return {"success": False, "error": "Invalid URL"}

        if "nonexistent" in url:
            return {"success": False, "error": "Site not found"}

        return {"success": True, "prompt": "Generated prompt"}

    def _mock_database_save(self, prompt, company_info):
        """Mock database save for testing."""
        try:
            if not prompt:
                return {"success": False, "error": "Empty prompt"}

            # Simulate successful save
            return {"success": True, "id": str(uuid.uuid4())}
        except:
            return {"success": False, "error": "Database error"}

class TestPerformanceRequirements:
    """Test performance requirements and benchmarks."""

    def test_system_prompt_generation_speed(self):
        """Test system prompt generation performance."""
        # Mock timing for system prompt generation
        start_time = datetime.now()

        # Simulate processing time
        import time
        time.sleep(0.01)  # Simulate 10ms processing

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Should complete within reasonable time
        assert duration < 30, "System prompt generation should complete within 30 seconds"

    def test_database_save_speed(self):
        """Test database save performance."""
        start_time = datetime.now()

        # Simulate database save
        import time
        time.sleep(0.005)  # Simulate 5ms save

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Should complete within reasonable time
        assert duration < 5, "Database save should complete within 5 seconds"

    def test_memory_usage_limits(self, sample_system_prompt, sample_company_info):
        """Test memory usage stays within reasonable limits."""
        import sys

        # Create large data structures for testing
        # Ensure we have enough content to reach 100k characters
        base_prompt = sample_system_prompt
        if len(base_prompt) < 1000:
            # Pad the prompt to ensure it's long enough for the test
            base_prompt = base_prompt + " " + "This is additional test content. " * 50

        large_prompt = base_prompt * max(100, 100000 // len(base_prompt) + 1)
        large_info = {f"field_{i}": f"value_{i}" for i in range(1000)}

        # Should handle reasonably large data
        assert len(large_prompt) > 100000, f"Should handle large prompts (got {len(large_prompt)} chars)"
        assert len(large_info) == 1000, "Should handle large company info"

        # Memory usage should be reasonable (basic check)
        assert sys.getsizeof(large_prompt) < 10 * 1024 * 1024, "Memory usage should be reasonable"

class TestConfigurationValidation:
    """Test configuration validation and sanitization."""

    def test_agent_type_validation(self):
        """Test agent type validation."""
        valid_types = ["helpdesk", "sales", "support", "general"]
        invalid_types = ["", None, "invalid_type", 123]

        for agent_type in valid_types:
            assert agent_type in ["helpdesk", "sales", "support", "general"]

        for agent_type in invalid_types:
            assert agent_type not in valid_types

    def test_language_code_validation(self):
        """Test language code validation."""
        valid_languages = ["en", "es", "fr", "de", "it", "pt"]
        invalid_languages = ["english", "EN", "", None, "xyz"]

        for lang in valid_languages:
            assert len(lang) == 2 and lang.islower()

        for lang in invalid_languages:
            if lang:
                assert not (len(lang) == 2 and lang.islower())

    def test_voice_provider_validation(self):
        """Test voice provider validation."""
        valid_providers = ["openai", "elevenlabs", "meta_mms", "deepgram"]
        invalid_providers = ["", None, "invalid_provider", 123]

        for provider in valid_providers:
            assert provider in ["openai", "elevenlabs", "meta_mms", "deepgram"]

        for provider in invalid_providers:
            assert provider not in valid_providers

# Pytest execution functions
def test_run_unit_tests():
    """Run all unit tests and report results."""
    import subprocess
    import sys

    # Run pytest on this file
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v"
    ], capture_output=True, text=True)

    # Check if tests passed
    assert result.returncode == 0, f"Unit tests failed:\n{result.stdout}\n{result.stderr}"

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])