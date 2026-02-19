import pytest
import httpx
from apps.shared.voice_engine.backend.helpers import transcribe, synthesize, llm, detect_language


@pytest.mark.asyncio
async def test_transcribe_returns_text(monkeypatch):
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/voice/stt"
        return httpx.Response(200, json={"partials": ["hi"], "text": "hi", "language": "en"})

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport, base_url="http://test")
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: client)

    data = await transcribe([1, 2], "http://test")
    assert data["text"] == "hi"


@pytest.mark.asyncio
async def test_synthesize_returns_samples(monkeypatch):
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/voice/tts"
        return httpx.Response(200, json={"samples": [1, 2]})

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport, base_url="http://test")
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: client)

    samples = await synthesize("hi", "http://test")
    assert samples == [1, 2]


@pytest.mark.asyncio
async def test_llm_returns_reply(monkeypatch):
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/voice/llm"
        return httpx.Response(200, json={"reply": "ok"})

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport, base_url="http://test")
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: client)

    reply = await llm("hi", "http://test")
    assert reply == "ok"


@pytest.mark.asyncio
async def test_detect_language(monkeypatch):
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"partials": [], "text": "", "language": "en"})

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport, base_url="http://test")
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: client)

    lang = await detect_language([1], "http://test")
    assert lang == "en"
