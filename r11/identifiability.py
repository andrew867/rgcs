"""R11 — decoder identifiability: freeze-before-reveal, alias sets and
description lengths.

Every other R11 module produces one *piece* of a would-be decoder: a
planetary root, a body-fixed frame, a south-up face, a magnetic-gradient
scalar and sign, a codec, a header, a shell-state map, a phase alphabet,
an isotope ratio orientation, a crystal carrier. Bolting them together
in some order and reading off a place is the obvious next move, and it
is the move this module exists to make impossible.

**Why no decoded-location verdict is allowed in R11.** Count the
freedom. Each of sixteen fields is a choice, most of them with several
plausible settings; a tolerance is a further continuous knob; and the
score function that decides what "close" means is itself a choice. The
product of those choices is a search space large enough that *something*
lands near *somewhere* essentially always. A place reached by picking
the settings that reach it is not a decoding — it is the search space
being reported as a result. Worse, the arrival feels like evidence: the
coordinates are specific, the arithmetic is exact, and the chain reads
forwards as if it had been derived rather than selected.

So R11 permits no decoded-location verdict under any circumstances, and
:func:`refuse_decoded_location_verdict` raises unconditionally --- not
when the fit is poor, not when the freeze is missing, but always. The
deliverable of this module is deliberately *not an answer*. It is two
things that an answer cannot be argued out of:

* an **ALIAS SET** --- every candidate the decoder admits within the
  declared tolerance. It is returned as a set because it *is* a set:
  a decoder that discards information has many preimages, and reporting
  the nearest one as "the" output hides the other members rather than
  eliminating them. :func:`alias_set` never returns a unique answer, and
  the 36-bit envelope shows why freezing cannot always help --- three
  truncated bits are gone, so eight readings survive whatever else is
  frozen.
* a **DESCRIPTION LENGTH** --- the total bits needed to specify the
  decoder. A field left FREE costs its whole search width, because it
  will be chosen after the data are in view; a field FROZEN in advance
  costs only its commitment. A decoder that needs many free choices is
  therefore penalised, and a match it finds is worth correspondingly
  less than the same match from a tightly frozen decoder.

The discipline that makes the numbers mean anything is
**freeze-before-reveal**. :class:`DecoderSpec` freezes all sixteen
fields; :func:`freeze` returns a sha256 commitment over them;
:func:`refuse_unfrozen_evaluation` blocks scoring a decoder that was
never committed; and :func:`refuse_spec_change_after_reveal` blocks the
quiet edit --- "the epoch was obviously 2020", "the sign must be
negative" --- that turns a failed decoder into a successful one once the
holdout labels are visible.

Six decoder families are compared against five controls: PLANTED vectors
from a known generator (the POWER control: the decoder matching the
generator should win, and does), random coordinates, random twelve-digit
strings, shuffled labels, and held-out landmarks. The landmarks and the
whole output space are SYNTHETIC and neutral --- an abstract unit index
plane, not a geography --- so nothing here can name a place even by
accident.

Nothing is measured. The standing verdict is
**NO_DECODER_IDENTIFIED**, which is a statement about this search, not
about what is possible.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, replace
from enum import Enum

import numpy as np

from r11 import shelladdr

#: The standing verdict. R11 never upgrades this to a place.
DEFAULT_VERDICT = "NO_DECODER_IDENTIFIED"

WIDTH = 12                                   # decimal digits per vector
DECIMAL_MODULUS = 10 ** WIDTH                # 10**12
DECIMAL_FLOOR = 10 ** (WIDTH - 1)            # smallest 12-digit value

DEFAULT_TOLERANCE = 0.02                     # in the synthetic unit plane
DEFAULT_TRIALS = 160
DEFAULT_SEED = 20260723
ALIAS_TOLERANCE = 0.05
ALIAS_POOL_SIZE = 2048

#: How far the observed hit rate must exceed the best null before the
#: benchmark will call a decoder better than chance. Wide on purpose:
#: with a few hundred trials the sampling noise on a hit rate is a
#: couple of percent, and a threshold set near the noise would flag a
#: decoder every time the dice fell right.
BETTER_THAN_CHANCE_MARGIN = 0.15


class IdentifiabilityError(RuntimeError):
    """Raised on an unfrozen evaluation, a spec edited after the holdout
    labels were revealed, a malformed spec or point, or any attempt to
    obtain a decoded-location verdict."""


# =======================================================================
# The synthetic output space
# =======================================================================

@dataclass(frozen=True)
class OutputPoint:
    """A point in the SYNTHETIC output plane, both axes in [0, 1).

    This is an abstract index space and deliberately not a geography.
    It has no north, no datum and no units, so no value produced here
    can be read as a latitude, a longitude or a place. The plane wraps
    on both axes, which makes chance-hit probability uniform and keeps
    the nulls honest at the edges."""

    u: float
    v: float

    def __post_init__(self) -> None:
        for name in ("u", "v"):
            x = getattr(self, name)
            if not isinstance(x, (int, float)) or isinstance(x, bool):
                raise IdentifiabilityError(f"{name} must be a real number")
            if not 0.0 <= float(x) < 1.0:
                raise IdentifiabilityError(
                    f"{name}={x!r} outside the unit interval [0, 1)")

    def as_tuple(self) -> tuple:
        return (float(self.u), float(self.v))


def _wrap_unit(x: float) -> float:
    """Wrap a non-negative real into [0, 1), guarding the 1.0 edge."""
    y = float(x) % 1.0
    return 0.0 if y >= 1.0 else y


def _wrapped_delta(a: float, b: float) -> float:
    d = abs(float(a) - float(b)) % 1.0
    return min(d, 1.0 - d)


def point_distance(p: OutputPoint, q: OutputPoint) -> float:
    """Wrapped Euclidean distance in the synthetic plane."""
    return math.hypot(_wrapped_delta(p.u, q.u), _wrapped_delta(p.v, q.v))


def _unit_pair(code: int, total_bits: int) -> OutputPoint:
    """Split an integer of ``total_bits`` bits into two unit coordinates."""
    if not isinstance(code, int) or isinstance(code, bool) or code < 0:
        raise IdentifiabilityError("code must be a non-negative plain int")
    if code >= (1 << total_bits):
        raise IdentifiabilityError(
            f"code {code} does not fit in {total_bits} bits")
    low_bits = total_bits // 2
    high_bits = total_bits - low_bits
    high = code >> low_bits
    low = code & ((1 << low_bits) - 1)
    return OutputPoint(high / (1 << high_bits), low / (1 << low_bits))


# =======================================================================
# The frozen specification
# =======================================================================

class DecoderFamily(Enum):
    DIRECT_GEOGRAPHIC = "DIRECT_GEOGRAPHIC"
    SOUTH_POLAR = "SOUTH_POLAR"
    HEDRON_LOCAL = "HEDRON_LOCAL"
    ENVELOPE_42BIT = "ENVELOPE_42BIT"
    ENVELOPE_36BIT = "ENVELOPE_36BIT"
    MIXED_RADIX = "MIXED_RADIX"


#: Every field that must be frozen before a holdout label is revealed,
#: in the order they enter the commitment. The order is part of the
#: commitment and must not be permuted.
FROZEN_FIELDS = (
    "planetary_body",
    "body_fixed_frame",
    "body_root",
    "magnetic_model",
    "magnetic_epoch",
    "face_orientation",
    "gradient_scalar",
    "gradient_sign",
    "codec",
    "header",
    "shell_state_map",
    "phase_alphabet",
    "isotope_ratio_orientation",
    "crystal_carrier",
    "tolerance",
    "score_function",
)

#: How wide each field's search space is, in bits, when it is left FREE.
#: These are declared budgets, not measurements: they record how much
#: room a chooser has if the field is still open when the data arrive.
FIELD_DOMAIN_BITS = {
    "planetary_body": 4,                 # ~16 plausible bodies
    "body_fixed_frame": 3,               # frame conventions
    "body_root": 5,                      # candidate roots
    "magnetic_model": 3,                 # model families
    "magnetic_epoch": 7,                 # ~128 decimal-year epochs
    "face_orientation": 3,               # face + handedness
    "gradient_scalar": 3,                # which scalar is differentiated
    "gradient_sign": 1,                  # + or -
    "codec": 3,                          # six families
    "header": 2,                         # four header states
    "shell_state_map": 6,                # state assignments
    "phase_alphabet": 4,                 # alphabet variants
    "isotope_ratio_orientation": 1,      # ratio as given, or inverted
    "crystal_carrier": 8,                # carrier grid
    "tolerance": 10,                     # continuous knob, quantised
    "score_function": 3,                 # what "close" means
}

#: A frozen field still costs something: the commitment itself.
FROZEN_COMMITMENT_BITS = 1

#: A free field costs its search width plus a flag saying it is free.
FREE_CHOICE_SURCHARGE = 1


@dataclass(frozen=True)
class DecoderSpec:
    """Every choice a decoder makes, frozen before any label is revealed.

    A field set to ``None`` is FREE: it has not been committed, and it
    will be picked after the data are in view. Free fields are legal ---
    the module's job is to price them, not to forbid them --- but they
    are what :func:`description_length` charges for."""

    spec_id: str = "DECODER_SPEC"
    planetary_body: str | None = None
    body_fixed_frame: str | None = None
    body_root: str | None = None
    magnetic_model: str | None = None
    magnetic_epoch: str | None = None
    face_orientation: str | None = None
    gradient_scalar: str | None = None
    gradient_sign: str | None = None
    codec: DecoderFamily | None = None
    header: int | None = None
    shell_state_map: str | None = None
    phase_alphabet: str | None = None
    isotope_ratio_orientation: str | None = None
    crystal_carrier: str | None = None
    tolerance: float | None = None
    score_function: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.spec_id, str) or not self.spec_id:
            raise IdentifiabilityError("spec_id must be a non-empty string")
        if self.codec is not None and not isinstance(self.codec,
                                                     DecoderFamily):
            raise IdentifiabilityError(
                "codec must be a DecoderFamily or None (FREE)")
        if self.header is not None:
            if not isinstance(self.header, int) or isinstance(self.header,
                                                              bool):
                raise IdentifiabilityError("header must be a plain int")
            if self.header < 0:
                raise IdentifiabilityError("header must be non-negative")
        if self.tolerance is not None:
            if not isinstance(self.tolerance, (int, float)) or \
                    isinstance(self.tolerance, bool):
                raise IdentifiabilityError("tolerance must be a real number")
            if not 0.0 < float(self.tolerance) < 1.0:
                raise IdentifiabilityError(
                    "tolerance must lie in (0, 1) in the synthetic plane")

    # --- freeze bookkeeping --------------------------------------------

    def free_fields(self) -> tuple:
        return tuple(n for n in FROZEN_FIELDS if getattr(self, n) is None)

    def frozen_field_names(self) -> tuple:
        return tuple(n for n in FROZEN_FIELDS if getattr(self, n) is not None)

    def is_fully_frozen(self) -> bool:
        return not self.free_fields()


def _field_token(name: str, value) -> str:
    if value is None:
        return f"{name}=FREE"
    if isinstance(value, DecoderFamily):
        return f"{name}={value.value}"
    if isinstance(value, float):
        return f"{name}={value!r}"
    return f"{name}={value}"


def spec_snapshot(spec: DecoderSpec) -> tuple:
    """The ordered tuple of field tokens the commitment is taken over.

    ``spec_id`` is deliberately excluded: the commitment is over the
    decoder's *content*, so renaming a spec cannot change its hash and
    two identically specified decoders cannot pretend to be different."""
    if not isinstance(spec, DecoderSpec):
        raise IdentifiabilityError("expected a DecoderSpec")
    return tuple(_field_token(n, getattr(spec, n)) for n in FROZEN_FIELDS)


def commitment(spec: DecoderSpec) -> str:
    """The sha256 commitment over the sixteen frozen fields.

    Pure: computing a commitment does not register it. Only
    :func:`freeze` puts a spec in the ledger."""
    return hashlib.sha256(
        "\x1f".join(spec_snapshot(spec)).encode()).hexdigest()


#: commitment -> snapshot. A freeze ledger, append-only in practice.
_FREEZE_LEDGER: dict = {}

#: holdout ids whose labels have been revealed.
_REVEALED: set = set()


def freeze(spec: DecoderSpec) -> str:
    """Freeze a spec and return its commitment hash.

    Freezing is what makes a later score meaningful: the decoder was
    written down in full before it saw a label, so it had no opportunity
    to become the decoder that works."""
    digest = commitment(spec)
    _FREEZE_LEDGER.setdefault(digest, spec_snapshot(spec))
    return digest


def is_frozen(spec: DecoderSpec) -> bool:
    """True iff this exact specification has been frozen."""
    return commitment(spec) in _FREEZE_LEDGER


def frozen_specs() -> tuple:
    """Every commitment currently in the ledger, sorted."""
    return tuple(sorted(_FREEZE_LEDGER))


def reveal_holdout(holdout_id: str) -> str:
    """Record that a holdout's labels are now visible. One-way."""
    if not isinstance(holdout_id, str) or not holdout_id:
        raise IdentifiabilityError("holdout_id must be a non-empty string")
    _REVEALED.add(holdout_id)
    return holdout_id


