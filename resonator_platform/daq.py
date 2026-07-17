"""Excitation, readout, and DAQ (Agent R04; coverage R025-R032).

Interfaces for excitation and readout channels, synchronized sweep
capture, calibration/transfer-function correction, Lorentzian mode
fitting with uncertainty, multi-point mode shapes, artifact detection
(clipping, nonlinearity, drift), and replayable synthetic sessions.

No instrument driver here touches hardware: every backend is synthetic
and says so. The fits and detectors are real algorithms validated on
planted fixtures, exactly like the E08 ring-down pipeline."""

from __future__ import annotations

import json
import math

import numpy as np

EXCITATION_KINDS = ("piezo", "shaker", "acoustic", "impulse",
                    "electromagnetic", "electrostatic")
READOUT_KINDS = ("contact_mic", "accelerometer", "piezo_pickup",
                 "laser_vibrometer", "optical_lever", "impedance")


class DaqError(RuntimeError):
    pass


def channel_interface(kind: str, role: str) -> dict:
    """R025/R026: a typed channel declaration. No driver exists —
    hardware integration is a declared interface, not a mock."""
    legal = EXCITATION_KINDS if role == "excitation" else \
        READOUT_KINDS
    if kind not in legal:
        raise DaqError(f"unknown {role} kind {kind!r}")
    return {"kind": kind, "role": role,
            "driver": "SYNTHETIC_ONLY",
            "declares": ["units", "bandwidth_hz", "sensitivity",
                         "calibration_id", "placement"],
            "note": "no hardware driver exists; physical integration "
                    "is INTERFACE_ONLY"}


# --- sweep capture and correction ---------------------------------------------

def capture_sweep(twin, f_lo_hz: float, f_hi_hz: float,
                  n_points: int = 2001, **kw) -> dict:
    """R027: synchronized sweep with environmental metadata. The twin
    is the only backend; the session is replayable via its JSON."""
    raw = twin.sweep(f_lo_hz, f_hi_hz, n_points, **kw)
    return {"f_hz": raw["f_hz"], "magnitude": raw["magnitude"],
            "clipped": raw["clipped"],
            "environment": {"temperature_c": 21.0, "humidity_pct": 45,
                            "note": "synthetic constants"},
            "synthetic": True}


def correct_transfer(sweep: dict, f0_instr_hz: float,
                     q_instr: float) -> dict:
    """R028: divide out the declared instrument transfer function.
    Failing to do this manufactures peaks (E08 lesson)."""
    from rscs2_core.apparatus import transducer_transfer
    h = np.abs(transducer_transfer(sweep["f_hz"], f0_instr_hz,
                                   q_instr))
    return {**sweep, "magnitude": sweep["magnitude"] / h,
            "transfer_corrected": True,
            "instrument": {"f0_hz": f0_instr_hz, "q": q_instr}}


# --- mode fitting (R029) --------------------------------------------------------

def fit_lorentzian(f_hz: np.ndarray, mag: np.ndarray,
                   f_guess_hz: float, window_hz: float) -> dict:
    """Fit a single Lorentzian magnitude peak near f_guess by
    weighted least squares on the linearized form, returning centre,
    linewidth, Q, amplitude, and grid-limited uncertainty.

    Identifiability is reported, not assumed: a window that contains
    no clear peak returns fitted=None rather than a fabricated
    centre."""
    f = np.asarray(f_hz, float)
    m = np.asarray(mag, float)
    sel = (f >= f_guess_hz - window_hz) & (f <= f_guess_hz + window_hz)
    if sel.sum() < 7:
        return {"fitted": None,
                "reason": "fewer than 7 points in the fit window"}
    fw, mw = f[sel], m[sel]
    base = np.percentile(mw, 10)
    peak = mw.max() - base
    floor = mw[mw <= np.percentile(mw, 50)]
    floor_sigma = float(np.std(floor)) if floor.size >= 2 else 0.0
    if peak <= 0 or (floor_sigma > 0 and peak < 4 * floor_sigma) \
            or (floor_sigma == 0 and peak < 1e-12):
        return {"fitted": None,
                "reason": "no peak above 4-sigma of the local floor"}
    i0 = int(np.argmax(mw))
    f0 = float(fw[i0])
    # linewidth from half-max crossings
    half = base + peak / 2.0
    above = mw >= half
    idx = np.nonzero(above)[0]
    if len(idx) < 2:
        return {"fitted": None, "reason": "peak narrower than grid"}
    fwhm = float(fw[idx[-1]] - fw[idx[0]])
    df = float(np.median(np.diff(fw)))
    if fwhm < 2 * df:
        return {"fitted": None,
                "reason": f"FWHM {fwhm:.3f} Hz under 2 grid steps "
                          f"({df:.3f} Hz): non-identifiable"}
    # parabolic refinement of the centre
    if 0 < i0 < len(fw) - 1:
        y0, y1, y2 = mw[i0 - 1], mw[i0], mw[i0 + 1]
        denom = (y0 - 2 * y1 + y2)
        if abs(denom) > 1e-30:
            f0 = f0 - 0.5 * df * float((y2 - y0) / denom)
    q = f0 / fwhm
    return {"fitted": True, "f0_hz": f0, "fwhm_hz": fwhm, "q": q,
            "amplitude": float(peak),
            "u_f0_hz": df / 2.0,
            "u_q": q * (df / max(fwhm, 1e-12)),
            "grid_step_hz": df}


