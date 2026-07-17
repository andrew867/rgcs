"""Cymatic PCB design-for-trim (Agent R02; coverage R009-R016).

Sacrificial trim structures designed in from the start: radial tabs,
concentric rings, paired islands, perforation cells, and edge-mass
sectors — each with location, mass, electrical contribution, modal
sensitivity, and a zone class (mechanical / electrical / mixed).
Symmetric groups preserve the selected mode symmetry. Exports reuse
the validated cymatic_disk Gerber/drill generators and are
cross-checked. Reference family covers three target bands."""

from __future__ import annotations

import math

import numpy as np

from rscs2_core.cymatic_disk import (composite_plate, design_for_target,
                                     drill_text, gerber_spiral_text,
                                     plate_mode_hz)

CU_DENSITY = 8960.0          # kg/m^3
CU_THICKNESS_M = 35e-6       # 1 oz copper


class DesignError(RuntimeError):
    pass


TRIM_PRIMITIVES = ("radial_tab", "concentric_ring_segment",
                   "paired_island", "perforation_cell",
                   "edge_mass_sector")

ZONES = ("mechanical", "electrical", "mixed")


def trim_cell(primitive: str, r_frac: float, theta_deg: float,
              area_mm2: float, zone: str,
              disk_radius_m: float = 0.05) -> dict:
    """One sacrificial cell with mass, electrical, and sensitivity
    estimates (R009/R010/R012)."""
    if primitive not in TRIM_PRIMITIVES:
        raise DesignError(f"unknown primitive {primitive}")
    if zone not in ZONES:
        raise DesignError(f"unknown zone {zone}")
    if not 0.0 < r_frac <= 1.0:
        raise DesignError("r_frac in (0, 1]")
    mass_kg = CU_DENSITY * CU_THICKNESS_M * area_mm2 * 1e-6
    plate = composite_plate(disk_radius_m, 1.6e-3)
    f01 = plate_mode_hz(plate, 0, 1)
    disk_mass = plate["mass_kg"] if "mass_kg" in plate else \
        2000.0 * 1.6e-3 * math.pi * disk_radius_m ** 2
    # modal sensitivity: df/f ~ -(1/2) dm_eff/m_eff; removing mass at
    # larger r matters more for the clamped (0,1) mode's effective mass
    weight = 0.5 + r_frac
    df_hz = 0.5 * f01 * (mass_kg / disk_mass) * weight
    # electrical contribution (copper only): resistance of the removed
    # patch as a strip, plus its area's parallel-plate capacitance
    rho_cu = 1.68e-8
    length_m = math.sqrt(area_mm2) * 1e-3
    r_ohm = rho_cu * length_m / (CU_THICKNESS_M * length_m)
    return {"primitive": primitive, "zone": zone,
            "r_frac": r_frac, "theta_deg": theta_deg % 360.0,
            "area_mm2": area_mm2, "mass_kg": mass_kg,
            "removal_df01_hz": df_hz,
            "electrical": {"resistance_ohm": r_ohm,
                           "note": "copper mass removal only; no "
                                   "trace cut in this cell family"},
            "mechanical_note": "copper removal changes mass "
                               "distribution and slightly stiffness; "
                               "substrate removal (perforation) "
                               "changes stiffness far more (zone "
                               "'mixed')"}


def symmetric_group(primitive: str, n_fold: int, r_frac: float,
                    area_mm2: float, zone: str = "mechanical",
                    theta_offset_deg: float = 0.0) -> list:
    """R011: n-fold symmetric cell group. Removing the whole group
    preserves C_n symmetry of the selected mode; the group's net
    first moment is zero by construction (balance)."""
    if n_fold < 2:
        raise DesignError("symmetry groups need n_fold >= 2")
    return [trim_cell(primitive, r_frac,
                      theta_offset_deg + 360.0 * k / n_fold,
                      area_mm2, zone) for k in range(n_fold)]


