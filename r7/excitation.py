"""P05 — non-contact excitation and self-oscillation firewall.

A passive crystal requires an energy source. A self-oscillator requires
a loop satisfying both Barkhausen conditions:

    |A(w) beta(w)| >= 1    and    arg[A(w) beta(w)] = 2 pi n.

Both. Not either. A loop with gain 100 and 90 degrees of phase error
does not oscillate; a loop with perfect phase and gain 0.9 does not
oscillate. The pair of conditions is why an amplifier is not
automatically an oscillator, and it is why a bare crystal — which has
no amplifier at all — cannot be one.

The observation the programme has to account for is a hand-held quartz
crystal that appears to "keep going". Three ordinary energy inputs
explain it, and all three are present whenever a hand is involved:

* physiological tremor, ~8-12 Hz, broadband, always present, coupled
  straight into the specimen through the skin;
* triboelectric and contact charge from skin against quartz;
* thermal drift from a 37 C hand against a specimen at room
  temperature, which shifts the resonance while it warms.

Each is energy going in. A resonator receiving energy is showing a
FORCED_RESPONSE; a resonator with the energy removed shows a
RINGDOWN. Neither is self-oscillation. Contact also *destroys* Q:
:func:`handheld_analysis` gives the order of magnitude.

Nothing here is bench data. No crystal has been suspended, driven,
damped or measured by this programme. Coupling efficiencies are
order-of-magnitude estimates from standard acoustics and transducer
literature, and instrument-class figures are catalogue class.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict

from . import EXCITATION_STATUSES

#: Physiological (normal) tremor band, Hz. Neurophysiology literature
#: class: an involuntary 8-12 Hz oscillation present in everyone, not a
#: pathology and not removable by trying harder.
PHYSIOLOGICAL_TREMOR_HZ = (8.0, 12.0)

#: Characteristic acoustic impedances, Pa s / m (literature class).
#: The ratio is what matters: air to quartz is a mismatch of about
#: four orders of magnitude, which is why airborne sound couples into
#: a crystal so badly.
Z_AIR = 413.0
Z_QUARTZ = 15.3e6

#: Default tolerance on the Barkhausen phase condition, radians.
DEFAULT_PHASE_TOL_RAD = 0.05


class ExcitationRefused(RuntimeError):
    """Raised when an excitation claim is refused."""


# --------------------------------------------------------------------
# Loop gain and the Barkhausen pair
# --------------------------------------------------------------------

@dataclass(frozen=True)
class LoopGain:
    """The complex open-loop transfer A(w) * beta(w) at one frequency.

    Stored as magnitude and phase because that is how both Barkhausen
    conditions are stated, and because a Cartesian pair invites the
    error of checking only that the product is "big".
    """

    frequency_hz: float
    magnitude: float
    phase_rad: float
    label: str = ""

    def __post_init__(self) -> None:
        if self.frequency_hz <= 0.0:
            raise ValueError("loop gain needs a positive frequency")
        if self.magnitude < 0.0:
            raise ValueError("a gain magnitude cannot be negative")

    @property
    def real(self) -> float:
        return self.magnitude * math.cos(self.phase_rad)

    @property
    def imag(self) -> float:
        return self.magnitude * math.sin(self.phase_rad)

    def as_record(self) -> dict:
        d = asdict(self)
        d["real"] = self.real
        d["imag"] = self.imag
        d["units"] = ("frequency in Hz, magnitude dimensionless, phase "
                      "in radians")
        d["evidence_class"] = "SYNTHETIC_MODEL"
        return d


def phase_error_rad(phase_rad: float) -> float:
    """Distance from the nearest multiple of 2 pi, in radians."""
    return abs((phase_rad + math.pi) % (2.0 * math.pi) - math.pi)


def barkhausen_check(gain_magnitude: float, phase_rad: float, *,
                     phase_tol_rad: float = DEFAULT_PHASE_TOL_RAD
                     ) -> dict:
    """Both Barkhausen conditions, reported separately then combined.

    ``oscillates`` is the AND of the two. The individual flags are
    returned as well so that a near-miss is legible: a loop failing only
    on phase is a design problem, while a loop failing only on gain is
    an energy problem, and they have different fixes.
    """
    if gain_magnitude < 0.0:
        raise ValueError("a gain magnitude cannot be negative")
    if phase_tol_rad < 0.0:
        raise ValueError("phase tolerance must be non-negative")

    err = phase_error_rad(phase_rad)
    gain_ok = gain_magnitude >= 1.0
    phase_ok = err <= phase_tol_rad
    oscillates = gain_ok and phase_ok

    if oscillates:
        note = ("both conditions are met: the loop sustains "
                "oscillation, and it does so because an active element "
                "supplies the gain.")
    elif gain_ok and not phase_ok:
        note = (f"gain is sufficient but the phase misses a multiple of "
                f"2 pi by {err:.3f} rad ({math.degrees(err):.1f} deg). "
                f"Feedback at the wrong phase suppresses rather than "
                f"sustains; this loop does not oscillate.")
    elif phase_ok and not gain_ok:
        note = (f"phase is correct but |A*beta| = {gain_magnitude:.3f} "
                f"< 1, so each round trip loses energy and any "
                f"disturbance decays. This loop does not oscillate.")
    else:
        note = ("neither condition is met; the loop is doubly short of "
                "oscillating.")

    return {
        "gain_magnitude": gain_magnitude,
        "phase_rad": phase_rad,
        "phase_error_from_2pi_n_rad": err,
        "phase_tol_rad": phase_tol_rad,
        "gain_condition_met": gain_ok,
        "phase_condition_met": phase_ok,
        "oscillates": oscillates,
        "conditions_required": "BOTH",
        "note": note,
        "units": "magnitude dimensionless, phases in radians",
        "evidence_class": "DERIVED_ARITHMETIC",
    }


# --------------------------------------------------------------------
# The condition registry
# --------------------------------------------------------------------

@dataclass(frozen=True)
class ExcitationCondition:
    """One row of the core/05 condition table.

    ``can_close_loop`` is the discriminating field. It is true only for
    conditions containing an ACTIVE element — something with a power
    supply that can amplify a sensed signal and return it. Every purely
    passive or open-loop condition is false, and no amount of drive
    power changes that: an open-loop drive of a megawatt is still a
    forced response.
    """

    name: str
    supplies_energy: bool
    can_close_loop: bool
    requires_contact: bool
    #: Order-of-magnitude fraction of source energy reaching the
    #: specimen's mechanical mode. Estimates, not measurements.
    coupling_efficiency: float
    coupling_order: int
    coupling_basis: str
    note: str

    def as_record(self) -> dict:
        d = asdict(self)
        d["units"] = ("coupling_efficiency is a dimensionless energy "
                      "fraction; coupling_order is its base-10 "
                      "exponent")
        d["evidence_class"] = "SYNTHETIC_MODEL"
        return d


def _cond(name: str, supplies: bool, closes: bool, contact: bool,
          eff: float, basis: str, note: str) -> ExcitationCondition:
    order = -99 if eff <= 0.0 else int(math.floor(math.log10(eff)))
    return ExcitationCondition(
        name=name, supplies_energy=supplies, can_close_loop=closes,
        requires_contact=contact, coupling_efficiency=eff,
        coupling_order=order, coupling_basis=basis, note=note)


#: Every condition named in core/05, none omitted.
EXCITATION_CONDITIONS: dict[str, ExcitationCondition] = {
    c.name: c for c in (
        _cond(
            "HANDHELD_STRAIN_AND_CHARGE", True, False, True, 1e-3,
            "direct mechanical contact transmits well, but almost all "
            "of the tremor spectrum lies far from any MHz resonance, "
            "so the fraction reaching the mode is small",
            "a hand supplies broadband tremor energy, contact charge "
            "and heat. All three are inputs. None is a feedback loop, "
            "because a hand has no phase-locked amplifier in it."),
        _cond(
            "FREE_SUSPENSION", False, False, False, 0.0,
            "no source; a suspension is a boundary condition, not a "
            "drive",
            "the reference condition. Energy in the mode can only "
            "decrease, which is exactly what makes it the right place "
            "to measure Q."),
        _cond(
            "SOFT_SUPPORT", False, False, True, 0.0,
            "no source; a compliant mount reduces clamping loss but "
            "supplies nothing",
            "still passive. Contact is present, so contact loss is "
            "present, merely less of it than a rigid clamp."),
        _cond(
            "ELECTROSTATIC_DRIVE", True, False, False, 1e-6,
            "force scales as epsilon_0 A V^2 / (2 d^2); at kilovolts "
            "across a sub-millimetre gap this is micronewtons against "
            "a stiff quartz bar",
            "genuinely non-contact and genuinely weak. Open loop by "
            "construction unless a sensor and amplifier are added."),
        _cond(
            "MAGNETIC_COIL_DRIVE", True, False, False, 1e-4,
            "quartz is diamagnetic and essentially transparent to a "
            "coil; useful coupling requires a magnet or conductive "
            "film bonded to the specimen, which then dominates the "
            "mechanics",
            "the coil drives whatever is magnetic. If nothing on the "
            "specimen is magnetic, the coil mostly heats the room."),
        _cond(
            "ACOUSTIC_AIRBORNE", True, False, False, 1e-4,
            "intensity transmission 4 Z1 Z2 / (Z1+Z2)^2 for air into "
            "quartz is about 1e-4; most incident sound reflects off "
            "the surface",
            "the impedance mismatch is the whole story. Airborne sound "
            "is a real but very inefficient drive, and it also leaks "
            "into every other object in the room, which is why "
            "acoustic leakage is a required nuisance channel."),
        _cond(
            "ULTRASONIC_NONCONTACT", True, False, False, 1e-3,
            "same air-to-quartz mismatch, improved by proximity, "
            "focusing and frequency matching to the mode",
            "the best of the truly non-contact mechanical drives, and "
            "still open loop on its own."),
        _cond(
            "OPTICAL_PHOTOTHERMAL_OR_RADIATION_PRESSURE", True, False,
            False, 1e-9,
            "radiation pressure is P/c: one watt gives 3.3 nN. "
            "Photothermal drive is larger but works by heating, which "
            "shifts the resonance it is exciting",
            "the weakest drive in the registry by orders of magnitude, "
            "and the one whose mechanism most easily masquerades as "
            "something else, because photothermal heating changes f0."),
        _cond(
            "ACTIVE_ELECTRICAL_FEEDBACK", True, True, False, 1e-1,
            "an oscillator circuit is engineered for efficient "
            "electrical-to-mechanical transfer at the mode frequency",
            "THIS is how a quartz oscillator works: a sustaining "
            "amplifier with a power supply, phase-shifted to satisfy "
            "the Barkhausen conditions. The crystal is the frequency-"
            "selective element; the energy comes from the rail."),
        _cond(
            "ACTIVE_ACOUSTIC_FEEDBACK", True, True, False, 1e-3,
            "a microphone-amplifier-speaker loop inherits the air "
            "coupling penalty at both ends",
            "can close a loop, and famously does — this is acoustic "
            "howl. The gain is in the amplifier, not the crystal."),
        _cond(
            "SHAM", False, False, False, 0.0,
            "no source by construction; the drive electronics are "
            "connected and set to zero output",
            "the control that distinguishes a real response from "
            "operator expectation, instrument artefact or ambient "
            "pickup. A sham condition that shows a response has found "
            "an uncontrolled input, which is a result."),
    )
}

#: Convenience alias — the contract calls this a registry.
CONDITIONS = EXCITATION_CONDITIONS


def condition_registry() -> dict:
    """Every excitation condition with its energy and loop verdict."""
    conds = {k: v.as_record() for k, v in EXCITATION_CONDITIONS.items()}
    return {
        "conditions": conds,
        "n_conditions": len(conds),
        "supply_energy": sorted(
            k for k, v in EXCITATION_CONDITIONS.items()
            if v.supplies_energy),
        "can_close_a_loop": sorted(
            k for k, v in EXCITATION_CONDITIONS.items()
            if v.can_close_loop),
        "passive": sorted(
            k for k, v in EXCITATION_CONDITIONS.items()
            if not v.supplies_energy),
        "invariant": (
            "every condition that can close a loop has ACTIVE in its "
            "name, because closing a loop requires an amplifier and an "
            "amplifier requires a power supply."),
        "acoustic_impedance_ratio_air_to_quartz": Z_QUARTZ / Z_AIR,
        "airborne_intensity_transmission":
            4.0 * Z_AIR * Z_QUARTZ / (Z_AIR + Z_QUARTZ) ** 2,
        "units": "coupling efficiencies dimensionless",
        "provenance": (
            "order-of-magnitude estimates from standard acoustics and "
            "transducer literature. No drive has been built or "
            "applied."),
        "evidence_class": "SYNTHETIC_MODEL",
    }


# --------------------------------------------------------------------
# Classification
# --------------------------------------------------------------------

def classify(condition: str, loop_gain: float, phase: float,
             contact_present: bool, *,
             phase_tol_rad: float = DEFAULT_PHASE_TOL_RAD) -> dict:
    """Assign one of :data:`r7.EXCITATION_STATUSES`.

    Order of tests matters and is deliberate:

    1. A loop that meets **both** Barkhausen conditions in a condition
       with an active element is ``ACTIVE_SELF_OSCILLATION``. This is
       ordinary engineering and is not refused.
    2. A loop that meets both conditions in a condition with **no**
       active element is a claim that energy appeared from nowhere. It
       is ``PASSIVE_SELF_OSCILLATION_CLAIM_REFUSED`` — checked before
       the contact test, so that the refusal is never masked by a
       milder verdict.
    3. Contact present, no sustained loop: contact damping dominates
       the observable, so ``CONTACT_LOADING_DOMINANT``.
    4. Energy supplied, no contact: ``FORCED_RESPONSE``.
    5. Nothing supplied: ``RINGDOWN``, the only thing a passive
       resonator does on its own.
    """
    if condition not in EXCITATION_CONDITIONS:
        raise ValueError(f"unknown excitation condition {condition!r}")
    c = EXCITATION_CONDITIONS[condition]
    bark = barkhausen_check(loop_gain, phase, phase_tol_rad=phase_tol_rad)

    if bark["oscillates"] and c.can_close_loop:
        status = "ACTIVE_SELF_OSCILLATION"
        reason = (
            f"{condition} contains an active element, and the loop "
            f"meets both Barkhausen conditions. The energy comes from "
            f"the amplifier's supply, not from the crystal.")
    elif bark["oscillates"]:
        status = "PASSIVE_SELF_OSCILLATION_CLAIM_REFUSED"
        reason = (
            f"{condition} contains no active element, so a loop gain "
            f"of {loop_gain:.3f} at the oscillation phase is not "
            f"available to it. A sustained loop under this condition "
            f"means an energy input has been mis-attributed or an "
            f"unmodelled active path exists; either way the passive "
            f"claim is refused, not recorded.")
    elif contact_present:
        status = "CONTACT_LOADING_DOMINANT"
        reason = (
            f"contact is present and no sustained loop exists. The "
            f"dominant effect on the observable is the loss the "
            f"contact introduces, which reduces Q by orders of "
            f"magnitude and broadens the resonance. Any amplitude seen "
            f"here is a forced response riding on a heavily damped "
            f"mode.")
    elif c.supplies_energy:
        status = "FORCED_RESPONSE"
        reason = (
            f"{condition} supplies energy with coupling of order 1e"
            f"{c.coupling_order}, and the loop does not sustain "
            f"({'gain' if not bark['gain_condition_met'] else 'phase'} "
            f"condition unmet). The response follows the drive and "
            f"stops when the drive stops.")
    else:
        status = "RINGDOWN"
        reason = (
            f"{condition} supplies no energy and no loop is closed. "
            f"Stored energy can only decay. This is the reference "
            f"behaviour of a passive resonator and the condition in "
            f"which Q is properly measured.")

    assert status in EXCITATION_STATUSES, status
    return {
        "condition": condition,
        "status": status,
        "reason": reason,
        "barkhausen": bark,
        "supplies_energy": c.supplies_energy,
        "can_close_loop": c.can_close_loop,
        "contact_present": contact_present,
        "coupling_efficiency": c.coupling_efficiency,
        "coupling_order": c.coupling_order,
        "units": "coupling dimensionless; phases in radians",
        "evidence_class": "DERIVED_ARITHMETIC",
    }


# --------------------------------------------------------------------
# The central refusal
# --------------------------------------------------------------------

def refuse_passive_self_oscillation(*args, **kwargs):
    """Always refuses. A passive resonator has no gain element.

    Energy conservation settles it before any experiment does. Sustained
    oscillation requires energy delivered every cycle to replace what
    damping removes. A passive crystal contains no source: it can store
    energy and it can lose energy, so its only unforced behaviour is
    ringing DOWN.

    A crystal that appears to "keep going" while hand-held is being
    driven. The inputs, all of them ordinary and all of them present:

    * physiological tremor at 8-12 Hz, broadband, involuntary, present
      in every human hand and coupled mechanically through skin
      contact;
    * triboelectric and contact charge from skin against quartz, which
      a piezoelectric material converts to strain;
    * thermal drift from a warm hand, which shifts the resonance and
      changes the amplitude of whatever is already being driven.

    Removing the hand removes all three at once, which is why the
    effect is reported as depending on holding it — and is also why the
    free-suspension and sham conditions exist.
    """
    raise ExcitationRefused(
        "a passive crystal cannot sustain its own oscillation. "
        "Sustained oscillation needs |A*beta| >= 1 at a phase that is a "
        "multiple of 2 pi, which needs a gain element, which needs a "
        "power supply. A passive resonator has none, so it can only "
        "ring down. A hand-held crystal that appears to keep going is "
        "receiving energy from physiological tremor (8-12 Hz, "
        "broadband, mechanically coupled), from triboelectric and "
        "contact charge at the skin, and from thermal drift of a warm "
        "hand — all of which are inputs (r7 FORBIDDEN_COLLAPSES: "
        "HANDHELD_RESPONSE_IS_SELF_OSCILLATION).")


def passive_resonator_can_self_oscillate() -> bool:
    """Constant ``False``, kept so the answer is inspectable."""
    return False


# --------------------------------------------------------------------
# Ringdown
# --------------------------------------------------------------------

def ringdown(q_factor: float, f0_hz: float, t: float) -> float:
    """Amplitude envelope exp(-pi f0 t / Q).

    The standard free-decay envelope for a linear resonator: energy
    falls as exp(-w0 t / Q) and amplitude as the square root of that.
    Higher Q means slower decay, which is the entire content of Q.
    """
    if q_factor <= 0.0:
        raise ValueError("Q must be positive")
    if f0_hz <= 0.0:
        raise ValueError("resonant frequency must be positive")
    if t < 0.0:
        raise ValueError("time must be non-negative")
    return math.exp(-math.pi * f0_hz * t / q_factor)


def time_to_decay(q: float, f0: float, fraction: float) -> float:
    """Time for the amplitude envelope to fall to ``fraction``.

    Inverting the envelope: t = -Q ln(fraction) / (pi f0). Linear in Q,
    so doubling Q doubles the ringdown time — the property that makes a
    free-suspension Q measurement the discriminating one.
    """
    if q <= 0.0:
        raise ValueError("Q must be positive")
    if f0 <= 0.0:
        raise ValueError("resonant frequency must be positive")
    if not 0.0 < fraction < 1.0:
        raise ValueError("fraction must lie strictly between 0 and 1")
    return -q * math.log(fraction) / (math.pi * f0)


# --------------------------------------------------------------------
# The hand-held condition, modelled honestly
# --------------------------------------------------------------------

#: Q figures are literature class for the resonator TYPE, spanning
#: several orders of magnitude by design: the point is the ratio, not
#: any single value.
Q_CLASS_FIGURES = {
    "AT_CUT_VACUUM_SEALED": 1e6,
    "FREE_SUSPENSION_IN_AIR": 1e5,
    "SOFT_SUPPORT": 1e4,
    "HAND_HELD": 1e2,
}


def handheld_analysis(f0_hz: float = 1e6) -> dict:
    """What a hand actually does to a crystal, in both directions.

    Two effects, pulling opposite ways on the observation:

    * a hand **removes** energy. Skin is lossy and acoustically far
      closer to quartz than air is, so contact damping typically
      dominates the loss budget and drops Q by three to four orders of
      magnitude against free suspension. The ringdown that follows is
      correspondingly shorter — milliseconds instead of seconds.
    * a hand **adds** energy, broadband, continuously, through tremor,
      charge and heat.

    Together they explain the reported phenomenon without any new
    physics: a heavily damped mode kept in continuous forced response by
    an uncontrolled broadband source. Both effects vanish when the hand
    does.
    """
    q_free = Q_CLASS_FIGURES["FREE_SUSPENSION_IN_AIR"]
    q_hand = Q_CLASS_FIGURES["HAND_HELD"]
    t_free = time_to_decay(q_free, f0_hz, 1.0 / math.e)
    t_hand = time_to_decay(q_hand, f0_hz, 1.0 / math.e)

    supported = ["FORCED_RESPONSE", "CONTACT_LOADING_DOMINANT",
                 "RINGDOWN"]
    unsupported = ["ACTIVE_SELF_OSCILLATION"]
    refused = ["PASSIVE_SELF_OSCILLATION_CLAIM_REFUSED"]
    for s in supported + unsupported + refused:
        assert s in EXCITATION_STATUSES, s

    return {
        "condition": "HANDHELD_STRAIN_AND_CHARGE",
        "f0_hz": f0_hz,
        "q_free_suspension": q_free,
        "q_hand_held": q_hand,
        "q_reduction_factor": q_free / q_hand,
        "q_reduction_orders_of_magnitude":
            math.log10(q_free / q_hand),
        "ringdown_tau_free_s": t_free,
        "ringdown_tau_handheld_s": t_hand,
        "energy_inputs": {
            "physiological_tremor": {
                "band_hz": list(PHYSIOLOGICAL_TREMOR_HZ),
                "note": ("involuntary 8-12 Hz oscillation present in "
                         "every human hand, broadband in practice, "
                         "coupled mechanically through the skin. It "
                         "cannot be suppressed by the operator and it "
                         "is present in every hand-held trial."),
            },
            "triboelectric_and_contact_charge": {
                "note": ("skin against quartz transfers charge; a "
                         "piezoelectric material converts the "
                         "resulting field to strain. This is an "
                         "electrical input through a mechanical "
                         "contact and is not removed by insulating "
                         "gloves, which are themselves triboelectric."),
            },
            "thermal_drift": {
                "note": ("a hand near 37 C against a specimen at room "
                         "temperature shifts f0 while it warms, which "
                         "changes the amplitude of any driven response "
                         "and reads as the response 'evolving'."),
            },
        },
        "statuses_this_condition_can_support": supported,
        "statuses_this_condition_cannot_support": unsupported,
        "statuses_this_condition_triggers_a_refusal_for": refused,
        "why_not_active_self_oscillation": (
            "ACTIVE_SELF_OSCILLATION requires an active element with a "
            "power supply inside the loop. A hand is not one: it "
            "supplies broadband energy with no phase relationship to "
            "the mode, which is the definition of a drive rather than "
            "of feedback. A hand-held passive specimen therefore "
            "cannot reach that status by any loop gain the operator "
            "reports."),
        "discriminating_experiment": (
            "measure Q by free-suspension ringdown, then repeat "
            "hand-held. If the hand were sustaining oscillation the "
            "hand-held Q would RISE; the model here predicts it falls "
            f"by about {math.log10(q_free / q_hand):.0f} orders of "
            "magnitude. The two predictions differ in sign, which is "
            "as clean a discrimination as this programme has."),
        "units": ("Q dimensionless, frequencies in Hz, times in "
                  "seconds"),
        "provenance": ("Q values are literature-class figures for the "
                       "resonator type. No crystal has been held, "
                       "suspended or rung down by this programme."),
        "evidence_class": "SYNTHETIC_MODEL",
    }


# --------------------------------------------------------------------
# Headline
# --------------------------------------------------------------------

def status_report() -> dict:
    """The P05 headline, computed rather than asserted."""
    hh = handheld_analysis()
    reg = condition_registry()
    # The two near-misses, to show that one condition alone is not enough.
    gain_only = barkhausen_check(50.0, math.pi / 2.0)
    phase_only = barkhausen_check(0.9, 0.0)
    return {
        "claim": ("a crystal held in the hand continues to oscillate "
                  "on its own"),
        "status": "PASSIVE_SELF_OSCILLATION_CLAIM_REFUSED",
        "conditions_modelled": reg["n_conditions"],
        "conditions_that_can_close_a_loop": reg["can_close_a_loop"],
        "gain_only_oscillates": gain_only["oscillates"],
        "phase_only_oscillates": phase_only["oscillates"],
        "handheld_q_reduction_orders":
            hh["q_reduction_orders_of_magnitude"],
        "verdict": (
            "Sustained oscillation requires both |A*beta| >= 1 and a "
            "loop phase that is a multiple of 2 pi, and satisfying "
            "either one alone gives nothing — the arithmetic above "
            "shows a gain of 50 at 90 degrees and a gain of 0.9 at 0 "
            "degrees both failing. Both conditions together require a "
            "gain element, which requires a power supply, which a bare "
            "crystal does not have. The hand-held observation is "
            "explained by a mode whose Q is reduced roughly "
            f"{hh['q_reduction_orders_of_magnitude']:.0f} orders of "
            "magnitude by contact loss, kept in forced response by "
            "tremor, contact charge and thermal drift."),
        "what_would_settle_it": (
            "a free-suspension ringdown Q, repeated hand-held, with a "
            "sham condition and the drive electronics disconnected. "
            "The two hypotheses predict opposite signs for the change "
            "in Q. Nothing has been measured."),
        "evidence_class": "DERIVED_ARITHMETIC",
    }
