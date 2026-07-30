"""R10.15A — exact Scale A geometry and the half-wave proxy.

The half-wave path is EXACT ARITHMETIC on declared inputs:

    L_eff = v_phase / (2 f N)

With v = 3800 m/s, f = 4096 Hz, N = 1 this is 475/1024 m exactly --
a dyadic rational, so it is representable exactly in binary floating
point. The longitudinal control branch (5700 m/s) gives 1425/2048 m.
Both are computed with ``fractions.Fraction`` and only converted to
float at the boundary.

EVIDENCE LABEL. The half-wave path is ``ANALYTIC_PROXY``: an exact
consequence of a SCALAR one-dimensional model applied to a
three-dimensional anisotropic body. It is not a resonance. The real
eigenmodes require the anisotropic FEM specified in ``fem_profile``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

from r1015a import DESIGN_ID, STATUS, ScaleAError

#: Declared acoustic branches. Velocities are SCALAR PROXIES for an
#: anisotropic material: quartz has direction-dependent speeds and
#: these single numbers are stand-ins until the tensor solve runs.
BRANCHES = {
    "shear_proxy": {"velocity_m_s": 3800.0, "role": "primary candidate",
                    "note": "scalar stand-in for a quasi-shear branch"},
    "longitudinal_proxy": {"velocity_m_s": 5700.0,
                           "role": "CONTROL BRANCH, not a second "
                                   "preferred answer",
                           "note": "scalar stand-in for a "
                                   "quasi-longitudinal branch"},
}

QUARTZ_DENSITY_G_CM3 = 2.65
ANGLE_MODES = ("face_slope", "apex_included", "axis_to_face")
DIAMETER_MODES = ("across_vertices", "across_flats")


def half_wave_path(velocity_m_s, frequency_hz, harmonic: int = 1):
    """Exact L_eff = v / (2 f N) as a Fraction of metres."""
    if harmonic < 1:
        raise ScaleAError("harmonic N must be a positive integer")
    if velocity_m_s <= 0 or frequency_hz <= 0:
        raise ScaleAError("velocity and frequency must be positive")
    return Fraction(velocity_m_s).limit_denominator(10 ** 12) / (
        2 * Fraction(frequency_hz).limit_denominator(10 ** 12)
        * harmonic)


def half_wave_proxy(branch: str = "shear_proxy",
                    frequency_hz: float = 4096.0,
                    harmonic: int = 1) -> dict:
    """The labelled analytic proxy output."""
    if branch not in BRANCHES:
        raise ScaleAError(
            f"unknown acoustic branch {branch!r}; declared branches are "
            f"{', '.join(BRANCHES)}")
    v = BRANCHES[branch]["velocity_m_s"]
    L = half_wave_path(v, frequency_hz, harmonic)
    return {
        "schema": "rgcs.r1015a.half-wave-proxy.v1",
        "branch": branch, "role": BRANCHES[branch]["role"],
        "velocity_m_s": v, "frequency_hz": frequency_hz,
        "harmonic": harmonic,
        "length_m_exact": [L.numerator, L.denominator],
        "length_mm": float(L) * 1000.0,
        "is_dyadic_rational": (L.denominator
                               & (L.denominator - 1)) == 0,
        "formula": "L_eff = v_phase / (2 f N)",
        "evidence_class": "ANALYTIC_PROXY",
        "is_measured_resonance": False,
        "is_final_cut_length": False,
        "limitations": [
            "scalar velocity applied to an anisotropic material",
            "one-dimensional path applied to a 3D tapered body",
            "no termination, electrode, fixture, temperature, or "
            "machining correction applied",
            "the actual eigenmodes require full anisotropic 3D FEM",
        ],
    }


@dataclass(frozen=True)
class ScaleAGeometry:
    """Six-sided Vogel-terminated body, all lengths in mm."""
    length_mm: float
    facets: int = 6
    length_to_avg_diameter: float = 6.0
    wide_to_narrow_ratio: float = 1.6
    rx_face_slope_deg: float = 51.843
    tx_face_slope_deg: float = 60.0
    angle_mode: str = "face_slope"
    diameter_mode: str = "across_vertices"
    facet_rotation_deg: float = 30.0

    def __post_init__(self):
        if not (math.isfinite(self.length_mm) and self.length_mm > 0):
            raise ScaleAError(
                f"length_mm must be positive and finite, got "
                f"{self.length_mm!r}")
        if self.facets < 3:
            raise ScaleAError(
                f"facets must be at least 3, got {self.facets!r}")
        if self.length_to_avg_diameter <= 0:
            raise ScaleAError("length_to_avg_diameter must be positive")
        if self.wide_to_narrow_ratio < 1.0:
            raise ScaleAError(
                f"wide_to_narrow_ratio must be >= 1 (the wide end "
                f"cannot be narrower than the narrow end), got "
                f"{self.wide_to_narrow_ratio!r}")
        if self.angle_mode not in ANGLE_MODES:
            raise ScaleAError(
                f"angle_mode {self.angle_mode!r} not in {ANGLE_MODES}")
        if self.diameter_mode not in DIAMETER_MODES:
            raise ScaleAError(
                f"diameter_mode {self.diameter_mode!r} not in "
                f"{DIAMETER_MODES}")
        for name, a in (("rx_face_slope_deg", self.rx_face_slope_deg),
                        ("tx_face_slope_deg", self.tx_face_slope_deg)):
            if not (0.0 < a < 90.0):
                raise ScaleAError(
                    f"{name} must lie strictly between 0 and 90 "
                    f"degrees for a face_slope convention, got {a!r}")

    # ------------------------------------------------- derived sizes
    @property
    def avg_diameter_mm(self) -> float:
        return self.length_mm / self.length_to_avg_diameter

    @property
    def narrow_diameter_mm(self) -> float:
        # avg = (wide + narrow)/2 and wide = k*narrow
        return 2.0 * self.avg_diameter_mm / (1.0 + self.wide_to_narrow_ratio)

    @property
    def wide_diameter_mm(self) -> float:
        return self.wide_to_narrow_ratio * self.narrow_diameter_mm

    def apothem_mm(self, diameter_mm: float) -> float:
        """Across-vertices diameter -> apothem of a regular polygon."""
        r = diameter_mm / 2.0
        if self.diameter_mode == "across_flats":
            return r
        return r * math.cos(math.pi / self.facets)

    def cap_height_mm(self, diameter_mm: float, angle_deg: float) -> float:
        a = self.apothem_mm(diameter_mm)
        t = math.radians(angle_deg)
        if self.angle_mode == "face_slope":
            return a * math.tan(t)
        if self.angle_mode == "axis_to_face":
            return a / math.tan(t)
        return a / math.tan(t / 2.0)          # apex_included

    @property
    def rx_cap_height_mm(self) -> float:
        return self.cap_height_mm(self.wide_diameter_mm,
                                  self.rx_face_slope_deg)

    @property
    def tx_cap_height_mm(self) -> float:
        return self.cap_height_mm(self.narrow_diameter_mm,
                                  self.tx_face_slope_deg)

    @property
    def shaft_height_mm(self) -> float:
        return (self.length_mm - self.rx_cap_height_mm
                - self.tx_cap_height_mm)

    # ------------------------------------------------------- volume
    def polygon_area_mm2(self, diameter_mm: float) -> float:
        """Regular n-gon area from the across-vertices diameter."""
        r = diameter_mm / 2.0
        if self.diameter_mode == "across_flats":
            r = r / math.cos(math.pi / self.facets)
        n = self.facets
        return 0.5 * n * r ** 2 * math.sin(2 * math.pi / n)

    @property
    def volume_mm3(self) -> float:
        """Tapered prism (conical frustum rule) plus two pyramids."""
        a_w = self.polygon_area_mm2(self.wide_diameter_mm)
        a_n = self.polygon_area_mm2(self.narrow_diameter_mm)
        shaft = (self.shaft_height_mm / 3.0) * (
            a_w + a_n + math.sqrt(a_w * a_n))
        rx = a_w * self.rx_cap_height_mm / 3.0
        tx = a_n * self.tx_cap_height_mm / 3.0
        return shaft + rx + tx

    @property
    def volume_cm3(self) -> float:
        return self.volume_mm3 / 1000.0

    def mass_g(self, density_g_cm3: float = QUARTZ_DENSITY_G_CM3
               ) -> float:
        return self.volume_cm3 * density_g_cm3

    def validate(self) -> dict:
        """Refuse geometries that cannot physically exist."""
        errors, warnings = [], []
        if self.shaft_height_mm <= 0:
            errors.append(
                f"the two terminations ({self.rx_cap_height_mm:.3f} mm "
                f"+ {self.tx_cap_height_mm:.3f} mm) consume the whole "
                f"{self.length_mm:.3f} mm body; there is no shaft left. "
                "Reduce the face slopes or increase the length.")
        if self.shaft_height_mm < 0.1 * self.length_mm and \
                self.shaft_height_mm > 0:
            warnings.append(
                "the shaft is less than 10 percent of the total "
                "length; the body is nearly all termination and the "
                "half-wave path proxy is a poor model for it")
        if self.wide_diameter_mm > self.length_mm:
            warnings.append(
                "the body is wider than it is long; a one-dimensional "
                "path model does not apply")
        return {"ok": not errors, "errors": errors,
                "warnings": warnings}

    def record(self) -> dict:
        v = self.validate()
        return {
            "schema": "rgcs.r1015a.geometry.v1",
            "design_id": DESIGN_ID, "status": STATUS,
            "length_mm": self.length_mm, "facets": self.facets,
            "length_to_average_diameter": self.length_to_avg_diameter,
            "wide_to_narrow_ratio": self.wide_to_narrow_ratio,
            "avg_diameter_mm": self.avg_diameter_mm,
            "wide_diameter_mm": self.wide_diameter_mm,
            "narrow_diameter_mm": self.narrow_diameter_mm,
            "rx_face_slope_deg": self.rx_face_slope_deg,
            "tx_face_slope_deg": self.tx_face_slope_deg,
            "rx_cap_height_mm": self.rx_cap_height_mm,
            "tx_cap_height_mm": self.tx_cap_height_mm,
            "shaft_height_mm": self.shaft_height_mm,
            "angle_mode": self.angle_mode,
            "diameter_mode": self.diameter_mode,
            "idealized_volume_cm3": self.volume_cm3,
            "idealized_mass_g_at_2p65": self.mass_g(),
            "valid": v["ok"], "errors": v["errors"],
            "warnings": v["warnings"],
            "evidence_class": "DERIVED",
            "is_fabrication_drawing": False,
        }


def scale_a_geometry(branch: str = "shear_proxy",
                     frequency_hz: float = 4096.0) -> ScaleAGeometry:
    """The frozen nominal Scale A body for a branch."""
    proxy = half_wave_proxy(branch, frequency_hz)
    return ScaleAGeometry(length_mm=proxy["length_mm"])


def physical_length_budget(effective_length_mm: float,
                           termination_mm: float | None = None,
                           electrode_mm: float | None = None,
                           fixture_mm: float | None = None,
                           temperature_mm: float | None = None,
                           machining_trim_mm: float | None = None
                           ) -> dict:
    """L_physical = L_effective + corrections.

    Every correction defaults to UNKNOWN rather than zero. Returning a
    physical length while any term is unknown would present a guess as
    a cut sheet, so the function refuses to total them.
    """
    terms = {"termination_mm": termination_mm,
             "electrode_mm": electrode_mm,
             "fixture_mm": fixture_mm,
             "temperature_mm": temperature_mm,
             "machining_trim_mm": machining_trim_mm}
    unknown = [k for k, v in terms.items() if v is None]
    out = {"schema": "rgcs.r1015a.length-budget.v1",
           "effective_length_mm": effective_length_mm,
           "corrections": terms, "unknown_terms": unknown,
           "formula": "L_physical = L_effective + termination + "
                      "electrode + fixture + temperature + machining"}
    if unknown:
        out["physical_length_mm"] = None
        out["status"] = "PHYSICAL_LENGTH_NOT_YET_SOLVED"
        out["refusal"] = (
            f"cannot total the budget: {unknown} are unknown. Returning "
            "a number here would present the effective path as a cut "
            "length. Measure or model each term first.")
    else:
        out["physical_length_mm"] = effective_length_mm + sum(
            terms.values())
        out["status"] = "ALL_TERMS_SUPPLIED"
        out["caveat"] = ("still requires a full 3D eigenmode solve and "
                         "a trim plan with irreversible-step limits "
                         "before any cut")
    return out
