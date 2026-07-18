"""RGCS v4.7 — Phase Memory, Worldline-Indexed Multipath Recovery,
Causal Channel Reconstruction, and Phryll Translation Hypothesis (PMWR).

    Lore proposes. Mathematics translates. Software attacks.
    Evidence decides. Provenance remembers.

The scientific centre (pack 00_START_HERE):

    A coherent signal carries measurable timing and phase history. A
    synchronized, calibrated receiver can estimate portions of that
    history only when the observation and model make the inverse
    problem identifiable.

This package EXTENDS the existing stack — exact arithmetic and units
(``cspc.units``), candidate registry (``cspc.exact``), DDS/closure
(``cspc.dds``, ``fkey_instrument.phase_closure``), spacetime constants
(``cspc.spacetime``), preregistration (``cspc.experiments``) — rather
than duplicating any of it.

Programme law (core/01), enforced mechanically where possible:

- A crystal is finite-coherence hardware, not an immortal phase oracle.
- Absolute phase is generally modulo 2π.
- Exact dyadic closure is both a synchronization feature and a delay
  alias.
- Multiple path histories can explain one observation.
- Recovery must expose rank, conditioning, posterior width, ambiguity,
  and refusal.
- Arrival reordering is not causal reversal.
- "Phryll" is an unresolved source term, not a sensor channel.
- Synthetic output is never physical evidence.

``DETECTED_PHRYLL`` is deliberately not a state anywhere in v4.7.
"""

from __future__ import annotations

SCHEMA_VERSION = "1.0.0"
PROGRAMME_ID = "RGCS-V4.7-PMWR"

#: v4.7 evidence classes (core/08), superset of the v4.6 ladder.
EVIDENCE_CLASSES = (
    "LORE",
    "METAPHOR",
    "SOURCE_CLAIM",
    "DERIVED_ARITHMETIC",
    "GEOMETRY_IDENTITY",
    "ANALYTIC_MODEL",
    "NUMERICAL_SIMULATION",
    "SYNTHETIC_RUN",
    "BENCH_MEASUREMENT",
    "CALIBRATED_MEASUREMENT",
    "ANTHROPOGENIC_STRUCTURE",
    "REPRESENTATION_ARTIFACT",
    "CIRCULAR_DERIVATION",
    "UNEXPLAINED_INSTRUMENT_RESIDUAL",
    "REPLICATED_ANOMALY",
    "PROSPECTIVE_PREDICTION",
    "UNSUPPORTED",
)

PHYSICAL_EVIDENCE_CLASSES = ("BENCH_MEASUREMENT", "CALIBRATED_MEASUREMENT",
                             "REPLICATED_ANOMALY")

#: The Phryll promotion ladder (core/06). Every arrow requires
#: preregistration, calibration, controls, uncertainty, blinding,
#: energy accounting, and independent replication.
PHRYLL_LADDER = (
    "SOURCE_CLAIM",
    "OPERATIONAL_HYPOTHESIS",
    "UNEXPLAINED_INSTRUMENT_RESIDUAL",
    "REPLICATED_ANOMALY",
    "CANDIDATE_NEW_MECHANISM",
)

#: States that must never exist in v4.7. Tests grep the package for
#: these; their absence is load-bearing.
PROHIBITED_STATES = ("DETECTED_PHRYLL", "PHRYLL_DETECTED",
                     "PHRYLL_CONFIRMED")

#: Non-negotiable firewalls (00_START_HERE). Claim -> why it is refused.
FIREWALLS = {
    "PERFECT_ABSOLUTE_PHASE":
        "quartz does not store perfect absolute phase; coherence is "
        "finite and phase is modulo 2*pi",
    "ENVIRONMENTAL_IMMUNITY":
        "a local crystal is not immune to motion, gravity, "
        "temperature, aging, mounting, or drive electronics",
    "ONE_RESIDUAL_ONE_PATH":
        "one scalar residual does not uniquely reveal one path; "
        "multiple path histories can explain one observation",
    "CLOSURE_REMOVES_AMBIGUITY":
        "exact closure does not remove delay ambiguity — it IS a "
        "delay alias at multiples of the closure window",
    "4096_PRIVILEGED":
        "4096 Hz is not privileged by nature (v4.6 corpus result: the "
        "simplicity metric measures human convention)",
    "PYRAMID_PROVES_MECHANISM":
        "the Great Pyramid angle proves no mechanism; the ratio is a "
        "geometry observation",
    "ANGLE_PROVES_DIRECTIONALITY":
        "51.843/60 degree terminations do not prove directional "
        "energy flow; directionality requires both-orientation tests "
        "with matched controls",
    "SENSOR_CHANGE_IS_PHRYLL":
        "a sensor change equals a sensor change; Phryll is an "
        "unresolved source term, not a channel",
    "DEVICE_MIRACLES":
        "the device creates none of: antigravity, free energy, "
        "torsion energy, metric curvature, consciousness transfer, "
        "healing, time travel",
    "REORDER_IS_REVERSAL":
        "arrival reordering is not causal reversal; emission order is "
        "fixed on the worldline",
}


class ClaimBoundaryError(ValueError):
    """Raised when an operation would cross an evidence or firewall
    boundary."""


class IdentifiabilityError(RuntimeError):
    """Raised when a reconstruction is requested from observations that
    do not identify it. Refusal is the correct output."""


def validate_evidence_class(cls: str) -> str:
    if cls not in EVIDENCE_CLASSES:
        raise ClaimBoundaryError(
            f"{cls!r} is not a v4.7 evidence class")
    return cls


def require_non_physical(cls: str, context: str = "") -> str:
    """Software lanes may never emit a physical evidence class."""
    validate_evidence_class(cls)
    if cls in PHYSICAL_EVIDENCE_CLASSES:
        raise ClaimBoundaryError(
            f"{cls} requires calibrated apparatus records"
            f"{(' — ' + context) if context else ''}")
    return cls
