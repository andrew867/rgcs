"""Agent M3 figure generation (public code paths only; deterministic).

    python tools/v4/gen_m3_figures.py
Writes docs/v4/proof/M3/figures/*.png + FIGURE_MANIFEST.json
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from rscs2_core import chiral_phonon as cp, curves, fem
from rscs2_core import optical_am as oam, torsion_mech as tm

OUT = REPO / "docs" / "v4" / "proof" / "M3" / "figures"
OUT.mkdir(parents=True, exist_ok=True)


def save(fig, name):
    p = OUT / name
    fig.savefig(p, dpi=120)
    plt.close(fig)
    return p


made = []

# 1. helix curvature/torsion vs exact
pts = curves.helix(0.02, 0.01, 4, 4001)
fr = curves.frenet_frames(pts)
ex = curves.helix_exact(0.02, 0.01)
fig, ax = plt.subplots(figsize=(7, 3.2))
s = curves.arclength(pts)
ax.plot(s, fr["curvature_per_m"], label="kappa (numeric)")
ax.plot(s, fr["torsion_per_m"], label="tau (numeric)")
ax.axhline(ex["curvature_per_m"], ls="--", c="k", lw=0.8,
           label="exact")
ax.axhline(ex["torsion_per_m"], ls="--", c="k", lw=0.8)
ax.set_xlabel("arclength (m)"); ax.set_ylabel("1/m")
ax.set_title("Frenet-Serret helix fixture (RGCS-V4-EQ-014)")
ax.legend(fontsize=8)
made.append(save(fig, "helix_frenet.png"))

# 2. torsional FEM benchmark
E, NU, RHO = 210e9, 0.3, 7850.0
G = E / (2 * (1 + NU))
a, L = 0.01, 0.12
prob = fem.assemble_isotropic(fem.box_mesh((a, a, L), (3, 3, 24)),
                              E, NU, RHO)
sol = fem.solve_modes(prob, 14)
ident = tm.identify_torsional_mode(prob, sol, L)
ana = tm.square_bar_torsional_ladder_hz(G, RHO, a, L, 1)
nr = sol["n_rigid_modes"]
prof = tm.twist_profile(prob,
                        sol["modes"][:, nr + ident["mode_index_elastic"]],
                        L)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.2))
ax1.bar(range(len(ident["all_overlaps"])), ident["all_overlaps"])
ax1.set_xlabel("elastic mode"); ax1.set_ylabel("torsional overlap")
ax1.set_title(f"FEM {ident['frequency_hz']:.1f} Hz vs Saint-Venant "
              f"{ana:.1f} Hz")
ax2.plot(prof["z_m"], prof["theta_rad"], "o-")
ax2.set_xlabel("z (m)"); ax2.set_ylabel("slice rotation (rad)")
ax2.set_title("twist profile (torsion.mechanical.twist_rate)")
made.append(save(fig, "torsion_benchmark.png"))

# 3. optical vortex: phase + charge
GX = np.linspace(-2e-3, 2e-3, 161)
f1 = oam.lg_beam(GX, GX, +1, 0.8e-3)
fm = oam.lg_beam(GX, GX, -1, 0.8e-3)
fig, axes = plt.subplots(1, 3, figsize=(11, 3.2))
for ax, (fld, tt) in zip(axes, [(f1, "l=+1"), (fm, "l=-1"),
                                (f1 + fm, "real superposition "
                                          "(charge 0)")]):
    q = oam.topological_charge(fld, GX, GX, 0.6e-3)
    ax.imshow(np.angle(fld).T, cmap="twilight", origin="lower")
    ax.set_title(f"{tt}: charge {q}", fontsize=9)
made.append(save(fig, "vortex_phase_charges.png"))

# 4. SAM/OAM maps
OM = 2 * math.pi * 4.7e14
lz = oam.oam_density_z(f1, GX, GX, OM)
az = oam.poynting_azimuthal(f1, GX, GX)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.4))
ax1.imshow(lz.T, origin="lower"); ax1.set_title("canonical OAM density")
ax2.imshow(az.T, origin="lower")
ax2.set_title("Poynting-style azimuthal flow (DISTINCT output)")
made.append(save(fig, "oam_vs_poynting.png"))

# 5. chiral phonon trajectories
w = 2 * math.pi * 5e12
t = np.linspace(0, 4 * 2 * math.pi / w, 2000)
fig, axes = plt.subplots(1, 3, figsize=(10, 3.2))
for ax, ph in zip(axes, (math.pi / 2, -math.pi / 2, 0.0)):
    tr = cp.trajectory(1.0, w, ph, t)
    ax.plot(tr["qx"], tr["qy"], lw=0.8)
    ax.set_title(f"phase {ph:+.2f}: <Lz> = "
                 f"{tr['lz_cycle_mean'] / w:+.2f} q0^2 w", fontsize=8)
    ax.set_aspect("equal")
made.append(save(fig, "chiral_phonon_trajectories.png"))

manifest = [{"file": p.name,
             "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
             "producer": "tools/v4/gen_m3_figures.py",
             "classification": "CORE_VALIDATED/REDUCED_ORDER per panel"}
            for p in made]
(OUT / "FIGURE_MANIFEST.json").write_text(
    json.dumps(manifest, indent=2))
print(f"{len(made)} figures + manifest")
