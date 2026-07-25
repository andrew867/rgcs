"""P09 — blind operator mode: mask the condition so expectancy cannot leak.

An operator who can see which condition is active during acquisition or
analysis can, without any dishonesty, nudge a result toward what they
expect: a knob held a moment longer, a marginal trace kept rather than
retaken, a fit re-run until it "settles". Blinding removes the channel by
removing the knowledge. This module makes that discipline mechanical for
an experimental run and gates the one moment it is allowed to end ---
unblinding --- behind a sealed commitment and a locked dataset.

**Roles carry authority, not everyone can lift the blind.** Five roles
are named --- OPERATOR, CUSTODIAN, ANALYST, AUDITOR, and UNBLINDER. The
operator runs acquisition on blinded packets; the analyst analyses
blinded data; the auditor may verify but never reveal; only the CUSTODIAN
and the UNBLINDER hold unblinding authority. :func:`refuse_unauthorized_unblind`
turns an analyst (or operator, or auditor) reaching for the reveal into a
refusal.

**The operator sees codes, never the assignment.** :func:`operator_packet`
and :func:`ui_payload` emit one-way codes for the condition label and for
each masked facet --- preferred frequency, specimen class, orientation
label, predicted outcome --- reusing the R13 preregister blinding, whose
codes are SHA-256 masks keyed to a sealed commitment. The real values
never appear in the packet, and :func:`packet_hides_assignment` checks it.

**No peeking: unblind only after the data are locked.** The legitimate
order is acquire, lock, analyse-while-blinded, then unblind. Unblinding
before the dataset is locked is peeking --- the assignment could still
steer the acquisition it is supposed to be independent of --- and
:func:`refuse_unblind_before_lock` refuses it. Unblinding also demands the
exact sealed commitment the blinding was locked under; a wrong or absent
commitment reveals nothing.

**Accidents and emergencies are logged and cost evidence.** A blind that
breaks --- an accidental disclosure, or an emergency unblind for safety
--- is recorded, never silently swallowed, and downgrades the affected
run's evidence from blinded support to an exploratory floor. A broken
blind is a real event with a real cost.

**Exploratory is not confirmatory.** A run opened in exploratory mode
cannot be relabelled confirmatory after the fact
(:func:`refuse_relabel_confirmatory`); confirmatory standing has to be
declared before the data, not conferred once the answer is attractive.

Nothing here is measured. Every label, facet, and dataset is a synthetic
fixture; the strongest thing this module produces is a
``SOFTWARE_IMPLEMENTED`` protocol result, and no physical validation is
claimed. The standing verdict is ``BLIND_OPERATOR_MODE_ENFORCED``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from r13 import holdout as _holdout
from r13 import preregister as _prereg
from r13 import serialize as _serialize
from r15 import claims as _claims

# =======================================================================
# Standing verdict, claim class, and the evidence levels this touches
# =======================================================================

#: The standing verdict for a well-formed blinded run.
VERDICT = "BLIND_OPERATOR_MODE_ENFORCED"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: The claim class this module can produce from software alone: a
#: protocol implementation, never a measurement.
CLAIM_CLASS = _claims.ClaimClass.SOFTWARE_IMPLEMENTED.value

#: The evidence a run may support while the blind holds. E6 in the R15
#: ladder is "blinded holdout support" -- the best a blinded protocol
#: reaches on the ladder (a real physical measurement would still be
#: capped below E4 elsewhere for missing bindings; this is the protocol's
#: own ceiling, not a measurement claim).
BLINDED_EVIDENCE_LEVEL = _claims.EvidenceLevel.E6

#: Where a run's evidence falls once the blind is broken -- an accidental
#: disclosure or an emergency unblind. A broken blind is exploratory at
#: best: the expectancy channel it existed to close was open.
BROKEN_BLIND_EVIDENCE_LEVEL = _claims.EvidenceLevel.E1


class BlindingError(RuntimeError):
    """Raised on an unauthorized unblind, an unblind attempted before the
    data are locked, an unblind offered the wrong sealed commitment, or an
    attempt to relabel an exploratory run as confirmatory."""


# =======================================================================
# Roles and modes
# =======================================================================

class Role(Enum):
    """Who is acting on a blinded run.

    OPERATOR runs the acquisition on blinded packets; CUSTODIAN holds the
    sealed commitment and the true assignment; ANALYST analyses the
    blinded data; AUDITOR may verify the machinery but never reveal; and
    UNBLINDER is the role explicitly delegated to lift the blind once the
    data are locked."""

    OPERATOR = "OPERATOR"
    CUSTODIAN = "CUSTODIAN"
    ANALYST = "ANALYST"
    AUDITOR = "AUDITOR"
    UNBLINDER = "UNBLINDER"


#: The only roles that may lift a blind. An operator, analyst, or auditor
#: reaching for the reveal is refused.
UNBLIND_AUTHORIZED_ROLES = frozenset({Role.CUSTODIAN, Role.UNBLINDER})


class StudyMode(Enum):
    """Whether a run's result may confirm a hypothesis or only suggest one.

    An EXPLORATORY run generates hypotheses; a CONFIRMATORY run tests a
    hypothesis fixed in advance. The mode must be declared before the data
    and cannot be upgraded afterwards."""

    EXPLORATORY = "EXPLORATORY"
    CONFIRMATORY = "CONFIRMATORY"


class Stage(Enum):
    """The stage a blinded run has reached. Ordered by value; unblinding
    is legal only at or after LOCKED."""

    OPEN = 0        # session opened, assignment blinded
    ACQUIRING = 1   # operator running on blinded packets
    LOCKED = 2      # acquired data sealed; analysis may proceed blinded
    UNBLINDED = 3   # blind lifted (normal, or broken)


class Facet(Enum):
    """The sensitive attributes a blinded packet must not disclose."""

    CONDITION_LABEL = "CONDITION_LABEL"
    PREFERRED_FREQUENCY = "PREFERRED_FREQUENCY"
    SPECIMEN_CLASS = "SPECIMEN_CLASS"
    ORIENTATION_LABEL = "ORIENTATION_LABEL"
    PREDICTED_OUTCOME = "PREDICTED_OUTCOME"


# =======================================================================
# The one-way code: reuse the R13 preregister blinding
# =======================================================================

def _code(value, salt: str) -> str:
    """A stable one-way code for a single value, keyed to ``salt``.

    Reuses :func:`r13.preregister.blind_labels`, whose codes are SHA-256
    masks: the same value under the same salt always maps to the same
    code, and the code shares nothing with the value. ``salt`` is expected
    to be a sealed commitment, so the mapping cannot be reproduced (nor
    the value recovered) without it."""
    return _prereg.blind_labels((str(value),), salt).blinded_labels[0]


def blind(labels, salt: str) -> _prereg.Blinding:
    """Mask a condition assignment behind one-way codes.

    Thin wrapper over :func:`r13.preregister.blind_labels`: ``salt`` is the
    sealed commitment the blinding is locked to, and :func:`unblind` will
    demand it back. The returned :class:`~r13.preregister.Blinding`
    preserves which units share a condition while hiding which condition
    is which."""
    return _prereg.blind_labels(labels, salt)


def unblind(sealed_commitment: str, blinding: _prereg.Blinding) -> tuple:
    """Reveal the true labels, only against the sealed commitment.

    Delegates to :func:`r13.preregister.unblind` and re-raises its refusal
    as a :class:`BlindingError`, so callers of this module see one
    exception type. A wrong or absent commitment reveals nothing."""
    try:
        return _prereg.unblind(sealed_commitment, blinding)
    except _prereg.PreregisterError as exc:
        raise BlindingError(str(exc)) from exc


def blinding_hides_assignment(blinding: _prereg.Blinding) -> bool:
    """True iff no blinded code coincides with a real condition label."""
    return _prereg.blinding_hides_assignment(blinding)


# =======================================================================
# The sensitive truth (custodian-held) and the blinded packet (operator)
# =======================================================================

@dataclass(frozen=True)
class RunAssignment:
    """The sensitive truth about one run: which condition is active and
    the masked facets that go with it.

    This is what the operator must NOT see. ``condition_label`` is the
    real group name (e.g. ``"TREATMENT"``); ``facets`` is a tuple of
    ``(facet_name, value)`` pairs -- preferred frequency, specimen class,
    orientation, predicted outcome -- each of which is equally revealing
    and equally masked."""

    run_id: str
    condition_label: str
    facets: tuple = ()

    def facet_items(self) -> tuple:
        return tuple((str(name), str(val)) for name, val in self.facets)

    def real_values(self) -> frozenset:
        return frozenset({str(self.condition_label)}
                         | {v for _, v in self.facet_items()})


@dataclass(frozen=True)
class BlindedRunPacket:
    """What the operator (and the operator UI) receives: codes, no truth.

    ``blinded_code`` masks the condition; ``facet_codes`` masks each
    sensitive facet. The real values are not present -- an operator can
    run the acquisition and see that two runs share a condition without
    ever learning which condition it is."""

    run_id: str
    blinded_code: str
    facet_codes: tuple
    mode: str

    def facet_code_map(self) -> dict:
        return {str(name): str(code) for name, code in self.facet_codes}

    def all_codes(self) -> tuple:
        return (self.blinded_code,) + tuple(c for _, c in self.facet_codes)


def operator_packet(assignment: RunAssignment, salt: str,
                    mode: StudyMode) -> BlindedRunPacket:
    """Build the blinded packet an operator runs against.

    Every sensitive value in ``assignment`` -- the condition and every
    facet -- is replaced by a one-way code keyed to ``salt`` (the sealed
    commitment). The packet carries the codes and the study mode and
    nothing that identifies the condition."""
    if not isinstance(assignment, RunAssignment):
        raise BlindingError("operator_packet needs a RunAssignment")
    code = _code(assignment.condition_label, salt)
    facet_codes = tuple((name, _code(val, salt))
                        for name, val in assignment.facet_items())
    return BlindedRunPacket(run_id=assignment.run_id, blinded_code=code,
                            facet_codes=facet_codes, mode=mode.value)


def packet_hides_assignment(packet: BlindedRunPacket,
                            assignment: RunAssignment) -> bool:
    """True iff none of the packet's codes equals any real value.

    The property blinding must have: the operator's packet shares no
    string with the sensitive truth it was derived from. Computed over a
    numpy membership array so a single leak flips the result."""
    if not isinstance(packet, BlindedRunPacket):
        raise BlindingError("expected a BlindedRunPacket")
    real = assignment.real_values()
    codes = np.array(packet.all_codes(), dtype=object)
    leaks = np.array([c in real for c in codes], dtype=bool)
    return not bool(leaks.any())


def ui_payload(packet: BlindedRunPacket) -> dict:
    """The operator-facing UI payload: only codes, mode, and a marker.

    Deliberately excludes any assignment. The ``blinded`` flag and the
    absence of a ``condition_label``/facet-value key are the contract:
    :func:`payload_leaks_assignment` checks that the real truth never
    rode along in it."""
    if not isinstance(packet, BlindedRunPacket):
        raise BlindingError("expected a BlindedRunPacket")
    return {
        "run_id": packet.run_id,
        "blinded": True,
        "condition_code": packet.blinded_code,
        "facet_codes": packet.facet_code_map(),
        "mode": packet.mode,
        "note": ("operator view: condition and facets are one-way codes; "
                 "the assignment is not present in this payload"),
    }


def payload_leaks_assignment(payload: dict,
                             assignment: RunAssignment) -> bool:
    """True iff any real value appears anywhere in a UI payload's values."""
    real = assignment.real_values()
    seen = set()

    def _walk(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, (list, tuple)):
            for v in obj:
                _walk(v)
        else:
            seen.add(str(obj))

    _walk(payload)
    return bool(real & seen)


