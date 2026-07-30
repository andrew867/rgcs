"""R10.28 Agent 03 — candidate vector decoder.

BOUNDARY (pack W04, non-negotiable): these are CANDIDATE vectors. They
must not become hard anchors and must not train the Terra projector
until independently verified. Nothing in this module writes to
``r1025.projector.HARD_ANCHORS``, and ``assert_not_anchor_eligible``
exists to make an accidental promotion fail loudly.

Each vector is tested against, in order:

  1. the Montreal quarantine;
  2. the ESTABLISHED transport grammar ``16 | payload | terminal``
     (R10.16C/R10.19) -- terminal digit and payload octal;
  3. exact 36-bit framing (12 octal digits);
  4. every 36-bit partition, including the SurfaceWord-compatibility
     test on Core30.

A vector that fails all of them is reported as failing all of them.
"""

from __future__ import annotations

from r1016.quarantine import assert_clean
from r1028.codec36 import OCTAL_DIGITS, analyse, core30_is_surfaceword_compatible

CANDIDATES = [
    ("ANCHORAGE_ALASKA", "16873059233"),
    # R10.30 operator correction: the prior transcription carried an
    # extra terminal digit. Corrected it is 11 digits, ends in the
    # established terminal 3, and is a CLEAN 12-octal-digit word.
    ("SANTA_FE_NEW_MEXICO", "16875092353"),
    ("JERUSALEM_PRIMARY", "168730592363363"),
    ("JERUSALEM_ALTERNATE", "1678059360633"),
    ("UNLABELED_A", "1687325683294368329"),
    ("UNLABELED_B", "56832954638729876433"),
]

#: The three verified 30-bit anchors, for comparison only.
VERIFIED_ANCHORS = {"STONEHENGE": 165876523, "ERIE": 167849523,
                    "TORONTO": 168930443}

TRANSPORT_HEADER = "16"
ESTABLISHED_TERMINAL = "3"
STONEHENGE_PAYLOAD_OCTAL = "2173604"


class AnchorPromotionError(RuntimeError):
    pass


def assert_not_anchor_eligible(label: str) -> None:
    """Refuse any attempt to promote a candidate to a hard anchor."""
    raise AnchorPromotionError(
        f"refused: {label} is an R10.28 CANDIDATE vector. Promotion to a "
        f"hard anchor requires independent coordinate verification "
        f"(pack item W04/W05). The Terra projector needs >=8 verified "
        f"anchors with >=3 sharing one F5; unverified candidates may not "
        f"be counted toward that.")


def transport_grammar(raw: str) -> dict:
    """Test against the ESTABLISHED 16 | payload | terminal grammar."""
    has_header = raw.startswith(TRANSPORT_HEADER)
    terminal = raw[-1] if raw else ""
    payload = raw[2:-1] if has_header and len(raw) > 3 else ""
    return {
        "has_16_header": has_header,
        "terminal_digit": terminal,
        "terminal_matches_established": terminal == ESTABLISHED_TERMINAL,
        "payload_decimal": payload,
        "payload_octal": format(int(payload), "o") if payload else "",
        "right_appends_stonehenge_payload":
            bool(payload) and format(int(payload), "o").startswith(
                STONEHENGE_PAYLOAD_OCTAL)
            and format(int(payload), "o") != STONEHENGE_PAYLOAD_OCTAL,
        "fits_established_grammar":
            has_header and terminal == ESTABLISHED_TERMINAL,
    }


def decode(label: str, raw: str) -> dict:
    assert_clean([raw], where="R10.28 candidate vector decode")
    value = int(raw)
    a = analyse(value)
    g = transport_grammar(raw)
    compat = []
    for row in a["rows"]:
        if row["partition"] == "H3_CORE30_T3":
            compat.append(row.get("core30_compatible", False))
    return {
        "label": label, "raw": raw,
        "decimal_digits": len(raw),
        "bit_length": a["bit_length"],
        "octal": a["octal"], "octal_digits": a["octal_digits"],
        "exact_36_bit_single_block": a["single_block_exact_36_bit"],
        "blocks_36bit": a["blocks"],
        "leading_block_is_short": a["leading_block_is_short"],
        **{f"grammar_{k}": v for k, v in g.items()},
        "any_block_core30_surfaceword_compatible": any(compat),
        "authority": "CANDIDATE_ONLY_NOT_A_HARD_ANCHOR",
        "may_train_projector": False,
        "rows": a["rows"],
    }


def decode_all() -> dict:
    rows = [decode(lab, raw) for lab, raw in CANDIDATES]
    clean36 = [r for r in rows if r["exact_36_bit_single_block"]]
    grammar_ok = [r for r in rows if r["grammar_fits_established_grammar"]]
    compat = [r for r in rows if r["any_block_core30_surfaceword_compatible"]]
    return {
        "schema": "rgcs.r1028.candidate-decode.v1",
        "rows": rows,
        "total": len(rows),
        "exact_36_bit_single_block": [r["label"] for r in clean36],
        "fit_established_transport_grammar": [r["label"] for r in grammar_ok],
        "core30_surfaceword_compatible": [r["label"] for r in compat],
        "promoted_to_hard_anchor": 0,
        "verdict": ("R10_28_CANDIDATE_VECTORS_DECODED_STRUCTURALLY_"
                    "NO_ANCHOR_PROMOTION"),
    }
