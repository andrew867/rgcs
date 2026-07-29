"""R10.31 Agent 02 — checksum over DECODED FIELDS.

R10.30 refuted every raw octal-digit rule. This module searches the next
family up: rules over the decoded R4 / S8 / P12 / E12 / E3[0..3] fields.

THE HONESTY PROBLEM, STATED UP FRONT
------------------------------------
The target is 3 bits. A random rule matches one example with p = 1/8 and
two examples with p = 1/64. Searching N rules against 2 examples yields
about N/64 false survivors. With N in the hundreds, survivors are
EXPECTED -- so a survivor count is meaningless unless it is compared
against N/64, and that comparison is computed and reported here.

A rule is only reported as FOUND when the survivor count is 1 AND the
example count is enough to make a single survivor surprising. With 2
examples it never is. This module is therefore expected to return
STILL_BLOCKED, and it says so with the arithmetic that forces it.
"""

from __future__ import annotations

import itertools

from r1028.codec36 import Block36

FIELD_NAMES = ("R4", "S8", "P12", "E12", "E3_0", "E3_1", "E3_2")


def fields_of(value: int) -> dict:
    b = Block36(value)
    p = b.split("R4_S8_P12_E12")
    e = b.e12_fields()
    return {"R4": p["R4"], "S8": p["S8"], "P12": p["P12"], "E12": p["E12"],
            "E3_0": e["epoch_refine_1"], "E3_1": e["epoch_refine_2"],
            "E3_2": e["epoch_frequency"], "target": e["m3_check"],
            "octal_parity": sum(int(c) for c in b.octal) % 2,
            "word": value}


def _crc3(value: int, poly: int) -> int:
    """3-bit LFSR over the leading 33 bits."""
    reg = 0
    for i in range(35, 2, -1):
        bit = (value >> i) & 1
        top = (reg >> 2) & 1
        reg = ((reg << 1) & 7) | (bit ^ top)
        if top:
            reg ^= poly
    return reg & 7


def rule_families():
    """Yield (name, fn) over decoded fields. All exact integer/GF(2)."""
    base = ["R4", "S8", "P12", "E12", "E3_0", "E3_1", "E3_2"]

    # linear mod 8 over single fields, with affine offset
    for f in base:
        for c in range(1, 8):
            for k in range(8):
                yield (f"LIN8[{c}*{f}+{k}]",
                       lambda d, f=f, c=c, k=k: (c * d[f] + k) % 8)

    # XOR over the three E3 fields, all subsets
    for r in range(1, 4):
        for combo in itertools.combinations(("E3_0", "E3_1", "E3_2"), r):
            for k in range(8):
                yield (f"XOR3[{'^'.join(combo)}^{k}]",
                       lambda d, combo=combo, k=k:
                       _xor([d[x] for x in combo]) ^ k)

    # weighted sums over root/surface/path/tail
    for w in itertools.product((0, 1, 2, 3), repeat=4):
        if not any(w):
            continue
        yield (f"WSUM8{w}",
               lambda d, w=w: (w[0] * d["R4"] + w[1] * d["S8"]
                               + w[2] * d["P12"] + w[3] * d["E3_2"]) % 8)

    # CRC-like 3-bit LFSR over the leading 33 bits
    for poly in range(1, 8):
        yield (f"CRC3[poly={poly}]", lambda d, poly=poly: _crc3(d["word"], poly))

    # parity-augmented
    for f in base:
        yield (f"PAR[{f}+octal_parity]",
               lambda d, f=f: (d[f] + d["octal_parity"]) % 8)


def _xor(vals) -> int:
    out = 0
    for v in vals:
        out ^= v
    return out


def search(values) -> dict:
    """values: iterable of (label, int). Only exact 36-bit words qualify."""
    ex = [(lab, fields_of(v)) for lab, v in values
          if len(format(v, "o")) == 12]
    n = len(ex)
    survivors, total = [], 0
    for name, fn in rule_families():
        total += 1
        if n and all(fn(d) == d["target"] for _, d in ex):
            survivors.append(name)
    p_single = 1 / 8
    p_all = p_single ** n if n else 1.0
    expected_false = total * p_all
    # a single survivor is only meaningful when chance would give << 1
    decisive = expected_false < 0.05 and len(survivors) == 1
    deg = degeneracy(values)
    return {
        "schema": "rgcs.r1031.field-checksum.v1",
        "examples": n,
        "degeneracy": deg,
        "example_labels": [lab for lab, _ in ex],
        "rules_tested": total,
        "survivors": survivors,
        "survivor_count": len(survivors),
        "p_random_rule_matches_all": p_all,
        "expected_false_survivors": expected_false,
        "decisive": decisive,
        "verdict": ("R10_31_FIELD_CHECKSUM_FOUND" if decisive
                    else "R10_31_FIELD_CHECKSUM_STILL_BLOCKED"),
        "exact_failure": (
            "" if decisive else
            f"{total} rules tested against {n} example(s); chance alone "
            f"predicts {expected_false:.1f} survivors and "
            f"{len(survivors)} were found. A 3-bit target needs enough "
            f"examples that expected_false << 1: with this rule-set size "
            f"that means >= {_needed(total)} clean 12-octal examples. "
            f"AND the binding defect is degeneracy, not count: the "
            f"constant field(s) {deg['constant_fields']} impose no "
            f"constraint at all, and the m3 target is "
            f"{'CONSTANT across every example, so the effective corpus is ONE example' if deg['target_is_constant'] else 'varying'}."),
        "needed_examples": _needed(total),
    }


def degeneracy(values) -> dict:
    """How much independent constraint do these examples actually give?

    This is the question that matters and it is easy to miss. Two
    examples that share a field value impose NO constraint on any rule
    reading only that field; two examples that share the TARGET value
    barely constrain anything at all, because every rule that happens to
    output that constant survives both.
    """
    ex = [fields_of(v) for _, v in values if len(format(v, "o")) == 12]
    if len(ex) < 2:
        return {"examples": len(ex), "constant_fields": [],
                "target_is_constant": None,
                "effective_independent_examples": len(ex)}
    const = [f for f in FIELD_NAMES
             if len({d[f] for d in ex}) == 1]
    tgt_const = len({d["target"] for d in ex}) == 1
    return {
        "examples": len(ex),
        "constant_fields": const,
        "varying_fields": [f for f in FIELD_NAMES if f not in const],
        "target_values": sorted({d["target"] for d in ex}),
        "target_is_constant": tgt_const,
        "effective_independent_examples": 1 if tgt_const else len(ex),
        "why": ("every example carries the same m3 target, so any rule "
                "that outputs that constant survives all of them; the "
                "corpus constrains barely more than a single example "
                "would" if tgt_const else
                "targets vary, so the examples do constrain the rule"),
        "rules_reading_only_constant_fields_are_unconstrained": const,
    }


def _needed(total: int) -> int:
    """Smallest example count making expected false survivors < 0.05."""
    n = 1
    while total * (1 / 8) ** n >= 0.05 and n < 32:
        n += 1
    return n
