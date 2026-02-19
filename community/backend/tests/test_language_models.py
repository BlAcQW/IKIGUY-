"""
Unit tests for language models in African Language Community Platform.
"""

import pytest
from pydantic import ValidationError
from bson import ObjectId

from models.language_models import LanguageFamily, LanguageSubfamily, Language, PyObjectId


class TestPyObjectId:
    """Test custom ObjectId validation."""

    def test_valid_objectid(self):
        """Test valid ObjectId creation."""
        obj_id = ObjectId()
        py_obj_id = PyObjectId.validate(str(obj_id))
        assert py_obj_id == obj_id

    def test_invalid_objectid(self):
        """Test invalid ObjectId raises error."""
        with pytest.raises(ValueError, match="Invalid ObjectId"):
            PyObjectId.validate("invalid_id")

    def test_objectid_from_string(self):
        """Test ObjectId creation from string."""
        obj_id_str = "507f1f77bcf86cd799439011"
        py_obj_id = PyObjectId.validate(obj_id_str)
        assert str(py_obj_id) == obj_id_str


class TestLanguageFamily:
    """Test LanguageFamily model validation."""

    def test_valid_language_family(self):
        """Test valid language family creation."""
        family_data = {
            "name": "Niger-Congo",
            "display_name": "Niger-Congo Languages",
            "description": "The largest language family in Africa",
            "geographic_region": ["West Africa", "Central Africa"],
            "subfamilies": ["Kwa", "Bantu", "Yoruboid"],
            "shared_features": {
                "noun_classes": True,
                "tone_language": True
            },
            "speaker_count_estimate": 700000000
        }

        family = LanguageFamily(**family_data)
        assert family.name == "Niger-Congo"
        assert family.display_name == "Niger-Congo Languages"
        assert len(family.subfamilies) == 3
        assert family.shared_features["noun_classes"] is True

    def test_required_fields(self):
        """Test that required fields are validated."""
        with pytest.raises(ValidationError):
            LanguageFamily()

        with pytest.raises(ValidationError):
            LanguageFamily(name="Niger-Congo")

    def test_optional_fields(self):
        """Test that optional fields have defaults."""
        from datetime import datetime

        minimal_family = LanguageFamily(
            name="test-family",
            display_name="Test Family",
            description="Test description",
            geographic_region=["Test Region"],
            subfamilies=[],
            shared_features={}
        )

        assert minimal_family.speaker_count_estimate is None
        # created_at is a datetime field with default_factory=datetime.utcnow
        assert isinstance(minimal_family.created_at, datetime)


class TestLanguageSubfamily:
    """Test LanguageSubfamily model validation."""

    def test_valid_subfamily(self):
        """Test valid subfamily creation."""
        subfamily_data = {
            "family_id": "507f1f77bcf86cd799439011",
            "name": "Kwa",
            "display_name": "Kwa Languages",
            "description": "A major branch of Niger-Congo",
            "geographic_region": ["Ghana", "Togo"],
            "languages": ["twi", "ga", "ewe"],
            "shared_features": {
                "serial_verbs": True,
                "tone_terracing": True
            },
            "transfer_learning_efficiency": {
                "twi_to_ga": 0.85,
                "ga_to_ewe": 0.72
            }
        }

        subfamily = LanguageSubfamily(**subfamily_data)
        assert subfamily.name == "Kwa"
        assert len(subfamily.languages) == 3
        assert subfamily.transfer_learning_efficiency["twi_to_ga"] == 0.85

    def test_transfer_learning_scores(self):
        """Test transfer learning efficiency validation."""
        subfamily_data = {
            "family_id": "507f1f77bcf86cd799439011",
            "name": "test",
            "display_name": "Test",
            "description": "Test",
            "geographic_region": ["Test"],
            "languages": ["lang1", "lang2"],
            "shared_features": {},
            "transfer_learning_efficiency": {
                "invalid_score": 1.5  # Should be <= 1.0
            }
        }

        # This should still create the model (validation is logical, not strict)
        subfamily = LanguageSubfamily(**subfamily_data)
        assert subfamily.transfer_learning_efficiency["invalid_score"] == 1.5


