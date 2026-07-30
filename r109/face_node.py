"""R10.9 node-23 / source-face arithmetic (R109-FACE-01..03).

Exact identities, reproduced:

    node 23 is a SIX-BIT 64-state face/node selector (not a 5-bit face)
    Stonehenge top-six state = 9
    23 - 9 = 14
    source_face = (F5 + 14) mod 20

The physical meaning of these identities remains source-reported; the
arithmetic below is deterministic. Face ordering is clockwise on the
dodecahedral dual from the Wilkes root using the SAA phase-zero
direction (source-reported; the geometric profiles live in
``cwatlas.r1082.wilkes`` and ``cwatlas.r1082.saa``).
"""

from __future__ import annotations

from r109.types import CodecTypeError

NODE_SELECTOR_BITS = 6
NODE_STATES = 2 ** NODE_SELECTOR_BITS          # 64
NODE_23 = 23                                   # six-bit selector state
STONEHENGE_TOP_SIX_STATE = 9
FACE_OFFSET = NODE_23 - STONEHENGE_TOP_SIX_STATE   # 14
FACE_COUNT = 20

FACE_ORDER_AUTHORITY = {
    "root_feature": "Wilkes face",
    "routing_graph": "dodecahedral dual",
    "order": "clockwise",
    "phase_zero": "SAA direction",
    "evidence_class": "SOURCE_REPORTED",
}


def node_state(value: int) -> int:
    """Validate a six-bit 64-state node selector."""
    if not isinstance(value, int) or not 0 <= value < NODE_STATES:
        raise CodecTypeError(
            f"node selector must be a six-bit state 0..{NODE_STATES - 1}")
    return value


def source_face(f5: int) -> int:
    """source_face = (F5 + 14) mod 20, for VALID packet faces only.

    Reserved faces (20..31) are refused before translation — the
    modulo never launders a reserved face into a source face.
    """
    if not isinstance(f5, int) or not 0 <= f5 <= 19:
        raise CodecTypeError(
            f"F5={f5} is not a valid source-face register value "
            f"(0..19); reserved faces are refused, never promoted")
    return (f5 + FACE_OFFSET) % FACE_COUNT


def refuse_literal_face_23(*_a, **_k) -> None:
    """A literal physical F5=23 remains reserved and refused."""
    raise CodecTypeError(
        "refused: F5=23 is in the reserved 20..31 range and names no "
        "source face; node 23 is a SIX-bit 64-state selector, not a "
        "five-bit packet face (R109-FACE-01/03)")


def receipt() -> dict:
    """Deterministic arithmetic receipt for the face/node identities."""
    return {
        "node_selector_bits": NODE_SELECTOR_BITS,
        "node_states": NODE_STATES,
        "node_23": NODE_23,
        "stonehenge_top_six_state": STONEHENGE_TOP_SIX_STATE,
        "offset_23_minus_9": FACE_OFFSET,
        "source_face_formula": "(F5 + 14) mod 20",
        "stonehenge_example": {"f5": 4, "source_face": source_face(4)},
        "face_order_authority": FACE_ORDER_AUTHORITY,
        "evidence_class": "EXACT_ARITHMETIC (identities) / "
                          "SOURCE_REPORTED (meaning)",
    }
