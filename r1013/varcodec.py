"""R10.13 Phase 28 — two-sided variable codec.

    C_L^dL | E3 | S_tor | S_pol | S_rad | C_R^dR

Legal payload width W = 21 + 3*(dL + dR) bits. There is NO extension
bit (supersedes any one-bit-extension reading). The parser chooses the
smallest legal width that contains the payload, then enumerates every
legal (dL, dR) split of the extra depth. Right-refinement with dL=0
coincides bit-for-bit with the R10.11D E3 frame (children appended on
the right), which this module verifies rather than assumes.

The three S6 states are SOURCE-REPORTED as toroidal, poloidal, and
radial phases. That labelling is carried as provenance; the
state-to-geometry mapping stays UNDERDETERMINED.
"""

from __future__ import annotations

from dataclasses import dataclass

from r1013.errors import UserError

STATE_LABELS_SOURCE_REPORTED = ("toroidal_phase", "poloidal_phase",
                                "radial_phase")


class VarCodecError(ValueError):
    pass


@dataclass(frozen=True)
class TwoSidedParse:
    wire: str
    e3: int
    states: tuple            # (S_tor, S_pol, S_rad)
    left_children: tuple
    right_children: tuple
    terminal: int
    width_bits: int

    @property
    def depth_left(self):
        return len(self.left_children)

    @property
    def depth_right(self):
        return len(self.right_children)


def _clean(wire) -> str:
    s = str(wire).strip()
    if not s.isdigit():
        raise VarCodecError(f"wire {wire!r} must be decimal digits")
    if not s.startswith("16"):
        raise VarCodecError(f"wire {s} does not start with header 16")
    if len(s) < 9:
        raise VarCodecError(f"wire {s} too short for the 21-bit core")
    return s


def parse_all(wire) -> dict:
    """Smallest legal width for the wire's digit family, then EVERY
    legal (dL, dR) split. Digit convention matches the LOCKED R10.11D
    frame: 6 payload digits at depth 0, one more per extra level;
    payloads exceeding the width refuse (never truncated)."""
    s = _clean(wire)
    payload_digits, terminal = s[2:-1], int(s[-1])
    value = int(payload_digits)
    d = len(payload_digits) - 6
    if d < 0:
        raise VarCodecError(f"wire {s}: payload shorter than the "
                            "compact width")
    width = 21 + 3 * d
    if value >= (1 << width):
        raise VarCodecError(
            f"wire {s}: payload {value} exceeds {width} bits at extra "
            f"depth {d} — width family violated, never truncated")
    splits = []
    for dl in range(d + 1):
        dr = d - dl
        bits = value
        # layout MSB->LSB: C_L^dL | E3 | S S S | C_R^dR
        right = []
        for _ in range(dr):
            right.append(bits & 0b111)
            bits >>= 3
        right.reverse()
        s_rad = bits & 0b111111
        bits >>= 6
        s_pol = bits & 0b111111
        bits >>= 6
        s_tor = bits & 0b111111
        bits >>= 6
        e3 = bits & 0b111
        bits >>= 3
        left = []
        for _ in range(dl):
            left.append(bits & 0b111)
            bits >>= 3
        left.reverse()
        if bits != 0:
            continue                      # payload exceeded this layout
        splits.append(TwoSidedParse(
            s, e3, (s_tor, s_pol, s_rad), tuple(left), tuple(right),
            terminal, width))
    if not splits:
        raise VarCodecError(f"wire {s}: payload does not fit any legal "
                            f"(dL,dR) split at width {width}")
    return {"wire": s, "width_bits": width, "extra_depth": d,
            "split_count": len(splits), "splits": splits,
            "state_labels_source_reported":
                list(STATE_LABELS_SOURCE_REPORTED),
            "no_extension_bit": True}


def encode(p: TwoSidedParse) -> str:
    bits = 0
    for c in p.left_children:
        bits = (bits << 3) | c
    bits = (bits << 3) | p.e3
    for s6 in p.states:
        bits = (bits << 6) | s6
    for c in p.right_children:
        bits = (bits << 3) | c
    d = len(p.left_children) + len(p.right_children)
    return "16" + str(bits).zfill(6 + d) + str(p.terminal)


def agrees_with_e3_frame(wire) -> dict:
    """Verify (not assume) that the dL=0 split reproduces the R10.11D
    canonical parser on a segmented wire."""
    from r1011 import e3_frame as e3
    ours = parse_all(wire)
    theirs = e3.parse(int(wire))
    d0 = [s for s in ours["splits"] if s.depth_left == 0]
    if not d0:
        return {"wire": str(wire), "agrees": False,
                "reason": "no dL=0 split exists"}
    s = d0[0]
    agrees = (s.e3 == theirs.e3
              and s.states == tuple(theirs.states)
              and s.right_children == tuple(theirs.children)
              and s.terminal == theirs.terminal)
    return {"wire": str(wire), "agrees": bool(agrees),
            "two_sided_dl0": {"e3": s.e3, "states": list(s.states),
                              "right": list(s.right_children)},
            "e3_frame": {"e3": theirs.e3, "states": list(theirs.states),
                         "children": list(theirs.children)}}
