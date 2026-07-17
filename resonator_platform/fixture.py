"""Measurement jig and fixture (Agent R03; coverage R017-R024).

The fixture is part of the instrument: a poor mount shifts the
spectrum more than an intended trim step, so boundary condition,
preload, contact, orientation, and environment are all recorded state,
and remount repeatability is a measured number, not an assumption."""

from __future__ import annotations

import math

import numpy as np

FIXTURE_KINDS = {
    # kind: (bc stiffness factor, typical remount scatter Hz,
    #        dominant risk)
    "center_clamp": (1.10, 0.6, "clamp torque changes f01 directly"),
    "three_point": (1.02, 0.3, "support position tolerance"),
    "edge_clamp": (1.35, 1.2, "highest bc sensitivity of the set"),
    "nodal_suspension": (1.005, 0.15,
                         "node moves when the mode changes"),
    "free_edge_suspension": (1.0, 0.1,
                             "lowest coupling; weakest drive"),
}


class FixtureError(RuntimeError):
    pass


def fixture_record(kind: str, preload_n: float,
                   contact_material: str, orientation_deg: float,
                   temperature_c: float, humidity_pct: float,
                   sensor_positions: list) -> dict:
    """R019/R020/R021: full fixture state as a typed record."""
    if kind not in FIXTURE_KINDS:
        raise FixtureError(f"unknown fixture kind {kind}")
    if preload_n < 0:
        raise FixtureError("preload must be >= 0")
    stiff, scatter, risk = FIXTURE_KINDS[kind]
    return {"kind": kind, "bc_stiffness_factor": stiff,
            "expected_remount_scatter_hz": scatter,
            "dominant_risk": risk,
            "preload_n": preload_n,
            "contact_material": contact_material,
            "orientation_deg": orientation_deg % 360.0,
            "temperature_c": temperature_c,
            "humidity_pct": humidity_pct,
            "sensor_positions": list(sensor_positions),
            "datum": "board fiducial F0 at theta=0, r=R",
            "synthetic": True}


def coupling_model(kind: str, preload_n: float,
                   f0_hz: float) -> dict:
    """R018: reduced-order fixture coupling — the boundary stiffness
    factor scales the effective stiffness, pulling the frequency as
    sqrt(k_eff); preload adds a small contact-stiffness term
    (Hertzian, saturating)."""
    stiff, scatter, _ = FIXTURE_KINDS[kind]
    contact = 1.0 + 0.004 * math.tanh(preload_n / 10.0)
    f = f0_hz * math.sqrt(stiff * contact)
    return {"kind": kind, "f_free_hz": f0_hz, "f_mounted_hz": f,
            "fixture_shift_hz": f - f0_hz,
            "expected_remount_scatter_hz": scatter,
            "note": "the fixture shift (here "
                    f"{f - f0_hz:.1f} Hz) can exceed a trim step; "
                    "it must be subtracted before any trim decision"}


def remount_repeatability(twin, kind: str, n_remounts: int = 8
                          ) -> dict:
    """R023: repeated remount protocol on the twin. Returns the
    scatter actually realized, which is the number that goes in the
    uncertainty budget — not the catalogue value."""
    stiff, _, _ = FIXTURE_KINDS[kind]
    f01 = []
    for _ in range(n_remounts):
        twin.mount(fixture_stiffness_factor=stiff)
        f01.append(twin.mode_hz(0, 1))
    arr = np.asarray(f01)
    return {"kind": kind, "n_remounts": n_remounts,
            "mean_hz": float(arr.mean()),
            "scatter_std_hz": float(arr.std(ddof=1)),
            "spread_hz": float(arr.max() - arr.min()),
            "synthetic": True,
            "rule": "a trim step smaller than the remount scatter "
                    "is unmeasurable and must not be attempted"}


def crosstalk_controls() -> list:
    """R022: actuator isolation and cross-talk control set."""
    return [
        {"id": "no-specimen drive", "isolates": "fixture + actuator "
         "self-response"},
        {"id": "actuator on, decoupled", "isolates": "airborne and "
         "structure-borne leakage"},
        {"id": "sensor swap", "isolates": "channel-specific "
         "artifacts"},
        {"id": "cable re-route", "isolates": "ground loops"},
        {"id": "sham remount", "isolates": "remount scatter without "
         "trim (R023)"},
    ]


def fabrication_package(kind: str) -> dict:
    """R024: drawing/BOM stubs for the two priority fixtures. These
    are ENGINEERING_PROTOTYPE documents; nothing has been machined."""
    if kind not in ("three_point", "nodal_suspension"):
        raise FixtureError("fabrication package exists for the two "
                           "priority fixtures only")
    return {"kind": kind,
            "drawing": f"docs/v4/resonator/fixture_{kind}.md",
            "bom": [
                {"item": "aluminium base plate 200x200x10", "qty": 1},
                {"item": "delrin contact tips", "qty": 3},
                {"item": "M6 preload screw + calibrated spring",
                 "qty": 3 if kind == "three_point" else 4},
                {"item": "digital torque driver 0.05 Nm", "qty": 1},
                {"item": "thermocouple + RH sensor", "qty": 1},
            ],
            "assembly_verification": [
                "flatness of base within 0.05 mm",
                "support positions within 0.1 mm of drawing",
                "preload calibration against a force gauge",
                "remount repeatability protocol (>=8 remounts) "
                "before first use"],
            "status": "ENGINEERING_PROTOTYPE — not fabricated"}
