"""P12 — the residual classifier: type a residual without inflating it.

A residual is what is left after the model, the calibration, and the known
ordinary effects have all been subtracted from an observation. The whole
point of R15 is to keep that residual *honest*: to give it exactly one claim
class, and to make the ceiling for anything a single laboratory can produce
an ``UNEXPLAINED_INSTRUMENT_RESIDUAL`` -- never new physics, never a
detection, never a ``PHRYLL_DETECTED`` state.

This module is the classifier. Given a residual magnitude, its error budget
(the combined uncertainty, decomposed per the R15 error-budget policy), the
results of the ordinary-explanation attacks (the P11 *concept* -- attack
results are passed in as inputs; this module does **not** import P11), and
any independent-replication evidence, it returns exactly one
:class:`~r15.claims.ClaimClass`:

* **within budget** -- the residual does not exceed the combined
  uncertainty. It is a ``KNOWN_ORDINARY_EFFECT`` and is **not anomalous**. A
  residual below combined uncertainty is never anomalous.
* **an ordinary attack fired** -- an ordinary explanation accounts for the
  residual. It is that attack's ordinary cause:
  ``KNOWN_ORDINARY_EFFECT``, ``MODEL_ERROR``, ``CALIBRATION_ERROR`` or
  ``FIXTURE_EFFECT``. Missing or invalid calibration forces a
  ``CALIBRATION_ERROR`` (invalid) state before anything else is considered;
  an inadequate model forces a ``MODEL_ERROR``.
* **survives every attack, exceeds the combined uncertainty, and is
  unreplicated** -- the ceiling: ``UNEXPLAINED_INSTRUMENT_RESIDUAL``. It is
  anomalous *and unexplained*, and that is as far as one laboratory's run
  can go.
* **independently replicated** -- only genuine independent replication
  (passed in: at least two distinct independent labs, each confirming the
  residual survived the full battery) can reach ``REPLICATED_ANOMALY``. One
  run, or one lab, cannot.

Nothing here is measured. The classifier types inputs it is given; it
operates no apparatus and acquires nothing. ``measured_here`` is
``"nothing"`` and ``PHYSICAL_VALIDATION_NOT_CLAIMED``. An
``UNEXPLAINED_INSTRUMENT_RESIDUAL`` is not new physics
(:func:`refuse_residual_as_new_physics`), it is not a replicated anomaly
without replication
(:func:`refuse_unexplained_as_replicated_without_replication`), and there is
no ``PHRYLL_DETECTED`` state (:func:`refuse_phryll_detected`, reused from the
governance core).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import sqrt
from typing import Mapping

import numpy as np

from r15 import claims

# --- standing vocabulary -------------------------------------------------

#: The standing verdict for this module.
VERDICT = "RESIDUAL_CLASSIFIER_TYPED_CEILING_AT_UNEXPLAINED_RESIDUAL"

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: The class of the classifier machinery itself.
SOFTWARE_CLAIM_CLASS = claims.ClaimClass.SOFTWARE_IMPLEMENTED

#: The strongest label an unreplicated residual can carry: the ceiling.
RESIDUAL_CEILING = claims.ClaimClass.UNEXPLAINED_INSTRUMENT_RESIDUAL

#: Bumped whenever the classification rules change; carried on every record
#: so a classification change is versioned and auditable.
CLASSIFIER_VERSION = "1.0.0"

#: The error-budget components, per R15_ERROR_BUDGET_POLICY, in canonical
#: order. Combined uncertainty is their quadrature sum.
CANONICAL_BUDGET_COMPONENTS: tuple = (
    "instrument_resolution",
    "calibration",
    "clock",
    "environment",
    "fixture_repeatability",
    "specimen_geometry",
    "orientation",
    "numerical_method",
    "dsp",
    "operator_action",
    "model_residual",
)

#: The ordinary-explanation causes a fired attack may carry. A residual that
#: an ordinary attack explains is one of exactly these; none of them is
#: anomalous.
ORDINARY_CAUSE_CLASSES: frozenset = frozenset({
    claims.ClaimClass.KNOWN_ORDINARY_EFFECT,
    claims.ClaimClass.MODEL_ERROR,
    claims.ClaimClass.CALIBRATION_ERROR,
    claims.ClaimClass.FIXTURE_EFFECT,
})

#: Deterministic precedence when several ordinary attacks fire at once: the
#: most fundamental instrument problem is reported first. A calibration
#: fault invalidates the number outright; a fixture effect is a boundary
#: artifact; a model error is a derivation fault; a known ordinary effect is
#: the mildest. This ordering makes a multi-fire classification reproducible.
ORDINARY_CAUSE_PRECEDENCE: tuple = (
    claims.ClaimClass.CALIBRATION_ERROR,
    claims.ClaimClass.FIXTURE_EFFECT,
    claims.ClaimClass.MODEL_ERROR,
    claims.ClaimClass.KNOWN_ORDINARY_EFFECT,
)

#: Independent replication requires at least this many *distinct* independent
#: laboratories, each confirming the residual survived the full battery. Two,
#: not one: a single lab -- however many times it repeats -- cannot claim
#: independent replication.
MIN_INDEPENDENT_LABS = 2


class ResidualError(RuntimeError):
    """Raised on a malformed input or a forbidden residual promotion."""


# --- the error budget ----------------------------------------------------

@dataclass(frozen=True)
class ErrorBudget:
    """A residual's combined uncertainty, decomposed per the R15 policy.

    ``components`` maps a subset of :data:`CANONICAL_BUDGET_COMPONENTS` to a
    non-negative standard uncertainty in the residual's units; the combined
    uncertainty is their quadrature sum. ``calibration_bound`` records
    whether a valid calibration underpins the budget -- without it the
    residual cannot be trusted and is forced to a ``CALIBRATION_ERROR``
    (invalid) state. ``model_adequate`` records whether the model that
    produced the residual is adequate; an inadequate model forces a
    ``MODEL_ERROR``.
    """

    components: Mapping[str, float]
    calibration_bound: bool = True
    model_adequate: bool = True

    def __post_init__(self) -> None:
        comps = dict(self.components)
        if not comps:
            raise ResidualError(
                "an error budget with no components declares no "
                "uncertainty; a residual with no combined uncertainty cannot "
                "be classified")
        unknown = set(comps) - set(CANONICAL_BUDGET_COMPONENTS)
        if unknown:
            raise ResidualError(
                f"unknown error-budget component(s) {sorted(unknown)}; the "
                f"policy names {list(CANONICAL_BUDGET_COMPONENTS)}")
        clean: dict[str, float] = {}
        for name, value in comps.items():
            v = float(value)
            if not np.isfinite(v) or v < 0.0:
                raise ResidualError(
                    f"error-budget component {name!r} must be a finite, "
                    f"non-negative standard uncertainty, got {value!r}")
            clean[name] = v
        object.__setattr__(self, "components", clean)

    def combined(self) -> float:
        """The combined standard uncertainty: the quadrature sum."""
        return sqrt(sum(v * v for v in self.components.values()))

    def as_dict(self) -> dict:
        """Canonical, schema-shaped combined_uncertainty object."""
        return {
            "components": {name: self.components[name]
                          for name in CANONICAL_BUDGET_COMPONENTS
                          if name in self.components},
            "combined": self.combined(),
            "calibration_bound": bool(self.calibration_bound),
            "model_adequate": bool(self.model_adequate),
        }


# --- the ordinary-explanation attack results (P11 concept, passed in) ----

@dataclass(frozen=True)
class OrdinaryAttackResult:
    """One ordinary-explanation attack's verdict, supplied by the caller.

    This is the P11 *concept* as an input: the classifier never runs the
    attacks and never imports P11. ``cause`` is the ordinary class the
    attack maps to (one of :data:`ORDINARY_CAUSE_CLASSES`); ``fired`` is
    ``True`` when the attack accounted for the residual.
    """

    name: str
    cause: claims.ClaimClass
    fired: bool
    detail: str = ""

    def __post_init__(self) -> None:
        if not str(self.name).strip():
            raise ResidualError("an attack result needs a name")
        if self.cause not in ORDINARY_CAUSE_CLASSES:
            raise ResidualError(
                f"attack {self.name!r} cause {self.cause} is not an ordinary "
                f"cause; ordinary causes are "
                f"{sorted(c.value for c in ORDINARY_CAUSE_CLASSES)}")

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "cause": self.cause.value,
            "fired": bool(self.fired),
            "detail": self.detail,
        }


# --- independent replication evidence (passed in) ------------------------

@dataclass(frozen=True)
class ReplicationRecord:
    """One laboratory's replication attempt for a residual, supplied in.

    ``independent`` is ``True`` only for a laboratory independent of the
    originating one; ``confirmed`` is ``True`` when that lab reproduced the
    residual and it survived the full ordinary-explanation battery there.
    """

    lab_id: str
    independent: bool
    confirmed: bool

    def __post_init__(self) -> None:
        if not str(self.lab_id).strip():
            raise ResidualError("a replication record needs a lab_id")

    def as_dict(self) -> dict:
        return {
            "lab_id": self.lab_id,
            "independent": bool(self.independent),
            "confirmed": bool(self.confirmed),
        }


@dataclass(frozen=True)
class ReplicationEvidence:
    """The set of replication attempts for a residual.

    Independent replication is reached only when at least
    :data:`MIN_INDEPENDENT_LABS` *distinct* laboratories are both
    ``independent`` and ``confirmed``. A single lab -- or the same lab
    repeated -- can never satisfy this.
    """

    replications: tuple = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "replications", tuple(self.replications))
        for r in self.replications:
            if not isinstance(r, ReplicationRecord):
                raise ResidualError(
                    f"{r!r} is not a ReplicationRecord")

    def independent_confirming_labs(self) -> frozenset:
        return frozenset(r.lab_id for r in self.replications
                        if r.independent and r.confirmed)

    def is_independently_replicated(self) -> bool:
        return len(self.independent_confirming_labs()) >= MIN_INDEPENDENT_LABS

    def as_list(self) -> list:
        return [r.as_dict() for r in self.replications]


# --- the classification result -------------------------------------------

@dataclass(frozen=True)
class Classification:
    """The verdict for one residual: exactly one claim class, and why."""

    claim_class: claims.ClaimClass
    anomalous: bool
    exceeds_uncertainty: bool
    survived_all_attacks: bool
    replicated: bool
    cause: claims.ClaimClass | None
    rationale: str

    def as_dict(self) -> dict:
        return {
            "claim_class": self.claim_class.value,
            "anomalous": bool(self.anomalous),
            "exceeds_uncertainty": bool(self.exceeds_uncertainty),
            "survived_all_attacks": bool(self.survived_all_attacks),
            "replicated": bool(self.replicated),
            "cause": None if self.cause is None else self.cause.value,
            "rationale": self.rationale,
        }


# --- the residual dossier (residual_record.schema.json) -------------------

@dataclass(frozen=True)
class ResidualRecord:
    """A residual dossier: the residual, its budget, its attacks, its class.

    Serializes to ``residual_record.schema.json`` -- ``residual_id``,
    ``observation_ids``, ``ordinary_explanation_attacks``,
    ``combined_uncertainty``, ``classification`` and ``reopening_test`` --
    plus the honest standing fields (``measured_here``,
    ``physical_validation``) and the ``classifier_version`` so a
    classification change is versioned.
    """

    residual_id: str
    observation_ids: tuple
    residual_magnitude: float
    error_budget: ErrorBudget
    attacks: tuple
    replication: ReplicationEvidence
    classification: Classification
    reopening_test: str
    classifier_version: str = CLASSIFIER_VERSION

    def as_dict(self) -> dict:
        return {
            "residual_id": self.residual_id,
            "observation_ids": list(self.observation_ids),
            "residual_magnitude": float(self.residual_magnitude),
            "ordinary_explanation_attacks": [a.as_dict() for a in self.attacks],
            "combined_uncertainty": self.error_budget.as_dict(),
            "replication": self.replication.as_list(),
            "classification": self.classification.claim_class.value,
            "classification_detail": self.classification.as_dict(),
            "reopening_test": self.reopening_test,
            "classifier_version": self.classifier_version,
            "evidence_ceiling": RESIDUAL_CEILING.value,
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
            "verdict": VERDICT,
        }


# --- reopening tests ------------------------------------------------------

def _reopening_test(claim_class: claims.ClaimClass) -> str:
    """The test that would reopen a given classification.

    Every classification is provisional: it names the evidence that must be
    re-run for the class to change. The ceiling's reopening test is the
    strictest -- only independent replication can reopen it, and never a
    single lab or a single run.
    """
    if claim_class is claims.ClaimClass.KNOWN_ORDINARY_EFFECT:
        return ("Reopen if a re-derived residual, or a tightened error "
                "budget, makes the residual exceed the combined uncertainty; "
                "then re-run the full ordinary-explanation battery.")
    if claim_class is claims.ClaimClass.CALIBRATION_ERROR:
        return ("Reopen after a valid calibration is bound and the residual "
                "is re-derived; without calibration the classification is "
                "invalid and no anomaly may be claimed.")
    if claim_class is claims.ClaimClass.MODEL_ERROR:
        return ("Reopen after the model is corrected or shown adequate and "
                "the residual is re-derived; then re-run the full battery.")
    if claim_class is claims.ClaimClass.FIXTURE_EFFECT:
        return ("Reopen after the fixture/boundary condition is corrected "
                "and the residual is re-derived; then re-run the full "
                "battery.")
    if claim_class is RESIDUAL_CEILING:
        return ("Reopen ONLY via independent replication in at least "
                f"{MIN_INDEPENDENT_LABS} distinct laboratories, each "
                "confirming the residual survives the full "
                "ordinary-explanation battery. A single lab or a single run "
                "cannot reopen this to a REPLICATED_ANOMALY, and it is never "
                "new physics.")
    if claim_class is claims.ClaimClass.REPLICATED_ANOMALY:
        return ("Reopen if any contributing replication is retracted or "
                "found non-independent, dropping the distinct independent-lab "
                f"count below {MIN_INDEPENDENT_LABS}.")
    return "Reopen if the classifying inputs change."  # pragma: no cover


# --- the classifier -------------------------------------------------------

class ResidualClassifier:
    """Classify a residual into exactly one claim class, without inflation.

    The classifier is pure and deterministic: the same inputs always yield
    the same dossier. It operates no apparatus and acquires nothing.
    """

    version = CLASSIFIER_VERSION

    def classify(
        self,
        *,
        residual_id: str,
        observation_ids,
        residual_magnitude: float,
        error_budget: ErrorBudget,
        attacks=(),
        replication: ReplicationEvidence | None = None,
    ) -> ResidualRecord:
        """Return the residual dossier for one residual.

        The decision order is fixed:

        1. **calibration gate** -- an unbound/invalid calibration forces
           ``CALIBRATION_ERROR`` (invalid); no anomaly may be claimed.
        2. **within budget** -- a residual not exceeding the combined
           uncertainty is a ``KNOWN_ORDINARY_EFFECT`` and is not anomalous.
        3. **ordinary explanation** -- if any ordinary attack fired (an
           inadequate model counts as a fired ``MODEL_ERROR``), the residual
           is that fired attack's ordinary cause, by precedence.
        4. **the ceiling** -- a residual that survives every attack and
           exceeds the combined uncertainty is an
           ``UNEXPLAINED_INSTRUMENT_RESIDUAL`` unless genuine independent
           replication is supplied, in which case -- and only then -- it is a
           ``REPLICATED_ANOMALY``.
        """
        if not str(residual_id).strip():
            raise ResidualError("a residual needs an id")
        obs = tuple(observation_ids)
        if not obs:
            raise ResidualError(
                f"{residual_id}: a residual must reference at least one "
                f"observation")
        mag = float(residual_magnitude)
        if not np.isfinite(mag) or mag < 0.0:
            raise ResidualError(
                f"{residual_id}: residual magnitude must be a finite, "
                f"non-negative value, got {residual_magnitude!r}")
        if not isinstance(error_budget, ErrorBudget):
            raise ResidualError(
                f"{residual_id}: error_budget must be an ErrorBudget")
        attacks = tuple(attacks)
        for a in attacks:
            if not isinstance(a, OrdinaryAttackResult):
                raise ResidualError(f"{a!r} is not an OrdinaryAttackResult")
        replication = replication or ReplicationEvidence()

        combined = error_budget.combined()
        exceeds = mag > combined

        classification = self._decide(
            residual_id=residual_id,
            magnitude=mag,
            combined=combined,
            exceeds=exceeds,
            error_budget=error_budget,
            attacks=attacks,
            replication=replication,
        )
        return ResidualRecord(
            residual_id=residual_id,
            observation_ids=obs,
            residual_magnitude=mag,
            error_budget=error_budget,
            attacks=attacks,
            replication=replication,
            classification=classification,
            reopening_test=_reopening_test(classification.claim_class),
        )

    def _decide(self, *, residual_id, magnitude, combined, exceeds,
                error_budget, attacks, replication) -> Classification:
        # -- fired ordinary attacks, plus model adequacy folded in as a
        #    synthesized MODEL_ERROR attack --
        fired_causes = {a.cause for a in attacks if a.fired}
        if not error_budget.model_adequate:
            fired_causes.add(claims.ClaimClass.MODEL_ERROR)
        survived_all = not fired_causes and error_budget.model_adequate

        # 1. calibration gate: an unbound calibration invalidates the number
        if not error_budget.calibration_bound:
            return Classification(
                claim_class=claims.ClaimClass.CALIBRATION_ERROR,
                anomalous=False,
                exceeds_uncertainty=exceeds,
                survived_all_attacks=False,
                replicated=False,
                cause=claims.ClaimClass.CALIBRATION_ERROR,
                rationale=(
                    "no valid calibration is bound to the residual; the "
                    "measurement is invalid and forced to CALIBRATION_ERROR "
                    "before any anomaly can be considered"),
            )

        # 2. within budget: a residual below combined uncertainty is not
        #    anomalous
        if not exceeds:
            return Classification(
                claim_class=claims.ClaimClass.KNOWN_ORDINARY_EFFECT,
                anomalous=False,
                exceeds_uncertainty=False,
                survived_all_attacks=survived_all,
                replicated=False,
                cause=claims.ClaimClass.KNOWN_ORDINARY_EFFECT,
                rationale=(
                    f"residual {magnitude:.6g} does not exceed the combined "
                    f"uncertainty {combined:.6g}; a residual below combined "
                    f"uncertainty is not anomalous"),
            )

        # 3. an ordinary explanation fired: report the highest-precedence one
        if fired_causes:
            cause = self._highest_precedence(fired_causes)
            return Classification(
                claim_class=cause,
                anomalous=False,
                exceeds_uncertainty=True,
                survived_all_attacks=False,
                replicated=False,
                cause=cause,
                rationale=(
                    f"residual {magnitude:.6g} exceeds the combined "
                    f"uncertainty {combined:.6g} but an ordinary explanation "
                    f"fired ({cause.value}); it is explained, not anomalous"),
            )

        # 4. the ceiling: survives every attack and exceeds uncertainty
        replicated = replication.is_independently_replicated()
        if replicated:
            return Classification(
                claim_class=claims.ClaimClass.REPLICATED_ANOMALY,
                anomalous=True,
                exceeds_uncertainty=True,
                survived_all_attacks=True,
                replicated=True,
                cause=None,
                rationale=(
                    f"residual {magnitude:.6g} exceeds the combined "
                    f"uncertainty {combined:.6g}, survived every "
                    f"ordinary-explanation attack, and was independently "
                    f"replicated by "
                    f"{sorted(replication.independent_confirming_labs())}"),
            )
        return Classification(
            claim_class=RESIDUAL_CEILING,
            anomalous=True,
            exceeds_uncertainty=True,
            survived_all_attacks=True,
            replicated=False,
            cause=None,
            rationale=(
                f"residual {magnitude:.6g} exceeds the combined uncertainty "
                f"{combined:.6g} and survived every ordinary-explanation "
                f"attack, but is unreplicated: the ceiling is "
                f"UNEXPLAINED_INSTRUMENT_RESIDUAL. This is not new physics "
                f"and not a replicated anomaly."),
        )

    @staticmethod
    def _highest_precedence(causes: set) -> claims.ClaimClass:
        for c in ORDINARY_CAUSE_PRECEDENCE:
            if c in causes:
                return c
        # every ordinary cause is in the precedence table
        raise ResidualError(  # pragma: no cover
            f"no precedence for causes {causes!r}")


# --- the load-bearing refusals -------------------------------------------

def refuse_residual_as_new_physics(*_a, **_k) -> None:
    """An unexplained instrument residual is not new physics. Always raises.

    Delegates to the governance core's canonical refusal so the text stays
    single-sourced, but raises a :class:`ResidualError` for this lane.
    """
    try:
        claims.refuse_residual_as_new_physics()
    except claims.ClaimError as exc:
        raise ResidualError(str(exc)) from exc


def refuse_unexplained_as_replicated_without_replication(
        replication: ReplicationEvidence | None = None) -> None:
    """Refuse to call an unreplicated residual a replicated anomaly.

    An ``UNEXPLAINED_INSTRUMENT_RESIDUAL`` becomes a ``REPLICATED_ANOMALY``
    only with independent replication in at least
    :data:`MIN_INDEPENDENT_LABS` distinct laboratories. One run, or one lab,
    cannot promote it. Always raises.
    """
    labs = (sorted(replication.independent_confirming_labs())
            if replication is not None else [])
    raise ResidualError(
        f"refused: an UNEXPLAINED_INSTRUMENT_RESIDUAL cannot be promoted to "
        f"REPLICATED_ANOMALY without independent replication in at least "
        f"{MIN_INDEPENDENT_LABS} distinct laboratories, each confirming the "
        f"residual survives the full ordinary-explanation battery. "
        f"Independent confirming labs present: {labs}. One run, or one lab, "
        f"is not independent replication.")


#: Reused from the governance core: there is no PHRYLL_DETECTED state.
refuse_phryll_detected = claims.refuse_phryll_detected


#: The refusals this module enforces, indexed for the red team.
RESIDUAL_REFUSALS = {
    "residual_to_new_physics": refuse_residual_as_new_physics,
    "unexplained_to_replicated_without_replication":
        refuse_unexplained_as_replicated_without_replication,
    "phryll_detected": refuse_phryll_detected,
}


# --- report ---------------------------------------------------------------

def residuals_report() -> dict:
    """The standing statement of what the classifier is and is not."""
    return {
        "what_this_is": (
            "the R15 residual classifier: given a residual, its error budget "
            "(combined uncertainty), the ordinary-explanation attack results "
            "(passed in; P11 is not imported) and any independent-replication "
            "evidence, it types the residual into exactly one claim class -- "
            "KNOWN_ORDINARY_EFFECT (within budget or a fired mild attack), "
            "MODEL_ERROR / CALIBRATION_ERROR / FIXTURE_EFFECT (a fired "
            "ordinary attack), UNEXPLAINED_INSTRUMENT_RESIDUAL (survives "
            "every attack, exceeds uncertainty, unreplicated -- the ceiling), "
            "or REPLICATED_ANOMALY (only with independent replication)"),
        "claim_classes_emitted": [
            claims.ClaimClass.KNOWN_ORDINARY_EFFECT.value,
            claims.ClaimClass.MODEL_ERROR.value,
            claims.ClaimClass.CALIBRATION_ERROR.value,
            claims.ClaimClass.FIXTURE_EFFECT.value,
            RESIDUAL_CEILING.value,
            claims.ClaimClass.REPLICATED_ANOMALY.value,
        ],
        "ordinary_causes": sorted(c.value for c in ORDINARY_CAUSE_CLASSES),
        "ordinary_cause_precedence": [c.value for c in ORDINARY_CAUSE_PRECEDENCE],
        "error_budget_components": list(CANONICAL_BUDGET_COMPONENTS),
        "residual_ceiling": RESIDUAL_CEILING.value,
        "min_independent_labs_for_replication": MIN_INDEPENDENT_LABS,
        "classifier_version": CLASSIFIER_VERSION,
        "refusals": list(RESIDUAL_REFUSALS),
        "has_phryll_detected_state": False,
        "claim_class": SOFTWARE_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "rules": [
            "a residual below combined uncertainty is not anomalous",
            "missing or invalid calibration forces CALIBRATION_ERROR "
            "(invalid) before any anomaly is considered",
            "an inadequate model forces MODEL_ERROR",
            "the ceiling for an unreplicated residual is "
            "UNEXPLAINED_INSTRUMENT_RESIDUAL",
            "one run or one lab cannot reach REPLICATED_ANOMALY",
            "an UNEXPLAINED_INSTRUMENT_RESIDUAL is never new physics and "
            "there is no PHRYLL_DETECTED state",
        ],
        "what_would_change_this": (
            "independent replication in at least "
            f"{MIN_INDEPENDENT_LABS} distinct laboratories, each confirming "
            "the residual survives the full ordinary-explanation battery -- "
            "none of which exists in this repository"),
        "what_this_does_not_say": (
            "It does not say any residual is a detection, a resonance, a new "
            "particle, a new energy, or new physics. The classifier operates "
            "no apparatus and measures nothing; it types inputs it is given. "
            "The strongest label an unreplicated residual can carry is "
            "UNEXPLAINED_INSTRUMENT_RESIDUAL. "
            "PHYSICAL_VALIDATION_NOT_CLAIMED."),
        "verdict": VERDICT,
    }


__all__ = [
    "VERDICT", "MEASURED_HERE", "PHYSICAL_VALIDATION",
    "SOFTWARE_CLAIM_CLASS", "RESIDUAL_CEILING", "CLASSIFIER_VERSION",
    "CANONICAL_BUDGET_COMPONENTS", "ORDINARY_CAUSE_CLASSES",
    "ORDINARY_CAUSE_PRECEDENCE", "MIN_INDEPENDENT_LABS",
    "ResidualError", "ErrorBudget", "OrdinaryAttackResult",
    "ReplicationRecord", "ReplicationEvidence", "Classification",
    "ResidualRecord", "ResidualClassifier",
    "refuse_residual_as_new_physics",
    "refuse_unexplained_as_replicated_without_replication",
    "refuse_phryll_detected", "RESIDUAL_REFUSALS", "residuals_report",
]
