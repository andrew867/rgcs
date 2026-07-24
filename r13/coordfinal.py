"""P37 — the finalized icosahedral-packet coordinate codec: a bijection at
the SYMBOL level, and a one-to-many ALIAS SET at the coordinate level.

This module finalizes the R12 icosahedral packet grammar (imported from
:mod:`r12.icosapacket`) into a coordinate codec, and it draws the one
line that the whole R13 pack turns on: **a coordinate alias is not a
decoded destination.** The codec produces, for any packet, a *set* of
candidate coordinates -- never a single decoded location.

The codec has two levels and they behave completely differently.

**The symbol level is a bijection, and that is real POWER.** A
thirty-bit word packs, without remainder, into a face, an eleven-level
quaternary refinement path and a shell, and unpacks back to exactly the
same word. :class:`PacketGrammar` finalizes that round trip:
``decode(encode(value)) == value`` for every value in range. Nothing is
lost, nothing is guessed, and the frame is provably faithful. This is the
one thing the codec establishes cleanly, and it is a statement about the
*bit layout*, not about any place.

**The coordinate level is one-to-many, and that is the finding.** The
same packet is consistent with many frames at once: face numbering, body
orientation, magnetic root, handedness and shell projection are each an
independent convention with several defensible settings, and none of them
is fixed by anything inside the packet. Their product is a set of
thirty-two frames, so :func:`PacketGrammar.decode_to_alias_set` returns
thirty-two candidate coordinates for one packet, and no field of the
packet distinguishes the nominal candidate from the other thirty-one.
The alias set *is* the output. Its size is the honest measure of how
little a packet pins down.

**Two load-bearing refusals.**

* :func:`refuse_alias_as_destination` raises whenever code tries to
  collapse the alias set to a single decoded destination. Reporting the
  nominal candidate -- or the nearest, or the "obvious" one -- as *the*
  location hides the other members rather than eliminating them, and the
  members were never eliminated: no evidence anywhere selects among them.

* :func:`refuse_numeric_match_as_authentication` raises when a decoded
  number happens to match some known coordinate. A retrospective numeric
  match is a ``RETROSPECTIVE_NUMERIC_MATCH`` and nothing more; it does
  not authenticate a source, a destination or an origin. The match was
  found *after* the number was in view, from a space large enough to hit
  something, so it is a property of the search, not of the packet.

The codec is deterministic -- the same input yields the same packet
always -- and it is versioned by a SHA-256 over its grammar parameters,
so a later change to the field widths or the frame set produces a
different :attr:`PacketGrammar.version_hash` and cannot be passed off as
the same codec.

Nothing here is measured, and no coordinate here is a geography: the
alias coordinates live in a synthetic index space with no datum, no north
and no units. The standing verdict is
**COORDINATE_CODEC_FINALIZED_ALIAS_SET_ONLY**.
"""

from __future__ import annotations

import hashlib
import itertools
from dataclasses import dataclass

import numpy as np

from r12 import icosapacket as ip

# =======================================================================
# Claim classes and the standing verdict
# =======================================================================

#: The claim classes this module is allowed to emit, verbatim.
CLAIM_EXACT_IDENTITY = "EXACT_IDENTITY"
CLAIM_ANALYTIC_MODEL = "ANALYTIC_MODEL"
CLAIM_REPOSITORY_COMPUTATIONAL_RESULT = "REPOSITORY_COMPUTATIONAL_RESULT"
CLAIM_RETROSPECTIVE_NUMERIC_MATCH = "RETROSPECTIVE_NUMERIC_MATCH"
CLAIM_UNSUPPORTED = "UNSUPPORTED"

VERDICT = "COORDINATE_CODEC_FINALIZED_ALIAS_SET_ONLY"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: The synthetic coordinate space. An abstract index range with no datum,
#: no north and no units, so nothing it produces can be read as a place.
COORD_MODULUS = 1 << 40


class CoordFinalError(ValueError):
    """Raised on an out-of-range coordinate, an attempt to collapse an
    alias set to a single decoded destination, or an attempt to read a
    retrospective numeric match as authentication of a source or a
    destination."""


