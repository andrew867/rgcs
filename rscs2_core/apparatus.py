"""Apparatus, instrument, and ordinary-artifact models (Agent C07;
coverage A16, E008-E027 hardware side; gate G14).

Real calculations where established formulas exist (Wheeler coil
inductance, Biot-Savart cross-coupling of orthogonal coils via the
validated E.10 integrator); ENG records elsewhere. The ordinary-
artifact model exists so no pickup/thermal/crosstalk signal can be
misread as a crystal effect."""

from __future__ import annotations

import math

import numpy as np

from .research_records import make_record


def wheeler_inductance_h(n_turns: int, coil_radius_m: float,
                         coil_length_m: float) -> float:
    """Wheeler's formula for a single-layer solenoid (accuracy ~1%
    for length > 0.8 radius): L = (r^2 n^2)/(9r + 10l) with r, l in
    METERS via the inch-form conversion L[uH] = (r_in^2 n^2)/
    (9 r_in + 10 l_in)."""
    r_in = coil_radius_m / 0.0254
    l_in = coil_length_m / 0.0254
    l_uh = (r_in ** 2 * n_turns ** 2) / (9 * r_in + 10 * l_in)
    return l_uh * 1e-6


def crossed_coil_coupling(radius_m: float = 0.03,
                          n_segments: int = 256) -> dict:
    """E008: two identical coils with axes at 90 degrees. By symmetry
    the mutual flux vanishes; computed numerically with the validated
    Biot-Savart integrator as the on-axis field of coil A projected on
    coil B's axis at the shared center."""
    from .projections import biot_savart_polyline, circular_coil
    coil_a = circular_coil(radius_m, n_segments=n_segments)  # +z axis
    b = biot_savart_polyline(coil_a, 1.0,
                             np.array([[0.0, 0.0, 0.0]]))[0]
    # coil B axis = +x: coupling field component is b[0]
    return {"b_axial_of_a_t": float(b[2]),
            "b_along_b_axis_t": float(b[0]),
            "cross_coupling_ratio": float(abs(b[0])
                                          / max(abs(b[2]), 1e-300)),
            "note": "orthogonal-axis mutual coupling is numerically "
                    "~zero at the shared center (symmetry)"}


def apparatus_registry() -> dict:
    R = {}

    def add(rec):
        R[rec["record_id"]] = rec

    def app(rid, title, status, tags, **kw):
        add(make_record("ApparatusRecord", rid, title, "experimental",
                        status, tags, **kw))

    l40 = wheeler_inductance_h(40, 0.015, 40 * 0.00033)
    app("E008", "crossed copper/silver coils at 90 deg",
        "ENGINEERING_PROTOTYPE", ["ENG", "DER"],
        model=crossed_coil_coupling(),
        note="cross-coupling computed ~0 by symmetry; any measured "
             "coupling is a misalignment diagnostic")
    app("E009", "40-turn 0.33 mm wire modern coil",
        "ENGINEERING_PROTOTYPE", ["ENG", "DER"],
        wheeler_inductance_h=l40,
        geometry={"turns": 40, "wire_mm": 0.33,
                  "assumed_radius_mm": 15.0},
        note="single-layer Wheeler estimate; measure before use")
    app("E010", "seven-turn coil, one-litre vessel, 70F historical "
        "scaffold", "SOURCE_HYPOTHESIS", ["SRC", "ENG"],
        source_ids=["SRC-V4X-VOGEL"],
        wheeler_inductance_h=wheeler_inductance_h(7, 0.055, 0.05),
        note="historical geometry preserved as-published; "
             "reconstruction is an ENG scaffold, not an endorsement")
    app("E019", "fixed nonmetal jig", "ENGINEERING_PROTOTYPE",
        ["ENG"], spec="polymer/wood cradle at the 0.224L/0.776L "
        "free-free node stations (frozen fixture convention)")
    app("E004", "tuning forks vs voice-coil/piezo drive",
        "ENGINEERING_PROTOTYPE", ["ENG"],
        comparison="fork = fixed-frequency high-Q mechanical drive; "
                   "voice-coil/piezo = sweepable calibrated drive; "
                   "campaign E01 runs both with the same jig")
    app("E025", "collector-reference geometry from CAD source",
        "SOURCE_HYPOTHESIS", ["SRC"],
        source_ids=["SRC-V4X-VOGEL"],
        note="scad/ v2/v3 Vogel parametric models are the local CAD "
             "authority")
    # instrument channels E011-E017
    for rid, title in (("E011", "3-axis magnetometer"),
                       ("E012", "high-impedance E-field/electrometer"),
                       ("E013", "capacitance and impedance bridge"),
                       ("E014", "microphone + contact microphone"),
                       ("E015", "accelerometer"),
                       ("E016", "scanning laser vibrometer"),
                       ("E017", "current/voltage/field/temperature/"
                        "humidity/SPL environment block")):
        add(make_record("InstrumentRecord", rid, title,
                        "experimental", "ENGINEERING_PROTOTYPE",
                        ["ENG"],
                        calibration_policy="calibrated against a "
                        "reference before each campaign; calibration "
                        "record required for MEAS data"))
    return R


