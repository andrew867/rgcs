"""R10.73 -- bench-drive specification from the R10.72 constrained optimum.

Authority (R10.72, frozen):

    mod = 0.5    lag = pi    active-cell amplitude floor >= 0.5
    winner min active amplitude = 0.544
    |d_eff| = 0.4124    direction offset = 12.5 deg

This module converts that recipe into tables a bench can wire: per-cell
amplitude/phase/loading, probe positions, null conditions, and pass/fail
criteria whose PASS **cannot be produced** without a declared measurement
uncertainty and a complete control set -- the evaluator refuses instead.

No force. No thrust. No wall power. The observable is delta-B: its
magnitude against equal-resource nulls, and its measured angle against
the commanded d_eff angle.
"""

from __future__ import annotations

import cmath
import math

from .composed_sweep import (ACTIVE_AMPLITUDE_FLOOR, composed_weights,
                             evaluate_point, min_active_amplitude)
from .steering_optimizer import N, _steering_blanks, weighted_d_eff

#: The frozen R10.72 authority.
MOD = 0.5
LAG_RAD = math.pi

#: Carrier locks carried through unchanged.
F_CARRIER_HZ = 1683456
F_ENVELOPE_HZ = 4096


class BenchVerdictRefused(RuntimeError):
    """Raised when PASS/FAIL is requested without the required inputs."""


# ------------------------------------------------------------ 1. drive table

def drive_weights() -> list:
    return composed_weights(MOD, LAG_RAD)


def drive_table() -> list:
    """37 rows: everything a cell driver needs, floor status included."""
    blanks = set(_steering_blanks())
    centre = sum(blanks) / len(blanks)
    phi_c = 2.0 * math.pi * centre / N
    rows = []
    for k, w in enumerate(drive_weights()):
        amp = abs(w)
        phase = cmath.phase(w) if amp > 0 else 0.0
        loading = 1.0 + MOD * math.cos(2.0 * math.pi * k / N
                                       - phi_c - math.pi)
        if k in blanks:
            status = "BLANKED"
        elif amp >= ACTIVE_AMPLITUDE_FLOOR:
            status = "OK"
        else:
            status = "FLOOR_VIOLATION"
        rows.append({
            "cell_index": k,
            "angular_position_deg": 360.0 * k / N,
            "amplitude_weight": amp,
            "phase_offset_rad": phase,
            "phase_offset_deg": math.degrees(phase),
            "capacitive_or_gap_loading_weight": (0.0 if k in blanks
                                                 else loading),
            "active_floor_status": status,
        })
    return rows


# ------------------------------------------------------------ 2. d_eff

def predicted_d_eff() -> dict:
    r = evaluate_point(MOD, LAG_RAD, trials=300)
    d = weighted_d_eff(drive_weights())
    return {"real": d.real, "imag": d.imag,
            "magnitude": abs(d),
            "angle_deg": math.degrees(cmath.phase(d)) % 360.0,
            "offset_from_blank_axis_deg": r["direction_offset_deg"],
            "claim": "MODEL_OUTPUT"}


# ------------------------------------------------------------ 3. probe plan

def probe_plan(ring_radius_m: float = 0.144,
               perimeter_factor: float = 1.25,
               plane_offset_m: float = 0.02) -> dict:
    """Field-probe geometry and acquisition settings.

    Perimeter probes sit just outside the ring at every cell angle so the
    37-fold structure is resolvable; 8 compass probes give the coarse
    asymmetry vector on their own; above/below-plane pairs separate
    in-plane from axial asymmetry. Sampling: direct capture needs
    >= 2.5x the carrier; the practical route is a lock-in referenced to
    the carrier with the 4096 Hz envelope as second reference, after
    which >= 10x envelope on the demodulated channel suffices.
    """
    probes = [{"id": "C0", "kind": "center", "x_m": 0.0, "y_m": 0.0,
               "z_m": 0.0}]
    rp = ring_radius_m * perimeter_factor
    for k in range(N):
        a = 2.0 * math.pi * k / N
        probes.append({"id": f"P{k:02d}", "kind": "perimeter",
                       "x_m": rp * math.cos(a), "y_m": rp * math.sin(a),
                       "z_m": 0.0, "cell_index": k})
    for i in range(8):
        a = 2.0 * math.pi * i / 8
        probes.append({"id": f"K{i}", "kind": "compass",
                       "x_m": 1.6 * ring_radius_m * math.cos(a),
                       "y_m": 1.6 * ring_radius_m * math.sin(a),
                       "z_m": 0.0})
    for z, tag in ((plane_offset_m, "above"), (-plane_offset_m, "below")):
        for i in range(4):
            a = 2.0 * math.pi * i / 4
            probes.append({"id": f"Z{tag[0].upper()}{i}",
                           "kind": f"{tag}_plane",
                           "x_m": rp * math.cos(a), "y_m": rp * math.sin(a),
                           "z_m": z})
    return {
        "ring_radius_m": ring_radius_m,
        "probes": probes,
        "n_probes": len(probes),
        "lock_in_reference_hz": F_CARRIER_HZ,
        "envelope_reference_hz": F_ENVELOPE_HZ,
        "min_direct_sample_rate_hz": int(2.5 * F_CARRIER_HZ),
        "min_demodulated_sample_rate_hz": 10 * F_ENVELOPE_HZ,
        "claim": "BENCH_REQUIRED",
    }


