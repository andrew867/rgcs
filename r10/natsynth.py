"""P06 — a blinded, matched natural-vs-synthetic quartz comparison.

The source hypothesis is that *naturally grown geological quartz is
"required"* -- that a crystal formed in the ground carries something a
laboratory-grown crystal does not. This module treats that claim the
only way it can be treated responsibly: as a **blinded, preregistered,
matched-controls experiment measuring ORDINARY material differences**,
and never as established consciousness science or exotic materials
physics. Naturally grown quartz, hydrothermal synthetic quartz, fused
silica, and glass are ordinary dielectrics; if any of them differs on an
ordinary endpoint it is because of ordinary differentiators -- trace
elements, fluid inclusions, dislocation density, water/OH content,
twinning -- until something far stronger is shown.

Why the experiment is matched and blinded
------------------------------------------

The failure mode this design defends against is a real one: an analyst
who can see that a specimen is "the natural one" scores it as special,
and geometry, mounting, and mass differences masquerade as an intrinsic
natural-vs-synthetic effect. So the protocol:

1. **Matches** natural and synthetic specimens on geometry, handedness,
   mass, c-axis orientation, and fixture, so a difference cannot be a
   difference in shape or mounting;
2. **Randomizes and blinds** specimen identity behind opaque codes, with
   **dummy** decoy specimens mixed in, so the analyst never knows which
   code is natural;
3. **Preregisters** the endpoints (acoustic Q, dielectric loss,
   absorption, ...) and the analysis, and **refuses** to score any
   endpoint that was not preregistered.

The headline statistic is a natural-vs-synthetic difference judged
against a **label-shuffle permutation null**. With no real group
difference the p-value is not small (the control); a planted
natural-group effect is recovered with a small p-value (the power
check); and significance is **Bonferroni-corrected** across endpoints.

The firewall the whole module exists to hold: a difference, if ever
found, is **materials science** -- attributed to ordinary
differentiators first -- and is never evidence of "consciousness
storage" or any exotic property. That refusal is explicit and tested.

No real specimens are in hand. Real-data status is
``BLOCKED_NO_SPECIMENS`` -- honest, not faked. The design, the blinding,
the null, and the power check are complete and tested on synthetic data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np


class NatSynthError(RuntimeError):
    """Raised on malformed input or a refused exotic/unpreregistered claim."""


# --- specimen classes ---------------------------------------------------

class SpecimenClass(Enum):
    """The true origin of a specimen, concealed from the analyst."""

    NATURAL = "NATURAL"            # naturally grown geological quartz
    SYNTHETIC = "SYNTHETIC"        # hydrothermal synthetic quartz
    FUSED_SILICA = "FUSED_SILICA"  # amorphous SiO2 control
    GLASS = "GLASS"               # ordinary glass control
    DUMMY = "DUMMY"               # decoy, present to defeat guessing


#: Which classes count as "natural" vs "not natural" for the contrast.
NATURAL_CLASSES = (SpecimenClass.NATURAL,)
SYNTHETIC_CLASSES = (SpecimenClass.SYNTHETIC,
                     SpecimenClass.FUSED_SILICA,
                     SpecimenClass.GLASS)

#: The variables that MUST be matched between the groups.
REQUIRED_MATCHING_VARIABLES = ("geometry", "handedness", "mass",
                               "fixture", "c_axis")

#: Ordinary differentiators a real difference is attributed to FIRST.
ORDINARY_DIFFERENTIATORS = ("trace_elements", "fluid_inclusions",
                            "dislocation_density", "water_OH_content",
                            "twinning", "surface_finish",
                            "electrode_contact")


# --- a single specimen --------------------------------------------------

@dataclass(frozen=True)
class Specimen:
    """One physical specimen. ``true_class`` is hidden behind a code."""

    specimen_id: str
    true_class: SpecimenClass
    geometry: str
    handedness: str               # "L", "R", or "NA" for amorphous
    mass_g: float
    c_axis: str                   # crystallographic axis orientation
    fixture: str


# --- the comparison schema ---------------------------------------------

@dataclass
class NaturalSyntheticComparison:
    """A blinded, matched natural-vs-synthetic comparison record.

    Every physical-measurement field defaults empty because this
    environment measures none of them: real specimens are
    ``BLOCKED_NO_SPECIMENS``.
    """

    comparison_id: str
    natural_specimens: tuple[Specimen, ...] = ()
    synthetic_specimens: tuple[Specimen, ...] = ()
    dummies: tuple[Specimen, ...] = ()
    matching_variables: tuple[str, ...] = REQUIRED_MATCHING_VARIABLES
    unmatched_variables: tuple[str, ...] = ORDINARY_DIFFERENTIATORS
    geometry: str = ""
    handedness: str = ""
    c_axis: str = ""
    fixture: str = ""
    excitation: str = ""
    measurements: dict = field(default_factory=dict)
    randomization: dict = field(default_factory=dict)
    blinding: str = "IDENTITY_BLINDED_BEHIND_CODES"
    preregistration: tuple[str, ...] = ()
    ordinary_models: tuple[str, ...] = ORDINARY_DIFFERENTIATORS
    endpoints: tuple[str, ...] = ()
    multiplicity: str = "BONFERRONI"
    result: str = "BLOCKED_NO_SPECIMENS"
    replication: str = "NOT_YET_REPLICATED"

    def all_specimens(self) -> tuple[Specimen, ...]:
        return (self.natural_specimens + self.synthetic_specimens
                + self.dummies)


# --- building a matched, blinded protocol ------------------------------

def matched_protocol(natural_specimens, synthetic_specimens, dummies,
                     *, geometry: str, handedness: str, mass_g: float,
                     c_axis: str, fixture: str, excitation: str,
                     endpoints, preregistration,
                     seed: int = 20260723) -> NaturalSyntheticComparison:
    """Build a design matched on the required variables and blinded.

    Every natural, synthetic, and dummy specimen must share the same
    ``geometry``, ``handedness``, ``mass_g`` (within tolerance),
    ``c_axis`` and ``fixture`` -- otherwise a group difference could be a
    shape or mounting difference and the protocol refuses to be built.
    Every scored endpoint must be preregistered. Dummies are required.
    """
    naturals = tuple(natural_specimens)
    synthetics = tuple(synthetic_specimens)
    decoys = tuple(dummies)
    if not naturals or not synthetics:
        raise NatSynthError(
            "need at least one natural and one synthetic specimen")
    if not decoys:
        raise NatSynthError(
            "dummy decoy specimens are required to defeat guessing")

    target = {"geometry": geometry, "handedness": handedness,
              "mass_g": mass_g, "c_axis": c_axis, "fixture": fixture}
    for sp in naturals + synthetics + decoys:
        if sp.geometry != target["geometry"]:
            raise NatSynthError(
                f"{sp.specimen_id} unmatched on geometry")
        if sp.handedness != target["handedness"]:
            raise NatSynthError(
                f"{sp.specimen_id} unmatched on handedness")
        if abs(sp.mass_g - target["mass_g"]) > 1e-6:
            raise NatSynthError(
                f"{sp.specimen_id} unmatched on mass")
        if sp.c_axis != target["c_axis"]:
            raise NatSynthError(
                f"{sp.specimen_id} unmatched on c_axis")
        if sp.fixture != target["fixture"]:
            raise NatSynthError(
                f"{sp.specimen_id} unmatched on fixture")

    endpoints = tuple(endpoints)
    prereg = tuple(preregistration)
    for e in endpoints:
        if e not in prereg:
            raise NatSynthError(
                f"endpoint {e!r} is not preregistered")

    rng = np.random.default_rng(seed)
    order = list(range(len(naturals) + len(synthetics) + len(decoys)))
    rng.shuffle(order)

    return NaturalSyntheticComparison(
        comparison_id="P06_matched",
        natural_specimens=naturals,
        synthetic_specimens=synthetics,
        dummies=decoys,
        geometry=geometry,
        handedness=handedness,
        c_axis=c_axis,
        fixture=fixture,
        excitation=excitation,
        randomization={"seed": seed, "presentation_order": order},
        preregistration=prereg,
        endpoints=endpoints,
        result="BLOCKED_NO_SPECIMENS",
    )


def matches_required_variables(design: NaturalSyntheticComparison) -> bool:
    """True iff every specimen shares the required matching variables."""
    specimens = design.all_specimens()
    if not specimens:
        return False
    ref = specimens[0]
    for sp in specimens:
        if (sp.geometry != ref.geometry
                or sp.handedness != ref.handedness
                or abs(sp.mass_g - ref.mass_g) > 1e-6
                or sp.c_axis != ref.c_axis
                or sp.fixture != ref.fixture):
            return False
    return True


# --- blinding: hide specimen identity behind codes ---------------------

@dataclass(frozen=True)
class BlindLabels:
    """Opaque codes shown to the analyst, plus the sealed reveal key.

    ``codes`` maps ``specimen_id`` -> opaque code (what the analyst
    sees). ``key`` maps opaque code -> true ``SpecimenClass`` and is
    meant to stay sealed until scoring is complete; it is carried here
    only so :func:`reveal` and the tests can round-trip it.
    """

    codes: dict = field(default_factory=dict)
    key: dict = field(default_factory=dict)


def blind_labels(specimens, seed: int = 20260723) -> BlindLabels:
    """Assign each specimen an opaque code that hides its true class."""
    specimens = tuple(specimens)
    if not specimens:
        raise NatSynthError("no specimens to blind")
    rng = np.random.default_rng(seed)
    idx = list(range(len(specimens)))
    rng.shuffle(idx)
    codes = {}
    key = {}
    for slot, i in enumerate(idx):
        code = f"code_{slot:03d}"
        sp = specimens[i]
        codes[sp.specimen_id] = code
        key[code] = sp.true_class
    return BlindLabels(codes=codes, key=key)


def reveal(labels: BlindLabels, key: dict) -> dict:
    """Recover each opaque code's true class from the sealed key."""
    try:
        return {code: key[code] for code in labels.codes.values()}
    except KeyError as exc:
        raise NatSynthError(
            f"code {exc} not in the supplied key") from exc


