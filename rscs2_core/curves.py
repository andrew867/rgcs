"""Curve geometry: arclength, Frenet-Serret frames, curvature and
GEOMETRIC torsion (Agent M3; RGCS-V4-EQ-014, quantity
torsion.curve.frenet_serret).

Geometric torsion of a space curve is NOT a force field and NOT the
mechanical twist rate (registry forbidden aliases enforce this)."""

from __future__ import annotations

import numpy as np

#: relative curvature floor: below kappa * (curve extent) < FLOOR_REL
#: the normal/binormal are numerically undefined and torsion is
#: reported as NaN with a flag rather than a fabricated value.
#: (An absolute floor fails for long curves whose roundoff curvature
#: scales with coordinate magnitude.)
CURVATURE_FLOOR_REL = 1e-9


def _derivatives(points: np.ndarray):
    """Uniform-parameter derivatives by central differences; the
    Frenet formulas below are parameterization-invariant."""
    p = np.asarray(points, float)
    r1 = np.gradient(p, axis=0)
    r2 = np.gradient(r1, axis=0)
    r3 = np.gradient(r2, axis=0)
    return r1, r2, r3


def arclength(points: np.ndarray) -> np.ndarray:
    p = np.asarray(points, float)
    seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
    return np.concatenate([[0.0], np.cumsum(seg)])


def frenet_frames(points: np.ndarray) -> dict:
    """Tangent/normal/binormal, curvature kappa, torsion tau along the
    curve. tau = (r' x r'') . r''' / |r' x r''|^2 (EQ-014)."""
    r1, r2, r3 = _derivatives(points)
    speed = np.linalg.norm(r1, axis=1)
    T = r1 / speed[:, None]
    c12 = np.cross(r1, r2)
    n12 = np.linalg.norm(c12, axis=1)
    kappa = n12 / speed ** 3
    extent = float(np.linalg.norm(
        np.asarray(points, float).max(0)
        - np.asarray(points, float).min(0))) or 1.0
    degenerate = kappa * extent < CURVATURE_FLOOR_REL
    with np.errstate(divide="ignore", invalid="ignore"):
        tau = np.einsum("ij,ij->i", c12, r3) / n12 ** 2
        B = c12 / n12[:, None]
    tau[degenerate] = np.nan
    B[degenerate] = np.nan
    N = np.cross(B, T)
    return {"quantity_id": "torsion.curve.frenet_serret",
            "tangent": T, "normal": N, "binormal": B,
            "curvature_per_m": kappa, "torsion_per_m": tau,
            "degenerate_curvature": degenerate,
            "note": "geometric curve torsion; not a force field, not "
                    "mechanical twist"}


def helix(radius_m: float, pitch_m: float, turns: float = 3.0,
          n: int = 2001, handedness: int = +1) -> np.ndarray:
    """Analytic fixture: helix with exact kappa = R/(R^2+p^2),
    tau = h*p/(R^2+p^2), p = pitch/(2 pi)."""
    t = np.linspace(0, 2 * np.pi * turns, n)
    p = pitch_m / (2 * np.pi)
    return np.stack([radius_m * np.cos(t),
                     handedness * radius_m * np.sin(t), p * t], axis=1)


def helix_exact(radius_m: float, pitch_m: float,
                handedness: int = +1) -> dict:
    p = pitch_m / (2 * np.pi)
    d = radius_m ** 2 + p ** 2
    return {"curvature_per_m": radius_m / d,
            "torsion_per_m": handedness * p / d}
