"""Exchange-mediated spin-electric control reference (Agent Q01).

Source: s41567-026-03353-w.pdf, DOI 10.1038/s41567-026-03353-w —
FePc and Fe-FePc on MgO/Ag(001), ESR-STM with a spin-polarized tip,
~1 K spectroscopy / ~50 mK coherent control.

Reduced model: a two-level spin whose resonance is shifted by a
bias-dependent exchange field. The exchange field turns on nonlinearly
near molecular-orbital thresholds (modelled as a logistic occupation
factor), reproducing the paper's qualitative structure: small linear
Stark-like shifts far from threshold, large nonlinear shifts (tens of
percent) near it, and a tunability/coherence trade-off because the
same coupling that tunes also broadens.

SOURCE SYSTEM: single molecules on MgO at millikelvin temperatures.
FORBIDDEN TRANSFER: any claim about alpha quartz, any room-temperature
claim, any assertion that a macroscopic resonator has an exchange
field. The firewall test drives these refusals."""

from __future__ import annotations

import math

import numpy as np

SOURCE = {"doi": "10.1038/s41567-026-03353-w",
          "file": "s41567-026-03353-w.pdf",
          "system": "FePc / Fe-FePc on MgO/Ag(001), ESR-STM",
          "temperature_k": (0.05, 1.0),
          "allowed_transfer": "two-level detuning mathematics; "
                              "tunability-vs-linewidth bookkeeping",
          "forbidden_transfer": "alpha quartz; room temperature; "
                                "macroscopic resonators"}


class TransferViolation(RuntimeError):
    pass


def guard_target(system: str):
    if any(t in system.lower() for t in
           ("quartz", "resonator", "pcb", "room temperature")):
        raise TransferViolation(
            f"Q01 reference model refuses target {system!r}: "
            + SOURCE["forbidden_transfer"])


def exchange_field_mev(bias_mv: np.ndarray, j0_mev: float,
                       threshold_mv: float, width_mv: float) -> \
        np.ndarray:
    """J(V) = J0 * sigma((V - V_th)/w): the exchange contribution
    follows the orbital occupation, which switches on over ~width
    around the threshold — the source of the nonlinearity."""
    v = np.asarray(bias_mv, float)
    return j0_mev / (1.0 + np.exp(-(v - threshold_mv) / width_mv))


def resonance_shift(bias_mv: np.ndarray, f0_ghz: float,
                    j0_mev: float, threshold_mv: float,
                    width_mv: float) -> dict:
    """Spin resonance frequency vs bias. Far below threshold the
    shift is exponentially small (linear-regime limit); near
    threshold df/dV is maximal; far above it saturates."""
    j = exchange_field_mev(bias_mv, j0_mev, threshold_mv, width_mv)
    mev_to_ghz = 241.799
    f = f0_ghz + j * mev_to_ghz
    rel = (f - f0_ghz) / f0_ghz
    return {"bias_mv": np.asarray(bias_mv, float), "f_ghz": f,
            "relative_shift": rel,
            "max_relative_shift": float(np.max(np.abs(rel))),
            "source": SOURCE["doi"]}


def rabi_detuning(f_drive_ghz: float, f_spin_ghz: float,
                  rabi_ghz: float) -> dict:
    """All-electrical Rabi detuning: effective rotation rate
    Omega_eff = sqrt(Omega^2 + delta^2), contrast Omega^2/Omega_eff^2.
    Standard two-level result (EST); the paper's contribution is the
    electrical control knob, not the formula."""
    delta = f_drive_ghz - f_spin_ghz
    om_eff = math.hypot(rabi_ghz, delta)
    contrast = (rabi_ghz / om_eff) ** 2 if om_eff else 1.0
    return {"detuning_ghz": delta, "omega_eff_ghz": om_eff,
            "contrast": contrast}


def coupled_pair_selectivity(j_pair_mev: float, rabi_ghz: float,
                             local_shift_ghz: float) -> dict:
    """Fe-FePc pair: a local exchange shift detunes ONE spin of the
    pair, so a fixed drive addresses it selectively. Selectivity =
    contrast(on-target) - contrast(off-target)."""
    on = rabi_detuning(0.0, 0.0, rabi_ghz)["contrast"]
    off = rabi_detuning(0.0, local_shift_ghz, rabi_ghz)["contrast"]
    return {"on_target_contrast": on, "off_target_contrast": off,
            "selectivity": on - off,
            "addressable": bool(on - off > 0.5)}


def tunability_coherence_tradeoff(j0_mev: float, width_mv: float,
                                  bias_noise_mv: float) -> dict:
    """The engineering lesson the paper states: the same steep J(V)
    that gives large tuning converts bias noise into frequency noise.
    Dephasing rate ~ (dJ/dV)*sigma_V; the figure of merit
    tuning-range/linewidth is NOT monotonic in slope."""
    slope_mev_per_mv = j0_mev / (4.0 * width_mv)   # max logistic slope
    mev_to_ghz = 241.799
    dephasing_ghz = slope_mev_per_mv * bias_noise_mv * mev_to_ghz
    tuning_range_ghz = j0_mev * mev_to_ghz
    fom = tuning_range_ghz / max(dephasing_ghz, 1e-12)
    return {"max_slope_mev_per_mv": slope_mev_per_mv,
            "dephasing_ghz": dephasing_ghz,
            "tuning_range_ghz": tuning_range_ghz,
            "figure_of_merit": fom,
            "lesson": "strong tuning competes with linewidth: the "
                      "knob that moves the frequency also feeds "
                      "noise into it"}