# =======================================================================
# The frames: five conventions, none fixed by the packet
# =======================================================================

#: The five conventions a coordinate reading of a packet would need, each
#: with the settings it could defensibly take. The packet fixes none of
#: them, so every combination is admissible and the product is the alias
#: set. These are exactly the five prerequisites R12 named unfrozen; here
#: they are enumerated rather than left open, which is what turns the
#: freedom into a countable set of candidates.
FRAME_AXES = (
    ("face_numbering", ("FACE_NUMBERING_A", "FACE_NUMBERING_B")),
    ("body_orientation", ("ORIENTATION_A", "ORIENTATION_B")),
    ("magnetic_root", ("ROOT_A", "ROOT_B")),
    ("handedness", ("RIGHT_HANDED", "LEFT_HANDED")),
    ("shell_projection", ("PROJECTION_A", "PROJECTION_B")),
)

#: The number of admissible frames: the product of the axis cardinalities.
FRAME_COUNT = int(np.prod([len(opts) for _n, opts in FRAME_AXES]))


@dataclass(frozen=True)
class Frame:
    """One admissible reading of a packet as a coordinate.

    A frame is a full setting of the five conventions. It is a *choice*,
    not a fact about the packet: the packet is equally consistent with
    this frame and with every other, so a frame's coordinate is one
    candidate among many and never 'the' answer."""

    face_numbering: str
    body_orientation: str
    magnetic_root: str
    handedness: str
    shell_projection: str

    @property
    def frame_id(self) -> str:
        return "|".join((
            self.face_numbering, self.body_orientation, self.magnetic_root,
            self.handedness, self.shell_projection))


def all_frames() -> tuple:
    """Every admissible frame, in a fixed deterministic order.

    The first frame is the NOMINAL one (the first setting of every axis).
    It is nominal only by naming convention; nothing in any packet marks
    it out, which is the whole point."""
    axes = [opts for _n, opts in FRAME_AXES]
    return tuple(Frame(*combo) for combo in itertools.product(*axes))


FRAMES = all_frames()
NOMINAL_FRAME = FRAMES[0]


# =======================================================================
# The packet
# =======================================================================

@dataclass(frozen=True)
class Packet:
    """One thirty-bit word rendered in the packet grammar.

    Carries the word and its exact symbol decomposition -- face, path,
    shell -- together with the binary and octal renderings. Every field
    is a lossless rendering of the same word, so a Packet is the word
    seen in the grammar's symbols and not a coordinate."""

    word: int
    face: int
    path: str
    shell: int
    bits: str
    octal: str

    def as_symbols(self) -> tuple:
        return (self.face, self.path, self.shell)


# =======================================================================
# The finalized grammar
# =======================================================================

