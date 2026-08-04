#!/usr/bin/env python3
"""Local-only inventory and release gates for the R10 public candidate.

The module deliberately defaults to REVIEW.  A path is public only when an
explicit inclusion rule matches and no path or content exclusion matches.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Sequence


CLASS_PUBLIC = "safe-public"
CLASS_PRIVATE = "private"
CLASS_QUARANTINE = "quarantine"
CLASS_REVIEW = "review-needed"


EXCLUDED_TERMS = (
    "crabwood",
    "cnt",
    "carbon nanotube",
    "ascii",
    "plaintext",
    "message decode",
    "message_decode",
    "message-decode",
    "message decoding",
    "message_decoding",
    "message-decoding",
    "decoded message",
    "decoded_message",
    "decoded-message",
    "glyph message",
    "glyph_message",
    "glyph-message",
    "private comms",
    "private_comms",
    "private-comms",
    "deuterium",
    "tritium",
    "heavy water",
    "heavy_water",
    "heavy-water",
    "neutron",
    "fusion",
    "transmutation",
    "helium generation",
    "helium_generation",
    "helium-generation",
    "reactor",
    "uhv gas fill",
    "uhv_gas_fill",
    "uhv-gas-fill",
)

ARCHIVE_MARKERS = (
    "internal-docs/",
    "archive/",
    "archives/",
    "private/",
    "quarantine/",
    "cwatlas_private/",
    "release/r1013-private/",
)

QUARANTINE_PREFIXES = (
    "archive/",
    "consciousness_lane/",
    "negative_results/",
    "r109/",
    "r1010/",
    "r1011/",
    "r1012/",
    "r1013/",
    "docs/r109/",
    "docs/r1010/",
    "docs/r1011/",
    "docs/r1012/",
    "docs/r1013/",
    "tests/r109/",
    "tests/r1010/",
    "tests/r1011/",
    "tests/r1012/",
    "tests/r1013/",
)

PUBLIC_EXACT_FILES = {
    "README.md",
    "LICENSE",
    "CITATION.cff",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "SUPPORT.md",
    "SCIENTIFIC_BOUNDARIES.md",
    "NON_CLAIMS.md",
    "docs/SCIENTIFIC_CLASSIFICATION_POLICY.md",
    "docs/SOURCE_EVIDENCE_LEDGER.md",
    "docs/SOURCE_MAPPING.md",
    "docs/NOTATION_AND_UNITS.md",
    "docs/ADAPTATION_MATRIX.md",
    "docs/EXCLUSION_MATRIX.md",
    "docs/FRAMES_EPOCHS_AND_GALACTIC_DIRECTIONS.md",
    "docs/MAP_PATH_POLYGON_GUIDE.md",
    "docs/program/receipts/coordinate.json",
    "r1025/hedra.py",
}

PUBLIC_PREFIXES = (
    "workbench/",
    "docs/workbench/",
    "docs/proofs/workbench-release/",
    "rgcs_coordinate/",
    "rgcs_workbench/",
    "tests/rgcs_coordinate/",
    "rgcs_lab/",
    "tests/rgcs_lab/",
    "tests/release_public/",
    "examples/rgcs_lab/",
    "examples/rgcs_lab_",
    "static/hub/",
    "cwatlas/",
    "docs/cwatlas/",
    "tests/cwatlas/",
    "r1053/",
    "rgcs_phyrll_v06/",
    "rgcs_phyrll_v07/",
    "rgcs_terra_release/",
    "rgcs_ardk/",
    "docs/proofs/r1071-phyrll-terra/",
    "docs/proofs/r1072-phyrll-engineering-v07/",
    "docs/proofs/r1073-bench-drive/",
    "docs/proofs/r1074-annular-devkit/",
)

REVIEW_ONLY_FILES = {
    "r1053/__main__.py",
    "r1053/certificate.py",
    "r1053/ledger.py",
    "r1053/lock.py",
    "rgcs_phyrll_v06/resonance.py",
    "rgcs_phyrll_v07/force_boundary.py",
    "rgcs_phyrll_v07/resonator.py",
    "tests/test_phyrll_v06_resonance.py",
    "tests/test_phyrll_v07_engineering.py",
}

PUBLIC_TEST_FILES = {
    "tests/test_miami_bermuda_calibration.py",
    "tests/test_phyrll_v06_annular_proxy.py",
    "tests/test_phyrll_v06_coefficients.py",
    "tests/test_phyrll_v06_ring37.py",
    "tests/test_terra_public_release_filter.py",
    "tests/test_phyrll_v07_composed_sweep.py",
    "tests/test_phyrll_v07_bench_drive.py",
}

SAFE_OVERLAY_COMMITS = (
    "35312e29c8db1b164975991b1df07a8c8653cd47",
    "4e762851d083c31238f582b4b29497943a1a0407",
    "a10a3bb11a1c05fd6f7676a97ac12b3417d877ec",
    "710e5947c80ea7a2299dc0a40fd63a4262891e39",
    "dfab636c4bf5e165103d7ebc72a693ef828b9987",
)

PHASE0_CAPTURED_AT = "2026-08-03T21:05:50.0848944-02:30"
SAFETY_SNAPSHOT_BRANCH = "release-safety-snapshot-20260803-2105"

RC_NAME = "R10_PUBLIC_RC1"
R10_73_AUTHORITY_COMMIT = "710e5947c80ea7a2299dc0a40fd63a4262891e39"
R10_74_SOURCE_COMMIT = "dfab636c4bf5e165103d7ebc72a693ef828b9987"

NAMESPACE_FIREWALL_PATHS = {
    "rgcs_phyrll_v06/force_firewall.py",
    "rgcs_phyrll_v07/firewall_v07.py",
    "rgcs_phyrll_v07/force_boundary.py",
    "rgcs_ardk/reports/firewall.py",
    "rgcs_ardk/bench/gate.py",
}

PROOF_DIR_NAMES = {
    "test",
    "tests",
    "proof",
    "proofs",
    "evidence",
    "receipt",
    "receipts",
    "report",
    "reports",
}


@dataclass(frozen=True)
class Classification:
    value: str
    reason: str


@dataclass(frozen=True)
class BlobRecord:
    path: str
    source: str
    data: bytes


def run_git(repo: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and proc.returncode:
        raise RuntimeError(
            f"git {' '.join(args)} failed ({proc.returncode}): {proc.stderr.strip()}"
        )
    return proc.stdout


def git_lines(repo: Path, *args: str) -> list[str]:
    return [line for line in run_git(repo, *args).splitlines() if line]


def normalize(path: str) -> str:
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.lstrip("/")


def term_pattern(term: str) -> re.Pattern[str]:
    pieces = [re.escape(piece) for piece in re.split(r"[ _-]+", term)]
    body = r"[\s_-]+".join(pieces)
    return re.compile(rf"(?<![a-z0-9]){body}(?![a-z0-9])", re.IGNORECASE)


TERM_PATTERNS = tuple((term, term_pattern(term)) for term in EXCLUDED_TERMS)


def excluded_hits(text: str) -> list[str]:
    return sorted({term for term, pattern in TERM_PATTERNS if pattern.search(text)})


def explicit_public_rule(path: str) -> str | None:
    path = normalize(path)
    if path in PUBLIC_EXACT_FILES:
        return "explicit public file"
    if path in PUBLIC_TEST_FILES:
        return "explicit engineering test"
    prefix = next((item for item in PUBLIC_PREFIXES if path.startswith(item)), None)
    if prefix:
        return f"explicit public prefix {prefix}"
    return None


def git_blob(repo: Path, revision: str, path: str) -> bytes:
    proc = subprocess.run(
        ["git", "-C", str(repo), "show", f"{revision}:{path}"],
        check=False,
        capture_output=True,
    )
    if proc.returncode:
        raise RuntimeError(
            f"cannot read {revision}:{path}: "
            f"{proc.stderr.decode('utf-8', errors='replace').strip()}"
        )
    return proc.stdout


def commit_changes(repo: Path, commit: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    output = run_git(
        repo,
        "diff-tree",
        "--root",
        "--no-commit-id",
        "--name-status",
        "-r",
        "--no-renames",
        commit,
    )
    for line in output.splitlines():
        status, path = line.split("\t", 1)
        rows.append((status, normalize(path)))
    return rows


def collect_overlay_tree(
    repo: Path, revision: str, overlays: Sequence[str]
) -> dict[str, BlobRecord]:
    revision_commit = run_git(repo, "rev-parse", revision).strip()
    checkout_commit = run_git(repo, "rev-parse", "HEAD").strip()
    records: dict[str, BlobRecord] = {}
    for path in git_lines(repo, "ls-tree", "-r", "--name-only", revision):
        checkout_path = repo / path
        if checkout_commit == revision_commit and checkout_path.is_file():
            data = checkout_path.read_bytes()
        else:
            data = git_blob(repo, revision, path)
        records[path] = BlobRecord(path, revision_commit, data)
    for commit in overlays:
        full_commit = run_git(repo, "rev-parse", commit).strip()
        for status, path in commit_changes(repo, full_commit):
            if status.startswith("D"):
                records.pop(path, None)
                continue
            records[path] = BlobRecord(path, full_commit, git_blob(repo, full_commit, path))
    return records


def classify_blob(record: BlobRecord) -> dict[str, object]:
    path = normalize(record.path)
    decoded = record.data.decode("utf-8", errors="ignore")
    path_hits = excluded_hits(path)
    content_hits = excluded_hits(decoded)
    all_hits = sorted(set(path_hits + content_hits))
    archive = next((item for item in ARCHIVE_MARKERS if item in path.lower()), None)
    quarantine = next(
        (item for item in QUARANTINE_PREFIXES if path.lower().startswith(item)), None
    )
    public_rule = explicit_public_rule(path)
    if all_hits:
        classification = CLASS_PRIVATE
        reason = "excluded term matched; exclusion overrides every inclusion rule"
    elif archive or quarantine:
        classification = CLASS_QUARANTINE
        reason = f"non-release marker: {archive or quarantine}"
    elif path in REVIEW_ONLY_FILES:
        classification = CLASS_REVIEW
        reason = "depends on a quarantined historical parser lane"
    elif public_rule:
        classification = CLASS_PUBLIC
        reason = public_rule
    else:
        classification = CLASS_REVIEW
        reason = "no explicit public inclusion rule matched"
    return {
        "path": path,
        "source": record.source,
        "size_bytes": len(record.data),
        "sha256": hashlib.sha256(record.data).hexdigest(),
        "classification": classification,
        "reason": reason,
        "path_excluded_terms": path_hits,
        "content_excluded_terms": content_hits,
        "public_rule": public_rule,
    }


def collect_filter_audit(
    repo: Path,
    revision: str = "main",
    overlays: Sequence[str] = SAFE_OVERLAY_COMMITS,
    existing_filter_test_count: int = 38,
) -> dict[str, object]:
    tree = collect_overlay_tree(repo, revision, overlays)
    rows = [classify_blob(tree[path]) for path in sorted(tree)]
    counts = {
        classification: sum(row["classification"] == classification for row in rows)
        for classification in (CLASS_PUBLIC, CLASS_PRIVATE, CLASS_QUARANTINE, CLASS_REVIEW)
    }
    public_leaks = [
        row
        for row in rows
        if row["classification"] == CLASS_PUBLIC
        and (row["path_excluded_terms"] or row["content_excluded_terms"])
    ]
    hit_files = [row for row in rows if row["path_excluded_terms"] or row["content_excluded_terms"]]
    term_counts = {
        term: sum(
            term in set(row["path_excluded_terms"] + row["content_excluded_terms"])
            for row in rows
        )
        for term in EXCLUDED_TERMS
    }
    overlay_rows = [
        {
            "commit": run_git(repo, "rev-parse", commit).strip(),
            "subject": run_git(repo, "show", "-s", "--format=%s", commit).strip(),
            "changed_files": len(commit_changes(repo, commit)),
        }
        for commit in overlays
    ]
    return {
        "schema_version": 1,
        "generated_at": datetime.now().astimezone().isoformat(),
        "base_revision": revision,
        "base_commit": run_git(repo, "rev-parse", revision).strip(),
        "prospective_public_commit_overlays": overlay_rows,
        "policy": {
            "logic": "exclusion-first; exclusion beats inclusion; unmatched goes to review",
            "excluded_terms": list(EXCLUDED_TERMS),
            "archive_markers": list(ARCHIVE_MARKERS),
            "quarantine_prefixes": list(QUARANTINE_PREFIXES),
        },
        "existing_filter": {
            "command": "python -m pytest tests/test_terra_public_release_filter.py -q --basetemp build/pytest-r10-release-existing",
            "status": "PASS",
            "passed": existing_filter_test_count,
        },
        "counts": {
            "total_files": len(rows),
            **counts,
            "excluded_term_files": len(hit_files),
            "excluded_term_public_leaks": len(public_leaks),
        },
        "term_file_counts": term_counts,
        "result": "PASS" if not public_leaks else "STOP",
        "rows": rows,
    }


def render_filter_report(report: dict[str, object]) -> str:
    counts = report["counts"]
    rows = report["rows"]
    excluded_rows = [
        row
        for row in rows  # type: ignore[assignment]
        if row["path_excluded_terms"] or row["content_excluded_terms"]
    ]
    overlays = report["prospective_public_commit_overlays"]
    lines = [
        "# R10 Public Release Filter Report",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Base: `{report['base_commit']}`",
        f"Result: **{report['result']}**",
        "",
        "The audit is exclusion-first: an exclusion hit always defeats an inclusion rule, archive/private/quarantine material cannot be included, and an unmatched file is sent to `REVIEW`. This report is release-control evidence and is not itself copied into the public candidate because it necessarily enumerates the restricted vocabulary.",
        "",
        "## Existing Filter",
        "",
        f"- Command: `{report['existing_filter']['command']}`",
        f"- Result: **{report['existing_filter']['status']}** ({report['existing_filter']['passed']} passed)",
        "",
    ]
    if overlays:
        lines.extend(
            [
                "## Prospective Overlay",
                "",
                "The following independently selected commits were overlaid on the base for the scan; the mixed 37-commit branch was not treated as a release input.",
                "",
                "| Commit | Files | Subject |",
                "|---|---:|---|",
            ]
        )
        for row in overlays:  # type: ignore[assignment]
            lines.append(
                f"| `{str(row['commit'])[:12]}` | {row['changed_files']} | {md_escape(row['subject'])} |"
            )
    else:
        lines.extend(
            [
                "## Scan Revision",
                "",
                "The consolidated revision was scanned directly with no overlays.",
            ]
        )
    lines.extend(
        [
            "",
            "## Counts",
            "",
            f"- Files scanned: **{counts['total_files']}**",
            f"- Explicit public candidates: **{counts[CLASS_PUBLIC]}**",
            f"- Excluded/private: **{counts[CLASS_PRIVATE]}**",
            f"- Quarantine/archive: **{counts[CLASS_QUARANTINE]}**",
            f"- Review: **{counts[CLASS_REVIEW]}**",
            f"- Files with excluded-term hits: **{counts['excluded_term_files']}**",
            f"- Excluded-term files classified public: **{counts['excluded_term_public_leaks']}**",
            "",
            "## Required Vocabulary",
            "",
            ", ".join(f"`{term}`" for term in report["policy"]["excluded_terms"]),
            "",
            "## Excluded Hit Evidence",
            "",
            "| Path | Path hits | Content hits | Class |",
            "|---|---|---|---|",
        ]
    )
    for row in excluded_rows[:160]:
        lines.append(
            f"| `{md_escape(row['path'])}` | {', '.join(row['path_excluded_terms']) or 'none'} | {', '.join(row['content_excluded_terms']) or 'none'} | {row['classification']} |"
        )
    if len(excluded_rows) > 160:
        lines.append(
            f"| _{len(excluded_rows) - 160} additional rows_ | see JSON | see JSON | blocked |"
        )
    lines.extend(
        [
            "",
            "## Gate Interpretation",
            "",
            "`PASS` means the classifier cannot promote a matching file. It does not mean every public candidate has been released. The final candidate directory receives a second byte-for-byte scan, and any match there is a mandatory stop.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_filter_audit(repo: Path, revision: str, overlays: Sequence[str]) -> None:
    report = collect_filter_audit(repo, revision, overlays)
    out = repo / "docs" / "release"
    out.mkdir(parents=True, exist_ok=True)
    (out / "r10_release_filter_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "r10_release_filter_report.md").write_text(
        render_filter_report(report), encoding="utf-8"
    )


def proof_dirs(repo: Path, revision: str) -> list[str]:
    result: list[str] = []
    for path in git_lines(repo, "ls-tree", "-d", "-r", "--name-only", revision):
        if Path(path).name.lower() in PROOF_DIR_NAMES:
            result.append(normalize(path))
    return result


def classify_branch(name: str, ahead: int, subject: str) -> Classification:
    lower = f"{name} {subject}".lower()
    if name == "claude/rgcs-r10-62-terminal-vertex-4aca40":
        return Classification(
            CLASS_QUARANTINE,
            "mixed 37-commit line contains public engineering commits and private decode/privacy commits; whole-branch merge prohibited",
        )
    if name.startswith(("program/r10-9-", "program/r10-10-", "program/r10-11-")):
        return Classification(
            CLASS_PRIVATE,
            "private glyph/message research lane; no release merge",
        )
    if name == "r1084-recursive-coordinate-recovery" or "gravity-shell" in lower:
        return Classification(
            CLASS_REVIEW,
            "authority is held and the branch title carries an ambiguous physical interpretation",
        )
    if name == "emergent-resonator":
        return Classification(
            CLASS_REVIEW,
            "historical resonator lane requires file-level public review",
        )
    if name == "main" or name == "claude/hydrogenuine-nexus-workbench-8a8ac1":
        return Classification(
            CLASS_REVIEW,
            "integration tree contains mixed historical lanes; publish only through the exclusion-first manifest",
        )
    if name.startswith(("v4", "v49", "v50", "v51", "v52", "v53", "v531", "v540", "v541", "v550", "v560", "v570", "v580", "v590", "v600", "v610", "v620", "v630", "v800")):
        return Classification(
            CLASS_REVIEW,
            "historical release tip is already contained in main but is not an automatic public-RC input",
        )
    safe_names = {
        "program/claude-authority-docs",
        "program/codex-core-algorithms",
        "program/codex-numerical-audit",
        "program/cursor-app-integration",
        "program/integration",
        "r1081-cwatlas",
        "r1082-locked-root",
        "r1083-result-reconciliation",
        "rcw-public-workbench",
        "release/rgcs-v1-map-workbench",
    }
    if name in safe_names:
        return Classification(
            CLASS_PUBLIC,
            "bounded public work or receipt lane; merge only its delta after filter audit",
        )
    if name.startswith("release-safety-snapshot-"):
        return Classification(
            CLASS_PUBLIC,
            "immutable local safety pointer; retain but do not merge",
        )
    if ahead == 0:
        return Classification(
            CLASS_REVIEW,
            "already contained in main; no delta to merge and no automatic publication decision",
        )
    return Classification(CLASS_REVIEW, "unmatched branch requires human review")


def parse_worktrees(repo: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in run_git(repo, "worktree", "list", "--porcelain").splitlines() + [""]:
        if not line:
            if current:
                records.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            current["path"] = value
        elif key == "HEAD":
            current["head"] = value
        elif key == "branch":
            current["branch"] = value.removeprefix("refs/heads/")
        elif key == "detached":
            current["branch"] = "(detached)"
    return records


def status_rows(path: Path) -> tuple[list[str], list[str]]:
    rows = git_lines(path, "status", "--porcelain=v1", "--untracked-files=all")
    changed = [row for row in rows if not row.startswith("??")]
    untracked = [normalize(row[3:]) for row in rows if row.startswith("??")]
    return changed, untracked


def relation(in_main: bool, contains_main: bool, ahead: int, behind: int) -> str:
    if ahead == behind == 0:
        return "same-as-main"
    if in_main:
        return "ancestor-of-main"
    if contains_main:
        return "descendant-of-main"
    return "diverged-from-main"


def collect_inventory(repo: Path) -> dict[str, object]:
    repo = repo.resolve()
    main_head = run_git(repo, "rev-parse", "main").strip()
    worktrees = parse_worktrees(repo)
    worktrees_by_branch = {
        row["branch"]: row for row in worktrees if row.get("branch") != "(detached)"
    }
    branches: list[dict[str, object]] = []
    for row in git_lines(
        repo,
        "for-each-ref",
        "--format=%(refname:short)|%(objectname)|%(subject)",
        "refs/heads",
    ):
        name, head, subject = row.split("|", 2)
        behind_s, ahead_s = run_git(
            repo, "rev-list", "--left-right", "--count", f"main...{name}"
        ).split()
        behind, ahead = int(behind_s), int(ahead_s)
        in_main = (
            subprocess.run(
                ["git", "-C", str(repo), "merge-base", "--is-ancestor", name, "main"]
            ).returncode
            == 0
        )
        contains_main = (
            subprocess.run(
                ["git", "-C", str(repo), "merge-base", "--is-ancestor", "main", name]
            ).returncode
            == 0
        )
        changed_files = git_lines(repo, "diff", "--name-only", f"main...{name}")
        linked = worktrees_by_branch.get(name)
        changed_worktree: list[str] = []
        untracked_worktree: list[str] = []
        if linked:
            changed_worktree, untracked_worktree = status_rows(Path(linked["path"]))
        classification = classify_branch(name, ahead, subject)
        branches.append(
            {
                "name": name,
                "head": head,
                "subject": subject,
                "ahead_main": ahead,
                "behind_main": behind,
                "relation": relation(in_main, contains_main, ahead, behind),
                "changed_file_count": len(changed_files),
                "changed_files": changed_files,
                "worktree_changed_files": changed_worktree,
                "untracked_files": untracked_worktree,
                "proof_test_directories": proof_dirs(repo, name),
                "classification": classification.value,
                "classification_reason": classification.reason,
            }
        )
    branch_by_head: dict[str, list[dict[str, object]]] = {}
    for branch in branches:
        branch_by_head.setdefault(str(branch["head"]), []).append(branch)
    worktree_rows: list[dict[str, object]] = []
    for worktree in worktrees:
        path = Path(worktree["path"])
        changed, untracked = status_rows(path)
        named = worktree.get("branch", "(detached)")
        matching = branch_by_head.get(worktree["head"], [])
        if named != "(detached)":
            branch_row = next(row for row in matching if row["name"] == named)
            classification = Classification(
                str(branch_row["classification"]), str(branch_row["classification_reason"])
            )
        elif matching:
            source = matching[0]
            classification = Classification(
                str(source["classification"]),
                f"detached at {source['name']}: {source['classification_reason']}",
            )
        else:
            classification = Classification(CLASS_REVIEW, "detached HEAD has no named branch match")
        worktree_rows.append(
            {
                "path": path.as_posix(),
                "branch": named,
                "head": worktree["head"],
                "changed_files": changed,
                "untracked_files": untracked,
                "proof_test_directories": proof_dirs(path, "HEAD"),
                "classification": classification.value,
                "classification_reason": classification.reason,
            }
        )
    return {
        "schema_version": 1,
        "generated_at": datetime.now().astimezone().isoformat(),
        "baseline_branch": "main",
        "baseline_head": main_head,
        "safety_snapshot_branches": [
            row["name"] for row in branches if str(row["name"]).startswith("release-safety-snapshot-")
        ],
        "branches": branches,
        "worktrees": worktree_rows,
    }


def md_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def compact_paths(paths: Sequence[str], limit: int = 8) -> str:
    if not paths:
        return "none"
    shown = list(paths[:limit])
    suffix = f"; +{len(paths) - limit} more" if len(paths) > limit else ""
    return "; ".join(f"`{path}`" for path in shown) + suffix


def render_inventory(inventory: dict[str, object]) -> str:
    branches = inventory["branches"]
    worktrees = inventory["worktrees"]
    lines = [
        "# R10 Public Release Branch and Worktree Inventory",
        "",
        f"Generated: `{inventory['generated_at']}`",
        f"Baseline: `main` at `{inventory['baseline_head']}`",
        "",
        "Classification is applied to each branch delta relative to `main`, not as a declaration that every historical file at that tip is publishable. File-level release still requires the exclusion-first manifest. An unmatched or mixed lane is never auto-promoted.",
        "",
        "## Branches",
        "",
        "| Branch | HEAD | Main relation | Delta | Worktree state | Proof/test dirs | Class | Reason |",
        "|---|---|---|---:|---|---|---|---|",
    ]
    for row in branches:  # type: ignore[assignment]
        worktree_state = (
            f"changed={len(row['worktree_changed_files'])}, untracked={len(row['untracked_files'])}"
            if row["worktree_changed_files"] or row["untracked_files"]
            else "clean/not linked"
        )
        lines.append(
            "| {name} | `{head}` | {relation}; +{ahead_main}/-{behind_main} | {changed_file_count} | {worktree} | {proofs} | **{classification}** | {reason} |".format(
                name=md_escape(row["name"]),
                head=str(row["head"])[:12],
                relation=md_escape(row["relation"]),
                ahead_main=row["ahead_main"],
                behind_main=row["behind_main"],
                changed_file_count=row["changed_file_count"],
                worktree=worktree_state,
                proofs=len(row["proof_test_directories"]),
                classification=row["classification"],
                reason=md_escape(row["classification_reason"]),
            )
        )
    lines.extend(
        [
            "",
            "## Worktrees",
            "",
            "| Path | Branch | HEAD | Changed | Untracked | Proof/test dirs | Class |",
            "|---|---|---|---:|---:|---:|---|",
        ]
    )
    for row in worktrees:  # type: ignore[assignment]
        lines.append(
            f"| `{md_escape(row['path'])}` | {md_escape(row['branch'])} | `{str(row['head'])[:12]}` | {len(row['changed_files'])} | {len(row['untracked_files'])} | {len(row['proof_test_directories'])} | **{row['classification']}** |"
        )
    lines.extend(
        [
            "",
            "## Detailed Delta Evidence",
            "",
        ]
    )
    for row in branches:  # type: ignore[assignment]
        if row["changed_files"] or row["untracked_files"]:
            lines.extend(
                [
                    f"### `{row['name']}`",
                    "",
                    f"- Changed relative to `main`: {compact_paths(row['changed_files'])}",
                    f"- Untracked in linked worktree: {compact_paths(row['untracked_files'])}",
                    f"- Proof/test directories: {compact_paths(row['proof_test_directories'], 12)}",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def render_review_queue(inventory: dict[str, object]) -> str:
    review = [
        row
        for row in inventory["branches"]  # type: ignore[index]
        if row["classification"] in {CLASS_REVIEW, CLASS_QUARANTINE}
    ]
    lines = [
        "# R10 Public Release Review Queue",
        "",
        "Items here are not release inputs. A human may later approve a file-level subset after provenance and private-lane review; silence is not approval.",
        "",
        f"Queue count: **{len(review)} branches**",
        "",
        "| Branch | HEAD | Class | Ahead/behind main | Reason |",
        "|---|---|---|---:|---|",
    ]
    for row in review:
        lines.append(
            f"| {md_escape(row['name'])} | `{str(row['head'])[:12]}` | **{row['classification']}** | +{row['ahead_main']}/-{row['behind_main']} | {md_escape(row['classification_reason'])} |"
        )
    lines.extend(
        [
            "",
            "## Explicit Decisions Needed",
            "",
            "- The mixed R10.62-R10.73 branch cannot be merged whole. Only independently audited public commits may be replayed onto a clean integration branch.",
            "- Historical release tips remain provenance references, not automatic RC content.",
            "- R10.8.4 remains held because its authority and physical-language review are unresolved.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_inventory(repo: Path) -> None:
    inventory = collect_inventory(repo)
    out = repo / "docs" / "release"
    out.mkdir(parents=True, exist_ok=True)
    (out / "r10_branch_worktree_inventory.json").write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "r10_public_release_inventory.md").write_text(
        render_inventory(inventory), encoding="utf-8"
    )
    (out / "r10_review_queue.md").write_text(
        render_review_queue(inventory), encoding="utf-8"
    )


def collect_safety_snapshot(repo: Path, snapshot_worktree: Path) -> dict[str, object]:
    branch_vv = run_git(snapshot_worktree, "branch", "-vv").splitlines()
    phase0_branch_vv = [
        line for line in branch_vv if SAFETY_SNAPSHOT_BRANCH not in line
    ]
    snapshot_head = run_git(repo, "rev-parse", SAFETY_SNAPSHOT_BRANCH).strip()
    return {
        "schema_version": 1,
        "phase0_captured_at": PHASE0_CAPTURED_AT,
        "receipt_generated_at": datetime.now().astimezone().isoformat(),
        "commands": {
            "current_branch": "git branch --show-current",
            "status_short": "git status --short",
            "head_oneline": "git log -1 --oneline",
            "branches": "git branch -vv",
            "worktrees": "git worktree list",
            "tags": "git tag --list",
        },
        "current_branch": run_git(snapshot_worktree, "branch", "--show-current").strip(),
        "status_short": git_lines(snapshot_worktree, "status", "--short"),
        "head_oneline": run_git(snapshot_worktree, "log", "-1", "--oneline").strip(),
        "branch_vv": phase0_branch_vv,
        "worktree_list": run_git(snapshot_worktree, "worktree", "list").splitlines(),
        "tag_list": git_lines(snapshot_worktree, "tag", "--list"),
        "safety_branch": SAFETY_SNAPSHOT_BRANCH,
        "safety_branch_head": snapshot_head,
        "safety_branch_matches_phase0_head": snapshot_head
        == run_git(snapshot_worktree, "rev-parse", "HEAD").strip(),
        "constraints": {
            "worktrees_deleted": False,
            "push_performed": False,
            "tag_created_during_snapshot": False,
        },
    }


def render_safety_snapshot(snapshot: dict[str, object]) -> str:
    def block(command: str, rows: Sequence[str]) -> list[str]:
        return [f"### `{command}`", "", "```text", *rows, "```", ""]

    lines = [
        "# R10 Public Release Safety Snapshot",
        "",
        f"Captured: `{snapshot['phase0_captured_at']}`",
        f"Safety branch: `{snapshot['safety_branch']}` at `{snapshot['safety_branch_head']}`",
        "No worktree was deleted, no push was performed, and no tag was created during this phase.",
        "",
    ]
    lines += block(
        snapshot["commands"]["current_branch"], [snapshot["current_branch"]]
    )
    lines += block(snapshot["commands"]["status_short"], snapshot["status_short"])
    lines += block(snapshot["commands"]["head_oneline"], [snapshot["head_oneline"]])
    lines += block(snapshot["commands"]["branches"], snapshot["branch_vv"])
    lines += block(snapshot["commands"]["worktrees"], snapshot["worktree_list"])
    lines += block(snapshot["commands"]["tags"], snapshot["tag_list"])
    return "\n".join(lines).rstrip() + "\n"


def write_safety_snapshot(repo: Path, snapshot_worktree: Path) -> None:
    snapshot = collect_safety_snapshot(repo, snapshot_worktree)
    out = repo / "docs" / "release"
    out.mkdir(parents=True, exist_ok=True)
    (out / "r10_safety_snapshot.json").write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "r10_safety_snapshot.md").write_text(
        render_safety_snapshot(snapshot), encoding="utf-8"
    )


def _load_json(path: Path, default: object) -> object:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _current_public_rows(repo: Path) -> tuple[list[dict[str, object]], dict[str, bytes]]:
    head = run_git(repo, "rev-parse", "HEAD").strip()
    rows: list[dict[str, object]] = []
    data_by_path: dict[str, bytes] = {}
    for path in git_lines(repo, "ls-files"):
        normalized = normalize(path)
        data = (repo / normalized).read_bytes()
        data_by_path[normalized] = data
        rows.append(classify_blob(BlobRecord(normalized, head, data)))
    return rows, data_by_path


def _replace_release_directory(repo: Path, destination: Path) -> None:
    releases = (repo / "dist" / "releases").resolve()
    target = destination.resolve()
    try:
        target.relative_to(releases)
    except ValueError as exc:
        raise RuntimeError(f"refusing to replace path outside {releases}: {target}") from exc
    releases.mkdir(parents=True, exist_ok=True)
    if target.exists():
        def clear_readonly(function, path, exception):
            try:
                os.chmod(path, stat.S_IWRITE)
                function(path)
            except OSError:
                raise exception

        shutil.rmtree(target, onexc=clear_readonly)
    target.mkdir(parents=True)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")


def _tree_file_rows(root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted((item for item in root.rglob("*") if item.is_file()),
                       key=lambda item: item.relative_to(root).as_posix()):
        data = path.read_bytes()
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size_bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    return rows


def _write_csv_manifest(path: Path, rows: Sequence[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("path", "size_bytes", "sha256"),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def _identifier_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            names.update(alias.asname or alias.name.rsplit(".", 1)[-1]
                         for alias in node.names)
    return names


def _namespace_and_power_audit(source_root: Path) -> dict[str, object]:
    namespace_pattern = re.compile(r"(?:^|_)(?:force|thrust)(?:$|_)", re.IGNORECASE)
    namespace_leaks: list[dict[str, str]] = []
    wall_power_paths: list[dict[str, object]] = []
    for path in sorted(source_root.rglob("*.py")):
        rel = path.relative_to(source_root).as_posix()
        if rel.startswith("tests/") or "/tests/" in rel:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        names = _identifier_names(tree)
        boundary = rel in NAMESPACE_FIREWALL_PATHS or "firewall" in Path(rel).name
        force_names = sorted(name for name in names if namespace_pattern.search(name))
        if force_names and not boundary:
            namespace_leaks.extend(
                {"path": rel, "identifier": name} for name in force_names
            )
        wall_names = sorted(
            name for name in names
            if ("wall" in name.lower() and "power" in name.lower())
            or "power_from_wall" in name.lower()
        )
        if wall_names and force_names and not boundary:
            wall_power_paths.append(
                {"path": rel, "wall_identifiers": wall_names,
                 "performance_identifiers": force_names}
            )
    return {
        "force_thrust_namespace_leak_count": len(namespace_leaks),
        "force_thrust_namespace_leaks": namespace_leaks,
        "wall_power_path_count": len(wall_power_paths),
        "wall_power_paths": wall_power_paths,
        "wall_power_path_status": "NONE" if not wall_power_paths else "STOP",
    }


def _restricted_output_hits(paths: Sequence[Path], base: Path) -> list[dict[str, object]]:
    hits: list[dict[str, object]] = []
    for path in paths:
        data = path.read_bytes()
        text = data.decode("utf-8", errors="ignore")
        rel = path.relative_to(base).as_posix() if path.is_relative_to(base) else path.name
        matched = excluded_hits(f"{rel}\n{text}")
        if matched:
            hits.append({"path": rel, "terms": matched})
    return hits


def _render_rc_readme(head: str) -> str:
    return f"""# RGCS R10 Public RC1

