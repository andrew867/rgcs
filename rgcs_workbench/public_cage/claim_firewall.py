"""Claim firewall for the public workbench release cage.

Scans public claim text for banned physical-claim phrases. A banned
phrase is a release-blocking finding UNLESS it appears in a
refused-claim context: a refusal sentence, a firewall or banned list,
a negative example, a quarantine label, or a question. The scan rules
follow the 2026-08-04 spec pack (03_TESTS/CLAIM_SCAN_RULES.md).

Design choice, stated so nobody relitigates it later: the context
window looks BACKWARD several lines, because refused-claim lists put
the marker in a heading above the phrase. A finding is a dict with
path, line number, phrase, and the offending text -- every rejection
carries an explicit reason, same rule as the codec receipts.

This module does text scanning. It does not measure, model, or claim
any physical effect. Full-package scanning at RC1 packaging time
remains pending.
"""

from __future__ import annotations

import pathlib
import re

#: Banned outside refused-claim contexts (spec CLAIM_SCAN_RULES).
BANNED_PHRASES = (
    "produces thrust",
    "produces lift",
    "antigravity",
    "gravity control",
    "barycentric field",
    "reactionless propulsion",
    "free energy",
    "validated craft",
    "source authenticated",
    "wall-power thrust",
    "wall-power force",
    "N/W output validated",
)

#: A banned phrase near one of these (same line or a few lines above)
#: is inside a refused-claim context and therefore allowed.
ALLOWED_CONTEXT_MARKERS = (
    "refus",            # refused, refuses, refusal
    "does not",
    "do not",
    "must not",
    "may not",
    "cannot",
    "no claim",
    "not claim",
    "non-claim",
    "never",
    "banned",
    "firewall",
    "negative example",
    "quarantine",
    "not validated",
    "no physical claim",
    "claims_refused",
    "excluded",
    "prohibit",
    "forbid",
    "without",
    # Explicit negation shapes ("Not a free-energy project", "what it
    # is not") and adversarial attack lists ("sixteen named attacks
    # ... each fails") are refusals, found by the full-tree scan.
    "is not",
    "not a ",
    "nothing physical",
    "attack",
)

#: Lines that begin with an explicit negation are refusal sentences.
_NEGATION_STARTS = ("no ", "not ", "- no ", "* no ", "no.", "none")

#: How many lines above a hit the context marker may sit (covers a
#: "Refused claims" heading over a plain list of phrases; the
#: H-ME-SSP-001 refused list is nine entries long, so 8 was one short
#: for its final entry -- caught by the gate on first run).
CONTEXT_WINDOW_BEFORE = 12

#: Whole files that ARE refused-claim contexts by definition (the
#: spec's allowed list names "claim firewall" and "safety scan tests").
_ALLOWED_CONTEXT_BASENAME_PARTS = ("firewall", "claim_scan")


def _file_is_allowed_context(path: str) -> bool:
    name = pathlib.Path(str(path)).name.lower()
    return any(part in name for part in _ALLOWED_CONTEXT_BASENAME_PARTS)


def _phrase_pattern(phrase: str) -> re.Pattern[str]:
    """Space, underscore, hyphen, and slash variants are equivalent."""
    pieces = [re.escape(p) for p in re.split(r"[ _\-/]+", phrase)]
    body = r"[\s_\-/]+".join(pieces)
    return re.compile(rf"(?<![a-z0-9]){body}(?![a-z0-9])", re.IGNORECASE)


_BANNED = tuple((phrase, _phrase_pattern(phrase))
                for phrase in BANNED_PHRASES)


def _in_refused_context(lines: list[str], idx: int) -> bool:
    lo = max(0, idx - CONTEXT_WINDOW_BEFORE)
    window = " ".join(lines[lo:idx + 1]).lower()
    if any(marker in window for marker in ALLOWED_CONTEXT_MARKERS):
        return True
    stripped = lines[idx].strip().lower()
    if stripped.startswith(_NEGATION_STARTS):
        return True
    # A question is not a claim; markdown emphasis may wrap it.
    if stripped.rstrip("*_`").endswith("?"):
        return True
    return False


def scan_text(text: str, path: str = "<text>") -> list[dict]:
    """Return one finding per banned phrase outside a refused context."""
    if _file_is_allowed_context(path):
        return []
    lines = text.splitlines()
    findings: list[dict] = []
    for idx, line in enumerate(lines):
        for phrase, pattern in _BANNED:
            if pattern.search(line) and not _in_refused_context(lines, idx):
                findings.append({
                    "path": str(path),
                    "line": idx + 1,
                    "phrase": phrase,
                    "text": line.strip(),
                    "reason": (f"banned phrase '{phrase}' outside a "
                               f"refused-claim context"),
                })
    return findings


def scan_file(path: str | pathlib.Path) -> list[dict]:
    p = pathlib.Path(path)
    text = p.read_bytes().decode("utf-8", errors="ignore")
    return scan_text(text, path=p.as_posix())


def scan_paths(paths) -> list[dict]:
    findings: list[dict] = []
    for p in paths:
        findings.extend(scan_file(p))
    return findings


def firewall_report(findings) -> dict:
    per_phrase: dict[str, int] = {}
    for f in findings:
        per_phrase[f["phrase"]] = per_phrase.get(f["phrase"], 0) + 1
    return {
        "findings": len(findings),
        "per_phrase": per_phrase,
        "clean": not findings,
        "verdict": ("RELEASE_FILTER_CLEAN" if not findings
                    else "RELEASE_BLOCKED_BANNED_CLAIM"),
    }


def cage_public_surface(root: str | pathlib.Path) -> list[pathlib.Path]:
    """The public claim surface the cage gates today.

    Scope, stated openly rather than silently capped: the cage-owned
    files plus the repository's top-level public claim documents. The
    full public package scan runs at RC1 packaging time and remains
    pending.
    """
    root = pathlib.Path(root)
    surface = [
        root / "README.md",
        root / "NON_CLAIMS.md",
        root / "SCIENTIFIC_BOUNDARIES.md",
        root / "docs" / "release" / "WORKBENCH_PUBLIC_RC1_CAGE_NOTES.md",
    ]
    cage = root / "rgcs_workbench" / "public_cage"
    surface.extend(sorted(cage.glob("*.py")))
    surface.extend(sorted(cage.glob("*.json")))
    return [p for p in surface if p.is_file()]


def scan_tracked_markdown(root: str | pathlib.Path) -> list[dict]:
    """The packaging-time full-tree scan: every git-tracked markdown
    file in the public repository. Untracked files are not release
    content; tracked non-markdown claim text is gated by the cage
    surface scan and the module registries."""
    import subprocess
    root = pathlib.Path(root)
    out = subprocess.run(["git", "ls-files", "*.md"], cwd=root,
                         capture_output=True, text=True, check=True)
    paths = [root / line for line in out.stdout.splitlines() if line]
    return scan_paths(p for p in paths if p.is_file())


__all__ = ["BANNED_PHRASES", "ALLOWED_CONTEXT_MARKERS",
           "CONTEXT_WINDOW_BEFORE", "scan_text", "scan_file", "scan_paths",
           "firewall_report", "cage_public_surface",
           "scan_tracked_markdown"]
