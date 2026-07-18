"""P04 — quartz handedness, optical rotation, and magnetochiral parity.

Alpha-quartz is enantiomorphic: it crystallizes in two mirror-image
forms that are structurally distinct, optically distinguishable, and
cannot be superimposed. That is ordinary, well-established crystal
physics, and this module models it.

Magnetochiral anisotropy (MChA) is also real and published: for a
chiral medium in a magnetic field, absorption acquires a term
proportional to ``k . B`` whose sign flips with the enantiomer. It is
NOT optical rotation, NOT circular dichroism, and NOT the Faraday
effect — it is the cross term that survives when you reverse both the
field and the handedness. It is also very small: measured fractional
anisotropies in real materials run from roughly 1e-4 in resonant,
strongly enhanced systems down to 1e-9. Any experiment proposing to see
it must state its instrument sensitivity first, which is what
:func:`required_sensitivity` exists to force.

NOTHING IN THIS MODULE IS BENCH DATA. No specimen has been cut, no
polarimeter aligned, no field applied. Every constant is a literature
value cited at its point of use; every function is a model evaluation.
The programme has determined no specimen's handedness and measured no
anisotropy.

The parity test is the headline's null
--------------------------------------
:func:`parity_test_matrix` is a four-cell design, ``(LEFT, RIGHT) x
(B up, B down)``. A genuine magnetochiral signal must reverse when
either the enantiomer or the field is reversed, and must be RESTORED
when both are reversed. That double reversal is the actual test. A
signal that survives one reversal, or that fails to come back under the
double reversal, is instrumental — a drift, an offset, a
field-dependent detector artefact, or a difference between the two
specimens that has nothing to do with chirality.
:func:`classify_parity_result` implements exactly that decomposition and
will return ``INSTRUMENTAL_OFFSET`` rather than a discovery.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

Handedness = Literal["LEFT", "RIGHT"]

HANDEDNESS_VALUES: tuple[str, ...] = ("LEFT", "RIGHT")

# --- literature constants ------------------------------------------------
# All values below are LITERATURE VALUES for alpha-quartz. None was
# measured by this programme.

#: Specific optical rotation of alpha-quartz along the optic axis at the
#: sodium D line (589.3 nm, ~20 C): approximately 21.7 deg/mm.
#: LITERATURE VALUE. NOT MEASURED BY THIS PROGRAMME.
ROTATORY_POWER_589_DEG_PER_MM = 21.72

#: Rotatory power of alpha-quartz along the optic axis as a function of
#: wavelength, deg/mm, at ~20 C. LITERATURE VALUES (classical quartz
#: rotatory-dispersion tables). NOT MEASURED BY THIS PROGRAMME.
#: Quoted to the precision the tables support (4 significant figures at
#: best); differences between sources at the 0.1% level exist and are not
#: resolved here.
ROTATORY_DISPERSION_DEG_PER_MM: dict[float, float] = {
    404.7: 48.93,
    508.6: 29.72,
    589.3: 21.72,
    656.3: 17.32,
}

#: Drude absorption-pole wavelength used to linearize the dispersion,
#: nm. LITERATURE-SCALE value (~93 nm) for the single-term Drude form
#: rho = A / (lambda^2 - lambda0^2) commonly fitted to quartz rotatory
#: dispersion. It is an interpolation aid, not a physical determination.
DRUDE_POLE_NM = 93.0

#: Wavelength range over which the dispersion table supports
#: interpolation. Outside it this module refuses rather than
#: extrapolates: a single-term Drude form is known to fail near the
#: ultraviolet absorption edge.
DISPERSION_VALID_NM: tuple[float, float] = (404.7, 656.3)

#: Space-group assignment by handedness, following the convention
#: requested for this programme. SEE THE WARNING BELOW.
SPACE_GROUP_BY_HANDEDNESS: dict[str, str] = {
    "LEFT": "P3121",    # No. 152
    "RIGHT": "P3221",   # No. 154
}

#: The two space groups are an enantiomorphic pair (Nos. 152 and 154);
#: that much is not in dispute. WHICH ONE IS CALLED "RIGHT-HANDED" IS.
#: The literature genuinely conflicts, because "right-handed quartz" has
#: been defined three different ways — by crystal morphology, by the
#: sign of the optical rotation, and by the sense of the structural
#: silicon helix — and these conventions do not all agree. The confusion
#: is documented in the crystallographic literature (see e.g. Glazer's
#: notes on the description of the quartz structure). R6 therefore
#: treats this mapping as a DECLARED CONVENTION, not a determination: a
#: specimen's space group must come from that specimen's own diffraction
#: data, never from this table.
SPACE_GROUP_CONVENTION_NOTE = (
    "SPACE-GROUP ASSIGNMENT IS CONVENTIONAL, NOT MEASURED. P3121 (152) "
    "and P3221 (154) are an enantiomorphic pair, but which is labelled "
    "'right-handed' depends on whether handedness is defined "
    "morphologically, optically, or by the sense of the structural "
    "helix, and published sources disagree. This module follows the "
    "declared convention LEFT=P3121, RIGHT=P3221 so that its own "
    "outputs are self-consistent. Do not cite it as a determination. "
    "Determine a specimen's space group from that specimen's "
    "diffraction data."
)

#: Order-of-magnitude range of magnetochiral anisotropies actually
#: MEASURED in real materials, as a fractional absorption difference.
#: LITERATURE RANGE, spanning resonant enhanced systems (~1e-4) down to
#: transparent non-resonant media (~1e-9). Cited so that a predicted
#: anisotropy can be placed against what instruments have ever resolved.
MCHA_MEASURED_RANGE = (1e-9, 1e-4)


class ChiralityRefusal(ValueError):
    """Raised when a handedness question has no referent for the material."""


class ChiralityModelError(ValueError):
    """Raised when a chirality model input is not physically meaningful."""


# --- specimen ------------------------------------------------------------

@dataclass(frozen=True)
class QuartzSpecimen:
    """A modeled alpha-quartz specimen with a declared handedness.

    ``handedness`` is the declared enantiomorph. ``space_group`` follows
    :data:`SPACE_GROUP_BY_HANDEDNESS` unless overridden, and carries the
    caveat in :data:`SPACE_GROUP_CONVENTION_NOTE`: the assignment is a
    convention this module keeps consistent, not something the programme
    determined.

    ``specific_rotation_deg_per_mm`` is the signed rotatory power at
    ``reference_wavelength_nm``, positive for RIGHT (dextrorotatory) by
    the convention adopted in :func:`optical_rotation_deg`.

    A specimen constructed here is a description of an intended object.
    No such specimen has been obtained, cut, or characterized.
    """

    handedness: Handedness
    length_m: float = 0.0
    space_group: str = ""
    reference_wavelength_nm: float = 589.3
    specific_rotation_deg_per_mm: float = 0.0
    provenance: str = "modeled specimen; not obtained, not characterized"

    def __post_init__(self) -> None:
        if self.handedness not in HANDEDNESS_VALUES:
            raise ChiralityModelError(
                f"handedness must be one of {HANDEDNESS_VALUES}, got "
                f"{self.handedness!r}")
        if self.length_m < 0.0 or not math.isfinite(self.length_m):
            raise ChiralityModelError("length_m must be finite, >= 0")
        if not self.space_group:
            object.__setattr__(
                self, "space_group",
                SPACE_GROUP_BY_HANDEDNESS[self.handedness])
        if self.specific_rotation_deg_per_mm == 0.0:
            object.__setattr__(
                self, "specific_rotation_deg_per_mm",
                _signed_rotatory_power(self.reference_wavelength_nm,
                                       self.handedness))

    @property
    def chi(self) -> int:
        """Enantiomer sign chi = +1 (RIGHT) / -1 (LEFT).

        This is the factor that flips the magnetochiral term. It is a
        label, not a measured quantity.
        """
        return +1 if self.handedness == "RIGHT" else -1

    def space_group_note(self) -> str:
        return SPACE_GROUP_CONVENTION_NOTE


def opposite(handedness: Handedness) -> Handedness:
    """The other enantiomorph."""
    if handedness not in HANDEDNESS_VALUES:
        raise ChiralityModelError(f"unknown handedness {handedness!r}")
    return "LEFT" if handedness == "RIGHT" else "RIGHT"


# --- optical rotation ----------------------------------------------------

def _drude_u(wavelength_nm: float) -> float:
    """Drude variable u = 1 / (lambda^2 - lambda0^2), nm^-2."""
    return 1.0 / (wavelength_nm ** 2 - DRUDE_POLE_NM ** 2)


def rotatory_power_deg_per_mm(wavelength_nm: float) -> float:
    """Unsigned rotatory power of quartz along the optic axis, deg/mm.

    Interpolates the LITERATURE table
    :data:`ROTATORY_DISPERSION_DEG_PER_MM` linearly in the Drude variable
    ``u = 1/(lambda^2 - lambda0^2)`` with ``lambda0`` = 93 nm. A
    single-term Drude form is very nearly linear in ``u`` across the
    visible, so this reproduces the tabulated points exactly and
    interpolates between them with an error small compared with the
    disagreement between published tables.

    REFUSES to extrapolate outside :data:`DISPERSION_VALID_NM`
    (404.7-656.3 nm). The single-term Drude form is known to break down
    approaching the ultraviolet absorption edge, and quoting a number
    there would be a fabricated precision, not a model limitation the
    caller could see.

    The dispersion is real and large — quartz rotates blue light more
    than twice as strongly as red — so any polarimetric protocol that
    does not state its wavelength is not reproducible.
    """
    lo, hi = DISPERSION_VALID_NM
    if not math.isfinite(wavelength_nm):
        raise ChiralityModelError("wavelength_nm must be finite")
    if wavelength_nm < lo or wavelength_nm > hi:
        raise ChiralityModelError(
            f"wavelength {wavelength_nm} nm is outside the tabulated "
            f"range {lo}-{hi} nm. This module refuses to extrapolate "
            f"quartz rotatory dispersion: the single-term Drude form "
            f"fails near the UV absorption edge, and an extrapolated "
            f"value would look like knowledge it is not.")

    points = sorted(ROTATORY_DISPERSION_DEG_PER_MM.items())
    for (l0, r0), (l1, r1) in zip(points, points[1:]):
        if l0 <= wavelength_nm <= l1:
            u, u0, u1 = (_drude_u(wavelength_nm), _drude_u(l0),
                         _drude_u(l1))
            if u1 == u0:  # pragma: no cover - table has distinct points
                return r0
            return r0 + (r1 - r0) * (u - u0) / (u1 - u0)
    raise ChiralityModelError(  # pragma: no cover - bracketed above
        f"no bracketing table interval for {wavelength_nm} nm")


def _signed_rotatory_power(wavelength_nm: float,
                           handedness: Handedness) -> float:
    if handedness not in HANDEDNESS_VALUES:
        raise ChiralityModelError(f"unknown handedness {handedness!r}")
    sign = +1.0 if handedness == "RIGHT" else -1.0
    return sign * rotatory_power_deg_per_mm(wavelength_nm)


def optical_rotation_deg(thickness_m: float, wavelength_nm: float,
                         handedness: Handedness) -> float:
    """Signed rotation of the plane of polarization, in degrees.

    Light propagating **along the optic axis** through a thickness
    ``t`` of alpha-quartz has its plane of polarization rotated by::

        alpha = sign(handedness) * rho(lambda) * t_mm

    where ``rho`` is the rotatory power from
    :func:`rotatory_power_deg_per_mm` (LITERATURE values; ~21.7 deg/mm at
    589.3 nm).

    Sign convention: RIGHT-handed (dextrorotatory) quartz is taken as
    POSITIVE, i.e. it rotates the plane clockwise as seen by an observer
    looking toward the source. LEFT-handed quartz gives the equal and
    opposite rotation. The sign flip under enantiomer reversal is exact
    and is the basis of :func:`handedness_from_rotation`.

    Model limits, all of which matter on a bench:

    - Valid **along the optic axis only**. Off-axis, quartz's linear
      birefringence (delta n ~ 0.009) dominates the rotatory effect
      completely and the polarization state is no longer simply rotated.
      This function has no way to detect an off-axis specimen and will
      return a confidently wrong number for one.
    - Monochromatic. Dispersion is applied per-wavelength; a broadband
      source produces a spread of rotations, not a single value.
    - Room temperature. Quartz rotatory power has a temperature
      coefficient this model does not carry.
    - The returned angle is not reduced modulo 180 degrees. A thick
      specimen produces many turns, and a polarimeter reading alone
      cannot distinguish ``alpha`` from ``alpha + 180 n``; resolving that
      requires a second wavelength or a known thickness.
    """
    if not math.isfinite(thickness_m) or thickness_m < 0.0:
        raise ChiralityModelError("thickness_m must be finite and >= 0")
    thickness_mm = thickness_m * 1000.0
    return _signed_rotatory_power(wavelength_nm, handedness) * thickness_mm


def handedness_from_rotation(sign: float) -> Handedness:
    """Handedness from the SIGN of the measured optical rotation.

    This is a case where the inference is legitimate and R6 does not
    refuse it: for alpha-quartz along the optic axis, the sign of the
    rotation is determined by which enantiomorph the specimen is.
    Positive (dextrorotatory, clockwise toward the source) means RIGHT;
    negative means LEFT. There is no third possibility for crystalline
    quartz.

    What this does NOT give you:

    - It does not give you the space group. That mapping is a convention
      here, not a determination — see
      :data:`SPACE_GROUP_CONVENTION_NOTE`.
    - It requires that the sign was measured on-axis on a crystalline
      specimen. An off-axis reading, or a reading through a birefringent
      or stressed sample, can carry any sign at all.
    - A zero reading is not "neither". It is a failed measurement — a
      zero-thickness sample, an off-axis path, an exact multiple of 180
      degrees, or a polarimeter that is not working. This function
      raises rather than guessing.
    """
    if not math.isfinite(sign):
        raise ChiralityModelError("rotation sign must be finite")
    if sign == 0.0:
        raise ChiralityModelError(
            "a zero optical rotation does not indicate 'neither "
            "handedness'. It indicates a failed or ambiguous "
            "measurement: zero thickness, an off-axis path, an exact "
            "multiple of 180 degrees, or an instrument fault. Determine "
            "the cause; do not assign a handedness.")
    return "RIGHT" if sign > 0.0 else "LEFT"


#: Materials with no crystal chirality to assign. Amorphous silica has no
#: long-range order and therefore no enantiomorph: it is not "racemic",
#: it is not "left" or "right", the question has no referent.
AMORPHOUS_MATERIALS: tuple[str, ...] = (
    "fused silica",
    "fused quartz",
    "amorphous sio2",
    "amorphous silica",
    "silica glass",
    "quartz glass",
    "vitreous silica",
    "glass",
    "opal",
    "silica gel",
)


def refuse_chirality_of_amorphous(material: str) -> str:
    """Refuse to assign handedness to an amorphous silica.

    Returns the normalized material name if the material IS crystalline
    (so the caller may proceed); raises :class:`ChiralityRefusal` if it
    is amorphous.

    "Fused quartz" is not quartz. It is amorphous SiO2 with no long-range
    order, no enantiomorphic space group, no optical activity along any
    axis, and therefore no handedness — the question has no referent, so
    the answer is a refusal rather than a value. This matters because
    the trade name contains the word "quartz" and because fused silica is
    the material most likely to be substituted for crystalline quartz in
    an optical setup. A protocol that assigns a handedness to fused
    silica has misidentified its specimen, and any downstream chirality
    result from it is void.
    """
    if not isinstance(material, str) or not material.strip():
        raise ChiralityModelError("material must be a non-empty string")
    norm = " ".join(material.strip().lower().replace("-", " ").split())
    for banned in AMORPHOUS_MATERIALS:
        if banned in norm:
            raise ChiralityRefusal(
                f"refusing to assign handedness to {material!r}: "
                f"{banned!r} is amorphous SiO2. Amorphous silica has no "
                f"long-range order, no enantiomorphic space group and no "
                f"optical activity, so it is not left-handed, not "
                f"right-handed, and not racemic — the question has no "
                f"referent. If a specimen labelled 'quartz' is in fact "
                f"fused silica, every chirality result taken from it is "
                f"void.")
    return norm


# --- magnetochiral anisotropy -------------------------------------------

@dataclass(frozen=True)
class MagnetochiralConfig:
    """A modeled magnetochiral anisotropy measurement.

    The effect: in a chiral medium, absorption acquires a term
    proportional to the projection of the wavevector on the field,

        A = A0 * (1 + gamma * (k_hat . B) * chi)

    where ``chi`` = +1/-1 distinguishes the two enantiomers and ``gamma``
    is the magnetochiral coupling per tesla. Reversing the propagation
    direction relative to the field flips the sign; so does swapping the
    enantiomer; doing both restores it. That last invariance is the
    parity signature and is the whole point of the four-cell design.

    Fields
    ------
    handedness
        Which enantiomorph is in the beam.
    b_field_tesla
        Field magnitude, T.
    k_dot_b_sign
        +1 if the propagation direction has a positive projection on B,
        -1 if negative. (Only the sign enters at this order.)
    gamma_per_tesla
        Magnetochiral coupling coefficient, 1/T. THIS IS AN INPUT
        ASSUMPTION, not a constant of nature this module supplies: it is
        material-, wavelength- and resonance-specific and spans many
        orders of magnitude. A caller who does not have a sourced gamma
        for their material and wavelength does not have a prediction.
    baseline_absorbance
        A0, the field-free absorbance.
    wavelength_nm
        Probe wavelength; recorded because gamma is strongly
        wavelength-dependent (MChA is enormously enhanced on resonance).
    instrument_fractional_noise
        The fractional absorbance resolution of the instrument in a
        single measurement. Used by :func:`required_sensitivity` to say
        how many averages the experiment needs, or that it is
        infeasible.
    """

    handedness: Handedness
    b_field_tesla: float
    k_dot_b_sign: int
    gamma_per_tesla: float
    baseline_absorbance: float = 1.0
    wavelength_nm: float = 589.3
    instrument_fractional_noise: float = 1e-5
    provenance: str = "modeled configuration; no field applied, no data"

    def __post_init__(self) -> None:
        if self.handedness not in HANDEDNESS_VALUES:
            raise ChiralityModelError(
                f"handedness must be one of {HANDEDNESS_VALUES}")
        if self.k_dot_b_sign not in (-1, 1):
            raise ChiralityModelError("k_dot_b_sign must be +1 or -1")
        for name in ("b_field_tesla", "gamma_per_tesla",
                     "baseline_absorbance", "instrument_fractional_noise"):
            v = getattr(self, name)
            if not math.isfinite(v):
                raise ChiralityModelError(f"{name} must be finite")
        if self.b_field_tesla < 0.0:
            raise ChiralityModelError(
                "b_field_tesla is a magnitude; put the direction in "
                "k_dot_b_sign")
        if self.baseline_absorbance <= 0.0:
            raise ChiralityModelError("baseline_absorbance must be > 0")
        if self.instrument_fractional_noise <= 0.0:
            raise ChiralityModelError(
                "instrument_fractional_noise must be > 0")

    @property
    def chi(self) -> int:
        """+1 for RIGHT, -1 for LEFT."""
        return +1 if self.handedness == "RIGHT" else -1

    def absorbance(self) -> float:
        """A = A0 (1 + gamma * (k.B) * chi), the modeled absorbance."""
        return self.baseline_absorbance * (
            1.0 + self.gamma_per_tesla * self.b_field_tesla
            * self.k_dot_b_sign * self.chi)

    def reversed_field(self) -> "MagnetochiralConfig":
        return MagnetochiralConfig(
            self.handedness, self.b_field_tesla, -self.k_dot_b_sign,
            self.gamma_per_tesla, self.baseline_absorbance,
            self.wavelength_nm, self.instrument_fractional_noise,
            self.provenance)

    def reversed_handedness(self) -> "MagnetochiralConfig":
        return MagnetochiralConfig(
            opposite(self.handedness), self.b_field_tesla,
            self.k_dot_b_sign, self.gamma_per_tesla,
            self.baseline_absorbance, self.wavelength_nm,
            self.instrument_fractional_noise, self.provenance)


def magnetochiral_anisotropy(config: MagnetochiralConfig) -> dict:
    """Predicted fractional magnetochiral anisotropy, with feasibility.

    The observable is the normalized difference between the two field
    directions at fixed enantiomer::

        g = (A(+k.B) - A(-k.B)) / mean(A) = 2 * gamma * B * chi

    so ``|g| = 2 * gamma * B`` and its sign carries the handedness.

    THE HONEST PART. Measured magnetochiral anisotropies in real
    materials are typically between 1e-4 (resonant, strongly enhanced
    systems, and even that is a hard measurement) and 1e-9 (transparent
    non-resonant media) as a fractional absorption difference — see
    :data:`MCHA_MEASURED_RANGE`. A predicted ``|g|`` above 1e-4 is not
    an exciting result; it is a sign that ``gamma_per_tesla`` was
    guessed rather than sourced, and this function flags it as such
    rather than reporting a large effect. A predicted ``|g|`` below
    1e-9 is below anything that has been resolved, and no protocol in
    R6 can claim to see it. The returned record says which regime the
    prediction is in, and :func:`required_sensitivity` says what
    instrument it would take.

    Everything here is arithmetic on an assumed coupling constant. No
    field has been applied and no absorbance measured.
    """
    g = (2.0 * config.gamma_per_tesla * config.b_field_tesla
         * config.chi)
    mag = abs(g)
    lo, hi = MCHA_MEASURED_RANGE

    if mag == 0.0:
        regime = "ZERO_BY_CONSTRUCTION"
        note = ("gamma or B is zero: the model predicts no anisotropy. "
                "This is arithmetic, not a null result from an "
                "experiment.")
    elif mag > hi:
        regime = "IMPLAUSIBLY_LARGE_CHECK_GAMMA"
        note = (f"predicted |g|={mag:.3e} exceeds the largest fractional "
                f"magnetochiral anisotropy ever measured (~{hi:.0e}). "
                f"Treat this as evidence that gamma_per_tesla was "
                f"assumed rather than sourced for this material and "
                f"wavelength, not as a large predicted effect.")
    elif mag < lo:
        regime = "BELOW_ANYTHING_EVER_RESOLVED"
        note = (f"predicted |g|={mag:.3e} is below the smallest "
                f"magnetochiral anisotropy that has been resolved "
                f"(~{lo:.0e}). No R6 protocol can claim to detect this.")
    else:
        regime = "WITHIN_MEASURED_LITERATURE_RANGE"
        note = (f"predicted |g|={mag:.3e} lies within the range of "
                f"anisotropies real instruments have resolved "
                f"({lo:.0e} to {hi:.0e}), which makes it a hard "
                f"measurement, not an easy one.")

    return {
        "claim_context": "quartz magnetochiral response (P04)",
        "handedness": config.handedness,
        "chi": config.chi,
        "b_field_tesla": config.b_field_tesla,
        "k_dot_b_sign": config.k_dot_b_sign,
        "gamma_per_tesla": config.gamma_per_tesla,
        "wavelength_nm": config.wavelength_nm,
        "fractional_anisotropy": g,
        "abs_fractional_anisotropy": mag,
        "formula": "g = (A(+k.B) - A(-k.B)) / mean(A) = 2 gamma B chi",
        "literature_measured_range": MCHA_MEASURED_RANGE,
        "regime": regime,
        "note": note,
        "gamma_is_an_assumption": True,
        "not_bench_data": True,
        "ceiling": (
            "A predicted fractional anisotropy from an assumed coupling "
            "constant. It is not a measurement, and it becomes evidence "
            "only after the four-cell parity test of "
            "parity_test_matrix() returns "
            "PARITY_CONSISTENT_MAGNETOCHIRAL on real data with the "
            "sensitivity that required_sensitivity() demands."),
    }


def required_sensitivity(config: MagnetochiralConfig,
                         target_snr: float = 5.0) -> dict:
    """What instrument this prediction would actually need.

    To resolve a fractional anisotropy ``|g|`` at signal-to-noise
    ``target_snr``, the effective fractional resolution must satisfy
    ``sigma_eff <= |g| / target_snr``. With a per-measurement fractional
    noise ``sigma_1`` and white averaging, ``sigma_eff = sigma_1 /
    sqrt(N)``, so::

        N = (sigma_1 * target_snr / |g|)^2

    The averaging count is reported honestly, including when it is
    absurd. Two things it deliberately does not do:

    - It does not cap ``N``. If the answer is 1e18 averages the answer
      is 1e18 averages, which is the useful information.
    - It does not assume the averaging actually works. White-noise
      1/sqrt(N) improvement holds only until drift dominates; every real
      magnetochiral measurement is limited by systematics (thermal drift,
      field-induced detector response, specimen differences), which is
      why the four-cell parity design exists. A feasible ``N`` here is a
      necessary condition, never a sufficient one.
    """
    if not math.isfinite(target_snr) or target_snr <= 0.0:
        raise ChiralityModelError("target_snr must be finite and > 0")

    pred = magnetochiral_anisotropy(config)
    mag = pred["abs_fractional_anisotropy"]
    sigma_1 = config.instrument_fractional_noise

    if mag == 0.0:
        required = 0.0
        n_avg = math.inf
        feasible = False
    else:
        required = mag / target_snr
        n_avg = (sigma_1 * target_snr / mag) ** 2
        feasible = n_avg <= 1e9

    return {
        "abs_fractional_anisotropy": mag,
        "target_snr": target_snr,
        "required_fractional_resolution": required,
        "instrument_fractional_noise": sigma_1,
        "required_averages": n_avg,
        "single_shot_sufficient": mag > 0.0 and sigma_1 <= required,
        "feasible_within_1e9_averages": feasible,
        "regime": pred["regime"],
        "note": (
            "Averaging count assumes white noise improving as "
            "1/sqrt(N). Real magnetochiral measurements are systematics-"
            "limited long before that, so a feasible N is a NECESSARY "
            "condition for the measurement, never a sufficient one. The "
            "four-cell parity test is what discriminates signal from "
            "systematics."),
        "not_bench_data": True,
    }


# --- the four-cell parity test ------------------------------------------

#: Cell labels for the parity design, in the order accepted by
#: :func:`classify_parity_result`.
PARITY_CELLS: tuple[tuple[str, str, str], ...] = (
    ("a", "LEFT", "UP"),
    ("b", "LEFT", "DOWN"),
    ("c", "RIGHT", "UP"),
    ("d", "RIGHT", "DOWN"),
)

PARITY_OUTCOMES: tuple[str, ...] = (
    "PARITY_CONSISTENT_MAGNETOCHIRAL",
    "INSTRUMENTAL_OFFSET",
    "ENANTIOMER_ONLY",
    "FIELD_ONLY",
    "INCONSISTENT",
)


def parity_test_matrix() -> dict:
    """The four-cell design: (LEFT, RIGHT) x (B up, B down).

    Cells, in the argument order of :func:`classify_parity_result`::

        a = (LEFT,  B up)      b = (LEFT,  B down)
        c = (RIGHT, B up)      d = (RIGHT, B down)

    For a signal ``s = s0 + g * chi * sign(k.B)`` the four readings are

        a = s0 + g      b = s0 - g      c = s0 - g      d = s0 + g

    so the magnetochiral prediction is precisely: ``a == d``,
    ``b == c``, and ``a != b``. **Reversing BOTH the enantiomer and the
    field restores the original signal.** That double reversal is the
    actual parity test. A difference that appears when you flip the field
    but does not come back when you also swap the enantiomer is not
    magnetochiral — it is the magnet doing something to the instrument. A
    difference between the two specimens that does not flip with the
    field is not magnetochiral either — it is a difference between two
    pieces of rock.

    Execution requirements that the arithmetic cannot supply: randomized
    cell order (not a-b-c-d, which aliases the effect onto drift),
    blinded specimen identity, interleaved repeats so drift is
    estimable, and both specimens matched in thickness, surface finish
    and mounting. Without these the classification below is decorative.
    """
    return {
        "cells": PARITY_CELLS,
        "model": "s = s0 + g * chi * sign(k.B)",
        "prediction": "a == d, b == c, a != b (double reversal restores)",
        "outcomes": PARITY_OUTCOMES,
        "the_actual_test": (
            "Reversing BOTH handedness and field must restore the "
            "original signal. Any component that does not reverse under "
            "the double reversal is instrumental."),
        "execution_requirements": (
            "randomized cell order",
            "blinded specimen identity",
            "interleaved repeats to estimate drift",
            "thickness/surface/mounting matched specimens",
            "field magnitude verified in both directions",
        ),
        "not_bench_data": True,
    }


def classify_parity_result(a: float, b: float, c: float, d: float,
                           tol: float = 0.05,
                           noise: float = 0.0) -> dict:
    """Classify a four-cell parity result into one of five outcomes.

    Arguments are the four cell readings in the order defined by
    :func:`parity_test_matrix`: ``a=(LEFT,UP)``, ``b=(LEFT,DOWN)``,
    ``c=(RIGHT,UP)``, ``d=(RIGHT,DOWN)``.

    The 2x2 design is decomposed into four orthogonal contrasts::

        mean         M0 = (a + b + c + d) / 4
        field        F  = ((a + c) - (b + d)) / 4     flips with B only
        enantiomer   E  = ((a + b) - (c + d)) / 4     flips with chi only
        product      P  = ((a + d) - (b + c)) / 4     flips with the
                                                       PRODUCT chi*(k.B)

    Only ``P`` has the magnetochiral symmetry.

    Two thresholds, deliberately separate:

    ``tol``
        Fraction of the LARGEST contrast below which a smaller contrast
        is treated as absent (default 5%). Scale-free: it compares
        contrasts with each other, never with the baseline, so a genuine
        1e-6 effect riding on a baseline of 1 is not misclassified as an
        offset.
    ``noise``
        Absolute measurement resolution, in the same units as the cell
        readings. Contrasts at or below it are not resolvable and the
        result is ``INSTRUMENTAL_OFFSET``. It defaults to 0.0, meaning
        "treat these four numbers as exact" — which is correct for
        arithmetic and WRONG for data. A caller with real readings must
        pass their measured resolution, or this function will happily
        classify their noise.

    Outcomes:

    ``PARITY_CONSISTENT_MAGNETOCHIRAL``
        P dominates; F and E are negligible. The signal reversed under
        each single reversal and was restored under the double reversal.
        This is the ONLY outcome consistent with magnetochiral
        anisotropy, and even it is consistency, not proof: it must
        replicate, on independent specimens, at the sensitivity
        :func:`required_sensitivity` demands.

    ``FIELD_ONLY``
        F dominates. The signal tracks the field and ignores the
        enantiomer. Almost always the magnet acting on the instrument —
        Faraday rotation in a window, a field-sensitive detector or
        photoelastic mount, or induced pickup.

    ``ENANTIOMER_ONLY``
        E dominates. The two specimens differ and the field does
        nothing. This is a difference between two pieces of rock —
        thickness, strain, surface, inclusions, alignment — not a
        magnetochiral effect.

    ``INSTRUMENTAL_OFFSET``
        No contrast is resolvable: all four cells agree within
        tolerance and only the common offset survives. Nothing reversed
        under any reversal. There is no effect here at the sensitivity
        achieved.

    ``INCONSISTENT``
        Two or more contrasts are comparable. The design has not
        separated the effect from its systematics; the correct action is
        to fix the experiment, not to report the P component as a
        finding.
    """
    for name, v in (("a", a), ("b", b), ("c", c), ("d", d)):
        if not math.isfinite(v):
            raise ChiralityModelError(f"cell {name} must be finite")
    if not (0.0 < tol < 1.0):
        raise ChiralityModelError("tol must be in (0, 1)")
    if not math.isfinite(noise) or noise < 0.0:
        raise ChiralityModelError("noise must be finite and >= 0")

    mean = (a + b + c + d) / 4.0
    field = ((a + c) - (b + d)) / 4.0
    enant = ((a + b) - (c + d)) / 4.0
    product = ((a + d) - (b + c)) / 4.0

    contrasts = {"field": field, "enantiomer": enant, "product": product}
    biggest = max(abs(v) for v in contrasts.values())
    # "Absent" means small compared with the largest contrast (scale-free)
    # or below the instrument's stated resolution (absolute). The baseline
    # never enters: a real 1e-6 effect on a baseline of 1 must not be
    # swallowed by a threshold defined as a fraction of the baseline.
    cut = max(tol * biggest, noise)
    present = {k: abs(v) > cut for k, v in contrasts.items()}
    n_present = sum(present.values())

    if biggest <= noise or n_present == 0:
        outcome = "INSTRUMENTAL_OFFSET"
        reason = ("no contrast is resolvable above tolerance; only the "
                  "common offset survives. Nothing reversed under any "
                  "reversal, so there is no effect at this sensitivity.")
    elif n_present > 1:
        outcome = "INCONSISTENT"
        reason = ("more than one contrast is comparable in size; the "
                  "design has not separated the magnetochiral component "
                  "from its systematics. Fix the experiment; do not "
                  "report the product component as a finding.")
    elif present["product"]:
        outcome = "PARITY_CONSISTENT_MAGNETOCHIRAL"
        reason = ("only the product contrast survives: the signal "
                  "reversed under each single reversal and was restored "
                  "under the double reversal. Consistent with "
                  "magnetochiral anisotropy — which is not the same as "
                  "demonstrating it. Replicate on independent specimens.")
    elif present["field"]:
        outcome = "FIELD_ONLY"
        reason = ("the signal tracks the field and ignores the "
                  "enantiomer. This is the magnet acting on the "
                  "instrument, not a chiral effect.")
    else:
        outcome = "ENANTIOMER_ONLY"
        reason = ("the two specimens differ and the field does nothing. "
                  "This is a difference between two pieces of rock, not "
                  "a magnetochiral effect.")

    return {
        "cells": {"a_left_up": a, "b_left_down": b,
                  "c_right_up": c, "d_right_down": d},
        "mean": mean,
        "field_contrast": field,
        "enantiomer_contrast": enant,
        "product_contrast": product,
        "double_reversal_restores": abs(a - d) <= cut and abs(b - c) <= cut,
        "tolerance": tol,
        "noise": noise,
        "cut": cut,
        "contrast_present": present,
        "outcome": outcome,
        "reason": reason,
        "evidence_class": "ORDINARY_CHANNEL_RESULT",
        "ceiling": (
            "A parity classification of four numbers. Consistency with "
            "the magnetochiral symmetry is not detection; detection "
            "requires replication on independent specimens at stated "
            "sensitivity, with randomized and blinded cell order."),
    }


__all__ = [
    "Handedness",
    "HANDEDNESS_VALUES",
    "ROTATORY_POWER_589_DEG_PER_MM",
    "ROTATORY_DISPERSION_DEG_PER_MM",
    "DISPERSION_VALID_NM",
    "DRUDE_POLE_NM",
    "SPACE_GROUP_BY_HANDEDNESS",
    "SPACE_GROUP_CONVENTION_NOTE",
    "MCHA_MEASURED_RANGE",
    "AMORPHOUS_MATERIALS",
    "PARITY_CELLS",
    "PARITY_OUTCOMES",
    "ChiralityRefusal",
    "ChiralityModelError",
    "QuartzSpecimen",
    "opposite",
    "rotatory_power_deg_per_mm",
    "optical_rotation_deg",
    "handedness_from_rotation",
    "refuse_chirality_of_amorphous",
    "MagnetochiralConfig",
    "magnetochiral_anisotropy",
    "required_sensitivity",
    "parity_test_matrix",
    "classify_parity_result",
]