# --- preregistration firewall ------------------------------------------

def refuse_unpreregistered_endpoint(endpoint: str,
                                    preregistration) -> None:
    """Refuse to score an endpoint that was not preregistered.

    Scoring an endpoint chosen after seeing the data is the
    look-elsewhere sin: with enough unplanned endpoints something always
    "reaches significance". Only preregistered endpoints may be scored.
    """
    if endpoint not in tuple(preregistration):
        raise NatSynthError(
            f"endpoint {endpoint!r} was not preregistered; scoring it "
            f"after the fact is a garden of forking paths and is refused. "
            f"Preregister the endpoint and its analysis before unblinding.")


# --- the group-difference estimator, null and power --------------------

def group_difference(measurements, labels) -> float:
    """Natural-minus-not-natural difference in mean of an endpoint.

    ``labels`` is a per-measurement sequence of "NATURAL" / "NOT" tags.
    """
    m = np.asarray(measurements, float)
    lab = np.asarray(labels, dtype=object)
    if len(m) != len(lab):
        raise NatSynthError("measurements and labels differ in length")
    nat = m[lab == "NATURAL"]
    other = m[lab == "NOT"]
    if len(nat) == 0 or len(other) == 0:
        raise NatSynthError(
            "need at least one NATURAL and one NOT measurement")
    return float(nat.mean() - other.mean())


