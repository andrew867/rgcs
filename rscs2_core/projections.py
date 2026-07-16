"""Optical, coil, and drive projections (Agent 08, RSCS2-E.8..E.11).

Computational projections only — no high-power hardware content. The
frozen safety envelopes bind every run description: optical class <=3R,
<=5 mW, interlock (D6); coil <=30 V, <=3 A, <=5 mJ/pulse,
dummy-load-first (D7-003).

Everything here EXTENDS the frozen v3 modules without modifying them:
  * rgcs_core.optics    — indices, Snell, ray/OPL/phase, photoelastic;
  * rgcs_core.timing    — coil pair phases, phase budget, closures;
  * rgcs_core.geometry  — node priors (RGCS-M.38/39);
  * rscs_core.coordinates.medium.PolarizationState (RSCS-C.9).

OCTAVE ARITHMETIC DISCLAIMER (stated, per user decision): the
"octave" wavelength presets are pure arithmetic — the optical frequency
2^49 Hz is the 4096 Hz carrier raised 37 octaves and 2^48 Hz is 36
octaves; lambda = c / 2^k. This is a numeric relationship between two
frequencies. It is NOT evidence of any special optical-acoustic
coupling; no such claim is made or implied.
"""

from __future__ import annotations

import math
from typing import Any, Callable

import numpy as np

from rgcs_core.geometry.crystal import apothem_mm
from rgcs_core.geometry.nodes import node_prior_mm
from rgcs_core.optics import (QUARTZ_N_E, QUARTZ_N_O, QUARTZ_PHOTOELASTIC,
                              photoelastic_index_shift, ray_to_target,
                              snell_refraction)
from rgcs_core.timing import (coil_pair_phases, exact_closure, key_closures,
                              phase_at_coordinate)

from .crystal110 import CanonicalCrystal

__all__ = [
    "WAVELENGTH_PRESETS_NM", "quartz_sellmeier", "uniaxial_index",
    "refract_ray", "crystal_targets", "shaft_apothem_mm", "probe_paths",
    "photoelastic_phase_shift_rad", "absorption_deposition_w",
    "jones_waveplate", "apply_jones",
    "circular_coil", "biot_savart_polyline", "coil_pair_field",
    "loop_axis_field_t", "field_gradient", "magnetic_energy_density_j_m3",
    "assemble_body_force", "project_force_vector",
    "capacitive_drive_traction_pa", "coil_coupling_report",
    "macro_sequences", "drive_phase_table",
]

_C_M_S = 299_792_458.0
_MU0 = 4.0e-7 * math.pi

#: Wavelength presets (nm). The two "octave" targets are ARITHMETIC:
#: lambda = c / 2^49 and c / 2^48 (the 4096 Hz carrier is 2^12 Hz; the
#: optical frequencies are 37 and 36 octaves above it). This numeric
#: relationship is not proof of special optical coupling (disclaimer in
#: the module docstring).
WAVELENGTH_PRESETS_NM: dict[str, dict[str, Any]] = {
    "green_532":  {"nm": 532.0,
                   "origin": "commercial DPSS/doubled Nd:YAG line"},
    "octave_green": {"nm": _C_M_S / 2.0 ** 49 * 1e9,   # 532.538...
                     "origin": "ARITHMETIC: c / 2^49 Hz "
                               "(4096 Hz * 2^37); no coupling claim"},
    "hene_633":   {"nm": 632.8, "origin": "HeNe reference line"},
    "diode_635":  {"nm": 635.0, "origin": "common diode reference"},
    "ir_1064":    {"nm": 1064.0, "origin": "Nd:YAG fundamental"},
    "octave_ir":  {"nm": _C_M_S / 2.0 ** 48 * 1e9,     # 1065.077...
                   "origin": "ARITHMETIC: c / 2^48 Hz "
                             "(4096 Hz * 2^36); no coupling claim"},
}


# --- anisotropic refractive index (RSCS2-E.8) -------------------------

