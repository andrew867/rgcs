"""Mechanical field circulation diagnostics (Agent M3; quantities
circulation.mechanical.{displacement,velocity}).

Line-integral circulation and curl of sampled displacement/velocity
fields. A circulation maximum is NEVER an automatic vortex claim
(frozen D6-003 posture; eye gates D4)."""

from __future__ import annotations

import numpy as np


def loop_circulation(field_fn, loop_points_m: np.ndarray) -> float:
    """Closed line integral  oint u . dl  by trapezoid over the loop.
    field_fn(points (N,3)) -> (N,3)."""
    lp = np.atleast_2d(np.asarray(loop_points_m, float))
    if not np.allclose(lp[0], lp[-1]):
        lp = np.vstack([lp, lp[0]])
    u = np.asarray(field_fn(lp), float)
    dl = np.diff(lp, axis=0)
    mid = 0.5 * (u[1:] + u[:-1])
    return float(np.sum(mid * dl))


def circle_loop(center_m, radius_m: float, normal="z",
                n: int = 720) -> np.ndarray:
    th = np.linspace(0, 2 * np.pi, n)
    c = np.asarray(center_m, float)
    if normal == "z":
        return np.stack([c[0] + radius_m * np.cos(th),
                         c[1] + radius_m * np.sin(th),
                         np.full_like(th, c[2])], axis=1)
    raise ValueError("only z-normal loops implemented")


def curl_grid(field_fn, center_m, half_m: float, n: int = 41) -> dict:
    """Central-difference curl_z on a z-plane grid around center."""
    xs = np.linspace(center_m[0] - half_m, center_m[0] + half_m, n)
    ys = np.linspace(center_m[1] - half_m, center_m[1] + half_m, n)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    pts = np.stack([X.ravel(), Y.ravel(),
                    np.full(X.size, center_m[2])], axis=1)
    u = np.asarray(field_fn(pts), float).reshape(n, n, 3)
    duy_dx = np.gradient(u[:, :, 1], xs, axis=0)
    dux_dy = np.gradient(u[:, :, 0], ys, axis=1)
    return {"x_m": xs, "y_m": ys, "curl_z": duy_dx - dux_dy}


def stokes_consistency(field_fn, center_m, radius_m: float,
                       n_grid: int = 81) -> dict:
    """Circulation theorem check: oint u.dl vs surface integral of
    curl_z over the enclosed disk (discretization-tolerance bound)."""
    circ = loop_circulation(field_fn,
                            circle_loop(center_m, radius_m))
    g = curl_grid(field_fn, center_m, radius_m, n_grid)
    X, Y = np.meshgrid(g["x_m"] - center_m[0], g["y_m"] - center_m[1],
                       indexing="ij")
    inside = (X ** 2 + Y ** 2) <= radius_m ** 2
    dx = g["x_m"][1] - g["x_m"][0]
    dy = g["y_m"][1] - g["y_m"][0]
    flux = float(np.sum(g["curl_z"][inside]) * dx * dy)
    denom = max(abs(circ), abs(flux), 1e-300)
    return {"quantity_id": "circulation.mechanical.displacement",
            "line_integral": circ, "curl_flux": flux,
            "rel_gap": abs(circ - flux) / denom,
            "note": "circulation is a field diagnostic; NOT an "
                    "automatic vortex claim"}
