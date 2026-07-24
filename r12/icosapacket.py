"""R12 — the icosahedral packet grammar: F5 | Q22 | S3, and the prefix
that is a fact about range rather than about content.

A thirty-bit word splits, exactly and without remainder, into three
fields::

    F5  |  Q22  |  S3
     5      22      3      = 30 bits

* **F5** — five bits of face identity. Twenty faces need
  ``ceil(log2 20) = 5`` bits, and five bits hold thirty-two codes, so
  the values 20..31 are patterns the field can carry and the solid
  cannot. They are OUT OF RANGE and are refused rather than folded,
  wrapped or clamped: a face index of 27 is not a face, and silently
  reducing it modulo twenty would manufacture a face assignment out of
  a malformed word.
* **Q22** — twenty-two bits read as **eleven quaternary levels of two
  bits each**. Each level picks one of four sub-triangles, so the field
  is a refinement path down a triangular subdivision, most significant
  level first.
* **S3** — three bits of shell. Eight shells, ``2**3 = 8``, exactly: the
  field is full, with no spare codes and nothing to refuse.

Thirty bits is also ten octal digits (``10 * 3 = 30``), so the word
serializes into octal with no padding and no ambiguity, and
:func:`refuse_decimal_digits_as_octal` keeps the symbols 8 and 9 out of
a base that does not contain them.

**The headline null.** Five registered vectors decode cleanly under this
grammar, and all five share a thirteen-bit binary prefix, a four-digit
decimal prefix, a four-digit octal prefix and a four-symbol quaternary
path prefix. That looks like shared content. It is not. The five numbers
lie within a span of 49,491, and numbers that close together are
*obliged* to agree in their leading bits: a span ``S`` forces agreement
in roughly ``30 - ceil(log2 S)`` leading bits, here about fourteen. The
observed thirteen is not more than the band requires -- it is slightly
less. :func:`band_clustering_null` makes the point by drawing random
values from the same band and measuring their shared prefix; they share
a comparable one, the p-value is not small, and the verdict is
``EXPLAINED_BY_RANGE``. This is the R10.6 band-clustering lesson in a
new frame, and :func:`refuse_prefix_as_content` refuses the inference it
invites. The same machinery has POWER: given a band it does *not*
explain, :func:`power_control_planted_prefix` shows the test flags a
prefix that really is longer than the range accounts for.

**Two layouts, neither privileged.** The same thirty bits also parse as
``H13 | L14 | S3`` -- a thirteen-bit header, a fourteen-bit local field
and the same three shell bits. Both consume the whole word, both are
self-consistent, and nothing inside the words chooses between them.
:func:`layouts` returns both, and :func:`refuse_single_layout` raises
unless one was PREREGISTERED, because picking the layout whose output
reads better is picking the answer.

**The grammar is not a decoder.** A word parses into a face, a path and
a shell; that is arithmetic. It becomes a place only when five separate
things are frozen independently of the result -- face numbering, body
orientation, magnetic root, handedness and shell projection -- and none
of them is frozen here. :func:`refuse_geographic_decode` raises
unconditionally, and :func:`decode_to_location` raises while any
prerequisite is UNFROZEN; with all five frozen it still returns only
``GRAMMAR_ONLY_NO_GEOGRAPHIC_CLAIM``, because five frozen conventions
make a coordinate system, not an observation.

Nothing here is measured. The standing verdict is
**ICOSAHEDRAL_PACKET_GRAMMAR_VALID_NOT_A_GEOGRAPHIC_DECODER**.
"""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

# =======================================================================
# Claim classes and the standing verdict
# =======================================================================


class ClaimClass(Enum):
    """The claim classes this repository is allowed to emit."""

    EXACT_IDENTITY = "EXACT_IDENTITY"
    SOURCE_ESTABLISHED_PHYSICS = "SOURCE_ESTABLISHED_PHYSICS"
    REPOSITORY_COMPUTATIONAL_RESULT = "REPOSITORY_COMPUTATIONAL_RESULT"
    ENGINEERING_CANDIDATE = "ENGINEERING_CANDIDATE"
    RETROSPECTIVE_NUMERIC_MATCH = "RETROSPECTIVE_NUMERIC_MATCH"
    PROSPECTIVE_PREDICTION = "PROSPECTIVE_PREDICTION"
    BENCH_MEASUREMENT = "BENCH_MEASUREMENT"
    UNSUPPORTED = "UNSUPPORTED"
    BLOCKED_MISSING_DATA = "BLOCKED_MISSING_DATA"


VERDICT = "ICOSAHEDRAL_PACKET_GRAMMAR_VALID_NOT_A_GEOGRAPHIC_DECODER"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"


class IcosaPacketError(ValueError):
    """Raised on an out-of-range field, a malformed word, a decimal
    string parsed as octal, a layout privileged without preregistration,
    a shared prefix read as content, or any geographic decode."""


# =======================================================================
# The grammar: field widths, exactly
# =======================================================================

#: Faces of the icosahedron. Five bits are needed and five bits are used.
FACE_COUNT = 20
FACE_BITS = 5                                   # ceil(log2 20) == 5
FACE_CODES = 1 << FACE_BITS                     # 32 patterns for 20 faces

