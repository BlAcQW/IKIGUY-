"""Utilities for detecting and handling code-switching in text."""
from __future__ import annotations

from typing import List, Optional, Sequence, Set, Tuple


DEFAULT_TWI_VOCAB: Set[str] = {
    "mepɛ",
    "anɔpa",
    "ɛha",
    "yẹn",
    "sɛn",
}


def _normalize_tokens(text: str) -> List[str]:
    """Split text into lowercase tokens.

    Args:
        text: Input text.

    Returns:
        List of lowercase tokens.
    """
    return [token.lower() for token in text.split()]


def detect_code_switch(text: str, twi_vocab: Optional[Sequence[str]] = None) -> bool:
    """Determine whether a string mixes Twi and English tokens.

    Args:
        text: Input text.
        twi_vocab: Optional collection of known Twi words.

    Returns:
        bool: ``True`` if both Twi and non-Twi tokens are present.

    Raises:
        ValueError: If ``text`` is empty.
    """
    if not text.strip():
        raise ValueError("text must not be empty")

    vocab: Set[str] = set(twi_vocab) if twi_vocab else DEFAULT_TWI_VOCAB
    tokens = _normalize_tokens(text)
    twi_count = sum(token in vocab for token in tokens)
    english_count = len(tokens) - twi_count
    return twi_count > 0 and english_count > 0


def segment_by_language(
    text: str, twi_vocab: Optional[Sequence[str]] = None
) -> List[Tuple[str, str]]:
    """Split text into consecutive language segments.

    Args:
        text: Input text.
        twi_vocab: Optional collection of known Twi words.

    Returns:
        List of ``(segment, language_code)`` tuples where ``language_code`` is
        ``"twi"`` or ``"en"``.

    Raises:
        ValueError: If ``text`` is empty.
    """
    if not text.strip():
        raise ValueError("text must not be empty")

    vocab: Set[str] = set(twi_vocab) if twi_vocab else DEFAULT_TWI_VOCAB
    tokens = text.split()
    segments: List[Tuple[str, str]] = []
    current_lang = None
    current_tokens: List[str] = []
    for token in tokens:
        lang = "twi" if token.lower() in vocab else "en"
        if current_lang is None:
            current_lang = lang
        if lang != current_lang:
            segments.append((" ".join(current_tokens), current_lang))
            current_tokens = [token]
            current_lang = lang
        else:
            current_tokens.append(token)
    if current_tokens:
        segments.append((" ".join(current_tokens), current_lang))
    return segments


def route_code_switched_text(
    text: str, target_lang: str, twi_vocab: Optional[Sequence[str]] = None
) -> List[Tuple[str, str, bool]]:
    """Route segments for translation based on target language.

    Args:
        text: Input text.
        target_lang: Desired output language, e.g., ``"en"`` or ``"twi"``.
        twi_vocab: Optional collection of known Twi words.

    Returns:
        List of tuples ``(segment, language_code, needs_translation)`` where
        ``needs_translation`` indicates whether the segment differs from
        ``target_lang``.

    Raises:
        ValueError: If ``text`` is empty.
    """
    segments = segment_by_language(text, twi_vocab)
    routed: List[Tuple[str, str, bool]] = []
    for segment, lang in segments:
        routed.append((segment, lang, lang != target_lang))
    return routed