@dataclass(frozen=True)
class PacketGrammar:
    """The finalized coordinate codec.

    At the symbol level it is a bijection: :meth:`encode` turns a value
    into a Packet and :meth:`decode` returns exactly that value. At the
    coordinate level it is one-to-many: :meth:`decode_to_alias_set`
    returns a candidate coordinate for every admissible frame, and there
    are many frames. The grammar carries a :attr:`version_hash` over its
    parameters so a change to the field widths or the frame set produces a
    different codec that cannot be mistaken for this one."""

    face_bits: int = ip.FACE_BITS
    path_bits: int = ip.PATH_BITS
    shell_bits: int = ip.SHELL_BITS
    coord_modulus: int = COORD_MODULUS

    @property
    def word_capacity_bits(self) -> int:
        return self.face_bits + self.path_bits + self.shell_bits

    @property
    def word_modulus(self) -> int:
        return 1 << self.word_capacity_bits

    @property
    def version_hash(self) -> str:
        """A SHA-256 over the grammar parameters and the frame set.

        Two grammars with the same field widths, coordinate space and
        frame set share this hash; any change to any of them changes it.
        The codec is thereby versioned, and 'the same codec' is a
        checkable statement rather than an assumption."""
        parts = [
            f"face_bits={self.face_bits}",
            f"path_bits={self.path_bits}",
            f"shell_bits={self.shell_bits}",
            f"coord_modulus={self.coord_modulus}",
            f"frame_count={FRAME_COUNT}",
            "frames=" + ";".join(f.frame_id for f in FRAMES),
        ]
        return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()

    # --- the symbol-level bijection ------------------------------------

    def _check_value(self, value: int) -> int:
        if not isinstance(value, int) or isinstance(value, bool):
            raise CoordFinalError("a coordinate value must be a plain int")
        if not 0 <= value < self.word_modulus:
            raise CoordFinalError(
                f"value {value} does not fit in {self.word_capacity_bits} "
                f"bits (0..{self.word_modulus - 1})")
        return value

    def encode(self, value: int) -> Packet:
        """Encode an integer coordinate into a packet. Deterministic.

        The same value always yields the same packet. Inverted exactly by
        :meth:`decode` -- this is the codec's clean, load-bearing power:
        the frame is faithful at the symbol level.

        A value in range but malformed under the grammar -- a face field
        in the out-of-range band 20..31 the icosahedron has no face for --
        is refused, not folded onto a face."""
        self._check_value(value)
        try:
            face, path, shell = ip.decode(value)
        except ip.IcosaPacketError as exc:
            raise CoordFinalError(
                f"value {value} is in range but is not a valid packet "
                f"under this grammar: {exc}") from exc
        return Packet(
            word=value, face=face, path=path, shell=shell,
            bits=ip.word_bits(value), octal=ip.word_octal(value))

    def encode_symbols(self, face: int, path, shell: int) -> Packet:
        """Encode a face/path/shell triple directly into a packet."""
        word = ip.encode(face, path, shell)
        return self.encode(word)

    def decode(self, packet: Packet) -> int:
        """Decode a packet back to its integer coordinate. Exact.

        Returns the word the packet was built from. Composed with
        :meth:`encode` in either order this is the identity, so the codec
        is a bijection on the symbol space."""
        if not isinstance(packet, Packet):
            raise CoordFinalError("decode expects a Packet")
        word = ip.encode(packet.face, packet.path, packet.shell)
        if word != packet.word:
            raise CoordFinalError(
                f"malformed packet: its symbols encode to {word}, not to "
                f"its stated word {packet.word}")
        return word

    # --- the coordinate-level alias map --------------------------------

    def _frame_coordinate(self, word: int, frame: Frame) -> int:
        """The synthetic coordinate this word takes under this frame.

        A deterministic hash of the word and the frame settings into the
        abstract index space. It is NOT a geography: the space has no
        datum, no north and no units. Different frames send the same word
        to different coordinates, which is precisely why one packet does
        not pin down one place."""
        seed = f"COORDFINAL\x1f{word}\x1f{frame.frame_id}"
        digest = hashlib.sha256(seed.encode()).hexdigest()
        return int(digest, 16) % self.coord_modulus

    def decode_to_alias_set(self, packet: Packet) -> tuple:
        """Every candidate coordinate consistent with this packet.

        One candidate per admissible frame, returned as a set of
        alias candidates -- never a single destination. The size of this
        set (``FRAME_COUNT``, here thirty-two) is the honest output: the
        packet is consistent with all of them at once and selects none.
        Returned as a tuple of :class:`AliasCandidate` in frame order; the
        distinct coordinates are :meth:`alias_coordinates`."""
        word = self.decode(packet)
        out = []
        for frame in FRAMES:
            coord = self._frame_coordinate(word, frame)
            out.append(AliasCandidate(
                frame_id=frame.frame_id, coordinate=coord,
                is_nominal=(frame == NOMINAL_FRAME)))
        return tuple(out)

    def alias_coordinates(self, packet: Packet) -> frozenset:
        """The distinct candidate coordinates in the alias set."""
        return frozenset(a.coordinate
                         for a in self.decode_to_alias_set(packet))

    def nominal_candidate(self, packet: Packet) -> "AliasCandidate":
        """The candidate under the NOMINAL frame.

        It is a member of the alias set and nothing more. Returning it is
        not decoding: no field of the packet marks the nominal frame out
        from the other thirty-one, so this candidate is indistinguishable
        from its peers within the set."""
        for a in self.decode_to_alias_set(packet):
            if a.is_nominal:
                return a
        raise CoordFinalError("no nominal candidate (frame set is empty)")

    def true_candidate_is_distinguishable(self, packet: Packet) -> bool:
        """Whether any packet field singles out one candidate. Always False.

        A packet carries a face, a path and a shell. None of the five
        frame conventions is among them, so no packet field can prefer one
        frame's coordinate over another's. The nominal candidate is
        therefore not distinguishable within the alias set -- not because
        the search was lazy, but because the information that would
        distinguish it is not present in the packet."""
        _ = self.decode(packet)          # validates the packet
        return False


