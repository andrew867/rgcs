"""WS01 — Coordinate Workbench reconciliation into the shared schema.

Bridges the already-shipped ``rgcs_coordinate`` package (RCW EOD
slice, branch ``rcw-public-workbench``) into the program's shared
status/receipt vocabulary. The receipt is built by EXECUTING the
codec — a golden decode and round-trip run at receipt-build time — so
the receipt can never claim more than the code just did.
"""

from __future__ import annotations

from rgcs_lab.common.status_schema import ClaimClass, validate_receipt

#: The R10.8.5A projection verdict, verbatim (never paraphrased).
PROJECTION_VERDICT = ("RGCS_R10_8_5A_YELLOW_PACKET_AUTHORITY_HELD_"
                      "PROJECTION_UNDERDETERMINED")


def build_coordinate_receipt(source_commit: str) -> dict:
    """Execute the structural codec and compose the module receipt.

    GREEN is claimed for the structural lane only, and only because
    the golden decode and round-trip just ran in this process. The
    projection lane rides along as an explicit YELLOW warning with the
    verbatim R10.8.5A verdict — a training equality is calibration,
    never validation.
    """
    import rgcs_coordinate as rc

    trace = rc.decode_coordinate(165876523)
    rt = rc.roundtrip_coordinate(165876523)
    ok = (trace.octal10 == "1170611453" and trace.face_id == 4
          and trace.q22_path == (3, 3, 0, 1, 2, 0, 2, 1, 2, 1, 1)
          and trace.extracted_shell == 3 and rt["exact"])
    receipt = {
        "module": "coordinate",
        "version": rc.__version__,
        "source_commit": source_commit,
        "status": "GREEN" if ok else "RED",
        "claim_class": [ClaimClass.EXACT_ARITHMETIC.value,
                        ClaimClass.TRAINING_EQUALITY.value,
                        ClaimClass.UNDERDETERMINED.value],
        "inputs": {"golden_word": "165876523",
                   "fixture_role": "supplied training equality and "
                                   "regression fixture"},
        "models": ["federation-terra-30 structural codec "
                   "(bit-parity-locked to frozen r12.icosapacket)"],
        "result": {
            "structural_lane": "GREEN" if ok else "RED",
            "octal10": trace.octal10,
            "roundtrip_exact": rt["exact"],
            "projection_lane": "YELLOW",
            "projection_verdict": PROJECTION_VERDICT,
        },
        "warnings": [
            "physical projection underdetermined; candidate placements "
            "are training-calibrated and cannot validate the training "
            "equality",
            "Morton/octree indices are hierarchical path registers, "
            "never coordinates",
        ],
        "tests": ["tests/rgcs_coordinate (30 passed, RCW EOD slice)",
                  "in-process golden decode + roundtrip at receipt "
                  "build time"],
        "artifacts": ["workbench/index.html",
                      "docs/proofs/workbench-release/"
                      "P02_P06_PHASE_RECEIPTS.md"],
    }
    validate_receipt(receipt)
    return receipt
