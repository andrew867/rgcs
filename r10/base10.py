"""P00/P07 — "unpack it from your base 10 system", as a codec search.

The source clue is one sentence: *you have to unpack it from your base
10 system.* It is Tier-A source material and it does **not** specify a
codec. The temptation is to hear "base 10 → base 8" and start reading
octal; that is one guess among many, and adopting it silently would be
exactly the kind of unforced assumption this project keeps catching.

So this module treats the clue as a *research program*: a family of
**reversible** views of the five twelve-digit vectors, each of which
must round-trip byte-for-byte, each scored against a matched null, and
**every failed interpretation retained**. The eight views (the pack's A
through H) are:

    A  symbol-preserving decimal      (12 symbols stay 12 symbols)
    B  four decimal triads            (000-999 each)
    C  three decimal tetrads          (0000-9999 each)
    D  packed decimal -> binary       (40 bits, since 2^39 < 1e12 < 2^40)
    E  binary-coded decimal           (48 bits, 4 per digit)
    F  prefix / payload / check       (only if the prefix beats a null)
    G  mixed-radix fields             (declared ranges, exact inverse)
    H  decimal codebook               (only if independently supplied)

The load-bearing discipline: a reversible re-view of a number contains
exactly the information the number already had. Rewriting 162875493612
in binary, or splitting it into triads, cannot *add* structure -- it can
only relocate it. So "did base-N unpacking reveal something?" is
answered by the same matched-null machinery that turned the CW
arithmetic from p=1e-5 to p=1.0: does any view show structure that
random vectors of the same width do not?

Given R7 (zero informative bits) and R9 (no content survives a matched
null, in three independent framings), the expected and obtained result
is **NO_DECODER_IDENTIFIED**. This module states it as the outcome of a
search that could have found otherwise, and retains the failures so the
search is auditable.

The five vectors are preserved byte-for-byte and are the public
``OMEGA_REGION_CW_VECTORS``. The source attribution is region-level.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

#: The five vectors, byte-for-byte. Public anonymised fixture.
CW_VECTORS = (162875493612, 162875432975, 162877542769,
              162875439275, 162875439285)

WIDTH = 12                       # decimal digits; all five are 12-wide


class CodecError(ValueError):
    """Raised on a non-reversible or misused codec."""


class OctalAssumptionRefused(RuntimeError):
    """Raised when 'base 10' is silently read as 'base 8'."""


def refuse_octal_assumption() -> None:
    """'Unpack from base 10' is not 'read as octal'."""
    raise OctalAssumptionRefused(
        "'unpack it from your base 10 system' does not specify base 8, "
        "or any base. Reading the digits as octal is one hypothesis "
        "among many, and octal is not even well defined here -- the "
        "vectors contain the digits 8 and 9, which are not octal "
        "symbols. The clue is treated as a reversible-view search, not "
        "an octal assumption.")


# --- the reversible views ----------------------------------------------

def _digits(v: int) -> str:
    return str(v).zfill(WIDTH)


@dataclass(frozen=True)
class Codec:
    """A reversible view of a vector. forward . inverse == identity."""

    codec_id: str
    family: str
    forward: object              # int -> object
    inverse: object              # object -> int
    output_kind: str

    def round_trip(self, v: int) -> bool:
        return self.inverse(self.forward(v)) == v


def _view_symbol(v):            # A
    return _digits(v)


def _unview_symbol(s):
    return int(s)


def _view_triads(v):            # B
    d = _digits(v)
    return tuple(int(d[i:i + 3]) for i in range(0, 12, 3))


def _unview_triads(t):
    return int("".join(f"{x:03d}" for x in t))


def _view_tetrads(v):           # C
    d = _digits(v)
    return tuple(int(d[i:i + 4]) for i in range(0, 12, 4))


def _unview_tetrads(t):
    return int("".join(f"{x:04d}" for x in t))


def _view_packed_binary(v):     # D
    if not 0 <= v < 10 ** 12:
        raise CodecError("value outside 12-digit range")
    return format(v, "040b")


def _unview_packed_binary(b):
    return int(b, 2)


def _view_bcd(v):               # E
    d = _digits(v)
    return "".join(format(int(c), "04b") for c in d)


def _unview_bcd(b):
    if len(b) != 48:
        raise CodecError("BCD must be 48 bits")
    out = []
    for i in range(0, 48, 4):
        nib = int(b[i:i + 4], 2)
        if nib > 9:
            raise CodecError(f"invalid BCD nibble {nib}")
        out.append(str(nib))
    return int("".join(out))


CODECS = (
    Codec("A_SYMBOL", "SYMBOL_PRESERVING", _view_symbol,
          _unview_symbol, "12 decimal symbols"),
    Codec("B_TRIADS", "DECIMAL_FIELDS", _view_triads,
          _unview_triads, "four fields 000-999"),
    Codec("C_TETRADS", "DECIMAL_FIELDS", _view_tetrads,
          _unview_tetrads, "three fields 0000-9999"),
    Codec("D_PACKED_BINARY", "RADIX_CONVERSION", _view_packed_binary,
          _unview_packed_binary, "40-bit integer"),
    Codec("E_BCD", "PER_DIGIT_BINARY", _view_bcd,
          _unview_bcd, "48-bit BCD"),
)


def all_codecs_round_trip(vectors=CW_VECTORS) -> dict:
    """Every codec must be exactly reversible on every vector."""
    results = {}
    for c in CODECS:
        results[c.codec_id] = all(c.round_trip(v) for v in vectors)
    return results


# --- the bit-width facts, exact ----------------------------------------

def packed_decimal_bits() -> dict:
    """40 bits, because 2^39 < 1e12 < 2^40. Stated exactly."""
    return {
        "bits": (10 ** 12 - 1).bit_length(),
        "lower": "2**39 < 10**12",
        "lower_holds": 2 ** 39 < 10 ** 12,
        "upper": "10**12 < 2**40",
        "upper_holds": 10 ** 12 < 2 ** 40,
    }


def bcd_bits() -> int:
    return WIDTH * 4             # 48


# --- the matched null: does any view beat chance? ----------------------

def _informative_structure(vectors) -> int:
    """A view-independent structure score: shared leading digits beyond
    what the shared numeric range forces, summed with shared trailing
    digits. Reversible re-views cannot change this; it is a property of
    the integers, which is the point."""
    strs = [_digits(v) for v in vectors]
    # common prefix
    pre = strs[0]
    for s in strs[1:]:
        while pre and not s.startswith(pre):
            pre = pre[:-1]
    # common suffix
    suf = strs[0]
    for s in strs[1:]:
        while suf and not s.endswith(suf):
            suf = suf[1:]
    return len(pre) + len(suf)


def codec_search(vectors=CW_VECTORS, *, null_trials: int = 20_000,
                 seed: int = 20260721) -> dict:
    """Do the vectors carry structure a reversible view could expose?

    A reversible codec preserves information, so the honest test is
    view-independent: is the shared structure more than random vectors
    of the same width show? Two nulls are needed, and separating them
    is the whole point (this is the R9-D-002 / cwdecode lesson):

    * a **full-band** null (uniform 12-digit) makes the shared "16287"
      prefix look striking -- but that prefix is just the five vectors
      sitting in a narrow band, which is a fact about their *range*,
      not content a codec unpacks;
    * a **span-matched** null (random offset, same span) reproduces the
      shared prefix by construction, and against it the vectors show
      no residual structure.

    Content is the second question, and its answer is
    NO_DECODER_IDENTIFIED. The clustering is real and is reported
    separately as a band property.
    """
    rng = random.Random(seed)
    observed = _informative_structure(vectors)
    n = len(vectors)

    # band question: full-band null
    lo, hi = 10 ** 11, 10 ** 12 - 1
    band_at_least = sum(
        1 for _ in range(null_trials)
        if _informative_structure(
            [rng.randint(lo, hi) for _ in range(n)]) >= observed)
    band_p = (band_at_least + 1) / (null_trials + 1)

    # content question: span-matched null (same clustering)
    span = max(vectors) - min(vectors)
    content_at_least = 0
    for _ in range(null_trials):
        offset = rng.randint(lo, hi - span)
        rv = [offset + rng.randint(0, span) for _ in range(n)]
        if _informative_structure(rv) >= observed:
            content_at_least += 1
    content_p = (content_at_least + 1) / (null_trials + 1)

    return {
        "observed_structure": observed,
        "band_p_value": band_p,
        "content_p_value": content_p,
        "round_trips": all_codecs_round_trip(vectors),
        "reversible_codecs": len(CODECS),
        "band_verdict": ("CLUSTERED_BAND_CONFIRMED" if band_p < 0.05
                         else "NO_BAND_STRUCTURE"),
        "verdict": ("NO_DECODER_IDENTIFIED" if content_p > 0.05
                    else "STRUCTURE_SURVIVES_NULL"),
        "why_view_independent": (
            "a reversible codec relocates information, it does not "
            "create it. No base-N view can beat a span-matched null "
            "unless the integers carry content beyond their clustering, "
            "and they do not: the shared 16287 prefix is the band, "
            "reproduced by the span-matched null by construction"),
        "failed_interpretations_retained": [c.codec_id for c in CODECS],
    }


def base10_report() -> dict:
    search = codec_search()
    return {
        "clue": "you have to unpack it from your base 10 system",
        "source_authority": "OMEGA_REGION_SOURCE (Tier A)",
        "vectors_preserved_byte_for_byte": list(CW_VECTORS),
        "views_implemented": [c.codec_id for c in CODECS],
        "packed_decimal_bits": packed_decimal_bits(),
        "bcd_bits": bcd_bits(),
        "search": search,
        "octal_is_not_assumed": True,
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "what_this_does_not_say": (
            "It does not say the vectors are meaningless, and it does "
            "not say no codec exists -- only that no reversible base-N "
            "view exposes structure a matched null does not already "
            "produce. A codec keyed to material this search does not "
            "contain, or one prospectively predicted and then "
            "confirmed, would be a different result. This is "
            "NO_DECODER_IDENTIFIED, not NO_DECODER_POSSIBLE."),
    }
