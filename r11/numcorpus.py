"""P0N — the numeric corpus, audited exhaustively, layout preserved.

A pile of numbers arrived as a *layout*: some rows carry one number, some
carry four separated by spaces, one carries a parenthesis, two carry
leading zeros, two are written as ratios. This module holds that pile
and audits it, and its first discipline is the least glamorous one:

**The layout is a datum. Regrouping it is an interpretation.**

``4096 12 63 24`` is four groups on one row. Reading it as the integer
4096122324, as the pair (4096, 122324), as a date, or as four independent
values are four *different hypotheses*, and the row itself does not
choose between them. Likewise ``096785`` is not the integer 96785 with a
stray character in front: the leading zero is part of what was recorded,
and a fixed-width field, an index, a padded identifier and a decimal
integer are different objects. ``(3)44478`` carries a parenthesis that
might be repetend notation, a footnote marker, a correction, or noise.
So every entry is stored **as the original string**, never as a
normalised integer, and :func:`raw_layout` returns the corpus exactly as
it was given. :func:`corpus_hash` content-addresses that layout, so any
silent regrouping changes the hash and is caught.

**Failed parses are retained, not dropped.** An entry that does not
parse as a plain number is kept with status ``PARSE_GROUPED`` or
``PARSE_AMBIGUOUS`` and stays in the corpus. Discarding the rows that
resist parsing, and then reporting how well the remainder fits, is
selection dressed as analysis. :func:`failed_parses` exists so the
awkward rows stay visible and countable.

**Negative results are retained too.** For every fraction and its
inverse the audit computes the exact reduced rational, the decimal
prefix and repetend found by long division, the denominator's prime
factorisation, the phase modulo one turn and its degrees, whether that
lands on the 15-degree lattice, whether the value times 4096 is an
integer, an isotope-age reading *in both orientations*, a
description-length complexity, and where that complexity sits in a null
of random fractions of similar size. Most of those come back
unremarkable, and the unremarkable answers are reported with the same
prominence as any hit -- that is the whole point of auditing
exhaustively rather than reporting the one row that looked good.

Two further refusals. The isotope reading ``t = 30.05 * log2(1 + R)`` is
labelled an INTERPRETATION and never a measurement; it is computed for
``R = a/b`` and for ``R = b/a`` because a bare ratio has no privileged
orientation, and the two answers differ. And unit consistency is
``UNDECLARED`` by default: a bare fraction has no unit, and none is
invented for it here.

Nothing in this module is measured. These are numbers under study, and
the standing result is that no decoder is identified.
"""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

# --- module-level declarations -----------------------------------------

EVIDENCE_CLASS = "DERIVED_MATHEMATICS over SOURCE_CLAIM numerals"
MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: The standing verdict. The corpus is audited; nothing decodes it.
VERDICT = "NUMERIC_CORPUS_AUDITED_NO_DECODER_IDENTIFIED"

#: One full turn in degrees, and the 24-fold 15-degree sector lattice.
DEGREES_PER_TURN = 360
SECTOR_DEGREES = Fraction(15)

#: The ladder base that recurs in the corpus (row 1, first group).
LADDER_BASE = 4096

#: The corpus entry "30.05", read -- as an INTERPRETATION -- as a
#: half-life in years so that t = 30.05 * log2(1 + R) can be evaluated.
#: Reading it that way is a hypothesis about the numeral, not a fact
#: about it, and the label travels with every age computed from it.
ISOTOPE_SCALE = Fraction("30.05")
ISOTOPE_LABEL = "INTERPRETATION_NOT_MEASUREMENT"

#: The preregistered null: how many random fractions, and the seed.
NULL_SAMPLES = 1000
NULL_SEED = 4096


class CorpusError(RuntimeError):
    """Raised when the corpus is regrouped, normalised away, or when a
    retired numeric sequence is reintroduced."""


# --- the corpus, exactly as given --------------------------------------

#: The corpus as a layout: one string per row, spacing and grouping
#: preserved verbatim. Leading zeros, the parenthesis, the internal
#: spaces and the trailing zeros of "8.300" are all part of the datum
#: and are never normalised away.
CORPUS_LAYOUT: tuple[str, ...] = (
    "4096 12 63 24",
    "9192 631 770",
    "55",
    "192",
    "30.05",
    "15 17 23 27 33 34 48",
    "(3)44478",
    "312553",
    "37/53",
    "51/84",
    "096785",
    "8697",
    "0341",
    "808",
    "8451",
    "1238",
    "1903",
    "3478",
    "23 34 56 72",
    "8.300",
    "1.876",
)


