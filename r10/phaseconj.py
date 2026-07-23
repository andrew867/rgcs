"""R10.7 P09 — a phase-conjugate return path, treated as ordinary DSP.

The source material wants a signal "returned" so that it undoes the
distortion it picked up on the way out. That is not exotic. It is
**phase conjugation** / **time reversal**, the operating principle of
optical phase-conjugate mirrors and acoustic time-reversal mirrors, and
it is a century-old piece of linear-systems engineering. This module
gives it an honest, reproducible treatment and puts firewalls on the
two places where the picture invites a physical over-claim.

**The real result (it works, and it is conventional).** In a
*reciprocal* linear channel -- forward and return paths share the same
frequency response ``H(w)`` -- a phase-conjugated field sent back
through the channel refocuses. The round trip multiplies the spectrum
by ``H(w) * conj(H(w)) = |H(w)|**2``, which is real and non-negative:
the channel's phase distortion cancels exactly, and a pulse that was
smeared on the way out comes back compact. :func:`focusing_experiment`
demonstrates it and :func:`peak_to_rms` / :func:`effective_width`
put numbers on it.

**Phase conjugation is not one operation, and it is not magic.** The
mirror operation that refocuses is *spectral* conjugation
``E(w) -> conj(E(w))``, which in the time domain equals conjugate
**and** time-reverse. It is genuinely different from a pointwise
conjugate ``z*(t) = I - jQ`` on its own, from a sign flip ``-z(t)``,
and from a bare time reversal ``z(-t)``. Only the specific combination
refocuses; the others do not, and :func:`focusing_experiment` shows
each of them failing. Conjugation is a distinct, load-bearing step.

**Reciprocity is required, and it is the control.** In a
*nonreciprocal* channel (a Faraday isolator, a moving medium, any
forward/return asymmetry) the round trip multiplies by
``H_ret(w) * conj(H_fwd(w))``, whose phase does not vanish, and the
refocus fails. :func:`focusing_experiment` shows the metric collapsing
to chance. Conjugation without reciprocity buys nothing.

**A causality firewall.** Phase conjugation compensates *dispersive*
phase; it does **not** compensate the bulk time-of-flight. Fold the
propagation delay into the conjugated phase and the algebra will
cheerfully cancel it, placing the refocused peak at ``t = 0`` -- a
superluminal return. The physics forbids it: a mirror cannot act on
the forward signal before it arrives, so the earliest the return can
come back is the full round-trip light time.
:func:`refuse_superluminal_return` refuses the cancelled-delay answer,
and :func:`causal_round_trip` books the delay as a real shift that
conjugation cannot touch.

Nothing here is measured. No apparatus exists. The carrier, key, local
oscillator and message clock are separate typed roles and are not
collapsed into one resonance without an experiment to tell them apart.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

import numpy as np

# --- provenance for every constant -------------------------------------

C_M_PER_S = 299_792_458          # exact, SI definition of the metre

#: Fixed seed so every figure in this module is reproducible. It is the
#: date the phase 09 work was done, and it carries no other meaning.
SEED = 20260722

PROVENANCE = {
    "CARRIER_HZ": ("4096 == 2**12; the r10 carrier ladder "
                   "(see r10.phaseframes and r10.breach LADDER_4096_HZ)"),
    "KEY_HZ": ("925; the numerator of the exact phase-frame ratio "
               "q = 925/4096 in r10.phaseframes"),
    "SAMPLE_RATE_HZ": ("32768 == 2**15, chosen so the carrier gets exactly "
                       "8 samples per cycle; a modelling choice, not a "
                       "physical rate"),
    "C_M_PER_S": "299792458, the SI definition of the metre",
}

CARRIER_HZ = Fraction(4096)
KEY_HZ = Fraction(925)
SAMPLE_RATE_HZ = Fraction(32768)

VERDICTS = (
    "PHASE_CONJUGATE_BASELINE_VALID",
    "RECIPROCITY_REQUIRED",
    "CAUSAL_DELAY_REQUIRED",
    "PHYSICAL_VALIDATION_NOT_CLAIMED",
)


class CausalityViolation(RuntimeError):
    """Raised when a return is claimed to arrive before the round trip."""


class Nonreciprocal(RuntimeError):
    """Raised when refocus is claimed without a reciprocal channel."""


class RoleCollapse(TypeError):
    """Raised when two distinct signal roles are treated as one."""


# --- (1) analytic signal and the pointwise conjugate --------------------

def analytic_signal(x: np.ndarray) -> np.ndarray:
    """z(t) = I(t) + jQ(t) via the FFT Hilbert method.

    Identical to ``scipy.signal.hilbert``: zero the negative-frequency
    half of the spectrum and double the positive half. The real part is
    the input; the imaginary part is its Hilbert transform.
    """
    x = np.asarray(x, dtype=float)
    n = x.shape[-1]
    if n == 0:
        raise ValueError("empty signal")
    spec = np.fft.fft(x)
    h = np.zeros(n)
    if n % 2 == 0:
        h[0] = h[n // 2] = 1.0
        h[1:n // 2] = 2.0
    else:
        h[0] = 1.0
        h[1:(n + 1) // 2] = 2.0
    return np.fft.ifft(spec * h)


def split_iq(z: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (I, Q) = (Re z, Im z)."""
    z = np.asarray(z)
    return (np.real(z).copy(), np.imag(z).copy())


