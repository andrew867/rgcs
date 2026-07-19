"""P08 — R7 bench hardware, priority, hazards, and dual-use policy.

Named ``benchr7`` rather than ``bench`` so that it cannot be confused
with, or shadow, :mod:`r6.bench`. It reuses R6's readiness-gate
vocabulary deliberately: the gates did not get easier between
programmes, and R7 must be judged against the same list.

R7 is still a software programme. It owns no instrument, holds no
calibration certificate, has no institutional safety reviewer, and has
taken no reading. Everything below is a *design* and a *costing*, and
every figure is a catalogue-class estimate — the kind of number a
reader could check against a distributor's price list — never a quote,
never an invoice, never a measurement.

The one thing this module is willing to be assertive about is
priority. R6 closed by recommending the two-oscillator comparison, and
the ranking in :func:`priority_ranking` puts it first on arithmetic
rather than on taste: it is the cheapest experiment in the set by an
order of magnitude, it exercises the entire phase-transfer chain that
every other measurement would depend on, and its claim ceiling is the
only one in the programme that is actually reachable with equipment a
private person can buy.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, field

from r6.bench import READINESS_GATES

#: Safety classes used by the experiment registry, ordered from the
#: benign to the one this programme will not run.
SAFETY_CLASSES = (
    "BENIGN_LOW_VOLTAGE",
    "CONTROLLED_OPTICAL",
    "CONTROLLED_ACOUSTIC",
    "CONTROLLED_HIGH_VOLTAGE",
    "CONTROLLED_VACUUM",
    "REQUIRES_QUALIFIED_PERSON",
)


class BenchRefused(RuntimeError):
    """Raised when a bench request is refused on policy grounds."""


# --------------------------------------------------------------------
# 1. The experiment registry
# --------------------------------------------------------------------

@dataclass(frozen=True)
class Experiment:
    """One candidate R7 experiment, costed and classified.

    ``cost_low_usd`` and ``cost_high_usd`` bracket a catalogue-class
    estimate for the marginal hardware, assuming a bench, a mains
    supply, a soldering iron and a computer already exist. They exclude
    labour, shipping, tax, and the cost of the first attempt failing,
    which in practice is the largest term.

    ``information_score`` is a declared 0-10 judgement of how much the
    experiment would settle, not a measured quantity. It is stated
    explicitly so that the ranking can be argued with rather than
    merely accepted.
    """

    id: str
    tests: str
    hardware: tuple[str, ...]
    cost_low_usd: float
    cost_high_usd: float
    safety_class: str
    hobbyist_achievable: bool
    information_score: float
    score_rationale: str
    claim_ceiling: str
    notes: str = ""

    def __post_init__(self):
        if self.safety_class not in SAFETY_CLASSES:
            raise ValueError(
                f"unknown safety class {self.safety_class!r}")
        if not 0.0 <= self.information_score <= 10.0:
            raise ValueError("information_score must be in [0, 10]")
        if self.cost_low_usd <= 0 or self.cost_high_usd < self.cost_low_usd:
            raise ValueError("cost band must be positive and ordered")

    @property
    def cost_mid_usd(self) -> float:
        """Geometric mean of the band.

        Geometric rather than arithmetic because these bands span
        factors of three to eight, and the arithmetic mean of such a
        band sits far too close to the top of it.
        """
        return (self.cost_low_usd * self.cost_high_usd) ** 0.5

    @property
    def information_per_kilodollar(self) -> float:
        return self.information_score / (self.cost_mid_usd / 1000.0)

    def as_record(self) -> dict:
        d = asdict(self)
        d["hardware"] = list(self.hardware)
        d["cost_mid_usd"] = self.cost_mid_usd
        d["information_per_kilodollar"] = self.information_per_kilodollar
        d["cost_basis"] = ("catalogue-class estimate, marginal "
                           "hardware only; not a quotation")
        return d


#: The R7 experiment set. Costs are catalogue-class estimates in USD
#: at pack time; instrument specifications are catalogue-class as well.
#: Nothing here has been purchased.
EXPERIMENTS: dict[str, Experiment] = {
    "CLOCK_LINK_BASELINE": Experiment(
        id="CLOCK_LINK_BASELINE",
        tests=("whether the whole phase-transfer and comparison chain "
               "measures what it claims to, using a source that is "
               "known to be common. One oscillator split two ways must "
               "read as zero differential drift; anything else is the "
               "measurement system's own noise floor, and finding it "
               "is the point."),
        hardware=(
            "one OCXO or synthesizer, 10 MHz",
            "resistive or hybrid two-way splitter",
            "frequency counter or time-interval counter with an "
            "external reference input, 100 ps class or better",
            "two temperature loggers (oscillator case and room)",
            "logging host and a coaxial set matched in length",
        ),
        cost_low_usd=400.0, cost_high_usd=2_000.0,
        safety_class="BENIGN_LOW_VOLTAGE",
        hobbyist_achievable=True,
        information_score=9.0,
        score_rationale=(
            "it is the only experiment in the set that can return a "
            "definite, interpretable answer with equipment a private "
            "person can buy, and every other clock measurement is "
            "uninterpretable until it has been run. A common-source "
            "split has a known correct answer, so it validates the "
            "instrument rather than the hypothesis, which is exactly "
            "what should come first."),
        claim_ceiling=("a characterized differential noise floor for "
                       "the link; no claim about any coordinate "
                       "system follows from it"),
        notes=("the priority experiment, carried forward unchanged "
               "from the R6 closing recommendation"),
    ),
    "CLOCK_LINK_INDEPENDENT": Experiment(
        id="CLOCK_LINK_INDEPENDENT",
        tests=("whether two independently disciplined oscillators show "
               "any differential behaviour beyond the floor measured "
               "by the baseline experiment, with every environmental "
               "nuisance channel logged alongside"),
        hardware=(
            "two independent OCXOs, ideally different manufacturers",
            "time-interval counter or dual-mixer time-difference "
            "arrangement",
            "temperature, humidity and supply-voltage logging on both "
            "units",
            "three-axis magnetometer for a nuisance channel",
            "optional GPSDO as a common long-term reference",
        ),
        cost_low_usd=1_500.0, cost_high_usd=9_000.0,
        safety_class="BENIGN_LOW_VOLTAGE",
        hobbyist_achievable=True,
        information_score=8.0,
        score_rationale=(
            "this is the experiment the programme actually wants, but "
            "its result is meaningless without the baseline: any "
            "differential it reports is indistinguishable from the "
            "measurement chain's own drift until that drift has been "
            "bounded separately."),
        claim_ceiling=("a bounded differential between two oscillators "
                       "with declared environmental covariates"),
        notes="strictly downstream of CLOCK_LINK_BASELINE",
    ),
    "DIRECTIONAL_FIELD_MAP": Experiment(
        id="DIRECTIONAL_FIELD_MAP",
        tests=("whether the field produced by a commanded geometry "
               "points where r7.vectorfield says it should. This tests "
               "the wiring and the compiler, and it is worth doing for "
               "that reason alone."),
        hardware=(
            "three-axis fluxgate or Hall magnetometer with a declared "
            "bandwidth and noise floor",
            "manual or motorized three-axis positioning stage",
            "non-magnetic fixturing (brass, aluminium, polymer)",
            "two-channel drive amplifier with independent phase "
            "control",
            "Helmholtz pair or mu-metal shield for background "
            "rejection",
        ),
        cost_low_usd=2_000.0, cost_high_usd=15_000.0,
        safety_class="BENIGN_LOW_VOLTAGE",
        hobbyist_achievable=True,
        information_score=5.0,
        score_rationale=(
            "a confirmed map would show the coils are wired as drawn "
            "and that realized direction tracks requested direction "
            "within the declared channel error. That is a genuine and "
            "checkable result. It is also, by r7.vectorfield's central "
            "argument, not evidence of anything beyond correct "
            "wiring."),
        claim_ceiling=("agreement between commanded and measured field "
                       "direction; explicitly not a force result"),
        notes=("the cheapest way to falsify the compiler; it cannot "
               "support any claim about thrust or metric effects"),
    ),
    "CRYSTAL_ALIGNMENT": Experiment(
        id="CRYSTAL_ALIGNMENT",
        tests=("whether a specimen's optic axis can be located to a "
               "declared angular uncertainty, and whether that "
               "uncertainty is small enough for any downstream "
               "orientation claim to mean anything"),
        hardware=(
            "conoscopic polariscope or polarizing microscope with a "
            "Bertrand lens",
            "electronic autocollimator, arcsecond class",
            "two-axis goniometer or tilt stage with a declared "
            "repeatability",
            "specimen mounts that do not stress the crystal",
            "reference flat and a calibration artifact",
        ),
        cost_low_usd=3_000.0, cost_high_usd=25_000.0,
        safety_class="CONTROLLED_OPTICAL",
        hobbyist_achievable=False,
        information_score=5.0,
        score_rationale=(
            "alignment uncertainty is the term that propagates into "
            "every orientation-dependent claim the programme might "
            "make, so bounding it is genuinely useful. But it bounds "
            "an error bar; it cannot confirm or refute any hypothesis "
            "on its own."),
        claim_ceiling=("a stated angular uncertainty on the optic "
                       "axis, traceable to a calibration artifact"),
        notes=("second-hand autocollimators bring the low end down; "
               "the calibration artifact is the part that is hard to "
               "obtain honestly"),
    ),
    "NONCONTACT_EXCITATION": Experiment(
        id="NONCONTACT_EXCITATION",
        tests=("whether a specimen driven without mechanical contact "
               "shows forced response and ringdown consistent with a "
               "passive resonator, and whether any observation "
               "survives the contact-loading and loop-gain firewall of "
               "core/05"),
        hardware=(
            "electrostatic drive electrode with a high-voltage "
            "amplifier, or an air-coupled ultrasonic transducer",
            "laser Doppler vibrometer or a homodyne interferometric "
            "pickup",
            "vacuum or acoustically isolated enclosure",
            "low-loss specimen suspension (thread, knife-edge or "
            "electrostatic)",
            "digitizer with the bandwidth to capture ringdown",
        ),
        cost_low_usd=8_000.0, cost_high_usd=60_000.0,
        safety_class="CONTROLLED_HIGH_VOLTAGE",
        hobbyist_achievable=False,
        information_score=6.0,
        score_rationale=(
            "this is the experiment that would settle the "
            "self-oscillation question, which is a real question. It "
            "is expensive because the vibrometer is expensive, and a "
            "cheaper pickup would reintroduce the contact loading the "
            "experiment exists to eliminate."),
        claim_ceiling=("a measured Q and ringdown time under declared "
                       "drive; a passive-self-oscillation claim "
                       "remains refused regardless of outcome"),
        notes=("the high-voltage electrode and the enclosure are both "
               "load-bearing for safety, not optional economies"),
    ),
    "FORCE_NULL": Experiment(
        id="FORCE_NULL",
        tests=("whether any force appears on a driven apparatus above "
               "the confound budget in r7.vectorfield.force_null_design"),
        hardware=(
            "torsion balance with a fine fibre and a mass-matched "
            "dummy arm",
            "vacuum chamber and pump reaching below 1e-3 Pa",
            "optical-lever or interferometric angle readout with an "
            "in-situ electrostatic calibration",
            "grounded conductive shield and non-magnetic fixturing",
            "environmental logging: temperature, pressure, magnetic "
            "field, seismic",
            "vibration isolation table",
        ),
        cost_low_usd=15_000.0, cost_high_usd=120_000.0,
        safety_class="CONTROLLED_VACUUM",
        hobbyist_achievable=False,
        information_score=4.0,
        score_rationale=(
            "the expected result is a bounded null, which is worth "
            "having and is worth much less than its cost. Worse, it is "
            "the experiment most likely to produce a spurious positive "
            "for a builder without vacuum and electrostatic discipline "
            "-- so its expected information is reduced by the "
            "probability that it misleads."),
        claim_ceiling=("an upper bound on force under declared "
                       "conditions; a bounded null is the expected and "
                       "publishable outcome"),
        notes=("ranked last on information per dollar, and that "
               "ranking is not a comment on whether the question "
               "matters"),
    ),
}


# --------------------------------------------------------------------
# 2. Readiness
# --------------------------------------------------------------------

@dataclass
class R7Readiness:
    gates_open: tuple[str, ...] = ()
    evidence: dict = field(default_factory=dict)

    def missing(self) -> tuple[str, ...]:
        return tuple(g for g in READINESS_GATES
                     if g not in self.gates_open)

    def as_record(self) -> dict:
        d = asdict(self)
        d["gates_open"] = list(self.gates_open)
        d["missing"] = list(self.missing())
        d["ready"] = not self.missing()
        return d


def current_assessment() -> R7Readiness:
    """R7's honest gate state.

    The pattern is R6's and the reason is R6's: gates that can be
    satisfied by writing something down are open, and gates that
    require an object, a person or an institution are shut, because R7
    acquired none of those.
    """
    return R7Readiness(
        gates_open=(
            "APPARATUS_SPECIFIED",
            "INSTRUMENT_MATRIX_COMPLETE",
            "CONTROL_DESIGN",
            "STOPPING_RULE",
        ),
        evidence={
            "APPARATUS_SPECIFIED":
                "EXPERIMENTS in this module: six experiments with "
                "hardware lists, cost bands and safety classes",
            "INSTRUMENT_MATRIX_COMPLETE":
                "each experiment declares the instruments it needs "
                "and the nuisance channels that must be logged",
            "CONTROL_DESIGN":
                "r7.vectorfield.THRUST_CONFOUNDS and force_null_design "
                "specify sham, reversal, thermal, electrostatic, "
                "magnetic, tether and buoyancy controls",
            "STOPPING_RULE":
                "honest_stop() in this module; the programme stops at "
                "the last real capability",
            "CALIBRATION_PLAN":
                "ABSENT: R7 owns no instrument, so there is no "
                "calibration certificate and no traceability chain",
            "BLINDING_PROTOCOL":
                "PARTIAL: force_null_design specifies interleaved "
                "blinded conditions, but no protocol is registered "
                "and no one exists to hold the key. Counted as shut.",
            "PREREGISTERED_ANALYSIS":
                "ABSENT: nothing registered with any third party",
            "SAFETY_REVIEW":
                "ABSENT: no reviewer, no institution. The hazard table "
                "here is a self-assessment, which is not a review.",
            "OPERATOR_COMPETENCE":
                "ABSENT: not assessed. High voltage, vacuum and "
                "mains work each require a qualified person.",
            "DATA_MANAGEMENT_PLAN":
                "ABSENT: no data exists to manage",
        })


def readiness() -> dict:
    """The P08 readiness statement. Reports not-ready, honestly."""
    a = current_assessment()
    return {
        "programme": "RGCS-V5.0-R7",
        "gates_total": len(READINESS_GATES),
        "gates_open": len(a.gates_open),
        "gates_missing": list(a.missing()),
        "ready_for_bench": False,
        "status": "SOFTWARE_COMPLETE_PHYSICALLY_UNTESTED",
        "evidence": a.evidence,
        "hazards": HAZARDS,
        "hazards_refused": [k for k, v in HAZARDS.items()
                            if v["status"].startswith("REFUSED")],
        "instruments_owned": 0,
        "calibration_certificates_held": 0,
        "measurements_taken": 0,
        "statement": (
            "R7 owns no hardware. The calibration, safety-review and "
            "operator-competence gates are therefore shut and cannot "
            "be opened by any amount of further writing. Bench "
            "readiness here describes documentation completeness and "
            "says nothing whatsoever about the physical world."),
    }


# --------------------------------------------------------------------
# 3. Priority
# --------------------------------------------------------------------

def priority_ranking() -> dict:
    """Rank the experiment set by information per dollar.

    The metric is ``information_score / (cost_mid_usd / 1000)``, with
    ``cost_mid_usd`` the geometric mean of the declared band. Both
    inputs are declared and arguable: the score is a judgement stated
    on the record, and the cost is a catalogue-class estimate. The
    ranking is deterministic given those two numbers, and ties break on
    the experiment id so the order never depends on dictionary
    insertion or on any hash.

    The clock-link baseline wins by a wide margin and would win under
    almost any plausible re-scoring, which is the useful property: at a
    geometric-mean cost near 900 USD against roughly 42 000 USD for the
    torsion balance, the baseline would have to be nearly fifty times
    less informative to lose, and it is more informative, not less.
    """
    rows = sorted(
        (e.as_record() for e in EXPERIMENTS.values()),
        key=lambda r: (-r["information_per_kilodollar"], r["id"]))
    for i, r in enumerate(rows, start=1):
        r["rank"] = i

    order = [r["id"] for r in rows]
    first, second = rows[0], rows[1]
    last = rows[-1]
    return {
        "metric": "information_score / (cost_mid_usd / 1000 USD)",
        "metric_inputs_are_judgements": True,
        "ranking": order,
        "rows": rows,
        "top": order[0],
        "margin_over_second": (
            first["information_per_kilodollar"]
            / second["information_per_kilodollar"]),
        "margin_over_last": (
            first["information_per_kilodollar"]
            / last["information_per_kilodollar"]),
        "justification": (
            f"{first['id']} scores "
            f"{first['information_per_kilodollar']:.2f} against "
            f"{second['information_per_kilodollar']:.2f} for "
            f"{second['id']} and "
            f"{last['information_per_kilodollar']:.3f} for "
            f"{last['id']}. Three things put it there. It is the "
            f"cheapest build in the set: one oscillator, one splitter "
            f"and a counter, or a single synthesizer split two ways. "
            f"Its claim ceiling is reachable, which no other "
            f"experiment in the set can say. And it validates the "
            f"phase-transfer chain that CLOCK_LINK_INDEPENDENT "
            f"depends on entirely, so running the independent "
            f"comparison first would produce a number nobody could "
            f"interpret."),
        "robustness": (
            "the ordering of the top two is insensitive to the "
            "scores: the baseline costs roughly a quarter of the "
            "independent comparison, so it leads even if the two are "
            "scored identically. The baseline only loses first place "
            "if it is judged less than a quarter as informative as "
            "the independent comparison, which would be hard to argue "
            "given that the independent comparison is uninterpretable "
            "without it."),
        "sequencing_note": (
            "information per dollar is not the only ordering "
            "principle. CLOCK_LINK_BASELINE would come first even if "
            "it ranked poorly, because CLOCK_LINK_INDEPENDENT cannot "
            "be interpreted before it. Here the two principles agree, "
            "which is a convenience rather than an argument."),
        "hobbyist_achievable": [
            e.id for e in EXPERIMENTS.values() if e.hobbyist_achievable],
        "not_hobbyist_achievable": [
            e.id for e in EXPERIMENTS.values()
            if not e.hobbyist_achievable],
        "none_of_these_have_been_run": True,
    }


# --------------------------------------------------------------------
# 4. Hazards
# --------------------------------------------------------------------

#: Hazards specific to the R7 experiment set. The shape is R6's, and
#: the classification is a self-assessment, not a safety review.
HAZARDS = {
    "HIGH_VOLTAGE_PULSE": {
        "description": "electrostatic excitation drive and any pulsed "
                       "coil drive store energy and produce large "
                       "back-EMF at switch-off",
        "control": "enclosed and interlocked drive, snubber and clamp, "
                   "bleeder resistor with a verified discharge time, "
                   "isolated or high-voltage-rated probes only, "
                   "single-hand rule",
        "status": "CONTROLLED_BY_DESIGN",
    },
    "MAINS_CONSTRUCTION": {
        "description": "any mains-connected build, including the "
                       "vacuum pump and the high-voltage supply",
        "control": "must be performed by a qualified person to the "
                   "local electrical code; RCD protection on the "
                   "bench supply",
        "status": "REFUSED_UNLESS_QUALIFIED",
    },
    "RF_EMISSION": {
        "description": "two-channel drive harmonics and switching "
                       "transients radiate, and a field-mapping rig is "
                       "an antenna by construction",
        "control": "screened enclosure, no open radiator, emission "
                   "survey before extended running, and compliance "
                   "with the local spectrum rules",
        "status": "CONTROLLED_BY_DESIGN",
    },
    "OPTICAL": {
        "description": "interferometer, vibrometer and autocollimator "
                       "sources; the vibrometer is the one with real "
                       "power behind it",
        "control": "fully enclosed beam path, no beam at seated or "
                   "standing eye height, interlocked covers, eyewear "
                   "matched to the wavelength and class, and no "
                   "reflective jewellery or tools at the beam plane",
        "status": "CONTROLLED_BY_DESIGN",
    },
    "ULTRASONIC": {
        "description": "air-coupled ultrasonic excitation above "
                       "audibility, which gives no natural warning",
        "control": "enclosure, published exposure limits observed, "
                   "no direct contact with the specimen mount while "
                   "driving, and a run indicator that is visible "
                   "because the drive is not audible",
        "status": "CONTROLLED_BY_DESIGN",
    },
    "MECHANICAL_FRACTURE": {
        "description": "a driven crystal or a stressed fibre can "
                       "fracture; a torsion fibre releases stored "
                       "energy when it fails",
        "control": "containment shield, drive amplitude ramped rather "
                   "than stepped, a declared modal Q limit, eye "
                   "protection, and an arm restraint that catches the "
                   "balance if the fibre parts",
        "status": "CONTROLLED_BY_DESIGN",
    },
    "VACUUM_IMPLOSION": {
        "description": "evacuated chambers and viewports fail "
                       "inwards, and glass viewports fail badly",
        "control": "rated chamber and viewports with documented "
                   "pressure ratings, guard mesh, no improvised "
                   "vessels, pump-down behind a shield",
        "status": "CONTROLLED_BY_DESIGN",
    },
    "BIOLOGICAL_EXPOSURE": {
        "description": "any deliberate human or animal exposure to "
                       "the drive, the field, the acoustic output or "
                       "the optical output",
        "control": "none offered",
        "status": "REFUSED_ENTIRELY",
    },
}


# --------------------------------------------------------------------
# 5. Dual use (core/10)
# --------------------------------------------------------------------

#: Subjects the public work may discuss (core/10).
PERMITTED_TOPICS = (
    "CLOCKS",
    "NAVIGATION",
    "QUARTZ_PHYSICS",
    "SIGNAL_PROCESSING",
    "OPEN_METROLOGY",
    "SCIENTIFIC_NULLS",
    "LOW_POWER_APPARATUS",
)

#: Applications the work must not optimize for (core/10).
PROHIBITED_OPTIMIZATIONS = (
    "WEAPON_GUIDANCE",
    "TARGETING",
    "EMITTER_GEOLOCATION_FOR_ATTACK",
    "ELECTRONIC_WARFARE",
    "HIGH_POWER_DIRECTED_ENERGY",
    "HAZARDOUS_BIOLOGICAL_EXPOSURE",
    "UNCONTROLLED_LASERS_RF_VOLTAGE_VACUUM_OR_PRESSURE",
)


def dual_use_policy() -> dict:
    """The core/10 policy, stated in a form a reader can check."""
    return {
        "may_discuss": list(PERMITTED_TOPICS),
        "must_not_optimize": list(PROHIBITED_OPTIMIZATIONS),
        "military_relevance": (
            "the component technologies here -- precision oscillators, "
            "phase transfer, magnetometry -- have well-documented "
            "military histories. R7 records that as prior context. It "
            "is not evidence that any classified system has been "
            "duplicated, and it is not an endorsement of any such "
            "use."),
        "benefit_framing": (
            "resilient civilian timing, open science, geodesy, "
            "communications, education and safety"),
        "why_a_null_matters_here": (
            "the dual-use pressure on this work comes almost entirely "
            "from claims that were never established. A published null "
            "reduces that pressure rather than adding to it, which is "
            "one more reason the programme's expected outputs are "
            "bounded nulls."),
        "enforcement": (
            "refuse_weaponization_assistance() raises unconditionally; "
            "the hazard table refuses biological exposure entirely; "
            "and the experiment set contains no high-power emitter."),
        "power_ceiling_note": (
            "every experiment in EXPERIMENTS is watt-scale or below at "
            "the specimen. There is no configuration in the set that "
            "could be turned toward directed energy by increasing a "
            "setting."),
    }


def refuse_weaponization_assistance(*args, **kwargs):
    """Always refuses. Not negotiable and not scoped to a requester."""
    raise BenchRefused(
        "R7 does not assist with weapon guidance, targeting, emitter "
        "geolocation for attack, electronic warfare, high-power "
        "directed energy, hazardous biological exposure, or "
        "uncontrolled lasers, RF, voltage, vacuum or pressure "
        "(core/10). This refusal is unconditional: it does not depend "
        "on who is asking, on a stated purpose, or on a claim that "
        "the application is defensive or hypothetical. The permitted "
        "subjects are clocks, navigation, quartz physics, signal "
        "processing, open metrology, scientific nulls and low-power "
        "apparatus.")


# --------------------------------------------------------------------
# 6. Where R7 stops
# --------------------------------------------------------------------

def honest_stop() -> dict:
    """The P08 closing statement."""
    rank = priority_ranking()
    return {
        "programme": "RGCS-V5.0-R7",
        "produced": [
            "a CW decoder frozen before any future vector exists",
            "an arithmetic firewall between geometry and the metric",
            "a directional-field compiler that separates requested "
            "from realized",
            "a force-null design with a quadrature confound budget",
            "an experiment set with catalogue-class costings",
            "refusals that raise",
        ],
        "not_produced": [
            "any measurement",
            "any calibrated instrument",
            "any oscillator comparison",
            "any aligned crystal",
            "any mapped field",
            "any force reading",
            "any independent replication",
        ],
        "instruments_owned": 0,
        "measurements_taken": 0,
        "ready_for_bench": False,
        "statement": (
            "R7 produced models, designs and refusals. It produced no "
            "measurement. No oscillator pair has been compared, no "
            "crystal aligned, no field mapped, and no force measured. "
            "Everything in this module is documentation, and "
            "documentation completeness is not a fact about the "
            "world."),
        "next_real_step": (
            f"{rank['top']}: one oscillator, a two-way splitter and a "
            f"counter, with both temperatures logged. It has a known "
            f"correct answer, so it tests the measurement chain rather "
            f"than the hypothesis, and nothing else in the programme "
            f"can be interpreted until it has been run."),
        "what_would_end_the_programme": (
            "a baseline that shows the measurement chain cannot reach "
            "the resolution the claims require would close the clock "
            "line honestly, and that outcome is entirely possible. "
            "The programme is designed so that this is a result, not "
            "a failure."),
    }


__all__ = [
    "SAFETY_CLASSES",
    "BenchRefused",
    "Experiment",
    "EXPERIMENTS",
    "READINESS_GATES",
    "R7Readiness",
    "current_assessment",
    "readiness",
    "priority_ranking",
    "HAZARDS",
    "PERMITTED_TOPICS",
    "PROHIBITED_OPTIMIZATIONS",
    "dual_use_policy",
    "refuse_weaponization_assistance",
    "honest_stop",
]
