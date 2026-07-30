"""R10.15 Phases B08, B09, B12 — exact angular mask spectra.

For N cells at angles phi_j = 2*pi*j/N and active set A, with per-cell
complex weight w_j, the angular Fourier coefficient is

    M_m = (1/N) sum_{j in A} w_j exp(-i m phi_j).

Everything here is EXACT arithmetic, not an approximation: the
two-gap closed form, the Parseval identity, the rectangular-aperture
shape factor, and the symmetry classification are all derived
consequences (ClaimClass.DERIVED).

Physical significance of the low harmonics, which the study layer
relies on: for a body inside an axisymmetric domain, only m = 0 can
produce a net AXIAL force and only m = +-1 can produce a net LATERAL
force. All higher harmonics integrate to zero net force (they produce
internal stress and torque structure instead). That orthogonality is
what makes the m=1 amplitude the decisive number for this device.
"""

from __future__ import annotations

import cmath
import math

from rgcs_surface_wave.evidence import ClaimClass
from rgcs_surface_wave.geometry import AnnularGeometry


class MaskError(ValueError):
    pass


def coefficient(cells: int, active: list | tuple, m: int,
                weights: dict | None = None) -> complex:
    """Exact M_m for an arbitrary active set and optional weights."""
    if cells < 1:
        raise MaskError("cells must be >= 1")
    acc = 0j
    for j in active:
        if not (0 <= j < cells):
            raise MaskError(f"active index {j} outside 0..{cells - 1}")
        w = 1.0 if weights is None else weights.get(j, 1.0)
        acc += w * cmath.exp(-1j * m * 2.0 * math.pi * j / cells)
    return acc / cells


def two_gap_closed_form(cells: int, g1: int, g2: int, m: int) -> complex:
    """Closed form for the all-active-except-two mask.

    M_m = delta(m mod N == 0) - (1/N)(exp(-i m phi_g1)
                                     + exp(-i m phi_g2)).
    """
    if g1 == g2:
        raise MaskError("the two omitted indices must differ")
    full = 1.0 + 0j if m % cells == 0 else 0j
    gaps = (cmath.exp(-1j * m * 2.0 * math.pi * g1 / cells)
            + cmath.exp(-1j * m * 2.0 * math.pi * g2 / cells)) / cells
    return full - gaps


def aperture_shape_factor(m: int, angular_width_rad: float) -> float:
    """EXACT factor for a rectangular cell of finite angular width.

    (1/dphi) * integral_{-dphi/2}^{+dphi/2} exp(-i m psi) dpsi
        = sin(m dphi / 2) / (m dphi / 2).

    This is an exact integral for a rect aperture, not a small-angle
    approximation. It is real and even in m, and it can change sign,
    which the study layer must not confuse with a phase reversal.
    """
    if angular_width_rad <= 0:
        raise MaskError("angular width must be positive")
    x = 0.5 * m * angular_width_rad
    return 1.0 if x == 0 else math.sin(x) / x


def radial_shape_factor(inner_m: float, outer_m: float,
                        profile: str = "uniform") -> float:
    """Radial weighting integral normalised to the uniform case.

    Declared profiles only; an unknown profile refuses rather than
    silently defaulting.
    """
    if not (0 < inner_m < outer_m):
        raise MaskError("require 0 < inner < outer")
    if profile == "uniform":
        return 1.0
    if profile == "linear_outward":
        # weight proportional to r, normalised by the uniform integral
        num = (outer_m ** 3 - inner_m ** 3) / 3.0
        den = ((outer_m ** 2 - inner_m ** 2) / 2.0) \
            * 0.5 * (inner_m + outer_m)
        return num / den
    if profile == "edge_concentrated":
        # all weight at the two rims (thin-annulus limit)
        return 0.5 * (inner_m + outer_m) * (outer_m - inner_m) \
            / ((outer_m ** 2 - inner_m ** 2) / 2.0)
    raise MaskError(
        f"unknown radial profile {profile!r}; declared profiles are "
        "uniform, linear_outward, edge_concentrated")


def spectrum(cells: int, active: list | tuple, m_max: int = 40,
             angular_width_rad: float | None = None,
             weights: dict | None = None) -> dict:
    """Full spectrum with Parseval residual and symmetry class."""
    active = tuple(active)
    coeffs = {}
    for m in range(-m_max, m_max + 1):
        c = coefficient(cells, active, m, weights)
        if angular_width_rad is not None:
            c *= aperture_shape_factor(m, angular_width_rad)
        coeffs[m] = c
    # Parseval over exactly one period m = 0..N-1 (point-sampled mask):
    #   sum |M_m|^2 = (1/N) sum_j |w_j|^2
    period = [coefficient(cells, active, m, weights)
              for m in range(cells)]
    lhs = sum(abs(c) ** 2 for c in period)
    rhs = sum((1.0 if weights is None else abs(weights.get(j, 1.0)) ** 2)
              for j in active) / cells
    return {
        "schema": "rgcs.r1015.mask-spectrum.v1",
        "cells": cells, "active_count": len(active),
        "omitted": [j for j in range(cells) if j not in set(active)],
        "coefficients": {str(m): [c.real, c.imag]
                         for m, c in coeffs.items()},
        "magnitude": {str(m): abs(c) for m, c in coeffs.items()},
        "phase_rad": {str(m): cmath.phase(c) for m, c in coeffs.items()},
        "m0": abs(coeffs[0]), "m1": abs(coeffs[1]),
        "parseval_lhs": lhs, "parseval_rhs": rhs,
        "parseval_residual": abs(lhs - rhs),
        "aperture_shape_applied": angular_width_rad is not None,
        "symmetry": symmetry_class(cells, active),
        "net_force_harmonics": {
            "axial_from": "m = 0 only",
            "lateral_from": "m = +-1 only",
            "note": "higher harmonics integrate to zero NET force on a "
                    "body in an axisymmetric domain"},
        "claim_class": ClaimClass.DERIVED.value,
    }


