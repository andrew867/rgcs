"""RGCS v4.6 — Crystalline Spacetime Coordinate Program (CSCP).

    Lore proposes. Mathematics translates. Software attacks.
    Evidence decides. Provenance remembers.

This package implements the v4.6 programme: exact unit-aware frequency
mathematics, preregistered statistical nulls, 64-tetrahedron simplicial
models, phase-coherent DDS/NCO recipe generation, controlled experiment
definitions, and relativistic clock / metric-energy audits.

It EXTENDS the existing RGCS subsystems rather than duplicating them:
exact frequency arithmetic and mechanism classification live in
``fkey_instrument`` (Fraction-exact, floats refused); phase closure in
``fkey_instrument.phase_closure``; the canonical evidence store and
workbook in ``rgcs_workbench``.

Binding doctrine (v4.6 core/03, core/04):

- Arithmetic equality is not spectral generation.
- Frequency correspondence is not physical coupling.
- Temporal order is not time travel.
- Clock sensitivity to spacetime is not spacetime propulsion.
- A numerical candidate is not a specimen resonance.
- A simulated result is not a bench measurement.
- Source lore is preserved, never silently promoted.

NOTHING in this package constitutes physical evidence. Every physical
hypothesis in the programme is UNTESTED unless a calibrated bench
record exists.
"""

from __future__ import annotations

SCHEMA_VERSION = "1.0.0"
PROGRAMME_ID = "RGCS-V4.6-CSCP"

#: Evidence ladder (core/04). Ordered weakest -> strongest for the
#: first eight; the last three are non-ladder statuses.
EVIDENCE_CLASSES = (
    "LORE",
    "SOURCE_CLAIM",
    "DERIVED_ARITHMETIC",
    "ANALYTIC_MODEL",
    "NUMERICAL_SIMULATION",
    "SYNTHETIC_RUN",
    "BENCH_MEASUREMENT",
    "REPLICATED_MEASUREMENT",
    "RELEASE_EVIDENCE",
    "UNSUPPORTED",
    "NOT_APPLICABLE",
)

#: Classes that assert something about the physical world. Software
#: alone may NEVER emit these.
PHYSICAL_EVIDENCE_CLASSES = ("BENCH_MEASUREMENT", "REPLICATED_MEASUREMENT")

#: Mandatory transfer firewalls (core/04). Each maps a tempting
#: inference to the reason it is refused. Enforced by
#: ``cspc.firewall`` and asserted by tests.
TRANSFER_FIREWALLS = {
    "ARITHMETIC_TO_SPECTRUM":
        "a multiplication or octave relation does not create a "
        "spectral component",
    "SPECTRUM_TO_COUPLING":
        "an available component does not prove the specimen couples "
        "to it",
    "COUPLING_TO_ANOMALY":
        "coupling does not imply an unknown mechanism",
    "TEMPORAL_ORDER_TO_TRAVEL":
        "periodic or subharmonic response is not displacement "
        "through time",
    "CLOCK_SHIFT_TO_METRIC_CONTROL":
        "sensing gravitational redshift is not generating useful "
        "curvature",
    "OPTICAL_FREQUENCY_TO_PHOTON_CONVERSION":
        "an octave relation does not perform nonlinear optical "
        "conversion",
    "GRAPH_SYMMETRY_TO_PHYSICAL_LATTICE":
        "combinatorial degeneracy does not establish a material "
        "structure",
    "SOURCE_PRECISION_TO_MEASUREMENT_PRECISION":
        "a 16-digit derived decimal does not inherit 16-digit "
        "empirical certainty from a nominal 2.45 GHz input",
}

#: Claims the programme must never make (core/03 charter).
EXCLUDED_CLAIMS = (
    "macroscopic time travel",
    "superluminal communication",
    "wormhole generation",
    "negative-energy production",
    "metric engineering",
    "torsion field detection without a defined detector and calibration",
    "consciousness transfer",
    "universal 4096 preference",
    "a unique frequency of water at 2.45 GHz",
    "optical/acoustic coupling from a power-of-two relationship alone",
)

#: Words that may not appear in a RESULT statement unless the exact
#: bounded claim and evidence class justify them (agent contract).
RESTRICTED_RESULT_WORDS = (
    "proves", "fundamental", "universal", "portal", "warp",
    "travel", "activation",
)


class ClaimBoundaryError(ValueError):
    """Raised when an operation would cross an evidence-class or
    transfer firewall — e.g. labelling a simulated result as a bench
    measurement, or promoting arithmetic into coupling."""


def validate_evidence_class(cls: str) -> str:
    if cls not in EVIDENCE_CLASSES:
        raise ClaimBoundaryError(
            f"{cls!r} is not a v4.6 evidence class; legal: "
            f"{', '.join(EVIDENCE_CLASSES)}")
    return cls


def require_non_physical(cls: str, context: str = "") -> str:
    """Guard for any software-only lane: refuse a physical evidence
    class. Software being green is not a measurement."""
    validate_evidence_class(cls)
    if cls in PHYSICAL_EVIDENCE_CLASSES:
        raise ClaimBoundaryError(
            f"{cls} requires a calibrated bench record with apparatus "
            f"provenance; software cannot emit it{(' — ' + context) if context else ''}")
    return cls