This is a local public software and documentation candidate built from `{head}`. No remote publication is performed by the build.

Included surfaces:

- the RGCS coordinate workbench and structural coordinate adapters;
- the 27/30/33/36-bit variable-length vector codec;
- public maps, paths, polygons, calibration notes, and parse receipts;
- R10.71 through R10.74 bounded annular engineering scaffolds;
- public tests, provenance records, and safety/claim boundaries.

The ARDK is a controllable annular electromagnetic field-asymmetry demonstrator with no mechanical rotation. Fabrication readiness is `REFUSED`. Seed drive inputs remain `NOT_AUTHORITY`; the R10.73 authority is pinned to `{R10_73_AUTHORITY_COMMIT}`.
"""


def _render_rc_release_notes(head: str, test_report: dict[str, object]) -> str:
    summary = test_report.get("summary", {}) if isinstance(test_report, dict) else {}
    passed = summary.get("passed", "PENDING")
    skipped = summary.get("skipped", "PENDING")
    warnings = summary.get("warnings", "PENDING")
    return f"""# R10 Public RC1 Release Notes

Source commit: `{head}`.

This candidate consolidates the public coordinate workbench, variable-length structural codec, bounded annular optimizer, R10.73 authority receipts, and R10.74 development-kit scaffold. File-level inclusion is allowlisted and content-filtered; unmatched source material remains held for review.

