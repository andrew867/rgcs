"""R10.12 Phases 07+10 — canonical E3 parser + typed wire certificate.

The canonical parser IS :mod:`r1011.e3_frame` (frozen, verified);
this module wraps every decode into the required certificate and never
reparses through the historical monolithic profile.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, asdict, field

from r1011 import e3_frame as e3
from r1012 import PARSER_VERSION, REGISTRY_VERSION
from r1012.evidence import Tier


class WireError(ValueError):
    pass


@dataclass(frozen=True)
class WireCertificate:
    raw_wire: str
    canonical_bits: str
    header_sol_bits: str
    header_terra_bits: str
    e3: int
    states: tuple[int, int, int]
    child_path: tuple[int, ...]
    terminal: int
    depth: int
    evidence_tier: str
    parser_version: str
    registry_version: str
    roundtrip_hash: str
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        d = asdict(self)
        d["states"] = list(self.states)
        d["child_path"] = list(self.child_path)
        d["warnings"] = list(self.warnings)
        return d


def _clean(wire) -> int:
    s = str(wire).strip()
    if not s or not s.isascii() or not s.isdigit():
        raise WireError(
            f"refused: wire {wire!r} is not a plain decimal digit string "
            f"(whitespace/unicode/sign/mutation rejected, never coerced)")
    if s != s.lstrip("0"):
        raise WireError(
            f"refused: leading zeros are not grammar-permitted on the "
            f"decimal wire {wire!r}")
    return int(s)


def certify(wire) -> WireCertificate:
    raw = _clean(wire)
    p = e3.parse(raw)                      # typed refusals propagate
    back = e3.encode(p)
    if back != raw:
        raise WireError(f"round-trip failure on {raw}: got {back}")
    bits = format(p.e3, "03b") \
        + "".join(format(s, "06b") for s in p.states) \
        + "".join(format(c, "03b") for c in p.children)
    warnings = []
    if p.terminal != 3:
        warnings.append(f"terminal {p.terminal} is NOT surface class 3 — "
                        f"kept distinct (5/7/9 never conflated)")
    if p.e3 not in (2, 3, 4, 6):
        warnings.append(f"E3={p.e3} outside observed range {{2,3,4,6}}")
    rt = hashlib.sha256(f"{raw}:{back}:{bits}".encode()).hexdigest()[:16]
    return WireCertificate(
        raw_wire=str(raw),
        canonical_bits="001|110|" + bits + f"|{p.terminal}",
        header_sol_bits="001", header_terra_bits="110",
        e3=p.e3, states=p.states, child_path=p.children,
        terminal=p.terminal, depth=p.depth,
        evidence_tier=Tier.SOURCE_KNOWN.value,   # the FRAME is locked;
        # semantic caveats (terminal class, E3 subdivision) ride in
        # warnings, never silently upgrade or downgrade the parse

        parser_version=PARSER_VERSION, registry_version=REGISTRY_VERSION,
        roundtrip_hash=rt, warnings=tuple(warnings))
