"""Dual-pole research agent reference — typed attack state machine."""

from __future__ import annotations

from typing import Any

ATTACK_FAMILIES = (
    "unsupported_factual_assertion",
    "circular_training_validation",
    "dimensional_error",
    "energy_or_momentum_violation",
    "codec_projection_conflation",
    "data_leakage",
    "stale_authority",
    "hidden_parameter_tuning",
    "alternative_ordinary_explanation",
    "citation_mismatch",
    "irreproducible_result",
)

STATES = (
    "INTAKE",
    "DECOMPOSE",
    "RETRIEVE",
    "PROPOSE",
    "EVIDENCE_BIND",
    "ATTACK",
    "BLOCK",
    "REVISE",
    "REATTACK",
    "ACCEPT_YELLOW",
    "ACCEPT_GREEN",
    "REJECT",
    "RECEIPT",
)


def audit_claim(claim: dict[str, Any]) -> dict[str, Any]:
    """Run a deterministic critic pass over a claim object."""
    path = ["INTAKE", "DECOMPOSE", "RETRIEVE", "PROPOSE", "EVIDENCE_BIND", "ATTACK"]
    attacks: list[dict[str, str]] = []
    text = " ".join(str(v) for v in claim.values()).lower()
    statement = str(claim.get("statement", claim.get("hypothesis", "")))

    if "anti-gravity" in text or "antigravity" in text or "torsion reson" in text:
        attacks.append({
            "family": "unsupported_factual_assertion",
            "detail": "promotes an unestablished gravity/torsion claim",
        })
    if "stonehenge" in text and "validate" in text:
        attacks.append({
            "family": "circular_training_validation",
            "detail": "training equality cannot validate the projection",
        })
    if "morton" in text and ("latitude" in text or "longitude" in text):
        attacks.append({
            "family": "codec_projection_conflation",
            "detail": "path indices conflated with geographic coordinates",
        })
    if "vacuum energy" in text or "free energy" in text:
        attacks.append({
            "family": "energy_or_momentum_violation",
            "detail": "energy accounting missing or violated in wording",
        })
    if not claim.get("evidence") and not claim.get("controls"):
        attacks.append({
            "family": "irreproducible_result",
            "detail": "no evidence objects or controls supplied",
        })

    if attacks:
        terminal = "BLOCK"
        path.extend(["BLOCK", "REJECT", "RECEIPT"])
        status = "YELLOW" if claim.get("allow_yellow") else "RED"
        decision = "REJECT" if status == "RED" else "ACCEPT_YELLOW"
        if decision == "ACCEPT_YELLOW":
            path[-2] = "ACCEPT_YELLOW"
            terminal = "ACCEPT_YELLOW"
    else:
        # No attack fired — still YELLOW unless claim class is exact arithmetic.
        classes = claim.get("claim_class") or []
        if "EXACT_ARITHMETIC" in classes and "UNDERDETERMINED" not in classes:
            terminal = "ACCEPT_GREEN"
            status = "GREEN"
            decision = "ACCEPT_GREEN"
        else:
            terminal = "ACCEPT_YELLOW"
            status = "YELLOW"
            decision = "ACCEPT_YELLOW"
        path.extend([terminal, "RECEIPT"])

    return {
        "state_path": path,
        "terminal_state": terminal,
        "decision": decision,
        "status": status,
        "attacks": attacks,
        "attack_families_available": list(ATTACK_FAMILIES),
        "statement": statement,
        "critic_bypassed": False,
    }
