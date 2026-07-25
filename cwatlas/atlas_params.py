"""P36 -- Body / epoch / shell / altitude / codec selection logic.

The pure-logic core behind the "click map to vector" UI (UI Workflow A steps
1-2): choose a body and coordinate frame, then an epoch, shell state, altitude
(height) convention, and codec. This module *validates* a parameter set,
*enumerates* the allowed values for each field, and *defaults sensibly* -- but
it never hides a default in a signed receipt. Every assumption the operator did
not set is either an explicit refusal or a named default recorded in
:meth:`AtlasParams.to_dict`.

The governance rule (P36 objective): **expose every assumption and forbid
hidden defaults in signed receipts.** :func:`validate_params` fills nothing in
silently -- an unset mandatory field is a typed refusal. :func:`default_params`
returns a fully-populated set whose every value is inspectable, so a receipt
built from it lists the body, frame, epoch, shell, altitude convention, codec,
and depth verbatim.

This is selection logic only; the browser widget is out of scope. Choosing a
parameter set asserts nothing geographic and measures nothing.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED

No wall-clock is read; epochs are decimal-year strings passed in.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cwatlas import claims
from cwatlas.addressing import CWPACK40_DEPTH, MAX_REFINEMENT_DEPTH
from cwatlas.frames import ITRF_REALIZATIONS
from cwatlas.mars_frame import BODIES, HeightConvention
from cwatlas.shells import SHELL_MAX, SHELL_MIN

#: Phase identity.
PHASE_ID = "P36"
TRANCHE = "T05"


class ParamError(ValueError):
    """Raised on an invalid or under-specified parameter set."""


#: The frames allowed per body. Earth carries the ITRF realizations plus WGS84
#: and its IAU body-fixed frame; Mars carries its declared IAU body-fixed frame.
ALLOWED_FRAMES: dict[str, tuple[str, ...]] = {
    "EARTH": ("WGS84",) + tuple(sorted(ITRF_REALIZATIONS)) + (
        "IAU_EARTH_BODY_FIXED",),
    "MARS": ("IAU_MARS_BODY_FIXED",),
}

#: The forward codecs the UI can select: the CW-GEO-1 baseline and the
#: advanced icosahedral CW-HCM-ICO codec.
ALLOWED_CODECS: tuple[str, ...] = ("CW-GEO-1", "CW-HCM-ICO")

#: The codecs that consume a refinement ``depth`` (icosahedral family).
DEPTH_CODECS: frozenset[str] = frozenset({"CW-HCM-ICO"})

#: Sensible per-body default frames.
_DEFAULT_FRAME: dict[str, str] = {
    "EARTH": "ITRF2020",
    "MARS": "IAU_MARS_BODY_FIXED",
}

#: The default epoch (a decimal-year string). Named, never hidden.
DEFAULT_EPOCH = "2020.0"
#: The default altitude/height convention.
DEFAULT_HEIGHT_CONVENTION = HeightConvention.ELLIPSOIDAL
#: The default codec and refinement depth.
DEFAULT_CODEC = "CW-GEO-1"
DEFAULT_DEPTH = CWPACK40_DEPTH


# -- enumerations -----------------------------------------------------------

def allowed_bodies() -> tuple[str, ...]:
    """The declared reference bodies (``EARTH``, ``MARS``)."""
    return tuple(sorted(BODIES))


def allowed_frames(body_id: str) -> tuple[str, ...]:
    """The frames allowed for ``body_id``; refuses an unknown body."""
    if body_id not in ALLOWED_FRAMES:
        raise ParamError(
            f"unknown body {body_id!r}; declared bodies are {allowed_bodies()}")
    return ALLOWED_FRAMES[body_id]


def allowed_shells() -> tuple[Optional[int], ...]:
    """The allowed shell states: ``None`` (unset) plus ``0..8``."""
    return (None,) + tuple(range(SHELL_MIN, SHELL_MAX + 1))


def allowed_height_conventions() -> tuple[str, ...]:
    """The allowed altitude/height convention names."""
    return tuple(c.value for c in HeightConvention)


def allowed_codecs() -> tuple[str, ...]:
    """The forward codecs the UI can select."""
    return ALLOWED_CODECS


def allowed_depths() -> tuple[int, int]:
    """The inclusive ``(min, max)`` refinement depth for a depth-taking codec."""
    return (0, MAX_REFINEMENT_DEPTH)


# -- the parameter set ------------------------------------------------------

@dataclass(frozen=True)
class AtlasParams:
    """A validated body/epoch/shell/altitude/codec selection.

    Every field is explicit; :meth:`to_dict` lists them all so a signed receipt
    carries no hidden default. ``depth`` is present only for a depth-taking
    codec and is ``None`` otherwise.
    """

    body_id: str
    frame_id: str
    epoch: str
    height_convention: HeightConvention
    codec_id: str
    shell_state: Optional[int] = None
    depth: Optional[int] = None

    def to_dict(self) -> dict:
        """Every assumption, verbatim -- the receipt's parameter block."""
        return {
            "body_id": self.body_id,
            "frame_id": self.frame_id,
            "epoch": self.epoch,
            "shell_state": self.shell_state,
            "height_convention": self.height_convention.value,
            "codec_id": self.codec_id,
            "depth": self.depth,
        }


