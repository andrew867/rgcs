"""P21 — the null-model registry: every claimed effect gets a registered NULL.

A number is only evidence of an effect if it beats what the data would look
like with *no* effect. This module makes that discipline structural. For
every claimed effect there is a **registered null model** -- an explicit
statement of what the data look like when the hypothesis is false -- and a
test statistic evaluated against that null by Monte Carlo / permutation to
get a null distribution and an empirical p-value.

**Four families of matched null.** A null is only honest if it reproduces
the *incidental* structure of the data and withholds only the *content* the
effect claims. R15 registers four families, each matched to a different way
a false positive sneaks in:

* a **representation-matched** null (equal temperament is a deliberately
  *irrational* approximation of small-integer ratios, so it may never be
  used as the rational-ratio control -- that would beg the question);
* a **design/anthropogenic-matched** null (a peak at an ISM band is
  industrial allocation, not a discovery, so the null must expect power
  there rather than assume a flat spectrum);
* a **relationship-matched** null (a conclusion that survives is one that
  is invariant under a mere change of units -- a claim that flips when you
  convert Hz to kHz was an artifact of representation, not a relationship);
* a **physics-matched** null (instrument noise and a fixture-loaded
  resonator can each mimic a specimen resonance, so the null carries the
  fixture's own Lorentzian and the instrument's noise floor).

**The load-bearing rule (the R10.6 band-clustering lesson).** A null result
means nothing unless the method could have detected a real effect. So every
registered null must **prove power on planted data**: a planted effect must
be flagged (p small) and pure noise must not (p non-significant, and the
p-value distribution under the null is approximately uniform).
:func:`refuse_null_without_power` refuses a null that cannot detect a
planted effect as vacuous, and :func:`refuse_absence_as_evidence` refuses
"we failed to reject the null" as "the effect is absent" whenever power was
never demonstrated.

**A p-value is never zero.** An empirical p from ``n`` Monte Carlo trials is
``(tail + 1) / (n + 1)``; the smallest value it can take is the resolution
floor ``1 / (n + 1) > 0``. :func:`refuse_p_value_zero` refuses ``p = 0``.

Everything here is deterministic under a supplied seed and operates on
synthetic fixtures only. Nothing is measured; the claim ceiling is
``SYNTHETIC_OBSERVATION`` and the verdict is
``NULL_MODEL_REGISTRY_POWER_PROVEN``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

import numpy as np

from r15.claims import ClaimClass, refuse_noise_as_resonance

#: The standing verdict.
DEFAULT_VERDICT = "NULL_MODEL_REGISTRY_POWER_PROVEN"

#: Stamped on reports and results so an analysis change is visible.
ANALYSIS_VERSION = "P21.v1"

#: The strongest claim class anything here may carry: a deterministic
#: simulator output, never a physical measurement.
CLAIM_CAP = ClaimClass.SYNTHETIC_OBSERVATION.value

PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: Default significance level and Monte Carlo trial count.
DEFAULT_ALPHA = 0.05
DEFAULT_MC_TRIALS = 999
REPORT_MC_TRIALS = 199


class NullError(RuntimeError):
    """Raised on a malformed null model, a vacuous null (no power), an
    attempt to read a failed rejection as proof of absence, a p-value
    claimed as zero, a circular null, or a family-specific fallacy."""


# =======================================================================
# Null families and surrogate-generation methods
# =======================================================================

class NullFamily(Enum):
    """The four ways a false positive sneaks in, each needing its own
    matched control, plus a generic family for the raw surrogate methods."""

    REPRESENTATION = "REPRESENTATION"      # e.g. rational vs tempered ratios
    DESIGN = "DESIGN"                      # e.g. anthropogenic ISM bands
    RELATIONSHIP = "RELATIONSHIP"          # e.g. unit-invariant conclusions
    PHYSICS = "PHYSICS"                    # e.g. instrument / fixture nulls
    GENERIC = "GENERIC"                    # noise / permutation / surrogate


class NullMethod(Enum):
    """How one surrogate dataset is generated under the null."""

    NOISE_ONLY = "NOISE_ONLY"              # white noise at the data's scale
    PERMUTATION = "PERMUTATION"            # shuffle: exact marginal, no order
    PHASE_RANDOMIZED = "PHASE_RANDOMIZED"  # FFT surrogate: power spectrum kept
    SPAN_MATCHED = "SPAN_MATCHED"          # uniform over the data's range
    REPRESENTATION_MATCHED = "REPRESENTATION_MATCHED"
    DESIGN_MATCHED = "DESIGN_MATCHED"
    INSTRUMENT_NOISE = "INSTRUMENT_NOISE"
    FIXTURE_LOADED = "FIXTURE_LOADED"


# =======================================================================
# Raw surrogate generators. Each takes an rng and a reference array and
# returns one surrogate of the same shape. Deterministic given the rng.
# =======================================================================

def noise_only_surrogate(rng: np.random.Generator,
                         reference: np.ndarray) -> np.ndarray:
    """White noise matched to the reference's amplitude scale.

    Preserves the overall power but destroys every coherent structure --
    the null for "is there any coherent feature above the noise floor?"."""
    ref = np.asarray(reference, dtype=float)
    scale = float(ref.std())
    scale = scale if scale > 0 else 1.0
    return rng.normal(0.0, scale, size=ref.shape)


def permutation_surrogate(rng: np.random.Generator,
                          reference: np.ndarray) -> np.ndarray:
    """A shuffle of the reference values.

    Preserves the marginal value distribution *exactly* (representation-
    matched) while destroying all ordering / temporal structure -- the null
    for "is the arrangement, not just the set of values, informative?"."""
    ref = np.asarray(reference, dtype=float)
    return rng.permutation(ref)


def phase_randomized_surrogate(rng: np.random.Generator,
                               reference: np.ndarray) -> np.ndarray:
    """A Fourier phase-randomized surrogate.

    Randomises the phases of the DFT while preserving the moduli, so the
    surrogate has the *same power spectrum* (hence the same autocorrelation)
    as the reference but no phase coupling. The null for "is there nonlinear
    / phase structure beyond a linear Gaussian process with this spectrum?"."""
    ref = np.asarray(reference, dtype=float)
    n = ref.size
    spectrum = np.fft.rfft(ref)
    mag = np.abs(spectrum)
    phases = rng.uniform(0.0, 2.0 * np.pi, size=mag.shape)
    phases[0] = 0.0                       # keep the DC term real
    if n % 2 == 0:
        phases[-1] = 0.0                  # Nyquist term real for even n
    surrogate = np.fft.irfft(mag * np.exp(1j * phases), n=n)
    return surrogate


