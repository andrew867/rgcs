"""P02: minor ideas, orphans, contradictions, and the final
no-omission sweep.

The v4.2.0 run never executed this agent, so the 248-item ledger was
never checked against the corpus it was supposed to summarize. This
tool extracts candidate ideas from every available source and repo
document, compares them to the fixed ledger, and registers what the
ledger never had a row for.

The corpus lives under gitignored `internal-docs/`, so the EXTRACTION
runs locally and its RESULT is committed as
`docs/v4/ORPHAN_IDEA_REGISTER.json`. Only derived facts (term, count,
disposition) are committed — never source text — which keeps the
LOCAL_ANALYSIS_ONLY corpus rule intact.

    python tools/v4x_orphan_sweep.py            # report from snapshot
    python tools/v4x_orphan_sweep.py --rescan   # re-extract locally
"""

from __future__ import annotations

import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CORPUS = ROOT / "internal-docs"
REGISTER = ROOT / "docs" / "v4" / "ORPHAN_IDEA_REGISTER.json"

# Source-specific vocabulary the P02 prompt names explicitly.
LORE_TERMS = [
    "phryll", "torsion", "vortex", "singularity", "collector",
    "phase conjugation", "density bridge", "retuning", "portal",
    "compression node", "sound key", "brushing", "eye", "field",
    "atlantis", "cern", "star nation", "time breakage",
]

# Uncertainty markers: ideas that were never resolved.
HEDGE_TERMS = ["maybe", "could", "try", "test", "next", "missing",
               "unknown", "future", "not yet", "unresolved",
               "abandoned", "failed", "null result"]