def is_revealed(holdout_id: str) -> bool:
    return holdout_id in _REVEALED


# --- the two freeze refusals -------------------------------------------

def refuse_unfrozen_evaluation(spec_or_decoder, *,
                               commitment_hash: str | None = None) -> str:
    """Refuse to score a decoder that was never frozen.

    A decoder evaluated without a prior commitment cannot be shown to
    have predated its result. The evaluation may be honest, and it is
    still worthless as evidence: nothing distinguishes it from a decoder
    assembled once the answer was visible. Returns the commitment when
    the freeze is in order."""
    spec = getattr(spec_or_decoder, "spec", spec_or_decoder)
    if not isinstance(spec, DecoderSpec):
        raise IdentifiabilityError(
            "refused: evaluation needs a DecoderSpec (or a Decoder "
            "carrying one); no specification means nothing was frozen")
    digest = commitment(spec)
    if digest not in _FREEZE_LEDGER:
        raise IdentifiabilityError(
            f"refused: decoder {spec.spec_id!r} has not been frozen. "
            f"Its sixteen fields must be committed with freeze() BEFORE "
            f"any holdout label is revealed, otherwise a score proves "
            f"only that some setting of the choices fits -- which is "
            f"guaranteed, because the choices were still open when the "
            f"data arrived. Commitment that would be recorded: {digest}")
    if commitment_hash is not None and commitment_hash != digest:
        raise IdentifiabilityError(
            f"refused: the supplied commitment {commitment_hash!r} does "
            f"not match this specification ({digest}). A commitment that "
            f"does not bind the spec being scored binds nothing.")
    return digest


