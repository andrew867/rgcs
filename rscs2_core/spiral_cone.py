"""Spiral-cone resonant geometry (Agent G01; coverage S001-S011,
S017-S019, S023-S024 geometry side; gates G16/G17).

Validated mathematics of the contracting logarithmic spiral and its
3-D cone lift, plus fabrication exports (OpenSCAD/DXF/STL text
generation, incl. the pinched-twisted variant). Geometry merit
functionals are declared ENG constructs — never physical claims."""

from __future__ import annotations

import math

import numpy as np


# --- S001: r(theta) = r0 exp(-a theta) --------------------------------------

def log_spiral(r0_mm: float, a: float, theta: np.ndarray
               ) -> np.ndarray:
    th = np.asarray(theta, float)
    r = r0_mm * np.exp(-a * th)
    return np.stack([r * np.cos(th), r * np.sin(th)], axis=1)


def curvature_invariant(a: float) -> float:
    """S005: for the log spiral, radius of curvature rho = r*sqrt(1+
    a^2), so the dimensionless invariant kappa*r = 1/sqrt(1+a^2)."""
    return 1.0 / math.sqrt(1.0 + a * a)


def numeric_curvature_times_r(r0_mm, a, theta):
    """Numeric check target for the invariant."""
    pts = log_spiral(r0_mm, a, theta)
    d1 = np.gradient(pts, theta, axis=0)
    d2 = np.gradient(d1, theta, axis=0)
    num = np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0])
    den = (d1[:, 0] ** 2 + d1[:, 1] ** 2) ** 1.5
    kappa = num / den
    r = np.linalg.norm(pts, axis=1)
    return kappa * r


def per_turn_ratio(a: float) -> float:
    """S006: radius ratio per full turn = exp(-2 pi a)."""
    return math.exp(-2 * math.pi * a)


def a_for_ratio(ratio: float) -> float:
    """Solve exp(-2 pi a) = 1/ratio for contraction toward the centre
    with scale ratio `ratio` per turn (phi, 2, e, 8...)."""
    if ratio <= 1.0:
        raise ValueError("ratio > 1 (contraction) required")
    return math.log(ratio) / (2 * math.pi)


# --- S002: inverse frequency-wavelength surface ------------------------------

def wavelength_surface(f_hz: np.ndarray, c_m_s: float = 343.0
                       ) -> np.ndarray:
    """Declared map: radius_mm(f) = 1000*c/f (acoustic wavelength).
    A plotting/design surface, not a resonance claim."""
    f = np.asarray(f_hz, float)
    if np.any(f <= 0):
        raise ValueError("positive frequencies required")
    return 1000.0 * c_m_s / f


# --- S003: 3-D spiral cone ----------------------------------------------------

def spiral_cone_path(r0_mm: float, a: float, height_mm: float,
                     p: float, turns: float, n: int = 2000,
                     twist_pinch: float = 0.0) -> np.ndarray:
    """(r cos, r sin, z) with z = H * (1 - (r/r0)^p) (vertical
    exponent p). twist_pinch > 0 adds the pinched-twisted variant
    (gate G17): an extra azimuthal advance proportional to height and
    a radial pinch factor."""
    th = np.linspace(0.0, 2 * math.pi * turns, n)
    r = r0_mm * np.exp(-a * th)
    z = height_mm * (1.0 - (r / r0_mm) ** p)
    phi = th + twist_pinch * (z / max(height_mm, 1e-12)) * math.pi
    pinch = 1.0 - 0.3 * twist_pinch * (z / max(height_mm, 1e-12))
    return np.stack([r * pinch * np.cos(phi), r * pinch * np.sin(phi),
                     z], axis=1)


# --- S004: stable focus --------------------------------------------------------

def focus_eigenvalues(a: float) -> np.ndarray:
    """The contracting-rotating flow xdot = A x with
    A = [[-a, -1], [1, -a]] has eigenvalues exactly -a +/- i."""
    A = np.array([[-a, -1.0], [1.0, -a]])
    return np.sort_complex(np.linalg.eigvals(A))


