"""Harmonic crystal family N=5..12 + specimen/metrology registry
(Agents C03/C05; coverage A11-A12, G001-G030; gates G09/G12).

The family generalizes the validated canonical ladder: the ideal N=7
length is (6310/(2*4096)) m / 7 = 770.263671875/7 mm (arithmetic,
frozen v4.0.0 provenance). L_N = 770.263671875 / N mm for N = 5..12,
built with the SAME validated geometry conventions (SP-Q154 diameter
ratios, 51.843deg/60deg face slopes, across-vertices diameters)."""

from __future__ import annotations

import math

from .crystal110 import CanonicalCrystal
from .research_records import make_record

LADDER_NUMERATOR_MM = 770.263671875           # (6310/(2*4096)) m in mm
FAMILY_N = tuple(range(5, 13))


def family_length_mm(n: int) -> float:
    if n not in FAMILY_N:
        raise ValueError("family covers N = 5..12")
    return LADDER_NUMERATOR_MM / n


def build_family_member(n: int) -> CanonicalCrystal:
    """Prospective specimen with the frozen geometry conventions."""
    L = family_length_mm(n)
    return CanonicalCrystal(
        variant=f"ideal_n{n}", length_mm=L,
        wide_diameter_mm=L * 40.0 / 154.0,
        narrow_diameter_mm=L * 30.0 / 154.0)


def family_table() -> list[dict]:
    rows = []
    for n in FAMILY_N:
        c = build_family_member(n)
        rows.append({"n": n, "length_mm": c.length_mm,
                     "wide_diameter_mm": c.wide_diameter_mm,
                     "narrow_diameter_mm": c.narrow_diameter_mm,
                     "female_cap_height_mm": c.female_cap_height_mm,
                     "male_cap_height_mm": c.male_cap_height_mm,
                     "shaft_length_mm": c.shaft_length_mm,
                     "status": "PROSPECTIVE_SPECIMEN (generated; "
                               "not fabricated)"})
    return rows


def tolerance_sensitivity(n: int, dl_mm: float = 0.1) -> dict:
    """Manufacturing-tolerance model (A12): to first order every
    modal frequency scales as f ~ 1/L, so df/f = -dL/L. A +/-0.1 mm
    machining tolerance on the length maps to the returned relative
    frequency band; diameters inherit the SP-Q154 ratios."""
    L = family_length_mm(n)
    rel = dl_mm / L
    return {"n": n, "length_mm": L, "dl_mm": dl_mm,
            "rel_frequency_band": rel,
            "note": "first-order -dL/L scaling, validated against "
                    "the ideal-vs-nominal pair at N=7 (v4.0.0 "
                    "internal-consistency check)"}


# --- angle registry (G001-G006) -------------------------------------------

ANGLE_REGISTRY = {
    "G001": {"label": "Rx receiving angle", "value_deg": 51.843,
             "basis": "frozen RG-16 source claim, v2 authority",
             "status": "SOURCE_HYPOTHESIS", "tags": ["SRC"]},
    "G002": {"label": "source form 51deg 51' 51\"",
             "value_deg": 51 + 51 / 60 + 51 / 3600,
             "basis": "sexagesimal source form = 51.864166... deg",
             "status": "SOURCE_HYPOTHESIS", "tags": ["SRC", "DER"],
             "note": "differs from 51.843 by 0.0212 deg — the two "
                     "source forms are NOT the same number; both "
                     "preserved"},
    "G003": {"label": "decimal conversion near 51.86 deg",
             "value_deg": 51.8642, "basis": "rounding of G002",
             "status": "SOURCE_HYPOTHESIS", "tags": ["DER"]},
    "G004": {"label": "vendor approximation", "value_deg": 52.0,
             "basis": "vendor catalog", "status": "SOURCE_HYPOTHESIS",
             "tags": ["SRC"]},
    "G005": {"label": "pyramid comparison", "value_deg": 51.827,
             "basis": "published Great Pyramid slope ~51deg50'40''",
             "status": "SOURCE_HYPOTHESIS", "tags": ["SRC"],
             "note": "numeric proximity to G001 is a motif, not "
                     "evidence of shared mechanism"},
    "G006": {"label": "Tx angle 60.000 deg (58-60 sensitivity)",
             "value_deg": 60.0, "band_deg": [58.0, 60.0],
             "basis": "frozen v2 geometry convention",
             "status": "CORE_VALIDATED", "tags": ["EST"]},
}


def angle_separations() -> dict:
    """Exact separations between the registered angle forms — the
    anti-conflation table (they are DIFFERENT numbers)."""
    a1 = ANGLE_REGISTRY["G001"]["value_deg"]
    a2 = ANGLE_REGISTRY["G002"]["value_deg"]
    a5 = ANGLE_REGISTRY["G005"]["value_deg"]
    return {"G001_vs_G002_deg": abs(a2 - a1),
            "G001_vs_G004_deg": abs(52.0 - a1),
            "G001_vs_G005_deg": abs(a5 - a1),
            "rule": "never silently substitute one form for another"}


# --- specimen catalog (G013-G030) ------------------------------------------

def _spec(rid, title, status, tags, **kw):
    return make_record("SpecimenRecord", rid, title, "metrology",
                       status, tags, **kw)