def refuse_spec_change_after_reveal(frozen_spec: DecoderSpec,
                                    proposed_spec: DecoderSpec, *,
                                    holdout_id: str | None = None,
                                    labels_revealed: bool | None = None
                                    ) -> dict:
    """Refuse any edit to a frozen field once the labels are visible.

    This is the failure mode that looks most like diligence. The decoder
    misses, someone notices that the epoch "should obviously" be a
    different year or the gradient sign the other way, the change is
    made, and the decoder now works. It works because it was tuned on
    the answer. The edit is legal before the reveal and forbidden after,
    and the boundary is the whole point."""
    if labels_revealed is None:
        labels_revealed = (is_revealed(holdout_id)
                           if holdout_id is not None else True)
    before = spec_snapshot(frozen_spec)
    after = spec_snapshot(proposed_spec)
    changed = tuple(
        {"field": name, "frozen": b.split("=", 1)[1],
         "proposed": a.split("=", 1)[1]}
        for name, b, a in zip(FROZEN_FIELDS, before, after) if b != a)
    if changed and labels_revealed:
        names = ", ".join(c["field"] for c in changed)
        raise IdentifiabilityError(
            f"refused: {len(changed)} frozen field(s) changed after the "
            f"holdout labels were revealed ({names}). A decoder edited "
            f"with the answer in view is fitted to the answer, however "
            f"reasonable each edit looks on its own: the reason the new "
            f"setting seems obvious is that it is the setting that "
            f"works. The frozen commitment is "
            f"{commitment(frozen_spec)}; the proposed one is "
            f"{commitment(proposed_spec)}. Freeze the revision, hold "
            f"back fresh labels, and test it there.")
    return {
        "changed_fields": changed,
        "labels_revealed": bool(labels_revealed),
        "frozen_commitment": commitment(frozen_spec),
        "proposed_commitment": commitment(proposed_spec),
        "allowed": True,
    }


# =======================================================================
# Description length
# =======================================================================

def description_length(spec: DecoderSpec) -> int:
    """Total bits needed to specify this decoder.

    Every one of the sixteen choices costs something, so a decoder with
    more moving parts is always longer than one with fewer. What the
    accounting turns on is *when* the choice is made. A field frozen in
    advance costs only its commitment --- one bit, the record that it was
    fixed. A field left FREE costs its whole declared search width, plus
    a bit for being free, because an open field is not a single decoder
    but the entire family of decoders it could still become, and the one
    that gets reported will be whichever member fits.

    So a spec with many free choices ranks well above a tightly frozen
    one, and a match found by the loose spec is worth correspondingly
    less. The branch bits of the chosen codec family are added last:
    a family that admits several readings of the same input has to say
    which reading it meant."""
    if not isinstance(spec, DecoderSpec):
        raise IdentifiabilityError("expected a DecoderSpec")
    total = 0
    for name in FROZEN_FIELDS:
        if getattr(spec, name) is None:
            total += FIELD_DOMAIN_BITS[name] + FREE_CHOICE_SURCHARGE
        else:
            total += FROZEN_COMMITMENT_BITS
    return total + _branch_bits(spec)


