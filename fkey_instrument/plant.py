"""BVD and coupled drive-to-sensor plant (Agent A08) and uncertainty /
identification (Agent A09).

The chain: source -> switch -> actuator -> fixture -> specimen mode ->
pickup, with a slow thermal model. The 2-DOF actuator+specimen option
exists so a TRANSDUCER resonance cannot masquerade as a CRYSTAL
resonance (A08 'coupled oscillator option'; A24 attack). Nonlinearity
is an explicit opt-in: with it off, no intermodulation exists anywhere
in the model (A08 gate: conventional channels only)."""

from __future__ import annotations

import math

import numpy as np

from rscs2_core.bvd import bvd_impedance  # reuse, not duplicate (A08)


class PlantError(ValueError):
    pass


def sdof_response(f_hz, f0_hz: float, q: float,
                  gain: float = 1.0) -> np.ndarray:
    f = np.asarray(f_hz, float)
    r = f / f0_hz
    return gain / (1.0 - r ** 2 + 1j * r / q)


class CoupledPlant:
    """2-DOF actuator (fa, Qa) + specimen (fs, Qs) with coupling k.
    Transfer to the pickup shows BOTH resonances; the discrimination
    is which peak moves when the SPECIMEN parameter changes."""

    def __init__(self, actuator_f0_hz: float, actuator_q: float,
                 specimen_f0_hz: float, specimen_q: float,
                 coupling: float = 0.05,
                 nonlinearity: float = 0.0):
        if not 0 <= coupling < 1:
            raise PlantError("coupling in [0,1)")
        self.fa, self.qa = actuator_f0_hz, actuator_q
        self.fs, self.qs = specimen_f0_hz, specimen_q
        self.k = coupling
        # nonlinearity is EXPLICIT: 0.0 means a strictly linear plant
        # and therefore zero intermodulation, computed or implied
        self.nonlinearity = float(nonlinearity)

    def transfer(self, f_hz) -> np.ndarray:
        a = sdof_response(f_hz, self.fa, self.qa)
        s = sdof_response(f_hz, self.fs, self.qs)
        return a * (1.0 + self.k * s)

    def which_peak_is_the_specimen(self, delta_frac: float = 0.01
                                   ) -> dict:
        """Perturb ONLY the specimen frequency and see which peak
        moves: the moving peak belongs to the specimen; the stationary
        one is the transducer. This is the executable answer to the
        A24 attack 'can a transducer resonance be mistaken for a
        crystal resonance'."""
        f = np.linspace(min(self.fa, self.fs) * 0.8,
                        max(self.fa, self.fs) * 1.2, 8001)
        base = np.abs(self.transfer(f))
        shifted = CoupledPlant(self.fa, self.qa,
                               self.fs * (1 + delta_frac), self.qs,
                               self.k, self.nonlinearity)
        after = np.abs(shifted.transfer(f))
        moved = f[int(np.argmax(np.abs(after - base)))]
        return {"perturbed": "specimen_f0",
                "most_responsive_hz": float(moved),
                "nearest_to": ("specimen"
                               if abs(moved - self.fs)
                               < abs(moved - self.fa)
                               else "actuator"),
                "rule": "the peak that tracks a specimen-parameter "
                        "change is the specimen's; identity by "
                        "response-to-perturbation, not by which peak "
                        "is bigger"}

    def intermod_products(self, f1_hz: float, f2_hz: float,
                          order: int = 3) -> dict:
        """Intermodulation exists ONLY if nonlinearity > 0 (A08 gate).
        With it enabled, list |m f1 ± n f2| up to the given order with
        amplitudes scaling as nonlinearity^(m+n-1)."""
        if self.nonlinearity == 0.0:
            return {"products": [],
                    "note": "plant is strictly linear: NO "
                            "intermodulation exists; an observed sum "
                            "or difference line would be an "
                            "instrument artifact (A06/A08 gate)"}
        prods = []
        for m in range(1, order + 1):
            for n in range(1, order + 1 - m + 1):
                for sign in (+1, -1):
                    f = abs(m * f1_hz + sign * n * f2_hz)
                    if f > 0:
                        prods.append({
                            "f_hz": f, "m": m, "n": sign * n,
                            "order": m + n,
                            "relative_amplitude":
                                self.nonlinearity ** (m + n - 1)})
        prods.sort(key=lambda p: (p["order"], p["f_hz"]))
        return {"products": prods,
                "nonlinearity": self.nonlinearity}


