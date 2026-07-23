"""P15 — a memory handshake over the fading crystal, software only.

This module bolts a *handshake* onto the R10.6 fading-memory crystal shift
register (:mod:`r10.crystalmem`). It writes an addressed frame, transports
it through the decaying store, reads it back **destructively** -- reading
consumes the stored value -- and **refreshes** (rewrites) it to persist,
delivering frames in the **order they were written**. It is a piece of
arithmetic and control logic, nothing more: no specimen is written,
driven, or read, and every retention number is derived from supplied model
parameters. ``measured_here: nothing``; ``PHYSICAL_VALIDATION_NOT_CLAIMED``.

Two properties are load-bearing, and both are inherited from crystalmem's
lesson rather than invented here.

**A fading memory that is read destructively must be refreshed.** A
genuine memory cell gives up its contents *when read*: the read collapses
the stored amplitude to zero, so the value is gone unless a refresh
rewrites it. This is the difference between a register cell and a passive
echo -- an echo you can sample twice and get the same reading, because
nothing was consumed. Here :func:`destructive_read` consumes the cell and
:func:`refuse_reread_without_refresh` makes the second read fail until a
:func:`refresh` puts the value back. A store whose reads do not consume,
or that persists without a rewrite, is a ringdown, not a memory.

**Ordered readout is the ONLY thing that separates a memory from ordinary
relaxation.** The store decays: hold a frame past its retention window and
it fades below the read threshold and is unreadable, exactly as an
acoustic ringdown, a thermal relaxation, or a trapped-charge decay would.
The decay curve therefore carries *zero* bits about whether anything was
stored -- with equal time constants the memory envelope and a passive
relaxation envelope are point-for-point identical. What a passive
relaxation cannot do is return a written pattern *in the correct order*
after a controlled delay. So ordered delayed readout is the whole claim.
:func:`refuse_memory_claim_without_ordered_readout` enforces this: you may
not call a decaying response a memory from its decay curve alone.

The retention arithmetic is not re-implemented; it is reused verbatim from
:mod:`r10.crystalmem` (its ``tau``/threshold decay, its destructive read,
and its refresh), so the two modules cannot drift apart.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

from r10 import crystalmem as cm

# --- claim discipline -------------------------------------------------

#: The whole module is derived arithmetic. Nothing is measured, so the
#: best it can carry is a software-only verdict.
EVIDENCE_CLASS = "DERIVED_MATHEMATICS"
MEASURED_HERE = "nothing"
VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: Default verdict: the handshake is a piece of software, not a memory
#: observed on any specimen.
VERDICT = "MEMORY_HANDSHAKE_SOFTWARE_ONLY"

#: Reused from crystalmem so the two modules share one read floor.
READ_THRESHOLD = cm.READ_THRESHOLD
DEFAULT_A0 = cm.DEFAULT_A0


class MemHandshakeError(RuntimeError):
    """Raised when the handshake's memory discipline is broken.

    Covers the three ways a fading store stops being a memory: a re-read
    of a consumed cell without a refresh, a frame routed to the wrong
    address, and a memory claim asserted without ordered delayed readout.
    """


# --- 1. the addressed frame -------------------------------------------

def frame_checksum(payload) -> int:
    """A position-weighted checksum over a bit payload.

    ``sum((i + 1) * bit)``. Position-weighting is deliberate: it changes
    when the payload is reordered, so a scrambled payload fails
    :func:`verify_checksum`. Bits only; anything else is refused.
    """
    bits = [int(b) for b in payload]
    if any(b not in (0, 1) for b in bits):
        raise ValueError("payload must be bits (0/1)")
    return sum((i + 1) * b for i, b in enumerate(bits))


@dataclass(frozen=True)
class MemoryFrame:
    """One addressed frame written to the store. Immutable.

    The ``payload`` is a tuple of bits; ``checksum`` must match the
    payload (enforced in ``__post_init__``) so a corrupted frame cannot
    masquerade as a clean one.
    """

    address: int
    payload: tuple[int, ...]
    write_time: float
    checksum: int

    def __post_init__(self) -> None:
        if not isinstance(self.address, int) or self.address < 0:
            raise ValueError("address must be a non-negative integer")
        if any(b not in (0, 1) for b in self.payload):
            raise ValueError("payload must be bits (0/1)")
        if self.write_time < 0:
            raise ValueError("write_time cannot be negative")
        if self.checksum != frame_checksum(self.payload):
            raise ValueError("checksum does not match payload")


def make_frame(address: int, payload, write_time: float = 0.0) -> MemoryFrame:
    """Build a frame, computing the checksum from the payload."""
    bits = tuple(int(b) for b in payload)
    return MemoryFrame(address, bits, write_time, frame_checksum(bits))


def verify_checksum(frame: MemoryFrame) -> bool:
    """True iff the frame's checksum still matches its payload."""
    return frame.checksum == frame_checksum(frame.payload)


# --- 2. the cell: a frame riding crystalmem's retention envelope ------

