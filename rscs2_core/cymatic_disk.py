"""Cymatic PCB disk reference (Agent G02; coverage S012-S024;
gates G18/G19).

Structural side: exact clamped-circular-plate modal frequencies from
the Kirchhoff frequency equation J_n(l) I_n'(l) - I_n(l) J_n'(l) = 0
(scipy Bessel root solve; l_01 = 3.1962... literature anchor), with a
declared layered-composite (FR4 + copper) stiffness/mass model.
Electrical side: planar-spiral inductance (Mohan) + parallel-plate
capacitance -> LC resonance. The two resonance families are computed
SEPARATELY and compared (gate G19: structural vs electrical never
conflated). Chladni pattern synthesis gives design node maps; ring-
down metrics support the E-lane analysis pipeline (S022)."""

from __future__ import annotations

import math

import numpy as np
from scipy.optimize import brentq
from scipy.special import iv, jv

MU0 = 4e-7 * math.pi
EPS0 = 8.8541878128e-12

#: material presets (declared ENG values)
FR4 = {"e_pa": 22e9, "nu": 0.13, "rho": 1900.0}
COPPER = {"e_pa": 110e9, "nu": 0.34, "rho": 8960.0}


def _clamped_char(n: int, lam: float) -> float:
    """Clamped-plate frequency equation for nodal-diameter count n."""
    return (jv(n, lam) * (iv(n + 1, lam) + (n / lam) * iv(n, lam))
            - iv(n, lam) * (-jv(n + 1, lam) + (n / lam) * jv(n, lam)))


def clamped_plate_lambdas(n: int, n_roots: int = 3) -> list[float]:
    """First roots lambda_nm of the clamped circular plate."""
    roots, lam = [], 0.5
    step = 0.05
    prev = _clamped_char(n, lam)
    while len(roots) < n_roots and lam < 40.0:
        lam2 = lam + step
        cur = _clamped_char(n, lam2)
        if prev * cur < 0:
            roots.append(brentq(lambda x: _clamped_char(n, x),
                                lam, lam2, xtol=1e-12))
        prev, lam = cur, lam2
    return roots


def composite_plate(radius_m: float, t_sub_m: float,
                    t_cu_m: float = 0.0, copper_coverage: float = 0.0,
                    sub=FR4, cu=COPPER) -> dict:
    """Layered FR4+copper Kirchhoff plate: smeared-copper composite
    bending stiffness about the composite neutral axis (declared ENG
    approximation; coverage in [0,1] scales the copper layer)."""
    if not (0.0 <= copper_coverage <= 1.0):
        raise ValueError("coverage in [0,1]")
    tc = t_cu_m * copper_coverage
    # neutral axis from first moments (substrate centered at 0)
    ea_s = sub["e_pa"] * t_sub_m
    ea_c = cu["e_pa"] * tc
    z_c = (t_sub_m + t_cu_m) / 2.0        # copper sits on top
    zbar = (ea_c * z_c) / (ea_s + ea_c) if (ea_s + ea_c) else 0.0
    d_s = sub["e_pa"] * (t_sub_m ** 3 / 12 + t_sub_m * zbar ** 2) \
        / (1 - sub["nu"] ** 2)
    d_c = cu["e_pa"] * (tc ** 3 / 12 + tc * (z_c - zbar) ** 2) \
        / (1 - cu["nu"] ** 2) if tc else 0.0
    return {"radius_m": radius_m,
            "d_n_m": d_s + d_c,
            "rho_h_kg_m2": sub["rho"] * t_sub_m + cu["rho"] * tc}


def plate_mode_hz(plate: dict, n: int, m: int) -> float:
    """f_nm = lambda_nm^2 / (2 pi R^2) * sqrt(D / rho h)."""
    lam = clamped_plate_lambdas(n, m)[m - 1]
    return lam ** 2 / (2 * math.pi * plate["radius_m"] ** 2) * \
        math.sqrt(plate["d_n_m"] / plate["rho_h_kg_m2"])


