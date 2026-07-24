"""P03 — the source corpus, normalized into typed records and hashed.

The equations, mechanisms, observables, assumptions and non-claims that
R13 draws on are conventional physics and standard literature. This module
registers them as exactly that: typed records, each traceable to a source
id and each carried with a hash of the document it comes from. Nothing
here is re-derived and nothing here is bench-validated — an equation is
*registered*, which is a statement about provenance, not about physics.

Five record types keep the corpus honest about what each entry is:

* :class:`SourceEquation` — a named equation with its LaTeX, its meaning,
  its claim class, and the digest of its source. Its ``__post_init__``
  refuses any record marked ``rederived_here`` or ``bench_validated``,
  because registering a paper's equation is neither of those things.
* :class:`MechanismRecord` — a physical mechanism named in a source.
* :class:`ObservableRecord` — a quantity a source treats as measurable.
* :class:`AssumptionRecord` — an assumption a source's result rests on.
* :class:`NonClaimRecord` — something a source explicitly does *not*
  claim, recorded so a later reader cannot quietly promote it.

Provenance is by digest: :func:`register_hash` records the SHA-256 of a
source document and :func:`verify_hash` checks a digest against it. A
wrong digest fails.

Two refusals are load-bearing.
:func:`refuse_paper_as_carrier_evidence` refuses to read a registered
paper as evidence that anything in it is an RGCS carrier — registering a
paper is citation, not confirmation.
:func:`refuse_unregistered_equation` refuses an equation the registry does
not carry.

Nothing here is measured, and no digest here is of any private file: the
seed digests are hashes of each source's own public citation label.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

DEFAULT_VERDICT = "SOURCE_CORPUS_REGISTERED_BY_HASH"

#: The claim classes a corpus record may declare. A registered equation is
#: established physics or conventional literature; it is never something
#: stronger, because registration does not re-derive or measure it.
CLAIM_CLASSES = (
    "EXACT_IDENTITY",
    "SOURCE_ESTABLISHED_PHYSICS",
    "CONVENTIONAL_LITERATURE",
    "DERIVED_ARITHMETIC",
    "ANALYTIC_MODEL",
    "NUMERICAL_SIMULATION",
    "REPOSITORY_COMPUTATIONAL_RESULT",
    "ENGINEERING_CANDIDATE",
    "SOURCE_CLAIM",
    "RETROSPECTIVE_NUMERIC_MATCH",
    "PROSPECTIVE_PREDICTION",
    "BENCH_MEASUREMENT",
    "UNSUPPORTED",
    "BLOCKED_MISSING_INPUT",
)

#: The claim classes a *registered* corpus entry is allowed to hold. An
#: entry may only be established physics or conventional literature.
REGISTRABLE_CLASSES = (
    "SOURCE_ESTABLISHED_PHYSICS",
    "CONVENTIONAL_LITERATURE",
)


class SrcRegistryError(RuntimeError):
    """Raised on an illegal corpus record or an unregistered lookup.

    Covers the construction-time refusals (a record marked re-derived or
    bench-validated, a bad claim class, a malformed digest) and the two
    governance refusals :func:`refuse_paper_as_carrier_evidence` and
    :func:`refuse_unregistered_equation`.
    """


def _valid_sha256(digest: str) -> str:
    """Return a normalized 64-hex-character SHA-256, or refuse."""
    if not isinstance(digest, str):
        raise SrcRegistryError("a SHA-256 digest must be a hex string")
    d = digest.strip().lower()
    if len(d) != 64 or any(c not in "0123456789abcdef" for c in d):
        raise SrcRegistryError(
            f"{digest!r} is not a 64-character hexadecimal SHA-256 digest")
    return d


def _source_digest(source_id: str) -> str:
    """A stable placeholder digest for a source *document*, by source id.

    These seed digests are the SHA-256 of the source id's own public
    citation label, never of any private document. Equations that come
    from the same source share its digest, exactly as they share the one
    document. They give the registry real, verifiable digests to exercise
    :func:`verify_hash` without importing any file from outside the public
    tree.
    """
    return hashlib.sha256(
        f"RGCS-R13-SOURCE-CITATION\x1f{source_id}".encode("utf-8")).hexdigest()


# --- the five typed record kinds -----------------------------------------

@dataclass(frozen=True)
class SourceEquation:
    """One equation, registered by provenance — not re-derived, not measured.

    ``sha256`` is the hex digest of the source document, passed in.
    ``rederived_here`` and ``bench_validated`` must both be False: an
    equation in this registry is *cited*, and a record that claims to have
    re-derived or bench-validated it is refused at construction.
    """

    eq_id: str
    latex_text: str
    meaning: str
    source_id: str
    sha256: str
    claim_class: str = "CONVENTIONAL_LITERATURE"
    rederived_here: bool = False
    bench_validated: bool = False

    def __post_init__(self) -> None:
        for name in ("eq_id", "latex_text", "meaning", "source_id"):
            if not str(getattr(self, name)).strip():
                raise SrcRegistryError(
                    f"a source equation needs a non-empty {name}")
        if self.claim_class not in REGISTRABLE_CLASSES:
            raise SrcRegistryError(
                f"a registered equation must be one of {REGISTRABLE_CLASSES}; "
                f"{self.claim_class!r} claims more than registration gives")
        object.__setattr__(self, "sha256", _valid_sha256(self.sha256))
        if self.rederived_here:
            raise SrcRegistryError(
                f"{self.eq_id}: registering an equation is not re-deriving "
                f"it. Nothing in this registry is rederived_here; the record "
                f"is a citation with a digest, not a derivation.")
        if self.bench_validated:
            raise SrcRegistryError(
                f"{self.eq_id}: registering an equation is not measuring it. "
                f"Nothing in this registry is bench_validated; no apparatus "
                f"was operated to confirm it here.")

    @property
    def digest(self) -> str:
        """SHA-256 over the record's identifying fields (not the source hash)."""
        parts = (self.eq_id, self.latex_text, self.meaning,
                 self.source_id, self.claim_class, self.sha256)
        return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MechanismRecord:
    """A physical mechanism named in a source."""

    id: str
    text: str
    source_id: str
    status: str = "REGISTERED"

    def __post_init__(self) -> None:
        if not str(self.id).strip() or not str(self.text).strip():
            raise SrcRegistryError("a mechanism needs an id and text")


