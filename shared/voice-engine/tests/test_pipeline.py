
from datetime import datetime, timedelta
from pathlib import Path
import sys

from collections import deque
import datetime
from datetime import timedelta


import numpy as np
import pytest

sys.path.append(str(Path(__file__).resolve().parents[4]))
from apps.shared.speech import real_time_processor
from apps.shared.speech.real_time_processor import (
    RealTimeSpeechProcessor,
    SpeechEventType,
    VoiceActivityResult,
)


@pytest.fixture(autouse=True)
def patch_dependencies(monkeypatch):
    """Ensure optional dependencies are marked available for tests."""
    monkeypatch.setattr(real_time_processor, "AUDIO_AVAILABLE", True)
    monkeypatch.setattr(real_time_processor, "AI_AVAILABLE", False)


@pytest.mark.asyncio
async def test_detect_voice_activity_high_energy():
    """High-energy audio should be detected as speech."""
    processor = RealTimeSpeechProcessor({"vad_threshold": 0.5, "sample_rate": 16000})
    await processor.start_call_processing("call_high")
    audio = (np.ones(16000, dtype=np.float32) * 1.0).tobytes()

    events = await processor.process_audio_chunk("call_high", audio)

    assert any(ev.event_type == SpeechEventType.SPEECH_START for ev in events)


@pytest.mark.asyncio
async def test_detect_voice_activity_low_energy():
    """Low-energy audio should not trigger speech detection."""
    processor = RealTimeSpeechProcessor({"vad_threshold": 0.5, "sample_rate": 16000})
    await processor.start_call_processing("call_low")
    audio = np.zeros(16000, dtype=np.float32).tobytes()

    events = await processor.process_audio_chunk("call_low", audio)

    assert all(ev.event_type != SpeechEventType.SPEECH_START for ev in events)


@pytest.mark.asyncio
async def test_hysteresis_short_speech_no_event():
    """Speech shorter than the minimum duration should be ignored."""
    processor = RealTimeSpeechProcessor({"vad_threshold": 0.5, "sample_rate": 16000})
    await processor.start_call_processing("call_edge")
    call_state = processor.active_calls["call_edge"]

    vad_result = VoiceActivityResult(
        is_speech=False,
        confidence=1.0,
        energy_level=0.1,
        duration_ms=50,
        timestamp=datetime.datetime.now(datetime.UTC),
    )
    call_state["vad_state"]["is_speaking"] = True
    call_state["vad_state"]["speech_start_time"] = vad_result.timestamp - timedelta(
        milliseconds=50
    )

    events = await processor._process_vad_result("call_edge", vad_result, call_state)

    assert events == []


@pytest.mark.asyncio
async def test_pipeline_routing_sequence():
    """Pipeline should route start and end events sequentially."""
    processor = RealTimeSpeechProcessor({"vad_threshold": 0.5, "sample_rate": 16000})
    await processor.start_call_processing("call_pipe")
    call_state = processor.active_calls["call_pipe"]

    start_result = VoiceActivityResult(
        is_speech=True,
        confidence=1.0,
        energy_level=0.6,
        duration_ms=100,
        timestamp=datetime.datetime.now(datetime.UTC),
    )
    end_result = VoiceActivityResult(
        is_speech=False,
        confidence=1.0,
        energy_level=0.0,
        duration_ms=100,
        timestamp=start_result.timestamp + timedelta(seconds=1),
    )

    events = []
    events.extend(
        await processor._process_vad_result("call_pipe", start_result, call_state)
    )
    events.extend(
        await processor._process_vad_result("call_pipe", end_result, call_state)
    )

    assert [e.event_type for e in events] == [
        SpeechEventType.SPEECH_START,
        SpeechEventType.SPEECH_END,
    ]
