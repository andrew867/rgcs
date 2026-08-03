#!/usr/bin/env python3
"""Local-only inventory and release gates for the R10 public candidate.

The module deliberately defaults to REVIEW.  A path is public only when an
explicit inclusion rule matches and no path or content exclusion matches.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
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
    "r1028/varcodec36.py",
}

PUBLIC_PREFIXES = (
    "docs/workbench/",
    "rgcs_coordinate/",
    "rgcs_workbench/",
    "tests/rgcs_coordinate/",
    "rgcs_lab/",
    "tests/rgcs_lab/",
    "examples/rgcs_lab_",
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

PUBLIC_TEST_FILES = {
    "tests/test_miami_bermuda_calibration.py",
    "tests/test_phyrll_v06_annular_proxy.py",
    "tests/test_phyrll_v06_coefficients.py",
    "tests/test_phyrll_v06_resonance.py",
    "tests/test_phyrll_v06_ring37.py",
    "tests/test_terra_public_release_filter.py",
    "tests/test_phyrll_v07_engineering.py",
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
    return path.replace("\\", "/").lstrip("./")


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
    existing_filter_test_count: int = 18,
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
        "## Prospective Overlay",
        "",
        "The following independently selected commits were overlaid on `main` for the pre-merge scan; the mixed 37-commit branch was not treated as a release input.",
        "",
        "| Commit | Files | Subject |",
        "|---|---:|---|",
    ]
    for row in overlays:  # type: ignore[assignment]
        lines.append(
            f"| `{str(row['commit'])[:12]}` | {row['changed_files']} | {md_escape(row['subject'])} |"
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


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("inventory")
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
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo = args.repo.resolve()
    if args.command == "inventory":
        write_inventory(repo)
        return 0
    if args.command == "snapshot":
        write_safety_snapshot(repo, args.snapshot_worktree.resolve())
        return 0
    if args.command == "audit":
        overlays = tuple(args.overlay) if args.overlay else SAFE_OVERLAY_COMMITS
        write_filter_audit(repo, args.revision, overlays)
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
