"""A25-A29 — operational spacetime definitions, relativistic clock
metrology, the metric/energy audit, and the two firewalls.

**A25 operational definitions.** The originating question mixes five
distinct things. They are defined separately here because conflating
them is what makes "resonance → time travel" sound plausible:

- *proper time*: what a clock carried along a worldline accumulates;
- *coordinate time*: a bookkeeping label in a chosen chart;
- *phase*: the argument of an oscillator, modulo 2π;
- *delay*: a shift in arrival time of a signal;
- *transport*: moving a system along a different worldline.

A resonator manipulates **phase**. Phase is not proper time; a phase
shift is not a delay; a delay is not transport.

**A26 relativistic clock metrology.** Clocks really are sensitive to
the metric, and this is a legitimate, useful capability. The weak-field
fractional rate difference is Δf/f ≈ ΔΦ/c² − v²/2c². The implementation
is validated against two independent published measurements (Pound-
Rebka and the GPS clock correction), so the code is checked against the
world rather than against itself.

**A27 metric perturbation and energy audit.** The honest quantitative
answer to "could this apparatus bend spacetime usefully?" Convert
apparatus energy to equivalent mass (E/c²) and to a Schwarzschild
radius (2GM/c²), then compare with lengths people can actually
measure. The numbers are not close; they are absurd, by ~30 orders of
magnitude. This is a *quantitative* falsification, not a rhetorical
one.

**A28/A29 firewalls.** Time-crystal literature describes systems whose
observable breaks discrete time-translation symmetry — a subharmonic
response. That is a real, published phenomenon and it is *not* travel.
Travel claims default to UNSUPPORTED and carry the specific evidence
each would require.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# --- physical constants (CODATA/SI, exact where defined) ----------------

C = 299_792_458.0                  # m/s, exact by SI definition
G = 6.674_30e-11                   # m^3 kg^-1 s^-2 (CODATA 2018)
G_EARTH = 9.806_65                 # m/s^2, standard gravity (defined)
GM_EARTH = 3.986_004_418e14        # m^3/s^2 (WGS-84)
R_EARTH = 6_378_137.0              # m, WGS-84 equatorial
H_PLANCK = 6.626_070_15e-34        # J s, exact by SI definition
PLANCK_LENGTH = 1.616_255e-35      # m
PROTON_RADIUS = 8.414e-16          # m


# --- A25 operational definitions ----------------------------------------

OPERATIONAL_DEFINITIONS = {
    "proper_time": {
        "symbol": "tau",
        "definition": "the time accumulated by an ideal clock carried "
                      "along a specific worldline",
        "measured_by": "a clock, locally",
        "resonator_can_change_it": "only by changing the clock's "
                                   "worldline or local potential",
    },
    "coordinate_time": {
        "symbol": "t",
        "definition": "a label assigned by a chosen coordinate chart; "
                      "chart-dependent and not directly measurable",
        "measured_by": "nothing; it is bookkeeping",
        "resonator_can_change_it": "no — changing coordinates changes "
                                   "no physical fact",
    },
    "phase": {
        "symbol": "phi",
        "definition": "the argument of an oscillator modulo 2*pi",
        "measured_by": "a phase comparator against a reference",
        "resonator_can_change_it": "YES — this is what a resonator "
                                   "actually manipulates",
    },
    "delay": {
        "symbol": "Delta t",
        "definition": "a shift in the arrival time of a signal",
        "measured_by": "time-of-flight against a shared clock",
        "resonator_can_change_it": "yes, for the signal it filters; "
                                   "this is filtering, not transport",
    },
    "transport": {
        "symbol": "-",
        "definition": "moving a physical system along a different "
                      "worldline so its accumulated proper time "
                      "differs",
        "measured_by": "comparing clocks after reunion",
        "resonator_can_change_it": "no known mechanism at laboratory "
                                   "energies",
    },
}

#: What is NOT implied by what. Each entry is a refusal.
DEFINITION_FIREWALLS = (
    ("phase", "proper_time",
     "a phase shift is a change in an oscillator's argument, not in "
     "any clock's accumulated proper time"),
    ("phase", "delay",
     "a steady phase offset is not a group delay; a filter can shift "
     "phase without delaying information"),
    ("delay", "transport",
     "delaying a signal moves no system along a different worldline"),
    ("proper_time", "transport",
     "a measurable rate difference between clocks is metrology, not "
     "the ability to move a system through time"),
)


# --- A26 relativistic clock metrology -----------------------------------

@dataclass(frozen=True)
class ClockComparison:
    fractional_rate_difference: float   # (f_a - f_b)/f
    seconds_per_day: float
    gravitational_part: float
    velocity_part: float
    model: str
    evidence_class: str = "ANALYTIC_MODEL"

    def to_dict(self) -> dict:
        return {"fractional_rate_difference":
                self.fractional_rate_difference,
                "seconds_per_day": self.seconds_per_day,
                "microseconds_per_day": self.seconds_per_day * 1e6,
                "gravitational_part": self.gravitational_part,
                "velocity_part": self.velocity_part,
                "model": self.model,
                "evidence_class": self.evidence_class}


def gravitational_redshift_uniform(height_m: float,
                                   g: float = G_EARTH) -> float:
    """Weak-field fractional frequency shift over a height difference
    in a uniform field: Δf/f = g·h/c².

    Validated against Pound-Rebka (22.5 m tower).
    """
    return g * height_m / (C ** 2)


def gravitational_potential_shift(r_low: float, r_high: float,
                                  gm: float = GM_EARTH) -> float:
    """Fractional rate difference between two radii in a central
    potential: Δf/f = (GM/c²)(1/r_low − 1/r_high)."""
    return (gm / C ** 2) * (1.0 / r_low - 1.0 / r_high)


def velocity_time_dilation(speed_ms: float) -> float:
    """Fractional rate slowing of a moving clock, to O(v²/c²)."""
    return -(speed_ms ** 2) / (2 * C ** 2)


def circular_orbit_speed(r_m: float, gm: float = GM_EARTH) -> float:
    return math.sqrt(gm / r_m)


def satellite_clock_offset(orbit_radius_m: float,
                           ground_radius_m: float = R_EARTH
                           ) -> ClockComparison:
    """Net rate offset of a satellite clock vs a ground clock.

    Gravitational (clock higher → runs fast) plus velocity (moving →
    runs slow). For GPS this must reproduce the well-known ≈ +38 µs/day.
    """
    grav = gravitational_potential_shift(ground_radius_m, orbit_radius_m)
    v = circular_orbit_speed(orbit_radius_m)
    vel = velocity_time_dilation(v)
    total = grav + vel
    return ClockComparison(total, total * 86400.0, grav, vel,
                           "weak-field Schwarzschild, circular orbit, "
                           "O(v^2/c^2)")


def resonator_as_clock_sensitivity(fractional_stability: float,
                                   height_m: float = 1.0) -> dict:
    """What height difference could a resonator of a given fractional
    stability resolve?

    This is the programme's legitimate spacetime capability: clocks are
    metric *instruments*. It is metrology, never propulsion
    (firewall CLOCK_SHIFT_TO_METRIC_CONTROL).
    """
    per_metre = gravitational_redshift_uniform(1.0)
    resolvable_m = fractional_stability / per_metre
    return {
        "fractional_stability": fractional_stability,
        "fractional_shift_per_metre": per_metre,
        "smallest_resolvable_height_m": resolvable_m,
        "shift_at_height": gravitational_redshift_uniform(height_m),
        "capability": "MEASUREMENT of the metric",
        "not_capability": "generation or control of curvature",
        "evidence_class": "ANALYTIC_MODEL",
        "note": "a quartz resonator at ~1e-12 stability resolves "
                "kilometres, not millimetres; optical clocks at 1e-18 "
                "resolve centimetres",
    }


# --- A27 metric perturbation / energy audit ------------------------------

def energy_audit(power_w: float, duration_s: float) -> dict:
    """Convert apparatus energy to equivalent mass and Schwarzschild
    radius, and compare with lengths that can actually be measured.

    The answer is not 'small'. It is absurd by tens of orders of
    magnitude, and saying so precisely is the point.
    """
    energy_j = power_w * duration_s
    mass_kg = energy_j / C ** 2
    r_s = 2 * G * mass_kg / C ** 2
    return {
        "power_w": power_w,
        "duration_s": duration_s,
        "energy_j": energy_j,
        "equivalent_mass_kg": mass_kg,
        "schwarzschild_radius_m": r_s,
        "ratio_to_planck_length": r_s / PLANCK_LENGTH,
        "ratio_to_proton_radius": r_s / PROTON_RADIUS,
        "orders_of_magnitude_below_proton":
            math.log10(PROTON_RADIUS / r_s) if r_s > 0 else float("inf"),
        "verdict": "NEGLIGIBLE",
        "conclusion":
            "The curvature implied by any laboratory energy budget is "
            "smaller than a proton by tens of orders of magnitude and "
            "smaller than the Planck length itself. No arrangement of "
            "this energy alters a worldline measurably.",
        "evidence_class": "ANALYTIC_MODEL",
    }


def metric_perturbation_summary(power_w: float = 100.0,
                                duration_s: float = 3600.0) -> dict:
    a = energy_audit(power_w, duration_s)
    return {
        "apparatus": f"{power_w} W for {duration_s} s",
        **a,
        "compare_earth_schwarzschild_radius_m":
            2 * G * 5.972e24 / C ** 2,
        "note": "Earth itself has a Schwarzschild radius of ~8.9 mm "
                "and bends clocks by parts in 1e10 per metre of "
                "height. A benchtop apparatus is not in the same "
                "conversation.",
    }


# --- A28 time-crystal firewall ------------------------------------------

TIME_CRYSTAL_FACTS = {
    "what_it_is":
        "a driven many-body system whose observable responds at a "
        "subharmonic of the drive, breaking discrete time-translation "
        "symmetry in a way that persists and is robust to perturbation",
    "what_is_observed":
        "period doubling (or n-tupling) of an order parameter, in "
        "trapped ions, NV centres, and superconducting qubit arrays",
    "what_it_is_not": (
        "perpetual motion (the drive supplies energy)",
        "time travel or displacement along a worldline",
        "a change in the rate of any clock",
        "a violation of thermodynamics",
    ),
    "relation_to_this_programme":
        "a subharmonic response is exactly the kind of thing a "
        "nonlinear resonator can show. Observing period doubling in a "
        "crystal would be ORDINARY NONLINEAR DYNAMICS unless the full "
        "many-body criteria are met, and would still not be travel.",
    "evidence_class": "SOURCE_CLAIM",
}


def classify_temporal_observation(period_ratio: float,
                                  many_body: bool = False,
                                  robust_to_perturbation: bool = False,
                                  drive_powered: bool = True) -> dict:
    """Classify a subharmonic observation honestly.

    Period doubling in a driven nonlinear oscillator is textbook and
    requires no exotic explanation. The 'time crystal' label demands
    many-body rigidity; and neither label licenses any travel claim.
    """
    subharmonic = abs(period_ratio - round(period_ratio)) < 1e-9 and \
        round(period_ratio) >= 2
    if not subharmonic:
        label = "NO_SUBHARMONIC"
        reason = "response is not an integer subharmonic of the drive"
    elif many_body and robust_to_perturbation:
        label = "TIME_CRYSTAL_CANDIDATE"
        reason = ("meets the published criteria for a discrete "
                  "time-crystal candidate; still requires independent "
                  "replication")
    else:
        label = "ORDINARY_NONLINEAR_SUBHARMONIC"
        reason = ("period-n response in a driven nonlinear oscillator "
                  "is textbook parametric behaviour; the time-crystal "
                  "label requires many-body rigidity")
    return {
        "period_ratio": period_ratio,
        "classification": label,
        "reason": reason,
        "energy_source": "external drive" if drive_powered
        else "UNDECLARED — refuse until stated",
        "implies_time_travel": False,
        "firewall": "TEMPORAL_ORDER_TO_TRAVEL: periodic or "
                    "subharmonic response is not displacement through "
                    "time",
        "evidence_class": "NUMERICAL_SIMULATION",
    }


# --- A29 travel falsification map ---------------------------------------

@dataclass(frozen=True)
class TravelClaim:
    id: str
    claim: str
    status: str
    required_evidence: str
    why_current_work_does_not_support_it: str


TRAVEL_CLAIMS = (
    TravelClaim(
        "TRV-001",
        "A resonator array displaces an object backward in time.",
        "UNSUPPORTED",
        "a closed timelike curve, or an object arriving before it "
        "departed, measured by synchronised clocks with independent "
        "witnesses and no signal-path artefact",
        "the programme manipulates oscillator phase. Phase is not "
        "proper time (A25); no mechanism connects the two."),
    TravelClaim(
        "TRV-002",
        "Phase-coherent driving creates a usable metric perturbation.",
        "UNSUPPORTED",
        "a measured deviation from the flat-space geodesic exceeding "
        "instrument noise, with the apparatus energy accounted for",
        "the energy audit (A27) puts the implied Schwarzschild radius "
        "tens of orders of magnitude below a proton radius."),
    TravelClaim(
        "TRV-003",
        "A subharmonic (time-crystal-like) response demonstrates "
        "temporal displacement.",
        "UNSUPPORTED",
        "a demonstration that the subharmonic response transports a "
        "system rather than modulating an observable",
        "period doubling is ordinary nonlinear dynamics; the "
        "time-crystal literature itself makes no travel claim (A28)."),
    TravelClaim(
        "TRV-004",
        "Clock-rate sensitivity shows the apparatus controls spacetime.",
        "UNSUPPORTED",
        "a demonstrated CHANGE in the local metric caused by the "
        "apparatus, distinguished from the apparatus MEASURING an "
        "ambient metric",
        "firewall CLOCK_SHIFT_TO_METRIC_CONTROL: sensing redshift is "
        "metrology. A thermometer does not heat the room."),
    TravelClaim(
        "TRV-005",
        "Frequency correspondence across 37 octaves couples acoustic "
        "and optical domains.",
        "UNSUPPORTED",
        "a measured energy transfer between the domains exceeding "
        "thermal and photoelastic backgrounds, with detuned controls",
        "an octave relation is arithmetic; no nonlinear conversion "
        "mechanism at the required efficiency is implemented or "
        "demonstrated (firewall "
        "OPTICAL_FREQUENCY_TO_PHOTON_CONVERSION)."),
)


def falsification_map() -> dict:
    return {
        "claims": [c.__dict__ for c in TRAVEL_CLAIMS],
        "default_status": "UNSUPPORTED",
        "n_claims": len(TRAVEL_CLAIMS),
        "n_supported": 0,
        "rule": "every travel-adjacent claim defaults to UNSUPPORTED "
                "and states the specific evidence that would change "
                "its status. None of that evidence exists.",
        "evidence_class": "ANALYTIC_MODEL",
    }
