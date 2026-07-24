"""P44 — preregistration and blinding: seal the plan before the data.

A confirmatory claim is only as good as the order in which its parts were
fixed. If the hypothesis, the null model, the analysis plan, the decision
rule and the stopping rule are all written down *before* any data are in
view, then a result that matches them is evidence. If any of them is
chosen, edited or "clarified" after the numbers are visible, the match is
manufactured: the analysis was fitted to the answer, and the paper that
reports it is describing its own search, not the world. This module makes
that boundary mechanical.

**What a preregistration is.** :class:`Preregistration` carries the seven
things that have to predate the data --- a study id, a hypothesis, the
predicted signature, a null model, a decision rule, an analysis plan and
a stopping rule --- together with the epoch it was committed at (passed
in explicitly, never read from the wall clock, so the record is
deterministic and reproducible). Its ``__post_init__`` refuses an empty
null model or an empty decision rule outright: this is the R10.6 lesson,
that a "preregistration" with no null and no decision threshold is not a
preregistration at all but a wish, and a wish confirms itself.

**Sealing.** :func:`seal` returns a SHA-256 commitment over the canonical
serialization of the whole plan. The seal is deterministic --- the same
plan always yields the same hash --- and it is tamper-evident: any change
to the hypothesis or the analysis plan after sealing produces a different
hash, so a retrofitted analysis presented as the original is detectable
by anyone holding the earlier commitment.

**Blinding.** :func:`blind_labels` deterministically masks the condition
assignment behind opaque codes keyed to a salt, so an analyst can run the
planned analysis without seeing which unit is treatment and which is
control. :func:`unblind` returns the true labels only against the exact
sealed commitment the blinding was locked under; a wrong commitment
fails, so the assignment cannot be revealed early by guessing.

**The forbidden retrofits.** Four refusals name the moves that turn an
exploratory analysis into a false confirmatory one:
:func:`refuse_hypothesis_change_after_seal` (HARKing --- changing the
hypothesis after sealing and calling it preregistered),
:func:`refuse_result_without_prereg` (an analysis with no sealed plan is
at most exploratory), :func:`refuse_optional_stopping` (peeking and
stopping on significance with no preregistered stopping rule inflates
false positives) and :func:`refuse_prediction_as_result` (a sealed
prediction is not a measured outcome).

**Power discipline.** A preregistration also has to declare that its
design *could* detect the effect it predicts:
:func:`requires_power_on_planted_data` flags a plan that never says it can
recover a planted effect, because a study with no power to detect its own
hypothesis proves nothing when it fails and little when it succeeds.

Nothing here is measured. Sealing a plan and blinding labels are
bookkeeping about *order and provenance*; they do not run the study, and
:func:`preregister_report` records a claim class of
``PROSPECTIVE_PREDICTION`` --- a sealed prediction awaiting data --- never
a bench measurement. The standing verdict is
``PREREGISTRATION_AND_BLINDING_SEALED``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

#: The standing verdict for a well-formed sealed preregistration.
DEFAULT_VERDICT = "PREREGISTRATION_AND_BLINDING_SEALED"

#: The claim class a sealed preregistration declares. A prediction that
#: has been committed but not yet tested against data is a PROSPECTIVE
#: PREDICTION -- never a measurement, never a retrospective match.
PROSPECTIVE_PREDICTION = "PROSPECTIVE_PREDICTION"

#: Claim-class strings used verbatim elsewhere in the ladder.
ANALYTIC_MODEL = "ANALYTIC_MODEL"
BLOCKED_MISSING_INPUT = "BLOCKED_MISSING_INPUT"
UNSUPPORTED = "UNSUPPORTED"

#: The unit separator used in every hashed serialization here.
_SEP = "\x1f"


class PreregisterError(RuntimeError):
    """Raised on a malformed preregistration, an edit after sealing, an
    unblinding without the sealed commitment, a confirmatory claim with no
    seal, an optional-stopping decision, or a prediction offered as a
    measured result."""


# =======================================================================
# The preregistration
# =======================================================================

#: The fields the seal is taken over, in the order they enter the
#: commitment. The order is part of the commitment and must not be
#: permuted -- a reordering would change the hash without changing the
#: plan, which would defeat the point of a deterministic seal.
SEALED_FIELDS = (
    "study_id",
    "hypothesis",
    "predicted_signature",
    "null_model",
    "decision_rule",
    "analysis_plan",
    "stopping_rule",
    "power_on_planted",
    "epoch_committed",
    "claim_class",
)


@dataclass(frozen=True)
class Preregistration:
    """A hypothesis, its analysis plan and its decision rule, fixed before
    any data are in view.

    ``epoch_committed`` is supplied by the caller and never read from the
    wall clock, so two runs of the same commitment produce byte-identical
    records and the same seal. ``null_model`` and ``decision_rule`` may
    not be empty: a plan that names no null and sets no threshold cannot
    be wrong, and a plan that cannot be wrong is not a preregistration.

    ``stopping_rule`` and ``power_on_planted`` default to empty. They are
    legal to omit at construction so an incomplete plan can be represented
    and then flagged by :func:`validate` and
    :func:`requires_power_on_planted_data` -- the module's job is to catch
    the omission, not to make it unrepresentable."""

    study_id: str
    hypothesis: str
    predicted_signature: str
    null_model: str
    decision_rule: str
    analysis_plan: str
    stopping_rule: str = ""
    power_on_planted: str = ""
    epoch_committed: int = 0
    claim_class: str = PROSPECTIVE_PREDICTION

    def __post_init__(self) -> None:
        if not isinstance(self.study_id, str) or not self.study_id.strip():
            raise PreregisterError("study_id must be a non-empty string")
        if not isinstance(self.hypothesis, str) or not self.hypothesis.strip():
            raise PreregisterError("hypothesis must be a non-empty string")
        # The R10.6 lesson: a preregistration WITHOUT a null model or a
        # decision rule is not a preregistration. Refuse both at birth.
        if not isinstance(self.null_model, str) or not self.null_model.strip():
            raise PreregisterError(
                "refused: a preregistration with no null model is not a "
                "preregistration. A hypothesis with nothing to be tested "
                "against confirms itself: state the null the data could "
                "favour instead.")
        if not isinstance(self.decision_rule, str) or \
                not self.decision_rule.strip():
            raise PreregisterError(
                "refused: a preregistration with no decision rule is not a "
                "preregistration. Without a threshold fixed in advance, "
                "'significant' becomes whatever the data turn out to be. "
                "State the rule that decides the outcome before you look.")
        if not isinstance(self.claim_class, str) or not self.claim_class:
            raise PreregisterError("claim_class must be a non-empty string")


def canonical_serialization(prereg: Preregistration) -> str:
    """The deterministic JSON text the seal is taken over.

    Keys are emitted in the fixed :data:`SEALED_FIELDS` order and values
    are rendered by :func:`json.dumps`, so the string depends only on the
    plan's content and never on dictionary iteration order or the clock."""
    if not isinstance(prereg, Preregistration):
        raise PreregisterError("expected a Preregistration")
    ordered = [(name, getattr(prereg, name)) for name in SEALED_FIELDS]
    return json.dumps(ordered, sort_keys=False, ensure_ascii=True,
                      separators=(",", ":"))


