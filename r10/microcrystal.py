"""P07 — a 13 MHz quartz microcrystal resonator, as a circuit model only.

The source material wants a "13 MHz crystal" to *mean* something -- a
distance, a wavelength in the stone, a resonance you could point an
antenna at. This module refuses that leap and does the one honest thing
that is fully defensible: it writes down the **Butterworth-Van Dyke
(BVD)** equivalent circuit of a quartz microcrystal resonator and works
its textbook algebra exactly.

**What is real here (and it is completely conventional).** A quartz
resonator near a mechanical mode behaves as a series motional branch
-- inductance ``Lm``, capacitance ``Cm``, resistance ``Rm`` -- sitting
in parallel with the static electrode capacitance ``C0``. That model
gives two resonances and a quality factor, all in closed form:

    fs = 1 / (2*pi*sqrt(Lm*Cm))            # series resonance
    fp = fs * sqrt(1 + Cm/C0)              # parallel (anti-)resonance
    Q  = (2*pi*fs*Lm) / Rm  ==  1/(2*pi*fs*Cm*Rm)

These are not measurements. They are the definitions of the circuit,
and :func:`bvd_series_resonance_hz`, :func:`bvd_parallel_resonance_hz`
and :func:`bvd_quality_factor` compute them to floating precision. The
ordering ``fs < fp`` is a structural fact of the model, not an
experimental finding.

**The load-bearing refusal.** A "13 MHz crystal" tempts you to read a
wavelength off it. The free-space wavelength of 13 MHz is
``lambda0 = c/f ~ 23.06 m`` and ``lambda0/4 ~ 5.77 m`` -- provided here
as arithmetic. But the acoustic wave inside quartz is not a free-space
electromagnetic wave: its wavelength depends on the acoustic velocity
of the specific cut and mode, the overtone, the temperature and the
propagation direction, and it is smaller than ``lambda0`` by roughly
five orders of magnitude. Using ``lambda0`` "inside the crystal" is a
category error. :func:`refuse_freespace_wavelength_in_quartz` raises
rather than return a number, and that refusal is the point of the
module.

**Overtones are odd.** A thickness-shear resonator supports only odd
overtones (1, 3, 5, ...); an even overtone is unphysical for this mode
and :class:`Resonator` refuses it.

**Phase noise is a shape, not a spectrum.** The Leeson picture predicts
a *qualitative* oscillator phase-noise profile -- a close-in ``1/f^3``
region, a ``1/f^2`` region, then a flat floor -- with corners set by
the flicker corner and the Leeson (half-bandwidth) corner. It is
offered as a typed model of the *shape*, never as a measured L(f).

Nothing here is measured. No crystal has been cut, mounted, or driven;
no apparatus exists. The schema records what such a part *would* be
specified by, and the module computes only what the circuit defines.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction

# --- provenance for every constant -------------------------------------

#: SI definition of the metre; exact.
C_M_PER_S = 299_792_458

#: The nominal fundamental target for this part. Exact by fiat: it is a
#: design target, not a measured line.
NOMINAL_FREQUENCY_HZ = Fraction(13_000_000)

PROVENANCE = {
    "C_M_PER_S": "299792458, the SI definition of the metre",
    "NOMINAL_FREQUENCY_HZ": (
        "13000000 Hz, the design target for the fundamental; a chosen "
        "number, not a measured resonance"),
    "BVD": ("Butterworth-Van Dyke equivalent circuit, the standard "
            "small-signal model of a piezoelectric resonator"),
}

VERDICTS = (
    "RESONATOR_MODEL_ONLY",
    "ODD_OVERTONE_REQUIRED",
    "FREESPACE_WAVELENGTH_REFUSED_IN_QUARTZ",
    "PHYSICAL_VALIDATION_NOT_CLAIMED",
)


class MicrocrystalError(RuntimeError):
    """Raised for any refusal: an even overtone, a free-space wavelength
    used inside the crystal, or an inconsistent BVD branch."""


# --- period and the (free-space) wavelength arithmetic ------------------

def period_seconds(frequency_hz: Fraction | float = NOMINAL_FREQUENCY_HZ
                   ) -> float:
    """T = 1/f. For 13 MHz this is ~76.923076923 ns."""
    f = float(frequency_hz)
    if f <= 0:
        raise MicrocrystalError("frequency must be positive")
    return 1.0 / f


def period_ns(frequency_hz: Fraction | float = NOMINAL_FREQUENCY_HZ) -> float:
    """The period in nanoseconds; ~76.923076923 ns at 13 MHz."""
    return period_seconds(frequency_hz) * 1e9


def freespace_wavelength_m(frequency_hz: Fraction | float
                           = NOMINAL_FREQUENCY_HZ) -> float:
    """lambda0 = c/f, the FREE-SPACE electromagnetic wavelength.

    ~23.060958307692 m at 13 MHz. This is arithmetic about a vacuum EM
    wave; it is NOT the acoustic wavelength inside quartz. See
    :func:`refuse_freespace_wavelength_in_quartz`.
    """
    f = float(frequency_hz)
    if f <= 0:
        raise MicrocrystalError("frequency must be positive")
    return C_M_PER_S / f


def freespace_quarter_wavelength_m(frequency_hz: Fraction | float
                                   = NOMINAL_FREQUENCY_HZ) -> float:
    """lambda0/4; ~5.765239576923 m at 13 MHz. Free-space, not in quartz."""
    return freespace_wavelength_m(frequency_hz) / 4.0


#: Cached free-space values for 13 MHz, as arithmetic only.
LAMBDA0_M = freespace_wavelength_m()
LAMBDA0_QUARTER_M = freespace_quarter_wavelength_m()


def refuse_freespace_wavelength_in_quartz(
        refractive_index: float | None = None,
        mode: str | None = None,
        cut: str | None = None,
        temperature_c: float | None = None,
        propagation_direction: str | None = None) -> float:
    """Refuse to use the free-space wavelength as a length inside quartz.

    The acoustic wave in the crystal has a wavelength set by the material
    velocity of the specific cut and mode, the overtone, the temperature
    and the propagation direction -- and it is about five orders of
    magnitude shorter than the free-space EM wavelength. Passing all of
    those in still does not license reusing ``lambda0``; the correct
    length is ``v_acoustic / f``, an entirely different quantity. So this
    function refuses unconditionally, and the required arguments exist
    only to name what a genuine in-crystal calculation would demand.
    """
    raise MicrocrystalError(
        "the free-space wavelength lambda0 = c/f (~23.06 m at 13 MHz) is "
        "an electromagnetic vacuum length and must not be used as a "
        "length inside quartz. The acoustic wavelength there is "
        "v_acoustic/f, set by the cut, mode, overtone, temperature and "
        "propagation direction, and is smaller by roughly five orders of "
        "magnitude. Substituting lambda0 for it is a category error. "
        "FREESPACE_WAVELENGTH_REFUSED_IN_QUARTZ.")


# --- the BVD equivalent circuit -----------------------------------------

def bvd_series_resonance_hz(lm_h: float, cm_f: float) -> float:
    """Series resonance fs = 1/(2*pi*sqrt(Lm*Cm)).

    The motional branch alone resonates here; C0 does not enter.
    """
    if lm_h <= 0 or cm_f <= 0:
        raise MicrocrystalError("Lm and Cm must be positive")
    return 1.0 / (2.0 * math.pi * math.sqrt(lm_h * cm_f))


def bvd_parallel_resonance_hz(fs_hz: float, cm_f: float, c0_f: float) -> float:
    """Parallel (anti-)resonance fp = fs*sqrt(1 + Cm/C0).

    Always above fs whenever Cm, C0 > 0, so fs < fp is structural.
    """
    if fs_hz <= 0:
        raise MicrocrystalError("fs must be positive")
    if cm_f <= 0 or c0_f <= 0:
        raise MicrocrystalError("Cm and C0 must be positive")
    return fs_hz * math.sqrt(1.0 + cm_f / c0_f)


def bvd_quality_factor(fs_hz: float, lm_h: float, rm_ohm: float) -> float:
    """Q = (2*pi*fs*Lm)/Rm."""
    if rm_ohm <= 0:
        raise MicrocrystalError("Rm must be positive")
    if fs_hz <= 0 or lm_h <= 0:
        raise MicrocrystalError("fs and Lm must be positive")
    return (2.0 * math.pi * fs_hz * lm_h) / rm_ohm


def quality_factor_from_cm(fs_hz: float, cm_f: float, rm_ohm: float) -> float:
    """Q = 1/(2*pi*fs*Cm*Rm), the equivalent motional-capacitance form.

    Equal to :func:`bvd_quality_factor` on a consistent branch, because
    ``2*pi*fs*Lm == 1/(2*pi*fs*Cm)`` at series resonance.
    """
    if rm_ohm <= 0:
        raise MicrocrystalError("Rm must be positive")
    if fs_hz <= 0 or cm_f <= 0:
        raise MicrocrystalError("fs and Cm must be positive")
    return 1.0 / (2.0 * math.pi * fs_hz * cm_f * rm_ohm)


def recover_lm_h(fs_hz: float, cm_f: float) -> float:
    """Invert the series-resonance relation: Lm = 1/((2*pi*fs)**2 * Cm).

    This is the estimator with power -- given a measured-in-principle fs
    and a known Cm it recovers the motional inductance, and feeding that
    Lm back through :func:`bvd_series_resonance_hz` returns fs exactly.
    """
    if fs_hz <= 0 or cm_f <= 0:
        raise MicrocrystalError("fs and Cm must be positive")
    return 1.0 / ((2.0 * math.pi * fs_hz) ** 2 * cm_f)


# --- the Leeson phase-noise SHAPE (qualitative, typed) ------------------

class NoiseRegion(Enum):
    """The three regions of the Leeson phase-noise shape."""

    FLICKER_FM = "1/f^3"      # close-in, up-converted flicker
    THERMAL_FM = "1/f^2"      # white-frequency / thermal FM
    NOISE_FLOOR = "flat"      # far-out white phase floor


@dataclass(frozen=True)
class LeesonModel:
    """A qualitative Leeson oscillator phase-noise shape.

    ``flicker_corner_hz`` separates the 1/f^3 and 1/f^2 regions;
    ``leeson_corner_hz`` (the resonator half-bandwidth fs/(2Q)) separates
    the 1/f^2 region from the flat floor. This is a shape, not a spectrum:
    no L(f) in dBc/Hz is asserted, only which region an offset lies in and
    the slope there.
    """

    flicker_corner_hz: float
    leeson_corner_hz: float

    def __post_init__(self) -> None:
        if self.flicker_corner_hz <= 0 or self.leeson_corner_hz <= 0:
            raise MicrocrystalError("corner frequencies must be positive")

    def region(self, offset_hz: float) -> NoiseRegion:
        """Which qualitative region an offset from the carrier lies in."""
        if offset_hz <= 0:
            raise MicrocrystalError("offset must be positive")
        if offset_hz < self.flicker_corner_hz:
            return NoiseRegion.FLICKER_FM
        if offset_hz < self.leeson_corner_hz:
            return NoiseRegion.THERMAL_FM
        return NoiseRegion.NOISE_FLOOR

    def slope_per_decade(self, offset_hz: float) -> int:
        """The power-law exponent of the region (-3, -2, or 0)."""
        return {NoiseRegion.FLICKER_FM: -3,
                NoiseRegion.THERMAL_FM: -2,
                NoiseRegion.NOISE_FLOOR: 0}[self.region(offset_hz)]


def leeson_corner_hz(fs_hz: float, q: float) -> float:
    """The Leeson corner, the resonator half-bandwidth fs/(2Q)."""
    if fs_hz <= 0 or q <= 0:
        raise MicrocrystalError("fs and Q must be positive")
    return fs_hz / (2.0 * q)


DRIVE_LEVEL_NOTE = (
    "drive-level dependence: motional resistance Rm, and therefore Q and "
    "the exact resonance, shift with the power dissipated in the crystal "
    "(drive-level dependence / DLD). The BVD parameters here are "
    "small-signal constants and carry no drive-level model; any Rm(P) or "
    "amplitude-frequency effect would require measurement.")


# --- the schema ---------------------------------------------------------

@dataclass(frozen=True)
class Resonator:
    """The specification schema for a quartz microcrystal resonator.

    Every field is a *specification*, not a measurement. The motional
    parameters (Lm, Cm, Rm, C0) define the BVD circuit; fs, fp and Q are
    derived from them and may be left as None until computed. The
    overtone must be odd for a thickness-shear mode.
    """

    resonator_id: str
    material: str = "quartz"
    cut: str = "AT"
    dimensions: str = "UNSPECIFIED"
    electrodes: str = "UNSPECIFIED"
    overtone: int = 1
    nominal_frequency: Fraction = NOMINAL_FREQUENCY_HZ
    fs: float | None = None
    fp: float | None = None
    Q: float | None = None
    C0: float | None = None
    Cm: float | None = None
    Lm: float | None = None
    Rm: float | None = None
    temperature_coefficient: str = "UNSPECIFIED"
    drive_level: str = "UNSPECIFIED"
    phase_noise: str = "UNSPECIFIED"
    packaging: str = "UNSPECIFIED"
    provenance: str = "specification only; nothing measured"
    status: str = "MODEL_ONLY"

    def __post_init__(self) -> None:
        if self.overtone < 1:
            raise MicrocrystalError("overtone must be a positive integer")
        if self.overtone % 2 == 0:
            raise MicrocrystalError(
                f"overtone {self.overtone} is even; a thickness-shear "
                f"resonator supports only ODD overtones (1, 3, 5, ...). "
                f"ODD_OVERTONE_REQUIRED.")

    @classmethod
    def from_bvd(cls, resonator_id: str, *, lm_h: float, cm_f: float,
                 rm_ohm: float, c0_f: float, overtone: int = 1,
                 **kwargs) -> "Resonator":
        """Build a resonator from its BVD branch, computing fs, fp, Q.

        The three derived quantities are guaranteed self-consistent and
        physically ordered (fs < fp) by construction.
        """
        fs = bvd_series_resonance_hz(lm_h, cm_f)
        fp = bvd_parallel_resonance_hz(fs, cm_f, c0_f)
        q = bvd_quality_factor(fs, lm_h, rm_ohm)
        return cls(resonator_id=resonator_id, overtone=overtone,
                   fs=fs, fp=fp, Q=q, Lm=lm_h, Cm=cm_f, Rm=rm_ohm,
                   C0=c0_f, **kwargs)


def make_13mhz_resonator(resonator_id: str = "MC13") -> Resonator:
    """A synthetic, self-consistent 13 MHz fundamental BVD example.

    The motional parameters are representative textbook values for a
    13 MHz AT-cut fundamental; they are chosen so fs lands on the 13 MHz
    target, and they are NOT measured. Cm is picked, Lm is solved from
    the target fs, and Rm/C0 are typical.
    """
    cm_f = 5.0e-15                       # 5 fF, representative motional C
    fs_target = float(NOMINAL_FREQUENCY_HZ)
    lm_h = recover_lm_h(fs_target, cm_f)  # solve Lm for the target fs
    rm_ohm = 8.0                          # representative ESR
    c0_f = 3.0e-12                        # 3 pF static capacitance
    return Resonator.from_bvd(
        resonator_id, lm_h=lm_h, cm_f=cm_f, rm_ohm=rm_ohm, c0_f=c0_f,
        cut="AT", overtone=1, dimensions="UNSPECIFIED",
        temperature_coefficient="AT-cut cubic, ~ppm scale (unspecified)",
        drive_level=DRIVE_LEVEL_NOTE, packaging="UNSPECIFIED")


# --- the report ---------------------------------------------------------

def microcrystal_report() -> dict:
    return {
        "what_this_is": (
            "the Butterworth-Van Dyke equivalent circuit of a 13 MHz "
            "quartz microcrystal resonator; textbook small-signal DSP of "
            "a piezoelectric part"),
        "the_real_result": (
            "the motional branch (Lm, Cm, Rm) in parallel with the static "
            "C0 gives fs = 1/(2*pi*sqrt(Lm*Cm)), fp = fs*sqrt(1+Cm/C0), "
            "and Q = 2*pi*fs*Lm/Rm; fs < fp is structural"),
        "period_ns_at_13mhz": period_ns(),
        "freespace_wavelength_m": LAMBDA0_M,
        "freespace_quarter_wavelength_m": LAMBDA0_QUARTER_M,
        "refusals": [
            "even overtones are refused: only odd overtones exist for a "
            "thickness-shear mode (ODD_OVERTONE_REQUIRED)",
            "the free-space wavelength must not be used inside quartz: the "
            "acoustic wavelength is v_acoustic/f, ~5 orders of magnitude "
            "shorter (FREESPACE_WAVELENGTH_REFUSED_IN_QUARTZ)",
        ],
        "phase_noise_model": (
            "Leeson shape only: 1/f^3 close-in, then 1/f^2, then a flat "
            "floor; a qualitative shape, never a measured L(f)"),
        "drive_level_note": DRIVE_LEVEL_NOTE,
        "provenance": PROVENANCE,
        "verdicts": list(VERDICTS),
        "evidence_class": "DERIVED_MATHEMATICS",
        "hardware_status": "DEFERRED — no crystal cut, mounted, or driven",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "RESONATOR_MODEL_ONLY",
        "what_this_does_not_say": (
            "It does not say any crystal exists, was cut, mounted, or "
            "driven, or that any resonance, Q, or phase noise was "
            "measured. It does not say 13 MHz maps to a length in the "
            "stone: the free-space wavelength is arithmetic about a vacuum "
            "EM wave, not the acoustic wavelength inside quartz. The BVD "
            "quantities are definitions of a circuit model, computed, not "
            "observed."),
    }
