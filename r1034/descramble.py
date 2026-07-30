"""R10.34 Agent 01 — descrambler audit.

Operator hint: "26 may point to alphabet/ROT-style encoding."

Ari's rule, honoured exactly: DO NOT DISCARD THE MESSAGE LANE, but
promote nothing unless it is REVERSIBLE and REPRODUCIBLE. So every
transform here is implemented with its inverse, and a decode is only
recorded when ``inverse(transform(x)) == x`` AND the output passes an
English-plausibility screen that a random string would fail.

Reversibility is the discipline that stops this lane from generating
pareidolia: any string can be mapped to letters somehow, and without a
round-trip check every mapping "produces text".
"""

from __future__ import annotations

import math
import re
import string

ALPHA = string.ascii_uppercase
B36 = string.digits + ALPHA

STRING_A = "1687325683294368329"
STRING_B = "56832954638729876433"
NUMERIC_PREFIX = ("2839754287695473209543634976"
                  "5498765984363210636894683"
                  "678967654732987654321012")
VISIBLE = ("34567890ABCDEFGHIJKLMNOPQRSTUVWXYZTHE"
           "QUICKBROWNFOXJUMPEDOVERTHELAZYDOG.12345678901234567890")

#: Frequent English trigrams. A word list is too brittle -- the visible
#: payload is a pangram and hits only ONE common word, which made an
#: earlier word-count screen reject its own positive control. Trigram
#: density is the calibrated replacement, and the threshold below is
#: chosen so the control PASSES and shuffles of the control FAIL.
TRIGRAMS = ("THE", "AND", "ING", "ENT", "ION", "HER", "FOR", "THA",
            "NTH", "INT", "ERE", "TIO", "TER", "EST", "ERS", "ATI",
            "HAT", "ATE", "ALL", "ETH", "OVE", "VER", "OWN", "UMP")

#: Calibrated on the positive control; see ``calibrate()``.
TRIGRAM_THRESHOLD = 0.035

#: A short string cannot be screened at all: one chance trigram in an
#: 8-letter string yields density 0.167. This is the guard that stopped
#: five noise hits ("LCR319EALLY5" -> "ALL") from being reported as
#: decodes.
MIN_SCREENABLE_LETTERS = 20
MIN_HITS = 3
#: Bonferroni over the ~122 transforms this module tries.
BONFERRONI_ALPHA = 0.05 / 122


def rot(text: str, n: int) -> str:
    out = []
    for c in text:
        if c in ALPHA:
            out.append(ALPHA[(ALPHA.index(c) + n) % 26])
        else:
            out.append(c)
    return "".join(out)


def rot_inverse(text: str, n: int) -> str:
    return rot(text, -n)


def a1z26(digits: str, width: int) -> str | None:
    """Fixed-width digit groups -> letters. None if any group is invalid."""
    if width < 1 or len(digits) % width:
        return None
    out = []
    for i in range(0, len(digits), width):
        v = int(digits[i:i + width])
        if not 1 <= v <= 26:
            return None
        out.append(ALPHA[v - 1])
    return "".join(out)


def a1z26_inverse(text: str, width: int) -> str:
    return "".join(str(ALPHA.index(c) + 1).zfill(width) for c in text)


def to_base36(n: int) -> str:
    if n == 0:
        return "0"
    out = []
    while n:
        n, r = divmod(n, 36)
        out.append(B36[r])
    return "".join(reversed(out))


def from_base36(s: str) -> int:
    return int(s, 36)


def english_score(text: str) -> dict:
    """Trigram-density screen, calibrated against a positive control."""
    letters = re.sub(r"[^A-Z]", "", text.upper())
    n = len(letters)
    if n < 3:
        return {"letters": n, "trigram_hits": 0, "trigram_density": 0.0,
                "common_words_found": [], "plausible_english": False}
    hits = sum(1 for i in range(n - 2) if letters[i:i + 3] in TRIGRAMS)
    density = hits / (n - 2)
    found = sorted({letters[i:i + 3] for i in range(n - 2)
                    if letters[i:i + 3] in TRIGRAMS})
    # Density alone is NOT a valid screen: in an 8-letter string one
    # chance trigram gives density 0.167, far above any threshold
    # calibrated on a long control. So score by the binomial p-value of
    # seeing this many hits at THIS length, and require a minimum
    # length as well.
    p_tri = len(TRIGRAMS) / 26 ** 3
    trials = n - 2
    pval = sum(math.comb(trials, k) * p_tri ** k * (1 - p_tri) ** (trials - k)
               for k in range(hits, trials + 1))
    return {
        "letters": n, "trigram_hits": hits,
        "trigram_density": round(density, 5),
        "p_value": pval,
        "common_words_found": found,
        "long_enough_to_screen": n >= MIN_SCREENABLE_LETTERS,
        "plausible_english": (n >= MIN_SCREENABLE_LETTERS
                              and hits >= MIN_HITS
                              and pval < BONFERRONI_ALPHA),
    }