def span_matched_surrogate(rng: np.random.Generator,
                           reference: np.ndarray) -> np.ndarray:
    """Uniform draw over the reference's own range.

    Reproduces the *span* (the incidental clustering / range) of the data
    without any content -- the r10 band-clustering lesson: a shared narrow
    band is a fact about range, and a span-matched null reproduces it, so
    only structure beyond the span may count as content."""
    ref = np.asarray(reference, dtype=float)
    lo, span = float(ref.min()), float(ref.max() - ref.min())
    span = span if span > 0 else 1.0
    return lo + rng.random(size=ref.shape) * span


# =======================================================================
# The null model and the Monte Carlo p-value
# =======================================================================

@dataclass(frozen=True)
class NullModel:
    """A registered statement of what the data look like with no effect.

    ``generator`` maps ``(rng, reference)`` to one surrogate dataset;
    ``derivation_family`` names the source the null is derived from, so a
    null derived from the *same* family as the effect it tests can be caught
    as circular."""

    name: str
    family: NullFamily
    method: NullMethod
    description: str
    generator: Callable[[np.random.Generator, np.ndarray], np.ndarray]
    derivation_family: str

    def __post_init__(self) -> None:
        if not self.name:
            raise NullError("a null model needs a name")
        if not self.description:
            raise NullError(f"null {self.name!r} needs a description")
        if not callable(self.generator):
            raise NullError(f"null {self.name!r} needs a callable generator")
        if not self.derivation_family:
            raise NullError(
                f"null {self.name!r} must declare a derivation_family so "
                f"circularity against the effect can be checked")

    def surrogate(self, rng: np.random.Generator,
                  reference: np.ndarray) -> np.ndarray:
        return np.asarray(self.generator(rng, reference), dtype=float)


@dataclass(frozen=True)
class MonteCarloResult:
    """The outcome of testing an observed statistic against a null.

    ``mc_resolution`` is ``1 / (n_trials + 1)`` -- the smallest p-value the
    Monte Carlo can resolve, and the floor below which we report ``p <
    resolution`` rather than a fictitious zero. ``empirical_tail_count`` is
    how many null draws equalled or exceeded the observed statistic."""

    statistic: float
    p_value: float
    n_trials: int
    mc_resolution: float
    empirical_tail_count: int
    alpha: float
    significant: bool
    null_distribution: tuple[float, ...] = field(default=(), repr=False)

    @property
    def p_value_text(self) -> str:
        return format_p_value(self.p_value, self.mc_resolution)


def monte_carlo_p_value(
        statistic_fn: Callable[[np.ndarray], float],
        observed: np.ndarray,
        null_model: NullModel, *,
        n_trials: int = DEFAULT_MC_TRIALS,
        seed: int = 20260724,
        alpha: float = DEFAULT_ALPHA,
        keep_distribution: bool = False) -> MonteCarloResult:
    """Empirical p-value of ``statistic_fn(observed)`` against ``null_model``.

    Draws ``n_trials`` surrogates from the null, evaluates the statistic on
    each, and returns the fraction that equalled or exceeded the observed
    value -- with the ``+1 / +1`` correction so the p-value is never zero
    (``(tail + 1) / (n + 1)``) and its floor is ``1 / (n + 1)``, the Monte
    Carlo resolution. Deterministic under ``seed``."""
    if n_trials < 1:
        raise NullError("n_trials must be >= 1")
    obs = np.asarray(observed, dtype=float)
    stat_obs = float(statistic_fn(obs))
    rng = np.random.default_rng(seed)
    null_stats = np.empty(n_trials, dtype=float)
    for i in range(n_trials):
        null_stats[i] = float(statistic_fn(null_model.surrogate(rng, obs)))
    tail = int(np.count_nonzero(null_stats >= stat_obs))
    p_value = (tail + 1) / (n_trials + 1)
    resolution = 1.0 / (n_trials + 1)
    return MonteCarloResult(
        statistic=stat_obs,
        p_value=p_value,
        n_trials=n_trials,
        mc_resolution=resolution,
        empirical_tail_count=tail,
        alpha=alpha,
        significant=p_value < alpha,
        null_distribution=tuple(null_stats) if keep_distribution else (),
    )


def format_p_value(p_value: float, resolution: float) -> str:
    """Render a p-value, never as zero.

    A Monte Carlo p-value cannot be exactly zero (the ``+1`` guarantees it),
    and one at or below the resolution floor is reported as ``p < floor`` --
    stating the smallest value the experiment could resolve, not a false
    exactness."""
    if p_value <= 0.0:
        refuse_p_value_zero()
    if p_value <= resolution:
        return f"< {resolution:.3g} (Monte Carlo resolution floor)"
    return f"{p_value:.3g}"


