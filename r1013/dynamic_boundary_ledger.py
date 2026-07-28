"""R10.13 Phase 27 — dynamic-boundary gated-wavepacket energy ledger.

CONVENTIONAL PHYSICS ONLY, built over rscs2_core.dynamic_boundary
where applicable. A phase-timed gate g_q(t) applied to a wavepacket
envelope u(t): effective duty cycle, sideband structure, ring-down,
and the conservation ledger

    E_before + W_switch + E_pump = E_after + E_loss.

Source interpretations (Phryll, environmental emission, craft motion,
multiverse transfer) are SOURCE-PROVENANCE RECORDS attached for
traceability; they are never outputs of this model, and asking the
model to confirm them refuses.
"""

from __future__ import annotations

import numpy as np

from r1013.errors import UserError
from r1013.timing import timing_relationship

#: Interpretations that may appear ONLY as provenance, never as model
#: output. The model cannot detect, confirm, or quantify any of them.
SOURCE_INTERPRETATIONS = (
    "phryll_generation", "environmental_emission", "craft_motion",
    "multiverse_transfer", "free_energy", "gravity_modification",
    "propulsion")


def gate_waveform(q: int, n_samples: int = 8192,
                  duty: float = 0.5) -> dict:
    """One closed macrocycle of carrier with a q-advanced gate."""
    rel = timing_relationship()
    if not (0 <= q < rel["phase_states"]):
        raise UserError("RGCS-E005",
                        f"q must be 0..{rel['phase_states'] - 1}.")
    t = np.linspace(0.0, rel["closed_macrocycle_ms"] / 1000.0,
                    n_samples, endpoint=False)
    carrier = np.sin(2 * np.pi * rel["carrier_hz"] * t)
    phase = (2 * np.pi * rel["carrier_hz"] * t
             + np.deg2rad(q * rel["phase_step_deg"])) % (2 * np.pi)
    gate = (phase < 2 * np.pi * duty).astype(float)
    return {"t_s": t, "carrier": carrier, "gate": gate, "q": q,
            "duty_nominal": duty}


def effective_duty(u: np.ndarray, gate: np.ndarray) -> float:
    """Energy-weighted duty cycle D_eff = int |u|^2 g / int |u|^2."""
    p = np.abs(u) ** 2
    tot = float(p.sum())
    if tot == 0:
        raise UserError("RGCS-E005", "wavepacket has zero energy")
    return float((p * gate).sum() / tot)


def sidebands(u_gated: np.ndarray, fs_hz: float, n_peaks: int = 8) -> list:
    """Strongest spectral lines of the gated packet (conventional
    chopping sidebands)."""
    spec = np.abs(np.fft.rfft(u_gated)) ** 2
    freqs = np.fft.rfftfreq(len(u_gated), 1.0 / fs_hz)
    idx = np.argsort(spec)[::-1][:n_peaks]
    return [{"frequency_hz": float(freqs[i]),
             "relative_power": float(spec[i] / spec.max())}
            for i in sorted(idx)]


def energy_ledger(q: int, duty: float = 0.5,
                  switch_work_j: float = 0.0,
                  pump_energy_j: float = 0.0,
                  loss_fraction: float = 0.05) -> dict:
    """Conservation ledger for one gated macrocycle of a unit-energy
    packet. Everything balances by construction; the ledger exists so
    an experiment can be compared line by line."""
    if not (0 <= loss_fraction < 1):
        raise UserError("RGCS-E005", "loss_fraction must be in [0,1).")
    w = gate_waveform(q, duty=duty)
    d_eff = effective_duty(w["carrier"], w["gate"])
    e_before = 1.0
    transmitted = e_before * d_eff
    reflected_or_stored = e_before * (1 - d_eff)
    e_in = e_before + switch_work_j + pump_energy_j
    e_loss = loss_fraction * e_in
    e_after = e_in - e_loss
    return {
        "q": q, "duty_nominal": duty, "duty_effective": d_eff,
        "ledger_j": {"E_before": e_before,
                     "W_switch": switch_work_j,
                     "E_pump": pump_energy_j,
                     "E_after": e_after, "E_loss": e_loss},
        "balance_residual_j": (e_before + switch_work_j + pump_energy_j)
        - (e_after + e_loss),
        "partition": {"transmitted_fraction": transmitted,
                      "gated_off_fraction": reflected_or_stored,
                      "note": "gated-off energy is reflected, stored, "
                              "or redistributed into other modes; it "
                              "does not vanish"},
        "observables": ["transmitted/reflected energy",
                        "optical sidebands", "acoustic sidebands",
                        "ring-down", "piezo output", "switching work",
                        "thermal change", "mode redistribution"],
        "evidence_class": "ANALYTIC",
        "model_status": "RESEARCH_ONLY_CONVENTIONAL",
    }


def interpret(claim: str) -> dict:
    """Any request to confirm a source interpretation refuses."""
    if claim in SOURCE_INTERPRETATIONS:
        return {"claim": claim, "status": "REFUSED",
                "reason": "source interpretation; not an output of the "
                          "conventional model. The energy ledger "
                          "balances without it and no observable in "
                          "this software can detect it.",
                "evidence_class": "SOURCE_PROVENANCE_ONLY"}
    raise UserError("RGCS-E006",
                    f"'{claim}' is not a registered source "
                    f"interpretation ({', '.join(SOURCE_INTERPRETATIONS)}).")