def raw_layout() -> tuple[str, ...]:
    """The corpus exactly as listed: grouping, zeros and brackets intact."""
    return CORPUS_LAYOUT


def corpus_hash(layout: tuple[str, ...] | None = None) -> str:
    """SHA-256 over the layout, row-separated. Regrouping changes it."""
    rows = CORPUS_LAYOUT if layout is None else tuple(layout)
    return hashlib.sha256("\x1f".join(rows).encode("utf-8")).hexdigest()


def refuse_regrouping(raw: str, regrouped: str) -> None:
    """Refuse to replace a recorded row with a regrouped reading.

    Raises unconditionally. A regrouping may be a perfectly good
    hypothesis; it is not the datum, and it does not get to overwrite it.
    """
    raise CorpusError(
        f"refusing to replace the recorded row {raw!r} with {regrouped!r}. "
        f"The grouping, the leading zeros and any bracket are part of "
        f"what was recorded; joining groups, stripping a zero or "
        f"dropping a bracket is an interpretation of the row, not a "
        f"cleaner copy of it. Add the reading alongside the row; the row "
        f"itself stays as given.")


# --- retired sequences --------------------------------------------------

#: Sequences that have been retired from study. A retired sequence is
#: never reintroduced, whatever it later appears to fit. The registry is
#: seeded with one documented placeholder so the mechanism is exercised
#: rather than dormant; it holds no private content and no real datum.
RETIRED_SEQUENCES: frozenset[str] = frozenset({
    "0000000000",   # placeholder: a synthetic retired sequence, no referent
})


def refuse_retired_sequence(seq: str) -> None:
    """Refuse to reintroduce a retired numeric sequence.

    Raises unconditionally. Retirement is a decision about provenance,
    not about how well the digits fit; a sequence that comes back
    because it now fits something is exactly the case the rule exists
    to stop.
    """
    known = str(seq) in RETIRED_SEQUENCES
    where = ("it is in the retired registry" if known
             else "it is not in the corpus and carries no provenance")
    raise CorpusError(
        f"refusing to reintroduce the numeric sequence {seq!r}: {where}. "
        f"A retired sequence stays retired; bringing it back because it "
        f"now appears to fit something is the look-elsewhere effect with "
        f"extra steps. The audited corpus is raw_layout(), and it is not "
        f"extended by discovery.")


# --- parsing, with failures retained ------------------------------------

class ParseStatus(str, Enum):
    """What kind of thing a row turned out to be, including failures."""

    PARSE_INTEGER = "PARSE_INTEGER"      # a single run of digits
    PARSE_DECIMAL = "PARSE_DECIMAL"      # a single decimal numeral
    PARSE_RATIO = "PARSE_RATIO"          # written a/b
    PARSE_GROUPED = "PARSE_GROUPED"      # several groups on one row
    PARSE_AMBIGUOUS = "PARSE_AMBIGUOUS"  # brackets or unreadable form


#: The statuses that did NOT yield a single number. Retained, never
#: dropped: the rows that resist parsing are data about the corpus.
UNPARSED_STATUSES = (ParseStatus.PARSE_GROUPED, ParseStatus.PARSE_AMBIGUOUS)


@dataclass(frozen=True)
class ParsedEntry:
    """One row of the corpus. ``raw`` is the datum; the rest is reading."""

    raw: str                          # verbatim, e.g. "096785" or "(3)44478"
    status: ParseStatus
    value: Fraction | None            # None whenever the row did not parse
    groups: tuple[str, ...]           # the row split on spaces, verbatim
    note: str = ""

    @property
    def parsed(self) -> bool:
        return self.status not in UNPARSED_STATUSES

    @property
    def leading_zeros(self) -> int:
        """Leading zeros on the first group -- part of the record."""
        first = self.groups[0] if self.groups else ""
        stripped = first.lstrip("0")
        return len(first) - len(stripped) if stripped else 0

    @property
    def declared_digits(self) -> int:
        """Digits as written, which trailing zeros of "8.300" contribute to."""
        return sum(c.isdigit() for c in self.raw)


def _is_digits(tok: str) -> bool:
    return bool(tok) and all(c.isdigit() for c in tok)