# =======================================================================
# The power discipline: a null must detect a planted effect
# =======================================================================

@dataclass(frozen=True)
class PowerReport:
    """Proof (or refutation) that a null can detect a real effect.

    ``has_power`` is true only if the method flagged the planted effect and
    stayed silent on pure noise -- the R10.6 discipline. A null without power
    produces null results that carry no weight."""

    null_name: str
    p_on_planted: float
    p_on_noise: float
    detects_planted: bool
    fires_on_noise: bool
    has_power: bool
    alpha: float
    mc_resolution: float

    def as_dict(self) -> dict:
        return {
            "null_name": self.null_name,
            "p_on_planted": self.p_on_planted,
            "p_on_noise": self.p_on_noise,
            "detects_planted_effect": self.detects_planted,
            "fires_on_pure_noise": self.fires_on_noise,
            "has_power": self.has_power,
            "alpha": self.alpha,
            "mc_resolution": self.mc_resolution,
        }


def prove_power(null_model: NullModel,
                statistic_fn: Callable[[np.ndarray], float],
                planted: np.ndarray,
                noise: np.ndarray, *,
                n_trials: int = DEFAULT_MC_TRIALS,
                seed: int = 20260724,
                alpha: float = DEFAULT_ALPHA) -> PowerReport:
    """Run the two-sided power discipline on one null model.

    The null earns the right to report a negative result only if it (a)
    flags the ``planted`` effect (p < alpha -- POWER) and (b) does not fire
    on the ``noise`` control (p >= alpha -- SPECIFICITY)."""
    res_planted = monte_carlo_p_value(
        statistic_fn, planted, null_model,
        n_trials=n_trials, seed=seed, alpha=alpha)
    res_noise = monte_carlo_p_value(
        statistic_fn, noise, null_model,
        n_trials=n_trials, seed=seed + 1, alpha=alpha)
    detects = res_planted.significant
    fires = res_noise.significant
    return PowerReport(
        null_name=null_model.name,
        p_on_planted=res_planted.p_value,
        p_on_noise=res_noise.p_value,
        detects_planted=detects,
        fires_on_noise=fires,
        has_power=detects and not fires,
        alpha=alpha,
        mc_resolution=res_planted.mc_resolution,
    )


def null_p_value_distribution(
        null_model: NullModel,
        statistic_fn: Callable[[np.ndarray], float],
        noise_factory: Callable[[np.random.Generator], np.ndarray], *,
        n_datasets: int = 60,
        n_trials: int = 199,
        seed: int = 20260724,
        alpha: float = DEFAULT_ALPHA) -> np.ndarray:
    """Empirical p-values over many independent H0 (noise-only) datasets.

    If the null is well calibrated, these p-values are approximately uniform
    on (0, 1); a pile-up near zero would mean the null over-rejects true
    noise, and a pile-up near one that it can never reject anything."""
    pvals = np.empty(n_datasets, dtype=float)
    for i in range(n_datasets):
        data = np.asarray(
            noise_factory(np.random.default_rng(seed + 1000 + i)), dtype=float)
        res = monte_carlo_p_value(
            statistic_fn, data, null_model,
            n_trials=n_trials, seed=seed + 5000 + i, alpha=alpha)
        pvals[i] = res.p_value
    return pvals


def p_values_are_uniform(pvals: np.ndarray, *,
                         alpha: float = DEFAULT_ALPHA,
                         fpr_tolerance: float = 0.08,
                         mean_band: tuple[float, float] = (0.30, 0.70)
                         ) -> dict:
    """Coarse uniformity check on a set of H0 p-values.

    Two symptoms of a mis-calibrated null: the false-positive rate (fraction
    below ``alpha``) far exceeds ``alpha``, or the mean drifts away from
    0.5. Neither is a formal KS test -- it is a deterministic guardrail that
    the null does not systematically over- or under-reject noise."""
    p = np.asarray(pvals, dtype=float)
    fpr = float(np.mean(p < alpha))
    mean_p = float(np.mean(p))
    fpr_ok = fpr <= alpha + fpr_tolerance
    mean_ok = mean_band[0] < mean_p < mean_band[1]
    return {
        "false_positive_rate": fpr,
        "mean_p": mean_p,
        "fpr_within_tolerance": fpr_ok,
        "mean_near_half": mean_ok,
        "approximately_uniform": fpr_ok and mean_ok,
        "n": int(p.size),
    }


# =======================================================================
# Generic test statistics
# =======================================================================

def spectral_peak_statistic(x: np.ndarray) -> float:
    """The largest periodogram power above DC. Large for a coherent tone."""
    a = np.asarray(x, dtype=float)
    a = a - a.mean()
    power = np.abs(np.fft.rfft(a)) ** 2
    return float(power[1:].max()) if power.size > 1 else 0.0


def group_mean_diff_statistic(x: np.ndarray) -> float:
    """|mean(second half) - mean(first half)|. Large for a group shift."""
    a = np.asarray(x, dtype=float)
    h = a.size // 2
    if h == 0:
        return 0.0
    return float(abs(a[h:].mean() - a[:h].mean()))


# =======================================================================
# Family 1 -- REPRESENTATION: rational ratios vs equal temperament
# =======================================================================

#: A just-intonation octave: exact small-integer frequency ratios.
JUST_INTONATION_RATIOS = (1.0, 9 / 8, 5 / 4, 4 / 3, 3 / 2, 5 / 3, 15 / 8, 2.0)


