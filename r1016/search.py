"""R10.16 — exhaustive discrete model search and the strict gate."""

from __future__ import annotations

import numpy as np

from cwatlas.r1085a import final_projection as fp
from r1016.project import (STRICT_ANCHORS, STRICT_GATE_RMS_KM,
                           RootVariant, anchor_rms, enumerate_variants)
from r1016.views import candidates

#: The frozen root also reads the wire as a plain decimal integer.
#: That reading is none of the five declared views, so it is carried
#: explicitly as the baseline rather than smuggled into view C.
FROZEN_BASELINE_VIEW = "Z_FULL_WIRE_DECIMAL_FROZEN_BASELINE"


def view_word_maps(wires) -> list[dict]:
    """All (view, window) -> {wire: word} maps across the wire set."""
    per_wire = {w: candidates(w) for w in wires}
    keys = set()
    for cs in per_wire.values():
        for c in cs:
            if c.get("word") is not None:
                keys.add((c["view"], c.get("window")))
    maps = []
    for view, window in sorted(keys, key=lambda t: (t[0], t[1] or -1)):
        words = {}
        for w, cs in per_wire.items():
            for c in cs:
                if c["view"] == view and c.get("window") == window \
                        and c.get("word") is not None:
                    words[w] = c["word"]
        maps.append({"view": view, "window": window, "words": words,
                     "coverage": len(words)})
    # frozen baseline: the wire itself, when it fits 30 bits
    base = {w: int(w) for w in wires if int(w) < (1 << 30)}
    if base:
        maps.append({"view": FROZEN_BASELINE_VIEW, "window": None,
                     "words": base, "coverage": len(base)})
    return maps


def run(contexts=("TRAINED",), epoch_year: float = 2025.0,
        progress=None) -> dict:
    """Exhaust every (numeric view x window) x (discrete root variant)."""
    frame, receipt = fp.training_alignment(epoch_year)
    rotations = {"TRAINED": np.asarray(frame.rotation, float)}
    for ctx, rot in fp.sealed_contexts().items():
        if ctx in contexts or "ALL_SEALED" in contexts:
            rotations[ctx] = np.asarray(rot, float)
    use_ctx = tuple(c for c in rotations if c in contexts
                    or "ALL_SEALED" in contexts)
    if not use_ctx:
        use_ctx = ("TRAINED",)
    maps = view_word_maps(list(STRICT_ANCHORS))
    variants = enumerate_variants(use_ctx)
    results, evaluated = [], 0
    for m in maps:
        for v in variants:
            rot = rotations.get(v.context)
            if rot is None:
                continue
            fit = anchor_rms(v, rot, m["words"])
            evaluated += 1
            if fit["rms_km"] is not None:
                results.append({
                    "view": m["view"], "window": m["window"],
                    "variant_id": v.id, "variant": v,
                    "anchor_coverage": fit["covered"],
                    "rms_km": fit["rms_km"], "max_km": fit.get("max_km"),
                    "passes_gate": fit["passes_gate"], "rows": fit["rows"]})
            if progress and evaluated % 500 == 0:
                progress(evaluated)
    results.sort(key=lambda r: (-r["anchor_coverage"], r["rms_km"]))
    survivors = [r for r in results if r["passes_gate"]]
    return {
        "schema": "rgcs.r1016.model-search.v1",
        "views_tested": sorted({m["view"] for m in maps}),
        "view_window_maps": len(maps),
        "root_variants": len(variants),
        "models_evaluated": evaluated,
        "models_with_full_anchor_coverage":
            sum(1 for r in results
                if r["anchor_coverage"] == len(STRICT_ANCHORS)),
        "gate_rms_km": STRICT_GATE_RMS_KM,
        "survivors": survivors,
        "survivor_count": len(survivors),
        "best": results[0] if results else None,
        "top": results[:25],
        "training_receipt_context": receipt.get("chosen_context"),
        "verdict": ("STRICT_ANCHOR_GATE_PASSED" if survivors
                    else "STRICT_ANCHOR_GATE_FAILED_ALL_DISCRETE_VARIANTS"),
    }
