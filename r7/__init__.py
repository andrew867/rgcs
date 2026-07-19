"""RGCS v5.0 R7 — Root Reference, CW Vector Decoder, Differential Clock
Link, Interferometric Crystal Alignment, Directional Field Geometry,
Falsifiable Metric Challenge, and Open-Legacy Decision.

    A coordinate space begins from a declared phase authority,
    not from a preferred story.

R7's priority, unchanged from the R6 closing recommendation: compare
two independently characterized oscillators through a declared
transfer link while recording every environmental nuisance channel.
The crystal apparatus proceeds in parallel and does not outrank it.

Three firewalls carry the programme:

1. **CW parse** (core/02) — retrospective structural compatibility is
   not evidence of encoding, and R7 computes exactly how much evidence
   it is not.
2. **Geometry to gravity** (core/07) — a claimed metric effect must
   survive u(t) -> T_munu -> g_munu arithmetic, reported as an
   order-of-magnitude gap against a real sensor floor.
3. **Publication** (core/09) — no public disclosure without a signed
   decision record. A commit is date evidence, not legal advice.

Extends cspc/, pmwr/, r3/, r4/, r6/. Nothing here is physical
evidence: no oscillator pair has been compared, no crystal aligned, no
field mapped, no force measured.
"""

from __future__ import annotations

SCHEMA_VERSION = "1.0.0"
PROGRAMME_ID = "RGCS-V5.0-R7"

#: CW vector promotion ladder (core/02). Note that the ladder has a
#: REJECTED terminal state as well as a CONFIRMED one: the decoder is
#: allowed to fail, and failing is a result.
CW_STATUSES = (
    "CW_VECTOR_RAW_SOURCE",
    "CW_PARSE_HYPOTHESIS",
    "CW_PARSE_RETROSPECTIVE",
    "CW_PARSE_PROSPECTIVE_SUPPORT",
    "CW_SEMANTICS_CONFIRMED",
    "CW_SEMANTICS_REJECTED",
)

#: Root-reference oscillator classes (core/01). No source is declared
#: fundamental; 4096 Hz may be *derived* from a root and need not be a
#: physical root oscillator.
ROOT_CLASSES = (
    "QUARTZ_XO",
    "TCXO",
    "OCXO",
    "RUBIDIUM",
    "CAESIUM",
    "GPSDO",
    "HYDROGEN_MASER",
    "OPTICAL",
    "TRANSFER_LOCKED_REMOTE",
    "SYNTHETIC_SOFTWARE_TEST_ONLY",
)

#: Non-contact excitation statuses (core/05). A passive crystal needs
#: an energy source; a self-oscillator needs loop gain >= 1.
EXCITATION_STATUSES = (
    "FORCED_RESPONSE",
    "RINGDOWN",
    "ACTIVE_SELF_OSCILLATION",
    "PASSIVE_SELF_OSCILLATION_CLAIM_REFUSED",
    "CONTACT_LOADING_DOMINANT",
)

#: Geometry-to-gravity arithmetic verdicts (core/07).
GRAVITY_STATUSES = (
    "REFUSED_BY_ARITHMETIC",
    "BELOW_SENSOR_FLOOR",
    "CONVENTIONAL_EFFECT_MEASURABLE",
    "ANOMALOUS_RESIDUAL_CANDIDATE",
)

#: The three publication paths (core/09). PRIVATE_RC is the only
#: reversible one.
PUBLICATION_PATHS = (
    "FILE_THEN_PUBLISH",
    "DEFENSIVE_PUBLICATION",
    "PRIVATE_RC",
)

#: States that must never exist in R7.
FORBIDDEN_STATES = (
    "METRIC_ACTUATED",
    "SPACETIME_ENGINEERED",
    "THRUST_CONFIRMED",
    "ANTIGRAVITY_DEMONSTRATED",
    "CW_SEMANTICS_ASSUMED",
    "PASSIVE_SELF_OSCILLATION_ACHIEVED",
    "PATENT_GRANTED",
)

#: Tempting identifications R7 refuses, with the reason.
FORBIDDEN_COLLAPSES = {
    "SHARED_PREFIX_IS_SHARED_PROTOCOL":
        "five integers that lie within 2^22 of each other necessarily "
        "share their leading bits; a constant header and first field "
        "is arithmetic, not evidence of a field layout (core/02)",
    "PARSE_COMPATIBILITY_IS_ENCODING":
        "38 = 2 + 3*12 = 2 + 6*6 is an identity about the number 38, "
        "and every 38-bit integer admits both parses; compatibility "
        "carries no information about intent",
    "VECTOR_SUM_IS_THRUST":
        "adding two 45-degree unit vectors gives sqrt(2) along the "
        "bisector by definition; a commanded field direction is not a "
        "measured force (core/06)",
    "STORED_ENERGY_IS_SPACETIME_CURVATURE":
        "E/c^2 for any bench-scale energy is a mass so small that its "
        "gravitational signature sits tens of orders of magnitude "
        "below any sensor (core/07)",
    "HANDHELD_RESPONSE_IS_SELF_OSCILLATION":
        "a crystal that rings while held is showing forced response "
        "and contact loading; self-oscillation requires a loop with "
        "gain at least unity and the right phase (core/05)",
    "COMMIT_DATE_IS_LEGAL_PRIORITY":
        "a git commit is useful evidence of a date and is not a "
        "patent filing, a defensive publication, or legal advice "
        "(core/09)",
}

__all__ = [
    "SCHEMA_VERSION",
    "PROGRAMME_ID",
    "CW_STATUSES",
    "ROOT_CLASSES",
    "EXCITATION_STATUSES",
    "GRAVITY_STATUSES",
    "PUBLICATION_PATHS",
    "FORBIDDEN_STATES",
    "FORBIDDEN_COLLAPSES",
]
