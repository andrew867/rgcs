"""P07 — geometry-to-gravity arithmetic firewall.

Any claimed metric effect has to survive the chain

    u_a(t) -> T_munu(x,t) -> g_munu(x,t)

and the first link is just energy. Whatever an apparatus does
electrically, elastically, acoustically or optically, its
gravitational signature is set by its stress-energy, and the leading
term is E/c^2.

That is a brutally small number. A joule is 1.1e-17 kg. The whole
point of this module is to compute the gap between what a bench
apparatus could produce and what any real instrument could detect,
and to report it in orders of magnitude rather than in adjectives.

The verdict is not an opinion. ``REFUSED_BY_ARITHMETIC`` is returned
when the predicted effect is so far below the sensor floor that no
integration time within the age of the universe would close it, and
that is the expected outcome for every configuration this programme
can build.

Sensor floors are literature-class figures for the best instruments
that exist, not for equipment this project owns. Using the *best*
instrument in the world makes the refusal stronger, not weaker.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict

from . import GRAVITY_STATUSES

# Physical constants (CODATA).
C = 299_792_458.0                 # m/s, exact
G = 6.674_30e-11                  # m^3 kg^-1 s^-2
G_EARTH = 9.806_65                # m/s^2, standard gravity

#: Best-in-world sensor floors, with what they are.
SENSOR_FLOORS = {
    "OPTICAL_CLOCK_FRACTIONAL": {
        "value": 1e-19,
        "unit": "fractional frequency",
        "note": "state-of-the-art optical lattice clock comparison "
                "after long averaging; ~1e-18 is routine, 1e-19 is "
                "the published frontier",
    },
    "CAESIUM_FRACTIONAL": {
        "value": 1e-16,
        "unit": "fractional frequency",
        "note": "primary caesium standard after a day of averaging",
    },
    "OCXO_FRACTIONAL": {
        "value": 1e-12,
        "unit": "fractional frequency",
        "note": "good oven-controlled quartz, short-term",
    },
    "SUPERCONDUCTING_GRAVIMETER": {
        "value": 1e-11,
        "unit": "m/s^2",
        "note": "superconducting gravimeter, long integration; ~1 nGal",
    },
    "ATOM_INTERFEROMETER": {
        "value": 1e-9,
        "unit": "m/s^2",
        "note": "transportable atom-interferometric gravimeter",
    },
    "TORSION_BALANCE_FORCE": {
        "value": 1e-15,
        "unit": "N",
        "note": "state-of-the-art torsion balance, sub-femtonewton "
                "after long integration",
    },
    "LIGO_STRAIN": {
        "value": 1e-23,
        "unit": "dimensionless strain",
        "note": "kilometre-scale interferometer at best sensitivity; "
                "included because it is the most sensitive "
                "displacement measurement humans have built",
    },
}


class GravityRefused(RuntimeError):
    """Raised when a metric claim is refused by arithmetic."""


# --------------------------------------------------------------------
# Energy budget
# --------------------------------------------------------------------

@dataclass(frozen=True)
class EnergyBudget:
    """Every ordinary stress-energy contribution of an apparatus state.

    All terms in joules. The point of enumerating them separately is
    that a reader can check none was inflated: the total is what the
    gravitational estimate uses.
    """

    label: str
    electromagnetic_j: float = 0.0
    elastic_strain_j: float = 0.0
    acoustic_j: float = 0.0
    thermal_j: float = 0.0
    kinetic_j: float = 0.0
    stored_electrical_j: float = 0.0
    optical_j: float = 0.0

    @property
    def total_j(self) -> float:
        return (self.electromagnetic_j + self.elastic_strain_j
                + self.acoustic_j + self.thermal_j + self.kinetic_j
                + self.stored_electrical_j + self.optical_j)

    @property
    def equivalent_mass_kg(self) -> float:
        return self.total_j / (C * C)

    @property
    def schwarzschild_radius_m(self) -> float:
        """r_s = 2GE/c^4. Included to make the scale visceral."""
        return 2.0 * G * self.total_j / (C ** 4)

    def as_record(self) -> dict:
        d = asdict(self)
        d["total_j"] = self.total_j
        d["equivalent_mass_kg"] = self.equivalent_mass_kg
        d["schwarzschild_radius_m"] = self.schwarzschild_radius_m
        return d


#: Apparatus configurations spanning the plausible range, from a
#: modest bench build to a deliberately absurd upper bound.
CONFIGURATIONS = {
    "HANDHELD_CRYSTAL": EnergyBudget(
        label="hand-held quartz, strain and charge only",
        elastic_strain_j=1e-6, acoustic_j=1e-9),
    "BENCH_COIL_DRIVE": EnergyBudget(
        label="dual-helix coil, 10 W drive, 1 s, plus stored field",
        electromagnetic_j=10.0, stored_electrical_j=1e-3,
        thermal_j=9.0),
    "HIGH_POWER_PULSE": EnergyBudget(
        label="1 kJ pulsed discharge into the coil",
        electromagnetic_j=1000.0, stored_electrical_j=1000.0,
        thermal_j=900.0),
    "ABSURD_UPPER_BOUND": EnergyBudget(
        label="1 MJ, far beyond anything this programme could build "
              "or safely operate",
        electromagnetic_j=1e6, stored_electrical_j=1e6),
}


# --------------------------------------------------------------------
# Weak-field predictions
# --------------------------------------------------------------------

def gravitational_acceleration(mass_kg: float, r_m: float) -> float:
    """a = Gm/r^2."""
    if r_m <= 0:
        raise ValueError("distance must be positive")
    return G * mass_kg / (r_m * r_m)


def potential_fractional_shift(mass_kg: float, r_m: float) -> float:
    """Fractional clock shift from the apparatus's own potential.

    df/f = dPhi/c^2 = Gm/(r c^2).
    """
    if r_m <= 0:
        raise ValueError("distance must be positive")
    return G * mass_kg / (r_m * C * C)


def height_fractional_shift(delta_h_m: float) -> float:
    """df/f = g*dh/c^2 — the Earth-field reference for comparison.

    Included so a reader can see that simply lifting a clock by a
    millimetre produces a vastly larger shift than the entire
    apparatus does.
    """
    return G_EARTH * delta_h_m / (C * C)


def orders_of_magnitude_gap(predicted: float, floor: float) -> float:
    """How many decades the prediction sits below the sensor floor.

    Positive means undetectable by that margin.
    """
    if predicted <= 0:
        return math.inf
    return math.log10(floor / predicted)


# --------------------------------------------------------------------
# The verdict
# --------------------------------------------------------------------

@dataclass(frozen=True)
class GravityVerdict:
    configuration: str
    total_energy_j: float
    equivalent_mass_kg: float
    schwarzschild_radius_m: float
    distance_m: float
    predicted_acceleration_ms2: float
    predicted_fractional_shift: float
    acceleration_floor: float
    clock_floor: float
    acceleration_gap_decades: float
    clock_gap_decades: float
    equivalent_height_mm: float
    status: str
    note: str

    def as_record(self) -> dict:
        return asdict(self)


def assess(config: str, *, distance_m: float = 0.1,
           acceleration_sensor: str = "SUPERCONDUCTING_GRAVIMETER",
           clock_sensor: str = "OPTICAL_CLOCK_FRACTIONAL"
           ) -> GravityVerdict:
    """Compute the gap for one apparatus configuration."""
    if config not in CONFIGURATIONS:
        raise ValueError(f"unknown configuration {config!r}")
    budget = CONFIGURATIONS[config]
    m = budget.equivalent_mass_kg

    a = gravitational_acceleration(m, distance_m)
    df = potential_fractional_shift(m, distance_m)

    a_floor = SENSOR_FLOORS[acceleration_sensor]["value"]
    c_floor = SENSOR_FLOORS[clock_sensor]["value"]

    a_gap = orders_of_magnitude_gap(a, a_floor)
    c_gap = orders_of_magnitude_gap(df, c_floor)

    # How high would you have to lift a clock to get the same shift?
    equiv_h_m = df * C * C / G_EARTH

    best_gap = min(a_gap, c_gap)
    if best_gap > 6:
        status = "REFUSED_BY_ARITHMETIC"
        note = (
            f"the predicted effect is {best_gap:.1f} orders of "
            f"magnitude below the best instrument that exists. "
            f"Averaging reduces white noise as sqrt(t), so closing "
            f"{best_gap:.1f} decades would need about 10^"
            f"{2 * best_gap:.0f} seconds of integration -- "
            f"unreachable regardless of patience or funding.")
    elif best_gap > 0:
        status = "BELOW_SENSOR_FLOOR"
        note = (
            f"below the floor by {best_gap:.1f} decades; longer "
            f"integration could in principle help. Read this "
            f"carefully: the channel that comes closest is "
            f"ACCELERATION, which is ordinary Newtonian attraction of "
            f"the equivalent mass at close range, not a metric "
            f"effect. The clock channel remains "
            f"{c_gap:.1f} decades away. Reaching even this point "
            f"requires an energy this programme cannot build or "
            f"safely operate.")
    else:
        status = "CONVENTIONAL_EFFECT_MEASURABLE"
        note = ("a conventional gravitational effect of this "
                "apparatus would be measurable; this would still be "
                "ordinary Newtonian attraction, not metric "
                "engineering")

    assert status in GRAVITY_STATUSES
    return GravityVerdict(
        configuration=config, total_energy_j=budget.total_j,
        equivalent_mass_kg=m,
        schwarzschild_radius_m=budget.schwarzschild_radius_m,
        distance_m=distance_m, predicted_acceleration_ms2=a,
        predicted_fractional_shift=df, acceleration_floor=a_floor,
        clock_floor=c_floor, acceleration_gap_decades=a_gap,
        clock_gap_decades=c_gap,
        equivalent_height_mm=equiv_h_m * 1000.0,
        status=status, note=note)


def full_assessment(distance_m: float = 0.1) -> dict:
    """Every configuration, with the headline comparison."""
    rows = {c: assess(c, distance_m=distance_m).as_record()
            for c in CONFIGURATIONS}
    refused = [c for c, r in rows.items()
               if r["status"] == "REFUSED_BY_ARITHMETIC"]
    # The comparison that makes the scale intuitive.
    mm_shift = height_fractional_shift(1e-3)
    best = max(rows.values(), key=lambda r: r["predicted_fractional_shift"])
    return {
        "configurations": rows,
        "configurations_refused_by_arithmetic": refused,
        "all_refused": len(refused) == len(rows),
        "reference_1mm_height_shift": mm_shift,
        "best_configuration_shift": best["predicted_fractional_shift"],
        "ratio_1mm_lift_over_best_apparatus":
            mm_shift / best["predicted_fractional_shift"],
        "verdict": (
            "Every configuration, including a deliberately absurd "
            "one-megajoule upper bound far beyond anything this "
            "programme could build or safely operate, is refused by "
            "arithmetic. Raising a clock by one millimetre against "
            "Earth's field produces a larger fractional shift than "
            "the entire apparatus does by "
            f"{mm_shift / best['predicted_fractional_shift']:.1e} "
            "times. The apparatus is not competing with a subtle "
            "effect; it is competing with the floor of the building."),
        "consequence": (
            "No metric-actuation claim can be tested by this "
            "apparatus, at any energy it could reach, with any "
            "instrument that exists. This is the strongest form of "
            "negative result the programme can produce: it does not "
            "depend on the crystal, the geometry, the drive pattern "
            "or the source corpus being right or wrong."),
        "what_this_does_not_say": (
            "It does not say relativity is untestable at bench "
            "scale. Optical clocks resolve centimetre height "
            "differences routinely. It says the apparatus's OWN "
            "stress-energy is irrelevant, so any real experiment here "
            "measures Earth's field, not the device's."),
    }


def refuse_metric_actuation(*args, **kwargs):
    """Always refuses. There is no path from this apparatus to g_munu."""
    raise GravityRefused(
        "metric actuation is refused by arithmetic, not by policy. "
        "The apparatus's stress-energy contributes a gravitational "
        "signature tens of orders of magnitude below the most "
        "sensitive instrument ever built, at every energy it could "
        "reach (r7 FORBIDDEN_COLLAPSES: "
        "STORED_ENERGY_IS_SPACETIME_CURVATURE).")