# =======================================================================
# The data lock: unblinding is gated on it
# =======================================================================

@dataclass(frozen=True)
class DataLock:
    """A seal over the acquired data, taken at a passed-in epoch.

    ``data_hash`` is the canonical content hash of the acquired dataset;
    ``epoch`` is supplied by the caller, never read from a clock, so the
    lock is deterministic and reproducible. A lock is what turns the
    acquisition into a fixed object that a later unblind cannot have
    steered."""

    data_hash: str
    epoch: int

    def matches(self, data) -> bool:
        return self.data_hash == _serialize.content_hash(data)


def lock_data(data, epoch: int) -> DataLock:
    """Seal a dataset under a content hash at an explicit epoch."""
    return DataLock(data_hash=_serialize.content_hash(data), epoch=int(epoch))


# =======================================================================
# Broken-blind events: accidental disclosure and emergency unblinding
# =======================================================================

@dataclass(frozen=True)
class Disclosure:
    """A recorded break in the blind: accidental or an emergency unblind.

    Every field is explicit and passed in. ``kind`` is ``"ACCIDENTAL"`` or
    ``"EMERGENCY"``; ``epoch`` is a passed-in timestamp; ``downgrades_to``
    records where the affected run's evidence falls as a result. A break
    is never silent -- it is logged and it costs evidence."""

    run_id: str
    kind: str
    reason: str
    epoch: int
    by_role: str
    downgrades_to: str = BROKEN_BLIND_EVIDENCE_LEVEL.name


