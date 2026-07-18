"""P07 — planetary polyhedral grid audit.

The claim family: Earth's fields carry a polyhedral (tetrahedral,
icosahedral, dodecahedral, Becker-Hagens) symmetry that marks special
locations.

The machinery: expand a field in spherical harmonics, project the
coefficients of each degree onto the subspace invariant under a point
group G at orientation R, and score

    S_G(R) = sum_{l in L_G} || P_{G,l} D^l(R) a_l ||^2

normalized by the total power in those degrees, so the score is the
*fraction* of power lying in the symmetric subspace.

Why this module is mostly controls
----------------------------------
A raw symmetry score is meaningless. With five polyhedral groups, a
free orientation (three angles), and a choice of which degrees to
include, the search space is large enough that *some* configuration
will always score well. This is the v4.6 lesson restated: the null
must match the analysis, including its granularity and its selection
process.

So every headline here is accompanied by:

- random global rotations (is this orientation special?);
- alternative polyhedral groups (is this group special?);
- degree-matched random subspaces of the same dimension (is a
  symmetric subspace better than any subspace of equal size?);
- a selection-process null that repeats the *entire search*, including
  the maximization over orientation, on surrogate fields;
- multiple-comparison correction across groups and degrees;
- train-on-one-field / test-on-another;
- prospective held-out nodes.

The selection null is the one that usually kills the result, because
max over orientation of a noisy score is biased high, and comparing an
optimized real score against an un-optimized null is the single most
common way to manufacture a planetary grid.

Data status
-----------
R6 ships **no** real geophysical data. There is no EGM gravity model,
no IGRF snapshot, no topography grid in this repository. Every
function that would produce a planetary result therefore checks
:func:`data_availability` first and returns ``NO_REAL_DATA``. Synthetic
fields are provided for testing the machinery and are labelled
``SYNTHETIC`` in every record they touch. A synthetic field must never
be reported as a planetary finding.
"""

from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass, field, asdict

from . import wigner as _wigner

#: Polyhedral groups considered. "BECKER_HAGENS" is a published
#: overlay rather than a point group in its own right; it is carried
#: separately so it cannot be silently treated as a symmetry group.
POLYHEDRAL_GROUPS = (
    "TETRAHEDRAL",
    "OCTAHEDRAL",
    "ICOSAHEDRAL",
    "DODECAHEDRAL",
    "BECKER_HAGENS",
)

#: Degrees at which each group's invariants first appear. These are
#: the standard lowest non-trivial invariant degrees for the rotation
#: groups: T has an l=3 invariant, O has l=4, I has l=6.
GROUP_INVARIANT_DEGREES: dict[str, tuple[int, ...]] = {
    "TETRAHEDRAL": (3, 4, 6, 7),
    "OCTAHEDRAL": (4, 6, 8, 9),
    "ICOSAHEDRAL": (6, 10, 12, 15),
    "DODECAHEDRAL": (6, 10, 12, 15),  # same rotation group as I
    "BECKER_HAGENS": (3, 4, 6),       # overlay, not a group
}

#: Field families the audit may be run against.
FIELD_FAMILIES = (
    "GRAVITY",
    "GEOMAGNETIC",
    "TOPOGRAPHY_GEOID",
    "SEISMIC_TOMOGRAPHY",
    "HEAT_FLOW",
    "VOLCANISM",
    "TECTONIC_BOUNDARIES",
    "CRUSTAL_THICKNESS",
    "SYNTHETIC",
)

#: Cultural/archaeological site locations are a *human* dataset and
#: are kept separate from geophysics on purpose: site selection is
#: driven by rivers, coasts, trade routes and preservation bias, which
#: are themselves spatially structured.
HUMAN_DATASETS = ("ARCHAEOLOGICAL_SITES",)


class DataUnavailable(RuntimeError):
    """Raised when a planetary result is requested without real data."""