def phase_conjugate(z: np.ndarray) -> np.ndarray:
    """z*(t) = I(t) - jQ(t): the *pointwise* conjugate. Distinct on its
    own from a sign flip and from a time reversal, and by itself it does
    NOT refocus a channel (see :func:`focusing_experiment`)."""
    return np.conj(np.asarray(z))


def sign_invert(z: np.ndarray) -> np.ndarray:
    """-z(t): negate. This is not conjugation; it flips I as well as Q."""
    return -np.asarray(z)


def time_reverse(z: np.ndarray) -> np.ndarray:
    """z[(-n) mod N]: circular time reversal, the DFT-consistent flip.

    Bare reversal (without conjugation) does not refocus a dispersive
    channel either.
    """
    z = np.asarray(z)
    return np.concatenate((z[:1], z[:0:-1]))


def phase_conjugate_mirror(z: np.ndarray) -> np.ndarray:
    """The operation an ideal phase-conjugate mirror performs on a field:
    *spectral* conjugation ``E(w) -> conj(E(w))``.

    By the DFT this equals ``conj(time_reverse(z))`` exactly -- conjugate
    AND time-reverse. That composition is what refocuses a reciprocal
    channel; neither component alone does.
    """
    return np.fft.ifft(np.conj(np.fft.fft(np.asarray(z))))


# --- focusing metrics ---------------------------------------------------

def peak_to_rms(env: np.ndarray) -> float:
    """Crest factor of |env|: max amplitude over RMS amplitude.

    A compact pulse concentrates energy and scores high; a field smeared
    across the record scores low. Invariant under time reversal, so a
    perfectly refocused pulse scores exactly what the original did.
    """
    a = np.abs(np.asarray(env))
    ms = float(np.mean(a * a))
    if ms <= 0.0:
        return 0.0
    return float(a.max() / math.sqrt(ms))


def effective_width(env: np.ndarray) -> float:
    """Participation width in samples: (sum p)**2 / sum p**2 with
    p = |env|**2. A single spike has width ~1; energy spread over the
    whole record of length N has width ~N."""
    p = np.abs(np.asarray(env)) ** 2
    s = float(p.sum())
    if s <= 0.0:
        return 0.0
    return float(s * s / float(np.sum(p * p)))


# --- the channel and the round trip -------------------------------------

def phase_screen(n: int, seed: int, *, strength: float = math.pi) -> np.ndarray:
    """A synthetic reciprocal channel: a random all-pass phase screen.

    ``|H(w)| == 1`` exactly at every bin, so the channel only smears
    phase, it removes no energy, and ``H * conj(H) == 1`` is exact. Two
    calls with the same seed give the same channel -- that identity is
    what "reciprocal" means here.
    """
    if n <= 0:
        raise ValueError("n must be positive")
    rng = np.random.default_rng(seed)
    phase = rng.uniform(-strength, strength, n)
    phase[0] = 0.0                       # no global phase offset
    return np.exp(1j * phase)


def propagate(env: np.ndarray, channel: np.ndarray) -> np.ndarray:
    """Send a complex envelope through a channel given as H(w)."""
    env = np.asarray(env)
    if env.shape != channel.shape:
        raise ValueError("envelope and channel length differ")
    return np.fft.ifft(np.fft.fft(env) * channel)


def make_pulse(n: int = 4096, *, center: int | None = None,
               width: float = 6.0, seed: int = SEED) -> np.ndarray:
    """A compact complex baseband pulse: a narrow Gaussian carrying a
    little random structure so it is generic (not symmetric, not real)."""
    if center is None:
        center = n // 2
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    envelope = np.exp(-0.5 * ((t - center) / width) ** 2)
    phase = rng.uniform(-math.pi, math.pi) * np.ones(n)
    twist = 0.15 * (t - center) / width
    return envelope * np.exp(1j * (phase + twist))


