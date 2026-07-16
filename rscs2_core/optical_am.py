"""Optical angular-momentum diagnostics (Agent M3; RGCS-V4-EQ-012;
quantities angular_momentum.optical.{spin,orbital,transverse_spin}).

Monochromatic complex fields on 2-D transverse grids. Canonical and
Poynting-based outputs are kept DISTINCT; extrinsic OAM is origin-
dependent and says so; a curl/intensity feature is never a vortex
claim — topological charge requires actual phase winding."""

from __future__ import annotations

import math

import numpy as np

EPS0 = 8.8541878128e-12


def lg_beam(grid_x_m, grid_y_m, ell: int, waist_m: float,
            amplitude: float = 1.0) -> np.ndarray:
    """Paraxial Laguerre-Gaussian (p=0) transverse profile with
    topological charge ell: u ~ (r/w)^|l| exp(-r^2/w^2) exp(i l phi)."""
    X, Y = np.meshgrid(grid_x_m, grid_y_m, indexing="ij")
    r = np.hypot(X, Y)
    phi = np.arctan2(Y, X)
    return (amplitude * (math.sqrt(2) * r / waist_m) ** abs(ell)
            * np.exp(-(r / waist_m) ** 2) * np.exp(1j * ell * phi))


def plane_wave(grid_x_m, grid_y_m, jones=(1.0, 0.0),
               amplitude: float = 1.0):
    X, _ = np.meshgrid(grid_x_m, grid_y_m, indexing="ij")
    ex = amplitude * jones[0] * np.ones_like(X, dtype=complex)
    ey = amplitude * jones[1] * np.ones_like(X, dtype=complex)
    return ex, ey


def helicity_density(ex, ey) -> np.ndarray:
    """Normalized helicity in [-1, 1]: sigma = 2 Im(Ex* Ey)/(|Ex|^2+|Ey|^2)."""
    num = 2.0 * np.imag(np.conj(ex) * ey)
    den = np.abs(ex) ** 2 + np.abs(ey) ** 2
    with np.errstate(invalid="ignore", divide="ignore"):
        out = np.where(den > 0, num / den, 0.0)
    return out


def sam_density_z(ex, ey, omega: float) -> np.ndarray:
    """Canonical longitudinal spin density (EQ-012):
    s_z = (eps0 / 2 omega) * Im(E* x E)_z = (eps0/omega) Im(Ex* Ey)."""
    return (EPS0 / omega) * np.imag(np.conj(ex) * ey)


def oam_density_z(field, grid_x_m, grid_y_m, omega: float,
                  origin_m=(0.0, 0.0)) -> np.ndarray:
    """Canonical orbital AM density about `origin` (EQ-012, scalar
    component): l_z = (eps0/2w) Im[E* (x-x0) dyE - E* (y-y0) dxE].
    ORIGIN-DEPENDENT for displaced beams (extrinsic part) — declared."""
    X, Y = np.meshgrid(grid_x_m, grid_y_m, indexing="ij")
    dEx = np.gradient(field, grid_x_m, axis=0)
    dEy = np.gradient(field, grid_y_m, axis=1)
    lz = (EPS0 / (2 * omega)) * np.imag(
        np.conj(field) * ((X - origin_m[0]) * dEy
                          - (Y - origin_m[1]) * dEx))
    return lz


def topological_charge(field, grid_x_m, grid_y_m,
                       radius_m: float, center_m=(0.0, 0.0),
                       n_theta: int = 720) -> int:
    """Winding of arg(E) around a closed circular contour: the ONLY
    accepted vortex evidence (an intensity null without winding does
    not count — gate D4/D5)."""
    f = np.asarray(field)
    # a (numerically) REAL field has phase only in {0, pi}: its zeros
    # are nodal LINES, not phase singularities — winding is undefined
    # and no vortex may be claimed (gate D4/D5)
    if np.max(np.abs(f.imag)) < 1e-12 * max(np.max(np.abs(f)), 1e-300):
        return 0
    th = np.linspace(0, 2 * np.pi, n_theta, endpoint=False)
    xs = center_m[0] + radius_m * np.cos(th)
    ys = center_m[1] + radius_m * np.sin(th)
    ix = np.clip(np.searchsorted(grid_x_m, xs), 0, len(grid_x_m) - 1)
    iy = np.clip(np.searchsorted(grid_y_m, ys), 0, len(grid_y_m) - 1)
    ph = np.angle(field[ix, iy])
    d = np.diff(np.concatenate([ph, ph[:1]]))
    d = (d + np.pi) % (2 * np.pi) - np.pi
    return int(round(d.sum() / (2 * np.pi)))


def transverse_spin_evanescent(kx: float, kappa: float,
                               omega: float) -> dict:
    """Transverse spin of an evanescent TM wave
    E ~ (1, 0, i kappa/kx) e^{i kx x - kappa z} (standard fixture):
    the spin is transverse (y), locked to propagation direction —
    sign flips with kx (spin-momentum locking)."""
    ex, ez = 1.0, 1j * kappa / kx
    sy = (EPS0 / (2 * omega)) * 2 * np.imag(np.conj(ez) * ex)
    return {"quantity_id": "angular_momentum.optical.transverse_spin",
            "s_y": float(sy),
            "locked_sign": float(np.sign(sy) == np.sign(kx)),
            "note": "canonical transverse spin; distinct from "
                    "longitudinal SAM and from OAM"}


def poynting_azimuthal(field, grid_x_m, grid_y_m) -> np.ndarray:
    """Poynting-style azimuthal energy-flow proxy for a scalar
    paraxial beam ~ Im(E* grad E)_phi. Kept DISTINCT from canonical
    OAM (different key, never interchanged)."""
    X, Y = np.meshgrid(grid_x_m, grid_y_m, indexing="ij")
    dEx = np.gradient(field, grid_x_m, axis=0)
    dEy = np.gradient(field, grid_y_m, axis=1)
    r = np.hypot(X, Y)
    with np.errstate(invalid="ignore", divide="ignore"):
        phix, phiy = -Y / r, X / r
    flow = np.imag(np.conj(field) * (phix * dEx + phiy * dEy))
    return np.where(r > 0, flow, 0.0)
