"""Coil sleeve and groove generator.

Spacing model (04_GEOMETRY_MATH/COIL_SPACING_MODEL):
    clear gap   = 2 * wire_d          (source rule: >= 2 diameters)
    groove pitch = 3 * wire_d          (wire + gap, center-to-center)
    nearest conductor standoff = clearance + wall - groove_depth
    coil center standoff       = nearest + wire_d / 2

Source wiring rules (SRC-PHYRLL-WIRE, recorded not validated): copper
clockwise, silver/non-ferrous counter-clockwise, crossed, never in
electrical contact; alternately pulsed at 4096 Hz through user limits.
"""
from __future__ import annotations

from dataclasses import dataclass

from rgcs_core.provenance import sha256_of_jsonable

from rgcs_desktop.services.phryll_v2.cone_generator import ConeDesign
from rgcs_desktop.services.phryll_v2.crystal_profile import CrystalProfile
from rgcs_desktop.services.phryll_v2.eye_alignment import (
    EyeAlignmentError, compute_eye_alignment, crossing_ladder,
    default_eye_tolerance_mm, solve_helix_phase_for_eye)
from rgcs_desktop.services.phryll_v2.schemas import validate

#: AWG -> bare-wire diameter (mm); AWG 28 is the source default
AWG_DIAMETER_MM = {24: 0.511, 26: 0.405, 28: 0.33, 30: 0.255, 32: 0.202}


class CoilSleeveError(ValueError):
    pass


@dataclass
class WireSpacing:
    wire_d_mm: float
    clear_gap_mm: float
    groove_pitch_mm: float

    def to_json(self) -> dict:
        return {"wire_d_mm": self.wire_d_mm,
                "clear_gap_mm": self.clear_gap_mm,
                "groove_pitch_mm": self.groove_pitch_mm}


@dataclass
class StandoffReport:
    nearest_conductor_standoff_mm: float
    coil_center_standoff_mm: float
    standoff_in_wire_diameters: float


def default_wire_spacing(wire_d_mm: float) -> WireSpacing:
    if wire_d_mm <= 0:
        raise CoilSleeveError("wire diameter must be > 0")
    return WireSpacing(wire_d_mm=wire_d_mm,
                       clear_gap_mm=2.0 * wire_d_mm,
                       groove_pitch_mm=3.0 * wire_d_mm)


def compute_coil_standoff(clearance_mm: float, wall_mm: float,
                          groove_depth_mm: float,
                          wire_d_mm: float) -> StandoffReport:
    if groove_depth_mm >= wall_mm:
        raise CoilSleeveError(
            f"groove depth {groove_depth_mm} mm does not fit inside "
            f"the {wall_mm} mm wall")
    nearest = clearance_mm + wall_mm - groove_depth_mm
    center = nearest + wire_d_mm / 2.0
    return StandoffReport(
        nearest_conductor_standoff_mm=nearest,
        coil_center_standoff_mm=center,
        standoff_in_wire_diameters=center / wire_d_mm)