#: The return-path mirror operations. Only ``phase_conjugate`` refocuses
#: a reciprocal channel; the rest are here to prove that.
MIRRORS = {
    "phase_conjugate": phase_conjugate_mirror,      # conj o time-reverse
    "pointwise_conjugate": phase_conjugate,         # conj only
    "time_reverse": time_reverse,                   # reverse only
    "sign_flip": sign_invert,                       # negate
    "identity": lambda z: np.asarray(z).copy(),     # no processing
}


def _random_return(received: np.ndarray, seed: int) -> np.ndarray:
    """A non-conjugate return: same spectral magnitude, random phase.
    The false-refocus null -- energy-matched, but not the conjugate."""
    rng = np.random.default_rng(seed)
    spec = np.fft.fft(np.asarray(received))
    phase = rng.uniform(-math.pi, math.pi, spec.shape[-1])
    return np.fft.ifft(np.abs(spec) * np.exp(1j * phase))


def round_trip(pulse: np.ndarray, forward: np.ndarray, back: np.ndarray,
               mirror: str) -> np.ndarray:
    """Forward through ``forward``, apply the mirror, return through
    ``back``. Reciprocal means ``back is forward``."""
    if mirror not in MIRRORS:
        raise ValueError(f"unknown mirror {mirror!r}")
    received = propagate(pulse, forward)
    returned = MIRRORS[mirror](received)
    return propagate(returned, back)


def false_refocus(pulse: np.ndarray, channel: np.ndarray,
                  seed: int) -> np.ndarray:
    """A random (non-conjugate) return through the reciprocal channel."""
    received = propagate(pulse, channel)
    returned = _random_return(received, seed)
    return propagate(returned, channel)


# --- (2,3,4,7) the whole experiment, as numbers -------------------------

def focusing_experiment(*, n: int = 4096, seed: int = SEED,
                        null_trials: int = 200) -> dict:
    """Run every case and report the focusing metric for each.

    * ``reciprocal_conjugate`` -- the real refocus. Exact: the returned
      envelope equals ``conj(reverse(pulse))``, so its metric equals the
      original's to floating-point precision.
    * ``reciprocal_identity`` / ``pointwise_conjugate`` / ``time_reverse``
      / ``sign_flip`` -- reciprocal channel, wrong return operation. None
      refocus. This is the (4) distinction, made quantitative.
    * ``nonreciprocal_conjugate`` -- (3) right operation, wrong channel.
      Refocus fails.
    * ``false_refocus`` -- (7) energy-matched random return. At chance.
    """
    pulse = make_pulse(n, seed=seed)
    fwd = phase_screen(n, seed, strength=math.pi)
    other = phase_screen(n, seed + 1, strength=math.pi)

    base = peak_to_rms(pulse)
    cases = {
        "original": pulse,
        "reciprocal_conjugate": round_trip(pulse, fwd, fwd, "phase_conjugate"),
        "reciprocal_identity": round_trip(pulse, fwd, fwd, "identity"),
        "reciprocal_pointwise_conjugate":
            round_trip(pulse, fwd, fwd, "pointwise_conjugate"),
        "reciprocal_time_reverse":
            round_trip(pulse, fwd, fwd, "time_reverse"),
        "reciprocal_sign_flip": round_trip(pulse, fwd, fwd, "sign_flip"),
        "nonreciprocal_conjugate":
            round_trip(pulse, fwd, other, "phase_conjugate"),
        "false_refocus": false_refocus(pulse, fwd, seed + 7),
    }
    metrics = {k: peak_to_rms(v) for k, v in cases.items()}
    widths = {k: effective_width(v) for k, v in cases.items()}

    # (7) the null distribution: many independent random returns.
    rng = np.random.default_rng(seed + 1000)
    null = np.array([
        peak_to_rms(false_refocus(pulse, fwd, int(rng.integers(1 << 31))))
        for _ in range(null_trials)])

    refocus = metrics["reciprocal_conjugate"]
    null_mean = float(null.mean())
    null_std = float(null.std())
    z = (refocus - null_mean) / null_std if null_std > 0 else math.inf

    return {
        "base_peak_to_rms": base,
        "peak_to_rms": metrics,
        "effective_width": widths,
        "refocus_exact": bool(np.allclose(
            np.abs(cases["reciprocal_conjugate"]),
            np.abs(time_reverse(pulse)), atol=1e-9)),
        "null_mean": null_mean,
        "null_std": null_std,
        "null_max": float(null.max()),
        "refocus_z_over_null": z,
        "verdict": "PHASE_CONJUGATE_BASELINE_VALID",
        "measured_here": "nothing",
    }


