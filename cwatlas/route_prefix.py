"""P37 -- Terra / Sol namespaces and variable-depth route prefixes.

A *route prefix* is human-facing routing metadata that labels a CW vector
without touching its numbers. It carries two things:

* a **namespace** -- a short label such as ``terra:`` or ``sol:`` that names
  the frame of reference a reader should assume, and
* a **variable-depth route** -- a depth-prefixed path (``d<N>/seg0/seg1/...``)
  that records how a client walked to the vector (folders, zoom levels, a
  breadcrumb). ``N`` declares the number of segments so a truncated or padded
  path is a typed refusal rather than a silent guess.

The single load-bearing invariant of this module (System Contract: a label is
not a coordinate) is:

    **a namespace or route prefix NEVER changes the numeric address.**

:func:`strip` returns the underlying CW vector byte-for-byte regardless of the
namespace or route wrapped around it, and :func:`rewrap` can move a vector from
``terra:`` to ``sol:`` without altering a single quantized token. A namespace is
a name; the geometry is untouched.

This is a MATHEMATICAL_TRANSLATION at the SOFTWARE level: a route is a label.
It asserts nothing geographic about any source vector. See
:mod:`cwatlas.claims`.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from cwatlas import claims

MODULE_PHASE = "P37"

#: The delimiter between a route prefix and the CW vector it labels. Chosen
#: because it never appears in a CW-GEO-1 payload (which uses ``;`` and ``=``).
PREFIX_DELIMITER = "|"

#: A route segment is a conservative, URL/file-safe identifier: no delimiters,
#: no path separators, no whitespace.
_SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")

#: A namespace label is a lowercase identifier terminated by a colon on the
#: wire; here we hold just the bare label.
_NAMESPACE_RE = re.compile(r"^[a-z][a-z0-9_-]*$")


class RoutePrefixError(ValueError):
    """Raised on a malformed namespace, depth, or route path."""


class Namespace(Enum):
    """The known top-level namespaces.

    These are *labels for the reader*, not transforms. ``TERRA`` marks a vector
    a client is presenting in an Earth-centred frame; ``SOL`` marks one
    presented in a solar / heliocentric frame. Neither changes the numbers.
    """

    TERRA = "terra"
    SOL = "sol"


#: Namespaces recognised without an explicit opt-in. A caller may still use a
#: custom lowercase-identifier namespace via :func:`make_prefix` with
#: ``allow_custom=True`` -- it is still label-only.
KNOWN_NAMESPACES = frozenset(ns.value for ns in Namespace)


def _validate_namespace(namespace: str, *, allow_custom: bool) -> str:
    if not isinstance(namespace, str) or not namespace:
        raise RoutePrefixError("namespace must be a non-empty string")
    if not _NAMESPACE_RE.match(namespace):
        raise RoutePrefixError(
            f"namespace {namespace!r} must be a lowercase identifier "
            f"([a-z][a-z0-9_-]*)")
    if namespace not in KNOWN_NAMESPACES and not allow_custom:
        raise RoutePrefixError(
            f"unknown namespace {namespace!r}; known={sorted(KNOWN_NAMESPACES)} "
            f"(pass allow_custom=True for a bespoke label)")
    return namespace


def _validate_segments(segments) -> Tuple[str, ...]:
    out = []
    for seg in segments:
        if not isinstance(seg, str) or not _SEGMENT_RE.match(seg):
            raise RoutePrefixError(
                f"route segment {seg!r} must match {_SEGMENT_RE.pattern}")
        out.append(seg)
    return tuple(out)


@dataclass(frozen=True)
class RoutePrefix:
    """A namespace plus a variable-depth route path (label-only metadata).

    ``depth`` is redundant with ``len(segments)`` on purpose: it is written on
    the wire as ``d<depth>`` so a corrupted path (fewer/more segments than the
    declared depth) is caught rather than silently accepted.
    """

    namespace: str
    segments: Tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_namespace(self.namespace, allow_custom=True)
        object.__setattr__(self, "segments", _validate_segments(self.segments))

    @property
    def depth(self) -> int:
        return len(self.segments)

    def format(self) -> str:
        """Format as ``<namespace>:d<depth>/seg0/seg1/...`` (no trailing slash).

        At depth 0 the route is just ``<namespace>:d0``.
        """
        body = "/".join((f"d{self.depth}", *self.segments))
        return f"{self.namespace}:{body}"


def make_prefix(
    namespace: str, *segments: str, allow_custom: bool = False
) -> RoutePrefix:
    """Build a :class:`RoutePrefix`, validating the namespace and every segment."""
    ns = _validate_namespace(namespace, allow_custom=allow_custom)
    return RoutePrefix(namespace=ns, segments=_validate_segments(segments))


def parse_prefix(text: str, *, allow_custom: bool = True) -> RoutePrefix:
    """Parse ``<namespace>:d<depth>/seg.../`` back into a :class:`RoutePrefix`.

    Refuses a missing colon, a missing/negative/mismatched depth, or a bad
    segment. The declared ``d<depth>`` must equal the number of trailing
    segments, or the path is a typed refusal.
    """
    if not isinstance(text, str) or ":" not in text:
        raise RoutePrefixError(
            f"route prefix {text!r} must be '<namespace>:d<depth>/...'")
    namespace, _, rest = text.partition(":")
    _validate_namespace(namespace, allow_custom=allow_custom)
    if not rest:
        raise RoutePrefixError("route prefix missing the d<depth> component")
    parts = rest.split("/")
    depth_tok, segments = parts[0], parts[1:]
    if not re.match(r"^d(0|[1-9][0-9]*)$", depth_tok):
        raise RoutePrefixError(
            f"route prefix depth token {depth_tok!r} must be 'd<N>'")
    declared = int(depth_tok[1:])
    if declared != len(segments):
        raise RoutePrefixError(
            f"route depth mismatch: declared d{declared} but found "
            f"{len(segments)} segment(s)")
    return RoutePrefix(namespace=namespace, segments=_validate_segments(segments))


def wrap(vector: str, prefix: RoutePrefix) -> str:
    """Attach a route prefix to a CW vector: ``<prefix>|<vector>``.

    The vector is stored verbatim. The delimiter must not already appear in the
    vector, so :func:`strip` is unambiguous.
    """
    if not isinstance(vector, str) or not vector:
        raise RoutePrefixError("vector must be a non-empty string")
    if PREFIX_DELIMITER in vector:
        raise RoutePrefixError(
            f"vector may not contain the prefix delimiter {PREFIX_DELIMITER!r}")
    return f"{prefix.format()}{PREFIX_DELIMITER}{vector}"


def split(routed: str) -> tuple[RoutePrefix, str]:
    """Split ``<prefix>|<vector>`` into its :class:`RoutePrefix` and raw vector."""
    if not isinstance(routed, str) or PREFIX_DELIMITER not in routed:
        raise RoutePrefixError(
            f"routed vector must be '<prefix>{PREFIX_DELIMITER}<vector>'")
    prefix_txt, _, vector = routed.partition(PREFIX_DELIMITER)
    return parse_prefix(prefix_txt), vector


def strip(routed: str) -> str:
    """Return the underlying CW vector, discarding any route/namespace label.

    This is the invariant enforcer: the numeric address is whatever follows the
    delimiter, untouched by the namespace or route wrapped around it.
    """
    return split(routed)[1]


def rewrap(routed: str, namespace: str, *segments: str,
           allow_custom: bool = False) -> str:
    """Re-label a routed vector under a new namespace/route, numbers unchanged.

    Proves the invariant operationally: ``strip(rewrap(x, ...)) == strip(x)``.
    """
    vector = strip(routed)
    return wrap(vector, make_prefix(namespace, *segments,
                                    allow_custom=allow_custom))


def route_prefix_report() -> dict:
    """Governance report: what this module is and, emphatically, is not."""
    return {
        "module": "cwatlas.route_prefix",
        "phase_id": MODULE_PHASE,
        "known_namespaces": sorted(KNOWN_NAMESPACES),
        "prefix_delimiter": PREFIX_DELIMITER,
        "invariant": "NAMESPACE_AND_ROUTE_ARE_LABEL_ONLY_NUMERIC_ADDRESS_UNCHANGED",
        "claim_class": claims.ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "level": "SOFTWARE",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "CW_ATLAS_ROUTE_PREFIX_LABEL_ONLY_ROUND_TRIP_STABLE",
        "what_this_does_not_say": (
            "A namespace such as terra: or sol: is a label for a reader, not a "
            "coordinate transform and not a geographic claim. Moving a vector "
            "between namespaces never alters a single quantized token, and no "
            "route path decodes a source vector to a real location."),
    }
