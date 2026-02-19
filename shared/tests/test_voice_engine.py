import math
import pytest

from apps.shared.voice_engine import (
    calculate_energy,
    calculate_wer,
    is_silence,
    synthesize_text,
    redact_pii,
    detect_consent,
    maybe_retain_audio,
    transcribe_samples,
    OfflineTurnQueue,
    register_voice,
    synthesize_with_voice,
    loop_samples,
)


def test_calculate_energy_basic():
    samples = [0, 32767, -32768, 0]
    energy = calculate_energy(samples)
    assert 0 < energy <= 1
    expected = math.sqrt((0**2 + 1**2 + 1**2 + 0**2) / 4)
    assert math.isclose(energy, expected, rel_tol=1e-4)


def test_calculate_energy_empty():
    assert calculate_energy([]) == 0.0


def test_calculate_energy_invalid_sample():
    # Sample outside 16-bit range should be clamped without error
    energy = calculate_energy([100000])
    assert 0 <= energy <= 1


def test_is_silence_true():
    samples = [0] * 100
    assert is_silence(samples)


def test_is_silence_false():
    samples = [1000] * 100
    assert not is_silence(samples)


def test_calculate_wer_matches():
    assert calculate_wer("me din de kofi", "me din de kofi") == 0.0


def test_calculate_wer_substitution():
    wer = calculate_wer("me din de kofi", "me din de yaw")
    assert math.isclose(wer, 0.25, rel_tol=1e-4)


def test_calculate_wer_empty_reference():
    try:
        calculate_wer("", "foo")
    except ValueError:
        return
    assert False, "Expected ValueError for empty reference"


def test_synthesize_text_basic():
    assert synthesize_text("ab") == [97, 98]


def test_synthesize_text_empty():
    assert synthesize_text("") == []


def test_synthesize_text_twi_characters():
    """Ensure Twi characters are converted to their code points."""
    assert synthesize_text("ɛda") == [603, 100, 97]


def test_synthesize_text_clamps_values():
    """Characters outside the PCM16 range should be clamped."""
    high_char = chr(70000)  # code point beyond 16-bit range
    assert synthesize_text(high_char) == [32767]


def test_redact_pii_masks_phone_and_email():
    text = "Call 123-456-7890 or email test@example.com"
    redacted = redact_pii(text)
    assert redacted == "Call ***-***-**** or email ***@example.com"


def test_redact_pii_no_pii():
    text = "hello world"
    assert redact_pii(text) == text


def test_redact_pii_invalid_type():
    with pytest.raises(TypeError):
        redact_pii(123)  # type: ignore[arg-type]


def test_detect_consent_true():
    text = "I agree to the terms"
    assert detect_consent(text) is True


def test_detect_consent_false():
    text = "No thanks"
    assert detect_consent(text) is False


def test_detect_consent_invalid_type():
    with pytest.raises(TypeError):
        detect_consent(123)  # type: ignore[arg-type]


def test_maybe_retain_audio_returns_samples():
    samples = [1, 2]
    assert maybe_retain_audio(samples, True) == samples


def test_maybe_retain_audio_drops_when_false():
    samples = [1, 2]
    assert maybe_retain_audio(samples, False) == []


def test_maybe_retain_audio_invalid_sample():
    with pytest.raises(TypeError):
        maybe_retain_audio([1, "a"], True)


def test_transcribe_samples_detect_language():
    samples = [ord(c) for c in "hello"]
    partials, text, lang, conf = transcribe_samples(samples, detect_language=True)
    assert partials[-1] == text == "hello"
    assert lang == "en"
    assert conf == 1.0


def test_transcribe_samples_unknown_language():
    samples = [ord(c) for c in "你好"]
    partials, text, lang, conf = transcribe_samples(samples, detect_language=True)
    assert text == "你好"
    assert lang == "unknown"
    assert conf == 0.0


def test_transcribe_samples_no_language_on_empty():
    partials, text, lang, conf = transcribe_samples([], detect_language=True)
    assert partials == []
    assert text == ""
    assert lang is None
    assert conf is None


def test_loop_samples_roundtrip():
    phrase = "mepa wo kyɛw"
    samples = [ord(c) for c in phrase]
    tts, partials, text = loop_samples(samples)
    assert tts == synthesize_text(phrase)
    assert partials[-1] == text == phrase


def test_offline_queue_flush_after_reconnect():
    queue = OfflineTurnQueue()
    queue.enqueue("turn1")
    queue.enqueue("turn2")

    calls = []
    online = [False]

    def sender(turn: str) -> None:
        if not online[0]:
            raise ConnectionError
        calls.append(turn)

    # First flush: backend down, nothing delivered
    assert queue.flush(sender, sleep=lambda _s: None, max_retries=1) == 0
    assert len(queue._queue) == 2

    # Second flush: backend up, both turns delivered
    online[0] = True
    assert queue.flush(sender, sleep=lambda _s: None) == 2
    assert len(queue._queue) == 0


def test_offline_queue_empty():
    queue = OfflineTurnQueue()
    assert queue.flush(lambda t: None, sleep=lambda _s: None) == 0


def test_offline_queue_persistent_failure():
    queue = OfflineTurnQueue()
    queue.enqueue("turn")

    def sender(_turn: str) -> None:
        raise ConnectionError

    assert queue.flush(sender, sleep=lambda _s: None, max_retries=2) == 0
    # Turn remains queued after failures
    assert len(queue._queue) == 1


def test_synthesize_with_voice_defaults_to_registered_voice():
    assert synthesize_with_voice("ab", "akuapem_female") == [97, 98]


def test_synthesize_with_voice_custom_registration():
    register_voice("custom_demo", lambda text: [1] * len(text))
    assert synthesize_with_voice("ab", "custom_demo") == [1, 1]
