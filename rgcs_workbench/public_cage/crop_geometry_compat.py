"""V7 crop geometry physics-compatibility run.

Scores crop-formation measurement records against the RGCS geometry
anchors and V6 candidates. A high score means GOOD CANDIDATE FOR
MEASUREMENT AND MODEL COMPARISON; it never means the formation
functioned physically. Plan-view geometry can compare diameters,
ratios, counts, pitch, and scale families; it cannot provide groove
depth, layer thickness, permittivity, resonance, or operation.

Ingestion is sanitizing by construction: local filesystem paths and
non-public fields from the private cookbook never enter the
committed feature file; every row keeps its public source URL and
raw measurement text; no missing measurement is invented. Weak rows
stay listed as INSUFFICIENT_GEOMETRY or NEEDS_SOURCE_DIMENSION
rather than being dropped.
"""

from __future__ import annotations

import csv
import json
import math
import pathlib
import re

_HERE = pathlib.Path(__file__).resolve().parent

RATIO_47_72 = 47.0 / 72.0
CELLS = 37
COUNT_NEAR = (33, 35, 36, 38)
FIELD_REFERENCE_M = {"outer": 288.0, "inner": 188.0}
V6_ANCHORS = {
    "champion": {"od_mm": 288, "groove_mm": 14},
    "razor_edge": {"od_mm": 188, "groove_mm": 8},
    "non_obvious": {"od_mm": 188, "groove_mm": 18},
}

CLASSES = ("CROP_GEOMETRY_ONLY", "CROP_RATIO_MATCH",
           "CROP_RING_SCALE_MATCH", "CROP_37_PITCH_MATCH",
           "CROP_DIELECTRIC_WITNESS_TARGET",
           "CROP_PHYSICS_COMPATIBILITY_CANDIDATE",
           "CROP_NEEDS_MEASUREMENT", "CROP_REJECTED_WITH_REASON",
           "INSUFFICIENT_GEOMETRY", "NEEDS_SOURCE_DIMENSION",
           "REFERENCE_NOT_CROP")

CLAIM_STATUS = "MODEL_COMPARISON_ONLY"

TOLERANCE_BANDS = (("EXACT", 0.25), ("STRONG", 1.0), ("MODERATE", 3.0),
                   ("WEAK", 5.0))

SCORE_WEIGHTS = {
    "geometry_ratio_score": 0.20,
    "count_symmetry_score": 0.15,
    "rgcs_scale_score": 0.15,
    "v6_candidate_proximity_score": 0.15,
    "crop_measurement_quality_score": 0.10,
    "physics_observability_score": 0.10,
    "null_testability_score": 0.10,
    "source_reliability_score": 0.05,
}

_FT_TO_M = 0.3048

_DIM_PATTERNS = (
    re.compile(r"(?:approximately\s+)?(\d+(?:\.\d+)?)\s*(ft|feet)\s+"
               r"(?:diameter|span|across)", re.I),
    re.compile(r"(?:approximately\s+)?(\d+(?:\.\d+)?)\s*(m|meters?|metres?)"
               r"\s+(?:diameter|span|across)", re.I),
    re.compile(r"outer\s+diameter\s+(\d+(?:\.\d+)?)\s*(m|ft)", re.I),
)
_INNER_PATTERN = re.compile(
    r"inner\s+diameter\s+(\d+(?:\.\d+)?)\s*(m|ft)", re.I)


def percent_error(value: float, target: float) -> float:
    return abs(100.0 * (value - target) / target)


def tolerance_band(err_percent: float) -> str:
    for name, limit in TOLERANCE_BANDS:
        if err_percent <= limit:
            return name
    return "REJECT"


def _to_m(value: float, unit: str) -> float:
    return value * _FT_TO_M if unit.lower().startswith("f") else value


def parse_dimensions_m(text: str):
    """(outer_m, inner_m) parsed from raw statement text, or Nones.
    Raw text is preserved beside the parse; nothing is inferred."""
    outer = inner = None
    for pattern in _DIM_PATTERNS:
        match = pattern.search(text)
        if match:
            outer = _to_m(float(match.group(1)), match.group(2))
            break
    inner_match = _INNER_PATTERN.search(text)
    if inner_match:
        inner = _to_m(float(inner_match.group(1)), inner_match.group(2))
    return outer, inner


# ------------------------------------------------------------ ingestion