def specimen_registry() -> dict:
    R = {}

    def add(rec):
        R[rec["record_id"]] = rec

    add(_spec("G013", "canonical ideal vs nominal 110 mm",
              "CORE_VALIDATED", ["EST", "DER"],
              lengths_mm=[LADDER_NUMERATOR_MM / 7, 110.0],
              note="machine-distinct; frozen v4.0.0 authority"))
    add(_spec("G014", "non-metric eye coordinate policy",
              "CORE_VALIDATED", ["ENG"],
              note="eye_coordinate is null in all canonical records; "
                   "the v4.1 candidate is preserved at its exact "
                   "coordinate with uncertainty"))
    catalog = [
        ("G015", "71 mm 24-sided natural citrine", 71.0, 24,
         "citrine"),
        ("G016", "81 mm 8-sided natural citrine", 81.0, 8, "citrine"),
        ("G017", "75 mm 24-sided Himalayan rutilated", 75.0, 24,
         "rutilated"),
        ("G018", "63 mm 24-sided Himalayan rutilated", 63.0, 24,
         "rutilated"),
        ("G019", "138 mm 24-sided Himalayan rutilated", 138.0, 24,
         "rutilated"),
        ("G020", "86 mm 24-sided Himalayan rutilated", 86.0, 24,
         "rutilated"),
        ("G021", "62 mm 24-sided Himalayan smoky", 62.0, 24, "smoky"),
        ("G022", "125 mm 8-sided Himalayan", 125.0, 8, "clear"),
        ("G023", "157 mm 8-sided flawless Himalayan", 157.0, 8,
         "clear"),
        ("G024", "125 mm 12-sided flawless Himalayan", 125.0, 12,
         "clear"),
    ]
    for rid, title, L, facets, variety in catalog:
        add(_spec(rid, title, "SOURCE_HYPOTHESIS", ["SRC"],
                  length_mm=L, facets=facets, variety=variety,
                  provenance="seller catalog (uncertainty G027)",
                  measurement_plan="mass/dims/photos on receipt; "
                                   "XRD axis check per G011"))
    add(_spec("G025", "catalog mass records 34/39/59 g + full list",
              "SOURCE_HYPOTHESIS", ["SRC"],
              masses_g=[34.0, 39.0, 59.0],
              note="all catalog mass/dimension records preserved; "
                   "verified only on receipt"))
    add(_spec("G026", "variety comparison set (clear/citrine/"
              "amethyst/smoky/rutilated)", "ENGINEERING_PROTOTYPE",
              ["ENG"],
              plan="same-geometry cross-variety modal comparison "
                   "(E04); impurity content is the variable"))
    add(_spec("G027", "provenance uncertainty policy",
              "ENGINEERING_PROTOTYPE", ["ENG"],
              note="inclusions, surface damage, polish, density, and "
                   "seller uncertainty are recorded per specimen; no "
                   "catalog value is treated as measured"))
    add(_spec("G028", "prospective N=5..12 family",
              "ENGINEERING_PROTOTYPE", ["DER", "ENG"],
              members=[r["n"] for r in family_table()],
              note="generated by harmonic_family.build_family_member"))
    add(_spec("G029", "printed polymer geometry controls",
              "ENGINEERING_PROTOTYPE", ["ENG"],
              plan="same geometry, non-piezoelectric material — "
                   "separates geometry from material effects"))
    add(_spec("G030", "glass acoustic controls",
              "ENGINEERING_PROTOTYPE", ["ENG"],
              plan="isotropic amorphous control"))
    # geometry motifs (G007-G012)
    for rid, title, note in (
            ("G007", "six-sided lattice alignment",
             "hexagonal habit is EST crystallography; alignment "
             "claims beyond that are SRC"),
            ("G008", "6/8/12/24 facet families",
             "catalog + family generator support all four counts"),
            ("G009", "facet rotation and square/hex alignment",
             "geometry motif; testable via modal splitting (M6 "
             "symmetry-lowering machinery)"),
            ("G010", "phi ellipse, sqrt(phi), sqrt(3), sqrt(5), "
             "60/72 deg motifs",
             "numeric motifs; look-elsewhere model applies before "
             "any significance claim"),
            ("G011", "C-axis / lateral-axis XRD determination",
             "measurement PROTOCOL: Laue or powder XRD on receipt; "
             "PROTOCOL_READY_HARDWARE_REQUIRED"),
            ("G012", "vendor 100 nm alignment claim",
             "retained as SRC; NOT accepted fact; testable by G011")):
        add(make_record("GeometryMotifRecord", rid, title,
                        "metrology", "SOURCE_HYPOTHESIS"
                        if rid in ("G010", "G012") else
                        "ENGINEERING_PROTOTYPE",
                        ["SRC"] if rid in ("G010", "G012") else
                        ["ENG"], note=note))
    # angles G001-G006 wrapped as records
    for rid, a in ANGLE_REGISTRY.items():
        add(make_record("GeometryMotifRecord", rid, a["label"],
                        "metrology", a["status"], a["tags"],
                        value_deg=a.get("value_deg"),
                        note=a.get("note", a["basis"])))
    return R
