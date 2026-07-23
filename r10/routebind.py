"""P14 — binding a handshake address to a rooted route, and the refusal
to retrofit a vector or a cue into a destination.

A handshake carries a *rooted address*: a symbolic reference to a
calculated root or a compiled route path (see r10.route, r10.rootframe),
never a latitude/longitude pair and never a raw numeric cue. This module
links such a symbolic address to a route *without inventing the link*.

The temptation it refuses is retrofit. Given a numeric cue heard in the
source (say a 1604 / 1644 pair), or a CW vector, it is trivial to hunt
until the digits "line up" with some route index or coordinate so they
"mean" a destination. That is fitting the target to the arrow after the
arrow has landed, and it is exactly the FROZEN_VALUES rule against
silently converting any value into a location, frequency, distance,
route index, historical event, or checksum. So:

* A binding is only ``ROUTE_BINDING_SOFTWARE_VALID`` when the route
  compiles (r10.route.compile_route) **and** the address token was
  *preregistered* -- declared before the route was seen. A binding
  discovered after the fact is refused (``refuse_retrofit``).
* A CW vector or numeric cue is never silently turned into a coordinate
  or a route index (``refuse_vector_to_coordinate``).
* Causality is inherited, not defeated. A bound route still carries the
  light-time floor from r10.route, and a zero-time transit still raises
  ``CausalityViolation`` through the binding path. No binding beats the
  light floor.

A valid binding is bookkeeping: it says a symbolic name and a compiled
frame-sequence were declared consistent ahead of time. It reaches
nothing, decodes nothing, and measures nothing. An unpreregistered
binding is ``NO_BETTER_THAN_CHANCE`` -- a post-hoc token search would
"find" a binding for almost any string, which is the look-elsewhere
trap, not evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from r10.route import (
    C_M_PER_S,
    CausalityViolation,
    RouteError,
    RouteHop,
    compile_route,
)


class RouteBindError(RuntimeError):
    """Raised on an unsupported or retrofitted address binding."""


@dataclass(frozen=True)
class AddressBinding:
    """A link between a symbolic rooted address and a handshake field.

    The address is symbolic -- a named root cell or a route path taken
    from r10.route -- never a coordinate reverse-fitted to digits. The
    provenance and the preregistration status are carried explicitly so
    the binding can be audited: a valid binding is one that was declared
    before the route was seen.
    """

    address_token: str            # symbolic rooted address, e.g. a path
    handshake_field: str          # which handshake field it binds to
    route_path: tuple             # the compiled route path it binds to
    light_floor_s: float          # inherited light-time floor, never zero-beat
    provenance: str               # where the token came from
    preregistered: bool           # declared before the route was seen
    verdict: str = "ROUTE_BINDING_SOFTWARE_VALID"


def bind_address(route_hops: list[RouteHop],
                 address_token: str,
                 preregistered: bool,
                 handshake_field: str = "rooted_address",
                 provenance: str = "PREREGISTERED_DECLARATION") -> AddressBinding:
    """Bind a symbolic address to a rooted route, or refuse.

    The route is compiled through r10.route.compile_route, so an
    unsupported edge, incompatible epochs, a disconnected path, or a
    zero-time transit propagate as RouteError / CausalityViolation --
    the binding never launders them. If the route is structurally valid
    but the token was not preregistered, the binding is refused as a
    retrofit; you may not fit an address to a route after the fact.
    """
    compiled = compile_route(route_hops)      # may raise RouteError / CausalityViolation
    if not preregistered:
        refuse_retrofit(address_token, compiled["path"])
    return AddressBinding(
        address_token=address_token,
        handshake_field=handshake_field,
        route_path=tuple(compiled["path"]),
        light_floor_s=compiled["total_light_floor_s"],
        provenance=provenance,
        preregistered=True,
        verdict="ROUTE_BINDING_SOFTWARE_VALID",
    )


def refuse_retrofit(address_token: str, route_path) -> None:
    """A binding discovered after seeing the route is a retrofit."""
    raise RouteBindError(
        f"address token {address_token!r} was not preregistered; fitting "
        f"it to route {list(route_path)!r} after the route was seen is a "
        f"retrofit. A binding is only valid when the token was declared "
        f"before the route existed. BINDING_UNSUPPORTED.")


def refuse_vector_to_coordinate(cue, target_kind: str = "coordinate") -> None:
    """A CW vector or numeric cue is not silently a coordinate/route index.

    Mirrors the FROZEN_VALUES rule: do not silently convert any value
    into a location, frequency, distance, route index, historical event,
    or checksum. The cue is passed through untouched in the message so no
    digits are invented here.
    """
    raise RouteBindError(
        f"a CW vector or numeric cue ({cue!r}) may not be silently "
        f"converted into a {target_kind}. Reverse-fitting digits to a "
        f"location, route index, frequency, distance, or checksum is "
        f"retrofit, not decoding. The cue stays an uninterpreted symbol "
        f"until an independent, preregistered mapping is supplied.")


def binding_is_better_than_chance(preregistered: bool) -> dict:
    """A binding is evidence only if it was preregistered.

    An unpreregistered token can be made to "bind" to some valid route
    by searching the space of tokens and routes -- the look-elsewhere
    effect -- so it carries no evidential weight.
    """
    if preregistered:
        return {
            "preregistered": True,
            "power": "BETTER_THAN_CHANCE",
            "why": (
                "the token was fixed before the route was seen, so a "
                "consistent binding is not a product of post-hoc search"),
        }
    return {
        "preregistered": False,
        "power": "NO_BETTER_THAN_CHANCE",
        "why": (
            "a post-hoc token search would find a binding for almost any "
            "string; that is the look-elsewhere trap, not evidence"),
    }


def routebind_report() -> dict:
    return {
        "verdicts": ["ROUTE_BINDING_SOFTWARE_VALID", "BINDING_UNSUPPORTED",
                     "NO_BETTER_THAN_CHANCE"],
        "refusals": [
            "binding an address that was not preregistered (retrofit)",
            "silently converting a CW vector or numeric cue into a "
            "coordinate or route index",
            "any binding that would lower the light-time floor (inherited "
            "from r10.route as CausalityViolation)"],
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "what_this_does_not_say": (
            "A valid binding is bookkeeping: a symbolic address and a "
            "compiled frame-sequence were declared consistent ahead of "
            "time. It does not say the address is a real place, that any "
            "destination is reached, or that a CW vector or numeric cue "
            "decodes to a coordinate. No digits are converted into "
            "locations here, and no binding beats the light-time floor."),
        "verdict": "ROUTE_BINDING_SOFTWARE_VALID",
    }
