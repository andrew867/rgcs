"""A11-A13 — exact radix algebra, quaternary symbol ontology, and the
address/payload separation.

The bridge is exact and finite, so it is verified exhaustively rather
than sampled: all 4096 keys round-trip through quaternary (6 digits),
octal (4 digits) and binary (12 bits), and the three representations
agree with each other for every key.

The ontology point (core/06, Q03): Q0-Q3 are ABSTRACT symbols. Calling
them "up/down/left/right" requires a declared basis — without one the
naming is meaningless, and ``SymbolAlphabet`` refuses it. This is the
mechanical form of "do not call them up/down/left/right without a
basis".

The architecture point (core/06, "Address or payload"): the address is
stored DIGITALLY and EXACTLY; only the local payload codeword is a
candidate for physical/quaternary storage. That keeps physical drift
out of the index, and ``Codeword`` enforces the separation by type.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import ClaimBoundaryError

QUATERNARY_DIGITS = 6          # 4^6 = 4096
OCTAL_DIGITS = 4               # 8^4 = 4096
BITS = 12                      # 2^12 = 4096
KEY_SPACE = 4096

#: The exact identity this programme is built on.
RADIX_IDENTITY = "4096 = 8^4 = 4^6 = 2^12 ; 64 = 8^2 = 4^3 = 2^6"


def to_quaternary(k: int, digits: int = QUATERNARY_DIGITS) -> list:
    """K -> [q0..q5] with K = sum q_j * 4^(5-j)."""
    if not (0 <= k < 4 ** digits):
        raise ClaimBoundaryError(
            f"key {k} outside [0, {4 ** digits})")
    out = []
    for j in range(digits):
        out.append((k // (4 ** (digits - 1 - j))) % 4)
    return out


def from_quaternary(q: list) -> int:
    n = len(q)
    total = 0
    for j, d in enumerate(q):
        if not (0 <= int(d) <= 3):
            raise ClaimBoundaryError(f"quaternary digit {d} not in 0..3")
        total += int(d) * 4 ** (n - 1 - j)
    return total


def to_octal(k: int, digits: int = OCTAL_DIGITS) -> list:
    if not (0 <= k < 8 ** digits):
        raise ClaimBoundaryError(f"key {k} outside [0, {8 ** digits})")
    return [(k // (8 ** (digits - 1 - j))) % 8 for j in range(digits)]


def from_octal(o: list) -> int:
    n = len(o)
    total = 0
    for j, d in enumerate(o):
        if not (0 <= int(d) <= 7):
            raise ClaimBoundaryError(f"octal digit {d} not in 0..7")
        total += int(d) * 8 ** (n - 1 - j)
    return total


def to_bits(k: int, width: int = BITS) -> list:
    if not (0 <= k < 2 ** width):
        raise ClaimBoundaryError(f"key {k} outside [0, {2 ** width})")
    return [(k >> (width - 1 - i)) & 1 for i in range(width)]


def from_bits(b: list) -> int:
    n = len(b)
    total = 0
    for i, bit in enumerate(b):
        if bit not in (0, 1):
            raise ClaimBoundaryError(f"bit {bit} not in 0..1")
        total += int(bit) << (n - 1 - i)
    return total


def radix_bridge(k: int) -> dict:
    """All three exact representations of one key, plus the standing
    refusal that this is compression."""
    return {
        "key": k,
        "quaternary": to_quaternary(k),
        "octal": to_octal(k),
        "bits": to_bits(k),
        "information_content_bits": BITS,
        "is_compression": False,
        "note": "exact radix conversion; identical information "
                "content in every representation (12 bits)",
        "evidence_class": "DERIVED_ARITHMETIC",
    }


def exhaustive_roundtrip() -> dict:
    """Verify all 4096 keys in all three radices — the space is finite,
    so nothing is sampled."""
    bad = []
    for k in range(KEY_SPACE):
        if from_quaternary(to_quaternary(k)) != k:
            bad.append(("quaternary", k))
        if from_octal(to_octal(k)) != k:
            bad.append(("octal", k))
        if from_bits(to_bits(k)) != k:
            bad.append(("binary", k))
    return {"keys_checked": KEY_SPACE, "failures": bad,
            "ok": not bad, "identity": RADIX_IDENTITY}


def three_symbols_select_64() -> dict:
    """core/06 Q08/Q09 answered arithmetically."""
    return {"three_quaternary_symbols_span": 4 ** 3,
            "six_quaternary_symbols_span": 4 ** 6,
            "equals_64": 4 ** 3 == 64,
            "equals_4096": 4 ** 6 == 4096,
            "note": "selection, not compression: 3 symbols carry "
                    "exactly 6 bits and 6 symbols exactly 12 bits"}


# --- quaternary symbol ontology (A12) -------------------------------------

#: Legal declared bases for naming quaternary symbols physically.
DECLARED_BASES = {
    "ABSTRACT": ("Q0", "Q1", "Q2", "Q3"),
    "SPIN_THREE_HALVES_MS": ("m_s=-3/2", "m_s=-1/2", "m_s=+1/2",
                             "m_s=+3/2"),
    "TWO_SPIN_PRODUCT": ("|00>", "|01>", "|10>", "|11>"),
    "TETRAHEDRAL_DIRECTIONS": ("n0", "n1", "n2", "n3"),
    "FOUR_CLASSICAL_DOMAINS": ("D0", "D1", "D2", "D3"),
}


@dataclass(frozen=True)
class SymbolAlphabet:
    """Four logical symbols with an explicitly declared basis.

    ``basis="ABSTRACT"`` is always safe. Any physical naming requires a
    basis that actually defines the states; direction words without one
    are refused (core/06 Q03/Q04).
    """
    basis: str = "ABSTRACT"

    def __post_init__(self):
        if self.basis not in DECLARED_BASES:
            raise ClaimBoundaryError(
                f"undeclared basis {self.basis!r}; legal: "
                f"{list(DECLARED_BASES)}")

    @property
    def labels(self) -> tuple:
        return DECLARED_BASES[self.basis]

    @property
    def orthogonal(self) -> bool:
        """Only some bases give four ORTHOGONAL states."""
        return self.basis in ("SPIN_THREE_HALVES_MS", "TWO_SPIN_PRODUCT",
                              "FOUR_CLASSICAL_DOMAINS", "ABSTRACT")


def name_directions(basis: str) -> tuple:
    """Refuse up/down/left/right talk unless a basis defines it."""
    if basis == "ABSTRACT":
        raise ClaimBoundaryError(
            "direction names require a declared physical basis; "
            "abstract Q0-Q3 have no spatial meaning (core/06 Q03)")
    a = SymbolAlphabet(basis)
    if basis == "TETRAHEDRAL_DIRECTIONS" and a.orthogonal:
        raise ClaimBoundaryError("internal inconsistency")
    return a.labels


# --- address / payload separation (A13) ------------------------------------

@dataclass(frozen=True)
class Address:
    """Hierarchical tetrahedral address. Stored digitally and exactly —
    never entrusted to a physical spin state."""
    key: int
    depth: int
    storage: str = "DIGITAL_EXACT"

    def __post_init__(self):
        if not (0 <= self.key < 8 ** self.depth):
            raise ClaimBoundaryError(
                f"address key {self.key} outside depth-{self.depth} "
                "range")
        if self.storage != "DIGITAL_EXACT":
            raise ClaimBoundaryError(
                "the address is stored DIGITALLY and EXACTLY so "
                "physical drift cannot corrupt the index (core/06)")


@dataclass(frozen=True)
class Payload:
    """The local content. This — not the address — is the candidate for
    quaternary/physical storage."""
    values: tuple
    kind: str = "SCALAR"
    storage: str = "QUATERNARY_OR_PHYSICAL"


@dataclass(frozen=True)
class Codeword:
    """C = (A, P, Phi, t, Sigma, E) with all six kept separate."""
    address: Address
    payload: Payload
    phase_rad: float = 0.0
    epoch: str = ""
    uncertainty: float = 0.0
    reconstruction_error: float = 0.0

    def to_dict(self) -> dict:
        return {"address_key": self.address.key,
                "address_depth": self.address.depth,
                "address_storage": self.address.storage,
                "payload_kind": self.payload.kind,
                "payload_len": len(self.payload.values),
                "payload_storage": self.payload.storage,
                "phase_rad": self.phase_rad, "epoch": self.epoch,
                "uncertainty": self.uncertainty,
                "reconstruction_error": self.reconstruction_error,
                "separation": "address is digital-exact; payload is the "
                              "physical/quaternary candidate"}


def refuse_address_in_spin(address: Address) -> None:
    """Explicit refusal for the tempting architecture."""
    raise ClaimBoundaryError(
        "storing the hierarchical ADDRESS in a physical spin state is "
        "refused: spin drift/relaxation would corrupt the index "
        "itself, making every payload unrecoverable. Store the address "
        "digitally; put the payload codeword in the physical state "
        "(core/06).")