def quartz_sellmeier(wavelength_nm: float) -> dict[str, float]:
    """alpha-quartz ordinary/extraordinary indices at a wavelength via
    the Ghosh (1999) Sellmeier fits (Opt. Commun. 163, 95; validity
    0.198-2.053 um). Conservative-extension anchor: at 589.3 nm this
    reproduces the FROZEN handbook constants QUARTZ_N_O/QUARTZ_N_E."""
    if not (math.isfinite(wavelength_nm) and 198.0 <= wavelength_nm <= 2053.0):
        raise ValueError("wavelength must be in [198, 2053] nm "
                         "(Ghosh 1999 validity range)")
    l2 = (wavelength_nm * 1e-3) ** 2          # um^2
    n_o2 = (1.28604141 + 1.07044083 * l2 / (l2 - 1.00585997e-2)
            + 1.10202242 * l2 / (l2 - 100.0))
    n_e2 = (1.28851804 + 1.09509924 * l2 / (l2 - 1.02101864e-2)
            + 1.15662475 * l2 / (l2 - 100.0))
    return {"n_o": math.sqrt(n_o2), "n_e": math.sqrt(n_e2),
            "birefringence": math.sqrt(n_e2) - math.sqrt(n_o2)}


def uniaxial_index(theta_from_optic_axis_rad: float, n_o: float,
                   n_e: float) -> float:
    """Extraordinary-ray index n(theta) from the index ellipsoid:
    1/n^2 = cos^2(theta)/n_o^2 + sin^2(theta)/n_e^2 (standard uniaxial
    crystal optics). theta = angle between wave normal and optic axis
    (crystal C-axis, +Z body frame by default). The o-ray always sees
    n_o. This IS the o/e split 'where feasible' (spec): plane-wave
    indices; full double-refraction walk-off is NOT modelled and any
    walk-off-dependent quantity must fail loud rather than use this."""
    for name, n in (("n_o", n_o), ("n_e", n_e)):
        if not (math.isfinite(n) and n >= 1.0):
            raise ValueError(f"{name} must be finite and >= 1")
    c, s = math.cos(theta_from_optic_axis_rad), \
        math.sin(theta_from_optic_axis_rad)
    return 1.0 / math.sqrt(c * c / n_o ** 2 + s * s / n_e ** 2)


def refract_ray(direction: np.ndarray, outward_normal: np.ndarray,
                n_outside: float, n_inside: float) -> dict[str, Any]:
    """Vector Snell refraction of an INCOMING ray at a facet.

    ``direction`` points toward the surface; ``outward_normal`` points
    out of the crystal. Returns the transmitted unit direction and the
    incidence/refraction angles. Raises on total internal reflection
    (only possible high->low index) — consistent with the frozen scalar
    snell_refraction."""
    d = np.asarray(direction, dtype=float)
    nrm = np.asarray(outward_normal, dtype=float)
    d = d / np.linalg.norm(d)
    nrm = nrm / np.linalg.norm(nrm)
    cos_i = -float(np.dot(d, nrm))
    if cos_i <= 0.0:
        raise ValueError("direction must point INTO the surface "
                         "(against the outward normal)")
    theta_i_deg = math.degrees(math.acos(min(1.0, cos_i)))
    # frozen scalar law fixes the transmitted angle (and TIR raise)
    theta_t_deg = snell_refraction(theta_i_deg, n_outside, n_inside)
    r = n_outside / n_inside
    cos_t = math.cos(math.radians(theta_t_deg))
    t = r * d + (r * cos_i - cos_t) * nrm
    t = t / np.linalg.norm(t)
    return {"transmitted": t, "incidence_deg": theta_i_deg,
            "refraction_deg": theta_t_deg}


# --- crystal targets and probe paths ----------------------------------

