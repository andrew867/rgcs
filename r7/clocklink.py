"""P03 — root reference authority and the differential clock link.

This is R7's priority experiment, and the one R6 ended by
recommending: compare two independently characterized oscillators
through a declared transfer link while recording every environmental
nuisance channel.

It is the priority because it is the only part of the programme whose
claim ceiling is actually reachable. It needs no crystal, no coil, no
contested geometry — two oscillators, a counter, and honest
bookkeeping.

The model:

    dphi_AB(t) = 2*pi*Int[nu_A(t') - nu_B(t')]dt'
                 + phi_link(t) + phi_instrument(t)

The claim ceiling, stated numerically rather than asserted: two
consumer quartz oscillators do not demonstrate metre-scale
relativistic height sensing. :func:`height_resolution` computes why,
and the reason is not impatience — it is the **flicker floor**. White
frequency noise averages down as 1/sqrt(tau), so a naive calculation
says "just integrate longer". Real oscillators stop averaging at
their flicker floor and then drift. Once the floor sits above the
target, no integration time closes the gap, and the honest answer is
"never" rather than "2.7 years".

Nothing here is bench data. No oscillator pair has been compared, no
transfer link built, no phase recorded.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, asdict, field

from . import ROOT_CLASSES

#: Catalogue-class oscillator specifications. ``adev_1s`` is the
#: short-term Allan deviation at 1 s; ``flicker_floor`` is the level
#: at which averaging stops helping; ``drift_per_day`` is the
#: systematic ageing term. These are order-of-magnitude figures for
#: typical commercial parts, not measurements of owned equipment.
OSCILLATORS = {
    "QUARTZ_XO": {
        "adev_1s": 1e-9, "flicker_floor": 1e-9,
        "drift_per_day": 1e-8, "cost_usd": 1,
        "note": "plain crystal oscillator; temperature dominates"},
    "TCXO": {
        "adev_1s": 1e-10, "flicker_floor": 5e-11,
        "drift_per_day": 1e-9, "cost_usd": 10,
        "note": "temperature-compensated"},
    "OCXO": {
        "adev_1s": 1e-12, "flicker_floor": 1e-13,
        "drift_per_day": 1e-10, "cost_usd": 200,
        "note": "oven-controlled; the realistic hobbyist ceiling"},
    "RUBIDIUM": {
        "adev_1s": 1e-11, "flicker_floor": 1e-14,
        "drift_per_day": 1e-13, "cost_usd": 1500,
        "note": "rubidium vapour cell; worse at 1 s than a good OCXO, "
                "far better after a day"},
    "GPSDO": {
        "adev_1s": 1e-10, "flicker_floor": 1e-14,
        "drift_per_day": 0.0, "cost_usd": 500,
        "note": "GPS-disciplined; long-term traceable, but the "
                "discipline loop is an external dependency"},
    "CAESIUM": {
        "adev_1s": 1e-11, "flicker_floor": 1e-15,
        "drift_per_day": 0.0, "cost_usd": 50_000,
        "note": "primary standard; no drift by definition"},
    "HYDROGEN_MASER": {
        "adev_1s": 1e-13, "flicker_floor": 1e-16,
        "drift_per_day": 1e-16, "cost_usd": 300_000,
        "note": "best short-to-medium term microwave standard"},
    "OPTICAL": {
        "adev_1s": 1e-16, "flicker_floor": 1e-19,
        "drift_per_day": 0.0, "cost_usd": 5_000_000,
        "note": "optical lattice clock; laboratory-scale facility"},
}

#: Transfer links, with the phase uncertainty each contributes.
TRANSFER_LINKS = {
    "COAX_SHORT": {"frac_uncertainty": 1e-15,
                   "note": "a metre of coax in a stable room"},
    "COAX_LONG": {"frac_uncertainty": 1e-13,
                  "note": "tens of metres; thermal expansion of the "
                          "cable modulates delay"},
    "FIBRE_STABILIZED": {"frac_uncertainty": 1e-18,
                         "note": "actively stabilized optical fibre"},
    "GPS_COMMON_VIEW": {"frac_uncertainty": 1e-15,
                        "note": "common-view GPS over a day"},
    "WIRELESS_UNDISCIPLINED": {"frac_uncertainty": 1e-11,
                               "note": "not suitable for metrology"},
}

#: The nine configurations from the contract, in the order they should
#: actually be run. The first two cost almost nothing and are the ones
#: that tell you whether the rest of the chain is trustworthy.
CONFIGURATIONS = (
    "COMMON_SOURCE_SPLIT",
    "ONE_SYNTHESIZER_TWO_OUTPUTS",
    "TWO_INDEPENDENT_QUARTZ",
    "DISCIPLINED_VS_HOLDOVER",
    "ATOMIC_REFERENCE",
    "APPARATUS_IN_TRANSFER_PATH",
    "SHAM_INSERTION",
    "SIMULATED_HEIGHT_PERTURBATION",
    "REAL_HEIGHT_COMPARISON",
)

C = 299_792_458.0
G_EARTH = 9.806_65


class ClockRefused(RuntimeError):
    """Raised when a clock-link claim is refused."""


# --------------------------------------------------------------------
# Root reference
# --------------------------------------------------------------------

@dataclass(frozen=True)
class RootReference:
    """R_0 — a declared phase authority, not a preferred story.

    4096 Hz may be *derived* from the root by division. It need not be,
    and generally is not, the physical root oscillator. A root is
    chosen on metrological grounds before any experimental outcome.
    """

    source_id: str
    root_class: str
    f0_hz: float
    phi0_rad: float
    t0_s: float
    time_scale: str
    adev_1s: float
    flicker_floor: float
    holdover_s: float
    calibration_id: str | None = None

    def __post_init__(self) -> None:
        if self.root_class not in ROOT_CLASSES:
            raise ValueError(f"unknown root class {self.root_class!r}")
        if self.f0_hz <= 0:
            raise ValueError("root frequency must be positive")
        if self.time_scale not in ("TAI", "UTC", "TT", "GPS", "LOCAL"):
            raise ValueError(f"undeclared time scale {self.time_scale!r}")
        if self.flicker_floor > self.adev_1s:
            raise ValueError(
                "flicker floor cannot be worse than the 1 s stability")

    def derive(self, target_hz: float) -> dict:
        """Derive a target frequency by an exact integer ratio if possible."""
        ratio = self.f0_hz / target_hz
        exact = abs(ratio - round(ratio)) < 1e-12
        return {
            "root_hz": self.f0_hz,
            "target_hz": target_hz,
            "ratio": ratio,
            "integer_ratio": exact,
            "divisor": round(ratio) if exact else None,
            "note": ("derived by integer division from the declared "
                     "root; the target is not itself a root"
                     if exact else
                     "requires fractional synthesis; the synthesizer "
                     "becomes part of the phase authority"),
        }


def candidate_roots() -> dict:
    """Every candidate root class with its selection-relevant figures.

    No source is declared fundamental (core/01).
    """
    return {
        name: dict(spec, root_class=name)
        for name, spec in OSCILLATORS.items()
    }


def select_root(requirement_adev: float, *,
                budget_usd: float = math.inf) -> dict:
    """Choose a root on stated requirements, before any outcome."""
    viable = [
        (n, s) for n, s in OSCILLATORS.items()
        if s["flicker_floor"] <= requirement_adev
        and s["cost_usd"] <= budget_usd
    ]
    if not viable:
        return {
            "selected": None,
            "status": "NO_VIABLE_ROOT",
            "note": (f"no candidate reaches {requirement_adev:.1e} "
                     f"within a budget of {budget_usd}"),
        }
    viable.sort(key=lambda kv: kv[1]["cost_usd"])
    name, spec = viable[0]
    return {
        "selected": name,
        "status": "ROOT_SELECTED",
        "flicker_floor": spec["flicker_floor"],
        "cost_usd": spec["cost_usd"],
        "note": "cheapest candidate meeting the stated requirement; "
                "selection is made before experimental outcomes",
    }


# --------------------------------------------------------------------
# Allan deviation
# --------------------------------------------------------------------

def overlapping_adev(y: list[float], tau0_s: float, m: int) -> float:
    """Overlapping Allan deviation of fractional-frequency data.

    ``y`` is a series of fractional frequency averages each of
    duration ``tau0_s``; ``m`` is the averaging factor, so the
    reported tau is m*tau0.
    """
    n = len(y)
    if m < 1 or 2 * m >= n:
        raise ValueError("averaging factor too large for the series")
    # cumulative phase (in units of seconds of time error)
    x = [0.0]
    for v in y:
        x.append(x[-1] + v * tau0_s)
    tau = m * tau0_s
    total = 0.0
    count = 0
    for i in range(len(x) - 2 * m):
        d = x[i + 2 * m] - 2 * x[i + m] + x[i]
        total += d * d
        count += 1
    if count == 0:
        raise ValueError("not enough data for this averaging factor")
    return math.sqrt(total / (2 * count * tau * tau))


def adev_model(adev_1s: float, flicker_floor: float,
               tau_s: float) -> float:
    """Modeled Allan deviation at averaging time tau.

    White frequency noise averages as 1/sqrt(tau) until it reaches the
    flicker floor, after which it stops improving. This single feature
    is what turns "integrate longer" from a strategy into a fantasy.
    """
    if tau_s <= 0:
        raise ValueError("averaging time must be positive")
    white = adev_1s / math.sqrt(tau_s)
    return max(white, flicker_floor)


def simulate_frequency_series(adev_1s: float, n: int, tau0_s: float,
                              *, seed: int,
                              flicker_floor: float = 0.0) -> list[float]:
    """A reproducible synthetic fractional-frequency series.

    White FM plus a constant offset representing the flicker floor.
    Explicitly synthetic — used to exercise the estimator, never to
    stand in for a measurement.
    """
    rng = random.Random(seed)
    sigma = adev_1s * math.sqrt(1.0 / tau0_s) if tau0_s > 0 else adev_1s
    walk = 0.0
    out = []
    for _ in range(n):
        walk += rng.gauss(0.0, flicker_floor) if flicker_floor else 0.0
        out.append(rng.gauss(0.0, sigma) + walk)
    return out


# --------------------------------------------------------------------
# The claim ceiling, computed
# --------------------------------------------------------------------

def height_fractional_shift(delta_h_m: float) -> float:
    """df/f = g*dh/c^2."""
    return G_EARTH * delta_h_m / (C * C)


@dataclass(frozen=True)
class HeightResolution:
    oscillator: str
    link: str
    target_height_m: float
    target_fractional: float
    flicker_floor: float
    link_floor: float
    combined_floor: float
    resolvable: bool
    tau_required_s: float | None
    tau_required_years: float | None
    status: str
    note: str

    def as_record(self) -> dict:
        return asdict(self)


def height_resolution(oscillator: str, *, link: str = "COAX_SHORT",
                      target_height_m: float = 1.0
                      ) -> HeightResolution:
    """Can this oscillator pair resolve this height difference?

    The naive answer integrates white noise down forever. The honest
    answer stops at the flicker floor: if the floor is above the
    target, the answer is never, not "longer".
    """
    if oscillator not in OSCILLATORS:
        raise ValueError(f"unknown oscillator {oscillator!r}")
    if link not in TRANSFER_LINKS:
        raise ValueError(f"unknown link {link!r}")
    spec = OSCILLATORS[oscillator]
    target = height_fractional_shift(target_height_m)

    # two oscillators of the same type: floors add in quadrature
    osc_floor = spec["flicker_floor"] * math.sqrt(2)
    link_floor = TRANSFER_LINKS[link]["frac_uncertainty"]
    combined = math.sqrt(osc_floor ** 2 + link_floor ** 2)

    if combined > target:
        limiter = ("the transfer link" if link_floor > osc_floor
                   else "the oscillators' flicker floor")
        return HeightResolution(
            oscillator=oscillator, link=link,
            target_height_m=target_height_m,
            target_fractional=target, flicker_floor=osc_floor,
            link_floor=link_floor, combined_floor=combined,
            resolvable=False, tau_required_s=None,
            tau_required_years=None,
            status="UNRESOLVABLE_AT_ANY_INTEGRATION_TIME",
            note=(
                f"the target shift is {target:.2e} and the noise floor "
                f"is {combined:.2e}, set by {limiter}. Averaging "
                f"reduces white frequency noise but not the floor, so "
                f"no integration time reaches this target. The answer "
                f"is not 'longer'; it is 'never with this hardware'."))

    # floor is below target: how long to average white noise down?
    adev1 = spec["adev_1s"] * math.sqrt(2)
    tau = (adev1 / target) ** 2
    years = tau / (365.25 * 86400.0)
    return HeightResolution(
        oscillator=oscillator, link=link,
        target_height_m=target_height_m, target_fractional=target,
        flicker_floor=osc_floor, link_floor=link_floor,
        combined_floor=combined, resolvable=True,
        tau_required_s=tau, tau_required_years=years,
        status=("RESOLVABLE" if years < 1.0
                else "RESOLVABLE_BUT_IMPRACTICAL"),
        note=(f"floor {combined:.2e} is below the target {target:.2e}; "
              f"averaging for {tau:.3g} s ({years:.3g} years) reaches "
              f"it"))


def limiter(oscillator: str, link: str) -> str:
    """Which term actually sets the floor for this pairing.

    Worth computing rather than assuming: for consumer parts the
    oscillator dominates, but for the best clocks the *transfer link*
    does. An optical pair on short coax is link-limited and cannot
    resolve a metre; the same pair on stabilized fibre resolves it in
    seconds. Buying a better clock without a better link buys nothing.
    """
    osc = OSCILLATORS[oscillator]["flicker_floor"] * math.sqrt(2)
    lnk = TRANSFER_LINKS[link]["frac_uncertainty"]
    if osc > 3 * lnk:
        return "OSCILLATOR_LIMITED"
    if lnk > 3 * osc:
        return "LINK_LIMITED"
    return "COMPARABLE_CONTRIBUTIONS"


def ceiling_report(target_height_m: float = 1.0,
                   links: tuple[str, ...] = ("COAX_SHORT",
                                             "FIBRE_STABILIZED")
                   ) -> dict:
    """The P03 headline: what each oscillator class can actually do.

    Swept over transfer links, because a single link would hide the
    fact that the bottleneck moves.
    """
    rows: dict = {}
    for name in OSCILLATORS:
        rows[name] = {}
        for lk in links:
            r = height_resolution(name, link=lk,
                                  target_height_m=target_height_m)
            rec = r.as_record()
            rec["limiter"] = limiter(name, lk)
            rows[name][lk] = rec
    quartz = [n for n in ("QUARTZ_XO", "TCXO", "OCXO")
              if not any(rows[n][lk]["resolvable"] for lk in links)]
    link_limited = [
        (n, lk) for n in rows for lk in links
        if rows[n][lk]["limiter"] == "LINK_LIMITED"
        and not rows[n][lk]["resolvable"]
    ]
    return {
        "target_height_m": target_height_m,
        "target_fractional": height_fractional_shift(target_height_m),
        "links_swept": list(links),
        "oscillators": rows,
        "consumer_quartz_unresolvable": quartz,
        "link_limited_pairings": [f"{n}+{lk}" for n, lk in link_limited],
        "bottleneck_note": (
            "The limiting term moves. Consumer quartz is "
            "oscillator-limited and no link helps it. The best clocks "
            "are link-limited: an optical pair on short coax cannot "
            "resolve a metre, while the same pair on stabilized fibre "
            "resolves it in seconds. Buying a better clock without "
            "also buying a better link buys nothing."),
        "claim_ceiling": (
            "Two consumer quartz oscillators do not demonstrate "
            "metre-scale relativistic height sensing. Not because the "
            "experiment is hard, but because their flicker floor sits "
            "above the target and averaging does not lower a floor."),
        "what_the_experiment_still_delivers": [
            "validated phase-transfer chain end to end",
            "measured instrument floor from the common-source split",
            "noise decomposition into white FM, flicker and drift",
            "environmental covariance against temperature and supply",
            "a real Allan deviation curve for the actual hardware",
            "an honest sensitivity budget for any later claim",
        ],
        "why_run_it_anyway": (
            "The common-source split costs almost nothing and is the "
            "only way to learn what the measurement chain itself "
            "contributes. Every later claim depends on that number, "
            "and no amount of modelling substitutes for it."),
    }


def refuse_height_claim(oscillator: str, target_height_m: float = 1.0):
    """Refuse a geodesy claim the hardware cannot support."""
    r = height_resolution(oscillator, target_height_m=target_height_m)
    if not r.resolvable:
        raise ClockRefused(
            f"{oscillator} cannot resolve {target_height_m} m: "
            f"{r.note}")
    return r


# --------------------------------------------------------------------
# Modified Allan and time deviation (R8-D-003)
# --------------------------------------------------------------------

def _phase_from_frequency(y: list[float], tau0_s: float) -> list[float]:
    """Cumulative phase (time error, seconds) from fractional frequency."""
    x = [0.0]
    for v in y:
        x.append(x[-1] + v * tau0_s)
    return x


def overlapping_mdev(y: list[float], tau0_s: float, m: int) -> float:
    """Overlapping modified Allan deviation.

    MVAR(tau) = 1 / (2 m^2 tau^2 (N - 3m + 2)) *
                sum_j [ sum_{i=j}^{j+m-1} (x_{i+2m} - 2 x_{i+m} + x_i) ]^2

    MDEV differs from ADEV by averaging the second difference over a
    window of m samples before squaring, which is what lets it
    separate white phase noise from flicker phase noise -- ADEV cannot,
    because both give the same tau^-1 slope.

    At m = 1 the inner sum has one term and MVAR reduces exactly to
    AVAR, which is the validation anchor used in the tests.
    """
    x = _phase_from_frequency(y, tau0_s)
    n = len(x)
    if m < 1 or n < 3 * m + 1:
        raise ValueError("series too short for this averaging factor")
    tau = m * tau0_s
    outer = 0.0
    count = 0
    for j in range(n - 3 * m + 1):
        inner = 0.0
        for i in range(j, j + m):
            inner += x[i + 2 * m] - 2.0 * x[i + m] + x[i]
        outer += inner * inner
        count += 1
    if count == 0:
        raise ValueError("not enough data for this averaging factor")
    mvar = outer / (2.0 * (m ** 4) * (tau0_s ** 2) * count)
    return math.sqrt(mvar)


def time_deviation(y: list[float], tau0_s: float, m: int) -> float:
    """Time deviation, TDEV(tau) = tau * MDEV(tau) / sqrt(3).

    This is a definition, not an estimate, so the tests assert it
    exactly rather than approximately.
    """
    tau = m * tau0_s
    return tau * overlapping_mdev(y, tau0_s, m) / math.sqrt(3.0)


#: Which estimators actually exist in code. R8-D-003: the analysis
#: plan previously named three and implemented one.
IMPLEMENTED_ESTIMATORS = {
    "ADEV": "overlapping_adev",
    "MDEV": "overlapping_mdev",
    "TDEV": "time_deviation",
}
