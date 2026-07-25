"""P19 — Calibration freeze and cryptographic receipt.

Before any holdout is decoded, the retained calibration is **frozen** and sealed
with a SHA-256 receipt conforming to ``schemas/calibration_receipt.schema.json``.
The receipt seals, together:

* the locked ``EARTH_ROOT_D_V1`` root profile id;
* the seven :data:`cwatlas.r1082.claims.FROZEN_PARAMETERS` at their locked
  values (grid rotation, handedness, root feature, topology, tokenisation,
  destination label split, epoch choice);
* the two training-anchor hashes (Wilkes fixed root + Stonehenge);
* the fitted parameters (orientation angle per retained family) and the retained
  alias set from P18;
* ``retuning_forbidden = true``.

Two disciplines are enforced (System Contract "No result shopping"):

* **Freeze precedes holdout scoring.** A :class:`CalibrationSession` refuses to
  score any holdout until :meth:`CalibrationSession.freeze` has been called
  (:class:`CalibrationOrderError`).
* **No post-freeze retuning.** After the freeze, changing any frozen parameter
  routes through :func:`cwatlas.r1082.claims.refuse_post_output_retuning`; a new
  configuration is only expressible as a *new* profile id.

The decoder's source-map mode requires a valid freeze receipt
(:func:`require_valid_receipt`). Nothing here is measured or physical; the
``created_at`` timestamp is passed in, never read from a wall clock.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Optional, Tuple

from cwatlas.r1082 import (
    calibration_fit,
    claims,
    config_authority,
    stonehenge_anchor,
    wilkes,
)
from cwatlas.r1082.partition import build_partition

#: The frozen root profile id and the receipt schema/version identity.
PROFILE_ID = "EARTH_ROOT_D_V1"
RECEIPT_VERSION = "1.0.0"
CODEC_FAMILY = "CW-R1082-SPATIALIZE"

#: A fixed, conventional freeze timestamp (ISO-8601). Passed in everywhere; this
#: constant is only a deterministic default (never a wall-clock read).
DEFAULT_FROZEN_AT = "2026-07-25T00:00:00Z"


class CalibrationFreezeError(RuntimeError):
    """Raised on an invalid freeze receipt or a malformed freeze."""


class CalibrationOrderError(RuntimeError):
    """Raised when a holdout is scored before the calibration is frozen."""


def _sha256_obj(obj) -> str:
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=float)
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _frozen_parameter_values(auth: config_authority.ConfigurationAuthority,
                             epoch_choice: float) -> dict:
    """Map the seven FROZEN_PARAMETERS onto their locked ADR values."""
    d = auth  # decisions accessor
    return {
        "grid_rotation": d.decision("orientation_pole").value,       # SOUTH_UP
        "handedness": d.decision("positive_rotation").value,          # CLOCKWISE
        "root_feature": d.decision("root_feature").value,
        "topology": d.decision("partition").value,
        "tokenization": d.decision("route_core").value,
        "destination_label_split": d.decision("semantic_address").value,
        "epoch_choice": epoch_choice,
    }


@dataclass(frozen=True)
class FrozenCalibration:
    """A sealed, hashed calibration receipt for ``EARTH_ROOT_D_V1``.

    Immutable. :meth:`receipt` renders the schema-conforming document;
    :meth:`verify` recomputes the freeze hash; :meth:`refuse_retune` refuses any
    post-freeze parameter change.
    """

    receipt_id: str
    created_at: str
    frozen_parameters: dict
    fitted_parameters: dict
    retained_families: Tuple[str, ...]
    training_anchor_hashes: Tuple[dict, ...]
    config_freeze_hash: str
    partition_digest: str
    freeze_hash: str
    retuning_forbidden: bool = True

    def receipt(self) -> dict:
        """The ``calibration_receipt.schema.json``-conforming document."""
        return {
            "receipt_id": self.receipt_id,
            "root_profile": PROFILE_ID,
            "training_anchors": list(self.training_anchor_hashes),
            "codec_family": CODEC_FAMILY,
            "parameters": {
                "receipt_version": RECEIPT_VERSION,
                "frozen": self.frozen_parameters,
                "fitted": self.fitted_parameters,
                "retained_families": list(self.retained_families),
                "retention": "FULL_RANKED_ALIAS_SET",
                "config_freeze_hash": self.config_freeze_hash,
                "partition_digest": self.partition_digest,
                "family_result_class":
                    claims.ResultClass.CANDIDATE_ALIAS_SET.value,
            },
            "freeze_hash": self.freeze_hash,
            "created_at": self.created_at,
            "retuning_forbidden": True,
        }

    def canonical_seal(self) -> dict:
        """The payload the freeze hash is taken over (excludes the hash)."""
        return {
            "profile_id": PROFILE_ID,
            "receipt_version": RECEIPT_VERSION,
            "frozen_parameters": self.frozen_parameters,
            "fitted_parameters": self.fitted_parameters,
            "retained_families": list(self.retained_families),
            "training_anchor_hashes": list(self.training_anchor_hashes),
            "config_freeze_hash": self.config_freeze_hash,
            "partition_digest": self.partition_digest,
            "created_at": self.created_at,
            "retuning_forbidden": True,
        }

    def verify(self) -> bool:
        """True iff the stored freeze hash matches the canonical seal."""
        return self.freeze_hash == _sha256_obj(self.canonical_seal())

    def refuse_retune(self, parameter: str = "") -> None:
        """Refuse any change to a frozen parameter (no result shopping)."""
        claims.refuse_post_output_retuning(parameter or "a frozen parameter",
                                           frozen=True)

    def orientation_matrix_by_family(self) -> dict:
        """Per-family fitted rotation matrices (about +Z), from sealed thetas.

        The two-anchor fit seals one azimuth per family
        (``fitted_parameters['orientation_theta_deg_by_family']``). Rebuilding
        the rotation here — with the same convention as
        ``calibration_fit._rot_z`` — is what lets the forward geocoder *apply*
        the calibration rather than merely declare it. Reconstruction is
        deterministic and reads only sealed values, so it is not a retune.
        """
        thetas = self.fitted_parameters.get(
            "orientation_theta_deg_by_family", {})
        out = {}
        for name, deg in dict(thetas).items():
            th = math.radians(float(deg))
            c, s = math.cos(th), math.sin(th)
            out[str(name)] = [[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]]
        return out


def freeze_calibration(fit: calibration_fit.CalibrationFit,
                       anchor: Optional[stonehenge_anchor.StonehengeAnchor] = None,
                       ensemble: Optional[wilkes.WilkesEnsemble] = None,
                       *, epoch_choice: float = 2020.0,
                       created_at: str = DEFAULT_FROZEN_AT) -> FrozenCalibration:
    """Freeze a P18 fit into a sealed, hashed :class:`FrozenCalibration`.

    Seals the seven frozen parameters, the two training-anchor hashes, and the
    fitted orientation angle per retained family. Deterministic: a clean
    checkout reproduces the freeze hash.
    """
    if anchor is None:
        anchor = stonehenge_anchor.build_anchor()
    if ensemble is None:
        ensemble = wilkes.default_ensemble()
    auth = config_authority.ConfigurationAuthority.load()

    frozen_parameters = _frozen_parameter_values(auth, epoch_choice)
    retained = fit.retained()  # full ranked alias set (nothing excluded)
    fitted_parameters = {
        "orientation_theta_deg_by_family": {
            f.family_name: f.theta_deg for f in retained},
        "combined_rms_deg_by_family": {
            f.family_name: math.degrees(f.combined_rms_rad)
            for f in retained},
    }
    training_anchor_hashes = (
        {"anchor": "WILKES_FIXED_ROOT",
         "hash": ensemble.ensemble_hash(),
         "selected_id": ensemble.selected_id},
        {"anchor": anchor.fixture_id,
         "hash": anchor.anchor_hash(),
         "route_hash": anchor.route_hash},
    )
    config_freeze_hash = "sha256:" + auth.freeze_hash()
    partition_digest = build_partition().digest()

    seal = {
        "profile_id": PROFILE_ID,
        "receipt_version": RECEIPT_VERSION,
        "frozen_parameters": frozen_parameters,
        "fitted_parameters": fitted_parameters,
        "retained_families": [f.family_name for f in retained],
        "training_anchor_hashes": list(training_anchor_hashes),
        "config_freeze_hash": config_freeze_hash,
        "partition_digest": partition_digest,
        "created_at": created_at,
        "retuning_forbidden": True,
    }
    freeze_hash = _sha256_obj(seal)
    receipt_id = "CALFREEZE-" + freeze_hash.split(":")[1][:16]
    return FrozenCalibration(
        receipt_id=receipt_id,
        created_at=created_at,
        frozen_parameters=frozen_parameters,
        fitted_parameters=fitted_parameters,
        retained_families=tuple(f.family_name for f in retained),
        training_anchor_hashes=training_anchor_hashes,
        config_freeze_hash=config_freeze_hash,
        partition_digest=partition_digest,
        freeze_hash=freeze_hash,
    )


def require_valid_receipt(receipt: dict) -> None:
    """Refuse source-map mode without a valid freeze receipt.

    The decoder calls this before entering source-map mode. A receipt is valid
    only if it names the locked root profile, forbids retuning, and carries a
    freeze hash. Anything else is refused.
    """
    if not isinstance(receipt, dict):
        raise CalibrationFreezeError("source-map mode requires a freeze receipt")
    if receipt.get("root_profile") != PROFILE_ID:
        raise CalibrationFreezeError(
            f"freeze receipt root_profile must be {PROFILE_ID!r}")
    if receipt.get("retuning_forbidden") is not True:
        raise CalibrationFreezeError(
            "freeze receipt must set retuning_forbidden = true")
    if not receipt.get("freeze_hash"):
        raise CalibrationFreezeError("freeze receipt is missing a freeze_hash")


class CalibrationSession:
    """State machine enforcing freeze-before-holdout ordering.

    A fresh session is *unfrozen*: :meth:`score_holdout` refuses until
    :meth:`freeze` is called. After the freeze, retuning any frozen parameter is
    refused (no result shopping).
    """

    def __init__(self, fit: calibration_fit.CalibrationFit) -> None:
        self._fit = fit
        self._frozen: Optional[FrozenCalibration] = None

    @property
    def is_frozen(self) -> bool:
        return self._frozen is not None

    @property
    def frozen(self) -> Optional[FrozenCalibration]:
        return self._frozen

    def freeze(self, *, epoch_choice: float = 2020.0,
               created_at: str = DEFAULT_FROZEN_AT) -> FrozenCalibration:
        """Freeze the calibration (idempotent for the same inputs)."""
        if self._frozen is None:
            self._frozen = freeze_calibration(
                self._fit, epoch_choice=epoch_choice, created_at=created_at)
        return self._frozen

    def retune(self, parameter: str) -> None:
        """Attempt to change a parameter.

        Permitted (a no-op refusal) while still fitting; refused once frozen —
        a post-freeze change mints a new profile id (no result shopping).
        """
        claims.refuse_post_output_retuning(parameter, frozen=self.is_frozen)

    def score_holdout(self, route, family_name: str) -> dict:
        """Score a holdout route — permitted only after the freeze.

        Refuses (:class:`CalibrationOrderError`) if the calibration is not yet
        frozen: freeze must precede holdout scoring so a result cannot be
        reverse-fit to the holdouts.
        """
        if self._frozen is None:
            raise CalibrationOrderError(
                "refused: a holdout may not be scored before the calibration is "
                "frozen. Freeze the retained calibration first (freeze precedes "
                "holdout scoring — no result shopping).")
        return {
            "route": list(route),
            "family_name": family_name,
            "freeze_hash": self._frozen.freeze_hash,
            "result_class": claims.ResultClass.CANDIDATE_CALIBRATED_POINT.value,
            "scored_after_freeze": True,
        }


def calibration_freeze_report() -> dict:
    """P19 declaration receipt. Freeze precedes holdout; no retuning after."""
    fit = calibration_fit.fit_all()
    frozen = freeze_calibration(fit)
    return {
        "phase_id": "P19",
        "tranche": "T05",
        "what_this_is": (
            "the calibration freeze and cryptographic receipt: the retained "
            "alias set is sealed with a SHA-256 receipt over the seven frozen "
            "parameters, the training-anchor hashes, and the fitted orientation "
            "angles; freeze precedes holdout scoring and post-freeze retuning "
            "is refused."),
        "profile_id": PROFILE_ID,
        "receipt_version": RECEIPT_VERSION,
        "receipt_id": frozen.receipt_id,
        "freeze_hash": frozen.freeze_hash,
        "frozen_parameters": list(claims.FROZEN_PARAMETERS),
        "retained_families": list(frozen.retained_families),
        "retuning_forbidden": True,
        "freeze_precedes_holdout": True,
        "post_freeze_retuning": "REFUSED",
        "decoder_requires_receipt": True,
        "receipt_verifies": frozen.verify(),
        "evidence_class": claims.EvidenceClass.CALIBRATED_CANDIDATE.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "CALIBRATION_FROZEN_SHA256_RECEIPT_NO_RESULT_SHOPPING",
        "what_this_does_not_say": (
            "Freezing the calibration fixes the configuration so it cannot be "
            "silently retuned. It does not make any candidate a measured fact "
            "and validates no source origin."),
    }
