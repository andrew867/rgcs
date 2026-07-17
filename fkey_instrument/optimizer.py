"""Multi-objective drive optimizer (Agent A10), experiment compiler
(Agent A11), hypothesis register (Agent A03), and the desktop bridge
(Agent A13).

The A10 gate, enforced in code: a high-order arithmetic match cannot
outrank a low-order physically generated component. Mechanism class
enters the score BEFORE any error term, and PHASE_CLOSURE_ONLY /
ARITHMETIC_COINCIDENCE candidates carry zero expected amplitude by
construction (the A06 engine gives them none)."""

from __future__ import annotations

import itertools
import random
from fractions import Fraction

from . import contracts
from .plant import CoupledPlant
from .relations import hz
from .spectrum import expected_line

# --- A03: preregistered hypotheses (immutable) ---------------------------------

HYPOTHESES = {
 "H-KEY-HARMONIC-01": {
    "statement": "a phase-coherent 4096 Hz nonsinusoidal drive can "
                 "excite a target-band mechanical response through "
                 "its fifth harmonic at 20.480 kHz",
    "mechanism": "HARMONIC (order 5)",
    "iv": "drive waveform (sine vs square/pulse) at 4096 Hz",
    "dv": "pickup amplitude in the 20.48 kHz band",
    "prediction": "square > sine by the modeled 5th-harmonic "
                  "transfer; sine ~ noise floor",
    "controls": ["output-off sham", "matched-RMS off-resonance",
                 "transducer-only (no specimen)"],
    "analysis": "band amplitude with uncertainty; matched "
                "target-component comparison",
    "stop": "sensor saturation or overtemperature",
    "disconfirmed_by": "square-drive band response indistinguishable "
                       "from sine-drive within uncertainty",
    "status": "UNTESTED"},
 "H-EQUIV-SPECTRUM-01": {
    "statement": "when the measured 20.480 kHz component delivered "
                 "to a linear plant is equalized, direct and "
                 "4096-derived excitation produce equivalent "
                 "target-mode response within uncertainty",
    "mechanism": "linear-systems equivalence (the decisive "
                 "ordinary-physics control)",
    "iv": "drive family at equalized measured target component",
    "dv": "target-mode response",
    "prediction": "equivalence (this is a NULL-style prediction)",
    "controls": ["component equalization by measurement, not "
                 "setpoint"],
    "analysis": "equivalence bounds (TOST-style)",
    "stop": "component equalization not achievable within limits",
    "disconfirmed_by": "a reproducible difference AFTER equalization "
                       "— which would indicate nonlinearity or an "
                       "unmodeled path, not magic",
    "status": "UNTESTED"},
 "H-RESONANCE-LOCK-01": {
    "statement": "direct drive at the measured specimen resonance "
                 "produces greater response than equal-power nearby "
                 "off-resonance controls",
    "mechanism": "MEASURED_RESONANCE_MATCH",
    "iv": "drive frequency (on vs off resonance, matched power)",
    "dv": "pickup amplitude",
    "prediction": "on > off by ~Q-factor ratio",
    "controls": ["equal-power off-resonance at +/- 5 linewidths"],
    "analysis": "amplitude ratio with uncertainty",
    "stop": "no peak found in the candidate band",
    "disconfirmed_by": "on/off ratio ~ 1",
    "status": "UNTESTED"},
 "H-FIXTURE-LOAD-01": {
    "statement": "support and hand loading shift frequency and Q "
                 "relative to a low-contact reference",
    "mechanism": "ordinary contact mechanics",
    "iv": "support configuration",
    "dv": "peak frequency and Q",
    "prediction": "measurable shifts, direction per contact model",
    "controls": ["repeated remount blocks"],
    "analysis": "shift vs remount scatter",
    "stop": "n/a",
    "disconfirmed_by": "shifts within remount scatter",
    "status": "UNTESTED"},
 "H-HIGHORDER-MIX-NULL": {
    "statement": "high-order combinations such as 1496 + 32*587 do "
                 "not produce a detectable target component at low "
                 "drive unless measurable nonlinearity exists",
    "mechanism": "ARITHMETIC_COINCIDENCE (order 33)",
    "iv": "multi-tone drive per the arithmetic recipe",
    "dv": "target-band amplitude",
    "prediction": "NULL at linear drive levels",
    "controls": ["single tones at matched power",
                 "deliberate clipping as positive control"],
    "analysis": "band amplitude vs noise floor",
    "stop": "unexpected heating",
    "disconfirmed_by": "a target component WITHOUT the deliberate "
                       "nonlinearity — which would first be hunted "
                       "as an instrument artifact (A24)",
    "status": "UNTESTED"},
 "H-ANOMALOUS-RESIDUAL-NULL": {
    "statement": "after conventional crosstalk and transfer paths "
                 "are modeled, no unexplained output channel "
                 "remains",
    "mechanism": "null over conventional channels",
    "iv": "full campaign set",
    "dv": "residual after modeled subtraction",
    "prediction": "NULL",
    "controls": ["everything above"],
    "analysis": "residual against the modeled artifact budget",
    "stop": "n/a",
    "disconfirmed_by": "a reproducible residual surviving every "
                       "conventional model — reported as "
                       "CANDIDATE_NOVEL for further work, never as "
                       "a field claim",
    "status": "UNTESTED"},
}


