"""Agent 09: eye diagnostic + consensus engine — the MANDATORY
adversarial battery. The engine must not assume an eye exists; a null
result is a passing scientific outcome."""
from __future__ import annotations

import numpy as np
import pytest

from rscs2_core import eye, fem, projections as pj
from rscs2_core.eye import (ALLOWED_STATUSES, DIAGNOSTIC_SPECS,
                            DiagnosticField, eye_consensus,
                            extract_candidates)

RNG = np.random.default_rng(20260716)

# --- synthetic-field harness -------------------------------------------

L = 100.0                       # body: box [0,20]x[0,20]x[0,100] mm
GEOM = {
    "length_mm": L,
    "inside_fn": lambda p: ((p[:, 0] >= 0) & (p[:, 0] <= 20)
                            & (p[:, 1] >= 0) & (p[:, 1] <= 20)
                            & (p[:, 2] >= 0) & (p[:, 2] <= L)),
    "geometric_centre_mm": np.array([10.0, 10.0, 50.0]),
    "shaft_midpoint_mm": np.array([10.0, 10.0, 50.0]),
    "node_prior_mm": np.array([10.0, 10.0, 51.6]),
    "conventional_features_mm": np.array([[10.0, 10.0, 22.4],
                                          [10.0, 10.0, 77.6]]),
}
# >= 3 distinct diagnostic families (anti-double-counting is real:
# D1/D3/D7 are ONE family)
DIAG_SET = ("D2", "D6", "D11", "D8")


def _grid():
    x, y, z = np.meshgrid(np.linspace(1, 19, 8), np.linspace(1, 19, 8),
                          np.linspace(1, 99, 34), indexing="ij")
    return np.stack([x.ravel(), y.ravel(), z.ravel()], axis=1)


def _blob_field(did, center, width=4.0, mode_indices=(0, 1),
                pts=None, extra_centers=(), noise=0.0, seed=0):
    pts = _grid() if pts is None else pts
    v = np.exp(-np.sum((pts - np.asarray(center)) ** 2, axis=1)
               / (2 * width ** 2))
    for c in extra_centers:
        v = v + np.exp(-np.sum((pts - np.asarray(c)) ** 2, axis=1)
                       / (2 * width ** 2))
    if noise > 0:
        v = v + noise * np.random.default_rng(seed).random(len(pts))
    m = v.max()
    return DiagnosticField(did, pts, v / m, float(m), "synthetic",
                           mode_indices)


def _fieldset(center, **kw):
    return [_blob_field(d, center, **kw) for d in DIAG_SET]


# --- registry completeness ---------------------------------------------

def test_all_sixteen_diagnostics_registered_with_full_metadata():
    assert set(DIAGNOSTIC_SPECS) == {f"D{i}" for i in range(1, 17)}
    required = {"field_definition", "units", "normalization",
                "conventional_interpretation", "failure_conditions",
                "artifact_risks", "classification", "provenance",
                "tests"}
    for did, spec in DIAGNOSTIC_SPECS.items():
        missing = required - set(spec)
        assert not missing, f"{did} missing {missing}"
        # DV4-010: eye diagnostics are never Established
        assert "DER" in spec["classification"]
        assert "EST" not in spec["classification"].split()[0]
    assert set(ALLOWED_STATUSES) == {
        "STABLE_CANDIDATE_REGION", "MODE_SPECIFIC_CANDIDATE",
        "BOUNDARY_SENSITIVE_CANDIDATE",
        "CONVENTIONAL_NODE_EXPLAINS_RESULT", "MESH_ARTIFACT_REJECTED",
        "NO_STABLE_CANDIDATE"}


# --- MANDATORY adversarial battery -------------------------------------

def test_adversarial_synthetic_known_candidate_found():
    """A candidate planted at a known point across >= 3 diagnostic
    families must be found as a REGION near that point."""
    c0 = np.array([10.0, 10.0, 40.0])
    res = eye_consensus(_fieldset(c0), GEOM,
                        refined_fields=_fieldset(c0),
                        uncertainty_fields=[_fieldset(c0 + d)
                                            for d in ([0.5, 0, 0],
                                                      [0, 0.5, 0],
                                                      [0, 0, 0.5])])
    assert res.status == "STABLE_CANDIDATE_REGION"
    top = res.candidates[0]
    assert np.linalg.norm(top.centroid_mm - c0) < 3.0
    assert top.gates["agreement_families"] >= 3
    assert top.uncertainty["recurrence_fraction"] == 1.0
    assert top.distances_mm["geometric_centre_mm"] == pytest.approx(
        10.0, abs=3.0)
    # bounding region, not point precision
    assert np.all(top.bbox_mm[1] > top.bbox_mm[0])


