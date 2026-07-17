"""Mechanism discrimination and pattern interpretation (Agent Q05)
and the unified reduced-model playground (Agent Q06).

Q05: before any observed effect (resonance shift, spatial pattern,
mode splitting, nonlinear response) may be attributed to a novel
mechanism, the ordinary alternatives must be evaluated and the
comparison's identifiability reported. Ambiguous stays INCONCLUSIVE.

Q06: a common schema for running the reduced models side by side.
Source-system labels are mandatory and immutable; the playground can
compare MATHEMATICS and is structurally unable to write evidence."""

from __future__ import annotations

# --- Q05: ordinary alternatives per observation class ---------------------

ORDINARY_ALTERNATIVES = {
    "resonance_shift": [
        ("fixture/remount", "remount scatter and preload drift; "
         "compare against the measured remount repeatability"),
        ("temperature", "TCF x observed delta-T"),
        ("mass loading", "adsorbed mass, handling residue"),
        ("drive level", "amplitude-dependent frequency pull"),
        ("aging/drift", "log-time drift since last measurement"),
    ],
    "spatial_pattern": [
        ("driven mode shape", "the pattern of the excited mode"),
        ("transfer function", "sensor/actuator placement artifact — "
         "the Q02 lesson: a pattern can be a property of the "
         "measurement, not the state"),
        ("redistribution", "internal rearrangement at constant "
         "total (Q02 classification)"),
    ],
    "mode_splitting": [
        ("symmetry breaking by mounting", "fixture-induced C_n "
         "breaking"),
        ("manufacturing anisotropy", "layup/rolling direction"),
        ("deliberate anisotropy", "designed bond asymmetry (Q03)"),
    ],
    "nonlinear_response": [
        ("drive clipping", "instrument saturation (R031)"),
        ("contact nonlinearity", "loose fixture rattling"),
        ("material nonlinearity", "amplitude-dependent modulus"),
    ],
}


def discrimination_tree(observation: str,
                        evaluations: dict) -> dict:
    """Given an observation class and {alternative: {'excluded': bool,
    'evidence': str}} for each ordinary alternative, return the honest
    verdict:

    - any ordinary alternative unevaluated -> INCONCLUSIVE;
    - any ordinary alternative not excluded -> ORDINARY_SUFFICIENT;
    - all excluded, with evidence strings -> CANDIDATE_NOVEL (which
      is a promotion to further work, never to a claim)."""
    if observation not in ORDINARY_ALTERNATIVES:
        raise KeyError(f"unknown observation class {observation}")
    alts = [a for a, _ in ORDINARY_ALTERNATIVES[observation]]
    missing = [a for a in alts if a not in evaluations]
    if missing:
        return {"verdict": "INCONCLUSIVE",
                "reason": f"unevaluated ordinary alternatives: "
                          f"{missing}",
                "rule": "an unevaluated alternative cannot be "
                        "excluded by silence"}
    not_excluded = [a for a in alts
                    if not evaluations[a].get("excluded")]
    if not_excluded:
        return {"verdict": "ORDINARY_SUFFICIENT",
                "sufficient_alternatives": not_excluded}
    weak = [a for a in alts
            if len(evaluations[a].get("evidence", "")) < 10]
    if weak:
        return {"verdict": "INCONCLUSIVE",
                "reason": f"exclusion asserted without evidence for "
                          f"{weak}"}
    return {"verdict": "CANDIDATE_NOVEL",
            "note": "all ordinary alternatives excluded WITH "
                    "evidence; this licenses further investigation, "
                    "not a claim (identifiability still applies)"}


def identifiability_report(effect_size, ordinary_bound,
                           measurement_uncertainty) -> dict:
    """Can the data distinguish novel from ordinary at all?"""
    margin = effect_size - ordinary_bound
    identifiable = margin > 2 * measurement_uncertainty
    return {"effect_size": effect_size,
            "ordinary_bound": ordinary_bound,
            "margin": margin,
            "measurement_uncertainty": measurement_uncertainty,
            "identifiable": bool(identifiable),
            "verdict_if_not": "INCONCLUSIVE — the margin is inside "
                              "the noise; collecting more data is "
                              "the only honest next step"}