def _is_decimal(tok: str) -> bool:
    if tok.count(".") != 1:
        return False
    whole, frac = tok.split(".")
    return _is_digits(whole) and _is_digits(frac)


def parse_entry(s: str) -> ParsedEntry:
    """Read one row, retaining it whatever the outcome.

    A row that does not resolve to a single number comes back with
    ``PARSE_GROUPED`` or ``PARSE_AMBIGUOUS`` and ``value=None``. It is
    still an entry, it is still counted, and it is still in the corpus.
    """
    raw = str(s)
    groups = tuple(raw.split())
    if "(" in raw or ")" in raw:
        return ParsedEntry(
            raw, ParseStatus.PARSE_AMBIGUOUS, None, groups,
            "the parenthesis has no declared meaning: repetend notation, "
            "a footnote marker, a correction and a transcription artefact "
            "are all live readings, and the row does not choose")
    if len(groups) > 1:
        return ParsedEntry(
            raw, ParseStatus.PARSE_GROUPED, None, groups,
            f"{len(groups)} groups on one row; concatenating, pairing or "
            f"reading them as independent values are different "
            f"hypotheses, so no single value is assigned")
    tok = groups[0] if groups else ""
    if "/" in tok:
        num, _, den = tok.partition("/")
        if _is_digits(num) and _is_digits(den) and int(den) != 0:
            return ParsedEntry(
                raw, ParseStatus.PARSE_RATIO, Fraction(int(num), int(den)),
                groups, "written as a ratio; units undeclared")
        return ParsedEntry(
            raw, ParseStatus.PARSE_AMBIGUOUS, None, groups,
            "slash present but the row is not a ratio of two integers")
    if _is_decimal(tok):
        return ParsedEntry(
            raw, ParseStatus.PARSE_DECIMAL, Fraction(tok), groups,
            "decimal numeral; trailing zeros are kept in the raw form "
            "because they declare precision the value does not carry")
    if _is_digits(tok):
        zeros = len(tok) - len(tok.lstrip("0"))
        note = "run of digits"
        if zeros and tok != "0":
            note = (f"{zeros} leading zero(s) retained: a padded field, an "
                    f"index and a decimal integer are different objects")
        return ParsedEntry(
            raw, ParseStatus.PARSE_INTEGER, Fraction(int(tok)), groups, note)
    return ParsedEntry(
        raw, ParseStatus.PARSE_AMBIGUOUS, None, groups,
        "not a readable numeral in any declared form")


def entries() -> tuple[ParsedEntry, ...]:
    """Every row of the corpus, parsed or not, in layout order."""
    return tuple(parse_entry(row) for row in raw_layout())


def failed_parses() -> tuple[ParsedEntry, ...]:
    """The rows that did not resolve to a single number. Retained."""
    return tuple(e for e in entries() if not e.parsed)


def parse_summary() -> dict:
    """How many rows landed in each status. No row is unaccounted for."""
    counts: dict[str, int] = {}
    for e in entries():
        counts[e.status.value] = counts.get(e.status.value, 0) + 1
    return {
        "rows": len(CORPUS_LAYOUT),
        "counts": counts,
        "retained_unparsed": len(failed_parses()),
        "all_rows_retained": sum(counts.values()) == len(CORPUS_LAYOUT),
    }


# --- exact decimal expansion by long division ---------------------------

@dataclass(frozen=True)
class DecimalExpansion:
    """The decimal form of a rational: prefix, then a repeating cycle."""

    prefix: str          # e.g. "0." for 1/3, "0.5" for 1/2
    repetend: str        # e.g. "3" for 1/3, "" when terminating
    terminating: bool

    @property
    def period(self) -> int:
        return len(self.repetend)

    def rendered(self, cycles: int = 2) -> str:
        return self.prefix + self.repetend * cycles


def decimal_expansion(value: Fraction) -> DecimalExpansion:
    """Long division: emit digits until a remainder repeats.

    The first remainder seen twice closes the cycle, so the digits after
    its first appearance are the repetend and the digits before it are
    the non-repeating prefix. Exact -- no floating point is involved.
    """
    v = Fraction(value)
    sign = "-" if v < 0 else ""
    v = abs(v)
    den = v.denominator
    whole, rem = divmod(v.numerator, den)
    digits: list[str] = []
    seen: dict[int, int] = {}
    repetend = ""
    while rem != 0:
        if rem in seen:
            start = seen[rem]
            repetend = "".join(digits[start:])
            digits = digits[:start]
            break
        seen[rem] = len(digits)
        q, rem = divmod(rem * 10, den)
        digits.append(str(q))
    prefix = f"{sign}{whole}." + "".join(digits)
    return DecimalExpansion(prefix, repetend, repetend == "")


