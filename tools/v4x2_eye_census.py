"""Y03: independent Eye replication — full-domain unbiased cluster
census and eigenspace tracking (43_EYE_INDEPENDENT_REPLICATION_AGENT).

The V5 ladder selected, at every level, the strain-energy cluster
NEAREST the v4.1 coordinate. That selection rule cannot see whether a
different, stronger cluster exists elsewhere, or whether "the"
candidate is one fragment of a family. This census removes the bias:

1. re-solve cl=3.0 and cl=2.0 (cheap levels);
2. extract ALL clusters from D2/D1/D8 at the tested quantile, over
   the full domain, with no nearest-to-anything selection;
3. rank clusters by size and report every centroid;
4. track the first elastic eigenSPACE across the two meshes by
   subspace principal angles on the shared coarse nodes (mode
   identity by overlap, not index);
5. answer: does a persistent cluster exist near z=102.24 (the v4.1
   coordinate) under this configuration? near z=99.78 (the V5
   coordinate)? anywhere stronger than both?

Language rule (42_V421_CLOSEOUT_DELTA): the output states what the
pipeline did and did not identify under the tested configuration —
never a bare nonexistence claim.

    python tools/v4x2_eye_census.py
Writes docs/v4/proof/C02/independent_census.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import numpy as np
from skfem import MeshTet

from rgcs_core.anisotropy import (ALPHA_QUARTZ_DENSITY_KG_M3,
                                  alpha_quartz_stiffness_pa)
from rscs2_core import crystal110 as c110, eye, fem
from rscs_core.propagation import voigt_to_tensor

OUT = REPO / "docs" / "v4" / "proof" / "C02"
C_FULL = voigt_to_tensor(alpha_quartz_stiffness_pa())
RHO = ALPHA_QUARTZ_DENSITY_KG_M3
CRY = c110.build_crystal("ideal_n7")
V41 = np.array([-0.295, -0.205, 102.240])
V5 = np.array([-0.048, -0.020, 99.783])
STATION = np.array([-0.447, 0.774, 106.018])


def _enc(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    return str(o)


def census_level(cl: float) -> dict:
    m = c110.mesh_crystal(CRY, cl, workdir=OUT / "scratch")
    mesh = MeshTet(m["nodes_m"].T, m["tets"].T)
    prob = fem.assemble_anisotropic(mesh, C_FULL, RHO)
    sol = fem.solve_modes(prob, 6 + 8)
    flds = eye.evaluate_elastic_diagnostics(prob, sol, 0, C_FULL,
                                            pair_index=1)
    clusters = []
    for did in ("D2", "D1", "D8"):
        for c in eye.extract_candidates(flds[did], quantile=0.95,
                                        link_radius_mm=6.0):
            cen = np.asarray(c["centroid_mm"], float)
            clusters.append({
                "diagnostic": did,
                "centroid_mm": cen.tolist(),
                "n_points": int(c.get("n_points", 0)),
                "d_to_v41_mm": float(np.linalg.norm(cen - V41)),
                "d_to_v5_mm": float(np.linalg.norm(cen - V5)),
                "d_to_station_mm": float(np.linalg.norm(cen -
                                                        STATION)),
            })
    clusters.sort(key=lambda c: -c["n_points"])
    return {"clmax_mm": cl, "n_clusters": len(clusters),
            "clusters": clusters,
            "f_elastic_hz": [float(x) for x in
                             sol["elastic_frequencies_hz"][:8]],
            "_solution": (prob, sol, m)}


def eigenspace_overlap(lv_a: dict, lv_b: dict, k: int = 2) -> dict:
    """Track the first k-dimensional elastic eigenspace across meshes:
    sample both mode shapes at the COARSE mesh nodes (nearest fine
    node), then principal angles between the spans. The (0,1)-type
    pair is nearly degenerate, so the SPACE, not the individual
    vector, is the trackable object."""
    prob_a, sol_a, m_a = lv_a["_solution"]
    prob_b, sol_b, m_b = lv_b["_solution"]
    na = m_a["nodes_m"]
    nb = m_b["nodes_m"]
    # nearest fine node for each coarse node
    idx = np.array([int(np.argmin(np.sum((nb - p) ** 2, axis=1)))
                    for p in na])

    def shapes(sol, nodes_idx, take):
        n_rigid = sol["n_rigid_modes"]
        vecs = np.asarray(sol["modes"])[:, n_rigid:n_rigid + take]
        out = []
        for j in range(vecs.shape[1]):
            v3 = vecs[:, j].reshape(-1, 3)
            out.append(v3[nodes_idx].ravel())
        return out

    a = shapes(sol_a, np.arange(len(na)), k)
    b = shapes(sol_b, idx, k)
    qa, _ = np.linalg.qr(np.column_stack(a))
    qb, _ = np.linalg.qr(np.column_stack(b))
    svals = np.linalg.svd(qa.T @ qb, compute_uv=False)
    svals = np.clip(svals, 0.0, 1.0)
    angles_deg = np.degrees(np.arccos(svals))
    return {"principal_angles_deg": angles_deg.tolist(),
            "subspace_overlap": float(np.prod(svals) ** 2),
            "tracked": bool(np.max(angles_deg) < 30.0),
            "note": "the nearly degenerate first pair is tracked as "
                    "a 2-D eigenSPACE; individual mode indices are "
                    "not identities (Y002)"}


def main() -> int:
    print("[census] cl=3.0 ...", flush=True)
    lv3 = census_level(3.0)
    print(f"  {lv3['n_clusters']} clusters", flush=True)
    print("[census] cl=2.0 ...", flush=True)
    lv2 = census_level(2.0)
    print(f"  {lv2['n_clusters']} clusters", flush=True)
    overlap = eigenspace_overlap(lv3, lv2)

    def near(clusters, target_mm, radius_mm=3.0):
        key = {"v41": "d_to_v41_mm", "v5": "d_to_v5_mm"}[target_mm]
        return [c for c in clusters if c[key] <= radius_mm]

    near_v41 = {"cl3.0": near(lv3["clusters"], "v41"),
                "cl2.0": near(lv2["clusters"], "v41")}
    near_v5 = {"cl3.0": near(lv3["clusters"], "v5"),
               "cl2.0": near(lv2["clusters"], "v5")}
    persistent_v41 = bool(near_v41["cl3.0"] and near_v41["cl2.0"])
    persistent_v5 = bool(near_v5["cl3.0"] and near_v5["cl2.0"])

    report = {
        "purpose": "unbiased full-domain cluster census + eigenspace "
                   "tracking (Y03); no nearest-to-candidate "
                   "selection anywhere in this pipeline",
        "configuration": {"quantile": 0.95, "link_radius_mm": 6.0,
                          "diagnostics": ["D2", "D1", "D8"],
                          "mode": "first elastic pair",
                          "geometry": "ideal_n7 (idealized model)"},
        "levels": {
            "cl3.0": {k: v for k, v in lv3.items()
                      if k != "_solution"},
            "cl2.0": {k: v for k, v in lv2.items()
                      if k != "_solution"},
        },
        "eigenspace_tracking": overlap,
        "findings": {
            "persistent_cluster_within_3mm_of_v41_coordinate":
                persistent_v41,
            "persistent_cluster_within_3mm_of_v5_coordinate":
                persistent_v5,
            "statement": (
                "Under the tested mode, mesh, interpolation, and "
                "clustering configuration, the census "
                + ("identified" if persistent_v41 else
                   "did not identify")
                + " a persistent cluster within 3 mm of the v4.1 "
                  "coordinate, and "
                + ("identified" if persistent_v5 else
                   "did not identify")
                + " one within 3 mm of the v4.2.1 coordinate. This "
                  "is a statement about this pipeline and this "
                  "idealized model, not a nonexistence claim and "
                  "not a physical measurement."),
        },
    }
    (OUT / "independent_census.json").write_text(
        json.dumps(report, indent=2, default=_enc), encoding="utf-8")
    print(json.dumps(report["findings"], indent=2))
    print("eigenspace tracked:", overlap["tracked"],
          "| max angle %.1f deg"
          % max(overlap["principal_angles_deg"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