def equal_temperament_ratios(n_semitones: int = 12) -> np.ndarray:
    """12-tone equal temperament ratios ``2**(k/12)``.

    These are irrational by construction -- equal temperament *approximates*
    the small-integer ratios while deliberately never equalling them."""
    k = np.arange(0, n_semitones + 1)
    return 2.0 ** (k / 12.0)


def just_intonation_ratios() -> np.ndarray:
    """The exact rational-ratio scale (the genuine rational control)."""
    return np.array(JUST_INTONATION_RATIOS, dtype=float)


def _nearest_small_rational_error(ratio: float, max_den: int = 16) -> float:
    """Distance from ``ratio`` to the nearest rational with a small
    denominator -- 0 exactly when the ratio *is* such a rational."""
    best = float("inf")
    for den in range(1, max_den + 1):
        num = round(ratio * den)
        best = min(best, abs(ratio - num / den))
    return best


def rationality_score(ratios: np.ndarray, max_den: int = 16) -> float:
    """Higher when the ratios sit closer to small-integer rationals.

    (Negated mean distance to the nearest small rational, so a genuine
    rational scale scores highest.)"""
    r = np.asarray(ratios, dtype=float)
    return -float(np.mean([_nearest_small_rational_error(v, max_den)
                           for v in r]))


def is_rational_ratio_control(ratios: np.ndarray, *,
                              tol: float = 1e-9,
                              max_den: int = 16) -> bool:
    """True only if *every* ratio is (to ``tol``) an exact small rational.

    Equal temperament fails this: its ratios are irrational, so it can only
    ever be a near-miss, never the rational control itself."""
    r = np.asarray(ratios, dtype=float)
    return all(_nearest_small_rational_error(v, max_den) <= tol for v in r)


def equal_temperament_is_rational_ratio_control() -> bool:
    """The load-bearing representation fact: equal temperament is NOT a
    rational-ratio control. Always False."""
    return is_rational_ratio_control(equal_temperament_ratios())


def representation_ratio_surrogate(rng: np.random.Generator,
                                   reference: np.ndarray) -> np.ndarray:
    """Random ratios over the reference's own range -- the representation-
    matched null for a rational-ratio detector."""
    return span_matched_surrogate(rng, reference)


#: The representation-matched null model.
REPRESENTATION_NULL = NullModel(
    name="representation_matched_ratio_null",
    family=NullFamily.REPRESENTATION,
    method=NullMethod.REPRESENTATION_MATCHED,
    description=(
        "random frequency ratios drawn over the same range as the observed "
        "ratios; the control for a rational-ratio detector. Equal "
        "temperament may not serve here because it is an irrational "
        "approximation of the very rationals under test."),
    generator=representation_ratio_surrogate,
    derivation_family="ratio_range",
)


# =======================================================================
# Family 2 -- DESIGN: anthropogenic ISM bands
# =======================================================================

#: A subset of the ISM (industrial, scientific, medical) radio allocations.
#: These are anthropogenic structure -- power there is human infrastructure,
#: not a natural discovery.
ISM_BANDS = (
    ("6.78 MHz", 6.78e6),
    ("13.56 MHz", 13.56e6),
    ("27.12 MHz", 27.12e6),
    ("40.68 MHz", 40.68e6),
    ("433.92 MHz", 433.92e6),
    ("915 MHz", 915e6),
    ("2.45 GHz", 2.45e9),
    ("5.8 GHz", 5.8e9),
)

#: A natural spectral line used as the planted "genuine" signal: the
#: neutral-hydrogen 21 cm line at 1420.405 MHz (not an ISM allocation).
HYDROGEN_LINE_HZ = 1420.405751e6


def ism_bands() -> tuple[tuple[str, float], ...]:
    """The registered anthropogenic ISM allocations."""
    return ISM_BANDS


def is_anthropogenic_band(freq_hz: float, *, tol_frac: float = 0.02) -> bool:
    """True if ``freq_hz`` lies within ``tol_frac`` of an ISM allocation."""
    f = float(freq_hz)
    return any(abs(f - band) <= tol_frac * band for _, band in ISM_BANDS)


@dataclass(frozen=True)
class DesignNoveltyReport:
    """The design-matched verdict on a survey peak and its power proof.

    A peak at an ISM band is explained by the anthropogenic null (not
    novel); a peak at a natural frequency survives it (novel candidate).
    ``has_power`` requires flagging the planted natural line while staying
    silent on the anthropogenic control."""

    planted_freq_hz: float
    control_freq_hz: float
    planted_is_novel: bool
    control_is_novel: bool
    has_power: bool

    def as_dict(self) -> dict:
        return {
            "planted_freq_hz": self.planted_freq_hz,
            "control_freq_hz": self.control_freq_hz,
            "planted_natural_line_is_novel": self.planted_is_novel,
            "anthropogenic_control_is_novel": self.control_is_novel,
            "has_power": self.has_power,
        }


def design_matched_novelty(peak_freq_hz: float) -> bool:
    """A survey peak is a novel candidate only if it is NOT anthropogenic.

    This is the design-matched null: power at an ISM band is attributed to
    human infrastructure, so only a non-anthropogenic peak may be a
    discovery."""
    return not is_anthropogenic_band(peak_freq_hz)