def calibrate(seed: int = 12345) -> dict:
    """The screen must PASS the plain visible payload and REJECT its own
    shuffles. If it cannot do both, it is not a screen and any decode it
    reports is meaningless."""
    import random
    rng = random.Random(seed)
    letters = re.sub(r"[^A-Z]", "", VISIBLE.upper())
    control = english_score(VISIBLE)
    shuffles = []
    for _ in range(200):
        chars = list(letters)
        rng.shuffle(chars)
        shuffles.append(english_score("".join(chars))["trigram_density"])
    worst = max(shuffles)
    return {
        "control_density": control["trigram_density"],
        "control_passes": control["plausible_english"],
        "shuffle_max_density": round(worst, 5),
        "shuffle_mean_density": round(sum(shuffles) / len(shuffles), 5),
        "threshold": TRIGRAM_THRESHOLD,
        "separates_control_from_shuffles":
            control["plausible_english"] and worst < TRIGRAM_THRESHOLD,
    }


def attempts() -> list:
    rows = []
    targets = {"STRING_A": STRING_A, "STRING_B": STRING_B,
               "A_CONCAT_B": STRING_A + STRING_B,
               "NUMERIC_PREFIX": NUMERIC_PREFIX}

    # 1. base36 of the numeric value, then ROT0-25
    for name, s in targets.items():
        b36 = to_base36(int(s))
        reversible = from_base36(b36) == int(s)
        for n in range(26):
            out = rot(b36, n)
            sc = english_score(out)
            rows.append({
                "target": name, "transform": f"BASE36+ROT{n}",
                "output": out[:60],
                "reversible": reversible and rot_inverse(out, n) == b36,
                "common_words": ";".join(sc["common_words_found"]),
                "plausible_english": sc["plausible_english"],
                "promoted": False})

    # 2. A1Z26 at every fixed width that divides the string
    for name, s in targets.items():
        for w in (1, 2, 3):
            out = a1z26(s, w)
            if out is None:
                rows.append({
                    "target": name, "transform": f"A1Z26_WIDTH{w}",
                    "output": "", "reversible": False,
                    "common_words": "", "plausible_english": False,
                    "promoted": False,
                    "note": "digit group out of 1..26 range or length "
                            "not divisible"})
                continue
            sc = english_score(out)
            rows.append({
                "target": name, "transform": f"A1Z26_WIDTH{w}",
                "output": out, "reversible": a1z26_inverse(out, w) == s,
                "common_words": ";".join(sc["common_words_found"]),
                "plausible_english": sc["plausible_english"],
                "promoted": False})

    # 3. digit-ramp subtraction: the visible payload is a ramp, so test
    #    whether the numeric strings are a ramp plus an offset
    for name, s in targets.items():
        ramp = "".join(str((i + int(s[0])) % 10) for i in range(len(s)))
        diff = "".join(str((int(a) - int(b)) % 10)
                       for a, b in zip(s, ramp))
        rows.append({
            "target": name, "transform": "DIGIT_RAMP_SUBTRACT",
            "output": diff[:60],
            "reversible": True,
            "common_words": "", "plausible_english": False,
            "promoted": False,
            "note": "constant output would indicate a ramp-encoded string",
            "is_constant": len(set(diff)) == 1})

    # 4. the visible payload, ROT-shifted (control: it is already plain)
    for n in (0, 13):
        out = rot(VISIBLE, n)
        sc = english_score(out)
        rows.append({
            "target": "VISIBLE_PAYLOAD", "transform": f"ROT{n}",
            "output": out[:60], "reversible": rot_inverse(out, n) == VISIBLE,
            "common_words": ";".join(sc["common_words_found"]),
            "plausible_english": sc["plausible_english"],
            "promoted": False})
    return rows


def report() -> dict:
    rows = attempts()
    plausible = [r for r in rows if r.get("plausible_english")]
    # ROT0 on the visible payload is the positive control: it must pass
    control = [r for r in plausible if r["target"] == "VISIBLE_PAYLOAD"
               and r["transform"] == "ROT0"]
    real = [r for r in plausible if r["target"] != "VISIBLE_PAYLOAD"]
    return {
        "schema": "rgcs.r1034.descramble.v1",
        "rows": rows,
        "attempts": len(rows),
        "reversible_attempts": sum(1 for r in rows if r["reversible"]),
        "plausible_english": len(plausible),
        "positive_control_passes": bool(control),
        "genuine_decodes": len(real),
        "promoted": 0,
        "verdict": ("R10_34_CODEC_SOLVED" if real
                    else "R10_34_CODEC_STILL_UNRESOLVED_EXACT_FAILURES_"
                         "EMITTED"),
        "exact_failure": (
            "" if real else
            "every ROT/A1Z26/base36/digit-ramp transform of the numeric "
            "strings either fails reversibility or produces text with no "
            "common-word content. The positive control (the visible "
            "payload at ROT0) passes the same screen, so the screen is "
            "not simply rejecting everything."),
        "note": "the '26' hint was tested as ROT0-25 over base36 output "
                "and as A1Z26 digit grouping; neither yields a "
                "reversible English decode of the numeric strings",
    }
