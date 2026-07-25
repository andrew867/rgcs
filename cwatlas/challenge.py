"""P54 — Prospective known-destination challenge protocol.

This is the **only** path to :class:`~cwatlas.claims.ClaimClass.CALIBRATED_MAPPING`.
The rule (System Contract invariant 5 / the claim-and-privacy boundary): a
retrospective fit to known anchors is, at most, an ``OPERATOR_HYPOTHESIS``.
Source semantics are promoted to ``CALIBRATED_MAPPING`` only when an operator
*commits* a decode of an **unseen** target **before** the truth is revealed, and
that sealed prediction later scores within tolerance against the revealed truth.

The protocol makes "before" enforceable, not merely asserted:

* **Seal.** The operator commits to a predicted point by publishing a SHA-256
  commitment over ``(target_id, predicted_point, salt)`` at ``commit_epoch``.
  The predicted point is bound but hidden. The target must be flagged unseen.
* **Reveal and score.** The truth is revealed at ``reveal_epoch > commit_epoch``.
  The operator opens the commitment; if the opening does not reproduce the
  sealed commitment the prediction was altered after seeing the truth and the
  challenge is refused. Otherwise the residual is scored, reusing
  :func:`cwatlas.calibration.prospective_challenge`. Passing promotes to
  ``CALIBRATED_MAPPING``; missing keeps it an ``OPERATOR_HYPOTHESIS``.

A reveal at or before the commit epoch is temporally retrospective and is
refused: you cannot commit to a prediction after already knowing the answer.

Deterministic. Epochs are decimal years passed in — never a wall-clock read. No
source vector is claimed to identify a real location.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Sequence, Tuple

from cwatlas import calibration
from cwatlas.claims import ClaimClass, ClaimError
from cwatlas.calibration import CalibrationResult, great_circle_m


class ChallengeError(ValueError):
    """Raised on a malformed challenge, duplicate seal, or bad epoch order."""


class SealError(ClaimError):
    """Raised when a sealed commitment is broken or a prediction is altered.

    Enforces the "commit before reveal" contract structurally.
    """


def refuse_retrospective_challenge(*_a, **_k) -> None:
    """A prediction committed after the truth is not a prospective challenge."""
    raise SealError(
        "refused: the truth epoch is at or before the commit epoch. A "
        "prospective challenge must seal its decode of an unseen target "
        "strictly before the destination is revealed; a prediction made after "
        "the answer is known is retrospective and never promotes to "
        "CALIBRATED_MAPPING.")


def _commitment(target_id: str, predicted_point: Tuple[float, float],
                salt: str) -> str:
    """Deterministic SHA-256 commitment binding target, prediction, and salt."""
    lat, lon = float(predicted_point[0]), float(predicted_point[1])
    blob = f"{target_id}\x1f{lat!r}\x1f{lon!r}\x1f{salt}"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ChallengeSeal:
    """The public commitment published at seal time.

    It reveals only that *some* prediction for ``target_id`` was fixed at
    ``commit_epoch`` — the predicted point stays hidden behind ``commitment``
    until it is opened at reveal.
    """

    target_id: str
    commitment: str
    commit_epoch: float
    unseen: bool


@dataclass(frozen=True)
class ChallengeOutcome:
    """The scored outcome of a revealed prospective challenge."""

    target_id: str
    predicted_point: Tuple[float, float]
    revealed_point: Tuple[float, float]
    residual_m: float
    tolerance_m: float
    commit_epoch: float
    reveal_epoch: float
    commitment_verified: bool
    passed: bool
    promoted: bool
    claim_class: str
    justification: str


class ChallengeProtocol:
    """Stateful holder of sealed decodes awaiting reveal.

    Seals are append-only and one-per-target: a target cannot be re-sealed, so
    an operator cannot quietly issue a second prediction after seeing a hint.
    """

    def __init__(self) -> None:
        self._seals: Dict[str, ChallengeSeal] = {}

    def __len__(self) -> int:
        return len(self._seals)

    @property
    def sealed_targets(self) -> Tuple[str, ...]:
        return tuple(self._seals)

    def seal(self, target_id: str, predicted_point: Tuple[float, float],
             salt: str, commit_epoch: float, *, unseen: bool = True
             ) -> ChallengeSeal:
        """Commit a decode of an unseen target before the truth is known."""
        if not target_id:
            raise ChallengeError("target_id must be a non-empty string.")
        if not salt:
            raise ChallengeError(
                "salt must be a non-empty string so the commitment is binding.")
        if not unseen:
            raise ChallengeError(
                "refused: the target must be unseen for a prospective "
                "challenge; a seen (training) target cannot be challenged.")
        if not math.isfinite(commit_epoch):
            raise ChallengeError("commit_epoch must be finite.")
        lat, lon = float(predicted_point[0]), float(predicted_point[1])
        if not (math.isfinite(lat) and math.isfinite(lon)):
            raise ChallengeError("predicted_point must be two finite floats.")
        if not (-90.0 <= lat <= 90.0):
            raise ChallengeError(f"latitude must be in [-90, 90], got {lat}.")
        if target_id in self._seals:
            raise ChallengeError(
                f"refused: target {target_id!r} is already sealed; a target may "
                f"be committed only once so predictions cannot be revised.")
        seal = ChallengeSeal(
            target_id=target_id,
            commitment=_commitment(target_id, (lat, lon), salt),
            commit_epoch=float(commit_epoch),
            unseen=True,
        )
        self._seals[target_id] = seal
        return seal

    def reveal_and_score(self, target_id: str,
                         opening_point: Tuple[float, float], opening_salt: str,
                         revealed_point: Tuple[float, float],
                         tolerance_m: float, reveal_epoch: float,
                         training_anchors: "Optional[calibration.SealedAnchorSet]" = None,
                         ) -> ChallengeOutcome:
        """Open the seal, verify the commitment, then score against the truth.

        Refuses if the reveal is not strictly after the commit (retrospective),
        or if the opening does not reproduce the sealed commitment (the
        prediction was altered after the truth was seen).
        """
        if target_id not in self._seals:
            raise ChallengeError(f"no sealed decode for target {target_id!r}.")
        seal = self._seals[target_id]
        if not math.isfinite(reveal_epoch):
            raise ChallengeError("reveal_epoch must be finite.")
        if reveal_epoch <= seal.commit_epoch:
            refuse_retrospective_challenge()
        if not (math.isfinite(tolerance_m) and tolerance_m > 0.0):
            raise ChallengeError("tolerance_m must be positive and finite.")

        opened = (float(opening_point[0]), float(opening_point[1]))
        if _commitment(target_id, opened, opening_salt) != seal.commitment:
            raise SealError(
                "refused: the opening does not reproduce the sealed "
                "commitment. The committed prediction cannot be changed after "
                "the destination is revealed.")

        revealed = (float(revealed_point[0]), float(revealed_point[1]))
        residual = great_circle_m(opened, revealed)
        passed = residual <= tolerance_m
        if passed:
            claim = ClaimClass.CALIBRATED_MAPPING.value
            why = ("prospective known-destination challenge passed: sealed "
                   f"decode within tolerance ({residual:.1f} m <= "
                   f"{tolerance_m:.1f} m); promoted to CALIBRATED_MAPPING.")
        else:
            claim = ClaimClass.OPERATOR_HYPOTHESIS.value
            why = ("prospective challenge missed tolerance "
                   f"({residual:.1f} m > {tolerance_m:.1f} m); remains an "
                   f"OPERATOR_HYPOTHESIS.")
        return ChallengeOutcome(
            target_id=target_id,
            predicted_point=opened,
            revealed_point=revealed,
            residual_m=residual,
            tolerance_m=float(tolerance_m),
            commit_epoch=seal.commit_epoch,
            reveal_epoch=float(reveal_epoch),
            commitment_verified=True,
            passed=passed,
            promoted=passed,
            claim_class=claim,
            justification=why,
        )


def seal_from_calibration(protocol: ChallengeProtocol,
                          calibration_result: CalibrationResult,
                          target_id: str,
                          challenge_source_vector: Sequence[float],
                          salt: str, commit_epoch: float,
                          ) -> Tuple[ChallengeSeal, Tuple[float, float]]:
    """Decode an unseen target with a frozen calibration and seal the result.

    Returns the seal (public) and the opening prediction (the operator keeps
    this until reveal). The calibration must already be frozen; a decode from an
    unfrozen calibration is refused as retrospective.
    """
    if not calibration_result.frozen:
        calibration.refuse_retrospective_fit_as_calibrated()
    predicted = calibration_result.predict(challenge_source_vector)
    seal = protocol.seal(target_id, predicted, salt, commit_epoch, unseen=True)
    return seal, predicted


def challenge_report() -> dict:
    """P54 declaration receipt."""
    return {
        "phase_id": "P54",
        "what_this_is": (
            "the prospective known-destination challenge protocol: seal a "
            "decode of an unseen target (SHA-256 commitment) before the truth "
            "is revealed, then open and score it; passing is the only path to "
            "CALIBRATED_MAPPING."),
        "only_path_to_calibrated_mapping": True,
        "retrospective_fit_promotes": False,
        "claim_class": ClaimClass.OPERATOR_HYPOTHESIS.value,
        "promoted_claim_class": ClaimClass.CALIBRATED_MAPPING.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "PROSPECTIVE_CHALLENGE_SEALED_COMMIT_BEFORE_REVEAL",
        "what_this_does_not_say": (
            "A passed prospective challenge calibrates a source-semantics "
            "transform within a declared tolerance; it does not prove any "
            "individual source vector identifies a real location, nor does it "
            "claim any physical validation. A retrospective fit never promotes."),
    }
