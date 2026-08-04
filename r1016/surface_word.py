"""R10.16B patch — canonical surface/projection word resolution.

A raw transport wire is not necessarily the word that gets projected.
Where a record carries a canonical packet or candidate, THAT is the
surface word, and projecting the raw wire instead can collapse a
vector into the wrong cluster.

The historical record that forced this distinction was removed from all
anchor lanes by the later R10.18 operator authority. The generic resolver
remains because future records can still distinguish transport and surface
words; removed records must not be reintroduced as examples or anchors.

Any projection from a raw wire where a canonical word exists must be
labelled RAW_TRANSPORT_WIRE_DIAGNOSTIC and kept separate.
"""

from __future__ import annotations

RAW_DIAGNOSTIC_LABEL = "RAW_TRANSPORT_WIRE_DIAGNOSTIC"

#: Strict-anchor records. MONTREAL WAS REMOVED at operator instruction
#: (R10.18): the 165879243 / 168500683 pairing was mislabelled at source
#: and is no longer an anchor in any lane. Do not reintroduce it.
#: ``canonical_packet_or_candidate`` is the
#: surface/projection word where it differs from the transport wire.
ANCHOR_RECORDS = {
    "Stonehenge": {
        "raw_vector": "165876523",
        "canonical_packet_or_candidate": "165876523",
        "current_status": "TRAINING_ANCHOR",
        "lat": 51.1789, "lon": -1.8262,
    },
    "Toronto": {
        "raw_vector": "168930443",
        "canonical_packet_or_candidate": "168930443",
        "current_status": "CORRECTED_WIRE_TO_CANONICAL_CANDIDATE",
        "lat": 43.6532, "lon": -79.3832,
    },
    "Erie": {
        "raw_vector": "167849523",
        "canonical_packet_or_candidate": "167849523",
        "current_status": "LEGACY_SAME_LOCATION_PAIR",
        "lat": 42.1292, "lon": -80.0851,
    },
}


def resolve_surface_word(record: dict):
    """Resolver exactly as specified by the patch."""
    canonical = record.get("canonical_packet_or_candidate")
    status = record.get("current_status", "")

    if canonical and str(canonical).isdigit():
        if "CORRECTED_WIRE_TO_CANONICAL_CANDIDATE" in status:
            return int(canonical), "canonical_packet_or_candidate"

        if "LEGACY_SAME_LOCATION_PAIR" in status:
            return int(canonical), "canonical_packet_or_candidate"

    return int(record["raw_vector"]), "raw_vector"


def resolved_anchors() -> dict:
    """{name: (surface_word, source, lat, lon, raw)}"""
    out = {}
    for name, rec in ANCHOR_RECORDS.items():
        word, src = resolve_surface_word(rec)
        out[name] = {"surface_word": word, "source": src,
                     "raw_vector": int(rec["raw_vector"]),
                     "lat": rec["lat"], "lon": rec["lon"],
                     "differs_from_raw": word != int(rec["raw_vector"])}
    return out


def payload_octal(word) -> str:
    return format(int(str(word)[2:-1]), "o")


def resolution_report() -> dict:
    r = resolved_anchors()
    rows = []
    for name, v in r.items():
        rows.append({
            "anchor": name,
            "raw_vector": v["raw_vector"],
            "surface_word": v["surface_word"],
            "resolved_from": v["source"],
            "differs_from_raw": v["differs_from_raw"],
            "raw_payload_octal": payload_octal(v["raw_vector"]),
            "surface_payload_octal": payload_octal(v["surface_word"]),
        })
    changed = [x for x in rows if x["differs_from_raw"]]
    return {
        "schema": "rgcs.r1016b.surface-word-resolution.v1",
        "rows": rows,
        "anchors_rebound": len(changed),
        "rebound": [x["anchor"] for x in changed],
        "note": "projecting a raw transport wire where a canonical "
                "surface word exists can collapse a vector into the "
                "wrong cluster; such runs are labelled "
                + RAW_DIAGNOSTIC_LABEL,
    }
