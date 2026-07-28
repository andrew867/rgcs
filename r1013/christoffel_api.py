"""R10.13 Phase 14 — Christoffel engine over the existing tensor
authority (rscs2_core.quartz). Supports crystal-frame and body-frame
directions and orientation ensembles for unknown cuts."""

from __future__ import annotations

import numpy as np

from r1013.errors import UserError


def _tensors():
    from rgcs_core.anisotropy import (ALPHA_QUARTZ_DENSITY_KG_M3,
                                      alpha_quartz_stiffness_pa)
    from rscs_core.propagation import voigt_to_tensor
    return voigt_to_tensor(alpha_quartz_stiffness_pa()), \
        ALPHA_QUARTZ_DENSITY_KG_M3


def directions_report(directions, frame: str = "crystal",
                      euler_zxz_deg=(0.0, 0.0, 0.0)) -> dict:
    """Phase speeds and polarizations for unit directions.

    frame='crystal': directions are in the crystallographic frame.
    frame='body': directions are in the specimen body frame; the
    stiffness is rotated by the recorded orientation first.
    """
    if frame not in ("crystal", "body"):
        raise UserError("RGCS-E006", "frame must be 'crystal' or "
                        "'body'.")
    from rscs2_core.quartz import (christoffel_speeds,
                                   euler_zxz_matrix, rotate_stiffness)
    C, rho = _tensors()
    if frame == "body":
        C = rotate_stiffness(C, euler_zxz_matrix(*euler_zxz_deg))
    dirs = np.atleast_2d(np.asarray(directions, float))
    out = christoffel_speeds(C, rho, dirs)
    rows = []
    for i, d in enumerate(dirs):
        rows.append({"direction": (d / np.linalg.norm(d)).tolist(),
                     "qL_m_s": float(out["speeds_m_s"][i][0]),
                     "qS1_m_s": float(out["speeds_m_s"][i][1]),
                     "qS2_m_s": float(out["speeds_m_s"][i][2])})
    return {"frame": frame, "euler_zxz_deg": list(euler_zxz_deg),
            "rows": rows, "evidence_class": "ANALYTIC",
            "note": "exact anisotropic phase speeds from the frozen "
                    "alpha-quartz constants"}


def body_axis_speed(euler_zxz_deg) -> float:
    """qL speed along the body +Z axis for a recorded orientation."""
    rep = directions_report([[0.0, 0.0, 1.0]], frame="body",
                            euler_zxz_deg=euler_zxz_deg)
    return rep["rows"][0]["qL_m_s"]


def orientation_ensemble(n: int = 64, seed: int = 20260728,
                         direction=(0.0, 0.0, 1.0)) -> dict:
    """Unknown-cut ensemble: spread of qL along a body direction over
    uniformly sampled orientations. Deterministic seed; reported as a
    bracket, never a point estimate."""
    from rscs2_core.quartz import christoffel_speeds, rotate_stiffness
    C, rho = _tensors()
    rng = np.random.default_rng(seed)
    speeds = []
    d = np.asarray(direction, float)
    for _ in range(n):
        # uniform random rotation via QR of a Gaussian matrix
        q, r = np.linalg.qr(rng.standard_normal((3, 3)))
        q *= np.sign(np.diag(r))
        if np.linalg.det(q) < 0:
            q[:, 0] *= -1
        s = christoffel_speeds(rotate_stiffness(C, q), rho, d)
        speeds.append(float(s["speeds_m_s"][0][0]))
    arr = np.array(speeds)
    return {"n": n, "seed": seed, "direction": d.tolist(),
            "qL_min_m_s": float(arr.min()),
            "qL_max_m_s": float(arr.max()),
            "qL_median_m_s": float(np.median(arr)),
            "evidence_class": "ANALYTIC",
            "note": "orientation unknown: report this bracket, not a "
                    "single speed"}