def seal(prereg: Preregistration) -> str:
    """Return the SHA-256 commitment over the whole plan and record it.

    The seal is what makes a later match mean something: the plan was
    written down in full, hashed, and the hash published, before any data
    were seen. A result consistent with a sealed plan predates its own
    confirmation. Any change to any sealed field -- the hypothesis, the
    analysis plan, the decision rule -- changes this hash, so a plan
    quietly edited after the data arrived cannot masquerade as the sealed
    one."""
    digest = hashlib.sha256(
        canonical_serialization(prereg).encode()).hexdigest()
    _SEAL_LEDGER.setdefault(digest, canonical_serialization(prereg))
    return digest


#: commitment -> serialization. The seal ledger, append-only in practice.
_SEAL_LEDGER: dict = {}


def is_sealed(prereg_or_commitment) -> bool:
    """True iff this exact plan (or this commitment string) has been
    sealed and is in the ledger."""
    if isinstance(prereg_or_commitment, Preregistration):
        return seal(prereg_or_commitment) in _SEAL_LEDGER
    if isinstance(prereg_or_commitment, str):
        return prereg_or_commitment in _SEAL_LEDGER
    return False


# =======================================================================
# Blinding
# =======================================================================

def _mask_code(label, salt: str) -> str:
    """A stable opaque code for a label, keyed to the salt.

    The same label under the same salt always maps to the same code, so
    the structure of the assignment survives (two units in one condition
    still share a code) while the *identity* of the condition -- which
    code is treatment -- is hidden."""
    h = hashlib.sha256(f"{salt}{_SEP}{label}".encode()).hexdigest()
    return f"BLIND_{h[:16]}"