@dataclass(frozen=True)
class MemoryCell:
    """One addressed cell.

    The ``bit`` is a :class:`crystalmem.StoredBit` used as the frame's
    *retention envelope* -- it tracks presence/amplitude and decays by
    crystalmem's own math -- while the frame carries the actual payload.
    ``consumed`` records that a destructive read has emptied the cell and
    a refresh is required before it can be read again.
    """

    address: int
    frame: MemoryFrame | None = None
    bit: cm.StoredBit | None = None
    consumed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.address, int) or self.address < 0:
            raise ValueError("address must be a non-negative integer")
        if self.frame is not None and self.frame.address != self.address:
            raise ValueError("frame address does not match cell address")


def is_readable(frame: MemoryFrame, elapsed: float, tau: float,
                threshold: Fraction = READ_THRESHOLD) -> bool:
    """Is a frame written at ``t=0`` still readable after ``elapsed``?

    Delegates to :func:`crystalmem.recoverable`: the frame's retention
    envelope must stay strictly above the read threshold. Past the
    retention window it has faded below threshold and is unreadable --
    the same decay that makes the store indistinguishable from ordinary
    relaxation until an ordered readout is shown.
    """
    if frame is None:
        raise ValueError("no frame to test")
    return cm.recoverable(elapsed, tau, DEFAULT_A0, threshold)


def age_cell(cell: MemoryCell, tau: float, dt: float) -> MemoryCell:
    """Advance a written cell's retention envelope by ``dt`` seconds."""
    if cell.bit is None:
        raise MemHandshakeError("cannot age an empty cell")
    return MemoryCell(cell.address, cell.frame,
                      cm.age_bit(cell.bit, tau, dt), cell.consumed)


# --- 3. destructive read, the refresh it forces, and re-read refusal --

def refuse_reread_without_refresh(cell: MemoryCell) -> None:
    """Refuse to re-read a consumed cell until it has been refreshed.

    A destructive read leaves the cell empty; reading it again would
    return data that is no longer there. This is the guard that makes the
    read genuinely destructive rather than a repeatable sample of an
    ongoing echo.
    """
    if cell.consumed:
        raise MemHandshakeError(
            f"cell at address {cell.address} was consumed by a destructive "
            f"read and has not been refreshed; its stored value is gone. A "
            f"memory cell gives up its contents when read -- reading again "
            f"without a refresh would report data that is no longer there. "
            f"Call refresh() to rewrite the value first. A store that lets "
            f"you re-read a consumed cell is a passive echo, not a memory.")


def destructive_read(cell: MemoryCell,
                     threshold: Fraction = READ_THRESHOLD
                     ) -> tuple[MemoryFrame | None, MemoryCell]:
    """Read a cell, consuming its stored value.

    Returns ``(frame, consumed_cell)``. The frame is returned only if the
    retention envelope is still above threshold; either way the cell is
    left consumed (envelope driven to zero) and must be refreshed to be
    read again. Re-reading a consumed cell raises via
    :func:`refuse_reread_without_refresh`.
    """
    refuse_reread_without_refresh(cell)
    if cell.frame is None or cell.bit is None:
        return None, MemoryCell(cell.address, cell.frame, cell.bit,
                                consumed=True)
    result = cm.destructive_read(cell.bit, threshold)
    consumed = MemoryCell(cell.address, cell.frame, result.residual,
                          consumed=True)
    frame = cell.frame if result.recovered else None
    return frame, consumed


def refresh(cell: MemoryCell, a0: float = DEFAULT_A0) -> MemoryCell:
    """Rewrite a cell's frame at full amplitude (the refresh cycle).

    Restores the retention envelope and clears the consumed flag, so the
    frame can be read again. An empty cell has nothing to refresh.
    """
    if cell.frame is None:
        raise MemHandshakeError("cannot refresh an empty cell; nothing was "
                                "written to address "
                                f"{cell.address}")
    bit = cell.bit if cell.bit is not None else cm.write_bit(1, a0)
    return MemoryCell(cell.address, cell.frame, cm.refresh(bit, a0),
                      consumed=False)


# --- 4. the addressed store and ordered readout -----------------------

@dataclass(frozen=True)
class MemoryStore:
    """An addressed store with an append-only write-order log.

    ``cells`` maps address -> :class:`MemoryCell`; ``write_order`` records
    the addresses in the exact order they were written, which is what an
    ordered readout must reproduce.
    """

    cells: dict = field(default_factory=dict)
    write_order: tuple[int, ...] = ()


def new_store(addresses) -> MemoryStore:
    """A fresh store with empty cells at each of ``addresses``."""
    addrs = [int(a) for a in addresses]
    if len(set(addrs)) != len(addrs):
        raise ValueError("addresses must be unique")
    cells = {a: MemoryCell(a) for a in addrs}
    return MemoryStore(cells, ())