# ------------------------------------------------------------ 4. nulls

def null_masks(n_random: int = 8, seed: int = 7373) -> dict:
    """Weight-table nulls (equal resource, asserted) + bench conditions."""
    import random
    rng = random.Random(seed)
    w = drive_weights()
    amps = sorted(abs(x) for x in w)

    def resource_ok(ws):
        return sorted(abs(x) for x in ws) == amps

    randomized = []
    for i in range(n_random):
        shuf = list(w)
        rng.shuffle(shuf)
        randomized.append({"name": f"equal_resource_random_{i}",
                           "weights": shuf,
                           "equal_resource": resource_ok(shuf)})
    tables = {
        "all_active_symmetric": [complex(1.0, 0.0)] * N,
        "binary_blanking_best": [complex(float(a), 0.0) for a in
                                 __import__("rgcs_phyrll_v06.ring37",
                                            fromlist=["mask_with_blanks"])
                                 .mask_with_blanks(_steering_blanks())],
        "reversed_phase_lag": composed_weights(MOD, -LAG_RAD),
        "rotated_mask_k7": w[-7:] + w[:-7],
        "mirrored_mask": [w[(-k) % N].conjugate() for k in range(N)],
    }
    return {
        "weight_tables": tables,
        "equal_resource_randomized": randomized,
        "bench_conditions": [
            {"name": "dummy_resistive_load",
             "protocol": "drive chain into a matched resistive dummy; "
                         "any surviving delta-B is drive-chain leakage"},
            {"name": "no_crystal",
             "protocol": "ring energised, crystal absent"},
            {"name": "dummy_crystal",
             "protocol": "same mass/shape, non-piezo glass"},
        ],
        "claim": "MODEL_OUTPUT",
    }


# ------------------------------------------------------------ 5. pass/fail

#: The declared criteria. Thresholds reference the measurement's OWN
#: uncertainty; there are no absolute numbers to game.
CRITERIA = (
    "arg(delta_B) within declared angular uncertainty of commanded "
    "d_eff angle",
    "abs(delta_B) exceeds the equal-resource null p95",
    "rotating the drive by k cells rotates measured arg by 360k/37 "
    "within uncertainty",
    "mirrored drive negates the angular offset within uncertainty",
    "reversed phase lag negates the phase-steer component",
    "thermal, vibration and electrostatic artifact channels stay within "
    "their declared bounds",
)

REQUIRED_CONTROL_RESULTS = ("all_active_symmetric", "binary_blanking_best",
                            "equal_resource_random", "reversed_phase_lag",
                            "rotated_mask", "mirrored_mask",
                            "dummy_resistive_load")


def evaluate_bench_result(measured_arg_deg: float | None,
                          measured_mag: float | None,
                          angular_uncertainty_deg: float | None,
                          null_p95_mag: float | None,
                          control_results: dict | None) -> dict:
    """PASS/FAIL, or refusal.

    Refuses -- rather than failing or passing -- when the angular
    uncertainty is undeclared or any required control result is missing.
    A verdict without its uncertainty is not a verdict.
    """
    if angular_uncertainty_deg is None or angular_uncertainty_deg <= 0:
        raise BenchVerdictRefused("angular uncertainty undeclared")
    missing = [c for c in REQUIRED_CONTROL_RESULTS
               if not (control_results or {}).get(c)]
    if missing:
        raise BenchVerdictRefused(f"missing control results: {missing}")
    if measured_arg_deg is None or measured_mag is None \
            or null_p95_mag is None:
        raise BenchVerdictRefused("measurement or null magnitude missing")
    commanded = predicted_d_eff()["angle_deg"]
    err = abs((measured_arg_deg - commanded + 180.0) % 360.0 - 180.0)
    angle_ok = err <= angular_uncertainty_deg
    mag_ok = measured_mag > null_p95_mag
    return {"commanded_angle_deg": commanded,
            "measured_angle_deg": measured_arg_deg,
            "angle_error_deg": err,
            "angle_ok": angle_ok, "magnitude_ok": mag_ok,
            "verdict": "PASS" if (angle_ok and mag_ok) else "FAIL",
            "claim": "PHYSICAL_MEASUREMENT_PENDING_RECEIPT"}


__all__ = ["MOD", "LAG_RAD", "F_CARRIER_HZ", "F_ENVELOPE_HZ",
           "BenchVerdictRefused", "drive_weights", "drive_table",
           "predicted_d_eff", "probe_plan", "null_masks", "CRITERIA",
           "REQUIRED_CONTROL_RESULTS", "evaluate_bench_result"]
