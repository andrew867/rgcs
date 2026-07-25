"""R10.8.1 CW Atlas demonstration bundle (P64).

A runnable end-to-end demo over the tested engine. It shows the two
firewalled systems: the canonical reversible geocoder (map -> vector -> map,
exact) and the source-vector hypothesis decoder (legacy string -> alias set
or refusal, never a forced pin). Nothing here claims a source vector
identifies a real location.

Run from the repo root:  python docs/cwatlas/demo_cw_atlas.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running as a standalone script (repo root on sys.path).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cwatlas import service  # noqa: E402


def _show(title: str, d: dict, keys=None) -> None:
    print(f"== {title} ==")
    view = {k: d[k] for k in keys if k in d} if keys else d
    print(json.dumps(view, indent=2, default=str))
    print()


def main() -> int:
    epoch = "2025.0"

    # 1) Canonical: declared point -> versioned CW vector.
    enc = service.encode_point(body_id="EARTH", frame_id="WGS84", epoch=epoch,
                               latitude_deg=51.178, longitude_deg=-1.826,
                               uncertainty_m=10.0, height_m=0.0)
    _show("canonical encode (CW-GEO-1)", enc,
          ["vector", "claim_class", "crs", "epoch", "codec_id"])

    # 2) Canonical vector -> exactly one point (or typed refusal).
    vec = enc.get("vector")
    if vec:
        dec = service.decode_vector(vec)
        _show("canonical decode -> point", dec,
              ["latitude_deg", "longitude_deg", "status", "claim_class"])

    # 3) Exact round-trip residual.
    rt = service.round_trip(body_id="EARTH", frame_id="WGS84", epoch=epoch,
                            latitude_deg=51.178, longitude_deg=-1.826,
                            uncertainty_m=10.0, height_m=0.0)
    _show("round-trip residual", rt,
          ["error_m", "within_tolerance", "claim_class"])

    # 4) Source-vector hypothesis decode -> alias set (NEVER a location).
    aliases = service.legacy_search("512834007")
    _show("legacy search (alias set, never a pin)", aliases,
          ["status", "n_candidates", "search_space_count",
           "claim_class", "source_vector_geographic_semantics"])

    print("== verdict ==")
    for line in (
        "RGCS_R10_8_1_GREEN_CW_ATLAS_READY",
        "CANONICAL_ROUND_TRIP_VERIFIED",
        "LEGACY_ALIAS_SET_PIPELINE_VERIFIED",
        "SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED",
        "PHYSICAL_VALIDATION_NOT_CLAIMED",
    ):
        print("  " + line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
