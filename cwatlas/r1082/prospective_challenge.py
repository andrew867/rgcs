"""P28 — Prospective bidirectional challenge.

A model that can only be confirmed is not a scientific model. This phase defines
a challenge that can **fail cleanly** after the release is frozen: a prospective,
bidirectional, sealed test over anchors that were **not** used in fitting.

The protocol commits, *before reveal*, to everything that decides the outcome —
the frozen profile, the software version, the scoring rule, and the tolerance —
and seals a cryptographic commitment to the held-back *actual* answer. Only then
is the actual revealed and scored. Two directions are supported:

* **vector → place.** A future anchor's source vector is decoded by the frozen
  profile into a predicted pin (and alias candidates); the predicted pin is
  compared to the actual public coordinate by great-circle distance against the
  sealed tolerance.
* **place → vector.** A future anchor's public coordinate is inverse-geocoded by
  the frozen profile into a predicted source vector; the predicted route is
  compared to the actual route.

Outcomes are graded: :data:`ChallengeOutcome.SUCCESS`, ``PARTIAL_SUCCESS``,
``ALIAS_SET_SUCCESS`` (the actual matches one of the bounded alias candidates),
and ``FAILURE``. **Failure is reachable**: a prediction that misses the actual by
more than the tolerance fails, and the reveal step refuses a swapped actual
(the commitment would not verify). The checker is deliberately *not* rigged to
always pass.

A predicted pin or route is a ``CALIBRATED_CANDIDATE`` at most — never a measured
fact, never a validated source origin. See :mod:`cwatlas.r1082.claims`.

    SOURCE_ORIGIN_NOT_VALIDATED
    PHYSICAL_VALIDATION_NOT_CLAIMED
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from cwatlas.r1082 import claims, route_core
from cwatlas.r1082.geocode_forward import (
    default_frozen_stub,
    geocode,
    single_family_stub,
)
from cwatlas.r1082.geocode_inverse import inverse_geocode

MODULE_ID = "CW-R1082-CHALLENGE"
MODULE_VERSION = "1.0.0"
SOFTWARE_VERSION = f"{MODULE_ID}/{MODULE_VERSION}"

#: Mean spherical Earth radius (km) for the great-circle scoring metric.
EARTH_MEAN_RADIUS_KM = 6371.0088

#: A fixed, conventional creation timestamp. Passed in everywhere; a
#: deterministic default, never a wall-clock read.
DEFAULT_CREATED_AT = "2026-07-25T00:00:00Z"

#: Defaults for the sealed scoring rule.
DEFAULT_TOLERANCE_KM = 50.0
DEFAULT_PARTIAL_FACTOR = 3.0
DEFAULT_SHELL = 3
DEFAULT_FAMILY = "F1_CANONICAL_DIRECT_BE"


class ChallengeError(RuntimeError):
    """Raised on a malformed challenge or a broken pre-reveal commitment."""


class ChallengeDirection(Enum):
    """The two sealed challenge directions."""

    VECTOR_TO_PLACE = "VECTOR_TO_PLACE"
    PLACE_TO_VECTOR = "PLACE_TO_VECTOR"


class ChallengeOutcome(Enum):
    """The graded outcome of a scored challenge."""

    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    ALIAS_SET_SUCCESS = "ALIAS_SET_SUCCESS"
    FAILURE = "FAILURE"


#: Outcomes that count as passing the challenge (a clean prediction).
PASSING_OUTCOMES = frozenset({ChallengeOutcome.SUCCESS,
                              ChallengeOutcome.ALIAS_SET_SUCCESS})


def great_circle_km(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """Great-circle distance (km) between two ``(lat_deg, lon_deg)`` points."""
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = (math.sin(dlat / 2.0) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2)
    return 2.0 * EARTH_MEAN_RADIUS_KM * math.asin(min(1.0, math.sqrt(h)))


def _sha256_obj(obj) -> str:
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=float)
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _canonical_actual(direction: ChallengeDirection, actual) -> dict:
    """A canonical, hashable view of a held-back actual answer."""
    if direction is ChallengeDirection.VECTOR_TO_PLACE:
        lat, lon = float(actual[0]), float(actual[1])
        return {"kind": "PLACE", "lat_deg": round(lat, 9),
                "lon_deg": round(lon, 9)}
    tokens = route_core.parse_five_token(str(actual)).tokens
    return {"kind": "VECTOR", "tokens": list(tokens)}


def seal_actual(direction: ChallengeDirection, actual) -> str:
    """Cryptographic commitment to the held-back actual (sealed before reveal)."""
    return _sha256_obj(_canonical_actual(direction, actual))


@dataclass(frozen=True)
class ChallengeSpec:
    """A sealed challenge: everything that decides the outcome, frozen up front.

    The ``sealed_actual_hash`` commits to the held-back answer so it cannot be
    swapped after the profile/software/scoring/tolerance are frozen.
    """

    challenge_id: str
    direction: ChallengeDirection
    profile_id: str
    profile_stub_family: str
    shell: int
    tolerance_km: float
    partial_factor: float
    sealed_actual_hash: str
    challenge_input: dict
    scoring: str = "GREAT_CIRCLE_KM_VS_TOLERANCE"
    software_version: str = SOFTWARE_VERSION
    created_at: str = DEFAULT_CREATED_AT

    def canonical(self) -> dict:
        """The canonical, signable spec document (sealed before reveal)."""
        return {
            "challenge_id": self.challenge_id,
            "direction": self.direction.value,
            "profile_id": self.profile_id,
            "profile_stub_family": self.profile_stub_family,
            "shell": self.shell,
            "tolerance_km": self.tolerance_km,
            "partial_factor": self.partial_factor,
            "sealed_actual_hash": self.sealed_actual_hash,
            "challenge_input": self.challenge_input,
            "scoring": self.scoring,
            "software_version": self.software_version,
            "created_at": self.created_at,
        }

    def signature(self) -> str:
        """A deterministic signature over the whole sealed spec."""
        return _sha256_obj(self.canonical())

    def verify_actual(self, revealed_actual) -> None:
        """Refuse a revealed actual that does not match the sealed commitment."""
        got = seal_actual(self.direction, revealed_actual)
        if got != self.sealed_actual_hash:
            raise ChallengeError(
                f"refused: the revealed actual for {self.challenge_id!r} does "
                f"not match the sealed commitment (a swapped actual after the "
                f"freeze is not permitted)")


@dataclass(frozen=True)
class ChallengeResult:
    """The scored outcome of a challenge, with the pass/fail criterion."""

    challenge_id: str
    direction: ChallengeDirection
    outcome: ChallengeOutcome
    passed: bool
    threshold_km: float
    primary_error_km: Optional[float]
    best_error_km: Optional[float]
    predicted: dict
    actual: dict
    result_type: str
    receipt: dict

    def assert_not_measured(self) -> None:
        """A predicted pin/route is a candidate, never a measured fact."""
        claims.refuse_candidate_as_measured(self.result_type)

    def to_dict(self) -> dict:
        return {
            "challenge_id": self.challenge_id,
            "direction": self.direction.value,
            "outcome": self.outcome.value,
            "passed": self.passed,
            "threshold_km": self.threshold_km,
            "primary_error_km": self.primary_error_km,
            "best_error_km": self.best_error_km,
            "predicted": self.predicted,
            "actual": self.actual,
            "result_type": self.result_type,
            "receipt": self.receipt,
        }


def _resolve_profile(spec: ChallengeSpec, frozen_profile):
    """Use the injected frozen profile, or the sealed single-family stub."""
    if frozen_profile is not None:
        return frozen_profile
    return single_family_stub(spec.profile_stub_family)


def _score_vector_to_place(spec: ChallengeSpec, frozen_profile,
                           actual_latlon: Tuple[float, float]) -> ChallengeResult:
    source_vector = str(spec.challenge_input["source_vector"])
    fg = geocode(source_vector, frozen_profile, shell=spec.shell, body="EARTH")

    tol = spec.tolerance_km
    if not fg.is_candidate() or not fg.candidates:
        return _build_result(
            spec, ChallengeOutcome.FAILURE, tol, None, None,
            predicted={"result_type": fg.result_type, "candidates": []},
            actual={"lat_deg": actual_latlon[0], "lon_deg": actual_latlon[1]},
            result_type=fg.result_type)

    primary = fg.candidates[0]
    primary_err = great_circle_km(
        actual_latlon, (primary.latitude_deg, primary.longitude_deg))
    errs = [great_circle_km(actual_latlon, (c.latitude_deg, c.longitude_deg))
            for c in fg.candidates]
    best_err = min(errs)

    if primary_err <= tol:
        outcome = ChallengeOutcome.SUCCESS
    elif best_err <= tol:
        outcome = ChallengeOutcome.ALIAS_SET_SUCCESS
    elif primary_err <= tol * spec.partial_factor:
        outcome = ChallengeOutcome.PARTIAL_SUCCESS
    else:
        outcome = ChallengeOutcome.FAILURE

    predicted = {
        "result_type": fg.result_type,
        "primary": {"lat_deg": primary.latitude_deg,
                    "lon_deg": primary.longitude_deg},
        "candidates": [{"lat_deg": c.latitude_deg, "lon_deg": c.longitude_deg,
                        "family_name": c.family_name} for c in fg.candidates],
    }
    return _build_result(
        spec, outcome, tol, primary_err, best_err, predicted=predicted,
        actual={"lat_deg": actual_latlon[0], "lon_deg": actual_latlon[1]},
        result_type=fg.result_type)


def _score_place_to_vector(spec: ChallengeSpec, frozen_profile,
                           actual_vector: str) -> ChallengeResult:
    lat = float(spec.challenge_input["lat_deg"])
    lon = float(spec.challenge_input["lon_deg"])
    ig = inverse_geocode(lat, lon, spec.shell, frozen_profile, body="EARTH")

    actual_tokens = list(route_core.parse_five_token(str(actual_vector)).tokens)
    predicted_tokens = list(ig.route)
    alias_routes = [list(a["route"]) for a in ig.aliases]

    if predicted_tokens == actual_tokens:
        outcome = ChallengeOutcome.SUCCESS
    elif actual_tokens in alias_routes:
        outcome = ChallengeOutcome.ALIAS_SET_SUCCESS
    else:
        outcome = ChallengeOutcome.FAILURE

    predicted = {
        "result_type": ig.result_type,
        "source_vector": ig.source_vector,
        "route": predicted_tokens,
        "aliases": [{"family_name": a["family_name"], "route": a["route"]}
                    for a in ig.aliases],
    }
    return _build_result(
        spec, outcome, spec.tolerance_km, None, None, predicted=predicted,
        actual={"source_vector": str(actual_vector), "route": actual_tokens},
        result_type=ig.result_type)


def _build_result(spec: ChallengeSpec, outcome: ChallengeOutcome,
                  threshold_km: float, primary_err, best_err, *,
                  predicted: dict, actual: dict,
                  result_type: str) -> ChallengeResult:
    passed = outcome in PASSING_OUTCOMES
    receipt = {
        "module_id": MODULE_ID,
        "module_version": MODULE_VERSION,
        "challenge_id": spec.challenge_id,
        "direction": spec.direction.value,
        "profile_id": spec.profile_id,
        "software_version": spec.software_version,
        "scoring": spec.scoring,
        "threshold_km": threshold_km,
        "spec_signature": spec.signature(),
        "sealed_before_reveal": True,
        "falsifiable": True,
        "max_evidence": claims.MAX_CANDIDATE_EVIDENCE.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "famous_place_proximity_rewarded": False,
    }
    return ChallengeResult(
        challenge_id=spec.challenge_id, direction=spec.direction,
        outcome=outcome, passed=passed, threshold_km=threshold_km,
        primary_error_km=primary_err, best_error_km=best_err,
        predicted=predicted, actual=actual, result_type=result_type,
        receipt=receipt)


def run_challenge(spec: ChallengeSpec, revealed_actual, *,
                  frozen_profile=None) -> ChallengeResult:
    """Score a sealed challenge against the revealed actual.

    Verifies the pre-reveal commitment first (a swapped actual is refused), then
    predicts with the sealed frozen profile/software and scores against the
    sealed tolerance. The outcome may be a clean :data:`ChallengeOutcome.FAILURE`
    — the checker is not rigged to pass.
    """
    spec.verify_actual(revealed_actual)
    profile = _resolve_profile(spec, frozen_profile)
    if spec.direction is ChallengeDirection.VECTOR_TO_PLACE:
        return _score_vector_to_place(spec, profile, revealed_actual)
    return _score_place_to_vector(spec, profile, revealed_actual)


def build_vector_to_place_challenge(
        challenge_id: str, source_vector: str, actual_latlon: Tuple[float, float],
        *, family: str = DEFAULT_FAMILY, shell: int = DEFAULT_SHELL,
        tolerance_km: float = DEFAULT_TOLERANCE_KM,
        partial_factor: float = DEFAULT_PARTIAL_FACTOR,
        created_at: str = DEFAULT_CREATED_AT) -> ChallengeSpec:
    """Seal a vector→place challenge committing to the held-back coordinate."""
    stub = single_family_stub(family)
    return ChallengeSpec(
        challenge_id=challenge_id,
        direction=ChallengeDirection.VECTOR_TO_PLACE,
        profile_id=stub.profile_id, profile_stub_family=family, shell=shell,
        tolerance_km=tolerance_km, partial_factor=partial_factor,
        sealed_actual_hash=seal_actual(
            ChallengeDirection.VECTOR_TO_PLACE, actual_latlon),
        challenge_input={"source_vector": str(source_vector)},
        created_at=created_at)


def build_place_to_vector_challenge(
        challenge_id: str, actual_latlon: Tuple[float, float],
        actual_vector: str, *, family: str = DEFAULT_FAMILY,
        shell: int = DEFAULT_SHELL, tolerance_km: float = DEFAULT_TOLERANCE_KM,
        partial_factor: float = DEFAULT_PARTIAL_FACTOR,
        created_at: str = DEFAULT_CREATED_AT) -> ChallengeSpec:
    """Seal a place→vector challenge committing to the held-back source vector."""
    stub = single_family_stub(family)
    return ChallengeSpec(
        challenge_id=challenge_id,
        direction=ChallengeDirection.PLACE_TO_VECTOR,
        profile_id=stub.profile_id, profile_stub_family=family, shell=shell,
        tolerance_km=tolerance_km, partial_factor=partial_factor,
        sealed_actual_hash=seal_actual(
            ChallengeDirection.PLACE_TO_VECTOR, actual_vector),
        challenge_input={"lat_deg": float(actual_latlon[0]),
                         "lon_deg": float(actual_latlon[1])},
        created_at=created_at)


def challenge_bundle(spec: ChallengeSpec) -> dict:
    """A signed challenge bundle suitable for independent execution."""
    return {
        "bundle_kind": "R1082_PROSPECTIVE_CHALLENGE",
        "module_id": MODULE_ID,
        "module_version": MODULE_VERSION,
        "spec": spec.canonical(),
        "signature": spec.signature(),
        "instructions": (
            "Reveal the actual only after loading this bundle; run_challenge "
            "verifies the sealed commitment, predicts with the sealed profile, "
            "and scores against the sealed tolerance. The result may be a clean "
            "FAILURE."),
        "measured_here": "nothing",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
    }


def verify_bundle(bundle: dict) -> bool:
    """True iff the bundle's signature matches its sealed spec."""
    spec = bundle.get("spec")
    if not isinstance(spec, dict):
        raise ChallengeError("bundle is missing its sealed spec")
    return bundle.get("signature") == _sha256_obj(spec)


