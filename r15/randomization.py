"""P08 — the randomization engine: a pre-committed, reproducible, balanced
assignment of experiment order and conditions that cannot be reordered
after the seal.

Order effects and operator leakage are ordinary explanations that will
swallow any apparent result unless the run order is fixed by something
other than the operator's judgement. This module fixes it by a committed
seed and a balanced design, sealed *before* any run, so nobody can pick
the order that flatters the answer after seeing the data.

**The assignment is deterministic under a seed.** :func:`randomize`,
:func:`random_blocks`, :func:`latin_square`, and the per-factor orders
(:func:`specimen_order`, :func:`frequency_order`, :func:`orientation_order`,
:func:`sensor_permutation`) all draw from ``numpy.random.default_rng(seed)``
and read no clock. The same seed reproduces the same schedule exactly; a
different seed generally produces a different one. Reproducibility is what
lets an independent party regenerate and check the schedule.

**The design is balanced.** Random blocks give each condition once per
block; a randomized Latin square gives each condition exactly once in
every row and every column, so a condition is never confounded with a row
(e.g. a session) or a column (e.g. a position). :func:`is_balanced_blocks`
and :func:`is_latin_square` check the property rather than trusting it.

**The schedule is sealed before runs.** :class:`RandomizationManifest`
carries the seed, the design, the produced schedule, and a
:func:`design_hash` over the design spec. :meth:`RandomizationManifest.seal`
takes a SHA-256 commitment over the seed, the design hash, and the
schedule (reusing the R13 canonical serializer, so the commitment is a
stable fingerprint of the content). A committed seed plus the design hash
makes the assignment tamper-evident: revealing a different order, or the
same order with one swap, fails the commitment while the true schedule
matches.

**No peeking, no post-hoc reordering.**
:func:`refuse_read_before_seal` refuses analysis code that reads the
assignment before the manifest is sealed -- an assignment read early can
still be nudged and then sealed as though it had predated the data.
:func:`refuse_post_commit_reorder` refuses any attempt to reorder the
schedule after the commit, because reordering after the seal is exactly
the cherry-picking the commit exists to prevent.

**Balance failures, restarts, and every deviation are recorded.** A
restart derives a fresh seed deterministically from the original seed and
a restart index and logs a :class:`Deviation`; unblinding is recorded and
:func:`refuse_confirmatory_after_unblind` collapses a run's status to
exploratory once the operator has seen the assignment, because a
confirmatory claim cannot survive the blind being broken.

Everything here is synthetic: conditions are opaque labels, seeds are
integers, and no order, block, or square is a measurement of anything.
The standing verdict is ``RANDOMIZATION_PRECOMMITTED_REPRODUCIBLE_BALANCED``.
Nothing is measured; no physical validation is claimed.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, replace
from enum import Enum

import numpy as np

from r13.serialize import content_hash
from r15 import claims as C

# =======================================================================
# Verdict, claim class, and the standing physical-validation disclaimer
# =======================================================================

VERDICT = "RANDOMIZATION_PRECOMMITTED_REPRODUCIBLE_BALANCED"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: The strongest class this module reaches: it implements a scheduler, it
#: measures nothing.
CLAIM_CLASS = C.ClaimClass.SOFTWARE_IMPLEMENTED

#: Salt bound into every manifest commitment.
DEFAULT_COMMIT_SALT = "R15_P08_RANDOMIZATION_COMMIT"


class RandomizationError(RuntimeError):
    """Raised on a schedule read before the seal, a reorder attempted
    after the commit, a labels/schedule set that does not match the sealed
    commitment, a malformed design, or a confirmatory status asserted
    after unblinding."""


class DesignType(Enum):
    """The balanced designs this engine can pre-commit."""

    COMPLETE_RANDOM = "COMPLETE_RANDOM"
    RANDOM_BLOCKS = "RANDOM_BLOCKS"
    LATIN_SQUARE = "LATIN_SQUARE"
    COUNTERBALANCED = "COUNTERBALANCED"


# =======================================================================
# Seed derivation: one master seed, independent per-factor sub-seeds
# =======================================================================

def derive_seed(seed: int, label: str) -> int:
    """A deterministic sub-seed for ``label`` under a master ``seed``.

    Each experimental factor (specimen, frequency, orientation, sensor)
    gets its own stream so the orders are independent, but every stream is
    a pure function of the master seed and the label -- no clock, no
    entropy source -- so the whole plan reproduces from the one committed
    seed."""
    digest = hashlib.sha256(f"{int(seed)}\x1f{label}".encode()).hexdigest()
    return int(digest[:16], 16)


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(int(seed))


# =======================================================================
# Core reproducible randomization
# =======================================================================

def randomize(conditions, seed: int) -> tuple:
    """Return a reproducible random permutation of ``conditions``.

    Deterministic under ``seed``: the same conditions and seed always give
    the same order, so an independent party can regenerate and check it. A
    different seed generally gives a different order. The engine reads no
    clock, so the assignment cannot drift between runs."""
    items = list(conditions)
    if len(items) < 1:
        raise RandomizationError("cannot randomize an empty condition set")
    perm = _rng(seed).permutation(len(items))
    return tuple(items[i] for i in perm)


def random_blocks(conditions, n_blocks: int, seed: int) -> tuple:
    """A randomized complete block design: ``n_blocks`` independent
    permutations of the full condition set.

    Each block contains every condition exactly once, so every condition
    is replicated ``n_blocks`` times and no condition is systematically
    early or late across blocks. Balance is a property of the design, not
    a promise -- see :func:`is_balanced_blocks`."""
    base = list(conditions)
    if len(base) < 1:
        raise RandomizationError("a block design needs at least one condition")
    if n_blocks < 1:
        raise RandomizationError("n_blocks must be >= 1")
    rng = _rng(seed)
    blocks = []
    for _ in range(int(n_blocks)):
        perm = rng.permutation(len(base))
        blocks.append(tuple(base[i] for i in perm))
    return tuple(blocks)


def is_balanced_blocks(blocks, conditions) -> bool:
    """True iff every block is a permutation of ``conditions`` (each
    condition once per block)."""
    want = sorted(map(str, conditions))
    return all(sorted(map(str, block)) == want for block in blocks)


def latin_square(symbols, seed: int) -> tuple:
    """A randomized Latin square over ``symbols``.

    Starts from a cyclic square (row ``i`` = symbols shifted by ``i``) and
    randomly permutes rows, columns, and symbol labels under ``seed`` --
    every such permutation is still a Latin square, so each symbol appears
    exactly once in every row and every column. That is what
    counterbalances a condition against both a row factor (say, a session)
    and a column factor (say, a position), removing order confounds."""
    syms = list(symbols)
    n = len(syms)
    if n < 1:
        raise RandomizationError("a Latin square needs at least one symbol")
    if len(set(map(str, syms))) != n:
        raise RandomizationError("Latin-square symbols must be distinct")
    base = np.array([[(i + j) % n for j in range(n)] for i in range(n)])
    rng = _rng(seed)
    row_perm = rng.permutation(n)
    col_perm = rng.permutation(n)
    sym_perm = rng.permutation(n)
    permuted = base[np.ix_(row_perm, col_perm)]
    square = tuple(
        tuple(syms[int(sym_perm[permuted[i, j]])] for j in range(n))
        for i in range(n)
    )
    return square


def is_latin_square(square, symbols) -> bool:
    """True iff ``square`` is an ``n x n`` Latin square over ``symbols``:
    each symbol appears exactly once in every row and every column."""
    rows = [list(r) for r in square]
    n = len(symbols)
    want = set(map(str, symbols))
    if len(rows) != n or any(len(r) != n for r in rows):
        return False
    for r in rows:
        if set(map(str, r)) != want:
            return False
    for j in range(n):
        col = [rows[i][j] for i in range(n)]
        if set(map(str, col)) != want:
            return False
    return True


# =======================================================================
# Per-factor orders: independent, reproducible streams off one seed
# =======================================================================

def specimen_order(specimens, seed: int) -> tuple:
    """Reproducible specimen presentation order (its own seed stream)."""
    return randomize(specimens, derive_seed(seed, "specimen"))


def frequency_order(frequencies, seed: int) -> tuple:
    """Reproducible frequency-sweep order (its own seed stream)."""
    return randomize(frequencies, derive_seed(seed, "frequency"))


def orientation_order(orientations, seed: int) -> tuple:
    """Reproducible specimen-orientation order (its own seed stream)."""
    return randomize(orientations, derive_seed(seed, "orientation"))


def sensor_permutation(sensors, seed: int) -> tuple:
    """Reproducible sensor/channel permutation (its own seed stream)."""
    return randomize(sensors, derive_seed(seed, "sensor"))


#: The factor labels a full plan orders, in a fixed sequence.
PLAN_FACTORS = ("specimen", "frequency", "orientation", "sensor")

_FACTOR_ORDER = {
    "specimen": specimen_order,
    "frequency": frequency_order,
    "orientation": orientation_order,
    "sensor": sensor_permutation,
}


def randomization_plan(factors: dict, seed: int) -> dict:
    """Order every supplied factor under independent sub-seeds of ``seed``.

    ``factors`` maps a name in :data:`PLAN_FACTORS` to its levels; the
    result maps each name to its reproducible order. Because every factor
    uses a derived sub-seed, the streams are independent yet the whole
    plan regenerates from the single committed master seed."""
    plan = {}
    for name in PLAN_FACTORS:
        if name in factors and factors[name] is not None:
            plan[name] = _FACTOR_ORDER[name](factors[name], seed)
    if not plan:
        raise RandomizationError(
            "randomization_plan needs at least one known factor "
            f"(one of {', '.join(PLAN_FACTORS)})")
    return plan


# =======================================================================
# Design hashing and the schedule fingerprint
# =======================================================================

def _canonical_schedule(schedule) -> list:
    """A canonical, JSON-friendly form of a schedule (nested tuples ->
    nested lists of strings) so the commitment is over stable content."""
    def norm(x):
        if isinstance(x, (list, tuple)):
            return [norm(v) for v in x]
        return str(x)
    return norm(schedule)


def design_hash(design_type: DesignType, factors: dict, seed: int) -> str:
    """A stable fingerprint of the design spec (type, factors, seed).

    Reuses the R13 canonical serializer's content hash, so the same design
    always hashes identically and any change to the type, the factor
    levels, or the seed changes the hash. This is half of the
    tamper-evidence: the committed seed pins the draw, the design hash pins
    what was drawn over."""
    spec = {
        "design_type": design_type.value,
        "seed": int(seed),
        "factors": {k: _canonical_schedule(v)
                    for k, v in sorted(factors.items())},
    }
    return content_hash(spec)


def commit_schedule(schedule, seed: int, dhash: str,
                    salt: str = DEFAULT_COMMIT_SALT) -> str:
    """SHA-256 commitment binding the seed, the design hash, and the
    schedule. A different order -- or the same order with one swap --
    yields a different commitment; the true schedule reproduces it."""
    payload = {
        "salt": salt,
        "seed": int(seed),
        "design_hash": dhash,
        "schedule": _canonical_schedule(schedule),
    }
    return content_hash(payload)


# =======================================================================
# Deviations
# =======================================================================

@dataclass(frozen=True)
class Deviation:
    """One recorded departure from the pre-committed plan.

    ``epoch`` is PASSED IN, never read from a clock, so a manifest and its
    deviations remain deterministic and reproducible."""

    kind: str
    detail: str
    epoch: int


# =======================================================================
# The sealed manifest
# =======================================================================

@dataclass
class RandomizationManifest:
    """A pre-committed randomization: the design, the seed, the produced
    schedule, its design hash, and (once sealed) a commitment.

    A manifest starts UNSEALED. Analysis code may not read the schedule
    until :meth:`seal` has taken the commitment
    (:func:`refuse_read_before_seal`), and once sealed the schedule may not
    be reordered (:func:`refuse_post_commit_reorder`). Every deviation from
    the plan is appended to :attr:`deviations`."""

    design_type: DesignType
    seed: int
    factors: dict
    schedule: tuple
    dhash: str
    commit_salt: str = DEFAULT_COMMIT_SALT
    commitment: str | None = None
    unblinded: bool = False
    deviations: tuple = field(default_factory=tuple)

    @property
    def committed(self) -> bool:
        return self.commitment is not None

    def seal(self) -> str:
        """Seal the manifest by committing to seed + design hash + schedule.

        Call this BEFORE any run. Sealing twice is refused: a second seal
        would let the schedule be swapped and resealed."""
        if self.committed:
            raise RandomizationError(
                "refused: this manifest is already sealed; resealing would "
                "allow the schedule to be swapped and committed again")
        self.commitment = commit_schedule(
            self.schedule, self.seed, self.dhash, self.commit_salt)
        return self.commitment

    def reveal_schedule(self) -> tuple:
        """Return the schedule, but only after the seal.

        The no-peek gate: reading the assignment before it is committed is
        refused, because an assignment seen early can be adjusted and then
        sealed as though it had predated the data."""
        refuse_read_before_seal(self)
        return self.schedule

    def verify(self, schedule=None) -> bool:
        """True iff ``schedule`` (default: the stored one) reproduces the
        commitment. A sealed manifest verifies against its own schedule and
        fails against any altered one."""
        if not self.committed:
            raise RandomizationError(
                "cannot verify an unsealed manifest; seal it first")
        candidate = self.schedule if schedule is None else schedule
        return commit_schedule(candidate, self.seed, self.dhash,
                               self.commit_salt) == self.commitment

    def record_deviation(self, kind: str, detail: str, epoch: int) -> None:
        """Append a :class:`Deviation` to the log. Records survive; a
        deviation is never silently dropped."""
        self.deviations = self.deviations + (Deviation(kind, detail, int(epoch)),)


def build_manifest(design_type: DesignType, factors: dict, seed: int,
                   commit_salt: str = DEFAULT_COMMIT_SALT
                   ) -> RandomizationManifest:
    """Build an UNSEALED manifest for a design.

    Constructs the schedule for ``design_type`` from ``factors`` and
    ``seed``, computes the design hash, and returns a manifest whose
    commitment is still ``None`` -- the caller seals it before any run."""
    schedule = build_schedule(design_type, factors, seed)
    dhash = design_hash(design_type, factors, seed)
    return RandomizationManifest(
        design_type=design_type, seed=int(seed), factors=dict(factors),
        schedule=schedule, dhash=dhash, commit_salt=commit_salt)


def build_schedule(design_type: DesignType, factors: dict, seed: int) -> tuple:
    """Produce the schedule for a design type from its factors and seed."""
    if design_type is DesignType.COMPLETE_RANDOM:
        conditions = factors.get("conditions")
        if conditions is None:
            raise RandomizationError(
                "COMPLETE_RANDOM needs factors['conditions']")
        return randomize(conditions, seed)
    if design_type is DesignType.RANDOM_BLOCKS:
        conditions = factors.get("conditions")
        n_blocks = factors.get("n_blocks")
        if conditions is None or n_blocks is None:
            raise RandomizationError(
                "RANDOM_BLOCKS needs factors['conditions'] and ['n_blocks']")
        return random_blocks(conditions, int(n_blocks), seed)
    if design_type is DesignType.LATIN_SQUARE:
        symbols = factors.get("symbols")
        if symbols is None:
            raise RandomizationError("LATIN_SQUARE needs factors['symbols']")
        return latin_square(symbols, seed)
    if design_type is DesignType.COUNTERBALANCED:
        # A full plan across specimen/frequency/orientation/sensor, ordered
        # into a stable tuple of (factor, order) pairs.
        plan = randomization_plan(factors, seed)
        return tuple((name, plan[name]) for name in PLAN_FACTORS
                     if name in plan)
    raise RandomizationError(f"unknown design type: {design_type!r}")


# =======================================================================
# The refusals
# =======================================================================

def refuse_read_before_seal(manifest, *_args, **_kwargs) -> None:
    """Refuse an assignment read before the manifest is sealed.

    Premature access is the leak this guards: analysis or operator code
    that reads the order before the commitment exists can still influence
    which order gets sealed, so the seal would no longer predate the data.
    The commitment must be taken first."""
    committed = getattr(manifest, "committed", None)
    if committed is None:
        committed = bool(getattr(manifest, "commitment", None))
    if not committed:
        raise RandomizationError(
            "refused: the randomization schedule was read before it was "
            "sealed. The manifest must be committed with seal() BEFORE any "
            "analysis or operator code reads the assignment; an order read "
            "before the commitment can still be adjusted and then sealed as "
            "though it had predated the run. Seal first, then read.")


def refuse_post_commit_reorder(manifest, proposed_schedule=None,
                               *_args, **_kwargs) -> None:
    """Refuse any reorder of a schedule after it has been committed.

    Reordering after the seal is precisely the cherry-picking the
    pre-commitment exists to prevent: the order was fixed and fingerprinted
    before the data, and a later reshuffle -- even one that claims to be a
    correction -- breaks that guarantee. A genuine change requires a new,
    separately committed manifest, recorded as a deviation."""
    if getattr(manifest, "committed", False):
        detail = ""
        if proposed_schedule is not None:
            same = _canonical_schedule(proposed_schedule) == \
                _canonical_schedule(getattr(manifest, "schedule", ()))
            detail = (" (the proposed order is identical to the sealed one)"
                      if same else
                      " (the proposed order differs from the sealed one)")
        raise RandomizationError(
            "refused: the schedule was reordered after the manifest was "
            "committed" + detail + ". The pre-committed order is "
            "tamper-evident under its commitment; a post-commit reorder "
            "would let the run order be chosen after seeing the data. Issue "
            "a new manifest and record the change as a deviation instead.")


def refuse_confirmatory_after_unblind(unblinded: bool = True,
                                      *_args, **_kwargs) -> None:
    """Refuse a confirmatory claim once the assignment has been unblinded.

    A confirmatory result rests on the operator not having seen the
    condition assignment while acquiring or reducing the data. Once the
    blind is broken, order effects and operator leakage can no longer be
    ruled out, so the run drops to exploratory. Analyses run before
    unblinding keep their status; this one is refused."""
    if unblinded:
        raise RandomizationError(
            "refused: confirmatory status cannot be asserted after "
            "unblinding. Once the operator has seen the condition "
            "assignment, order and leakage effects are no longer excluded "
            "and the analysis is exploratory only. A confirmatory claim "
            "requires the blind to have held through acquisition and "
            "reduction.")


def analysis_status(manifest) -> str:
    """The status a manifest supports: not-yet-sealed, exploratory (if
    unblinded), or confirmatory-eligible (sealed and still blind)."""
    if getattr(manifest, "unblinded", False):
        return "EXPLORATORY_ONLY"
    if not getattr(manifest, "committed", False):
        return "NOT_YET_SEALED"
    return "CONFIRMATORY_ELIGIBLE"


# =======================================================================
# Restart / balance policy
# =======================================================================

def restart_seed(seed: int, restart_index: int) -> int:
    """A fresh, deterministic seed for a restart.

    Derived from the original seed and the restart index, so a restart is
    reproducible and independent of the aborted attempt, and no two
    restarts collide. Nothing is drawn from a clock."""
    if restart_index < 1:
        raise RandomizationError("restart_index must be >= 1")
    return derive_seed(seed, f"restart#{int(restart_index)}")


def restart(manifest: RandomizationManifest, reason: str, epoch: int,
            restart_index: int = 1) -> RandomizationManifest:
    """Produce a NEW unsealed manifest for a restarted run and log the
    deviation on it.

    A restart never edits the committed manifest -- that would defeat the
    seal. It builds a fresh manifest under a derived restart seed, carrying
    the old deviations plus a RESTART entry, ready to be sealed anew."""
    new_seed = restart_seed(manifest.seed, restart_index)
    fresh = build_manifest(manifest.design_type, manifest.factors, new_seed,
                           manifest.commit_salt)
    dev = Deviation("RESTART",
                    f"restart #{int(restart_index)} of seed {manifest.seed}: "
                    f"{reason}", int(epoch))
    return replace(fresh, deviations=manifest.deviations + (dev,))


# =======================================================================
# The report
# =======================================================================

def randomization_report() -> dict:
    """The standing result: a reproducible, balanced, sealed randomization
    with its no-peek and no-reorder refusals demonstrated."""
    conditions = tuple(f"C{i}" for i in range(6))

    # Reproducibility: same seed, same order; different seed, different.
    order_a = randomize(conditions, seed=20260724)
    order_a2 = randomize(conditions, seed=20260724)
    order_b = randomize(conditions, seed=20260725)

    # Balance: blocks and a Latin square.
    blocks = random_blocks(conditions, n_blocks=4, seed=7)
    square = latin_square(conditions, seed=11)

    # A sealed counterbalanced plan across four factors.
    factors = {
        "specimen": ("S1", "S2", "S3"),
        "frequency": (1000, 2000, 3000, 4000),
        "orientation": ("X", "Y", "Z"),
        "sensor": ("ch0", "ch1", "ch2", "ch3"),
    }
    manifest = build_manifest(DesignType.COUNTERBALANCED, factors, seed=42)
    commitment = manifest.seal()

    # Tamper-evidence: the true schedule matches; a swapped one does not.
    swapped = (manifest.schedule[1], manifest.schedule[0]) + \
        tuple(manifest.schedule[2:])
    true_matches = manifest.verify()
    swapped_matches = manifest.verify(swapped)

    # A refused post-commit reorder.
    reorder_refused = False
    try:
        refuse_post_commit_reorder(manifest, swapped)
    except RandomizationError:
        reorder_refused = True

    # A refused pre-seal read.
    unsealed = build_manifest(DesignType.COMPLETE_RANDOM,
                              {"conditions": conditions}, seed=1)
    read_before_seal_refused = False
    try:
        unsealed.reveal_schedule()
    except RandomizationError:
        read_before_seal_refused = True

    # Unblinding collapses confirmatory status.
    confirmatory_refused = False
    try:
        refuse_confirmatory_after_unblind(True)
    except RandomizationError:
        confirmatory_refused = True

    return {
        "what_this_is": (
            "a pre-committed randomization engine for experiment order and "
            "condition assignment: reproducible under a committed seed, "
            "balanced (blocks and Latin squares), sealed before runs, and "
            "refusing both premature reads and post-commit reordering"),
        "designs": [d.value for d in DesignType],
        "same_seed_same_order": order_a == order_a2,
        "different_seed_different_order": order_a != order_b,
        "blocks_balanced": is_balanced_blocks(blocks, conditions),
        "latin_square_valid": is_latin_square(square, conditions),
        "design_hash": manifest.dhash,
        "commitment": commitment,
        "true_schedule_matches_commitment": true_matches,
        "swapped_schedule_matches_commitment": swapped_matches,
        "post_commit_reorder_refused": reorder_refused,
        "read_before_seal_refused": read_before_seal_refused,
        "confirmatory_after_unblind_refused": confirmatory_refused,
        "analysis_status_sealed_blind": analysis_status(manifest),
        "refusals": [
            "refuse_read_before_seal",
            "refuse_post_commit_reorder",
            "refuse_confirmatory_after_unblind",
        ],
        "claim_class": CLAIM_CLASS.value,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not measure, acquire, or run anything. It assigns "
            "order and conditions from a committed seed so the schedule is "
            "reproducible and, once sealed, tamper-evident: the seed pins "
            "the draw and the design hash pins what was drawn over, so a "
            "reordered or swapped schedule fails the commitment while the "
            "true one matches. Balance (each condition once per block; each "
            "symbol once per row and column of a Latin square) defends "
            "against order effects; the seal and the no-peek / no-reorder "
            "refusals defend against operator leakage and cherry-picking. "
            "Reading the assignment before the seal or reordering it after "
            "is refused, and unblinding drops the run to exploratory. Every "
            "condition and seed is synthetic; nothing here is a physical "
            "measurement and no physical validation is claimed."),
    }


__all__ = [
    "RandomizationError", "DesignType", "VERDICT", "PHYSICAL_VALIDATION",
    "CLAIM_CLASS", "DEFAULT_COMMIT_SALT",
    "derive_seed", "randomize", "random_blocks", "is_balanced_blocks",
    "latin_square", "is_latin_square",
    "specimen_order", "frequency_order", "orientation_order",
    "sensor_permutation", "PLAN_FACTORS", "randomization_plan",
    "design_hash", "commit_schedule", "_canonical_schedule",
    "Deviation", "RandomizationManifest", "build_manifest", "build_schedule",
    "refuse_read_before_seal", "refuse_post_commit_reorder",
    "refuse_confirmatory_after_unblind", "analysis_status",
    "restart_seed", "restart", "randomization_report",
]
