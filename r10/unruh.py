"""P18 — Unruh temperature, Rindler horizons, and the scale refusal.

The Unruh effect is real, conventional, and forty years old: a
detector with uniform proper acceleration ``a`` through the Minkowski
vacuum responds as if immersed in a thermal bath at

    T = hbar * a / (2 * pi * c * k_B)

That is the whole of the physics this module implements. Everything
else here is arithmetic about how big ``a`` has to be, because the
prefactor is where the argument actually lives.

The coefficient ``hbar / (2 pi c k_B)`` is about 4.06e-21 K per
(m/s^2). Inverting it: **one kelvin of Unruh temperature requires a
proper acceleration of about 2.47e20 m/s^2**, and a millikelvin still
requires about 2.47e17 m/s^2. Earth's surface gravity gives 3.98e-20
K. A laboratory ultracentrifuge at ~1e6 m/s^2 gives ~4e-15 K. There
is no mechanical apparatus, and no plausible one, whose Unruh
temperature is measurable.

The honest complication, and it is worth stating rather than
suppressing: a *single electron* in the field of a record-intensity
laser does reach ~1e26 m/s^2, for an Unruh temperature of order 1e6 K.
That is not absurd at all, and it is exactly why serious proposals to
detect the Unruh effect use extreme laser fields (Chen & Tajima, PRL
83, 256 (1999)) rather than centrifuges. So the scale argument must be
made precisely: bulk mechanical acceleration is hopeless by fourteen
orders of magnitude; single-charge acceleration in extreme fields is
not hopeless as a *detection* target.

Neither case makes it an energy source, and that is a separate
argument with a separate number. At 1e23 W/cm^2 the driving field
carries an energy density of order 1e18 J/m^3 while the Unruh bath it
induces carries of order 1e8 J/m^3 -- ten orders of magnitude less.
The bath is not free; it is a very expensive by-product of the agent
doing the accelerating, it exists only in the accelerated frame, and
an inertial observer looking at the same region sees vacuum. There is
no cycle here that nets energy, and ``refuse_unruh_as_energy_source``
raises unconditionally.

Constants are CODATA / exact-SI values with sources named. Nothing in
this module is a measurement: this programme owns no accelerator, no
high-field laser and no Unruh-DeWitt detector of any kind.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# --- constants, each with its provenance --------------------------------

#: Speed of light in vacuum, m/s. Exact by SI definition (1983 CGPM).
C_M_PER_S = 299_792_458.0

#: Planck constant, J s. Exact by SI definition since the 2019
#: redefinition (SI Brochure, 9th ed.).
PLANCK_J_S = 6.626_070_15e-34

#: Reduced Planck constant, J s = h / (2 pi). CODATA 2018/2022 value,
#: exact up to the truncation shown.
HBAR_J_S = PLANCK_J_S / (2.0 * math.pi)

#: Boltzmann constant, J/K. Exact by SI definition since 2019.
BOLTZMANN_J_PER_K = 1.380_649e-23

#: Elementary charge, C. Exact by SI definition since 2019.
ELEMENTARY_CHARGE_C = 1.602_176_634e-19

#: Electron rest mass, kg. CODATA 2018 recommended value,
#: 9.109_383_7015(28)e-31 kg.
ELECTRON_MASS_KG = 9.109_383_7015e-31

#: Vacuum electric permittivity, F/m. CODATA 2018 recommended value,
#: 8.854_187_8128(13)e-12 F/m. No longer exact after the 2019
#: redefinition, since it is now tied to the measured fine-structure
#: constant.
EPSILON_0_F_PER_M = 8.854_187_8128e-12

#: Standard acceleration of gravity, m/s^2. Conventional exact value
#: (3rd CGPM, 1901).
STANDARD_GRAVITY_M_PER_S2 = 9.806_65

#: Radiation (Stefan-Boltzmann energy-density) constant,
#: a = 4*sigma/c = 7.565_733e-16 J m^-3 K^-4, derived from the exact
#: Stefan-Boltzmann constant sigma = 5.670_374_419e-8 W m^-2 K^-4
#: (CODATA; exact given the 2019 SI).
STEFAN_BOLTZMANN_W_PER_M2_K4 = 5.670_374_419e-8
RADIATION_CONSTANT_J_PER_M3_K4 = (
    4.0 * STEFAN_BOLTZMANN_W_PER_M2_K4 / C_M_PER_S)

#: The Unruh coefficient, K per (m/s^2). This single number is the
#: whole scale argument: hbar / (2 pi c k_B) ~ 4.06e-21.
UNRUH_COEFFICIENT_K_PER_M_PER_S2 = (
    HBAR_J_S / (2.0 * math.pi * C_M_PER_S * BOLTZMANN_J_PER_K))

#: Primary sources for the effect itself.
UNRUH_SOURCES = (
    "Fulling, Phys. Rev. D 7, 2850 (1973)",
    "Davies, J. Phys. A 8, 609 (1975)",
    "Unruh, Phys. Rev. D 14, 870 (1976)",
    "Crispino, Higuchi & Matsas, Rev. Mod. Phys. 80, 787 (2008) "
    "(review)",
)


class UnruhClaimRefused(RuntimeError):
    """Raised when an Unruh/Rindler claim is refused."""


# --- the conventional calculators ---------------------------------------


def unruh_temperature_k(proper_acceleration_m_per_s2: float) -> float:
    """T = hbar * a / (2 pi c k_B), in kelvin."""
    a = float(proper_acceleration_m_per_s2)
    if a < 0:
        raise ValueError("proper acceleration magnitude must be "
                         "non-negative")
    return UNRUH_COEFFICIENT_K_PER_M_PER_S2 * a


def acceleration_for_temperature_m_per_s2(temperature_k: float) -> float:
    """The proper acceleration whose Unruh temperature is T.

    The inverse of ``unruh_temperature_k``. This is the function that
    produces the headline: T = 1 K needs a ~ 2.47e20 m/s^2.
    """
    t = float(temperature_k)
    if t < 0:
        raise ValueError("temperature must be non-negative kelvin")
    return t / UNRUH_COEFFICIENT_K_PER_M_PER_S2


def rindler_horizon_distance_m(proper_acceleration_m_per_s2: float
                               ) -> float:
    """d = c^2 / a: the Rindler horizon behind a uniformly accelerated
    observer.

    Signals emitted beyond this proper distance behind the observer
    never catch up while the acceleration is maintained. The relation
    is a hyperbola, not a coincidence: ``d * a = c^2`` exactly, which
    the tests check as an invariant.
    """
    a = float(proper_acceleration_m_per_s2)
    if a <= 0:
        raise ValueError(
            "an unaccelerated observer has no Rindler horizon; the "
            "distance diverges as a -> 0")
    return C_M_PER_S ** 2 / a


def rindler_worldline(proper_time_s: float,
                      proper_acceleration_m_per_s2: float
                      ) -> tuple[float, float]:
    """(t, x) in the inertial frame for proper time tau on the
    hyperbolic worldline::

        x = (c^2 / a) * cosh(a * tau / c)
        t = (c / a)   * sinh(a * tau / c)

    Parameterised so that ``x(0) = c^2 / a`` and ``t(0) = 0``.
    """
    a = float(proper_acceleration_m_per_s2)
    if a <= 0:
        raise ValueError("proper acceleration must be positive")
    eta = a * float(proper_time_s) / C_M_PER_S
    return ((C_M_PER_S / a) * math.sinh(eta),
            (C_M_PER_S ** 2 / a) * math.cosh(eta))


def rapidity(proper_time_s: float,
             proper_acceleration_m_per_s2: float) -> float:
    """Dimensionless rapidity ``a*tau/c`` accumulated in proper time."""
    a = float(proper_acceleration_m_per_s2)
    if a <= 0:
        raise ValueError("proper acceleration must be positive")
    return a * float(proper_time_s) / C_M_PER_S


def characteristic_proper_time_s(proper_acceleration_m_per_s2: float
                                 ) -> float:
    """c / a: the proper time in which rapidity reaches 1.

    At a = 2.47e20 m/s^2 this is ~1.2e-12 s, which is the second half
    of the laboratory problem: even if the acceleration existed, it
    would have to be *uniform* for long enough that the detector's
    response thermalises, and the natural timescale is picoseconds.
    """
    a = float(proper_acceleration_m_per_s2)
    if a <= 0:
        raise ValueError("proper acceleration must be positive")
    return C_M_PER_S / a


def thermal_energy_density_j_per_m3(temperature_k: float) -> float:
    """Blackbody energy density ``a_rad * T^4``, J/m^3.

    Used only to compare the induced bath against the field that
    induces it. Treating the Unruh bath as an exactly thermal photon
    gas is the most generous assumption available for that comparison,
    which is why it is used here.
    """
    t = float(temperature_k)
    if t < 0:
        raise ValueError("temperature must be non-negative kelvin")
    return RADIATION_CONSTANT_J_PER_M3_K4 * t ** 4


# --- how you get a large acceleration at all ----------------------------


def field_from_intensity_v_per_m(intensity_w_per_m2: float) -> float:
    """Peak electric field of a plane wave: E = sqrt(2 I / (eps0 c)).

    Standard relation between cycle-averaged intensity and peak field
    amplitude for a linearly polarised plane wave in vacuum.
    """
    i = float(intensity_w_per_m2)
    if i < 0:
        raise ValueError("intensity must be non-negative")
    return math.sqrt(2.0 * i / (EPSILON_0_F_PER_M * C_M_PER_S))


def electron_acceleration_in_field_m_per_s2(field_v_per_m: float) -> float:
    """a = eE/m for an electron. Non-relativistic estimate.

    Deliberately the *simple* estimate, and the caveat matters: at
    these field strengths the electron is violently relativistic
    within a fraction of an optical cycle, so the instantaneous proper
    acceleration differs from eE/m by gamma-dependent factors of order
    unity to order ten. That is irrelevant to a comparison spanning
    fourteen orders of magnitude, and it would be relevant to any
    precision claim, so no precision claim is made.
    """
    e = float(field_v_per_m)
    if e < 0:
        raise ValueError("field magnitude must be non-negative")
    return ELEMENTARY_CHARGE_C * e / ELECTRON_MASS_KG


#: Record focused laser intensity, W/cm^2. 1.1e23 W/cm^2 reported at
#: CoReLS: Yoon, Kim, Choi, Sung, Lee, Lee & Nam, Optica 8, 630
#: (2021). Quoted as an order-of-magnitude anchor for the largest
#: acceleration a charged particle has plausibly experienced in a
#: laboratory.
RECORD_LASER_INTENSITY_W_PER_CM2 = 1.1e23


def record_laser_electron_acceleration_m_per_s2() -> float:
    """Electron acceleration at the record laboratory laser intensity.

    Computed, not asserted: intensity -> field -> eE/m. Comes out at
    ~1.6e26 m/s^2.
    """
    i_si = RECORD_LASER_INTENSITY_W_PER_CM2 * 1e4  # W/cm^2 -> W/m^2
    return electron_acceleration_in_field_m_per_s2(
        field_from_intensity_v_per_m(i_si))


# --- the scale table ----------------------------------------------------


@dataclass(frozen=True)
class AccelerationScale:
    """One row of the scale comparison. A source is mandatory."""

    label: str
    acceleration_m_per_s2: float
    kind: str          # BULK_MECHANICAL | SINGLE_CHARGE | REQUIREMENT
    source: str

    def __post_init__(self) -> None:
        if self.acceleration_m_per_s2 <= 0:
            raise ValueError(f"{self.label!r}: acceleration must be "
                             f"positive")
        if not self.source.strip():
            raise ValueError(
                f"{self.label!r}: a scale-table row without a source "
                f"is an invented number. Refused.")
        if self.kind not in ("BULK_MECHANICAL", "SINGLE_CHARGE",
                             "REQUIREMENT"):
            raise ValueError(f"{self.label!r}: unknown kind "
                             f"{self.kind!r}")

    @property
    def unruh_temperature_k(self) -> float:
        return unruh_temperature_k(self.acceleration_m_per_s2)

    @property
    def rindler_horizon_m(self) -> float:
        return rindler_horizon_distance_m(self.acceleration_m_per_s2)


def acceleration_scale_table() -> tuple[AccelerationScale, ...]:
    """Available accelerations against required ones.

    Rows are computed where they can be computed. The two REQUIREMENT
    rows are the inverse-function results, not independent inputs, so
    that the table cannot drift away from the formula it is comparing
    against.
    """
    return (
        AccelerationScale(
            "Earth surface gravity", STANDARD_GRAVITY_M_PER_S2,
            "BULK_MECHANICAL",
            "standard gravity, 3rd CGPM (1901), conventional exact "
            "value"),
        AccelerationScale(
            "sustained human tolerance, ~9 g", 9.0 * 9.80665,
            "BULK_MECHANICAL",
            "aerospace physiology, order-of-magnitude"),
        AccelerationScale(
            "laboratory ultracentrifuge rotor, ~1e5 g", 1e6,
            "BULK_MECHANICAL",
            "commercial ultracentrifuge specifications, "
            "order-of-magnitude (~1e6 g-force class rotors)"),
        AccelerationScale(
            "electron in a 100 GV/m plasma-wakefield gradient",
            electron_acceleration_in_field_m_per_s2(1e11),
            "SINGLE_CHARGE",
            "gradient scale from Blumenfeld et al., Nature 445, 741 "
            "(2007) (energy doubling at ~52 GV/m); acceleration "
            "computed here as eE/m"),
        AccelerationScale(
            "electron at record focused laser intensity "
            "(1.1e23 W/cm^2)",
            record_laser_electron_acceleration_m_per_s2(),
            "SINGLE_CHARGE",
            "intensity from Yoon et al., Optica 8, 630 (2021); field "
            "and acceleration computed here from that intensity"),
        AccelerationScale(
            "REQUIRED for T = 1 mK",
            acceleration_for_temperature_m_per_s2(1e-3),
            "REQUIREMENT",
            "inverse of the Unruh relation, computed in this module"),
        AccelerationScale(
            "REQUIRED for T = 1 K",
            acceleration_for_temperature_m_per_s2(1.0),
            "REQUIREMENT",
            "inverse of the Unruh relation, computed in this module"),
    )


def scale_verdict() -> dict:
    """The P18 headline, with the honest complication kept in.

    A single number is not enough here, because the bulk-mechanical
    case and the single-charge case have opposite answers and running
    them together would misrepresent both.
    """
    table = acceleration_scale_table()
    by_label = {r.label: r for r in table}
    need_1k = by_label["REQUIRED for T = 1 K"].acceleration_m_per_s2
    centrifuge = by_label[
        "laboratory ultracentrifuge rotor, ~1e5 g"]
    laser = by_label[
        "electron at record focused laser intensity (1.1e23 W/cm^2)"]
    return {
        "coefficient_k_per_m_per_s2": UNRUH_COEFFICIENT_K_PER_M_PER_S2,
        "acceleration_for_1_k": need_1k,
        "acceleration_for_1_mk":
            by_label["REQUIRED for T = 1 mK"].acceleration_m_per_s2,
        "rindler_horizon_at_1_k_m":
            rindler_horizon_distance_m(need_1k),
        "characteristic_time_at_1_k_s":
            characteristic_proper_time_s(need_1k),
        "bulk_mechanical_shortfall":
            need_1k / centrifuge.acceleration_m_per_s2,
        "bulk_mechanical_temperature_k": centrifuge.unruh_temperature_k,
        "single_charge_best_m_per_s2": laser.acceleration_m_per_s2,
        "single_charge_temperature_k": laser.unruh_temperature_k,
        "bulk_verdict": "HOPELESS_BY_FOURTEEN_ORDERS_OF_MAGNITUDE",
        "single_charge_verdict": "NOT_HOPELESS_AS_A_DETECTION_TARGET",
        "summary": (
            "One kelvin of Unruh temperature costs about 2.5e20 m/s^2. "
            "No bulk mechanical apparatus comes within fourteen orders "
            "of magnitude of that: an ultracentrifuge at 1e6 m/s^2 "
            "sits at about 4e-15 K. A single electron in a "
            "record-intensity laser focus does reach ~1e26 m/s^2, for "
            "an Unruh temperature of order 1e6 K, which is why "
            "detection proposals use extreme fields rather than "
            "rotating machinery. Detectability and extractability are "
            "different questions and only the first has a hopeful "
            "answer."),
        "sources": list(UNRUH_SOURCES),
        "evidence_class": "LITERATURE_CONSTANTS_AND_ARITHMETIC",
        "measured_here": "nothing",
        "what_this_does_not_say": (
            "It does not say the Unruh effect has been observed; as of "
            "the sources cited it has not been directly detected. It "
            "does not say any acceleration in this programme is "
            "nonzero in the relevant sense. It does not say a quartz "
            "resonator, a rotating mass, or any bench apparatus "
            "accesses a Rindler horizon, and it licenses no claim "
            "about coupling between acceleration and any observable "
            "measured here."),
    }


# --- the energy-source refusal -----------------------------------------


def unruh_energy_budget() -> dict:
    """Compare the induced bath against the field that induces it.

    This is the quantitative core of the refusal. It is a comparison
    of energy densities, both computed, at the most favourable
    laboratory conditions that exist.
    """
    a = record_laser_electron_acceleration_m_per_s2()
    t = unruh_temperature_k(a)
    bath = thermal_energy_density_j_per_m3(t)
    # Energy density of the driving field: u = I / c for a plane wave.
    drive = (RECORD_LASER_INTENSITY_W_PER_CM2 * 1e4) / C_M_PER_S
    return {
        "acceleration_m_per_s2": a,
        "unruh_temperature_k": t,
        "unruh_bath_energy_density_j_per_m3": bath,
        "driving_field_energy_density_j_per_m3": drive,
        "drive_to_bath_ratio": drive / bath,
        "conclusion": (
            "the field required to induce the bath carries of order "
            "1e10 times the bath's own energy density, before any "
            "question of how one would couple to the bath, extract "
            "from it, or close a cycle. The bath is a by-product of "
            "the accelerating agent and is more expensive than what it "
            "contains."),
        "frame_dependence": (
            "the bath exists in the accelerated detector's frame. An "
            "inertial observer looking at the same region of spacetime "
            "sees the Minkowski vacuum. A quantity that vanishes under "
            "a change of observer is not a fuel supply."),
        "measured_here": "nothing",
    }


def refuse_unruh_as_energy_source(*args, **kwargs):
    """Always refuses. Hard gate, no parameters, no conditions.

    Deliberately unconditional and deliberately argument-swallowing,
    so that no call site can construct a set of inputs under which the
    claim is permitted.
    """
    b = unruh_energy_budget()
    raise UnruhClaimRefused(
        "Unruh radiation as a laboratory energy source is refused. "
        "Three independent reasons, any one sufficient: "
        "(1) SCALE -- one kelvin costs ~2.5e20 m/s^2 of proper "
        "acceleration; no bulk apparatus is within fourteen orders of "
        "magnitude, and an ultracentrifuge sits at ~4e-15 K. "
        f"(2) BUDGET -- at the record laboratory laser intensity the "
        f"driving field carries ~{b['drive_to_bath_ratio']:.2g} times "
        f"the energy density of the bath it induces, so the bath is a "
        f"net cost and not a source. "
        "(3) FRAME -- the bath is a response of an accelerated "
        "detector; an inertial observer sees vacuum in the same "
        "region. Nothing that disappears under a change of observer "
        "supplies energy to a cycle. "
        "Separately: this programme owns no accelerator, no high-field "
        "laser and no Unruh-DeWitt detector, and the Unruh effect has "
        "not been directly observed by anyone.")


def refuse_horizon_as_a_place(*args, **kwargs):
    """Refuse the Rindler horizon as a location or a reservoir."""
    raise UnruhClaimRefused(
        "the Rindler horizon is not a place, a surface, or a store. It "
        "is observer-dependent: it exists relative to a particular "
        "uniformly accelerated worldline and moves with it, different "
        "observers have different horizons through the same events, "
        "and an inertial observer has none at all. Its distance c^2/a "
        "is a property of the observer's acceleration, not a boundary "
        "anything could be placed at or drawn from.")