@dataclass(frozen=True)
class AliasCandidate:
    """One member of a packet's alias set: a frame and its coordinate."""

    frame_id: str
    coordinate: int
    is_nominal: bool = False


#: The finalized codec, at its default parameters.
GRAMMAR = PacketGrammar()


# =======================================================================
# Round-trip and determinism checks
# =======================================================================

def round_trip_ok(value: int, grammar: PacketGrammar = GRAMMAR) -> bool:
    """True iff ``decode(encode(value)) == value`` at the symbol level."""
    return grammar.decode(grammar.encode(value)) == value


def is_deterministic(value: int, grammar: PacketGrammar = GRAMMAR) -> bool:
    """True iff encoding a value twice yields identical packets."""
    return grammar.encode(value) == grammar.encode(value)


def alias_spread(packet: Packet, grammar: PacketGrammar = GRAMMAR) -> dict:
    """A numeric summary of how far apart the alias candidates lie.

    The candidates scatter across the whole synthetic index space, so the
    spread is large: the packet does not confine its coordinate to a
    neighbourhood, let alone a point."""
    coords = np.array(sorted(grammar.alias_coordinates(packet)),
                      dtype=object)
    values = np.array([int(c) for c in coords], dtype=float)
    return {
        "distinct_coordinates": int(len(coords)),
        "min": int(values.min()),
        "max": int(values.max()),
        "span": int(values.max() - values.min()),
        "space_size": grammar.coord_modulus,
        "claim_class": CLAIM_REPOSITORY_COMPUTATIONAL_RESULT,
    }


# =======================================================================
# The two load-bearing refusals
# =======================================================================

def refuse_alias_as_destination(alias_set, *_args, **_kwargs) -> None:
    """Refuse to collapse an alias set to one decoded destination.

    This is the refusal the whole module exists to enforce. An alias set
    is a set because the codec is one-to-many: the same packet is
    consistent with every frame at once, and reporting one member as
    *the* location does not remove the others -- it removes the reader's
    ability to see them. There is no evidence anywhere in this repository
    that selects among the members, so any single destination read off
    the set is a choice dressed as a decoding."""
    try:
        size = len(alias_set)
    except TypeError:
        size = FRAME_COUNT
    raise CoordFinalError(
        f"refused: an alias set of {size} candidate coordinate(s) cannot "
        f"be collapsed to a single decoded destination. The codec is "
        f"one-to-many by construction -- five conventions (face "
        f"numbering, body orientation, magnetic root, handedness, shell "
        f"projection) are each unfixed by the packet, so every one of the "
        f"{FRAME_COUNT} frames is equally consistent with it. No packet "
        f"field distinguishes them, and nothing measured here selects "
        f"one. Reporting the nominal, nearest or 'obvious' candidate as "
        f"the destination hides the others rather than eliminating them. "
        f"The alias set IS the output; its size is the result. The "
        f"standing verdict is {VERDICT}.")