def crystal_targets(c: CanonicalCrystal) -> dict[str, Any]:
    """The path-target menu (body frame, female apex z=0):
    geometric centre (RGCS-M.38), RGCS node prior (frozen RGCS-M.39),
    and the eye-candidate slot — None until an eye coordinate is
    MEASURED or derived by the diagnostic engine; never assumed."""
    zc = c.length_mm / 2.0
    zn = node_prior_mm(c.length_mm, c.female_cap_height_mm,
                       c.male_cap_height_mm)
    return {
        "geometric_centre_mm": np.array([0.0, 0.0, zc]),
        "node_prior_mm": np.array([0.0, 0.0, zn]),
        "eye_candidate_mm": None,    # supplied later by Agent 09, if found
    }


def shaft_apothem_mm(c: CanonicalCrystal, z_mm: float) -> float:
    """Apothem of the tapered hexagonal shaft at height z (body frame).
    Linear taper between the wide ring (top of female cap) and the
    narrow ring (bottom of male cap)."""
    hf, hm = c.female_cap_height_mm, c.male_cap_height_mm
    if not (hf <= z_mm <= c.length_mm - hm):
        raise ValueError("z outside the shaft")
    a_f = apothem_mm(c.wide_diameter_mm, c.facets)
    a_m = apothem_mm(c.narrow_diameter_mm, c.facets)
    return a_f + (a_m - a_f) * (z_mm - hf) / c.shaft_length_mm


def probe_paths(c: CanonicalCrystal, wavelength_nm: float = 632.8,
                eye_candidate_mm: np.ndarray | None = None) -> dict:
    """The Agent-08 probe-path menu on the canonical crystal, all via
    the FROZEN ray_to_target (straight-ray, o-index at the requested
    wavelength from the Sellmeier fit):

      axial_tx_to_rx : male apex (transmitter end) -> female apex
      axial_rx_to_tx : female apex -> male apex (reciprocity partner)
      side_to_centre / side_to_node_prior [/ side_to_eye_candidate]:
          entry at the lower shaft facet (z = 0.4 L per the canonical
          region annotations), aimed at each target.
    """
    n_o = quartz_sellmeier(wavelength_nm)["n_o"]
    tg = crystal_targets(c)
    ze = 0.4 * c.length_mm
    entry_side = np.array([shaft_apothem_mm(c, ze), 0.0, ze])
    apex_f = np.array([0.0, 0.0, 0.0])
    apex_m = np.array([0.0, 0.0, c.length_mm])
    paths = {
        "axial_tx_to_rx": ray_to_target(apex_m, apex_f, n_o, wavelength_nm),
        "axial_rx_to_tx": ray_to_target(apex_f, apex_m, n_o, wavelength_nm),
        "side_to_centre": ray_to_target(
            entry_side, tg["geometric_centre_mm"], n_o, wavelength_nm),
        "side_to_node_prior": ray_to_target(
            entry_side, tg["node_prior_mm"], n_o, wavelength_nm),
    }
    if eye_candidate_mm is not None:
        paths["side_to_eye_candidate"] = ray_to_target(
            entry_side, np.asarray(eye_candidate_mm, float), n_o,
            wavelength_nm)
    return {"wavelength_nm": wavelength_nm, "n_o": n_o,
            "entry_side_mm": entry_side, "targets": tg, "paths": paths}


# --- photoelastic & thermal projections (RSCS2-E.9) --------------------

def photoelastic_phase_shift_rad(strain_samples: np.ndarray,
                                 segment_lengths_mm: np.ndarray,
                                 refractive_index: float = QUARTZ_N_O,
                                 p_constant: float | None = None,
                                 wavelength_nm: float = 632.8) -> float:
    """Optical phase modulation of a probe from a strain field sampled
    along its path: dphi = (2 pi / lambda) * sum_i dn(S_i) * L_i with
    dn = -1/2 n^3 p S per segment (FROZEN photoelastic_index_shift).
    This is the projection RSCS2-D.5 uses: FE mode strain in ->
    predicted probe phase modulation out (H-20 sideband magnitude)."""
    p = QUARTZ_PHOTOELASTIC["p11"] if p_constant is None else p_constant
    s = np.asarray(strain_samples, dtype=float)
    ell = np.asarray(segment_lengths_mm, dtype=float)
    if s.shape != ell.shape:
        raise ValueError("strain and segment-length arrays must match")
    if not (np.all(np.isfinite(s)) and np.all(np.isfinite(ell))
            and np.all(ell >= 0)):
        raise ValueError("inputs must be finite; lengths >= 0")
    dn = np.array([photoelastic_index_shift(refractive_index, p, si)
                   for si in s])
    return float(2.0 * math.pi * np.sum(dn * ell * 1e-3)
                 / (wavelength_nm * 1e-9))