def refuse_role_collapse(a: "Role", b: "Role",
                         discriminating_experiment: str | None = None) -> None:
    """Refuse to treat two roles as one without a way to tell them apart.

    The carrier (4096 Hz), the key (925 Hz), the local oscillator and
    the message clock are four different jobs. Some may even sit at the
    same frequency in a given build -- but "same frequency" is not "same
    role", and only an experiment that discriminates them licenses
    merging them.
    """
    if a == b:
        return
    if discriminating_experiment:
        return
    raise RoleCollapse(
        f"{a.value!r} and {b.value!r} are separate signal roles and may "
        f"not be treated as one without an experiment that discriminates "
        f"them. A carrier is not a key, a key is not a local oscillator, "
        f"and a message clock is none of them; sharing a frequency is a "
        f"coincidence of numbers, not an identity of roles.")


# --- (6) the roles, kept separate ---------------------------------------

class Role(Enum):
    CARRIER = "carrier"
    KEY = "key"
    LOCAL_OSCILLATOR = "local_oscillator"
    MESSAGE_CLOCK = "message_clock"


#: Frequencies where a role has a fixed one. The local oscillator and the
#: message clock do not: the LO is set at mix-down and the clock is the
#: symbol rate, both free parameters, and pinning them to a constant here
#: would be exactly the role-collapse the module refuses.
ROLE_FREQ_HZ: dict[Role, Fraction | None] = {
    Role.CARRIER: CARRIER_HZ,
    Role.KEY: KEY_HZ,
    Role.LOCAL_OSCILLATOR: None,
    Role.MESSAGE_CLOCK: None,
}


# --- (5) the causality firewall -----------------------------------------

@dataclass(frozen=True)
class CausalBudget:
    """The propagation-delay bookkeeping for a return path."""

    path_length_m: float
    sample_rate_hz: float

    def __post_init__(self) -> None:
        if self.path_length_m < 0:
            raise ValueError("path length cannot be negative")
        if self.sample_rate_hz <= 0:
            raise ValueError("sample rate must be positive")

    @property
    def one_way_delay_s(self) -> float:
        return self.path_length_m / C_M_PER_S

    @property
    def round_trip_delay_s(self) -> float:
        return 2.0 * self.path_length_m / C_M_PER_S

    @property
    def round_trip_delay_samples(self) -> int:
        return int(round(self.round_trip_delay_s * self.sample_rate_hz))


def refuse_superluminal_return(reported_arrival_samples: float,
                               causal_delay_samples: float) -> None:
    """Refuse any return whose peak is reported earlier than the round
    trip. Phase conjugation cancels *dispersive* phase, and if the bulk
    time-of-flight is folded into that phase the algebra cancels it too,
    putting the refocused peak at ``t = 0``. That is the trap. A mirror
    cannot act on a signal it has not yet received, so the earliest a
    return can arrive is the full round-trip light time."""
    if reported_arrival_samples < causal_delay_samples - 1e-9:
        raise CausalityViolation(
            f"a refocused return reported at "
            f"{reported_arrival_samples:g} samples would arrive before "
            f"the causal round-trip delay of {causal_delay_samples:g} "
            f"samples. Phase conjugation compensates dispersion, not "
            f"time-of-flight: the mirror cannot act before the forward "
            f"signal arrives, and the return still takes at least the "
            f"one-way light time. CAUSAL_DELAY_REQUIRED.")


def naive_delay_cancellation(n: int = 4096, *, center: int = 200,
                             delay_samples: int = 400) -> dict:
    """The trap, made explicit. Treat the propagation delay as ordinary
    phase and let the round-trip conjugation act on it in one shared
    buffer: the linear-phase term cancels and the round-trip delay
    evaporates to zero. The refocused peak lands exactly where a
    zero-delay conjugate reflection would put it, so the buffer math
    implies the return took no time at all -- a superluminal answer.

    Returns the *implied* round-trip delay (0), which is the number
    :func:`refuse_superluminal_return` exists to reject.
    """
    pulse = np.zeros(n, dtype=complex)
    pulse[center % n] = 1.0

    # reference: a conjugate reflection with NO propagation delay.
    reference = np.fft.ifft(np.conj(np.fft.fft(pulse)))
    ref_peak = int(np.argmax(np.abs(reference)))

    # now fold a real propagation delay into the conjugated phase.
    delay = np.exp(-2j * math.pi * np.fft.fftfreq(n) * delay_samples)
    forward_spec = np.fft.fft(pulse) * delay          # forward leg
    # return leg conjugates and folds the same delay: conj(delay)*delay==1
    tripped = np.fft.ifft(np.conj(forward_spec) * delay)
    trip_peak = int(np.argmax(np.abs(tripped)))

    implied = (trip_peak - ref_peak) % n
    return {
        "implied_round_trip_delay_samples": implied,
        "requested_delay_samples": delay_samples,
        "causal_delay_samples": 2 * delay_samples,
        "note": ("the round-trip delay cancelled inside the shared "
                 "buffer; the conjugation reflects the timeline and "
                 "negates the forward delay, so the buffer alone can "
                 "never account for time-of-flight -- it must be booked "
                 "externally"),
    }


