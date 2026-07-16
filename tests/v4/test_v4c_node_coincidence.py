"""V4C-D-001 regression battery: the uncertainty-aware node-
coincidence rule. A proximity threshold may never absorb a resolved
separation; coincidence is numerical exactness or interval overlap."""
from __future__ import annotations

import numpy as np
import pytest

from rscs2_core import eye, fem
from rscs2_core.eye import (NUMERICAL_COINCIDENCE_TOL_MM,
                            node_coincidence_comparison)


def _cmp(sep, cand_hw, comp_hw):
    return node_coincidence_comparison(
        np.array([0.0, 0.0, 0.0]),
        np.array([[0.0, 0.0, sep]]),
        cand_hw, comp_hw, mesh_resolution_mm=comp_hw,
        convergence_shift_mm=None, cloud_rms_mm=None)


# --- classifier unit cases (user-mandated) -------------------------------

def test_394mm_separation_is_never_coincident():
    """The defining case: 3.94 mm with sub-mm localization is DISTINCT
    and the exact separation is preserved."""
    out = _cmp(3.94, 0.5, 0.5)
    assert out["classification"] in (
        "NEAR_CONVENTIONAL_NODE_BUT_DISTINCT",
        "DISTINCT_FROM_CONVENTIONAL_NODE")
    assert out["classification"] != \
        "EXACT_CONVENTIONAL_NODE_COINCIDENCE"
    assert out["separation_mm"] == pytest.approx(3.94, rel=1e-12)
    # a 4 mm proximity radius must not exist anywhere in the rule
    assert "proximity threshold" in out["rule"]


def test_01mm_distinct_unless_uncertainty_overlaps():
    tight = _cmp(0.1, 0.02, 0.02)
    assert tight["classification"] == \
        "NEAR_CONVENTIONAL_NODE_BUT_DISTINCT"
    assert tight["separation_mm"] == pytest.approx(0.1)
    loose = _cmp(0.1, 0.08, 0.05)
    assert loose["classification"] == \
        "UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE"
    # overlap is a statement about intervals, not a reclassification
    # of the coordinate: separation still reported exactly
    assert loose["separation_mm"] == pytest.approx(0.1)


def test_exact_synthetic_coincidence_passes():
    assert _cmp(0.0, 0.5, 0.5)["classification"] == \
        "EXACT_CONVENTIONAL_NODE_COINCIDENCE"
    assert _cmp(1e-9, 0.5, 0.5)["classification"] == \
        "EXACT_CONVENTIONAL_NODE_COINCIDENCE"
    # just above the numerical tolerance with ZERO uncertainty is
    # distinct — exactness is numerical, not physical
    out = _cmp(1e-3, 0.0, 0.0)
    assert out["classification"] != \
        "EXACT_CONVENTIONAL_NODE_COINCIDENCE"
    assert NUMERICAL_COINCIDENCE_TOL_MM <= 1e-5


def test_full_evidence_always_reported():
    out = node_coincidence_comparison(
        np.array([1.0, 2.0, 3.0]), np.array([[1.0, 2.0, 6.94]]),
        0.7, 0.3, mesh_resolution_mm=0.3, convergence_shift_mm=0.6,
        cloud_rms_mm=0.35)
    for key in ("candidate_mm", "nearest_comparator_mm",
                "separation_mm", "candidate_halfwidth_mm",
                "comparator_halfwidth_mm", "mesh_resolution_mm",
                "convergence_shift_mm", "cloud_rms_mm",
                "numerical_tol_mm", "classification", "rule"):
        assert key in out, key
    assert out["separation_mm"] == pytest.approx(3.94)


# --- integration through the engine ---------------------------------------

def _grid(spacing_mm):
    ax = np.arange(1.0, 19.0 + 1e-9, spacing_mm)
    az = np.arange(1.0, 99.0 + 1e-9, spacing_mm * 2)
    x, y, z = np.meshgrid(ax, ax, az, indexing="ij")
    return np.stack([x.ravel(), y.ravel(), z.ravel()], axis=1)


