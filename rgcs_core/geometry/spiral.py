"""Spiral/conical 4D projected path and compact-radius prior (RGCS-M.30..M.37).

Units: radii, heights, and path lengths in mm; theta in rad; the fourth
coordinate chi in rad (reduced mod 2 pi). The AUTHORITATIVE 3D path
length is the converged numeric polyline (RGCS-M.35, closes D-09); the
workbook closed form is exposed only as a labeled, retired approximation
with its error reported.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from ..provenance import classified, classification_string

__all__ = ["SpiralGeometry", "spiral_pitch_parameter", "spiral_curve",
           "spiral_path_length_3d_mm", "spiral_metrics"]


class SpiralGeometry(BaseModel):
    """Spiral state S_sp: q, T, R_0, H, p_z, Omega_s (RGCS-M.30 inputs).
    Defaults are design choices (RG-08); q = e is Source claim (JH spiral)."""

    model_config = ConfigDict(frozen=True)

    q_per_turn: float = Field(default=math.e, gt=1.0)
    turns: float = Field(default=4.0, gt=0.0)
    outer_radius_mm: float = Field(default=60.0, gt=0.0)
    height_mm: float = Field(default=80.0, gt=0.0)
    cone_exponent: float = Field(default=1.5, gt=0.0)   # p_z (D-07 rename)
    phase_winding: float = Field(default=1.0, gt=0.0)   # Omega_s
    chi_0_rad: float = 0.0


@classified("Established", registry=("RGCS-M.31",), sources=("RG-08",))
def spiral_pitch_parameter(q_per_turn: float) -> float:
    """Pitch parameter a = ln q / (2 pi) (RGCS-M.31). Golden: q = e ->
    a = 0.15915494309 (G-10)."""
    if not (math.isfinite(q_per_turn) and q_per_turn > 1.0):
        raise ValueError("q_per_turn must be > 1")
    return math.log(q_per_turn) / (2.0 * math.pi)


@classified("Established", registry=("RGCS-M.30",), sources=("RG-08",),
            note="differential geometry Established; physical relevance is "
                 "Hypothesis H-06")
def spiral_curve(g: SpiralGeometry, samples: int = 1200) -> dict[str, np.ndarray]:
    """Sample the 4D spiral state path X(theta) (RGCS-M.30):
    [R_0 e^{-a theta} cos theta, R_0 e^{-a theta} sin theta,
     H (1 - (r/R_0)^{p_z}), chi_0 + Omega_s theta].
    The fourth coordinate mod 2 pi is the compact phase chi."""
    if samples < 32:
        raise ValueError("samples must be >= 32")
    a = spiral_pitch_parameter(g.q_per_turn)
    theta = np.linspace(0.0, 2.0 * math.pi * g.turns, samples)
    r = g.outer_radius_mm * np.exp(-a * theta)
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    normalized = np.clip(r / g.outer_radius_mm, 0.0, 1.0)
    z = g.height_mm * (1.0 - normalized ** g.cone_exponent)
    chi = np.mod(g.chi_0_rad + g.phase_winding * theta, 2.0 * math.pi)
    return {"theta": theta, "r": r, "x": x, "y": y, "z": z, "chi": chi}


def _polyline_length(g: SpiralGeometry, samples: int) -> float:
    c = spiral_curve(g, samples)
    dx, dy, dz = np.diff(c["x"]), np.diff(c["y"]), np.diff(c["z"])
    return float(np.sum(np.sqrt(dx * dx + dy * dy + dz * dz)))


@classified("Derived", registry=("RGCS-M.35",),
            note="the single project definition of the 3D path length "
                 "(closes D-09); sample count doubled until rel change < 1e-6")
def spiral_path_length_3d_mm(g: SpiralGeometry, rel_tol: float = 1e-6,
                             initial_samples: int = 1200,
                             max_doublings: int = 14) -> dict[str, Any]:
    """AUTHORITATIVE numeric 3D path length (RGCS-M.35): polyline length
    over theta with sample count doubled until |l(2s) - l(s)|/l(2s) < rel_tol
    (>= 1200 initial samples)."""
    if initial_samples < 1200:
        raise ValueError("initial_samples must be >= 1200 (RGCS-M.35)")
    s = initial_samples
    prev = _polyline_length(g, s)
    for _ in range(max_doublings):
        s *= 2
        cur = _polyline_length(g, s)
        if abs(cur - prev) / cur < rel_tol:
            return {"length_mm": cur, "samples": s,
                    "rel_change": abs(cur - prev) / cur, "converged": True,
                    "classification":
                        classification_string(spiral_path_length_3d_mm)}
        prev = cur
    raise RuntimeError("3D path length did not converge (RGCS-M.35 criterion)")


@classified("Derived", registry=("RGCS-M.31", "RGCS-M.32", "RGCS-M.33",
                                 "RGCS-M.34", "RGCS-M.35", "RGCS-M.36",
                                 "RGCS-M.37"),
            sources=("RG-08", "RG-09"),
            note="R_chi priors are Hypothesis (definition choices A-07); "
                 "the retired closed form is reported ONLY as a labeled "
                 "approximation with its error vs RGCS-M.35")
def spiral_metrics(g: SpiralGeometry) -> dict[str, Any]:
    """Spiral invariants and compact-radius priors.

    * a = ln q/(2 pi)                         (RGCS-M.31, Established)
    * lambda_s = -a + i                       (RGCS-M.32, Established)
    * r_kappa = 1/sqrt(1+a^2)                 (RGCS-M.33, Established)
    * exact planar arc length                 (RGCS-M.34, Established)
    * converged numeric 3D length             (RGCS-M.35, AUTHORITATIVE)
    * R_chi^(s) = l_3D/(2 pi T)               (RGCS-M.36, Hypothesis A-07)
    * per-turn l_k and R_chi,k = l_k/(2 pi)   (RGCS-M.37, Hypothesis,
      competing definition; model comparison required, RG-09)

    NOTE (D-21): the TEX default R_chi = 100 mm is an arbitrary placeholder,
    unrelated to these spiral-derived priors."""
    a = spiral_pitch_parameter(g.q_per_turn)
    planar = (g.outer_radius_mm * math.sqrt(1.0 + a * a) / a
              * (1.0 - math.exp(-2.0 * math.pi * a * g.turns)))
    conv = spiral_path_length_3d_mm(g)
    l3d = conv["length_mm"]
    samples = conv["samples"]

    # Per-turn 3D lengths from the converged sampling (RGCS-M.37).
    c = spiral_curve(g, samples)
    seg = np.sqrt(np.diff(c["x"]) ** 2 + np.diff(c["y"]) ** 2
                  + np.diff(c["z"]) ** 2)
    mid_theta = 0.5 * (c["theta"][1:] + c["theta"][:-1])
    n_whole = int(math.floor(g.turns))
    per_turn = [float(np.sum(seg[(mid_theta >= 2 * math.pi * k)
                                 & (mid_theta < 2 * math.pi * (k + 1))]))
                for k in range(n_whole)]

    retired_closed_form = planar * math.sqrt(1.0 + (g.height_mm / planar) ** 2)

    return {
        "pitch_parameter_a": a,
        "scale_rotation_eigenvalue": complex(-a, 1.0),
        "curvature_invariant_rkappa": 1.0 / math.sqrt(1.0 + a * a),
        "pitch_angle_deg": math.degrees(math.atan(a)),
        "radial_scale_after_turn": 1.0 / g.q_per_turn,
        "planar_arc_length_mm": planar,
        "path_length_3d_mm": l3d,                      # AUTHORITATIVE (M.35)
        "path_length_samples": samples,
        "per_turn_length_mm": per_turn,                # RGCS-M.37
        "compact_radius_prior_mm": l3d / (2.0 * math.pi * g.turns),  # M.36
        "per_turn_compact_radius_mm": [lk / (2.0 * math.pi)
                                       for lk in per_turn],          # M.37
        "retired_closed_form_mm": retired_closed_form,
        "retired_closed_form_rel_error": retired_closed_form / l3d - 1.0,
        "classification": classification_string(spiral_metrics),
    }
