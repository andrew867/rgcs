"""P02 — CW vector decoder, frozen before any future vector arrives.

The source supplied five 12-digit decimal strings. Each needs exactly
38 bits, and

    38 = 2 + 3*12 = 2 + 6*6

which lines up with the RGCS 4096-state and 64-state spaces. Parsed as
a 2-bit header plus three 12-bit fields, all five share the header
``10`` and the first field ``1516``. Parsed as a 2-bit header plus six
6-bit fields, all five share ``[23, 44]``.

That looks like a protocol. It is not.

The five values span 2 109 794, which is under 2^22. Any set of
38-bit integers spanning less than 2^22 has **at least 15 identical
leading bits by arithmetic alone**. The header (2 bits) plus the first
12-bit field occupy the top 14 bits — entirely inside that forced
region. So "every value has header 10 and field one 1516" is a
restatement of "these five numbers are close together". It carries no
information about encoding whatsoever.

:func:`forced_common_bits` computes the guarantee, :func:`parse_report`
separates forced agreement from informative agreement, and
:func:`shared_prefix_null` confirms it empirically by drawing random
integers from the same span and showing the identical "structure"
appears every time.

None of this proves the numbers are *not* a protocol. It proves that
this particular observation is not evidence that they are. The
decoder is frozen here so that future vectors can test it
prospectively, which is the only thing that could settle it.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, asdict, field

from . import CW_STATUSES

#: The source strings, preserved as strings. Leading zeros would be
#: destroyed by integer conversion, so the string is the artifact and
#: the integer is derived (core/02).
SOURCE_STRINGS: tuple[str, ...] = (
    "162875493612",
    "162875432975",
    "162877542769",
    "162875439275",
    "162875439285",
)

#: Every parse hypothesis frozen at pack time. Reporting all of them
#: is a decoder-law requirement: a decoder that shows only its
#: favourite parse is presenting a conclusion as an observation.
PARSE_HYPOTHESES = (
    "RAW_DECIMAL_IDENTIFIER",
    "SIX_DECIMAL_PAIRS",
    "FOUR_DECIMAL_TRIPLETS",
    "BCD_DIGIT_STREAM",
    "UINT38",
    "HEADER2_PLUS_3X12",
    "HEADER2_PLUS_6X6",
    "CHECKSUM_BEARING_PACKET",
    "ENCRYPTED_OR_PSEUDORANDOM",
    "UNRELATED_LABELS",
)

WORD_BITS = 38


class CWRefused(RuntimeError):
    """Raised when a decoder operation is refused."""


# --------------------------------------------------------------------
# The arithmetic that settles it
# --------------------------------------------------------------------

def as_ints(strings: tuple[str, ...] = SOURCE_STRINGS) -> tuple[int, ...]:
    return tuple(int(s) for s in strings)


def forced_common_bits(values: tuple[int, ...],
                       width: int = WORD_BITS) -> int:
    """Leading bits pinned by the *interval* the values occupy.

    Computed as the common binary prefix of the minimum and maximum.
    Any value lying between them necessarily shares that prefix, so
    this is a guarantee that follows from the interval alone and says
    nothing about how the values were generated.

    Note the tempting shortcut ``width - span.bit_length()`` is
    **wrong**: it assumes a narrow span pins the high bits, but values
    can straddle a power-of-two boundary. 127 and 128 span 1 and share
    no leading bits at all. Using the shortcut here reported 16 forced
    bits against 15 observed — more forced than actually agree, which
    is impossible and is how the error was caught.
    """
    if len(values) < 2:
        raise ValueError("need at least two values to bound a span")
    lo, hi = min(values), max(values)
    if lo == hi:
        return width
    n = 0
    for b in range(width - 1, -1, -1):
        if ((lo >> b) & 1) != ((hi >> b) & 1):
            break
        n += 1
    return n


def observed_common_bits(values: tuple[int, ...],
                         width: int = WORD_BITS) -> int:
    """Leading bits that actually agree."""
    n = 0
    for b in range(width - 1, -1, -1):
        if len({(v >> b) & 1 for v in values}) != 1:
            break
        n += 1
    return n


def split_fields(value: int, header_bits: int, field_bits: int,
                 n_fields: int, width: int = WORD_BITS
                 ) -> tuple[int, tuple[int, ...]]:
    """Split ``value`` into a header and ``n_fields`` fixed-width fields."""
    if header_bits + field_bits * n_fields != width:
        raise ValueError(
            f"{header_bits} + {field_bits}*{n_fields} != {width}")
    header = value >> (width - header_bits)
    fields = []
    for i in range(n_fields):
        shift = width - header_bits - field_bits * (i + 1)
        fields.append((value >> shift) & ((1 << field_bits) - 1))
    return header, tuple(fields)


@dataclass(frozen=True)
class ParseReport:
    """What a fixed-width parse actually shows, forced part separated."""

    parse: str
    header_bits: int
    field_bits: int
    n_fields: int
    headers: tuple[int, ...]
    fields: tuple[tuple[int, ...], ...]
    forced_common_bits: int
    observed_common_bits: int
    #: Fields whose constancy is entirely inside the forced prefix.
    constant_fields_forced: tuple[int, ...]
    #: Fields that are constant but NOT explained by the prefix.
    constant_fields_informative: tuple[int, ...]
    header_is_forced: bool
    informative_bits: int
    status: str
    note: str

    def as_record(self) -> dict:
        d = asdict(self)
        for k in ("headers", "constant_fields_forced",
                  "constant_fields_informative"):
            d[k] = list(getattr(self, k))
        d["fields"] = [list(f) for f in self.fields]
        return d


def parse_report(values: tuple[int, ...], header_bits: int,
                 field_bits: int, n_fields: int,
                 parse: str, width: int = WORD_BITS) -> ParseReport:
    """Apply a parse and report forced vs informative agreement."""
    forced = forced_common_bits(values, width)
    observed = observed_common_bits(values, width)

    headers, allfields = [], []
    for v in values:
        h, f = split_fields(v, header_bits, field_bits, n_fields, width)
        headers.append(h)
        allfields.append(f)

    header_forced = header_bits <= forced
    forced_const, info_const = [], []
    for i in range(n_fields):
        col = {f[i] for f in allfields}
        if len(col) != 1:
            continue
        # highest bit index this field occupies, counted from the top
        top = header_bits + field_bits * (i + 1)
        (forced_const if top <= forced else info_const).append(i)

    informative = max(observed - forced, 0)

    if not info_const and header_forced:
        status = "CW_PARSE_RETROSPECTIVE"
        note = (
            f"every constant produced by this parse lies inside the "
            f"{forced} leading bits that are forced identical by the "
            f"values' span alone. The parse reveals nothing the "
            f"magnitudes did not already guarantee.")
    elif info_const:
        status = "CW_PARSE_RETROSPECTIVE"
        note = (
            f"fields {info_const} are constant beyond the {forced} "
            f"forced bits. That is worth a prospective test, but "
            f"retrospective structure still receives no semantic "
            f"promotion.")
    else:
        status = "CW_PARSE_HYPOTHESIS"
        note = "no constant structure under this parse."

    return ParseReport(
        parse=parse, header_bits=header_bits, field_bits=field_bits,
        n_fields=n_fields, headers=tuple(headers),
        fields=tuple(allfields), forced_common_bits=forced,
        observed_common_bits=observed,
        constant_fields_forced=tuple(forced_const),
        constant_fields_informative=tuple(info_const),
        header_is_forced=header_forced, informative_bits=informative,
        status=status, note=note)


# --------------------------------------------------------------------
# The matched null
# --------------------------------------------------------------------

def shared_prefix_null(values: tuple[int, ...], header_bits: int,
                       field_bits: int, n_fields: int, *,
                       n_draws: int, seed: int,
                       width: int = WORD_BITS) -> dict:
    """Draw random integers spanning the same range and re-run the parse.

    The null preserves the one property that matters — the span — and
    destroys everything else. If random numbers from the same interval
    show the same constant header and constant leading field as often
    as the real vectors do, the real vectors' structure is explained
    by the interval and nothing else.
    """
    rng = random.Random(seed)
    lo, hi = min(values), max(values)
    hits_header = 0
    hits_field0 = 0
    hits_both = 0
    for _ in range(n_draws):
        draw = tuple(rng.randint(lo, hi) for _ in values)
        heads, fields = [], []
        for v in draw:
            h, f = split_fields(v, header_bits, field_bits, n_fields,
                                width)
            heads.append(h)
            fields.append(f)
        hc = len(set(heads)) == 1
        f0 = len({f[0] for f in fields}) == 1
        hits_header += hc
        hits_field0 += f0
        hits_both += hc and f0
    return {
        "n_draws": n_draws,
        "seed": seed,
        "span": hi - lo,
        "p_constant_header": hits_header / n_draws,
        "p_constant_field0": hits_field0 / n_draws,
        "p_both": hits_both / n_draws,
        "note": ("random integers drawn from the same interval, with "
                 "no encoding whatsoever, reproduce the observed "
                 "constancy at this rate"),
    }


# --------------------------------------------------------------------
# Alternative parses, all reported
# --------------------------------------------------------------------

def decimal_segments(strings: tuple[str, ...] = SOURCE_STRINGS) -> dict:
    """Decimal pair/triplet parses, kept because the decoder law says
    every alternative must be shown."""
    return {
        s: {
            "pairs": [int(s[i:i + 2]) for i in range(0, len(s), 2)],
            "triplets": [int(s[i:i + 3]) for i in range(0, len(s), 3)],
            "digits": [int(c) for c in s],
        }
        for s in strings
    }


def all_parses(strings: tuple[str, ...] = SOURCE_STRINGS) -> dict:
    """Every frozen parse hypothesis, evaluated."""
    vals = as_ints(strings)
    return {
        "source_strings": list(strings),
        "values": list(vals),
        "bit_lengths": [v.bit_length() for v in vals],
        "identity": "38 = 2 + 3*12 = 2 + 6*6",
        "identity_note": (
            "this is a fact about the integer 38. EVERY 38-bit value "
            "admits both parses, so admitting them is not a property "
            "of these particular numbers."),
        "forced_common_bits": forced_common_bits(vals),
        "observed_common_bits": observed_common_bits(vals),
        "header2_plus_3x12": parse_report(
            vals, 2, 12, 3, "HEADER2_PLUS_3X12").as_record(),
        "header2_plus_6x6": parse_report(
            vals, 2, 6, 6, "HEADER2_PLUS_6X6").as_record(),
        "decimal_segments": decimal_segments(strings),
        "hypotheses_frozen": list(PARSE_HYPOTHESES),
    }


# --------------------------------------------------------------------
# The frozen decoder
# --------------------------------------------------------------------

@dataclass(frozen=True)
class FrozenDecoder:
    """A decoder pinned before future vectors exist.

    The freeze hash covers the parse definition. Changing any field
    boundary changes the hash, which is what makes "we did not move
    the goalposts" checkable rather than assertable.
    """

    parse: str
    header_bits: int
    field_bits: int
    n_fields: int
    width: int = WORD_BITS
    frozen_at_commit: str = "v5.0-R7"

    def digest(self) -> str:
        blob = (f"{self.parse}|{self.header_bits}|{self.field_bits}|"
                f"{self.n_fields}|{self.width}")
        return hashlib.sha256(blob.encode()).hexdigest()

    def decode(self, value: int) -> dict:
        h, f = split_fields(value, self.header_bits, self.field_bits,
                            self.n_fields, self.width)
        return {"header": h, "fields": list(f),
                "decoder": self.digest(),
                "semantics": None,
                "note": ("syntax only; no field has a declared "
                         "meaning (core/02 decoder law)")}


FROZEN_DECODERS = (
    FrozenDecoder("HEADER2_PLUS_3X12", 2, 12, 3),
    FrozenDecoder("HEADER2_PLUS_6X6", 2, 6, 6),
)


def reassign_fields(*args, **kwargs):
    """Always refuses. After-the-fact field reassignment is banned."""
    raise CWRefused(
        "field boundaries may not be reassigned after seeing new "
        "vectors. The decoder is frozen and identified by its digest; "
        "a different layout is a different decoder and must be "
        "declared as a new hypothesis before the data arrive "
        "(core/02 decoder law).")


def promote(current: str, *, prospective_vectors: int = 0,
            controlled_command_correlation: bool = False,
            independent_replication: bool = False) -> str:
    """Advance the CW ladder, gated on evidence that does not exist yet."""
    if current not in CW_STATUSES:
        raise ValueError(f"unknown status {current!r}")
    if current == "CW_PARSE_RETROSPECTIVE":
        if prospective_vectors <= 0:
            return current
        return "CW_PARSE_PROSPECTIVE_SUPPORT"
    if current == "CW_PARSE_PROSPECTIVE_SUPPORT":
        if not controlled_command_correlation:
            return current
        if not independent_replication:
            return current
        return "CW_SEMANTICS_CONFIRMED"
    return current


def status_report() -> dict:
    """The P02 headline, computed rather than asserted."""
    vals = as_ints()
    rep12 = parse_report(vals, 2, 12, 3, "HEADER2_PLUS_3X12")
    null12 = shared_prefix_null(vals, 2, 12, 3, n_draws=20_000,
                                seed=20260718)
    rep6 = parse_report(vals, 2, 6, 6, "HEADER2_PLUS_6X6")
    null6 = shared_prefix_null(vals, 2, 6, 6, n_draws=20_000,
                               seed=20260719)
    return {
        "claim": "the five CW strings encode a header plus 4096-state "
                 "fields",
        "status": "CW_PARSE_RETROSPECTIVE",
        "forced_common_bits": rep12.forced_common_bits,
        "observed_common_bits": rep12.observed_common_bits,
        "informative_bits": rep12.informative_bits,
        "header_is_forced_by_span": rep12.header_is_forced,
        "constant_fields_forced": list(rep12.constant_fields_forced),
        "constant_fields_informative":
            list(rep12.constant_fields_informative),
        "null_3x12_p_both": null12["p_both"],
        "null_6x6_p_both": null6["p_both"],
        "verdict": (
            "The shared header and shared leading field are forced by "
            "the values' span, not by any encoding. Random integers "
            "drawn from the same interval reproduce the same "
            "'structure' at a rate of "
            f"{null12['p_both']:.3f}. The observation is compatible "
            "with a protocol and is equally compatible with five "
            "arbitrary numbers that happen to be close together, so "
            "it discriminates between them not at all."),
        "what_would_settle_it": (
            "Prospective vectors decoded by the frozen decoder "
            "without changing field boundaries, ideally with a "
            "controlled command whose effect is predicted before it "
            "is applied. Nothing retrospective can do this."),
        "ceiling": "CW_PARSE_RETROSPECTIVE",
    }
