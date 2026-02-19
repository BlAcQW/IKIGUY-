"""Utility helpers for the voice engine frontend."""

from typing import Any, Dict


def is_auto_detect(message: Dict[str, Any]) -> bool:
    """Check if a WebSocket message enables auto-detect mode.

    Args:
        message (Dict[str, Any]): Parsed JSON message from the server.

    Returns:
        bool: True if auto-detect is active, False otherwise.
    """
    return message.get("type") == "language_changed" and bool(
        message.get("auto_detect")
    )
