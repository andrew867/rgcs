"""RGCS v4.8 R4 — Tetrahedral Spin-Addressed Multiresolution Codec,
Quaternary Memory, and Physical Spin-Memory Qualification.

    Lore proposes. Mathematics translates. Software attacks.
    Evidence decides. Provenance remembers.

The exact radix bridge (core/03):

    64   = 8^2 = 4^3 = 2^6
    4096 = 8^4 = 4^6 = 2^12

Three quaternary symbols select one of 64 states; six select one of
4096. **This is exact radix conversion, not compression.** Compression
must come from adaptive hierarchy, prototypes, residuals, sparsity and
entropy coding, and must be demonstrated as lower rate at equal
distortion (or lower distortion at equal rate) against fair baselines.

Six things stay separate throughout (00_START_HERE):

1. tetrahedral hierarchical address;
2. quaternary logical symbol;
3. payload / prototype;
4. phase and epoch metadata;
5. physical spin realization, if any;
6. reconstruction error and uncertainty.

Extends r3/ (addressing), pmwr/ (phase authority), cspc/ (units).
Nothing here is physical evidence: no spin memory has been written,
read, or reset in any material.
"""

from __future__ import annotations

SCHEMA_VERSION = "1.0.0"
PROGRAMME_ID = "RGCS-V4.8-R4"

#: The six separated concerns of a codeword C = (A, P, Phi, t, Sigma, E).
CODEWORD_COMPONENTS = ("address", "payload", "phase", "epoch",
                       "uncertainty", "reconstruction_error")

#: Physical four-state ontology (core/05). Never merged implicitly.
PHYSICAL_FOUR_STATE_TYPES = (
    "LOGICAL_QUATERNARY",
    "SPIN_HALF_FOUR_DIRECTIONS",
    "SPIN_THREE_HALVES",
    "TWO_COUPLED_SPIN_HALF",
    "FOUR_CLASSICAL_DOMAINS",
    "TETRAHEDRAL_SIC_OUTCOMES",
    "QUARTZ_DEFECT_PLATFORM",
)

#: Compression modes (core/04).
CODEC_MODES = ("LOSSLESS_STRUCTURE", "LOSSLESS_PAYLOAD",
               "LOSSY_FIXED_ERROR", "LOSSY_FIXED_RATE",
               "PROGRESSIVE", "SPARSE_RANDOM_ACCESS")

#: Physical stop-matrix gates (core/13). Blocked is a first-class
#: status; the programme may continue in simulation, but may never
#: synthesize a physical verdict.
PHYSICAL_GATES = {
    "FOUR_LOGICAL_SYMBOLS": "LOGICAL_ALPHABET_INCOMPLETE",
    "PHYSICAL_STATE_COUNT": "FOUR_STATE_MANIFOLD_UNPROVEN",
    "WRITE": "WRITE_PATH_INCOMPLETE",
    "READ": "READOUT_DEGENERATE",
    "RESET": "RESET_UNAVAILABLE",
    "RETENTION": "RETENTION_UNMEASURED",
    "CROSSTALK": "CROSSTALK_UNBOUNDED",
    "CALIBRATION": "CALIBRATION_INCOMPLETE",
    "SAFETY": "HARDWARE_SAFETY_BLOCKED",
    "CODEC_INTEGRATION": "PHYSICAL_CODEC_UNVERIFIED",
}

#: Claims the programme may not make (00_START_HERE scientific ceiling).
EXCLUDED_CLAIMS = (
    "spin storage in quartz without specimen evidence",
    "four orthogonal spin-1/2 states from four directions",
    "compression from base conversion alone",
    "consciousness storage",
    "Phryll detection",
    "spacetime torsion",
    "nodal-point operation",
    "metric actuation",
    "transport",
)


class ClaimBoundaryError(ValueError):
    """An operation would cross an R4 claim or ontology boundary."""


class PhysicalGateBlocked(RuntimeError):
    """A physical gate is not satisfied. Simulation may continue; a
    physical verdict may not be emitted."""


def validate_four_state_type(t: str) -> str:
    if t not in PHYSICAL_FOUR_STATE_TYPES:
        raise ClaimBoundaryError(
            f"{t!r} is not a declared four-state platform type")
    return t


def refuse_radix_compression_claim() -> None:
    """The single most likely self-deception in this programme."""
    raise ClaimBoundaryError(
        "base conversion is not compression: 4096 = 8^4 = 4^6 = 2^12 "
        "is an exact re-encoding of the same 12 bits. Compression "
        "requires lower rate at equal distortion against a fair "
        "baseline (core/04).")
