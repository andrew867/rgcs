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