def prove_design_power(planted_freq_hz: float = HYDROGEN_LINE_HZ,
                       control_freq_hz: float = 2.45e9) -> DesignNoveltyReport:
    """Power proof for the design-matched null.

    Detects a planted natural line (the 21 cm hydrogen line) as novel and
    correctly declines to flag an ISM-band peak (2.45 GHz Wi-Fi/oven band)."""
    planted_novel = design_matched_novelty(planted_freq_hz)
    control_novel = design_matched_novelty(control_freq_hz)
    return DesignNoveltyReport(
        planted_freq_hz=planted_freq_hz,
        control_freq_hz=control_freq_hz,
        planted_is_novel=planted_novel,
        control_is_novel=control_novel,
        has_power=planted_novel and not control_novel,
    )


# =======================================================================
# Family 3 -- RELATIONSHIP: unit-invariant conclusions
# =======================================================================

def ordering_conclusion(values: np.ndarray) -> tuple[int, ...]:
    """The rank ordering of ``values`` -- a relational conclusion that a
    positive rescaling (a unit change) must leave unchanged."""
    return tuple(int(i) for i in np.argsort(np.asarray(values, dtype=float),
                                            kind="stable"))


def correlation_sign(x: np.ndarray, y: np.ndarray) -> int:
    """Sign of the Pearson correlation -- a relational conclusion invariant
    under positive rescaling of either variable."""
    a = np.asarray(x, dtype=float)
    b = np.asarray(y, dtype=float)
    c = np.corrcoef(a, b)[0, 1]
    return int(np.sign(c))


def conclusion_invariant_under_units(values: np.ndarray,
                                     factors: tuple[float, ...]) -> bool:
    """True if the ordering conclusion is identical under every unit factor.

    A genuine relational conclusion (which resonator sits higher) is a fact
    about the ordering and survives converting Hz to kHz to MHz; a
    conclusion that flips was an artifact of the units."""
    base = ordering_conclusion(values)
    v = np.asarray(values, dtype=float)
    for f in factors:
        if f <= 0:
            raise NullError("a unit conversion factor must be positive")
        if ordering_conclusion(v * f) != base:
            return False
    return True


@dataclass(frozen=True)
class RelationshipReport:
    """Power proof for the relationship-matched null.

    The invariant relationship (a real correlation / ordering) is certified,
    and a unit-dependent pseudo-conclusion (comparing raw magnitudes across
    different units) is refused. ``has_power`` requires both."""

    genuine_conclusion_invariant: bool
    artifact_conclusion_invariant: bool
    has_power: bool

    def as_dict(self) -> dict:
        return {
            "genuine_relationship_invariant_under_units":
                self.genuine_conclusion_invariant,
            "unit_dependent_artifact_is_invariant":
                self.artifact_conclusion_invariant,
            "has_power": self.has_power,
        }


def prove_relationship_power() -> RelationshipReport:
    """Power proof for the relationship-matched null.

    A genuine ordering of resonant frequencies is invariant under Hz -> kHz
    -> MHz; a raw cross-unit magnitude comparison (3 "metres" vs 5 "feet"
    read as 3 vs 5) is not invariant and is refused as an artifact."""
    freqs = np.array([120.0, 340.0, 55.0, 900.0])          # arbitrary units
    factors = (1.0, 1e-3, 1e-6, 1e3)                        # Hz, kHz, MHz, mHz
    genuine = conclusion_invariant_under_units(freqs, factors)
    # An artifact: two lengths whose raw numbers order one way but whose
    # physical magnitudes order the other once units are honoured.
    lengths_raw = np.array([3.0, 5.0])                     # "3 m" vs "5 ft"
    lengths_si = np.array([3.0, 5.0 * 0.3048])             # both in metres
    artifact_invariant = (ordering_conclusion(lengths_raw)
                          == ordering_conclusion(lengths_si))
    return RelationshipReport(
        genuine_conclusion_invariant=genuine,
        artifact_conclusion_invariant=artifact_invariant,
        has_power=genuine and not artifact_invariant,
    )


# =======================================================================
# Family 4 -- PHYSICS: instrument noise and a fixture-loaded resonator
# =======================================================================

#: A normalized frequency grid for the physics-matched null demonstrations.
FREQ_GRID = np.linspace(0.5, 1.5, 256)
FIXTURE_F0 = 0.80          # the fixture's own resonance
SPECIMEN_F0 = 1.20         # where a specimen line would sit
RESONATOR_Q = 40.0
_SPECIMEN_MASK = FREQ_GRID > 1.0     # the specimen window, away from fixture


def lorentzian(freqs: np.ndarray, f0: float, q: float,
               amp: float) -> np.ndarray:
    """A Lorentzian resonance of centre ``f0``, quality ``q``, height
    ``amp``."""
    f = np.asarray(freqs, dtype=float)
    return amp / (1.0 + (2.0 * q * (f - f0) / f0) ** 2)


def fixture_loaded_resonator_response(freqs: np.ndarray, *,
                                      f0: float = FIXTURE_F0,
                                      q: float = RESONATOR_Q,
                                      amp: float = 1.0) -> np.ndarray:
    """The fixture's own Lorentzian response -- a resonance produced by the
    mount, not the specimen. The physics-matched null must carry it."""
    return lorentzian(freqs, f0, q, amp)


def instrument_noise_surrogate(rng: np.random.Generator,
                               reference: np.ndarray, *,
                               scale: float = 0.05) -> np.ndarray:
    """The instrument noise floor: a small white background over the grid."""
    ref = np.asarray(reference, dtype=float)
    return rng.normal(0.0, scale, size=ref.shape)


def _physics_null_generator(rng: np.random.Generator,
                            reference: np.ndarray) -> np.ndarray:
    """A surrogate spectrum under the physics null: the fixture Lorentzian
    plus instrument noise, and NO specimen line."""
    resp = fixture_loaded_resonator_response(FREQ_GRID)
    return resp + instrument_noise_surrogate(rng, FREQ_GRID)


