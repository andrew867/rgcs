"""Sub-millimetre Eye refinement (Agent C02; coverage A07-A10;
gates G07/G08).

Extends the v4.1 canonical analysis with (a) a finer mesh level and a
convergence ladder for the candidate coordinate, (b) more elastic
modes, (c) a SOLVED complex driven response feeding the D9/D10 phase
diagnostics for the first time on the real crystal, and (d) frequency
sensitivity versus probe coordinate. The exact candidate coordinate is
always preserved (G07); if resolution remains insufficient the status
says so honestly (G08) — no threshold games."""

from __future__ import annotations

import numpy as np

from . import eye, fem
from .eye import node_coincidence_comparison


def candidate_ladder(levels: dict) -> dict:
    """Convergence ladder over mesh levels: each entry of `levels`
    maps label -> {clmax_mm, centroid_mm (3,), element_spacing_mm}.
    Returns per-level records + successive centroid shifts + the
    finest-level localization halfwidth."""
    labels = list(levels)
    rows = []
    prev = None
    for lab in labels:
        rec = levels[lab]
        c = np.asarray(rec["centroid_mm"], float)
        shift = float(np.linalg.norm(c - prev)) if prev is not None \
            else None
        rows.append({"level": lab, "clmax_mm": rec["clmax_mm"],
                     "centroid_mm": c.tolist(),
                     "element_spacing_mm": rec["element_spacing_mm"],
                     "shift_from_previous_mm": shift})
        prev = c
    shifts = [r["shift_from_previous_mm"] for r in rows[1:]]
    converging = all(a >= b for a, b in zip(shifts, shifts[1:])) \
        if len(shifts) >= 2 else None
    return {"ladder": rows,
            "shifts_mm": shifts,
            "monotone_converging": converging,
            "finest_halfwidth_mm": rows[-1]["element_spacing_mm"],
            "note": "halfwidth is mesh-resolution dominated; the "
                    "candidate coordinate at every level is "
                    "preserved exactly (G07)"}


def refined_verdict(candidate_mm, station_mm, halfwidth_mm: float,
                    convergence_shift_mm: float,
                    cloud_rms_mm: float) -> dict:
    """Re-run the v4.1 uncertainty-aware comparison with the refined
    localization interval. Never restores a proximity threshold."""
    return node_coincidence_comparison(
        np.asarray(candidate_mm, float),
        np.asarray(station_mm, float)[None, :],
        candidate_halfwidth_mm=halfwidth_mm,
        comparator_halfwidth_mm=halfwidth_mm,
        mesh_resolution_mm=halfwidth_mm,
        convergence_shift_mm=convergence_shift_mm,
        cloud_rms_mm=cloud_rms_mm)


def driven_phase_diagnostics(problem, sol, mode_index: int,
                             damping_ratio: float = 0.01,
                             grid_n: int = 61,
                             slab_halfwidth_mm: float = 4.0) -> dict:
    """A09: drive the structure at an elastic mode's frequency with
    its own mass-weighted shape, take the SOLVED complex field, and
    run the real D9 (phase coherence) and D10 (winding) diagnostics —
    the first genuinely applicable run on the crystal (previously the
    engine refused, correctly, for undamped real modes)."""
    nr = sol["n_rigid_modes"]
    phi = sol["modes"][:, nr + mode_index]
    f0 = float(sol["elastic_frequencies_hz"][mode_index])
    force = problem.M @ phi
    force = force / max(np.linalg.norm(force), 1e-300)  # conditioning
    u = fem.harmonic_field(problem, force, f0, damping_ratio)
    locs = problem.basis.doflocs
    zcomp = fem.component_dofs(problem.basis, 2)
    pts = locs[:, zcomp].T * 1000.0                 # mm
    w = u[zcomp]
    # D9 on a thinned point set near the y=0 slab
    slab = np.abs(pts[:, 1]) < slab_halfwidth_mm
    sel = np.nonzero(slab)[0][::max(1, slab.sum() // 800)]
    coh = eye.phase_coherence_field(pts[sel], w[sel], radius_mm=6.0)
    # D10 on an interpolated x-z grid (y ~ 0)
    from scipy.interpolate import griddata
    gx = np.linspace(pts[slab, 0].min(), pts[slab, 0].max(), grid_n)
    gz = np.linspace(pts[slab, 2].min(), pts[slab, 2].max(), grid_n)
    GX, GZ = np.meshgrid(gx, gz, indexing="ij")
    grid = griddata(pts[slab][:, [0, 2]], w[slab], (GX, GZ),
                    method="linear", fill_value=0.0)
    sing = eye.phase_singularities_on_plane(gx, gz, grid)
    return {"drive_frequency_hz": f0,
            "damping_ratio": damping_ratio,
            "solved_complex_field": True,
            "d9_mean_coherence": float(np.mean(coh.values)),
            "d9_min_coherence": float(np.min(coh.values)),
            "d10_n_singularities": int(len(sing["charges"])),
            "d10_charges": sing["charges"].tolist(),
            "note": "phase diagnostics on an ACTUALLY SOLVED complex "
                    "response; near-resonant single-mode drive is "
                    "expected to be highly phase-coherent — vortices "
                    "here would indicate multi-mode interference"}


def frequency_sensitivity_map(problem, sol, points_mm: np.ndarray,
                              sigma_kg_m2: float = 5.0,
                              patch_mm: float = 4.0,
                              n_modes: int = 4) -> dict:
    """A10: df/f of the first modes for a small surface mass patch
    placed at each probe coordinate — how strongly each location
    couples to each mode (the candidate's mechanical signature)."""
    base = sol["elastic_frequencies_hz"][:n_modes]
    rows = []
    for p in np.atleast_2d(points_mm):
        pm = p / 1000.0
        r = patch_mm / 1000.0

        def near(x, c=pm, rr=r):
            return ((x[0] - c[0]) ** 2 + (x[1] - c[1]) ** 2
                    + (x[2] - c[2]) ** 2) < rr ** 2
        try:
            pert = fem.add_surface_mass(problem, near, sigma_kg_m2)
        except Exception:
            rows.append({"point_mm": p.tolist(),
                         "status": "NO_SURFACE_FACETS_IN_PATCH"})
            continue
        psol = fem.solve_modes(pert, 6 + n_modes)
        df = (psol["elastic_frequencies_hz"][:n_modes] - base) / base
        rows.append({"point_mm": p.tolist(),
                     "rel_shift_per_mode": df.tolist()})
    return {"base_hz": base.tolist(), "probes": rows,
            "sigma_kg_m2": sigma_kg_m2, "patch_mm": patch_mm}
