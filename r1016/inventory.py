"""R10.16 — the vector inventory for this diagnostic run.

Public corpora come from the committed R10.11/R10.12/R10.13 registries.
The 17 private path vectors are read from the operator's private lane
ONLY when explicitly enabled: the operator authorised them as
non-PII public-working data for this run, but that authorisation is
for the WORKING OUTPUT, not for the tracked public tree. The R10.15
privacy gate stays armed, so this module never writes them into the
repository and the atlas outputs are produced outside it.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

#: The private lane location is NEVER hardcoded here. Embedding the
#: directory or the ledger filename in tracked source would itself be
#: a private-path disclosure, which the R10.15 privacy gate correctly
#: flags. Both come from the environment at run time:
#:
#:   RGCS_R1016_PRIVATE_LANE  directory holding the operator's lane
#:   RGCS_R1016_LEDGER_NAME   ledger filename inside it
#:
#: With neither set, this module simply has no private input and the
#: inventory is public-only.
PRIVATE_LANE_ENV = "RGCS_R1016_PRIVATE_LANE"
LEDGER_NAME_ENV = "RGCS_R1016_LEDGER_NAME"

#: Source notes for named / described vectors (descriptions are SOURCE
#: CLAIMS, never confirmed places).
SOURCE_NOTES = {
    "165876523": "Stonehenge (strict anchor; TRAINING equality)",
    "168930443": "Toronto (strict anchor)",
    "165879243": "Montreal corrected (strict anchor)",
    "167849523": "Erie (strict anchor)",
    "165892733": "described St John's; see prefix rule",
    "167829573": "described McKean County",
    "167854923": "described historical / lunar candidate",
    "165823973": "slash-pair member",
    "1658729343": "slash-pair refined member",
    "165892323": "Channel/Guernsey family candidate",
    "165872943": "Channel/Guernsey family candidate",
    "165872393": "frozen probe P5",
    "165879633": "frozen probe P6",
}

#: Vectors the source describes as lunar or historical-lunar.
LUNAR_CANDIDATES = {"167854923"}


def public_wires() -> dict:
    out = {}
    try:
        from r1012.corpus import golden28
        for w in golden28()["wires"]:
            out[str(w)] = "golden28"
    except Exception:                       # pragma: no cover
        pass
    try:
        from r1013.exact_cover import WIRES_19
        for w in WIRES_19:
            out.setdefault(str(w), "legacy19")
    except Exception:                       # pragma: no cover
        pass
    return out


def private_wires(enable: bool = False) -> dict:
    """Operator-authorised path vectors, read from the private lane.

    Returns {} unless explicitly enabled AND the environment variable
    RGCS_R1016_PATH_VECTORS=authorized is set, so that no ordinary
    import can pull private material in by accident.
    """
    if not enable or os.environ.get("RGCS_R1016_PATH_VECTORS") != \
            "authorized":
        return {}
    lane = os.environ.get(PRIVATE_LANE_ENV)
    name = os.environ.get(LEDGER_NAME_ENV)
    if not lane or not name:
        return {}
    led = Path(lane) / name
    if not led.is_file():
        return {}
    out = {}
    for line in led.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out[str(json.loads(line)["wire"])] = "path_vector"
    return out


def inventory(include_private: bool = False) -> dict:
    wires = dict(public_wires())
    priv = private_wires(include_private)
    for w, src in priv.items():
        wires.setdefault(w, src)
    rows = []
    for w, src in sorted(wires.items()):
        rows.append({
            "wire": w, "corpus": src,
            "source_note": SOURCE_NOTES.get(w, "unlabelled"),
            "labelled": w in SOURCE_NOTES,
            "body_profile": ("MOON" if w in LUNAR_CANDIDATES
                             else "EARTH"),
            "digits": len(w),
            "has_8_or_9": bool(re.search(r"[89]", w)),
            "bit_length": int(w).bit_length(),
            "is_private_path_vector": src == "path_vector",
        })
    return {"schema": "rgcs.r1016.inventory.v1",
            "total": len(rows),
            "public": sum(1 for r in rows
                          if not r["is_private_path_vector"]),
            "path_vectors": sum(1 for r in rows
                                if r["is_private_path_vector"]),
            "labelled": sum(1 for r in rows if r["labelled"]),
            "unlabelled": sum(1 for r in rows if not r["labelled"]),
            "lunar_candidates": sorted(LUNAR_CANDIDATES),
            "rows": rows}
