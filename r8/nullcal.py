"""P06 — adversarial null calibration.

The methods paper's engine, and its thesis in one line:

    A null result is interpretable only if the detector has been shown
    able to recover a planted signal.

That is not a new statistical idea. Injection-recovery testing is
routine in transit searches and gravitational-wave pipelines, and
surrogate-data methods have been standard since the early 1990s. What
this module contributes is a *reproducible harness* plus three worked
failure modes drawn from this programme's own history, each of which
produced a scientifically plausible answer while the inference
machinery was invalid.

The required sequence (core/02):

    1. validate the null generator
    2. inject a known signal into the statistic's target subspace
    3. verify monotonic recovery versus signal strength
    4. estimate detection power
    5. calibrate false-positive and false-negative rates
    6. freeze the analysis
    7. evaluate the real data

Step 2 carries the weight. "Into the statistic's target subspace" is
the clause that the blind-detector case failed: power was injected
into the right *degrees* but the wrong *subspace*, and the detector
could not see it at any amplitude.

Nothing here is physical data.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, asdict, field
from typing import Callable

#: Verdicts a calibration can return. A detector that fails
#: calibration produces NO usable null, which is a stronger statement
#: than "we found nothing".
CALIBRATION_VERDICTS = (
    "CALIBRATED",
    "BLIND_DETECTOR",
    "NON_MONOTONIC_RECOVERY",
    "NULL_GENERATOR_INVALID",
    "UNDERPOWERED",
)


class CalibrationRefused(RuntimeError):
    """Raised when a null is requested from an uncalibrated detector."""


# --------------------------------------------------------------------
# The harness
# --------------------------------------------------------------------

@dataclass(frozen=True)
class CalibrationResult:
    verdict: str
    strengths: tuple[float, ...]
    detection_rate: tuple[float, ...]
    monotonic: bool
    blind: bool
    false_positive_rate: float
    power_at_max: float
    min_detectable_strength: float | None
    n_trials: int
    alpha: float
    seed: int
    note: str

    @property
    def usable(self) -> bool:
        return self.verdict == "CALIBRATED"

    def as_record(self) -> dict:
        d = asdict(self)
        for k in ("strengths", "detection_rate"):
            d[k] = list(getattr(self, k))
        d["usable"] = self.usable
        return d


def calibrate(statistic: Callable[[object], float],
              null_generator: Callable[[random.Random], object],
              injector: Callable[[object, float, random.Random], object],
              *,
              strengths: tuple[float, ...] = (0.0, 0.1, 0.25, 0.5,
                                              1.0, 2.0),
              n_trials: int = 200,
              alpha: float = 0.05,
              seed: int = 20260719) -> CalibrationResult:
    """Run the full injection calibration for one detector.

    ``statistic`` maps a dataset to a scalar where larger means more
    signal. ``null_generator`` produces a dataset with no signal.
    ``injector`` adds signal of a given strength.

    The threshold is set from the null distribution at ``1 - alpha``,
    then detection rate is measured at each injected strength. A
    detector whose rate never rises above the false-positive rate is
    reported ``BLIND_DETECTOR`` and its nulls are unusable.
    """
    if 0.0 not in strengths:
        raise ValueError(
            "strengths must include 0.0 so the false-positive rate is "
            "measured on the same footing as detection")
    rng = random.Random(seed)

    # 1. null distribution and threshold
    null_stats = sorted(statistic(null_generator(rng))
                        for _ in range(n_trials))
    k = min(int(math.ceil((1 - alpha) * n_trials)), n_trials - 1)
    threshold = null_stats[k]

    # 2-3. detection rate versus injected strength
    rates = []
    for s in strengths:
        hits = 0
        for _ in range(n_trials):
            data = null_generator(rng)
            if s > 0:
                data = injector(data, s, rng)
            if statistic(data) > threshold:
                hits += 1
        rates.append(hits / n_trials)

    fpr = rates[strengths.index(0.0)]
    power = rates[-1]
    nonzero = [(s, r) for s, r in zip(strengths, rates) if s > 0]
    monotonic = all(a[1] <= b[1] + 1e-9
                    for a, b in zip(nonzero, nonzero[1:]))

    mds = next((s for s, r in nonzero if r >= 0.5), None)
    blind = power <= max(fpr, alpha) + 1e-9

    if blind:
        verdict = "BLIND_DETECTOR"
        note = (
            f"detection rate at the strongest injection ({power:.3f}) "
            f"does not exceed the false-positive rate ({fpr:.3f}). "
            f"The detector cannot see a signal it was handed, so its "
            f"nulls carry no information. A 'not significant' result "
            f"from this detector is a statement about the detector.")
    elif not monotonic:
        verdict = "NON_MONOTONIC_RECOVERY"
        note = ("detection rate does not increase monotonically with "
                "injected strength; the statistic is not measuring "
                "what the injection is adding")
    elif power < 0.5:
        verdict = "UNDERPOWERED"
        note = (f"power at the strongest injection is only "
                f"{power:.3f}; a null from this detector bounds the "
                f"signal only weakly and the bound must be quoted")
    else:
        verdict = "CALIBRATED"
        note = (f"false-positive rate {fpr:.3f} against nominal "
                f"{alpha}, power {power:.3f}, monotonic recovery, "
                f"minimum detectable strength {mds}")

    assert verdict in CALIBRATION_VERDICTS
    return CalibrationResult(
        verdict=verdict, strengths=tuple(strengths),
        detection_rate=tuple(rates), monotonic=monotonic, blind=blind,
        false_positive_rate=fpr, power_at_max=power,
        min_detectable_strength=mds, n_trials=n_trials, alpha=alpha,
        seed=seed, note=note)


def require_calibration(result: CalibrationResult) -> None:
    """Gate: refuse to interpret a null from an uncalibrated detector."""
    if not result.usable:
        raise CalibrationRefused(
            f"null is uninterpretable: calibration returned "
            f"{result.verdict}. {result.note}")


# --------------------------------------------------------------------
# Case study 1 — forced structure
# --------------------------------------------------------------------

def forced_prefix_bits(values: tuple[int, ...], width: int) -> int:
    """Leading bits pinned by the interval the values occupy.

    Computed as the common prefix of the endpoints. The naive
    ``width - span.bit_length()`` is wrong because values can straddle
    a power of two (127 and 128 span 1 and share no leading bits).
    """
    lo, hi = min(values), max(values)
    if lo == hi:
        return width
    n = 0
    for b in range(width - 1, -1, -1):
        if ((lo >> b) & 1) != ((hi >> b) & 1):
            break
        n += 1
    return n


def informative_bits(values: tuple[int, ...], width: int,
                     header_bits: int, field_bits: int) -> dict:
    """How much of an apparent shared structure is actually evidence.

    A parse that reads its constants entirely out of the forced prefix
    is reporting the interval, not the encoding.
    """
    forced = forced_prefix_bits(values, width)
    used = header_bits + field_bits
    return {
        "forced_prefix_bits": forced,
        "bits_used_by_parse": used,
        "inside_forced_region": used <= forced,
        "informative_bits": max(0, used - forced),
        "note": ("a constant read entirely from the forced prefix is "
                 "arithmetic about the values' magnitudes, not "
                 "evidence of a field layout"),
    }


def forced_structure_null(values: tuple[int, ...], width: int,
                          header_bits: int, field_bits: int, *,
                          n_draws: int = 2000,
                          seed: int = 20260719) -> dict:
    """Matched-interval null: same span, no encoding whatsoever."""
    rng = random.Random(seed)
    lo, hi = min(values), max(values)
    hits = 0
    for _ in range(n_draws):
        draw = [rng.randint(lo, hi) for _ in values]
        heads = {v >> (width - header_bits) for v in draw}
        f0 = {(v >> (width - header_bits - field_bits))
              & ((1 << field_bits) - 1) for v in draw}
        if len(heads) == 1 and len(f0) == 1:
            hits += 1
    return {"n_draws": n_draws, "seed": seed,
            "p_structure_reproduced": hits / n_draws,
            "note": ("random integers from the same interval, with no "
                     "encoding, reproducing the observed structure")}


# --------------------------------------------------------------------
# Case study 2 — circular metric / granularity mismatch
# --------------------------------------------------------------------

def granularity_mismatch_demo(*, n: int = 400,
                              seed: int = 20260719) -> dict:
    """Why a fixed-grid null makes every round-number corpus 'simple'.

    Score a rational by the bit-size of its reduced numerator and
    denominator. Draw nulls on a fixed decimal grid and every observed
    corpus of round numbers looks simpler than chance — including a
    deliberate negative control that should show nothing. Draw nulls
    that reuse each observed value's denominator and the effect
    vanishes.

    The failure is not in the statistic. It is in the null.
    """
    from fractions import Fraction
    rng = random.Random(seed)

    def score(fr: Fraction) -> float:
        return math.log2(fr.numerator) + math.log2(fr.denominator)

    # a deliberate NEGATIVE CONTROL: arbitrary round numbers with no
    # special structure at all
    observed = [Fraction(v, 1) for v in
                (440, 528, 639, 741, 852)]
    obs = sum(score(f) for f in observed) / len(observed)

    # bad null: fixed decimal grid, denominator 10**6
    bad = []
    for _ in range(n):
        vals = [Fraction(round(rng.uniform(100, 1000) * 10 ** 6),
                         10 ** 6) for _ in observed]
        bad.append(sum(score(v) for v in vals) / len(vals))
    p_bad = (sum(1 for b in bad if b <= obs) + 1) / (n + 1)

    # good null: reuse each observed member's denominator
    good = []
    for _ in range(n):
        vals = [Fraction(rng.randint(100, 1000), f.denominator)
                for f in observed]
        good.append(sum(score(v) for v in vals) / len(vals))
    p_good = (sum(1 for g in good if g <= obs) + 1) / (n + 1)

    return {
        "observed_score": obs,
        "fixed_grid_null_mean": sum(bad) / len(bad),
        "matched_granularity_null_mean": sum(good) / len(good),
        "p_fixed_grid": p_bad,
        "p_matched_granularity": p_good,
        "fixed_grid_declares_significance": p_bad < 0.05,
        "matched_declares_significance": p_good < 0.05,
        "inverted": (p_bad < 0.05) != (p_good < 0.05),
        "note": ("the corpus is a NEGATIVE CONTROL of arbitrary round "
                 "numbers. A fixed-grid null carries denominator 1e6, "
                 "whose rational complexity swamps everything, so the "
                 "control appears significant. Matching granularity "
                 "removes the artifact."),
    }


# --------------------------------------------------------------------
# Case study 3 — blind detector
# --------------------------------------------------------------------

def blind_detector_demo(*, n_trials: int = 120,
                        seed: int = 20260719) -> dict:
    """A detector that projects after destroying the target subspace.

    The good detector projects onto a fixed subspace. The blind one
    applies a dense norm-preserving scramble first, which spreads
    injected structure uniformly and leaves nothing for the projection
    to find. Both return plausible nulls on noise; only injection
    separates them.
    """
    dim = 12
    sub = 3          # the invariant subspace the signal lives in

    def gen(rng: random.Random) -> list[float]:
        return [rng.gauss(0, 1) for _ in range(dim)]

    def inject(v: list[float], s: float,
               rng: random.Random) -> list[float]:
        out = list(v)
        for i in range(sub):
            out[i] += s * 3.0
        return out

    def good(v: list[float]) -> float:
        tot = sum(x * x for x in v)
        return sum(x * x for x in v[:sub]) / tot if tot else 0.0

    def blind(v: list[float]) -> float:
        # dense scramble: every output mixes every input equally
        m = sum(v) / dim
        scrambled = [m + (x - m) * 0.0 + m * 0.0 for x in v]
        # norm-preserving-ish but structure-destroying
        nrm = math.sqrt(sum(x * x for x in v))
        scrambled = [nrm / math.sqrt(dim)] * dim
        tot = sum(x * x for x in scrambled)
        return (sum(x * x for x in scrambled[:sub]) / tot
                if tot else 0.0)

    good_cal = calibrate(good, gen, inject, n_trials=n_trials,
                         seed=seed)
    blind_cal = calibrate(blind, gen, inject, n_trials=n_trials,
                          seed=seed)
    return {
        "good_detector": good_cal.as_record(),
        "blind_detector": blind_cal.as_record(),
        "both_plausible_on_noise": True,
        "separated_only_by_injection": (good_cal.usable
                                        and blind_cal.blind),
        "note": ("both detectors return an unremarkable null on pure "
                 "noise. Only injection reveals that one of them "
                 "cannot detect a signal at any strength."),
    }


# --------------------------------------------------------------------
# The two things that survived prior art
# --------------------------------------------------------------------

def retrospective_information(bits_used: int, bits_forced: int) -> dict:
    """Informative content of a retrospective parse, stated generally.

        I = max(0, bits_used - bits_forced)

    where ``bits_forced`` is the number of bits determined by the
    constraints of the admissible set, and ``bits_used`` is the number
    the proposed structure reads. A parse whose constants come
    entirely out of the forced region has ``I = 0``: it restates the
    constraint.

    The prior-art review found the general *principle* — that a null
    must preserve the constraints of the observed data — thoroughly
    established (Efron 1971 on Bode's law; McKay et al. 1999 on the
    Bible code; Diaconis & Mosteller 1989 on coincidences). It did
    NOT find this bits-accounting form published, so this is offered
    as a sharper statement of a known theorem rather than a new one.
    """
    if bits_used < 0 or bits_forced < 0:
        raise ValueError("bit counts must be non-negative")
    info = max(0, bits_used - bits_forced)
    return {
        "bits_used": bits_used,
        "bits_forced": bits_forced,
        "informative_bits": info,
        "carries_evidence": info > 0,
        "interpretation": (
            "the structure restates the constraint and discriminates "
            "nothing" if info == 0 else
            f"{info} bits lie outside the forced region and are worth "
            f"a prospective test"),
        "prior_art": (
            "sharper form of an established principle; see Efron "
            "(1971), McKay et al. (1999), Diaconis & Mosteller (1989)"),
    }


def negative_control_signature(control_p: float, observed_p: float,
                               alpha: float = 0.05) -> dict:
    """The self-diagnosing failure: a negative control scoring well.

    If a corpus known to contain no effect scores significant under
    the same analysis, the analysis is broken — regardless of what the
    real corpus does. This is stronger than a suspicion, because it
    needs no knowledge of the true effect.

    The prior-art review could not find this presented as a general
    diagnostic, and it is the most portable thing in the methods
    paper: any pipeline can run it, and its failure is unambiguous.
    """
    broken = control_p < alpha
    return {
        "negative_control_p": control_p,
        "observed_p": observed_p,
        "alpha": alpha,
        "analysis_is_broken": broken,
        "verdict": (
            "NULL_INVALID: a negative control reached significance, so "
            "the observed result carries no information whatever it is"
            if broken else
            "negative control behaves; the analysis passes this check"),
        "note": ("this check requires no knowledge of the true effect "
                 "size and its failure is unambiguous"),
    }


#: The reusable artifact the review recommended: three questions to
#: answer BEFORE believing any null.
PREFLIGHT_CHECKS = (
    ("NULL_MATCHED",
     "Is the null matched on every property the metric is sensitive "
     "to -- not merely on magnitude?",
     "granularity_mismatch_demo"),
    ("STRUCTURE_NOT_FORCED",
     "Is the observed structure forced by a constraint of the "
     "admissible set?",
     "retrospective_information"),
    ("DETECTOR_RECOVERS",
     "Has the detector recovered a planted signal at known strength, "
     "with monotonic response?",
     "calibrate"),
)


def preflight(null_matched: bool, structure_not_forced: bool,
              detector_recovers: bool) -> dict:
    """Run the three-question pre-flight and report what a null is worth."""
    answers = {
        "NULL_MATCHED": null_matched,
        "STRUCTURE_NOT_FORCED": structure_not_forced,
        "DETECTOR_RECOVERS": detector_recovers,
    }
    failed = [k for k, v in answers.items() if not v]
    return {
        "answers": answers,
        "failed": failed,
        "null_is_interpretable": not failed,
        "verdict": ("null may be interpreted" if not failed else
                    f"null is uninterpretable: {', '.join(failed)}"),
        "lineage": (
            "this is the positive-control principle, and formally a "
            "severity requirement (Mayo & Spanos 2011): a test that "
            "could not have detected a discrepancy provides no "
            "evidence against it. The principle is old and has been "
            "independently renamed in astronomy (injection-recovery), "
            "particle physics (blind analysis), biology (positive "
            "control) and machine learning (sanity checks). It is not "
            "claimed as novel here."),
    }
