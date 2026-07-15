#!/usr/bin/env python3
"""Generate the optical/nonreciprocal reference-mechanism comparison table
(Agent 06 deliverable) from the frozen provenance ledgers.

Reads references/source_registry.yaml and references/equation_provenance.yaml
and writes docs/generated/OPTICAL_MECHANISM_COMPARISON.md. Deterministic:
same inputs -> byte-identical output (pinned by
tests/unit/test_rscs_optical.py::test_comparison_table_up_to_date).

Usage:  python tools/generate_optical_comparison.py [--check]
  --check: exit 1 if the committed file differs from the regenerated one.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "docs" / "generated" / "OPTICAL_MECHANISM_COMPARISON.md"

#: The optical/nonreciprocal source set Agent 06 integrates (SRC-3-01..06;
#: the NHT/HAL sources 07/08 belong to the memory bridge, not this table).
OPTICAL_SOURCES = ["SRC-3-01", "SRC-3-02", "SRC-3-03",
                   "SRC-3-04", "SRC-3-05", "SRC-3-06"]


def _load(path: Path):
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _cell(text: str) -> str:
    """Escape a YAML string for a one-line markdown table cell."""
    return " ".join(str(text).split()).replace("|", "\\|")


def generate() -> str:
    sources = _load(REPO / "references" / "source_registry.yaml")
    prov = _load(REPO / "references" / "equation_provenance.yaml")

    src_by_id = {s["source_id"]: s for s in sources["sources"]}
    eqs_by_src: dict[str, list] = {}
    for eq in prov["equations"]:
        eqs_by_src.setdefault(eq["source_id"], []).append(eq)

    lines = [
        "# Optical / Nonreciprocal Reference-Mechanism Comparison",
        "",
        "**GENERATED FILE — do not edit.** Regenerate with",
        "`python tools/generate_optical_comparison.py`. Source of truth:",
        "`references/source_registry.yaml` + `references/equation_provenance.yaml`",
        "(frozen, Agent 02). Compiled by Agent 06.",
        "",
        "Every mechanism below achieves nonreciprocity or mode conversion via",
        "an ACTIVE ingredient (bias field, drive, nonlinearity, magneto-optic",
        "material) that alpha-quartz is **not** claimed to have. The",
        "`forbidden transfer` column is binding (EXCLUSION_MATRIX): only the",
        "`reusable math` crosses into RSCS, always re-derived and re-tested.",
        "The pre-registered null for quartz directional tests is NO asymmetry",
        "(DECISION_LOG D6-003).",
        "",
    ]

    for sid in OPTICAL_SOURCES:
        src = src_by_id[sid]
        title = src.get("title", sid)
        cite = src.get("citation", src.get("reference", ""))
        weight = src.get("class", src.get("weight", ""))
        lines += [f"## {sid} — {_cell(title)}", ""]
        meta = []
        if cite:
            meta.append(f"*{_cell(cite)}*")
        if weight:
            meta.append(f"registry class: **{_cell(weight)}**")
        if meta:
            lines += ["  \n".join(meta), ""]
        lines += [
            "| EP id | Mechanism / equation | Reusable math (adapted) | "
            "Forbidden transfer (binding) | RSCS home |",
            "|---|---|---|---|---|",
        ]
        for eq in eqs_by_src.get(sid, []):
            lines.append(
                f"| {eq['prov_id']} | {_cell(eq['name'])} | "
                f"{_cell(eq['reusable_math'])} | "
                f"{_cell(eq['forbidden_transfer'])} | "
                f"{_cell(eq['target_rscs'])} |")
        lines.append("")

    lines += [
        "## Cross-mechanism summary",
        "",
        "| Ingredient that breaks reciprocity | Which sources | Quartz "
        "status |",
        "|---|---|---|",
        "| Travelling acoustic drive (phase-matched, momentum-biased) | "
        "SRC-3-01, SRC-3-02 | possible to APPLY externally; effect size "
        "must be computed, not imported (RSCS-O.19) |",
        "| Signal-induced chi(3) spin term | SRC-3-04 | not claimed for "
        "quartz; modelled as the s_z term of RSCS-O.22 with null default |",
        "| Doppler-selected atomic population | SRC-3-05 | no quartz "
        "analogue; abstracted to the selection coordinate RSCS-C.10 only |",
        "| Magneto-optic bias (TMOKE / latched garnet) | SRC-3-03, "
        "SRC-3-06 | quartz is not magneto-optic; delta_beta of RSCS-C.17 "
        "defaults to 0 |",
        "",
        "A passive, lossless, unbiased quartz path is reciprocal. Any "
        "measured asymmetry is HYP (claims H-21/H-23) until it survives the "
        "reversal battery.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    text = generate()
    if "--check" in sys.argv[1:]:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != text:
            print(f"STALE: {OUT} differs from regenerated content")
            return 1
        print(f"OK: {OUT} is up to date")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
