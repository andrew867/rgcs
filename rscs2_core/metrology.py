"""Specimen metrology, orientation, and material registry (Agent C05;
coverage G001-G030 metrology side; gates G12, G25).

The v4.2.0 ledger pointed C05 at `harmonic_family.specimen_registry()`,
which is a REGISTRY, not a metrology pipeline. This module supplies the
pipeline the C05 prompt required: calibrated measurement records,
seller-versus-measured separation, mass/volume/density consistency,
facet and cap metrology, uncertainty propagation, an XRD orientation
INTERFACE, and scan-to-mesh import with malformed-scan handling.

NOTHING HERE IS MEASURED. No specimen has been scanned, weighed, or
XRD-oriented. Every record produced by this module is either a declared
seller value (SRC), a protocol, or a synthetic fixture. The schema
refuses to let a seller value become a measured value, and the XRD
interface refuses to infer axes from facets."""

from __future__ import annotations

import math

import numpy as np

from .research_records import make_record

MODULE_ID = "rscs2.metrology"

# Instruments the protocol declares, with the resolution each must
# demonstrate at calibration before its data may be used (C05).
REQUIRED_INSTRUMENTS = {
    "caliper": {"quantity": "length", "unit": "mm",
                "resolution": 0.01, "calibration": "gauge block"},
    "micrometer": {"quantity": "width", "unit": "mm",
                   "resolution": 0.001, "calibration": "gauge block"},
    "balance": {"quantity": "mass", "unit": "g",
                "resolution": 0.001, "calibration": "OIML class E2"},
    "goniometer": {"quantity": "facet angle", "unit": "deg",
                   "resolution": 0.1, "calibration": "optical flat"},
    "camera": {"quantity": "image scale", "unit": "px/mm",
               "resolution": 0.05, "calibration": "checkerboard"},
    "scanner": {"quantity": "surface", "unit": "mm",
                "resolution": 0.05, "calibration": "sphere artifact"},
    "xrd": {"quantity": "c-axis orientation", "unit": "deg",
            "resolution": 0.05, "calibration": "reference quartz"},
}


class MetrologyError(ValueError):
    pass


# --- seller versus measured separation ---------------------------------------

def specimen_record(specimen_id: str, seller_values: dict,
                    measured_values: dict | None = None,
                    measurement_provenance: dict | None = None) -> dict:
    """C05 core rule: seller values and measured values live in
    SEPARATE fields and are never merged. A seller value can never be
    promoted to a measurement, and a measured block is refused unless
    it carries instrument + calibration + operator + timestamp.

    The vendor '100 nm flatness' style claim stays SRC until an
    independent measurement exists (declared in the C05 prompt)."""
    if measured_values and not measurement_provenance:
        raise MetrologyError(
            "measured values require measurement_provenance "
            "(instrument, calibration_id, operator, timestamp)")
    if measurement_provenance:
        need = ("instrument", "calibration_id", "operator", "timestamp")
        missing = [k for k in need if k not in measurement_provenance]
        if missing:
            raise MetrologyError(f"provenance missing {missing}")
        inst = measurement_provenance["instrument"]
        if inst not in REQUIRED_INSTRUMENTS:
            raise MetrologyError(f"unknown instrument {inst}")
    status = "EXPERIMENTALLY_MEASURED" if measured_values else \
        "PROTOCOL_READY_HARDWARE_REQUIRED"
    tags = ["MEAS"] if measured_values else ["SRC"]
    extra = {}
    if measured_values:
        extra = {"raw_hash": measurement_provenance.get("raw_hash",
                                                        "UNSET"),
                 "instrument": measurement_provenance["instrument"],
                 "calibration_id":
                     measurement_provenance["calibration_id"],
                 "protocol_version": "C05-metrology-1",
                 "randomization": "n/a (metrology)",
                 "blinding": measurement_provenance.get("blinding",
                                                        "none"),
                 "safety_gate_id": "S01-metrology"}
    return make_record(
        "SpecimenRecord", specimen_id,
        f"specimen {specimen_id}", "geometry", status, tags,
        seller_values=dict(seller_values),
        measured_values=dict(measured_values or {}),
        measurement_provenance=dict(measurement_provenance or {}),
        rule="seller values are SRC and are never overwritten by, nor "
             "merged with, measured values (C05)",
        **extra)