def absorption_deposition_w(power_in_w: float, alpha_per_m: float,
                            path_m: float) -> dict[str, float]:
    """Beer-Lambert absorbed-power PROXY: P_abs = P0 (1 - e^(-alpha L)).
    alpha is a declared input (measured or handbook); this bounds
    thermal deposition, it is NOT a heating/temperature claim."""
    for name, v in (("power_in_w", power_in_w),
                    ("alpha_per_m", alpha_per_m), ("path_m", path_m)):
        if not (math.isfinite(v) and v >= 0):
            raise ValueError(f"{name} must be finite and >= 0")
    p_abs = power_in_w * (1.0 - math.exp(-alpha_per_m * path_m))
    return {"absorbed_w": p_abs, "transmitted_w": power_in_w - p_abs,
            "note": "Beer-Lambert proxy; no temperature claim"}


# --- polarization elements (Jones matrices; states via frozen C.9) ----

def jones_waveplate(retardance_rad: float,
                    fast_axis_deg: float = 0.0) -> np.ndarray:
    """Jones matrix of a linear retarder (waveplate): retardance delta
    with the fast axis at the given angle from x. delta = pi/2 is a
    quarter-wave plate; pi a half-wave plate. Standard form."""
    th = math.radians(fast_axis_deg)
    c, s = math.cos(th), math.sin(th)
    rot = np.array([[c, s], [-s, c]])
    core = np.array([[1.0, 0.0],
                     [0.0, np.exp(1j * retardance_rad)]], dtype=complex)
    return rot.T @ core @ rot


def apply_jones(matrix: np.ndarray, ex: complex, ey: complex):
    """Apply a Jones element to a Jones vector; returns (ex', ey')."""
    v = np.asarray(matrix, dtype=complex) @ np.array([ex, ey],
                                                     dtype=complex)
    return complex(v[0]), complex(v[1])


# --- coil branch (RSCS2-E.10): quasi-static Biot-Savart ---------------

def circular_coil(radius_m: float, n_turns: int = 1, n_segments: int = 128,
                  center_m=(0.0, 0.0, 0.0), axis=(0.0, 0.0, 1.0),
                  handedness: int = +1) -> np.ndarray:
    """Closed polyline (N,3) approximating a circular coil of n_turns
    stacked at the same plane (filament model). handedness=+1 winds
    counterclockwise around +axis (right-handed); -1 reverses — the
    'counter-wound' option of the coil pair."""
    if handedness not in (+1, -1):
        raise ValueError("handedness must be +1 or -1")
    ax = np.asarray(axis, float)
    ax = ax / np.linalg.norm(ax)
    # orthonormal in-plane pair
    seed = np.array([1.0, 0.0, 0.0])
    if abs(np.dot(seed, ax)) > 0.9:
        seed = np.array([0.0, 1.0, 0.0])
    e1 = seed - np.dot(seed, ax) * ax
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(ax, e1)
    th = handedness * np.linspace(0.0, 2.0 * np.pi * n_turns,
                                  n_segments * n_turns + 1)
    pts = (np.asarray(center_m, float)[None, :]
           + radius_m * (np.cos(th)[:, None] * e1[None, :]
                         + np.sin(th)[:, None] * e2[None, :]))
    return pts