def chladni_pattern(plate: dict, n: int, m: int,
                    grid: int = 121) -> dict:
    """S015: mode shape W(r,th) = [J_n(l r/R) - (J_n(l)/I_n(l))
    I_n(l r/R)] cos(n th) on a grid + nodal-line map."""
    lam = clamped_plate_lambdas(n, m)[m - 1]
    R = plate["radius_m"]
    x = np.linspace(-R, R, grid)
    X, Y = np.meshgrid(x, x, indexing="ij")
    r = np.hypot(X, Y)
    th = np.arctan2(Y, X)
    rr = np.clip(lam * r / R, 0, lam)
    W = (jv(n, rr) - (jv(n, lam) / iv(n, lam)) * iv(n, rr)) \
        * np.cos(n * th)
    W[r > R] = np.nan
    nodal = np.abs(W) < 0.02 * np.nanmax(np.abs(W))
    return {"x_m": x, "w": W, "nodal_mask": nodal,
            "lambda_nm": lam, "n": n, "m": m}


# --- electrical branch (gate G19: separate family) --------------------------

def spiral_inductance_h(n_turns: int, d_out_m: float,
                        d_in_m: float) -> float:
    """Mohan et al. current-sheet expression for a circular planar
    spiral: L = mu0 n^2 d_avg c1/2 [ln(c2/rho) + c3 rho + c4 rho^2],
    (c1..c4) = (1.00, 2.46, 0.00, 0.20)."""
    d_avg = 0.5 * (d_out_m + d_in_m)
    rho = (d_out_m - d_in_m) / (d_out_m + d_in_m)
    c1, c2, c3, c4 = 1.00, 2.46, 0.0, 0.20
    return (MU0 * n_turns ** 2 * d_avg * c1 / 2
            * (math.log(c2 / rho) + c3 * rho + c4 * rho ** 2))


def disk_capacitance_f(radius_m: float, t_sub_m: float,
                       eps_r: float = 4.4,
                       coverage: float = 1.0) -> float:
    area = math.pi * radius_m ** 2 * coverage
    return EPS0 * eps_r * area / t_sub_m


def electrical_resonance_hz(l_h: float, c_f: float) -> float:
    return 1.0 / (2 * math.pi * math.sqrt(l_h * c_f))


def resonance_separation_report(radius_m=0.05, t_sub_m=1.6e-3,
                                t_cu_m=35e-6, n_turns=20) -> dict:
    """Gate G19: structural f_01 vs electrical f_LC for a typical
    100 mm FR4 cymatic disk — different families, different physics,
    reported separately."""
    plate = composite_plate(radius_m, t_sub_m, t_cu_m, 0.5)
    f_struct = plate_mode_hz(plate, 0, 1)
    L = spiral_inductance_h(n_turns, 2 * radius_m * 0.9,
                            2 * radius_m * 0.2)
    C = disk_capacitance_f(radius_m, t_sub_m, coverage=0.3)
    f_elec = electrical_resonance_hz(L, C)
    return {"structural_f01_hz": f_struct,
            "electrical_f_lc_hz": f_elec,
            "ratio": f_elec / f_struct,
            "separated": f_elec / f_struct > 100.0,
            "note": "structural (kHz plate modes) and electrical "
                    "(MHz LC) resonances are DISTINCT families; "
                    "conflating them is a registered error"}


def design_for_target(target_hz: float, t_sub_m=1.6e-3,
                      t_cu_m=35e-6, coverage=0.5) -> dict:
    """S023: choose the disk radius so f_01 hits a selected kHz
    target (closed-form: R = lam01 * (D/rho h)^(1/4) / sqrt(2 pi f))."""
    plate0 = composite_plate(0.05, t_sub_m, t_cu_m, coverage)
    lam = clamped_plate_lambdas(0, 1)[0]
    R = math.sqrt(lam ** 2 / (2 * math.pi * target_hz)
                  * math.sqrt(plate0["d_n_m"]
                              / plate0["rho_h_kg_m2"]))
    achieved = plate_mode_hz(
        composite_plate(R, t_sub_m, t_cu_m, coverage), 0, 1)
    return {"target_hz": target_hz, "radius_m": R,
            "achieved_hz": achieved}


# --- controls + fabrication (S016-S021, S024) --------------------------------