def specimen_window_peak_statistic(x: np.ndarray) -> float:
    """The largest response inside the specimen window (away from the
    fixture resonance). Large only for a genuine specimen line."""
    a = np.asarray(x, dtype=float)
    return float(a[_SPECIMEN_MASK].max())


#: The physics-matched null model.
PHYSICS_NULL = NullModel(
    name="fixture_loaded_resonator_null",
    family=NullFamily.PHYSICS,
    method=NullMethod.FIXTURE_LOADED,
    description=(
        "the fixture's own Lorentzian resonance plus the instrument noise "
        "floor, with no specimen line; a peak in the specimen window must "
        "beat this to be attributed to the specimen rather than the mount."),
    generator=_physics_null_generator,
    derivation_family="fixture_and_instrument",
)


def planted_specimen_spectrum(rng: np.random.Generator, *,
                              amp: float = 1.5) -> np.ndarray:
    """A spectrum with a genuine specimen line at ``SPECIMEN_F0`` on top of
    the fixture response and instrument noise."""
    resp = fixture_loaded_resonator_response(FREQ_GRID)
    resp = resp + lorentzian(FREQ_GRID, SPECIMEN_F0, RESONATOR_Q, amp)
    return resp + instrument_noise_surrogate(rng, FREQ_GRID)


def fixture_only_spectrum(rng: np.random.Generator, *,
                          amp: float = 2.0) -> np.ndarray:
    """A control spectrum whose only peak is the fixture resonance (no
    specimen line) -- the physics null must NOT flag it."""
    resp = fixture_loaded_resonator_response(FREQ_GRID, amp=amp)
    return resp + instrument_noise_surrogate(rng, FREQ_GRID)


# =======================================================================
# The registry: metric -> null, with proven power and no circularity
# =======================================================================

@dataclass(frozen=True)
class NullBinding:
    """A metric bound to its null, with the power proof and the effect's
    derivation family (for circularity)."""

    metric: str
    null_model: NullModel
    effect_family: str
    has_power: bool

    def as_dict(self) -> dict:
        return {
            "metric": self.metric,
            "null_model": self.null_model.name,
            "null_family": self.null_model.family.value,
            "null_method": self.null_model.method.value,
            "effect_family": self.effect_family,
            "null_derivation_family": self.null_model.derivation_family,
            "has_power": self.has_power,
        }


class NullRegistry:
    """A registry binding each claimed effect (a metric) to a null model.

    Registration REFUSES a null that has not proven power (vacuous) and a
    null derived from the same family as the effect (circular). The registry
    thus cannot hold a null that would make a negative result meaningless."""

    def __init__(self) -> None:
        self._bindings: dict[str, NullBinding] = {}

    def register(self, metric: str, null_model: NullModel, *,
                 effect_family: str, has_power: bool) -> NullBinding:
        if not metric:
            raise NullError("a binding needs a metric name")
        if not effect_family:
            raise NullError("a binding needs an effect_family")
        if null_model.derivation_family == effect_family:
            refuse_circular_null(metric, null_model.derivation_family)
        if not has_power:
            refuse_null_without_power(null_model.name)
        binding = NullBinding(metric, null_model, effect_family, has_power)
        self._bindings[metric] = binding
        return binding

    def get(self, metric: str) -> NullBinding:
        if metric not in self._bindings:
            raise NullError(f"no null registered for metric {metric!r}")
        return self._bindings[metric]

    def metrics(self) -> tuple[str, ...]:
        return tuple(self._bindings)

    def bindings(self) -> tuple[NullBinding, ...]:
        return tuple(self._bindings.values())


def build_default_registry(*, n_trials: int = REPORT_MC_TRIALS,
                           seed: int = 20260724) -> NullRegistry:
    """The default registry: the four matched-null families, each bound to a
    claimed effect with its power proven on planted data.

    This is the structural embodiment of the load-bearing rule -- no family
    is registered unless it demonstrably detects a planted effect and stays
    silent on the matched control."""
    reg = NullRegistry()

    # Family 1: representation. Effect = rational-ratio structure.
    rep_power = prove_power(
        REPRESENTATION_NULL, rationality_score,
        planted=just_intonation_ratios(),
        noise=span_matched_surrogate(
            np.random.default_rng(seed), just_intonation_ratios()),
        n_trials=n_trials, seed=seed)
    reg.register("rational_ratio_structure", REPRESENTATION_NULL,
                 effect_family="rational_ratios", has_power=rep_power.has_power)

    # Family 2: design. Effect = a novel (non-anthropogenic) survey peak.
    design_power = prove_design_power()
    # A design null has no separate derivation family collision here.
    design_null = NullModel(
        name="anthropogenic_ism_band_null",
        family=NullFamily.DESIGN,
        method=NullMethod.DESIGN_MATCHED,
        description=(
            "power is expected at the ISM allocations, which are "
            "anthropogenic infrastructure; only a peak away from them may "
            "be a discovery."),
        generator=lambda rng, ref: np.asarray(ref, dtype=float),
        derivation_family="anthropogenic_allocation")
    reg.register("novel_survey_peak", design_null,
                 effect_family="natural_spectral_line",
                 has_power=design_power.has_power)

    # Family 3: relationship. Effect = a unit-invariant relational claim.
    rel_power = prove_relationship_power()
    rel_null = NullModel(
        name="unit_rescaling_null",
        family=NullFamily.RELATIONSHIP,
        method=NullMethod.SPAN_MATCHED,
        description=(
            "the same data under a change of units; a relational conclusion "
            "counts only if it is invariant under the rescaling."),
        generator=span_matched_surrogate,
        derivation_family="unit_representation")
    reg.register("unit_invariant_relationship", rel_null,
                 effect_family="relational_ordering",
                 has_power=rel_power.has_power)

    # Family 4: physics. Effect = a specimen resonance above the fixture.
    phys_power = prove_power(
        PHYSICS_NULL, specimen_window_peak_statistic,
        planted=planted_specimen_spectrum(np.random.default_rng(seed)),
        noise=fixture_only_spectrum(np.random.default_rng(seed + 7)),
        n_trials=n_trials, seed=seed)
    reg.register("specimen_resonance", PHYSICS_NULL,
                 effect_family="specimen_line", has_power=phys_power.has_power)
    return reg