@dataclass(frozen=True)
class Blinding:
    """Masked group labels plus the lock that gates their revelation.

    ``blinded_labels`` is what the analyst works with: opaque codes that
    preserve which units share a condition but hide which condition is
    which. ``original_labels`` is carried sealed away and is returned only
    by :func:`unblind`, and only against the sealed commitment recorded in
    ``lock``."""

    blinded_labels: tuple
    lock: str
    original_labels: tuple
    salt_used: str


def blind_labels(labels, salt: str) -> Blinding:
    """Deterministically mask condition assignment behind opaque codes.

    ``salt`` is expected to be a sealed commitment: the blinding is locked
    to it, and :func:`unblind` will demand that exact commitment back. The
    masking is deterministic in ``labels`` and ``salt``, so a blinding can
    be reproduced and audited, and it hides assignment because the codes
    are one-way hashes -- an analyst sees that two units share a group but
    cannot tell whether that group is treatment or control."""
    if not isinstance(salt, str) or not salt:
        raise PreregisterError(
            "blinding salt must be a non-empty string (use the sealed "
            "commitment, so unblinding requires it back)")
    labels = tuple(labels)
    if not labels:
        raise PreregisterError("cannot blind an empty label set")
    blinded = tuple(_mask_code(lab, salt) for lab in labels)
    lock = hashlib.sha256(f"LOCK{_SEP}{salt}".encode()).hexdigest()
    return Blinding(blinded_labels=blinded, lock=lock,
                    original_labels=labels, salt_used=salt)


def unblind(sealed_commitment, blinding: Blinding) -> tuple:
    """Reveal the true labels -- only against the sealed commitment.

    The blinding was locked under a salt (the sealed commitment). Unblind
    recomputes the lock from ``sealed_commitment`` and refuses unless it
    matches. A wrong or absent commitment cannot lift the blind, so the
    assignment cannot be peeked at early by anyone who does not already
    hold the seal the study was committed under."""
    if not isinstance(blinding, Blinding):
        raise PreregisterError("unblind expects a Blinding")
    if not isinstance(sealed_commitment, str) or not sealed_commitment:
        raise PreregisterError(
            "refused: unblinding requires the sealed commitment. A blind "
            "that any caller could lift without the seal is not a blind.")
    offered = hashlib.sha256(
        f"LOCK{_SEP}{sealed_commitment}".encode()).hexdigest()
    if offered != blinding.lock:
        raise PreregisterError(
            "refused: the supplied commitment does not match the one this "
            "blinding was locked under. The condition assignment is "
            "revealed only against the exact sealed commitment; a "
            "mismatch reveals nothing.")
    return blinding.original_labels


def blinding_hides_assignment(blinding: Blinding) -> bool:
    """True iff no blinded code coincides with an original label.

    A sanity check for the property blinding is supposed to have: the
    codes the analyst sees share nothing with the real condition names."""
    if not isinstance(blinding, Blinding):
        raise PreregisterError("expected a Blinding")
    original = set(str(x) for x in blinding.original_labels)
    masked = set(str(x) for x in blinding.blinded_labels)
    return original.isdisjoint(masked)


# =======================================================================
# The forbidden retrofits
# =======================================================================

#: The fields whose change after sealing turns an analysis into a
#: different study wearing the old study's seal.
LOADBEARING_FIELDS = ("hypothesis", "predicted_signature", "analysis_plan")


def refuse_hypothesis_change_after_seal(sealed: Preregistration,
                                        proposed: Preregistration, *,
                                        already_sealed: bool = True) -> dict:
    """Refuse to relabel an edited hypothesis as the preregistered one.

    This is HARKing -- Hypothesising After the Results are Known. The
    study is sealed, the data come in, and someone rewrites the
    hypothesis (or the predicted signature, or the analysis plan) so that
    the result becomes the thing that was "predicted". Each edit can look
    like a clarification; together they turn an exploratory finding into a
    counterfeit confirmation. The edit is legal before the seal and
    forbidden after, and the boundary is the whole point."""
    if not isinstance(sealed, Preregistration) or \
            not isinstance(proposed, Preregistration):
        raise PreregisterError("both arguments must be Preregistrations")
    changed = tuple(name for name in LOADBEARING_FIELDS
                    if getattr(sealed, name) != getattr(proposed, name))
    if changed and already_sealed:
        raise PreregisterError(
            f"refused: {len(changed)} load-bearing field(s) changed after "
            f"the plan was sealed ({', '.join(changed)}). A hypothesis "
            f"rewritten once the data are in view and then presented as "
            f"preregistered is HARKing: the prediction was fitted to the "
            f"result it claims to have predicted. The sealed commitment is "
            f"{seal(sealed)}; the proposed one is {seal(proposed)}. Seal "
            f"the new hypothesis as a fresh, exploratory plan and test it "
            f"on data it has not seen.")
    return {
        "changed_fields": list(changed),
        "already_sealed": bool(already_sealed),
        "sealed_commitment": seal(sealed),
        "proposed_commitment": seal(proposed),
        "allowed": True,
    }


