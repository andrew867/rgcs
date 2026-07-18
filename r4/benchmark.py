"""A27, A55-A56 — the rate-distortion harness, fair baselines, and the
null campaign.

The programme's compression claim is only meaningful against honest
competition, so the baselines include the ones that usually win:
flat float32, raw quaternary/octal (which is the SAME 12 bits — the
radix "win" that isn't), uniform scalar quantization, and
general-purpose lossless compression (zlib) of the raw bytes.

**The negative control (R50) is load-bearing.** On incompressible
random data every method must fail to compress. A codec that reports
gains on white noise is measuring its own bookkeeping, not structure —
the same class of error that inverted the v4.6 headline result.

All costs are total: topology + address + codebook + symbols +
entropy model + residual. Encode/decode time and random-access cost
are reported alongside (R51).
"""

from __future__ import annotations

import time
import zlib
from dataclasses import dataclass

import numpy as np

from .codec import encode, entropy_bits, random_access

# --- corpora (A32/A55) --------------------------------------------------------


def corpus(name: str, n: int = 4096, seed: int = 20260718
           ) -> np.ndarray:
    """Deterministic benchmark payloads. ``RANDOM_UNIFORM`` and
    ``RANDOM_GAUSSIAN`` are the negative controls."""
    rng = np.random.default_rng(seed)
    x = np.linspace(0, 1, n)
    if name == "SMOOTH_FIELD":
        return np.sin(2 * np.pi * x) + 0.3 * np.sin(8 * np.pi * x)
    if name == "PIECEWISE_CONSTANT":
        return np.repeat(rng.normal(size=n // 64), 64)[:n]
    if name == "SPARSE_EVENTS":
        v = np.zeros(n)
        v[rng.choice(n, size=max(n // 128, 1), replace=False)] = 1.0
        return v
    if name == "PHASE_RAMP":
        return np.mod(np.cumsum(np.full(n, 0.03)), 2 * np.pi)
    if name == "RANDOM_UNIFORM":
        return rng.uniform(-1, 1, n)
    if name == "RANDOM_GAUSSIAN":
        return rng.normal(0, 1, n)
    raise ValueError(f"unknown corpus {name!r}")


CORPORA = ("SMOOTH_FIELD", "PIECEWISE_CONSTANT", "SPARSE_EVENTS",
           "PHASE_RAMP", "RANDOM_UNIFORM", "RANDOM_GAUSSIAN")
NEGATIVE_CONTROLS = ("RANDOM_UNIFORM", "RANDOM_GAUSSIAN")


# --- baselines (A56) ----------------------------------------------------------

def baseline_flat_float32(data: np.ndarray) -> dict:
    return {"name": "FLAT_FLOAT32", "total_bits": 32 * len(data),
            "mse": 0.0, "lossless": True}


def baseline_raw_quaternary(data: np.ndarray) -> dict:
    """The radix 'win' that isn't: writing the same float32 as
    quaternary digits costs the SAME bits (6 quaternary = 12 bits per
    12-bit group)."""
    return {"name": "RAW_QUATERNARY", "total_bits": 32 * len(data),
            "mse": 0.0, "lossless": True,
            "note": "identical to flat binary — radix conversion is "
                    "not compression"}


def baseline_uniform_quantizer(data: np.ndarray, bits: int = 8) -> dict:
    lo, hi = float(np.min(data)), float(np.max(data))
    if hi == lo:
        q = np.zeros_like(data)
    else:
        levels = 2 ** bits - 1
        idx = np.round((data - lo) / (hi - lo) * levels)
        q = lo + idx / levels * (hi - lo)
    return {"name": f"UNIFORM_Q{bits}",
            "total_bits": bits * len(data) + 64,   # + range header
            "mse": float(np.mean((data - q) ** 2)), "lossless": False}


def baseline_zlib(data: np.ndarray) -> dict:
    raw = np.asarray(data, dtype=np.float32).tobytes()
    comp = zlib.compress(raw, 9)
    return {"name": "ZLIB_FLOAT32", "total_bits": 8 * len(comp),
            "mse": 0.0, "lossless": True}


def baseline_entropy_only(data: np.ndarray, bits: int = 8) -> dict:
    """Uniform quantize then ideal entropy-code the symbols."""
    lo, hi = float(np.min(data)), float(np.max(data))
    levels = 2 ** bits - 1
    idx = (np.round((data - lo) / (hi - lo) * levels).astype(int)
           if hi > lo else np.zeros(len(data), dtype=int))
    q = lo + idx / levels * (hi - lo) if hi > lo else data * 0
    ent = entropy_bits(list(idx), alphabet=2 ** bits)
    return {"name": f"ENTROPY_Q{bits}",
            "total_bits": ent["total_bits"] + 64,
            "mse": float(np.mean((data - q) ** 2)), "lossless": False}


BASELINES = (baseline_flat_float32, baseline_raw_quaternary,
             baseline_uniform_quantizer, baseline_zlib,
             baseline_entropy_only)


# --- harness (A27) -------------------------------------------------------------

#: Codebook sizes swept alongside lambda. Sweeping only lambda pins
#: fidelity at the CODEBOOK bottleneck (the tree can be exact while the
#: prototypes are still quantized to k levels), so the resulting curve
#: is not a rate-distortion frontier at all. Both rate knobs are swept.
CODEBOOK_SIZES = (4, 16, 64, 256)


def rate_distortion_curve(data: np.ndarray, lambdas: list,
                          max_depth: int = 5,
                          codebook_sizes: tuple = CODEBOOK_SIZES
                          ) -> list:
    """Sweep BOTH rate knobs (tree granularity lambda and codebook size
    k). Each point is (total bits, MSE) with full accounting."""
    out = []
    for lam in lambdas:
        for k in codebook_sizes:
            if k > max(len(data) // 2, 2):
                continue
            t0 = time.perf_counter()
            r = encode(data, "LOSSY_FIXED_ERROR", max_depth, lam, k)
            enc_s = time.perf_counter() - t0
            mse = float(np.mean((data - r["reconstruction"]) ** 2))
            out.append({"lambda": lam, "k": k,
                        "total_bits": r["bit_accounting"]["total_bits"],
                        "mse": mse, "n_leaves": r["n_leaves"],
                        "encode_s": enc_s,
                        "compression_ratio": r["compression_ratio"]})
    return out


def pareto_front(curve: list) -> list:
    """Points not dominated on both bits and MSE — the honest frontier
    to compare against a baseline."""
    front = []
    for c in sorted(curve, key=lambda x: x["total_bits"]):
        if not any(o["mse"] <= c["mse"] and
                   o["total_bits"] <= c["total_bits"] and o is not c
                   for o in front):
            front.append(c)
    return front


def benchmark_corpus(name: str, n: int = 4096,
                     lambdas: list | None = None) -> dict:
    """One corpus against the codec and every baseline."""
    data = corpus(name, n)
    lambdas = lambdas or [0.01, 0.1, 1.0, 10.0, 100.0]
    curve = rate_distortion_curve(data, lambdas)
    base = [b(data) for b in BASELINES]
    ra = random_access(data, n // 2)

    # fair comparison: the codec point closest in MSE to each lossy
    # baseline, and bits-vs-bits at matched distortion
    verdicts = []
    for b in base:
        if b["lossless"]:
            best = min(curve, key=lambda c: c["mse"])
            beats = best["total_bits"] < b["total_bits"] and \
                best["mse"] < 1e-12
        else:
            cands = [c for c in curve if c["mse"] <= b["mse"] * 1.05]
            best = min(cands, key=lambda c: c["total_bits"]) \
                if cands else None
            beats = bool(best and best["total_bits"] < b["total_bits"])
        verdicts.append({"baseline": b["name"],
                         "baseline_bits": b["total_bits"],
                         "baseline_mse": b["mse"],
                         "codec_bits_at_matched_distortion":
                             best["total_bits"] if best else None,
                         "codec_beats_baseline": beats})
    return {
        "corpus": name,
        "n": n,
        "is_negative_control": name in NEGATIVE_CONTROLS,
        "rate_distortion": curve,
        "baselines": base,
        "verdicts": verdicts,
        "beats_any_baseline": any(v["codec_beats_baseline"]
                                  for v in verdicts),
        "random_access_nodes_touched": ra["nodes_touched"],
        "evidence_class": "NUMERICAL_SIMULATION",
    }


def full_campaign(n: int = 2048) -> dict:
    """Every corpus, with the negative-control gate applied.

    The gate: if the codec 'beats' a baseline on random data, the
    result set is not trustworthy and the campaign says so.
    """
    results = {c: benchmark_corpus(c, n) for c in CORPORA}
    control_failures = [
        c for c in NEGATIVE_CONTROLS
        if results[c]["beats_any_baseline"]
    ]
    structured = [c for c in CORPORA if c not in NEGATIVE_CONTROLS]
    wins = [c for c in structured if results[c]["beats_any_baseline"]]
    return {
        "results": results,
        "negative_controls": list(NEGATIVE_CONTROLS),
        "negative_control_failures": control_failures,
        "negative_control_gate":
            "PASS" if not control_failures else "FAIL",
        "structured_corpora_with_wins": wins,
        "interpretation":
            ("Codec gains appear only on structured payloads and NOT "
             "on incompressible random data — the expected signature "
             "of real structure exploitation."
             if not control_failures else
             "FAIL: gains reported on random data. The accounting or "
             "the comparison is wrong; no compression claim may be "
             "made from this campaign."),
        "claim_boundary":
            "rate-distortion on synthetic corpora with full bit "
            "accounting. Nothing here is a physical measurement, and "
            "radix conversion contributes zero compression.",
        "evidence_class": "NUMERICAL_SIMULATION",
    }