def control_set(radius_m: float) -> list[dict]:
    return [
        {"id": "S016", "kind": "plain_disk", "radius_m": radius_m},
        {"id": "S017", "kind": "simple_cone", "radius_m": radius_m},
        {"id": "S018", "kind": "flat_log_spiral",
         "radius_m": radius_m},
        {"id": "S019", "kind": "archimedean_spiral",
         "radius_m": radius_m},
        {"id": "S020", "kind": "mass_matched_blank",
         "radius_m": radius_m,
         "note": "same rho*h, no pattern"},
        {"id": "S021", "kind": "material_controls",
         "materials": ["printed polymer", "glass", "copper",
                       "quartz-like"]},
    ]


def gerber_spiral_text(n_turns: int, d_out_mm: float,
                       d_in_mm: float, trace_mm: float = 0.5,
                       n_seg: int = 720) -> str:
    """Minimal RS-274X Gerber: one spiral copper trace as stroked
    draws (linear interpolation segments)."""
    hdr = ["%FSLAX46Y46*%", "%MOMM*%",
           f"%ADD10C,{trace_mm:.3f}*%", "D10*", "G01*"]
    body = []
    r0, r1 = d_out_mm / 2, d_in_mm / 2
    for i in range(n_seg + 1):
        t = i / n_seg
        th = 2 * math.pi * n_turns * t
        r = r0 + (r1 - r0) * t
        x = int(round(r * math.cos(th) * 1e6))
        y = int(round(r * math.sin(th) * 1e6))
        code = "D02*" if i == 0 else "D01*"
        body.append(f"X{x}Y{y}{code}")
    return "\n".join(hdr + body + ["M02*"]) + "\n"


def drill_text(holes_mm: list) -> str:
    """Minimal Excellon drill file."""
    lines = ["M48", "METRIC,TZ", "T1C1.000", "%", "T1"]
    for x, y in holes_mm:
        lines.append(f"X{x:.3f}Y{y:.3f}")
    lines.append("M30")
    return "\n".join(lines) + "\n"


def bom() -> list[dict]:
    return [{"item": "FR4 disk PCB, 100 mm, 1.6 mm, 1 oz copper",
             "qty": 5, "role": "cymatic disks + controls"},
            {"item": "plain FR4 blank (S016/S020)", "qty": 2,
             "role": "controls"},
            {"item": "piezo disk driver 27 mm", "qty": 2,
             "role": "excitation"},
            {"item": "fine sand / semolina", "qty": 1,
             "role": "Chladni visualization"},
            {"item": "nonmetal standoffs", "qty": 8,
             "role": "mounting (E019 jig)"}]


_MOTIFS = [
    ("S012", "clamped circular plate eigenvalues (Bessel roots)",
     "clamped_plate_lambdas", "EST"),
    ("S013", "composite FR4+copper plate stiffness",
     "composite_plate", "DER"),
    ("S014", "plate mode frequencies f_nm", "plate_mode_hz", "DER"),
    ("S015", "Chladni mode-shape pattern", "chladni_pattern", "DER"),
    ("S016", "plain-disk control", "control_set", "ENG"),
    ("S017", "simple-cone control", "control_set", "ENG"),
    ("S018", "flat log-spiral control", "control_set", "ENG"),
    ("S019", "Archimedean-spiral control", "control_set", "ENG"),
    ("S020", "mass-matched blank control", "control_set", "ENG"),
    ("S021", "material controls", "control_set", "ENG"),
    ("S022", "spiral inductance and disk capacitance (Mohan)",
     "spiral_inductance_h,disk_capacitance_f", "EST"),
    ("S023", "design for target frequency", "design_for_target",
     "ENG"),
    ("S024", "Gerber/drill/BOM fabrication export",
     "gerber_spiral_text,drill_text,bom", "ENG"),
]


def motif_registry() -> dict:
    """S012-S024 coverage declaration (gate G42)."""
    from .research_records import make_record
    out = {}
    for rid, title, fn, tag in _MOTIFS:
        out[rid] = make_record(
            "GeometryMotifRecord", rid, title, "geometry",
            "ENGINEERING_PROTOTYPE" if tag == "ENG"
            else "REDUCED_ORDER_VALIDATED", [tag],
            implementation=f"rscs2_core/cymatic_disk.py::{fn}")
    return out
