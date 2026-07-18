"""P06 — information-carrier transduction.

The contract (core/06) is a communications system:

    M --E--> X(t) --T_q--> Y(t)

with M the message, E the encoder, X(t) the physical carrier waveform,
T_q the quartz/apparatus transfer operator, and Y(t) the observation.
Known digital messages and controlled waveforms first; symbol error,
capacity, mutual information, transfer function, nonlinear features,
stability and decoder generalization measured before anything else is
discussed.

The module exists mostly to hold one ceiling firmly in place.

**The semantic ceiling.** A claim that *message content* affects the
output beyond the waveform differences it produced is the claim

    I(M ; Y | X, A) > 0

with A the apparatus and nuisance state. Conditioning on X is what
makes it a real claim rather than a restatement of "different
messages make different waveforms, and different waveforms make
different outputs" — which is true of a telephone and is not
interesting. :func:`semantic_information_test` implements that
conditioning, and its honest outcome is zero: if two different messages
produce the same waveform and the apparatus responds to the waveform,
conditioning removes the apparent mutual information entirely.

The test additionally refuses to report anything else without blinded
labels, held-out decoding and independent replication, and it always
reports a permutation null over message labels. The strongest thing it
can ever return is that a semantic effect was not excluded — a
residual, on the r6 ladder, at UNEXPLAINED_INSTRUMENT_RESIDUAL.

**Nothing here is bench data.** No waveform has been transmitted, no
crystal driven, no output recorded. Every number this module produces
comes from a declared model with a declared seed. And no human
intention or EEG experiment precedes the digital-message control
system: see :func:`refuse_intention_experiment`.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, asdict

from . import PHRYLL_CLASSES

# --------------------------------------------------------------------
# Encoder E
# --------------------------------------------------------------------

#: Symbol constellations, one entry per bit value (index 0 -> bit 0).
#:
#: OOK and BPSK are dimensionless normalized amplitudes. FSK symbols
#: are frequency offsets in Hz about the carrier, which is why its
#: numbers are large: an FSK symbol is not an amplitude and the two
#: schemes are not on a common scale. Keeping them in their own units
#: is deliberate — rescaling FSK to +/-1 would silently turn it into
#: BPSK and hide the fact that a frequency-keyed channel has a
#: different noise geometry.
CONSTELLATIONS: dict[str, tuple[float, float]] = {
    "OOK": (0.0, 1.0),
    "BPSK": (-1.0, 1.0),
    "FSK": (-1000.0, 1000.0),
}

SCHEMES = tuple(CONSTELLATIONS)

#: Unit of the symbol values, per scheme.
SYMBOL_UNITS = {
    "OOK": "normalized amplitude",
    "BPSK": "normalized amplitude",
    "FSK": "Hz frequency offset from carrier",
}


class RefusedError(RuntimeError):
    """Raised when an operation is refused rather than approximated."""


def _bits(message_bits) -> tuple[int, ...]:
    if isinstance(message_bits, str):
        out = []
        for ch in message_bits:
            if ch not in "01":
                raise ValueError(
                    f"message bit string contains {ch!r}; expected 0/1")
            out.append(int(ch))
        return tuple(out)
    out = []
    for b in message_bits:
        ib = int(b)
        if ib not in (0, 1):
            raise ValueError(f"message bit {b!r} is not 0 or 1")
        out.append(ib)
    return tuple(out)


def encode(message_bits, scheme: str) -> tuple[float, ...]:
    """M --E--> X: map message bits to a symbol sequence.

    Deterministic and stateless: the same bits and scheme always give
    the same symbols, with no RNG anywhere. One symbol per bit.
    """
    if scheme not in CONSTELLATIONS:
        raise ValueError(
            f"unknown scheme {scheme!r}; supported: {SCHEMES}")
    points = CONSTELLATIONS[scheme]
    return tuple(points[b] for b in _bits(message_bits))


def decide(symbols, scheme: str) -> tuple[float, ...]:
    """Hard-decide observed values onto the nominal constellation.

    Nearest-point decision. Ties (exactly midway) resolve to the
    lower-index point, which is an arbitrary but *fixed* convention so
    the decision is deterministic.
    """
    if scheme not in CONSTELLATIONS:
        raise ValueError(f"unknown scheme {scheme!r}")
    points = CONSTELLATIONS[scheme]
    out = []
    for y in symbols:
        best, best_d = points[0], abs(y - points[0])
        for p in points[1:]:
            d = abs(y - p)
            if d < best_d:
                best, best_d = p, d
        out.append(best)
    return tuple(out)


def decode(symbols, scheme: str) -> tuple[int, ...]:
    """X --> M: recover bits from (possibly noisy) symbol values."""
    points = CONSTELLATIONS[scheme]
    return tuple(points.index(s) for s in decide(symbols, scheme))


# --------------------------------------------------------------------
# Channel T_q
# --------------------------------------------------------------------

@dataclass(frozen=True)
class Channel:
    """A model of the apparatus transfer operator T_q.

    Deliberately crude and completely declared:

        delay      -> integer sample shift, zero-filled
        band-limit -> one-pole low-pass, alpha = 1 - exp(-2 pi B / fs)
        gain and   -> y = gain * (x + nonlinearity * x^3)
        nonlinearity
        noise      -> additive Gaussian, sigma, from a seeded RNG

    applied in that order. The cubic term is the smallest nonlinearity
    that produces harmonic and intermodulation products without
    breaking the sign symmetry of BPSK; a real quartz apparatus has
    more structure than this, and any fitted transfer function must
    replace this model rather than decorate it.

    This is a model. No apparatus has been characterized.
    """

    gain: float = 1.0
    bandwidth_hz: float = 1e6
    nonlinearity: float = 0.0
    noise_sigma: float = 0.0
    delay_samples: int = 0
    sample_rate_hz: float = 1e6

    def __post_init__(self) -> None:
        if self.gain <= 0:
            raise ValueError("gain must be positive")
        if self.bandwidth_hz <= 0:
            raise ValueError("bandwidth must be positive")
        if self.noise_sigma < 0:
            raise ValueError("noise sigma must be non-negative")
        if self.delay_samples < 0 or int(self.delay_samples) != \
                self.delay_samples:
            raise ValueError("delay_samples must be a non-negative integer")
        if self.sample_rate_hz <= 0:
            raise ValueError("sample rate must be positive")

    @property
    def alpha(self) -> float:
        """One-pole smoothing coefficient in (0, 1]."""
        a = 1.0 - math.exp(-2.0 * math.pi * self.bandwidth_hz
                           / self.sample_rate_hz)
        return min(1.0, a)

    def effective_bandwidth_hz(self) -> float:
        """Bandwidth actually usable at this sample rate (Nyquist-capped)."""
        return min(self.bandwidth_hz, self.sample_rate_hz / 2.0)

    def as_record(self) -> dict:
        d = asdict(self)
        d["alpha"] = self.alpha
        d["effective_bandwidth_hz"] = self.effective_bandwidth_hz()
        return d


def transmit(x, channel: Channel, seed: int) -> tuple[float, ...]:
    """X(t) --T_q--> Y(t). Deterministic given ``seed``.

    ``seed`` is required, not optional: an unseeded channel makes a
    result irreproducible, and an irreproducible result cannot be
    checked against a null.
    """
    xs = [float(v) for v in x]
    n = len(xs)

    delayed = [0.0] * channel.delay_samples + xs
    delayed = delayed[:n] if channel.delay_samples else xs

    a = channel.alpha
    filtered: list[float] = []
    state = 0.0
    for v in delayed:
        state = state + a * (v - state)
        filtered.append(state)

    rng = random.Random(seed)
    out: list[float] = []
    for v in filtered:
        y = channel.gain * (v + channel.nonlinearity * v ** 3)
        if channel.noise_sigma > 0:
            y += rng.gauss(0.0, channel.noise_sigma)
        out.append(y)
    return tuple(out)


def receive(y, channel: Channel, scheme: str) -> tuple[float, ...]:
    """Normalize out the known gain and hard-decide.

    Assumes the gain is known — which it is only because this is a
    model. On a bench the gain is estimated from a training sequence
    and that estimate carries its own uncertainty.
    """
    if channel.gain == 0:
        raise ValueError("cannot normalize a zero-gain channel")
    return decide([v / channel.gain for v in y], scheme)


def symbol_error_rate(sent, received) -> float:
    """Fraction of symbols that differ.

    Both arguments must be *decided* symbol sequences of equal length
    (see :func:`decide` / :func:`receive`). Comparing raw noisy floats
    against nominal symbols would report an error rate of 1.0 for any
    non-zero noise, which is true and useless.
    """
    sent = tuple(sent)
    received = tuple(received)
    if len(sent) != len(received):
        raise ValueError(
            f"length mismatch: {len(sent)} sent, {len(received)} received")
    if not sent:
        raise ValueError("cannot compute a symbol error rate on no symbols")
    return sum(1 for a, b in zip(sent, received) if a != b) / len(sent)


# --------------------------------------------------------------------
# Information measures
# --------------------------------------------------------------------

def entropy_bits(seq, *, correction: str = "none") -> float:
    """Plug-in Shannon entropy of an empirical sequence, in bits."""
    seq = tuple(seq)
    n = len(seq)
    if n == 0:
        raise ValueError("entropy of an empty sequence is undefined")
    counts: dict = {}
    for v in seq:
        counts[v] = counts.get(v, 0) + 1
    h = -sum((c / n) * math.log2(c / n) for c in counts.values())
    if correction == "miller_madow":
        h += (len(counts) - 1) / (2.0 * n)
    elif correction != "none":
        raise ValueError(f"unknown correction {correction!r}")
    return h


def mutual_information_bits(sent, received, *,
                            correction: str = "miller_madow") -> float:
    """Empirical mutual information I(X;Y) in bits, from the joint
    histogram.

    **Bias.** The plug-in (maximum-likelihood) estimator of mutual
    information from a finite sample is biased **UPWARD**. Its expected
    value exceeds the true MI by roughly

        (m_x - 1)(m_y - 1) / (2 N ln 2)   bits

    for N samples over alphabets of size m_x and m_y. Two *independent*
    variables therefore produce a positive measured MI, and the smaller
    the sample the larger it is. This matters enormously here: an
    upward-biased statistic applied to a small run is exactly how a
    channel that carries nothing comes to look like a channel that
    carries something. The bias is why every headline in this module
    needs a permutation null — the null absorbs the bias, because the
    permuted data has the same alphabet sizes and the same N.

    ``correction="miller_madow"`` (the default) applies the
    Miller-Madow entropy correction to each of H(X), H(Y) and H(X,Y),
    which subtracts most of the leading bias term. It reduces the
    estimate; it does not eliminate the bias, and it is not a
    substitute for the null. ``correction="none"`` gives the raw
    plug-in value.

    The result is clamped to ``[0, min(H(X), H(Y))]`` using the
    *uncorrected* plug-in entropies, because both ends of that interval
    are hard identities for the empirical joint distribution and the
    Miller-Madow term can otherwise push the estimate past them: the
    correction is applied to three entropies whose alphabet sizes need
    not satisfy m_xy >= m_x + m_y - 1, and when they do not, the
    corrected value can exceed the source entropy. A mutual information
    above the entropy of the source is an estimator artifact, and
    reporting one would invite exactly the over-reading this module
    exists to prevent.
    """
    sent = tuple(sent)
    received = tuple(received)
    if len(sent) != len(received):
        raise ValueError(
            f"length mismatch: {len(sent)} and {len(received)}")
    if not sent:
        raise ValueError("mutual information of an empty sample "
                         "is undefined")
    hx = entropy_bits(sent, correction=correction)
    hy = entropy_bits(received, correction=correction)
    hxy = entropy_bits(tuple(zip(sent, received)), correction=correction)
    ceiling = min(entropy_bits(sent), entropy_bits(received))
    return min(ceiling, max(0.0, hx + hy - hxy))


def conditional_mutual_information_bits(m, y, x, *,
                                        correction: str = "miller_madow",
                                        ) -> float:
    """I(M ; Y | X) in bits, as the X-weighted average of within-stratum
    MI.

    This is the quantity the semantic ceiling is about. Note the
    structural fact that makes the whole test honest: within a stratum
    where X is constant, if M is also constant then M and Y have
    nothing to be mutually informative *about*, and the stratum
    contributes exactly zero. A design in which every message maps to
    its own unique waveform therefore has no power at all — see
    :func:`semantic_information_test`, which detects that case and says
    so rather than reporting a comfortable zero.
    """
    m, y, x = tuple(m), tuple(y), tuple(x)
    if not (len(m) == len(y) == len(x)):
        raise ValueError("m, y and x must have equal length")
    if not m:
        raise ValueError("conditional MI of an empty sample is undefined")
    n = len(m)
    total = 0.0
    for xv in sorted(set(x), key=repr):
        idx = [i for i in range(n) if x[i] == xv]
        if len(idx) < 2:
            continue
        w = len(idx) / n
        total += w * mutual_information_bits(
            [m[i] for i in idx], [y[i] for i in idx],
            correction=correction)
    return total


def capacity_bound(channel: Channel, *, signal_power: float = 1.0) -> float:
    """Shannon capacity of the modeled AWGN channel, in bits/second.

        C = B log2(1 + S/N),  S/N = gain^2 * signal_power / sigma^2

    Any claimed throughput can be checked against this. A claim above
    C is a claim that the channel model is wrong, not that information
    got through.

    Caveats, since the formula is easy to over-trust: B is the
    Nyquist-capped bandwidth; the cubic nonlinearity is *not* covered
    by the AWGN result, and a strongly nonlinear channel needs its own
    capacity analysis; and this bounds a channel whose parameters were
    declared, not measured.
    """
    if channel.noise_sigma <= 0:
        raise ValueError(
            "a noiseless channel has unbounded capacity in this model; "
            "supply a positive noise_sigma so the bound means something")
    if signal_power <= 0:
        raise ValueError("signal power must be positive")
    snr = (channel.gain ** 2) * signal_power / (channel.noise_sigma ** 2)
    return channel.effective_bandwidth_hz() * math.log2(1.0 + snr)


# --------------------------------------------------------------------
# The semantic ceiling
# --------------------------------------------------------------------

#: Preconditions that must ALL hold before the test is permitted to
#: report anything other than "no semantic information above waveform".
SEMANTIC_PRECONDITIONS = (
    "blinded_labels",
    "held_out_decoding",
    "independent_replication",
)

SEMANTIC_STATUSES = (
    #: The design cannot test the question: every waveform stratum has
    #: a single message, so conditioning on X leaves nothing to vary.
    "DESIGN_DEGENERATE_NO_POWER",
    #: The honest default. Conditioning on the waveform drives the
    #: conditional MI to zero (or into the permutation null).
    "NO_SEMANTIC_INFORMATION_ABOVE_WAVEFORM",
    #: Conditional MI cleared the null, but the preconditions were not
    #: met, so the result is not reportable as anything but a lead.
    "PRECONDITIONS_NOT_MET",
    #: The strongest available outcome: not excluded. Still a residual.
    "SEMANTIC_EFFECT_NOT_EXCLUDED",
)


@dataclass(frozen=True)
class SemanticTestResult:
    """Outcome of the I(M;Y|X,A) test. Never a detection."""

    status: str
    evidence_class: str
    mi_marginal_bits: float
    mi_conditional_bits: float
    p_value: float
    n_permutations: int
    null_mean_bits: float
    null_max_bits: float
    alpha: float
    seed: int
    n_samples: int
    n_waveform_strata: int
    n_informative_strata: int
    preconditions: dict
    notes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status not in SEMANTIC_STATUSES:
            raise ValueError(f"unknown status {self.status!r}")
        if self.evidence_class not in PHRYLL_CLASSES:
            raise ValueError(
                f"evidence_class {self.evidence_class!r} is not on the "
                f"ladder {PHRYLL_CLASSES}")
        if not 0.0 <= self.p_value <= 1.0:
            raise ValueError("p value must lie in [0, 1]")

    def as_record(self) -> dict:
        d = asdict(self)
        d["notes"] = list(self.notes)
        d["ceiling"] = (
            "The strongest outcome available is "
            "SEMANTIC_EFFECT_NOT_EXCLUDED, which is a residual and not "
            "a detection.")
        return d


def semantic_information_test(messages, waveforms, observations, *,
                              blinded_labels: bool = False,
                              held_out_decoding: bool = False,
                              independent_replication: bool = False,
                              n_permutations: int = 1000,
                              alpha: float = 0.05,
                              seed: int = 20260718,
                              correction: str = "miller_madow",
                              ) -> SemanticTestResult:
    """Test I(M ; Y | X, A) > 0 — does message content add anything
    beyond the waveform?

    ``messages`` are message labels M, ``waveforms`` are waveform
    identities X (any hashable label; two trials sharing a label are
    asserted to have produced the *same* carrier waveform), and
    ``observations`` are the observed outputs Y, already reduced to a
    discrete statistic. Apparatus and nuisance state A should be folded
    into the waveform label when it is not constant across the run, so
    that conditioning is on (X, A) as the contract requires.

    Method:

    1. Report the marginal I(M;Y). It is *expected* to be positive and
       it means nothing on its own: different messages produce
       different waveforms and different waveforms produce different
       outputs. This is the number that gets quoted by mistake.
    2. Condition on the waveform. I(M;Y|X) is the X-weighted average of
       the within-stratum MI. If two different messages produced an
       identical waveform, this is where any real semantic effect would
       survive — and where an artifact of the encoder disappears.
    3. Permutation null: shuffle the message labels **within each
       waveform stratum**, so the null preserves the waveform-to-output
       relationship and destroys only the message-to-output one, then
       recompute. This is what absorbs the upward bias of the MI
       estimator (see :func:`mutual_information_bits`).
    4. Refuse to report anything but the ordinary outcome unless
       blinded labels, held-out decoding and independent replication
       are all in place.

    The honest outcome is NO_SEMANTIC_INFORMATION_ABOVE_WAVEFORM. The
    strongest possible outcome is SEMANTIC_EFFECT_NOT_EXCLUDED, which
    sits at UNEXPLAINED_INSTRUMENT_RESIDUAL on the r6 ladder and is a
    measurement not yet understood, not a discovery.

    Not bench data: no message has been transmitted through any
    apparatus.
    """
    m = tuple(messages)
    x = tuple(waveforms)
    y = tuple(observations)
    if not (len(m) == len(x) == len(y)):
        raise ValueError(
            f"messages ({len(m)}), waveforms ({len(x)}) and "
            f"observations ({len(y)}) must have equal length")
    if len(m) < 2:
        raise ValueError("need at least two trials")
    if n_permutations < 1:
        raise ValueError("need at least one permutation for the null")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie strictly in (0, 1)")

    n = len(m)
    strata: dict = {}
    for i in range(n):
        strata.setdefault(x[i], []).append(i)

    #: A stratum is informative only if it holds at least two trials
    #: AND more than one distinct message. Otherwise conditioning on X
    #: has already fixed M and there is nothing left to test.
    informative = [idx for idx in strata.values()
                   if len(idx) >= 2 and len({m[i] for i in idx}) > 1]

    notes: list[str] = [
        "Marginal I(M;Y) is expected to be positive whenever the "
        "encoder works, and is not evidence of anything semantic.",
        "The permutation null shuffles message labels within waveform "
        "strata, preserving the waveform-output relation.",
        "MI estimates are biased upward at small N; the null carries "
        "the same bias, which is the point of having it.",
        "Not bench data.",
    ]

    mi_marginal = mutual_information_bits(m, y, correction=correction)

    if not informative:
        notes.insert(0, (
            "DESIGN DEGENERATE: no waveform stratum contains two "
            "different messages, so conditioning on X fixes M and "
            "I(M;Y|X) is identically zero by construction. This is not "
            "a null result — it is a design with no power. Testing the "
            "semantic claim requires at least two distinct messages "
            "that produce the SAME waveform."))
        return SemanticTestResult(
            status="DESIGN_DEGENERATE_NO_POWER",
            evidence_class="OPERATIONAL_HYPOTHESIS",
            mi_marginal_bits=mi_marginal,
            mi_conditional_bits=0.0,
            p_value=1.0,
            n_permutations=0,
            null_mean_bits=0.0,
            null_max_bits=0.0,
            alpha=alpha,
            seed=seed,
            n_samples=n,
            n_waveform_strata=len(strata),
            n_informative_strata=0,
            preconditions={
                "blinded_labels": blinded_labels,
                "held_out_decoding": held_out_decoding,
                "independent_replication": independent_replication,
            },
            notes=tuple(notes))

    mi_cond = conditional_mutual_information_bits(
        m, y, x, correction=correction)

    rng = random.Random(seed)
    null: list[float] = []
    stratum_index = [idx for idx in strata.values()]
    for _ in range(n_permutations):
        permuted = list(m)
        for idx in stratum_index:
            labels = [m[i] for i in idx]
            rng.shuffle(labels)
            for i, lab in zip(idx, labels):
                permuted[i] = lab
        null.append(conditional_mutual_information_bits(
            permuted, y, x, correction=correction))

    #: Add-one p-value, so p is never zero and always lies in [0, 1].
    n_ge = sum(1 for v in null if v >= mi_cond)
    p_value = (1.0 + n_ge) / (1.0 + n_permutations)
    null_mean = sum(null) / len(null)
    null_max = max(null)

    preconditions = {
        "blinded_labels": blinded_labels,
        "held_out_decoding": held_out_decoding,
        "independent_replication": independent_replication,
    }
    unmet = [k for k, v in preconditions.items() if not v]

    cleared = (mi_cond > 0.0) and (p_value <= alpha)

    if not cleared:
        status = "NO_SEMANTIC_INFORMATION_ABOVE_WAVEFORM"
        evidence_class = "ORDINARY_CHANNEL_RESULT"
        notes.insert(0, (
            f"Conditioning on the waveform leaves I(M;Y|X) = "
            f"{mi_cond:.6g} bits against a null mean of "
            f"{null_mean:.6g} bits (p = {p_value:.4g}). The message "
            f"content adds nothing beyond the waveform it produced."))
    elif unmet:
        status = "PRECONDITIONS_NOT_MET"
        evidence_class = "ORDINARY_CHANNEL_RESULT"
        notes.insert(0, (
            f"I(M;Y|X) = {mi_cond:.6g} bits cleared the permutation "
            f"null (p = {p_value:.4g}), but the preconditions "
            f"{unmet} were not met, so this is a lead to be designed "
            f"against and not a reportable result. Waveform matching, "
            f"blinded labels, held-out decoding, artifact channels and "
            f"independent replication are all required (core/06)."))
    else:
        status = "SEMANTIC_EFFECT_NOT_EXCLUDED"
        evidence_class = "UNEXPLAINED_INSTRUMENT_RESIDUAL"
        notes.insert(0, (
            f"I(M;Y|X) = {mi_cond:.6g} bits cleared the permutation "
            f"null (p = {p_value:.4g}) with blinded labels, held-out "
            f"decoding and independent replication in place. A "
            f"semantic effect is NOT EXCLUDED. This is an unexplained "
            f"instrument residual: the most likely remaining "
            f"explanations are an unmodeled encoder-side difference "
            f"that the waveform label failed to capture, and an "
            f"apparatus or nuisance variable correlated with the "
            f"message schedule. Register it with r6.instrument and "
            f"work down that list."))

    return SemanticTestResult(
        status=status,
        evidence_class=evidence_class,
        mi_marginal_bits=mi_marginal,
        mi_conditional_bits=mi_cond,
        p_value=p_value,
        n_permutations=n_permutations,
        null_mean_bits=null_mean,
        null_max_bits=null_max,
        alpha=alpha,
        seed=seed,
        n_samples=n,
        n_waveform_strata=len(strata),
        n_informative_strata=len(informative),
        preconditions=preconditions,
        notes=tuple(notes))


# --------------------------------------------------------------------
# The refusal
# --------------------------------------------------------------------

#: Nuisance channels an EEG-derived carrier experiment must record
#: (core/06). Every one of these can produce a signal that a naive
#: pipeline will read as intention.
EEG_NUISANCE_CHANNELS = (
    "EOG",
    "EMG",
    "ECG",
    "respiration",
    "microphone",
    "accelerometer",
    "temperature",
    "motion",
    "timing",
    "experimenter_cues",
)


def refuse_intention_experiment(*args, **kwargs):
    """Always refuses. No human intention experiment runs here.

    core/06 is explicit: **no human intention experiment precedes the
    digital-message control system**, and EEG-derived carriers are
    later-stage only. The order is not bureaucratic. Until the digital
    control system has measured symbol error, capacity, mutual
    information, the transfer function, nonlinear features, stability
    and decoder generalization, there is no characterized channel for
    an intention experiment to be an experiment *about* — any result
    would be uninterpretable, and the interpretation reached for would
    be the exciting one.

    An EEG carrier additionally requires every channel in
    :data:`EEG_NUISANCE_CHANNELS` to be recorded, because ocular and
    muscular artifacts, cardiac and respiratory rhythm, ambient sound,
    head and body motion, skin temperature, timing structure and
    experimenter cues each produce EEG-band signals that survive
    conventional preprocessing and correlate with instructed intent.

    :raises RefusedError: always.
    """
    raise RefusedError(
        "refused: no human intention or EEG experiment precedes the "
        "digital-message control system (core/06). EEG-derived "
        "carriers are later-stage only, and require these nuisance "
        "channels to be recorded: "
        + ", ".join(EEG_NUISANCE_CHANNELS)
        + ". Run the digital control system first: encode(), "
          "transmit(), symbol_error_rate(), mutual_information_bits(), "
          "capacity_bound() and semantic_information_test(). R6 also "
          "does not test biological or medical claims "
          "(r6.BIOLOGICAL_REFUSAL_REASON).")


def refuse_eeg_carrier(*args, **kwargs):
    """Alias kept so the EEG refusal is findable by name."""
    return refuse_intention_experiment(*args, **kwargs)
