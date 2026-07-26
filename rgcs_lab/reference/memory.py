"""Provenance-memory benchmark reference — deterministic bag-of-tokens."""

from __future__ import annotations

import hashlib
import re
from collections import Counter


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


DEFAULT_CORPUS = [
    {
        "id": "doc-codec",
        "text": (
            "Federation Terra packet F5 Q22 S3 structural decode is exact "
            "arithmetic. Morton indices are hierarchical path registers."
        ),
    },
    {
        "id": "doc-golay",
        "text": (
            "Extended binary Golay G24 corrects up to three bit flips in a "
            "twenty-four bit codeword used as a transport wrapper."
        ),
    },
    {
        "id": "doc-energy",
        "text": (
            "Parametric resonance draws energy from the pump. Superelastic "
            "collisions release stored internal energy. No free vacuum power."
        ),
    },
    {
        "id": "doc-yellow",
        "text": (
            "Physical Earth projection remains underdetermined. Stonehenge "
            "decimal is a training equality until independent reproduction."
        ),
    },
]


def run_benchmark(
    query: str = "golay bit flips transport wrapper",
    corpus: list[dict] | None = None,
) -> dict:
    docs = corpus or DEFAULT_CORPUS
    q = Counter(_tokens(query))
    scored = []
    for doc in docs:
        t = Counter(_tokens(doc["text"]))
        overlap = sum(min(q[k], t[k]) for k in q)
        scored.append({
            "id": doc["id"],
            "score": float(overlap),
            "preview": doc["text"][:120],
        })
    scored.sort(key=lambda r: (-r["score"], r["id"]))
    digest = hashlib.sha256(
        ("|".join(f"{r['id']}:{r['score']}" for r in scored)).encode()
    ).hexdigest()
    return {
        "query": query,
        "n_docs": len(docs),
        "ranking": scored,
        "top_id": scored[0]["id"] if scored else None,
        "benchmark_digest": digest,
        "model": "bag-of-tokens-overlap-v1",
    }