def biot_savart_polyline(vertices_m: np.ndarray, current_a: float,
                         points_m: np.ndarray) -> np.ndarray:
    """Magnetic field (T) of a current polyline at the given points.

    Exact per-segment closed form (Hanson & Hirshman 2002, numerically
    stable): B = (mu0 I / 4 pi) * (r1 x r2) * 2 (|r1|+|r2|) /
    (|r1||r2| ((|r1|+|r2|)^2 - L^2)). Magnetoquasistatic (valid far
    below coil self-resonance, which the frozen coil model checks)."""
    v = np.asarray(vertices_m, dtype=float)
    p = np.atleast_2d(np.asarray(points_m, dtype=float))
    a, b = v[:-1], v[1:]                        # (S,3) segment ends
    L2 = np.sum((b - a) ** 2, axis=1)           # (S,)
    r1 = p[:, None, :] - a[None, :, :]          # (M,S,3)
    r2 = p[:, None, :] - b[None, :, :]
    n1 = np.linalg.norm(r1, axis=2)
    n2 = np.linalg.norm(r2, axis=2)
    cross = np.cross(r1, r2)
    denom = n1 * n2 * ((n1 + n2) ** 2 - L2[None, :])
    with np.errstate(divide="ignore", invalid="ignore"):
        coef = 2.0 * (n1 + n2) / denom
    coef[~np.isfinite(coef)] = 0.0              # on-segment points
    B = _MU0 * current_a / (4.0 * np.pi) * np.sum(
        cross * coef[:, :, None], axis=1)
    return B


def loop_axis_field_t(radius_m: float, current_a: float,
                      z_m: float) -> float:
    """EXACT on-axis field of a single circular loop:
    B_z = mu0 I R^2 / (2 (R^2 + z^2)^(3/2)) — the closed-form test
    anchor for the Biot-Savart integrator."""
    return (_MU0 * current_a * radius_m ** 2
            / (2.0 * (radius_m ** 2 + z_m ** 2) ** 1.5))


def coil_pair_field(points_m: np.ndarray, radius_m: float,
                    separation_m: float, current_a: float,
                    phase_a_deg: float = 0.0, mode: str = "opposed",
                    counter_wound: bool = True,
                    n_segments: int = 128) -> dict[str, Any]:
    """Quasi-static phasor field of the opposed A/B coil pair, coaxial
    on +Z at z = +/- separation/2. Electrical phases come from the
    FROZEN coil_pair_phases; winding handedness is geometric
    (counter_wound=True gives B the opposite handedness). Returns the
    complex phasor field: B(t) = Re[B_phasor e^{i w t}]."""
    ph = coil_pair_phases(phase_a_deg, mode=mode)
    coil_a = circular_coil(radius_m, n_segments=n_segments,
                           center_m=(0, 0, -separation_m / 2.0),
                           handedness=+1)
    coil_b = circular_coil(radius_m, n_segments=n_segments,
                           center_m=(0, 0, +separation_m / 2.0),
                           handedness=-1 if counter_wound else +1)
    Ba = biot_savart_polyline(coil_a, current_a, points_m)
    Bb = biot_savart_polyline(coil_b, current_a, points_m)
    phasor = (Ba * np.exp(1j * math.radians(ph["coil_a_deg"]))
              + Bb * np.exp(1j * math.radians(ph["coil_b_deg"])))
    return {"phasor_t": phasor, "phases_deg": ph,
            "counter_wound": counter_wound}


def field_gradient(field_fn: Callable[[np.ndarray], np.ndarray],
                   points_m: np.ndarray, h_m: float = 1e-5) -> np.ndarray:
    """Central-difference gradient tensor dB_i/dx_j, shape (M, 3, 3)."""
    p = np.atleast_2d(np.asarray(points_m, dtype=float))
    out = np.zeros((p.shape[0], 3, 3))
    for j in range(3):
        dp = np.zeros(3)
        dp[j] = h_m
        out[:, :, j] = (field_fn(p + dp) - field_fn(p - dp)) / (2 * h_m)
    return out


def magnetic_energy_density_j_m3(b_field_t: np.ndarray) -> np.ndarray:
    """u = |B|^2 / (2 mu0) (J/m^3)."""
    b = np.atleast_2d(np.asarray(b_field_t, dtype=float))
    return np.sum(b * b, axis=1) / (2.0 * _MU0)


