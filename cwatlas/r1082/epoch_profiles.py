"""P12 — Cs-Ba epoch profile registry (typed, separate candidate lanes).

The source ontology proposes several isotope-derived ways to read an epoch. This
module implements each as a **typed, separate candidate profile** and keeps them
distinct — it never pretends one isotope lane is already proven, and it never
silently selects one over the others.

The five candidate profiles (Locked Decisions, "Epoch candidates"):

* ``CS133_FINE_PHASE`` — Cs-133 fine coherent cycle / phase authority. The
  hyperfine transition frequency (9 192 631 770 Hz) *defines* the SI second; the
  observable is the fractional phase (wraps every cycle).
* ``CS137_DECAY_ENVELOPE`` — Cs-137 coarse exponential decay envelope; the
  observable is the remaining parent fraction (half at one half-life).
* ``BA137_DAUGHTER_RATIO`` — Ba-137 daughter / material-age ratio, accumulated
  as the Cs-137 parent decays (equal parent/daughter at one parent half-life).
* ``BA130_PARENT_FULL`` — Ba-130 parent-full / creation-scale candidate; its
  double-electron-capture half-life is cosmological, so the parent fraction is
  essentially full on any human timescale.
* ``COMPOSITE_VARIABLE_DEPTH`` — a variable-depth combination (coarse envelope +
  fine phase) matching the packed wire epoch.

Two hard rules:

* **Conventional timestamps stay mandatory.** A certificate must carry a
  conventional UTC/TAI/TT/TDB timestamp *even when* a compressed source epoch is
  present. :func:`build_certificate` refuses otherwise.
* **Isotope constants and source ontology are separate fields.** Physical
  constants (half-life, frequency, uncertainty) never mix with the source's
  interpretation of the lane.

Each lane is evidence class ``DERIVED_MATHEMATICS`` and claim class
``OPERATOR_HYPOTHESIS`` — a candidate transform, ``proven=False``. Promoting a
lane to proven, or selecting one silently, is refused.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

from cwatlas.claims import ClaimClass
from cwatlas.r1082 import claims as _r1082
from cwatlas.r1082.claims import R1082ClaimError

# -- conventional timescales (mandatory metadata) ---------------------------

TIMESCALES = frozenset({"UTC", "TAI", "TT", "TDB"})

#: Conventional epoch origin (J2000-style reference). A declared constant, not a
#: wall-clock read; all transforms take seconds elapsed from this origin.
EPOCH_ORIGIN = {"timescale": "TT", "value": "2000-01-01T12:00:00"}

# -- isotope constants (physical, kept separate from source ontology) -------

#: Cs-133 ground-state hyperfine transition frequency — defines the SI second
#: exactly, so its relative uncertainty is zero.
CS133_HYPERFINE_HZ = 9_192_631_770.0

_JULIAN_YEAR_S = 365.25 * 86400.0
CS137_HALF_LIFE_S = 30.17 * _JULIAN_YEAR_S          # ~9.52e8 s
BA137M_HALF_LIFE_S = 2.552 * 60.0                    # Ba-137m metastable daughter
BA130_HALF_LIFE_S = 2.5e21 * _JULIAN_YEAR_S          # 2n double-EC, creation-scale


class EpochProfileId(Enum):
    """The five candidate epoch lanes (match the shell_epoch schema enum)."""

    CS133_FINE_PHASE = "CS133_FINE_PHASE"
    CS137_DECAY_ENVELOPE = "CS137_DECAY_ENVELOPE"
    BA137_DAUGHTER_RATIO = "BA137_DAUGHTER_RATIO"
    BA130_PARENT_FULL = "BA130_PARENT_FULL"
    COMPOSITE_VARIABLE_DEPTH = "COMPOSITE_VARIABLE_DEPTH"


@dataclass(frozen=True)
class IsotopeConstants:
    """Physical constants for a lane — never mixed with source interpretation."""

    isotope: str
    half_life_s: float | None
    hyperfine_hz: float | None
    uncertainty_rel: float


@dataclass(frozen=True)
class SourceOntology:
    """The source's interpretation of a lane — kept apart from the constants."""

    lane_label: str
    observable: str
    interpretation: str


@dataclass(frozen=True)
class EpochProfile:
    """One typed candidate epoch transform. ``proven`` is always False."""

    profile_id: EpochProfileId
    constants: IsotopeConstants
    ontology: SourceOntology
    claim_class: ClaimClass = ClaimClass.OPERATOR_HYPOTHESIS
    evidence_class: str = _r1082.EvidenceClass.DERIVED_MATHEMATICS.value
    proven: bool = field(default=False)

    def __post_init__(self) -> None:
        if self.proven:
            raise R1082ClaimError(
                f"refused: epoch lane {self.profile_id.value} may not be marked "
                f"proven; each isotope lane is a CANDIDATE transform "
                f"(SOURCE_ORIGIN_NOT_VALIDATED, no lane discriminated).")

    def evaluate(self, t_seconds: float) -> dict:
        return _TRANSFORMS[self.profile_id](t_seconds)