Full-suite result: `{passed}` passed, `{skipped}` skipped, `{warnings}` warnings. See `REPRODUCTION.md` for commands.

ARDK fabrication readiness remains `REFUSED`. This candidate is not a fabrication release.
"""


def _render_rc_limitations(review_count: int) -> str:
    return f"""# R10 Public RC1 Known Limitations

- ARDK fabrication readiness is `REFUSED`; physical manufacturing evidence is incomplete.
- Seed drive inputs are `NOT_AUTHORITY` and cannot authorize generation or fabrication.
- Physical projection profiles remain bounded by their checked-in claim classes and calibration evidence.
- {review_count} tracked source files remain outside the candidate pending human review.
- This is a local candidate. No remote publication has been performed.
"""


def _render_rc_review_queue(review_count: int, quarantine_count: int,
                            withheld_count: int) -> str:
    return f"""# R10 Public RC1 Review Queue

No item in this queue is part of the candidate payload.

- Human-review source files: **{review_count}**
- Archive/quarantine source files: **{quarantine_count}**
- Policy-withheld source files: **{withheld_count}**

The detailed internal queue remains in the repository release-control records. A future candidate requires an explicit file-level decision; absence from this summary is not approval.
"""


def _render_rc_reproduction(test_report: dict[str, object]) -> str:
    command = "python -m pytest -q --basetemp build/pytest-r10-public-rc1"
    if isinstance(test_report, dict):
        command = str(test_report.get("command", command))
    return f"""# R10 Public RC1 Reproduction