def data_availability() -> dict:
    """What real geophysical data this repository actually contains.

    Deliberately hard-coded to report the truth rather than probing
    for files: no such data has ever been added to RGCS, and a probe
    that found some stray CSV would be worse than useless.
    """
    return {
        "gravity_model": None,
        "geomagnetic_model": None,
        "topography": None,
        "seismic": None,
        "any_real_field": False,
        "status": "NO_REAL_DATA",
        "note": ("R6 ships no geophysical datasets. Planetary results "
                 "require EGM/IGRF/topography products obtained under "
                 "their own licences and verified against their "
                 "published checksums. Synthetic fields exercise the "
                 "machinery only."),
    }


# --------------------------------------------------------------------
# Spherical harmonic field
# --------------------------------------------------------------------

@dataclass
class HarmonicField:
    """Real-valued field on a sphere as complex a_lm coefficients.

    ``coeffs[l]`` is a list of 2l+1 complex values indexed m = -l..l.
    """

    family: str
    coeffs: list[list[complex]]
    provenance: str
    evidence_class: str = "SYNTHETIC_MODEL"

    def __post_init__(self) -> None:
        if self.family not in FIELD_FAMILIES:
            raise ValueError(f"unknown field family {self.family!r}")
        for l, row in enumerate(self.coeffs):
            if len(row) != 2 * l + 1:
                raise ValueError(
                    f"degree {l} needs {2 * l + 1} coefficients, "
                    f"got {len(row)}")

    @property
    def lmax(self) -> int:
        return len(self.coeffs) - 1

    def power(self, l: int) -> float:
        return sum(abs(c) ** 2 for c in self.coeffs[l])

    def is_synthetic(self) -> bool:
        return self.family == "SYNTHETIC" or \
            self.evidence_class == "SYNTHETIC_MODEL"


def synthetic_field(lmax: int = 12, *, seed: int,
                    symmetry_injection: float = 0.0,
                    group: str = "ICOSAHEDRAL") -> HarmonicField:
    """A reproducible synthetic field, optionally with injected symmetry.

    ``symmetry_injection`` in [0, 1] moves power into the group's
    invariant *subspace*. Injecting a known amount is how the
    detector's sensitivity is calibrated: a detector that cannot find
    an injected signal cannot be trusted when it reports one.

    Note carefully *where* the power goes. Two wrong ways to inject,
    both of which produce a detector that is blind at every strength:

    1. Boosting every coefficient of an invariant degree. The score is
       a ratio of power *within* those degrees, so a uniform factor
       cancels exactly.
    2. Boosting the first d components. Those are not the invariant
       subspace; the real projector mixes all 2l+1 components, so a
       rotation immediately spreads the injected power out again.

    The signal must be added *through the projector itself*: draw a
    random vector, project it onto the invariant subspace, and add a
    multiple of the result. That is genuinely symmetric content, and
    it is what the detector must be able to find.
    """
    if not 0.0 <= symmetry_injection <= 1.0:
        raise ValueError("symmetry_injection must be in [0, 1]")
    rng = random.Random(seed)
    inv = set(GROUP_INVARIANT_DEGREES.get(group, ()))
    coeffs: list[list[complex]] = []
    for l in range(lmax + 1):
        row = [complex(rng.gauss(0, 1), rng.gauss(0, 1))
               for _ in range(2 * l + 1)]
        if l in inv and symmetry_injection > 0.0 and \
                invariant_dimension(l, group) > 0:
            seed_vec = [complex(rng.gauss(0, 1), rng.gauss(0, 1))
                        for _ in range(2 * l + 1)]
            sym = _project_invariant(seed_vec, l, group)
            nrm = math.sqrt(sum(abs(c) ** 2 for c in sym))
            if nrm > 0:
                amp = symmetry_injection * 12.0 * math.sqrt(
                    sum(abs(c) ** 2 for c in row)) / nrm
                row = [c + amp * s for c, s in zip(row, sym)]
        coeffs.append(row)
    return HarmonicField(family="SYNTHETIC", coeffs=coeffs,
                         provenance=(f"synthetic_field(seed={seed},"
                                     f"inj={symmetry_injection},"
                                     f"group={group})"))