class TestLanguage:
    """Test Language model validation."""

    def test_valid_language(self):
        """Test valid language creation."""
        language_data = {
            "subfamily_id": "507f1f77bcf86cd799439011",
            "code": "twi",
            "name": "Twi (Akan)",
            "native_name": "Twi",
            "alternative_names": ["Akan", "Asante Twi"],
            "countries": ["Ghana"],
            "regions": ["Ashanti Region", "Brong-Ahafo Region"],
            "speaker_count": 9000000,
            "linguistic_features": {
                "word_order": "SVO",
                "tone_levels": 2
            },
            "phonetic_inventory": {
                "vowels": 10,
                "consonants": 20
            },
            "tonal_system": {
                "levels": ["high", "low"],
                "contours": ["falling", "rising"]
            },
            "writing_systems": ["Latin", "Adinkra"],
            "cultural_context": {
                "primary_use": "daily_communication",
                "ceremonial_use": True
            },
            "dialects": ["Asante", "Akuapem", "Fante"],
            "data_tier": "tier-1-validated",
            "voice_support_level": "full",
            "active_contributors": 156
        }

        language = Language(**language_data)
        assert language.code == "twi"
        assert language.name == "Twi (Akan)"
        assert language.speaker_count == 9000000
        assert language.data_tier == "tier-1-validated"
        assert len(language.dialects) == 3

    def test_language_code_validation(self):
        """Test language code format."""
        # Valid language codes should be accepted
        valid_language = Language(
            subfamily_id="507f1f77bcf86cd799439011",
            code="twi",
            name="Twi",
            native_name="Twi",
            alternative_names=[],
            countries=["Ghana"],
            regions=["Ashanti"],
            linguistic_features={},
            phonetic_inventory={},
            writing_systems=["Latin"],
            cultural_context={},
            dialects=[],
            data_tier="tier-1-validated",
            voice_support_level="basic",
            active_contributors=0
        )
        assert valid_language.code == "twi"

    def test_data_tier_values(self):
        """Test data tier validation."""
        language_data = {
            "subfamily_id": "507f1f77bcf86cd799439011",
            "code": "test",
            "name": "Test Language",
            "native_name": "Test",
            "alternative_names": [],
            "countries": ["Test Country"],
            "regions": ["Test Region"],
            "linguistic_features": {},
            "phonetic_inventory": {},
            "writing_systems": ["Latin"],
            "cultural_context": {},
            "dialects": [],
            "voice_support_level": "basic",
            "active_contributors": 0
        }

        # Test valid tiers
        for tier in ["tier-1-validated", "tier-2-reviewed", "tier-3-submitted"]:
            lang = Language(**{**language_data, "data_tier": tier})
            assert lang.data_tier == tier

    def test_voice_support_levels(self):
        """Test voice support level validation."""
        language_data = {
            "subfamily_id": "507f1f77bcf86cd799439011",
            "code": "test",
            "name": "Test Language",
            "native_name": "Test",
            "alternative_names": [],
            "countries": ["Test Country"],
            "regions": ["Test Region"],
            "linguistic_features": {},
            "phonetic_inventory": {},
            "writing_systems": ["Latin"],
            "cultural_context": {},
            "dialects": [],
            "data_tier": "tier-1-validated",
            "active_contributors": 0
        }

        # Test valid voice support levels
        for level in ["none", "basic", "intermediate", "full"]:
            lang = Language(**{**language_data, "voice_support_level": level})
            assert lang.voice_support_level == level

    def test_required_language_fields(self):
        """Test language required fields validation."""
        with pytest.raises(ValidationError):
            Language()

        # Missing subfamily_id
        with pytest.raises(ValidationError):
            Language(
                code="twi",
                name="Twi",
                native_name="Twi"
            )