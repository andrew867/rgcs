"""P03 — exact common-phase closure in multi-tone DDS.

The result the R8.1 DDS paper rests on, stated generally rather than as
a worked example.

Setup. An N-bit phase accumulator driven by reference ``f_r`` with
integer tuning word ``K`` emits

    f = K * f_r / 2**N.

Every realizable output is therefore an integer multiple of the
*synthesis quantum*

    delta = f_r / 2**N,

and the whole question of phase closure is a question about that
quantum, not about the DAC, the filter, or the phase noise.

**Theorem (common closure).** Write ``delta = p/q`` in lowest terms.
For tuning words ``K_1..K_m`` the realized tones are ``f_i = K_i p/q``
and the least positive ``T`` with ``f_i T`` integral for every ``i`` is

    T = q / (p * gcd(K_1, ..., K_m)).

*Proof.* ``f_i T`` integral means ``K_i p T / q`` integral. Let
``g = gcd(K_i)`` and ``K_i = g k_i`` with ``gcd(k_i) = 1``. Then all
``f_i`` are multiples of ``g p / q`` and, since the ``k_i`` are
collectively coprime, ``gp/q`` is the largest such common divisor —
the tone set generates exactly the lattice ``(gp/q) Z``. ``T`` closes
the lattice iff ``T`` is a multiple of ``q/(gp)``, and the least
positive such value is ``q/(gp)``. Because ``p/q`` is in lowest terms,
``gcd(p, q) = 1``, so no further cancellation occurs. QED

Two corollaries carry the paper.

1. **Exactness is a property of the reference, not the resolution.**
   A requested tone ``f`` is exactly representable iff
   ``f * 2**N / f_r`` is an integer. Raising ``N`` shrinks the quantum
   but does not make ``5**8`` divide a power of two, so a decimal
   reference can never represent a dyadic tone set exactly, at any
   accumulator width.
2. **A slower clock can be strictly better.** ``2**26`` Hz
   (67.108864 MHz) is slower than 100 MHz and yet restores exact
   closure, because its quantum is dyadic.

Nothing here is measured. This is exact arithmetic over the rationals,
computed with :class:`fractions.Fraction`; a float implementation would
manufacture agreement at the tenth digit and hide the entire effect.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict, field
from fractions import Fraction

#: Rounding policies for choosing an integer tuning word.
TUNING_POLICIES = ("ROUND", "TRUNCATE")


class DDSRefused(RuntimeError):
    """Raised when a closure question is not well posed."""


# --------------------------------------------------------------------
# Core arithmetic
# --------------------------------------------------------------------

def synthesis_quantum(reference_hz: Fraction | int,
                      accumulator_bits: int) -> Fraction:
    """delta = f_r / 2**N, exactly."""
    if accumulator_bits <= 0:
        raise ValueError("accumulator width must be positive")
    if Fraction(reference_hz) <= 0:
        raise ValueError("reference frequency must be positive")
    return Fraction(reference_hz) / Fraction(2 ** accumulator_bits)


def tuning_word(target_hz: Fraction | int, reference_hz: Fraction | int,
                accumulator_bits: int, policy: str = "ROUND") -> int:
    """Integer tuning word for a requested tone."""
    if policy not in TUNING_POLICIES:
        raise ValueError(f"unknown tuning policy {policy!r}")
    exact = Fraction(target_hz) / synthesis_quantum(reference_hz,
                                                    accumulator_bits)
    if policy == "TRUNCATE":
        return int(exact)  # Fraction -> int truncates toward zero
    return round(exact)


def is_exactly_representable(target_hz: Fraction | int,
                             reference_hz: Fraction | int,
                             accumulator_bits: int) -> bool:
    """True iff the requested tone needs no rounding at all."""
    exact = Fraction(target_hz) / synthesis_quantum(reference_hz,
                                                    accumulator_bits)
    return exact.denominator == 1


def realized_frequency(word: int, reference_hz: Fraction | int,
                       accumulator_bits: int) -> Fraction:
    """The tone the synthesizer actually emits, exactly."""
    return word * synthesis_quantum(reference_hz, accumulator_bits)


def _lcm(a: int, b: int) -> int:
    return a * b // math.gcd(a, b)


def common_closure(words: tuple[int, ...],
                   reference_hz: Fraction | int,
                   accumulator_bits: int) -> Fraction:
    """T = q / (p * gcd(K_i)) — the theorem, applied.

    Derived in closed form from the reduced quantum, not by stepping
    phase or by searching. A brute-force search over 42.9 s at
    100 MHz would visit 4.3e9 accumulator states.
    """
    if not words:
        raise DDSRefused("closure of an empty tone set is undefined")
    if any(w <= 0 for w in words):
        raise DDSRefused(
            "a non-positive tuning word emits DC or an alias; closure "
            "is not defined for it")
    delta = synthesis_quantum(reference_hz, accumulator_bits)
    p, q = delta.numerator, delta.denominator
    g = 0
    for w in words:
        g = math.gcd(g, w)
    return Fraction(q, p * g)


def ideal_closure(targets: tuple[Fraction | int, ...]) -> Fraction:
    """Closure of the REQUESTED tones, before any quantization.

    LCM over rationals: for f_i = n_i/d_i in lowest terms, the closure
    is lcm(d_i)/gcd(n_i).
    """
    if not targets:
        raise DDSRefused("closure of an empty tone set is undefined")
    fr = [Fraction(t) for t in targets]
    if any(f <= 0 for f in fr):
        raise DDSRefused("tones must be positive")
    den = 1
    num = 0
    for f in fr:
        den = _lcm(den, f.denominator)
        num = math.gcd(num, f.numerator)
    return Fraction(den, num)


# --------------------------------------------------------------------
# Reported analysis
# --------------------------------------------------------------------

@dataclass(frozen=True)
class ClosureReport:
    reference_hz: str
    accumulator_bits: int
    policy: str
    requested_hz: tuple[str, ...]
    tuning_words: tuple[int, ...]
    realized_hz: tuple[str, ...]
    all_exact: bool
    quantum_hz: str
    ideal_closure_s: str
    quantized_closure_s: str
    closure_ratio: float
    closure_preserved: bool
    max_frequency_error_hz: str
    note: str

    def as_record(self) -> dict:
        d = asdict(self)
        for k in ("requested_hz", "realized_hz", "tuning_words"):
            d[k] = list(getattr(self, k))
        return d


def analyze(targets: tuple[Fraction | int, ...],
            reference_hz: Fraction | int,
            accumulator_bits: int = 32,
            policy: str = "ROUND") -> ClosureReport:
    """Full closure analysis for one reference-clock choice."""
    tg = tuple(Fraction(t) for t in targets)
    words = tuple(tuning_word(t, reference_hz, accumulator_bits, policy)
                  for t in tg)
    realized = tuple(realized_frequency(w, reference_hz,
                                        accumulator_bits)
                     for w in words)
    exact = all(is_exactly_representable(t, reference_hz,
                                         accumulator_bits) for t in tg)
    t_ideal = ideal_closure(tg)
    t_q = common_closure(words, reference_hz, accumulator_bits)
    err = max(abs(r - t) for r, t in zip(realized, tg))
    ratio = float(t_q / t_ideal)
    preserved = (t_q == t_ideal)

    if preserved:
        note = ("every requested tone has an exact integer tuning word, "
                "so the ideal closure survives quantization unchanged")
    else:
        note = (f"quantization stretches the common closure by a factor "
                f"of {ratio:.6g}. The cause is arithmetic, not noise: "
                f"the synthesis quantum is "
                f"{synthesis_quantum(reference_hz, accumulator_bits)} Hz "
                f"and the requested tones are not integer multiples "
                f"of it")

    return ClosureReport(
        reference_hz=str(Fraction(reference_hz)),
        accumulator_bits=accumulator_bits, policy=policy,
        requested_hz=tuple(str(t) for t in tg), tuning_words=words,
        realized_hz=tuple(str(r) for r in realized), all_exact=exact,
        quantum_hz=str(synthesis_quantum(reference_hz,
                                         accumulator_bits)),
        ideal_closure_s=str(t_ideal), quantized_closure_s=str(t_q),
        closure_ratio=ratio, closure_preserved=preserved,
        max_frequency_error_hz=str(err), note=note)


def exact_reference_exists(targets: tuple[Fraction | int, ...],
                           accumulator_bits: int = 32,
                           *, min_oversample: int = 10) -> dict:
    """Smallest *usable* dyadic reference giving every tone an exact word.

    ``min_oversample`` is not decoration. Without it this search returns
    mathematically valid nonsense: a 2 Hz reference gives 4096 Hz an
    exact tuning word, because exactness only asks that
    ``f * 2**N / f_r`` be an integer and says nothing about whether the
    synthesizer can emit the tone at all. A DDS must run its output
    well below the reference — Nyquist is the hard floor and practical
    designs keep ``f_out`` under roughly ``0.4 f_r`` for
    reconstruction. The default of 10x is a deliberately conservative
    practical bound, declared rather than assumed.
    """
    tg = [Fraction(t) for t in targets]
    if min_oversample < 2:
        raise ValueError(
            "min_oversample below 2 violates Nyquist; a DDS cannot "
            "emit a tone at or above half its reference")
    floor = max(tg) * min_oversample
    for k in range(1, 64):
        fr = Fraction(2 ** k)
        if fr < floor:
            continue
        if all(is_exactly_representable(t, fr, accumulator_bits)
               for t in tg):
            return {
                "reference_hz": 2 ** k,
                "reference_expr": f"2^{k}",
                "reference_mhz": (2 ** k) / 1e6,
                "accumulator_bits": accumulator_bits,
                "min_oversample": min_oversample,
                "oversample_achieved": float(fr / max(tg)),
                "tuning_words": [tuning_word(t, fr, accumulator_bits)
                                 for t in tg],
                "all_exact": True,
                "status": "EXACT_DYADIC_REFERENCE_EXISTS",
            }
    return {"reference_hz": None, "all_exact": False,
            "status": "NO_USABLE_DYADIC_REFERENCE_UNDER_2^63"}


def accuracy_closure_tradeoff(targets: tuple[Fraction | int, ...],
                              reference_hz: Fraction | int,
                              widths: tuple[int, ...] = (24, 32, 40, 48,
                                                         56, 64)) -> dict:
    """The paper's headline: accuracy and closure move in opposite ways.

    Widening the accumulator shrinks the synthesis quantum, so the
    realized tones land closer to the requested ones — frequency error
    falls geometrically. But the quantum's denominator ``q`` doubles
    with every bit while the tuning words stay collectively coprime,
    so ``T = q/(p * gcd K)`` grows geometrically too.

    A designer optimizing the number everyone quotes (frequency error)
    is therefore *actively destroying* the property a phase-coherent
    multi-tone instrument depends on, and the datasheet will not
    mention it.
    """
    rows = []
    for n in widths:
        rep = analyze(targets, reference_hz, n)
        rows.append({
            "accumulator_bits": n,
            "max_frequency_error_hz": float(
                Fraction(rep.max_frequency_error_hz)),
            "closure_ratio": rep.closure_ratio,
            "closure_s": float(Fraction(rep.quantized_closure_s)),
            "all_exact": rep.all_exact,
        })
    first, last = rows[0], rows[-1]
    if last["max_frequency_error_hz"] == 0:
        # An exactly-representable tone set has zero error at every
        # width, so there is no trade-off to report. This is not a
        # degenerate case to guard against -- it is the whole point:
        # a dyadic reference is immune.
        return {
            "reference_hz": str(Fraction(reference_hz)),
            "rows": rows,
            "frequency_error_improvement": None,
            "closure_degradation": 1.0,
            "anticorrelated": False,
            "conclusion": (
                "every tone is exactly representable at every width, "
                "so frequency error is identically zero and the "
                "common closure is preserved. The anti-correlation is "
                "a property of an inexact reference, not of DDS."),
        }
    err_gain = (first["max_frequency_error_hz"]
                / last["max_frequency_error_hz"])
    closure_loss = last["closure_ratio"] / first["closure_ratio"]
    span = last["accumulator_bits"] - first["accumulator_bits"]
    structural = 2.0 ** span
    return {
        "reference_hz": str(Fraction(reference_hz)),
        "rows": rows,
        "frequency_error_improvement": err_gain,
        "closure_degradation": closure_loss,
        "structural_factor": structural,
        "anticorrelated": err_gain > 1 and closure_loss > 1,
        "conclusion": (
            f"across {first['accumulator_bits']}.."
            f"{last['accumulator_bits']} bits ({span} bits) the "
            f"frequency error improves by {err_gain:.3g}x while the "
            f"common closure degrades by {closure_loss:.3g}x. "
            f"Accuracy and phase closure are anti-correlated in "
            f"accumulator width; optimizing the quoted specification "
            f"degrades the unquoted one."),
        "honesty_note": (
            f"Both effects are STRUCTURALLY 2^{span} = "
            f"{structural:.3g}. The closure figure matches it exactly "
            f"because closure scales as q ~ 2^N. The frequency-error "
            f"figure ({err_gain:.3g}) does NOT, because it is the "
            f"realized rounding error for these particular tones, "
            f"which depends on where each lands relative to the grid "
            f"and is luck. Presenting the two as independently "
            f"derived quantities that happen to nearly agree "
            f"overstates the finding: there is one mechanism, not a "
            f"coincidence between two."),
    }


def resolution_does_not_help(targets: tuple[Fraction | int, ...],
                             reference_hz: Fraction | int,
                             widths: tuple[int, ...] = (24, 32, 40, 48,
                                                        56, 64)) -> dict:
    """Corollary 1, demonstrated: widening the accumulator never fixes it.

    A decimal reference carries a factor of 5**k that no power of two
    can cancel, so exactness fails at every width. The frequency error
    shrinks; the closure does not come back.
    """
    rows = []
    for n in widths:
        rep = analyze(targets, reference_hz, n)
        rows.append({
            "accumulator_bits": n,
            "all_exact": rep.all_exact,
            "closure_preserved": rep.closure_preserved,
            "closure_ratio": rep.closure_ratio,
            "max_frequency_error_hz": rep.max_frequency_error_hz,
        })
    return {
        "reference_hz": str(Fraction(reference_hz)),
        "rows": rows,
        "any_width_exact": any(r["all_exact"] for r in rows),
        "conclusion": (
            "frequency error falls monotonically with accumulator "
            "width while exact closure is never recovered; resolution "
            "and exactness are different properties"),
    }


def degradation_factor(targets: tuple[Fraction | int, ...],
                       reference_hz: Fraction | int,
                       accumulator_bits: int = 32) -> dict:
    """Closed form for how far quantization stretches the closure.

    **Corollary.** The degradation ratio is

        T_q / T_ideal = W_fund / gcd(K_i)

    where ``W_fund`` is the *unrounded* tuning word of the ideal
    fundamental (the reciprocal of the ideal closure). Proof: with
    ``delta = p/q``, ``T_q = q/(p g)`` and ``T_ideal = 1/f_fund``, so
    the ratio is ``f_fund q/(p g) = (f_fund/delta)/g = W_fund/g``.

    This explains a near-collision that is otherwise puzzling. For the
    canonical case the ratio is ``2**36/5**8 = 175921.8604...`` while
    the tuning word for 4096 Hz is ``175922``. They are not
    coincidentally close: the ratio *is* the unrounded word, and the
    word is its rounding. Reporting the ratio as the integer 175922
    would be wrong, and wrong in the direction that looks tidier.
    """
    tg = tuple(Fraction(t) for t in targets)
    delta = synthesis_quantum(reference_hz, accumulator_bits)
    words = tuple(tuning_word(t, reference_hz, accumulator_bits)
                  for t in tg)
    g = 0
    for w in words:
        g = math.gcd(g, w)
    t_ideal = ideal_closure(tg)
    t_q = common_closure(words, reference_hz, accumulator_bits)
    f_fund = 1 / t_ideal
    w_fund = f_fund / delta
    return {
        "ratio_exact": str(t_q / t_ideal),
        "ratio_float": float(t_q / t_ideal),
        "unrounded_fundamental_word": str(w_fund),
        "gcd_tuning_words": g,
        "closed_form_matches": (t_q / t_ideal) == (w_fund / g),
        "is_integer": (t_q / t_ideal).denominator == 1,
        "note": ("the degradation ratio equals the unrounded tuning "
                 "word of the ideal fundamental, divided by the gcd "
                 "of the realized words"),
    }


# --------------------------------------------------------------------
# Two notions of closure, and where they disagree
# --------------------------------------------------------------------

def odd_part(n: int) -> int:
    """The largest odd divisor of n."""
    if n <= 0:
        raise ValueError("odd_part is defined for positive integers")
    while n % 2 == 0:
        n //= 2
    return n


def accumulator_closure(words: tuple[int, ...],
                        reference_hz: Fraction | int,
                        accumulator_bits: int) -> Fraction:
    """When the phase ACCUMULATOR returns to state zero.

    This is the quantity the DDS literature calls the grand repetition
    rate, ``GRR = 2**N / gcd(FTW, 2**N)`` for a single tone, extended
    to a tone set by taking the lcm of the per-tone recurrences.

    It is **not** the same as :func:`common_closure`, which is the
    closure of the ideal continuous phase ramp. See
    :func:`closure_discrepancy`.
    """
    if not words:
        raise DDSRefused("closure of an empty tone set is undefined")
    if any(w <= 0 for w in words):
        raise DDSRefused("non-positive tuning word")
    m = 2 ** accumulator_bits
    ticks = 1
    for w in words:
        per = m // math.gcd(w, m)
        ticks = _lcm(ticks, per)
    return Fraction(ticks) / Fraction(reference_hz)


def closure_discrepancy(words: tuple[int, ...],
                        reference_hz: Fraction | int,
                        accumulator_bits: int) -> dict:
    """Where the continuous and sampled notions of closure disagree.

    This is the substantive result of the DDS work, and it survived a
    prior-art review that found the closure formula itself already
    published (Nicholas & Samueli 1987; Hwang et al. 2017 for the
    multi-tone GCD rule; Fujifilm US12422666B2 for it on tuning words).

    The continuous formula ``T = q/(p*gcd K)`` describes the analog
    phase ramp: the instant at which every reconstructed tone has
    completed a whole number of cycles. The accumulator formula
    describes when the *digital state* returns to zero. They coincide
    only when ``gcd(K_i)`` is a power of two, and otherwise differ by
    exactly its odd part:

        T_accumulator / T_continuous = odd_part(gcd(K_i)).

    The reason is that the continuous ramp can reach 2*pi at a moment
    that falls *between* clock ticks, so the analog phase closes while
    the accumulator never lands on zero at that instant.

    Which one is physically meaningful depends on the application. A
    phase-coherent multi-tone measurement that cares about the
    reconstructed analog waveform wants the continuous figure. A
    system that latches, resets, or compares accumulator state wants
    the sampled one. Quoting the continuous figure for a system that
    depends on state recurrence overstates closure quality by the odd
    part of the gcd -- a factor of three in the worked case below, and
    unbounded in general.
    """
    t_cont = common_closure(words, reference_hz, accumulator_bits)
    t_acc = accumulator_closure(words, reference_hz, accumulator_bits)
    g = 0
    for w in words:
        g = math.gcd(g, w)
    op = odd_part(g)
    return {
        "tuning_words": list(words),
        "gcd": g,
        "odd_part_of_gcd": op,
        "continuous_closure_s": str(t_cont),
        "accumulator_closure_s": str(t_acc),
        "ratio": str(t_acc / t_cont),
        "ratio_float": float(t_acc / t_cont),
        "agree": t_acc == t_cont,
        "predicted_ratio_is_odd_part": (t_acc / t_cont) == op,
        "note": ("the two notions coincide iff gcd(K) is a power of "
                 "two; otherwise the continuous figure is optimistic "
                 "by exactly the odd part of the gcd"),
    }