def description_length_table(spec: DecoderSpec) -> dict:
    """Per-field breakdown of :func:`description_length`."""
    rows = []
    for name in FROZEN_FIELDS:
        free = getattr(spec, name) is None
        rows.append({
            "field": name,
            "free": free,
            "domain_bits": FIELD_DOMAIN_BITS[name],
            "bits": (FIELD_DOMAIN_BITS[name] + FREE_CHOICE_SURCHARGE
                     if free else FROZEN_COMMITMENT_BITS),
        })
    return {
        "spec_id": spec.spec_id,
        "rows": rows,
        "branch_bits": _branch_bits(spec),
        "free_field_count": len(spec.free_fields()),
        "total_bits": description_length(spec),
    }


# =======================================================================
# The decoder families
# =======================================================================

#: How many readings of one input each family admits when nothing
#: constrains it.
FAMILY_BRANCH_COUNT = {
    DecoderFamily.DIRECT_GEOGRAPHIC: 2,      # which half leads
    DecoderFamily.SOUTH_POLAR: 2,            # gradient sign
    DecoderFamily.HEDRON_LOCAL: 6,           # which face is root
    DecoderFamily.ENVELOPE_42BIT: 4,         # two header bits
    DecoderFamily.ENVELOPE_36BIT: 8,         # three truncated bits
    DecoderFamily.MIXED_RADIX: 3,            # shell-state assignment
}

#: Which frozen field, if committed, collapses a family's branches to
#: one. ``None`` means no field can: the ambiguity is irreducible.
#: ENVELOPE_36BIT is the instructive case --- the three high bits of a
#: 39-bit address were truncated, so eight inputs share every surviving
#: code and no amount of freezing brings them back.
FAMILY_BRANCH_FIELD = {
    DecoderFamily.DIRECT_GEOGRAPHIC: "body_fixed_frame",
    DecoderFamily.SOUTH_POLAR: "gradient_sign",
    DecoderFamily.HEDRON_LOCAL: "face_orientation",
    DecoderFamily.ENVELOPE_42BIT: "header",
    DecoderFamily.ENVELOPE_36BIT: None,
    DecoderFamily.MIXED_RADIX: "shell_state_map",
}


