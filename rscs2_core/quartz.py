"""Orientation-aware anisotropic alpha-quartz material layer (Agent 04).

RSCS2-E.3 (constitutive, reusing the FROZEN v3 stiffness constants) plus
the Bond/tensor rotation machinery between crystallographic, crystal-body
and laboratory frames, and batched Christoffel sweeps validated against
the frozen `rgcs_core.anisotropy.wave_speeds`.

Conventions (declared, tested):
  * Voigt ordering 11,22,33,23,13,12 (matches frozen v3 module).
  * Crystallographic frame: X = a-axis (2-fold), Z = c/optic axis
    (3-fold), right-handed (IEEE 176 / Bechmann 1958).
  * Rotations: intrinsic Euler z-x-z (alpha, beta, gamma), matching the
    v3 `fea_export` orientation record. R maps CRYSTAL components to
    LAB components: v_lab = R v_crystal.
  * Full-tensor rotation (exact "Bond" transformation):
      C'_ijkl = R_ia R_jb R_kc R_ld C_abcd     (rank 4)
      e'_kij  = R_ka R_ib R_jc e_abc           (rank 3)
      eps'_ij = R_ia R_jb eps_ab               (rank 2)

Piezoelectric / dielectric constants (EST handbook input; first use in
v4, registered per governance): Bechmann, Phys. Rev. 110, 1060 (1958),
IEEE-176 sign convention, room temperature:
  e11 = 0.171 C/m^2, e14 = -0.0406 C/m^2 (class 32 matrix form);
  relative permittivity (constant strain) eps11 = 4.428, eps33 = 4.634.
Third-decimal values are reference/temperature dependent and are
declared with uncertainty fields, exactly as the frozen elastic
constants were (D5-002 pattern). Temperature reference: 25 C.

No new physics: standard tensor algebra + frozen constants.
"""

from __future__ import annotations

import numpy as np

from rgcs_core.anisotropy import (ALPHA_QUARTZ_C_GPA,
                                  ALPHA_QUARTZ_DENSITY_KG_M3,
                                  alpha_quartz_stiffness_pa)
from rscs_core.propagation import voigt_to_tensor

__all__ = ["QUARTZ", "material_record", "euler_zxz_matrix",
           "rotate_stiffness", "rotate_piezo", "rotate_dielectric",
           "christoffel_speeds", "orientation_sweep",
           "quartz_piezo_tensor_c_m2", "quartz_dielectric_f_m",
           "EPS0_F_M"]

EPS0_F_M = 8.8541878128e-12   # vacuum permittivity (SI, CODATA)

# --- alpha-quartz class-32 piezoelectric matrix (stress-charge e-form),
#     3x6 Voigt, C/m^2 (Bechmann 1958 / IEEE 176) ---
_E11, _E14 = 0.171, -0.0406
_PIEZO_VOIGT = np.array([
    [_E11, -_E11, 0.0, _E14, 0.0,   0.0],
    [0.0,   0.0,  0.0, 0.0, -_E14, -_E11],
    [0.0,   0.0,  0.0, 0.0,  0.0,   0.0],
])

# relative permittivity at constant strain
_EPSR = np.diag([4.428, 4.428, 4.634])

#: Voigt index -> (i, j) pairs for expanding 3x6 piezo matrix to e_kij.
_VOIGT_IJ = ((0, 0), (1, 1), (2, 2), (1, 2), (0, 2), (0, 1))


def quartz_piezo_tensor_c_m2() -> np.ndarray:
    """Full rank-3 piezoelectric tensor e_kij (C/m^2) from the class-32
    Voigt matrix. Symmetric in (i,j) by construction."""
    e = np.zeros((3, 3, 3))
    for v, (i, j) in enumerate(_VOIGT_IJ):
        for k in range(3):
            e[k, i, j] = _PIEZO_VOIGT[k, v]
            e[k, j, i] = _PIEZO_VOIGT[k, v]
    return e


def quartz_dielectric_f_m() -> np.ndarray:
    """Dielectric tensor at constant strain, F/m."""
    return _EPSR * EPS0_F_M


def material_record() -> dict:
    """The alpha-quartz material record: constants + convention +
    provenance + uncertainty declaration. Elastic part is the FROZEN v3
    module verbatim."""
    return {
        "material": "alpha-quartz",
        "symmetry_class": "trigonal-32",
        "density_kg_m3": ALPHA_QUARTZ_DENSITY_KG_M3,
        "stiffness_voigt_gpa": ALPHA_QUARTZ_C_GPA.tolist(),
        "piezo_voigt_c_m2": _PIEZO_VOIGT.tolist(),
        "dielectric_relative_constant_strain": np.diag(_EPSR).tolist(),
        "voigt_order": "11,22,33,23,13,12",
        "frame": "X=a-axis(2-fold), Z=c-axis(3-fold), right-handed",
        "temperature_ref_c": 25.0,
        "provenance": ["frozen rgcs_core.anisotropy (Bechmann 1958; "
                       "Auld 1973)", "piezo/dielectric: Bechmann 1958, "
                       "IEEE 176 convention"],
        "uncertainty": {"elastic_third_decimal": "reference/temperature "
                        "dependent (D5-002)", "piezo_pct": 2.0,
                        "dielectric_pct": 2.0, "density_pct": 0.1},
        "classification": "EST (handbook input)",
    }