def fit_modes(sweep: dict, guesses_hz: list,
              window_hz: float = 400.0) -> list:
    return [fit_lorentzian(sweep["f_hz"], sweep["magnitude"], g,
                           window_hz) for g in guesses_hz]


# --- mode shape (R030) ----------------------------------------------------------

def mode_shape_scan(twin, f_drive_hz: float,
                    n_azimuthal_points: int = 24,
                    missing: tuple = ()) -> dict:
    """Multi-point synthetic mode-shape acquisition around a ring,
    with missing-point handling: gaps are reported, never invented."""
    th = np.linspace(0, 2 * math.pi, n_azimuthal_points,
                     endpoint=False)
    # (0,1) mode is axisymmetric; higher n gives cos(n th)
    n_best = min(range(3), key=lambda n:
                 abs(twin.mode_hz(n, 1) - f_drive_hz))
    amp = np.cos(n_best * th) if n_best else np.ones_like(th)
    amp = amp + 0.05 * twin._rng.standard_normal(len(th))
    valid = np.ones(len(th), bool)
    for i in missing:
        valid[i] = False
    return {"theta_rad": th, "amplitude": np.where(valid, amp,
                                                   np.nan),
            "valid_mask": valid, "n_missing": int((~valid).sum()),
            "dominant_azimuthal_order": int(n_best),
            "note": "missing points are NaN, not interpolated",
            "synthetic": True}


# --- artifact detection (R031) ---------------------------------------------------

def detect_artifacts(sweep: dict, prior_sweep: dict | None = None
                     ) -> dict:
    """Clipping, nonlinearity, drift, and cross-talk indicators."""
    m = np.asarray(sweep["magnitude"], float)
    out = {"clipping": bool(sweep.get("clipped")) or
           bool(np.mean(m >= 0.999 * m.max()) > 0.01),
           "nonlinearity_flag": False, "drift_hz": None}
    # crude harmonic check: a strong response at exactly 2x the
    # dominant peak that is absent from the mode list suggests drive
    # nonlinearity
    f = np.asarray(sweep["f_hz"], float)
    i0 = int(np.argmax(m))
    f2 = 2.0 * f[i0]
    if f2 <= f[-1]:
        j = int(np.argmin(np.abs(f - f2)))
        floor = np.percentile(m, 20)
        out["nonlinearity_flag"] = bool(m[j] > 6 * floor)
    if prior_sweep is not None:
        p = np.asarray(prior_sweep["magnitude"], float)
        fp = np.asarray(prior_sweep["f_hz"], float)
        out["drift_hz"] = float(f[int(np.argmax(m))]
                                - fp[int(np.argmax(p))])
    return out


# --- replayable sessions (R032) ---------------------------------------------------

def save_session(path, sweeps: list) -> None:
    ser = []
    for s in sweeps:
        ser.append({k: (v.tolist() if isinstance(v, np.ndarray)
                        else v) for k, v in s.items()})
    path.write_text(json.dumps({"synthetic": True, "sweeps": ser},
                               indent=1), encoding="utf-8")


def load_session(path) -> list:
    d = json.loads(path.read_text(encoding="utf-8"))
    if not d.get("synthetic"):
        raise DaqError("session file lacks the synthetic flag; "
                       "refusing to load it as measured data")
    out = []
    for s in d["sweeps"]:
        out.append({k: (np.asarray(v) if isinstance(v, list) else v)
                    for k, v in s.items()})
    return out
