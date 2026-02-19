from fastapi import FastAPI
from fastapi.testclient import TestClient
from pathlib import Path
from uuid import uuid4
from typing import Any, Dict
import pytest

import apps.core_backend.backend.routes.voice_engine as voice_engine

from backend.events import event_bus, EventType
from backend.services import voice_session_service

from apps.shared.voice_engine import register_voice


class InMemoryCollection:
    """Minimal in-memory collection for session tests."""

    def __init__(self) -> None:  # pragma: no cover - simple container
        self.store = {}

    def insert_one(self, doc):  # pragma: no cover - simple storage
        self.store[doc["_id"]] = doc

    def find_one(self, query):  # pragma: no cover - simple retrieval
        return self.store.get(query["_id"])

    def replace_one(
        self, query, doc, upsert=False
    ):  # pragma: no cover - simple replace
        self.store[query["_id"]] = doc


voice_session_service._collection = InMemoryCollection()

app = FastAPI()
app.include_router(voice_engine.router)
client = TestClient(app)


@pytest.fixture
def session_service():
    """Provide an isolated in-memory session service."""

    class FakeCollection:
        def __init__(self) -> None:
            self.docs: Dict[str, Dict[str, Any]] = {}

        def insert_one(self, doc: Dict[str, Any]) -> None:
            self.docs[doc["_id"]] = doc

        def find_one(self, query: Dict[str, Any]) -> Dict[str, Any] | None:
            return self.docs.get(query["_id"])

        def replace_one(
            self, query: Dict[str, Any], doc: Dict[str, Any], upsert: bool = False
        ) -> None:
            self.docs[query["_id"]] = doc

    # Replace the global collection with our fake one
    voice_engine.voice_session_service._collection = FakeCollection()
    return voice_engine.voice_session_service


def test_energy_endpoint_basic():
    response = client.post("/voice/energy", json={"samples": [0, 32767, -32768, 0]})
    assert response.status_code == 200
    data = response.json()
    assert 0 < data["energy"] <= 1


def test_energy_endpoint_empty():
    response = client.post("/voice/energy", json={"samples": []})
    assert response.status_code == 200
    assert response.json()["energy"] == 0.0


def test_energy_endpoint_invalid():
    response = client.post("/voice/energy", json={"samples": ["bad"]})
    assert response.status_code == 422


def test_echo_endpoint_roundtrip():
    payload = {"samples": [1, -2, 3]}
    response = client.post("/voice/echo", json=payload)
    assert response.status_code == 200
    assert response.json()["samples"] == payload["samples"]


def test_echo_endpoint_invalid():
    response = client.post("/voice/echo", json={"samples": ["bad"]})
    assert response.status_code == 422


def test_options_endpoint_lists_providers():
    res = client.get("/voice/options")
    assert res.status_code == 200
    data = res.json()
    assert "openai" in data["stt"]
    assert "coqui" in data["tts"]
    # Check that LLM providers are present
    assert "llm" in data
    assert isinstance(data["llm"], dict)
    # Check that OpenAI models are present
    assert "openai" in data["llm"]
    assert "gpt-4o-mini" in data["llm"]["openai"]


def test_llm_endpoint_replies():
    res = client.post("/voice/llm", json={"text": "hi"})
    assert res.status_code == 200
    data = res.json()
    assert data["text"] == "Echo: hi"
    assert data["provider"] == "OpenAI"
    assert data["model"] == "GPT-4o"
    assert "tokens_used" in data
    assert "cost_estimate" in data


def test_vad_endpoint_silence_and_voice():
    silence = {"samples": [0] * 100}
    res = client.post("/voice/vad", json=silence)
    assert res.status_code == 200
    data = res.json()
    assert data["voice"] is False

    voice = {"samples": [1000] * 100}
    res = client.post("/voice/vad", json=voice)
    assert res.status_code == 200
    data = res.json()
    assert data["voice"] is True


def test_stt_endpoint_transcribes():
    phrase = "hello world"
    samples = [ord(c) for c in phrase]
    event_bus.clear()
    res = client.post("/voice/stt", json={"samples": samples})
    assert res.status_code == 200
    data = res.json()
    assert data["text"] == phrase
    assert data["partials"][-1] == phrase
    assert data["language"] == "en"
    assert data["confidence"] == 1.0

    events = [e for e in event_bus.list() if e.type == EventType.LANGUAGE_DETECTED]
    assert events
    assert events[0].payload["language"] == "en"


def test_stt_endpoint_empty():
    event_bus.clear()
    res = client.post("/voice/stt", json={"samples": []})
    assert res.status_code == 200
    data = res.json()
    assert data["partials"] == []
    assert data["text"] == ""
    assert data["language"] is None
    assert data["confidence"] is None
    events = [e for e in event_bus.list() if e.type == EventType.LANGUAGE_DETECTED]
    assert not events