#: The quaternary refinement path: eleven levels of two bits.
QUATERNARY_LEVELS = 11
BITS_PER_LEVEL = 2                              # one of four sub-triangles
PATH_BITS = QUATERNARY_LEVELS * BITS_PER_LEVEL  # 22

#: The shell field. Eight shells in three bits: exactly full.
SHELL_COUNT = 8
SHELL_BITS = 3                                  # 2**3 == 8

#: The whole word.
WORD_CAPACITY_BITS = FACE_BITS + PATH_BITS + SHELL_BITS      # 30
WORD_OCTAL_DIGITS = WORD_CAPACITY_BITS // 3                  # 10
WORD_MODULUS = 1 << WORD_CAPACITY_BITS

#: The alternative parse. Same thirty bits, different fields.
ALT_HEADER_BITS = 13
ALT_LOCAL_BITS = 14
ALT_SHELL_BITS = SHELL_BITS                                  # 3

_FACE_SHIFT = PATH_BITS + SHELL_BITS            # 25
_PATH_MASK = (1 << PATH_BITS) - 1
_SHELL_MASK = (1 << SHELL_BITS) - 1


def field_widths() -> dict:
    """State the width arithmetic exactly. Every sum is checked here."""
    return {
        "face_bits": FACE_BITS,
        "face_count": FACE_COUNT,
        "face_bits_are_minimal": (
            (1 << (FACE_BITS - 1)) < FACE_COUNT <= (1 << FACE_BITS)),
        "face_codes": FACE_CODES,
        "face_codes_out_of_range": FACE_CODES - FACE_COUNT,   # 12
        "quaternary_levels": QUATERNARY_LEVELS,
        "bits_per_level": BITS_PER_LEVEL,
        "path_bits": PATH_BITS,
        "path_bits_exact": QUATERNARY_LEVELS * BITS_PER_LEVEL == PATH_BITS,
        "shell_bits": SHELL_BITS,
        "shell_count": SHELL_COUNT,
        "shell_field_is_exactly_full": (1 << SHELL_BITS) == SHELL_COUNT,
        "word_capacity_bits": WORD_CAPACITY_BITS,
        "word_bits_sum_exactly": (
            FACE_BITS + PATH_BITS + SHELL_BITS == WORD_CAPACITY_BITS),
        "word_octal_digits": WORD_OCTAL_DIGITS,
        "octal_digits_exact": WORD_OCTAL_DIGITS * 3 == WORD_CAPACITY_BITS,
        "claim_class": ClaimClass.EXACT_IDENTITY.value,
    }


# =======================================================================
# Octal hygiene: 8 and 9 are not octal symbols
# =======================================================================

def refuse_decimal_digits_as_octal(s: str) -> None:
    """Refuse to read a string as octal when it cannot be one.

    Base 8 has the symbols 0..7. A string containing 8 or 9 has no octal
    value whatever, so parsing it as octal is not a lenient reading; it
    is a category error that quietly yields a different number and then
    presents it as the same one. Carried forward unchanged from the
    R10.6/R11 octal discipline."""
    if not isinstance(s, str):
        raise IcosaPacketError("octal candidate must be a string")
    if not s:
        raise IcosaPacketError("empty octal string has no value")
    bad = sorted({c for c in s if c in "89"})
    if bad:
        raise IcosaPacketError(
            f"refused: {s!r} contains the decimal digit(s) "
            f"{','.join(bad)}, which are not octal symbols. Base 8 has "
            f"only 0..7, so this string has no octal value at all. "
            f"Reading it as octal would silently produce a different "
            f"number and label it the same one.")
    for c in s:
        if c not in "01234567":
            raise IcosaPacketError(
                f"refused: {s!r} contains {c!r}, which is not an octal "
                f"symbol")


def parse_octal_word(s: str) -> int:
    """Parse a ten-digit octal word, refusing 8 and 9 explicitly first."""
    refuse_decimal_digits_as_octal(s)
    if len(s) != WORD_OCTAL_DIGITS:
        raise IcosaPacketError(
            f"a {WORD_CAPACITY_BITS}-bit word is exactly "
            f"{WORD_OCTAL_DIGITS} octal digits, got {len(s)}")
    return int(s, 8)


# =======================================================================
# Encode / decode: exact inverses
# =======================================================================

