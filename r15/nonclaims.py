"""P34 — negative results and non-claims register.

The explicit list of what R15 does NOT establish, each mapped to the code
refusal that enforces it. R15 builds measurement infrastructure; it advances
no physical claim. The strongest an unreplicated residual reaches is
``UNEXPLAINED_INSTRUMENT_RESIDUAL`` and there is no ``PHRYLL_DETECTED`` state.
"""

from __future__ import annotations

from dataclasses import dataclass

from r15 import claims as C


class NonClaimError(RuntimeError):
    """Raised if code tries to assert one of the registered non-claims."""


@dataclass(frozen=True)
class NonClaim:
    """A thing R15 does not establish, and the refusal that enforces it."""

    statement: str
    enforcing_refusal: str


#: The R15 non-claims. Each maps to a refusal in r15.claims (or a lane).
NON_CLAIMS = (
    NonClaim("new energy beyond measured input", "refuse_residual_as_new_physics"),
    NonClaim("Phyrll detection or a Phyrll carrier", "refuse_phryll_detected"),
    NonClaim("spacetime modification", "refuse_residual_as_new_physics"),
    NonClaim("a decoded destination / person-specific resonance",
             "refuse_source_as_measurement"),
    NonClaim("an unperformed physical result as measured",
             "refuse_synthetic_as_physical"),
    NonClaim("a model prediction as a measurement", "refuse_model_as_measurement"),
    NonClaim("noise or a sub-uncertainty feature as a resonance",
             "refuse_noise_as_resonance"),
    NonClaim("an unexplained instrument residual as new physics",
             "refuse_residual_as_new_physics"),
    NonClaim("a single-lab residual as a replicated anomaly",
             "refuse_residual_as_new_physics"),
)


def verify_refusals_exist() -> list[str]:
    """Every enforcing refusal named here must exist in r15.claims and raise."""
    missing = []
    for nc in NON_CLAIMS:
        fn = getattr(C, nc.enforcing_refusal, None)
        if fn is None:
            missing.append(nc.enforcing_refusal)
            continue
        try:
            fn()
        except Exception:
            continue
        else:
            missing.append(nc.enforcing_refusal + " (did not raise)")
    return missing


def refuse_positive_claim(statement: str) -> None:
    """Refuse to assert any registered non-claim as an established result."""
    raise NonClaimError(
        f"refused: {statement!r} is a registered R15 non-claim; R15 advances "
        f"no physical claim and has no PHRYLL_DETECTED state.")


def nonclaims_report() -> dict:
    return {
        "what_this_is": "the R15 negative-results and non-claims register",
        "non_claims": [nc.statement for nc in NON_CLAIMS],
        "claim_class": "SOFTWARE_IMPLEMENTED",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "residual_ceiling": C.ClaimClass.UNEXPLAINED_INSTRUMENT_RESIDUAL.value,
        "has_phryll_detected_state": False,
        "verdict": "R15_NON_CLAIMS_REGISTERED_NO_PHYSICAL_CLAIMS_ADVANCED",
        "what_this_does_not_say": (
            "It records what R15 does not establish; it does not establish "
            "any of them."),
    }
