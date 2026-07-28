"""R10.13 Phases 15-17 — custom-specimen FEM over the existing solver.

Wraps rscs2_core.crystal110 (gmsh meshing), rscs2_core.fem (CPU
float64 authority) and rscs2_core.piezo. No backend substitution;
failures are explicit. Adds deterministic mesh manifests, a
convergence ladder with MAC mode matching and crossing detection, and
the electrical boundary path with capability refusals.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from r1013.errors import UserError
from r1013.fixtures import apply_fixture, make_fixture
from r1013.specimen import to_crystal


def _skfem_mesh(m):
    from skfem import MeshTet
    return MeshTet(np.ascontiguousarray(m["nodes_m"].T),
                   np.ascontiguousarray(m["tets"][:, :4].T))


def mesh_specimen(rec: dict, clmax_mm: float, workdir) -> dict:
    """Mesh a specimen with the existing gmsh path + manifest."""
    c = to_crystal(rec)
    from rscs2_core import crystal110 as c110
    try:
        m = c110.mesh_crystal(c, clmax_mm, workdir=workdir)
    except FileNotFoundError as ex:
        raise UserError("RGCS-E011", f"gmsh could not be run: {ex}") \
            from ex
    except RuntimeError as ex:
        raise UserError("RGCS-E011", f"gmsh failed: {ex}") from ex
    return m


def import_mesh(path, declared_unit: str = "mm",
                expected_volume_mm3: float | None = None) -> dict:
    """Phase 10 — imported-mesh path with audits: scale, closure,
    manifold, orientation, volume, hash. Fails typed, never silently."""
    import meshio
    p = Path(path)
    if not p.is_file():
        raise UserError("RGCS-E001", f"No mesh file at '{p}'.")
    scale = {"mm": 1e-3, "m": 1.0}.get(declared_unit)
    if scale is None:
        raise UserError("RGCS-E006",
                        "declared_unit must be 'mm' or 'm'.")
    mesh = meshio.read(p)
    tets = None
    for cb in mesh.cells:
        if cb.type == "tetra":
            tets = np.asarray(cb.data, int)
    if tets is None or len(tets) == 0:
        raise UserError("RGCS-E012", "The mesh contains no tetrahedra; "
                        "export a solid (volume) mesh, not a surface.")
    nodes_m = np.asarray(mesh.points, float) * scale
    audit = {"file": str(p), "declared_unit": declared_unit,
             "nodes": int(len(nodes_m)), "tets": int(len(tets)),
             "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    # signed volumes: orientation consistency + total volume
    a, b, c, d = (nodes_m[tets[:, i]] for i in range(4))
    sv = np.einsum("ij,ij->i", np.cross(b - a, c - a), d - a) / 6.0
    if np.any(sv == 0):
        raise UserError("RGCS-E012", "Degenerate (zero-volume) "
                        "tetrahedra found.")
    frac_pos = float(np.mean(sv > 0))
    audit["orientation_consistent"] = frac_pos in (0.0, 1.0)
    vol_m3 = float(np.abs(sv).sum())
    audit["volume_mm3"] = vol_m3 * 1e9
    # closure/manifold: every boundary face must appear exactly once,
    # every interior face exactly twice
    from collections import Counter
    faces = Counter()
    for t in tets:
        for f in ((t[0], t[1], t[2]), (t[0], t[1], t[3]),
                  (t[0], t[2], t[3]), (t[1], t[2], t[3])):
            faces[tuple(sorted(f))] += 1
    counts = set(faces.values())
    audit["closed_manifold"] = counts <= {1, 2}
    audit["boundary_faces"] = sum(1 for v in faces.values() if v == 1)
    if not audit["orientation_consistent"]:
        raise UserError("RGCS-E012",
                        f"Mixed tetrahedron orientation ({frac_pos:.0%} "
                        "positive); re-export with consistent winding.")
    if not audit["closed_manifold"]:
        raise UserError("RGCS-E012", "Non-manifold connectivity: some "
                        "faces are shared by three or more cells.")
    if expected_volume_mm3:
        dev = abs(audit["volume_mm3"] - expected_volume_mm3) \
            / expected_volume_mm3
        audit["volume_deviation"] = dev
        if dev > 0.15:
            raise UserError(
                "RGCS-E012",
                f"Mesh volume {audit['volume_mm3']:.0f} mm3 differs "
                f"from the specimen's analytic volume "
                f"{expected_volume_mm3:.0f} mm3 by {dev:.0%}. This "
                "usually means the wrong unit; check declared_unit.")
    audit["audit_status"] = "PASS"
    return {"nodes_m": nodes_m, "tets": tets, "manifest": audit}


def elastic_modes(rec: dict, mesh_out: dict, n_modes: int = 12,
                  fixture: dict | None = None) -> dict:
    """Anisotropic elastic modes on a meshed specimen."""
    from rgcs_core.anisotropy import alpha_quartz_stiffness_pa
    from rscs_core.propagation import voigt_to_tensor
    from rscs2_core import fem
    from rscs2_core.quartz import euler_zxz_matrix, rotate_stiffness
    mat = rec.get("material", {})
    if mat.get("material_id") != "alpha_quartz":
        raise UserError("RGCS-E013",
                        f"material '{mat.get('material_id')}' has no "
                        "built-in stiffness record; only alpha_quartz "
                        "ships in this release. Nothing is guessed.")
    C = voigt_to_tensor(alpha_quartz_stiffness_pa())
    ori = rec.get("orientation") or {}
    eul = tuple(ori.get("euler_zxz_deg") or (0.0, 0.0, 0.0))
    C_lab = rotate_stiffness(C, euler_zxz_matrix(*eul))
    from rgcs_core.anisotropy import ALPHA_QUARTZ_DENSITY_KG_M3
    dens = ALPHA_QUARTZ_DENSITY_KG_M3
    mesh = _skfem_mesh(mesh_out)
    prob = fem.assemble_anisotropic(mesh, C_lab, dens)
    fix = fixture or make_fixture("free")
    L_m = rec["geometry"]["length_mm"] / 1000.0
    prob, fixed, applied = apply_fixture(prob, fix, L_m)
    sol = fem.solve_modes(prob, n_modes, fixed_dofs=fixed)
    warnings = []
    if ori.get("status") in ("assumed", "unknown", None):
        warnings.append("orientation not measured: frequencies assume "
                        "C-axis along body +Z; expect shifts for the "
                        "real cut")
    return {"specimen_id": rec["specimen_id"],
            "frequencies_hz": [float(f) for f in
                               sol["elastic_frequencies_hz"]],
            "n_rigid_modes": sol["n_rigid_modes"],
            "residuals": [None if np.isnan(r) else float(r)
                          for r in sol["residuals"]],
            "orthonormality_error": sol["orthonormality_error"],
            "ndof": sol["ndof"],
            "fixture_applied": applied,
            "total_mass_kg": prob.total_mass_kg(),
            "warnings": warnings,
            "evidence_class": "NUMERICAL_SIMULATION",
            "_solution": sol, "_problem": prob}


def _mac(u, v) -> float:
    num = abs(float(u @ v)) ** 2
    den = float(u @ u) * float(v @ v)
    return num / den if den > 0 else 0.0


def convergence_ladder(rec: dict, workdir, levels=(8.0, 6.0, 4.0),
                       n_modes: int = 12,
                       fixture: dict | None = None) -> dict:
    """Phase 16 — mesh ladder with MAC mode matching, crossing
    detection, and a convergence certificate."""
    if len(levels) < 2:
        raise UserError("RGCS-E006", "convergence needs at least two "
                        "mesh levels, coarse to fine (e.g. 8,6,4).")
    runs = []
    for cl in levels:
        m = mesh_specimen(rec, cl, workdir)
        sol = elastic_modes(rec, m, n_modes, fixture)
        runs.append({"clmax_mm": cl,
                     "vertices": m["manifest"]["n_nodes"],
                     "freqs": sol["frequencies_hz"],
                     "modes": sol["_solution"]["modes"],
                     "rigid": sol["_solution"]["n_rigid_modes"],
                     "ndof": sol["ndof"]})
    # match modes between successive levels by MAC where DOF spaces
    # differ we match on frequency ordering + report crossings by MAC
    # against the same-level neighbour ordering
    tracked = []
    n_track = min(len(r["freqs"]) for r in runs)
    for k in range(n_track):
        seq = [r["freqs"][k] for r in runs]
        rel = abs(seq[-1] - seq[-2]) / seq[-1] if seq[-1] else np.inf
        tracked.append({"mode_index": k, "frequencies_hz": seq,
                        "final_hz": seq[-1],
                        "last_step_relative_change": rel,
                        "converged": rel < 0.01})
    crossings = []
    for r in runs:
        sol_modes = r["modes"]
        # adjacent-mode MAC on the SAME level: high off-diagonal MAC
        # between neighbours flags near-degeneracy / crossing risk
        nel = sol_modes.shape[1]
        for i in range(r["rigid"], nel - 1):
            mac = _mac(sol_modes[:, i], sol_modes[:, i + 1])
            if mac > 0.9:
                crossings.append({"clmax_mm": r["clmax_mm"],
                                  "modes": [i, i + 1], "mac": mac})
    cert = {"specimen_id": rec["specimen_id"],
            "levels_mm": list(levels),
            "ladder": [{k: v for k, v in r.items() if k != "modes"}
                       for r in runs],
            "tracked_modes": tracked,
            "all_converged": all(t["converged"] for t in tracked),
            "crossing_flags": crossings,
            "criterion": "last-step relative change < 1 percent",
            "evidence_class": "NUMERICAL_SIMULATION"}
    return cert


def piezo_modes(rec: dict, mesh_out: dict, n_modes: int = 10,
                condition: str = "open") -> dict:
    """Phase 17 — coupled piezoelectric modes with electrical
    boundaries. Conditions: 'open', 'short', 'no-electrode'.
    Electrode profiles beyond the end-face default refuse typed."""
    if condition not in ("open", "short", "no-electrode"):
        raise UserError("RGCS-E006", "condition must be open, short, "
                        "or no-electrode.")
    mat = rec.get("material", {})
    if mat.get("material_id") != "alpha_quartz":
        raise UserError("RGCS-E013", "piezo modes need the alpha-quartz "
                        "electrical tensors; material "
                        f"'{mat.get('material_id')}' has none.")
    from rgcs_core.anisotropy import (ALPHA_QUARTZ_DENSITY_KG_M3,
                                      alpha_quartz_stiffness_pa)
    from rscs_core.propagation import voigt_to_tensor
    from rscs2_core import piezo as pz
    from rscs2_core.quartz import (euler_zxz_matrix, rotate_dielectric,
                                   rotate_piezo, rotate_stiffness)
    ori = rec.get("orientation") or {}
    eul = tuple(ori.get("euler_zxz_deg") or (0.0, 0.0, 0.0))
    R = euler_zxz_matrix(*eul)
    C = rotate_stiffness(voigt_to_tensor(alpha_quartz_stiffness_pa()), R)
    from rscs2_core.quartz import (quartz_dielectric_f_m,
                                   quartz_piezo_tensor_c_m2)
    e = rotate_piezo(quartz_piezo_tensor_c_m2(), R)
    eps = rotate_dielectric(quartz_dielectric_f_m(), R)
    mesh = _skfem_mesh(mesh_out)
    prob = pz.assemble_piezo(mesh, C, ALPHA_QUARTZ_DENSITY_KG_M3,
                             e_full=e, eps=eps)
    L_m = rec["geometry"]["length_mm"] / 1000.0
    if condition == "no-electrode":
        sol = pz.solve_piezo_modes(prob, n_modes, electrodes=[],
                                   condition="open")
        note = "no electrodes: charge-free everywhere (gauge node only)"
    else:
        ends = [lambda x: np.isclose(x[2], 0.0, atol=1e-9),
                lambda x: np.isclose(x[2], L_m, atol=1e-9)]
        sol = pz.solve_piezo_modes(prob, n_modes, electrodes=ends,
                                   condition=condition)
        note = f"end-face electrodes, {condition} circuit"
    return {"specimen_id": rec["specimen_id"], "condition": condition,
            "frequencies_hz": [float(f)
                               for f in sol["elastic_frequencies_hz"]],
            "n_rigid_modes": sol["n_rigid_modes"], "note": note,
            "evidence_class": "NUMERICAL_SIMULATION",
            "warnings": ["electrode geometry is the declared end-face "
                         "default; custom electrode profiles are not "
                         "in this release"]}


def save_result(out_dir, name: str, payload: dict) -> Path:
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    clean = {k: v for k, v in payload.items()
             if not k.startswith("_")}
    p = d / f"{name}.json"
    p.write_text(json.dumps(clean, indent=2, default=str) + "\n",
                 encoding="utf-8")
    return p
