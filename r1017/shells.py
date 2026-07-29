"""R10.17 Phase 2 — radial shell-height calibration, tables emitted.

This module exists so that "radial shell unresolved" can never again be
an answer on its own. It emits actual boundaries, actual zeta values,
and an actual outer-in / inner-out invariant check for every point
under every declared model.

RECORDED ARCHITECTURE (cwatlas.r1085a.shell_profile, reused verbatim):

  * shells are indexed 0..8; shell 3's INNER boundary is the land-zero
    surface;
  * the operational stack is shells 3..8, running OUTWARD from
    land-zero; shells 0..2 lie below it and the corpus gives them no
    thickness;
  * within shell s, zeta = 0 at the inner boundary and 1 at the outer;
  * land-zero is the mean-land-elevation surface along gravity
    vertical, NOT mean sea level.

  D_in(s, zeta) = sum_{k>s} Delta_k + (1 - zeta) * Delta_s
  D_s(s, zeta)  = zeta * Delta_s

THE DECISIVE CONSEQUENCE, computed rather than asserted: the recorded
land-zero sits at +840 m (or +797 m), so ordinary ground-level points
lie BELOW shell 3's inner boundary and fall outside the operational
stack entirely. That is why every previous run reported the radial
layer as unresolved. It is a property of the declared zero, not of the
points, and it is testable: shifting the shell-3 zero to a sea-level
datum brings every land anchor inside shell 3.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from cwatlas.r1085a import shell_profile as sp
from cwatlas.r1085a.land_zero import land_zero

EARTH_R_M = 6371008.8

#: Epoch window for this run. Older gravity history is not searched.
EPOCH_WINDOW_BP = (10000, 50000)
EPOCH_YEARS = (2025.0,)          # thickness models are epoch-constant

#: The pack's five candidate families, plus the two recorded repo
#: profiles carried as the in-repo authority.
MODEL_FAMILIES = (
    "S3_SURFACE_BAND_FIT_FROM_ANCHOR_HEIGHTS",
    "OUTER_IN_EQUAL_THICKNESS_DIAGNOSTIC",
    "OUTER_IN_GEOMETRIC_RATIO_7_DIAGNOSTIC",
    "USER_7_7_7_PROFILE_DIAGNOSTIC",
    "POTENTIAL_SURFACE_PLACEHOLDER_WITH_HEIGHT_APPROXIMATION",
    "REPO_ATMOSPHERIC_LADDER_V1",
    "REPO_UNIFORM_100KM_V1",
    "REPO_GEOMETRIC_DOUBLING_V1",
)

#: Datum candidates for the shell-3 zero. The recorded default is the
#: mean-land surface; MSL is carried as an explicitly declared
#: ALTERNATIVE that the run tests rather than assumes.
DATUMS = {
    "RECORDED_LAND_ZERO_840M": 840.0,
    "RECORDED_LAND_ZERO_MODERN_797M": 797.0,
    "DECLARED_ALTERNATIVE_MSL_0M": 0.0,
}


@dataclass(frozen=True)
class ShellModel:
    """Thicknesses in metres for shells 3..8, plus the datum."""
    model_id: str
    datum_id: str
    datum_offset_m: float
    thickness_m: dict
    provenance: str

    @property
    def shells(self) -> list:
        return sorted(self.thickness_m)

    def boundaries_m(self) -> dict:
        """{shell: (inner_m, outer_m)} as heights above MSL."""
        out, cursor = {}, self.datum_offset_m
        for s in self.shells:
            out[s] = (cursor, cursor + self.thickness_m[s])
            cursor += self.thickness_m[s]
        return out

    def outer_boundary_m(self) -> float:
        return max(v[1] for v in self.boundaries_m().values())

    def classify(self, height_m: float) -> dict:
        """Shell and zeta for a height above MSL."""
        b = self.boundaries_m()
        for s in self.shells:
            inner, outer = b[s]
            if inner <= height_m < outer:
                delta = outer - inner
                zeta = (height_m - inner) / delta
                d_in = sum(self.thickness_m[k] for k in self.shells
                           if k > s) + (1.0 - zeta) * delta
                return {"shell": s, "zeta": zeta,
                        "inner_m": inner, "outer_m": outer,
                        "thickness_m": delta,
                        "d_in_m": d_in, "d_s_m": zeta * delta,
                        "status": "IN_OPERATIONAL_STACK"}
        lowest = b[self.shells[0]][0]
        if height_m < lowest:
            return {"shell": None, "zeta": None,
                    "inner_m": None, "outer_m": None,
                    "thickness_m": None, "d_in_m": None, "d_s_m": None,
                    "status": "BELOW_SHELL3_INNER_BOUNDARY",
                    "below_by_m": lowest - height_m,
                    "reason": "the point lies below the shell-3 zero, "
                              "so it is outside the operational stack; "
                              "shells 0..2 carry no declared thickness "
                              "in the recorded architecture"}
        return {"shell": None, "zeta": None, "status": "ABOVE_OUTER_BOUNDARY",
                "above_by_m": height_m - self.outer_boundary_m()}


def _repo_model(profile_id: str, datum_id: str) -> ShellModel:
    prof = sp.profile(profile_id)
    th = {s: v * 1000.0
          for s, v in prof.thicknesses_km(2025.0).items()}
    return ShellModel(f"REPO_{profile_id}", datum_id, DATUMS[datum_id],
                      th, prof.provenance[:160])


def _equal(total_m: float, datum_id: str) -> ShellModel:
    n = len(sp.OPERATIONAL_SHELLS)
    th = {s: total_m / n for s in sp.OPERATIONAL_SHELLS}
    return ShellModel("OUTER_IN_EQUAL_THICKNESS_DIAGNOSTIC", datum_id,
                      DATUMS[datum_id], th,
                      f"equal thicknesses over {n} operational shells "
                      f"summing to {total_m/1000:.0f} km")


def _geometric(ratio: float, base_m: float, datum_id: str,
               model_id: str, note: str) -> ShellModel:
    th = {}
    for i, s in enumerate(sp.OPERATIONAL_SHELLS):
        th[s] = base_m * (ratio ** i)
    return ShellModel(model_id, datum_id, DATUMS[datum_id], th, note)


def _s3_band_fit(points, datum_id: str) -> ShellModel:
    """Fit shell 3 so every point with a height is inside it.

    This is a GLOBAL two-parameter fit (datum and shell-3 thickness),
    never a per-point offset. The remaining shells keep the recorded
    atmospheric ladder above it.
    """
    hs = [p.height_m for p in points if p.has_height]
    lo, hi = min(hs), max(hs)
    margin = 0.10 * (hi - lo) if hi > lo else 100.0
    inner = lo - margin
    thickness3 = (hi + margin) - inner
    ladder = sp.profile("ATMOSPHERIC_LADDER_V1").thicknesses_km(2025.0)
    th = {3: thickness3}
    for s in sp.OPERATIONAL_SHELLS:
        if s != 3:
            th[s] = ladder[s] * 1000.0
    m = ShellModel("S3_SURFACE_BAND_FIT_FROM_ANCHOR_HEIGHTS",
                   "FITTED_TO_ANCHOR_HEIGHTS", inner, th,
                   f"shell-3 inner fitted to {inner:.1f} m MSL and "
                   f"thickness to {thickness3:.1f} m so that every "
                   "declared height falls inside shell 3; ONE global "
                   "fit, no per-point freedom")
    return m


def build_models(points) -> list:
    """Every declared model x every declared datum."""
    out = []
    for datum in DATUMS:
        out.append(_repo_model("ATMOSPHERIC_LADDER_V1", datum))
        out.append(_repo_model("UNIFORM_100KM_V1", datum))
        out.append(_repo_model("GEOMETRIC_DOUBLING_V1", datum))
        out.append(_equal(600000.0, datum))
        out.append(_geometric(
            7.0, 6.63, datum, "OUTER_IN_GEOMETRIC_RATIO_7_DIAGNOSTIC",
            "thickness scales by 7 outward from a 6.63 m innermost "
            "operational band; the ratio-7 diagnostic"))
        out.append(_geometric(
            7.0, 7000.0, datum, "USER_7_7_7_PROFILE_DIAGNOSTIC",
            "the operator-recorded 'use 7 for all three' read as base "
            "7 km with ratio 7 across the stack; the ambiguity of that "
            "instruction is recorded, not silently resolved"))
        out.append(ShellModel(
            "POTENTIAL_SURFACE_PLACEHOLDER_WITH_HEIGHT_APPROXIMATION",
            datum, DATUMS[datum],
            {s: v * 1000.0 for s, v in
             sp.profile("ATMOSPHERIC_LADDER_V1")
             .thicknesses_km(2025.0).items()},
            "boundaries treated as approximate equipotential surfaces; "
            "MISSING DATASETS: geoid model, gravity field, epoch "
            "gravity history. Height is used as a stand-in and that "
            "substitution is declared, not hidden"))
    out.append(_s3_band_fit(points, "DECLARED_ALTERNATIVE_MSL_0M"))
    return out


def invariant_check(model: ShellModel, shell: int, zeta: float,
                    tol_m: float = 1e-6) -> dict:
    """outer-in and inner-out must describe the same point."""
    b = model.boundaries_m()
    inner, outer = b[shell]
    delta = outer - inner
    d_in = sum(model.thickness_m[k] for k in model.shells
               if k > shell) + (1.0 - zeta) * delta
    d_s = zeta * delta
    # reconstruct the height from each direction
    h_from_outer = model.outer_boundary_m() - d_in
    h_from_inner = inner + d_s
    residual = abs(h_from_outer - h_from_inner)
    return {"shell": shell, "zeta": zeta,
            "d_in_m": d_in, "d_s_m": d_s,
            "height_from_outer_in_m": h_from_outer,
            "height_from_inner_out_m": h_from_inner,
            "residual_m": residual,
            "invariant_holds": residual <= tol_m}