@dataclass(frozen=True)
class ObservableRecord:
    """A quantity a source treats as observable/measurable."""

    id: str
    text: str
    source_id: str
    status: str = "REGISTERED"

    def __post_init__(self) -> None:
        if not str(self.id).strip() or not str(self.text).strip():
            raise SrcRegistryError("an observable needs an id and text")


@dataclass(frozen=True)
class AssumptionRecord:
    """An assumption a source's result rests on."""

    id: str
    text: str
    source_id: str
    status: str = "REGISTERED"

    def __post_init__(self) -> None:
        if not str(self.id).strip() or not str(self.text).strip():
            raise SrcRegistryError("an assumption needs an id and text")


@dataclass(frozen=True)
class NonClaimRecord:
    """Something a source explicitly does NOT claim, recorded to block promotion."""

    id: str
    text: str
    source_id: str
    status: str = "REGISTERED_NON_CLAIM"

    def __post_init__(self) -> None:
        if not str(self.id).strip() or not str(self.text).strip():
            raise SrcRegistryError("a non-claim needs an id and text")


# --- the seeded registry -------------------------------------------------

#: Six representative equations, all conventional physics / standard
#: literature, none re-derived and none bench-validated. The meanings are
#: generic and correct; no specific paper's contents are reproduced.
REGISTRY: tuple[SourceEquation, ...] = (
    SourceEquation(
        "EQ_DAMPED_OSC_GREEN",
        r"G(\omega) = 1/(\omega_0^2 - \omega^2 - i\gamma\omega)",
        "Green function (frequency response) of a damped harmonic "
        "oscillator; a Lorentzian resonance with damping rate gamma",
        "SRC_LINEAR_RESPONSE",
        _source_digest("SRC_LINEAR_RESPONSE"),
        claim_class="SOURCE_ESTABLISHED_PHYSICS"),
    SourceEquation(
        "EQ_BOGOLIUBOV",
        r"a_{out} = \alpha a_{in} + \beta a_{in}^{\dagger},\ "
        r"|\alpha|^2 - |\beta|^2 = 1",
        "Bogoliubov transformation: a linear canonical transformation of "
        "bosonic mode operators preserving the commutator",
        "SRC_QUANTUM_OPTICS",
        _source_digest("SRC_QUANTUM_OPTICS"),
        claim_class="CONVENTIONAL_LITERATURE"),
    SourceEquation(
        "EQ_BVD",
        r"Y(\omega) = i\omega C_0 + "
        r"1/(R_1 + i\omega L_1 + 1/(i\omega C_1))",
        "Butterworth-Van Dyke model: admittance of a piezoelectric "
        "resonator as a motional RLC branch across a static capacitance",
        "SRC_RESONATOR_CIRCUITS",
        _source_digest("SRC_RESONATOR_CIRCUITS"),
        claim_class="CONVENTIONAL_LITERATURE"),
    SourceEquation(
        "EQ_BRAGG",
        r"n\lambda = 2 d \sin\theta",
        "Bragg law relating diffraction order, wavelength, lattice plane "
        "spacing and scattering angle",
        "SRC_CRYSTALLOGRAPHY",
        _source_digest("SRC_CRYSTALLOGRAPHY"),
        claim_class="SOURCE_ESTABLISHED_PHYSICS"),
    SourceEquation(
        "EQ_KRAMERS_KRONIG",
        r"\mathrm{Re}\,\chi(\omega) = "
        r"\frac{1}{\pi}\,\mathrm{P}\!\int "
        r"\frac{\mathrm{Im}\,\chi(\omega')}{\omega'-\omega}\,d\omega'",
        "Kramers-Kronig relations: causality ties the real and imaginary "
        "parts of a linear response function by a Hilbert transform",
        "SRC_LINEAR_RESPONSE",
        _source_digest("SRC_LINEAR_RESPONSE"),
        claim_class="SOURCE_ESTABLISHED_PHYSICS"),
    SourceEquation(
        "EQ_IGRF_SECULAR",
        r"B(t) = B(t_0) + \dot{B}\,(t - t_0)",
        "IGRF secular variation: linear-in-time drift of the geomagnetic "
        "field coefficients between reference epochs",
        "SRC_GEOMAGNETISM",
        _source_digest("SRC_GEOMAGNETISM"),
        claim_class="CONVENTIONAL_LITERATURE"),
)