def symmetry_class(cells: int, active: list | tuple) -> dict:
    """Rotational and reflection symmetry of the active set."""
    A = set(active)
    rots = [k for k in range(1, cells)
            if {(j + k) % cells for j in A} == A]
    cyclic_order = cells // min(rots) if rots else 1
    mirrors = [s for s in range(cells)
               if {(s - j) % cells for j in A} == A]
    return {"rotational_invariances": rots,
            "cyclic_order": cyclic_order,
            "mirror_axes": len(mirrors),
            "class": ("full_rotational" if len(A) == cells else
                      ("C%d" % cyclic_order if cyclic_order > 1 else
                       ("Cs" if mirrors else "C1")))}


def expected_mode_couplings(cells: int, active: list | tuple,
                            base_m: int = 0, m_max: int = 6,
                            threshold: float = 1e-12) -> list:
    """Which annular modes the mask can couple to, by harmonic."""
    out = []
    for m in range(-m_max, m_max + 1):
        c = coefficient(cells, active, m)
        if abs(c) > threshold:
            out.append({"harmonic": m, "target_mode": base_m + m,
                        "amplitude": abs(c),
                        "can_produce_net_force": m in (-1, 0, 1)})
    return out


# ------------------------------------------------------- Phase B12
def null_library(cells: int = 35) -> dict:
    """Control masks. Every candidate must be reported beside these."""
    all_active = tuple(range(cells))
    near = cells // 2                       # nearest-diametric offset
    lib = {
        "all_active": {
            "omitted": [], "active": all_active,
            "role": "control: perfectly symmetric, all net-force "
                    "harmonics vanish except m=0"},
        "adjacent_gaps": {
            "omitted": [0, 1], "active": tuple(j for j in range(cells)
                                               if j not in (0, 1)),
            "role": "control: maximal m=1 asymmetry for a two-gap mask"},
        "nearest_diametric_gaps": {
            "omitted": [0, near], "active": tuple(j for j in range(cells)
                                                  if j not in (0, near)),
            "role": "control: minimal m=1 asymmetry reachable with two "
                    "gaps on an odd cell count"},
        "symmetric_gaps": {
            "omitted": [0, cells // 3],
            "active": tuple(j for j in range(cells)
                            if j not in (0, cells // 3)),
            "role": "control: intermediate separation"},
        "randomized_gaps": {
            "omitted": [7, 22],             # fixed seed-free choice
            "active": tuple(j for j in range(cells)
                            if j not in (7, 22)),
            "role": "control: arbitrary separation, no candidate status"},
        "unpatterned_annulus": {
            "omitted": [], "active": all_active, "continuum": True,
            "role": "control: no angular patterning at all; the "
                    "continuum limit of all_active"},
    }
    for name, entry in lib.items():
        sp = spectrum(cells, entry["active"], m_max=3)
        entry["m0"] = sp["m0"]
        entry["m1"] = sp["m1"]
        entry["parseval_residual"] = sp["parseval_residual"]
    if cells % 2:
        lib["exact_diametric_gaps"] = {
            "status": "IMPOSSIBLE",
            "reason": f"cells={cells} is odd, so no pair of indices is "
                      "separated by exactly pi; the nearest available "
                      "separation is used instead and is reported as "
                      "nearest_diametric_gaps",
            "claim_class": ClaimClass.NULL.value}
    return {"schema": "rgcs.r1015.null-library.v1", "cells": cells,
            "masks": lib, "claim_class": ClaimClass.DERIVED.value}


def analyze(geo: AnnularGeometry, m_max: int = 40,
            use_finite_aperture: bool = True) -> dict:
    """Phase B08/B09 entry point for a geometry record."""
    width = geo.pitch_rad if use_finite_aperture else None
    sp = spectrum(geo.cells, geo.active_cells, m_max, width)
    sp["geometry"] = geo.record()
    sp["radial_shape_uniform"] = radial_shape_factor(
        geo.inner_radius_m, geo.outer_radius_m, "uniform")
    sp["comparison_to_nulls"] = {
        name: {"m1": e.get("m1"), "role": e.get("role")}
        for name, e in null_library(geo.cells)["masks"].items()
        if "m1" in e}
    return sp