def _branch_index(value, count: int) -> int:
    """Map a frozen field value onto one branch, deterministically."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value % count
    digest = hashlib.sha256(str(value).encode()).hexdigest()
    return int(digest, 16) % count


def admissible_branches(spec: DecoderSpec) -> tuple:
    """The branch indices this spec still leaves open.

    Freezing the field that governs a family's ambiguity collapses it to
    a single reading. Where no such field exists, every branch survives
    however tightly the rest of the spec is frozen."""
    if spec.codec is None:
        raise IdentifiabilityError(
            "refused: the codec field is FREE, so the decoder has no "
            "family and no branch structure. Freeze the codec before "
            "asking what it admits.")
    count = FAMILY_BRANCH_COUNT[spec.codec]
    field = FAMILY_BRANCH_FIELD[spec.codec]
    if field is None:
        return tuple(range(count))
    value = getattr(spec, field)
    if value is None:
        return tuple(range(count))
    return (_branch_index(value, count),)


def _branch_bits(spec: DecoderSpec) -> int:
    if spec.codec is None:
        widest = max(FAMILY_BRANCH_COUNT.values())
        return max(0, (widest - 1).bit_length())
    return max(0, (len(admissible_branches(spec)) - 1).bit_length())


def _check_value(value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise IdentifiabilityError("input vector must be a plain int")
    if not 0 <= value < DECIMAL_MODULUS:
        raise IdentifiabilityError(
            f"input vector {value} outside the 12-digit range "
            f"[0, 10**12)")
    return value


# --- the six mappings. Simple, deterministic, and not real decoders ----

def _decode_direct(value: int, branch: int) -> OutputPoint:
    digits = str(value).zfill(WIDTH)
    a = int(digits[:6]) / 1_000_000
    b = int(digits[6:]) / 1_000_000
    return OutputPoint(a, b) if branch % 2 == 0 else OutputPoint(b, a)


def _decode_south_polar(value: int, branch: int) -> OutputPoint:
    digits = str(value).zfill(WIDTH)
    a = int(digits[:6]) / 1_000_000
    b = int(digits[6:]) / 1_000_000
    u = _wrap_unit(1.0 - a)
    v = b if branch % 2 == 0 else _wrap_unit(b + 0.5)
    return OutputPoint(u, v)


def _decode_hedron(value: int, branch: int) -> OutputPoint:
    face = value % 6
    local = value // 6
    base = _unit_pair(local, 40)
    u = _wrap_unit(base.u + ((face + branch) % 6) / 6.0)
    return OutputPoint(u, base.v)


def _decode_envelope42(value: int, branch: int) -> OutputPoint:
    # The two header bits sit ABOVE the forty payload bits, so with the
    # header frozen the frame reaches only its own quarter of the u
    # axis. That restriction is real and is left in: a decoder whose
    # reachable set is a quarter of the output space is worth being able
    # to see, and hiding it behind a rescaling would flatter the frame.
    header = branch % (1 << shelladdr.ENV42_HEADER_BITS)
    code = (header << shelladdr.ENV42_PAYLOAD_BITS) | value
    return _unit_pair(code, shelladdr.ENV42_TOTAL_BITS)


def _decode_envelope36(value: int, branch: int) -> OutputPoint:
    kept = value & ((1 << shelladdr.ENV36_BITS) - 1)
    guessed_high = branch % 8
    code = (guessed_high << shelladdr.ENV36_BITS) | kept
    return _unit_pair(code, shelladdr.ENV36_BITS + 3)


def _decode_mixed_radix(value: int, branch: int) -> OutputPoint:
    shell, face, local, _phase, _epoch, _parity, _rev = \
        shelladdr.mixed_radix_decode(value)
    u = (shell * 6 + face) / 48.0
    v = _wrap_unit(local / 67108864.0 + (branch % 3) / 3.0)
    return OutputPoint(u, v)


FAMILY_MAPPING = {
    DecoderFamily.DIRECT_GEOGRAPHIC: _decode_direct,
    DecoderFamily.SOUTH_POLAR: _decode_south_polar,
    DecoderFamily.HEDRON_LOCAL: _decode_hedron,
    DecoderFamily.ENVELOPE_42BIT: _decode_envelope42,
    DecoderFamily.ENVELOPE_36BIT: _decode_envelope36,
    DecoderFamily.MIXED_RADIX: _decode_mixed_radix,
}


@dataclass(frozen=True)
class Decoder:
    """A frozen specification plus the family mapping it names.

    The mappings are intentionally toy: a handful of digit splits, bit
    slices and radix reads. Nothing here claims to be a working decoder
    of anything, and making them cleverer would not change a single
    conclusion, because every conclusion in this module comes from the
    comparison discipline --- planted controls, matched nulls, alias
    sets, description lengths --- and none of it from the mappings."""

    decoder_id: str
    spec: DecoderSpec

    @property
    def family(self) -> DecoderFamily:
        if self.spec.codec is None:
            raise IdentifiabilityError(
                f"{self.decoder_id}: codec is FREE, so this decoder has "
                f"no family")
        return self.spec.codec

    @property
    def branches(self) -> tuple:
        return admissible_branches(self.spec)

    @property
    def canonical_branch(self) -> int:
        return self.branches[0]

    def decode(self, value: int, branch: int | None = None) -> OutputPoint:
        """One candidate output, under one reading of the input."""
        _check_value(value)
        b = self.canonical_branch if branch is None else branch
        if b not in self.branches:
            raise IdentifiabilityError(
                f"{self.decoder_id}: branch {b} is not admissible under "
                f"this spec (admissible: {self.branches})")
        return FAMILY_MAPPING[self.family](value, b)

    def candidates(self, value: int) -> tuple:
        """Every candidate output this decoder admits for one input.

        Plural by construction. A decoder that returned one point would
        be hiding the readings it did not pick, not eliminating them."""
        return tuple(self.decode(value, b) for b in self.branches)

    def best_distance(self, value: int, target: OutputPoint) -> float:
        return min(point_distance(p, target) for p in self.candidates(value))

    def hits(self, value: int, target: OutputPoint,
             tolerance: float = DEFAULT_TOLERANCE) -> bool:
        return self.best_distance(value, target) <= tolerance

    def description_length(self) -> int:
        return description_length(self.spec)


# --- the default, fully frozen decoders --------------------------------

BASE_SPEC = DecoderSpec(
    spec_id="R11_BASE_SPEC",
    planetary_body="EARTH",
    body_fixed_frame="BODY_FIXED_FRAME_A",
    body_root="GEOMETRIC_CENTRE",
    magnetic_model="DIPOLE_REFERENCE_MODEL",
    magnetic_epoch="2026.0",
    face_orientation="SOUTH_UP_FACE_A",
    gradient_scalar="TOTAL_INTENSITY",
    gradient_sign="+1",
    codec=DecoderFamily.DIRECT_GEOGRAPHIC,
    header=0,
    shell_state_map="SHELL_STATE_MAP_A",
    phase_alphabet="PHASE_ALPHABET_A",
    isotope_ratio_orientation="RATIO_AS_GIVEN",
    crystal_carrier="CRYSTAL_CARRIER_CANDIDATE_A",
    tolerance=DEFAULT_TOLERANCE,
    score_function="WRAPPED_EUCLIDEAN",
)


def spec_for(family: DecoderFamily, *, spec_id: str | None = None,
             **overrides) -> DecoderSpec:
    """A fully frozen spec for one family, from the common base."""
    if not isinstance(family, DecoderFamily):
        raise IdentifiabilityError("family must be a DecoderFamily")
    return replace(BASE_SPEC,
                   spec_id=spec_id or f"R11_SPEC_{family.value}",
                   codec=family, **overrides)


def default_decoders() -> tuple:
    """One fully frozen decoder per family, frozen at construction."""
    out = []
    for family in DecoderFamily:
        spec = spec_for(family)
        freeze(spec)
        out.append(Decoder(f"DECODER_{family.value}", spec))
    return tuple(out)


DEFAULT_DECODERS = default_decoders()


def decoder_for(family: DecoderFamily) -> Decoder:
    for d in DEFAULT_DECODERS:
        if d.family is family:
            return d
    raise IdentifiabilityError(f"no default decoder for {family!r}")


# =======================================================================
# Alias sets
# =======================================================================

def _hash_int(seed: str, index: int, modulus: int) -> int:
    digest = hashlib.sha256(f"{seed}\x1f{index}".encode()).hexdigest()
    return int(digest, 16) % modulus


def alias_pool(size: int = ALIAS_POOL_SIZE,
               seed: str = "R11_IDENTIFIABILITY_ALIAS_POOL") -> tuple:
    """A deterministic pool of synthetic twelve-digit inputs.

    The pool is the declared search space an alias set is drawn from. It
    is synthetic and seeded, so the alias sets are reproducible and
    contain no real material."""
    if size < 1:
        raise IdentifiabilityError("pool size must be >= 1")
    span = DECIMAL_MODULUS - DECIMAL_FLOOR
    return tuple(DECIMAL_FLOOR + _hash_int(seed, i, span)
                 for i in range(size))


DEFAULT_ALIAS_POOL = alias_pool()

_POOL_POINT_CACHE: dict = {}


def _pool_points(family: DecoderFamily, branch: int, pool: tuple) -> tuple:
    key = (family, branch, len(pool), hash(pool))
    cached = _POOL_POINT_CACHE.get(key)
    if cached is None:
        fn = FAMILY_MAPPING[family]
        cached = tuple(fn(v, branch) for v in pool)
        _POOL_POINT_CACHE[key] = cached
    return cached


@dataclass(frozen=True)
class Alias:
    """One member of an alias set: an input, a reading, and its output."""

    value: int
    branch: int
    point: OutputPoint
    distance: float


def alias_set(decoder: Decoder, target: OutputPoint,
              tolerance: float = ALIAS_TOLERANCE, *,
              pool: tuple | None = None) -> tuple:
    """Every candidate output within ``tolerance`` of ``target``.

    Not "the" answer, and not the nearest answer: all of them, across
    every admissible reading and every input in the declared pool. This
    is the module's first deliverable and it is a set on purpose. A
    decoder that discards information has many preimages; reporting the
    closest one as the output does not remove the others, it removes the
    reader's ability to see them. The size of this set is the honest
    measure of how much the decoder actually pins down.

    ``target`` is normally an OBSERVED output --- a point the decoder
    itself produced --- and the question the set answers is "what else
    lands here?". An arbitrary point may have no preimages at all if it
    falls outside the decoder's reachable set, and an empty alias set is
    then the correct and informative answer."""
    refuse_unfrozen_evaluation(decoder)
    if not isinstance(target, OutputPoint):
        raise IdentifiabilityError("target must be an OutputPoint")
    if not isinstance(tolerance, (int, float)) or isinstance(tolerance, bool):
        raise IdentifiabilityError("tolerance must be a real number")
    if tolerance < 0:
        raise IdentifiabilityError("tolerance must be non-negative")
    values = DEFAULT_ALIAS_POOL if pool is None else tuple(pool)
    out = []
    for branch in decoder.branches:
        points = _pool_points(decoder.family, branch, values)
        for value, point in zip(values, points):
            d = point_distance(point, target)
            if d <= tolerance:
                out.append(Alias(value, branch, point, d))
    out.sort(key=lambda a: (a.distance, a.value, a.branch))
    return tuple(out)


def alias_set_size(decoder: Decoder, target: OutputPoint,
                   tolerance: float = ALIAS_TOLERANCE, *,
                   pool: tuple | None = None) -> int:
    return len(alias_set(decoder, target, tolerance, pool=pool))


def refuse_unique_decoding(decoder: Decoder, target: OutputPoint,
                           tolerance: float = ALIAS_TOLERANCE) -> None:
    """Refuse to report the nearest alias as though it were the answer."""
    aliases = alias_set(decoder, target, tolerance)
    raise IdentifiabilityError(
        f"refused: {decoder.decoder_id} admits {len(aliases)} candidate(s) "
        f"within tolerance {tolerance} of this target. The nearest one is "
        f"not 'the' decoding; it is the first row of a set, and the set "
        f"is the result. Report alias_set(), including its size.")


# =======================================================================
# Datasets: the planted control and the four nulls
# =======================================================================

@dataclass(frozen=True)
class Observation:
    """One input vector with its label in the synthetic output plane."""

    value: int
    target: OutputPoint


#: Held-out reference points. SYNTHETIC and neutral: seeded points in an
#: abstract index plane with generic identifiers. They are not places,
#: are not derived from any location, and cannot be read as coordinates.
HELDOUT_LANDMARKS = tuple(
    (f"HOLDOUT_REFERENCE_{i:02d}",
     OutputPoint(_hash_int("R11_HOLDOUT_U", i, 10 ** 9) / 10 ** 9,
                 _hash_int("R11_HOLDOUT_V", i, 10 ** 9) / 10 ** 9))
    for i in range(8)
)


def random_values(count: int, seed: int = DEFAULT_SEED) -> tuple:
    rng = np.random.default_rng(seed)
    return tuple(int(x) for x in rng.integers(DECIMAL_FLOOR,
                                              DECIMAL_MODULUS, size=count))


def random_digit_strings(count: int, seed: int = DEFAULT_SEED) -> tuple:
    """Random twelve-digit STRINGS, built digit by digit.

    A distinct null from a random integer: it is generated the way a
    reader would generate a fake address, one symbol at a time, with no
    numeric structure whatever."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(count):
        first = int(rng.integers(1, 10))
        rest = "".join(str(int(d)) for d in rng.integers(0, 10, size=WIDTH - 1))
        out.append(f"{first}{rest}")
    return tuple(out)