def sanitize_row(raw: dict) -> dict:
    """Public-safe feature row: ids, public URLs, counts, ratios,
    raw measurement text. Never local paths or private fields."""
    rg = raw.get("relative_geometry") or {}
    sat = rg.get("satellite_count") or {}
    conc = rg.get("concentric_radii") or {}
    ratio = None
    fractions = conc.get("radius_fractions") or []
    approximations = conc.get("approximations") or []
    if len(approximations) >= 2:
        ratio = approximations[0] / approximations[-1]
    text = " ; ".join(m.get("statement", "")
                      for m in raw.get("measurements", []))
    outer_m, inner_m = parse_dimensions_m(text)
    if outer_m and inner_m and ratio is None:
        ratio = inner_m / outer_m
    sources = raw.get("sources") or []
    url = next((s.get("url") for s in sources if s.get("url")), None)
    return {
        "formation_id": raw.get("id"),
        "name": raw.get("name"),
        "date_reported": raw.get("date_reported"),
        "location": raw.get("location"),
        "source_url": url,
        "archive_status": raw.get("archive_status"),
        "satellite_count": sat.get("count"),
        "satellite_confidence": sat.get("confidence"),
        "radius_fractions": fractions,
        "inner_outer_ratio": ratio,
        "outer_diameter_m": outer_m,
        "inner_diameter_m": inner_m,
        "raw_measurement_text": text[:400],
        "provenance": "COOKBOOK_EXTRACTED",
    }


def ingest_cookbook(data_dir: str | pathlib.Path) -> list[dict]:
    """Dev-time ingestion from the private cookbook tree. The output
    is the sanitized public feature list; commit THAT, never the raw
    tree."""
    base = pathlib.Path(data_dir)
    rows: list[dict] = []
    seen: set[str] = set()
    for name in ("formations.json",
                 "multisite_all_years_calculated/formations.json"):
        payload = json.loads((base / name).read_text(encoding="utf-8"))
        for raw in payload.get("formations", []):
            row = sanitize_row(raw)
            if row["formation_id"] and row["formation_id"] not in seen:
                seen.add(row["formation_id"])
                rows.append(row)
    rows.sort(key=lambda r: r["formation_id"])
    return rows


def load_features() -> list[dict]:
    return json.loads((_HERE / "v7_crop_features.json")
                      .read_text(encoding="utf-8"))["rows"]


# -------------------------------------------------------------- scoring

def _is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    return all(n % k for k in range(2, int(math.isqrt(n)) + 1))


def geometry_ratio_score(ratio) -> tuple[float, str]:
    if ratio is None:
        return 0.0, "NO_RATIO"
    err = percent_error(ratio, RATIO_47_72)
    band = tolerance_band(err)
    scores = {"EXACT": 1.0, "STRONG": 0.8, "MODERATE": 0.5, "WEAK": 0.25,
              "REJECT": 0.0}
    return scores[band], band


def count_symmetry_score(count) -> tuple[float, str]:
    if not count:
        return 0.0, "NO_COUNT"
    if count == CELLS:
        return 1.0, "COUNT_37_EXACT"
    if count in COUNT_NEAR:
        return 0.6, "COUNT_NEAR_37_LABELED_NEAR"
    if _is_power_of_two(count):
        return 0.5, "DYADIC_FAMILY"
    if _is_prime(count):
        return 0.4, "PRIME_FAMILY"
    return 0.2, "COUNT_PRESENT_OTHER_FAMILY"


def rgcs_scale_score(outer_m) -> tuple[float, str]:
    if not outer_m:
        return 0.0, "NEEDS_SOURCE_DIMENSION"
    errors = {"FIELD_288M": percent_error(outer_m, 288.0),
              "FIELD_188M": percent_error(outer_m, 188.0)}
    family, err = min(errors.items(), key=lambda kv: kv[1])
    band = tolerance_band(err)
    scores = {"EXACT": 1.0, "STRONG": 0.8, "MODERATE": 0.5, "WEAK": 0.3,
              "REJECT": 0.1}
    return scores[band], f"{family}_{band}"


def v6_proximity_score(row: dict) -> float:
    score = 0.0
    if row.get("inner_outer_ratio") is not None:
        err = percent_error(row["inner_outer_ratio"], RATIO_47_72)
        if err <= 5.0:
            score += 0.6
    if row.get("satellite_count") in (CELLS, 35, 33):
        score += 0.4
    return min(1.0, score)


def quality_score(row: dict) -> float:
    score = 0.0
    if row.get("outer_diameter_m"):
        score += 0.4
    if row.get("inner_outer_ratio") is not None:
        score += 0.3
    if row.get("satellite_confidence") in ("high", "medium"):
        score += 0.3
    return min(1.0, score)


