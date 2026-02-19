import pytest

from apps.shared.speech.code_switch import (
    DEFAULT_TWI_VOCAB,
    detect_code_switch,
    segment_by_language,
    route_code_switched_text,
)


def test_detect_code_switch_mixed():
    text = "Mepɛ appointment for Friday anɔpa"
    assert detect_code_switch(text, DEFAULT_TWI_VOCAB)


def test_detect_code_switch_single_language():
    text = "Mepɛ anɔpa"
    assert not detect_code_switch(text, DEFAULT_TWI_VOCAB)


def test_detect_code_switch_empty():
    with pytest.raises(ValueError):
        detect_code_switch("", DEFAULT_TWI_VOCAB)


def test_segment_by_language_mixed():
    text = "Mepɛ appointment for Friday anɔpa"
    segments = segment_by_language(text, DEFAULT_TWI_VOCAB)
    assert segments == [
        ("Mepɛ", "twi"),
        ("appointment for Friday", "en"),
        ("anɔpa", "twi"),
    ]


def test_route_code_switched_text_translation_flags():
    text = "Mepɛ appointment for Friday anɔpa"
    routed = route_code_switched_text(text, "en", DEFAULT_TWI_VOCAB)
    assert routed == [
        ("Mepɛ", "twi", True),
        ("appointment for Friday", "en", False),
        ("anɔpa", "twi", True),
    ]
