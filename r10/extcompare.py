"""P16 — contemporaneous comparison against a public external corpus.

A recurring temptation is to take a private session's content, search a
public corpus (news, social posts, video transcripts), find something
that "matches", and treat the match as confirmation. This module exists
to do that comparison **honestly with respect to time**, because the
temptation almost always fails on the calendar.

**Comparing a session to material published AFTER the session proves
nothing prospective.** If the corpus item post-dates the session, the
session could not have drawn on it and the item could not have drawn on
the session -- so a later publication that happens to overlap is, at
best, a retrospective coincidence check. It cannot support a claim that
the session *anticipated* anything. Only material that was published
before the session AND was plausibly accessible speaks to prior
exposure; only that direction of time carries evidential weight, and it
weighs *against* originality, not for prescience.

So every corpus item is stamped with its own publication and access
times and classified: :data:`TemporalClass.PRIOR_EXPOSURE_POSSIBLE`,
:data:`TemporalClass.CONTEMPORANEOUS`, or
:data:`TemporalClass.POST_SESSION`.
:func:`refuse_prospective_from_post_session` makes the forbidden move
raise.

The overlap itself is measured skeptically. A Jaccard overlap is only
interesting relative to a **null** built from many UNRELATED corpora
(:func:`semantic_null`), with a multiplicity correction for the number
of comparisons made, and an :func:`independence_score` that discounts
overlap explained by shared common vocabulary rather than genuine
correspondence. A planted near-duplicate shows the comparator has power;
unrelated corpora show it does not fire at random.

Nothing here is a physical measurement, and no private content appears
in this module -- only the schema and the arithmetic of an honest
comparison. PHYSICAL_VALIDATION_NOT_CLAIMED.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum

import numpy as np

#: Significance threshold used for the "flagged" convenience booleans.
ALPHA = 0.05


class CompareError(RuntimeError):
    """Raised when a comparison is made dishonestly with respect to time."""


class TemporalClass(str, Enum):
    """Where a corpus item sits in time relative to the session."""

    #: Published before the session and plausibly accessible -- speaks to
    #: prior exposure, i.e. weighs against originality.
    PRIOR_EXPOSURE_POSSIBLE = "PRIOR_EXPOSURE_POSSIBLE"
    #: Published around the session time; neither side clearly precedes.
    CONTEMPORANEOUS = "CONTEMPORANEOUS"
    #: Published after the session -- cannot support a prospective claim.
    POST_SESSION = "POST_SESSION"


# --- corpus items and time discipline ----------------------------------

@dataclass(frozen=True)
class CorpusItem:
    """One public item, with its own publication and access times.

    ``text_features`` is a bag/set of tokens (or any hashable feature
    labels). It is never raw private content; it is the derived features
    a comparison operates on.
    """

    id: str
    publication_time: object              # datetime or comparable number
    access_time: object | None            # first time it was accessed
    text_features: frozenset

    def __post_init__(self) -> None:
        object.__setattr__(self, "text_features",
                           frozenset(self.text_features))


def _delta_seconds(a, b) -> float:
    """a - b as a float, for datetimes (timedelta) or plain numbers."""
    d = a - b
    total = getattr(d, "total_seconds", None)
    return total() if callable(total) else float(d)


def _window_seconds(window) -> float:
    total = getattr(window, "total_seconds", None)
    return total() if callable(total) else float(window)


def classify_temporal(item: CorpusItem, session_time,
                      first_access_time=None, window=86400.0) -> TemporalClass:
    """Classify an item's publication time relative to the session.

    ``window`` (seconds, or a ``timedelta``) is the half-width of the
    band treated as "around" the session. An item beyond it in the
    future is :data:`POST_SESSION`; beyond it in the past is
    :data:`PRIOR_EXPOSURE_POSSIBLE`; inside it is
    :data:`CONTEMPORANEOUS`.
    """
    delta = _delta_seconds(item.publication_time, session_time)
    win = _window_seconds(window)
    if delta > win:
        return TemporalClass.POST_SESSION
    if delta < -win:
        return TemporalClass.PRIOR_EXPOSURE_POSSIBLE
    return TemporalClass.CONTEMPORANEOUS


def plausible_exposure(item: CorpusItem, session_time,
                       first_access_time=None) -> bool:
    """Was the item both earlier than AND reachable before the session?

    Prior *exposure* needs more than an earlier publication date: the
    material also had to be accessible. This refines
    :data:`TemporalClass.PRIOR_EXPOSURE_POSSIBLE` from a temporal
    possibility into a plausible one.
    """
    if _delta_seconds(item.publication_time, session_time) >= 0:
        return False
    if item.access_time is not None and item.access_time <= session_time:
        return True
    if first_access_time is not None and first_access_time <= session_time:
        return True
    return False


def refuse_prospective_from_post_session(item: CorpusItem,
                                         session_time,
                                         window=86400.0) -> None:
    """Refuse to treat a POST_SESSION item as prospective confirmation."""
    label = classify_temporal(item, session_time, window=window)
    if label is TemporalClass.POST_SESSION:
        raise CompareError(
            f"item {item.id!r} was published after the session and cannot "
            f"be prospective confirmation of it. The session could not "
            f"have drawn on it and it could not have drawn on the "
            f"session; a later overlap is a retrospective coincidence "
            f"check at most, never evidence that the session anticipated "
            f"anything.")


# --- semantic overlap --------------------------------------------------

def jaccard(a, b) -> float:
    """Jaccard overlap of two token sets. 0.0 when both are empty."""
    a, b = frozenset(a), frozenset(b)
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def exact_overlap(session_features, item_features) -> bool:
    """True only when the two feature sets are identical (verbatim)."""
    return frozenset(session_features) == frozenset(item_features)


def independence_score(session_features, item_features,
                       common_vocab) -> float:
    """Fraction of the overlap that is NOT shared common vocabulary.

    An overlap made entirely of common words ("the", "energy",
    "signal") is not correspondence -- any two texts share it. This
    returns 1.0 when the overlap is all distinctive tokens and 0.0 when
    it is all common ones, so it can penalise a Jaccard score that only
    looks impressive because of background vocabulary. With no overlap
    at all there is nothing to confound, and it returns 1.0.
    """
    shared = frozenset(session_features) & frozenset(item_features)
    if not shared:
        return 1.0
    informative = shared - frozenset(common_vocab)
    return len(informative) / len(shared)


# --- the null and its multiplicity correction --------------------------

def multiplicity_correct(p_raw: float, n_comparisons: int) -> float:
    """Bonferroni-correct a raw p-value for the number of comparisons."""
    if n_comparisons < 1:
        raise CompareError("n_comparisons must be at least 1")
    return min(1.0, p_raw * n_comparisons)


def semantic_null(session_features, null_corpora, observed_overlap: float,
                  n_comparisons: int | None = None) -> dict:
    """Build a null overlap distribution from UNRELATED corpora.

    The overlaps of the session against many unrelated corpora define
    what "overlap by chance" looks like. The observed overlap earns a
    p-value = P(null overlap >= observed), add-one smoothed so it is
    never zero, and that p-value is Bonferroni-corrected for the number
    of candidate comparisons actually made (``n_comparisons``, defaulting
    to 1 -- the single observed comparison). The null-set size is the
    reference distribution, not the multiplicity factor: testing one
    candidate against a large null is still one hypothesis.
    """
    null_overlaps = np.array(
        [jaccard(session_features, c.text_features) for c in null_corpora],
        dtype=float)
    n = int(null_overlaps.size)
    if n == 0:
        raise CompareError("a null needs at least one unrelated corpus")
    ge = int(np.sum(null_overlaps >= observed_overlap))
    p_raw = (1 + ge) / (1 + n)
    m = n_comparisons if n_comparisons is not None else 1
    p_corrected = multiplicity_correct(p_raw, m)
    return {
        "observed_overlap": float(observed_overlap),
        "null_n": n,
        "null_mean": float(null_overlaps.mean()),
        "null_max": float(null_overlaps.max()),
        "p_raw": float(p_raw),
        "n_comparisons": int(m),
        "p_corrected": float(p_corrected),
        "flagged": bool(p_corrected < ALPHA),
    }


def planted_power_check(session_features, null_corpora,
                        noise_fraction: float = 0.1) -> dict:
    """POWER: plant a near-duplicate of the session and confirm it fires.

    A near-copy of the session features is added as a corpus item and
    scored the same way as everything else. If the comparator has power,
    the planted item's overlap p-value should be flagged where the
    unrelated corpora are not.
    """
    session = list(frozenset(session_features))
    k = max(0, int(len(session) * noise_fraction))
    near_dup = frozenset(session[k:]) if k < len(session) else \
        frozenset(session)
    observed = jaccard(session_features, near_dup)
    result = semantic_null(session_features, null_corpora, observed)
    result["planted_overlap"] = float(observed)
    return result


# --- the comparison record ---------------------------------------------

def session_hash(session_features) -> str:
    """A content hash of the derived features (order-independent)."""
    tokens = " ".join(sorted(str(t) for t in session_features))
    return hashlib.sha256(tokens.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ExternalComparison:
    """The full, honest record of one external-corpus comparison."""

    comparison_id: str
    frozen_query_time: object
    session_hash: str
    source_corpus: str
    publication_times: tuple
    access_times: tuple
    prior_exposure: bool
    exact_overlap: bool
    semantic_features: tuple
    null_corpora: tuple
    multiplicity: int
    independence_score: float
    result: str

    def as_record(self) -> dict:
        return {
            "comparison_id": self.comparison_id,
            "session_hash": self.session_hash,
            "source_corpus": self.source_corpus,
            "prior_exposure": self.prior_exposure,
            "exact_overlap": self.exact_overlap,
            "multiplicity": self.multiplicity,
            "independence_score": self.independence_score,
            "result": self.result,
        }


def build_comparison(comparison_id: str, frozen_query_time,
                     session_features, target: CorpusItem,
                     null_corpora, source_corpus: str,
                     common_vocab=frozenset(), session_time=None,
                     first_access_time=None) -> ExternalComparison:
    """Assemble an :class:`ExternalComparison` from its parts, honestly.

    If the target post-dates the session this refuses to dress the match
    up as prospective; the recorded ``result`` says so explicitly.
    """
    if session_time is not None:
        # The refusal fires before any "result" can be manufactured.
        refuse_prospective_from_post_session(target, session_time)
        label = classify_temporal(target, session_time)
        prior = plausible_exposure(target, session_time, first_access_time)
    else:
        label = TemporalClass.CONTEMPORANEOUS
        prior = False

    observed = jaccard(session_features, target.text_features)
    null = semantic_null(session_features, null_corpora, observed)
    indep = independence_score(session_features, target.text_features,
                               common_vocab)
    result = (
        f"{label.value}; overlap={observed:.3f}; "
        f"p_corrected={null['p_corrected']:.3f}; "
        f"independence={indep:.3f}; "
        f"prospective_claim=REFUSED")
    return ExternalComparison(
        comparison_id=comparison_id,
        frozen_query_time=frozen_query_time,
        session_hash=session_hash(session_features),
        source_corpus=source_corpus,
        publication_times=(target.publication_time,),
        access_times=(target.access_time,),
        prior_exposure=prior,
        exact_overlap=exact_overlap(session_features, target.text_features),
        semantic_features=tuple(sorted(str(t) for t in session_features)),
        null_corpora=tuple(c.id for c in null_corpora),
        multiplicity=null["n_comparisons"],
        independence_score=indep,
        result=result,
    )


def extcompare_report() -> dict:
    return {
        "phase": "P16",
        "temporal_classes": [c.value for c in TemporalClass],
        "how_overlap_is_judged": (
            "Jaccard overlap against a null built from unrelated corpora, "
            "Bonferroni-corrected for the number of comparisons, and "
            "discounted by an independence score for shared common "
            "vocabulary"),
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "what_this_does_not_say": (
            "It does not say that any semantic overlap with a public "
            "corpus is confirmation of a session. Overlap with material "
            "published AFTER the session proves nothing prospective -- "
            "the session could not have drawn on it and it could not have "
            "drawn on the session, so a later match is a coincidence "
            "check at most. Overlap with earlier, accessible material "
            "speaks only to prior exposure, which weighs against "
            "originality, not for prescience. Shared vocabulary is not "
            "correspondence, correspondence is not transfer, and none of "
            "it is a physical measurement."),
        "verdict": "COMPARISON_IS_NOT_PROSPECTIVE_EVIDENCE",
    }