def write(store: MemoryStore, frame: MemoryFrame,
          a0: float = DEFAULT_A0) -> MemoryStore:
    """Route a frame to its addressed cell and log the write order.

    A frame whose address has no cell is refused -- addressed framing
    means the address routes the frame to the right cell, and a wrong
    address is an error, not a silent drop.
    """
    if frame.address not in store.cells:
        raise MemHandshakeError(
            f"no cell at address {frame.address}; the frame is misaddressed. "
            f"Known addresses: {sorted(store.cells)}")
    if not verify_checksum(frame):
        raise MemHandshakeError(
            f"frame at address {frame.address} failed its checksum")
    cells = dict(store.cells)
    cells[frame.address] = MemoryCell(frame.address, frame,
                                      cm.write_bit(1, a0), consumed=False)
    return MemoryStore(cells, store.write_order + (frame.address,))


def ordered_read(store: MemoryStore,
                 threshold: Fraction = READ_THRESHOLD) -> tuple[MemoryFrame, ...]:
    """Read every written cell back in the order it was written.

    Follows ``write_order`` so the frames come back in write order. This
    is the observable that a passive relaxation cannot reproduce: a
    decaying envelope carries no order. Unreadable (faded) cells are
    skipped rather than fabricated.
    """
    frames: list[MemoryFrame] = []
    for addr in store.write_order:
        cell = store.cells[addr]
        frame, _ = destructive_read(cell, threshold)
        if frame is not None:
            frames.append(frame)
    return tuple(frames)


def verify_write_order(readout, expected_order) -> bool:
    """True iff the readout's addresses equal the expected write order.

    The falsifiable core of the ordered-readout claim: a shuffled store
    produces a readout whose address sequence no longer matches the write
    order, and this returns False.
    """
    return tuple(f.address for f in readout) == tuple(expected_order)


def ordered_readout_demonstrates_memory(readout, expected_order) -> bool:
    """Ordered readout is what turns a decay curve into a memory claim.

    Returns True only when the readout is non-empty *and* reproduces the
    exact write order. An empty readout (everything faded) or a scrambled
    one does not demonstrate a memory.
    """
    return bool(list(readout)) and verify_write_order(readout, expected_order)


def refuse_memory_claim_without_ordered_readout() -> None:
    """Refuse to call a decaying store a memory. This is the firewall.

    Reuses crystalmem's lesson: a store that decays and disperses is
    exactly what ordinary material relaxation looks like, so the decay
    curve alone settles nothing. A memory claim requires the written
    frames to return in the correct order after a controlled delay.
    """
    raise MemHandshakeError(
        "no memory claim is available from a decay curve. A store that "
        "fades is presumed ordinary material relaxation -- acoustic "
        "ringdown, thermal relaxation, trapped-charge decay -- until an "
        "ordered delayed readout is demonstrated. With equal time constants "
        "the memory envelope and the relaxation envelope are point-for-point "
        "identical and carry zero bits about whether anything was stored. "
        "The claim requires the written frames to return in the correct "
        "order after a controlled delay, distinguishable from an envelope "
        "that carries no order, and to survive a destructive read followed "
        "by a refresh. No specimen has been written, driven, or read; "
        "nothing here is measured.")


# --- 5. the report ----------------------------------------------------

def memhandshake_report() -> dict:
    """One summary of what the handshake computes and, loudly, disclaims."""
    return {
        "evidence_class": EVIDENCE_CLASS,
        "measured_here": MEASURED_HERE,
        "physical_validation": VALIDATION,
        "verdict": VERDICT,
        "reuses": "r10.crystalmem retention/decay, destructive read, refresh",
        "what_this_is": (
            "a memory handshake over the fading crystal store: write an "
            "addressed frame, transport it through the decaying register, "
            "read it destructively so the read consumes the value, refresh "
            "to persist, and deliver frames in the order written."),
        "the_firewall": (
            "a fading store is indistinguishable from ordinary relaxation "
            "until ordered delayed readout is demonstrated; the decay curve "
            "alone carries zero bits about whether anything was stored. See "
            "refuse_memory_claim_without_ordered_readout()."),
        "what_this_does_not_say": (
            "it does not say any crystal stores information, that a "
            "retention window has been observed, that any handshake has run "
            "on hardware, or that a frame has been written to or read from a "
            "specimen. Every retention number is derived from supplied model "
            "parameters. Nothing has been measured, and the best this can "
            "carry is a software-only verdict."),
    }


__all__ = [
    "EVIDENCE_CLASS", "MEASURED_HERE", "VALIDATION", "VERDICT",
    "READ_THRESHOLD", "DEFAULT_A0",
    "MemHandshakeError",
    "frame_checksum", "MemoryFrame", "make_frame", "verify_checksum",
    "MemoryCell", "is_readable", "age_cell",
    "refuse_reread_without_refresh", "destructive_read", "refresh",
    "MemoryStore", "new_store", "write", "ordered_read",
    "verify_write_order", "ordered_readout_demonstrates_memory",
    "refuse_memory_claim_without_ordered_readout",
    "memhandshake_report",
]