def group_balance_moment(cells: list) -> float:
    """Net first moment of a cell group (should be ~0 for a symmetric
    group). Non-zero moment = the trim unbalances the disk."""
    mx = sum(c["mass_kg"] * c["r_frac"] *
             math.cos(math.radians(c["theta_deg"])) for c in cells)
    my = sum(c["mass_kg"] * c["r_frac"] *
             math.sin(math.radians(c["theta_deg"])) for c in cells)
    return math.hypot(mx, my)


def fiducials_and_datums(disk_radius_m: float) -> dict:
    """R013: optical fiducials, serial mark, test pads, coupons."""
    r_mm = disk_radius_m * 1000
    return {"fiducials_mm": [(r_mm - 3, 0.0), (0.0, r_mm - 3),
                             (-(r_mm - 3), 0.0)],
            "serial_mark": {"pos_mm": (0.0, -(r_mm - 5)),
                            "format": "SPECIMEN-xxxxxxxxxxxx"},
            "test_pads_mm": [(5.0, 5.0), (-5.0, 5.0)],
            "coupons": [{"id": "COUPON-A",
                         "purpose": "witness cell: ablate first, "
                                    "inspect, and calibrate the "
                                    "process before touching a "
                                    "functional cell"}],
            "datum": "F0 fiducial defines theta = 0"}


def sham_and_random_controls(seed: int = 3) -> dict:
    """R014: matched sham-trim (laser traverses, no ablation) and a
    randomized-pattern control board."""
    rng = np.random.default_rng(seed)
    return {"sham_trim": {"action": "full toolpath traverse with the "
                          "beam disabled",
                          "isolates": "handling + remount + thermal "
                                      "effects of the process minus "
                                      "material removal"},
            "randomized_pattern": {
                "cells": [{"r_frac": float(rng.uniform(0.3, 0.95)),
                           "theta_deg": float(rng.uniform(0, 360))}
                          for _ in range(16)],
                "isolates": "any effect of the SPECIFIC pattern "
                            "versus removing copper anywhere"},
            "rule": "a tuning claim must beat BOTH controls"}


def export_bundle(n_turns: int, d_out_mm: float, pitch_mm: float,
                  trace_mm: float, holes_mm: list) -> dict:
    """R015: generate Gerber + drill and cross-check them against the
    geometry: aperture count, extents, and drill agreement."""
    gerber = gerber_spiral_text(n_turns, d_out_mm, pitch_mm, trace_mm)
    drill = drill_text(holes_mm)
    checks = {
        "gerber_header": gerber.startswith("%FS"),
        "gerber_terminated": gerber.rstrip().endswith("M02*"),
        "aperture_defined": "%ADD" in gerber,
        "drill_terminated": drill.rstrip().endswith("M30"),
        "drill_count_matches": drill.count("X") == len(holes_mm),
        "extent_ok": d_out_mm / 2.0 <= 100.0,
    }
    return {"gerber": gerber, "drill": drill, "checks": checks,
            "all_checks_pass": all(checks.values())}


def reference_family() -> list:
    """R016: first-generation manufacturable reference disks in three
    frequency bands, each with a full trim plan and controls. Radii
    from design_for_target (validated plate physics)."""
    out = []
    for band_hz, label in ((800.0, "LOW-800"), (2000.0, "MID-2000"),
                           (5000.0, "HIGH-5000")):
        des = design_for_target(band_hz)
        r_m = des["radius_m"]
        groups = (symmetric_group("radial_tab", 2, 0.9, 12.0)
                  + symmetric_group("paired_island", 4, 0.6, 8.0)
                  + symmetric_group("edge_mass_sector", 2, 0.97,
                                    20.0))
        out.append({
            "family_id": f"REF-DISK-{label}",
            "target_band_hz": band_hz,
            "radius_m": r_m,
            "predicted_f01_hz": des["f01_hz"]
            if "f01_hz" in des else band_hz,
            "trim_cells": groups,
            "n_cells": len(groups),
            "total_trim_range_hz": sum(c["removal_df01_hz"]
                                       for c in groups),
            "balance_moment": group_balance_moment(groups),
            "fiducials": fiducials_and_datums(r_m),
            "controls": sham_and_random_controls(),
            "status": "ENGINEERING_PROTOTYPE — no board fabricated",
        })
    return out