def seller_vs_measured_delta(record: dict) -> dict:
    """Report the discrepancy without resolving it. A disagreement is
    information, not an error to be smoothed away."""
    s, m = record["seller_values"], record["measured_values"]
    if not m:
        return {"comparable": False,
                "reason": "no measured values exist for this specimen",
                "status": "PROTOCOL_READY_HARDWARE_REQUIRED"}
    out = {}
    for k in set(s) & set(m):
        try:
            out[k] = {"seller": float(s[k]), "measured": float(m[k]),
                      "delta": float(m[k]) - float(s[k]),
                      "relative": (float(m[k]) - float(s[k]))
                      / max(abs(float(s[k])), 1e-12)}
        except (TypeError, ValueError):
            out[k] = {"seller": s[k], "measured": m[k],
                      "delta": "non-numeric"}
    return {"comparable": True, "deltas": out,
            "note": "a seller/measured disagreement is preserved, not "
                    "reconciled by overwriting either side"}


# --- dimensional / mass / density consistency --------------------------------

def density_from_mass_volume(mass_g: float, volume_cm3: float,
                             u_mass_g: float = 0.001,
                             u_volume_cm3: float = 0.05) -> dict:
    """rho = m/V with first-order uncertainty propagation:
    (u_rho/rho)^2 = (u_m/m)^2 + (u_V/V)^2."""
    if mass_g <= 0 or volume_cm3 <= 0:
        raise MetrologyError("mass and volume must be positive")
    rho = mass_g / volume_cm3
    rel = math.sqrt((u_mass_g / mass_g) ** 2
                    + (u_volume_cm3 / volume_cm3) ** 2)
    return {"density_g_cm3": rho, "u_density_g_cm3": rho * rel,
            "relative_uncertainty": rel, "unit": "g/cm^3"}


QUARTZ_DENSITY_G_CM3 = 2.648  # alpha quartz, EST (v3 authority)


def mass_volume_consistency(mass_g: float, volume_cm3: float,
                            expected_density: float =
                            QUARTZ_DENSITY_G_CM3,
                            tolerance: float = 0.02) -> dict:
    """Adversarial check: a specimen whose implied density is far from
    alpha quartz is either mis-measured, not quartz, or heavily
    included. The check reports which, and never silently rescales."""
    d = density_from_mass_volume(mass_g, volume_cm3)
    rel = (d["density_g_cm3"] - expected_density) / expected_density
    consistent = abs(rel) <= tolerance
    if consistent:
        verdict = "CONSISTENT_WITH_QUARTZ"
    elif rel < 0:
        verdict = "LOW_DENSITY: voids/fractures, wrong volume, or " \
                  "not quartz"
    else:
        verdict = "HIGH_DENSITY: dense inclusions, wrong volume, or " \
                  "not quartz"
    return {**d, "expected_density_g_cm3": expected_density,
            "relative_deviation": rel, "consistent": bool(consistent),
            "verdict": verdict}


def dimensional_record(tip_to_tip_mm: float, widths_mm: list,
                       axial_positions_mm: list, cap_heights_mm: list,
                       facet_count: int, u_length_mm: float = 0.01
                       ) -> dict:
    """Tip-to-tip length, widths at declared axial stations, cap
    heights, facet count, with the measurement uncertainty carried."""
    if len(widths_mm) != len(axial_positions_mm):
        raise MetrologyError("widths and axial positions must pair")
    if facet_count not in (6, 8, 12, 24):
        raise MetrologyError(f"unsupported facet count {facet_count} "
                             "(C03 supports 6/8/12/24)")
    w = np.asarray(widths_mm, float)
    return {"tip_to_tip_mm": tip_to_tip_mm,
            "u_tip_to_tip_mm": u_length_mm,
            "widths_mm": w.tolist(),
            "axial_positions_mm": list(axial_positions_mm),
            "mean_width_mm": float(w.mean()),
            "taper_mm_per_mm": float(
                np.polyfit(axial_positions_mm, w, 1)[0])
            if len(w) > 1 else 0.0,
            "cap_heights_mm": list(cap_heights_mm),
            "facet_count": facet_count,
            "u_facet_angle_deg":
                REQUIRED_INSTRUMENTS["goniometer"]["resolution"]}