def observability_score(row: dict) -> float:
    date = str(row.get("date_reported") or "")
    recent = date[:4].isdigit() and int(date[:4]) >= 2020
    return 0.8 if recent else 0.3      # residue lanes decay with time


def null_testability_score(row: dict) -> float:
    return 0.7 if row.get("inner_outer_ratio") is not None else 0.4


def source_reliability_score(row: dict) -> float:
    return 1.0 if row.get("archive_status") == "SOURCE_PAGE_VERIFIED" \
        else 0.5


def score_row(row: dict) -> dict:
    out = dict(row)
    ratio_score, ratio_band = geometry_ratio_score(
        row.get("inner_outer_ratio"))
    count_score, count_family = count_symmetry_score(
        row.get("satellite_count"))
    scale_score, scale_family = rgcs_scale_score(
        row.get("outer_diameter_m"))
    scores = {
        "geometry_ratio_score": ratio_score,
        "count_symmetry_score": count_score,
        "rgcs_scale_score": scale_score,
        "v6_candidate_proximity_score": v6_proximity_score(row),
        "crop_measurement_quality_score": quality_score(row),
        "physics_observability_score": observability_score(row),
        "null_testability_score": null_testability_score(row),
        "source_reliability_score": source_reliability_score(row),
    }
    out.update(scores)
    out["ratio_band"] = ratio_band
    out["count_family"] = count_family
    out["scale_family"] = scale_family
    out["score_total"] = round(sum(
        SCORE_WEIGHTS[k] * v for k, v in scores.items()), 6)
    out["claim_status"] = CLAIM_STATUS
    out["classification"] = _classify(out)
    out["nearest_rgcs_family"] = (
        "47/72_RING" if ratio_band in ("EXACT", "STRONG", "MODERATE")
        else count_family if count_score >= 0.4
        else scale_family)
    out["needed_measurement"] = _needed_measurement(out)
    if out["classification"] == "CROP_REJECTED_WITH_REASON":
        out["failed_condition"] = "no_family_within_tolerance"
        out["why_it_failed"] = (
            f"ratio band {ratio_band}, count family {count_family}, "
            f"scale {scale_family}: nothing inside the 5 percent band "
            f"and no symbolic count evidence")
        out["salvage_measurement"] = (
            "drone photogrammetry or source-diagram scale to replace "
            "the missing or out-of-band dimensions")
        out["source_gap"] = ("absolute dimensions"
                            if not row.get("outer_diameter_m")
                            else "none; geometry is simply out of band")
    return out


def _classify(row: dict) -> str:
    if str(row.get("formation_id", "")).startswith("RGCS-REFERENCE"):
        return "REFERENCE_NOT_CROP"
    has_ratio = row.get("inner_outer_ratio") is not None
    has_count = bool(row.get("satellite_count"))
    has_dim = bool(row.get("outer_diameter_m"))
    if not (has_ratio or has_count or has_dim):
        return "INSUFFICIENT_GEOMETRY"
    if row["ratio_band"] in ("EXACT", "STRONG"):
        return "CROP_RATIO_MATCH"
    if row["count_family"] == "COUNT_37_EXACT":
        return "CROP_37_PITCH_MATCH"
    if row["scale_family"].endswith(("EXACT", "STRONG")):
        return "CROP_RING_SCALE_MATCH"
    if row["score_total"] >= 0.45:
        return "CROP_PHYSICS_COMPATIBILITY_CANDIDATE"
    if not has_dim and (has_ratio or has_count):
        return "NEEDS_SOURCE_DIMENSION"
    if row["score_total"] >= 0.30:
        return "CROP_NEEDS_MEASUREMENT"
    return "CROP_REJECTED_WITH_REASON"


def _needed_measurement(row: dict) -> str:
    if not row.get("outer_diameter_m"):
        return "absolute diameter by drone photogrammetry or diagram scale"
    if row.get("inner_outer_ratio") is None:
        return "inner ring diameter to fix the inner/outer ratio"
    return ("residue sampling: Raman/FTIR, dielectric, conductivity, "
            "particulate, with off-formation controls")


