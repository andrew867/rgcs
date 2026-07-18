"""A13/A28/A30/A31/A32 — path state, relativistic worldline channels,
and the arrival/causal-order firewall.

A *path* is a propagation route with delay, Doppler, gain, angle,
polarization and medium. A *worldline* is the spacetime history of an
endpoint. They are distinct: two receivers on different worldlines see
different delays and proper times for the SAME path geometry, and one
receiver sees one observation for MANY candidate path sets.

The causal firewall (A32) is the load-bearing piece: signals emitted
in one order can arrive in any order (different delays do that
trivially), and re-sorting arrivals never reverses causation. The
emission order is fixed on the emitter's worldline; a receiver that
sees B before A has learned about path delays, not about time.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import ClaimBoundaryError
from cspc.spacetime import C, gravitational_potential_shift, \
    velocity_time_dilation

#: media with representative propagation speeds (m/s) for delay
#: screening. Real work uses measured dispersion (A29).
MEDIUM_SPEEDS = {
    "VACUUM_EM": C,
    "AIR_EM": C / 1.0003,
    "FIBER_1550NM": C / 1.468,
    "COAX_PE": C * 0.66,
    "AIR_ACOUSTIC": 343.0,
    "WATER_ACOUSTIC": 1481.0,
    "QUARTZ_LONGITUDINAL": 5720.0,
}


@dataclass(frozen=True)
class PathState:
    id: str
    delay_s: float
    doppler_scale: float = 1.0
    complex_gain: complex = 1.0 + 0j
    angle_deg: float = 0.0
    polarization: str = ""
    medium: str = "VACUUM_EM"
    worldline_id: str = ""
    uncertainty: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.delay_s < 0:
            raise ClaimBoundaryError(
                "negative path delay refused: an advance would be a "
                "causality violation, not a channel parameter")
        if self.medium not in MEDIUM_SPEEDS:
            raise ClaimBoundaryError(f"unknown medium {self.medium!r}")


@dataclass(frozen=True)
class Emission:
    """An event on the emitter's worldline."""
    label: str
    emit_time_s: float


def arrivals(emissions: list, paths) -> list:
    """All (emission, path) arrival events, sorted by arrival time.

    ``paths`` is either a shared list (broadcast channel: every
    emission takes every path) or a dict label -> list (routed
    channel). Routing is what makes arrival reordering possible at
    all: with shared paths, first arrivals always track emission
    order.
    """
    out = []
    for e in emissions:
        plist = paths[e.label] if isinstance(paths, dict) else paths
        for p in plist:
            out.append({"label": e.label, "path": p.id,
                        "emit_time_s": e.emit_time_s,
                        "arrival_time_s": e.emit_time_s + p.delay_s})
    return sorted(out, key=lambda r: r["arrival_time_s"])


def causal_order_audit(emissions: list, paths) -> dict:
    """The A32 firewall as a computation.

    Detects arrival reordering (later emission arriving earlier via a
    shorter path) and states what it is: path-delay geometry. The
    audit REFUSES to emit any 'causal reversal' field — the concept is
    not representable in its output.
    """
    ordered_emit = sorted(emissions, key=lambda e: e.emit_time_s)
    arr = arrivals(emissions, paths)
    arrival_labels = [a["label"] for a in arr]
    emit_labels = [e.label for e in ordered_emit]
    # first-arrival order per emission
    first = {}
    for a in arr:
        first.setdefault(a["label"], a["arrival_time_s"])
    first_order = [k for k, _ in
                   sorted(first.items(), key=lambda kv: kv[1])]
    reordered = first_order != emit_labels
    return {
        "emission_order": emit_labels,
        "first_arrival_order": first_order,
        "all_arrivals": arrival_labels,
        "arrival_reordering_present": reordered,
        "explanation": ("later emissions arrived first over shorter "
                        "paths — ordinary delay geometry"
                        if reordered else
                        "arrival order matches emission order"),
        "causal_order": "UNCHANGED — emission order is fixed on the "
                        "emitter's worldline; receivers cannot alter "
                        "it (firewall REORDER_IS_REVERSAL)",
        "evidence_class": "DERIVED_ARITHMETIC",
    }


def assert_no_reversal_claim(text: str) -> None:
    """Lint: prose derived from an arrival analysis may not contain
    reversal language."""
    banned = ("causal reversal", "backwards in time", "time reversal",
              "arrived before it was sent")
    low = text.lower()
    for b in banned:
        if b in low:
            raise ClaimBoundaryError(
                f"reversal language {b!r} refused: arrival reordering "
                "is not causal reversal")


# --- relativistic worldline channel (A30/A31) ----------------------------

@dataclass(frozen=True)
class Worldline:
    """Constant-radius, constant-speed worldline in the weak field —
    enough to make proper-time bookkeeping real without a full metric
    integrator."""
    id: str
    radius_m: float
    speed_ms: float = 0.0

    def proper_rate_offset(self, reference_radius_m: float) -> float:
        """d(tau)/dt - 1 relative to a static clock at the reference
        radius (weak field + O(v^2/c^2)).

        Sign convention follows the v4.6 GPS fixture
        (``cspc.spacetime.satellite_clock_offset``):
        ``gravitational_potential_shift(r_ref, r)`` is positive when
        this worldline sits HIGHER than the reference and its clock
        runs fast; velocity dilation is negative for a moving clock.
        A LEO worldline must come out net-negative (velocity wins),
        GPS net-positive — both asserted by test against published
        values."""
        grav = gravitational_potential_shift(reference_radius_m,
                                             self.radius_m)
        vel = velocity_time_dilation(self.speed_ms)
        return grav + vel


def two_geodesic_case(reference_radius_m: float = 6378137.0) -> dict:
    """A31: one emitter, two receivers on different worldlines, same
    nominal path length. Their proper-time rates differ, so identical
    coordinate delays accumulate different proper phases. The
    discrepancy is real physics — and it is METROLOGY, not a channel
    for travel (v4.6 firewall CLOCK_SHIFT_TO_METRIC_CONTROL)."""
    ground = Worldline("GROUND", reference_radius_m, 0.0)
    orbit = Worldline("LEO", reference_radius_m + 400e3, 7670.0)
    f = 4096.0
    dt = 86400.0                      # one day
    rate_g = ground.proper_rate_offset(reference_radius_m)
    rate_o = orbit.proper_rate_offset(reference_radius_m)
    dphase_cycles = f * dt * (rate_o - rate_g)
    return {
        "worldlines": [ground.id, orbit.id],
        "carrier_hz": f,
        "duration_s": dt,
        "rate_offset_ground": rate_g,
        "rate_offset_orbit": rate_o,
        "differential_rate": rate_o - rate_g,
        "differential_phase_cycles_per_day": dphase_cycles,
        "interpretation":
            "two receivers on different worldlines accumulate "
            "different proper phase from the same emission — a "
            "measurable, worldline-indexed channel property",
        "not_an_interpretation":
            "this is clock metrology; it moves nothing and reverses "
            "nothing",
        "evidence_class": "ANALYTIC_MODEL",
    }