# =======================================================================
# The session: the state a blinded run passes through
# =======================================================================

@dataclass
class BlindOperatorSession:
    """The state a blinded run passes through: open, acquire, lock, unblind.

    A session holds the sensitive assignments and the sealed commitment
    the blinding is locked to. The operator draws :meth:`operator_packets`
    and never the assignments; the data are locked with :meth:`lock`; and
    only after the lock, and only from an authorized role holding the
    sealed commitment, does :meth:`unblind` succeed. Accidental
    disclosures and emergency unblinds are recorded on the session and
    downgrade the evidence of the runs they touch."""

    study_id: str
    mode: StudyMode
    sealed_commitment: str
    assignments: tuple
    stage: Stage = Stage.OPEN
    data_lock: DataLock | None = None
    disclosures: tuple = ()
    revealed_labels: tuple | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.sealed_commitment, str) or \
                not self.sealed_commitment:
            raise BlindingError(
                "a blinded session needs a non-empty sealed commitment; "
                "the blinding is locked to it and unblinding demands it back")
        self.assignments = tuple(self.assignments)
        if not self.assignments:
            raise BlindingError("a session needs at least one RunAssignment")
        if not all(isinstance(a, RunAssignment) for a in self.assignments):
            raise BlindingError("assignments must be RunAssignment records")

    # -- the blinding over the condition labels --------------------------

    def condition_labels(self) -> tuple:
        return tuple(a.condition_label for a in self.assignments)

    def blinding(self) -> _prereg.Blinding:
        """The R13 blinding over this session's condition labels."""
        return blind(self.condition_labels(), self.sealed_commitment)

    # -- what the operator gets ------------------------------------------

    def operator_packets(self) -> tuple:
        """The blinded packets for every run. Contains no assignment."""
        if self.stage is Stage.OPEN:
            self.stage = Stage.ACQUIRING
        return tuple(operator_packet(a, self.sealed_commitment, self.mode)
                     for a in self.assignments)

    # -- locking the data ------------------------------------------------

    def lock(self, data, epoch: int) -> DataLock:
        """Seal the acquired data; unblinding becomes possible only now."""
        self.data_lock = lock_data(data, epoch)
        self.stage = Stage.LOCKED
        return self.data_lock

    @property
    def is_locked(self) -> bool:
        return self.data_lock is not None and self.stage.value >= \
            Stage.LOCKED.value

    # -- the recorded breaks ---------------------------------------------

    def record_accidental_disclosure(self, run_id: str, reason: str,
                                     epoch: int, by_role: Role) -> Disclosure:
        """Log an accidental disclosure and downgrade that run's evidence."""
        d = Disclosure(run_id=run_id, kind="ACCIDENTAL", reason=reason,
                       epoch=int(epoch), by_role=by_role.value)
        self.disclosures = self.disclosures + (d,)
        return d

    def emergency_unblind(self, role: Role, sealed_commitment: str,
                          reason: str, epoch: int) -> dict:
        """Break the blind early for cause. Logged; downgrades evidence.

        Unlike :meth:`unblind`, this does not require the data to be
        locked -- an emergency (a safety stop, a subject withdrawal) can
        arrive at any stage. It still requires an authorized role and the
        sealed commitment, it is always recorded as a
        :class:`Disclosure`, and it downgrades every affected run to the
        broken-blind evidence floor."""
        refuse_unauthorized_unblind(role)
        labels = unblind(sealed_commitment, self.blinding())
        d = Disclosure(run_id=self.study_id, kind="EMERGENCY", reason=reason,
                       epoch=int(epoch), by_role=role.value)
        self.disclosures = self.disclosures + (d,)
        self.revealed_labels = labels
        self.stage = Stage.UNBLINDED
        return {
            "study_id": self.study_id,
            "kind": "EMERGENCY",
            "logged": True,
            "reason": reason,
            "by_role": role.value,
            "epoch": int(epoch),
            "evidence_before": BLINDED_EVIDENCE_LEVEL.name,
            "evidence_after": BROKEN_BLIND_EVIDENCE_LEVEL.name,
            "downgraded": True,
            "revealed_label_count": len(labels),
        }

    def broken_runs(self) -> frozenset:
        """Run ids whose blind was broken by any recorded disclosure."""
        return frozenset(d.run_id for d in self.disclosures)

    def evidence_level_for(self, run_id: str) -> _claims.EvidenceLevel:
        """The evidence a run supports: blinded, unless its blind broke.

        A run touched by any disclosure -- accidental or emergency, and an
        emergency break is logged against the whole study -- falls to the
        broken-blind floor; an untouched run keeps the blinded level."""
        broken = self.broken_runs()
        if run_id in broken or self.study_id in broken:
            return BROKEN_BLIND_EVIDENCE_LEVEL
        return BLINDED_EVIDENCE_LEVEL

    # -- the reveal ------------------------------------------------------

    def unblind(self, role: Role, sealed_commitment: str,
                epoch: int) -> dict:
        """Lift the blind: authorized role, locked data, sealed commitment.

        Three gates, in order. The role must hold unblinding authority
        (:func:`refuse_unauthorized_unblind`); the data must already be
        locked, or this is peeking (:func:`refuse_unblind_before_lock`);
        and the sealed commitment must match the one the blinding was
        locked under, or nothing is revealed. Only when all three pass are
        the true labels returned."""
        refuse_unauthorized_unblind(role)
        refuse_unblind_before_lock(self)
        labels = unblind(sealed_commitment, self.blinding())
        self.revealed_labels = labels
        self.stage = Stage.UNBLINDED
        return {
            "study_id": self.study_id,
            "by_role": role.value,
            "epoch": int(epoch),
            "data_was_locked": True,
            "revealed_labels": list(labels),
            "claim_class": CLAIM_CLASS,
        }

    # -- mode discipline -------------------------------------------------

    def relabel_mode(self, new_mode: StudyMode) -> "BlindOperatorSession":
        """Change the study mode, subject to the confirmatory rule.

        Downgrading confirmatory to exploratory is always allowed; the
        forbidden move -- exploratory to confirmatory after the fact -- is
        refused by :func:`refuse_relabel_confirmatory`."""
        refuse_relabel_confirmatory(self.mode, new_mode)
        self.mode = new_mode
        return self


