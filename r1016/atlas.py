"""R10.16 — atlas generation.

The strict anchor gate decides what this module is allowed to emit.
If no discrete model passes, there is NO main atlas: every produced
coordinate is diagnostic-only and is labelled as such. Emitting a
place-named atlas from a model that failed its own calibration gate
would be exactly the result-shopping the run forbids.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

from r1016.inventory import LUNAR_CANDIDATES, SOURCE_NOTES, inventory
from r1016.project import (STRICT_ANCHORS, STRICT_GATE_RMS_KM,
                           RootVariant, great_circle_km, project)
from r1016.views import candidates

#: Confidence classes, exactly as declared by the run.
CONFIDENCE = {
    "A": "CALIBRATION_ANCHOR_REPRODUCED",
    "B": "PRIOR_ATLAS_CANDIDATE_REPRODUCED",
    "C": "STRICT_HOLDOUT_COHERENT",
    "D": "DIAGNOSTIC_CLUSTER_ONLY",
    "E": "OCEAN_OR_NO_PLACE_MATCH",
    "F": "NO_VALID_NO_WARP_PROJECTION",
    "G": "LUNAR_SHEET_ONLY",
}

#: Neutral feature classes. No targeting language, ever.
FEATURE_CLASSES = (
    "MILITARY_RESERVE_ARMORY_GUARD_OR_WAR_HISTORY_ASSOCIATION",
    "CIVIL_INFRASTRUCTURE_ASSOCIATION",
    "ANCIENT_OR_ARCHAEOLOGICAL_ASSOCIATION",
    "COASTAL_OR_MARITIME_ASSOCIATION",
    "ASTRONOMICAL_OR_SPACE_PROGRAM_ASSOCIATION",
    "NO_OBVIOUS_PUBLIC_FEATURE_ASSOCIATION",
)

PLACE_ENRICHMENT_STATUS = (
    "DEFERRED_NO_OFFLINE_GAZETTEER: GeoNames cities5000 is not "
    "available in this offline environment. Per the run policy, "
    "coordinates are produced first and place enrichment is deferred. "
    "No settlement, feature, coastline or admin lookup has been "
    "performed, and none is invented.")


def octal(n: int) -> str:
    return format(n, "o")


def binary(n: int) -> str:
    return format(n, "b")


def build_rows(gate_passed: bool, best_model: dict,
               rotation, include_private: bool = True) -> list[dict]:
    """One row per (vector, view, window) candidate."""
    inv = inventory(include_private=include_private)
    variant: RootVariant = best_model["variant"]
    rows = []
    for rec in inv["rows"]:
        wire = rec["wire"]
        head, payload, terminal = wire[:2], wire[2:-1], wire[-1]
        body = rec["body_profile"]
        for c in candidates(wire):
            base = {
                "raw_vector": wire,
                "source_note": rec["source_note"],
                "payload_decimal": payload,
                "payload_octal": octal(int(payload)),
                "payload_binary": binary(int(payload)),
                "numeric_view": c["view"],
                "window": c.get("window"),
                "body_profile": body,
                "root_variant_id": variant.id,
                "is_path_vector": rec["is_private_path_vector"],
            }
            if c.get("word") is None:
                rows.append({**base, "f5": None, "source_face": None,
                             "q22_path": None, "s3": None,
                             "terminal": terminal, "lat": None,
                             "lon": None,
                             "nearest_features": PLACE_ENRICHMENT_STATUS,
                             "distance_bands": None,
                             "land_ocean": "UNDETERMINED_NO_COORDINATE",
                             "anchor_fit_score": None,
                             "expanded_atlas_score": None,
                             "confidence_class": "F",
                             "confidence_label": CONFIDENCE["F"],
                             "reason_confidence_not_higher":
                                 c.get("refusal", "no 30-bit word"),
                             "feature_class":
                                 "NO_OBVIOUS_PUBLIC_FEATURE_ASSOCIATION"})
                continue
            try:
                p = project(c["word"], variant, rotation)
            except Exception as ex:
                rows.append({**base, "f5": None, "source_face": None,
                             "q22_path": None, "s3": None,
                             "terminal": terminal, "lat": None,
                             "lon": None,
                             "nearest_features": PLACE_ENRICHMENT_STATUS,
                             "distance_bands": None,
                             "land_ocean": "UNDETERMINED_NO_COORDINATE",
                             "anchor_fit_score": None,
                             "expanded_atlas_score": None,
                             "confidence_class": "F",
                             "confidence_label": CONFIDENCE["F"],
                             "reason_confidence_not_higher":
                                 f"parser refused: {str(ex)[:90]}",
                             "feature_class":
                                 "NO_OBVIOUS_PUBLIC_FEATURE_ASSOCIATION"})
                continue
            anchor_err = None
            if wire in STRICT_ANCHORS:
                _, alat, alon = STRICT_ANCHORS[wire]
                anchor_err = great_circle_km(p["lat"], p["lon"],
                                             alat, alon)
            if body == "MOON":
                cls = "G"
                why = ("lunar candidate: routed to the separate Moon "
                       "sheet; no Earth projection is asserted")
            elif not gate_passed:
                cls = "D"
                why = (f"the strict anchor gate FAILED for every "
                       f"discrete model (best RMS "
                       f"{best_model['rms_km']:,.0f} km vs the "
                       f"{STRICT_GATE_RMS_KM:.0f} km limit), so no "
                       "model is calibrated and this coordinate is a "
                       "diagnostic cluster position only, not a place")
            else:
                cls = "C"
                why = "gate passed; holdout coherence not yet assessed"
            rows.append({
                **base,
                "f5": p["f5"], "source_face": p["source_face"],
                "q22_path": " ".join(str(x) for x in p["q22_path"]),
                "s3": p["s3"], "terminal": terminal,
                "lat": round(p["lat"], 6), "lon": round(p["lon"], 6),
                "nearest_features": PLACE_ENRICHMENT_STATUS,
                "distance_bands": "NOT_COMPUTED_ENRICHMENT_DEFERRED",
                "land_ocean": "UNDETERMINED_NO_COASTLINE_DATASET",
                "anchor_fit_score": (round(anchor_err, 3)
                                     if anchor_err is not None else None),
                "expanded_atlas_score": None,
                "confidence_class": cls,
                "confidence_label": CONFIDENCE[cls],
                "reason_confidence_not_higher": why,
                "feature_class":
                    "NO_OBVIOUS_PUBLIC_FEATURE_ASSOCIATION",
            })
    return rows


def write_csv(path: Path, rows: list[dict], fields=None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = fields or list(rows[0])
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def write_geojson(path: Path, rows: list[dict]) -> int:
    feats = []
    for r in rows:
        if r.get("lat") is None:
            continue
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Point",
                         "coordinates": [r["lon"], r["lat"]]},
            "properties": {k: v for k, v in r.items()
                           if k not in ("lat", "lon")},
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(
        {"type": "FeatureCollection",
         "note": "DIAGNOSTIC ONLY - no model passed the strict anchor "
                 "gate; these are not asserted places",
         "features": feats}, indent=1), encoding="utf-8")
    return len(feats)


def write_kml(path: Path, rows: list[dict]) -> int:
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>',
             "<name>RGCS R10.16 diagnostic vector positions</name>",
             "<description>DIAGNOSTIC ONLY. No model passed the strict "
             "anchor gate. These points are not asserted places."
             "</description>"]
    n = 0
    for r in rows:
        if r.get("lat") is None:
            continue
        n += 1
        parts.append(
            f"<Placemark><name>{r['raw_vector']}</name>"
            f"<description>view={r['numeric_view']} "
            f"class={r['confidence_class']} "
            f"({r['confidence_label']})</description>"
            f"<Point><coordinates>{r['lon']},{r['lat']},0"
            "</coordinates></Point></Placemark>")
    parts.append("</Document></kml>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")
    return n