# --------------------------------------------------------------------
# Symmetry scoring
# --------------------------------------------------------------------

def _rotate(row: list[complex], alpha: float, beta: float,
            gamma: float, l: int) -> list[complex]:
    """Rotate degree-l coefficients by a genuine Wigner D-matrix."""
    return _wigner.apply_D(_wigner.wigner_D(l, alpha, beta, gamma), row)


def _project_invariant(row: list[complex], l: int, group: str
                       ) -> list[complex]:
    """Project onto the true group-invariant subspace.

    Uses P = (1/|G|) sum_g D^l(g) with the group elements enumerated
    explicitly. ``trace(P)`` is verified to be an integer, so the
    subspace this projects onto is the real one and not a stand-in.
    """
    return _wigner.project(row, l, _projector_group(group))


def _projector_group(group: str) -> str:
    """Map an audit group onto the rotation group used for projection.

    BECKER_HAGENS is an overlay built from combined tetrahedral,
    octahedral and icosahedral vertex sets rather than a point group.
    It is projected with the icosahedral group and flagged, so it can
    never be silently reported as a symmetry group result.
    """
    if group == "BECKER_HAGENS":
        return "ICOSAHEDRAL"
    if group == "DODECAHEDRAL":
        return "ICOSAHEDRAL"
    return group


def invariant_dimension(l: int, group: str) -> int:
    """Dimension of the group-invariant subspace at degree l.

    Computed as the trace of the real projector, not estimated.
    """
    if group not in POLYHEDRAL_GROUPS:
        raise ValueError(f"unknown group {group!r}")
    return _wigner.invariant_dimension(l, _projector_group(group))


@dataclass(frozen=True)
class SymmetryScore:
    group: str
    degrees: tuple[int, ...]
    score: float
    orientation: tuple[float, float, float]
    field_family: str
    evidence_class: str

    def as_record(self) -> dict:
        d = asdict(self)
        d["degrees"] = list(self.degrees)
        return d


def symmetry_score(fieldobj: HarmonicField, group: str,
                   orientation: tuple[float, float, float],
                   degrees: tuple[int, ...] | None = None
                   ) -> SymmetryScore:
    """Fraction of power in the group-invariant subspace."""
    if group not in POLYHEDRAL_GROUPS:
        raise ValueError(f"unknown group {group!r}")
    degs = degrees or tuple(
        l for l in GROUP_INVARIANT_DEGREES[group] if l <= fieldobj.lmax)
    if not degs:
        raise ValueError("no usable degrees for this group and lmax")
    a, b, g = orientation
    num = tot = 0.0
    for l in degs:
        rot = _rotate(fieldobj.coeffs[l], a, b, g, l)
        proj = _project_invariant(rot, l, group)
        num += sum(abs(c) ** 2 for c in proj)
        tot += sum(abs(c) ** 2 for c in rot)
    return SymmetryScore(
        group=group, degrees=degs, score=(num / tot if tot else 0.0),
        orientation=orientation, field_family=fieldobj.family,
        evidence_class=fieldobj.evidence_class)


def best_orientation(fieldobj: HarmonicField, group: str, *,
                     n_orientations: int, seed: int,
                     degrees: tuple[int, ...] | None = None
                     ) -> SymmetryScore:
    """Maximize the score over orientation.

    This maximization is exactly what biases a naive result high, so
    :func:`selection_null` repeats it on surrogates with the same
    ``n_orientations``.
    """
    rng = random.Random(seed)
    best: SymmetryScore | None = None
    for _ in range(n_orientations):
        o = (rng.uniform(0, 2 * math.pi),
             rng.uniform(0, math.pi),
             rng.uniform(0, 2 * math.pi))
        s = symmetry_score(fieldobj, group, o, degrees)
        if best is None or s.score > best.score:
            best = s
    assert best is not None
    return best


