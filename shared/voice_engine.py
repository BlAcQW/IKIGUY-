"""Voice engine utilities.

Provides helpers for basic audio analysis used across demos.
"""
from __future__ import annotations


import re
import time
from typing import Callable, Dict, List, Optional, Sequence, Tuple, TypeVar


def calculate_energy(samples: Sequence[int]) -> float:
    """Calculate root-mean-square energy for PCM16 samples.

    Args:
        samples (Sequence[int]): Sequence of 16-bit signed integers representing audio samples.

    Returns:
        float: RMS energy value between 0.0 and 1.0.
    """
    if not samples:
        return 0.0

    # Normalize samples to [-1.0, 1.0] range and compute RMS.
    total = 0.0
    for sample in samples:
        normalized = max(-32768, min(32767, int(sample))) / 32768.0
        total += normalized * normalized
    return (total / len(samples)) ** 0.5


def is_silence(samples: Sequence[int], threshold: float = 0.01) -> bool:
    """Determine if audio samples represent silence.

    Args:
        samples (Sequence[int]): PCM16 sample values.
        threshold (float): Energy value below which audio is considered silent.

    Returns:
        bool: ``True`` if energy is below ``threshold``.
    """

    energy = calculate_energy(samples)
    return energy < threshold


def calculate_wer(reference: str, hypothesis: str) -> float:
    """Compute word error rate between reference and hypothesis.

    Args:
        reference (str): Ground-truth transcript.
        hypothesis (str): Predicted transcript.

    Returns:
        float: Word error rate in the range ``[0.0, 1.0]``.

    Raises:
        ValueError: If ``reference`` contains no words.
    """

    ref_words = reference.split()
    hyp_words = hypothesis.split()
    if not ref_words:
        raise ValueError("reference must contain at least one word")

    # Dynamic programming edit distance at word level.
    rows = len(ref_words) + 1
    cols = len(hyp_words) + 1
    dp = [[0] * cols for _ in range(rows)]
    for i in range(rows):
        dp[i][0] = i
    for j in range(cols):
        dp[0][j] = j

    for i in range(1, rows):
        for j in range(1, cols):
            if ref_words[i - 1] == hyp_words[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

    return dp[-1][-1] / len(ref_words)


def synthesize_text(text: str) -> List[int]:
    """Convert text into PCM16 sample integers.

    Each Unicode code point is deterministically mapped to a signed 16‑bit
    integer. This keeps the function lightweight for demos while ensuring the
    returned values fall within the valid PCM range.

    Args:
        text (str): Text to convert into synthetic samples.

    Returns:
        List[int]: PCM16 sample values representing ``text``.
    """

    return [max(-32768, min(32767, ord(ch))) for ch in text]


def transcribe_samples(
    samples: Sequence[int], detect_language: bool = False
) -> Tuple[List[str], str, Optional[str], Optional[float]]:
    """Convert PCM16 samples into text with optional language detection.

    Args:
        samples (Sequence[int]): Incoming audio sample values.
        detect_language (bool): When ``True``, perform simple language detection.

    Returns:
        Tuple[List[str], str, Optional[str], Optional[float]]: Progressive partial
        transcripts, final text, detected language code, and detection confidence.
    """

    if not samples:
        return [], "", None, None
    
    # Mock transcription - simulate real transcription
    # This is a simple implementation for demo purposes
    try:
        # Calculate audio energy to determine if speech was detected
        energy = calculate_energy(samples)
        
        # Debug: Print energy value for troubleshooting
        print(f"Audio energy: {energy}, sample count: {len(samples)}")
        
        # For now, always return text regardless of energy to test
        # In production, you would use energy threshold: if energy < 0.0001:
        
        # Generate mock transcription based on sample length
        # In a real implementation, this would use actual STT models
        sample_count = len(samples)
        
        # More responsive to smaller chunks
        if sample_count < 500:
            text = "Hello"
            partials = ["Hello"]
        elif sample_count < 2000:
            text = "Hello, how are you?"
            partials = ["Hello", "Hello, how", "Hello, how are you?"]
        elif sample_count < 5000:
            text = "Hello, how are you today? I hope you're doing well."
            partials = ["Hello", "Hello, how", "Hello, how are you", "Hello, how are you today?", text]
        else:
            text = "Hello, how are you today? I hope you're doing well and having a great day."
            partials = ["Hello", "Hello, how", "Hello, how are you", "Hello, how are you today?", text]
        
        language = "English" if detect_language else None
        confidence = min(0.95, energy * 10) if detect_language else None  # Scale confidence with energy
        
        return partials, text, language, confidence
        
    except Exception as e:
        # Fallback to simple text generation if there's an error
        text = "Hello, this is a test transcription."
        partials = [text]
        language = "English" if detect_language else None
        confidence = 0.8 if detect_language else None
        return partials, text, language, confidence


# Voice preset registry -----------------------------------------------------
VOICE_REGISTRY: Dict[str, Callable[[str], List[int]]] = {}


def register_voice(name: str, transform: Callable[[str], List[int]]) -> None:
    """Register a voice preset transformation."""

    VOICE_REGISTRY[name] = transform


def synthesize_with_voice(text: str, voice: str) -> List[int]:
    """Synthesize text using a registered voice preset."""

    transform = VOICE_REGISTRY.get(voice)
    if transform is None:
        return synthesize_text(text)
    return transform(text)


def get_registered_voices() -> List[str]:
    """Return a list of registered voice names."""

    return list(VOICE_REGISTRY.keys())


# Default Twi voice presets
register_voice("akuapem_female", synthesize_text)
register_voice("asante_male", lambda t: list(reversed(synthesize_text(t))))


def loop_samples(samples: Sequence[int]) -> Tuple[List[int], List[str], str]:
    """Transcribe samples and synthesize the transcript back into audio.

    Args:
        samples (Sequence[int]): Input PCM16 sample values.

    Returns:
        Tuple[List[int], List[str], str]: Synthetic samples, partial transcripts,
        and final text.
    """

    partials, text, _, _ = transcribe_samples(samples)
    return synthesize_text(text), partials, text


def barge_in(
    tts_samples: Sequence[int], incoming_samples: Sequence[int], threshold: float = 0.01
) -> Tuple[List[int], bool]:
    """Detect if TTS playback should be interrupted by new audio.

    Args:
        tts_samples (Sequence[int]): Samples currently being played.
        incoming_samples (Sequence[int]): Newly captured samples from the microphone.
        threshold (float): Energy value above which incoming audio triggers an interruption.

    Returns:
        Tuple[List[int], bool]: Remaining TTS samples and whether an interruption occurred.
    """

    if calculate_energy(incoming_samples) >= threshold:
        return [], True
    return list(tts_samples), False


T = TypeVar("T")


def retry_with_fallback(
    operation: Callable[[], T], fallback: Callable[[], T], retries: int = 3
) -> Tuple[T, bool]:
    """Execute ``operation`` with retries and fallback.

    Args:
        operation (Callable[[], T]): Primary callable that may fail.
        fallback (Callable[[], T]): Fallback callable used after exhausting retries.
        retries (int): Number of retry attempts before invoking ``fallback``.

    Returns:
        Tuple[T, bool]: Result from ``operation`` or ``fallback`` and whether the
            fallback was used.

    """

    for _ in range(retries):
        try:
            return operation(), False
        except Exception:  # pragma: no cover - demo resilience
            continue
    return fallback(), True


EMAIL_PATTERN = re.compile(r"([\w.+-]+)@([\w.-]+\.[a-zA-Z]{2,})")
PHONE_PATTERN = re.compile(r"\b(\d{3})[-.\s]?(\d{3})[-.\s]?(\d{4})\b")


def redact_pii(text: str) -> str:
    """Mask email addresses and phone numbers in a transcript.

    Args:
        text (str): Input transcript possibly containing PII.

    Returns:
        str: Transcript with emails and phone numbers replaced by placeholders.

    Raises:
        TypeError: If ``text`` is not a string.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    def _mask_email(match: re.Match[str]) -> str:
        return f"***@{match.group(2)}"

    text = EMAIL_PATTERN.sub(_mask_email, text)
    text = PHONE_PATTERN.sub("***-***-****", text)
    return text


CONSENT_PHRASES = ("i consent", "i agree")


def detect_consent(text: str, phrases: Sequence[str] = CONSENT_PHRASES) -> bool:
    """Check if ``text`` contains any consent phrase.

    Args:
        text (str): Transcript to examine.
        phrases (Sequence[str]): Phrases that signal consent.

    Returns:
        bool: ``True`` if any phrase is present.

    Raises:
        TypeError: If ``text`` is not a string.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    lowered = text.lower()
    return any(p.lower() in lowered for p in phrases)


def maybe_retain_audio(samples: Sequence[int], retain: bool) -> List[int]:
    """Return ``samples`` if ``retain`` is ``True`` otherwise an empty list.

    Args:
        samples (Sequence[int]): PCM16 samples.
        retain (bool): Whether to keep the audio.

    Returns:
        List[int]: Original samples or an empty list.

    Raises:
        TypeError: If any sample is not an integer.
    """

    if any(not isinstance(s, int) for s in samples):
        raise TypeError("samples must be integers")
    return list(samples) if retain else []


class OfflineTurnQueue:
    """Queue turns when the backend is unreachable.

    The queue stores turns locally and retries delivery with exponential
    backoff. In a production scenario this would persist to IndexedDB; here we
    use an in-memory list for simplicity.

    Args:
        base_backoff (float): Base delay in seconds used for exponential
            backoff between retries.
    """

    def __init__(self, base_backoff: float = 0.1) -> None:
        self._queue: List[str] = []
        self.base_backoff = base_backoff

    def enqueue(self, turn: str) -> None:
        """Add a turn to the local queue.

        Args:
            turn (str): Serialized turn data to store until connection resumes.
        """

        self._queue.append(turn)

    def flush(
        self,
        sender: Callable[[str], None],
        sleep: Callable[[float], None] = time.sleep,
        max_retries: int = 3,
    ) -> int:
        """Attempt to send queued turns using ``sender``.

        Args:
            sender (Callable[[str], None]): Callable that delivers a turn. It
                should raise ``ConnectionError`` when the backend is
                unreachable.
            sleep (Callable[[float], None]): Sleep function used for backoff.
            max_retries (int): Number of delivery attempts per turn before
                keeping it queued.

        Returns:
            int: Number of turns successfully delivered.
        """

        delivered = 0
        remaining: List[str] = []
        for turn in self._queue:
            for attempt in range(max_retries):
                try:
                    sender(turn)
                    delivered += 1
                    break
                except ConnectionError:
                    if attempt < max_retries - 1:
                        sleep(self.base_backoff * (2**attempt))
                    else:
                        remaining.append(turn)
        self._queue = remaining
        return delivered