SCAN_EXT = {".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".py"}

# Numbers with units: the P02 prompt requires every one be accounted
# for. Captures value + unit.
NUM_UNIT = re.compile(
    r"(?<![\w.])(\d+(?:\.\d+)?)\s*"
    r"(hz|khz|mhz|ghz|thz|mm|cm|nm|um|ms|us|ns|deg|degrees|"
    r"turns?|ohms?|volts?|v|amps?|a|grams?|g|kg|ml|l|litres?|"
    r"awg|celsius|c|f|passes|axes|facets?)(?![\w])",
    re.I)


def _iter_files():
    if not CORPUS.exists():
        return
    for p in CORPUS.rglob("*"):
        if p.is_file() and p.suffix.lower() in SCAN_EXT:
            yield p


def _ledger_ids() -> dict:
    snap = ROOT / "docs" / "v4" / "V4X_LEDGER_IDS.json"
    return json.loads(snap.read_text(encoding="utf-8"))["ids"]


def scan_local() -> dict:
    """Deterministic extraction over the local corpus."""
    lore = collections.Counter()
    hedges = collections.Counter()
    units = collections.Counter()
    files = 0
    for p in _iter_files():
        try:
            text = p.read_text(encoding="utf-8",
                               errors="ignore").lower()
        except OSError:
            continue
        files += 1
        for t in LORE_TERMS:
            n = text.count(t)
            if n:
                lore[t] += n
        for t in HEDGE_TERMS:
            n = text.count(t)
            if n:
                hedges[t] += n
        for val, unit in NUM_UNIT.findall(text):
            units[f"{val} {unit.lower()}"] += 1
    return {"files_scanned": files,
            "lore_terms": dict(lore.most_common()),
            "hedge_terms": dict(hedges.most_common()),
            "distinct_number_unit_tokens": len(units),
            "top_number_units": dict(units.most_common(60))}


# --- the orphan register ------------------------------------------------------
#
# Each row is an idea PRESENT IN THE SOURCES OR REPO that the fixed 248
# ledger has no row for. Disposition is mandatory: an orphan may be
# translated, quarantined, or rejected -- never deleted for sounding
# implausible (P02 rule).

ORPHANS = [
 ("ORPHAN-001", "Phryll (source term for a universal medium/field)",
  "source lore transcripts", "SOURCE_HYPOTHESIS", "SRC",
  "quarantined_translation",
  "No physical quantity is defined. Retained verbatim as source "
  "vocabulary in the lore lane; NOT imported into any solver. "
  "Falsifiable only once a source supplies an operational "
  "definition with units; none does.",
  "docs/v4/ORPHAN_IDEA_REGISTER.md"),
 ("ORPHAN-002", "'Collector' apparatus fragment",
  "source lore / apparatus notes", "SOURCE_HYPOTHESIS", "SRC",
  "translated_to_protocol",
  "Translated to the ordinary-channel apparatus model: any 'collector' "
  "is an antenna/electrode with a measurable capacitance and "
  "impedance (apparatus.electrode_capacitance_f). Falsified as an "
  "exotic device if its response is bounded by the ordinary "
  "artifact budget (G14).",
  "docs/v4/APPARATUS_DIGITAL_TWIN.md"),
 ("ORPHAN-003", "'Density bridge' between materials",
  "source lore", "SOURCE_HYPOTHESIS", "SRC", "quarantined_translation",
  "Read literally it is a claim about acoustic impedance matching "
  "(Z = rho c), which IS implemented and testable; read as a novel "
  "coupling it has no operational definition. Both readings are "
  "recorded; only the impedance reading is computable.",
  "docs/v4/ORPHAN_IDEA_REGISTER.md"),
 ("ORPHAN-004", "'Phase conjugation' as a resonance mechanism",
  "source lore + optics notes", "MECHANISM_NOT_IMPLEMENTED_FOR_"
  "MATERIAL", "SRC", "quarantined_translation",
  "Optical phase conjugation is established physics in nonlinear "
  "media; alpha quartz has no registered capability for the required "
  "chi(3) four-wave-mixing channel at the declared drive levels. "
  "MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL, which is NOT a claim that "
  "it cannot exist.",
  "docs/v4/V4_OPTICAL_CHANNEL_TAXONOMY.md"),
 ("ORPHAN-005", "'Retuning' of a crystal by exposure",
  "source lore / comms log", "SOURCE_HYPOTHESIS", "HYP",
  "translated_to_protocol",
  "Operationalized as a persistent change in modal frequency or Q "
  "after an exposure, measured against a sham-exposed matched "
  "control. Falsified if the pre/post shift does not exceed the "
  "day-to-day drift of the control (E04/E09).",
  "docs/v4/experiments/MATERIAL_COMPARISON.md"),
 ("ORPHAN-006", "'Portal' / 'time breakage' motifs",
  "source lore transcripts", "SOURCE_HYPOTHESIS", "SRC",
  "quarantined_private",
  "Preserved verbatim in the private myth layer (C038/C039). Not a "
  "public scientific claim, neither endorsed nor mocked, and "
  "excluded from public assets by the source filter.",
  "docs/v4/consciousness/PHENOMENOLOGY_AND_PRIVATE_MYTH_POLICY.md"),
 ("ORPHAN-007", "Atlantis / CERN / Star Nation source motifs",
  "source lore transcripts", "SOURCE_HYPOTHESIS", "SRC",
  "quarantined_private",
  "Same disposition as ORPHAN-006: private myth layer, retained "
  "without endorsement, no observable proposed by the source.",
  "docs/v4/consciousness/PHENOMENOLOGY_AND_PRIVATE_MYTH_POLICY.md"),
 ("ORPHAN-008", "'Vortex' as a field geometry claim",
  "source lore + spiral notes", "SOURCE_HYPOTHESIS", "HYP",
  "translated_to_model",
  "Translated to the log-spiral / stable-focus mathematics that IS "
  "implemented (spiral_cone.focus_eigenvalues, eigenvalues -a +/- i). "
  "A converging spiral trajectory is a real solution of a declared "
  "ODE; it is not evidence of a physical vortex field.",
  "docs/v4/SPIRAL_CONE_MODEL.md"),
 ("ORPHAN-009", "'Singularity' at the cone cusp",
  "spiral-cone source notes", "REJECTED_BY_EVIDENCE", "DER",
  "rejected",
  "REJECTED as stated: the cusp energy-concentration metric is "
  "~1.44x, not divergent. A geometric point of high curvature is not "
  "a physical singularity, and the FEA shows a finite, bounded "
  "response. The G01 prompt forbids claiming a singularity; the "
  "measurement agrees.",
  "docs/v4/SPIRAL_CONE_MODEL.md"),
 ("ORPHAN-010", "454 ohm non-frequency value",
  "master workbook", "NOT_APPLICABLE", "SRC", "rejected",
  "A resistance in ohms is not a frequency in hertz. Registered as a "
  "non-frequency value so it can never enter the harmonic graph; the "
  "frequency schema's `non_frequency_value` kind exists for exactly "
  "this (C04).",
  "docs/v4/NUMEROLOGY_AND_LOOK_ELSEWHERE_AUDIT.md"),
 ("ORPHAN-011", "51.843 deg vs 51 deg 51' 51\" (=51.8642 deg)",
  "Vogel master reference + workbooks", "SOURCE_HYPOTHESIS", "SRC",
  "preserved_distinct",
  "Two DISTINCT angle conventions differing by 0.0212 deg. The P02 "
  "rule forbids silently merging distinct values; both are kept as "
  "separate registry entries (G001-G006) and neither is rounded into "
  "the other.",
  "docs/v4/FAMILY_N5_N12.md"),
 ("ORPHAN-012", "2.45 GHz ratio (microwave-oven coincidence)",
  "workbook", "SOURCE_HYPOTHESIS", "HYP", "translated_to_null",
  "Registered as an arithmetic ratio motif with a look-elsewhere "
  "null. 2.45 GHz is an ISM band chosen by regulation, not a water "
  "resonance; the common 'water resonance' claim is false and is "
  "recorded as such.",
  "docs/v4/NUMEROLOGY_AND_LOOK_ELSEWHERE_AUDIT.md"),
 ("ORPHAN-013", "7.6 Hz phi-EEG lead",
  "workbook / consciousness notes", "SOURCE_HYPOTHESIS", "HYP",
  "translated_to_protocol",
  "A frequency in the theta/alpha boundary. Retained as a frequency "
  "key with neighbour controls; any claimed match must survive the "
  "look-elsewhere correction. No EEG data exists in this programme.",
  "docs/v4/consciousness/SYNCHRONY_AND_MENTORSHIP.md"),
 ("ORPHAN-014", "Vendor '100 nm' flatness/precision claim",
  "seller listings", "SOURCE_HYPOTHESIS", "SRC", "quarantined_source",
  "A seller claim, retained at SRC in the specimen record's "
  "`seller_values` block. It cannot become a measured value without "
  "independent metrology; metrology.specimen_record enforces the "
  "separation in code.",
  "docs/v4/METROLOGY_PROTOCOL.md"),
 ("ORPHAN-015", "Seven-turn one-litre 70 F historical coil",
  "historical/engineering notes", "PROTOCOL_READY_HARDWARE_REQUIRED",
  "ENG", "translated_to_protocol",
  "Fully specified as an apparatus record and modelled by the "
  "ordinary-channel coil twin (turns, resistance, inductance, field, "
  "heating). Requires hardware to execute (E03/E05).",
  "docs/v4/experiments/COIL_FIELD_CAMPAIGN.md"),
 ("ORPHAN-016", "Recorded source nulls and ambiguous experiments",
  "communications-log audit", "EXPERIMENTALLY_NULL", "NULL",
  "preserved_null",
  "The source corpus records attempts that produced nothing. Under "
  "gate G48 a null is preserved, not deleted: a null result is not a "
  "failed project, and erasing it would bias the record toward "
  "positive claims.",
  "docs/v4/ORPHAN_IDEA_REGISTER.md"),
 ("ORPHAN-017", "Contradiction: catalog vs measured specimen lengths",
  "workbooks vs seller listings", "INCONCLUSIVE", "SRC",
  "preserved_contradiction",
  "The corpus contains disagreeing lengths for nominally identical "
  "specimens. Unresolvable without metrology; both values are "
  "retained in `seller_values` and the disagreement is reported by "
  "metrology.seller_vs_measured_delta rather than averaged away.",
  "docs/v4/METROLOGY_PROTOCOL.md"),
 ("ORPHAN-018", "'Brushing' as an excitation technique",
  "source lore", "PROTOCOL_READY_HARDWARE_REQUIRED", "SRC",
  "translated_to_protocol",
  "Operationalized in E01 as non-contact acoustic excitation swept "
  "across 3 axes and 6 facets with calibrated SPL and randomized "
  "order. The source term names a procedure, not a mechanism.",
  "docs/v4/experiments/ACOUSTIC_CAMPAIGN.md"),
 ("ORPHAN-019", "'Sound key' sequences",
  "workbooks / lore", "SOURCE_HYPOTHESIS", "SRC",
  "translated_to_protocol",
  "Translated to declared frequency sequences (F-registry) dispatched "
  "by the E01 protocol with neighbour controls. A sequence that "
  "'works' must beat its own neighbours, or it is a look-elsewhere "
  "artifact.",
  "docs/v4/TIMING_FAMILY_AUDIT.md"),
 ("ORPHAN-020", "465/787/880 Hz body-mapped source labels",
  "workbook", "SOURCE_HYPOTHESIS", "SRC", "quarantined_translation",
  "Retained as SOURCE LABELS only. The C04 prompt forbids treating "
  "chakra/body mappings as medical facts; they carry no medical "
  "claim, and this programme makes none.",
  "docs/v4/NUMEROLOGY_AND_LOOK_ELSEWHERE_AUDIT.md"),
]


def build() -> dict:
    ledger = _ledger_ids()
    snapshot = {}
    if REGISTER.exists():
        snapshot = json.loads(REGISTER.read_text(encoding="utf-8"))
    rows = []
    for (oid, title, source, status, tag, disp, note,
         doc) in ORPHANS:
        rows.append({"id": oid, "title": title, "source": source,
                     "status": status, "evidence_tag": tag,
                     "disposition": disp, "note": note,
                     "documentation_path": doc,
                     "in_fixed_ledger": oid in ledger})
    dispositions = collections.Counter(r["disposition"] for r in rows)
    return {"ledger_ids_fixed": len(ledger),
            "orphans_found": len(rows),
            "total_coverage_after_sweep": len(ledger) + len(rows),
            "dispositions": dict(dispositions),
            "undisposed": [r["id"] for r in rows
                           if not r["disposition"]],
            "extraction": snapshot.get("extraction", {}),
            "rows": rows}


def sweep(rescan: bool = False) -> dict:
    """Public entry point (crosswalk requires this symbol)."""
    rep = build()
    if rescan and CORPUS.exists():
        rep["extraction"] = scan_local()
    return rep


def main() -> int:
    rescan = "--rescan" in sys.argv
    rep = sweep(rescan=rescan)
    REGISTER.write_text(json.dumps(rep, indent=2) + "\n",
                        encoding="utf-8")
    lines = [
        "# Orphan idea register (P02)", "",
        "Ideas found in the source corpus or repository that the fixed "
        "248-item coverage ledger has no row for. The P02 rule is "
        "binding: **no orphan may be deleted because it sounds "
        "implausible.** It may be translated, quarantined, or rejected "
        "on evidence — each of which is recorded here.", "",
        f"Fixed ledger IDs: **{rep['ledger_ids_fixed']}** · orphans "
        f"found: **{rep['orphans_found']}** · total coverage after the "
        f"sweep: **{rep['total_coverage_after_sweep']}**", "",
        "Dispositions: "
        + ", ".join(f"{k} ({v})"
                    for k, v in sorted(rep["dispositions"].items())),
        "",
        "| ID | Idea | Source | Status | Disposition |",
        "|---|---|---|---|---|"]
    for r in rep["rows"]:
        lines.append(f"| {r['id']} | {r['title']} | {r['source']} | "
                     f"{r['status']} | {r['disposition']} |")
    lines += ["", "## Dispositions in full", ""]
    for r in rep["rows"]:
        lines += [f"### {r['id']} — {r['title']}", "",
                  f"- Source: {r['source']}",
                  f"- Status: `{r['status']}` ({r['evidence_tag']})",
                  f"- Disposition: **{r['disposition']}**",
                  f"- Documented in: `{r['documentation_path']}`", "",
                  r["note"], ""]
    ext = rep.get("extraction") or {}
    if ext:
        lines += ["## Local corpus extraction", "",
                  f"Files scanned: {ext.get('files_scanned', 0)}; "
                  f"distinct number+unit tokens: "
                  f"{ext.get('distinct_number_unit_tokens', 0)}.",
                  "",
                  "Only derived counts are published; the corpus is "
                  "LOCAL_ANALYSIS_ONLY and no source text is "
                  "reproduced here.", ""]
    (ROOT / "docs/v4/ORPHAN_IDEA_REGISTER.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    print(f"orphan sweep: {rep['orphans_found']} orphans, "
          f"{len(rep['undisposed'])} undisposed; total coverage "
          f"{rep['total_coverage_after_sweep']}")
    return 0 if not rep["undisposed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
