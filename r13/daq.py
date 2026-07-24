"""P24 — a synchronized data-acquisition MODEL and an energy ledger.

Data acquisition is where a continuous physical signal becomes a finite
list of numbers, and every honest thing about it is a statement about how
much was thrown away in the process. This module builds that chain -- a
sampler, a multi-channel clock, a jitter model, and an energy ledger --
entirely in software, from synthetic signals. No instrument is operated
and nothing is acquired.

**Sampling and the fold.** :func:`sample` evaluates a signal function on a
uniform clock. Below the Nyquist frequency (``fs/2``) a tone comes back at
its own frequency; above it, the tone is indistinguishable from a lower
one and returns *aliased* to ``f_alias = |f - fs*round(f/fs)|``. That fold
is not a bug to be tolerated, it is the load-bearing correctness fact of
sampling: an under-sampled tone does not look noisy, it looks like a clean
tone at the wrong frequency, and only knowing ``fs`` tells them apart.
:func:`alias_frequency` gives the prediction and
:func:`dominant_frequency` reads back what the sampler actually produced.

**Synchronization.** Several channels share one clock but each carries its
own skew. :func:`cross_correlation_lag` recovers the relative delay
between two channels to within one sample, and :func:`synchronize` applies
the correction so a common event lines up across channels. A skew left
uncorrected is a phantom relative timing that later looks like physics.

**Timebase jitter.** A real clock does not tick on a perfect grid; its
edges wander. :func:`sample_with_jitter` models that wander as phase
noise, and :func:`jitter_snr` shows the consequence: jitter scatters a
tone's energy out of its bin and raises the noise floor, so more jitter
means a monotonically worse signal-to-noise ratio -- the Leeson-like
penalty a timebase pays.

**The energy ledger.** :func:`energy_ledger` ties an electrical drive
energy in to a signal energy out, through efficiency, dissipation and
storage terms, and reports whether the books ``close``. A **synthetic**
ledger built from declared dyadic values closes exactly, and dropping a
loss term leaves a residual exactly equal to that term -- which is how the
ledger is shown to have teeth. The **real** ledger is
``BLOCKED_MISSING_INPUT``: no instrument measured any of these energies
here. :func:`refuse_unclosed_as_new_energy` refuses to call a residual
whose interval spans zero a new energy channel.

**No promotion.** Synthetic sampled data is not acquired instrument data,
and :func:`refuse_synthetic_daq_as_acquired` refuses that promotion.
Nothing here is measured, and the verdict is
``SYNCHRONIZED_DAQ_ENERGY_LEDGER_MODEL``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

# --- verdict and claim vocabulary -----------------------------------------

#: The standing verdict for this module.
VERDICT = "SYNCHRONIZED_DAQ_ENERGY_LEDGER_MODEL"

NUMERICAL_SIMULATION = "NUMERICAL_SIMULATION"
ANALYTIC_MODEL = "ANALYTIC_MODEL"
REPOSITORY_COMPUTATIONAL_RESULT = "REPOSITORY_COMPUTATIONAL_RESULT"
BLOCKED_MISSING_INPUT = "BLOCKED_MISSING_INPUT"

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: Exact-closure tolerance for the ledger. The synthetic terms are dyadic,
#: so the books close in binary64 without a fudge factor.
LEDGER_TOL = 0.0


class DAQError(RuntimeError):
    """Raised when a DAQ or ledger statement exceeds the model.

    Covers the structural guards (a non-positive sample rate, mismatched
    channels, an unknown ledger term) and the two load-bearing refusals
    :func:`refuse_unclosed_as_new_energy` and
    :func:`refuse_synthetic_daq_as_acquired`.
    """


# --- (1) sampling and the Nyquist fold ------------------------------------

@dataclass(frozen=True)
class SampledSignal:
    """A signal evaluated on a uniform clock: the samples and their times."""

    t: np.ndarray
    values: np.ndarray
    fs: float
    duration: float

    @property
    def n(self) -> int:
        return int(self.values.size)

    @property
    def nyquist(self) -> float:
        return 0.5 * self.fs


def sample(signal_func, fs: float, duration: float) -> SampledSignal:
    """Evaluate ``signal_func`` on a uniform clock of rate ``fs``.

    Returns ``N = round(fs*duration)`` samples at times ``n/fs``. The
    sampler does not warn about aliasing: a tone above ``fs/2`` is
    evaluated exactly like one below it, and the fold is left visible in
    the returned samples for :func:`dominant_frequency` to read back.
    """
    rate = float(fs)
    dur = float(duration)
    if rate <= 0.0:
        raise DAQError("the sample rate must be positive")
    if dur <= 0.0:
        raise DAQError("the duration must be positive")
    n = int(round(rate * dur))
    if n < 2:
        raise DAQError("need at least two samples to represent a tone")
    t = np.arange(n, dtype=float) / rate
    values = np.asarray(signal_func(t), dtype=float)
    if values.shape != t.shape:
        raise DAQError("signal_func must return one value per sample time")
    return SampledSignal(t=t, values=values, fs=rate, duration=dur)


def alias_frequency(f: float, fs: float) -> float:
    """Where a tone at ``f`` lands after sampling at ``fs``.

    ``f_alias = |f - fs*round(f/fs)|``. Below Nyquist this is ``f`` itself;
    above it the tone folds into ``[0, fs/2]``.
    """
    rate = float(fs)
    if rate <= 0.0:
        raise DAQError("the sample rate must be positive")
    return abs(float(f) - rate * round(float(f) / rate))


def dominant_frequency(samples: np.ndarray, fs: float) -> float:
    """The frequency of the strongest tone in a real sampled record.

    Reads back what the sampler produced, so an aliased tone reports its
    aliased frequency, not its original one.
    """
    x = np.asarray(samples, dtype=float)
    if x.size < 2:
        raise DAQError("need at least two samples to find a tone")
    rate = float(fs)
    if rate <= 0.0:
        raise DAQError("the sample rate must be positive")
    spectrum = np.abs(np.fft.rfft(x - x.mean()))
    freqs = np.fft.rfftfreq(x.size, d=1.0 / rate)
    return float(freqs[int(np.argmax(spectrum))])


# --- (2) multi-channel synchronization ------------------------------------

def cross_correlation_lag(reference: np.ndarray, channel: np.ndarray) -> int:
    """Integer sample lag of ``channel`` relative to ``reference``.

    A positive lag ``s`` means ``channel`` is ``reference`` delayed by
    ``s`` samples (``channel[n] ~ reference[n - s]``). Recovered from the
    peak of the cross-correlation, so it is exact for an integer skew and
    within one sample otherwise.
    """
    a = np.asarray(reference, dtype=float)
    b = np.asarray(channel, dtype=float)
    if a.shape != b.shape:
        raise DAQError("channels must share a length to be cross-correlated")
    if a.size < 2:
        raise DAQError("need at least two samples to cross-correlate")
    a = a - a.mean()
    b = b - b.mean()
    corr = np.correlate(b, a, mode="full")
    return int(np.argmax(corr) - (a.size - 1))


@dataclass(frozen=True)
class SyncResult:
    """The outcome of aligning a set of channels on a shared clock."""

    aligned: np.ndarray          # (n_channels, n_samples), corrected
    applied_skews: tuple[int, ...]

    @property
    def n_channels(self) -> int:
        return int(self.aligned.shape[0])


def synchronize(channels, skews) -> SyncResult:
    """Correct a set of channels by rolling each back by its clock skew.

    ``channels`` is a sequence of equal-length records sampled on one
    clock; ``skews`` is the per-channel skew in samples (as recovered by
    :func:`cross_correlation_lag`). Each channel is rolled by ``-skew`` so
    that a common event lines up across all channels afterwards.
    """
    chans = [np.asarray(c, dtype=float) for c in channels]
    sk = [int(s) for s in skews]
    if not chans:
        raise DAQError("no channels to synchronize")
    if len(sk) != len(chans):
        raise DAQError("need exactly one skew per channel")
    length = chans[0].size
    if any(c.size != length for c in chans):
        raise DAQError("channels must share a length to be synchronized")
    aligned = np.vstack([np.roll(c, -s) for c, s in zip(chans, sk)])
    return SyncResult(aligned=aligned, applied_skews=tuple(sk))


def estimate_skews(channels, reference_index: int = 0) -> tuple[int, ...]:
    """Per-channel skews relative to one reference channel, by correlation."""
    chans = [np.asarray(c, dtype=float) for c in channels]
    if not chans:
        raise DAQError("no channels to estimate")
    if not 0 <= reference_index < len(chans):
        raise DAQError("reference_index is out of range")
    ref = chans[reference_index]
    return tuple(cross_correlation_lag(ref, c) for c in chans)


# --- (3) timebase jitter, as phase noise ----------------------------------

def sample_with_jitter(signal_func, fs: float, duration: float,
                       jitter_std: float, seed: int = 0) -> SampledSignal:
    """Sample on a clock whose edges wander with Gaussian jitter.

    Each nominal sample time ``n/fs`` is displaced by an independent
    Gaussian of standard deviation ``jitter_std`` seconds. The signal is
    still evaluated exactly, but at the wrong instants, which is how a
    timebase turns into phase noise on the recovered tone.
    """
    rate = float(fs)
    dur = float(duration)
    if rate <= 0.0:
        raise DAQError("the sample rate must be positive")
    if dur <= 0.0:
        raise DAQError("the duration must be positive")
    if float(jitter_std) < 0.0:
        raise DAQError("the jitter standard deviation cannot be negative")
    n = int(round(rate * dur))
    if n < 2:
        raise DAQError("need at least two samples to represent a tone")
    nominal = np.arange(n, dtype=float) / rate
    rng = np.random.default_rng(int(seed))
    jittered = nominal + rng.normal(0.0, float(jitter_std), size=n)
    values = np.asarray(signal_func(jittered), dtype=float)
    return SampledSignal(t=nominal, values=values, fs=rate, duration=dur)


def tone_snr(samples: np.ndarray, fs: float, f_tone: float) -> float:
    """Signal-to-noise ratio of a tone: its bin power over the noise floor.

    Power in the bin nearest ``f_tone`` divided by the mean power of the
    remaining bins. A perfectly clocked tone puts essentially all its
    energy in one bin and scores very high; jitter scatters energy into
    the other bins and lowers the ratio.
    """
    x = np.asarray(samples, dtype=float)
    if x.size < 4:
        raise DAQError("need at least four samples for an SNR estimate")
    rate = float(fs)
    if rate <= 0.0:
        raise DAQError("the sample rate must be positive")
    power = np.abs(np.fft.rfft(x - x.mean())) ** 2
    freqs = np.fft.rfftfreq(x.size, d=1.0 / rate)
    bin_index = int(np.argmin(np.abs(freqs - float(f_tone))))
    signal_power = float(power[bin_index])
    noise_mask = np.ones(power.size, dtype=bool)
    noise_mask[bin_index] = False
    noise_power = float(np.mean(power[noise_mask]))
    if noise_power <= 0.0:
        noise_power = np.finfo(float).tiny
    return signal_power / noise_power


def jitter_snr(f_tone: float, fs: float, duration: float,
               jitter_std: float, n_realizations: int = 32,
               seed: int = 0) -> float:
    """Mean tone SNR over several jitter realizations, at one jitter level.

    Averaging over realizations smooths the estimator so the dependence on
    ``jitter_std`` is the systematic one -- more jitter, less SNR -- rather
    than the luck of one noise draw.
    """
    if int(n_realizations) < 1:
        raise DAQError("need at least one realization")
    snrs = []
    for k in range(int(n_realizations)):
        sig = sample_with_jitter(
            lambda t: np.cos(2.0 * np.pi * float(f_tone) * t),
            fs, duration, jitter_std, seed=int(seed) + k)
        snrs.append(tone_snr(sig.values, fs, f_tone))
    return float(np.mean(snrs))


# --- (4) the energy ledger ------------------------------------------------

#: The output-side terms of the ledger, in reporting order.
LEDGER_TERMS: tuple[str, ...] = ("e_out", "e_dissipated", "e_stored")


def energy_ledger(e_in: float, *, e_out: float = 0.0,
                  e_dissipated: float = 0.0, e_stored: float = 0.0,
                  drop: str | None = None, tol: float = LEDGER_TOL) -> dict:
    """Tie drive energy in to signal energy out, and report closure.

    The identity is ``E_in = E_out + E_dissipated + E_stored``. The
    residual is ``E_in - sum(included terms)``, and ``closes`` is true when
    it is within ``tol`` (zero by default: the synthetic terms are dyadic
    and close exactly). ``drop`` names one output term to leave out -- the
    residual then equals exactly that term, which is how the ledger is
    shown to be sensitive to a missing loss channel.

    The values here are model energies, not measured ones. A ledger of
    REAL energies is :func:`blocked_ledger`, which is
    ``BLOCKED_MISSING_INPUT``.
    """
    values = {
        "e_out": float(e_out),
        "e_dissipated": float(e_dissipated),
        "e_stored": float(e_stored),
    }
    if drop is not None and drop not in LEDGER_TERMS:
        raise DAQError(f"{drop!r} is not a ledger term")
    included = {k: v for k, v in values.items() if k != drop}
    outputs_total = float(sum(included.values()))
    residual = float(e_in) - outputs_total
    efficiency = (values["e_out"] / float(e_in)) if float(e_in) != 0.0 \
        else float("nan")
    return {
        "identity": "E_in = E_out + E_dissipated + E_stored",
        "e_in": float(e_in),
        "e_out": values["e_out"],
        "e_dissipated": values["e_dissipated"],
        "e_stored": values["e_stored"],
        "dropped_term": drop,
        "outputs_total": outputs_total,
        "residual": residual,
        "efficiency": efficiency,
        "closes": bool(abs(residual) <= float(tol)),
        "claim_class": NUMERICAL_SIMULATION,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
    }


#: A synthetic ledger whose dyadic terms close in binary64 exactly. Every
#: number is a model value in joules, not a measurement.
SYNTHETIC_LEDGER: dict[str, float] = {
    "e_out": 6.0,
    "e_dissipated": 3.0,
    "e_stored": 1.0,
}
SYNTHETIC_INPUT = float(sum(SYNTHETIC_LEDGER.values()))     # 10.0 J exactly


def synthetic_ledger(drop: str | None = None) -> dict:
    """The power control: a ledger with known terms that closes exactly.

    With every term present the residual is exactly zero. Drop a term and
    the residual is exactly that term -- neither approximately nor to a
    tolerance -- which is the point of the control.
    """
    return energy_ledger(SYNTHETIC_INPUT, drop=drop, **SYNTHETIC_LEDGER)


def blocked_ledger() -> dict:
    """The ledger of REAL energies, as it actually stands here: blocked.

    No drive voltage, current, dissipated heat or stored field has been
    measured in this environment, so a ledger of real energies cannot be
    formed at all. It is ``BLOCKED_MISSING_INPUT``.
    """
    return {
        "identity": "E_in = E_out + E_dissipated + E_stored",
        "status": BLOCKED_MISSING_INPUT,
        "reason": ("no drive energy, output energy, dissipation or stored "
                   "energy has been measured; no instrument was operated"),
        "claim_class": BLOCKED_MISSING_INPUT,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
    }


def refuse_unclosed_as_new_energy(
        residual: float = 0.0, interval: tuple = (-1.0, 1.0),
        claim: str = "a new energy channel") -> None:
    """Refuse a zero-spanning residual being called new energy. Always raises.

    A residual whose confidence interval includes zero is consistent with
    the books closing; the gap is a statement about calibration, not a
    discovery. Promoting it to a new energy channel is the move this
    refusal blocks.
    """
    lo, hi = float(interval[0]), float(interval[1])
    spans = lo <= 0.0 <= hi
    raise DAQError(
        f"refused: calling E_residual = {float(residual):g} J "
        f"{claim!r}. The reported interval is [{lo:g}, {hi:g}], which "
        f"{'includes' if spans else 'excludes'} zero. A residual that is "
        f"consistent with zero is an uncalibrated ledger, not a new energy "
        f"channel, and none of these energies was measured in the first "
        f"place: the real ledger is {BLOCKED_MISSING_INPUT}. {VERDICT}.")


# --- (5) the acquisition refusal ------------------------------------------

def refuse_synthetic_daq_as_acquired(
        claim: str = "these samples are acquired instrument data") -> None:
    """Synthetic sampled data is not acquired data. Always raises.

    Every record in this module is produced by evaluating a signal
    function on a modelled clock. No transducer, amplifier, anti-alias
    filter or analogue-to-digital converter was operated, so there is no
    acquisition to speak of. Treating synthetic samples as an instrument
    capture is the promotion this refusal blocks.
    """
    raise DAQError(
        f"refused: {claim!r}. The samples here come from evaluating a "
        f"signal_func on a modelled clock -- a {NUMERICAL_SIMULATION}, not "
        f"an acquisition. No sensor was read, no converter was clocked, and "
        f"no channel was digitised, so nothing was acquired. Synthetic "
        f"samples become acquired data only when an instrument produces "
        f"them, which did not happen here. {VERDICT}.")


# --- report ----------------------------------------------------------------

def daq_report() -> dict:
    """The standing statement of what this module is and is not."""
    return {
        "what_this_is": (
            "a synchronized data-acquisition model and an energy ledger, "
            "all synthetic: a Nyquist-aware sampler, multi-channel skew "
            "correction by cross-correlation, a phase-noise jitter model, "
            "and a drive-in-to-signal-out ledger that closes for declared "
            "values and is blocked for real ones"),
        "alias_identity": "f_alias = |f - fs*round(f/fs)|",
        "sync_note": ("relative channel skew is recovered by "
                      "cross-correlation and corrected to within one "
                      "sample"),
        "jitter_note": ("clock jitter is modelled as phase noise; more "
                        "jitter lowers a tone's SNR monotonically"),
        "ledger_identity": "E_in = E_out + E_dissipated + E_stored",
        "synthetic_ledger_closes": synthetic_ledger()["closes"],
        "real_ledger_status": BLOCKED_MISSING_INPUT,
        "refusals": [
            "refuse_unclosed_as_new_energy",
            "refuse_synthetic_daq_as_acquired",
        ],
        "claim_class": NUMERICAL_SIMULATION,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not say any signal was acquired, that any channel was "
            "digitised, or that any energy was measured. The samples come "
            "from evaluating functions on a modelled clock; the only ledger "
            "that closes here is a synthetic one built from declared dyadic "
            "values, and a ledger of real energies is BLOCKED_MISSING_INPUT "
            "because no instrument was operated. Synthetic samples are not "
            "acquired data, and a residual consistent with zero is not a "
            "new energy channel."),
    }


__all__ = [
    "VERDICT", "NUMERICAL_SIMULATION", "ANALYTIC_MODEL",
    "REPOSITORY_COMPUTATIONAL_RESULT", "BLOCKED_MISSING_INPUT",
    "MEASURED_HERE", "PHYSICAL_VALIDATION", "LEDGER_TOL", "DAQError",
    "SampledSignal", "sample", "alias_frequency", "dominant_frequency",
    "cross_correlation_lag", "SyncResult", "synchronize", "estimate_skews",
    "sample_with_jitter", "tone_snr", "jitter_snr",
    "LEDGER_TERMS", "energy_ledger", "SYNTHETIC_LEDGER", "SYNTHETIC_INPUT",
    "synthetic_ledger", "blocked_ledger", "refuse_unclosed_as_new_energy",
    "refuse_synthetic_daq_as_acquired", "daq_report",
]