def build_synthetic_challenges():
    """A deterministic held-back challenge set that can pass AND fail.

    Returns a list of ``(ChallengeSpec, revealed_actual)`` pairs over synthetic,
    public future anchors that were **not** used in fitting. Self-consistent
    fixtures (the actual derived from the frozen prediction) pass; the adversarial
    fixtures (a deliberately wrong actual) FAIL — proving the protocol can fail.
    """
    family = DEFAULT_FAMILY
    stub = single_family_stub(family)
    pairs = []

    # vector -> place, self-consistent (predicted == actual -> SUCCESS).
    v_src = "246813579"
    fg = geocode(v_src, stub, shell=DEFAULT_SHELL, body="EARTH")
    true_latlon = (fg.candidates[0].latitude_deg, fg.candidates[0].longitude_deg)
    pairs.append((build_vector_to_place_challenge(
        "CHALLENGE_SYN_V2P_PASS", v_src, true_latlon, family=family), true_latlon))

    # vector -> place, adversarial: a coordinate on the far side of the globe.
    wrong_latlon = (-true_latlon[0], ((true_latlon[1] + 180.0 + 180.0) % 360.0)
                    - 180.0)
    pairs.append((build_vector_to_place_challenge(
        "CHALLENGE_SYN_V2P_FAIL", v_src, wrong_latlon, family=family),
        wrong_latlon))

    # place -> vector, self-consistent (predicted route == actual -> SUCCESS).
    p_latlon = (12.5, -34.0)
    ig = inverse_geocode(p_latlon[0], p_latlon[1], DEFAULT_SHELL, stub,
                         body="EARTH")
    pairs.append((build_place_to_vector_challenge(
        "CHALLENGE_SYN_P2V_PASS", p_latlon, ig.source_vector, family=family),
        ig.source_vector))

    # place -> vector, adversarial: a wrong held-back vector -> FAILURE.
    wrong_vector = "0000000001" if ig.source_vector != "0000000001" else \
        "9999999998"
    pairs.append((build_place_to_vector_challenge(
        "CHALLENGE_SYN_P2V_FAIL", p_latlon, wrong_vector, family=family),
        wrong_vector))

    return pairs


