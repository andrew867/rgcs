"""R10.11 late intake (2026-07-27 23:49-23:55) — E2|S6 frame, 64-state
table search, new vectors, holdout label reveal.

Everything here is registration + bounded testing. Nothing selects a
transition table using geographic labels, British outputs, or sealed
holdouts (candidate tables are tested ONLY against the exact
same-location pairs + the PROBABLE slash pair, as instructed).
"""

from __future__ import annotations

from dataclasses import dataclass

# ------------------------------------------------------------- intake
NEW_VECTORS = {
    1658729343: "probable refined member of slash pair (source '1658729343 / 165823973')",
    165823973: "probable compact member of slash pair",
    165652893: "new vector, no description",
    165879633: "new vector, no description",
    165778933: "new vector, no description",
    165872393: "new vector; source wording implies its middle state is exactly 23 under the true frame",
}

#: "16" radix reading — explicitly UNRESOLVED (do not silently lock).
HEADER_16_READINGS = {
    "decimal_integer": {"value": 16, "binary": "10000", "bits": 5},
    "two_octal_symbols": {"value": "1|6", "binary": "001|110", "bits": 6,
                          "status": "currently favored by wording, NOT locked"},
}

#: Source-reported label reveal for the frozen blind holdout.
HOLDOUT_167854923_REVEAL = {
    "raw": 167854923,
    "revealed_label": "historical lunar-surface location",
    "evidence_class": "SOURCE_REPORTED",
    "revealed_at": "2026-07-27 23:49-23:55 window (operator relay)",
    "frozen_predictions": {
        "v1": (41.730063, -80.833659),
        "v2_folded_diagnostic": (41.711411, -81.337712),
        "note": "both are Earth-surface outputs under Earth-calibrated maps",
    },
    "score": "WRONG_BODY / NON_GEOGRAPHIC_EARTH_OUTCOME — the frozen "
             "Earth-map predictions cannot be correct for a lunar-surface "
             "label; recorded as-is, NO RETUNING (the maps are not "
             "adjusted, the receipts stand)",
    "consistency_notes": [
        "decimal prefix 167 matches the 20:07 Luna sub-space wording (16-7)",
        "old-profile S3=3 and decimal terminal 3 both read 'surface' — "
        "consistent with 'lunar-SURFACE' under body-relative shells",
        "TENSION: 167849523 carries the Erie (Earth) training label yet "
        "shares the 167 prefix — unresolved, recorded, not repaired",
    ],
}


# ---------------------------------------------------- candidate frame
def parse_e2s6_compact(raw: int, header_digits: int = 3) -> dict:
    """Candidate frame E2|S6|S6|S6 over the zero-padded payload after
    clipping a decimal header. E2 is NOT assumed to be a face class."""
    s = str(raw)
    head, pay = s[:header_digits], int(s[header_digits:])
    b = format(pay, "020b") if pay < (1 << 20) else format(pay, "b")
    return {"header": head, "E2": b[:2],
            "states": [int(b[2 + 6 * i:8 + 6 * i], 2) for i in range(3)]
            if len(b) == 20 else None,
            "payload_bits": len(b)}


FRAME_SCAN_RESULT = {
    "claim": "165872393 middle state == 23 under the true frame",
    "tested": "every contiguous 6-bit reading: clips {none,16,165} x "
              "payload widths up to 33 x E2 {front,back,absent} x state "
              "window {front,back}; plus ALL 6-bit substrings of every "
              "variant",
    "result": "NO reading yields 23 anywhere in 165872393 — the value "
              "23 (010111) does not occur as any aligned or unaligned "
              "6-bit window in any tested rendering",
    "conclusion": "the middle-state-23 property requires a "
                  "NON-CONTIGUOUS interleave, a different state "
                  "numbering, or transition-table indirection — "
                  "UNRESOLVED; recorded, not forced",
}

TABLE_SEARCH_RESULT = {
    "instruction": "the existing 64-state lattice-node table IS the "
                   "compact-to-refined transition table (source-reported)",
    "found_in_repo": [
        "rgcs_lab/lattice.py — WS06 64-state coupled-mode RING "
        "(hermitian_ring_hamiltonian: state i couples to (i±1) mod 64, "
        "optional defect state) — the only in-repo 64-state lattice-node "
        "structure",
        "r1010/t11_search_v2.py — six-bit spin*20+face selector split "
        "(R10.10 candidate machinery, not a table)",
    ],
    "found_in_archives": [
        "R7 pack (2026-07-18) A13_38_BIT_HEADER_AND_6X6_DECODER.md + "
        "CW_VECTOR_PRELIMINARY_DECODE.md — the archived 2+6x6 "
        "architecture (E2 + six S6 states over 38-bit CW vectors); the "
        "evident origin of the E2|S6 frame; no explicit 64-row "
        "transition table ships with it",
    ],
    "tests_run": [
        "ring-successor/offset table s -> (s+k) mod 64 for all k in "
        "0..63 against compact(30-bit,5xS6) vs refined(33-bit,first "
        "5xS6) on Stonehenge/Toronto/CYYT/slash pairs: NO k works",
    ],
    "status": "NO in-repo or archived 64-state table reproduces the "
              "compact->refined relation on the exact pairs under the "
              "readings tested; the specific table the source means is "
              "NOT identified — ask the source WHICH lattice-node table "
              "(the WS06 ring? an unshared one?) and the '16' radix "
              "question before further search",
}


@dataclass(frozen=True)
class IntakeRecord:
    raw: int
    note: str
    status: str = "REGISTERED_2026-07-27_2349_2355"


def intake_records() -> list[IntakeRecord]:
    return [IntakeRecord(raw, note) for raw, note in NEW_VECTORS.items()]