def label_shuffle_null(measurements, labels, *, trials: int = 2000,
                       seed: int = 20260723) -> dict:
    """Permutation null over the natural-vs-not group-label assignment.

    Shuffling which measurements are called NATURAL destroys any real
    group/endpoint link while preserving the measured values. The
    two-sided p-value is the fraction of shuffles whose absolute
    difference meets or exceeds the observed one. With no real group
    difference the p-value is not small.
    """
    m = np.asarray(measurements, float)
    lab = np.asarray(labels, dtype=object)
    obs = abs(group_difference(m, lab))
    rng = np.random.default_rng(seed)
    at_least = 0
    for _ in range(trials):
        lp = rng.permutation(lab)
        if abs(group_difference(m, lp)) >= obs - 1e-12:
            at_least += 1
    p = (at_least + 1) / (trials + 1)
    return {
        "observed_difference": float(group_difference(m, lab)),
        "observed_abs_difference": obs,
        "p_value": p,
        "verdict": ("GROUP_DIFFERENCE_DETECTED" if p < 0.05
                    else "NO_GROUP_DIFFERENCE"),
    }


def planted_group_effect_power(*, n_per_group: int = 12, effect: float = 3.0,
                               noise: float = 1.0, trials: int = 1000,
                               seed: int = 7) -> dict:
    """Plant a real natural-group effect and show the null recovers it.

    NATURAL measurements are drawn with mean ``effect`` above the
    not-natural group (both with Gaussian ``noise``). A working test
    returns a small p-value here.
    """
    rng = np.random.default_rng(seed)
    nat = rng.normal(effect, noise, size=n_per_group)
    other = rng.normal(0.0, noise, size=n_per_group)
    measurements = np.concatenate([nat, other])
    labels = np.array(["NATURAL"] * n_per_group
                      + ["NOT"] * n_per_group, dtype=object)
    res = label_shuffle_null(measurements, labels, trials=trials,
                             seed=seed + 1)
    return {
        "planted_effect": effect,
        "p_value": res["p_value"],
        "observed_difference": res["observed_difference"],
        "has_power": bool(res["p_value"] < 0.05),
    }