# --- S007/S008: translations ----------------------------------------------------

def one_pointed_spinning_waveform(a: float, t: np.ndarray,
                                  omega: float = 1.0) -> dict:
    """S007 translation: the 'one-pointed spinning waveform' motif is
    the stable-focus trajectory x(t) = e^{-a w t}(cos wt, sin wt) —
    a spiral that converges to ONE POINT while spinning. SRC motif ->
    DER mathematics; no physical claim."""
    tt = np.asarray(t, float)
    x = np.exp(-a * omega * tt) * np.cos(omega * tt)
    y = np.exp(-a * omega * tt) * np.sin(omega * tt)
    return {"x": x, "y": y,
            "converges_to_origin": bool(
                np.hypot(x[-1], y[-1]) < np.hypot(x[0], y[0]) * 1e-3
                or a * omega * tt[-1] > 7)}


def cusp_response_metric(path_mm: np.ndarray,
                         amplitude: np.ndarray) -> float:
    """S008: energy concentration at the cusp/centre = fraction of
    total integrated |amplitude|^2 ds within the innermost 10 percent
    radius. Arc-length weighted so the answer does not depend on how
    densely the path is sampled (theta-uniform sampling crowds points
    near the centre of a log spiral)."""
    p = np.asarray(path_mm, float)
    r = np.linalg.norm(p[:, :2], axis=1)
    seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
    ds = np.zeros(len(p))
    ds[:-1] += 0.5 * seg
    ds[1:] += 0.5 * seg
    a2 = np.asarray(amplitude, float) ** 2 * ds
    inner = r <= 0.1 * r.max()
    return float(a2[inner].sum() / max(a2.sum(), 1e-300))


def mode_overlap(psi_a: np.ndarray, psi_b: np.ndarray,
                 weights: np.ndarray | None = None) -> float:
    """S009: Lambda_ab = <psi_a, psi_b> / (||psi_a|| ||psi_b||)."""
    w = np.ones_like(psi_a) if weights is None else weights
    num = float(np.sum(w * psi_a * psi_b))
    den = math.sqrt(float(np.sum(w * psi_a ** 2))
                    * float(np.sum(w * psi_b ** 2)))
    return num / max(den, 1e-300)


def geometry_merit(cusp_metric: float, overlap: float,
                   q_factor: float) -> dict:
    """S010: Gamma_s = cusp * |overlap| * log10(1+Q). DECLARED ENG
    ranking functional for design comparison — not a physical law."""
    val = cusp_metric * abs(overlap) * math.log10(1.0 + q_factor)
    return {"gamma_s": val, "classification": "ENGINEERING_PROTOTYPE",
            "note": "declared design-ranking functional (ENG); "
                    "carries no physical significance claim"}


# --- S011/S024: fabrication exports ----------------------------------------------

def openscad_text(r0_mm: float, a: float, height_mm: float, p: float,
                  turns: float, wall_mm: float = 1.2,
                  twist_pinch: float = 0.0) -> str:
    """Printable spiral-cone shell as an OpenSCAD polyhedron sweep
    (linear_extrude of a spiral polygon with twist), plus parameters
    header for reproducibility."""
    return f"""// RGCS V4X spiral cone (Agent G01)
// r0={r0_mm} a={a} H={height_mm} p={p} turns={turns}
// twist_pinch={twist_pinch}  (0 = plain; >0 = pinched-twisted G17)
r0 = {r0_mm}; a = {a}; H = {height_mm}; P = {p};
turns = {turns}; wall = {wall_mm}; pinch = {twist_pinch};
module spiral_profile() {{
  pts = [for (i = [0:400])
    let (th = i/400 * 360 * turns,
         r = r0 * exp(-a * th * PI / 180))
      [r * cos(th), r * sin(th)]];
  polygon(concat(pts,
    [for (i = [400:-1:0])
      let (th = i/400 * 360 * turns,
           r = r0 * exp(-a * th * PI / 180) - wall)
        [max(r,0.01) * cos(th), max(r,0.01) * sin(th)]]));
}}
linear_extrude(height = H, twist = pinch * 180,
               scale = pow(0.02, 1/P))
  spiral_profile();
"""