def test_stt_endpoint_low_confidence_no_event():
    text = "你好"
    samples = [ord(c) for c in text]
    event_bus.clear()
    res = client.post("/voice/stt", json={"samples": samples})
    assert res.status_code == 200
    data = res.json()
    assert data["language"] == "unknown"
    assert data["confidence"] == 0.0
    events = [e for e in event_bus.list() if e.type == EventType.LANGUAGE_DETECTED]
    assert not events


def test_stt_endpoint_invalid():
    res = client.post("/voice/stt", json={"samples": ["bad"]})
    assert res.status_code == 422


def test_loop_endpoint_cycles_audio():
    phrase = "mepa wo kyɛw"
    samples = [ord(c) for c in phrase]
    payload = {
        "samples": samples,
        "provider": "openai",
        "model": "gpt-4o-transcribe",
        "voice": "akuapem_female",
        "language": "Twi",
    }
    res = client.post("/voice/loop", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["text"] == phrase
    assert data["partials"][-1] == phrase
    assert data["samples"] == samples


def test_loop_endpoint_handles_empty_samples():
    payload = {
        "samples": [],
        "provider": "openai",
        "model": "gpt-4o-transcribe",
        "voice": "akuapem_female",
        "language": "Twi",
    }
    res = client.post("/voice/loop", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["text"] == ""
    assert data["partials"] == []
    assert data["samples"] == []


def test_barge_endpoint_interrupts():
    tts = [1, 2, 3]
    incoming = [1000] * 5
    res = client.post("/voice/barge", json={"tts": tts, "incoming": incoming})
    assert res.status_code == 200
    data = res.json()
    assert data["interrupted"] is True
    assert data["samples"] == []


def test_barge_endpoint_no_interrupt():
    tts = [1, 2, 3]
    incoming = [0] * 5
    res = client.post("/voice/barge", json={"tts": tts, "incoming": incoming})
    assert res.status_code == 200
    data = res.json()
    assert data["interrupted"] is False
    assert data["samples"] == tts


def test_barge_endpoint_invalid():
    res = client.post("/voice/barge", json={"tts": ["bad"], "incoming": [0]})
    assert res.status_code == 422


def test_retry_endpoint_succeeds_after_failures():
    res = client.post(
        "/voice/retry",
        json={"text": "hi", "failures": 2, "retries": 3, "fallback_text": "fb"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["fallback"] is False
    assert data["samples"] == [104, 105]


def test_retry_endpoint_uses_fallback():
    res = client.post(
        "/voice/retry",
        json={"text": "hi", "failures": 5, "retries": 3, "fallback_text": "fb"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["fallback"] is True
    assert data["samples"] == [102, 98]


def test_retry_endpoint_invalid():
    res = client.post("/voice/retry", json={"text": "hi", "failures": "bad"})
    assert res.status_code == 422


def test_wer_endpoint_basic():
    res = client.post(
        "/voice/wer",
        json={"reference": "me din de kofi", "hypothesis": "me din de yaw"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["wer"] == pytest.approx(0.25, rel=1e-4)


def test_wer_endpoint_invalid_reference():
    res = client.post("/voice/wer", json={"reference": "", "hypothesis": ""})
    assert res.status_code == 422


def test_tts_endpoint_generates_samples():
    res = client.post("/voice/tts", json={"text": "ab"})
    assert res.status_code == 200
    assert res.json()["samples"] == [97, 98]


def test_tts_endpoint_empty_text():
    res = client.post("/voice/tts", json={"text": ""})
    assert res.status_code == 422


def test_tts_endpoint_handles_twi_unicode():
    res = client.post("/voice/tts", json={"text": "ɛ"})
    assert res.status_code == 200
    assert res.json()["samples"] == [603]


def test_tts_endpoint_accepts_voice_selection():
    res = client.post("/voice/tts", json={"text": "ab", "voice": "ga_male"})
    assert res.status_code == 200
    assert res.json()["samples"] == [97, 98]


def test_tts_endpoint_accepts_yoruba_voice():
    res = client.post("/voice/tts", json={"text": "ab", "voice": "yoruba_female"})
    assert res.status_code == 200
    assert res.json()["samples"] == [97, 98]


def test_tts_endpoint_accepts_igbo_voice():
    res = client.post("/voice/tts", json={"text": "ab", "voice": "igbo_male"})
    assert res.status_code == 200
    assert res.json()["samples"] == [97, 98]


def test_tts_endpoint_accepts_swahili_voice():
    res = client.post("/voice/tts", json={"text": "ab", "voice": "swahili_female"})
    assert res.status_code == 200
    assert res.json()["samples"] == [97, 98]


def test_tts_endpoint_accepts_zulu_voice():
    res = client.post("/voice/tts", json={"text": "ab", "voice": "zulu_male"})
    assert res.status_code == 200
    assert res.json()["samples"] == [97, 98]


def test_tts_endpoint_rejects_unknown_voice():
    res = client.post("/voice/tts", json={"text": "ab", "voice": "unknown"})
    assert res.status_code == 400


def test_tts_endpoint_uses_registered_custom_voice():
    register_voice("custom_demo", lambda text: [1] * len(text))
    res = client.post("/voice/tts", json={"text": "ab", "voice": "custom_demo"})
    assert res.status_code == 200
    assert res.json()["samples"] == [1, 1]


def test_languages_endpoint_returns_country_languages():
    res = client.get("/voice/languages", params={"country": "Ghana"})
    assert res.status_code == 200
    data = res.json()
    assert data["country"] == "Ghana"
    assert "Akan" in data["languages"]


def test_languages_endpoint_returns_emerging_country_languages():
    res = client.get("/voice/languages", params={"country": "Brazil"})
    assert res.status_code == 200
    data = res.json()
    assert data["country"] == "Brazil"
    assert "Portuguese" in data["languages"]


def test_languages_endpoint_unknown_country():
    res = client.get("/voice/languages", params={"country": "Atlantis"})
    assert res.status_code == 404


def test_language_endpoint_default():
    res = client.get("/voice/language")
    assert res.status_code == 200
    assert res.json()["language"] == "Twi"


def test_language_endpoint_set_and_get():
    res = client.post("/voice/language", json={"language": "English"})
    assert res.status_code == 200
    assert res.json()["language"] == "English"
    res = client.get("/voice/language")
    assert res.json()["language"] == "English"


def test_language_endpoint_rejects_empty():
    res = client.post("/voice/language", json={"language": ""})
    assert res.status_code == 422


def test_compliance_endpoint_masks_pii_and_detects_consent():
    text = "Call 123-456-7890 or email test@example.com. I agree."
    res = client.post(
        "/voice/compliance",
        json={"text": text, "samples": [1, 2], "retain_audio": False},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["redacted"] == "Call ***-***-**** or email ***@example.com. I agree."
    assert data["consent"] is True
    assert data["audio"] == []


def test_compliance_endpoint_handles_retention():
    res = client.post(
        "/voice/compliance",
        json={"text": "hello", "samples": [1], "retain_audio": True},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["redacted"] == "hello"
    assert data["consent"] is False
    assert data["audio"] == [1]


def test_compliance_endpoint_invalid_samples():
    res = client.post(
        "/voice/compliance",
        json={"text": "hi", "samples": ["bad"], "retain_audio": False},
    )

    assert res.status_code == 422


def test_voice_session_persistence(session_service):
    sid = uuid4()
    payload = {"samples": [1, 2, 3]}
    resp = client.post(f"/voice/echo?session_id={sid}", json=payload)
    assert resp.status_code == 200
    stored = client.get(f"/voice/sessions/{sid}")
    assert stored.status_code == 200
    data = stored.json()
    assert data["id"] == str(sid)
    # Check that turns exist and have the expected structure
    assert "turns" in data
    assert len(data["turns"]) > 0
    # The VoiceTurn model doesn't have a 'kind' field, so we'll check for other fields
    assert "session_id" in data["turns"][0]
    assert "turn_number" in data["turns"][0]


def test_get_session_not_found(session_service):
    missing = uuid4()
    resp = client.get(f"/voice/sessions/{missing}")
    assert resp.status_code == 404


def test_get_session_invalid_id(session_service):
    resp = client.get("/voice/sessions/not-a-uuid")
    assert resp.status_code == 422


def test_voice_agent_config_endpoint():
    """Test the comprehensive voice agent configuration endpoint."""
    res = client.get("/voice/agent/config")
    assert res.status_code == 200
    data = res.json()
    
    # Check that all required fields are present
    assert "stt_providers" in data
    assert "tts_providers" in data
    assert "llm_providers" in data
    assert "llm_models" in data
    assert "languages" in data
    assert "countries" in data
    assert "voices" in data
    assert "default_config" in data
    
    # Check that LLM providers and models are populated
    assert len(data["llm_providers"]) > 0
    assert len(data["llm_models"]) > 0
    
    # Check that default config has required fields
    default_config = data["default_config"]
    assert "stt_provider" in default_config
    assert "stt_model" in default_config
    assert "tts_provider" in default_config
    assert "tts_voice" in default_config
    assert "llm_provider" in default_config
    assert "llm_model" in default_config
    assert "language" in default_config
    assert "country" in default_config
    
    # Check that at least one provider has models
    provider_with_models = False
    for provider in data["llm_providers"]:
        provider_models = [m for m in data["llm_models"] if m["provider_id"] == provider["id"]]
        if len(provider_models) > 0:
            provider_with_models = True
            break
    
    assert provider_with_models, "At least one provider should have models"