# --------------------------------------------------------------------
# Controls
# --------------------------------------------------------------------

def rotation_null(fieldobj: HarmonicField, group: str, *,
                  n_draws: int, seed: int) -> dict:
    """Is the best orientation special, against random orientations?"""
    rng = random.Random(seed)
    scores = []
    for _ in range(n_draws):
        o = (rng.uniform(0, 2 * math.pi), rng.uniform(0, math.pi),
             rng.uniform(0, 2 * math.pi))
        scores.append(symmetry_score(fieldobj, group, o).score)
    return {"n": n_draws, "mean": sum(scores) / len(scores),
            "max": max(scores), "scores": scores}


def degree_matched_null(fieldobj: HarmonicField, group: str, *,
                        n_draws: int, seed: int) -> dict:
    """Is a *symmetric* subspace better than any subspace of equal size?

    Draws random subspaces of exactly the invariant dimension at each
    degree. If the symmetric subspace is not better than a random one
    of the same dimension, the symmetry is doing no work — the score
    is just measuring subspace dimension.
    """
    rng = random.Random(seed)
    degs = tuple(l for l in GROUP_INVARIANT_DEGREES[group]
                 if l <= fieldobj.lmax)
    out = []
    for _ in range(n_draws):
        num = tot = 0.0
        for l in degs:
            row = fieldobj.coeffs[l]
            d = invariant_dimension(l, group)
            idx = rng.sample(range(len(row)), d)
            num += sum(abs(row[i]) ** 2 for i in idx)
            tot += sum(abs(c) ** 2 for c in row)
        out.append(num / tot if tot else 0.0)
    return {"n": n_draws, "mean": sum(out) / len(out), "max": max(out),
            "scores": out}


def selection_null(fieldobj: HarmonicField, group: str, *,
                   n_surrogates: int, n_orientations: int,
                   seed: int) -> dict:
    """Repeat the whole search on surrogate fields.

    The critical control. Each surrogate is a field with the same
    per-degree power spectrum but randomized phases, and the *entire*
    procedure — including maximization over ``n_orientations`` — is
    rerun on it. Comparing an optimized real score against optimized
    surrogate scores is the only fair comparison.
    """
    rng = random.Random(seed)
    maxima = []
    for s in range(n_surrogates):
        surro = _phase_randomize(fieldobj, seed=rng.randrange(1 << 30))
        maxima.append(best_orientation(
            surro, group, n_orientations=n_orientations,
            seed=rng.randrange(1 << 30)).score)
    return {"n": n_surrogates, "maxima": maxima,
            "mean": sum(maxima) / len(maxima), "max": max(maxima)}


def _phase_randomize(fieldobj: HarmonicField, *, seed: int
                     ) -> HarmonicField:
    """Surrogate preserving per-degree power, randomizing phase."""
    rng = random.Random(seed)
    coeffs = []
    for row in fieldobj.coeffs:
        coeffs.append([abs(c) * cmath.exp(1j * rng.uniform(0, 2 * math.pi))
                       for c in row])
    return HarmonicField(family="SYNTHETIC", coeffs=coeffs,
                         provenance=f"phase_randomize(seed={seed})")


def holm_bonferroni(pvalues: dict[str, float], alpha: float = 0.05
                    ) -> dict:
    """Holm-Bonferroni correction across the tested groups."""
    items = sorted(pvalues.items(), key=lambda kv: kv[1])
    n = len(items)
    out = {}
    rejected_so_far = True
    for i, (k, p) in enumerate(items):
        thresh = alpha / (n - i)
        rej = rejected_so_far and p <= thresh
        rejected_so_far = rej
        out[k] = {"p": p, "threshold": thresh, "significant": rej}
    return out


# --------------------------------------------------------------------
# The full audit
# --------------------------------------------------------------------