def hypothesis_register() -> dict:
    """Deep copy; the register is preregistered and the optimizer
    cannot rewrite it (A03 gate — tested)."""
    import json as _json
    return _json.loads(_json.dumps(HYPOTHESES))


# --- A10: candidate generation and mechanism-first scoring ----------------------

MECHANISM_AMPLITUDE_RANK = {
    "MEASURED_RESONANCE_MATCH": 3, "HARMONIC": 2,
    "SUBHARMONIC_CLOCK": 2, "AMPLITUDE_MODULATION_SIDEBAND": 1,
    "INTERMODULATION": 0, "PHASE_CLOSURE_ONLY": 0,
    "ARITHMETIC_COINCIDENCE": 0,
}


def candidate_families(f_r_hz: float = 20278.96) -> list:
    """The required search families (orchestrator's ten comparisons
    are compiled from these)."""
    fams = [
        dict(family="direct_sine_target", kind="sine",
             f="20480", mechanism="HARMONIC", order=1,
             hypothesis="H-EQUIV-SPECTRUM-01"),
        dict(family="direct_square_target", kind="square",
             f="20480", mechanism="HARMONIC", order=1,
             hypothesis="H-EQUIV-SPECTRUM-01"),
        dict(family="clock_sine_4096", kind="sine", f="4096",
             mechanism="PHASE_CLOSURE_ONLY", order=5,
             hypothesis="H-KEY-HARMONIC-01",
             note="an ideal sine has NO 5th harmonic: this is the "
                  "negative control"),
        dict(family="clock_square_4096", kind="square", f="4096",
             mechanism="SUBHARMONIC_CLOCK", order=5,
             hypothesis="H-KEY-HARMONIC-01"),
        dict(family="resonance_locked_sine", kind="sine",
             f=str(f_r_hz), mechanism="MEASURED_RESONANCE_MATCH",
             order=1, hypothesis="H-RESONANCE-LOCK-01"),
        dict(family="resonance_locked_clock", kind="square",
             f=str(Fraction(str(f_r_hz)) / 5),
             mechanism="SUBHARMONIC_CLOCK", order=5,
             hypothesis="H-RESONANCE-LOCK-01"),
        dict(family="off_resonance_control", kind="sine",
             f=str(Fraction(str(f_r_hz)) * Fraction("1.05")),
             mechanism="HARMONIC", order=1, control=True,
             hypothesis="H-RESONANCE-LOCK-01"),
        dict(family="sham_output_off", kind="off", f="0",
             mechanism="PHASE_CLOSURE_ONLY", order=0, control=True,
             hypothesis="H-ANOMALOUS-RESIDUAL-NULL"),
        dict(family="am_envelope_20_48", kind="square", f="20480",
             mechanism="AMPLITUDE_MODULATION_SIDEBAND", order=1,
             envelope="20.48", hypothesis="H-KEY-HARMONIC-01"),
        dict(family="chirp_band", kind="sweep", f="19800",
             sweep_end="20800", mechanism="HARMONIC", order=1,
             hypothesis="H-RESONANCE-LOCK-01"),
        dict(family="highorder_mix", kind="sine", f="20280",
             mechanism="ARITHMETIC_COINCIDENCE", order=33,
             hypothesis="H-HIGHORDER-MIX-NULL",
             note="the 1496+32*587 arithmetic case, compiled as its "
                  "own null-test condition"),
    ]
    return fams