_BY_EQ_ID = {e.eq_id: e for e in REGISTRY}

#: A few representative mechanisms, observables, assumptions and
#: non-claims, kept generic.
MECHANISMS: tuple[MechanismRecord, ...] = (
    MechanismRecord("MECH_RESONANT_ABSORPTION",
                    "resonant energy absorption by a damped oscillator "
                    "driven near its natural frequency", "SRC_LINEAR_RESPONSE"),
    MechanismRecord("MECH_PARAMETRIC_PAIR",
                    "parametric pair creation from a time-dependent "
                    "boundary condition, described by a Bogoliubov mixing",
                    "SRC_QUANTUM_OPTICS"),
)

OBSERVABLES: tuple[ObservableRecord, ...] = (
    ObservableRecord("OBS_LINEWIDTH",
                     "the full width at half maximum of a resonance, "
                     "related to the damping rate", "SRC_LINEAR_RESPONSE"),
    ObservableRecord("OBS_DIFFRACTION_ANGLE",
                     "the scattering angle at which a diffraction order "
                     "appears for a given lattice spacing", "SRC_CRYSTALLOGRAPHY"),
)

ASSUMPTIONS: tuple[AssumptionRecord, ...] = (
    AssumptionRecord("ASM_LINEARITY",
                     "the response is linear in the drive, so superposition "
                     "and a single transfer function apply", "SRC_LINEAR_RESPONSE"),
    AssumptionRecord("ASM_CAUSALITY",
                     "the response is causal and vanishes at infinite "
                     "frequency, which the Kramers-Kronig relation requires",
                     "SRC_LINEAR_RESPONSE"),
)

