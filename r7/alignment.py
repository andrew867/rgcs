"""P04 — crystal axis and interferometric alignment.

The source claims the crystal's body axis, the local gravity axis and
the crystallographic C-axis should all coincide: the prism stands
"perpendicular to the planet's surface, in alignment with the planet's
center core".

That sentence contains three separate axes and two separate errors.

The three axes are genuinely distinct objects. :class:`Axis` models
each with its own frame and its own angular uncertainty, and they
coincide **only if the crystal was cut and mounted so they do**. A
natural quartz prism's morphological long axis lies near the c-axis but
not on it; the cut introduces a tolerance, the mount introduces
another, and the plumb line introduces a third.

The two errors are:

1. The c-axis cannot be read off the prism's external shape. Brazil and
   Dauphine twinning reorder the external faces without moving the
   lattice, and regrowth and etch distort faces further. Only
   diffraction (Laue back-reflection, XRD) finds the c-axis directly;
   conoscopy finds the optic axis, which coincides with c in quartz but
   at ~0.5 degree resolution. :func:`refuse_c_axis_from_morphology`
   raises rather than guessing.
2. "Toward the planet's centre" and "plumb" are different directions.
   The geodetic-to-geocentric difference reaches ~0.19 degree — about
   690 arcsec — which is roughly 690 times an autocollimator's
   resolution. See :func:`earth_axis_note`.

Nothing here is bench data. No crystal has been cut, aligned, mounted
or measured by this programme. Every instrument resolution quoted is a
literature or manufacturer-catalogue class figure for the instrument
type, not a calibration of equipment this project owns.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import ClassVar

#: Declared reference frames. An axis without a frame is not an axis,
#: it is three numbers.
FRAMES = (
    "CRYSTAL_LATTICE",
    "SPECIMEN_BODY",
    "MOUNT",
    "LOCAL_LEVEL",
    "GEOCENTRIC",
    "INSTRUMENT",
)

#: The kinds of axis this module distinguishes. They are separate
#: objects precisely because they are separately determined.
AXIS_KINDS = ("BODY", "GRAVITY", "C_AXIS")

#: WGS84 reciprocal flattening — a defining geodetic constant, not a
#: measurement made here.
WGS84_INVERSE_FLATTENING = 298.257_223_563
WGS84_FLATTENING = 1.0 / WGS84_INVERSE_FLATTENING

ARCSEC_PER_RAD = 180.0 * 3600.0 / math.pi
ARCMIN_PER_RAD = 180.0 * 60.0 / math.pi
DEG_PER_RAD = 180.0 / math.pi


def arcsec(rad: float) -> float:
    """Radians to arcseconds."""
    return rad * ARCSEC_PER_RAD


def from_arcsec(a: float) -> float:
    """Arcseconds to radians."""
    return a / ARCSEC_PER_RAD


def from_deg(d: float) -> float:
    """Degrees to radians."""
    return d / DEG_PER_RAD


class AlignmentRefused(RuntimeError):
    """Raised when an alignment determination is refused."""


# --------------------------------------------------------------------
# The axis object
# --------------------------------------------------------------------

@dataclass(frozen=True)
class Axis:
    """A unit 3-vector with a declared frame and angular uncertainty.

    ``sigma_rad`` is the half-angle of the cone the true direction is
    believed to lie in. An axis carrying no uncertainty is a claim, not
    a measurement, so the field is mandatory and must be non-negative.

    Construction validates normalization. The zero vector is rejected
    outright: it has no direction, and silently normalizing it would
    invent one.
    """

    x: float
    y: float
    z: float
    frame: str
    sigma_rad: float
    kind: str = "BODY"
    label: str = ""
    #: How this direction was obtained. ``None`` means "declared", which
    #: is deliberately distinguishable from "measured".
    method: str | None = None

    #: Tolerance on |v| = 1 at construction. A class constant, not a
    #: field: a per-instance tolerance would let a caller widen it.
    NORM_TOL: ClassVar[float] = 1e-9

    def __post_init__(self) -> None:
        if self.frame not in FRAMES:
            raise ValueError(f"unknown frame {self.frame!r}")
        if self.kind not in AXIS_KINDS:
            raise ValueError(f"unknown axis kind {self.kind!r}")
        if self.sigma_rad < 0.0:
            raise ValueError("angular uncertainty must be non-negative")
        n = self.norm
        if n == 0.0:
            raise ValueError(
                "the zero vector has no direction; an Axis cannot be "
                "constructed from it. Normalizing it would invent a "
                "direction that was never measured.")
        if abs(n - 1.0) > self.NORM_TOL:
            raise ValueError(
                f"axis is not a unit vector (|v| = {n!r}); use "
                f"Axis.unit(...) if normalization is intended")

    # -- geometry ----------------------------------------------------

    @property
    def norm(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y
                         + self.z * self.z)

    @property
    def components(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)

    @classmethod
    def unit(cls, x: float, y: float, z: float, frame: str,
             sigma_rad: float, kind: str = "BODY", label: str = "",
             method: str | None = None) -> "Axis":
        """Normalize explicitly. Still rejects the zero vector."""
        n = math.sqrt(x * x + y * y + z * z)
        if n == 0.0:
            raise ValueError(
                "the zero vector has no direction; refusing to "
                "normalize it")
        return cls(x / n, y / n, z / n, frame, sigma_rad, kind, label,
                   method)

    def dot(self, other: "Axis") -> float:
        return (self.x * other.x + self.y * other.y + self.z * other.z)

    def angle_to(self, other: "Axis") -> float:
        """Unsigned angle in radians between two axes.

        Frames are *not* silently reconciled. If the two axes are
        declared in different frames the angle is still computed, but
        the caller is told through :meth:`separation_record` that the
        number rests on an undeclared transform.
        """
        d = max(-1.0, min(1.0, self.dot(other)))
        return math.acos(d)

    def separation_record(self, other: "Axis") -> dict:
        """Angle between two axes with its combined uncertainty."""
        theta = self.angle_to(other)
        combined = math.sqrt(self.sigma_rad ** 2 + other.sigma_rad ** 2)
        same_frame = self.frame == other.frame
        return {
            "axis_a": self.label or self.kind,
            "axis_b": other.label or other.kind,
            "frame_a": self.frame,
            "frame_b": other.frame,
            "same_frame": same_frame,
            "separation_rad": theta,
            "separation_arcsec": arcsec(theta),
            "combined_sigma_rad": combined,
            "combined_sigma_arcsec": arcsec(combined),
            "resolvable": theta > combined,
            "note": (
                "the two axes are declared in different frames; this "
                "angle assumes an identity transform that has not been "
                "measured" if not same_frame else
                "both axes are declared in the same frame"),
            "units": "radians unless the key says arcsec",
            "evidence_class": "DERIVED_ARITHMETIC",
        }

    def as_record(self) -> dict:
        d = asdict(self)
        d.pop("NORM_TOL", None)
        d["sigma_arcsec"] = arcsec(self.sigma_rad)
        d["units"] = "dimensionless components; sigma in radians"
        d["evidence_class"] = "SYNTHETIC_MODEL"
        return d


# --------------------------------------------------------------------
# Alignment methods — literature / catalogue class resolutions
# --------------------------------------------------------------------

#: Angular resolutions are class figures for the *instrument type*,
#: drawn from manufacturer catalogues and standard metrology texts.
#: They are not calibrations of any device this programme owns, and no
#: measurement has been taken with any of them.
ALIGNMENT_METHODS: dict[str, dict] = {
    "AUTOCOLLIMATOR": {
        "resolution_rad": from_arcsec(1.0),
        "resolution_arcsec": 1.0,
        "finds": ("BODY",),
        "direct_c_axis": False,
        "measures": "angular deviation of a reflecting surface",
        "note": ("electronic autocollimator, catalogue-class ~0.1-1 "
                 "arcsec resolution against a polished flat. It "
                 "measures the FACE it is pointed at, so it reports the "
                 "body/mount orientation and knows nothing about the "
                 "lattice underneath."),
        "source_class": "MANUFACTURER_CATALOGUE_CLASS",
    },
    "LASER_INTERFEROMETRY": {
        "resolution_rad": from_arcsec(0.1),
        "resolution_arcsec": 0.1,
        "finds": ("BODY",),
        "direct_c_axis": False,
        "measures": "displacement and optical path difference",
        "note": ("Michelson fringe counting resolves sub-nanometre "
                 "displacement, giving sub-arcsec angle over a "
                 "reasonable lever arm on a flat. Per core/04: "
                 "interferometry measures displacement and optical "
                 "path, and does NOT replace crystallographic "
                 "determination of the C-axis."),
        "source_class": "LITERATURE_CLASS",
    },
    "XRD_LAUE_BACK_REFLECTION": {
        "resolution_rad": from_deg(0.01),
        "resolution_arcsec": from_deg(0.01) * ARCSEC_PER_RAD,
        "finds": ("C_AXIS",),
        "direct_c_axis": True,
        "measures": "diffraction from the lattice planes themselves",
        "note": ("Laue back-reflection / X-ray goniometry, typical "
                 "~0.01 degree on a routine orientation. This is the "
                 "ONLY method in this registry that interrogates the "
                 "lattice directly, which is why it is the only one "
                 "that can settle the c-axis. It also reveals twinning "
                 "instead of being fooled by it."),
        "source_class": "LITERATURE_CLASS",
    },
    "CONOSCOPIC_INTERFERENCE_FIGURE": {
        "resolution_rad": from_deg(0.5),
        "resolution_arcsec": from_deg(0.5) * ARCSEC_PER_RAD,
        "finds": ("C_AXIS",),
        "direct_c_axis": False,
        "measures": "optic axis via the interference figure between "
                    "crossed polars",
        "note": ("polarizing-microscope conoscopy, ~0.5 degree class. "
                 "In quartz the optic axis coincides with the "
                 "crystallographic c-axis, so this is an OPTICAL proxy "
                 "for c rather than a lattice measurement. It is a "
                 "real determination of a physical axis; it is two "
                 "orders of magnitude coarser than Laue and it cannot "
                 "distinguish Dauphine twins, whose optical properties "
                 "are unchanged."),
        "source_class": "LITERATURE_CLASS",
    },
    "BUBBLE_LEVEL_OR_PLUMB": {
        "resolution_rad": from_deg(0.1),
        "resolution_arcsec": from_deg(0.1) * ARCSEC_PER_RAD,
        "finds": ("GRAVITY",),
        "direct_c_axis": False,
        "measures": "local gravity direction",
        "note": ("a machinist's spirit level or plumb bob, ~0.1 degree "
                 "class; a precision electronic inclinometer reaches "
                 "arcsec class. Either way this finds the PLUMB LINE, "
                 "which is not the geocentric radial: see "
                 "earth_axis_note()."),
        "source_class": "MANUFACTURER_CATALOGUE_CLASS",
    },
}


def method_registry() -> dict:
    """Every alignment method with its class-figure resolution."""
    return {
        "methods": {k: dict(v) for k, v in ALIGNMENT_METHODS.items()},
        "direct_c_axis_methods": [
            k for k, v in ALIGNMENT_METHODS.items()
            if v["direct_c_axis"]],
        "units": "resolution in radians and arcseconds",
        "provenance": (
            "every resolution is a literature or catalogue-class figure "
            "for the instrument TYPE. No instrument in this registry "
            "has been used by this programme, and no specimen has been "
            "measured."),
        "evidence_class": "SYNTHETIC_MODEL",
    }


def best_method_for(axis_kind: str) -> dict:
    """The finest-resolution method that actually finds ``axis_kind``.

    "Finds" is doing real work here. An autocollimator has a hundred
    times the angular resolution of Laue back-reflection and is still
    the wrong instrument for the c-axis, because resolution on the
    wrong quantity buys nothing.
    """
    if axis_kind not in AXIS_KINDS:
        raise ValueError(f"unknown axis kind {axis_kind!r}")
    candidates = {k: v for k, v in ALIGNMENT_METHODS.items()
                  if axis_kind in v["finds"]}
    if not candidates:
        raise AlignmentRefused(
            f"no method in the registry determines the {axis_kind} axis")
    name = min(candidates, key=lambda k: candidates[k]["resolution_rad"])
    finer = [k for k, v in ALIGNMENT_METHODS.items()
             if v["resolution_rad"] < candidates[name]["resolution_rad"]]
    return {
        "axis_kind": axis_kind,
        "method": name,
        "resolution_rad": candidates[name]["resolution_rad"],
        "resolution_arcsec": candidates[name]["resolution_arcsec"],
        "candidates": sorted(candidates),
        "finer_instruments_that_measure_something_else": sorted(finer),
        "note": candidates[name]["note"],
        "units": "radians and arcseconds",
        "evidence_class": "SYNTHETIC_MODEL",
    }


# --------------------------------------------------------------------
# The three axes, modelled as three separate objects
# --------------------------------------------------------------------

#: Default error terms, each a class figure with a stated origin. All
#: in radians.
DEFAULT_BUDGET_TERMS: dict[str, dict] = {
    "cut_tolerance_rad": {
        "value": from_deg(0.05),
        "what": "angle between the lattice c-axis and the sawn/lapped "
                "body axis of the finished specimen",
        "origin": ("commercial oriented-quartz cutting is specified in "
                   "minutes of arc; a few arcmin is ordinary and a "
                   "precision cut reaches arcsec class at cost. For a "
                   "NATURAL prism used as-found this term is not a "
                   "tolerance at all but an unknown of order degrees."),
    },
    "mounting_tolerance_rad": {
        "value": from_deg(0.1),
        "what": "angle introduced between the specimen body axis and "
                "the mount reference face by clamping, bonding or "
                "seating",
        "origin": ("machine-shop class figure for a kinematic or "
                   "clamped mount; adhesive cure shrinkage and clamp "
                   "asymmetry both contribute."),
    },
    "gravity_deflection_rad": {
        "value": from_arcsec(10.0),
        "what": "deflection of the vertical — the angle between the "
                "local plumb line and the ellipsoidal normal, from "
                "terrain and subsurface density anomalies",
        "origin": ("geodetic literature class: a few arcsec on flat "
                   "terrain, tens of arcsec to ~1 arcmin in mountains. "
                   "This is a property of the SITE and cannot be "
                   "improved by better hardware."),
    },
    "measurement_error_rad": {
        "value": from_arcsec(1.0),
        "what": "angular resolution of the instrument actually used",
        "origin": ("set from ALIGNMENT_METHODS; defaults to the "
                   "autocollimator's 1 arcsec class figure."),
    },
}


def misalignment_budget(
    *,
    cut_tolerance_rad: float | None = None,
    mounting_tolerance_rad: float | None = None,
    gravity_deflection_rad: float | None = None,
    measurement_error_rad: float | None = None,
    method: str | None = None,
) -> dict:
    """Combine the four independent error terms in quadrature.

    Quadrature is the right combination only because the four terms are
    independent: how a boule was sawn does not influence how a clamp
    seats, and neither influences the local geoid. Each term is named
    and returned separately so a reader can see which one dominates
    rather than being handed a single number to trust.

    If ``method`` is given, the measurement term is taken from that
    method's class-figure resolution.
    """
    overrides = {
        "cut_tolerance_rad": cut_tolerance_rad,
        "mounting_tolerance_rad": mounting_tolerance_rad,
        "gravity_deflection_rad": gravity_deflection_rad,
        "measurement_error_rad": measurement_error_rad,
    }
    if method is not None:
        if method not in ALIGNMENT_METHODS:
            raise ValueError(f"unknown method {method!r}")
        if overrides["measurement_error_rad"] is None:
            overrides["measurement_error_rad"] = \
                ALIGNMENT_METHODS[method]["resolution_rad"]

    terms: dict[str, dict] = {}
    for name, spec in DEFAULT_BUDGET_TERMS.items():
        v = overrides[name]
        v = spec["value"] if v is None else float(v)
        if v < 0.0:
            raise ValueError(f"{name} must be non-negative")
        terms[name] = {
            "value_rad": v,
            "value_arcsec": arcsec(v),
            "value_deg": v * DEG_PER_RAD,
            "what": spec["what"],
            "origin": spec["origin"],
            "supplied": overrides[name] is not None,
        }

    total = math.sqrt(sum(t["value_rad"] ** 2 for t in terms.values()))
    dominant = max(terms, key=lambda k: terms[k]["value_rad"])
    return {
        "terms": terms,
        "term_names": sorted(terms),
        "method": method,
        "total_rad": total,
        "total_arcsec": arcsec(total),
        "total_deg": total * DEG_PER_RAD,
        "dominant_term": dominant,
        "combination": "quadrature (root sum of squares)",
        "combination_justification": (
            "the four terms are independent: cut, mount, site geoid and "
            "instrument share no common cause, so their variances add. "
            "If any two were correlated — a single fixture that both "
            "cuts and mounts, say — they would have to be added "
            "linearly instead and the total would be larger."),
        "units": "radians, with arcsec and degree duplicates",
        "evidence_class": "DERIVED_ARITHMETIC",
    }


@dataclass(frozen=True)
class CrystalMounting:
    """Three axes that are only equal if someone made them equal.

    ``body_axis`` is the prism's geometric long axis — what a
    coordinate-measuring machine or photogrammetry reports.
    ``c_axis`` is the crystallographic optic axis, obtainable only from
    diffraction or an optical determination. ``gravity_axis`` is the
    local plumb line.

    The programme's claim is that all three coincide. This class exists
    so that the claim has to be *stated as three objects and a measured
    separation* rather than assumed by writing one vector three times.
    """

    specimen_id: str
    body_axis: Axis
    gravity_axis: Axis
    c_axis: Axis

    def __post_init__(self) -> None:
        for axis, kind in ((self.body_axis, "BODY"),
                           (self.gravity_axis, "GRAVITY"),
                           (self.c_axis, "C_AXIS")):
            if axis.kind != kind:
                raise ValueError(
                    f"axis declared as {axis.kind} supplied where "
                    f"{kind} was required")

    def coincidence_report(self) -> dict:
        """Every pairwise separation, with nothing collapsed."""
        pairs = {
            "body_to_c": self.body_axis.separation_record(self.c_axis),
            "body_to_gravity":
                self.body_axis.separation_record(self.gravity_axis),
            "c_to_gravity":
                self.c_axis.separation_record(self.gravity_axis),
        }
        worst = max(pairs, key=lambda k: pairs[k]["separation_rad"])
        c_from_lattice = (
            self.c_axis.method is not None
            and ALIGNMENT_METHODS.get(self.c_axis.method, {})
            .get("direct_c_axis", False))
        return {
            "specimen_id": self.specimen_id,
            "pairs": pairs,
            "largest_separation": worst,
            "largest_separation_rad": pairs[worst]["separation_rad"],
            "all_resolvable": all(p["resolvable"] for p in pairs.values()),
            "c_axis_method": self.c_axis.method,
            "c_axis_from_lattice_measurement": c_from_lattice,
            "caveat": (
                "the c-axis in this mounting was not obtained from a "
                "lattice measurement, so every separation involving it "
                "inherits an unbounded morphological error (see "
                "refuse_c_axis_from_morphology)"
                if not c_from_lattice else
                "the c-axis was obtained from a direct lattice method"),
            "note": ("no specimen exists; these separations are "
                     "arithmetic on declared vectors"),
            "units": "radians and arcseconds within each pair record",
            "evidence_class": "DERIVED_ARITHMETIC",
        }


def alignment_report(claimed_misalignment_rad: float,
                     *,
                     method: str = "AUTOCOLLIMATOR",
                     budget: dict | None = None) -> dict:
    """Is a claimed alignment resolvable by the method that made it?

    A claim of "aligned to within X" is meaningful only when X exceeds
    the total angular uncertainty. Below that the instrument cannot
    tell the claimed alignment from any other alignment inside the same
    cone, and the claim is not wrong so much as untested.
    """
    if claimed_misalignment_rad < 0.0:
        raise ValueError("a claimed misalignment cannot be negative")
    if method not in ALIGNMENT_METHODS:
        raise ValueError(f"unknown method {method!r}")
    b = budget if budget is not None else misalignment_budget(
        method=method)
    total = b["total_rad"]
    res = ALIGNMENT_METHODS[method]["resolution_rad"]

    resolvable = claimed_misalignment_rad > total
    if resolvable:
        verdict = (
            f"the claimed misalignment of "
            f"{arcsec(claimed_misalignment_rad):.1f} arcsec exceeds the "
            f"total uncertainty of {arcsec(total):.1f} arcsec, so the "
            f"claim is testable by this method.")
    else:
        verdict = (
            f"the claimed misalignment of "
            f"{arcsec(claimed_misalignment_rad):.1f} arcsec sits inside "
            f"the total uncertainty of {arcsec(total):.1f} arcsec, "
            f"dominated by {b['dominant_term']}. The claim is not "
            f"contradicted; it is unresolved. Improving the instrument "
            f"alone will not help unless the instrument is the "
            f"dominant term.")

    return {
        "claimed_misalignment_rad": claimed_misalignment_rad,
        "claimed_misalignment_arcsec": arcsec(claimed_misalignment_rad),
        "method": method,
        "method_resolution_rad": res,
        "method_resolution_arcsec": arcsec(res),
        "method_finds": list(ALIGNMENT_METHODS[method]["finds"]),
        "total_uncertainty_rad": total,
        "total_uncertainty_arcsec": arcsec(total),
        "dominant_term": b["dominant_term"],
        "budget_terms": b["term_names"],
        "resolvable": resolvable,
        "instrument_is_limiting": res >= total * 0.5,
        "verdict": verdict,
        "units": "radians, with arcsec duplicates",
        "evidence_class": "DERIVED_ARITHMETIC",
    }


# --------------------------------------------------------------------
# The critical refusal
# --------------------------------------------------------------------

def refuse_c_axis_from_morphology(*args, **kwargs):
    """Always refuses. External shape does not give the lattice axis.

    A quartz prism looks like it announces its c-axis: six prism faces
    running parallel to it, a termination at each end. The inference
    fails for reasons that are ordinary mineralogy, not edge cases:

    * **Dauphine twinning** — an electrical twin related by a 180
      degree rotation about the c-axis. It leaves the external
      morphology and the optical properties essentially unchanged while
      reversing the sense of the polar a-axes, so it is invisible to
      shape and invisible to conoscopy. It is revealed by etching or
      by X-ray topography.
    * **Brazil twinning** — an optical twin relating left- and
      right-handed domains. A single specimen can contain both
      handednesses, so "the crystal's" optical rotation is not a single
      well-defined property of the piece, and the external form again
      does not report the domain structure.
    * Natural faces are commonly distorted, etched, regrown or
      overgrown, and a specimen may be a fragment whose long dimension
      is a fracture direction rather than a growth direction. Prism
      faces can be absent entirely on a well-formed but atypical habit.

    The consequence is not that morphology is useless; it is that
    morphology gives a *prior*, of order degrees, and the programme's
    claim needs arcseconds. Use ``XRD_LAUE_BACK_REFLECTION`` for the
    lattice, or ``CONOSCOPIC_INTERFERENCE_FIGURE`` for a ~0.5 degree
    optical determination of the optic axis.
    """
    raise AlignmentRefused(
        "the crystallographic c-axis may not be inferred from the "
        "prism's external morphology. Brazil twinning (optical, "
        "left/right-handed domains in one specimen) and Dauphine "
        "twinning (electrical, 180 degrees about c, invisible to both "
        "shape and conoscopy) defeat morphological inference outright, "
        "and natural faces are additionally distorted, etched or "
        "regrown. Only diffraction (XRD_LAUE_BACK_REFLECTION) "
        "determines the lattice axis directly; "
        "CONOSCOPIC_INTERFERENCE_FIGURE gives the optic axis at ~0.5 "
        "degree. Interferometry measures displacement and optical path "
        "and does not replace crystallographic determination "
        "(core/04).")


def c_axis_is_the_long_axis(*args, **kwargs) -> bool:
    """Constant ``False``, kept so the answer is inspectable."""
    return False


# --------------------------------------------------------------------
# Plumb is not "toward the centre"
# --------------------------------------------------------------------

def geocentric_latitude_rad(geodetic_lat_rad: float,
                            flattening: float = WGS84_FLATTENING
                            ) -> float:
    """Geocentric latitude for a geodetic latitude on the ellipsoid.

    tan(phi_c) = (1 - f)^2 tan(phi).
    """
    return math.atan((1.0 - flattening) ** 2
                     * math.tan(geodetic_lat_rad))


def plumb_geocentric_deviation_rad(geodetic_lat_rad: float,
                                   flattening: float = WGS84_FLATTENING
                                   ) -> float:
    """Angle between the ellipsoidal normal and the geocentric radial.

    This is the "toward the centre" error, and it is a pure consequence
    of the equatorial bulge: it vanishes at the equator and at the
    poles and peaks near 45 degrees.
    """
    return abs(geodetic_lat_rad
               - geocentric_latitude_rad(geodetic_lat_rad, flattening))


def max_plumb_geocentric_deviation(flattening: float = WGS84_FLATTENING,
                                   *, samples: int = 90_001) -> dict:
    """Maximum geodetic-to-geocentric deviation, computed not quoted.

    Deterministic: a fixed uniform grid over 0 to 90 degrees, no
    randomness anywhere.
    """
    if samples < 3:
        raise ValueError("need at least three samples")
    best_lat = 0.0
    best = 0.0
    for i in range(samples):
        lat = (math.pi / 2.0) * i / (samples - 1)
        if lat >= math.pi / 2.0:
            continue
        d = plumb_geocentric_deviation_rad(lat, flattening)
        if d > best:
            best, best_lat = d, lat
    return {
        "max_deviation_rad": best,
        "max_deviation_deg": best * DEG_PER_RAD,
        "max_deviation_arcmin": best * ARCMIN_PER_RAD,
        "max_deviation_arcsec": arcsec(best),
        "at_geodetic_latitude_deg": best_lat * DEG_PER_RAD,
        "flattening": flattening,
        "samples": samples,
        "units": "radians, with degree/arcmin/arcsec duplicates",
        "evidence_class": "DERIVED_ARITHMETIC",
    }


def earth_axis_note(geodetic_lat_deg: float = 45.0) -> dict:
    """Why "in alignment with the planet's center core" is two claims.

    The source's phrase merges three directions that a geodesist keeps
    apart:

    * the **geocentric radial**, pointing at the Earth's centre of mass;
    * the **ellipsoidal normal**, perpendicular to the reference
      ellipsoid — what "perpendicular to the planet's surface" means;
    * the **plumb line**, the direction local gravity actually pulls,
      which is what any level, plumb bob or inclinometer finds.

    The first two differ by up to ~0.19 degree because the Earth is an
    oblate spheroid. The last two differ by the deflection of the
    vertical: arcseconds on flat terrain, tens of arcsec to ~1 arcmin
    near mountains or strong density contrasts.

    So a crystal set truly plumb is *not* pointing at the core, and the
    discrepancy is hundreds of times an autocollimator's resolution.
    Whichever direction the programme means, it has to say which.
    """
    lat = from_deg(geodetic_lat_deg)
    dev = plumb_geocentric_deviation_rad(lat)
    peak = max_plumb_geocentric_deviation()
    auto = ALIGNMENT_METHODS["AUTOCOLLIMATOR"]["resolution_rad"]
    defl = DEFAULT_BUDGET_TERMS["gravity_deflection_rad"]["value"]
    return {
        "geodetic_latitude_deg": geodetic_lat_deg,
        "geocentric_latitude_deg":
            geocentric_latitude_rad(lat) * DEG_PER_RAD,
        "deviation_at_latitude_rad": dev,
        "deviation_at_latitude_deg": dev * DEG_PER_RAD,
        "deviation_at_latitude_arcmin": dev * ARCMIN_PER_RAD,
        "deviation_at_latitude_arcsec": arcsec(dev),
        "max_deviation_deg": peak["max_deviation_deg"],
        "max_deviation_arcmin": peak["max_deviation_arcmin"],
        "max_deviation_arcsec": peak["max_deviation_arcsec"],
        "max_at_geodetic_latitude_deg": peak["at_geodetic_latitude_deg"],
        "deflection_of_vertical_typical_arcsec": arcsec(defl),
        "deflection_of_vertical_range": (
            "a few arcsec on flat terrain with smooth geology; tens of "
            "arcsec to about 1 arcmin in mountainous terrain or over "
            "strong subsurface density contrasts"),
        "autocollimator_resolution_arcsec": arcsec(auto),
        "ratio_max_deviation_to_autocollimator":
            peak["max_deviation_rad"] / auto,
        "plumb_is_geocentric_radial": False,
        "three_directions": [
            "GEOCENTRIC_RADIAL (toward the centre of mass)",
            "ELLIPSOIDAL_NORMAL (perpendicular to the surface)",
            "PLUMB_LINE (what a level actually finds)",
        ],
        "verdict": (
            "'perpendicular to the planet's surface' and 'in alignment "
            "with the planet's center core' are DIFFERENT directions, "
            "separated by up to "
            f"{peak['max_deviation_deg']:.3f} degree "
            f"({peak['max_deviation_arcmin']:.1f} arcmin) from the "
            "equatorial bulge alone. That is about "
            f"{peak['max_deviation_rad'] / auto:.0f} times an "
            "autocollimator's 1 arcsec resolution, so the difference is "
            "not a rounding detail — it is the largest single term in "
            "any alignment budget that fails to declare which direction "
            "is meant. Local gravity anomalies and terrain add the "
            "deflection of the vertical on top, of order arcsec to ~1 "
            "arcmin, and no instrument can remove it."),
        "consequence": (
            "the programme must pick one reference direction and name "
            "it. Until then, 'aligned to the core' has an irreducible "
            "ambiguity larger than every instrument in the registry can "
            "resolve."),
        "units": "radians, with degree/arcmin/arcsec duplicates",
        "evidence_class": "DERIVED_ARITHMETIC",
    }


# --------------------------------------------------------------------
# Headline
# --------------------------------------------------------------------

def status_report() -> dict:
    """The P04 headline, computed rather than asserted."""
    peak = max_plumb_geocentric_deviation()
    budget = misalignment_budget()
    note = earth_axis_note()
    return {
        "claim": ("the crystal body axis, the local gravity axis and "
                  "the crystallographic C-axis are one axis"),
        "axes_modelled_separately": list(AXIS_KINDS),
        "total_alignment_uncertainty_arcsec": budget["total_arcsec"],
        "total_alignment_uncertainty_deg": budget["total_deg"],
        "dominant_term": budget["dominant_term"],
        "budget_terms": budget["term_names"],
        "max_plumb_geocentric_deviation_deg":
            peak["max_deviation_deg"],
        "ratio_deviation_to_autocollimator":
            note["ratio_max_deviation_to_autocollimator"],
        "only_direct_c_axis_method": "XRD_LAUE_BACK_REFLECTION",
        "c_axis_from_morphology": "REFUSED",
        "verdict": (
            "The three axes coincide only if a specimen was cut and "
            "mounted so they do, and no specimen has been cut or "
            "mounted. The c-axis cannot be read from the prism's "
            "shape — Brazil and Dauphine twinning defeat that "
            "inference — so a diffraction measurement is mandatory "
            "before any alignment claim exists at all. Separately, "
            "'plumb' and 'toward the centre' differ by up to "
            f"{peak['max_deviation_deg']:.3f} degree, which is larger "
            "than every instrument resolution in the registry."),
        "what_would_settle_it": (
            "a Laue back-reflection orientation on the actual "
            "specimen, a coordinate-measuring body-axis determination, "
            "an inclinometer reading of the mounted plumb angle, and a "
            "declared choice between the plumb line and the geocentric "
            "radial. All four are absent."),
        "evidence_class": "DERIVED_ARITHMETIC",
    }
