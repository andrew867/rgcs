"""P03 — pulse spectrum, matched-energy control, and piezoelectric response.

Source claim R6-C-005 (verbatim, see :mod:`r6.claims`):

    "Why is it that the singularity vortex only opens when
    piezoelectrically stimulated? Because of the pulse."

The only defensible content in that sentence is a statement about
signals: **a pulse has broadband spectral content that a sinusoid does
not**. That is true, it is elementary Fourier analysis, and it is
testable. "Singularity vortex" has no definition, no instrument and no
proposed signature; this module does not model it, does not detect it,
and does not name it as a state. The claim ceiling stands at
"a bandwidth-dependent response".

NOTHING IN THIS MODULE IS BENCH DATA. No crystal has been driven, no
charge collected, no spectrum measured. Every number here is either a
closed-form evaluation of an analytic model or a literature constant
cited at its point of use. The programme has taken no measurements.

The mandatory control
---------------------
Any claim of the form "the pulse did it" is confounded with "the pulse
delivered more energy" until it is tested against a sinusoidal drive
carrying the *same total energy* at a single frequency. That control is
:func:`matched_energy_sinusoid`, and R6 treats a pulse/sinusoid
comparison without it as uninterpretable rather than as weak evidence.

The null
--------
:func:`source_frequency_audit` carries the v4.6 lesson: the null must be
matched to the *granularity* of the candidate set. The three source
frequencies are quoted as integers in Hz, so the null draws integer-Hz
triples from the same declared band. A continuum null over the same band
would make almost any integer triple look "close to something" and is
the exact error v4.6 was built to stop repeating. The audit reports the
p-value it computes, whatever it is, and never upgrades a result it did
not obtain.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Literal, Sequence

# --- literature constants ------------------------------------------------
# All values below are LITERATURE VALUES for alpha-quartz (SiO2, trigonal,
# class 32). They are cited here as published constants; none of them was
# measured by this programme.

#: Piezoelectric strain coefficient d11 of alpha-quartz, C/N.
#: Literature value (standard piezoelectric-materials tables, e.g. IEEE
#: Std 176 / Bechmann's constants for alpha-quartz at 25 C).
#: NOT MEASURED BY THIS PROGRAMME.
D11_QUARTZ_C_PER_N = 2.31e-12

#: Piezoelectric strain coefficient d14 of alpha-quartz, C/N (shear).
#: Literature value, same source family as d11. Sign conventions for d14
#: differ between references and with crystal handedness; magnitude only
#: is used here. NOT MEASURED BY THIS PROGRAMME.
D14_QUARTZ_C_PER_N = 0.727e-12

#: Vacuum permittivity, SI (CODATA; exact-by-definition chain since 2019
#: is via c and mu0, so this is a defined-derived constant).
EPS0_F_PER_M = 8.8541878128e-12

#: Relative permittivity eps11/eps0 of alpha-quartz at constant strain,
#: perpendicular to the optic axis. Literature value ~4.52 (quartz is
#: anisotropic: eps33/eps0 ~ 4.63). NOT MEASURED BY THIS PROGRAMME.
#: The capacitor model below uses eps11 because the d11 charge is
#: collected on the X faces.
EPS11_REL_QUARTZ = 4.52

#: Longitudinal (extensional) acoustic velocity in alpha-quartz along the
#: X axis, m/s. Literature value ~5720 m/s. Quartz is strongly
#: anisotropic and the velocity along Z is different (~6320 m/s), so the
#: axis must always be stated. NOT MEASURED BY THIS PROGRAMME.
QUARTZ_LONGITUDINAL_VELOCITY_X_MS = 5720.0

#: The three drive frequencies asserted by the source corpus (claim
#: R6-C-006, verbatim "1496 Hz preferred; 644 Hz; 587 Hz"). Integers in
#: Hz — that granularity is what the null must match.
SOURCE_FREQUENCIES_HZ: tuple[int, ...] = (1496, 644, 587)

#: Declared null band for the frequency audit, integers in Hz inclusive.
#: Declared as a fixed prior so it cannot be retuned after seeing a
#: p-value. It is the audio decade containing the source triple. Widening
#: or narrowing this band changes the p-value; the band is therefore
#: reported alongside every audit result.
NULL_BAND_HZ: tuple[int, int] = (100, 2000)

#: RNG seed for the frequency-audit null. Fixed and documented so the
#: p-value is reproducible; it is the corpus amendment date.
NULL_SEED = 20260718

#: Number of null draws. Fixed; with the add-one estimator the smallest
#: reportable p-value is 1/(N+1).
NULL_DRAWS = 20000

#: Significance threshold declared in advance.
ALPHA = 0.05

ShapeName = Literal["RECT", "GAUSSIAN", "TRAPEZOID"]

_SHAPES: tuple[str, ...] = ("RECT", "GAUSSIAN", "TRAPEZOID")


class PulseModelError(ValueError):
    """Raised when a pulse specification is not physically meaningful."""


def _sinc(x: float) -> float:
    """Unnormalized sinc: sin(x)/x, with sinc(0) = 1."""
    if x == 0.0:
        return 1.0
    return math.sin(x) / x


def cmath_exp(theta: float) -> complex:
    """exp(j*theta) written out, so the phase convention is visible."""
    return complex(math.cos(theta), math.sin(theta))


# --- pulse specification -------------------------------------------------

@dataclass(frozen=True)
class PulseShape:
    """One drive pulse, specified by its timing and amplitude.

    Parameters
    ----------
    rise_s, width_s, fall_s
        Rise time, flat-top width and fall time in seconds. Their
        interpretation depends on ``shape``:

        - ``RECT``: ``width_s`` is the full duration. ``rise_s`` and
          ``fall_s`` must be zero — a rectangle with a finite edge is a
          trapezoid, and pretending otherwise would understate the
          high-frequency content.
        - ``TRAPEZOID``: linear ramps of ``rise_s`` and ``fall_s`` around
          a flat top of ``width_s``. Total duration is the sum.
        - ``GAUSSIAN``: ``width_s`` is the full width at half maximum
          (FWHM). Ramps are not separately specified and must be zero;
          the Gaussian has no edges to time.
    amplitude
        Peak drive amplitude, in whatever drive unit the caller is
        working in (volts, newtons, pascals). The module is
        unit-agnostic; energies are therefore reported in
        ``amplitude^2 * second``.
    shape
        One of ``RECT``, ``GAUSSIAN``, ``TRAPEZOID``.

    This is a model of a commanded waveform, not a recording of one.
    """

    rise_s: float
    width_s: float
    fall_s: float
    amplitude: float
    shape: ShapeName = "RECT"

    def __post_init__(self) -> None:
        if self.shape not in _SHAPES:
            raise PulseModelError(
                f"unknown pulse shape {self.shape!r}; expected one of "
                f"{_SHAPES}")
        for name in ("rise_s", "width_s", "fall_s"):
            v = getattr(self, name)
            if not math.isfinite(v) or v < 0.0:
                raise PulseModelError(
                    f"{name} must be finite and non-negative, got {v!r}")
        if not math.isfinite(self.amplitude):
            raise PulseModelError("amplitude must be finite")
        if self.width_s <= 0.0:
            raise PulseModelError(
                "width_s must be positive: a zero-width pulse has no "
                "energy and no spectrum")
        if self.shape == "RECT" and (self.rise_s or self.fall_s):
            raise PulseModelError(
                "RECT requires rise_s == fall_s == 0; a rectangle with a "
                "finite edge is a TRAPEZOID, and calling it RECT would "
                "understate its high-frequency content")
        if self.shape == "GAUSSIAN" and (self.rise_s or self.fall_s):
            raise PulseModelError(
                "GAUSSIAN requires rise_s == fall_s == 0; width_s is the "
                "FWHM and the Gaussian has no edges to time")

    # -- derived timing ---------------------------------------------------
    @property
    def duration_s(self) -> float:
        """Support of the pulse in seconds.

        For ``GAUSSIAN`` the support is infinite; the value returned is
        the conventional +/-3 sigma window (99.73% of the energy of the
        envelope), used only for windowing the matched-energy control.
        """
        if self.shape == "GAUSSIAN":
            return 6.0 * self.sigma_s
        return self.rise_s + self.width_s + self.fall_s

    @property
    def sigma_s(self) -> float:
        """Gaussian standard deviation from the FWHM.

        FWHM = 2*sqrt(2*ln2)*sigma, so sigma = FWHM / 2.35482...
        """
        if self.shape != "GAUSSIAN":
            raise PulseModelError("sigma_s is defined for GAUSSIAN only")
        return self.width_s / (2.0 * math.sqrt(2.0 * math.log(2.0)))


# --- spectra -------------------------------------------------------------

def spectrum(pulse: PulseShape, f_hz: float) -> float:
    """Analytic magnitude spectrum |X(f)| of ``pulse``, at ``f_hz``.

    Returns the magnitude of the continuous Fourier transform
    ``X(f) = integral x(t) exp(-j 2 pi f t) dt``, in units of
    ``amplitude * second``. Magnitude only: the phase of a pulse depends
    on where its time origin is placed and carries no claim.

    Closed forms
    ------------
    ``RECT`` (amplitude A, duration w)::

        |X(f)| = |A * w * sinc(pi f w)|,    sinc(x) = sin(x)/x

        The transform of a rectangle of width w is A*w*sin(pi f w)/(pi f w).
        First null at f = 1/w; the -3 dB point is at f ~ 0.4429/w. The
        envelope falls as 1/f, i.e. -20 dB/decade: this slow roll-off is
        the entire "broadband" content of a rectangular pulse.

    ``GAUSSIAN`` (amplitude A, FWHM w, sigma = w / (2*sqrt(2*ln2)))::

        x(t)   = A * exp(-t^2 / (2 sigma^2))
        |X(f)| = A * sigma * sqrt(2 pi) * exp(-2 pi^2 f^2 sigma^2)

        The Fourier transform of a Gaussian is a Gaussian. It has no
        nulls and no algebraic tail: the content dies exponentially, so a
        Gaussian pulse is markedly *less* broadband than a rectangle of
        the same duration. Any claim that "a pulse" supplies broadband
        excitation must therefore say which pulse.

    ``TRAPEZOID`` (amplitude A, rise r, flat w, fall g)::

        The derivative of the trapezoid is two rectangles, of height A/r
        on [0, r] and -A/g on [r+w, r+w+g]. With
        ``X(f) = FT{x'}(f) / (j 2 pi f)``,

            FT{x'}(f) = A sinc(pi f r) exp(-j pi f r)
                      - A sinc(pi f g) exp(-j 2 pi f (r + w + g/2))

        and |X(f)| is the magnitude of that divided by 2 pi f. For the
        symmetric case r == g this reduces exactly to

            |X(f)| = |A (w + r) sinc(pi f (w + r)) sinc(pi f r)|

        i.e. a rectangle of width (w+r) multiplied by a second sinc set
        by the edge time. The second factor imposes an additional 1/f
        roll-off above f ~ 1/r: finite edges are what actually bound the
        bandwidth of a real "square" pulse.

    All three are model evaluations. No spectrum in this module was
    measured.
    """
    if not math.isfinite(f_hz):
        raise PulseModelError("f_hz must be finite")
    a = pulse.amplitude

    if pulse.shape == "RECT":
        w = pulse.width_s
        return abs(a * w * _sinc(math.pi * f_hz * w))

    if pulse.shape == "GAUSSIAN":
        sigma = pulse.sigma_s
        return abs(a * sigma * math.sqrt(2.0 * math.pi)
                   * math.exp(-2.0 * (math.pi ** 2) * (f_hz ** 2)
                              * (sigma ** 2)))

    # TRAPEZOID
    r, w, g = pulse.rise_s, pulse.width_s, pulse.fall_s
    if r == 0.0 and g == 0.0:
        return abs(a * w * _sinc(math.pi * f_hz * w))
    if f_hz == 0.0:
        # DC term is the area of the trapezoid.
        return abs(a * (w + 0.5 * (r + g)))

    term1 = complex(_sinc(math.pi * f_hz * r), 0.0) * cmath_exp(
        -math.pi * f_hz * r)
    term2 = complex(_sinc(math.pi * f_hz * g), 0.0) * cmath_exp(
        -2.0 * math.pi * f_hz * (r + w + 0.5 * g))
    deriv = a * (term1 - term2)
    return abs(deriv / (1j * 2.0 * math.pi * f_hz))


def dc_magnitude(pulse: PulseShape) -> float:
    """|X(0)|, the pulse area. Closed form per shape (see spectrum)."""
    a = pulse.amplitude
    if pulse.shape == "RECT":
        return abs(a * pulse.width_s)
    if pulse.shape == "GAUSSIAN":
        return abs(a * pulse.sigma_s * math.sqrt(2.0 * math.pi))
    return abs(a * (pulse.width_s + 0.5 * (pulse.rise_s + pulse.fall_s)))


def total_energy(pulse: PulseShape) -> float:
    """Total signal energy ``E = integral x(t)^2 dt``.

    Units are ``amplitude^2 * second``. This is the quantity the
    matched-energy control equalizes.

    Closed forms::

        RECT       E = A^2 * w
        GAUSSIAN   E = A^2 * sigma * sqrt(pi)
                     (from integral exp(-t^2/sigma^2) dt = sigma sqrt(pi))
        TRAPEZOID  E = A^2 * (w + (r + g)/3)
                     (flat top A^2 w, plus A^2 r/3 and A^2 g/3 from the
                      two linear ramps)
    """
    a2 = pulse.amplitude ** 2
    if pulse.shape == "RECT":
        return a2 * pulse.width_s
    if pulse.shape == "GAUSSIAN":
        return a2 * pulse.sigma_s * math.sqrt(math.pi)
    return a2 * (pulse.width_s + (pulse.rise_s + pulse.fall_s) / 3.0)


def bandwidth_3db(pulse: PulseShape) -> float:
    """Half-power (-3 dB) bandwidth in Hz.

    The lowest positive frequency at which ``|X(f)| = |X(0)| / sqrt(2)``.
    Found by bracketing then bisection on the analytic magnitude, to a
    relative tolerance of 1e-12 — this is a root of a closed form, not a
    fit to data.

    Sanity anchors (both are standard results, and both are checked in
    the test suite): a rectangle of width w has ``B ~ 0.4429 / w``; a
    Gaussian of FWHM w has ``B = sqrt(ln 2) / (2 pi sigma)``.
    """
    target = dc_magnitude(pulse) / math.sqrt(2.0)
    if target <= 0.0:
        raise PulseModelError("pulse has zero area; -3 dB point undefined")

    # Bracket: start from a scale set by the pulse duration and walk up.
    scale = 1.0 / max(pulse.duration_s, 1e-30)
    lo, hi = 0.0, scale
    for _ in range(200):
        if spectrum(pulse, hi) < target:
            break
        lo = hi
        hi *= 2.0
    else:  # pragma: no cover - unreachable for the supported shapes
        raise PulseModelError("failed to bracket the -3 dB point")

    for _ in range(400):
        mid = 0.5 * (lo + hi)
        if spectrum(pulse, mid) > target:
            lo = mid
        else:
            hi = mid
        if hi - lo <= 1e-12 * max(hi, 1.0):
            break
    return 0.5 * (lo + hi)


def spectral_energy_fraction(pulse: PulseShape, f_lo: float,
                             f_hi: float, n_points: int = 4001) -> float:
    """Fraction of the pulse's energy lying in the band [f_lo, f_hi] Hz.

    By Parseval, ``E = integral |X(f)|^2 df`` over all f, and since
    ``|X(f)|`` is even for a real pulse the one-sided band energy is
    ``2 * integral_{f_lo}^{f_hi} |X(f)|^2 df``. The numerator is
    evaluated by composite Simpson's rule on the analytic ``|X(f)|`` with
    ``n_points`` samples (odd; deterministic, no RNG). The denominator is
    the closed-form :func:`total_energy`, so the returned fraction is not
    self-normalized and a quadrature error shows up as a fraction that
    does not converge to 1 over a wide band. That is deliberate.
    """
    if f_lo < 0.0 or f_hi < f_lo:
        raise PulseModelError("require 0 <= f_lo <= f_hi")
    if n_points < 3:
        raise PulseModelError("n_points must be at least 3")
    if n_points % 2 == 0:
        n_points += 1
    if f_hi == f_lo:
        return 0.0

    h = (f_hi - f_lo) / (n_points - 1)
    acc = 0.0
    for i in range(n_points):
        f = f_lo + i * h
        w = 1.0 if i in (0, n_points - 1) else (4.0 if i % 2 else 2.0)
        acc += w * spectrum(pulse, f) ** 2
    band = 2.0 * acc * h / 3.0
    return band / total_energy(pulse)


# --- the mandatory matched-energy control --------------------------------

@dataclass(frozen=True)
class SinusoidDrive:
    """A single-frequency drive used as the control for a pulse.

    ``x(t) = amplitude * sin(2 pi frequency_hz t)`` over
    ``duration_s``. Its energy equals the pulse's energy by construction.
    """

    amplitude: float
    frequency_hz: float
    duration_s: float
    energy: float
    matched_to: str
    note: str

    def energy_check(self) -> float:
        """Recompute the energy from the sinusoid's own parameters.

        ``E = A^2 * T / 2`` for an integer number of half-cycles, which
        is what :func:`matched_energy_sinusoid` guarantees. Provided so a
        caller can verify the match rather than trust it.
        """
        return 0.5 * self.amplitude ** 2 * self.duration_s


def matched_energy_sinusoid(pulse: PulseShape, f_hz: float) -> SinusoidDrive:
    """The mandatory control: a sinusoid at ``f_hz`` with the SAME energy.

    Why this is mandatory
    ---------------------
    A pulse and a sinusoid differ in two ways at once: spectral content
    and delivered energy. If a response appears under pulsed drive and
    not under sinusoidal drive, "the pulse did it" is confounded with
    "the pulse delivered more energy" until the two drives are equalized
    on energy. R6 therefore treats any pulse-versus-sinusoid comparison
    without this control as uninterpretable, not as weak support. This
    is the operational content of claim R6-C-005's required evidence
    entry "matched-energy sinusoidal control".

    Construction
    ------------
    The sinusoid runs for a duration equal to the pulse's own duration,
    rounded *up* to a whole number of half-cycles at ``f_hz`` so that
    ``E = A^2 T / 2`` holds exactly rather than approximately. The
    amplitude is then ``A = sqrt(2 E / T)`` with ``E`` from
    :func:`total_energy`.

    What it does not control for
    ----------------------------
    Equal energy is not equal peak amplitude, not equal peak power, not
    equal dE/dt, and not equal spectral phase. A response that tracks
    peak field or slew rate will differ between the two drives even
    though this control is satisfied. Those are separate controls and
    this function does not supply them.
    """
    if not math.isfinite(f_hz) or f_hz <= 0.0:
        raise PulseModelError("control frequency must be finite and > 0")

    energy = total_energy(pulse)
    if energy <= 0.0:
        raise PulseModelError("pulse carries no energy to match")

    half_cycle = 0.5 / f_hz
    n_half = max(1, math.ceil(pulse.duration_s / half_cycle))
    duration = n_half * half_cycle
    amplitude = math.sqrt(2.0 * energy / duration)

    return SinusoidDrive(
        amplitude=amplitude,
        frequency_hz=f_hz,
        duration_s=duration,
        energy=energy,
        matched_to=f"{pulse.shape} pulse, width_s={pulse.width_s!r}",
        note=("matched on total signal energy only; peak amplitude, peak "
              "power, slew rate and spectral phase are NOT matched and "
              "require separate controls"),
    )


# --- piezoelectric response ---------------------------------------------

def piezo_charge(stress_pa: float, area_m2: float,
                 d_coeff: float = D11_QUARTZ_C_PER_N) -> float:
    """Charge liberated on the electroded faces, in coulombs.

    The direct piezoelectric effect in the stress form is
    ``D = d * T`` (electric displacement = coefficient times stress), so
    the charge collected over an electrode of area ``A`` under uniform
    stress ``T`` is::

        Q = d * T * A          [C/N * N/m^2 * m^2 = C]

    equivalently ``Q = d * F`` for an applied force ``F = T * A``.

    ``d_coeff`` defaults to :data:`D11_QUARTZ_C_PER_N` (2.31e-12 C/N),
    the longitudinal coefficient for compression along X with charge
    collected on the X faces. Pass :data:`D14_QUARTZ_C_PER_N`
    (0.727e-12 C/N) for the shear mode. Both are LITERATURE VALUES for
    alpha-quartz; neither was measured by this programme.

    This is a linear, quasi-static, uniform-stress model. It ignores
    the modal response of the specimen (see :func:`modal_frequencies`),
    electrode fringing, leakage through the crystal's finite resistivity,
    depolarization, and every nonlinearity. It is a floor-of-the-model
    estimate, not a prediction of a bench reading.
    """
    for name, v in (("stress_pa", stress_pa), ("area_m2", area_m2),
                    ("d_coeff", d_coeff)):
        if not math.isfinite(v):
            raise PulseModelError(f"{name} must be finite")
    if area_m2 <= 0.0:
        raise PulseModelError("area_m2 must be positive")
    return d_coeff * stress_pa * area_m2


def piezo_capacitance(area_m2: float, thickness_m: float,
                      eps_rel: float = EPS11_REL_QUARTZ) -> float:
    """Parallel-plate capacitance of the electroded crystal, in farads.

    ``C = eps0 * eps_rel * A / t``. ``eps_rel`` defaults to
    :data:`EPS11_REL_QUARTZ` = 4.52, the LITERATURE relative permittivity
    of alpha-quartz perpendicular to the optic axis, chosen because the
    d11 charge is collected on the X faces. Quartz is anisotropic
    (eps33/eps0 ~ 4.63), so the axis is part of the constant.

    The parallel-plate form ignores fringing and is only accurate while
    the electrode dimension is large compared with ``thickness_m``.
    """
    if area_m2 <= 0.0 or thickness_m <= 0.0:
        raise PulseModelError("area_m2 and thickness_m must be positive")
    if eps_rel <= 0.0:
        raise PulseModelError("eps_rel must be positive")
    return EPS0_F_PER_M * eps_rel * area_m2 / thickness_m


def piezo_voltage(stress_pa: float, area_m2: float, thickness_m: float,
                  d_coeff: float = D11_QUARTZ_C_PER_N,
                  eps_rel: float = EPS11_REL_QUARTZ) -> float:
    """Open-circuit voltage across the electroded crystal, in volts.

    The crystal is modeled as its own capacitor: the piezoelectric charge
    :func:`piezo_charge` develops across :func:`piezo_capacitance`, so::

        V = Q / C = (d * T * A) / (eps0 * eps_rel * A / t)
                  = d * T * t / (eps0 * eps_rel)

    Note that the electrode area cancels: open-circuit piezoelectric
    voltage depends on stress and thickness, not on area. Area still sets
    the charge, and therefore the current available into a finite load.

    Permittivity used: eps11 = 4.52 * eps0 (LITERATURE value for
    alpha-quartz perpendicular to the optic axis; see
    :data:`EPS11_REL_QUARTZ`).

    Strictly open-circuit and quasi-static. Any real instrument loads the
    crystal with cable and amplifier input capacitance, which are
    typically comparable to or larger than the crystal's own capacitance
    and will reduce this voltage substantially. This function does not
    model the measurement chain, and a number it returns must not be
    compared with a bench reading without one.
    """
    q = piezo_charge(stress_pa, area_m2, d_coeff)
    c = piezo_capacitance(area_m2, thickness_m, eps_rel)
    return q / c


# --- acoustic modes ------------------------------------------------------

def modal_frequencies(
        length_m: float,
        sound_speed_ms: float = QUARTZ_LONGITUDINAL_VELOCITY_X_MS,
        n_modes: int = 8) -> tuple[float, ...]:
    """Free-free longitudinal mode frequencies of a bar, in Hz.

    For a uniform bar with both ends free (stress-free boundaries), the
    longitudinal standing-wave condition is a half-wavelength fit::

        f_n = n * v / (2 L),    n = 1, 2, 3, ...

    ``sound_speed_ms`` defaults to 5720 m/s, the LITERATURE longitudinal
    (extensional) acoustic velocity of alpha-quartz along the X axis.
    Quartz is strongly anisotropic — the value along Z is different
    (~6320 m/s) — so the axis is part of the constant and a specimen cut
    on another axis needs its own velocity. NOT MEASURED BY THIS
    PROGRAMME.

    This is a one-dimensional slender-bar model. It ignores the Poisson
    correction, transverse and torsional families, the thickness-shear
    modes that a real quartz resonator is usually operated on, mounting
    and winding mass loading (claim R6-C-004), and the finite Q that sets
    how wide each of these lines actually is. Treating a computed f_n as
    the specimen's resonance without a modal measurement would be exactly
    the error the audit below is built to catch.
    """
    if length_m <= 0.0 or not math.isfinite(length_m):
        raise PulseModelError("length_m must be finite and positive")
    if sound_speed_ms <= 0.0 or not math.isfinite(sound_speed_ms):
        raise PulseModelError("sound_speed_ms must be finite and positive")
    if n_modes < 1:
        raise PulseModelError("n_modes must be at least 1")
    return tuple(n * sound_speed_ms / (2.0 * length_m)
                 for n in range(1, n_modes + 1))


def _nearest_mode_detuning(f_hz: float,
                           modes: Sequence[float]) -> tuple[float, float]:
    """(nearest mode, fractional detuning |f - f_n| / f_n)."""
    best = min(modes, key=lambda m: abs(f_hz - m))
    return best, abs(f_hz - best) / best


def _triple_statistic(freqs: Sequence[float],
                      modes: Sequence[float]) -> float:
    """Test statistic: mean fractional detuning to the nearest mode.

    Smaller is a better fit. Chosen before the null was run, and used
    unchanged for both the observed triple and every null draw.
    """
    return sum(_nearest_mode_detuning(f, modes)[1] for f in freqs) / len(freqs)


def source_frequency_audit(
        length_m: float,
        sound_speed_ms: float = QUARTZ_LONGITUDINAL_VELOCITY_X_MS,
        n_modes: int = 40,
        frequencies_hz: Sequence[int] = SOURCE_FREQUENCIES_HZ,
        band_hz: tuple[int, int] = NULL_BAND_HZ,
        n_draws: int = NULL_DRAWS,
        seed: int = NULL_SEED,
        alpha: float = ALPHA) -> dict:
    """Do the three source frequencies land near this specimen's modes?

    Asks, for a specimen of ``length_m``, whether 1496 / 644 / 587 Hz sit
    closer to computed free-free longitudinal modes than an arbitrary
    triple of integer frequencies would.

    The granularity-matched null (the v4.6 lesson)
    ----------------------------------------------
    The source quotes its frequencies as **integers in Hz**. The null
    therefore draws triples of *distinct integers in Hz* from the same
    declared band :data:`NULL_BAND_HZ`, computes the same statistic, and
    reports how often a random triple does at least as well as the
    source triple. A null drawn from a continuum over the same band would
    be a different and much weaker test: with a continuum the source
    triple's integer-ness itself becomes a spurious source of apparent
    structure. v4.6 produced its null results precisely by matching the
    null to the candidate set's granularity, and this audit does the
    same.

    Determinism: the RNG is ``random.Random(seed)`` with ``seed`` fixed at
    :data:`NULL_SEED` = 20260718 and recorded in the returned record. The
    band is declared in advance and is also returned, because narrowing
    the band would lower the p-value without adding any evidence.

    p-value: the add-one estimator
    ``p = (1 + #{null <= observed}) / (1 + n_draws)``, one-sided (small
    statistic = good fit). Its floor is ``1/(1 + n_draws)``.

    The returned record carries ``significant`` and ``verdict``. The
    verdict is derived mechanically from ``p >= alpha``; this function
    has no branch that can report a positive finding at ``p >= alpha``.

    Returns
    -------
    dict with the modal spectrum, per-frequency detuning, the observed
    statistic, the null p-value, and an explicit
    ``all_below_fundamental`` flag — for any specimen short enough to be
    a laboratory object the fundamental is tens of kHz and all three
    source frequencies fall below it, in which case "nearest mode" means
    "the fundamental, far away" and the audit is reporting the absence of
    an assignment rather than a poor one.
    """
    lo, hi = band_hz
    if lo < 1 or hi <= lo:
        raise PulseModelError("band_hz must be an increasing positive band")
    k = len(frequencies_hz)
    if hi - lo + 1 < k:
        raise PulseModelError("band too narrow to draw a distinct triple")
    if n_draws < 1:
        raise PulseModelError("n_draws must be at least 1")

    modes = modal_frequencies(length_m, sound_speed_ms, n_modes)
    per_frequency = []
    for f in frequencies_hz:
        mode, det = _nearest_mode_detuning(float(f), modes)
        per_frequency.append({
            "frequency_hz": f,
            "nearest_mode_hz": mode,
            "mode_index": modes.index(mode) + 1,
            "fractional_detuning": det,
            "below_fundamental": float(f) < modes[0],
        })
    observed = _triple_statistic([float(f) for f in frequencies_hz], modes)

    rng = random.Random(seed)
    population = range(lo, hi + 1)
    at_least_as_good = 0
    for _ in range(n_draws):
        draw = rng.sample(population, k)
        if _triple_statistic([float(x) for x in draw], modes) <= observed:
            at_least_as_good += 1
    p_value = (1 + at_least_as_good) / (1 + n_draws)

    significant = p_value < alpha
    if significant:
        verdict = (
            f"The source triple fits the computed modal spectrum better "
            f"than {1 - p_value:.4f} of granularity-matched random "
            f"triples (p={p_value:.5f} < alpha={alpha}). This is a "
            f"statement about a MODEL spectrum, not a measurement: no "
            f"modal analysis of any specimen has been performed, so this "
            f"cannot be promoted past OPERATIONAL_HYPOTHESIS.")
    else:
        verdict = (
            f"NOT SIGNIFICANT: p={p_value:.5f} >= alpha={alpha}. Random "
            f"integer-Hz triples drawn from {lo}-{hi} Hz fit this "
            f"specimen's computed modal spectrum at least as well as the "
            f"source triple {at_least_as_good} times in {n_draws}. The "
            f"three source frequencies carry no demonstrated relationship "
            f"to the modeled modes.")

    return {
        "claim_id": "R6-C-006",
        "evidence_class": "OPERATIONAL_HYPOTHESIS",
        "length_m": length_m,
        "sound_speed_ms": sound_speed_ms,
        "n_modes": n_modes,
        "fundamental_hz": modes[0],
        "highest_mode_hz": modes[-1],
        "frequencies_hz": tuple(frequencies_hz),
        "per_frequency": per_frequency,
        "all_below_fundamental": all(pf["below_fundamental"]
                                     for pf in per_frequency),
        "statistic": observed,
        "statistic_definition":
            "mean fractional detuning to the nearest computed mode; "
            "smaller is a better fit",
        "null_band_hz": (lo, hi),
        "null_granularity": "distinct integers in Hz (matches the source "
                            "corpus's own quoted granularity)",
        "null_draws": n_draws,
        "null_seed": seed,
        "null_at_least_as_good": at_least_as_good,
        "p_value": p_value,
        "alpha": alpha,
        "significant": significant,
        "verdict": verdict,
        "ceiling": (
            "Three frequencies to test against a MODELED spectrum. "
            "Nothing here is a measurement of any specimen, and a "
            "significant p against a model spectrum would still require "
            "a bench modal analysis before it meant anything."),
        "not_bench_data": True,
    }


__all__ = [
    "D11_QUARTZ_C_PER_N",
    "D14_QUARTZ_C_PER_N",
    "EPS0_F_PER_M",
    "EPS11_REL_QUARTZ",
    "QUARTZ_LONGITUDINAL_VELOCITY_X_MS",
    "SOURCE_FREQUENCIES_HZ",
    "NULL_BAND_HZ",
    "NULL_SEED",
    "NULL_DRAWS",
    "ALPHA",
    "PulseModelError",
    "PulseShape",
    "SinusoidDrive",
    "spectrum",
    "dc_magnitude",
    "total_energy",
    "bandwidth_3db",
    "spectral_energy_fraction",
    "matched_energy_sinusoid",
    "piezo_charge",
    "piezo_capacitance",
    "piezo_voltage",
    "modal_frequencies",
    "source_frequency_audit",
]
