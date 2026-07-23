"""A01 — source registry, privacy scanning, and the claim ledger.

Three jobs, all of them about provenance rather than physics.

**Sources.** Every equation R11 implements is traceable to a named
authority: ITRF and Earth orientation, planetary magnetic-field models,
Rabi and Ramsey resonance, hydrogen-maser theory, the Cs-133 hyperfine
definition and its systematic shifts, Cs-137 to Ba-137 decay data,
Ephemeris Time, quartz flywheels, the dynamical-Casimir literature, and
planetary/hydrogenic scaling. A registered source is a *citation*, never
a private file path.

**Privacy.** Public generation must never read the private operator
delta. :func:`refuse_private_delta_read` blocks any read whose path lands
in the ignored private area, and :func:`privacy_scan` runs the committed
and history scanners from :mod:`r10.firewall` over the public tree.

**The declared residual.** One condition cannot be satisfied and is
therefore *declared* rather than quietly dropped: identity strings for
the alleged communicators exist in the public tree and in immutable
history, reaching back to the frozen v2.0.0 baseline. Purging them would
require rewriting published history and re-cutting released tags, which
release policy forbids. The operator reviewed this and elected to leave
history intact. It is recorded here as
``DECLARED_RESIDUAL_EXPOSURE`` — by category, never by repeating the
strings — exactly as :func:`r10.firewall.frozen_surface_exposure` already
records the frozen absolute-path residual. A clean tree with the residual
quietly excluded would not be an honest pass.

Nothing here is measured.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class SourceError(RuntimeError):
    """Raised on an unregistered source, a bad trace, or a privacy breach."""


class SourceKind(Enum):
    ESTABLISHED_SOURCE = "ESTABLISHED_SOURCE"
    CONVENTIONAL_LITERATURE = "CONVENTIONAL_LITERATURE"
    DERIVED_ARITHMETIC = "DERIVED_ARITHMETIC"
    ANALYTIC_MODEL = "ANALYTIC_MODEL"
    SOURCE_CLAIM = "SOURCE_CLAIM"
    BLOCKED_MISSING_DATA = "BLOCKED_MISSING_DATA"


@dataclass(frozen=True)
class SourceRecord:
    """One registered authority. ``locator`` is a citation, not a path."""

    source_id: str
    title: str
    authority: str
    kind: SourceKind
    locator: str
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.source_id or not self.locator:
            raise SourceError("source_id and locator are required")
        low = self.locator.lower()
        if "c:\\" in low or low.startswith("/home/") or "private" in low:
            raise SourceError(
                "a source locator must be a citation, never a private or "
                "absolute filesystem path")

    @property
    def digest(self) -> str:
        parts = (self.source_id, self.title, self.authority,
                 self.kind.value, self.locator)
        return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()


#: The authorities R11 traces its equations to. Registered as citations.
SOURCE_REGISTRY: tuple[SourceRecord, ...] = (
    SourceRecord("SRC_ITRF", "International Terrestrial Reference Frame and "
                 "Earth orientation parameters", "IERS",
                 SourceKind.ESTABLISHED_SOURCE,
                 "IERS Conventions; IERS Annual Report (ITRF realizations)"),
    SourceRecord("SRC_WGS84", "World Geodetic System 1984 ellipsoid",
                 "NGA", SourceKind.ESTABLISHED_SOURCE,
                 "NGA WGS-84 definition (a = 6378137.0 m, 1/f = 298.257223563)"),
    SourceRecord("SRC_IGRF", "International Geomagnetic Reference Field",
                 "IAGA", SourceKind.ESTABLISHED_SOURCE,
                 "IAGA IGRF model coefficients and epochs"),
    SourceRecord("SRC_PLANET_MAG", "Planetary magnetic-field models "
                 "(Mars, Moon, Mercury, Jupiter, Venus)", "planetary literature",
                 SourceKind.CONVENTIONAL_LITERATURE,
                 "Mission-derived field models; crustal-anomaly maps"),
    SourceRecord("SRC_RABI", "Rabi resonance / molecular-beam magnetic resonance",
                 "Rabi et al.", SourceKind.CONVENTIONAL_LITERATURE,
                 "Rabi, Zacharias, Millman, Kusch (1938) and standard texts"),
    SourceRecord("SRC_RAMSEY", "Ramsey separated oscillatory fields",
                 "N. F. Ramsey", SourceKind.CONVENTIONAL_LITERATURE,
                 "Ramsey, Molecular Beams; separated-field method"),
    SourceRecord("SRC_HMASER", "Hydrogen maser theory and error budget",
                 "frequency-standards literature",
                 SourceKind.CONVENTIONAL_LITERATURE,
                 "Standard hydrogen-maser treatments (wall shift, cavity pulling)"),
    SourceRecord("SRC_CS133", "Cs-133 ground-state hyperfine transition",
                 "BIPM", SourceKind.ESTABLISHED_SOURCE,
                 "BIPM SI Brochure: the second, 9 192 631 770 Hz by definition"),
    SourceRecord("SRC_CS137", "Cs-137 to Ba-137 decay data",
                 "nuclear data evaluation", SourceKind.CONVENTIONAL_LITERATURE,
                 "Evaluated nuclear structure/decay data (half-life, branching)"),
    SourceRecord("SRC_ET", "Ephemeris Time and its successors",
                 "IAU", SourceKind.ESTABLISHED_SOURCE,
                 "IAU resolutions on time scales (ET, TDT/TT, TDB)"),
    SourceRecord("SRC_QUARTZ", "Quartz oscillator flywheels",
                 "frequency-control literature",
                 SourceKind.CONVENTIONAL_LITERATURE,
                 "Standard quartz-oscillator and servo/flywheel treatments"),
    SourceRecord("SRC_DYNCASIMIR", "Dynamical Casimir effect experiments",
                 "quantum-optics literature",
                 SourceKind.CONVENTIONAL_LITERATURE,
                 "Superconducting-circuit dynamical Casimir observations"),
    SourceRecord("SRC_TRUNCPHOTON",
                 "A truncated photon (Rukan, Gulla & Skaar, Univ. of Oslo)",
                 "arXiv:2510.21636v2, dated 26 May 2026",
                 SourceKind.ESTABLISHED_SOURCE,
                 "arXiv:2510.21636v2 'A truncated photon', main text and "
                 "supplemental material",
                 notes="INGESTED in the R11 delta and hash-verified; its "
                       "equations are REGISTERED in r11/photonadapter.py, "
                       "not re-derived. No QFT solver exists here, so no "
                       "quantum result is reproduced or bench-validated"),
    SourceRecord("SRC_CAVITY_MODEMIX",
                 "Efficient operator method for modelling mode mixing in "
                 "misaligned optical cavities (Hughes, Doherty, Blackmore, "
                 "Horak & Goodwin)",
                 "arXiv:2306.05929v2, Oxford / Southampton",
                 SourceKind.CONVENTIONAL_LITERATURE,
                 "arXiv:2306.05929v2, Fabry-Perot mode mixing under "
                 "transverse mirror misalignment",
                 notes="supplied alongside the R11 delta. Conventional "
                       "cavity optics; registered for the optical detector "
                       "lane. No R11 claim depends on it"),
    SourceRecord("SRC_ORBITS", "Planetary orbital dynamics and hydrogenic "
                 "orbital scaling", "standard texts",
                 SourceKind.CONVENTIONAL_LITERATURE,
                 "Celestial mechanics; hydrogenic r ~ n^2/Z scaling"),
)

_BY_ID = {s.source_id: s for s in SOURCE_REGISTRY}

#: SHA-256 of reference PDFs ingested in the R11 delta, verified by
#: re-hashing the actual files. The documents themselves are NOT in the
#: public tree; only their identity and digest are recorded here.
REFERENCE_HASHES: dict[str, str] = {
    "SRC_TRUNCPHOTON":
        "b9e54ac8b1f7a4f7a1d00f98d540d1941684f3483bc4b96648337a6693f6472e",
    "SRC_CAVITY_MODEMIX":
        "e6cf53234d6b99a23d63caffbe79e0e0b755de88d30078d0cad5559747a3cfd6",
}

#: A provenance note the delta forced into the open. The R11 delta named
#: the truncated-photon paper and gave its digest, but the file actually
#: attached to the request was a DIFFERENT paper (the cavity mode-mixing
#: one). Both were located and hashed: the named paper's digest matched
#: exactly, and the attachment was registered separately on its own
#: merits. Recorded rather than glossed, because "the attachment is the
#: paper" is precisely the kind of assumption this registry exists to stop.
ATTACHMENT_DISCREPANCY = {
    "named_in_request": "SRC_TRUNCPHOTON (arXiv:2510.21636v2)",
    "named_digest_status": "VERIFIED_MATCH",
    "actually_attached": "SRC_CAVITY_MODEMIX (arXiv:2306.05929v2)",
    "resolution": ("both documents located and hashed; the named paper's "
                   "equations are the ones registered, and the attachment "
                   "is registered separately as conventional cavity optics"),
    "status": "RESOLVED_BOTH_REGISTERED",
}


def verify_reference_hash(source_id: str, digest: str) -> bool:
    """True iff ``digest`` matches the recorded digest for the source."""
    if source_id not in REFERENCE_HASHES:
        raise SourceError(f"no reference digest recorded for {source_id!r}")
    return REFERENCE_HASHES[source_id] == digest


def get_source(source_id: str) -> SourceRecord:
    if source_id not in _BY_ID:
        raise SourceError(f"unregistered source {source_id!r}")
    return _BY_ID[source_id]


#: equation/model id -> the sources it is traceable to.
TRACEABILITY: dict[str, tuple[str, ...]] = {
    "geodetic_to_ecef": ("SRC_WGS84",),
    "south_up_rotation": ("SRC_ITRF",),
    "magnetic_gradient_zero": ("SRC_IGRF", "SRC_PLANET_MAG"),
    "planetary_root_certificate": ("SRC_PLANET_MAG",),
    "rabi_flopping": ("SRC_RABI",),
    "ramsey_fringe": ("SRC_RAMSEY",),
    "cavity_pulling": ("SRC_HMASER",),
    "cs133_definition": ("SRC_CS133",),
    "cs137_coarse_age": ("SRC_CS137",),
    "ephemeris_time": ("SRC_ET",),
    "quartz_flywheel": ("SRC_QUARTZ",),
    "bogoliubov_photon_creation": ("SRC_DYNCASIMIR", "SRC_TRUNCPHOTON"),
    "hydrogenic_scaling": ("SRC_ORBITS",),
}


def trace(equation_id: str) -> tuple[SourceRecord, ...]:
    """Return the authorities an implemented equation rests on."""
    if equation_id not in TRACEABILITY:
        raise SourceError(
            f"no source trace registered for {equation_id!r}; every "
            f"implemented equation must be traceable to an authority")
    return tuple(get_source(s) for s in TRACEABILITY[equation_id])


@dataclass(frozen=True)
class CorrectionReceipt:
    """A recorded correction. Corrections are appended, never silent."""

    receipt_id: str
    what_changed: str
    why: str
    supersedes: str | None = None
    status: str = "APPLIED"


# --- privacy -----------------------------------------------------------

#: Path fragments that mark the ignored private area. Public generation
#: must never read from these.
PRIVATE_MARKERS = ("internal-docs", "private_operator_delta",
                   "PRIVATE_OPERATOR_DELTA")


def is_private_path(path: str | Path) -> bool:
    s = str(path).replace("\\", "/").lower()
    return any(m.lower() in s for m in PRIVATE_MARKERS)


def refuse_private_delta_read(path: str | Path) -> None:
    """Refuse to read the private operator delta during public generation."""
    if is_private_path(path):
        raise SourceError(
            "refused: public generation must not read the private operator "
            "delta or any ignored private document. Private material is "
            "local provenance only and never enters public output.")


def privacy_scan(root: Path, *, max_commits: int = 200) -> dict:
    """Run the committed-tree and history scanners over the public tree."""
    from r10 import firewall as F           # imported lazily, reused not copied

    committed = F.scan_committed(Path(root))
    history = F.scan_git_history(Path(root), max_commits=max_commits)
    serious = [f for f in history
               if f.category in ("CREDENTIAL", "PRIVATE_CHANNELLING")]
    return {
        "committed_findings": len(committed),
        "committed_clean": not committed,
        "history_categories": sorted({f.category for f in history}),
        "history_serious": [f.as_record() for f in serious],
        "declared_residual": DECLARED_RESIDUAL,
        "verdict": ("PRIVACY_SCAN_CLEAN_WITH_DECLARED_RESIDUAL"
                    if not committed and not serious
                    else "PRIVACY_SCAN_FINDINGS"),
    }


#: The residual that cannot be repaired without rewriting published
#: history. Recorded by CATEGORY; the strings themselves are not repeated
#: here, because a leak report must not restate the leak.
DECLARED_RESIDUAL = {
    "category": "ALLEGED_COMMUNICATOR_IDENTITY_STRINGS",
    "surfaces": ["public working tree", "immutable Git history",
                 "published release tags"],
    "earliest_surface": "the frozen v2.0.0 baseline",
    "status": "DECLARED_RESIDUAL_EXPOSURE",
    "why_not_repaired": (
        "removal would require rewriting published Git history and "
        "re-cutting released tags, which release policy forbids "
        "('tags and records never modified'); existing clones would retain "
        "the old history regardless"),
    "operator_decision": (
        "reviewed and accepted; history is not to be rewritten. Recorded "
        "rather than silently excluded"),
    "assessed_severity": (
        "LOW-MODERATE: names of alleged communicators already published "
        "across prior releases. No credential, location, medical, or "
        "financial data is exposed"),
    "forward_rule": (
        "no NEW identity strings are added by R11; public modules use the "
        "neutral aliases only"),
}


def refuse_new_identity_exposure(text: str) -> None:
    """Refuse to add NEW identity strings to public output.

    The historical residual is declared; it is not a licence to add more.
    """
    raise SourceError(
        "refused: R11 public output uses neutral aliases only. The "
        "pre-existing identity exposure in frozen history is a declared "
        "residual, not permission to introduce new identity strings.")


def sources_report() -> dict:
    return {
        "what_this_is": (
            "the R11 source registry, equation traceability, correction "
            "receipts, and the privacy scan with its declared residual"),
        "registered_sources": len(SOURCE_REGISTRY),
        "traced_equations": len(TRACEABILITY),
        "reference_digests": len(REFERENCE_HASHES),
        "attachment_discrepancy": ATTACHMENT_DISCREPANCY["status"],
        "blocked_sources": [s.source_id for s in SOURCE_REGISTRY
                            if s.kind is SourceKind.BLOCKED_MISSING_DATA],
        "declared_residual": DECLARED_RESIDUAL["status"],
        "evidence_class": "ESTABLISHED_SOURCE and CONVENTIONAL_LITERATURE",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "SOURCES_REGISTERED_PRIVACY_RESIDUAL_DECLARED",
        "what_this_does_not_say": (
            "The truncated-photon paper was read and its PDF digest "
            "verified, but that means its equations are REGISTERED, not "
            "re-derived: no QFT solver exists here and no quantum result "
            "is reproduced or bench-validated. It also does not claim the "
            "public tree is free of historical identity strings — that "
            "exposure is declared, not repaired."),
    }