NON_CLAIMS: tuple[NonClaimRecord, ...] = (
    NonClaimRecord("NONCLAIM_NO_CARRIER",
                   "no registered source claims that any equation in it is "
                   "an RGCS carrier; registration is citation, not carrier "
                   "evidence", "SRC_QUANTUM_OPTICS"),
    NonClaimRecord("NONCLAIM_NO_MEASUREMENT",
                   "no registered equation is claimed to have been measured "
                   "or re-derived in this repository", "SRC_LINEAR_RESPONSE"),
)


# --- provenance by digest ------------------------------------------------

#: source_id -> registered SHA-256 digest. Seeded from the corpus.
_HASHES: dict[str, str] = {}


def register_hash(source_id: str, sha256: str) -> str:
    """Record the SHA-256 digest of a source document. Returns the digest."""
    if not str(source_id).strip():
        raise SrcRegistryError("a hash registration needs a source id")
    d = _valid_sha256(sha256)
    _HASHES[source_id] = d
    return d


def verify_hash(source_id: str, sha256: str) -> bool:
    """True iff ``sha256`` matches the digest registered for ``source_id``."""
    if source_id not in _HASHES:
        raise SrcRegistryError(
            f"no digest registered for {source_id!r}; register it first")
    return _HASHES[source_id] == _valid_sha256(sha256)


def _seed_hashes() -> None:
    """Register a digest for every source id named in the corpus."""
    for e in REGISTRY:
        if e.source_id not in _HASHES:
            _HASHES[e.source_id] = e.sha256


_seed_hashes()


# --- lookups and the two governance refusals -----------------------------

def get_equation(eq_id: str) -> SourceEquation:
    """The registered equation for ``eq_id``, or refuse."""
    if eq_id not in _BY_EQ_ID:
        raise SrcRegistryError(f"unregistered equation {eq_id!r}")
    return _BY_EQ_ID[eq_id]


def refuse_unregistered_equation(eq_id: str) -> None:
    """Refuse an equation the registry does not carry."""
    if eq_id not in _BY_EQ_ID:
        raise SrcRegistryError(
            f"refused: {eq_id!r} is not in the source registry. An equation "
            f"used here must be registered by id, with a source and a "
            f"digest, before it can be relied on.")


def refuse_paper_as_carrier_evidence(*_a, **_k) -> None:
    """Registering a paper is citation, not evidence of an RGCS carrier."""
    raise SrcRegistryError(
        "refused: registering a paper records that it exists and pins its "
        "digest. It is citation, not evidence that any equation, mechanism "
        "or observable in it is an RGCS carrier. A carrier claim needs a "
        "bench measurement, which this repository does not have.")


# --- the report ----------------------------------------------------------

def srcregistry_report() -> dict:
    return {
        "what_this_is": (
            "the R13 source corpus normalized into typed equations, "
            "mechanisms, observables, assumptions and non-claims, each "
            "registered by hash"),
        "registered_equations": len(REGISTRY),
        "mechanisms": len(MECHANISMS),
        "observables": len(OBSERVABLES),
        "assumptions": len(ASSUMPTIONS),
        "non_claims": len(NON_CLAIMS),
        "registered_hashes": len(_HASHES),
        "all_conventional_or_established": all(
            e.claim_class in REGISTRABLE_CLASSES for e in REGISTRY),
        "none_rederived": not any(e.rederived_here for e in REGISTRY),
        "none_bench_validated": not any(e.bench_validated for e in REGISTRY),
        "claim_class": "CONVENTIONAL_LITERATURE",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": DEFAULT_VERDICT,
        "what_this_does_not_say": (
            "It does not say any registered equation was re-derived or "
            "bench-validated here, nor that a registered paper is evidence "
            "for an RGCS carrier. Registration pins provenance by digest; "
            "it is citation, not confirmation, and nothing here is measured."),
    }
