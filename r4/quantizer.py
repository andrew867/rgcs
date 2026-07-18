"""A14-A17 — the tetrahedral vector quantizer, the SIC representation
adapter, the distortion registry, and GF(4) integrity primitives.

Tetrahedral codebook geometry is exact: four unit vectors with

    n_i . n_j = -1/3  (i != j),    sum_i n_i = 0,
    sum_i n_i n_i^T = (4/3) I.

**The SIC firewall (A15, R15).** For a Bloch vector r,

    p_i = (1/4)(1 + r . n_i),      r = 3 sum_i p_i n_i

is an informationally complete MEASUREMENT representation. Its four
outcomes are NOT four orthogonal storage states — the four directions
are mutually non-orthogonal (overlap -1/3), so a spin-1/2 cannot store
two bits this way. ``sic_probabilities`` therefore returns an object
that refuses to be treated as memory.

Distortion is payload-specific and unit-tagged, so a scalar MSE can
never be silently compared against an angular error.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from . import ClaimBoundaryError

_S = 1.0 / math.sqrt(3.0)

#: The four regular-tetrahedron unit vectors (exact by construction).
TETRA_CODEBOOK = np.array([
    [_S, _S, _S],
    [_S, -_S, -_S],
    [-_S, _S, -_S],
    [-_S, -_S, _S],
])


def codebook_geometry() -> dict:
    """Verify the exact geometry the doctrine specifies."""
    G = TETRA_CODEBOOK @ TETRA_CODEBOOK.T
    off = [G[i, j] for i in range(4) for j in range(4) if i != j]
    return {
        "norms": [float(np.linalg.norm(v)) for v in TETRA_CODEBOOK],
        "pairwise_dot": [float(x) for x in off],
        "all_pairs_minus_one_third":
            all(abs(x + 1 / 3) < 1e-12 for x in off),
        "sum_is_zero":
            float(np.linalg.norm(TETRA_CODEBOOK.sum(axis=0))) < 1e-12,
        "frame_operator_is_4_3_identity":
            float(np.linalg.norm(
                TETRA_CODEBOOK.T @ TETRA_CODEBOOK
                - (4 / 3) * np.eye(3))) < 1e-12,
        "orthogonal": False,
        "note": "four directions at -1/3 overlap are NOT an orthogonal "
                "basis; they cannot hold two bits in one spin-1/2",
        "evidence_class": "DERIVED_ARITHMETIC",
    }


def quantize_vector(v) -> dict:
    """Nearest codeword by maximum dot product (A14)."""
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v)
    if n == 0:
        raise ClaimBoundaryError("zero vector has no nearest direction")
    u = v / n
    dots = TETRA_CODEBOOK @ u
    idx = int(np.argmax(dots))
    recon = TETRA_CODEBOOK[idx] * n
    return {"symbol": idx, "dot": float(dots[idx]),
            "angular_error_deg":
                float(math.degrees(math.acos(
                    max(-1.0, min(1.0, float(dots[idx])))))),
            "reconstruction": recon,
            "euclidean_error": float(np.linalg.norm(v - recon))}


def max_angular_error_deg() -> float:
    """Worst-case angular error of the 4-cell quantizer: the angle from
    a codeword to the boundary of its Voronoi cell."""
    # the worst direction is equidistant from two codewords; angle
    # between codewords is arccos(-1/3) ~ 109.47 deg, so half is ~54.74
    return math.degrees(math.acos(-1 / 3)) / 2


# --- SIC representation adapter (A15) --------------------------------------

@dataclass(frozen=True)
class SICOutcome:
    """Four SIC-POVM outcome probabilities. A MEASUREMENT object.

    It deliberately exposes no storage interface: attempting to treat
    it as a four-state memory raises.
    """
    probabilities: tuple

    def __post_init__(self):
        if len(self.probabilities) != 4:
            raise ClaimBoundaryError("a SIC frame has four outcomes")
        if abs(sum(self.probabilities) - 1.0) > 1e-9:
            raise ClaimBoundaryError(
                f"probabilities sum to {sum(self.probabilities)}, not 1")
        if any(p < -1e-12 for p in self.probabilities):
            raise ClaimBoundaryError("negative probability")

    def as_storage_symbol(self):
        raise ClaimBoundaryError(
            "SIC outcomes are measurement statistics, not persistent "
            "storage states. The four tetrahedral directions are "
            "non-orthogonal (overlap -1/3); they do not provide four "
            "distinguishable memory levels (R15 firewall).")

    def bloch_vector(self) -> np.ndarray:
        return 3.0 * sum(p * n for p, n in
                         zip(self.probabilities, TETRA_CODEBOOK))


def sic_probabilities(bloch_vector) -> SICOutcome:
    """p_i = (1/4)(1 + r . n_i)."""
    r = np.asarray(bloch_vector, dtype=float)
    if np.linalg.norm(r) > 1.0 + 1e-9:
        raise ClaimBoundaryError(
            "Bloch vector longer than 1 is not a physical state")
    p = tuple(float(0.25 * (1.0 + float(r @ n))) for n in TETRA_CODEBOOK)
    return SICOutcome(p)


def sic_roundtrip_error(bloch_vector) -> float:
    r = np.asarray(bloch_vector, dtype=float)
    return float(np.linalg.norm(
        sic_probabilities(r).bloch_vector() - r))


# --- distortion registry (A16) ---------------------------------------------

#: metric -> (unit, applicable payload kinds)
DISTORTION_METRICS = {
    "MSE": ("payload_units^2", ("SCALAR", "FIELD", "EMBEDDING")),
    "MAX_ABS": ("payload_units", ("SCALAR", "FIELD")),
    "EUCLIDEAN": ("payload_units", ("VECTOR", "EMBEDDING")),
    "ANGULAR_DEG": ("degrees", ("VECTOR",)),
    "KL_DIVERGENCE": ("nats", ("PROBABILITY",)),
    "RETRIEVAL_LOSS": ("fraction", ("EMBEDDING",)),
}


def distortion(metric: str, a, b, payload_kind: str) -> dict:
    """Compute a distortion with its unit and applicability checked —
    a scalar MSE can never be silently compared with an angle."""
    if metric not in DISTORTION_METRICS:
        raise ClaimBoundaryError(f"unknown metric {metric!r}")
    unit, kinds = DISTORTION_METRICS[metric]
    if payload_kind not in kinds:
        raise ClaimBoundaryError(
            f"metric {metric} does not apply to payload kind "
            f"{payload_kind} (applies to {kinds})")
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if metric == "MSE":
        val = float(np.mean((a - b) ** 2))
    elif metric == "MAX_ABS":
        val = float(np.max(np.abs(a - b)))
    elif metric == "EUCLIDEAN":
        val = float(np.linalg.norm(a - b))
    elif metric == "ANGULAR_DEG":
        ca = a / np.linalg.norm(a)
        cb = b / np.linalg.norm(b)
        val = float(math.degrees(math.acos(
            max(-1.0, min(1.0, float(ca @ cb))))))
    elif metric == "KL_DIVERGENCE":
        mask = a > 0
        val = float(np.sum(a[mask] * np.log(a[mask] / b[mask])))
    else:                                    # RETRIEVAL_LOSS
        val = float(np.mean(a != b))
    return {"metric": metric, "value": val, "unit": unit,
            "payload_kind": payload_kind}


# --- GF(4) integrity primitives (A17) ---------------------------------------

#: GF(4) = {0,1,2,3} with 2 = x, 3 = x+1 modulo x^2 + x + 1.
_GF4_MUL = [[0, 0, 0, 0],
            [0, 1, 2, 3],
            [0, 2, 3, 1],
            [0, 3, 1, 2]]


def gf4_add(a: int, b: int) -> int:
    """Addition in GF(4) is XOR (characteristic 2)."""
    _check_gf4(a)
    _check_gf4(b)
    return a ^ b


def gf4_mul(a: int, b: int) -> int:
    _check_gf4(a)
    _check_gf4(b)
    return _GF4_MUL[a][b]


def _check_gf4(x: int) -> None:
    if x not in (0, 1, 2, 3):
        raise ClaimBoundaryError(f"{x} is not a GF(4) element")


def gf4_inverse(a: int) -> int:
    _check_gf4(a)
    if a == 0:
        raise ClaimBoundaryError("0 has no multiplicative inverse")
    for b in (1, 2, 3):
        if gf4_mul(a, b) == 1:
            return b
    raise AssertionError("unreachable")


def parity_symbol(symbols: list) -> int:
    """Single GF(4) parity symbol: detects any single-symbol error and
    corrects a single ERASURE (a known-position loss)."""
    p = 0
    for s in symbols:
        p = gf4_add(p, s)
    return p


def correct_erasure(symbols_with_gap: list, parity: int,
                    gap_index: int) -> int:
    """Recover one erased symbol from the parity — the honest scope of
    a single parity symbol (it cannot LOCATE an unknown error)."""
    acc = parity
    for i, s in enumerate(symbols_with_gap):
        if i != gap_index:
            acc = gf4_add(acc, s)
    return acc


def integrity_scope() -> dict:
    """State exactly what the fixture does and does not do (A17)."""
    return {
        "detects": "any single-symbol error in the protected block",
        "corrects": "one ERASURE at a known position",
        "does_not_correct": "an unknown-position single error (needs "
                            "more parity, e.g. a GF(4) Hamming code)",
        "status": "PROOF_FIXTURE",
        "note": "a small quaternary code is a proof fixture, not a "
                "universal production choice (core/06)",
    }