# --- drive projection (RSCS2-E.11) -------------------------------------

def assemble_body_force(problem, force_fn: Callable) -> np.ndarray:
    """Assemble the generalized force vector F_i = int b . v_i dV for a
    body-force density b(x) [N/m^3]; force_fn(x) takes the (3, ...)
    quadrature coordinates and returns the (3, ...) force density."""
    from skfem import LinearForm
    from skfem.helpers import dot as _dot

    @LinearForm
    def lf(v, w):
        return _dot(np.asarray(force_fn(w.x)), v)

    return lf.assemble(problem.basis)


def project_force_vector(sol: dict, force_vector: np.ndarray) -> np.ndarray:
    """Modal drive amplitudes f_n = phi_n^T F for the (mass-
    orthonormal) modes of a solve_modes result. This is projection onto
    modes, not an electromechanical field solve (spec section 2)."""
    return sol["modes"].T @ np.asarray(force_vector, dtype=float)


def capacitive_drive_traction_pa(voltage_v: float, gap_m: float,
                                 e_constant_c_m2: float = 0.171) -> float:
    """Electric/capacitive drive PROXY: uniform field E = V/gap between
    opposed electrode candidates converts to an equivalent piezoelectric
    surface traction t = e * E (default e11 of alpha-quartz,
    Bechmann 1958). A scalar magnitude proxy for drive budgeting; the
    full field solve lives in rscs2_core.piezo."""
    if not (math.isfinite(voltage_v) and math.isfinite(gap_m)
            and gap_m > 0):
        raise ValueError("voltage finite, gap positive")
    return e_constant_c_m2 * voltage_v / gap_m


def coil_coupling_report(mode_label: str, drive_amplitude: float,
                         leakage_baseline: dict | None) -> dict[str, Any]:
    """Structured coupling record. REQUIRES the leakage control: a
    'coil-only, no-specimen' baseline field at the sensor coordinate.
    No coupling is reported without its artifact channel (spec s.3)."""
    if leakage_baseline is None or "sensor_field_t" not in leakage_baseline:
        raise ValueError(
            "leakage control missing: supply the coil-only no-specimen "
            "baseline {'sensor_field_t': ..., 'sensor_point_m': ...} — "
            "no coupling may be reported without it")
    return {"mode": mode_label,
            "modal_drive_amplitude": float(drive_amplitude),
            "leakage_control": leakage_baseline,
            "claim_gate": "coupling must exceed the leakage baseline "
                          "channel to be reportable"}


# --- timing projections (frozen phase budget) ---------------------------

def macro_sequences(carrier_hz: float = 4096.0) -> dict[str, Any]:
    """Standard and half-spacing macro sequences over the source key
    set, with HONEST closure flags from the frozen exact_closure:
    the standard windows close exactly (golden rows: 1496 Hz/125 ms,
    644 Hz/250 ms, 587 Hz/1 s vs the 4096 Hz carrier); the half-spacing
    variants generally do NOT close and are flagged, never hidden."""
    kc = key_closures(carrier_hz)
    seq = []
    for key_hz, row in kc["keys"].items():
        w = row["closure_window_s"]
        for label, window in (("standard", w), ("half_spacing", w / 2.0)):
            chk = exact_closure([carrier_hz, key_hz], window)
            seq.append({
                "sequence": label, "key_hz": key_hz,
                "carrier_hz": carrier_hz, "window_s": window,
                "closes_exactly": chk["all_close"],
                "per_frequency": chk["per_frequency"],
            })
    return {"carrier_hz": carrier_hz, "steps": seq}


def drive_phase_table(frequencies_hz, **phase_kwargs) -> list[dict]:
    """Actual phase at the interaction coordinate for each drive
    frequency — one row per frequency from the FROZEN
    phase_at_coordinate (driver, cable, inductive, acoustic, optical,
    group delay terms all reported separately)."""
    return [{"frequency_hz": float(f),
             **phase_at_coordinate(f, **phase_kwargs)}
            for f in frequencies_hz]
