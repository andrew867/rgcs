"""UI-level scientific gates (binding requirements from Agent 04/06 handoffs).

These gates decide what *workflows the UI enables*; they never alter data.

* Coherence-claim workflows require post_drive_ratio >= 2.5 AND n_runs >= 100.
* human_loading manifests require the ethics block (ethics_review_ref and
  no_energized_contact_confirmed = true).
* Unknown major schema_version is refused (see services.schemas).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

MIN_POST_DRIVE_RATIO = 2.5   # KOS-12: coverage >= 2.5x past drive-off
MIN_N_RUNS_FOR_CLAIM = 100   # pre-registered ensemble size gate


@dataclass(frozen=True)
class GateResult:
    ok: bool
    reasons: tuple[str, ...] = field(default_factory=tuple)

    def summary(self) -> str:
        return "PASS" if self.ok else "BLOCKED: " + "; ".join(self.reasons)


def coherence_claim_gate(manifest: dict[str, Any]) -> GateResult:
    """Enable coherence-claim workflows only when the acquisition supports
    them. Analysis itself stays available; only *claim* workflows gate."""
    reasons: list[str] = []
    acq = manifest.get("acquisition", {}) or {}
    n_runs = acq.get("n_runs")
    if n_runs is None:
        reasons.append("acquisition.n_runs missing")
    elif n_runs < MIN_N_RUNS_FOR_CLAIM:
        reasons.append(
            f"n_runs = {n_runs} < {MIN_N_RUNS_FOR_CLAIM} (ensemble too small "
            f"for a coherence claim; exploratory analysis only)")
    ratio = (acq.get("post_drive") or {}).get("post_drive_ratio")
    if ratio is None:
        reasons.append("acquisition.post_drive.post_drive_ratio missing")
    elif ratio < MIN_POST_DRIVE_RATIO:
        reasons.append(
            f"post_drive_ratio = {ratio} < {MIN_POST_DRIVE_RATIO} "
            f"(insufficient post-drive coverage, KOS-12)")
    return GateResult(not reasons, tuple(reasons))


def ethics_gate(manifest: dict[str, Any]) -> GateResult:
    """human_loading runs are excluded without the ethics block."""
    if manifest.get("protocol_branch") != "human_loading":
        return GateResult(True)
    hl = manifest.get("human_loading") or {}
    reasons: list[str] = []
    if not hl.get("ethics_review_ref"):
        reasons.append("human_loading.ethics_review_ref missing (hard gate: "
                       "runs without ethics sign-off are excluded)")
    if hl.get("no_energized_contact_confirmed") is not True:
        reasons.append("human_loading.no_energized_contact_confirmed must be "
                       "true (no energized contact during human loading)")
    return GateResult(not reasons, tuple(reasons))


def all_gates(manifest: dict[str, Any]) -> dict[str, GateResult]:
    return {
        "coherence_claim": coherence_claim_gate(manifest),
        "ethics": ethics_gate(manifest),
    }
