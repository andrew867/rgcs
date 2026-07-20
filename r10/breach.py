"""S17/S18 — "breach" as a resonant-frequency change, and pump typing.

The source material's "breach" now has an operational candidate: a
**persistent change in a crystal's resonant frequency**. That is a real
improvement, because a frequency shift is measurable, and measurable
claims can be wrong.

It also has an immediate problem. A quartz resonator's frequency moves
for a long list of thoroughly ordinary reasons, and most of those move
it by *more* than a careless observer would expect:

    aging (first year)        1 to 5 ppm, and it never stops
    temperature off-turnover  0.5 to 30 ppm/degC depending on cut
    load capacitance          10 to 100+ ppm across a trimmer's range
    drive level               0.1 to 10 ppm across a decade of drive
    mechanical/mount stress   1 to 100 ppm after a shock or re-seating
    contamination             1 to 50 ppm, usually one-way

So the question is never "did the frequency change" -- it always
changes -- but **"did it change by more than the ordinary causes can
account for, under controls that were in place before the change"**.

:func:`assess_shift` answers that arithmetically. The ordinary budget
is combined in quadrature for independent contributors, and a shift
inside the budget returns ``ORDINARY``. There is no exotic verdict
anywhere in this module: the best available outcome is
``UNEXPLAINED_BY_THIS_BUDGET``, which names what was not controlled
rather than what was discovered.

S18 keeps the pump branches apart. 20 Hz, 20.48 Hz and 21 Hz differ by
2.4 to 5 per cent. Whether that is "the same frequency" is not a matter
of taste -- it depends on the linewidth of whatever is being driven,
and :func:`resolvable` decides it from Q.

Nothing here is measured. No apparatus has been built, and physical
hardware is deferred by the pack.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

# --- S18: the pump branches, kept separate ----------------------------

#: Exact: 20.48 = 512/25, and 20.48 * 200 == 4096 exactly.
PUMP_BRANCHES = {
    "PUMP_20_HZ": {
        "hz": Fraction(20),
        "role": "nominal low-frequency pump",
        "exact": True,
    },
    "PUMP_20_48_HZ": {
        "hz": Fraction(512, 25),
        "role": "4096/200, an exact submultiple of the 4096 ladder",
        "exact": True,
    },
    "PUMP_21_HZ": {
        "hz": Fraction(21),
        "role": "alternate branch; note the CW 21-vs-20 substitution",
        "exact": True,
    },
    "CARRIER_1496_HZ": {
        "hz": Fraction(1496),
        "role": "carrier candidate; 1496 = 8 * 11 * 17",
        "exact": True,
    },
    "LADDER_4096_HZ": {
        "hz": Fraction(4096),
        "role": "2**12; 8 Hz * 2**9 = 4096 Hz exactly",
        "exact": True,
    },
}

#: The pack is explicit that these are different proposed roles and
#: must not be collapsed into one resonance.
DO_NOT_COLLAPSE = ("PUMP_20_HZ", "PUMP_20_48_HZ", "PUMP_21_HZ")


class CollapsedBranches(ValueError):
    """Raised when distinct pump branches are treated as one."""


def eight_hz_ladder() -> dict:
    """8 Hz * 2**9 = 4096 Hz. Exact, and exactly that much."""
    base, doublings = Fraction(8), 9
    return {
        "base_hz": str(base),
        "doublings": doublings,
        "result_hz": str(base * 2 ** doublings),
        "exact": base * 2 ** doublings == 4096,
        "also": "4096 == 2**12",
        "what_it_shows": (
            "that 8 and 4096 are related by nine octaves, which is "
            "arithmetic"),
        "what_it_does_not_show": (
            "that either frequency is physically privileged. Nine "
            "doublings from 8 reaches 4096 the same way nine doublings "
            "from 7 reaches 3584; the relation is a property of the "
            "radix, not evidence about a resonator."),
    }


def fractional_separation(a: str, b: str) -> float:
    """|f_a - f_b| / f_a, as a fraction."""
    fa, fb = PUMP_BRANCHES[a]["hz"], PUMP_BRANCHES[b]["hz"]
    return abs(float(fb - fa) / float(fa))


def resolvable(a: str, b: str, q_factor: float) -> dict:
    """Are two branches distinguishable at this Q?

    A resonance of quality factor Q has fractional bandwidth 1/Q. Two
    drives separated by more than that are driving measurably
    different things. This is the whole of the "same frequency?"
    question, and it has a number in it.
    """
    if q_factor <= 0:
        raise ValueError("Q must be positive")
    sep = fractional_separation(a, b)
    bandwidth = 1.0 / q_factor
    return {
        "a": a, "b": b,
        "fractional_separation": sep,
        "fractional_bandwidth": bandwidth,
        "separated_in_linewidths": sep / bandwidth,
        "resolvable": sep > bandwidth,
        "note": (
            "at this Q the two are different frequencies and cannot be "
            "treated as one" if sep > bandwidth else
            "at this Q the two fall inside one linewidth; they may be "
            "driving the same resonance, and that is a statement about "
            "Q, not about the numbers"),
    }


def refuse_branch_collapse() -> None:
    """Refuse to merge the three low-frequency branches."""
    seps = {f"{a} vs {b}": f"{fractional_separation(a, b) * 100:.2f}%"
            for i, a in enumerate(DO_NOT_COLLAPSE)
            for b in DO_NOT_COLLAPSE[i + 1:]}
    raise CollapsedBranches(
        f"the low-frequency branches are separated by {seps}. For any "
        f"resonator with Q above about 40 those are different "
        f"frequencies, and a quartz crystal's Q is four to six orders "
        f"higher. They carry different proposed roles and are not "
        f"interchangeable.")


# --- S17: ordinary causes of a frequency shift -------------------------

@dataclass(frozen=True)
class OrdinaryCause:
    """A conventional mechanism that moves a resonator's frequency."""

    name: str
    typical_ppm: float
    worst_ppm: float
    controllable: bool
    control: str
    source: str

    def __post_init__(self) -> None:
        if self.typical_ppm < 0 or self.worst_ppm < self.typical_ppm:
            raise ValueError(
                "need 0 <= typical_ppm <= worst_ppm")


