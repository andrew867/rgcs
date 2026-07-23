"""P04 — a numeric-cue and search-budget registry, preregistered.

Numbers that surface in a source -- ``1604``, ``1644``, ``1964``,
``1969``, ``2012``, a session timestamp -- invite a hunt: read one as a
year, another as a frequency, a third backwards, a fourth times four.
With enough transforms *something* will land near *something*, and the
landing will be reported as a discovery. That is the look-elsewhere
effect, and the only defence against it is to fix the search **before**
the results are inspected.

So this module is a **preregistration registry**. Each cue is entered as
data -- the raw token, its parsed value, how many digits were spoken,
the units (left unresolved unless actually given) -- together with the
transforms that are *allowed* and a *search budget* (the maximum number
of transforms that may be spent). All of that is frozen into a SHA-256
content hash at registration time. After that:

* a transform that was never registered is refused;
* a transform beyond the budget is refused;
* a cue marked **retrospective** (its results may already have been
  seen) can carry no weight unless the transform was preregistered;
* attaching a unit the cue never had is refused; and
* ``verify_hash`` returns ``False`` the moment any committed field is
  altered.

Registering the hypothesis before seeing the result is the whole point.
A transform declared afterward -- however clever -- is a post-hoc story,
not evidence, and this registry exists to make that distinction
mechanical rather than a matter of good intentions. Nothing here is
measured; the cues are tokens, and their referents stay unknown.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction


class NumCueError(RuntimeError):
    """Raised on any misuse of the preregistration discipline."""


class Provenance(str, Enum):
    """Was the cue registered before any result was inspected?"""

    PROSPECTIVE = "PROSPECTIVE"    # registered before any result seen
    RETROSPECTIVE = "RETROSPECTIVE"  # results possibly already seen


class CueStatus(str, Enum):
    REGISTERED = "REGISTERED"
    TRANSFORM_APPLIED = "TRANSFORM_APPLIED"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"


# --- the preregistered record ------------------------------------------

@dataclass
class NumericCue:
    """A numeric cue, its allowed transforms, and its search budget.

    The committed fields (everything except ``residuals``, ``status``,
    ``applied_transforms`` and ``hash``) are frozen into ``hash`` at
    registration. The working state accrues afterward and is not hashed.
    """

    cue_id: str
    raw_token: str                       # exactly as it appeared, e.g. "1604"
    parsed_value: Fraction               # the number, as a value
    units: str | None                    # None unless actually provided
    significant_digits: int
    spoken_digits: str                   # e.g. "1-6-0-4", distinct from value
    timestamp: str                       # registration time (ISO-8601)
    candidate_roles: tuple[str, ...]     # e.g. ("YEAR", "FREQUENCY_HZ")
    allowed_transforms: tuple[str, ...]  # the only transforms permitted
    search_budget: int                   # max transforms that may be spent
    provenance: Provenance
    residuals: dict = field(default_factory=dict)        # working state
    applied_transforms: list = field(default_factory=list)  # working state
    status: CueStatus = CueStatus.REGISTERED
    hash: str = ""

    @property
    def retrospective(self) -> bool:
        return self.provenance is Provenance.RETROSPECTIVE

    @property
    def prospective(self) -> bool:
        return self.provenance is Provenance.PROSPECTIVE


def _canonical(cue: NumericCue) -> str:
    """The committed fields, in a fixed order. Working state excluded."""
    parts = (
        cue.cue_id,
        cue.raw_token,
        str(cue.parsed_value),
        "NONE" if cue.units is None else cue.units,
        str(cue.significant_digits),
        cue.spoken_digits,
        cue.timestamp,
        "|".join(cue.candidate_roles),
        "|".join(cue.allowed_transforms),
        str(cue.search_budget),
        cue.provenance.value,
    )
    return "\x1f".join(parts)


def _compute_hash(cue: NumericCue) -> str:
    return hashlib.sha256(_canonical(cue).encode("utf-8")).hexdigest()


def register_cue(cue_id: str, raw_token: str, parsed_value: Fraction, *,
                 units: str | None = None, significant_digits: int = 0,
                 spoken_digits: str = "", timestamp: str,
                 candidate_roles: tuple[str, ...] = (),
                 allowed_transforms: tuple[str, ...] = (),
                 search_budget: int = 0,
                 provenance: Provenance = Provenance.PROSPECTIVE
                 ) -> NumericCue:
    """Freeze a cue: its allowed transforms and budget are set here, now.

    ``allowed_transforms`` and ``search_budget`` are the preregistered
    commitment; they cannot be widened after the hash is taken without
    ``verify_hash`` noticing.
    """
    if search_budget < 0:
        raise NumCueError("search_budget must be non-negative")
    if not isinstance(parsed_value, Fraction):
        raise NumCueError("parsed_value must be an exact Fraction")
    cue = NumericCue(
        cue_id=cue_id,
        raw_token=raw_token,
        parsed_value=parsed_value,
        units=units,
        significant_digits=significant_digits,
        spoken_digits=spoken_digits,
        timestamp=timestamp,
        candidate_roles=tuple(candidate_roles),
        allowed_transforms=tuple(allowed_transforms),
        search_budget=search_budget,
        provenance=provenance,
    )
    cue.hash = _compute_hash(cue)
    return cue


def verify_hash(cue: NumericCue) -> bool:
    """False if any committed field changed after registration."""
    return bool(cue.hash) and cue.hash == _compute_hash(cue)


# --- refusals ----------------------------------------------------------

def refuse_unregistered_transform(cue: NumericCue, transform_id: str) -> None:
    """A transform not named at registration is post-hoc; refuse it."""
    raise NumCueError(
        f"transform {transform_id!r} was not preregistered for cue "
        f"{cue.cue_id!r} (allowed: {list(cue.allowed_transforms)}). "
        f"Declaring a transform after the fact is a look-elsewhere "
        f"story, not evidence.")


def refuse_budget_exhausted(cue: NumericCue) -> None:
    """The search budget is a commitment; spending past it is refused."""
    raise NumCueError(
        f"search budget for cue {cue.cue_id!r} is exhausted "
        f"({len(cue.applied_transforms)}/{cue.search_budget} spent). "
        f"More transforms would mine noise; the budget was fixed at "
        f"registration.")


def refuse_unit_invention(cue: NumericCue, claimed_unit: str) -> None:
    """A cue with no declared unit gets none for free."""
    raise NumCueError(
        f"cue {cue.cue_id!r} ({cue.raw_token!r}) has no declared units. "
        f"Assigning it {claimed_unit!r} -- a year, a frequency, a "
        f"distance -- is inventing evidence. A cue is a token, not a "
        f"measurement.")


# --- applying a preregistered transform --------------------------------

def apply_transform(cue: NumericCue, transform_id: str,
                    residual=None) -> NumericCue:
    """Apply a transform, but only within the preregistered commitment.

    Refuses if the cue was tampered with, if the transform was not
    allowed, if the budget is spent, or if the cue is retrospective and
    the transform was not preregistered (which, for a retrospective cue,
    is the same allowed-list check -- stated explicitly because a
    retrospective cue can carry weight only under a preregistered
    transform).
    """
    if not verify_hash(cue):
        raise NumCueError(
            f"cue {cue.cue_id!r} fails its content hash; it was altered "
            f"after registration and cannot be trusted.")
    if transform_id not in cue.allowed_transforms:
        refuse_unregistered_transform(cue, transform_id)
    if cue.retrospective and transform_id not in cue.allowed_transforms:
        # Unreachable given the check above, but the retrospective rule
        # is load-bearing and stated on its own terms.
        refuse_unregistered_transform(cue, transform_id)
    if len(cue.applied_transforms) >= cue.search_budget:
        cue.status = CueStatus.BUDGET_EXHAUSTED
        refuse_budget_exhausted(cue)
    cue.applied_transforms.append(transform_id)
    cue.residuals[transform_id] = residual
    cue.status = (CueStatus.BUDGET_EXHAUSTED
                  if len(cue.applied_transforms) >= cue.search_budget
                  else CueStatus.TRANSFORM_APPLIED)
    return cue


# --- the cues to register, as data -------------------------------------

#: The numeric cues, entered as tokens. Units are deliberately None:
#: none was supplied with the raw numbers, and this registry does not
#: invent one. ``spoken_digits`` is kept distinct from ``parsed_value``.
CUE_TOKENS = (
    ("CUE_1604", "1604", "1-6-0-4"),
    ("CUE_1644", "1644", "1-6-4-4"),
    ("CUE_1964", "1964", "1-9-6-4"),
    ("CUE_1969", "1969", "1-9-6-9"),
    ("CUE_2012", "2012", "2-0-1-2"),
)

#: A fixed registration timestamp for the seeded fixtures.
REGISTRATION_TIMESTAMP = "2026-07-21T00:00:00Z"


def register_default_cues() -> dict:
    """Register the seeded cues prospectively, with a modest budget."""
    cues = {}
    for cue_id, token, spoken in CUE_TOKENS:
        cues[cue_id] = register_cue(
            cue_id, token, Fraction(int(token)),
            units=None, significant_digits=len(token),
            spoken_digits=spoken, timestamp=REGISTRATION_TIMESTAMP,
            candidate_roles=("YEAR", "FREQUENCY_HZ", "INDEX"),
            allowed_transforms=("IDENTITY", "AS_YEAR"),
            search_budget=2, provenance=Provenance.PROSPECTIVE)
    return cues


def numcue_report() -> dict:
    cues = register_default_cues()
    return {
        "cues_registered": list(cues),
        "all_hashes_verify": all(verify_hash(c) for c in cues.values()),
        "units_all_unresolved": all(
            c.units is None for c in cues.values()),
        "spoken_distinct_from_value": all(
            c.spoken_digits.replace("-", "") == str(int(c.parsed_value))
            for c in cues.values()),
        "budget_per_cue": {k: v.search_budget for k, v in cues.items()},
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "what_this_does_not_say": (
            "It does not say any cue means a year, a frequency, a "
            "distance, or anything at all; it does not resolve their "
            "units, and it does not claim a transform found a signal. It "
            "says only that transforms must be declared, with a budget, "
            "before their results are inspected -- so that a match "
            "reported later cannot be a post-hoc selection dressed as a "
            "discovery."),
        "verdict": "PREREGISTRATION_ENFORCED",
    }
