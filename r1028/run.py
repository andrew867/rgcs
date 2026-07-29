"""R10.28 / R10.29 — reproducible run driver.

Run:  python -m r1028.run <output_dir>
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from r1016.quarantine import QUARANTINED
from r1028 import (checksum, crystal1031, fieldsum, freq1030, payload,
                   research, sspp221, vectors)


def _write(path: Path, rows, keys=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys = keys or sorted({k for r in rows for k in r})
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (json.dumps(v) if isinstance(v, (list, dict))
                            else v) for k, v in r.items()})


def main(outdir: str) -> dict:
    out = Path(outdir)
    data, reports = out / "data", out / "reports"

    # --- 36-bit codec test results ---------------------------------
    dec = vectors.decode_all()
    codec_rows = []
    for r in dec["rows"]:
        for row in r["rows"]:
            codec_rows.append({"label": r["label"], "raw": r["raw"], **row})
    _write(data / "36bit_codec_test_results.csv", codec_rows)

    # --- candidate vector decode -----------------------------------
    _write(data / "candidate_vector_decode_results.csv",
           [{k: v for k, v in r.items() if k != "rows"} for r in dec["rows"]])

    # --- checksum search -------------------------------------------
    ex = [(lab, int(raw), raw) for lab, raw in vectors.CANDIDATES]
    cs = checksum.search(ex)
    _write(data / "checksum_formula_search.csv", cs["rows"])

    # --- long payload ----------------------------------------------
    pl = payload.report()
    _write(data / "long_payload_decode_attempts.csv", pl["numeric_attempts"])
    _write(data / "long_payload_block_classification.csv", pl["blocks"])

    # --- SSPP / OAM -------------------------------------------------
    sp = sspp221.report()
    _write(data / "sspp_oam_221_modulation_table.csv",
           sspp221.modulation_table())
    _write(data / "sspp_oam_35_position_sequences.csv",
           [{"step_order": i, "position_index": p}
            for i, p in enumerate(sp["stepping_sequence"])])
    _write(data / "sspp_oam_resonator_variant_matrix.csv",
           sspp221.resonator_matrix())
    _write(data / "sspp_oam_bench_variants.csv", sspp221.variants())
    _write(data / "frequency_downshift_ratio_tests.csv",
           sspp221.downshift_ratio_tests())

    # --- research lane ----------------------------------------------
    rs = research.report()
    _write(data / "bird_frequency_ratio_research_table.csv", rs["questions"])
    _write(data / "external_research_claims_state.csv", rs["claims"])
    _write(data / "research_formula_slots.csv", rs["formula_slots"])

    # --- R10.30 frequency law + Apollo/patent lanes ----------------
    fq = freq1030.report()
    _write(data / "frequency_arithmetic_r1030.csv", fq["tests"])
    _write(data / "power_of_two_recurrences_r1030.csv",
           fq["power_of_two_recurrences"])
    _write(data / "apollo_lunar_reference_lane_r1030.csv", fq["apollo_lane"])
    _write(data / "patent_window_july1969_r1030.csv",
           [{k: v for k, v in fq["patent_window"].items() if k != "results"}])
    (data / "freq1030_report.json").write_text(
        json.dumps(fq, indent=2), encoding="utf-8")

    # --- R10.31 decoded-field checksum + crystal stack -------------
    fs = fieldsum.search([(lab, int(raw)) for lab, raw in vectors.CANDIDATES])
    _write(data / "field_checksum_search_r1031.csv",
           [{"rule": r} for r in fs["survivors"]])
    _write(data / "field_checksum_degeneracy_r1031.csv", [fs["degeneracy"]])
    cr = crystal1031.report()
    _write(data / "crystal_frequency_stack_r1031.csv", cr["stack_roles"])
    _write(data / "lunar_root_lane_r1031.csv", cr["lunar_root_lane"])
    _write(data / "attestation_40ghz_r1031.csv", [cr["attestation_40ghz"]])
    (data / "r1031_field_checksum.json").write_text(
        json.dumps({k: v for k, v in fs.items() if k != "survivors"},
                   indent=2), encoding="utf-8")
    (data / "r1031_crystal_stack.json").write_text(
        json.dumps(cr, indent=2), encoding="utf-8")

    # --- quarantine receipt -----------------------------------------
    qr = []
    for f in sorted(data.glob("*.csv")):
        if f.name == "quarantine_clean_receipt.csv":
            continue
        txt = f.read_text(encoding="utf-8", errors="ignore")
        hits = [v for v in QUARANTINED if v in txt]
        qr.append({"artifact": f.name,
                   "quarantined_values_present": ";".join(hits),
                   "pass": not hits})
    _write(data / "quarantine_clean_receipt.csv", qr)

    summary = {
        "verdicts": {
            "candidate_vectors": dec["verdict"],
            "checksum": cs["verdict"],
            "long_payload": pl["verdict"],
            "sspp_oam": sp["verdict"],
            "research_lane": rs["verdict"],
        },
        "exact_36_bit_single_block": dec["exact_36_bit_single_block"],
        "fit_established_transport_grammar":
            dec["fit_established_transport_grammar"],
        "core30_surfaceword_compatible": dec["core30_surfaceword_compatible"],
        "checksum_clean_examples": cs["clean_12_octal_examples"],
        "checksum_rules_consistent": cs["rules_consistent"],
        "checksum_identified": cs["identified"],
        "long_payload_is_test_pattern": pl["pangram"]["is_test_pattern"],
        "long_payload_full_base36": pl["alphabet_coverage"][
            "exercises_full_base36_symbol_set"],
        "ring_closes_exactly": sp["ring"]["ring_closes_exactly"],
        "promoted_to_hard_anchor": dec["promoted_to_hard_anchor"],
        "quarantine_all_pass": all(r["pass"] for r in qr),
        "external_facts_asserted": rs["external_facts_asserted_by_this_run"],
        "r1030_frequency_law": fq["verdict"],
        "r1030_f_op_mhz": fq["law"]["F_op_mhz"],
        "r1030_free_constants_fitted": fq["law"]["free_constants_fitted"],
        "r1031_field_checksum": fs["verdict"],
        "r1031_rules_tested": fs["rules_tested"],
        "r1031_survivors": fs["survivor_count"],
        "r1031_expected_false": round(fs["expected_false_survivors"], 2),
        "r1031_effective_examples":
            fs["degeneracy"]["effective_independent_examples"],
        "r1031_phase_lockable": cr["phase_lock"]["phase_lockable"],
        "r1031_is_scale_a_harmonic":
            cr["harmonic_coincidence"]["is_integer_harmonic"],
        "r1031_40ghz_status": cr["attestation_40ghz"]["status"],
    }
    (data / "r1028_run_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    reports.mkdir(parents=True, exist_ok=True)
    (data / "long_payload_report.json").write_text(
        json.dumps(pl, indent=2), encoding="utf-8")
    (data / "sspp221_report.json").write_text(
        json.dumps(sp, indent=2), encoding="utf-8")
    (data / "checksum_report.json").write_text(
        json.dumps(cs, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1]), indent=2))