def test_adversarial_no_candidate_flat_and_noise():
    """Flat fields (body-spanning) and independent random hotspots must
    BOTH yield NO_STABLE_CANDIDATE — the null result passes."""
    pts = _grid()
    flat = [DiagnosticField(d, pts, np.ones(len(pts)), 1.0, "flat",
                            (0, 1)) for d in DIAG_SET]
    res = eye_consensus(flat, GEOM)
    assert res.status == "NO_STABLE_CANDIDATE"
    assert any("not localized" in r["reason"] for r in res.rejected)
    noisy = [_blob_field(d, RNG.uniform([2, 2, 5], [18, 18, 95]),
                         width=3.0, seed=i)
             for i, d in enumerate(DIAG_SET)]
    res2 = eye_consensus(noisy, GEOM)
    assert res2.status == "NO_STABLE_CANDIDATE"


def test_adversarial_mesh_artifact_rejected():
    """A blob present at coarse resolution but ABSENT from the refined
    solve is a mesh artifact."""
    c0 = np.array([10.0, 10.0, 40.0])
    far = np.array([10.0, 10.0, 80.0])
    res = eye_consensus(_fieldset(c0), GEOM,
                        refined_fields=_fieldset(far))
    assert res.status == "MESH_ARTIFACT_REJECTED"
    assert res.candidates[0].gates["mesh_persistence_shift_mm"] > 5.0


def test_adversarial_boundary_created_false_candidate():
    """A candidate that moves when the mounting/BC changes is
    boundary-created, not intrinsic."""
    c0 = np.array([10.0, 10.0, 40.0])
    res = eye_consensus(
        _fieldset(c0), GEOM, refined_fields=_fieldset(c0),
        boundary_fields={"free": _fieldset(c0),
                         "cradle": _fieldset([10.0, 10.0, 70.0])})
    assert res.status == "BOUNDARY_SENSITIVE_CANDIDATE"


def test_adversarial_two_competing_regions():
    c1, c2 = np.array([10., 10., 30.]), np.array([10., 10., 70.])
    flds = [_blob_field(d, c1, extra_centers=[c2]) for d in DIAG_SET]
    res = eye_consensus(flds, GEOM, refined_fields=flds)
    stable = [c for c in res.candidates
              if c.status == "STABLE_CANDIDATE_REGION"]
    assert len(stable) == 2
    assert res.procedure["competing_candidates"] is True
    got = sorted(c.centroid_mm[2] for c in stable)
    assert got[0] == pytest.approx(30.0, abs=3.0)
    assert got[1] == pytest.approx(70.0, abs=3.0)


def test_adversarial_candidate_outside_body_rejected():
    pts = np.vstack([_grid(),
                     RNG.uniform([30, 30, 40], [40, 40, 60], (200, 3))])
    flds = [_blob_field(d, [35.0, 35.0, 50.0], pts=pts)
            for d in DIAG_SET]
    res = eye_consensus(flds, GEOM)
    assert res.status == "NO_STABLE_CANDIDATE"
    assert any("outside the body" in r["reason"] for r in res.rejected)


def test_adversarial_uncertainty_collapse():
    """A candidate that survives only 1 of 4 material-perturbation
    draws collapses (recurrence 0.25 < 0.6)."""
    c0 = np.array([10.0, 10.0, 40.0])
    draws = [_fieldset(c0)] + [_fieldset([10.0, 10.0, z])
                               for z in (65.0, 80.0, 90.0)]
    res = eye_consensus(_fieldset(c0), GEOM,
                        refined_fields=_fieldset(c0),
                        uncertainty_fields=draws)
    assert res.status == "NO_STABLE_CANDIDATE"
    assert any("collapsed under parameter uncertainty" in r["reason"]
               for r in res.rejected)


def test_adversarial_conventional_node_explains():
    """A blob sitting ON an ordinary node/antinode station is explained
    conventionally, never promoted."""
    c0 = np.array([10.0, 10.0, 22.4])       # a conventional feature
    res = eye_consensus(_fieldset(c0), GEOM,
                        refined_fields=_fieldset(c0))
    assert res.status == "CONVENTIONAL_NODE_EXPLAINS_RESULT"
    d = res.candidates[0].distances_mm["nearest_conventional_feature"]
    assert d <= 3.0


def test_adversarial_symmetric_body_no_unique_eye():
    """REAL FEM: a free isotropic cube (fully symmetric) must not
    produce a STABLE_CANDIDATE_REGION from single-mode fields."""
    mesh = fem.box_mesh((0.05, 0.05, 0.05), (6, 6, 6))
    prob = fem.assemble_isotropic(mesh, 210e9, 0.3, 7850.0)
    sol = fem.solve_modes(prob, 10)
    lam = 210e9 * 0.3 / ((1.3) * (0.4))
    mu = 210e9 / 2.6
    c_iso = (lam * np.einsum("ij,kl->ijkl", np.eye(3), np.eye(3))
             + mu * (np.einsum("ik,jl->ijkl", np.eye(3), np.eye(3))
                     + np.einsum("il,jk->ijkl", np.eye(3), np.eye(3))))
    flds = list(eye.evaluate_elastic_diagnostics(
        prob, sol, 0, c_iso, pair_index=1).values())
    geom = {
        "length_mm": 50.0,
        "inside_fn": lambda p: np.all((p >= -1e-9) & (p <= 50 + 1e-9),
                                      axis=1),
        "geometric_centre_mm": np.full(3, 25.0),
        "shaft_midpoint_mm": np.full(3, 25.0),
        "node_prior_mm": np.full(3, 25.0),
        "conventional_features_mm": np.empty((0, 3)),
    }
    res = eye_consensus(flds, geom)
    assert res.status != "STABLE_CANDIDATE_REGION"


