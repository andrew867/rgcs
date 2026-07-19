"""P06/P10 — hidden neutral carrier hypotheses and coupling feasibility.

The R9 question, stated as the pack poses it:

    Does the source corpus and current physics support a coherent
    hidden-neutral-carrier model, and what measurements would
    distinguish an antineutrino analogy, sterile/right-handed neutrino
    physics, another hidden sector, an ordinary apparatus effect, or
    no new carrier?

This module answers the *feasibility* half, and the answer is a
refusal — but a more interesting one than "zero".

Neutrinos do interact with a bench crystal. About once a year. The
barrier is not that the rate vanishes; it is that

1. the rate is ~1/yr against ~2e7 cosmic muons/yr through the same
   volume, a signal-to-background of ~6e-8; and
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
        "process": "neutrino-electron elastic scattering at ~1 MeV",
        "source": "standard electroweak cross-section, textbook",
    },
    "INVERSE_BETA_DECAY_MEV": {
        "sigma_cm2": 1e-43,
        "process": "inverse beta decay, nu_e-bar + p -> n + e+, few MeV",
        "source": "reactor-neutrino literature, order of magnitude",
    },
    "COHERENT_CEVNS": {
        "sigma_cm2": 1e-39,
        "process": "coherent elastic neutrino-nucleus scattering",
        "source": "COHERENT experiment regime; enhanced by N^2 but "
                  "deposits only sub-keV nuclear recoil",
    },
}

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
    6000: 1e-6,       # SNOLAB scale
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
    #: Overburden in metres water equivalent. Sea level is 0. This
    #: field exists because omitting it made the model "refute"
    #: Super-Kamiokande, which demonstrably works -- see
    #: MUON_ATTENUATION.
    overburden_mwe: float = 0.0

    def __post_init__(self) -> None:
        if self.mass_g <= 0 or self.molar_mass_g <= 0:
            raise ValueError("mass and molar mass must be positive")

    @property
    def n_nucleons(self) -> float:
        return (self.mass_g / self.molar_mass_g) * AVOGADRO \
            * self.nucleons_per_molecule


#: The apparatus this programme actually contemplates, plus the scale
#: real experiments use, for comparison.
TARGETS = {
    "BENCH_QUARTZ_100G": Target(
        "100 g quartz crystal", 100.0, 60.08, 60, 40.0),
    "GENEROUS_QUARTZ_10KG": Target(
        "10 kg quartz, far beyond the current apparatus",
        10_000.0, 60.08, 60, 900.0),
    "SUPER_K_SCALE": Target(
        "22.5 kilotonne water fiducial volume, ~2700 mwe overburden",
        2.25e10, 18.015, 18, 4.5e7, overburden_mwe=2700.0),
}


def interaction_rate_per_year(target: Target, flux_per_cm2_s: float,
                              sigma_cm2: float) -> float:
    """R = flux * N * sigma, in interactions per year."""
    if flux_per_cm2_s < 0 or sigma_cm2 <= 0:
        raise ValueError("flux must be non-negative, sigma positive")
    return flux_per_cm2_s * target.n_nucleons * sigma_cm2 \
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
           has_readout_channel: bool = False) -> FeasibilityResult:
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
    rate = interaction_rate_per_year(t, flux_per_cm2_s, sigma)
    bg = muon_background_per_year(t)
    stb = rate / bg if bg > 0 else math.inf

    if not has_readout_channel:
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


def scale_gap() -> dict:
    """How far the bench apparatus is from a real neutrino detector."""
    bench = TARGETS["BENCH_QUARTZ_100G"]
    real = TARGETS["SUPER_K_SCALE"]
    return {
        "bench_mass_g": bench.mass_g,
        "reference_mass_g": real.mass_g,
        "mass_ratio": real.mass_g / bench.mass_g,
        "note": ("a working neutrino observatory uses of order 1e8 "
                 "times the target mass of a bench crystal, sited "
                 "under a kilometre of rock. The gap is not a "
                 "refinement problem."),
    }


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