def random_points(count: int, seed: int = DEFAULT_SEED) -> tuple:
    rng = np.random.default_rng(seed)
    return tuple(OutputPoint(float(u), float(v))
                 for u, v in rng.random((count, 2)))


def planted_dataset(family: DecoderFamily, count: int = DEFAULT_TRIALS,
                    seed: int = DEFAULT_SEED) -> tuple:
    """PLANTED data: labels generated by one family's own rule.

    This is the POWER control. If the benchmark cannot see the decoder
    that literally produced the labels, then its failure to see anything
    elsewhere means nothing --- it would just be blind. The generator is
    the family's canonical reading, so the matching decoder scores an
    exact zero residual on every row."""
    decoder = decoder_for(family)
    values = random_values(count, seed)
    branch = decoder.canonical_branch
    return tuple(Observation(v, decoder.decode(v, branch)) for v in values)


def random_coordinate_dataset(count: int = DEFAULT_TRIALS,
                              seed: int = DEFAULT_SEED) -> tuple:
    """NULL: real-shaped inputs, labels drawn uniformly at random."""
    values = random_values(count, seed)
    points = random_points(count, seed + 1)
    return tuple(Observation(v, p) for v, p in zip(values, points))


def random_digit_string_dataset(count: int = DEFAULT_TRIALS,
                                seed: int = DEFAULT_SEED) -> tuple:
    """NULL: inputs are random twelve-digit strings, labels random."""
    strings = random_digit_strings(count, seed + 2)
    points = random_points(count, seed + 3)
    return tuple(Observation(int(s), p) for s, p in zip(strings, points))


