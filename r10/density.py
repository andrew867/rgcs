"""P02/P03 — the nine-"density" ontology, typed, with two anchors only.

The source material describes a nine-step ladder it calls "density",
running from base matter to "Source". This module represents it as
software so it can be reasoned about and argued with -- and the first
thing the software enforces is the thing most likely to be confused.

**"Density" here is a source-language word. It is not mathematical
dimension, and it is not physical mass density.** The source ladder
puts "time and free will" at step 4 and "oneness with Source" at step
9; nothing about that is a coordinate count or a kg/m^3. Conflating the
source's "density N" with an N-dimensional space, or with a material
density, is a category error, and :func:`refuse_dimension_conflation`
raises on it. This firewall is the point of the module.

**Only two numbers are anchored.** The source supplies exactly two:
the light-body fraction is 0.5 at step 6 (the "50/50" balance), and
step 9 is "Source" itself (fraction 1.0 by definition of the endpoint).
Every other fraction is *model-derived*, and the module refuses to
report a point value for it -- it returns an interpolated estimate
**with an uncertainty band**, and marks it `MODEL_DERIVED`. Reading a
crisp "step 5 is 0.34 light" off a two-point fit would be inventing
evidence.

Nothing here is measured, and none of it is biology, physics, or
cosmology. It is a typed record of a source ontology plus honest
interpolation between two supplied anchors.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# --- the firewall this module exists to enforce -----------------------

class DimensionConflation(TypeError):
    """Raised when source-'density' is treated as dimension or mass."""


class UnsupportedAnchor(ValueError):
    """Raised when a point value is demanded where only a band exists."""


def refuse_dimension_conflation(kind: str) -> None:
    """'Density N' is not N dimensions and not N kg/m^3."""
    raise DimensionConflation(
        f"source 'density' is a rung on an ontological ladder, not "
        f"{kind}. 'Density 4' is the source's word for 'time and free "
        f"will', not a four-dimensional space and not a mass density. "
        f"The mathematical dimensionality of any model in this "
        f"repository is tracked separately and is never set from a "
        f"source density number.")


# --- the ladder, as source ontology -----------------------------------

#: The nine steps, labelled at a granularity safe to state publicly.
#: The full source descriptions stay in the private corpus; these are
#: neutral one-line glosses.
DENSITY_STEPS = {
    1: "base matter",
    2: "simple organisms",
    3: "embodied conscious organisms",
    4: "time and free will (a separate source narrative)",
    5: "additional perceptual/interaction channels claimed",
    6: "claimed material/light balance; individuality retained",
    7: "individuality described as diminishing",
    8: "planetary-scale identity",
    9: "Source; the ladder's endpoint",
}

#: The ONLY two anchored light-body fractions. Everything else is
#: model-derived (see interpolate_light_fraction).
LIGHT_FRACTION_ANCHORS = {6: 0.5, 9: 1.0}

#: Individuation is described qualitatively, not numerically. Kept as
#: ordered labels, never as a fraction, because the source gives none.
INDIVIDUATION = {
    6: "RETAINED",
    7: "DIMINISHING",
    8: "PLANETARY",
    9: "SOURCE_IDENTITY",
}

CLAIM_STATUS = "SOURCE_CLAIM"        # the ladder itself is a source claim


@dataclass(frozen=True)
class DensityState:
    """One rung, typed. Numeric fields carry their support explicitly."""

    density_id: int
    gloss: str
    light_fraction: float | None      # None where unsupplied
    light_fraction_support: str       # ANCHORED | MODEL_DERIVED
    light_fraction_uncertainty: float # 0 for anchors; band half-width
    individuation: str
    claim_status: str = CLAIM_STATUS

    def __post_init__(self) -> None:
        if not 1 <= self.density_id <= 9:
            raise ValueError("density_id must be 1..9")
        if self.light_fraction_support not in ("ANCHORED", "MODEL_DERIVED",
                                               "UNSUPPLIED"):
            raise ValueError("bad support flag")


# --- P03: interpolation that refuses to overclaim ----------------------

#: Competing monotone models between the anchors. None is privileged;
#: their disagreement IS the uncertainty, so they are reported together.
def _linear(d): return 0.5 + (d - 6) * (1.0 - 0.5) / (9 - 6)
def _concave(d): return 0.5 + (1.0 - 0.5) * ((d - 6) / 3) ** 0.5
def _convex(d): return 0.5 + (1.0 - 0.5) * ((d - 6) / 3) ** 2

MONOTONE_MODELS = {"LINEAR": _linear, "CONCAVE": _concave, "CONVEX": _convex}


def interpolate_light_fraction(density_id: int) -> dict:
    """Estimate the light fraction, honestly, between two anchors.

    Above step 6 the three monotone models bracket the estimate; the
    band half-width is half their spread. Below step 6 there is no
    lower anchor at all, so the fraction is returned as UNSUPPLIED --
    not extrapolated. Two points do not determine a curve, and one
    anchor determines nothing below it.
    """
    if not 1 <= density_id <= 9:
        raise ValueError("density_id must be 1..9")
    if density_id in LIGHT_FRACTION_ANCHORS:
        return {
            "density_id": density_id,
            "light_fraction": LIGHT_FRACTION_ANCHORS[density_id],
            "support": "ANCHORED",
            "uncertainty": 0.0,
            "models": {},
            "note": "supplied by the source; not interpolated",
        }
    if density_id < 6:
        return {
            "density_id": density_id,
            "light_fraction": None,
            "support": "UNSUPPLIED",
            "uncertainty": None,
            "models": {},
            "note": ("no anchor exists below step 6, so any number here "
                     "would be pure extrapolation from a single point. "
                     "Refused."),
        }
    vals = {k: f(density_id) for k, f in MONOTONE_MODELS.items()}
    lo, hi = min(vals.values()), max(vals.values())
    return {
        "density_id": density_id,
        "light_fraction": (lo + hi) / 2,
        "support": "MODEL_DERIVED",
        "uncertainty": (hi - lo) / 2,
        "models": vals,
        "note": ("midpoint of three monotone models pinned to the "
                 "step-6 and step-9 anchors; the spread is the "
                 "uncertainty, and it is not a measurement"),
    }


def light_fraction_point(density_id: int) -> float:
    """Refuse to hand out a bare number where only a band exists."""
    r = interpolate_light_fraction(density_id)
    if r["support"] != "ANCHORED":
        raise UnsupportedAnchor(
            f"step {density_id}'s light fraction is {r['support']}, not "
            f"anchored. Estimate {r['light_fraction']} plus/minus "
            f"{r['uncertainty']}, or UNSUPPLIED below step 6. A point "
            f"value would imply precision the source never gave.")
    return r["light_fraction"]


def build_ladder() -> list[DensityState]:
    out = []
    for d in range(1, 10):
        est = interpolate_light_fraction(d)
        out.append(DensityState(
            density_id=d,
            gloss=DENSITY_STEPS[d],
            light_fraction=est["light_fraction"],
            light_fraction_support=est["support"],
            light_fraction_uncertainty=est["uncertainty"] or 0.0,
            individuation=INDIVIDUATION.get(d, "UNSPECIFIED"),
        ))
    return out


def anchors_are_respected(ladder=None) -> bool:
    """The two anchors must come back exactly, uninterpolated."""
    ladder = ladder or build_ladder()
    by_id = {s.density_id: s for s in ladder}
    return (by_id[6].light_fraction == 0.5
            and by_id[6].light_fraction_support == "ANCHORED"
            and by_id[9].light_fraction == 1.0
            and by_id[9].light_fraction_support == "ANCHORED")


def density_report() -> dict:
    ladder = build_ladder()
    model_derived = [s.density_id for s in ladder
                     if s.light_fraction_support == "MODEL_DERIVED"]
    unsupplied = [s.density_id for s in ladder
                  if s.light_fraction_support == "UNSUPPLIED"]
    return {
        "steps": len(ladder),
        "anchored": sorted(LIGHT_FRACTION_ANCHORS),
        "model_derived": model_derived,
        "unsupplied_below_anchor": unsupplied,
        "claim_status": CLAIM_STATUS,
        "the_firewall": (
            "source 'density' is not mathematical dimension and not "
            "mass density; refuse_dimension_conflation() enforces it"),
        "what_is_supplied": (
            "exactly two numbers: light fraction 0.5 at step 6 and the "
            "Source endpoint at step 9. Everything else is model-"
            "derived with an uncertainty band or refused as unsupplied"),
        "evidence_class": "SOURCE_CLAIM translated to typed record",
        "measured_here": "nothing",
        "what_this_does_not_say": (
            "It does not say the ladder is real, that beings occupy its "
            "rungs, or that the light fractions correspond to anything "
            "measurable. It is a faithful, typed record of a source "
            "ontology with its two supplied anchors preserved and its "
            "gaps left open."),
    }
