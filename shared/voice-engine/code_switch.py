"""Utilities for basic code-switch handling between Twi and English.

This module provides heuristics to tag tokens in a sentence as either
Twi (``tw``) or English (``en``) and a helper to translate English spans
before recombining them.  It is intentionally lightweight so it can run
in low‑latency streaming pipelines.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List

TW_DIACRITICS = {"ɛ", "ɔ"}
EN_DAY_NAMES = {
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
}


def detect_token_language(token: str) -> str:
    """Return ``'tw'`` for Twi or proper nouns, otherwise ``'en'``.

    The heuristic checks for Twi diacritics first.  Capitalized tokens are
    treated as proper nouns and passed through without translation, except for
    common English day names which remain translatable.  The approach trades
    accuracy for speed; production systems should use ``fastText`` or another
    language‑ID model.
    """
    for ch in token.lower():
        if ch in TW_DIACRITICS:
            return "tw"
    if token in EN_DAY_NAMES:
        return "en"
    if token and token[0].isupper():
        return "tw"
    return "en"


@dataclass
class Token:
    text: str
    lang: str


def tag_sentence(sentence: str) -> List[Token]:
    """Split a sentence into whitespace tokens and tag their language."""
    return [Token(tok, detect_token_language(tok)) for tok in sentence.split()]


def translate_and_merge(
    tokens: List[Token], translate_en_to_tw: Callable[[str], str]
) -> str:
    """Translate contiguous English spans then recombine tokens.

    ``translate_en_to_tw`` is a callable so callers can plug in a real
    translation service.  Consecutive English tokens are joined before
    translation to preserve context and minimize service calls.  Tokens tagged
    as Twi are passed through unchanged.
    """
    translated: List[str] = []
    buffer: List[str] = []

    def flush_buffer() -> None:
        if buffer:
            phrase = " ".join(buffer)
            translated.append(translate_en_to_tw(phrase))
            buffer.clear()

    for token in tokens:
        if token.lang == "en":
            buffer.append(token.text)
        else:
            flush_buffer()
            translated.append(token.text)

    flush_buffer()
    return " ".join(translated)