QUARTZ = material_record()


# --- rotations -------------------------------------------------------

def euler_zxz_matrix(alpha_deg: float, beta_deg: float,
                     gamma_deg: float) -> np.ndarray:
    """Intrinsic z-x-z Euler rotation matrix, crystal -> lab."""
    a, b, g = np.radians([alpha_deg, beta_deg, gamma_deg])

    def rz(t):
        return np.array([[np.cos(t), -np.sin(t), 0],
                         [np.sin(t), np.cos(t), 0], [0, 0, 1.0]])

    def rx(t):
        return np.array([[1.0, 0, 0], [0, np.cos(t), -np.sin(t)],
                         [0, np.sin(t), np.cos(t)]])

    return rz(a) @ rx(b) @ rz(g)


def _check_rotation(r: np.ndarray) -> np.ndarray:
    r = np.asarray(r, dtype=float)
    if r.shape != (3, 3) or not np.allclose(r @ r.T, np.eye(3), atol=1e-10) \
            or not np.isclose(np.linalg.det(r), 1.0, atol=1e-10):
        raise ValueError("R must be a proper rotation (R R^T = I, det=+1)")
    return r


def rotate_stiffness(c_full: np.ndarray, r: np.ndarray) -> np.ndarray:
    """Exact rank-4 (Bond) rotation of a stiffness tensor."""
    r = _check_rotation(r)
    return np.einsum("ia,jb,kc,ld,abcd->ijkl", r, r, r, r, c_full,
                     optimize=True)


def rotate_piezo(e_full: np.ndarray, r: np.ndarray) -> np.ndarray:
    """Rank-3 rotation of a piezoelectric tensor e_kij."""
    r = _check_rotation(r)
    return np.einsum("ka,ib,jc,abc->kij", r, r, r, e_full, optimize=True)


def rotate_dielectric(eps: np.ndarray, r: np.ndarray) -> np.ndarray:
    """Rank-2 rotation of a dielectric tensor."""
    r = _check_rotation(r)
    return r @ np.asarray(eps, dtype=float) @ r.T


# --- Christoffel -----------------------------------------------------

def christoffel_speeds(c_full: np.ndarray, density_kg_m3: float,
                       directions: np.ndarray) -> dict:
    """Batched Christoffel phase speeds for unit direction(s).

    directions: (3,) or (N,3). Returns speeds (N,3) sorted descending
    (qL, qS1, qS2) and polarization vectors (N,3,3). The single-direction
    case must agree with the FROZEN `rgcs_core.anisotropy.wave_speeds`
    (machine-tested)."""
    n = np.atleast_2d(np.asarray(directions, dtype=float))
    if n.shape[1] != 3 or not np.all(np.isfinite(n)):
        raise ValueError("directions must be finite (N,3)")
    norms = np.linalg.norm(n, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("zero direction")
    n = n / norms
    # Gamma_ik = C_ijkl n_j n_l, batched
    gamma = np.einsum("ijkl,nj,nl->nik", c_full, n, n, optimize=True)
    vals, vecs = np.linalg.eigh(gamma)          # ascending
    speeds = np.sqrt(np.clip(vals, 0.0, None) / density_kg_m3)
    order = np.argsort(speeds, axis=1)[:, ::-1]  # descending: qL first
    speeds = np.take_along_axis(speeds, order, axis=1)
    vecs = np.take_along_axis(vecs, order[:, None, :], axis=2)
    return {"speeds_m_s": speeds, "polarizations": vecs}


def orientation_sweep(n_theta: int = 46, n_phi: int = 91,
                      r: np.ndarray | None = None) -> dict:
    """Spherical sweep of quasi-longitudinal / shear speeds for
    (optionally rotated) alpha-quartz. Returns the grid and speed
    surfaces; used for the wave-speed surface figures."""
    c = voigt_to_tensor(alpha_quartz_stiffness_pa())
    if r is not None:
        c = rotate_stiffness(c, r)
    theta = np.linspace(0.0, np.pi, n_theta)      # from +Z
    phi = np.linspace(0.0, 2 * np.pi, n_phi)
    tt, pp = np.meshgrid(theta, phi, indexing="ij")
    dirs = np.stack([np.sin(tt) * np.cos(pp),
                     np.sin(tt) * np.sin(pp),
                     np.cos(tt)], axis=-1).reshape(-1, 3)
    out = christoffel_speeds(c, ALPHA_QUARTZ_DENSITY_KG_M3, dirs)
    s = out["speeds_m_s"].reshape(n_theta, n_phi, 3)
    return {"theta": theta, "phi": phi, "v_qL": s[:, :, 0],
            "v_qS1": s[:, :, 1], "v_qS2": s[:, :, 2]}