def _fieldset(center, pts, dids=("D2", "D6", "D11", "D8"),
              width=3.0):
    out = []
    for d in dids:
        v = np.exp(-np.sum((pts - np.asarray(center)) ** 2, axis=1)
                   / (2 * width ** 2))
        out.append(eye.DiagnosticField(d, pts, v / v.max(),
                                       float(v.max()), "synthetic",
                                       (0, 1)))
    return out


GEOM = {
    "length_mm": 100.0,
    "inside_fn": lambda p: ((p[:, 0] >= 0) & (p[:, 0] <= 20)
                            & (p[:, 1] >= 0) & (p[:, 1] <= 20)
                            & (p[:, 2] >= 0) & (p[:, 2] <= 100)),
    "geometric_centre_mm": np.array([10.0, 10.0, 50.0]),
    "shaft_midpoint_mm": np.array([10.0, 10.0, 50.0]),
    "node_prior_mm": np.array([10.0, 10.0, 51.6]),
    # the conventional station sits EXACTLY 3.94 mm from the blob
    "conventional_features_mm": np.array([[10.0, 10.0, 43.94]]),
}
C0 = np.array([10.0, 10.0, 40.0])


def test_engine_fine_mesh_394mm_is_distinct_with_exact_separation():
    pts = _grid(1.0)                        # ~1 mm resolution
    flds = _fieldset(C0, pts, width=2.0)
    res = eye.eye_consensus(
        flds, GEOM, refined_fields=_fieldset(C0, pts, width=2.0),
        uncertainty_fields=[_fieldset(C0 + d, pts, width=2.0)
                            for d in ([0.2, 0, 0], [0, 0.2, 0],
                                      [0, 0, 0.2])],
        link_radius_mm=4.0)
    assert res.status == "DISTINCT_STABLE_CANDIDATE"
    nc = res.candidates[0].node_comparison
    assert nc["separation_mm"] == pytest.approx(3.94, abs=0.15)
    assert nc["classification"] in (
        "NEAR_CONVENTIONAL_NODE_BUT_DISTINCT",
        "DISTINCT_FROM_CONVENTIONAL_NODE")
    # the raw coordinate is preserved, not moved onto the node
    assert res.candidates[0].centroid_mm[2] == pytest.approx(40.0,
                                                             abs=0.15)


def test_engine_coarse_mesh_gives_overlap_not_forced_conventional():
    """Coarse-mesh localization uncertainty must produce the
    indeterminate/overlap class — never a forced conventional
    verdict, and never EXACT."""
    pts = _grid(4.0)                        # coarse: ~4 mm resolution
    flds = _fieldset(C0, pts, width=5.0)
    res = eye.eye_consensus(
        flds, GEOM, refined_fields=_fieldset(C0, pts, width=5.0),
        link_radius_mm=8.0)
    assert res.status == "UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE"
    nc = res.candidates[0].node_comparison
    assert nc["classification"] == \
        "UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE"
    assert nc["classification"] != \
        "EXACT_CONVENTIONAL_NODE_COINCIDENCE"
    # exact separation still reported
    assert nc["separation_mm"] > 1.0


def test_frequency_sensitivity_real_solve():
    mesh = fem.box_mesh((0.08, 0.01, 0.01), (10, 2, 2))
    prob = fem.assemble_isotropic(mesh, 210e9, 0.3, 7850.0)
    fixed = prob.basis.get_dofs(
        lambda x: np.isclose(x[0], 0.0)).flatten()
    sol = fem.solve_modes(prob, 4, fixed_dofs=fixed)
    tip = eye.frequency_sensitivity(prob, sol,
                                    np.array([80.0, 5.0, 5.0]), 6.0)
    root = eye.frequency_sensitivity(prob, sol,
                                     np.array([5.0, 5.0, 5.0]), 6.0)
    # added mass lowers frequency; the tip dominates for bending
    assert tip[0]["df_dm_hz_per_kg"] < 0
    assert abs(tip[0]["df_dm_hz_per_kg"]) > \
        10 * abs(root[0]["df_dm_hz_per_kg"])
