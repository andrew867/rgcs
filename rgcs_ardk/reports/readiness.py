"""Evidence-driven fabrication readiness evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from rgcs_ardk.bench import BenchVerdict, evaluate_bench_result


class FabricationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REFUSED = "REFUSED"


@dataclass(frozen=True)
class FabricationEvidence:
    authority_valid: bool
    seed_used: bool
    board_a_generated: bool
    board_b_generated: bool
    boards_separate: bool
    deterministic_nets: bool
    geometry_valid: bool
    publication_hold: bool
    manufacturer_stackup: str | None = None
    drc_board_a: bool | None = None
    drc_board_b: bool | None = None
    fabrication_hashes: Mapping[str, str] = field(default_factory=dict)
    bom_reviewed: bool | None = None
    assembly_drawing_reviewed: bool | None = None
    pick_place_reviewed_if_populated: bool | None = None
    safety_reviewed: bool | None = None
    board_a_calibrated: bool | None = None
    board_b_dummy_load_complete: bool | None = None
    board_b_symmetric_control_complete: bool | None = None


@dataclass(frozen=True)
class FabricationReport:
    status: FabricationStatus
    blockers: tuple[str, ...]
    failures: tuple[str, ...]
    publication_hold: bool


def evaluate_fabrication_readiness(
    evidence: FabricationEvidence,
    bench_result: Mapping[str, Any] | None = None,
) -> FabricationReport:
    """Return PASS only when every documentary and physical gate exists."""
    blockers: list[str] = []
    failures: list[str] = []
    if not evidence.authority_valid:
        blockers.append("R10.73 authority is absent, stale, or invalid")
    if evidence.seed_used:
        blockers.append("a seed table was selected")
    if not evidence.board_a_generated or not evidence.board_b_generated:
        blockers.append("both board variants have not been generated")
    if not evidence.boards_separate:
        blockers.append("Board A and Board B are not separate")
    if not evidence.deterministic_nets:
        blockers.append("net registry is not deterministic")
    if not evidence.geometry_valid:
        blockers.append("annular geometry locks are not satisfied")
    if not evidence.publication_hold:
        blockers.append("PUBLICATION_HOLD is not asserted")
    if not evidence.manufacturer_stackup:
        blockers.append("manufacturer stackup is not approved")
    for label, value in (
        ("Board A DRC", evidence.drc_board_a),
        ("Board B DRC", evidence.drc_board_b),
    ):
        if value is None:
            blockers.append(f"{label} evidence is missing")
        elif value is False:
            failures.append(f"{label} failed")
    if not evidence.fabrication_hashes:
        blockers.append("fabrication outputs are not hashed")
    for label, value in (
        ("BOM review", evidence.bom_reviewed),
        ("assembly drawing review", evidence.assembly_drawing_reviewed),
        ("pick/place review when populated", evidence.pick_place_reviewed_if_populated),
        ("safety review", evidence.safety_reviewed),
        ("Board A calibration", evidence.board_a_calibrated),
        ("Board B dummy-load run", evidence.board_b_dummy_load_complete),
        ("Board B all-active symmetric run", evidence.board_b_symmetric_control_complete),
    ):
        if value is None:
            blockers.append(f"{label} evidence is missing")
        elif value is False:
            failures.append(f"{label} failed")
    if bench_result is None:
        blockers.append("complete bench receipt is missing")
    else:
        verdict = evaluate_bench_result(bench_result)
        if verdict is not BenchVerdict.PASS:
            failures.append("complete bench receipt did not pass")
    status = (
        FabricationStatus.FAIL
        if failures
        else FabricationStatus.REFUSED
        if blockers
        else FabricationStatus.PASS
    )
    return FabricationReport(status, tuple(blockers), tuple(failures), evidence.publication_hold)


def current_scaffold_evidence() -> FabricationEvidence:
    """Evidence truthfully available from repository generation alone."""
    return FabricationEvidence(
        authority_valid=True,
        seed_used=False,
        board_a_generated=True,
        board_b_generated=True,
        boards_separate=True,
        deterministic_nets=True,
        geometry_valid=True,
        publication_hold=True,
    )


def render_report(report: FabricationReport) -> str:
    lines = [
        "# Manufacturing Readiness Report",
        "",
        f"**Fabrication readiness:** `{report.status.value}`",
        f"**Publication hold:** `{str(report.publication_hold).lower()}`",
        "",
    ]
    if report.blockers:
        lines.extend(("## Refusal blockers", ""))
        lines.extend(f"- {blocker}." for blocker in report.blockers)
        lines.append("")
    if report.failures:
        lines.extend(("## Failed evidence", ""))
        lines.extend(f"- {failure}." for failure in report.failures)
        lines.append("")
    lines.extend(
        (
            "## Boundary",
            "",
            "The repository supplies a deterministic development scaffold. It does not supply",
            "manufacturer approval, local DRC evidence, fabrication exports, or physical bench receipts.",
            "",
        )
    )
    return "\n".join(lines)
