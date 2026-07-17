"""The complete synthetic design-to-certificate campaign (R008).

This is the platform's integrated proof: one run exercises every
module in dependency order —

  design -> predicted modes -> fabrication variation -> fixture ->
  synthetic sweeps -> Lorentzian fit -> trim candidates ->
  conservative selection -> approval -> (dry-run) trim ->
  remeasure -> guards -> >=2 iterations -> held-out verification ->
  signed certificate

Everything is SYNTHETIC and marked so at every layer. The campaign is
deterministic given its seed.
"""

from __future__ import annotations

from . import daq, fixture as fx, trim_control as tc
from .certificate import issue, verify
from .records import (Lifecycle, ResonatorLedger, frequency_record,
                      make_id)
from .twin import ResonatorTwin

SIGNING_KEY = b"rgcs-synthetic-demo-key"   # demo key, in-repo, not a
#                                            secret: certificates are
#                                            SYNTHETIC


def run_campaign(target_hz: float | None = None,
                 band_hz: float = 3.0,
                 seed: int = 7,
                 max_iterations: int = 6) -> dict:
    """Run the full loop. Returns the certificate plus the audit
    trail. Raises GuardTripped if a stop condition fires (which is a
    correct outcome, not a failure of the campaign)."""
    ledger = ResonatorLedger(synthetic=True)
    twin = ResonatorTwin(seed=seed)

    design_id = make_id("design", "ref-disk-A", seed)
    specimen_id = make_id("specimen", design_id, "S1")
    life = Lifecycle(ledger, specimen_id)

    # --- design + predicted modes (never overwritten) ---------------
    predicted_f01 = twin.mode_hz(0, 1)      # includes fab variation
    ledger.append("design", {"design_id": design_id,
                             "predicted_f01_hz": predicted_f01})
    life.to("SIMULATED")
    life.to("FABRICATED", fabrication="synthetic variation applied")

    # preregistered acceptance band, declared BEFORE measurement
    if target_hz is None:
        target_hz = predicted_f01 + 6.0     # ask for a real trim
    band = (target_hz - band_hz, target_hz + band_hz)
    ledger.append("preregistration", {"target_hz": target_hz,
                                      "band_hz": list(band)})

    # --- fixture -----------------------------------------------------
    fix = fx.fixture_record("three_point", 5.0, "delrin", 0.0,
                            21.0, 45.0, [(0.8, 0.0), (0.8, 120.0)])
    twin.mount(fix["bc_stiffness_factor"])
    life.to("FIXTURED", fixture=fix["kind"])

    # --- measure + fit ------------------------------------------------
    def measure() -> dict:
        s = daq.capture_sweep(twin, predicted_f01 - 400,
                              predicted_f01 + 400, 4001)
        s = daq.correct_transfer(s, f0_instr_hz=predicted_f01 * 3,
                                 q_instr=2.0)
        fit = daq.fit_lorentzian(s["f_hz"], s["magnitude"],
                                 predicted_f01, 300.0)
        ledger.append("sweep", {
            "sweep_id": make_id("sweep", specimen_id, len(ledger)),
            "fit": {k: v for k, v in fit.items()},
            "artifacts": daq.detect_artifacts(s)})
        return fit

    life.to("MEASURED")
    fit0 = measure()
    assert fit0["fitted"], "initial mode not identifiable"
    life.to("MODE_IDENTIFIED", f0_hz=fit0["f0_hz"])

    # --- iterate: trim / remeasure -------------------------------------
    fit = fit0
    iterations = 0
    trim_history = []
    guard_events = []
    while iterations < max_iterations:
        gap = target_hz - fit["f0_hz"]
        if abs(gap) <= band_hz:
            break
        cands = tc.trim_candidates(twin, symmetry_order=2)
        sel = tc.select_trim(cands, fit["f0_hz"], target_hz, band_hz)
        if sel is None:
            guard_events.append("no viable non-overshooting "
                                "candidate; stopping short")
            break
        life.to("TRIM_PLANNED", cells=sel["cells"])
        token = tc.approval_token("synthetic-operator", specimen_id,
                                  sel["cells"])
        life.to("TRIM_APPROVED", token=token)
        before = fit
        exec_rec = tc.execute_trim(twin, ledger, specimen_id, sel,
                                   token, "synthetic-operator",
                                   dry_run=True)
        trim_history.append(exec_rec)
        life.to("TRIM_EXECUTED")
        life.to("FIXTURED", remount=True)
        twin.mount(fix["bc_stiffness_factor"])
        life.to("MEASURED")
        fit = measure()
        life.to("MODE_IDENTIFIED", f0_hz=fit.get("f0_hz"))
        guard = tc.check_guards(before, fit,
                                sel["predicted_shift_hz"],
                                target_hz, band_hz)
        guard_events.append(guard)
        # empirical sensitivity update (R039)
        upd = tc.update_sensitivity(
            float(twin.cell_sensitivity_hz[sel["cells"][0]]),
            sel["predicted_shift_hz"], guard["realized_shift_hz"],
            len(sel["cells"]))
        ledger.append("sensitivity_update", upd)
        iterations += 1

    # --- held-out verification -----------------------------------------
    life.to("VERIFIED")
    holdout = measure()          # an independent remeasure, new sweep
    in_band = holdout["fitted"] and \
        band[0] <= holdout["f0_hz"] <= band[1]
    accepted_hz = holdout["f0_hz"] if in_band else None
    life.to("ACCEPTED" if in_band else "REJECTED",
            holdout_hz=holdout.get("f0_hz"))

    freq = frequency_record(
        predicted_hz=predicted_f01,
        measured_peak_hz=holdout.get("f0_hz"),
        fitted_hz=holdout.get("f0_hz"),
        fitted_uncertainty_hz=holdout.get("u_f0_hz"),
        accepted_hz=accepted_hz)

    cert = issue(specimen_id,
                 design={"design_id": design_id,
                         "family": "reference disk A"},
                 fixture=fix, frequency=freq,
                 trim_history=trim_history,
                 ledger_head=ledger.events()[-1]["event_hash"],
                 acceptance_band_hz=band,
                 signing_key=SIGNING_KEY, synthetic=True)
    return {
        "certificate": cert,
        "certificate_valid": verify(cert, SIGNING_KEY)["valid"],
        "iterations": iterations,
        "accepted": bool(in_band),
        "final_state": life.state,
        "guard_events": guard_events,
        "ledger_intact": ledger.verify()["intact"],
        "n_ledger_events": len(ledger),
        "predicted_f01_hz": predicted_f01,
        "target_hz": target_hz,
        "final_fitted_hz": holdout.get("f0_hz"),
        "synthetic": True,
    }