# =======================================================================
# The refusals
# =======================================================================

def refuse_unauthorized_unblind(role: Role) -> None:
    """Refuse an unblind attempted by a role without unblinding authority.

    Only CUSTODIAN and UNBLINDER may lift a blind. An operator or analyst
    who could unblind on their own could see the assignment during the
    very acquisition or analysis the blind exists to protect, which is the
    whole leak the blind was meant to close."""
    if not isinstance(role, Role):
        raise BlindingError("unblinding needs a Role")
    if role not in UNBLIND_AUTHORIZED_ROLES:
        raise BlindingError(
            f"refused: role {role.value} has no unblinding authority. The "
            f"blind may be lifted only by "
            f"{', '.join(sorted(r.value for r in UNBLIND_AUTHORIZED_ROLES))}; "
            f"an operator or analyst who could unblind themselves could see "
            f"the assignment during the acquisition or analysis the blind "
            f"exists to protect, reopening the expectancy channel.")


def refuse_unblind_before_lock(session: BlindOperatorSession) -> None:
    """Refuse an unblind attempted before the acquired data are locked.

    The legitimate order is acquire, lock, analyse-while-blinded, then
    unblind. Revealing the assignment before the dataset is locked is
    peeking: the assignment can still steer the acquisition it is supposed
    to be independent of, and an analysis run after an early reveal is no
    longer blinded even if it is presented as such. Lock the data first;
    then, and only then, may the blind be lifted."""
    locked = getattr(session, "is_locked", None)
    if locked is None:
        locked = getattr(session, "data_lock", None) is not None
    if not locked:
        raise BlindingError(
            "refused: an unblind was attempted before the acquired data "
            "were locked. This is peeking: with the data still open, "
            "knowing the assignment can steer the acquisition the blind is "
            "meant to protect, and any analysis after the reveal is no "
            "longer blinded. Lock the dataset (session.lock(...)) first, "
            "then unblind.")


