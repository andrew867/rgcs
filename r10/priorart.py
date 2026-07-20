"""S05/S09 — conventional prior art, from public academic sources.

Two peer-reviewed papers were supplied with the source corpus. They are
ordinary public literature -- not private material -- and they are
recorded here as `CONVENTIONAL_LITERATURE`, the strongest evidence class
this project produces without a bench.

Both do the same useful thing to the surrounding lore: they replace a
dramatic number with a smaller, better-supported one.

**The firefly paper** (Silver 2026) is titled "Resolving a century of
overestimation", and that is its result. A firefly flash contains
roughly 10^8 to 10^11 photons -- *far fewer* than the 10^13 to 10^14
implied by Coblentz's 1912 figure. So the headline is not "fireflies are
bright"; it is that the classic estimate was high by three to six orders
of magnitude, and the honest figure is much smaller and range-valued.
Quoting the old number, or the top of the new range, would repeat the
error the paper exists to correct.

**The tetrahedron paper** (Vilcu & Vilcu 2018) is the exact prior art
for :mod:`r10.inverse`. The R10.1 Q19 work reproduced its result --
estimating a tetrahedron's vertices from uniform interior points via
moments -- but could not fetch the paper at the time and so recorded
`prior_art.verified = False`. The paper is now in hand. The reproduction
was independent and its constants (20, 60) were derived from scratch, so
this does not change the mathematics; it changes the citation from
"unverified" to "confirmed", and confirms the work is a reproduction of
published prior art rather than a discovery.

Nothing here is measured by this project. These are other people's
measurements and proofs, cited.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class PriorArtError(ValueError):
    """Raised when prior art is misrepresented."""


@dataclass(frozen=True)
class Reference:
    """A conventional, public, peer-reviewed source."""

    key: str
    authors: str
    year: int
    title: str
    venue: str
    doi: str
    what_it_establishes: str
    limitations: str
    evidence_class: str = "CONVENTIONAL_LITERATURE"
    supersedes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.doi:
            raise PriorArtError(f"{self.key}: a reference needs a DOI")
        if self.evidence_class != "CONVENTIONAL_LITERATURE":
            raise PriorArtError(
                f"{self.key}: these are public literature, not a "
                f"project result")


FIREFLY = Reference(
    key="silver_2026_firefly",
    authors="D. H. Silver",
    year=2026,
    title="How bright is a firefly? Resolving a century of overestimation",
    venue="American Journal of Physics 94, 520-524",
    doi="10.1119/5.0325834",
    what_it_establishes=(
        "a firefly flash contains roughly 1e8 to 1e11 photons, far "
        "fewer than the 1e13 to 1e14 implied by Coblentz's 1912 "
        "estimate -- a downward correction of three to six orders of "
        "magnitude"),
    limitations=(
        "the figure is a range, not a point. Reconstructing absolute "
        "photons per flash also requires in-vivo substrate turnover "
        "and measurement geometry that the quantum-yield and "
        "intensity data do not fix, so the range is irreducible with "
        "present inputs"),
    supersedes=("Coblentz 1912 estimate of 1e13-1e14 photons/flash",),
)

TETRAHEDRON = Reference(
    key="vilcu_2018_tetrahedron",
    authors="A.-D. Vilcu and G.-E. Vilcu",
    year=2018,
    title=("An algorithm to estimate the vertices of a tetrahedron "
           "from uniform random points inside"),
    venue="Annali di Matematica Pura ed Applicata 197, 487-500",
    doi="10.1007/s10231-017-0688-6",
    what_it_establishes=(
        "the published method that r10.inverse reproduces: recovering "
        "a tetrahedron's four vertices from points drawn uniformly "
        "inside it, using moments of the point cloud"),
    limitations=(
        "the result holds for the UNIFORM interior density only. It "
        "says nothing about non-uniform density, shell-confined "
        "support, or a moving target -- which are exactly the "
        "conditions under which r10.inverse measured the estimator to "
        "fail (biases of 25% and worse, and outright "
        "non-identifiability)"),
)

REFERENCES = (FIREFLY, TETRAHEDRON)


#: The firefly figures, kept as an explicit before/after so the
#: correction cannot be quietly dropped.
FIREFLY_PHOTONS = {
    "corrected_2026_low": 1e8,
    "corrected_2026_high": 1e11,
    "coblentz_1912_low": 1e13,
    "coblentz_1912_high": 1e14,
    "correction_orders_of_magnitude_low": 2,   # 1e11 -> 1e13
    "correction_orders_of_magnitude_high": 6,  # 1e8  -> 1e14
    "direction": "DOWNWARD",
    "framing": (
        "the paper's result is a REDUCTION. The interesting number is "
        "not the photon count but the size of the old error"),
}


def firefly_photons_per_flash() -> dict:
    lo, hi = FIREFLY_PHOTONS["corrected_2026_low"], \
        FIREFLY_PHOTONS["corrected_2026_high"]
    return {
        "reference": FIREFLY.key,
        "photons_low": lo,
        "photons_high": hi,
        "range_decades": 3,
        "old_estimate_low": FIREFLY_PHOTONS["coblentz_1912_low"],
        "old_estimate_high": FIREFLY_PHOTONS["coblentz_1912_high"],
        "correction": FIREFLY_PHOTONS["framing"],
        "limitation": FIREFLY.limitations,
    }


def confirm_tetrahedron_prior_art() -> dict:
    """Close the Q19 'could not verify' caveat.

    The paper is now available and matches the reproduced method. The
    reproduction stays a reproduction; the citation becomes verified.
    """
    return {
        "reference": TETRAHEDRON.key,
        "doi": TETRAHEDRON.doi,
        "verified": True,
        "reproduced_by": "r10.inverse",
        "novelty": "NONE",
        "relationship": (
            "r10.inverse independently derived the estimator's "
            "constants (20 and 60) and then reproduced the published "
            "result. Having the paper in hand confirms the citation "
            "without changing the mathematics."),
        "what_the_paper_does_not_cover": (
            "non-uniform density, shell support, and motion -- the "
            "regimes r10.inverse measured as biased or "
            "non-identifiable. The paper's guarantee is for uniform "
            "interior sampling and is not evidence about any hidden "
            "object's shape"),
    }


def refuse_lore_promotion(reference_key: str) -> None:
    """A conventional citation does not authenticate a source claim."""
    raise PriorArtError(
        f"reference {reference_key!r} is conventional public "
        f"literature. Citing it lends its authority to its own "
        f"measured claim and to nothing else. It does not corroborate "
        f"any source-corpus assertion, and a source claim that happens "
        f"to mention fireflies, tetrahedra, or photons is not "
        f"supported by a paper that shares its vocabulary.")


def prior_art_report() -> dict:
    return {
        "references": [
            {"key": r.key, "authors": r.authors, "year": r.year,
             "title": r.title, "venue": r.venue, "doi": r.doi,
             "establishes": r.what_it_establishes,
             "limitations": r.limitations,
             "evidence_class": r.evidence_class,
             "supersedes": list(r.supersedes)}
            for r in REFERENCES],
        "firefly": firefly_photons_per_flash(),
        "tetrahedron": confirm_tetrahedron_prior_art(),
        "both_papers_do_the_same_thing": (
            "each replaces a dramatic figure with a smaller, "
            "better-supported one -- the firefly count downward by "
            "orders of magnitude, and the tetrahedron estimator's "
            "scope down to the uniform case it was proved for"),
        "evidence_class": "CONVENTIONAL_LITERATURE",
        "measured_here": "nothing",
    }
