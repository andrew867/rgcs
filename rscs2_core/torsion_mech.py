"""Mechanical torsion (Agent M3; RGCS-V4-EQ-015; quantities
torsion.mechanical.twist_rate / mode_energy).

Validated against Saint-Venant closed forms and the existing FEM
authority: the free-free torsional modal ladder of a prismatic bar is
f_n = n * v_t / (2 L) with v_t = sqrt(G Jt / (rho Ip)) — for a square
section Jt = 0.1406 a^4 (Saint-Venant's constant) and Ip = a^4/6."""

from __future__ import annotations

import math

import numpy as np

from .multiphysics import get_material, make_result

#: Saint-Venant torsion constant coefficient for a square section
SQUARE_JT_COEFF = 0.1406


def saint_venant_twist_rate(torque_n_m: float, shear_modulus_pa: float,
                            radius_m: float) -> float:
    """Circular shaft: theta' = T / (G J), J = pi r^4 / 2 (exact)."""
    J = math.pi * radius_m ** 4 / 2.0
    return torque_n_m / (shear_modulus_pa * J)


def square_bar_torsional_ladder_hz(shear_modulus_pa: float,
                                   density_kg_m3: float, side_m: float,
                                   length_m: float, n: int = 1) -> float:
    """Free-free torsional frequency of a square prismatic bar
    (Saint-Venant warping constant; classical)."""
    jt = SQUARE_JT_COEFF * side_m ** 4
    ip = side_m ** 4 / 6.0
    v_t = math.sqrt(shear_modulus_pa * jt / (density_kg_m3 * ip))
    return n * v_t / (2.0 * length_m)


def _torsion_template(basis, length_m, n_half_waves=1):
    """Nodal template of the n-th free-free torsional mode of a bar
    along z: u = cos(n pi z / L) * (z_hat x r) (rigid rotation per
    slice with axial cosine profile)."""
    x, y, z = basis.doflocs
    xc, yc = x - x.mean(), y - y.mean()
    prof = np.cos(n_half_waves * np.pi * z / length_m)
    u = np.zeros(basis.N)
    comp = np.arange(basis.N) % 3
    u[comp == 0] = (-yc * prof)[comp == 0]
    u[comp == 1] = (xc * prof)[comp == 1]
    return u


def identify_torsional_mode(problem, sol, length_m: float,
                            n_half_waves: int = 1) -> dict:
    """Find the elastic mode with maximal M-weighted overlap against
    the torsional template; return index, frequency, twist profile."""
    templ = _torsion_template(problem.basis, length_m, n_half_waves)
    templ = templ / math.sqrt(float(templ @ (problem.M @ templ)))
    nr = sol["n_rigid_modes"]
    overlaps = []
    for k in range(nr, sol["modes"].shape[1]):
        ov = abs(float(templ @ (problem.M @ sol["modes"][:, k])))
        overlaps.append(ov)
    best = int(np.argmax(overlaps))
    return {"mode_index_elastic": best,
            "frequency_hz": float(sol["elastic_frequencies_hz"][best]),
            "overlap": float(overlaps[best]),
            "all_overlaps": overlaps}


def twist_profile(problem, mode: np.ndarray, length_m: float,
                  n_slices: int = 12) -> dict:
    """Per-slice rigid-rotation angle fit theta(z) and finite-diff
    twist rate d theta/dz (quantity torsion.mechanical.twist_rate)."""
    locs = problem.basis.doflocs
    x, y, z = locs
    xc, yc = x - x.mean(), y - y.mean()
    comp = np.arange(problem.basis.N) % 3
    edges = np.linspace(z.min(), z.max(), n_slices + 1)
    zs, th = [], []
    for i in range(n_slices):
        m = (z >= edges[i]) & (z <= edges[i + 1])
        mx = m & (comp == 0)
        my = m & (comp == 1)
        # least-squares rotation angle: u_x = -theta*y, u_y = theta*x
        num = float(-(mode[mx] * yc[mx]).sum()
                    + (mode[my] * xc[my]).sum())
        den = float((yc[mx] ** 2).sum() + (xc[my] ** 2).sum())
        if den > 0:
            zs.append(0.5 * (edges[i] + edges[i + 1]))
            th.append(num / den)
    zs, th = np.array(zs), np.array(th)
    rate = np.gradient(th, zs)
    return {"quantity_id": "torsion.mechanical.twist_rate",
            "z_m": zs, "theta_rad": th, "twist_rate_rad_m": rate}


def torsional_mode_energy(problem, sol, elastic_index: int) -> dict:
    """Modal strain energy of a mass-orthonormal mode:
    U = 1/2 phi^T K phi = 1/2 omega^2 (quantity
    torsion.mechanical.mode_energy, per unit modal amplitude)."""
    nr = sol["n_rigid_modes"]
    phi = sol["modes"][:, nr + elastic_index]
    u = 0.5 * float(phi @ (problem.K @ phi))
    return {"quantity_id": "torsion.mechanical.mode_energy",
            "energy_j_per_unit_amplitude2": u}


def torque_mode_overlap(problem, sol, length_m: float,
                        axial_profile=None) -> np.ndarray:
    """Generalized force of a twisting body torque density
    b(x) = p(z) * (z_hat x r), projected on the mass-orthonormal modes
    (validated E.11 projection). A UNIFORM p(z) is orthogonal to every
    free-free torsional mode (their cos(n pi z/L) profiles integrate
    to zero) and couples only to the rigid rotation — callers wanting
    the fundamental must supply p(z) = cos(pi z / L)."""
    from .projections import assemble_body_force, project_force_vector
    if axial_profile is None:
        axial_profile = lambda z: np.ones_like(z)

    def torque_density(x):
        xc = x[0] - x[0].mean()
        yc = x[1] - x[1].mean()
        p = axial_profile(x[2])
        return np.stack([-yc * p, xc * p, np.zeros_like(xc)])

    F = assemble_body_force(problem, torque_density)
    return project_force_vector(sol, F)


def torsion_benchmark_result(fem_hz: float, analytic_hz: float,
                             material_id: str =
                             "reference.isotropic_benchmark") -> dict:
    """Result envelope for the Saint-Venant benchmark (gate D2)."""
    get_material(material_id)          # firewall lookup
    rel = abs(fem_hz - analytic_hz) / analytic_hz
    return make_result(
        "rscs2.torsion_mech.square_bar_ladder", material_id,
        "CORE_VALIDATED", ["EST", "DER"],
        {"fem_hz": fem_hz, "analytic_hz": analytic_hz,
         "rel_err": rel},
        {"frequency": "Hz", "rel_err": "dimensionless"},
        source_ids=["SRC-V4-00"], equation_ids=["RGCS-V4-EQ-015"],
        assumptions=["free-free prismatic bar",
                     "Saint-Venant Jt=0.1406 a^4 (square)"])