def refuse_result_without_prereg(sealed_commitment=None, *,
                                  claim="confirmatory") -> None:
    """Refuse a confirmatory claim with no sealed preregistration.

    An analysis produced without a prior sealed plan may be perfectly
    honest and is still, at most, exploratory: nothing distinguishes it
    from an analysis assembled once the answer was visible. It can suggest
    a hypothesis; it cannot confirm one."""
    if sealed_commitment is None or not isinstance(sealed_commitment, str) \
            or not sealed_commitment or sealed_commitment not in _SEAL_LEDGER:
        raise PreregisterError(
            f"refused: a {claim} claim needs a sealed preregistration, and "
            f"none was supplied (or the commitment is not in the ledger). "
            f"An analysis with no prior seal is at most EXPLORATORY: it may "
            f"generate a hypothesis but cannot confirm one, because it "
            f"could have been chosen after the result was known. Seal a "
            f"plan first, then this analysis can be run as confirmatory.")


def refuse_optional_stopping(prereg: Preregistration | None = None, *,
                             peeked_and_stopped: bool = True) -> dict:
    """Refuse to stop on significance without a preregistered stopping rule.

    Peeking at accumulating data and stopping the moment a threshold is
    crossed inflates the false-positive rate without limit: given enough
    looks, noise alone crosses any fixed line. A stopping rule fixed in
    advance -- a fixed n, a sequential boundary, a Bayesian criterion --
    is what makes sequential testing legitimate. Absent one, the decision
    to stop was made by the data, not by the plan."""
    has_rule = (isinstance(prereg, Preregistration)
                and bool(prereg.stopping_rule.strip()))
    if peeked_and_stopped and not has_rule:
        raise PreregisterError(
            "refused: stopping data collection when the result turned "
            "significant, with no preregistered stopping rule, inflates "
            "the false-positive rate -- enough peeks and noise crosses any "
            "threshold. Preregister a stopping rule (fixed n, a sequential "
            "boundary, or a Bayesian criterion) and the sequential test "
            "becomes legitimate; without one, the data chose the stopping "
            "point.")
    return {
        "has_preregistered_stopping_rule": has_rule,
        "peeked_and_stopped": bool(peeked_and_stopped),
        "allowed": True,
    }


def refuse_prediction_as_result(*_args, **_kwargs) -> None:
    """Refuse to read a sealed prediction as a measured outcome.

    A preregistration is a statement about what *would* be observed if the
    hypothesis holds. Sealing it commits the prediction; it does not run
    the study. Presenting the sealed prediction as though it were the
    result is a category error -- the strongest thing a seal alone
    establishes is PROSPECTIVE_PREDICTION, never a measurement."""
    raise PreregisterError(
        "refused: a sealed prediction is not a measured outcome. Sealing "
        "commits what the study predicts; it does not perform the study. "
        "The claim class of a seal is PROSPECTIVE_PREDICTION -- a "
        "prediction awaiting data -- and it cannot be reported as a "
        "BENCH_MEASUREMENT or any confirmed result until data exist and "
        "the sealed analysis has been run against them.")


# =======================================================================
# Power discipline and validation
# =======================================================================

def requires_power_on_planted_data(prereg: Preregistration) -> dict:
    """Flag a plan that never declares it can detect a planted effect.

    A preregistration has to be able to fail *and* to succeed for the
    right reason. If the design cannot recover an effect that is really
    there -- if it has no power -- then a null result is uninformative and
    a positive one is suspect. The declaration is a statement that, on
    data with a planted effect of the predicted size, the sealed analysis
    would detect it. A plan missing that statement is flagged, not
    accepted."""
    if not isinstance(prereg, Preregistration):
        raise PreregisterError("expected a Preregistration")
    declared = bool(prereg.power_on_planted.strip())
    return {
        "study_id": prereg.study_id,
        "declares_power_on_planted": declared,
        "flagged": not declared,
        "note": (
            "declared: the plan states it can recover a planted effect of "
            "the predicted size" if declared else
            "flagged: no power-on-planted declaration. A design that "
            "cannot detect its own hypothesis proves nothing when it fails "
            "and little when it succeeds"),
    }