def refuse_numeric_match_as_authentication(decoded_value,
                                           known_coordinate=None,
                                           *_args, **_kwargs) -> None:
    """Refuse to read a numeric match as authentication of a source.

    A decoded number that matches some known coordinate is a
    ``RETROSPECTIVE_NUMERIC_MATCH`` and nothing stronger. The match was
    found after the number was in view, from a space large enough that
    *some* known value is nearly always within reach, so it certifies
    neither a source nor a destination. A coincidence noticed afterwards
    is not a signature."""
    raise CoordFinalError(
        f"refused: a decoded value ({decoded_value!r}) matching a known "
        f"coordinate ({known_coordinate!r}) is a "
        f"{CLAIM_RETROSPECTIVE_NUMERIC_MATCH}, not authentication of a "
        f"source or a destination. The match is retrospective: it was "
        f"found once the number was already in view, and the codec's "
        f"alias set spans a space large enough that a match to some known "
        f"value is available almost always. A coincidence noticed after "
        f"the fact certifies nothing about where a packet came from or "
        f"where it points.")


# =======================================================================
# The report
# =======================================================================

def coordfinal_report(grammar: PacketGrammar = GRAMMAR) -> dict:
    sample = grammar.encode(ip.REGISTERED_VALUES[0])
    aliases = grammar.decode_to_alias_set(sample)
    return {
        "what_this_is": (
            "the finalized icosahedral-packet coordinate codec: a "
            "bijection at the symbol level and a one-to-many alias map at "
            "the coordinate level"),
        "version_hash": grammar.version_hash,
        "word_capacity_bits": grammar.word_capacity_bits,
        "symbol_round_trip_ok": all(
            round_trip_ok(v, grammar) for v in ip.REGISTERED_VALUES),
        "deterministic": all(
            is_deterministic(v, grammar) for v in ip.REGISTERED_VALUES),
        "frame_count": FRAME_COUNT,
        "alias_set_size": len(aliases),
        "distinct_alias_coordinates": len(
            grammar.alias_coordinates(sample)),
        "true_candidate_distinguishable":
            grammar.true_candidate_is_distinguishable(sample),
        "alias_spread": alias_spread(sample, grammar),
        "frame_axes": [name for name, _opts in FRAME_AXES],
        "refusals": [
            "refuse_alias_as_destination",
            "refuse_numeric_match_as_authentication",
        ],
        "claim_class": CLAIM_REPOSITORY_COMPUTATIONAL_RESULT,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not say the codec decodes a location. The codec is a "
            "clean bijection at the SYMBOL level -- a thirty-bit word "
            "round-trips through face, path and shell without loss -- and "
            "that faithfulness is a fact about the bit layout, not about "
            "any place. At the COORDINATE level the codec is one-to-many: "
            "the same packet decodes to an ALIAS SET of "
            f"{FRAME_COUNT} candidate coordinates, one per admissible "
            "frame, because face numbering, body orientation, magnetic "
            "root, handedness and shell projection are each unfixed by "
            "the packet. No packet field distinguishes the nominal "
            "candidate from the rest, so the alias set cannot be collapsed "
            "to a single decoded destination "
            "(refuse_alias_as_destination), and a decoded number that "
            "matches a known coordinate is a retrospective numeric match "
            "rather than authentication "
            "(refuse_numeric_match_as_authentication). The alias "
            "coordinates live in a synthetic index space with no datum, "
            "north or units; no place is named or implied. Nothing here "
            "is measured and no physical validation is claimed."),
    }


__all__ = [
    "CoordFinalError", "VERDICT", "PHYSICAL_VALIDATION",
    "COORD_MODULUS", "FRAME_AXES", "FRAME_COUNT",
    "Frame", "all_frames", "FRAMES", "NOMINAL_FRAME",
    "Packet", "PacketGrammar", "GRAMMAR", "AliasCandidate",
    "round_trip_ok", "is_deterministic", "alias_spread",
    "refuse_alias_as_destination",
    "refuse_numeric_match_as_authentication",
    "coordfinal_report",
    "CLAIM_EXACT_IDENTITY", "CLAIM_ANALYTIC_MODEL",
    "CLAIM_REPOSITORY_COMPUTATIONAL_RESULT",
    "CLAIM_RETROSPECTIVE_NUMERIC_MATCH", "CLAIM_UNSUPPORTED",
]