#: Order-of-magnitude figures from standard quartz-resonator practice.
#: These are engineering ranges, not measurements by this project, and
#: they are deliberately generous: a budget that understates ordinary
#: causes manufactures anomalies.
ORDINARY_CAUSES = (
    OrdinaryCause(
        "AGING", 2.0, 5.0, False,
        "cannot be eliminated; characterise with a long baseline",
        "first-year aging for a typical commercial AT-cut resonator"),
    OrdinaryCause(
        "TEMPERATURE", 5.0, 30.0, True,
        "hold and log temperature; know the cut's turnover point",
        "AT-cut cubic tempco away from turnover; other cuts are worse"),
    OrdinaryCause(
        "LOAD_CAPACITANCE", 10.0, 100.0, True,
        "fix and measure the load network, including stray capacitance",
        "pullability across a typical trimmer range"),
    OrdinaryCause(
        "DRIVE_LEVEL", 1.0, 10.0, True,
        "hold drive constant and log it",
        "drive-level dependence across a decade of drive current"),
    OrdinaryCause(
        "MOUNT_STRESS", 5.0, 100.0, True,
        "do not re-seat, re-clamp, or move the crystal mid-experiment",
        "stress sensitivity after shock or re-mounting"),
    OrdinaryCause(
        "CONTAMINATION", 1.0, 50.0, True,
        "sealed enclosure; note that this cause is usually one-way",
        "mass loading from adsorbed contamination"),
)

VERDICTS = (
    "ORDINARY",
    "WITHIN_UNCONTROLLED_BUDGET",
    "UNEXPLAINED_BY_THIS_BUDGET",
    "REFUSED_NO_BASELINE",
)


def ordinary_budget_ppm(controlled: set[str] | None = None,
                        worst_case: bool = False) -> float:
    """Combined ordinary budget, in ppm.

    Independent contributors add in quadrature. Naming a cause as
    controlled removes it, which is the only way the budget shrinks --
    and it must be controlled *before* the shift, not argued away
    after.
    """
    controlled = controlled or set()
    unknown = {c.name for c in ORDINARY_CAUSES} - controlled
    bad = controlled - {c.name for c in ORDINARY_CAUSES}
    if bad:
        raise ValueError(f"unknown cause(s) named as controlled: {bad}")
    terms = [(c.worst_ppm if worst_case else c.typical_ppm)
             for c in ORDINARY_CAUSES if c.name in unknown]
    return math.sqrt(sum(t * t for t in terms))


