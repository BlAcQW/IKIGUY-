"""
Phone number normalization utilities for ChurchFlow.

This module provides utilities for normalizing phone numbers to handle
various input formats and ensure consistent database lookups.
"""

import re
from typing import List


def normalize_phone_number(phone: str) -> List[str]:
    """
    Generate possible phone number formats for lookup.

    Handles various phone number formats including:
    - International format: +233244123456
    - National format: 0244123456
    - Without prefix: 244123456

    Args:
        phone: Input phone number in any format

    Returns:
        List of normalized formats to search in database

    Examples:
        >>> normalize_phone_number("+233244123456")
        ['+233244123456', '0244123456', '244123456']

        >>> normalize_phone_number("0244123456")
        ['0244123456', '+233244123456', '244123456']

        >>> normalize_phone_number("244123456")
        ['244123456', '+233244123456', '0244123456']
    """
    if not phone:
        return []

    # Remove all non-digit characters except leading +
    cleaned = re.sub(r'[^\d+]', '', phone)

    if not cleaned:
        return []

    # Remove + sign for processing
    digits_only = cleaned.lstrip('+')

    # Initialize result list with the original cleaned input
    formats = [cleaned]

    # Handle Ghana phone numbers (country code: 233)
    if digits_only.startswith('233'):
        # Extract the local number without country code
        local_number = digits_only[3:]

        # Add international format
        if not cleaned.startswith('+'):
            formats.append(f'+233{local_number}')

        # Add national format (0 + local number)
        if not local_number.startswith('0'):
            formats.append(f'0{local_number}')

        # Add local format without prefix
        formats.append(local_number)

    elif digits_only.startswith('0'):
        # National format (0244123456)
        local_number = digits_only[1:]  # Remove leading 0

        # Add national format
        if digits_only not in formats:
            formats.append(digits_only)

        # Add international format
        formats.append(f'+233{local_number}')

        # Add local format without prefix
        formats.append(local_number)

    else:
        # Assume it's a local number without prefix (244123456)
        # Add as-is
        if digits_only not in formats:
            formats.append(digits_only)

        # Add international format
        formats.append(f'+233{digits_only}')

        # Add national format
        formats.append(f'0{digits_only}')

    # Remove duplicates while preserving order
    seen = set()
    result = []
    for fmt in formats:
        if fmt not in seen:
            seen.add(fmt)
            result.append(fmt)

    return result


def validate_phone_number(phone: str) -> bool:
    """
    Validate if a phone number has a reasonable format.

    Args:
        phone: Phone number to validate

    Returns:
        True if phone number appears valid, False otherwise

    Examples:
        >>> validate_phone_number("+233244123456")
        True

        >>> validate_phone_number("0244123456")
        True

        >>> validate_phone_number("abc")
        False

        >>> validate_phone_number("123")
        False
    """
    if not phone:
        return False

    # Remove all non-digit characters except leading +
    cleaned = re.sub(r'[^\d+]', '', phone)

    # Remove + sign for digit counting
    digits_only = cleaned.lstrip('+')

    # Phone number should have at least 9 digits and at most 15 digits
    if len(digits_only) < 9 or len(digits_only) > 15:
        return False

    # Should contain only digits after removing +
    if not digits_only.isdigit():
        return False

    return True
