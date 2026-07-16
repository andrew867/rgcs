"""Agent 05: canonical 110 mm crystal geometry + deterministic meshing.

gmsh runs as a subprocess (DV4-006); these tests are skipped cleanly if
gmsh is unavailable so the CPU-only CI story stays honest.
"""
from __future__ import annotations

import numpy as np
import pytest

from rscs2_core import crystal110 as c110
from rscs2_core import fem

gmsh_available = True
try:
    import subprocess
    subprocess.run(c110._gmsh_cmd() + ["--version"], capture_output=True,
                   timeout=60, check=True)
except Exception:
    gmsh_available = False

needs_gmsh = pytest.mark.skipif(not gmsh_available,
                                reason="gmsh CLI not available")


def test_ideal_and_nominal_are_distinct():
    ideal = c110.build_crystal("ideal_n7")
    nominal = c110.build_crystal("nominal")
    assert ideal.length_mm == pytest.approx(770.263671875 / 7.0, abs=0)
    assert nominal.length_mm == 110.0
    assert ideal.length_mm != nominal.length_mm
    assert abs(ideal.length_mm - 110.0376674107143) < 1e-10
    # the two records can never be confused
    assert ideal.record()["variant"] == "ideal_n7"
    assert nominal.record()["variant"] == "nominal"
    # provenance arithmetic: L_ideal = (6310/(2*4096))/7 m
    assert ideal.length_mm == pytest.approx(
        6310.0 / (2 * 4096.0) / 7.0 * 1000.0, rel=1e-12)


def test_geometry_record_conventions():
    c = c110.build_crystal("ideal_n7")
    rec = c.record()
    assert rec["angle_mode"] == "face_slope"
    assert rec["diameter_mode"] == "across_vertices"
    assert rec["eye_coordinate"] is None          # never assumed
    assert "SP-Q154" in rec["diameter_policy"]
    # caps + shaft = total length
    assert (c.female_cap_height_mm + c.male_cap_height_mm
            + c.shaft_length_mm) == pytest.approx(c.length_mm, rel=1e-12)
    with pytest.raises(ValueError):
        c110.build_crystal("bogus")


def test_analytic_volume_positive_and_scales():
    c = c110.build_crystal("ideal_n7")
    v = c110.analytic_volume_mm3(c)
    assert v > 0
    # doubling both diameters at fixed L: cap volumes scale EXACTLY x8
    # (A ~ D^2, h ~ D); total volume strictly increases
    big = c110.build_crystal("ideal_n7",
                             wide_diameter_mm=2 * c.wide_diameter_mm,
                             narrow_diameter_mm=2 * c.narrow_diameter_mm)
    from rgcs_core.geometry.crystal import polygon_area_mm2
    cap_v = (polygon_area_mm2(c.wide_diameter_mm, 6)
             * c.female_cap_height_mm / 3.0)
    cap_v_big = (polygon_area_mm2(big.wide_diameter_mm, 6)
                 * big.female_cap_height_mm / 3.0)
    assert cap_v_big == pytest.approx(8.0 * cap_v, rel=1e-12)
    assert c110.analytic_volume_mm3(big) > v


@needs_gmsh
def test_mesh_volume_matches_analytic_and_quality():
    c = c110.build_crystal("ideal_n7")
    out = c110.mesh_crystal(c, clmax_mm=8.0,
                            workdir="evidence/v4/agent05/scratch")
    man = out["manifest"]
    assert man["quality"]["n_inverted"] == 0
    # planar-facet polyhedron: linear tets tile it exactly
    assert man["volume_rel_err"] < 1e-9
    assert man["quality"]["min_dihedral_deg"] > 8.0
    assert man["quality"]["max_aspect"] < 6.0


@needs_gmsh
def test_mesh_determinism_and_refinement():
    c = c110.build_crystal("nominal")
    a = c110.mesh_crystal(c, clmax_mm=9.0,
                          workdir="evidence/v4/agent05/scratch/det_a")
    b = c110.mesh_crystal(c, clmax_mm=9.0,
                          workdir="evidence/v4/agent05/scratch/det_b")
    # deterministic rebuild: identical counts and hashes
    assert a["manifest"]["n_tets"] == b["manifest"]["n_tets"]
    assert a["manifest"]["nodes_sha256"] == b["manifest"]["nodes_sha256"]
    assert a["manifest"]["tets_sha256"] == b["manifest"]["tets_sha256"]
    # refinement increases element count and keeps volume
    fine = c110.mesh_crystal(c, clmax_mm=5.0,
                             workdir="evidence/v4/agent05/scratch")
    assert fine["manifest"]["n_tets"] > 2 * a["manifest"]["n_tets"]
    assert fine["manifest"]["volume_rel_err"] < 1e-9


@needs_gmsh
def test_canonical_crystal_free_quartz_modes():
    """Flagship: free anisotropic quartz modes of the canonical crystal
    (C-axis along body Z). Six rigid modes; elastic modes converge
    between refinement levels; frequencies in a physically sane band."""
    from rgcs_core.anisotropy import (ALPHA_QUARTZ_DENSITY_KG_M3,
                                      alpha_quartz_stiffness_pa)
    from rscs_core.propagation import voigt_to_tensor
    from skfem import MeshTet
    c_full = voigt_to_tensor(alpha_quartz_stiffness_pa())
    freqs = {}
    for cl in (9.0, 6.0):
        out = c110.mesh_crystal(c110.build_crystal("ideal_n7"), cl,
                                workdir="evidence/v4/agent05/scratch")
        mesh = MeshTet(out["nodes_m"].T, out["tets"].T)
        prob = fem.assemble_anisotropic(mesh, c_full,
                                        ALPHA_QUARTZ_DENSITY_KG_M3)
        sol = fem.solve_modes(prob, 10)
        assert sol["n_rigid_modes"] == 6
        res = sol["residuals"][~np.isnan(sol["residuals"])]
        assert np.all(res < 1e-6)
        freqs[cl] = sol["elastic_frequencies_hz"][:4]
    # P2 refinement moves frequencies down, small relative change
    assert np.all(freqs[6.0] <= freqs[9.0] * 1.001)
    assert np.max(np.abs(freqs[6.0] - freqs[9.0]) / freqs[9.0]) < 0.05
    # sane band: tens of kHz for an 11 cm quartz body
    assert 5e3 < freqs[6.0][0] < 1e5