def generate_crossed_coil_paths(profile: CrystalProfile,
                                cone: ConeDesign,
                                coil_settings: dict) -> dict:
    """Crossed copper/silver helix parameters phased onto the Eye.

    Returns the schema-valid coil_sleeve design dict, including per-coil
    handedness, pitch, helix phase, turns, groove band, and the crossing
    ladder with the Eye rung marked.
    """
    wire_d = coil_settings.get("wire_diameter_mm")
    if wire_d is None:
        gauge = coil_settings.get("wire_gauge", "AWG28")
        awg = int(str(gauge).upper().replace("AWG", "").strip())
        if awg not in AWG_DIAMETER_MM:
            raise CoilSleeveError(
                f"no diameter table entry for AWG {awg} (have: "
                f"{sorted(AWG_DIAMETER_MM)})")
        wire_d = AWG_DIAMETER_MM[awg]
    wire_d = float(wire_d)
    spacing = default_wire_spacing(wire_d)
    if "clear_gap_mm" in coil_settings:
        gap = float(coil_settings["clear_gap_mm"])
        if gap < 2.0 * wire_d - 1e-9:
            raise CoilSleeveError(
                f"clear gap {gap} mm violates the source rule of at "
                f"least twice the wire diameter ({2 * wire_d:.3f} mm)")
        spacing = WireSpacing(wire_d, gap, wire_d + gap)
    groove_depth = float(coil_settings.get("groove_depth_mm", 0.25))

    if profile.z_eye_mm is None:
        raise CoilSleeveError(
            "crystal profile has no Eye coordinate — the coil crossing "
            "plane aligns to the Eye, so enter/calculate/import it "
            "first")
    z_eye = float(profile.z_eye_mm)
    tolerance = default_eye_tolerance_mm(profile.eye_uncertainty_mm)

    # winding band: the middle of the cone, symmetric around the Eye,
    # limited by the cone ends with a one-pitch margin
    pitch = spacing.groove_pitch_mm
    margin = max(pitch, 2.0)
    band_top = min(profile.length_mm - margin,
                   z_eye + profile.length_mm * 0.25)
    band_bottom = max(margin, z_eye - profile.length_mm * 0.25)
    if band_bottom >= band_top:
        raise CoilSleeveError(
            f"no winding band fits around the Eye at {z_eye} mm on a "
            f"{profile.length_mm} mm crystal")
    turns = int((band_top - band_bottom) / pitch)
    if turns < 3:
        raise CoilSleeveError(
            f"winding band only fits {turns} turns; widen the band or "
            f"use finer wire")

    clearance = float(cone.fit["clearance_mm"])
    wall = float(cone.fit["wall_thickness_mm"])
    standoff = compute_coil_standoff(clearance, wall, groove_depth,
                                     wire_d)
    try:
        phase_cu = solve_helix_phase_for_eye(z_eye, pitch, "clockwise")
        phase_ag = solve_helix_phase_for_eye(z_eye, pitch,
                                             "counter_clockwise")
    except EyeAlignmentError as exc:
        raise CoilSleeveError(str(exc)) from exc
    # phased construction puts a crossing exactly on the Eye plane
    z_cross = z_eye
    alignment = compute_eye_alignment(z_eye, z_cross, tolerance)
    ladder = crossing_ladder(z_eye, pitch, profile.length_mm)

    design = {
        "schema_version": "2.0.0",
        "design_id": f"COIL-{cone.design_id}",
        "crystal_id": profile.crystal_id,
        "wire": {
            "wire_gauge": coil_settings.get("wire_gauge", "AWG28"),
            "wire_diameter_mm": wire_d,
            "copper_material": coil_settings.get(
                "copper_material", "enameled copper"),
            "silver_material": coil_settings.get(
                "silver_material",
                "silver or non-ferrous source-selected conductor"),
        },
        "spacing": {
            "clear_gap_mm": spacing.clear_gap_mm,
            "groove_pitch_mm": spacing.groove_pitch_mm,
            "groove_depth_mm": groove_depth,
            "coil_center_standoff_mm":
                standoff.coil_center_standoff_mm,
            "nearest_conductor_standoff_mm":
                standoff.nearest_conductor_standoff_mm,
        },
        "eye_alignment": alignment.to_json(),
        "paths": {
            "copper": {"handedness": "clockwise",
                       "pitch_mm": pitch,
                       "phase_rad_at_z0": phase_cu,
                       "turns": turns},
            "silver": {"handedness": "counter_clockwise",
                       "pitch_mm": pitch,
                       "phase_rad_at_z0": phase_ag,
                       "turns": turns},
            "band_bottom_mm": band_bottom,
            "band_top_mm": band_top,
            "crossing_ladder_mm": ladder,
            "no_electrical_contact": True,
        },
    }
    design["sha256"] = sha256_of_jsonable(
        {k: v for k, v in design.items() if k != "sha256"})
    errors = validate("coil_sleeve", design)
    if errors:
        raise CoilSleeveError("coil sleeve failed its own schema: "
                              + "; ".join(errors))
    return design


def align_coil_crossing_to_eye(paths: dict, z_eye_mm: float) -> dict:
    """Re-phase existing paths onto a (new) Eye coordinate."""
    out = dict(paths)
    pitch = float(out["copper"]["pitch_mm"])
    out["copper"] = {**out["copper"],
                     "phase_rad_at_z0":
                         solve_helix_phase_for_eye(z_eye_mm, pitch,
                                                   "clockwise")}
    out["silver"] = {**out["silver"],
                     "phase_rad_at_z0":
                         solve_helix_phase_for_eye(z_eye_mm, pitch,
                                                   "counter_clockwise")}
    return out
