"""P27 — Search-space and description-length ledger.

An honest reader must be able to see **how much freedom** was spent to obtain a
candidate map, and weigh it against how little **evidence** constrains it. This
module counts the actual search space and description length behind every
candidate, and compares the degrees of freedom against the number of sealed
anchors (only **two**).

It counts the selectable axes:

* **spatialization families** tried (the bounded ensemble, 4 — of which
  ``F1`` and ``F3`` are indistinguishable under the default root, so the number
  of *distinguishable* families is smaller: surfaced explicitly);
* **continuous parameters** fitted (the orientation angle — one per family);
* **Wilkes centroid** candidate profiles, **epoch** profiles, and **codec /
  centroid** profile alternatives.

From those it computes the **total bits of selection freedom** (the log2 of the
discrete alternatives plus the quantised continuous-angle bits) and, per
candidate, a **description length** in bits (the selection index plus the
five-token route payload). It then compares the degrees of freedom against the
2 sealed anchors so the weakness of the constraint is not hidden.

Finally it **separates** four kinds of accounting that must never be conflated:
exact arithmetic (the codec bijection, zero fitted freedom), calibration fit
(the orientation angle against 2 anchors), holdout prediction, and destination
catalogue proximity (explicitly **not** rewarded).

Nothing here is measured or physical; a candidate remains a
``CALIBRATED_CANDIDATE`` at most.

    SOURCE_ORIGIN_NOT_VALIDATED
    PHYSICAL_VALIDATION_NOT_CLAIMED
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence, Tuple

from cwatlas.r1082 import claims, spatialization, wilkes
from cwatlas.r1082.candidate_ensemble import DEFAULT_EPOCH_PROFILES

LEDGER_ID = "CW-R1082-SEARCH-LEDGER"
LEDGER_VERSION = "1.0.0"

#: The number of sealed training anchors that constrain the whole fit.
SEALED_ANCHORS = 2

#: Continuous parameters fitted per family (the orientation angle only).
CONTINUOUS_PARAMS_PER_FAMILY = 1

#: The quantisation used to give the continuous orientation angle a finite
#: description length. One degree over the full turn -> log2(360) bits. Declared
#: so the "continuous" freedom is counted honestly, not hidden as free.
ANGLE_QUANTISATION_DEG = 1.0
ANGLE_RANGE_DEG = 360.0

#: The centroid / codec profile alternatives available to a candidate map. The
#: codec family is fixed (1); the centroid alternative is the Wilkes ensemble
#: (counted separately). Kept explicit for the ledger.
CODEC_PROFILE_ALTERNATIVES = 1


def _log2(n: int) -> float:
    """log2 of a positive count (0.0 for a single, forced choice)."""
    return math.log2(n) if n > 0 else 0.0


def _angle_bits() -> float:
    """Bits to describe the fitted orientation angle at the declared quantum."""
    steps = ANGLE_RANGE_DEG / ANGLE_QUANTISATION_DEG
    return math.log2(steps)


def _route_payload_bits() -> float:
    """Bits carried by a five-token base-100 route (the map input payload)."""
    return spatialization.ROUTE_TOKENS * math.log2(spatialization.TOKEN_BASE)


def distinguishable_family_count() -> int:
    """Distinct families under the default root (``F1 ≡ F3`` collapse to one).

    ``F3_CANONICAL_ROOTREL_BE`` uses the same token/digit order as
    ``F1_CANONICAL_DIRECT_BE`` and, at the default root face 0, the root-relative
    offset is the identity — so the two are indistinguishable. The ledger reports
    the *nominal* count (4) and this smaller distinguishable count together.
    """
    seen = set()
    for f in spatialization.FAMILIES:
        # The distinguishing signature at the default root: token order, digit
        # order, and the effective face offset (0 for DIRECT and for
        # ROOT_RELATIVE at root face 0).
        offset = (f.root_face % spatialization.FACE_COUNT
                  if f.face_entry == "ROOT_RELATIVE" else 0)
        seen.add((tuple(f.token_order), f.digit_order, offset))
    return len(seen)


@dataclass(frozen=True)
class SearchSpaceLedger:
    """The counted search space and its selection-freedom bits."""

    family_count: int
    distinguishable_families: int
    continuous_params: int
    wilkes_candidates: int
    epoch_profiles: int
    codec_profile_alternatives: int
    sealed_anchors: int

    def discrete_alternatives(self) -> int:
        """The product of the discrete selectable alternatives."""
        return (self.family_count * self.wilkes_candidates
                * self.epoch_profiles * self.codec_profile_alternatives)

    def discrete_selection_bits(self) -> float:
        """log2 of the discrete alternatives (index bits to pick one map)."""
        return (_log2(self.family_count) + _log2(self.wilkes_candidates)
                + _log2(self.epoch_profiles)
                + _log2(self.codec_profile_alternatives))

    def continuous_bits(self) -> float:
        """Quantised bits of the fitted continuous parameter(s)."""
        return self.continuous_params * _angle_bits()

    def total_selection_bits(self) -> float:
        """Total bits of selection freedom (discrete index + continuous fit)."""
        return self.discrete_selection_bits() + self.continuous_bits()

    def degrees_of_freedom(self) -> int:
        """The number of free axes: discrete selection axes + continuous params.

        Counts each discrete axis that has more than one alternative, plus each
        fitted continuous parameter.
        """
        dof = self.continuous_params
        for n in (self.family_count, self.wilkes_candidates,
                  self.epoch_profiles, self.codec_profile_alternatives):
            if n > 1:
                dof += 1
        return dof

    def dof_vs_anchors(self) -> dict:
        """Compare the degrees of freedom against the 2 sealed anchors.

        Surfaces the honest reading: with only two anchors and this many free
        axes, the constraint is weak and the fit is (near-)underdetermined.
        """
        dof = self.degrees_of_freedom()
        return {
            "degrees_of_freedom": dof,
            "sealed_anchors": self.sealed_anchors,
            "dof_at_least_anchors": dof >= self.sealed_anchors,
            "constraint_is_weak": dof >= self.sealed_anchors,
            "note": (
                f"{dof} free axes are constrained by only {self.sealed_anchors} "
                f"sealed anchors: the map is weakly constrained and cannot be "
                f"treated as a measured fact."),
        }

    def to_dict(self) -> dict:
        return {
            "family_count": self.family_count,
            "distinguishable_families": self.distinguishable_families,
            "continuous_params": self.continuous_params,
            "wilkes_candidates": self.wilkes_candidates,
            "epoch_profiles": self.epoch_profiles,
            "codec_profile_alternatives": self.codec_profile_alternatives,
            "sealed_anchors": self.sealed_anchors,
            "discrete_alternatives": self.discrete_alternatives(),
            "discrete_selection_bits": self.discrete_selection_bits(),
            "continuous_bits": self.continuous_bits(),
            "total_selection_bits": self.total_selection_bits(),
            "degrees_of_freedom": self.degrees_of_freedom(),
            "dof_vs_anchors": self.dof_vs_anchors(),
        }


def build_ledger(*, epoch_profiles: Sequence[float] = DEFAULT_EPOCH_PROFILES
                 ) -> SearchSpaceLedger:
    """Build the ledger from the live ensemble, family, and epoch counts."""
    ensemble = wilkes.default_ensemble()
    return SearchSpaceLedger(
        family_count=spatialization.FAMILY_COUNT,
        distinguishable_families=distinguishable_family_count(),
        continuous_params=CONTINUOUS_PARAMS_PER_FAMILY,
        wilkes_candidates=len(ensemble.profiles),
        epoch_profiles=len(tuple(epoch_profiles)),
        codec_profile_alternatives=CODEC_PROFILE_ALTERNATIVES,
        sealed_anchors=SEALED_ANCHORS,
    )


def description_length_bits(ledger: SearchSpaceLedger) -> float:
    """Per-candidate description length in bits.

    The cost to describe one candidate map: the selection index that picks the
    (family, Wilkes candidate, epoch) combination and the fitted angle, plus the
    five-token route payload the map consumes.
    """
    return ledger.total_selection_bits() + _route_payload_bits()


@dataclass(frozen=True)
class CandidateDescription:
    """A per-candidate description-length figure and its accounting."""

    candidate_id: str
    selection_bits: float
    route_payload_bits: float
    description_length_bits: float

    def to_dict(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "selection_bits": self.selection_bits,
            "route_payload_bits": self.route_payload_bits,
            "description_length_bits": self.description_length_bits,
        }


def describe_candidate(candidate_id: str,
                       ledger: SearchSpaceLedger) -> CandidateDescription:
    """The description length of one named candidate under the ledger."""
    sel = ledger.total_selection_bits()
    payload = _route_payload_bits()
    return CandidateDescription(
        candidate_id=candidate_id,
        selection_bits=sel,
        route_payload_bits=payload,
        description_length_bits=sel + payload,
    )


def constraint_accounting() -> dict:
    """Separate the four kinds of accounting that must never be conflated."""
    return {
        "exact_arithmetic": {
            "what": "the codec route <-> (face, octal path) bijection",
            "fitted_freedom_bits": 0.0,
            "evidence_class": claims.EvidenceClass.DERIVED_MATHEMATICS.value,
        },
        "calibration_fit": {
            "what": "the orientation angle fitted against the 2 sealed anchors",
            "fitted_continuous_params": CONTINUOUS_PARAMS_PER_FAMILY,
            "sealed_anchors": SEALED_ANCHORS,
            "evidence_class": claims.EvidenceClass.CALIBRATED_CANDIDATE.value,
        },
        "holdout_prediction": {
            "what": "scoring sealed holdouts after the freeze (P25/P28)",
            "evidence_class": claims.EvidenceClass.CALIBRATED_CANDIDATE.value,
        },
        "destination_catalogue_proximity": {
            "what": "landing near an unsealed famous place",
            "rewarded": False,
            "evidence_class": "NOT_EVIDENCE",
        },
    }


def refuse_candidate_as_measured(*_a, **_k) -> None:
    """A ledger entry is bookkeeping; a candidate is never a measured fact."""
    claims.refuse_candidate_as_measured()


def search_ledger_report() -> dict:
    """P27 declaration receipt. Counts the freedom; DOF >= anchors surfaced."""
    ledger = build_ledger()
    dl = description_length_bits(ledger)
    dof = ledger.dof_vs_anchors()
    return {
        "phase_id": "P27",
        "tranche": "T07",
        "what_this_is": (
            "the search-space and description-length ledger: it counts the "
            "families tried, the continuous orientation angle fitted, the "
            "Wilkes/epoch/codec profile alternatives, and the total bits of "
            "selection freedom; it compares the degrees of freedom against the "
            "2 sealed anchors so the weakness of the constraint is visible, and "
            "gives a per-candidate description length."),
        "ledger_id": LEDGER_ID,
        "ledger_version": LEDGER_VERSION,
        "search_space": ledger.to_dict(),
        "description_length_bits_per_candidate": dl,
        "degrees_of_freedom": dof["degrees_of_freedom"],
        "sealed_anchors": SEALED_ANCHORS,
        "dof_at_least_anchors": dof["dof_at_least_anchors"],
        "constraint_is_weak": dof["constraint_is_weak"],
        "family_indistinguishability_note": (
            "F1 and F3 are indistinguishable at the default root; nominal "
            f"family_count={ledger.family_count}, distinguishable="
            f"{ledger.distinguishable_families}"),
        "constraint_accounting": constraint_accounting(),
        "famous_place_proximity_rewarded": False,
        "negative_results": [
            "The degrees of freedom exceed or equal the 2 sealed anchors, so the "
            "map is weakly constrained: an honest reader cannot treat any "
            "candidate as a measured fact.",
            "Two of the four nominal families (F1, F3) are indistinguishable at "
            "the default root, so the effective family search is even smaller "
            "and no family is uniquely selected by the anchors.",
            "Proximity to an unsealed famous-place catalogue contributes zero "
            "evidence and is never scored.",
        ],
        "claim_class": claims.EvidenceClass.SOFTWARE_RESULT.value,
        "max_evidence": claims.MAX_CANDIDATE_EVIDENCE.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "R1082_SEARCH_LEDGER_FREEDOM_COUNTED_DOF_GE_ANCHORS_SURFACED",
        "what_this_does_not_say": (
            "The ledger counts freedom and description length; it makes no "
            "candidate a measured fact, validates no source origin, and rewards "
            "no proximity to any catalogue. It exists to show, honestly, how "
            "weakly two anchors constrain the search."),
    }