def refuse_relabel_confirmatory(current: StudyMode,
                                proposed: StudyMode) -> None:
    """Refuse promoting an exploratory run to confirmatory after the fact.

    Confirmatory standing is a statement that the hypothesis and analysis
    were fixed before the data. A run opened as exploratory did not make
    that commitment; relabelling it confirmatory once the result looks
    attractive manufactures a confirmation out of an exploration. The
    reverse -- confirmatory down to exploratory -- is always allowed."""
    if current is StudyMode.EXPLORATORY and proposed is StudyMode.CONFIRMATORY:
        raise BlindingError(
            "refused: an EXPLORATORY run cannot be relabelled CONFIRMATORY. "
            "Confirmatory standing means the hypothesis and analysis were "
            "sealed before the data; a run opened as exploratory made no "
            "such commitment, and promoting it after the result is visible "
            "turns an exploration into a counterfeit confirmation. Open a "
            "fresh confirmatory run with a sealed plan instead.")


# =======================================================================
# A worked, fully specified example and the report
# =======================================================================

#: A sealed commitment used by the report and the tests. Built from a
#: complete R13 preregistration so it is a genuine seal, and deterministic
#: because every field (including the epoch) is fixed.
EXAMPLE_COMMITMENT = _prereg.seal(_prereg.EXAMPLE_PREREG)


