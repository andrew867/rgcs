"""Dual-pole proposer/critic workflow core."""

from __future__ import annotations

import json
from pathlib import Path

from .receipts import receipt


ATTACKS = {
    "unsupported factual assertion": ["proves", "confirmed", "validated external"],
    "energy or momentum violation": ["excess energy", "energy from nowhere", "unlimited usable power"],
    "codec/projection conflation": ["hierarchical path indices are coordinates", "packet proves location"],
    "data leakage": ["private operator", "unpublished location corpus"],
    "ordinary explanation missing": ["gravity coupling", "anti-gravity", "spacetime drive"],
    "citation mismatch": ["patent proves", "ai-generated paper proves"],
}


def audit_claim(payload: dict[str, object]) -> dict[str, object]:
    proposal = str(payload.get("proposal", ""))
    evidence = payload.get("evidence", [])
    claim_class = payload.get("claim_class", [])
    waiver = payload.get("operator_waiver")
    lower = proposal.lower()
    findings = []
    for family, needles in ATTACKS.items():
        for needle in needles:
            if needle in lower:
                findings.append({"attack_family": family,
                                 "matched": needle,
                                 "severity": "BLOCK"})
    if "gravity" in lower and "electromagnetic" in lower:
        findings.append({"attack_family": "ordinary explanation missing",
                         "matched": "gravity inferred from electromagnetic simulation",
                         "severity": "BLOCK"})
    if "resonance gain" in lower and "pump" not in lower and "drive" not in lower:
        findings.append({"attack_family": "energy or momentum violation",
                         "matched": "resonance gain without pump/drive attribution",
                         "severity": "BLOCK"})
    has_evidence = isinstance(evidence, list) and len(evidence) > 0
    blocked = bool(findings) or not has_evidence
    if not has_evidence:
        findings.append({"attack_family": "unsupported factual assertion",
                         "matched": "no evidence objects",
                         "severity": "BLOCK"})
    if blocked and waiver:
        verdict = "ACCEPT_YELLOW"
        waiver_recorded = True
    elif blocked:
        verdict = "BLOCK"
        waiver_recorded = False
    else:
        verdict = "ACCEPT_GREEN" if "EXACT" in claim_class else "ACCEPT_YELLOW"
        waiver_recorded = False
    return {
        "state_path": ["INTAKE", "DECOMPOSE", "RETRIEVE", "PROPOSE",
                       "EVIDENCE_BIND", "ATTACK",
                       verdict if verdict == "BLOCK" else "REATTACK",
                       verdict, "RECEIPT"],
        "proposal": proposal,
        "claim_class": claim_class,
        "evidence_count": len(evidence) if isinstance(evidence, list) else 0,
        "findings": findings,
        "operator_waiver_recorded": waiver_recorded,
        "verdict": verdict,
    }


def audit_file(path: str | Path) -> dict[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    result = audit_claim(payload)
    status = "GREEN" if result["verdict"] == "ACCEPT_GREEN" else "YELLOW"
    if result["verdict"] == "BLOCK":
        status = "RED"
    return receipt(
        "dual-pole", status, ["ADVERSARIAL_RESEARCH_LOOP"],
        {"claim_file": str(path)},
        [{"name": "deterministic_dual_pole_state_machine",
          "critic_override_rule": "block requires new evidence or typed operator waiver"}],
        result,
        ["tests/rgcs_lab/test_memory_dual.py"],
        warnings=["Critic blocks cannot be overridden without new evidence or a recorded operator waiver."],
    )