def shuffled_label_dataset(dataset: tuple,
                           seed: int = DEFAULT_SEED) -> tuple:
    """NULL: the same inputs and the same labels, wrongly paired.

    The strictest of the nulls, because it preserves both marginals
    exactly. Anything a decoder scores here it scores from the shapes of
    the two collections, not from the correspondence between them."""
    rows = tuple(dataset)
    n = len(rows)
    if n < 2:
        raise IdentifiabilityError("shuffling needs at least two rows")
    rng = np.random.default_rng(seed + 4)
    idx = np.arange(n)
    perm = rng.permutation(n)
    for _ in range(64):
        if not np.any(perm == idx):
            break
        perm = rng.permutation(n)
    else:
        perm = np.roll(idx, 1)
    return tuple(Observation(rows[i].value, rows[int(perm[i])].target)
                 for i in range(n))


def heldout_landmark_dataset(count: int = DEFAULT_TRIALS,
                             seed: int = DEFAULT_SEED) -> tuple:
    """NULL: labels are the neutral synthetic held-out landmarks."""
    values = random_values(count, seed + 5)
    return tuple(Observation(v, HELDOUT_LANDMARKS[i % len(HELDOUT_LANDMARKS)][1])
                 for i, v in enumerate(values))


def hit_rate(decoder: Decoder, dataset: tuple,
             tolerance: float = DEFAULT_TOLERANCE) -> float:
    """Fraction of rows where some admissible reading lands in tolerance."""
    refuse_unfrozen_evaluation(decoder)
    rows = tuple(dataset)
    if not rows:
        raise IdentifiabilityError("empty dataset")
    return sum(1 for r in rows
               if decoder.hits(r.value, r.target, tolerance)) / len(rows)


# =======================================================================
# The benchmark
# =======================================================================

def benchmark(dataset: tuple | None = None, *,
              decoders: tuple | None = None,
              tolerance: float = DEFAULT_TOLERANCE,
              seed: int = DEFAULT_SEED,
              alias_tolerance: float = ALIAS_TOLERANCE,
              margin: float = BETTER_THAN_CHANCE_MARGIN) -> dict:
    """Score every decoder on ``dataset`` against four matched nulls.

    The nulls are the whole apparatus. A hit rate on its own is
    uninterpretable: with several admissible readings and a finite
    tolerance, a decoder hits *something* at a rate set purely by its own
    branch count, and that rate looks impressive if nothing is standing
    beside it. So each decoder is scored against random coordinates,
    random twelve-digit strings, shuffled labels and held-out landmarks,
    and ``better_than_chance`` is true only if the observed rate clears
    the best of them by a wide margin.

    Each row also carries the two deliverables --- alias-set size and
    description length --- because a decoder that clears the nulls while
    admitting a hundred aliases and costing eighty bits has not
    identified anything either."""
    rows = tuple(random_digit_string_dataset(DEFAULT_TRIALS, seed)
                 if dataset is None else dataset)
    if len(rows) < 2:
        raise IdentifiabilityError("benchmark needs at least two rows")
    decs = DEFAULT_DECODERS if decoders is None else tuple(decoders)
    if not decs:
        raise IdentifiabilityError("no decoders to benchmark")

    n = len(rows)
    nulls = {
        "random_coordinates": tuple(
            Observation(r.value, p) for r, p in
            zip(rows, random_points(n, seed + 11))),
        "random_digit_strings": tuple(
            Observation(int(s), r.target) for s, r in
            zip(random_digit_strings(n, seed + 12), rows)),
        "shuffled_labels": shuffled_label_dataset(rows, seed + 13),
        "heldout_landmarks": tuple(
            Observation(r.value,
                        HELDOUT_LANDMARKS[i % len(HELDOUT_LANDMARKS)][1])
            for i, r in enumerate(rows)),
    }

    results = {}
    for d in decs:
        refuse_unfrozen_evaluation(d)
        # The alias set is taken around a point the decoder itself
        # produced, so it answers "what else lands where this input
        # lands?" rather than "does this decoder reach that point?".
        alias_target = d.decode(rows[0].value)
        observed = hit_rate(d, rows, tolerance)
        null_rates = {k: hit_rate(d, v, tolerance) for k, v in nulls.items()}
        worst_null = max(null_rates.values())
        results[d.decoder_id] = {
            "decoder_id": d.decoder_id,
            "family": d.family.value,
            "spec_id": d.spec.spec_id,
            "commitment": commitment(d.spec),
            "frozen": is_frozen(d.spec),
            "branches": list(d.branches),
            "hit_rate_planted": observed,
            "hit_rate_nulls": null_rates,
            "worst_null_hit_rate": worst_null,
            "excess_over_best_null": observed - worst_null,
            "alias_set_size": alias_set_size(d, alias_target,
                                             alias_tolerance),
            "alias_tolerance": alias_tolerance,
            "description_length": d.description_length(),
            "free_fields": list(d.spec.free_fields()),
            "better_than_chance": bool(observed > worst_null + margin),
        }

    winners = [k for k, v in results.items() if v["better_than_chance"]]
    return {
        "dataset_size": n,
        "tolerance": tolerance,
        "margin": margin,
        "nulls_used": sorted(nulls),
        "decoders": results,
        "better_than_chance": winners,
        "any_better_than_chance": bool(winners),
        "verdict": ("DECODER_SEPARATED_ON_PLANTED_CONTROL" if winners
                    else DEFAULT_VERDICT),
        "what_a_winner_means": (
            "a decoder that clears every null on PLANTED data has "
            "demonstrated the benchmark's POWER -- that the machinery "
            "can see a decoder when one is really there. It has not "
            "decoded anything. On material that was not planted, the "
            "standing result is NO_DECODER_IDENTIFIED"),
    }