def example_assignments() -> tuple:
    """A synthetic two-condition assignment with masked facets.

    Neutral labels and abstract facet values -- nothing here names or
    implies any real quantity, specimen, or prediction."""
    return (
        RunAssignment(
            run_id="RUN_0001", condition_label="CONDITION_A",
            facets=((Facet.PREFERRED_FREQUENCY.value, "FREQ_TOKEN_1"),
                    (Facet.SPECIMEN_CLASS.value, "CLASS_X"),
                    (Facet.ORIENTATION_LABEL.value, "ORI_0"),
                    (Facet.PREDICTED_OUTCOME.value, "OUTCOME_HIGH"))),
        RunAssignment(
            run_id="RUN_0002", condition_label="CONDITION_B",
            facets=((Facet.PREFERRED_FREQUENCY.value, "FREQ_TOKEN_2"),
                    (Facet.SPECIMEN_CLASS.value, "CLASS_Y"),
                    (Facet.ORIENTATION_LABEL.value, "ORI_1"),
                    (Facet.PREDICTED_OUTCOME.value, "OUTCOME_LOW"))),
    )


def blinding_report() -> dict:
    """The standing result: a blinded run with a gated, logged reveal."""
    assignments = example_assignments()
    session = BlindOperatorSession(
        study_id="R15_P09_BLIND_DEMO",
        mode=StudyMode.CONFIRMATORY,
        sealed_commitment=EXAMPLE_COMMITMENT,
        assignments=assignments,
    )
    packets = session.operator_packets()
    payload = ui_payload(packets[0])
    hides = all(packet_hides_assignment(p, a)
                for p, a in zip(packets, assignments))
    payload_clean = not payload_leaks_assignment(payload, assignments[0])

    # Peeking is refused before the lock.
    peek_refused = False
    try:
        session.unblind(Role.UNBLINDER, EXAMPLE_COMMITMENT, epoch=20260724)
    except BlindingError:
        peek_refused = True

    # An analyst has no authority to unblind, even after the lock.
    session.lock({"run": "RUN_0001", "samples": [1, 2, 3]}, epoch=20260724)
    analyst_refused = False
    try:
        session.unblind(Role.ANALYST, EXAMPLE_COMMITMENT, epoch=20260725)
    except BlindingError:
        analyst_refused = True

    # A wrong commitment reveals nothing.
    wrong_commitment_refused = False
    try:
        session.unblind(Role.CUSTODIAN, EXAMPLE_COMMITMENT + "00", epoch=1)
    except BlindingError:
        wrong_commitment_refused = True

    # The custodian, after the lock, with the sealed commitment, succeeds.
    revealed = session.unblind(Role.CUSTODIAN, EXAMPLE_COMMITMENT,
                               epoch=20260726)

    # Exploratory cannot be relabelled confirmatory.
    relabel_refused = False
    try:
        refuse_relabel_confirmatory(StudyMode.EXPLORATORY,
                                    StudyMode.CONFIRMATORY)
    except BlindingError:
        relabel_refused = True

    # An emergency unblind on a fresh session is logged and downgrades.
    emergency_session = BlindOperatorSession(
        study_id="R15_P09_EMERGENCY_DEMO",
        mode=StudyMode.CONFIRMATORY,
        sealed_commitment=EXAMPLE_COMMITMENT,
        assignments=assignments,
    )
    emergency = emergency_session.emergency_unblind(
        Role.UNBLINDER, EXAMPLE_COMMITMENT,
        reason="synthetic safety stop", epoch=20260727)

    return {
        "what_this_is": (
            "a blind operator mode: condition and facet labels are masked "
            "behind one-way codes so the operator cannot see the "
            "assignment during acquisition or analysis, and unblinding is "
            "gated on an authorized role, a locked dataset, and the sealed "
            "commitment the blinding was locked under"),
        "roles": [r.value for r in Role],
        "unblind_authorized_roles":
            sorted(r.value for r in UNBLIND_AUTHORIZED_ROLES),
        "study_modes": [m.value for m in StudyMode],
        "masked_facets": [f.value for f in Facet],
        "sealed_commitment": EXAMPLE_COMMITMENT,
        "operator_packet_example": ui_payload(packets[0]),
        "operator_packet_hides_assignment": hides,
        "ui_payload_free_of_assignment": payload_clean,
        "peek_before_lock_refused": peek_refused,
        "analyst_unblind_refused": analyst_refused,
        "wrong_commitment_refused": wrong_commitment_refused,
        "authorized_unblind_succeeded":
            revealed["revealed_labels"] == list(session.condition_labels()),
        "exploratory_to_confirmatory_refused": relabel_refused,
        "emergency_unblind_logged": emergency["logged"],
        "emergency_downgrades_evidence": (
            emergency["evidence_before"] == BLINDED_EVIDENCE_LEVEL.name
            and emergency["evidence_after"] == BROKEN_BLIND_EVIDENCE_LEVEL.name),
        "evidence_after_emergency":
            emergency_session.evidence_level_for("RUN_0001").name,
        "refusals": [
            "refuse_unauthorized_unblind",
            "refuse_unblind_before_lock",
            "refuse_relabel_confirmatory",
        ],
        "claim_class": CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not say any condition, specimen, orientation, "
            "frequency, or predicted outcome is real: every label and "
            "facet here is a synthetic fixture. It does not measure "
            "anything and claims no physical validation. Blinding is a "
            "statement about what the operator can see and when the blind "
            "may be lifted -- codes during acquisition and analysis, a "
            "reveal only from an authorized role after the data are locked "
            "and against the sealed commitment. A blind that breaks is "
            "logged and costs evidence; an exploratory run is never "
            "silently promoted to confirmatory. The strongest class here "
            "is SOFTWARE_IMPLEMENTED."),
    }


__all__ = [
    "VERDICT", "PHYSICAL_VALIDATION", "CLAIM_CLASS",
    "BLINDED_EVIDENCE_LEVEL", "BROKEN_BLIND_EVIDENCE_LEVEL",
    "BlindingError",
    "Role", "UNBLIND_AUTHORIZED_ROLES", "StudyMode", "Stage", "Facet",
    "blind", "unblind", "blinding_hides_assignment",
    "RunAssignment", "BlindedRunPacket", "operator_packet",
    "packet_hides_assignment", "ui_payload", "payload_leaks_assignment",
    "DataLock", "lock_data", "Disclosure", "BlindOperatorSession",
    "refuse_unauthorized_unblind", "refuse_unblind_before_lock",
    "refuse_relabel_confirmatory",
    "EXAMPLE_COMMITMENT", "example_assignments", "blinding_report",
]
