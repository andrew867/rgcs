"""Physics-spine loaders and validators -- research lanes, not claims.

Loads the candidate physics-spine entries and the patent/paper seed
ledger, and validates the schema the RC2 integration pack requires:
every entry has a lane, source class, external anchor, observables,
controls, and forbidden claims; every ledger row has a claim
boundary; the positron and dynamical-Casimir lanes stay marked
LONG_TERM_ANALOGY_ONLY with bench priority zero.

This module does schema validation over research metadata. It does
not model, measure, or claim any physical effect. Bench work remains
pending for every lane that has a bench plan at all.
"""

from __future__ import annotations

import csv
import json
import pathlib

_HERE = pathlib.Path(__file__).resolve().parent

SOURCE_CLASSES = (
    "EXTERNAL_TECH_ANCHOR", "PATENT_ANCHOR", "SOURCE_REPORTED_CLAIM",
    "RGCS_DERIVED_MATH", "SIMULATION_RESULT", "BENCH_MEASUREMENT",
    "CONTROL_NULL",
)

PUBLIC_STATUSES = ("PUBLIC_RESEARCH", "LONG_TERM_ANALOGY_ONLY")

#: Lanes that may never grow a bench plan or hardware path.
ANALOGY_ONLY_LANES = ("DCE_ANALOGY", "POSITRON_LANE")

LEDGER_FIELDS = ("id", "type", "title", "identifier_or_url",
                 "source_quality", "relevance_to_rgcs", "claim_boundary")


def load_spine() -> dict:
    return json.loads((_HERE / "physics_spine_entries.json")
                      .read_text(encoding="utf-8"))


def load_ledger_json() -> list[dict]:
    return json.loads((_HERE / "patent_paper_ledger.json")
                      .read_text(encoding="utf-8"))


def load_ledger_csv() -> list[dict]:
    with open(_HERE / "patent_paper_ledger.csv", encoding="utf-8-sig",
              newline="") as handle:
        return list(csv.DictReader(handle))


def validate_spine() -> list[str]:
    """Problems with reasons; empty means the spine schema holds."""
    spine = load_spine()
    approved = set(spine.get("approved_observables", ()))
    problems: list[str] = []
    seen: set[str] = set()
    for entry in spine.get("entries", []):
        eid = entry.get("id", "<missing id>")
        if eid in seen:
            problems.append(f"duplicate entry id {eid}")
        seen.add(eid)
        for field in ("lane", "source_class", "external_anchor",
                      "rgcs_operator", "forbidden_claims", "controls",
                      "public_status"):
            if not entry.get(field):
                problems.append(f"{eid} missing {field}")
        if entry.get("source_class") not in SOURCE_CLASSES:
            problems.append(f"{eid} unknown source_class "
                            f"'{entry.get('source_class')}'")
        if entry.get("public_status") not in PUBLIC_STATUSES:
            problems.append(f"{eid} unknown public_status "
                            f"'{entry.get('public_status')}'")
        for obs in entry.get("observables", []):
            if obs not in approved:
                problems.append(f"{eid} observable '{obs}' is not in "
                                f"the approved first-stage list")
        lane = entry.get("lane")
        if lane in ANALOGY_ONLY_LANES:
            if entry.get("public_status") != "LONG_TERM_ANALOGY_ONLY":
                problems.append(f"{eid} lane {lane} must be "
                                f"LONG_TERM_ANALOGY_ONLY")
            if entry.get("bench_priority") != 0:
                problems.append(f"{eid} lane {lane} must have bench "
                                f"priority 0 (no bench path)")
        elif entry.get("observables"):
            if not entry.get("controls"):
                problems.append(f"{eid} has bench observables but no "
                                f"null/control")
        forbidden = " ".join(entry.get("forbidden_claims", [])).lower()
        if lane not in ANALOGY_ONLY_LANES and "thrust" not in forbidden \
                and "energy" not in forbidden and "proven" not in forbidden \
                and "authenticated" not in forbidden:
            problems.append(f"{eid} forbidden-claims list does not name "
                            f"a physical-claim refusal")
    return problems


def validate_ledger() -> list[str]:
    rows_json = load_ledger_json()
    rows_csv = load_ledger_csv()
    problems: list[str] = []
    for source, rows in (("json", rows_json), ("csv", rows_csv)):
        for row in rows:
            rid = row.get("id", "<missing id>")
            for field in LEDGER_FIELDS:
                if not row.get(field):
                    problems.append(f"{source}:{rid} missing {field}")
    ids_json = [r["id"] for r in rows_json]
    ids_csv = [r["id"] for r in rows_csv]
    if ids_json != ids_csv:
        problems.append("csv and json ledgers disagree on ids or order")
    return problems


__all__ = ["SOURCE_CLASSES", "PUBLIC_STATUSES", "ANALOGY_ONLY_LANES",
           "LEDGER_FIELDS", "load_spine", "load_ledger_json",
           "load_ledger_csv", "validate_spine", "validate_ledger"]