# --- factorisation, phase, ladder ---------------------------------------

def prime_factorization(n: int) -> dict[int, int]:
    """Prime factors of a positive integer, as {prime: exponent}."""
    n = int(n)
    if n < 1:
        raise CorpusError(f"prime_factorization needs n >= 1, got {n}")
    factors: dict[int, int] = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors


def factorization_string(factors: dict[int, int]) -> str:
    """Render {2: 6, 3: 1} as 2^6*3. The empty factorisation renders as 1."""
    if not factors:
        return "1"
    return "*".join(f"{p}^{e}" if e > 1 else f"{p}"
                    for p, e in sorted(factors.items()))


def phase_mod_turn(value: Fraction) -> Fraction:
    """The value read as turns, reduced into [0, 1). Exact."""
    return Fraction(value) % 1


def degrees_of(phase_turns: Fraction) -> Fraction:
    """Turns to degrees, exactly."""
    return Fraction(phase_turns) * DEGREES_PER_TURN


def sector_relation(degrees: Fraction) -> dict:
    """Where the angle sits on the 15-degree lattice, and whether exactly."""
    idx = Fraction(degrees) / SECTOR_DEGREES
    exact = idx.denominator == 1
    return {
        "sector_index": str(idx),
        "sector_index_int": int(idx) if exact else None,
        "on_15_degree_lattice": exact,
        "sector_degrees": str(SECTOR_DEGREES),
    }


def ladder_4096(value: Fraction) -> dict:
    """Is value * 4096 an integer, and what is it? Exact either way."""
    scaled = Fraction(value) * LADDER_BASE
    is_int = scaled.denominator == 1
    return {
        "base": LADDER_BASE,
        "value_times_base": str(scaled),
        "is_integer": is_int,
        "integer": int(scaled) if is_int else None,
        "flag": "ON_LADDER" if is_int else "OFF_LADDER_NOT_AN_INTEGER",
    }


# --- unit status --------------------------------------------------------

class UnitStatus(str, Enum):
    """A bare fraction has no unit; that is a status, not an oversight."""

    UNDECLARED = "UNDECLARED"
    DECLARED_CONSISTENT = "DECLARED_CONSISTENT"
    DECLARED_INCONSISTENT = "DECLARED_INCONSISTENT"


def unit_status(unit_a: str | None = None,
                unit_b: str | None = None) -> UnitStatus:
    """Consistency of the two sides of a ratio. UNDECLARED by default."""
    if unit_a is None or unit_b is None:
        return UnitStatus.UNDECLARED
    return (UnitStatus.DECLARED_CONSISTENT if unit_a == unit_b
            else UnitStatus.DECLARED_INCONSISTENT)


# --- complexity and its null -------------------------------------------

def expression_complexity(value: Fraction) -> int:
    """A description-length proxy: bits of numerator plus bits of denominator.

    Crude on purpose. It is not a measure of significance; it exists only
    so "niceness" is a number that a null can be run against.
    """
    v = Fraction(value)
    return abs(v.numerator).bit_length() + v.denominator.bit_length()


def null_percentile(a: int, b: int, n_samples: int = NULL_SAMPLES,
                    seed: int = NULL_SEED) -> dict:
    """Where this fraction's simplicity sits among random ones its size.

    Draw ``n_samples`` random fractions with numerator and denominator
    uniform on [1, max(|a|, |b|)], reduce each, and count how many are at
    least as simple as a/b. A high share means the fraction is ordinary:
    most random fractions of that size are as tidy as this one, so its
    tidiness carries no weight.
    """
    if b == 0:
        raise CorpusError("null_percentile: denominator must be nonzero")
    hi = max(abs(int(a)), abs(int(b)), 2)
    observed = expression_complexity(Fraction(a, b))
    rng = random.Random(seed)
    at_least_as_simple = 0
    for _ in range(n_samples):
        x = rng.randint(1, hi)
        y = rng.randint(1, hi)
        if expression_complexity(Fraction(x, y)) <= observed:
            at_least_as_simple += 1
    p = at_least_as_simple / n_samples
    return {
        "observed_complexity": observed,
        "n_samples": n_samples,
        "seed": seed,
        "draw_range": [1, hi],
        "share_at_least_as_simple": p,
        "verdict": ("NOT_UNUSUALLY_SIMPLE" if p > 0.05
                    else "SIMPLER_THAN_MOST_OF_THE_NULL"),
        "note": ("a simplicity percentile is not a significance test; it "
                 "says only how ordinary this fraction looks among "
                 "fractions of similar size"),
    }


