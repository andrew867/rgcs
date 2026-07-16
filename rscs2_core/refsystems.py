"""Conventional reference systems (Agent 10, RSCS2-V.4 fork + cavity).

Proves the machinery outside the crystal application:
  * acoustic cavity — Helmholtz eigenproblem with EXACT closed-form
    reference frequencies (rigid-wall rectangular box);
  * tuning fork — symmetric/antisymmetric prong modes, common-mode
    rejection, and the V.9 avoided-crossing anchor against the FROZEN
    v3 coupled-mode model (RSCS-O.4 / RGCS-M.24).

The cantilever reference is the validated M3 benchmark (Agent 03).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import meshio
import numpy as np
from scipy.sparse.linalg import eigsh
from skfem import Basis, BilinearForm, ElementTetP2, MeshTet
from skfem.helpers import dot, grad

from .crystal110 import _gmsh_cmd, mesh_quality

__all__ = ["cavity_modes_fem", "cavity_modes_analytic", "fork_mesh",
           "SOUND_SPEED_AIR_M_S"]

SOUND_SPEED_AIR_M_S = 343.0        # dry air 20 C (standard)


# --- acoustic cavity (Helmholtz, rigid walls / Neumann) ---------------

def cavity_modes_analytic(lengths_m, c_m_s=SOUND_SPEED_AIR_M_S,
                          n_max=3) -> np.ndarray:
    """Exact rigid-wall rectangular-cavity frequencies
    f = (c/2) sqrt((l/Lx)^2 + (m/Ly)^2 + (n/Lz)^2), (l,m,n) != 0."""
    lx, ly, lz = lengths_m
    out = []
    for l_ in range(n_max + 1):
        for m_ in range(n_max + 1):
            for n_ in range(n_max + 1):
                if l_ == m_ == n_ == 0:
                    continue
                out.append(0.5 * c_m_s * np.sqrt(
                    (l_ / lx) ** 2 + (m_ / ly) ** 2 + (n_ / lz) ** 2))
    return np.sort(np.array(out))


def cavity_modes_fem(lengths_m, divisions, n_modes=8,
                     c_m_s=SOUND_SPEED_AIR_M_S) -> dict:
    """Helmholtz eigenproblem: -lap(p) = (w/c)^2 p, Neumann walls.
    K = int grad p . grad q, M = int p q / c^2; the constant-pressure
    mode (f=0) is the scalar analogue of a rigid mode."""
    from .fem import box_mesh
    mesh = box_mesh(lengths_m, divisions)
    basis = Basis(mesh, ElementTetP2())

    @BilinearForm
    def stiff(p, q, w):
        return dot(grad(p), grad(q))

    @BilinearForm
    def mass(p, q, w):
        return p * q / c_m_s ** 2

    K = stiff.assemble(basis)
    M = mass.assemble(basis)
    vals, vecs = eigsh(K, k=n_modes + 1, M=M, sigma=0.0, which="LM")
    order = np.argsort(vals)
    freqs = np.sqrt(np.clip(vals[order], 0, None)) / (2 * np.pi)
    return {"frequencies_hz": freqs, "modes": vecs[:, order],
            "basis": basis,
            "n_constant_modes": int(np.sum(freqs < 1.0))}


# --- tuning fork -------------------------------------------------------

_FORK_GEO = """SetFactory("OpenCASCADE");
Mesh.CharacteristicLengthMax = {cl};
Box(1) = {{0, 0, 0, {bw}, {bt}, {bh}}};                       // base
Box(2) = {{0, 0, {bh}, {pw}, {bt}, {ph}}};                    // prong A
Box(3) = {{{px}, 0, {bh}, {pw}, {bt}, {ph}}};                 // prong B
BooleanUnion{{ Volume{{1}}; Delete; }}{{ Volume{{2,3}}; Delete; }}
Physical Volume("fork") = {{1}};
"""


def fork_mesh(workdir, prong_len_m=0.06, prong_w_m=0.006,
              thickness_m=0.006, gap_m=0.010, base_h_m=0.015,
              cl_mm=4.0) -> dict:
    """U-shaped tuning fork: base block + two prongs (gmsh OCC boolean
    union via SUBPROCESS, DV4-006). Dimensions in meters; gmsh works in
    the same unit (consistency kept by using meters throughout)."""
    wd = Path(workdir)
    wd.mkdir(parents=True, exist_ok=True)
    bw = 2 * prong_w_m + gap_m
    geo = wd / f"fork_cl{cl_mm:g}.geo"
    msh = geo.with_suffix(".msh")
    geo.write_text(_FORK_GEO.format(
        cl=cl_mm / 1000.0, bw=bw, bt=thickness_m, bh=base_h_m,
        pw=prong_w_m, ph=prong_len_m, px=bw - prong_w_m),
        encoding="utf-8")
    run = subprocess.run(_gmsh_cmd() + ["-3", str(geo), "-o", str(msh),
                                        "-format", "msh2", "-v", "2"],
                         capture_output=True, text=True, timeout=600)
    if run.returncode != 0 or not msh.exists():
        raise RuntimeError(f"gmsh fork failed: {run.stderr[-1500:]}")
    m = meshio.read(msh)
    tets = [cb.data for cb in m.cells if cb.type == "tetra"][0]
    q = mesh_quality(m.points * 1000.0, tets)     # quality in mm units
    if q["n_inverted"] > 0:
        raise RuntimeError("inverted tets in fork mesh")
    return {"mesh": MeshTet(m.points.T, tets.T), "quality": q,
            "dims": {"prong_len_m": prong_len_m, "prong_w_m": prong_w_m,
                     "thickness_m": thickness_m, "gap_m": gap_m,
                     "base_h_m": base_h_m, "base_w_m": bw}}