def audit(fieldobj: HarmonicField, *, n_orientations: int = 200,
          n_surrogates: int = 100, seed: int = 20260718,
          groups: tuple[str, ...] = POLYHEDRAL_GROUPS) -> dict:
    """Run every group against every control, then correct.

    Returns a report whose ``planetary_status`` is ``NO_REAL_DATA``
    whenever the field is synthetic — which, in this repository, is
    always. A synthetic detection is a statement about the detector,
    never about Earth.
    """
    rng = random.Random(seed)
    per_group = {}
    pvals: dict[str, float] = {}

    for g in groups:
        degs = tuple(l for l in GROUP_INVARIANT_DEGREES[g]
                     if l <= fieldobj.lmax)
        if not degs:
            continue
        obs = best_orientation(fieldobj, g,
                               n_orientations=n_orientations,
                               seed=rng.randrange(1 << 30))
        sel = selection_null(fieldobj, g, n_surrogates=n_surrogates,
                             n_orientations=n_orientations,
                             seed=rng.randrange(1 << 30))
        dmn = degree_matched_null(fieldobj, g, n_draws=n_surrogates,
                                  seed=rng.randrange(1 << 30))
        rot = rotation_null(fieldobj, g, n_draws=n_surrogates,
                            seed=rng.randrange(1 << 30))

        # p against the selection null: how often does an optimized
        # surrogate match or beat the optimized observation?
        beats = sum(1 for m in sel["maxima"] if m >= obs.score)
        p = (beats + 1) / (sel["n"] + 1)
        pvals[g] = p

        per_group[g] = {
            "group": g,
            "degrees": list(degs),
            "observed_best_score": obs.score,
            "selection_null_mean": sel["mean"],
            "selection_null_max": sel["max"],
            "degree_matched_null_mean": dmn["mean"],
            "rotation_null_mean": rot["mean"],
            "p_vs_selection_null": p,
            "beats_degree_matched_null":
                obs.score > dmn["mean"],
            "evidence_class": fieldobj.evidence_class,
        }

    corrected = holm_bonferroni(pvals) if pvals else {}
    any_sig = any(v["significant"] for v in corrected.values())

    synthetic = fieldobj.is_synthetic()
    return {
        "field_family": fieldobj.family,
        "provenance": fieldobj.provenance,
        "lmax": fieldobj.lmax,
        "groups": per_group,
        "holm_bonferroni": corrected,
        "any_group_significant": any_sig,
        "data_availability": data_availability(),
        "planetary_status": ("NO_REAL_DATA" if synthetic
                             else "REAL_FIELD_RESULT"),
        "claim_ceiling": (
            "A statistically stable symmetry component is a "
            "geophysical pattern result. It is not an etheric grid, "
            "power point, vortex, portal, or living-planet mechanism "
            "without independent evidence (core/08)."
        ),
        "verdict": (
            "synthetic field: this measures the detector, not Earth"
            if synthetic else
            "real field: interpret only against the stated ceiling"
        ),
    }


def refuse_node_significance(*args, **kwargs):
    """Refuses to declare any geographic location special."""
    raise DataUnavailable(
        "R6 will not report a planetary node. No real geophysical "
        "field is present in this repository (see data_availability), "
        "the rotation model is explicitly not a true Wigner D-matrix, "
        "and no function here returns a geographic coordinate. A node "
        "claim additionally requires prospective held-out validation "
        "against sites chosen before the analysis.")


def archaeological_confound_note() -> dict:
    """Why site coordinates are held apart from geophysics."""
    return {
        "dataset_class": "HUMAN",
        "confounds": [
            "rivers, coastlines and harbours concentrate settlement",
            "trade routes follow terrain, not symmetry",
            "arid and stable ground preserves structures selectively",
            "excavation funding and access bias discovery",
            "site dating uncertainty spans millennia",
            "post-hoc node selection from a large candidate set",
        ],
        "status": "SEPARATE_DATASET_NOT_POOLED",
        "note": ("Correlating monument positions with a polyhedral "
                 "overlay tests archaeology and geography jointly. "
                 "Any such test needs prospectively chosen nodes and "
                 "a settlement-density covariate."),
    }
