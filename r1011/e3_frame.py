"""R10.11D — octal-aligned E3 frame for the ``16...t`` family.

Arithmetic correction over R10.11C: the ``E2`` payload frame cannot
hold the sealed vector ``1687209343`` (stripped payload ``8720934``
needs 24 bits). The octal-aligned candidate

    1_3 | 6_3 | E3 | S6 | S6 | S6 | C3^depth | terminal_3

is 30 bits at compact precision and adds exactly three bits per
refinement level. Every R10.11C state triple and sparse transition is
preserved (old ``E2`` values acquire a leading zero inside ``E3``).

Semantics guard (do NOT overwrite the source): the source-reported
statement says the leading shell/epoch information concerns TWO bits;
the total octal-ALIGNED field here is THREE bits, and the internal
semantic subdivision of E3 remains UNRESOLVED.

Terminal-digit guard: only terminal 3 is the source-reported broad
surface class. Terminals 5, 7, 9 are parsed and RECORDED, never
silently treated as class 3.
"""

from __future__ import annotations

from dataclasses import dataclass

HEADER = "16"                       # octal 1|6 = 001|110 (Sol|Terra, locked)
SURFACE_TERMINAL = 3                # ONLY terminal 3 is broad surface class

E3_SEMANTICS = ("total aligned field = 3 bits; source-reported "
                "shell/epoch wording concerns 2 bits; internal "
                "subdivision of E3 UNRESOLVED")


class E3FrameError(ValueError):
    pass


@dataclass(frozen=True)
class E3Parse:
    wire: int
    e3: int
    states: tuple[int, int, int]
    children: tuple[int, ...]        # depth = len(children)
    terminal: int
    payload_bits: int

    @property
    def depth(self) -> int:
        return len(self.children)

    @property
    def terminal_is_surface_class(self) -> bool:
        return self.terminal == SURFACE_TERMINAL


def parse(wire: int) -> E3Parse:
    s = str(wire)
    if not s.startswith(HEADER) or len(s) < 9:
        raise E3FrameError(f"{wire} is not a 16-headed wire of the "
                           f"segmented family")
    terminal = int(s[-1])
    mid = s[2:-1]
    depth = len(mid) - 6
    if depth < 0:
        raise E3FrameError(f"{wire}: payload shorter than compact width")
    width = 21 + 3 * depth
    pay = int(mid)
    if pay >= (1 << width):
        raise E3FrameError(
            f"{wire}: payload {pay} exceeds {width} bits at depth {depth} "
            f"— width family violated, never truncated")
    b = format(pay, f"0{width}b")
    e3 = int(b[:3], 2)
    states = tuple(int(b[3 + 6 * i:9 + 6 * i], 2) for i in range(3))
    children = tuple(int(b[21 + 3 * i:24 + 3 * i], 2) for i in range(depth))
    return E3Parse(wire, e3, states, children, terminal, width)


def encode(p: E3Parse) -> int:
    bits = (format(p.e3, "03b")
            + "".join(format(st, "06b") for st in p.states)
            + "".join(format(c, "03b") for c in p.children))
    pay = int(bits, 2)
    return int(HEADER + str(pay).zfill(6 + p.depth) + str(p.terminal))