def dxf_polyline_text(points_xy_mm: np.ndarray) -> str:
    """Minimal ASCII DXF with one LWPOLYLINE (flat spiral cut path)."""
    pts = np.asarray(points_xy_mm, float)
    body = [f"0\nSECTION\n2\nENTITIES\n0\nLWPOLYLINE\n90\n{len(pts)}"
            "\n70\n0"]
    for x, y in pts:
        body.append(f"10\n{x:.4f}\n20\n{y:.4f}")
    body.append("0\nENDSEC\n0\nEOF\n")
    return "\n".join(body)


def stl_text_from_path(path_mm: np.ndarray, name="spiral_cone"
                       ) -> str:
    """ASCII STL ribbon along the path (design-preview mesh: each
    consecutive path pair is joined to the axis point below it)."""
    p = np.asarray(path_mm, float)
    lines = [f"solid {name}"]
    for i in range(len(p) - 1):
        a, b = p[i], p[i + 1]
        c = np.array([0.0, 0.0, 0.5 * (a[2] + b[2])])
        n = np.cross(b - a, c - a)
        nl = np.linalg.norm(n) or 1.0
        n = n / nl
        lines.append(f" facet normal {n[0]:.6e} {n[1]:.6e} "
                     f"{n[2]:.6e}\n  outer loop")
        for v in (a, b, c):
            lines.append(f"   vertex {v[0]:.6e} {v[1]:.6e} "
                         f"{v[2]:.6e}")
        lines.append("  endloop\n endfacet")
    lines.append(f"endsolid {name}")
    return "\n".join(lines)


def archimedean_control(r0_mm: float, turns: float, n=2000
                        ) -> np.ndarray:
    """S019 control: r = r0 * (1 - th/th_max) linear spiral."""
    th = np.linspace(0, 2 * math.pi * turns, n)
    r = r0_mm * (1 - th / th.max())
    return np.stack([r * np.cos(th), r * np.sin(th)], axis=1)


_MOTIFS = [
    ("S001", "logarithmic spiral r = r0 e^{a th}", "log_spiral", "DER"),
    ("S002", "curvature invariant kappa * r = 1/sqrt(1+a^2)",
     "curvature_invariant", "DER"),
    ("S003", "per-turn ratio e^{-2 pi a}", "per_turn_ratio", "DER"),
    ("S004", "wavelength surface / cone taper", "wavelength_surface",
     "DER"),
    ("S005", "spiral cone path + pinched twisted variant",
     "spiral_cone_path", "ENG"),
    ("S006", "stable-focus eigenvalues -a +/- i", "focus_eigenvalues",
     "DER"),
    ("S007", "one-pointed spinning waveform motif",
     "one_pointed_spinning_waveform", "DER"),
    ("S008", "cusp energy-concentration metric",
     "cusp_response_metric", "DER"),
    ("S009", "mode overlap Lambda_ab", "mode_overlap", "DER"),
    ("S010", "geometry merit function", "geometry_merit", "ENG"),
    ("S011", "SCAD/DXF/STL fabrication export",
     "openscad_text,dxf_polyline_text,stl_text_from_path", "ENG"),
]


def motif_registry() -> dict:
    """S001-S011 coverage declaration (gate G42)."""
    from .research_records import make_record
    out = {}
    for rid, title, fn, tag in _MOTIFS:
        out[rid] = make_record(
            "GeometryMotifRecord", rid, title, "geometry",
            "ENGINEERING_PROTOTYPE" if tag == "ENG"
            else "REDUCED_ORDER_VALIDATED", [tag],
            implementation=f"rscs2_core/spiral_cone.py::{fn}")
    return out
