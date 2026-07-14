"""rgcs_core.experiments — run/campaign schemas, control-subtracted
analysis, and the engineering merit score (RGCS-M.57..M.58, M.61;
KOS-01/05/13/14 apparatus-contract lessons).

Units: observable Y in the declared campaign unit X; effect sizes
dimensionless; currents in A.

Normative rules baked into the schemas: amplitude and coherence are
separate quantities (KOS-03); nulls adjudicated on amplitude alone are
"amplitude-null, coherence-untested" (D-20); acquisition extends >= 2.5x
past drive-off (KOS-12); artifacts and negative results are registered.
"""

from __future__ import annotations

import math
from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from ..provenance import classified, classification_string, to_jsonable

__all__ = ["SensorChannel", "ApparatusRecord", "RunRecord",
           "control_subtracted_metrics", "merit_score",
           "current_to_electron_rate"]

ELEMENTARY_CHARGE_C = 1.602176634e-19   # exact (SI 2019)


class SensorChannel(BaseModel):
    """One sensor channel (KOS-11 sensor-geometry lesson)."""

    model_config = ConfigDict(frozen=True)

    name: str
    position_mm: float | None = None
    axis: Literal["x", "y", "z", "other"] = "other"
    aperture_mm: float | None = Field(default=None, gt=0.0)
    observable_unit: str = "V"


class ApparatusRecord(BaseModel):
    """Apparatus contract (KOS-01/05/13/14): geometry, drive branch,
    shared-reference declaration, and artifact register are mandatory
    fields of every campaign."""

    model_config = ConfigDict(frozen=True)

    campaign_id: str
    specimen_id: str
    crystal_length_mm: float = Field(gt=0.0)
    drive_branch: Literal["electrode", "coil", "acoustic", "other"]
    drive_position_mm: float | None = None
    sensors: tuple[SensorChannel, ...] = ()
    shared_reference: bool = False
    reference_description: str = ""
    known_artifacts: tuple[str, ...] = ()
    notes: str = ""


class RunRecord(BaseModel):
    """One run: pre-registered observable summary plus controls status.
    Amplitude and coherence are separate fields (KOS-03); a null decided
    on amplitude alone must be labeled amplitude-null/coherence-untested
    (D-20)."""

    model_config = ConfigDict(frozen=True)

    run_id: str
    condition: Literal["configuration", "control"]
    control_kind: Literal["none", "dummy_load", "no_crystal",
                          "detuned"] = "none"
    drive_off_time_s: float | None = None
    acquisition_end_s: float | None = None
    amplitude_summary: float | None = None
    coherence_summary: float | None = None
    coherence_tested: bool = False
    negative_result: bool = False
    negative_result_note: str = ""

    def null_label(self) -> str:
        """D-20 rule: adjudicating a null on amplitude alone is labeled
        'amplitude-null, coherence-untested'."""
        if not self.negative_result:
            return "not-a-null"
        return ("null (amplitude and coherence tested)"
                if self.coherence_tested
                else "amplitude-null, coherence-untested")

    def post_drive_coverage_ok(self) -> bool | None:
        """KOS-12: acquisition must extend >= 2.5x past drive-off."""
        if self.drive_off_time_s is None or self.acquisition_end_s is None:
            return None
        if self.drive_off_time_s <= 0:
            return None
        return self.acquisition_end_s >= 2.5 * self.drive_off_time_s


@classified("Established", registry=("RGCS-M.57",),
            note="d_c is the evidence-bearing quantity; G_c feeds only the "
                 "merit score S")
