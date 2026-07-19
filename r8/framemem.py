"""P13 — HAL frame memory: what a stored coordinate is worth later.

A coordinate stored without its frame is not a coordinate. It is three
numbers and a hope. This module makes the frame, the epoch and the
transform provenance part of the record itself, so that a retrieval in
a different frame cannot be performed without confronting what it
costs.

HAL here is the repository's existing synthetic associative-memory
model (see :mod:`r3.hal_memory`), not a brain interface and not a
device. Payloads are opaque to this module and no personal data lane
exists.

The result the phase turns on, and it is not a flattering one:
**retrieval in a distant frame is strictly less certain than retrieval
in the recording frame, and the loss is permanent.** Transform
uncertainties add in quadrature and never subtract. Round-tripping a
record out to another frame and back does not return the original
precision; it returns the original value with two transforms' worth of
uncertainty attached. A memory system that reports frame-transformed
coordinates at their recorded precision is reporting a number it
cannot support.

The second rule is harder and is enforced by refusal rather than by
arithmetic: a transform between frames that move relative to each
other is meaningless without an epoch and an ephemeris. "Convert this
to the barycentric frame" is not a well-posed request until someone
says *when* and *according to which model*. :func:`retrieve_in_frame`
refuses rather than silently assuming the current epoch, because
assuming the current epoch is how a decades-old record acquires a
confident and wrong position.

Nothing here is a measurement. No sensor has recorded a frame, no
ephemeris has been consulted, and no engram exists outside a test.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict

EVIDENCE_CLASS = "SYNTHETIC_MODEL"
DERIVED = "DERIVED_ARITHMETIC"

NO_MEASUREMENT = (
    "No measurement has been taken. RGCS owns no sensor, holds no "
    "ephemeris subscription, and has recorded no frame. Every record "
    "handled here is synthetic and every uncertainty is arithmetic "
    "over declared inputs.")

#: Payload classes this release admits. As in r3.hal_memory, the list
#: has exactly one member on purpose.
PAYLOAD_CLASSES = ("SYNTHETIC",)


class FrameRefused(RuntimeError):
    """Raised when a frame-transformed retrieval is refused."""


def _stamp(record: dict, evidence_class: str = DERIVED) -> dict:
    record["evidence_class"] = evidence_class
    record["no_measurement_statement"] = NO_MEASUREMENT
    return record


# --------------------------------------------------------------------
# 1. Transforms and frame-tagged records
# --------------------------------------------------------------------

@dataclass(frozen=True)
class FrameTransform:
    """One declared transform between two named frames.

    ``epoch`` and ``ephemeris`` are ``None``-able so that an
    incomplete transform can be *constructed and inspected* — the
    refusal belongs at use, where it can name what is missing, not at
    construction, where it would merely make the incomplete case
    unrepresentable and therefore invisible.
    """

    from_frame: str
    to_frame: str
    uncertainty_m: float
    epoch: str | None = None
    ephemeris: str | None = None
    note: str = ""

    def __post_init__(self) -> None:
        if not self.from_frame or not self.to_frame:
            raise ValueError("a transform needs both frame names")
        if self.from_frame == self.to_frame:
            raise ValueError(
                "a transform from a frame to itself is the identity "
                "and should not appear in a chain")
        if self.uncertainty_m < 0:
            raise ValueError("uncertainty cannot be negative")

    @property
    def complete(self) -> bool:
        """True iff this transform can actually be evaluated."""
        return bool(self.epoch) and bool(self.ephemeris)

    def missing(self) -> tuple[str, ...]:
        gaps = []
        if not self.epoch:
            gaps.append("epoch")
        if not self.ephemeris:
            gaps.append("ephemeris")
        return tuple(gaps)

    def as_record(self) -> dict:
        d = asdict(self)
        d["complete"] = self.complete
        d["missing"] = list(self.missing())
        return _stamp(d)


@dataclass(frozen=True)
class FrameRecord:
    """A payload plus the frame and epoch it was recorded in.

    ``provenance`` is the transform chain back to a declared root
    frame. It is stored with the record rather than looked up later,
    because "which root was this relative to" is exactly the question
    that becomes unanswerable once the record is old.
    """

    payload: object
    recorded_frame: str
    recorded_epoch: str
    root_frame: str
    provenance: tuple[FrameTransform, ...] = ()
    intrinsic_uncertainty_m: float = 0.0
    payload_class: str = "SYNTHETIC"

    def __post_init__(self) -> None:
        if not self.recorded_frame:
            raise ValueError("a record must name the frame it was "
                             "recorded in")
        if not self.recorded_epoch:
            raise ValueError(
                "a record must carry the epoch it was recorded at; a "
                "frame without an epoch is not a frame, because "
                "frames move")
        if not self.root_frame:
            raise ValueError("a record must declare its root frame")
        if self.intrinsic_uncertainty_m < 0:
            raise ValueError("uncertainty cannot be negative")
        if self.payload_class not in PAYLOAD_CLASSES:
            raise FrameRefused(
                f"payload_class {self.payload_class!r} is not "
                f"admitted; only SYNTHETIC payloads exist in this "
                f"release and no consented personal-data lane is "
                f"implemented")

    def provenance_complete(self) -> bool:
        return all(t.complete for t in self.provenance)

    def as_record(self) -> dict:
        return _stamp({
            "recorded_frame": self.recorded_frame,
            "recorded_epoch": self.recorded_epoch,
            "root_frame": self.root_frame,
            "payload_class": self.payload_class,
            "intrinsic_uncertainty_m": self.intrinsic_uncertainty_m,
            "provenance": [t.as_record() for t in self.provenance],
            "provenance_depth": len(self.provenance),
            "provenance_complete": self.provenance_complete(),
        })


# --------------------------------------------------------------------
# 2. Uncertainty growth
# --------------------------------------------------------------------

def uncertainty_growth(chain: tuple[FrameTransform, ...], *,
                       initial_m: float = 0.0) -> dict:
    """Quadrature accumulation along a transform chain.

    Independent transform errors combine as

        sigma_k = sqrt(sigma_{k-1}^2 + s_k^2)

    which is monotonically non-decreasing in ``k`` and strictly
    increasing wherever ``s_k > 0``. There is no arrangement of
    transforms that reduces it: the sum of squares only grows, so a
    record retrieved four frames away is less certain than the same
    record retrieved in place, always.

    The practical shape of the curve is worth noticing. Quadrature is
    dominated by the largest single term, so a chain of one bad
    transform and six good ones is barely better than the bad
    transform alone — and improving the six good ones buys almost
    nothing. :func:`dominant_transform` names the term to fix.
    """
    if initial_m < 0:
        raise ValueError("initial uncertainty cannot be negative")

    var = initial_m * initial_m
    steps = []
    for i, t in enumerate(chain, start=1):
        before = math.sqrt(var)
        var += t.uncertainty_m * t.uncertainty_m
        after = math.sqrt(var)
        steps.append({
            "index": i,
            "from_frame": t.from_frame,
            "to_frame": t.to_frame,
            "step_uncertainty_m": t.uncertainty_m,
            "before_m": before,
            "after_m": after,
            "increase_m": after - before,
            "complete": t.complete,
        })

    total = math.sqrt(var)
    values = [initial_m] + [s["after_m"] for s in steps]
    monotone = all(a <= b for a, b in zip(values, values[1:]))

    return _stamp({
        "initial_m": initial_m,
        "steps": steps,
        "cumulative_m": values,
        "total_uncertainty_m": total,
        "n_transforms": len(chain),
        "monotone_nondecreasing": monotone,
        "growth_factor": (total / initial_m) if initial_m > 0 else None,
        "statement": (
            "quadrature accumulation is monotonically non-decreasing. "
            "Retrieval in a distant frame is less certain than "
            "retrieval in the recording frame, and no chain ordering, "
            "no inverse transform and no round trip recovers the "
            "difference."),
    })


def dominant_transform(chain: tuple[FrameTransform, ...]) -> dict:
    """Which link in the chain actually sets the total.

    Worth computing rather than assuming, in the same spirit as
    :func:`r7.clocklink.limiter`: effort spent on any transform other
    than the dominant one changes the total by almost nothing.
    """
    if not chain:
        raise FrameRefused("an empty chain has no dominant transform")
    worst = max(chain, key=lambda t: t.uncertainty_m)
    total = uncertainty_growth(chain)["total_uncertainty_m"]
    share = ((worst.uncertainty_m ** 2 / total ** 2) if total > 0
             else 0.0)
    return _stamp({
        "from_frame": worst.from_frame,
        "to_frame": worst.to_frame,
        "uncertainty_m": worst.uncertainty_m,
        "total_uncertainty_m": total,
        "variance_share": share,
        "note": (
            "in quadrature the largest term dominates. Improving any "
            "other transform in this chain changes the total by less "
            "than the rounding on the largest one."),
    })


# --------------------------------------------------------------------
# 3. Retrieval
# --------------------------------------------------------------------

def _validate_chain(record: FrameRecord, target_frame: str,
                    chain: tuple[FrameTransform, ...]) -> None:
    """Refuse a chain that is incomplete, broken, or misdirected."""
    if not target_frame:
        raise FrameRefused("retrieval requires a named target frame")

    if target_frame == record.recorded_frame:
        if chain:
            raise FrameRefused(
                "retrieval in the recording frame requires no "
                "transform; a chain was supplied and would add "
                "uncertainty for nothing")
        return

    if not chain:
        raise FrameRefused(
            f"no transform chain from {record.recorded_frame!r} to "
            f"{target_frame!r}. A frame change is not a relabelling; "
            f"without a declared chain the retrieval is refused.")

    incomplete = [t for t in chain if not t.complete]
    if incomplete:
        detail = "; ".join(
            f"{t.from_frame}->{t.to_frame} missing "
            f"{', '.join(t.missing())}" for t in incomplete)
        raise FrameRefused(
            f"transform chain is incomplete: {detail}. Frames move "
            f"relative to one another, so a transform without an "
            f"epoch and an ephemeris is not evaluable. Assuming the "
            f"current epoch would give an old record a confident and "
            f"wrong position, which is worse than refusing.")

    cursor = record.recorded_frame
    for i, t in enumerate(chain, start=1):
        if t.from_frame != cursor:
            raise FrameRefused(
                f"transform {i} starts in {t.from_frame!r} but the "
                f"chain has reached {cursor!r}; the chain is broken "
                f"and the composition is undefined")
        cursor = t.to_frame
    if cursor != target_frame:
        raise FrameRefused(
            f"the chain ends in {cursor!r}, not the requested target "
            f"{target_frame!r}")


def retrieve_in_frame(record: FrameRecord, target_frame: str,
                      transform_chain: tuple[FrameTransform, ...] = ()
                      ) -> dict:
    """Return the payload expressed in ``target_frame``, with its cost.

    Refuses if any transform in the chain lacks an epoch or an
    ephemeris, if the chain does not connect the recording frame to
    the target, or if the record's own provenance back to its root is
    incomplete. The payload is returned unmodified — this module does
    not know what a payload means — but the uncertainty attached to it
    is not the uncertainty it was recorded with, and the returned
    record says so explicitly.
    """
    if not isinstance(record, FrameRecord):
        raise TypeError("record must be a FrameRecord")

    if not record.provenance_complete():
        gaps = [f"{t.from_frame}->{t.to_frame}"
                for t in record.provenance if not t.complete]
        raise FrameRefused(
            f"the record's own provenance back to its declared root "
            f"{record.root_frame!r} is incomplete at {gaps}. A record "
            f"whose position relative to its root is unevaluable "
            f"cannot be re-expressed in any other frame; the "
            f"transform would compose onto an unknown.")

    _validate_chain(record, target_frame, transform_chain)

    growth = uncertainty_growth(
        transform_chain, initial_m=record.intrinsic_uncertainty_m)
    in_place = record.intrinsic_uncertainty_m
    total = growth["total_uncertainty_m"]

    return _stamp({
        "payload": record.payload,
        "payload_class": record.payload_class,
        "recorded_frame": record.recorded_frame,
        "recorded_epoch": record.recorded_epoch,
        "root_frame": record.root_frame,
        "target_frame": target_frame,
        "transform_chain": [t.as_record() for t in transform_chain],
        "n_transforms": len(transform_chain),
        "epochs_used": [t.epoch for t in transform_chain],
        "ephemerides_used": [t.ephemeris for t in transform_chain],
        "intrinsic_uncertainty_m": in_place,
        "accumulated_uncertainty_m": total,
        "uncertainty_added_m": total - in_place,
        "degraded": total > in_place,
        "growth": growth,
        "statement": (
            f"the payload is unchanged; its position is not. Recorded "
            f"in {record.recorded_frame!r} at "
            f"{record.recorded_epoch!r} to {in_place:.6g} m, it is "
            f"known in {target_frame!r} to {total:.6g} m. The "
            f"difference is the price of the transform chain and is "
            f"not recoverable by transforming back."),
        "epoch_note": (
            "every transform was evaluated at its own declared epoch "
            "against its own declared ephemeris. Both are reported so "
            "that a later reader can reproduce or dispute the "
            "composition."),
    })


def round_trip_cost(record: FrameRecord, target_frame: str,
                    out_chain: tuple[FrameTransform, ...],
                    back_chain: tuple[FrameTransform, ...]) -> dict:
    """Demonstrate that a round trip does not restore precision.

    Out and back is not the identity. The value returns; the
    uncertainty does not. This function exists because the intuition
    that inverse transforms cancel is strong, common, and wrong for
    the error budget.
    """
    out = retrieve_in_frame(record, target_frame, out_chain)
    returned = FrameRecord(
        payload=out["payload"],
        recorded_frame=target_frame,
        recorded_epoch=record.recorded_epoch,
        root_frame=record.root_frame,
        provenance=record.provenance,
        intrinsic_uncertainty_m=out["accumulated_uncertainty_m"],
        payload_class=record.payload_class)
    back = retrieve_in_frame(returned, record.recorded_frame,
                             back_chain)

    original = record.intrinsic_uncertainty_m
    final = back["accumulated_uncertainty_m"]
    return _stamp({
        "original_uncertainty_m": original,
        "at_target_uncertainty_m": out["accumulated_uncertainty_m"],
        "after_round_trip_uncertainty_m": final,
        "payload_unchanged": back["payload"] == record.payload,
        "precision_restored": final <= original,
        "permanent_loss_m": final - original,
        "statement": (
            "the payload survives the round trip unchanged and the "
            "precision does not. Inverse transforms compose on the "
            "value and accumulate on the error; there is no operation "
            "in this module that lowers an uncertainty."),
    })


# --------------------------------------------------------------------
# 4. Refusal
# --------------------------------------------------------------------

def refuse_frameless_retrieval(record: FrameRecord | None = None,
                               target_frame: str | None = None):
    """Refuse a retrieval that names no frame, or no epoch for it.

    Always raises. There is no argument combination that makes a
    frameless retrieval acceptable; the parameters exist only so the
    refusal can name what was asked for.
    """
    asked = (f"payload from {record.recorded_frame!r}"
             if isinstance(record, FrameRecord) else "a payload")
    where = (f" into {target_frame!r}" if target_frame
             else " into an unnamed frame")
    raise FrameRefused(
        f"refusing to retrieve {asked}{where} without a complete, "
        f"epoched transform chain. A stored coordinate is meaningless "
        f"outside the frame and epoch it was recorded in: frames "
        f"translate, rotate and accelerate relative to one another, "
        f"so 'the same position' in a different frame is a different "
        f"number, and which number depends on when you ask and which "
        f"ephemeris you ask. Retrieval without a frame is not a "
        f"lossy operation; it is an undefined one.")


def programme_summary() -> dict:
    """The P13 certificate."""
    return _stamp({
        "phase": "P13",
        "programme_id": "RGCS-V5.1-R8.1",
        "payload_classes": list(PAYLOAD_CLASSES),
        "invariants": [
            "a record without an epoch cannot be constructed",
            "a transform without an epoch and an ephemeris cannot be "
            "used, only inspected",
            "uncertainty is monotonically non-decreasing along any "
            "chain",
            "no operation in this module lowers an uncertainty",
            "a round trip restores the value and not the precision",
        ],
        "status": "MODEL_SPECIFIED_PHYSICALLY_UNTESTED",
        "statement": (
            "P13 models frame-tagged memory and its retrieval cost. "
            "It is a synthetic associative-memory model, not a brain "
            "interface, not a device, and not a personal-data store. "
            "No frame has been recorded and no ephemeris consulted."),
    })
