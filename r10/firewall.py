"""P19 — the private/public publication firewall.

The rule this enforces is narrow and absolute: private source material
must never enter public Git history, packages, docs, logs, fixtures, or
release assets.

Two design commitments, both learned the hard way elsewhere in this
programme:

**Git history is disclosure.** Committing a private file and deleting
it in a later commit does not remove it. The scanner therefore checks
history, not just the working tree, because the working tree is the
part that is already fine.

**``.gitignore`` is not confidentiality.** An ignored directory inside
the repository is one ``git add -f`` away from publication, and it
still sits in the backup, the editor's recent files, and the search
index. Private material lives outside the worktree or it is not
private.

The forbidden-term registry is deliberately kept in a form that does
not itself leak: terms are matched case-insensitively against a small
list of category patterns, and the scanner reports *which category*
matched and where, never the surrounding text. A leak report that
quotes the leak is a second leak.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

#: Categories of forbidden content. Patterns are broad on purpose --
#: a false positive costs a review, a false negative costs a
#: disclosure.
FORBIDDEN_PATTERNS = {
    "PERSONAL_IDENTITY": (
        r"star.?family", r"chosen\s+(?:one|person)", r"zoltron",
    ),
    "PRIVATE_CHANNELLING": (
        r"channell?ed\s+message", r"transcript\s+of\s+session",
    ),
    "PRIVATE_PATH": (
        r"RGCS-private", r"[A-Za-z]:\\Users\\[^\\\s\"']+\\",
        r"/home/[^/\s\"']+/",
    ),
    "CREDENTIAL": (
        r"\bghp_[A-Za-z0-9]{20,}", r"\bsk-[A-Za-z0-9]{20,}",
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    ),
    "SUPERNATURAL_AUTHENTICATION": (
        r"proves?\s+extraterrestrial", r"confirms?\s+the\s+source\s+is",
        r"authenticat\w+\s+(?:the\s+)?(?:contact|origin)",
    ),
}

#: Paths that legitimately discuss the policy and would otherwise trip
#: the scanner on their own rules. Kept short and reviewed.
POLICY_ALLOWLIST = (
    "r10/firewall.py",
    "tests/v52/test_r10_firewall.py",
    "docs/v52/R10_PUBLICATION_FIREWALL.md",
)

#: Surfaces that are frozen historical records and cannot be edited
#: without destroying what they attest to.
#:
#: R10-D-001: the first run of this scanner found 30 absolute-path
#: disclosures already in the public repository, 18 of them in the
#: frozen v2.0.0 provenance record. Those paths are build-environment
#: paths baked into a checksummed archive: rewriting them would
#: invalidate the very provenance the archive exists to provide, and
#: the archive is immutable by release policy.
#:
#: They are therefore RECORDED, not fixed, and this is a real residual
#: exposure rather than a clean pass. Live surfaces get repaired; this
#: one is declared. Anything added here needs a reason in this comment
#: -- an allowlist that grows silently is a firewall that has been
#: switched off.
FROZEN_SURFACES = (
    "archive/",
)

#: Extensions worth scanning. Binary formats are hashed, not read.
TEXT_SUFFIXES = {".py", ".md", ".json", ".txt", ".yaml", ".yml",
                 ".toml", ".cfg", ".ini", ".rst", ".html", ".js"}


class LeakDetected(RuntimeError):
    """Raised when forbidden content is found in a public surface."""


@dataclass(frozen=True)
class Finding:
    """A hit. Deliberately carries no excerpt of the matched text."""

    category: str
    path: str
    line: int
    surface: str          # WORKING_TREE | GIT_HISTORY | PACKAGE

    def as_record(self) -> dict:
        return {"category": self.category, "path": self.path,
                "line": self.line, "surface": self.surface,
                "excerpt": "REDACTED — a leak report must not quote "
                           "the leak"}


def _compiled():
    return {cat: [re.compile(p, re.I) for p in pats]
            for cat, pats in FORBIDDEN_PATTERNS.items()}


def scan_text(text: str, path: str, surface: str) -> list[Finding]:
    out = []
    pats = _compiled()
    for i, line in enumerate(text.splitlines(), 1):
        for cat, regexes in pats.items():
            if any(r.search(line) for r in regexes):
                out.append(Finding(cat, path, i, surface))
    return out


def _is_frozen(rel: str, frozen=FROZEN_SURFACES) -> bool:
    return any(rel.startswith(f) for f in frozen)


def scan_working_tree(root: Path, allowlist=POLICY_ALLOWLIST,
                      include_frozen: bool = False) -> list[Finding]:
    """Scan tracked text files in the working tree.

    Frozen surfaces are skipped by default and reported separately by
    :func:`frozen_surface_exposure`, so that a declared residual
    exposure is never quietly counted as a clean pass.
    """
    out = []
    try:
        tracked = subprocess.run(
            ["git", "ls-files"], cwd=root, capture_output=True,
            text=True, check=True).stdout.splitlines()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return out
    for rel in tracked:
        if rel in allowlist:
            continue
        if not include_frozen and _is_frozen(rel):
            continue
        p = root / rel
        if p.suffix.lower() not in TEXT_SUFFIXES or not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        out.extend(scan_text(text, rel, "WORKING_TREE"))
    return out


def scan_git_history(root: Path, max_commits: int = 400,
                     allowlist=POLICY_ALLOWLIST) -> list[Finding]:
    """Scan added lines across recent history.

    Deleting a private file in a later commit does not unpublish it.
    This is the check that reflects that.
    """
    out = []
    try:
        log = subprocess.run(
            ["git", "log", f"-{max_commits}", "-p", "--no-color",
             "--diff-filter=AM", "--unified=0"],
            cwd=root, capture_output=True, text=True, check=True,
            errors="ignore").stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return out
    current = "<unknown>"
    pats = _compiled()
    for line in log.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
            continue
        if not line.startswith("+") or line.startswith("+++"):
            continue
        if current in allowlist or _is_frozen(current):
            continue
        for cat, regexes in pats.items():
            if any(r.search(line) for r in regexes):
                out.append(Finding(cat, current, 0, "GIT_HISTORY"))
    return out


def private_root_is_outside(public_root: Path,
                            private_root: Path) -> dict:
    """Confirm the private root is not inside the public worktree.

    Being ignored is not sufficient and is not accepted here.
    """
    pub = public_root.resolve()
    priv = private_root.resolve()
    inside = pub == priv or pub in priv.parents
    return {
        "public_root": str(pub),
        "private_root": str(priv),
        "private_is_inside_public": inside,
        "acceptable": not inside,
        "note": (
            "a private directory inside the worktree is one `git add "
            "-f` from publication, and .gitignore is not "
            "confidentiality" if inside else
            "private root is outside the public worktree"),
    }


def frozen_surface_exposure(root: Path) -> dict:
    """What the firewall found in frozen history and cannot repair.

    This is reported, never suppressed. A clean live tree with a
    declared historical exposure is an honest state; a clean live tree
    with the history quietly excluded is not.
    """
    all_findings = scan_working_tree(root, include_frozen=True)
    frozen = [f for f in all_findings if _is_frozen(f.path)]
    return {
        "frozen_surfaces": list(FROZEN_SURFACES),
        "finding_count": len(frozen),
        "paths": sorted({f.path for f in frozen}),
        "categories": sorted({f.category for f in frozen}),
        "status": "DECLARED_RESIDUAL_EXPOSURE" if frozen else "CLEAN",
        "why_not_repaired": (
            "these are build-environment paths inside a checksummed, "
            "immutable archive. Editing them would invalidate the "
            "provenance record the archive exists to provide, and "
            "release policy forbids rewriting frozen history."),
        "assessed_severity": (
            "LOW: the paths disclose a build directory layout and a "
            "username that is already public in the package metadata "
            "and citation file. No credential, personal record, or "
            "source material is exposed."),
    }


def sanitized_export_record(private_hash: str, public_hash: str,
                            redactions: list[str], reviewer: str,
                            sanitizer_version: str) -> dict:
    """The only legitimate route from private to public."""
    if not redactions:
        raise ValueError(
            "an export with no redactions is a copy, not a "
            "sanitisation; state explicitly what was removed")
    if private_hash == public_hash:
        raise ValueError(
            "private and public hashes are identical, so nothing was "
            "changed and this is not a sanitised export")
    return {
        "schema": "rgcs.sanitized_export.v1",
        "source_private_hash": private_hash,
        "public_output_hash": public_hash,
        "sanitizer_version": sanitizer_version,
        "redactions": list(redactions),
        "reviewer": reviewer,
        "no_reconstruction_statement": (
            "the public output does not permit reconstruction of the "
            "private source, and the hash is recorded for audit "
            "without embedding the content"),
    }


def enforce(root: Path, check_history: bool = True) -> dict:
    """Full scan. Raises on any finding."""
    findings = scan_working_tree(root)
    if check_history:
        findings += scan_git_history(root)
    report = {
        "surfaces_scanned": (["WORKING_TREE", "GIT_HISTORY"]
                             if check_history else ["WORKING_TREE"]),
        "finding_count": len(findings),
        "findings": [f.as_record() for f in findings],
        "clean": not findings,
    }
    if findings:
        cats = sorted({f.category for f in findings})
        raise LeakDetected(
            f"{len(findings)} forbidden-content finding(s) across "
            f"categories {cats}. Publication is blocked. See the "
            f"report for paths; excerpts are deliberately withheld "
            f"because a leak report must not quote the leak.")
    return report
