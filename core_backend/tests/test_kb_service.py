import io
import sys
from pathlib import Path
from uuid import uuid4
from urllib.error import URLError

import mongomock
import pytest

from backend import kb


@pytest.fixture(autouse=True)
def mock_mongo(monkeypatch):
    """Provide isolated in-memory MongoDB collections."""
    client = mongomock.MongoClient()
    db = client["kasaai_core"]
    monkeypatch.setattr(kb, "_sources", db["kb_sources"])
    monkeypatch.setattr(kb, "_chunks", db["kb_chunks"])


def test_fetch_url_returns_text(monkeypatch):
    """fetch_url returns text content for a valid URL."""
    monkeypatch.setattr(kb, "urlopen", lambda url: io.BytesIO(b"hello"))
    assert kb.fetch_url("http://example.com") == "hello"


def test_fetch_url_invalid_url(monkeypatch):
    """fetch_url raises an error for an invalid URL."""

    def fake_urlopen(url: str):
        raise URLError("bad url")

    monkeypatch.setattr(kb, "urlopen", fake_urlopen)
    with pytest.raises(URLError):
        kb.fetch_url("http://invalid")


def test_ingest_stores_chunks():
    """ingest persists the source and its chunks."""
    tenant_id = uuid4()
    source, count = kb.ingest(tenant_id, "alpha beta", "http://src", "url")
    assert count == 1
    assert source.uri == "http://src"
    assert kb._sources.count_documents({}) == 1
    assert kb._chunks.count_documents({}) == 1


def test_search_returns_results():
    """search retrieves relevant chunks."""
    tenant_id = uuid4()
    kb.ingest(tenant_id, "alpha beta", "http://src", "url")
    results = kb.search(tenant_id, "alpha")
    assert len(results) == 1
    chunk, score = results[0]
    assert chunk.text == "alpha beta"
    assert isinstance(score, float)


def test_search_empty_results():
    """search returns an empty list when no matches exist."""
    tenant_id = uuid4()
    results = kb.search(tenant_id, "missing")
    assert results == []
