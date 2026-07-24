"""P22 — the QCM / BVD / ring-down measurement stack, as models not a device.

A quartz-crystal-microbalance measurement leans on three pieces of
textbook physics that must agree with one another:

* the **Sauerbrey relation**, ``Delta f = -C_f * Delta m`` -- adding mass
  to the electrode lowers the resonant frequency, linearly, with a
  sensitivity ``C_f`` fixed by the crystal's fundamental and material
  constants;
* the **Butterworth-Van Dyke (BVD)** equivalent circuit -- a motional
  branch ``R, L, C`` in series, shunted by a static capacitance ``C0`` --
  whose complex impedance sweep carries the series resonance ``f_s``, the
  parallel resonance ``f_p``, and the quality factor ``Q``;
* the **ring-down**, ``A * exp(-t/tau) * cos(w t)`` -- the free decay of
  the resonance after the drive is cut, from which ``Q = w * tau / 2``.

This module implements all three as models and exercises them on
**synthetic** data. :func:`fit_bvd` recovers planted ``R, L, C, C0`` from
a synthetic impedance sweep; :func:`ringdown_Q` recovers a planted ``Q``
and ``tau`` from a synthetic decay; :func:`sauerbrey_delta_f` gives the
mass-loading shift; and :func:`stack_agreement` confirms that the three
routes give the **same** ``f`` and ``Q`` for the **same** synthetic
resonator. That agreement is *model self-consistency* -- three correct
pieces of arithmetic describing one set of numbers this module generated
-- and it is **not** measurement agreement, because no crystal, network
analyser, or oscilloscope exists here.

The two load-bearing refusals draw the line. A fit to synthetic data is
not a measured crystal (:func:`refuse_synthetic_fit_as_measured_crystal`),
and a model ``Q`` is not a device ``Q``
(:func:`refuse_model_Q_as_device_Q`). Any real device number is
``BLOCKED_MISSING_INPUT``: it needs a physical crystal on an instrument
that is not in this repository.

Nothing here is measured. Every ``R``, ``L``, ``C``, ``C0``, ``f``, ``Q``
and ``tau`` is planted by this module and recovered from data this module
synthesised.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

# --- verdict and claim vocabulary ----------------------------------------

#: The standing verdict for this module.
VERDICT = "QCM_BVD_RINGDOWN_STACK_MODEL"

#: The typed claim vocabulary, exact strings, shared across the release.
CLAIM_CLASSES: tuple[str, ...] = (
    "EXACT_IDENTITY",
    "SOURCE_ESTABLISHED_PHYSICS",
    "CONVENTIONAL_LITERATURE",
    "ANALYTIC_MODEL",
    "NUMERICAL_SIMULATION",
    "REPOSITORY_COMPUTATIONAL_RESULT",
    "ENGINEERING_CANDIDATE",
    "BENCH_MEASUREMENT",
    "UNSUPPORTED",
    "BLOCKED_MISSING_INPUT",
)

ANALYTIC_MODEL = "ANALYTIC_MODEL"
REPOSITORY_COMPUTATIONAL_RESULT = "REPOSITORY_COMPUTATIONAL_RESULT"
BLOCKED_MISSING_INPUT = "BLOCKED_MISSING_INPUT"

EVIDENCE_CLASS = "ANALYTIC_MODEL"
MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: AT-cut quartz material constants, conventional literature values.
QUARTZ_DENSITY_KG_M3 = 2648.0             # rho_q
QUARTZ_SHEAR_MODULUS_PA = 2.947e10        # mu_q
#: A nominal active electrode area for the Sauerbrey sensitivity, m^2.
DEFAULT_AREA_M2 = 1.0e-4                   # 1 cm^2


class QCMStackError(RuntimeError):
    """Raised when a model is asked to be a measurement, or is misused.

    Covers the structural guards (a non-positive mass sensitivity, a
    degenerate sweep, a ring-down too short to fit) and the two
    load-bearing refusals :func:`refuse_synthetic_fit_as_measured_crystal`
    and :func:`refuse_model_Q_as_device_Q`.
    """


# --- small guards ---------------------------------------------------------

def _positive(value: object, what: str) -> float:
    try:
        x = float(value)                              # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise QCMStackError(f"cannot read {value!r} as {what}") from None
    if not math.isfinite(x):
        raise QCMStackError(f"{what} must be finite, got {value!r}")
    if x <= 0.0:
        raise QCMStackError(f"{what} must be positive, got {x!r}")
    return x


# --- (1) the Sauerbrey relation ------------------------------------------

def sauerbrey_delta_f(delta_m: float, Cf: float) -> float:
    """The Sauerbrey mass-loading shift ``Delta f = -C_f * Delta m``.

    Mass added to the electrode lowers the resonant frequency, so the
    shift is negative for a positive mass load and the relation is exactly
    linear in ``Delta m``. ``Cf`` is a positive mass sensitivity (Hz per
    kg); ``delta_m`` is a signed mass change (kg).
    """
    cf = _positive(Cf, "the Sauerbrey mass sensitivity Cf")
    return -cf * float(delta_m)


def sauerbrey_constant(f0: float, area_m2: float = DEFAULT_AREA_M2,
                       harmonic: int = 1,
                       density: float = QUARTZ_DENSITY_KG_M3,
                       shear_modulus: float = QUARTZ_SHEAR_MODULUS_PA
                       ) -> float:
    """The Sauerbrey sensitivity ``C_f = 2 n f0^2 / (A sqrt(rho * mu))``.

    Fixed by the fundamental ``f0``, the active area ``A``, the harmonic
    number ``n``, and the quartz density and shear modulus. This is the
    coupling that ties the Sauerbrey route to the same ``f0`` the BVD and
    ring-down routes see.
    """
    f = _positive(f0, "the fundamental f0")
    a = _positive(area_m2, "the active area")
    n = int(harmonic)
    if n < 1:
        raise QCMStackError("the harmonic number must be a positive integer")
    root = math.sqrt(_positive(density, "the density")
                     * _positive(shear_modulus, "the shear modulus"))
    return 2.0 * n * f * f / (a * root)


def sauerbrey_f0_from_Cf(Cf: float, area_m2: float = DEFAULT_AREA_M2,
                         harmonic: int = 1,
                         density: float = QUARTZ_DENSITY_KG_M3,
                         shear_modulus: float = QUARTZ_SHEAR_MODULUS_PA
                         ) -> float:
    """Invert :func:`sauerbrey_constant` back to the fundamental ``f0``.

    ``f0 = sqrt(C_f * A * sqrt(rho * mu) / (2 n))``. The exact inverse, so
    the Sauerbrey route can be checked to carry the same ``f0`` as the
    other two routes.
    """
    cf = _positive(Cf, "the Sauerbrey sensitivity Cf")
    a = _positive(area_m2, "the active area")
    n = int(harmonic)
    if n < 1:
        raise QCMStackError("the harmonic number must be a positive integer")
    root = math.sqrt(_positive(density, "the density")
                     * _positive(shear_modulus, "the shear modulus"))
    return math.sqrt(cf * a * root / (2.0 * n))


# --- (2) the Butterworth-Van Dyke model ----------------------------------

@dataclass(frozen=True)
class BVDResonator:
    """A Butterworth-Van Dyke resonator: motional R,L,C shunted by C0.

    A synthetic resonator, not a crystal. The values are planted so a fit
    can recover them; they are not the parameters of any physical device.
    """

    R: float          # motional resistance, ohm
    L: float          # motional inductance, henry
    C: float          # motional capacitance, farad
    C0: float         # static (parallel) capacitance, farad

    def __post_init__(self) -> None:
        for name in ("R", "L", "C", "C0"):
            _positive(getattr(self, name), f"the BVD parameter {name}")

    @property
    def omega_s(self) -> float:
        """Series (motional) resonance angular frequency ``1/sqrt(LC)``."""
        return 1.0 / math.sqrt(self.L * self.C)

    @property
    def f_s(self) -> float:
        """Series resonance frequency, Hz."""
        return self.omega_s / (2.0 * math.pi)

    @property
    def f_p(self) -> float:
        """Parallel resonance ``f_s * sqrt(1 + C/C0)``, Hz."""
        return self.f_s * math.sqrt(1.0 + self.C / self.C0)

    @property
    def Q(self) -> float:
        """Quality factor ``omega_s * L / R``."""
        return self.omega_s * self.L / self.R

    def impedance(self, freqs: np.ndarray) -> np.ndarray:
        """Complex impedance of the BVD network over ``freqs`` (Hz)."""
        w = 2.0 * math.pi * np.asarray(freqs, dtype=float)
        z_motional = self.R + 1j * (w * self.L - 1.0 / (w * self.C))
        y = 1.0 / z_motional + 1j * w * self.C0
        return 1.0 / y


#: The default synthetic resonator: f_s = 1 MHz, Q = 1000.
DEFAULT_RESONATOR = BVDResonator(R=10.0, L=1.5915e-3, C=1.5915e-11,
                                 C0=1.0e-10)


def synthetic_bvd_sweep(resonator: BVDResonator = DEFAULT_RESONATOR,
                        f_lo: float | None = None,
                        f_hi: float | None = None,
                        n: int = 16001) -> dict:
    """Synthesize a complex impedance sweep for a BVD resonator.

    The sweep spans the series and parallel resonances with enough points
    to resolve the narrow conductance peak. Every number is generated here
    from ``resonator``; nothing is measured.
    """
    if not isinstance(resonator, BVDResonator):
        raise QCMStackError("synthetic_bvd_sweep needs a BVDResonator")
    fs = resonator.f_s
    lo = 0.9 * fs if f_lo is None else _positive(f_lo, "f_lo")
    hi = 1.15 * fs if f_hi is None else _positive(f_hi, "f_hi")
    if hi <= lo:
        raise QCMStackError("f_hi must exceed f_lo")
    if int(n) < 64:
        raise QCMStackError("a sweep needs at least 64 points")
    freqs = np.linspace(lo, hi, int(n))
    z = resonator.impedance(freqs)
    return {
        "freqs_hz": freqs,
        "Z": z,
        "true_R": resonator.R,
        "true_L": resonator.L,
        "true_C": resonator.C,
        "true_C0": resonator.C0,
        "true_f_s": fs,
        "true_f_p": resonator.f_p,
        "true_Q": resonator.Q,
        "measured_here": MEASURED_HERE,
    }


def _parabolic_peak(x: np.ndarray, y: np.ndarray, i: int
                    ) -> tuple[float, float]:
    """Sub-sample peak of ``y`` near index ``i`` via a 3-point parabola."""
    if 0 < i < len(x) - 1:
        y0, y1, y2 = float(y[i - 1]), float(y[i]), float(y[i + 1])
        denom = y0 - 2.0 * y1 + y2
        if denom != 0.0:
            delta = 0.5 * (y0 - y2) / denom
            dx = (float(x[i + 1]) - float(x[i - 1])) / 2.0
            x_peak = float(x[i]) + delta * dx
            y_peak = y1 - 0.25 * (y0 - y2) * delta
            return x_peak, y_peak
    return float(x[i]), float(y[i])


def _half_power_crossing(freqs: np.ndarray, g: np.ndarray, i_peak: int,
                         half: float, forward: bool) -> float:
    """Linear-interpolated frequency where ``g`` falls to ``half``."""
    step = 1 if forward else -1
    i = i_peak
    n = len(freqs)
    while 0 <= i + step < n:
        j = i + step
        if g[j] <= half:
            f1, f2 = float(freqs[i]), float(freqs[j])
            g1, g2 = float(g[i]), float(g[j])
            if g1 == g2:
                return f2
            frac = (g1 - half) / (g1 - g2)
            return f1 + frac * (f2 - f1)
        i = j
    raise QCMStackError(
        "the sweep does not fall to half power on one side of the peak; "
        "widen the frequency span so the resonance is fully captured")


def fit_bvd(freqs: object, Z: object) -> dict:
    """Recover ``f_s``, ``f_p``, ``Q`` and ``R, L, C, C0`` from a sweep.

    The conductance ``G = Re(1/Z)`` is the motional conductance (the
    static ``C0`` is purely susceptive and drops out of the real part),
    so its peak locates ``f_s`` and gives ``R = 1/G_max``; its half-power
    width gives ``Q = f_s / FWHM``; and ``L, C`` follow from ``Q, R,
    f_s``. ``C0`` is recovered from the off-resonance susceptance, and
    ``f_p`` from the impedance-magnitude maximum. This is a fit to
    SYNTHETIC data, not a measured crystal.
    """
    f = np.asarray(freqs, dtype=float)
    z = np.asarray(Z, dtype=complex)
    if f.shape != z.shape or f.ndim != 1 or f.size < 64:
        raise QCMStackError("freqs and Z must be matching 1-D arrays of at "
                            "least 64 points")
    y = 1.0 / z
    g = np.real(y)
    b = np.imag(y)

    i_peak = int(np.argmax(g))
    f_s, g_max = _parabolic_peak(f, g, i_peak)
    if g_max <= 0.0:
        raise QCMStackError("the conductance peak is non-positive; this is "
                            "not a resonance")
    R = 1.0 / g_max

    half = g_max / 2.0
    f_lo = _half_power_crossing(f, g, i_peak, half, forward=False)
    f_hi = _half_power_crossing(f, g, i_peak, half, forward=True)
    fwhm = f_hi - f_lo
    if fwhm <= 0.0:
        raise QCMStackError("a non-positive linewidth cannot give a Q")
    Q = f_s / fwhm

    omega_s = 2.0 * math.pi * f_s
    L = Q * R / omega_s
    C = 1.0 / (omega_s * omega_s * L)

    # C0 from the off-resonance susceptance: B = Im(Y_motional) + omega*C0.
    w = 2.0 * math.pi * f
    z_motional = R + 1j * (w * L - 1.0 / (w * C))
    b_motional = np.imag(1.0 / z_motional)
    far = np.abs(f - f_s) > 10.0 * fwhm
    if int(np.count_nonzero(far)) < 4:
        raise QCMStackError("too few off-resonance points to recover C0; "
                            "widen the sweep")
    c0_samples = (b[far] - b_motional[far]) / w[far]
    C0 = float(np.median(c0_samples))
    if C0 <= 0.0:
        raise QCMStackError("recovered a non-physical (non-positive) C0")

    i_zmax = int(np.argmax(np.abs(z)))
    f_p, _ = _parabolic_peak(f, np.abs(z), i_zmax)

    return {
        "f_s_hz": f_s,
        "f_p_hz": f_p,
        "Q": Q,
        "fwhm_hz": fwhm,
        "R": R,
        "L": L,
        "C": C,
        "C0": C0,
        "claim_class": REPOSITORY_COMPUTATIONAL_RESULT,
        "measured_here": MEASURED_HERE,
        "note": ("a fit to a SYNTHETIC impedance sweep generated in this "
                 "module; not a measurement of any crystal"),
    }


# --- (3) the ring-down ----------------------------------------------------

def synthetic_ringdown(f0: float, Q: float, sample_rate_hz: float = 1.0e7,
                       n_tau: float = 8.0, amplitude: float = 1.0,
                       phase: float = 0.0, noise: float = 0.0,
                       seed: int = 0) -> dict:
    """A synthetic ring-down ``A exp(-t/tau) cos(w t + phi)`` for ``f0, Q``.

    The decay time follows from the quality factor, ``tau = Q/(pi f0)``,
    which is the same ``Q = w tau / 2`` written for ``tau``. Every sample
    is generated here; nothing is recorded from a device.
    """
    f = _positive(f0, "the frequency f0")
    q = _positive(Q, "the quality factor Q")
    fs = _positive(sample_rate_hz, "the sample rate")
    if fs <= 2.0 * f:
        raise QCMStackError(
            f"the sample rate {fs:g} Hz does not satisfy Nyquist for a "
            f"{f:g} Hz ring-down (needs > {2.0 * f:g} Hz)")
    tau = q / (math.pi * f)
    span = _positive(n_tau, "n_tau") * tau
    n = int(round(span * fs))
    if n < 16:
        raise QCMStackError("a ring-down needs at least sixteen samples")
    t = np.arange(n, dtype=float) / fs
    w = 2.0 * math.pi * f
    envelope = float(amplitude) * np.exp(-t / tau)
    signal = envelope * np.cos(w * t + float(phase))
    if noise:
        rng = np.random.default_rng(int(seed))
        signal = signal + float(noise) * rng.standard_normal(n)
    return {
        "t_s": t,
        "signal": signal,
        "true_f0_hz": f,
        "true_Q": q,
        "true_tau_s": tau,
        "true_omega": w,
        "sample_rate_hz": fs,
        "measured_here": MEASURED_HERE,
    }


def _analytic_envelope(signal: np.ndarray) -> np.ndarray:
    """Amplitude envelope via the FFT Hilbert transform (numpy only)."""
    x = np.asarray(signal, dtype=float)
    n = x.size
    spectrum = np.fft.fft(x)
    weights = np.zeros(n)
    if n % 2 == 0:
        weights[0] = weights[n // 2] = 1.0
        weights[1:n // 2] = 2.0
    else:
        weights[0] = 1.0
        weights[1:(n + 1) // 2] = 2.0
    return np.abs(np.fft.ifft(spectrum * weights))


def _estimate_tau(t: np.ndarray, signal: np.ndarray,
                  envelope_floor: float = 0.05) -> float:
    """Recover ``tau`` from a decay by a log-linear fit of its envelope."""
    x = np.asarray(signal, dtype=float)
    full = _analytic_envelope(x)
    margin = min(max(1, int(round(0.02 * t.size))), (t.size - 8) // 2)
    interior = slice(margin, t.size - margin)
    ti = t[interior]
    env = full[interior]
    peak = float(np.max(env))
    if peak <= 0.0:
        raise QCMStackError("a flat-zero signal has no ring-down to fit")
    keep = env >= envelope_floor * peak
    if int(np.count_nonzero(keep)) < 8:
        raise QCMStackError("too little of the envelope is above the floor "
                            "to fit a decay")
    slope, _ = np.polyfit(ti[keep], np.log(env[keep]), 1)
    if slope >= 0.0:
        raise QCMStackError("the envelope does not decay; this is not a "
                            "ring-down")
    return float(-1.0 / slope)


def _estimate_omega(t: np.ndarray, signal: np.ndarray) -> float:
    """Recover the angular frequency from the dominant spectral peak."""
    x = np.asarray(signal, dtype=float)
    x = x - float(np.mean(x))
    n = x.size
    dt = float(np.mean(np.diff(t)))
    if dt <= 0.0:
        raise QCMStackError("the time base must be increasing")
    window = np.hanning(n)
    mag = np.abs(np.fft.rfft(x * window))
    freqs = np.fft.rfftfreq(n, dt)
    i = int(np.argmax(mag))
    if i == 0:
        raise QCMStackError("the ring-down has no resolvable carrier")
    f_peak, _ = _parabolic_peak(freqs, mag, i)
    return 2.0 * math.pi * f_peak


def ringdown_Q(signal: object, t: object) -> dict:
    """Recover ``Q`` and ``tau`` from a ring-down, ``Q = w tau / 2``.

    ``tau`` comes from a log-linear fit of the amplitude envelope and
    ``w`` from the dominant spectral peak, so ``Q = w tau / 2`` is
    recovered from the data rather than assumed. It also reports the
    equivalent Lorentzian linewidth ``FWHM = 1/(pi tau)`` so the ring-down
    ``Q`` can be checked against the BVD ``Q = f_s / FWHM``. A fit to
    synthetic data, not a device measurement.
    """
    tt = np.asarray(t, dtype=float)
    sig = np.asarray(signal, dtype=float)
    if tt.shape != sig.shape or tt.ndim != 1 or tt.size < 16:
        raise QCMStackError("signal and t must be matching 1-D arrays of at "
                            "least sixteen points")
    tau = _estimate_tau(tt, sig)
    omega = _estimate_omega(tt, sig)
    q = omega * tau / 2.0
    f = omega / (2.0 * math.pi)
    fwhm = 1.0 / (math.pi * tau)
    return {
        "Q": q,
        "tau_s": tau,
        "omega": omega,
        "f_hz": f,
        "fwhm_hz": fwhm,
        "q_from_fwhm": f / fwhm,
        "claim_class": REPOSITORY_COMPUTATIONAL_RESULT,
        "measured_here": MEASURED_HERE,
        "note": ("a fit to a SYNTHETIC decay generated in this module; not "
                 "a measurement of any resonator"),
    }


# --- (4) the stack self-consistency check --------------------------------

def stack_agreement(resonator: BVDResonator = DEFAULT_RESONATOR,
                    area_m2: float = DEFAULT_AREA_M2,
                    rel_tol: float = 0.02) -> dict:
    """Confirm Sauerbrey, BVD and ring-down agree on one synthetic resonator.

    For a single planted :class:`BVDResonator`:

    * BVD recovers ``f_s`` and ``Q`` from a synthetic impedance sweep;
    * a synthetic ring-down built from that ``f_s`` and ``Q`` recovers a
      matching ``f`` and ``Q``, and its linewidth ``FWHM`` reproduces the
      BVD ``Q = f_s/FWHM``;
    * the Sauerbrey sensitivity built from ``f_s`` inverts back to the
      same ``f0``.

    All three carry the same ``f`` and ``Q``. This is MODEL
    self-consistency -- three correct computations on one set of
    synthetic numbers -- and it is not measurement agreement, because no
    crystal was measured.
    """
    sweep = synthetic_bvd_sweep(resonator)
    bvd = fit_bvd(sweep["freqs_hz"], sweep["Z"])

    rd_data = synthetic_ringdown(bvd["f_s_hz"], bvd["Q"])
    rd = ringdown_Q(rd_data["signal"], rd_data["t_s"])

    cf = sauerbrey_constant(bvd["f_s_hz"], area_m2=area_m2)
    f0_back = sauerbrey_f0_from_Cf(cf, area_m2=area_m2)

    f_values = [bvd["f_s_hz"], rd["f_hz"], f0_back]
    q_values = [bvd["Q"], rd["Q"]]

    def _spread(vals: list[float]) -> float:
        m = sum(vals) / len(vals)
        return max(abs(v - m) for v in vals) / m

    f_spread = _spread(f_values)
    q_spread = _spread(q_values)
    # ring-down linewidth reproduces the BVD Q = f_s/FWHM
    q_from_ringdown_linewidth = bvd["f_s_hz"] / rd["fwhm_hz"]
    linewidth_rel = abs(q_from_ringdown_linewidth - bvd["Q"]) / bvd["Q"]

    return {
        "f_s_bvd_hz": bvd["f_s_hz"],
        "f_ringdown_hz": rd["f_hz"],
        "f0_from_sauerbrey_hz": f0_back,
        "Q_bvd": bvd["Q"],
        "Q_ringdown": rd["Q"],
        "sauerbrey_Cf_hz_per_kg": cf,
        "f_relative_spread": f_spread,
        "q_relative_spread": q_spread,
        "q_from_ringdown_linewidth": q_from_ringdown_linewidth,
        "linewidth_relative_error": linewidth_rel,
        "f_consistent": f_spread <= rel_tol,
        "q_consistent": q_spread <= rel_tol,
        "linewidth_consistent": linewidth_rel <= rel_tol,
        "all_consistent": (f_spread <= rel_tol and q_spread <= rel_tol
                           and linewidth_rel <= rel_tol),
        "rel_tol": rel_tol,
        "claim_class": REPOSITORY_COMPUTATIONAL_RESULT,
        "measured_here": MEASURED_HERE,
        "note": ("MODEL self-consistency across three routes on one "
                 "synthetic resonator; NOT measurement agreement"),
    }


# --- (5) the load-bearing refusals ---------------------------------------

def refuse_synthetic_fit_as_measured_crystal(
        claim: str = "the BVD fit measured a crystal",
        quantity: str | None = None) -> None:
    """Refuse a synthetic fit read as a crystal measurement. Always raises.

    :func:`fit_bvd` recovers the parameters this module *planted* in a
    synthetic sweep. There is no crystal, no network analyser and no
    impedance bridge here, so the recovered ``R, L, C, C0, f_s, f_p, Q``
    describe a model, not a device. A measured crystal number is
    ``BLOCKED_MISSING_INPUT``.
    """
    named = f" of {quantity}" if quantity else ""
    raise QCMStackError(
        f"refused: {claim!r}{named}. The BVD fit recovers parameters "
        f"PLANTED by this module in a SYNTHETIC impedance sweep; no "
        f"crystal, network analyser, or impedance bridge exists here, so "
        f"nothing was measured. A measured crystal's R, L, C, C0, f_s, "
        f"f_p or Q is {BLOCKED_MISSING_INPUT}, pending a physical device "
        f"on a calibrated instrument. {PHYSICAL_VALIDATION}. {VERDICT}")


def refuse_model_Q_as_device_Q(
        claim: str = "the model Q is the device Q",
        q_value: float | None = None) -> None:
    """Refuse a model ``Q`` read as a device ``Q``. Always raises.

    The ``Q`` from :func:`fit_bvd` or :func:`ringdown_Q` is computed from
    numbers this module synthesised. A real resonator's ``Q`` depends on
    mounting loss, electrode loss, gas damping and anchor loss that no
    model here contains, and it is ``BLOCKED_MISSING_INPUT``.
    """
    named = f" (Q={q_value})" if q_value is not None else ""
    raise QCMStackError(
        f"refused: {claim!r}{named}. The Q recovered here is a MODEL Q, "
        f"computed from a synthetic sweep or a synthetic decay this module "
        f"generated. A physical resonator's Q is set by mounting, "
        f"electrode, gas-damping and anchor losses that this model does "
        f"not contain; the device Q is {BLOCKED_MISSING_INPUT} until a "
        f"crystal is measured on an instrument that is not in this "
        f"repository. {PHYSICAL_VALIDATION}. {VERDICT}")


# --- (6) report -----------------------------------------------------------

def qcmstack_report() -> dict:
    """The standing statement of what the stack is and is not."""
    agreement = stack_agreement()
    cf = sauerbrey_constant(DEFAULT_RESONATOR.f_s)
    return {
        "what_this_is": (
            "the QCM measurement stack -- the Sauerbrey mass relation, the "
            "Butterworth-Van Dyke equivalent circuit, and the ring-down Q "
            "-- as models exercised on synthetic data, with a "
            "self-consistency check that the three routes agree on the "
            "same synthetic resonator"),
        "sauerbrey": {
            "relation": "Delta f = -C_f * Delta m",
            "constant": "C_f = 2 n f0^2 / (A sqrt(rho * mu))",
            "example_Cf_hz_per_kg": cf,
            "claim_class": ANALYTIC_MODEL,
        },
        "bvd": {
            "model": "motional R,L,C in series, shunted by static C0",
            "recovers": ["f_s", "f_p", "Q", "R", "L", "C", "C0"],
            "claim_class": REPOSITORY_COMPUTATIONAL_RESULT,
        },
        "ringdown": {
            "model": "A exp(-t/tau) cos(w t), Q = w tau / 2",
            "linewidth": "FWHM = 1/(pi tau), so Q = f_s/FWHM",
            "claim_class": REPOSITORY_COMPUTATIONAL_RESULT,
        },
        "stack_agreement": agreement,
        "refusals": [
            "refuse_synthetic_fit_as_measured_crystal",
            "refuse_model_Q_as_device_Q",
        ],
        "firewalls": [
            "fit_bvd recovers parameters PLANTED in a synthetic sweep; no "
            "crystal is measured",
            "the ring-down and BVD Q are model Q values, not device Q",
            "the three-route agreement is MODEL self-consistency, not "
            "measurement agreement",
            "any real device number is BLOCKED_MISSING_INPUT",
        ],
        "device_status": (
            f"{BLOCKED_MISSING_INPUT} - no crystal, network analyser, "
            f"impedance bridge or oscilloscope exists here"),
        "claim_class": REPOSITORY_COMPUTATIONAL_RESULT,
        "claim_classes": list(CLAIM_CLASSES),
        "evidence_class": EVIDENCE_CLASS,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "what_would_change_this": (
            "a physical crystal measured on a calibrated network analyser "
            "for the BVD parameters, a captured free decay on an "
            "oscilloscope for the ring-down Q, and a controlled mass "
            "deposition for the Sauerbrey sensitivity, each with its "
            "uncertainty and its null"),
        "what_this_does_not_say": (
            "It does not say any crystal was measured: fit_bvd recovers "
            "parameters this module planted in a SYNTHETIC impedance "
            "sweep, ringdown_Q recovers a Q and tau from a SYNTHETIC "
            "decay, and there is no crystal, network analyser, impedance "
            "bridge or oscilloscope in this repository. It does not say a "
            "model Q is a device Q: a physical resonator's Q is set by "
            "losses this model does not contain. The three-route "
            "agreement is MODEL self-consistency -- three correct "
            "computations on one set of synthetic numbers -- not "
            "measurement agreement. Any real device number is "
            "BLOCKED_MISSING_INPUT. PHYSICAL_VALIDATION_NOT_CLAIMED."),
        "verdict": VERDICT,
    }


__all__ = [
    "VERDICT", "CLAIM_CLASSES", "ANALYTIC_MODEL",
    "REPOSITORY_COMPUTATIONAL_RESULT", "BLOCKED_MISSING_INPUT",
    "EVIDENCE_CLASS", "MEASURED_HERE", "PHYSICAL_VALIDATION",
    "QUARTZ_DENSITY_KG_M3", "QUARTZ_SHEAR_MODULUS_PA", "DEFAULT_AREA_M2",
    "QCMStackError",
    "sauerbrey_delta_f", "sauerbrey_constant", "sauerbrey_f0_from_Cf",
    "BVDResonator", "DEFAULT_RESONATOR", "synthetic_bvd_sweep", "fit_bvd",
    "synthetic_ringdown", "ringdown_Q", "stack_agreement",
    "refuse_synthetic_fit_as_measured_crystal", "refuse_model_Q_as_device_Q",
    "qcmstack_report",
]