def ordinary_artifact_model(drive_current_a: float,
                            drive_freq_hz: float,
                            mutual_inductance_h: float,
                            temp_drift_c_per_h: float,
                            temp_coeff_hz_per_c: float) -> dict:
    """Gate G14: the ordinary-signal budget every claimed effect must
    exceed. EM pickup emf = -M dI/dt (peak M*I*w); thermal frequency
    drift = coeff * drift rate."""
    emf_peak_v = mutual_inductance_h * drive_current_a * \
        (2 * math.pi * drive_freq_hz)
    return {"em_pickup_peak_v": emf_peak_v,
            "thermal_drift_hz_per_h": temp_coeff_hz_per_c
            * temp_drift_c_per_h,
            "rule": "no residual claim until the measured signal "
                    "exceeds this ordinary budget with controls "
                    "(dummy coil, no-crystal, rotated crystal, "
                    "metal bracket) subtracted"}


# --- C07 digital twin: ordinary channels, quantified --------------------------
#
# The C07 boundary rule is that a residual may not be called exotic until
# the ordinary apparatus channels are bounded. These functions exist so
# the ordinary channels have NUMBERS rather than adjectives.

MU0 = 4e-7 * math.pi
RHO_CU_20C = 1.68e-8          # ohm*m
ALPHA_CU = 3.93e-3            # 1/K
RHO_AG_20C = 1.59e-8          # ohm*m


def wire_resistance_ohm(length_m: float, diameter_m: float,
                        temperature_c: float = 20.0,
                        material: str = "Cu") -> dict:
    """DC resistance with the linear temperature coefficient:
    R = rho(T) L / A, rho(T) = rho20 (1 + alpha (T - 20))."""
    rho20 = {"Cu": RHO_CU_20C, "Ag": RHO_AG_20C}[material]
    rho = rho20 * (1.0 + ALPHA_CU * (temperature_c - 20.0))
    area = math.pi * (diameter_m / 2.0) ** 2
    return {"resistance_ohm": rho * length_m / area,
            "resistivity_ohm_m": rho, "area_m2": area,
            "material": material, "temperature_c": temperature_c}


def skin_depth_m(f_hz: float, material: str = "Cu",
                 temperature_c: float = 20.0) -> float:
    """delta = sqrt(rho / (pi f mu0)). Below ~10 kHz in 0.33 mm wire
    the skin depth exceeds the wire radius, so the DC resistance is the
    right model — this function exists so that claim is checkable."""
    rho = wire_resistance_ohm(1.0, 1e-3, temperature_c,
                              material)["resistivity_ohm_m"]
    return math.sqrt(rho / (math.pi * f_hz * MU0))


def coil_model(n_turns: int, radius_m: float, length_m: float,
               wire_diameter_m: float, current_a: float,
               f_hz: float = 4096.0,
               temperature_c: float = 20.0,
               material: str = "Cu") -> dict:
    """Full ordinary-channel model of a drive coil: resistance,
    inductance, reactance, on-axis field, dissipated power, and skin
    depth. Every one of these is an artifact source that must be
    subtracted before a residual is discussed (G14/E03)."""
    wire_len = n_turns * 2.0 * math.pi * radius_m
    r = wire_resistance_ohm(wire_len, wire_diameter_m, temperature_c,
                            material)
    l_h = wheeler_inductance_h(n_turns, radius_m, length_m)
    x_l = 2.0 * math.pi * f_hz * l_h
    b_center = MU0 * n_turns * current_a / (2.0 * radius_m)
    p_w = current_a ** 2 * r["resistance_ohm"]
    delta = skin_depth_m(f_hz, material, temperature_c)
    return {"n_turns": n_turns, "wire_length_m": wire_len,
            "resistance_ohm": r["resistance_ohm"],
            "inductance_h": l_h,
            "reactance_ohm": x_l,
            "impedance_mag_ohm": math.hypot(r["resistance_ohm"], x_l),
            "b_center_t": b_center,
            "power_w": p_w,
            "skin_depth_m": delta,
            "skin_effect_negligible": delta > wire_diameter_m / 2.0,
            "note": "magnetoquasistatic filament model; b_center_t is "
                    "the ideal loop-stack formula, cross-checked "
                    "against the Biot-Savart integrator in tests"}