def _coerce_height_convention(value) -> HeightConvention:
    if isinstance(value, HeightConvention):
        return value
    if isinstance(value, str):
        try:
            return HeightConvention(value)
        except ValueError:
            pass
    raise ParamError(
        f"unknown height_convention {value!r}; allowed: "
        f"{allowed_height_conventions()}")


def validate_params(
    *,
    body_id: str,
    frame_id: str,
    epoch: str,
    codec_id: str,
    height_convention=DEFAULT_HEIGHT_CONVENTION,
    shell_state: Optional[int] = None,
    depth: Optional[int] = None,
) -> AtlasParams:
    """Validate a parameter set into a typed :class:`AtlasParams`.

    Every mandatory field must be supplied explicitly; an unknown or missing
    value is a typed refusal, never a silent fill. The CRS (frame) and epoch
    are mandatory (invariant 9), enforced through
    :func:`cwatlas.claims.refuse_pin_without_crs_epoch`.
    """
    if body_id not in ALLOWED_FRAMES:
        raise ParamError(
            f"unknown body {body_id!r}; declared bodies are {allowed_bodies()}")
    # Invariant 9: CRS (frame) and epoch mandatory.
    claims.refuse_pin_without_crs_epoch(crs=frame_id, epoch=(epoch or None))
    if frame_id not in ALLOWED_FRAMES[body_id]:
        raise ParamError(
            f"frame {frame_id!r} is not valid for body {body_id!r}; allowed: "
            f"{ALLOWED_FRAMES[body_id]}")
    if codec_id not in ALLOWED_CODECS:
        raise ParamError(
            f"unknown codec {codec_id!r}; allowed: {ALLOWED_CODECS}")
    convention = _coerce_height_convention(height_convention)
    if shell_state is not None:
        if not isinstance(shell_state, int) or isinstance(shell_state, bool):
            raise ParamError(
                f"shell_state must be an int or None, got {shell_state!r}")
        if not (SHELL_MIN <= shell_state <= SHELL_MAX):
            raise ParamError(
                f"shell_state must be in [{SHELL_MIN}, {SHELL_MAX}], got "
                f"{shell_state!r}")
    lo, hi = allowed_depths()
    if codec_id in DEPTH_CODECS:
        if depth is None:
            raise ParamError(
                f"codec {codec_id!r} requires an explicit refinement depth in "
                f"[{lo}, {hi}]; none was given (no hidden default)")
        if not isinstance(depth, int) or isinstance(depth, bool):
            raise ParamError(f"depth must be an int, got {depth!r}")
        if not (lo <= depth <= hi):
            raise ParamError(f"depth must be in [{lo}, {hi}], got {depth!r}")
    elif depth is not None:
        raise ParamError(
            f"codec {codec_id!r} does not take a refinement depth; got "
            f"depth={depth!r}")
    return AtlasParams(
        body_id=body_id,
        frame_id=frame_id,
        epoch=epoch,
        height_convention=convention,
        codec_id=codec_id,
        shell_state=shell_state,
        depth=depth,
    )


def default_params(body_id: str = "EARTH", *, codec_id: str = DEFAULT_CODEC
                  ) -> AtlasParams:
    """A fully-populated, sensible default parameter set for ``body_id``.

    Every default is named and inspectable via :meth:`AtlasParams.to_dict`, so
    a receipt built from it exposes -- rather than hides -- each assumption.
    """
    if body_id not in ALLOWED_FRAMES:
        raise ParamError(
            f"unknown body {body_id!r}; declared bodies are {allowed_bodies()}")
    depth = DEFAULT_DEPTH if codec_id in DEPTH_CODECS else None
    return validate_params(
        body_id=body_id,
        frame_id=_DEFAULT_FRAME[body_id],
        epoch=DEFAULT_EPOCH,
        codec_id=codec_id,
        height_convention=DEFAULT_HEIGHT_CONVENTION,
        shell_state=None,
        depth=depth,
    )


def atlas_params_report() -> dict:
    """What this module claims -- and, deliberately, what it does not."""
    return {
        "module": "cwatlas.atlas_params",
        "phase_id": PHASE_ID,
        "tranche": TRANCHE,
        "bodies": list(allowed_bodies()),
        "frames": {b: list(f) for b, f in ALLOWED_FRAMES.items()},
        "shells": list(allowed_shells()),
        "height_conventions": list(allowed_height_conventions()),
        "codecs": list(allowed_codecs()),
        "depth_range": list(allowed_depths()),
        "defaults": default_params().to_dict(),
        "hidden_defaults": "none (validate_params refuses unset mandatory fields)",
        "claim_class": claims.ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "ATLAS_PARAMS_VALIDATED_ENUMERATED_NO_HIDDEN_DEFAULTS",
        "what_this_does_not_say": (
            "Selecting a body, frame, epoch, shell, altitude convention, and "
            "codec asserts nothing geographic about any source vector; it only "
            "declares the conventions a downstream codec will operate under."),
    }
