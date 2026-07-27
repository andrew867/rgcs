"""R10.9 canonical typed address family (Phase 3).

Explicit types instead of bare integers, per
``02_SPEC/VARIABLE_DEPTH_CODEC_SPEC.md``. The decimal terminal marker,
binary S3 field, physical shell semantics, and epoch/phase closure are
DISTINCT until proved equivalent (shell-marker firewall): a parser may
report all of them, and may never silently collapse them.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class CodecTypeError(ValueError):
    """A typed-address invariant was violated (never silently fixed)."""


@dataclass(frozen=True)
class SolGroup:
    """Source-reported federation group/member codes. Typed, not parsed:
    the wire encoding (transport-header width, position) is unknown and
    is not invented here."""

    group_code: int                    # 16, source-reported
    member_code: int | None            # Terra=5, Luna=7 when resolved
    evidence_class: str

    def __post_init__(self) -> None:
        if self.evidence_class != "SOURCE_REPORTED":
            raise CodecTypeError(
                "SolGroup values are source-reported only; no other "
                "evidence class is currently justified")


SOL_GROUP = SolGroup(group_code=16, member_code=None,
                     evidence_class="SOURCE_REPORTED")
TERRA = SolGroup(group_code=16, member_code=5,
                 evidence_class="SOURCE_REPORTED")
LUNA = SolGroup(group_code=16, member_code=7,
                evidence_class="SOURCE_REPORTED")


@dataclass(frozen=True)
class DecimalTerminalMarker:
    """The last DECIMAL digit of the wire value, kept as its own typed
    fact (source-reported: 3 => surface object, 7 => object in orbit).
    NOT the binary S3 field; the firewall test proves the distinction
    is maintained."""

    digit: int
    source_reported_meaning: str

    @classmethod
    def from_raw(cls, raw: int) -> "DecimalTerminalMarker":
        d = int(str(raw)[-1])
        meaning = {3: "surface object (source-reported)",
                   7: "object in orbit (source-reported)"}.get(
                       d, "no source-reported meaning recorded")
        return cls(digit=d, source_reported_meaning=meaning)


@dataclass(frozen=True)
class WireAddress:
    """One raw wire value with its exact renderings; no truncation."""

    raw_decimal: int
    decimal_digits: str
    decimal_terminal_marker: DecimalTerminalMarker
    binary: str
    octal: str
    octal_depth: int
    provenance_id: str

    @classmethod
    def from_raw(cls, raw: int, provenance_id: str) -> "WireAddress":
        if not isinstance(raw, int) or isinstance(raw, bool) or raw < 0:
            raise CodecTypeError("wire value must be a non-negative int")
        octal = format(raw, "o")
        return cls(
            raw_decimal=raw,
            decimal_digits=str(raw),
            decimal_terminal_marker=DecimalTerminalMarker.from_raw(raw),
            binary=format(raw, "b"),
            octal=octal,
            octal_depth=len(octal),
            provenance_id=provenance_id,
        )


@dataclass(frozen=True)
class CompactAddress:
    """T10 fields (the frozen F5|Q22|S3 packet)."""

    f5: int
    q22_path: tuple[int, ...]          # eleven quaternary symbols
    s3: int

    def __post_init__(self) -> None:
        if len(self.q22_path) != 11 or any(p not in (0, 1, 2, 3)
                                           for p in self.q22_path):
            raise CodecTypeError("q22_path must be 11 quaternary symbols")
        if not 0 <= self.f5 <= 19:
            raise CodecTypeError("f5 must be a valid source face 0..19")
        if not 0 <= self.s3 <= 7:
            raise CodecTypeError("s3 must fit 3 bits")


@dataclass(frozen=True)
class RefinedAddress:
    """T11 candidate decode: parent path + ONE appended 8-way child,
    child at the end of the recursive path before shell/epoch."""

    source_face: int
    path: tuple[int, ...]
    child_digit: int
    shell: int
    epoch_state: object | None
    parent_compact: CompactAddress | None
    alias_id: str                       # which T11 candidate produced this

    def __post_init__(self) -> None:
        if not 0 <= self.child_digit <= 7:
            raise CodecTypeError("child digit is one eight-way refinement")


@dataclass(frozen=True)
class ShellSemantics:
    """Physical shell semantics (source-reported), separate from bits."""

    shell_id: int
    semantic: str
    evidence_class: str = "SOURCE_REPORTED"


SHELL3_CRUSTAL_BAND = ShellSemantics(
    3, "finite crustal/surface band; sea floor, land and mountains occupy "
       "variable depth within it; thickness is body-specific")
SHELL7_ORBIT_CLASS = ShellSemantics(
    7, "orbital object class")
