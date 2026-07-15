"""rgcs_core.timing — synchronized excitation and measurement architecture
(RGCS v3, Agent 07).

One authoritative master timebase, exact-cycle closures for the source key
frequencies, the modulation families, coil A/B phase relationships, the
actual phase at the measured interaction coordinate (cable + driver +
inductive + acoustic + optical + group delay), the coil electrical model
(mutual inductance, distributed capacitance, ringing, saturation, safe
energy), parameter sweeps, the pre-registered factorial control matrix,
cross-correlation fidelity, and safe function-generator presets.

Builds ON, never replaces, the frozen v2 `rgcs_core.drive` envelope
families (D-13/D7-002: `standard`, `half_spacing`, `double_rate` -- the two
readings of the source's ambiguous "shorter by half" keep their distinct
names). No new RSCS ids (D7-001). Safety envelope per D7-003: signal-level
recipes only; no high-voltage construction instructions; no human exposure.

Units: Hz, s (suffixed ms/us where stated), V, A, H, F, ohm, uJ, deg/rad.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Any, Sequence

import numpy as np

from ..provenance import classified

__all__ = [
    "MASTER_CLOCK_DEFAULT", "master_clock", "exact_closure",
    "closure_window_s", "key_closures", "MODULATION_FAMILIES",
    "modulation_family_report", "coil_pair_phases",
    "phase_at_coordinate", "coil_impedance", "self_resonance_hz",
    "mutual_inductance_h", "ring_response", "pulse_energy_uj",
    "safe_drive_check", "SAFETY_LIMITS", "phase_sweep", "sweep_grid",
    "CONTROL_BRANCHES", "control_matrix", "randomized_order",
    "cross_correlation", "signal_fidelity", "function_generator_presets",
]

_C_M_S = 299_792_458.0


# --------------------------------------------------------------------------
# Master clock and exact-cycle closures
# --------------------------------------------------------------------------

#: Authoritative master timebase (ENG): 32.768 kHz TCXO divided by 8 gives
#: the 4096 Hz carrier (matches the v2 drive_config wording); jitter and
#: drift are DECLARED budget fields, to be measured per D7-001.
MASTER_CLOCK_DEFAULT: dict[str, Any] = {
    "reference_hz": 32768.0,
    "reference_source": "32.768 kHz TCXO",
    "carrier_divider": 8,
    "carrier_hz": 4096.0,
    "jitter_budget_ns_rms": 100.0,       # acceptance requirement, not a claim
    "drift_budget_ppm": 2.0,             # TCXO-class stability budget
}


@classified("Derived", sources=("RG-14",),
            note="single authoritative timebase: every channel is derived "
                 "from ONE reference; per-channel latency calibration is a "
                 "required field, not an option")
def master_clock(reference_hz: float = 32768.0, carrier_divider: int = 8,
                 channels: dict[str, float] | None = None) -> dict[str, Any]:
    """Master-clock model: one reference, derived channels, latency slots.

    ``channels`` maps channel name -> target frequency (Hz). Each channel
    reports its exact divider (as a Fraction of the reference) and whether
    it is exactly derivable; non-exact channels are flagged (they need a
    DDS/PLL fractional synthesis stage, Agent 08)."""
    if not (math.isfinite(reference_hz) and reference_hz > 0):
        raise ValueError("reference_hz must be positive and finite")
    if not (isinstance(carrier_divider, int) and carrier_divider >= 1):
        raise ValueError("carrier_divider must be a positive integer")
    carrier_hz = reference_hz / carrier_divider
    out: dict[str, Any] = {
        "reference_hz": float(reference_hz),
        "carrier_divider": carrier_divider,
        "carrier_hz": carrier_hz,
        "jitter_budget_ns_rms": MASTER_CLOCK_DEFAULT["jitter_budget_ns_rms"],
        "drift_budget_ppm": MASTER_CLOCK_DEFAULT["drift_budget_ppm"],
        "channels": {},
    }
    for name, f in (channels or {}).items():
        if not (math.isfinite(f) and f > 0):
            raise ValueError(f"channel {name!r} frequency must be positive")
        ratio = Fraction(f).limit_denominator(10 ** 9) / Fraction(
            reference_hz).limit_denominator(10 ** 9)
        exact = (Fraction(reference_hz).limit_denominator(10 ** 9)
                 % Fraction(f).limit_denominator(10 ** 9) == 0)
        out["channels"][name] = {
            "frequency_hz": float(f),
            "ratio_to_reference": ratio,
            "integer_divider": exact,
            "latency_calibration_s": None,   # MUST be measured per channel
        }
    return out


@classified("Derived", sources=("RG-12", "RG-13"),
            note="cycles = f*T; integer iff the window closes exactly. "
                 "Golden: 125 ms closes 4096 Hz (512) and 1496 Hz (187)")
def exact_closure(frequencies_hz: Sequence[float],
                  window_s: float) -> dict[str, Any]:
    """Cycle counts of each frequency in a window; flags exact closure.

    A window 'closes' a frequency when f*T is an integer (the drive ends at
    zero phase). Golden case (brief item 7): T = 0.125 s -> 4096 Hz: 512
    cycles, 1496 Hz: 187 cycles, both exact."""
    if not (math.isfinite(window_s) and window_s > 0):
        raise ValueError("window_s must be positive and finite")
    rows = {}
    all_exact = True
    for f in frequencies_hz:
        if not (math.isfinite(f) and f > 0):
            raise ValueError("frequencies must be positive and finite")
        cycles = f * window_s
        # exact iff f*T is integer as a rational (tolerate float repr only)
        frac = Fraction(f).limit_denominator(10 ** 6) * Fraction(
            window_s).limit_denominator(10 ** 6)
        is_int = frac.denominator == 1
        all_exact &= is_int
        rows[f] = {"cycles": cycles, "integer": is_int,
                   "residue_cycles": cycles - round(cycles)}
    return {"window_s": float(window_s), "per_frequency": rows,
            "all_close": bool(all_exact)}


@classified("Derived", sources=("RG-12", "RG-13"),
            note="minimal common closure window: T = k / gcd of the "
                 "rational frequencies")
def closure_window_s(frequencies_hz: Sequence[float]) -> float:
    """Smallest window T > 0 in which EVERY frequency completes an integer
    number of cycles: T = 1 / gcd(f_1, ..., f_n) over the rationals."""
    fracs = []
    for f in frequencies_hz:
        if not (math.isfinite(f) and f > 0):
            raise ValueError("frequencies must be positive and finite")
        fracs.append(Fraction(f).limit_denominator(10 ** 6))
    if not fracs:
        raise ValueError("need at least one frequency")
    g = fracs[0]
    for fr in fracs[1:]:
        # gcd over rationals: gcd(a/b, c/d) = gcd(a*d, c*b) / (b*d)
        g = Fraction(math.gcd(g.numerator * fr.denominator,
                              fr.numerator * g.denominator),
                     g.denominator * fr.denominator)
    return float(1 / g)


@classified("Derived", sources=("RG-12", "RG-13"),
            note="key-frequency closures vs the 4096 Hz carrier; the source "
                 "key values 1496/644/587 Hz are Source claims (RG-13) that "
                 "parameterize windows, they carry no truth value")
def key_closures(carrier_hz: float = 4096.0) -> dict[str, Any]:
    """Closure windows of each source key against the carrier.

    Golden rows: 1496 Hz closes with 4096 Hz in 125 ms (187 & 512 cycles);
    644 Hz in 250 ms (161 & 1024); 587 Hz (coprime to 4096) needs 1 s
    (587 & 4096)."""
    out: dict[str, Any] = {"carrier_hz": float(carrier_hz), "keys": {}}
    for key_hz in (1496.0, 644.0, 587.0):
        t = closure_window_s([carrier_hz, key_hz])
        out["keys"][key_hz] = {
            "closure_window_s": t,
            "key_cycles": round(key_hz * t),
            "carrier_cycles": round(carrier_hz * t),
        }
    return out


#: Modulation families (brief): 20 and 21 Hz are Source-stated electrode
#: rates (RG-13); 20.48 Hz = 4096/200 and 40.96 Hz = 4096/100 are the
#: exact-cycle engineering variants (integer-ratio sub-harmonics of the
#: carrier). The source values are NOT replaced by the exact variants.
MODULATION_FAMILIES: dict[str, dict[str, Any]] = {
    "mod_20":    {"frequency_hz": 20.0,   "origin": "Source claim (RG-13)",
                  "carrier_ratio": 4096.0 / 20.0, "exact_subharmonic": False},
    "mod_20_48": {"frequency_hz": 20.48,  "origin": "Derived exact variant",
                  "carrier_ratio": 200.0, "exact_subharmonic": True},
    "mod_21":    {"frequency_hz": 21.0,   "origin": "Source claim (RG-13)",
                  "carrier_ratio": 4096.0 / 21.0, "exact_subharmonic": False},
    "mod_40_96": {"frequency_hz": 40.96,  "origin": "Derived exact variant",
                  "carrier_ratio": 100.0, "exact_subharmonic": True},
}


@classified("Derived", sources=("RG-13",),
            note="20/21 Hz are Source rates; 20.48/40.96 Hz are the exact "
                 "carrier/200 and carrier/100 engineering variants")
def modulation_family_report(carrier_hz: float = 4096.0) -> dict[str, Any]:
    """Closure report for the four modulation families vs the carrier."""
    report = {}
    for name, fam in MODULATION_FAMILIES.items():
        f = fam["frequency_hz"]
        report[name] = {
            **fam,
            "closure_window_s": closure_window_s([carrier_hz, f]),
        }
    return report


# --------------------------------------------------------------------------
# Coil pair and phase at the interaction coordinate
# --------------------------------------------------------------------------

@classified("Derived", sources=("RG-14",),
            note="coil A/B relationship: 'opposed' = complementary 180 deg "
                 "(WB3 wording); 'in_phase' = 0 deg; explicit offset allowed")
def coil_pair_phases(phase_a_deg: float,
                     mode: str = "opposed",
                     offset_deg: float | None = None) -> dict[str, float]:
    """Coil A / coil B commanded phases (deg, wrapped to [0, 360)).

    ``mode``: 'opposed' (B = A + 180, the complementary source setting),
    'in_phase' (B = A), or 'offset' (B = A + offset_deg, for phase sweeps)."""
    if not math.isfinite(phase_a_deg):
        raise ValueError("phase_a_deg must be finite")
    if mode == "opposed":
        off = 180.0
    elif mode == "in_phase":
        off = 0.0
    elif mode == "offset":
        if offset_deg is None or not math.isfinite(offset_deg):
            raise ValueError("mode 'offset' requires a finite offset_deg")
        off = float(offset_deg)
    else:
        raise ValueError("mode must be 'opposed', 'in_phase', or 'offset'")
    a = float(phase_a_deg) % 360.0
    return {"coil_a_deg": a, "coil_b_deg": (a + off) % 360.0,
            "offset_deg": off}


@classified("Derived", sources=("RG-14",),
            note="actual phase at the measured interaction coordinate = "
                 "commanded phase + 2*pi*f*(cable + driver + acoustic + "
                 "optical + group delays) + inductive phase atan(wL/R); "
                 "every term reported separately (never inferred from GPIO "
                 "timing alone)")
def phase_at_coordinate(frequency_hz: float,
                        commanded_phase_deg: float = 0.0,
                        cable_length_m: float = 0.0,
                        cable_velocity_factor: float = 0.66,
                        driver_delay_s: float = 0.0,
                        coil_inductance_h: float = 0.0,
                        coil_resistance_ohm: float = float("inf"),
                        acoustic_path_mm: float = 0.0,
                        acoustic_speed_m_s: float = 0.0,
                        optical_transit_s: float = 0.0,
                        group_delay_s: float = 0.0) -> dict[str, Any]:
    """Accumulate every delay between the generator and the measured
    interaction coordinate and report the ACTUAL phase there.

    The interaction coordinate is wherever the run manifest says it was
    MEASURED (geometric centre, predicted node, and measured node are three
    distinct locations -- the manifest must name one). Terms:
      cable      : length / (velocity_factor * c)
      driver     : datasheet/measured latency (s)
      inductive  : atan(2*pi*f*L / R) of the coil load (rad; 0 if L = 0)
      acoustic   : path / speed (use rgcs_core.anisotropy wave_speeds for
                   the oriented speed, NOT a guessed scalar)
      optical    : transit time from rgcs_core.optics.ray_to_target
      group      : dispersion group delay (rscs_core RSCS-O.18/O.8)
    """
    if not (math.isfinite(frequency_hz) and frequency_hz > 0):
        raise ValueError("frequency_hz must be positive and finite")
    for name, v in (("commanded_phase_deg", commanded_phase_deg),
                    ("cable_length_m", cable_length_m),
                    ("driver_delay_s", driver_delay_s),
                    ("coil_inductance_h", coil_inductance_h),
                    ("acoustic_path_mm", acoustic_path_mm),
                    ("optical_transit_s", optical_transit_s),
                    ("group_delay_s", group_delay_s)):
        if not math.isfinite(v) or v < 0 and name != "commanded_phase_deg":
            if name == "commanded_phase_deg" and math.isfinite(v):
                continue
            raise ValueError(f"{name} must be finite and >= 0")
    if not (0 < cable_velocity_factor <= 1):
        raise ValueError("cable_velocity_factor must be in (0, 1]")

    cable_s = cable_length_m / (cable_velocity_factor * _C_M_S)
    if acoustic_path_mm > 0:
        if not (math.isfinite(acoustic_speed_m_s) and acoustic_speed_m_s > 0):
            raise ValueError("acoustic_speed_m_s must be positive when an "
                             "acoustic path is given")
        acoustic_s = (acoustic_path_mm * 1e-3) / acoustic_speed_m_s
    else:
        acoustic_s = 0.0
    if coil_inductance_h > 0:
        if not (coil_resistance_ohm > 0):
            raise ValueError("coil_resistance_ohm must be positive when an "
                             "inductance is given")
        inductive_rad = math.atan2(
            2 * math.pi * frequency_hz * coil_inductance_h,
            coil_resistance_ohm)
    else:
        inductive_rad = 0.0

    delays = {
        "cable_s": cable_s,
        "driver_s": float(driver_delay_s),
        "acoustic_s": acoustic_s,
        "optical_s": float(optical_transit_s),
        "group_s": float(group_delay_s),
    }
    total_delay_s = sum(delays.values())
    delay_rad = 2 * math.pi * frequency_hz * total_delay_s
    total_rad = (math.radians(commanded_phase_deg) + delay_rad
                 + inductive_rad)
    return {
        "delays_s": delays,
        "total_delay_s": total_delay_s,
        "inductive_phase_rad": inductive_rad,
        "phase_from_delays_rad": delay_rad,
        "actual_phase_rad": total_rad % (2 * math.pi),
        "actual_phase_deg": math.degrees(total_rad) % 360.0,
    }


# --------------------------------------------------------------------------
# Coil electrical model: impedance, resonance, ringing, saturation, energy
# --------------------------------------------------------------------------

@classified("Established", sources=("series RL + parallel C model",),
            note="Z = R + jwL in parallel with the distributed capacitance")
def coil_impedance(frequency_hz: float, inductance_h: float,
                   resistance_ohm: float,
                   parallel_capacitance_f: float = 0.0) -> dict[str, float]:
    """Coil impedance with distributed capacitance: (R + jwL) || (1/jwC)."""
    if not (math.isfinite(frequency_hz) and frequency_hz > 0):
        raise ValueError("frequency_hz must be positive and finite")
    for name, v in (("inductance_h", inductance_h),
                    ("resistance_ohm", resistance_ohm),
                    ("parallel_capacitance_f", parallel_capacitance_f)):
        if not (math.isfinite(v) and v >= 0):
            raise ValueError(f"{name} must be finite and >= 0")
    w = 2 * math.pi * frequency_hz
    z_series = complex(resistance_ohm, w * inductance_h)
    if parallel_capacitance_f > 0:
        z_c = 1.0 / complex(0.0, w * parallel_capacitance_f)
        z = z_series * z_c / (z_series + z_c)
    else:
        z = z_series
    return {"impedance_ohm": abs(z), "phase_rad": math.atan2(z.imag, z.real),
            "real_ohm": z.real, "imag_ohm": z.imag}


@classified("Established", sources=("LC resonance",),
            note="f_sr = 1/(2*pi*sqrt(L*C)): the coil is only 'an inductor' "
                 "well below this")
def self_resonance_hz(inductance_h: float, capacitance_f: float) -> float:
    """Self-resonance from inductance and distributed capacitance."""
    for name, v in (("inductance_h", inductance_h),
                    ("capacitance_f", capacitance_f)):
        if not (math.isfinite(v) and v > 0):
            raise ValueError(f"{name} must be positive and finite")
    return 1.0 / (2 * math.pi * math.sqrt(inductance_h * capacitance_f))


@classified("Established", sources=("coupled-inductor model",),
            note="M = k*sqrt(L1*L2), 0 <= k <= 1")
def mutual_inductance_h(l1_h: float, l2_h: float, k: float) -> float:
    """Mutual inductance of the coil pair: M = k sqrt(L1 L2)."""
    for name, v in (("l1_h", l1_h), ("l2_h", l2_h)):
        if not (math.isfinite(v) and v > 0):
            raise ValueError(f"{name} must be positive and finite")
    if not (math.isfinite(k) and 0.0 <= k <= 1.0):
        raise ValueError("coupling k must be in [0, 1]")
    return k * math.sqrt(l1_h * l2_h)


@classified("Established", sources=("series RLC step response",),
            note="ring frequency, Q, damping ratio, and overshoot of the "
                 "pulse edge into the coil (drives the 'ringing' control)")
def ring_response(inductance_h: float, capacitance_f: float,
                  resistance_ohm: float) -> dict[str, float]:
    """Series-RLC ringing of a pulse edge: f_ring, Q, zeta, overshoot."""
    for name, v in (("inductance_h", inductance_h),
                    ("capacitance_f", capacitance_f),
                    ("resistance_ohm", resistance_ohm)):
        if not (math.isfinite(v) and v > 0):
            raise ValueError(f"{name} must be positive and finite")
    w0 = 1.0 / math.sqrt(inductance_h * capacitance_f)
    zeta = (resistance_ohm / 2.0) * math.sqrt(
        capacitance_f / inductance_h)
    q = 1.0 / (2.0 * zeta)
    if zeta < 1.0:
        wd = w0 * math.sqrt(1.0 - zeta * zeta)
        overshoot = math.exp(-math.pi * zeta / math.sqrt(1 - zeta * zeta))
    else:
        wd, overshoot = 0.0, 0.0            # overdamped: no ring
    return {"natural_hz": w0 / (2 * math.pi),
            "ring_hz": wd / (2 * math.pi),
            "q_factor": q, "damping_ratio": zeta,
            "overshoot_fraction": overshoot,
            "underdamped": zeta < 1.0}


@classified("Established", sources=("magnetic energy",),
            note="E = 1/2 L I^2, reported in uJ (v2 micro-pulse convention)")
def pulse_energy_uj(inductance_h: float, peak_current_a: float) -> float:
    """Stored magnetic energy per pulse: E = L I^2 / 2 (uJ)."""
    if not (math.isfinite(inductance_h) and inductance_h > 0):
        raise ValueError("inductance_h must be positive and finite")
    if not (math.isfinite(peak_current_a) and peak_current_a >= 0):
        raise ValueError("peak_current_a must be finite and >= 0")
    return 0.5 * inductance_h * peak_current_a ** 2 * 1e6


#: Public-replication safety envelope (D7-003). These are HARD limits for
#: every schema/preset in this repository; exceeding them is out of scope.
SAFETY_LIMITS: dict[str, float] = {
    "voltage_v_max": 30.0,
    "current_a_max": 3.0,
    "pulse_energy_mj_max": 5.0,
    "specimen_temp_rise_c_max": 5.0,
    "laser_power_mw_max": 5.0,
}


@classified("Derived", sources=("RG-13", "RG-14"),
            note="D7-003 safety envelope check; dummy-load-first rule; "
                 "saturation flagged against the driver current limit")
def safe_drive_check(voltage_v: float, peak_current_a: float,
                     inductance_h: float,
                     specimen_temp_rise_c: float = 0.0,
                     dummy_load_validated: bool = False) -> dict[str, Any]:
    """Check a drive point against the D7-003 public-replication envelope.

    Returns ok + individual verdicts + reasons. A drive point is only
    'cleared' when it passes ALL limits AND has been validated on an
    instrumented dummy load first."""
    for name, v in (("voltage_v", voltage_v),
                    ("peak_current_a", peak_current_a),
                    ("inductance_h", inductance_h),
                    ("specimen_temp_rise_c", specimen_temp_rise_c)):
        if not (math.isfinite(v) and v >= 0):
            raise ValueError(f"{name} must be finite and >= 0")
    energy_mj = pulse_energy_uj(inductance_h, peak_current_a) / 1000.0 \
        if inductance_h > 0 else 0.0
    checks = {
        "voltage_ok": voltage_v <= SAFETY_LIMITS["voltage_v_max"],
        "current_ok": peak_current_a <= SAFETY_LIMITS["current_a_max"],
        "energy_ok": energy_mj <= SAFETY_LIMITS["pulse_energy_mj_max"],
        "thermal_ok": (specimen_temp_rise_c
                       <= SAFETY_LIMITS["specimen_temp_rise_c_max"]),
        "dummy_load_validated": bool(dummy_load_validated),
    }
    reasons = [k for k, ok in checks.items() if not ok]
    return {"ok": not reasons, "pulse_energy_mj": energy_mj,
            "checks": checks, "failed": reasons,
            "limits": dict(SAFETY_LIMITS)}


# --------------------------------------------------------------------------
# Sweeps, factorial control matrix, randomization
# --------------------------------------------------------------------------

@classified("Derived", sources=(),
            note="full 0-360 deg phase sweep (brief item 5); inclusive of 0, "
                 "exclusive of 360 (S^1 wrap)")
def phase_sweep(step_deg: float = 15.0) -> list[float]:
    """Phase sweep points over [0, 360) deg."""
    if not (math.isfinite(step_deg) and 0 < step_deg <= 360):
        raise ValueError("step_deg must be in (0, 360]")
    n = int(round(360.0 / step_deg))
    if abs(n * step_deg - 360.0) > 1e-9:
        raise ValueError("step_deg must divide 360 evenly")
    return [i * step_deg for i in range(n)]


@classified("Derived", sources=(),
            note="cartesian sweep grid over declared parameter lists; "
                 "deterministic ordering")
def sweep_grid(parameters: dict[str, Sequence[Any]]) -> list[dict[str, Any]]:
    """Cartesian product of parameter value lists as a list of run dicts.
    Sweepable parameters (brief): phase, delay, frequency, amplitude,
    polarization, direction, loading."""
    if not parameters:
        raise ValueError("need at least one parameter")
    names = list(parameters)
    grids: list[dict[str, Any]] = [{}]
    for name in names:
        vals = list(parameters[name])
        if not vals:
            raise ValueError(f"parameter {name!r} has no values")
        grids = [{**g, name: v} for g in grids for v in vals]
    return grids


#: The pre-registered factorial control branches (brief). Every campaign
#: manifest must state which branches ran and which were skipped (skipping
#: is allowed; silent omission is not).
CONTROL_BRANCHES: tuple[str, ...] = (
    "coil_only", "optical_only", "acoustic_only", "combined",
    "dummy_crystal", "glass_control", "rotated_crystal", "sham_timing",
    "thermal_control", "randomized_blinded",
)


@classified("Derived", sources=(),
            note="factorial matrix = control branches x sweep grid; "
                 "randomized order is seeded (reproducible)")
def control_matrix(sweep: list[dict[str, Any]] | None = None,
                   branches: Sequence[str] = CONTROL_BRANCHES,
                   seed: int | None = None) -> list[dict[str, Any]]:
    """Pre-registered factorial experiment matrix: every control branch
    crossed with the sweep grid; optionally seeded-shuffled with blind
    codes attached."""
    for b in branches:
        if b not in CONTROL_BRANCHES:
            raise ValueError(f"unknown control branch {b!r}")
    rows = [{"branch": b, **(pt or {})}
            for b in branches for pt in (sweep or [{}])]
    for i, row in enumerate(rows):
        row["run_index"] = i
    if seed is not None:
        rows = randomized_order(rows, seed)
        for i, row in enumerate(rows):
            row["blind_code"] = f"BC-{seed:04d}-{i:04d}"
    return rows


@classified("Derived", sources=(),
            note="seeded deterministic shuffle (numpy default_rng); the "
                 "seed is recorded in the manifest for unblinding")
def randomized_order(items: Sequence[Any], seed: int) -> list[Any]:
    """Deterministic seeded shuffle of the run order."""
    if not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(items))
    return [items[int(i)] for i in order]


# --------------------------------------------------------------------------
# Signal fidelity / cross-correlation
# --------------------------------------------------------------------------

@classified("Established", sources=("normalized cross-correlation",),
            note="normalized full cross-correlation; returns peak value and "
                 "lag (s); the measurement layer for phase/delay checks")
def cross_correlation(x: np.ndarray, y: np.ndarray,
                      sample_rate_hz: float) -> dict[str, Any]:
    """Normalized cross-correlation of two records with the peak lag.

    Correlation is normalized so identical records peak at 1.0 at lag 0.
    lag_s > 0 means y LAGS x by that time."""
    a = np.asarray(x, dtype=float)
    b = np.asarray(y, dtype=float)
    if a.ndim != 1 or a.shape != b.shape or a.size < 2:
        raise ValueError("records must be equal-length 1-D with >= 2 samples")
    if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
        raise ValueError("records must be finite")
    if not (math.isfinite(sample_rate_hz) and sample_rate_hz > 0):
        raise ValueError("sample_rate_hz must be positive and finite")
    a0 = a - a.mean()
    b0 = b - b.mean()
    denom = math.sqrt(float(np.sum(a0 ** 2)) * float(np.sum(b0 ** 2)))
    if denom == 0.0:
        raise ValueError("records must have non-zero variance")
    corr = np.correlate(a0, b0, mode="full") / denom
    peak_idx = int(np.argmax(np.abs(corr)))
    lag_samples = (a.size - 1) - peak_idx
    return {"peak_correlation": float(corr[peak_idx]),
            "lag_samples": int(lag_samples),
            "lag_s": lag_samples / sample_rate_hz}


@classified("Derived", sources=("normalized cross-correlation",),
            note="zero-lag normalized correlation as the scalar signal-"
                 "fidelity figure (EP-05-02 principle, classical form)")
def signal_fidelity(reference: np.ndarray, measured: np.ndarray) -> float:
    """Zero-lag normalized correlation in [-1, 1]: the scalar fidelity of a
    measured record against its reference (1 = perfect shape fidelity)."""
    a = np.asarray(reference, dtype=float)
    b = np.asarray(measured, dtype=float)
    if a.ndim != 1 or a.shape != b.shape or a.size < 2:
        raise ValueError("records must be equal-length 1-D with >= 2 samples")
    a0 = a - a.mean()
    b0 = b - b.mean()
    denom = math.sqrt(float(np.sum(a0 ** 2)) * float(np.sum(b0 ** 2)))
    if denom == 0.0:
        raise ValueError("records must have non-zero variance")
    return float(np.sum(a0 * b0) / denom)


# --------------------------------------------------------------------------
# Function-generator presets (signal-level only, D7-003)
# --------------------------------------------------------------------------

@classified("Derived", sources=("RG-12", "RG-13", "RG-14"),
            note="signal-level recipes ONLY (D7-003): generator settings "
                 "into a driver/dummy load; no high-voltage construction. "
                 "Source-stated operating points remain Source claims")
def function_generator_presets() -> dict[str, dict[str, Any]]:
    """Machine-readable function-generator presets for the named modes.

    All presets are SIGNAL-LEVEL (generator output <= 10 Vpp into the
    driver input or a dummy load); the D7-003 envelope applies to whatever
    the driver produces, and `safe_drive_check` must clear every operating
    point on a dummy load before a specimen run."""
    presets: dict[str, dict[str, Any]] = {
        "carrier_4096": {
            "waveform": "square", "frequency_hz": 4096.0,
            "amplitude_vpp": 5.0, "phase_between_outputs_deg": 180.0,
            "notes": "coil pair carrier; complementary outputs (opposed)",
        },
        "sound_key_1496": {
            "waveform": "sine", "frequency_hz": 1496.0,
            "amplitude_vpp": 2.0, "burst": {"on_s": 3.0, "off_s": 3.0},
            "notes": "sound key (Source frequency, RG-13); acoustic branch",
        },
        "sound_key_644": {
            "waveform": "sine", "frequency_hz": 644.0,
            "amplitude_vpp": 2.0, "burst": {"on_s": 3.0, "off_s": 3.0},
            "notes": "sound key (Source frequency, RG-13)",
        },
        "sound_key_587": {
            "waveform": "sine", "frequency_hz": 587.0,
            "amplitude_vpp": 2.0, "burst": {"on_s": 3.0, "off_s": 3.0},
            "notes": "sound key (Source frequency, RG-13)",
        },
        "electrode_20": {
            "waveform": "pulse", "frequency_hz": 20.0,
            "amplitude_vpp": 5.0, "pulse_width_us": 500.0,
            "notes": "electrode rate family (Source, RG-13); 21 Hz variant "
                     "= same preset at 21 Hz; 20.48/40.96 Hz are the "
                     "exact-cycle variants (MODULATION_FAMILIES)",
        },
        "macro_standard": {
            "waveform": "burst_macro", "carrier_hz": 4096.0,
            "mode": "standard",
            "notes": "46/46x4/184 ms envelope (v2 drive_sequence)",
        },
        "macro_half_spacing": {
            "waveform": "burst_macro", "carrier_hz": 4096.0,
            "mode": "half_spacing",
            "notes": "46/23x4/92 ms envelope; keeps its unambiguous frozen "
                     "name (D7-002)",
        },
        "macro_double_rate": {
            "waveform": "burst_macro", "carrier_hz": 4096.0,
            "mode": "double_rate",
            "notes": "23/23x4/92 ms envelope; the other reading of "
                     "'shorter by half' (D7-002)",
        },
        "laser_trigger": {
            "waveform": "ttl_trigger", "frequency_hz": 20.0,
            "amplitude_vpp": 3.3,
            "notes": "isolated TTL to the optical modulator/laser trigger; "
                     "synchronized_to master_clock (optical_probe schema); "
                     "laser limits per D6 schema (class <= 3R, <= 5 mW)",
        },
    }
    for p in presets.values():
        amp = p.get("amplitude_vpp", 0.0)
        if amp > 10.0:
            raise AssertionError("preset exceeds signal-level envelope")
    return presets
