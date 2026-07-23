"""P08 — binding a codec output to a coordinate, and the refusal to read
a bare number as a position.

A CW codec output is a NUMBER (or a tuple of numbers). That is all it is.
A number is not a coordinate. Before a decoded value can be called a
position it must be bound to *five* declared things: a calculated root
(see r10.rootframe / r10.route), a frame convention, an epoch, an
optional density layer, and an uncertainty. Until all of those are
attached, the value is an uninterpreted symbol, and this module refuses
to pretend otherwise.

Three refusals are load-bearing, and each mirrors a rule already in
force elsewhere in R10:

* **A frame and an epoch are mandatory** (GREEN_FRAME_EPOCH_REQUIRED).
  A coordinate stated without a frame and an epoch is meaningless -- the
  same digits name different places in different frames and at different
  epochs. Binding without both is refused
  (``refuse_binding_without_frame_epoch``). This is the FROZEN_VALUES
  rule against silently converting a value into a location or route
  index: no frame, no epoch, no coordinate.
* **An uncertainty is mandatory.** A decoded integer is not an
  infinitely precise point. A coordinate with zero or missing
  uncertainty is refused (``refuse_zero_uncertainty_point``); every
  bound position carries a sigma or a covariance.
* **Preregistration is mandatory.** A binding fit after the codec output
  was seen is a retrofit -- fit the coordinate to the number after the
  number landed and almost any value "becomes" some place in some frame.
  That is refused (``refuse_retrofit_binding``).

A valid ``CoordinateBinding`` is bookkeeping: a number, a typed root, a
frame, an epoch, a layer, and an uncertainty were declared consistent
ahead of time. It reaches nothing, decodes nothing, and measures
nothing. An unpreregistered binding to an arbitrary frame is
``NO_BETTER_THAN_CHANCE``: any number can be called a coordinate in some
frame, which is the look-elsewhere trap, not evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from r10.rootframe import RootFrame
from r10.route import SUPPORTED_EDGES


class CodecBindError(RuntimeError):
    """Raised on an unframed, uncertain, or retrofitted coordinate binding."""


#: Symbolic root tokens that are real typed roots: every endpoint that
#: appears in the r10.route supported graph. A bound root must be one of
#: these tokens or a fully-determined r10.rootframe.RootFrame -- never an
#: ad-hoc string invented at binding time.
KNOWN_ROOT_TOKENS = frozenset(
    tok for edge in SUPPORTED_EDGES for tok in edge)


def _root_id(root) -> str:
    """Resolve a symbolic root id from a RootFrame or a known token.

    A RootFrame is accepted because building it already forced a
    determined roll, an epoch, a handedness, and a scale (see
    r10.rootframe). A bare string is accepted only if it is a known
    typed root token from the r10.route graph. Anything else is an
    ad-hoc string and is refused -- a coordinate is not bound to a name
    someone made up at decode time.
    """
    if isinstance(root, RootFrame):
        return root.root_id
    if isinstance(root, str) and root in KNOWN_ROOT_TOKENS:
        return root
    raise CodecBindError(
        f"root {root!r} is not a typed root. A coordinate binds to a "
        f"determined r10.rootframe.RootFrame or a known root token from "
        f"the r10.route graph ({sorted(KNOWN_ROOT_TOKENS)}), never to an "
        f"ad-hoc string invented at decode time. BINDING_UNSUPPORTED.")


def _has_uncertainty(uncertainty) -> bool:
    """True only for a genuinely nonzero sigma or covariance.

    None, zero, or an all-zero covariance mean "an exact point", which a
    decoded number is not. A scalar sigma must be positive; a covariance
    (any nested sequence) must have at least one nonzero entry.
    """
    if uncertainty is None:
        return False
    if isinstance(uncertainty, bool):
        return False
    if isinstance(uncertainty, (int, float)):
        return uncertainty > 0
    try:
        flat = _flatten(uncertainty)
    except TypeError:
        return False
    return len(flat) > 0 and any(abs(v) > 0 for v in flat)


def _flatten(x) -> list:
    out: list = []
    for item in x:
        if isinstance(item, (list, tuple)):
            out.extend(_flatten(item))
        else:
            out.append(item)
    return out


@dataclass(frozen=True)
class CoordinateBinding:
    """A codec output declared consistent with a coordinate.

    The value is a number (or tuple of numbers); the root is a typed
    root id (from a RootFrame or the r10.route graph); the frame and
    epoch are the mandatory convention; the layer is an optional density
    layer; the uncertainty is a sigma or covariance, never zero. The
    preregistration status and provenance are carried so the binding can
    be audited: a valid binding was declared before the codec output was
    seen.
    """

    codec_value: object           # a decoded number or tuple of numbers
    root: str                     # symbolic typed root id
    frame_id: str                 # declared frame convention
    epoch: str                    # ISO epoch string
    uncertainty: object           # sigma (scalar) or covariance
    preregistered: bool           # declared before the codec output was seen
    layer: str | None = None      # optional density layer
    provenance: str = "PREREGISTERED_DECLARATION"
    verdict: str = "CODEC_BINDING_SOFTWARE_VALID"


def bind_coordinate(codec_value,
                    root,
                    frame_id: str,
                    epoch: str,
                    uncertainty,
                    preregistered: bool,
                    layer: str | None = None,
                    provenance: str = "PREREGISTERED_DECLARATION",
                    ) -> CoordinateBinding:
    """Bind a codec output to a coordinate, or refuse.

    The refusals are checked in order and none is skippable: a frame and
    an epoch must both be present; an uncertainty must be genuinely
    nonzero; the binding must have been preregistered; and the root must
    resolve to a real typed root. Only when all four hold does a
    CODEC_BINDING_SOFTWARE_VALID binding come back. The binding launders
    nothing: a bare number does not become a position by passing through
    here, it becomes an audited, fully-qualified coordinate declaration.
    """
    if not frame_id or not epoch:
        refuse_binding_without_frame_epoch(codec_value, frame_id, epoch)
    if not _has_uncertainty(uncertainty):
        refuse_zero_uncertainty_point(codec_value)
    if not preregistered:
        refuse_retrofit_binding(codec_value, frame_id)
    root_id = _root_id(root)
    return CoordinateBinding(
        codec_value=codec_value,
        root=root_id,
        frame_id=frame_id,
        epoch=epoch,
        uncertainty=uncertainty,
        preregistered=True,
        layer=layer,
        provenance=provenance,
        verdict="CODEC_BINDING_SOFTWARE_VALID",
    )


def refuse_binding_without_frame_epoch(codec_value,
                                       frame_id: str,
                                       epoch: str) -> None:
    """A coordinate with no frame and epoch is not a coordinate."""
    missing = []
    if not frame_id:
        missing.append("frame_id")
    if not epoch:
        missing.append("epoch")
    raise CodecBindError(
        f"codec output {codec_value!r} cannot be bound as a coordinate "
        f"without {' and '.join(missing) or 'a frame and an epoch'}. The "
        f"same digits name different places in different frames and at "
        f"different epochs; silently reading a number as a location is "
        f"the FROZEN_VALUES violation. GREEN_FRAME_EPOCH_REQUIRED, "
        f"BINDING_UNSUPPORTED.")


def refuse_zero_uncertainty_point(codec_value) -> None:
    """A decoded number is not an infinitely precise position."""
    raise CodecBindError(
        f"codec output {codec_value!r} cannot be bound as a zero-"
        f"uncertainty point. A decoded integer is not an infinitely "
        f"precise position; every bound coordinate carries a positive "
        f"sigma or a nonzero covariance. Refusing the exact-point "
        f"binding. BINDING_UNSUPPORTED.")


def refuse_retrofit_binding(codec_value, frame_id: str) -> None:
    """A binding fit after the codec output was seen is a retrofit."""
    raise CodecBindError(
        f"codec output {codec_value!r} was not preregistered to a "
        f"coordinate; fitting it to frame {frame_id!r} after the output "
        f"was seen is a retrofit. Any number can be called a coordinate "
        f"in some frame, so a post-hoc binding is the look-elsewhere "
        f"trap, not a decode. A binding is valid only when the frame, "
        f"epoch, and uncertainty were declared before the output "
        f"existed. BINDING_UNSUPPORTED.")


def binding_is_better_than_chance(preregistered: bool) -> dict:
    """A coordinate binding is evidence only if it was preregistered.

    Without preregistration a number can be paired with some frame in
    which it "lands" on a place of interest -- the space of frames is
    large enough that a search will always succeed -- so the binding
    carries no evidential weight.
    """
    if preregistered:
        return {
            "preregistered": True,
            "power": "BETTER_THAN_CHANCE",
            "why": (
                "the frame, epoch, and uncertainty were fixed before the "
                "codec output was seen, so a consistent coordinate is not "
                "a product of post-hoc frame search"),
        }
    return {
        "preregistered": False,
        "power": "NO_BETTER_THAN_CHANCE",
        "why": (
            "any number can be called a coordinate in some frame; a "
            "post-hoc frame search would place almost any value on a "
            "point of interest, which is the look-elsewhere trap, not "
            "evidence"),
    }


def codecbind_report() -> dict:
    return {
        "verdicts": ["CODEC_BINDING_SOFTWARE_VALID", "BINDING_UNSUPPORTED",
                     "NO_BETTER_THAN_CHANCE"],
        "required_fields": [
            "codec_value", "root", "frame_id", "epoch", "uncertainty",
            "preregistered", "provenance"],
        "refusals": [
            "binding a coordinate without a frame and an epoch "
            "(GREEN_FRAME_EPOCH_REQUIRED)",
            "binding a decoded number as a zero-uncertainty point",
            "binding fit after the codec output was seen (retrofit)",
            "binding a root that is an ad-hoc string, not a typed root"],
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "what_this_does_not_say": (
            "A valid binding is bookkeeping: a number, a typed root, a "
            "frame, an epoch, a layer, and an uncertainty were declared "
            "consistent ahead of time. It does not say the codec output "
            "is a real place, that a position was reached or measured, "
            "or that a bare number decodes to a coordinate. No digits are "
            "silently converted into locations here, and a coordinate "
            "with no frame, epoch, or uncertainty is refused."),
        "verdict": "CODEC_BINDING_SOFTWARE_VALID",
    }