def test_stable_requires_persistence_evidence():
    """V4-D-004 regression: even a perfect planted candidate must NOT
    be STABLE when no mesh-refinement evidence is supplied (G21)."""
    c0 = np.array([10.0, 10.0, 40.0])
    res = eye_consensus(_fieldset(c0), GEOM)      # no refined_fields
    assert res.status == "NO_STABLE_CANDIDATE"
    assert any("persistence not evaluated" in r["reason"]
               for r in res.rejected)


# --- complex-field diagnostics -----------------------------------------

def test_d9_phase_coherence_refuses_real_and_ranks_coherent():
    pts = _grid()[:300]
    with pytest.raises(ValueError, match="COMPLEX"):
        eye.phase_coherence_field(pts, np.ones(len(pts)), 5.0)
    uniform = np.exp(1j * 0.7) * np.ones(len(pts))
    coh = eye.phase_coherence_field(pts, uniform, 8.0)
    assert np.allclose(coh.values, 1.0)
    scrambled = np.exp(1j * RNG.uniform(0, 2 * np.pi, len(pts)))
    coh2 = eye.phase_coherence_field(pts, scrambled, 8.0)
    assert coh2.values.mean() < 0.5


def test_d10_phase_singularity_winding_and_refusal():
    x = np.linspace(-5, 5, 41)
    z = np.linspace(-5, 5, 41)
    X, Z = np.meshgrid(x, z)              # rows z, cols x
    # single +1 vortex at (1.1, -2.1), deliberately OFF-grid (a vortex
    # exactly on a node has undefined phase there)
    w = (X - 1.1) + 1j * (Z + 2.1)
    out = eye.phase_singularities_on_plane(x, z, w)
    assert len(out["charges"]) == 1
    assert out["charges"][0] == 1
    assert np.allclose(out["singularities_mm"][0], [1.1, -2.1],
                       atol=0.3)
    assert "not" in out["note"] and "vortices" in out["note"]
    with pytest.raises(ValueError, match="COMPLEX"):
        eye.phase_singularities_on_plane(x, z, np.abs(w))


def test_d5_electric_energy_density_refusal_and_uniform_field():
    """D5 refuses to run without a solved potential; a linear potential
    phi = z gives the uniform w_e = 1/2 eps_33 everywhere."""
    from skfem import Basis, ElementTetP2
    mesh = fem.box_mesh((0.02, 0.02, 0.02), (3, 3, 3))
    basis = Basis(mesh, ElementTetP2())
    epsd = np.diag([3.92e-11, 3.92e-11, 4.10e-11])
    with pytest.raises(ValueError, match="SOLVED potential"):
        eye.electric_energy_density_field(basis, None, epsd)
    phi = basis.project(lambda x: x[2])
    fld = eye.electric_energy_density_field(basis, phi, epsd)
    assert fld.diagnostic_id == "D5"
    assert fld.raw_max == pytest.approx(0.5 * 4.10e-11, rel=1e-6)
    assert np.allclose(fld.values, 1.0, atol=1e-6)   # uniform


def test_d12_em_circulation_amperes_law_and_refusal():
    """Circulation of the SOLVED Biot-Savart field around a straight
    wire equals mu0*I (Ampere); refuses to run with no field."""
    with pytest.raises(ValueError, match="SOLVED EM field"):
        eye.em_circulation(None, np.zeros((4, 3)))
    wire = np.array([[0.0, 0.0, -50.0], [0.0, 0.0, 50.0]])
    current = 2.0
    th = np.linspace(0, 2 * np.pi, 721)
    loop = np.stack([0.01 * np.cos(th), 0.01 * np.sin(th),
                     np.zeros_like(th)], axis=1)
    out = eye.em_circulation(
        lambda p: pj.biot_savart_polyline(wire, current, p), loop)
    mu0 = 4e-7 * np.pi
    assert out["circulation_t_m"] == pytest.approx(mu0 * current,
                                                   rel=1e-3)


def test_candidates_are_regions_and_json_serializable():
    c0 = np.array([10.0, 10.0, 40.0])
    res = eye_consensus(_fieldset(c0), GEOM,
                        refined_fields=_fieldset(c0))
    s = res.to_json()
    assert '"status"' in s and "STABLE" in s
    cands = extract_candidates(_blob_field("D2", c0))
    assert cands and cands[0]["n_points"] >= 3
