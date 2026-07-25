"""P11 — Packed shell-epoch composite and variable-depth wire format.

Locked Decisions 14 and 15: shell and epoch may **share a compressed wire
field**, and packets may **omit unused epoch components** while a full
certificate carries them. This module defines a versioned wire grammar with
three packet depths:

* ``SHELL_ONLY`` — the shell alone (no epoch component);
* ``SHELL_PLUS_COARSE`` — the shell packed with a coarse epoch in one composite
  token;
* ``FULL`` — the shell + coarse composite plus a fine-epoch token.

Every depth serializes to a base-100 token string and back **exactly**
(``decode(encode(p)) == p``). The wire is self-describing: a leading depth tag
removes ambiguity between depths.

Governance rules honoured here:

* **The shell supplies the radius.** :func:`decode` resolves the body-relative
  radius from the shell (P10 ``resolve_shell_radius_m``); a decoded packet never
  reports "altitude missing" when a shell is present.
* **``8 <-> 0`` is an explicit transition flag, not integer equality.** A shell
  of 8 sets ``shell_closure_transition`` (reusing ``cwatlas.shells`` source
  ontology). The closure is stored, never silently applied; shell 8 is not
  treated as equal to shell 0.
* **Ambiguous legacy packets yield a typed alias set.** An untagged legacy
  token string that admits more than one depth interpretation is returned as a
  ``CANDIDATE_ALIAS_SET``, never forced to one packet.

Evidence class ``DERIVED_MATHEMATICS`` / claim class ``MATHEMATICAL_TRANSLATION``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from cwatlas import shells as _shells
from cwatlas.claims import ClaimClass
from cwatlas.codec_base100 import decode_to_path as _b100_decode
from cwatlas.codec_base100 import encode as _b100_encode
from cwatlas.r1082 import claims as _r1082
from cwatlas.r1082.route_core import RouteError
from cwatlas.r1082.semantic_expand import (
    SHELL_MAX, SHELL_MIN, resolve_shell_radius_m,
)

WIRE_VERSION = "CW_WIRE_V1"

#: The shell packs with a coarse epoch as ``coarse * _SHELL_BASE + shell``.
_SHELL_BASE = SHELL_MAX + 1  # 9
COARSE_MIN, COARSE_MAX = 0, 10  # keeps the composite token <= 98 (< 100)
FINE_MIN, FINE_MAX = 0, 99


class PacketDepth(Enum):
    """The three variable-depth wire packets."""

    SHELL_ONLY = "SHELL_ONLY"
    SHELL_PLUS_COARSE = "SHELL_PLUS_COARSE"
    FULL = "FULL"


#: Wire depth tag tokens (token[0]).
_DEPTH_CODE = {
    PacketDepth.SHELL_ONLY: 1,
    PacketDepth.SHELL_PLUS_COARSE: 2,
    PacketDepth.FULL: 3,
}
_CODE_DEPTH = {v: k for k, v in _DEPTH_CODE.items()}


@dataclass(frozen=True)
class Packet:
    """A decoded wire packet at one of the three depths.

    ``coarse_epoch`` is present for ``SHELL_PLUS_COARSE`` and ``FULL``;
    ``fine_epoch`` only for ``FULL``. ``shell_closure_transition`` is an explicit
    flag (shell 8 <-> 0), never integer equality. ``radius_m`` is supplied by
    the shell so altitude is never reported missing.
    """

    depth: PacketDepth
    shell: int
    coarse_epoch: int | None = None
    fine_epoch: int | None = None
    version: str = WIRE_VERSION
    shell_closure_transition: bool = field(default=False, compare=False)
    radius_m: float | None = field(default=None, compare=False)

    def __post_init__(self) -> None:
        if not SHELL_MIN <= self.shell <= SHELL_MAX:
            raise RouteError(
                f"shell {self.shell} out of range [{SHELL_MIN}, {SHELL_MAX}].")
        needs_coarse = self.depth in (PacketDepth.SHELL_PLUS_COARSE,
                                      PacketDepth.FULL)
        if needs_coarse:
            if self.coarse_epoch is None \
                    or not COARSE_MIN <= self.coarse_epoch <= COARSE_MAX:
                raise RouteError(
                    f"{self.depth.value} requires a coarse epoch in "
                    f"[{COARSE_MIN}, {COARSE_MAX}], got {self.coarse_epoch!r}.")
        elif self.coarse_epoch is not None:
            raise RouteError(
                f"{self.depth.value} must omit the coarse epoch "
                f"(variable depth), got {self.coarse_epoch!r}.")
        if self.depth is PacketDepth.FULL:
            if self.fine_epoch is None \
                    or not FINE_MIN <= self.fine_epoch <= FINE_MAX:
                raise RouteError(
                    f"FULL requires a fine epoch in [{FINE_MIN}, {FINE_MAX}], "
                    f"got {self.fine_epoch!r}.")
        elif self.fine_epoch is not None:
            raise RouteError(
                f"{self.depth.value} must omit the fine epoch, got "
                f"{self.fine_epoch!r}.")


def make_packet(depth: PacketDepth, shell: int, *,
                coarse_epoch: int | None = None,
                fine_epoch: int | None = None) -> Packet:
    """Construct a validated packet with the shell-supplied radius and flag."""
    return Packet(
        depth=depth, shell=shell, coarse_epoch=coarse_epoch,
        fine_epoch=fine_epoch,
        shell_closure_transition=(shell == _shells.SHELL_CLOSURE["from_shell"]),
        radius_m=resolve_shell_radius_m(shell),
    )


def _composite(shell: int, coarse: int) -> int:
    return coarse * _SHELL_BASE + shell


def encode(packet: Packet) -> str:
    """Serialize a packet to a base-100 token string (exact, self-describing)."""
    tokens = [_DEPTH_CODE[packet.depth]]
    if packet.depth is PacketDepth.SHELL_ONLY:
        tokens.append(packet.shell)
    elif packet.depth is PacketDepth.SHELL_PLUS_COARSE:
        tokens.append(_composite(packet.shell, packet.coarse_epoch))
    else:  # FULL
        tokens.append(_composite(packet.shell, packet.coarse_epoch))
        tokens.append(packet.fine_epoch)
    return _b100_encode(tokens)


def decode(wire: str) -> Packet:
    """Decode a tagged wire string to an exact packet (inverse of encode)."""
    tokens = _b100_decode(wire)  # refuses malformed base-100
    if len(tokens) < 2:
        raise RouteError(
            f"wire packet needs at least a depth tag and one field, got "
            f"{len(tokens)} tokens.")
    code = tokens[0]
    if code not in _CODE_DEPTH:
        raise RouteError(
            f"unknown wire depth code {code}; expected one of "
            f"{sorted(_CODE_DEPTH)}.")
    depth = _CODE_DEPTH[code]
    if depth is PacketDepth.SHELL_ONLY:
        if len(tokens) != 2:
            raise RouteError("SHELL_ONLY packet must have exactly 2 tokens.")
        return make_packet(depth, tokens[1])
    if depth is PacketDepth.SHELL_PLUS_COARSE:
        if len(tokens) != 2:
            raise RouteError(
                "SHELL_PLUS_COARSE packet must have exactly 2 tokens.")
        shell = tokens[1] % _SHELL_BASE
        coarse = tokens[1] // _SHELL_BASE
        return make_packet(depth, shell, coarse_epoch=coarse)
    # FULL
    if len(tokens) != 3:
        raise RouteError("FULL packet must have exactly 3 tokens.")
    shell = tokens[1] % _SHELL_BASE
    coarse = tokens[1] // _SHELL_BASE
    return make_packet(depth, shell, coarse_epoch=coarse, fine_epoch=tokens[2])


# -- legacy (untagged) decode: ambiguity becomes a typed alias set ----------

@dataclass(frozen=True)
class LegacyDecodeResult:
    """A typed result for an untagged legacy token string.

    ``status`` is one of the locked result classes: ``CANONICAL_EXACT_POINT``
    (single admissible interpretation), ``CANDIDATE_ALIAS_SET`` (more than one),
    or ``INVALID`` (none). ``candidates`` are the admissible packets; the wire
    is never forced to one packet when ambiguous.
    """

    status: str
    candidates: tuple[Packet, ...]

    def alias_set(self) -> tuple[dict, ...]:
        return tuple(
            {"depth": p.depth.value, "shell": p.shell,
             "coarse_epoch": p.coarse_epoch, "fine_epoch": p.fine_epoch}
            for p in self.candidates)


def decode_legacy(wire: str) -> LegacyDecodeResult:
    """Interpret an **untagged** legacy token string across all depths.

    Enumerates every depth whose token count and field ranges the string admits.
    One admissible interpretation -> ``CANONICAL_EXACT_POINT``; more than one ->
    ``CANDIDATE_ALIAS_SET`` (ambiguity is surfaced, not resolved by fiat); none
    -> ``INVALID``.
    """
    tokens = _b100_decode(wire)
    candidates: list[Packet] = []
    n = len(tokens)
    if n == 1:
        v = tokens[0]
        if SHELL_MIN <= v <= SHELL_MAX:
            candidates.append(make_packet(PacketDepth.SHELL_ONLY, v))
        shell, coarse = v % _SHELL_BASE, v // _SHELL_BASE
        if COARSE_MIN <= coarse <= COARSE_MAX:
            candidates.append(make_packet(
                PacketDepth.SHELL_PLUS_COARSE, shell, coarse_epoch=coarse))
    elif n == 2:
        shell, coarse = tokens[0] % _SHELL_BASE, tokens[0] // _SHELL_BASE
        if COARSE_MIN <= coarse <= COARSE_MAX \
                and FINE_MIN <= tokens[1] <= FINE_MAX:
            candidates.append(make_packet(
                PacketDepth.FULL, shell, coarse_epoch=coarse,
                fine_epoch=tokens[1]))
    if not candidates:
        return LegacyDecodeResult(
            _r1082.ResultClass.INVALID.value, ())
    if len(candidates) == 1:
        return LegacyDecodeResult(
            _r1082.ResultClass.CANONICAL_EXACT_POINT.value, tuple(candidates))
    return LegacyDecodeResult(
        _r1082.ResultClass.CANDIDATE_ALIAS_SET.value, tuple(candidates))


def to_shell_epoch(packet: Packet, conventional_epoch: dict) -> dict:
    """Build a ``shell_epoch`` object (schema-conforming) for a packet.

    The conventional UTC/TAI/TT/TDB timestamp is mandatory. The shell supplies
    the radius; a compressed epoch is present only when the packet carries one.
    """
    if not conventional_epoch or "timescale" not in conventional_epoch \
            or "value" not in conventional_epoch:
        raise RouteError(
            "a conventional_epoch (timescale + value) is mandatory even when a "
            "compressed source epoch is used.")
    out: dict = {
        "shell": {
            "index": packet.shell,
            "profile_id": f"EARTH_SHELL_R_V1:{packet.shell}",
            "radius_m": resolve_shell_radius_m(packet.shell),
            "altitude_m": None,
            "effective_potential": None,
        },
        "conventional_epoch": dict(conventional_epoch),
    }
    if packet.depth is PacketDepth.SHELL_ONLY:
        out["compressed_epoch"] = None
    else:
        payload = {"coarse": packet.coarse_epoch}
        if packet.fine_epoch is not None:
            payload["fine"] = packet.fine_epoch
        out["compressed_epoch"] = {
            "profile": "COMPOSITE_VARIABLE_DEPTH",
            "payload": payload,
        }
    return out


def wire_format_report() -> dict:
    """P11 declaration receipt. Reversible wire grammar; nothing measured."""
    return {
        "phase_id": "P11",
        "tranche": "T03",
        "what_this_is": (
            "a versioned variable-depth wire grammar (SHELL_ONLY, "
            "SHELL_PLUS_COARSE, FULL) with a packed shell+epoch composite "
            "token; exact encode/decode round-trip at every depth; the shell "
            "supplies the radius; 8<->0 is an explicit transition flag; "
            "ambiguous legacy packets return a typed alias set."),
        "wire_version": WIRE_VERSION,
        "packet_depths": [d.value for d in PacketDepth],
        "shell_supplies_radius": True,
        "eight_zero_transition_is_flag_not_equality": True,
        "evidence_class": _r1082.EvidenceClass.DERIVED_MATHEMATICS.value,
        "claim_class": ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": ("GREEN_R10_8_2_P11_PACKED_SHELL-EPOCH_AND_"
                    "VARIABLE-DEPTH_WIRE_FORMAT"),
        "what_this_does_not_say": (
            "The wire grammar is a reversible codec; a decoded packet is not a "
            "measured altitude or a proven epoch, and the 8<->0 closure is "
            "stored ontology, never silently applied."),
    }
