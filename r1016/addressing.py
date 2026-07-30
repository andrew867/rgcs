"""R10.16C — TransportWire / SurfaceWord type split.

The R10.16B patch fixed WHICH word to project. This fixes HOW that
word is read, which was a second and deeper defect.

A transport wire is lexical: ``16 | payload_decimal | 3``. A surface
word is NUMERIC: a 30-bit value whose TEN-DIGIT OCTAL rendering is the
surface address. Those are different objects, and reparsing a resolved
surface word back into a lexical 16...3 wire is a category error:

    WRONG   168500683 -> "16" | "850068" | "3" -> payload octal 3174224
    RIGHT   168500683 -> format(168500683, "010o") -> 1202616713

The wrong reading produced a spurious prefix/distance contradiction
that is now retracted. Under the correct surface view, the four strict
anchors are cleanly hierarchical.

Rules enforced here:
  1. active_split() may only consume a TransportWire.
  2. resolve_surface_word() returns a SurfaceWord, never a TransportWire.
  3. hierarchy metrics use SurfaceWord.surface_octal10.
  4. payload-prefix metrics survive ONLY as labelled diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass

RAW_DIAGNOSTIC = "RAW_TRANSPORT_WIRE_DIAGNOSTIC"
REPARSE_DIAGNOSTIC = "SURFACE_WORD_REPARSED_AS_WIRE_DIAGNOSTIC"


class AddressingError(ValueError):
    pass


@dataclass(frozen=True)
class TransportWire:
    """The lexical carrier: header, decimal payload, terminal."""
    raw_text: str

    def __post_init__(self):
        s = self.raw_text
        if not s.isdigit() or len(s) < 4:
            raise AddressingError(
                f"transport wire {s!r} must be at least four decimal "
                "digits")

    @property
    def header(self) -> str:
        return self.raw_text[:2]

    @property
    def payload_decimal_text(self) -> str:
        return self.raw_text[2:-1]

    @property
    def terminal(self) -> str:
        return self.raw_text[-1]

    @property
    def payload_octal(self) -> str:
        """DIAGNOSTIC ONLY. This is the transport-layer view and must
        never be used for hierarchy metrics."""
        return format(int(self.payload_decimal_text), "o")

    def record(self) -> dict:
        return {"kind": "TransportWire", "raw_text": self.raw_text,
                "header": self.header,
                "payload_decimal_text": self.payload_decimal_text,
                "payload_octal": self.payload_octal,
                "terminal": self.terminal,
                "payload_octal_scope": REPARSE_DIAGNOSTIC}


@dataclass(frozen=True)
class SurfaceWord:
    """The numeric surface/projection address."""
    value: int
    source: str = "raw_vector"

    def __post_init__(self):
        if not isinstance(self.value, int) or self.value < 0:
            raise AddressingError("surface word must be a "
                                  "non-negative integer")

    @property
    def surface_octal10(self) -> str:
        return format(self.value, "010o")

    @property
    def F5(self) -> int:
        return (self.value >> 25) & 0b11111

    @property
    def Q22(self) -> int:
        return (self.value >> 3) & ((1 << 22) - 1)

    @property
    def S3(self) -> int:
        return self.value & 0b111

    def record(self) -> dict:
        return {"kind": "SurfaceWord", "value": self.value,
                "source": self.source,
                "surface_octal10": self.surface_octal10,
                "F5": self.F5, "Q22": self.Q22, "S3": self.S3}


def active_split(wire) -> dict:
    """Lexical split. Refuses anything that is not a TransportWire."""
    if isinstance(wire, SurfaceWord):
        raise AddressingError(
            "refused: active_split() may not consume a SurfaceWord. "
            "Reparsing a resolved surface word as a lexical 16...3 "
            "transport wire is a category error and produced the "
            "retracted payload-prefix contradiction. Use "
            "SurfaceWord.surface_octal10 instead.")
    if not isinstance(wire, TransportWire):
        raise AddressingError(
            f"active_split() requires a TransportWire, got "
            f"{type(wire).__name__}")
    return wire.record()


def resolve_surface_word(record: dict) -> SurfaceWord:
    """Resolver from the R10.16B patch, now returning a SurfaceWord."""
    canonical = record.get("canonical_packet_or_candidate")
    status = record.get("current_status", "")

    if canonical and str(canonical).isdigit():
        if "CORRECTED_WIRE_TO_CANONICAL_CANDIDATE" in status:
            return SurfaceWord(int(canonical),
                               "canonical_packet_or_candidate")
        if "LEGACY_SAME_LOCATION_PAIR" in status:
            return SurfaceWord(int(canonical),
                               "canonical_packet_or_candidate")

    return SurfaceWord(int(record["raw_vector"]), "raw_vector")


def surface_prefix(a: SurfaceWord, b: SurfaceWord) -> int:
    n = 0
    for x, y in zip(a.surface_octal10, b.surface_octal10):
        if x != y:
            break
        n += 1
    return n
