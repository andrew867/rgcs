"""P01 — the source claim graph.

Every claim the R6 corpus contains is registered here verbatim, with a
defensible translation, the evidence that translation would require,
and a *ceiling*: the strongest statement the programme is permitted to
make even if every planned test succeeds.

The registry is the reason paraphrase cannot quietly replace source
wording. ``verbatim`` is what the source said. ``translation`` is what
R6 will actually model. A reader can always see both.

Two source statements are factually wrong as stated and are recorded
as corrections rather than silently reinterpreted:

- the SI second derives from the caesium-133 ground-state hyperfine
  *transition*, not from radioactive *decay* of a caesium source;
- Vogel's "critical rotational angle" is a fixed-geometry claim, and
  the corpus's own reply ("the etheric field is a torsion field in
  constant movement") contradicts it rather than supporting it.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal

from . import PHRYLL_CLASSES

SourceClass = Literal[
    "SOURCE_CLAIM",
    "LORE",
    "APPARATUS_HYPOTHESIS_SEED",
    "PLANETARY_GRID_HYPOTHESIS_SEED",
    "INFORMATION_CARRIER_HYPOTHESIS_SEED",
    "OPERATOR_ARCHITECTURE_NOTE",
    "MODEL_INTERPRETATION",
]

#: Standing statuses carried over from the pack's correction matrix.
STANDING = (
    "HYPOTHESIS",
    "IMPLEMENTABLE",
    "IMPLEMENTABLE_WITH_LIMITS",
    "IMPLEMENTABLE_WITH_REFUSAL",
    "NOT_YET_ACHIEVED",
    "UNSUPPORTED_AS_ABSOLUTE",
    "UNSUPPORTED_AS_COMPLETE",
    "NOT_AUTHORITY_YET",
    "PLAUSIBLE_PROGRAMME",
    "FACTUALLY_CORRECTED",
    "REFUSED_NOT_TESTED",
)


@dataclass(frozen=True)
class Claim:
    """One source statement and everything R6 is allowed to do with it."""

    id: str
    verbatim: str
    source_class: SourceClass
    translation: str
    required_evidence: tuple[str, ...]
    standing: str
    ceiling: str
    #: Ordinary mechanisms that must be modeled and excluded first.
    ordinary_first: tuple[str, ...] = ()
    #: Set when the source statement is wrong as written.
    correction: str | None = None
    evidence_class: str = "SOURCE_CLAIM"
    provenance: str = "JH corpus amendment 2026-07-18"

    def __post_init__(self) -> None:
        if self.standing not in STANDING:
            raise ValueError(f"unknown standing {self.standing!r}")
        if self.evidence_class not in PHRYLL_CLASSES:
            raise ValueError(
                f"claim {self.id}: evidence_class {self.evidence_class!r} "
                f"is not on the ladder {PHRYLL_CLASSES}")
        if self.standing == "FACTUALLY_CORRECTED" and not self.correction:
            raise ValueError(
                f"claim {self.id}: FACTUALLY_CORRECTED requires a "
                f"correction explaining what is wrong")

    def as_record(self) -> dict:
        d = asdict(self)
        d["required_evidence"] = list(self.required_evidence)
        d["ordinary_first"] = list(self.ordinary_first)
        return d


def _c(*a, **k) -> Claim:
    return Claim(*a, **k)


#: The apparatus corpus (source_claims/JH_APPARATUS_...).
APPARATUS_CLAIMS: tuple[Claim, ...] = (
    _c(
        id="R6-C-001",
        verbatim=(
            "The sender angle must be in resonance with the geometry "
            "of the holographic matrix that is the receiver."
        ),
        source_class="SOURCE_CLAIM",
        translation=(
            "A directional coupling hypothesis: transfer efficiency "
            "between two elements depends on their relative "
            "orientation. Modeled as an orientation-dependent mutual "
            "inductance and radiation pattern, swept over angle."
        ),
        required_evidence=(
            "measured orientation-dependent coupling",
            "geometry-matched controls at non-special angles",
            "blinded orientation assignment",
        ),
        standing="HYPOTHESIS",
        ceiling=(
            "An orientation-dependent coupling coefficient. Not "
            "evidence of a holographic matrix, and 60 degrees carries "
            "no privileged status without a measured peak."
        ),
        ordinary_first=("impedance_and_mutual_inductance",
                        "magnetic_field", "electric_field"),
    ),
    _c(
        id="R6-C-002",
        verbatim=(
            "Both pulses should be equal in intensity, but if you "
            "alternate the structure of the two pulses it will "
            "empower the torsion field."
        ),
        source_class="APPARATUS_HYPOTHESIS_SEED",
        translation=(
            "Two interleaved drive trains (copper 1-0-1-0-1-0, silver "
            "0-1-0-1-0-1) at equal amplitude and opposite phase. This "
            "is a differential-mode drive; R6 decomposes any dual-coil "
            "programme into common and differential components and "
            "reports both."
        ),
        required_evidence=(
            "measured current in each winding",
            "measured field decomposition",
            "a defined, instrumented observable for 'torsion field'",
        ),
        standing="IMPLEMENTABLE_WITH_LIMITS",
        ceiling=(
            "A differential-mode drive programme with a measured field "
            "decomposition. 'Torsion field' has no instrument in R6, "
            "so no quantity can be said to be empowered."
        ),
        ordinary_first=("drive_current", "drive_voltage",
                        "magnetic_field",
                        "impedance_and_mutual_inductance"),
    ),
    _c(
        id="R6-C-003",
        verbatim=(
            "The crystal must be perpendicular to the planet's "
            "surface, in alignment with the planet's center core. "
            "This is important regarding the electromagnetic field of "
            "the planet."
        ),
        source_class="SOURCE_CLAIM",
        translation=(
            "An orientation hypothesis testable against the local "
            "geomagnetic vector. R6 builds an orientation "
            "discriminator that compares aligned, anti-aligned, "
            "orthogonal and randomized mountings."
        ),
        required_evidence=(
            "IGRF local field vector",
            "orientation sweep with randomized order",
            "null distribution over orientation",
        ),
        standing="HYPOTHESIS",
        ceiling=(
            "An orientation-dependent response, or its absence. The "
            "local geomagnetic field is ~25-65 microtesla and static; "
            "any claimed dependence must exceed the orientation null."
        ),
        ordinary_first=("magnetic_field", "displacement_and_strain",
                        "environmental_and_instrumentation_crosstalk"),
    ),
    _c(
        id="R6-C-004",
        verbatim=(
            "It is preferable that the wiring stops below the angle "
            "of the pyramidion. A crystal has its proper form "
            "dynamics. It needs to be pulsing freely."
        ),
        source_class="APPARATUS_HYPOTHESIS_SEED",
        translation=(
            "Mechanical loading by windings damps the crystal's "
            "acoustic modes. Terminating the winding below the "
            "termination face reduces mass loading and clamping at "
            "the antinode. This is a standard resonator-Q argument."
        ),
        required_evidence=(
            "modal analysis with and without winding load",
            "measured Q against winding coverage",
        ),
        standing="IMPLEMENTABLE",
        ceiling=(
            "A mass-loading and clamping effect on modal Q. This is "
            "ordinary mechanics and needs no new mechanism."
        ),
        ordinary_first=("displacement_and_strain",
                        "sound_and_ultrasound"),
    ),
    _c(
        id="R6-C-005",
        verbatim=(
            "Why is it that the singularity vortex only opens when "
            "piezoelectrically stimulated? Because of the pulse."
        ),
        source_class="SOURCE_CLAIM",
        translation=(
            "A pulse has broadband spectral content that a sinusoid "
            "does not. R6 models the pulse spectrum and the "
            "piezoelectric response, and asks whether any observable "
            "requires broadband excitation."
        ),
        required_evidence=(
            "pulse spectrum characterization",
            "matched-energy sinusoidal control",
            "a defined observable for 'vortex opening'",
        ),
        standing="UNSUPPORTED_AS_ABSOLUTE",
        ceiling=(
            "A bandwidth-dependent response. 'Singularity vortex' has "
            "no definition, no instrument, and no proposed signature; "
            "R6 cannot test it and does not claim to."
        ),
        ordinary_first=("crystal_charge", "displacement_and_strain",
                        "electric_field", "sound_and_ultrasound"),
    ),
    _c(
        id="R6-C-006",
        verbatim="1496 Hz preferred; 644 Hz; 587 Hz.",
        source_class="SOURCE_CLAIM",
        translation=(
            "Three candidate acoustic drive frequencies. R6 places "
            "them in the pulse/acoustic model and tests them against "
            "the specimen's own computed modal spectrum and against "
            "frequency-matched nulls."
        ),
        required_evidence=(
            "specimen modal spectrum",
            "frequency sweep including these three",
            "granularity-matched null over the same band",
        ),
        standing="HYPOTHESIS",
        ceiling=(
            "Three frequencies to test. Their significance must "
            "survive the v4.6 lesson: a null matched in granularity "
            "to the candidate set, not to a continuum."
        ),
        ordinary_first=("sound_and_ultrasound",
                        "displacement_and_strain"),
    ),
    _c(
        id="R6-C-007",
        verbatim=(
            "No, as the etheric field is a torsion field in constant "
            "movement."
        ),
        source_class="SOURCE_CLAIM",
        translation=(
            "A rejection of Vogel's fixed critical rotational angle "
            "in favour of a time-varying field. R6 models this as the "
            "difference between a static orientation optimum and a "
            "rotating-field drive, which are distinguishable "
            "experiments."
        ),
        required_evidence=(
            "static-angle sweep",
            "rotating-field drive with controlled rotation rate",
            "comparison of the two response surfaces",
        ),
        standing="FACTUALLY_CORRECTED",
        correction=(
            "The source uses this statement to dismiss a fixed "
            "critical angle, but a field 'in constant movement' does "
            "not eliminate a preferred angle; it makes the response "
            "depend on rotation rate as well as angle. The two claims "
            "are not alternatives. R6 tests both axes."
        ),
        ceiling=(
            "Two distinguishable drive regimes to compare. 'Etheric "
            "field' and 'torsion field' remain undefined and "
            "un-instrumented."
        ),
        ordinary_first=("magnetic_field", "drive_current"),
    ),
    _c(
        id="R6-C-008",
        verbatim=(
            "A 52 degree copper cone or pyramid collector for "
            "accumulated charge. Anything that measure the electric "
            "charge in the photonic field."
        ),
        source_class="APPARATUS_HYPOTHESIS_SEED",
        translation=(
            "An electrostatic collector. R6 models it as a capacitive "
            "pickup with a computed geometry-dependent capacitance "
            "and charge sensitivity."
        ),
        required_evidence=(
            "electrostatic model of the collector",
            "measured charge with and without drive",
            "sham-drive control",
        ),
        standing="IMPLEMENTABLE_WITH_LIMITS",
        ceiling=(
            "A capacitive charge measurement. Photons carry no "
            "electric charge, so 'charge in the photonic field' has "
            "no referent; the instrument measures collector charge."
        ),
        correction=(
            "Photons are electrically neutral. The phrase is recorded "
            "verbatim but cannot be implemented as stated; the "
            "implementable reading is collector charge."
        ),
        ordinary_first=("collector_charge", "electric_field",
                        "electrostatic_ion_ozone_humidity_airflow"),
    ),
)

#: The metric-witness corpus (source_claims/METRIC_INDEXED_...).
WITNESS_CLAIMS: tuple[Claim, ...] = (
    _c(
        id="R6-C-101",
        verbatim=(
            "epoch returned as the time of decay of the cesium clock "
            "source"
        ),
        source_class="OPERATOR_ARCHITECTURE_NOTE",
        translation=(
            "An epoch stamped against a caesium time reference. The "
            "implementable reading is a timestamp traceable to a "
            "caesium primary standard."
        ),
        required_evidence=("traceable time source", "declared timescale"),
        standing="FACTUALLY_CORRECTED",
        correction=(
            "The SI second is defined by the caesium-133 ground-state "
            "hyperfine TRANSITION frequency (9 192 631 770 Hz), not "
            "by radioactive decay. Caesium-133 is stable. 'Time of "
            "decay of the caesium source' describes no real process; "
            "R6 implements a transition-referenced epoch."
        ),
        ceiling=(
            "A timestamp on a declared timescale with a declared "
            "traceability chain."
        ),
        provenance="metric witness amendment 2026-07-18",
    ),
    _c(
        id="R6-C-102",
        verbatim="memory is approximate and decays like human memory",
        source_class="OPERATOR_ARCHITECTURE_NOTE",
        translation=(
            "A stretched-exponential relaxation of the payload "
            "posterior toward a declared prior, with the decay law, "
            "prior and refresh policy all explicit."
        ),
        required_evidence=(
            "characterized decay law",
            "nuisance controls for the twelve ordinary causes",
        ),
        standing="IMPLEMENTABLE_WITH_LIMITS",
        ceiling=(
            "A modeled relaxation with reported posterior "
            "uncertainty. Decay is not evidence of a clock and not "
            "evidence of proper time."
        ),
        provenance="metric witness amendment 2026-07-18",
    ),
    _c(
        id="R6-C-103",
        verbatim="active self-documenting witness",
        source_class="MODEL_INTERPRETATION",
        translation=(
            "A clock-attested event logger with environmental records "
            "and signed receipts."
        ),
        required_evidence=("calibrated oscillator", "signed receipts"),
        standing="HYPOTHESIS",
        ceiling="A clock-attested event logger.",
        provenance="Gemini value-claim correction matrix",
    ),
    _c(
        id="R6-C-104",
        verbatim="tamper-evident spacetime log",
        source_class="MODEL_INTERPRETATION",
        translation=(
            "A cryptographically chained, time-bounded log with hash "
            "chain, signatures and clock attestation."
        ),
        required_evidence=("hash chain", "signatures", "clock attestation"),
        standing="IMPLEMENTABLE",
        ceiling=(
            "A tamper-evident log. The adjective 'spacetime' adds "
            "nothing the cryptography provides; physical drift alone "
            "is not tamper evidence."
        ),
        provenance="Gemini value-claim correction matrix",
    ),
    _c(
        id="R6-C-105",
        verbatim="re-inflate degraded data",
        source_class="MODEL_INTERPRETATION",
        translation=(
            "Bayesian reconstruction from a declared prior and new "
            "observations, reporting posterior uncertainty and "
            "refusing under non-identifiability."
        ),
        required_evidence=(
            "identifiable likelihood",
            "posterior uncertainty",
        ),
        standing="IMPLEMENTABLE_WITH_REFUSAL",
        ceiling=(
            "Bounded reconstruction. A root certificate and a prior "
            "cannot restore information the channel destroyed."
        ),
        provenance="Gemini value-claim correction matrix",
    ),
    _c(
        id="R6-C-106",
        verbatim="metric-defined positioning",
        source_class="MODEL_INTERPRETATION",
        translation=(
            "Clock-, gravity-, inertial- and map-aided navigation "
            "with an explicit observability analysis."
        ),
        required_evidence=(
            "multiple sensors", "field model", "initial conditions",
        ),
        standing="NOT_YET_ACHIEVED",
        ceiling=(
            "A bounded position estimate when the posterior is "
            "informative, and POSITION_UNOBSERVABLE when it is not."
        ),
        provenance="Gemini value-claim correction matrix",
    ),
    _c(
        id="R6-C-107",
        verbatim="sovereign navigation",
        source_class="MODEL_INTERPRETATION",
        translation=(
            "Documented signal-denied navigation with its actual "
            "external dependencies stated."
        ),
        required_evidence=("bench field trials", "observability report"),
        standing="UNSUPPORTED_AS_ABSOLUTE",
        ceiling=(
            "SOVEREIGN_NAVIGATION_UNSUPPORTED. Every candidate "
            "signal-denied method depends on maps, ephemerides, field "
            "models or initial conditions supplied from outside."
        ),
        provenance="Gemini value-claim correction matrix",
    ),
    _c(
        id="R6-C-108",
        verbatim="entire causal history reconstruction",
        source_class="MODEL_INTERPRETATION",
        translation=(
            "Bounded reconstruction of the measured path variables "
            "that the channel actually recorded."
        ),
        required_evidence=("observable invertible channel",),
        standing="UNSUPPORTED_AS_COMPLETE",
        ceiling=(
            "Reconstruction of what was measured, with uncertainty. "
            "A module is not automatically a complete causal-history "
            "recorder."
        ),
        provenance="Gemini value-claim correction matrix",
    ),
    _c(
        id="R6-C-109",
        verbatim="protocol authority for spacetime-indexed information",
        source_class="MODEL_INTERPRETATION",
        translation=(
            "An open draft protocol with a conformance suite and test "
            "vectors."
        ),
        required_evidence=(
            "independent implementations", "governance", "adoption",
        ),
        standing="NOT_AUTHORITY_YET",
        ceiling="EXPERIMENTAL_SCHEMA advancing to DRAFT_PROTOCOL.",
        provenance="Gemini value-claim correction matrix",
    ),
    _c(
        id="R6-C-110",
        verbatim="distributed spacetime sensor network",
        source_class="MODEL_INTERPRETATION",
        translation=(
            "A distributed clock-comparison network using calibrated "
            "clocks and phase-transfer links."
        ),
        required_evidence=("calibrated clocks", "phase-transfer links"),
        standing="PLAUSIBLE_PROGRAMME",
        ceiling=(
            "Relativistic geodesy with optical clock networks is real "
            "and published. R6 models it; R6 has not built one."
        ),
        provenance="Gemini value-claim correction matrix",
    ),
    _c(
        id="R6-C-111",
        verbatim="spin stores payload, not address",
        source_class="OPERATOR_ARCHITECTURE_NOTE",
        translation=(
            "The R4 firewall restated: the exact address is digital "
            "and never stored in a physical spin state."
        ),
        required_evidence=(),
        standing="IMPLEMENTABLE",
        ceiling=(
            "An architectural invariant, already enforced by "
            "r4.radix.refuse_address_in_spin()."
        ),
        provenance="metric witness amendment 2026-07-18",
    ),
)

#: Claims R6 registers and refuses to test (core/09).
REFUSED_CLAIMS: tuple[Claim, ...] = tuple(
    _c(
        id=f"R6-C-2{i:02d}",
        verbatim=topic.replace("_", " "),
        source_class="LORE",
        translation="not translated; R6 does not test this claim",
        required_evidence=(
            "independent medical/ethics programme",
            "institutional oversight",
            "preregistration",
        ),
        standing="REFUSED_NOT_TESTED",
        ceiling=(
            "No result. Registering the refusal keeps the claim "
            "visible instead of silently absent."
        ),
        provenance="JH corpus (biological lane)",
    )
    for i, topic in enumerate((
        "dna_repair",
        "hydrogen_bonds_and_chromosomes",
        "regeneration",
        "reduced_food_requirements",
        "chakras",
        "gamma_brainwaves",
        "bodily_phryll_harvesting",
        "water_programming",
        "disease_treatment",
    ), start=1)
)

ALL_CLAIMS: tuple[Claim, ...] = (
    APPARATUS_CLAIMS + WITNESS_CLAIMS + REFUSED_CLAIMS
)


def registry() -> dict[str, Claim]:
    """All claims by id. Raises if any id is duplicated."""
    out: dict[str, Claim] = {}
    for c in ALL_CLAIMS:
        if c.id in out:
            raise ValueError(f"duplicate claim id {c.id!r}")
        out[c.id] = c
    return out


def corrections() -> tuple[Claim, ...]:
    """Claims that are wrong as stated, with the correction."""
    return tuple(c for c in ALL_CLAIMS if c.correction)


def refused() -> tuple[Claim, ...]:
    return tuple(c for c in ALL_CLAIMS
                 if c.standing == "REFUSED_NOT_TESTED")


def claim_records() -> list[dict]:
    """Flat records for the canonical store / workbook."""
    return [c.as_record() for c in ALL_CLAIMS]