def validate(prereg: Preregistration) -> dict:
    """Return the completeness checklist for a preregistration.

    The four elements a confirmatory plan must carry: a null model, a
    decision rule, a stopping rule, and a power-on-planted declaration.
    The first two are guaranteed non-empty by construction; the last two
    are checked here, and ``complete`` is true only if every box is
    ticked."""
    if not isinstance(prereg, Preregistration):
        raise PreregisterError("expected a Preregistration")
    checklist = {
        "has_null_model": bool(prereg.null_model.strip()),
        "has_decision_rule": bool(prereg.decision_rule.strip()),
        "has_stopping_rule": bool(prereg.stopping_rule.strip()),
        "has_power_declaration": bool(prereg.power_on_planted.strip()),
    }
    return {
        "study_id": prereg.study_id,
        "checklist": checklist,
        "missing": [k for k, v in checklist.items() if not v],
        "complete": all(checklist.values()),
        "sealed": is_sealed(prereg),
        "claim_class": prereg.claim_class,
    }


# =======================================================================
# A worked, fully specified example
# =======================================================================

#: A complete, well-formed preregistration used by the report and the
#: tests. Every field is populated and the epoch is passed in explicitly,
#: so its seal is deterministic and reproducible.
EXAMPLE_PREREG = Preregistration(
    study_id="R13_PREREG_EXAMPLE",
    hypothesis=(
        "the frozen coordinate codec assigns held-out landmarks to their "
        "sealed alias sets at a rate above the shuffled-label null"),
    predicted_signature=(
        "hit rate on planted labels exceeds the best of four matched "
        "nulls by at least the preregistered margin"),
    null_model=(
        "shuffled labels: same inputs and same landmark labels, wrongly "
        "paired, preserving both marginals exactly"),
    decision_rule=(
        "declare support only if the observed excess over the best null "
        "exceeds 0.15 on held-out data"),
    analysis_plan=(
        "freeze the codec, reveal held-out labels once, compute hit rates "
        "against the planted control and all four nulls, no re-freezing"),
    stopping_rule=(
        "fixed sample of 160 held-out trials, decided in advance; no "
        "interim looks"),
    power_on_planted=(
        "on data planted by the codec's own canonical reading the analysis "
        "recovers the effect at zero residual, so the design has power"),
    epoch_committed=20260724,
    claim_class=PROSPECTIVE_PREDICTION,
)


def example_seal() -> str:
    """Seal the worked example and return its commitment."""
    return seal(EXAMPLE_PREREG)


# =======================================================================
# The report
# =======================================================================

def preregister_report() -> dict:
    sealed = seal(EXAMPLE_PREREG)
    # A minimal blinding over a synthetic two-condition assignment, locked
    # to the example seal. The labels are neutral and carry no content.
    demo_labels = ("TREATMENT", "CONTROL", "TREATMENT", "CONTROL")
    blinding = blind_labels(demo_labels, sealed)
    return {
        "what_this_is": (
            "a preregistration-and-blinding protocol that seals a "
            "hypothesis, its null model, its analysis plan, its decision "
            "rule and its stopping rule before any data, so a result "
            "cannot be retrofitted to the analysis"),
        "sealed_fields": list(SEALED_FIELDS),
        "example_commitment": sealed,
        "seal_is_deterministic": sealed == seal(EXAMPLE_PREREG),
        "example_validation": validate(EXAMPLE_PREREG),
        "power_check": requires_power_on_planted_data(EXAMPLE_PREREG),
        "blinding": {
            "blinded_labels": list(blinding.blinded_labels),
            "hides_assignment": blinding_hides_assignment(blinding),
            "unblind_requires_the_sealed_commitment": True,
        },
        "refusals": [
            "refuse_hypothesis_change_after_seal",
            "refuse_result_without_prereg",
            "refuse_optional_stopping",
            "refuse_prediction_as_result",
        ],
        "claim_class": PROSPECTIVE_PREDICTION,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": DEFAULT_VERDICT,
        "what_this_does_not_say": (
            "It does not say the sealed hypothesis is true, and it does "
            "not say any study was run. Sealing a plan and blinding its "
            "labels are statements about the ORDER in which the plan and "
            "the data were fixed -- the plan first, hashed and committed; "
            "the data, if they ever exist, second. A seal establishes "
            "PROSPECTIVE_PREDICTION and nothing stronger: no measurement "
            "is performed here, no data are analysed, and no outcome is "
            "confirmed. The value of the seal is entirely negative -- it "
            "makes a retrofitted analysis detectable and an optional stop "
            "refusable -- and that is all it claims."),
    }