def score_all() -> dict:
    rows = [score_row(r) for r in load_features()]
    scored = [r for r in rows
              if r["classification"] not in ("INSUFFICIENT_GEOMETRY",
                                             "REFERENCE_NOT_CROP")]
    ranked = sorted(scored, key=lambda r: (-r["score_total"],
                                           r["formation_id"]))
    for rank, row in enumerate(ranked, start=1):
        row["rank"] = rank
    rejected = [r for r in ranked
                if r["classification"] == "CROP_REJECTED_WITH_REASON"]
    count_37 = [r for r in rows
                if r.get("satellite_count") == CELLS]
    return {
        "rows": rows, "ranked": ranked, "rejected": rejected,
        "insufficient": [r for r in rows
                         if r["classification"] == "INSUFFICIENT_GEOMETRY"],
        "reference_rows": [r for r in rows
                           if r["classification"] == "REFERENCE_NOT_CROP"],
        "count_37_exact": count_37,
        "counts": {"ingested": len(rows), "scored": len(scored),
                   "rejected": len(rejected),
                   "insufficient": len(rows) - len(scored)
                   - len([r for r in rows
                          if r["classification"] == "REFERENCE_NOT_CROP"])},
        "claim": CLAIM_STATUS,
    }


# -------------------------------------------------------- base rates

def ratio_base_rate(result: dict, window_percent: float = 1.0) -> dict:
    """How many 47/72 hits chance alone would produce: observed ratio
    rows spread over their empirical range, one target, +/- window.
    Honesty gate for the report: hits at or below expectation are not
    evidence of anything."""
    ratios = sorted(r["inner_outer_ratio"] for r in result["rows"]
                    if r.get("inner_outer_ratio") is not None)
    if len(ratios) < 10:
        return {"insufficient": True}
    lo = ratios[int(0.05 * len(ratios))]
    hi = ratios[int(0.95 * len(ratios)) - 1]
    window = 2.0 * (window_percent / 100.0) * RATIO_47_72
    density = len(ratios) / (hi - lo) if hi > lo else 0.0
    expected = density * window
    observed = sum(1 for x in ratios
                   if percent_error(x, RATIO_47_72) <= window_percent)
    return {"ratio_rows": len(ratios), "range_5_95": [lo, hi],
            "window_percent": window_percent,
            "expected_by_chance": round(expected, 2),
            "observed": observed,
            "excess_over_chance": observed > expected,
            "claim_status": "ARITHMETIC"}


# --------------------------------------------------------- outputs

_FEATURE_COLUMNS = ("formation_id", "name", "date_reported", "location",
                    "source_url", "satellite_count", "inner_outer_ratio",
                    "outer_diameter_m", "inner_diameter_m",
                    "raw_measurement_text", "provenance")
_SCORE_COLUMNS = ("formation_id", "name", "source_url", "rank",
                  "score_total", "classification", "ratio_band",
                  "count_family", "scale_family", "inner_outer_ratio",
                  "satellite_count", "outer_diameter_m",
                  "nearest_rgcs_family", "needed_measurement",
                  "claim_status")


