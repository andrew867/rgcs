"""A29-A33 — HAL memory codec adapter, hierarchical retrieval, loss
policy, and the ablation study.

Extends ``r3.hal_memory`` (synthetic-only records on tetrahedral
addresses) with codec-backed payload storage. Three invariants carry
over and are re-asserted here because this lane now touches payloads:

- records stay SYNTHETIC; personal data is refused by default (R29);
- an EXACT fallback path always exists (R30), so a lossy embedding can
  never become the only copy of something that mattered;
- provenance and authority survive compression (R28) — they are stored
  losslessly beside the payload, never inside the lossy channel.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import ClaimBoundaryError
from .codec import decode, encode
from r3.hal_memory import MemoryRecord


@dataclass(frozen=True)
class CodedMemory:
    """One HAL record whose payload is codec-compressed, with its
    provenance kept lossless and outside the lossy channel."""
    record: MemoryRecord
    container: bytes
    provenance: dict                    # LOSSLESS, never compressed
    exact_fallback: tuple | None        # R30
    reconstruction_error: float

    def __post_init__(self):
        if self.record.payload_class != "SYNTHETIC":
            raise ClaimBoundaryError(
                "only SYNTHETIC payloads may be stored (R29)")
        for k in ("authority", "created_epoch_s", "consent_ref"):
            if k not in self.provenance:
                raise ClaimBoundaryError(
                    f"provenance must retain {k!r} losslessly (R28)")


def store(record: MemoryRecord, payload, provenance: dict,
          keep_exact: bool = True, lam: float = 1.0,
          k: int = 16) -> CodedMemory:
    payload = np.asarray(payload, dtype=float)
    r = encode(payload, "LOSSY_FIXED_ERROR", 4, lam, k)
    err = float(np.mean((payload - r["reconstruction"]) ** 2))
    return CodedMemory(
        record, r["container"], dict(provenance),
        tuple(float(x) for x in payload) if keep_exact else None, err)


def retrieve(mem: CodedMemory, exact: bool = False) -> dict:
    """Retrieve approximately (fast) or exactly (fallback)."""
    if exact:
        if mem.exact_fallback is None:
            raise ClaimBoundaryError(
                "exact retrieval requested but no exact fallback was "
                "retained; the lossy copy is not authoritative (R30)")
        return {"values": np.asarray(mem.exact_fallback),
                "mode": "EXACT", "error": 0.0}
    return {"values": decode(mem.container), "mode": "APPROXIMATE",
            "error": mem.reconstruction_error}


def hierarchical_search(memories: list, query, top_k: int = 3) -> list:
    """A30: rank by distance on the DECOMPRESSED payload, then report
    what an exact rescoring would change — approximate search must
    never silently stand in for exact ranking."""
    q = np.asarray(query, dtype=float)
    approx = []
    for m in memories:
        v = decode(m.container)
        n = min(len(v), len(q))
        approx.append((float(np.linalg.norm(v[:n] - q[:n])), m))
    approx.sort(key=lambda t: t[0])
    exact = []
    for m in memories:
        if m.exact_fallback is None:
            continue
        v = np.asarray(m.exact_fallback)
        n = min(len(v), len(q))
        exact.append((float(np.linalg.norm(v[:n] - q[:n])), m))
    exact.sort(key=lambda t: t[0])
    a_ids = [m.record.address_k for _, m in approx[:top_k]]
    e_ids = [m.record.address_k for _, m in exact[:top_k]]
    return [{"approximate_top_k": a_ids,
             "exact_top_k": e_ids,
             "agreement": a_ids == e_ids,
             "note": "disagreement is the real cost of lossy "
                     "retrieval and is reported, not hidden"}]


def loss_policy() -> dict:
    """A31: what may be discarded, and what may never be."""
    return {
        "may_be_lossy": ("payload prototypes", "embeddings",
                         "field samples"),
        "must_be_lossless": ("addresses", "provenance", "authority",
                             "consent references", "receipts",
                             "correction records"),
        "rationale":
            "losing a payload sample degrades an answer; losing an "
            "address or a provenance record destroys the ability to "
            "know what was stored or whether it was permitted",
        "exact_fallback_required": True,
        "evidence_class": "ANALYTIC_MODEL",
    }


def ablation_study(n_records: int = 24, dim: int = 256,
                   seed: int = 20260718) -> dict:
    """A33: does the codec actually help HAL retrieval, and at what
    fidelity cost? Baseline = uncompressed float32."""
    rng = np.random.default_rng(seed)
    payloads = [np.repeat(rng.normal(size=dim // 16), 16)
                for _ in range(n_records)]
    prov = {"authority": "programme", "created_epoch_s": 0.0,
            "consent_ref": "n/a-synthetic"}
    # BOTH rate knobs are swept. Pinning lambda makes the tree refuse
    # to split whenever the rate cost of children exceeds the
    # distortion gain, which silently reduces the study to "one
    # prototype for everything" and reports the payload variance as
    # the codec's error.
    rows = []
    for lam in (0.01, 0.1, 1.0):
        for k in (4, 16, 64):
            mems = [store(MemoryRecord(i, 2, "SYNTHETIC", 0.0), p,
                          prov, True, lam, k)
                    for i, p in enumerate(payloads)]
            bits = sum(len(m.container) * 8 for m in mems)
            err = float(np.mean([m.reconstruction_error for m in mems]))
            agree = hierarchical_search(mems,
                                        payloads[0])[0]["agreement"]
            rows.append({"lambda": lam, "codebook_k": k,
                         "total_container_bits": bits,
                         "mean_mse": err,
                         "top_k_agrees_with_exact": agree})
    raw_bits = n_records * dim * 32
    return {"n_records": n_records, "dim": dim,
            "raw_float32_bits": raw_bits, "ablation": rows,
            "note": "container bits include the codebook; agreement "
                    "compares approximate ranking against the exact "
                    "fallback",
            "evidence_class": "NUMERICAL_SIMULATION"}