def score(candidate: dict, plant: CoupledPlant,
          uncertainty_band_hz: tuple = (20100.0, 20500.0)) -> dict:
    """Multi-objective score with mechanism-first hard ordering.

    expected_amplitude comes from the A06 engine through the plant —
    NOT from arithmetic closeness. Robustness = mean plant gain over
    the uncertainty band (A09: consume uncertainty, not points)."""
    f = float(hz(candidate["f"])) if candidate["f"] != "0" else 0.0
    if candidate["kind"] == "off" or f == 0.0:
        exp_amp = 0.0
    else:
        target_line = f * candidate["order"] if \
            candidate["mechanism"] in ("SUBHARMONIC_CLOCK",) else f
        line = expected_line(
            str(candidate["f"]),
            candidate["order"] if candidate["mechanism"]
            == "SUBHARMONIC_CLOCK" else 1,
            duty=0.5 if candidate["kind"] in ("square", "pulse")
            else 0.5,
            rise_time_s=200e-9, plant_f0_hz=plant.fs,
            plant_q=plant.qs)
        # a sine drive has no harmonic content above order 1
        if candidate["kind"] == "sine" and candidate["order"] > 1:
            exp_amp = 0.0
        elif candidate["mechanism"] in ("PHASE_CLOSURE_ONLY",
                                        "ARITHMETIC_COINCIDENCE"):
            exp_amp = 0.0
        else:
            exp_amp = line["expected_amplitude"]
        del target_line
    import numpy as np
    band = np.linspace(*uncertainty_band_hz, 41)
    robustness = float(np.mean(np.abs(
        plant.transfer(band)))) if f else 0.0
    discrim = 1.0 if candidate.get("control") or \
        "NULL" in candidate.get("hypothesis", "") else \
        0.5 + 0.5 * (candidate["order"] <= 5)
    complexity = 1 + (candidate["kind"] in ("sweep", "burst")) \
        + (candidate.get("envelope") is not None)
    power_penalty = 0.2 if candidate["kind"] == "square" else 0.1
    return {**candidate,
            "mechanism_rank":
                MECHANISM_AMPLITUDE_RANK.get(candidate["mechanism"],
                                             0),
            "expected_target_amplitude": exp_amp,
            "robustness": robustness,
            "discriminating_value": discrim,
            "complexity": complexity,
            "power_penalty": power_penalty}


def pareto_frontier(scored: list) -> list:
    """Non-dominated set over (maximize expected amplitude, maximize
    discriminating value, minimize complexity) — computed WITHIN each
    hypothesis, because candidates testing different hypotheses are
    not substitutes: a sham run cannot be 'dominated' by a resonance
    tone; they answer different questions. The frontier is therefore
    a SET spanning the hypothesis register, never one mystical
    winner (A10)."""
    front = []
    for c in scored:
        dominated = False
        for d in scored:
            if d is c:
                continue
            if d.get("hypothesis") != c.get("hypothesis"):
                continue           # different question: incomparable
            if bool(d.get("control")) != bool(c.get("control")):
                continue           # a control is not a substitute
            if (d["expected_target_amplitude"]
                    >= c["expected_target_amplitude"]
                    and d["discriminating_value"]
                    >= c["discriminating_value"]
                    and d["complexity"] <= c["complexity"]
                    and (d["expected_target_amplitude"]
                         > c["expected_target_amplitude"]
                         or d["discriminating_value"]
                         > c["discriminating_value"]
                         or d["complexity"] < c["complexity"])):
                dominated = True
                break
        if not dominated:
            front.append(c)
    # mechanism-first hard ordering inside the frontier (A10 gate)
    return sorted(front, key=lambda c: (-c["mechanism_rank"],
                                        c["order"],
                                        -c["expected_target_amplitude"
                                           ]))


