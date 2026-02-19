"""Knowledge base ingestion and search backed by MongoDB."""

from __future__ import annotations

import hashlib
from typing import List, Tuple
from uuid import UUID
from urllib.request import urlopen

from .mongo import get_collection
from .models import KbSource, KbChunk


def _chunk_text(text: str, size: int = 200) -> List[str]:
    """Split text into fixed-size chunks."""
    return [text[i : i + size] for i in range(0, len(text), size)]


def _embed(text: str) -> List[float]:
    """Generate a deterministic embedding vector for a chunk."""
    digest = hashlib.sha256(text.encode()).digest()
    return [int.from_bytes(digest[i : i + 8], "big") / 2**64 for i in range(0, 24, 8)]


def fetch_url(url: str) -> str:
    """Return the contents of a URL as text."""
    with urlopen(url) as resp:  # nosec - controlled ingestion
        return resp.read().decode("utf-8")


_sources = get_collection("kb_sources")
_chunks = get_collection("kb_chunks")


def _serialize_source(src: KbSource) -> dict:
    doc = src.model_dump()
    doc["_id"] = str(doc.pop("id"))
    doc["tenant_id"] = str(doc["tenant_id"])
    return doc


def _serialize_chunk(chunk: KbChunk) -> dict:
    doc = chunk.model_dump()
    doc["_id"] = str(doc.pop("id"))
    doc["source_id"] = str(doc["source_id"])
    return doc


def ingest(tenant_id: UUID, content: str, uri: str, source_type: str) -> Tuple[KbSource, int]:
    """Store content chunks and their embeddings."""
    source = KbSource(tenant_id=tenant_id, type=source_type, uri=uri, status="ready")
    _sources.insert_one(_serialize_source(source))

    chunks = _chunk_text(content)
    for chunk_text in chunks:
        emb = _embed(chunk_text)
        chunk = KbChunk(source_id=source.id, text=chunk_text, embedding=emb)
        _chunks.insert_one(_serialize_chunk(chunk))
    return source, len(chunks)


def _bm25(query: str, text: str) -> float:
    """Simple term-frequency score used to approximate BM25."""
    return sum(text.lower().count(term) for term in query.lower().split())


def _cross_score(query: str, text: str) -> float:
    """Deterministic cross-encoder-like score for reranking."""
    digest = hashlib.sha256(f"{query}|{text}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def search(tenant_id: UUID, query: str, top_k: int = 5) -> List[Tuple[KbChunk, float]]:
    """Return chunks ordered by hybrid score with cross-encoder rerank."""
    query_emb = _embed(query)
    src_ids = [str(s["_id"]) for s in _sources.find({"tenant_id": str(tenant_id)})]
    rows: List[KbChunk] = []
    for doc in _chunks.find({"source_id": {"$in": src_ids}}):
        doc["id"] = doc["_id"]
        rows.append(KbChunk.model_validate(doc))
    scored: List[Tuple[float, KbChunk]] = []
    for chunk in rows:
        bm25 = _bm25(query, chunk.text)
        vec = sum(a * b for a, b in zip(query_emb, chunk.embedding))
        scored.append((bm25 + vec, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]
    reranked = [
        (
            s + _cross_score(query, c.text),
            c,
        )
        for s, c in top
    ]
    reranked.sort(key=lambda x: x[0], reverse=True)
    return [(c, s) for s, c in reranked]


__all__ = ["fetch_url", "ingest", "search"]