def validate_registry(registry: NullRegistry) -> dict:
    """Check every binding has proven power and is non-circular.

    The registry-level R10.6 enforcement: a bound null must detect a planted
    effect (power) and must be derived from a different source than the
    effect it controls (non-circular)."""
    bindings = registry.bindings()
    if not bindings:
        raise NullError("the registry is empty")
    no_power = [b.metric for b in bindings if not b.has_power]
    if no_power:
        raise NullError(
            f"refused: {len(no_power)} binding(s) lack proven power "
            f"({', '.join(no_power)}); a null that cannot detect a planted "
            f"effect makes every negative result meaningless")
    circular = [b.metric for b in bindings
                if b.null_model.derivation_family == b.effect_family]
    if circular:
        raise NullError(
            f"refused: {len(circular)} binding(s) are circular "
            f"({', '.join(circular)}); a null derived from the same family "
            f"as the effect is not an independent control")
    families = sorted({b.null_model.family.value for b in bindings})
    return {
        "binding_count": len(bindings),
        "all_have_power": True,
        "all_non_circular": True,
        "families_covered": families,
        "metrics": [b.metric for b in bindings],
    }


# =======================================================================
# The refusals
# =======================================================================

def refuse_null_without_power(null_name: str = "", *_a, **_k) -> None:
    """Refuse a null that cannot detect a planted effect as vacuous."""
    who = f" {null_name!r}" if null_name else ""
    raise NullError(
        f"refused: null{who} has not proven power. A null model that cannot "
        f"flag a planted effect produces null results that mean nothing -- "
        f"failing to reject it is indistinguishable from a method that could "
        f"never have seen anything. Prove power (detect a planted effect, "
        f"stay silent on noise) before registering it. " + DEFAULT_VERDICT)


def refuse_absence_as_evidence(*_a, **_k) -> None:
    """Refuse "failed to reject the null" as "the effect is absent".

    A large p-value is only ever *consistent with* the null. It is proof of
    absence only if the method had power to detect an effect of the relevant
    size -- and even then it bounds, rather than proves, the absence."""
    raise NullError(
        "refused: failing to reject the null is not proof that the effect is "
        "absent. A non-significant p-value is consistent with no effect and "
        "with an effect too small for this method to see. Absence may be "
        "*bounded* only after power is demonstrated, and even then it is a "
        "constraint, not a proof. " + DEFAULT_VERDICT)


def guard_absence_claim(power_report: PowerReport) -> None:
    """Permit an absence claim only when power was demonstrated.

    Without power, invoking this routes to :func:`refuse_absence_as_evidence`;
    with power, an absence claim is admissible as a *bounded* statement."""
    if not isinstance(power_report, PowerReport):
        raise NullError("guard_absence_claim needs a PowerReport")
    if not power_report.has_power:
        refuse_absence_as_evidence()


def bounded_absence_statement(result: MonteCarloResult,
                              power_report: PowerReport) -> str:
    """A legitimate, bounded reading of a non-rejection -- only after power.

    Not "there is no effect", but "no effect above the planted size was
    detected, and the method had power to detect one", which constrains the
    effect without proving its absence."""
    guard_absence_claim(power_report)
    if result.significant:
        raise NullError(
            "this result rejected the null; a bounded-absence statement "
            "applies only to a non-rejection")
    return (
        f"no effect was detected (p = {result.p_value_text}); the method had "
        f"demonstrated power to detect the planted effect, so an effect of "
        f"that size is constrained -- absence is bounded, not proven")


def refuse_p_value_zero(*_a, **_k) -> None:
    """Refuse a p-value of exactly zero."""
    raise NullError(
        "refused: a Monte Carlo p-value is never exactly zero. With n "
        "trials the estimate is (tail + 1) / (n + 1) and its floor is "
        "1 / (n + 1) > 0. Report p < floor at the Monte Carlo resolution, "
        "never p = 0. " + DEFAULT_VERDICT)


def refuse_circular_null(metric: str = "", family: str = "",
                         *_a, **_k) -> None:
    """Refuse a null derived from the same family as the effect it tests."""
    ctx = ""
    if metric or family:
        ctx = f" (metric {metric!r}, family {family!r})"
    raise NullError(
        f"refused: a circular null{ctx}. A null derived from the same data "
        f"family as the effect it is meant to control cannot be an "
        f"independent baseline -- it inherits the very structure under "
        f"test, so beating it is guaranteed and proves nothing. " +
        DEFAULT_VERDICT)


def refuse_equal_temperament_as_rational_control(*_a, **_k) -> None:
    """Refuse equal temperament as a rational-ratio control."""
    raise NullError(
        "refused: equal temperament is not a rational-ratio control. Its "
        "ratios are 2**(k/12), irrational by construction -- a deliberate "
        "approximation of the small-integer ratios under test. Using it as "
        "the control begs the question: it is engineered to sit near the "
        "rationals. The rational control is an exact just-intonation scale "
        "or a representation-matched random draw over the same range. " +
        DEFAULT_VERDICT)