def optimize(plant: CoupledPlant | None = None) -> dict:
    plant = plant or CoupledPlant(4300.0, 8.0, 20278.96, 400.0)
    scored = [score(c, plant) for c in candidate_families(plant.fs)]
    front = pareto_frontier(scored)
    return {"candidates": scored, "pareto": front,
            "gate_check": {
                "rule": "high-order arithmetic cannot outrank "
                        "low-order physical generation",
                "holds": all(
                    f["mechanism_rank"] > 0
                    or f["discriminating_value"] >= 1.0
                    for f in front[:4])},
            "synthetic": True}


# --- A11: experiment compiler ---------------------------------------------------

CAMPAIGNS = [
    "C1 instrument characterization",
    "C2 actuator and fixture characterization",
    "C3 coarse resonance sweep",
    "C4 fine sweep and Q estimate",
    "C5 direct vs 4096-derived target component",
    "C6 support-loading study",
    "C7 AM envelope comparison",
    "C8 high-order mixing null test",
]


def compile_campaign(candidates: list, seed: int = 0,
                     blocks: int = 3) -> dict:
    """Randomized, blinded campaign manifest. Conditions are shuffled
    per block with a seeded RNG; blind labels map to conditions in a
    sealed table; sham and warm-up blocks are inserted; stop rules
    and missing-data policy declared up front (A11)."""
    rng = random.Random(seed)
    conditions = [c["family"] for c in candidates]
    if "sham_output_off" not in conditions:
        conditions.append("sham_output_off")
    order = []
    for b in range(blocks):
        block = conditions[:]
        rng.shuffle(block)
        order.append(block)
    labels = {f"COND-{i:03d}": c
              for i, c in enumerate(sorted(conditions))}
    sealed = {v: k for k, v in labels.items()}
    return {
        "manifest_id": f"SYNTHETIC-CAMPAIGN-{seed:04d}",
        "synthetic": True,
        "campaigns": CAMPAIGNS,
        "blocks": [[sealed[c] for c in blk] for blk in order],
        "sealed_labels": labels,
        "warm_up_s": 120, "cool_down_s": 60,
        "remount_between_blocks": True,
        "stop_rules": ["sensor saturation", "overtemperature",
                       "operator stop", "fault latch"],
        "missing_data_policy": "a missing condition voids its block; "
                               "blocks are never partially "
                               "reanalyzed",
        "post_hoc_rule": "no frequency may be added after data "
                         "without a NEW exploratory revision "
                         "(A11/A24)",
    }


# --- A13: desktop bridge ---------------------------------------------------------

class Bridge:
    """Desktop bridge against a device (the simulator today; HTTP or
    serial transport is a declared interface for real hardware). No
    command bypasses the device's own state machine (A13 gate) —
    the bridge only calls the device's public API."""

    def __init__(self, device):
        self.device = device

    def list_devices(self) -> list:
        return [self.device.status()]

    def compile_recipe(self, family: dict,
                       duration_s: float = 5.0) -> dict:
        seg = {"label": family["family"],
               "kind": family["kind"] if family["kind"] != "off"
               else "off",
               "frequency_hz": family["f"] if family["f"] != "0"
               else "1",
               "duration_s": duration_s,
               "duty": 0.5, "amplitude_frac": 0.3,
               "backend": "SIMULATOR"}
        if family["kind"] == "sweep":
            seg["sweep_end_hz"] = family.get("sweep_end")
        rec = contracts.example_recipe(
            f"SYNTHETIC-{family['family']}", [seg],
            hypothesis_id=family.get("hypothesis"))
        return rec

    def upload(self, recipe: dict) -> dict:
        return self.device.load_recipe(recipe,
                                       contracts.validate_recipe)

    def arm_start_run(self, ttl_s: float = 30.0) -> dict:
        lease = self.device.request_arm(ttl_s)
        started = self.device.start(lease["token"])
        if not started["started"]:
            return {"ok": False, "device": self.device.status()}
        result = self.device.run_segments()
        return {"ok": result["completed"], "result": result}

    def download_and_verify_logs(self) -> dict:
        chain = self.device.verify_log_chain()
        return {"n_events": len(self.device.log),
                "chain": chain,
                "all_synthetic": all(e["synthetic"]
                                     for e in self.device.log)}