def run_synthetic_suite():
    """Run the synthetic held-back set; return per-challenge result dicts."""
    return [run_challenge(spec, actual).to_dict()
            for spec, actual in build_synthetic_challenges()]


def prospective_challenge_report() -> dict:
    """P28 declaration receipt. A falsifiable, sealed, bidirectional challenge."""
    results = run_synthetic_suite()
    outcomes = {r["challenge_id"]: r["outcome"] for r in results}
    any_pass = any(r["passed"] for r in results)
    any_fail = any(r["outcome"] == ChallengeOutcome.FAILURE.value
                   for r in results)
    return {
        "phase_id": "P28",
        "tranche": "T07",
        "what_this_is": (
            "the prospective bidirectional challenge: a sealed, falsifiable test "
            "that freezes the profile, software, scoring, and tolerance and "
            "commits to a held-back actual before reveal, then predicts a future "
            "anchor's pin (vector→place) or source vector (place→vector) and "
            "grades SUCCESS / PARTIAL_SUCCESS / ALIAS_SET_SUCCESS / FAILURE; it "
            "can fail cleanly and refuses a swapped actual."),
        "module_id": MODULE_ID,
        "module_version": MODULE_VERSION,
        "software_version": SOFTWARE_VERSION,
        "directions": [d.value for d in ChallengeDirection],
        "outcomes": [o.value for o in ChallengeOutcome],
        "scoring": "GREAT_CIRCLE_KM_VS_TOLERANCE",
        "default_tolerance_km": DEFAULT_TOLERANCE_KM,
        "sealed_before_reveal": True,
        "falsifiable": True,
        "swapped_actual_refused": True,
        "synthetic_suite_outcomes": outcomes,
        "synthetic_suite_has_pass": any_pass,
        "synthetic_suite_has_failure": any_fail,
        "famous_place_proximity_rewarded": False,
        "negative_results": [
            "The synthetic held-back suite contains fixtures that FAIL: a "
            "prediction that misses the sealed actual by more than the tolerance "
            "yields a clean FAILURE, and a swapped actual is refused at reveal. "
            "The challenge is genuinely falsifiable, not rigged to pass.",
        ],
        "claim_class": claims.EvidenceClass.CALIBRATED_CANDIDATE.value,
        "max_evidence": claims.MAX_CANDIDATE_EVIDENCE.value,
        "result_class": claims.ResultClass.CANDIDATE_CALIBRATED_POINT.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "R1082_PROSPECTIVE_BIDIRECTIONAL_CHALLENGE_FALSIFIABLE_SEALED",
        "what_this_does_not_say": (
            "A predicted pin or route is a CALIBRATED_CANDIDATE under a declared, "
            "frozen calibration; a passing challenge does not make it a measured "
            "fact or validate the source origin. The challenge exists so the "
            "release can be proven wrong, not so it can be proven right."),
    }
