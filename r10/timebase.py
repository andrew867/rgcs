"""P09 — frequency/time standards, modelled from official primary sources.

The source material reaches for the cesium clock, the "wavelength" of a
transition, and atomic time as if quoting them settled something. They
are worth quoting *exactly* -- and quoting them exactly is precisely what
stops them from settling anything here. This module models the SI time
and frequency standards from their **primary definitions** (BIPM, and the
national metrology institutes that realise them) and refuses the two
moves the lore invites: reading a nominal number as a measured one, and
turning a vacuum wavelength into a wavelength in matter for free.

**What is exact by definition, and therefore not a measurement.** Since
1967 the SI second is *defined* by the cesium-133 ground-state hyperfine
transition frequency, fixed at exactly ``9 192 631 770 Hz`` (BIPM SI
Brochure, 9th ed.). That integer is not the result of a measurement with
an error bar; it is the definition that *gives* the second its length, so
its uncertainty is **zero by definition**. A clock's job is to *realise*
that definition, and the realisation -- a cesium fountain such as NIST-F1
/ NIST-F2, or an optical standard -- is where the uncertainty lives.
:func:`si_second_definition` reports the definition; the module never
dresses it up as something this project measured.

**Vacuum wavelength is arithmetic; a medium wavelength is not.** With the
speed of light fixed at exactly ``299 792 458 m/s`` (the SI definition of
the metre), ``lambda = c / f`` is exact in vacuum -- for the cesium
hyperfine line, about ``0.0326 m`` (~3.26 cm), a microwave, not light.
:func:`vacuum_wavelength_m` returns it. But the wavelength *in a material*
is ``lambda / n(f)``, and without the medium's refractive index there is
no answer. :func:`refuse_medium_wavelength_without_index` refuses to
invent one.

**A nominal frequency is not a measured frequency.** A standard's
*nominal* value (what it is meant to produce) and its *measured* value
(what a comparison against a reference actually found, with an Allan
deviation and an uncertainty budget) are different objects.
:func:`refuse_nominal_as_measured` keeps them apart, and every
:class:`Timebase` here carries ``measured_frequency = None`` with status
``BLOCKED_NO_DATA_SOURCE``: no live standard is compared in this
environment, and that gap is declared, not faked.

**A real estimator, so the module has power.** :func:`overlapping_allan_deviation`
is the standard overlapping Allan deviation ``sigma_y(tau)`` for a
fractional-frequency series -- the workhorse of the field. It is exercised
on synthetic white-frequency noise, where theory demands
``sigma_y(tau) ~ tau^{-1/2}``, and the estimator recovers that slope.

Nothing here is measured. The default verdict is ``STANDARDS_MODEL_ONLY``:
literature definitions and honest arithmetic, with no bench and no live
data feed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction

import numpy as np

# --- exact SI constants, with provenance -------------------------------

#: The SI second: the cesium-133 ground-state hyperfine transition
#: frequency, fixed at EXACTLY this integer by the definition of the
#: second (BIPM SI Brochure, 9th ed., 2019). It defines the second, so it
#: carries ZERO uncertainty by definition -- it is not a measurement.
CS_HYPERFINE_HZ: int = 9_192_631_770

#: The speed of light in vacuum, fixed EXACTLY by the SI definition of the
#: metre (BIPM SI Brochure, 9th ed., 2019).
C_M_PER_S: int = 299_792_458

#: Real primary-standard references. These are conventional public
#: metrology documents, not project results and not source-corpus claims.
PRIMARY_SOURCES: tuple[str, ...] = (
    "BIPM, The International System of Units (SI Brochure), 9th ed. "
    "(2019): definition of the second via the cesium-133 hyperfine "
    "transition frequency, exactly 9 192 631 770 Hz",
    "BIPM SI Brochure, 9th ed. (2019): definition of the metre via the "
    "speed of light in vacuum, exactly 299 792 458 m/s",
    "NIST cesium fountain primary frequency standards NIST-F1 / NIST-F2 "
    "documentation (realisation of the SI second)",
    "BIPM Circular T / TAI-UTC bulletins (international atomic time "
    "scale, computed from contributing clocks)",
    "IEEE Std 1139: standard definitions of physical quantities for "
    "fundamental frequency and time metrology (Allan deviation and "
    "related measures)",
)

#: Averaging-time bins, as a modelling convenience.
DEFAULT_VERDICT = "STANDARDS_MODEL_ONLY"
LIVE_DATA_STATUS = "BLOCKED_NO_DATA_SOURCE"


class TimebaseError(ValueError):
    """Raised when a time/frequency standard is misrepresented."""


# --- the schema ---------------------------------------------------------

class SourceType(Enum):
    """The kind of frequency/time source being modelled."""

    CESIUM_PRIMARY = "cesium_primary"          # SI-second realisation
    HYDROGEN_MASER = "hydrogen_maser"
    RUBIDIUM = "rubidium"
    OCXO = "ovenized_crystal_oscillator"
    OPTICAL_LATTICE = "optical_lattice_clock"
    DEFINITION = "definition"                  # not a device: the SI second


@dataclass(frozen=True)
class Timebase:
    """A modelled time/frequency standard.

    ``nominal_frequency`` is what the standard is *meant* to produce.
    ``measured_frequency`` is what a comparison against a reference
    *found*; here it is ``None`` because no comparison is run, and
    ``status`` records why. The two are never conflated.
    """

    timebase_id: str
    source_type: SourceType
    nominal_frequency: Fraction | None
    measured_frequency: Fraction | None
    uncertainty: Fraction | None               # (1-sigma) fractional; 0 => exact-by-definition
    phase_noise: float | None                  # dBc/Hz at a stated offset, if known
    Allan_deviation: float | None              # sigma_y at a stated tau, if known
    temperature: float | None                  # K, if specified
    aging: float | None                        # fractional/day, if specified
    wavelength_model: str                       # how a wavelength would be derived
    medium: str                                 # "vacuum" | material | "N/A"
    primary_source_reference: str
    calibration_date: str | None
    status: str

    def __post_init__(self) -> None:
        if not self.primary_source_reference:
            raise TimebaseError(
                f"{self.timebase_id}: a standard needs a primary-source "
                f"reference; an unsourced number is not a standard")
        if self.measured_frequency is not None \
                and self.status != "MEASURED":
            raise TimebaseError(
                f"{self.timebase_id}: a measured_frequency is set but the "
                f"status is not MEASURED; a value without a comparison is "
                f"nominal, not measured")


#: The SI second itself -- a DEFINITION, not a device and not a
#: measurement. Its uncertainty is exactly zero because it *fixes* the
#: second; there is nothing to compare it against.
CESIUM_SI_SECOND = Timebase(
    timebase_id="SI_SECOND_CS133",
    source_type=SourceType.DEFINITION,
    nominal_frequency=Fraction(CS_HYPERFINE_HZ),
    measured_frequency=None,                    # a definition is not measured
    uncertainty=Fraction(0),                    # zero BY DEFINITION
    phase_noise=None,
    Allan_deviation=None,
    temperature=None,
    aging=None,
    wavelength_model="vacuum: lambda = c / f (exact)",
    medium="vacuum",
    primary_source_reference=PRIMARY_SOURCES[0],
    calibration_date=None,                       # definitions are not calibrated
    status="DEFINITION_EXACT",
)


#: A realisation of the definition -- e.g. a cesium fountain. Its nominal
#: frequency is the defined value; its MEASURED frequency and uncertainty
#: would come from a comparison this environment does not run.
CESIUM_FOUNTAIN_MODEL = Timebase(
    timebase_id="CS_FOUNTAIN_MODEL",
    source_type=SourceType.CESIUM_PRIMARY,
    nominal_frequency=Fraction(CS_HYPERFINE_HZ),
    measured_frequency=None,                     # no live comparison
    uncertainty=None,                            # unknown without data
    phase_noise=None,
    Allan_deviation=None,
    temperature=None,
    aging=None,
    wavelength_model="vacuum: lambda = c / f (exact); medium requires n(f)",
    medium="vacuum",
    primary_source_reference=PRIMARY_SOURCES[2],
    calibration_date=None,
    status=LIVE_DATA_STATUS,
)

TIMEBASES = (CESIUM_SI_SECOND, CESIUM_FOUNTAIN_MODEL)


# --- the SI second, as a definition -------------------------------------

def si_second_definition() -> dict:
    """Report the SI second as a definition with zero uncertainty.

    The number is exact because it *defines* the second. Treating it as a
    measurement -- attaching an error bar, or claiming this project found
    it -- would be a category error.
    """
    return {
        "cs_hyperfine_hz": CS_HYPERFINE_HZ,
        "is_exact_integer": CS_HYPERFINE_HZ == 9_192_631_770,
        "uncertainty": 0,
        "uncertainty_kind": "ZERO_BY_DEFINITION",
        "measured_here": "nothing",
        "primary_source_reference": PRIMARY_SOURCES[0],
        "note": (
            "9 192 631 770 Hz is the DEFINITION of the second, not a "
            "measurement with an error bar. Its realisation by a cesium "
            "fountain carries uncertainty; the definition does not"),
    }


# --- wavelengths --------------------------------------------------------

def vacuum_wavelength_m(f_hz: float | int | Fraction) -> float:
    """Vacuum wavelength ``lambda = c / f`` in metres.

    Exact arithmetic on exact SI constants. For the cesium hyperfine line
    this is about ``0.0326 m`` -- a microwave, not visible light.
    """
    f = float(f_hz)
    if f <= 0:
        raise TimebaseError("frequency must be positive to give a wavelength")
    return C_M_PER_S / f


def refuse_medium_wavelength_without_index(
        f_hz: float | int | Fraction,
        refractive_index: float | None = None) -> None:
    """Refuse a wavelength in a material medium without its index.

    In matter the wavelength is ``lambda_vac / n(f)``. The refractive
    index is frequency-dependent and material-specific; without it there
    is no medium wavelength to give, and assuming ``n = 1`` (vacuum) is
    inventing the medium away.
    """
    if refractive_index is not None:
        # a caller who supplies n has not asked for the refusal; still,
        # this function's contract is to refuse, so signal misuse.
        raise TimebaseError(
            "refuse_medium_wavelength_without_index is a refusal; to "
            "compute a medium wavelength with a known index use "
            "vacuum_wavelength_m(f) / n directly")
    raise TimebaseError(
        f"cannot give a wavelength in a medium for f = {float(f_hz):g} Hz "
        f"without a refractive index n(f). The medium wavelength is "
        f"lambda_vac / n(f); n is frequency-dependent and "
        f"material-specific, and assuming n = 1 silently substitutes "
        f"vacuum for the medium. Supply n(f) or state 'vacuum' "
        f"explicitly.")


# --- nominal vs measured ------------------------------------------------

def refuse_nominal_as_measured(tb: Timebase) -> None:
    """Refuse to read a nominal frequency as a measured one.

    A nominal value is what a standard is meant to produce; a measured
    value is what a comparison against a reference found, with an Allan
    deviation and an uncertainty budget. No comparison is run here, so
    every measured_frequency is None and must stay None.
    """
    if tb.measured_frequency is not None and tb.status == "MEASURED":
        return
    raise TimebaseError(
        f"{tb.timebase_id}: nominal_frequency "
        f"({tb.nominal_frequency} Hz) is what this standard is meant to "
        f"produce, not what was measured. There is no measured frequency "
        f"({LIVE_DATA_STATUS}): no live comparison against a reference is "
        f"run in this environment, so a nominal number cannot be reported "
        f"as a measurement.")


# --- the overlapping Allan deviation estimator --------------------------

def overlapping_allan_deviation(y: np.ndarray | list,
                                tau0: float,
                                m: int) -> float:
    """Overlapping Allan deviation ``sigma_y(tau)`` at ``tau = m * tau0``.

    ``y`` is a series of fractional-frequency samples spaced ``tau0`` in
    time; ``m`` is the averaging factor. Computed via the phase-data form

        sigma_y^2(tau) = 1 / (2 (N - 2m) tau^2)
                         * sum_i (x_{i+2m} - 2 x_{i+m} + x_i)^2

    where the phase ``x`` is the cumulative sum of ``y`` scaled by
    ``tau0``. This is the standard overlapping estimator (IEEE Std 1139),
    using all overlapping samples for a lower-variance estimate.
    """
    y = np.asarray(y, dtype=float)
    if y.ndim != 1:
        raise TimebaseError("y must be a 1-D fractional-frequency series")
    if tau0 <= 0:
        raise TimebaseError("tau0 must be positive")
    if m < 1:
        raise TimebaseError("averaging factor m must be >= 1")
    M = y.size
    # phase data x has M+1 points: x_0 = 0, x_k = tau0 * sum_{i<k} y_i
    x = np.concatenate(([0.0], np.cumsum(y))) * tau0
    N = x.size                                   # = M + 1 phase points
    if N - 2 * m < 1:
        raise TimebaseError(
            f"series too short: need at least 2m+1 = {2 * m + 1} phase "
            f"points for m = {m}, have {N}")
    tau = m * tau0
    second_diff = x[2 * m:] - 2 * x[m:N - m] + x[:N - 2 * m]
    n_terms = second_diff.size                   # = N - 2m
    avar = float(np.sum(second_diff * second_diff)) / (2.0 * tau * tau * n_terms)
    return math.sqrt(avar)


def allan_deviation_sweep(y: np.ndarray | list, tau0: float,
                          factors: tuple[int, ...] | list) -> dict:
    """``sigma_y(tau)`` at several averaging factors, for a slope fit."""
    taus, adevs = [], []
    for m in factors:
        taus.append(m * tau0)
        adevs.append(overlapping_allan_deviation(y, tau0, m))
    return {"tau": taus, "adev": adevs, "factors": list(factors)}


# --- report -------------------------------------------------------------

def timebase_report() -> dict:
    return {
        "what_this_is": (
            "the SI time and frequency standards modelled from their "
            "primary definitions (BIPM) and realisations (national "
            "metrology institutes), with a standard Allan-deviation "
            "estimator"),
        "si_second": si_second_definition(),
        "cesium_hyperfine_hz": CS_HYPERFINE_HZ,
        "cesium_vacuum_wavelength_m": vacuum_wavelength_m(CS_HYPERFINE_HZ),
        "speed_of_light_m_per_s": C_M_PER_S,
        "timebases": [
            {"timebase_id": t.timebase_id,
             "source_type": t.source_type.value,
             "nominal_frequency": (str(t.nominal_frequency)
                                   if t.nominal_frequency is not None
                                   else None),
             "measured_frequency": (str(t.measured_frequency)
                                    if t.measured_frequency is not None
                                    else None),
             "uncertainty": (str(t.uncertainty)
                             if t.uncertainty is not None else None),
             "medium": t.medium,
             "wavelength_model": t.wavelength_model,
             "primary_source_reference": t.primary_source_reference,
             "status": t.status}
            for t in TIMEBASES],
        "distinctions_enforced": [
            "the SI second is a DEFINITION with zero uncertainty, not a "
            "measurement (refuse to attach an error bar to the "
            "definition)",
            "a nominal frequency is not a measured frequency "
            "(refuse_nominal_as_measured)",
            "a vacuum wavelength is not a medium wavelength without n(f) "
            "(refuse_medium_wavelength_without_index)",
        ],
        "primary_sources": list(PRIMARY_SOURCES),
        "verdict": DEFAULT_VERDICT,
        "live_measured_data_status": LIVE_DATA_STATUS,
        "evidence_class": "CONVENTIONAL_LITERATURE",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "what_this_does_not_say": (
            "It does not measure any clock, compare any standard against "
            "a reference, or claim a frequency, an Allan deviation, or an "
            "uncertainty budget for real hardware. It quotes the SI "
            "definitions exactly, does the exact arithmetic they license "
            "(vacuum lambda = c/f), and refuses the rest: a nominal value "
            "is not a measurement, and a vacuum wavelength is not a "
            "wavelength in matter. No live standard is read "
            f"({LIVE_DATA_STATUS}), and that gap is declared, not faked."),
    }
