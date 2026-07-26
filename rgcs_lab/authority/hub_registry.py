"""WS09 — the nine-module public hub registry (authority layer).

Each module card declares what it demonstrates, what it does NOT
demonstrate, its I/O, owner, and how its live status is derived.
Status is NEVER hand-set here: :func:`module_status` reads the
module's machine-readable receipt from ``docs/program/receipts/`` and
returns RED ``NOT_EXECUTED`` when none exists — a module cannot be
GREEN merely because a UI rendered, and an agent cannot be GREEN by
assertion.

Cursor renders cards FROM this registry; it does not restate claims.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass

from rgcs_lab.common.status_schema import (
    MODULES,
    ClaimClass,
    ModuleStatus,
    validate_receipt,
)

RECEIPT_DIR = pathlib.Path("docs") / "program" / "receipts"


@dataclass(frozen=True)
class ModuleCard:
    """Static authority metadata for one hub module."""

    module: str
    title: str
    demonstrates: str
    does_not_demonstrate: str
    inputs: str
    outputs: str
    owner: str                    # codex | cursor | claude | mixed
    default_claim_class: tuple[str, ...]


CARDS: tuple[ModuleCard, ...] = (
    ModuleCard(
        "coordinate", "Coordinate",
        "exact, reversible F5|Q22|S3 structural packet decoding with "
        "golden vectors and a training-calibrated candidate projection",
        "that any packet independently decodes to a verified Earth "
        "location — 165876523=Stonehenge is a supplied training "
        "equality; the physical projection is underdetermined",
        "decimal packet word (30-bit family)",
        "structural trace JSON; candidate projection with assumptions",
        "claude",
        (ClaimClass.EXACT_ARITHMETIC.value,
         ClaimClass.TRAINING_EQUALITY.value,
         ClaimClass.UNDERDETERMINED.value)),
    ModuleCard(
        "golay", "Golay",
        "extended binary Golay [24,12,8] encoding with visible "
        "bit-flip injection and correction up to 3 errors",
        "that error-corrected transport implies any physical channel, "
        "carrier or source contact",
        "12-bit data words; error masks",
        "codewords, syndromes, corrected words, correction receipts",
        "codex",
        (ClaimClass.EXACT_ARITHMETIC.value,
         ClaimClass.IMPLEMENTED_SOFTWARE.value)),
    ModuleCard(
        "frames", "Frames",
        "ordered quaternion frame rotations (composition "
        "non-commutativity, gimbal-free attitude, exact round-trips)",
        "that quaternionic state representation implies physical "
        "spacetime frames, torsion, or navigation of a craft",
        "rotation sequences (axis-angle / quaternion)",
        "composed frames, round-trip residuals (exact where rational)",
        "codex",
        (ClaimClass.EXACT_ARITHMETIC.value,
         ClaimClass.IMPLEMENTED_SOFTWARE.value)),
    ModuleCard(
        "memory", "Memory",
        "a multiresolution provenance-memory graph benchmarked against "
        "equal-budget conventional retrieval baselines with ablations",
        "consciousness, self-awareness, or agent continuity — symbolic "
        "resonance is a ranking method, and style continuity is not "
        "self-awareness",
        "document corpus; queries; retrieval budget",
        "retrieval metrics, ablation reports, provenance chains",
        "codex",
        (ClaimClass.IMPLEMENTED_SOFTWARE.value,)),
    ModuleCard(
        "dual_pole", "Dual-Pole",
        "an enforced proposer/critic/reviser loop where the critic can "
        "BLOCK unsupported promotion, with a typed claim ledger",
        "that agreement between two agents is independent evidence, or "
        "that the agents are conscious",
        "research claims with evidence bindings",
        "approval/refusal receipts; blocked-promotion records",
        "claude",
        (ClaimClass.IMPLEMENTED_SOFTWARE.value,)),
    ModuleCard(
        "lattice", "Lattice",
        "a programmable 64-state coupled-mode lattice simulator with "
        "deterministic traces",
        "that a synthetic lattice is a physical spacetime lattice or "
        "that its dynamics demonstrate new physics",
        "lattice topology, coupling schedule, initial state",
        "state trajectories, spectra, deterministic trace files",
        "codex",
        (ClaimClass.IMPLEMENTED_SOFTWARE.value,
         ClaimClass.EXPLORATORY_MODEL.value)),
    ModuleCard(
        "metasurface", "Metasurface",
        "an energy-accounted reduced-order spoof-SPP metasurface "
        "simulator (dispersion, Q, counterrotating modes) tied to "
        "buildable geometry",
        "gravity modification, thrust, or excess energy — MHz "
        "spoof-SPPs are not optical plasmons; simulated gain is not "
        "excess energy; the ledger must close",
        "unit-cell geometry, drive parameters, epoch-free material data",
        "dispersion curves, loss/Q, closed energy ledgers, geometry "
        "exports",
        "codex",
        (ClaimClass.CONVENTIONAL_PHYSICS.value,
         ClaimClass.EXPLORATORY_MODEL.value)),
    ModuleCard(
        "predictions", "Predictions",
        "a tamper-evident registry of frozen prospective predictions "
        "with sham/null controls and outcome classification",
        "that a prediction is evidence before measurement, or that a "
        "hit establishes the proposed mechanism by itself",
        "prediction records, freeze commits, measurement imports",
        "frozen registry entries, outcome classifications, proof "
        "bundles",
        "claude",
        (ClaimClass.PROSPECTIVE_PREDICTION.value,)),
    ModuleCard(
        "proofs", "Proofs",
        "the receipt index: every module's machine-readable receipts, "
        "test results and claim classes in one inspectable place",
        "that a receipt's existence validates a physical claim — "
        "receipts record what ran and what it is allowed to mean",
        "module receipts",
        "validated receipt index; program verdict",
        "cursor",
        (ClaimClass.IMPLEMENTED_SOFTWARE.value,)),
)

assert tuple(c.module for c in CARDS) == MODULES, "hub must show all nine"

_BY_MODULE = {c.module: c for c in CARDS}


def card(module: str) -> ModuleCard:
    try:
        return _BY_MODULE[module]
    except KeyError:
        raise KeyError(f"unknown module {module!r}; hub modules: "
                       f"{MODULES}") from None


def module_status(module: str,
                  repo_root: pathlib.Path | str = ".") -> ModuleStatus:
    """Live status derived from the module's receipt — or honest RED.

    No receipt file -> RED NOT_EXECUTED. A receipt that fails schema
    validation -> RED INVALID_RECEIPT (loud, not hidden). Otherwise the
    receipt's own status and claim classes are surfaced verbatim.
    """
    c = card(module)
    path = pathlib.Path(repo_root) / RECEIPT_DIR / f"{module}.json"
    if not path.exists():
        return ModuleStatus(
            module=module, status="RED",
            claim_class=(ClaimClass.UNDERDETERMINED.value,),
            result={"state": "NOT_EXECUTED",
                    "note": f"no receipt at {path.as_posix()}; a module "
                            f"is never GREEN by assertion or UI render"},
        )
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
        validate_receipt(receipt)
    except Exception as exc:
        return ModuleStatus(
            module=module, status="RED",
            claim_class=(ClaimClass.UNDERDETERMINED.value,),
            result={"state": "INVALID_RECEIPT", "error": str(exc)})
    return ModuleStatus(
        module=module, status=receipt["status"],
        claim_class=tuple(receipt["claim_class"]),
        result=dict(receipt["result"]),
        warnings=tuple(receipt.get("warnings", ())),
        receipt={"path": path.as_posix(),
                 "source_commit": receipt["source_commit"]})


def hub_index(repo_root: pathlib.Path | str = ".") -> dict:
    """The full nine-card index with live statuses — what Cursor renders."""
    entries = []
    for c in CARDS:
        s = module_status(c.module, repo_root)
        entries.append({
            "module": c.module, "title": c.title,
            "demonstrates": c.demonstrates,
            "does_not_demonstrate": c.does_not_demonstrate,
            "inputs": c.inputs, "outputs": c.outputs,
            "owner": c.owner,
            "status": s.status, "badge": s.badge_text(),
            "claim_class": list(s.claim_class),
            "state": s.result.get("state", "EXECUTED"),
        })
    greens = sum(1 for e in entries if e["status"] == "GREEN")
    return {"product": "RGCS Recursive Infrastructure Lab",
            "headline": "Recursive infrastructure you can inspect, "
                        "run, and falsify.",
            "modules": entries,
            "green_count": greens,
            "module_count": len(entries)}