def causal_round_trip(n: int = 4096, *, seed: int = SEED,
                      delay_samples: int = 400, width: float = 6.0) -> dict:
    """An honest round trip. The refocused *shape* is real DSP -- the
    compact envelope of the reciprocal phase-conjugate refocus. The
    *timing* is an external ledger conjugation cannot touch: the mirror
    records for one one-way delay before it can retransmit, and the
    return takes another, so the refocused pulse is delivered at
    ``2 * delay_samples`` and never earlier.

    Unlike :func:`naive_delay_cancellation`, the delay is not folded into
    the conjugated phase (where it would cancel); it is a physical shift
    imposed on top of the compact refocus.
    """
    causal = 2 * delay_samples
    if causal + int(8 * width) >= n:
        raise ValueError("record too short for this delay; increase n")

    # the compact refocused envelope, from an actual reciprocal round trip
    pulse = make_pulse(n, center=n // 2, width=width, seed=seed)
    fwd = phase_screen(n, seed, strength=math.pi)
    refocused = round_trip(pulse, fwd, fwd, "phase_conjugate")
    env = np.abs(refocused)                       # compact, non-negative

    # deliver that compact envelope with its peak at the causal round trip
    shape_peak = int(np.argmax(env))
    delivered = np.zeros(n)
    shift = causal - shape_peak
    idx = (np.arange(n) + shift) % n
    delivered[idx] = env                          # place peak at ``causal``

    peak = int(np.argmax(delivered))
    return {
        "refocused_envelope": delivered,
        "refocused_peak_to_rms": peak_to_rms(refocused),
        "emit_index": 0,
        "peak_index": peak,
        "arrival_samples": peak,                  # emitted at index 0
        "causal_delay_samples": causal,
        "arrives_no_earlier_than_causal": peak >= causal,
        "buffer_math_would_give_samples":
            naive_delay_cancellation(
                n, delay_samples=delay_samples
            )["implied_round_trip_delay_samples"],
        "verdict": "CAUSAL_DELAY_REQUIRED",
    }


# --- report -------------------------------------------------------------

def phaseconj_report() -> dict:
    return {
        "what_this_is": (
            "phase conjugation / time reversal, the operating principle "
            "of phase-conjugate mirrors and time-reversal mirrors; "
            "ordinary linear-systems DSP"),
        "the_real_result": (
            "in a reciprocal channel a phase-conjugated return refocuses "
            "the channel's phase distortion, because the round trip "
            "multiplies the spectrum by |H|**2, which is real"),
        "the_controls": [
            "reciprocity is required: a nonreciprocal channel does not "
            "refocus (RECIPROCITY_REQUIRED)",
            "conjugation is a specific operation: a sign flip, a bare "
            "time reversal, or a pointwise conjugate alone do not "
            "refocus",
            "a random energy-matched return does not refocus: the "
            "refocus is real, not an artifact of the metric",
        ],
        "firewalls": [
            "phase conjugation compensates dispersion, not time-of-"
            "flight; the return still takes the round-trip light time",
            "the carrier, key, local oscillator and message clock are "
            "separate roles and are not collapsed into one resonance",
        ],
        "roles": {r.name: (str(ROLE_FREQ_HZ[r]) if ROLE_FREQ_HZ[r]
                           else "free parameter") for r in Role},
        "provenance": PROVENANCE,
        "verdicts": list(VERDICTS),
        "evidence_class": "DERIVED_MATHEMATICS",
        "hardware_status": "DEFERRED — no apparatus has been built",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "what_this_does_not_say": (
            "It does not say any signal was sent, returned, or refocused "
            "on a bench. It does not say a channel was measured, that a "
            "return beat the light-time, or that conjugation transmits "
            "anything faster than light. The refocus is a property of "
            "reciprocal linear channels, shown in simulation with a "
            "fixed seed, and the causality firewall is the point, not a "
            "caveat."),
    }
