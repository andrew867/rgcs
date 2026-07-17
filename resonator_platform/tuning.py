"""Bidirectional and reversible tuning (Agent R06; coverage R041-R048).

Ablation only raises this family's frequencies (mass removal). Real
platforms need to move both ways and to test a correction before
committing to an irreversible one. This module provides:

- signed tuning actions (removal raises f; addition lowers f);
- REVERSIBLE actions (clip-on test mass, temporary damper) with
  rollback, so a correction can be trialled before any laser fires;
- a multi-objective selector (frequency error, Q penalty, symmetry,
  action count);
- the regularized empirical update re-exported from trim_control so
  both directions learn from realized shifts.
"""

from __future__ import annotations

import copy

from .trim_control import TrimError, update_sensitivity  # noqa: F401

ACTION_KINDS = {
    # kind: (sign of df for a positive amount, reversible?)
    "ablate_copper_cell": (+1, False),
    "ablate_substrate": (+1, False),
    "add_epoxy_mass": (-1, False),
    "add_clip_test_mass": (-1, True),
    "attach_temp_damper": (0, True),      # Q change only
}


class TuningAction:
    """A signed, possibly reversible tuning action."""

    def __init__(self, kind: str, amount: float,
                 sensitivity_hz_per_unit: float):
        if kind not in ACTION_KINDS:
            raise TrimError(f"unknown action kind {kind}")
        if amount <= 0:
            raise TrimError("amount must be positive; direction "
                            "comes from the action kind")
        self.kind = kind
        self.amount = amount
        self.sign, self.reversible = ACTION_KINDS[kind]
        self.sensitivity = sensitivity_hz_per_unit

    @property
    def predicted_shift_hz(self) -> float:
        return self.sign * self.amount * self.sensitivity

    def as_record(self) -> dict:
        return {"kind": self.kind, "amount": self.amount,
                "signed_predicted_shift_hz": self.predicted_shift_hz,
                "reversible": self.reversible}


class ReversibleSession:
    """Apply reversible actions to a twin with rollback (R043).

    The twin's irreversible state (removed cells) is never touched;
    only an additive frequency offset is applied, and rollback
    restores it exactly."""

    def __init__(self, twin):
        self.twin = twin
        self._applied: list[tuple[TuningAction, float]] = []
        self._base_shift = twin.fixture_shift_hz

    def apply(self, action: TuningAction) -> dict:
        if not action.reversible:
            raise TrimError(
                f"{action.kind} is irreversible and cannot be "
                "applied through a reversible session — use the "
                "guarded trim path")
        df = action.predicted_shift_hz
        self.twin.fixture_shift_hz += df
        self._applied.append((action, df))
        return {"applied": action.as_record(),
                "trial_shift_hz": df, "rollback_available": True}

    def rollback(self) -> dict:
        total = sum(df for _, df in self._applied)
        self.twin.fixture_shift_hz -= total
        n = len(self._applied)
        self._applied.clear()
        return {"rolled_back_actions": n,
                "restored_shift_hz": -total,
                "state_restored": abs(self.twin.fixture_shift_hz
                                      - self._base_shift) < 1e-12}


def plan_bidirectional(current_hz: float, target_hz: float,
                       band_hz: float,
                       removal_sensitivity_hz: float,
                       addition_sensitivity_hz: float) -> dict:
    """Choose the direction and the minimal action list. Signed
    sensitivities are explicit (R041): removal raises, addition
    lowers, and the two magnitudes are independent empirical numbers,
    never assumed symmetric."""
    gap = target_hz - current_hz
    if abs(gap) <= band_hz:
        return {"direction": "none", "actions": [],
                "reason": "already inside the acceptance band"}
    if gap > 0:
        n = max(1, int(gap / max(removal_sensitivity_hz, 1e-12)))
        return {"direction": "raise", "mechanism": "mass removal",
                "estimated_actions": n,
                "sensitivity_hz": +removal_sensitivity_hz,
                "reversible_trial_first": False}
    n = max(1, int(-gap / max(addition_sensitivity_hz, 1e-12)))
    return {"direction": "lower", "mechanism": "mass addition",
            "estimated_actions": n,
            "sensitivity_hz": -addition_sensitivity_hz,
            "reversible_trial_first": True,
            "note": "trial with a clip-on test mass and rollback "
                    "before any permanent epoxy (R043)"}


def multi_objective_score(freq_error_hz: float, q_change: float,
                          n_actions: int, symmetry_preserved: bool,
                          weights: dict | None = None) -> dict:
    """R045: declared-weight scalarization plus the raw components,
    so the trade-off is visible rather than swallowed by one score."""
    w = {"freq": 1.0, "q": 50.0, "actions": 0.2, "symmetry": 10.0}
    w.update(weights or {})
    penalty = (w["freq"] * abs(freq_error_hz)
               + w["q"] * max(0.0, -q_change)
               + w["actions"] * n_actions
               + (0.0 if symmetry_preserved else w["symmetry"]))
    return {"score": penalty, "components": {
        "freq_error_hz": freq_error_hz, "q_change": q_change,
        "n_actions": n_actions,
        "symmetry_preserved": symmetry_preserved},
        "weights": w,
        "note": "lower is better; components reported so the "
                "scalarization cannot hide the trade"}