def thermal_drift(power_w: float, minutes: float,
                  tau_min: float = 8.0,
                  k_c_per_w: float = 4.0,
                  tcf_ppm_per_c: float = -20.0,
                  f0_hz: float = 20280.0) -> dict:
    """Slow thermal model: first-order rise toward P*k with time
    constant tau; frequency drifts by TCF. Warm-up is why campaigns
    include warm-up blocks (A11)."""
    dt_c = power_w * k_c_per_w * (1 - math.exp(-minutes / tau_min))
    df = f0_hz * tcf_ppm_per_c * 1e-6 * dt_c
    return {"delta_t_c": dt_c, "delta_f_hz": df,
            "note": "thermal drift can exceed a narrow resonance "
                    "linewidth; sweeps must bracket conditions in "
                    "time (A11 warm-up/cool-down blocks)"}


def synthetic_sweep(plant: CoupledPlant, f_lo: float, f_hi: float,
                    n: int = 2001, noise: float = 0.01,
                    seed: int = 0) -> dict:
    """SYNTHETIC sweep log with unmistakable markers (A21)."""
    rng = np.random.default_rng(seed)
    f = np.linspace(f_lo, f_hi, n)
    mag = np.abs(plant.transfer(f)) + noise * rng.standard_normal(n)
    return {"synthetic": True,
            "id": f"SYNTHETIC-SWEEP-{seed:04d}",
            "f_hz": f, "magnitude": np.abs(mag),
            "plant": {"actuator_f0": plant.fa,
                      "specimen_f0": plant.fs},
            "marker": "SYNTHETIC DATA — no instrument existed"}


# --- A09: identification with refusal ------------------------------------------

def fit_peak(f_hz: np.ndarray, mag: np.ndarray,
             min_points_per_linewidth: float = 5.0) -> dict:
    """Peak + Q from a sweep, refusing fits the data cannot support:
    a linewidth sampled by fewer than min_points is non-identifiable
    (A09: reject fits with insufficient bandwidth or sample rate)."""
    f = np.asarray(f_hz, float)
    m = np.asarray(mag, float)
    i0 = int(np.argmax(m))
    if i0 in (0, len(f) - 1):
        return {"fitted": None,
                "reason": "peak at the sweep edge: the band does not "
                          "bracket the resonance"}
    peak = m[i0]
    floor = np.percentile(m, 10)
    half = floor + (peak - floor) / math.sqrt(2)
    above = m >= half
    idx = np.nonzero(above)[0]
    fwhm = f[idx[-1]] - f[idx[0]]
    df = float(np.median(np.diff(f)))
    if fwhm / df < min_points_per_linewidth:
        return {"fitted": None,
                "reason": f"only {fwhm / df:.1f} points per "
                          "linewidth (< "
                          f"{min_points_per_linewidth}): "
                          "non-identifiable; densify the sweep"}
    if (m >= 0.999 * m.max()).sum() > max(3, 0.01 * len(m)):
        return {"fitted": None,
                "reason": "flat-topped/saturated peak: sensor or "
                          "drive clipping suspected (A09 "
                          "saturation detection)"}
    f0 = float(f[i0])
    q = f0 / float(fwhm)
    return {"fitted": True, "f0_hz": f0, "fwhm_hz": float(fwhm),
            "q": q, "u_f0_hz": df / 2.0,
            "grid_hz": df}


def bootstrap_q(f_hz, mag, n_boot: int = 200, seed: int = 1) -> dict:
    """Bootstrap interval for Q by residual resampling around a
    smoothed magnitude (A09 bootstrap intervals)."""
    rng = np.random.default_rng(seed)
    f = np.asarray(f_hz, float)
    m = np.asarray(mag, float)
    kernel = np.ones(9) / 9.0
    smooth = np.convolve(m, kernel, mode="same")
    resid = m - smooth
    qs = []
    for _ in range(n_boot):
        boot = smooth + rng.choice(resid, len(resid))
        fit = fit_peak(f, boot)
        if fit["fitted"]:
            qs.append(fit["q"])
    if len(qs) < n_boot // 2:
        return {"ok": False,
                "reason": "majority of bootstrap fits refused: the "
                          "data cannot support a Q interval"}
    lo, hi = np.percentile(qs, [2.5, 97.5])
    return {"ok": True, "q_ci95": [float(lo), float(hi)],
            "n_effective": len(qs)}