def _check_int(value, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise IcosaPacketError(f"{name} must be a plain int")
    return value


def normalise_path(path) -> str:
    """Canonicalise a refinement path to eleven quaternary symbols.

    Accepts the canonical string form ``"33012032222"`` or any iterable
    of eleven ints in 0..3, most significant level first."""
    if isinstance(path, str):
        digits = list(path)
    else:
        try:
            digits = [str(_check_int(d, "path level")) for d in path]
        except TypeError as exc:
            raise IcosaPacketError(
                "path must be a string or an iterable of ints") from exc
    if len(digits) != QUATERNARY_LEVELS:
        raise IcosaPacketError(
            f"a refinement path has exactly {QUATERNARY_LEVELS} levels, "
            f"got {len(digits)}")
    for d in digits:
        if d not in "0123":
            raise IcosaPacketError(
                f"quaternary level {d!r} outside 0..3; each level picks "
                f"one of four sub-triangles and there is no fifth")
    return "".join(digits)


def path_levels(path) -> tuple:
    """The refinement path as a tuple of eleven ints, MSB level first."""
    return tuple(int(c) for c in normalise_path(path))


def encode(face: int, path, shell: int) -> int:
    """Pack ``F5 | Q22 | S3`` into one thirty-bit word.

    Exactly inverted by :func:`decode`. Out-of-range fields raise: face
    codes 20..31 exist in the field and not on the solid, so they are
    refused rather than reduced."""
    _check_int(face, "face")
    _check_int(shell, "shell")
    if not 0 <= face < FACE_COUNT:
        raise IcosaPacketError(
            f"face {face} is out of range: the icosahedron has "
            f"{FACE_COUNT} faces (0..{FACE_COUNT - 1}). The five-bit "
            f"field carries {FACE_CODES} codes, so "
            f"{FACE_COUNT}..{FACE_CODES - 1} are patterns the field can "
            f"hold and the solid cannot. They are refused, not reduced "
            f"modulo {FACE_COUNT}: wrapping would manufacture a face "
            f"assignment out of a malformed word.")
    if not 0 <= shell < SHELL_COUNT:
        raise IcosaPacketError(
            f"shell {shell} outside 0..{SHELL_COUNT - 1}; the three-bit "
            f"shell field is exactly full")
    levels = path_levels(path)
    code = 0
    for level in levels:
        code = (code << BITS_PER_LEVEL) | level
    return (face << _FACE_SHIFT) | (code << SHELL_BITS) | shell


def decode(word: int) -> tuple:
    """Invert :func:`encode`: ``(face, path, shell)``. Exact.

    ``path`` comes back in the canonical eleven-symbol string form."""
    _check_int(word, "word")
    if not 0 <= word < WORD_MODULUS:
        raise IcosaPacketError(
            f"word {word} does not fit in {WORD_CAPACITY_BITS} bits")
    face = word >> _FACE_SHIFT
    code = (word >> SHELL_BITS) & _PATH_MASK
    shell = word & _SHELL_MASK
    if face >= FACE_COUNT:
        raise IcosaPacketError(
            f"refused: the face field of word {word} decodes to {face}, "
            f"which is one of the {FACE_CODES - FACE_COUNT} five-bit "
            f"codes ({FACE_COUNT}..{FACE_CODES - 1}) that no face of the "
            f"icosahedron carries. The word is malformed under this "
            f"grammar and is refused rather than folded onto a face.")
    digits = [str((code >> (BITS_PER_LEVEL * k)) & 0x3)
              for k in range(QUATERNARY_LEVELS - 1, -1, -1)]
    return face, "".join(digits), shell


def word_bits(word: int) -> str:
    """The word as exactly thirty binary symbols."""
    _check_int(word, "word")
    if not 0 <= word < WORD_MODULUS:
        raise IcosaPacketError(
            f"word {word} does not fit in {WORD_CAPACITY_BITS} bits")
    return format(word, f"0{WORD_CAPACITY_BITS}b")


def word_octal(word: int) -> str:
    """The word as exactly ten octal digits."""
    _check_int(word, "word")
    if not 0 <= word < WORD_MODULUS:
        raise IcosaPacketError(
            f"word {word} does not fit in {WORD_CAPACITY_BITS} bits")
    return format(word, f"0{WORD_OCTAL_DIGITS}o")


def decode_record(word: int) -> dict:
    """Every consistent rendering of one word, with its round-trip."""
    face, path, shell = decode(word)
    bits = word_bits(word)
    octal = word_octal(word)
    return {
        "word": word,
        "bits": bits,
        "octal": octal,
        "decimal": str(word),
        "face": face,
        "path": path,
        "path_levels": path_levels(path),
        "shell": shell,
        "face_bits": bits[:FACE_BITS],
        "path_bits": bits[FACE_BITS:FACE_BITS + PATH_BITS],
        "shell_bits": bits[FACE_BITS + PATH_BITS:],
        "round_trip": encode(face, path, shell) == word,
        "octal_round_trip": parse_octal_word(octal) == word,
        "claim_class": ClaimClass.EXACT_IDENTITY.value,
    }


# =======================================================================
# The five registered vectors
# =======================================================================

@dataclass(frozen=True)
class PacketVector:
    """One registered word with its decode, stated in full."""

    vector_id: str
    value: int
    face: int
    path: str
    shell: int
    octal: str

    def verify(self) -> bool:
        face, path, shell = decode(self.value)
        return (face == self.face and path == self.path
                and shell == self.shell
                and word_octal(self.value) == self.octal
                and encode(face, path, shell) == self.value)


#: The five registered vectors, with the decode reproduced exactly.
REGISTERED_VECTORS = (
    PacketVector("PACKET_VECTOR_A", 165879123, 4, "33012032222", 3,
                 "1170616523"),
    PacketVector("PACKET_VECTOR_B", 165829763, 4, "33010232100", 3,
                 "1170456203"),
    PacketVector("PACKET_VECTOR_C", 165874293, 4, "33012011032", 5,
                 "1170605165"),
    PacketVector("PACKET_VECTOR_D", 165878965, 4, "33012032112", 5,
                 "1170616265"),
    PacketVector("PACKET_VECTOR_E", 165879253, 4, "33012032322", 5,
                 "1170616725"),
)

REGISTERED_VALUES = tuple(v.value for v in REGISTERED_VECTORS)


def verify_registered_vectors() -> dict:
    """Decode all five and check every field against the register."""
    rows = [{
        "vector_id": v.vector_id,
        "value": v.value,
        "bits": word_bits(v.value),
        "face": v.face,
        "path": v.path,
        "shell": v.shell,
        "octal": v.octal,
        "verified": v.verify(),
    } for v in REGISTERED_VECTORS]
    return {
        "rows": rows,
        "all_verified": all(r["verified"] for r in rows),
        "count": len(rows),
        "claim_class": ClaimClass.EXACT_IDENTITY.value,
    }


# =======================================================================
# Collision audit: the grammar must be injective
# =======================================================================

def collision_scan(words) -> dict:
    """Verify that distinct words decode to distinct ``(face, path, shell)``.

    A grammar that is a bijection on its own field space cannot collide;
    the scan is here so that claim is checked rather than assumed, and so
    a future layout change that broke injectivity would be caught."""
    seen: dict = {}
    collisions = []
    count = 0
    for w in words:
        count += 1
        key = decode(w)
        if key in seen and seen[key] != w:
            collisions.append((seen[key], w, key))
        else:
            seen.setdefault(key, w)
    return {
        "count": count,
        "distinct_decodes": len(seen),
        "collisions": collisions,
        "collision_count": len(collisions),
        "injective": not collisions,
        "collision_class": "INJECTIVE" if not collisions else "COLLIDING",
        "claim_class": ClaimClass.EXACT_IDENTITY.value,
    }


# =======================================================================
# Two layouts. Neither is privileged.
# =======================================================================

@dataclass(frozen=True)
class PacketLayout:
    """One candidate parse of the same thirty bits."""

    layout_id: str
    fields: tuple                     # ((name, bits), ...) MSB first
    rationale: str

    @property
    def total_bits(self) -> int:
        return sum(b for _n, b in self.fields)

    def split(self, word: int) -> dict:
        """Split a word into this layout's fields, MSB first."""
        _check_int(word, "word")
        if not 0 <= word < WORD_MODULUS:
            raise IcosaPacketError(
                f"word {word} does not fit in {WORD_CAPACITY_BITS} bits")
        out = {}
        shift = self.total_bits
        for name, bits in self.fields:
            shift -= bits
            out[name] = (word >> shift) & ((1 << bits) - 1)
        return out


LAYOUT_FACE_PATH_SHELL = PacketLayout(
    layout_id="F5_Q22_S3",
    fields=(("face", FACE_BITS), ("path", PATH_BITS),
            ("shell", SHELL_BITS)),
    rationale=(
        "twenty faces need five bits, eleven quaternary refinement "
        "levels need twenty-two, eight shells need three"),
)

LAYOUT_HEADER_LOCAL_SHELL = PacketLayout(
    layout_id="H13_L14_S3",
    fields=(("header", ALT_HEADER_BITS), ("local", ALT_LOCAL_BITS),
            ("shell", ALT_SHELL_BITS)),
    rationale=(
        "a thirteen-bit header over a fourteen-bit local field and the "
        "same three shell bits; consumes the same thirty bits"),
)


def layouts() -> tuple:
    """Both candidate layouts, in registration order and unranked.

    They are COMPETING parses. Both consume the whole thirty-bit word,
    both are internally consistent, and nothing inside the words picks
    one. Returning them as a pair is the honest output; returning one is
    a decision, and a decision needs a reason that is not "it read
    better"."""
    return (LAYOUT_FACE_PATH_SHELL, LAYOUT_HEADER_LOCAL_SHELL)


def layout_table(word: int) -> dict:
    """One word split under every candidate layout, side by side."""
    return {
        "word": word,
        "bits": word_bits(word),
        "layouts": {ly.layout_id: {
            "fields": ly.split(word),
            "total_bits": ly.total_bits,
            "consumes_whole_word": ly.total_bits == WORD_CAPACITY_BITS,
            "rationale": ly.rationale,
        } for ly in layouts()},
        "layout_count": len(layouts()),
        "privileged_layout": None,
        "claim_class": ClaimClass.REPOSITORY_COMPUTATIONAL_RESULT.value,
    }


def refuse_single_layout(preregistered: str | None = None,
                         *_args, **_kwargs) -> PacketLayout:
    """Refuse to report one layout unless it was PREREGISTERED.

    Both parses fit the same bits perfectly, so a choice between them
    cannot come from the words; it comes from the reader. Choosing after
    looking at the output is choosing the output. With a layout named in
    advance this returns it -- still one candidate among two, now
    labelled by the commitment that selected it."""
    if preregistered is None:
        raise IcosaPacketError(
            f"refused: {len(layouts())} layouts parse these thirty bits "
            f"and none is privileged "
            f"({', '.join(ly.layout_id for ly in layouts())}). Both "
            f"consume the whole word and both are self-consistent, so "
            f"nothing in the data selects one; a layout picked after its "
            f"output was inspected is fitted, not tested. Preregister a "
            f"layout_id and pass it explicitly, or report layouts() in "
            f"full.")
    for ly in layouts():
        if ly.layout_id == preregistered:
            return ly
    raise IcosaPacketError(
        f"refused: {preregistered!r} is not a registered layout "
        f"({', '.join(ly.layout_id for ly in layouts())})")


# =======================================================================
# The shared prefix, and why it is a fact about range
# =======================================================================

def _as_values(values) -> tuple:
    vals = tuple(values)
    if len(vals) < 2:
        raise IcosaPacketError(
            "a shared prefix needs at least two values")
    for v in vals:
        _check_int(v, "value")
        if not 0 <= v < WORD_MODULUS:
            raise IcosaPacketError(
                f"value {v} does not fit in {WORD_CAPACITY_BITS} bits")
    return vals


def shared_prefix_bits(values, width: int = WORD_CAPACITY_BITS) -> int:
    """Length of the common leading binary prefix, in bits.

    Values are compared zero-padded to ``width`` bits, so the answer is
    a property of the fixed-width words and not of however many digits
    each happened to print."""
    vals = _as_values(values)
    rendered = [format(v, f"0{width}b") for v in vals]
    n = 0
    for i in range(width):
        column = {r[i] for r in rendered}
        if len(column) != 1:
            break
        n += 1
    return n


def common_prefix(strings) -> str:
    """The longest common leading substring of a collection of strings."""
    items = [str(s) for s in strings]
    if not items:
        return ""
    out = []
    for chars in zip(*items):
        if len(set(chars)) != 1:
            break
        out.append(chars[0])
    return "".join(out)


def prefix_expected_from_range(values,
                               width: int = WORD_CAPACITY_BITS) -> dict:
    """How many leading bits a span this narrow forces on its own.

    If every value lies inside a span ``S``, then at most ``ceil(log2 S)``
    low bits are free to vary, so about ``width - ceil(log2 S)`` leading
    bits must agree. The bound is approximate in one direction only: a
    span that straddles a power-of-two boundary can break the agreement
    early, which is why the *expected* prefix is an upper reference and
    an observed value at or below it carries no information at all.

    Exact arithmetic throughout: the span and its bit length are
    integers, and the fraction of the word the span occupies is a
    :class:`~fractions.Fraction`."""
    vals = _as_values(values)
    lo, hi = min(vals), max(vals)
    span = hi - lo + 1
    span_bits = (span - 1).bit_length() if span > 1 else 0
    expected = width - span_bits
    observed = shared_prefix_bits(vals, width)
    return {
        "count": len(vals),
        "min": lo,
        "max": hi,
        "span": span,
        "span_bits": span_bits,
        "expected_prefix_bits": expected,
        "observed_prefix_bits": observed,
        "excess_over_expected": observed - expected,
        "observed_exceeds_expected": observed > expected,
        "span_fraction_of_word": Fraction(span, WORD_MODULUS),
        "span_fraction_float": float(Fraction(span, WORD_MODULUS)),
        "width": width,
        "why": (
            f"values confined to a span of {span} leave at most "
            f"{span_bits} low bits free, so roughly {expected} leading "
            f"bits are forced to agree by the range alone. The observed "
            f"{observed} is a fact about how close these numbers are, "
            f"not about what they contain."),
        "claim_class": ClaimClass.EXACT_IDENTITY.value,
    }


DEFAULT_NULL_TRIALS = 2000
DEFAULT_NULL_SEED = 20260724

#: p at or below which the observed prefix would count as longer than
#: the band explains. Deliberately conventional: the point of the test
#: is the direction of the result, not a borderline call.
PREFIX_ALPHA = 0.05


def band_clustering_null(values, trials: int = DEFAULT_NULL_TRIALS,
                         seed: int = DEFAULT_NULL_SEED, *,
                         band: tuple | None = None) -> dict:
    """Draw random values from the SAME band and compare their prefixes.

    This is the whole argument, made empirically. The observed prefix is
    compared against the prefix that random numbers from the same narrow
    band happen to share; if the random draws share a comparable prefix,
    the observed one told us nothing beyond where the numbers live.

    ``band`` defaults to the closed interval spanned by ``values``. It
    can be supplied explicitly to ask a different question -- "is this
    prefix longer than a *wider* band would explain?" -- which is what
    :func:`power_control_planted_prefix` does.

    The p-value is the fraction of trials whose null prefix is at least
    as long as the observed one, with the usual add-one correction so it
    is never zero."""
    vals = _as_values(values)
    if not isinstance(trials, int) or isinstance(trials, bool) or trials < 1:
        raise IcosaPacketError("trials must be a positive int")
    if band is None:
        lo, hi = min(vals), max(vals)
    else:
        lo, hi = (int(band[0]), int(band[1]))
        if lo > hi:
            raise IcosaPacketError("band must be (low, high) with low <= high")
        if not (0 <= lo and hi < WORD_MODULUS):
            raise IcosaPacketError(
                f"band must lie inside 0..{WORD_MODULUS - 1}")
    observed = shared_prefix_bits(vals)
    rng = random.Random(seed)
    n = len(vals)
    at_least = 0
    total = 0
    longest = 0
    histogram: dict = {}
    for _ in range(trials):
        sample = [rng.randint(lo, hi) for _ in range(n)]
        p = shared_prefix_bits(sample)
        histogram[p] = histogram.get(p, 0) + 1
        total += p
        longest = max(longest, p)
        if p >= observed:
            at_least += 1
    p_value = (1 + at_least) / (trials + 1)
    explained = p_value > PREFIX_ALPHA
    return {
        "observed_prefix_bits": observed,
        "expected_prefix_bits": prefix_expected_from_range(
            vals)["expected_prefix_bits"],
        "band_low": lo,
        "band_high": hi,
        "band_span": hi - lo + 1,
        "trials": trials,
        "seed": seed,
        "null_mean_prefix_bits": total / trials,
        "null_max_prefix_bits": longest,
        "null_prefix_histogram": dict(sorted(histogram.items())),
        "trials_at_least_observed": at_least,
        "p_value": p_value,
        "alpha": PREFIX_ALPHA,
        "explained_by_range": explained,
        "verdict": "EXPLAINED_BY_RANGE" if explained
        else "PREFIX_EXCEEDS_BAND_EXPECTATION",
        "claim_class": ClaimClass.REPOSITORY_COMPUTATIONAL_RESULT.value,
        "what_this_shows": (
            "random values drawn from the same band share a prefix of "
            "comparable length, so the observed agreement is a "
            "consequence of the numbers being close together and is not "
            "evidence that they share content"),
    }


def power_control_planted_prefix(prefix_bits: int = 24, count: int = 5,
                                 trials: int = DEFAULT_NULL_TRIALS,
                                 seed: int = DEFAULT_NULL_SEED) -> dict:
    """POWER: a prefix the band does NOT explain is flagged.

    Values are planted to share ``prefix_bits`` leading bits and the null
    is run against the WHOLE thirty-bit space rather than their own tiny
    span. If :func:`band_clustering_null` could not distinguish that case
    from the registered one, its ``EXPLAINED_BY_RANGE`` verdict would be
    a property of the test rather than of the data."""
    if not 1 <= prefix_bits < WORD_CAPACITY_BITS:
        raise IcosaPacketError(
            f"prefix_bits must lie in 1..{WORD_CAPACITY_BITS - 1}")
    if count < 2:
        raise IcosaPacketError("need at least two planted values")
    rng = random.Random(seed + 1)
    free = WORD_CAPACITY_BITS - prefix_bits
    head = rng.getrandbits(prefix_bits) << free
    planted = []
    while len(planted) < count:
        v = head | rng.getrandbits(free)
        if v not in planted:
            planted.append(v)
    result = band_clustering_null(planted, trials, seed,
                                  band=(0, WORD_MODULUS - 1))
    return {
        "planted_prefix_bits": prefix_bits,
        "planted_values": tuple(planted),
        "observed_prefix_bits": result["observed_prefix_bits"],
        "p_value": result["p_value"],
        "explained_by_range": result["explained_by_range"],
        "detected": not result["explained_by_range"],
        "verdict": result["verdict"],
        "claim_class": ClaimClass.REPOSITORY_COMPUTATIONAL_RESULT.value,
        "note": (
            "against the full thirty-bit band a planted prefix is not "
            "explained by range and the test says so, which is what "
            "makes the EXPLAINED_BY_RANGE result on the registered "
            "vectors a finding rather than a blind spot"),
    }


def prefix_account(values=REGISTERED_VALUES) -> dict:
    """Every shared prefix of the registered vectors, with its cause."""
    vals = _as_values(values)
    return {
        "binary_prefix_bits": shared_prefix_bits(vals),
        "binary_prefix": common_prefix(
            [format(v, f"0{WORD_CAPACITY_BITS}b") for v in vals]),
        "decimal_prefix": common_prefix([str(v) for v in vals]),
        "octal_prefix": common_prefix([word_octal(v) for v in vals]),
        "path_prefix": common_prefix([decode(v)[1] for v in vals]),
        "range_expectation": prefix_expected_from_range(vals),
        "claim_class": ClaimClass.EXACT_IDENTITY.value,
        "interpretation": (
            "four prefixes in four bases, all of them the same fact: "
            "these numbers are close together. Agreement in the leading "
            "symbols of a fixed-width rendering is forced by proximity "
            "and carries no content"),
    }


def refuse_prefix_as_content(values=REGISTERED_VALUES,
                             *_args, **_kwargs) -> None:
    """Refuse to read a shared prefix as shared content.

    The inference is seductive because the agreement is exact and
    visible in four bases at once. It is still a statement about the
    numbers' magnitude. Values inside a narrow band MUST agree in their
    leading bits -- the band leaves them nowhere else to differ -- and a
    matched null drawn from that same band agrees just as much."""
    vals = _as_values(values)
    account = prefix_expected_from_range(vals)
    raise IcosaPacketError(
        f"refused: the {account['observed_prefix_bits']}-bit shared "
        f"prefix is not evidence of shared content. These "
        f"{account['count']} values lie within a span of "
        f"{account['span']}, which leaves only {account['span_bits']} "
        f"low bits free and therefore forces roughly "
        f"{account['expected_prefix_bits']} leading bits to agree "
        f"whatever the numbers mean. The observed prefix does not exceed "
        f"that -- it is {account['excess_over_expected']} bits relative "
        f"to the expectation -- and random values drawn from the same "
        f"band share a comparable one (band_clustering_null). This is "
        f"the R10.6 band-clustering lesson: a common prefix is a fact "
        f"about RANGE, and reading it as a common header, a common "
        f"origin or a common payload is reading the band back as a "
        f"finding.")


# =======================================================================
# Decoder discipline: five frozen things, and even then no geography
# =======================================================================

UNFROZEN = "UNFROZEN"

#: The five things that must each be frozen independently of the result
#: before this grammar could address anything physical.
DECODE_PREREQUISITE_FIELDS = (
    "face_numbering",
    "body_orientation",
    "magnetic_root",
    "handedness",
    "shell_projection",
)


@dataclass(frozen=True)
class DecodePrerequisites:
    """The five conventions a geographic reading would need frozen.

    Every field defaults to ``None`` -- UNFROZEN -- and that default is
    load-bearing. Each one is a free choice with several defensible
    settings; left open they multiply into a space large enough to place
    a word almost anywhere, and the setting that would be picked is
    whichever one puts it somewhere interesting."""

    face_numbering: str | None = None
    body_orientation: str | None = None
    magnetic_root: str | None = None
    handedness: str | None = None
    shell_projection: str | None = None

    def unfrozen(self) -> tuple:
        return tuple(n for n in DECODE_PREREQUISITE_FIELDS
                     if getattr(self, n) is None)

    def frozen(self) -> tuple:
        return tuple(n for n in DECODE_PREREQUISITE_FIELDS
                     if getattr(self, n) is not None)

    def all_frozen(self) -> bool:
        return not self.unfrozen()

    def status(self) -> dict:
        return {n: (getattr(self, n) if getattr(self, n) is not None
                    else UNFROZEN)
                for n in DECODE_PREREQUISITE_FIELDS}

    def commitment(self) -> str:
        """A sha256 over the five settings, for an audit trail."""
        parts = [f"{n}={getattr(self, n) or UNFROZEN}"
                 for n in DECODE_PREREQUISITE_FIELDS]
        return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()


#: The standing state of the five prerequisites in R12: none is frozen.
DEFAULT_PREREQUISITES = DecodePrerequisites()


def decode_to_location(word: int,
                       prerequisites: DecodePrerequisites
                       = DEFAULT_PREREQUISITES) -> dict:
    """Parse a word with the five prerequisites checked first.

    Raises while any prerequisite is UNFROZEN. With all five frozen it
    returns the grammar fields, the commitment over the conventions, and
    the status ``GRAMMAR_ONLY_NO_GEOGRAPHIC_CLAIM`` -- because five
    frozen conventions define a coordinate system, and a coordinate
    system is a way of naming places, not a measurement of one."""
    if not isinstance(prerequisites, DecodePrerequisites):
        raise IcosaPacketError("prerequisites must be a DecodePrerequisites")
    missing = prerequisites.unfrozen()
    if missing:
        raise IcosaPacketError(
            f"refused: {len(missing)} of {len(DECODE_PREREQUISITE_FIELDS)} "
            f"decode prerequisites are UNFROZEN ({', '.join(missing)}). "
            f"Each is an independent convention with several defensible "
            f"settings; left open they span a space that can place this "
            f"word almost anywhere, and the setting that gets chosen is "
            f"the one that lands somewhere worth reporting. Freeze all "
            f"five in advance, or read the word as grammar only.")
    face, path, shell = decode(word)
    return {
        "word": word,
        "face": face,
        "path": path,
        "shell": shell,
        "prerequisites": prerequisites.status(),
        "prerequisite_commitment": prerequisites.commitment(),
        "all_prerequisites_frozen": True,
        "status": "GRAMMAR_ONLY_NO_GEOGRAPHIC_CLAIM",
        "latitude": None,
        "longitude": None,
        "claim_class": ClaimClass.EXACT_IDENTITY.value,
        "why_still_no_location": (
            "freezing the five conventions makes the address "
            "well-defined; it does not make it an observation. A face "
            "number, a refinement path and a shell index are positions "
            "in a declared coordinate system, and no measurement "
            "anywhere in this repository ties that system to a body, a "
            "surface or a place"),
    }


def refuse_geographic_decode(*_args, **_kwargs) -> None:
    """Refuse a geographic decode. Always, without exception.

    Not "unless the prerequisites are frozen" -- freezing them is what
    :func:`decode_to_location` checks, and even a full freeze yields
    only ``GRAMMAR_ONLY_NO_GEOGRAPHIC_CLAIM``. This refusal is
    unconditional because the failure it guards against does not need a
    broken freeze: a clean parse into face, path and shell reads exactly
    like a coordinate, and the temptation to print it as one survives
    every amount of internal rigour."""
    raise IcosaPacketError(
        f"refused: this grammar is not a geographic decoder and cannot "
        f"become one here. A thirty-bit word parses into a face, an "
        f"eleven-level refinement path and a shell; that is arithmetic "
        f"about a bit layout. Turning it into a place requires "
        f"{len(DECODE_PREREQUISITE_FIELDS)} things frozen independently "
        f"of the result -- "
        f"{', '.join(DECODE_PREREQUISITE_FIELDS)} -- and none of them is "
        f"frozen in this repository. Even with all five frozen the "
        f"output is a position in a declared coordinate system, which is "
        f"a way of naming a place and not a measurement of one. The "
        f"standing verdict is {VERDICT}.")


# =======================================================================
# Fingerprint and report
# =======================================================================

def packet_fingerprint(values=REGISTERED_VALUES) -> str:
    """A stable hash over the registered decodes, for an audit trail."""
    parts = []
    for v in _as_values(values):
        face, path, shell = decode(v)
        parts.append(f"{v}:{face}:{path}:{shell}:{word_octal(v)}")
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()


def icosapacket_report() -> dict:
    null = band_clustering_null(REGISTERED_VALUES)
    power = power_control_planted_prefix()
    return {
        "what_this_is": (
            "a thirty-bit packet grammar F5 | Q22 | S3 with an exact "
            "round trip, a competing H13 | L14 | S3 parse, a "
            "band-clustering null over the shared prefix of five "
            "registered vectors, and an unconditional refusal to read "
            "any of it as geography"),
        "field_widths": field_widths(),
        "word_capacity_bits": WORD_CAPACITY_BITS,
        "word_octal_digits": WORD_OCTAL_DIGITS,
        "registered_vectors": verify_registered_vectors(),
        "prefix_account": prefix_account(),
        "band_clustering_null": null,
        "power_control": power,
        "layouts": [{"layout_id": ly.layout_id,
                     "fields": list(ly.fields),
                     "total_bits": ly.total_bits,
                     "rationale": ly.rationale} for ly in layouts()],
        "privileged_layout": None,
        "decode_prerequisites": DEFAULT_PREREQUISITES.status(),
        "prerequisites_all_frozen": DEFAULT_PREREQUISITES.all_frozen(),
        "fingerprint": packet_fingerprint(),
        "refusals": [
            "refuse_decimal_digits_as_octal",
            "refuse_single_layout",
            "refuse_prefix_as_content",
            "refuse_geographic_decode",
        ],
        "claim_class": ClaimClass.REPOSITORY_COMPUTATIONAL_RESULT.value,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not say the five registered vectors are "
            "meaningless, and it does not say no decoder exists. It says "
            "the thirty-bit grammar is arithmetically exact and "
            "arithmetically exact is all it is: the round trip proves "
            "the frame is faithful and proves nothing about content. The "
            "thirteen-bit prefix the five vectors share is a fact about "
            "their RANGE -- values inside a span of 49,491 are forced to "
            "agree in about fourteen leading bits, and random values "
            "from the same band share a comparable prefix -- so it is "
            "EXPLAINED_BY_RANGE and is not evidence of a common header "
            "or a common origin. A second layout parses the same bits "
            "just as cleanly and neither is privileged. No face "
            "numbering, body orientation, magnetic root, handedness or "
            "shell projection is frozen anywhere in this repository, so "
            "no word here addresses any place; with all five frozen the "
            "result would still be a position in a declared coordinate "
            "system rather than an observation. Nothing here is "
            "measured and no physical validation is claimed."),
    }