def control_subtracted_metrics(y_config: np.ndarray | list[float],
                               y_control: np.ndarray | list[float]
                               ) -> dict[str, Any]:
    """Control-subtracted gain and effect size (RGCS-M.57):
    G_c = max(0, (Ybar_cfg - Ybar_ctl)/Ybar_ctl);
    d_c = (Ybar_cfg - Ybar_ctl)/s_pooled, s_pooled^2 = (s_cfg^2+s_ctl^2)/2.
    Controls: dummy-load, no-crystal, or detuned (eps ~ 1.25 convention)."""
    yc = np.asarray(y_config, dtype=float)
    yk = np.asarray(y_control, dtype=float)
    if yc.size < 2 or yk.size < 2:
        raise ValueError("need >= 2 samples in each condition")
    if np.any(~np.isfinite(yc)) or np.any(~np.isfinite(yk)):
        raise ValueError("observations must be finite")
    mean_c, mean_k = float(np.mean(yc)), float(np.mean(yk))
    s_c = float(np.std(yc, ddof=1))
    s_k = float(np.std(yk, ddof=1))
    s_pooled = math.sqrt((s_c ** 2 + s_k ** 2) / 2.0)
    gain = max(0.0, (mean_c - mean_k) / mean_k) if mean_k != 0 \
        else float("inf")
    d_c = (mean_c - mean_k) / s_pooled if s_pooled > 0 else float("inf")
    return {
        "mean_configuration": mean_c,
        "mean_control": mean_k,
        "n_configuration": int(yc.size),
        "n_control": int(yk.size),
        "control_subtracted_gain": gain,       # G_c, clipped at 0
        "effect_size_d": d_c,                  # evidence-bearing
        "s_pooled": s_pooled,
        "classification":
            classification_string(control_subtracted_metrics),
    }


@classified("Derived", registry=("RGCS-M.58",), sources=("RG-18",),
            note="engineering heuristic - not evidence; ranks "
                 "configurations for replication priority only; every "
                 "factor reported independently (policy 3.2)")
def merit_score(overlap: float, q_a: float, q_b: float, f_a_hz: float,
                f_b_hz: float, phase_residue_cycles: float = 0.0,
                node_offset_sigma: float = 0.0,
                control_gain: float = 1.0) -> dict[str, Any]:
    """Engineering merit S = |Lambda|^2 D_f P_phi N_x G_c (RGCS-M.58).
    NOT a physical quantity; never evidence. D_f = 1/(1+(2 Q_eff Delta_f)^2)
    with Delta_f = (f_A - f_B)/sqrt(f_A f_B) (Lorentzian half-power form,
    harmonic-mean Q_eff — declared modeling choices D-19d)."""
    if not (0.0 <= overlap <= 1.0):
        raise ValueError("overlap must lie in [0, 1]")
    for name, v in (("q_a", q_a), ("q_b", q_b), ("f_a_hz", f_a_hz),
                    ("f_b_hz", f_b_hz)):
        if not (math.isfinite(v) and v > 0):
            raise ValueError(f"{name} must be positive and finite")
    if control_gain < 0:
        raise ValueError("control_gain (G_c) must be >= 0 (clipped)")
    q_eff = 2.0 / (1.0 / q_a + 1.0 / q_b)
    delta_f = (f_a_hz - f_b_hz) / math.sqrt(f_a_hz * f_b_hz)
    d_factor = 1.0 / (1.0 + (2.0 * q_eff * delta_f) ** 2)
    p_factor = math.cos(math.pi * phase_residue_cycles) ** 2
    n_factor = math.exp(-(node_offset_sigma ** 2))
    score = overlap ** 2 * d_factor * p_factor * n_factor * control_gain
    return {
        "q_effective": q_eff,
        "detuning_fraction": delta_f,
        "detuning_factor": d_factor,
        "phase_factor": p_factor,
        "node_factor": n_factor,
        "control_gain": control_gain,
        "merit_score": score,
        "note": "engineering heuristic - not evidence (policy 3.2)",
        "classification": classification_string(merit_score),
    }


@classified("Established", sources=("RG-15",),
            note="unit arithmetic correcting a Source claim (the source's "
                 "'2,000 electrons/s' figure was wrong by ~31.2x)")
def current_to_electron_rate(current_a: float) -> float:
    """Electrons per second carried by a DC current (RG-15).
    Golden (G-14): 1e-14 A -> 62,415.09 e/s."""
    if not (math.isfinite(current_a) and current_a >= 0):
        raise ValueError("current_a must be >= 0 and finite")
    return current_a / ELEMENTARY_CHARGE_C


def run_record_to_json(run: RunRecord) -> dict[str, Any]:
    """JSON-safe dict of a run record (null, never NaN; D-03)."""
    payload = to_jsonable(run)
    payload["null_label"] = run.null_label()
    payload["post_drive_coverage_ok"] = run.post_drive_coverage_ok()
    return payload