def apex_angle_deg(cap_height_mm: float, width_mm: float) -> dict:
    """Included apex angle from cap height and half-width:
    theta = 2*atan((w/2)/h). Reported with the propagated uncertainty
    from both inputs."""
    if cap_height_mm <= 0 or width_mm <= 0:
        raise MetrologyError("positive cap height and width required")
    half = width_mm / 2.0
    theta = 2.0 * math.degrees(math.atan(half / cap_height_mm))
    # d(theta)/d(half) and d(theta)/d(h), degrees per mm
    denom = half * half + cap_height_mm * cap_height_mm
    d_half = math.degrees(2.0 * cap_height_mm / denom)
    d_h = math.degrees(-2.0 * half / denom)
    u = math.hypot(d_half * 0.01, d_h * 0.01)
    return {"apex_angle_deg": theta, "u_apex_angle_deg": u,
            "note": "geometric apex angle; NOT a crystallographic axis"}


# --- XRD orientation interface (no fabricated orientation) -------------------

def xrd_orientation_interface(specimen_id: str,
                              scan_available: bool = False,
                              scan: dict | None = None) -> dict:
    """C05 boundary: crystallographic axes may NOT be inferred from
    visual facets. Without a real XRD scan this returns
    INTERFACE_ONLY and no orientation number.

    A facet normal is a geometric fact; a c-axis is a crystallographic
    one. Quartz can be cut at any angle to its axes, so the two are
    independent and the code refuses to conflate them."""
    if not scan_available or scan is None:
        return {"specimen_id": specimen_id,
                "classification": "INTERFACE_ONLY",
                "evidence_tags": ["ENG"],
                "c_axis_deg": None, "lateral_axis_deg": None,
                "declares": {"input": "2-theta/omega scan + reference "
                                      "quartz calibration",
                             "output": "c-axis and lateral-axis "
                                       "orientation with uncertainty"},
                "note": "no XRD data exists; orientation is NOT "
                        "computed and must NOT be inferred from facet "
                        "geometry (C05 boundary)"}
    need = ("two_theta_deg", "intensity", "calibration_id")
    missing = [k for k in need if k not in scan]
    if missing:
        raise MetrologyError(f"XRD scan missing {missing}")
    tt = np.asarray(scan["two_theta_deg"], float)
    inten = np.asarray(scan["intensity"], float)
    if tt.size != inten.size or tt.size < 3:
        raise MetrologyError("malformed XRD scan")
    peak = float(tt[int(np.argmax(inten))])
    return {"specimen_id": specimen_id,
            "classification": "EXPERIMENTALLY_MEASURED",
            "evidence_tags": ["MEAS"],
            "dominant_two_theta_deg": peak,
            "calibration_id": scan["calibration_id"],
            "note": "peak assignment to a crystallographic plane "
                    "requires the reference pattern; this returns the "
                    "measured peak only"}


# --- scan-to-mesh import with malformed handling -----------------------------

