"""P07 — the rooted interbody route compiler, with causal refusals.

Routes are compiled *through calculated roots*, not through lat/lon:

    Earth local cell -> Earth body root -> Earth-Moon parent root
                     -> Moon body root -> Moon local cell

Each transition carries a source root, a destination root, an epoch, a
transform, a conventional travel-time baseline, and a causal status.
The compiler's job is bookkeeping, and its value is what it **refuses**:

* an edge whose two roots are at incompatible epochs;
* a transition with no supported graph edge;
* a root whose roll is undetermined (delegated to r10.rootframe);
* and, most importantly, **a conventional travel across a nonzero
  distance in zero time.** Software route existence is not a physical
  gateway; a compiled path is a label for a sequence of frames, and the
  travel-time baseline is the light-time floor, never zero.

`ROUTE_SOFTWARE_VALID` means the frames compose and the bookkeeping is
consistent. It never means a physical edge exists -- that is
`PHYSICAL_EDGE_UNSUPPORTED`, and `CAUSAL_DELAY_REQUIRED` is attached to
every hop that spans a distance.
"""

from __future__ import annotations

from dataclasses import dataclass, field

C_M_PER_S = 299_792_458


class RouteError(ValueError):
    """Raised on a malformed or unsupported route edge."""


class CausalityViolation(RuntimeError):
    """Raised when a hop claims to cross distance in zero time."""


#: The supported root graph (which roots connect to which).
SUPPORTED_EDGES = {
    ("EARTH_CELL", "EARTH_ROOT"),
    ("EARTH_ROOT", "EARTH_MOON_ROOT"),
    ("EARTH_MOON_ROOT", "MOON_ROOT"),
    ("MOON_ROOT", "MOON_CELL"),
    ("EARTH_ROOT", "SOLAR_ROOT"),
    ("SOLAR_ROOT", "MARS_SYSTEM_ROOT"),
    ("MARS_SYSTEM_ROOT", "MARS_ROOT"),
    ("MARS_ROOT", "MARS_CELL"),
    ("MARS_SYSTEM_ROOT", "MARS_ORBIT_ROOT"),
}


@dataclass(frozen=True)
class RouteHop:
    """One transition between two roots."""

    source_root: str
    dest_root: str
    epoch_source: str
    epoch_dest: str
    distance_m: float            # nonzero for a spatial hop
    conventional_travel_s: float
    density_layer: str
    source_authority: str
    evidence_status: str

    def __post_init__(self) -> None:
        if (self.source_root, self.dest_root) not in SUPPORTED_EDGES:
            raise RouteError(
                f"no supported edge {self.source_root} -> "
                f"{self.dest_root}; the compiler does not invent graph "
                f"edges (PHYSICAL_EDGE_UNSUPPORTED)")
        if self.epoch_source != self.epoch_dest:
            raise RouteError(
                f"incompatible epochs {self.epoch_source} != "
                f"{self.epoch_dest}; a hop must be stated at one epoch "
                f"or carry an explicit ephemeris transform")
        if self.distance_m < 0:
            raise RouteError("distance cannot be negative")
        floor = self.distance_m / C_M_PER_S
        if self.distance_m > 0 and self.conventional_travel_s < floor - 1e-9:
            raise CausalityViolation(
                f"a conventional hop of {self.distance_m:g} m in "
                f"{self.conventional_travel_s:g} s beats light "
                f"(floor {floor:g} s). Software route existence is not "
                f"a gateway; the baseline is the light-time floor.")

    @property
    def light_floor_s(self) -> float:
        return self.distance_m / C_M_PER_S

    @property
    def causal_status(self) -> str:
        return ("INSTANTANEOUS_LOCAL" if self.distance_m == 0
                else "CAUSAL_DELAY_REQUIRED")


def compile_route(hops: list[RouteHop]) -> dict:
    """Check a sequence of hops composes into a consistent route."""
    if not hops:
        raise RouteError("an empty route is not a route")
    for a, b in zip(hops, hops[1:]):
        if a.dest_root != b.source_root:
            raise RouteError(
                f"route is not connected: {a.dest_root} != "
                f"{b.source_root}")
    total_floor = sum(h.light_floor_s for h in hops)
    return {
        "hops": len(hops),
        "path": [hops[0].source_root] + [h.dest_root for h in hops],
        "total_light_floor_s": total_floor,
        "spatial_hops": sum(1 for h in hops if h.distance_m > 0),
        "verdict": "ROUTE_SOFTWARE_VALID",
        "physical_edge_status": "PHYSICAL_EDGE_UNSUPPORTED",
        "causal_status": ("CAUSAL_DELAY_REQUIRED"
                          if total_floor > 0 else "LOCAL_ONLY"),
        "note": (
            "the frames compose and the bookkeeping is consistent. This "
            "is not a physical path: no edge is a gateway, and every "
            "spatial hop carries the light-time floor as its baseline"),
    }


def refuse_zero_time_transit(distance_m: float) -> None:
    floor = distance_m / C_M_PER_S
    raise CausalityViolation(
        f"a transit of {distance_m:g} m cannot take zero time; the floor "
        f"is {floor:g} s. A compiled route is a sequence of frames, not "
        f"a shortcut through spacetime, and no software edge lowers the "
        f"light-time floor.")


def route_report() -> dict:
    return {
        "supported_edges": sorted("->".join(e) for e in SUPPORTED_EDGES),
        "verdicts": ["ROUTE_SOFTWARE_VALID", "PHYSICAL_EDGE_UNSUPPORTED",
                     "CAUSAL_DELAY_REQUIRED"],
        "refusals": [
            "unsupported graph edge",
            "incompatible epochs without an ephemeris transform",
            "zero-time transit across nonzero distance",
            "underdetermined root roll (via r10.rootframe)"],
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "what_this_does_not_say": (
            "A compiled route is bookkeeping over calculated frames. It "
            "is not a gateway, a wormhole, or a faster-than-light path; "
            "software route existence establishes no physical edge and "
            "no destination is reached."),
    }
