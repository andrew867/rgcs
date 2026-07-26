"""The Physics Truth Gate, machine-readable (program authority).

Encodes ``00_CONTROL/PHYSICS_TRUTH_GATE.md`` so no workstream can
promote a banned claim silently: the implementable-effects whitelist,
the never-promote list, the mandatory energy-ledger fields, the
promotion protocol, and — separately, with exact energy and evidence
boundaries — the four concepts the program must never blur together:
parametric resonance, intrinsic quantum spin, torsion, and quantum
energy teleportation.

Nothing here validates physics; it validates *language and
accounting*. A result may say "anomalous residual detected under
protocol X"; it may not say "anti-gravity confirmed".
"""

from __future__ import annotations

from dataclasses import dataclass

from rgcs_lab.common.status_schema import ClaimClass, SchemaError

#: Effects that may be implemented or simulated (whitelist, verbatim).
IMPLEMENTABLE_EFFECTS = (
    "parametric resonance",
    "ordinary and nonlinear resonance",
    "internal energy release in superelastic collisions",
    "classical gyroscopic precession",
    "intrinsic quantum spin",
    "electron, nuclear, and ferromagnetic resonance",
    "conventional Einstein-Cartan and metric-affine models",
    "candidate propagating-torsion theories when explicitly named",
    "quantum energy teleportation protocols",
    "spoof surface plasmon polaritons",
    "metasurface dispersion",
    "counterrotating electromagnetic modes",
    "error-correcting codes",
    "quaternionic frame rotations",
    "synthetic dimensions and coupled-mode lattices",
)

#: Claims that must never be promoted silently (verbatim).
NEVER_PROMOTE = (
    "parametric resonance amplifies gravity",
    "a superelastic collision obtains energy from nowhere",
    "gyroscopic precession is antigravity",
    "intrinsic spin can be aligned in ordinary material to create "
    "useful spacetime torsion",
    "a known MHz frequency reverses gravity",
    "spin connection resonance is an experimentally established "
    "anti-gravity mechanism",
    "Einstein-Cartan theory predicts a tabletop repulsive-gravity "
    "resonance",
    "quantum energy teleportation provides net vacuum-energy extraction",
    "zero-point energy has been harvested as unlimited usable power",
    "Schumann or cyclotron tuning creates lift",
    "a patent proves physical operation",
    "an AI-generated paper proves a physical effect",
    "a simulation anomaly is thrust, gravity modification, or excess "
    "energy",
)

#: Words that may never appear as a free-floating explanation.
NO_FREE_EXPLANATION_TERMS = ("torsion", "spin connection", "torsionon",
                             "resonance")

#: Mandatory energy-ledger fields for every driven/resonant system.
ENERGY_LEDGER_FIELDS = (
    "input_electrical_power_w",
    "input_mechanical_power_w",
    "stored_field_energy_j",
    "stored_mechanical_energy_j",
    "thermal_loss_w",
    "radiation_loss_w",
    "dielectric_loss_w",
    "ohmic_loss_w",
    "numerical_error_j",
    "measured_mechanical_output_w",
    "unexplained_residual_w",
    "unexplained_residual_uncertainty_w",
)

#: The promotion protocol steps (all nine, ordered, verbatim).
PROMOTION_PROTOCOL = (
    "declared hypothesis",
    "frozen apparatus and analysis",
    "calibrated sensors",
    "power and momentum accounting",
    "sham and detuned controls",
    "orientation reversal",
    "blind run order where practical",
    "uncertainty budget",
    "independent replication",
)

ALLOWED_CONCLUSION_TEMPLATE = "anomalous residual detected under protocol X"
FORBIDDEN_CONCLUSIONS = ("anti-gravity confirmed",
                         "vacuum energy extracted",
                         "spacetime torsion resonated")


@dataclass(frozen=True)
class ConceptBoundary:
    """One physics concept with its exact energy and evidence boundary.

    These four are SEPARATE concepts. Nothing in the program may chain
    them into a combined mechanism without each link independently
    meeting the promotion protocol.
    """

    concept_id: str
    what_it_is: str
    energy_boundary: str
    evidence_boundary: str
    claim_class: str


