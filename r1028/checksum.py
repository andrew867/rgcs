"""R10.28 Agent 02 — the check-digit solver, and its exact failure.

Source phrase:

    mod(10) + sqrt(2)/phi = last digit sum of 12 digits of octal

TWO INDEPENDENT REASONS THIS CANNOT BE ADOPTED AS WRITTEN
---------------------------------------------------------
1. ``sqrt(2)/phi = 0.8740320488976422...`` is IRRATIONAL. A checksum is
   an exact function into a finite field -- here 3 bits or one octal
   digit. Adding an irrational constant to an integer can never yield an
   integer, so no rounding-free reading of the phrase is implementable.
   Any implementation must therefore pick a rounding rule, and the pack
   is explicit: "Do not choose checksum without exact integer/3-bit
   rule." So the irrational reading is REFUSED, not approximated.

2. Even setting that aside, the corpus is too small to identify a rule.
   Exactly ONE candidate vector is a clean 12-octal-digit word
   (Anchorage). One example gives one equation. Every rule below that
   happens to output the observed check value fits it, and they cannot
   be told apart. That is underdetermination, not a solution.

So this module SEARCHES and REPORTS, and refuses to select. The output
is a table of which rules are consistent with the available example(s),
with the explicit count of examples behind each verdict.
"""

from __future__ import annotations

import math

SQRT2_OVER_PHI = math.sqrt(2) / ((1 + math.sqrt(5)) / 2)
SQRT2_OVER_PHI_NOTE = 0.8740320488976422


class ChecksumError(ValueError):
    pass


def refuse_irrational_checksum() -> None:
    """The literal reading of the source phrase is not implementable."""
    raise ChecksumError(
        f"refused: sqrt(2)/phi = {SQRT2_OVER_PHI!r} is irrational, so "
        f"'mod(10) + sqrt(2)/phi' cannot map integers to an exact 3-bit "
        f"or single-octal-digit check field. An exact integer rule is "
        f"required (R10.28 Agent 02); no rounding convention is adopted "
        f"here because none is stated in the source.")


def octal_digits(value: int, width: int = 12) -> list:
    return [int(c) for c in format(value, f"0{width}o")]


#: Candidate EXACT integer rules. Each takes the leading 11 octal digits
#: and must predict the 12th. Nothing irrational appears in any of them.
def _rules() -> dict:
    return {
        "SUM11_MOD_8": lambda d: sum(d[:11]) % 8,
        "SUM11_MOD_10_MOD_8": lambda d: (sum(d[:11]) % 10) % 8,
        "NEG_SUM11_MOD_8": lambda d: (-sum(d[:11])) % 8,
        "XOR11": lambda d: _xor(d[:11]),
        "ALTERNATING_SUM11_MOD_8":
            lambda d: sum(x if i % 2 == 0 else -x
                          for i, x in enumerate(d[:11])) % 8,
        "WEIGHTED_POSITION_MOD_8":
            lambda d: sum((i + 1) * x for i, x in enumerate(d[:11])) % 8,
        "SUM11_MOD_7": lambda d: sum(d[:11]) % 7,
        "DIGITSUM_DECIMAL_MOD_8": None,     # filled per-vector, needs decimal
    }


def _xor(ds) -> int:
    out = 0
    for d in ds:
        out ^= d
    return out


def search(examples) -> dict:
    """Test every exact rule against every clean 12-octal-digit example.

    ``examples`` is an iterable of (label, value, decimal_string).
    """
    clean = [(lab, v, s) for lab, v, s in examples
             if len(format(v, "o")) == 12]
    rows = []
    for name, fn in _rules().items():
        if fn is None:
            hits, total, detail = 0, 0, []
            for lab, v, s in clean:
                d = octal_digits(v)
                pred = sum(int(c) for c in s) % 8
                ok = pred == d[11]
                hits += ok
                total += 1
                detail.append(f"{lab}:{pred}vs{d[11]}")
        else:
            hits, total, detail = 0, 0, []
            for lab, v, s in clean:
                d = octal_digits(v)
                pred = fn(d)
                ok = pred == d[11]
                hits += ok
                total += 1
                detail.append(f"{lab}:{pred}vs{d[11]}")
        rows.append({
            "rule": name,
            "exact_integer_rule": True,
            "examples_tested": total,
            "examples_matched": hits,
            "consistent_with_all_examples": total > 0 and hits == total,
            "detail": ";".join(detail),
        })
    consistent = [r for r in rows if r["consistent_with_all_examples"]]
    n = len(clean)
    return {
        "schema": "rgcs.r1028.checksum-search.v1",
        "clean_12_octal_examples": n,
        "example_labels": [lab for lab, _, _ in clean],
        "rows": rows,
        "rules_consistent": len(consistent),
        "identified": len(consistent) == 1 and n >= 4,
        "verdict": (
            "R10_28_CHECKSUM_EXACT_FAILURE_ALL_CANDIDATE_RULES_REFUTED"
            if n >= 2 and not consistent else
            "R10_28_CHECKSUM_EXACT_FAILURE_UNDERDETERMINED"
            if n < 4 else
            ("R10_28_CHECKSUM_IDENTIFIED" if len(consistent) == 1
             else "R10_28_CHECKSUM_EXACT_FAILURE_AMBIGUOUS")),
        "exact_failure": (
            f"{n} clean 12-octal-digit example(s); NO candidate exact rule "
            f"survives all of them. The whole candidate set is refuted, "
            f"not merely undecided -- a new rule family is required, not "
            f"more examples of the same kind."
            if n >= 2 and not consistent else
            f"only {n} clean 12-octal-digit example(s) available; "
            f"{len(consistent)} exact rule(s) are consistent with it and "
            f"cannot be distinguished. A checksum over a 3-bit field "
            f"needs at least ~4 independent examples to isolate one rule "
            f"from this candidate set."),
        "irrational_reading": "REFUSED_NOT_IMPLEMENTABLE",
        "sqrt2_over_phi": SQRT2_OVER_PHI,
        "sqrt2_over_phi_matches_source_note":
            abs(SQRT2_OVER_PHI - SQRT2_OVER_PHI_NOTE) < 1e-15,
    }