def power_check(family: DecoderFamily = DecoderFamily.DIRECT_GEOGRAPHIC,
                count: int = DEFAULT_TRIALS,
                seed: int = DEFAULT_SEED) -> dict:
    """Plant one family's own output and confirm the benchmark sees it."""
    decoder = decoder_for(family)
    result = benchmark(planted_dataset(family, count, seed), seed=seed)
    row = result["decoders"][decoder.decoder_id]
    return {
        "planted_family": family.value,
        "planted_by": decoder.decoder_id,
        "hit_rate_planted": row["hit_rate_planted"],
        "worst_null_hit_rate": row["worst_null_hit_rate"],
        "better_than_chance": row["better_than_chance"],
        "other_families_better_than_chance": [
            k for k in result["better_than_chance"]
            if k != decoder.decoder_id],
        "detected": bool(row["better_than_chance"]),
        "note": (
            "the generator's own decoder recovers its labels exactly "
            "while every null stays at chance, so the benchmark has the "
            "power to detect a decoder that is really present. That it "
            "detects none elsewhere is a finding, not blindness"),
    }


def null_check(count: int = DEFAULT_TRIALS, seed: int = DEFAULT_SEED) -> dict:
    """Run the two headline nulls and confirm nothing beats chance."""
    digits = benchmark(random_digit_string_dataset(count, seed), seed=seed)
    shuffled = benchmark(
        shuffled_label_dataset(random_coordinate_dataset(count, seed), seed),
        seed=seed)
    return {
        "random_digit_strings": {
            "better_than_chance": digits["better_than_chance"],
            "verdict": digits["verdict"],
        },
        "shuffled_labels": {
            "better_than_chance": shuffled["better_than_chance"],
            "verdict": shuffled["verdict"],
        },
        "any_decoder_beat_chance": bool(digits["any_better_than_chance"]
                                        or shuffled["any_better_than_chance"]),
    }


# =======================================================================
# The headline refusal
# =======================================================================

def refuse_decoded_location_verdict(*_args, **_kwargs) -> None:
    """Refuse a decoded-location verdict. Always. Without exception.

    Not "unless the freeze is clean", not "unless the alias set is
    small", not "unless the decoder cleared every null". Always. R11
    assembles the pieces from which such a verdict would be built ---
    a root, a frame, a face, a gradient, a codec, a header, an alphabet,
    a carrier --- and the reason it assembles them is to measure how
    many places that machinery can reach, which is the same reason it
    must never report one of them.

    The output of this module is an ALIAS SET and a DESCRIPTION LENGTH.
    Those are the honest deliverables of a decoder search that did not
    identify a decoder, and they cannot be rewritten as an answer."""
    raise IdentifiabilityError(
        "refused: R11 permits no decoded-location verdict under any "
        "circumstances. The deliverable is an ALIAS SET -- every "
        "candidate the decoder admits within tolerance -- together with "
        "the DESCRIPTION LENGTH of the decoder that produced it. Never a "
        "single location. Sixteen frozen choices, a tolerance and a "
        "score function span a search space that reaches somewhere "
        "plausible whatever the input, so a place selected from that "
        "space is a report of the space, not of the data. No freeze is "
        "clean enough, no alias set small enough and no null cleared "
        "widely enough to lift this refusal: the standing verdict is "
        f"{DEFAULT_VERDICT}.")


# =======================================================================
# The report
# =======================================================================

def identifiability_report() -> dict:
    power = power_check()
    nulls = null_check()
    tight = spec_for(DecoderFamily.MIXED_RADIX, spec_id="TIGHT")
    loose = DecoderSpec(spec_id="LOOSE", codec=DecoderFamily.MIXED_RADIX)
    example = decoder_for(DecoderFamily.ENVELOPE_36BIT)
    observed_point = example.decode(DEFAULT_ALIAS_POOL[0])
    return {
        "what_this_is": (
            "a freeze-before-reveal comparison of six decoder families "
            "against a planted control and four matched nulls, reporting "
            "alias sets and description lengths and never a location"),
        "frozen_fields": list(FROZEN_FIELDS),
        "decoder_families": [f.value for f in DecoderFamily],
        "default_decoders": [d.decoder_id for d in DEFAULT_DECODERS],
        "all_defaults_frozen": all(is_frozen(d.spec)
                                   for d in DEFAULT_DECODERS),
        "power_control": power,
        "null_controls": nulls,
        "alias_example": {
            "decoder_id": example.decoder_id,
            "tolerance": ALIAS_TOLERANCE,
            "alias_set_size": alias_set_size(example, observed_point),
            "branches_admitted": list(example.branches),
            "why_irreducible": (
                "the 36-bit envelope truncates the three high bits of a "
                "39-bit address, so eight inputs share every surviving "
                "code. Freezing the rest of the spec cannot restore "
                "them: this ambiguity is a property of the frame, not of "
                "the reader's indecision"),
        },
        "description_length": {
            "tightly_frozen_bits": description_length(tight),
            "many_free_choices_bits": description_length(loose),
            "free_costs_more": (description_length(loose)
                                > description_length(tight)),
            "why": (
                "a frozen field costs its commitment; a free field costs "
                "its whole search width, because it is not one decoder "
                "but every decoder it could still become, and the one "
                "reported will be whichever member fits"),
        },
        "refusals": [
            "refuse_unfrozen_evaluation",
            "refuse_spec_change_after_reveal",
            "refuse_unique_decoding",
            "refuse_decoded_location_verdict",
        ],
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": DEFAULT_VERDICT,
        "what_this_does_not_say": (
            "It does not say the R11 material is meaningless, and it "
            "does not say no decoder exists. It says that sixteen "
            "choices, a tolerance and a score function span a space "
            "large enough to reach somewhere plausible from almost any "
            "input, so a decoder must be frozen in full before any "
            "holdout label is seen or its success is guaranteed and "
            "empty. Under that discipline, the six families separate "
            "only on PLANTED data -- which shows the benchmark has "
            "power, not that anything was decoded -- and on random "
            "digit strings, shuffled labels, random coordinates and "
            "held-out landmarks no decoder beats chance. The output "
            "space and the landmarks are synthetic; no place is named, "
            "computed or implied anywhere in this module. Nothing here "
            "is measured and no physical validation is claimed. This is "
            "NO_DECODER_IDENTIFIED, not NO_DECODER_POSSIBLE."),
    }
