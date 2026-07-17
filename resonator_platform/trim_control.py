"""Laser/CNC irreversible trim control (Agent R05; coverage R033-R040)
and bidirectional tuning (Agent R06; coverage R041-R048).

The planner is deliberately conservative: it selects the SMALLEST trim
set predicted to reach the band, refuses moves that could overshoot,
preserves the declared symmetry group, requires an explicit approval
token plus a machine-capability flag before anything irreversible, and
stops automatically on mode loss, overshoot risk, or inconsistent
response. There is no force flag and no way to trim without approval.
"""

from __future__ import annotations

import hashlib
import math

import numpy as np


class TrimError(RuntimeError):
    pass


class GuardTripped(RuntimeError):
    """A stop condition fired; the loop must halt, not retry."""


# --- candidate generation (R033/R034) -------------------------------------------

def trim_candidates(twin, symmetry_order: int = 2) -> list:
    """Candidates from UNUSED sacrificial cells only, grouped so a
    selected set preserves the declared symmetry (cells are taken in
    symmetric pairs/groups, R011/R035)."""
    unused = [i for i in range(twin.n_cells) if i not in twin.removed]
    groups = {}
    for i in unused:
        key = i % (twin.n_cells // symmetry_order)
        groups.setdefault(key, []).append(i)
    out = []
    for key, cells in groups.items():
        if len(cells) < symmetry_order:
            continue                     # symmetry partner consumed
        cells = cells[:symmetry_order]
        pred = float(sum(twin.cell_sensitivity_hz[c] for c in cells))
        out.append({"cells": cells,
                    "predicted_shift_hz": pred,
                    "predicted_q_change": -0.001 * len(cells),
                    "symmetry_preserved": True,
                    "balance_moment": 0.0,   # symmetric pair cancels
                    "electrical_effect": "copper mass only; no "
                                         "trace cut in this family"})
    return sorted(out, key=lambda c: c["predicted_shift_hz"])


# --- conservative selection (R035) ----------------------------------------------

def select_trim(candidates: list, current_hz: float,
                target_hz: float, band_hz: float,
                overshoot_margin: float = 0.5) -> dict | None:
    """Pick the smallest candidate that moves toward the band without
    risking overshoot: the predicted post-trim frequency must not pass
    the target by more than overshoot_margin * band. If every
    candidate overshoots, return None — undershoot is recoverable,
    overshoot is not (trims are irreversible)."""
    gap = target_hz - current_hz
    if abs(gap) <= band_hz:
        return None                          # already in band
    if gap < 0:
        # removal only RAISES frequency in this family; a negative
        # gap cannot be fixed by ablation (see tuning.py for
        # bidirectional options)
        raise TrimError(
            "current frequency is above target: ablation cannot "
            "lower it in this trim family; use a bidirectional "
            "action (mass addition) or reject")
    viable = []
    for c in candidates:
        post = current_hz + c["predicted_shift_hz"]
        overshoot = post - target_hz
        if overshoot > overshoot_margin * band_hz:
            continue
        viable.append((abs(target_hz - post), c))
    if not viable:
        return None
    return min(viable, key=lambda t: t[0])[1]


# --- approval + capability gate (R036) --------------------------------------------

MACHINE_CAPABILITIES: dict = {}     # empty: no machine is configured


def register_machine(machine_id: str, *, enclosure_class: str,
                     fume_extraction: bool, interlock: bool) -> None:
    """A machine may only be registered with its safety evidence.
    FR-4 ablation without qualified extraction is refused at
    registration time (S01: FR-4 fumes are hazardous)."""
    if not (fume_extraction and interlock):
        raise TrimError("machine registration requires fume "
                        "extraction and interlock evidence (S01)")
    MACHINE_CAPABILITIES[machine_id] = {
        "enclosure_class": enclosure_class,
        "fume_extraction": fume_extraction, "interlock": interlock}


def approval_token(operator: str, specimen_id: str,
                   trim_cells: list) -> str:
    """An approval is specific to operator + specimen + exact cell
    set; it cannot be reused for a different trim."""
    return hashlib.sha256(
        f"{operator}|{specimen_id}|{sorted(trim_cells)}".encode()
    ).hexdigest()[:16]


def execute_trim(twin, ledger, specimen_id: str, selection: dict,
                 token: str, operator: str,
                 machine_id: str | None = None,
                 dry_run: bool = True) -> dict:
    """The ONLY execution path. Requirements, in order:

    1. dry_run=True (default) simulates on the twin — always allowed.
    2. dry_run=False requires a registered machine (capability flag)
       AND a token matching operator+specimen+cells exactly.

    No machine is registered in this repository, so a physical
    execution path cannot be reached today — which is the honest
    state: the platform has no laser."""
    expected = approval_token(operator, specimen_id,
                              selection["cells"])
    if token != expected:
        raise TrimError("approval token does not match this exact "
                        "operator/specimen/cell set")
    if not dry_run:
        if machine_id not in MACHINE_CAPABILITIES:
            raise TrimError(
                "no registered machine capability: physical trim is "
                "refused (no laser/CNC exists in this programme)")
    results = []
    for cell in selection["cells"]:
        r = twin.execute_trim(cell)
        ledger.append("trim_executed", {
            "specimen_id": specimen_id, "cell": cell,
            "dry_run": dry_run, "operator": operator,
            "token": token, **r})
        results.append(r)
    return {"cells": selection["cells"], "results": results,
            "realized_shift_hz": sum(r["realized_shift_hz"]
                                     for r in results),
            "predicted_shift_hz": selection["predicted_shift_hz"],
            "dry_run": dry_run}


# --- toolpath export (R037), capability-gated -------------------------------------

def toolpath_text(twin, cells: list, machine_id: str) -> str:
    """Machine-specific G-code-style toolpath. Refuses without a
    registered machine: a toolpath for a machine that does not exist
    is an invitation to run it on whatever is lying around."""
    if machine_id not in MACHINE_CAPABILITIES:
        raise TrimError("toolpath export requires a registered "
                        "machine capability (R037/S01)")
    lines = [f"; RGCS trim toolpath — machine {machine_id}",
             "; UNITS mm; SAFE_Z 5.0; refuse if fiducials not found"]
    for c in cells:
        r = twin.cell_radius_frac[c] * twin.radius_m * 1000
        a = twin.cell_angle_rad[c]
        x, y = r * math.cos(a), r * math.sin(a)
        lines += [f"G0 X{x:.3f} Y{y:.3f}",
                  "M3 ; enable (interlock verified)",
                  "G1 F300 ; ablate cell",
                  "M5 ; disable"]
    lines.append("M2")
    return "\n".join(lines) + "\n"


# --- stop conditions (R040) --------------------------------------------------------

def check_guards(fit_before: dict, fit_after: dict,
                 predicted_shift_hz: float, target_hz: float,
                 band_hz: float, sensitivity_tol: float = 3.0
                 ) -> dict:
    """Automatic stops: mode loss, overshoot, inconsistent response.
    Raises GuardTripped — the loop must halt for a human."""
    if not fit_after.get("fitted"):
        raise GuardTripped("MODE LOSS: the target mode is no longer "
                           "identifiable after the trim")
    realized = fit_after["f0_hz"] - fit_before["f0_hz"]
    if fit_after["f0_hz"] - target_hz > band_hz:
        raise GuardTripped(
            f"OVERSHOOT: fitted {fit_after['f0_hz']:.1f} Hz exceeds "
            f"target {target_hz:.1f} +/- {band_hz:.1f} Hz; trims are "
            "irreversible — stopping")
    if predicted_shift_hz > 0 and (
            realized <= 0 or
            realized > sensitivity_tol * predicted_shift_hz):
        raise GuardTripped(
            f"INCONSISTENT RESPONSE: predicted "
            f"{predicted_shift_hz:.2f} Hz, realized {realized:.2f} "
            "Hz; the sensitivity model is wrong — stopping")
    return {"realized_shift_hz": realized, "guards_passed": True}


# --- empirical sensitivity update (R039) --------------------------------------------

def update_sensitivity(prior_hz_per_cell: float, predicted_hz: float,
                       realized_hz: float, n_cells: int,
                       learning_rate: float = 0.5) -> dict:
    """Regularized empirical update: shrink toward the observation by
    the declared learning rate. The prior is never hidden (R048)."""
    if n_cells <= 0:
        raise TrimError("n_cells must be positive")
    observed = realized_hz / n_cells
    updated = (1 - learning_rate) * prior_hz_per_cell \
        + learning_rate * observed
    return {"prior_hz_per_cell": prior_hz_per_cell,
            "observed_hz_per_cell": observed,
            "updated_hz_per_cell": updated,
            "learning_rate": learning_rate,
            "note": "declared shrinkage; prior and observation both "
                    "reported (no hidden prior)"}
