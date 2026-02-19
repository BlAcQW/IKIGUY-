"""
HTTP Header Utilities

Provides functions for safely decoding header values.
HTTP headers must only contain ISO-8859-1 (Latin-1) characters.
This utility uses base64 decoding to handle encoded organization IDs.
"""

import base64
import logging

logger = logging.getLogger(__name__)


def is_base64_encoded(value: str) -> bool:
    """
    Check if a string is valid base64-encoded.

    Args:
        value: String to validate

    Returns:
        bool: True if the string is valid base64
    """
    if not value or not value.strip():
        return False

    try:
        # Try to decode - if it succeeds, it's likely base64
        base64.b64decode(value, validate=True)
        return True
    except Exception:
        return False


def decode_organization_id(encoded_value: str | None) -> str | None:
    """
    Decode organization ID from HTTP header.

    Supports both base64-encoded and plain values for backward compatibility.
    If the value is base64-encoded, it will be decoded. If decoding fails or
    the value is not encoded, the original value is returned.

    This ensures backward compatibility during the transition period when
    some clients may send plain organization IDs and others send encoded ones.

    Args:
        encoded_value: Organization ID from X-Organization-ID header

    Returns:
        str | None: Decoded organization ID, or original value if not encoded,
                    or None if input is None/empty

    Example:
        >>> decode_organization_id("NjU3YjFhMmNkZWY0NTY3ODkw")
        "657b1a2cdef4567890"

        >>> decode_organization_id("plain-org-id")  # Not encoded
        "plain-org-id"

        >>> decode_organization_id(None)
        None
    """
    # Handle null/undefined/empty
    if not encoded_value or not encoded_value.strip():
        return None

    # Try to decode from base64
    try:
        if is_base64_encoded(encoded_value):
            decoded_bytes = base64.b64decode(encoded_value, validate=True)
            decoded_str = decoded_bytes.decode('utf-8')
            logger.debug(f"Decoded organization ID from base64: {encoded_value[:10]}... -> {decoded_str}")
            return decoded_str
        else:
            # Not base64-encoded, return as-is (backward compatibility)
            logger.debug(f"Organization ID not base64-encoded, using as-is: {encoded_value}")
            return encoded_value
    except Exception as e:
        # If decoding fails, assume it's not encoded (backward compatibility)
        logger.warning(f"Failed to decode organization ID, using as-is: {encoded_value}. Error: {e}")
        return encoded_value
