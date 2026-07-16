"""Agent C02 canonical run: sub-mm Eye refinement on the 110 mm
crystal. Ladder cl 8.0 / 5.5 / 4.5 mm, 8 elastic modes, driven
complex-response D9/D10, frequency-sensitivity map.

    python tools/v4x_eye_refinement_run.py
Writes docs/v4/proof/C02/*.json
"""
from __future__ import annotations

import json

def _enc(o):
    import numpy as _np
    if isinstance(o, _np.ndarray):
        return o.tolist()
    if isinstance(o, (_np.floating, _np.integer)):
        return o.item()
    return str(o)
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import numpy as np
from skfem import MeshTet

from rscs2_core import crystal110 as c110, eye, eye_refinement as er, fem
from rgcs_core.anisotropy import (ALPHA_QUARTZ_DENSITY_KG_M3,
                                  alpha_quartz_stiffness_pa)
from rscs_core.propagation import voigt_to_tensor

OUT = REPO / "docs" / "v4" / "proof" / "C02"
OUT.mkdir(parents=True, exist_ok=True)
C_FULL = voigt_to_tensor(alpha_quartz_stiffness_pa())
RHO = ALPHA_QUARTZ_DENSITY_KG_M3
CRY = c110.build_crystal("ideal_n7")
CAND = np.array([-0.295, -0.205, 102.240])       # frozen v4.1 record
STATION = np.array([-0.447, 0.774, 106.018])

levels = {}
sols = {}
for label, cl in (("coarse", 8.0), ("fine", 5.5), ("finer", 4.5)):
    print(f"[{label}] cl={cl} ...", flush=True)
    m = c110.mesh_crystal(CRY, cl, workdir=OUT / "scratch")
    mesh = MeshTet(m["nodes_m"].T, m["tets"].T)
    prob = fem.assemble_anisotropic(mesh, C_FULL, RHO)
    sol = fem.solve_modes(prob, 6 + 8)           # 8 elastic (A08)
    sols[label] = (prob, sol, m)
    # candidate at this level: strain-energy cluster nearest the
    # frozen candidate coordinate
    flds = eye.evaluate_elastic_diagnostics(prob, sol, 0, C_FULL,
                                            pair_index=1)
    cands = []
    for did in ("D2", "D1", "D8"):
        cands += eye.extract_candidates(flds[did], quantile=0.95,
                                        link_radius_mm=6.0)
    best = min(cands, key=lambda c:
               np.linalg.norm(np.asarray(c["centroid_mm"]) - CAND))
    # element spacing = mean edge length proxy from quality manifest
    spacing = m["manifest"]["quality"].get("mean_edge_mm")
    if spacing is None:
        vol = m["manifest"]["analytic_volume_mm3"] \
            if "analytic_volume_mm3" in m["manifest"] else None
        n_tets = m["manifest"]["n_tets"]
        spacing = ((vol or 6.0e4) / n_tets) ** (1 / 3) * 1.7
    levels[label] = {"clmax_mm": cl,
                     "centroid_mm": best["centroid_mm"],
                     "element_spacing_mm": float(spacing),
                     "f_elastic_hz":
                     sol["elastic_frequencies_hz"][:8].tolist()}
    print(f"  centroid {np.round(best['centroid_mm'], 3)} "
          f"spacing~{spacing:.2f} mm", flush=True)

ladder = er.candidate_ladder(levels)
finest = levels["finer"]
verdict = er.refined_verdict(
    finest["centroid_mm"], STATION,
    halfwidth_mm=ladder["finest_halfwidth_mm"],
    convergence_shift_mm=ladder["shifts_mm"][-1],
    cloud_rms_mm=0.032)
(OUT / "refinement_ladder.json").write_text(
    json.dumps({"levels": levels, "ladder": ladder,
                "refined_verdict": verdict}, indent=2, default=_enc))
print("verdict:", verdict["classification"],
      "sep", round(verdict["separation_mm"], 3),
      "halfwidth", round(verdict["candidate_halfwidth_mm"], 3))

# A09: driven complex response + D9/D10 (finer level)
prob, sol, _ = sols["fine"]
phase = er.driven_phase_diagnostics(prob, sol, 0)
(OUT / "driven_phase_diagnostics.json").write_text(
    json.dumps(phase, indent=2, default=_enc))
print("D9 mean coherence", round(phase["d9_mean_coherence"], 4),
      "| D10 singularities", phase["d10_n_singularities"])

# A10: frequency sensitivity at candidate / station / midpoint
prob_c, sol_c, _ = sols["coarse"]
sens = {"rayleigh_point_sensitivity": {
            "candidate": eye.frequency_sensitivity(prob_c, sol_c,
                                                   CAND, 5.0)[:4],
            "station": eye.frequency_sensitivity(prob_c, sol_c,
                                                 STATION, 5.0)[:4]},
        "surface_patch_map": er.frequency_sensitivity_map(
            prob_c, sol_c,
            np.array([CAND, STATION,
                      0.5 * (CAND + STATION)]))}
(OUT / "frequency_sensitivity_map.json").write_text(
    json.dumps(sens, indent=2, default=_enc))
print("C02 artifacts written to", OUT)