# --- the isotope reading, in both orientations --------------------------

def isotope_age(ratio: Fraction, scale: Fraction = ISOTOPE_SCALE) -> float:
    """t = scale * log2(1 + R). An INTERPRETATION of the numerals."""
    r = Fraction(ratio)
    if r <= -1:
        raise CorpusError(f"isotope_age needs R > -1, got {r}")
    return float(scale) * math.log2(1.0 + float(r))


def isotope_both_orientations(a: int, b: int,
                              scale: Fraction = ISOTOPE_SCALE) -> dict:
    """Both readings of the same bare ratio, because neither is privileged."""
    if a == 0 or b == 0:
        raise CorpusError(
            "isotope_both_orientations needs both terms nonzero so that "
            "a/b and b/a both exist")
    fwd = Fraction(a, b)
    inv = Fraction(b, a)
    t_fwd = isotope_age(fwd, scale)
    t_inv = isotope_age(inv, scale)
    return {
        "scale": str(scale),
        "formula": "t = scale * log2(1 + R)",
        "forward_ratio": str(fwd),
        "forward_age": t_fwd,
        "inverse_ratio": str(inv),
        "inverse_age": t_inv,
        "orientations_differ": t_fwd != t_inv,
        "status": ISOTOPE_LABEL,
        "units": "UNDECLARED (the scale is read as years only by hypothesis)",
        "note": (
            "a bare ratio does not say which term is parent and which is "
            "daughter, so both orientations are computed and both are "
            "reported. That they disagree is the finding: an age read off "
            "an unoriented ratio is not determined by the ratio"),
    }


# --- the per-fraction audit ---------------------------------------------

def audit_one(a: int, b: int) -> dict:
    """Every scheduled quantity for the single rational a/b."""
    if b == 0:
        raise CorpusError(f"audit_one: {a}/{b} has a zero denominator")
    value = Fraction(int(a), int(b))
    dec = decimal_expansion(value)
    den_factors = prime_factorization(value.denominator)
    num_factors = (prime_factorization(abs(value.numerator))
                   if value.numerator else {})
    phase = phase_mod_turn(value)
    degrees = degrees_of(phase)
    return {
        "written": f"{int(a)}/{int(b)}",
        "reduced": str(value),
        "numerator": value.numerator,
        "denominator": value.denominator,
        "float": float(value),
        "decimal_prefix": dec.prefix,
        "repetend": dec.repetend,
        "repetend_period": dec.period,
        "terminating": dec.terminating,
        "denominator_factorization": den_factors,
        "denominator_factorization_string": factorization_string(den_factors),
        "numerator_factorization": num_factors,
        "phase_turns": str(phase),
        "degrees": str(degrees),
        "degrees_float": float(degrees),
        "sector": sector_relation(degrees),
        "ladder_4096": ladder_4096(value),
        "expression_complexity": expression_complexity(value),
        "null": null_percentile(int(a), int(b)),
    }


def audit_fraction(a: int, b: int) -> dict:
    """Audit a/b and b/a together, with the isotope reading both ways.

    The inverse is audited alongside because nothing in a bare ratio
    says which way round it goes, and several of the scheduled
    quantities -- the repetend, the ladder, the age -- are not symmetric
    under inversion.
    """
    a, b = int(a), int(b)
    if a == 0 or b == 0:
        raise CorpusError(
            f"audit_fraction({a}, {b}): both terms must be nonzero so "
            f"that the fraction and its inverse both exist")
    return {
        "label": f"{a}/{b}",
        "forward": audit_one(a, b),
        "inverse": audit_one(b, a),
        "isotope_interpretation": isotope_both_orientations(a, b),
        "unit_status": unit_status().value,
        "unit_note": ("a bare fraction has no unit; none is assigned here, "
                      "and the ratio is dimensionless only in the trivial "
                      "sense that its terms were never dimensioned"),
        "verdict": VERDICT,
    }