def multiplicity_correct(p_values, *, method: str = "BONFERRONI") -> dict:
    """Correct raw p-values across endpoints for multiple comparisons.

    Bonferroni multiplies each p-value by the number of endpoints
    (capped at 1). More endpoints means a raw p must be smaller to
    survive, so significance shrinks as the endpoint count grows.
    """
    p = np.asarray(list(p_values), float)
    if len(p) == 0:
        raise NatSynthError("no p-values to correct")
    if method != "BONFERRONI":
        raise NatSynthError(f"unsupported multiplicity method {method!r}")
    n = len(p)
    corrected = np.minimum(p * n, 1.0)
    return {
        "method": method,
        "n_endpoints": n,
        "raw": [float(x) for x in p],
        "corrected": [float(x) for x in corrected],
        "n_significant_raw": int(np.sum(p < 0.05)),
        "n_significant_corrected": int(np.sum(corrected < 0.05)),
    }


# --- the ordinary-explanation firewall ---------------------------------

def refuse_exotic_explanation(
        difference: float,
        claim: str = "consciousness storage in natural quartz") -> None:
    """Refuse to attribute a group difference to any exotic property.

    A measured natural-vs-synthetic difference, if ever found, is
    materials science: it is attributed to ordinary differentiators
    (trace elements, fluid inclusions, dislocation density, water/OH
    content, twinning) FIRST, and remains so until an ordinary account
    is conclusively excluded. It is never, on its own, evidence of
    consciousness storage or any exotic property.
    """
    raise NatSynthError(
        f"refusing the claim {claim!r}: an observed natural-vs-synthetic "
        f"difference of {difference:+.4g} is materials science until "
        f"proven otherwise. Ordinary differentiators "
        f"({', '.join(ORDINARY_DIFFERENTIATORS)}) must be excluded "
        f"before any exotic property is even entertained, and no "
        f"specimen has been measured here in any case.")


# --- real specimens are blocked, not faked -----------------------------

REAL_SPECIMEN_STATUS = {
    "status": "BLOCKED_NO_SPECIMENS",
    "why": ("a real comparison needs matched natural and synthetic "
            "quartz specimens, a metrology fixture (acoustic-Q resonator, "
            "dielectric cell, spectrophotometer) and a blinded analyst -- "
            "none of which this environment has. No acoustic Q, dielectric "
            "loss, absorption, or any other endpoint is measured"),
    "not_faked": ("no measured material result is reported, and no "
                  "natural-vs-synthetic difference is claimed. The design, "
                  "the matching, the blinding, the null, the power check "
                  "and the multiplicity correction are complete and tested "
                  "on synthetic data"),
}


def natsynth_report() -> dict:
    return {
        "design": ("blinded, preregistered, matched-controls "
                   "natural-vs-synthetic quartz comparison"),
        "matching_variables": list(REQUIRED_MATCHING_VARIABLES),
        "ordinary_differentiators": list(ORDINARY_DIFFERENTIATORS),
        "estimator": ("natural-minus-not-natural endpoint difference vs a "
                      "label-shuffle permutation null, Bonferroni-corrected"),
        "real_data": REAL_SPECIMEN_STATUS,
        "verdict": "MATCHED_PROTOCOL_SOFTWARE_ONLY",
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "what_this_does_not_say": (
            "It does not measure any material property, and it does not "
            "say that naturally grown quartz differs from synthetic quartz, "
            "fused silica, or glass on any endpoint. Should a difference "
            "ever be found, it is materials science -- attributed to "
            "ordinary differentiators first -- and never evidence of "
            "consciousness storage or any exotic property; that reading is "
            "refused. Real specimen data is blocked for want of specimens, "
            "not faked."),
    }
