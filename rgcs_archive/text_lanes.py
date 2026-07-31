"""R10.61 -- conventional character packings over a bitstream.

Every profile is named, its table provenance is recorded, and every legal
bit offset and bit order is swept. Scoring never calls a printable
fragment plaintext: a candidate must beat a matched random null on
trigram likelihood, and the number of hypotheses searched is reported so
the correction can be applied.

The expected result for the reference fixture is that NO convincing
conventional text survives. That is a regression expectation, not an
immutable conclusion -- if a future record produces text that clears the
null, this module will say so.
"""

from __future__ import annotations

import random

#: DEC Radix-50 alphabet: 40 symbols, historically written as octal 50.
RADIX50_ALPHABET = " ABCDEFGHIJKLMNOPQRSTUVWXYZ$.%0123456789"

#: CDC display code, kept DISTINCT from DEC SIXBIT on purpose -- they are
#: different tables and conflating them is a common error.
CDC_DISPLAY = (":ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-*/()$= ,.#[]%\"_!&'?<>@\\^;")

COMMON_TRIGRAMS = {
    "THE", "AND", "ING", "ENT", "ION", "HER", "FOR", "THA", "NTH", "INT",
    "ERE", "TIO", "TER", "EST", "ERS", "ATI", "HAT", "ATE", "ALL", "ETH",
    "OUR", "ARE", "NOT", "YOU", "WIT", "HAS", "HIS", "ITH", "VER", "WAS",
}

PROFILES = ("sixbit_dec", "cdc_display", "ascii7", "multics9", "radix50")


def _bits(payload_octal: str) -> str:
    return "".join(format(int(c, 8), "03b") for c in payload_octal)


def decode(bits: str, profile: str) -> str:
    """Decode a bitstream under one named character profile."""
    out = []
    if profile == "sixbit_dec":                 # PDP-6/PDP-10 SIXBIT
        for i in range(0, len(bits) - 5, 6):
            out.append(chr(int(bits[i:i + 6], 2) + 32))
    elif profile == "cdc_display":
        for i in range(0, len(bits) - 5, 6):
            v = int(bits[i:i + 6], 2)
            out.append(CDC_DISPLAY[v] if v < len(CDC_DISPLAY) else "?")
    elif profile == "ascii7":
        for i in range(0, len(bits) - 6, 7):
            v = int(bits[i:i + 7], 2)
            out.append(chr(v) if 32 <= v < 127 else ".")
    elif profile == "multics9":
        for i in range(0, len(bits) - 8, 9):
            v = int(bits[i:i + 9], 2)
            out.append(chr(v) if 32 <= v < 127 else ".")
    elif profile == "radix50":
        # THREE characters per SIXTEEN bits -- the actual packing.
        for i in range(0, len(bits) - 15, 16):
            v = int(bits[i:i + 16], 2)
            if v >= 40 ** 3:
                out.append("???")
                continue
            cs = []
            for _ in range(3):
                cs.append(RADIX50_ALPHABET[v % 40])
                v //= 40
            out.append("".join(reversed(cs)))
    else:
        raise ValueError(f"unknown profile {profile!r}")
    return "".join(out)


def score(text: str) -> dict:
    """Printable/alphabetic/whitespace fractions and trigram count."""
    if not text:
        return {"length": 0, "printable": 0.0, "alphabetic": 0.0,
                "whitespace": 0.0, "trigrams": 0}
    u = text.upper()
    return {
        "length": len(text),
        "printable": sum(1 for c in text if 32 <= ord(c) < 127) / len(text),
        "alphabetic": sum(1 for c in u if c.isalpha()) / len(text),
        "whitespace": sum(1 for c in text if c.isspace()) / len(text),
        "trigrams": sum(1 for i in range(len(u) - 2)
                        if u[i:i + 3] in COMMON_TRIGRAMS),
    }


def sweep(payload_octal: str) -> dict:
    """Every profile, every legal bit offset, both bit orders."""
    base = _bits(payload_octal)
    variants = {
        "msb_first": base,
        "lsb_first": "".join(base[i:i + 8][::-1]
                             for i in range(0, len(base), 8)),
        "whole_reversed": base[::-1],
    }
    rows = []
    for order, b in variants.items():
        for profile in PROFILES:
            step = {"sixbit_dec": 6, "cdc_display": 6, "ascii7": 7,
                    "multics9": 9, "radix50": 16}[profile]
            for off in range(step):
                t = decode(b[off:], profile)
                rows.append({"profile": profile, "bit_order": order,
                             "offset": off, "text": t, **score(t)})
    return {
        "schema": "rgcs.r1061.text-sweep.v1",
        "hypotheses_searched": len(rows),
        "rows": rows,
        "best_by_trigrams": max(rows, key=lambda r: r["trigrams"]),
    }


def null_distribution(n_bits: int, trials: int = 400, seed: int = 13) -> dict:
    """Matched random controls under the same sweep."""
    rng = random.Random(seed)
    best = []
    for _ in range(trials):
        octal = "".join(rng.choice("01234567") for _ in range(n_bits // 3))
        s = sweep(octal)
        best.append(s["best_by_trigrams"]["trigrams"])
    best.sort()
    return {"trials": trials, "max_trigrams_null_mean": sum(best) / len(best),
            "max_trigrams_null_p95": best[int(0.95 * len(best))],
            "max_trigrams_null_max": best[-1]}


def assess(payload_octal: str, trials: int = 200) -> dict:
    """Sweep, compare against the matched null, and refuse to over-claim."""
    s = sweep(payload_octal)
    null = null_distribution(len(payload_octal) * 3, trials)
    best = s["best_by_trigrams"]
    survives = best["trigrams"] > null["max_trigrams_null_p95"]
    return {
        "schema": "rgcs.r1061.text-assessment.v1",
        "hypotheses_searched": s["hypotheses_searched"],
        "best": {k: best[k] for k in
                 ("profile", "bit_order", "offset", "trigrams",
                  "alphabetic", "printable")},
        "best_text": best["text"][:64],
        "null": null,
        "survives_null": survives,
        "result_class": ("CONVENTIONAL_TEXT_CANDIDATE" if survives
                         else "NULL_COMPATIBLE"),
        "note": "a printable fragment is not plaintext; the candidate must "
                "beat the 95th percentile of matched random controls under "
                "the same number of hypotheses",
    }