def coil_field_map(n_turns: int, radius_m: float, current_a: float,
                   points_m: np.ndarray,
                   n_segments: int = 256) -> np.ndarray:
    """3-axis B field at arbitrary points via the validated
    Biot-Savart integrator (E03 field-mapping predictions)."""
    from .projections import biot_savart_polyline, circular_coil
    coil = circular_coil(radius_m, n_segments=n_segments)
    return biot_savart_polyline(coil, current_a * n_turns,
                                np.atleast_2d(points_m))


def thermal_rise_c(power_w: float,
                   thermal_resistance_c_per_w: float = 25.0,
                   ambient_c: float = 20.0) -> dict:
    """Steady-state coil temperature: T = T_amb + P * R_th. A coil that
    heats the fixture moves every resonance through thermal expansion;
    that is an ordinary channel, and the interlock limit is declared."""
    rise = power_w * thermal_resistance_c_per_w
    t = ambient_c + rise
    return {"power_w": power_w, "temperature_rise_c": rise,
            "steady_state_c": t,
            "within_safe_limit": bool(t <= 60.0),
            "limit_c": 60.0,
            "note": "exceeding 60 C requires an interlock and is a "
                    "hardware-enable blocker (S01)"}


def electrode_capacitance_f(area_m2: float, gap_m: float,
                            eps_r: float = 4.5) -> dict:
    """Parallel-plate capacitance C = eps0 eps_r A / d, with the
    fringing caveat stated rather than hidden."""
    eps0 = 8.8541878128e-12
    c = eps0 * eps_r * area_m2 / gap_m
    return {"capacitance_f": c, "eps_r": eps_r,
            "fringing_underestimate": True,
            "note": "parallel-plate ideal; fringing makes the true "
                    "capacitance larger, so this is a lower bound"}


def contact_load_model(force_n: float, contact_radius_m: float,
                       modal_stiffness_n_per_m: float,
                       modal_mass_kg: float,
                       e_star_pa: float = 5e9) -> dict:
    """Hertzian contact stiffness k = 2 E* a, added in parallel with
    the modal stiffness; the frequency pulls as sqrt(1 + k_c/k_m).

    This is the E06 ordinary channel: a hand or a mount changes the
    frequency by ordinary mechanics, and that shift must be subtracted
    before any operator-state interpretation."""
    k_c = 2.0 * e_star_pa * contact_radius_m
    f0 = math.sqrt(modal_stiffness_n_per_m / modal_mass_kg) \
        / (2 * math.pi)
    f1 = math.sqrt((modal_stiffness_n_per_m + k_c) / modal_mass_kg) \
        / (2 * math.pi)
    return {"contact_stiffness_n_per_m": k_c,
            "unloaded_hz": f0, "loaded_hz": f1,
            "delta_f_hz": f1 - f0,
            "relative_shift": (f1 - f0) / f0,
            "force_n": force_n,
            "note": "ordinary mechanical loading; NOT an operator "
                    "effect (E06 boundary)"}


def transducer_transfer(f_hz, f_resonance_hz: float, q: float,
                        sensitivity: float = 1.0) -> np.ndarray:
    """Second-order transducer/instrument transfer function
    H(f) = S / (1 - (f/f0)^2 + j f/(f0 Q)). Every measured spectrum is
    the product of the specimen response and this; failing to divide it
    out manufactures peaks (E08)."""
    f = np.asarray(f_hz, float)
    r = f / f_resonance_hz
    return sensitivity / (1.0 - r ** 2 + 1j * r / q)


def cable_loading(capacitance_pf_per_m: float, length_m: float,
                  source_impedance_ohm: float) -> dict:
    """Cable capacitance forms a low-pass with the source impedance:
    f_3dB = 1/(2 pi R C). A rolled-off high-frequency channel looks
    like a missing resonance."""
    c = capacitance_pf_per_m * 1e-12 * length_m
    f3 = 1.0 / (2 * math.pi * source_impedance_ohm * c)
    return {"cable_capacitance_f": c, "f_3db_hz": f3,
            "note": "measurements above f_3dB are attenuated by the "
                    "cable, not by the specimen"}