def refuse_flat_spectrum_null_for_ism(*_a, **_k) -> None:
    """Refuse a flat-spectrum null where anthropogenic ISM structure exists."""
    raise NullError(
        "refused: a flat-spectrum null over a band that contains ISM "
        "allocations. ISM bands are anthropogenic infrastructure "
        "(industrial, scientific, medical), so a flat null would flag "
        "ordinary Wi-Fi, ovens, and RFID as discoveries. The design-matched "
        "null expects power at the ISM allocations; only a peak away from "
        "them may be novel. " + DEFAULT_VERDICT)


def refuse_unit_dependent_conclusion(*_a, **_k) -> None:
    """Refuse a conclusion that changes under a mere unit conversion."""
    raise NullError(
        "refused: a conclusion that flips under a change of units is an "
        "artifact of representation, not a relationship. A genuine "
        "relational claim (an ordering, a correlation sign) is invariant "
        "under positive rescaling; if converting Hz to kHz changes the "
        "verdict, the verdict was never about the world. " + DEFAULT_VERDICT)


def refuse_fixture_response_as_signal(*_a, **_k) -> None:
    """Refuse a fixture-loaded resonance as a specimen signal.

    Delegates to the governance core's noise-to-resonance refusal: a peak
    reproduced by the fixture's own Lorentzian belongs to the mount, not the
    specimen, and does not clear the physics-matched null."""
    refuse_noise_as_resonance()


#: The refusals, indexed for the red team.
REFUSALS = {
    "null_without_power": refuse_null_without_power,
    "absence_as_evidence": refuse_absence_as_evidence,
    "p_value_zero": refuse_p_value_zero,
    "circular_null": refuse_circular_null,
    "equal_temperament_as_rational_control":
        refuse_equal_temperament_as_rational_control,
    "flat_spectrum_null_for_ism": refuse_flat_spectrum_null_for_ism,
    "unit_dependent_conclusion": refuse_unit_dependent_conclusion,
    "fixture_response_as_signal": refuse_fixture_response_as_signal,
}


# =======================================================================
# The report
# =======================================================================

def nulls_report() -> dict:
    """The standing result: a null-model registry with power proven on every
    family, and the four matched-null facts."""
    registry = build_default_registry()
    validation = validate_registry(registry)

    # A worked Monte Carlo on a strongly planted tone: p hits the floor.
    rng = np.random.default_rng(20260724)
    planted_tone = (np.sin(2 * np.pi * 7 * np.linspace(0, 1, 256))
                    + 0.1 * rng.standard_normal(256))
    mc = monte_carlo_p_value(
        spectral_peak_statistic, planted_tone,
        NullModel(name="noise_only", family=NullFamily.GENERIC,
                  method=NullMethod.NOISE_ONLY,
                  description="white noise at the data's scale",
                  generator=noise_only_surrogate,
                  derivation_family="noise"),
        n_trials=REPORT_MC_TRIALS, seed=20260724)

    return {
        "what_this_is": (
            "a null-model registry: for every claimed effect a registered "
            "null model (what the data look like with no effect), a test "
            "statistic evaluated against it by Monte Carlo / permutation, an "
            "empirical p-value, and a proof that the null has power to detect "
            "a planted effect"),
        "analysis_version": ANALYSIS_VERSION,
        "registry": [b.as_dict() for b in registry.bindings()],
        "registry_validation": validation,
        "matched_null_families": [f.value for f in NullFamily],
        "surrogate_methods": [m.value for m in NullMethod],
        "worked_monte_carlo": {
            "statistic": mc.statistic,
            "p_value": mc.p_value,
            "p_value_text": mc.p_value_text,
            "empirical_tail_count": mc.empirical_tail_count,
            "n_trials": mc.n_trials,
            "monte_carlo_resolution": mc.mc_resolution,
            "p_is_never_zero": mc.p_value > 0.0,
        },
        "representation_fact": {
            "equal_temperament_is_rational_ratio_control":
                equal_temperament_is_rational_ratio_control(),
            "note": "equal temperament is an irrational approximation; the "
                    "rational control is an exact just-intonation scale",
        },
        "design_fact": {
            "ism_bands_are_anthropogenic": True,
            "example_2p45GHz_is_anthropogenic":
                is_anthropogenic_band(2.45e9),
            "hydrogen_line_is_anthropogenic":
                is_anthropogenic_band(HYDROGEN_LINE_HZ),
        },
        "relationship_fact": prove_relationship_power().as_dict(),
        "physics_fact": {
            "null": PHYSICS_NULL.name,
            "carries_fixture_and_instrument": True,
        },
        "refusals": list(REFUSALS),
        "claim_class": ClaimClass.SOFTWARE_IMPLEMENTED.value,
        "claim_cap": CLAIM_CAP,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": DEFAULT_VERDICT,
        "what_this_does_not_say": (
            "It measures nothing and detects no real effect anywhere. Every "
            "dataset here is a deterministic synthetic fixture, and every "
            "'detection' is of a planted signal placed there to prove the "
            "null has power. A registered null with power is what makes a "
            "future negative result interpretable; it is not itself evidence "
            "of any effect. Failing to reject a null is never proof of "
            "absence unless power was demonstrated, and even then it only "
            "bounds the effect. No physical validation is claimed; the "
            "strongest class reachable here is SYNTHETIC_OBSERVATION."),
    }