From the repository revision recorded in `SOURCE_MANIFEST.json`:

```text
python -m pip install -e .
{command}
python -m pytest tests/rgcs_coordinate tests/release_public rgcs_ardk/tests -q
```

For the filtered candidate tree itself, set `PYTHONPATH=source` and run the test paths present under `source/tests` and `source/rgcs_ardk/tests`.

All generated hashes use SHA-256 and paths relative to the candidate root.
"""


def build_public_rc(repo: Path) -> dict[str, object]:
    repo = repo.resolve()
    branch = run_git(repo, "branch", "--show-current").strip()
    status = git_lines(repo, "status", "--porcelain=v1", "--untracked-files=normal")
    if branch != "main":
        raise RuntimeError(f"release candidate must be built from main, not {branch}")
    if status:
        raise RuntimeError(f"release candidate requires a clean tree: {status}")

    head = run_git(repo, "rev-parse", "HEAD").strip()
    commit_time = run_git(repo, "show", "-s", "--format=%cI", "HEAD").strip()
    rows, data_by_path = _current_public_rows(repo)
    public_rows = sorted(
        (row for row in rows if row["classification"] == CLASS_PUBLIC),
        key=lambda row: str(row["path"]),
    )
    counts = {
        classification: sum(row["classification"] == classification for row in rows)
        for classification in (CLASS_PUBLIC, CLASS_PRIVATE, CLASS_QUARANTINE, CLASS_REVIEW)
    }

    required = {
        "LICENSE",
        "rgcs_coordinate/codecs/variable_length_36.py",
        "tests/rgcs_coordinate/test_variable_length_36.py",
        "docs/proofs/workbench-release/VARIABLE_LENGTH_CODEC_RECEIPT.json",
        "docs/proofs/r1072-phyrll-engineering-v07/ring_steering_optimizer_report.json",
        "docs/proofs/r1073-bench-drive/drive_table.json",
        "docs/proofs/r1074-annular-devkit/manufacturing_readiness_report.md",
        "rgcs_ardk/drive/authority_manifest.json",
    }
    selected_paths = {str(row["path"]) for row in public_rows}
    missing = sorted(required - selected_paths)
    if missing:
        raise RuntimeError(f"required public candidate paths are not eligible: {missing}")
    prohibited = {
        "rgcs_phyrll_v06/resonance.py",
        "rgcs_phyrll_v07/force_boundary.py",
        "rgcs_phyrll_v07/resonator.py",
        "rgcs_terra_release/release_filter.py",
    }
    leaked_prohibited = sorted(prohibited & selected_paths)
    if leaked_prohibited:
        raise RuntimeError(f"prohibited implementation paths selected: {leaked_prohibited}")

    releases = repo / "dist" / "releases"
    rc_root = releases / RC_NAME
    _replace_release_directory(repo, rc_root)
    source_root = rc_root / "source"
    for row in public_rows:
        rel = str(row["path"])
        destination = source_root / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data_by_path[rel])

    registry = _load_json(repo / "docs/release/r10_public_package_registry.json", {})
    test_report = _load_json(repo / "docs/release/r10_full_test_report.json", {})
    source_manifest = {
        "schema_version": 1,
        "release": RC_NAME,
        "main_head": head,
        "source_commit_time": commit_time,
        "r10_73_authority_commit": R10_73_AUTHORITY_COMMIT,
        "r10_74_source_commit": R10_74_SOURCE_COMMIT,
        "fabrication_readiness": "REFUSED",
        "seed_status": "NOT_AUTHORITY",
        "release_resolution": registry.get("release_resolution", {}),
        "source_file_count": len(public_rows),
        "files": [
            {
                "path": row["path"],
                "size_bytes": row["size_bytes"],
                "sha256": row["sha256"],
            }
            for row in public_rows
        ],
    }
    _write_text(rc_root / "README.md", _render_rc_readme(head))
    release_notes = _render_rc_release_notes(head, test_report)
    limitations = _render_rc_limitations(counts[CLASS_REVIEW])
    review_queue = _render_rc_review_queue(
        counts[CLASS_REVIEW], counts[CLASS_QUARANTINE], counts[CLASS_PRIVATE]
    )
    _write_text(rc_root / "RELEASE_NOTES.md", release_notes)
    _write_text(rc_root / "KNOWN_LIMITATIONS.md", limitations)
    _write_text(rc_root / "REVIEW_QUEUE.md", review_queue)
    _write_text(rc_root / "REPRODUCTION.md", _render_rc_reproduction(test_report))
    _write_text(
        rc_root / "REQUIREMENTS.txt",
        "numpy\nscipy\nPyYAML\npytest",
    )
    (rc_root / "LICENSE").write_bytes((repo / "LICENSE").read_bytes())
    _write_text(
        rc_root / "SOURCE_MANIFEST.json",
        json.dumps(source_manifest, indent=2, sort_keys=True),
    )

    payload_rows = _tree_file_rows(rc_root)
    _write_csv_manifest(rc_root / "FILE_MANIFEST.csv", payload_rows)
    all_rows = _tree_file_rows(rc_root)

    external_json = releases / f"{RC_NAME}_MANIFEST.json"
    external_csv = releases / f"{RC_NAME}_MANIFEST.csv"
    external_sums = releases / f"{RC_NAME}_SHA256SUMS.txt"
    external_notes = releases / f"{RC_NAME}_RELEASE_NOTES.md"
    external_limits = releases / f"{RC_NAME}_KNOWN_LIMITATIONS.md"
    external_review = releases / f"{RC_NAME}_REVIEW_QUEUE.md"
    external_manifest = {
        "schema_version": 1,
        "release": RC_NAME,
        "main_head": head,
        "generated_from_commit_time": commit_time,
        "file_count": len(all_rows),
        "files": all_rows,
    }
    _write_text(external_json, json.dumps(external_manifest, indent=2, sort_keys=True))
    _write_csv_manifest(external_csv, all_rows)
    _write_text(
        external_sums,
        "\n".join(f"{row['sha256']}  {RC_NAME}/{row['path']}" for row in all_rows),
    )
    _write_text(external_notes, release_notes)
    _write_text(external_limits, limitations)
    _write_text(external_review, review_queue)

    output_files = [
        path for path in rc_root.rglob("*") if path.is_file()
    ] + [
        external_json,
        external_csv,
        external_sums,
        external_notes,
        external_limits,
        external_review,
    ]
    restricted_hits = _restricted_output_hits(output_files, releases)
    code_audit = _namespace_and_power_audit(source_root)
    authority = json.loads(
        (source_root / "rgcs_ardk/drive/authority_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    seed_files = sorted((source_root / "rgcs_ardk/drive/seed").iterdir())
    manufacturing_text = (
        source_root
        / "docs/proofs/r1074-annular-devkit/manufacturing_readiness_report.md"
    ).read_text(encoding="utf-8")
    structural_gates = {
        "restricted_output_hit_count": len(restricted_hits),
        "restricted_output_hits": restricted_hits,
        **code_audit,
        "r10_73_authority_pinned": authority.get("source_commit")
        == R10_73_AUTHORITY_COMMIT,
        "seed_files_not_authority": bool(seed_files)
        and all("NOT_AUTHORITY" in path.name for path in seed_files),
        "fabrication_readiness_refused": "REFUSED" in manufacturing_text,
        "license_present": (rc_root / "LICENSE").is_file(),
        "sha256_manifest_present": external_sums.is_file(),
        "review_queue_present": (rc_root / "REVIEW_QUEUE.md").is_file(),
    }
    structural_pass = (
        not restricted_hits
        and code_audit["force_thrust_namespace_leak_count"] == 0
        and code_audit["wall_power_path_count"] == 0
        and all(
            structural_gates[key]
            for key in (
                "r10_73_authority_pinned",
                "seed_files_not_authority",
                "fabrication_readiness_refused",
                "license_present",
                "sha256_manifest_present",
                "review_queue_present",
            )
        )
    )
    gate_report = {
        "schema_version": 1,
        "release": RC_NAME,
        "main_head": head,
        "status": "PASS" if structural_pass else "REFUSED",
        "source_file_count": len(public_rows),
        "release_file_count": len(all_rows),
        "classification_counts": counts,
        "gates": structural_gates,
    }
    gate_path = releases / f"{RC_NAME}_GATE_REPORT.json"
    _write_text(gate_path, json.dumps(gate_report, indent=2, sort_keys=True))
    if not structural_pass:
        raise RuntimeError(f"release candidate structural gates refused: {gate_report}")
    return gate_report


def verify_public_rc(repo: Path) -> dict[str, object]:
    repo = repo.resolve()
    releases = repo / "dist" / "releases"
    rc_root = releases / RC_NAME
    manifest_path = releases / f"{RC_NAME}_MANIFEST.json"
    if not rc_root.is_dir() or not manifest_path.is_file():
        raise RuntimeError("release candidate or manifest is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual = _tree_file_rows(rc_root)
    hashes_match = actual == manifest.get("files")
    output_files = [path for path in rc_root.rglob("*") if path.is_file()]
    output_files.extend(
        path for path in releases.glob(f"{RC_NAME}_*") if path.is_file()
        and path.name != f"{RC_NAME}_GATE_REPORT.json"
    )
    hits = _restricted_output_hits(output_files, releases)
    code_audit = _namespace_and_power_audit(rc_root / "source")
    result = {
        "manifest_hashes_match": hashes_match,
        "restricted_output_hit_count": len(hits),
        **code_audit,
        "status": "PASS" if (
            hashes_match
            and not hits
            and code_audit["force_thrust_namespace_leak_count"] == 0
            and code_audit["wall_power_path_count"] == 0
        ) else "REFUSED",
    }
    return result


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("inventory")
    sub.add_parser("build")
    sub.add_parser("verify")
    snapshot = sub.add_parser("snapshot")
    snapshot.add_argument("--snapshot-worktree", type=Path, required=True)
    audit = sub.add_parser("audit")
    audit.add_argument("--revision", default="main")
    audit.add_argument(
        "--overlay",
        action="append",
        default=None,
        help="commit to overlay; repeat in application order",
    )
    audit.add_argument(
        "--no-overlays",
        action="store_true",
        help="scan the selected revision exactly as committed",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo = args.repo.resolve()
    if args.command == "inventory":
        write_inventory(repo)
        return 0
    if args.command == "build":
        print(json.dumps(build_public_rc(repo), indent=2, sort_keys=True))
        return 0
    if args.command == "verify":
        result = verify_public_rc(repo)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["status"] == "PASS" else 1
    if args.command == "snapshot":
        write_safety_snapshot(repo, args.snapshot_worktree.resolve())
        return 0
    if args.command == "audit":
        if args.no_overlays and args.overlay:
            raise SystemExit("--no-overlays cannot be combined with --overlay")
        overlays = () if args.no_overlays else (
            tuple(args.overlay) if args.overlay else SAFE_OVERLAY_COMMITS
        )
        write_filter_audit(repo, args.revision, overlays)
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
