"""WS08 — frozen prospective prediction and null-control registry.

Tamper-evident by construction: a prediction record is frozen by
hashing its canonical JSON together with the freeze commit; any later
edit changes the digest; measurements attach AFTER the freeze and can
never alter the frozen text. Outcome classification is closed-
vocabulary, and no outcome ever upgrades the mechanism claim by
itself.

Non-claims (WS08 spec): a prediction is not evidence before
measurement; a successful prediction does not establish the proposed
mechanism by itself.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from rgcs_lab.common.status_schema import ClaimClass, SchemaError

OUTCOMES = ("PENDING", "HIT", "MISS", "NULL_CONTROL_FAILED",
            "MEASUREMENT_INVALID", "WITHDRAWN")

#: Controls every prediction must declare before freezing.
REQUIRED_CONTROLS = ("sham", "detuned")


def _canonical(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class FrozenPrediction:
    """One frozen prediction. Immutable after construction."""

    prediction_id: str
    hypothesis: str
    observable: str
    predicted_value: str          # value WITH units, as text, exact
    uncertainty: str              # declared band WITH units
    apparatus: str
    analysis_plan: str
    controls: tuple[str, ...]
    freeze_commit: str
    blind_label: str
    digest: str = ""

    def __post_init__(self) -> None:
        for c in REQUIRED_CONTROLS:
            if c not in self.controls:
                raise SchemaError(
                    f"prediction {self.prediction_id!r} missing "
                    f"required control {c!r}: predictions freeze WITH "
                    f"their sham and detuned controls, not before.")
        for fname in ("hypothesis", "observable", "predicted_value",
                      "uncertainty", "apparatus", "analysis_plan",
                      "freeze_commit"):
            if not getattr(self, fname):
                raise SchemaError(f"prediction field {fname!r} is empty")
        object.__setattr__(self, "digest", self.compute_digest())

    def compute_digest(self) -> str:
        payload = {k: v for k, v in self.__dict__.items()
                   if k != "digest"}
        payload["controls"] = list(self.controls)
        return hashlib.sha256(_canonical(payload).encode()).hexdigest()

    def verify(self) -> bool:
        return self.digest == self.compute_digest()


@dataclass(frozen=True)
class MeasurementRecord:
    """A measurement attached AFTER the freeze."""

    prediction_digest: str
    measured_value: str            # with units
    measurement_uncertainty: str   # with units
    instrument_calibration_ref: str
    analysis_notebook_sha256: str
    outcome: str

    def __post_init__(self) -> None:
        if self.outcome not in OUTCOMES:
            raise SchemaError(f"outcome must be one of {OUTCOMES}")
        if self.outcome != "PENDING" and (
                not self.instrument_calibration_ref
                or not self.analysis_notebook_sha256):
            raise SchemaError(
                "a classified outcome requires a calibration reference "
                "and the frozen analysis-notebook hash")


class PredictionRegistry:
    """Append-only registry with tamper checks on every read."""

    def __init__(self) -> None:
        self._frozen: dict[str, FrozenPrediction] = {}
        self._measurements: dict[str, MeasurementRecord] = {}

    def freeze(self, prediction: FrozenPrediction) -> str:
        if prediction.prediction_id in self._frozen:
            raise SchemaError(
                f"prediction {prediction.prediction_id!r} is already "
                f"frozen; freezes are append-only — register a new id.")
        if not prediction.verify():
            raise SchemaError("prediction digest does not verify")
        self._frozen[prediction.prediction_id] = prediction
        return prediction.digest

    def attach_measurement(self, prediction_id: str,
                           record: MeasurementRecord) -> None:
        p = self._frozen.get(prediction_id)
        if p is None:
            raise SchemaError(
                f"no frozen prediction {prediction_id!r}: a measurement "
                f"without a prior freeze is not a prospective test.")
        if record.prediction_digest != p.digest:
            raise SchemaError(
                "measurement references a different prediction digest — "
                "the frozen text may have been altered; refused.")
        if prediction_id in self._measurements:
            raise SchemaError("measurement already attached; append-only")
        self._measurements[prediction_id] = record

    def status(self, prediction_id: str) -> dict:
        p = self._frozen.get(prediction_id)
        if p is None:
            raise SchemaError(f"unknown prediction {prediction_id!r}")
        if not p.verify():
            return {"prediction_id": prediction_id,
                    "state": "TAMPER_DETECTED"}
        m = self._measurements.get(prediction_id)
        outcome = m.outcome if m else "PENDING"
        return {
            "prediction_id": prediction_id,
            "digest": p.digest,
            "freeze_commit": p.freeze_commit,
            "blind_label": p.blind_label,
            "outcome": outcome,
            "claim_class": (ClaimClass.MEASUREMENT.value if m and
                            outcome in ("HIT", "MISS")
                            else ClaimClass.PROSPECTIVE_PREDICTION.value),
            "non_claims": [
                "a prediction is not evidence before measurement",
                "a HIT does not establish the proposed mechanism by "
                "itself",
            ],
        }

    def public_bundle(self) -> dict:
        return {"predictions": [self.status(pid)
                                for pid in sorted(self._frozen)],
                "registry_discipline": "append-only; digests verified "
                                       "on every read; controls frozen "
                                       "with the prediction"}
