"""P06/P10 — hidden neutral carrier hypotheses and coupling feasibility.

The R9 question, stated as the pack poses it:

    Does the source corpus and current physics support a coherent
    hidden-neutral-carrier model, and what measurements would
    distinguish an antineutrino analogy, sterile/right-handed neutrino
    physics, another hidden sector, an ordinary apparatus effect, or
    no new carrier?

This module answers the *feasibility* half, and the answer is a
refusal — but a more interesting one than "zero".

Neutrinos do interact with a bench crystal -- of order once a year,
and at a zero detection threshold, which is the most optimistic way
to count (see THRESHOLD_CAVEAT). The barrier is not that the rate
vanishes; it is that

1. the rate is ~0.6/yr against ~2e7 cosmic muons/yr through the same
   volume, a signal-to-background of ~3e-8; and
2. a quartz resonator has no single-quantum readout channel, so even
   an interaction that occurred would not be registered as an event.

You cannot know *which* event it was. That is the whole difficulty,
and it is why real neutrino detectors are kilotons deep underground
rather than grams on a bench.

Constants are literature values with their sources named. Nothing here
is a measurement: this programme owns no detector, no shielding, and
no particle-physics instrumentation of any kind.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict

#: Typed hypothesis ladder (P06). Ordered from the most mundane
#: explanation to the least, because that is the order in which they
#: must be excluded.
CARRIER_HYPOTHESES = (
    "ORDINARY_APPARATUS_MODE",
    "ORDINARY_ENVIRONMENTAL_COUPLING",
    "INSTRUMENTATION_ARTEFACT",
    "ACTIVE_ANTINEUTRINO",
    "STERILE_NEUTRINO",
    "RIGHT_HANDED_NEUTRINO",
    "HEAVY_NEUTRAL_LEPTON",
    "GENERIC_HIDDEN_SECTOR",
    "UNKNOWN_MECHANISM",
    "NO_NEW_CARRIER",
)

#: Verdicts the feasibility calculation may return.
FEASIBILITY_VERDICTS = (
    "REFUSED_BY_ARITHMETIC",
    "BELOW_BACKGROUND",
    "NO_READOUT_CHANNEL",
    "NO_TARGET_CENTRES",
    "REQUIRES_DEDICATED_DETECTOR",
    "CONVENTIONALLY_MEASURABLE",
)

# --- literature constants, each with its provenance -------------------

AVOGADRO = 6.022_140_76e23          # exact, SI definition
SECONDS_PER_YEAR = 3.155_695_2e7    # Julian year

#: Neutrino cross-sections, cm^2. Order-of-magnitude literature values
#: for the stated process and energy; not measurements by this project.
CROSS_SECTIONS = {
    "NU_E_ELASTIC_MEV": {
        "sigma_cm2": 1e-44,
        "per": "ELECTRON",
        "process": "neutrino-electron elastic scattering at ~1 MeV",
        "source": "standard electroweak cross-section, textbook",
    },
    "INVERSE_BETA_DECAY_MEV": {
        "sigma_cm2": 1e-43,
        "per": "FREE_PROTON",
        "process": "inverse beta decay, nu_e-bar + p -> n + e+, few MeV",
        "source": "reactor-neutrino literature, order of magnitude",
    },
    "COHERENT_CEVNS": {
        "sigma_cm2": 1e-39,
        "per": "NUCLEUS",
        "process": "coherent elastic neutrino-nucleus scattering",
        "source": "COHERENT experiment regime; enhanced by N^2 but "
                  "deposits only sub-keV nuclear recoil",
    },
}

#: R9-D-015. Every cross-section used to be multiplied by
#: ``target.n_nucleons``, but the three have three different
#: denominators, so two of the three were wrong by construction:
#:
#: * elastic scattering is per **electron** -- quartz has 30 e per
#:   60 nucleons, so this overcounted by ~2x;
#: * inverse beta decay is per **free proton** -- quartz (SiO2) has
#:   **none**, and the module cheerfully reported 12.34 IBD
#:   interactions per year in it;
#: * CEvNS is per **nucleus** -- using nucleon count overcounted by
#:   ~20x, and the inflated figure stopped the verdict short of
#:   REFUSED_BY_ARITHMETIC.
#:
#: No test exercised a non-default cross-section, so none of it
#: surfaced. Target counts are now selected by the ``per`` field.
TARGET_COUNT_KINDS = ("ELECTRON", "FREE_PROTON", "NUCLEUS", "NUCLEON")

#: R9-D-018. Measured solar neutrino-electron scattering rate, per
#: electron per second, anchored to Borexino.
#:
#: The module previously took sigma = 1e-44 cm^2 (the textbook
#: neutrino-electron value at ~1 MeV) and applied it to the *total*
#: solar flux of 6.5e10 /cm^2/s. But 99.9% of that flux is pp
#: neutrinos with <E> ~ 0.267 MeV, and the elastic cross-section falls
#: roughly linearly with energy, so a 1 MeV sigma overstates the
#: flux-weighted average by about an order of magnitude. The bench
#: figure came out ~0.6/yr when the measurement-anchored answer is
#: ~0.06/yr -- one interaction every sixteen years, not one a year.
#:
#: Derivation: Borexino/SSM see ~186 counts/day per 100 t of
#: scintillator (pp ~131, Be-7 ~48, pep/CNO ~7). At ~3.4e23 electrons
#: per gram that is 6.33e-35 per electron per second, which implies an
#: effective flux-weighted sigma of 9.7e-46 cm^2 -- and that number is
#: a measurement, not a textbook value evaluated at the wrong energy.
SOLAR_NU_E_RATE_PER_ELECTRON_PER_S = 6.33e-35
SOLAR_RATE_SOURCE = (
    "Borexino measured solar neutrino-electron elastic scattering "
    "rates (pp, Be-7, pep/CNO), ~186 counts/day/100 t; converted to a "
    "per-electron rate. Preferred over a textbook 1 MeV cross-section "
    "because the solar spectrum is dominated by 0.267 MeV pp "
    "neutrinos."
)


def solar_interaction_rate_per_year(target: Target) -> float:
    """Measurement-anchored solar rate for an electron target.

    Uses the Borexino-derived per-electron rate directly, so no
    cross-section is evaluated at an energy the solar spectrum does
    not actually have (R9-D-018).
    """
    return (target.n_electrons * SOLAR_NU_E_RATE_PER_ELECTRON_PER_S
            * SECONDS_PER_YEAR)


#: Sea-level cosmic-ray muon flux, the dominant unshielded background.
MUON_FLUX_PER_CM2_PER_MIN = 1.0     # ~1/cm^2/min, standard figure

#: Muon flux suppression versus overburden, metres water equivalent.
#: R9-D-001: the first version of this module applied the sea-level
#: flux to every target, which made it report Super-Kamiokande as
#: REFUSED_BY_ARITHMETIC. Super-K has detected solar neutrinos since
#: 1996. A feasibility model that refutes a working experiment is
#: wrong, and the omission was the overburden: deep sites suppress the
#: muon background by five to six orders of magnitude, which is
#: precisely why they are deep.
MUON_ATTENUATION = {
    0: 1.0,           # sea level
    100: 1e-2,
    1000: 1e-4,
    2700: 1e-5,       # Super-Kamiokande, ~2700 mwe
    # R9-D-017: this entry read 1e-6 and was wrong by ~50x. SNOLAB's
    # measured flux is 0.27 muons/m^2/day = 3.1e-10 /cm^2/s against
    # 1.67e-2 /cm^2/s at sea level, a ratio of ~2e-8. Only the 2700
    # mwe entry had been checked against a real site, so the deepest
    # entry -- the one that matters most for a shielding argument --
    # was the least constrained.
    6000: 2e-8,       # SNOLAB, measured
}


def muon_suppression(overburden_mwe: float) -> float:
    """Interpolate the muon suppression factor, log-linear in depth."""
    if overburden_mwe < 0:
        raise ValueError("overburden cannot be negative")
    depths = sorted(MUON_ATTENUATION)
    if overburden_mwe <= depths[0]:
        return MUON_ATTENUATION[depths[0]]
    if overburden_mwe >= depths[-1]:
        return MUON_ATTENUATION[depths[-1]]
    for lo, hi in zip(depths, depths[1:]):
        if lo <= overburden_mwe <= hi:
            f = (overburden_mwe - lo) / (hi - lo)
            a, b = MUON_ATTENUATION[lo], MUON_ATTENUATION[hi]
            return a * (b / a) ** f
    raise AssertionError("unreachable")


#: R9-D-016. The Super-K validation used to assert raw
#: signal-to-background > 1, and it passed at 1.17 -- a 17% margin
#: produced by two large errors partly cancelling (a 1 MeV
#: cross-section applied to the whole solar flux, 99.9% of which is
#: sub-threshold pp neutrinos, against an inflated cross-sectional
#: area). Correcting the electron count broke it, which is the useful
#: part: the test was wrong in principle, not just in its numbers.
#:
#: Super-Kamiokande's true raw S/B is of order 1e-4. It does not
#: detect solar neutrinos by out-numbering muons. It detects them by
#: Cherenkov event reconstruction, directionality back to the Sun,
#: energy thresholds, fiducial-volume cuts and muon tagging -- an
#: analysis chain this module does not model at all.
#:
#: So raw S/B cannot be the criterion that validates the model. What
#: the model can legitimately say is which targets are refused
#: outright and which require a dedicated detector; whether a
#: dedicated detector then succeeds is a question about its analysis
#: chain, not its raw rate ratio.
RAW_SB_IS_NOT_THE_DISCRIMINATOR = (
    "raw signal-to-background does not determine whether a detector "
    "works. Super-Kamiokande runs at a raw S/B of order 1e-4 and "
    "detects solar neutrinos anyway, through event reconstruction, "
    "directionality, energy thresholds and muon tagging. This module "
    "models none of that. It can distinguish 'refused by arithmetic' "
    "from 'requires a dedicated detector'; it cannot certify that a "
    "dedicated detector succeeds."
)


class CarrierRefused(RuntimeError):
    """Raised when a carrier-detection claim is refused."""


# --- rate arithmetic ---------------------------------------------------

@dataclass(frozen=True)
class Target:
    """A candidate detector mass."""

    label: str
    mass_g: float
    molar_mass_g: float
    nucleons_per_molecule: int
    cross_section_cm2_area: float
    #: Electrons and free protons per molecule. Required because
    #: cross-sections have different denominators (R9-D-015): quartz
    #: has 30 electrons and NO free protons per SiO2; water has 10
    #: electrons and 2 free protons (the hydrogens) per H2O.
    electrons_per_molecule: int = 0
    free_protons_per_molecule: int = 0
    #: Overburden in metres water equivalent. Sea level is 0. This
    #: field exists because omitting it made the model "refute"
    #: Super-Kamiokande, which demonstrably works -- see
    #: MUON_ATTENUATION.
    overburden_mwe: float = 0.0

    def __post_init__(self) -> None:
        if self.mass_g <= 0 or self.molar_mass_g <= 0:
            raise ValueError("mass and molar mass must be positive")

    @property
    def n_molecules(self) -> float:
        return (self.mass_g / self.molar_mass_g) * AVOGADRO

    @property
    def n_nucleons(self) -> float:
        return self.n_molecules * self.nucleons_per_molecule

    @property
    def n_electrons(self) -> float:
        return self.n_molecules * self.electrons_per_molecule

    @property
    def n_free_protons(self) -> float:
        return self.n_molecules * self.free_protons_per_molecule

    def target_count(self, kind: str) -> float:
        """How many scattering centres of the given kind.

        Getting this wrong is not a rounding error: using nucleons for
        a per-nucleus cross-section overcounts by ~20x, and using them
        for inverse beta decay in quartz invents 6e25 free protons
        that do not exist.
        """
        if kind not in TARGET_COUNT_KINDS:
            raise ValueError(
                f"unknown target-count kind {kind!r}; "
                f"expected one of {TARGET_COUNT_KINDS}")
        return {
            "ELECTRON": self.n_electrons,
            "FREE_PROTON": self.n_free_protons,
            "NUCLEUS": self.n_molecules,
            "NUCLEON": self.n_nucleons,
        }[kind]


#: The apparatus this programme actually contemplates, plus the scale
#: real experiments use, for comparison.
TARGETS = {
    # SiO2: 60 nucleons, 30 electrons, 0 free protons.
    "BENCH_QUARTZ_100G": Target(
        "100 g quartz crystal", 100.0, 60.08, 60, 40.0,
        electrons_per_molecule=30, free_protons_per_molecule=0),
    "GENEROUS_QUARTZ_10KG": Target(
        "10 kg quartz, far beyond the current apparatus",
        10_000.0, 60.08, 60, 900.0,
        electrons_per_molecule=30, free_protons_per_molecule=0),
    # H2O: 18 nucleons, 10 electrons, 2 free protons (the hydrogens).
    "SUPER_K_SCALE": Target(
        "22.5 kilotonne water fiducial volume, ~2700 mwe overburden",
        2.25e10, 18.015, 18, 4.5e7, overburden_mwe=2700.0,
        electrons_per_molecule=10, free_protons_per_molecule=2),
}


def interaction_rate_per_year(target: Target, flux_per_cm2_s: float,
                              sigma_cm2: float,
                              per: str = "NUCLEON") -> float:
    """R = flux * N * sigma, in interactions per year.

    ``per`` selects which scattering centres N counts. It defaults to
    NUCLEON only for backward compatibility; callers should pass the
    ``per`` field of the cross-section in use (R9-D-015).
    """
    if flux_per_cm2_s < 0 or sigma_cm2 <= 0:
        raise ValueError("flux must be non-negative, sigma positive")
    return flux_per_cm2_s * target.target_count(per) * sigma_cm2 \
        * SECONDS_PER_YEAR


def muon_background_per_year(target: Target) -> float:
    """Cosmic muon count through the target, depth-corrected."""
    return (MUON_FLUX_PER_CM2_PER_MIN * target.cross_section_cm2_area
            * 60.0 * 24.0 * 365.25
            * muon_suppression(target.overburden_mwe))


@dataclass(frozen=True)
class FeasibilityResult:
    target: str
    hypothesis: str
    flux_per_cm2_s: float
    sigma_cm2: float
    interactions_per_year: float
    background_per_year: float
    signal_to_background: float
    has_readout_channel: bool
    verdict: str
    note: str

    def as_record(self) -> dict:
        return asdict(self)


def assess(target_key: str, *, hypothesis: str = "ACTIVE_ANTINEUTRINO",
           flux_per_cm2_s: float = 6.5e10,
           cross_section_key: str = "NU_E_ELASTIC_MEV",
           has_readout_channel: bool = False,
           use_measured_solar_rate: bool = True) -> FeasibilityResult:
    """Can this target detect this carrier at all?

    ``flux_per_cm2_s`` defaults to the total solar neutrino flux at
    Earth, which is the largest natural flux available and therefore
    the most generous assumption a bench experiment could make.

    ``has_readout_channel`` defaults False and that default is the
    point: a quartz resonator has no mechanism to register a single
    sub-keV nuclear recoil. Setting it True asks the counterfactual
    "even if readout existed, would the rate suffice?"
    """
    if target_key not in TARGETS:
        raise ValueError(f"unknown target {target_key!r}")
    if hypothesis not in CARRIER_HYPOTHESES:
        raise ValueError(f"unknown hypothesis {hypothesis!r}")
    if cross_section_key not in CROSS_SECTIONS:
        raise ValueError(f"unknown cross-section {cross_section_key!r}")

    t = TARGETS[target_key]
    sigma = CROSS_SECTIONS[cross_section_key]["sigma_cm2"]
    per = CROSS_SECTIONS[cross_section_key]["per"]
    if cross_section_key == "NU_E_ELASTIC_MEV" and use_measured_solar_rate:
        # R9-D-018: prefer the Borexino-anchored per-electron rate over
        # a 1 MeV cross-section applied to a 0.267 MeV spectrum.
        rate = solar_interaction_rate_per_year(t)
    else:
        rate = interaction_rate_per_year(t, flux_per_cm2_s, sigma,
                                         per=per)
    bg = muon_background_per_year(t)
    stb = rate / bg if bg > 0 else math.inf

    if rate == 0.0:
        # R9-D-015 made this reachable and it should be: quartz has no
        # free protons, so inverse beta decay cannot occur in it at
        # all. Previously the nucleon count was used regardless, and
        # the module reported 12.34 IBD interactions/yr in a material
        # containing zero free protons.
        verdict = "NO_TARGET_CENTRES"
        note = (
            f"{t.label} contains no {per.lower().replace('_', ' ')} "
            f"targets, so the process "
            f"'{CROSS_SECTIONS[cross_section_key]['process']}' cannot "
            f"occur in it at any rate. This is a statement about "
            f"chemistry, not sensitivity: no exposure time changes it.")
    elif not has_readout_channel:
        verdict = "NO_READOUT_CHANNEL"
        note = (
            f"{rate:.3g} interactions/yr would occur, but the target "
            f"has no channel capable of registering a single sub-keV "
            f"recoil. An interaction that is never transduced is not a "
            f"measurement. This is the binding obstacle for the "
            f"current apparatus, and it is prior to the rate question.")
    elif stb < 1e-6:
        verdict = "REFUSED_BY_ARITHMETIC"
        note = (
            f"signal-to-background is {stb:.3g}: roughly one candidate "
            f"interaction per {1 / stb:.3g} cosmic muons through the "
            f"same volume. No analysis recovers a signal that far "
            f"under an unvetoed background; real detectors solve this "
            f"with kilotonnes and kilometres of rock, not with "
            f"cleverness.")
    elif stb < 1.0:
        verdict = "BELOW_BACKGROUND"
        note = (f"signal sits below background at {stb:.3g}; shielding "
                f"and veto would be mandatory before any claim")
    elif rate < 100:
        verdict = "REQUIRES_DEDICATED_DETECTOR"
        note = (f"{rate:.3g} interactions/yr is a real but slow rate "
                f"needing dedicated instrumentation")
    else:
        verdict = "CONVENTIONALLY_MEASURABLE"
        note = (f"{rate:.3g} interactions/yr above background; this is "
                f"the regime real neutrino observatories operate in")

    assert verdict in FEASIBILITY_VERDICTS
    return FeasibilityResult(
        target=t.label, hypothesis=hypothesis,
        flux_per_cm2_s=flux_per_cm2_s, sigma_cm2=sigma,
        interactions_per_year=rate, background_per_year=bg,
        signal_to_background=stb,
        has_readout_channel=has_readout_channel,
        verdict=verdict, note=note)


#: Published detectors, smallest-first. Added after the R9 prior-art
#: review, which corrected the framing of this module in a useful
#: direction (R9-D-006).
DETECTOR_BENCHMARKS = {
    "NUCLEUS": {
        "mass_g": 10.0,
        "material": "CaWO4 / Al2O3 cryogenic calorimeter",
        "status": "commissioning; no detection published yet",
        "threshold_eV": 20.0,
        "conditions": ("~10 mK cryogenics, reactor-adjacent flux, "
                       "heavy shielding plus active muon veto"),
        "source": "arXiv:1704.04320; commissioning arXiv:2508.02488",
    },
    "CONUS_PLUS": {
        "mass_g": 3_000.0,
        "material": "germanium diodes (4 x 1 kg)",
        "status": ("first reactor CEvNS detection, 3.7 sigma, "
                   "327 kg-days"),
        "threshold_eV": 160.0,
        "conditions": "reactor site, shielded",
        "source": "Nature (2025); arXiv:2501.05206",
    },
    "COHERENT": {
        "mass_g": 14_600.0,
        "material": "CsI[Na]",
        "status": "first CEvNS observation, 6.7 sigma, 2017",
        "threshold_eV": 4_800.0,
        "conditions": "spallation neutron source, shielded basement",
        "source": "Science 357:1123; arXiv:1708.01294",
    },
}

#: The miniaturisation argument is not ours and is 42 years old.
COHERENT_SCATTERING_PRIOR_ART = (
    "Freedman (1974) predicted coherent elastic neutrino-nucleus "
    "scattering; Drukier & Stodolsky (1984) is the canonical proposal "
    "that coherence permits drastically smaller neutrino detectors. "
    "The entire small-detector argument is theirs."
)


def scale_gap() -> dict:
    """What actually separates this bench from a neutrino detector.

    R9-D-006. This function used to compare the bench against
    Super-Kamiokande and conclude the barrier was **mass** -- a factor
    of 1e8. The prior-art review showed that framing is wrong, and
    wrong in an informative direction: NUCLEUS runs a 10 g target,
    one tenth of the bench crystal, and gram-scale neutrino detection
    is an active funded programme.

    So mass is not the barrier. Ten grams is enough. What NUCLEUS has
    that the bench does not is a **readout channel** -- a cryogenic
    calorimeter at ~10 mK with a ~20 eV threshold -- plus depth,
    shielding and an active veto. The field solved the small-detector
    problem by engineering transduction, which is exactly the obstacle
    this module identifies as binding.

    The corrected conclusion is stronger than the original: the bench
    is not short of mass, it is short of a way to notice.
    """
    bench = TARGETS["BENCH_QUARTZ_100G"]
    smallest = DETECTOR_BENCHMARKS["NUCLEUS"]
    return {
        "bench_mass_g": bench.mass_g,
        "smallest_real_detector_g": smallest["mass_g"],
        "mass_ratio_to_smallest": smallest["mass_g"] / bench.mass_g,
        "bench_is_heavier_than_smallest_detector": (
            bench.mass_g > smallest["mass_g"]),
        "benchmarks": DETECTOR_BENCHMARKS,
        "barrier": "READOUT_NOT_MASS",
        "note": (
            "the bench crystal is ten times heavier than the NUCLEUS "
            "target. Mass is not what it lacks. It lacks a "
            "transduction channel -- NUCLEUS uses a ~10 mK cryogenic "
            "calorimeter with a ~20 eV threshold -- and depth, "
            "shielding and a veto. The gap is not a refinement "
            "problem, but it is a readout problem, not a size one."),
        "prior_art": COHERENT_SCATTERING_PRIOR_ART,
    }


#: The computed rate assumes every interaction counts, i.e. zero
#: detection threshold. Real devices have thresholds, and the rate
#: above threshold is far lower.
THRESHOLD_CAVEAT = (
    "the ~0.06 interactions/yr figure is a ZERO-THRESHOLD ceiling, not "
    "an expectation. Published solar pp CEvNS rates (~16.6 events per "
    "kg-yr in germanium, arXiv:2104.14352) are likewise quoted at zero "
    "threshold. Recoil energies here are sub-keV; at any threshold a "
    "quartz resonator could plausibly reach, the rate above threshold "
    "is consistent with zero. The honest reading is that ~1.2/yr is "
    "the most optimistic number available, and the real one is lower."
)


def refuse_carrier_detection_claim(*args, **kwargs):
    """Always refuses. No detector exists in this programme."""
    raise CarrierRefused(
        "a hidden-carrier detection claim is refused. This programme "
        "owns no particle detector, no shielding and no veto, and the "
        "quartz apparatus has no channel capable of registering a "
        "single sub-keV recoil. Interactions occurring is not the "
        "same as interactions being measured.")


# --- what would actually distinguish the hypotheses -------------------

#: The discriminating observables, per hypothesis. Included because
#: "what measurement would tell these apart" is the pack's central
#: question and deserves a concrete answer rather than a gesture.
DISCRIMINATORS = {
    "ORDINARY_APPARATUS_MODE": (
        "reproduces under sham drive with the specimen absent",
        "tracks temperature, supply voltage or mounting",
        "disappears with the empty-mount control",
    ),
    "ORDINARY_ENVIRONMENTAL_COUPLING": (
        "correlates with a logged environmental channel",
        "changes with siting, orientation or time of day",
    ),
    "INSTRUMENTATION_ARTEFACT": (
        "moves when the instrument changes but the apparatus does not",
        "absent on an independent measurement chain",
    ),
    "ACTIVE_ANTINEUTRINO": (
        "rate scales with a known flux: reactor on/off, solar zenith, "
        "or distance from a source",
        "energy spectrum matches the emitting process",
        "requires a target mass and shielding this programme lacks",
    ),
    "STERILE_NEUTRINO": (
        "baseline-dependent disappearance in an oscillation "
        "experiment",
        "an anomaly at short baseline not explained by three-flavour "
        "mixing",
    ),
    "RIGHT_HANDED_NEUTRINO": (
        "helicity-sensitive observable",
        "coupling suppressed relative to active flavours by a "
        "measurable mixing angle",
    ),
    "HEAVY_NEUTRAL_LEPTON": (
        "displaced-vertex or missing-mass signature at an accelerator",
        "kinematic edge set by the mass",
    ),
    "GENERIC_HIDDEN_SECTOR": (
        "portal-specific: kinetic mixing, Higgs portal or neutrino "
        "portal each predict different couplings",
        "no single experiment covers the space",
    ),
    "UNKNOWN_MECHANISM": (
        "reproducible under blinding, with ordinary channels bounded",
        "an effect that survives a sham control and an independent "
        "replication",
    ),
    "NO_NEW_CARRIER": (
        "every ordinary channel accounts for the observation",
        "the residual is consistent with zero within uncertainty",
    ),
}


def distinguishing_programme() -> dict:
    """The honest answer to the pack's central question."""
    return {
        "question": ("what measurement would distinguish an "
                     "antineutrino analogy, sterile/right-handed "
                     "neutrino physics, another hidden sector, an "
                     "ordinary apparatus effect, or no new carrier?"),
        "answer": (
            "For the current apparatus, none of them — because the "
            "apparatus cannot register a single interaction of any of "
            "these carriers. The discriminating measurements exist and "
            "are listed per hypothesis, but every one of the exotic "
            "options requires instrumentation this programme does not "
            "have and could not safely build."),
        "what_is_reachable": (
            "The ordinary hypotheses are fully testable here and "
            "should be tested first: sham drive, empty mount, "
            "environmental logging, and an independent measurement "
            "chain. Those close the mundane explanations, which is a "
            "precondition for taking any exotic one seriously."),
        "discriminators": {k: list(v) for k, v in DISCRIMINATORS.items()},
        "ordering_rule": (
            "hypotheses are excluded in the order listed in "
            "CARRIER_HYPOTHESES: mundane first. An exotic carrier is "
            "not a candidate explanation until the ordinary ones have "
            "been measured and bounded."),
    }