CONCEPT_BOUNDARIES: tuple[ConceptBoundary, ...] = (
    ConceptBoundary(
        "PARAMETRIC_RESONANCE",
        "growth of an oscillation when a system parameter is modulated "
        "(e.g. at twice the natural frequency); textbook classical "
        "dynamics.",
        "all amplified energy comes from the time-varying pump or "
        "modulated parameter — the drive does measurable work; nothing "
        "is amplified for free, and gravity is not a pumpable "
        "parameter in any established sense.",
        "implementable and demonstrable in software and on a bench; "
        "any claim that it amplifies GRAVITY is on the never-promote "
        "list.",
        ClaimClass.CONVENTIONAL_PHYSICS.value),
    ConceptBoundary(
        "INTRINSIC_SPIN",
        "quantum angular momentum of particles; basis of ESR/NMR/FMR, "
        "all implementable as conventional physics.",
        "spin alignment stores ordinary magnetic energy; it does not "
        "create useful spacetime torsion in ordinary material — "
        "Einstein-Cartan torsion is algebraically sourced by spin "
        "density, does not propagate outside matter, and its "
        "corrections are expected only at extreme spin densities.",
        "spin resonance demonstrations are fine; 'aligned spins -> "
        "useful torsion' is on the never-promote list.",
        ClaimClass.CONVENTIONAL_PHYSICS.value),
    ConceptBoundary(
        "TORSION",
        "geometric torsion in Einstein-Cartan / metric-affine gravity; "
        "propagating-torsion variants are separate, explicitly named "
        "speculative theories with their own parameters.",
        "standard EC torsion carries no free energy budget to tap; "
        "propagating-torsion models add new dynamical terms that must "
        "be named, parameterized and bounded, never invoked as a free "
        "explanation.",
        "conventional models may be implemented; 'torsion', 'spin "
        "connection', 'torsionon' and 'resonance' may never appear as "
        "free explanations; tabletop repulsive-gravity claims are on "
        "the never-promote list.",
        ClaimClass.EXPLORATORY_MODEL.value),
    ConceptBoundary(
        "QET",
        "quantum energy teleportation: LOCC protocols that make "
        "locally-passive energy accessible at a distant site using "
        "prior entanglement and classical messages.",
        "obeys local operations, classical communication and strict "
        "energy conservation; the injected measurement energy pays for "
        "everything — NET energy is never created and vacuum energy is "
        "not 'extracted' in the free-power sense.",
        "protocol simulations are implementable; 'net vacuum-energy "
        "extraction' is on the never-promote list.",
        ClaimClass.CONVENTIONAL_PHYSICS.value),
)

_BY_ID = {c.concept_id: c for c in CONCEPT_BOUNDARIES}


def concept(concept_id: str) -> ConceptBoundary:
    try:
        return _BY_ID[concept_id]
    except KeyError:
        raise SchemaError(
            f"unknown concept {concept_id!r}; bounded concepts: "
            f"{sorted(_BY_ID)}") from None


def refuse_concept_conflation(*concept_ids: str) -> None:
    """Refuse chaining bounded concepts into one combined mechanism."""
    named = [concept(c).concept_id for c in concept_ids]
    raise SchemaError(
        f"refused: {' + '.join(named)} may not be chained into a "
        f"combined mechanism. Each is a separate concept with its own "
        f"energy and evidence boundary; every link would need to pass "
        f"the nine-step promotion protocol independently, and none has.")


def screen_text_for_banned_claims(text: str) -> list[str]:
    """Return every never-promote claim asserted verbatim in ``text``.

    A quoted/negated mention is the caller's responsibility to wrap —
    this screen is deliberately dumb, loud and reviewable, not clever.
    """
    low = " ".join(text.lower().split())
    return [claim for claim in NEVER_PROMOTE + FORBIDDEN_CONCLUSIONS
            if claim.lower() in low]


def validate_energy_ledger(ledger: dict) -> dict:
    """Check a driven-system energy ledger for the mandatory fields and
    arithmetic closure: residual = inputs - losses - outputs (within
    the declared numerical error and uncertainty)."""
    missing = [f for f in ENERGY_LEDGER_FIELDS if f not in ledger]
    if missing:
        raise SchemaError(
            f"energy ledger missing mandatory fields: {missing}")
    inputs = (ledger["input_electrical_power_w"]
              + ledger["input_mechanical_power_w"])
    losses = (ledger["thermal_loss_w"] + ledger["radiation_loss_w"]
              + ledger["dielectric_loss_w"] + ledger["ohmic_loss_w"])
    out = ledger["measured_mechanical_output_w"]
    residual = inputs - losses - out
    declared = ledger["unexplained_residual_w"]
    tol = abs(ledger["unexplained_residual_uncertainty_w"]) + 1e-12
    closes = abs(residual - declared) <= tol
    if not closes:
        raise SchemaError(
            f"energy ledger does not close: computed residual "
            f"{residual} W vs declared {declared} W beyond uncertainty "
            f"{tol} W. Fix the accounting; do not narrate the gap.")
    return {"closes": True, "residual_w": residual,
            "conclusion_ceiling": ALLOWED_CONCLUSION_TEMPLATE}