def scan_to_mesh(points_mm: np.ndarray,
                 max_edge_mm: float = 2.0) -> dict:
    """Import a photogrammetric/structured-light point cloud and report
    whether it is usable as a geometry source. Malformed scans are
    REFUSED, not silently repaired: a hole-filled guess would enter the
    solver as if it were measured geometry."""
    p = np.asarray(points_mm, float)
    if p.ndim != 2 or p.shape[1] != 3:
        raise MetrologyError("point cloud must be (N,3) in mm")
    if len(p) < 32:
        return {"usable": False, "status": "INSUFFICIENT_RESOLUTION",
                "reason": f"only {len(p)} points; cannot bound a "
                          "surface", "n_points": len(p)}
    if not np.all(np.isfinite(p)):
        return {"usable": False, "status": "INCONCLUSIVE",
                "reason": "non-finite coordinates in scan",
                "n_points": len(p)}
    extent = p.max(axis=0) - p.min(axis=0)
    centroid = p.mean(axis=0)
    # nearest-neighbour spacing as a crude density probe
    sample = p[::max(1, len(p) // 200)]
    d = np.linalg.norm(sample[:, None, :] - sample[None, :, :], axis=2)
    np.fill_diagonal(d, np.inf)
    spacing = float(np.median(d.min(axis=1)))
    usable = spacing <= max_edge_mm
    return {"usable": bool(usable),
            "status": "REDUCED_ORDER_VALIDATED" if usable
            else "INSUFFICIENT_RESOLUTION",
            "n_points": int(len(p)),
            "extent_mm": extent.tolist(),
            "centroid_mm": centroid.tolist(),
            "median_point_spacing_mm": spacing,
            "bounding_length_mm": float(extent.max()),
            "reason": "" if usable else
            f"median point spacing {spacing:.3f} mm exceeds the "
            f"{max_edge_mm} mm target; scan is too sparse to define "
            "the geometry",
            "note": "no hole filling or smoothing is applied; a "
                    "repaired scan is a model, not a measurement"}


def ideal_vs_scanned(ideal_length_mm: float, scan_report: dict
                     ) -> dict:
    """Compare the ideal design geometry to an as-scanned body. The
    deviation is reported at its exact value."""
    if not scan_report.get("usable"):
        return {"comparable": False,
                "status": scan_report.get("status",
                                          "INSUFFICIENT_RESOLUTION"),
                "reason": "scan is not usable as a geometry source"}
    got = scan_report["bounding_length_mm"]
    return {"comparable": True,
            "ideal_length_mm": ideal_length_mm,
            "scanned_length_mm": got,
            "deviation_mm": got - ideal_length_mm,
            "relative": (got - ideal_length_mm)
            / max(ideal_length_mm, 1e-12),
            "note": "the ideal geometry is NOT adjusted to match the "
                    "scan, and the scan is not adjusted to match the "
                    "ideal"}


# --- protocol record ----------------------------------------------------------

def metrology_protocol() -> dict:
    """The C05 protocol as a typed record: what must be measured, with
    what, to what resolution, in what order."""
    steps = [
        "calibrate every instrument and record calibration_id",
        "photograph on a calibrated scale target, multi-angle",
        "tip-to-tip length (caliper, 3 repeats, different operators)",
        "widths at >=5 declared axial stations (micrometer)",
        "facet count and rotation (goniometer + photograph)",
        "cap heights and included apex angles (goniometer)",
        "mass (balance, 3 repeats)",
        "volume (displacement or scan-derived, declared method)",
        "density and mass-volume consistency check",
        "polish/chip/crack/inclusion/rutile map (photograph)",
        "mount points and electrode coverage",
        "XRD c-axis and lateral axis (INTERFACE until hardware)",
        "temperature and humidity at measurement time",
        "seller values recorded separately, never overwritten",
    ]
    return make_record(
        "ExperimentProtocolRecord", "C05-METROLOGY",
        "specimen metrology and orientation protocol", "geometry",
        "PROTOCOL_READY_HARDWARE_REQUIRED", ["ENG"],
        steps=steps, instruments=REQUIRED_INSTRUMENTS,
        controls=["repeated measurement (>=3)",
                  "inter-operator variation (>=2 operators)",
                  "calibration before and after session",
                  "seller-versus-measured separation",
                  "mass-volume consistency versus quartz density"],
        failure_conditions=[
            "inter-operator spread exceeds the instrument resolution "
            "by >5x (protocol not reproducible)",
            "implied density deviates >2% from 2.648 g/cm^3 without "
            "an inclusion explanation",
            "XRD unavailable: orientation stays INTERFACE_ONLY"],
        blocker="no specimen has been measured; requires physical "
                "instruments and specimens in hand")
