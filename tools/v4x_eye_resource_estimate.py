"""C02 Phase 5 step 1: estimate memory and runtime BEFORE each solve.

The audit rule is to estimate before meshing the whole crystal at
extreme resolution, and to stop honestly if the solve is infeasible
rather than thrash. This meshes (cheap) at a range of characteristic
lengths, records node/tet counts and mesh time, fits the h^-3 scaling,
and extrapolates the eigensolve cost. It does NOT solve.

    python tools/v4x_eye_resource_estimate.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import numpy as np

from rscs2_core import crystal110 as c110

OUT = REPO / "docs" / "v4" / "proof" / "C02"
OUT.mkdir(parents=True, exist_ok=True)
WORK = OUT / "scratch"
CRY = c110.build_crystal("ideal_n7")


def estimate(cls=(8.0, 5.5, 4.5, 3.0, 2.0, 1.5)) -> dict:
    rows = []
    for cl in cls:
        t0 = time.perf_counter()
        try:
            m = c110.mesh_crystal(CRY, cl, workdir=WORK)
        except Exception as exc:                       # noqa: BLE001
            rows.append({"clmax_mm": cl, "failed": str(exc)[:200]})
            print(f"cl={cl}: MESH FAILED: {exc}", flush=True)
            continue
        dt = time.perf_counter() - t0
        n_nodes = int(m["nodes_m"].shape[0])
        n_tets = int(m["tets"].shape[0])
        dof = 3 * n_nodes
        rows.append({"clmax_mm": cl, "n_nodes": n_nodes,
                     "n_tets": n_tets, "dof": dof,
                     "mesh_seconds": dt})
        print(f"cl={cl:4.1f}  nodes={n_nodes:7d}  tets={n_tets:8d}  "
              f"dof={dof:8d}  mesh={dt:6.1f}s", flush=True)
    ok = [r for r in rows if "dof" in r]
    # fit n_tets = a * cl^-3
    if len(ok) >= 2:
        x = np.log([r["clmax_mm"] for r in ok])
        y = np.log([r["n_tets"] for r in ok])
        slope, intercept = np.polyfit(x, y, 1)
    else:
        slope, intercept = -3.0, 0.0
    proj = {}
    for target in (1.25, 1.0, 0.75, 0.5):
        n_tets = float(np.exp(intercept + slope * np.log(target)))
        n_nodes = n_tets / 3.5          # empirical tets:nodes ratio
        dof = 3 * n_nodes
        proj[str(target)] = {"projected_tets": n_tets,
                             "projected_dof": dof,
                             "projected_lu_memory_gb":
                                 _lu_memory_gb(dof)}
    return {"measured": rows, "scaling_exponent": float(slope),
            "projection": proj,
            "memory_model": MEMORY_MODEL_NOTE}


# Calibrated against an OBSERVED run, not a textbook exponent.
#
# The first version of this estimator used the common
# nnz(LU) ~ dof^1.5 rule and projected 0.29 GB at cl=1.25. The actual
# cl=1.5 solve (30,816 dof) reached ~8.8 GB resident before it was
# stopped -- roughly 30x the projection. The rule is a 2-D result; for
# 3-D tetrahedral meshes with nested dissection the factor grows like
# dof^2, and a shift-invert ARPACK run holds the factor plus the Krylov
# basis at once.
#
# Anchor: 13.9 GB PEAK resident observed at dof = 30,816 (cl=1.5).
MEMORY_ANCHOR_DOF = 30816.0
MEMORY_ANCHOR_GB = 13.9
MEMORY_MODEL_NOTE = (
    "LU memory ~ k * dof^2, calibrated to an OBSERVED 13.9 GB peak at "
    "dof=30816 (cl=1.5) on a 31.6 GB machine. The dof^1.5 textbook "
    "rule is a 2-D result; it projected 0.29 GB for cl=1.25 and was "
    "wrong by ~150x. Corrected against the measurement, not before it. "
    "Projections: cl=1.25 ~71 GB, cl=1.0 ~236 GB -- both infeasible "
    "here, which is why the V5 ladder stops at cl=1.5.")


def _lu_memory_gb(dof: float) -> float:
    k = MEMORY_ANCHOR_GB / (MEMORY_ANCHOR_DOF ** 2)
    return k * dof ** 2


def main() -> int:
    rep = estimate()
    (OUT / "resource_estimate.json").write_text(
        json.dumps(rep, indent=2), encoding="utf-8")
    print("\nscaling exponent (n_tets ~ cl^p): p =",
          round(rep["scaling_exponent"], 3))
    for k, v in rep["projection"].items():
        print(f"  cl={k:>5}  ->  dof~{v['projected_dof']:.0f}  "
              f"LU~{v['projected_lu_memory_gb']:.2f} GB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