# -- the transforms (deterministic; seconds elapsed from EPOCH_ORIGIN) ------

def cs133_fine_phase(t_seconds: float) -> dict:
    """Cs-133 fine phase: fractional cycle count (wraps every cycle)."""
    total_cycles = t_seconds * CS133_HYPERFINE_HZ
    phase = total_cycles - math.floor(total_cycles)
    return {
        "observable": "fine_phase_cycles",
        "phase": phase,
        "total_cycles": total_cycles,
        "uncertainty_rel": 0.0,  # SI-defined frequency
    }


def cs137_decay_envelope(t_seconds: float) -> dict:
    """Cs-137 coarse decay envelope: remaining parent fraction 2**(-t/T)."""
    remaining = 2.0 ** (-t_seconds / CS137_HALF_LIFE_S)
    return {
        "observable": "remaining_fraction",
        "remaining_fraction": remaining,
        "half_life_s": CS137_HALF_LIFE_S,
        "uncertainty_rel": 1.0e-3,
    }


def ba137_daughter_ratio(t_seconds: float) -> dict:
    """Ba-137 daughter/parent ratio accumulated as Cs-137 decays (=1 at T)."""
    remaining = 2.0 ** (-t_seconds / CS137_HALF_LIFE_S)
    ratio = (1.0 - remaining) / remaining if remaining > 0 else math.inf
    return {
        "observable": "daughter_parent_ratio",
        "daughter_parent_ratio": ratio,
        "parent_half_life_s": CS137_HALF_LIFE_S,
        "daughter_half_life_s": BA137M_HALF_LIFE_S,
        "uncertainty_rel": 2.0e-3,
    }


def ba130_parent_full(t_seconds: float) -> dict:
    """Ba-130 parent-full / creation-scale: parent fraction ~1 on human scales."""
    remaining = 2.0 ** (-t_seconds / BA130_HALF_LIFE_S)
    return {
        "observable": "parent_remaining_fraction",
        "remaining_fraction": remaining,
        "half_life_s": BA130_HALF_LIFE_S,
        "creation_scale": True,
        "uncertainty_rel": 5.0e-2,
    }


def composite_variable_depth(t_seconds: float, *, full: bool = True) -> dict:
    """Composite: coarse envelope (+ fine phase for a full-depth packet)."""
    out: dict = {
        "observable": "composite",
        "coarse": cs137_decay_envelope(t_seconds),
    }
    if full:
        out["fine"] = cs133_fine_phase(t_seconds)
    return out


_TRANSFORMS = {
    EpochProfileId.CS133_FINE_PHASE: cs133_fine_phase,
    EpochProfileId.CS137_DECAY_ENVELOPE: cs137_decay_envelope,
    EpochProfileId.BA137_DAUGHTER_RATIO: ba137_daughter_ratio,
    EpochProfileId.BA130_PARENT_FULL: ba130_parent_full,
    EpochProfileId.COMPOSITE_VARIABLE_DEPTH: composite_variable_depth,
}


#: The registry — five distinct candidate lanes, none proven, none selected.
PROFILE_REGISTRY: dict[EpochProfileId, EpochProfile] = {
    EpochProfileId.CS133_FINE_PHASE: EpochProfile(
        EpochProfileId.CS133_FINE_PHASE,
        IsotopeConstants("Cs-133", None, CS133_HYPERFINE_HZ, 0.0),
        SourceOntology("cs133_fine", "fine_phase_cycles",
                       "fine coherent cycle / phase authority")),
    EpochProfileId.CS137_DECAY_ENVELOPE: EpochProfile(
        EpochProfileId.CS137_DECAY_ENVELOPE,
        IsotopeConstants("Cs-137", CS137_HALF_LIFE_S, None, 1.0e-3),
        SourceOntology("cs137_coarse", "remaining_fraction",
                       "coarse exponential decay envelope")),
    EpochProfileId.BA137_DAUGHTER_RATIO: EpochProfile(
        EpochProfileId.BA137_DAUGHTER_RATIO,
        IsotopeConstants("Ba-137", BA137M_HALF_LIFE_S, None, 2.0e-3),
        SourceOntology("ba137_daughter", "daughter_parent_ratio",
                       "daughter ratio / material-age observable")),
    EpochProfileId.BA130_PARENT_FULL: EpochProfile(
        EpochProfileId.BA130_PARENT_FULL,
        IsotopeConstants("Ba-130", BA130_HALF_LIFE_S, None, 5.0e-2),
        SourceOntology("ba130_parent", "parent_remaining_fraction",
                       "parent-full / creation-scale origin candidate")),
    EpochProfileId.COMPOSITE_VARIABLE_DEPTH: EpochProfile(
        EpochProfileId.COMPOSITE_VARIABLE_DEPTH,
        IsotopeConstants("Cs-137+Cs-133", CS137_HALF_LIFE_S,
                         CS133_HYPERFINE_HZ, 1.0e-3),
        SourceOntology("composite", "composite",
                       "variable-depth coarse envelope + fine phase")),
}