#: The fractions and ratios scheduled for audit. Fixed in advance: the
#: two ratios written in the corpus, the 192/55 pair in both
#: orientations, the four phase rationals, and 63/6 from row 1.
AUDIT_PAIRS: tuple[tuple[int, int], ...] = (
    (37, 53),
    (51, 84),
    (192, 55),
    (55, 192),
    (2, 3),
    (3, 4),
    (5, 6),
    (7, 2),
    (63, 6),
)


def audit_all() -> dict:
    """Every scheduled pair, audited. Unremarkable rows included."""
    return {f"{a}/{b}": audit_fraction(a, b) for a, b in AUDIT_PAIRS}


def audit_summary() -> list[dict]:
    """A compact table of the audit: one row per scheduled pair."""
    rows = []
    for (a, b) in AUDIT_PAIRS:
        au = audit_fraction(a, b)
        f = au["forward"]
        rows.append({
            "label": au["label"],
            "reduced": f["reduced"],
            "decimal_prefix": f["decimal_prefix"],
            "repetend": f["repetend"],
            "terminating": f["terminating"],
            "denominator_factorization": f["denominator_factorization_string"],
            "degrees": f["degrees"],
            "on_15_degree_lattice": f["sector"]["on_15_degree_lattice"],
            "ladder_4096": f["ladder_4096"]["flag"],
            "forward_age": au["isotope_interpretation"]["forward_age"],
            "inverse_age": au["isotope_interpretation"]["inverse_age"],
            "null_share_at_least_as_simple":
                f["null"]["share_at_least_as_simple"],
        })
    return rows


# --- report -------------------------------------------------------------

def numcorpus_report(verdict: str = VERDICT) -> dict:
    """What the corpus is, what was computed on it, and what it is not."""
    return {
        "raw_layout": list(raw_layout()),
        "corpus_hash": corpus_hash(),
        "rows": len(CORPUS_LAYOUT),
        "parse_summary": parse_summary(),
        "failed_parses": [
            {"raw": e.raw, "status": e.status.value,
             "groups": list(e.groups), "note": e.note}
            for e in failed_parses()],
        "audit_summary": audit_summary(),
        "retired_sequences": sorted(RETIRED_SEQUENCES),
        "isotope_scale": str(ISOTOPE_SCALE),
        "isotope_status": ISOTOPE_LABEL,
        "unit_status_default": UnitStatus.UNDECLARED.value,
        "evidence_class": EVIDENCE_CLASS,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not say these numbers are a message, a code, a "
            "frequency, a coordinate, a date, or an age. It does not "
            "regroup a row into a reading and then treat the reading as "
            "the datum: the layout, its leading zeros and its bracket are "
            "kept exactly as recorded, and the rows that refuse to parse "
            "are retained rather than quietly dropped. The isotope ages "
            "are an interpretation of the numeral 30.05, computed in both "
            "orientations precisely because the ratio does not choose one, "
            "and they disagree. The simplicity nulls are not significance "
            "tests. No unit is declared for any entry, and no decoder is "
            "identified."),
        "verdict": verdict,
    }


__all__ = [
    "EVIDENCE_CLASS", "MEASURED_HERE", "PHYSICAL_VALIDATION", "VERDICT",
    "DEGREES_PER_TURN", "SECTOR_DEGREES", "LADDER_BASE",
    "ISOTOPE_SCALE", "ISOTOPE_LABEL", "NULL_SAMPLES", "NULL_SEED",
    "CorpusError",
    "CORPUS_LAYOUT", "raw_layout", "corpus_hash", "refuse_regrouping",
    "RETIRED_SEQUENCES", "refuse_retired_sequence",
    "ParseStatus", "UNPARSED_STATUSES", "ParsedEntry", "parse_entry",
    "entries", "failed_parses", "parse_summary",
    "DecimalExpansion", "decimal_expansion",
    "prime_factorization", "factorization_string",
    "phase_mod_turn", "degrees_of", "sector_relation", "ladder_4096",
    "UnitStatus", "unit_status",
    "expression_complexity", "null_percentile",
    "isotope_age", "isotope_both_orientations",
    "audit_one", "audit_fraction", "AUDIT_PAIRS", "audit_all",
    "audit_summary", "numcorpus_report",
]
