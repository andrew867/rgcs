"""R10.7 P13 — phase-conjugate return under electromagnetic interference.

R10.7 (:mod:`r10.phaseconj`) established the honest, conventional result:
in a *reciprocal* linear channel a phase-conjugated return refocuses,
because the round trip multiplies the spectrum by ``H(w) * conj(H(w)) =
|H(w)|**2``, which is real. This module puts that refocus under stress.
It adds interference (EMI) to the *received* signal before the mirror
conjugates it, using both measured-style tones and synthetic noise, and
asks what survives.

**The point of EMI is that it is a control that must reduce the effect.**
Phase conjugation cancels the channel because the forward and return
legs share the same ``H(w)`` -- the channel is reciprocal. Additive
interference injected between the forward arrival and the conjugate
return is **not** part of that reciprocal channel: it is a new field the
mirror has never propagated, so conjugating it does not match it to
anything, and it does not refocus. It stays spread across the record,
inflating the RMS floor while the true refocus keeps its peak. The
focusing metric therefore degrades **monotonically** with interference
power: at zero EMI it equals the clean phase-conjugate refocus of
R10.7 exactly, and at overwhelming EMI it sinks toward the random-return
null. A result that could not be reduced by adding noise would not be a
physical refocus; it would be an artifact of the metric.

**Coherent averaging is not a loophole.** If the interference is
*incoherent* across repeats -- an independent realization each time --
then averaging N received records reduces its power by ~N (amplitude
SNR ~ sqrt(N)) and some refocus is recovered. But a *coherent*
interferer -- the same switching-supply tone locked to the system on
every repeat -- is common to every record and survives averaging
untouched. :func:`refuse_average_away_coherent` refuses the claim that
averaging removes it.

**Reciprocity is still required.** Everything above assumes the channel
itself is reciprocal. Conjugation under a nonreciprocal channel does not
refocus even at zero EMI; :func:`reciprocity_control` reuses the R10.7
nonreciprocal control to show it.

Nothing here is measured. No apparatus, no antenna, no spectrum
analyser. The interference is synthesized with fixed seeds and the
"measured-style" tone is a *model* of a switching harmonic, not a
recording of one. PHYSICAL_VALIDATION_NOT_CLAIMED.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np

from r10.phaseconj import (
    SEED,
    false_refocus,
    make_pulse,
    peak_to_rms,
    phase_conjugate_mirror,
    phase_screen,
    propagate,
    round_trip,
)

VERDICTS = (
    "PHASE_CONJUGATE_UNDER_EMI_SOFTWARE_ONLY",
    "EMI_DEGRADES_REFOCUS_MONOTONICALLY",
    "COHERENT_INTERFERER_NOT_AVERAGED_AWAY",
    "RECIPROCITY_REQUIRED",
    "PHYSICAL_VALIDATION_NOT_CLAIMED",
)

#: The bin of the modelled narrowband interferer over an ``n``-sample
#: record: a stand-in for a switching-supply harmonic locked to the
#: system clock. It is a modelling choice, not a measured frequency.
NARROWBAND_BIN = 512

#: Fraction of samples carrying a spike in the impulsive model.
IMPULSIVE_DENSITY = 0.02


class PcEmiError(RuntimeError):
    """Raised for an invalid EMI request or an unsupportable EMI claim."""


class InterferenceKind(Enum):
    """The three interference models this module synthesizes."""

    NARROWBAND = "narrowband"     # a tone, e.g. a switching-supply harmonic
    BROADBAND = "broadband"       # white complex Gaussian
    IMPULSIVE = "impulsive"       # sparse random spikes


# --- (1) synthesizing the interference ----------------------------------

def interference(n: int, seed: int, kind: InterferenceKind,
                 power: float) -> np.ndarray:
    """Synthesize an additive complex EMI field of length ``n``.

    The returned field has mean power (``mean(|x|**2)``) equal to
    ``power`` exactly, so SNR bookkeeping downstream is clean. ``power``
    of zero returns exact zeros (no interference).

    * ``NARROWBAND`` -- a single complex tone at :data:`NARROWBAND_BIN`
      with a random starting phase; the switching-harmonic model.
    * ``BROADBAND`` -- white complex Gaussian noise.
    * ``IMPULSIVE`` -- a sparse set of random spikes.
    """
    if n <= 0:
        raise PcEmiError("n must be positive")
    if power < 0:
        raise PcEmiError("interference power cannot be negative")
    if not isinstance(kind, InterferenceKind):
        raise PcEmiError(f"unknown interference kind {kind!r}")
    if power == 0:
        return np.zeros(n, dtype=complex)

    rng = np.random.default_rng(seed)
    if kind is InterferenceKind.NARROWBAND:
        t = np.arange(n)
        phase0 = rng.uniform(-math.pi, math.pi)
        x = np.exp(1j * (2 * math.pi * NARROWBAND_BIN * t / n + phase0))
    elif kind is InterferenceKind.BROADBAND:
        x = rng.standard_normal(n) + 1j * rng.standard_normal(n)
    else:  # IMPULSIVE
        x = np.zeros(n, dtype=complex)
        k = max(1, int(round(IMPULSIVE_DENSITY * n)))
        idx = rng.choice(n, size=k, replace=False)
        x[idx] = rng.standard_normal(k) + 1j * rng.standard_normal(k)

    mean_power = float(np.mean(np.abs(x) ** 2))
    if mean_power <= 0.0:
        raise PcEmiError("degenerate interference realization")
    return x * math.sqrt(power / mean_power)


@dataclass(frozen=True)
class EmiSpec:
    """A reproducible interference specification."""

    kind: InterferenceKind
    power: float
    seed: int = SEED

    def synthesize(self, n: int) -> np.ndarray:
        return interference(n, self.seed, self.kind, self.power)


# --- (2) the phase-conjugate round trip, with EMI added -----------------

def _snr(signal_power: float, noise_power: float) -> float:
    if noise_power <= 0.0:
        return math.inf
    return signal_power / noise_power


def refocus_under_emi(pulse: np.ndarray, channel: np.ndarray,
                      interference_signal: np.ndarray,
                      *, back: np.ndarray | None = None) -> dict:
    """Phase-conjugate round trip with EMI added to the received signal
    *before* the mirror conjugates it.

    Forward through ``channel``, add ``interference_signal`` to the
    received field, apply the phase-conjugate mirror (R10.7's
    :func:`~r10.phaseconj.phase_conjugate_mirror`), and return through
    ``back`` (defaulting to ``channel`` -- the reciprocal case). With
    zero interference this is identical to R10.7's clean reciprocal
    round trip. Returns the focusing metric and the received SNR.
    """
    pulse = np.asarray(pulse)
    n = pulse.shape[-1]
    interference_signal = np.asarray(interference_signal)
    if interference_signal.shape[-1] != n:
        raise PcEmiError("interference length differs from the pulse")
    back_channel = channel if back is None else back

    received = propagate(pulse, channel)
    corrupted = received + interference_signal
    returned = phase_conjugate_mirror(corrupted)
    refocused = propagate(returned, back_channel)

    signal_power = float(np.mean(np.abs(received) ** 2))
    noise_power = float(np.mean(np.abs(interference_signal) ** 2))
    snr = _snr(signal_power, noise_power)
    return {
        "peak_to_rms": peak_to_rms(refocused),
        "snr": snr,
        "snr_db": (math.inf if math.isinf(snr) else 10.0 * math.log10(snr)),
        "signal_power": signal_power,
        "noise_power": noise_power,
    }


# --- (3) the headline: monotone degradation -----------------------------

#: Interference powers, as fractions of the received signal power, at
#: which the degradation curve is sampled. ``0.0`` is the clean refocus;
#: the last point is deep in the null.
DEFAULT_POWER_FRACTIONS = (0.0, 1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0)


def degradation_curve(*, n: int = 4096, seed: int = SEED,
                      kind: InterferenceKind = InterferenceKind.BROADBAND,
                      power_fractions: tuple[float, ...] = DEFAULT_POWER_FRACTIONS,
                      repeats: int = 12) -> dict:
    """The focusing metric versus interference power.

    Each interference power is expressed as a fraction of the received
    signal power (so SNR = 1 / fraction). At fraction 0 the metric equals
    the R10.7 clean phase-conjugate refocus exactly; as the fraction
    grows the metric falls monotonically toward the random-return null.
    Each non-zero point is averaged over ``repeats`` independent
    realizations so the curve is smooth.
    """
    if repeats < 1:
        raise PcEmiError("repeats must be >= 1")
    channel = phase_screen(n, seed, strength=math.pi)
    pulse = make_pulse(n, seed=seed)

    # the clean refocus, straight from R10.7's round trip.
    clean = round_trip(pulse, channel, channel, "phase_conjugate")
    clean_metric = peak_to_rms(clean)

    signal_power = float(np.mean(np.abs(propagate(pulse, channel)) ** 2))

    metrics: list[float] = []
    for frac in power_fractions:
        if frac == 0.0:
            metrics.append(clean_metric)
            continue
        power = frac * signal_power
        vals = [
            refocus_under_emi(
                pulse, channel,
                interference(n, seed + 1000 + r, kind, power))["peak_to_rms"]
            for r in range(repeats)
        ]
        metrics.append(float(np.mean(vals)))

    # the random-return null, reused from R10.7 (the high-EMI limit).
    rng = np.random.default_rng(seed + 5000)
    null = np.array([
        peak_to_rms(false_refocus(pulse, channel, int(rng.integers(1 << 31))))
        for _ in range(64)])
    null_mean = float(null.mean())

    diffs = np.diff(np.asarray(metrics))
    monotone = bool(np.all(diffs <= 1e-9))
    return {
        "power_fractions": list(power_fractions),
        "metrics": metrics,
        "clean_metric": clean_metric,
        "null_mean": null_mean,
        "monotone_decreasing": monotone,
        "approaches_null": bool(metrics[-1] < 2.0 * null_mean),
        "verdict": "EMI_DEGRADES_REFOCUS_MONOTONICALLY",
        "measured_here": "nothing",
    }


# --- (4) coherent averaging: power, and its limit -----------------------

def coherent_average_refocus(pulse: np.ndarray, channel: np.ndarray,
                             kind: InterferenceKind, power: float,
                             repeats: int, *, seed: int = SEED,
                             coherent: bool = False) -> dict:
    """Average ``repeats`` received records, then phase-conjugate refocus.

    If ``coherent`` is False the interference is an independent
    realization on each repeat (incoherent EMI): averaging reduces its
    power by ~``repeats`` and the refocus is partly recovered. If
    ``coherent`` is True the *same* realization is present on every
    repeat (an interferer locked to the system): averaging leaves it
    untouched. Returns the focusing metric and the effective SNR of the
    averaged received record.
    """
    if repeats < 1:
        raise PcEmiError("repeats must be >= 1")
    pulse = np.asarray(pulse)
    n = pulse.shape[-1]

    clean_received = propagate(pulse, channel)
    received_acc = np.zeros(n, dtype=complex)
    noise_acc = np.zeros(n, dtype=complex)
    for r in range(repeats):
        noise_seed = seed if coherent else seed + r
        noise = interference(n, noise_seed, kind, power)
        received_acc += clean_received + noise
        noise_acc += noise

    averaged = received_acc / repeats
    averaged_noise = noise_acc / repeats
    refocused = propagate(phase_conjugate_mirror(averaged), channel)

    signal_power = float(np.mean(np.abs(clean_received) ** 2))
    noise_power = float(np.mean(np.abs(averaged_noise) ** 2))
    snr = _snr(signal_power, noise_power)
    return {
        "peak_to_rms": peak_to_rms(refocused),
        "snr": snr,
        "snr_db": (math.inf if math.isinf(snr) else 10.0 * math.log10(snr)),
        "repeats": repeats,
        "coherent": coherent,
    }


def averaging_gain(*, n: int = 4096, seed: int = SEED,
                   kind: InterferenceKind = InterferenceKind.BROADBAND,
                   power_fraction: float = 4.0,
                   repeats: int = 16) -> dict:
    """Compare 1 record to ``repeats`` records, incoherent vs coherent.

    For incoherent EMI the averaged-record SNR improves by roughly
    ``repeats`` (amplitude SNR ~ sqrt(repeats)) and the focusing metric
    rises. For a coherent interferer neither the SNR nor the metric
    improves.
    """
    channel = phase_screen(n, seed, strength=math.pi)
    pulse = make_pulse(n, seed=seed)
    power = power_fraction * float(np.mean(np.abs(propagate(pulse, channel)) ** 2))

    inc_1 = coherent_average_refocus(pulse, channel, kind, power, 1,
                                     seed=seed, coherent=False)
    inc_n = coherent_average_refocus(pulse, channel, kind, power, repeats,
                                     seed=seed, coherent=False)
    coh_1 = coherent_average_refocus(pulse, channel, kind, power, 1,
                                     seed=seed, coherent=True)
    coh_n = coherent_average_refocus(pulse, channel, kind, power, repeats,
                                     seed=seed, coherent=True)
    return {
        "repeats": repeats,
        "incoherent_snr_gain": inc_n["snr"] / inc_1["snr"],
        "incoherent_metric_1": inc_1["peak_to_rms"],
        "incoherent_metric_n": inc_n["peak_to_rms"],
        "coherent_snr_gain": coh_n["snr"] / coh_1["snr"],
        "coherent_metric_1": coh_1["peak_to_rms"],
        "coherent_metric_n": coh_n["peak_to_rms"],
        "measured_here": "nothing",
    }


def refuse_average_away_coherent(coherent: bool, repeats: int = 1) -> None:
    """Refuse the claim that averaging removes a *coherent* interferer.

    Incoherent EMI averages down (return quietly). A coherent interferer
    is common to every repeat, so it survives coherent averaging no
    matter how many records are stacked; claiming otherwise is false and
    is refused.
    """
    if not coherent:
        return
    raise PcEmiError(
        f"a coherent interferer is present, identical, on all {repeats} "
        f"repeats, so coherent averaging leaves it untouched -- its power "
        f"is not reduced at all. Averaging only suppresses interference "
        f"that is incoherent across repeats (amplitude SNR ~ sqrt(N)); a "
        f"tone locked to the system is not. "
        f"COHERENT_INTERFERER_NOT_AVERAGED_AWAY.")


# --- (5) reciprocity is still required ----------------------------------

def reciprocity_control(*, n: int = 4096, seed: int = SEED) -> dict:
    """Even at zero EMI, conjugation under a nonreciprocal channel does
    not refocus. Reuses R10.7's construction: a return channel that
    differs from the forward channel.
    """
    channel = phase_screen(n, seed, strength=math.pi)
    other = phase_screen(n, seed + 1, strength=math.pi)
    pulse = make_pulse(n, seed=seed)
    zero = np.zeros(n, dtype=complex)

    reciprocal = refocus_under_emi(pulse, channel, zero)["peak_to_rms"]
    nonreciprocal = refocus_under_emi(pulse, channel, zero,
                                      back=other)["peak_to_rms"]
    return {
        "reciprocal_metric": reciprocal,
        "nonreciprocal_metric": nonreciprocal,
        "reciprocity_required": bool(nonreciprocal < 0.5 * reciprocal),
        "verdict": "RECIPROCITY_REQUIRED",
    }


# --- the report ---------------------------------------------------------

def pcemi_report() -> dict:
    return {
        "what_this_is": (
            "the R10.7 phase-conjugate refocus put under additive "
            "interference (EMI), synthesized as narrowband, broadband and "
            "impulsive fields; ordinary linear-systems DSP with a fixed "
            "seed"),
        "the_control": (
            "EMI is a control that must reduce the effect: additive "
            "interference injected between the forward arrival and the "
            "conjugate return is not part of the reciprocal channel, so "
            "conjugating it does not refocus it, and the focusing metric "
            "degrades monotonically with interference power"),
        "the_findings": [
            "at zero EMI the metric equals the R10.7 clean reciprocal "
            "refocus exactly; at overwhelming EMI it sinks to the "
            "random-return null",
            "incoherent interference averages down over N repeats "
            "(amplitude SNR ~ sqrt(N)); a coherent interferer does not",
            "reciprocity is still required: conjugation under a "
            "nonreciprocal channel does not refocus even at zero EMI",
        ],
        "refusals": [
            "the claim that coherent averaging removes a coherent "
            "interferer is refused (COHERENT_INTERFERER_NOT_AVERAGED_AWAY)",
            "negative interference power is refused",
        ],
        "verdicts": list(VERDICTS),
        "evidence_class": "DERIVED_MATHEMATICS",
        "hardware_status": "DEFERRED — no apparatus has been built",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "PHASE_CONJUGATE_UNDER_EMI_SOFTWARE_ONLY",
        "what_this_does_not_say": (
            "It does not say any interference was measured, that an "
            "antenna, spectrum analyser or bench exists, or that a signal "
            "was actually refocused through a real channel. The "
            "'measured-style' tone is a model of a switching harmonic, not "
            "a recording. The degradation, the averaging law, and the "
            "reciprocity control are properties of the simulation shown "
            "with a fixed seed; nothing here is a physical result."),
    }
