"""R10.15A — anisotropic FEM profile for the Scale A body.

This module SPECIFIES and, where the toolchain is available, EXECUTES
the anisotropic eigenmode problem that must replace the scalar
half-wave proxy. It reuses the frozen quartz tensors and the verified
solvers in ``rscs2_core`` rather than duplicating them.

Mandatory typed inputs (requirement 5 of the Scale A authority). None
of these has a silent default: an unset value is UNRESOLVED and the
profile refuses to claim a solved eigenmode while any remains unset.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from r1015a import ScaleAError
from r1015a.design import ScaleAGeometry

MANDATORY_INPUTS = (
    "handedness", "c_axis_direction", "a_axis_azimuth_deg",
    "electrode_condition", "fixture", "temperature_c",
    "velocity_uncertainty_pct",
)
HANDEDNESS = ("left", "right")
ELECTRODE_CONDITIONS = ("open", "short", "finite_load", "no_electrode")
FIXTURES = ("free", "clamped", "declared_fixture")


@dataclass
class ScaleAFemProfile:
    """Typed inputs for the anisotropic solve."""
    geometry: ScaleAGeometry
    handedness: str | None = None
    c_axis_direction: str | None = None          # e.g. "+Z_body"
    a_axis_azimuth_deg: float | None = None
    electrode_condition: str | None = None
    fixture: str | None = None
    temperature_c: float | None = None
    velocity_uncertainty_pct: float | None = None
    finite_load_ohm: float | None = None
    fixture_contacts: tuple = ()
    fixture_preload_n: float | None = None
    mesh_clmax_mm: float = 12.0
    n_modes: int = 12

    def unresolved(self) -> list:
        out = [k for k in MANDATORY_INPUTS
               if getattr(self, k) is None]
        if self.electrode_condition == "finite_load" and \
                self.finite_load_ohm is None:
            out.append("finite_load_ohm")
        if self.fixture == "declared_fixture" and not self.fixture_contacts:
            out.append("fixture_contacts")
        return out

    def validate(self) -> dict:
        errors = []
        if self.handedness is not None and \
                self.handedness not in HANDEDNESS:
            errors.append(f"handedness must be one of {HANDEDNESS}")
        if self.electrode_condition is not None and \
                self.electrode_condition not in ELECTRODE_CONDITIONS:
            errors.append("electrode_condition must be one of "
                          f"{ELECTRODE_CONDITIONS}")
        if self.fixture is not None and self.fixture not in FIXTURES:
            errors.append(f"fixture must be one of {FIXTURES}")
        if self.a_axis_azimuth_deg is not None and \
                not (0.0 <= self.a_axis_azimuth_deg < 360.0):
            errors.append("a_axis_azimuth_deg must lie in [0, 360)")
        if self.velocity_uncertainty_pct is not None and \
                self.velocity_uncertainty_pct < 0:
            errors.append("velocity_uncertainty_pct must be >= 0")
        return {"ok": not errors, "errors": errors,
                "unresolved": self.unresolved()}

    def record(self) -> dict:
        v = self.validate()
        return {
            "schema": "rgcs.r1015a.fem-profile.v1",
            "geometry": self.geometry.record(),
            "handedness": self.handedness,
            "c_axis_direction": self.c_axis_direction,
            "a_axis_azimuth_deg": self.a_axis_azimuth_deg,
            "electrode_condition": self.electrode_condition,
            "finite_load_ohm": self.finite_load_ohm,
            "fixture": self.fixture,
            "fixture_contacts": list(self.fixture_contacts),
            "fixture_preload_n": self.fixture_preload_n,
            "temperature_c": self.temperature_c,
            "velocity_uncertainty_pct": self.velocity_uncertainty_pct,
            "mesh_clmax_mm": self.mesh_clmax_mm,
            "n_modes": self.n_modes,
            "valid": v["ok"], "errors": v["errors"],
            "unresolved_inputs": v["unresolved"],
            "solvable": v["ok"] and not v["unresolved"],
        }


def assert_solvable(profile: ScaleAFemProfile) -> None:
    v = profile.validate()
    if v["errors"]:
        raise ScaleAError("; ".join(v["errors"]))
    if v["unresolved"]:
        raise ScaleAError(
            f"refused: the anisotropic eigenmode solve needs "
            f"{v['unresolved']}, which are unresolved. Every one of "
            "them changes the answer, so solving without them would "
            "produce a number with no defensible meaning. Supply them "
            "or keep using the labelled half-wave proxy.")


def solve_eigenmodes(profile: ScaleAFemProfile, workdir) -> dict:
    """Execute the anisotropic solve. Requires gmsh + scikit-fem.

    Uses the R10.13 specimen bridge so the frozen alpha-quartz tensors
    and the verified FEM path are reused rather than reimplemented.
    """
    assert_solvable(profile)
    geo = profile.geometry
    rec = {
        "schema_version": "rgcs.crystal-specimen/1.0",
        "specimen_id": "scale-a-4096",
        "name": "Scale A 4096 Hz shear candidate",
        "material": {"material_id": "alpha_quartz",
                     "density_g_cm3": 2.65,
                     "handedness": profile.handedness},
        "geometry": {
            "length_mm": geo.length_mm,
            "wide_diameter_mm": geo.wide_diameter_mm,
            "narrow_diameter_mm": geo.narrow_diameter_mm,
            "facets": geo.facets,
            "female_angle_deg": geo.rx_face_slope_deg,
            "male_angle_deg": geo.tx_face_slope_deg,
            "diameter_mode": ("across_vertices"
                              if geo.diameter_mode == "across_vertices"
                              else "across_flats"),
            "angle_mode": "face_slope"},
        "orientation": {
            "status": "known",
            "c_axis_body_axis": profile.c_axis_direction,
            "euler_zxz_deg": [profile.a_axis_azimuth_deg, 0.0, 0.0]},
        "measurements": {"temperature_c": profile.temperature_c},
    }
    from r1013.fem_api import elastic_modes, mesh_specimen, piezo_modes
    from r1013.fixtures import make_fixture
    mesh = mesh_specimen(rec, profile.mesh_clmax_mm, workdir)
    fix = make_fixture("free" if profile.fixture == "free"
                       else "end_clamp" if profile.fixture == "clamped"
                       else "three_point")
    elastic = elastic_modes(rec, mesh, profile.n_modes, fix)
    out = {"schema": "rgcs.r1015a.eigenmodes.v1",
           "profile": profile.record(),
           "elastic_frequencies_hz": elastic["frequencies_hz"],
           "n_rigid_modes": elastic["n_rigid_modes"],
           "fixture_applied": elastic["fixture_applied"],
           "evidence_class": "NUMERICAL_SIMULATION",
           "converged": False,
           "convergence_note": "single mesh level; a convergence "
                               "ladder is required before any "
                               "frequency here is quoted"}
    if profile.electrode_condition in ("open", "short"):
        pz = piezo_modes(rec, mesh, min(profile.n_modes, 8),
                         profile.electrode_condition)
        out["piezo_frequencies_hz"] = pz["frequencies_hz"]
        out["electrode_condition"] = profile.electrode_condition
    return out


def velocity_sweep(branch: str = "shear_proxy",
                   frequency_hz: float = 4096.0,
                   uncertainty_pct: float = 5.0,
                   points: int = 9) -> dict:
    """How the half-wave path moves with velocity uncertainty.

    The path is exactly linear in velocity, so a +-x% velocity
    uncertainty is a +-x% length uncertainty. At 5 percent that is
    +-23 mm on this body, which dwarfs every machining tolerance and
    is the single largest source of length uncertainty today.
    """
    from r1015a.design import BRANCHES, half_wave_path
    if branch not in BRANCHES:
        raise ScaleAError(f"unknown branch {branch!r}")
    if uncertainty_pct < 0:
        raise ScaleAError("uncertainty_pct must be >= 0")
    v0 = BRANCHES[branch]["velocity_m_s"]
    rows = []
    for i in range(points):
        frac = -1.0 + 2.0 * i / (points - 1) if points > 1 else 0.0
        v = v0 * (1.0 + frac * uncertainty_pct / 100.0)
        L = float(half_wave_path(v, frequency_hz)) * 1000.0
        rows.append({"velocity_m_s": v, "delta_pct": frac * uncertainty_pct,
                     "length_mm": L})
    lengths = [r["length_mm"] for r in rows]
    nominal = float(half_wave_path(v0, frequency_hz)) * 1000.0
    return {"schema": "rgcs.r1015a.velocity-sweep.v1",
            "branch": branch, "nominal_velocity_m_s": v0,
            "nominal_length_mm": nominal,
            "uncertainty_pct": uncertainty_pct,
            "rows": rows,
            "length_span_mm": max(lengths) - min(lengths),
            "length_span_pct": 100.0 * (max(lengths) - min(lengths))
            / nominal,
            "relationship": "exactly linear: L scales with v",
            "dominant_uncertainty": (
                "velocity uncertainty dominates: a "
                f"{uncertainty_pct} percent velocity band gives a "
                f"{max(lengths) - min(lengths):.1f} mm length band, "
                "far larger than machining tolerance"),
            "evidence_class": "DERIVED"}


def branch_comparison(frequency_hz: float = 4096.0) -> dict:
    """Shear candidate against the longitudinal CONTROL branch."""
    from r1015a.design import BRANCHES, half_wave_proxy
    rows = []
    for name in BRANCHES:
        p = half_wave_proxy(name, frequency_hz)
        rows.append({"branch": name, "role": BRANCHES[name]["role"],
                     "velocity_m_s": p["velocity_m_s"],
                     "length_mm": p["length_mm"]})
    return {"schema": "rgcs.r1015a.branch-comparison.v1",
            "rows": rows,
            "primary": "shear_proxy",
            "control": "longitudinal_proxy",
            "rule": "the longitudinal branch is a CONTROL, not a "
                    "second preferred answer; it exists so that a "
                    "result which appears for both branches can be "
                    "recognised as branch-independent and therefore "
                    "not evidence for either",
            "evidence_class": "DERIVED"}
