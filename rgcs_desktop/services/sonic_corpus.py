"""Frequency Key Studio corpus tools (v1.2): a metadata-only corpus
store, duplicate clustering, and recipe recommendation.

Everything operates on source_recipe records (schema-valid dicts from
``sonic_ingest``). No audio, no network — records in, records out.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from rgcs_core.provenance import json_dumps

from rgcs_desktop.services.sonic_recipes import load_recipes

#: near-duplicate title threshold (token Jaccard similarity)
_TITLE_SIMILARITY = 0.8


class CorpusStore:
    """A JSON-file corpus of source_recipe records, deduplicated by
    URL. Load/add/save/export — nothing else touches the file."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.records: list[dict] = []
        if self.path.is_file():
            body = json.loads(self.path.read_text(encoding="utf-8"))
            self.records = list(body.get("records", []))

    def add(self, record: dict) -> bool:
        """Add a parsed record; returns False for duplicate URLs."""
        url = record.get("url")
        if any(r.get("url") == url for r in self.records):
            return False
        self.records.append(record)
        return True

    def save(self) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        body = {"corpus_kind": "frequency_key_studio_sources",
                "note": "Metadata only. Claimed uses are recorded from "
                        "source text, not endorsed.",
                "records": self.records}
        self.path.write_text(json_dumps(body, indent=2, sort_keys=True),
                             encoding="utf-8")
        return self.path

    def to_csv(self, out_path: str | Path) -> Path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["source_id", "url", "platform", "title",
                        "frequencies_hz", "claimed_uses",
                        "recipe_type_guess", "review_status"])
            for r in self.records:
                w.writerow([
                    r.get("source_id", ""), r.get("url", ""),
                    r.get("platform", ""), r.get("title", ""),
                    "; ".join(f"{f['hz']:g}" for f in
                              r.get("extracted_frequencies_hz", [])),
                    "; ".join(r.get("claimed_uses", [])),
                    r.get("recipe_type_guess", ""),
                    r.get("review_status", ""),
                ])
        return out_path


# ------------------------------------------------------------ clustering

def _frequency_signature(record: dict) -> tuple:
    """Carrier/beat signature: carriers rounded to whole Hz, beats to
    0.1 Hz — recordings of the same recipe cluster together."""
    carriers, beats = [], []
    for f in record.get("extracted_frequencies_hz", []):
        if f.get("role") in ("carrier_candidate",):
            carriers.append(round(float(f["hz"])))
        elif f.get("role") in ("beat_target_candidate",):
            beats.append(round(float(f["hz"]), 1))
    return tuple(sorted(set(carriers))), tuple(sorted(set(beats)))


def _title_tokens(title: str) -> set[str]:
    return {t for t in "".join(
        c.lower() if c.isalnum() or c == "." else " "
        for c in title).split() if t}


def _similar_titles(a: str, b: str) -> bool:
    ta, tb = _title_tokens(a), _title_tokens(b)
    if not ta or not tb:
        return False
    return len(ta & tb) / len(ta | tb) >= _TITLE_SIMILARITY


def cluster_corpus(records: list[dict]) -> list[dict]:
    """Group records into duplicate clusters.

    Two records cluster when they share a non-empty frequency signature,
    or when their titles are near-duplicates. Returns clusters sorted
    by size (largest first): {signature, records, representative}.
    """
    clusters: list[dict] = []
    for record in records:
        sig = _frequency_signature(record)
        placed = False
        for cluster in clusters:
            same_sig = (sig == cluster["signature"]
                        and (sig[0] or sig[1]))
            near_title = any(_similar_titles(record.get("title", ""),
                                             r.get("title", ""))
                             for r in cluster["records"])
            if same_sig or near_title:
                cluster["records"].append(record)
                placed = True
                break
        if not placed:
            clusters.append({"signature": sig, "records": [record]})
    for cluster in clusters:
        cluster["representative"] = cluster["records"][0]
        cluster["size"] = len(cluster["records"])
    return sorted(clusters, key=lambda c: -c["size"])


# -------------------------------------------------------- recommendation

def recommend_recipes(record: dict, top_n: int = 3) -> list[dict]:
    """Rank seed recipes against a corpus record.

    Scoring (declared, deterministic): +2 per carrier within 2%, +2 per
    beat within 5%, +1 per claimed-use word appearing in the recipe's
    intent/family/title. Returns [{recipe, score, reasons}] with
    score > 0, best first.
    """
    carriers = [float(f["hz"]) for f in
                record.get("extracted_frequencies_hz", [])
                if f.get("role") == "carrier_candidate"]
    beats = [float(f["hz"]) for f in
             record.get("extracted_frequencies_hz", [])
             if f.get("role") == "beat_target_candidate"]
    uses = [u.lower() for u in record.get("claimed_uses", [])]

    ranked = []
    for recipe in load_recipes():
        score, reasons = 0, []
        for c in carriers:
            if abs(recipe["carrier_hz"] - c) <= 0.02 * c:
                score += 2
                reasons.append(f"carrier {recipe['carrier_hz']:g} Hz "
                               f"matches {c:g} Hz")
        for b in beats:
            if abs(recipe["beat_hz"] - b) <= 0.05 * max(b, 0.1):
                score += 2
                reasons.append(f"beat {recipe['beat_hz']:g} Hz matches "
                               f"{b:g} Hz")
        recipe_text = " ".join(str(recipe.get(k, "")) for k in
                               ("intent", "family", "title")).lower()
        for use in uses:
            for word in use.split():
                if len(word) > 3 and word in recipe_text:
                    score += 1
                    reasons.append(f"claimed use '{use}' overlaps "
                                   f"recipe intent")
                    break
        if score > 0:
            ranked.append({"recipe": recipe, "score": score,
                           "reasons": sorted(set(reasons))})
    ranked.sort(key=lambda r: (-r["score"], r["recipe"]["recipe_id"]))
    return ranked[:top_n]
