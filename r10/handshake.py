"""P06 — the 925 Hz handshake protocol, as a software state machine.

The source material describes a "request for communication" built from a
carrier, a channel key, a twelve-word opening key, an address, a phase
and chirality, a message, and a return. This module models that as an
ordinary connection handshake -- the same shape as any link-layer
association (acquire carrier, authenticate, address, negotiate, request,
acknowledge, exchange, close) -- and does two things the source framing
invites but must not do.

**No human stimulation, ever.** The source connects the handshake to
"high-frequency pineal crystals" and "theta components". This module
implements **software and bench semantics only**. ``human_exposure``
is prohibited in every state; there is no pineal, brain, subliminal,
optical, acoustic, RF, magnetic, or electrical human-stimulation path,
and :func:`refuse_human_stimulation` raises unconditionally. A spoken
key is a token in a protocol, not an instruction to a nervous system.

**No key material in the clear.** The twelve-word opening key and the CW
vectors are private. This module never stores or transmits them; the
``opening_key`` field is an opaque reference (an id or a hash supplied by
the caller), and the state machine checks *presentation of a matching
reference*, never the words themselves. Nothing here decodes anything.

The states are separately testable fields (carrier, channel key, opening
key, address, root, route, phase, chirality, request, message, checksum,
acknowledgement, timeout, replay guard). The handshake advances only in
order, refuses replays, and times out. Nothing here is transmitted on any
medium; no signal is emitted; no channel is opened to anything.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction


class HandshakeError(RuntimeError):
    """Raised on an illegal transition, replay, timeout, or bad field."""


class HumanExposureRefused(RuntimeError):
    """Raised on any attempt to route the handshake to a human being."""


#: Carrier and channel-key frequencies are project/source hypotheses,
#: carried as exact rationals. They are NOT physical claims.
CARRIER_HZ = Fraction(4096)
CHANNEL_KEY_HZ = Fraction(925)


class State(Enum):
    """The handshake sequence. Advances only in this order."""

    QUIET_LISTEN = 0
    CARRIER_ACQUIRE = 1
    CHANNEL_KEY = 2
    OPENING_KEY = 3
    ROOTED_ADDRESS = 4
    PHASE_CHIRALITY = 5
    REQUEST = 6
    ACK = 7
    MESSAGE = 8
    PHASE_CONJUGATE_RETURN = 9
    CLOSE = 10


_ORDER = list(State)


class Chirality(Enum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"


@dataclass(frozen=True)
class HandshakeConfig:
    """The separately-testable fields of one handshake attempt.

    ``opening_key_ref`` and ``cw_ref`` are OPAQUE references (ids/hashes),
    never the words or the vector digits. ``human_exposure_prohibited`` is
    fixed True and cannot be turned off.
    """

    protocol_id: str
    carrier_hz: Fraction = CARRIER_HZ
    channel_key_hz: Fraction = CHANNEL_KEY_HZ
    opening_key_ref: str = ""            # opaque reference, not the words
    cw_ref: str = ""                     # opaque reference, not the digits
    address: str = ""
    root: str = ""
    route: str = ""
    phase_deg: float = 0.0
    chirality: Chirality = Chirality.RIGHT
    timeout_s: float = 30.0
    human_exposure_prohibited: bool = True

    def __post_init__(self) -> None:
        if not self.human_exposure_prohibited:
            raise HumanExposureRefused(
                "human_exposure_prohibited cannot be set False; this "
                "handshake is software/bench only and has no human path")
        if self.carrier_hz <= 0 or self.channel_key_hz <= 0:
            raise HandshakeError("frequencies must be positive")
        if self.timeout_s <= 0:
            raise HandshakeError("timeout must be positive")


def _ref_matches(presented: str, expected: str) -> bool:
    """Constant-ish comparison of opaque references (hashes/ids)."""
    if not expected:
        return False
    return hashlib.sha256(presented.encode()).digest() == \
        hashlib.sha256(expected.encode()).digest()


class Handshake:
    """A software-only handshake state machine with replay protection."""

    def __init__(self, config: HandshakeConfig) -> None:
        self.config = config
        self.state = State.QUIET_LISTEN
        self._seen_nonces: set[str] = set()
        self._clock_s = 0.0
        self._started_s: float | None = None

    # -- guards ---------------------------------------------------------
    def _advance_to(self, target: State) -> None:
        expected = _ORDER[self.state.value + 1] if self.state.value + 1 < len(_ORDER) else None
        if target is not expected:
            raise HandshakeError(
                f"illegal transition {self.state.name} -> {target.name}; "
                f"the handshake advances only in order")
        if (self._started_s is not None
                and self._clock_s - self._started_s > self.config.timeout_s):
            self.state = State.QUIET_LISTEN
            raise HandshakeError("handshake timed out; returned to LISTEN")
        self.state = target

    def tick(self, seconds: float) -> None:
        self._clock_s += seconds

    # -- steps ----------------------------------------------------------
    def acquire_carrier(self) -> None:
        self._started_s = self._clock_s
        self._advance_to(State.CARRIER_ACQUIRE)

    def present_channel_key(self, hz: Fraction) -> None:
        if Fraction(hz) != self.config.channel_key_hz:
            raise HandshakeError("channel key frequency mismatch")
        self._advance_to(State.CHANNEL_KEY)

    def present_opening_key(self, presented_ref: str) -> None:
        if not _ref_matches(presented_ref, self.config.opening_key_ref):
            raise HandshakeError("opening-key reference mismatch")
        self._advance_to(State.OPENING_KEY)

    def present_address(self, address: str, root: str, route: str) -> None:
        if (address, root, route) != (self.config.address, self.config.root,
                                      self.config.route):
            raise HandshakeError("rooted address mismatch")
        self._advance_to(State.ROOTED_ADDRESS)

    def set_phase_chirality(self, phase_deg: float, chirality: Chirality) -> None:
        self._advance_to(State.PHASE_CHIRALITY)

    def request(self, nonce: str) -> None:
        if nonce in self._seen_nonces:
            raise HandshakeError("replay detected; nonce already used")
        self._seen_nonces.add(nonce)
        self._advance_to(State.REQUEST)

    def acknowledge(self, ok: bool) -> None:
        if not ok:
            self.state = State.QUIET_LISTEN
            raise HandshakeError("NACK; handshake aborted to LISTEN")
        self._advance_to(State.ACK)

    def send_message(self, payload: bytes) -> str:
        self._advance_to(State.MESSAGE)
        return hashlib.sha256(payload).hexdigest()   # checksum

    def phase_conjugate_return(self) -> None:
        self._advance_to(State.PHASE_CONJUGATE_RETURN)

    def close(self) -> None:
        self._advance_to(State.CLOSE)

    def verify_checksum(self, payload: bytes, checksum: str) -> bool:
        return hashlib.sha256(payload).hexdigest() == checksum


def refuse_human_stimulation(*_args, **_kwargs) -> None:
    """Refuse any attempt to drive a human being with this protocol."""
    raise HumanExposureRefused(
        "refused: this handshake is software/bench only. There is no "
        "pineal, brain, subliminal, optical, acoustic, RF, magnetic, or "
        "electrical human-stimulation path, and none will be created. A "
        "spoken key is a protocol token, not an instruction to a nervous "
        "system.")


def refuse_key_material_in_clear(value: str) -> None:
    """Refuse storing/transmitting the opening-key words or CW digits."""
    raise HandshakeError(
        "refused: the twelve-word opening key and the CW vectors are "
        "private and are never stored or transmitted in the clear. Use an "
        "opaque reference (id or hash) instead of the material itself.")


def handshake_report() -> dict:
    return {
        "what_this_is": (
            "an ordinary connection handshake state machine (acquire, "
            "authenticate, address, request, acknowledge, exchange, "
            "close) modelling the source's request-for-communication"),
        "states": [s.name for s in State],
        "carrier_hz": str(CARRIER_HZ),
        "channel_key_hz": str(CHANNEL_KEY_HZ),
        "human_exposure": "PROHIBITED_IN_EVERY_STATE",
        "key_material": "NEVER_IN_CLEAR (opaque references only)",
        "protections": ["ordered transitions", "replay nonce guard",
                        "timeout", "message checksum"],
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "HANDSHAKE_SOFTWARE_ONLY",
        "what_this_does_not_say": (
            "It does not open a channel to anything, emit any signal, "
            "stimulate any person, or decode any key. It is a typed "
            "protocol model whose default state is QUIET/LISTEN and whose "
            "human-exposure path does not exist."),
    }