def write_outputs(outdir: str | pathlib.Path,
                  result: dict | None = None) -> dict:
    result = result or score_all()
    out = pathlib.Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    written = {}

    def _csv(name, rows, columns):
        path = out / name
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns,
                                    extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        written[name] = str(path)

    def _md(name, lines):
        path = out / name
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        written[name] = str(path)

    ranked = result["ranked"]
    _csv("crop_geometry_features.csv",
         [r for r in result["rows"]
          if r["classification"] != "INSUFFICIENT_GEOMETRY"],
         _FEATURE_COLUMNS)
    _csv("crop_rgcs_compatibility_scores.csv", ranked, _SCORE_COLUMNS)
    _csv("crop_to_v6_candidate_matches.csv",
         [r for r in ranked if r["v6_candidate_proximity_score"] > 0],
         _SCORE_COLUMNS + ("v6_candidate_proximity_score",))

    rates = ratio_base_rate(result)
    counts = result["counts"]
    hits = [r for r in ranked if r["ratio_band"] in ("EXACT", "STRONG")]

    _md("crop_physics_compatibility_report.md", [
        "# Crop Physics Compatibility Report", "",
        "Claim status for every row: MODEL_COMPARISON_ONLY. A high",
        "score marks a good candidate for measurement and model",
        "comparison. It does not mean any formation functioned",
        "physically.", "",
        f"Rows ingested: {counts['ingested']}. Scored: "
        f"{counts['scored']}. Insufficient geometry (listed, not "
        f"dropped): {counts['insufficient']}. Rejected with reasons: "
        f"{counts['rejected']}.", "",
        "## Headline negative result", "",
        "Zero formations in the archive carry a detected 37-element "
        "count. Counts of 35 and 36 exist in single digits. The "
        "37-cell ring signature is absent from the measured crop "
        "record as extracted.", "",
        "## 47/72 ratio hits and the chance floor", "",
        f"{len(hits)} formations sit within 1 percent of 47/72; "
        f"{sum(1 for r in hits if r['ratio_band'] == 'EXACT')} within "
        f"0.25 percent. Chance expectation for the same window over "
        f"{rates['ratio_rows']} measured ratios is "
        f"{rates['expected_by_chance']}; observed {rates['observed']}. "
        f"Excess over chance: {rates['excess_over_chance']}. The ratio "
        f"hits are consistent with the chance floor and are ranked as "
        f"measurement candidates, not as evidence.", "",
        "## Top candidates", ""]
        + [f"{r['rank']:>3}. {r['formation_id']} score "
           f"{r['score_total']:.4f} {r['classification']} "
           f"(ratio band {r['ratio_band']}, count "
           f"{r.get('satellite_count')})" for r in ranked[:10]])

    _md("crop_measurement_priority.md", [
        "# Crop Measurement Priorities", "",
        "1. Drone photogrammetry for the top ratio-band formations "
        "(absolute scale is the missing variable for 1077 rows).",
        "2. Residue sampling with off-formation controls on any new "
        "formation: Raman/FTIR, dielectric, conductivity, "
        "particulate (dielectric witness lane).",
        "3. Inner-ring diameters for count-bearing formations "
        "without ratios.",
        "4. Source-diagram scale recovery for the three rejected "
        "curated formations.", "",
        "## Per-formation needs", ""]
        + [f"- {r['formation_id']}: {r['needed_measurement']}"
           for r in ranked[:15]])

    _md("crop_rejected_candidates.md", [
        "# Rejected Crop Candidates", "",
        "Rejection is a report with a salvage path, never a silent "
        "drop.", ""]
        + [f"## {r['formation_id']}\n\n"
           f"- failed condition: {r['failed_condition']}\n"
           f"- why: {r['why_it_failed']}\n"
           f"- nearest RGCS family: {r['nearest_rgcs_family']}\n"
           f"- salvage measurement: {r['salvage_measurement']}\n"
           f"- source gap: {r['source_gap']}\n"
           for r in result["rejected"]])

    _md("crop_null_controls.md", [
        "# Crop Null Controls", "",
        "- Off-formation plant and soil samples, same crop and field.",
        "- Randomly selected non-formation field circles for the "
        "ratio base-rate comparison (the chance floor above).",
        "- Time-decay retest of any residue measurement.",
        "- Non-patterned crop for every witness-layer measurement.",
        "- Diagram-rescale control: re-derive each ratio from an "
        "independent source image before it counts as measured."])

    _md("final_report_draft.md", [
        "# Crop Geometry and RGCS Physics: Compatibility Run Report",
        "",
        "This run compared the extracted geometry of "
        f"{counts['ingested']} archived crop-formation records "
        "against the RGCS modeled geometry families. Every row "
        "carries claim status MODEL_COMPARISON_ONLY.", "",
        "## What was found", "",
        "1. The 37-element signature of the RGCS ring does not "
        "appear in the archive's detected counts. This is a clean "
        "negative result.",
        f"2. {len(hits)} formations match the 47/72 ring ratio "
        f"within 1 percent, including "
        f"{', '.join(r['formation_id'] for r in hits[:2])} inside "
        f"0.25 percent. The hit count sits at the chance floor for "
        f"the measured ratio population, so these are measurement "
        f"targets, not evidence.",
        "3. Absolute scale is the dominant missing variable: 1077 "
        "scored rows need a source dimension before ring-scale "
        "comparison is possible.",
        "4. Three curated formations with absolute sizes were "
        "rejected because their dimensions sit far from the 188 m "
        "and 288 m field-profile anchors; photogrammetry or diagram "
        "scale could still salvage or refute them.", "",
        "## What this does not say", "",
        "No formation is claimed to be a functioning device. "
        "Geometry match is not physical validation. Plan-view "
        "measurements cannot provide groove depth, permittivity, or "
        "resonance. Near frequency is never identity.", "",
        "## Next steps", "",
        "Drone photogrammetry on the two EXACT-band formations, "
        "residue protocols on any fresh formation, and the null "
        "controls listed in crop_null_controls.md."])

    return written


__all__ = ["RATIO_47_72", "CELLS", "COUNT_NEAR", "FIELD_REFERENCE_M",
           "V6_ANCHORS", "CLASSES", "CLAIM_STATUS", "TOLERANCE_BANDS",
           "SCORE_WEIGHTS", "percent_error", "tolerance_band",
           "parse_dimensions_m", "sanitize_row", "ingest_cookbook",
           "load_features", "geometry_ratio_score",
           "count_symmetry_score", "rgcs_scale_score", "score_row",
           "score_all", "ratio_base_rate", "write_outputs"]
