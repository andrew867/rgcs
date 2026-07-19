"""P11 — the clock-link measurement programme.

R7 computed the claim ceiling. This module specifies the *programme*
that would test it: what to buy, in what order to run it, what floor
to expect, and how the data will be analysed — with the analysis
frozen before any data exists, because that is the only point at which
freezing it means anything.

Read this alongside :mod:`r7.clocklink`, which owns the physics. Every
resolution figure quoted here is *computed* by
:func:`r7.clocklink.height_resolution` at call time rather than
transcribed, so the two modules cannot drift apart.

The uncomfortable result, stated up front so that no tier table reads
as encouragement: **no tier in this document resolves a one-metre
height difference.** The best tier specified here — a rubidium pair on
short coax, about fifteen thousand dollars — reaches a minimum
resolvable height of roughly one hundred and thirty metres. That is a
hillside, not a bench. The programme is still worth running, but for
the instrument floor it measures, not for the geodesy it cannot do.

Nothing in this module is a measurement. RGCS owns no oscillator, no
counter, no coax and no temperature logger. No clock pair has been
compared, no Allan deviation estimated from hardware, and no
environmental channel logged. Prices are catalogue-class estimates
gathered to establish order of magnitude; they are not quotes, they
are not current, and they are not offers.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict

from r7 import clocklink

#: Everything this module emits is either a specification of intent or
#: arithmetic over declared catalogue figures. Neither is a reading.
EVIDENCE_CLASS = "SYNTHETIC_MODEL"
DERIVED = "DERIVED_ARITHMETIC"

NO_MEASUREMENT = (
    "No measurement has been taken. RGCS owns no clock-link hardware, "
    "holds no calibration certificate, and has recorded no phase, no "
    "frequency and no environmental channel. This object specifies a "
    "measurement programme; it does not report one.")

PRICE_BASIS = (
    "CATALOGUE_CLASS_ESTIMATE_NOT_A_QUOTE: order-of-magnitude figures "
    "for the part category, assembled to size the programme. Not "
    "solicited, not current, not binding.")

#: Budget tiers, cheapest first.
TIERS = ("MINIMAL", "STANDARD", "GOOD")


class MeasurementRefused(RuntimeError):
    """Raised when a measurement claim is refused."""


def _stamp(record: dict, evidence_class: str = EVIDENCE_CLASS) -> dict:
    """Attach the evidence class and the no-measurement statement.

    Applied to every dict this module returns. A record that escapes
    without it is a bug, and the tests check for exactly that.
    """
    record["evidence_class"] = evidence_class
    record["no_measurement_statement"] = NO_MEASUREMENT
    return record


# --------------------------------------------------------------------
# 1. Bill of materials
# --------------------------------------------------------------------

#: Line items per tier. ``qty``/``unit_usd`` are catalogue-class
#: estimates (see :data:`PRICE_BASIS`). ``role`` says what the part is
#: for, because a BOM that only lists parts cannot be criticized.
BOM: dict[str, dict] = {
    "MINIMAL": {
        "budget_usd": 300,
        "oscillator": "TCXO",
        "link": "COAX_SHORT",
        # A plain reciprocal frequency counter, not a time-interval
        # counter: single-shot time resolution of order 100 ns. This
        # one number, not the oscillators, sets the short-tau floor.
        "tic_single_shot_s": 100e-9,
        "instrument_note": (
            "a bench frequency counter, not a TIC. Its single-shot "
            "resolution dominates until tau is of order an hour"),
        "items": (
            {"part": "TCXO oscillator module, 10 MHz, sine or CMOS",
             "qty": 2, "unit_usd": 15,
             "role": "the two devices under comparison"},
            {"part": "reciprocal frequency counter, 8 digit, used "
                     "bench instrument with external reference input",
             "qty": 1, "unit_usd": 150,
             "role": "reads the frequency difference; the dominant "
                     "noise source at short tau"},
            {"part": "resistive power splitter / BNC tee, 50 ohm",
             "qty": 1, "unit_usd": 10,
             "role": "common-source split for step 1; a resistive "
                     "split is lossy but has no active noise"},
            {"part": "RG-316 coaxial jumper, 0.5 m, SMA/BNC",
             "qty": 4, "unit_usd": 8,
             "role": "the declared transfer link; keep short and "
                     "keep the routing fixed between runs"},
            {"part": "USB temperature and humidity logger, 1-minute "
                     "cadence",
             "qty": 1, "unit_usd": 30,
             "role": "the nuisance channel that actually explains "
                     "TCXO behaviour"},
            {"part": "linear bench power supply, used, low ripple",
             "qty": 1, "unit_usd": 60,
             "role": "supply voltage is the second nuisance channel; "
                     "a switching brick injects its own spurs"},
        ),
    },
    "STANDARD": {
        "budget_usd": 2_000,
        "oscillator": "OCXO",
        "link": "COAX_SHORT",
        # A real time-interval counter (TAPR TICC class or a used
        # SR620): ~60 ps single shot.
        "tic_single_shot_s": 60e-12,
        "instrument_note": (
            "a genuine time-interval counter. The instrument stops "
            "being the limit somewhere in the tens-to-hundreds of "
            "seconds and the oscillators take over"),
        "items": (
            {"part": "OCXO module, 10 MHz, oven-controlled",
             "qty": 2, "unit_usd": 200,
             "role": "the two devices under comparison"},
            {"part": "time-interval counter, ~60 ps single-shot "
                     "resolution (TICC-class kit or used TIC)",
             "qty": 1, "unit_usd": 700,
             "role": "measures time error directly rather than "
                     "differencing two frequency readings"},
            {"part": "distribution amplifier, 4-way, 50 ohm, "
                     "isolated outputs",
             "qty": 1, "unit_usd": 250,
             "role": "fans the reference out without the crosstalk a "
                     "resistive split allows"},
            {"part": "GPSDO, 10 MHz + 1 PPS",
             "qty": 1, "unit_usd": 500,
             "role": "long-term traceability and the disciplined "
                     "side of the holdover comparison in step 4"},
            {"part": "phase-stable coaxial cable set, SMA",
             "qty": 1, "unit_usd": 80,
             "role": "thermal expansion of ordinary coax modulates "
                     "delay and mimics a frequency offset"},
            {"part": "multi-channel temperature logger, 4 probes",
             "qty": 1, "unit_usd": 120,
             "role": "oven, ambient, cable run and counter chassis "
                     "are four different temperatures"},
            {"part": "low-noise regulated linear supply, multi-rail",
             "qty": 1, "unit_usd": 150,
             "role": "supply pushing is a specified OCXO parameter "
                     "and must be logged to be subtracted"},
        ),
    },
    "GOOD": {
        "budget_usd": 15_000,
        "oscillator": "RUBIDIUM",
        "link": "COAX_SHORT",
        "tic_single_shot_s": 1e-12,
        "instrument_note": (
            "a dual-mixer or high-resolution TIC. The instrument is "
            "no longer the limit at any tau of interest; the "
            "oscillators and the coax are"),
        "items": (
            {"part": "rubidium frequency standard, 10 MHz",
             "qty": 2, "unit_usd": 1_500,
             "role": "the two devices under comparison. Note the "
                     "trade: worse than a good OCXO at 1 s, far "
                     "better after a day"},
            {"part": "phase-noise / time-interval test set, ~1 ps "
                     "resolution (DMTD or used SR620-class)",
             "qty": 1, "unit_usd": 6_000,
             "role": "removes the instrument from the noise budget"},
            {"part": "GPSDO with sawtooth correction output",
             "qty": 1, "unit_usd": 1_200,
             "role": "traceability, and the sawtooth output is what "
                     "makes 1 PPS comparisons honest"},
            {"part": "distribution amplifier, 8-way, isolated",
             "qty": 1, "unit_usd": 900,
             "role": "one reference, many instruments, no ground "
                     "loops"},
            {"part": "temperature-controlled enclosure, +/- 0.1 K",
             "qty": 1, "unit_usd": 1_500,
             "role": "controls the nuisance channel rather than "
                     "merely logging it"},
            {"part": "phase-stable cable set, low thermal "
                     "coefficient",
             "qty": 1, "unit_usd": 400,
             "role": "at this floor the cable is a real term in the "
                     "budget, not a detail"},
            {"part": "environmental logging: temperature, humidity, "
                     "barometric pressure, supply rails",
             "qty": 1, "unit_usd": 500,
             "role": "every channel that could produce the effect "
                     "must be recorded or it cannot be excluded"},
            {"part": "online UPS / conditioned mains",
             "qty": 1, "unit_usd": 600,
             "role": "a mains dropout mid-run destroys the holdover "
                     "arm of step 4"},
        ),
    },
}

#: Heights swept when reporting what a tier can and cannot resolve.
#: One metre is included because it is the number the programme is
#: repeatedly tempted to claim.
DEFAULT_TARGET_HEIGHTS_M = (1.0, 10.0, 100.0, 1_000.0, 10_000.0)


def _check_tier(tier: str) -> dict:
    if tier not in BOM:
        raise ValueError(f"unknown budget tier {tier!r}; "
                         f"expected one of {TIERS}")
    return BOM[tier]


def tier_cost(tier: str) -> dict:
    """Line-item and total cost for a tier, summed not asserted."""
    spec = _check_tier(tier)
    lines = [dict(it, line_usd=it["qty"] * it["unit_usd"])
             for it in spec["items"]]
    total = sum(line["line_usd"] for line in lines)
    return _stamp({
        "tier": tier,
        "items": lines,
        "total_usd": total,
        "nominal_budget_usd": spec["budget_usd"],
        "within_nominal_budget": total <= spec["budget_usd"] * 1.2,
        "price_basis": PRICE_BASIS,
    }, DERIVED)


def minimum_resolvable_height_m(tier: str) -> float:
    """The smallest height difference this tier's floor could ever see.

    Inverts ``df/f = g dh/c^2`` at the combined floor computed by
    :func:`r7.clocklink.height_resolution`. Below this height no
    integration time helps, because averaging lowers white noise and
    not a floor.
    """
    spec = _check_tier(tier)
    r = clocklink.height_resolution(
        spec["oscillator"], link=spec["link"], target_height_m=1.0)
    return r.combined_floor * clocklink.C ** 2 / clocklink.G_EARTH


def bill_of_materials(
        tier: str,
        target_heights_m: tuple[float, ...] = DEFAULT_TARGET_HEIGHTS_M
) -> dict:
    """The BOM for a tier, with its capability computed from r7.

    ``resolvable`` and ``unresolvable`` are not editorial claims: each
    entry comes from :func:`r7.clocklink.height_resolution` for this
    tier's oscillator and link. If R7's oscillator table changes, this
    table changes with it.
    """
    spec = _check_tier(tier)
    cost = tier_cost(tier)

    heights = {}
    for h in target_heights_m:
        r = clocklink.height_resolution(
            spec["oscillator"], link=spec["link"], target_height_m=h)
        heights[h] = r.as_record()
        heights[h]["limiter"] = clocklink.limiter(spec["oscillator"],
                                                  spec["link"])

    resolvable = [h for h, r in heights.items() if r["resolvable"]]
    unresolvable = [h for h, r in heights.items() if not r["resolvable"]]
    h_min = minimum_resolvable_height_m(tier)

    return _stamp({
        "tier": tier,
        "oscillator": spec["oscillator"],
        "oscillator_spec": clocklink.OSCILLATORS[spec["oscillator"]],
        "link": spec["link"],
        "link_spec": clocklink.TRANSFER_LINKS[spec["link"]],
        "items": cost["items"],
        "total_usd": cost["total_usd"],
        "nominal_budget_usd": spec["budget_usd"],
        "price_basis": PRICE_BASIS,
        "instrument_note": spec["instrument_note"],
        "tic_single_shot_s": spec["tic_single_shot_s"],
        "heights": heights,
        "can_resolve_m": sorted(resolvable),
        "cannot_resolve_m": sorted(unresolvable),
        "minimum_resolvable_height_m": h_min,
        "resolves_one_metre": 1.0 in resolvable,
        "capability_statement": (
            f"this tier's combined floor corresponds to a height "
            f"difference of {h_min:,.4g} m. Anything smaller is "
            f"unreachable at any integration time. Anything larger is "
            f"reachable only after averaging white frequency noise "
            f"down to the floor, which the procedure below budgets "
            f"time for."),
    }, DERIVED)


def bom_report(target_heights_m: tuple[float, ...]
               = DEFAULT_TARGET_HEIGHTS_M) -> dict:
    """All three tiers side by side, plus the headline refusal."""
    tiers = {t: bill_of_materials(t, target_heights_m) for t in TIERS}
    any_metre = [t for t, r in tiers.items() if r["resolves_one_metre"]]
    best_h = min(r["minimum_resolvable_height_m"] for r in tiers.values())
    ceiling = clocklink.ceiling_report()
    return _stamp({
        "tiers": tiers,
        "tiers_resolving_one_metre": any_metre,
        "cheapest_minimum_height_m": best_h,
        "headline": (
            f"no specified tier resolves a one-metre height "
            f"difference. The best of them reaches a floor equivalent "
            f"to roughly {best_h:,.0f} m of height. Spending more "
            f"inside this architecture moves the number but does not "
            f"cross the gap: at the top of the range the transfer "
            f"link, not the oscillator, becomes the limit, and short "
            f"coax cannot be bought out of."),
        "what_it_does_deliver":
            ceiling["what_the_experiment_still_delivers"],
        "claim_ceiling": ceiling["claim_ceiling"],
    }, DERIVED)


# --------------------------------------------------------------------
# 2. Procedure
# --------------------------------------------------------------------

@dataclass(frozen=True)
class Step:
    """One ordered step of the programme.

    ``produces`` is deliberately a *specific number*, not an outcome.
    A step that does not name the number it produces is a step that
    can be declared successful after the fact.
    """

    index: int
    configuration: str
    title: str
    measures: str
    rules_out: str
    duration_h: float
    produces: str
    tiers: tuple[str, ...]
    prerequisite: int | None = None

    def as_record(self) -> dict:
        d = asdict(self)
        d["tiers"] = list(self.tiers)
        return _stamp(d)


PROCEDURE: tuple[Step, ...] = (
    Step(
        index=1,
        configuration="COMMON_SOURCE_SPLIT",
        title="Common-source split: the instrument floor",
        measures=(
            "one oscillator, split into both counter channels through "
            "matched cables. The true frequency difference is "
            "identically zero, so everything recorded is the "
            "measurement chain itself"),
        rules_out=(
            "counter trigger jitter, channel asymmetry, cable delay "
            "drift, ground loops, and the reference distribution — "
            "all of which otherwise masquerade as an oscillator "
            "result in every later step"),
        duration_h=24.0,
        produces=(
            "sigma_y_instrument(tau) over the full tau decade set: the "
            "single number every later claim is divided by"),
        tiers=TIERS,
        prerequisite=None,
    ),
    Step(
        index=2,
        configuration="ONE_SYNTHESIZER_TWO_OUTPUTS",
        title="One synthesizer, two outputs",
        measures=(
            "two outputs derived from a single internal reference. "
            "Any difference is synthesis and output-stage noise, not "
            "oscillator noise"),
        rules_out=(
            "the synthesizer and its output stages as an explanation "
            "for step 3, and separates them from the counter floor "
            "already measured in step 1"),
        duration_h=12.0,
        produces=(
            "sigma_y_synth(tau), and the ratio "
            "sigma_y_synth / sigma_y_instrument, which must exceed 1 "
            "or step 1 was optimistic"),
        tiers=("STANDARD", "GOOD"),
        prerequisite=1,
    ),
    Step(
        index=3,
        configuration="TWO_INDEPENDENT_QUARTZ",
        title="Two independent oscillators",
        measures=(
            "the pair actually under test, each on its own supply, "
            "through the declared transfer link"),
        rules_out=(
            "nothing on its own. Its result is interpretable only "
            "against the step 1 floor, which is why step 1 comes "
            "first and is not optional"),
        duration_h=168.0,
        produces=(
            "sigma_y_pair(tau), the tau at which the curve stops "
            "falling as 1/sqrt(tau), and the flicker floor of the "
            "pair — the number R7's claim ceiling turns on"),
        tiers=TIERS,
        prerequisite=1,
    ),
    Step(
        index=4,
        configuration="DISCIPLINED_VS_HOLDOVER",
        title="Disciplined versus holdover",
        measures=(
            "the same pair with one side GPS-disciplined and the "
            "other free-running, then the disciplined side placed "
            "into deliberate holdover"),
        rules_out=(
            "the discipline loop itself as a source of structure. A "
            "GPSDO's loop bandwidth writes a visible bump into the "
            "Allan curve, and a programme that has not seen that bump "
            "in its own hardware will eventually mistake it for a "
            "result"),
        duration_h=72.0,
        produces=(
            "the loop time constant in seconds, read off the ADEV "
            "bump, and the holdover drift rate in s/day"),
        tiers=("STANDARD", "GOOD"),
        prerequisite=3,
    ),
    Step(
        index=5,
        configuration="APPARATUS_IN_TRANSFER_PATH",
        title="Apparatus inserted in the transfer path",
        measures=(
            "the step 3 configuration with the apparatus under study "
            "physically present in the path"),
        rules_out=(
            "nothing yet. It is the exposed arm and is meaningless "
            "without step 6"),
        duration_h=168.0,
        produces=(
            "sigma_y_exposed(tau), to be compared only against the "
            "sham of step 6 and never against step 3 alone"),
        tiers=("STANDARD", "GOOD"),
        prerequisite=4,
    ),
    Step(
        index=6,
        configuration="SHAM_INSERTION",
        title="Sham insertion: the blank",
        measures=(
            "an inert object of the same mass, thermal load and "
            "geometry in the same position, with the same cabling "
            "disturbed the same way"),
        rules_out=(
            "the insertion itself — handling, thermal mass, airflow "
            "obstruction, cable re-routing. In practice this is where "
            "most apparent effects go to die, which is why the sham "
            "is scheduled as a step and not as a courtesy"),
        duration_h=168.0,
        produces=(
            "sigma_y_sham(tau) and the exposed-minus-sham difference "
            "with its confidence interval"),
        tiers=("STANDARD", "GOOD"),
        prerequisite=5,
    ),
    Step(
        index=7,
        configuration="SIMULATED_HEIGHT_PERTURBATION",
        title="Simulated height perturbation: the positive control",
        measures=(
            "a known fractional frequency offset injected by "
            "calibrated means, sized to the height the tier can "
            "actually resolve"),
        rules_out=(
            "the possibility that the chain would fail to see a real "
            "effect of the claimed size. A null result from a chain "
            "with no demonstrated positive control is not a null "
            "result; it is an untested apparatus"),
        duration_h=48.0,
        produces=(
            "the recovered offset against the injected offset, and "
            "the smallest injection recovered at 3 sigma"),
        tiers=TIERS,
        prerequisite=1,
    ),
    Step(
        index=8,
        configuration="REAL_HEIGHT_COMPARISON",
        title="Real height comparison",
        measures=(
            "the pair separated by a surveyed vertical distance "
            "exceeding the tier's minimum resolvable height, with the "
            "link extended and re-characterized"),
        rules_out=(
            "nothing that steps 1-7 have not already ruled out. It is "
            "gated on step 7 succeeding and on the separation being "
            "larger than the computed minimum, which for every tier "
            "specified here means a hillside rather than a building"),
        duration_h=336.0,
        produces=(
            "the fractional offset against the surveyed height, and "
            "the residual against g*dh/c^2"),
        tiers=("GOOD",),
        prerequisite=7,
    ),
)


def procedure(tier: str | None = None) -> dict:
    """The ordered procedure, optionally filtered to one tier.

    Ordering is not cosmetic. Step 1 is first because every later
    number is reported as a ratio against it, and a programme that
    runs the interesting configuration first has no denominator.
    """
    steps = PROCEDURE
    if tier is not None:
        _check_tier(tier)
        steps = tuple(s for s in PROCEDURE if tier in s.tiers)

    total_h = sum(s.duration_h for s in steps)
    return _stamp({
        "tier": tier,
        "n_steps": len(steps),
        "steps": [s.as_record() for s in steps],
        "first_step": steps[0].configuration if steps else None,
        "total_duration_h": total_h,
        "total_duration_days": total_h / 24.0,
        "excluded_for_tier": [
            s.configuration for s in PROCEDURE if s not in steps],
        "ordering_rationale": (
            "the common-source split is step 1 because it is the only "
            "configuration whose true answer is known in advance — "
            "zero — and therefore the only one that measures the "
            "measurement chain. Every subsequent result is reported "
            "as a ratio against it. Running steps out of order does "
            "not merely waste time; it produces numbers with no "
            "denominator, which are unfalsifiable rather than wrong."),
    }, DERIVED)


# --------------------------------------------------------------------
# 3. Expected floor
# --------------------------------------------------------------------

#: Decade-spaced averaging times the programme reports at.
DEFAULT_TAUS_S = (1.0, 10.0, 100.0, 1_000.0, 10_000.0, 100_000.0)


def _instrument_adev(single_shot_s: float, tau_s: float) -> float:
    """White phase-modulation floor from a time-interval counter.

    Two independent single-shot readings bound each interval, so the
    time-error uncertainty is sqrt(2)*sigma_x and the resulting Allan
    deviation falls as 1/tau — faster than the 1/sqrt(tau) of white
    FM. That difference in slope is how the two are told apart on a
    real plot, and it is why a poor counter stops mattering if you are
    patient enough.
    """
    if tau_s <= 0:
        raise ValueError("averaging time must be positive")
    return math.sqrt(2.0) * single_shot_s / tau_s


def expected_floor(tier: str,
                   taus_s: tuple[float, ...] = DEFAULT_TAUS_S) -> dict:
    """Predicted floor for a tier, with the dominant term named at each tau.

    Three terms compete and the winner changes with tau:

    * the counter's white PM noise, falling as 1/tau;
    * the oscillator pair's white FM noise, falling as 1/sqrt(tau);
    * the oscillator pair's flicker floor, falling not at all.

    Naming the winner per tau is the useful output. A programme that
    quotes a single "floor" has either not looked at short tau or has
    not looked at long tau.
    """
    spec = _check_tier(tier)
    osc = clocklink.OSCILLATORS[spec["oscillator"]]
    link_floor = clocklink.TRANSFER_LINKS[spec["link"]]["frac_uncertainty"]

    # two nominally identical devices: terms add in quadrature
    pair_adev_1s = osc["adev_1s"] * math.sqrt(2)
    pair_floor = osc["flicker_floor"] * math.sqrt(2)
    sigma_x = spec["tic_single_shot_s"]

    rows = []
    for tau in taus_s:
        instr = _instrument_adev(sigma_x, tau)
        white_fm = pair_adev_1s / math.sqrt(tau)
        terms = {
            "COUNTER_WHITE_PM": instr,
            "OSCILLATOR_WHITE_FM": white_fm,
            "OSCILLATOR_FLICKER_FLOOR": pair_floor,
            "TRANSFER_LINK": link_floor,
        }
        dominant = max(terms, key=terms.__getitem__)
        rows.append({
            "tau_s": tau,
            "terms": terms,
            "dominant_term": dominant,
            "dominant_value": terms[dominant],
            # quadrature sum, since the terms are independent
            "total_adev": math.sqrt(sum(v * v for v in terms.values())),
        })

    # tau at which the counter stops being the limit: solve
    # sqrt(2)*sigma_x/tau = max(oscillator floor, link floor)
    osc_side = max(pair_floor, link_floor)
    crossover = math.sqrt(2.0) * sigma_x / osc_side
    instrument_limited_at_1s = _instrument_adev(sigma_x, 1.0) > (
        max(pair_adev_1s, osc_side))

    return _stamp({
        "tier": tier,
        "oscillator": spec["oscillator"],
        "link": spec["link"],
        "tic_single_shot_s": sigma_x,
        "pair_adev_1s": pair_adev_1s,
        "pair_flicker_floor": pair_floor,
        "link_floor": link_floor,
        "rows": rows,
        "instrument_limited_at_1s": instrument_limited_at_1s,
        "instrument_crossover_tau_s": crossover,
        "asymptotic_floor": math.sqrt(pair_floor ** 2 + link_floor ** 2),
        "dominant_terms_seen": sorted({r["dominant_term"] for r in rows}),
        "note": (
            f"below tau = {crossover:.3g} s this tier measures its own "
            f"counter. Above it, the oscillators. A run shorter than "
            f"the crossover characterises the instrument and should "
            f"be reported as such rather than as an oscillator "
            f"result."),
    }, DERIVED)


def floor_report(taus_s: tuple[float, ...] = DEFAULT_TAUS_S) -> dict:
    """Expected floors for all three tiers."""
    return _stamp({
        "tiers": {t: expected_floor(t, taus_s) for t in TIERS},
        "note": (
            "the crossover time falls by roughly the ratio of counter "
            "resolutions between tiers. Most of what the higher tiers "
            "buy at short tau is counter, not oscillator."),
    }, DERIVED)


# --------------------------------------------------------------------
# 4. Analysis plan — frozen before data
# --------------------------------------------------------------------

def analysis_plan(tier: str = "STANDARD") -> dict:
    """The analysis plan, frozen internally before any data exists.

    R8-D-004: this is an **INTERNAL_ANALYSIS_FREEZE**, not
    preregistration. No third-party registry holds a copy, nobody
    outside this repository can verify the freeze date independently,
    and `r6.bench` correctly records PREREGISTERED_ANALYSIS as ABSENT.
    The word "frozen" describes this module's content and must not be
    read as an external commitment.

    Frozen, and frozen *now*, because the freeze is worthless the
    moment a single point has been seen. An Allan deviation plot is
    unusually easy to argue with after the fact: the analyst chooses
    the tau window, the estimator (ADEV, MDEV, TDEV, Hadamard), the
    outlier rule and the run length, and each choice moves the curve.
    Choosing them while looking at the data is not fraud and does not
    feel like fraud, which is exactly why it has to be prevented
    structurally rather than by intention.

    Three estimators are specified together because they discriminate
    noise types that a single one confounds:

    * **ADEV** — the headline curve, but it cannot separate white PM
      from flicker PM: both appear with slope -1.
    * **MDEV** — modified Allan deviation, which does separate them
      (-3/2 versus -1) and is therefore the estimator that tells you
      whether the counter or the distribution chain is the limit.
    * **TDEV** — time deviation, reported because time error, not
      fractional frequency, is the quantity a downstream user cares
      about.
    """
    spec = _check_tier(tier)
    floor = expected_floor(tier)
    run_s = 168.0 * 3600.0        # the step 3 duration, in seconds

    return _stamp({
        "freeze_status": "INTERNAL_ANALYSIS_FREEZE",
        "externally_preregistered": False,
        "freeze_caveat": (
            "frozen in-repository only; no third-party registration exists and none is claimed"),
        "frozen_before_data": True,
        "freeze_statement": (
            "This analysis is FROZEN. It is recorded before any datum "
            "exists, and it is recorded because no measurement has "
            "been taken — a freeze declared after first sight of the "
            "data is not a freeze. Any deviation from this plan must "
            "be reported as a deviation, with its effect on the "
            "result stated, and the preregistered analysis must be "
            "reported alongside it."),
        "why_frozen": (
            "the tau window, the estimator and the run length are all "
            "analyst choices that move an Allan curve. Chosen after "
            "seeing the data, they convert a null into whatever was "
            "wanted, without anyone experiencing themselves as "
            "dishonest."),
        "tier": tier,
        "estimators": {
            "ADEV": {
                "name": "overlapping Allan deviation",
                "implementation": "r7.clocklink.overlapping_adev",
                "role": "headline stability curve",
                "limitation": "cannot separate white PM from flicker "
                              "PM; both show slope -1",
            },
            "MDEV": {
                "name": "modified Allan deviation",
                "role": "noise-type discrimination at short tau",
                "discriminates": "white PM (slope -3/2) from flicker "
                                 "PM (slope -1)",
            },
            "TDEV": {
                "name": "time deviation",
                "relation": "TDEV(tau) = tau * MDEV(tau) / sqrt(3)",
                "role": "reports time error, the quantity a "
                        "downstream user actually consumes",
            },
        },
        "tau_range": {
            "tau0_s": 1.0,
            "spacing": "octave (2^k * tau0), reported to the largest "
                       "octave not exceeding tau_max",
            "tau_max_s": run_s / 5.0,
            "tau_max_rule": (
                "tau_max = T_run / 5. Beyond roughly a fifth of the "
                "run the estimator has too few independent samples "
                "and the confidence interval swamps the point. "
                "Extending the plotted range past this is the most "
                "common way an Allan plot is made to show a downturn "
                "that is not there."),
            "run_duration_s": run_s,
        },
        "pass_criteria": {
            "instrument_separation": (
                "sigma_y_pair(tau) must exceed sigma_y_instrument(tau) "
                "by a factor of at least 10 across the reported tau "
                "range. Below that the result is an instrument "
                "characterisation and must be reported as one"),
            "positive_control": (
                "step 7 must recover an injected offset within 3 "
                "sigma at the tier's minimum resolvable size, or no "
                "null from steps 5-6 is reportable"),
            "sham_difference": (
                "any exposed-minus-sham difference must exceed the "
                "combined uncertainty by 5 sigma and must reproduce "
                "in an independent run before it is described as an "
                "effect. 3 sigma is a hint, not a result"),
            "environmental_covariance": (
                "the residual must show no correlation with logged "
                "temperature or supply voltage above |r| = 0.3; if it "
                "does, the covariate is regressed out and BOTH the "
                "raw and corrected results are reported"),
            "expected_outcome": (
                f"the predicted asymptotic floor for this tier is "
                f"{floor['asymptotic_floor']:.3g}, corresponding to "
                f"{minimum_resolvable_height_m(tier):,.4g} m of "
                f"height. The preregistered expectation is a NULL for "
                f"any height claim below that, and the programme "
                f"commits to publishing that null."),
        },
        "stopping_rule": {
            "rule": (
                "each configuration runs for its scheduled duration "
                "in the procedure table, decided in advance. The run "
                "stops early only for a declared fault — mains "
                "interruption, oven unlock, logger gap exceeding 5 "
                "percent of the block, or an environmental excursion "
                "outside the declared bounds — and a fault-stopped "
                "block is discarded whole and repeated, never "
                "truncated and analysed"),
            "forbidden": (
                "the run may NOT be stopped because the result looks "
                "good, because it looks bad, because the curve has "
                "'settled', or because a difference has reached a "
                "significance threshold. Optional stopping on a "
                "significance threshold guarantees eventual "
                "significance from pure noise; that is the failure "
                "mode this rule exists to prevent"),
            "extension": (
                "a run may be extended only if the extension is "
                "declared before the original run ends, and the "
                "analysis is then reported at both the original and "
                "the extended duration"),
            "scheduled_durations_h": {
                s.configuration: s.duration_h for s in PROCEDURE},
        },
        "outlier_policy": (
            "points are removed only for a documented physical cause "
            "recorded in the operator log at the time — never on "
            "statistical grounds alone. The count and fraction of "
            "removed points is reported with every curve."),
        "blinding": (
            "exposed and sham blocks are labelled by an assistant and "
            "unblinded only after the analysis script has been run "
            "and its output committed. If no assistant is available, "
            "block labels are hashed and the hash committed before "
            "analysis."),
        "data_management": (
            "raw counter output, environmental logs and operator "
            "notes are committed unmodified with checksums before any "
            "analysis is run. The analysis script is committed before "
            "the data."),
    }, EVIDENCE_CLASS)


# --------------------------------------------------------------------
# 5. Refusal
# --------------------------------------------------------------------

def refuse_measured_claim(*args, **kwargs):
    """Refuse to treat anything in this module as a measurement.

    Every number here is either a catalogue estimate or arithmetic
    over one. There is no reading, no instrument, and no data file.
    """
    raise MeasurementRefused(
        "No value in r8.measurement is a measurement. This module "
        "specifies a clock-link programme: a bill of materials, an "
        "ordered procedure, a predicted floor and a frozen analysis "
        "plan. RGCS owns no oscillator, no counter and no logger, has "
        "compared no clock pair, and has recorded no phase. The "
        "evidence classes BENCH_MEASUREMENT and "
        "INDEPENDENT_REPLICATION are closed to this programme.")


# --------------------------------------------------------------------
# 6. Operator workbench
# --------------------------------------------------------------------

def operator_workbench(tier: str = "STANDARD") -> dict:
    """A checklist an operator could actually follow.

    Written at the level of "do this, write this down", because a
    procedure that says "log the environment" and does not say which
    channels at what cadence will be followed differently by every
    operator and by the same operator on different days.
    """
    spec = _check_tier(tier)
    steps = [s for s in PROCEDURE if tier in s.tiers]
    floor = expected_floor(tier)

    return _stamp({
        "tier": tier,
        "sections": {
            "A_BEFORE_POWER_ON": [
                "Record the date, operator name, and the git commit "
                "of the analysis script. The script is committed "
                "before the data, not after.",
                "Photograph the bench layout and cable routing. "
                "Routing must not change between blocks; if it does, "
                "the block is a new configuration.",
                "Record every serial number: oscillators, counter, "
                "distribution amplifier, supply.",
                "Record the counter's last calibration date, or "
                "record explicitly that it has none. 'Unknown' is a "
                "valid entry; blank is not.",
                "Confirm all cables are the declared phase-stable set "
                "and record their lengths.",
            ],
            "B_WARMUP": [
                f"Power the {spec['oscillator']} units and leave them "
                f"undisturbed. Do not begin logging yet.",
                "OCXO and rubidium units require a minimum of 24 h "
                "from cold before any block is started. Retrace after "
                "a power cycle is a real and specified effect; a unit "
                "power-cycled mid-programme restarts its 24 h clock.",
                "Record the time of power-on and the time of first "
                "logged sample separately.",
            ],
            "C_ENVIRONMENTAL_LOGGING": [
                "Ambient temperature at the bench, 1-minute cadence, "
                "logged continuously for the whole block including "
                "warmup.",
                "Oscillator case temperature, one probe per unit, "
                "1-minute cadence.",
                "Cable-run temperature, one probe at the midpoint of "
                "the longest run.",
                "Supply voltage on every rail, 1-minute cadence. "
                "Supply pushing is a datasheet parameter and cannot "
                "be subtracted if it was not recorded.",
                "Relative humidity and, for the GOOD tier, barometric "
                "pressure.",
                "Door openings, HVAC cycles, and anyone entering the "
                "room, by hand in the operator log with timestamps. "
                "These correlate with the temperature record and are "
                "how an unexplained step gets explained.",
                "A logger gap exceeding 5 percent of a block "
                "invalidates that block under the stopping rule.",
            ],
            "D_SHAM_AND_BLANK_CONDITIONS": [
                "BLANK (step 1): one oscillator split to both counter "
                "channels. The true difference is exactly zero. Any "
                "structure recorded here is instrumental and is "
                "subtracted from nothing — it is the denominator.",
                "SHAM (step 6): inert object matched in mass, "
                "external geometry and thermal load, in the same "
                "position, handled the same way, with the same cables "
                "disturbed and re-seated.",
                "The sham must be inserted and removed the same "
                "number of times as the real article, by the same "
                "person, at the same times of day.",
                "Sham and exposed blocks are interleaved, never run "
                "as two consecutive halves. A slow thermal drift "
                "across a day maps perfectly onto a two-block design "
                "and will produce a difference from nothing.",
                "Block labels are sealed or hashed before analysis "
                "per the blinding clause of the analysis plan.",
            ],
            "E_DURING_THE_RUN": [
                "Do not touch the bench. Do not re-seat a connector. "
                "Do not 'just check' a reading on a different "
                "instrument.",
                "If anything is touched, log it with a timestamp. An "
                "unlogged disturbance is worse than a logged one "
                "because it is indistinguishable from a result.",
                f"Expect the counter to dominate below tau = "
                f"{floor['instrument_crossover_tau_s']:.3g} s. Data "
                f"shorter than that characterises the instrument.",
                "Check logger continuity once per day by reading the "
                "file size, not by opening and inspecting the data. "
                "Do not plot the data during the run.",
            ],
            "F_END_OF_BLOCK": [
                "Stop at the scheduled duration. Record the actual "
                "stop time and the reason, which must be 'scheduled' "
                "or a declared fault.",
                "Checksum the raw files and commit them unmodified "
                "before running any analysis.",
                "Write the operator log entry before looking at any "
                "curve.",
            ],
            "G_ANALYSIS": [
                "Run the committed analysis script unmodified.",
                "Report ADEV, MDEV and TDEV over the preregistered "
                "tau range only.",
                "Report the ratio to the step 1 instrument floor at "
                "every tau.",
                "Report the count and fraction of removed points, "
                "with the physical cause logged for each.",
                "If the plan was deviated from, report the deviation "
                "and both analyses.",
            ],
        },
        "steps_for_tier": [s.index for s in steps],
        "total_bench_time_days": sum(s.duration_h for s in steps) / 24.0,
        "competence_note": (
            "Nothing in this checklist requires mains-side work. If a "
            "build step would require it, it must be performed by a "
            "qualified person to the local electrical code; this "
            "programme does not specify one."),
        "standing_refusal": (
            "This workbench is a specification. No operator has "
            "followed it, no block has been run, and no log exists."),
    }, EVIDENCE_CLASS)


def programme_summary() -> dict:
    """The P11 certificate: everything above, in one object."""
    return _stamp({
        "phase": "P11",
        "programme_id": "RGCS-V5.1-R8.1",
        "bom": bom_report(),
        "procedure": procedure(),
        "floors": floor_report(),
        "analysis_plan_frozen": analysis_plan()["frozen"],
        "status": "PROGRAMME_SPECIFIED_PHYSICALLY_UNTESTED",
        "statement": (
            "P11 specifies the first reachable physical measurement "
            "lane and stops there. The specification is complete "
            "enough to price, order and follow. It has not been "
            "priced, ordered or followed."),
    }, DERIVED)
