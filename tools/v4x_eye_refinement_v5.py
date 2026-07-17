"""C02 Phase 5: the genuinely finer Eye refinement ladder (V5).

The v4.2.0 run called cl 8.0/5.5/4.5 mm a "sub-millimetre refinement".
It was not: the finest element spacing was 4.096 mm, and the
localization halfwidth never fell below the 3.906 mm separation, so the
run could not answer the question it was built for.

Resource estimation (tools/v4x_eye_resource_estimate.py) showed the
crystal meshes are small enough that a genuinely fine GLOBAL ladder is
feasible on this hardware:

    cl=1.5 ->  30,816 dof      cl=1.25 -> ~69k dof
    cl=1.0 -> ~127k dof, ~0.7 GB LU

so this runs 3.0 / 2.0 / 1.5 / 1.25 (and 1.0 if --deep), with a wall
clock guard. Global refinement is preferred over local size fields
here because uniform refinement gives a clean convergence claim; local
refinement would leave the convergence rate entangled with the size
field's shape.

Every level preserves the exact coordinates. No proximity threshold is
used at any point: exact coincidence is 1e-6 mm and a resolved
separation is reported at its exact value (V4C-D-001).

    python tools/v4x_eye_refinement_v5.py [--deep] [--budget SECONDS]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import numpy as np
from skfem import MeshTet

from rgcs_core.anisotropy import (ALPHA_QUARTZ_DENSITY_KG_M3,
                                  alpha_quartz_stiffness_pa)
from rscs2_core import crystal110 as c110
from rscs2_core import eye
from rscs2_core import eye_refinement as er
from rscs2_core import fem
from rscs_core.propagation import voigt_to_tensor

OUT = REPO / "docs" / "v4" / "proof" / "C02"
OUT.mkdir(parents=True, exist_ok=True)

C_FULL = voigt_to_tensor(alpha_quartz_stiffness_pa())
RHO = ALPHA_QUARTZ_DENSITY_KG_M3
CRY = c110.build_crystal("ideal_n7")

# frozen v4.1 canonical record — never modified, never moved
CAND = np.array([-0.295, -0.205, 102.240])
STATION = np.array([-0.447, 0.774, 106.018])
CANONICAL_SEPARATION_MM = 3.906


def _enc(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    return str(o)


def _spacing(m) -> float:
    """Representative element spacing: (volume/n_tets)^(1/3) scaled to
    an edge length for a regular tet."""
    man = m["manifest"]
    q = man.get("quality", {})
    if q.get("mean_edge_mm"):
        return float(q["mean_edge_mm"])
    nodes_mm = m["nodes_m"] * 1000.0
    tets = m["tets"]
    p = nodes_mm[tets]
    v = np.abs(np.einsum("ij,ij->i",
                         p[:, 1] - p[:, 0],
                         np.cross(p[:, 2] - p[:, 0],
                                  p[:, 3] - p[:, 0]))) / 6.0
    return float(np.mean((v * 6 * np.sqrt(2)) ** (1 / 3)))


def _free_gb() -> float:
    """Available physical memory, so a level that would thrash the
    machine is skipped rather than discovered by swapping."""
    try:
        import ctypes

        class MS(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        s = MS()
        s.dwLength = ctypes.sizeof(MS)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s))
        return s.ullAvailPhys / 1e9
    except Exception:                                  # noqa: BLE001
        return float("inf")


def run(levels_cl, budget_s: float, min_free_gb: float = 6.0) -> dict:
    levels = {}
    sols = {}
    t_start = time.perf_counter()
    for cl in levels_cl:
        elapsed = time.perf_counter() - t_start
        if elapsed > budget_s:
            print(f"[budget] {elapsed:.0f}s used; stopping before "
                  f"cl={cl}. This is an honest stop, not a result.",
                  flush=True)
            levels["_stopped_before"] = cl
            break
        free = _free_gb()
        if free < min_free_gb:
            print(f"[memory] only {free:.1f} GB free; stopping before "
                  f"cl={cl}. Infeasible on this hardware, which is an "
                  "honest stop, not a result.", flush=True)
            levels["_stopped_before"] = cl
            levels["_stop_reason"] = f"only {free:.1f} GB free"
            break
        label = f"cl{cl:g}"
        print(f"[{label}] meshing...", flush=True)
        t0 = time.perf_counter()
        m = c110.mesh_crystal(CRY, cl, workdir=OUT / "scratch")
        mesh = MeshTet(m["nodes_m"].T, m["tets"].T)
        prob = fem.assemble_anisotropic(mesh, C_FULL, RHO)
        n_dof = 3 * m["nodes_m"].shape[0]
        print(f"[{label}] dof={n_dof} solving...", flush=True)
        sol = fem.solve_modes(prob, 6 + 8)
        dt = time.perf_counter() - t0
        sols[label] = (prob, sol, m)
        flds = eye.evaluate_elastic_diagnostics(prob, sol, 0, C_FULL,
                                                pair_index=1)
        cands = []
        for did in ("D2", "D1", "D8"):
            cands += eye.extract_candidates(flds[did], quantile=0.95,
                                            link_radius_mm=6.0)
        if not cands:
            print(f"[{label}] no candidate cluster; skipping",
                  flush=True)
            continue
        best = min(cands, key=lambda c: np.linalg.norm(
            np.asarray(c["centroid_mm"]) - CAND))
        sp = _spacing(m)
        levels[label] = {
            "clmax_mm": cl,
            "centroid_mm": list(map(float, best["centroid_mm"])),
            "element_spacing_mm": sp,
            "n_dof": int(n_dof),
            "n_tets": int(m["tets"].shape[0]),
            "solve_seconds": dt,
            "f_elastic_hz":
                [float(x) for x in sol["elastic_frequencies_hz"][:8]],
        }
        c = np.asarray(best["centroid_mm"])
        print(f"[{label}] centroid {np.round(c, 3)} "
              f"spacing~{sp:.3f} mm  sep_to_station="
              f"{np.linalg.norm(c - STATION):.3f} mm  ({dt:.0f}s)  "
              f"free={_free_gb():.1f} GB", flush=True)
        # write after EVERY level: a later level that dies must not
        # destroy the levels that already succeeded
        (OUT / "refinement_levels_v5_partial.json").write_text(
            json.dumps(levels, indent=2, default=_enc),
            encoding="utf-8")
    return levels, sols


def main() -> int:
    deep = "--deep" in sys.argv
    budget = 3000.0
    if "--budget" in sys.argv:
        budget = float(sys.argv[sys.argv.index("--budget") + 1])
    cls = [3.0, 2.0, 1.5, 1.25] + ([1.0] if deep else [])
    levels, sols = run(cls, budget)
    real = {k: v for k, v in levels.items()
            if not k.startswith("_")}
    if len(real) < 2:
        print("insufficient levels completed; no verdict")
        return 1

    ladder = er.candidate_ladder(real)
    finest_key = list(real)[-1]
    finest = real[finest_key]
    verdict = er.refined_verdict(
        finest["centroid_mm"], STATION,
        halfwidth_mm=ladder["finest_halfwidth_mm"],
        convergence_shift_mm=ladder["shifts_mm"][-1],
        cloud_rms_mm=0.032)

    sep = verdict["separation_mm"]
    half = verdict["candidate_halfwidth_mm"]
    resolved = half < sep
    report = {
        "purpose": "genuinely finer Eye refinement (V5); supersedes "
                   "the cl 8.0/5.5/4.5 preliminary ladder in framing "
                   "only -- the earlier record is preserved",
        "canonical_record": {
            "candidate_mm": CAND.tolist(),
            "station_mm": STATION.tolist(),
            "separation_mm": CANONICAL_SEPARATION_MM,
            "halfwidth_mm": 3.08, "convergence_shift_mm": 0.353,
            "cloud_rms_mm": 0.032,
            "numerical_tolerance_mm": 1e-6,
            "note": "preserved unchanged; this run does not supersede "
                    "it and the candidate was never moved onto the "
                    "comparator"},
        "levels": real,
        "ladder": ladder,
        "refined_verdict": verdict,
        "halfwidth_below_separation": bool(resolved),
        "resolution_status": ("RESOLVED" if resolved
                              else "INSUFFICIENT_RESOLUTION"),
        "stopped_before_cl": levels.get("_stopped_before"),
    }
    (OUT / "refinement_ladder_v5.json").write_text(
        json.dumps(report, indent=2, default=_enc), encoding="utf-8")
    print("\n=== V5 verdict ===")
    print("classification:", verdict["classification"])
    print(f"separation {sep:.4f} mm   halfwidth {half:.4f} mm")
    print("halfwidth < separation:", resolved,
          "->", report["resolution_status"])
    print("artifacts:", OUT / "refinement_ladder_v5.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