__all__ = [
    "ClaimClass", "IcosaPacketError", "VERDICT",
    "FACE_BITS", "PATH_BITS", "SHELL_BITS", "FACE_COUNT",
    "QUATERNARY_LEVELS", "SHELL_COUNT",
    "WORD_CAPACITY_BITS", "WORD_OCTAL_DIGITS",
    "ALT_HEADER_BITS", "ALT_LOCAL_BITS", "ALT_SHELL_BITS",
    "field_widths", "encode", "decode", "decode_record",
    "word_bits", "word_octal", "normalise_path", "path_levels",
    "parse_octal_word", "refuse_decimal_digits_as_octal",
    "PacketVector", "REGISTERED_VECTORS", "REGISTERED_VALUES",
    "verify_registered_vectors", "collision_scan",
    "PacketLayout", "layouts", "layout_table", "refuse_single_layout",
    "LAYOUT_FACE_PATH_SHELL", "LAYOUT_HEADER_LOCAL_SHELL",
    "shared_prefix_bits", "common_prefix", "prefix_expected_from_range",
    "band_clustering_null", "power_control_planted_prefix",
    "prefix_account", "refuse_prefix_as_content",
    "DecodePrerequisites", "DECODE_PREREQUISITE_FIELDS",
    "DEFAULT_PREREQUISITES", "decode_to_location",
    "refuse_geographic_decode", "packet_fingerprint",
    "icosapacket_report",
]
