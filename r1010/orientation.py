"""R10.10 Phase 2 — triangle orientation algebra (the S3 group).

A triangular face's local frame is one of the six permutations of its
corner labels (A,B,C) = (0,1,2): three cyclic rotations (even parity)
and three reflected rotations (odd parity). Pure stdlib, exact,
hash-stable.

Convention: an orientation ``o`` is the permutation tuple
``(o[0], o[1], o[2])`` meaning "local corner i is global corner o[i]".
Composition is function composition: ``(a * b)[i] = a[b[i]]``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools


class OrientationError(ValueError):
    pass


@dataclass(frozen=True)
class Orientation:
    perm: tuple[int, int, int]

    def __post_init__(self) -> None:
        if sorted(self.perm) != [0, 1, 2]:
            raise OrientationError(f"not a corner permutation: {self.perm}")

    # ------------------------------------------------------------ algebra
    def compose(self, other: "Orientation") -> "Orientation":
        """self ∘ other (apply ``other`` first, then ``self``)."""
        return Orientation(tuple(self.perm[other.perm[i]] for i in range(3)))

    def inverse(self) -> "Orientation":
        inv = [0, 0, 0]
        for i, p in enumerate(self.perm):
            inv[p] = i
        return Orientation(tuple(inv))

    @property
    def parity(self) -> int:
        """+1 for cyclic rotations, -1 for reflections."""
        p = self.perm
        swaps = sum(1 for i in range(3) for j in range(i + 1, 3)
                    if p[i] > p[j])
        return 1 if swaps % 2 == 0 else -1

    # -------------------------------------------------------- application
    def apply_vertices(self, verts) -> tuple:
        """Reorder a vertex triple into this local frame."""
        if len(verts) != 3:
            raise OrientationError("vertex triple required")
        return tuple(verts[self.perm[i]] for i in range(3))

    def apply_corner(self, local_corner: int) -> int:
        if local_corner not in (0, 1, 2):
            raise OrientationError("corner must be 0..2")
        return self.perm[local_corner]

    # ------------------------------------------------------ serialization
    def serialize(self) -> str:
        return "".join(str(p) for p in self.perm)

    @classmethod
    def deserialize(cls, text: str) -> "Orientation":
        if len(text) != 3 or any(c not in "012" for c in text):
            raise OrientationError(f"bad serialized orientation {text!r}")
        return cls(tuple(int(c) for c in text))

    def stable_hash(self) -> str:
        return hashlib.sha256(self.serialize().encode("ascii")).hexdigest()[:16]


IDENTITY = Orientation((0, 1, 2))

#: All six group elements, deterministic order.
ALL: tuple[Orientation, ...] = tuple(
    Orientation(p) for p in itertools.permutations((0, 1, 2)))

ROTATIONS = tuple(o for o in ALL if o.parity == 1)
REFLECTIONS = tuple(o for o in ALL if o.parity == -1)


def group_receipt() -> dict:
    """Exhaustive closure/inverse/parity receipt for the six elements."""
    table = {}
    for a in ALL:
        for b in ALL:
            table[f"{a.serialize()}*{b.serialize()}"] = a.compose(b).serialize()
    return {
        "elements": [o.serialize() for o in ALL],
        "rotations": [o.serialize() for o in ROTATIONS],
        "reflections": [o.serialize() for o in REFLECTIONS],
        "identity": IDENTITY.serialize(),
        "inverses": {o.serialize(): o.inverse().serialize() for o in ALL},
        "parities": {o.serialize(): o.parity for o in ALL},
        "cayley_table": table,
        "closure_verified": all(v in {o.serialize() for o in ALL}
                                for v in table.values()),
        "stable_hashes": {o.serialize(): o.stable_hash() for o in ALL},
    }
