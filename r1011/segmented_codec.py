"""R10.11C — segmented wire codec for the ``16...3`` family (LOCKED).

Source-reported confirmations (2026-07-27/28 authority patch), now the
CURRENT parsing authority for wires of the form ``16<payload>3``:

    header: two octal symbols  1|6 = 001|110, ordered Sol|Terra
    terminal decimal 3: broad surface class
    compact payload (6 digits):  E2 | S6 | S6 | S6   (20 bits, zero-padded)
    refined payload (7 digits):  E2 | S6 | S6 | S6 | C3  (23 bits)
    E2: finer shell/epoch state (NOT a face class)
    transition operator: T[current_state, added_child] -> next_state

Verified EXACTLY on all four confirmed same-location pairs (Stonehenge,
Toronto, CYYT, and the confirmed slash pair): refined states are
``T[compact_state, child]`` slot-by-slot with E2 preserved — the twelve
sparse entries below are precisely those transitions, mutually
consistent and per-child injective. The middle-state-23 checksum for
``165872393`` holds under this frame.

The full 64x8 table is NOT in the repository or any archive (searched;
no file matches even two of the twelve triples). The 500 unknown cells
are **UNDERDETERMINED** — decoding through an unknown cell returns a
typed refusal, never a guess.

The monolithic ``F5|Q22|S3`` reading remains a preserved HISTORICAL
candidate: the explicit compatibility test shows its fields do NOT
correspond to the segmented fields (old F5=5 vectors split across
E2=10 and E2=11), so the two are different partitions of the same
integers; both stay exact and reversible as READINGS.
"""

from __future__ import annotations

from dataclasses import dataclass

HEADER = "16"
HEADER_OCTAL_BITS = ("001", "110")           # 1|6, Sol|Terra (source-reported)
TERMINAL_SURFACE = "3"                        # broad surface class

#: Sparse transition table T[(state, child)] -> next_state.
#: SOURCE_REPORTED 2026-07-27/28; the ONLY known cells of the 64x8 table.
T_SPARSE: dict[tuple[int, int], int] = {
    (15, 5): 5, (30, 5): 40, (4, 5): 37,
    (26, 5): 30, (1, 5): 25, (52, 5): 31,
    (15, 6): 49, (55, 6): 53, (25, 6): 45,
    (14, 6): 51, (11, 6): 14, (61, 6): 36,
}

#: Inverse per child (validated injective on known cells at import).
T_INVERSE: dict[tuple[int, int], int] = {}
for (_s, _c), _n in T_SPARSE.items():
    key = (_n, _c)
    if key in T_INVERSE:
        raise ValueError("sparse table not injective per child")
    T_INVERSE[key] = _s

TABLE_STATUS = ("UNDERDETERMINED: 12 of 512 cells known (source-"
                "reported); no repository or archive table matches; "
                "unknown cells REFUSE, never guessed")


class SegmentedCodecError(ValueError):
    pass


@dataclass(frozen=True)
class CompactSeg:
    e2: str                      # two bits, finer shell/epoch state
    states: tuple[int, int, int]

    def payload_int(self) -> int:
        bits = self.e2 + "".join(format(s, "06b") for s in self.states)
        return int(bits, 2)


@dataclass(frozen=True)
class RefinedSeg:
    e2: str
    states: tuple[int, int, int]
    child: int

    def payload_int(self) -> int:
        bits = (self.e2 + "".join(format(s, "06b") for s in self.states)
                + format(self.child, "03b"))
        return int(bits, 2)


def _split(raw: int) -> tuple[str, str]:
    s = str(raw)
    if not (s.startswith(HEADER) and s.endswith(TERMINAL_SURFACE)):
        raise SegmentedCodecError(
            f"{raw} is not in the 16...3 family; the segmented codec "
            f"applies only there (other families UNRESOLVED)")
    return s[2:-1], s


def decode_compact(raw: int) -> CompactSeg:
    mid, _ = _split(raw)
    if len(mid) != 6:
        raise SegmentedCodecError(
            f"{raw}: compact 16...3 wires carry a 6-digit payload")
    pay = int(mid)
    if pay >= (1 << 20):
        raise SegmentedCodecError("compact payload exceeds 20 bits")
    b = format(pay, "020b")
    return CompactSeg(b[:2], tuple(int(b[2 + 6 * i:8 + 6 * i], 2)
                                   for i in range(3)))


def decode_refined(raw: int) -> RefinedSeg:
    mid, _ = _split(raw)
    if len(mid) != 7:
        raise SegmentedCodecError(
            f"{raw}: refined 16...3 wires carry a 7-digit payload")
    pay = int(mid)
    if pay >= (1 << 23):
        raise SegmentedCodecError("refined payload exceeds 23 bits")
    b = format(pay, "023b")
    return RefinedSeg(b[:2], tuple(int(b[2 + 6 * i:8 + 6 * i], 2)
                                   for i in range(3)), int(b[20:], 2))


def encode_compact(seg: CompactSeg) -> int:
    return int(HEADER + str(seg.payload_int()).zfill(6) + TERMINAL_SURFACE)


def encode_refined(seg: RefinedSeg) -> int:
    return int(HEADER + str(seg.payload_int()).zfill(7) + TERMINAL_SURFACE)


def parent_reduce(refined: RefinedSeg) -> CompactSeg:
    """Refined -> compact parent through the inverse transition table.

    E2 is preserved; each state passes through T^-1[., child]. Unknown
    cells refuse (UNDERDETERMINED, R10.11C)."""
    parent_states = []
    for s in refined.states:
        key = (s, refined.child)
        if key not in T_INVERSE:
            raise SegmentedCodecError(
                f"T^-1[{s}, child={refined.child}] is an UNKNOWN cell of "
                f"the 64x8 table ({TABLE_STATUS})")
        parent_states.append(T_INVERSE[key])
    return CompactSeg(refined.e2, tuple(parent_states))


def child_apply(compact: CompactSeg, child: int) -> RefinedSeg:
    """Compact -> refined through T (forward). Unknown cells refuse."""
    out = []
    for s in compact.states:
        key = (s, child)
        if key not in T_SPARSE:
            raise SegmentedCodecError(
                f"T[{s}, child={child}] is an UNKNOWN cell of the 64x8 "
                f"table ({TABLE_STATUS})")
        out.append(T_SPARSE[key])
    return RefinedSeg(compact.e2, tuple(out), child)


#: Explicit compatibility record vs the historical monolithic profile.
MONOLITHIC_COMPATIBILITY = {
    "status": "FIELDS_DO_NOT_CORRESPOND",
    "evidence": "old F5=5 vectors split across segmented E2 values "
                "(167854923/167849523 -> E2=10, 168724343 -> E2=11); "
                "old S3 values {1,3,5,7} appear against uniform "
                "terminal-3 surface class",
    "disposition": "F5|Q22|S3 preserved as EXACT_OLD_STRUCTURAL_PROFILE "
                   "(historical candidate); segmented parsing is current "
                   "source-reported authority for the 16...3 family; "
                   "both readings remain exact and reversible on the "
                   "same integers",
}