def assess_shift(observed_ppm: float, *, controlled: set[str] | None = None,
                 has_pre_baseline: bool = False,
                 baseline_days: float = 0.0,
                 worst_case: bool = False) -> dict:
    """Is this shift larger than ordinary causes can account for?

    ``has_pre_baseline`` is not a formality. Without a characterised
    before-state there is nothing to have shifted *from*, and aging
    alone guarantees the frequency was already moving. A claim without
    a baseline is refused rather than scored.
    """
    controlled = controlled or set()
    if observed_ppm < 0:
        raise ValueError("observed shift magnitude cannot be negative")

    if not has_pre_baseline or baseline_days <= 0:
        return {
            "verdict": "REFUSED_NO_BASELINE",
            "observed_ppm": observed_ppm,
            "why": (
                "no characterised pre-change baseline. Aging alone "
                "means the frequency was already drifting, so without "
                "a baseline there is no 'before' for the shift to be "
                "measured against, and any number is unfalsifiable."),
        }

    budget = ordinary_budget_ppm(controlled, worst_case)
    uncontrolled = sorted({c.name for c in ORDINARY_CAUSES} - controlled)
    exceeds = observed_ppm > budget

    if not exceeds:
        verdict = "ORDINARY"
    elif uncontrolled:
        verdict = "WITHIN_UNCONTROLLED_BUDGET" if observed_ppm <= \
            ordinary_budget_ppm(controlled, worst_case=True) \
            else "UNEXPLAINED_BY_THIS_BUDGET"
    else:
        verdict = "UNEXPLAINED_BY_THIS_BUDGET"

    return {
        "verdict": verdict,
        "observed_ppm": observed_ppm,
        "ordinary_budget_ppm": budget,
        "worst_case_budget_ppm": ordinary_budget_ppm(controlled, True),
        "ratio_to_budget": observed_ppm / budget if budget else math.inf,
        "controlled": sorted(controlled),
        "uncontrolled": uncontrolled,
        "baseline_days": baseline_days,
        "what_this_verdict_is_not": (
            "UNEXPLAINED_BY_THIS_BUDGET means this budget does not "
            "cover the shift. It does not mean the cause is unknown to "
            "physics, and it certainly does not mean the cause is "
            "exotic. The commonest explanation for a shift outside a "
            "budget is a cause missing from the budget."),
    }


def breach_protocol() -> dict:
    """What would have to be done before a shift meant anything."""
    return {
        "operational_definition": (
            "a persistent change in a crystal's series resonant "
            "frequency, measured against a characterised baseline"),
        "why_this_is_an_improvement": (
            "it is measurable, so it can be wrong. 'Breach' as a "
            "narrative term could not be."),
        "required_before_any_claim": [
            "a baseline long enough to separate aging from a step: "
            "weeks, not hours",
            "temperature logged continuously, and the cut's turnover "
            "point known",
            "load network and stray capacitance fixed and measured",
            "drive level held constant and recorded",
            "the crystal not re-seated, moved, or shocked mid-run",
            "a second, untreated crystal measured on the same "
            "instrument throughout",
            "the measurement instrument's own drift characterised "
            "against a reference",
        ],
        "the_control_that_matters_most": (
            "the second untreated crystal. It converts an absolute "
            "frequency measurement, which drifts for a dozen reasons, "
            "into a differential one, which mostly does not. Without "
            "it, instrument drift and room temperature are "
            "indistinguishable from the effect."),
        "ordinary_causes": [
            {"name": c.name, "typical_ppm": c.typical_ppm,
             "worst_ppm": c.worst_ppm, "control": c.control,
             "source": c.source}
            for c in ORDINARY_CAUSES],
        "typical_total_budget_ppm": ordinary_budget_ppm(),
        "hardware_status": "DEFERRED — no apparatus has been built",
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
    }


def refuse_breach_claim() -> None:
    """No breach has been observed, because nothing has been measured."""
    raise RuntimeError(
        "no breach claim is available. No apparatus has been built, no "
        "crystal has been measured, and no baseline exists. This "
        "module defines what would have to be true and computes the "
        "budget a shift would have to exceed; it reports no "
        "observation, and the best verdict it can ever return is "
        "UNEXPLAINED_BY_THIS_BUDGET.")