def get_profile(profile_id: EpochProfileId) -> EpochProfile:
    """Return one candidate lane, or refuse an unknown id."""
    try:
        return PROFILE_REGISTRY[profile_id]
    except KeyError:
        raise R1082ClaimError(
            f"unknown epoch profile {profile_id!r}.") from None


def refuse_lane_selected(*_a, **_k) -> None:
    """Refuse any silent selection of one isotope lane as the epoch."""
    raise R1082ClaimError(
        "refused: no single isotope lane is discriminated or proven; the "
        "epoch registry reports all candidate lanes side by side. Selecting "
        "one silently would assert an unvalidated source epoch.")


def compare_profiles(t_seconds: float) -> dict:
    """Report every candidate lane side by side — never selects one.

    Returns each lane's isotope constants, source ontology, and evaluated
    observable at ``t_seconds``, plus an explicit ``selected: None``.
    """
    lanes = {}
    for pid, profile in PROFILE_REGISTRY.items():
        lanes[pid.value] = {
            "isotope_constants": {
                "isotope": profile.constants.isotope,
                "half_life_s": profile.constants.half_life_s,
                "hyperfine_hz": profile.constants.hyperfine_hz,
                "uncertainty_rel": profile.constants.uncertainty_rel,
            },
            "source_ontology": {
                "lane_label": profile.ontology.lane_label,
                "observable": profile.ontology.observable,
                "interpretation": profile.ontology.interpretation,
            },
            "claim_class": profile.claim_class.value,
            "evidence_class": profile.evidence_class,
            "proven": profile.proven,
            "value": profile.evaluate(t_seconds),
        }
    return {
        "t_seconds": t_seconds,
        "epoch_origin": EPOCH_ORIGIN,
        "lanes": lanes,
        "selected": None,  # no lane chosen (requirement 5)
        "note": "candidate lanes reported side by side; none discriminated.",
    }


def build_certificate(profile_id: EpochProfileId, t_seconds: float, *,
                      conventional_epoch: dict) -> dict:
    """Build a compressed-epoch certificate; the conventional timestamp is mandatory.

    Refuses if ``conventional_epoch`` is missing or does not carry a valid
    UTC/TAI/TT/TDB timescale and value — the conventional timestamp stays
    mandatory even when a compressed source epoch is used.
    """
    if not conventional_epoch:
        raise R1082ClaimError(
            "refused: a conventional UTC/TAI/TT/TDB timestamp is mandatory in "
            "the certificate even when a compressed source epoch is used.")
    ts = conventional_epoch.get("timescale")
    if ts not in TIMESCALES or not conventional_epoch.get("value"):
        raise R1082ClaimError(
            f"refused: conventional_epoch timescale must be one of "
            f"{sorted(TIMESCALES)} with a value, got {conventional_epoch!r}.")
    profile = get_profile(profile_id)
    return {
        "conventional_epoch": dict(conventional_epoch),  # MANDATORY
        "compressed_epoch": {
            "profile": profile_id.value,
            "payload": profile.evaluate(t_seconds),
        },
        "isotope_constants": {  # separate field
            "isotope": profile.constants.isotope,
            "half_life_s": profile.constants.half_life_s,
            "hyperfine_hz": profile.constants.hyperfine_hz,
            "uncertainty_rel": profile.constants.uncertainty_rel,
        },
        "source_ontology": {  # separate field
            "lane_label": profile.ontology.lane_label,
            "observable": profile.ontology.observable,
            "interpretation": profile.ontology.interpretation,
        },
        "claim_class": profile.claim_class.value,
        "evidence_class": profile.evidence_class,
        "proven": profile.proven,
        "epoch_origin": EPOCH_ORIGIN,
    }


def epoch_profiles_report() -> dict:
    """P12 declaration receipt. Candidate lanes only; none proven or selected."""
    return {
        "phase_id": "P12",
        "tranche": "T03",
        "what_this_is": (
            "a registry of five typed, separate candidate epoch transforms "
            "(Cs-133 fine phase, Cs-137 decay envelope, Ba-137 daughter ratio, "
            "Ba-130 parent-full, composite); conventional UTC/TAI/TT/TDB "
            "timestamps stay mandatory; lanes reported side by side, none "
            "selected or proven."),
        "profiles": [p.value for p in EpochProfileId],
        "timescales": sorted(TIMESCALES),
        "conventional_timestamp_mandatory": True,
        "no_lane_selected": True,
        "no_lane_proven": True,
        "evidence_class": _r1082.EvidenceClass.DERIVED_MATHEMATICS.value,
        "claim_class": ClaimClass.OPERATOR_HYPOTHESIS.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "GREEN_R10_8_2_P12_CS-BA_EPOCH_PROFILE_REGISTRY",
        "what_this_does_not_say": (
            "Each isotope lane is a candidate transform, not a proven epoch; "
            "no lane is discriminated and the source epoch origin remains "
            "NOT_VALIDATED. Conventional timestamps remain mandatory."),
    }
