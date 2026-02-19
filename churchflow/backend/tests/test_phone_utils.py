"""
Unit tests for phone number utilities.
"""

import pytest
from app.utils.phone import normalize_phone_number, validate_phone_number


class TestNormalizePhoneNumber:
    """Test cases for phone number normalization."""

    def test_international_format(self):
        """Test normalization of international format (+233)."""
        result = normalize_phone_number("+233244123456")
        assert "+233244123456" in result
        assert "0244123456" in result
        assert "244123456" in result
        assert len(result) >= 3

    def test_national_format(self):
        """Test normalization of national format (0244)."""
        result = normalize_phone_number("0244123456")
        assert "0244123456" in result
        assert "+233244123456" in result
        assert "244123456" in result
        assert len(result) >= 3

    def test_local_format(self):
        """Test normalization of local format (244)."""
        result = normalize_phone_number("244123456")
        assert "244123456" in result
        assert "+233244123456" in result
        assert "0244123456" in result
        assert len(result) >= 3

    def test_with_spaces(self):
        """Test phone number with spaces."""
        result = normalize_phone_number("+233 244 123 456")
        assert "+233244123456" in result
        assert "0244123456" in result
        assert "244123456" in result

    def test_with_dashes(self):
        """Test phone number with dashes."""
        result = normalize_phone_number("+233-244-123-456")
        assert "+233244123456" in result
        assert "0244123456" in result
        assert "244123456" in result

    def test_with_parentheses(self):
        """Test phone number with parentheses."""
        result = normalize_phone_number("+233 (244) 123-456")
        assert "+233244123456" in result
        assert "0244123456" in result

    def test_empty_string(self):
        """Test empty string input."""
        result = normalize_phone_number("")
        assert result == []

    def test_none_input(self):
        """Test None input."""
        result = normalize_phone_number(None)
        assert result == []

    def test_no_duplicates(self):
        """Test that result has no duplicates."""
        result = normalize_phone_number("+233244123456")
        assert len(result) == len(set(result))

    def test_different_ghana_numbers(self):
        """Test different Ghana mobile prefixes."""
        # Vodafone (020)
        result = normalize_phone_number("0201234567")
        assert "0201234567" in result
        assert "+233201234567" in result

        # MTN (024)
        result = normalize_phone_number("0241234567")
        assert "0241234567" in result
        assert "+233241234567" in result

        # AirtelTigo (027)
        result = normalize_phone_number("0271234567")
        assert "0271234567" in result
        assert "+233271234567" in result


class TestValidatePhoneNumber:
    """Test cases for phone number validation."""

    def test_valid_international_format(self):
        """Test valid international format."""
        assert validate_phone_number("+233244123456") is True

    def test_valid_national_format(self):
        """Test valid national format."""
        assert validate_phone_number("0244123456") is True

    def test_valid_local_format(self):
        """Test valid local format."""
        assert validate_phone_number("244123456") is True

    def test_valid_with_spaces(self):
        """Test valid phone with spaces."""
        assert validate_phone_number("+233 244 123 456") is True

    def test_valid_with_dashes(self):
        """Test valid phone with dashes."""
        assert validate_phone_number("+233-244-123-456") is True

    def test_too_short(self):
        """Test phone number that's too short."""
        assert validate_phone_number("123") is False
        assert validate_phone_number("12345") is False

    def test_too_long(self):
        """Test phone number that's too long."""
        assert validate_phone_number("1234567890123456") is False

    def test_alphabetic_characters(self):
        """Test phone number with letters."""
        assert validate_phone_number("abc") is False
        assert validate_phone_number("123abc456") is False

    def test_empty_string(self):
        """Test empty string."""
        assert validate_phone_number("") is False

    def test_none_input(self):
        """Test None input."""
        assert validate_phone_number(None) is False

    def test_special_characters_only(self):
        """Test only special characters."""
        assert validate_phone_number("---") is False
        assert validate_phone_number("+++") is False

    def test_minimum_valid_length(self):
        """Test minimum valid phone length (9 digits)."""
        assert validate_phone_number("123456789") is True

    def test_maximum_valid_length(self):
        """Test maximum valid phone length (15 digits)."""
        assert validate_phone_number("123456789012345") is True

    def test_edge_case_formats(self):
        """Test various edge case formats."""
        # Valid formats
        assert validate_phone_number("+1 234 567 8900") is True  # US format
        assert validate_phone_number("(020) 1234567") is True  # Parentheses

        # Invalid formats
        assert validate_phone_number("12-34") is False  # Too short after cleanup
